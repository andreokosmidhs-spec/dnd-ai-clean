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

# Class flavor — mirrors campaign_service._CLASS_FLAVOR. Kept local to avoid
# a cross-module import and to let the DM prompt evolve independently.
_CLASS_FLAVOR = {
    "barbarian": "visceral, physical, raw — heartbeat, breath, primal instinct",
    "bard": "performative, attuned to rumor, social undercurrents, rhythm",
    "cleric": "reverent, disciplined; the divine is quiet pressure, not constant miracle",
    "druid": "rooted in weather, animal signs, the smell of earth",
    "fighter": "practical — reads terrain, weapons, exits, threats",
    "monk": "spare, precise, attentive to breath, balance, stillness",
    "paladin": "oath-bound; moral weight colors every scene",
    "ranger": "tracker's eye — prints, broken twigs, wind, animal silence",
    "rogue": "shadows, sightlines, locks, pockets; always reads the room",
    "sorcerer": "magic in the blood; subtle currents, flickers of the uncanny",
    "warlock": "a patron's presence lurks at the edge; whispered debts",
    "wizard": "cerebral, analytical; arcane patterns and cataloged observation",
    "artificer": "tinker's eye — materials, mechanisms, improvisation",
    "_default": "grounded, observant, driven by the hero's own reasons",
}


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
    appearance = character.get("appearance") or {}

    hero_name = identity.get("name", "The Adventurer")
    class_key = (class_.get("key") or "adventurer").lower()
    class_name = _format_title(class_key)
    race_name = _format_title(race.get("key"))
    bg_name = _format_title(bg.get("key"))
    class_flavor = _CLASS_FLAVOR.get(class_key, _CLASS_FLAVOR["_default"])

    appearance_bits: List[str] = []
    if appearance.get("build"):
        appearance_bits.append(f"{appearance['build']} build")
    if appearance.get("hairColor"):
        appearance_bits.append(f"{appearance['hairColor']} hair")
    if appearance.get("eyeColor"):
        appearance_bits.append(f"{appearance['eyeColor']} eyes")
    notable = appearance.get("notableFeatures") or []
    if notable:
        appearance_bits.append("notable: " + ", ".join(notable[:3]))
    appearance_line = "; ".join(appearance_bits) if appearance_bits else "unremarkable at first glance"

    card_summaries: List[str] = []
    for c in cards[:12]:
        title = c.get("title") or ""
        content = (c.get("content") or c.get("description") or "")[:140]
        ctype = c.get("type") or "lore"
        if title:
            card_summaries.append(f"- [{ctype}] {title}: {content}")
    card_block = "\n".join(card_summaries) if card_summaries else "(no active cards — rely on campaign context)"

    tone = intent.get("tone", "heroic")

    return (
        "You are the Dungeon Master for a Dungeons & Dragons 5e campaign. You narrate outcomes "
        "of the player's actions in grounded, cinematic second-person prose. You PERSONALIZE every "
        "reply to this specific hero and the established campaign context. You never produce "
        "generic fantasy filler.\n\n"
        "=== CAMPAIGN ===\n"
        f"Tone: {tone} | Focus: {intent.get('focus', 'mixed')} | "
        f"Scope: {intent.get('scope', 'local')} | Danger: {intent.get('danger', 'medium')}\n"
        f"World theme: {world.get('theme', 'mixed')} | World tone: {world.get('tone', 'mixed')}\n"
        f"Starting location: {starting.get('name', 'Unknown')} — {starting.get('description', '')}\n\n"
        "=== HERO ===\n"
        f"Name: {hero_name} (address them by name naturally when fitting)\n"
        f"Race: {race_name} | Class: {class_name} (Level {class_.get('level', 1)}) | Background: {bg_name}\n"
        f"Appearance cues: {appearance_line}\n"
        f"Class flavor to honor: {class_flavor}\n"
        f"Abilities: STR {abilities.get('str', 10)}, DEX {abilities.get('dex', 10)}, "
        f"CON {abilities.get('con', 10)}, INT {abilities.get('int', 10)}, "
        f"WIS {abilities.get('wis', 10)}, CHA {abilities.get('cha', 10)}\n\n"
        "=== ACTIVE KNOWLEDGE CARDS (weave relevant ones in when natural) ===\n"
        f"{card_block}\n\n"
        "=== STYLE REQUIREMENTS ===\n"
        "- 80-160 words, one to two tight paragraphs, SECOND PERSON present tense.\n"
        "- Advance the scene each reply. No stalling, no pure mood pieces.\n"
        "- Ground the reply with at least ONE concrete sensory detail (sight, sound, smell, "
        "touch, or taste). Be specific — textures, faint noises, a smell on the wind.\n"
        f"- Match the campaign tone ({tone}). No cartoonish humor in dark campaigns; no grimdark in light ones.\n"
        f"- Let class flavor color perception: {class_flavor}.\n"
        "- If the action would require a check, describe the outcome naturally — DO NOT ask the "
        "player to roll dice or quote DCs.\n\n"
        "=== HARD BANS ===\n"
        "- Phrases: \"a chill runs down your spine\", \"destiny awaits\", \"little did you know\", "
        "\"legends speak\", \"in a land far away\", \"a mysterious stranger\", \"ye olde\", "
        "\"the adventure begins\".\n"
        "- Do NOT invent named NPCs unless the player's action clearly created/encountered one. "
        "Prefer descriptive tags (\"the hooded woman at the well\") until a name is natural.\n"
        "- No headings, no bullet lists, no OOC/meta commentary, no stat blocks, no dice language.\n"
        "- Do not describe the hero's feelings as abstractions; show reactions via body/environment.\n\n"
        "=== MANDATORY ENDING ===\n"
        "The final 1-2 sentences MUST give the player a CONCRETE next move. Choose exactly one:\n"
        "  (A) Offer 2-3 tangible, actionable choices phrased as a natural sentence (e.g., "
        "\"You can press the cracked door open, slip back toward the stair, or call out to whoever is breathing in the dark.\").\n"
        "  (B) Pose ONE sharp, specific question that forces an immediate decision "
        "(e.g., \"Do you draw steel, or keep your hands where he can see them?\").\n"
        "Never end on vague mood, foreshadowing, or an open cliffhanger without a choice. "
        "The player must know what they can do next."
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
