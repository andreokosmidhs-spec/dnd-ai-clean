"""Voice casting API router.

POST /api/voices/assign/{campaignId}/{npcId}
  — match voice tags → assign permanent voice → store in world_state

POST /api/voices/speak/{campaignId}/{npcId}
  — generate WAV for a line with optional emotion modifier (cached)

GET  /api/voices/registry
  — list all voices with tags (for debug / DM tooling)

GET  /api/voices/cache/stats
  — in-memory cache statistics

DELETE /api/voices/cache/{npcId}
  — evict one NPC's audio from cache (or all if npcId == "_all")
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voices", tags=["voice_casting"])


# ── Helpers to load / save campaign ─────────────────────────────────────────

async def _get_campaign(campaign_id: str) -> dict:
    """Load campaign document from DB or raise 404."""
    from server import db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    doc = await db["campaigns"].find_one({"_id": campaign_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    return doc


async def _save_world_state(campaign_id: str, world_state: dict) -> None:
    from server import db
    if db is None:
        return
    await db["campaigns"].update_one(
        {"_id": campaign_id},
        {"$set": {"world_state": world_state}},
    )


def _find_npc(campaign: dict, npc_id: str) -> Optional[dict]:
    """Find NPC in world_blueprint.key_npcs by id or name slug."""
    blueprint = campaign.get("world_blueprint") or {}
    for npc in blueprint.get("key_npcs", []):
        if npc.get("id") == npc_id or npc.get("name", "").lower().replace(" ", "_") == npc_id:
            return npc
    return None


# ── Request / response models ─────────────────────────────────────────────────

class AssignVoiceRequest(BaseModel):
    voiceTags: list[str] = Field(default_factory=list,
        description="Semantic tags from the AI DM (e.g. ['female','dry','urban','middle_aged'])")
    emotionalStyle: str = Field(default="neutral")
    forceReassign: bool = Field(default=False,
        description="Reassign even if voice already set")


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    emotion: str = Field(default="neutral")
    tier: int = Field(default=1, ge=1, le=3,
        description="Priority tier: 1=realtime, 2=cached bark, 3=skip (ambient)")
    useCache: bool = Field(default=True)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/registry")
async def get_voice_registry():
    """List all available Kokoro voices with tags and emotional support."""
    from services.voice_casting_service import get_registry
    return {"voices": get_registry()}


@router.get("/emotions")
async def get_supported_emotions():
    """List all supported emotional modifiers."""
    from services.voice_casting_service import get_supported_emotions
    return {"emotions": get_supported_emotions()}


@router.post("/assign/{campaign_id}/{npc_id}")
async def assign_voice(campaign_id: str, npc_id: str, req: AssignVoiceRequest):
    """Assign a permanent voice to an NPC based on AI DM voice tags.

    If the NPC already has a voice, skip unless forceReassign=true.
    Stores the result in world_state.npc_voice_profiles[npc_id].
    """
    from services.voice_casting_service import assign_voice_to_npc, match_voice

    campaign = await _get_campaign(campaign_id)
    world_state = campaign.get("world_state") or {}
    voice_profiles = world_state.setdefault("npc_voice_profiles", {})

    if npc_id in voice_profiles and not req.forceReassign:
        return {"voiceProfile": voice_profiles[npc_id], "reassigned": False}

    # Build a minimal NPC dict for the matcher
    npc = _find_npc(campaign, npc_id) or {"id": npc_id}
    npc_with_tags = {
        **npc,
        "voiceProfile": {
            "voiceTags": req.voiceTags or npc.get("voiceProfile", {}).get("voiceTags", []),
            "emotionalStyle": req.emotionalStyle,
        },
    }

    updated_profile = assign_voice_to_npc(npc_with_tags)
    voice_profiles[npc_id] = updated_profile
    world_state["npc_voice_profiles"] = voice_profiles
    await _save_world_state(campaign_id, world_state)

    return {"voiceProfile": updated_profile, "reassigned": True}


@router.post("/speak/{campaign_id}/{npc_id}")
async def speak(campaign_id: str, npc_id: str, req: SpeakRequest):
    """Generate WAV audio for an NPC line with emotional modifiers.

    Returns audio/wav binary. Cached lines are served instantly.
    """
    from services.voice_casting_service import generate_npc_speech, assign_voice_to_npc

    campaign = await _get_campaign(campaign_id)
    world_state = campaign.get("world_state") or {}
    voice_profiles = world_state.get("npc_voice_profiles") or {}

    # Auto-assign if not yet assigned
    if npc_id not in voice_profiles:
        npc = _find_npc(campaign, npc_id) or {"id": npc_id}
        profile = assign_voice_to_npc(npc)
        voice_profiles[npc_id] = profile
        world_state["npc_voice_profiles"] = voice_profiles
        await _save_world_state(campaign_id, world_state)
    else:
        profile = voice_profiles[npc_id]

    if not profile.get("assignedVoice"):
        raise HTTPException(status_code=422, detail="NPC has no assigned voice and could not be auto-assigned")

    audio_bytes = generate_npc_speech(
        npc_id=npc_id,
        text=req.text,
        voice_profile=profile,
        emotion=req.emotion,
        use_cache=req.useCache,
        tier=req.tier,
    )

    if audio_bytes is None:
        raise HTTPException(status_code=503,
            detail="TTS unavailable. Ensure kokoro-onnx models are downloaded.")

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={
            "Content-Disposition": f"inline; filename={npc_id}_{req.emotion}.wav",
            "X-NPC-Voice": profile.get("assignedVoice", ""),
            "X-NPC-Emotion": req.emotion,
            "Cache-Control": "no-cache",
        },
    )


@router.get("/profile/{campaign_id}/{npc_id}")
async def get_voice_profile(campaign_id: str, npc_id: str):
    """Return the stored voice profile for an NPC."""
    campaign = await _get_campaign(campaign_id)
    profiles = (campaign.get("world_state") or {}).get("npc_voice_profiles") or {}
    if npc_id not in profiles:
        raise HTTPException(status_code=404, detail="NPC has no voice profile yet")
    return {"voiceProfile": profiles[npc_id]}


@router.get("/cache/stats")
async def get_cache_stats():
    from services.voice_casting_service import cache_stats
    return cache_stats()


@router.delete("/cache/{npc_id}")
async def clear_cache(npc_id: str):
    from services.voice_casting_service import clear_npc_cache
    target = None if npc_id == "_all" else npc_id
    removed = clear_npc_cache(target)
    return {"cleared": removed}
