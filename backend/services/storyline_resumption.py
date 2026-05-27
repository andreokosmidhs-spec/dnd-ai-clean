"""Paused-storyline resumption ruling.

When the player tries to pick up a paused storyline ("I head back to the
Anvil & Cup to find Hester"), the DM rules whether the thread is still
recoverable. A single LLM call given:

  - the paused storyline summary + the player's stated approach
  - hours elapsed since pause (real-time delta)
  - mission-type urgency
  - the campaign's current world clock (hour-of-day)

returns one of three rulings:

  ACTIVE   — still recoverable as-is. Resume with a tense reconnect beat.
  COLD     — recoverable but with concrete consequences (lost ally, harder
             DC, NPC mood shift). Resume; complications baked in.
  EXPIRED  — the thread is dead. Optional: emit a NEW lead-hook the player
             can pursue from a fresh angle (per product decision 2c).

Returned shape:

  {
    "ruling":   "active" | "cold" | "expired",
    "narration": str,           # 2-4 sentence Mercer-style ruling for the log
    "consequence": str,         # 1 sentence — what the player loses/gains by trying
    "new_lead":  Optional[{      # only when ruling=expired (DM's discretion)
        "hook_text": str,
        "hook_topic": str,
    }],
    "reasoning": str,            # internal — not shown to the player
  }
"""
from __future__ import annotations

import json as _json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from services.claude_client import call_haiku_async

logger = logging.getLogger(__name__)


def _strip_json_fence(s: str) -> str:
    s = (s or "").strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:].lstrip()
    return s


def _hours_since(iso_ts: Optional[str]) -> float:
    if not iso_ts:
        return 0.0
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        return max(0.0, delta.total_seconds() / 3600.0)
    except Exception:  # noqa: BLE001
        return 0.0


async def rule_on_resume_attempt(
    *,
    paused_storyline: Dict,
    pending_obligation: Optional[Dict],
    player_action: str,
    campaign_tone: str = "Balanced",
    clock_hour: int = 9,
) -> Optional[Dict]:
    """Single LLM call returning the structured ruling, or None when the
    LLM is unavailable / response is unparseable. Caller should default
    to a conservative {ruling:'cold', ...} fallback in that case."""
    action = (player_action or "").strip()
    if not action:
        return {
            "ruling": "cold",
            "narration": "You can't approach the thread without a stated direction.",
            "consequence": "No time lost; nothing learned.",
            "new_lead": None,
            "reasoning": "empty player_action",
        }
    hours = _hours_since((pending_obligation or {}).get("paused_at"))
    urgency = (pending_obligation or {}).get("urgency") or "medium"
    deadline_hours = (pending_obligation or {}).get("deadline_hours") or 96
    npcs = ", ".join((pending_obligation or {}).get("npc_names") or []) or "(no named NPCs)"
    locs = ", ".join((pending_obligation or {}).get("location_names") or []) or "(no named places)"
    summary = (pending_obligation or {}).get("summary") or paused_storyline.get("title") or "an investigation"

    sys_msg = (
        "You are a Matthew Mercer-style D&D Dungeon Master ruling on whether "
        "a paused storyline can still be recovered. Players do NOT teleport "
        "back to threads — they must EARN their way back through plausible "
        "in-fiction action. You judge fairly: if real time has passed and "
        "the thread was urgent, NPCs MAY have left, moved on, or hardened "
        "against the player. If the thread was patient or recent, recovery "
        "is usually possible at a cost. You always give the player something "
        "to do — never just 'nothing happens'. Output STRICT JSON only."
    )
    user_msg = (
        "=== PAUSED STORYLINE ===\n"
        f"Title: {paused_storyline.get('title','')}\n"
        f"Mission type: {(paused_storyline.get('mission_type') or {}).get('name','—')} "
        f"(slug: {(paused_storyline.get('mission_type') or {}).get('slug','—')})\n"
        f"Summary of what's unresolved: {summary[:300]}\n"
        f"Known NPCs involved: {npcs}\n"
        f"Known locations involved: {locs}\n\n"
        "=== TIMING ===\n"
        f"Real-time hours elapsed since pause: {hours:.1f}h "
        f"(~{hours / 24.0:.1f} in-fiction days assumed at 1:1 rate)\n"
        f"Mission urgency: {urgency} "
        f"(soft deadline ~{deadline_hours}h; consider this a guide, not a hard gate)\n"
        f"Current world clock: hour {clock_hour}/24 of the day\n\n"
        "=== PLAYER'S STATED RECONNECT ATTEMPT ===\n"
        f"\"{action[:400]}\"\n\n"
        "=== TASK — JUDGE THE RULING ===\n"
        "Choose ONE of three rulings based on (a) urgency vs hours elapsed, "
        "(b) whether the player's approach is plausible (asking the right "
        "NPC, going to the right place, at a reasonable hour), and (c) tone "
        f"of the campaign ({campaign_tone}):\n\n"
        "  'active'  — Thread is still warm and recoverable as-is. The "
        "player's approach makes sense. Narrate them reconnecting (the NPC "
        "is annoyed but still talks; the lead is still cold but not dead).\n"
        "  'cold'    — Recoverable but with COSTS. Maybe the key NPC has "
        "moved, a rival learned what the player knows, the price has gone "
        "up, OR an NPC is angry and will charge interest. Always give the "
        "player a concrete way forward, just with bite.\n"
        "  'expired' — The thread is dead in its original form. Key NPC has "
        "fled / been killed / moved out of reach. Player may need a new "
        "lead. AT YOUR DISCRETION (60% of expired rulings), emit a "
        "`new_lead` — a fresh hook for an alternate angle. Otherwise leave "
        "`new_lead` null (sunk cost).\n\n"
        "Rules of thumb:\n"
        "- urgency=critical, hours>48: lean toward expired.\n"
        "- urgency=high, hours>72: lean toward cold/expired.\n"
        "- urgency=patient, hours<168: usually active or cold.\n"
        "- If the player's approach is wildly implausible ('I go to a "
        "different city to find them'), lean colder.\n"
        "- ALWAYS include 2-4 sentences of Mercer-style narration. Source "
        "specifics in-fiction (a stall now empty, a witness who saw the NPC "
        "leave). NO 'somehow you sense', 'fate decides'.\n\n"
        "=== OUTPUT (strict JSON, no code fence) ===\n"
        "{\n"
        "  \"ruling\": \"active|cold|expired\",\n"
        "  \"narration\": \"2-4 sentences in second-person POV. Name the NPC/place. Use in-fiction sources.\",\n"
        "  \"consequence\": \"1 sentence — what is gained or lost by this attempt.\",\n"
        "  \"new_lead\": null OR {\n"
        "    \"hook_text\": \"single-sentence concrete hook the player can act on\",\n"
        "    \"hook_topic\": \"2-5 word noun phrase\"\n"
        "  },\n"
        "  \"reasoning\": \"one-sentence rationale, internal only\"\n"
        "}"
    )
    try:
        raw = await call_haiku_async(sys_msg, user_msg, max_tokens=400, temperature=0) or ""
        s = _strip_json_fence(raw)
        try:
            data = _json.loads(s)
        except Exception:
            a, b = s.find("{"), s.rfind("}")
            data = _json.loads(s[a:b + 1]) if a != -1 and b > a else {}
        if not isinstance(data, dict):
            return None
        ruling = (data.get("ruling") or "").strip().lower()
        if ruling not in {"active", "cold", "expired"}:
            ruling = "cold"
        out: Dict = {
            "ruling": ruling,
            "narration": (data.get("narration") or "").strip()[:900],
            "consequence": (data.get("consequence") or "").strip()[:240],
            "new_lead": None,
            "reasoning": (data.get("reasoning") or "").strip()[:200],
            "hours_elapsed": round(hours, 1),
            "urgency": urgency,
        }
        nl = data.get("new_lead")
        if isinstance(nl, dict) and (nl.get("hook_text") or "").strip():
            out["new_lead"] = {
                "hook_text": str(nl.get("hook_text") or "").strip()[:240],
                "hook_topic": str(nl.get("hook_topic") or "").strip()[:60],
            }
        return out
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"resume ruling failed: {exc}")
        return None
