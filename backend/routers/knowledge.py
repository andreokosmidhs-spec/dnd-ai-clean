"""
Knowledge & Player Notes API
Handles entity profiles and player notes with strict player-knowledge-only enforcement.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
from bson import ObjectId

from models.knowledge_models import (
    KnowledgeFact,
    PlayerNote,
    EntityProfileResponse,
    CreateNoteRequest,
    UpdateNoteRequest,
    NoteResponse
)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

# Database will be injected from main app
_db = None

def set_database(db):
    """Set the MongoDB database instance"""
    global _db
    _db = db

def get_db():
    """Get the MongoDB database instance"""
    if _db is None:
        raise RuntimeError("Database not initialized. Call set_database() first.")
    return _db


@router.get("/entity-profile/{entity_type}/{entity_id}", response_model=EntityProfileResponse)
async def get_entity_profile(
    entity_type: str,
    entity_id: str,
    campaign_id: str = Query(..., description="Campaign ID"),
    character_id: Optional[str] = Query(None, description="Optional character ID for character-specific knowledge")
):
    """
    Get player-known profile for an entity.
    
    CRITICAL: This endpoint ONLY returns information from KnowledgeFacts and PlayerNotes.
    It NEVER accesses raw world entity collections (world_npcs, world_locations, etc).
    This prevents spoiler leaks and maintains player perspective.
    """
    db = get_db()
    
    # Query knowledge facts for this entity
    fact_query = {
        "campaign_id": campaign_id,
        "entity_type": entity_type,
        "entity_id": entity_id
    }
    if character_id:
        fact_query["character_id"] = character_id
    
    facts = await db.knowledge_facts.find(fact_query, {"_id": 0}).to_list(1000)
    
    if not facts:
        # Entity not known to player yet
        raise HTTPException(status_code=404, detail=f"No knowledge about {entity_type} '{entity_id}' yet")
    
    # Query player notes
    note_query = {
        "campaign_id": campaign_id,
        "entity_type": entity_type,
        "entity_id": entity_id
    }
    if character_id:
        note_query["character_id"] = character_id
    
    notes_cursor = db.player_notes.find(note_query, {"_id": 1, "note_text": 1, "created_at": 1, "updated_at": 1})
    notes = await notes_cursor.to_list(1000)
    
    # Build profile from facts only
    profile = EntityProfileResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        name=facts[0]["entity_name"],  # Get name from first fact
        first_seen=facts[0]["revealed_at"],
        total_facts=len(facts)
    )
    
    # Aggregate facts by type
    descriptions = []
    interactions = []
    factions = []
    members = []
    quest_items = []
    related_quests = []
    notable_npcs = []
    features = []
    purposes = []
    threats = []
    rumors = []
    appearance_parts = []
    
    for fact in facts:
        fact_type = fact["fact_type"]
        fact_text = fact["fact_text"]
        
        if fact_type == "introduction" or fact_type == "description":
            descriptions.append(fact_text)
        elif fact_type == "interaction":
            interactions.append(fact_text)
        elif fact_type == "membership":
            # Parse faction membership (metadata should have faction info)
            if "faction" in fact.get("metadata", {}):
                factions.append(fact["metadata"]["faction"])
            else:
                factions.append({"name": fact_text, "role": "member"})
        elif fact_type == "quest_related":
            if "quest" in fact.get("metadata", {}):
                related_quests.append(fact["metadata"]["quest"])
            if "item" in fact.get("metadata", {}):
                quest_items.append(fact["metadata"]["item"])
        elif fact_type == "purpose":
            purposes.append(fact_text)
        elif fact_type == "threat":
            threats.append(fact_text)
        elif fact_type == "rumor":
            rumors.append(fact_text)
    
    # Fill in profile sections
    profile.known_summary = " ".join(descriptions)
    profile.important_interactions = interactions
    profile.known_factions = factions
    profile.known_members = members
    profile.quest_items_given = quest_items
    profile.related_quests = related_quests
    profile.notable_npcs = notable_npcs
    profile.known_features = features
    profile.known_threats = threats
    profile.known_rumors = rumors
    
    # Entity type specific
    if entity_type == "item" and appearance_parts:
        profile.appearance = " ".join(appearance_parts)
    
    if purposes:
        profile.known_purpose = " ".join(purposes)
    
    # Add player notes
    profile.player_notes = [
        {
            "id": str(note["_id"]),
            "text": note["note_text"],
            "created_at": note.get("created_at"),
            "updated_at": note.get("updated_at")
        }
        for note in notes
    ]
    
    profile.last_updated = max(
        [fact["revealed_at"] for fact in facts] + 
        [note.get("updated_at") for note in notes if note.get("updated_at")]
    )
    
    return profile


@router.post("/notes", response_model=NoteResponse)
async def create_player_note(request: CreateNoteRequest):
    """Create a new player note for an entity"""
    db = get_db()
    
    note_doc = {
        "campaign_id": request.campaign_id,
        "character_id": request.character_id,
        "entity_type": request.entity_type,
        "entity_id": request.entity_id,
        "note_text": request.note_text,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.player_notes.insert_one(note_doc)
    note_doc["_id"] = result.inserted_id
    
    return NoteResponse(
        note_id=str(result.inserted_id),
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        note_text=request.note_text,
        created_at=note_doc["created_at"],
        updated_at=note_doc["updated_at"]
    )


@router.put("/notes/{note_id}", response_model=NoteResponse)
async def update_player_note(note_id: str, request: UpdateNoteRequest):
    """Update an existing player note"""
    db = get_db()
    
    try:
        obj_id = ObjectId(note_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid note ID")
    
    result = await db.player_notes.find_one_and_update(
        {"_id": obj_id},
        {
            "$set": {
                "note_text": request.note_text,
                "updated_at": datetime.utcnow()
            }
        },
        return_document=True
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return NoteResponse(
        note_id=note_id,
        entity_type=result["entity_type"],
        entity_id=result["entity_id"],
        note_text=result["note_text"],
        created_at=result["created_at"],
        updated_at=result["updated_at"]
    )


@router.delete("/notes/{note_id}")
async def delete_player_note(note_id: str):
    """Delete a player note"""
    db = get_db()
    
    try:
        obj_id = ObjectId(note_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid note ID")
    
    result = await db.player_notes.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return {"success": True, "message": "Note deleted"}


@router.post("/facts")
async def create_knowledge_fact(fact: KnowledgeFact):
    """
    Create a new knowledge fact (usually called by narration system).
    This records that the player has learned something about an entity.
    """
    db = get_db()
    
    fact_doc = fact.model_dump()
    await db.knowledge_facts.insert_one(fact_doc)
    
    return {"success": True, "message": "Knowledge fact recorded"}


@router.get("/facts")
async def get_knowledge_facts(
    campaign_id: str = Query(...),
    entity_id: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    character_id: Optional[str] = Query(None)
):
    """Get all knowledge facts for a campaign (optionally filtered by entity)"""
    db = get_db()
    
    query = {"campaign_id": campaign_id}
    if entity_id:
        query["entity_id"] = entity_id
    if entity_type:
        query["entity_type"] = entity_type
    if character_id:
        query["character_id"] = character_id
    
    facts = await db.knowledge_facts.find(query, {"_id": 0}).to_list(1000)
    return {"facts": facts}

