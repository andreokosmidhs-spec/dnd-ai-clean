"""
Battlefield Layout Service — generates and caches tactical grid maps per location.

A grid is generated once via LLM the first time combat starts at a location,
then cached in MongoDB so the map is always identical on re-visits.
"""
import json
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

GRID_COLS = 8
GRID_ROWS = 6

_SYSTEM_PROMPT = (
    "You design tactical battle grid maps for D&D 5e encounters. "
    "Return ONLY valid JSON with no markdown fences and no extra text."
)


def _default_grid() -> Dict[str, Any]:
    """Fallback 8×6 stone-room grid: border walls, two pillars, central floor."""
    cells = []
    for y in range(GRID_ROWS):
        for x in range(GRID_COLS):
            if x == 0 or x == GRID_COLS - 1 or y == 0 or y == GRID_ROWS - 1:
                # Door openings on left and right mid-walls
                if (x == 0 and y == 2) or (x == GRID_COLS - 1 and y == 3):
                    t = "door"
                else:
                    t = "wall"
            elif (x == 2 and y == 2) or (x == 5 and y == 3):
                t = "pillar"
            else:
                t = "floor"
            cells.append({"x": x, "y": y, "type": t})
    return {"cols": GRID_COLS, "rows": GRID_ROWS, "cells": cells, "generated": False}


def _parse_json_grid(raw: str) -> Optional[Dict[str, Any]]:
    """Strip markdown fences if present and parse JSON."""
    raw = raw.strip()
    # Remove ```json ... ``` or ``` ... ```
    raw = re.sub(r"^```(?:json)?", "", raw).rstrip("`").strip()
    try:
        data = json.loads(raw)
        if "cells" not in data or len(data["cells"]) < 40:
            return None
        return data
    except (json.JSONDecodeError, ValueError):
        return None


def generate_grid_layout(
    location_name: str,
    location_description: str = "",
    biome: str = "dungeon",
) -> Dict[str, Any]:
    """
    Call the LLM (Haiku, sync) to generate a battlefield grid for a location.
    Returns the default grid on any error.
    """
    from services.claude_client import call_haiku_sync

    user_content = f"""Location: {location_name}
Description: {location_description or "A classic adventuring location"}
Environment: {biome}
Grid size: {GRID_COLS} columns (x: 0–{GRID_COLS-1}) × {GRID_ROWS} rows (y: 0–{GRID_ROWS-1})
Each cell = 5 feet. Total area: {GRID_COLS*5}ft × {GRID_ROWS*5}ft.

Create a tactical battle map. Rules:
- All {GRID_COLS * GRID_ROWS} cells (every x/y combination) must be present exactly once.
- Border cells (x=0, x={GRID_COLS-1}, y=0, y={GRID_ROWS-1}) are mostly walls.
- Add 1–2 door/opening cells in the borders so combatants can enter/exit.
- Add 2–4 interior terrain features that fit the environment theme.
- At least 60% of interior (non-border) cells must be walkable (floor/difficult/cover/water/altar).
- Player token spawns LEFT side (x=1), enemy tokens spawn RIGHT side (x={GRID_COLS-2}).

Available cell types: floor, wall, pillar, difficult, cover, door, water, tree, rock, rubble, altar, chest

Return ONLY this JSON (no markdown, no comments):
{{"cols": {GRID_COLS}, "rows": {GRID_ROWS}, "cells": [{{"x": 0, "y": 0, "type": "wall"}}, ...]}}"""

    try:
        raw = call_haiku_sync(
            system_prompt=_SYSTEM_PROMPT,
            user_content=user_content,
            max_tokens=1400,
            temperature=0.3,
        )
        data = _parse_json_grid(raw)
        if data is None:
            raise ValueError("Grid JSON invalid or too few cells")
        data["generated"] = True
        logger.info(f"🗺️ Generated grid for '{location_name}' ({len(data['cells'])} cells)")
        return data
    except Exception as exc:
        logger.warning(f"⚠️ Grid generation failed for '{location_name}': {exc} — using default")
        return _default_grid()


async def get_or_generate_layout(
    db,
    campaign_id: str,
    location_key: str,
    location_name: str,
    location_description: str = "",
    biome: str = "dungeon",
) -> Dict[str, Any]:
    """
    Return the cached battlefield grid for (campaign_id, location_key),
    generating and storing it if no cache entry exists.
    """
    import asyncio

    cached = await db["battlefield_layouts"].find_one(
        {"campaign_id": campaign_id, "location_key": location_key},
        {"_id": 0, "grid": 1},
    )
    if cached:
        logger.info(f"🗺️ Cache hit for battlefield layout '{location_name}'")
        return cached["grid"]

    # Generate in a thread (sync LLM call)
    grid = await asyncio.to_thread(
        generate_grid_layout, location_name, location_description, biome
    )

    await db["battlefield_layouts"].insert_one({
        "campaign_id": campaign_id,
        "location_key": location_key,
        "location_name": location_name,
        "grid": grid,
    })
    return grid


def location_key_for(location_name: str) -> str:
    """Stable, lowercase slug used as the cache key."""
    return re.sub(r"[^a-z0-9]+", "_", (location_name or "unknown").lower()).strip("_")


def enemy_start_positions(enemies: list, grid_cols: int = GRID_COLS, grid_rows: int = GRID_ROWS) -> list:
    """
    Assign initial grid_x / grid_y positions to enemies based on their role/lane.
    Enemies start on the right half; player starts left at (1, 2).
    """
    mid_y = grid_rows // 2  # row 3

    for i, enemy in enumerate(enemies):
        lane = enemy.get("lane", 2)
        # Map lane to approximate column
        if lane >= 3:
            x = grid_cols - 2  # far right, just inside wall
        else:
            x = grid_cols - 3  # close-right

        # Spread enemies vertically
        y = max(1, min(grid_rows - 2, mid_y - 1 + i))

        enemy["grid_x"] = x
        enemy["grid_y"] = y

    return enemies
