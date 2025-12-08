"""
Quest System Router
FastAPI endpoints for quest management
"""
import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from models.quest_models import (
    Quest, QuestGenerateRequest, QuestAcceptRequest, QuestAdvanceRequest,
    QuestCompleteRequest, QuestFailRequest, QuestAbandonRequest,
    quest_to_dict, dict_to_quest
)
from services import quest_generator, quest_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quests", tags=["quests"])

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


# ═══════════════════════════════════════════════════════════════
# QUEST GENERATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/generate")
async def generate_quests(request: QuestGenerateRequest):
    """
    Generate new quests for a campaign
    
    Request:
    {
        "campaign_id": "uuid",
        "character_id": "uuid | null",
        "count": 3,
        "filters": {"difficulty": "medium"}
    }
    """
    try:
        db = get_db()
        
        # Load campaign and world_blueprint
        campaign = await db.campaigns.find_one({"campaign_id": request.campaign_id}, {"_id": 0})
        if not campaign:
            return {
                "success": False,
                "data": None,
                "error": {"type": "not_found", "message": "Campaign not found", "details": {}}
            }
        
        world_blueprint = campaign.get("world_blueprint", {})
        
        # Load character if provided
        character_state = None
        if request.character_id:
            character_doc = await db.characters.find_one({"character_id": request.character_id}, {"_id": 0})
            if character_doc:
                character_state = character_doc.get("character_state", {})
        
        # Load world_state
        world_state_doc = await db.world_states.find_one({"campaign_id": request.campaign_id}, {"_id": 0})
        world_state = world_state_doc.get("world_state", {}) if world_state_doc else {}
        
        # Generate quests
        quests = quest_generator.generate_quests(
            world_blueprint=world_blueprint,
            character_state=character_state,
            world_state=world_state,
            campaign_id=request.campaign_id,
            count=request.count
        )
        
        # Save quests to database with verification
        saved_quests = []
        for quest in quests:
            quest_dict = quest_to_dict(quest)
            
            try:
                result = await db.quests.insert_one(quest_dict)
                logger.info(f"✅ Quest created: {quest.name} ({quest.quest_id})")
                
                # Verification read
                verify = await db.quests.find_one({"quest_id": quest.quest_id}, {"_id": 0})
                if not verify:
                    raise RuntimeError(f"Quest insert verification failed: {quest.quest_id}")
                logger.info(f"✅ VERIFIED: Quest {quest.quest_id} exists in MongoDB")
                
                saved_quests.append(quest.dict())
                
            except Exception as e:
                logger.error(f"❌ Failed to save quest {quest.quest_id}: {e}")
                continue
        
        return {
            "success": True,
            "data": {
                "quests": saved_quests,
                "count": len(saved_quests)
            },
            "error": None
        }
        
    except Exception as e:
        logger.error(f"❌ Quest generation failed: {e}")
        return {
            "success": False,
            "data": None,
            "error": {"type": "internal_error", "message": str(e), "details": {}}
        }


# ═══════════════════════════════════════════════════════════════
# QUEST LISTING ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/by-campaign/{campaign_id}")
async def list_quests_by_campaign(
    campaign_id: str,
    status: Optional[str] = None,
    character_id: Optional[str] = None,
    archetype: Optional[str] = None
):
    """
    List quests for a campaign with optional filters
    """
    try:
        db = get_db()
        
        # Build query
        query = {"campaign_id": campaign_id}
        if status:
            query["status"] = status
        if character_id:
            query["character_id"] = character_id
        if archetype:
            query["archetype"] = archetype
        
        # Fetch quests
        quest_docs = await db.quests.find(query, {"_id": 0}).to_list(100)
        
        quests = [dict_to_quest(doc).dict() for doc in quest_docs]
        
        return {
            "success": True,
            "data": {
                "quests": quests,
                "count": len(quests)
            },
            "error": None
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to list quests: {e}")
        return {
            "success": False,
            "data": None,
            "error": {"type": "internal_error", "message": str(e), "details": {}}
        }


@router.get("/by-character/{character_id}")
async def list_quests_by_character(character_id: str):
    """
    List quests assigned to a character
    """
    try:
        db = get_db()
        
        quest_docs = await db.quests.find(
            {"character_id": character_id},
            {"_id": 0}
        ).to_list(100)
        
        quests = [dict_to_quest(doc).dict() for doc in quest_docs]
        
        return {
            "success": True,
            "data": {
                "quests": quests,
                "count": len(quests)
            },
            "error": None
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to list quests by character: {e}")
        return {
            "success": False,
            "data": None,
            "error": {"type": "internal_error", "message": str(e), "details": {}}
        }


@router.get("/{quest_id}")
async def get_quest(quest_id: str):
    """
    Get quest details by ID
    """
    try:
        db = get_db()
        
        quest_doc = await db.quests.find_one({"quest_id": quest_id}, {"_id": 0})
        if not quest_doc:
            return {
                "success": False,
                "data": None,
                "error": {"type": "not_found", "message": "Quest not found", "details": {}}
            }
        
        quest = dict_to_quest(quest_doc)
        
        return {
            "success": True,
            "data": {"quest": quest.dict()},
            "error": None
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get quest: {e}")
        return {
            "success": False,
            "data": None,
            "error": {"type": "internal_error", "message": str(e), "details": {}}
        }


# ═══════════════════════════════════════════════════════════════
# QUEST LIFECYCLE ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/accept")
async def accept_quest(request: QuestAcceptRequest):
    """
    Accept a quest for a character
    """
    try:
        db = get_db()
        
        # Load quest
        quest_doc = await db.quests.find_one({"quest_id": request.quest_id}, {"_id": 0})
        if not quest_doc:
            return {
                "success": False,
                "data": None,
                "error": {"type": "not_found", "message": "Quest not found", "details": {}}
            }
        
        quest = dict_to_quest(quest_doc)
        
        # Validate quest is available
        if quest.status != "available":
            return {
                "success": False,
                "data": None,
                "error": {"type": "invalid_state", "message": f"Quest is {quest.status}, not available", "details": {}}
            }
        
        # Load character to check requirements
        character_doc = await db.characters.find_one({"character_id": request.character_id}, {"_id": 0})
        if not character_doc:
            return {
                "success": False,
                "data": None,
                "error": {"type": "not_found", "message": "Character not found", "details": {}}
            }
        
        character_state = character_doc.get("character_state", {})
        
        # Check requirements
        requirements_met, unmet = quest_manager.check_quest_requirements(quest, character_state)
        if not requirements_met:
            return {
                "success": False,
                "data": None,
                "error": {"type": "requirements_not_met", "message": "Quest requirements not met", "details": {"unmet": unmet}}
            }
        
        # Accept quest
        quest.status = "accepted"
        quest.character_id = request.character_id
        quest.lifecycle_state.accepted_at = datetime.now(timezone.utc)
        quest.updated_at = datetime.now(timezone.utc)
        
        # Update in database
        quest_dict = quest_to_dict(quest)
        result = await db.quests.update_one(
            {"quest_id": request.quest_id},
            {"$set": quest_dict}
        )
        
        logger.info(f"✅ Quest accepted: {quest.name} by character {request.character_id}")
        
        # Verification read
        verify = await db.quests.find_one({"quest_id": request.quest_id}, {"_id": 0})
        if not verify or verify["status"] != "accepted":
            raise RuntimeError(f"Quest accept verification failed: {request.quest_id}")
        
        return {
            "success": True,
            "data": {
                "quest": quest.dict(),
                "status": "accepted"
            },
            "error": None
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to accept quest: {e}")
        return {
            "success": False,
            "data": None,
            "error": {"type": "internal_error", "message": str(e), "details": {}}
        }


@router.post("/advance")
async def advance_quest(request: QuestAdvanceRequest):
    """
    Update quest progress based on game event
    """
    try:
        db = get_db()
        
        # Load quest
        quest_doc = await db.quests.find_one({"quest_id": request.quest_id}, {"_id": 0})
        if not quest_doc:
            return {
                "success": False,
                "data": None,
                "error": {"type": "not_found", "message": "Quest not found", "details": {}}
            }
        
        quest = dict_to_quest(quest_doc)
        
        # Update progress
        updated_quest, updated_objectives = quest_manager.update_quest_progress(quest, request.event)
        
        # Save to database
        quest_dict = quest_to_dict(updated_quest)
        await db.quests.update_one(
            {"quest_id": request.quest_id},
            {"$set": quest_dict}
        )
        
        logger.info(f"✅ Quest progress updated: {updated_quest.name}, {len(updated_objectives)} objectives updated")
        
        return {
            "success": True,
            "data": {
                "quest": updated_quest.dict(),
                "objectives_updated": updated_objectives,
                "quest_completed": updated_quest.status == "completed"
            },
            "error": None
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to advance quest: {e}")
        return {
            "success": False,
            "data": None,
            "error": {"type": "internal_error", "message": str(e), "details": {}}
        }


@router.post("/complete")
async def complete_quest(request: QuestCompleteRequest):
    """
    Complete a quest and apply rewards
    """
    try:
        db = get_db()
        
        # Load quest
        quest_doc = await db.quests.find_one({"quest_id": request.quest_id}, {"_id": 0})
        if not quest_doc:
            return {
                "success": False,
                "data": None,
                "error": {"type": "not_found", "message": "Quest not found", "details": {}}
            }
        
        quest = dict_to_quest(quest_doc)
        
        # Validate quest can be completed
        if not all(obj.completed for obj in quest.objectives):
            return {
                "success": False,
                "data": None,
                "error": {"type": "invalid_state", "message": "Not all objectives completed", "details": {}}
            }
        
        # Load character
        character_doc = await db.characters.find_one({"character_id": request.character_id}, {"_id": 0})
        if not character_doc:
            return {
                "success": False,
                "data": None,
                "error": {"type": "not_found", "message": "Character not found", "details": {}}
            }
        
        character_state = character_doc.get("character_state", {})
        
        # Apply rewards
        rewards_applied = quest_manager.apply_quest_rewards(quest, character_state)
        
        # Update quest status
        quest.status = "completed"
        quest.lifecycle_state.completed_at = datetime.now(timezone.utc)
        quest.updated_at = datetime.now(timezone.utc)
        
        # Save quest
        quest_dict = quest_to_dict(quest)
        await db.quests.update_one({"quest_id": request.quest_id}, {"$set": quest_dict})
        
        # Save character
        await db.characters.update_one(
            {"character_id": request.character_id},
            {"$set": {
                "character_state": character_state,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"🎊 Quest completed: {quest.name}, rewards applied")
        
        return {
            "success": True,
            "data": {
                "quest": quest.dict(),
                "rewards_applied": rewards_applied,
                "character_updates": {
                    "current_xp": character_state.get("current_xp"),
                    "level": character_state.get("level"),
                    "level_up": rewards_applied["level_up"]
                }
            },
            "error": None
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to complete quest: {e}")
        return {
            "success": False,
            "data": None,
            "error": {"type": "internal_error", "message": str(e), "details": {}}
        }


@router.post("/fail")
async def fail_quest(request: QuestFailRequest):
    """
    Mark quest as failed
    """
    try:
        db = get_db()
        
        quest_doc = await db.quests.find_one({"quest_id": request.quest_id}, {"_id": 0})
        if not quest_doc:
            return {
                "success": False,
                "data": None,
                "error": {"type": "not_found", "message": "Quest not found", "details": {}}
            }
        
        quest = dict_to_quest(quest_doc)
        
        quest.status = "failed"
        quest.lifecycle_state.failed_at = datetime.now(timezone.utc)
        quest.updated_at = datetime.now(timezone.utc)
        
        quest_dict = quest_to_dict(quest)
        await db.quests.update_one({"quest_id": request.quest_id}, {"$set": quest_dict})
        
        logger.info(f"❌ Quest failed: {quest.name}, reason: {request.reason}")
        
        return {
            "success": True,
            "data": {
                "quest": quest.dict(),
                "status": "failed",
                "failure_reason": request.reason
            },
            "error": None
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to fail quest: {e}")
        return {
            "success": False,
            "data": None,
            "error": {"type": "internal_error", "message": str(e), "details": {}}
        }


@router.post("/abandon")
async def abandon_quest(request: QuestAbandonRequest):
    """
    Abandon a quest
    """
    try:
        db = get_db()
        
        quest_doc = await db.quests.find_one({"quest_id": request.quest_id}, {"_id": 0})
        if not quest_doc:
            return {
                "success": False,
                "data": None,
                "error": {"type": "not_found", "message": "Quest not found", "details": {}}
            }
        
        quest = dict_to_quest(quest_doc)
        
        # Validate character owns quest
        if quest.character_id != request.character_id:
            return {
                "success": False,
                "data": None,
                "error": {"type": "unauthorized", "message": "Character does not own this quest", "details": {}}
            }
        
        quest.status = "abandoned"
        quest.updated_at = datetime.now(timezone.utc)
        
        quest_dict = quest_to_dict(quest)
        await db.quests.update_one({"quest_id": request.quest_id}, {"$set": quest_dict})
        
        logger.info(f"🚫 Quest abandoned: {quest.name}")
        
        return {
            "success": True,
            "data": {
                "quest": quest.dict(),
                "status": "abandoned"
            },
            "error": None
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to abandon quest: {e}")
        return {
            "success": False,
            "data": None,
            "error": {"type": "internal_error", "message": str(e), "details": {}}
        }
