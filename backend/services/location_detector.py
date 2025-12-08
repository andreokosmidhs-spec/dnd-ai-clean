"""
Location Change Detection Service
Detects when player is trying to move to a new location from their action text
"""
import logging
import re
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class LocationDetector:
    """Detects location changes from player actions"""
    
    # Movement keywords that indicate location change
    MOVEMENT_KEYWORDS = [
        'go to', 'head to', 'travel to', 'walk to', 'move to',
        'enter', 'approach', 'visit', 'return to', 'leave for',
        'make my way to', 'venture to', 'proceed to', 'journey to'
    ]
    
    @staticmethod
    def detect_movement(action: str) -> bool:
        """
        Check if the action indicates movement to a new location
        
        Args:
            action: Player's action text
            
        Returns:
            True if action indicates movement
        """
        action_lower = action.lower()
        
        # Check for movement keywords
        for keyword in LocationDetector.MOVEMENT_KEYWORDS:
            if keyword in action_lower:
                return True
                
        return False
    
    @staticmethod
    def extract_destination(action: str, world_blueprint: Dict[str, Any]) -> Optional[str]:
        """
        Extract the destination location from the action text
        
        Args:
            action: Player's action text
            world_blueprint: World blueprint with known locations
            
        Returns:
            Location name if found, None otherwise
        """
        action_lower = action.lower()
        
        # Get list of known locations from world blueprint
        known_locations = []
        
        # Add starting town
        starting_town = world_blueprint.get("starting_town", {})
        if starting_town.get("name"):
            known_locations.append(starting_town["name"])
        
        # Add other towns
        for town in world_blueprint.get("towns", []):
            if town.get("name"):
                known_locations.append(town["name"])
        
        # Add points of interest from starting town
        for poi in starting_town.get("points_of_interest", []):
            if poi.get("name"):
                known_locations.append(poi["name"])
        
        # Check if any known location is mentioned in the action
        for location in known_locations:
            if location.lower() in action_lower:
                logger.info(f"🗺️ Detected destination: {location}")
                return location
        
        # If no exact match, try to extract location name after movement keywords
        for keyword in LocationDetector.MOVEMENT_KEYWORDS:
            if keyword in action_lower:
                # Extract text after the keyword
                pattern = rf"{keyword}\s+(?:the\s+)?([a-zA-Z\s']+?)(?:\.|,|$|to\s)"
                match = re.search(pattern, action_lower)
                if match:
                    potential_location = match.group(1).strip()
                    # Capitalize first letter of each word
                    potential_location = ' '.join(word.capitalize() for word in potential_location.split())
                    logger.info(f"🗺️ Extracted potential destination: {potential_location}")
                    return potential_location
        
        return None
    
    @staticmethod
    async def detect_and_update_location(
        action: str,
        world_blueprint: Dict[str, Any],
        current_location: str
    ) -> Optional[str]:
        """
        Detect if player is moving and return new location
        
        Args:
            action: Player's action text
            world_blueprint: World blueprint
            current_location: Current location
            
        Returns:
            New location name if movement detected, None otherwise
        """
        # Check if action indicates movement
        if not LocationDetector.detect_movement(action):
            return None
        
        # Extract destination
        destination = LocationDetector.extract_destination(action, world_blueprint)
        
        if destination and destination != current_location:
            logger.info(f"🗺️ Location change: '{current_location}' → '{destination}'")
            return destination
        
        return None
