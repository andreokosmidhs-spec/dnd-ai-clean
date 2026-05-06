"""Character Deck routes.

GET    /api/characters/{characterId}/deck                    — full deck (auto-seeds if missing)
POST   /api/characters/{characterId}/deck/cards/{cardId}/use — decrement uses or mark spent
POST   /api/characters/{characterId}/deck/long-rest          — restore per-day uses
POST   /api/characters/{characterId}/deck/draw               — draw a card from a quest/level/curse event
                                                              body: {source, title, description, rarity, mechanical?, per_day?, uses_max?}
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Body, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

from services.character_deck import (
    SOURCES,
    deck_context_block,
    merge_deck,
    seed_deck_for_character,
)

router = APIRouter(prefix="/api/characters", tags=["character-deck"])
logger = logging.getLogger(__name__)


def _db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]]


async def _load_character(character_id: str):
    db = _db()
    try:
        oid = ObjectId(character_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid character id") from exc
    char = await db.characters_v2.find_one({"_id": oid})
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    char["id"] = str(char.pop("_id"))
    return char


async def _load_or_seed_deck(character) -> List[dict]:
    db = _db()
    char_id = character["id"]
    doc = await db.character_decks.find_one({"character_id": char_id})
    if doc and isinstance(doc.get("cards"), list):
        # Re-seed and merge: handles new auto-features after level-up etc.
        fresh = seed_deck_for_character(character)
        merged = merge_deck(doc["cards"], fresh)
        await db.character_decks.update_one(
            {"character_id": char_id},
            {"$set": {"cards": merged, "updated_at": datetime.now(timezone.utc)}},
        )
        return merged
    cards = seed_deck_for_character(character)
    await db.character_decks.insert_one({
        "character_id": char_id,
        "cards": cards,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })
    return cards


@router.get("/{character_id}/deck")
async def get_deck(character_id: str):
    """Return the character's deck. Auto-seeds on first call."""
    char = await _load_character(character_id)
    cards = await _load_or_seed_deck(char)
    return {
        "character_id": character_id,
        "cards": cards,
        "context_block": deck_context_block(cards),
    }


class UseCardBody(BaseModel):
    delta: int = Field(default=1, ge=1, le=10)


@router.post("/{character_id}/deck/cards/{card_id}/use")
async def use_card(character_id: str, card_id: str, body: UseCardBody = Body(default=None)):
    """Decrement `uses_remaining` (or mark spent if no uses tracked)."""
    delta = (body.delta if body else 1) or 1
    db = _db()
    doc = await db.character_decks.find_one({"character_id": character_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Deck not found")
    cards = doc.get("cards", [])
    target = next((c for c in cards if c.get("id") == card_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Card not found in deck")
    if target.get("status") != "active":
        raise HTTPException(status_code=400, detail=f"Card is {target['status']}")

    if target.get("uses_max"):
        target["uses_remaining"] = max(0, int(target.get("uses_remaining", 0)) - delta)
        if target["uses_remaining"] == 0:
            target["status"] = "spent"
            target["used_at"] = datetime.now(timezone.utc)
    elif target.get("consumable"):
        target["status"] = "spent"
        target["used_at"] = datetime.now(timezone.utc)
    else:
        # Passive trait without uses — record use but stay active.
        target["used_at"] = datetime.now(timezone.utc)

    await db.character_decks.update_one(
        {"character_id": character_id},
        {"$set": {"cards": cards, "updated_at": datetime.now(timezone.utc)}},
    )
    return {"ok": True, "card": target}


@router.post("/{character_id}/deck/long-rest")
async def long_rest(character_id: str):
    """Restore per-day uses for all per_day cards; mark spent per-day cards
    active again. Lost cards stay lost."""
    db = _db()
    doc = await db.character_decks.find_one({"character_id": character_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Deck not found")
    cards = doc.get("cards", [])
    restored = 0
    for c in cards:
        if c.get("per_day") and c.get("status") in {"active", "spent"} and c.get("uses_max"):
            c["uses_remaining"] = c["uses_max"]
            c["status"] = "active"
            restored += 1
    await db.character_decks.update_one(
        {"character_id": character_id},
        {"$set": {"cards": cards, "updated_at": datetime.now(timezone.utc)}},
    )
    return {"ok": True, "restored": restored, "cards": cards}


class DrawCardBody(BaseModel):
    source: str
    title: str
    description: str
    rarity: str = "common"
    mechanical: Optional[str] = ""
    per_day: bool = False
    consumable: bool = False
    uses_max: int = 0
    tags: Optional[List[str]] = None


@router.post("/{character_id}/deck/draw")
async def draw_card(character_id: str, body: DrawCardBody):
    """Add a card to the deck (quest reward, curse, item, etc.)."""
    if body.source not in SOURCES:
        raise HTTPException(status_code=400, detail=f"Invalid source. Must be one of: {SOURCES}")
    db = _db()
    doc = await db.character_decks.find_one({"character_id": character_id})
    if not doc:
        # Auto-seed first then draw
        char = await _load_character(character_id)
        await _load_or_seed_deck(char)
        doc = await db.character_decks.find_one({"character_id": character_id})

    from services.character_deck import _new_card  # local import to keep module clean
    card = _new_card(
        source=body.source,
        title=body.title,
        description=body.description,
        rarity=body.rarity,
        mechanical=body.mechanical or "",
        per_day=body.per_day,
        consumable=body.consumable,
        uses_max=body.uses_max,
        tags=body.tags or [],
    )
    cards = doc.get("cards", [])
    cards.append(card)
    await db.character_decks.update_one(
        {"character_id": character_id},
        {"$set": {"cards": cards, "updated_at": datetime.now(timezone.utc)}},
    )
    return {"ok": True, "card": card}
