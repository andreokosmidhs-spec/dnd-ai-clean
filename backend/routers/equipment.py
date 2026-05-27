"""
Equipment management endpoints.
"""
from __future__ import annotations
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["equipment"])

_db = None

def set_db(db):
    global _db
    _db = db

def get_db():
    if _db is None:
        raise RuntimeError("DB not set")
    return _db


class EquipRequest(BaseModel):
    slot: str                       # "main_hand" | "off_hand" | "armor"
    item_name: Optional[str] = None # None = unequip
    two_handed: bool = False        # for versatile weapons


@router.patch("/campaigns/{campaign_id}/characters/{character_id}/equipment")
async def update_equipment(campaign_id: str, character_id: str, req: EquipRequest):
    from services.equipment_service import equip_item, compute_ac, has_free_hand, equipment_context_line

    db = get_db()
    char_doc = await db.characters.find_one(
        {"campaign_id": campaign_id, "character_id": character_id}
    )
    if not char_doc:
        raise HTTPException(status_code=404, detail="Character not found")

    char_state = char_doc["character_state"]
    updated_state, error = equip_item(
        char_state,
        slot=req.slot,
        item_name=req.item_name,
        two_handed=req.two_handed,
    )
    if error:
        raise HTTPException(status_code=400, detail=error)

    await db.characters.update_one(
        {"campaign_id": campaign_id, "character_id": character_id},
        {"$set": {
            "character_state": updated_state,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )

    eq = updated_state.get("equipment", {})
    return {
        "success": True,
        "equipment": eq,
        "ac": compute_ac(updated_state),
        "free_hand": has_free_hand(updated_state),
        "inventory": updated_state.get("inventory", []),
        "summary": equipment_context_line(updated_state),
    }


@router.get("/campaigns/{campaign_id}/characters/{character_id}/equipment")
async def get_equipment(campaign_id: str, character_id: str):
    from services.equipment_service import (
        get_equipment as _get_eq,
        compute_ac, has_free_hand, has_spellcasting_hand,
        equipment_context_line, WEAPON_PROPERTIES, OFFHAND_ITEMS, ARMOR_PROPERTIES,
    )

    db = get_db()
    char_doc = await db.characters.find_one(
        {"campaign_id": campaign_id, "character_id": character_id}
    )
    if not char_doc:
        raise HTTPException(status_code=404, detail="Character not found")

    char_state = char_doc["character_state"]
    eq = _get_eq(char_state)

    return {
        "equipment": eq,
        "ac": compute_ac(char_state),
        "free_hand": has_free_hand(char_state),
        "spellcasting_hand": has_spellcasting_hand(char_state),
        "inventory": char_state.get("inventory", []),
        "summary": equipment_context_line(char_state),
        # Catalog for the UI
        "weapon_catalog": {k: v for k, v in WEAPON_PROPERTIES.items()},
        "offhand_catalog": OFFHAND_ITEMS,
        "armor_catalog": ARMOR_PROPERTIES,
    }
