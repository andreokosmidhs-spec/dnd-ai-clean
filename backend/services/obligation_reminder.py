"""
Immersive paused-quest reminder narration.

When the player has pending obligations (paused storylines with NPCs waiting),
this service occasionally surfaces a flavoured world-event beat in the Adventure Log:
a raven bearing a lord's seal, a street urchin with a note, a whispered rumour at
the tavern bar — tailored to the NPC type, urgency, and mission kind.
"""

from __future__ import annotations

import logging
import os
import random
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Per-turn fire probability by urgency tier.
_FIRE_PROBABILITY = {
    "critical": 0.40,
    "high":     0.25,
    "medium":   0.15,
    "patient":  0.08,
}

# Delivery flavour keyed by mission type — the "fiction envelope" the reminder arrives in.
_DELIVERY_BY_MISSION = {
    "rescue":             "a breathless runner who finds you in the street",
    "heist":              "a coded note slipped into your pocket",
    "assassination":      "a whispered name pressed into your ear at the bar",
    "political_intrigue": "a rumour drifting across the common room",
    "escort":             "a city messenger bearing a sealed scroll",
    "investigation":      "a folded letter left with the innkeep",
    "dungeon":            "a hooded figure who falls into step beside you",
    "wilderness":         "a hawk bearing a rolled note tied to its leg",
}

_DELIVERY_BY_URGENCY = {
    "critical": "a breathless rider who reins up hard in front of you",
    "high":     "a city messenger bearing a sealed letter",
    "medium":   "a note left with the innkeep",
    "patient":  "a rumour drifting across the tavern",
}

# Title prefixes that imply a noble who would use a raven or formal courier.
_NOBLE_PREFIXES = {
    "lord", "lady", "baron", "baroness", "duke", "duchess",
    "count", "countess", "earl", "viscount", "king", "queen",
    "prince", "princess", "sir", "dame",
}


def _pick_delivery_method(obligation: Dict) -> str:
    slug = (obligation.get("mission_type_slug") or "").lower()
    urgency = (obligation.get("urgency") or "medium").lower()
    npc_names = obligation.get("npc_names") or []

    for name in npc_names:
        first_word = (name or "").strip().split()[0].lower().rstrip(".")
        if first_word in _NOBLE_PREFIXES:
            return "a raven bearing a wax-sealed letter"

    if slug in _DELIVERY_BY_MISSION:
        return _DELIVERY_BY_MISSION[slug]
    return _DELIVERY_BY_URGENCY.get(urgency, "a note left with the innkeep")


def _pick_most_urgent(obligations: List[Dict]) -> Optional[Dict]:
    order = {"critical": 0, "high": 1, "medium": 2, "patient": 3}
    active = [o for o in obligations if isinstance(o, dict) and o.get("urgency")]
    if not active:
        return None
    return min(active, key=lambda o: order.get(o.get("urgency", "patient"), 3))


def _should_fire(urgency: str) -> bool:
    return random.random() < _FIRE_PROBABILITY.get(urgency, 0.10)


async def generate_obligation_reminder(
    obligations: List[Dict],
    campaign: Dict,
    character: Dict,
) -> Optional[Dict]:
    """Maybe generate an immersive in-world reminder about a paused quest.

    Returns:
        {narration, storyline_id, storyline_title, npc_name, delivery_method, urgency}
        or None if no reminder fires this turn.
    """
    if not obligations:
        return None

    obligation = _pick_most_urgent(obligations)
    if obligation is None:
        return None

    urgency = (obligation.get("urgency") or "medium").lower()
    if not _should_fire(urgency):
        return None

    npc_names = obligation.get("npc_names") or []
    npc_name = npc_names[0] if npc_names else None
    storyline_title = obligation.get("storyline_title") or "a paused quest"
    summary = obligation.get("summary") or ""
    mission_type = obligation.get("mission_type_slug") or ""
    delivery_method = _pick_delivery_method(obligation)

    hero_name = ((character.get("identity") or {}).get("name") or "the adventurer")

    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        from uuid import uuid4

        npc_line = f"NPC: {npc_name}." if npc_name else "Anonymous contact — no named NPC."
        urgency_label = {
            "critical": "life-or-death urgent — the window is closing fast",
            "high":     "pressing — delay breeds real consequences",
            "medium":   "noticeable — the NPC has waited long enough",
            "patient":  "gentle nudge — still patient but not forgotten",
        }.get(urgency, "pending")

        system = (
            "You are a D&D Dungeon Master writing a 2-3 sentence atmospheric world-event beat. "
            "Narrate ONLY the physical arrival of the reminder — the moment the delivery reaches "
            "the player — in present tense, second person. "
            "Do NOT use 'you feel', 'you sense', 'you wonder', or any inner-state language. "
            "If the NPC sends a written message or spoken word, quote it (1 line max) in their voice. "
            "Keep it vivid and grounded. Stop after 3 sentences. No dice, no meta, no OOC."
        )
        prompt = (
            f"Paused quest: '{storyline_title}'.\n"
            f"{npc_line}\n"
            f"Context: {summary[:200]}\n"
            f"Urgency feel: {urgency_label}.\n"
            f"Delivery method: {delivery_method}.\n"
            f"Mission kind: {mission_type or 'unspecified'}.\n"
            f"Hero's name: {hero_name}.\n\n"
            "Write the delivery beat now."
        )

        chat = LlmChat(
            api_key=api_key,
            session_id=f"obligation-reminder-{uuid4().hex[:8]}",
            system_message=system,
        )
        chat.with_model("openai", "gpt-4o-mini").with_params(temperature=0.85, max_tokens=120)

        raw = (await chat.send_message(UserMessage(text=prompt))) or ""
        narration = raw.strip()
        if not narration:
            return None

        return {
            "narration": narration,
            "storyline_id": obligation.get("storyline_id"),
            "storyline_title": storyline_title,
            "npc_name": npc_name,
            "delivery_method": delivery_method,
            "urgency": urgency,
        }

    except Exception as exc:
        logger.warning(f"Obligation reminder generation failed (non-fatal): {exc}")
        return None
