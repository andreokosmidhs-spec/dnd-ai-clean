"""
Campaign Log API Router
Endpoints for accessing and managing the player's campaign log.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime

from models.log_models import (
    GetLogRequest,
    GetLogSummaryResponse,
    GetEntityDetailRequest,
    CampaignLog
)
from services.campaign_log_service import CampaignLogService

router = APIRouter(prefix="/api/campaign/log", tags=["campaign_log"])

# Database will be injected from main app
_db = None

def set_database(db):
    """Set the MongoDB database instance"""
    global _db
    _db = db

def get_db():
    """Get the MongoDB database instance"""
    if _db is None:
        raise RuntimeError("Database not initialized. Call set_database() first.")
    return _db


@router.get("/summary")
async def get_log_summary(
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID")
):
    """
    Get summary of the campaign log (counts per category).
    
    Returns:
    {
      "campaign_id": "...",
      "counts": {
        "locations": 5,
        "npcs": 12,
        "factions": 3,
        "quests": 4,
        "rumors": 8,
        "items": 6,
        "decisions": 7
      },
      "last_updated": "2025-01-15T10:30:00Z"
    }
    """
    db = get_db()
    service = CampaignLogService(db)
    
    summary = await service.get_log_summary(campaign_id, character_id)
    return summary


@router.get("/full")
async def get_full_log(
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID")
):
    """
    Get the complete campaign log with all entries.
    
    Returns: CampaignLog object with all categories populated
    """
    db = get_db()
    service = CampaignLogService(db)
    
    log = await service.get_log(campaign_id, character_id)
    if not log:
        raise HTTPException(status_code=404, detail="Campaign log not found")
    
    return log


@router.get("/locations")
async def get_all_locations(
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID")
):
    """Get all known locations"""
    db = get_db()
    service = CampaignLogService(db)
    
    log = await service.get_log(campaign_id, character_id)
    if not log:
        return {"locations": []}
    
    return {"locations": list(log.locations.values())}


@router.get("/locations/{location_id}")
async def get_location_detail(
    location_id: str,
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID")
):
    """Get detailed information about a specific location"""
    db = get_db()
    service = CampaignLogService(db)
    
    entity = await service.get_entity(campaign_id, "location", location_id, character_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Location '{location_id}' not found in campaign log")
    
    return entity


@router.get("/npcs")
async def get_all_npcs(
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID")
):
    """Get all known NPCs"""
    db = get_db()
    service = CampaignLogService(db)
    
    log = await service.get_log(campaign_id, character_id)
    if not log:
        return {"npcs": []}
    
    return {"npcs": list(log.npcs.values())}


@router.get("/npcs/{npc_id}")
async def get_npc_detail(
    npc_id: str,
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID")
):
    """Get detailed information about a specific NPC"""
    db = get_db()
    service = CampaignLogService(db)
    
    entity = await service.get_entity(campaign_id, "npc", npc_id, character_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"NPC '{npc_id}' not found in campaign log")
    
    return entity


@router.get("/factions")
async def get_all_factions(
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID")
):
    """Get all known factions"""
    db = get_db()
    service = CampaignLogService(db)
    
    log = await service.get_log(campaign_id, character_id)
    if not log:
        return {"factions": []}
    
    return {"factions": list(log.factions.values())}


@router.get("/factions/{faction_id}")
async def get_faction_detail(
    faction_id: str,
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID")
):
    """Get detailed information about a specific faction"""
    db = get_db()
    service = CampaignLogService(db)
    
    entity = await service.get_entity(campaign_id, "faction", faction_id, character_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Faction '{faction_id}' not found in campaign log")
    
    return entity


@router.get("/quests")
async def get_all_quests(
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID")
):
    """Get all known quests"""
    db = get_db()
    service = CampaignLogService(db)
    
    log = await service.get_log(campaign_id, character_id)
    if not log:
        return {"quests": []}
    
    return {"quests": list(log.quests.values())}


@router.get("/quests/{quest_id}")
async def get_quest_detail(
    quest_id: str,
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID")
):
    """Get detailed information about a specific quest"""
    db = get_db()
    service = CampaignLogService(db)
    
    entity = await service.get_entity(campaign_id, "quest", quest_id, character_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Quest '{quest_id}' not found in campaign log")
    
    return entity


@router.get("/rumors")
async def get_all_rumors(
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID")
):
    """Get all known rumors"""
    db = get_db()
    service = CampaignLogService(db)
    
    log = await service.get_log(campaign_id, character_id)
    if not log:
        return {"rumors": []}
    
    return {"rumors": list(log.rumors.values())}


@router.get("/items")
async def get_all_items(
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID")
):
    """Get all known items"""
    db = get_db()
    service = CampaignLogService(db)
    
    log = await service.get_log(campaign_id, character_id)
    if not log:
        return {"items": []}
    
    return {"items": list(log.items.values())}


@router.get("/decisions")
async def get_all_decisions(
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID")
):
    """Get all recorded decisions"""
    db = get_db()
    service = CampaignLogService(db)
    
    log = await service.get_log(campaign_id, character_id)
    if not log:
        return {"decisions": []}
    
    return {"decisions": list(log.decisions.values())}


@router.get("/leads")
async def get_all_leads(
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID"),
    status: Optional[str] = Query(None, description="Filter by status (unexplored, active, resolved, abandoned)")
):
    """
    Get all leads (quest hooks).
    Optionally filter by status.
    
    Returns: { "leads": [...] }
    """
    db = get_db()
    service = CampaignLogService(db)
    
    log = await service.get_log(campaign_id, character_id)
    if not log:
        return {"leads": []}
    
    # Get all leads
    leads = list(log.leads.values())
    
    # Filter by status if provided
    if status:
        leads = [lead for lead in leads if lead.status == status]
    
    return {"leads": leads}


@router.get("/leads/open")
async def get_open_leads(
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID"),
    include_abandoned: bool = Query(False, description="Include abandoned leads")
):
    """
    Get all open leads (not resolved).
    By default excludes abandoned leads unless include_abandoned=true.
    
    Returns: { "leads": [...] }
    """
    db = get_db()
    service = CampaignLogService(db)
    
    leads = await service.list_open_leads(campaign_id, character_id, include_abandoned)
    
    return {"leads": leads}


@router.get("/leads/{lead_id}")
async def get_lead_detail(
    lead_id: str,
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID")
):
    """Get detailed information about a specific lead"""
    db = get_db()
    service = CampaignLogService(db)
    
    lead = await service.get_lead(campaign_id, lead_id, character_id)
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead '{lead_id}' not found in campaign log")
    
    return lead


@router.patch("/leads/{lead_id}/status")
async def update_lead_status(
    lead_id: str,
    campaign_id: str = Query(..., description="Campaign ID"),
    new_status: str = Query(..., description="New status (unexplored, active, resolved, abandoned)"),
    character_id: Optional[str] = Query(None, description="Optional character ID"),
    player_notes: Optional[str] = Query(None, description="Optional player notes to append")
):
    """
    Update the status of a lead.
    
    Valid statuses: unexplored, active, resolved, abandoned
    """
    # Validate status
    valid_statuses = ["unexplored", "active", "resolved", "abandoned"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{new_status}'. Must be one of: {', '.join(valid_statuses)}"
        )
    
    db = get_db()
    service = CampaignLogService(db)
    
    lead = await service.update_lead_status(
        campaign_id=campaign_id,
        lead_id=lead_id,
        new_status=new_status,
        character_id=character_id,
        player_notes=player_notes
    )
    
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead '{lead_id}' not found in campaign log")
    
    return {
        "success": True,
        "lead": lead,
        "message": f"Lead status updated to '{new_status}'"
    }
