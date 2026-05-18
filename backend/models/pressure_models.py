"""
LIVING CAMPAIGN PRESSURE ENGINE — Data Models

World wound → pressure → hook → lead → quest → consequence → world mutation.
Everything cycles. Nothing important disappears without meaning.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════
# WORLD WOUND — the seed of all pressure
# ═══════════════════════════════════════════════════════════════════

class WorldWound(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    origin: str                          # "ancient war", "failed harvest", "betrayed pact"
    affected_regions: List[str] = Field(default_factory=list)
    affected_factions: List[str] = Field(default_factory=list)
    severity: float = Field(ge=0.0, le=1.0, default=0.5)  # 0=dormant, 1=critical
    is_resolved: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════════════════════
# REGIONAL PRESSURE — what a wound produces
# ═══════════════════════════════════════════════════════════════════

class RegionalPressure(BaseModel):
    region_id: str
    region_name: str

    # Pressure axes (0.0–1.0)
    crime: float = 0.1
    war: float = 0.0
    scarcity: float = 0.1
    corruption: float = 0.1
    cult_activity: float = 0.0
    magical_instability: float = 0.0
    social_unrest: float = 0.1

    # Derived state (updated by narrative tick)
    guard_presence: float = 0.2
    fear: float = 0.1
    rumor_density: float = 0.2
    faction_activity: float = 0.2
    price_pressure: float = 0.1

    source_wound_ids: List[str] = Field(default_factory=list)
    last_ticked: Optional[datetime] = None

    @property
    def total_pressure(self) -> float:
        axes = [self.crime, self.war, self.scarcity, self.corruption,
                self.cult_activity, self.magical_instability, self.social_unrest]
        return round(sum(axes) / len(axes), 3)

    @property
    def pressure_label(self) -> str:
        t = self.total_pressure
        if t >= 0.8: return "CRITICAL"
        if t >= 0.6: return "HIGH"
        if t >= 0.4: return "MODERATE"
        if t >= 0.2: return "LOW"
        return "CALM"


# ═══════════════════════════════════════════════════════════════════
# HOOK — visible pressure made tangible
# ═══════════════════════════════════════════════════════════════════

HookType = Literal[
    "visible_clue", "strange_behavior", "rumor", "environmental_sign",
    "missing_person", "faction_movement", "npc_warning", "item_found"
]

class Hook(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    campaign_id: str
    region_id: str

    hook_type: HookType = "rumor"
    title: str
    description: str                     # What the player perceives
    hidden_truth: str                    # What's really happening (DM only)

    source_pressure_axes: List[str] = Field(default_factory=list)
    source_wound_id: Optional[str] = None
    source_antagonist_operation_id: Optional[str] = None

    status: Literal["visible", "noticed", "lead_created", "expired"] = "visible"
    importance_score: float = 0.3

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════════════
# LEAD — hook the player has engaged with
# ═══════════════════════════════════════════════════════════════════

LeadStatus = Literal["active", "ignored", "resolved", "abandoned", "sealed", "transformed"]

class Lead(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    campaign_id: str
    character_id: Optional[str] = None

    title: str
    summary: str
    player_notes: str = ""

    status: LeadStatus = "active"
    source_hook_id: Optional[str] = None
    linked_quest_id: Optional[str] = None

    related_npc_ids: List[str] = Field(default_factory=list)
    related_faction_ids: List[str] = Field(default_factory=list)
    known_by_npc_ids: List[str] = Field(default_factory=list)  # NPCs who know this lead

    importance_score: float = 0.4
    narrative_importance: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════════════════════
# ANTAGONIST — living pressure source
# ═══════════════════════════════════════════════════════════════════

AntagonistMO = Literal[
    "secretive", "spectacle", "manipulative", "chaotic", "brute_force", "dramatic"
]

NetworkType = Literal["solo", "gang", "faction", "systemic"]

ActPhase = Literal["act1_shadow", "act2_pressure", "act3_confrontation", "act4_resolution"]

class AntagonistOperation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    antagonist_id: str
    operation_type: str     # "murder", "theft", "purge", "recruitment", "propaganda", etc.
    target_region_id: str
    description: str

    visible_effects: List[str] = Field(default_factory=list)
    hidden_effects: List[str] = Field(default_factory=list)
    involved_npc_ids: List[str] = Field(default_factory=list)

    generated_hook_seeds: List[str] = Field(default_factory=list)
    escalation_value: float = Field(ge=0.0, le=1.0, default=0.1)

    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    player_interfered: bool = False


class Antagonist(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    campaign_id: str

    name: str
    origin_wound: str               # Which world wound created them
    world_history_connection: str
    ideology: str
    flavor: str                     # Narrative texture / voice

    mo: AntagonistMO = "secretive"
    network_type: NetworkType = "faction"
    pressure_style: str             # "economic strangulation", "terror campaigns", etc.

    connected_npc_ids: List[str] = Field(default_factory=list)
    related_faction_ids: List[str] = Field(default_factory=list)
    known_lead_ids: List[str] = Field(default_factory=list)
    hidden_lead_ids: List[str] = Field(default_factory=list)

    escalation_level: float = Field(ge=0.0, le=1.0, default=0.1)
    act_phase: ActPhase = "act1_shadow"
    regional_influence: Dict[str, float] = Field(default_factory=dict)  # region_id → 0-1
    public_presence: float = Field(ge=0.0, le=1.0, default=0.05)
    operational_style: str = ""

    operations: List[AntagonistOperation] = Field(default_factory=list)

    revealed_signature: bool = False   # Has the player seen "something serious entered the world"
    revealed_motive: bool = False
    revealed_full_network: bool = False

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════════════════════
# CLEANSING EVENT — narrative garbage collection
# ═══════════════════════════════════════════════════════════════════

CleansingType = Literal[
    "passive_memory_cleanup",
    "plague", "earthquake", "purge", "magical_storm",
    "gang_war", "fire", "famine", "political_crackdown", "monster_outbreak"
]

class CleansingEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    campaign_id: str
    region_id: str

    cleansing_type: CleansingType
    title: str
    description: str
    warning_signs: List[str] = Field(default_factory=list)

    # What it affects
    archived_lead_ids: List[str] = Field(default_factory=list)
    transformed_lead_ids: List[str] = Field(default_factory=list)
    new_hook_seeds: List[str] = Field(default_factory=list)    # Hooks born from the cleansing
    affected_npc_ids: List[str] = Field(default_factory=list)

    # Player opportunity
    player_intervention_possible: bool = True
    intervention_window_turns: int = 3
    rescue_quest_generated: bool = False

    triggered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False


# ═══════════════════════════════════════════════════════════════════
# CAMPAIGN PRESSURE STATE — top-level document stored per campaign
# ═══════════════════════════════════════════════════════════════════

class CampaignPressureState(BaseModel):
    campaign_id: str

    wounds: List[WorldWound] = Field(default_factory=list)
    regional_pressures: Dict[str, RegionalPressure] = Field(default_factory=dict)
    hooks: List[Hook] = Field(default_factory=list)
    leads: List[Lead] = Field(default_factory=list)
    antagonists: List[Antagonist] = Field(default_factory=list)
    cleansing_events: List[CleansingEvent] = Field(default_factory=list)

    # Campaign memory — compressed history of what mattered
    campaign_memory: List[Dict[str, Any]] = Field(default_factory=list)

    act_phase: ActPhase = "act1_shadow"
    player_level: int = 1

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════

class PressureTickRequest(BaseModel):
    campaign_id: str
    trigger: Literal["long_rest", "travel", "next_day", "major_quest_completion"]
    region_id: Optional[str] = None

class HookNoticeRequest(BaseModel):
    campaign_id: str
    hook_id: str
    character_id: str

class LeadCreateRequest(BaseModel):
    campaign_id: str
    hook_id: str
    character_id: str
    player_notes: str = ""

class AntagonistOperationRequest(BaseModel):
    campaign_id: str
    antagonist_id: str
    operation_type: str
    target_region_id: str

class CleansingCheckRequest(BaseModel):
    campaign_id: str
    region_id: str
