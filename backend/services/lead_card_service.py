"""Unified lead card service.

All three legacy lead systems (pressure engine Leads, campaign-log LeadEntries,
and storyline-minted lead cards) converge here.  The canonical store is the
`campaign_cards` MongoDB collection with ``type="lead"``, ``pool="world"``.

Public API
----------
make_lead_card(campaign_id, *, title, summary, ...)  → dict
    Build a ready-to-insert campaign_cards document.

async seed_opening_leads(db, campaign_id, intent_dict, world, character)
    Create 3-5 flavored opening lead cards at campaign generation time.
    Uses event_catalog templates + character background/bonds; no LLM needed.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Status vocabulary that covers all three legacy models.
LEAD_STATUSES = frozenset({
    "planted",     # seeded at campaign creation — not yet encountered
    "active",      # player has engaged with the hook
    "unexplored",  # known but not yet pursued (LeadEntry default)
    "sealed",      # failed knowledge check — body hidden
    "resolved",    # lead followed to conclusion
    "abandoned",   # player chose to drop it
    "ignored",     # pressure-engine: player noticed but didn't pursue
    "transformed", # pressure-engine: cleansing event changed it
})

# Event catalog types that map well to lead cards
_LEAD_CATALOG_TYPES = {"mystery", "discovery", "quest", "faction"}


def make_lead_card(
    campaign_id: str,
    *,
    title: str,
    summary: str,
    source: str = "dm_created",
    source_type: str = "",         # "hook|observation|rumor|environmental|conversation|catalog"
    character_id: Optional[str] = None,
    status: str = "planted",
    tags: Optional[List[str]] = None,
    # Relational links
    source_hook_id: Optional[str] = None,
    source_scene_id: Optional[str] = None,
    location_id: Optional[str] = None,
    linked_quest_id: Optional[str] = None,
    related_npc_ids: Optional[List[str]] = None,
    related_faction_ids: Optional[List[str]] = None,
    related_location_ids: Optional[List[str]] = None,
    player_notes: str = "",
    importance_score: float = 0.4,
    # Reveal mechanics (compatible with Phase 4 info-card pattern)
    secret_content: Optional[Dict] = None,
    reveal_dc: int = 13,
    reveal_check_type: str = "Investigation",
    # Extra metadata
    narrative_importance: Optional[Dict] = None,
    pinned: bool = False,
) -> Dict:
    """Build a unified campaign_cards document for a lead."""
    if status not in LEAD_STATUSES:
        status = "planted"
    now = datetime.now(timezone.utc).isoformat()
    base_tags = list(tags or [])
    if "lead" not in base_tags:
        base_tags.insert(0, "lead")

    return {
        "id": f"lead_{uuid.uuid4().hex[:10]}",
        "campaign_id": campaign_id,
        "character_id": character_id,
        "type": "lead",
        "pool": "world",
        "title": title[:80].strip(),
        "content": summary[:480].strip(),
        "secret_content": secret_content,
        "status": status,
        "tags": base_tags,
        # Source & context
        "source": source,
        "source_type": source_type,
        "source_hook_id": source_hook_id,
        "source_scene_id": source_scene_id,
        "location_id": location_id,
        # Relations
        "linked_quest_id": linked_quest_id,
        "related_npc_ids": related_npc_ids or [],
        "related_faction_ids": related_faction_ids or [],
        "related_location_ids": related_location_ids or [],
        # Player-editable
        "player_notes": player_notes,
        # Scoring
        "importance_score": round(float(importance_score), 3),
        # Reveal (for sealed leads from storylines)
        "reveal_dc": reveal_dc,
        "reveal_check_type": reveal_check_type,
        # Meta
        "auto_seeded": source != "dm_created",
        "pinned": pinned,
        "narrative_importance": narrative_importance or {},
        "createdAt": now,
        "updatedAt": now,
    }


async def seed_opening_leads(
    db,
    campaign_id: str,
    intent_dict: Dict[str, str],
    world: Dict[str, Any],
    character: Optional[Dict[str, Any]],
) -> List[Dict]:
    """Insert 3-5 opening lead cards into campaign_cards at campaign generation.

    Templates are drawn from the event catalog (mystery / discovery / quest /
    faction types) and flavored with character background, bonds, and the
    campaign's starting location. Status is "planted" — the player doesn't see
    them until the DM weaves the hook into narration and they engage with it.
    """
    from data.event_catalog import preview_campaign_deck

    # Pull candidates from the catalog biased toward this intent
    deck = preview_campaign_deck(intent_dict, top_n=20)
    candidates = [c for c in deck if c.get("type") in _LEAD_CATALOG_TYPES][:12]

    if not candidates:
        candidates = deck[:6]

    # Character flavor extraction
    location_name = (
        (world.get("startingLocation") or {}).get("name")
        or (world.get("starting_town") or {}).get("name")
        or "the starting area"
    )
    char_bonds: List[str] = []
    char_background = ""
    if character:
        identity = character.get("identity") or {}
        char_bonds = list(identity.get("bonds") or [])
        bg = character.get("background") or {}
        char_background = bg.get("key") or bg.get("name") or ""
        # V2 schema can also have bonds at top level
        if not char_bonds:
            char_bonds = list(character.get("bonds") or [])

    bond_hint = char_bonds[0][:60] if char_bonds else ""
    bg_hint = char_background[:30] if char_background else "wanderer"

    # Pick 3-5 distinct templates and create lead cards
    picked = candidates[:5]
    now = datetime.now(timezone.utc).isoformat()
    inserted: List[Dict] = []

    for tmpl in picked:
        title = tmpl.get("title") or "Unknown Lead"
        desc = tmpl.get("desc") or tmpl.get("description") or ""
        ttype = tmpl.get("type") or "mystery"

        # Flavor the description with location + character bonds/background
        flavor_suffix = f" (Near {location_name}"
        if bond_hint:
            flavor_suffix += f"; resonates with your bond: '{bond_hint}'"
        flavor_suffix += ".)"

        summary = (desc[:300] + flavor_suffix)[:480]

        # Build importance score: mystery > quest > discovery > faction
        importance = {"mystery": 0.65, "quest": 0.70, "discovery": 0.55, "faction": 0.60}.get(ttype, 0.50)

        # Tag with catalog type + background hint
        tags = ["lead", f"catalog-{ttype}", bg_hint.lower().replace(" ", "-")]
        if char_bonds:
            tags.append("bond-linked")

        card = make_lead_card(
            campaign_id,
            title=title,
            summary=summary,
            source="catalog",
            source_type="catalog",
            status="planted",
            tags=tags,
            importance_score=importance,
        )

        # Deduplicate: don't re-seed if a card with this title already exists
        existing = await db.campaign_cards.find_one(
            {"campaign_id": campaign_id, "type": "lead", "title": title}
        )
        if existing:
            continue

        try:
            await db.campaign_cards.insert_one(card)
            card.pop("_id", None)
            inserted.append(card)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[lead-seed] insert failed for {title!r}: {exc}")

    if inserted:
        logger.info(
            f"[lead-seed] seeded {len(inserted)} opening lead(s) for campaign {campaign_id}"
        )
    return inserted
