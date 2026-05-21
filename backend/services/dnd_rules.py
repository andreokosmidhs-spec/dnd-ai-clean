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


def roll_initiative(dex_score: int = 10) -> int:
    """D&D 5e initiative: d20 + DEX modifier."""
    return roll_d20() + calculate_ability_modifier(int(dex_score))


def proficiency_bonus_for_level(level: int) -> int:
    """5e proficiency bonus by character level."""
    try:
        lvl = int(level)
    except Exception:  # noqa: BLE001
        lvl = 1
    if lvl <= 4:
        return 2
    if lvl <= 8:
        return 3
    if lvl <= 12:
        return 4
    if lvl <= 16:
        return 5
    return 6


_PERCEPTION_KEYS = {"perception", "Perception", "PERCEPTION"}


def compute_passive_perception(character: Dict[str, Any]) -> Dict[str, Any]:
    """5e passive Perception = 10 + WIS modifier + (prof bonus if proficient).

    Returns {"score": int, "wis_mod": int, "proficient": bool, "prof_bonus": int,
             "tier": str}. `tier` buckets the score for narration calibration:
        oblivious  : <=10   — needs explicit checks for almost everything
        average    : 11-13  — sees the obvious, misses the subtle
        sharp      : 14-16  — catches one subtle detail per scene
        keen       : 17-19  — flags hooks proactively, rarely misses leads
        uncanny    : >=20   — almost nothing escapes their notice
    """
    abil = (character or {}).get("abilityScores") or (character or {}).get("ability_scores") or {}
    # The model uses 'wis' (and 'str'/'dex'/'con'/'int'/'cha') — but ability
    # scores can also live nested under abilityScores in different shapes.
    wis = abil.get("wis") or abil.get("WIS") or abil.get("wisdom") or 10
    try:
        wis = int(wis)
    except Exception:  # noqa: BLE001
        wis = 10
    wis_mod = calculate_ability_modifier(wis)

    cls = (character or {}).get("class_") or (character or {}).get("class") or {}
    level = cls.get("level") if isinstance(cls, dict) else 1
    prof_bonus = proficiency_bonus_for_level(level)

    skill_profs = (cls.get("skillProficiencies") or []) if isinstance(cls, dict) else []
    proficient = any(str(s).strip() in _PERCEPTION_KEYS for s in skill_profs)

    score = 10 + wis_mod + (prof_bonus if proficient else 0)

    if score <= 10:
        tier = "oblivious"
    elif score <= 13:
        tier = "average"
    elif score <= 16:
        tier = "sharp"
    elif score <= 19:
        tier = "keen"
    else:
        tier = "uncanny"

    return {
        "score": score,
        "wis_mod": wis_mod,
        "proficient": proficient,
        "prof_bonus": prof_bonus,
        "tier": tier,
    }


def passive_perception_block(character: Dict[str, Any]) -> str:
    """Tight DM-prompt section telling the LLM how informative the narration
    should be relative to this character's passive Perception. Threaded into
    the lean DM + storyline scene prompts."""
    pp = compute_passive_perception(character or {})
    score, tier = pp["score"], pp["tier"]
    guidance = {
        "oblivious": (
            "Narration is bare. Reveal only the obvious — the wagon, the man, "
            "the fire. Subtle details (faint scent, scuff in the dust, a "
            "guarded glance) are NOT mentioned unless the player makes an "
            "active check."
        ),
        "average": (
            "Narration shows the obvious cleanly and one (1) modest cue per "
            "scene — a footprint at the doorway, a tone in someone's voice, "
            "a smell that doesn't belong. Subtler clues still need active "
            "checks."
        ),
        "sharp": (
            "Narration includes the obvious AND 1-2 subtle cues per scene "
            "(scuff marks, a too-clean alibi, a pulse at the throat). Begin "
            "to flag opportunities lightly — 'a side door stands ajar', "
            "'someone here keeps glancing toward the kitchen'."
        ),
        "keen": (
            "Narration is rich. Surface 2-3 subtle cues per scene plus EXPLICIT "
            "opportunity flags ('the latch is unlocked from the inside', "
            "'his hands say tired but his eyes say hunting'). Almost nothing "
            "should escape this character without an active check."
        ),
        "uncanny": (
            "Narration is exhaustive. Surface ALL relevant cues including "
            "ones a normal person would miss (breath behind a curtain, the "
            "smell of metal under perfume). Hooks and exits are essentially "
            "telegraphed — this character's perception is preternatural."
        ),
    }[tier]
    return (
        "=== PASSIVE PERCEPTION ===\n"
        f"Character's passive Perception is {score} (tier: {tier}). "
        f"{guidance}"
    )




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
    force_non_lethal: bool = False,
    advantage: bool = False,
    disadvantage: bool = False,
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
    - Advantage: roll 2d20 take highest; Disadvantage: roll 2d20 take lowest

    Args:
        attacker: Attacker data with abilities, proficiency_bonus, attack_bonus
        target: Target data with ac, hp, max_hp
        weapon_type: "melee", "finesse", or "ranged"
        weapon_damage: Dice notation like "1d6" or "1d8+2"
        is_unarmed: If True, use unarmed strike rules (1 + STR mod)
        force_non_lethal: If True, target becomes unconscious instead of dying at 0 HP
        advantage: Roll with advantage (2d20 take higher)
        disadvantage: Roll with disadvantage (2d20 take lower)

    Returns:
        {
            "hit": bool,
            "is_crit": bool,
            "critical_miss": bool,
            "roll": int,  # The final d20 result used
            "roll1": int,  # First die (always present)
            "roll2": int or None,  # Second die (only when adv/disadv active)
            "total_attack": int,  # d20 + all modifiers
            "target_ac": int,
            "damage": int,
            "ability_used": str,
            "new_target_hp": int,
            "target_hp_remaining": int,  # Alias for new_target_hp
            "knocked_unconscious": bool,
            "killed": bool,
            "target_killed": bool,  # Alias for killed
            "advantage": bool,
            "disadvantage": bool,
        }
    """
    # Get attacker stats
    proficiency_bonus = attacker.get('proficiency_bonus', 2)
    attack_bonus = attacker.get('attack_bonus', 0)  # Additional bonus (magic items, level scaling)
    ability_name, ability_mod = get_attack_ability_modifier(attacker, weapon_type)

    # Get target stats
    target_ac = target.get('ac', 10)
    target_hp = target.get('hp', 10)

    # Roll attack with advantage/disadvantage support
    attack_roll, roll1, roll2 = _make_attack_roll(advantage, disadvantage)
    total_attack = attack_roll + proficiency_bonus + ability_mod + attack_bonus

    adv_label = " (advantage)" if advantage and not disadvantage else " (disadvantage)" if disadvantage and not advantage else ""
    logger.info(
        f"⚔️ Attack: d20={attack_roll}{adv_label}, proficiency={proficiency_bonus}, "
        f"{ability_name} mod={ability_mod}, attack_bonus={attack_bonus}, "
        f"total={total_attack} vs AC {target_ac}"
    )

    # Check for critical miss (natural 1 - automatic miss per D&D 5e rules)
    if attack_roll == 1:
        logger.info("❌ CRITICAL MISS (Natural 1)! Attack automatically fails.")
        return {
            "hit": False,
            "is_crit": False,
            "critical": False,
            "critical_miss": True,
            "roll": attack_roll,
            "roll1": roll1,
            "roll2": roll2,
            "attack_roll": attack_roll,
            "total_attack": total_attack,
            "target_ac": target_ac,
            "damage": 0,
            "ability_used": ability_name,
            "new_target_hp": target_hp,
            "target_hp_remaining": target_hp,
            "knocked_unconscious": False,
            "killed": False,
            "target_killed": False,
            "advantage": advantage,
            "disadvantage": disadvantage,
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
            "roll1": roll1,
            "roll2": roll2,
            "attack_roll": attack_roll,
            "total_attack": total_attack,
            "target_ac": target_ac,
            "damage": damage,
            "ability_used": ability_name,
            "new_target_hp": new_hp,
            "target_hp_remaining": new_hp,
            "knocked_unconscious": is_unconscious,
            "killed": is_killed,
            "target_killed": is_killed,
            "advantage": advantage,
            "disadvantage": disadvantage,
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
            "roll1": roll1,
            "roll2": roll2,
            "attack_roll": attack_roll,
            "total_attack": total_attack,
            "target_ac": target_ac,
            "damage": damage,
            "ability_used": ability_name,
            "new_target_hp": new_hp,
            "target_hp_remaining": new_hp,
            "knocked_unconscious": is_unconscious,
            "killed": is_killed,
            "target_killed": is_killed,
            "advantage": advantage,
            "disadvantage": disadvantage,
        }
    else:
        logger.info(f"❌ Miss! ({total_attack} vs AC {target_ac})")
        return {
            "hit": False,
            "is_crit": False,
            "critical": False,
            "critical_miss": False,
            "roll": attack_roll,
            "roll1": roll1,
            "roll2": roll2,
            "attack_roll": attack_roll,
            "total_attack": total_attack,
            "target_ac": target_ac,
            "damage": 0,
            "ability_used": ability_name,
            "new_target_hp": target_hp,
            "target_hp_remaining": target_hp,
            "knocked_unconscious": False,
            "killed": False,
            "target_killed": False,
            "advantage": advantage,
            "disadvantage": disadvantage,
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


# ── Advantage / Disadvantage ──────────────────────────────────────────────────

def _make_attack_roll(advantage: bool, disadvantage: bool) -> Tuple[int, int, Optional[int]]:
    """Return (final_roll, roll1, roll2_or_None).

    When both advantage and disadvantage are active they cancel out (PHB rule).
    """
    if advantage and not disadvantage:
        r1, r2 = roll_d20(), roll_d20()
        return max(r1, r2), r1, r2
    elif disadvantage and not advantage:
        r1, r2 = roll_d20(), roll_d20()
        return min(r1, r2), r1, r2
    else:
        r = roll_d20()
        return r, r, None


def compute_advantage_flags(
    attacker_conditions: list,
    target_conditions: list,
    weapon_type: str = "melee",
    blinded: bool = False,
) -> Tuple[bool, bool]:
    """Return (advantage, disadvantage) based on D&D 5e conditions.

    Conservative: only sets flags when conditions are explicitly present.
    """
    advantage = False
    disadvantage = False

    # Attacker conditions
    conds = [c.lower() for c in (attacker_conditions or [])]
    if "poisoned" in conds:
        disadvantage = True
    if "frightened" in conds:
        disadvantage = True
    if "invisible" in conds:
        advantage = True
    if "blinded" in conds:
        disadvantage = True
        # Attacks against blinded targets have advantage (handled via target)

    # Blinded by environment (darkness without darkvision)
    if blinded:
        disadvantage = True

    # Target conditions
    t_conds = [c.lower() for c in (target_conditions or [])]
    if "prone" in t_conds:
        if weapon_type == "ranged":
            disadvantage = True
        else:
            advantage = True
    if "paralyzed" in t_conds or "unconscious" in t_conds:
        advantage = True

    return advantage, disadvantage


# ── Death Saving Throws ───────────────────────────────────────────────────────

def roll_death_save() -> Dict[str, Any]:
    """D&D 5e death saving throw. Returns result dict."""
    roll = roll_d20()
    if roll == 20:
        result = "critical_success"   # regain 1 HP
    elif roll == 1:
        result = "critical_failure"   # counts as 2 failures
    elif roll >= 10:
        result = "success"
    else:
        result = "failure"
    return {"roll": roll, "result": result}


# ── Action Economy ────────────────────────────────────────────────────────────

# Action cost by action type keyword
ACTION_COSTS = {
    "attack": "action",
    "cast": "action",
    "dodge": "action",
    "dash": "action",
    "disengage": "action",
    "help": "action",
    "hide": "action",
    "ready": "action",
    "two-weapon": "bonus_action",
    "off-hand": "bonus_action",
    "healing word": "bonus_action",
    "cunning": "bonus_action",
    "second wind": "bonus_action",
    "opportunity": "reaction",
    "shield": "reaction",
}


def classify_action_cost(player_action: str) -> str:
    """Return 'action', 'bonus_action', or 'reaction'."""
    lower = player_action.lower()
    for keyword, cost in ACTION_COSTS.items():
        if keyword in lower:
            return cost
    return "action"  # default
