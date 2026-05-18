"""
Claude client helpers for D&D AI game.
- Claude Sonnet 4.6 for high-quality narration (with prompt caching)
- Claude Haiku 4.5 for cheap, fast tasks
Uses litellm (already a dependency) so no new packages needed.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SONNET = "claude-sonnet-4-6"
HAIKU = "claude-haiku-4-5-20251001"


def _get_anthropic_key() -> str:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment")
    return key


def _cached_system(system_prompt: str) -> list:
    """Wrap system prompt in a cache_control block for Anthropic prompt caching."""
    return [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]


# ── Async ──────────────────────────────────────────────────────────────────────

async def call_sonnet_async(
    system_prompt: str,
    user_content: str,
    max_tokens: int = 2500,
    temperature: float = 0.7,
    cache: bool = True,
) -> str:
    """
    Claude Sonnet 4.6 — async. Use for DM narration, world gen, story consistency.
    Caches system prompt by default (saves ~30% tokens per session).
    """
    from litellm import acompletion

    system = _cached_system(system_prompt) if cache else system_prompt
    response = await acompletion(
        model=SONNET,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        api_key=_get_anthropic_key(),
    )
    return response.choices[0].message.content.strip()


async def call_haiku_async(
    system_prompt: str,
    user_content: str,
    max_tokens: int = 500,
    temperature: float = 0.1,
) -> str:
    """Claude Haiku 4.5 — async. Use for intent tagging, log extraction, short tasks."""
    from litellm import acompletion

    response = await acompletion(
        model=HAIKU,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        api_key=_get_anthropic_key(),
    )
    return response.choices[0].message.content.strip()


# ── Sync ───────────────────────────────────────────────────────────────────────

def call_sonnet_sync(
    system_prompt: str,
    user_content: str,
    max_tokens: int = 2500,
    temperature: float = 0.7,
    cache: bool = False,
) -> str:
    """Claude Sonnet 4.6 — sync. Use for world generation, character creation."""
    from litellm import completion

    system = _cached_system(system_prompt) if cache else system_prompt
    response = completion(
        model=SONNET,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        api_key=_get_anthropic_key(),
    )
    return response.choices[0].message.content.strip()


def call_haiku_sync(
    system_prompt: str,
    user_content: str,
    max_tokens: int = 500,
    temperature: float = 0.1,
) -> str:
    """Claude Haiku 4.5 — sync. Use for scene generation, short structured tasks."""
    from litellm import completion

    response = completion(
        model=HAIKU,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        api_key=_get_anthropic_key(),
    )
    return response.choices[0].message.content.strip()
