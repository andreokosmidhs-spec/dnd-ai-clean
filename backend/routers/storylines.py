"""Storyline endpoints — orchestrate hook → multi-beat investigation → reward.

Endpoints:

  POST /api/campaigns/{campaign_id}/storylines/draft
    body: {
      character_id: str,
      hook_id: str | null,
      hook_text: str,
      hook_topic: str | null,
      hook_verb: str | null,
      narration_context: str | null,
    }
    -> { storyline, quest }   # creates a quest knowledge card linked to the storyline

  GET /api/campaigns/{campaign_id}/storylines
    -> { storylines: [...] }   # active + completed for this campaign

  GET /api/campaigns/{campaign_id}/storylines/{storyline_id}
    -> storyline

  POST /api/campaigns/{campaign_id}/storylines/{storyline_id}/resolve
    body: {
      outcome: "passed" | "failed" | "skipped",
      outcome_text: str | null,
      roll_total: int | null,
    }
    -> { storyline, completed: bool, reward: {...} | null }
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from bson import ObjectId
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from models.campaign_models import KnowledgeCard
from services.storyline_service import (
    advance_storyline,
    draft_initial_scene,
    draft_storyline,
    generate_complication_beat,
    generate_next_scene,
    generate_storyline_reward,
    judge_creative_approach,
    storyline_to_dict,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaigns", tags=["storylines"])

_db = None


def set_database(db):
    global _db
    _db = db


def _get_db():
    if _db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return _db


def _storylines_collection():
    return _get_db()["campaign_storylines"]


def _cards_collection():
    return _get_db()["campaign_cards"]


async def _load_campaign(campaign_id: str) -> Dict:
    db = _get_db()
    campaign = await db.campaigns.find_one({"campaign_id": campaign_id}) or \
               await db.campaigns.find_one({"id": campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign not found: {campaign_id}")
    return campaign


async def _load_character(character_id: str) -> Optional[Dict]:
    db = _get_db()
    try:
        oid = ObjectId(character_id)
    except Exception:
        return None
    char = await db.characters_v2.find_one({"_id": oid})
    if char:
        char["id"] = str(char.pop("_id"))
    return char


def _format_action_summary(
    beat: Dict,
    *,
    outcome: str,
    roll_total: Optional[int] = None,
    outcome_text: Optional[str] = None,
    complication: Optional[str] = None,
    creative_text: Optional[str] = None,
    judgment: Optional[str] = None,
    narration: Optional[str] = None,
) -> str:
    """Compact one-paragraph summary of what the player just did + result.
    Fed to generate_next_scene so the LLM can write a continuation that
    reflects the actual play."""
    lines = [
        f"Beat just resolved: '{beat.get('title','')}' "
        f"({beat.get('check_type','Investigation')} DC {beat.get('dc',12)})",
        f"Outcome: {outcome}",
    ]
    if creative_text:
        lines.append(f'Player approach: "{creative_text.strip()[:300]}"')
        if judgment:
            lines.append(f"DM judgment: {judgment}")
        if narration:
            lines.append(f"DM narration of approach: {narration[:240]}")
    elif outcome == "skipped":
        lines.append("Player chose to proceed without rolling.")
    else:
        if roll_total is not None:
            lines.append(f"Roll total: {roll_total} vs DC {beat.get('dc',12)}")
        if outcome_text:
            lines.append(f"Detail: {outcome_text[:240]}")
    if complication:
        lines.append(f"Complication: {complication[:240]}")
    return "\n".join(lines)


# -------------------- request bodies --------------------


class DraftStorylineBody(BaseModel):
    character_id: str
    hook_text: str
    hook_id: Optional[str] = None
    hook_topic: Optional[str] = None
    hook_verb: Optional[str] = None
    narration_context: Optional[str] = None


class ResolveStorylineBody(BaseModel):
    outcome: str  # "passed" | "failed" | "skipped"
    outcome_text: Optional[str] = None
    roll_total: Optional[int] = None
    # Failure handling: "fail-forward" advances to next beat with a complication,
    # "press-on" retries the SAME beat (one-time per storyline) with a complication.
    # Defaults to "fail-forward" when outcome="failed".
    mode: Optional[str] = None  # "fail-forward" | "press-on"


class CreativeApproachBody(BaseModel):
    """Player describes an alternative way to resolve the current beat."""
    approach_text: str


# -------------------- endpoints --------------------


@router.post("/{campaign_id}/storylines/draft")
async def draft_storyline_endpoint(campaign_id: str, body: DraftStorylineBody):
    if not body.hook_text or not body.hook_text.strip():
        raise HTTPException(status_code=400, detail="hook_text is required")

    campaign = await _load_campaign(campaign_id)
    character = await _load_character(body.character_id)
    if not character:
        raise HTTPException(status_code=404, detail=f"Character not found: {body.character_id}")

    # Pass recent active knowledge cards so the storyline grounds in existing
    # NPCs / locations / factions instead of inventing fresh names every turn.
    try:
        cards_cursor = _cards_collection().find(
            {"campaign_id": campaign_id, "status": {"$ne": "failed"}}, {"_id": 0}
        ).sort("updatedAt", -1).limit(20)
        recent_cards = await cards_cursor.to_list(length=20)
        campaign["_recent_cards"] = recent_cards
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to load recent cards for storyline grounding: {exc}")

    hook = {
        "id": body.hook_id or f"hook_{uuid4().hex[:8]}",
        "text": body.hook_text.strip(),
        "topic": (body.hook_topic or body.hook_text.strip()[:48]),
        "verb_hint": (body.hook_verb or "examine"),
    }

    drafted = await draft_initial_scene(
        campaign=campaign,
        character=character,
        hook=hook,
        narration_context=body.narration_context or "",
    )

    now = datetime.now(timezone.utc)
    storyline_id = f"sl_{uuid4().hex[:10]}"

    # Seed a quest KnowledgeCard from the FIRST beat. Open-ended storylines
    # show the active scene with no fixed "Beat X of N" since beats are
    # generated dynamically as the player acts.
    first_beat = (drafted.get("beats") or [{}])[0]
    quest_card = KnowledgeCard(
        type="quest",
        title=drafted.get("title") or "Active Investigation",
        description=(
            f"{first_beat.get('description','')} (Active scene — "
            f"suggested {first_beat.get('check_type','Investigation')} DC {first_beat.get('dc',12)}.)"
        ),
        source="hook-storyline",
        confidence="high",
        tags=["quest", "active", "investigation", "storyline"],
        status="active",
        updatedAt=now,
    )
    quest_doc = {**quest_card.model_dump(), "campaign_id": campaign_id, "storyline_id": storyline_id}
    await _cards_collection().insert_one(quest_doc)

    storyline_doc = {
        "id": storyline_id,
        "campaign_id": campaign_id,
        "character_id": body.character_id,
        "title": drafted.get("title") or "Investigation",
        "hook_text": hook["text"],
        "hook_id": hook["id"],
        "hook_topic": hook["topic"],
        "status": "active",
        "current_beat": 0,
        "beats": drafted["beats"],
        "total_dc": drafted["total_dc"],
        "open_ended": True,
        "press_on_used": False,
        "complication": None,
        "reward": None,
        "quest_card_id": quest_card.id,
        "created_at": now,
        "updated_at": now,
    }
    await _storylines_collection().insert_one(dict(storyline_doc))

    return {
        "storyline": storyline_to_dict(storyline_doc),
        "quest_card_id": quest_card.id,
    }


@router.get("/{campaign_id}/storylines")
async def list_storylines(campaign_id: str):
    cursor = _storylines_collection().find({"campaign_id": campaign_id}, {"_id": 0}).sort("updated_at", -1)
    docs = await cursor.to_list(length=100)
    for d in docs:
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
        if isinstance(d.get("updated_at"), datetime):
            d["updated_at"] = d["updated_at"].isoformat()
    return {"storylines": docs}


@router.get("/{campaign_id}/storylines/{storyline_id}")
async def get_storyline(campaign_id: str, storyline_id: str):
    doc = await _storylines_collection().find_one(
        {"campaign_id": campaign_id, "id": storyline_id}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Storyline not found")
    return storyline_to_dict(doc)


_ENTITY_TYPE_TO_CARD_TYPE = {
    "npc": "character",
    "character": "character",
    "person": "character",
    "location": "location",
    "place": "location",
    "faction": "faction",
    "guild": "faction",
    "house": "faction",
}


_ENTITY_BLOCKLIST = {
    "you", "your", "the", "a", "an", "this", "that", "and", "or", "but", "is",
    "are", "was", "were", "be", "been", "being", "to", "of", "in", "on", "at",
    "by", "for", "with", "from", "as", "it", "its", "they", "them", "their",
}


def _entity_label(entity_type: str, name: str) -> str:
    """Normalize an entity name for case-insensitive de-duplication."""
    return f"{(entity_type or '').strip().lower()}::{(name or '').strip().lower()}"


def _description_snippet_for(name: str, description: str, max_len: int = 240) -> str:
    """Pick the sentence(s) from `description` that mention `name` so the
    auto-minted card carries the most relevant context. Falls back to a
    leading slice of the description if no sentence directly names the entity.
    """
    text = (description or "").strip()
    if not text:
        return ""
    name_low = (name or "").strip().lower()
    if not name_low:
        return text[:max_len].strip()
    # Split by sentence-ending punctuation
    import re as _re
    sentences = _re.split(r"(?<=[.!?])\s+", text)
    matched = [s.strip() for s in sentences if name_low in s.lower()]
    if matched:
        joined = " ".join(matched)
        return joined[:max_len].strip()
    return text[:max_len].strip()


async def _extract_targets_from_description_llm(
    description: str, max_targets: int = 4
) -> List[Dict]:
    """Cheap LLM fallback when the storyline beat returned `targets: []` but
    the description clearly names entities. Returns a normalized list of
    {type, name} entries (npc | location | faction). Empty on any failure.
    """
    text = (description or "").strip()
    if not text:
        return []
    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return []
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        prompt = (
            "Extract up to "
            f"{max_targets} NAMED ENTITIES from the D&D scene below — proper nouns "
            "the player has now learned by name. Each entity must be one of: "
            "npc (a person), location (a place), or faction (a guild/house/order). "
            "Names must appear verbatim in the text. Skip generic nouns like "
            "'the merchant', 'a guard', 'the tavern' — only entities with proper "
            "names. Cap at top "
            f"{max_targets}.\n\n"
            "=== SCENE ===\n"
            f"{text}\n\n"
            "=== OUTPUT (strict JSON, no code fence) ===\n"
            "{\"entities\": ["
            "{\"type\": \"npc|location|faction\", \"name\": \"<verbatim proper noun>\"}"
            "]}\n"
            "Return {\"entities\": []} if there are no proper-name entities."
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"target-extract-{uuid4()}",
            system_message=(
                "You are a precise scene parser. You return only proper-noun "
                "entities verbatim. Output strict JSON only."
            ),
        )
        chat.with_model("openai", "gpt-4o-mini")
        raw = (await chat.send_message(UserMessage(text=prompt))) or ""
        s = raw.strip()
        if s.startswith("```"):
            s = s.strip("`")
            if s.lower().startswith("json"):
                s = s[4:].lstrip()
        import json as _json
        try:
            data = _json.loads(s)
        except Exception:
            a, b = s.find("{"), s.rfind("}")
            data = _json.loads(s[a:b + 1]) if a != -1 and b > a else {}
        out: List[Dict] = []
        for e in (data.get("entities") or [])[:max_targets]:
            if not isinstance(e, dict):
                continue
            t = (e.get("type") or "").strip().lower()
            n = (e.get("name") or "").strip()
            if t not in {"npc", "location", "faction"}:
                continue
            if not n or n.lower() in _ENTITY_BLOCKLIST:
                continue
            # Verbatim check — must appear in the description
            if n.lower() not in text.lower():
                continue
            out.append({"type": t, "name": n[:80]})
        return out
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"target extraction (LLM) failed: {exc}")
        return []


async def _mint_target_cards_if_revealed(
    *,
    campaign_id: str,
    storyline: Dict,
    beat: Dict,
    outcome: str,
) -> List[Dict]:
    """When a knowledge beat is revealed (passed or partial via creative path),
    auto-mint Knowledge Cards for each named entity in `beat.targets[]`
    (or fall back to extracting them from the description). NPCs become
    'character' cards, locations become 'location' cards, factions become
    'faction' cards. Skips entities the campaign already has a card for
    (case-insensitive type+title match) so we don't pollute the deck on
    every re-reveal.
    Returns the list of newly-minted card dicts.
    """
    if outcome != "passed":
        return []
    revelation = (beat.get("description") or "").strip()
    if not revelation:
        return []

    raw_targets = beat.get("targets") or []
    targets: List[Dict] = []
    for t in raw_targets:
        if not isinstance(t, dict):
            continue
        et = (t.get("type") or "").strip().lower()
        nm = (t.get("name") or "").strip()
        if et in _ENTITY_TYPE_TO_CARD_TYPE and nm and nm.lower() not in _ENTITY_BLOCKLIST:
            targets.append({"type": et, "name": nm})

    # Fallback: LLM extracts entities from the description text
    if not targets:
        try:
            targets = await _extract_targets_from_description_llm(revelation, max_targets=4)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"fallback target extraction failed: {exc}")
            targets = []

    if not targets:
        return []

    # Pre-load existing card titles for de-dup
    existing_labels = set()
    try:
        cur = _cards_collection().find(
            {"campaign_id": campaign_id, "type": {"$in": ["character", "location", "faction"]}},
            {"_id": 0, "type": 1, "title": 1},
        )
        async for c in cur:
            existing_labels.add(_entity_label(c.get("type", ""), c.get("title", "")))
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"existing-card preload failed: {exc}")

    minted: List[Dict] = []
    now = datetime.now(timezone.utc)
    storyline_title = storyline.get("title") or "investigation"
    storyline_id = storyline.get("id")

    for t in targets[:4]:
        card_type = _ENTITY_TYPE_TO_CARD_TYPE.get(t["type"])
        if not card_type:
            continue
        title = t["name"].strip()
        if not title:
            continue
        label = _entity_label(card_type, title)
        if label in existing_labels:
            continue
        existing_labels.add(label)  # avoid dupes within same call
        snippet = _description_snippet_for(title, revelation, max_len=300)
        if not snippet:
            snippet = f"Mentioned during the {storyline_title}."
        try:
            card = KnowledgeCard(
                type=card_type,
                title=title[:80],
                description=snippet,
                source="storyline-target",
                confidence="medium",
                tags=[
                    "auto-minted",
                    "from-storyline",
                    storyline_title.lower(),
                    f"target-{t['type']}",
                ],
                status="active",
                updatedAt=now,
            )
            doc = {
                **card.model_dump(),
                "campaign_id": campaign_id,
                "storyline_id": storyline_id,
                "beat_title": beat.get("title"),
            }
            await _cards_collection().insert_one(dict(doc))
            out = {k: v for k, v in doc.items() if k != "_id"}
            if isinstance(out.get("updatedAt"), datetime):
                out["updatedAt"] = out["updatedAt"].isoformat()
            minted.append(out)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"target card mint failed for {title}: {exc}")
            continue

    return minted


async def _mint_lead_card_if_knowledge(
    *,
    campaign_id: str,
    storyline: Dict,
    beat: Dict,
    outcome: str,
    creative_text: Optional[str] = None,
) -> Optional[Dict]:
    """If the just-resolved beat was reveal_type='knowledge', mint a Lead
    knowledge card.
      - On 'passed': the lead is REVEALED (description = the secret revelation).
      - On 'failed': the lead is SEALED — title visible, body hidden behind a
        prompt encouraging the player to find help to unravel it later.
    Returns the card dict (without _id) so the caller can include it in the
    response payload, or None if the beat wasn't a knowledge beat.
    """
    if (beat.get("reveal_type") or "") != "knowledge":
        return None

    revelation = (beat.get("description") or "").strip()
    if not revelation:
        return None

    targets = beat.get("targets") or []
    target_names = [str(t.get("name", "")).strip() for t in targets if isinstance(t, dict) and t.get("name")]
    target_chip = ", ".join(target_names[:3])
    base_tags = ["lead", storyline.get("title", "investigation").lower()]
    if target_chip:
        base_tags.append(target_chip.lower())
    for t in targets:
        if isinstance(t, dict) and t.get("type"):
            base_tags.append(f"target-{t['type']}")

    now = datetime.now(timezone.utc)
    if outcome == "passed":
        card = KnowledgeCard(
            type="lead",
            title=beat.get("title") or "Lead",
            description=revelation,
            source="storyline-knowledge",
            confidence="high",
            tags=base_tags + ["revealed"],
            status="active",
            updatedAt=now,
        )
        doc = {
            **card.model_dump(),
            "campaign_id": campaign_id,
            "storyline_id": storyline.get("id"),
            "beat_title": beat.get("title"),
            "secret_content": None,         # nothing left hidden
            "reveal_dc": beat.get("dc", 12),
            "reveal_check_type": beat.get("check_type", "Investigation"),
            "targets": targets,
        }
    else:  # 'failed'
        targets_hint = (" Targets pointed to: " + target_chip + ".") if target_chip else ""
        sealed_body = (
            "A lead worth pursuing — but you couldn't piece it together in the moment."
            " Find someone who can help you read it." + targets_hint
        )
        card = KnowledgeCard(
            type="lead",
            title=beat.get("title") or "Sealed Lead",
            description=sealed_body,
            source="storyline-knowledge",
            confidence="low",
            tags=base_tags + ["sealed"],
            status="sealed",
            updatedAt=now,
        )
        doc = {
            **card.model_dump(),
            "campaign_id": campaign_id,
            "storyline_id": storyline.get("id"),
            "beat_title": beat.get("title"),
            "secret_content": revelation,    # held back until unsealed
            "reveal_dc": beat.get("dc", 12),
            "reveal_check_type": beat.get("check_type", "Investigation"),
            "targets": targets,
        }

    await _cards_collection().insert_one(dict(doc))
    out = {k: v for k, v in doc.items() if k != "_id"}
    if isinstance(out.get("updatedAt"), datetime):
        out["updatedAt"] = out["updatedAt"].isoformat()
    return out


@router.post("/{campaign_id}/storylines/{storyline_id}/resolve")
async def resolve_storyline_beat(campaign_id: str, storyline_id: str, body: ResolveStorylineBody):
    if body.outcome not in {"passed", "failed", "skipped"}:
        raise HTTPException(status_code=400, detail="outcome must be passed|failed|skipped")

    doc = await _storylines_collection().find_one({"campaign_id": campaign_id, "id": storyline_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Storyline not found")
    if doc.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Storyline already completed")

    current = int(doc.get("current_beat") or 0)
    beats = doc.get("beats") or []
    cur_beat = beats[current] if 0 <= current < len(beats) else {}
    campaign = await _load_campaign(campaign_id)
    character = await _load_character(doc.get("character_id")) or {}

    # Pass recent active knowledge cards so the next-scene generator grounds
    # in existing NPCs / locations / factions instead of inventing fresh
    # names every beat.
    try:
        cards_cursor = _cards_collection().find(
            {"campaign_id": campaign_id, "status": {"$ne": "failed"}}, {"_id": 0}
        ).sort("updatedAt", -1).limit(20)
        recent_cards = await cards_cursor.to_list(length=20)
        campaign["_recent_cards"] = recent_cards
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to load recent cards for next-scene grounding: {exc}")

    # Decide failure mode (only relevant when outcome == 'failed').
    mode = (body.mode or "").strip().lower()
    is_press_on = (body.outcome == "failed" and mode == "press-on")

    if is_press_on:
        if doc.get("press_on_used"):
            raise HTTPException(status_code=400, detail="Press On already used this storyline")
        # Generate the cost-of-retry complication beat WITHOUT advancing.
        complication_text = await generate_complication_beat(
            intent=campaign.get("intent") or {},
            world=campaign.get("world") or {},
            character=character,
            storyline=doc,
            beat=cur_beat,
            mode="press-on",
        )
        # Mark the beat with the complication note but keep it active.
        beats = doc.get("beats") or []
        if 0 <= current < len(beats):
            beats[current]["status"] = "active"
            beats[current]["outcome_text"] = (body.outcome_text or "Failed — pressing on.")[:240]
        doc["press_on_used"] = True
        doc["complication"] = complication_text
        doc["updated_at"] = datetime.now(timezone.utc)
        await _storylines_collection().update_one(
            {"campaign_id": campaign_id, "id": storyline_id},
            {"$set": {k: v for k, v in doc.items() if k != "_id"}},
        )
        return {
            "storyline": storyline_to_dict(doc),
            "completed": False,
            "mode": "press-on",
            "complication": complication_text,
            "reward": None,
        }

    # Default path: advance the beat (outcome can be passed | failed | skipped).
    storyline = advance_storyline(doc, current, body.outcome, body.outcome_text)

    # Knowledge-beat reward: mint a "lead" knowledge card. Passed = revealed;
    # failed = sealed (player can later try to unseal it).
    lead_card: Optional[Dict] = None
    target_cards: List[Dict] = []
    if body.outcome in {"passed", "failed"}:
        try:
            lead_card = await _mint_lead_card_if_knowledge(
                campaign_id=campaign_id,
                storyline=storyline,
                beat=cur_beat,
                outcome=body.outcome,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"lead card mint failed (non-fatal): {exc}")
        # Also auto-mint Knowledge Cards for every named entity revealed
        # (NPCs, locations, factions). Only on a clean pass — failed leads
        # stay sealed and don't expose the entities.
        if body.outcome == "passed":
            try:
                target_cards = await _mint_target_cards_if_revealed(
                    campaign_id=campaign_id,
                    storyline=storyline,
                    beat=cur_beat,
                    outcome=body.outcome,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"target card mint failed (non-fatal): {exc}")

    # If failed (and not press-on), produce a fail-forward complication so the
    # Adventure Log gets a narrative beat tying the failure to the story.
    # On success/skip, clear any previously carried complication — the player
    # has resolved the beat clean, the carry-over is no longer pressing.
    complication_text: Optional[str] = None
    if body.outcome == "failed":
        try:
            complication_text = await generate_complication_beat(
                intent=campaign.get("intent") or {},
                world=campaign.get("world") or {},
                character=character,
                storyline=storyline,
                beat=cur_beat,
                mode="fail-forward",
            )
            storyline["complication"] = complication_text
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"complication beat failed (non-fatal): {exc}")
    else:
        storyline["complication"] = None

    # Open-ended storylines: after resolving the current beat, the DM decides
    # whether to wrap up OR draft the next scene card based on what happened.
    if storyline.get("open_ended") and storyline.get("status") != "completed":
        action_summary = _format_action_summary(
            cur_beat,
            outcome=body.outcome,
            roll_total=body.roll_total,
            outcome_text=body.outcome_text,
            complication=complication_text,
        )
        try:
            nxt = await generate_next_scene(
                campaign=campaign,
                character=character,
                storyline=storyline,
                player_action_summary=action_summary,
            )
            if nxt.get("is_final"):
                storyline["status"] = "completed"
                storyline["epilogue"] = nxt.get("epilogue")
            else:
                new_beat = nxt.get("beat") or {}
                if new_beat:
                    beats_list = storyline.get("beats") or []
                    beats_list.append(new_beat)
                    storyline["beats"] = beats_list
                    storyline["current_beat"] = len(beats_list) - 1
                    # Bump total_dc for reward scaling
                    storyline["total_dc"] = int(storyline.get("total_dc", 0)) + int(new_beat.get("dc") or 0)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"next-scene generation failed (non-fatal): {exc}")

    completed = storyline.get("status") == "completed"
    reward: Optional[Dict] = None
    if completed:
        reward = await generate_storyline_reward(campaign, character, storyline)
        storyline["reward"] = reward
        # Mark the linked quest card based on pass ratio: completed if any
        # beats passed, else failed.
        passed_any = any(b.get("status") == "passed" for b in (storyline.get("beats") or []))
        quest_status = "completed" if passed_any else "failed"
        quest_card_id = storyline.get("quest_card_id")
        if quest_card_id:
            await _cards_collection().update_one(
                {"campaign_id": campaign_id, "id": quest_card_id},
                {"$set": {"status": quest_status, "updatedAt": datetime.now(timezone.utc)}},
            )
    else:
        # Update the linked quest card description so the Quest Log reflects
        # the new active beat. Open-ended storylines drop "Beat X of N" since
        # the chain grows dynamically.
        quest_card_id = storyline.get("quest_card_id")
        if quest_card_id:
            beats = storyline.get("beats") or []
            cur = int(storyline.get("current_beat") or 0)
            cur_beat_now = beats[cur] if 0 <= cur < len(beats) else {}
            if storyline.get("open_ended"):
                check_chip = ""
                if int(cur_beat_now.get("dc") or 0) > 0:
                    check_chip = (
                        f" (Active scene — suggested "
                        f"{cur_beat_now.get('check_type','Investigation')} "
                        f"DC {cur_beat_now.get('dc',12)}.)"
                    )
                else:
                    check_chip = " (Active scene.)"
                new_desc = f"{cur_beat_now.get('description','')}{check_chip}"
            else:
                new_desc = (
                    f"{cur_beat_now.get('description','')} (Beat {cur+1} of {len(beats)} — "
                    f"{cur_beat_now.get('check_type','Investigation')} DC {cur_beat_now.get('dc',12)}.)"
                )
            await _cards_collection().update_one(
                {"campaign_id": campaign_id, "id": quest_card_id},
                {"$set": {"description": new_desc, "updatedAt": datetime.now(timezone.utc)}},
            )

    await _storylines_collection().update_one(
        {"campaign_id": campaign_id, "id": storyline_id},
        {"$set": {k: v for k, v in storyline.items() if k != "_id"}},
    )

    return {
        "storyline": storyline_to_dict(storyline),
        "completed": completed,
        "mode": "fail-forward" if body.outcome == "failed" else "advance",
        "complication": complication_text,
        "reward": reward,
        "lead": lead_card,
        "target_cards": target_cards,
    }


@router.post("/{campaign_id}/storylines/{storyline_id}/creative")
async def creative_approach_endpoint(
    campaign_id: str, storyline_id: str, body: CreativeApproachBody
):
    """Player proposes an alternative approach to the current beat. The DM
    judges (passed | partial | failed); on passed/partial, the beat advances
    and the player gets credit. On failed, the beat is marked failed and we
    fall through to fail-forward (complication + advance)."""
    text = (body.approach_text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="approach_text is required")

    doc = await _storylines_collection().find_one({"campaign_id": campaign_id, "id": storyline_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Storyline not found")
    if doc.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Storyline already completed")

    current = int(doc.get("current_beat") or 0)
    beats = doc.get("beats") or []
    if not (0 <= current < len(beats)):
        raise HTTPException(status_code=400, detail="No active beat")
    cur_beat = beats[current]

    campaign = await _load_campaign(campaign_id)
    character = await _load_character(doc.get("character_id")) or {}

    # Ground next-scene generation in existing knowledge cards.
    try:
        cards_cursor = _cards_collection().find(
            {"campaign_id": campaign_id, "status": {"$ne": "failed"}}, {"_id": 0}
        ).sort("updatedAt", -1).limit(20)
        recent_cards = await cards_cursor.to_list(length=20)
        campaign["_recent_cards"] = recent_cards
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to load recent cards for creative-path grounding: {exc}")

    judgment = await judge_creative_approach(
        intent=campaign.get("intent") or {},
        world=campaign.get("world") or {},
        character=character,
        storyline=doc,
        beat=cur_beat,
        approach_text=text,
    )

    judged_outcome = judgment.get("outcome", "partial")
    narration = judgment.get("narration") or ""
    # Map judgment to a storyline outcome:
    #   'passed'  -> advance with a clean pass
    #   'partial' -> advance, marked passed (player took a hit narratively)
    #   'failed'  -> mark failed, fall through to fail-forward
    storyline_outcome = "passed" if judged_outcome in {"passed", "partial"} else "failed"

    storyline = advance_storyline(
        doc, current, storyline_outcome,
        outcome_text=f"Creative approach ({judged_outcome}): {narration}"[:240],
    )

    # Knowledge-beat reward via creative path: same minting rules.
    lead_card: Optional[Dict] = None
    target_cards: List[Dict] = []
    try:
        lead_card = await _mint_lead_card_if_knowledge(
            campaign_id=campaign_id,
            storyline=storyline,
            beat=cur_beat,
            outcome=storyline_outcome,
            creative_text=text,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"lead card mint via creative failed: {exc}")
    # Auto-mint Knowledge Cards for revealed entities on a creative pass.
    if storyline_outcome == "passed":
        try:
            target_cards = await _mint_target_cards_if_revealed(
                campaign_id=campaign_id,
                storyline=storyline,
                beat=cur_beat,
                outcome=storyline_outcome,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"target card mint via creative failed: {exc}")

    complication_text: Optional[str] = None
    if storyline_outcome == "failed":
        try:
            complication_text = await generate_complication_beat(
                intent=campaign.get("intent") or {},
                world=campaign.get("world") or {},
                character=character,
                storyline=storyline,
                beat=cur_beat,
                mode="fail-forward",
            )
            storyline["complication"] = complication_text
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"complication after creative-fail failed: {exc}")
    else:
        # Player solved this beat creatively — the carried complication (if any)
        # has been worked around. Clear it.
        storyline["complication"] = None

    # Open-ended storylines: chain into the next dynamically-generated scene.
    if storyline.get("open_ended") and storyline.get("status") != "completed":
        action_summary = _format_action_summary(
            cur_beat,
            outcome=storyline_outcome,
            outcome_text=f"Creative approach ({judged_outcome}).",
            complication=complication_text,
            creative_text=text,
            judgment=judged_outcome,
            narration=narration,
        )
        try:
            nxt = await generate_next_scene(
                campaign=campaign,
                character=character,
                storyline=storyline,
                player_action_summary=action_summary,
            )
            if nxt.get("is_final"):
                storyline["status"] = "completed"
                storyline["epilogue"] = nxt.get("epilogue")
            else:
                new_beat = nxt.get("beat") or {}
                if new_beat:
                    beats_list = storyline.get("beats") or []
                    beats_list.append(new_beat)
                    storyline["beats"] = beats_list
                    storyline["current_beat"] = len(beats_list) - 1
                    storyline["total_dc"] = int(storyline.get("total_dc", 0)) + int(new_beat.get("dc") or 0)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"next-scene generation (creative path) failed: {exc}")

    completed = storyline.get("status") == "completed"
    reward: Optional[Dict] = None
    if completed:
        reward = await generate_storyline_reward(campaign, character, storyline)
        storyline["reward"] = reward
        passed_any = any(b.get("status") == "passed" for b in (storyline.get("beats") or []))
        quest_status = "completed" if passed_any else "failed"
        quest_card_id = storyline.get("quest_card_id")
        if quest_card_id:
            await _cards_collection().update_one(
                {"campaign_id": campaign_id, "id": quest_card_id},
                {"$set": {"status": quest_status, "updatedAt": datetime.now(timezone.utc)}},
            )

    await _storylines_collection().update_one(
        {"campaign_id": campaign_id, "id": storyline_id},
        {"$set": {k: v for k, v in storyline.items() if k != "_id"}},
    )

    return {
        "storyline": storyline_to_dict(storyline),
        "completed": completed,
        "judgment": judged_outcome,        # 'passed' | 'partial' | 'failed'
        "narration": narration,            # DM's response to the creative approach
        "applied_check": judgment.get("applied_check"),
        "complication": complication_text,  # only when judged_outcome == 'failed'
        "reward": reward,
        "lead": lead_card,
        "target_cards": target_cards,
    }


@router.post("/{campaign_id}/storylines/{storyline_id}/abandon")
async def abandon_storyline(campaign_id: str, storyline_id: str):
    res = await _storylines_collection().update_one(
        {"campaign_id": campaign_id, "id": storyline_id, "status": "active"},
        {"$set": {"status": "abandoned", "updated_at": datetime.now(timezone.utc)}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Active storyline not found")
    # Mark linked quest card failed
    doc = await _storylines_collection().find_one(
        {"campaign_id": campaign_id, "id": storyline_id}, {"quest_card_id": 1}
    )
    if doc and doc.get("quest_card_id"):
        await _cards_collection().update_one(
            {"campaign_id": campaign_id, "id": doc["quest_card_id"]},
            {"$set": {"status": "failed", "updatedAt": datetime.now(timezone.utc)}},
        )
    return {"ok": True}


# ==================== Sealed Lead Cards ====================


class UnsealLeadBody(BaseModel):
    """Player attempts to unseal a previously failed knowledge lead.
    `mode` selects roll vs creative:
      - "roll":     rolls d20 + ability mod (frontend computes total)
      - "creative": LLM judge, similar to storyline /creative
    """
    mode: str  # "roll" | "creative"
    roll_total: Optional[int] = None
    creative_text: Optional[str] = None


@router.post("/{campaign_id}/cards/{card_id}/unseal")
async def unseal_lead(campaign_id: str, card_id: str, body: UnsealLeadBody):
    card = await _cards_collection().find_one(
        {"campaign_id": campaign_id, "id": card_id}, {"_id": 0}
    )
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if card.get("type") != "lead" or card.get("status") != "sealed":
        raise HTTPException(status_code=400, detail="Card is not a sealed lead")

    secret = (card.get("secret_content") or "").strip()
    if not secret:
        raise HTTPException(status_code=400, detail="Lead has no hidden content to unseal")

    dc = int(card.get("reveal_dc") or 12)
    check_type = card.get("reveal_check_type") or "Investigation"
    now = datetime.now(timezone.utc)

    if body.mode == "roll":
        if body.roll_total is None:
            raise HTTPException(status_code=400, detail="roll_total required for mode=roll")
        succeeded = int(body.roll_total) >= dc
        if not succeeded:
            return {
                "ok": False,
                "unsealed": False,
                "narration": (
                    "You turn the matter over again, but the picture won't resolve. "
                    "You'll need someone with a sharper eye on this — or a fresh angle entirely."
                ),
                "card": card,
            }
        await _cards_collection().update_one(
            {"campaign_id": campaign_id, "id": card_id},
            {"$set": {
                "status": "active",
                "description": secret,
                "secret_content": None,
                "tags": list({*(card.get("tags") or []), "revealed", "unsealed"} - {"sealed"}),
                "confidence": "high",
                "updatedAt": now,
            }},
        )
        narration = (
            "It clicks into place — the piece you were missing surfaces, "
            "and the lead reads cleanly now."
        )
    elif body.mode == "creative":
        approach = (body.creative_text or "").strip()
        if not approach:
            raise HTTPException(status_code=400, detail="creative_text required for mode=creative")
        campaign = await _load_campaign(campaign_id)
        # Find any character_id we can use for the judge — fall back to None
        sl_id = card.get("storyline_id")
        character = None
        if sl_id:
            sl = await _storylines_collection().find_one(
                {"campaign_id": campaign_id, "id": sl_id}, {"character_id": 1}
            )
            if sl and sl.get("character_id"):
                character = await _load_character(sl["character_id"]) or {}
        # Synthetic beat for the judge
        synthetic_beat = {
            "title": card.get("title") or "Sealed Lead",
            "task": "Find a way to unravel the lead by an alternative means.",
            "description": secret,
            "dc": dc,
            "check_type": check_type,
        }
        from services.storyline_service import judge_creative_approach
        judgment = await judge_creative_approach(
            intent=campaign.get("intent") or {},
            world=campaign.get("world") or {},
            character=character or {},
            storyline={"title": card.get("title", "Sealed Lead")},
            beat=synthetic_beat,
            approach_text=approach,
        )
        outcome = judgment.get("outcome") or "partial"
        narration = judgment.get("narration") or ""
        if outcome in {"passed", "partial"}:
            await _cards_collection().update_one(
                {"campaign_id": campaign_id, "id": card_id},
                {"$set": {
                    "status": "active",
                    "description": secret,
                    "secret_content": None,
                    "tags": list({*(card.get("tags") or []), "revealed", "unsealed"} - {"sealed"}),
                    "confidence": "high" if outcome == "passed" else "medium",
                    "updatedAt": now,
                }},
            )
        else:
            return {
                "ok": False,
                "unsealed": False,
                "narration": narration or (
                    "Your angle doesn't pry it open. The lead stays sealed."
                ),
                "card": card,
            }
    else:
        raise HTTPException(status_code=400, detail="mode must be 'roll' or 'creative'")

    updated = await _cards_collection().find_one(
        {"campaign_id": campaign_id, "id": card_id}, {"_id": 0}
    )
    if updated and isinstance(updated.get("updatedAt"), datetime):
        updated["updatedAt"] = updated["updatedAt"].isoformat()
    return {
        "ok": True,
        "unsealed": True,
        "narration": narration,
        "card": updated,
    }
