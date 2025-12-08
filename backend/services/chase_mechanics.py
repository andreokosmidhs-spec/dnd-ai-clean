"""
Chase & Stealth Movement Mechanics
Implements D&D 5e speed-based chase rules
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


# D&D 5e Base Speeds by Race (in feet)
RACE_SPEEDS = {
    "Human": 30,
    "Elf": 30,
    "Dwarf": 25,
    "Halfling": 25,
    "Gnome": 25,
    "Half-Orc": 30,
    "Half-Elf": 30,
    "Tiefling": 30,
    "Dragonborn": 30
}

# Mount Speeds
MOUNT_SPEEDS = {
    "Horse": 60,
    "Pony": 40,
    "Warhorse": 60,
    "Draft Horse": 50,
    "Riding Horse": 60,
    "Mule": 40,
    "Camel": 50,
    "Elephant": 40
}


class ChaseMechanics:
    """Handles chase and stealth movement mechanics"""
    
    @staticmethod
    def get_character_speed(character_state: Dict[str, Any]) -> int:
        """
        Get character's base movement speed
        
        Returns: Speed in feet per round
        """
        race = character_state.get("race", "Human")
        base_speed = RACE_SPEEDS.get(race, 30)
        
        # Check for mounted
        # (Future: check inventory or active effects)
        
        return base_speed
    
    @staticmethod
    def get_stealth_speed(base_speed: int, is_mounted: bool = False) -> int:
        """
        Calculate speed while moving stealthily
        
        Rules:
        - Stealth speed is HALF normal speed (unless mounted)
        - If mounted: use mount's speed, but must hide mount too
        
        Returns: Stealth speed in feet
        """
        if is_mounted:
            # Mounted stealth uses mount's speed
            # But note: must succeed on check to hide mount too
            return base_speed  # Mount's speed already calculated
        else:
            # On foot: half speed
            return base_speed // 2
    
    @staticmethod
    def check_target_escaping(
        player_speed: int,
        target_speed: int,
        player_stealthing: bool = False
    ) -> Dict[str, Any]:
        """
        Determine if target is escaping due to speed difference
        
        Returns:
            Dict with escape_risk and required_check info
        """
        effective_player_speed = player_speed
        if player_stealthing:
            effective_player_speed = ChaseMechanics.get_stealth_speed(player_speed)
        
        speed_diff = target_speed - effective_player_speed
        
        if speed_diff <= 0:
            # Player is fast enough
            return {
                "escape_risk": False,
                "speed_advantage": "player",
                "message": None
            }
        elif speed_diff <= 10:
            # Close - Perception check to keep eyes on target
            return {
                "escape_risk": True,
                "required_check": {
                    "type": "perception",
                    "ability": "WIS",
                    "skill": "Perception",
                    "dc": 13,
                    "reason": "Target moving faster - keep them in sight"
                },
                "speed_disadvantage": speed_diff,
                "message": f"The target moves faster ({target_speed} ft vs your {effective_player_speed} ft). Make Perception check to maintain visual contact."
            }
        else:
            # Large gap - Investigation to track where they went
            return {
                "escape_risk": True,
                "required_check": {
                    "type": "investigation",
                    "ability": "INT",
                    "skill": "Investigation",
                    "dc": 15,
                    "reason": "Target much faster - deduce their route"
                },
                "speed_disadvantage": speed_diff,
                "message": f"The target is much faster ({target_speed} ft vs your {effective_player_speed} ft). You lose visual. Make Investigation check to deduce their route."
            }
    
    @staticmethod
    def generate_mounted_stealth_check() -> Dict[str, Any]:
        """
        Generate check requirement for hiding while mounted
        
        Both rider and mount must be hidden
        """
        return {
            "type": "stealth",
            "ability": "DEX",
            "skill": "Stealth",
            "dc": 16,  # Higher DC for hiding mount
            "reason": "Attempting to move stealthily while mounted - must hide both you and mount",
            "note": "Mount must move slowly (half speed) to remain quiet"
        }
    
    @staticmethod
    def check_finding_hidden_target() -> Dict[str, Any]:
        """
        Generate check for finding a hidden target
        
        Rules: Investigation check to search/find hidden person
        """
        return {
            "type": "investigation",
            "ability": "INT",
            "skill": "Investigation",
            "dc": 15,
            "reason": "Searching for hidden target",
            "opposed": True,  # Contested by target's Stealth
            "note": "Target's Stealth result becomes the DC"
        }
    
    @staticmethod
    def calculate_chase_dc(speed_difference: int, base_dc: int = 13) -> int:
        """
        Calculate DC based on speed difference
        
        Faster target = harder to follow
        """
        if speed_difference <= 0:
            return base_dc
        elif speed_difference <= 10:
            return base_dc + 1
        elif speed_difference <= 20:
            return base_dc + 2
        else:
            return base_dc + 3
