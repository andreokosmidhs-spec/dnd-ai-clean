"""Storyline endpoints — orchestrate hook → multi-beat investigation → reward.

Endpoints:

  POST /api/campaigns/{campaign_id}/storylines/draft
    body: {
      character_id: str,
      hook_id: str | null,
      hook_text: str,
      hook_topic: str | null,
      hook_verb: str | null,
      narration_context: str | null,
    }
    -> { storyline, quest }   # creates a quest knowledge card linked to the storyline

  GET /api/campaigns/{campaign_id}/storylines
    -> { storylines: [...] }   # active + completed for this campaign

  GET /api/campaigns/{campaign_id}/storylines/{storyline_id}
    -> storyline

  POST /api/campaigns/{campaign_id}/storylines/{storyline_id}/resolve
    body: {
      outcome: "passed" | "failed" | "skipped",
      outcome_text: str | null,
      roll_total: int | null,
    }
    -> { storyline, completed: bool, reward: {...} | null }
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

from bson import ObjectId
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from models.campaign_models import KnowledgeCard
from services.storyline_service import (
    advance_storyline,
    draft_storyline,
    generate_storyline_reward,
    storyline_to_dict,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaigns", tags=["storylines"])

_db = None


def set_database(db):
    global _db
    _db = db


def _get_db():
    if _db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return _db


def _storylines_collection():
    return _get_db()["campaign_storylines"]


def _cards_collection():
    return _get_db()["campaign_cards"]


async def _load_campaign(campaign_id: str) -> Dict:
    db = _get_db()
    campaign = await db.campaigns.find_one({"campaign_id": campaign_id}) or \
               await db.campaigns.find_one({"id": campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign not found: {campaign_id}")
    return campaign


async def _load_character(character_id: str) -> Optional[Dict]:
    db = _get_db()
    try:
        oid = ObjectId(character_id)
    except Exception:
        return None
    char = await db.characters_v2.find_one({"_id": oid})
    if char:
        char["id"] = str(char.pop("_id"))
    return char


# -------------------- request bodies --------------------


class DraftStorylineBody(BaseModel):
    character_id: str
    hook_text: str
    hook_id: Optional[str] = None
    hook_topic: Optional[str] = None
    hook_verb: Optional[str] = None
    narration_context: Optional[str] = None


class ResolveStorylineBody(BaseModel):
    outcome: str  # "passed" | "failed" | "skipped"
    outcome_text: Optional[str] = None
    roll_total: Optional[int] = None


# -------------------- endpoints --------------------


@router.post("/{campaign_id}/storylines/draft")
async def draft_storyline_endpoint(campaign_id: str, body: DraftStorylineBody):
    if not body.hook_text or not body.hook_text.strip():
        raise HTTPException(status_code=400, detail="hook_text is required")

    campaign = await _load_campaign(campaign_id)
    character = await _load_character(body.character_id)
    if not character:
        raise HTTPException(status_code=404, detail=f"Character not found: {body.character_id}")

    hook = {
        "id": body.hook_id or f"hook_{uuid4().hex[:8]}",
        "text": body.hook_text.strip(),
        "topic": (body.hook_topic or body.hook_text.strip()[:48]),
        "verb_hint": (body.hook_verb or "examine"),
    }

    drafted = await draft_storyline(
        campaign=campaign,
        character=character,
        hook=hook,
        narration_context=body.narration_context or "",
    )

    now = datetime.now(timezone.utc)
    storyline_id = f"sl_{uuid4().hex[:10]}"

    # Seed a quest KnowledgeCard from the FIRST beat. The card is the player-
    # facing surface for the storyline in the Quest Log; subsequent beats
    # update it via on the same card (description summarises 'Beat X of N').
    first_beat = (drafted.get("beats") or [{}])[0]
    quest_card = KnowledgeCard(
        type="quest",
        title=drafted.get("title") or "Active Investigation",
        description=(
            f"{first_beat.get('description','')} (Beat 1 of {len(drafted.get('beats') or [])} — "
            f"{first_beat.get('check_type','Investigation')} DC {first_beat.get('dc',12)}.)"
        ),
        source="hook-storyline",
        confidence="high",
        tags=["quest", "active", "investigation", "storyline"],
        status="active",
        updatedAt=now,
    )
    quest_doc = {**quest_card.model_dump(), "campaign_id": campaign_id, "storyline_id": storyline_id}
    await _cards_collection().insert_one(quest_doc)

    storyline_doc = {
        "id": storyline_id,
        "campaign_id": campaign_id,
        "character_id": body.character_id,
        "title": drafted.get("title") or "Investigation",
        "hook_text": hook["text"],
        "hook_id": hook["id"],
        "hook_topic": hook["topic"],
        "status": "active",
        "current_beat": 0,
        "beats": drafted["beats"],
        "total_dc": drafted["total_dc"],
        "reward": None,
        "quest_card_id": quest_card.id,
        "created_at": now,
        "updated_at": now,
    }
    await _storylines_collection().insert_one(dict(storyline_doc))

    return {
        "storyline": storyline_to_dict(storyline_doc),
        "quest_card_id": quest_card.id,
    }


@router.get("/{campaign_id}/storylines")
async def list_storylines(campaign_id: str):
    cursor = _storylines_collection().find({"campaign_id": campaign_id}, {"_id": 0}).sort("updated_at", -1)
    docs = await cursor.to_list(length=100)
    for d in docs:
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
        if isinstance(d.get("updated_at"), datetime):
            d["updated_at"] = d["updated_at"].isoformat()
    return {"storylines": docs}


@router.get("/{campaign_id}/storylines/{storyline_id}")
async def get_storyline(campaign_id: str, storyline_id: str):
    doc = await _storylines_collection().find_one(
        {"campaign_id": campaign_id, "id": storyline_id}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Storyline not found")
    return storyline_to_dict(doc)


@router.post("/{campaign_id}/storylines/{storyline_id}/resolve")
async def resolve_storyline_beat(campaign_id: str, storyline_id: str, body: ResolveStorylineBody):
    if body.outcome not in {"passed", "failed", "skipped"}:
        raise HTTPException(status_code=400, detail="outcome must be passed|failed|skipped")

    doc = await _storylines_collection().find_one({"campaign_id": campaign_id, "id": storyline_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Storyline not found")
    if doc.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Storyline already completed")

    current = int(doc.get("current_beat") or 0)
    storyline = advance_storyline(doc, current, body.outcome, body.outcome_text)

    completed = storyline.get("status") == "completed"
    reward: Optional[Dict] = None
    if completed:
        campaign = await _load_campaign(campaign_id)
        character = await _load_character(doc.get("character_id")) or {}
        reward = await generate_storyline_reward(campaign, character, storyline)
        storyline["reward"] = reward
        # Mark the linked quest card completed (best-effort)
        quest_card_id = storyline.get("quest_card_id")
        if quest_card_id:
            await _cards_collection().update_one(
                {"campaign_id": campaign_id, "id": quest_card_id},
                {"$set": {"status": "completed", "updatedAt": datetime.now(timezone.utc)}},
            )
    else:
        # Update the linked quest card description so the Quest Log reflects
        # the new active beat.
        quest_card_id = storyline.get("quest_card_id")
        if quest_card_id:
            beats = storyline.get("beats") or []
            cur = int(storyline.get("current_beat") or 0)
            cur_beat = beats[cur] if 0 <= cur < len(beats) else {}
            new_desc = (
                f"{cur_beat.get('description','')} (Beat {cur+1} of {len(beats)} — "
                f"{cur_beat.get('check_type','Investigation')} DC {cur_beat.get('dc',12)}.)"
            )
            await _cards_collection().update_one(
                {"campaign_id": campaign_id, "id": quest_card_id},
                {"$set": {"description": new_desc, "updatedAt": datetime.now(timezone.utc)}},
            )

    await _storylines_collection().update_one(
        {"campaign_id": campaign_id, "id": storyline_id},
        {"$set": {k: v for k, v in storyline.items() if k != "_id"}},
    )

    return {
        "storyline": storyline_to_dict(storyline),
        "completed": completed,
        "reward": reward,
    }


@router.post("/{campaign_id}/storylines/{storyline_id}/abandon")
async def abandon_storyline(campaign_id: str, storyline_id: str):
    res = await _storylines_collection().update_one(
        {"campaign_id": campaign_id, "id": storyline_id, "status": "active"},
        {"$set": {"status": "abandoned", "updated_at": datetime.now(timezone.utc)}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Active storyline not found")
    # Mark linked quest card failed
    doc = await _storylines_collection().find_one(
        {"campaign_id": campaign_id, "id": storyline_id}, {"quest_card_id": 1}
    )
    if doc and doc.get("quest_card_id"):
        await _cards_collection().update_one(
            {"campaign_id": campaign_id, "id": doc["quest_card_id"]},
            {"$set": {"status": "failed", "updatedAt": datetime.now(timezone.utc)}},
        )
    return {"ok": True}
