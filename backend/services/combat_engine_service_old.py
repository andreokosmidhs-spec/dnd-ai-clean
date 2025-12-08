"""
COMBAT ENGINE Service - Simple D&D-style turn-based combat.
Server-side combat resolution with HP, AC, attack rolls, damage.
"""
import random
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


def roll_d20() -> int:
    """Roll a d20"""
    return random.randint(1, 20)


def roll_damage(damage_die: str) -> int:
    """
    Roll damage dice. Simple parser for common patterns like "1d6", "2d8+2"
    
    Args:
        damage_die: String like "1d6" or "2d8+2"
    
    Returns:
        Total damage
    """
    parts = damage_die.lower().replace(" ", "").split("+")
    base = parts[0]
    bonus = int(parts[1]) if len(parts) > 1 else 0
    
    # Parse "XdY" format
    if "d" in base:
        count, sides = base.split("d")
        count = int(count) if count else 1
        sides = int(sides)
        total = sum(random.randint(1, sides) for _ in range(count))
        return total + bonus
    
    return 0


def calculate_modifier(stat_value: int) -> int:
    """Calculate D&D ability modifier from stat value"""
    return (stat_value - 10) // 2


def build_enemy_from_blueprint(
    enemy_template: Dict[str, Any],
    enemy_id: str
) -> Dict[str, Any]:
    """
    Build an EnemyState from a template in world_blueprint or a simple descriptor.
    
    Args:
        enemy_template: Dict with enemy info (name, hp, ac, etc.)
        enemy_id: Unique ID for this enemy instance
    
    Returns:
        EnemyState dict
    """
    return {
        "id": enemy_id,
        "name": enemy_template.get("name", "Unknown Enemy"),
        "hp": enemy_template.get("hp", 10),
        "max_hp": enemy_template.get("hp", 10),
        "ac": enemy_template.get("ac", 12),
        "attack_bonus": enemy_template.get("attack_bonus", 2),
        "damage_die": enemy_template.get("damage_die", "1d6"),
        "conditions": []
    }


def start_combat(
    character_state: Dict[str, Any],
    enemy_templates: List[Dict[str, Any]],
    campaign_id: str,
    character_id: str
) -> Dict[str, Any]:
    """
    Initialize combat state.
    
    Args:
        character_state: Player character state
        enemy_templates: List of enemy templates to spawn
        campaign_id: Campaign ID
        character_id: Character ID
    
    Returns:
        CombatState dict
    """
    # Build enemy list
    enemies = []
    for i, template in enumerate(enemy_templates):
        enemy_id = f"enemy_{i+1}"
        enemies.append(build_enemy_from_blueprint(template, enemy_id))
    
    # Simple initiative: player always goes first
    turn_order = ["player"] + [e["id"] for e in enemies]
    
    combat_state = {
        "enemies": enemies,
        "turn_order": turn_order,
        "active_turn": "player",
        "round": 1,
        "combat_over": False,
        "outcome": None
    }
    
    logger.info(f"⚔️ Combat started: {len(enemies)} enemies, player goes first")
    return combat_state


def process_player_combat_action(
    player_action: str,
    character_state: Dict[str, Any],
    combat_state: Dict[str, Any]
) -> Tuple[str, Dict[str, Any], bool]:
    """
    Process player's combat action.
    
    Args:
        player_action: What the player wants to do
        character_state: Player stats
        combat_state: Current combat state
    
    Returns:
        (narration, combat_state_update, advance_turn)
    """
    action_lower = player_action.lower()
    enemies = combat_state["enemies"]
    
    # Find alive enemies
    alive_enemies = [e for e in enemies if e["hp"] > 0]
    
    if not alive_enemies:
        return "There are no more enemies to fight.", {}, False
    
    # Determine action type
    if any(word in action_lower for word in ["attack", "strike", "hit", "slash", "stab"]):
        return process_attack_action(player_action, character_state, combat_state)
    elif any(word in action_lower for word in ["flee", "run", "escape", "retreat"]):
        return process_flee_action(player_action, character_state, combat_state)
    elif any(word in action_lower for word in ["defend", "dodge", "block", "guard"]):
        return process_defend_action(player_action, character_state, combat_state)
    else:
        # Default: treat as attack
        return process_attack_action(player_action, character_state, combat_state)


def process_attack_action(
    player_action: str,
    character_state: Dict[str, Any],
    combat_state: Dict[str, Any]
) -> Tuple[str, Dict[str, Any], bool]:
    """Process player attack"""
    enemies = combat_state["enemies"]
    alive_enemies = [e for e in enemies if e["hp"] > 0]
    
    if not alive_enemies:
        return "There are no enemies left to attack.", {}, False
    
    # Pick target based on player's action text
    target = None
    player_action_lower = player_action.lower()
    
    # Try to find target by name mention
    for enemy in alive_enemies:
        enemy_name = enemy["name"].lower()
        # Check for exact name or partial match
        if enemy_name in player_action_lower or any(word in player_action_lower for word in enemy_name.split()):
            target = enemy
            logger.info(f"🎯 Detected target: {enemy['name']} from action '{player_action}'")
            break
    
    # Fallback to first alive enemy if no target detected
    if not target:
        target = alive_enemies[0]
        logger.info(f"🎯 No specific target detected, defaulting to first enemy: {target['name']}")
    
    # Get player's attack modifier (use STR or DEX, whichever is higher)
    abilities = character_state.get("abilities", {})
    str_mod = calculate_modifier(abilities.get("str", 10))
    dex_mod = calculate_modifier(abilities.get("dex", 10))
    attack_mod = max(str_mod, dex_mod)
    proficiency = character_state.get("proficiency_bonus", 2)
    
    # P3.5: Include attack_bonus for real power spikes at L3 & L5
    attack_bonus = character_state.get("attack_bonus", 0)
    
    # Roll attack
    attack_roll = roll_d20()
    total_attack = attack_roll + attack_mod + proficiency + attack_bonus
    
    logger.info(f"⚔️ Player attacks {target['name']}: d20={attack_roll}, modifier={attack_mod}+{proficiency}+{attack_bonus}, total={total_attack} vs AC {target['ac']}")
    
    if attack_roll == 1:
        # Critical miss
        narration = f"You swing wildly at the {target['name']}, but lose your balance and miss completely!"
    elif attack_roll == 20:
        # Critical hit
        damage = roll_damage("2d6") + attack_mod  # Double damage dice
        target["hp"] = max(0, target["hp"] - damage)
        if target["hp"] <= 0:
            narration = f"**Critical hit!** You strike the {target['name']} with devastating force for {damage} damage! The {target['name']} falls defeated!"
        else:
            narration = f"**Critical hit!** You deal {damage} damage to the {target['name']} ({target['hp']}/{target['max_hp']} HP remaining)."
    elif total_attack >= target["ac"]:
        # Hit
        damage = roll_damage("1d6") + attack_mod
        target["hp"] = max(0, target["hp"] - damage)
        if target["hp"] <= 0:
            narration = f"You strike the {target['name']} for {damage} damage! The {target['name']} collapses, defeated!"
        else:
            narration = f"You hit the {target['name']} for {damage} damage! ({target['hp']}/{target['max_hp']} HP remaining)"
    else:
        # Miss
        narration = f"You attack the {target['name']}, but your strike glances off their defenses (rolled {total_attack} vs AC {target['ac']})."
    
    # Update combat state
    combat_state_update = {
        "enemies": enemies
    }
    
    return narration, combat_state_update, True


def process_defend_action(
    player_action: str,
    character_state: Dict[str, Any],
    combat_state: Dict[str, Any]
) -> Tuple[str, Dict[str, Any], bool]:
    """Process player defend action"""
    narration = "You take a defensive stance, preparing to dodge incoming attacks."
    # In a full implementation, this would give temporary AC bonus
    # For now, just narrative flavor
    return narration, {}, True


def process_flee_action(
    player_action: str,
    character_state: Dict[str, Any],
    combat_state: Dict[str, Any]
) -> Tuple[str, Dict[str, Any], bool]:
    """Process player flee attempt"""
    # Simple flee check: DEX check vs DC 12
    dex = character_state.get("abilities", {}).get("dex", 10)
    dex_mod = calculate_modifier(dex)
    flee_roll = roll_d20() + dex_mod
    
    if flee_roll >= 12:
        narration = "You successfully disengage and flee from combat!"
        combat_state_update = {
            "combat_over": True,
            "outcome": "fled"
        }
        return narration, combat_state_update, False
    else:
        narration = f"You attempt to flee but the enemies block your escape (rolled {flee_roll} vs DC 12)!"
        return narration, {}, True


def process_enemy_turns(
    character_state: Dict[str, Any],
    combat_state: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    """
    Process all enemy turns (simplified: all enemies attack player).
    
    Returns:
        (narration, combat_state_update)
    """
    enemies = combat_state["enemies"]
    alive_enemies = [e for e in enemies if e["hp"] > 0]
    
    if not alive_enemies:
        return "", {}
    
    narrations = []
    player_hp = character_state.get("hp", 10)
    player_ac = character_state.get("ac", 10)
    total_damage = 0
    
    for enemy in alive_enemies:
        # Enemy attacks player
        attack_roll = roll_d20()
        attack_bonus = enemy.get("attack_bonus", 2)  # Default to +2 if not specified
        total_attack = attack_roll + attack_bonus
        
        logger.info(f"⚔️ {enemy['name']} attacks player: d20={attack_roll}, bonus={attack_bonus}, total={total_attack} vs AC {player_ac}")
        
        if attack_roll == 1:
            narrations.append(f"The {enemy['name']} swings clumsily and misses.")
        elif attack_roll == 20:
            damage_die = enemy.get("damage_die", "1d6")  # Default to 1d6 if not specified
            damage = roll_damage(damage_die) * 2
            total_damage += damage
            narrations.append(f"**Critical hit!** The {enemy['name']} strikes you hard for {damage} damage!")
        elif total_attack >= player_ac:
            damage_die = enemy.get("damage_die", "1d6")
            damage = roll_damage(damage_die)
            total_damage += damage
            narrations.append(f"The {enemy['name']} hits you for {damage} damage!")
        else:
            narrations.append(f"The {enemy['name']} attacks but you dodge (rolled {total_attack} vs AC {player_ac}).")
    
    # Update player HP
    new_player_hp = max(0, player_hp - total_damage)
    
    full_narration = " ".join(narrations)
    if total_damage > 0:
        full_narration += f"\n\n**You take {total_damage} total damage. HP: {new_player_hp}/{character_state.get('max_hp', 10)}**"
    
    # Check if player is defeated
    combat_over = new_player_hp <= 0
    outcome = "player_defeated" if combat_over else None
    
    return full_narration, {
        "player_hp_change": -total_damage,
        "combat_over": combat_over,
        "outcome": outcome
    }


def resolve_combat_turn(
    player_action: str,
    character_state: Dict[str, Any],
    combat_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main combat turn resolution.
    
    Args:
        player_action: Player's action text
        character_state: Player character state
        combat_state: Current combat state
    
    Returns:
        {
            "narration": str,
            "combat_state_update": dict,
            "character_state_update": dict,
            "combat_over": bool,
            "outcome": str | None,
            "xp_gained": int  # P3: XP for defeated enemies
        }
    """
    # Process player action
    player_narration, player_combat_update, advance_turn = process_player_combat_action(
        player_action, character_state, combat_state
    )
    
    # Apply player updates to combat state
    for key, value in player_combat_update.items():
        combat_state[key] = value
    
    # Check if combat ended from player action
    alive_enemies = [e for e in combat_state["enemies"] if e["hp"] > 0]
    if not alive_enemies:
        combat_state["combat_over"] = True
        combat_state["outcome"] = "victory"
        
        # P3: Calculate XP from defeated enemies
        from services.progression_service import calculate_xp_for_enemy
        total_xp = sum(calculate_xp_for_enemy(e) for e in combat_state["enemies"])
        
        return {
            "narration": player_narration + "\n\n**Victory!** All enemies have been defeated!",
            "combat_state_update": combat_state,
            "character_state_update": {},
            "combat_over": True,
            "outcome": "victory",
            "xp_gained": total_xp  # P3
        }
    
    if combat_state.get("combat_over", False):
        # Player fled or other end condition
        return {
            "narration": player_narration,
            "combat_state_update": combat_state,
            "character_state_update": {},
            "combat_over": True,
            "outcome": combat_state.get("outcome"),
            "xp_gained": 0  # P3: No XP for fleeing
        }
    
    # Process enemy turns (if player didn't end combat)
    if advance_turn:
        enemy_narration, enemy_updates = process_enemy_turns(character_state, combat_state)
        
        # Apply enemy updates
        player_hp_change = enemy_updates.get("player_hp_change", 0)
        character_state_update = {}
        if player_hp_change != 0:
            new_hp = max(0, character_state.get("hp", 10) + player_hp_change)
            character_state_update["hp"] = new_hp
        
        # Update combat state
        combat_state["combat_over"] = enemy_updates.get("combat_over", False)
        combat_state["outcome"] = enemy_updates.get("outcome")
        combat_state["round"] += 1
        
        full_narration = player_narration + "\n\n" + enemy_narration
        
        # P3: If combat ended with player defeat, no XP
        xp_gained = 0
        
        return {
            "narration": full_narration,
            "combat_state_update": combat_state,
            "character_state_update": character_state_update,
            "combat_over": combat_state.get("combat_over", False),
            "outcome": combat_state.get("outcome"),
            "xp_gained": xp_gained  # P3
        }
    else:
        # Player action didn't advance turn (e.g., invalid action)
        return {
            "narration": player_narration,
            "combat_state_update": combat_state,
            "character_state_update": {},
            "combat_over": combat_state.get("combat_over", False),
            "outcome": combat_state.get("outcome"),
            "xp_gained": 0  # P3
        }


def generate_combat_options(combat_state: Dict[str, Any]) -> List[str]:
    """Generate action options for player during combat"""
    alive_enemies = [e for e in combat_state["enemies"] if e["hp"] > 0]
    
    if not alive_enemies:
        return ["Continue your adventure"]
    
    options = [
        f"Attack the {alive_enemies[0]['name']}",
        "Take a defensive stance",
        "Attempt to flee"
    ]
    
    if len(alive_enemies) > 1:
        options.insert(1, f"Attack the {alive_enemies[1]['name']}")
    
    return options
