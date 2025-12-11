from typing import List

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.character_v2 import (
    CharacterV2Create,
    CharacterV2Stored,
    CharacterV2Update,
)

COLLECTION_NAME = "characters_v2"

# Routers for both legacy and current prefixes
router = APIRouter(prefix="/api/characters/v2", tags=["characters_v2"])
router_alias = APIRouter(prefix="/api/v2/characters", tags=["characters_v2"])

# Database will be injected from the main app
_db: AsyncIOMotorDatabase | None = None


def set_database(db: AsyncIOMotorDatabase):
    """Set the MongoDB database instance for Character V2 routes."""

    global _db
    _db = db


def get_db() -> AsyncIOMotorDatabase:
    """Get the MongoDB database instance or raise if missing."""

    if _db is None:
        raise RuntimeError("Database not initialized. Call set_database() first.")
    return _db


def get_collection():
    return get_db()[COLLECTION_NAME]


def validate_object_id(character_id: str) -> ObjectId:
    try:
        return ObjectId(character_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid character id format")


def serialize_character(doc) -> CharacterV2Stored:
    """Convert MongoDB document to API response model."""

    if not doc:
        raise HTTPException(status_code=404, detail="Character not found")

    serialized = dict(doc)
    serialized["id"] = str(serialized.pop("_id"))
    return CharacterV2Stored.model_validate(serialized)


@router.post("/create", response_model=CharacterV2Stored)
async def create_character_v2(character: CharacterV2Create):
    """Create a new Character using the V2 schema (Mongo-backed)."""

    collection = get_collection()
    character_dict = character.model_dump(by_alias=True)
    result = await collection.insert_one(character_dict)

    return CharacterV2Stored(id=str(result.inserted_id), **character_dict)


@router.get("/", response_model=List[CharacterV2Stored])
async def list_characters_v2(
    limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)
):
    """List characters with optional limit/offset pagination."""

    collection = get_collection()
    cursor = collection.find({}).skip(offset).limit(limit)
    return [serialize_character(doc) async for doc in cursor]


@router.get("/list", response_model=List[CharacterV2Stored])
async def list_characters_v2_alias(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    """Alias endpoint for listing all V2 characters."""

    return await list_characters_v2(limit=limit, offset=offset)


@router.get("/{character_id}", response_model=CharacterV2Stored)
async def get_character_v2(character_id: str):
    """Fetch a single V2 character by id from MongoDB."""

    collection = get_collection()
    object_id = validate_object_id(character_id)
    doc = await collection.find_one({"_id": object_id})
    return serialize_character(doc)


@router.put("/{character_id}", response_model=CharacterV2Stored)
async def update_character_v2(character_id: str, character: CharacterV2Create):
    """Replace a character document by id."""

    collection = get_collection()
    object_id = validate_object_id(character_id)
    existing = await collection.find_one({"_id": object_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Character not found")

    replacement = character.model_dump(by_alias=True)
    # Preserve original creation timestamp when present
    if isinstance(existing, dict) and existing.get("meta") and replacement.get("meta"):
        replacement["meta"].setdefault("createdAt", existing["meta"].get("createdAt"))

    await collection.replace_one({"_id": object_id}, replacement)
    return CharacterV2Stored(id=str(object_id), **replacement)


@router.patch("/{character_id}", response_model=CharacterV2Stored)
async def patch_character_v2(character_id: str, character: CharacterV2Update):
    """Partially update a character document by id."""

    collection = get_collection()
    object_id = validate_object_id(character_id)
    existing = await collection.find_one({"_id": object_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Character not found")

    update_data = character.model_dump(exclude_unset=True, by_alias=True)
    if update_data:
        await collection.update_one({"_id": object_id}, {"$set": update_data})

    updated = await collection.find_one({"_id": object_id})
    return serialize_character(updated)


@router.delete("/{character_id}", status_code=204)
async def delete_character_v2(character_id: str):
    """Delete a character document by id."""

    collection = get_collection()
    object_id = validate_object_id(character_id)
    result = await collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Character not found")


# Alias routes that maintain compatibility with clients using the alternate prefix
@router_alias.post("/create", response_model=CharacterV2Stored)
async def create_character_v2_alias(character: CharacterV2Create):
    return await create_character_v2(character)


@router_alias.get("/", response_model=List[CharacterV2Stored])
async def list_characters_v2_alias_root(
    limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)
):
    return await list_characters_v2(limit=limit, offset=offset)


@router_alias.get("/list", response_model=List[CharacterV2Stored])
async def list_characters_v2_alias_list(
    limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)
):
    return await list_characters_v2(limit=limit, offset=offset)


@router_alias.get("/{character_id}", response_model=CharacterV2Stored)
async def get_character_v2_alias(character_id: str):
    return await get_character_v2(character_id)


@router_alias.put("/{character_id}", response_model=CharacterV2Stored)
async def update_character_v2_alias(character_id: str, character: CharacterV2Create):
    return await update_character_v2(character_id, character)


@router_alias.patch("/{character_id}", response_model=CharacterV2Stored)
async def patch_character_v2_alias(character_id: str, character: CharacterV2Update):
    return await patch_character_v2(character_id, character)


@router_alias.delete("/{character_id}", status_code=204)
async def delete_character_v2_alias(character_id: str):
    return await delete_character_v2(character_id)


# Quick local smoke test guidance (no automated test suite available here):
# 1) POST /api/characters/v2/create with a valid CharacterV2Create payload and store the returned id.
# 2) GET  /api/characters/v2/{id} should return the created document.
# 3) PATCH /api/characters/v2/{id} with a subset of fields should update and return the merged document.
# 4) DELETE /api/characters/v2/{id} should return 204, and subsequent GET should return 404.
