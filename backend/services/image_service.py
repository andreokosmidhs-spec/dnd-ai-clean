"""
Scene image generation via fal.ai (Flux Schnell) or OpenAI DALL-E 3.

Priority:
  1. FAL_KEY  → fal.ai  Flux-Schnell (~$0.003/image, very fast)
  2. REPLICATE_API_TOKEN → Replicate Flux-Schnell (~$0.003/image)
  3. OPENAI_API_KEY → DALL-E 3 (~$0.04/image, highest quality)
  4. No key → returns None (graceful degradation)
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

FAL_KEY             = os.getenv("FAL_KEY", "")
REPLICATE_TOKEN     = os.getenv("REPLICATE_API_TOKEN", "")
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY", "")

# Shared async HTTP client (module-level, reused across calls)
_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=60.0)
    return _client


async def generate_scene_image(prompt: str) -> Optional[str]:
    """
    Generate a scene image for the given prompt.
    Returns a URL string or None if generation is unavailable/fails.
    """
    if FAL_KEY:
        return await _fal_flux(prompt)
    if REPLICATE_TOKEN:
        return await _replicate_flux(prompt)
    if OPENAI_API_KEY:
        return await _dalle3(prompt)
    return None


def build_scene_prompt(narration: str, location: str = "", character_name: str = "") -> str:
    """
    Craft an image prompt from DM narration. Keeps it concise and visual.
    """
    base = narration[:300].replace('"', '').strip()
    loc  = f" in {location}" if location else ""
    style = (
        "fantasy digital painting, dramatic lighting, D&D 5e art style, "
        "cinematic composition, highly detailed, no text"
    )
    return f"{base}{loc}. {style}"


# ── Provider implementations ─────────────────────────────────────────────────

async def _fal_flux(prompt: str) -> Optional[str]:
    try:
        client = _get_client()
        resp = await client.post(
            "https://fal.run/fal-ai/flux/schnell",
            headers={"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"},
            json={"prompt": prompt, "image_size": "landscape_4_3", "num_images": 1},
        )
        resp.raise_for_status()
        data = resp.json()
        images = data.get("images") or []
        return images[0]["url"] if images else None
    except Exception as e:
        logger.warning(f"fal.ai image generation failed: {e}")
        return None


async def _replicate_flux(prompt: str) -> Optional[str]:
    try:
        client = _get_client()
        # Start prediction
        start = await client.post(
            "https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions",
            headers={
                "Authorization": f"Bearer {REPLICATE_TOKEN}",
                "Content-Type": "application/json",
                "Prefer": "wait=30",
            },
            json={"input": {"prompt": prompt, "aspect_ratio": "4:3", "num_outputs": 1}},
        )
        start.raise_for_status()
        data = start.json()

        # If synchronous wait returned output already
        output = data.get("output")
        if output:
            return output[0] if isinstance(output, list) else output

        # Otherwise poll
        poll_url = data.get("urls", {}).get("get")
        if not poll_url:
            return None
        for _ in range(20):
            await asyncio.sleep(2)
            poll = await client.get(
                poll_url,
                headers={"Authorization": f"Bearer {REPLICATE_TOKEN}"},
            )
            pdata = poll.json()
            if pdata.get("status") == "succeeded":
                out = pdata.get("output")
                return out[0] if isinstance(out, list) else out
            if pdata.get("status") in ("failed", "canceled"):
                return None
        return None
    except Exception as e:
        logger.warning(f"Replicate image generation failed: {e}")
        return None


async def _dalle3(prompt: str) -> Optional[str]:
    try:
        client = _get_client()
        resp = await client.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": "dall-e-3", "prompt": prompt, "n": 1, "size": "1024x1024"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"][0]["url"]
    except Exception as e:
        logger.warning(f"DALL-E 3 image generation failed: {e}")
        return None
