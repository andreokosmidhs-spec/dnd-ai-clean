"""
Rest mechanics for D&D 5e.

Short rest: roll 1 hit die + CON mod, recover HP up to max.
             Warlock pact magic slots fully recover.
             Requires at least 1 hit die remaining.
Long rest:  full HP, all spell slots, clear short-term conditions.
             Recover max(1, level // 2) hit dice.
"""
from __future__ import annotations

import random
import re
from typing import Any, Dict, List, Optional, Tuple

from data.spell_slots import get_spell_slots

# Hit die by class (d-value only)
_HIT_DICE: Dict[str, int] = {
    "barbarian": 12,
    "fighter": 10, "paladin": 10, "ranger": 10,
    "bard": 8, "cleric": 8, "druid": 8, "monk": 8, "rogue": 8, "warlock": 8,
    "sorcerer": 6, "wizard": 6,
}

# Pact casters recover slots on short rest
_PACT_CASTERS = {"warlock"}

# Conditions that clear on a long rest
_LONG_REST_CLEARS = {"poisoned", "exhausted", "fatigued", "stunned", "frightened", "charmed"}
# Conditions that clear on a short rest (brief recovery)
_SHORT_REST_CLEARS = {"frightened"}

_LONG_REST_PATTERNS = re.compile(
    r"\b(long\s*rest|sleep\s*(?:through|until|for|the\s*night)|"
    r"rest\s*(?:through\s*the\s*night|the\s*night|until\s*(?:morning|dawn))|make\s*camp|"
    r"set\s*up\s*camp|camp\s*for\s*the\s*night|sleep)\b",
    re.IGNORECASE,
)
_SHORT_REST_PATTERNS = re.compile(
    r"\b(short\s*rest|catch\s*(?:my|our)\s*breath|take\s*a\s*(?:short\s*)?break|"
    r"rest\s*for\s*a(?:n\s*hour)?|bind\s*(?:my|our)\s*wounds|"
    r"tend\s*(?:to\s*)?(?:my|our)\s*wounds|take\s*a\s*moment)\b",
    re.IGNORECASE,
)


def detect_rest_intent(action: str) -> Optional[str]:
    """Return 'long', 'short', or None."""
    if _LONG_REST_PATTERNS.search(action):
        return "long"
    if _SHORT_REST_PATTERNS.search(action):
        return "short"
    return None


def _class_key(char_state: Dict[str, Any]) -> str:
    raw = char_state.get("class") or char_state.get("class_") or ""
    return str(raw).strip().lower()


def _con_mod(char_state: Dict[str, Any]) -> int:
    abilities = char_state.get("abilities") or char_state.get("stats") or {}
    con = abilities.get("con", 10) if isinstance(abilities, dict) else 10
    return (int(con) - 10) // 2


def _get_hit_dice_remaining(char_state: Dict[str, Any]) -> int:
    """Return current hit dice remaining; defaults to level (full) if not yet tracked."""
    stored = char_state.get("hit_dice_remaining")
    if stored is not None:
        return int(stored)
    return int(char_state.get("level", 1))


def compute_short_rest(char_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Short rest mechanics:
    - Requires at least 1 hit die remaining; returns no_hit_dice=True if none left
    - Roll 1 hit die + CON mod, minimum 1, capped at max_hp
    - Decrement hit_dice_remaining by 1
    - Warlocks recover all pact magic slots
    Returns a result dict (not the full char_state patch — caller merges).
    """
    cls = _class_key(char_state)
    hit_die = _HIT_DICE.get(cls, 8)
    con = _con_mod(char_state)
    level = int(char_state.get("level", 1))

    # Check hit dice availability
    hit_dice_remaining = _get_hit_dice_remaining(char_state)
    hit_dice_max = int(char_state.get("hit_dice_max", level))

    if hit_dice_remaining <= 0:
        # No hit dice left — can still short rest but no HP recovery
        current_hp = int(char_state.get("hp", 1))
        current_slots: Dict[str, int] = dict(char_state.get("spell_slots") or {})
        recovered_slots: Dict[str, int] = {}
        if cls in _PACT_CASTERS:
            full = get_spell_slots(cls.title(), level)
            for slot_lvl, count in full.items():
                prev = current_slots.get(slot_lvl, 0)
                current_slots[slot_lvl] = count
                if count > prev:
                    recovered_slots[slot_lvl] = count - prev
        conditions: List[str] = list(char_state.get("conditions") or [])
        cleared = [c for c in conditions if c.lower() in _SHORT_REST_CLEARS]
        conditions = [c for c in conditions if c.lower() not in _SHORT_REST_CLEARS]
        return {
            "rest_type": "short",
            "no_hit_dice": True,
            "hp": current_hp,
            "hp_gained": 0,
            "hit_die_roll": 0,
            "hit_die_type": hit_die,
            "con_mod": con,
            "hit_dice_remaining": 0,
            "hit_dice_max": hit_dice_max,
            "spell_slots": current_slots,
            "slots_recovered": recovered_slots,
            "conditions": conditions,
            "conditions_cleared": cleared,
        }

    # Spend 1 hit die
    roll = random.randint(1, hit_die)
    hp_gain = max(1, roll + con)
    hit_dice_remaining -= 1

    current_hp = int(char_state.get("hp", 1))
    max_hp = int(char_state.get("max_hp", current_hp))
    new_hp = min(max_hp, current_hp + hp_gain)
    actual_gain = new_hp - current_hp

    # Slot recovery: Warlock recovers all pact slots
    current_slots_2: Dict[str, int] = dict(char_state.get("spell_slots") or {})
    recovered_slots_2: Dict[str, int] = {}

    if cls in _PACT_CASTERS:
        full = get_spell_slots(cls.title(), level)
        for slot_lvl, count in full.items():
            prev = current_slots_2.get(slot_lvl, 0)
            current_slots_2[slot_lvl] = count
            if count > prev:
                recovered_slots_2[slot_lvl] = count - prev

    # Conditions — clear frightened on short rest
    conditions_2: List[str] = list(char_state.get("conditions") or [])
    cleared_2 = [c for c in conditions_2 if c.lower() in _SHORT_REST_CLEARS]
    conditions_2 = [c for c in conditions_2 if c.lower() not in _SHORT_REST_CLEARS]

    return {
        "rest_type": "short",
        "no_hit_dice": False,
        "hp": new_hp,
        "hp_gained": actual_gain,
        "hit_die_roll": roll,
        "hit_die_type": hit_die,
        "con_mod": con,
        "hit_dice_remaining": hit_dice_remaining,
        "hit_dice_max": hit_dice_max,
        "spell_slots": current_slots_2,
        "slots_recovered": recovered_slots_2,
        "conditions": conditions_2,
        "conditions_cleared": cleared_2,
    }


def compute_long_rest(char_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Long rest mechanics:
    - Full HP recovery
    - All spell slots restored to maximum
    - Recover max(1, level // 2) hit dice
    - Short-term conditions cleared
    Returns a result dict (caller merges into char_state).
    """
    cls = _class_key(char_state)
    level = int(char_state.get("level", 1))
    max_hp = int(char_state.get("max_hp", char_state.get("hp", 10)))
    current_hp = int(char_state.get("hp", max_hp))
    hp_gain = max_hp - current_hp

    # Restore all spell slots from table
    full_slots = get_spell_slots(cls.title(), level)
    current_slots = dict(char_state.get("spell_slots") or {})
    recovered_slots: Dict[str, int] = {}
    for slot_lvl, count in full_slots.items():
        prev = current_slots.get(slot_lvl, 0)
        current_slots[slot_lvl] = count
        if count > prev:
            recovered_slots[slot_lvl] = count - prev

    # Recover hit dice: regain max(1, level // 2), capped at hit_dice_max
    hit_dice_max = int(char_state.get("hit_dice_max", level))
    hit_dice_before = _get_hit_dice_remaining(char_state)
    hit_dice_recovered = max(1, level // 2)
    hit_dice_after = min(hit_dice_max, hit_dice_before + hit_dice_recovered)
    actual_dice_recovered = hit_dice_after - hit_dice_before

    # Clear long-rest conditions
    conditions: List[str] = list(char_state.get("conditions") or [])
    cleared = [c for c in conditions if c.lower() in _LONG_REST_CLEARS]
    conditions = [c for c in conditions if c.lower() not in _LONG_REST_CLEARS]

    return {
        "rest_type": "long",
        "hp": max_hp,
        "hp_gained": hp_gain,
        "spell_slots": current_slots,
        "spell_slots_max": full_slots,
        "slots_recovered": recovered_slots,
        "hit_dice_remaining": hit_dice_after,
        "hit_dice_max": hit_dice_max,
        "hit_dice_recovered": actual_dice_recovered,
        "conditions": conditions,
        "conditions_cleared": cleared,
    }


def build_rest_narration(rest_type: str, result: Dict[str, Any], location: str = "") -> str:
    """Generate atmospheric DM narration for the rest."""
    loc = f" in {location}" if location and location.lower() not in ("unknown", "") else ""

    if rest_type == "short":
        hp_gained = result.get("hp_gained", 0)
        roll = result.get("hit_die_roll", 0)
        die = result.get("hit_die_type", 8)
        slots = result.get("slots_recovered", {})
        no_dice = result.get("no_hit_dice", False)
        remaining = result.get("hit_dice_remaining", 0)
        hit_dice_max = result.get("hit_dice_max", 1)

        if no_dice:
            dice_line = " You have no hit dice remaining — you need a long rest to fully recover."
            hp_line = "You rest briefly, but have no reserves left to draw on."
        else:
            dice_line = f" ({remaining}/{hit_dice_max} hit dice remaining)"
            hp_line = (
                f"You bind your wounds and catch your breath, recovering {hp_gained} hit point{'s' if hp_gained != 1 else ''}."
                if hp_gained > 0
                else "You rest, but your wounds are too fresh to heal further."
            )

        slot_line = ""
        if slots:
            slot_line = " Your magical reserves return as you clear your mind."

        if no_dice:
            return f"You take a short rest{loc}. {hp_line}{dice_line}{slot_line}"

        con_str = ""
        if result.get("con_mod", 0) > 0:
            con_str = f" + {result['con_mod']}"
        elif result.get("con_mod", 0) < 0:
            con_str = f" - {abs(result['con_mod'])}"

        return (
            f"You take a short rest{loc}. "
            f"({roll} on a d{die}{con_str}) "
            f"{hp_line}{dice_line}{slot_line}"
        )

    else:  # long
        hp_gained = result.get("hp_gained", 0)
        slots = result.get("slots_recovered", {})
        cleared = result.get("conditions_cleared", [])
        dice_recovered = result.get("hit_dice_recovered", 0)
        hit_dice_remaining = result.get("hit_dice_remaining", 0)
        hit_dice_max = result.get("hit_dice_max", 1)

        recovery_lines = []
        if hp_gained > 0:
            recovery_lines.append(f"fully restored ({hp_gained} HP recovered)")
        else:
            recovery_lines.append("already at full health")
        if slots:
            total = sum(slots.values())
            recovery_lines.append(f"{total} spell slot{'s' if total != 1 else ''} recovered")
        if dice_recovered > 0:
            recovery_lines.append(
                f"{dice_recovered} hit {'die' if dice_recovered == 1 else 'dice'} recovered "
                f"({hit_dice_remaining}/{hit_dice_max} available)"
            )
        if cleared:
            recovery_lines.append(f"{', '.join(cleared)} cleared")

        recovery_str = "; ".join(recovery_lines) if recovery_lines else "well rested"

        return (
            f"You take a long rest{loc}, sleeping through the night. "
            f"When you wake, you feel refreshed — {recovery_str}. "
            f"You are ready to face whatever the day brings."
        )

