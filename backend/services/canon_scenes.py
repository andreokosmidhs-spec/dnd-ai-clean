"""Canon Scenes — auto-checkpointing system.

When a player PASSES a beat (via roll or creative approach), the resolved
beat becomes locked-in canon. The DM is told these scenes are established
truth and must not contradict them. The most recent canon scene is the
"current scene" — the DM's anchor.

Schema (collection: `canon_scenes`):
  {
    id: str,
    campaign_id: str,
    character_id: str,
    scene_number: int,             # monotonic per campaign
    storyline_id: str | None,
    storyline_title: str | None,
    beat_index: int | None,
    beat_title: str,
    title: str,                    # short scene title
    summary: str,                  # 2-3 sentence summary
    facts: List[str],              # bullet-point canon facts
    check_passed: dict | None,     # {check_type, dc, roll_total, quality}
    narration_snippet: str,        # last DM narration that became canon
    pitch_text: str | None,        # the player's pitch (if any)
    is_current: bool,
    created_at: datetime,
  }

Indexes (created on first use): (campaign_id, scene_number desc).
"""
from __future__ import annotations

import json as _json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _strip_json_fence(s: str) -> str:
    s = (s or "").strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:].lstrip()
    return s


async def _distill_canon(
    *, storyline_title: str, beat_title: str, beat_description: str,
    outcome_text: str, narration_snippet: str, check_type: Optional[str],
    dc: Optional[int], roll_total: Optional[int], pitch_text: Optional[str],
) -> Dict:
    """Single LLM call that produces {title, summary, facts[]} — the
    locked-in canon for this passed beat. Always returns something usable;
    falls back to deterministic strings if the LLM fails or is unavailable.
    """
    fallback = {
        "title": (beat_title or storyline_title or "Scene")[:80],
        "summary": (narration_snippet or outcome_text or beat_description or "")[:240],
        "facts": [],
    }
    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return fallback
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        check_block = (
            f"Resolved via: {check_type} (DC {dc}, roll {roll_total})"
            if check_type and dc is not None
            else "Resolved as a creative success."
        )
        pitch_block = f'\nPlayer pitch: "{pitch_text}"' if pitch_text else ""
        prompt = (
            "You are journaling a D&D scene that just resolved successfully. "
            "Lock in what HAPPENED as canon — what's now true in the world. "
            "Be concrete; only canonize what actually occurred, not what was "
            "implied. Output strict JSON only.\n\n"
            f"=== STORYLINE ===\n{storyline_title or '(untitled)'}\n\n"
            f"=== BEAT ===\nTitle: {beat_title}\nDescription: {beat_description[:600]}\n"
            f"What the player did: {outcome_text[:300]}\n"
            f"{check_block}{pitch_block}\n\n"
            f"=== DM NARRATION (snapshot) ===\n{narration_snippet[:800]}\n\n"
            "=== OUTPUT (strict JSON, no code fence) ===\n"
            "{\n"
            "  \"title\": \"<5-8 word scene title, evocative, no punctuation>\",\n"
            "  \"summary\": \"<2-3 sentence canon summary of what's now true>\",\n"
            "  \"facts\": [\"<bullet 1: a CONCRETE fact established here — NPC said X, location holds Y, item bears mark Z>\", \"<bullet 2>\", \"<bullet 3>\"]\n"
            "}"
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"canon-{uuid4()}",
            system_message=(
                "You are a concise D&D scribe. You produce locked-in canon "
                "records — never speculate, never invent, never reuse cliches. "
                "Output strict JSON only."
            ),
        )
        chat.with_model("openai", "gpt-4o-mini")
        raw = (await chat.send_message(UserMessage(text=prompt))) or ""
        s = _strip_json_fence(raw)
        try:
            data = _json.loads(s)
        except Exception:
            a, b = s.find("{"), s.rfind("}")
            data = _json.loads(s[a:b + 1]) if a != -1 and b > a else {}
        if not isinstance(data, dict):
            return fallback
        title = (data.get("title") or fallback["title"]).strip()[:80]
        summary = (data.get("summary") or fallback["summary"]).strip()[:400]
        facts_raw = data.get("facts") or []
        facts = [str(f).strip()[:240] for f in facts_raw if str(f).strip()][:5]
        return {"title": title, "summary": summary, "facts": facts}
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"canon distillation failed: {exc}")
        return fallback


async def checkpoint_passed_beat(
    db, *,
    campaign_id: str,
    character_id: Optional[str],
    storyline_id: Optional[str],
    storyline_title: Optional[str],
    beat: Dict,
    beat_index: Optional[int],
    outcome_text: str,
    roll_total: Optional[int],
    narration_snippet: str,
    creative_quality: Optional[str] = None,
) -> Optional[Dict]:
    """Create a new canon scene record from a passed beat. Marks any
    previous current scene as no-longer-current. Returns the stored doc,
    or None on persistence failure.
    """
    coll = db["canon_scenes"]
    # Atomically unmark previous current scenes
    try:
        await coll.update_many(
            {"campaign_id": campaign_id, "is_current": True},
            {"$set": {"is_current": False}},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"unmark previous current failed: {exc}")

    # Determine next scene_number
    try:
        latest = await coll.find_one(
            {"campaign_id": campaign_id}, {"_id": 0, "scene_number": 1},
            sort=[("scene_number", -1)],
        )
        next_num = int((latest or {}).get("scene_number", 0)) + 1
    except Exception:
        next_num = 1

    check_type = beat.get("check_type")
    dc = beat.get("dc")
    pitch_text = beat.get("pitch_text")

    distilled = await _distill_canon(
        storyline_title=storyline_title or "",
        beat_title=beat.get("title", ""),
        beat_description=beat.get("description", ""),
        outcome_text=outcome_text or "",
        narration_snippet=narration_snippet or "",
        check_type=check_type,
        dc=dc,
        roll_total=roll_total,
        pitch_text=pitch_text,
    )

    doc = {
        "id": f"cs_{uuid4().hex[:10]}",
        "campaign_id": campaign_id,
        "character_id": character_id,
        "scene_number": next_num,
        "storyline_id": storyline_id,
        "storyline_title": storyline_title,
        "beat_index": beat_index,
        "beat_title": beat.get("title"),
        "title": distilled["title"],
        "summary": distilled["summary"],
        "facts": distilled["facts"],
        "check_passed": (
            {
                "check_type": check_type,
                "dc": dc,
                "roll_total": roll_total,
                "quality": creative_quality,
            }
            if check_type or creative_quality
            else None
        ),
        "narration_snippet": (narration_snippet or "")[:800],
        "pitch_text": (pitch_text or "")[:400] if pitch_text else None,
        "is_current": True,
        "created_at": _now(),
    }
    try:
        await coll.insert_one(dict(doc))
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"canon checkpoint insert failed: {exc}")
        return None
    return doc


async def load_recent_canon(
    db, *, campaign_id: str, limit: int = 5
) -> List[Dict]:
    """Most recent N canon scenes, newest first."""
    coll = db["canon_scenes"]
    cursor = coll.find(
        {"campaign_id": campaign_id}, {"_id": 0}
    ).sort("scene_number", -1).limit(limit)
    return await cursor.to_list(length=limit)


def render_canon_for_prompt(scenes: List[Dict]) -> str:
    """Render the CANON block injected into the lean_dm system prompt.
    The first scene in the list is the CURRENT (most recent) — fully
    expanded with facts. Older scenes get one-liner summaries.
    """
    if not scenes:
        return (
            "=== CANON SCENES (locked-in truth — never contradict) ===\n"
            "(no canon scenes yet — the player has not passed any checks)"
        )
    lines: List[str] = [
        "=== CANON SCENES (locked-in truth — established by the player's "
        "successful actions. NEVER contradict, NEVER retcon. Build forward "
        "FROM these facts.) ==="
    ]
    # The first scene is the current anchor — render in full.
    cur = scenes[0]
    lines.append(
        f"\n[★ CURRENT SCENE — Scene {cur.get('scene_number','?')}: {cur.get('title','')}]"
    )
    lines.append(f"  Summary: {cur.get('summary','')}")
    facts = cur.get("facts") or []
    if facts:
        lines.append("  Established facts:")
        for f in facts[:5]:
            lines.append(f"    • {f}")
    cp = cur.get("check_passed") or {}
    if cp.get("check_type"):
        roll = cp.get("roll_total")
        roll_chip = f" (roll {roll})" if roll is not None else ""
        lines.append(
            f"  Locked-in via: {cp['check_type']} DC {cp.get('dc','?')}{roll_chip}"
        )
    if len(scenes) > 1:
        lines.append("\n[Prior canon — also true, do not contradict]")
        for s in scenes[1:6]:
            num = s.get("scene_number", "?")
            title = s.get("title", "")
            summary = (s.get("summary") or "").split(". ")[0]
            lines.append(f"  Scene {num} — {title}: {summary}.")
    lines.append("")
    lines.append(
        "When the player makes a new move, narrate it as continuous from the "
        "★ CURRENT SCENE. Any NPC who appeared there is still there (unless "
        "they explicitly left). Any item the player picked up is still on "
        "them. Any fact established is unchallenged. The current scene IS "
        "the anchor — every narration thread back to it."
    )
    return "\n".join(lines)


async def find_rewind_target(
    db, *, campaign_id: str, before_beat_index: Optional[int] = None,
    storyline_id: Optional[str] = None,
) -> Optional[Dict]:
    """Find the most recent canon scene that PRECEDES the contested beat
    so the DM Feedback flow can tag a retro check with "rewind to scene X".
    If before_beat_index is None, returns the current scene.
    """
    coll = db["canon_scenes"]
    query: Dict = {"campaign_id": campaign_id}
    if storyline_id and before_beat_index is not None:
        # Prefer scenes inside the same storyline up to (but not including)
        # the contested beat. Fall back to any earlier canon if none match.
        same_storyline = await coll.find(
            {
                "campaign_id": campaign_id,
                "storyline_id": storyline_id,
                "beat_index": {"$lt": before_beat_index},
            },
            {"_id": 0},
        ).sort("scene_number", -1).limit(1).to_list(length=1)
        if same_storyline:
            return same_storyline[0]
    cursor = coll.find(query, {"_id": 0}).sort("scene_number", -1).limit(1)
    docs = await cursor.to_list(length=1)
    return docs[0] if docs else None
