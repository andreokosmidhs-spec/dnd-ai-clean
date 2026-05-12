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
    """HARD-rule prompt block telling the DM which sensory cues, NPC
    activities, and atmospheric language are permitted at the current
    hour — and which are FORBIDDEN. The DM must self-check before writing
    any narration.
    """
    b = bucket_for_hour(hour)
    key = b["key"]

    # Per-period guidance: light & sky, who's typically awake, who is
    # definitely NOT around, ambient sounds, and language to avoid.
    GUIDES = {
        "night": {
            "light": "deep darkness — only moonlight, lanterns, torches, or fire-glow. Streetlamps if the world has them; otherwise pitch-black between buildings.",
            "awake": "the Watch on patrol, sleepless drunks staggering home, thieves and informants who choose this hour, owls, stray dogs, a baker stoking the dawn ovens.",
            "asleep": "children, families, most merchants, market vendors, official offices, ordinary craftsfolk. They are inside, behind shutters.",
            "sounds": "boots on cobble echoing too loud, distant tavern brawls bleeding through walls, wind rattling shutters, a watchman's bell at the half-hour.",
            "forbid": "dawn light, morning mist, fresh-baked bread smells, merchants 'setting up', stalls open for business, children in the street, crowds in the market, the bustle of citizens.",
        },
        "dawn": {
            "light": "thin grey light just spilling between rooftops, sky bruising purple-to-orange in the east, lanterns being doused.",
            "awake": "bakers, the Watch changing shift, fishmongers heading to the wharf, early travellers, roosters, monks.",
            "asleep": "most citizens still abed, no children in the streets yet, taverns closed, stalls still shuttered.",
            "sounds": "first roosters, distant hammers, the creak of a baker's door, the slap of a fish-cart wheel.",
            "forbid": "noon sun, packed markets, children playing, full crowds, evening lanterns, midnight stillness.",
        },
        "morning": {
            "light": "clear golden light angling low across the rooftops; long shadows.",
            "awake": "merchants opening stalls, market traffic building, children on errands, the Watch on day-shift, craftsfolk at their benches.",
            "asleep": "drunks, late-night workers; taverns are slow but not closed.",
            "sounds": "stall bells, hawkers calling wares, hammers, wheelbarrow wheels, gossip at the well.",
            "forbid": "lanterns lit, twilight, sunset, midnight bells, deep shadows, drunks on the curb, sleeping streets.",
        },
        "midday": {
            "light": "harsh overhead sun; minimal shadows; heat shimmer over flagstones.",
            "awake": "the market at peak, lunchtime crowds, scribes, civic officials, midday Watch.",
            "asleep": "no one — full daylight bustle.",
            "sounds": "loud crowd hum, sizzling food carts, the noon bell, dogs panting in shade.",
            "forbid": "anything implying low light, lantern-light, twilight, evening chill, morning dew, late-afternoon slant.",
        },
        "afternoon": {
            "light": "warm slanting light, lengthening shadows. Dust motes visible in shafts.",
            "awake": "merchants still trading, journeymen on errands, schoolchildren released, courtiers strolling.",
            "asleep": "no one specifically.",
            "sounds": "afternoon hush after the noon peak, vendor calls softening, distant temple bells.",
            "forbid": "dawn light, morning bread, lanterns lit, midnight quiet.",
        },
        "late_afternoon": {
            "light": "golden hour, long shadows reaching across streets, sky beginning to flush.",
            "awake": "merchants closing up, workers heading home, taverns filling, the night Watch arriving.",
            "asleep": "no one — but children being called inside.",
            "sounds": "shutters being closed, stalls broken down, tavern doors swinging, the curfew bell warming up.",
            "forbid": "dawn, morning bustle, midday sun, midnight bells.",
        },
        "dusk": {
            "light": "the sky deep orange to violet; first lanterns lit; street corners darkening.",
            "awake": "tavern crowds, lamplighters, the night Watch, lovers, beggars finding doorways.",
            "asleep": "children, most merchants, market is closed, shutters closing one by one.",
            "sounds": "lamplighters' clicks, tavern song spilling out, dogs barking at lengthening shadows.",
            "forbid": "morning light, fresh bread baking, children in the street, market vendors at work.",
        },
        "evening": {
            "light": "full dark with pools of lantern-light; sky a deep ink; cool air settling.",
            "awake": "tavern patrons, late-shift Watch, smugglers, courtesans, gamblers, off-duty soldiers.",
            "asleep": "all families, all children, all daytime merchants and craftsfolk.",
            "sounds": "tavern noise, lanterns hissing, occasional drunken shouts, the curfew bell having tolled.",
            "forbid": "morning bustle, dawn light, fresh bread, children, open markets, midday sun.",
        },
        "midnight": {
            "light": "near-total darkness with only the moon and lantern-pools; everything beyond ten feet is shadow.",
            "awake": "the Watch, thieves and cutpurses, drunks, smugglers at the docks, the desperately ill seeking healers, owls, stray cats.",
            "asleep": "EVERYONE else — children, families, merchants, vendors, craftsfolk, clerics off-shift, courtiers. The streets are EMPTY of ordinary citizens. Shop shutters are bolted.",
            "sounds": "a distant tavern dying down, watchmen's footsteps echoing alone, a far-off dog, the wind, occasionally the harbour bells, a baby's cry quickly hushed inside.",
            "forbid": "MORNING LIGHT, DAWN, fresh bread smell, merchants 'setting up' or 'still setting up', open stalls, market crowds, children in the streets, children tugging at mothers' sleeves, parents and children on the street, watchmen 'sifting through produce', anything that implies daytime bustle.",
        },
    }
    g = GUIDES.get(key, GUIDES["morning"])

    return (
        f"=== TIME OF DAY (HARD RULE — check every sentence against this) ===\n"
        f"Current period: {b['label']} ({b['icon']}, hour {b['hour']:02d}/24).\n\n"
        f"LIGHT/SKY: {g['light']}\n"
        f"WHO'S AWAKE & IN PUBLIC: {g['awake']}\n"
        f"WHO IS ASLEEP / NOT IN THE STREETS: {g['asleep']}\n"
        f"AMBIENT SOUNDS: {g['sounds']}\n\n"
        f"FORBIDDEN at {b['label']} (do not write any of these, even as metaphor): "
        f"{g['forbid']}\n\n"
        f"Before you write each sentence, ask: 'Is this consistent with "
        f"{b['label']}?' If a beat's premise (e.g. 'children playing') is "
        f"impossible at the current hour, REWRITE the beat to something "
        f"plausible at this hour (a watchman's tipoff, a lone informant in "
        f"a doorway, the silence after a murder, a tavern emptying). "
        f"Reference time naturally — never quote the hour as a number, but "
        f"ALWAYS reflect it in the prose. Treat this as a hard constraint "
        f"that overrides any contradicting hook from earlier turns."
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

