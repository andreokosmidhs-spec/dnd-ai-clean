"""
NPC PERSONALITY ENGINE - DMG p.186, p.105
Implements distinctive NPC personalities with mannerisms, traits, and emotional states.

DMG p.186: "Give NPCs distinctive personalities and roles"
DMG p.105: "Make NPCs memorable through distinctive speech and behavior"
"""

import logging
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class NPCPersonalityEngine:
    """
    Generate and manage NPC personalities with traits, mannerisms, and emotional states.
    
    Based on DMG p.186 guidelines for memorable NPC creation.
    """
    
    # DMG p.186: Mannerisms make NPCs memorable
    MANNERISMS = [
        "speaks in third person",
        "constantly adjusts spectacles",
        "laughs at inappropriate times",
        "whispers even when not necessary",
        "uses overly formal language",
        "fidgets with coins or jewelry",
        "quotes obscure poets",
        "has a distinctive accent",
        "taps fingers rhythmically",
        "avoids eye contact",
        "speaks very loudly",
        "uses hand gestures excessively",
        "sniffs frequently",
        "clears throat before speaking",
        "repeats last word of sentences",
        "interrupts others constantly",
        "speaks in rhymes occasionally",
        "has a nervous laugh",
        "touches face when thinking",
        "stares intensely when listening",
        "uses archaic phrases",
        "mispronounces common words",
        "speaks slowly and deliberately",
        "has a habit of humming",
        "wrings hands when anxious"
    ]
    
    # Personality traits (DMG character building guidelines)
    PERSONALITY_TRAITS = [
        "optimistic", "pessimistic", "suspicious", "trusting",
        "ambitious", "content", "greedy", "generous",
        "brave", "cowardly", "arrogant", "humble",
        "curious", "cautious", "impulsive", "patient",
        "friendly", "aloof", "serious", "playful",
        "honest", "deceptive", "loyal", "self-serving"
    ]
    
    # DMG ideals, bonds, flaws
    IDEALS = [
        "order", "freedom", "power", "knowledge", 
        "honor", "tradition", "beauty", "greed",
        "glory", "redemption", "faith", "charity"
    ]
    
    BONDS = [
        "family", "guild", "oath", "mentor", 
        "debt", "revenge", "homeland", "sacred_place",
        "artifact", "promise", "lost_love", "duty"
    ]
    
    FLAWS = [
        "arrogance", "cowardice", "greed", "addiction",
        "secret", "prejudice", "vengeance", "envy",
        "pride", "stubbornness", "impulsiveness", "gullibility"
    ]
    
    # Emotional states (affects NPC behavior)
    EMOTIONAL_STATES = [
        "friendly", "neutral", "suspicious", "afraid",
        "hostile", "excited", "sad", "angry",
        "relaxed", "tense", "cheerful", "melancholic"
    ]
    
    # Role-based behavior templates (DMG p.105)
    ROLE_BEHAVIORS = {
        "innkeeper": {
            "typical_actions": ["greets warmly", "offers food and drink", "shares local gossip", "tends to customers"],
            "speech_style": "welcoming and chatty",
            "likely_knowledge": ["local news", "travelers", "rumors", "town events"]
        },
        "guard": {
            "typical_actions": ["stands at post", "questions strangers", "enforces law", "patrols area"],
            "speech_style": "formal and direct",
            "likely_knowledge": ["security", "laws", "recent crimes", "suspicious activity"]
        },
        "merchant": {
            "typical_actions": ["displays wares", "haggles prices", "appraises items", "seeks profit"],
            "speech_style": "persuasive and business-like",
            "likely_knowledge": ["trade routes", "item values", "supply and demand", "economics"]
        },
        "scholar": {
            "typical_actions": ["reads constantly", "takes notes", "lectures", "researches"],
            "speech_style": "verbose and technical",
            "likely_knowledge": ["history", "magic", "lore", "ancient texts"]
        },
        "criminal": {
            "typical_actions": ["watches carefully", "counts coins", "speaks in code", "seeks opportunities"],
            "speech_style": "evasive and cautious",
            "likely_knowledge": ["underworld", "black market", "secrets", "escape routes"]
        },
        "noble": {
            "typical_actions": ["gives orders", "maintains dignity", "judges others", "expects deference"],
            "speech_style": "refined and authoritative",
            "likely_knowledge": ["politics", "etiquette", "lineages", "court intrigue"]
        },
        "priest": {
            "typical_actions": ["prays", "offers blessings", "counsels", "performs rituals"],
            "speech_style": "solemn and spiritual",
            "likely_knowledge": ["religion", "theology", "healing", "divine lore"]
        },
        "farmer": {
            "typical_actions": ["works land", "tends animals", "complains about weather", "speaks plainly"],
            "speech_style": "simple and practical",
            "likely_knowledge": ["agriculture", "seasons", "local terrain", "weather patterns"]
        }
    }
    
    @staticmethod
    def generate_personality(
        npc_name: str,
        npc_role: str = "default",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete NPC personality.
        
        DMG p.186: "Give NPCs distinctive personalities and roles"
        
        Args:
            npc_name: Name of the NPC
            npc_role: Role/profession of NPC (innkeeper, guard, merchant, etc.)
            seed: Random seed for consistent generation
            
        Returns:
            Complete personality dict
        """
        if seed:
            random.seed(seed)
        
        # Normalize role
        role = npc_role.lower() if npc_role else "default"
        role_behavior = NPCPersonalityEngine.ROLE_BEHAVIORS.get(role, {})
        
        personality = {
            "name": npc_name,
            "role": role,
            "mannerisms": random.sample(NPCPersonalityEngine.MANNERISMS, 2),
            "personality_trait": random.choice(NPCPersonalityEngine.PERSONALITY_TRAITS),
            "ideal": random.choice(NPCPersonalityEngine.IDEALS),
            "bond": random.choice(NPCPersonalityEngine.BONDS),
            "flaw": random.choice(NPCPersonalityEngine.FLAWS),
            "emotional_state": "neutral",
            "role_behavior": role_behavior,
            "interaction_history": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"✨ Generated personality for {npc_name} ({role}): {personality['personality_trait']}")
        
        return personality
    
    @staticmethod
    def update_emotional_state(
        personality: Dict[str, Any],
        player_action: str,
        action_type: str
    ) -> str:
        """
        Update NPC emotional state based on player interaction.
        
        Args:
            personality: NPC personality dict
            player_action: What the player did
            action_type: Type of action (friendly, hostile, neutral, etc.)
            
        Returns:
            New emotional state
        """
        current_state = personality.get('emotional_state', 'neutral')
        
        # Define state transitions based on action type
        state_transitions = {
            "friendly": {
                "hostile": "suspicious",
                "afraid": "neutral",
                "suspicious": "neutral",
                "neutral": "friendly",
                "friendly": "friendly"
            },
            "hostile": {
                "friendly": "suspicious",
                "neutral": "hostile",
                "suspicious": "hostile",
                "afraid": "hostile",
                "hostile": "hostile"
            },
            "neutral": {
                "hostile": "suspicious",
                "friendly": "friendly",
                "suspicious": "suspicious",
                "neutral": "neutral"
            }
        }
        
        # Get transition map for action type
        transitions = state_transitions.get(action_type, {})
        new_state = transitions.get(current_state, current_state)
        
        # Record interaction in history
        personality['interaction_history'].append({
            "action": player_action,
            "action_type": action_type,
            "previous_state": current_state,
            "new_state": new_state,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Limit history to last 10 interactions
        if len(personality['interaction_history']) > 10:
            personality['interaction_history'] = personality['interaction_history'][-10:]
        
        personality['emotional_state'] = new_state
        
        logger.info(f"💭 {personality['name']} emotional state: {current_state} → {new_state}")
        
        return new_state
    
    @staticmethod
    def format_personality_for_prompt(personality: Dict[str, Any]) -> str:
        """
        Format personality data for inclusion in DM prompt.
        
        DMG p.186: Make NPCs memorable through distinctive characteristics
        
        Args:
            personality: NPC personality dict
            
        Returns:
            Formatted string for DM prompt
        """
        role_info = personality.get('role_behavior', {})
        
        prompt_block = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTIVE NPC: {personality['name']} ({personality['role']})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Personality Trait: {personality['personality_trait']}
Mannerisms: {', '.join(personality['mannerisms'])}
Ideal: {personality['ideal']}
Bond: {personality['bond']}
Flaw: {personality['flaw']}

Current Emotional State: {personality['emotional_state']}

Role Behavior ({personality['role']}):
- Speech Style: {role_info.get('speech_style', 'natural')}
- Typical Actions: {', '.join(role_info.get('typical_actions', ['interacts naturally']))}

Recent Interactions:
{NPCPersonalityEngine._format_interaction_history(personality['interaction_history'])}

DMG p.186 DIRECTIVE: Make this NPC memorable through:
1. Using their mannerisms in dialogue and actions
2. Reflecting their personality trait in responses
3. Speaking in their role-appropriate style
4. Reacting according to their emotional state
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return prompt_block
    
    @staticmethod
    def _format_interaction_history(history: List[Dict[str, Any]]) -> str:
        """Format interaction history for display"""
        if not history:
            return "No previous interactions"
        
        recent = history[-3:]  # Last 3 interactions
        formatted = []
        for interaction in recent:
            formatted.append(
                f"- Player: {interaction['action'][:50]}... "
                f"(NPC became {interaction['new_state']})"
            )
        return '\n'.join(formatted) if formatted else "No previous interactions"
    
    @staticmethod
    def get_role_appropriate_greeting(personality: Dict[str, Any]) -> str:
        """Generate a role-appropriate greeting for NPC"""
        role = personality['role']
        emotional_state = personality['emotional_state']
        
        greetings = {
            "innkeeper": {
                "friendly": "Welcome, friend! Come in, come in! What can I get for you?",
                "neutral": "Good day. Looking for a room or a meal?",
                "suspicious": "What brings you here? We don't want any trouble.",
                "hostile": "We're closed. You should leave."
            },
            "guard": {
                "friendly": "Greetings, citizen. Everything alright?",
                "neutral": "State your business.",
                "suspicious": "Hold there. I need to ask you some questions.",
                "hostile": "You're under arrest. Don't resist."
            },
            "merchant": {
                "friendly": "Ah, a potential customer! Come, see my wares!",
                "neutral": "Looking to buy or sell?",
                "suspicious": "I don't do business with troublemakers.",
                "hostile": "Get away from my shop!"
            }
        }
        
        role_greetings = greetings.get(role, {
            "friendly": "Hello there!",
            "neutral": "Yes?",
            "suspicious": "What do you want?",
            "hostile": "Leave me alone."
        })
        
        return role_greetings.get(emotional_state, role_greetings.get("neutral", "Hello."))


def generate_npc_personality(npc_name: str, npc_role: str = "default") -> Dict[str, Any]:
    """
    Convenience function for generating NPC personality.
    
    Args:
        npc_name: Name of the NPC
        npc_role: Role/profession (innkeeper, guard, merchant, etc.)
        
    Returns:
        Complete personality dict
    """
    return NPCPersonalityEngine.generate_personality(npc_name, npc_role)


def update_npc_emotional_state(
    personality: Dict[str, Any],
    player_action: str,
    action_type: str = "neutral"
) -> str:
    """
    Update NPC's emotional state based on player action.
    
    Args:
        personality: NPC personality dict
        player_action: Player's action text
        action_type: Type of action (friendly, hostile, neutral)
        
    Returns:
        New emotional state
    """
    return NPCPersonalityEngine.update_emotional_state(personality, player_action, action_type)


def format_for_dm_prompt(personality: Dict[str, Any]) -> str:
    """
    Format personality for DM prompt inclusion.
    
    Args:
        personality: NPC personality dict
        
    Returns:
        Formatted prompt block
    """
    return NPCPersonalityEngine.format_personality_for_prompt(personality)
