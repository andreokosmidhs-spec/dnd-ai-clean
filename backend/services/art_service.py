"""Unified art generation.

Provider priority (first available wins):
  1. Replicate API      — REPLICATE_API_TOKEN  (cloud, best quality, ~$0.003–0.05/img)
  2. Pollinations Kontext — free, uses FLUX Kontext for character consistency
                           (reference portrait → same face in new scene)
  3. Local SD           — A1111_URL or SD_LOCAL=true  (free, runs on your machine)

Optional env var:
  ART_LORA_URL  — HuggingFace .safetensors LoRA URL applied to all Replicate
                  generations for a unified visual style.

Generation strategy
───────────────────
Character / NPC portraits (initial)
  Replicate: fofr/consistent-character
  Pollinations: FLUX text-to-image (free)
  Local SD:  portrait prompt → local_sd_service.generate_portrait()

Character portraits (with existing reference → consistency)
  Replicate: fofr/consistent-character + subject_image_0
  Pollinations: FLUX Kontext — same face preserved in new scene (free)

Location / item cards
  Replicate: flux-schnell (fast) or flux-dev-lora (with LoRA)
  Pollinations: FLUX text-to-image (free)
  Local SD:  scene / square prompts via local_sd_service
"""

import base64
import io
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_CONSISTENT_CHARACTER = "fofr/consistent-character"
_FLUX_SCHNELL = "black-forest-labs/flux-schnell"
_FLUX_LORA = "lucataco/flux-dev-lora"

_STYLE = (
    "dark fantasy RPG concept art, painterly oil-on-canvas style, "
    "dramatic chiaroscuro lighting, highly detailed, professional illustration"
)


def _client():
    if not os.getenv("REPLICATE_API_TOKEN"):
        return None
    try:
        import replicate
        return replicate
    except ImportError:
        logger.error("[art] replicate package not installed — run: pip install replicate")
        return None


def _data_url_to_bytes(data_url: str) -> Optional[io.BytesIO]:
    if not data_url or "," not in data_url:
        return None
    try:
        _, b64 = data_url.split(",", 1)
        return io.BytesIO(base64.b64decode(b64))
    except Exception:
        return None


async def _fetch_as_data_url(url: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=90) as http:
            resp = await http.get(str(url))
            resp.raise_for_status()
        mime = resp.headers.get("content-type", "image/webp").split(";")[0].strip()
        return f"data:{mime};base64,{base64.b64encode(resp.content).decode()}"
    except Exception as exc:
        logger.warning(f"[art] image fetch failed: {exc}")
        return None


def _first(output) -> Optional[str]:
    if output is None:
        return None
    if isinstance(output, list):
        return str(output[0]) if output else None
    return str(output)


def build_character_subject(character: dict) -> str:
    identity = character.get("identity") or {}
    race = (character.get("race") or {}).get("key", "human")
    cls = (character.get("class") or {}).get("key", "fighter")
    app = character.get("appearance") or {}

    parts = [
        f"{app.get('ageCategory', 'adult')} {identity.get('sex', '')} {race} {cls}".strip(),
        f"{app.get('build', '')} build".strip() if app.get("build") else "",
        f"{app.get('skinTone', '')} skin".strip() if app.get("skinTone") else "",
        f"{app.get('hairStyle', '')} {app.get('hairColor', '')} hair".strip() if app.get("hairColor") else "",
        f"{app.get('eyeColor', '')} eyes".strip() if app.get("eyeColor") else "",
    ]
    features = app.get("notableFeatures") or []
    if features:
        parts.append(", ".join(features))
    return ", ".join(p for p in parts if p)


def _gear_phrase(character: dict) -> str:
    inventory = character.get("inventory") or []
    names = [i.get("name", "") for i in inventory if i.get("equipped") and i.get("name")]
    return ("wearing " + ", ".join(names[:6])) if names else "adventurer's clothing"


async def generate_character_portrait(
    character: dict,
    reference_data_url: Optional[str] = None,
) -> Optional[str]:
    subject = build_character_subject(character)
    gear = _gear_phrase(character)
    lora_url = os.getenv("ART_LORA_URL", "")
    prompt = (
        f"fantasy RPG character portrait, {gear}, "
        f"head-and-shoulders view, {_STYLE}, plain dark background"
    )

    r = _client()
    if r is not None:
        try:
            if lora_url:
                output = await r.async_run(
                    _FLUX_LORA,
                    input={
                        "prompt": f"portrait of {subject}, {gear}, {_STYLE}, plain dark background",
                        "hf_lora": lora_url,
                        "num_inference_steps": 28,
                        "guidance_scale": 3.5,
                        "output_format": "webp",
                        "output_quality": 85,
                    },
                )
            elif reference_data_url:
                ref_file = _data_url_to_bytes(reference_data_url)
                output = await r.async_run(
                    _CONSISTENT_CHARACTER,
                    input={
                        "prompt": prompt,
                        "subject": subject,
                        "subject_image_0": ref_file,
                        "num_outputs": 1,
                        "output_format": "webp",
                        "output_quality": 85,
                    },
                )
            else:
                output = await r.async_run(
                    _CONSISTENT_CHARACTER,
                    input={
                        "prompt": prompt,
                        "subject": subject,
                        "num_outputs": 1,
                        "output_format": "webp",
                        "output_quality": 85,
                    },
                )
            url = _first(output)
            result = await _fetch_as_data_url(url) if url else None
            if result:
                return result
        except Exception as exc:
            logger.warning(f"[art] Replicate portrait failed, trying local SD: {exc}")

    full_prompt = f"portrait of {subject}, {gear}, {_STYLE}, plain dark background"

    # 2. Pollinations Kontext (free) — consistent face if reference available,
    #    otherwise plain text-to-image
    try:
        from services.pollinations_service import generate_kontext, generate_image
        if reference_data_url:
            result = await generate_kontext(
                f"The same character, {gear}, fantasy RPG portrait, head and shoulders, {_STYLE}, plain dark background",
                reference_data_url,
            )
        else:
            result = await generate_image(full_prompt, width=768, height=1024, model="flux")
        if result:
            return result
    except Exception as exc:
        logger.warning(f"[art] Pollinations portrait failed, trying local SD: {exc}")

    try:
        from services.local_sd_service import generate_portrait as _local_portrait
        return await _local_portrait(full_prompt)
    except Exception as exc:
        logger.error(f"[art] local SD portrait failed: {exc}")
    return None


async def generate_npc_art(name: str, description: str, role: str = "") -> Optional[str]:
    lora_url = os.getenv("ART_LORA_URL", "")
    subject = ", ".join(filter(None, [name, description, role]))
    prompt = f"fantasy RPG NPC portrait of {subject}, head and shoulders, {_STYLE}, plain dark background"

    r = _client()
    if r is not None:
        try:
            if lora_url:
                output = await r.async_run(
                    _FLUX_LORA,
                    input={"prompt": prompt, "hf_lora": lora_url, "num_inference_steps": 28, "output_format": "webp"},
                )
            else:
                output = await r.async_run(
                    _CONSISTENT_CHARACTER,
                    input={"prompt": prompt, "subject": subject, "num_outputs": 1, "output_format": "webp"},
                )
            url = _first(output)
            result = await _fetch_as_data_url(url) if url else None
            if result:
                return result
        except Exception as exc:
            logger.warning(f"[art] Replicate NPC art failed, trying Pollinations: {exc}")

    try:
        from services.pollinations_service import generate_image as _poll
        result = await _poll(prompt, width=768, height=1024, model="flux")
        if result:
            return result
    except Exception as exc:
        logger.warning(f"[art] Pollinations NPC art failed, trying local SD: {exc}")

    try:
        from services.local_sd_service import generate_portrait as _local_portrait
        return await _local_portrait(prompt)
    except Exception as exc:
        logger.error(f"[art] local SD NPC art failed: {exc}")
    return None


async def generate_place_art(name: str, description: str, biome: str = "") -> Optional[str]:
    lora_url = os.getenv("ART_LORA_URL", "")
    biome_tag = f"{biome}, " if biome else ""
    prompt = f"{biome_tag}{name}, {description}, fantasy RPG location, wide establishing shot, {_STYLE}"

    r = _client()
    if r is not None:
        try:
            if lora_url:
                output = await r.async_run(
                    _FLUX_LORA,
                    input={"prompt": prompt, "hf_lora": lora_url, "num_inference_steps": 28,
                           "output_format": "webp", "aspect_ratio": "16:9"},
                )
            else:
                output = await r.async_run(
                    _FLUX_SCHNELL,
                    input={"prompt": prompt, "num_inference_steps": 4,
                           "output_format": "webp", "aspect_ratio": "16:9"},
                )
            url = _first(output)
            result = await _fetch_as_data_url(url) if url else None
            if result:
                return result
        except Exception as exc:
            logger.warning(f"[art] Replicate place art failed, trying Pollinations: {exc}")

    try:
        from services.pollinations_service import generate_image as _poll
        result = await _poll(prompt, width=1280, height=720, model="flux")
        if result:
            return result
    except Exception as exc:
        logger.warning(f"[art] Pollinations place art failed, trying local SD: {exc}")

    try:
        from services.local_sd_service import generate_scene as _local_scene
        return await _local_scene(prompt)
    except Exception as exc:
        logger.error(f"[art] local SD place art failed: {exc}")
    return None


async def generate_item_art(name: str, description: str, rarity: str = "common") -> Optional[str]:
    lora_url = os.getenv("ART_LORA_URL", "")
    rarity_tag = {
        "legendary": "radiant, golden glow, mythic",
        "epic": "ornate, enchanted, arcane runes",
        "rare": "detailed, masterwork",
    }.get(rarity.lower(), "")
    prompt = f"{name}, {description}, fantasy RPG item art, {rarity_tag}, isolated on dark background, {_STYLE}"

    r = _client()
    if r is not None:
        try:
            if lora_url:
                output = await r.async_run(
                    _FLUX_LORA,
                    input={"prompt": prompt, "hf_lora": lora_url, "num_inference_steps": 28,
                           "output_format": "webp", "aspect_ratio": "1:1"},
                )
            else:
                output = await r.async_run(
                    _FLUX_SCHNELL,
                    input={"prompt": prompt, "num_inference_steps": 4,
                           "output_format": "webp", "aspect_ratio": "1:1"},
                )
            url = _first(output)
            result = await _fetch_as_data_url(url) if url else None
            if result:
                return result
        except Exception as exc:
            logger.warning(f"[art] Replicate item art failed, trying Pollinations: {exc}")

    try:
        from services.pollinations_service import generate_image as _poll
        result = await _poll(prompt, width=1024, height=1024, model="flux")
        if result:
            return result
    except Exception as exc:
        logger.warning(f"[art] Pollinations item art failed, trying local SD: {exc}")

    try:
        from services.local_sd_service import generate_square as _local_square
        return await _local_square(prompt)
    except Exception as exc:
        logger.error(f"[art] local SD item art failed: {exc}")
    return None
