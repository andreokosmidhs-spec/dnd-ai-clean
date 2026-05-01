"""Hook extraction — pulls "points of interest" from DM narration.

A hook is a short clause planted by the DM that hints at something the player
*could* explore, observe, or interact with. Examples from the parchment opener:
  - "a metal latch set into a rotting door"
  - "a broken crate spilling its contents onto the ground"
  - "scuff marks leading away from the scene"

The extractor returns spans (start/end indexes) so the frontend can render the
hook inline (italic dashed underline) without altering the narration text.

Two passes:
  1. Cheap regex pass — finds the canonical "Three things draw the eye: A, B, and C."
     enumeration we explicitly prompt for in opening intros. Always free.
  2. LLM pass — for non-enumeration narrations, asks gpt-4o-mini to return up to
     three observable hooks with their literal text spans. Falls back to []
     silently on any error / missing API key.

Each hook carries:
  - id           : stable hook id (so engagement detection can reference it)
  - text         : the literal substring as it appears in the narration
  - start, end   : zero-indexed character span (inclusive start, exclusive end)
  - topic        : a short noun-phrase summary ("broken crate", "scuff marks")
  - verb_hint    : primary action verb suggested ("examine" / "follow" / "watch" / "search")
"""
from __future__ import annotations

import json as _json
import logging
import os
import re
from typing import Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


_HOOK_INTRO_RE = re.compile(
    r"\b(three\s+things?\s+(?:draw|catch|hold)\s+(?:the\s+|your\s+)?eye[s]?|"
    r"three\s+details?\s+stand\s+out|"
    r"three\s+things?\s+stand\s+out)[\s,:.\-—–]*",
    re.IGNORECASE,
)


def _split_clauses(enum_text: str) -> List[str]:
    """Split 'A, B, and C' / 'A, B and C' / 'A; B; C' into clauses.
    Drops empty / very short fragments.
    """
    # Normalize ' and ' / ' & ' before final clause -> comma
    norm = re.sub(r",?\s+(?:and|&)\s+", ", ", enum_text)
    parts = [p.strip(" ,.;:—–-") for p in re.split(r"[;,]", norm)]
    return [p for p in parts if p and len(p) >= 4]


def _make_hook(narration: str, clause: str, search_from: int = 0) -> Optional[Dict]:
    """Locate `clause` inside `narration` (case-insensitive) and return a hook dict
    with literal text + char span. Falls back to a fuzzier 4-word lead-match
    if exact match fails."""
    if not clause:
        return None
    idx = narration.lower().find(clause.lower(), search_from)
    if idx == -1:
        # Fuzzy: try first 4 words
        words = clause.split()
        if len(words) >= 4:
            lead = " ".join(words[:4]).lower()
            idx = narration.lower().find(lead, search_from)
            if idx != -1:
                # Try to consume to a natural punctuation boundary
                tail = narration[idx:idx + 240]
                m = re.search(r"[.,;]", tail)
                end = idx + (m.start() if m else min(len(tail), len(clause) + 30))
                literal = narration[idx:end]
            else:
                return None
        else:
            return None
    else:
        literal = narration[idx:idx + len(clause)]
    return {
        "id": f"hook_{uuid4().hex[:8]}",
        "text": literal.strip(" ,.;:—–-"),
        "start": idx,
        "end": idx + len(literal.rstrip(" ,.;:—–-")),
        "topic": (literal[:48].strip()),
        "verb_hint": _guess_verb(literal),
    }


def _guess_verb(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ("door", "gate", "hatch", "latch", "lock", "chest", "crate")):
        return "examine"
    if any(w in t for w in ("scuff", "track", "footprint", "trail", "path")):
        return "follow"
    if any(w in t for w in ("figure", "stranger", "thief", "watcher", "shadow")):
        return "watch"
    if any(w in t for w in ("voice", "argument", "whisper", "song", "chant")):
        return "listen"
    if any(w in t for w in ("smell", "scent", "odor")):
        return "investigate"
    return "examine"


def extract_hooks_regex(narration: str, max_hooks: int = 3) -> List[Dict]:
    """Cheap pass — catches the canonical "Three things draw the eye: A, B, and C."
    pattern produced by the opening-scene Mercer prompt. Returns [] if the
    pattern isn't present.
    """
    if not narration:
        return []
    m = _HOOK_INTRO_RE.search(narration)
    if not m:
        return []
    after = narration[m.end():].strip()
    # Take up to the next sentence-ending period
    sent_end = re.search(r"\.(?:\s|$)", after)
    enum = after[: sent_end.start()] if sent_end else after
    clauses = _split_clauses(enum)[:max_hooks]
    hooks: List[Dict] = []
    cursor = m.end()
    for c in clauses:
        h = _make_hook(narration, c, search_from=cursor)
        if h:
            hooks.append(h)
            cursor = h["end"]
    return hooks


async def extract_hooks_llm(narration: str, max_hooks: int = 3) -> List[Dict]:
    """LLM pass — asks gpt-4o-mini for up to `max_hooks` literal observable
    phrases the player could investigate / follow / watch. Returns [] on
    any failure (no key, parse error, etc.).
    """
    if not narration or not narration.strip():
        return []
    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return []
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        prompt = (
            "Extract up to "
            f"{max_hooks} POINTS OF INTEREST from the D&D scene below — short literal "
            "phrases the player could investigate, follow, observe, or interact with. "
            "Each phrase MUST be a verbatim substring of the scene text (no paraphrase, "
            "no quotation marks, no edits). Prefer concrete observable nouns over abstract "
            "feelings. Skip already-named people you've met by full name (those are NPC entities).\n\n"
            "=== SCENE ===\n"
            f"{narration}\n\n"
            "=== OUTPUT (strict JSON, no code fence) ===\n"
            "{\"hooks\": [\n"
            "  {\"text\": \"<literal substring>\", \"topic\": \"<2-4 word noun summary>\", "
            "\"verb_hint\": \"<one of: examine|follow|watch|listen|investigate|approach|search>\"}\n"
            "]}\n"
            "If the scene has no clear hooks (pure dialogue, transition), return {\"hooks\": []}."
        )

        chat = LlmChat(
            api_key=api_key,
            session_id=f"hook-extract-{uuid4()}",
            system_message=(
                "You are an expert D&D scene parser. You return verbatim substrings "
                "the player could investigate. Output strict JSON only."
            ),
        )
        chat.with_model("openai", "gpt-4o-mini")
        raw = (await chat.send_message(UserMessage(text=prompt))) or ""
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        try:
            data = _json.loads(text)
        except Exception:
            s, e = text.find("{"), text.rfind("}")
            data = _json.loads(text[s:e + 1]) if s != -1 and e > s else {}

        hooks: List[Dict] = []
        cursor = 0
        for h in (data.get("hooks") or [])[:max_hooks]:
            if not isinstance(h, dict):
                continue
            clause = (h.get("text") or "").strip().strip('"')
            if not clause:
                continue
            built = _make_hook(narration, clause, search_from=cursor)
            if built:
                topic = (h.get("topic") or "").strip()
                if topic:
                    built["topic"] = topic[:48]
                vb = (h.get("verb_hint") or "").strip().lower()
                if vb in {"examine", "follow", "watch", "listen", "investigate", "approach", "search"}:
                    built["verb_hint"] = vb
                hooks.append(built)
                cursor = built["end"]
        return hooks
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"LLM hook extraction failed: {exc}")
        return []


async def extract_hooks(narration: str, max_hooks: int = 3) -> List[Dict]:
    """Combined extractor — regex fast-path first, LLM fallback if it returned nothing."""
    if not narration:
        return []
    hooks = extract_hooks_regex(narration, max_hooks=max_hooks)
    if hooks:
        return hooks
    return await extract_hooks_llm(narration, max_hooks=max_hooks)


# -------------------- engagement detection --------------------


async def detect_engaged_hook(
    player_action: str,
    active_hooks: List[Dict],
) -> Optional[Dict]:
    """Given a player action and a list of recently-presented hooks (from the
    last 1-2 DM turns), return the hook the player is engaging with — or None.

    The check is intent-based:
      - "I keep watching the thief" engages a "hooded figure at the well" hook
      - "Examine the broken crate" engages a "broken crate" hook
      - "I look around" does NOT engage any specific hook (too generic)

    Uses gpt-4o-mini for nuance; cheap fallback on any failure.
    """
    text = (player_action or "").strip()
    if not text or not active_hooks:
        return None

    # Cheap pass — substring overlap on topic words
    text_low = text.lower()
    candidates: List[Dict] = []
    for h in active_hooks:
        topic_words = re.findall(r"[a-z]{3,}", (h.get("topic") or "").lower())
        if not topic_words:
            continue
        hits = sum(1 for w in topic_words if w in text_low)
        if hits >= max(1, min(2, len(topic_words) // 2)):
            candidates.append(h)
    # If exactly one candidate, take it without an LLM call.
    if len(candidates) == 1:
        return candidates[0]

    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return candidates[0] if candidates else None
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        # If we have substring candidates, only ask the LLM to disambiguate
        # among those; otherwise ask against the full set.
        pool = candidates if candidates else active_hooks
        labelled = "\n".join(
            f"{i+1}. id={h['id']} | {h.get('topic','')} — \"{h.get('text','')}\""
            for i, h in enumerate(pool)
        )
        prompt = (
            "A D&D player just took an action. Decide whether the action engages one of "
            "the listed POINTS OF INTEREST from the recent narration. Engagement means the "
            "player is actively investigating, following, watching, listening, approaching, "
            "or interacting with that specific hook. Generic exploration ('I look around') "
            "does NOT count.\n\n"
            f"=== PLAYER ACTION ===\n{text}\n\n"
            f"=== HOOKS ===\n{labelled}\n\n"
            "=== OUTPUT (strict JSON) ===\n"
            "{\"engaged_id\": \"<hook id from list, or null>\"}"
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"hook-engage-{uuid4()}",
            system_message="You are a precise classifier. Output strict JSON only.",
        )
        chat.with_model("openai", "gpt-4o-mini")
        raw = (await chat.send_message(UserMessage(text=prompt))) or ""
        text_out = raw.strip()
        if text_out.startswith("```"):
            text_out = text_out.strip("`")
            if text_out.lower().startswith("json"):
                text_out = text_out[4:].lstrip()
        try:
            data = _json.loads(text_out)
        except Exception:
            s, e = text_out.find("{"), text_out.rfind("}")
            data = _json.loads(text_out[s:e + 1]) if s != -1 and e > s else {}
        engaged_id = (data.get("engaged_id") or "").strip()
        if not engaged_id or engaged_id.lower() == "null":
            return None
        for h in pool:
            if h.get("id") == engaged_id:
                return h
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"engagement detection failed: {exc}")
        return candidates[0] if candidates else None
