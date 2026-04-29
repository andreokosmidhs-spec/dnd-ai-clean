"""Character portrait generation using Gemini Nano Banana (gemini-3.1-flash-image-preview)."""

import base64
import os
import uuid
from typing import Optional

from bson import ObjectId
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv()


_PORTRAIT_MODEL = "gemini-3.1-flash-image-preview"


def _build_portrait_prompt(character: dict) -> str:
    identity = character.get("identity") or {}
    race = character.get("race") or {}
    class_ = character.get("class") or {}
    appearance = character.get("appearance") or {}

    parts = []
    name = identity.get("name") or "adventurer"
    sex = identity.get("sex") or ""
    age_category = appearance.get("ageCategory") or ""
    race_name = race.get("key") or "human"
    class_name = class_.get("key") or "adventurer"
    build = appearance.get("build") or ""
    skin = appearance.get("skinTone") or ""
    hair = appearance.get("hairColor") or ""
    eyes = appearance.get("eyeColor") or ""
    features = appearance.get("notableFeatures") or []

    descriptor = " ".join(
        filter(None, [age_category, sex, race_name, class_name])
    ).strip() or f"{race_name} {class_name}"

    parts.append(
        f"Fantasy D&D character portrait of {name}, a {descriptor}."
    )
    hair_style = appearance.get("hairStyle") or ""
    facial_hair = appearance.get("facialHair") or ""
    # Compose a single hair phrase: "long auburn hair (braided)" / "short black hair"
    hair_phrase = ""
    if hair or hair_style:
        hair_phrase = " ".join(filter(None, [hair_style, hair])).strip() + " hair"
    body = ", ".join(
        filter(
            None,
            [
                f"{build} build" if build else "",
                skin and f"{skin} skin",
                hair_phrase,
                eyes and f"{eyes} eyes",
                facial_hair and f"facial hair: {facial_hair}",
            ],
        )
    )
    if body:
        parts.append(body + ".")
    if features:
        parts.append("Notable features: " + ", ".join(features) + ".")
    parts.append(
        "Head-and-shoulders portrait, dramatic fantasy lighting, painterly oil-on-canvas style, "
        "detailed facial features, plain dark background."
    )
    return " ".join(parts)


async def generate_character_portrait(character: dict) -> Optional[str]:
    """Generate a portrait for the character and return a data URL (or None on failure)."""

    api_key = os.getenv("EMERGENT_LLM_KEY")
    if not api_key:
        return None

    prompt = _build_portrait_prompt(character)
    session_id = f"portrait-{character.get('_id') or character.get('id') or uuid.uuid4()}"

    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message="You are an expert fantasy illustrator.",
    )
    chat.with_model("gemini", _PORTRAIT_MODEL).with_params(modalities=["image", "text"])

    msg = UserMessage(text=prompt)
    try:
        _text, images = await chat.send_message_multimodal_response(msg)
    except Exception as exc:  # noqa: BLE001
        print(f"[portrait] generation failed: {exc}")
        return None

    if not images:
        return None

    first = images[0]
    mime = first.get("mime_type") or "image/png"
    data = first.get("data")
    if not data:
        return None
    # Already base64-encoded per the playbook; just wrap as a data URL
    return f"data:{mime};base64,{data}"


async def persist_portrait(db, character_id: str, data_url: str, in_memory_store: dict) -> bool:
    """Store the data URL on the character document. Returns True on success."""

    if db is not None:
        try:
            object_id = ObjectId(character_id)
        except Exception:  # noqa: BLE001
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
