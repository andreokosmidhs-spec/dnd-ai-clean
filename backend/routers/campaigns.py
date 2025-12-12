from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from bson import ObjectId
from fastapi import APIRouter, Body, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.campaign_models import (
    CampaignDraftRequest,
    CampaignDraftResponse,
    CampaignIntent,
    GenerateWorldResponse,
    KnowledgeCard,
)
from services.campaign_service import (
    build_starting_scene,
    build_world_blueprint,
    generate_initial_cards,
)

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

_db: Optional[AsyncIOMotorDatabase] = None
_in_memory_campaigns: Dict[str, Dict] = {}
_in_memory_cards: Dict[str, List[Dict]] = {}


def set_database(db: Optional[AsyncIOMotorDatabase]):
    global _db
    _db = db


def is_db_available() -> bool:
    return _db is not None


def get_campaign_collection():
    if _db is None:
        raise RuntimeError("Database not initialized. Call set_database() first.")
    return _db["campaigns"]


def get_cards_collection():
    if _db is None:
        raise RuntimeError("Database not initialized. Call set_database() first.")
    return _db["campaign_cards"]


async def _fetch_character(character_id: str) -> Optional[Dict]:
    if not is_db_available():
        return None

    try:
        object_id = ObjectId(character_id)
    except Exception:
        return None

    char = await _db["characters_v2"].find_one({"_id": object_id})
    if char:
        char["id"] = str(char.pop("_id"))
        return char

    legacy = await _db["characters"].find_one({"id": character_id})
    return legacy


async def _save_campaign_doc(doc: Dict):
    if is_db_available():
        collection = get_campaign_collection()
        existing = await collection.find_one({"campaign_id": doc["campaign_id"]})
        if existing:
            await collection.update_one({"campaign_id": doc["campaign_id"]}, {"$set": doc})
        else:
            await collection.insert_one(doc)
    else:
        _in_memory_campaigns[doc["campaign_id"]] = doc


async def _get_campaign(campaign_id: str) -> Optional[Dict]:
    if is_db_available():
        doc = await get_campaign_collection().find_one({"campaign_id": campaign_id}, {"_id": 0})
        return doc
    return _in_memory_campaigns.get(campaign_id)


async def _replace_cards(campaign_id: str, cards: List[KnowledgeCard]):
    card_dicts = [card.model_dump() for card in cards]
    if is_db_available():
        collection = get_cards_collection()
        await collection.delete_many({"campaign_id": campaign_id})
        if card_dicts:
            await collection.insert_many([{**card, "campaign_id": campaign_id} for card in card_dicts])
    else:
        _in_memory_cards[campaign_id] = [{**card, "campaign_id": campaign_id} for card in card_dicts]


async def _get_cards(campaign_id: str) -> List[Dict]:
    if is_db_available():
        cursor = get_cards_collection().find({"campaign_id": campaign_id}, {"_id": 0})
        return [card async for card in cursor]
    return _in_memory_cards.get(campaign_id, [])


async def _upsert_cards(campaign_id: str, new_cards: List[KnowledgeCard], updated_cards: List[KnowledgeCard]):
    collection_data = _in_memory_cards.setdefault(campaign_id, []) if not is_db_available() else None

    if is_db_available():
        collection = get_cards_collection()
        to_insert = [{**card.model_dump(), "campaign_id": campaign_id} for card in new_cards]
        if to_insert:
            await collection.insert_many(to_insert)
        for card in updated_cards:
            await collection.update_one(
                {"campaign_id": campaign_id, "id": card.id},
                {"$set": card.model_dump()},
            )
    else:
        if new_cards:
            collection_data.extend([{**card.model_dump(), "campaign_id": campaign_id} for card in new_cards])
        if updated_cards:
            updated_map = {card.id: card for card in updated_cards}
            for idx, stored in enumerate(collection_data):
                card_id = stored.get("id")
                if card_id in updated_map:
                    merged = {**stored, **updated_map[card_id].model_dump()}
                    collection_data[idx] = merged


@router.post("/draft", response_model=CampaignDraftResponse)
async def create_campaign_draft(request: CampaignDraftRequest):
    if not request.characterId:
        raise HTTPException(status_code=400, detail="characterId is required")

    campaign_id = str(uuid4())
    now = datetime.utcnow()
    campaign_doc = {
        "campaign_id": campaign_id,
        "character_id": request.characterId,
        "intent": request.intent.model_dump(),
        "status": "draft",
        "created_at": now,
        "updated_at": now,
    }

    if is_db_available():
        character = await _fetch_character(request.characterId)
        if character is None:
            raise HTTPException(status_code=404, detail="Character not found for campaign draft")

    await _save_campaign_doc(campaign_doc)
    return CampaignDraftResponse(campaignId=campaign_id, status="draft")


@router.post("/{campaignId}/generate-world", response_model=GenerateWorldResponse)
async def generate_world(campaignId: str):
    campaign = await _get_campaign(campaignId)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    intent = CampaignIntent(**campaign["intent"])
    character = await _fetch_character(campaign.get("character_id"))

    world = build_world_blueprint(intent, character)
    starting_scene = build_starting_scene(campaignId, world)

    campaign.update({
        "world": world,
        "status": "ready",
        "updated_at": datetime.utcnow(),
    })
    await _save_campaign_doc(campaign)

    initial_cards = generate_initial_cards(campaignId, intent, world, character)
    await _replace_cards(campaignId, initial_cards)

    return GenerateWorldResponse(
        campaignId=campaignId,
        status="ready",
        world=world,
        startingScene=starting_scene,
    )


@router.get("/{campaignId}/log/cards")
async def list_cards(campaignId: str):
    cards = await _get_cards(campaignId)
    return {"cards": cards}


@router.post("/{campaignId}/log/cards/upsert")
async def upsert_cards(
    campaignId: str,
    payload: Dict = Body(...),
):
    new_cards_payload = payload.get("newCards") or []
    updated_cards_payload = payload.get("updatedCards") or []

    now = datetime.utcnow()
    new_cards = [KnowledgeCard(updatedAt=now, **card) for card in new_cards_payload]
    updated_cards = [KnowledgeCard(updatedAt=now, **card) for card in updated_cards_payload]

    await _upsert_cards(campaignId, new_cards, updated_cards)
    return {"ok": True}
