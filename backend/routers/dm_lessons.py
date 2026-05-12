"""DM Lessons endpoints — the persistent DM notebook the player can view,
edit, toggle, and feed via 👍/👎 reactions on narration beats.

Endpoints:

  GET    /api/campaigns/{campaign_id}/dm-lessons
         ?character_id=<id>    (optional — includes per-character lessons)
         -> { lessons: [...] }

  POST   /api/campaigns/{campaign_id}/dm-lessons
         body: { type, text, trigger_keywords?, weight?, character_id? }
         -> { lesson }
         Manual lesson entry from the DM Notebook UI.

  PATCH  /api/campaigns/{campaign_id}/dm-lessons/{lesson_id}
         body: { enabled?, weight?, text?, trigger_keywords? }
         -> { lesson }

  DELETE /api/campaigns/{campaign_id}/dm-lessons/{lesson_id}
         -> { ok: true }

  POST   /api/campaigns/{campaign_id}/dm-lessons/reaction
         body: { reaction: "like"|"dislike", narration, beat_title?,
                 character_id?, note?, message_id? }
         -> { lesson | null, action: "merged"|"created"|"skipped" }
         Distills a player's 👍/👎 on a DM beat into a lesson.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.dm_lessons import (
    distill_lesson_from_reaction,
    distill_session_review,
    merge_or_create_lesson,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaigns", tags=["dm_lessons"])

_db = None


def set_database(db):
    global _db
    _db = db


def _get_db():
    if _db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return _db


def _coll():
    return _get_db()["dm_lessons"]


def _to_out(doc: dict) -> dict:
    out = {k: v for k, v in doc.items() if k != "_id"}
    for k in ("created_at", "updated_at", "last_applied_at"):
        v = out.get(k)
        if isinstance(v, datetime):
            out[k] = v.isoformat()
    return out


# -------------------- request bodies --------------------


class ReactionBody(BaseModel):
    reaction: str  # "like" | "dislike"
    narration: str
    beat_title: Optional[str] = None
    character_id: Optional[str] = None
    note: Optional[str] = None
    message_id: Optional[str] = None  # opaque ref to the message in the log


class SessionReviewBody(BaseModel):
    character_id: Optional[str] = None


class ManualLessonBody(BaseModel):
    type: str
    text: str
    trigger_keywords: Optional[List[str]] = None
    weight: Optional[int] = 3
    character_id: Optional[str] = None


class UpdateLessonBody(BaseModel):
    enabled: Optional[bool] = None
    weight: Optional[int] = None
    text: Optional[str] = None
    trigger_keywords: Optional[List[str]] = None


# -------------------- endpoints --------------------


@router.get("/{campaign_id}/dm-lessons")
async def list_lessons(campaign_id: str, character_id: Optional[str] = None):
    query: dict = {"campaign_id": campaign_id}
    if character_id:
        query["$or"] = [{"character_id": character_id}, {"character_id": None}]
    cursor = _coll().find(query, {"_id": 0}).sort(
        [("enabled", -1), ("weight", -1), ("created_at", -1)]
    )
    docs = await cursor.to_list(length=200)
    return {"lessons": [_to_out(d) for d in docs]}


@router.post("/{campaign_id}/dm-lessons")
async def create_lesson(campaign_id: str, body: ManualLessonBody):
    if body.type not in {
        "rule_correction", "dc_calibration", "style_preference", "taboo",
        "challenge_tuning", "npc_craft", "narration_craft",
        "reward_balance", "villain_craft",
    }:
        raise HTTPException(status_code=400, detail="invalid lesson type")
    if not body.text or not body.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    lesson_partial = {
        "type": body.type,
        "text": body.text.strip()[:400],
        "trigger_keywords": [t.strip().lower()[:40] for t in (body.trigger_keywords or []) if t.strip()][:8],
        "weight": max(1, min(5, int(body.weight or 3))),
        "enabled": True,
        "source": "manual",
    }
    stored = await merge_or_create_lesson(
        _get_db(),
        campaign_id=campaign_id,
        character_id=body.character_id,
        lesson=lesson_partial,
    )
    return {"lesson": _to_out(stored)}


@router.patch("/{campaign_id}/dm-lessons/{lesson_id}")
async def update_lesson(campaign_id: str, lesson_id: str, body: UpdateLessonBody):
    updates: dict = {}
    if body.enabled is not None:
        updates["enabled"] = bool(body.enabled)
    if body.weight is not None:
        updates["weight"] = max(1, min(5, int(body.weight)))
    if body.text is not None:
        if not body.text.strip():
            raise HTTPException(status_code=400, detail="text cannot be empty")
        updates["text"] = body.text.strip()[:400]
    if body.trigger_keywords is not None:
        updates["trigger_keywords"] = [
            t.strip().lower()[:40] for t in body.trigger_keywords if str(t).strip()
        ][:8]
    if not updates:
        raise HTTPException(status_code=400, detail="no updates provided")
    res = await _coll().update_one(
        {"campaign_id": campaign_id, "id": lesson_id}, {"$set": updates}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="lesson not found")
    doc = await _coll().find_one({"campaign_id": campaign_id, "id": lesson_id}, {"_id": 0})
    return {"lesson": _to_out(doc) if doc else None}


@router.delete("/{campaign_id}/dm-lessons/{lesson_id}")
async def delete_lesson(campaign_id: str, lesson_id: str):
    res = await _coll().delete_one({"campaign_id": campaign_id, "id": lesson_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="lesson not found")
    return {"ok": True}


@router.post("/{campaign_id}/dm-lessons/reaction")
async def react_to_beat(campaign_id: str, body: ReactionBody):
    if body.reaction not in {"like", "dislike"}:
        raise HTTPException(status_code=400, detail="reaction must be 'like' or 'dislike'")
    if not (body.narration or "").strip():
        raise HTTPException(status_code=400, detail="narration is required")
    partial = await distill_lesson_from_reaction(
        reaction=body.reaction,
        narration=body.narration,
        beat_title=body.beat_title,
        note=body.note,
    )
    if not partial:
        return {"lesson": None, "action": "skipped"}
    stored = await merge_or_create_lesson(
        _get_db(),
        campaign_id=campaign_id,
        character_id=body.character_id,
        lesson=partial,
        source_ref={
            "reaction": body.reaction,
            "beat_title": body.beat_title,
            "message_id": body.message_id,
            "note": body.note,
        },
    )
    action = "merged" if stored.get("apply_count", 0) > 0 else "created"
    return {"lesson": _to_out(stored), "action": action}


@router.post("/{campaign_id}/dm-lessons/session-review")
async def session_review(campaign_id: str, body: SessionReviewBody):
    """Distill the recent session into lessons across the five craft
    categories (challenge_tuning / npc_craft / narration_craft /
    reward_balance / villain_craft). Triggered silently when the player
    returns to the main menu so the DM Notebook grows between sessions.
    """
    stored = await distill_session_review(
        _get_db(),
        campaign_id=campaign_id,
        character_id=body.character_id,
    )
    return {"lessons": [_to_out(d) for d in stored], "count": len(stored)}
