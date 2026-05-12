"""
Intro narration service using NARRATOR-INTRO prompt.
"""
import json
import logging
from typing import Optional
from .llm_client import get_openai_client
from .prompts import INTRO_SYSTEM_PROMPT
from .time_service import time_context_block

logger = logging.getLogger(__name__)


def generate_intro_markdown(
    character: dict,
    region: dict,
    world_blueprint: dict,
    clock_hour: Optional[int] = None,
) -> str:
    """
    Generate a campaign intro using Matt Mercer's macro-to-micro zoom (8-12 sentences).
    
    Provides world context, political tension, and player location in a structured
    narrative that sounds like a human DM speaking at a table.
    
    Args:
        character: Character dict with name, race, class, background, goal
        region: Region dict with name, description
        world_blueprint: Complete world_blueprint JSON
        clock_hour: Optional current world clock (0-23). When provided, the
            intro will be written to match the in-fiction time-of-day. When
            omitted, the intro generator defaults to whatever the LLM
            chooses (typically dawn / morning).
        
    Returns:
        str: Plain text intro narration (8-12 sentences with world-building context)
    """
    payload = {
        "character": character,
        "region": region,
        "world_blueprint": world_blueprint,
    }

    # If the campaign has an active world clock, the intro MUST match it —
    # otherwise the player sees "dawn spills over the rooftops" while the
    # UI shows Midnight. We prepend a hard-rule time block to the system
    # prompt instead of inlining it into the payload so the LLM treats it
    # with the same weight as the rest of the rules.
    system = INTRO_SYSTEM_PROMPT
    if clock_hour is not None:
        system = (
            INTRO_SYSTEM_PROMPT
            + "\n\n"
            + time_context_block(int(clock_hour))
            + "\n\nThis intro must open AT the current time-of-day above. "
            "Choose sensory cues, NPC activities, ambient sounds, and light "
            "that match. If the period is Midnight, the streets are EMPTY of "
            "ordinary citizens — write the Watch on patrol, smugglers in "
            "shadow, a tavern's last patron stumbling home; NOT dawn light, "
            "merchants 'setting up', children, or fresh bread."
        )
    
    logger.info(
        f"Generating intro for character: {character.get('name')} "
        f"(clock_hour={clock_hour})"
    )
    
    try:
        client = get_openai_client()
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload)},
            ],
            temperature=0.7,
        )
        
        intro_md = completion.choices[0].message.content.strip()
        logger.info(f"Successfully generated intro ({len(intro_md)} chars)")
        return intro_md
        
    except Exception as e:
        logger.error(f"Error generating intro: {e}")
        raise
