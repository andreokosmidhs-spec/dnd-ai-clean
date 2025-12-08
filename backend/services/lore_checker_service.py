"""
LORE CHECKER Service - Deterministic validation of narration against world blueprint.
No LLM calls - purely rule-based validation and correction.
"""
import re
import logging
from typing import Dict, List, Any, Set, Tuple

logger = logging.getLogger(__name__)


def extract_names_from_narration(narration: str) -> Dict[str, Set[str]]:
    """
    Extract potential NPC names, place names, and faction names from narration.
    Uses simple heuristics: capitalized words/phrases.
    
    Returns:
        {
            "potential_npcs": set of capitalized names,
            "potential_places": set of capitalized names,
            "potential_factions": set of capitalized names/phrases
        }
    """
    # Find all capitalized words (potential proper nouns)
    # Pattern: words that start with capital letter, may include spaces for multi-word names
    capitalized_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    matches = re.findall(capitalized_pattern, narration)
    
    # P2.5: Expanded stopword list to reduce false positives
    common_words = {
        # Pronouns
        "You", "I", "He", "She", "They", "We", "It", "Them", "Him", "Her", "Me",
        # Determiners
        "The", "A", "An", "This", "That", "These", "Those",
        # Possessives
        "Your", "My", "His", "Her", "Their", "Our", "Its",
        # Question words
        "What", "Where", "When", "Why", "How", "Who", "Which",
        # Common generic nouns that get capitalized
        "Market", "Tavern", "Inn", "Guard", "Fog", "Mist", "Gate", "Wall", "Tower",
        "Street", "Road", "Path", "Square", "Hall", "Court", "Bridge", "River",
        "Forest", "Mountain", "Sea", "Ocean", "Lake", "City", "Town", "Village",
        # Common verbs/actions that might start sentences
        "As", "But", "If", "Though", "While", "After", "Before", "During",
        # Time/direction
        "North", "South", "East", "West", "Morning", "Evening", "Night", "Day"
    }
    
    potential_names = set([m for m in matches if m not in common_words])
    
    return {
        "potential_npcs": potential_names,
        "potential_places": potential_names,
        "potential_factions": potential_names
    }


def build_blueprint_lookup(world_blueprint: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build fast lookup tables from world_blueprint.
    
    Returns:
        {
            "npcs": {name: npc_data},
            "places": {name: place_data},
            "factions": {name: faction_data}
        }
    """
    npcs = {}
    places = {}
    factions = {}
    
    # Extract NPCs
    for npc in world_blueprint.get("key_npcs", []):
        name = npc.get("name", "")
        if name:
            npcs[name] = npc
    
    # Extract places (starting_town + points_of_interest)
    starting_town = world_blueprint.get("starting_town", {})
    if starting_town.get("name"):
        places[starting_town["name"]] = starting_town
    
    for poi in world_blueprint.get("points_of_interest", []):
        name = poi.get("name", "")
        if name:
            places[name] = poi
    
    # Also add starting region
    starting_region = world_blueprint.get("starting_region", {})
    if starting_region.get("name"):
        places[starting_region["name"]] = starting_region
    
    # Extract factions
    for faction in world_blueprint.get("factions", []):
        name = faction.get("name", "")
        if name:
            factions[name] = faction
    
    return {
        "npcs": npcs,
        "places": places,
        "factions": factions
    }


def find_best_substitute(
    unknown_name: str,
    category: str,
    blueprint_lookup: Dict[str, Any],
    world_state: Dict[str, Any]
) -> Tuple[str, str]:
    """
    Find a safe substitute for an unknown name.
    
    Args:
        unknown_name: The name that wasn't found in blueprint
        category: "npcs", "places", or "factions"
        blueprint_lookup: Lookup tables from build_blueprint_lookup()
        world_state: Current world state (for context like active_npcs, current_location)
    
    Returns:
        (substitute_name, reason) or (unknown_name, "no_safe_substitute")
    """
    valid_entries = blueprint_lookup.get(category, {})
    
    if not valid_entries:
        return unknown_name, "no_safe_substitute"
    
    # Strategy 1: If we're talking about NPCs, prefer active NPCs
    if category == "npcs":
        active_npcs = world_state.get("active_npcs", [])
        for npc_name in active_npcs:
            if npc_name in valid_entries:
                logger.info(f"Substituting unknown NPC '{unknown_name}' with active NPC '{npc_name}'")
                return npc_name, f"substituted_with_active_npc"
    
    # Strategy 2: If we're talking about places, prefer current location
    if category == "places":
        current_location = world_state.get("current_location", "")
        if current_location and current_location in valid_entries:
            logger.info(f"Substituting unknown place '{unknown_name}' with current location '{current_location}'")
            return current_location, f"substituted_with_current_location"
    
    # Strategy 3: Use first valid entry as fallback (safest generic option)
    # Only do this if the unknown name is very similar (risky otherwise)
    # For now, we'll NOT auto-substitute blindly - just flag the issue
    
    return unknown_name, "no_safe_substitute"


def check_lore_consistency(
    narration: str,
    world_blueprint: Dict[str, Any],
    world_state: Dict[str, Any],
    auto_correct: bool = False
) -> Dict[str, Any]:
    """
    Check if narration is consistent with world_blueprint.
    
    P2.5: Runs in "soft mode" by default - detects issues but does NOT auto-correct.
    Auto-correction can be enabled via the auto_correct flag.
    
    Args:
        narration: The DM narration to validate
        world_blueprint: The static world definition
        world_state: Current mutable world state
        auto_correct: If True, attempts safe auto-corrections (default: False)
    
    Returns:
        {
            "valid": bool,
            "issues": [string],
            "corrected_narration": string,
            "corrections_made": int
        }
    """
    # Build lookup tables
    blueprint_lookup = build_blueprint_lookup(world_blueprint)
    
    # Extract names from narration
    extracted = extract_names_from_narration(narration)
    
    issues = []
    corrections_made = 0
    corrected_narration = narration
    
    # Check NPCs
    for potential_npc in extracted["potential_npcs"]:
        if potential_npc not in blueprint_lookup["npcs"]:
            # Check if it's a place or faction (common confusion)
            if potential_npc in blueprint_lookup["places"] or potential_npc in blueprint_lookup["factions"]:
                continue  # Not an NPC, but valid entity
            
            # P2.5: Only auto-correct if explicitly enabled
            if auto_correct:
                # Try to find substitute
                substitute, reason = find_best_substitute(
                    potential_npc, "npcs", blueprint_lookup, world_state
                )
                
                if reason != "no_safe_substitute":
                    # Safe to substitute
                    corrected_narration = corrected_narration.replace(potential_npc, substitute)
                    corrections_made += 1
                    issues.append(f"Auto-corrected unknown NPC '{potential_npc}' → '{substitute}'")
                else:
                    # Flag but don't break
                    issues.append(f"Warning: Unknown NPC '{potential_npc}' not in blueprint")
            else:
                # Soft mode: just flag, don't correct
                issues.append(f"Unknown NPC '{potential_npc}' not in blueprint")
    
    # Check places
    for potential_place in extracted["potential_places"]:
        if potential_place not in blueprint_lookup["places"]:
            # Check if it's an NPC or faction
            if potential_place in blueprint_lookup["npcs"] or potential_place in blueprint_lookup["factions"]:
                continue
            
            # P2.5: Only auto-correct if explicitly enabled
            if auto_correct:
                # Try to find substitute
                substitute, reason = find_best_substitute(
                    potential_place, "places", blueprint_lookup, world_state
                )
                
                if reason != "no_safe_substitute":
                    corrected_narration = corrected_narration.replace(potential_place, substitute)
                    corrections_made += 1
                    issues.append(f"Auto-corrected unknown place '{potential_place}' → '{substitute}'")
                else:
                    issues.append(f"Unknown place '{potential_place}' not in blueprint")
            else:
                # Soft mode: just flag, don't correct
                issues.append(f"Unknown place '{potential_place}' not in blueprint")
    
    # Check factions
    for potential_faction in extracted["potential_factions"]:
        if potential_faction not in blueprint_lookup["factions"]:
            if potential_faction in blueprint_lookup["npcs"] or potential_faction in blueprint_lookup["places"]:
                continue
            
            # For factions, we're conservative - only flag multi-word names (more likely to be factions)
            if len(potential_faction.split()) > 1:
                issues.append(f"Possible unknown faction '{potential_faction}' not in blueprint")
    
    # Determine validity (P2.5: soft mode means issues don't invalidate, just warn)
    # Only mark as invalid if there are critical unknown entities AND auto_correct is enabled
    if auto_correct:
        critical_issues = [i for i in issues if "Auto-corrected" not in i]
        valid = len(critical_issues) == 0
    else:
        # Soft mode: always mark as valid, issues are just warnings
        valid = True
    
    if issues:
        mode = "auto-correct ON" if auto_correct else "soft mode (warnings only)"
        logger.info(f"🔍 LORE CHECKER ({mode}): Found {len(issues)} issues, made {corrections_made} corrections")
        for issue in issues[:5]:  # Limit log spam to first 5 issues
            logger.info(f"   - {issue}")
        if len(issues) > 5:
            logger.info(f"   ... and {len(issues) - 5} more issues")
    else:
        logger.info(f"🔍 LORE CHECKER: No issues found, narration is consistent")
    
    return {
        "valid": valid,
        "issues": issues,
        "corrected_narration": corrected_narration,
        "corrections_made": corrections_made
    }
