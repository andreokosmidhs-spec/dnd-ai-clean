"""Light level resolution for D&D 5e combat.

Three tiers:
  bright  — full visibility, no modifiers
  dim     — lightly obscured; Perception DC +3; no attack penalty
  dark    — heavily obscured; blinded condition (disadvantage on attacks,
            attackers gain advantage) unless attacker has darkvision

Darkvision (racial trait):
  dark  → treats as dim light (normal attacks, Perception DC +3)
  dim   → treats as bright  (no modifiers at all)

Light sources override time-of-day (torch, magical light, etc.)
"""
from __future__ import annotations
from typing import Dict, Optional
from services.time_service import bucket_for_hour

# ── Tier definitions ─────────────────────────────────────────────────────────
LIGHT_LEVELS: Dict[str, Dict] = {
    "bright": {
        "label": "Bright Light",
        "icon": "☀️",
        "color": "yellow",
        "perception_dc_bonus": 0,
        "blinded": False,           # no attack modifier
        "css_overlay": None,
    },
    "dim": {
        "label": "Dim Light",
        "icon": "🌙",
        "color": "orange",
        "perception_dc_bonus": 3,
        "blinded": False,
        "css_overlay": "dim",       # subtle dark overlay on frontend
    },
    "dark": {
        "label": "Darkness",
        "icon": "🌑",
        "color": "red",
        "perception_dc_bonus": 5,
        "blinded": True,            # → disadvantage on attacks unless darkvision
        "css_overlay": "dark",      # heavy vignette on frontend
    },
}

# ── Clock-hour → outdoor light level ─────────────────────────────────────────
_BUCKET_OUTDOOR: Dict[str, str] = {
    "night":          "dark",
    "dawn":           "dim",
    "morning":        "bright",
    "midday":         "bright",
    "afternoon":      "bright",
    "late_afternoon": "dim",
    "dusk":           "dim",
    "evening":        "dim",
    "midnight":       "dark",
}

# Keywords in location names that imply underground / no natural light
_UNDERGROUND_KEYWORDS = (
    "cave", "cavern", "dungeon", "mine", "crypt", "tomb",
    "sewer", "underground", "basement", "cellar", "vault",
)

_INDOOR_KEYWORDS = (
    "tavern", "inn", "house", "hall", "chamber", "room",
    "shop", "store", "library", "temple", "keep", "tower",
    "castle", "fort", "building", "warehouse",
)


def _classify_location(location_name: str) -> str:
    """Return 'underground' | 'indoor' | 'outdoor'."""
    loc = (location_name or "").lower()
    if any(k in loc for k in _UNDERGROUND_KEYWORDS):
        return "underground"
    if any(k in loc for k in _INDOOR_KEYWORDS):
        return "indoor"
    return "outdoor"


def compute_light_level(
    clock_hour: int,
    location_name: str = "",
    has_torch: bool = False,
    has_magical_light: bool = False,
) -> Dict:
    """
    Determine battlefield light level.

    Priority:
      1. Magical light  → bright
      2. Torch          → dim  (simplified: bright close, dim far)
      3. Underground    → dark (always)
      4. Indoor + time  → depends on period (day = bright, night/eve = dim/dark)
      5. Outdoor + time → bucket from clock_hour
    """
    bucket = bucket_for_hour(clock_hour)
    key = bucket["key"]

    if has_magical_light:
        base, source = "bright", "magical light"
    elif has_torch:
        base, source = "dim", f"torchlight ({bucket['label']} outside)"
    else:
        loc_type = _classify_location(location_name)
        if loc_type == "underground":
            base, source = "dark", "underground"
        elif loc_type == "indoor":
            if key in ("night", "midnight"):
                base, source = "dark", f"night indoors"
            elif key in ("dawn", "dusk", "evening", "late_afternoon"):
                base, source = "dim", f"low natural light ({bucket['label']})"
            else:
                base, source = "bright", f"indoor daylight ({bucket['label']})"
        else:
            base = _BUCKET_OUTDOOR.get(key, "bright")
            source = f"{bucket['label']} {bucket['icon']}"

    info = dict(LIGHT_LEVELS[base])
    info["level"] = base
    info["source"] = source
    info["time_period"] = key
    info["time_icon"] = bucket["icon"]
    return info


def resolve_attacker_vision(
    light_level: Dict,
    attacker_has_darkvision: bool,
) -> Dict:
    """
    Return the effective light level for a specific attacker,
    accounting for darkvision.

    Returns {effective_level, disadvantage_on_attacks, advantage_for_targets, note}
    """
    level = light_level.get("level", "bright")
    blinded = light_level.get("blinded", False)

    if not blinded:
        return {
            "effective_level": level,
            "disadvantage_on_attacks": False,
            "advantage_for_targets": False,
            "note": None,
        }

    # darkness territory
    if attacker_has_darkvision:
        return {
            "effective_level": "dim",  # darkvision treats dark as dim
            "disadvantage_on_attacks": False,
            "advantage_for_targets": False,
            "note": "Darkvision: darkness treated as dim light",
        }

    return {
        "effective_level": "dark",
        "disadvantage_on_attacks": True,
        "advantage_for_targets": True,
        "note": "Blinded in darkness: attacks at disadvantage, enemies have advantage",
    }


def has_darkvision(character_cards: list) -> bool:
    """Check if character deck contains a Darkvision card."""
    return any(
        "darkvision" in (c.get("title") or "").lower()
        for c in (character_cards or [])
    )


def passive_condition_chip(light_level: Dict) -> Optional[str]:
    """One-line string suitable for displaying as a battlefield condition chip."""
    level = light_level.get("level", "bright")
    if level == "bright":
        return None
    icon = light_level.get("icon", "")
    label = light_level.get("label", "")
    source = light_level.get("source", "")
    if level == "dim":
        return f"{icon} {label} ({source}) · Perception DC+3"
    return f"{icon} {label} ({source}) · Attacks at disadvantage without darkvision"
