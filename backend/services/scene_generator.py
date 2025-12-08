"""
Dynamic Scene Generator Service
Generates contextually-aware scene descriptions for arrivals, returns, and transitions
Integrates with world_blueprint, world_state, character_state, and quest hooks
"""
import logging
from typing import Dict, Any, Optional, List
from .llm_client import get_openai_client

logger = logging.getLogger(__name__)


def generate_scene_description(
    scene_type: str,
    location: Dict[str, Any],
    character_state: Dict[str, Any],
    world_state: Dict[str, Any],
    world_blueprint: Dict[str, Any],
    available_quest_hooks: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, str]:
    """
    Generate dynamic scene description using LLM
    
    Args:
        scene_type: "arrival", "return", "transition", "time_skip"
        location: Location data from world_blueprint (starting_town or POI)
        character_state: Character data including level, background, reputation
        world_state: Current world state including time, weather, active_npcs
        world_blueprint: Full world blueprint for context
        available_quest_hooks: List of quest hooks to subtly inject
        
    Returns:
        Dict with keys: location, description, why_here
    """
    if not available_quest_hooks:
        available_quest_hooks = []
    
    location_name = location.get("name", "Unknown")
    location_role = location.get("role", "settlement")
    location_summary = location.get("summary", "A mysterious place")
    signature_products = location.get("signature_products", [])
    
    character_name = character_state.get("name", "Adventurer")
    character_level = character_state.get("level", 1)
    character_background = character_state.get("background", "wanderer")
    character_class = character_state.get("class", character_state.get("class_", "unknown"))
    
    time_of_day = world_state.get("time_of_day", "midday")
    weather = world_state.get("weather", "clear")
    
    # Get reputation context
    reputation = character_state.get("reputation", {})
    is_wanted = world_state.get("guards_hostile", False) or world_state.get("city_hostile", False)
    
    # Get nearby threats
    global_threat = world_blueprint.get("global_threat", {})
    early_signs = global_threat.get("early_signs_near_starting_town", [])
    
    # Build prompt
    prompt = build_scene_generator_prompt(
        scene_type=scene_type,
        location_name=location_name,
        location_role=location_role,
        location_summary=location_summary,
        signature_products=signature_products,
        character_name=character_name,
        character_level=character_level,
        character_background=character_background,
        character_class=character_class,
        time_of_day=time_of_day,
        weather=weather,
        is_wanted=is_wanted,
        reputation=reputation,
        early_signs=early_signs,
        quest_hooks=available_quest_hooks
    )
    
    try:
        client = get_openai_client()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # Use mini for faster/cheaper scene generation
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Generate scene description for {scene_type} at {location_name}"}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        generated_text = completion.choices[0].message.content.strip()
        
        # Parse the generated scene
        # Expected format: Location description (2-3 sentences) + arrival context (1 sentence)
        # Split into description and why_here
        sentences = generated_text.split(". ")
        
        if len(sentences) >= 2:
            # Last sentence is "why_here", rest is description
            description = ". ".join(sentences[:-1]) + "."
            why_here = sentences[-1].strip()
            if not why_here.endswith('.'):
                why_here += "."
        else:
            # Fallback: use whole text as description, generate simple why_here
            description = generated_text
            why_here = f"You arrive in {location_name}, ready for whatever awaits."
        
        logger.info(f"✅ Generated dynamic scene for {location_name} ({scene_type})")
        
        return {
            "location": location_name,
            "description": description,
            "why_here": why_here
        }
        
    except Exception as e:
        logger.error(f"❌ Scene generation failed: {e}")
        # Fallback to simple template
        return {
            "location": location_name,
            "description": location_summary,
            "why_here": f"You have arrived in {location_name} seeking adventure and fortune. The world awaits your choices."
        }


def build_scene_generator_prompt(
    scene_type: str,
    location_name: str,
    location_role: str,
    location_summary: str,
    signature_products: List[str],
    character_name: str,
    character_level: int,
    character_background: str,
    character_class: str,
    time_of_day: str,
    weather: str,
    is_wanted: bool,
    reputation: Dict[str, Any],
    early_signs: List[str],
    quest_hooks: List[Dict[str, Any]]
) -> str:
    """Build system prompt for scene generation"""
    
    # Determine character experience level
    experience_level = "inexperienced" if character_level <= 3 else "seasoned" if character_level <= 7 else "legendary"
    
    # Format quest hooks
    hooks_text = ""
    if quest_hooks:
        hooks_list = []
        for hook in quest_hooks[:2]:  # Max 2 hooks per scene
            hook_type = hook.get("type", "conversation")
            hook_desc = hook.get("description", "")
            hooks_list.append(f"- {hook_type.capitalize()}: {hook_desc}")
        hooks_text = "\n".join(hooks_list)
    
    # Format signature products
    products_text = ", ".join(signature_products[:3]) if signature_products else "various goods"
    
    prompt = f"""UNIFIED DM SYSTEM PROMPT v6.0 (Scene Generation Mode)

SYSTEM

Scene generation for arrivals, returns, and transitions.

Apply unified v6.0 rules:

Strict second-person POV

6-8 sentence limit (travel mode)

No omniscience

No invented emotions

Vivid but concise

End with agency

CONTEXT

Scene Type: {scene_type}

Location: {location_name} ({location_role})

Description: {location_summary}

Known For: {products_text}

Time: {time_of_day}

Weather: {weather}

Character: {character_name} (Level {character_level} {character_class})

Background: {character_background}

Wanted Status: {"YES - guards watching" if is_wanted else "No"}

{"Quest Hooks Available:" if quest_hooks else ""}
{hooks_text if quest_hooks else ""}

{"Threat Signs:" if early_signs else ""}
{chr(10).join([f"- {sign}" for sign in early_signs[:2]]) if early_signs else ""}

OUTPUT

Write 6-8 sentences:

Opening sensory detail (time/weather appropriate)

Three spatial cues (left, right, ahead)

Brief arrival narration

End with: "What do you do?"

RESTRICTIONS

Second person only

No flowery language

No clichés

No invented emotions

Concrete nouns only

Generate scene description now:"""
    
    return prompt
