"""
Knowledge & Player Notes System
Tracks what players know about entities (NPCs, Locations, Factions, Items)
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class KnowledgeFact(BaseModel):
    """
    A single piece of information the player has learned about an entity.
    ONLY facts revealed through narration or explicit knowledge grants.
    """
    campaign_id: str
    character_id: Optional[str] = None
    entity_type: Literal["npc", "location", "faction", "item"]
    entity_id: str
    entity_name: str
    fact_type: Literal["introduction", "interaction", "description", "quest_related", "membership", "purpose", "threat", "rumor"]
    fact_text: str
    revealed_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    source: Literal["narration", "quest", "dialogue", "player_note"] = "narration"
    metadata: dict = Field(default_factory=dict)


class PlayerNote(BaseModel):
    """
    Player's personal notes about an entity.
    Fully editable by the player.
    """
    campaign_id: str
    character_id: Optional[str] = None
    entity_type: Literal["npc", "location", "faction", "item"]
    entity_id: str
    note_text: str
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())


class EntityMention(BaseModel):
    """
    Structure for entity mentions in narration responses.
    Tells frontend which entities to highlight.
    """
    type: Literal["npc", "location", "faction", "item"]
    id: str
    name: str
    first_mention: bool = False  # Is this the first time player sees this entity?


class EntityProfileResponse(BaseModel):
    """
    Player-facing profile built ONLY from KnowledgeFacts + PlayerNotes.
    NEVER includes GM-only world data.
    """
    entity_type: str
    entity_id: str
    name: str
    
    # Overview
    known_summary: str = ""  # Concatenated description facts
    first_seen: Optional[datetime] = None
    
    # Interactions & Events
    important_interactions: List[str] = Field(default_factory=list)
    
    # Affiliations (for NPCs and Factions)
    known_factions: List[dict] = Field(default_factory=list)  # [{name, role}]
    known_members: List[dict] = Field(default_factory=list)  # [{name, role}]
    
    # Quest & Item Related
    quest_items_given: List[str] = Field(default_factory=list)
    related_quests: List[str] = Field(default_factory=list)
    
    # Location Specific
    notable_npcs: List[dict] = Field(default_factory=list)  # NPCs seen at this location
    known_features: List[str] = Field(default_factory=list)  # Taverns, markets, landmarks
    
    # Faction Specific
    known_purpose: str = ""  # What the party believes the faction wants
    relationship_status: Optional[str] = None  # "ally", "neutral", "hostile"
    
    # Item Specific
    appearance: str = ""
    known_purpose: str = ""
    source_entity: Optional[dict] = None  # {"type": "npc", "id": "...", "name": "..."}
    
    # Threats & Rumors
    known_threats: List[str] = Field(default_factory=list)
    known_rumors: List[str] = Field(default_factory=list)
    
    # Player Notes (CRUD)
    player_notes: List[dict] = Field(default_factory=list)  # [{id, text, created_at, updated_at}]
    
    # Metadata
    total_facts: int = 0
    last_updated: Optional[datetime] = None


class CreateNoteRequest(BaseModel):
    """Request to create a new player note"""
    campaign_id: str
    character_id: Optional[str] = None
    entity_type: Literal["npc", "location", "faction", "item"]
    entity_id: str
    note_text: str


class UpdateNoteRequest(BaseModel):
    """Request to update an existing note"""
    note_text: str


class NoteResponse(BaseModel):
    """Response after note creation/update"""
    note_id: str
    entity_type: str
    entity_id: str
    note_text: str
    created_at: datetime
    updated_at: datetime

