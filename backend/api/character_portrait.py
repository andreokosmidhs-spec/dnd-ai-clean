"""Character portrait generation.

Priority chain:
  1. Replicate (REPLICATE_API_TOKEN) via services.art_service
  2. Local SD — A1111_URL or SD_LOCAL=true  (free, runs on your machine)
  3. Gemini image model (EMERGENT_LLM_KEY)
  4. DALL-E 3 (OPENAI_API_KEY)
  5. SVG placeholder avatar — always works, no key needed
"""

import base64
import logging
import os
import re
import uuid
from typing import Optional

from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_ALLOWED_REF_MIME = {"image/jpeg", "image/png", "image/webp"}


# ── Prompt builder (shared by Gemini / DALL-E fallbacks) ──────────────────────

def _parse_data_url(data_url: str):
    if not data_url or not isinstance(data_url, str):
        return None, None
    match = re.match(r"^data:([^;]+);base64,(.+)$", data_url, re.DOTALL)
    if not match:
        return None, None
    mime = match.group(1).strip().lower()
    payload = match.group(2).strip()
    try:
        base64.b64decode(payload[:64], validate=True)
    except Exception:
        return None, None
    return mime, payload


def _build_portrait_prompt(character: dict) -> str:
    identity = character.get("identity") or {}
    race = character.get("race") or {}
    class_ = character.get("class") or {}
    appearance = character.get("appearance") or {}

    name = identity.get("name") or "adventurer"
    sex = identity.get("sex") or ""
    age_category = appearance.get("ageCategory") or ""
    race_name = race.get("key") or "human"
    class_name = class_.get("key") or "adventurer"
    build = appearance.get("build") or ""
    skin = appearance.get("skinTone") or ""
    hair = appearance.get("hairColor") or ""
    hair_style = appearance.get("hairStyle") or ""
    eyes = appearance.get("eyeColor") or ""
    facial_hair = appearance.get("facialHair") or ""
    features = appearance.get("notableFeatures") or []

    descriptor = " ".join(filter(None, [age_category, sex, race_name, class_name])).strip()
    parts = [f"Fantasy D&D character portrait of {name}, a {descriptor}."]

    hair_phrase = " ".join(filter(None, [hair_style, hair])).strip() + " hair" if (hair or hair_style) else ""
    body = ", ".join(filter(None, [
        f"{build} build" if build else "",
        f"{skin} skin" if skin else "",
        hair_phrase,
        f"{eyes} eyes" if eyes else "",
        f"facial hair: {facial_hair}" if facial_hair else "",
    ]))
    if body:
        parts.append(body + ".")
    if features:
        parts.append("Notable features: " + ", ".join(features) + ".")
    parts.append(
        "Head-and-shoulders portrait, dramatic fantasy lighting, painterly oil-on-canvas style, "
        "detailed facial features, plain dark background."
    )
    return " ".join(parts)


# ── SVG placeholder (no API needed) ───────────────────────────────────────────

def _svg_placeholder(character: dict) -> str:
    identity = character.get("identity") or {}
    name = identity.get("name") or "?"
    initial = name[0].upper() if name else "?"
    class_key = ((character.get("class") or {}).get("key") or "fighter").lower()

    colors = {
        "fighter": "#8B4513", "barbarian": "#DC143C", "paladin": "#FFD700",
        "ranger": "#228B22", "rogue": "#4B0082", "monk": "#DEB887",
        "wizard": "#4169E1", "sorcerer": "#8A2BE2", "warlock": "#6B0082",
        "cleric": "#C0C0C0", "druid": "#556B2F", "bard": "#FF69B4",
    }
    bg = colors.get(class_key, "#6B7280")

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">'
        f'<rect width="512" height="512" fill="#1a1a2e"/>'
        f'<circle cx="256" cy="256" r="220" fill="{bg}" opacity="0.15" stroke="{bg}" stroke-width="2"/>'
        f'<circle cx="256" cy="190" r="90" fill="{bg}" opacity="0.55"/>'
        f'<ellipse cx="256" cy="390" rx="130" ry="85" fill="{bg}" opacity="0.4"/>'
        f'<text x="256" y="210" font-family="Georgia,serif" font-size="90" fill="white" '
        f'text-anchor="middle" dominant-baseline="middle" font-weight="bold">{initial}</text>'
        f'</svg>'
    )
    return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"


# ── Gemini fallback ────────────────────────────────────────────────────────────

async def _gemini_portrait(character: dict, api_key: str) -> Optional[str]:
    try:
        from emergentintegrations.llm.chat import FileContent, LlmChat, UserMessage
    except ImportError:
        return None

    _PORTRAIT_MODEL = "gemini-3.1-flash-image-preview"
    prompt = _build_portrait_prompt(character)
    session_id = f"portrait-{character.get('_id') or character.get('id') or uuid.uuid4()}"

    chat = LlmChat(api_key=api_key, session_id=session_id, system_message="You are an expert fantasy illustrator.")
    chat.with_model("gemini", _PORTRAIT_MODEL).with_params(modalities=["image", "text"])

    appearance = character.get("appearance") or {}
    reference_data_url = appearance.get("referenceImage") or ""
    file_contents = []
    if reference_data_url:
        mime, b64 = _parse_data_url(reference_data_url)
        if mime in _ALLOWED_REF_MIME and b64:
            file_contents.append(FileContent(content_type=mime, file_content_base64=b64))
            prompt += (
                " A reference image is provided; use it as visual inspiration for "
                "the character's face, hair, and overall mood — but adapt it to the "
                "described race, class, gear, and fantasy setting."
            )

    msg = UserMessage(text=prompt, file_contents=file_contents or None)
    try:
        _text, images = await chat.send_message_multimodal_response(msg)
    except Exception as exc:
        logger.warning(f"[portrait] Gemini failed: {exc}")
        return None

    if not images:
        return None
    first = images[0]
    mime = first.get("mime_type") or "image/png"
    data = first.get("data")
    return f"data:{mime};base64,{data}" if data else None


# ── DALL-E 3 fallback ─────────────────────────────────────────────────────────

async def _dalle_portrait(character: dict) -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import AsyncOpenAI
        oai = AsyncOpenAI(api_key=api_key)
        prompt = _build_portrait_prompt(character) + " Digital oil painting, high detail, fantasy art style."
        response = await oai.images.generate(
            model="dall-e-3", prompt=prompt, size="1024x1024",
            quality="standard", response_format="b64_json", n=1,
        )
        b64 = response.data[0].b64_json
        return f"data:image/png;base64,{b64}" if b64 else None
    except Exception as exc:
        logger.warning(f"[portrait] DALL-E fallback failed: {exc}")
        return None


# ── Public API ────────────────────────────────────────────────────────────────

async def generate_character_portrait(
    character: dict,
    reference_data_url: Optional[str] = None,
) -> str:
    """Generate a portrait and always return a data URL (never None).

    Pass reference_data_url (the character's stored portraitDataUrl) to
    re-render the same face with updated gear (Replicate only).
    """
    # 1. Replicate (LoRA / consistent-character)
    if os.getenv("REPLICATE_API_TOKEN"):
        try:
            from services.art_service import generate_character_portrait as _replicate_portrait
            result = await _replicate_portrait(character, reference_data_url)
            if result:
                return result
            logger.info("[portrait] Replicate returned nothing, trying next provider")
        except Exception as exc:
            logger.warning(f"[portrait] Replicate error: {exc}")

    # 2. Local SD (A1111 or diffusers — free, no API cost)
    if os.getenv("A1111_URL") or os.getenv("SD_LOCAL"):
        try:
            from services.local_sd_service import generate_portrait as _local_portrait
            prompt = _build_portrait_prompt(character)
            result = await _local_portrait(prompt)
            if result:
                return result
            logger.info("[portrait] Local SD returned nothing, trying next provider")
        except Exception as exc:
            logger.warning(f"[portrait] Local SD error: {exc}")

    # 3. Gemini
    emergent_key = os.getenv("EMERGENT_LLM_KEY")
    if emergent_key:
        result = await _gemini_portrait(character, emergent_key)
        if result:
            return result

    # 4. DALL-E 3
    result = await _dalle_portrait(character)
    if result:
        return result

    # 5. SVG placeholder — always works
    logger.info("[portrait] All providers unavailable, using SVG placeholder")
    return _svg_placeholder(character)


async def persist_portrait(db, character_id: str, data_url: str, in_memory_store: dict) -> bool:
    """Store the portrait data URL on the character document."""
    if db is not None:
        try:
            object_id = ObjectId(character_id)
        except Exception:
            return False
        res = await db["characters_v2"].update_one(
            {"_id": object_id}, {"$set": {"portraitDataUrl": data_url}}
        )
        return res.matched_count > 0

    if character_id in in_memory_store:
        stored = in_memory_store[character_id]
        stored_dict = stored.model_dump(by_alias=True) if hasattr(stored, "model_dump") else dict(stored)
        stored_dict["portraitDataUrl"] = data_url
        from models.character_v2 import CharacterV2Stored
        in_memory_store[character_id] = CharacterV2Stored(
            id=character_id, **{k: v for k, v in stored_dict.items() if k != "id"}
        )
        return True
    return False
