"""Downtime & breathing room service.

After 3-4 hook resolutions the narrative pressure should ease. The player
needs time to prepare, socialize, eat, rest, train, explore, and celebrate.

This service tracks pacing state and tells the DM when and how to open
the world up — shifting from the urgency of active investigation to the
richness of a world that exists between quests.

Pacing state lives in campaign["world_state"]["narrative_pacing"] so it
persists across turns without a separate collection.
"""
from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# After this many resolved hooks without rest, breathing room triggers
HOOK_RESOLUTION_THRESHOLD = 3

# In-game hours before hunger surfaces naturally in narration
MEAL_INTERVAL_HOURS = 6

# In-game hours before exhaustion surfaces naturally
REST_INTERVAL_HOURS = 16

# Keywords that indicate the player ate or drank
_MEAL_KEYWORDS = re.compile(
    r"\b(eat|eating|ate|drink|drinking|drank|food|meal|breakfast|lunch|dinner|"
    r"supper|tavern|inn|ration|feast|bread|soup|stew|ale|wine|water)\b",
    re.IGNORECASE,
)

# Keywords that indicate the player rested or slept
_REST_KEYWORDS = re.compile(
    r"\b(sleep|sleeping|slept|rest|resting|rested|long rest|camp|camping|camped|"
    r"bed|bedroll|inn room|lie down|close my eyes|take a rest|short rest)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def get_pacing_state(campaign: dict) -> dict:
    """Return the current pacing state, initialised to safe defaults."""
    pacing = (campaign.get("world_state") or {}).get("narrative_pacing") or {}
    return {
        "hook_resolutions": int(pacing.get("hook_resolutions", 0)),
        "last_meal_hour": pacing.get("last_meal_hour"),
        "last_rest_hour": pacing.get("last_rest_hour"),
        "phase": pacing.get("phase", "active"),
        "victory_pending": bool(pacing.get("victory_pending", False)),
        "victory_title": str(pacing.get("victory_title", "")),
        "downtime_hours_remaining": int(pacing.get("downtime_hours_remaining", 0)),
    }


def _save_pacing(campaign: dict, pacing: dict) -> None:
    campaign.setdefault("world_state", {})["narrative_pacing"] = pacing


def _hours_since(reference_hour: Optional[int], current_hour: int) -> Optional[int]:
    if reference_hour is None:
        return None
    return int((current_hour - reference_hour) % 24)


# ---------------------------------------------------------------------------
# State mutation helpers (call these and then persist the campaign doc)
# ---------------------------------------------------------------------------

def increment_hook_resolutions(campaign: dict) -> None:
    pacing = get_pacing_state(campaign)
    pacing["hook_resolutions"] += 1
    _save_pacing(campaign, pacing)


def record_meal(campaign: dict, clock_hour: int) -> None:
    pacing = get_pacing_state(campaign)
    pacing["last_meal_hour"] = clock_hour
    _save_pacing(campaign, pacing)


def record_rest(campaign: dict, clock_hour: int) -> None:
    """Long rest: resets hook counter and returns to active phase."""
    pacing = get_pacing_state(campaign)
    pacing["last_rest_hour"] = clock_hour
    pacing["hook_resolutions"] = 0
    pacing["phase"] = "active"
    _save_pacing(campaign, pacing)


def open_preparation_window(campaign: dict, hours_available: int = 48) -> None:
    """Open after the player receives a new lead — gives them in-game time."""
    pacing = get_pacing_state(campaign)
    pacing["phase"] = "preparation"
    pacing["downtime_hours_remaining"] = hours_available
    _save_pacing(campaign, pacing)


def trigger_victory_feast(campaign: dict, victory_title: str) -> None:
    pacing = get_pacing_state(campaign)
    pacing["victory_pending"] = True
    pacing["victory_title"] = victory_title
    _save_pacing(campaign, pacing)


def clear_victory_feast(campaign: dict) -> None:
    pacing = get_pacing_state(campaign)
    pacing["victory_pending"] = False
    pacing["victory_title"] = ""
    pacing["hook_resolutions"] = 0
    pacing["phase"] = "active"
    _save_pacing(campaign, pacing)


def check_player_action_for_needs(player_action: str, campaign: dict, clock_hour: int) -> None:
    """Detect if the player's action satisfies a meal or rest need and record it."""
    if _MEAL_KEYWORDS.search(player_action):
        record_meal(campaign, clock_hour)
    if _REST_KEYWORDS.search(player_action):
        record_rest(campaign, clock_hour)


# ---------------------------------------------------------------------------
# Context block builder
# ---------------------------------------------------------------------------

def build_downtime_block(
    campaign: dict,
    clock_hour: int,
    character: Optional[Dict] = None,
    current_location: Optional[Dict] = None,
) -> str:
    """Build the downtime / breathing room context block for the DM prompt.

    Returns an empty string when no pacing intervention is needed.
    Returns a formatted block when breathing room, downtime, preparation,
    or a victory feast is active.
    """
    pacing = get_pacing_state(campaign)
    phase = pacing["phase"]
    hook_resolutions = pacing["hook_resolutions"]
    victory_pending = pacing["victory_pending"]
    victory_title = pacing["victory_title"]

    # Compute need states
    hours_since_meal = _hours_since(pacing["last_meal_hour"], clock_hour)
    hours_since_rest = _hours_since(pacing["last_rest_hour"], clock_hour)
    hunger = hours_since_meal is not None and hours_since_meal >= MEAL_INTERVAL_HOURS
    fatigue = hours_since_rest is not None and hours_since_rest >= REST_INTERVAL_HOURS

    # Extract personality for personal-moment surfacing
    bond = ""
    ideal = ""
    flaw = ""
    if character:
        ideals = character.get("ideals") or []
        bonds = character.get("bonds") or []
        flaws = character.get("flaws_detailed") or []
        if ideals and isinstance(ideals[0], dict):
            ideal = (ideals[0].get("principle") or "").strip()
        if bonds and isinstance(bonds[0], dict):
            bond = (bonds[0].get("person_or_cause") or "").strip()
        if flaws and isinstance(flaws[0], dict):
            flaw = (flaws[0].get("habit") or "").strip()
        if not ideal or not bond or not flaw:
            bg_p = (character.get("background") or {}).get("personality") or {}
            ideal = ideal or (bg_p.get("ideal") or "").strip()
            bond = bond or (bg_p.get("bond") or "").strip()
            flaw = flaw or (bg_p.get("flaw") or "").strip()

    # Priority: victory feast > active downtime > breathing room due > needs only
    if victory_pending:
        return _victory_feast_block(victory_title, hunger, fatigue, bond)

    if phase in ("downtime", "preparation"):
        return _open_world_block(phase, pacing, hunger, fatigue, bond, ideal, flaw)

    if hook_resolutions >= HOOK_RESOLUTION_THRESHOLD:
        return _breathing_room_trigger(hook_resolutions, hunger, fatigue, bond, ideal, flaw)

    # No full downtime — surface needs quietly if present
    need_lines: List[str] = []
    if hunger:
        need_lines.append(
            f"HUNGER ({hours_since_meal}h since last meal): surface this naturally — "
            "a passing food smell, a rumbling stomach, an inn sign. Do not interrupt "
            "the active thread."
        )
    if fatigue:
        need_lines.append(
            f"FATIGUE ({hours_since_rest}h without rest): the body accumulates weight. "
            "A yawn, heavy eyelids, slower reactions. Surface without overriding the scene."
        )
    if need_lines:
        return "=== PHYSICAL NEEDS ===\n" + "\n".join(need_lines)

    return ""


# ---------------------------------------------------------------------------
# Block builders
# ---------------------------------------------------------------------------

def _breathing_room_trigger(
    hook_resolutions: int,
    hunger: bool,
    fatigue: bool,
    bond: str,
    ideal: str,
    flaw: str,
) -> str:
    lines = [
        "=== BREATHING ROOM ===",
        f"{hook_resolutions} investigation threads resolved without a break. "
        "The immediate pressure has eased. Open the world.",
        "",
        "DM MODE — OPEN WORLD (hold this until the player rests or starts the next lead):",
        "- DROP urgency. No closing window of pressure. The player has time — show them.",
        "- The world hums without them. Merchants are open. NPCs have their own afternoons.",
        "- Surface 1-2 of these as natural scene texture (never as a list or menu):",
        "  ▸ A merchant stall with specific goods visible — something relevant to the quest ahead",
        "  ▸ A training ground, weapons master, or skilled craftsperson at work",
        "  ▸ A tavern or inn: warmth, food on the fire, locals in mid-conversation",
        "  ▸ A quiet place where the bond NPC could be found or remembered",
        "  ▸ An unexplored part of the location — a street not yet walked, a building not entered",
    ]
    if bond:
        lines.append(f"  ▸ Personal moment: '{bond}' — is there an opportunity to act on this?")
    if flaw:
        lines.append(f"  ▸ The flaw under peace: '{flaw}' — peace is when flaws surface most clearly")
    lines += [
        "- Plant ONE soft hook — a rumor, an overheard fragment, a letter under a door.",
        "  Not urgent. Interesting. The next arc seeds itself in the quiet between things.",
        "- Meals: name the food. Name the drink. Let eating be a real moment, not a parenthetical.",
        "- Rest: describe what the body releases. What sleep sounds like in this place. "
        "What the morning light brings when there's no immediate threat.",
    ]
    if hunger:
        lines.append(
            "- HUNGER ACTIVE: the character hasn't eaten in too long. "
            "Let this be the first thing the scene offers — specific, warm, earned."
        )
    if fatigue:
        lines.append(
            "- FATIGUE ACTIVE: the character needs sleep. "
            "An inn room, a bedroll in a safe corner, a chair by a fire. Make rest feel earned."
        )
    return "\n".join(lines)


def _open_world_block(
    phase: str,
    pacing: dict,
    hunger: bool,
    fatigue: bool,
    bond: str,
    ideal: str,
    flaw: str,
) -> str:
    label = "PREPARATION WINDOW" if phase == "preparation" else "DOWNTIME"
    remaining = pacing.get("downtime_hours_remaining", 0)

    lines = [f"=== {label} ==="]

    if phase == "preparation" and remaining > 0:
        days = remaining // 24
        hours = remaining % 24
        time_str = f"{days}d {hours}h" if days else f"{hours}h"
        lines.append(
            f"The player has ~{time_str} of in-game time before the lead requires action. "
            "Use it. Show what a character does with time they've been given."
        )

    lines += [
        "",
        "DM MODE — OPEN WORLD:",
        "- No urgency. No closing window of threat. Describe the world at its own pace.",
        "- Available without being offered (surface as scene texture):",
        "  ▸ Equipment and supplies: a specific merchant, a specific item visible in the stall",
        "  ▸ Training: someone skilled nearby, a practice space, a book on a shelf",
        "  ▸ Social: NPCs have their own preoccupations — conversations start themselves",
        "  ▸ Personal: bond, flaw, ideal — peace is when these become visible",
        "  ▸ Exploration: the location has texture not seen under pressure",
        "  ▸ Rest and food: earned, specific, described with the weight they deserve",
        "- Plant soft hooks. The next arc begins as background noise — a name overheard, "
        "a notice on a board, a stranger asking an odd question. Not urgent. Present.",
    ]
    if bond:
        lines.append(f"- Bond opportunity: '{bond}' — downtime is when bonds get tended.")
    if flaw:
        lines.append(f"- Flaw surface: '{flaw}' — without urgency to hide behind, this shows.")
    if ideal:
        lines.append(f"- Ideal in peace: '{ideal}' — how does this express when no one is watching?")
    if hunger:
        lines.append("- HUNGER: resolve this first. Specific food. The smell of it. The texture. Rest follows.")
    if fatigue:
        lines.append("- FATIGUE: the character's body needs sleep. Describe the quality of rest — it matters here.")

    return "\n".join(lines)


def _victory_feast_block(
    victory_title: str,
    hunger: bool,
    fatigue: bool,
    bond: str,
) -> str:
    lines = [
        "=== VICTORY FEAST ===",
        f"TRIGGER: '{victory_title}' resolved. A celebration is natural and earned.",
        "",
        "FEAST DESIGN:",
        "- Someone offers to celebrate — an innkeeper, an ally NPC, the community. "
        "The offer is genuine. Let the player accept.",
        "- Name the food. Name the drink. Describe the noise and warmth of a room "
        "where something went right. This is specific, not generic.",
        "- Characters at the feast can share their bond, surface their flaw, act on "
        "their ideal — this is a rare safe moment. Let personality breathe.",
        "- ONE person at the feast mentions something that opens the next arc. "
        "Soft — an overheard fragment, a name dropped, a letter passed across the table. "
        "Not a briefing. The next loop opens before this one fully closes.",
        "- MOOD: earned rest. Warmth. The specific relief of having done something "
        "that mattered to someone. Do NOT rush past the feast — it is a scene.",
    ]
    if bond:
        lines.append(
            f"- Bond moment: '{bond}' — is this person at the feast, or is there a "
            "chance to send word, raise a cup in their name, think of them?"
        )
    if hunger:
        lines.append(
            "- The character is hungry. The first plate lands with satisfaction — let it."
        )
    if fatigue:
        lines.append(
            "- The character is exhausted. After the feast, sleep comes easily. "
            "Describe what deep, safe, earned rest feels like."
        )
    return "\n".join(lines)
