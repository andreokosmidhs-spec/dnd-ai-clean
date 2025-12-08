"""
DC (Difficulty Class) Rules & Taxonomy
Provides standardized DC calculation based on D&D 5e rules and action context
"""
import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class DCBand(Enum):
    """DC difficulty bands based on D&D 5e DMG p.238"""
    TRIVIAL = "trivial"           # 5: Almost always succeeds
    EASY = "easy"                 # 10: Easy task
    MODERATE = "moderate"         # 15: Moderate difficulty
    HARD = "hard"                 # 20: Hard task
    VERY_HARD = "very_hard"       # 25: Very hard task
    NEARLY_IMPOSSIBLE = "nearly_impossible"  # 30: Nearly impossible


# DC Band to numeric DC mapping
DC_BAND_VALUES = {
    DCBand.TRIVIAL: 5,
    DCBand.EASY: 10,
    DCBand.MODERATE: 15,
    DCBand.HARD: 20,
    DCBand.VERY_HARD: 25,
    DCBand.NEARLY_IMPOSSIBLE: 30
}


class DCHelper:
    """Helper for calculating appropriate DCs based on action context"""
    
    # Action type base DCs (DMG p.238)
    ACTION_BASE_DC = {
        # Physical actions
        "climb": DCBand.MODERATE,
        "jump": DCBand.EASY,
        "swim": DCBand.MODERATE,
        "lift": DCBand.MODERATE,
        "break_object": DCBand.HARD,
        
        # Social actions
        "persuade": DCBand.MODERATE,
        "deceive": DCBand.MODERATE,
        "intimidate": DCBand.MODERATE,
        "perform": DCBand.MODERATE,
        
        # Mental actions
        "investigate": DCBand.MODERATE,
        "perception": DCBand.MODERATE,
        "insight": DCBand.MODERATE,
        "recall_knowledge": DCBand.MODERATE,
        
        # Stealth actions
        "hide": DCBand.MODERATE,
        "move_silently": DCBand.MODERATE,
        "pickpocket": DCBand.HARD,
        "pick_lock": DCBand.MODERATE,
        "disable_trap": DCBand.HARD,
        
        # Survival actions
        "track": DCBand.MODERATE,
        "forage": DCBand.MODERATE,
        "navigate": DCBand.MODERATE,
        
        # Magic/Arcane
        "identify_magic": DCBand.MODERATE,
        "dispel_magic": DCBand.HARD,
        "resist_spell": DCBand.HARD
    }
    
    # Environmental modifiers
    ENVIRONMENT_MODIFIERS = {
        "rain": +2,
        "heavy_rain": +5,
        "fog": +2,
        "darkness": +5,
        "dim_light": +2,
        "loud_noise": +2,
        "crowded": +2,
        "distracted_target": -2,
        "ideal_conditions": -2
    }
    
    # Risk level modifiers
    RISK_MODIFIERS = {
        "low_risk": -2,      # Plenty of time, no pressure
        "normal_risk": 0,    # Standard situation
        "high_risk": +2,     # Time pressure or consequences
        "critical_risk": +5  # Life-or-death situation
    }
    
    @staticmethod
    def calculate_dc(
        action_type: str,
        risk_level: str = "normal_risk",
        environment: Optional[list] = None,
        character_level: int = 1,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, str, DCBand]:
        """
        Calculate appropriate DC for an action
        
        Args:
            action_type: Type of action (e.g., "climb", "persuade", "pick_lock")
            risk_level: Risk level of the situation
            environment: List of environmental conditions
            character_level: Character's level (affects scaling)
            additional_context: Extra context that might affect DC
            
        Returns:
            Tuple of (numeric_dc, reasoning, dc_band)
        """
        if environment is None:
            environment = []
        if additional_context is None:
            additional_context = {}
        
        # Step 1: Get base DC band
        base_band = DCHelper.ACTION_BASE_DC.get(
            action_type.lower().replace(" ", "_"), 
            DCBand.MODERATE
        )
        base_dc = DC_BAND_VALUES[base_band]
        
        # Step 2: Apply risk modifier
        risk_mod = DCHelper.RISK_MODIFIERS.get(risk_level, 0)
        
        # Step 3: Apply environmental modifiers
        env_mod = sum(DCHelper.ENVIRONMENT_MODIFIERS.get(e, 0) for e in environment)
        
        # Step 4: Calculate final DC
        final_dc = base_dc + risk_mod + env_mod
        
        # Step 5: Apply level-based scaling (optional)
        # Higher level characters face slightly harder challenges for routine tasks
        if character_level >= 5 and action_type in ["climb", "jump", "swim"]:
            # Routine physical tasks become trivial at high levels
            final_dc = max(final_dc - 2, 5)
        
        # Clamp DC to valid range (5-30)
        final_dc = max(5, min(30, final_dc))
        
        # Determine final band
        final_band = DCHelper._dc_to_band(final_dc)
        
        # Build reasoning
        reasoning_parts = [
            f"Base: {base_band.value} ({base_dc})"
        ]
        if risk_mod != 0:
            reasoning_parts.append(f"Risk: {risk_level} ({risk_mod:+d})")
        if env_mod != 0:
            reasoning_parts.append(f"Environment: {environment} ({env_mod:+d})")
        
        reasoning = " | ".join(reasoning_parts) + f" | Final: DC {final_dc} ({final_band.value})"
        
        logger.info(f"📊 DC Calculation: {action_type} → {reasoning}")
        
        return final_dc, reasoning, final_band
    
    @staticmethod
    def _dc_to_band(dc: int) -> DCBand:
        """Convert numeric DC to difficulty band"""
        if dc <= 5:
            return DCBand.TRIVIAL
        elif dc <= 10:
            return DCBand.EASY
        elif dc <= 15:
            return DCBand.MODERATE
        elif dc <= 20:
            return DCBand.HARD
        elif dc <= 25:
            return DCBand.VERY_HARD
        else:
            return DCBand.NEARLY_IMPOSSIBLE
    
    @staticmethod
    def get_action_type_from_intent(player_action: str, intent_flags: Dict[str, Any]) -> str:
        """
        Determine action type from player action and intent flags
        
        Args:
            player_action: Raw player action text
            intent_flags: Intent classification from intent_tagger
            
        Returns:
            Action type string for DC calculation
        """
        action_lower = player_action.lower()
        
        # Physical actions
        if any(word in action_lower for word in ["climb", "scale", "ascend"]):
            return "climb"
        if any(word in action_lower for word in ["jump", "leap"]):
            return "jump"
        if any(word in action_lower for word in ["swim", "dive"]):
            return "swim"
        if any(word in action_lower for word in ["lift", "push", "pull"]):
            return "lift"
        if any(word in action_lower for word in ["break", "smash", "destroy"]):
            return "break_object"
        
        # Social actions
        if any(word in action_lower for word in ["persuade", "convince", "plead"]):
            return "persuade"
        if any(word in action_lower for word in ["lie", "deceive", "bluff"]):
            return "deceive"
        if any(word in action_lower for word in ["intimidate", "threaten", "scare"]):
            return "intimidate"
        if any(word in action_lower for word in ["perform", "sing", "dance"]):
            return "perform"
        
        # Mental actions
        if any(word in action_lower for word in ["investigate", "search", "examine", "inspect"]):
            return "investigate"
        if any(word in action_lower for word in ["look", "spot", "notice", "watch"]):
            return "perception"
        if any(word in action_lower for word in ["sense", "read", "gauge", "discern"]):
            return "insight"
        if any(word in action_lower for word in ["recall", "remember", "know"]):
            return "recall_knowledge"
        
        # Stealth actions
        if any(word in action_lower for word in ["hide", "conceal"]):
            return "hide"
        if any(word in action_lower for word in ["sneak", "move quietly", "creep"]):
            return "move_silently"
        if any(word in action_lower for word in ["pickpocket", "steal"]):
            return "pickpocket"
        if any(word in action_lower for word in ["pick lock", "unlock"]):
            return "pick_lock"
        if any(word in action_lower for word in ["disarm", "disable trap"]):
            return "disable_trap"
        
        # Survival actions
        if any(word in action_lower for word in ["track", "follow trail"]):
            return "track"
        if any(word in action_lower for word in ["forage", "gather", "hunt"]):
            return "forage"
        if any(word in action_lower for word in ["navigate", "find way"]):
            return "navigate"
        
        # Default to moderate investigation
        return "investigate"
    
    @staticmethod
    def should_require_check(action_type: str, character_level: int) -> bool:
        """
        Determine if an action should require a check
        
        Some actions are trivial for high-level characters
        """
        trivial_actions = ["jump", "climb"] if character_level >= 10 else []
        return action_type not in trivial_actions
    
    @staticmethod
    def get_suggested_ability_and_skill(action_type: str) -> Tuple[str, Optional[str]]:
        """
        Get the suggested ability and skill for an action type
        
        Returns:
            Tuple of (ability, skill) where skill can be None
        """
        ability_skill_map = {
            # Physical (Strength)
            "climb": ("strength", "Athletics"),
            "jump": ("strength", "Athletics"),
            "swim": ("strength", "Athletics"),
            "lift": ("strength", "Athletics"),
            "break_object": ("strength", None),
            
            # Social (Charisma)
            "persuade": ("charisma", "Persuasion"),
            "deceive": ("charisma", "Deception"),
            "intimidate": ("charisma", "Intimidation"),
            "perform": ("charisma", "Performance"),
            
            # Mental (Intelligence/Wisdom)
            "investigate": ("intelligence", "Investigation"),
            "perception": ("wisdom", "Perception"),
            "insight": ("wisdom", "Insight"),
            "recall_knowledge": ("intelligence", "History"),
            
            # Stealth (Dexterity)
            "hide": ("dexterity", "Stealth"),
            "move_silently": ("dexterity", "Stealth"),
            "pickpocket": ("dexterity", "Sleight of Hand"),
            "pick_lock": ("dexterity", "Sleight of Hand"),
            "disable_trap": ("dexterity", "Sleight of Hand"),
            
            # Survival (Wisdom)
            "track": ("wisdom", "Survival"),
            "forage": ("wisdom", "Survival"),
            "navigate": ("wisdom", "Survival"),
            
            # Magic (Intelligence)
            "identify_magic": ("intelligence", "Arcana"),
            "dispel_magic": ("intelligence", "Arcana"),
            "resist_spell": ("wisdom", None)
        }
        
        return ability_skill_map.get(action_type, ("dexterity", None))
