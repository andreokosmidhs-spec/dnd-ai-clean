"""
Progression Service - XP and leveling system for P3.
Handles XP gain, level-ups, and stat progression.
"""
import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)


# P3.5: Adjusted XP curve - slower early progression
XP_TO_NEXT_LEVEL = {
    1: 150,  # L1 -> L2 (was 100, now ~3 combats instead of 2)
    2: 300,  # L2 -> L3 (was 250, feels more earned)
    3: 500,  # L3 -> L4 (was 450, steady climb)
    4: 800,  # L4 -> L5 (was 700, cap remains at 5)
    5: 0     # Level cap
}


# P3: XP rewards per enemy type
ENEMY_XP_REWARDS = {
    "minor": 20,      # Weak Beast, Low-level Cultist
    "standard": 35,   # Bandit, Guard, Smuggler, Wolf
    "elite": 60,      # Guard Captain, Zealot, Undead Champion
    "mini_boss": 100, # Named quest enemy
    "boss": 150       # Major arc / dungeon boss (can go up to 200)
}


def get_xp_to_next(level: int) -> int:
    """
    Get XP required to reach next level.
    
    Args:
        level: Current character level
    
    Returns:
        XP needed to level up, or 0 if at max level
    """
    return XP_TO_NEXT_LEVEL.get(level, 0)


def get_enemy_archetype_tier(enemy_name: str) -> str:
    """
    Classify enemy into tier for XP rewards.
    
    Args:
        enemy_name: Name of the enemy
    
    Returns:
        Tier string: "minor", "standard", "elite", "mini_boss", or "boss"
    """
    name_lower = enemy_name.lower()
    
    # Boss tier (named, unique)
    if any(word in name_lower for word in ["boss", "lord", "king", "queen", "champion of"]):
        return "boss"
    
    # Mini-boss tier
    if any(word in name_lower for word in ["captain", "zealot", "champion", "elder", "master"]):
        return "elite"
    
    # Elite tier
    if any(word in name_lower for word in ["elite", "veteran", "assassin", "bear", "ogre"]):
        return "elite"
    
    # Minor tier
    if any(word in name_lower for word in ["weak", "young", "sickly", "scout"]):
        return "minor"
    
    # Default: standard
    return "standard"


def calculate_xp_for_enemy(enemy: Dict[str, Any]) -> int:
    """
    Calculate XP reward for defeating an enemy.
    
    Args:
        enemy: Enemy dict with at least 'name' key
    
    Returns:
        XP value
    """
    tier = get_enemy_archetype_tier(enemy.get("name", "Unknown"))
    xp = ENEMY_XP_REWARDS.get(tier, ENEMY_XP_REWARDS["standard"])
    
    logger.info(f"💰 Enemy '{enemy.get('name')}' tier={tier}, XP={xp}")
    
    return xp


def apply_xp_gain(
    character: Dict[str, Any],
    xp_gain: int
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Add XP to character and handle level-ups.
    
    Args:
        character: Character state dict
        xp_gain: Amount of XP to add
    
    Returns:
        Tuple of (updated_character, level_up_events)
        level_up_events is a list like ["LEVEL_UP:2", "LEVEL_UP:3"] if multiple levels gained
    """
    level_up_events = []
    
    # Add XP
    current_xp = character.get("current_xp", 0)
    level = character.get("level", 1)
    
    current_xp += xp_gain
    logger.info(f"✨ Character gained {xp_gain} XP (total: {current_xp})")
    
    # Check for level-ups (handle multiple levels if needed)
    while level < 5:  # Level cap for P3
        xp_to_next = get_xp_to_next(level)
        
        if xp_to_next == 0:  # At max level
            break
        
        if current_xp >= xp_to_next:
            # Level up!
            current_xp -= xp_to_next
            level += 1
            
            logger.info(f"🎉 LEVEL UP! Character is now level {level}")
            
            # Apply level-up bonuses
            character["level"] = level
            character["max_hp"] = character.get("max_hp", 10) + 6  # +6 HP per level
            character["hp"] = character["max_hp"]  # Full heal on level-up
            
            # +1 attack bonus at levels 3 and 5
            if level == 3 or level == 5:
                character["attack_bonus"] = character.get("attack_bonus", 0) + 1
                logger.info(f"⚔️ Attack bonus increased to {character['attack_bonus']}")
            
            # Update xp_to_next for new level
            character["xp_to_next"] = get_xp_to_next(level)
            
            # Record event
            level_up_events.append(f"LEVEL_UP:{level}")
        else:
            # Not enough XP for next level
            break
    
    # Update character XP
    character["current_xp"] = current_xp
    
    # If at max level, store excess XP
    if level >= 5:
        character["xp_to_next"] = 0
        logger.info(f"🏆 Character at max level (5), excess XP stored")
    
    return character, level_up_events


def calculate_non_combat_xp(action_type: str, success: bool = True) -> int:
    """
    Calculate XP reward for non-combat actions.
    
    Args:
        action_type: Type of action ("minor", "moderate", "major")
        success: Whether the action succeeded
    
    Returns:
        XP value
    """
    if not success:
        return 0
    
    rewards = {
        "minor": 10,      # Small success (bribe guard, get info)
        "moderate": 20,   # Clever plan, risk of failure
        "major": 50       # Quest objective, key clue (40-60 range)
    }
    
    return rewards.get(action_type, 10)
