"""
TARGET RESOLVER Service - Resolves player combat targets with priority-based logic.

Target Resolution Priority:
1. Explicit client_target_id from frontend (if provided)
2. Enemy in active combat_state (if in combat)
3. NPC in world_state.active_npcs (convert to enemy if hostile action)
4. None - requires DM clarification
"""
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


def resolve_target(
    player_action: str,
    client_target_id: Optional[str],
    combat_state: Optional[Dict[str, Any]],
    world_state: Dict[str, Any],
    world_blueprint: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Resolve the target of a player action using priority-based logic.
    
    Args:
        player_action: The player's action text
        client_target_id: Explicit target ID from frontend (highest priority)
        combat_state: Current combat state (if any)
        world_state: Current mutable world state
        world_blueprint: Static world blueprint
    
    Returns:
        {
            "status": "single_target" | "needs_clarification" | "no_target_found" | "plot_armor_blocked",
            "target": dict or None,  # CombatParticipant-compatible dict
            "target_type": "enemy" | "npc" | "none",
            "target_id": str or None,
            "target_name": str or None,
            "ambiguous_options": list,  # List of possible targets when ambiguous
            "clarification_reason": str or None,
            "plot_armor_reason": str or None
        }
    """
    logger.info(f"🎯 Resolving target for action: '{player_action[:50]}...'")
    logger.info(f"   client_target_id: {client_target_id}")
    logger.info(f"   combat_active: {combat_state is not None and not combat_state.get('combat_over', True)}")
    
    # Priority 1: Explicit client_target_id
    if client_target_id:
        logger.info(f"🎯 Priority 1: Checking explicit client_target_id='{client_target_id}'")
        
        # Check if it's an enemy ID in combat
        if combat_state and not combat_state.get('combat_over', True):
            for enemy in combat_state.get('enemies', []):
                if enemy.get('id') == client_target_id and enemy.get('hp', 0) > 0:
                    logger.info(f"✅ Found enemy target: {enemy['name']}")
                    return {
                        "status": "single_target",
                        "target": enemy,
                        "target_type": "enemy",
                        "target_id": enemy['id'],
                        "target_name": enemy['name'],
                        "ambiguous_options": [],
                        "clarification_reason": None,
                        "plot_armor_reason": None
                    }
        
        # Check if it's an NPC ID in world_state
        active_npcs = world_state.get('active_npcs', [])
        for npc_id in active_npcs:
            npc = find_npc_by_id(npc_id, world_blueprint)
            if npc and npc.get('id') == client_target_id:
                logger.info(f"✅ Found NPC target: {npc['name']}")
                return {
                    "status": "single_target",
                    "target": npc,
                    "target_type": "npc",
                    "target_id": npc['id'],
                    "target_name": npc['name'],
                    "ambiguous_options": [],
                    "clarification_reason": None,
                    "plot_armor_reason": None
                }
        
        logger.warning(f"⚠️ client_target_id '{client_target_id}' not found in enemies or NPCs")
    
    # Priority 1.5: Named target in action text (check before defaulting to single enemy)
    named_target = extract_named_target_from_text(player_action, world_state, world_blueprint, combat_state)
    if named_target:
        logger.info(f"🎯 Priority 1.5: Found named target in text: {named_target['name']}")
        return {
            "status": "single_target",
            "target": named_target,
            "target_type": named_target.get('target_type', 'npc'),
            "target_id": named_target.get('id'),
            "target_name": named_target.get('name'),
            "ambiguous_options": [],
            "clarification_reason": None,
            "plot_armor_reason": None
        }
    
    # Priority 2: Enemy in active combat_state
    if combat_state and not combat_state.get('combat_over', True):
        alive_enemies = [e for e in combat_state.get('enemies', []) if e.get('hp', 0) > 0]
        
        if len(alive_enemies) == 1:
            # Only one enemy, auto-target
            enemy = alive_enemies[0]
            logger.info(f"🎯 Priority 2: Auto-targeting sole enemy: {enemy['name']}")
            return {
                "status": "single_target",
                "target": enemy,
                "target_type": "enemy",
                "target_id": enemy['id'],
                "target_name": enemy['name'],
                "ambiguous_options": [],
                "clarification_reason": None,
                "plot_armor_reason": None
            }
        elif len(alive_enemies) > 1:
            # Multiple enemies, try to parse from action text
            parsed_enemy = parse_enemy_from_action(player_action, alive_enemies)
            if parsed_enemy:
                logger.info(f"🎯 Priority 2: Parsed enemy from action text: {parsed_enemy['name']}")
                return {
                    "status": "single_target",
                    "target": parsed_enemy,
                    "target_type": "enemy",
                    "target_id": parsed_enemy['id'],
                    "target_name": parsed_enemy['name'],
                    "ambiguous_options": [],
                    "clarification_reason": None,
                    "plot_armor_reason": None
                }
            else:
                # Ambiguous, need clarification
                logger.info(f"❓ Priority 2: Multiple enemies, need clarification")
                return {
                    "status": "needs_clarification",
                    "target": None,
                    "target_type": "none",
                    "target_id": None,
                    "target_name": None,
                    "ambiguous_options": [{"id": e['id'], "name": e['name']} for e in alive_enemies],
                    "clarification_reason": f"Multiple enemies present. Which one do you attack: {', '.join(e['name'] for e in alive_enemies)}?",
                    "plot_armor_reason": None
                }
    
    # Priority 3: NPC in world_state (only if hostile action detected)
    if is_hostile_action(player_action):
        logger.info(f"🎯 Priority 3: Hostile action detected, checking NPCs...")
        active_npcs = world_state.get('active_npcs', [])
        
        if len(active_npcs) == 1:
            # Only one NPC present
            npc_id = active_npcs[0]
            npc = find_npc_by_id(npc_id, world_blueprint)
            if npc:
                logger.info(f"🎯 Priority 3: Auto-targeting sole NPC: {npc['name']}")
                return {
                    "status": "single_target",
                    "target": npc,
                    "target_type": "npc",
                    "target_id": npc['id'],
                    "target_name": npc['name'],
                    "ambiguous_options": [],
                    "clarification_reason": None,
                    "plot_armor_reason": None
                }
        elif len(active_npcs) > 1:
            # Multiple NPCs, try to parse from action text
            npc_list = [find_npc_by_id(npc_id, world_blueprint) for npc_id in active_npcs]
            npc_list = [npc for npc in npc_list if npc is not None]
            
            parsed_npc = parse_npc_from_action(player_action, npc_list)
            if parsed_npc:
                logger.info(f"🎯 Priority 3: Parsed NPC from action text: {parsed_npc['name']}")
                return {
                    "status": "single_target",
                    "target": parsed_npc,
                    "target_type": "npc",
                    "target_id": parsed_npc['id'],
                    "target_name": parsed_npc['name'],
                    "ambiguous_options": [],
                    "clarification_reason": None,
                    "plot_armor_reason": None
                }
            else:
                # Ambiguous, need clarification
                logger.info(f"❓ Priority 3: Multiple NPCs, need clarification")
                return {
                    "status": "needs_clarification",
                    "target": None,
                    "target_type": "none",
                    "target_id": None,
                    "target_name": None,
                    "ambiguous_options": [{"id": npc['id'], "name": npc['name']} for npc in npc_list],
                    "clarification_reason": f"Multiple people present. Who do you target: {', '.join(npc['name'] for npc in npc_list)}?",
                    "plot_armor_reason": None
                }
    
    # Priority 4: No valid target found
    logger.info(f"🎯 No target found for action")
    return {
        "status": "no_target_found",
        "target": None,
        "target_type": "none",
        "target_id": None,
        "target_name": None,
        "ambiguous_options": [],
        "clarification_reason": "No valid target found. Please specify who or what you want to attack.",
        "plot_armor_reason": None
    }


def extract_named_target_from_text(
    player_action: str,
    world_state: Dict[str, Any],
    world_blueprint: Dict[str, Any],
    combat_state: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Extract a named target from the action text.
    E.g., "I punch Aria" should identify Aria as the target.
    """
    action_lower = player_action.lower()
    
    # Check NPCs first (more specific)
    active_npcs = world_state.get('active_npcs', [])
    for npc_id in active_npcs:
        npc = find_npc_by_id(npc_id, world_blueprint)
        if npc:
            npc_name = npc.get('name', '').lower()
            # Look for exact name matches with word boundaries
            if f" {npc_name} " in f" {action_lower} " or action_lower.endswith(f" {npc_name}"):
                npc['target_type'] = 'npc'
                return npc
    
    # Check enemies in combat
    if combat_state and not combat_state.get('combat_over', True):
        for enemy in combat_state.get('enemies', []):
            if enemy.get('hp', 0) > 0:
                enemy_name = enemy.get('name', '').lower()
                if f" {enemy_name} " in f" {action_lower} " or action_lower.endswith(f" {enemy_name}"):
                    enemy['target_type'] = 'enemy'
                    return enemy
    
    return None


def is_hostile_action(player_action: str) -> bool:
    """
    Detect if the player action is a hostile action requiring a target.
    
    P1 FIX: Strengthened detection to catch more hostile patterns including:
    - Direct violence keywords
    - Weapon usage
    - Aggressive verbs
    - Repeated violence patterns
    """
    action_lower = player_action.lower()
    
    # Primary hostile keywords - direct violence
    hostile_keywords = [
        'attack', 'strike', 'hit', 'slash', 'stab', 'punch', 'kick',
        'shoot', 'fire at', 'throw at', 'swing at', 'charge',
        'grapple', 'shove', 'tackle', 'headbutt', 'smash', 'crush',
        'beat', 'assault', 'fight', 'kill', 'murder', 'execute'
    ]
    
    # Weapon-related actions
    weapon_keywords = [
        'sword', 'dagger', 'axe', 'mace', 'spear', 'bow', 'arrow',
        'blade', 'weapon', 'club', 'hammer', 'knife'
    ]
    
    # Aggressive action verbs
    aggressive_verbs = [
        'draw weapon', 'unsheathe', 'aim at', 'point weapon',
        'threaten', 'menace', 'lunge', 'rush', 'leap at'
    ]
    
    # Repeated violence patterns (attacking "again", "once more")
    repeat_patterns = ['again', 'once more', 'another', 'keep attacking', 'continue']
    
    # Check primary hostile keywords
    if any(keyword in action_lower for keyword in hostile_keywords):
        logger.info(f"🎯 Hostile action detected: violence keyword")
        return True
    
    # Check weapon usage combined with aggressive intent
    has_weapon = any(weapon in action_lower for weapon in weapon_keywords)
    has_action = any(verb in ['use', 'swing', 'wield', 'brandish'] for verb in action_lower.split())
    if has_weapon and has_action:
        logger.info(f"🎯 Hostile action detected: weapon usage")
        return True
    
    # Check aggressive verbs
    if any(verb in action_lower for verb in aggressive_verbs):
        logger.info(f"🎯 Hostile action detected: aggressive verb")
        return True
    
    # Check for repeated violence
    if any(pattern in action_lower for pattern in repeat_patterns):
        # If "again" or "once more" is used, assume it's continuing hostile action
        if any(word in action_lower for word in ['hit', 'attack', 'punch', 'strike']):
            logger.info(f"🎯 Hostile action detected: repeated violence")
            return True
    
    return False


def parse_enemy_from_action(player_action: str, enemies: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Try to parse which enemy the player is targeting from action text.
    Uses case-insensitive substring matching.
    """
    action_lower = player_action.lower()
    
    for enemy in enemies:
        enemy_name = enemy.get('name', '').lower()
        # Check for exact name or word-level matches
        if enemy_name in action_lower:
            return enemy
        # Check for individual words from enemy name
        enemy_words = enemy_name.split()
        if any(word in action_lower for word in enemy_words if len(word) > 3):
            return enemy
    
    return None


def parse_npc_from_action(player_action: str, npcs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Try to parse which NPC the player is targeting from action text.
    Uses case-insensitive substring matching.
    """
    action_lower = player_action.lower()
    
    for npc in npcs:
        npc_name = npc.get('name', '').lower()
        # Check for exact name or word-level matches
        if npc_name in action_lower:
            return npc
        # Check for individual words from NPC name
        npc_words = npc_name.split()
        if any(word in action_lower for word in npc_words if len(word) > 3):
            return npc
    
    return None


def find_npc_by_id(npc_id: str, world_blueprint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Find an NPC in the world_blueprint by ID.
    """
    key_npcs = world_blueprint.get('key_npcs', [])
    for npc in key_npcs:
        if npc.get('id') == npc_id or npc.get('name', '').lower().replace(' ', '_') == npc_id:
            # Ensure NPC has an ID field
            if 'id' not in npc:
                npc['id'] = npc.get('name', '').lower().replace(' ', '_')
            return npc
    return None
