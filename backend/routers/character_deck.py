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
    art_key_for,
    attach_saved_art,
    deck_context_block,
    merge_deck,
    seed_deck_for_character,
)
from services.narrative_tick_service import narrative_tick_service

router = APIRouter(prefix="/api/characters", tags=["character-deck"])
logger = logging.getLogger(__name__)


# Cap on uploaded art size (post-base64). Frontend resizes to ~512px wide JPEG;
# 600 KB is a generous ceiling that comfortably fits high-quality 512x512.
_MAX_ART_BYTES = 600 * 1024


def _db():
    cli = AsyncIOMotorClient(os.getenv("MONGO_URL", ""))
    return cli[os.getenv("DB_NAME", "dnd_ai_clean")]


async def _load_art_library(db) -> dict:
    """Pull the {art_key: data_url} library from Mongo. Library is shared
    across the whole app — once a player picks art for 'Sneak Attack', every
    Rogue they ever play sees it."""
    out = {}
    cursor = db.card_art_library.find({}, {"art_key": 1, "data_url": 1, "_id": 0})
    async for doc in cursor:
        if doc.get("art_key") and doc.get("data_url"):
            out[doc["art_key"]] = doc["data_url"]
    return out


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
    art_library = await _load_art_library(db)
    doc = await db.character_decks.find_one({"character_id": char_id})
    if doc and isinstance(doc.get("cards"), list):
        # Re-seed and merge: handles new auto-features after level-up etc.
        fresh = seed_deck_for_character(character)
        merged = merge_deck(doc["cards"], fresh)
        attach_saved_art(merged, art_library)
        await db.character_decks.update_one(
            {"character_id": char_id},
            {"$set": {"cards": merged, "updated_at": datetime.now(timezone.utc)}},
        )
        return merged
    cards = seed_deck_for_character(character)
    attach_saved_art(cards, art_library)
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
    tick = None
    try:
        campaign = await db.campaigns.find_one(
            {"character_id": character_id},
            {"_id": 0},
            sort=[("updated_at", -1)],
        )
        if campaign and campaign.get("campaign_id"):
            tick = await narrative_tick_service.run_tick(
                db,
                campaign["campaign_id"],
                "long_rest",
                context={"character_id": character_id},
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Narrative tick failed after long rest for {character_id}: {exc}")
    return {"ok": True, "restored": restored, "cards": cards, "narrative_tick": tick}


class LevelUpBody(BaseModel):
    new_level: int = Field(..., ge=2, le=20, description="The level to advance to. Must equal current level + 1.")


@router.post("/{character_id}/level-up")
async def level_up(character_id: str, body: LevelUpBody):
    """Advance the character by one level.

    - Validates new_level == current_level + 1.
    - Updates the character document in characters_v2.
    - Reseeds and merges the deck (picks up all new level features).
    - Returns new_level, the list of newly gained cards, and the full deck.
    """
    char = await _load_character(character_id)

    cls_block = char.get("class_") or char.get("class") or {}
    current_level = max(1, int(cls_block.get("level") or 1))

    if body.new_level != current_level + 1:
        raise HTTPException(
            status_code=400,
            detail=f"new_level must be current level + 1 (current={current_level}, requested={body.new_level})",
        )

    # Update character level in the database before reseeding so the seed
    # function sees the new level.
    db = _db()
    try:
        oid = ObjectId(character_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid character id") from exc

    level_field = "class_.level" if "class_" in char else "class.level"
    await db.characters_v2.update_one(
        {"_id": oid},
        {"$set": {level_field: body.new_level}},
    )

    # Reload character with the updated level so seed_deck_for_character
    # produces the right feature set.
    char = await _load_character(character_id)

    # Snapshot existing card keys before the merge so we can diff afterward.
    existing_doc = await db.character_decks.find_one({"character_id": character_id})
    existing_keys: set = set()
    if existing_doc and isinstance(existing_doc.get("cards"), list):
        existing_keys = {(c.get("source"), c.get("title")) for c in existing_doc["cards"]}

    # Reseed + merge — _load_or_seed_deck now includes all features up to new_level.
    updated_cards = await _load_or_seed_deck(char)

    # Upgraded cards: existing cards whose stats were patched this level-up.
    upgraded_cards = [
        c for c in updated_cards
        if c.get("metadata", {}).get("last_upgraded_at_level") == body.new_level
    ]

    # Truly new cards: (source, title) was not in the deck before and not an upgrade.
    upgraded_keys = {(c.get("source"), c.get("title")) for c in upgraded_cards}
    new_cards = [
        c for c in updated_cards
        if (c.get("source"), c.get("title")) not in existing_keys
        and c.get("status") == "active"
        and (c.get("source"), c.get("title")) not in upgraded_keys
    ]

    return {
        "ok": True,
        "new_level": body.new_level,
        "new_cards": new_cards,
        "upgraded_cards": upgraded_cards,
        "deck": updated_cards,
        "context_block": deck_context_block(updated_cards),
    }


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
    # If saved art exists for this card's slot, attach it immediately.
    art_library = await _load_art_library(db)
    if card.get("art_key") in art_library:
        card["art_data_url"] = art_library[card["art_key"]]
    cards.append(card)
    await db.character_decks.update_one(
        {"character_id": character_id},
        {"$set": {"cards": cards, "updated_at": datetime.now(timezone.utc)}},
    )
    return {"ok": True, "card": card}


# -------------------- Card Art Library --------------------

class CardArtBody(BaseModel):
    """Either supply `data_url` directly (frontend resizes + base64-encodes
    JPEG), or provide nothing to clear the saved art."""
    data_url: Optional[str] = None


@router.post("/{character_id}/deck/cards/{card_id}/art")
async def set_card_art(character_id: str, card_id: str, body: CardArtBody):
    """Upload (or clear) the art for one deck card.

    The art is keyed by the card's `art_key` (stable hash of source+title) and
    saved to the global `card_art_library` collection. So once you pick art
    for 'Sneak Attack', every Rogue you ever play sees it; same for
    'Criminal Contact' across every Criminal-background character, etc.
    """
    db = _db()
    doc = await db.character_decks.find_one({"character_id": character_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Deck not found")
    cards = doc.get("cards", [])
    target = next((c for c in cards if c.get("id") == card_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Card not found")

    art_key = target.get("art_key") or art_key_for(target.get("source", ""), target.get("title", ""))
    target["art_key"] = art_key

    if body.data_url:
        if not body.data_url.startswith("data:image/"):
            raise HTTPException(status_code=400, detail="data_url must be a 'data:image/...' URL")
        # rough size check on the base64 payload
        if len(body.data_url) > _MAX_ART_BYTES * 1.4:  # base64 = ~1.37x raw
            raise HTTPException(status_code=413, detail=f"Art too large (max ~{_MAX_ART_BYTES // 1024} KB)")
        await db.card_art_library.update_one(
            {"art_key": art_key},
            {"$set": {
                "art_key": art_key,
                "data_url": body.data_url,
                "source": target.get("source"),
                "title": target.get("title"),
                "updated_at": datetime.now(timezone.utc),
            }, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
        target["art_data_url"] = body.data_url
        # Also update other cards in this deck sharing the same art_key
        for c in cards:
            if c.get("art_key") == art_key:
                c["art_data_url"] = body.data_url
    else:
        await db.card_art_library.delete_one({"art_key": art_key})
        target["art_data_url"] = None
        for c in cards:
            if c.get("art_key") == art_key:
                c["art_data_url"] = None

    await db.character_decks.update_one(
        {"character_id": character_id},
        {"$set": {"cards": cards, "updated_at": datetime.now(timezone.utc)}},
    )
    return {"ok": True, "art_key": art_key, "card": target}
