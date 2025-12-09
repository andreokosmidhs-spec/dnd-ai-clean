from fastapi import APIRouter, HTTPException
from typing import List
from uuid import uuid4

from backend.models.character_v2 import CharacterV2Create, CharacterV2Stored

router = APIRouter(
    prefix="/api/characters/v2",
    tags=["characters_v2"],
)


# Simple in-memory store for now (we'll swap this for Mongo later)
FAKE_CHAR_STORE: List[CharacterV2Stored] = []


@router.post("/create", response_model=CharacterV2Stored)
async def create_character_v2(character: CharacterV2Create):
    """
    Create a new Character using the V2 schema.
    For now this just stores it in memory and echoes it back.
    Later we'll persist to the real database.
    """
    stored_character = CharacterV2Stored(id=str(uuid4()), **character.dict(by_alias=True))
    FAKE_CHAR_STORE.append(stored_character)
    return stored_character


@router.get("/", response_model=List[CharacterV2Stored])
async def list_characters_v2():
    """
    List all V2 characters (from the in-memory store).
    Mainly useful for debugging while we build this.
    """
    return FAKE_CHAR_STORE
