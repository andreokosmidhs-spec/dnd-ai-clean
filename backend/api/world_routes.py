from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import random

from models.world import Location, LocationCreate, WorldEvent, WorldEventCreate, Region, Resource
from models.character import Character
from models.npc import NPC
from services.game_engine import game_engine
from services.ai_service import ai_service

router = APIRouter(prefix="/world", tags=["world"])

# In-memory storage for demo
locations_db = {}
regions_db = {}
events_db = {}

@router.post("/locations", response_model=Location)
async def create_location(location_data: LocationCreate):
    """Create a new location with dynamic properties"""
    
    # Generate resources based on terrain and climate
    resources = _generate_location_resources(location_data.terrain, location_data.climate)
    
    # Determine building materials based on resources
    building_material = _determine_building_material(resources)
    
    # Generate features based on location type and population
    features = _generate_location_features(location_data.location_type, location_data.population_size)
    
    location = Location(
        name=location_data.name,
        description=location_data.description,
        location_type=location_data.location_type,
        region=location_data.region,
        climate=location_data.climate,
        terrain=location_data.terrain,
        rule_system=location_data.rule_system,
        population_size=location_data.population_size,
        resources=resources,
        primary_building_material=building_material,
        architectural_style=_determine_architectural_style(building_material, location_data.climate),
        features=features,
        wealth_level=_calculate_wealth_level(resources, location_data.population_size)
    )
    
    locations_db[location.id] = location
    return location

@router.get("/locations/{location_id}", response_model=Location)
async def get_location(location_id: str):
    """Get location by ID"""
    if location_id not in locations_db:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return locations_db[location_id]

@router.get("/locations")
async def get_all_locations() -> List[Location]:
    """Get all locations"""
    return list(locations_db.values())

@router.post("/locations/{location_id}/visit")
async def visit_location(location_id: str, character_id: str, action: str = "arrive"):
    """Record a character visiting a location"""
    if location_id not in locations_db:
        raise HTTPException(status_code=404, detail="Location not found")
    
    location = locations_db[location_id]
    
    # Update location memory (mock character for now)
    await game_engine.update_location_memory(
        location, 
        Character(
            id=character_id,
            name="Mock Character",
            race="Human",
            character_class="Fighter", 
            background="Soldier",
            stats={"strength": 15, "dexterity": 14, "constitution": 13, "intelligence": 12, "wisdom": 13, "charisma": 11},
            hit_points=20,
            max_hit_points=20,
            current_location=location_id
        ),
        f"Character {action} at {location.name}",
        0.0
    )
    
    # Generate arrival description
    description = await ai_service.get_ai_response(
        f"Character arrives at {location.name}",
        {'location': location.dict()},
        'world_description'
    )
    
    return {
        'location': location,
        'arrival_description': description,
        'current_time': datetime.utcnow()
    }

@router.post("/events", response_model=WorldEvent)
async def create_world_event(event_data: WorldEventCreate):
    """Create a new world event"""
    event = WorldEvent(
        title=event_data.title,
        description=event_data.description,
        event_type=event_data.event_type,
        affected_locations=event_data.affected_locations,
        severity=event_data.severity,
        duration_days=event_data.duration_days
    )
    
    events_db[event.id] = event
    return event

@router.get("/events/active")
async def get_active_events() -> List[WorldEvent]:
    """Get all currently active world events"""
    active_events = []
    current_time = datetime.utcnow()
    
    for event in events_db.values():
        if event.active:
            # Check if event should still be active
            if event.duration_days:
                end_time = event.start_time + timedelta(days=event.duration_days)
                if current_time > end_time:
                    event.active = False
                    continue
            
            active_events.append(event)
    
    return active_events

@router.get("/events/location/{location_id}")
async def get_location_events(location_id: str) -> List[WorldEvent]:
    """Get events affecting a specific location"""
    location_events = []
    
    for event in events_db.values():
        if event.active and location_id in event.affected_locations:
            location_events.append(event)
    
    return location_events

@router.post("/locations/{location_id}/generate-event")
async def generate_dynamic_event(location_id: str, context: Dict[str, Any] = None):
    """Generate a dynamic event for a location based on current conditions"""
    if location_id not in locations_db:
        raise HTTPException(status_code=404, detail="Location not found")
    
    location = locations_db[location_id]
    
    # Mock NPCs and characters for event generation
    mock_npcs = [
        NPC(
            name="Local Resident",
            description="A concerned citizen",
            occupation="merchant",
            home_location=location_id,
            current_location=location_id,
            stats={"strength": 10, "dexterity": 12, "constitution": 11, "intelligence": 13, "wisdom": 14, "charisma": 12}
        )
    ]
    
    # Generate event
    event = await game_engine.generate_dynamic_event(location, [], mock_npcs)
    
    if event:
        events_db[event.id] = event
        return {
            'event_generated': True,
            'event': event,
            'location': location.name
        }
    else:
        return {
            'event_generated': False,
            'message': 'No event triggered at this time',
            'location': location.name
        }

@router.get("/locations/{location_id}/description")
async def get_location_description(location_id: str, character_perspective: str = "neutral"):
    """Get an AI-generated description of a location"""
    if location_id not in locations_db:
        raise HTTPException(status_code=404, detail="Location not found")
    
    location = locations_db[location_id]
    
    # Generate rich description based on location properties
    context = {
        'location': location.dict(),
        'perspective': character_perspective
    }
    
    description = await ai_service.get_ai_response(
        f"Describe {location.name} in detail",
        context,
        'world_description'
    )
    
    return {
        'location_id': location_id,
        'name': location.name,
        'generated_description': description,
        'base_description': location.description,
        'features': location.features,
        'atmosphere': _get_location_atmosphere(location)
    }

@router.post("/regions", response_model=Region)
async def create_region(region_data: dict):
    """Create a new region"""
    region = Region(
        name=region_data['name'],
        description=region_data['description'],
        climate=region_data['climate'],
        dominant_terrain=region_data['dominant_terrain'],
        government_type=region_data.get('government_type', 'feudal'),
        dominant_culture=region_data.get('dominant_culture', 'mixed'),
        primary_language=region_data.get('primary_language', 'Common')
    )
    
    regions_db[region.id] = region
    return region

@router.get("/regions")
async def get_all_regions() -> List[Region]:
    """Get all regions"""
    return list(regions_db.values())

@router.get("/locations/{location_id}/trade-routes")
async def get_trade_routes(location_id: str):
    """Get trade routes connected to a location"""
    if location_id not in locations_db:
        raise HTTPException(status_code=404, detail="Location not found")
    
    location = locations_db[location_id]
    
    # Generate trade routes based on resources and connections
    trade_routes = []
    
    for connection in location.connected_locations:
        connected_location_id = connection.get('id')
        if connected_location_id in locations_db:
            connected_location = locations_db[connected_location_id]
            
            # Determine what goods are traded
            exported_goods = [resource.name for resource in location.resources if resource.abundance > 0.6]
            imported_goods = [resource.name for resource in connected_location.resources if resource.abundance > 0.6]
            
            trade_routes.append({
                'destination': connected_location.name,
                'destination_id': connected_location_id,
                'distance': connection.get('distance', 0),
                'difficulty': connection.get('difficulty', 0.5),
                'exported_goods': exported_goods,
                'imported_goods': imported_goods,
                'active': True
            })
    
    return {
        'location': location.name,
        'trade_routes': trade_routes,
        'economic_strength': location.wealth_level
    }

@router.post("/locations/{location_id}/reputation")
async def update_character_reputation(
    location_id: str, 
    character_id: str, 
    action: str, 
    reputation_change: float
):
    """Update character reputation at a location"""
    if location_id not in locations_db:
        raise HTTPException(status_code=404, detail="Location not found")
    
    location = locations_db[location_id]
    
    # Update reputation
    current_rep = location.character_reputations.get(character_id, 0)
    new_rep = max(-1, min(1, current_rep + reputation_change))
    location.character_reputations[character_id] = new_rep
    
    # Add to location memory
    from models.world import LocationMemory
    memory = LocationMemory(
        character_id=character_id,
        event=action,
        reputation_change=reputation_change
    )
    location.recent_memories.append(memory)
    
    # Get reputation description
    rep_description = _get_reputation_description(new_rep)
    
    return {
        'character_id': character_id,
        'location': location.name,
        'old_reputation': current_rep,
        'new_reputation': new_rep,
        'reputation_description': rep_description,
        'action': action
    }

def _generate_location_resources(terrain: str, climate: str) -> List[Resource]:
    """Generate resources based on terrain and climate"""
    resource_map = {
        'forest': [
            Resource(name="Timber", abundance=0.9, quality=0.7, trade_value=3.0),
            Resource(name="Game", abundance=0.6, quality=0.6, trade_value=2.0),
            Resource(name="Herbs", abundance=0.5, quality=0.5, trade_value=4.0)
        ],
        'mountains': [
            Resource(name="Iron", abundance=0.7, quality=0.8, trade_value=5.0),
            Resource(name="Stone", abundance=0.9, quality=0.7, trade_value=2.0),
            Resource(name="Precious Metals", abundance=0.3, quality=0.9, trade_value=8.0)
        ],
        'plains': [
            Resource(name="Grain", abundance=0.8, quality=0.6, trade_value=2.5),
            Resource(name="Livestock", abundance=0.7, quality=0.6, trade_value=3.0),
            Resource(name="Clay", abundance=0.4, quality=0.5, trade_value=1.5)
        ],
        'desert': [
            Resource(name="Gems", abundance=0.4, quality=0.8, trade_value=7.0),
            Resource(name="Salt", abundance=0.6, quality=0.7, trade_value=3.0),
            Resource(name="Rare Spices", abundance=0.3, quality=0.9, trade_value=6.0)
        ],
        'coast': [
            Resource(name="Fish", abundance=0.8, quality=0.6, trade_value=2.0),
            Resource(name="Salt", abundance=0.7, quality=0.7, trade_value=3.0),
            Resource(name="Pearls", abundance=0.2, quality=0.9, trade_value=9.0)
        ]
    }
    
    base_resources = resource_map.get(terrain, [
        Resource(name="Basic Materials", abundance=0.5, quality=0.5, trade_value=1.0)
    ])
    
    # Climate modifications
    if climate == 'arid':
        for resource in base_resources:
            if resource.name in ['Timber', 'Game', 'Grain']:
                resource.abundance *= 0.6  # Reduce abundance in arid climates
    elif climate == 'arctic':
        for resource in base_resources:
            if resource.name in ['Grain', 'Herbs']:
                resource.abundance *= 0.3  # Very low plant resources in arctic
    
    return base_resources

def _determine_building_material(resources: List[Resource]) -> str:
    """Determine primary building material based on available resources"""
    material_scores = {
        'stone': 0,
        'wood': 0,
        'clay': 0,
        'metal': 0
    }
    
    for resource in resources:
        if resource.name in ['Stone', 'Iron', 'Precious Metals']:
            material_scores['stone'] += resource.abundance * resource.quality
        elif resource.name in ['Timber']:
            material_scores['wood'] += resource.abundance * resource.quality
        elif resource.name in ['Clay']:
            material_scores['clay'] += resource.abundance * resource.quality
        elif resource.name in ['Iron', 'Precious Metals']:
            material_scores['metal'] += resource.abundance * resource.quality * 0.5  # Metal is expensive
    
    # Default to wood if no clear winner
    if not any(material_scores.values()):
        return 'wood'
    
    return max(material_scores, key=material_scores.get)

def _determine_architectural_style(material: str, climate: str) -> str:
    """Determine architectural style based on materials and climate"""
    style_map = {
        ('wood', 'temperate'): 'rustic timber',
        ('wood', 'arctic'): 'insulated log',
        ('wood', 'arid'): 'shade-focused timber',
        ('stone', 'temperate'): 'classic masonry',
        ('stone', 'arid'): 'thick-walled fortress',
        ('stone', 'arctic'): 'wind-resistant stone',
        ('clay', 'arid'): 'adobe',
        ('clay', 'temperate'): 'earthen brick',
        ('metal', 'temperate'): 'reinforced construction'
    }
    
    return style_map.get((material, climate), 'mixed construction')

def _generate_location_features(location_type, population_size: int) -> List[str]:
    """Generate location features based on type and size"""
    base_features = []
    
    if location_type == 'city':
        base_features = ['Market Square', 'Temple District', 'Noble Quarter', 'Merchant Guild', 'Guard Barracks']
        if population_size > 5000:
            base_features.extend(['University', 'Grand Cathedral', 'Palace', 'Multiple Markets'])
    elif location_type == 'town':
        base_features = ['Market', 'Inn', 'Temple', 'Blacksmith', 'Town Hall']
        if population_size > 1000:
            base_features.extend(['Guild Hall', 'Multiple Shops', 'Guard Post'])
    elif location_type == 'village':
        base_features = ['Inn', 'General Store', 'Shrine', 'Village Green']
        if population_size > 200:
            base_features.extend(['Blacksmith', 'Mill'])
    else:  # wilderness, dungeon, etc.
        base_features = ['Natural Landmark', 'Shelter', 'Water Source']
    
    return base_features

def _calculate_wealth_level(resources: List[Resource], population_size: int) -> float:
    """Calculate location wealth based on resources and population"""
    resource_value = sum(resource.trade_value * resource.abundance for resource in resources)
    population_factor = min(1.0, population_size / 10000)  # Normalize to city size
    
    wealth = (resource_value / 20.0) * (0.5 + 0.5 * population_factor)
    return min(1.0, wealth)

def _get_location_atmosphere(location: Location) -> str:
    """Generate atmospheric description based on location properties"""
    atmospheres = {
        'high_wealth': ['prosperous', 'bustling', 'vibrant'],
        'low_wealth': ['struggling', 'quiet', 'modest'],
        'severe_rules': ['orderly', 'tense', 'regulated'],
        'lawless': ['chaotic', 'dangerous', 'unpredictable'],
        'large_population': ['crowded', 'lively', 'diverse'],
        'small_population': ['intimate', 'close-knit', 'peaceful']
    }
    
    descriptors = []
    
    if location.wealth_level > 0.7:
        descriptors.extend(random.sample(atmospheres['high_wealth'], 1))
    elif location.wealth_level < 0.3:
        descriptors.extend(random.sample(atmospheres['low_wealth'], 1))
    
    if location.rule_system.value == 'severe':
        descriptors.extend(random.sample(atmospheres['severe_rules'], 1))
    elif location.rule_system.value == 'lawless':
        descriptors.extend(random.sample(atmospheres['lawless'], 1))
    
    if location.population_size > 2000:
        descriptors.extend(random.sample(atmospheres['large_population'], 1))
    else:
        descriptors.extend(random.sample(atmospheres['small_population'], 1))
    
    return ', '.join(descriptors) if descriptors else 'unremarkable'

def _get_reputation_description(reputation: float) -> str:
    """Convert reputation value to descriptive text"""
    if reputation > 0.8:
        return "Legendary hero"
    elif reputation > 0.5:
        return "Well respected"
    elif reputation > 0.2:
        return "Known positively"
    elif reputation > -0.2:
        return "Unknown"
    elif reputation > -0.5:
        return "Viewed with suspicion"
    elif reputation > -0.8:
        return "Actively disliked"
    else:
        return "Notorious villain"