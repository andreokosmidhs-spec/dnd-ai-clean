"""
Generate an end-of-session adventure journal entry from recent scene history.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

RECAP_SYSTEM = (
    "You are a skilled chronicler writing a brief adventure journal entry. "
    "Write in second person (\"You...\"), past tense, 3-5 sentences. "
    "Capture the key events, any major decisions, enemies defeated, and "
    "story revelations. Be evocative but concise — this is a player's "
    "personal record, not a full novel chapter. Return ONLY the journal text."
)


async def generate_session_recap(
    recent_scenes: List[str],
    character_name: str,
    location: str,
    quests: Optional[Dict] = None,
) -> str:
    """
    Summarise the session into a short journal paragraph using the LLM.
    Falls back to a canned message if the API call fails.
    """
    if not recent_scenes:
        return f"{character_name} rested quietly, awaiting the next chapter of their journey."

    scenes_text = "\n".join(f"- {s}" for s in recent_scenes[-20:])
    quests_text = ""
    if quests:
        active = [q for q in quests.values() if isinstance(q, dict) and q.get("status") == "active"]
        if active:
            names = ", ".join(q.get("title", "unknown quest") for q in active[:3])
            quests_text = f"\nActive quests: {names}"

    user_msg = (
        f"Character: {character_name}\n"
        f"Current location: {location}\n"
        f"{quests_text}\n\n"
        f"Recent events:\n{scenes_text}\n\n"
        f"Write the journal entry for this session."
    )

    try:
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=RECAP_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        logger.warning(f"Session recap LLM call failed: {e}")
        return (
            f"Another session of adventure concluded for {character_name}. "
            f"The road continues, and new challenges await on the horizon."
        )
