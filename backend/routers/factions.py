"""Faction CRUD endpoints for V2 campaigns.

Provides full upsert, reputation management, known-member tracking, and
hierarchy slot assignment for faction knowledge cards.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from services.faction_service import reputation_tier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaigns", tags=["factions"])

_db = None


def set_database(db):
    global _db
    _db = db


def get_db():
    return _db


# ---------------------------------------------------------------------------
# GET /{campaign_id}/factions
# ---------------------------------------------------------------------------

@router.get("/{campaign_id}/factions")
async def list_factions(campaign_id: str):
    """Return all faction cards for a campaign."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        cursor = db.campaign_cards.find(
            {"campaign_id": campaign_id, "type": "faction"},
            {"_id": 0},
        )
        factions = await cursor.to_list(length=200)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[factions] list failed for campaign {campaign_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc
    return {"success": True, "factions": factions}


# ---------------------------------------------------------------------------
# PUT /{campaign_id}/factions/{faction_id}  — full upsert
# ---------------------------------------------------------------------------

@router.put("/{campaign_id}/factions/{faction_id}")
async def upsert_faction(campaign_id: str, faction_id: str, request: Request):
    """Full upsert a faction card. Merges body fields; preserves id/campaign_id/type."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        body: dict = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {exc}") from exc

    # Strip protected fields from the caller's payload
    for protected in ("id", "campaign_id", "type"):
        body.pop(protected, None)

    now = datetime.now(timezone.utc).isoformat()

    try:
        existing = await db.campaign_cards.find_one(
            {"campaign_id": campaign_id, "id": faction_id},
            {"_id": 0},
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[factions] fetch failed for {faction_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    if existing:
        # Merge — only update keys present in body
        update_fields = {**body, "updatedAt": now}
        try:
            await db.campaign_cards.update_one(
                {"campaign_id": campaign_id, "id": faction_id},
                {"$set": update_fields},
            )
            updated = await db.campaign_cards.find_one(
                {"campaign_id": campaign_id, "id": faction_id},
                {"_id": 0},
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"[factions] update failed for {faction_id}: {exc}")
            raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc
    else:
        # Insert a new document with required fields plus body
        import uuid as _uuid
        new_doc = {
            "id": faction_id,
            "campaign_id": campaign_id,
            "type": "faction",
            "status": "introduced",
            "auto_seeded": False,
            "pinned": False,
            "reputation": 0,
            "known_members": [],
            "hierarchy": [],
            "tier_perks": [],
            "createdAt": now,
            "updatedAt": now,
            **body,
        }
        try:
            await db.campaign_cards.insert_one(new_doc)
            updated = await db.campaign_cards.find_one(
                {"campaign_id": campaign_id, "id": faction_id},
                {"_id": 0},
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"[factions] insert failed for {faction_id}: {exc}")
            raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    return {"success": True, "faction": updated}


# ---------------------------------------------------------------------------
# PATCH /{campaign_id}/factions/{faction_id}/reputation
# ---------------------------------------------------------------------------

@router.patch("/{campaign_id}/factions/{faction_id}/reputation")
async def update_reputation(campaign_id: str, faction_id: str, request: Request):
    """Apply a reputation delta (clamped to [-100, 100])."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        body: dict = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {exc}") from exc

    delta = body.get("delta")
    if delta is None:
        raise HTTPException(status_code=400, detail="Missing required field: delta")
    try:
        delta = int(delta)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Field 'delta' must be an integer") from exc

    try:
        faction = await db.campaign_cards.find_one(
            {"campaign_id": campaign_id, "id": faction_id},
            {"_id": 0},
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[factions] fetch failed for {faction_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    if not faction:
        raise HTTPException(status_code=404, detail=f"Faction not found: {faction_id}")

    current_rep = int(faction.get("reputation") or 0)
    new_rep = max(-100, min(100, current_rep + delta))
    tier_info = reputation_tier(new_rep)
    now = datetime.now(timezone.utc).isoformat()

    try:
        await db.campaign_cards.update_one(
            {"campaign_id": campaign_id, "id": faction_id},
            {"$set": {"reputation": new_rep, "updatedAt": now}},
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[factions] reputation update failed for {faction_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    return {"success": True, "reputation": new_rep, "tier": tier_info["label"]}


# ---------------------------------------------------------------------------
# POST /{campaign_id}/factions/{faction_id}/members
# ---------------------------------------------------------------------------

@router.post("/{campaign_id}/factions/{faction_id}/members")
async def add_member(campaign_id: str, faction_id: str, request: Request):
    """Add a known member to a faction card (deduplicated by name)."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        body: dict = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {exc}") from exc

    member_name = (body.get("name") or "").strip()
    if not member_name:
        raise HTTPException(status_code=400, detail="Missing required field: name")

    member_role = (body.get("role") or "").strip()
    member_tier = body.get("tier")
    member_card_id = (body.get("card_id") or "").strip() or None

    try:
        faction = await db.campaign_cards.find_one(
            {"campaign_id": campaign_id, "id": faction_id},
            {"_id": 0},
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[factions] fetch failed for {faction_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    if not faction:
        raise HTTPException(status_code=404, detail=f"Faction not found: {faction_id}")

    existing_members: list = faction.get("known_members") or []
    # Deduplicate by name (case-insensitive)
    if any(m.get("name", "").strip().lower() == member_name.lower() for m in existing_members):
        return {"success": True}

    new_member: dict = {"name": member_name, "role": member_role}
    if member_tier is not None:
        try:
            new_member["tier"] = int(member_tier)
        except (TypeError, ValueError):
            pass
    if member_card_id:
        new_member["card_id"] = member_card_id

    now = datetime.now(timezone.utc).isoformat()
    try:
        await db.campaign_cards.update_one(
            {"campaign_id": campaign_id, "id": faction_id},
            {
                "$push": {"known_members": new_member},
                "$set": {"updatedAt": now},
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[factions] member add failed for {faction_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    return {"success": True}


# ---------------------------------------------------------------------------
# DELETE /{campaign_id}/factions/{faction_id}/members/{member_name}
# ---------------------------------------------------------------------------

@router.delete("/{campaign_id}/factions/{faction_id}/members/{member_name}")
async def remove_member(campaign_id: str, faction_id: str, member_name: str):
    """Remove a known member from a faction card by name."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        faction = await db.campaign_cards.find_one(
            {"campaign_id": campaign_id, "id": faction_id},
            {"_id": 0},
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[factions] fetch failed for {faction_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    if not faction:
        raise HTTPException(status_code=404, detail=f"Faction not found: {faction_id}")

    now = datetime.now(timezone.utc).isoformat()
    try:
        await db.campaign_cards.update_one(
            {"campaign_id": campaign_id, "id": faction_id},
            {
                "$pull": {"known_members": {"name": member_name}},
                "$set": {"updatedAt": now},
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[factions] member remove failed for {faction_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    return {"success": True}


# ---------------------------------------------------------------------------
# PATCH /{campaign_id}/factions/{faction_id}/hierarchy/{tier_num}
# ---------------------------------------------------------------------------

@router.patch("/{campaign_id}/factions/{faction_id}/hierarchy/{tier_num}")
async def update_hierarchy_slot(
    campaign_id: str, faction_id: str, tier_num: int, request: Request
):
    """Set or clear the filled_by field of a hierarchy entry by tier number."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        body: dict = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {exc}") from exc

    # "filled_by" may be a string or null/None
    filled_by = body.get("filled_by")  # None is valid (clears the slot)

    try:
        faction = await db.campaign_cards.find_one(
            {"campaign_id": campaign_id, "id": faction_id},
            {"_id": 0},
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[factions] fetch failed for {faction_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    if not faction:
        raise HTTPException(status_code=404, detail=f"Faction not found: {faction_id}")

    hierarchy: list = list(faction.get("hierarchy") or [])
    matched = False
    for entry in hierarchy:
        if entry.get("tier") == tier_num:
            entry["filled_by"] = filled_by
            matched = True
            break

    if not matched:
        raise HTTPException(
            status_code=404,
            detail=f"Hierarchy tier {tier_num} not found on faction {faction_id}",
        )

    now = datetime.now(timezone.utc).isoformat()
    try:
        await db.campaign_cards.update_one(
            {"campaign_id": campaign_id, "id": faction_id},
            {"$set": {"hierarchy": hierarchy, "updatedAt": now}},
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[factions] hierarchy update failed for {faction_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    return {"success": True}
