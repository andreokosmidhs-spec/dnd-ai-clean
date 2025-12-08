"""
World generation service using WORLD-FORGE prompt.
"""
import json
import logging
from .llm_client import get_openai_client
from .prompts import WORLD_FORGE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def generate_world_blueprint(world_name: str, tone: str, starting_region_hint: str) -> dict:
    """
    Generate a complete world blueprint JSON using WORLD-FORGE.
    
    Args:
        world_name: Name of the world/continent
        tone: Overall tone (e.g., "Dark fantasy with rare magic")
        starting_region_hint: Brief description of starting region
        
    Returns:
        dict: Complete world_blueprint matching schema
        
    Raises:
        ValueError: If LLM returns invalid JSON
    """
    user_content = {
        "world_name": world_name,
        "tone": tone,
        "starting_region_hint": starting_region_hint,
    }
    
    logger.info(f"Generating world blueprint for: {world_name}")
    
    try:
        client = get_openai_client()
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": WORLD_FORGE_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_content)},
            ],
            temperature=0.7,
        )
        
        raw = completion.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        
        world_blueprint = json.loads(raw)
        logger.info(f"Successfully generated world blueprint for {world_name}")
        return world_blueprint
        
    except json.JSONDecodeError as e:
        logger.error(f"WORLD_FORGE returned invalid JSON: {e}")
        logger.error(f"Raw output: {raw[:500]}")
        raise ValueError(f"WORLD_FORGE did not return valid JSON: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating world blueprint: {e}")
        raise
