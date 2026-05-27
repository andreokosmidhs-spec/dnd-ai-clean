"""
Location transition detection — two lightweight signals that keep
world_state.current_location accurate without an extra LLM call.

Signal 1 (primary): a new location card was just auto-seeded this turn.
Signal 2 (secondary): movement keywords in the player action or DM narration
                      match the name of an already-known location card.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

_ARRIVAL_RE = re.compile(
    r"\b(?:arriv(?:e|es|ed|ing) at|enter(?:s|ed|ing)?|reach(?:es|ed|ing)?|"
    r"step(?:s|ped|ping)? into|walk(?:s|ed|ing)? into|pass(?:es|ed|ing)? through|"
    r"head(?:s|ed|ing)? (?:to|toward|towards|for|into)|"
    r"travel(?:s|ed|ing)? to|make(?:s|ing)? (?:your|their|his|her) way to|"
    r"return(?:s|ed|ing)? to|go(?:es|ing)?|went to|come(?:s|ing)? to|"
    r"set(?:s|ting)? (?:off|out) for|depart(?:s|ed|ing)? for)\b",
    re.IGNORECASE,
)


def detect_transition_from_new_cards(new_cards: List[Dict]) -> Optional[Dict]:
    """If auto-seed just created a location card, that IS the new current location."""
    for card in new_cards:
        if (card.get("type") or "").lower() == "location":
            return {"name": (card.get("title") or "").strip(), "card_id": card.get("id") or ""}
    return None


def detect_transition_from_known_locations(
    player_action: str,
    narration: str,
    known_location_cards: List[Dict],
) -> Optional[Dict]:
    """Check if player or narration implies moving to an already-known location.

    Only fires when movement keywords are present AND a known location name
    appears near them in the combined text.
    """
    combined = f"{player_action}\n{narration}".lower()
    if not _ARRIVAL_RE.search(combined):
        return None

    # Longest-name-first so "Silver Stag Inn" wins over "Inn"
    candidates = sorted(
        known_location_cards,
        key=lambda c: len(c.get("title") or ""),
        reverse=True,
    )
    for card in candidates:
        name = (card.get("title") or "").strip()
        if not name or len(name) < 3:
            continue
        if name.lower() in combined:
            return {"name": name, "card_id": card.get("id") or ""}
    return None
