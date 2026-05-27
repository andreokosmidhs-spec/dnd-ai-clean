"""
Battlefield condition card art generation.

The card's description text is the creative brief for the image.
We wrap it in a consistent art-direction prompt, call DALL-E 3,
cache the result in MongoDB so we only generate once per unique card.

Cache key = sha256(title + description)[:20] — stable across sessions.
"""
from __future__ import annotations

import base64
import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

_ART_STYLE = (
    "Dark fantasy tabletop card illustration, dramatic chiaroscuro lighting, "
    "oil painting style with rich texture, moody atmosphere, "
    "cinematic composition, no text, no borders, no UI elements, "
    "high detail, painterly, D&D 5e aesthetic"
)


def _art_key(title: str, description: str) -> str:
    raw = f"{title}|{description}"
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


def _build_prompt(title: str, description: str) -> str:
    # Strip the interactive-hint sentence (usually the last one) from the description
    # so the image prompt is purely visual.
    sentences = description.replace(" — ", ". ").split(". ")
    visual_sentences = [s for s in sentences if not any(
        kw in s.lower()
        for kw in ("clever", "if they know", "might", "could be used",
                   "anyone brave", "whoever", "depends entirely", "opportunity")
    )]
    visual_core = ". ".join(visual_sentences[:3]).strip(". ") or description
    return f"{_ART_STYLE}. Scene: {visual_core}. Card title: '{title}'."


async def get_or_generate_art(
    db,
    title: str,
    description: str,
) -> Optional[str]:
    """
    Return a data_url for the condition art.
    Checks MongoDB cache first; generates with DALL-E 3 on cache miss.
    Returns None if generation is not available (no API key, quota exceeded, etc.).
    """
    key = _art_key(title, description)
    collection = db.combat_condition_art

    # Cache hit
    cached = await collection.find_one({"art_key": key})
    if cached and cached.get("data_url"):
        logger.info(f"🎨 Art cache hit for '{title}' ({key})")
        return cached["data_url"]

    # Generate
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        logger.warning("No API key for image generation — skipping art")
        return None

    prompt = _build_prompt(title, description)
    logger.info(f"🎨 Generating art for '{title}' (key={key})")

    try:
        from openai import AsyncOpenAI

        # Emergent keys route through a compatible endpoint
        base_url = None
        if api_key.startswith("sk-emergent-"):
            base_url = os.environ.get("EMERGENT_BASE_URL", "https://api.emergentintegrations.com/v1")

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
            response_format="b64_json",
        )
        b64 = response.data[0].b64_json
        data_url = f"data:image/png;base64,{b64}"

        # Cache it
        await collection.update_one(
            {"art_key": key},
            {"$set": {
                "art_key": key,
                "title": title,
                "data_url": data_url,
                "prompt": prompt,
                "created_at": datetime.now(timezone.utc),
            }},
            upsert=True,
        )
        logger.info(f"✅ Art generated and cached for '{title}'")
        return data_url

    except Exception as exc:
        logger.warning(f"Art generation failed for '{title}': {exc}")
        return None
