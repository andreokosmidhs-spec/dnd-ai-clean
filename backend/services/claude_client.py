"""
Claude client helpers for D&D AI game.
- Claude Sonnet 4.6 for high-quality narration (with prompt caching)
- Claude Haiku 4.5 for cheap, fast tasks
Uses litellm (already a dependency) so no new packages needed.
Falls back to OpenAI/Emergent client when ANTHROPIC_API_KEY is not set.
"""
import os
import logging
import asyncio

logger = logging.getLogger(__name__)

SONNET = "claude-sonnet-4-6"
HAIKU = "claude-haiku-4-5-20251001"

# Fallback models when using OpenAI/Emergent key
_OPENAI_SONNET_FALLBACK = "gpt-4o"
_OPENAI_HAIKU_FALLBACK = "gpt-4o-mini"


def _get_anthropic_key() -> str | None:
    return os.getenv("ANTHROPIC_API_KEY")


def _get_openai_key() -> str | None:
    return os.getenv("OPENAI_API_KEY")


_SPLIT = "\x00CONTEXT_SPLIT\x00"

def _cached_system(system_prompt: str) -> list:
    """
    Build a system content list with prompt caching.

    If the prompt contains the _SPLIT sentinel, the part before it (static rules)
    gets cache_control so only that prefix is cached. The dynamic context after
    the sentinel is a plain text block that changes every turn — caching it would
    bust the cache immediately and waste the write cost.

    Without the sentinel the entire prompt is wrapped in one cache block (legacy
    behaviour, preserved for callers that don't use the marker).
    """
    if _SPLIT in system_prompt:
        static, dynamic = system_prompt.split(_SPLIT, 1)
        static = static.rstrip("- \n")   # strip the trailing `---` separator
        dynamic = dynamic.lstrip("- \n") # strip the leading `---` separator
        return [
            {"type": "text", "text": static, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": dynamic},
        ]
    return [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]


def _extract_system_text(system) -> str:
    """Extract plain text from system prompt regardless of format."""
    if isinstance(system, str):
        return system
    if isinstance(system, list) and system:
        return system[0].get("text", "")
    return ""


def _call_openai_fallback_sync(openai_model: str, system_prompt, user_content: str, max_tokens: int, temperature: float) -> str:
    """Call via OpenAI-compatible client (supports Emergent sk-emergent-* keys)."""
    from .llm_client import get_openai_client
    client = get_openai_client()
    system_text = _extract_system_text(system_prompt)
    response = client.chat.completions.create(
        model=openai_model,
        messages=[
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_content},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content


async def _call_openai_fallback_async(openai_model: str, system_prompt, user_content: str, max_tokens: int, temperature: float) -> str:
    """Async wrapper for the OpenAI fallback (EmergentClientWrapper is sync)."""
    return await asyncio.to_thread(
        _call_openai_fallback_sync, openai_model, system_prompt, user_content, max_tokens, temperature
    )


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
    Falls back to GPT-4o if ANTHROPIC_API_KEY is not set.
    """
    anthropic_key = _get_anthropic_key()
    if anthropic_key:
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
            api_key=anthropic_key,
        )
        return response.choices[0].message.content.strip()

    logger.warning("⚠️  ANTHROPIC_API_KEY not set — falling back to GPT-4o via OpenAI/Emergent")
    return await _call_openai_fallback_async(_OPENAI_SONNET_FALLBACK, system_prompt, user_content, max_tokens, temperature)


async def call_haiku_async(
    system_prompt: str,
    user_content: str,
    max_tokens: int = 500,
    temperature: float = 0.1,
) -> str:
    """Claude Haiku 4.5 — async. Falls back to GPT-4o-mini if no Anthropic key."""
    anthropic_key = _get_anthropic_key()
    if anthropic_key:
        from litellm import acompletion
        response = await acompletion(
            model=HAIKU,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            api_key=anthropic_key,
        )
        return response.choices[0].message.content.strip()

    logger.warning("⚠️  ANTHROPIC_API_KEY not set — falling back to GPT-4o-mini via OpenAI/Emergent")
    return await _call_openai_fallback_async(_OPENAI_HAIKU_FALLBACK, system_prompt, user_content, max_tokens, temperature)


# ── Sync ───────────────────────────────────────────────────────────────────────

def call_sonnet_sync(
    system_prompt: str,
    user_content: str,
    max_tokens: int = 2500,
    temperature: float = 0.7,
    cache: bool = False,
) -> str:
    """Claude Sonnet 4.6 — sync. Falls back to GPT-4o if no Anthropic key."""
    anthropic_key = _get_anthropic_key()
    if anthropic_key:
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
            api_key=anthropic_key,
        )
        return response.choices[0].message.content.strip()

    logger.warning("⚠️  ANTHROPIC_API_KEY not set — falling back to GPT-4o via OpenAI/Emergent")
    return _call_openai_fallback_sync(_OPENAI_SONNET_FALLBACK, system_prompt, user_content, max_tokens, temperature)


def call_haiku_sync(
    system_prompt: str,
    user_content: str,
    max_tokens: int = 500,
    temperature: float = 0.1,
) -> str:
    """Claude Haiku 4.5 — sync. Falls back to GPT-4o-mini if no Anthropic key."""
    anthropic_key = _get_anthropic_key()
    if anthropic_key:
        from litellm import completion
        response = completion(
            model=HAIKU,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            api_key=anthropic_key,
        )
        return response.choices[0].message.content.strip()

    logger.warning("⚠️  ANTHROPIC_API_KEY not set — falling back to GPT-4o-mini via OpenAI/Emergent")
    return _call_openai_fallback_sync(_OPENAI_HAIKU_FALLBACK, system_prompt, user_content, max_tokens, temperature)
