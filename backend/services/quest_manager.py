"""
Quest Manager Service
Handles quest lifecycle, progress tracking, and state transitions
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from models.quest_models import Quest, QuestObjective

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# QUEST PROGRESS TRACKING
# ═══════════════════════════════════════════════════════════════

def update_quest_progress(
    quest: Quest,
    event: Dict[str, Any]
) -> tuple[Quest, List[Dict[str, Any]]]:
    """
    Update quest objective progress based on event
    
    Args:
        quest: Quest object to update
        event: Event dict with type and target
            Examples:
            - {"type": "enemy_killed", "target": "cultist"}
            - {"type": "entered_location", "target": "poi_ruins"}
            - {"type": "talked_to", "target": "npc_elder"}
            - {"type": "discovered", "target": "secret_passage"}
    
    Returns:
        Tuple of (updated_quest, list_of_updated_objectives)
    """
    event_type = event.get("type")
    event_target = event.get("target")
    
    updated_objectives = []
    
    # Only update if quest is accepted or in_progress
    if quest.status not in ["accepted", "in_progress"]:
        return quest, updated_objectives
    
    for objective in quest.objectives:
        # Skip completed objectives
        if objective.completed:
            continue
        
        # Match event to objective
        matched = False
        
        if objective.type == "kill" and event_type == "enemy_killed":
            if objective.target == event_target:
                objective.progress = min(objective.progress + 1, objective.count)
                matched = True
                logger.info(f"📈 Quest '{quest.name}': kill progress {objective.progress}/{objective.count}")
        
        elif objective.type == "go_to" and event_type == "entered_location":
            if objective.target == event_target:
                objective.progress = 1
                matched = True
                logger.info(f"📍 Quest '{quest.name}': arrived at {objective.target}")
        
        elif objective.type == "interact" and event_type == "talked_to":
            if objective.target == event_target:
                objective.progress = 1
                matched = True
                logger.info(f"💬 Quest '{quest.name}': talked to {objective.target}")
        
        elif objective.type == "discover" and event_type == "discovered":
            if objective.target == event_target:
                objective.progress = 1
                matched = True
                logger.info(f"🔍 Quest '{quest.name}': discovered {objective.target}")
        
        elif objective.type == "deliver" and event_type == "delivered":
            if objective.target == event_target:
                objective.progress = 1
                matched = True
                logger.info(f"📦 Quest '{quest.name}': delivered to {objective.target}")
        
        elif objective.type == "investigate" and event_type == "clue_found":
            if objective.target == event_target:
                objective.progress = min(objective.progress + 1, objective.count)
                matched = True
                logger.info(f"🔎 Quest '{quest.name}': clue progress {objective.progress}/{objective.count}")
        
        # Check if objective completed
        if matched and objective.progress >= objective.count:
            objective.completed = True
            logger.info(f"✅ Quest objective completed: {objective.description}")
            updated_objectives.append(objective.dict())
        elif matched:
            updated_objectives.append(objective.dict())
    
    # If quest was 'accepted', transition to 'in_progress' on first progress
    if quest.status == "accepted" and updated_objectives:
        quest.status = "in_progress"
        quest.lifecycle_state.started_at = datetime.now(timezone.utc)
        logger.info(f"🎬 Quest started: {quest.name}")
    
    # Check if all objectives completed
    if all(obj.completed for obj in quest.objectives):
        quest.status = "completed"
        quest.lifecycle_state.completed_at = datetime.now(timezone.utc)
        logger.info(f"🎊 Quest completed: {quest.name}")
    
    quest.updated_at = datetime.now(timezone.utc)
    
    return quest, updated_objectives


def check_quest_failure_conditions(
    quest: Quest,
    world_state: Dict[str, Any]
) -> tuple[bool, Optional[str]]:
    """
    Check if quest should fail based on failure conditions
    
    Args:
        quest: Quest to check
        world_state: Current world state
    
    Returns:
        Tuple of (should_fail, failure_reason)
    """
    if not quest.failure_conditions:
        return False, None
    
    for condition in quest.failure_conditions:
        # Check NPC killed condition
        if "_killed" in condition:
            npc_id = condition.replace("_killed", "")
            # Check if NPC is in permanent enemies or world_state indicates death
            # This would require more integration with world_state tracking
            pass
        
        # Check faction hostile condition
        if "_hostile" in condition:
            faction_id = condition.replace("_hostile", "")
            if world_state.get("city_hostile") or faction_id in world_state.get("permanent_enemies", []):
                return True, condition
        
        # Check time limit exceeded
        if "time_limit_exceeded" in condition:
            if quest.time_limit.type != "none" and quest.time_limit.started_at:
                # Calculate elapsed time (this would need proper time tracking)
                pass
    
    return False, None


def check_quest_requirements(
    quest: Quest,
    character_state: Dict[str, Any]
) -> tuple[bool, List[str]]:
    """
    Check if character meets quest requirements
    
    Args:
        quest: Quest to check requirements for
        character_state: Character state
    
    Returns:
        Tuple of (requirements_met, list_of_unmet_requirements)
    """
    unmet = []
    
    # Check level requirement
    char_level = character_state.get("level", 1)
    if char_level < quest.requirements.min_level:
        unmet.append(f"Level {quest.requirements.min_level} required (you are level {char_level})")
    
    # Check required items
    char_inventory = character_state.get("inventory", [])
    for required_item in quest.requirements.required_items:
        if required_item not in char_inventory:
            unmet.append(f"Missing required item: {required_item}")
    
    # Check reputation requirements
    char_reputation = character_state.get("reputation", {})
    for faction_id, min_rep in quest.requirements.reputation_gates.items():
        current_rep = char_reputation.get(faction_id, 0)
        if current_rep < min_rep:
            unmet.append(f"Insufficient reputation with {faction_id} (need {min_rep}, have {current_rep})")
    
    return len(unmet) == 0, unmet


# ═══════════════════════════════════════════════════════════════
# QUEST REWARDS
# ═══════════════════════════════════════════════════════════════

def apply_quest_rewards(
    quest: Quest,
    character_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply quest rewards to character
    
    Args:
        quest: Completed quest
        character_state: Character state to update
    
    Returns:
        Dict with reward application summary
    """
    rewards_applied = {
        "xp": 0,
        "gold": 0,
        "items": [],
        "reputation": {},
        "level_up": False,
        "unlocks": []
    }
    
    # Apply XP
    if quest.rewards.xp > 0:
        character_state["current_xp"] = character_state.get("current_xp", 0) + quest.rewards.xp
        rewards_applied["xp"] = quest.rewards.xp
        logger.info(f"💎 Awarded {quest.rewards.xp} XP")
        
        # Check for level up
        xp_to_next = character_state.get("xp_to_next", 100)
        if character_state["current_xp"] >= xp_to_next:
            character_state["level"] = character_state.get("level", 1) + 1
            character_state["current_xp"] -= xp_to_next
            character_state["xp_to_next"] = int(xp_to_next * 1.5)  # Scale XP requirement
            rewards_applied["level_up"] = True
            logger.info(f"🎉 LEVEL UP! Now level {character_state['level']}")
    
    # Apply gold
    if quest.rewards.gold > 0:
        character_state["gold"] = character_state.get("gold", 0) + quest.rewards.gold
        rewards_applied["gold"] = quest.rewards.gold
        logger.info(f"💰 Awarded {quest.rewards.gold} gold")
    
    # Apply items
    if quest.rewards.items:
        inventory = character_state.get("inventory", [])
        for item in quest.rewards.items:
            inventory.append(item)
            rewards_applied["items"].append(item)
            logger.info(f"🎁 Received item: {item}")
        character_state["inventory"] = inventory
    
    # Apply reputation
    if quest.rewards.reputation:
        reputation = character_state.get("reputation", {})
        for faction_id, rep_change in quest.rewards.reputation.items():
            reputation[faction_id] = reputation.get(faction_id, 0) + rep_change
            rewards_applied["reputation"][faction_id] = rep_change
            logger.info(f"📊 Reputation with {faction_id}: {rep_change:+d}")
        character_state["reputation"] = reputation
    
    # Track unlocks (for future use)
    if quest.rewards.unlocks:
        rewards_applied["unlocks"] = quest.rewards.unlocks
    
    return rewards_applied


# ═══════════════════════════════════════════════════════════════
# QUEST FILTERING
# ═══════════════════════════════════════════════════════════════

def filter_quests(
    quests: List[Quest],
    status: Optional[str] = None,
    character_id: Optional[str] = None,
    archetype: Optional[str] = None,
    difficulty: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> List[Quest]:
    """
    Filter quests based on criteria
    
    Args:
        quests: List of quests to filter
        status: Filter by status
        character_id: Filter by character_id
        archetype: Filter by archetype
        difficulty: Filter by difficulty
        tags: Filter by tags (quest must have at least one matching tag)
    
    Returns:
        Filtered list of quests
    """
    filtered = quests
    
    if status:
        filtered = [q for q in filtered if q.status == status]
    
    if character_id:
        filtered = [q for q in filtered if q.character_id == character_id]
    
    if archetype:
        filtered = [q for q in filtered if q.archetype == archetype]
    
    if difficulty:
        filtered = [q for q in filtered if q.difficulty == difficulty]
    
    if tags:
        filtered = [q for q in filtered if any(tag in q.tags for tag in tags)]
    
    return filtered
