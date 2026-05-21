"""
D&D 5e spell slot tables and spellcasting ability by class.

Full casters:    Bard, Cleric, Druid, Sorcerer, Wizard
Half casters:    Paladin, Ranger      (slots start at level 2)
Pact magic:      Warlock              (short-rest slots, level scales)
Non-casters:     Barbarian, Fighter, Monk, Rogue
"""
from typing import Dict, Optional

# Spellcasting ability by class
SPELLCASTING_ABILITY: Dict[str, str] = {
    "Bard":      "cha",
    "Cleric":    "wis",
    "Druid":     "wis",
    "Paladin":   "cha",
    "Ranger":    "wis",
    "Sorcerer":  "cha",
    "Warlock":   "cha",
    "Wizard":    "int",
    # Half-casters / sub-classes default
    "Fighter":   "int",   # Eldritch Knight
    "Rogue":     "int",   # Arcane Trickster
}

# Full caster slot table (level → slot_level_str → count)
_FULL: Dict[int, Dict[str, int]] = {
    1:  {"1": 2},
    2:  {"1": 3},
    3:  {"1": 4, "2": 2},
    4:  {"1": 4, "2": 3},
    5:  {"1": 4, "2": 3, "3": 2},
    6:  {"1": 4, "2": 3, "3": 3},
    7:  {"1": 4, "2": 3, "3": 3, "4": 1},
    8:  {"1": 4, "2": 3, "3": 3, "4": 2},
    9:  {"1": 4, "2": 3, "3": 3, "4": 3, "5": 1},
    10: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2},
    11: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1},
    12: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1},
    13: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1},
    14: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1},
    15: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1},
    16: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1},
    17: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1, "9": 1},
    18: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 1, "7": 1, "8": 1, "9": 1},
    19: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 2, "7": 1, "8": 1, "9": 1},
    20: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 2, "7": 2, "8": 1, "9": 1},
}

# Half caster (Paladin, Ranger) — rounds down, starts at level 2
_HALF: Dict[int, Dict[str, int]] = {
    1:  {},
    2:  {"1": 2},
    3:  {"1": 3},
    4:  {"1": 3},
    5:  {"1": 4, "2": 2},
    6:  {"1": 4, "2": 2},
    7:  {"1": 4, "2": 3},
    8:  {"1": 4, "2": 3},
    9:  {"1": 4, "2": 3, "3": 2},
    10: {"1": 4, "2": 3, "3": 2},
    11: {"1": 4, "2": 3, "3": 3},
    12: {"1": 4, "2": 3, "3": 3},
    13: {"1": 4, "2": 3, "3": 3, "4": 1},
    14: {"1": 4, "2": 3, "3": 3, "4": 1},
    15: {"1": 4, "2": 3, "3": 3, "4": 2},
    16: {"1": 4, "2": 3, "3": 3, "4": 2},
    17: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 1},
    18: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 1},
    19: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2},
    20: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2},
}

# Warlock pact magic — short-rest refresh, slots all at pact slot level
_PACT_SLOT_LEVEL: Dict[int, str] = {
    1: "1", 2: "1", 3: "2", 4: "2", 5: "3",
    6: "3", 7: "4", 8: "4", 9: "5", 10: "5",
    11: "5", 12: "5", 13: "5", 14: "5", 15: "5",
    16: "5", 17: "5", 18: "5", 19: "5", 20: "5",
}
_PACT_SLOT_COUNT: Dict[int, int] = {
    **{lvl: 1 for lvl in range(1, 2)},
    **{lvl: 2 for lvl in range(2, 11)},
    **{lvl: 3 for lvl in range(11, 17)},
    **{lvl: 4 for lvl in range(17, 19)},
    **{lvl: 4 for lvl in range(19, 21)},
}

# Which classes use which table
_FULL_CASTERS = {"Bard", "Cleric", "Druid", "Sorcerer", "Wizard"}
_HALF_CASTERS = {"Paladin", "Ranger"}
_PACT_CASTERS = {"Warlock"}


def get_spell_slots(class_name: str, level: int) -> Dict[str, int]:
    """Return {slot_level_str: count} for this class at this level. Empty dict = no casting."""
    level = max(1, min(20, int(level or 1)))
    cls = str(class_name or "").strip().title()

    if cls in _FULL_CASTERS:
        return dict(_FULL.get(level, {}))
    if cls in _HALF_CASTERS:
        return dict(_HALF.get(level, {}))
    if cls in _PACT_CASTERS:
        sl = _PACT_SLOT_LEVEL.get(level, "1")
        ct = _PACT_SLOT_COUNT.get(level, 1)
        return {sl: ct}
    return {}


def get_spellcasting_ability(class_name: str) -> Optional[str]:
    """Return the spellcasting ability (lowercase) for this class, or None."""
    return SPELLCASTING_ABILITY.get(str(class_name or "").strip().title())
