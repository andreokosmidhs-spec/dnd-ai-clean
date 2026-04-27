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
    build_starting_scene_with_ai,
    build_world_blueprint,
    generate_initial_cards,
    generate_opening_quest_card_with_ai,
    generate_world_setting_with_ai,
    setting_knowledge_cards,
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


@router.get("/v2/latest")
async def get_latest_v2_campaign():
    """V2-aware "load last campaign" endpoint.

    Returns the most-recently-updated V2 campaign whose character still exists.
    Frontend uses this to drop the player straight back into the adventure
    screen with session state pre-populated.
    """
    if not is_db_available():
        if not _in_memory_campaigns:
            raise HTTPException(status_code=404, detail="No V2 campaigns found")
        # Latest by updated_at in memory
        latest = max(
            _in_memory_campaigns.values(),
            key=lambda c: c.get("updated_at") or c.get("created_at") or datetime.min,
        )
        return {
            "campaign_id": latest.get("campaign_id"),
            "character_id": latest.get("character_id"),
            "status": latest.get("status"),
            "updated_at": (latest.get("updated_at") or latest.get("created_at") or datetime.utcnow()).isoformat()
            if not isinstance(latest.get("updated_at"), str)
            else latest.get("updated_at"),
        }

    collection = get_campaign_collection()
    cursor = (
        collection.find({"character_id": {"$exists": True, "$ne": None}}, {"_id": 0})
        .sort("updated_at", -1)
        .limit(20)
    )
    candidates = await cursor.to_list(length=20)
    for camp in candidates:
        char = await _fetch_character(camp.get("character_id"))
        if char:
            updated = camp.get("updated_at")
            return {
                "campaign_id": camp.get("campaign_id"),
                "character_id": camp.get("character_id"),
                "status": camp.get("status"),
                "updated_at": updated.isoformat() if isinstance(updated, datetime) else updated,
                "character_name": (char.get("identity") or {}).get("name") or char.get("name"),
            }
    raise HTTPException(status_code=404, detail="No V2 campaigns with characters found")


@router.post("/{campaignId}/generate-world", response_model=GenerateWorldResponse)
async def generate_world(campaignId: str):
    campaign = await _get_campaign(campaignId)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    intent = CampaignIntent(**campaign["intent"])
    character = await _fetch_character(campaign.get("character_id"))

    world = build_world_blueprint(intent, character)

    # Generate the world's SETTING (era, factions, recent events, current
    # tension) so the intro can ground the player in a real place with real
    # history, and the DM can reference factions/events on every turn.
    setting = await generate_world_setting_with_ai(intent, world, character)
    world["setting"] = setting

    # Generate the AI opening-quest card FIRST so it can be planted in the intro.
    opening_quest = await generate_opening_quest_card_with_ai(intent, world, character)

    starting_scene = await build_starting_scene_with_ai(
        campaignId,
        world,
        intent,
        character,
        active_quest=opening_quest.model_dump(),
        setting=setting,
    )

    campaign.update({
        "world": world,
        "starting_scene": starting_scene,
        "status": "ready",
        "updated_at": datetime.utcnow(),
    })
    await _save_campaign_doc(campaign)

    # Seed cards: location/contact/cultural + faction/event/tension + opening lead.
    initial_cards = generate_initial_cards(campaignId, intent, world, character)
    initial_cards.extend(setting_knowledge_cards(setting))
    initial_cards.append(opening_quest)
    await _replace_cards(campaignId, initial_cards)

    return GenerateWorldResponse(
        campaignId=campaignId,
        status="ready",
        world=world,
        startingScene=starting_scene,
    )


@router.get("/{campaignId}")
async def get_campaign(campaignId: str):
    campaign = await _get_campaign(campaignId)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.pop("_id", None)
    return campaign


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


def _derive_card_title(text: str, fallback: str = "Remembered Beat") -> str:
    text = (text or "").strip()
    if not text:
        return fallback
    # Prefer the first sentence; cap at 60 chars
    for delim in (". ", "! ", "? ", "\n"):
        idx = text.find(delim)
        if 10 <= idx <= 70:
            return text[:idx].strip()
    return text[:60].rstrip() + ("…" if len(text) > 60 else "")


@router.post("/{campaignId}/log/cards/remember")
async def remember_beat(
    campaignId: str,
    payload: Dict = Body(...),
):
    """Promote a DM narration beat into a pinned knowledge card so the DM will
    keep it in context on future turns.
    """
    campaign = await _get_campaign(campaignId)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    text = (payload.get("text") or payload.get("content") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    title = (payload.get("title") or "").strip() or _derive_card_title(text)
    card_type = (payload.get("type") or "event").strip() or "event"
    tags = payload.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    # Always include 'remembered' tag so the UI can distinguish user-pinned beats
    if "remembered" not in tags:
        tags = [*tags, "remembered"]

    # Truncate overly long descriptions — the DM prompt already trims to 140 chars
    description = text if len(text) <= 600 else text[:600].rstrip() + "…"

    now = datetime.utcnow()
    card = KnowledgeCard(
        type=card_type,
        title=title,
        description=description,
        source="player-remember",
        confidence="high",
        tags=tags,
        updatedAt=now,
    )
    await _upsert_cards(campaignId, [card], [])
    return {"ok": True, "card": card.model_dump()}


def _quest_card_to_ui(card: Dict) -> Dict:
    """Adapt a quest-type KnowledgeCard to the shape QuestLogPanel expects."""
    tags = [str(t).lower() for t in (card.get("tags") or [])]
    status = card.get("status")
    if not status:
        # Back-compat: derive from tags, default 'active'
        if "completed" in tags:
            status = "completed"
        elif "failed" in tags:
            status = "failed"
        else:
            status = "active"
    return {
        "quest_id": card.get("id"),
        "name": card.get("title") or "Untitled quest",
        "summary": card.get("description") or "",
        "status": status,
        "tags": tags,
        "source": card.get("source") or "generator",
        # Minimal synthetic objective so the UI renders a progress line without
        # requiring the legacy dungeon_forge schema.
        "objectives": [
            {
                "type": "discover",
                "target": "Advance this thread",
                "progress": 1 if status == "completed" else 0,
                "count": 1,
            }
        ],
        "rewards_xp": 0,
        "giver_npc_id": None,
        "location_id": None,
        "updated_at": card.get("updatedAt"),
    }


@router.get("/{campaignId}/quests")
async def list_quests(campaignId: str):
    """Return all quest-type knowledge cards shaped for the Quest Log UI.
    Opening leads come first, then other active, then completed/failed.
    """
    cards = await _get_cards(campaignId)
    quest_cards = [c for c in (cards or []) if (c.get("type") or "").lower() == "quest"]

    def sort_key(c):
        tags = [str(t).lower() for t in (c.get("tags") or [])]
        status = (c.get("status") or "").lower()
        if not status:
            status = "completed" if "completed" in tags else ("failed" if "failed" in tags else "active")
        priority = 0 if "opening" in tags else 1
        status_rank = {"active": 0, "completed": 1, "failed": 2}.get(status, 3)
        return (priority, status_rank, c.get("updatedAt") or "")

    quest_cards.sort(key=sort_key)
    return {"quests": [_quest_card_to_ui(c) for c in quest_cards]}


@router.post("/{campaignId}/quests/{questId}/status")
async def update_quest_status(
    campaignId: str,
    questId: str,
    payload: Dict = Body(...),
):
    """Update the status of a quest card: 'active' | 'completed' | 'failed'."""
    status = (payload.get("status") or "").strip().lower()
    if status not in {"active", "completed", "failed"}:
        raise HTTPException(
            status_code=400, detail="status must be one of 'active', 'completed', 'failed'"
        )
    # Find the card
    cards = await _get_cards(campaignId)
    target = next((c for c in cards if c.get("id") == questId and (c.get("type") or "").lower() == "quest"), None)
    if not target:
        raise HTTPException(status_code=404, detail="Quest not found")

    updated = KnowledgeCard(**{k: v for k, v in target.items() if k != "campaign_id"})
    updated.status = status
    updated.updatedAt = datetime.utcnow()
    await _upsert_cards(campaignId, [], [updated])
    return {"ok": True, "quest": _quest_card_to_ui(updated.model_dump())}


@router.post("/{campaignId}/log/cards/remember-as-quest")
async def remember_as_quest(
    campaignId: str,
    payload: Dict = Body(...),
):
    """Promote a DM narration beat into an ACTIVE quest card so it appears in
    the Quest Log AND gets prioritized by the DM's next turns.
    """
    campaign = await _get_campaign(campaignId)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    text = (payload.get("text") or payload.get("content") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    title = (payload.get("title") or "").strip() or _derive_card_title(text)
    tags = payload.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    tags = [str(t).lower() for t in tags]
    for required in ("quest", "remembered", "active"):
        if required not in tags:
            tags.append(required)

    description = text if len(text) <= 600 else text[:600].rstrip() + "…"

    now = datetime.utcnow()
    card = KnowledgeCard(
        type="quest",
        title=title,
        description=description,
        source="player-remember",
        confidence="high",
        tags=tags,
        status="active",
        updatedAt=now,
    )
    await _upsert_cards(campaignId, [card], [])
    return {"ok": True, "quest": _quest_card_to_ui(card.model_dump())}



# ==================== Scene Reports ============================================
# "Report this scene" — a one-click dev snapshot a player can submit when a
# DM turn feels off. Captures the rendered text + player action + full context
# (character, campaign intent, active/closed quests, knowledge cards, world).


def _scene_reports_collection():
    if _db is None:
        raise RuntimeError("Database not initialized. Call set_database() first.")
    return _db["scene_reports"]


@router.post("/{campaignId}/scene-reports")
async def create_scene_report(
    campaignId: str,
    payload: Dict = Body(...),
):
    """Store a rich snapshot of the moment a player flagged.

    Client payload (all fields optional except messageText or message_text):
      - messageText / message_text: the DM narration the player is reporting
      - playerActionText / player_action_text: what the player wrote (previous turn)
      - userNote / user_note: free-text from the "What went wrong?" field
      - tags: list[str] of quick reason flags (e.g. ["pov-leak", "cliche"])
    """
    campaign = await _get_campaign(campaignId)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    message_text = (
        (payload.get("messageText") or payload.get("message_text") or "").strip()
    )
    if not message_text:
        raise HTTPException(status_code=400, detail="messageText is required")

    player_action_text = (
        (payload.get("playerActionText") or payload.get("player_action_text") or "").strip()
    )
    user_note = (payload.get("userNote") or payload.get("user_note") or "").strip()
    raw_tags = payload.get("tags") or []
    tags = [str(t).strip().lower() for t in raw_tags if t]

    # Fetch rich snapshot context
    character = None
    try:
        character = await _fetch_character(campaign.get("character_id"))
    except Exception:  # noqa: BLE001
        character = None

    cards = await _get_cards(campaignId)
    quest_cards = [c for c in cards if (c.get("type") or "").lower() == "quest"]
    non_quest_cards = [c for c in cards if (c.get("type") or "").lower() != "quest"]
    active_quests = [_quest_card_to_ui(c) for c in quest_cards if (c.get("status") or "active") == "active"]
    closed_quests = [_quest_card_to_ui(c) for c in quest_cards if (c.get("status") or "") in {"completed", "failed"}]

    # Pull the character's personality + a tight snapshot (avoid mega blobs)
    character_snapshot = None
    if character:
        identity = character.get("identity") or {}
        cls = character.get("class") or character.get("class_") or {}
        bg = character.get("background") or {}
        character_snapshot = {
            "id": character.get("id"),
            "name": identity.get("name"),
            "race": (character.get("race") or {}).get("key"),
            "class": cls.get("key"),
            "level": cls.get("level", 1),
            "background": bg.get("key"),
            "abilityScores": character.get("abilityScores"),
            "personality": bg.get("personality"),
            "appearance": character.get("appearance"),
        }

    report_id = str(uuid4())
    now = datetime.utcnow()
    report = {
        "id": report_id,
        "campaign_id": campaignId,
        "created_at": now,
        "message_text": message_text,
        "player_action_text": player_action_text,
        "user_note": user_note,
        "tags": tags,
        "context": {
            "intent": campaign.get("intent"),
            "world": campaign.get("world"),
            "character": character_snapshot,
            "active_quests": active_quests,
            "closed_quests": closed_quests,
            "knowledge_cards": [
                {
                    "id": c.get("id"),
                    "type": c.get("type"),
                    "title": c.get("title"),
                    "description": c.get("description"),
                    "tags": c.get("tags"),
                    "status": c.get("status"),
                }
                for c in non_quest_cards[:20]
            ],
        },
    }

    if is_db_available():
        await _scene_reports_collection().insert_one({**report, "_id": report_id})

    # Drop _id before returning
    report.pop("_id", None)
    return {"ok": True, "report_id": report_id, "created_at": now.isoformat()}


@router.get("/{campaignId}/scene-reports")
async def list_scene_reports(campaignId: str, limit: int = 50):
    """Browse recent scene reports for a campaign (newest first)."""
    if not is_db_available():
        return {"reports": []}
    cursor = (
        _scene_reports_collection()
        .find({"campaign_id": campaignId}, {"_id": 0})
        .sort("created_at", -1)
        .limit(max(1, min(200, int(limit))))
    )
    reports = await cursor.to_list(length=limit)
    # Stringify datetimes for transport
    for r in reports:
        if isinstance(r.get("created_at"), datetime):
            r["created_at"] = r["created_at"].isoformat()
    return {"reports": reports}
