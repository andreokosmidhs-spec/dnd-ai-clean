from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import uuid

class CharacterStats(BaseModel):
    strength: int = Field(ge=1, le=30)
    dexterity: int = Field(ge=1, le=30)
    constitution: int = Field(ge=1, le=30)
    intelligence: int = Field(ge=1, le=30)
    wisdom: int = Field(ge=1, le=30)
    charisma: int = Field(ge=1, le=30)

class SpellSlot(BaseModel):
    level: int
    total: int
    remaining: int

class CharacterTrait(BaseModel):
    name: str
    description: str
    stability: float = Field(ge=0.0, le=1.0)  # How likely trait is to change
    acquired_at: datetime = Field(default_factory=datetime.utcnow)

class CharacterMemory(BaseModel):
    event: str
    location: str
    npcs_involved: List[str] = []
    emotional_impact: float = Field(ge=-1.0, le=1.0)  # -1 negative, +1 positive
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Character(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    race: str
    character_class: str = Field(alias="class")
    background: str
    level: int = Field(default=1, ge=1)
    experience: int = Field(default=0, ge=0)
    
    # Core stats
    stats: CharacterStats
    hit_points: int
    max_hit_points: int
    
    # Magic system
    spell_slots: List[SpellSlot] = []
    known_spells: List[str] = []
    
    # Trait system for personality evolution
    traits: List[CharacterTrait] = []
    ambitions: List[str] = []  # Goals that drive behavior
    
    # Social systems
    reputation: Dict[str, float] = {}  # location_id -> reputation (-1 to 1)
    relationships: Dict[str, float] = {}  # npc_id -> relationship (-1 to 1)
    
    # Persistent memory
    memories: List[CharacterMemory] = []
    
    # Current state
    current_location: str
    inventory: List[Dict] = []
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)

class CharacterCreate(BaseModel):
    name: str
    race: str
    character_class: str = Field(alias="class")
    background: str
    stats: CharacterStats

class CharacterUpdate(BaseModel):
    hit_points: Optional[int] = None
    experience: Optional[int] = None
    current_location: Optional[str] = None
    inventory: Optional[List[Dict]] = None
    memories: Optional[List[CharacterMemory]] = None
    traits: Optional[List[CharacterTrait]] = None
    reputation: Optional[Dict[str, float]] = None
    relationships: Optional[Dict[str, float]] = None