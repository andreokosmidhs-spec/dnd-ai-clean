"""
Scene and Hook Integration Service
Orchestrates the flow: Scene Generation → Advanced Hook Generation → Embed Hooks in Narration → Lead Extraction
"""
import logging
from typing import Dict, Any, List, Optional
from .scene_generator import generate_scene_description
from .advanced_hook_generator import generate_advanced_hooks
from .embedded_hook_narrator import generate_narration_with_embedded_hooks

logger = logging.getLogger(__name__)


async def generate_scene_with_advanced_hooks(
    scene_type: str,
    location: Dict[str, Any],
    character_state: Dict[str, Any],
    world_state: Dict[str, Any],
    world_blueprint: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Complete scene generation pipeline with advanced quest hooks EMBEDDED in narration
    
    Flow:
    1. Generate initial atmospheric scene description
    2. Generate advanced quest hooks FROM the scene
    3. Re-generate narration WITH hooks embedded naturally into the prose
    4. Return narration with embedded hooks + hooks for Campaign Log
    
    Args:
        scene_type: "arrival", "return", "transition", "time_skip"
        location: Location data from world_blueprint
        character_state: Character data
        world_state: Current world state
        world_blueprint: Full world blueprint
        
    Returns:
        Dict with keys:
            - location: str
            - description: str (scene text WITH embedded hooks)
            - why_here: str
            - quest_hooks: List[Dict] (advanced hooks for Campaign Log)
    """
    
    location_name = location.get("name", "Unknown")
    
    # STEP 1: Generate initial atmospheric scene description
    scene_data = generate_scene_description(
        scene_type=scene_type,
        location=location,
        character_state=character_state,
        world_state=world_state,
        world_blueprint=world_blueprint,
        available_quest_hooks=None
    )
    
    initial_scene_description = scene_data.get("description", "")
    
    logger.info(f"📖 Generated initial scene description for {location_name}")
    
    # STEP 2: Generate advanced quest hooks FROM the scene
    try:
        advanced_hooks = generate_advanced_hooks(
            scene_description=initial_scene_description,
            location_name=location_name,
            world_blueprint=world_blueprint,
            world_state=world_state,
            character_state=character_state,
            max_hooks=4
        )
        
        logger.info(f"🎯 Generated {len(advanced_hooks)} advanced quest hooks for {location_name}")
        
    except Exception as e:
        logger.error(f"❌ Failed to generate advanced hooks: {e}")
        advanced_hooks = []
    
    # STEP 3: Re-generate narration WITH hooks embedded naturally
    if advanced_hooks:
        try:
            # Get time and weather context
            time_of_day = world_state.get("time_of_day", "midday")
            weather = world_state.get("weather", "clear")
            
            embedded_narration = generate_narration_with_embedded_hooks(
                location=location,
                scene_type=scene_type,
                character_state=character_state,
                world_state=world_state,
                quest_hooks=advanced_hooks,
                time_of_day=time_of_day,
                weather=weather
            )
            
            logger.info(f"✨ Generated narration with {len(advanced_hooks)} hooks embedded for {location_name}")
            
            final_description = embedded_narration
            
        except Exception as e:
            logger.error(f"❌ Failed to embed hooks into narration: {e}")
            # Fallback to initial scene description
            final_description = initial_scene_description
    else:
        final_description = initial_scene_description
    
    # STEP 4: Return combined result
    return {
        "location": scene_data.get("location", location_name),
        "description": final_description,  # Narration with embedded hooks
        "why_here": scene_data.get("why_here", ""),
        "quest_hooks": advanced_hooks  # Hooks for Campaign Log
    }


def convert_hooks_to_lead_deltas(
    hooks: List[Dict[str, Any]],
    location_id: str,
    scene_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Convert advanced quest hooks into LeadDelta format for Campaign Log
    
    Args:
        hooks: List of advanced hooks from generate_advanced_hooks()
        location_id: Current location ID
        scene_id: Optional scene identifier
        
    Returns:
        List of LeadDelta-compatible dictionaries
    """
    lead_deltas = []
    
    for idx, hook in enumerate(hooks):
        # Generate unique lead ID
        lead_id = f"lead_{location_id.lower().replace(' ', '_')}_{hook.get('type', 'unknown')}_{idx}"
        
        # Map hook to LeadDelta format
        lead_delta = {
            "id": lead_id,
            "short_text": hook.get("short_text", "Unknown lead"),
            "location_id": location_id,
            "source_scene_id": scene_id,
            "source_type": hook.get("type", "observation"),  # Use hook type as source type
            "status": "unexplored",
            "related_npc_ids": hook.get("related_npcs", []),
            "related_location_ids": hook.get("related_locations", []),
            "related_faction_ids": hook.get("related_factions", [])
        }
        
        lead_deltas.append(lead_delta)
    
    logger.info(f"✅ Converted {len(lead_deltas)} hooks to lead deltas")
    
    return lead_deltas
