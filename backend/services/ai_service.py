"""
AI Service - Modular AI Response System
This service provides a unified interface for AI interactions.
Currently uses mock responses, easily replaceable with OpenAI GPT-4o later.
"""

from typing import Dict, List, Optional, Any
import random
import json
from datetime import datetime

class AIService:
    def __init__(self):
        self.conversation_history = {}
        self.context_memory = {}
        
    async def get_ai_response(
        self, 
        prompt: str, 
        context: Dict[str, Any] = None,
        response_type: str = "general"
    ) -> str:
        """
        Main AI response function - will be replaced with OpenAI API later
        
        Args:
            prompt: The input text/command from the player
            context: Game context (character, location, NPCs, etc.)
            response_type: Type of response needed ("dialogue", "narration", "ability_check", etc.)
        """
        if context is None:
            context = {}
            
        # Mock AI responses based on type and context
        if response_type == "npc_dialogue":
            return await self._generate_npc_dialogue(prompt, context)
        elif response_type == "narration":
            return await self._generate_narration(prompt, context)
        elif response_type == "ability_check":
            return await self._generate_ability_check_response(prompt, context)
        elif response_type == "world_description":
            return await self._generate_world_description(prompt, context)
        elif response_type == "event_generation":
            return await self._generate_event(prompt, context)
        else:
            return await self._generate_general_response(prompt, context)
    
    async def _generate_npc_dialogue(self, prompt: str, context: Dict) -> str:
        """Generate NPC dialogue based on their personality and context"""
        npc = context.get('npc', {})
        character = context.get('character', {})
        location = context.get('location', {})
        
        # Mock responses based on NPC traits and relationship
        if npc.get('occupation') == 'Blacksmith':
            responses = [
                "Ah, looking for quality metalwork? You've come to the right place, friend.",
                "These are dangerous times for travelers. Make sure your blade is sharp.",
                "I've been working iron since before you were born. What can I craft for you?",
                "The ore from the northern mines isn't what it used to be. Damn goblins disrupting trade."
            ]
        elif npc.get('occupation') == 'Innkeeper':
            responses = [
                "Welcome to my establishment! Looking for a room, or perhaps some local gossip?",
                "You have the look of someone with interesting tales. Care to share over an ale?",
                "Strange happenings lately. The ravens seem more restless than usual...",
                "A word of advice - avoid the old forest road after dark."
            ]
        elif npc.get('occupation') == 'Priest' or npc.get('occupation') == 'Cleric':
            responses = [
                "May the light guide your path, traveler. These are dark times indeed.",
                "I sense a troubled spirit in you. Perhaps prayer might bring clarity?",
                "The omens speak of change coming to our lands. We must be prepared.",
                "Faith is our shield against the encroaching darkness."
            ]
        else:
            responses = [
                "Greetings, stranger. What brings you to these parts?",
                "Times are hard, but we endure. What can I do for you?",
                "You're not from around here, are you? I can always tell.",
                "Watch yourself out there. Not everyone is as friendly as I am."
            ]
        
        # Add relationship modifier to response tone
        relationship = context.get('relationship', 0)
        if relationship > 0.5:
            responses = [r + " You're always welcome here." for r in responses]
        elif relationship < -0.5:
            responses = [r.replace("friend", "stranger") for r in responses]
        
        return random.choice(responses)
    
    async def _generate_narration(self, prompt: str, context: Dict) -> str:
        """Generate narrative descriptions of actions and environments"""
        location = context.get('location', {})
        character = context.get('character', {})
        action = prompt.lower()
        
        if 'look' in action or 'examine' in action:
            descriptions = [
                f"You survey {location.get('name', 'the area')} with keen eyes. The {location.get('terrain', 'landscape')} stretches before you, marked by the passage of countless souls.",
                f"Your gaze takes in the details of {location.get('name', 'your surroundings')}. The {location.get('climate', 'atmosphere')} climate has shaped both the land and its people.",
                f"As you observe {location.get('name', 'the location')}, you notice how the {location.get('primary_building_material', 'local architecture')} reflects the available resources."
            ]
        elif 'search' in action or 'investigate' in action:
            descriptions = [
                "You methodically search the area, your trained eyes picking up details others might miss.",
                "Your investigation reveals subtle clues about the recent activities in this place.",
                "As you examine the surroundings more closely, patterns begin to emerge."
            ]
        elif 'travel' in action or 'move' in action:
            descriptions = [
                "You set out on your journey, the path ahead filled with unknown possibilities.",
                "The road stretches before you, each step taking you further from the familiar.",
                "You begin to travel, alert to both the beauty and dangers of the landscape."
            ]
        else:
            descriptions = [
                "Your actions ripple through the world around you, setting events in motion.",
                "The consequences of your choice begin to unfold in ways both seen and unseen.",
                "Time moves forward, carrying the weight of your decisions."
            ]
        
        return random.choice(descriptions)
    
    async def _generate_ability_check_response(self, prompt: str, context: Dict) -> str:
        """Determine if an ability check is needed and provide context"""
        action = prompt.lower()
        character = context.get('character', {})
        
        # Determine appropriate ability and DC based on action
        if any(word in action for word in ['climb', 'jump', 'lift', 'break']):
            ability = 'strength'
            dc = random.randint(12, 18)
        elif any(word in action for word in ['sneak', 'dodge', 'balance', 'hide']):
            ability = 'dexterity' 
            dc = random.randint(10, 16)
        elif any(word in action for word in ['endure', 'resist', 'survive']):
            ability = 'constitution'
            dc = random.randint(12, 16)
        elif any(word in action for word in ['recall', 'analyze', 'deduce', 'research']):
            ability = 'intelligence'
            dc = random.randint(10, 18)
        elif any(word in action for word in ['notice', 'perceive', 'sense', 'intuition']):
            ability = 'wisdom'
            dc = random.randint(8, 16)
        elif any(word in action for word in ['persuade', 'intimidate', 'deceive', 'perform']):
            ability = 'charisma'
            dc = random.randint(10, 18)
        else:
            # General check
            ability = random.choice(['wisdom', 'intelligence'])
            dc = random.randint(12, 15)
        
        return json.dumps({
            'requires_check': True,
            'ability': ability,
            'dc': dc,
            'context': f"This action requires a {ability.title()} check (DC {dc})"
        })
    
    async def _generate_world_description(self, prompt: str, context: Dict) -> str:
        """Generate rich descriptions of world elements"""
        location = context.get('location', {})
        climate = location.get('climate', 'temperate')
        terrain = location.get('terrain', 'plains')
        
        descriptions = {
            'temperate': [
                "The mild climate has fostered lush growth, with ancient trees standing sentinel over well-trodden paths.",
                "Seasons flow gently here, each bringing its own character to the landscape.",
                "The temperate weather makes this region welcoming to travelers and traders alike."
            ],
            'arid': [
                "The dry air carries whispers of ancient secrets buried in the shifting sands.",
                "Heat shimmers rise from sun-baked earth, creating mirages that dance on the horizon.",
                "Life here is precious and hardy, adapted to the harsh embrace of the desert."
            ],
            'arctic': [
                "The bitter cold cuts through even the thickest cloaks, demanding respect from all who venture here.",
                "Snow and ice dominate the landscape, creating a world of stark, crystalline beauty.",
                "The aurora dances overhead, painting the night sky in ethereal hues."
            ]
        }
        
        climate_descriptions = descriptions.get(climate, descriptions['temperate'])
        return random.choice(climate_descriptions)
    
    async def _generate_event(self, prompt: str, context: Dict) -> str:
        """Generate dynamic world events based on context"""
        location = context.get('location', {})
        npcs = context.get('npcs', [])
        
        event_types = [
            "A merchant caravan has gone missing on the trade routes, causing concern among local traders.",
            "Strange lights have been seen in the night sky, sparking rumors and superstitions.",
            "A mysterious figure has been asking questions about ancient artifacts.",
            "Local wildlife has been acting strangely, fleeing from something in the deep wilderness.",
            "A traveling bard brings news of political upheaval in distant lands.",
            "An old ruin has been discovered, revealing hints of a forgotten civilization."
        ]
        
        return random.choice(event_types)
    
    async def _generate_general_response(self, prompt: str, context: Dict) -> str:
        """Generate general AI responses for unspecified contexts"""
        responses = [
            "The world responds to your presence, full of hidden possibilities.",
            "Your words carry weight in this realm where thought becomes reality.",
            "The fabric of the world shifts subtly around your intentions.",
            "Something stirs in response to your actions, though its nature remains unclear."
        ]
        
        return random.choice(responses)
    
    async def parse_player_intent(self, command: str, context: Dict) -> Dict[str, Any]:
        """
        Parse player commands to determine intent and required actions
        Will be enhanced with AI later for semantic understanding
        """
        command = command.lower().strip()
        
        # Basic intent classification
        intent_mapping = {
            'dialogue': ['talk', 'speak', 'ask', 'tell', 'say', 'conversation', 'chat'],
            'movement': ['go', 'travel', 'move', 'walk', 'run', 'enter', 'leave', 'exit'],
            'examination': ['look', 'examine', 'inspect', 'observe', 'check', 'view'],
            'search': ['search', 'find', 'hunt', 'seek', 'investigate', 'explore'],
            'combat': ['attack', 'fight', 'strike', 'battle', 'hit', 'kill'],
            'magic': ['cast', 'spell', 'magic', 'enchant', 'summon'],
            'social': ['persuade', 'intimidate', 'deceive', 'charm', 'influence'],
            'trade': ['buy', 'sell', 'trade', 'purchase', 'barter', 'shop'],
            'rest': ['rest', 'sleep', 'camp', 'recover', 'heal'],
            'inventory': ['use', 'equip', 'unequip', 'drop', 'pick', 'take', 'give']
        }
        
        detected_intent = 'general'
        confidence = 0.0
        
        for intent, keywords in intent_mapping.items():
            for keyword in keywords:
                if keyword in command:
                    detected_intent = intent
                    confidence = 0.8  # Mock confidence score
                    break
            if confidence > 0:
                break
        
        # Extract potential targets (NPCs, objects, directions)
        potential_targets = []
        if context.get('npcs'):
            for npc in context['npcs']:
                npc_name = npc.get('name', '').lower()
                if npc_name in command:
                    potential_targets.append({
                        'type': 'npc',
                        'id': npc.get('id'),
                        'name': npc.get('name')
                    })
        
        # Direction parsing
        directions = ['north', 'south', 'east', 'west', 'up', 'down', 'inside', 'outside']
        for direction in directions:
            if direction in command:
                potential_targets.append({
                    'type': 'direction',
                    'value': direction
                })
        
        return {
            'intent': detected_intent,
            'confidence': confidence,
            'original_command': command,
            'targets': potential_targets,
            'requires_ai_processing': confidence < 0.7  # Low confidence = needs AI
        }

# Global AI service instance
ai_service = AIService()