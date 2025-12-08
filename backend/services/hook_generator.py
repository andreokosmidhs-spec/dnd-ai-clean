"""
Quest Hook Generator Service
Generates subtle quest hooks from world_blueprint and active quests
Provides hooks for scene_generator to weave into narration
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def generate_location_hooks(
    location_name: str,
    world_blueprint: Dict[str, Any],
    world_state: Dict[str, Any],
    character_level: int,
    max_hooks: int = 3
) -> List[Dict[str, str]]:
    """
    Generate quest hooks available at current location
    
    Args:
        location_name: Current location name
        world_blueprint: Full world blueprint
        world_state: Current world state
        character_level: Player level (for filtering appropriate hooks)
        max_hooks: Maximum hooks to return
        
    Returns:
        List of hook dicts with: type, description, source
    """
    hooks = []
    
    # 1. Extract hooks from NPCs at this location
    npc_hooks = extract_npc_hooks(location_name, world_blueprint, world_state)
    hooks.extend(npc_hooks)
    
    # 2. Extract hooks from POIs near this location
    poi_hooks = extract_poi_hooks(location_name, world_blueprint)
    hooks.extend(poi_hooks)
    
    # 3. Extract hooks from factions
    faction_hooks = extract_faction_hooks(world_blueprint, world_state)
    hooks.extend(faction_hooks)
    
    # 4. Extract hooks from global threat
    threat_hooks = extract_threat_hooks(world_blueprint, location_name)
    hooks.extend(threat_hooks)
    
    # Filter and limit
    filtered_hooks = [h for h in hooks if is_level_appropriate(h, character_level)]
    
    # Return max_hooks
    return filtered_hooks[:max_hooks]


def extract_npc_hooks(
    location_name: str,
    world_blueprint: Dict[str, Any],
    world_state: Dict[str, Any]
) -> List[Dict[str, str]]:
    """Extract hooks from NPCs at this location"""
    hooks = []
    
    key_npcs = world_blueprint.get("key_npcs", [])
    active_npc_ids = world_state.get("active_npcs", [])
    
    for npc in key_npcs:
        npc_id = npc.get("id", "")
        
        # Only include active NPCs
        if npc_id not in active_npc_ids:
            continue
        
        npc_name = npc.get("name", "")
        npc_role = npc.get("role", "")
        npc_secret = npc.get("secret", "")
        knows_about = npc.get("knows_about", [])
        
        # Generate hook from secret
        if npc_secret and len(npc_secret) > 10:
            hook_desc = f"You notice {npc_name}, a {npc_role}, acting strangely. They glance around nervously."
            hooks.append({
                "type": "observation",
                "description": hook_desc,
                "source": f"npc:{npc_id}",
                "difficulty": "medium"
            })
        
        # Generate hook from knows_about
        if knows_about:
            topic = knows_about[0]  # First topic
            hook_desc = f"You overhear {npc_name} mentioning something about {topic.lower()}."
            hooks.append({
                "type": "rumor",
                "description": hook_desc,
                "source": f"npc:{npc_id}",
                "difficulty": "low"
            })
    
    return hooks


def extract_poi_hooks(
    location_name: str,
    world_blueprint: Dict[str, Any]
) -> List[Dict[str, str]]:
    """Extract hooks from nearby POIs"""
    hooks = []
    
    pois = world_blueprint.get("points_of_interest", [])
    
    for poi in pois[:3]:  # Limit to first 3 POIs
        poi_name = poi.get("name", "")
        poi_type = poi.get("type", "location")
        hidden_function = poi.get("hidden_function", "")
        
        # Skip if no hidden function (no hook)
        if not hidden_function:
            continue
        
        # Generate environmental hook
        hook_desc = f"You hear locals whisper about strange happenings near {poi_name}."
        
        # Customize by type
        if "ruins" in poi_type.lower() or "dungeon" in poi_type.lower():
            hook_desc = f"Smoke or strange lights have been seen near {poi_name} at night."
        elif "tower" in poi_name.lower():
            hook_desc = f"The old {poi_name} shows signs of recent activity despite years of abandonment."
        
        hooks.append({
            "type": "environmental",
            "description": hook_desc,
            "source": f"poi:{poi.get('id', poi_name)}",
            "difficulty": "medium"
        })
    
    return hooks


def extract_faction_hooks(
    world_blueprint: Dict[str, Any],
    world_state: Dict[str, Any]
) -> List[Dict[str, str]]:
    """Extract hooks from faction activities"""
    hooks = []
    
    factions = world_blueprint.get("factions", [])
    
    for faction in factions[:2]:  # Limit to 2 factions
        faction_name = faction.get("name", "")
        public_goal = faction.get("public_goal", "")
        secret_goal = faction.get("secret_goal", "")
        
        # Generate hook from public goal
        if public_goal:
            hook_desc = f"You hear talk of {faction_name} seeking help with their mission: {public_goal.lower()}"
            hooks.append({
                "type": "conversation",
                "description": hook_desc,
                "source": f"faction:{faction_name}",
                "difficulty": "medium"
            })
    
    return hooks


def extract_threat_hooks(
    world_blueprint: Dict[str, Any],
    location_name: str
) -> List[Dict[str, str]]:
    """Extract hooks from global threat"""
    hooks = []
    
    global_threat = world_blueprint.get("global_threat", {})
    threat_name = global_threat.get("name", "")
    early_signs = global_threat.get("early_signs_near_starting_town", [])
    
    if early_signs:
        # Use first early sign as hook
        sign = early_signs[0]
        hook_desc = f"Locals mention unsettling signs: {sign.lower()}"
        hooks.append({
            "type": "rumor",
            "description": hook_desc,
            "source": f"threat:{threat_name}",
            "difficulty": "high"
        })
    
    return hooks


def is_level_appropriate(hook: Dict[str, str], character_level: int) -> bool:
    """Filter hooks by character level"""
    difficulty = hook.get("difficulty", "medium")
    
    if difficulty == "low":
        return True  # Always appropriate
    elif difficulty == "medium":
        return character_level >= 2
    elif difficulty == "high":
        return character_level >= 5
    
    return True
