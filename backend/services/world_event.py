"""
World events — spontaneous acted-out NPC encounters that happen TO the player.

These are not mysteries or rewards. They are ambient slice-of-life moments:
an NPC physically approaches and delivers their opening line in their own voice.
The player can engage or ignore them. If they engage, the main DM voices the NPC
consistently using the character card that gets seeded here with a full identity sheet.
"""

from __future__ import annotations

import logging
import os
import random
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

_BASE_PROBABILITY = 0.20
_NIGHT_PROBABILITY = 0.06  # 10pm–5am — streets are emptier

# Each archetype gives the LLM a tight brief so it produces a specific
# character instead of a generic "friendly NPC". Temperature 0.95 handles
# the variation; the archetype controls the TYPE of encounter.
_ARCHETYPES = [
    {
        "slug": "drunk_conspiracist",
        "category": "comedy",
        "brief": (
            "A visibly drunk man who is absolutely convinced of a wild conspiracy "
            "theory and desperately needs someone — anyone — to believe him"
        ),
        "npc_state": "drunk, swaying, wine-breathed, completely earnest",
        "speech_hint": (
            "slurred speech, loses the thread mid-sentence, uses '*hic*' as "
            "punctuation, speaks in breathless fragments of grand revelation"
        ),
    },
    {
        "slug": "ugly_flirt",
        "category": "social",
        "brief": (
            "Someone who is objectively unattractive and completely unaware of it, "
            "aggressively flirting with overconfident charm and terrible pickup lines"
        ),
        "npc_state": "bold, preening, entirely self-assured, thick-skinned to any reaction",
        "speech_hint": (
            "uses terrible pickup lines with total sincerity, occasionally refers "
            "to themselves in the third person, calls the player 'friend' immediately"
        ),
    },
    {
        "slug": "clingy_fan",
        "category": "social",
        "brief": (
            "A local who recognizes the player from their adventures and becomes "
            "overwhelmingly, embarrassingly clingy — wants to tell everyone nearby"
        ),
        "npc_state": "breathless with excitement, grabs player's arm, won't stop talking",
        "speech_hint": (
            "rapid-fire questions, wildly exaggerates what they 'heard about you', "
            "keeps saying 'I knew it was you', tries to introduce you to strangers nearby"
        ),
    },
    {
        "slug": "teenager_scheme",
        "category": "comedy",
        "brief": (
            "A teenager who wants the player to pretend to be their parent or guardian "
            "so they can purchase something they are clearly too young to buy"
        ),
        "npc_state": "nervous, whispering, glancing around, trying hard to look casual",
        "speech_hint": (
            "conspiratorial hush, overly casual to cover nerves, has clearly "
            "rehearsed this speech, drops the pretense the moment anyone looks at them"
        ),
    },
    {
        "slug": "street_prophet",
        "category": "weird",
        "brief": (
            "A wild-eyed street preacher who has just received a very specific and "
            "absurd divine prophecy that apparently involves the player personally"
        ),
        "npc_state": "intense, eyes wide, gesturing at the sky, grabbing at passersby",
        "speech_hint": (
            "dramatic pauses, archaic phrasing, absolute unshakeable conviction, "
            "the prophecy involves oddly specific mundane details"
        ),
    },
    {
        "slug": "wrong_person",
        "category": "comedy",
        "brief": (
            "Someone who is completely and unshakeably convinced the player is a "
            "specific other person they know well — and refuses to hear otherwise"
        ),
        "npc_state": "warm familiarity, uses the wrong name, laughs off any denial",
        "speech_hint": (
            "references shared memories that never happened, calls the player by "
            "the wrong name throughout, treats denials as jokes"
        ),
    },
    {
        "slug": "desperate_vendor",
        "category": "comedy",
        "brief": (
            "A merchant who absolutely needs one more sale today or loses their stall, "
            "growing increasingly creative and unhinged in their sales pitch"
        ),
        "npc_state": "smile cracking under pressure, voice a pitch too loud, sweating",
        "speech_hint": (
            "invents product features on the fly, price drops every other sentence, "
            "dramatic claims about the item's history or magical properties"
        ),
    },
    {
        "slug": "lost_child",
        "category": "comedy",
        "brief": (
            "A small child who has just found the most impressive rock they have "
            "ever seen and has chosen the player specifically to show it to"
        ),
        "npc_state": "completely earnest, holding out a very ordinary-looking rock, proud",
        "speech_hint": (
            "simple vocabulary, breathless with importance, describes the rock "
            "with absolute reverence, oblivious to any social context"
        ),
    },
    {
        "slug": "old_rival",
        "category": "social",
        "brief": (
            "Someone who claims to have beaten the player at something years ago "
            "and has clearly been dining out on that story ever since — very smug"
        ),
        "npc_state": "smug, arms folded, waiting for recognition that never comes",
        "speech_hint": (
            "keeps referencing 'that time in [place]', expects the player to "
            "remember vividly, deflated when they don't, doubles down anyway"
        ),
    },
    {
        "slug": "rambling_poet",
        "category": "weird",
        "brief": (
            "A travelling bard who has written a terrible epic ballad about the player "
            "based entirely on incorrect secondhand information and wants to perform it"
        ),
        "npc_state": "excited, clutching a scroll, already clearing their throat",
        "speech_hint": (
            "speaks in attempted verse even out of character, gets the player's "
            "deeds hilariously wrong, extremely proud of the work"
        ),
    },
]


def _should_fire(clock_hour: int) -> bool:
    night = clock_hour >= 22 or clock_hour < 5
    return random.random() < (_NIGHT_PROBABILITY if night else _BASE_PROBABILITY)


async def generate_world_event(
    campaign: Dict,
    character: Dict,
    clock_hour: int,
    cards_collection=None,
) -> Optional[Dict]:
    """Maybe generate a spontaneous acted-out NPC encounter.

    Returns:
        {narration, npc_name, event_type, category}  or  None
    """
    if not _should_fire(clock_hour):
        return None

    archetype = random.choice(_ARCHETYPES)

    world = campaign.get("world") or {}
    identity = character.get("identity") or {}
    hero_name = identity.get("name") or "the adventurer"
    cls = character.get("class") or {}
    class_name = (cls.get("key") or "adventurer").title()
    starting = world.get("startingLocation") or {}
    location_name = starting.get("name") or "the street"
    tone = (campaign.get("intent") or {}).get("tone", "heroic")

    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        import json as _json

        system = (
            "You are a D&D Dungeon Master writing a spontaneous ambient NPC encounter. "
            "The NPC physically approaches the player and delivers their opening lines IN CHARACTER.\n\n"
            "Rules (non-negotiable):\n"
            "1. Give the NPC a specific name — first name + optional surname or epithet.\n"
            "2. Write 1-2 sentences of physical approach: what the player sees/hears as the NPC "
            "arrives. Use present tense, second person. No inner state, no 'you feel'.\n"
            "3. Then write the NPC's ACTUAL SPOKEN WORDS in double quotes. Render their voice "
            "literally: slurred syllables, dropped letters, interruptions, '*hic*', em-dashes for "
            "pauses, sentence fragments. The voice must be unmistakable on the page.\n"
            "4. End after the NPC's opening line. Do NOT resolve the encounter — the player decides.\n"
            "5. Output strict JSON only (no code fence):\n"
            "{\n"
            '  "npc_name": "specific name",\n'
            '  "encounter": "the full acted encounter text — approach + quoted opening line",\n'
            '  "speech_style": "one line describing their voice for DM continuity",\n'
            '  "mannerisms": ["physical habit 1", "physical habit 2", "physical habit 3"],\n'
            '  "personality_flaw": "their main flaw in one phrase",\n'
            '  "current_motivation": "what they want RIGHT NOW in this moment"\n'
            "}"
        )

        prompt = (
            f"Archetype: {archetype['brief']}\n"
            f"NPC state: {archetype['npc_state']}\n"
            f"Voice hint: {archetype['speech_hint']}\n"
            f"Location: {location_name}\n"
            f"Hour: {clock_hour:02d}:00\n"
            f"Campaign tone: {tone}\n"
            f"Hero: {hero_name} the {class_name}\n\n"
            "Generate the NPC and their opening encounter now."
        )

        chat = LlmChat(
            api_key=api_key,
            session_id=f"world-event-{uuid4().hex[:8]}",
            system_message=system,
        )
        chat.with_model("openai", "gpt-4o-mini").with_params(temperature=0.95, max_tokens=300)

        raw = (await chat.send_message(UserMessage(text=prompt))) or ""
        s = raw.strip()
        if s.startswith("```"):
            s = s.strip("`")
            if s.lower().startswith("json"):
                s = s[4:].lstrip()
        try:
            data = _json.loads(s)
        except Exception:
            a, b = s.find("{"), s.rfind("}")
            data = _json.loads(s[a : b + 1]) if a != -1 and b > a else {}
        if not isinstance(data, dict):
            return None

        npc_name = (data.get("npc_name") or "").strip()
        encounter = (data.get("encounter") or "").strip()
        if not npc_name or not encounter:
            return None

        # Seed a character card with the full identity sheet so the main DM
        # can voice this NPC consistently if the player engages next turn.
        if cards_collection is not None:
            campaign_id = campaign.get("campaign_id") or campaign.get("id")
            if campaign_id:
                try:
                    existing = await cards_collection.find_one(
                        {"campaign_id": campaign_id, "title": npc_name, "type": "character"}
                    )
                    if not existing:
                        now = datetime.now(timezone.utc)
                        await cards_collection.insert_one({
                            "id": str(uuid4()),
                            "campaign_id": campaign_id,
                            "title": npc_name,
                            "type": "character",
                            "content": (
                                f"Met in {location_name}. {archetype['brief'].capitalize()}."
                            ),
                            "status": "introduced",
                            "auto_seeded": True,
                            "source": "world_event",
                            "pinned": False,
                            "secret_content": {
                                "speech_style": data.get("speech_style") or archetype["speech_hint"],
                                "personality": {
                                    "trait": archetype["npc_state"],
                                    "ideal": "",
                                    "flaw": data.get("personality_flaw") or "",
                                },
                                "mannerisms": data.get("mannerisms") or [],
                                "current_motivation": (
                                    data.get("current_motivation") or archetype["brief"]
                                ),
                                "stats": {
                                    "intimidation_dc": 10,
                                    "persuasion_dc": 12,
                                    "deception_dc": 11,
                                    "insight_dc": 10,
                                },
                                "secrets": [],
                                "allegiances": [],
                            },
                            "createdAt": now.isoformat(),
                            "updatedAt": now.isoformat(),
                        })
                except Exception as exc:
                    logger.warning(f"World event NPC card seed failed (non-fatal): {exc}")

        return {
            "narration": encounter,
            "npc_name": npc_name,
            "event_type": archetype["slug"],
            "category": archetype["category"],
        }

    except Exception as exc:
        logger.warning(f"World event generation failed (non-fatal): {exc}")
        return None
