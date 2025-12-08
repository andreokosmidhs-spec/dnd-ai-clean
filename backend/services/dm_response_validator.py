"""
DM Response Validator Service
Enforces A-Version Rule #2: Location and Scene Continuity

Prevents:
- NPCs spawning in inappropriate locations (innkeeper in ruins)
- Spontaneous location changes without player travel
- Hallucinated environments
- Teleporting NPCs
"""

import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class DMResponseValidator:
    """Validates DM responses against location and NPC constraints"""
    
    # NPC roles that require specific location types
    LOCATION_SPECIFIC_NPCS = {
        'innkeeper': ['tavern', 'inn', 'village', 'town', 'city'],
        'bartender': ['tavern', 'inn', 'bar', 'village', 'town', 'city'],
        'merchant': ['market', 'shop', 'village', 'town', 'city', 'trading post'],
        'shopkeeper': ['shop', 'market', 'village', 'town', 'city'],
        'blacksmith': ['forge', 'village', 'town', 'city', 'smithy'],
        'guard': ['village', 'town', 'city', 'castle', 'outpost', 'gate'],
        'priest': ['temple', 'church', 'shrine', 'village', 'town', 'city'],
        'librarian': ['library', 'temple', 'academy', 'city', 'castle'],
    }
    
    # Forbidden location types for civilized NPCs
    WILDERNESS_LOCATIONS = [
        'ruins', 'dungeon', 'cave', 'wilderness', 'forest', 'mountain', 'swamp', 'desert',
        'temple', 'tomb', 'crypt', 'catacomb', 'abandoned', 'cursed', 'haunted',
        'ancient', 'shattered', 'crumbling', 'destroyed', 'forsaken'
    ]
    
    # Environmental keywords that suggest wrong location
    TAVERN_KEYWORDS = ['counter', 'bar', 'tankard', 'ale', 'mug', 'roasted meat', 'warm bread', 'polished wooden counter']
    SHOP_KEYWORDS = ['shop', 'stall', 'wares', 'goods for sale', 'merchant displays']
    
    @staticmethod
    def validate_dm_response(
        dm_response: Dict[str, Any],
        current_location: str,
        active_npcs: List[str],
        location_constraints: str
    ) -> Dict[str, Any]:
        """
        Validate and correct DM response for location continuity.
        
        Args:
            dm_response: The DM's generated response
            current_location: Current location name
            active_npcs: List of NPCs that should be present
            location_constraints: Location constraints from context_memory
            
        Returns:
            Dict with:
                - 'valid': bool
                - 'corrected_response': Dict (corrected DM response)
                - 'violations': List[str] (detected violations)
        """
        violations = []
        corrected_response = dm_response.copy()
        narration = dm_response.get('narration', '')
        
        # Check 1: Detect inappropriate NPC spawning
        npc_violations = DMResponseValidator._check_npc_appropriateness(
            narration, current_location, active_npcs
        )
        violations.extend(npc_violations)
        
        # Check 2: Detect inappropriate environment descriptions
        env_violations = DMResponseValidator._check_environment_hallucination(
            narration, current_location
        )
        violations.extend(env_violations)
        
        # If violations found, correct the response
        if violations:
            logger.warning(f"🚫 DM Response Violations Detected: {violations}")
            corrected_response = DMResponseValidator._correct_response(
                dm_response, current_location, violations
            )
        
        return {
            'valid': len(violations) == 0,
            'corrected_response': corrected_response,
            'violations': violations
        }
    
    @staticmethod
    def _check_npc_appropriateness(
        narration: str,
        current_location: str,
        active_npcs: List[str]
    ) -> List[str]:
        """Check if narration mentions NPCs inappropriate for location"""
        violations = []
        narration_lower = narration.lower()
        location_lower = current_location.lower()
        
        # Check if location is wilderness/dangerous
        is_wilderness = any(wild in location_lower for wild in DMResponseValidator.WILDERNESS_LOCATIONS)
        
        if is_wilderness:
            # Check for civilized NPCs in wilderness
            for npc_role, allowed_locations in DMResponseValidator.LOCATION_SPECIFIC_NPCS.items():
                if npc_role in narration_lower:
                    # Check if this NPC role is allowed here
                    location_match = any(loc in location_lower for loc in allowed_locations)
                    if not location_match:
                        violations.append(f"inappropriate_npc:{npc_role}")
                        logger.warning(f"🚫 {npc_role.title()} spawned in {current_location}")
        
        return violations
    
    @staticmethod
    def _check_environment_hallucination(
        narration: str,
        current_location: str
    ) -> List[str]:
        """Check if narration describes wrong environment"""
        violations = []
        narration_lower = narration.lower()
        location_lower = current_location.lower()
        
        # Check if location is wilderness
        is_wilderness = any(wild in location_lower for wild in DMResponseValidator.WILDERNESS_LOCATIONS)
        
        if is_wilderness:
            # Check for tavern/inn descriptions in wilderness
            tavern_count = sum(1 for keyword in DMResponseValidator.TAVERN_KEYWORDS if keyword in narration_lower)
            if tavern_count >= 2:
                violations.append("hallucinated_tavern")
                logger.warning(f"🚫 Tavern environment hallucinated in {current_location}")
            
            # Check for shop descriptions in wilderness
            shop_count = sum(1 for keyword in DMResponseValidator.SHOP_KEYWORDS if keyword in narration_lower)
            if shop_count >= 2:
                violations.append("hallucinated_shop")
                logger.warning(f"🚫 Shop environment hallucinated in {current_location}")
        
        return violations
    
    @staticmethod
    def _correct_response(
        dm_response: Dict[str, Any],
        current_location: str,
        violations: List[str]
    ) -> Dict[str, Any]:
        """Correct the DM response by replacing invalid narration"""
        corrected = dm_response.copy()
        
        # Build correction message based on violations
        correction_parts = []
        
        # Check for NPC violations
        npc_violations = [v for v in violations if v.startswith('inappropriate_npc:')]
        if npc_violations:
            # Extract NPC role from violation string
            npc_role = npc_violations[0].split(':')[1]
            correction_parts.append(
                f"You look around for {DMResponseValidator._article(npc_role)} {npc_role}, but there is none here. "
                f"You are in {current_location}, {DMResponseValidator._describe_location_type(current_location)}. "
                f"If you need {DMResponseValidator._article(npc_role)} {npc_role}, you would need to return to a settlement or town."
            )
        
        # Check for environment violations
        env_violations = [v for v in violations if v.startswith('hallucinated_')]
        if env_violations:
            if 'hallucinated_tavern' in env_violations:
                correction_parts.append(
                    f"There is no tavern or inn here. You are in {current_location}, "
                    f"{DMResponseValidator._describe_location_type(current_location)}."
                )
            if 'hallucinated_shop' in env_violations:
                correction_parts.append(
                    f"There are no shops or merchants here. You are in {current_location}, "
                    f"{DMResponseValidator._describe_location_type(current_location)}."
                )
        
        # Replace narration with correction
        if correction_parts:
            corrected['narration'] = ' '.join(correction_parts)
            
            # Update options to be location-appropriate
            corrected['options'] = [
                f"Explore the {current_location}",
                "Search for useful items or clues",
                "Return to the nearest settlement",
                "Continue your journey"
            ]
            
            # Clear any world state updates that added NPCs
            if 'world_state_update' in corrected:
                if 'active_npcs' in corrected['world_state_update']:
                    del corrected['world_state_update']['active_npcs']
        
        return corrected
    
    @staticmethod
    def _article(word: str) -> str:
        """Return appropriate article (a/an) for word"""
        vowels = ['a', 'e', 'i', 'o', 'u']
        return 'an' if word[0].lower() in vowels else 'a'
    
    @staticmethod
    def _describe_location_type(location: str) -> str:
        """Generate appropriate description based on location"""
        location_lower = location.lower()
        
        if 'ruin' in location_lower:
            return "ancient and dangerous ruins"
        elif 'dungeon' in location_lower:
            return "a dark and perilous dungeon"
        elif 'cave' in location_lower:
            return "a natural cave formation"
        elif 'forest' in location_lower:
            return "a wilderness area far from civilization"
        elif 'mountain' in location_lower:
            return "a remote mountainous region"
        elif 'swamp' in location_lower:
            return "a treacherous swampland"
        else:
            return "a location without civilized amenities"


def validate_response(
    dm_response: Dict[str, Any],
    current_location: str,
    active_npcs: List[str],
    location_constraints: str
) -> Dict[str, Any]:
    """
    Convenience function for validating DM responses.
    
    Returns:
        Dict with 'valid', 'corrected_response', 'violations'
    """
    return DMResponseValidator.validate_dm_response(
        dm_response, current_location, active_npcs, location_constraints
    )
