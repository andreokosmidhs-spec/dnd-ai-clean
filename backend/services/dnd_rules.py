"""
D&D 5E RULES Engine - Strict mechanical combat resolution following D&D 5e rules.

Implements:
- Attack rolls: d20 + proficiency + ability modifier
- Armor Class (AC) checks
- Damage rolls: weapon die + ability modifier
- Critical hits (nat 20) and critical misses (nat 1)
- Unarmed strikes: 1 + STR mod (minimum 1 damage)
- Initiative (fixed for now)
- Death at 0 HP
"""
import random
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


def roll_d20() -> int:
    """Roll a standard d20"""
    return random.randint(1, 20)


def roll_dice(dice_notation: str) -> int:
    """
    Roll dice from notation like "1d6", "2d8+2", "1d4".
    
    Args:
        dice_notation: String like "1d6" or "2d8+2"
    
    Returns:
        Total rolled value
    """
    notation = dice_notation.lower().replace(" ", "")
    
    # Handle bonus
    parts = notation.split("+")
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


def calculate_ability_modifier(ability_score: int) -> int:
    """
    Calculate D&D 5e ability modifier from ability score.
    Formula: (score - 10) // 2
    """
    return (ability_score - 10) // 2


def get_attack_ability_modifier(attacker: Dict[str, Any], weapon_type: str = "melee") -> Tuple[str, int]:
    """
    Get the appropriate ability modifier for an attack.
    
    Args:
        attacker: Attacker data (character or enemy)
        weapon_type: "melee", "finesse", or "ranged"
    
    Returns:
        (ability_name, modifier_value)
    """
    abilities = attacker.get('abilities', {})
    
    if weapon_type == "ranged":
        # Ranged weapons use DEX
        dex = abilities.get('dex', 10)
        return ('DEX', calculate_ability_modifier(dex))
    elif weapon_type == "finesse":
        # Finesse weapons use STR or DEX (whichever is higher)
        str_val = abilities.get('str', 10)
        dex_val = abilities.get('dex', 10)
        str_mod = calculate_ability_modifier(str_val)
        dex_mod = calculate_ability_modifier(dex_val)
        return ('DEX', dex_mod) if dex_mod > str_mod else ('STR', str_mod)
    else:
        # Melee weapons use STR
        str_val = abilities.get('str', 10)
        return ('STR', calculate_ability_modifier(str_val))


def resolve_attack(
    attacker: Dict[str, Any],
    target: Dict[str, Any],
    weapon_type: str = "melee",
    weapon_damage: str = "1d6",
    is_unarmed: bool = False,
    force_non_lethal: bool = False
) -> Dict[str, Any]:
    """
    Resolve a D&D 5e attack following strict rules.
    
    D&D 5e Attack Rules:
    - Attack Roll: d20 + ability modifier + proficiency bonus (if proficient)
    - Natural 20: Automatic hit, double damage dice
    - Natural 1: Automatic miss
    - Hit if: total attack >= target AC
    - Damage: weapon dice + ability modifier (minimum 1)
    - Unarmed Strike: 1 + STR modifier bludgeoning damage (minimum 1)
    - Non-lethal: Target reduced to 0 HP becomes unconscious, not dead
    
    Args:
        attacker: Attacker data with abilities, proficiency_bonus, attack_bonus
        target: Target data with ac, hp, max_hp
        weapon_type: "melee", "finesse", or "ranged"
        weapon_damage: Dice notation like "1d6" or "1d8+2"
        is_unarmed: If True, use unarmed strike rules (1 + STR mod)
        force_non_lethal: If True, target becomes unconscious instead of dying at 0 HP
    
    Returns:
        {
            "hit": bool,
            "is_crit": bool,
            "critical_miss": bool,
            "roll": int,  # The d20 roll
            "total_attack": int,  # d20 + all modifiers
            "target_ac": int,
            "damage": int,
            "ability_used": str,
            "new_target_hp": int,
            "target_hp_remaining": int,  # Alias for new_target_hp
            "knocked_unconscious": bool,
            "killed": bool,
            "target_killed": bool  # Alias for killed
        }
    """
    # Get attacker stats
    proficiency_bonus = attacker.get('proficiency_bonus', 2)
    attack_bonus = attacker.get('attack_bonus', 0)  # Additional bonus (magic items, level scaling)
    ability_name, ability_mod = get_attack_ability_modifier(attacker, weapon_type)
    
    # Get target stats
    target_ac = target.get('ac', 10)
    target_hp = target.get('hp', 10)
    
    # Roll attack (d20 + proficiency + ability mod + attack bonus)
    attack_roll = roll_d20()
    total_attack = attack_roll + proficiency_bonus + ability_mod + attack_bonus
    
    logger.info(f"⚔️ Attack: d20={attack_roll}, proficiency={proficiency_bonus}, {ability_name} mod={ability_mod}, attack_bonus={attack_bonus}, total={total_attack} vs AC {target_ac}")
    
    # Check for critical miss (natural 1 - automatic miss per D&D 5e rules)
    if attack_roll == 1:
        logger.info("❌ CRITICAL MISS (Natural 1)! Attack automatically fails.")
        return {
            "hit": False,
            "is_crit": False,
            "critical": False,
            "critical_miss": True,
            "roll": attack_roll,
            "attack_roll": attack_roll,
            "total_attack": total_attack,
            "target_ac": target_ac,
            "damage": 0,
            "ability_used": ability_name,
            "new_target_hp": target_hp,
            "target_hp_remaining": target_hp,
            "knocked_unconscious": False,
            "killed": False,
            "target_killed": False
        }
    
    # Check for critical hit (natural 20 - automatic hit + double damage dice per D&D 5e)
    if attack_roll == 20:
        logger.info("✨ CRITICAL HIT (Natural 20)! Automatic hit, double damage dice.")
        if is_unarmed:
            # Unarmed crit: Roll 1 twice, then add STR mod once
            # (1 + 1) + STR mod, minimum 2
            damage = max(2, 2 + ability_mod)
        else:
            # Roll damage dice twice (not the modifier), then add ability mod once
            damage_roll_1 = roll_dice(weapon_damage.split("+")[0])
            damage_roll_2 = roll_dice(weapon_damage.split("+")[0])
            damage = damage_roll_1 + damage_roll_2 + ability_mod
        
        # Ensure minimum 1 damage
        damage = max(1, damage)
        
        new_hp = max(0, target_hp - damage)
        
        # Check if target is killed or knocked unconscious
        is_killed = new_hp <= 0 and not force_non_lethal
        is_unconscious = new_hp <= 0 and force_non_lethal
        
        logger.info(f"💥 Critical damage: {damage}. Target HP: {target_hp} → {new_hp}")
        if is_unconscious:
            logger.info("😴 Target knocked unconscious (non-lethal)")
        elif is_killed:
            logger.info("☠️ Target killed")
        
        return {
            "hit": True,
            "is_crit": True,
            "critical": True,
            "critical_miss": False,
            "roll": attack_roll,
            "attack_roll": attack_roll,
            "total_attack": total_attack,
            "target_ac": target_ac,
            "damage": damage,
            "ability_used": ability_name,
            "new_target_hp": new_hp,
            "target_hp_remaining": new_hp,
            "knocked_unconscious": is_unconscious,
            "killed": is_killed,
            "target_killed": is_killed
        }
    
    # Normal hit check (total attack >= AC)
    if total_attack >= target_ac:
        logger.info(f"✅ Hit! ({total_attack} vs AC {target_ac})")
        if is_unarmed:
            # Unarmed strike: 1 + STR mod (minimum 1 damage per D&D 5e)
            damage = max(1, 1 + ability_mod)
        else:
            # Normal weapon damage: roll dice + ability mod
            damage_roll = roll_dice(weapon_damage.split("+")[0])
            damage = max(1, damage_roll + ability_mod)  # Minimum 1 damage
        
        new_hp = max(0, target_hp - damage)
        
        # Check if target is killed or knocked unconscious
        is_killed = new_hp <= 0 and not force_non_lethal
        is_unconscious = new_hp <= 0 and force_non_lethal
        
        logger.info(f"💥 Damage: {damage}. Target HP: {target_hp} → {new_hp}")
        if is_unconscious:
            logger.info("😴 Target knocked unconscious (non-lethal)")
        elif is_killed:
            logger.info("☠️ Target killed")
        
        return {
            "hit": True,
            "is_crit": False,
            "critical": False,
            "critical_miss": False,
            "roll": attack_roll,
            "attack_roll": attack_roll,
            "total_attack": total_attack,
            "target_ac": target_ac,
            "damage": damage,
            "ability_used": ability_name,
            "new_target_hp": new_hp,
            "target_hp_remaining": new_hp,
            "knocked_unconscious": is_unconscious,
            "killed": is_killed,
            "target_killed": is_killed
        }
    else:
        logger.info(f"❌ Miss! ({total_attack} vs AC {target_ac})")
        return {
            "hit": False,
            "is_crit": False,
            "critical": False,
            "critical_miss": False,
            "roll": attack_roll,
            "attack_roll": attack_roll,
            "total_attack": total_attack,
            "target_ac": target_ac,
            "damage": 0,
            "ability_used": ability_name,
            "new_target_hp": target_hp,
            "target_hp_remaining": target_hp,
            "knocked_unconscious": False,
            "killed": False,
            "target_killed": False
        }


def apply_damage_to_target(target: Dict[str, Any], damage: int) -> Dict[str, Any]:
    """
    Apply damage to a target and return updated target data.
    
    Args:
        target: Target data with hp and max_hp
        damage: Damage amount
    
    Returns:
        Updated target data
    """
    target['hp'] = max(0, target.get('hp', 0) - damage)
    return target
