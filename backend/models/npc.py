from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
import uuid

class NPCStatus(str, Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

class NPCNeed(BaseModel):
    name: str  # "hunger", "shelter", "belonging", "power", etc.
    current_level: float = Field(ge=0.0, le=1.0)  # 0 = desperate, 1 = satisfied
    importance: float = Field(ge=0.0, le=1.0)  # How important this need is to this NPC

class NPCValue(BaseModel):
    name: str  # "justice", "freedom", "wealth", "knowledge", etc.
    strength: float = Field(ge=0.0, le=1.0)  # How strongly they hold this value
    flexibility: float = Field(ge=0.0, le=1.0)  # How willing to compromise

class NPCTrait(BaseModel):
    name: str
    description: str
    stability: float = Field(ge=0.0, le=1.0)  # Likelihood of keeping this trait
    environmental_factor: float = Field(ge=0.0, le=1.0)  # How much environment affects this

class NPCMemory(BaseModel):
    character_id: str
    event_description: str
    emotional_impact: float = Field(ge=-1.0, le=1.0)
    location: str
    relationship_change: float = Field(ge=-0.5, le=0.5)  # How this affected relationship
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class NPCStats(BaseModel):
    strength: int = Field(ge=1, le=30)
    dexterity: int = Field(ge=1, le=30)
    constitution: int = Field(ge=1, le=30)
    intelligence: int = Field(ge=1, le=30)
    wisdom: int = Field(ge=1, le=30)
    charisma: int = Field(ge=1, le=30)

class NPC(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    
    # Classification
    status: NPCStatus = NPCStatus.COMMON
    occupation: str
    social_class: str  # "peasant", "merchant", "noble", "clergy", etc.
    
    # Location and mobility
    home_location: str
    current_location: str
    movement_pattern: str = "stationary"  # "stationary", "local", "traveling"
    
    # Psychology system
    needs: List[NPCNeed] = []
    values: List[NPCValue] = []
    traits: List[NPCTrait] = []
    ambitions: List[str] = []  # Number depends on status
    
    # Stats for ability checks and combat
    stats: NPCStats
    
    # Social relationships
    relationships: Dict[str, float] = {}  # character_id -> relationship (-1 to 1)
    known_characters: List[str] = []  # IDs of characters they've met
    
    # Memory and learning
    memories: List[NPCMemory] = []
    gossip: List[Dict] = []  # Information they've heard about others
    
    # Behavioral patterns
    dialogue_style: str = "neutral"  # "formal", "casual", "gruff", "eloquent", etc.
    cooperation_tendency: float = Field(ge=0.0, le=1.0)  # Likelihood to help strangers
    suspicion_level: float = Field(ge=0.0, le=1.0)  # How trusting they are
    
    # Dynamic state
    current_mood: str = "neutral"
    stress_level: float = Field(ge=0.0, le=1.0)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_interaction: Optional[datetime] = None

class NPCCreate(BaseModel):
    name: str
    description: str
    occupation: str
    home_location: str
    status: NPCStatus = NPCStatus.COMMON
    stats: NPCStats
    needs: List[NPCNeed] = []
    values: List[NPCValue] = []
    traits: List[NPCTrait] = []

class NPCInteraction(BaseModel):
    npc_id: str
    character_id: str
    interaction_type: str  # "conversation", "trade", "quest", "conflict", etc.
    player_action: str
    context: Dict = {}  # Additional context for AI processing
    location: str