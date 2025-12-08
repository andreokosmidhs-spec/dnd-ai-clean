from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from services.ai_service import ai_service
from services.game_engine import game_engine
from models.character import Character
from models.npc import NPC
from models.world import Location

router = APIRouter(prefix="/game", tags=["game"])

# Game session storage
game_sessions = {}

@router.post("/session/start")
async def start_game_session(character_id: str):
    """Start a new game session"""
    session_id = str(uuid.uuid4())
    
    game_sessions[session_id] = {
        'character_id': character_id,
        'session_start': datetime.utcnow(),
        'action_count': 0,
        'current_context': {},
        'conversation_history': []
    }
    
    return {
        'session_id': session_id,
        'message': 'Game session started',
        'character_id': character_id
    }

@router.post("/session/{session_id}/action")
async def process_game_action(
    session_id: str, 
    action: str, 
    context: Dict[str, Any] = None
):
    """Process a player action through the AI system"""
    
    if session_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    session = game_sessions[session_id]
    session['action_count'] += 1
    
    if context is None:
        context = {}
    
    # Parse player intent
    intent_data = await ai_service.parse_player_intent(action, context)
    
    # Mock game state for processing
    mock_context = {
        'session_id': session_id,
        'character_id': session['character_id'],
        'location_id': context.get('location_id', 'ravens-hollow'),
        'npcs': context.get('npcs', []),
        'current_context': session.get('current_context', {})
    }
    
    response_data = {
        'session_id': session_id,
        'action_number': session['action_count'],
        'player_action': action,
        'intent': intent_data,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Process based on intent
    if intent_data['intent'] == 'dialogue':
        response_data['response'] = await _process_dialogue_action(action, mock_context)
        response_data['type'] = 'dialogue'
        
    elif intent_data['intent'] == 'examination':
        response_data['response'] = await _process_examination_action(action, mock_context)
        response_data['type'] = 'description'
        
    elif intent_data['intent'] == 'movement':
        response_data['response'] = await _process_movement_action(action, mock_context)
        response_data['type'] = 'movement'
        
    elif intent_data['intent'] == 'combat':
        response_data['response'] = await _process_combat_action(action, mock_context)
        response_data['type'] = 'combat'
        
    elif intent_data['intent'] == 'search':
        response_data['response'] = await _process_search_action(action, mock_context)
        response_data['type'] = 'search'
        
    else:
        # General AI response
        ai_response = await ai_service.get_ai_response(action, mock_context, 'general')
        response_data['response'] = {
            'message': ai_response,
            'requires_input': True
        }
        response_data['type'] = 'general'
    
    # Update session context
    session['current_context'].update(context)
    session['conversation_history'].append({
        'action': action,
        'response': response_data['response'],
        'timestamp': datetime.utcnow()
    })
    
    return response_data

@router.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get current game session status"""
    if session_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    session = game_sessions[session_id]
    
    return {
        'session_id': session_id,
        'character_id': session['character_id'],
        'session_duration': str(datetime.utcnow() - session['session_start']),
        'action_count': session['action_count'],
        'current_context': session['current_context'],
        'recent_actions': session['conversation_history'][-5:]  # Last 5 actions
    }

@router.post("/session/{session_id}/ability-check")
async def trigger_ability_check(
    session_id: str,
    ability: str,
    action_context: str,
    dc: Optional[int] = None
):
    """Trigger an ability check during gameplay"""
    if session_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    session = game_sessions[session_id]
    
    # Mock character for ability check
    mock_character = Character(
        id=session['character_id'],
        name="Player Character",
        race="Human",
        character_class="Fighter",
        background="Soldier",
        stats={
            "strength": 15,
            "dexterity": 14, 
            "constitution": 13,
            "intelligence": 12,
            "wisdom": 13,
            "charisma": 11
        },
        hit_points=20,
        max_hit_points=20,
        current_location="ravens-hollow"
    )
    
    # Calculate or use provided DC
    if dc is None:
        dc, explanation = await game_engine.calculate_dynamic_dc(
            action_context, 
            mock_character, 
            session['current_context']
        )
    else:
        explanation = f"Manual DC: {dc}"
    
    # Make the check
    result = await game_engine.make_ability_check(
        mock_character, 
        ability, 
        dc, 
        {'action': action_context}
    )
    
    # Generate narrative response
    if result['success']:
        narrative = await ai_service.get_ai_response(
            f"Success on {ability} check for {action_context}",
            {'result': result, 'context': action_context},
            'narration'
        )
    else:
        narrative = await ai_service.get_ai_response(
            f"Failure on {ability} check for {action_context}",
            {'result': result, 'context': action_context},
            'narration'
        )
    
    return {
        'ability_check': result,
        'narrative': narrative,
        'dc_explanation': explanation
    }

@router.post("/world/generate-content")
async def generate_world_content(
    content_type: str,
    context: Dict[str, Any] = None
):
    """Generate world content using AI"""
    
    if context is None:
        context = {}
    
    if content_type == 'location':
        response = await ai_service.get_ai_response(
            "Generate a detailed location description",
            context,
            'world_description'
        )
    elif content_type == 'npc':
        response = await ai_service.get_ai_response(
            "Generate an interesting NPC",
            context,
            'npc_dialogue'
        )
    elif content_type == 'event':
        response = await ai_service.get_ai_response(
            "Generate a world event",
            context,
            'event_generation'
        )
    else:
        response = await ai_service.get_ai_response(
            f"Generate {content_type} content",
            context,
            'general'
        )
    
    return {
        'content_type': content_type,
        'generated_content': response,
        'context_used': context,
        'timestamp': datetime.utcnow()
    }

async def _process_dialogue_action(action: str, context: Dict) -> Dict[str, Any]:
    """Process dialogue actions"""
    
    # Extract NPC target if mentioned
    npc_target = None
    for target in context.get('npcs', []):
        if target.get('name', '').lower() in action.lower():
            npc_target = target
            break
    
    if npc_target:
        # Generate NPC response
        dialogue_context = {
            'npc': npc_target,
            'player_message': action,
            'relationship': 0.0  # Neutral starting relationship
        }
        
        npc_response = await ai_service.get_ai_response(
            action, 
            dialogue_context, 
            'npc_dialogue'
        )
        
        return {
            'type': 'npc_dialogue',
            'npc_name': npc_target.get('name'),
            'npc_response': npc_response,
            'relationship_change': 0.1,  # Small positive change for talking
            'conversation_continues': True
        }
    else:
        return {
            'type': 'general_dialogue',
            'message': "There's no one here to talk to, but you speak your thoughts aloud.",
            'suggestion': "Try 'talk to [NPC name]' when NPCs are present."
        }

async def _process_examination_action(action: str, context: Dict) -> Dict[str, Any]:
    """Process examination/look actions"""
    
    location_context = {
        'location': context.get('current_location', {}),
        'action': action
    }
    
    description = await ai_service.get_ai_response(
        action,
        location_context,
        'world_description'
    )
    
    # Check if an ability check might be needed
    if 'closely' in action.lower() or 'carefully' in action.lower():
        investigation_needed = True
        suggested_check = 'wisdom'
    else:
        investigation_needed = False
        suggested_check = None
    
    return {
        'type': 'examination',
        'description': description,
        'investigation_needed': investigation_needed,
        'suggested_check': suggested_check,
        'detailed_view': 'closely' in action.lower()
    }

async def _process_movement_action(action: str, context: Dict) -> Dict[str, Any]:
    """Process movement actions"""
    
    # Parse direction or destination
    directions = ['north', 'south', 'east', 'west', 'up', 'down']
    direction = None
    
    for dir_word in directions:
        if dir_word in action.lower():
            direction = dir_word
            break
    
    if direction:
        # Generate travel description
        travel_context = {
            'direction': direction,
            'current_location': context.get('location_id', 'unknown')
        }
        
        description = await ai_service.get_ai_response(
            f"Traveling {direction}",
            travel_context,
            'narration'
        )
        
        return {
            'type': 'movement',
            'direction': direction,
            'description': description,
            'requires_check': True,
            'check_type': 'constitution',
            'travel_time': '1 hour'
        }
    else:
        return {
            'type': 'movement_unclear',
            'message': "Where would you like to go? Try specifying a direction (north, south, east, west) or a destination."
        }

async def _process_combat_action(action: str, context: Dict) -> Dict[str, Any]:
    """Process combat actions"""
    
    # Generate combat scenario
    combat_context = {
        'action': action,
        'location': context.get('location_id', 'unknown')
    }
    
    scenario = await ai_service.get_ai_response(
        "Generate combat encounter",
        combat_context,
        'narration'
    )
    
    # Mock combat mechanics
    return {
        'type': 'combat',
        'scenario': scenario,
        'initiative_required': True,
        'suggested_checks': ['strength', 'dexterity'],
        'combat_started': True,
        'enemy_type': 'generated'
    }

async def _process_search_action(action: str, context: Dict) -> Dict[str, Any]:
    """Process search/investigation actions"""
    
    search_context = {
        'action': action,
        'location': context.get('location_id', 'unknown')
    }
    
    # Determine if ability check is needed
    check_needed = await ai_service.get_ai_response(
        action,
        search_context,
        'ability_check'
    )
    
    # Generate search results
    results = await ai_service.get_ai_response(
        action,
        search_context,
        'narration'
    )
    
    return {
        'type': 'search',
        'results': results,
        'ability_check_needed': True,
        'suggested_ability': 'wisdom',
        'dc_range': '12-16',
        'time_required': '10 minutes'
    }