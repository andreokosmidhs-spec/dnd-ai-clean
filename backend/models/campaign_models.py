from datetime import datetime
from typing import List, Literal, Optional
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
