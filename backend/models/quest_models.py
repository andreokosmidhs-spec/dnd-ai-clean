"""
Quest System Data Models
Pydantic models for quest system with MongoDB compatibility
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid


# ═══════════════════════════════════════════════════════════════
# QUEST COMPONENT MODELS
# ═══════════════════════════════════════════════════════════════

class QuestObjective(BaseModel):
    """Individual quest objective with progress tracking"""
    objective_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # go_to, kill, interact, discover, deliver, escort, investigate
    description: str
    target: str
    target_type: str  # location, npc, enemy, item
    count: int = 1
    progress: int = 0
    completed: bool = False
    order: int = 1


class QuestGiver(BaseModel):
    """Quest giver information (NPC, faction, or environment)"""
    type: str  # npc, faction, environment
    npc_id: Optional[str] = None
    faction_id: Optional[str] = None
    location_id: Optional[str] = None


class QuestRewards(BaseModel):
    """Quest completion rewards"""
    xp: int = 0
    gold: int = 0
    items: List[str] = Field(default_factory=list)
    reputation: Dict[str, int] = Field(default_factory=dict)
    unlocks: List[str] = Field(default_factory=list)  # Unlocked locations, quests, etc.


class QuestLifecycleState(BaseModel):
    """Quest lifecycle timestamps"""
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None


class QuestRequirements(BaseModel):
    """Requirements to accept/complete quest"""
    min_level: int = 1
    required_items: List[str] = Field(default_factory=list)
    required_quests: List[str] = Field(default_factory=list)  # Quest IDs that must be completed first
    reputation_gates: Dict[str, int] = Field(default_factory=dict)  # faction_id: min_reputation


class QuestTimeLimit(BaseModel):
    """Quest time limit configuration"""
    type: str = "none"  # turns, days, none
    value: int = 0
    started_at: Optional[datetime] = None


class QuestGenerationContext(BaseModel):
    """Context about how quest was generated (for debugging/analytics)"""
    source_type: str  # world_blueprint, character_background, faction, threat
    source_poi_id: Optional[str] = None
    source_npc_id: Optional[str] = None
    source_faction: Optional[str] = None
    character_goal_alignment: Optional[str] = None
    character_background: Optional[str] = None
    threat_level: int = 1


# ═══════════════════════════════════════════════════════════════
# MAIN QUEST MODEL
# ═══════════════════════════════════════════════════════════════

class Quest(BaseModel):
    """Complete quest definition"""
    quest_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    campaign_id: str
    character_id: Optional[str] = None  # Null if not yet accepted
    
    name: str
    summary: str
    description: str
    
    status: str = "available"  # available, accepted, in_progress, completed, failed, abandoned
    lifecycle_state: QuestLifecycleState = Field(default_factory=QuestLifecycleState)
    
    giver: QuestGiver
    objectives: List[QuestObjective] = Field(default_factory=list)
    rewards: QuestRewards = Field(default_factory=QuestRewards)
    requirements: QuestRequirements = Field(default_factory=QuestRequirements)
    
    generation_context: QuestGenerationContext
    failure_conditions: List[str] = Field(default_factory=list)
    time_limit: QuestTimeLimit = Field(default_factory=QuestTimeLimit)
    
    tags: List[str] = Field(default_factory=list)
    difficulty: str = "medium"  # easy, medium, hard, deadly
    archetype: str = "fetch"  # fetch, kill, escort, investigation, social, exploration
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════

class QuestGenerateRequest(BaseModel):
    """Request to generate new quests"""
    campaign_id: str
    character_id: Optional[str] = None
    count: int = Field(default=3, ge=1, le=10)
    filters: Optional[Dict[str, Any]] = None


class QuestAcceptRequest(BaseModel):
    """Request to accept a quest"""
    quest_id: str
    character_id: str


class QuestAdvanceRequest(BaseModel):
    """Request to update quest progress"""
    quest_id: str
    event: Dict[str, Any]  # Event data: {type, target, context}


class QuestCompleteRequest(BaseModel):
    """Request to complete a quest"""
    quest_id: str
    character_id: str


class QuestFailRequest(BaseModel):
    """Request to fail a quest"""
    quest_id: str
    reason: str


class QuestAbandonRequest(BaseModel):
    """Request to abandon a quest"""
    quest_id: str
    character_id: str


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def quest_to_dict(quest: Quest) -> Dict[str, Any]:
    """Convert Quest model to MongoDB-ready dict"""
    quest_dict = quest.dict()
    
    # Convert datetime objects to ISO strings for MongoDB
    quest_dict["created_at"] = quest_dict["created_at"].isoformat() if isinstance(quest_dict["created_at"], datetime) else quest_dict["created_at"]
    quest_dict["updated_at"] = quest_dict["updated_at"].isoformat() if isinstance(quest_dict["updated_at"], datetime) else quest_dict["updated_at"]
    
    lifecycle = quest_dict["lifecycle_state"]
    for key in ["generated_at", "accepted_at", "started_at", "completed_at", "failed_at"]:
        if lifecycle.get(key) and isinstance(lifecycle[key], datetime):
            lifecycle[key] = lifecycle[key].isoformat()
    
    if quest_dict["time_limit"].get("started_at") and isinstance(quest_dict["time_limit"]["started_at"], datetime):
        quest_dict["time_limit"]["started_at"] = quest_dict["time_limit"]["started_at"].isoformat()
    
    return quest_dict


def dict_to_quest(quest_dict: Dict[str, Any]) -> Quest:
    """Convert MongoDB dict to Quest model"""
    # Convert ISO strings back to datetime objects if needed
    # Pydantic will handle this automatically in most cases
    return Quest(**quest_dict)
