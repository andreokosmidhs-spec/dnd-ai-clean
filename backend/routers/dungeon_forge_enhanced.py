# This file documents the enhancements made to dungeon_forge.py
# Added robust error handling and verification reads

# Enhancement 1: Verification after insert
# Example pattern added to create_campaign:
"""
async def create_campaign(campaign_id, world_name, world_blueprint):
    try:
        # Insert campaign
        result = await db.campaigns.insert_one(campaign_dict)
        logger.info(f"✅ MongoDB insert: inserted_id={result.inserted_id}")
        
        # VERIFICATION READ
        verify = await db.campaigns.find_one({"campaign_id": campaign_id})
        if verify:
            logger.info(f"✅ VERIFIED: Campaign {campaign_id} exists in MongoDB")
        else:
            logger.error(f"❌ VERIFICATION FAILED: Campaign {campaign_id} not found after insert")
            raise RuntimeError("Campaign insert verification failed")
        
        return campaign_dict
    except Exception as e:
        logger.error(f"❌ create_campaign failed: {e}")
        raise
"""

# Enhancement 2: Explicit error logging
# All insert_one calls now wrapped in try/except with detailed logging

# Enhancement 3: Database connection verification on startup
# Added to server.py startup event to verify DB connectivity
