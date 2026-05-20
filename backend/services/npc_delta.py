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
    api_key: str,
) -> List[Dict]:
    """Return a list of {npc, type, fact} dicts for this turn. May return []."""
    if not narration or not npc_names or not api_key:
        return []

    # Only call the LLM if at least one NPC is actually mentioned in the narration
    mentioned = [n for n in npc_names if _npc_mentioned(n, narration)]
    if not mentioned:
        return []

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        prompt = (
            f"NPCs in scene: {', '.join(mentioned)}\n\n"
            f"Player action: {player_action[:300]}\n\n"
            f"DM narration: {narration[:1200]}\n\n"
            "List ONLY state changes that occurred THIS turn. Ignore unchanged background facts."
        )
        chat = LlmChat(
            api_key=api_key,
            session_id="npc-delta-extract",
            system_message=_SYSTEM,
        )
        chat.with_model("openai", "gpt-4o-mini").with_params(temperature=0, max_tokens=200)
        raw = (await chat.send_message(UserMessage(text=prompt))) or ""
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

        # Propagate attitude deltas to card status for live status display
        for d in npc_deltas:
            if d.get("type") == "attitude":
                fact = (d.get("fact") or "").lower()
                new_status = None
                if any(w in fact for w in ("hostile", "attacks", "draws weapon", "threatens")):
                    new_status = "hostile"
                elif any(w in fact for w in ("dead", "killed", "slain", "dies", "died")):
                    new_status = "dead"
                elif any(w in fact for w in ("friendly", "grateful", "trusts", "allies", "warmly")):
                    new_status = "friendly"
                elif any(w in fact for w in ("neutral", "wary", "suspicious", "indifferent")):
                    new_status = "neutral"
                if new_status:
                    try:
                        await cards_collection.update_one(
                            {"campaign_id": campaign_id, "title": name, "type": "character"},
                            {"$set": {"status": new_status}},
                        )
                    except Exception:
                        pass
                break  # only the first attitude delta per turn changes status


def render_deltas_for_prompt(deltas: List[Dict], limit: int = 8) -> str:
    """Format the most recent N deltas as a compact single-line history string."""
    if not deltas:
        return ""
    recent = deltas[-limit:]
    parts = [f"[{d.get('type','note')}] {d.get('fact','')}" for d in recent if d.get("fact")]
    return " | ".join(parts) if parts else ""
