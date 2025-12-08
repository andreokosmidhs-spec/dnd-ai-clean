"""
SESSION FLOW MANAGER - DMG p.20-24
Tracks and manages game modes (exploration, conversation, encounter, etc.)

DMG p.20-21: "Game modes define the structure and pace of play"
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SessionFlowManager:
    """
    Track and manage game modes to adjust DM narration style.
    
    DMG p.20-21: Different game modes require different DM approaches.
    """
    
    # DMG p.20-21: Core game modes
    GAME_MODES = {
        "exploration": {
            "description": "Moving through environment, making decisions",
            "dm_guidance": "DMG p.20: Describe environment, listen to actions, narrate results",
            "narration_style": "descriptive and atmospheric",
            "detail_level": "high",
            "pace": "moderate",
            "focus": "discovery and decision-making",
            "typical_duration_minutes": 30
        },
        "conversation": {
            "description": "Social interaction with NPCs",
            "dm_guidance": "DMG p.21: Not a skill challenge, explore information naturally",
            "narration_style": "dialogue-focused and character-driven",
            "detail_level": "moderate",
            "pace": "relaxed",
            "focus": "NPC personality and information exchange",
            "typical_duration_minutes": 15
        },
        "encounter": {
            "description": "Combat or high-stakes challenge",
            "dm_guidance": "DMG p.21: Tension and urgency, rules are most important",
            "narration_style": "fast-paced and action-focused",
            "detail_level": "low (focus on mechanics)",
            "pace": "fast",
            "focus": "tactical decisions and immediate danger",
            "typical_duration_minutes": 20
        },
        "investigation": {
            "description": "Searching for clues, solving puzzles",
            "dm_guidance": "DMG p.24: Provide information based on checks and player cleverness",
            "narration_style": "analytical and detail-oriented",
            "detail_level": "high (clues and details)",
            "pace": "slow",
            "focus": "problem-solving and deduction",
            "typical_duration_minutes": 20
        },
        "travel": {
            "description": "Moving between locations",
            "dm_guidance": "DMG p.21: Gloss over mundane travel, highlight interesting moments",
            "narration_style": "summarized and efficient",
            "detail_level": "low",
            "pace": "fast",
            "focus": "getting to destination, occasional encounters",
            "typical_duration_minutes": 5
        },
        "downtime": {
            "description": "Rest, shopping, planning, character development",
            "dm_guidance": "DMG p.21: Allow preparation and character moments",
            "narration_style": "relaxed and functional",
            "detail_level": "moderate",
            "pace": "relaxed",
            "focus": "preparation and character interaction",
            "typical_duration_minutes": 10
        },
        "exposition": {
            "description": "Player seeking information, listening, or asking for explanation",
            "dm_guidance": "PHASE 2.5: Deliver clear, plot-relevant information. Stop vibes, start facts.",
            "narration_style": "informative and plot-advancing",
            "detail_level": "high (concrete facts and revelations)",
            "pace": "moderate",
            "focus": "revealing who, what, where, why, stakes, and next actions",
            "typical_duration_minutes": 10
        }
    }
    
    @staticmethod
    def detect_session_mode(
        player_action: str,
        intent_flags: Dict[str, Any],
        world_state: Dict[str, Any],
        combat_active: bool
    ) -> Dict[str, Any]:
        """
        Detect current session mode based on player action and context.
        
        DMG p.20-21: Different situations require different DM approaches
        
        Args:
            player_action: Player's current action
            intent_flags: Intent classification
            world_state: Current world state
            combat_active: Whether combat is active
            
        Returns:
            Mode detection result
        """
        action_lower = player_action.lower()
        
        # Combat/Encounter mode (highest priority)
        if combat_active:
            return SessionFlowManager._create_mode_result("encounter", "Combat is active")
        
        # PHASE 2.5: Exposition mode (info-seeking actions)
        # Detect when player is explicitly listening/waiting/asking for information
        exposition_keywords = [
            'wait', 'listen', 'hear', 'let them talk', 'unfold more information',
            'hear more', 'listen closely', 'hear what they say', 'find out what',
            'explain', 'tell me what', 'what\'s going on', 'what is happening',
            'continue listening', 'keep listening', 'pay attention', 'observe the conversation',
            'let them continue', 'hear them out', 'what are they saying'
        ]
        
        # Check if action is primarily about listening/waiting for info
        # Priority: If player is NOT taking direct action, but seeking info → exposition
        is_passive_listening = any(keyword in action_lower for keyword in exposition_keywords)
        
        # Additional heuristic: short actions like "I wait" or "I listen" without other verbs
        action_words = action_lower.split()
        is_simple_wait = len(action_words) <= 5 and any(w in action_words for w in ['wait', 'listen', 'hear'])
        
        if is_passive_listening or is_simple_wait:
            return SessionFlowManager._create_mode_result("exposition", "Player seeking information/listening")
        
        # Check for explicit mode indicators in action
        # Conversation indicators (but not exposition)
        conversation_keywords = ['talk', 'speak', 'ask', 'tell', 'converse', 'discuss', 'negotiate', 'persuade', 'greet', 'introduce']
        if any(keyword in action_lower for keyword in conversation_keywords):
            return SessionFlowManager._create_mode_result("conversation", "Social interaction detected")
        
        # Investigation indicators
        investigation_keywords = ['search', 'investigate', 'examine', 'inspect', 'look for', 'study', 'analyze']
        if any(keyword in action_lower for keyword in investigation_keywords):
            return SessionFlowManager._create_mode_result("investigation", "Investigation action detected")
        
        # Travel indicators
        travel_keywords = ['travel', 'journey', 'go to', 'head to', 'walk to', 'move to', 'leave for']
        if any(keyword in action_lower for keyword in travel_keywords):
            return SessionFlowManager._create_mode_result("travel", "Travel action detected")
        
        # Downtime indicators (removed 'wait' since it's now exposition)
        downtime_keywords = ['rest', 'sleep', 'shop', 'buy', 'sell', 'prepare', 'plan']
        if any(keyword in action_lower for keyword in downtime_keywords):
            return SessionFlowManager._create_mode_result("downtime", "Downtime activity detected")
        
        # Default to exploration
        return SessionFlowManager._create_mode_result("exploration", "General exploration/interaction")
    
    @staticmethod
    def _create_mode_result(mode: str, reason: str) -> Dict[str, Any]:
        """Create a mode detection result"""
        mode_data = SessionFlowManager.GAME_MODES.get(mode, SessionFlowManager.GAME_MODES["exploration"])
        
        result = {
            "mode": mode,
            "detection_reason": reason,
            **mode_data
        }
        
        logger.info(f"🎮 Session mode detected: {mode} ({reason})")
        
        return result
    
    @staticmethod
    def format_mode_for_prompt(mode_result: Dict[str, Any]) -> str:
        """
        Format session mode for DM prompt.
        
        DMG p.20-21: DM approach should match current game mode
        
        Args:
            mode_result: Mode detection result
            
        Returns:
            Formatted prompt block
        """
        mode = mode_result['mode']
        narration_style = mode_result['narration_style']
        detail_level = mode_result['detail_level']
        pace = mode_result['pace']
        focus = mode_result['focus']
        dm_guidance = mode_result['dm_guidance']
        
        prompt_block = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SESSION MODE: {mode.upper()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Narration Style: {narration_style}
Detail Level: {detail_level}
Pace: {pace}
Focus: {focus}

DMG Guidance: {dm_guidance}

"""
        
        # Add mode-specific instructions
        if mode == "exploration":
            prompt_block += """EXPLORATION MODE INSTRUCTIONS:
- Rich sensory details (sights, sounds, smells)
- Describe environment and atmosphere
- Present choices and opportunities
- Moderate pacing, allow player decisions

"""
        elif mode == "conversation":
            prompt_block += """CONVERSATION MODE INSTRUCTIONS:
- Focus on NPC personality and dialogue
- Use NPC's voice, mannerisms, emotional state
- Information exchange through natural conversation
- Don't make it a skill challenge - let it flow naturally

"""
        elif mode == "encounter":
            prompt_block += """ENCOUNTER MODE INSTRUCTIONS:
- Short, punchy narration
- Focus on immediate action and danger
- Clear mechanical results
- Fast-paced, exciting descriptions
- Turn-by-turn structure

"""
        elif mode == "investigation":
            prompt_block += """INVESTIGATION MODE INSTRUCTIONS:
- Provide clear clues and details
- Reward clever questions and observations
- Describe what can be seen, found, deduced
- Don't hide critical information behind rolls

"""
        elif mode == "travel":
            prompt_block += """TRAVEL MODE INSTRUCTIONS:
- Summarize mundane travel briefly
- Highlight interesting landmarks or encounters
- Move story forward efficiently
- Don't dwell on routine details

"""
        elif mode == "downtime":
            prompt_block += """DOWNTIME MODE INSTRUCTIONS:
- Relaxed, functional narration
- Allow character moments and preparation
- Shopping, resting, planning are valid activities
- Keep it simple and practical

"""
        elif mode == "exposition":
            prompt_block += """🎯 EXPOSITION MODE INSTRUCTIONS (PHASE 2.5 - CRITICAL):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ PLAYER IS EXPLICITLY SEEKING INFORMATION ⚠️

Your job is to ADVANCE THE PLOT, not just set mood.

MANDATORY REQUIREMENTS:
1. Deliver 3-5 concrete pieces of NEW information
2. Reveal facts about: who, what, where, why, stakes
3. Present clear choices or next possible actions
4. NO purple prose or atmospheric filler
5. Be direct and informative

GOOD EXPOSITION:
✓ "The merchant leans in: 'The cult operates from the old mill. 
   They're planning something for the new moon—three days from now. 
   My contact saw them move crates of black powder there last night.'"

✓ "The guard explains: 'The mayor's been acting strange since his 
   trip to the capital. He fired half the town watch and hired 
   mercenaries—rough types from the Bloodstone Company. 
   Something's wrong, but no one dares speak up.'"

BAD EXPOSITION:
✗ "The atmosphere grows tense as they continue speaking..."
✗ "You sense there's more to this story..."
✗ "The conversation unfolds around you with subtle nuances..."

CRITICAL: If player is listening/waiting, NPCs MUST actively share 
information. Don't make them ask again. Give answers NOW.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        prompt_block += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        return prompt_block
    
    @staticmethod
    def get_mode_transition_text(old_mode: str, new_mode: str) -> Optional[str]:
        """
        Generate smooth transition text when mode changes.
        
        DMG p.20: Transitions should be smooth and natural
        
        Args:
            old_mode: Previous mode
            new_mode: New mode
            
        Returns:
            Transition text or None
        """
        if old_mode == new_mode:
            return None
        
        transitions = {
            ("exploration", "encounter"): "Suddenly, danger emerges!",
            ("conversation", "encounter"): "The situation turns violent!",
            ("encounter", "exploration"): "With the threat neutralized, you can now explore.",
            ("encounter", "conversation"): "The combat ends, and you can now speak.",
            ("investigation", "exploration"): "With your findings in mind, you continue onward.",
            ("travel", "exploration"): "You arrive at your destination.",
            ("downtime", "exploration"): "Rested and prepared, you set out once more."
        }
        
        return transitions.get((old_mode, new_mode))
    
    @staticmethod
    def should_adjust_narration_length(mode: str) -> Dict[str, Any]:
        """
        Get narration length guidelines for mode.
        
        Args:
            mode: Current game mode
            
        Returns:
            Length guidelines
        """
        guidelines = {
            "exploration": {"min_words": 80, "max_words": 200, "style": "descriptive"},
            "conversation": {"min_words": 50, "max_words": 150, "style": "dialogue-heavy"},
            "encounter": {"min_words": 30, "max_words": 80, "style": "concise"},
            "investigation": {"min_words": 60, "max_words": 180, "style": "detailed"},
            "travel": {"min_words": 20, "max_words": 60, "style": "summary"},
            "downtime": {"min_words": 40, "max_words": 100, "style": "functional"},
            "exposition": {"min_words": 100, "max_words": 250, "style": "informative with concrete facts"}
        }
        
        return guidelines.get(mode, guidelines["exploration"])


def detect_mode(
    player_action: str,
    intent_flags: Dict[str, Any],
    world_state: Dict[str, Any],
    combat_active: bool = False
) -> Dict[str, Any]:
    """
    Detect current session mode.
    
    Args:
        player_action: Player's action
        intent_flags: Intent classification
        world_state: World state
        combat_active: Is combat active
        
    Returns:
        Mode detection result
    """
    return SessionFlowManager.detect_session_mode(
        player_action, intent_flags, world_state, combat_active
    )


def format_for_dm_prompt(mode_result: Dict[str, Any]) -> str:
    """
    Format mode for DM prompt.
    
    Args:
        mode_result: Mode detection result
        
    Returns:
        Formatted prompt block
    """
    return SessionFlowManager.format_mode_for_prompt(mode_result)


def get_narration_guidelines(mode: str) -> Dict[str, Any]:
    """Get narration length guidelines for mode"""
    return SessionFlowManager.should_adjust_narration_length(mode)
