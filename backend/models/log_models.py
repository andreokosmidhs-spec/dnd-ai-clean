"""
Campaign Log Models - Player-Known Information System
Tracks all player-discoverable knowledge across NPCs, Locations, Factions, Quests, etc.

This system replaces the simple player notes system with a structured, auto-updating log.
The log is the single source of truth for what the party knows.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════
# INDIVIDUAL KNOWLEDGE MODELS
# ═══════════════════════════════════════════════════════════════════════

class LocationKnowledge(BaseModel):
    """
    What the party knows about a location.
    Auto-populated from narration mentions + LLM extraction.
    """
    id: str  # location_tavern_name, location_region_name
    name: str  # "The Rusty Anchor", "Shadowfen"
    
    # Geographic & Environmental
    geography: str = ""  # "Coastal town", "Dark swamp", "Mountain pass"
    climate: str = ""  # "Temperate, rainy", "Hot and humid"
    
    # Political & Social
    controlling_faction: Optional[str] = None  # faction ID
    other_factions: List[str] = Field(default_factory=list)  # faction IDs present here
    
    # Points of Interest
    notable_places: List[str] = Field(default_factory=list)  # ["Town Square", "The Iron Forge"]
    npcs_met_here: List[str] = Field(default_factory=list)  # NPC IDs
    
    # Architecture & Culture
    architecture: str = ""  # "Stone buildings, thatched roofs"
    culture_notes: str = ""  # "Superstitious locals, fear of the woods"
    
    # History
    history_snippet: str = ""  # "Once a thriving trade hub"
    
    # Discovered info
    first_visited: datetime = Field(default_factory=lambda: datetime.utcnow())
    last_updated: datetime = Field(default_factory=lambda: datetime.utcnow())


class NpcKnowledge(BaseModel):
    """
    What the party knows about an NPC.
    """
    id: str  # npc_innkeeper_gregor
    name: str  # "Gregor the Innkeeper"
    
    # Identity
    role: str = ""  # "Innkeeper", "Guard Captain", "Merchant"
    location_id: Optional[str] = None  # Where they were first met
    
    # Personality & Traits
    personality: str = ""  # "Gruff but kind-hearted"
    appearance: str = ""  # "Bald dwarf with a thick beard"
    
    # Motivation & Goals
    wants: str = ""  # "Wants to find his missing daughter"
    offered: str = ""  # "Offered a place to stay for free"
    
    # Relationships
    faction_id: Optional[str] = None
    relationship_to_party: str = "neutral"  # "ally", "neutral", "hostile", "suspicious"
    
    # Quest & Story Ties
    related_quest_ids: List[str] = Field(default_factory=list)
    
    # Discovery
    first_met: datetime = Field(default_factory=lambda: datetime.utcnow())
    last_updated: datetime = Field(default_factory=lambda: datetime.utcnow())


class FactionKnowledge(BaseModel):
    """
    What the party knows about a faction/organization.
    """
    id: str  # faction_thieves_guild
    name: str  # "The Thieves' Guild"
    
    # Purpose & Goals
    stated_purpose: str = ""  # What they claim to do
    suspected_purpose: str = ""  # What the party suspects
    
    # Leadership & Members
    known_leader: Optional[str] = None  # NPC ID
    known_members: List[str] = Field(default_factory=list)  # NPC IDs
    
    # Territory
    base_location_id: Optional[str] = None
    controlled_locations: List[str] = Field(default_factory=list)  # location IDs
    
    # Relationships
    allies: List[str] = Field(default_factory=list)  # faction IDs
    enemies: List[str] = Field(default_factory=list)  # faction IDs
    relationship_to_party: str = "neutral"  # "ally", "neutral", "hostile"
    
    # Symbols & Culture
    symbols: str = ""  # "A red crow"
    culture_notes: str = ""  # "Honor among thieves"
    
    # Discovery
    first_heard: datetime = Field(default_factory=lambda: datetime.utcnow())
    last_updated: datetime = Field(default_factory=lambda: datetime.utcnow())


class QuestKnowledge(BaseModel):
    """
    What the party knows about a quest or objective.
    """
    id: str  # quest_find_missing_daughter
    title: str  # "Find Gregor's Daughter"
    
    # Quest Details
    quest_giver_npc_id: Optional[str] = None
    description: str = ""  # What they've been asked to do
    motivation: str = ""  # Why this matters
    
    # Origin / Source
    source_lead_id: Optional[str] = None  # Lead that was converted to this quest (if any)
    
    # Status
    status: str = "active"  # "rumored", "active", "completed", "failed"
    
    # Objectives
    objectives: List[str] = Field(default_factory=list)  # ["Search the eastern woods", "Talk to the ranger"]
    completed_objectives: List[str] = Field(default_factory=list)
    
    # Rewards
    promised_rewards: List[str] = Field(default_factory=list)  # ["50 gold", "Magic sword"]
    
    # Related Entities
    related_location_ids: List[str] = Field(default_factory=list)
    related_npc_ids: List[str] = Field(default_factory=list)
    related_faction_ids: List[str] = Field(default_factory=list)
    
    # Discovery
    discovered: datetime = Field(default_factory=lambda: datetime.utcnow())
    last_updated: datetime = Field(default_factory=lambda: datetime.utcnow())


class RumorKnowledge(BaseModel):
    """
    Rumors and unconfirmed information the party has heard.
    """
    id: str  # rumor_haunted_woods
    content: str  # "The eastern woods are haunted"
    
    # Source
    source_npc_id: Optional[str] = None  # Who told them
    source_location_id: Optional[str] = None  # Where they heard it
    
    # Verification
    confirmed: bool = False
    contradicted: bool = False
    
    # Related Entities
    related_entities: List[Dict[str, str]] = Field(default_factory=list)  # [{"type": "npc", "id": "..."}]
    
    # Discovery
    heard_when: datetime = Field(default_factory=lambda: datetime.utcnow())


class ItemKnowledge(BaseModel):
    """
    What the party knows about significant items.
    """
    id: str  # item_glowing_amulet
    name: str  # "Glowing Amulet"
    
    # Description
    appearance: str = ""  # "Silver amulet with a green gem"
    known_properties: str = ""  # "Glows near undead"
    suspected_properties: str = ""  # "Might protect against curses"
    
    # Origin
    found_where: Optional[str] = None  # location ID
    received_from: Optional[str] = None  # NPC ID
    
    # Status
    currently_held: bool = False  # Is it in party inventory?
    
    # Lore
    historical_info: str = ""  # "Said to belong to a long-dead paladin"
    
    # Discovery
    discovered: datetime = Field(default_factory=lambda: datetime.utcnow())
    last_updated: datetime = Field(default_factory=lambda: datetime.utcnow())


class DecisionKnowledge(BaseModel):
    """
    Major decisions the party has made (for consequence tracking).
    """
    id: str  # decision_spared_bandit_leader
    description: str  # "Spared the bandit leader instead of killing him"
    
    # Context
    location_id: Optional[str] = None
    involved_npcs: List[str] = Field(default_factory=list)  # NPC IDs
    involved_factions: List[str] = Field(default_factory=list)
    
    # Consequences
    immediate_outcome: str = ""  # "He fled into the woods"
    potential_consequences: List[str] = Field(default_factory=list)  # ["Might return for revenge", "Could become an ally"]
    
    # Timestamp
    decided_when: datetime = Field(default_factory=lambda: datetime.utcnow())


class LeadEntry(BaseModel):
    """
    Quest hooks/leads that the party has encountered but not yet pursued.
    These are narrative breadcrumbs for potential quests or investigations.
    
    Examples:
    - "Strange noises heard near the Old Barracks"
    - "Merchant mentioned missing shipments on the north road"
    - "Guard captain seeks help with bandit problem"
    """
    id: str  # lead_old_barracks_noises, lead_missing_shipments
    short_text: str  # The hook phrase as presented in narration
    
    # Source & Context
    location_id: Optional[str] = None  # Where this lead was discovered
    source_scene_id: Optional[str] = None  # Scene/narration that introduced this lead
    source_type: str = ""  # "observation", "rumor", "environmental", "conversation"
    
    # Quest Connection (for future integration)
    linked_quest_id: Optional[str] = None  # Quest this lead could trigger (if known)
    
    # Status Tracking
    status: str = "unexplored"  # "unexplored" | "active" | "resolved" | "abandoned"
    
    # Related Entities
    related_npc_ids: List[str] = Field(default_factory=list)  # NPCs mentioned in lead
    related_location_ids: List[str] = Field(default_factory=list)  # Locations mentioned
    related_faction_ids: List[str] = Field(default_factory=list)  # Factions involved
    
    # Player Notes
    player_notes: str = ""  # Optional player-added context
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())


# ═══════════════════════════════════════════════════════════════════════
# TOP-LEVEL CAMPAIGN LOG
# ═══════════════════════════════════════════════════════════════════════

class CampaignLog(BaseModel):
    """
    Master container for all player-known information in a campaign.
    This is the single source of truth for what the party knows.
    """
    campaign_id: str
    character_id: Optional[str] = None  # For character-specific logs
    
    # Knowledge Categories (keyed by entity ID)
    locations: Dict[str, LocationKnowledge] = Field(default_factory=dict)
    npcs: Dict[str, NpcKnowledge] = Field(default_factory=dict)
    factions: Dict[str, FactionKnowledge] = Field(default_factory=dict)
    quests: Dict[str, QuestKnowledge] = Field(default_factory=dict)
    rumors: Dict[str, RumorKnowledge] = Field(default_factory=dict)
    items: Dict[str, ItemKnowledge] = Field(default_factory=dict)
    decisions: Dict[str, DecisionKnowledge] = Field(default_factory=dict)
    leads: Dict[str, LeadEntry] = Field(default_factory=dict)  # Quest hooks/breadcrumbs
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    last_updated: datetime = Field(default_factory=lambda: datetime.utcnow())


# ═══════════════════════════════════════════════════════════════════════
# LLM EXTRACTION DELTA MODELS
# ═══════════════════════════════════════════════════════════════════════

class LocationDelta(BaseModel):
    """Delta update for a location from LLM extraction"""
    id: str
    name: Optional[str] = None
    geography: Optional[str] = None
    climate: Optional[str] = None
    controlling_faction: Optional[str] = None
    notable_places: List[str] = Field(default_factory=list)
    npcs_met_here: List[str] = Field(default_factory=list)
    architecture: Optional[str] = None
    culture_notes: Optional[str] = None
    history_snippet: Optional[str] = None


class NpcDelta(BaseModel):
    """Delta update for an NPC from LLM extraction"""
    id: str
    name: Optional[str] = None
    role: Optional[str] = None
    location_id: Optional[str] = None
    personality: Optional[str] = None
    appearance: Optional[str] = None
    wants: Optional[str] = None
    offered: Optional[str] = None
    faction_id: Optional[str] = None
    relationship_to_party: Optional[str] = None


class FactionDelta(BaseModel):
    """Delta update for a faction from LLM extraction"""
    id: str
    name: Optional[str] = None
    stated_purpose: Optional[str] = None
    suspected_purpose: Optional[str] = None
    known_leader: Optional[str] = None
    base_location_id: Optional[str] = None
    relationship_to_party: Optional[str] = None
    symbols: Optional[str] = None


class QuestDelta(BaseModel):
    """Delta update for a quest from LLM extraction"""
    id: str
    title: Optional[str] = None
    quest_giver_npc_id: Optional[str] = None
    description: Optional[str] = None
    source_lead_id: Optional[str] = None
    status: Optional[str] = None
    new_objectives: List[str] = Field(default_factory=list)
    completed_objectives: List[str] = Field(default_factory=list)


class RumorDelta(BaseModel):
    """New rumor from LLM extraction"""
    id: str
    content: str
    source_npc_id: Optional[str] = None
    source_location_id: Optional[str] = None
    confirmed: bool = False
    contradicted: bool = False


class ItemDelta(BaseModel):
    """Delta update for an item from LLM extraction"""
    id: str
    name: Optional[str] = None
    appearance: Optional[str] = None
    known_properties: Optional[str] = None
    suspected_properties: Optional[str] = None
    found_where: Optional[str] = None
    received_from: Optional[str] = None
    currently_held: Optional[bool] = None


class DecisionDelta(BaseModel):
    """New decision from LLM extraction"""
    id: str
    description: str
    location_id: Optional[str] = None
    involved_npcs: List[str] = Field(default_factory=list)
    immediate_outcome: Optional[str] = None
    potential_consequences: List[str] = Field(default_factory=list)


class LeadDelta(BaseModel):
    """
    New lead/quest hook from LLM extraction or scene generation.
    Represents a breadcrumb that could lead to a quest.
    """
    id: str
    short_text: str  # The hook phrase
    location_id: Optional[str] = None
    source_scene_id: Optional[str] = None
    source_type: Optional[str] = None  # "observation", "rumor", "environmental", "conversation"
    status: str = "unexplored"
    related_npc_ids: List[str] = Field(default_factory=list)
    related_location_ids: List[str] = Field(default_factory=list)
    related_faction_ids: List[str] = Field(default_factory=list)


class CampaignLogDelta(BaseModel):
    """
    Delta updates extracted by LLM from a single scene/narration.
    Only includes what changed or was newly discovered.
    """
    locations: List[LocationDelta] = Field(default_factory=list)
    npcs: List[NpcDelta] = Field(default_factory=list)
    factions: List[FactionDelta] = Field(default_factory=list)
    quests: List[QuestDelta] = Field(default_factory=list)
    rumors: List[RumorDelta] = Field(default_factory=list)
    items: List[ItemDelta] = Field(default_factory=list)
    decisions: List[DecisionDelta] = Field(default_factory=list)
    leads: List[LeadDelta] = Field(default_factory=list)  # Quest hooks discovered


# ═══════════════════════════════════════════════════════════════════════
# API REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════

class GetLogRequest(BaseModel):
    """Request to get the full campaign log"""
    campaign_id: str
    character_id: Optional[str] = None


class GetLogSummaryResponse(BaseModel):
    """Summary response with counts"""
    campaign_id: str
    counts: Dict[str, int]  # {"locations": 5, "npcs": 12, ...}
    last_updated: datetime


class GetEntityDetailRequest(BaseModel):
    """Request to get details for a specific entity"""
    campaign_id: str
    entity_type: str  # "location", "npc", "faction", etc.
    entity_id: str
    character_id: Optional[str] = None
