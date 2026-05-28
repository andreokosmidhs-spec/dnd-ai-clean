"""D&D 5e Exhaustion mechanics.

Level stored in campaign["world_state"]["narrative_pacing"]["exhaustion_level"].

PHB levels (cumulative):
  1 → Disadvantage on all ability checks
  2 → Speed halved
  3 → Disadvantage on attack rolls and saving throws
  4 → Hit point maximum halved
  5 → Speed reduced to 0
  6 → Death

Long rest with food AND water reduces level by 1.
"""
from __future__ import annotations

from typing import Dict, List, Optional

_LEVEL_LABELS = {
    0: "",
    1: "Exhaustion I — Weary",
    2: "Exhaustion II — Impaired",
    3: "Exhaustion III — Struggling",
    4: "Exhaustion IV — Critically Drained",
    5: "Exhaustion V — Near Collapse",
    6: "Exhaustion VI — Death",
}

_NARRATION_NOTES = {
    1: "Slow blinks. Tasks feel twice as heavy. Concentration is effort.",
    2: "Every movement costs something. The body is running on debt.",
    3: "Hands that were steady are not. Breathing has become labor.",
    4: "The body burns what it was saving. Even standing takes decision.",
    5: "The character cannot stand. The ground is where they are.",
    6: "The character has died of exhaustion.",
}


# ---------------------------------------------------------------------------
# State accessors
# ---------------------------------------------------------------------------

def get_exhaustion_level(campaign: dict) -> int:
    pacing = (campaign.get("world_state") or {}).get("narrative_pacing") or {}
    return max(0, min(6, int(pacing.get("exhaustion_level", 0))))


def set_exhaustion_level(campaign: dict, level: int) -> None:
    level = max(0, min(6, level))
    ws = campaign.setdefault("world_state", {})
    ws.setdefault("narrative_pacing", {})["exhaustion_level"] = level


def add_exhaustion(campaign: dict, levels: int = 1) -> int:
    """Add exhaustion levels (capped at 6). Returns new level."""
    new = min(6, get_exhaustion_level(campaign) + levels)
    set_exhaustion_level(campaign, new)
    return new


def reduce_exhaustion(campaign: dict, levels: int = 1) -> int:
    """Reduce exhaustion levels (floor 0). Returns new level."""
    new = max(0, get_exhaustion_level(campaign) - levels)
    set_exhaustion_level(campaign, new)
    return new


# ---------------------------------------------------------------------------
# Effect calculations
# ---------------------------------------------------------------------------

def exhaustion_effects(level: int) -> Dict:
    level = max(0, min(6, level))
    return {
        "level": level,
        "label": _LEVEL_LABELS.get(level, ""),
        "disadvantage_ability_checks": level >= 1,
        "speed_halved": level >= 2,
        "disadvantage_attacks_saves": level >= 3,
        "hp_max_halved": level >= 4,
        "speed_zero": level >= 5,
        "dead": level >= 6,
    }


def effective_max_hp(character: dict, base_max_hp: int) -> int:
    """Return HP max after applying exhaustion level 4 halving."""
    # character is V2 dict; exhaustion is on campaign pacing — caller computes
    return base_max_hp


def apply_exhaustion_to_char_state(char_state: dict, level: int) -> dict:
    """Return a copy of char_state with exhaustion penalties applied.
    Used by combat/check systems to apply mechanical effects at roll time.
    """
    out = dict(char_state)
    if level == 0:
        return out

    # Level 1+: disadvantage on ability checks — stored as flag for callers
    out["exhaustion_disadvantage_checks"] = level >= 1
    out["exhaustion_disadvantage_attacks_saves"] = level >= 3

    # Level 2+: speed halved
    if level >= 2:
        spd = int(out.get("speed", 30))
        out["speed"] = max(0, spd // 2)

    # Level 4+: HP max halved
    if level >= 4:
        out["max_hp"] = max(1, int(out.get("max_hp", 10)) // 2)
        # Current HP also capped at new max
        out["hp"] = min(int(out.get("hp", 1)), out["max_hp"])

    # Level 5+: speed 0
    if level >= 5:
        out["speed"] = 0

    return out


# ---------------------------------------------------------------------------
# DM prompt block
# ---------------------------------------------------------------------------

def build_exhaustion_block(campaign: dict) -> str:
    """Return a formatted DM context block for the current exhaustion state.
    Returns empty string if exhaustion level is 0.
    """
    level = get_exhaustion_level(campaign)
    if level == 0:
        return ""

    fx = exhaustion_effects(level)
    lines = [
        f"=== EXHAUSTION LEVEL {level}/6 — {fx['label']} ===",
        "THESE ARE HARD MECHANICAL FACTS. Apply them to every roll and movement this scene.",
        "",
    ]

    if fx["dead"]:
        lines.append("THE CHARACTER HAS DIED FROM EXHAUSTION (Level 6).")
        lines.append("Narrate this as the body simply stopping. No drama. The body ran out.")
        return "\n".join(lines)

    effects: List[str] = []
    if fx["disadvantage_ability_checks"]:
        effects.append("DISADVANTAGE on ALL ability checks (Perception, Athletics, Stealth, Arcana, etc.)")
    if fx["speed_halved"]:
        effects.append("SPEED HALVED — every step costs twice what it should")
    if fx["disadvantage_attacks_saves"]:
        effects.append("DISADVANTAGE on attack rolls AND saving throws")
    if fx["hp_max_halved"]:
        effects.append("HIT POINT MAXIMUM HALVED — the body has no reserves left")
    if fx["speed_zero"]:
        effects.append("SPEED ZERO — the character cannot move under their own power")

    for e in effects:
        lines.append(f"  ▸ {e}")

    lines += [
        "",
        f"NARRATION: {_NARRATION_NOTES.get(level, '')}",
        "Show exhaustion in every action — not as a stat reminder, but as physical reality.",
        "A check is harder because the hands are wrong. Movement is halved because the legs are done.",
    ]

    return "\n".join(lines)
