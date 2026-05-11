"""Canon Scenes endpoints — list/inspect the auto-checkpointed canon
backbone of a campaign. Used by the Canon Timeline UI.

Endpoints:

  GET  /api/campaigns/{campaign_id}/canon
       -> { scenes: [...], current: scene | null }
       Returns up to 50 canon scenes newest-first.

  GET  /api/campaigns/{campaign_id}/canon/current
       -> scene | null

The actual checkpoint CREATION happens automatically inside
storylines.py::resolve_storyline_beat when outcome=='passed', so there is
no public POST endpoint for that — canon is earned, not assigned.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaigns", tags=["canon_scenes"])

_db = None


def set_database(db):
    global _db
    _db = db


def _get_db():
    if _db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return _db


def _coll():
    return _get_db()["canon_scenes"]


def _to_out(doc: dict) -> dict:
    out = {k: v for k, v in doc.items() if k != "_id"}
    for k in ("created_at",):
        v = out.get(k)
        if isinstance(v, datetime):
            out[k] = v.isoformat()
    return out


@router.get("/{campaign_id}/canon")
async def list_canon(campaign_id: str, limit: int = 50):
    cursor = _coll().find(
        {"campaign_id": campaign_id}, {"_id": 0}
    ).sort("scene_number", -1).limit(max(1, min(200, int(limit))))
    docs = await cursor.to_list(length=200)
    current = next((d for d in docs if d.get("is_current")), docs[0] if docs else None)
    return {
        "scenes": [_to_out(d) for d in docs],
        "current": _to_out(current) if current else None,
    }


@router.get("/{campaign_id}/canon/current")
async def get_current_canon(campaign_id: str):
    doc = await _coll().find_one(
        {"campaign_id": campaign_id, "is_current": True}, {"_id": 0}
    )
    if not doc:
        # Fall back to the highest scene_number (in case is_current flag drift)
        doc = await _coll().find_one(
            {"campaign_id": campaign_id}, {"_id": 0},
            sort=[("scene_number", -1)],
        )
    return _to_out(doc) if doc else None
