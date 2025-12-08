"""
DC (Difficulty Class) Calculator Service
Determines appropriate DCs for skill checks based on D&D 5e guidelines
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# D&D 5e DC Guidelines
DC_GUIDELINES = {
    "very_easy": 5,     # Almost anyone can do this
    "easy": 10,          # Routine task for someone trained
    "medium": 15,        # Requires skill and focus
    "hard": 20,          # Difficult even for experts
    "very_hard": 25,     # Nearly impossible
    "nearly_impossible": 30  # Legendary difficulty
}

# Context-based DC adjustments
CONTEXT_MODIFIERS = {
    "combat": +2,              # Things are harder in combat
    "distraction": +2,         # Loud environment, crowds
    "time_pressure": +3,       # Racing against time
    "darkness": +5,            # Can't see well
    "magical_interference": +3, # Magical wards, counterspells
    "favorable_conditions": -2, # Perfect setup, tools, prep time
    "help_from_ally": -2,      # Someone helping
}


def calculate_dc(
    action_description: str,
    base_difficulty: str = "medium",
    context: Optional[Dict[str, Any]] = None,
    character_level: int = 1
) -> int:
    """
    Calculate appropriate DC for a skill check
    
    Args:
        action_description: What the player is trying to do
        base_difficulty: "very_easy", "easy", "medium", "hard", "very_hard", "nearly_impossible"
        context: Dict with keys like "in_combat", "time_pressure", "has_tools", etc.
        character_level: Player level (for scaling challenges)
        
    Returns:
        DC value (int)
    """
    
    # Start with base DC
    base_dc = DC_GUIDELINES.get(base_difficulty, DC_GUIDELINES["medium"])
    
    # Apply context modifiers
    final_dc = base_dc
    if context:
        if context.get("in_combat"):
            final_dc += CONTEXT_MODIFIERS["combat"]
        if context.get("distracted") or context.get("loud_environment"):
            final_dc += CONTEXT_MODIFIERS["distraction"]
        if context.get("time_pressure") or context.get("rushing"):
            final_dc += CONTEXT_MODIFIERS["time_pressure"]
        if context.get("darkness") or context.get("poor_visibility"):
            final_dc += CONTEXT_MODIFIERS["darkness"]
        if context.get("magical_interference"):
            final_dc += CONTEXT_MODIFIERS["magical_interference"]
        if context.get("favorable_conditions") or context.get("perfect_setup"):
            final_dc += CONTEXT_MODIFIERS["favorable_conditions"]
        if context.get("has_help") or context.get("ally_helping"):
            final_dc += CONTEXT_MODIFIERS["help_from_ally"]
    
    # Level-based scaling (optional)
    # Make challenges slightly harder for high-level characters
    if character_level >= 10:
        final_dc += 2
    elif character_level >= 15:
        final_dc += 3
    
    # Clamp DC between 5 and 30
    final_dc = max(5, min(30, final_dc))
    
    logger.info(f"📊 Calculated DC: {final_dc} (base: {base_difficulty} = {base_dc}, context adjustments: {final_dc - base_dc})")
    
    return final_dc


def infer_dc_from_action(
    action: str,
    world_state: Optional[Dict[str, Any]] = None,
    character_level: int = 1
) -> int:
    """
    Infer appropriate DC from action description using heuristics
    
    Args:
        action: Player's action description
        world_state: Current world state (for context)
        character_level: Player level
        
    Returns:
        DC value (int)
    """
    
    action_lower = action.lower()
    
    # Detect base difficulty from keywords
    base_difficulty = "medium"  # Default
    
    # Very Easy (DC 5)
    if any(word in action_lower for word in ["casual", "simple", "basic", "easy", "routine"]):
        base_difficulty = "very_easy"
    
    # Easy (DC 10)
    elif any(word in action_lower for word in ["carefully", "take my time", "prepared"]):
        base_difficulty = "easy"
    
    # Hard (DC 20)
    elif any(word in action_lower for word in ["difficult", "tricky", "complex", "dangerous"]):
        base_difficulty = "hard"
    
    # Very Hard (DC 25)
    elif any(word in action_lower for word in ["impossible", "legendary", "master"]):
        base_difficulty = "very_hard"
    
    # Detect context modifiers
    context = {}
    
    if any(word in action_lower for word in ["quietly", "stealthily", "sneakily", "unnoticed"]):
        # Stealth actions are harder in noisy environments
        if world_state and world_state.get("environment_noise") == "loud":
            context["distracted"] = True
    
    if any(word in action_lower for word in ["quickly", "fast", "hurry", "rush"]):
        context["time_pressure"] = True
    
    if world_state:
        if world_state.get("in_combat"):
            context["in_combat"] = True
        if world_state.get("visibility") == "dark":
            context["darkness"] = True
    
    # Calculate final DC
    dc = calculate_dc(
        action_description=action,
        base_difficulty=base_difficulty,
        context=context,
        character_level=character_level
    )
    
    return dc


# DC Guidelines for DM Prompt
DC_GUIDELINES_TEXT = """
## DC (Difficulty Class) Guidelines

When requesting ability checks, set appropriate DCs using these guidelines:

**DC 5** (Very Easy): Almost anyone can do this
- Climb a knotted rope
- Notice something large in plain sight
- Follow fresh tracks in snow

**DC 10** (Easy): Routine task for someone trained
- Climb a rope with knots
- Hear an approaching guard
- Spot a hidden door that's marked

**DC 15** (Medium): Requires skill and focus  
- Climb a rough rock surface
- Pick a simple lock
- Sneak past an alert guard

**DC 20** (Hard): Difficult even for experts
- Climb a slippery cliff face
- Pick a complex lock
- Forge a royal seal

**DC 25** (Very Hard): Nearly impossible
- Climb a smooth wall
- Pick a masterwork lock
- Leap across a 25-foot chasm

**DC 30** (Nearly Impossible): Legendary difficulty
- Climb an ice-covered wall
- Remember an ancient forgotten language
- Swim against a waterfall

### Context Modifiers:
- **In Combat**: +2 DC (harder to focus)
- **Time Pressure**: +3 DC (rushing makes mistakes)
- **Darkness/Poor Visibility**: +5 DC (can't see well)
- **Distraction/Noise**: +2 DC (loud environment)
- **Favorable Conditions**: -2 DC (perfect setup, tools, prep)
- **Help from Ally**: -2 DC (someone assisting)

### Examples:
- "Sneak past a guard" → DC 15 (Medium stealth)
- "Sneak past a guard in combat" → DC 17 (Medium + combat)
- "Quickly pick a lock while guards approach" → DC 18 (Medium + time pressure)
- "Climb a wet rope in darkness" → DC 20 (Easy climb + darkness + slippery)
"""


def get_dc_guidelines_for_prompt() -> str:
    """Return DC guidelines text for inclusion in DM system prompt"""
    return DC_GUIDELINES_TEXT
