"""
Game Engine - Core game mechanics and state management
Handles ability checks, character progression, world state, and game logic
"""

import random
import math
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from models.character import Character, CharacterTrait, CharacterMemory
from models.npc import NPC, NPCMemory, NPCStatus
from models.world import Location, WorldEvent
from services.ai_service import ai_service

class GameEngine:
    def __init__(self):
        self.active_sessions = {}  # session_id -> game_state
        
    def roll_d20(self) -> int:
        """Roll a 20-sided die"""
        return random.randint(1, 20)
    
    def roll_dice(self, count: int, sides: int, modifier: int = 0) -> Tuple[int, List[int]]:
        """Roll multiple dice and return total and individual rolls"""
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + modifier
        return total, rolls
    
    def get_stat_modifier(self, stat_value: int) -> int:
        """Calculate D&D 5e ability modifier"""
        return math.floor((stat_value - 10) / 2)
    
    def get_proficiency_bonus(self, level: int) -> int:
        """Calculate proficiency bonus based on character level"""
        return math.ceil(level / 4) + 1
    
    async def make_ability_check(
        self, 
        character: Character, 
        ability: str, 
        dc: int, 
        context: Dict = None
    ) -> Dict[str, Any]:
        """
        Perform an ability check with contextual modifiers
        """
        if context is None:
            context = {}
        
        # Get base modifier
        stat_value = getattr(character.stats, ability)
        base_modifier = self.get_stat_modifier(stat_value)
        
        # Add proficiency if applicable
        proficiency_bonus = 0
        if context.get('proficient', False):
            proficiency_bonus = self.get_proficiency_bonus(character.level)
        
        # Environmental and situational modifiers
        circumstance_modifier = context.get('circumstance_modifier', 0)
        
        # Roll the dice
        roll = self.roll_d20()
        total = roll + base_modifier + proficiency_bonus + circumstance_modifier
        
        # Determine success
        success = total >= dc
        degree_of_success = total - dc if success else dc - total
        
        # Critical success/failure
        critical_success = roll == 20 and success
        critical_failure = roll == 1 and not success
        
        result = {
            'roll': roll,
            'base_modifier': base_modifier,
            'proficiency_bonus': proficiency_bonus,
            'circumstance_modifier': circumstance_modifier,
            'total': total,
            'dc': dc,
            'success': success,
            'critical_success': critical_success,
            'critical_failure': critical_failure,
            'degree_of_success': degree_of_success,
            'ability': ability
        }
        
        # Add to character memory
        memory = CharacterMemory(
            event=f"Made {ability} check (DC {dc}): {'Success' if success else 'Failure'}",
            location=character.current_location,
            emotional_impact=0.1 if success else -0.1
        )
        character.memories.append(memory)
        
        return result
    
    async def evolve_character_traits(self, character: Character, context: Dict) -> List[str]:
        """
        Evolve character traits based on experiences and environment
        Uses Wisdom and Intelligence for trait stability and adaptation
        """
        changes = []
        location = context.get('location')
        recent_events = context.get('recent_events', [])
        
        wisdom_modifier = self.get_stat_modifier(character.stats.wisdom)
        intelligence_modifier = self.get_stat_modifier(character.stats.intelligence)
        
        for trait in character.traits:
            # Wisdom check for trait stability
            stability_roll = self.roll_d20() + wisdom_modifier
            stability_dc = int(trait.stability * 20)  # Higher stability = higher DC to change
            
            if stability_roll < stability_dc:
                # Trait might change - Intelligence check for adaptation
                adaptation_roll = self.roll_d20() + intelligence_modifier
                
                if adaptation_roll > 15:  # Successfully adapt
                    # Get environmental traits from location
                    environmental_traits = self._get_environmental_traits(location)
                    if environmental_traits and random.random() > 0.7:
                        new_trait_name = random.choice(environmental_traits)
                        # Replace or modify existing trait
                        old_name = trait.name
                        trait.name = new_trait_name
                        trait.acquired_at = datetime.utcnow()
                        changes.append(f"'{old_name}' evolved into '{new_trait_name}' due to environmental influence")
        
        return changes
    
    def _get_environmental_traits(self, location: Optional[Location]) -> List[str]:
        """Get traits common to a location's environment"""
        if not location:
            return []
        
        trait_map = {
            'desert': ['Hardy', 'Cautious', 'Resourceful', 'Patient'],
            'forest': ['Stealthy', 'Nature-loving', 'Observant', 'Peaceful'],
            'mountains': ['Resilient', 'Determined', 'Sure-footed', 'Independent'], 
            'city': ['Streetwise', 'Social', 'Ambitious', 'Adaptable'],
            'arctic': ['Stoic', 'Prepared', 'Enduring', 'Isolated']
        }
        
        return trait_map.get(location.terrain, ['Adaptable', 'Observant'])
    
    async def calculate_dynamic_dc(
        self, 
        base_action: str, 
        character: Character, 
        context: Dict
    ) -> Tuple[int, str]:
        """
        Calculate context-aware Difficulty Class for actions
        Considers character stats, environment, and social factors
        """
        base_dc = 15  # Default moderate difficulty
        
        # Action-specific base DCs
        action_dcs = {
            'persuasion': 12,
            'intimidation': 14,
            'stealth': 13,
            'investigation': 15,
            'athletics': 15,
            'sleight_of_hand': 16,
            'deception': 14,
            'insight': 13
        }
        
        base_dc = action_dcs.get(base_action.lower(), base_dc)
        
        # Environmental modifiers
        location = context.get('location')
        if location:
            if location.rule_system.value == 'severe':
                base_dc += 2  # Harder to get away with things
            elif location.rule_system.value == 'lawless':
                base_dc -= 2  # Easier, but more dangerous
        
        # Reputation modifiers
        reputation = character.reputation.get(character.current_location, 0)
        if reputation > 0.5:
            base_dc -= 2  # Good reputation helps
        elif reputation < -0.5:
            base_dc += 3  # Bad reputation hinders
        
        # NPC relationship modifiers
        target_npc = context.get('target_npc')
        if target_npc:
            relationship = character.relationships.get(target_npc.id, 0)
            if relationship > 0.5:
                base_dc -= 3  # Good relationship helps significantly
            elif relationship < -0.5:
                base_dc += 3  # Bad relationship hinders
        
        # Stress and fatigue (mock implementation)
        if context.get('character_stressed', False):
            base_dc += 2
        
        # Ensure DC stays in reasonable bounds
        final_dc = max(5, min(25, base_dc))
        
        explanation = f"Base DC {action_dcs.get(base_action.lower(), 15)}"
        if reputation != 0:
            explanation += f", reputation modifier: {int(reputation * 2)}"
        if target_npc and character.relationships.get(target_npc.id, 0) != 0:
            rel_mod = int(character.relationships.get(target_npc.id, 0) * 3)
            explanation += f", relationship modifier: {rel_mod}"
        
        return final_dc, explanation
    
    async def process_npc_interaction(
        self, 
        character: Character, 
        npc: NPC, 
        interaction_type: str, 
        player_action: str,
        location: Location
    ) -> Dict[str, Any]:
        """
        Process interactions between character and NPCs
        Updates relationships, memories, and triggers AI responses
        """
        # Determine relationship change based on interaction
        relationship_change = await self._calculate_relationship_change(
            character, npc, interaction_type, player_action
        )
        
        # Update character relationship
        current_relationship = character.relationships.get(npc.id, 0)
        new_relationship = max(-1, min(1, current_relationship + relationship_change))
        character.relationships[npc.id] = new_relationship
        
        # Update character memory
        char_memory = CharacterMemory(
            event=f"Interacted with {npc.name}: {player_action}",
            location=location.id,
            npcs_involved=[npc.id],
            emotional_impact=relationship_change
        )
        character.memories.append(char_memory)
        
        # Update NPC memory
        npc_memory = NPCMemory(
            character_id=character.id,
            event_description=player_action,
            emotional_impact=relationship_change,
            location=location.id,
            relationship_change=relationship_change
        )
        npc.memories.append(npc_memory)
        
        # Update NPC relationship
        npc.relationships[character.id] = new_relationship
        
        # Add character to NPC's known characters if first meeting
        if character.id not in npc.known_characters:
            npc.known_characters.append(character.id)
        
        # Generate AI response based on context
        ai_context = {
            'npc': npc.dict(),
            'character': character.dict(),
            'location': location.dict(),
            'relationship': new_relationship,
            'interaction_type': interaction_type
        }
        
        ai_response = await ai_service.get_ai_response(
            player_action, 
            ai_context, 
            "npc_dialogue"
        )
        
        return {
            'npc_response': ai_response,
            'relationship_change': relationship_change,
            'new_relationship': new_relationship,
            'memory_created': True,
            'interaction_successful': True
        }
    
    async def _calculate_relationship_change(
        self, 
        character: Character, 
        npc: NPC, 
        interaction_type: str, 
        player_action: str
    ) -> float:
        """Calculate how an interaction affects NPC relationship"""
        base_change = 0.0
        
        # Interaction type base changes
        interaction_changes = {
            'friendly': 0.1,
            'trade': 0.05,
            'quest': 0.15,
            'hostile': -0.2,
            'deception': -0.3,
            'help': 0.2,
            'insult': -0.25
        }
        
        base_change = interaction_changes.get(interaction_type, 0.0)
        
        # Character charisma modifier
        charisma_mod = self.get_stat_modifier(character.stats.charisma)
        base_change += charisma_mod * 0.02  # Small charisma influence
        
        # NPC cooperation tendency
        cooperation_factor = npc.cooperation_tendency
        if base_change > 0:
            base_change *= (0.5 + cooperation_factor)  # More cooperative = bigger positive changes
        
        # NPC suspicion level
        suspicion_factor = npc.suspicion_level
        if base_change > 0:
            base_change *= (1.5 - suspicion_factor)  # More suspicious = smaller positive changes
        
        # Cap the change
        return max(-0.5, min(0.5, base_change))
    
    async def update_location_memory(
        self, 
        location: Location, 
        character: Character, 
        event: str, 
        reputation_change: float = 0.0
    ):
        """Update location's memory of character actions"""
        from models.world import LocationMemory
        
        memory = LocationMemory(
            character_id=character.id,
            event=event,
            reputation_change=reputation_change
        )
        
        location.recent_memories.append(memory)
        
        # Update character reputation at location
        current_rep = location.character_reputations.get(character.id, 0)
        new_rep = max(-1, min(1, current_rep + reputation_change))
        location.character_reputations[character.id] = new_rep
        character.reputation[location.id] = new_rep
    
    async def generate_dynamic_event(
        self, 
        location: Location, 
        characters_present: List[Character], 
        npcs_present: List[NPC]
    ) -> Optional[WorldEvent]:
        """Generate events based on current world state and NPC interactions"""
        
        # Check for value conflicts among NPCs
        conflicting_npcs = self._find_conflicting_npcs(npcs_present)
        
        if conflicting_npcs and random.random() > 0.8:  # 20% chance of conflict
            event_description = await ai_service.get_ai_response(
                f"Generate conflict between NPCs with opposing values",
                {
                    'location': location.dict(),
                    'npcs': [npc.dict() for npc in conflicting_npcs]
                },
                "event_generation"
            )
            
            from models.world import WorldEvent
            event = WorldEvent(
                title="Local Tension",
                description=event_description,
                event_type="social",
                affected_locations=[location.id],
                affected_npcs=[npc.id for npc in conflicting_npcs],
                severity=0.3
            )
            
            return event
        
        return None
    
    def _find_conflicting_npcs(self, npcs: List[NPC]) -> List[NPC]:
        """Find NPCs with conflicting values that might lead to events"""
        conflicting = []
        
        for i, npc1 in enumerate(npcs):
            for npc2 in npcs[i+1:]:
                # Check for opposing values
                for value1 in npc1.values:
                    for value2 in npc2.values:
                        if self._are_opposing_values(value1.name, value2.name):
                            if value1.strength > 0.7 and value2.strength > 0.7:
                                conflicting.extend([npc1, npc2])
                                break
        
        return list(set(conflicting))  # Remove duplicates
    
    def _are_opposing_values(self, value1: str, value2: str) -> bool:
        """Check if two values are naturally opposing"""
        opposing_pairs = [
            ('order', 'chaos'),
            ('justice', 'freedom'),
            ('wealth', 'generosity'),
            ('tradition', 'progress'),
            ('individual', 'community'),
            ('power', 'humility')
        ]
        
        value1_lower = value1.lower()
        value2_lower = value2.lower()
        
        for pair in opposing_pairs:
            if (value1_lower in pair[0] and value2_lower in pair[1]) or \
               (value1_lower in pair[1] and value2_lower in pair[0]):
                return True
        
        return False

# Global game engine instance
game_engine = GameEngine()