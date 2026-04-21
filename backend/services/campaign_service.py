from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4
import logging

from models.campaign_models import CampaignIntent, KnowledgeCard

logger = logging.getLogger(__name__)


def _format_title(text: str) -> str:
    return text.replace("_", " ").title()


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

    return {
        "summary": summary,
        "tags": [intent.tone.lower(), intent.focus.lower(), intent.scope.lower(), intent.danger.lower()],
        "startingLocation": starting_location,
        "theme": intent.focus,
        "tone": intent.tone,
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

        hero_bits: List[str] = []
        if character:
            identity = character.get("identity") or {}
            race = character.get("race") or {}
            class_info = character.get("class") or character.get("class_") or {}
            bg = character.get("background") or {}
            appearance = character.get("appearance") or {}
            name = identity.get("name") or "the adventurer"
            race_name = _format_title(race.get("key", "human"))
            class_name = _format_title(class_info.get("key", "adventurer"))
            bg_name = _format_title(bg.get("key", "drifter"))
            hero_bits.append(f"{name}, a {race_name} {class_name} ({bg_name} background)")
            notable = appearance.get("notableFeatures") or []
            if notable:
                hero_bits.append("notable features: " + ", ".join(notable))

        prompt = (
            "Write a short cinematic campaign OPENING narration for a Dungeons & Dragons 5e session.\n\n"
            f"Tone: {intent.tone}\nFocus: {intent.focus}\nScope: {intent.scope}\nDanger: {intent.danger}\n"
            f"Starting location: {location_name} — {starting_location.get('description', '')}\n"
            f"World theme: {world.get('theme', 'mixed')} | world tone: {world.get('tone', 'mixed')}\n"
            f"Hero: {'; '.join(hero_bits) if hero_bits else 'unknown traveler'}\n\n"
            "REQUIREMENTS:\n"
            "- 110-160 words, exactly one paragraph, written in SECOND PERSON (\"you\").\n"
            "- Vivid sensory detail: sight, sound, smell — ground the reader in the scene.\n"
            "- Introduce the starting location and a subtle hook (a rumor, a stranger, a tension in the air).\n"
            "- End on a small cliff of intrigue that invites the player's first action.\n"
            "- DO NOT name NPCs who aren't established; keep the hook vague enough for the DM to develop.\n"
            "- Output ONLY the narration text. No headings, no quotes, no meta commentary."
        )

        chat = LlmChat(
            api_key=api_key,
            session_id=f"campaign-intro-{campaign_id}",
            system_message="You are a master D&D storyteller writing cinematic campaign openings.",
        )
        chat.with_model("openai", "gpt-4o-mini")

        response = await chat.send_message(UserMessage(text=prompt))
        text = (response or "").strip()
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
