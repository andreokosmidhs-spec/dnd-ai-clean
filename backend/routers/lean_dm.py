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

from services.campaign_service import build_v2_entity_index
from services.auto_cards import auto_seed_cards_from_narration
from services.dnd_rules import compute_passive_perception, passive_perception_block
from services.roleplay_chaos import (
    apply_alignment_delta,
    build_curse_card_payload,
    chaos_block_for_dm,
    chaos_tier,
    evaluate_alignment,
    get_chaos,
    roll_for_curse,
)
from services.character_deck import (
    _new_card as _new_deck_card,
    art_key_for,
    deck_context_block,
    seed_deck_for_character,
    merge_deck,
)
from services.hook_extractor import extract_hooks, detect_engaged_hook
from services.storyline_service import draft_initial_scene, storyline_to_dict
from services.time_service import (
    DEFAULT_CLOCK_HOUR,
    advance_clock,
    bucket_for_hour,
    estimate_time_advance,
    get_world_clock,
    time_context_block,
)
from utils.entity_mentions import extract_entity_mentions

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


def _build_system_prompt(campaign: dict, character: dict, cards: List[dict], clock_hour: int, deck: Optional[List[dict]] = None, chaos: int = 0) -> str:
    intent = campaign.get("intent") or {}
    world = campaign.get("world") or {}
    starting = world.get("startingLocation") or {}
    setting = world.get("setting") or {}

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
    if appearance.get("hairColor") or appearance.get("hairStyle"):
        hair_phrase = " ".join(
            filter(None, [appearance.get("hairStyle"), appearance.get("hairColor")])
        ).strip()
        if hair_phrase:
            appearance_bits.append(f"{hair_phrase} hair")
    if appearance.get("facialHair"):
        appearance_bits.append(f"{appearance['facialHair']} facial hair")
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

    # Pull the most recently updated location card with biome metadata —
    # that's effectively "where the player is right now" for grounding
    # Survival/Nature checks. Falls back to a "no biome" block.
    current_biome_card = None
    for c in cards:
        if (c.get("type") or "").lower() == "location" and c.get("biome"):
            current_biome_card = c
            break
    if current_biome_card:
        biome_block = (
            f"Biome: {current_biome_card.get('biome_label') or current_biome_card.get('biome')} "
            f"({current_biome_card.get('title')})\n"
            f"Survival DC modifier: {current_biome_card.get('biome_survival_dc_mod', 0):+d} "
            f"(higher = harder)\n"
            f"Nature DC modifier: {current_biome_card.get('biome_nature_dc_mod', 0):+d}\n"
            f"Resources available: {', '.join(current_biome_card.get('biome_resources', [])[:6])}\n"
            f"Wildlife: {', '.join(current_biome_card.get('biome_animals', [])[:6])}\n"
            f"Local threats: {', '.join(current_biome_card.get('biome_monsters', [])[:5])}"
        )
    else:
        biome_block = "(no biome data — describe environment naturally)"

    # Setting block — era, factions, recent events, current tension.
    setting_lines: List[str] = []
    if setting:
        era = (setting.get("era") or "").strip()
        if era:
            setting_lines.append(f"- Era: {era}")
        for f in (setting.get("factions") or [])[:3]:
            if not f.get("name"):
                continue
            detail = "; ".join(p for p in [f.get("domain"), f.get("stance")] if p)
            setting_lines.append(f"- Faction — {f['name']}: {detail}")
        for e in (setting.get("recent_events") or [])[:2]:
            if not e.get("title"):
                continue
            setting_lines.append(f"- Recent event — {e['title']}: {e.get('summary', '')}")
        tension = (setting.get("current_tension") or "").strip()
        if tension:
            setting_lines.append(f"- Current tension: {tension}")
    setting_block = "\n".join(setting_lines) if setting_lines else "(no setting context)"

    # NPC roleplay anchors — pull the hidden identity sheets from any NPC
    # cards in the player's deck so the DM can voice them consistently and
    # gate social actions against their actual social DCs. Cap at 6 to keep
    # the prompt tight; the DM only needs the in-scene crowd, not every NPC
    # they've ever met.
    npc_anchor_lines: List[str] = []
    for c in cards[:24]:
        if (c.get("type") or "").lower() != "character":
            continue
        secret = c.get("secret_content") or {}
        if not isinstance(secret, dict) or not secret:
            continue
        nm = (c.get("title") or "").strip()
        if not nm:
            continue
        stats = secret.get("stats") or {}
        pers = secret.get("personality") or {}
        manners = secret.get("mannerisms") or []
        npc_anchor_lines.append(
            f"- {nm} — speech: {secret.get('speech_style','plain')}; "
            f"voice: {pers.get('trait','')}; ideal: {pers.get('ideal','')}; "
            f"flaw: {pers.get('flaw','')}; mannerisms: {', '.join(manners[:3])}; "
            f"motive THIS scene: {secret.get('current_motivation','')}; "
            f"social DCs — Intim {stats.get('intimidation_dc',13)}, "
            f"Persuasion {stats.get('persuasion_dc',13)}, "
            f"Deception (against them) {stats.get('deception_dc',13)}, "
            f"Insight (to read them) {stats.get('insight_dc',12)}; "
            f"secrets (NEVER reveal unless extracted): {' | '.join((secret.get('secrets') or [])[:2])}; "
            f"allegiances: {', '.join((secret.get('allegiances') or [])[:2])}"
        )
        if len(npc_anchor_lines) >= 6:
            break
    npc_anchor_block = (
        "\n".join(npc_anchor_lines)
        if npc_anchor_lines
        else "(no NPCs with identity sheets in scene — describe new NPCs as silhouettes/voices until interacted with)"
    )

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
        "=== WORLD SETTING (ground truth — factions / events / tension that shape every scene) ===\n"
        f"{setting_block}\n\n"
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
        "=== NPC ROLEPLAY ANCHORS (DM-only, NEVER reveal verbatim — these are the "
        "actor's notes for staying in character across turns) ===\n"
        f"{npc_anchor_block}\n\n"
        "=== CURRENT BIOME (use for environment details + naturally adjust check difficulty) ===\n"
        f"{biome_block}\n\n"
        f"{time_context_block(clock_hour)}\n\n"
        f"{passive_perception_block(character)}\n\n"
        f"{deck_context_block(deck or [])}\n\n"
        f"{chaos_block_for_dm(chaos)}\n\n"
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
        "4b) IN-CHARACTER NPC ROLEPLAY (HARD RULE). Once an NPC has an identity sheet "
        "in the NPC ROLEPLAY ANCHORS block above, they MUST stay in character across "
        "every turn — same speech style, same mannerisms, same motive. Their decisions "
        "follow their flaw + bond + current_motivation; they NEVER act 'out of character' "
        "to advance plot. They never volunteer their listed secrets — those have to be "
        "EXTRACTED via successful Intimidation/Persuasion/Deception/Insight. Write their "
        "dialogue with their voice ('clipped, drops r's' = clipped, drops r's), drop "
        "their physical mannerisms into the prose. If multiple NPCs are present, "
        "their voices must be DISTINCT from each other.\n"
        "5) TIME, LIGHT, WEATHER do mood work — not adjective stacks.\n"
        f"6) TONE-MATCHED: gritty = short sentences, working-class smells, cold details. "
        f"Heroic = open vistas, no saccharine. Mystery = emphasize what is OUT of place. "
        f"Match {tone} without naming it.\n"
        "7) NO dice talk. No DC numbers. No \"roll a check.\" Describe outcomes naturally — "
        "if the action would fail, narrate the failure with cause-and-effect specifics.\n"
        "7b) SOCIAL-ACTION GATING (HARD RULE). When the player's action contains "
        "INTIMIDATION cues (threaten, draw a weapon at an NPC, growl, snarl, "
        "raise a fist), PERSUASION cues (convince, plead, persuade, talk down, "
        "flatter, charm), DECEPTION cues (lie, bluff, fake, pretend, pose as), "
        "or INSIGHT/READ cues (read their face, sense if they're lying), DO NOT "
        "auto-resolve the NPC's reaction. Instead: narrate ONLY the visible "
        "BEAT (your dagger catches the lamplight; the man's pupils tighten; his "
        "hand drifts toward his belt) and END the reply by suggesting the "
        "appropriate ability check naturally — e.g. 'his eyes flick to the "
        "blade — what's your tone?' or 'this is a threat held at the edge of a "
        "blade.' The system layer will roll the check; you narrate the FALLOUT "
        "in the next turn. Auto-resolving social pressure (NPC instantly "
        "confesses / believes / bows) without a check breaks the rule.\n"
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

    # Pull HOOKS the DM planted in the LAST 1-2 turns so we can detect if
    # this player action is engaging one of them. Hooks are persisted alongside
    # DM messages by this very endpoint at the end of the previous turn.
    active_hooks: List[dict] = []
    try:
        recent_dm = await db[_MESSAGES_COLLECTION].find(
            {"session_id": session_id, "role": "dm"},
            {"_id": 0, "hooks": 1},
        ).sort("timestamp", -1).limit(2).to_list(length=2)
        for m in recent_dm:
            for h in (m.get("hooks") or []):
                if isinstance(h, dict) and h.get("id"):
                    active_hooks.append(h)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to load active hooks: {exc}")
    # First-turn fallback: no DM messages yet, but the starting_scene was the
    # opening DM beat. Pull its hooks so engagement detection works on turn 1.
    if not active_hooks:
        try:
            ss_hooks = ((campaign.get("starting_scene") or {}).get("hooks")) or []
            for h in ss_hooks:
                if isinstance(h, dict) and h.get("id"):
                    active_hooks.append(h)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Failed to load starting_scene hooks: {exc}")

    # Engagement detection — does the player's action target one of the active hooks?
    # If so, draft a storyline IN PARALLEL with the DM narration. The drafted
    # storyline is returned in the response so the frontend can render the
    # "Active Investigation" panel + first beat.
    engaged_hook = None
    storyline_payload = None
    if active_hooks:
        try:
            engaged_hook = await detect_engaged_hook(req.player_action, active_hooks)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Hook engagement check failed: {exc}")
            engaged_hook = None

    # Fallback: cached hooks may be stale (older campaigns saved only the
    # canonical "three things" enumeration and missed concrete narrative
    # objects like a posted notice or a sign on a wall). Re-extract hooks
    # from the most recent DM narration on demand and retry engagement so
    # players never get stuck targeting something the narration clearly
    # showed but the cached hook list omitted.
    if engaged_hook is None:
        try:
            recent_text_parts: List[str] = []
            # Most recent DM narration from history (last 1-2 turns).
            for m in reversed(history or []):
                if m.get("role") == "dm" and m.get("content"):
                    recent_text_parts.append(str(m["content"]))
                    if len(recent_text_parts) >= 2:
                        break
            # First-turn fallback: starting_scene introText.
            if not recent_text_parts:
                ss = campaign.get("starting_scene") or {}
                intro = ss.get("introText") or ss.get("intro_text")
                if intro:
                    recent_text_parts.append(str(intro))
            recent_narration = "\n\n".join(recent_text_parts)[:4000]
            if recent_narration:
                refreshed = await extract_hooks(recent_narration, max_hooks=5)
                # Keep only hooks not already in active_hooks (by topic match).
                seen_topics = {(h.get("topic") or "").lower() for h in active_hooks}
                new_hooks = [
                    h for h in refreshed
                    if (h.get("topic") or "").lower() not in seen_topics
                ]
                if new_hooks:
                    merged_pool = list(active_hooks) + new_hooks
                    engaged_hook = await detect_engaged_hook(req.player_action, merged_pool)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Hook re-extraction fallback failed: {exc}")

    # Build LLM prompt — inject current time-of-day for narration grounding.
    clock_hour = get_world_clock(campaign)
    passive_perception = compute_passive_perception(character)
    chaos_value = get_chaos(campaign)

    # Load (or seed) the player's deck so the DM can read what the character
    # has — race traits, languages, class features, background contacts etc.
    try:
        deck_doc = await db.character_decks.find_one({"character_id": req.character_id})
        _deck_now = datetime.now(timezone.utc)
        if deck_doc and isinstance(deck_doc.get("cards"), list):
            fresh = seed_deck_for_character(character)
            deck_cards = merge_deck(deck_doc["cards"], fresh)
            await db.character_decks.update_one(
                {"character_id": req.character_id},
                {"$set": {"cards": deck_cards, "updated_at": _deck_now}},
            )
        else:
            deck_cards = seed_deck_for_character(character)
            await db.character_decks.insert_one({
                "character_id": req.character_id,
                "cards": deck_cards,
                "created_at": _deck_now,
                "updated_at": _deck_now,
            })
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Deck load failed (non-fatal): {exc}")
        deck_cards = []

    system_prompt = _build_system_prompt(campaign, character, cards, clock_hour, deck=deck_cards, chaos=chaos_value)

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

    # Time-of-day advancement — lightweight regex on player action + DM narration.
    # Each turn moves the campaign clock by 0..8 hours (default 0 for routine
    # play; rest/travel/thorough actions bump it). Persisted on world_state
    # so the next turn picks up the new period naturally.
    advance_h = estimate_time_advance(req.player_action, narration)
    new_clock_hour = advance_clock(clock_hour, advance_h)
    if new_clock_hour != clock_hour:
        try:
            await db.campaigns.update_one(
                {"campaign_id": campaign_id},
                {"$set": {"world_state.clock_hour": new_clock_hour}},
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Failed to persist clock_hour: {exc}")
    time_bucket = bucket_for_hour(new_clock_hour)
    # Update in-memory campaign so any downstream code (storyline draft) sees it.
    campaign.setdefault("world_state", {})["clock_hour"] = new_clock_hour

    # ===== Roleplay alignment check + chaos meter =====
    alignment = await evaluate_alignment(character, req.player_action)
    new_chaos = apply_alignment_delta(chaos_value, alignment.get("severity", 0))

    drafted_curse = None
    # Only draft a curse on a violation turn (severity > 0) AND when the roll
    # passes — keeps the punishment scene-bound rather than a steady drip.
    if alignment.get("severity", 0) > 0 and roll_for_curse(new_chaos):
        try:
            payload = build_curse_card_payload(new_chaos)
            curse_card = _new_deck_card(
                source=payload["source"],
                title=payload["title"],
                description=payload["description"],
                rarity=payload["rarity"],
                mechanical=payload["mechanical"],
                tags=payload.get("tags", ["curse"]),
            )
            # Attach saved art if any user has uploaded for this curse before.
            try:
                art_doc = await db.card_art_library.find_one({"art_key": curse_card["art_key"]})
                if art_doc and art_doc.get("data_url"):
                    curse_card["art_data_url"] = art_doc["data_url"]
            except Exception:  # noqa: BLE001
                pass
            existing_deck = await db.character_decks.find_one({"character_id": req.character_id})
            if existing_deck:
                cards_list = existing_deck.get("cards", [])
                cards_list.append(curse_card)
                await db.character_decks.update_one(
                    {"character_id": req.character_id},
                    {"$set": {"cards": cards_list, "updated_at": datetime.now(timezone.utc)}},
                )
            drafted_curse = curse_card
            # Cool chaos slightly when a curse drafts — the "punishment" lands
            # so pressure releases (still elevated, but not maxed).
            new_chaos = max(0, new_chaos - 12)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"curse draft failed (non-fatal): {exc}")

    if new_chaos != chaos_value:
        try:
            await db.campaigns.update_one(
                {"campaign_id": campaign_id},
                {"$set": {"world_state.chaos": new_chaos}},
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Failed to persist chaos: {exc}")
    chaos_payload = {
        "value": new_chaos,
        "delta": new_chaos - chaos_value,
        "tier": chaos_tier(new_chaos),
        "alignment": alignment,
        "drafted_curse": drafted_curse,
    }

    # Extract HOOKS from this DM narration so the next turn can detect
    # engagement and the frontend can render them inline. Cheap regex first;
    # LLM fallback only if regex finds nothing.
    try:
        narration_hooks = await extract_hooks(narration, max_hooks=3)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Hook extraction failed: {exc}")
        narration_hooks = []

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
                    "hooks": narration_hooks,
                },
            ]
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to persist messages (non-fatal): {exc}")

    # If the player's action engaged a previously-planted hook, draft a
    # storyline now (after narration). This lands as a payload the frontend
    # can render as an "Active Investigation" panel + quest card.
    if engaged_hook is not None:
        try:
            # Pass recent cards to ground the storyline in named entities.
            campaign["_recent_cards"] = cards or []
            drafted = await draft_initial_scene(
                campaign=campaign,
                character=character,
                hook=engaged_hook,
                narration_context=narration,
            )
            from uuid import uuid4 as _uuid4
            storyline_id = f"sl_{_uuid4().hex[:10]}"
            first_beat = (drafted.get("beats") or [{}])[0]

            # Seed a quest KnowledgeCard linked to the storyline so the player
            # sees it in the Quest Log immediately. Open-ended scene-driven
            # storyline — no fixed "Beat X of N" framing.
            from models.campaign_models import KnowledgeCard
            quest_card = KnowledgeCard(
                type="quest",
                title=drafted.get("title") or "Active Investigation",
                description=(
                    f"{first_beat.get('description','')} (Active scene — suggested "
                    f"{first_beat.get('check_type','Investigation')} DC {first_beat.get('dc',12)}.)"
                ),
                source="hook-storyline",
                confidence="high",
                tags=["quest", "active", "investigation", "storyline"],
                status="active",
                updatedAt=now,
            )
            await db.campaign_cards.insert_one(
                {**quest_card.model_dump(), "campaign_id": campaign_id, "storyline_id": storyline_id}
            )

            storyline_doc = {
                "id": storyline_id,
                "campaign_id": campaign_id,
                "character_id": req.character_id,
                "title": drafted.get("title") or "Investigation",
                "hook_text": engaged_hook.get("text", ""),
                "hook_id": engaged_hook.get("id"),
                "hook_topic": engaged_hook.get("topic", ""),
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
            await db.campaign_storylines.insert_one(dict(storyline_doc))
            storyline_payload = storyline_to_dict(storyline_doc)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Storyline auto-draft failed: {exc}")
            storyline_payload = None

    # Return a response shape that's compatible with AdventureLogWithDM
    world_dict = campaign.get("world") or {}
    entity_index = build_v2_entity_index(world_dict, cards=cards)

    # Auto-card seeding: detect brand-new NPCs / locations / factions that
    # the DM just introduced and auto-create knowledge cards for them.
    # Runs in the same turn BEFORE mention extraction, so the new cards
    # become clickable entities in this very response — no "it only works
    # on the next turn" lag.
    starting_town = (world_dict.get("starting_town") or {}).get("name") or ""
    realm_name = (world_dict.get("world_core") or {}).get("name") or ""
    location_origin = starting_town or realm_name or None
    new_cards = await auto_seed_cards_from_narration(
        campaign_id=campaign_id,
        narration=narration,
        entity_index=entity_index,
        cards_collection=db.campaign_cards,
        location_origin=location_origin,
    )
    if new_cards:
        entity_index = build_v2_entity_index(world_dict, cards=cards + new_cards)

    mentions = extract_entity_mentions(narration, entity_index)
    return {
        "success": True,
        "data": {
            "narration": narration,
            "entity_mentions": mentions,
            "hooks": narration_hooks,
            "engaged_hook_id": (engaged_hook or {}).get("id") if engaged_hook else None,
            "storyline": storyline_payload,
            "world_state_update": {
                "clock_hour": new_clock_hour,
                "time_of_day": time_bucket["key"],     # string — legacy compatibility
                "time_bucket": time_bucket,            # full {key, label, icon, hour} for new UI
                "time_advanced_hours": advance_h,
                "passive_perception": passive_perception,  # {score, tier, wis_mod, proficient, prof_bonus}
                "chaos": chaos_payload,                # {value, delta, tier, alignment, drafted_curse}
            },
            "player_updates": {},
            "options": [],
        },
    }
