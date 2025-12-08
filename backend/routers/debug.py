"""
Debug Router - MongoDB Diagnostic Endpoints
Provides visibility into database state for troubleshooting
"""
import logging
from fastapi import APIRouter
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debug", tags=["debug"])

# Database will be injected from main app
_db = None

def set_database(db):
    """Set the MongoDB database instance"""
    global _db
    _db = db

def get_db():
    """Get the MongoDB database instance"""
    if _db is None:
        raise RuntimeError("Database not initialized")
    return _db

@router.get("/db")
async def debug_database():
    """
    Debug endpoint showing MongoDB state
    Returns collection counts and sample documents
    """
    try:
        db = get_db()
        
        # Get collection counts
        campaigns_count = await db.campaigns.count_documents({})
        characters_count = await db.characters.count_documents({})
        world_states_count = await db.world_states.count_documents({})
        
        # Get sample documents
        sample_campaign = await db.campaigns.find_one({}, sort=[('_id', -1)])
        sample_character = await db.characters.find_one({}, sort=[('_id', -1)])
        
        # Get database name
        db_name = db.name
        
        return {
            "success": True,
            "data": {
                "database_name": db_name,
                "collections": {
                    "campaigns": campaigns_count,
                    "characters": characters_count,
                    "world_states": world_states_count
                },
                "samples": {
                    "latest_campaign_id": sample_campaign.get('campaign_id') if sample_campaign else None,
                    "latest_character_id": sample_character.get('character_id') if sample_character else None
                }
            },
            "error": None
        }
    except Exception as e:
        logger.error(f"Debug endpoint error: {e}")
        return {
            "success": False,
            "data": None,
            "error": {
                "type": "internal_error",
                "message": str(e),
                "details": {}
            }
        }
