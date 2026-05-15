"""Off-hook storyline spawner.

When the player attempts an action that doesn't fit the active beat (e.g.
"I look for a beggar on the street" while the current scene is about
overheard Guild whispers), the DM should weave it into a NEW storyline
using the closest existing mission-type blueprint — instead of glueing
it onto the current scene.

This module is a single LLM call that, given:
  - the player's freeform action text,
  - the current beat's description (what's happening RIGHT NOW), and
  - the available mission-type blueprints (system + campaign-owned),

returns a structured decision:

  {
    "is_off_hook":        bool,   # True = spawn a new storyline
    "mission_type_slug":  str,    # closest existing slug (NEVER invents)
    "hook_text":          str,    # one-line hook to seed the new storyline
    "hook_topic":         str,    # short noun-phrase (4 words max)
    "reasoning":          str,    # one-sentence rationale (logged only)
  }

We deliberately never *generate* a brand-new mission type here — per the
product decision we always pick the closest existing blueprint. New
types are still authored via the explicit /mission-types/from-prompt
flow in Campaign Setup.
"""
from __future__ import annotations

import json as _json
import logging
import os
from typing import Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


def _strip_json_fence(s: str) -> str:
    s = (s or "").strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:].lstrip()
    return s


def _render_mission_palette(mission_types: List[Dict]) -> str:
    """Compact one-line-per-type listing for the classifier prompt."""
    if not mission_types:
        return "(no mission types available)"
    lines: List[str] = []
    for mt in mission_types[:12]:
        slug = mt.get("slug") or "?"
        name = mt.get("name") or slug
        icon = mt.get("icon") or ""
        desc = (mt.get("description") or "").strip().replace("\n", " ")[:140]
        lines.append(f"  - {slug}  | {icon} {name}: {desc}")
    return "\n".join(lines)


async def classify_action_for_spawn(
    *,
    player_action: str,
    current_beat_description: str,
    current_storyline_title: str,
    mission_types: List[Dict],
    narration_context: str = "",
) -> Optional[Dict]:
    """Returns a structured spawn decision dict, or None when the LLM is
    unavailable / the response is unparseable. Callers must default to
    {is_off_hook: False} on None to fall back to the normal flow."""
    action = (player_action or "").strip()
    if not action:
        return {"is_off_hook": False, "mission_type_slug": "", "hook_text": "", "hook_topic": "", "reasoning": "empty action"}
    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    palette = _render_mission_palette(mission_types or [])
    valid_slugs = ",".join((mt.get("slug") or "") for mt in (mission_types or []) if mt.get("slug"))

    sys_msg = (
        "You are an in-session D&D Dungeon Master deciding whether the "
        "player's stated action belongs to the CURRENT SCENE or whether "
        "it opens a NEW STORYLINE. You are STRICT about this — players "
        "often pivot, and pretending their off-topic action 'fits' the "
        "current beat is the #1 DM mistake. Output strict JSON only."
    )
    user_msg = (
        "=== CURRENT SCENE (what is happening RIGHT NOW) ===\n"
        f"Storyline title: {current_storyline_title or '(none)'}\n"
        f"Current beat description: {(current_beat_description or '')[:600]}\n"
        f"Recent narration: {(narration_context or '')[:400]}\n\n"
        "=== PLAYER'S STATED ACTION ===\n"
        f"\"{action[:400]}\"\n\n"
        "=== AVAILABLE MISSION TYPES (pick the CLOSEST fit; never invent) ===\n"
        f"{palette}\n\n"
        "=== TASK ===\n"
        "Decide:\n"
        "1. is_off_hook — TRUE if the action proposes a NEW investigation, "
        "person, place, or goal that is NOT the literal subject of the "
        "current beat. Concretely:\n"
        "   • The current beat is about 'whispering merchant about the "
        "Guild' but the player says 'I look for a beggar' → OFF-HOOK = TRUE.\n"
        "   • The current beat is about reading a posted bounty notice and "
        "the player says 'I ask the posting clerk for details' → "
        "OFF-HOOK = FALSE (same scene, same subject).\n"
        "   • The current beat is talking to NPC X and the player says "
        "'I attack X' or 'I bribe X' → OFF-HOOK = FALSE (same NPC).\n"
        "   When in DOUBT lean toward TRUE — players appreciate having "
        "their pivots taken seriously.\n"
        "2. mission_type_slug — IF off-hook=TRUE, pick the CLOSEST slug "
        f"from this exact list: [{valid_slugs}]. Match by intent: "
        "looking for a person → rescue or political_intrigue depending on "
        "tone; stealing or breaking-in → heist; targeted-kill → "
        "assassination. NEVER invent a slug not in the list.\n"
        "3. hook_text — IF off-hook=TRUE, a single-sentence hook that "
        "captures the NEW thread, rooted literally in the player's "
        "action. Examples — player says 'look for a beggar' → hook_text="
        "'A ragged figure crouches near the south gate; you've decided "
        "to find them and learn what they know.' Be concrete. NO "
        "metaphors. Mention 1 sensory or location anchor.\n"
        "4. hook_topic — 2-5 word noun phrase for the hook ('The Crouching "
        "Beggar', 'The Locked Vault', 'The Vanished Priest').\n"
        "5. reasoning — ONE sentence rationale (≤ 100 chars). Internal only.\n\n"
        "=== OUTPUT (strict JSON, no code fence) ===\n"
        "{\n"
        "  \"is_off_hook\": true,\n"
        "  \"mission_type_slug\": \"<one of the valid slugs OR empty string when is_off_hook=false>\",\n"
        "  \"hook_text\": \"<one-sentence concrete hook OR empty>\",\n"
        "  \"hook_topic\": \"<2-5 word noun phrase OR empty>\",\n"
        "  \"reasoning\": \"<one sentence>\"\n"
        "}"
    )
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=api_key,
            session_id=f"spawn-classify-{uuid4()}",
            system_message=sys_msg,
        )
        chat.with_model("openai", "gpt-4o-mini")
        raw = (await chat.send_message(UserMessage(text=user_msg))) or ""
        s = _strip_json_fence(raw)
        try:
            data = _json.loads(s)
        except Exception:
            a, b = s.find("{"), s.rfind("}")
            data = _json.loads(s[a:b + 1]) if a != -1 and b > a else {}
        if not isinstance(data, dict):
            return None
        # Defensive normalization.
        is_off = bool(data.get("is_off_hook"))
        slug = (data.get("mission_type_slug") or "").strip().lower()
        # Reject hallucinated slugs.
        valid_set = {(mt.get("slug") or "").lower() for mt in (mission_types or [])}
        if is_off and slug and slug not in valid_set:
            # Soft fallback: pick the first mission type as default.
            slug = next(iter(valid_set), "") if valid_set else ""
        return {
            "is_off_hook": is_off,
            "mission_type_slug": slug,
            "hook_text": (data.get("hook_text") or "").strip()[:280],
            "hook_topic": (data.get("hook_topic") or "").strip()[:60],
            "reasoning": (data.get("reasoning") or "").strip()[:160],
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"spawn classifier failed: {exc}")
        return None


def extract_pending_obligations_from_storyline(storyline: Dict) -> Dict:
    """Distill a paused storyline into a compact 'pending obligation' that
    the lean_dm prompt can reference. NPCs/locations the player has
    interacted with become 'people you owe an answer to'.

    Returns:
        {
          "storyline_id": str,
          "storyline_title": str,
          "summary": str,            # 1-2 sentence summary of what was left undone
          "npc_names": [str],        # named NPCs touched by this storyline (max 4)
          "location_names": [str],   # named places (max 3)
          "paused_at_beat": int,
          "paused_at": iso str,
          "urgency": str,            # "critical" | "high" | "medium" | "patient"
          "deadline_hours": int,     # informational only — DM rules with discretion
          "mission_type_slug": str,
        }
    """
    from datetime import datetime, timezone

    beats = storyline.get("beats") or []
    current = int(storyline.get("current_beat") or 0)
    npcs: List[str] = []
    locs: List[str] = []
    seen = set()
    for b in beats[: current + 1]:
        for t in (b.get("targets") or []):
            if not isinstance(t, dict):
                continue
            name = (t.get("name") or "").strip()
            t_type = (t.get("type") or "").strip().lower()
            if not name:
                continue
            key = (t_type, name.lower())
            if key in seen:
                continue
            seen.add(key)
            if t_type in {"npc", "character", "person"}:
                npcs.append(name)
            elif t_type in {"location", "place"}:
                locs.append(name)
    npcs = npcs[:4]
    locs = locs[:3]

    last_resolved = beats[max(0, current - 1)] if beats and current > 0 else (beats[0] if beats else {})
    last_outcome = (last_resolved.get("outcome_text") or last_resolved.get("description") or "")[:200]

    summary = (
        f"You walked away from '{storyline.get('title') or 'an investigation'}' "
        f"after starting to look into {last_outcome.strip()[:140] or 'an open lead'}. "
        f"It hasn't been resolved."
    )

    # Urgency derived from the mission-type slug — purely informational; the
    # resume endpoint's LLM call uses it as soft guidance, not a hard gate.
    slug = (storyline.get("mission_type") or {}).get("slug") or ""
    URGENCY_TABLE = {
        "rescue":             ("critical", 48),   # 2 days — life on the line
        "heist":              ("high",     72),   # 3 days — target may move
        "assassination":      ("high",     120),  # 5 days — mark may flee
        "political_intrigue": ("patient",  168),  # 7 days — slow burn
    }
    urgency_label, deadline_hours = URGENCY_TABLE.get(slug, ("medium", 96))

    return {
        "storyline_id": storyline.get("id"),
        "storyline_title": storyline.get("title") or "",
        "summary": summary,
        "npc_names": npcs,
        "location_names": locs,
        "paused_at_beat": current,
        "paused_at": datetime.now(timezone.utc).isoformat(),
        "urgency": urgency_label,
        "deadline_hours": deadline_hours,
        "mission_type_slug": slug,
    }


def render_pending_obligations_for_prompt(obligations: List[Dict]) -> str:
    """Render the campaign's pending_obligations into a system-prompt block
    instructing the DM that paused-storyline NPCs may seek the player out."""
    obligations = [o for o in (obligations or []) if isinstance(o, dict)]
    if not obligations:
        return ""
    lines = [
        "=== PENDING OBLIGATIONS (paused storylines the player walked away from) ===",
        "The player abandoned these threads mid-scene. The NPCs involved",
        "REMEMBER — they may seek the player out, glare from a stall, send a",
        "messenger, leave a sharp note, or confront them in passing. React",
        "ACCORDING TO EACH NPC'S PERSONALITY (a desperate informant pleads; a",
        "proud noble cuts them dead; a criminal contact warns then threatens).",
        "Reference these no more than once per scene unless the player engages.",
    ]
    for o in obligations[:4]:
        npcs = ", ".join(o.get("npc_names") or []) or "(no named NPCs)"
        locs = ", ".join(o.get("location_names") or []) or "(no named places)"
        lines.append(
            f"  - '{o.get('storyline_title','?')}' — {o.get('summary','')[:160]} "
            f"Involved NPCs: {npcs}. Places: {locs}."
        )
    lines.append("")
    return "\n".join(lines)
