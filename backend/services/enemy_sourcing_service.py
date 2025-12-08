"""
Enemy Sourcing Service - Context-aware enemy selection for combat.
Binds enemies to world_blueprint, world_state, and location context.
"""
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


# Enemy archetype templates by context
ENEMY_ARCHETYPES = {
    "guard": [
        {"name": "Town Guard", "hp": 18, "ac": 16, "attack_bonus": 4, "damage_die": "1d8+2"},
        {"name": "Guard Captain", "hp": 25, "ac": 17, "attack_bonus": 5, "damage_die": "1d8+3"},
    ],
    "bandit": [
        {"name": "Bandit", "hp": 15, "ac": 13, "attack_bonus": 3, "damage_die": "1d6+1"},
        {"name": "Thug", "hp": 12, "ac": 12, "attack_bonus": 2, "damage_die": "1d4+1"},
    ],
    "cultist": [
        {"name": "Cultist", "hp": 14, "ac": 12, "attack_bonus": 3, "damage_die": "1d6"},
        {"name": "Zealot", "hp": 16, "ac": 13, "attack_bonus": 3, "damage_die": "1d6+1"},
    ],
    "undead": [
        {"name": "Skeleton", "hp": 13, "ac": 13, "attack_bonus": 4, "damage_die": "1d6+2"},
        {"name": "Zombie", "hp": 22, "ac": 8, "attack_bonus": 3, "damage_die": "1d6+1"},
    ],
    "beast": [
        {"name": "Wolf", "hp": 11, "ac": 13, "attack_bonus": 4, "damage_die": "2d4+2"},
        {"name": "Bear", "hp": 34, "ac": 11, "attack_bonus": 5, "damage_die": "1d8+4"},
    ],
    "criminal": [
        {"name": "Smuggler", "hp": 14, "ac": 14, "attack_bonus": 3, "damage_die": "1d6+1"},
        {"name": "Assassin", "hp": 16, "ac": 15, "attack_bonus": 4, "damage_die": "1d6+2"},
    ],
}


def map_location_to_enemy_type(
    world_blueprint: Dict[str, Any],
    world_state: Dict[str, Any]
) -> str:
    """
    Determine enemy archetype based on current location and world context.
    
    Returns:
        Enemy archetype key (e.g., "guard", "bandit", "cultist")
    """
    current_location = world_state.get("current_location", "").lower()
    world_tone = world_blueprint.get("world_core", {}).get("tone", "").lower()
    
    # Check POIs for context
    pois = world_blueprint.get("points_of_interest", [])
    location_poi = None
    for poi in pois:
        if poi.get("name", "").lower() == current_location:
            location_poi = poi
            break
    
    # Map based on POI type or location keywords
    if location_poi:
        poi_type = location_poi.get("type", "").lower()
        poi_name = location_poi.get("name", "").lower()
        
        # Religious sites
        if any(word in poi_type or word in poi_name for word in ["shrine", "temple", "altar", "sacred"]):
            return "cultist"
        
        # Military/guard locations
        if any(word in poi_type or word in poi_name for word in ["barracks", "garrison", "guard", "fortress"]):
            return "guard"
        
        # Criminal areas
        if any(word in poi_type or word in poi_name for word in ["tavern", "dock", "alley", "market", "underground"]):
            return "criminal"
        
        # Wilderness/ruins
        if any(word in poi_type or word in poi_name for word in ["forest", "wild", "ruin", "cave", "tomb"]):
            if "dark" in world_tone or "undead" in world_tone:
                return "undead"
            return "beast"
    
    # Fallback based on world tone
    if "dark" in world_tone or "gothic" in world_tone:
        return "undead"
    
    # Default fallback
    return "bandit"


def scale_enemy_for_level(base_enemy: Dict[str, Any], character_level: int) -> Dict[str, Any]:
    """
    Scale enemy stats based on character level (P3).
    
    Args:
        base_enemy: Base enemy template
        character_level: Player's current level
    
    Returns:
        Scaled enemy dict
    """
    # Make a copy to avoid mutating the template
    enemy = base_enemy.copy()
    
    # Scale HP: base_hp + (level - 1) * 3
    # Cap at base + 4*3 (assuming max level 5)
    hp_bonus = min((character_level - 1) * 3, 4 * 3)
    enemy["hp"] = enemy["hp"] + hp_bonus
    enemy["max_hp"] = enemy["hp"]
    
    # Scale attack bonus: base + floor((level - 1) / 2)
    # Cap at +2
    attack_bonus_increase = min((character_level - 1) // 2, 2)
    enemy["attack_bonus"] = enemy["attack_bonus"] + attack_bonus_increase
    
    if character_level > 1:
        logger.info(f"📈 Scaled {enemy['name']}: HP +{hp_bonus}, Attack +{attack_bonus_increase} for level {character_level}")
    
    return enemy


def select_enemies_for_location(
    world_blueprint: Dict[str, Any],
    world_state: Dict[str, Any],
    character_level: int = 1
) -> List[Dict[str, Any]]:
    """
    Select appropriate enemies based on world context and scale them for character level (P3).
    
    Args:
        world_blueprint: The static world definition
        world_state: Current mutable world state
        character_level: Player level (for scaling)
    
    Returns:
        List of scaled enemy template dictionaries
    """
    try:
        # Determine enemy archetype
        enemy_type = map_location_to_enemy_type(world_blueprint, world_state)
        
        logger.info(f"🎯 Enemy sourcing: location={world_state.get('current_location')}, type={enemy_type}, player_level={character_level}")
        
        # Get templates for this type
        templates = ENEMY_ARCHETYPES.get(enemy_type, ENEMY_ARCHETYPES["bandit"])
        
        # Select 1-2 enemies
        count = min(2, len(templates))
        selected = templates[:count]
        
        # P3: Scale enemies based on character level
        scaled_enemies = [scale_enemy_for_level(enemy, character_level) for enemy in selected]
        
        logger.info(f"✅ Selected {count} enemies: {[e['name'] for e in scaled_enemies]}")
        
        return scaled_enemies
        
    except Exception as e:
        logger.error(f"❌ Enemy sourcing failed: {e}, using fallback")
        # Safe fallback with scaling
        fallback = [
            {"name": "Bandit", "hp": 15, "ac": 13, "attack_bonus": 3, "damage_die": "1d6+1"},
            {"name": "Thug", "hp": 12, "ac": 12, "attack_bonus": 2, "damage_die": "1d4"}
        ]
        return [scale_enemy_for_level(e, character_level) for e in fallback]


def get_enemies_for_faction(
    faction_name: str,
    world_blueprint: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Get enemies associated with a specific faction.
    
    Args:
        faction_name: Name of the faction
        world_blueprint: The world definition
    
    Returns:
        List of enemy templates for that faction
    """
    factions = world_blueprint.get("factions", [])
    faction = None
    
    for f in factions:
        if f.get("name", "").lower() == faction_name.lower():
            faction = f
            break
    
    if not faction:
        return ENEMY_ARCHETYPES["bandit"][:2]
    
    faction_type = faction.get("type", "").lower()
    
    # Map faction type to enemy archetype
    if "military" in faction_type or "order" in faction_type:
        return ENEMY_ARCHETYPES["guard"][:2]
    elif "cult" in faction_type or "religious" in faction_type:
        return ENEMY_ARCHETYPES["cultist"][:2]
    elif "criminal" in faction_type or "shadow" in faction_type:
        return ENEMY_ARCHETYPES["criminal"][:2]
    
    return ENEMY_ARCHETYPES["bandit"][:2]
