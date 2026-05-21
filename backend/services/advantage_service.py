"""
DM contextual advantage / disadvantage assessment.

A fast Haiku call that looks at the *narrative* scene — positioning, surprise,
cover, creative tactics — and decides whether the player's attack deserves
advantage or disadvantage beyond what the mechanical conditions already grant.

Mechanical conditions (blinded, prone, poisoned…) are handled by
compute_advantage_flags() in dnd_rules.py.  This service covers everything else.
"""
from __future__ import annotations
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_SYSTEM = """\
You are a D&D 5e combat rules judge embedded inside a live game.

Your job: decide whether this player's attack gets ADVANTAGE, DISADVANTAGE, or NEITHER
based purely on NARRATIVE / POSITIONAL context.

What you MUST ignore (already handled mechanically):
  - Any condition explicitly listed in attacker_conditions or target_conditions
  - Light level — already calculated separately

What you SHOULD judge:
  - Flanking: an ally is on the opposite side of the target  → advantage
  - Surprise / ambush: target didn't know the player was there  → advantage
  - High ground / elevation  → advantage
  - Creative environment use: swing from chandelier, kick table into target  → advantage
  - Target fully cornered with no escape and panicking  → advantage
  - Attacking into wind, heavy rain, magical smoke (not darkness)  → disadvantage
  - Cramped space that limits weapon swing  → disadvantage
  - Called shot into unusually well-protected area  → disadvantage
  - Player's described action is reckless/telegraphed  → disadvantage
  - Distracted target (being attacked by another creature)  → advantage

Rules:
  - Advantage AND disadvantage in same attack cancel → return {"advantage": false, "disadvantage": false}
  - When the narrative gives no clear signal → return neither (default)
  - Keep reason to one concise sentence or leave empty

Return ONLY valid JSON. No markdown, no explanation outside JSON:
{"advantage": false, "disadvantage": false, "reason": ""}
"""


async def get_dm_advantage_assessment(
    player_action: str,
    target_name: str,
    target_conditions: List[str],
    attacker_conditions: List[str],
    battlefield_conditions: List[str],
    light_level: str = "bright",
    extra_context: str = "",
) -> Dict:
    """Return {advantage, disadvantage, reason} based on narrative scene context.

    Falls back to {advantage: False, disadvantage: False, reason: ""} on any error.
    """
    default = {"advantage": False, "disadvantage": False, "reason": ""}

    try:
        from services.claude_client import call_haiku_async

        user_msg = (
            f"Player action: {player_action}\n"
            f"Target: {target_name}\n"
            f"Target conditions (mechanical, already applied): {', '.join(target_conditions) or 'none'}\n"
            f"Attacker conditions (mechanical, already applied): {', '.join(attacker_conditions) or 'none'}\n"
            f"Active battlefield conditions: {', '.join(battlefield_conditions) or 'none'}\n"
            f"Light level: {light_level}\n"
        )
        if extra_context:
            user_msg += f"Additional context: {extra_context}\n"

        response = await call_haiku_async(
            system_prompt=_SYSTEM,
            user_content=user_msg,
            max_tokens=80,
            temperature=0.0,
        )

        text = (response or "").strip()
        # Extract JSON from response
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start == -1 or end == 0:
            return default

        result = json.loads(text[start:end])
        return {
            "advantage":    bool(result.get("advantage", False)),
            "disadvantage": bool(result.get("disadvantage", False)),
            "reason":       str(result.get("reason", "")),
        }

    except Exception as exc:
        logger.debug(f"DM advantage assessment failed (non-critical): {exc}")
        return default
