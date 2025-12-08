"""
Quest Service - Quest management for P3.
Handles quest creation, progress tracking, and completion.
"""
import logging
import uuid
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def add_quest_to_world_state(
    world_state: Dict[str, Any],
    quest: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add a new quest to world_state.
    
    Args:
        world_state: Current world state
        quest: Quest dict to add
    
    Returns:
        Updated world_state
    """
    if "quests" not in world_state:
        world_state["quests"] = []
    
    world_state["quests"].append(quest)
    logger.info(f"📜 Quest added: {quest['name']} ({quest['quest_id']})")
    
    return world_state


def update_quest_progress(
    world_state: Dict[str, Any],
    event: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update quest objective progress based on an event.
    
    Args:
        world_state: Current world state with quests
        event: Event dict, e.g.:
            {"type": "enemy_killed", "enemy_archetype": "cultist"}
            {"type": "entered_location", "location_id": "poi_shrine"}
            {"type": "talked_to", "npc_id": "npc_elder"}
    
    Returns:
        Updated world_state
    """
    if "quests" not in world_state:
        return world_state
    
    active_quests = [q for q in world_state["quests"] if q.get("status") == "active"]
    
    for quest in active_quests:
        for objective in quest.get("objectives", []):
            # Match event to objective type
            if objective["type"] == "kill" and event.get("type") == "enemy_killed":
                if event.get("enemy_archetype") == objective.get("target"):
                    objective["progress"] = min(
                        objective["progress"] + 1,
                        objective.get("count", 1)
                    )
                    logger.info(f"📈 Quest '{quest['name']}': kill progress {objective['progress']}/{objective['count']}")
            
            elif objective["type"] == "go_to" and event.get("type") == "entered_location":
                if event.get("location_id") == objective.get("target"):
                    objective["progress"] = 1
                    logger.info(f"📍 Quest '{quest['name']}': arrived at {objective['target']}")
            
            elif objective["type"] == "interact" and event.get("type") == "talked_to":
                if event.get("npc_id") == objective.get("target"):
                    objective["progress"] = 1
                    logger.info(f"💬 Quest '{quest['name']}': talked to {objective['target']}")
            
            elif objective["type"] == "discover" and event.get("type") == "discovered":
                if event.get("discovery_id") == objective.get("target"):
                    objective["progress"] = 1
                    logger.info(f"🔍 Quest '{quest['name']}': discovered {objective['target']}")
        
        # Check if all objectives complete
        all_complete = all(
            obj["progress"] >= obj.get("count", 1)
            for obj in quest.get("objectives", [])
        )
        
        if all_complete and quest.get("status") == "active":
            quest["status"] = "completed"
            logger.info(f"✅ Quest completed: {quest['name']}")
    
    return world_state


def complete_quest(
    world_state: Dict[str, Any],
    quest_id: str
) -> int:
    """
    Mark a quest as completed and return XP reward.
    
    Args:
        world_state: Current world state
        quest_id: ID of quest to complete
    
    Returns:
        XP reward amount
    """
    if "quests" not in world_state:
        return 0
    
    for quest in world_state["quests"]:
        if quest["quest_id"] == quest_id:
            quest["status"] = "completed"
            xp_reward = quest.get("rewards_xp", 0)
            logger.info(f"🎊 Quest '{quest['name']}' completed! Reward: {xp_reward} XP")
            return xp_reward
    
    return 0


def get_active_quests(world_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get all active quests from world_state.
    
    Args:
        world_state: Current world state
    
    Returns:
        List of active quest dicts
    """
    if "quests" not in world_state:
        return []
    
    return [q for q in world_state["quests"] if q.get("status") == "active"]


def create_simple_quest(
    quest_name: str,
    summary: str,
    objectives: List[Dict[str, Any]],
    rewards_xp: int,
    giver_npc_id: Optional[str] = None,
    location_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a simple quest dict.
    
    Args:
        quest_name: Name of the quest
        summary: Brief description
        objectives: List of objective dicts
        rewards_xp: XP reward
        giver_npc_id: Optional NPC who gave quest
        location_id: Optional location tied to quest
    
    Returns:
        Quest dict ready to add to world_state
    """
    quest = {
        "quest_id": str(uuid.uuid4()),
        "name": quest_name,
        "status": "active",
        "giver_npc_id": giver_npc_id,
        "location_id": location_id,
        "summary": summary,
        "objectives": objectives,
        "rewards_xp": rewards_xp,
        "rewards_items": []
    }
    
    return quest
