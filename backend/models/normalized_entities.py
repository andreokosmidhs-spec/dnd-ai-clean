"""
Normalized entity schemas with guaranteed shapes and safe defaults.
These models ensure data consistency throughout the application.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class HPStats(BaseModel):
    """HP is NEVER optional - always has current/max"""
    current: int = Field(ge=0, description="Current HP")
    max: int = Field(gt=0, description="Maximum HP")
    temp: int = Field(default=0, ge=0, description="Temporary HP")


class NormalizedCharacterState(BaseModel):
    """Canonical character shape - hp is ALWAYS present"""
    id: str
    name: str
    race: str
    class_name: str = Field(alias="class")
    level: int = Field(ge=1, le=20)
    hp: HPStats
    ac: int = Field(ge=1, le=30, default=10)
    proficiency_bonus: int = Field(ge=2, le=6, default=2)
    attack_bonus: int = Field(default=0, description="Weapon/feat bonuses")
    
    # Abilities - always present with defaults
    abilities: Dict[str, int] = Field(default_factory=lambda: {
        "str": 10, "dex": 10, "con": 10,
        "int": 10, "wis": 10, "cha": 10
    })
    
    # Optional fields
    current_xp: int = Field(default=0, ge=0)
    xp_to_next: int = Field(default=300, ge=1)
    proficiencies: List[str] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True


class NormalizedEnemy(BaseModel):
    """Canonical enemy shape - combat stats ALWAYS present"""
    id: str
    name: str
    hp: int = Field(ge=0)
    max_hp: int = Field(gt=0)
    ac: int = Field(ge=1, le=30, default=10)
    attack_bonus: int = Field(default=2, description="To-hit bonus")
    damage_die: str = Field(default="1d6", description="Damage roll (e.g., 1d6, 2d8)")
    
    # Optional fields
    type: Optional[str] = None
    abilities: Optional[Dict[str, int]] = None
    special_abilities: List[str] = Field(default_factory=list)


class NormalizedMessage(BaseModel):
    """Canonical message shape for adventure log"""
    id: str
    type: str = Field(description="dm, player, roll_result, error")
    text: str
    timestamp: int
    
    # Optional fields based on type
    options: List[str] = Field(default_factory=list)
    checkRequest: Optional[Dict[str, Any]] = None
    npcMentions: List[Dict[str, str]] = Field(default_factory=list)
    isCinematic: bool = False
    audioUrl: Optional[str] = None
    isGeneratingAudio: bool = False
    messageType: Optional[str] = None  # For player messages: action, say, dm-question
    rollData: Optional[Dict[str, Any]] = None  # For roll_result messages
    retry: bool = False  # For error messages


def normalize_character(raw_data: Dict[str, Any]) -> NormalizedCharacterState:
    """
    Normalize character data from any source (DB, API, frontend).
    Ensures HP is always present with safe defaults.
    """
    # Handle HP normalization
    hp_data = raw_data.get("hp", {})
    if isinstance(hp_data, dict):
        normalized_hp = HPStats(
            current=hp_data.get("current", 10),
            max=hp_data.get("max", 10),
            temp=hp_data.get("temp", 0)
        )
    else:
        # Legacy: hp might be a single number (max_hp)
        max_hp = raw_data.get("max_hp", 10)
        normalized_hp = HPStats(current=max_hp, max=max_hp, temp=0)
    
    return NormalizedCharacterState(
        id=raw_data.get("id", "unknown"),
        name=raw_data.get("name", "Unknown"),
        race=raw_data.get("race", "Human"),
        class_name=raw_data.get("class", "Fighter"),
        level=raw_data.get("level", 1),
        hp=normalized_hp,
        ac=raw_data.get("ac", 10),
        proficiency_bonus=raw_data.get("proficiency_bonus", 2),
        attack_bonus=raw_data.get("attack_bonus", 0),
        abilities=raw_data.get("abilities", {}),
        current_xp=raw_data.get("current_xp", 0),
        xp_to_next=raw_data.get("xp_to_next", 300),
        proficiencies=raw_data.get("proficiencies", [])
    )


def normalize_enemy(raw_data: Dict[str, Any]) -> NormalizedEnemy:
    """
    Normalize enemy data to ensure combat stats are always present.
    Prevents KeyErrors in combat engine.
    """
    return NormalizedEnemy(
        id=raw_data.get("id", f"enemy-{raw_data.get('name', 'unknown')}"),
        name=raw_data.get("name", "Unknown Enemy"),
        hp=raw_data.get("hp", 10),
        max_hp=raw_data.get("max_hp", 10),
        ac=raw_data.get("ac", 10),
        attack_bonus=raw_data.get("attack_bonus", 2),
        damage_die=raw_data.get("damage_die", "1d6"),
        type=raw_data.get("type"),
        abilities=raw_data.get("abilities"),
        special_abilities=raw_data.get("special_abilities", [])
    )


def normalize_enemy_list(enemies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize a list of enemies for combat.
    Returns list of dicts (not Pydantic models) for compatibility.
    """
    normalized = []
    for enemy_data in enemies:
        enemy_model = normalize_enemy(enemy_data)
        normalized.append(enemy_model.model_dump(by_alias=True))
    return normalized
