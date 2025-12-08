"""
INFORMATION DISPENSING SERVICE - DMG p.26-27

Implements DMG guidance on how and when to reveal information to players:
- "Give players information they need to make smart choices" (p.26)
- "Use passive skill checks regularly to maintain momentum" (p.26)
- "Tell players everything they need to know, but not all at once" (p.26)
- "Make conditions clear to players" (p.27)
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class InformationDispenser:
    """
    Control information flow following DMG p.26-27 guidance.
    """
    
    # DMG p.27: Condition explanations in plain language
    CONDITION_EXPLANATIONS = {
        'unconscious': "You are unconscious (0 HP). You cannot take actions. Enemies have advantage against you. Melee attacks within 5 feet are automatic critical hits.",
        'poisoned': "You are poisoned. You have disadvantage on attack rolls and ability checks.",
        'prone': "You are prone on the ground. You have disadvantage on attack rolls. Enemies within 5 feet have advantage against you. Standing up costs half your movement.",
        'grappled': "You are grappled. Your speed becomes 0, and you can't benefit from any bonus to your speed.",
        'restrained': "You are restrained. Your speed becomes 0. Attack rolls against you have advantage. Your attack rolls have disadvantage. You have disadvantage on Dexterity saving throws.",
        'stunned': "You are stunned. You can't move or take actions or reactions. Attack rolls against you have advantage. You automatically fail Strength and Dexterity saving throws.",
        'paralyzed': "You are paralyzed. You are incapacitated and can't move or speak. Attack rolls against you have advantage. Melee attacks within 5 feet are automatic critical hits. You automatically fail Strength and Dexterity saving throws.",
        'frightened': "You are frightened. You have disadvantage on ability checks and attack rolls while the source of fear is within sight. You can't willingly move closer to the source of fear.",
        'charmed': "You are charmed. You can't attack the charmer or target them with harmful abilities. The charmer has advantage on social interaction checks with you.",
        'blinded': "You are blinded. You can't see. Attack rolls against you have advantage. Your attack rolls have disadvantage.",
        'deafened': "You are deafened. You can't hear and automatically fail ability checks that require hearing.",
        'invisible': "You are invisible. You can't be seen. Attack rolls against you have disadvantage. Your attack rolls have advantage."
    }
    
    @staticmethod
    def apply_passive_perception(
        character_state: Dict[str, Any],
        world_state: Dict[str, Any],
        location_secrets: List[Dict[str, Any]] = None
    ) -> List[str]:
        """
        DMG p.26: "Use passive skill checks regularly to maintain momentum and suspense"
        
        Auto-reveal information based on character's passive Perception score.
        No player action required - happens automatically.
        
        Args:
            character_state: Player character data
            world_state: Current world state
            location_secrets: List of discoverable secrets with DC values
        
        Returns:
            List of auto-revealed information strings
        """
        if not location_secrets:
            location_secrets = world_state.get('location_secrets', [])
        
        if not location_secrets:
            return []
        
        # Calculate passive Perception: 10 + WIS modifier + proficiency (if proficient)
        abilities = character_state.get('abilities', {})
        wis_score = abilities.get('wis', 10)
        wis_mod = (wis_score - 10) // 2
        
        # Assume proficiency in Perception (adjust if needed)
        proficiency_bonus = character_state.get('proficiency_bonus', 2)
        passive_perception = 10 + wis_mod + proficiency_bonus
        
        logger.info(f"🔍 Passive Perception check: {passive_perception} (10 + WIS {wis_mod:+d} + prof {proficiency_bonus:+d})")
        
        # Auto-reveal secrets that meet the DC threshold
        revealed = []
        for secret in location_secrets:
            dc = secret.get('dc', 15)
            info = secret.get('information', '')
            already_revealed = secret.get('revealed', False)
            
            if not already_revealed and passive_perception >= dc:
                revealed.append(info)
                secret['revealed'] = True
                logger.info(f"✅ AUTO-REVEALED (DC {dc}): {info[:50]}...")
        
        return revealed
    
    @staticmethod
    def drip_feed_information(
        information_list: List[str],
        tension_phase: str,
        max_items: Optional[int] = None
    ) -> List[str]:
        """
        DMG p.26: "Tell players everything they need to know, but not all at once"
        
        Control information release based on pacing phase.
        
        Pacing-based limits:
        - Calm: Give 3-4 pieces (players can absorb more)
        - Building: Give 2-3 pieces with ominous framing
        - Tense: Give 1-2 pieces (withhold to maintain mystery)
        - Climax: Give all critical info (players need it to act)
        - Resolution: Give remaining info (wrap up loose ends)
        
        Args:
            information_list: All available information
            tension_phase: Current pacing phase
            max_items: Override max items (optional)
        
        Returns:
            Filtered list of information to reveal now
        """
        if not information_list:
            return []
        
        # Determine how much to reveal based on tension
        limits = {
            "calm": 4,
            "building": 3,
            "tense": 2,
            "climax": 999,  # Give everything critical
            "resolution": 999  # Give everything remaining
        }
        
        limit = max_items if max_items is not None else limits.get(tension_phase, 3)
        
        revealed = information_list[:limit]
        withheld = information_list[limit:]
        
        if withheld:
            logger.info(f"📋 Information drip-feed: Revealing {len(revealed)}/{len(information_list)} items (tension: {tension_phase})")
            logger.info(f"   Withheld for later: {len(withheld)} items")
        else:
            logger.info(f"📋 Revealing all {len(revealed)} information items")
        
        return revealed
    
    @staticmethod
    def clarify_conditions(character_state: Dict[str, Any]) -> List[str]:
        """
        DMG p.27: "Make conditions clear to players"
        
        Return plain language explanations of all active conditions.
        
        Args:
            character_state: Player character data
        
        Returns:
            List of condition explanation strings
        """
        conditions = character_state.get('conditions', [])
        
        if not conditions:
            return []
        
        explanations = []
        for condition in conditions:
            condition_lower = condition.lower()
            explanation = InformationDispenser.CONDITION_EXPLANATIONS.get(
                condition_lower,
                f"You are {condition}."
            )
            explanations.append(f"**{condition.upper()}:** {explanation}")
            logger.info(f"🏷️ Condition clarified: {condition}")
        
        return explanations
    
    @staticmethod
    def format_information_for_narration(
        auto_revealed: List[str],
        drip_fed: List[str],
        condition_explanations: List[str]
    ) -> str:
        """
        Format all information types into a coherent narration addition.
        
        Returns:
            Formatted string to prepend to DM narration
        """
        parts = []
        
        # Passive Perception reveals (DMG p.26)
        if auto_revealed:
            parts.append("**You notice:** " + " ".join(auto_revealed))
        
        # Drip-fed information
        if drip_fed:
            parts.append(" ".join(drip_fed))
        
        # Condition clarifications (DMG p.27)
        if condition_explanations:
            parts.append("\n\n**Your current conditions:**\n" + "\n".join(condition_explanations))
        
        return "\n\n".join(parts) if parts else ""
    
    @staticmethod
    def should_withhold_information(
        information_type: str,
        tension_phase: str
    ) -> bool:
        """
        Determine if specific information should be withheld for suspense.
        
        DMG p.26: Use information control to maintain tension.
        
        Rules:
        - Never withhold critical information during climax
        - Can withhold details during tense phase for mystery
        - Should reveal freely during calm and resolution
        """
        if tension_phase == "climax":
            return False  # Give everything during action
        
        if tension_phase == "tense" and information_type in ["mystery_clue", "enemy_weakness"]:
            return True  # Withhold to maintain suspense
        
        if tension_phase == "resolution":
            return False  # Reveal everything after crisis
        
        return False  # Default: reveal
    
    @staticmethod
    def get_information_priority(
        information_list: List[Dict[str, Any]],
        current_situation: str
    ) -> List[Dict[str, Any]]:
        """
        DMG p.26: "Give players information they need to make smart choices"
        
        Prioritize information based on immediate relevance.
        
        Priority order:
        1. Critical (needed for immediate decision)
        2. Important (relevant to current quest)
        3. Useful (helpful but not essential)
        4. Flavor (world-building, atmosphere)
        
        Args:
            information_list: List of info dicts with 'priority' field
            current_situation: combat, exploration, social, etc.
        
        Returns:
            Sorted list (highest priority first)
        """
        priority_order = {"critical": 0, "important": 1, "useful": 2, "flavor": 3}
        
        sorted_info = sorted(
            information_list,
            key=lambda x: priority_order.get(x.get('priority', 'useful'), 2)
        )
        
        logger.info(f"📊 Information prioritized: {len(sorted_info)} items sorted by relevance")
        return sorted_info
    
    @staticmethod
    def check_information_overload(
        information_count: int,
        tension_phase: str
    ) -> bool:
        """
        Detect if too much information is being given at once.
        
        DMG p.26: "not all at once" - prevent overwhelming players
        
        Returns True if information overload detected
        """
        overload_thresholds = {
            "calm": 5,
            "building": 4,
            "tense": 3,
            "climax": 999,  # No limit during action
            "resolution": 6
        }
        
        threshold = overload_thresholds.get(tension_phase, 4)
        
        if information_count > threshold:
            logger.warning(f"⚠️ INFORMATION OVERLOAD: {information_count} items exceeds threshold of {threshold} for {tension_phase} phase")
            return True
        
        return False
