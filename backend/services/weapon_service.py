"""Resolve which weapon a player is attacking with.

Priority order:
1. If a card_id is provided, find that card in deck_cards and parse its mechanical text
2. Fall back to class-based default weapon
"""
import re
from typing import Dict, Any, Optional, List

# Default weapon by class name (key = lowercase class name)
CLASS_DEFAULT_WEAPONS = {
    "fighter":    {"name": "Longsword",    "damage_die": "1d8",  "weapon_type": "melee"},
    "paladin":    {"name": "Longsword",    "damage_die": "1d8",  "weapon_type": "melee"},
    "barbarian":  {"name": "Greataxe",     "damage_die": "1d12", "weapon_type": "melee"},
    "ranger":     {"name": "Longbow",      "damage_die": "1d8",  "weapon_type": "ranged"},
    "rogue":      {"name": "Shortsword",   "damage_die": "1d6",  "weapon_type": "finesse"},
    "monk":       {"name": "Unarmed",      "damage_die": "1d6",  "weapon_type": "melee"},
    "wizard":     {"name": "Quarterstaff", "damage_die": "1d6",  "weapon_type": "melee"},
    "sorcerer":   {"name": "Dagger",       "damage_die": "1d4",  "weapon_type": "finesse"},
    "warlock":    {"name": "Pact Blade",   "damage_die": "1d8",  "weapon_type": "melee"},
    "bard":       {"name": "Rapier",       "damage_die": "1d8",  "weapon_type": "finesse"},
    "cleric":     {"name": "Mace",         "damage_die": "1d6",  "weapon_type": "melee"},
    "druid":      {"name": "Scimitar",     "damage_die": "1d6",  "weapon_type": "finesse"},
}

_FALLBACK = {"name": "Unarmed Strike", "damage_die": "1d4", "weapon_type": "melee"}

# Parse damage die from mechanical text e.g. "1d8 piercing damage, Versatile (1d10)"
_DIE_PATTERN = re.compile(r'\b(\d+d\d+(?:\+\d+)?)\b')
_WEAPON_TYPE_KEYWORDS = {
    "ranged": ["bow", "crossbow", "dart", "sling", "thrown"],
    "finesse": ["rapier", "shortsword", "dagger", "whip", "scimitar"],
}


def _parse_weapon_type_from_text(text: str) -> str:
    t = text.lower()
    for wtype, keywords in _WEAPON_TYPE_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return wtype
    return "melee"


def _get_class_name(character_state: Dict[str, Any]) -> str:
    cls = character_state.get("class_") or character_state.get("class") or {}
    if isinstance(cls, dict):
        return (cls.get("name") or cls.get("key") or "").strip().lower()
    return str(cls).strip().lower()


def resolve_player_weapon(
    character_state: Dict[str, Any],
    card_used_id: Optional[str],
    deck_cards: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """Return {name, damage_die, weapon_type} for the player's attack."""
    # Try card first
    if card_used_id and deck_cards:
        card = next((c for c in deck_cards if c.get("id") == card_used_id), None)
        if card:
            mech = card.get("mechanical") or ""
            title = card.get("title") or ""
            combined = f"{title} {mech}"
            # Extract damage die from mechanical text
            die_matches = _DIE_PATTERN.findall(combined)
            if die_matches:
                damage_die = die_matches[0]
                weapon_type = _parse_weapon_type_from_text(combined)
                return {"name": title, "damage_die": damage_die, "weapon_type": weapon_type}
    # Fall back to class default
    class_name = _get_class_name(character_state)
    for key, weapon in CLASS_DEFAULT_WEAPONS.items():
        if key in class_name:
            return dict(weapon)
    return dict(_FALLBACK)
