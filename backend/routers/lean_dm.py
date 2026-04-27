"""Lean DM endpoint for the V2 campaign flow.

Consumes campaigns (campaigns.py), V2 characters (characters_v2), and knowledge
cards (campaign_cards) — no dependency on the legacy dungeon_forge world_state
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

    personality = bg.get("personality") or {}
    ideal = (personality.get("ideal") or "").strip()
    bond = (personality.get("bond") or "").strip()
    flaw = (personality.get("flaw") or "").strip()

    personality_lines: List[str] = []
    if ideal:
        personality_lines.append(f"- Ideal: {ideal}")
    if bond:
        personality_lines.append(f"- Bond: {bond}")
    if flaw:
        personality_lines.append(f"- Flaw: {flaw}")
    personality_block = "\n".join(personality_lines) if personality_lines else "- (no personality hooks set)"

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
    active_leads: List[str] = []
    closed_leads: List[str] = []
    for c in cards[:16]:
        title = c.get("title") or ""
        content = (c.get("content") or c.get("description") or "")[:200]
        ctype = (c.get("type") or "lore").lower()
        tags = [str(t).lower() for t in (c.get("tags") or [])]
        status = (c.get("status") or "").lower()
        if not title:
            continue
        is_quest = ctype == "quest"
        is_active_lead = is_quest and (
            status == "active" or ("opening" in tags and status != "completed" and status != "failed")
        )
        is_closed = is_quest and status in {"completed", "failed"}
        line = f"- [{ctype}] {title}: {content}"
        if is_active_lead:
            active_leads.append(line)
        elif is_closed:
            closed_leads.append(f"- [{status}] {title}")
        else:
            card_summaries.append(line)
    # Cap lore cards at 12 to keep prompt tight, but always include leads.
    card_summaries = card_summaries[:12]
    card_block = "\n".join(card_summaries) if card_summaries else "(no active cards — rely on campaign context)"
    active_lead_block = "\n".join(active_leads) if active_leads else "(no active opening lead — advance scene naturally)"
    closed_lead_block = "\n".join(closed_leads) if closed_leads else "(none)"

    tone = intent.get("tone", "heroic")

    return (
        "You are the Dungeon Master for a Dungeons & Dragons 5e campaign in the "
        "tradition of Matthew Mercer (Critical Role): cinematic but RESTRAINED, "
        "grounded, never melodramatic. You narrate the OUTCOMES of the player's "
        "actions and what the world does in response — never what the hero thinks, "
        "decides, or chooses. The player owns those choices.\n\n"
        "=== CAMPAIGN ===\n"
        f"Tone: {tone} | Focus: {intent.get('focus', 'mixed')} | "
        f"Scope: {intent.get('scope', 'local')} | Danger: {intent.get('danger', 'medium')}\n"
        f"World theme: {world.get('theme', 'mixed')} | World tone: {world.get('tone', 'mixed')}\n"
        f"Starting location: {starting.get('name', 'Unknown')} — {starting.get('description', '')}\n\n"
        "=== HERO (player-controlled) ===\n"
        f"Name: {hero_name} (use sparingly — never twice in one reply)\n"
        f"Race: {race_name} | Class: {class_name} (Level {class_.get('level', 1)}) | Background: {bg_name}\n"
        f"Appearance cues: {appearance_line}\n"
        f"Class flavor (subtle, not stereotype): {class_flavor}\n"
        f"Abilities: STR {abilities.get('str', 10)}, DEX {abilities.get('dex', 10)}, "
        f"CON {abilities.get('con', 10)}, INT {abilities.get('int', 10)}, "
        f"WIS {abilities.get('wis', 10)}, CHA {abilities.get('cha', 10)}\n"
        "Personality hooks (use sparingly — let NPCs react TO these; do not put them in "
        "the hero's head, do not quote verbatim):\n"
        f"{personality_block}\n\n"
        "=== ACTIVE OPENING LEAD(S) (advance or raise stakes in the next 1-3 turns unless the player pivots hard) ===\n"
        f"{active_lead_block}\n\n"
        "=== CLOSED LEADS (do NOT push these again; reference only if naturally relevant) ===\n"
        f"{closed_lead_block}\n\n"
        "=== OTHER KNOWLEDGE CARDS (weave in only when natural) ===\n"
        f"{card_block}\n\n"
        "=== MERCER STYLE — STRICT ===\n"
        "1) DESCRIBE OUTCOMES, NOT DECISIONS. The player declared an action — narrate "
        "what HAPPENS as a result, in the world. The hero's body executes their stated "
        "intent. You may say \"the door yields\" or \"the latch clicks open\" but NEVER "
        "\"you decide to\", \"you know X\", \"you wonder\", \"you sense the truth\".\n"
        "2) NEVER override the player's perception or judgment. Forbidden: \"you scan the room\" "
        "(unless they said so), \"your eyes catch\" (perception in disguise), \"a part of you "
        "knows\", \"in the back of your mind\", \"you smile\", \"you nod\". Show body/world "
        "facts: \"the latch is cold\", \"a floorboard creaks behind you\".\n"
        "3) ONE simile MAX per reply, preferably zero. Never chain similes. No \"like X, like Y\". "
        "Cut metaphor density by 80% from a typical AI default.\n"
        "4) NPCs are silhouettes/voices/postures until named or interacted with. \"The hooded "
        "figure stiffens\", \"a man's voice cuts through the noise\". Do NOT invent names.\n"
        "5) TIME, LIGHT, WEATHER do mood work — not adjective stacks.\n"
        f"6) TONE-MATCHED: gritty = short sentences, working-class smells, cold details. "
        f"Heroic = open vistas, no saccharine. Mystery = emphasize what is OUT of place. "
        f"Match {tone} without naming it.\n"
        "7) NO dice talk. No DC numbers. No \"roll a check.\" Describe outcomes naturally — "
        "if the action would fail, narrate the failure with cause-and-effect specifics.\n"
        "8) APPEARANCE may surface only via (a) physical sensation, (b) a reflection, (c) gear "
        "the hero touches, or (d) someone reacting to them. Never describe the hero's own "
        "face/eyes/build from outside.\n"
        "9) HARD-BAN PHRASES: \"a chill runs down your spine\", \"destiny awaits\", \"the "
        "adventure begins\", \"a mysterious stranger\", \"feels personal\", \"pulls at you\", "
        "\"tugs at your heart\", \"weighs on your soul\", \"stirs something deep\", \"swirl "
        "like autumn leaves\", \"like fingers across\", \"gleam and promise fortune\", "
        "\"ye olde\", rhetorical questions like \"What better place...?\".\n\n"
        "=== LENGTH & FORM ===\n"
        "- 70-130 words, 1-2 tight paragraphs, second person present tense.\n"
        "- Mix sentence lengths. No headings, no bullet lists, no OOC, no meta.\n\n"
        "=== ENDING (Mercer's signature — hand agency back) ===\n"
        "End by giving the player a CLEAR moment of choice. Choose one:\n"
        "  (A) State 2-3 concrete observable facts UNIQUE to this scene (do not reuse a "
        "previous reply's set). Schematic example only: \"<a specific physical fact you just "
        "discovered>; <a specific sound or movement happening now>; <a specific person doing "
        "a specific thing>.\" Replace each placeholder with details true to THIS turn. Stop. "
        "Let the player choose.\n"
        "  (B) Pose ONE sharp specific question rooted in what just changed: "
        "\"Do you draw, or keep your hands where he can see them?\".\n"
        "  (C) End with the simple plain handover: \"What do you do?\"\n"
        "Do NOT prescribe the hero's next action (\"you can duck into...\"). List facts; "
        "the player invents the verb. NEVER reuse a previous reply's facts."
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

    # Load active knowledge cards (canonical collection: campaign_cards)
    cards_cursor = db.campaign_cards.find(
        {"campaign_id": campaign_id}, {"_id": 0}
    ).sort("updatedAt", -1).limit(20)
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
