"""DM Lessons — persistent memory of player feedback and preferences.

This service captures, distills, and surfaces "lessons" the DM has learned
from a given player so future narration improves over time. Lessons are
distilled via LLM from:

  - DM feedback judgments  (rule_correction, dc_calibration)
  - Player likes / dislikes on beats (style_preference, taboo)
  - Manual entries from the DM Notebook UI

Each lesson is a compact imperative the DM can apply ("When player tries
to hide / sneak, require a Stealth check vs passive Perception"). Active
lessons are injected into the lean_dm system prompt under a DM NOTEBOOK
section so the model actually conditions on them.

Schema (collection: `dm_lessons`):
  {
    id: str,
    campaign_id: str,
    character_id: str | None,    # None = campaign-wide lesson
    type: "rule_correction" | "dc_calibration" | "style_preference" | "taboo",
    text: str,                   # short imperative for the DM
    trigger_keywords: List[str], # words/phrases that should fire this lesson
    weight: int,                 # 1..5, used for prompt ordering
    enabled: bool,
    source: str,                 # "dm_feedback" | "like" | "dislike" | "manual"
    source_ref: dict | None,     # {feedback_id, beat_title, ...} for traceability
    apply_count: int,
    created_at: datetime,
    last_applied_at: datetime | None,
  }
"""
from __future__ import annotations

import json as _json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


_LESSON_TYPES = {"rule_correction", "dc_calibration", "style_preference", "taboo"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_kw(text: str) -> List[str]:
    """Extract lowercase 1-2 word keywords from arbitrary text for matching."""
    if not text:
        return []
    words = re.findall(r"[a-zA-Z']{3,}", text.lower())
    stop = {"the", "and", "for", "that", "with", "this", "from", "your", "you",
            "are", "was", "were", "they", "their", "have", "has", "but", "not",
            "into", "onto", "than", "then", "what", "when", "where", "why",
            "how", "out", "off", "in", "on", "at", "to", "of", "is"}
    return [w for w in words if w not in stop][:8]


def _strip_json_fence(s: str) -> str:
    s = (s or "").strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:].lstrip()
    return s


async def _llm_distill(prompt: str, system: str) -> Optional[Dict]:
    """Generic single-call distiller. Returns parsed JSON or None."""
    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=api_key,
            session_id=f"lesson-distill-{uuid4()}",
            system_message=system,
        )
        chat.with_model("openai", "gpt-4o-mini")
        raw = (await chat.send_message(UserMessage(text=prompt))) or ""
        s = _strip_json_fence(raw)
        try:
            return _json.loads(s)
        except Exception:
            a, b = s.find("{"), s.rfind("}")
            if a != -1 and b > a:
                return _json.loads(s[a:b + 1])
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"lesson distill failed: {exc}")
        return None


async def distill_lesson_from_feedback(
    feedback: Dict, judgment: Dict
) -> Optional[Dict]:
    """Turn a DM feedback record + judgment into 1 lesson, or None if the
    judge disagreed and there's nothing actionable to learn.
    Returns a partial lesson dict (without id / campaign_id / character_id).
    """
    if not judgment or not judgment.get("agrees_with_player"):
        # Judge disagreed — store as a *taboo* only if the player explicitly
        # complained, so the DM remembers the player WANTS this kind of check
        # in similar future situations (soft signal).
        if (feedback.get("kind") or "") not in {"missed_check", "wrong_check"}:
            return None

    action = (feedback.get("player_action") or "")[:240]
    check_type = judgment.get("check_type") or feedback.get("suggested_check")
    dc = judgment.get("dc") or feedback.get("suggested_dc")
    reasoning = (judgment.get("dc_reasoning") or judgment.get("explanation") or "")[:240]
    if not action and not check_type:
        return None

    # Type classification:
    kind = feedback.get("kind") or "general"
    if kind == "wrong_check":
        lesson_type = "dc_calibration"
    elif kind in {"missed_check", "why_no_check"}:
        lesson_type = "rule_correction"
    else:
        lesson_type = "rule_correction"

    # Compose a one-line directive.
    if check_type and dc:
        text = (
            f"When the player tries to '{action}' or similar, require a "
            f"{check_type} check (DC {int(dc)}). {reasoning}".strip()
        )
    elif check_type:
        text = (
            f"When the player tries to '{action}' or similar, require a "
            f"{check_type} check. {reasoning}".strip()
        )
    else:
        text = f"Player flagged: '{action}'. Reasoning: {reasoning}"

    trigger_keywords = _normalize_kw(action)
    weight = 4 if judgment.get("agrees_with_player") else 2

    return {
        "type": lesson_type,
        "text": text[:400],
        "trigger_keywords": trigger_keywords,
        "weight": weight,
        "enabled": True,
        "source": "dm_feedback",
    }


async def distill_lesson_from_reaction(
    *, reaction: str, narration: str, beat_title: Optional[str] = None,
    note: Optional[str] = None,
) -> Optional[Dict]:
    """Turn a 👍 (like) or 👎 (dislike) on a DM narration beat into a
    style_preference or taboo lesson. Uses an LLM to extract WHAT made the
    moment good/bad (pacing, dialogue, sensory specificity, NPC voice,
    rules adjudication, etc.) so the lesson is reusable across scenes.
    """
    if reaction not in {"like", "dislike"}:
        return None
    snippet = (narration or "")[:1200].strip()
    if not snippet:
        return None
    extra = (note or "").strip()
    sys = (
        "You are a senior D&D Dungeon Master analyzing what worked (or didn't) "
        "in a fellow DM's narration moment. Your job: produce ONE short, "
        "reusable lesson the DM should APPLY (or AVOID) in future scenes. "
        "Focus on craft — pacing, sensory choices, NPC voice, restraint, "
        "openness of choice — not the specifics of this scene. Output strict JSON only."
    )
    direction = "DID WELL" if reaction == "like" else "WENT WRONG"
    target_type = "style_preference" if reaction == "like" else "taboo"
    user_extra = f"\nPlayer note: \"{extra}\"" if extra else ""
    prompt = (
        f"=== DM NARRATION BEAT ({direction} — player tapped {'👍' if reaction == 'like' else '👎'}) ===\n"
        f"Beat title: {beat_title or '(untitled)'}\n"
        f"Narration:\n\"\"\"\n{snippet}\n\"\"\"{user_extra}\n\n"
        "=== TASK ===\n"
        f"Identify ONE specific craft element that {direction} in the snippet. "
        f"Phrase the lesson as a concise imperative the DM should "
        f"{'KEEP DOING' if reaction == 'like' else 'AVOID'} going forward. "
        "Examples of good lessons:\n"
        '  - "Lead with a single sharp sensory detail (smell, sound, posture) before any plot fact."\n'
        '  - "Avoid stacking similes — one comparison per paragraph max."\n'
        '  - "End scenes by handing the player 2-3 concrete observable facts, never prescribing the next verb."\n'
        '  - "When voicing the Innkeeper, use clipped working-class cadence."\n\n'
        "=== OUTPUT (strict JSON, no code fence) ===\n"
        "{\n"
        f"  \"type\": \"{target_type}\",\n"
        "  \"text\": \"<one imperative, <= 180 chars, lead with a strong verb>\",\n"
        "  \"trigger_keywords\": [\"2-5 short words/phrases that should fire this lesson, e.g. 'sensory', 'simile', 'NPC voice'\"]\n"
        "}"
    )
    data = await _llm_distill(prompt, sys)
    if not data or not isinstance(data, dict):
        return None
    text = (data.get("text") or "").strip()
    if not text:
        return None
    triggers = data.get("trigger_keywords") or []
    if not isinstance(triggers, list):
        triggers = []
    triggers = [str(t).strip().lower()[:40] for t in triggers if str(t).strip()][:6]
    weight = 4 if reaction == "like" else 5  # dislikes weigh slightly higher
    return {
        "type": target_type,
        "text": text[:400],
        "trigger_keywords": triggers,
        "weight": weight,
        "enabled": True,
        "source": reaction,
    }


def _similarity(a: Dict, b: Dict) -> float:
    """0..1 — Jaccard over keyword sets, plus a small bonus when type matches."""
    if a.get("type") != b.get("type"):
        return 0.0
    ka = set(a.get("trigger_keywords") or [])
    kb = set(b.get("trigger_keywords") or [])
    if not ka or not kb:
        return 0.0
    inter = len(ka & kb)
    union = len(ka | kb)
    if union == 0:
        return 0.0
    return inter / union


async def merge_or_create_lesson(
    db, *, campaign_id: str, character_id: Optional[str], lesson: Dict,
    source_ref: Optional[Dict] = None,
) -> Dict:
    """Look for an existing similar lesson (same type, Jaccard >= 0.4 on
    keywords) and bump its weight + refresh its text instead of creating a
    duplicate. Otherwise insert a fresh lesson. Returns the stored doc.
    """
    coll = db["dm_lessons"]
    cursor = coll.find(
        {
            "campaign_id": campaign_id,
            "character_id": character_id,
            "type": lesson["type"],
            "enabled": True,
        },
        {"_id": 0},
    )
    existing = await cursor.to_list(length=50)
    best = None
    best_score = 0.0
    for e in existing:
        s = _similarity(lesson, e)
        if s > best_score:
            best = e
            best_score = s
    now = _now()
    if best and best_score >= 0.4:
        # Merge — bump weight, append new keywords, refresh text if newer one is longer/clearer
        merged_keywords = sorted({*best.get("trigger_keywords", []), *lesson.get("trigger_keywords", [])})[:10]
        new_weight = min(5, int(best.get("weight", 1)) + 1)
        # Keep the older text unless the new one is meaningfully different and shorter
        new_text = best["text"]
        if len(lesson["text"]) < 250 and lesson["text"] != best["text"]:
            new_text = lesson["text"]
        await coll.update_one(
            {"id": best["id"]},
            {
                "$set": {
                    "text": new_text,
                    "trigger_keywords": merged_keywords,
                    "weight": new_weight,
                    "updated_at": now,
                },
                "$inc": {"apply_count": 1},
            },
        )
        best.update({
            "text": new_text,
            "trigger_keywords": merged_keywords,
            "weight": new_weight,
            "updated_at": now,
            "apply_count": int(best.get("apply_count", 0)) + 1,
        })
        return best

    # Create new
    doc = {
        "id": f"lsn_{uuid4().hex[:10]}",
        "campaign_id": campaign_id,
        "character_id": character_id,
        "type": lesson["type"],
        "text": lesson["text"],
        "trigger_keywords": lesson.get("trigger_keywords") or [],
        "weight": int(lesson.get("weight", 3)),
        "enabled": bool(lesson.get("enabled", True)),
        "source": lesson.get("source", "manual"),
        "source_ref": source_ref or {},
        "apply_count": 0,
        "created_at": now,
        "last_applied_at": None,
    }
    await coll.insert_one(dict(doc))
    return doc


async def load_active_lessons(
    db, *, campaign_id: str, character_id: Optional[str] = None, limit: int = 12,
) -> List[Dict]:
    """Top N enabled lessons by weight, then recency. Includes both
    campaign-scoped and character-scoped lessons when character_id is given.
    """
    coll = db["dm_lessons"]
    query: Dict = {"campaign_id": campaign_id, "enabled": True}
    if character_id:
        query["$or"] = [
            {"character_id": character_id},
            {"character_id": None},
        ]
    else:
        query["character_id"] = None
    cursor = coll.find(query, {"_id": 0}).sort([("weight", -1), ("created_at", -1)]).limit(limit)
    return await cursor.to_list(length=limit)


def render_lessons_for_prompt(lessons: List[Dict]) -> str:
    """Render the DM Notebook block injected into the lean_dm system prompt."""
    if not lessons:
        return (
            "=== DM NOTEBOOK (lessons learned from this player) ===\n"
            "(no lessons on record yet — DM has not been corrected or coached)"
        )
    # Group by type for readability
    by_type: Dict[str, List[Dict]] = {}
    for lsn in lessons:
        by_type.setdefault(lsn.get("type", "rule_correction"), []).append(lsn)
    order = ["rule_correction", "dc_calibration", "taboo", "style_preference"]
    headings = {
        "rule_correction": "RULES TO APPLY",
        "dc_calibration": "DC CALIBRATIONS",
        "taboo": "AVOID — player has flagged these",
        "style_preference": "STYLE — player has praised these",
    }
    lines: List[str] = [
        "=== DM NOTEBOOK (lessons learned from THIS player — apply every turn) ==="
    ]
    for t in order:
        items = by_type.get(t) or []
        if not items:
            continue
        lines.append(f"\n[{headings.get(t, t.upper())}]")
        for lsn in items[:6]:
            star = "★" * min(5, max(1, int(lsn.get("weight", 3))))
            lines.append(f"  {star} {lsn['text']}")
    lines.append("")
    lines.append(
        "Apply these like a second-DM in your ear — if a current player action "
        "matches a RULES or DC entry, follow it (require the check, narrate the "
        "beat without auto-resolving). Avoid TABOO patterns. Favor STYLE patterns "
        "the player has praised. Never quote these lessons aloud — apply them silently."
    )
    return "\n".join(lines)


async def bump_apply_counts(db, *, campaign_id: str, lesson_ids: List[str]) -> None:
    """Bump apply_count + last_applied_at for the lessons we actually fed to
    the DM this turn. Fire-and-forget — failures are non-fatal."""
    if not lesson_ids:
        return
    try:
        await db["dm_lessons"].update_many(
            {"campaign_id": campaign_id, "id": {"$in": lesson_ids}},
            {"$set": {"last_applied_at": _now()}, "$inc": {"apply_count": 1}},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"bump_apply_counts failed: {exc}")
