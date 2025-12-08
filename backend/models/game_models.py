"""
Game state models for DUNGEON FORGE engine.
MongoDB-oriented schemas with Pydantic validation.
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
# CAMPAIGN MODELS
# ═══════════════════════════════════════════════════════════════

class Campaign(BaseModel):
    """Campaign document - stores persistent world blueprint"""
    campaign_id: str
    world_name: str
    world_blueprint: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════
# WORLD STATE MODELS
# ═══════════════════════════════════════════════════════════════

class WorldStateDoc(BaseModel):
    """World state document - tracks mutable NPC/faction/location states"""
    campaign_id: str
    world_state: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WorldState(BaseModel):
    """Mutable world state"""
    location: str
    current_location: str
    active_npcs: List[str] = Field(default_factory=list)
    active_conflicts: List[str] = Field(default_factory=list)
    discovered_locations: List[str] = Field(default_factory=list)
    time_of_day: str = "morning"
    
    # Phase 1: DMG Systems (p.24, p.26-27, p.32)
    tension_state: Optional[Dict[str, Any]] = None  # Pacing & Tension (DMG p.24)
    transgressions: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)  # Consequence tracking (DMG p.32)
    consequence_escalations: List[Dict[str, Any]] = Field(default_factory=list)  # Escalation history
    location_secrets: List[Dict[str, Any]] = Field(default_factory=list)  # For passive Perception (DMG p.26)
    guard_alert: bool = False
    guard_suspicion: bool = False
    guards_hostile: bool = False
    city_hostile: bool = False
    bounties: List[Dict[str, Any]] = Field(default_factory=list)
    permanent_enemies: List[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# QUEST MODELS (P3)
# ═══════════════════════════════════════════════════════════════

class QuestObjective(BaseModel):
    """Individual quest objective"""
    type: str  # "go_to", "kill", "interact", "discover"
    target: Optional[str] = None  # NPC id, location id, enemy archetype, etc.
    count: Optional[int] = 1
    progress: int = 0


class Quest(BaseModel):
    """Quest definition - must use existing world_blueprint entities"""
    quest_id: str
    name: str
    status: str = "active"  # "active", "completed", "failed"
    giver_npc_id: Optional[str] = None
    location_id: Optional[str] = None
    summary: str
    objectives: List[QuestObjective] = Field(default_factory=list)
    rewards_xp: int = 0
    rewards_items: List[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# CHARACTER MODELS
# ═══════════════════════════════════════════════════════════════

class CharacterState(BaseModel):
    """Character state - D&D 5e character sheet data"""
    model_config = {"populate_by_name": True}  # Allow population by alias
    
    name: str
    race: str
    subrace: Optional[str] = None  # Race variant (e.g., "High Elf", "Mountain Dwarf")
    class_: str = Field(alias="class")
    background: str
    goal: str
    level: int = 1
    hp: int = 10
    max_hp: int = 10
    ac: int = 10
    abilities: Dict[str, int] = Field(default_factory=dict)
    proficiencies: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    inventory: List[str] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)
    reputation: Dict[str, int] = Field(default_factory=dict)
    
    # Equipment & Resources
    gold: int = 0
    tool_proficiencies: List[str] = Field(default_factory=list)
    weapon_proficiencies: List[str] = Field(default_factory=list)
    armor_proficiencies: List[str] = Field(default_factory=list)
    racial_traits: List[Dict[str, str]] = Field(default_factory=list)
    speed: int = 30  # Movement speed in feet
    
    # P3: Progression system
    current_xp: int = 0
    xp_to_next: int = 100
    proficiency_bonus: int = 2
    attack_bonus: int = 0  # Generic attack bonus for scaling
    
    # P3: Defeat tracking
    injury_count: int = 0


class CharacterDoc(BaseModel):
    """Character document - character with metadata"""
    campaign_id: str
    character_id: str
    player_id: Optional[str] = None
    character_state: CharacterState
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════
# COMBAT MODELS
# ═══════════════════════════════════════════════════════════════

class CombatParticipant(BaseModel):
    """Unified model for any combat participant (player, enemy, or converted NPC)"""
    id: str
    name: str
    hp: int
    max_hp: int
    ac: int
    participant_type: str  # "player", "enemy", "npc"
    
    # Combat stats
    abilities: Dict[str, int] = Field(default_factory=dict)  # str, dex, con, int, wis, cha
    proficiency_bonus: int = 2
    attack_bonus: int = 0
    
    # Enemy/NPC specific
    damage_die: Optional[str] = "1d6"
    conditions: List[str] = Field(default_factory=list)
    faction_id: Optional[str] = None
    
    # NPC specific (for plot armor tracking)
    is_essential: bool = False
    plot_armor_attempts: int = 0  # Number of times attacked while having plot armor


class EnemyState(BaseModel):
    """Individual enemy in combat (legacy compatibility)"""
    id: str
    name: str
    hp: int
    max_hp: int
    ac: int
    conditions: List[str] = Field(default_factory=list)
    faction_id: Optional[str] = None
    
    # Combat stats for D&D 5e mechanics
    abilities: Dict[str, int] = Field(default_factory=lambda: {"str": 10, "dex": 10, "con": 10})
    proficiency_bonus: int = 2
    attack_bonus: int = 0
    damage_die: str = "1d6"


class CombatState(BaseModel):
    """Combat state - turn-by-turn combat tracking"""
    enemies: List[EnemyState] = Field(default_factory=list)
    participants: List[CombatParticipant] = Field(default_factory=list)  # Unified participant list
    turn_order: List[str] = Field(default_factory=list)
    active_turn: Optional[str] = None
    round: int = 1
    combat_over: bool = False
    outcome: Optional[str] = None  # None during combat, set to "victory"/"fled"/"player_defeated" when over
    
    # Track original NPC IDs that were converted to enemies
    converted_npcs: List[str] = Field(default_factory=list)


class CombatDoc(BaseModel):
    """Combat document - combat with metadata"""
    campaign_id: str
    character_id: str
    combat_state: CombatState
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════════

class WorldBlueprintGenerateRequest(BaseModel):
    """Request to generate world blueprint"""
    world_name: str
    tone: str
    starting_region_hint: str


class IntroGenerateRequest(BaseModel):
    """Request to generate cinematic intro"""
    campaign_id: str
    character_id: str


class ActionRequest(BaseModel):
    """Request for gameplay action"""
    campaign_id: str
    character_id: str
    player_action: str
    choice_source: Optional[str] = None
    check_result: Optional[int] = None
    client_target_id: Optional[str] = None  # Phase 1: Explicit target selection from frontend
