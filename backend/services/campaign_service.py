from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4
import logging

from models.campaign_models import CampaignIntent, KnowledgeCard

logger = logging.getLogger(__name__)


def _format_title(text: str) -> str:
    return text.replace("_", " ").title()


# Short flavor guidance per D&D class — keeps the AI narrator's language
# tonally consistent with the hero's archetype without stereotyping.
_CLASS_FLAVOR = {
    "barbarian": "visceral, physical, raw — think breath, heartbeat, primal instincts",
    "bard": "performative, observant of social undercurrents, attuned to rumor and rhythm",
    "cleric": "reverent and disciplined; the divine is quiet pressure, not constant miracle",
    "druid": "rooted in weather, animal signs, the smell of earth; nature as a character",
    "fighter": "practical, trained eye for terrain, weapons, exits, and threats",
    "monk": "spare, precise, attentive to breath, balance, and the stillness between sounds",
    "paladin": "moral weight and conviction; oaths color how the world is seen",
    "ranger": "tracker's eye — footprints, broken twigs, wind direction, animal silence",
    "rogue": "shadows, sightlines, escape routes, pockets, locks — always reading the room",
    "sorcerer": "magic is in the blood; subtle currents, intuition, flickers of the uncanny",
    "warlock": "a patron's presence lurks at the edge; whispered debts, unsettling omens",
    "wizard": "cerebral, analytical — arcane patterns, etymology, cataloged observation",
    "artificer": "tinker's eye — materials, mechanisms, opportunities to improvise",
    "_default": "grounded, observant, driven by the hero's own reasons",
}


def _build_starting_location(intent: CampaignIntent) -> Dict:
    scope_names = {
        "City": "Gate of Emberfall",
        "Wilderness": "Trail of Whispering Pines",
        "Dungeon": "Vault of Forgotten Echoes",
        "Mixed": "Crossroads of Twin Lanterns",
    }
    return {
        "name": scope_names.get(intent.scope, "Frontier Outpost"),
        "description": f"A {intent.scope.lower()} starting point shaped by a {intent.tone.lower()} tone.",
        "danger": intent.danger,
        "focus": intent.focus,
    }


def build_world_blueprint(intent: CampaignIntent, character: Dict | None) -> Dict:
    hero_desc = "adventurer"
    if character:
        race = character.get("race", {})
        class_info = character.get("class", {}) or character.get("class_", {})
        background = character.get("background", {})
        race_name = _format_title(race.get("key", "wanderer"))
        class_name = _format_title(class_info.get("key", "hero"))
        bg_name = _format_title(background.get("key", "drifter"))
        hero_desc = f"{race_name} {class_name} from a {bg_name} background"

    starting_location = _build_starting_location(intent)

    summary = (
        f"A {intent.tone.lower()} campaign focused on {intent.focus.lower()} begins in the {starting_location['name']}, "
        f"tailored for a {hero_desc}."
    )

    realm_name = f"Realm of {_format_title(intent.focus)}"

    return {
        "summary": summary,
        "tags": [intent.tone.lower(), intent.focus.lower(), intent.scope.lower(), intent.danger.lower()],
        "startingLocation": starting_location,
        "theme": intent.focus,
        "tone": intent.tone,
        # Legacy-compatible aliases so the frontend WorldInfoPanel shows real names
        # instead of "Unknown Realm / Unknown Town".
        "world_core": {
            "name": realm_name,
            "summary": summary,
            "tone": intent.tone,
        },
        "starting_town": {
            "name": starting_location["name"],
            "summary": starting_location["description"],
        },
    }


def build_starting_scene(campaign_id: str, world: Dict) -> Dict:
    starting_location = world.get("startingLocation", {})
    location_name = starting_location.get("name", "the starting point")
    intro_text = (
        f"You arrive at {location_name}, a place colored by {world.get('tone', 'mixed')} tales. "
        "Locals watch curiously as your journey begins."
    )
    return {
        "seed": f"scene_{campaign_id[:8]}",
        "introText": intro_text,
    }


async def build_starting_scene_with_ai(
    campaign_id: str,
    world: Dict,
    intent: CampaignIntent,
    character: Optional[Dict],
) -> Dict:
    """Produce a cinematic second-person campaign intro using the LLM.
    Falls back to the template intro on any failure.
    """
    fallback = build_starting_scene(campaign_id, world)
    try:
        import os
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("No LLM key for intro generation; using fallback")
            return fallback

        starting_location = world.get("startingLocation", {})
        location_name = starting_location.get("name", "the starting point")
        location_desc = starting_location.get("description", "")

        # Collect hero details
        name = "the adventurer"
        race_name = "human"
        class_name = "adventurer"
        class_key = "adventurer"
        bg_name = "drifter"
        appearance_bits: List[str] = []
        age_category = ""
        sex = ""
        ideal = ""
        bond = ""
        flaw = ""

        if character:
            identity = character.get("identity") or {}
            race = character.get("race") or {}
            class_info = character.get("class") or character.get("class_") or {}
            bg = character.get("background") or {}
            appearance = character.get("appearance") or {}
            name = identity.get("name") or name
            sex = identity.get("sex") or ""
            race_name = _format_title(race.get("key", "human"))
            class_key = (class_info.get("key") or "adventurer").lower()
            class_name = _format_title(class_key)
            bg_name = _format_title(bg.get("key", "drifter"))
            age_category = appearance.get("ageCategory") or ""
            build = appearance.get("build") or ""
            hair = appearance.get("hairColor") or ""
            eyes = appearance.get("eyeColor") or ""
            notable = appearance.get("notableFeatures") or []
            if build:
                appearance_bits.append(f"{build} build")
            if hair:
                appearance_bits.append(f"{hair} hair")
            if eyes:
                appearance_bits.append(f"{eyes} eyes")
            if notable:
                appearance_bits.append("notable: " + ", ".join(notable[:3]))
            personality = bg.get("personality") or {}
            ideal = (personality.get("ideal") or "").strip()
            bond = (personality.get("bond") or "").strip()
            flaw = (personality.get("flaw") or "").strip()

        class_flavor = _CLASS_FLAVOR.get(class_key, _CLASS_FLAVOR["_default"])
        appearance_line = "; ".join(appearance_bits) if appearance_bits else "unremarkable at first glance"
        hero_header = f"{name} — a {age_category or 'adult'} {sex or ''} {race_name} {class_name}, {bg_name} background".replace("  ", " ").strip()

        personality_lines: List[str] = []
        if ideal:
            personality_lines.append(f"- Ideal: {ideal}")
        if bond:
            personality_lines.append(f"- Bond: {bond}")
        if flaw:
            personality_lines.append(f"- Flaw: {flaw}")
        personality_block = "\n".join(personality_lines) if personality_lines else "- (no personality hooks set)"

        system_message = (
            "You are a master Dungeons & Dragons 5e storyteller. You write grounded, cinematic "
            "second-person openings that PERSONALIZE the scene to the specific hero and campaign "
            "tone given. You never produce generic fantasy filler."
        )

        prompt = (
            "Write the OPENING narration of a new D&D 5e campaign.\n\n"
            "=== CAMPAIGN ===\n"
            f"Tone: {intent.tone} | Focus: {intent.focus} | Scope: {intent.scope} | Danger: {intent.danger}\n"
            f"World theme: {world.get('theme', 'mixed')} | World tone: {world.get('tone', 'mixed')}\n\n"
            "=== LOCATION (use this exact name; do NOT invent a different place) ===\n"
            f"{location_name} — {location_desc}\n\n"
            "=== HERO (reference them BY NAME, at least once) ===\n"
            f"{hero_header}\n"
            f"Appearance cues: {appearance_line}\n"
            f"Class flavor to honor: {class_flavor}\n"
            "Personality hooks (weave in ONE subtly — a reaction, a hesitation, "
            "or a detail the hero notices because of who they are; do NOT quote verbatim):\n"
            f"{personality_block}\n\n"
            "=== STYLE REQUIREMENTS ===\n"
            "- 110-160 words, EXACTLY ONE paragraph, SECOND PERSON present tense (\"you\").\n"
            f"- Address the hero by name (\"{name}\") naturally at least once.\n"
            "- Ground the reader with at least TWO distinct sensory details from different senses "
            "(sight, sound, smell, touch, or taste). Be concrete and specific — real textures, "
            "weather, faint noises, a smell on the wind.\n"
            f"- Match the campaign tone ({intent.tone}). Do NOT drift into cartoonish or saccharine prose.\n"
            f"- Reflect the class flavor: {class_flavor}\n"
            f"- Use the starting location name ({location_name}) at least once; do not invent a tavern, inn, "
            "or marketplace if the location isn't one.\n\n"
            "=== HARD BANS (do not write any of these) ===\n"
            "- The words/phrases: \"tavern\", \"wizened old man\", \"a chill runs down your spine\", \"destiny awaits\", "
            "\"little did you know\", \"dark and stormy\", \"legends speak\", \"in a land far away\", "
            "\"a mysterious stranger approaches you\", \"ye olde\", \"bustling marketplace\".\n"
            "- Do NOT name any NPC who isn't already established.\n"
            "- Do NOT describe the hero's internal feelings as abstractions (\"you feel destiny calling\"). "
            "Show reactions through body and environment instead.\n"
            "- No headings, no quotes around the passage, no OOC commentary, no stats, no meta text.\n\n"
            "=== MANDATORY ENDING ===\n"
            "The final 1-2 sentences MUST present the player with a CONCRETE next move. Choose exactly one:\n"
            "  (A) Offer 2-3 tangible, actionable choices the hero can take RIGHT NOW (e.g., "
            "\"You can approach the hooded figure at the well, duck into the narrow side-street, "
            "or wait and watch from the shadow of the archway.\"). Write them as a natural sentence, not a list.\n"
            "  (B) Pose ONE pressing, specific question that forces an immediate decision "
            "(e.g., \"Do you follow the bloody footprints now, or turn back before the gate closes?\").\n"
            "Do NOT end on vague mood, foreshadowing, or \"the adventure begins.\" The player must "
            "know what they can do next.\n\n"
            "Output ONLY the narration paragraph."
        )

        chat = LlmChat(
            api_key=api_key,
            session_id=f"campaign-intro-{campaign_id}",
            system_message=system_message,
        )
        chat.with_model("openai", "gpt-4o-mini")

        response = await chat.send_message(UserMessage(text=prompt))
        text = (response or "").strip()
        # Strip accidental wrapping quotes if the model added them
        if text.startswith('"') and text.endswith('"') and len(text) > 2:
            text = text[1:-1].strip()
        if text:
            return {"seed": f"scene_{campaign_id[:8]}", "introText": text}
        logger.warning("AI intro returned empty text; using template fallback")
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"AI intro generation failed, using template fallback: {exc}")
    return fallback


def generate_initial_cards(campaign_id: str, intent: CampaignIntent, world: Dict, character: Dict | None) -> List[KnowledgeCard]:
    starting_location = world.get("startingLocation", {})
    race_name = _format_title(character.get("race", {}).get("key", "traveler")) if character else "traveler"
    class_name = _format_title((character.get("class", {}) or character.get("class_", {})).get("key", "adventurer")) if character else "adventurer"
    background_name = _format_title(character.get("background", {}).get("key", "wanderer")) if character else "wanderer"

    cards: List[KnowledgeCard] = [
        KnowledgeCard(
            id=str(uuid4()),
            type="place",
            title=starting_location.get("name", "Starting Point"),
            description=starting_location.get(
                "description",
                "The place where your journey begins, shaped by your chosen tone and scope.",
            ),
            tags=[intent.scope.lower(), "starting-location"],
        ),
        KnowledgeCard(
            id=str(uuid4()),
            type="npc",
            title="Local Steward",
            description=(
                "A pragmatic contact assigned to greet new arrivals and keep order. "
                f"They appreciate {intent.focus.lower()}-driven heroes."
            ),
            tags=["contact", intent.focus.lower()],
        ),
        KnowledgeCard(
            id=str(uuid4()),
            type="belief",
            title="Cultural Thread",
            description=(
                f"Stories of {race_name} traditions blend with your {background_name} upbringing, "
                "creating shared expectations about honor and duty."
            ),
            tags=[race_name.lower(), background_name.lower()],
        ),
        KnowledgeCard(
            id=str(uuid4()),
            type="quest",
            title="Opening Lead",
            description=(
                f"Rumors speak of a task suited for a {class_name}: safeguard the {starting_location.get('name', 'outpost')} "
                f"as tension rises ({intent.danger.lower()} danger)."
            ),
            tags=["quest", intent.danger.lower()],
        ),
    ]

    return cards
