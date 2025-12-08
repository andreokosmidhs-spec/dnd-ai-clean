from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
import uuid

class LocationType(str, Enum):
    CITY = "city"
    TOWN = "town"
    VILLAGE = "village"
    WILDERNESS = "wilderness"
    DUNGEON = "dungeon"
    LANDMARK = "landmark"

class RuleSystem(str, Enum):
    SEVERE = "severe"  # Law strictly enforced by authorities
    MODERATE = "moderate"  # Some law enforcement
    TRIVIAL = "trivial"  # Rules enforced by guilds/gangs
    LAWLESS = "lawless"  # No organized law

class Resource(BaseModel):
    name: str
    abundance: float = Field(ge=0.0, le=1.0)  # How abundant this resource is
    quality: float = Field(ge=0.0, le=1.0)  # Quality of the resource
    trade_value: float = Field(ge=0.0, le=10.0)  # Economic importance

class LocationMemory(BaseModel):
    character_id: str
    event: str
    reputation_change: float = Field(ge=-0.5, le=0.5)
    witnesses: List[str] = []  # NPC IDs who witnessed the event
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Location(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    location_type: LocationType
    
    # Hierarchy
    region: str
    country: Optional[str] = None
    parent_location: Optional[str] = None  # For buildings within cities, etc.
    
    # Geography and resources
    climate: str  # "temperate", "arid", "arctic", "tropical", etc.
    terrain: str  # "forest", "plains", "mountains", "desert", etc.
    resources: List[Resource] = []
    
    # Architecture influenced by resources
    primary_building_material: str = "wood"  # Based on available resources
    architectural_style: str = "rustic"
    
    # Social and political
    rule_system: RuleSystem = RuleSystem.MODERATE
    ruling_faction: Optional[str] = None
    population_size: int = Field(ge=0)
    wealth_level: float = Field(ge=0.0, le=1.0)  # Overall prosperity
    
    # NPCs and dynamics
    resident_npcs: List[str] = []  # NPC IDs
    visiting_npcs: List[str] = []  # Temporary NPCs
    
    # Features and services
    features: List[str] = []  # "inn", "market", "temple", "blacksmith", etc.
    available_services: List[str] = []
    
    # Dynamic state
    current_events: List[str] = []  # Active events affecting this location
    recent_memories: List[LocationMemory] = []
    
    # Reputation system
    character_reputations: Dict[str, float] = {}  # character_id -> reputation
    
    # Connectivity
    connected_locations: List[Dict] = []  # {"id": "loc_id", "distance": 5, "difficulty": 0.3}
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class Region(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    climate: str
    dominant_terrain: str
    
    # Resources that influence the entire region
    natural_resources: List[Resource] = []
    trade_routes: List[str] = []  # Important trade connections
    
    # Political structure
    government_type: str = "feudal"  # "feudal", "republic", "theocracy", etc.
    dominant_culture: str
    primary_language: str
    
    # Locations within this region
    major_cities: List[str] = []  # Location IDs
    minor_settlements: List[str] = []
    points_of_interest: List[str] = []
    
    # Regional characteristics that affect NPCs and events
    cultural_values: List[str] = []  # Values commonly held in this region
    common_professions: List[str] = []
    typical_conflicts: List[str] = []  # Common sources of tension
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WorldEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    event_type: str  # "political", "natural", "economic", "social", "supernatural"
    
    # Scope and impact
    affected_locations: List[str] = []  # Location IDs
    affected_npcs: List[str] = []  # NPC IDs
    severity: float = Field(ge=0.0, le=1.0)  # How much this affects daily life
    
    # Timing
    start_time: datetime = Field(default_factory=datetime.utcnow)
    duration_days: Optional[int] = None  # None = ongoing
    
    # Narrative elements
    consequences: List[str] = []  # Potential outcomes
    character_involvement: Dict[str, str] = {}  # character_id -> involvement level
    
    # Status
    active: bool = True
    resolution: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LocationCreate(BaseModel):
    name: str
    description: str
    location_type: LocationType
    region: str
    climate: str = "temperate"
    terrain: str = "plains"
    rule_system: RuleSystem = RuleSystem.MODERATE
    population_size: int = 100
    features: List[str] = []

class WorldEventCreate(BaseModel):
    title: str
    description: str
    event_type: str
    affected_locations: List[str] = []
    severity: float = Field(ge=0.0, le=1.0)
    duration_days: Optional[int] = None