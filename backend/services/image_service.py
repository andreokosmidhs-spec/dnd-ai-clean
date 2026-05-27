"""
Scene image generation — supports multiple providers in priority order:

  1. GOOGLE_API_KEY  → Gemini 3 Pro Image (Nano Banana Pro) ~$0.134/image
  2. FAL_KEY         → fal.ai  Flux-Schnell                  ~$0.003/image
  3. REPLICATE_API_TOKEN → Replicate Flux-Schnell            ~$0.003/image
  4. OPENAI_API_KEY  → DALL-E 3                              ~$0.04/image
  5. No key          → returns None (graceful degradation)

Set whichever key your deployment provides; the service uses the first available.
Emergent deployments typically provide GOOGLE_API_KEY (Nano Banana Pro).
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

GOOGLE_API_KEY  = os.getenv("GOOGLE_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
FAL_KEY         = os.getenv("FAL_KEY", "")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")

_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=90.0)
    return _client


async def generate_scene_image(prompt: str) -> Optional[str]:
    """
    Generate a scene image. Returns a URL or base64 data URL, or None if unavailable.
    """
    if GOOGLE_API_KEY:
        return await _gemini_image(prompt)
    if FAL_KEY:
        return await _fal_flux(prompt)
    if REPLICATE_TOKEN:
        return await _replicate_flux(prompt)
    if OPENAI_API_KEY:
        return await _dalle3(prompt)
    logger.info("No image generation API key configured — skipping scene image")
    return None


def build_scene_prompt(narration: str, location: str = "", character_name: str = "") -> str:
    """Craft a visual image prompt from DM narration."""
    base  = narration[:300].replace('"', '').strip()
    loc   = f" in {location}" if location else ""
    style = (
        "fantasy digital painting, dramatic lighting, D&D 5e art style, "
        "cinematic composition, highly detailed, no text, no UI elements"
    )
    return f"{base}{loc}. {style}"


# ── Provider implementations ─────────────────────────────────────────────────

async def _gemini_image(prompt: str) -> Optional[str]:
    """Gemini 3 Pro Image (Nano Banana Pro) — returns base64 data URL."""
    try:
        client = _get_client()
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent?key={GOOGLE_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseModalities": ["IMAGE"],
                    "imageConfig": {"aspectRatio": "4:3"},
                },
            },
        )
        resp.raise_for_status()
        data  = resp.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        for part in parts:
            inline = part.get("inline_data", {})
            if inline.get("data"):
                mime = inline.get("mime_type", "image/jpeg")
                return f"data:{mime};base64,{inline['data']}"
        return None
    except Exception as e:
        logger.warning(f"Gemini image generation failed: {e}")
        return None


async def _fal_flux(prompt: str) -> Optional[str]:
    try:
        client = _get_client()
        resp = await client.post(
            "https://fal.run/fal-ai/flux/schnell",
            headers={"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"},
            json={"prompt": prompt, "image_size": "landscape_4_3", "num_images": 1},
        )
        resp.raise_for_status()
        images = resp.json().get("images") or []
        return images[0]["url"] if images else None
    except Exception as e:
        logger.warning(f"fal.ai image generation failed: {e}")
        return None


async def _replicate_flux(prompt: str) -> Optional[str]:
    try:
        client = _get_client()
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
        data   = start.json()
        output = data.get("output")
        if output:
            return output[0] if isinstance(output, list) else output
        poll_url = data.get("urls", {}).get("get")
        if not poll_url:
            return None
        for _ in range(20):
            await asyncio.sleep(2)
            poll  = await client.get(poll_url, headers={"Authorization": f"Bearer {REPLICATE_TOKEN}"})
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
        return resp.json()["data"][0]["url"]
    except Exception as e:
        logger.warning(f"DALL-E 3 image generation failed: {e}")
        return None
