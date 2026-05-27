"""
NPC delta tracking — records what changes about characters during play.

After each turn, a lightweight LLM call scans the DM narration for
meaningful NPC state changes: attitude shifts, secrets the player
learned, favours owed, promises made, items exchanged, location moves.

Deltas accumulate on the character card (character_deltas array, capped
at 20 entries). They are injected into the DM anchor block on the next
turn so past interactions shape every future scene.

The extraction only fires when at least one present NPC's name appears
in the narration — most turns that never mention a known NPC pay zero
cost.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_DELTA_TYPES = {"attitude", "secret", "favour", "promise", "item", "location", "note"}

# How each relationship tier shifts the NPC's social DCs relative to their base.
# Positive = harder for the player; negative = easier.
_TIER_MODIFIERS = {
    "grateful":  {"persuasion_dc": -4, "intimidation_dc": +3, "deception_dc": +1, "insight_dc":  0},
    "friendly":  {"persuasion_dc": -2, "intimidation_dc": +2, "deception_dc": +1, "insight_dc":  0},
    "neutral":   {"persuasion_dc":  0, "intimidation_dc":  0, "deception_dc":  0, "insight_dc":  0},
    "wary":      {"persuasion_dc": +2, "intimidation_dc": -1, "deception_dc": +2, "insight_dc": -1},
    "hostile":   {"persuasion_dc": +4, "intimidation_dc": -3, "deception_dc": +4, "insight_dc":  0},
}

_DC_MIN, _DC_MAX = 6, 22


def _attitude_tier(fact: str) -> str | None:
    """Map an attitude delta fact string to a relationship tier."""
    f = fact.lower()
    if any(w in f for w in ("hostile", "attacks", "threatens", "draws weapon", "furious", "enraged")):
        return "hostile"
    if any(w in f for w in ("dead", "killed", "slain", "dies", "died")):
        return "dead"
    if any(w in f for w in ("wary", "suspicious", "distrustful", "cautious", "uncertain")):
        return "wary"
    if any(w in f for w in ("grateful", "deeply thankful", "owes life", "indebted")):
        return "grateful"
    if any(w in f for w in ("friendly", "trusts", "ally", "allied", "friend", "warmly", "likes")):
        return "friendly"
    if any(w in f for w in ("neutral", "indifferent", "calm", "resolved", "diffused")):
        return "neutral"
    return None

_SYSTEM = (
    "You extract NPC relationship changes from D&D narration. "
    "Be conservative — only record what ACTUALLY happened this turn.\n\n"
    "Delta types:\n"
    "- attitude: how the NPC now feels toward the player (hostile/suspicious/friendly/grateful/wary/neutral)\n"
    "- secret: something the player learned about this NPC's past, motives, or hidden identity\n"
    "- favour: someone now owes someone something (specify who owes whom what)\n"
    "- promise: a commitment made this turn (by whom, to whom, what exactly)\n"
    "- item: something that changed hands between player and NPC\n"
    "- location: the NPC explicitly moved to a different named place\n"
    "- note: any other important relationship fact that will affect future interactions\n\n"
    "Output strict JSON only (no code fence):\n"
    '[{"npc": "exact name", "type": "...", "fact": "one concise sentence"}]\n'
    "If nothing changed for any NPC, output: []"
)


def _npc_mentioned(name: str, text: str) -> bool:
    return name.lower() in text.lower()


async def extract_npc_deltas(
    narration: str,
    player_action: str,
    npc_names: List[str],
    api_key: str = "",  # kept for backwards compat, unused — uses ANTHROPIC_API_KEY
) -> List[Dict]:
    """Return a list of {npc, type, fact} dicts for this turn. May return []."""
    if not narration or not npc_names:
        return []

    # Only call the LLM if at least one NPC is actually mentioned in the narration
    mentioned = [n for n in npc_names if _npc_mentioned(n, narration)]
    if not mentioned:
        return []

    try:
        from services.claude_client import call_haiku_async

        prompt = (
            f"NPCs in scene: {', '.join(mentioned)}\n\n"
            f"Player action: {player_action[:300]}\n\n"
            f"DM narration: {narration[:1200]}\n\n"
            "List ONLY state changes that occurred THIS turn. Ignore unchanged background facts."
        )
        raw = await call_haiku_async(_SYSTEM, prompt, max_tokens=200, temperature=0)
        s = raw.strip()
        if s.startswith("```"):
            s = re.sub(r"^```[a-z]*\n?", "", s).rstrip("`").strip()
        results = json.loads(s)
        if not isinstance(results, list):
            return []
        valid = []
        for r in results:
            if (
                isinstance(r, dict)
                and r.get("npc")
                and r.get("type") in _DELTA_TYPES
                and r.get("fact")
            ):
                valid.append({
                    "npc": str(r["npc"]).strip(),
                    "type": str(r["type"]).strip(),
                    "fact": str(r["fact"]).strip()[:200],
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                })
        return valid
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"NPC delta extraction failed (non-fatal): {exc}")
        return []


async def apply_npc_deltas(
    cards_collection,
    campaign_id: str,
    deltas: List[Dict],
) -> None:
    """Append deltas to the matching character cards, capped at 20 per NPC."""
    if not deltas or cards_collection is None:
        return

    # Group deltas by NPC name
    by_npc: Dict[str, List[Dict]] = {}
    for d in deltas:
        name = d.get("npc") or ""
        if name:
            by_npc.setdefault(name, []).append({
                "type": d["type"],
                "fact": d["fact"],
                "recorded_at": d.get("recorded_at") or datetime.now(timezone.utc).isoformat(),
            })

    for name, npc_deltas in by_npc.items():
        try:
            await cards_collection.update_one(
                {"campaign_id": campaign_id, "title": name, "type": "character"},
                # $push + $slice keeps the array capped at 20, newest at the end
                {"$push": {"character_deltas": {"$each": npc_deltas, "$slice": -20}}},
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Failed to write NPC deltas for {name!r}: {exc}")

        # Propagate attitude deltas → live card status + calibrated social DCs.
        # Only the first attitude delta per turn drives the update.
        attitude_delta = next((d for d in npc_deltas if d.get("type") == "attitude"), None)
        if attitude_delta:
            tier = _attitude_tier(attitude_delta.get("fact") or "")
            # Status mapping (grateful/friendly both read as "friendly" on the pill)
            _status_for_tier = {
                "hostile": "hostile", "dead": "dead", "wary": "wary",
                "grateful": "friendly", "friendly": "friendly", "neutral": "neutral",
            }
            new_status = _status_for_tier.get(tier or "")
            if tier and tier in _TIER_MODIFIERS:
                # Read current card to get base_stats (stored once, never overwritten)
                try:
                    card_doc = await cards_collection.find_one(
                        {"campaign_id": campaign_id, "title": name, "type": "character"},
                        {"secret_content": 1},
                    )
                    sec = (card_doc or {}).get("secret_content") or {}
                    base = sec.get("base_stats") or sec.get("stats") or {}
                    mods = _TIER_MODIFIERS[tier]
                    new_stats = {
                        k: max(_DC_MIN, min(_DC_MAX, (base.get(k) or 12) + mods[k]))
                        for k in ("persuasion_dc", "intimidation_dc", "deception_dc", "insight_dc")
                    }
                    update: Dict = {"secret_content.stats": new_stats}
                    if new_status:
                        update["status"] = new_status
                    # Persist base_stats once so future tier shifts always recalculate from it
                    if base and not sec.get("base_stats"):
                        update["secret_content.base_stats"] = base
                    await cards_collection.update_one(
                        {"campaign_id": campaign_id, "title": name, "type": "character"},
                        {"$set": update},
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(f"DC tier update failed for {name!r}: {exc}")
            elif new_status:
                # dead or unrecognised tier — just update status
                try:
                    await cards_collection.update_one(
                        {"campaign_id": campaign_id, "title": name, "type": "character"},
                        {"$set": {"status": new_status}},
                    )
                except Exception:
                    pass


_TIER_DOWNGRADE = {
    "grateful": "friendly",
    "friendly": "neutral",
    "neutral":  "wary",
    "wary":     "hostile",
    "hostile":  "hostile",
}


async def downgrade_npc_relationship(
    cards_collection,
    campaign_id: str,
    npc_name: str,
    reason: str,
) -> None:
    """
    Drop an NPC one relationship tier on a failed social check.
    Writes an attitude delta and updates live DCs — deterministic, no LLM needed.
    """
    if not cards_collection or not npc_name:
        return
    try:
        card = await cards_collection.find_one(
            {"campaign_id": campaign_id, "title": npc_name, "type": "character"},
            {"status": 1, "secret_content": 1},
        )
        if not card:
            return
        current_tier = card.get("status", "neutral")
        new_tier = _TIER_DOWNGRADE.get(current_tier, "wary")
        if new_tier == current_tier:
            return  # already at floor

        fact = f"{npc_name} is now {new_tier} toward the player — {reason}"
        delta = {
            "type": "attitude",
            "fact": fact,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        await cards_collection.update_one(
            {"campaign_id": campaign_id, "title": npc_name, "type": "character"},
            {"$push": {"character_deltas": {"$each": [delta], "$slice": -20}}},
        )
        # Recalculate DCs for the new tier
        await apply_npc_deltas(
            cards_collection,
            campaign_id,
            [{"npc": npc_name, **delta}],
        )
        logger.info(f"📉 NPC relationship downgraded: {npc_name} {current_tier} → {new_tier}")
    except Exception as exc:
        logger.warning(f"NPC relationship downgrade failed (non-fatal): {exc}")


def render_deltas_for_prompt(deltas: List[Dict], limit: int = 8) -> str:
    """Format the most recent N deltas as a compact single-line history string."""
    if not deltas:
        return ""
    recent = deltas[-limit:]
    parts = [f"[{d.get('type','note')}] {d.get('fact','')}" for d in recent if d.get("fact")]
    return " | ".join(parts) if parts else ""
