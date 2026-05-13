"""Mission Types endpoints.

  GET    /api/mission-types?campaign_id=<id>          → list system + campaign-scoped
  GET    /api/mission-types/{mission_type_id}          → fetch by id
  POST   /api/mission-types                            → create from full JSON
  POST   /api/mission-types/from-prompt                → LLM generates from free text
  DELETE /api/mission-types/{mission_type_id}          → remove user-owned only
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.mission_types import (
    create_mission_type,
    delete_mission_type,
    generate_from_prompt,
    get_mission_type,
    list_mission_types,
)

router = APIRouter(prefix="/api/mission-types", tags=["mission_types"])

_db = None


def set_database(db):
    global _db
    _db = db


def _get_db():
    if _db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return _db


def _to_out(doc: dict) -> dict:
    out = {k: v for k, v in doc.items() if k != "_id"}
    if isinstance(out.get("created_at"), datetime):
        out["created_at"] = out["created_at"].isoformat()
    return out


class PhaseModel(BaseModel):
    name: str
    goal: str
    check_palette: List[str] = []
    reveal_type: str = "knowledge"
    target_palette: List[str] = []
    typical_dc_range: List[int] = [12, 15]
    min_beats: int = 1
    max_beats: int = 2
    signature_rewards: List[str] = []


class CreateBody(BaseModel):
    slug: str
    name: str
    icon: Optional[str] = "🎲"
    description: Optional[str] = ""
    phases: List[PhaseModel]
    signature_rewards: List[str] = []
    signature_complications: List[str] = []
    campaign_id: Optional[str] = None  # if set → owned by campaign, else system (admin only)


class FromPromptBody(BaseModel):
    prompt: str
    campaign_id: Optional[str] = None  # if set, save the result owned by that campaign
    auto_save: bool = False  # if True, persist immediately; else just return the draft


@router.get("")
async def list_types(campaign_id: Optional[str] = None):
    docs = await list_mission_types(_get_db(), campaign_id=campaign_id)
    return {"mission_types": [_to_out(d) for d in docs]}


@router.get("/{mission_type_id}")
async def get_type(mission_type_id: str):
    doc = await get_mission_type(_get_db(), mission_type_id=mission_type_id)
    if not doc:
        raise HTTPException(status_code=404, detail="mission type not found")
    return _to_out(doc)


@router.post("")
async def create_type(body: CreateBody):
    if not body.phases or len(body.phases) < 2:
        raise HTTPException(status_code=400, detail="at least 2 phases required")
    owner_id = f"campaign:{body.campaign_id}" if body.campaign_id else "system"
    data = body.model_dump()
    doc = await create_mission_type(_get_db(), owner_id=owner_id, data=data)
    return {"mission_type": _to_out(doc)}


@router.post("/from-prompt")
async def from_prompt(body: FromPromptBody):
    if not body.prompt or not body.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt is required")
    draft = await generate_from_prompt(body.prompt.strip())
    if not draft:
        raise HTTPException(status_code=502, detail="generator failed to produce a valid type")
    saved = None
    if body.auto_save:
        owner_id = f"campaign:{body.campaign_id}" if body.campaign_id else "system"
        doc = await create_mission_type(_get_db(), owner_id=owner_id, data=draft)
        saved = _to_out(doc)
    return {"draft": draft, "saved": saved}


@router.delete("/{mission_type_id}")
async def delete_type(mission_type_id: str, campaign_id: Optional[str] = None):
    owner = f"campaign:{campaign_id}" if campaign_id else None
    if not owner:
        raise HTTPException(status_code=400, detail="campaign_id required to authorise deletion")
    ok = await delete_mission_type(_get_db(), mission_type_id=mission_type_id, requester_owner=owner)
    if not ok:
        raise HTTPException(status_code=404, detail="mission type not found or not owned by this campaign")
    return {"ok": True}
