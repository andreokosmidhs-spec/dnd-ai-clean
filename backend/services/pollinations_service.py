"""Pollinations.ai image generation — free, no API key required.

Two modes:
  generate_image()   — text-to-image via FLUX (basic portraits, scenes, items)
  generate_kontext() — image-to-image via FLUX Kontext (character consistency)
                       Pass the character's existing portrait as reference to
                       keep the same face/appearance in a new scene.

Rate limits (free Seed tier after registering at auth.pollinations.ai):
  1 request / 5 seconds  — fine for D&D session-level usage
"""

import base64
import io
import logging
import re
import urllib.parse
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_BASE     = "https://image.pollinations.ai"
_API_BASE = "https://gen.pollinations.ai"
_TIMEOUT  = 60.0  # Kontext can be slow on free tier


def _data_url_to_bytes(data_url: str) -> Optional[tuple[bytes, str]]:
    """Convert a base64 data URL to (raw_bytes, mime_type)."""
    match = re.match(r"^data:([^;]+);base64,(.+)$", data_url.strip(), re.DOTALL)
    if not match:
        return None
    mime = match.group(1).strip()
    try:
        raw = base64.b64decode(match.group(2).strip())
        return raw, mime
    except Exception:
        return None


async def _to_data_url(raw: bytes, mime: str = "image/png") -> str:
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


async def generate_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    model: str = "flux",
) -> Optional[str]:
    """Text-to-image using Pollinations FLUX (free, no reference image)."""
    encoded = urllib.parse.quote(prompt, safe="")
    url = f"{_BASE}/prompt/{encoded}?width={width}&height={height}&model={model}&nologo=true"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        mime = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
        return await _to_data_url(resp.content, mime)
    except Exception as exc:
        logger.warning(f"[pollinations] text-to-image failed: {exc}")
        return None


async def generate_kontext(
    prompt: str,
    reference_data_url: str,
    width: int = 1024,
    height: int = 1024,
) -> Optional[str]:
    """Image-to-image using FLUX Kontext — preserves character appearance.

    Pass an existing portrait as reference_data_url (base64 data URL).
    Kontext keeps the face/clothing/style and applies the scene from prompt.
    """
    parsed = _data_url_to_bytes(reference_data_url)
    if not parsed:
        logger.warning("[pollinations] kontext: invalid reference_data_url, skipping")
        return None
    raw_bytes, mime = parsed

    ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
    ext = ext_map.get(mime, "jpg")
    filename = f"reference.{ext}"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{_API_BASE}/v1/images/edits",
                data={"prompt": prompt, "model": "kontext",
                      "width": str(width), "height": str(height)},
                files={"image": (filename, io.BytesIO(raw_bytes), mime)},
            )
            resp.raise_for_status()
        out_mime = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
        return await _to_data_url(resp.content, out_mime)
    except Exception as exc:
        logger.warning(f"[pollinations] kontext failed: {exc}")
        return None
