"""Combat battlefield condition cards + death saves + saving throws.

GET  /api/campaigns/{campaign_id}/combat/conditions
     — list active conditions for the current combat

POST /api/campaigns/{campaign_id}/combat/conditions
     — DM creates a custom condition (title + description)

DELETE /api/campaigns/{campaign_id}/combat/conditions/{condition_id}
     — remove / deactivate a condition

POST /api/campaigns/{campaign_id}/combat/conditions/{condition_id}/interact
     — player proposes using the environment; AI DM adjudicates

POST /api/campaigns/{campaign_id}/combat/death-save
     — player rolls a D&D 5e death saving throw

POST /api/campaigns/{campaign_id}/combat/saving-throw
     — player rolls a D&D 5e saving throw against a DC
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Body, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaigns", tags=["combat-conditions"])

MONGO_URL = os.environ.get("MONGO_URL", "")
DB_NAME   = os.environ.get("DB_NAME", "dnd")


def _db():
    return AsyncIOMotorClient(MONGO_URL)[DB_NAME]


# ── Models ───────────────────────────────────────────────────────────────────

class CreateConditionBody(BaseModel):
    title: str
    description: str
    tags: Optional[List[str]] = None
    biome: Optional[str] = "custom"
    rarity: Optional[str] = "common"


class InteractBody(BaseModel):
    player_action: str          # "I try to slide through the mud toward the enemy"
    roll: int                   # d20 result (1-20)
    character_state: Optional[dict] = None
    combat_state: Optional[dict] = None
    character_id: Optional[str] = None


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _get_active_conditions(db, campaign_id: str) -> List[dict]:
    from services.condition_art_service import _art_key

    cursor = db.combat_conditions.find(
        {"campaign_id": campaign_id, "active": True},
        sort=[("created_at", 1)],
    )
    docs = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        # Attach cached art if available and not already on the doc
        if not doc.get("art_data_url"):
            key = _art_key(doc.get("title", ""), doc.get("description", ""))
            art = await db.combat_condition_art.find_one({"art_key": key}, {"data_url": 1})
            if art and art.get("data_url"):
                doc["art_data_url"] = art["data_url"]
        docs.append(doc)
    return docs


async def _seed_biome_conditions(db, campaign_id: str, location_name: str) -> List[dict]:
    """Auto-seed battlefield conditions from the detected biome.
    Only seeds if no conditions exist yet for this campaign combat."""
    from data.biome_conditions import detect_biome, conditions_for_biome

    existing = await db.combat_conditions.count_documents(
        {"campaign_id": campaign_id, "active": True}
    )
    if existing > 0:
        return []

    biome = detect_biome(location_name)
    biome_cards = conditions_for_biome(biome, max_count=3)

    now = datetime.now(timezone.utc)
    seeded = []
    for card in biome_cards:
        doc = {
            "condition_id": f"biome_{card['key']}_{uuid.uuid4().hex[:6]}",
            "campaign_id": campaign_id,
            "title": card["title"],
            "description": card["description"],
            "tags": card.get("tags", []),
            "biome": biome,
            "rarity": card.get("rarity", "common"),
            "source": "biome",
            "active": True,
            "created_at": now,
            "updated_at": now,
        }
        await db.combat_conditions.insert_one(doc)
        doc["id"] = str(doc.pop("_id"))
        seeded.append(doc)
        logger.info(f"🌍 Seeded biome condition '{card['title']}' for {campaign_id} ({biome})")

    return seeded


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/{campaign_id}/combat/conditions")
async def get_conditions(campaign_id: str, location: Optional[str] = None):
    """Return active battlefield conditions. Auto-seeds from biome if empty."""
    db = _db()
    if location:
        await _seed_biome_conditions(db, campaign_id, location)
    conditions = await _get_active_conditions(db, campaign_id)
    return {"conditions": conditions, "count": len(conditions)}


@router.post("/{campaign_id}/combat/conditions")
async def create_condition(campaign_id: str, body: CreateConditionBody):
    """DM creates a custom battlefield condition mid-combat."""
    db = _db()
    now = datetime.now(timezone.utc)
    doc = {
        "condition_id": f"dm_{uuid.uuid4().hex[:8]}",
        "campaign_id": campaign_id,
        "title": body.title,
        "description": body.description,
        "tags": body.tags or [],
        "biome": body.biome or "custom",
        "rarity": body.rarity or "common",
        "source": "dm",
        "active": True,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.combat_conditions.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    logger.info(f"✍️ DM created condition '{body.title}' for campaign {campaign_id}")
    return {"ok": True, "condition": doc}


@router.delete("/{campaign_id}/combat/conditions/{condition_id}")
async def remove_condition(campaign_id: str, condition_id: str):
    """Deactivate (soft-delete) a condition."""
    db = _db()
    res = await db.combat_conditions.update_one(
        {"campaign_id": campaign_id, "condition_id": condition_id},
        {"$set": {"active": False, "updated_at": datetime.now(timezone.utc)}},
    )
    if res.matched_count == 0:
        raise HTTPException(404, "Condition not found")
    return {"ok": True}


@router.post("/{campaign_id}/combat/conditions/seed")
async def seed_conditions(campaign_id: str, body: dict = Body(default={})):
    """Explicitly seed biome conditions for a location (called at combat start)."""
    db = _db()
    location = body.get("location", "")
    seeded = await _seed_biome_conditions(db, campaign_id, location)
    return {"ok": True, "seeded": seeded}


@router.post("/{campaign_id}/combat/conditions/{condition_id}/art")
async def generate_condition_art(campaign_id: str, condition_id: str):
    """
    Generate (or return cached) AI art for a battlefield condition.
    The card description is used as the image prompt core.
    Returns {art_url} — may be null if generation is unavailable.
    """
    db = _db()
    condition = await db.combat_conditions.find_one(
        {"campaign_id": campaign_id, "condition_id": condition_id}
    )
    if not condition:
        raise HTTPException(404, "Condition not found")

    from services.condition_art_service import get_or_generate_art
    data_url = await get_or_generate_art(
        db,
        title=condition["title"],
        description=condition["description"],
    )

    if data_url:
        # Persist art_data_url on the condition document
        await db.combat_conditions.update_one(
            {"campaign_id": campaign_id, "condition_id": condition_id},
            {"$set": {"art_data_url": data_url, "updated_at": datetime.now(timezone.utc)}},
        )

    return {"ok": True, "art_url": data_url}


@router.post("/{campaign_id}/combat/conditions/clear")
async def clear_conditions(campaign_id: str):
    """Clear all active conditions (e.g. after combat ends)."""
    db = _db()
    await db.combat_conditions.update_many(
        {"campaign_id": campaign_id, "active": True},
        {"$set": {"active": False, "updated_at": datetime.now(timezone.utc)}},
    )
    return {"ok": True}


# ── Player interaction with a condition ──────────────────────────────────────

@router.post("/{campaign_id}/combat/conditions/{condition_id}/interact")
async def interact_with_condition(
    campaign_id: str,
    condition_id: str,
    body: InteractBody,
):
    """
    Player proposes using the battlefield environment creatively.

    The AI DM adjudicates based on:
      - The condition's narrative description
      - The player's proposed action
      - The d20 roll result

    Returns DM narration + outcome hint.
    """
    db = _db()

    # Load condition
    condition = await db.combat_conditions.find_one(
        {"campaign_id": campaign_id, "condition_id": condition_id, "active": True}
    )
    if not condition:
        raise HTTPException(404, "Condition not found or no longer active")

    roll = max(1, min(20, body.roll))
    player_action = (body.player_action or "").strip()
    if not player_action:
        raise HTTPException(400, "player_action is required")

    char = body.character_state or {}
    char_name = (
        char.get("identity", {}).get("name")
        or char.get("name")
        or "The adventurer"
    )
    char_class = (
        (char.get("class_") or char.get("class") or {}).get("name")
        or char.get("class")
        or "adventurer"
    )

    # Build adjudication prompt
    roll_tier = (
        "nat 20 — legendary success, something spectacular happens"        if roll == 20 else
        "high roll (15-19) — creative success with a notable bonus"        if roll >= 15 else
        "solid roll (8-14) — it works, no extra bonus or penalty"          if roll >= 8  else
        "low roll (2-7) — risky approach backfires, some consequence"      if roll >= 2  else
        "nat 1 — spectacular failure, an entertaining catastrophe"
    )

    prompt = f"""You are the Dungeon Master adjudicating a player's creative use of the battlefield environment.

BATTLEFIELD CONDITION:
Title: {condition['title']}
Description: {condition['description']}

PLAYER ({char_name}, {char_class}) PROPOSES:
"{player_action}"

DICE ROLL: {roll}/20 — {roll_tier}

YOUR TASK:
Write 2-4 sentences of vivid DM narration describing what happens when {char_name} attempts this.

Rules:
- High roll (15+): award a meaningful bonus — extra damage, advantageous position, a foe off-balance, something cinematic
- Mid roll (8-14): the action works as described, no extra reward or punishment
- Low roll (1-7): the gambit backfires in a narratively fitting way — maybe they slip, drop something, end up in a worse position, or give the enemy an opening. The consequence should fit the environment.
- Nat 20: something spectacular and memorable — go big
- Nat 1: a creative catastrophe — funny or painful, but fitting
- Do NOT use the word "roll" or reference dice in your narration
- Write in second-person present tense ("You plant your foot and...")
- Keep it to 2-4 sentences maximum
- End with a one-line OUTCOME in brackets: [BONUS: +Xd6 damage] or [PENALTY: Prone / disarmed / etc.] or [NEUTRAL: action succeeds] or [SPECTACULAR: describe]

Narrate now:"""

    try:
        import litellm
        model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
        response = await litellm.acompletion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.8,
        )
        raw = response.choices[0].message.content.strip()
    except Exception as exc:
        logger.warning(f"LLM failed for condition interaction: {exc}")
        # Graceful fallback narration
        if roll >= 15:
            raw = (
                f"You seize the moment brilliantly — the {condition['title'].lower()} "
                f"works in your favour exactly as you imagined. "
                f"The enemy has no answer for your ingenuity. [BONUS: +1d6 damage]"
            )
        elif roll >= 8:
            raw = (
                f"You use the {condition['title'].lower()} as intended — "
                f"it works, clean and simple. [NEUTRAL: action succeeds]"
            )
        else:
            raw = (
                f"You try to use the {condition['title'].lower()} but the environment "
                f"turns against you at the worst possible moment. "
                f"The gambit costs you more than it gives. [PENALTY: Prone]"
            )

    # Parse bracket outcome hint from narration
    outcome_raw = ""
    if "[" in raw and "]" in raw:
        start = raw.rfind("[")
        end = raw.rfind("]")
        outcome_raw = raw[start + 1 : end].strip()
        narration = raw[:start].strip()
    else:
        narration = raw

    # Classify outcome type
    outcome_lower = outcome_raw.lower()
    if "bonus" in outcome_lower or "spectacular" in outcome_lower:
        outcome_type = "bonus"
    elif "penalty" in outcome_lower:
        outcome_type = "penalty"
    else:
        outcome_type = "neutral"

    # Log the interaction
    await db.combat_condition_interactions.insert_one({
        "campaign_id": campaign_id,
        "condition_id": condition_id,
        "character_id": body.character_id,
        "player_action": player_action,
        "roll": roll,
        "narration": narration,
        "outcome_raw": outcome_raw,
        "outcome_type": outcome_type,
        "created_at": datetime.now(timezone.utc),
    })

    return {
        "ok": True,
        "narration": narration,
        "outcome": {
            "type": outcome_type,
            "description": outcome_raw,
            "roll": roll,
        },
        "condition": {
            "id": condition_id,
            "title": condition["title"],
        },
    }


# ── Death Saving Throws ───────────────────────────────────────────────────────

@router.post("/{campaign_id}/combat/death-save")
async def make_death_save(campaign_id: str, body: dict = Body(default={})):
    """Player rolls a D&D 5e death saving throw. Updates combat state.

    Body: { character_id: str }
    Returns: { ok, save, death_saves, combat_state }
    """
    character_id = body.get("character_id")
    if not character_id:
        raise HTTPException(400, "character_id required")

    db = _db()
    combat_doc = await db.combats.find_one(
        {"campaign_id": campaign_id, "character_id": character_id}
    )
    if not combat_doc:
        raise HTTPException(404, "No active combat found")

    from services.dnd_rules import roll_death_save
    save = roll_death_save()
    combat_state = combat_doc.get("combat_state", {})
    death_saves = combat_state.get(
        "death_saves",
        {"successes": 0, "failures": 0, "stable": False, "dead": False},
    )

    outcome = "ongoing"
    if save["result"] == "critical_success":
        # Nat 20: regain 1 HP, no longer dying
        death_saves = {"successes": 0, "failures": 0, "stable": False, "dead": False}
        combat_state["player_hp"] = 1
        combat_state["player_dying"] = False
        outcome = "revived"
        logger.info(f"✨ Death save nat 20 — player revived with 1 HP in campaign {campaign_id}")
    elif save["result"] == "critical_failure":
        death_saves["failures"] = min(3, death_saves.get("failures", 0) + 2)
    elif save["result"] == "success":
        death_saves["successes"] = min(3, death_saves.get("successes", 0) + 1)
    else:  # failure
        death_saves["failures"] = min(3, death_saves.get("failures", 0) + 1)

    dead = death_saves.get("failures", 0) >= 3
    stable = death_saves.get("successes", 0) >= 3 and not dead
    death_saves["dead"] = dead
    death_saves["stable"] = stable

    if dead:
        combat_state["combat_over"] = True
        combat_state["outcome"] = "player_defeated"
        combat_state["player_dying"] = False
        outcome = "dead"
        logger.warning(f"☠️ Player died from death saves in campaign {campaign_id}")
    elif stable:
        combat_state["player_dying"] = False
        outcome = "stable"
        logger.info(f"💚 Player stabilized (3 death save successes) in campaign {campaign_id}")

    combat_state["death_saves"] = death_saves

    await db.combats.update_one(
        {"campaign_id": campaign_id, "character_id": character_id},
        {"$set": {
            "combat_state": combat_state,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )

    return {
        "ok": True,
        "save": save,
        "outcome": outcome,
        "death_saves": death_saves,
        "combat_state": combat_state,
    }


# ── Saving Throws ─────────────────────────────────────────────────────────────

@router.post("/{campaign_id}/combat/saving-throw")
async def make_saving_throw(campaign_id: str, body: dict = Body(default={})):
    """Player rolls a D&D 5e ability saving throw against a DC.

    Body: {
        character_id: str,
        ability: str,          # "str" | "dex" | "con" | "int" | "wis" | "cha"
        dc: int,
        advantage?: bool,
        disadvantage?: bool,
    }
    Returns full save result dict.
    """
    character_id = body.get("character_id")
    ability = body.get("ability", "con")
    dc = int(body.get("dc", 15))
    advantage = bool(body.get("advantage", False))
    disadvantage = bool(body.get("disadvantage", False))

    if not character_id:
        raise HTTPException(400, "character_id required")

    db = _db()

    # Try to load character state for modifier calculation
    char_doc = await db.characters.find_one({"character_id": character_id})
    if not char_doc:
        # Fallback: minimal state with no modifiers
        char_state: dict = {}
    else:
        char_state = char_doc.get("character_state", {})

    from services.saving_throw_service import roll_saving_throw
    result = roll_saving_throw(
        character_state=char_state,
        ability=ability,
        dc=dc,
        advantage=advantage,
        disadvantage=disadvantage,
    )

    logger.info(
        f"🎲 Saving throw: {ability.upper()} DC {dc} — "
        f"roll={result['roll']} total={result['total']} {'SUCCESS' if result['success'] else 'FAILURE'}"
    )

    return {"ok": True, "result": result}
