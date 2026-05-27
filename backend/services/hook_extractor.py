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
import re
from typing import Dict, List, Optional
from uuid import uuid4

from services.claude_client import call_haiku_async

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
    try:
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

        raw = await call_haiku_async(
            "You are an expert D&D scene parser. You return verbatim substrings "
            "the player could investigate. Output strict JSON only.",
            prompt,
            max_tokens=300,
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


def _hooks_overlap(a: Dict, b: Dict) -> bool:
    """Two hooks overlap if their character spans intersect or one contains
    the other's topic words. Used to dedupe regex+LLM merges."""
    try:
        a_s, a_e = int(a.get("start", -1)), int(a.get("end", -1))
        b_s, b_e = int(b.get("start", -1)), int(b.get("end", -1))
    except Exception:
        return False
    if a_s < 0 or b_s < 0:
        return False
    # Span intersection
    if not (a_e <= b_s or b_e <= a_s):
        return True
    # Topic-word containment
    a_top = (a.get("topic") or "").lower().strip()
    b_top = (b.get("topic") or "").lower().strip()
    if a_top and b_top and (a_top in b_top or b_top in a_top):
        return True
    return False


async def extract_hooks(narration: str, max_hooks: int = 3) -> List[Dict]:
    """Combined extractor — runs BOTH the regex enumeration pass and the LLM
    semantic pass, then merges (regex first, LLM appended for non-overlapping
    spans). This catches both the canonical 'three things draw the eye' list
    AND salient narrative objects mentioned earlier in the paragraph (e.g. a
    posted notice, an open ledger, a sign on a wall) that the player is
    likely to engage with even though the DM didn't enumerate them.
    Capped at `max_hooks * 2` to give the engagement detector enough surface
    area without flooding the inline-render budget.
    """
    if not narration:
        return []
    regex_hooks = extract_hooks_regex(narration, max_hooks=max_hooks)
    # Always run the LLM pass too (cheap gpt-4o-mini call). Ask for up to
    # max_hooks more so we don't double-count the enumeration when both fire.
    try:
        llm_hooks = await extract_hooks_llm(narration, max_hooks=max_hooks)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"LLM hook merge failed: {exc}")
        llm_hooks = []
    # Merge: keep regex hooks, then append LLM hooks that don't overlap.
    merged: List[Dict] = list(regex_hooks)
    for h in llm_hooks:
        if not any(_hooks_overlap(h, m) for m in merged):
            merged.append(h)
    # Sort by start position so inline render order matches the prose flow.
    merged.sort(key=lambda h: int(h.get("start", 0)))
    return merged[: max(max_hooks * 2, max_hooks)]


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

    # Short-circuit: idle/passive actions can never engage a hook. This stops
    # the LLM from over-matching on phrases like "I rest in the room and wait
    # quietly" by latching onto the noun "room" or "wait".
    text_low = text.lower()
    _IDLE_PATTERNS = (
        r"\b(rest|sleep|wait|stand\s+still|do\s+nothing|stay\s+put|hold\s+position|"
        r"breathe|relax|sit\s+down|stay\s+silent|listen\s+for\s+a\s+moment)\b"
    )
    if re.search(_IDLE_PATTERNS, text_low) and len(text_low.split()) <= 12:
        return None

    _ACTION_VERBS = (
        r"\b(examine|inspect|search|look|study|approach|follow|trail|chase|track|"
        r"watch|spy|observe|listen|eavesdrop|investigate|check|read|open|pick|"
        r"climb|enter|talk|ask|question|interrogate|confront|grab|take|pull|push|"
        r"break|force|sneak|tail|peek|peer|kneel|crouch|reach|touch|move\s+toward|"
        r"go\s+to|head\s+(?:to|toward))\b"
    )
    has_action_verb = bool(re.search(_ACTION_VERBS, text_low))

    # Scene-investigation verbs: a GENERIC sweep of the place ("I investigate
    # the warehouse", "I search the room", "I look around"). We treat these
    # as engaging the MOST THEMATIC hook from the active set so the player
    # never gets stuck just because they didn't name a specific noun.
    _SCENE_VERBS = (
        r"\b(investigate|search|explore|look\s+around|check\s+(?:out|around)|"
        r"examine\s+(?:the\s+)?(?:area|room|place|warehouse|building|hall|street|alley|chamber)|"
        r"scout|case|sweep|survey|study\s+(?:the\s+)?(?:area|room|place))\b"
    )
    is_scene_action = bool(re.search(_SCENE_VERBS, text_low))

    # Cheap pass — substring overlap on topic words
    candidates: List[Dict] = []
    for h in active_hooks:
        topic_words = re.findall(r"[a-z]{3,}", (h.get("topic") or "").lower())
        if not topic_words:
            continue
        hits = sum(1 for w in topic_words if w in text_low)
        if hits >= max(1, min(2, len(topic_words) // 2)):
            candidates.append(h)

    # Generic scene action with no topic match → fall back to the FIRST hook.
    # This covers "I investigate the warehouse" against {latch, crate, scuff marks}
    # — any of those is a sensible answer; we pick the one the DM listed first.
    if not candidates and is_scene_action and active_hooks:
        return active_hooks[0]

    # If we have candidates but the action has no real verb cue, defer to the LLM
    # only when there's a single topic match — otherwise reject as ambiguous.
    if candidates and not has_action_verb and len(candidates) > 1:
        return None
    # If exactly one candidate AND a clear action verb, take it without an LLM call.
    if len(candidates) == 1 and has_action_verb:
        return candidates[0]

    try:
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
            "or interacting with that specific hook.\n\n"
            "BE GENEROUS — if the player is taking a clear investigatory or observational "
            "action toward the SCENE that contains the hooks (e.g. 'I investigate the warehouse' "
            "while the hooks are 'a metal latch in a rotting door', 'a broken crate', "
            "'scuff marks'), return the FIRST hook listed (it's the one the DM most wants the "
            "player to find first). Only return null when the action is purely idle "
            "(rest, wait, do nothing) or unrelated to the scene.\n\n"
            f"=== PLAYER ACTION ===\n{text}\n\n"
            f"=== HOOKS ===\n{labelled}\n\n"
            "=== OUTPUT (strict JSON) ===\n"
            "{\"engaged_id\": \"<hook id from list, or null>\"}"
        )
        raw = await call_haiku_async(
            "You are a precise classifier. Output strict JSON only.",
            prompt,
            max_tokens=150,
            temperature=0,
        ) or ""
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
