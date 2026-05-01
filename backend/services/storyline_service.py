"""Storyline service — drafts a 3-5 beat investigation chain from a hook,
advances beats, computes the final reward.

Model:

  Storyline = {
    id, campaign_id, character_id,
    title,                    # short investigation title
    hook_text,                # the literal hook phrase
    hook_id,                  # ref into the originating message's hooks
    status,                   # 'active' | 'completed' | 'abandoned'
    current_beat,             # int index into beats[]
    beats: [Beat],
    total_dc,                 # sum of beat.dc — drives reward magnitude
    reward,                   # populated on completion
    quest_card_id,            # link to the KnowledgeCard the first beat seeded
    created_at, updated_at
  }

  Beat = {
    title,                    # 3-6 word beat name
    description,              # 1-2 sentences of DM narration the beat opens with
    task,                     # what the player must DO
    dc,                       # 10..18
    check_type,               # 'Investigation' | 'Perception' | 'Insight' | 'Persuasion' | 'Stealth' | 'Athletics'
    ability,                  # 'INT' | 'WIS' | 'CHA' | 'DEX' | 'STR' | 'CON'
    status,                   # 'pending' | 'active' | 'passed' | 'failed' | 'skipped'
    outcome_text              # populated when resolved
  }

The hook becomes the FIRST beat's task by definition (the player engaged with
the hook, so beat 1 is the literal first investigation step). Beats 2..N
deepen the storyline with linked twists (e.g. "the sick sister", "the unpaid
debt", "the deception"). Linear progression: cards must resolve in order.
"""
from __future__ import annotations

import json as _json
import logging
import os
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


_VALID_CHECK_TYPES = {
    "Investigation": "INT",
    "Perception":    "WIS",
    "Insight":       "WIS",
    "Persuasion":    "CHA",
    "Deception":     "CHA",
    "Intimidation":  "CHA",
    "Stealth":       "DEX",
    "Sleight of Hand": "DEX",
    "Athletics":     "STR",
    "Arcana":        "INT",
    "History":       "INT",
    "Nature":        "WIS",
    "Survival":      "WIS",
}


# -------------------- deterministic fallback --------------------

_FALLBACK_BEAT_TEMPLATES = [
    {
        "title": "First Sign",
        "description": "What looked simple opens into something stranger; "
                       "small details disagree with the surface story.",
        "task_tmpl": "Look closer at {topic}",
        "check_type": "Investigation",
        "dc": 12,
    },
    {
        "title": "A Witness",
        "description": "Someone nearby saw what happened. Their willingness "
                       "to talk depends on how you approach them.",
        "task_tmpl": "Get a witness to speak about {topic}",
        "check_type": "Persuasion",
        "dc": 13,
    },
    {
        "title": "The Hidden Stake",
        "description": "Beneath the obvious motive sits a smaller, more "
                       "human one. Someone is paying for something they cannot afford.",
        "task_tmpl": "Read between the lines around {topic}",
        "check_type": "Insight",
        "dc": 14,
    },
    {
        "title": "Confrontation",
        "description": "The thread leads back to a person who would rather "
                       "the truth stay buried. The room sharpens.",
        "task_tmpl": "Confront whoever is behind {topic}",
        "check_type": "Intimidation",
        "dc": 15,
    },
]


def _template_storyline(hook: Dict, intent_focus: str = "Mystery") -> Dict:
    topic = (hook.get("topic") or hook.get("text") or "this matter").strip()
    title = f"The {topic.title()[:36]}".rstrip()
    beats: List[Dict] = []
    for i, t in enumerate(_FALLBACK_BEAT_TEMPLATES):
        ability = _VALID_CHECK_TYPES.get(t["check_type"], "INT")
        beats.append({
            "title": t["title"],
            "description": t["description"],
            "task": t["task_tmpl"].format(topic=topic),
            "dc": int(t["dc"]),
            "check_type": t["check_type"],
            "ability": ability,
            "status": "active" if i == 0 else "pending",
            "outcome_text": None,
        })
    total_dc = sum(b["dc"] for b in beats)
    return {
        "title": title,
        "beats": beats,
        "total_dc": total_dc,
    }


# -------------------- LLM-driven draft --------------------


async def draft_storyline(
    campaign: Dict,
    character: Dict,
    hook: Dict,
    narration_context: str = "",
) -> Dict:
    """Draft a 3-5 beat linear investigation chain rooted in `hook`.

    Returns a dict with `title`, `beats`, `total_dc`. Caller (router) wraps it
    with ids, status, timestamps before persisting.
    """
    fallback = _template_storyline(hook, (campaign.get("intent") or {}).get("focus", "Mystery"))

    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return fallback
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        intent = campaign.get("intent") or {}
        world = campaign.get("world") or {}
        starting = world.get("startingLocation") or {}
        identity = character.get("identity") or {}
        cls = character.get("class") or character.get("class_") or {}
        bg = character.get("background") or {}

        hero_name = identity.get("name") or "the hero"
        class_key = (cls.get("key") or "adventurer").lower()
        bg_key = (bg.get("key") or "wanderer").lower()
        location = starting.get("name") or (world.get("starting_town") or {}).get("name") or "the town"
        realm = (world.get("world_core") or {}).get("name") or "the realm"

        prompt = (
            "Draft a SHORT INVESTIGATION CHAIN (3-5 linked beats) that grows out of a "
            "single point of interest the player just engaged with. The first beat IS "
            "the literal investigation of the hook; the remaining beats deepen the story "
            "with linked twists (e.g. for 'someone stealing from someone' → 'the sick "
            "sister', 'the unpaid debt', 'the deception'). Linear progression: each "
            "beat must be resolvable before the next is opened.\n\n"
            "=== CAMPAIGN ===\n"
            f"Realm: {realm} | Location: {location}\n"
            f"Tone: {intent.get('tone','Balanced')} | Focus: {intent.get('focus','Mystery')} | "
            f"Danger: {intent.get('danger','Medium')}\n\n"
            "=== HERO ===\n"
            f"{hero_name} ({class_key}, {bg_key} background)\n\n"
            "=== HOOK (the player just engaged with this) ===\n"
            f"{hook.get('text','')}\n"
            f"(topic: {hook.get('topic','')}, suggested verb: {hook.get('verb_hint','examine')})\n\n"
            f"=== RECENT NARRATION CONTEXT ===\n{(narration_context or '')[:600]}\n\n"
            "=== REQUIREMENTS ===\n"
            "- 3-5 beats. Linear order. Each beat is a discrete TASK with a DC.\n"
            "- Beat 1 must be the literal first step of investigating the hook.\n"
            "- Each subsequent beat introduces a NEW small revelation that links back\n"
            "  (a relationship, a debt, a lie, a place, a witness) — not a copy of the previous.\n"
            "- Vary check types across beats. DC range: 10..18. At least one beat between 13-16.\n"
            "- Plausible at level 1-3.\n"
            "- NO clichés ('ancient evil', 'chosen one', 'prophecy'). Real human stakes.\n"
            "- Title for the storyline is 3-6 words.\n\n"
            "=== OUTPUT (strict JSON only, no code fence) ===\n"
            "{\n"
            "  \"title\": \"...\",\n"
            "  \"beats\": [\n"
            "    {\n"
            "      \"title\": \"...\",\n"
            "      \"description\": \"1-2 sentences opening this beat (mid-cinematic, present tense, second person; <=240 chars)\",\n"
            "      \"task\": \"what the hero must DO this beat (one short imperative)\",\n"
            "      \"dc\": 10,\n"
            "      \"check_type\": \"Investigation|Perception|Insight|Persuasion|Deception|Intimidation|Stealth|Sleight of Hand|Athletics|Arcana|History|Nature|Survival\"\n"
            "    }\n"
            "  ]\n"
            "}\n"
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"storyline-draft-{uuid4()}",
            system_message=(
                "You are a senior D&D campaign designer. You draft tight, linked "
                "investigation chains with concrete tasks and clear DCs. Output strict JSON only."
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

        title = (data.get("title") or "").strip() or fallback["title"]
        raw_beats = data.get("beats") or []
        beats: List[Dict] = []
        for i, rb in enumerate(raw_beats[:5]):
            if not isinstance(rb, dict):
                continue
            t = (rb.get("title") or "").strip()
            d = (rb.get("description") or "").strip()
            tk = (rb.get("task") or "").strip()
            ct = (rb.get("check_type") or "Investigation").strip()
            if ct not in _VALID_CHECK_TYPES:
                ct = "Investigation"
            ab = _VALID_CHECK_TYPES[ct]
            try:
                dc = int(rb.get("dc") or 12)
            except Exception:
                dc = 12
            dc = max(8, min(20, dc))
            if not (t and d and tk):
                continue
            beats.append({
                "title": t[:48],
                "description": d[:280],
                "task": tk[:160],
                "dc": dc,
                "check_type": ct,
                "ability": ab,
                "status": "active" if i == 0 else "pending",
                "outcome_text": None,
            })
        if len(beats) < 3:
            return fallback
        total_dc = sum(b["dc"] for b in beats)
        return {"title": title[:60], "beats": beats, "total_dc": total_dc}
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Storyline draft LLM failed, using template: {exc}")
        return fallback


# -------------------- reward --------------------

def _xp_for_total_dc(total_dc: int) -> int:
    """Total DC -> XP. Roughly DC*8 with a soft floor and ceiling.
    A 4-beat storyline summing to DC 56 yields ~450 XP — a solid level-1
    chunk without trivializing levels.
    """
    base = max(60, total_dc * 8)
    # Smooth-cap: round to nearest 25, max 1200
    return min(1200, int(round(base / 25)) * 25)


async def generate_storyline_reward(
    campaign: Dict,
    character: Dict,
    storyline: Dict,
) -> Dict:
    """LLM-themed completion reward. Always returns a dict with at least
    `xp` populated; `item`, `title`, and `description` come from the LLM
    when available, else from a deterministic template.
    """
    total_dc = int(storyline.get("total_dc") or 0)
    xp = _xp_for_total_dc(total_dc)
    fallback = {
        "xp": xp,
        "title": storyline.get("title") or "Investigation Resolved",
        "description": (
            f"You closed the thread you started pulling. Word of your work "
            f"will travel quietly through {((campaign.get('world') or {}).get('starting_town') or {}).get('name', 'the district')}."
        ),
        "item": None,
        "tone": "satisfaction",
    }

    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return fallback
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        beat_summary = "\n".join(
            f"- {b.get('title','')}: {b.get('outcome_text') or b.get('description','')}"
            for b in (storyline.get("beats") or [])
        )
        intent = campaign.get("intent") or {}

        prompt = (
            "The player has resolved an investigation chain. Generate a CLOSING REWARD "
            "that feels earned by the actual beats they played through.\n\n"
            f"=== STORYLINE ===\nTitle: {storyline.get('title','')}\n{beat_summary}\n\n"
            f"=== CAMPAIGN TONE ===\n{intent.get('tone','Balanced')} | {intent.get('focus','Mystery')}\n\n"
            f"=== TOTAL DIFFICULTY ===\nDC sum: {total_dc} (player will receive {xp} XP separately)\n\n"
            "=== RULES ===\n"
            "- 1 thematic ITEM (not always magical — could be a piece of information, a "
            "  letter sealed by an NPC, a small heirloom, a contact's name, a key).\n"
            "- 1 short closing line (<=160 chars) that lands the resolution as narrative — "
            "  Mercer-style, restrained, no fate talk.\n"
            "- NO XP number in the closing line; XP is shown by the UI.\n"
            "- Output strict JSON, no code fence.\n\n"
            "=== OUTPUT ===\n"
            "{\n"
            "  \"item\": {\"name\": \"...\", \"description\": \"...\", \"kind\": \"item|info|favor|key\"},\n"
            "  \"description\": \"closing line\",\n"
            "  \"tone\": \"satisfaction|grim|hopeful|bitter|reverent\"\n"
            "}\n"
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"storyline-reward-{uuid4()}",
            system_message="You are a senior D&D campaign designer. Output strict JSON only.",
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

        item = data.get("item") if isinstance(data.get("item"), dict) else None
        if item:
            item = {
                "name": str(item.get("name") or "Token of the Investigation")[:60],
                "description": str(item.get("description") or "")[:240],
                "kind": str(item.get("kind") or "item")[:16],
            }
        return {
            "xp": xp,
            "title": storyline.get("title") or fallback["title"],
            "description": str(data.get("description") or fallback["description"])[:200],
            "item": item,
            "tone": str(data.get("tone") or fallback["tone"])[:24],
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Reward LLM failed, using template: {exc}")
        return fallback


# -------------------- progression helpers --------------------


def advance_storyline(storyline: Dict, beat_index: int, outcome: str, outcome_text: Optional[str] = None) -> Dict:
    """Mutate `storyline` in place: mark beat `beat_index` with the given outcome,
    activate the next beat, or mark the storyline complete if it was the last beat.

    Returns the (mutated) storyline dict for convenience.
    """
    if outcome not in {"passed", "failed", "skipped"}:
        outcome = "passed"
    beats = storyline.get("beats") or []
    if not (0 <= beat_index < len(beats)):
        return storyline

    beat = beats[beat_index]
    beat["status"] = outcome
    if outcome_text:
        beat["outcome_text"] = outcome_text[:240]
    storyline["updated_at"] = datetime.now(timezone.utc)

    # Activate next pending beat
    next_idx = beat_index + 1
    if next_idx < len(beats):
        beats[next_idx]["status"] = "active"
        storyline["current_beat"] = next_idx
    else:
        storyline["status"] = "completed"
        storyline["current_beat"] = beat_index
    return storyline


def storyline_to_dict(storyline: Dict) -> Dict:
    """Strip _id / normalize datetimes for transport."""
    out = {k: v for k, v in storyline.items() if k != "_id"}
    for k, v in list(out.items()):
        if isinstance(v, datetime):
            out[k] = v.isoformat()
    return out
