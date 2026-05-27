"""Roleplay Chaos meter.

Each campaign carries a `chaos` integer (0..100) on its `world_state`. After
every player action, a small LLM call evaluates whether the action ALIGNED
with or VIOLATED the character's ideal/bond/flaw. Violations raise chaos by
a severity-weighted amount; alignment lets it slowly cool. When chaos crosses
threshold, a curse card may be drafted into the player's deck.

The system is always-on but lightweight:
  * One small `gpt-4o-mini` call per turn, tight JSON output, ~1s latency.
  * Heuristic fallback if the LLM call fails — chaos doesn't move on errors.
  * Curse roll is weighted: chance = chaos / 200, capped at 35%.

Curse cards come from a small static catalog (4 per rarity tier) and can also
be LLM-flavored to the campaign.
"""
from __future__ import annotations

import json as _json
import logging
import random
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from services.claude_client import call_haiku_async

logger = logging.getLogger(__name__)

DEFAULT_CHAOS = 0
MAX_CHAOS = 100

# Severity → chaos delta. Severity 0 (aligned) cools chaos slightly.
_CHAOS_DELTA = {0: -3, 1: 4, 2: 9, 3: 16}

# Curse catalog — title, description, rarity, mechanical.
_CURSE_CATALOG = [
    # Common (chaos 1-30)
    {"title": "Restless Sleep", "rarity": "common",
     "description": "Your dreams are uneasy. Long rests restore only half their normal effect for the next 24 hours.",
     "mechanical": "½ rest benefit · 24 h"},
    {"title": "Lingering Stench", "rarity": "common",
     "description": "Something on you draws strays and merchants alike to wrinkle their nose. Disadvantage on Persuasion until you bathe in clear water.",
     "mechanical": "Disadv: Persuasion until cleansed"},
    {"title": "Shaking Hands", "rarity": "common",
     "description": "A nervous tremor settles in your fingers. The next fine-motor check (Sleight of Hand, lockpicking, calligraphy) is at disadvantage.",
     "mechanical": "Next fine-motor check: disadvantage"},
    {"title": "Unwelcome Echo", "rarity": "common",
     "description": "Your footsteps echo louder than they should — Stealth checks within walls/buildings are at -2 until next dawn.",
     "mechanical": "-2 Stealth indoors · until dawn"},

    # Rare (chaos 30-60)
    {"title": "Witnessed", "rarity": "rare",
     "description": "Someone present saw what you did. They will tell others — and one of them, somewhere in this region, now knows your name and face.",
     "mechanical": "New unfriendly NPC · regional"},
    {"title": "Marked by the Faith", "rarity": "rare",
     "description": "A nearby temple's wards flicker when you pass. Priests of the local faith may refuse you service or worse.",
     "mechanical": "Disadv vs religious factions"},
    {"title": "Petty Thief's Shadow", "rarity": "rare",
     "description": "A small handful of coin or a minor item is missing the next time you check your pack. The thief watches from a distance now.",
     "mechanical": "Lose 1d10 gp or one minor item"},
    {"title": "Bad Omen", "rarity": "rare",
     "description": "You roll one fewer die when you have advantage on the next two ability checks; the world has decided to make this harder.",
     "mechanical": "No advantage · next 2 checks"},

    # Epic (chaos 60-90)
    {"title": "Hunted by Fate", "rarity": "epic",
     "description": "An ill-favored stranger has been asking after you in the streets — name, face, last seen direction. They are getting closer.",
     "mechanical": "Active threat · pursues across regions"},
    {"title": "The Curse of Hollow Sleep", "rarity": "epic",
     "description": "You cannot regain hit points from rests until a cleric of 5th level or higher lifts the curse, or you complete an act of redress.",
     "mechanical": "No rest healing · until cleansed"},
    {"title": "Disease: Crawling Pox", "rarity": "epic",
     "description": "You shake with fever. Maximum hit points reduced by 1d4 every dawn until cured. Highly contagious.",
     "mechanical": "Max HP -1d4/day · contagious"},

    # Legendary (chaos 90-100)
    {"title": "Geas of the Wronged Powers", "rarity": "legendary",
     "description": "A binding compulsion settles into your soul. You feel the pull of an act of penance — you do not yet know its shape, only that you will not rest until it is done.",
     "mechanical": "Quest-grade compulsion"},
]


def get_chaos(campaign: Dict) -> int:
    ws = (campaign or {}).get("world_state") or {}
    try:
        v = int(ws.get("chaos", DEFAULT_CHAOS))
    except Exception:  # noqa: BLE001
        v = DEFAULT_CHAOS
    return max(0, min(MAX_CHAOS, v))


def chaos_tier(chaos: int) -> Dict:
    """Bucket chaos for UI coloring."""
    if chaos <= 15:
        return {"key": "calm",       "label": "Calm",       "color": "emerald"}
    if chaos <= 35:
        return {"key": "stirring",   "label": "Stirring",   "color": "lime"}
    if chaos <= 55:
        return {"key": "agitated",   "label": "Agitated",   "color": "amber"}
    if chaos <= 75:
        return {"key": "turbulent",  "label": "Turbulent",  "color": "orange"}
    if chaos <= 90:
        return {"key": "perilous",   "label": "Perilous",   "color": "red"}
    return {"key": "consuming", "label": "Consuming", "color": "rose"}


async def evaluate_alignment(character: Dict, player_action: str) -> Dict:
    """Tiny LLM call: judge the player_action against the character's
    ideal/bond/flaw. Returns {severity: 0..3, axis: 'ideal'|'bond'|'flaw'|null,
    reason: str}. Severity 0 = aligned (cools chaos); 1-3 = violation."""
    bg = (character or {}).get("background") or {}
    personality = bg.get("personality") or {}
    ideal = (personality.get("ideal") or "").strip()
    bond = (personality.get("bond") or "").strip()
    flaw = (personality.get("flaw") or "").strip()

    fallback = {"severity": 0, "axis": None, "reason": ""}
    if not (ideal or bond or flaw) or not (player_action or "").strip():
        return fallback

    try:
        prompt = (
            "You are a roleplay alignment judge for a D&D campaign. The player has just "
            "declared an action. Evaluate whether it aligns with or violates the "
            "character's roleplay anchors.\n\n"
            f"=== CHARACTER ANCHORS ===\n"
            f"Ideal: {ideal or '(none)'}\n"
            f"Bond:  {bond or '(none)'}\n"
            f"Flaw:  {flaw or '(none)'}\n\n"
            f"=== PLAYER'S ACTION ===\n{player_action[:500]}\n\n"
            "=== RULES ===\n"
            "- Severity 0 = action is consistent with the character's ideal/bond, OR "
            "  honestly indulges the flaw (a thief stealing trinkets IS a flaw indulgence "
            "  for 'Sticky fingers' — that's flat 0, no violation).\n"
            "- Severity 1 = small drift (e.g. a 'protect the weak' character ignores someone in distress).\n"
            "- Severity 2 = active violation (e.g. 'honor among thieves' character rats out a crew member).\n"
            "- Severity 3 = profound betrayal (e.g. 'crew members' bond character sells the crew to the watch).\n"
            "- Most actions are routine and should return 0. ONLY return >0 if a specific anchor is clearly "
            "  contradicted. Do NOT return >0 for actions that have no clear bearing on any anchor.\n"
            "- `axis` should be the anchor type that was violated/honored: 'ideal', 'bond', or 'flaw'. "
            "  Use null for severity 0 if no anchor was relevant.\n"
            "- `reason` is a TIGHT 1-sentence explanation (max 90 chars). For severity 0 with no anchor "
            "  contact, return an empty string.\n\n"
            "=== OUTPUT (strict JSON only, no code fence) ===\n"
            "{\"severity\": 0, \"axis\": null, \"reason\": \"\"}\n"
        )
        raw = await call_haiku_async(
            "You judge roleplay alignment. Output strict JSON only. Be conservative — most actions are 0.",
            prompt,
            max_tokens=150,
            temperature=0,
        ) or ""
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        try:
            data = _json.loads(text)
        except Exception:
            s, e = text.find("{"), text.rfind("}")
            data = _json.loads(text[s : e + 1]) if s != -1 and e > s else fallback

        try:
            sev = int(data.get("severity", 0))
        except Exception:  # noqa: BLE001
            sev = 0
        sev = max(0, min(3, sev))
        axis = data.get("axis") if data.get("axis") in {"ideal", "bond", "flaw"} else None
        reason = str(data.get("reason") or "")[:160]
        return {"severity": sev, "axis": axis, "reason": reason}
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"alignment eval failed: {exc}")
        return fallback


def _pick_curse(chaos: int, rng: Optional[random.Random] = None) -> Dict:
    """Pick a curse template scaled to chaos:
       1-30 → common; 30-60 → rare; 60-90 → epic; 90+ → legendary."""
    rng = rng or random.Random()
    if chaos >= 90:
        tier = "legendary"
    elif chaos >= 60:
        tier = "epic"
    elif chaos >= 30:
        tier = "rare"
    else:
        tier = "common"
    pool = [c for c in _CURSE_CATALOG if c["rarity"] == tier]
    if not pool:
        pool = _CURSE_CATALOG
    return rng.choice(pool)


def roll_for_curse(chaos: int, rng: Optional[random.Random] = None) -> bool:
    """Probability of drafting a curse this turn = chaos / 200, capped at 35%.
    Below 30 chaos, no roll happens."""
    rng = rng or random.Random()
    if chaos < 30:
        return False
    chance = min(chaos / 200.0, 0.35)
    return rng.random() < chance


def apply_alignment_delta(current_chaos: int, severity: int) -> int:
    """Return the new chaos value after applying a severity result."""
    delta = _CHAOS_DELTA.get(severity, 0)
    return max(0, min(MAX_CHAOS, current_chaos + delta))


def build_curse_card_payload(chaos: int) -> Dict:
    """Pick a curse template + format it as a `/deck/draw` body."""
    tpl = _pick_curse(chaos)
    return {
        "source": "curse",
        "title": tpl["title"],
        "description": tpl["description"],
        "rarity": tpl["rarity"],
        "mechanical": tpl["mechanical"],
        "tags": ["curse", "chaos-drafted"],
    }


def chaos_block_for_dm(chaos: int) -> str:
    """Tight block for the DM prompt so narration can reflect chaos pressure
    in subtle ways (the world tilts against the character at higher chaos)."""
    tier = chaos_tier(chaos)
    flavor = {
        "calm":       "World aligns with the character's path; no special pressure.",
        "stirring":   "Small dissonance — a glance lingers, a coin goes missing in a pocket.",
        "agitated":   "The world begins to push back: doors stick, dogs bark, strangers misremember.",
        "turbulent":  "Misfortune compounds — accidents and unlucky timing weave through scenes.",
        "perilous":   "Open enmity surfaces — wronged parties recognize the character on sight.",
        "consuming":  "Calamity is imminent. Every breath of fortune is borrowed and overdue.",
    }[tier["key"]]
    return (
        "=== CHAOS METER ===\n"
        f"Current chaos: {chaos}/100 ({tier['label']}). {flavor} "
        "Reflect this pressure subtly in narration — don't announce 'chaos' as a "
        "number; let it color the world's reactions to the character."
    )
