"""Lightweight time-of-day tracker.

Stores a single integer `clock_hour` (0..23) on the campaign's world_state.
Each player action can advance the clock by N hours; the LLM reports this as
`time_advance` in its JSON response so the DM gets to decide pace per scene
(quick conversation = 0-1h; investigating a building = 2h; travel = 4h+; long
rest = 8h).

The hour is bucketed into named periods for narration & UI:

  0-4   night          🌙
  5-6   dawn           🌅
  7-10  morning        ☀️
  11-13 midday         🌞
  14-16 afternoon      🌤️
  17-18 late afternoon 🌇
  19-20 dusk           🌆
  21-22 evening        🌃
  23    midnight       🌌

Bucket labels are short and human; the DM uses them in narration without
ever quoting the exact hour to keep the immersion clean.
"""
from __future__ import annotations

from typing import Dict, Tuple

# Default starting hour for new campaigns: morning.
DEFAULT_CLOCK_HOUR = 9

# (lower_inclusive, upper_inclusive, key, label, icon)
_BUCKETS: Tuple = (
    (0,  4,  "night",          "Night",          "🌙"),
    (5,  6,  "dawn",           "Dawn",           "🌅"),
    (7,  10, "morning",        "Morning",        "☀️"),
    (11, 13, "midday",         "Midday",         "🌞"),
    (14, 16, "afternoon",      "Afternoon",      "🌤️"),
    (17, 18, "late_afternoon", "Late Afternoon", "🌇"),
    (19, 20, "dusk",           "Dusk",           "🌆"),
    (21, 22, "evening",        "Evening",        "🌃"),
    (23, 23, "midnight",       "Midnight",       "🌌"),
)


def normalize_hour(hour: int) -> int:
    """Wrap any int into 0..23."""
    try:
        return int(hour) % 24
    except Exception:  # noqa: BLE001
        return DEFAULT_CLOCK_HOUR


def bucket_for_hour(hour: int) -> Dict:
    """Return {key, label, icon, hour} for the given hour. Wraps to 0..23."""
    h = normalize_hour(hour)
    for lo, hi, key, label, icon in _BUCKETS:
        if lo <= h <= hi:
            return {"key": key, "label": label, "icon": icon, "hour": h}
    # Should not happen — buckets cover full range.
    return {"key": "night", "label": "Night", "icon": "🌙", "hour": h}


def advance_clock(current_hour: int, advance_hours: int) -> int:
    """Advance the clock by `advance_hours` (clamped to 0..12 per turn so a
    single misbehaving LLM response can't fast-forward days). Wraps mod 24."""
    cur = normalize_hour(current_hour)
    try:
        delta = max(0, min(12, int(advance_hours)))
    except Exception:  # noqa: BLE001
        delta = 0
    return (cur + delta) % 24


def get_world_clock(campaign: Dict) -> int:
    """Read the current clock_hour from a campaign doc, defaulting to morning."""
    ws = (campaign or {}).get("world_state") or {}
    return normalize_hour(ws.get("clock_hour", DEFAULT_CLOCK_HOUR))


def time_context_block(hour: int) -> str:
    """Short prompt block the DM can be fed each turn so narration matches the
    current period. Kept tight to avoid bloating the system prompt."""
    b = bucket_for_hour(hour)
    return (
        f"=== TIME OF DAY ===\n"
        f"Current period: {b['label']} (hour {b['hour']:02d}/24).\n"
        f"Sensory cues should match this hour — light, sounds, who's awake, "
        f"how the streets behave. Reference time naturally (e.g. 'the lanterns "
        f"are being lit', 'the market hums full', 'a thin grey light spills "
        f"between the rooftops'); never quote the hour as a number."
    )


# -------------------- heuristic time advancement --------------------

import re as _re

_REST_LONG_RE = _re.compile(
    r"\b(long\s*rest|sleep\s*(?:through|until|for|the\s*night)|"
    r"rest\s*(?:the\s*night|until\s*(?:morning|dawn))|"
    r"until\s*(?:morning|dawn|sunrise))\b",
    _re.IGNORECASE,
)
_REST_SHORT_RE = _re.compile(
    r"\b(short\s*rest|catch\s*(?:my|your)\s*breath|take\s*a\s*break|"
    r"rest\s*for\s*an?\s*hour)\b",
    _re.IGNORECASE,
)
_TRAVEL_RE = _re.compile(
    r"\b(travel|journey|head\s+(?:to|toward|for)|make\s+(?:my|your)\s+way\s+to|"
    r"set\s+out\s+for|ride\s+to|walk\s+to|march\s+to|trek\s+to)\b",
    _re.IGNORECASE,
)
_THOROUGH_RE = _re.compile(
    r"\b(thoroughly|comb\s+through|search\s+every|interrogate\s+at\s+length|"
    r"wait\s+(?:for|until)|negotiate\s+at\s+length|stake\s*out|tail\s+(?:them|him|her))\b",
    _re.IGNORECASE,
)


def estimate_time_advance(player_action: str, narration: str = "") -> int:
    """Lightweight heuristic: how many in-fiction hours did this turn consume?

    Pure regex on player_action + DM narration. Returns 0..8.
      - 0  : quick beat (chat, glance, single check, brief look)
      - 1  : standard play (investigate a room, search a stall, short rest)
      - 2  : extended play (thorough search, stake-out, deep negotiation)
      - 3  : travel between districts / a few miles
      - 8  : long rest / sleep through the night

    Default is 0 to prevent runaway clock-jumping on routine turns.
    """
    text = (player_action or "") + " " + (narration or "")
    if _REST_LONG_RE.search(text):
        return 8
    if _TRAVEL_RE.search(text):
        return 3
    if _THOROUGH_RE.search(text):
        return 2
    if _REST_SHORT_RE.search(text):
        return 1
    return 0

