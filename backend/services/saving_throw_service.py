"""D&D 5e saving throw resolution."""
from typing import Dict, Any, Optional
from services.dnd_rules import roll_d20, calculate_ability_modifier, proficiency_bonus_for_level

CLASS_SAVE_PROFICIENCIES: Dict[str, list] = {
    "Barbarian": ["str", "con"],
    "Bard":      ["dex", "cha"],
    "Cleric":    ["wis", "cha"],
    "Druid":     ["int", "wis"],
    "Fighter":   ["str", "con"],
    "Monk":      ["str", "dex"],
    "Paladin":   ["wis", "cha"],
    "Ranger":    ["str", "dex"],
    "Rogue":     ["dex", "int"],
    "Sorcerer":  ["con", "cha"],
    "Warlock":   ["wis", "cha"],
    "Wizard":    ["int", "wis"],
}


def _get_level(character_state: Dict[str, Any]) -> int:
    cls = character_state.get("class_") or character_state.get("class") or {}
    if isinstance(cls, dict):
        return int(cls.get("level") or 1)
    return 1


def _get_class_name(character_state: Dict[str, Any]) -> str:
    cls = character_state.get("class_") or character_state.get("class") or {}
    if isinstance(cls, dict):
        return (cls.get("name") or cls.get("key") or "").strip().title()
    return str(cls).strip().title()


def roll_saving_throw(
    character_state: Dict[str, Any],
    ability: str,          # "str", "dex", "con", "int", "wis", "cha"
    dc: int,
    advantage: bool = False,
    disadvantage: bool = False,
) -> Dict[str, Any]:
    """Roll a saving throw. Returns full result dict.

    Exhaustion level 3+ adds disadvantage on saving throws (5e PHB).
    """
    ability = ability.lower()
    abilities = (
        character_state.get("abilities")
        or character_state.get("abilityScores")
        or {}
    )
    score = int(abilities.get(ability) or 10)
    modifier = calculate_ability_modifier(score)

    class_name = _get_class_name(character_state)
    level = _get_level(character_state)
    prof_bonus = proficiency_bonus_for_level(level)
    proficient = ability in CLASS_SAVE_PROFICIENCIES.get(class_name, [])
    total_mod = modifier + (prof_bonus if proficient else 0)

    # Exhaustion level 3+ → disadvantage on saving throws
    exhaustion = int(character_state.get("exhaustion_level", 0))
    if exhaustion >= 3:
        disadvantage = True

    # Roll with adv/disadv
    r1 = roll_d20()
    if advantage and not disadvantage:
        r2 = roll_d20()
        roll = max(r1, r2)
    elif disadvantage and not advantage:
        r2 = roll_d20()
        roll = min(r1, r2)
    else:
        r2 = None
        roll = r1

    total = roll + total_mod
    success = total >= dc

    return {
        "ability": ability.upper(),
        "roll": roll,
        "roll1": r1,
        "roll2": r2,
        "modifier": modifier,
        "proficient": proficient,
        "prof_bonus": prof_bonus if proficient else 0,
        "total": total,
        "dc": dc,
        "success": success,
        "advantage": advantage,
        "disadvantage": disadvantage,
    }


def spell_save_dc(character_state: Dict[str, Any], spellcasting_ability: str = "int") -> int:
    """DC = 8 + proficiency bonus + spellcasting ability modifier."""
    level = _get_level(character_state)
    prof = proficiency_bonus_for_level(level)
    abilities = character_state.get("abilities") or character_state.get("abilityScores") or {}
    score = int(abilities.get(spellcasting_ability.lower()) or 10)
    return 8 + prof + calculate_ability_modifier(score)
