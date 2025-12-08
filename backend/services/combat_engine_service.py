"""
COMPLETE COMBAT ENGINE Service - D&D 5e combat with target resolution, NPC conversion, and plot armor.

Features:
- Priority-based target resolution
- NPC-to-enemy conversion for hostile actions
- Plot armor protection for essential NPCs
- Strict D&D 5e mechanical combat resolution
- Proper combat state cleanup (combat_over = true)
- Non-lethal damage for protected NPCs
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from services.target_resolver import resolve_target, is_hostile_action
from services.plot_armor_service import check_plot_armor, apply_plot_armor_consequences
from services.dnd_rules import (
    resolve_attack,
    apply_damage_to_target,
    calculate_ability_modifier
)

logger = logging.getLogger(__name__)


def convert_npc_to_enemy(
    npc_data: Dict[str, Any],
    world_blueprint: Dict[str, Any],
    character_level: int = 1
) -> Dict[str, Any]:
    """
    Convert an NPC to an enemy combatant.
    
    Args:
        npc_data: NPC data from world_blueprint
        world_blueprint: Full world blueprint
        character_level: Player character level (for scaling)
    
    Returns:
        Enemy dict compatible with CombatParticipant model
    """
    # Basic stats based on NPC role
    role = npc_data.get('role', '').lower()
    
    # Default stats
    base_hp = 15
    ac = 12
    abilities = {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10}
    damage_die = "1d6"
    proficiency_bonus = 2
    
    # Adjust stats based on role
    if 'guard' in role or 'soldier' in role:
        base_hp = 20
        ac = 14
        abilities["str"] = 14
        abilities["con"] = 12
        damage_die = "1d8"
    elif 'merchant' in role or 'innkeeper' in role:
        base_hp = 10
        ac = 10
        abilities["dex"] = 12
        abilities["cha"] = 14
        damage_die = "1d4"
    elif 'thief' in role or 'rogue' in role:
        base_hp = 12
        ac = 13
        abilities["dex"] = 16
        abilities["str"] = 8
        damage_die = "1d6"
    elif 'mage' in role or 'wizard' in role:
        base_hp = 8
        ac = 11
        abilities["int"] = 16
        abilities["dex"] = 12
        damage_die = "1d4"
    
    # Scale HP for character level
    scaled_hp = base_hp + (character_level - 1) * 2
    
    # Create enemy ID
    enemy_id = f"npc_enemy_{npc_data.get('id', npc_data.get('name', 'unknown').lower().replace(' ', '_'))}"
    
    return {
        "id": enemy_id,
        "name": npc_data.get('name', 'Hostile NPC'),
        "hp": scaled_hp,
        "max_hp": scaled_hp,
        "ac": ac,
        "abilities": abilities,
        "proficiency_bonus": proficiency_bonus,
        "attack_bonus": 0,
        "damage_die": damage_die,
        "conditions": [],
        "faction_id": None,
        "participant_type": "npc",
        "is_essential": False,
        "plot_armor_attempts": 0
    }


def start_combat_with_target(
    target_resolution: Dict[str, Any],
    character_state: Dict[str, Any],
    world_blueprint: Dict[str, Any],
    character_level: int = 1
) -> Dict[str, Any]:
    """
    Initialize combat state with a resolved target.
    
    Args:
        target_resolution: Result from target_resolver
        character_state: Player character state
        world_blueprint: World blueprint
        character_level: Player character level
    
    Returns:
        CombatState dict
    """
    enemies = []
    converted_npcs = []
    
    if target_resolution['target_type'] == 'npc':
        # Convert NPC to enemy
        npc_enemy = convert_npc_to_enemy(
            target_resolution['target_data'],
            world_blueprint,
            character_level
        )
        enemies.append(npc_enemy)
        converted_npcs.append(target_resolution['target_id'])
        logger.info(f"⚔️ Converted NPC {target_resolution['target_name']} to enemy")
    elif target_resolution['target_type'] == 'enemy':
        # Already an enemy, add to combat
        enemies.append(target_resolution['target_data'])
        logger.info(f"⚔️ Starting combat with enemy {target_resolution['target_name']}")
    
    # Simple initiative: player always goes first
    turn_order = ["player"] + [e["id"] for e in enemies]
    
    combat_state = {
        "enemies": enemies,
        "participants": [],  # Will be populated with CombatParticipant models
        "turn_order": turn_order,
        "active_turn": "player",
        "round": 1,
        "combat_over": False,
        "outcome": None,
        "converted_npcs": converted_npcs
    }
    
    logger.info(f"⚔️ Combat initialized: {len(enemies)} enemies, player goes first")
    return combat_state


def process_player_attack(
    target_id: str,
    character_state: Dict[str, Any],
    combat_state: Dict[str, Any],
    force_non_lethal: bool = False
) -> Dict[str, Any]:
    """
    Process player's attack action with strict D&D 5e mechanics.
    
    Args:
        target_id: ID of the target to attack
        character_state: Player character data
        combat_state: Current combat state
        force_non_lethal: If True, target becomes unconscious instead of dying
    
    Returns:
        {
            "success": bool,
            "mechanical_summary": dict,  # Structured combat results for DM
            "combat_state_update": dict,
            "character_state_update": dict,
            "combat_over": bool,
            "xp_gained": int
        }
    """
    # Find target enemy
    enemies = combat_state.get('enemies', [])
    target = None
    for enemy in enemies:
        if enemy['id'] == target_id and enemy['hp'] > 0:
            target = enemy
            break
    
    if not target:
        logger.error(f"❌ Target {target_id} not found or already defeated")
        return {
            "success": False,
            "mechanical_summary": {
                "error": f"Target {target_id} not found or already defeated"
            },
            "combat_state_update": {},
            "character_state_update": {},
            "combat_over": False,
            "xp_gained": 0
        }
    
    # Prepare attacker data (player)
    attacker = {
        "abilities": character_state.get('abilities', {}),
        "proficiency_bonus": character_state.get('proficiency_bonus', 2),
        "attack_bonus": character_state.get('attack_bonus', 0)
    }
    
    # Determine weapon (for now, assume unarmed)
    # TODO: Read from character inventory in future
    weapon_type = "melee"
    weapon_damage = "1d6"
    is_unarmed = True
    
    # Resolve attack using strict D&D 5e rules
    attack_result = resolve_attack(
        attacker=attacker,
        target=target,
        weapon_type=weapon_type,
        weapon_damage=weapon_damage,
        is_unarmed=is_unarmed,
        force_non_lethal=force_non_lethal
    )
    
    # Update target HP
    target['hp'] = attack_result['new_target_hp']
    
    # Handle unconscious state
    if attack_result['knocked_unconscious']:
        target['conditions'] = target.get('conditions', [])
        if 'unconscious' not in target['conditions']:
            target['conditions'].append('unconscious')
        logger.info(f"😴 {target['name']} knocked unconscious")
    
    # Check if all enemies are defeated
    alive_enemies = [e for e in enemies if e['hp'] > 0]
    combat_over = len(alive_enemies) == 0
    
    # Update combat state - CRITICAL: Always set combat_over correctly
    combat_state_update = {
        "enemies": enemies,
        "combat_over": combat_over,
        "outcome": "victory" if combat_over else None
    }
    
    # Calculate XP if combat ended in victory
    xp_gained = 0
    if combat_over:
        try:
            from services.progression_service import calculate_xp_for_enemy
            xp_gained = sum(calculate_xp_for_enemy(e) for e in enemies)
            logger.info(f"💰 Combat victory! Awarding {xp_gained} XP")
        except Exception as e:
            logger.warning(f"⚠️ Could not calculate XP: {e}")
            xp_gained = 0
    
    return {
        "success": True,
        "mechanical_summary": {
            "attacker": character_state.get('name', 'You'),
            "target": target['name'],
            "attack_roll": attack_result['roll'],
            "total_attack": attack_result['total_attack'],
            "target_ac": attack_result['target_ac'],
            "hit": attack_result['hit'],
            "critical": attack_result['is_crit'],
            "critical_miss": attack_result['critical_miss'],
            "damage": attack_result['damage'],
            "target_hp_remaining": attack_result['new_target_hp'],
            "target_max_hp": target['max_hp'],
            "target_killed": attack_result['killed'],
            "knocked_unconscious": attack_result['knocked_unconscious'],
            "ability_used": attack_result['ability_used']
        },
        "combat_state_update": combat_state_update,
        "character_state_update": {},
        "combat_over": combat_over,
        "xp_gained": xp_gained
    }


def process_enemy_turns(
    character_state: Dict[str, Any],
    combat_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process all enemy turns using D&D 5e mechanics.
    
    Args:
        character_state: Player character state
        combat_state: Current combat state
    
    Returns:
        {
            "enemy_actions": list of mechanical summaries,
            "total_damage_to_player": int,
            "character_state_update": dict,
            "combat_over": bool
        }
    """
    enemies = combat_state.get('enemies', [])
    alive_enemies = [e for e in enemies if e['hp'] > 0]
    
    if not alive_enemies:
        return {
            "enemy_actions": [],
            "total_damage_to_player": 0,
            "character_state_update": {},
            "combat_over": False
        }
    
    enemy_actions = []
    total_damage = 0
    player_hp = character_state.get('hp', 10)
    player_max_hp = character_state.get('max_hp', 10)
    
    # Prepare target (player)
    player_target = {
        "ac": character_state.get('ac', 10),
        "hp": player_hp,
        "max_hp": player_max_hp
    }
    
    for enemy in alive_enemies:
        # Enemy attacks player
        attack_result = resolve_attack(
            attacker=enemy,
            target=player_target,
            weapon_type="melee",
            weapon_damage=enemy.get('damage_die', '1d6'),
            is_unarmed=False
        )
        
        total_damage += attack_result['damage']
        player_target['hp'] = attack_result['target_hp_remaining']
        
        enemy_actions.append({
            "attacker": enemy['name'],
            "attack_roll": attack_result['attack_roll'],
            "total_attack": attack_result['total_attack'],
            "target_ac": player_target['ac'],
            "hit": attack_result['hit'],
            "critical": attack_result['critical'],
            "critical_miss": attack_result['critical_miss'],
            "damage": attack_result['damage']
        })
    
    # Update player HP
    new_player_hp = player_target['hp']
    combat_over = new_player_hp <= 0
    
    return {
        "enemy_actions": enemy_actions,
        "total_damage_to_player": total_damage,
        "character_state_update": {
            "hp": new_player_hp
        },
        "combat_over": combat_over,
        "outcome": "player_defeated" if combat_over else None
    }


def check_and_apply_plot_armor(
    npc_data: Dict[str, Any],
    world_blueprint: Dict[str, Any],
    world_state: Dict[str, Any],
    character_state: Dict[str, Any],
    action_type: str = "attack"
) -> Dict[str, Any]:
    """
    Check if NPC has plot armor and handle consequences.
    
    Returns:
        {
            "status": "blocked" | "allowed" | "forced_non_lethal",
            "plot_armor_outcome": PlotArmorOutcome dict,
            "world_state_update": dict,
            "character_state_update": dict,
            "narrative_hint": str
        }
    """
    # Check plot armor
    plot_armor_outcome = check_plot_armor(
        npc_data=npc_data,
        world_blueprint=world_blueprint,
        world_state=world_state,
        action_type=action_type
    )
    
    if not plot_armor_outcome['handled']:
        return {
            "status": "allowed",
            "plot_armor_outcome": plot_armor_outcome,
            "world_state_update": {},
            "character_state_update": {},
            "narrative_hint": None
        }
    
    # Plot armor triggered - apply consequences
    logger.warning(f"🛡️ Plot armor activated for {npc_data.get('name')}")
    
    consequence_result = apply_plot_armor_consequences(
        world_state=world_state,
        character_state=character_state,
        consequences=plot_armor_outcome['consequences']
    )
    
    # Determine status
    if plot_armor_outcome['allow_combat']:
        if plot_armor_outcome['mechanical_override'] == 'forced_non_lethal':
            status = "forced_non_lethal"
        else:
            status = "allowed"
    else:
        status = "blocked"
    
    return {
        "status": status,
        "plot_armor_outcome": plot_armor_outcome,
        "world_state_update": consequence_result['world_state_update'],
        "character_state_update": consequence_result['character_state_update'],
        "narrative_hint": plot_armor_outcome['narrative_hint']
    }
