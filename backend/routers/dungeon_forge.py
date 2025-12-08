"""
DUNGEON FORGE Router - Multi-agent AI DM endpoints
Handles world generation, character creation, intro generation, and action resolution
"""
import os
import json
import logging
import uuid
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add parent directory to path for utils import
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.api_response import api_success, api_error, validation_error, not_found_error
from utils.entity_mentions import (
    build_entity_index_from_world_blueprint,
    extract_entity_mentions
)

# Import scene generation services
from services.scene_generator import generate_scene_description
from services.hook_generator import generate_location_hooks
from services.scene_hook_integration import (
    generate_scene_with_advanced_hooks,
    convert_hooks_to_lead_deltas
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["dungeon_forge"])

# Database will be injected from main app
_db = None

# ═══════════════════════════════════════════════════════════════════════
# MODE-AWARE SENTENCE LIMITS (v6.1 Compliance)
# ═══════════════════════════════════════════════════════════════════════
MODE_LIMITS = {
    "intro": {"min": 12, "max": 16},
    "exploration": {"min": 6, "max": 10},
    "social": {"min": 6, "max": 10},
    "combat": {"min": 4, "max": 8},
    "downtime": {"min": 4, "max": 8},
    "travel": {"min": 6, "max": 8},
    "rest": {"min": 3, "max": 6},
}

def set_database(db):
    """Set the MongoDB database instance"""
    global _db
    _db = db

def get_db():
    """Get the MongoDB database instance"""
    if _db is None:
        raise RuntimeError("Database not initialized. Call set_database() first.")
    return _db


# ═══════════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════

class WorldBlueprintRequest(BaseModel):
    """Request for generating a world blueprint"""
    world_name: str
    tone: str
    starting_region_hint: str
    campaign_id: Optional[str] = None

class IntroGenerationRequest(BaseModel):
    """Request for generating cinematic intro"""
    campaign_id: str
    character_id: str

class CharacterCreateRequest(BaseModel):
    """Request to create a character"""
    campaign_id: str
    character: Dict[str, Any]


# ═══════════════════════════════════════════════════════════════════════
# MONGODB CRUD HELPERS
# ═══════════════════════════════════════════════════════════════════════

async def create_campaign(campaign_id: str, world_name: str, world_blueprint: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new campaign document in MongoDB with verification"""
    from models.game_models import Campaign
    
    db = get_db()
    campaign = Campaign(
        campaign_id=campaign_id,
        world_name=world_name,
        world_blueprint=world_blueprint,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    campaign_dict = campaign.dict()
    campaign_dict['created_at'] = campaign_dict['created_at'].isoformat()
    campaign_dict['updated_at'] = campaign_dict['updated_at'].isoformat()
    
    try:
        result = await db.campaigns.insert_one(campaign_dict)
        logger.info(f"✅ MongoDB insert: campaign inserted_id={result.inserted_id}")
        
        # VERIFICATION READ
        verify = await db.campaigns.find_one({"campaign_id": campaign_id})
        if verify:
            logger.info(f"✅ VERIFIED: Campaign {campaign_id} exists in MongoDB")
        else:
            logger.error(f"❌ VERIFICATION FAILED: Campaign {campaign_id} not found after insert")
            raise RuntimeError("Campaign insert verification failed")
        
        return campaign_dict
    except Exception as e:
        logger.error(f"❌ create_campaign failed: {e}")
        raise

async def get_campaign(campaign_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve campaign by ID"""
    db = get_db()
    campaign = await db.campaigns.find_one({"campaign_id": campaign_id})
    return campaign

async def create_world_state(campaign_id: str, initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """Create initial world state for a campaign"""
    from models.game_models import WorldStateDoc
    
    db = get_db()
    world_state = WorldStateDoc(
        campaign_id=campaign_id,
        world_state=initial_state,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    world_state_dict = world_state.dict()
    world_state_dict['created_at'] = world_state_dict['created_at'].isoformat()
    world_state_dict['updated_at'] = world_state_dict['updated_at'].isoformat()
    
    await db.world_states.insert_one(world_state_dict)
    logger.info(f"✅ World state created for campaign: {campaign_id}")
    return world_state_dict

async def get_world_state(campaign_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve world state by campaign ID"""
    db = get_db()
    world_state = await db.world_states.find_one({"campaign_id": campaign_id})
    return world_state

async def update_world_state(campaign_id: str, state_update: Dict[str, Any]) -> Dict[str, Any]:
    """Update world state with new changes"""
    db = get_db()
    result = await db.world_states.update_one(
        {"campaign_id": campaign_id},
        {
            "$set": {
                "world_state": state_update,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.matched_count == 0:
        raise ValueError(f"World state not found for campaign: {campaign_id}")
    
    return await get_world_state(campaign_id)

async def create_character_doc(campaign_id: str, character_id: str, character_state: Dict[str, Any], player_id: Optional[str] = None) -> Dict[str, Any]:
    """Create character document"""
    from models.game_models import CharacterDoc, CharacterState
    
    db = get_db()
    char_state = CharacterState(**character_state)
    char_doc = CharacterDoc(
        campaign_id=campaign_id,
        character_id=character_id,
        player_id=player_id,
        character_state=char_state,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    char_dict = char_doc.dict()
    char_dict['created_at'] = char_dict['created_at'].isoformat()
    char_dict['updated_at'] = char_dict['updated_at'].isoformat()
    
    await db.characters.insert_one(char_dict)
    logger.info(f"✅ Character created: {character_id}")
    return char_dict

async def get_character_doc(campaign_id: str, character_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve character by campaign and character ID"""
    db = get_db()
    char_doc = await db.characters.find_one({"campaign_id": campaign_id, "character_id": character_id})
    return char_doc

async def update_character_state(campaign_id: str, character_id: str, character_state: Dict[str, Any]) -> Dict[str, Any]:
    """Update character state"""
    db = get_db()
    result = await db.characters.update_one(
        {"campaign_id": campaign_id, "character_id": character_id},
        {
            "$set": {
                "character_state": character_state,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.matched_count == 0:
        raise ValueError(f"Character not found: {character_id} in campaign {campaign_id}")
    
    return await get_character_doc(campaign_id, character_id)


# ═══════════════════════════════════════════════════════════════════════
# AGENT HELPERS
# ═══════════════════════════════════════════════════════════════════════

async def run_intent_tagger(player_action: str, character_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    INTENT TAGGER: Classify player action into structured intent.
    """
    from services.llm_client import get_openai_client
    
    client = get_openai_client()
    
    prompt = f"""You are an INTENT TAGGER for a D&D 5e RPG.

Analyze this player action and output JSON with:
{{
  "needs_check": boolean,
  "ability": "STR|DEX|CON|INT|WIS|CHA" or null,
  "skill": "Stealth|Perception|Insight|Deception|Persuasion|Intimidation|Athletics|Sleight of Hand|Investigation" or null,
  "action_type": "stealth|social|investigation|combat|movement|exploration",
  "risk_level": 0-3
}}

Player action: "{player_action}"

Character proficiencies: {character_state.get("proficiencies", [])}

Output ONLY valid JSON."""
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise JSON classifier."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        content = completion.choices[0].message.content.strip()
        
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        intent = json.loads(content)
        return intent
        
    except Exception as e:
        logger.error(f"❌ Intent tagger failed: {e}")
        return {
            "needs_check": False,
            "ability": None,
            "skill": None,
            "action_type": "exploration",
            "risk_level": 1
        }


async def run_dungeon_forge(
    player_action: str,
    character_state: Dict[str, Any],
    world_blueprint: Dict[str, Any],
    world_state: Dict[str, Any],
    intent_flags: Dict[str, Any],
    check_result: Optional[int] = None,
    pacing_instructions: Dict[str, Any] = None,
    auto_revealed_info: List[str] = None,
    condition_explanations: List[str] = None,
    session_mode: Optional[Dict[str, Any]] = None,
    improvisation_result: Optional[Dict[str, Any]] = None,
    npc_personalities: Optional[List[Dict[str, Any]]] = None,
    active_tailing_quest: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    DUNGEON FORGE: Main action resolution agent.
    PHASE 1: DMG-based pacing, information, and consequence guidance.
    PHASE 2: NPC personality, improvisation, session flow.
    """
    from services.llm_client import get_openai_client
    from services.consequence_service import ConsequenceEscalation
    
    client = get_openai_client()
    from services.context_memory_service import ContextMemory
    
    # Set defaults for Phase 1 systems
    if pacing_instructions is None:
        pacing_instructions = {
            "tension_score": 20,
            "phase": "calm",
            "emoji": "🏘️",
            "dm_guidance": "Brief, functional narration",
            "narration_style": "relaxed"
        }
    
    if auto_revealed_info is None:
        auto_revealed_info = []
    
    if condition_explanations is None:
        condition_explanations = []
    
    character_name = character_state.get("name", "Adventurer")
    character_class = character_state.get("class", character_state.get("class_", "Unknown"))
    current_location = world_state.get("current_location", "Unknown")
    time_of_day = world_state.get("time_of_day", "day")
    weather = world_state.get("weather", "clear")
    
    # Generate context memory constraints (FIX for narrative coherence)
    location_constraints = ContextMemory.enforce_location_context(current_location, world_blueprint)
    npc_constraints = ContextMemory.enforce_active_npcs(
        world_state.get('active_npcs', []),
        world_blueprint
    )
    ongoing_situations = ContextMemory.get_ongoing_situation_summary(
        world_state,
        combat_active=False  # Will be set properly from context
    )
    
    # Build A-Version compliant DM prompt (Phase 1 + Phase 2)
    system_prompt = build_a_version_dm_prompt(
        character_state=character_state,
        world_state=world_state,
        world_blueprint=world_blueprint,
        intent_flags=intent_flags,
        player_action=player_action,
        mechanical_summary=None,  # Set if combat active
        pacing_instructions=pacing_instructions,
        auto_revealed_info=auto_revealed_info,
        condition_explanations=condition_explanations,
        location_constraints=location_constraints,
        npc_constraints=npc_constraints,
        ongoing_situations=ongoing_situations,
        check_result=check_result,
        session_mode=session_mode,
        improvisation_result=improvisation_result,
        npc_personalities=npc_personalities,
        active_tailing_quest=active_tailing_quest
    )
    
    # A-Version prompt now built above - removed old prompt code
    # Old prompt content removed - now using A-Version prompt built above
    
    user_content = f"""Player action: "{player_action}"
Check result: {check_result if check_result else "None (needs check if intent_flags.needs_check is true)"}

Generate the JSON response."""
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7
        )
        
        content = completion.choices[0].message.content.strip()
        
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        dm_response = json.loads(content)
        
        # P0 FIX: Validate DM response for location continuity
        from services.dm_response_validator import validate_response
        
        validation_result = validate_response(
            dm_response=dm_response,
            current_location=current_location,
            active_npcs=world_state.get('active_npcs', []),
            location_constraints=location_constraints
        )
        
        if not validation_result['valid']:
            logger.warning(f"🚫 DM Response Validation Failed: {validation_result['violations']}")
            dm_response = validation_result['corrected_response']
        
        return dm_response
        
    except Exception as e:
        logger.error(f"❌ DUNGEON FORGE failed: {e}")
        return {
            "narration": "You take a moment to assess the situation. The world around you feels full of possibility.",
            "options": [
                "Look around carefully",
                "Talk to someone nearby",
                "Move to a different location"
            ],
            "check_request": None,
            "world_state_update": {},
            "starts_combat": False
        }


# ═══════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.post("/world-blueprint/generate")
async def generate_world_blueprint_endpoint(request: WorldBlueprintRequest):
    """
    Generate a persistent world blueprint using WORLD-FORGE.
    Stores in MongoDB under campaigns collection.
    """
    try:
        from services.world_forge_service import generate_world_blueprint
        
        logger.info(f"🌍 Generating world blueprint: {request.world_name}")
        
        blueprint = generate_world_blueprint(
            world_name=request.world_name,
            tone=request.tone,
            starting_region_hint=request.starting_region_hint
        )
        
        campaign_id = request.campaign_id or str(uuid.uuid4())
        campaign_dict = await create_campaign(
            campaign_id=campaign_id,
            world_name=request.world_name,
            world_blueprint=blueprint
        )
        
        starting_location = blueprint.get("starting_town", {}).get("name", "Unknown")
        initial_world_state = {
            "location": starting_location,
            "current_location": starting_location,
            "time_of_day": "midday",
            "weather": "clear",
            "active_npcs": [],
            "faction_states": {},
            "quest_flags": {}
        }
        
        await create_world_state(campaign_id, initial_world_state)
        
        logger.info(f"✅ World blueprint generated and stored for campaign: {campaign_id}")
        return api_success({
            "campaign_id": campaign_id,
            "world_blueprint": blueprint,
            "world_state": initial_world_state
        })
        
    except ValueError as e:
        logger.error(f"❌ World blueprint generation failed: {e}")
        return api_error("service_error", str(e), status_code=500)
    except Exception as e:
        logger.error(f"❌ Unexpected error in world blueprint generation: {e}")
        return api_error("internal_error", f"World generation failed: {str(e)}", status_code=500)


@router.get("/campaigns/latest")
async def get_latest_campaign():
    """
    Fetch the most recent campaign with all data for testing.
    Returns the latest campaign that has a character.
    """
    try:
        db = get_db()
        
        # Get all campaigns sorted by newest first
        campaigns = await db.campaigns.find({}, sort=[("_id", -1)]).limit(10).to_list(10)
        
        if not campaigns:
            return not_found_error("No campaigns found")
        
        # Find the first campaign that has a character
        campaign = None
        character = None
        for camp in campaigns:
            campaign_id = camp["campaign_id"]
            char = await db.characters.find_one({"campaign_id": campaign_id})
            if char:
                campaign = camp
                character = char
                break
        
        if not campaign or not character:
            return not_found_error("No campaigns with characters found")
        
        campaign_id = campaign["campaign_id"]
        
        # Get world state
        world_state = await db.world_states.find_one({"campaign_id": campaign_id})
        
        # Re-extract entity mentions from intro for display
        intro_text = campaign.get("intro", "")
        
        # P0 FIX: Apply filter to existing intros (in case they were saved before filter was added)
        if intro_text:
            from services.narration_filter import NarrationFilter
            intro_text = NarrationFilter.apply_filter(intro_text, max_sentences=16, context="campaigns_latest_load")
            logger.info(f"✅ Filtered loaded intro to {NarrationFilter.count_sentences(intro_text)} sentences")
        
        entity_mentions = []
        if intro_text:
            try:
                entity_index = build_entity_index_from_world_blueprint(
                    campaign.get("world_blueprint", {})
                )
                entity_mentions = extract_entity_mentions(intro_text, entity_index)
                logger.info(f"🔗 Re-extracted {len(entity_mentions)} entity mentions from stored intro")
            except Exception as e:
                logger.error(f"❌ Failed to re-extract entity mentions: {e}")
        
        # Generate dynamic scene description for loaded campaigns
        starting_town = campaign.get("world_blueprint", {}).get("starting_town", {})
        starting_location = world_state.get("world_state", {}).get("current_location") if world_state else starting_town.get("name", "Unknown")
        
        # Get character state for scene generation
        character_state = character.get("character_state", {})
        world_state_dict = world_state.get("world_state", {}) if world_state else {}
        world_blueprint_dict = campaign.get("world_blueprint", {})
        
        # Generate dynamic scene description WITH ADVANCED HOOKS
        try:
            scene_data = await generate_scene_with_advanced_hooks(
                scene_type="return",  # Loaded campaigns are returns
                location=starting_town,
                character_state=character_state,
                world_state=world_state_dict,
                world_blueprint=world_blueprint_dict
            )
            
            # FILTER SCENE DESCRIPTION using exploration limits (scene descriptions are environmental)
            from services.narration_filter import NarrationFilter
            exploration_limits = MODE_LIMITS.get("exploration", {"min": 6, "max": 10})
            filtered_scene_desc = NarrationFilter.apply_filter(
                scene_data["description"], 
                max_sentences=exploration_limits["max"], 
                context="scene_description_load"
            )
            
            scene_description = {
                "location": scene_data["location"],
                "description": filtered_scene_desc,
                "why_here": scene_data["why_here"]
            }
            
            logger.info(f"✅ Generated filtered dynamic scene for {starting_town.get('name')} with {len(scene_data['quest_hooks'])} advanced hooks")
            
            # Convert advanced hooks to leads and add to Campaign Log
            try:
                from services.campaign_log_service import CampaignLogService
                from models.log_models import CampaignLogDelta
                
                lead_deltas = convert_hooks_to_lead_deltas(
                    hooks=scene_data["quest_hooks"],
                    location_id=starting_town.get("name", "Unknown"),
                    scene_id=f"scene_load_{campaign_id[:8]}"
                )
                
                if lead_deltas:
                    log_service = CampaignLogService(db)
                    await log_service.apply_delta(
                        campaign_id,
                        CampaignLogDelta(leads=lead_deltas),
                        character.get("character_id")
                    )
                    logger.info(f"🎯 Added {len(lead_deltas)} advanced quest hooks as leads to Campaign Log")
            except Exception as e:
                logger.error(f"❌ Failed to add advanced hooks to campaign log: {e}")
                
        except Exception as e:
            logger.error(f"❌ Scene generation with advanced hooks failed, using fallback: {e}")
            # Fallback to simple template
            scene_description = {
                "location": starting_town.get("name", "Unknown"),
                "description": starting_town.get("summary", "A mysterious place"),
                "why_here": f"You have arrived in {starting_town.get('name', 'this place')} seeking adventure and fortune. The world awaits your choices."
            }
        
        return api_success({
            "campaign_id": campaign_id,
            "world_blueprint": campaign.get("world_blueprint", {}),
            "intro": intro_text,
            "entity_mentions": entity_mentions,  # Add entity mentions for frontend display
            "scene_description": scene_description,  # Add scene description for loaded campaigns
            "starting_location": starting_location,
            "character": character.get("character_state", {}),
            "character_id": character.get("character_id"),
            "world_state": world_state.get("world_state", {}) if world_state else {}
        })
        
    except Exception as e:
        logger.error(f"Failed to fetch latest campaign: {e}")
        return api_error("internal_error", f"Failed to fetch campaign: {str(e)}", status_code=500)


@router.post("/intro/generate")
async def generate_intro_endpoint(request: IntroGenerationRequest):
    """
    Generate a 5-section cinematic intro using INTRO-NARRATOR.
    Consumes campaign's world_blueprint and character to ensure consistency.
    """
    try:
        from services.intro_service import generate_intro_markdown
        
        logger.info(f"📖 Generating intro for campaign: {request.campaign_id}, character: {request.character_id}")
        
        campaign = await get_campaign(request.campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail=f"Campaign not found: {request.campaign_id}")
        
        char_doc = await get_character_doc(request.campaign_id, request.character_id)
        if not char_doc:
            raise HTTPException(status_code=404, detail=f"Character not found: {request.character_id}")
        
        world_blueprint = campaign["world_blueprint"]
        character_state = char_doc["character_state"]
        
        character = {
            "name": character_state["name"],
            "race": character_state["race"],
            "class": character_state.get("class", character_state.get("class_", "Adventurer")),
            "background": character_state["background"],
            "goal": character_state["goal"]
        }
        
        region = {
            "name": world_blueprint.get("starting_region", {}).get("name", "Unknown Region"),
            "description": world_blueprint.get("starting_region", {}).get("description", "")
        }
        
        intro_md = generate_intro_markdown(
            character=character,
            region=region,
            world_blueprint=world_blueprint
        )
        
        # P0 FIX: Apply narration filter to intro (allow 16 for geography + world-building)
        from services.narration_filter import NarrationFilter
        intro_md = NarrationFilter.apply_filter(intro_md, max_sentences=16, context="intro_generate_endpoint")
        logger.info(f"✅ Intro filtered to {NarrationFilter.count_sentences(intro_md)} sentences")
        
        # P3.5 Fix: Save intro to campaign for persistence
        db = get_db()
        await db.campaigns.update_one(
            {"campaign_id": request.campaign_id},
            {"$set": {"intro": intro_md}}
        )
        logger.info(f"✅ Intro generated ({len(intro_md)} chars) and saved to campaign")
        
        # Extract entity mentions from intro
        entity_index = build_entity_index_from_world_blueprint(world_blueprint)
        entity_mentions = extract_entity_mentions(intro_md, entity_index)
        logger.info(f"🔗 Extracted {len(entity_mentions)} entity mentions from intro")
        
        # Auto-create KnowledgeFacts for entities mentioned in intro
        if entity_mentions:
            from routers import knowledge as knowledge_router
            for mention in entity_mentions:
                # For intro, all mentions are new
                await knowledge_router.get_db().knowledge_facts.insert_one({
                    "campaign_id": request.campaign_id,
                    "character_id": request.character_id,
                    "entity_type": mention["entity_type"],
                    "entity_id": mention["entity_id"],
                    "entity_name": mention["display_text"],
                    "fact_type": "introduction",
                    "fact_text": f"Introduced in campaign intro: '{mention['display_text']}'",
                    "revealed_at": datetime.now(timezone.utc),
                    "source": "narration",
                    "metadata": {}
                })
                logger.info(f"📚 Created intro knowledge fact for {mention['entity_type']}: {mention['display_text']}")
        
        # Generate dynamic scene description (where and why)
        starting_town = world_blueprint.get("starting_town", {})
        
        # CAMPAIGN LOG: Extract structured knowledge from intro
        try:
            from services.campaign_log_extractor import extract_campaign_log_from_scene
            from services.campaign_log_service import CampaignLogService
            from models.log_models import CampaignLogDelta
            
            log_service = CampaignLogService(db)
            starting_location = world_blueprint.get("starting_town", {}).get("name", "Unknown")
            scene_id = f"scene_arrival_{request.campaign_id[:8]}"
            
            # Extract structured delta using LLM (without hooks for now)
            campaign_log_delta = await extract_campaign_log_from_scene(
                narration=intro_md,
                entity_mentions=entity_mentions,
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                current_location=starting_location,
                quest_hooks=[],  # Will add hooks separately with advanced system
                scene_id=scene_id
            )
            
            # Apply delta to campaign log (knowledge from intro)
            if campaign_log_delta:
                await log_service.apply_delta(request.campaign_id, campaign_log_delta, request.character_id)
                logger.info("📖 Campaign log initialized with intro knowledge")
        except Exception as e:
            logger.error(f"❌ Campaign log extraction from intro failed: {e}")
            # Don't fail the whole request if log extraction fails
        
        # Generate dynamic scene description WITH ADVANCED HOOKS
        try:
            scene_data = await generate_scene_with_advanced_hooks(
                scene_type="arrival",  # First time arrival for new character
                location=starting_town,
                character_state=character,
                world_state={},  # Empty world state for new character
                world_blueprint=world_blueprint
            )
            
            # FILTER SCENE DESCRIPTION using exploration limits
            exploration_limits = MODE_LIMITS.get("exploration", {"min": 6, "max": 10})
            filtered_scene_desc = NarrationFilter.apply_filter(
                scene_data["description"], 
                max_sentences=exploration_limits["max"], 
                context="scene_description_arrival"
            )
            
            scene_description = {
                "location": scene_data["location"],
                "description": filtered_scene_desc,
                "why_here": scene_data["why_here"]
            }
            
            logger.info(f"✅ Generated filtered dynamic arrival scene for {starting_town.get('name')} with {len(scene_data['quest_hooks'])} advanced hooks")
            
            # Convert advanced hooks to leads and add to Campaign Log
            try:
                lead_deltas = convert_hooks_to_lead_deltas(
                    hooks=scene_data["quest_hooks"],
                    location_id=starting_town.get("name", "Unknown"),
                    scene_id=scene_id
                )
                
                if lead_deltas:
                    await log_service.apply_delta(
                        request.campaign_id,
                        CampaignLogDelta(leads=lead_deltas),
                        request.character_id
                    )
                    logger.info(f"🎯 Added {len(lead_deltas)} advanced quest hooks as leads to Campaign Log")
            except Exception as e:
                logger.error(f"❌ Failed to add advanced hooks to campaign log: {e}")
                
        except Exception as e:
            logger.error(f"❌ Scene generation with advanced hooks failed, using fallback: {e}")
            # Fallback to simple template
            scene_description = {
                "location": starting_town.get("name", "Unknown"),
                "description": starting_town.get("summary", "A mysterious place"),
                "why_here": f"You have arrived in {starting_town.get('name', 'this place')} seeking adventure and fortune. The world awaits your choices."
            }
        
        return {
            "intro_markdown": intro_md,
            "entity_mentions": entity_mentions,
            "character": character,
            "starting_location": world_blueprint.get("starting_town", {}).get("name", "Unknown"),
            "scene_description": scene_description
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Intro generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Intro generation failed: {str(e)}")


def generate_combat_options(combat_state: Dict[str, Any]) -> List[str]:
    """Generate combat options based on current state"""
    alive_enemies = [e for e in combat_state.get('enemies', []) if e.get('hp', 0) > 0]
    
    if not alive_enemies:
        return ["Continue your adventure"]
    
    options = ["Defend", "Try to flee"]
    
    # Add attack options for each enemy
    for enemy in alive_enemies[:2]:  # Limit to 2 enemies for UI
        options.insert(0, f"Attack the {enemy['name']}")
    
    return options


def build_a_version_dm_prompt(
    character_state: Dict[str, Any],
    world_state: Dict[str, Any],
    world_blueprint: Dict[str, Any],
    intent_flags: Dict[str, Any],
    player_action: str,
    mechanical_summary: Optional[Dict[str, Any]],
    pacing_instructions: Dict[str, Any],
    auto_revealed_info: List[str],
    condition_explanations: List[str],
    location_constraints: str,
    npc_constraints: str,
    ongoing_situations: str,
    check_result: Optional[int] = None,
    session_mode: Optional[Dict[str, Any]] = None,
    improvisation_result: Optional[Dict[str, Any]] = None,
    npc_personalities: Optional[List[Dict[str, Any]]] = None,
    active_tailing_quest: Optional[Dict[str, Any]] = None
) -> str:
    """
    Build A-Version compliant DM system prompt.
    
    Integrates all 10 A-Version requirements with Phase 1 & Phase 2 DMG systems.
    
    PHASE 1: Pacing, Information, Consequences, Context Memory
    PHASE 2: NPC Personality, Improvisation, Session Flow
    """
    from services.consequence_service import ConsequenceEscalation
    from services.npc_personality_service import format_for_dm_prompt as format_personality_prompt
    from services.session_flow_service import format_for_dm_prompt as format_session_prompt
    from services.improvisation_service import format_for_dm_prompt as format_improvisation_prompt
    from services.matt_mercer_narration import get_narration_guidelines_for_mode as get_mercer_guidelines_for_mode
    
    character_name = character_state.get("name", "Adventurer")
    character_class = character_state.get("class", character_state.get("class_", "Unknown"))
    current_location = world_state.get("current_location", "Unknown")
    time_of_day = world_state.get("time_of_day", "day")
    weather = world_state.get("weather", "clear")
    
    # Build mechanical summary display if combat active
    mechanical_display = ""
    if mechanical_summary:
        mechanical_display = f"""
════════════════════════════════════════════════════════
MECHANICAL COMBAT RESULTS (BACKEND AUTHORITY)
════════════════════════════════════════════════════════
{json.dumps(mechanical_summary, indent=2)}

⚠️ YOUR NARRATION MUST MATCH THESE RESULTS EXACTLY.
⚠️ DO NOT invent different outcomes.
"""
    
    # ═══════════════════════════════════════════════════════════════════
    # DUNGEON MASTER AGENT — v3.1 PRODUCTION BUILD
    # ═══════════════════════════════════════════════════════════════════
    # DUNGEON MASTER AGENT — v3.1 PRODUCTION BUILD
    # ═══════════════════════════════════════════════════════════════════
    
    # Build DC info section
    dc_info = ""
    if intent_flags.get("suggested_dc"):
        dc_info = f"""**SYSTEM-CALCULATED DC (USE THIS):**
DC: {intent_flags['suggested_dc']} ({intent_flags.get('dc_band', 'moderate')})
Ability: {intent_flags.get('suggested_ability', 'N/A')}
Skill: {intent_flags.get('suggested_skill', 'None')}
Reasoning: {intent_flags.get('dc_reasoning', '')}
**YOU MUST USE THIS DC - DO NOT INVENT YOUR OWN**
"""
    
    # Build check result info
    check_result_info = ""
    if check_result is not None:
        check_result_info = f"**CHECK RESULT:** Player rolled {check_result}"
    else:
        check_result_info = "No check result yet - await player roll if check required."
    
    prompt = f"""DUNGEON MASTER AGENT — SYSTEM PROMPT (v6.1 Unified Edition)

SYSTEM

You are the Dungeon Master (DM) Engine for a D&D sandbox application.
Your purpose is to generate immersive second-person narration describing only what the player perceives.
You do not determine mechanics, resolve checks, modify world state, invent DCs, or infer unseen information.

Your narration must strictly follow:

world_blueprint

world_state

quest_state

npc_registry

story_threads

mechanical_context

You are not a co-author of the story.
You are the camera that describes perceptible outcomes of validated mechanics.

BEHAVIOR RULES

1. Perspective & Voice

Strict second-person POV ("You step… You see…").

No first-person ("I") or third-person ("the hero").

No omniscience: only reveal what the player knows, sees, senses, or learns through checks.

2. Sentence Limits

Based on scene_mode:

intro → 12–16 sentences

exploration → 6–10 sentences

social → 6–10 sentences

combat → 4–8 sentences

travel → 6–8 sentences

rest → 3–6 sentences

NEVER exceed the max; never fall below the minimum.

3. Information Boundaries

You may not:

Reveal NPC thoughts, secrets, motivations unless discovered.

Reveal hidden traps, illusions, or enemies prematurely.

Retcon or contradict existing world canon.

Describe the outcome of ability checks unless mechanical_context provides results.

4. Canon & Consistency

You must respect ALL injected canonical data:

world_blueprint — immutable geography, factions, cultures, history

world_state — active events, known facts, current conditions

quest_state — active quests, stages, goals

npc_registry — NPC personalities, relationships, knowledge, location

story_threads — long-running narrative arcs

scene_history — previous narration context

You may add small sensory details, but NEVER contradict canon.

5. Mechanics Compliance

You must accept mechanical data as authoritative:

HP values

Conditions

Check results

Success/Fail outcomes

Damage dealt

Turn order (combat)

You cannot invent or change mechanics.

6. Tone & Style

Vivid but concise description

Balanced sensory detail (sound, sight, touch, smell)

No verbosity

No meta-commentary

No rules explanations

No dialogue unless necessary

Avoid clichés ("Suddenly…", "Out of nowhere…")

7. Always End with Player Agency

Every narration ends with:

"What do you do?"

Never create option lists or numbered choices.

TASK RULES — DM NARRATION LOOP

When generating narration, follow these steps:

1. Validate Inputs

Check that required context exists.
If something major is missing (rare), still generate narration but avoid referencing unknown details.

2. Interpret Player Action

Understand what the player attempted and what the engine resolved.

3. Integrate Mechanical Outcomes

If mechanical_context includes check results, HP changes, or conditions → narrate them faithfully.

4. Pull Relevant Canon

Use world_blueprint, quest_state, npc_registry, and story_threads to maintain consistency.

5. Construct Scene-Mode-appropriate Narration

Apply sentence limits and tone rules for the active scene_mode.

6. Maintain Story Continuity

Do not drop active quests, NPC arcs, or story threads unless resolved.

7. Add Sensory Detail

Provide environmental immersion without over-writing.

8. Finish With Agency

End with: "What do you do?"

CONTEXT

The runtime system injects:

scene_mode
player_action
mechanical_context
world_blueprint
world_state
quest_state
npc_registry
story_threads
scene_history
entity_visibility

These MUST guide your narration.

---

INJECTED CONTEXT FOR THIS REQUEST

Player Character
```
Name: {character_name}
Class: {character_class}
Level: {character_state.get("level", 1)}
HP: {character_state.get("hp", "?")} / {character_state.get("max_hp", "?")}
AC: {character_state.get("ac", "?")}

Stats:
  STR {character_state.get("stats", {}).get("strength", 10)} ({(character_state.get("stats", {}).get("strength", 10) - 10) // 2:+d})
  DEX {character_state.get("stats", {}).get("dexterity", 10)} ({(character_state.get("stats", {}).get("dexterity", 10) - 10) // 2:+d})
  CON {character_state.get("stats", {}).get("constitution", 10)} ({(character_state.get("stats", {}).get("constitution", 10) - 10) // 2:+d})
  INT {character_state.get("stats", {}).get("intelligence", 10)} ({(character_state.get("stats", {}).get("intelligence", 10) - 10) // 2:+d})
  WIS {character_state.get("stats", {}).get("wisdom", 10)} ({(character_state.get("stats", {}).get("wisdom", 10) - 10) // 2:+d})
  CHA {character_state.get("stats", {}).get("charisma", 10)} ({(character_state.get("stats", {}).get("charisma", 10) - 10) // 2:+d})

Passive Perception: {10 + (character_state.get("stats", {}).get("wisdom", 10) - 10) // 2}
Skills: {", ".join(character_state.get("skills", [])) if character_state.get("skills") else "None"}
Conditions: {", ".join(character_state.get("conditions", [])) if character_state.get("conditions") else "None"}
Inventory: {", ".join(character_state.get("inventory", [])) if character_state.get("inventory") else "Empty"}
```

Environment
```
Location: {current_location}
Time: {time_of_day}
Weather: {weather}

{location_constraints if location_constraints else ""}
```

Visible Entities
```
{npc_constraints if npc_constraints else "No visible NPCs or creatures."}
```

Ongoing Situations
```
{ongoing_situations if ongoing_situations else "None"}
```

Auto-Revealed Information (Passive Perception)
```
{", ".join(auto_revealed_info) if auto_revealed_info else "Nothing automatically noticed."}
```

Active Conditions
```
{"; ".join(condition_explanations) if condition_explanations else "None"}
```

Combat State (if applicable)
```
{mechanical_display if mechanical_display else ""}
```

System-Calculated DC (if provided)
```
{dc_info if dc_info else "No DC provided - determine if check is needed based on action context."}
```

Check Result (if resolved)
```
{check_result_info}
```

Current Scene Mode
```
{session_mode.get("mode", "exploration") if session_mode else "exploration"}
```

Player Action
```
{player_action}
```

---

OUTPUT FORMAT

Return ONLY this JSON:

{{
  "narration": "string",
  "requested_check": null | {{
      "ability": "STR | DEX | CON | INT | WIS | CHA",
      "reason": "string"
  }},
  "entities": [],
  "scene_mode": "intro | exploration | combat | social | travel | rest",
  "world_state_update": {{}},
  "player_updates": {{}}
}}

Restrictions:

requested_check ONLY when absolutely necessary.

NEVER add fields not defined above.

NEVER invent entities unless visible.

---

PRIORITY HIERARCHY

If conflicts arise:

SYSTEM

BEHAVIOR RULES

TASK RULES

CONTEXT

Style guidance (e.g., Matt Mercer inspiration)

Scene history

SYSTEM overrides everything.

---

INJECTED CONTEXT FOR THIS REQUEST

Player Character
```
Name: {character_name}
Class: {character_class}
Level: {character_state.get("level", 1)}
HP: {character_state.get("hp", "?")} / {character_state.get("max_hp", "?")}
AC: {character_state.get("ac", "?")}

Stats:
  STR {character_state.get("stats", {}).get("strength", 10)} ({(character_state.get("stats", {}).get("strength", 10) - 10) // 2:+d})
  DEX {character_state.get("stats", {}).get("dexterity", 10)} ({(character_state.get("stats", {}).get("dexterity", 10) - 10) // 2:+d})
  CON {character_state.get("stats", {}).get("constitution", 10)} ({(character_state.get("stats", {}).get("constitution", 10) - 10) // 2:+d})
  INT {character_state.get("stats", {}).get("intelligence", 10)} ({(character_state.get("stats", {}).get("intelligence", 10) - 10) // 2:+d})
  WIS {character_state.get("stats", {}).get("wisdom", 10)} ({(character_state.get("stats", {}).get("wisdom", 10) - 10) // 2:+d})
  CHA {character_state.get("stats", {}).get("charisma", 10)} ({(character_state.get("stats", {}).get("charisma", 10) - 10) // 2:+d})

Passive Perception: {10 + (character_state.get("stats", {}).get("wisdom", 10) - 10) // 2}
Skills: {", ".join(character_state.get("skills", [])) if character_state.get("skills") else "None"}
Conditions: {", ".join(character_state.get("conditions", [])) if character_state.get("conditions") else "None"}
Inventory: {", ".join(character_state.get("inventory", [])) if character_state.get("inventory") else "Empty"}
```

Environment
```
Location: {current_location}
Time: {time_of_day}
Weather: {weather}

{location_constraints if location_constraints else ""}
```

Visible Entities
```
{npc_constraints if npc_constraints else "No visible NPCs or creatures."}
```

Ongoing Situations
```
{ongoing_situations if ongoing_situations else "None"}
```

Auto-Revealed Information (Passive Perception)
```
{", ".join(auto_revealed_info) if auto_revealed_info else "Nothing automatically noticed."}
```

Active Conditions
```
{"; ".join(condition_explanations) if condition_explanations else "None"}
```

Combat State (if applicable)
```
{mechanical_display if mechanical_display else ""}
```

System-Calculated DC (if provided)
```
{dc_info if dc_info else "No DC provided - determine if check is needed based on action context."}
```

Check Result (if resolved)
```
{check_result_info}
```

Current Scene Mode
```
{session_mode.get("mode", "exploration") if session_mode else "exploration"}
```

Player Action
```
{player_action}
```

---

Generate your response now.
"""


def generate_combat_narration_from_mechanical(
    mechanical_summary: Dict[str, Any],
    character_state: Dict[str, Any]
) -> str:
    """
    Generate combat narration from mechanical combat results.
    This ensures the narration matches what actually happened mechanically.
    
    Args:
        mechanical_summary: Mechanical combat results
        character_state: Player character state
    
    Returns:
        Narration string
    """
    narration_parts = []
    
    # Player attack
    player_attack = mechanical_summary['player_attack']
    target = player_attack['target']
    
    if player_attack['critical_miss']:
        narration_parts.append(f"You swing at the {target}, but your attack goes completely awry!")
    elif player_attack['critical']:
        narration_parts.append(
            f"**Critical hit!** You strike the {target} with devastating force for **{player_attack['damage']} damage**!"
        )
        if player_attack['target_killed']:
            narration_parts.append(f"The {target} collapses, defeated!")
    elif player_attack['hit']:
        narration_parts.append(
            f"You hit the {target} for **{player_attack['damage']} damage**! "
            f"({player_attack['target_hp_remaining']}/{player_attack['target_max_hp']} HP remaining)"
        )
        if player_attack['target_killed']:
            narration_parts.append(f"The {target} falls defeated!")
    else:
        narration_parts.append(
            f"You attack the {target}, but miss! "
            f"(Rolled {player_attack['total_attack']} vs AC {player_attack['target_ac']})"
        )
    
    # Enemy turns
    if mechanical_summary['enemy_turns']:
        enemy_narration_parts = []
        for enemy_action in mechanical_summary['enemy_turns']:
            attacker = enemy_action['attacker']
            if enemy_action['critical_miss']:
                enemy_narration_parts.append(f"The {attacker} swings wildly and misses completely.")
            elif enemy_action['critical']:
                enemy_narration_parts.append(
                    f"**Critical hit!** The {attacker} strikes you hard for **{enemy_action['damage']} damage**!"
                )
            elif enemy_action['hit']:
                enemy_narration_parts.append(
                    f"The {attacker} hits you for **{enemy_action['damage']} damage**!"
                )
            else:
                enemy_narration_parts.append(f"The {attacker} attacks but you dodge!")
        
        if enemy_narration_parts:
            narration_parts.append("\n\n" + " ".join(enemy_narration_parts))
        
        if mechanical_summary['total_damage_to_player'] > 0:
            current_hp = character_state.get('hp', 10)
            max_hp = character_state.get('max_hp', 10)
            narration_parts.append(
                f"\n\n**You take {mechanical_summary['total_damage_to_player']} total damage. HP: {current_hp}/{max_hp}**"
            )
    
    # Combat end
    if mechanical_summary['combat_over']:
        if mechanical_summary['outcome'] == 'victory':
            narration_parts.append("\n\n**Victory!** All enemies have been defeated!")
        elif mechanical_summary['outcome'] == 'player_defeated':
            narration_parts.append("\n\n**You have been defeated!** Everything goes dark...")
    
    return "".join(narration_parts)


async def select_homeland_for_character(
    character: dict,
    world_blueprint: dict
) -> str:
    """
    Use AI to select an appropriate homeland from world_blueprint POIs.
    
    Args:
        character: Character state dict with name, race, class, background
        world_blueprint: World blueprint with POIs, factions, starting_town
    
    Returns:
        Name of selected homeland (POI or starting_town)
    """
    # Extract available locations
    starting_town = world_blueprint.get("starting_town", {})
    pois = world_blueprint.get("points_of_interest", [])
    
    # Build list of viable homelands
    locations = []
    if starting_town.get("name"):
        locations.append({
            "name": starting_town["name"],
            "type": starting_town.get("type", "town"),
            "summary": starting_town.get("summary", "")
        })
    
    for poi in pois[:5]:  # Limit to first 5 POIs
        if poi.get("name"):
            locations.append({
                "name": poi["name"],
                "type": poi.get("type", "location"),
                "summary": poi.get("summary", "")
            })
    
    if not locations:
        return "Unknown Land"
    
    # Use AI to select best fit
    from services.llm_client import get_openai_client
    client = get_openai_client()
    
    prompt = f"""Given this character and available locations, select the MOST appropriate homeland.

CHARACTER:
- Name: {character.get('name')}
- Race: {character.get('race')}
- Class: {character.get('class')}
- Background: {character.get('background')}

AVAILABLE LOCATIONS:
{chr(10).join([f"- {loc['name']} ({loc['type']}): {loc['summary']}" for loc in locations])}

Select the single best-fitting location name. Consider:
- Race/class synergy (e.g., elves from forests, dwarves from mountains)
- Background compatibility (e.g., nobles from cities, outlanders from wilderness)

Respond with ONLY the location name, nothing else."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a D&D world-building assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=50
        )
        
        selected = response.choices[0].message.content.strip()
        
        # Validate selection exists in locations
        if any(loc['name'].lower() in selected.lower() for loc in locations):
            logger.info(f"🏠 Selected homeland: {selected} for {character.get('name')}")
            return selected
        else:
            # Fallback to starting town
            fallback = locations[0]['name']
            logger.warning(f"⚠️ AI selected invalid homeland '{selected}', using fallback: {fallback}")
            return fallback
            
    except Exception as e:
        logger.error(f"❌ Homeland selection failed: {e}")
        return locations[0]['name'] if locations else "Unknown Land"


@router.post("/characters/create")
async def create_character_endpoint(request: CharacterCreateRequest):
    """
    Create a character and store in MongoDB.
    Returns character_id for use in subsequent requests.
    """
    try:
        from models.game_models import CharacterState
        
        logger.info(f"🎭 Creating character for campaign: {request.campaign_id}")
        
        character_id = str(uuid.uuid4())
        char_data = request.character
        
        # Build CharacterState using 'class' key with alias
        # P3: Explicitly set xp_to_next using progression service
        from services.progression_service import get_xp_to_next
        char_level = char_data.get("level", 1)
        
        character_state = CharacterState(**{
            "name": char_data.get("name", "Unnamed"),
            "race": char_data.get("race", "Human"),
            "class": char_data.get("class", "Fighter"),
            "background": char_data.get("background", "Folk Hero"),
            "goal": char_data.get("aspiration", {}).get("goal", "Survive and thrive"),
            "level": char_level,
            "hp": char_data.get("hitPoints", 10),
            "max_hp": char_data.get("hitPoints", 10),
            "ac": 10 + ((char_data.get("stats", {}).get("dexterity", 10) - 10) // 2),
            "abilities": {
                "str": char_data.get("stats", {}).get("strength", 10),
                "dex": char_data.get("stats", {}).get("dexterity", 10),
                "con": char_data.get("stats", {}).get("constitution", 10),
                "int": char_data.get("stats", {}).get("intelligence", 10),
                "wis": char_data.get("stats", {}).get("wisdom", 10),
                "cha": char_data.get("stats", {}).get("charisma", 10),
            },
            "proficiencies": char_data.get("proficiencies", []),
            "languages": char_data.get("languages", []),
            "inventory": char_data.get("inventory", []),
            "features": [
                # P3.5 Fix: Handle both string and dict formats for features/racial_traits
                f if isinstance(f, str) else f.get("name", str(f))
                for f in char_data.get("racial_traits", [])
            ],
            "conditions": [],
            "reputation": {},
            # Equipment & Resources
            "gold": char_data.get("gold", 0),
            "tool_proficiencies": char_data.get("tool_proficiencies", []),
            "weapon_proficiencies": char_data.get("weapon_proficiencies", []),
            "armor_proficiencies": char_data.get("armor_proficiencies", []),
            "racial_traits": char_data.get("racial_traits", []),
            "speed": char_data.get("speed", 30),  # Base movement speed
            # P3: Progression fields
            "current_xp": 0,
            "xp_to_next": get_xp_to_next(char_level),
            "proficiency_bonus": 2,
            "attack_bonus": 0,
            "injury_count": 0
        })
        
        # P3.5: Auto-select homeland from world_blueprint based on character
        db = get_db()
        campaign_doc = await db.campaigns.find_one({"campaign_id": request.campaign_id})
        
        if campaign_doc and "world_blueprint" in campaign_doc:
            world_blueprint = campaign_doc["world_blueprint"]
            
            # AI selects appropriate homeland from available locations
            homeland = await select_homeland_for_character(
                character_state.dict(),
                world_blueprint
            )
            
            # Add homeland to character
            character_state_dict = character_state.dict()
            character_state_dict["homeland"] = homeland
            
            char_doc = await create_character_doc(
                campaign_id=request.campaign_id,
                character_id=character_id,
                character_state=character_state_dict,
                player_id=None
            )
            
            # P3.5: Generate intro immediately and return it with character
            from services.intro_service import generate_intro_markdown
            
            starting_town = world_blueprint.get("starting_town", {})
            region = {
                "name": starting_town.get("name", "Unknown Region"),
                "summary": starting_town.get("summary", ""),
                "tone": world_blueprint.get("world_core", {}).get("tone", "balanced")
            }
            
            intro_md = generate_intro_markdown(
                character=character_state_dict,
                region=region,
                world_blueprint=world_blueprint
            )
            
            # FILTER INTRO NARRATION (allow 16 sentences for geography + world-building)
            from services.narration_filter import NarrationFilter
            intro_md = NarrationFilter.apply_filter(intro_md, max_sentences=16, context="character_intro")
            logger.info(f"✅ Intro filtered to {NarrationFilter.count_sentences(intro_md)} sentences")
            
            # Save intro to campaign
            await db.campaigns.update_one(
                {"campaign_id": request.campaign_id},
                {"$set": {"intro": intro_md}}
            )
            
            # Extract entity mentions from intro for display
            entity_index = build_entity_index_from_world_blueprint(world_blueprint)
            entity_mentions = extract_entity_mentions(intro_md, entity_index)
            logger.info(f"🔗 Extracted {len(entity_mentions)} entity mentions from intro")
            
            # Auto-create KnowledgeFacts for entities mentioned in intro
            if entity_mentions:
                from routers import knowledge as knowledge_router
                for mention in entity_mentions:
                    await knowledge_router.get_db().knowledge_facts.insert_one({
                        "campaign_id": request.campaign_id,
                        "character_id": character_id,
                        "entity_type": mention["entity_type"],
                        "entity_id": mention["entity_id"],
                        "entity_name": mention["display_text"],
                        "fact_type": "introduction",
                        "fact_text": f"Introduced in campaign intro: '{mention['display_text']}'",
                        "revealed_at": datetime.now(timezone.utc),
                        "source": "narration",
                        "metadata": {}
                    })
                    logger.info(f"📚 Created intro knowledge fact for {mention['entity_type']}: {mention['display_text']}")
            
            # CAMPAIGN LOG: Extract structured knowledge from intro
            try:
                from services.campaign_log_extractor import extract_campaign_log_from_scene
                from services.campaign_log_service import CampaignLogService
                from models.log_models import CampaignLogDelta
                
                log_service = CampaignLogService(db)
                starting_location = starting_town.get("name", "Unknown")
                scene_id = f"scene_arrival_{request.campaign_id[:8]}_internal"
                
                # Extract structured delta using LLM (without hooks for now)
                campaign_log_delta = await extract_campaign_log_from_scene(
                    narration=intro_md,
                    entity_mentions=entity_mentions,
                    openai_api_key=os.getenv("OPENAI_API_KEY"),
                    current_location=starting_location,
                    quest_hooks=[],  # Will add hooks separately with advanced system
                    scene_id=scene_id
                )
                
                # Apply delta to campaign log (knowledge from intro)
                if campaign_log_delta:
                    await log_service.apply_delta(request.campaign_id, campaign_log_delta, character_id)
                    logger.info("📖 Campaign log initialized with intro knowledge")
            except Exception as e:
                logger.error(f"❌ Campaign log extraction from intro failed: {e}")
                # Don't fail the whole request if log extraction fails
            
            # Generate dynamic scene description WITH ADVANCED HOOKS
            try:
                scene_data = await generate_scene_with_advanced_hooks(
                    scene_type="arrival",  # First time arrival for new character
                    location=starting_town,
                    character_state=character_state_dict,
                    world_state={},  # Empty world state for new character
                    world_blueprint=world_blueprint
                )
                
                # FILTER SCENE DESCRIPTION using exploration limits
                from services.narration_filter import NarrationFilter
                exploration_limits = MODE_LIMITS.get("exploration", {"min": 6, "max": 10})
                filtered_scene_desc = NarrationFilter.apply_filter(
                    scene_data["description"], 
                    max_sentences=exploration_limits["max"], 
                    context="scene_description_character_creation"
                )
                
                scene_description = {
                    "location": scene_data["location"],
                    "description": filtered_scene_desc,
                    "why_here": scene_data["why_here"]
                }
                
                logger.info(f"✅ Generated filtered dynamic arrival scene for {starting_town.get('name')} with {len(scene_data['quest_hooks'])} advanced hooks (internal)")
                
                # Convert advanced hooks to leads and add to Campaign Log
                try:
                    lead_deltas = convert_hooks_to_lead_deltas(
                        hooks=scene_data["quest_hooks"],
                        location_id=starting_town.get("name", "Unknown"),
                        scene_id=scene_id
                    )
                    
                    if lead_deltas:
                        await log_service.apply_delta(
                            request.campaign_id,
                            CampaignLogDelta(leads=lead_deltas),
                            character_id
                        )
                        logger.info(f"🎯 Added {len(lead_deltas)} advanced quest hooks as leads to Campaign Log (internal)")
                except Exception as e:
                    logger.error(f"❌ Failed to add advanced hooks to campaign log: {e}")
                    
            except Exception as e:
                logger.error(f"❌ Scene generation with advanced hooks failed, using fallback: {e}")
                # Fallback to simple template
                scene_description = {
                    "location": starting_town.get("name", "Unknown"),
                    "description": starting_town.get("summary", "A mysterious place"),
                    "why_here": f"You have arrived in {starting_town.get('name', 'this place')} seeking adventure and fortune. The world awaits your choices."
                }
            
            logger.info(f"✅ Character created: {character_id} - {character_state.name} from {homeland}")
            logger.info(f"✅ Intro generated ({len(intro_md)} chars) and included in response")
            
            # P0 FIX: Log the exact intro being returned to verify filter is working
            intro_sentence_count = NarrationFilter.count_sentences(intro_md)
            logger.info(f"🔍 DEBUG: intro_md has {intro_sentence_count} sentences")
            logger.info(f"🔍 DEBUG: First 200 chars of intro_md being returned: {intro_md[:200]}")
            
            return api_success({
                "character_id": character_id,
                "character_state": character_state_dict,
                "intro_markdown": intro_md,
                "entity_mentions": entity_mentions,
                "starting_location": starting_town.get("name", "Unknown"),
                "scene_description": scene_description
            })
        else:
            # Fallback if world not found
            char_doc = await create_character_doc(
                campaign_id=request.campaign_id,
                character_id=character_id,
                character_state=character_state.dict(),
                player_id=None
            )
            
            logger.info(f"✅ Character created: {character_id} - {character_state.name}")
            return api_success({
                "character_id": character_id,
                "character_state": character_state.dict()
            })
        
    except Exception as e:
        logger.error(f"❌ Character creation failed: {e}", exc_info=True)
        return api_error("internal_error", f"Character creation failed: {str(e)}", status_code=500)


@router.post("/rpg_dm/resolve_check")
async def resolve_check(request: dict):
    """
    Resolve an ability check after player rolls dice.
    
    Flow:
    1. Receive PlayerRoll from frontend
    2. Retrieve CheckRequest from session/previous DM response
    3. Create CheckResolution with graded outcome
    4. Call DM to narrate the outcome based on resolution
    5. Return narrated outcome to frontend
    """
    try:
        from models.check_models import PlayerRoll, CheckRequest, CheckResolution
        
        campaign_id = request.get("campaign_id")
        character_id = request.get("character_id")
        roll_data = request.get("player_roll")
        check_request_data = request.get("check_request")
        
        if not all([campaign_id, character_id, roll_data, check_request_data]):
            return validation_error("Missing required fields: campaign_id, character_id, player_roll, check_request")
        
        # Parse models
        try:
            player_roll = PlayerRoll(**roll_data)
            check_request = CheckRequest(**check_request_data)
        except Exception as e:
            return validation_error(f"Invalid roll or check data: {str(e)}")
        
        # Create CheckResolution
        resolution = CheckResolution.from_roll_and_request(player_roll, check_request)
        
        logger.info(f"🎲 Check Resolution: {check_request.skill or check_request.ability} check")
        logger.info(f"   Roll: {player_roll.d20_roll} + {player_roll.modifier} = {player_roll.total}")
        logger.info(f"   DC: {check_request.dc} | Result: {resolution.outcome} (margin: {resolution.margin:+d})")
        
        # Now call DM to narrate the outcome
        # We need to format this as a special "resolve check" action
        db = get_db()
        
        # Fetch campaign and character
        campaign = await db.campaigns.find_one({"campaign_id": campaign_id}, {"_id": 0})
        if not campaign:
            return not_found_error(f"Campaign {campaign_id} not found")
        
        char_doc = await db.characters.find_one({"campaign_id": campaign_id, "character_id": character_id}, {"_id": 0})
        if not char_doc:
            return not_found_error(f"Character {character_id} not found")
        
        world_state = await db.world_states.find_one({"campaign_id": campaign_id, "character_id": character_id}, {"_id": 0})
        if not world_state:
            world_state = {"world_state": {}}
        
        # Build a narration prompt for the DM with the resolution
        narration_prompt = f"""The player just completed an ability check. Here is the structured result:

CHECK: {check_request.skill or check_request.ability} ({check_request.ability})
ACTION: {check_request.action_context}
DC: {check_request.dc} ({check_request.dc_band})

ROLL RESULT:
- D20 Roll: {player_roll.d20_roll}
- Modifier: {player_roll.modifier}
- Total: {player_roll.total}

OUTCOME: {resolution.outcome.upper()}
- Success: {resolution.success}
- Margin: {resolution.margin:+d}
- Tier: {resolution.outcome_tier}

NARRATION GUIDANCE: {resolution.suggested_narration_style}

YOU MUST:
1. Narrate what happens based on this result
2. DO NOT re-roll or change the outcome
3. Show specific consequences (items found, information learned, complications, etc.)
4. Update world_state_update if needed
5. Update player_updates with any rewards/consequences"""

        # Call DUNGEON FORGE with the resolution context
        try:
            dm_response = await run_dungeon_forge(
                player_action=narration_prompt,
                character_state=char_doc["character_state"],
                world_blueprint=campaign["world_blueprint"],
                world_state=world_state["world_state"],
                intent_flags={"check_resolution": True, "resolution": resolution.dict()},
                check_result=player_roll.total,  # Pass the total for reference
                pacing_instructions=None,
                auto_revealed_info=[],
                condition_explanations=[],
                session_mode=None,  # No specific mode for check resolution
                improvisation_result=None,
                npc_personalities=[]
            )
            
            # Extract narration
            narration_text = dm_response.get("narration", "")
            logger.info(f"📝 DM narration received: {len(narration_text)} chars")
            
            # Apply narration filter using exploration limits (checks can happen in any mode, exploration is most common)
            from services.narration_filter import NarrationFilter
            exploration_limits = MODE_LIMITS.get("exploration", {"min": 6, "max": 10})
            narration_text = NarrationFilter.apply_filter(narration_text, max_sentences=exploration_limits["max"], context="check_resolution")
            logger.info(f"✂️ Narration filtered: {len(narration_text)} chars")
            
            # Extract entity mentions
            entity_index = build_entity_index_from_world_blueprint(
                campaign["world_blueprint"],
                world_state["world_state"]
            )
            entity_mentions = extract_entity_mentions(narration_text, entity_index)
            
            # Apply world state updates
            world_state_update = dm_response.get("world_state_update", {})
            if world_state_update:
                current_world = world_state["world_state"]
                current_world.update(world_state_update)
                await db.world_states.update_one(
                    {"campaign_id": campaign_id, "character_id": character_id},
                    {"$set": {"world_state": current_world}}
                )
            
            # Apply player updates
            player_updates = dm_response.get("player_updates", {})
            if player_updates:
                # Update character state
                current_char = char_doc["character_state"]
                if "gold_gained" in player_updates:
                    current_char["gold"] = current_char.get("gold", 0) + player_updates["gold_gained"]
                if "items_gained" in player_updates:
                    current_char["inventory"] = current_char.get("inventory", []) + player_updates["items_gained"]
                if "hp" in player_updates:
                    current_char["hp"] = player_updates["hp"]
                
                await update_character_state(campaign_id, character_id, current_char)
            
            # v4.1 UNIFIED SPEC: No options field - narration ends with open prompts
            response_data = {
                "narration": narration_text,
                "entity_mentions": entity_mentions,
                "world_state_update": world_state_update,
                "player_updates": player_updates,
                "resolution": {
                    "success": resolution.success,
                    "outcome": resolution.outcome,
                    "margin": resolution.margin
                }
            }
            
            logger.info(f"✅ Check resolution complete - returning response")
            logger.info(f"   Narration: {len(narration_text)} chars")
            logger.info(f"   Outcome: {resolution.outcome}")
            
            return api_success(response_data)
            
        except Exception as e:
            logger.error(f"❌ DM narration failed: {e}", exc_info=True)
            return api_error("internal_error", f"Failed to generate narration: {str(e)}", status_code=500)
        
    except Exception as e:
        logger.error(f"❌ Check resolution failed: {e}", exc_info=True)
        return api_error("internal_error", f"Check resolution failed: {str(e)}", status_code=500)


@router.post("/rpg_dm/action")
async def process_action(request: dict):
    """
    Main gameplay action endpoint for DUNGEON FORGE.
    
    Orchestration flow:
    1. Fetch campaign, character, world_state, combat_state from MongoDB (parallelized)
    2. Route to appropriate handler:
       - If combat active: COMBAT ENGINE with target resolution
       - If hostile action detected: Target resolution → Combat initiation or Plot Armor
       - Else: ACTION MODE (INTENT TAGGER → DUNGEON FORGE → LORE CHECKER → WORLD MUTATOR)
    
    Phase 1 Changes:
    - Added target resolution using target_resolver service
    - Added NPC-to-enemy conversion for hostile actions
    - Added plot armor checking for essential NPCs
    - Mechanical combat resolution BEFORE DM narration
    """
    try:
        from models.game_models import ActionRequest
        
        action_req = ActionRequest(**request)
        campaign_id = action_req.campaign_id
        character_id = action_req.character_id
        player_action = action_req.player_action
        check_result = action_req.check_result
        client_target_id = action_req.client_target_id  # Phase 1: Explicit target from frontend
        
        logger.info(f"🎮 Processing action for campaign: {campaign_id}, character: {character_id}")
        logger.info(f"   Action: {player_action[:100]}")
        if client_target_id:
            logger.info(f"   Explicit target: {client_target_id}")
        
        # Fetch state from DB (parallelized for performance)
        db = get_db()
        campaign, char_doc, world_state, combat_doc = await asyncio.gather(
            get_campaign(campaign_id),
            get_character_doc(campaign_id, character_id),
            get_world_state(campaign_id),
            db.combats.find_one({"campaign_id": campaign_id, "character_id": character_id})
        )
        
        # Validate all required data exists
        if not campaign:
            raise HTTPException(status_code=404, detail=f"Campaign not found: {campaign_id}")
        if not char_doc:
            raise HTTPException(status_code=404, detail=f"Character not found: {character_id}")
        if not world_state:
            raise HTTPException(status_code=404, detail=f"World state not found for campaign: {campaign_id}")
        
        is_combat_active = combat_doc and not combat_doc.get("combat_state", {}).get("combat_over", True)
        
        # Ensure NPCs are activated for current location
        from services.npc_activation_service import populate_active_npcs_for_location, ensure_npcs_have_ids
        
        # Ensure all NPCs have IDs
        ensure_npcs_have_ids(campaign["world_blueprint"])
        
        # Get current location
        current_location = world_state["world_state"].get("current_location", world_state["world_state"].get("location", ""))
        
        if not current_location:
            # Default to starting town
            current_location = campaign["world_blueprint"].get("starting_town", {}).get("name", "Unknown")
        
        # TAILING QUEST DETECTION: Check if player is following someone
        from services.tailing_quest_service import TailingQuestService
        from services.chase_mechanics import ChaseMechanics
        
        tailing_intent = TailingQuestService.detect_tailing_intent(player_action)
        active_tailing_quest = None
        chase_check_required = None
        
        if tailing_intent:
            logger.info(f"🕵️ Tailing intent detected: {tailing_intent}")
            
            # Check if there's already an active tailing quest
            existing_quests = world_state["world_state"].get("active_quests", {})
            active_tailing = [q for q in existing_quests.values() if q.get("type") == "investigation" and q.get("status") == "active"]
            
            if not active_tailing:
                # Create new tailing quest
                quest_data = await TailingQuestService.create_tailing_quest(
                    campaign_id=campaign_id,
                    character_id=character_id,
                    target_name=tailing_intent["target"],
                    location=current_location,
                    world_state=world_state["world_state"],
                    db=db
                )
                
                # Store in world state
                if "active_quests" not in world_state["world_state"]:
                    world_state["world_state"]["active_quests"] = {}
                world_state["world_state"]["active_quests"][quest_data["quest_id"]] = quest_data
                
                active_tailing_quest = quest_data
                logger.info(f"✨ Created tailing quest: {quest_data['quest_id']}")
            else:
                active_tailing_quest = active_tailing[0]
                logger.info(f"📋 Continuing existing tailing quest: {active_tailing_quest['quest_id']}")
        
        # LOCATION CHANGE DETECTION: Check if player is moving to a new location
        from services.location_detector import LocationDetector
        
        new_location = await LocationDetector.detect_and_update_location(
            action=player_action,
            world_blueprint=campaign["world_blueprint"],
            current_location=current_location
        )
        
        location_changed = False
        if new_location:
            logger.info(f"🗺️ LOCATION CHANGE DETECTED: '{current_location}' → '{new_location}'")
            current_location = new_location
            location_changed = True
            
            # Update world state with new location
            world_state["world_state"]["current_location"] = new_location
            
            # Generate scene for new location
            try:
                from services.scene_hook_integration import generate_scene_with_advanced_hooks
                
                scene_result = await generate_scene_with_advanced_hooks(
                    campaign_id=campaign_id,
                    character_id=character_id,
                    location_name=new_location,
                    world_blueprint=campaign["world_blueprint"],
                    world_state=world_state["world_state"],
                    character_state=char_doc["character_state"],
                    db=db
                )
                
                # Store scene for later injection into narration
                world_state["_generated_scene"] = scene_result.get("scene_description", "")
                
                # Update active NPCs for new location
                if scene_result.get("active_npcs"):
                    world_state["world_state"]["active_npcs"] = scene_result["active_npcs"]
                    logger.info(f"👥 Updated active NPCs for {new_location}: {scene_result['active_npcs']}")
                    
                logger.info(f"✨ Generated scene for new location: {new_location}")
                
            except Exception as e:
                logger.error(f"❌ Failed to generate scene: {e}")
        
        # Populate active NPCs if not already done
        if not world_state["world_state"].get("active_npcs"):
            active_npc_ids = populate_active_npcs_for_location(
                location_name=current_location,
                world_blueprint=campaign["world_blueprint"],
                world_state=world_state["world_state"]
            )
            
            # Update world state with active NPCs
            world_state["world_state"]["active_npcs"] = active_npc_ids
            await update_world_state(campaign_id, world_state["world_state"])
            logger.info(f"🎭 Activated {len(active_npc_ids)} NPCs for location: {current_location}")
        else:
            logger.info(f"🎭 {len(world_state['world_state'].get('active_npcs', []))} NPCs already active")
        
        # PHASE 1: DMG SYSTEMS INTEGRATION (p.24, p.26-27, p.32)
        from services.pacing_service import TensionManager
        from services.information_service import InformationDispenser
        from services.consequence_service import ConsequenceEscalation
        
        # Calculate current tension (DMG p.24)
        tension_score = TensionManager.calculate_tension(
            world_state=world_state["world_state"],
            character_state=char_doc["character_state"],
            combat_active=is_combat_active,
            recent_actions=[player_action]
        )
        
        pacing_instructions = TensionManager.get_dm_pacing_instructions(tension_score)
        logger.info(f"📊 TENSION: {tension_score}/100 - Phase: {pacing_instructions['phase']} {pacing_instructions['emoji']}")
        
        # Update tension state in world_state
        tension_state = TensionManager.update_tension_state(tension_score, world_state["world_state"])
        world_state["world_state"]["tension_state"] = tension_state
        
        # PHASE 2: SESSION FLOW & IMPROVISATION (DMG p.20-24, p.28-29)
        from services.session_flow_service import detect_mode, format_for_dm_prompt as format_mode_prompt
        from services.improvisation_service import classify_action, format_for_dm_prompt as format_improv_prompt
        from services.npc_personality_service import format_for_dm_prompt as format_personality_prompt
        
        # Detect session mode (DMG p.20-21)
        session_mode = detect_mode(
            player_action=player_action,
            intent_flags={},  # Will be populated by intent_tagger
            world_state=world_state["world_state"],
            combat_active=is_combat_active
        )
        logger.info(f"🎮 Session Mode: {session_mode['mode']}")
        
        # Classify action for improvisation (DMG p.28-29)
        improvisation_result = classify_action(
            player_action=player_action,
            intent_flags={},  # Will be populated
            character_state=char_doc["character_state"]
        )
        logger.info(f"🎭 Improvisation: {improvisation_result['classification']}")
        
        # Get NPC personalities for active NPCs (PHASE 2)
        active_npc_ids = world_state["world_state"].get("active_npcs", [])
        npc_personalities_data = []
        if active_npc_ids and "npc_personalities" in world_state["world_state"]:
            for npc_id in active_npc_ids[:3]:  # Limit to 3 for prompt size
                personality = world_state["world_state"]["npc_personalities"].get(npc_id)
                if personality:
                    npc_personalities_data.append(personality)
        logger.info(f"✨ {len(npc_personalities_data)} NPC personalities loaded for prompt")
        
        # Apply passive Perception (DMG p.26)
        auto_revealed_info = InformationDispenser.apply_passive_perception(
            character_state=char_doc["character_state"],
            world_state=world_state["world_state"]
        )
        
        # Clarify active conditions (DMG p.27)
        condition_explanations = InformationDispenser.clarify_conditions(
            character_state=char_doc["character_state"]
        )
        
        # Phase 1: Check for hostile action and resolve target BEFORE combat or DM
        from services.target_resolver import resolve_target, is_hostile_action
        
        if is_hostile_action(player_action) and not is_combat_active:
            logger.info("🎯 Hostile action detected outside combat - resolving target...")
            
            target_resolution = resolve_target(
                player_action=player_action,
                client_target_id=client_target_id,
                combat_state=None,  # Not in combat yet
                world_state=world_state["world_state"],
                world_blueprint=campaign["world_blueprint"]
            )
            
            logger.info(f"🎯 Target resolution: type={target_resolution['target_type']}, name={target_resolution.get('target_name')}")
            
            # Check if clarification is needed
            if target_resolution['status'] == 'needs_clarification':
                logger.info("❓ Target clarification needed")
                # FILTER TARGET CLARIFICATION
                from services.narration_filter import NarrationFilter
                clarification = NarrationFilter.apply_filter(target_resolution['clarification_reason'], max_sentences=3, context="target_clarification")
                
                return api_success({
                    "narration": clarification,
                    "entity_mentions": [],
                    "options": [],
                    "world_state_update": {},
                    "player_updates": {}
                })
            
            # If target found, check for plot armor (NPC only)
            if target_resolution['target_type'] == 'npc':
                from services.combat_engine_service import check_and_apply_plot_armor
                
                plot_armor_result = check_and_apply_plot_armor(
                    npc_data=target_resolution['target'],
                    world_blueprint=campaign["world_blueprint"],
                    world_state=world_state["world_state"],
                    character_state=char_doc["character_state"],
                    action_type="attack"
                )
                
                if plot_armor_result['status'] == 'blocked':
                    logger.info(f"🛡️ Plot armor BLOCKED attack on {target_resolution['target_name']}")
                    
                    # P1 FIX: Track consequence with violence flag
                    from services.consequence_service import ConsequenceEscalation
                    
                    escalation_result = ConsequenceEscalation.track_transgression(
                        world_state=world_state["world_state"],
                        target_id=target_resolution.get('target_id', 'village_elder'),
                        action=f"assault on {target_resolution['target_name']}",
                        severity="minor",
                        is_violent=True
                    )
                    
                    # P1 FIX: Check if combat should be triggered from escalation
                    if escalation_result and escalation_result.get('should_trigger_combat', False):
                        logger.error("🔥 ESCALATION TRIGGERED COMBAT after repeated assault")
                        
                        # Force combat initiation
                        from models.game_models import CombatDoc, CombatState
                        
                        # Convert NPC to enemy and start combat
                        combat_id = str(uuid.uuid4())
                        character_level = char_doc["character_state"].get("level", 1)
                        
                        combat_state = CombatState(
                            combat_id=combat_id,
                            campaign_id=campaign_id,
                            character_id=character_id,
                            active=True,
                            round=1,
                            turn_order=["player", "guards"],
                            current_turn="player",
                            enemies=[{
                                "id": "town_guard_1",
                                "name": "Town Guard",
                                "hp": 11,
                                "max_hp": 11,
                                "ac": 16,
                                "attack_bonus": 3,
                                "damage_dice": "1d6+1",
                                "challenge_rating": 1/8
                            }],
                            combat_log=[],
                            combat_over=False
                        )
                        
                        # Create CombatDoc
                        combat_doc_new = CombatDoc(
                            combat_id=combat_id,
                            campaign_id=campaign_id,
                            character_id=character_id,
                            combat_state=combat_state.dict(),
                            created_at=datetime.now(timezone.utc)
                        )
                        
                        db = get_db()
                        await db.combats.insert_one(combat_doc_new.dict())
                        logger.info("⚔️ Combat initiated with guards (escalation-triggered)")
                        
                        # Update world state with escalation
                        updated_world = {**world_state["world_state"], **plot_armor_result.get('world_state_update', {})}
                        updated_world['guard_alert'] = True
                        updated_world['guards_hostile'] = True
                        await update_world_state(campaign_id, updated_world)
                        
                        # v4.1 UNIFIED SPEC: No options field - narration ends with open prompts
                        return {
                            "narration": escalation_result['narrative_hint'] + "\n\n" + plot_armor_result['narrative_hint'] + "\n\nWhat do you do?",
                            "check_request": None,
                            "world_state_update": updated_world,
                            "starts_combat": True
                        }
                    
                    # Apply consequences to world state and character
                    if plot_armor_result['world_state_update']:
                        updated_world = {**world_state["world_state"], **plot_armor_result['world_state_update']}
                        await update_world_state(campaign_id, updated_world)
                    
                    if plot_armor_result['character_state_update']:
                        updated_char = {**char_doc["character_state"], **plot_armor_result['character_state_update']}
                        await update_character_state(campaign_id, character_id, updated_char)
                    
                    # v4.1 UNIFIED SPEC: No options field - narration ends with open prompts
                    return {
                        "narration": plot_armor_result['narrative_hint'] + "\n\nWhat do you do?",
                        "check_request": None,
                        "world_state_update": plot_armor_result['world_state_update'],
                        "player_updates": {}
                    }
                
                # If forced non-lethal, continue with combat but mark it
                force_non_lethal = plot_armor_result['status'] == 'forced_non_lethal'
                logger.info(f"⚔️ Combat allowed with {target_resolution['target_name']}, force_non_lethal={force_non_lethal}")
            
            # Target resolved, no plot armor - initiate combat with mechanical resolution
            if target_resolution['target_type'] in ['enemy', 'npc']:
                # Initialize force_non_lethal flag (from plot armor check above)
                force_non_lethal = False  # Default
                
                logger.info(f"⚔️ Initiating combat with {target_resolution['target_name']}")
                from services.combat_engine_service import (
                    start_combat_with_target,
                    process_player_attack,
                    process_enemy_turns
                )
                from models.game_models import CombatDoc, CombatState
                
                # Start combat
                character_level = char_doc["character_state"].get("level", 1)
                combat_state_dict = start_combat_with_target(
                    target_resolution=target_resolution,
                    character_state=char_doc["character_state"],
                    world_blueprint=campaign["world_blueprint"],
                    character_level=character_level
                )
                
                # Process player's first attack mechanically
                target_id = target_resolution['target_id']
                attack_result = process_player_attack(
                    target_id=target_id,
                    character_state=char_doc["character_state"],
                    combat_state=combat_state_dict,
                    force_non_lethal=force_non_lethal
                )
                
                # Update combat state with attack results
                combat_state_dict.update(attack_result['combat_state_update'])
                
                # Process enemy turns if combat continues
                enemy_result = {"enemy_actions": [], "total_damage_to_player": 0}
                if not attack_result['combat_over']:
                    enemy_result = process_enemy_turns(
                        character_state=char_doc["character_state"],
                        combat_state=combat_state_dict
                    )
                    
                    # Update character HP
                    if enemy_result['character_state_update']:
                        updated_char = {**char_doc["character_state"], **enemy_result['character_state_update']}
                        await update_character_state(campaign_id, character_id, updated_char)
                    
                    # Check if player defeated
                    if enemy_result.get('combat_over'):
                        combat_state_dict['combat_over'] = True
                        combat_state_dict['outcome'] = enemy_result.get('outcome')
                
                # Create mechanical summary for DM to narrate
                mechanical_summary = {
                    "player_attack": attack_result['mechanical_summary'],
                    "enemy_turns": enemy_result.get('enemy_actions', []),
                    "total_damage_to_player": enemy_result.get('total_damage_to_player', 0),
                    "combat_over": attack_result['combat_over'] or enemy_result.get('combat_over', False),
                    "outcome": combat_state_dict.get('outcome')
                }
                
                # Store combat in DB
                combat_doc_new = CombatDoc(
                    campaign_id=campaign_id,
                    character_id=character_id,
                    combat_state=CombatState(**combat_state_dict),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                combat_dict = combat_doc_new.dict()
                combat_dict['created_at'] = combat_dict['created_at'].isoformat()
                combat_dict['updated_at'] = combat_dict['updated_at'].isoformat()
                
                await db.combats.insert_one(combat_dict)
                logger.info("✅ Combat state saved to database")
                
                # Generate narration from mechanical results
                narration = generate_combat_narration_from_mechanical(mechanical_summary, char_doc["character_state"])
                
                # Handle combat end
                player_updates = {}
                if mechanical_summary['combat_over']:
                    if mechanical_summary['outcome'] == 'victory':
                        # Award XP
                        xp_gained = attack_result.get('xp_gained', 0)
                        if xp_gained > 0:
                            from services.progression_service import apply_xp_gain
                            updated_char_with_xp, level_up_events = apply_xp_gain(
                                char_doc["character_state"],
                                xp_gained
                            )
                            await update_character_state(campaign_id, character_id, updated_char_with_xp)
                            player_updates["xp_gained"] = xp_gained
                            player_updates["level_up_events"] = level_up_events
                    
                    elif mechanical_summary['outcome'] == 'player_defeated':
                        # Handle defeat
                        current_char = char_doc["character_state"]
                        current_char["injury_count"] = current_char.get("injury_count", 0) + 1
                        max_hp = current_char.get("max_hp", 10)
                        current_char["hp"] = max(1, int(max_hp * 0.5))
                        
                        await update_character_state(campaign_id, character_id, current_char)
                        player_updates["defeat_handled"] = True
                        player_updates["injury_count"] = current_char["injury_count"]
                        player_updates["hp_restored"] = current_char["hp"]
                
                return {
                    "narration": narration,
                    "options": ["Continue"] if mechanical_summary['combat_over'] else ["Attack again", "Defend", "Try to flee"],
                    "combat_started": not mechanical_summary['combat_over'],
                    "combat_over": mechanical_summary['combat_over'],
                    "outcome": mechanical_summary.get('outcome'),
                    "world_state_update": {},
                    "player_updates": player_updates
                }
        
        if is_combat_active:
            # Route to COMBAT ENGINE with Phase 1 mechanical resolution
            logger.info("⚔️ Combat active - routing to COMBAT ENGINE")
            from services.combat_engine_service import process_player_attack, process_enemy_turns
            from services.target_resolver import resolve_target
            from models.normalized_entities import normalize_enemy_list
            
            combat_state = combat_doc["combat_state"]
            
            # Normalize enemies to ensure combat stats are always present
            if "enemies" in combat_state and combat_state["enemies"]:
                combat_state["enemies"] = normalize_enemy_list(combat_state["enemies"])
                logger.info(f"✅ Normalized {len(combat_state['enemies'])} enemies for combat")
            
            # Phase 1: Resolve target in combat
            target_resolution = resolve_target(
                player_action=player_action,
                client_target_id=client_target_id,
                combat_state=combat_state,
                world_state=world_state["world_state"],
                world_blueprint=campaign["world_blueprint"]
            )
            
            # Check if clarification needed
            if target_resolution['status'] == 'needs_clarification':
                # FILTER TARGET CLARIFICATION
                from services.narration_filter import NarrationFilter
                clarification = NarrationFilter.apply_filter(target_resolution['clarification_reason'], max_sentences=3, context="target_clarification")
                
                # v4.1 UNIFIED SPEC: No options field - narration ends with open prompts
                return api_success({
                    "narration": clarification + "\n\nWhat do you do?",
                    "entity_mentions": [],
                    "combat_active": True,
                    "world_state_update": {},
                    "player_updates": {}
                })
            
            # Process player attack mechanically
            attack_result = process_player_attack(
                target_id=target_resolution['target_id'],
                character_state=char_doc["character_state"],
                combat_state=combat_state
            )
            
            if not attack_result['success']:
                # v4.1 UNIFIED SPEC: No options field - narration ends with open prompts
                return {
                    "narration": attack_result['mechanical_summary'].get('error', 'Unable to process attack') + "\n\nWhat do you do?",
                    "combat_active": True,
                    "world_state_update": {},
                    "player_updates": {}
                }
            
            # Update combat state
            combat_state.update(attack_result['combat_state_update'])
            
            # Process enemy turns if combat continues
            enemy_result = {"enemy_actions": [], "total_damage_to_player": 0}
            if not attack_result['combat_over']:
                enemy_result = process_enemy_turns(
                    character_state=char_doc["character_state"],
                    combat_state=combat_state
                )
                
                # Update character HP
                if enemy_result['character_state_update']:
                    updated_char = {**char_doc["character_state"], **enemy_result['character_state_update']}
                    await update_character_state(campaign_id, character_id, updated_char)
                
                # Check if player defeated
                if enemy_result.get('combat_over'):
                    combat_state['combat_over'] = True
                    combat_state['outcome'] = enemy_result.get('outcome')
            
            # Generate mechanical summary
            mechanical_summary = {
                "player_attack": attack_result['mechanical_summary'],
                "enemy_turns": enemy_result.get('enemy_actions', []),
                "total_damage_to_player": enemy_result.get('total_damage_to_player', 0),
                "combat_over": attack_result['combat_over'] or enemy_result.get('combat_over', False),
                "outcome": combat_state.get('outcome')
            }
            
            # Generate narration
            narration = generate_combat_narration_from_mechanical(mechanical_summary, char_doc["character_state"])
            
            combat_result = {
                "narration": narration,
                "combat_state_update": combat_state,
                "character_state_update": enemy_result.get('character_state_update', {}),
                "combat_over": mechanical_summary['combat_over'],
                "outcome": mechanical_summary.get('outcome'),
                "xp_gained": attack_result.get('xp_gained', 0)
            }
            
            # Update combat state in DB
            db = get_db()
            await db.combats.update_one(
                {"campaign_id": campaign_id, "character_id": character_id},
                {
                    "$set": {
                        "combat_state": combat_result["combat_state_update"],
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            # Generate options
            options = generate_combat_options(combat_result["combat_state_update"])
            
            # Check if combat ended
            if combat_result["combat_over"]:
                logger.info(f"⚔️ Combat ended: {combat_result['outcome']}")
                
                # Mark combat as over in DB
                await db.combats.update_one(
                    {"campaign_id": campaign_id, "character_id": character_id},
                    {"$set": {"combat_state.combat_over": True}}
                )
                
                # P3: Handle different outcomes
                player_updates = {}
                level_up_events = []
                world_state_update = {}
                
                if combat_result["outcome"] == "victory":
                    # Clear enemies from active NPCs
                    active_npcs = world_state["world_state"].get("active_npcs", [])
                    enemy_names = [e["name"] for e in combat_result["combat_state_update"]["enemies"]]
                    world_state_update["active_npcs"] = [n for n in active_npcs if n not in enemy_names]
                    
                    # P3: Apply XP gain and level-ups
                    xp_gained = combat_result.get("xp_gained", 0)
                    if xp_gained > 0:
                        from services.progression_service import apply_xp_gain
                        updated_char_with_xp, level_up_events = apply_xp_gain(
                            char_doc["character_state"],
                            xp_gained
                        )
                        # Update character in DB
                        await update_character_state(campaign_id, character_id, updated_char_with_xp)
                        player_updates["xp_gained"] = xp_gained
                        player_updates["level_up_events"] = level_up_events
                        logger.info(f"💰 Awarded {xp_gained} XP, level-ups: {level_up_events}")
                
                elif combat_result["outcome"] == "player_defeated":
                    # P3: Handle player defeat
                    logger.warning("☠️ Player defeated in combat")
                    
                    # Apply defeat consequences
                    current_char = char_doc["character_state"]
                    current_char["injury_count"] = current_char.get("injury_count", 0) + 1
                    
                    # Restore HP to 50% of max
                    max_hp = current_char.get("max_hp", 10)
                    current_char["hp"] = max(1, int(max_hp * 0.5))
                    
                    # P3.5: XP penalty on defeat (15% of current level progress, min 5 XP)
                    level_xp = current_char.get("current_xp", 0)
                    xp_penalty = int(level_xp * 0.15)
                    xp_penalty = max(5, xp_penalty)  # Minimum sting
                    old_xp = level_xp
                    current_char["current_xp"] = max(0, level_xp - xp_penalty)
                    logger.warning(f"💀 XP penalty on defeat: {old_xp} -> {current_char['current_xp']} (-{xp_penalty})")
                    
                    # Update character in DB
                    await update_character_state(campaign_id, character_id, current_char)
                    
                    player_updates["defeat_handled"] = True
                    player_updates["injury_count"] = current_char["injury_count"]
                    player_updates["hp_restored"] = current_char["hp"]
                    player_updates["xp_penalty"] = xp_penalty  # P3.5: Show in UI
                
                # v4.1 UNIFIED SPEC: No options field - narration ends with open prompts
                return {
                    "narration": combat_result["narration"],
                    "combat_over": True,
                    "outcome": combat_result["outcome"],
                    "world_state_update": world_state_update,
                    "player_updates": player_updates  # P3
                }
            
            # v4.1 UNIFIED SPEC: No options field - narration ends with open prompts
            return {
                "narration": combat_result["narration"],
                "combat_active": True,
                "world_state_update": {},
                "player_updates": {}  # P3: No updates mid-combat
            }
        
        # ACTION MODE pipeline
        logger.info("🏷️ Running INTENT TAGGER...")
        intent_flags = await run_intent_tagger(player_action, char_doc["character_state"])
        logger.info(f"   Intent: {intent_flags}")
        
        # DC CALCULATION: Use new DC taxonomy system
        suggested_dc = None
        dc_band = None
        dc_reasoning = None
        suggested_ability = None
        suggested_skill = None
        
        if intent_flags.get("needs_check"):
            from services.dc_rules import DCHelper
            try:
                # Determine action type from player action
                action_type = DCHelper.get_action_type_from_intent(player_action, intent_flags)
                
                # Get environmental conditions
                world = world_state.get("world_state", {})
                environment = []
                if world.get("weather") in ["rain", "heavy_rain", "fog"]:
                    environment.append(world.get("weather"))
                if world.get("time_of_day") == "night":
                    environment.append("darkness")
                
                # Determine risk level
                risk_level = "normal_risk"
                if world.get("guards_hostile") or world.get("combat_active"):
                    risk_level = "high_risk"
                
                # Calculate DC using taxonomy
                suggested_dc, dc_reasoning, dc_band = DCHelper.calculate_dc(
                    action_type=action_type,
                    risk_level=risk_level,
                    environment=environment,
                    character_level=char_doc["character_state"].get("level", 1)
                )
                
                # Get suggested ability and skill
                suggested_ability, suggested_skill = DCHelper.get_suggested_ability_and_skill(action_type)
                
                logger.info(f"📊 DC Calculation: {dc_reasoning}")
                
                # Add to intent_flags for DM prompt
                intent_flags["suggested_dc"] = suggested_dc
                intent_flags["dc_band"] = dc_band.value
                intent_flags["dc_reasoning"] = dc_reasoning
                intent_flags["suggested_ability"] = suggested_ability
                intent_flags["suggested_skill"] = suggested_skill
                intent_flags["action_type"] = action_type
                
            except Exception as e:
                logger.error(f"❌ DC calculation failed: {e}", exc_info=True)
                suggested_dc = 15  # Fallback to medium difficulty
                dc_band = "moderate"
                intent_flags["suggested_dc"] = suggested_dc
                intent_flags["dc_band"] = "moderate"
        
        logger.info("🎲 Running DUNGEON FORGE...")
        dm_response = await run_dungeon_forge(
            player_action=player_action,
            character_state=char_doc["character_state"],
            world_blueprint=campaign["world_blueprint"],
            world_state=world_state["world_state"],
            intent_flags=intent_flags,
            check_result=check_result,
            pacing_instructions=pacing_instructions,
            auto_revealed_info=auto_revealed_info,
            condition_explanations=condition_explanations,
            session_mode=session_mode,
            improvisation_result=improvisation_result,
            npc_personalities=npc_personalities_data,
            active_tailing_quest=active_tailing_quest
        )
        logger.info(f"   DM Response: narration length={len(dm_response.get('narration', ''))}")
        
        # STORY CONSISTENCY LAYER v6.0 (validate and correct DM output)
        from config.story_consistency_config import (
            USE_STORY_CONSISTENCY_LAYER,
            CONSISTENCY_AUTO_CORRECT,
            CONSISTENCY_HARD_BLOCK
        )
        
        if USE_STORY_CONSISTENCY_LAYER:
            logger.info("🔍 Running STORY CONSISTENCY LAYER v6.0...")
            from services.story_consistency_agent import validate_dm_output
            
            # Build dm_draft from DM output
            dm_draft = {
                "narration": dm_response.get("narration", ""),
                "scene_mode": dm_response.get("scene_mode", session_mode.get("mode", "exploration") if session_mode else "exploration"),
                "requested_check": dm_response.get("requested_check"),
                "world_state_update": dm_response.get("world_state_update", {}),
                "player_updates": dm_response.get("player_updates", {}),
                "notes": dm_response.get("scene_status", {})
            }
            
            # Prepare canonical data structures
            quest_state = world_state["world_state"].get("quests", {})
            npc_registry = world_state["world_state"].get("npcs", {})
            story_threads = world_state["world_state"].get("story_threads", [])
            scene_history = world_state["world_state"].get("recent_scenes", [])
            
            mechanical_context = {
                "player_state": char_doc["character_state"],
                "check_result": check_result,
                "combat_state": world_state["world_state"].get("combat_state")
            }
            
            # Validate DM output
            validation = await validate_dm_output(
                dm_draft=dm_draft,
                world_blueprint=campaign["world_blueprint"],
                world_state=world_state["world_state"],
                quest_state=quest_state,
                npc_registry=npc_registry,
                story_threads=story_threads,
                scene_history=scene_history,
                mechanical_context=mechanical_context
            )
            
            decision = validation.get("decision", "approve")
            logger.info(f"   Story Consistency Decision: {decision}")
            
            if decision == "approve":
                corrected = validation.get("corrected_narration")
                if corrected and CONSISTENCY_AUTO_CORRECT:
                    dm_response["narration"] = corrected
                    logger.info("   Applied minimal consistency corrections")
                elif corrected:
                    logger.info("   Consistency corrections available but auto-correct disabled")
            
            elif decision == "revise_required":
                corrected = validation.get("corrected_narration")
                if corrected and CONSISTENCY_AUTO_CORRECT:
                    dm_response["narration"] = corrected
                    changes = validation.get("narration_changes_summary", [])
                    logger.warning(f"⚠️ Story consistency revisions applied: {changes}")
                else:
                    logger.warning(f"⚠️ Story consistency issues detected but auto-correct disabled")
            
            elif decision == "hard_block":
                issues = validation.get("issues", [])
                logger.error(f"❌ STORY CONSISTENCY HARD BLOCK: {len(issues)} critical issues")
                for issue in issues:
                    logger.error(f"   [{issue['severity']}] {issue['type']}: {issue['message']}")
                
                if CONSISTENCY_HARD_BLOCK:
                    # Replace narration with safe fallback
                    dm_response["narration"] = "The scene becomes unclear for a moment. What do you do?"
                    logger.error("   DM output replaced with safe fallback")
                else:
                    logger.warning("   Hard block disabled - using original DM output with warnings")
            
            # Log all issues for debugging
            if validation.get("issues"):
                for issue in validation["issues"]:
                    if issue["severity"] == "error":
                        logger.error(f"   Consistency Issue: [{issue['type']}] {issue['message']}")
                    elif issue["severity"] == "warning":
                        logger.warning(f"   Consistency Warning: [{issue['type']}] {issue['message']}")
        
        # LORE CHECKER (P2.5: soft mode by default)
        logger.info("🔍 Running LORE CHECKER...")
        from services.lore_checker_service import check_lore_consistency
        
        lore_check_result = check_lore_consistency(
            narration=dm_response.get("narration", ""),
            world_blueprint=campaign["world_blueprint"],
            world_state=world_state["world_state"],
            auto_correct=False  # P2.5: soft mode - warnings only, no auto-corrections
        )
        
        # In soft mode, corrected_narration == original (no changes made)
        # We still use it for consistency with the API
        if lore_check_result["corrections_made"] > 0:
            dm_response["narration"] = lore_check_result["corrected_narration"]
            logger.info(f"✅ LORE CHECKER: Applied {lore_check_result['corrections_made']} corrections")
        
        # Log issues as warnings (soft mode doesn't block responses)
        if lore_check_result["issues"]:
            logger.warning(f"⚠️ LORE CHECKER: Found {len(lore_check_result['issues'])} potential issues (soft mode - not blocking)")
        else:
            logger.info("✅ LORE CHECKER: No issues detected")
        
        # APPLY HUMAN DM FILTER v4.1 - Enforce context-based sentence limits and remove AI phrases
        logger.info("🎭 Applying Human DM Filter v4.1...")
        from services.narration_filter import NarrationFilter
        original_narration = dm_response.get("narration", "")
        original_sentence_count = NarrationFilter.count_sentences(original_narration)
        logger.info(f"📏 Original narration: {original_sentence_count} sentences, {len(original_narration)} chars")
        
        # Get the scene mode from DM response to apply correct sentence limit
        scene_mode = dm_response.get("scene_mode", "exploration")
        filtered_narration = NarrationFilter.apply_filter(original_narration, context=scene_mode)
        final_sentence_count = NarrationFilter.count_sentences(filtered_narration)
        
        dm_response["narration"] = filtered_narration
        logger.info(f"✅ Narration filtered: {final_sentence_count} sentences, {len(filtered_narration)} chars")
        
        # Get expected limit for this context
        expected_limit = NarrationFilter.SENTENCE_LIMITS.get(scene_mode, 10)
        if original_sentence_count > expected_limit:
            logger.warning(f"⚠️ LLM VIOLATED {expected_limit}-SENTENCE LIMIT for {scene_mode}: Generated {original_sentence_count}, truncated to {final_sentence_count}")
        
        # WORLD MUTATOR (apply state changes)
        logger.info("🌍 Running WORLD MUTATOR...")
        world_state_update = dm_response.get("world_state_update", {})
        
        if world_state_update:
            updated_state = {**world_state["world_state"], **world_state_update}
            await update_world_state(campaign_id, updated_state)
            logger.info(f"   World state updated: {list(world_state_update.keys())}")
        
        # TAILING QUEST: Process information and detection
        if active_tailing_quest and quest_updates.get("information_discovered"):
            quest_id = active_tailing_quest["quest_id"]
            info = quest_updates["information_discovered"]
            detection_gain = quest_updates.get("detection_level", 0)
            
            # Update quest in world state
            if "active_quests" not in world_state["world_state"]:
                world_state["world_state"]["active_quests"] = {}
            
            if quest_id in world_state["world_state"]["active_quests"]:
                quest = world_state["world_state"]["active_quests"][quest_id]
                quest.setdefault("information_gathered", []).append({
                    "info": info,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                quest["detection_level"] = min(100, quest.get("detection_level", 0) + detection_gain)
                quest["events_completed"] = quest.get("events_completed", 0) + 1
                
                # Check completion
                if quest["detection_level"] >= 100:
                    quest["status"] = "failed"
                    player_updates["quest_failed"] = "Detected by target"
                elif quest["events_completed"] >= 3:
                    quest["status"] = "completed"
                    player_updates["quest_completed"] = quest["title"]
                    player_updates["xp_gained"] = quest["rewards"]["xp"]
                
                logger.info(f"🕵️ Tailing quest updated: {info[:50]}..., detection: {quest['detection_level']}")
        
        # P3.5: Handle quest updates from DUNGEON FORGE
        quest_updates = dm_response.get("quest_updates", {})
        if quest_updates and any([
            quest_updates.get("new_quests"),
            quest_updates.get("progress_events"),
            quest_updates.get("completed_quest_ids")
        ]):
            logger.info("📜 Processing quest updates from DUNGEON FORGE...")
            from services.quest_service import (
                add_quest_to_world_state,
                update_quest_progress,
                complete_quest,
                create_simple_quest
            )
            
            # Fetch current world state with quests
            current_world = world_state["world_state"]
            
            # Add new quests
            for quest_data in quest_updates.get("new_quests", []):
                logger.info(f"📜 Adding new quest: {quest_data.get('name')}")
                current_world = add_quest_to_world_state(current_world, quest_data)
            
            # Update quest progress
            for progress_event in quest_updates.get("progress_events", []):
                quest_id = progress_event.get("quest_id")
                obj_idx = progress_event.get("objective_index", 0)
                delta = progress_event.get("progress_delta", 1)
                
                # Find quest and update
                for quest in current_world.get("quests", []):
                    if quest["quest_id"] == quest_id and len(quest["objectives"]) > obj_idx:
                        quest["objectives"][obj_idx]["progress"] += delta
                        quest["objectives"][obj_idx]["progress"] = min(
                            quest["objectives"][obj_idx]["progress"],
                            quest["objectives"][obj_idx].get("count", 1)
                        )
                        logger.info(f"📈 Quest '{quest['name']}' progress: obj {obj_idx} -> {quest['objectives'][obj_idx]['progress']}")
                        
                        # Check if all objectives complete
                        if all(obj["progress"] >= obj.get("count", 1) for obj in quest["objectives"]):
                            quest["status"] = "completed"
                            logger.info(f"✅ Quest '{quest['name']}' completed!")
            
            # Handle completed quests
            for quest_id in quest_updates.get("completed_quest_ids", []):
                quest_xp = complete_quest(current_world, quest_id)
                logger.info(f"🎊 Quest completed, awarding {quest_xp} XP")
            
            # Save updated world state with quests
            await update_world_state(campaign_id, current_world)
        
        # P3.5: Handle XP rewards (quest completion + non-combat)
        player_updates = dm_response.get("player_updates", {})
        level_up_events = []
        
        # P3.5: Non-combat XP from DUNGEON FORGE
        xp_reward = dm_response.get("xp_reward") or {}  # Handle None case
        xp_from_action = xp_reward.get("amount", 0)
        xp_reason = xp_reward.get("reason", "")
        
        # Legacy support: also check player_updates.xp_gained
        xp_from_legacy = player_updates.get("xp_gained", 0)
        
        total_xp = xp_from_action + xp_from_legacy
        
        if total_xp > 0:
            from services.progression_service import apply_xp_gain
            updated_char_with_xp, level_up_events = apply_xp_gain(
                char_doc["character_state"],
                total_xp
            )
            await update_character_state(campaign_id, character_id, updated_char_with_xp)
            player_updates["xp_gained"] = total_xp
            player_updates["xp_reason"] = xp_reason if xp_reason else "Action reward"
            player_updates["level_up_events"] = level_up_events
            logger.info(f"💰 Non-combat XP awarded: {total_xp} XP ({xp_reason}), level-ups: {level_up_events}")
        
        # Handle gold, item rewards, and item usage from player_updates
        gold_gained = player_updates.get("gold_gained", 0)
        gold_spent = player_updates.get("gold_spent", 0)
        items_gained = player_updates.get("items_gained", [])
        items_used = player_updates.get("items_used", [])
        items_removed = player_updates.get("items_removed", [])
        
        if gold_gained > 0 or gold_spent > 0 or items_gained or items_used or items_removed:
            current_char = char_doc["character_state"]
            
            # Update gold
            if gold_gained > 0:
                current_gold = current_char.get("gold", 0)
                current_char["gold"] = current_gold + gold_gained
                logger.info(f"💰 Gold gained: {gold_gained} (total: {current_char['gold']})")
            
            if gold_spent > 0:
                current_gold = current_char.get("gold", 0)
                new_gold = max(0, current_gold - gold_spent)
                current_char["gold"] = new_gold
                logger.info(f"💸 Gold spent: {gold_spent} (remaining: {current_char['gold']})")
            
            # Update inventory - add items
            if items_gained:
                current_inventory = current_char.get("inventory", [])
                current_inventory.extend(items_gained)
                current_char["inventory"] = current_inventory
                logger.info(f"🎒 Items gained: {items_gained}")
            
            # Update inventory - remove used/consumed items
            if items_used or items_removed:
                current_inventory = current_char.get("inventory", [])
                for item in (items_used + items_removed):
                    if item in current_inventory:
                        current_inventory.remove(item)
                        logger.info(f"🗑️ Item removed: {item}")
                current_char["inventory"] = current_inventory
            
            # Save updated character
            await update_character_state(campaign_id, character_id, current_char)
        
        if dm_response.get("starts_combat", False):
            logger.info("⚔️ Combat triggered - initializing COMBAT ENGINE")
            from services.combat_engine_service import start_combat, generate_combat_options
            from services.enemy_sourcing_service import select_enemies_for_location
            from models.normalized_entities import normalize_character, normalize_enemy_list
            
            # Build enemy templates from world context (P2.5: world-aware enemy sourcing)
            character_level = char_doc["character_state"].get("level", 1)
            enemy_templates = select_enemies_for_location(
                world_blueprint=campaign["world_blueprint"],
                world_state=world_state["world_state"],
                character_level=character_level
            )
            
            # Normalize enemies before combat starts
            normalized_enemies = normalize_enemy_list(enemy_templates)
            logger.info(f"✅ Normalized {len(normalized_enemies)} enemies for combat initialization")
            
            # Start combat
            from models.game_models import CombatDoc, CombatState
            combat_state_dict = start_combat(
                character_state=char_doc["character_state"],
                enemy_templates=normalized_enemies,
                campaign_id=campaign_id,
                character_id=character_id
            )
            
            # Create CombatDoc
            combat_doc_new = CombatDoc(
                campaign_id=campaign_id,
                character_id=character_id,
                combat_state=CombatState(**combat_state_dict),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            combat_dict = combat_doc_new.dict()
            combat_dict['created_at'] = combat_dict['created_at'].isoformat()
            combat_dict['updated_at'] = combat_dict['updated_at'].isoformat()
            
            # Store in DB
            db = get_db()
            await db.combats.insert_one(combat_dict)
            
            # Generate combat options
            options = generate_combat_options(combat_state_dict)
            
            # Extract entity mentions from narration (combat start)
            combat_narration = dm_response.get("narration", "") + "\n\n**Combat begins!**"
            
            # FILTER COMBAT NARRATION using mode-aware limit
            from services.narration_filter import NarrationFilter
            combat_limits = MODE_LIMITS.get("combat", {"min": 4, "max": 8})
            combat_narration = NarrationFilter.apply_filter(combat_narration, max_sentences=combat_limits["max"], context="combat_start")
            
            entity_index = build_entity_index_from_world_blueprint(
                campaign["world_blueprint"],
                world_state["world_state"]
            )
            entity_mentions = extract_entity_mentions(combat_narration, entity_index)
            
            # v4.1 UNIFIED SPEC: No options field - narration ends with open prompts
            return api_success({
                "narration": combat_narration,
                "entity_mentions": entity_mentions,
                "combat_started": True,
                "world_state_update": world_state_update,
                "player_updates": {}
            })
        
        # Extract entity mentions from narration (normal action)
        # NOTE: Narration was already filtered at line 2715 with scene_mode context
        narration_text = dm_response.get("narration", "")
        
        entity_index = build_entity_index_from_world_blueprint(
            campaign["world_blueprint"],
            world_state["world_state"]
        )
        entity_mentions = extract_entity_mentions(narration_text, entity_index)
        
        logger.info(f"🔗 Extracted {len(entity_mentions)} entity mentions from narration")
        
        # Auto-create KnowledgeFacts for first-time mentions
        if entity_mentions:
            from routers import knowledge as knowledge_router
            existing_facts = await knowledge_router.get_db().knowledge_facts.find({
                "campaign_id": campaign_id
            }, {"entity_id": 1, "entity_type": 1}).to_list(1000)
            
            for mention in entity_mentions:
                # Check if this is the first time player sees this entity
                is_new = not any(
                    f.get("entity_type") == mention["entity_type"] and 
                    f.get("entity_id") == mention["entity_id"]
                    for f in existing_facts
                )
                
                if is_new:
                    # Create introduction fact
                    await knowledge_router.get_db().knowledge_facts.insert_one({
                        "campaign_id": campaign_id,
                        "character_id": character_id,
                        "entity_type": mention["entity_type"],
                        "entity_id": mention["entity_id"],
                        "entity_name": mention["display_text"],
                        "fact_type": "introduction",
                        "fact_text": f"First encountered in narration: '{narration_text[:100]}...'",
                        "revealed_at": datetime.now(timezone.utc),
                        "source": "narration",
                        "metadata": {}
                    })
                    logger.info(f"📚 Created knowledge fact for {mention['entity_type']}: {mention['display_text']}")
        
        # CAMPAIGN LOG: Extract structured knowledge from narration
        # NOTE: This is for ongoing gameplay narration, not arrival scenes
        # Hooks are only generated for arrival/scene descriptions, not action responses
        try:
            from services.campaign_log_extractor import extract_campaign_log_from_scene
            from services.campaign_log_service import CampaignLogService
            
            log_service = CampaignLogService(db)
            current_location = world_state.get("world_state", {}).get("current_location", "unknown")
            
            # Extract structured delta using LLM (no hooks for action narration)
            campaign_log_delta = await extract_campaign_log_from_scene(
                narration=narration_text,
                entity_mentions=entity_mentions,
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                current_location=current_location,
                quest_hooks=None,  # No hooks for action responses
                scene_id=None
            )
            
            # Apply delta to campaign log
            if campaign_log_delta:
                await log_service.apply_delta(campaign_id, campaign_log_delta, character_id)
                logger.info(f"📖 Campaign log updated with {len(campaign_log_delta.locations)} locations, {len(campaign_log_delta.npcs)} NPCs")
        except Exception as e:
            logger.error(f"❌ Campaign log extraction failed: {e}")
            # Don't fail the whole request if log extraction fails
        
        # DC VALIDATION: Ensure check_request has valid DC
        # v3.1 compatibility: DM prompt outputs "requested_check", map to "check_request"
        check_request = dm_response.get("check_request") or dm_response.get("requested_check")
        if check_request:
            # Normalize to check_request for consistency
            if "requested_check" in dm_response and "check_request" not in dm_response:
                dm_response["check_request"] = dm_response.pop("requested_check")
                check_request = dm_response["check_request"]
            # Validate DC is present and within range
            if not check_request.get("dc") or not isinstance(check_request.get("dc"), int):
                # Use suggested_dc as fallback if LLM didn't provide DC
                fallback_dc = suggested_dc if suggested_dc else 15
                check_request["dc"] = fallback_dc
                logger.warning(f"⚠️ DM didn't provide DC, using fallback: {fallback_dc}")
            
            # Clamp DC to valid range (5-30)
            if check_request["dc"] < 5:
                logger.warning(f"⚠️ DC too low ({check_request['dc']}), clamping to 5")
                check_request["dc"] = 5
            elif check_request["dc"] > 30:
                logger.warning(f"⚠️ DC too high ({check_request['dc']}), clamping to 30")
                check_request["dc"] = 30
            
            logger.info(f"✅ Final DC for check: {check_request['dc']}")
        
        # INJECT GENERATED SCENE: If location changed, prepend the scene description
        if world_state.get("_generated_scene"):
            generated_scene = world_state["_generated_scene"]
            # FILTER SCENE DESCRIPTION using mode-aware limit
            current_mode = session_mode.get("mode", "exploration") if session_mode else "exploration"
            mode_limits = MODE_LIMITS.get(current_mode, {"min": 4, "max": 8})
            generated_scene = NarrationFilter.apply_filter(generated_scene, max_sentences=mode_limits["max"], context=f"scene_description_{current_mode}")
            # Prepend scene to narration
            narration_text = f"{generated_scene}\n\n{narration_text}"
            logger.info(f"✨ Injected filtered scene into narration")
            
            # Add location to world_state_update
            world_state_update["current_location"] = world_state["world_state"]["current_location"]
            
            # After prepending scene, re-apply final filter to combined narration
            narration_text = NarrationFilter.apply_filter(narration_text, max_sentences=mode_limits["max"], context=f"final_combined_{current_mode}")
        
        # v4.1 UNIFIED SPEC: No options field - narration ends with open prompts
        return api_success({
            "narration": narration_text,
            "entity_mentions": entity_mentions,
            "check_request": check_request,
            "world_state_update": world_state_update,
            "player_updates": player_updates
        })
        
    except Exception as e:
        logger.error(f"❌ Action processing failed: {e}", exc_info=True)
        return api_error("internal_error", f"Action processing failed: {str(e)}", status_code=500)
