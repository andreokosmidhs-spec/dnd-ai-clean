"""Lean DM endpoint for the V2 campaign flow.

Consumes campaigns (campaigns.py), V2 characters (characters_v2), and knowledge
cards (campaign_log_cards) — no dependency on the legacy dungeon_forge world_state
pipeline. Uses emergentintegrations + gpt-4o-mini for narration.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaigns", tags=["lean_dm"])

# Database injected by server.py
_db = None


def set_database(db):
    global _db
    _db = db


def get_db():
    return _db


_MAX_HISTORY = 10
_MESSAGES_COLLECTION = "campaign_messages"


class LeanDMRequest(BaseModel):
    character_id: str
    player_action: str
    check_result: Optional[dict] = None
    client_target_id: Optional[str] = None


def _format_title(s: str) -> str:
    return str(s or "").replace("_", " ").strip().title()


def _build_system_prompt(campaign: dict, character: dict, cards: List[dict]) -> str:
    intent = campaign.get("intent") or {}
    world = campaign.get("world") or {}
    starting = world.get("startingLocation") or {}

    identity = character.get("identity") or {}
    race = character.get("race") or {}
    class_ = character.get("class") or {}
    bg = character.get("background") or {}
    abilities = character.get("abilityScores") or {}

    card_summaries: List[str] = []
    for c in cards[:12]:
        title = c.get("title") or ""
        content = (c.get("content") or "")[:140]
        ctype = c.get("type") or "lore"
        if title:
            card_summaries.append(f"- [{ctype}] {title}: {content}")

    card_block = "\n".join(card_summaries) if card_summaries else "(no active cards)"

    return (
        "You are the Dungeon Master for a Dungeons & Dragons 5e campaign. You narrate outcomes "
        "of the player's actions in vivid second-person prose.\n\n"
        "=== CAMPAIGN ===\n"
        f"Tone: {intent.get('tone', 'heroic')} | Focus: {intent.get('focus', 'mixed')} | "
        f"Scope: {intent.get('scope', 'local')} | Danger: {intent.get('danger', 'medium')}\n"
        f"World theme: {world.get('theme', 'mixed')} | World tone: {world.get('tone', 'mixed')}\n"
        f"Starting location: {starting.get('name', 'Unknown')} — {starting.get('description', '')}\n\n"
        "=== HERO ===\n"
        f"Name: {identity.get('name', 'The Adventurer')}\n"
        f"Race: {_format_title(race.get('key'))} | Class: {_format_title(class_.get('key'))} "
        f"(Level {class_.get('level', 1)}) | Background: {_format_title(bg.get('key'))}\n"
        f"Abilities: STR {abilities.get('str', 10)}, DEX {abilities.get('dex', 10)}, "
        f"CON {abilities.get('con', 10)}, INT {abilities.get('int', 10)}, "
        f"WIS {abilities.get('wis', 10)}, CHA {abilities.get('cha', 10)}\n\n"
        "=== ACTIVE KNOWLEDGE CARDS ===\n"
        f"{card_block}\n\n"
        "=== DM GUIDELINES ===\n"
        "- Respond in 80-160 words, one to two paragraphs, second-person narration.\n"
        "- Be concrete and sensory; advance the scene with each reply.\n"
        "- Respect the campaign tone; don't slip into cartoonish humor in a dark campaign.\n"
        "- If the action requires a check, describe the outcome naturally; don't ask for rolls.\n"
        "- End with a subtle hook or an open invitation for the player's next action.\n"
        "- Never produce headings, bullet lists, OOC commentary, or stats."
    )


async def _load_recent_messages(db, session_id: str) -> List[dict]:
    if db is None:
        return []
    cursor = (
        db[_MESSAGES_COLLECTION]
        .find({"session_id": session_id}, {"_id": 0})
        .sort("timestamp", -1)
        .limit(_MAX_HISTORY)
    )
    docs = await cursor.to_list(length=_MAX_HISTORY)
    docs.reverse()
    return docs


@router.post("/{campaign_id}/dm/action")
async def dm_action(campaign_id: str, req: LeanDMRequest):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    # Load campaign
    campaign = await db.campaigns.find_one({"campaign_id": campaign_id}) or await db.campaigns.find_one({"id": campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign not found: {campaign_id}")

    # Load V2 character
    try:
        char_obj_id = ObjectId(req.character_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid character_id: {exc}") from exc
    character = await db.characters_v2.find_one({"_id": char_obj_id})
    if not character:
        raise HTTPException(status_code=404, detail=f"Character not found: {req.character_id}")

    # Load active knowledge cards
    cards_cursor = db.campaign_log_cards.find(
        {"campaign_id": campaign_id}, {"_id": 0}
    ).sort("created_at", -1).limit(20)
    cards = await cards_cursor.to_list(length=20)

    # Load recent message history (session = campaign + character)
    session_id = f"{campaign_id}:{req.character_id}"
    history = await _load_recent_messages(db, session_id)

    # Build LLM prompt
    system_prompt = _build_system_prompt(campaign, character, cards)

    # Call the LLM
    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="LLM key not configured")

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=system_prompt,
        )
        chat.with_model("openai", "gpt-4o-mini")

        # Fold previous history into a single context prefix to keep latency low
        history_block = ""
        if history:
            lines: List[str] = []
            for m in history[-_MAX_HISTORY:]:
                role = m.get("role") or "user"
                text = (m.get("content") or "").strip()
                if not text:
                    continue
                lines.append(f"{role.upper()}: {text}")
            if lines:
                history_block = "Recent events:\n" + "\n".join(lines) + "\n\n"

        check_note = ""
        if req.check_result:
            check_note = f"\n[Check result context: {req.check_result}]\n"

        user_msg = (
            f"{history_block}"
            f"Player action: {req.player_action}{check_note}\n"
            f"Narrate the next beat."
        )

        narration = (await chat.send_message(UserMessage(text=user_msg))).strip()
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Lean DM LLM call failed: {exc}")
        raise HTTPException(status_code=502, detail=f"DM generation failed: {exc}") from exc

    now = datetime.now(timezone.utc)
    try:
        await db[_MESSAGES_COLLECTION].insert_many(
            [
                {
                    "session_id": session_id,
                    "campaign_id": campaign_id,
                    "character_id": req.character_id,
                    "role": "player",
                    "content": req.player_action,
                    "timestamp": now.isoformat(),
                },
                {
                    "session_id": session_id,
                    "campaign_id": campaign_id,
                    "character_id": req.character_id,
                    "role": "dm",
                    "content": narration,
                    "timestamp": now.isoformat(),
                },
            ]
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to persist messages (non-fatal): {exc}")

    # Return a response shape that's compatible with AdventureLogWithDM
    return {
        "success": True,
        "data": {
            "narration": narration,
            "entity_mentions": [],
            "world_state_update": {},
            "player_updates": {},
            "options": [],
        },
    }
