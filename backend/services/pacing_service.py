"""
PACING & TENSION SERVICE - DMG p.24 "Ebb and flow of action and anticipation"

Tracks narrative tension and adjusts DM behavior dynamically to create proper pacing.
Implements the five tension phases from the Dungeon Master's Guide.
"""
import logging
from typing import Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class TensionManager:
    """
    Track and manage narrative tension following DMG p.24 guidance.
    
    DMG Quote: "The pacing of your game is the ebb and flow of action and 
    anticipation, built on varying the kinds of encounters you present to the players."
    """
    
    TENSION_LEVELS = {
        "calm": {
            "range": (0, 20),
            "description": "Safe, routine, social interaction",
            "dm_guidance": "Use for shopping, resting, planning. Brief, functional narration.",
            "narration_style": "relaxed",
            "next_phase": "building",
            "emoji": "🏘️"
        },
        "building": {
            "range": (21, 40),
            "description": "Hints of danger, mysterious clues",
            "dm_guidance": "DMG p.24: Create 'brooding menace in exploration mode'. Describe shadows, sounds, ominous signs.",
            "narration_style": "atmospheric",
            "next_phase": "tense",
            "emoji": "🌫️"
        },
        "tense": {
            "range": (41, 60),
            "description": "Danger is near, players alert",
            "dm_guidance": "Use passive Perception, reveal threats partially. Maintain suspense.",
            "narration_style": "suspenseful",
            "next_phase": "climax",
            "emoji": "⚠️"
        },
        "climax": {
            "range": (61, 90),
            "description": "Active combat or crisis resolution",
            "dm_guidance": "DMG p.24: 'Pulse-pounding action'. Communicate excitement, keep action moving fast.",
            "narration_style": "fast_paced",
            "next_phase": "resolution",
            "emoji": "⚔️"
        },
        "resolution": {
            "range": (91, 100),
            "description": "Crisis resolved, rewards distributed",
            "dm_guidance": "DMG p.24: 'Natural rest points'. Wrap up, give XP, allow rest.",
            "narration_style": "concluding",
            "next_phase": "calm",
            "emoji": "✅"
        }
    }
    
    @staticmethod
    def calculate_tension(
        world_state: Dict[str, Any],
        character_state: Dict[str, Any],
        combat_active: bool,
        recent_actions: list = None
    ) -> int:
        """
        Calculate current tension level (0-100) based on game state.
        
        Factors:
        - Combat status (immediate climax)
        - Time since last combat (tension decay)
        - Player HP percentage (danger indicator)
        - Quest urgency
        - Environmental dangers
        - Recent hostile actions
        
        Returns:
            Tension score 0-100
        """
        tension = 0
        
        # FACTOR 1: Combat Status (DMG p.24 - Climactic Action)
        if combat_active:
            tension += 70  # Immediate high tension
            logger.info("⚔️ Combat active: +70 tension")
        else:
            # Check time since last combat
            time_since_combat = world_state.get('time_since_combat_minutes', 999)
            if time_since_combat < 5:
                tension += 50  # Recently ended combat
                logger.info(f"🕐 Recent combat ({time_since_combat}m ago): +50 tension")
            elif time_since_combat < 15:
                tension += 30  # Still tense from recent action
                logger.info(f"🕐 Combat aftermath ({time_since_combat}m ago): +30 tension")
            elif time_since_combat < 30:
                tension += 10  # Tension fading
                logger.info(f"🕐 Post-combat ({time_since_combat}m ago): +10 tension")
        
        # FACTOR 2: Player HP (danger indicator)
        current_hp = character_state.get('hp', 10)
        max_hp = character_state.get('max_hp', 10)
        hp_percentage = current_hp / max_hp if max_hp > 0 else 1.0
        
        if hp_percentage < 0.25:
            tension += 30  # Critically wounded
            logger.info(f"💔 Critical HP ({hp_percentage:.0%}): +30 tension")
        elif hp_percentage < 0.5:
            tension += 20  # Wounded
            logger.info(f"❤️‍🩹 Low HP ({hp_percentage:.0%}): +20 tension")
        elif hp_percentage < 0.75:
            tension += 10  # Injured
            logger.info(f"💛 Injured ({hp_percentage:.0%}): +10 tension")
        
        # FACTOR 3: Quest Urgency
        quest_urgency = world_state.get('quest_urgency', 'normal')
        if quest_urgency == 'critical':
            tension += 25
            logger.info("🚨 Critical quest: +25 tension")
        elif quest_urgency == 'high':
            tension += 15
            logger.info("⚡ Urgent quest: +15 tension")
        
        # FACTOR 4: Environmental Dangers
        location_danger = world_state.get('location_danger_level', 'safe')
        if location_danger == 'deadly':
            tension += 20
            logger.info("☠️ Deadly location: +20 tension")
        elif location_danger == 'dangerous':
            tension += 10
            logger.info("⚠️ Dangerous location: +10 tension")
        
        # FACTOR 5: Recent Hostile Actions
        if recent_actions:
            hostile_count = sum(1 for a in recent_actions if 'attack' in a.lower() or 'hostile' in a.lower())
            if hostile_count > 0:
                tension += min(20, hostile_count * 5)
                logger.info(f"🎯 Recent hostile actions ({hostile_count}): +{min(20, hostile_count * 5)} tension")
        
        # FACTOR 6: Active Threats (guards, bounties)
        if world_state.get('guard_alert'):
            tension += 15
            logger.info("👮 Guards alerted: +15 tension")
        
        if world_state.get('bounties') and len(world_state['bounties']) > 0:
            tension += 10
            logger.info("💰 Bounty active: +10 tension")
        
        # Cap at 100
        final_tension = min(100, tension)
        logger.info(f"📊 FINAL TENSION: {final_tension}/100")
        
        return final_tension
    
    @staticmethod
    def get_tension_phase(tension_score: int) -> str:
        """
        Determine which tension phase we're in based on score.
        
        Returns phase name: calm, building, tense, climax, or resolution
        """
        for phase_name, phase_data in TensionManager.TENSION_LEVELS.items():
            min_val, max_val = phase_data["range"]
            if min_val <= tension_score <= max_val:
                return phase_name
        return "calm"  # Default
    
    @staticmethod
    def get_dm_pacing_instructions(tension_score: int) -> Dict[str, Any]:
        """
        Get DM narration guidance based on current tension.
        
        DMG p.24: Different phases require different narration styles.
        
        Returns:
            {
                "phase": str,
                "description": str,
                "dm_guidance": str,
                "narration_style": str,
                "emoji": str
            }
        """
        phase = TensionManager.get_tension_phase(tension_score)
        phase_data = TensionManager.TENSION_LEVELS[phase]
        
        return {
            "phase": phase,
            "tension_score": tension_score,
            "description": phase_data["description"],
            "dm_guidance": phase_data["dm_guidance"],
            "narration_style": phase_data["narration_style"],
            "emoji": phase_data["emoji"]
        }
    
    @staticmethod
    def adjust_narration_for_tension(narration: str, tension_score: int) -> str:
        """
        Modify narration based on tension level.
        
        DMG p.24 guidance:
        - Calm: Brief, functional
        - Building: Atmospheric, ominous
        - Tense: Suspenseful, partial reveals
        - Climax: Fast-paced, exciting
        - Resolution: Conclusive, rewarding
        
        Note: This is a light touch - main adjustment happens in DM prompt.
        """
        phase = TensionManager.get_tension_phase(tension_score)
        emoji = TensionManager.TENSION_LEVELS[phase]["emoji"]
        
        # Add phase emoji to beginning (subtle indicator)
        # Don't modify the narration text itself - that's handled by DM prompt adjustments
        return f"{emoji} {narration}"
    
    @staticmethod
    def should_introduce_tension_break(
        current_tension: int,
        session_duration_minutes: int
    ) -> bool:
        """
        DMG p.24: "Taking Breaks - Use natural pause points for breaks"
        
        Determine if the narrative needs a tension break (calm period).
        """
        # After climax, allow resolution
        if current_tension > 80 and session_duration_minutes > 30:
            return True
        
        # Long high-tension period needs relief
        if current_tension > 60 and session_duration_minutes > 60:
            return True
        
        return False
    
    @staticmethod
    def get_tension_transition_narration(from_phase: str, to_phase: str) -> str:
        """
        Generate transition narration when tension phase changes.
        
        DMG p.24: Smooth transitions between pacing phases.
        """
        transitions = {
            ("calm", "building"): "The air grows heavy with anticipation...",
            ("building", "tense"): "Your senses sharpen as danger draws near...",
            ("tense", "climax"): "The moment of action is upon you!",
            ("climax", "resolution"): "The immediate danger passes...",
            ("resolution", "calm"): "You take a moment to catch your breath and regroup.",
            ("tense", "calm"): "The danger seems to have passed, for now.",
            ("climax", "calm"): "With the threat eliminated, peace returns."
        }
        
        return transitions.get((from_phase, to_phase), "")
    
    @staticmethod
    def update_tension_state(
        tension_score: int,
        world_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update world_state with current tension information.
        
        Returns updated tension_state dict to be saved in world_state.
        """
        current_phase = TensionManager.get_tension_phase(tension_score)
        
        # Get previous phase if it exists
        previous_state = world_state.get('tension_state', {})
        previous_phase = previous_state.get('phase', 'calm')
        
        # Check if phase changed
        phase_changed = previous_phase != current_phase
        
        tension_state = {
            "score": tension_score,
            "phase": current_phase,
            "previous_phase": previous_phase,
            "phase_changed": phase_changed,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "phase_duration_minutes": previous_state.get('phase_duration_minutes', 0) + 1 if not phase_changed else 0
        }
        
        if phase_changed:
            logger.info(f"🔄 TENSION PHASE TRANSITION: {previous_phase} → {current_phase}")
            transition_text = TensionManager.get_tension_transition_narration(previous_phase, current_phase)
            if transition_text:
                tension_state["transition_narration"] = transition_text
        
        return tension_state
