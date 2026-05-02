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
    generate_complication_beat,
    generate_storyline_reward,
    judge_creative_approach,
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
    # Failure handling: "fail-forward" advances to next beat with a complication,
    # "press-on" retries the SAME beat (one-time per storyline) with a complication.
    # Defaults to "fail-forward" when outcome="failed".
    mode: Optional[str] = None  # "fail-forward" | "press-on"


class CreativeApproachBody(BaseModel):
    """Player describes an alternative way to resolve the current beat."""
    approach_text: str


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
        "press_on_used": False,
        "complication": None,
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
    beats = doc.get("beats") or []
    cur_beat = beats[current] if 0 <= current < len(beats) else {}
    campaign = await _load_campaign(campaign_id)
    character = await _load_character(doc.get("character_id")) or {}

    # Decide failure mode (only relevant when outcome == 'failed').
    mode = (body.mode or "").strip().lower()
    is_press_on = (body.outcome == "failed" and mode == "press-on")

    if is_press_on:
        if doc.get("press_on_used"):
            raise HTTPException(status_code=400, detail="Press On already used this storyline")
        # Generate the cost-of-retry complication beat WITHOUT advancing.
        complication_text = await generate_complication_beat(
            intent=campaign.get("intent") or {},
            world=campaign.get("world") or {},
            character=character,
            storyline=doc,
            beat=cur_beat,
            mode="press-on",
        )
        # Mark the beat with the complication note but keep it active.
        beats = doc.get("beats") or []
        if 0 <= current < len(beats):
            beats[current]["status"] = "active"
            beats[current]["outcome_text"] = (body.outcome_text or "Failed — pressing on.")[:240]
        doc["press_on_used"] = True
        doc["complication"] = complication_text
        doc["updated_at"] = datetime.now(timezone.utc)
        await _storylines_collection().update_one(
            {"campaign_id": campaign_id, "id": storyline_id},
            {"$set": {k: v for k, v in doc.items() if k != "_id"}},
        )
        return {
            "storyline": storyline_to_dict(doc),
            "completed": False,
            "mode": "press-on",
            "complication": complication_text,
            "reward": None,
        }

    # Default path: advance the beat (outcome can be passed | failed | skipped).
    storyline = advance_storyline(doc, current, body.outcome, body.outcome_text)

    # If failed (and not press-on), produce a fail-forward complication so the
    # Adventure Log gets a narrative beat tying the failure to the story.
    complication_text: Optional[str] = None
    if body.outcome == "failed":
        try:
            complication_text = await generate_complication_beat(
                intent=campaign.get("intent") or {},
                world=campaign.get("world") or {},
                character=character,
                storyline=storyline,
                beat=cur_beat,
                mode="fail-forward",
            )
            storyline["complication"] = complication_text
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"complication beat failed (non-fatal): {exc}")

    completed = storyline.get("status") == "completed"
    reward: Optional[Dict] = None
    if completed:
        reward = await generate_storyline_reward(campaign, character, storyline)
        storyline["reward"] = reward
        # Mark the linked quest card based on pass ratio: completed if any
        # beats passed, else failed.
        passed_any = any(b.get("status") == "passed" for b in (storyline.get("beats") or []))
        quest_status = "completed" if passed_any else "failed"
        quest_card_id = storyline.get("quest_card_id")
        if quest_card_id:
            await _cards_collection().update_one(
                {"campaign_id": campaign_id, "id": quest_card_id},
                {"$set": {"status": quest_status, "updatedAt": datetime.now(timezone.utc)}},
            )
    else:
        # Update the linked quest card description so the Quest Log reflects
        # the new active beat.
        quest_card_id = storyline.get("quest_card_id")
        if quest_card_id:
            beats = storyline.get("beats") or []
            cur = int(storyline.get("current_beat") or 0)
            cur_beat_now = beats[cur] if 0 <= cur < len(beats) else {}
            new_desc = (
                f"{cur_beat_now.get('description','')} (Beat {cur+1} of {len(beats)} — "
                f"{cur_beat_now.get('check_type','Investigation')} DC {cur_beat_now.get('dc',12)}.)"
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
        "mode": "fail-forward" if body.outcome == "failed" else "advance",
        "complication": complication_text,
        "reward": reward,
    }


@router.post("/{campaign_id}/storylines/{storyline_id}/creative")
async def creative_approach_endpoint(
    campaign_id: str, storyline_id: str, body: CreativeApproachBody
):
    """Player proposes an alternative approach to the current beat. The DM
    judges (passed | partial | failed); on passed/partial, the beat advances
    and the player gets credit. On failed, the beat is marked failed and we
    fall through to fail-forward (complication + advance)."""
    text = (body.approach_text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="approach_text is required")

    doc = await _storylines_collection().find_one({"campaign_id": campaign_id, "id": storyline_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Storyline not found")
    if doc.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Storyline already completed")

    current = int(doc.get("current_beat") or 0)
    beats = doc.get("beats") or []
    if not (0 <= current < len(beats)):
        raise HTTPException(status_code=400, detail="No active beat")
    cur_beat = beats[current]

    campaign = await _load_campaign(campaign_id)
    character = await _load_character(doc.get("character_id")) or {}

    judgment = await judge_creative_approach(
        intent=campaign.get("intent") or {},
        world=campaign.get("world") or {},
        character=character,
        storyline=doc,
        beat=cur_beat,
        approach_text=text,
    )

    judged_outcome = judgment.get("outcome", "partial")
    narration = judgment.get("narration") or ""
    # Map judgment to a storyline outcome:
    #   'passed'  -> advance with a clean pass
    #   'partial' -> advance, marked passed (player took a hit narratively)
    #   'failed'  -> mark failed, fall through to fail-forward
    storyline_outcome = "passed" if judged_outcome in {"passed", "partial"} else "failed"

    storyline = advance_storyline(
        doc, current, storyline_outcome,
        outcome_text=f"Creative approach ({judged_outcome}): {narration}"[:240],
    )

    complication_text: Optional[str] = None
    if storyline_outcome == "failed":
        try:
            complication_text = await generate_complication_beat(
                intent=campaign.get("intent") or {},
                world=campaign.get("world") or {},
                character=character,
                storyline=storyline,
                beat=cur_beat,
                mode="fail-forward",
            )
            storyline["complication"] = complication_text
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"complication after creative-fail failed: {exc}")

    completed = storyline.get("status") == "completed"
    reward: Optional[Dict] = None
    if completed:
        reward = await generate_storyline_reward(campaign, character, storyline)
        storyline["reward"] = reward
        passed_any = any(b.get("status") == "passed" for b in (storyline.get("beats") or []))
        quest_status = "completed" if passed_any else "failed"
        quest_card_id = storyline.get("quest_card_id")
        if quest_card_id:
            await _cards_collection().update_one(
                {"campaign_id": campaign_id, "id": quest_card_id},
                {"$set": {"status": quest_status, "updatedAt": datetime.now(timezone.utc)}},
            )

    await _storylines_collection().update_one(
        {"campaign_id": campaign_id, "id": storyline_id},
        {"$set": {k: v for k, v in storyline.items() if k != "_id"}},
    )

    return {
        "storyline": storyline_to_dict(storyline),
        "completed": completed,
        "judgment": judged_outcome,        # 'passed' | 'partial' | 'failed'
        "narration": narration,            # DM's response to the creative approach
        "applied_check": judgment.get("applied_check"),
        "complication": complication_text,  # only when judged_outcome == 'failed'
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
