"""
Advanced Quest Hook Generator Service (Multi-Stage Pipeline)
Generates concrete, actionable quest hooks from scenes using LLM-powered analysis

This replaces the basic template-driven hook generation with a sophisticated
multi-stage reasoning process that produces specific, visible, actionable hooks.
"""
import logging
import json
from typing import Dict, Any, List, Optional
from .llm_client import get_openai_client

logger = logging.getLogger(__name__)

# Advanced Hook Generation System Prompt
ADVANCED_HOOK_GENERATOR_SYSTEM_PROMPT = """You are the Advanced Quest Hook Generator for a dynamic D&D-style RPG system.
Your purpose is to transform any scene into 2–5 high-quality, actionable quest hooks that can be turned into Leads and Quests.

Follow this multi-stage reasoning process internally, but only output final JSON hooks.

------------------------------------
### STAGE 1 — Extract Scene Signals
Identify:
- Tensions (fear, secrecy, unrest, wealth, danger, hope)
- Entities present (NPCs, factions, POIs, creatures, world forces)
- Environmental anomalies (blood, graffiti, tracks, smells, sounds)
- Social patterns (whispers, crowds, arguments, evasive behavior)
- Opportunity vectors (jobs, bargains, secrets, vulnerabilities)
- Implied danger (ambush points, predators, traps, watchers)
- Factional dynamics (power struggles, territory, recruitment, surveillance)

------------------------------------
### STAGE 2 — Transform Signals Into Hook Types
Assign each potential hook to one of these categories:

- investigation: something to inspect or uncover  
- opportunity: a chance for profit, alliance, or advantage  
- threat: immediate or emerging danger  
- social: negotiation, influence, deception, or diplomacy  
- exploration: hidden routes, secret places, unknown areas  

Hooks must be **diverse**—avoid repeating the same type.

------------------------------------
### STAGE 3 — Materialize Hooks Into Actionable Prompts
A proper hook includes:
1. **A concrete trigger**  
   e.g., "a hooded courier drops a sealed letter," not "people are secretive"

2. **A reason to care**  
   e.g., it looks valuable, urgent, dangerous, or suspicious

3. **A target**  
   NPC, faction, POI, location, or world force

4. **Minimal lore invention**  
   You may create placeholder NPCs or factions if needed, but keep them simple:
   - npc:mysterious_courier
   - faction:local_smugglers
   - poi:abandoned_storehouse

Do NOT invent deep lore or large world changes.

Hooks must be **shorter, tighter, more actionable** than narration itself.

------------------------------------
### STAGE 4 — Difficulty Assessment
Estimate difficulty using:
- easy → Social encounters, simple investigations, minor tasks
- medium → Tensions, danger signs, criminal activity, pursuit, stealth
- hard → Combat, deep conspiracies, faction conflict, supernatural threats

------------------------------------
### STAGE 5 — Output Clean JSON
Return ONLY a JSON array of hooks.

Each hook object MUST match this schema:

{
  "type": "investigation" | "opportunity" | "threat" | "social" | "exploration",
  "short_text": "6–12 word actionable hook title",
  "description": "One-sentence, concrete description of the quest hook with specific visible details.",
  "source": "npc:{id} | faction:{id} | poi:{id} | world:{keyword}",
  "difficulty": "easy" | "medium" | "hard",
  "related_npcs": ["npc_id"],
  "related_locations": ["location_id"],
  "related_factions": ["faction_id"]
}

------------------------------------
### CRITICAL RULES
- Hooks must be SPECIFIC with VISIBLE details, not vague atmospherics
- Include what the player can SEE, HEAR, or OBSERVE right now
- Describe the NPC's appearance, location, and visible behavior
- Hooks must arise from the scene, not from generic templates
- Hooks must not promise future events—only describe present opportunities
- Hooks must be unique, varied, and non-repetitive
- Use world_blueprint entities if relevant, otherwise introduce light placeholders
- Make hooks IMMEDIATELY actionable (player can act on them NOW)
- Add sensory details: what they look like, where they are, what they're doing
- Do NOT mention these stages or rules in the final output

IMPORTANT: Return ONLY the JSON array. No additional text, explanations, or markdown formatting."""


def generate_advanced_hooks(
    scene_description: str,
    location_name: str,
    world_blueprint: Dict[str, Any],
    world_state: Dict[str, Any],
    character_state: Dict[str, Any],
    max_hooks: int = 4
) -> List[Dict[str, Any]]:
    """
    Generate advanced quest hooks using multi-stage LLM analysis
    
    Args:
        scene_description: The current scene narration text
        location_name: Current location name
        world_blueprint: Full world blueprint with NPCs, factions, POIs
        world_state: Current world state
        character_state: Character data for context
        max_hooks: Maximum number of hooks to generate (2-5)
        
    Returns:
        List of advanced hook dictionaries with concrete, actionable details
    """
    
    # Prepare world context
    world_context = _prepare_world_context(
        location_name,
        world_blueprint,
        world_state,
        character_state
    )
    
    # Build user prompt
    user_prompt = f"""Generate advanced quest hooks using the multi-stage hook generation model.

Scene:
{scene_description}

Location: {location_name}

World Blueprint Context:
{world_context}

Player Context:
- Name: {character_state.get('name', 'Adventurer')}
- Class: {character_state.get('class', 'Unknown')}
- Level: {character_state.get('level', 1)}
- Background: {character_state.get('background', 'Unknown')}

Generate {max_hooks} diverse, actionable quest hooks.
Return only the JSON array of hooks."""

    try:
        client = get_openai_client()
        
        completion = client.chat.completions.create(
            model="gpt-4o",  # Use full model for sophisticated reasoning
            messages=[
                {"role": "system", "content": ADVANCED_HOOK_GENERATOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,  # Higher temp for creative hook generation
            max_tokens=1500,
            response_format={"type": "json_object"}  # Force JSON output
        )
        
        raw_response = completion.choices[0].message.content.strip()
        
        # Clean markdown code blocks if present
        if raw_response.startswith("```"):
            # Remove markdown code blocks
            lines = raw_response.split("\n")
            # Remove first line (```json or ```)
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw_response = "\n".join(lines).strip()
        
        # Parse JSON response
        try:
            # Handle if response is wrapped in a root object
            parsed = json.loads(raw_response)
            if isinstance(parsed, dict) and "hooks" in parsed:
                hooks = parsed["hooks"]
            elif isinstance(parsed, list):
                hooks = parsed
            else:
                # Assume the entire object is hooks
                hooks = [parsed] if isinstance(parsed, dict) else []
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse hook JSON: {e}\nRaw response: {raw_response}")
            return _fallback_hooks(location_name, world_blueprint, world_state)
        
        # Validate and clean hooks
        validated_hooks = []
        for hook in hooks[:max_hooks]:
            if _validate_hook(hook):
                validated_hooks.append(hook)
            else:
                logger.warning(f"⚠️ Invalid hook structure, skipping: {hook}")
        
        if validated_hooks:
            logger.info(f"✅ Generated {len(validated_hooks)} advanced quest hooks for {location_name}")
            return validated_hooks
        else:
            logger.warning("⚠️ No valid hooks generated, using fallback")
            return _fallback_hooks(location_name, world_blueprint, world_state)
            
    except Exception as e:
        logger.error(f"❌ Advanced hook generation failed: {str(e)}", exc_info=True)
        return _fallback_hooks(location_name, world_blueprint, world_state)


def _prepare_world_context(
    location_name: str,
    world_blueprint: Dict[str, Any],
    world_state: Dict[str, Any],
    character_state: Dict[str, Any]
) -> str:
    """Prepare concise world context for LLM"""
    
    context_parts = []
    
    # Active NPCs
    active_npc_ids = world_state.get("active_npcs", [])
    key_npcs = world_blueprint.get("key_npcs", [])
    active_npcs = [npc for npc in key_npcs if npc.get("id") in active_npc_ids]
    
    if active_npcs:
        npc_list = []
        for npc in active_npcs[:3]:  # Limit to 3 for context brevity
            npc_list.append(
                f"- {npc.get('name')} ({npc.get('role')}) - Secret: {npc.get('secret', 'Unknown')}"
            )
        context_parts.append("Active NPCs:\n" + "\n".join(npc_list))
    
    # Nearby POIs
    pois = world_blueprint.get("points_of_interest", [])
    if pois:
        poi_list = []
        for poi in pois[:3]:
            poi_list.append(
                f"- {poi.get('name')} ({poi.get('type')}) - Hidden: {poi.get('hidden_function', 'None')}"
            )
        context_parts.append("Nearby Points of Interest:\n" + "\n".join(poi_list))
    
    # Factions
    factions = world_blueprint.get("factions", [])
    if factions:
        faction_list = []
        for faction in factions[:2]:
            faction_list.append(
                f"- {faction.get('name')}: {faction.get('public_goal', 'Unknown goal')}"
            )
        context_parts.append("Active Factions:\n" + "\n".join(faction_list))
    
    # Global threat
    global_threat = world_blueprint.get("global_threat", {})
    if global_threat:
        threat_name = global_threat.get("name", "Unknown")
        early_signs = global_threat.get("early_signs_near_starting_town", [])
        if early_signs:
            context_parts.append(f"Global Threat: {threat_name}\nEarly signs: {', '.join(early_signs[:2])}")
    
    # World state flags
    flags = []
    if world_state.get("guards_hostile"):
        flags.append("Guards are hostile")
    if world_state.get("city_hostile"):
        flags.append("City is hostile")
    if world_state.get("guard_alert"):
        flags.append("Guards on alert")
    
    if flags:
        context_parts.append("Current Situation: " + ", ".join(flags))
    
    return "\n\n".join(context_parts) if context_parts else "No specific world context available."


def _validate_hook(hook: Dict[str, Any]) -> bool:
    """Validate hook structure"""
    required_fields = ["type", "short_text", "description", "source", "difficulty"]
    
    # Check all required fields exist
    if not all(field in hook for field in required_fields):
        return False
    
    # Validate type
    valid_types = ["investigation", "opportunity", "threat", "social", "exploration"]
    if hook["type"] not in valid_types:
        return False
    
    # Validate difficulty
    valid_difficulties = ["easy", "medium", "hard"]
    if hook["difficulty"] not in valid_difficulties:
        return False
    
    # Ensure text fields are non-empty strings
    if not isinstance(hook["short_text"], str) or len(hook["short_text"]) < 5:
        return False
    
    if not isinstance(hook["description"], str) or len(hook["description"]) < 10:
        return False
    
    return True


def _fallback_hooks(
    location_name: str,
    world_blueprint: Dict[str, Any],
    world_state: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate basic fallback hooks if LLM fails
    Uses simple template-based generation
    """
    hooks = []
    
    # Try to generate at least one hook from NPCs
    active_npc_ids = world_state.get("active_npcs", [])
    key_npcs = world_blueprint.get("key_npcs", [])
    
    for npc in key_npcs:
        if npc.get("id") in active_npc_ids:
            hooks.append({
                "type": "social",
                "short_text": f"Speak with {npc.get('name', 'an NPC')}",
                "description": f"You notice {npc.get('name', 'someone')} ({npc.get('role', 'a local')}) who might have information.",
                "source": f"npc:{npc.get('id', 'unknown')}",
                "difficulty": "easy",
                "related_npcs": [npc.get("id", "")],
                "related_locations": [],
                "related_factions": []
            })
            break
    
    # Generic exploration hook
    hooks.append({
        "type": "exploration",
        "short_text": f"Explore {location_name}",
        "description": f"There are unexplored areas of {location_name} that might hold secrets or opportunities.",
        "source": f"poi:{location_name}",
        "difficulty": "easy",
        "related_npcs": [],
        "related_locations": [location_name],
        "related_factions": []
    })
    
    return hooks[:2]  # Return max 2 fallback hooks
