"""
Scene Refresh Router - Dev Tool for Testing Advanced Hooks
Allows regenerating scene descriptions with new advanced hook system
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.scene_hook_integration import (
    generate_scene_with_advanced_hooks,
    convert_hooks_to_lead_deltas
)
from services.campaign_log_service import CampaignLogService
from models.log_models import CampaignLogDelta

router = APIRouter(prefix="/api/scene", tags=["scene"])
logger = logging.getLogger(__name__)

# Database will be injected
_db = None

def set_database(db: AsyncIOMotorDatabase):
    global _db
    _db = db

def get_db():
    if _db is None:
        raise RuntimeError("Database not initialized")
    return _db


@router.post("/refresh-with-advanced-hooks")
async def refresh_scene_with_advanced_hooks(
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: str = Query(..., description="Character ID"),
    location_name: Optional[str] = Query(None, description="Location name (defaults to current location)")
):
    """
    DEV TOOL: Regenerate current scene with advanced quest hooks
    
    This endpoint:
    1. Loads current game state
    2. Generates new scene description with advanced hooks
    3. Creates leads from the hooks
    4. Updates Campaign Log
    5. Returns new scene data
    
    Use this to test the advanced hook system on existing campaigns
    """
    try:
        db = get_db()
        
        # Load campaign data
        campaign = await db.campaigns.find_one({"campaign_id": campaign_id}, {"_id": 0})
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Load character data
        character = await db.characters.find_one({"character_id": character_id}, {"_id": 0})
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")
        
        # Load world state
        world_state_doc = await db.world_states.find_one({"campaign_id": campaign_id}, {"_id": 0})
        world_state = world_state_doc.get("world_state", {}) if world_state_doc else {}
        
        # Get location
        world_blueprint = campaign.get("world_blueprint", {})
        current_location_name = location_name or world_state.get("current_location") or world_blueprint.get("starting_town", {}).get("name", "Unknown")
        
        # Find location details
        starting_town = world_blueprint.get("starting_town", {})
        if starting_town.get("name") == current_location_name:
            location = starting_town
        else:
            # Try to find in POIs
            pois = world_blueprint.get("points_of_interest", [])
            location = next((poi for poi in pois if poi.get("name") == current_location_name), starting_town)
        
        logger.info(f"🔄 Refreshing scene for {current_location_name} with advanced hooks")
        
        # Generate scene with advanced hooks
        scene_data = await generate_scene_with_advanced_hooks(
            scene_type="return",  # Using "return" since they're already in the location
            location=location,
            character_state=character.get("character_state", {}),
            world_state=world_state,
            world_blueprint=world_blueprint
        )
        
        logger.info(f"✅ Generated scene with {len(scene_data['quest_hooks'])} advanced hooks")
        
        # Convert hooks to leads
        lead_deltas = convert_hooks_to_lead_deltas(
            hooks=scene_data["quest_hooks"],
            location_id=current_location_name,
            scene_id=f"refresh_{campaign_id}"
        )
        
        # Update Campaign Log with new leads
        campaign_log_service = CampaignLogService(db)
        await campaign_log_service.apply_delta(
            campaign_id=campaign_id,
            delta=CampaignLogDelta(leads=lead_deltas),
            character_id=character_id
        )
        
        logger.info(f"✅ Added {len(lead_deltas)} leads to Campaign Log")
        
        return {
            "success": True,
            "message": f"Scene refreshed with {len(scene_data['quest_hooks'])} advanced hooks",
            "scene_data": {
                "location": scene_data["location"],
                "description": scene_data["description"],
                "why_here": scene_data["why_here"]
            },
            "quest_hooks": scene_data["quest_hooks"],
            "leads_created": len(lead_deltas)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Scene refresh failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scene refresh failed: {str(e)}")
