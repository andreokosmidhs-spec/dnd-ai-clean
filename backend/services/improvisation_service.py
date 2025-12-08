"""
PLAYER AGENCY / IMPROVISATION FRAMEWORK - DMG p.28-29
Implements "Say Yes" principle for creative player actions.

DMG p.28: "Build on player actions and ideas"
DMG p.29: "Use the 'Yes, and...' or 'Yes, but...' approach"
"""

import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ImprovisationEngine:
    """
    Handle creative and unexpected player actions using DMG improvisation guidelines.
    
    DMG p.28-29: "Say Yes" - Build on player actions, don't block them unnecessarily.
    """
    
    # Keywords indicating creative/unusual actions
    CREATIVE_ACTION_INDICATORS = [
        "swing from", "chandelier", "rope", "flip", "acrobat",
        "creative", "unusual", "clever", "improvise", "trick",
        "distract", "feint", "bluff", "deceive", "ruse",
        "unconventional", "surprise", "outsmart"
    ]
    
    # Keywords indicating risky actions
    RISKY_ACTION_INDICATORS = [
        "jump", "leap", "throw", "dangerous", "risky",
        "uncertain", "gamble", "chance", "attempt",
        "try to", "might work", "hopefully"
    ]
    
    # Keywords indicating impossible/absurd actions
    IMPOSSIBLE_INDICATORS = [
        "fly without", "teleport", "time travel", "mind control",
        "instant kill", "destroy the world", "become god",
        "violate physics", "ignore rules"
    ]
    
    @staticmethod
    def classify_player_action(
        player_action: str,
        intent_flags: Dict[str, Any],
        character_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Classify player action for improvisation handling.
        
        DMG p.28-29: Determine if action is:
        - creative_and_plausible (reward with advantage)
        - risky_but_possible (allow with complication)
        - impossible (suggest alternative)
        - standard (normal resolution)
        
        Args:
            player_action: Player's action text
            intent_flags: Intent classification from classifier
            character_state: Character capabilities
            
        Returns:
            Classification result
        """
        action_lower = player_action.lower()
        
        # Check for impossible actions first
        if any(keyword in action_lower for keyword in ImprovisationEngine.IMPOSSIBLE_INDICATORS):
            return {
                "classification": "impossible",
                "approach": "no_and_alternative",
                "reasoning": "Action violates fundamental game rules or physics",
                "dm_hint": "Explain why it won't work, suggest alternatives",
                "apply_advantage": False,
                "add_complication": False
            }
        
        # Check for creative actions
        is_creative = any(keyword in action_lower for keyword in ImprovisationEngine.CREATIVE_ACTION_INDICATORS)
        is_risky = any(keyword in action_lower for keyword in ImprovisationEngine.RISKY_ACTION_INDICATORS)
        
        # Analyze complexity
        is_complex = (
            len(player_action.split()) > 15 or  # Long, detailed action
            ' and ' in action_lower or  # Multiple actions
            ' while ' in action_lower  # Simultaneous actions
        )
        
        if is_creative and not is_risky:
            # DMG p.28: Reward creativity
            return {
                "classification": "creative_and_plausible",
                "approach": "yes_and",
                "reasoning": "Creative action that enhances gameplay",
                "dm_hint": "Reward creativity with advantage or lower DC. DMG p.28: Build on player ideas.",
                "apply_advantage": True,
                "add_complication": False,
                "creativity_bonus": "advantage_on_check"
            }
        
        elif is_risky or (is_creative and is_complex):
            # DMG p.29: Allow but add complication
            return {
                "classification": "risky_but_possible",
                "approach": "yes_but",
                "reasoning": "Action is possible but carries risk",
                "dm_hint": "Allow it but introduce a complication or twist. DMG p.29: Success at a cost.",
                "apply_advantage": False,
                "add_complication": True,
                "complication_type": "narrative_cost"
            }
        
        else:
            # Standard action
            return {
                "classification": "standard",
                "approach": "standard_resolution",
                "reasoning": "Normal action within expected gameplay",
                "dm_hint": "Resolve normally using standard rules",
                "apply_advantage": False,
                "add_complication": False
            }
    
    @staticmethod
    def generate_alternative(
        player_action: str,
        reason: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Generate alternative suggestions for impossible actions.
        
        DMG p.28: Don't just say "no" - offer alternatives
        
        Args:
            player_action: The impossible action
            reason: Why it's impossible
            context: Current game context
            
        Returns:
            Alternative suggestion text
        """
        alternatives = []
        
        # Extract intent from action
        if "fly" in player_action.lower():
            alternatives.append("You could try to jump and grab onto something")
            alternatives.append("Look for magical items or spells that grant flight")
        
        if "teleport" in player_action.lower():
            alternatives.append("You could search for a teleportation circle")
            alternatives.append("Investigate if there are magic users who can help")
        
        if "instant" in player_action.lower():
            alternatives.append("You could attempt a powerful attack, but it would require a roll")
            alternatives.append("Consider weakening them first with tactical actions")
        
        # Generic fallback
        if not alternatives:
            alternatives = [
                "You could try a different approach to achieve a similar goal",
                "Consider using your skills or equipment in a creative way",
                "Look for environmental advantages or allies who can help"
            ]
        
        return "Alternatives: " + " OR ".join(alternatives)
    
    @staticmethod
    def generate_complication(
        player_action: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate appropriate complication for risky actions.
        
        DMG p.29: "Yes, but..." - allow action with a cost
        
        Args:
            player_action: The risky action
            context: Current game context
            
        Returns:
            Complication details
        """
        complication_types = [
            {
                "type": "time_cost",
                "description": "Action takes longer than expected",
                "dm_hint": "Narrative: 'You succeed, but it takes precious time...'"
            },
            {
                "type": "resource_cost",
                "description": "Action consumes resources or causes damage",
                "dm_hint": "Narrative: 'You succeed, but your equipment is damaged...'"
            },
            {
                "type": "attention_drawn",
                "description": "Action draws unwanted attention",
                "dm_hint": "Narrative: 'You succeed, but others have noticed...'"
            },
            {
                "type": "partial_success",
                "description": "Action works but not perfectly",
                "dm_hint": "Narrative: 'You succeed partially, but...'"
            },
            {
                "type": "unforeseen_consequence",
                "description": "Action causes unexpected side effect",
                "dm_hint": "Narrative: 'You succeed, but something unexpected happens...'"
            }
        ]
        
        # Select appropriate complication based on context
        import random
        complication = random.choice(complication_types)
        
        logger.info(f"🎲 Complication generated: {complication['type']}")
        
        return complication
    
    @staticmethod
    def format_improvisation_for_prompt(
        improvisation_result: Dict[str, Any]
    ) -> str:
        """
        Format improvisation result for DM prompt.
        
        Args:
            improvisation_result: Classification result
            
        Returns:
            Formatted prompt block
        """
        classification = improvisation_result['classification']
        approach = improvisation_result['approach']
        dm_hint = improvisation_result.get('dm_hint', '')
        
        prompt_block = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPROVISATION GUIDANCE (DMG p.28-29)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Action Classification: {classification}
Approach: {approach}

{dm_hint}
"""
        
        if improvisation_result.get('apply_advantage'):
            prompt_block += """
✅ REWARD CREATIVITY:
- Grant advantage on the check
- Or lower DC by 2-5
- Narrate how their creativity helps

"""
        
        if improvisation_result.get('add_complication'):
            complication = improvisation_result.get('complication_type', 'narrative_cost')
            prompt_block += f"""
⚠️ ADD COMPLICATION:
- Type: {complication}
- Use "Yes, but..." phrasing
- Success comes at a cost

"""
        
        if improvisation_result.get('classification') == 'impossible':
            prompt_block += """
❌ IMPOSSIBLE ACTION:
- Explain why it won't work
- Suggest plausible alternatives
- Use "No, but you could..." phrasing

"""
        
        prompt_block += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        return prompt_block
    
    @staticmethod
    def should_grant_advantage(improvisation_result: Dict[str, Any]) -> bool:
        """Check if player should receive advantage from creativity"""
        return improvisation_result.get('apply_advantage', False)
    
    @staticmethod
    def get_creativity_reward(improvisation_result: Dict[str, Any]) -> Optional[str]:
        """Get reward type for creative action"""
        if improvisation_result.get('apply_advantage'):
            return "advantage"
        return None


def classify_action(
    player_action: str,
    intent_flags: Dict[str, Any],
    character_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Classify player action for improvisation handling.
    
    Args:
        player_action: Player's action text
        intent_flags: Intent classification
        character_state: Character state
        
    Returns:
        Classification result
    """
    return ImprovisationEngine.classify_player_action(
        player_action, intent_flags, character_state
    )


def format_for_dm_prompt(improvisation_result: Dict[str, Any]) -> str:
    """
    Format improvisation result for DM prompt.
    
    Args:
        improvisation_result: Classification result
        
    Returns:
        Formatted prompt block
    """
    return ImprovisationEngine.format_improvisation_for_prompt(improvisation_result)


def should_apply_advantage(improvisation_result: Dict[str, Any]) -> bool:
    """Check if creativity bonus should be applied"""
    return ImprovisationEngine.should_grant_advantage(improvisation_result)
