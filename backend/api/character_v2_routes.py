from fastapi import APIRouter, HTTPException
from typing import List

from backend.models.character_v2 import CharacterV2

router = APIRouter(
    prefix="/api/characters/v2",
    tags=["characters_v2"],
)


# Simple in-memory store for now (we'll swap this for Mongo later)
FAKE_CHAR_STORE: List[CharacterV2] = []


@router.post("/create", response_model=CharacterV2)
async def create_character_v2(character: CharacterV2):
    """
    Create a new Character using the V2 schema.
    For now this just stores it in memory and echoes it back.
    Later we'll persist to the real database.
    """
    FAKE_CHAR_STORE.append(character)
    return character


@router.get("/", response_model=List[CharacterV2])
async def list_characters_v2():
    """
    List all V2 characters (from the in-memory store).
    Mainly useful for debugging while we build this.
    """
    return FAKE_CHAR_STORE
