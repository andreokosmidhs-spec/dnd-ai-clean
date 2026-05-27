"""
Scene Intelligence Service — extracts tactical pre-combat data from DM narration.

Runs after each narration response. Accumulates a scene_intelligence dict in
world_state that the encounter composer uses when combat triggers.

The DM never breaks immersion — spatial and tactical details are embedded
naturally in narration. This service reads those details and builds the
battlefield before the player ever swings a sword.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Tension score thresholds for DM embedding protocol
TENSION_CALM       = 0.0
TENSION_WATCH      = 0.25   # People and rough layout described
TENSION_RISING     = 0.45   # Positions, exits, notable objects described
TENSION_THREAT     = 0.65   # Threat signals, weapon hints, tactical tells
TENSION_IMMINENT   = 0.80   # Final beat — stage fully set

# Keywords that signal rising tension in narration.
# Use single words — multi-word phrases fail when the DM inserts articles/verbs between them
# (e.g. "eyes are narrowed" won't match "eyes narrowed" but will match "narrowed").
_TENSION_KEYWORDS = {
    "low": ["relaxed", "peaceful", "calm", "quiet", "friendly", "warm", "laughter", "singing"],
    "medium": [
        "watching", "glances", "tense", "suspicious", "nervous", "argument",
        "narrowed", "hilt",       # formerly "eyes narrowed", "hand on hilt"
        "scarred", "stares", "staring", "glare", "glaring",
        "uneasy", "wary", "unlatched", "edgy",
    ],
    "high": [
        "hostile", "threat", "warning", "blade", "weapon", "danger",
        "confrontation", "challenge", "grip", "clenched", "unsheathed",
    ],
    "imminent": [
        "draws", "lunges", "attacks", "combat", "initiative", "roll for",
        "fight", "aggression", "violence", "charges", "strikes",
    ],
}

# Simple tier recognition from narrative words
_TIER_WORDS = {
    "commoner": ["farmer", "merchant", "barkeep", "innkeeper", "patron", "drunk", "villager", "laborer", "dockworker", "civilian"],
    "gifted":   ["brawler", "brute", "scarred", "veteran", "muscled", "thug", "duelist", "rough-looking", "fighter", "mercenary"],
    "specialist": ["guard", "soldier", "watchman", "trained", "armored", "patrol", "disciplined", "formation"],
    "commander":  ["captain", "sergeant", "lieutenant", "commander", "officer", "leader", "boss", "chief"],
}


def _narration_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:16]


def _detect_tension_score_fast(narration: str, existing_score: float = 0.0) -> float:
    """
    Fast keyword-based tension detection. Returns 0.0–1.0.
    Never decreases existing score (tension only ratchets up during a scene).
    """
    text = narration.lower()
    score = existing_score

    for word in _TENSION_KEYWORDS["imminent"]:
        if word in text:
            score = max(score, 0.85)
            break
    for word in _TENSION_KEYWORDS["high"]:
        if word in text:
            score = max(score, 0.65)
            break
    for word in _TENSION_KEYWORDS["medium"]:
        if word in text:
            score = max(score, 0.35)
            break

    return min(score, 1.0)


_PERSON_NOUNS = frozenset({
    "man", "men", "woman", "women", "people", "person", "persons",
    "figure", "figures", "stranger", "strangers",
    "guard", "guards", "soldier", "soldiers", "warrior", "warriors",
    "patron", "patrons", "customer", "customers", "drinker", "drinkers",
    "mercenary", "mercenaries", "thug", "thugs", "bandit", "bandits",
    "cultist", "cultists", "brawler", "brawlers", "drunkard", "drunk",
    "fighter", "fighters", "rogue", "rogues", "mage", "mages",
    "dwarf", "elf", "orc", "human", "halfling",
    "knight", "knights", "rider", "riders", "traveler", "travelers",
})


def _extract_people_fast(narration: str) -> List[Dict[str, Any]]:
    """
    Fast regex-based people extraction. Finds number+group patterns.
    e.g. "three men playing cards" → {count:3, description:"men playing cards", tier:"gifted"}
    """
    from data.scene_types import infer_tier_from_description

    number_words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "a": 1, "an": 1,
        "several": 4, "a few": 3, "some": 3, "a group": 4,
        "a handful": 4, "a crowd": 8,
    }

    people = []
    text_lower = narration.lower()

    # Pattern: (number/word) + (description up to punctuation)
    pattern = r'\b(one|two|three|four|five|six|seven|eight|a|an|several|some|a few)\s+([a-z][a-z\s]{3,40}?)(?=[,\.;]|\s+(?:and|are|is|at|near|by|stand|sit|watch))'
    for m in re.finditer(pattern, text_lower):
        num_word = m.group(1)
        desc = m.group(2).strip()
        # Reject matches where the first word is a non-person noun (table, step, door, etc.)
        first_word = desc.split()[0] if desc.split() else ""
        desc_words = set(desc.split())
        if not desc_words.intersection(_PERSON_NOUNS):
            continue
        count = number_words.get(num_word, 1)
        tier = infer_tier_from_description(desc)
        # Try to get a position hint from context
        position = "unknown"
        context_after = narration[m.end():m.end()+60].lower()
        for loc in ("table", "bar", "corner", "door", "window", "wall", "counter", "stage", "back", "center"):
            if loc in context_after:
                position = loc
                break
        people.append({
            "description": desc,
            "count": count,
            "tier_hint": tier,
            "position": position,
            "confidence": "low",
        })

    return people


def _extract_exits_fast(narration: str) -> List[str]:
    """Extract exit mentions from narration."""
    exits = []
    text = narration.lower()
    exit_patterns = [
        ("door", "door"), ("window", "window"), ("gate", "gate"),
        ("staircase", "stairs"), ("stairs", "stairs"), ("alley", "alley"),
        ("passage", "passage"), ("corridor", "corridor"), ("exit", "exit"),
        ("back", "back_exit"), ("entrance", "entrance"),
    ]
    for keyword, exit_name in exit_patterns:
        if keyword in text and exit_name not in exits:
            exits.append(exit_name)
    return exits


def _extract_objects_fast(narration: str) -> Tuple[List[str], List[str]]:
    """Return (cover_items, improvised_weapons) found in narration."""
    text = narration.lower()

    cover_keywords = ["table", "bar", "counter", "pillar", "column", "wall",
                      "crate", "barrel", "stone", "altar", "stall", "cart"]
    weapon_keywords = ["bottle", "stool", "chair", "mug", "tankard", "torch",
                       "knife", "pitchfork", "tool", "candlestick", "poker",
                       "chain", "rope", "rock", "stone"]

    # Match keyword optionally followed by 's'/'es' (plurals), but not mid-word substring
    cover = [k for k in cover_keywords if re.search(r'\b' + k + r'(?:s|es)?\b', text)]
    weapons = [k for k in weapon_keywords if re.search(r'\b' + k + r'(?:s|es)?\b', text)]
    return cover, weapons


async def extract_scene_intelligence_llm(
    narration: str,
    existing_intel: Dict[str, Any],
    quest_context: Dict[str, Any],
    location_name: str,
) -> Dict[str, Any]:
    """
    Full LLM-based extraction. Runs asynchronously.
    Returns a scene_intelligence patch dict to merge into existing_intel.
    """
    import os
    try:
        import litellm
        model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

        prompt = f"""You are a D&D tactical scene analyst. Extract combat-relevant spatial intelligence from this DM narration.

NARRATION:
{narration}

LOCATION: {location_name}
ACTIVE QUEST TYPE: {quest_context.get('quest_type', 'unknown')}

Extract as JSON with EXACTLY this structure (use null for unknown fields):
{{
  "people": [
    {{"description": "string", "count": int, "tier_hint": "commoner|gifted|specialist|commander", "position": "string or null"}}
  ],
  "exits": ["string", ...],
  "cover": ["string", ...],
  "hazards": ["string", ...],
  "improvised_weapons": ["string", ...],
  "factions": [
    {{"group": "string", "count": int, "apparent_loyalty": "string or null"}}
  ],
  "tension_signals": ["string", ...],
  "notable_npcs": [
    {{"description": "string", "tier_hint": "string", "position": "string or null", "quest_relevant": bool}}
  ]
}}

Rules:
- Only extract what's EXPLICITLY stated or strongly implied in the narration
- tier_hint: use observable physical/behavioral clues
- position: where in the space (corner, door, bar, etc.)
- factions: distinct groups with apparent cohesion
- Do NOT invent details not present in the narration
- Return ONLY valid JSON, no commentary"""

        response = await litellm.acompletion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        logger.warning("LLM scene extraction failed: %s — using fast extraction only", e)
        return {}


def merge_scene_intel(existing: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge a new extraction patch into existing scene_intelligence.
    Lists are deduplicated. Scores are maxed (tension never decreases).
    """
    result = dict(existing)

    # Merge people: deduplicate by description
    existing_descs = {p["description"] for p in existing.get("people", [])}
    new_people = [p for p in patch.get("people", []) if p["description"] not in existing_descs]
    result["people"] = existing.get("people", []) + new_people

    # Merge lists (exits, cover, hazards, etc.) — deduplicate
    for key in ("exits", "cover", "hazards", "improvised_weapons", "tension_signals"):
        existing_set = set(existing.get(key, []))
        merged = list(existing_set | set(patch.get(key, [])))
        result[key] = merged

    # Merge factions
    existing_groups = {f["group"] for f in existing.get("factions", [])}
    new_factions = [f for f in patch.get("factions", []) if f["group"] not in existing_groups]
    result["factions"] = existing.get("factions", []) + new_factions

    # Merge notable_npcs
    existing_npc_descs = {n["description"] for n in existing.get("notable_npcs", [])}
    new_npcs = [n for n in patch.get("notable_npcs", []) if n["description"] not in existing_npc_descs]
    result["notable_npcs"] = existing.get("notable_npcs", []) + new_npcs

    return result


def update_scene_intelligence(
    narration: str,
    existing_intel: Dict[str, Any],
    quest_context: Dict[str, Any],
    location_name: str,
) -> Dict[str, Any]:
    """
    SYNCHRONOUS fast-path update. Runs immediately after narration.
    Returns updated scene_intelligence dict.

    The async LLM enrichment is called separately if tension warrants it.
    """
    from data.scene_types import get_scene_type

    # Initialize if empty
    if not existing_intel:
        scene_profile = get_scene_type(location_name)
        existing_intel = {
            "location_name": location_name,
            "scene_type": scene_profile.get("scene_type_key", "street"),
            "tension_score": 0.0,
            "people": [],
            "exits": list(scene_profile.get("exits", [])),
            "cover": list(scene_profile.get("cover", [])),
            "hazards": list(scene_profile.get("hazards", [])),
            "improvised_weapons": list(scene_profile.get("improvised_weapons", [])),
            "factions": [],
            "notable_npcs": [],
            "conditions": list(scene_profile.get("conditions", [])),
            "reinforcement_hint": scene_profile.get("reinforcement_hint"),
            "light_level": scene_profile.get("light_level", "bright"),
            "crowd_density": scene_profile.get("crowd_density", "moderate"),
            "tension_signals": [],
            "narration_count": 0,
            "quest_context": quest_context,
        }

    # Update tension (ratchets up only)
    old_tension = existing_intel.get("tension_score", 0.0)
    new_tension = _detect_tension_score_fast(narration, old_tension)
    existing_intel["tension_score"] = new_tension

    # Fast-extract people, exits, objects
    fast_people = _extract_people_fast(narration)
    fast_exits = _extract_exits_fast(narration)
    fast_cover, fast_weapons = _extract_objects_fast(narration)

    patch = {
        "people": fast_people,
        "exits": fast_exits,
        "cover": fast_cover,
        "improvised_weapons": fast_weapons,
        "factions": [],
        "notable_npcs": [],
        "tension_signals": [],
        "hazards": [],
    }
    merged = merge_scene_intel(existing_intel, patch)
    merged["narration_count"] = existing_intel.get("narration_count", 0) + 1
    merged["quest_context"] = quest_context

    return merged


def get_dm_embedding_instructions(scene_intel: Dict[str, Any]) -> str:
    """
    Returns DM instructions to embed tactical info naturally into narration,
    scaled by current tension score.

    These instructions are injected into the DM prompt — the DM weaves
    spatial intelligence into flavor text at the right tension level.
    """
    tension = scene_intel.get("tension_score", 0.0)
    location = scene_intel.get("location_name", "the location")
    quest_ctx = scene_intel.get("quest_context", {})
    quest_modifier = quest_ctx.get("objective_hint", "")

    if tension < TENSION_WATCH:
        return ""  # Peaceful — no tactical embedding needed

    lines = ["SCENE INTELLIGENCE EMBEDDING PROTOCOL (weave naturally into narration):"]

    if tension >= TENSION_WATCH:
        # Describe people count and rough physicality
        people = scene_intel.get("people", [])
        if people:
            people_summary = "; ".join(
                f"{p['count']} {p['description']} ({p['tier_hint']}) near {p.get('position','unknown')}"
                for p in people[:4]
            )
            lines.append(f"People present (describe naturally as atmosphere): {people_summary}")
        else:
            lines.append("Mention how many people are present and roughly how they carry themselves (rough, disciplined, afraid, etc.)")

    if tension >= TENSION_RISING:
        # Establish positions and exits
        exits = scene_intel.get("exits", [])
        cover = scene_intel.get("cover", [])
        if exits:
            lines.append(f"Exits the player could notice naturally: {', '.join(exits[:3])}")
        if cover:
            lines.append(f"Cover/obstacles to weave in as description: {', '.join(cover[:3])}")

    if tension >= TENSION_THREAT:
        # Threat signals and weapon tells
        weapons = scene_intel.get("improvised_weapons", [])
        hazards = scene_intel.get("hazards", [])
        if weapons:
            lines.append(f"Improvised weapons in the scene (mention as props, not threats): {', '.join(weapons[:3])}")
        if hazards:
            lines.append(f"Environmental hazards to hint at (natural description): {', '.join(hazards[:2])}")
        npcs = scene_intel.get("notable_npcs", [])
        for npc in npcs:
            if npc.get("tier_hint") in ("specialist", "commander"):
                lines.append(f"Notable threat: '{npc['description']}' — describe their bearing/movement as a tell")

    if tension >= TENSION_IMMINENT:
        # Final beat — everything is on the table
        reinforcement = scene_intel.get("reinforcement_hint")
        if reinforcement:
            lines.append(f"Reinforce possibility hint (subtle): {reinforcement}")
        if quest_modifier:
            lines.append(f"Quest objective signal: {quest_modifier}")
        lines.append("This is the final narration beat before combat. The battlefield should feel fully established.")

    lines.append("TONE: These are flavor details, NOT tactical briefings. Weave them as sensory observations.")
    lines.append("NEVER say 'the exit is 12 feet away' — say 'the back door hangs ajar in the far wall'.")

    return "\n".join(lines)


def scene_intel_to_encounter_input(
    scene_intel: Dict[str, Any],
    player_level: int,
    player_intel_level: int = 0,
) -> Dict[str, Any]:
    """
    Convert accumulated scene_intelligence into encounter composer inputs.

    Returns a dict with:
      location_type, narrative_tension, player_level, player_intel,
      trigger_type, scene_people, quest_modifier, conditions, reinforcements
    """
    from data.scene_types import get_quest_modifier

    tension = scene_intel.get("tension_score", 0.5)
    quest_ctx = scene_intel.get("quest_context", {})
    quest_type = quest_ctx.get("quest_type", "default")

    if tension >= 0.85:
        narrative_tension = "critical"
    elif tension >= 0.65:
        narrative_tension = "high"
    elif tension >= 0.4:
        narrative_tension = "medium"
    else:
        narrative_tension = "low"

    # Infer location type from scene type
    scene_type = scene_intel.get("scene_type", "street")
    from data.scene_types import SCENE_TYPES
    location_type = SCENE_TYPES.get(scene_type, {}).get("encounter_template", "bandit_road")

    # Infer trigger type from tension signals
    signals = " ".join(scene_intel.get("tension_signals", [])).lower()
    if "ambush" in signals or "surprise" in signals:
        trigger_type = "ambush"
    elif "defense" in signals or "protect" in signals:
        trigger_type = "defense"
    elif "raid" in signals:
        trigger_type = "raid"
    else:
        trigger_type = "confrontation"

    quest_modifier = get_quest_modifier(quest_type)

    # Count people and estimate enemy pool from scene observations
    scene_people: List[Dict[str, Any]] = []
    for person in scene_intel.get("people", []):
        scene_people.append({
            "description": person["description"],
            "count": person["count"],
            "tier": person["tier_hint"],
            "position": person.get("position", "unknown"),
        })

    return {
        "location_type": location_type,
        "narrative_tension": narrative_tension,
        "player_level": player_level,
        "player_intel": player_intel_level,
        "trigger_type": trigger_type,
        "scene_people": scene_people,
        "quest_modifier": quest_modifier,
        "conditions": scene_intel.get("conditions", []),
        "reinforcements": bool(scene_intel.get("reinforcement_hint")),
        "reinforcement_hint": scene_intel.get("reinforcement_hint"),
        "light_level": scene_intel.get("light_level", "bright"),
        "exits": scene_intel.get("exits", []),
        "cover": scene_intel.get("cover", []),
        "improvised_weapons": scene_intel.get("improvised_weapons", []),
    }


def build_encounter_from_scene(
    scene_intel: Dict[str, Any],
    player_level: int,
    player_intel_level: int,
) -> Dict[str, Any]:
    """
    Top-level bridge: scene_intelligence → full composed encounter.
    Calls encounter_composer_service.compose_encounter with scene context.
    """
    from services.encounter_composer_service import compose_encounter

    enc_input = scene_intel_to_encounter_input(scene_intel, player_level, player_intel_level)

    encounter = compose_encounter(
        location_type=enc_input["location_type"],
        narrative_tension=enc_input["narrative_tension"],
        player_level=player_level,
        player_intel=player_intel_level,
        trigger_type=enc_input["trigger_type"],
    )

    # Enrich with scene-specific data
    encounter["location_type"] = enc_input["location_type"]
    encounter["scene_conditions"] = enc_input["conditions"]
    encounter["reinforcement_hint"] = enc_input["reinforcement_hint"]
    encounter["exits"] = enc_input["exits"]
    encounter["cover"] = enc_input["cover"]
    encounter["improvised_weapons"] = enc_input["improvised_weapons"]
    encounter["light_level"] = enc_input["light_level"]
    encounter["quest_modifier"] = enc_input["quest_modifier"]
    encounter["scene_people"] = enc_input["scene_people"]

    # Apply quest modifier to objectives
    q = enc_input["quest_modifier"]
    if q.get("objective_hint"):
        encounter["objectives"] = [q["objective_hint"]] + encounter.get("objectives", [])
    if q.get("commander_note"):
        encounter["objectives"].append(q["commander_note"])

    logger.info(
        "Scene -> Encounter: %s (%s tension, %d enemies, %s difficulty)",
        enc_input["location_type"], enc_input["narrative_tension"],
        len(encounter.get("enemies", [])), encounter.get("difficulty", "?"),
    )

    return encounter
