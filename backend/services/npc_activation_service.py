"""
NPC ACTIVATION SERVICE - Populates active NPCs from world blueprint based on location.

This service bridges the gap between static world_blueprint NPCs and active world_state NPCs,
ensuring NPCs are discoverable for targeting and interaction.

PHASE 2: Now generates NPC personalities on activation (DMG p.186)
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def generate_npc_personality_on_activation(
    npc_data: Dict[str, Any],
    world_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate personality for NPC on first activation.
    
    DMG p.186: Give NPCs distinctive personalities and roles
    
    Args:
        npc_data: NPC data from world blueprint
        world_state: World state to store personality
        
    Returns:
        Personality data
    """
    from services.npc_personality_service import generate_npc_personality
    
    npc_name = npc_data.get('name', 'Unknown')
    npc_role = npc_data.get('role', 'default')
    npc_id = npc_data.get('id', npc_name.lower().replace(' ', '_'))
    
    # Check if personality already exists
    if 'npc_personalities' not in world_state:
        world_state['npc_personalities'] = {}
    
    if npc_id in world_state['npc_personalities']:
        # Return existing personality
        return world_state['npc_personalities'][npc_id]
    
    # Generate new personality
    personality = generate_npc_personality(npc_name, npc_role)
    world_state['npc_personalities'][npc_id] = personality
    
    logger.info(f"✨ Generated personality for {npc_name}: {personality['personality_trait']}")
    
    return personality


def populate_active_npcs_for_location(
    location_name: str,
    world_blueprint: Dict[str, Any],
    world_state: Dict[str, Any]
) -> List[str]:
    """
    Populate active NPCs based on the current location.
    
    Args:
        location_name: Current location name
        world_blueprint: Static world blueprint with key_npcs
        world_state: Mutable world state
    
    Returns:
        List of NPC IDs that are now active
    """
    location_lower = location_name.lower()
    active_npc_ids = []
    
    logger.info(f"🎭 Activating NPCs for location: {location_name}")
    
    # Get all NPCs from blueprint
    key_npcs = world_blueprint.get('key_npcs', [])
    
    if not key_npcs:
        logger.warning("⚠️ No key_npcs found in world_blueprint")
        return []
    
    # Check starting town NPCs
    starting_town = world_blueprint.get('starting_town', {})
    starting_town_name = starting_town.get('name', '').lower()
    
    if starting_town_name and starting_town_name in location_lower:
        # Activate all NPCs associated with starting town
        for npc in key_npcs:
            npc_id = npc.get('id') or npc.get('name', '').lower().replace(' ', '_')
            
            # Ensure NPC has an ID
            if not npc.get('id'):
                npc['id'] = npc_id
            
            # Check if NPC is associated with this location
            npc_location_poi = npc.get('location_poi_id', '')
            
            # If NPC has no specific location, assume they're in starting town
            if not npc_location_poi or 'town' in npc.get('role', '').lower():
                active_npc_ids.append(npc_id)
                # PHASE 2: Generate personality on activation
                generate_npc_personality_on_activation(npc, world_state)
                logger.info(f"  ✅ Activated NPC: {npc.get('name')} ({npc_id})")
    
    # Check POI-specific NPCs
    pois = world_blueprint.get('points_of_interest', [])
    for poi in pois:
        poi_name = poi.get('name', '').lower()
        poi_id = poi.get('id', '')
        
        if poi_name in location_lower or location_lower in poi_name:
            # Activate NPCs at this POI
            for npc in key_npcs:
                npc_id = npc.get('id') or npc.get('name', '').lower().replace(' ', '_')
                npc_location_poi = npc.get('location_poi_id', '')
                
                if npc_location_poi == poi_id:
                    if npc_id not in active_npc_ids:
                        active_npc_ids.append(npc_id)
                        # PHASE 2: Generate personality on activation
                        generate_npc_personality_on_activation(npc, world_state)
                        logger.info(f"  ✅ Activated NPC at POI: {npc.get('name')} ({npc_id})")
    
    # If no NPCs found but we're in a known location, activate some default NPCs
    if not active_npc_ids and key_npcs:
        # Activate first 3 NPCs as fallback (likely important characters)
        for npc in key_npcs[:3]:
            npc_id = npc.get('id') or npc.get('name', '').lower().replace(' ', '_')
            if not npc.get('id'):
                npc['id'] = npc_id
            active_npc_ids.append(npc_id)
            logger.info(f"  ✅ Activated default NPC: {npc.get('name')} ({npc_id})")
    
    logger.info(f"🎭 Total NPCs activated: {len(active_npc_ids)}")
    return active_npc_ids


def ensure_npcs_have_ids(world_blueprint: Dict[str, Any]) -> None:
    """
    Ensure all NPCs in world_blueprint have IDs.
    Modifies blueprint in place.
    """
    key_npcs = world_blueprint.get('key_npcs', [])
    
    for npc in key_npcs:
        if not npc.get('id'):
            # Generate ID from name
            npc_id = npc.get('name', 'unknown').lower().replace(' ', '_')
            npc['id'] = npc_id
            logger.info(f"🆔 Assigned ID to NPC: {npc.get('name')} → {npc_id}")


def get_active_npcs_list(
    world_state: Dict[str, Any],
    world_blueprint: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Get the list of active NPC objects (not just IDs).
    
    Args:
        world_state: Current world state
        world_blueprint: Static world blueprint
    
    Returns:
        List of NPC dicts
    """
    active_npc_ids = world_state.get('active_npcs', [])
    key_npcs = world_blueprint.get('key_npcs', [])
    
    active_npcs = []
    for npc_id in active_npc_ids:
        for npc in key_npcs:
            if npc.get('id') == npc_id or npc.get('name', '').lower().replace(' ', '_') == npc_id:
                active_npcs.append(npc)
                break
    
    return active_npcs
