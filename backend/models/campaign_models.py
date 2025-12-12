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


class WorldBlueprint(BaseModel):
    summary: str
    tags: List[str] = Field(default_factory=list)
    startingLocation: dict
    theme: Optional[str] = None
    tone: Optional[str] = None


class StartingScene(BaseModel):
    seed: str
    introText: Optional[str] = None


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
