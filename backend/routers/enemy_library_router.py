"""
Enemy Library Router

GET  /api/enemy-library
     — list all enemies (id, name, cr, type, behavior_profile, description)

GET  /api/enemy-library/{enemy_id}
     — full stat block for one enemy

POST /api/enemy-library/add-to-combat
     — body: {campaign_id, character_id, enemy_id, name_override?}
       Adds enemy to active combat_state.enemies in the combats collection.
"""
from __future__ import annotations

import logging
import os
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

from data.enemy_library import ENEMY_LIBRARY, list_enemies
from services.enemy_behavior_service import build_combat_enemy

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/enemy-library", tags=["enemy-library"])

MONGO_URL = os.environ.get("MONGO_URL", "")
DB_NAME = os.environ.get("DB_NAME", "dnd")


def _db():
    return AsyncIOMotorClient(MONGO_URL)[DB_NAME]


# ── Models ────────────────────────────────────────────────────────────────────

class EnemySummary(BaseModel):
    id: str
    name: str
    cr: str
    type: str
    behavior_profile: str
    description: str
    hp: int
    ac: int
    xp: int


class AddToCombatRequest(BaseModel):
    campaign_id: str
    character_id: str
    enemy_id: str
    name_override: Optional[str] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[EnemySummary])
async def list_all_enemies():
    """Return a summary list of all enemies in the library."""
    summaries = []
    for e in list_enemies():
        summaries.append(EnemySummary(
            id=e["id"],
            name=e["name"],
            cr=e["cr"],
            type=e["type"],
            behavior_profile=e.get("behavior_profile", "brute"),
            description=e.get("description", ""),
            hp=e.get("hp", 0),
            ac=e.get("ac", 10),
            xp=e.get("xp", 0),
        ))
    return summaries


@router.get("/{enemy_id}")
async def get_enemy(enemy_id: str):
    """Return the full stat block for a specific enemy."""
    enemy = ENEMY_LIBRARY.get(enemy_id)
    if enemy is None:
        raise HTTPException(status_code=404, detail=f"Enemy '{enemy_id}' not found in library.")
    return enemy


@router.post("/add-to-combat")
async def add_enemy_to_combat(body: AddToCombatRequest):
    """
    Build a combat-ready enemy from the library and append it to the active
    combat_state.enemies list for the given campaign + character.
    """
    # Build the combat-ready enemy dict
    combat_enemy = build_combat_enemy(body.enemy_id, name_override=body.name_override)
    if combat_enemy is None:
        raise HTTPException(
            status_code=404,
            detail=f"Enemy '{body.enemy_id}' not found in library.",
        )

    if not MONGO_URL or not DB_NAME:
        # No DB configured — return the enemy dict so the client can use it
        logger.warning("No MongoDB configured — returning enemy dict without persisting.")
        return {
            "success": True,
            "message": "No database configured; enemy built but not persisted.",
            "enemy": combat_enemy,
        }

    db = _db()
    combat_doc = await db.combats.find_one(
        {"campaign_id": body.campaign_id, "character_id": body.character_id}
    )
    if combat_doc is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No active combat found for campaign '{body.campaign_id}' "
                f"and character '{body.character_id}'."
            ),
        )

    # Append enemy to existing enemies list
    result = await db.combats.update_one(
        {"campaign_id": body.campaign_id, "character_id": body.character_id},
        {"$push": {"combat_state.enemies": combat_enemy}},
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=500,
            detail="Failed to add enemy to combat state.",
        )

    logger.info(
        "Added enemy '%s' (instance %s) to combat for campaign %s",
        combat_enemy.get("name"),
        combat_enemy.get("instance_id"),
        body.campaign_id,
    )

    return {
        "success": True,
        "message": f"Added {combat_enemy['name']} to combat.",
        "enemy": combat_enemy,
    }
