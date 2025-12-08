"""
Intro narration service using NARRATOR-INTRO prompt.
"""
import json
import logging
from .llm_client import get_openai_client
from .prompts import INTRO_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def generate_intro_markdown(
    character: dict,
    region: dict,
    world_blueprint: dict
) -> str:
    """
    Generate a campaign intro using Matt Mercer's macro-to-micro zoom (8-12 sentences).
    
    Provides world context, political tension, and player location in a structured
    narrative that sounds like a human DM speaking at a table.
    
    Args:
        character: Character dict with name, race, class, background, goal
        region: Region dict with name, description
        world_blueprint: Complete world_blueprint JSON
        
    Returns:
        str: Plain text intro narration (8-12 sentences with world-building context)
    """
    payload = {
        "character": character,
        "region": region,
        "world_blueprint": world_blueprint,
    }
    
    logger.info(f"Generating intro for character: {character.get('name')}")
    
    try:
        client = get_openai_client()
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": INTRO_SYSTEM_PROMPT},
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
