"""
Living Campaign Pressure Engine — FastAPI Router

Endpoints:
  POST /api/pressure/tick                — advance world pressure
  GET  /api/pressure/{campaign_id}       — get full pressure state
  GET  /api/pressure/{campaign_id}/summary — lightweight summary
  POST /api/pressure/{campaign_id}/hooks — get/generate hooks for a region
  POST /api/pressure/{campaign_id}/leads — create a lead from a hook
  POST /api/pressure/{campaign_id}/antagonist/operate — trigger antagonist action
  GET  /api/pressure/{campaign_id}/cleansing — get cleansing events
  POST /api/pressure/init                — initialize pressure state for a campaign
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.pressure_models import (
    Antagonist, AntagonistMO, CampaignPressureState, CleansingEvent,
    Hook, Lead, LeadCreateRequest, PressureTickRequest,
    RegionalPressure, WorldWound, AntagonistOperationRequest,
)
from services.pressure_engine import (
    build_world_pressure_summary,
    check_cleansing_conditions,
    generate_antagonist_operation,
    generate_hooks_from_pressure,
    hook_to_lead,
    run_pressure_cycle,
    score_lead_importance,
    advance_antagonist_phase,
    get_antagonist_reveal_text,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pressure", tags=["pressure-engine"])

_db = None


def set_database(db):
    global _db
    _db = db


def _get_db():
    if _db is None:
        raise RuntimeError("Pressure engine DB not initialized.")
    return _db


COLLECTION = "campaign_pressure_states"


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

async def _load_state(campaign_id: str) -> Optional[CampaignPressureState]:
    db = _get_db()
    doc = await db[COLLECTION].find_one({"campaign_id": campaign_id})
    if not doc:
        return None
    doc.pop("_id", None)
    return CampaignPressureState(**doc)


async def _save_state(state: CampaignPressureState) -> None:
    db = _get_db()
    data = state.model_dump(mode="json")
    await db[COLLECTION].replace_one(
        {"campaign_id": state.campaign_id},
        data,
        upsert=True,
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════
# INIT — create pressure state for a new campaign
# ═══════════════════════════════════════════════════════════════════

class InitPressureRequest(BaseModel):
    campaign_id: str
    world_summary: Optional[str] = ""
    regions: Optional[List[Dict[str, Any]]] = None   # [{id, name, ...pressure axes}]
    wounds: Optional[List[Dict[str, Any]]] = None
    antagonist_seed: Optional[Dict[str, Any]] = None  # partial antagonist fields


@router.post("/init")
async def init_pressure_state(req: InitPressureRequest):
    """
    Initialize the Living Campaign Pressure Engine for a campaign.
    Called after world generation. Seeds wounds, regions, and antagonist.
    """
    existing = await _load_state(req.campaign_id)
    if existing:
        return {"status": "already_initialized", "campaign_id": req.campaign_id}

    # Build regions
    regions: Dict[str, RegionalPressure] = {}
    for r in (req.regions or []):
        region = RegionalPressure(
            region_id=r.get("id", r.get("name", "region_1").lower().replace(" ", "_")),
            region_name=r.get("name", "Unknown Region"),
            crime=r.get("crime", 0.15),
            scarcity=r.get("scarcity", 0.1),
            corruption=r.get("corruption", 0.1),
            cult_activity=r.get("cult_activity", 0.05),
            social_unrest=r.get("social_unrest", 0.1),
            magical_instability=r.get("magical_instability", 0.05),
            war=r.get("war", 0.0),
        )
        regions[region.region_id] = region

    # Default region if none provided
    if not regions:
        regions["starting_region"] = RegionalPressure(
            region_id="starting_region",
            region_name="Starting Region",
        )

    # Build world wounds
    wounds = [WorldWound(**w) for w in (req.wounds or [])]

    # Build antagonist (seeded but in act 1 shadow)
    antagonists: List[Antagonist] = []
    if req.antagonist_seed:
        seed = req.antagonist_seed
        ant = Antagonist(
            campaign_id=req.campaign_id,
            name=seed.get("name", "The Unknown"),
            origin_wound=seed.get("origin_wound", "A forgotten injustice"),
            world_history_connection=seed.get("world_history_connection", "Tied to the old war"),
            ideology=seed.get("ideology", "Order through dominance"),
            flavor=seed.get("flavor", "Cold, methodical, patient"),
            mo=seed.get("mo", "secretive"),
            network_type=seed.get("network_type", "faction"),
            pressure_style=seed.get("pressure_style", "Slow economic strangulation"),
            regional_influence={rid: 0.1 for rid in regions},
        )
        antagonists.append(ant)

    state = CampaignPressureState(
        campaign_id=req.campaign_id,
        wounds=wounds,
        regional_pressures=regions,
        antagonists=antagonists,
    )

    await _save_state(state)
    logger.info(f"🌍 Pressure state initialized for campaign {req.campaign_id}")

    return {
        "status": "initialized",
        "campaign_id": req.campaign_id,
        "regions": len(regions),
        "wounds": len(wounds),
        "antagonists": len(antagonists),
    }


# ═══════════════════════════════════════════════════════════════════
# GET STATE
# ═══════════════════════════════════════════════════════════════════

@router.get("/{campaign_id}")
async def get_pressure_state(campaign_id: str):
    """Full pressure state for a campaign."""
    state = await _load_state(campaign_id)
    if not state:
        raise HTTPException(status_code=404, detail="Pressure state not found. Call /init first.")
    return state.model_dump(mode="json")


@router.get("/{campaign_id}/summary")
async def get_pressure_summary(campaign_id: str):
    """Lightweight summary — designed for frontend dashboard."""
    state = await _load_state(campaign_id)
    if not state:
        raise HTTPException(status_code=404, detail="Pressure state not found.")
    return build_world_pressure_summary(state)


# ═══════════════════════════════════════════════════════════════════
# NARRATIVE TICK — world advances when time passes
# ═══════════════════════════════════════════════════════════════════

@router.post("/tick")
async def pressure_tick(req: PressureTickRequest):
    """
    Advance the world pressure state.
    Triggered by: long_rest, travel, next_day, major_quest_completion.
    """
    state = await _load_state(req.campaign_id)
    if not state:
        raise HTTPException(status_code=404, detail="Pressure state not found. Call /init first.")

    # Count active quests for dampening effect
    db = _get_db()
    try:
        active_quest_count = await db["quests"].count_documents({
            "campaign_id": req.campaign_id,
            "status": {"$in": ["active", "accepted", "in_progress"]},
        })
    except Exception:
        active_quest_count = 0

    updated_state, summary = run_pressure_cycle(
        state,
        trigger=req.trigger,
        region_id=req.region_id,
        active_quest_count=active_quest_count,
    )

    await _save_state(updated_state)

    logger.info(f"⏱️ Pressure tick [{req.trigger}] for {req.campaign_id} — {len(summary['new_hooks'])} new hooks")
    return {
        "status": "ticked",
        "campaign_id": req.campaign_id,
        "trigger": req.trigger,
        "summary": summary,
        "world_state": build_world_pressure_summary(updated_state),
    }


# ═══════════════════════════════════════════════════════════════════
# HOOKS
# ═══════════════════════════════════════════════════════════════════

@router.get("/{campaign_id}/hooks")
async def get_hooks(campaign_id: str, region_id: Optional[str] = None, status: Optional[str] = None):
    """Get all hooks for a campaign, optionally filtered."""
    state = await _load_state(campaign_id)
    if not state:
        raise HTTPException(status_code=404, detail="Pressure state not found.")

    hooks = state.hooks
    if region_id:
        hooks = [h for h in hooks if h.region_id == region_id]
    if status:
        hooks = [h for h in hooks if h.status == status]

    return {
        "hooks": [h.model_dump(mode="json") for h in hooks],
        "total": len(hooks),
    }


class HookNoticeRequest(BaseModel):
    hook_id: str
    character_id: str


@router.post("/{campaign_id}/hooks/notice")
async def notice_hook(campaign_id: str, req: HookNoticeRequest):
    """Player notices a hook — marks it as 'noticed', ready to become a lead."""
    state = await _load_state(campaign_id)
    if not state:
        raise HTTPException(status_code=404, detail="Pressure state not found.")

    hook = next((h for h in state.hooks if h.id == req.hook_id), None)
    if not hook:
        raise HTTPException(status_code=404, detail="Hook not found.")

    hook.status = "noticed"
    await _save_state(state)

    return {"status": "noticed", "hook_id": req.hook_id, "hook": hook.model_dump(mode="json")}


# ═══════════════════════════════════════════════════════════════════
# LEADS
# ═══════════════════════════════════════════════════════════════════

@router.get("/{campaign_id}/leads")
async def get_leads(campaign_id: str, status: Optional[str] = None):
    """Get all leads for a campaign."""
    state = await _load_state(campaign_id)
    if not state:
        raise HTTPException(status_code=404, detail="Pressure state not found.")

    leads = state.leads
    if status:
        leads = [l for l in leads if l.status == status]

    # Attach current importance scores
    return {
        "leads": [
            {**l.model_dump(mode="json"), "importance_score": score_lead_importance(l)}
            for l in leads
        ],
        "total": len(leads),
        "active": len([l for l in leads if l.status == "active"]),
    }


@router.post("/{campaign_id}/leads")
async def create_lead(campaign_id: str, req: LeadCreateRequest):
    """Convert a noticed hook into a trackable lead."""
    state = await _load_state(campaign_id)
    if not state:
        raise HTTPException(status_code=404, detail="Pressure state not found.")

    hook = next((h for h in state.hooks if h.id == req.hook_id), None)
    if not hook:
        raise HTTPException(status_code=404, detail="Hook not found.")

    lead = hook_to_lead(hook, req.character_id, req.player_notes)
    hook.status = "lead_created"

    state.leads.append(lead)
    await _save_state(state)

    return {
        "status": "lead_created",
        "lead": lead.model_dump(mode="json"),
        "hook_id": req.hook_id,
    }


class UpdateLeadRequest(BaseModel):
    status: Optional[str] = None
    player_notes: Optional[str] = None
    linked_quest_id: Optional[str] = None


@router.patch("/{campaign_id}/leads/{lead_id}")
async def update_lead(campaign_id: str, lead_id: str, req: UpdateLeadRequest):
    """Update lead status, notes, or quest link."""
    state = await _load_state(campaign_id)
    if not state:
        raise HTTPException(status_code=404, detail="Pressure state not found.")

    lead = next((l for l in state.leads if l.id == lead_id), None)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found.")

    if req.status:
        lead.status = req.status  # type: ignore
    if req.player_notes is not None:
        lead.player_notes = req.player_notes
    if req.linked_quest_id:
        lead.linked_quest_id = req.linked_quest_id
    lead.updated_at = datetime.now(timezone.utc)
    lead.importance_score = score_lead_importance(lead)

    await _save_state(state)
    return {"status": "updated", "lead": lead.model_dump(mode="json")}


# ═══════════════════════════════════════════════════════════════════
# ANTAGONIST
# ═══════════════════════════════════════════════════════════════════

@router.get("/{campaign_id}/antagonists")
async def get_antagonists(campaign_id: str):
    """Get antagonist state — phase, escalation, revealed info."""
    state = await _load_state(campaign_id)
    if not state:
        raise HTTPException(status_code=404, detail="Pressure state not found.")

    result = []
    for ant in state.antagonists:
        data = ant.model_dump(mode="json")
        # Only expose what should be player-visible
        player_view = {
            "id": data["id"],
            "act_phase": data["act_phase"],
            "escalation_level": data["escalation_level"],
            "public_presence": data["public_presence"],
            "revealed_signature": data["revealed_signature"],
            "recent_operations_count": len(data.get("operations", [])),
        }
        if ant.revealed_signature:
            player_view["reveal_text"] = get_antagonist_reveal_text(ant)
        if ant.revealed_motive:
            player_view["ideology"] = data["ideology"]
        result.append(player_view)

    return {"antagonists": result}


@router.post("/{campaign_id}/antagonist/operate")
async def antagonist_operate(campaign_id: str, req: AntagonistOperationRequest):
    """
    Manually trigger an antagonist operation (for testing or DM override).
    Normally called automatically during pressure tick.
    """
    state = await _load_state(campaign_id)
    if not state:
        raise HTTPException(status_code=404, detail="Pressure state not found.")

    ant = next((a for a in state.antagonists if a.id == req.antagonist_id), None)
    if not ant:
        raise HTTPException(status_code=404, detail="Antagonist not found.")

    operation = generate_antagonist_operation(ant, req.target_region_id, state.player_level)
    ant.operations.append(operation)
    ant.updated_at = datetime.now(timezone.utc)

    # Operation affects region
    if req.target_region_id in state.regional_pressures:
        region = state.regional_pressures[req.target_region_id]
        from services.pressure_engine import _clamp
        region.crime = _clamp(region.crime + operation.escalation_value * 0.3)
        region.faction_activity = _clamp(region.faction_activity + operation.escalation_value * 0.2)

    await _save_state(state)

    return {
        "status": "operation_executed",
        "operation": operation.model_dump(mode="json"),
        "visible_effects": operation.visible_effects,
    }


@router.post("/{campaign_id}/antagonist/{antagonist_id}/advance-phase")
async def advance_antagonist(campaign_id: str, antagonist_id: str):
    """Force-check and advance antagonist phase based on current player level."""
    state = await _load_state(campaign_id)
    if not state:
        raise HTTPException(status_code=404, detail="Pressure state not found.")

    ant = next((a for a in state.antagonists if a.id == antagonist_id), None)
    if not ant:
        raise HTTPException(status_code=404, detail="Antagonist not found.")

    old_phase = ant.act_phase
    updated = advance_antagonist_phase(ant, state.player_level)

    for i, a in enumerate(state.antagonists):
        if a.id == antagonist_id:
            state.antagonists[i] = updated

    await _save_state(state)

    return {
        "old_phase": old_phase,
        "new_phase": updated.act_phase,
        "changed": old_phase != updated.act_phase,
        "reveal_text": get_antagonist_reveal_text(updated),
    }


# ═══════════════════════════════════════════════════════════════════
# CLEANSING
# ═══════════════════════════════════════════════════════════════════

@router.get("/{campaign_id}/cleansing")
async def get_cleansing_events(campaign_id: str, active_only: bool = True):
    """Get cleansing events — active by default."""
    state = await _load_state(campaign_id)
    if not state:
        raise HTTPException(status_code=404, detail="Pressure state not found.")

    events = state.cleansing_events
    if active_only:
        events = [e for e in events if not e.resolved]

    return {
        "cleansing_events": [e.model_dump(mode="json") for e in events],
        "total": len(events),
    }


@router.post("/{campaign_id}/cleansing/{event_id}/resolve")
async def resolve_cleansing(campaign_id: str, event_id: str):
    """Mark a cleansing event as resolved (player intervened or time passed)."""
    state = await _load_state(campaign_id)
    if not state:
        raise HTTPException(status_code=404, detail="Pressure state not found.")

    event = next((e for e in state.cleansing_events if e.id == event_id), None)
    if not event:
        raise HTTPException(status_code=404, detail="Cleansing event not found.")

    event.resolved = True
    await _save_state(state)

    return {"status": "resolved", "event_id": event_id}


# ═══════════════════════════════════════════════════════════════════
# PLAYER LEVEL SYNC — called when player levels up
# ═══════════════════════════════════════════════════════════════════

class LevelSyncRequest(BaseModel):
    campaign_id: str
    player_level: int


@router.post("/sync-level")
async def sync_player_level(req: LevelSyncRequest):
    """
    Sync player level into pressure state.
    Triggers antagonist phase check at levels 3, 5, 9.
    """
    state = await _load_state(req.campaign_id)
    if not state:
        raise HTTPException(status_code=404, detail="Pressure state not found.")

    old_level = state.player_level
    state.player_level = req.player_level
    phase_changes = []

    for i, ant in enumerate(state.antagonists):
        old_phase = ant.act_phase
        updated = advance_antagonist_phase(ant, req.player_level)
        if updated.act_phase != old_phase:
            phase_changes.append({
                "antagonist": updated.name,
                "old_phase": old_phase,
                "new_phase": updated.act_phase,
                "reveal_text": get_antagonist_reveal_text(updated),
            })
        state.antagonists[i] = updated

    await _save_state(state)

    return {
        "status": "synced",
        "old_level": old_level,
        "new_level": req.player_level,
        "phase_changes": phase_changes,
    }
