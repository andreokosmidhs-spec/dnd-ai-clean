from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class CampaignIntent(BaseModel):
    tone: str
    focus: str
    scope: str
    danger: str


class CampaignDraftRequest(BaseModel):
    characterId: str
    intent: CampaignIntent
    # Optional mission-type blueprint chosen at setup (id or slug). Stored
    # on the campaign so all storyline drafts inherit it unless overridden.
    mission_type_id: Optional[str] = None
    mission_type_slug: Optional[str] = None


class CampaignDraftResponse(BaseModel):
    campaignId: str
    status: Literal["draft"]


class StartingScene(BaseModel):
    seed: str
    introText: Optional[str] = None
    # Macro chronicler preface displayed as a SEPARATE adventure-log entry
    # before the personal arrival scene.
    worldBrief: Optional[str] = None


class WorldBlueprint(BaseModel):
    summary: str
    tags: List[str] = Field(default_factory=list)
    startingLocation: dict
    theme: Optional[str] = None
    tone: Optional[str] = None
    # Legacy-compatible aliases consumed by the frontend WorldInfoPanel.
    world_core: Optional[dict] = None
    starting_town: Optional[dict] = None
    # Rich setting (era, factions, recent_events, current_tension) used by both
    # the intro and the Lean DM.
    setting: Optional[dict] = None
    # Macro chronicler preface persisted alongside setting so it loads on
    # campaign reopen.
    world_brief: Optional[str] = None


class GenerateWorldResponse(BaseModel):
    campaignId: str
    status: Literal["ready"]
    world: WorldBlueprint
    startingScene: StartingScene


class RevealCondition(BaseModel):
    """Condition that must be met before an info card's content is shown.

    type="check"  — player must pass a D&D skill check (roll_result >= dc).
    type="quest"  — a specific quest must be completed.
    type="free"   — no condition; card may be revealed at any time.
    """
    type: str = "free"                  # "check" | "quest" | "free"
    check_type: Optional[str] = None    # D&D skill name, e.g. "investigation"
    dc: Optional[int] = None
    quest_id: Optional[str] = None


class KnowledgeCard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    title: str
    description: str
    source: str = "generator"
    confidence: str = "high"
    tags: List[str] = Field(default_factory=list)
    # Optional status — primarily used by quest-type cards: 'active'|'completed'|'failed'
    status: Optional[str] = None
    # Interaction hint visible on entity/info cards before the full description
    # is revealed. E.g. "vendor", "questgiver", "enemy", "lore", "dungeon", "hub".
    interaction_hint: Optional[str] = None
    # Reveal mechanics (primarily for type="info" cards).
    revealed: bool = True               # entity cards are always visible; info cards start hidden
    reveal_condition: Optional[RevealCondition] = None
    hint_text: Optional[str] = None     # teaser shown to player before reveal
    # Backend-only retention metadata used by narrative tick/world progression.
    narrative_importance: Dict[str, Any] = Field(default_factory=dict)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)


class CampaignDocument(BaseModel):
    campaign_id: str
    character_id: str
    intent: CampaignIntent
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    world: Optional[dict] = None

    model_config = {
        "populate_by_name": True,
    }
