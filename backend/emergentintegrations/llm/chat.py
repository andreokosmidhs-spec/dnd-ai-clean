"""
Compatibility stub for emergentintegrations.llm.chat.

Provides LlmChat and UserMessage with the same interface as the real
emergentintegrations package, but routes calls to:
  - Anthropic Claude (claude-sonnet-4-6 / claude-haiku-4-5) when ANTHROPIC_API_KEY is set
  - Standard OpenAI (gpt-4o / gpt-4o-mini) when OPENAI_API_KEY is set

This lets all services that `from emergentintegrations.llm.chat import LlmChat, UserMessage`
continue to work when deployed outside the Emergent platform.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Map OpenAI model names → Claude equivalents for Anthropic routing
_CLAUDE_MODEL_MAP = {
    "gpt-4o": "claude-sonnet-4-6",
    "gpt-4": "claude-sonnet-4-6",
    "gpt-4-turbo": "claude-sonnet-4-6",
    "gpt-4o-mini": "claude-haiku-4-5-20251001",
    "gpt-3.5-turbo": "claude-haiku-4-5-20251001",
    "gpt-4o-mini-2024-07-18": "claude-haiku-4-5-20251001",
    "gpt-5-thinking": "claude-sonnet-4-6",
    "gpt-5-a-t-mini": "claude-haiku-4-5-20251001",
}


class UserMessage:
    """Simple message wrapper compatible with the real emergentintegrations UserMessage."""

    def __init__(self, text: str):
        self.text = text
        self.role = "user"
        self.content = text


class FileContent:
    """Stub for file/image attachments (used by character_portrait). Not functional outside Emergent."""

    def __init__(self, content_type: str = "", file_content_base64: str = "", **_kwargs):
        self.content_type = content_type
        self.file_content_base64 = file_content_base64


class LlmChat:
    """
    Drop-in replacement for emergentintegrations.llm.chat.LlmChat.

    Usage (unchanged from the real package):
        chat = LlmChat(api_key=key, session_id="abc", system_message="...")
        chat.with_model("openai", "gpt-4o-mini").with_params(temperature=0.0)
        response = await chat.send_message(UserMessage(text="Hello"))
    """

    def __init__(
        self,
        api_key: str,
        session_id: str,
        system_message: str = "",
    ):
        self._api_key = api_key
        self._session_id = session_id
        self._system_message = system_message
        self._model = "gpt-4o"
        self._provider = "openai"
        self._temperature: float = 0.7
        self._max_tokens: Optional[int] = None

    def with_model(self, provider: str, model: str) -> "LlmChat":
        self._provider = provider
        self._model = model
        return self

    def with_params(self, temperature: float = 0.7, max_tokens: Optional[int] = None, **_kwargs) -> "LlmChat":
        self._temperature = temperature
        if max_tokens is not None:
            self._max_tokens = max_tokens
        return self

    async def send_message(self, user_message: UserMessage) -> str:
        """Route to Anthropic or OpenAI based on available env keys."""
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            return await self._call_anthropic(anthropic_key, user_message.text)

        openai_key = os.getenv("OPENAI_API_KEY") or self._api_key
        if openai_key and not openai_key.startswith("sk-emergent-"):
            return await self._call_openai(openai_key, user_message.text)

        raise RuntimeError(
            "No LLM key available. Set ANTHROPIC_API_KEY (recommended) or OPENAI_API_KEY in your environment."
        )

    async def _call_anthropic(self, api_key: str, prompt: str) -> str:
        from litellm import acompletion

        claude_model = _CLAUDE_MODEL_MAP.get(self._model, "claude-haiku-4-5-20251001")
        kwargs = dict(
            model=claude_model,
            messages=[
                {"role": "system", "content": self._system_message},
                {"role": "user", "content": prompt},
            ],
            temperature=self._temperature,
            api_key=api_key,
        )
        if self._max_tokens:
            kwargs["max_tokens"] = self._max_tokens

        response = await acompletion(**kwargs)
        return response.choices[0].message.content.strip()

    async def _call_openai(self, api_key: str, prompt: str) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)
        kwargs = dict(
            model=self._model,
            messages=[
                {"role": "system", "content": self._system_message},
                {"role": "user", "content": prompt},
            ],
            temperature=self._temperature,
        )
        if self._max_tokens:
            kwargs["max_tokens"] = self._max_tokens

        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message.content.strip()
