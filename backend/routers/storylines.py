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


def _campaigns_collection():
    return _get_db()["campaigns"]


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


from services.mission_types import get_mission_type, get_mission_type_by_slug


async def _resolve_mission_type(
    campaign_id: str,
    mission_type_id: Optional[str],
    mission_type_slug: Optional[str],
    campaign_doc: Optional[Dict] = None,
) -> Optional[Dict]:
    """Look up a mission-type blueprint by id-or-slug; returns None when
    not given or not found. Slug lookup includes both the system seeds
    AND any user-defined types owned by THIS campaign.

    When neither id nor slug is supplied on the request, falls back to
    the mission type chosen at campaign setup (stored on the campaign doc)."""
    if mission_type_id:
        doc = await get_mission_type(_get_db(), mission_type_id=mission_type_id)
        if doc:
            return doc
    if mission_type_slug:
        doc = await get_mission_type_by_slug(
            _get_db(), slug=mission_type_slug, campaign_id=campaign_id,
        )
        if doc:
            return doc
    # Fallback: read from the campaign-level selection captured at setup.
    if campaign_doc:
        fb_id = campaign_doc.get("mission_type_id")
        fb_slug = campaign_doc.get("mission_type_slug")
        if fb_id:
            doc = await get_mission_type(_get_db(), mission_type_id=fb_id)
            if doc:
                return doc
        if fb_slug:
            doc = await get_mission_type_by_slug(
                _get_db(), slug=fb_slug, campaign_id=campaign_id,
            )
            if doc:
                return doc
    return None


class DraftStorylineBody(BaseModel):
    character_id: str
    hook_text: str
    hook_id: Optional[str] = None
    hook_topic: Optional[str] = None
    hook_verb: Optional[str] = None
    narration_context: Optional[str] = None
    # Optional mission-type id (or slug) — when set, the storyline is
    # shaped to follow that blueprint's phase arc.
    mission_type_id: Optional[str] = None
    mission_type_slug: Optional[str] = None


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

    resolved_mission_type = await _resolve_mission_type(
        campaign_id, body.mission_type_id, body.mission_type_slug,
        campaign_doc=campaign,
    )

    drafted = await draft_initial_scene(
        campaign=campaign,
        character=character,
        hook=hook,
        narration_context=body.narration_context or "",
        mission_type=resolved_mission_type,
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

    # Lightweight snapshot stored on the storyline so future generate_next_scene
    # calls + the frontend Active-Phase badge can read it without a join.
    from services.storyline_service import _mission_type_snapshot
    mission_type_snapshot = _mission_type_snapshot(resolved_mission_type)

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
        "mission_type": mission_type_snapshot,
        "created_at": now,
        "updated_at": now,
    }
    await _storylines_collection().insert_one(dict(storyline_doc))

    return {
        "storyline": storyline_to_dict(storyline_doc),
        "quest_card_id": quest_card.id,
    }



# -------------------- Off-hook storyline spawner --------------------
#
# When the player's action doesn't fit the current beat, this endpoint pauses
# the current storyline (preserving "pending obligations" so NPCs the player
# walked away from can react later) and drafts a NEW storyline rooted in the
# action, using the CLOSEST existing mission-type blueprint.

class SpawnFromActionBody(BaseModel):
    character_id: str
    player_action: str
    current_storyline_id: Optional[str] = None
    narration_context: Optional[str] = None


@router.post("/{campaign_id}/storylines/spawn-from-action")
async def spawn_storyline_from_action(campaign_id: str, body: SpawnFromActionBody):
    action = (body.player_action or "").strip()
    if not action:
        raise HTTPException(status_code=400, detail="player_action is required")

    campaign = await _load_campaign(campaign_id)
    character = await _load_character(body.character_id)
    if not character:
        raise HTTPException(status_code=404, detail=f"Character not found: {body.character_id}")

    # Load the current storyline (if the caller provided an id) so we can
    # describe the CURRENT beat to the classifier.
    current_storyline: Optional[Dict] = None
    if body.current_storyline_id:
        current_storyline = await _storylines_collection().find_one(
            {"campaign_id": campaign_id, "id": body.current_storyline_id}, {"_id": 0}
        )
    current_beat_desc = ""
    current_title = ""
    if current_storyline:
        cur_idx = int(current_storyline.get("current_beat") or 0)
        beats = current_storyline.get("beats") or []
        if 0 <= cur_idx < len(beats):
            cb = beats[cur_idx] or {}
            current_beat_desc = (cb.get("description") or "")
        current_title = current_storyline.get("title") or ""

    # Available mission types — system + this campaign's owned customs.
    from services.mission_types import list_mission_types, get_mission_type_by_slug
    mission_types = await list_mission_types(_get_db(), campaign_id=campaign_id)

    from services.storyline_spawner import (
        classify_action_for_spawn,
        extract_pending_obligations_from_storyline,
    )
    decision = await classify_action_for_spawn(
        player_action=action,
        current_beat_description=current_beat_desc,
        current_storyline_title=current_title,
        mission_types=mission_types,
        narration_context=body.narration_context or "",
    )
    if not decision or not decision.get("is_off_hook"):
        # Not off-hook OR classifier unavailable — let the caller fall back
        # to the normal creative-approach flow.
        return {
            "spawned": False,
            "reason": (decision or {}).get("reasoning") or "action fits the current scene",
            "is_off_hook": bool(decision and decision.get("is_off_hook")),
        }

    # --- OFF-HOOK: pause the current storyline + record pending obligations ---
    paused_obligation = None
    if current_storyline and current_storyline.get("status") == "active":
        paused_obligation = extract_pending_obligations_from_storyline(current_storyline)
        now = datetime.now(timezone.utc)
        await _storylines_collection().update_one(
            {"campaign_id": campaign_id, "id": current_storyline["id"]},
            {"$set": {
                "status": "paused",
                "paused_at": now,
                "paused_reason": "player_pivoted",
                "updated_at": now,
            }},
        )
        # Append to the campaign's pending_obligations list so lean_dm picks
        # it up across storylines.
        await _campaigns_collection().update_one(
            {"campaign_id": campaign_id},
            {"$push": {"pending_obligations": paused_obligation}},
        )

    # --- Resolve the chosen mission type blueprint (full doc) ---
    slug = decision.get("mission_type_slug") or ""
    mission_type = None
    if slug:
        mission_type = await get_mission_type_by_slug(
            _get_db(), slug=slug, campaign_id=campaign_id,
        )

    hook_text = decision.get("hook_text") or action
    hook_topic = decision.get("hook_topic") or action[:40]
    hook = {
        "id": f"hook_{uuid4().hex[:8]}",
        "text": hook_text,
        "topic": hook_topic,
        "verb_hint": "investigate",
    }

    # Ground the new scene in current cards so it shares NPC/place names.
    try:
        cards_cursor = _cards_collection().find(
            {"campaign_id": campaign_id, "status": {"$ne": "failed"}}, {"_id": 0}
        ).sort("updatedAt", -1).limit(20)
        recent_cards = await cards_cursor.to_list(length=20)
        campaign["_recent_cards"] = recent_cards
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"spawn: failed to load recent cards: {exc}")

    drafted = await draft_initial_scene(
        campaign=campaign,
        character=character,
        hook=hook,
        narration_context=body.narration_context or "",
        mission_type=mission_type,
    )

    now = datetime.now(timezone.utc)
    storyline_id = f"sl_{uuid4().hex[:10]}"
    first_beat = (drafted.get("beats") or [{}])[0]

    quest_card = KnowledgeCard(
        type="quest",
        title=drafted.get("title") or hook_topic or "New Thread",
        description=(
            f"{first_beat.get('description','')} (Active scene — "
            f"suggested {first_beat.get('check_type','Investigation')} DC {first_beat.get('dc',12)}.)"
        ),
        source="off-hook-spawn",
        confidence="high",
        tags=["quest", "active", "investigation", "storyline", "spawned"],
        status="active",
        updatedAt=now,
    )
    quest_doc = {**quest_card.model_dump(), "campaign_id": campaign_id, "storyline_id": storyline_id}
    await _cards_collection().insert_one(quest_doc)

    from services.storyline_service import _mission_type_snapshot
    mission_type_snapshot = _mission_type_snapshot(mission_type)

    storyline_doc = {
        "id": storyline_id,
        "campaign_id": campaign_id,
        "character_id": body.character_id,
        "title": drafted.get("title") or hook_topic or "New Thread",
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
        "mission_type": mission_type_snapshot,
        "spawned_from": {
            "trigger": "off_hook_player_action",
            "paused_storyline_id": current_storyline.get("id") if current_storyline else None,
            "player_action": action[:240],
            "reasoning": decision.get("reasoning"),
        },
        "created_at": now,
        "updated_at": now,
    }
    await _storylines_collection().insert_one(dict(storyline_doc))

    return {
        "spawned": True,
        "storyline": storyline_to_dict(storyline_doc),
        "quest_card_id": quest_card.id,
        "mission_type": mission_type_snapshot,
        "paused_storyline_id": current_storyline.get("id") if current_storyline else None,
        "paused_obligation": paused_obligation,
        "reasoning": decision.get("reasoning"),
    }



# -------------------- Paused-storyline resumption ruling --------------------
#
# The player cannot teleport back to a paused storyline — they must EARN
# the reconnect through plausible in-fiction action. The DM rules whether
# the thread is still recoverable based on real-time elapsed, mission
# urgency, and the player's stated approach.

class AttemptResumeBody(BaseModel):
    character_id: str
    player_action: str


@router.post("/{campaign_id}/storylines/{storyline_id}/attempt-resume")
async def attempt_resume_storyline(
    campaign_id: str, storyline_id: str, body: AttemptResumeBody
):
    action = (body.player_action or "").strip()
    if not action:
        raise HTTPException(status_code=400, detail="player_action is required")

    campaign = await _load_campaign(campaign_id)
    paused = await _storylines_collection().find_one(
        {"campaign_id": campaign_id, "id": storyline_id}, {"_id": 0}
    )
    if not paused:
        raise HTTPException(status_code=404, detail="Storyline not found")
    if paused.get("status") not in {"paused", "expired", "cold"}:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot resume a storyline with status '{paused.get('status')}'",
        )
    if paused.get("status") == "expired":
        raise HTTPException(
            status_code=409,
            detail="This thread has expired permanently — find a new lead via play.",
        )

    # Find the matching pending_obligation (carries urgency + paused_at).
    obligations: List[Dict] = list(campaign.get("pending_obligations") or [])
    obligation = next(
        (o for o in obligations if (o or {}).get("storyline_id") == storyline_id),
        None,
    )

    # Current clock hour, for the DM ruling.
    from services.time_service import get_world_clock
    clock_hour = get_world_clock(campaign)

    from services.storyline_resumption import rule_on_resume_attempt
    ruling = await rule_on_resume_attempt(
        paused_storyline=paused,
        pending_obligation=obligation,
        player_action=action,
        campaign_tone=(campaign.get("intent") or {}).get("tone", "Balanced"),
        clock_hour=clock_hour,
    )
    if not ruling:
        # Conservative fallback when the LLM is unavailable — keep the thread
        # cold so the player can try again without permanent damage.
        ruling = {
            "ruling": "cold",
            "narration": "The trail's gone quiet. You'll need to try a different angle.",
            "consequence": "No clear progress, but no door closed yet.",
            "new_lead": None,
            "reasoning": "llm unavailable",
            "hours_elapsed": 0,
            "urgency": (obligation or {}).get("urgency"),
        }

    now = datetime.now(timezone.utc)
    decision = ruling.get("ruling") or "cold"
    new_status_for_doc = "active" if decision == "active" else (
        "active" if decision == "cold" else "expired"
    )

    update_payload = {
        "status": new_status_for_doc,
        "updated_at": now,
        "last_resume_ruling": {
            "ruling": decision,
            "narration": ruling.get("narration"),
            "consequence": ruling.get("consequence"),
            "hours_elapsed": ruling.get("hours_elapsed"),
            "player_action": action[:240],
            "ruled_at": now.isoformat(),
        },
    }
    if decision == "expired":
        update_payload["expired_at"] = now
    await _storylines_collection().update_one(
        {"campaign_id": campaign_id, "id": storyline_id},
        {"$set": update_payload},
    )

    # If the DM gave the player a NEW lead while ruling expired, surface it
    # as a hook card so the player can engage it as a fresh storyline.
    new_lead_card_id = None
    new_lead = ruling.get("new_lead")
    if decision == "expired" and isinstance(new_lead, dict) and new_lead.get("hook_text"):
        lead_card = KnowledgeCard(
            type="rumor",
            title=new_lead.get("hook_topic") or "A New Angle",
            description=new_lead["hook_text"],
            source="resume-fallback-lead",
            confidence="medium",
            tags=["lead", "active", "fallback", "resumption"],
            status="active",
            updatedAt=now,
        )
        lead_doc = {
            **lead_card.model_dump(),
            "campaign_id": campaign_id,
            "spawned_from_storyline_id": storyline_id,
        }
        await _cards_collection().insert_one(lead_doc)
        new_lead_card_id = lead_card.id

    # Refresh the storyline doc to return its post-update state.
    refreshed = await _storylines_collection().find_one(
        {"campaign_id": campaign_id, "id": storyline_id}, {"_id": 0}
    ) or paused

    # Per product decision 3a — NPCs hold grudges permanently. We do NOT
    # remove the pending_obligation from the campaign on expiry. Storyline
    # status flips to 'expired'; the obligation entry stays so NPCs keep
    # reacting in lean_dm narration.

    return {
        "storyline": storyline_to_dict(refreshed),
        "ruling": ruling,
        "new_lead_card_id": new_lead_card_id,
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


async def _generate_npc_identity_sheet(
    *, name: str, role_snippet: str, campaign: Optional[Dict] = None
) -> Dict:
    """LLM-generate a HIDDEN NPC identity sheet so the DM can roleplay this
    NPC consistently across turns and the player can contest social DCs
    against grounded numbers. The sheet is stored on the card under
    `secret_content` and stays redacted from the player UI until specific
    fields are revealed in fiction.

    Sheet shape (each field independently revealable):
      stats: {ac, hp, intimidation_dc, persuasion_dc, deception_dc, insight_dc, passive_insight}
      personality: {trait, ideal, bond, flaw}
      background: short paragraph
      mannerisms: [list of 2-3 physical tics / habits]
      speech_style: short phrase ("clipped, eastern accent, drops r's")
      secrets: [1-3 hidden facts]
      allegiances: [factions/people they answer to]
      current_motivation: what they want from the player THIS scene
    """
    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key or not name:
        return {}
    realm = ((campaign or {}).get("world") or {}).get("world_core", {}).get("name", "the realm")
    starting = ((campaign or {}).get("world") or {}).get("startingLocation", {}).get("name", "the town")
    tone = ((campaign or {}).get("intent") or {}).get("tone", "balanced")
    danger = ((campaign or {}).get("intent") or {}).get("danger", "medium")
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        prompt = (
            f"Generate a HIDDEN NPC identity sheet for **{name}** based on the in-fiction "
            f"context below. The player has just learned this NPC's name; you are filling in "
            f"the personal details only the DM sees. Numbers should reflect a {tone} {danger}-"
            f"danger campaign.\n\n"
            f"=== CONTEXT (what's already known about this NPC) ===\n{role_snippet}\n\n"
            f"=== CAMPAIGN ===\nRealm: {realm} | Starting town: {starting}\n\n"
            "=== OUTPUT (strict JSON, no code fence) ===\n"
            "{\n"
            "  \"stats\": {\n"
            "    \"ac\": 12,\n"
            "    \"hp\": 18,\n"
            "    \"intimidation_dc\": 13,  // DC the PC must hit to intimidate them — fearful=10, brave=18\n"
            "    \"persuasion_dc\": 13,    // DC for talking them around\n"
            "    \"deception_dc\": 13,     // DC for lying to them (their Insight contest)\n"
            "    \"insight_dc\": 12,       // DC the PC must hit to read this NPC's lies\n"
            "    \"passive_insight\": 11   // their default 'lie-detector' threshold\n"
            "  },\n"
            "  \"personality\": {\n"
            "    \"trait\": \"single visible trait — 'twitchy when lying', 'never breaks eye contact'\",\n"
            "    \"ideal\": \"what they believe in (1 short clause)\",\n"
            "    \"bond\": \"who/what they care about (1 short clause)\",\n"
            "    \"flaw\": \"what trips them up (1 short clause)\"\n"
            "  },\n"
            "  \"background\": \"1-2 sentence backstory — where they came from, how they ended up here\",\n"
            "  \"mannerisms\": [\"physical tic 1\", \"speech tic 2\", \"body-language habit 3\"],\n"
            "  \"speech_style\": \"short descriptor — 'gravelly, clipped, drops r's' or 'sing-song southern lilt'\",\n"
            "  \"secrets\": [\"hidden fact 1 (something the NPC would never volunteer)\", \"hidden fact 2\"],\n"
            "  \"allegiances\": [\"named faction or person they actually answer to\"],\n"
            "  \"current_motivation\": \"what THIS NPC wants from the player THIS scene — not generic, scene-specific\"\n"
            "}\n"
            "Make the numbers playable (DCs 9-19). Make the personality and secrets "
            "specific and useful as roleplay anchors — never generic 'wants gold'."
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"npc-sheet-{uuid4()}",
            system_message=(
                "You are a senior D&D Dungeon Master statting a brand-new NPC. "
                "You produce concrete, playable, roleplay-ready sheets. Output "
                "strict JSON only."
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
        if not isinstance(data, dict):
            return {}
        return data
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"NPC sheet generation failed for {name}: {exc}")
        return {}


async def _mint_target_cards_if_revealed(
    *,
    campaign_id: str,
    storyline: Dict,
    beat: Dict,
    outcome: str,
) -> List[Dict]:
    """When a beat resolves with `passed` OR `skipped` (knowledge OR action —
    public reveals like reading a sign also reveal named entities, even when
    no roll was needed), auto-mint Knowledge Cards for each named entity in
    `beat.targets[]` (or fall back to extracting them from the description).
    NPCs become 'character' cards, locations become 'location' cards, factions
    become 'faction' cards. Skips entities the campaign already has a card for
    (case-insensitive type+title match) so we don't pollute the deck on
    every re-reveal.
    Returns the list of newly-minted card dicts.
    """
    # Mint on:
    #   - passed (any beat): the player earned the reveal
    #   - skipped (action beats with dc<=0 or roll_optional): the description
    #     was already public/visible, the player just confirmed they've read it.
    # Skipping a knowledge beat (which gates the description behind a roll)
    # should NOT mint targets — the player chose not to engage.
    if outcome == "skipped":
        if (beat.get("reveal_type") or "") == "knowledge":
            return []
        if int(beat.get("dc") or 0) > 0 and not beat.get("roll_optional"):
            return []
    elif outcome != "passed":
        return []
    revelation = (beat.get("description") or "").strip()
    # Creative approaches deposit new names ("Eliarin, an operative…") in
    # outcome_text, NOT description — so include that too when extracting
    # entities so the deck mints fresh contact cards from a successful gambit.
    outcome_text = (beat.get("outcome_text") or "").strip()
    extraction_text = (revelation + ("\n\n" + outcome_text if outcome_text else "")).strip()
    if not extraction_text:
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

    # ALWAYS run the LLM extractor on the FULL extraction_text (description +
    # outcome_text) so creative-approach names like "Eliarin" land in the
    # deck. Merge with explicit beat targets, dedup by case-insensitive
    # type+name match. This catches both fresh entities AND backfills when
    # beat.targets[] is empty.
    try:
        llm_targets = await _extract_targets_from_description_llm(extraction_text, max_targets=5)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"target extraction (LLM) failed: {exc}")
        llm_targets = []
    seen_pairs = {(t["type"], t["name"].lower()) for t in targets}
    for lt in llm_targets:
        key = (lt["type"], lt["name"].lower())
        if key not in seen_pairs:
            targets.append(lt)
            seen_pairs.add(key)

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

    # Pull the campaign once so the NPC sheet generator can use it.
    campaign_for_sheets: Optional[Dict] = None
    try:
        campaign_for_sheets = await _campaigns_collection().find_one(
            {"campaign_id": campaign_id}, {"_id": 0}
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"campaign load for NPC sheets failed: {exc}")

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
        snippet = _description_snippet_for(title, extraction_text, max_len=300)
        if not snippet:
            snippet = f"Mentioned during the {storyline_title}."

        # NPCs get a hidden identity sheet so the DM can roleplay them
        # consistently and the player can contest social DCs against grounded
        # numbers. The sheet stays redacted from the player UI until specific
        # fields are revealed in fiction.
        secret_content: Optional[Dict] = None
        revealed_fields: List[str] = ["title", "description"]  # what's already public
        if card_type == "character":
            try:
                secret_content = await _generate_npc_identity_sheet(
                    name=title,
                    role_snippet=snippet,
                    campaign=campaign_for_sheets,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"NPC sheet generation failed inline for {title}: {exc}")
                secret_content = None

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
                # Hidden DM-only sheet (NPC stats / mannerisms / secrets).
                # Frontend redacts everything except the keys in revealed_fields.
                "secret_content": secret_content or {},
                "revealed_fields": revealed_fields,
                # Newly-minted cards glow with a highlight border in the deck
                # library until the player hovers/opens them. The frontend
                # clears this flag via PATCH after first hover.
                "is_new": True,
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
    # Auto-mint Knowledge Cards for every named entity revealed (NPCs,
    # locations, factions). Fires on a clean PASS for any beat, OR on SKIP
    # for action beats whose description was already public (no roll gating).
    # Failed leads stay sealed.
    if body.outcome in {"passed", "skipped"}:
        try:
            target_cards = await _mint_target_cards_if_revealed(
                campaign_id=campaign_id,
                storyline=storyline,
                beat=cur_beat,
                outcome=body.outcome,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"target card mint failed (non-fatal): {exc}")

    # On a passed social check, uncloak the appropriate fields on the
    # target NPC's identity sheet (Insight → flaw+bond, Persuasion →
    # motive+ideal, Intimidation → secret_0+flaw, Deception → ideal,
    # Investigation → background+ac+hp, History → allegiances). Revealed
    # fields render un-redacted on the NPC card and become available to
    # the pitch judge as legitimate levers.
    npc_field_reveals: List[Dict] = []
    if body.outcome == "passed":
        try:
            npc_field_reveals = await _reveal_npc_fields_on_resolve(
                campaign_id=campaign_id,
                beat=cur_beat,
                outcome=body.outcome,
                storyline_title=storyline.get("title"),
                beat_title=cur_beat.get("title"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"NPC field reveal failed (non-fatal): {exc}")

    # Auto-checkpoint canon: on a successful pass, lock the beat in as a
    # canon scene the DM can never contradict.
    canon_scene: Optional[Dict] = None
    if body.outcome == "passed":
        try:
            from services.canon_scenes import checkpoint_passed_beat
            narration_snippet = await _latest_dm_narration(
                campaign_id, storyline.get("character_id")
            )
            canon_scene = await checkpoint_passed_beat(
                _get_db(),
                campaign_id=campaign_id,
                character_id=storyline.get("character_id"),
                storyline_id=storyline.get("id"),
                storyline_title=storyline.get("title"),
                beat=cur_beat,
                beat_index=current,
                outcome_text=body.outcome_text or "",
                roll_total=body.roll_total,
                narration_snippet=narration_snippet,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"canon checkpoint failed (non-fatal): {exc}")

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
        "npc_field_reveals": npc_field_reveals,
        "canon_scene": canon_scene,
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
    npc_field_reveals: List[Dict] = []
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
        # Same auto-reveal logic as the roll path — passed social check
        # uncloaks NPC sheet fields.
        try:
            npc_field_reveals = await _reveal_npc_fields_on_resolve(
                campaign_id=campaign_id,
                beat=cur_beat,
                outcome=storyline_outcome,
                storyline_title=storyline.get("title"),
                beat_title=cur_beat.get("title"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"NPC field reveal via creative failed: {exc}")

    # Auto-checkpoint canon for creative-path passes too.
    canon_scene: Optional[Dict] = None
    if storyline_outcome == "passed":
        try:
            from services.canon_scenes import checkpoint_passed_beat
            narration_snippet = await _latest_dm_narration(
                campaign_id, storyline.get("character_id")
            )
            canon_scene = await checkpoint_passed_beat(
                _get_db(),
                campaign_id=campaign_id,
                character_id=storyline.get("character_id"),
                storyline_id=storyline.get("id"),
                storyline_title=storyline.get("title"),
                beat=cur_beat,
                beat_index=current,
                outcome_text=f"Creative approach ({judged_outcome}): {narration}"[:400],
                roll_total=None,
                narration_snippet=narration_snippet or narration,
                creative_quality=judged_outcome,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"canon checkpoint via creative failed: {exc}")

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
        "npc_field_reveals": npc_field_reveals,
        "canon_scene": canon_scene,
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



@router.post("/{campaign_id}/cards/{card_id}/seen")
async def mark_card_seen(campaign_id: str, card_id: str):
    """Clear the `is_new` highlight from a card. Called by the deck UI on
    first hover so the new-card glow only shows until the player notices it.
    Idempotent — no-op for cards that were already seen.
    """
    res = await _cards_collection().update_one(
        {"campaign_id": campaign_id, "id": card_id, "is_new": True},
        {"$set": {"is_new": False}},
    )
    return {"ok": True, "cleared": bool(res.modified_count)}


@router.post("/{campaign_id}/cards/seen-all")
async def mark_all_cards_seen(campaign_id: str):
    """Bulk-clear all new-card highlights for a campaign — used by the
    'mark all read' button or when the player closes the deck library.
    """
    res = await _cards_collection().update_many(
        {"campaign_id": campaign_id, "is_new": True},
        {"$set": {"is_new": False}},
    )
    return {"ok": True, "cleared": int(res.modified_count)}



async def _latest_dm_narration(campaign_id: str, character_id: Optional[str]) -> str:
    """Best-effort fetch of the most recent DM narration text for canon
    distillation. Empty string on failure (canon falls back to outcome_text)."""
    if not character_id:
        return ""
    try:
        session_id = f"{campaign_id}:{character_id}"
        doc = await _get_db()["campaign_messages"].find_one(
            {"session_id": session_id, "role": "dm"},
            {"_id": 0, "content": 1},
            sort=[("timestamp", -1)],
        )
        return (doc or {}).get("content", "") or ""
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"latest DM narration fetch failed: {exc}")
        return ""


# ====================================================================
# DM FEEDBACK — players can contest a missed check or ask the DM why
# ====================================================================

class DMFeedbackBody(BaseModel):
    """Payload for the player flagging a DM ruling on a beat.

    kind:
      - 'missed_check'    : "you should have asked for X check"
      - 'why_no_check'    : "explain your reasoning"
      - 'wrong_check'     : "this is the wrong check / DC"
      - 'general'         : freeform
    """
    kind: str
    suggested_check: Optional[str] = None  # e.g. "Stealth", "Performance", "Intimidation"
    suggested_dc: Optional[int] = None     # 8-25, optional
    player_action: Optional[str] = None    # what the player actually tried to do
    note: Optional[str] = None             # freeform extra context
    beat_index: Optional[int] = None       # which beat the feedback is about
    apply_correction: bool = True          # if True and the judge agrees, retro-add a check beat


def _feedback_collection():
    return _get_db()["campaign_dm_feedback"]


async def _judge_dm_feedback(
    *,
    campaign: Dict,
    storyline: Dict,
    beat: Dict,
    feedback: DMFeedbackBody,
) -> Dict:
    """LLM judge that decides whether the player's complaint is valid and,
    if so, what corrective check the DM should have asked for. Returns:
      {
        "agrees_with_player": bool,
        "explanation": str,        # the DM's reasoning, in-character
        "should_correct": bool,    # True iff a retro check is justified
        "check_type": str | None,  # e.g. "Stealth"
        "dc": int | None,          # 8-20
        "dc_reasoning": str,       # one-line "why this DC"
      }
    """
    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "agrees_with_player": False,
            "explanation": "(DM judge unavailable — please retry shortly.)",
            "should_correct": False,
            "check_type": None,
            "dc": None,
            "dc_reasoning": "",
        }
    intent = campaign.get("intent") or {}
    realm = (campaign.get("world") or {}).get("world_core", {}).get("name", "the realm")
    sl_title = storyline.get("title") or "the scene"
    beat_title = beat.get("title") or "the beat"
    beat_desc = beat.get("description") or ""
    beat_outcome = beat.get("outcome_text") or ""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        prompt = (
            "You are an experienced D&D rules judge reviewing a DM ruling. The player "
            "is contesting a moment in the scene. Your job: decide if the player has a "
            "point, explain the reasoning clearly, and if a check IS warranted, name "
            "the right ability check and DC.\n\n"
            "=== CAMPAIGN ===\n"
            f"Realm: {realm} | Tone: {intent.get('tone','heroic')} | Danger: {intent.get('danger','medium')}\n\n"
            f"=== STORYLINE ===\n{sl_title}\n\n"
            f"=== BEAT ===\nTitle: {beat_title}\nDescription: {beat_desc[:600]}\n"
            f"What player did: {beat_outcome[:300]}\n\n"
            "=== PLAYER FEEDBACK ===\n"
            f"Type: {feedback.kind}\n"
            f"Player action they actually attempted: {feedback.player_action or '(not specified)'}\n"
            f"Suggested check: {feedback.suggested_check or '(none)'}\n"
            f"Suggested DC: {feedback.suggested_dc if feedback.suggested_dc is not None else '(none)'}\n"
            f"Note: {feedback.note or '(none)'}\n\n"
            "=== RULES OF THUMB (apply pragmatically — D&D 5e baseline) ===\n"
            "- Hidden / unobserved physical action attempting NOT to be seen → STEALTH "
            "(against passive Perception of observers, or DC 13-15 in moderate cover).\n"
            "- Distracting / luring / acting a part to mislead → DECEPTION (vs target's "
            "passive Insight) or PERFORMANCE if it's a public ruse.\n"
            "- Threatening, weapon-drawn intimidation → INTIMIDATION (vs target's social DC).\n"
            "- Persuading, pleading, charming → PERSUASION.\n"
            "- Reading body language / catching lies → INSIGHT.\n"
            "- Climbing, jumping, breaking grapple → ATHLETICS (or ACROBATICS for finesse).\n"
            "- Spotting hidden things → PERCEPTION (passive first; active only if searching).\n"
            "- Recalling lore → ARCANA / HISTORY / NATURE / RELIGION as appropriate.\n"
            "- A check is NOT needed when the action is automatic (reading a public sign, "
            "  walking down a street, asking the price), or when failure has no meaningful "
            "  consequence.\n"
            "- If the player tried something with stealth/deception cues AND there were "
            "  in-fiction observers (NPC eyes on them, guards in earshot, a target they're "
            "  trying to fool), the DM SHOULD have asked for the corresponding check.\n\n"
            "=== OUTPUT (strict JSON, no code fence) ===\n"
            "{\n"
            "  \"agrees_with_player\": true|false,\n"
            "  \"explanation\": \"1-3 sentence DM explanation. If you agree, name the rule. If you disagree, explain why no check was needed (e.g. action was automatic, or no observer existed).\",\n"
            "  \"should_correct\": true|false,  // true iff a retro check beat is justified\n"
            "  \"check_type\": \"Stealth|Deception|Performance|Intimidation|Persuasion|Insight|Athletics|Acrobatics|Perception|Investigation|Sleight of Hand|Arcana|History|Nature|Religion|Survival|null\",\n"
            "  \"dc\": 12,    // 8-20, null if no check\n"
            "  \"dc_reasoning\": \"one-line: why this DC (e.g. 'moderate cover, distracted target')\"\n"
            "}"
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"dm-feedback-{uuid4()}",
            system_message=(
                "You are a fair, experienced D&D rules judge. You side with the player "
                "when the rules support them and explain clearly. Output strict JSON only."
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
        if not isinstance(data, dict):
            return {
                "agrees_with_player": False,
                "explanation": "(Judge returned malformed output — please retry.)",
                "should_correct": False,
                "check_type": None,
                "dc": None,
                "dc_reasoning": "",
            }
        # Normalize
        ct = data.get("check_type")
        if ct and str(ct).strip().lower() == "null":
            ct = None
        try:
            dc_val = int(data.get("dc")) if data.get("dc") is not None else None
            if dc_val is not None:
                dc_val = max(8, min(20, dc_val))
        except Exception:
            dc_val = None
        return {
            "agrees_with_player": bool(data.get("agrees_with_player")),
            "explanation": (data.get("explanation") or "").strip()[:700],
            "should_correct": bool(data.get("should_correct")),
            "check_type": ct,
            "dc": dc_val,
            "dc_reasoning": (data.get("dc_reasoning") or "").strip()[:200],
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"DM feedback judge failed: {exc}")
        return {
            "agrees_with_player": False,
            "explanation": f"(Judge errored: {exc}.)",
            "should_correct": False,
            "check_type": None,
            "dc": None,
            "dc_reasoning": "",
        }


@router.post("/{campaign_id}/storylines/{storyline_id}/dm-feedback")
async def submit_dm_feedback(campaign_id: str, storyline_id: str, body: DMFeedbackBody):
    """Player contests / queries a DM ruling on a beat. Returns the DM's
    explanation; if a corrective check is justified AND `apply_correction`
    is true, optionally appends a corrective check beat and persists the
    feedback so future DM prompts can learn from it.
    """
    sl = await _storylines_collection().find_one(
        {"campaign_id": campaign_id, "id": storyline_id}, {"_id": 0}
    )
    if not sl:
        raise HTTPException(status_code=404, detail="Storyline not found")

    beats = sl.get("beats") or []
    if not beats:
        raise HTTPException(status_code=400, detail="Storyline has no beats")

    # Default to the most recently resolved beat if no index given.
    idx = body.beat_index
    if idx is None or idx < 0 or idx >= len(beats):
        # Find the latest beat that has any outcome the player could contest.
        idx = max(
            (i for i, b in enumerate(beats) if (b.get("outcome_text") or b.get("status") in {"passed", "failed", "skipped"})),
            default=len(beats) - 1,
        )
    beat = beats[idx]

    campaign = await _load_campaign(campaign_id)
    judgment = await _judge_dm_feedback(
        campaign=campaign, storyline=sl, beat=beat, feedback=body
    )

    # Persist the feedback so future DM prompts can pull recent corrections.
    now = datetime.now(timezone.utc)
    record = {
        "id": f"fb_{uuid4().hex[:10]}",
        "campaign_id": campaign_id,
        "storyline_id": storyline_id,
        "beat_index": idx,
        "beat_title": beat.get("title"),
        "kind": body.kind,
        "suggested_check": body.suggested_check,
        "suggested_dc": body.suggested_dc,
        "player_action": body.player_action,
        "note": body.note,
        "judge": judgment,
        "created_at": now,
    }
    try:
        await _feedback_collection().insert_one(dict(record))
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"feedback persist failed: {exc}")
    record_out = {k: v for k, v in record.items() if k != "_id"}
    if isinstance(record_out.get("created_at"), datetime):
        record_out["created_at"] = record_out["created_at"].isoformat()

    # Distill this feedback into a persistent DM Lesson so the DM Notebook
    # accumulates rule corrections + DC calibrations across turns. Non-fatal.
    distilled_lesson: Optional[Dict] = None
    try:
        from services.dm_lessons import (
            distill_lesson_from_feedback,
            merge_or_create_lesson,
        )
        partial = await distill_lesson_from_feedback(
            feedback=body.model_dump(), judgment=judgment
        )
        if partial:
            stored = await merge_or_create_lesson(
                _get_db(),
                campaign_id=campaign_id,
                character_id=sl.get("character_id"),
                lesson=partial,
                source_ref={
                    "feedback_id": record["id"],
                    "storyline_id": storyline_id,
                    "beat_title": beat.get("title"),
                },
            )
            distilled_lesson = {
                k: v for k, v in stored.items() if k != "_id"
            }
            for k in ("created_at", "updated_at", "last_applied_at"):
                v = distilled_lesson.get(k)
                if isinstance(v, datetime):
                    distilled_lesson[k] = v.isoformat()
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"DM lesson distill failed (non-fatal): {exc}")

    # If the judge agrees AND a correction is warranted AND the player asked
    # us to apply it, append a corrective check beat so the player can
    # actually roll for what they tried to do.
    correction_beat: Optional[Dict] = None
    rewind_target: Optional[Dict] = None
    if (
        body.apply_correction
        and judgment.get("should_correct")
        and judgment.get("check_type")
        and judgment.get("dc")
    ):
        # Identify which canon scene we're rewinding from — the most recent
        # canon scene preceding the contested beat. The DM is told to step
        # back to it so the retroactive check feels diegetic, not a
        # mechanical undo.
        try:
            from services.canon_scenes import find_rewind_target
            rewind_target = await find_rewind_target(
                _get_db(),
                campaign_id=campaign_id,
                before_beat_index=idx,
                storyline_id=storyline_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"rewind target lookup failed: {exc}")

        rewind_chip = ""
        if rewind_target:
            rewind_chip = (
                f" The DM rewinds to "
                f"Scene {rewind_target.get('scene_number')} — "
                f"'{rewind_target.get('title')}' — and replays from canon."
            )

        correction_beat = {
            "title": f"Retroactive {judgment['check_type']} check",
            "description": (
                f"You called out the missed beat: '{(body.player_action or 'your stated approach')[:140]}'. "
                f"The DM agrees and rewinds — roll {judgment['check_type']} (DC {judgment['dc']}) to "
                f"resolve what you actually attempted. "
                f"({judgment.get('dc_reasoning','')})"
                f"{rewind_chip}"
            ).strip(),
            "task": f"Roll {judgment['check_type']} (DC {judgment['dc']})",
            "check_type": judgment["check_type"],
            "dc": int(judgment["dc"]),
            "ability": _ability_for_check(judgment["check_type"]),
            "reveal_type": "action",
            "prompt": "",
            "targets": [],
            "status": "active",
            "outcome_text": None,
            "roll_optional": False,
            "from_dm_feedback": True,
            "rewind_to_scene_id": rewind_target.get("id") if rewind_target else None,
            "rewind_to_scene_number": rewind_target.get("scene_number") if rewind_target else None,
        }
        beats.append(correction_beat)
        new_idx = len(beats) - 1
        await _storylines_collection().update_one(
            {"campaign_id": campaign_id, "id": storyline_id},
            {"$set": {"beats": beats, "current_beat": new_idx}},
        )
        sl["beats"] = beats
        sl["current_beat"] = new_idx

    return {
        "ok": True,
        "judgment": judgment,
        "feedback_record": record_out,
        "correction_applied": bool(correction_beat),
        "lesson": distilled_lesson,
        "rewind_target": rewind_target,
        "storyline": storyline_to_dict(sl),
    }


def _ability_for_check(check: str) -> str:
    """Map check type to its governing ability (used so the corrective
    beat can be auto-rolled with the right modifier)."""
    m = {
        "Stealth": "dex", "Sleight of Hand": "dex", "Acrobatics": "dex",
        "Athletics": "str",
        "Perception": "wis", "Insight": "wis", "Survival": "wis",
        "Animal Handling": "wis", "Medicine": "wis",
        "Persuasion": "cha", "Deception": "cha", "Intimidation": "cha",
        "Performance": "cha",
        "Investigation": "int", "Arcana": "int", "History": "int",
        "Nature": "int", "Religion": "int",
    }
    return m.get(check, "wis")



# Map: which check, when passed against an NPC, reveals which fields on
# their identity sheet. The values are written into the NPC card's
# `revealed_fields` array; the frontend NPCIdentityPanel re-renders those
# fields un-redacted, and `_judge_pitch_quality` lets the player leverage
# them in pitches.
_CHECK_REVEALS_NPC_FIELDS: Dict[str, List[str]] = {
    # Reading body language → see what they care about and what trips them
    "Insight": ["personality.flaw", "personality.bond", "speech_style", "mannerisms"],
    # Convincing them — you learn what they actually want from this scene
    "Persuasion": ["current_motivation", "personality.ideal"],
    # Intimidation → they crack and one buried secret slips
    "Intimidation": ["secret_0", "personality.flaw"],
    # Successfully fooling them shows you read them well — their ideal
    "Deception": ["personality.ideal", "passive_insight"],
    # Investigation around / about them — backstory + stats glimpse
    "Investigation": ["background", "stats.ac", "stats.hp"],
    # History / lore — their allegiances are public knowledge if you know
    "History": ["allegiances"],
}


async def _reveal_npc_fields_on_resolve(
    *,
    campaign_id: str,
    beat: Dict,
    outcome: str,
    storyline_title: Optional[str] = None,
    beat_title: Optional[str] = None,
) -> List[Dict]:
    """When a social check passes against a named NPC, append the appropriate
    fields to that NPC's `revealed_fields` array so the player sees their
    identity sheet uncloak in real time. Also appends a Discovery Log entry
    per field so the player can see WHEN and HOW each piece was uncovered.
    Returns the list of NPC card patches
    `[{title, newly_revealed: [...], log_entries: [...]}, ...]` so the
    frontend can highlight the fresh info.
    """
    if outcome != "passed":
        return []
    check = beat.get("check_type")
    fields = _CHECK_REVEALS_NPC_FIELDS.get(check) or []
    if not fields:
        return []

    # NPC targets on the beat — these are the people the check actually
    # acted upon. We unmask each one.
    npc_names: List[str] = []
    for t in (beat.get("targets") or []):
        if not isinstance(t, dict):
            continue
        if (t.get("type") or "").lower() not in {"npc", "character"}:
            continue
        nm = (t.get("name") or "").strip()
        if nm:
            npc_names.append(nm)
    if not npc_names:
        return []

    patches: List[Dict] = []
    coll = _cards_collection()
    now = datetime.now(timezone.utc)
    sl_title = storyline_title or "(unknown scene)"
    b_title = beat_title or beat.get("title") or "(beat)"

    for nm in npc_names[:3]:
        card = await coll.find_one(
            {"campaign_id": campaign_id, "type": "character", "title": nm},
            {"_id": 0},
        )
        if not card:
            continue
        existing = set(card.get("revealed_fields") or ["title", "description"])
        secret = card.get("secret_content") or {}
        # Skip fields the NPC doesn't actually have data for — no point
        # revealing an empty 'allegiances' list.
        newly: List[str] = []
        for f in fields:
            if f in existing:
                continue
            # Validate the path actually has data
            if f.startswith("personality."):
                key = f.split(".", 1)[1]
                if (secret.get("personality") or {}).get(key):
                    newly.append(f)
            elif f.startswith("stats."):
                key = f.split(".", 1)[1]
                if (secret.get("stats") or {}).get(key) is not None:
                    newly.append(f)
            elif f == "secret_0":
                if (secret.get("secrets") or [None])[0]:
                    newly.append(f)
            elif f == "secret_1":
                if len(secret.get("secrets") or []) > 1 and secret["secrets"][1]:
                    newly.append(f)
            else:
                if secret.get(f):
                    newly.append(f)
        if not newly:
            continue
        merged = sorted(existing.union(newly))
        # Build Discovery Log entries — one per newly-revealed field — so
        # the player can later trace exactly when and how each piece of
        # intel was uncovered.
        log_entries = [
            {
                "field": f,
                "check_type": check,
                "storyline_title": sl_title,
                "beat_title": b_title,
                "at": now.isoformat(),
            }
            for f in newly
        ]
        await coll.update_one(
            {"campaign_id": campaign_id, "type": "character", "title": nm},
            {
                "$set": {"revealed_fields": merged, "is_new": True},
                "$push": {"discovery_log": {"$each": log_entries}},
            },
        )
        patches.append({
            "title": nm,
            "newly_revealed": newly,
            "log_entries": log_entries,
        })
    return patches




class AdjustDCBody(BaseModel):
    """Player tells the DM what they actually say/do for a social check.
    The DM evaluates pitch quality vs the NPC's personality + scene context
    and returns an adjusted DC with a rationale. The roll happens after,
    against the adjusted DC.
    """
    beat_index: int
    approach_text: str


async def _judge_pitch_quality(
    *,
    campaign: Dict,
    storyline: Dict,
    beat: Dict,
    approach_text: str,
    npc_card: Optional[Dict] = None,
) -> Dict:
    """LLM judge: evaluates the player's pitch and returns a DC modifier
    in the range -5..+8 from the beat's base DC, plus a one-line rationale.
    Smart, in-character, well-targeted offers REDUCE the DC; insulting,
    blunt, or off-target attempts RAISE it.
    """
    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    base_dc = int(beat.get("dc") or 12)
    check_type = beat.get("check_type") or "Persuasion"

    if not api_key:
        return {
            "modifier": 0,
            "adjusted_dc": base_dc,
            "rationale": "Judge offline — DC unchanged.",
            "quality": "neutral",
        }

    intent = campaign.get("intent") or {}
    realm = (campaign.get("world") or {}).get("world_core", {}).get("name", "the realm")

    # NPC context — voice, ideal, flaw, motive — so the judge knows what
    # would actually move THIS person. ONLY fields the player has REVEALED
    # in-game count: knowing the NPC's bond (e.g. via Insight) unlocks the
    # brilliant-pitch band; without it the judge plays blind and the player
    # can only neutral-pitch their way through. This makes in-fiction intel
    # mechanically rewarding.
    npc_block = ""
    if npc_card and isinstance(npc_card.get("secret_content"), dict):
        sc = npc_card["secret_content"]
        revealed = set(npc_card.get("revealed_fields") or ["title", "description"])
        pers = sc.get("personality", {})

        def _show(key: str, value: str) -> str:
            """Render a field as either its real value or a hidden marker
            so the judge knows it CANNOT factor that lever in."""
            if key in revealed and value:
                return str(value)
            return "[hidden — player has not learned this]"

        npc_block = (
            f"NPC TARGET: {npc_card.get('title','an NPC')}\n"
            f"  voice: {_show('speech_style', sc.get('speech_style','plain'))}\n"
            f"  trait: {_show('personality.trait', pers.get('trait',''))}\n"
            f"  ideal: {_show('personality.ideal', pers.get('ideal',''))}\n"
            f"  bond:  {_show('personality.bond', pers.get('bond',''))}\n"
            f"  flaw:  {_show('personality.flaw', pers.get('flaw',''))}\n"
            f"  motive THIS scene: {_show('current_motivation', sc.get('current_motivation',''))}\n"
            "(Hidden levers EXIST but the player does not know them. You may NOT "
            "reward a pitch that 'happens to' target a hidden lever — only credit "
            "pitches that target levers marked above, OR generic angles. If the "
            "pitch coincidentally hits a hidden lever, rate it on its surface "
            "merits only — call it 'lucky' in the rationale.)"
        )
    else:
        npc_block = "NPC TARGET: an NPC the player is trying to influence (no detailed sheet on file).\n"

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        prompt = (
            f"You are an experienced D&D Dungeon Master sizing up the player's PITCH "
            f"before they roll a {check_type} check. Your job: rate the quality of what "
            f"they actually said/did and adjust the base DC accordingly. Smart, "
            f"in-character, well-targeted approaches REDUCE the DC. Insulting, blunt, "
            f"clueless, or off-target attempts RAISE the DC. Be a fair table DM, not a "
            f"pushover.\n\n"
            f"=== CAMPAIGN ===\n"
            f"Realm: {realm} | Tone: {intent.get('tone','heroic')}\n\n"
            f"=== STORYLINE & BEAT ===\n"
            f"Storyline: {storyline.get('title','the scene')}\n"
            f"Beat: {beat.get('title','')} — base DC {base_dc}\n"
            f"Beat description: {(beat.get('description') or '')[:400]}\n"
            f"Check: {check_type}\n\n"
            f"=== {npc_block}\n"
            f"=== PLAYER'S PITCH (what they actually say/do) ===\n"
            f'"{approach_text}"\n\n'
            "=== QUALITY RUBRIC ===\n"
            "  brilliant   (modifier -5 to -3): targets the NPC's bond/flaw exactly, "
            "                                   in-character, leverages a real lever\n"
            "  smart       (modifier -3 to -1): reasonable angle, decent framing, plays "
            "                                   to NPC's interests\n"
            "  neutral     (modifier  0 to +1): generic approach, neither aided nor hurt\n"
            "  weak        (modifier +2 to +4): blunt, generic, ignores NPC traits, "
            "                                   slightly off-tone\n"
            "  foolish     (modifier +5 to +8): insulting, threatening when persuading, "
            "                                   contradicts NPC values, calls them stupid\n\n"
            "Output strict JSON, no code fence:\n"
            "{\n"
            "  \"modifier\": -3,           // integer -5..+8\n"
            "  \"adjusted_dc\": 10,        // base + modifier, clamped 5..25\n"
            "  \"rationale\": \"one short sentence — why this modifier (cite a specific element of the pitch)\",\n"
            "  \"quality\": \"brilliant|smart|neutral|weak|foolish\"\n"
            "}"
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"dc-adjust-{uuid4()}",
            system_message=(
                "You are a fair, experienced D&D Dungeon Master. You reward smart play "
                "with lower DCs and punish dumb play with higher DCs — never zero, never "
                "auto-success. Output strict JSON only."
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
        if not isinstance(data, dict):
            return {
                "modifier": 0,
                "adjusted_dc": base_dc,
                "rationale": "Judge returned malformed output — DC unchanged.",
                "quality": "neutral",
            }
        try:
            mod = int(data.get("modifier", 0))
        except Exception:
            mod = 0
        mod = max(-5, min(8, mod))
        adjusted = max(5, min(25, base_dc + mod))
        return {
            "modifier": mod,
            "adjusted_dc": adjusted,
            "rationale": (data.get("rationale") or "").strip()[:240],
            "quality": (data.get("quality") or "neutral").strip().lower()[:16],
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"pitch judge failed: {exc}")
        return {
            "modifier": 0,
            "adjusted_dc": base_dc,
            "rationale": f"Judge errored: {exc}",
            "quality": "neutral",
        }


@router.post("/{campaign_id}/storylines/{storyline_id}/adjust-dc")
async def adjust_beat_dc(campaign_id: str, storyline_id: str, body: AdjustDCBody):
    """Player tells the DM what they say/do; DM evaluates and returns the
    DC modifier + adjusted DC. The storyline beat is updated in place so
    subsequent rolls happen against the adjusted DC. Idempotent in spirit:
    submitting a new pitch overwrites the prior adjustment (player can
    revise their pitch up until they actually roll).
    """
    text = (body.approach_text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="approach_text is required")
    if len(text) < 8:
        raise HTTPException(status_code=400, detail="Pitch is too short — say more.")

    sl = await _storylines_collection().find_one(
        {"campaign_id": campaign_id, "id": storyline_id}, {"_id": 0}
    )
    if not sl:
        raise HTTPException(status_code=404, detail="Storyline not found")
    beats = sl.get("beats") or []
    if body.beat_index < 0 or body.beat_index >= len(beats):
        raise HTTPException(status_code=400, detail="beat_index out of range")
    beat = beats[body.beat_index]

    # Snapshot the original base DC ONCE (so revising the pitch always
    # adjusts from the truth, not from a prior adjustment).
    if "base_dc" not in beat:
        beat["base_dc"] = int(beat.get("dc") or 12)
    base_dc = int(beat["base_dc"])
    beat["dc"] = base_dc  # reset before recompute

    campaign = await _load_campaign(campaign_id)

    # Try to find the NPC card the player is talking to — pull from beat.targets[]
    # first (most reliable), fall back to scanning the description.
    npc_card: Optional[Dict] = None
    target_npc_name: Optional[str] = None
    for t in (beat.get("targets") or []):
        if isinstance(t, dict) and (t.get("type") or "").lower() in {"npc", "character"}:
            target_npc_name = (t.get("name") or "").strip()
            break
    if target_npc_name:
        npc_card = await _cards_collection().find_one(
            {
                "campaign_id": campaign_id,
                "type": "character",
                "title": target_npc_name,
            },
            {"_id": 0},
        )

    judgment = await _judge_pitch_quality(
        campaign=campaign,
        storyline=sl,
        beat=beat,
        approach_text=text,
        npc_card=npc_card,
    )

    # Stamp the adjustment onto the beat so the UI can render it AND so
    # downstream resolve calls roll against the adjusted DC. We also keep
    # the player's pitch on the beat as `pitch_text` for the next-scene
    # prompt to weave in naturally.
    beat["dc"] = int(judgment["adjusted_dc"])
    beat["dc_adjustment"] = {
        "base_dc": base_dc,
        "modifier": int(judgment["modifier"]),
        "adjusted_dc": int(judgment["adjusted_dc"]),
        "quality": judgment["quality"],
        "rationale": judgment["rationale"],
        "pitch_text": text[:600],
    }
    beat["pitch_text"] = text[:600]
    beats[body.beat_index] = beat

    await _storylines_collection().update_one(
        {"campaign_id": campaign_id, "id": storyline_id},
        {"$set": {"beats": beats}},
    )
    sl["beats"] = beats
    return {
        "ok": True,
        "judgment": judgment,
        "storyline": storyline_to_dict(sl),
    }
