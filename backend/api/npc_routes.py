from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
import random

from models.npc import NPC, NPCCreate, NPCInteraction, NPCStatus, NPCNeed, NPCValue, NPCTrait, NPCStats
from models.character import Character
from models.world import Location
from services.game_engine import game_engine
from services.ai_service import ai_service

router = APIRouter(prefix="/npcs", tags=["npcs"])

# In-memory storage for demo
npcs_db = {}

@router.post("/", response_model=NPC)
async def create_npc(npc_data: NPCCreate):
    """Create a new NPC with psychological depth"""
    
    # Generate dynamic needs based on occupation and status
    needs = _generate_npc_needs(npc_data.occupation, npc_data.status)
    
    # Generate values based on occupation and social context
    values = _generate_npc_values(npc_data.occupation)
    
    # Generate traits
    traits = _generate_npc_traits(npc_data.status)
    
    # Generate ambitions based on status
    ambitions = _generate_npc_ambitions(npc_data.status, npc_data.occupation)
    
    npc = NPC(
        name=npc_data.name,
        description=npc_data.description,
        occupation=npc_data.occupation,
        home_location=npc_data.home_location,
        current_location=npc_data.home_location,
        status=npc_data.status,
        stats=npc_data.stats,
        needs=needs,
        values=values,
        traits=traits,
        ambitions=ambitions,
        social_class=_determine_social_class(npc_data.occupation),
        dialogue_style=_determine_dialogue_style(npc_data.occupation),
        cooperation_tendency=random.uniform(0.3, 0.8),
        suspicion_level=random.uniform(0.2, 0.7)
    )
    
    npcs_db[npc.id] = npc
    return npc

@router.get("/location/{location_id}")
async def get_npcs_by_location(location_id: str) -> List[NPC]:
    """Get all NPCs currently at a location"""
    location_npcs = []
    for npc in npcs_db.values():
        if npc.current_location == location_id:
            location_npcs.append(npc)
    
    return location_npcs

@router.get("/{npc_id}", response_model=NPC)
async def get_npc(npc_id: str):
    """Get NPC by ID"""
    if npc_id not in npcs_db:
        raise HTTPException(status_code=404, detail="NPC not found")
    
    return npcs_db[npc_id]

@router.post("/interact")
async def interact_with_npc(interaction: NPCInteraction):
    """Process interaction between character and NPC"""
    
    # Get NPC
    if interaction.npc_id not in npcs_db:
        raise HTTPException(status_code=404, detail="NPC not found")
    
    npc = npcs_db[interaction.npc_id]
    
    # For now, create mock character and location objects
    # In production, these would be fetched from database
    mock_character = Character(
        id=interaction.character_id,
        name="Player Character",
        race="Human",
        character_class="Fighter",
        background="Soldier",
        stats={"strength": 15, "dexterity": 14, "constitution": 13, "intelligence": 12, "wisdom": 13, "charisma": 11},
        hit_points=20,
        max_hit_points=20,
        current_location=interaction.location
    )
    
    mock_location = Location(
        id=interaction.location,
        name="Mock Location",
        location_type="town",
        region="Test Region",
        climate="temperate",
        terrain="plains",
        population_size=500
    )
    
    # Process the interaction through game engine
    result = await game_engine.process_npc_interaction(
        mock_character, npc, interaction.interaction_type, 
        interaction.player_action, mock_location
    )
    
    # Update NPC in database
    npcs_db[interaction.npc_id] = npc
    
    return result

@router.post("/{npc_id}/evolve")
async def evolve_npc_traits(npc_id: str, environmental_context: dict = None):
    """Evolve NPC traits based on environmental and social factors"""
    if npc_id not in npcs_db:
        raise HTTPException(status_code=404, detail="NPC not found")
    
    npc = npcs_db[npc_id]
    
    # Simulate trait evolution
    changes = []
    
    for trait in npc.traits:
        # Wisdom-based stability check
        wisdom_modifier = game_engine.get_stat_modifier(npc.stats.wisdom)
        stability_roll = game_engine.roll_d20() + wisdom_modifier
        
        # Environmental influence
        environmental_pressure = environmental_context.get('pressure', 0.5) if environmental_context else 0.5
        stability_dc = int(trait.stability * 20 * (1 + environmental_pressure))
        
        if stability_roll < stability_dc:
            # Trait changes - Intelligence check for adaptation
            intelligence_modifier = game_engine.get_stat_modifier(npc.stats.intelligence)
            adaptation_roll = game_engine.roll_d20() + intelligence_modifier
            
            if adaptation_roll > 15:
                old_name = trait.name
                # Get new trait based on environment
                environmental_traits = _get_environmental_traits(environmental_context)
                if environmental_traits:
                    trait.name = random.choice(environmental_traits)
                    changes.append(f"{old_name} -> {trait.name}")
    
    return {
        'npc_id': npc_id,
        'trait_changes': changes,
        'current_traits': [trait.dict() for trait in npc.traits]
    }

@router.get("/{npc_id}/relationship/{character_id}")
async def get_npc_relationship(npc_id: str, character_id: str):
    """Get NPC's relationship with a specific character"""
    if npc_id not in npcs_db:
        raise HTTPException(status_code=404, detail="NPC not found")
    
    npc = npcs_db[npc_id]
    relationship = npc.relationships.get(character_id, 0)
    
    # Calculate relationship description
    if relationship > 0.8:
        description = "Devoted ally"
    elif relationship > 0.5:
        description = "Good friend"
    elif relationship > 0.2:
        description = "Friendly acquaintance"
    elif relationship > -0.2:
        description = "Neutral"
    elif relationship > -0.5:
        description = "Distrustful"
    elif relationship > -0.8:
        description = "Hostile"
    else:
        description = "Bitter enemy"
    
    # Get memories of this character
    memories = [memory for memory in npc.memories if memory.character_id == character_id]
    
    return {
        'npc_id': npc_id,
        'character_id': character_id,
        'relationship_value': relationship,
        'relationship_description': description,
        'memory_count': len(memories),
        'recent_memories': [memory.dict() for memory in memories[-3:]]  # Last 3 memories
    }

@router.post("/{npc_id}/dialogue")
async def generate_npc_dialogue(
    npc_id: str, 
    player_message: str, 
    context: dict = None
):
    """Generate contextual NPC dialogue"""
    if npc_id not in npcs_db:
        raise HTTPException(status_code=404, detail="NPC not found")
    
    npc = npcs_db[npc_id]
    
    # Prepare context for AI
    ai_context = {
        'npc': npc.dict(),
        'player_message': player_message,
        'context': context or {}
    }
    
    # Generate response
    response = await ai_service.get_ai_response(
        player_message, 
        ai_context, 
        "npc_dialogue"
    )
    
    return {
        'npc_id': npc_id,
        'npc_name': npc.name,
        'response': response,
        'dialogue_style': npc.dialogue_style,
        'current_mood': npc.current_mood
    }

def _generate_npc_needs(occupation: str, status: NPCStatus) -> List[NPCNeed]:
    """Generate NPC needs based on occupation and status"""
    basic_needs = [
        NPCNeed(name="hunger", current_level=random.uniform(0.6, 0.9), importance=0.9),
        NPCNeed(name="shelter", current_level=random.uniform(0.7, 1.0), importance=0.8),
        NPCNeed(name="safety", current_level=random.uniform(0.5, 0.8), importance=0.8)
    ]
    
    # Add occupation-specific needs
    occupation_needs = {
        'blacksmith': [NPCNeed(name="craftsmanship pride", current_level=0.7, importance=0.6)],
        'innkeeper': [NPCNeed(name="social connection", current_level=0.8, importance=0.7)],
        'priest': [NPCNeed(name="spiritual fulfillment", current_level=0.9, importance=0.9)],
        'merchant': [NPCNeed(name="profit", current_level=0.6, importance=0.8)]
    }
    
    if occupation.lower() in occupation_needs:
        basic_needs.extend(occupation_needs[occupation.lower()])
    
    # Add status-based needs
    if status in [NPCStatus.RARE, NPCStatus.EPIC, NPCStatus.LEGENDARY]:
        basic_needs.append(NPCNeed(name="respect", current_level=0.7, importance=0.7))
        basic_needs.append(NPCNeed(name="influence", current_level=0.5, importance=0.6))
    
    return basic_needs

def _generate_npc_values(occupation: str) -> List[NPCValue]:
    """Generate NPC values based on occupation"""
    occupation_values = {
        'blacksmith': [
            NPCValue(name="craftsmanship", strength=0.9, flexibility=0.3),
            NPCValue(name="honesty", strength=0.7, flexibility=0.4)
        ],
        'innkeeper': [
            NPCValue(name="hospitality", strength=0.8, flexibility=0.5),
            NPCValue(name="community", strength=0.7, flexibility=0.4)
        ],
        'priest': [
            NPCValue(name="faith", strength=0.9, flexibility=0.2),
            NPCValue(name="compassion", strength=0.8, flexibility=0.3)
        ],
        'merchant': [
            NPCValue(name="profit", strength=0.8, flexibility=0.6),
            NPCValue(name="reputation", strength=0.7, flexibility=0.4)
        ],
        'guard': [
            NPCValue(name="order", strength=0.8, flexibility=0.3),
            NPCValue(name="duty", strength=0.7, flexibility=0.3)
        ]
    }
    
    return occupation_values.get(occupation.lower(), [
        NPCValue(name="survival", strength=0.7, flexibility=0.5),
        NPCValue(name="family", strength=0.6, flexibility=0.4)
    ])

def _generate_npc_traits(status: NPCStatus) -> List[NPCTrait]:
    """Generate NPC traits based on status"""
    common_traits = [
        NPCTrait(name="Hardworking", description="Diligent in their work", stability=0.8, environmental_factor=0.3),
        NPCTrait(name="Cautious", description="Careful in decisions", stability=0.7, environmental_factor=0.4)
    ]
    
    status_traits = {
        NPCStatus.COMMON: [
            NPCTrait(name="Humble", description="Modest and unassuming", stability=0.7, environmental_factor=0.5)
        ],
        NPCStatus.RARE: [
            NPCTrait(name="Ambitious", description="Driven to succeed", stability=0.6, environmental_factor=0.4),
            NPCTrait(name="Confident", description="Self-assured", stability=0.7, environmental_factor=0.3)
        ],
        NPCStatus.EPIC: [
            NPCTrait(name="Charismatic", description="Naturally inspiring", stability=0.8, environmental_factor=0.2),
            NPCTrait(name="Visionary", description="Sees the bigger picture", stability=0.7, environmental_factor=0.3)
        ],
        NPCStatus.LEGENDARY: [
            NPCTrait(name="Legendary Presence", description="Commands respect", stability=0.9, environmental_factor=0.1),
            NPCTrait(name="Wise", description="Possesses deep wisdom", stability=0.9, environmental_factor=0.2)
        ]
    }
    
    traits = common_traits.copy()
    if status in status_traits:
        traits.extend(status_traits[status])
    
    return traits

def _generate_npc_ambitions(status: NPCStatus, occupation: str) -> List[str]:
    """Generate NPC ambitions based on status and occupation"""
    ambition_count = {
        NPCStatus.COMMON: 1,
        NPCStatus.RARE: 2,
        NPCStatus.EPIC: 3,
        NPCStatus.LEGENDARY: 4
    }
    
    occupation_ambitions = {
        'blacksmith': [
            "Create a masterwork weapon",
            "Open a larger forge",
            "Train an apprentice",
            "Discover a new alloy"
        ],
        'innkeeper': [
            "Expand the inn",
            "Host a famous gathering",
            "Learn every traveler's story",
            "Create the perfect ale recipe"
        ],
        'priest': [
            "Build a grand temple", 
            "Perform a miracle",
            "Convert non-believers",
            "Receive a divine vision"
        ]
    }
    
    available_ambitions = occupation_ambitions.get(occupation.lower(), [
        "Achieve recognition",
        "Improve social standing",
        "Accumulate wealth",
        "Find true love",
        "Master a skill",
        "Travel the world"
    ])
    
    count = ambition_count.get(status, 1)
    return random.sample(available_ambitions, min(count, len(available_ambitions)))

def _determine_social_class(occupation: str) -> str:
    """Determine social class based on occupation"""
    class_mapping = {
        'priest': 'clergy',
        'cleric': 'clergy',
        'merchant': 'merchant',
        'blacksmith': 'artisan',
        'innkeeper': 'merchant',
        'guard': 'common',
        'farmer': 'peasant',
        'noble': 'nobility'
    }
    
    return class_mapping.get(occupation.lower(), 'common')

def _determine_dialogue_style(occupation: str) -> str:
    """Determine dialogue style based on occupation"""
    style_mapping = {
        'priest': 'formal',
        'cleric': 'formal',
        'noble': 'eloquent',
        'blacksmith': 'gruff',
        'innkeeper': 'casual',
        'guard': 'direct',
        'merchant': 'persuasive'
    }
    
    return style_mapping.get(occupation.lower(), 'neutral')

def _get_environmental_traits(context: dict) -> List[str]:
    """Get traits influenced by environmental context"""
    if not context:
        return ["Adaptable", "Observant"]
    
    environment_type = context.get('environment', 'neutral')
    
    trait_map = {
        'hostile': ['Paranoid', 'Aggressive', 'Survival-focused'],
        'peaceful': ['Trusting', 'Relaxed', 'Community-minded'],
        'chaotic': ['Flexible', 'Opportunistic', 'Street-smart'],
        'orderly': ['Disciplined', 'Rule-following', 'Predictable']
    }
    
    return trait_map.get(environment_type, ['Adaptable', 'Observant'])