from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
import random
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from models.character import Character, CharacterCreate, CharacterUpdate, CharacterStats, SpellSlot
    from services.game_engine import game_engine
    from services.ai_service import ai_service
    IMPORTS_OK = True
except ImportError as e:
    print(f"Character routes import error: {e}")
    IMPORTS_OK = False
    
    # Fallback basic models
    from pydantic import BaseModel
    from typing import Dict
    
    class CharacterStats(BaseModel):
        strength: int
        dexterity: int
        constitution: int
        intelligence: int
        wisdom: int
        charisma: int
    
    class CharacterCreate(BaseModel):
        name: str
        race: str
        character_class: str
        background: str
        stats: CharacterStats

router = APIRouter(prefix="/characters", tags=["characters"])

# In-memory storage for demo - would be MongoDB in production
characters_db = {}

@router.post("/", response_model=Character)
async def create_character(character_data: CharacterCreate):
    """Create a new character with D&D 5e mechanics"""
    
    # Generate spell slots based on class
    spell_slots = []
    if character_data.character_class.lower() in ['wizard', 'cleric', 'sorcerer']:
        spell_slots = [SpellSlot(level=1, total=2, remaining=2)]
    elif character_data.character_class.lower() in ['ranger', 'paladin']:
        # Rangers and Paladins get spells at higher levels
        spell_slots = []
    
    # Calculate hit points based on class and constitution
    class_hit_dice = {
        'fighter': 10,
        'ranger': 10,
        'wizard': 6,
        'cleric': 8,
        'rogue': 8,
        'barbarian': 12,
        'sorcerer': 6,
        'warlock': 8
    }
    
    hit_die = class_hit_dice.get(character_data.character_class.lower(), 8)
    constitution_modifier = game_engine.get_stat_modifier(character_data.stats.constitution)
    hit_points = hit_die + constitution_modifier
    
    # Create character
    character = Character(
        name=character_data.name,
        race=character_data.race,
        character_class=character_data.character_class,
        background=character_data.background,
        stats=character_data.stats,
        hit_points=hit_points,
        max_hit_points=hit_points,
        spell_slots=spell_slots,
        current_location="ravens-hollow",  # Starting location
        ambitions=_generate_ambitions(character_data.character_class, character_data.background)
    )
    
    # Store in database
    characters_db[character.id] = character
    
    return character

@router.get("/{character_id}", response_model=Character)
async def get_character(character_id: str):
    """Get character by ID"""
    if character_id not in characters_db:
        raise HTTPException(status_code=404, detail="Character not found")
    
    character = characters_db[character_id]
    character.last_active = datetime.utcnow()
    return character

@router.put("/{character_id}", response_model=Character)
async def update_character(character_id: str, updates: CharacterUpdate):
    """Update character data"""
    if character_id not in characters_db:
        raise HTTPException(status_code=404, detail="Character not found")
    
    character = characters_db[character_id]
    
    # Apply updates
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(character, field):
            setattr(character, field, value)
    
    character.last_active = datetime.utcnow()
    return character

@router.post("/{character_id}/ability-check")
async def make_ability_check(
    character_id: str,
    ability: str,
    dc: Optional[int] = None,
    context: dict = None
):
    """Make an ability check for the character"""
    if character_id not in characters_db:
        raise HTTPException(status_code=404, detail="Character not found")
    
    character = characters_db[character_id]
    
    # Use provided DC or calculate dynamic DC
    if dc is None:
        action = context.get('action', 'general') if context else 'general'
        dc, explanation = await game_engine.calculate_dynamic_dc(action, character, context or {})
    else:
        explanation = f"Manual DC: {dc}"
    
    # Make the check
    result = await game_engine.make_ability_check(character, ability, dc, context)
    result['dc_explanation'] = explanation
    
    # Update character in database
    characters_db[character_id] = character
    
    return result
from services.progression_service import get_xp_to_next

@router.post("/{character_id}/level-up")
async def level_up_character(character_id: str):
    """Level up using canonical XP progression"""

    if character_id not in characters_db:
        raise HTTPException(status_code=404, detail="Character not found")

    character = characters_db[character_id]

    xp_needed = get_xp_to_next(character.level)

    if xp_needed <= 0:
        raise HTTPException(status_code=400, detail="Already at max level")

    if character.experience < xp_needed:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough XP. Need {xp_needed}, have {character.experience}"
        )

    # Deduct XP
    character.experience -= xp_needed

    # Increase level
    character.level += 1

    # TODO: HP gain, spell slots, etc, using standardized logic later

    return { "message": f"{character.name} reached level {character.level}" }

    # Add spell slots if spellcaster
    if character.character_class.lower() in ['wizard', 'cleric', 'sorcerer']:
        # Simplified spell slot progression
        if character.level == 2:
            character.spell_slots.append(SpellSlot(level=1, total=1, remaining=1))
        elif character.level == 3:
            character.spell_slots.append(SpellSlot(level=2, total=2, remaining=2))
    
    return {
        "message": f"{character.name} reached level {character.level}!",
        "hp_gained": hp_increase,
        "new_total_hp": character.max_hit_points
    }

@router.post("/{character_id}/rest")
async def rest_character(character_id: str, rest_type: str = "short"):
    """Rest to recover resources"""
    if character_id not in characters_db:
        raise HTTPException(status_code=404, detail="Character not found")
    
    character = characters_db[character_id]
    
    if rest_type == "short":
        # Short rest - recover some hit points and abilities
        recovery = min(character.level, character.max_hit_points - character.hit_points)
        character.hit_points += recovery
        message = f"Short rest completed. Recovered {recovery} hit points."
        
    elif rest_type == "long":
        # Long rest - full recovery
        character.hit_points = character.max_hit_points
        
        # Restore spell slots
        for slot in character.spell_slots:
            slot.remaining = slot.total
            
        message = "Long rest completed. Fully recovered hit points and spell slots."
        
    else:
        raise HTTPException(status_code=400, detail="Invalid rest type. Use 'short' or 'long'")
    
    return {"message": message, "current_hp": character.hit_points}

@router.get("/{character_id}/stats")
async def get_character_stats(character_id: str):
    """Get detailed character statistics"""
    if character_id not in characters_db:
        raise HTTPException(status_code=404, detail="Character not found")
    
    character = characters_db[character_id]
    
    # Calculate derived stats
    stats_with_modifiers = {}
    for stat_name in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
        value = getattr(character.stats, stat_name)
        modifier = game_engine.get_stat_modifier(value)
        stats_with_modifiers[stat_name] = {
            'value': value,
            'modifier': modifier,
            'modifier_string': f"+{modifier}" if modifier >= 0 else str(modifier)
        }
    
    return {
        'character_id': character.id,
        'name': character.name,
        'level': character.level,
        'experience': character.experience,
        'hit_points': character.hit_points,
        'max_hit_points': character.max_hit_points,
        'stats': stats_with_modifiers,
        'proficiency_bonus': game_engine.get_proficiency_bonus(character.level),
        'armor_class': 10 + game_engine.get_stat_modifier(character.stats.dexterity),  # Base AC
        'spell_slots': character.spell_slots,
        'traits': [trait.dict() for trait in character.traits],
        'current_location': character.current_location
    }

@router.post("/{character_id}/evolve-traits")
async def evolve_character_traits(character_id: str, context: dict = None):
    """Trigger trait evolution based on recent experiences"""
    if character_id not in characters_db:
        raise HTTPException(status_code=404, detail="Character not found")
    
    character = characters_db[character_id]
    changes = await game_engine.evolve_character_traits(character, context or {})
    
    # Update character in database
    characters_db[character_id] = character
    
    return {
        'trait_changes': changes,
        'current_traits': [trait.dict() for trait in character.traits]
    }

def _generate_ambitions(character_class: str, background: str) -> List[str]:
    """Generate character ambitions based on class and background"""
    class_ambitions = {
        'fighter': ['Become a legendary warrior', 'Protect the innocent', 'Master all weapons'],
        'wizard': ['Uncover ancient knowledge', 'Master powerful magic', 'Join the Circle of Mages'],
        'cleric': ['Spread divine will', 'Heal the suffering', 'Build a grand temple'],
        'rogue': ['Accumulate wealth', 'Master the shadows', 'Lead a thieves guild'],
        'ranger': ['Protect the wilderness', 'Track dangerous beasts', 'Become one with nature']
    }
    
    background_ambitions = {
        'noble': ['Reclaim family honor', 'Expand political influence'],
        'criminal': ['Go straight', 'Build a criminal empire'],
        'soldier': ['Rise through the ranks', 'Earn military honors'],
        'acolyte': ['Serve faithfully', 'Perform miracles'],
        'folk hero': ['Protect common folk', 'Become a legend']
    }
    
    ambitions = []
    
    # Add class-based ambition
    if character_class.lower() in class_ambitions:
        ambitions.append(random.choice(class_ambitions[character_class.lower()]))
    
    # Add background-based ambition
    if background.lower() in background_ambitions:
        ambitions.append(random.choice(background_ambitions[background.lower()]))
    
    # Ensure at least one ambition
    if not ambitions:
        ambitions.append("Seek adventure and glory")
    
    return ambitions
