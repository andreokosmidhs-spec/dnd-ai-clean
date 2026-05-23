"""
Encounter Composer Service — DM's brain for building balanced, narratively coherent encounters.

Takes location type, narrative tension, player level, and scouting intel as inputs,
and returns a fully composed encounter with stat blocks, difficulty rating, terrain
notes, objectives, and an intel report calibrated to what the player actually discovered.
"""
from __future__ import annotations

import logging
import random
from typing import Any, Dict, List, Optional, Tuple

from data.npc_tiers import NPC_TIERS, ENCOUNTER_TEMPLATES, get_tier, get_encounter_template

logger = logging.getLogger(__name__)

# ── XP budget per tier (simplified D&D 5e DMG values) ─────────────────────────
_TIER_XP: Dict[str, int] = {
    "commoner":   25,
    "gifted":    100,
    "specialist": 450,
    "commander": 1100,
    "mythic":    5000,
}

# ── Enemy count XP multiplier (DMG p. 82) ─────────────────────────────────────
def _xp_multiplier(count: int) -> float:
    if count == 1:   return 1.0
    if count == 2:   return 1.5
    if count <= 6:   return 2.0
    return 2.5

# ── Player level XP thresholds per level (easy / medium / hard / deadly) ──────
# Source: DMG table "XP Thresholds by Character Level"
_LEVEL_THRESHOLDS: Dict[int, Tuple[int, int, int, int]] = {
    1:  (25,   50,   75,   100),
    2:  (50,   100,  150,  200),
    3:  (75,   150,  225,  400),
    4:  (125,  250,  375,  500),
    5:  (250,  500,  750,  1100),
    6:  (300,  600,  900,  1400),
    7:  (350,  750,  1100, 1700),
    8:  (450,  900,  1400, 2100),
    9:  (550,  1100, 1600, 2400),
    10: (600,  1200, 1900, 2800),
    11: (800,  1600, 2400, 3600),
    12: (1000, 2000, 3000, 4500),
    13: (1100, 2200, 3400, 5100),
    14: (1250, 2500, 3800, 5700),
    15: (1400, 2800, 4300, 6400),
    16: (1600, 3200, 4800, 7200),
    17: (2000, 3900, 5900, 8800),
    18: (2100, 4200, 6300, 9500),
    19: (2400, 4900, 7300, 10900),
    20: (2800, 5700, 8500, 12700),
}

# ── Behavior tree IDs per tier ─────────────────────────────────────────────────
_TIER_TREE: Dict[str, str] = {
    "commoner":   "commoner",
    "gifted":     "orc",            # aggressive, simple
    "specialist": "generic_brute",  # guard_soldier not in DEFAULT_TREES; fallback
    "commander":  "guard_leader",   # faction_leader not in DEFAULT_TREES; use guard_leader
    "mythic":     "generic_brute",  # placeholder until mythic trees built
}

# ── Location types that allow commoners ────────────────────────────────────────
_COMMONER_ALLOWED_LOCATIONS = {
    "tavern_brawl", "bandit_road", "cult_ritual", "village_defense"
}

# ── Enemy name pools per encounter type & tier ────────────────────────────────
_NAME_POOLS: Dict[str, Dict[str, List[str]]] = {
    "tavern_brawl": {
        "commoner":   ["Tavern Drunk", "Bar Brawler", "Angry Patron", "Rowdy Local"],
        "gifted":     ["Tavern Brawler", "Bar Fighter", "Drunken Pit Fighter"],
    },
    "bandit_road": {
        "commoner":   ["Bandit Lookout", "Desperate Footpad", "Road Bandit"],
        "gifted":     ["Hardened Bandit", "Scarred Veteran", "Ruthless Cutthroat"],
        "specialist": ["Bandit Lieutenant", "Roadwarden Turncoat"],
    },
    "guard_post": {
        "specialist": ["City Guard", "Watch Soldier", "Gate Guard", "Armored Sentinel"],
        "commander":  ["Guard Captain", "Watch Commander", "Sergeant-at-Arms"],
    },
    "military_assault": {
        "gifted":     ["Military Conscript", "Green Recruit"],
        "specialist": ["Line Soldier", "Heavy Infantry", "Combat Engineer", "Crossbowman"],
        "commander":  ["Field Commander", "War Captain", "Lieutenant"],
    },
    "cult_ritual": {
        "commoner":   ["Cult Initiate", "Fanatic Villager", "Willing Sacrifice"],
        "gifted":     ["Devoted Acolyte", "Marked Cultist"],
        "specialist": ["Cult Guard", "Ritual Enforcer", "Blood Warden"],
        "commander":  ["High Cultist", "Ritual Master"],
    },
    "ancient_dungeon": {
        "specialist": ["Dungeon Warden", "Ancient Sentinel", "Accursed Guard"],
        "commander":  ["Dungeon Lord", "Ruined Captain"],
        "mythic":     ["Ancient Horror", "Dungeon Apex", "The Buried One"],
    },
    "village_defense": {
        "commoner":   ["Desperate Farmer", "Armed Villager", "Pitchfork Militia"],
        "gifted":     ["Village Elder", "Former Soldier", "Local Hunter"],
    },
    "mercenary_camp": {
        "gifted":     ["Mercenary Footsoldier", "Camp Grunt", "Hired Blade"],
        "specialist": ["Veteran Mercenary", "Elite Sellsword", "Battle-Tested Soldier"],
        "commander":  ["Merc Commander", "Camp Boss", "Contract Leader"],
    },
}

_DEFAULT_NAME_POOL: Dict[str, List[str]] = {
    "commoner":   ["Commoner"],
    "gifted":     ["Fighter"],
    "specialist": ["Soldier"],
    "commander":  ["Commander"],
    "mythic":     ["Ancient Horror"],
}

# ── Occupation assignments by encounter type ──────────────────────────────────
_COMMONER_OCCUPATIONS_BY_LOCATION: Dict[str, str] = {
    "tavern_brawl":    "barkeep",
    "bandit_road":     "laborer",
    "cult_ritual":     "default",
    "village_defense": "farmer",
}


def _get_enemy_name(location_type: str, tier: str, index: int) -> str:
    pool = _NAME_POOLS.get(location_type, {}).get(tier) or _DEFAULT_NAME_POOL.get(tier, ["Unknown"])
    return pool[index % len(pool)]


def _midpoint(lo: int, hi: int) -> int:
    return (lo + hi) // 2


def _generate_stat_block(
    tier_name: str,
    role_name: str,
    index: int,
    location_type: str,
) -> Dict[str, Any]:
    """Generate a stat block from the tier template midpoints."""
    tier = get_tier(tier_name)
    hp_lo, hp_hi = tier["hp_range"]
    ac_lo, ac_hi = tier["ac_range"]
    atk_lo, atk_hi = tier["attack_bonus_range"]

    hp = _midpoint(hp_lo, hp_hi)
    ac = _midpoint(ac_lo, ac_hi)
    atk_bonus = _midpoint(atk_lo, atk_hi)

    name = _get_enemy_name(location_type, tier_name, index)
    enemy_id = f"{tier_name}_{role_name}_{index}"

    occupation = _COMMONER_OCCUPATIONS_BY_LOCATION.get(location_type, "default") if tier_name == "commoner" else None

    enemy: Dict[str, Any] = {
        "id": enemy_id,
        "name": name,
        "tier": tier_name,
        "hp": hp,
        "max_hp": hp,
        "ac": ac,
        "attack_bonus": atk_bonus,
        "damage_die": tier["damage_die"],
        "damage_type": "slashing",
        "type": "humanoid",
        "behavior_tree_id": _TIER_TREE[tier_name],
        "abilities": {
            "str": 10, "dex": 10, "con": 10,
            "int": 10, "wis": 10, "cha": 10,
        },
        "proficiency_bonus": tier["proficiency_bonus"],
        "cr": tier["cr_range"][0],
        "conditions": [],
        "faction_id": None,
    }
    if occupation:
        enemy["occupation"] = occupation

    return enemy


def _compute_difficulty(enemies: List[Dict[str, Any]], player_level: int) -> Tuple[str, str]:
    """Return (difficulty_label, reason_string)."""
    raw_xp = sum(_TIER_XP.get(e.get("tier", "gifted"), 100) for e in enemies)
    multiplier = _xp_multiplier(len(enemies))
    adjusted_xp = int(raw_xp * multiplier)

    lvl = max(1, min(20, player_level))
    easy, medium, hard, deadly = _LEVEL_THRESHOLDS.get(lvl, _LEVEL_THRESHOLDS[1])

    if adjusted_xp < easy:
        label = "trivial"
        reason = f"Adjusted XP {adjusted_xp} is below Easy threshold ({easy}) for level {lvl}."
    elif adjusted_xp < medium:
        label = "easy"
        reason = f"Adjusted XP {adjusted_xp} falls in Easy range ({easy}–{medium - 1}) for level {lvl}."
    elif adjusted_xp < hard:
        label = "medium"
        reason = f"Adjusted XP {adjusted_xp} falls in Medium range ({medium}–{hard - 1}) for level {lvl}."
    elif adjusted_xp < deadly:
        label = "hard"
        reason = f"Adjusted XP {adjusted_xp} falls in Hard range ({hard}–{deadly - 1}) for level {lvl}."
    else:
        label = "deadly"
        reason = f"Adjusted XP {adjusted_xp} meets or exceeds Deadly threshold ({deadly}) for level {lvl}."

    return label, reason


def _tier_description(tier_name: str) -> str:
    tier = NPC_TIERS.get(tier_name, {})
    return tier.get("name", tier_name)


def _build_intel_report(
    intel_level: int,
    enemies: List[Dict[str, Any]],
    template: Dict[str, Any],
) -> Dict[str, Any]:
    """Build the intel report dict at the given scouting level (0–3)."""
    count = len(enemies)
    tier_counts: Dict[str, int] = {}
    for e in enemies:
        t = e.get("tier", "gifted")
        tier_counts[t] = tier_counts.get(t, 0) + 1

    tier_desc = ", ".join(
        f"{v} {_tier_description(k)}{'s' if v > 1 else ''}"
        for k, v in tier_counts.items()
    )
    commanders = [e for e in enemies if e.get("tier") == "commander"]
    has_commander = bool(commanders)

    # Special abilities hint (highest-tier enemy's signature mechanic)
    special_ability_hint: Optional[str] = None
    for tier_name in ("mythic", "commander", "specialist"):
        for e in enemies:
            if e.get("tier") == tier_name:
                tier_data = NPC_TIERS.get(tier_name, {})
                mechanics = tier_data.get("signature_mechanics", [])
                if mechanics:
                    special_ability_hint = mechanics[0].replace("_", " ").title()
                break
        if special_ability_hint:
            break

    reinf = template.get("reinforcements", False)

    if intel_level == 0:
        return {
            "visible": "You see figures in the shadows — you can't tell how many.",
            "detail": None,
            "commander_location": None,
            "special_abilities": None,
        }
    elif intel_level == 1:
        equip_desc = "ragged" if "commoner" in tier_counts else ("well-equipped" if "commander" in tier_counts else "organized")
        return {
            "visible": f"{count} armed figure{'s' if count != 1 else ''}, mix of {tier_desc}.",
            "detail": f"They look {equip_desc}.",
            "commander_location": None,
            "special_abilities": None,
        }
    elif intel_level == 2:
        return {
            "visible": f"{count} enemies: {tier_desc}.",
            "detail": (
                f"Full assessment: {tier_desc}. "
                + ("There appears to be a commander in the group. " if has_commander else "")
                + f"Terrain: {template.get('terrain_notes', 'standard terrain')}."
            ),
            "commander_location": "The commander stands at the back" if has_commander else None,
            "special_abilities": None,
        }
    else:  # intel_level == 3
        reinf_note = (
            " Reinforcements may arrive if an alarm is raised."
            if reinf else " No reinforcements expected."
        )
        return {
            "visible": f"{count} enemies: {tier_desc}.",
            "detail": (
                f"Full assessment: {tier_desc}. "
                + ("Commander directing the group. " if has_commander else "")
                + f"Terrain: {template.get('terrain_notes', 'standard terrain')}."
                + reinf_note
            ),
            "commander_location": "The commander stands at the back, directing the group" if has_commander else None,
            "special_abilities": special_ability_hint,
        }


def _narrative_objectives(enemies: List[Dict[str, Any]], location_type: str) -> List[str]:
    """Derive narrative objectives based on the enemy composition."""
    objectives: List[str] = []
    tier_names = {e.get("tier") for e in enemies}

    if "commander" in tier_names:
        objectives.append("Neutralize the commander to break enemy coordination.")
    if "specialist" in tier_names:
        objectives.append("Disrupt specialist formations before they can support each other.")
    if "commoner" in tier_names:
        objectives.append("Drive off panicking commoners or offer them a chance to surrender.")
    if "mythic" in tier_names:
        objectives.append("Discover the mythic creature's weakness before engaging fully.")

    if location_type == "guard_post":
        objectives.append("Prevent the bell from being rung — reinforcements arrive in round 3.")
    elif location_type == "cult_ritual":
        objectives.append("Disrupt the ritual at the altar before it completes.")
    elif location_type == "ancient_dungeon":
        objectives.append("Avoid triggering traps in the crumbling halls.")

    if not objectives:
        objectives.append("Defeat or rout all enemies.")

    return objectives


def _coherence_enforce(
    tier_mix: List[Tuple[str, int]],
    location_type: str,
    player_level: int,
    narrative_tension: str,
) -> List[Tuple[str, int]]:
    """
    Apply coherence rules:
    - Commander requires ≥2 specialists
    - Commoners only in allowed locations
    - Mythics only at level ≥8 + high/critical tension
    """
    result: List[Tuple[str, int]] = []
    tier_counts: Dict[str, int] = dict(tier_mix)

    # Strip commoners from disallowed locations
    if location_type not in _COMMONER_ALLOWED_LOCATIONS:
        tier_counts.pop("commoner", None)

    # Strip mythics if player too low or tension too low
    if "mythic" in tier_counts:
        if player_level < 8 or narrative_tension not in ("high", "critical"):
            tier_counts.pop("mythic", None)

    # Commander requires ≥2 specialists
    if "commander" in tier_counts and tier_counts["commander"] > 0:
        spec_count = tier_counts.get("specialist", 0)
        if spec_count < 2:
            # Either bump specialists or remove commander
            if spec_count == 0 and location_type not in ("guard_post", "military_assault", "mercenary_camp"):
                tier_counts.pop("commander", None)
            else:
                tier_counts["specialist"] = max(2, spec_count)

    for tier_name, count in tier_counts.items():
        if count > 0:
            result.append((tier_name, count))

    return result


def compose_encounter(
    location_type: str,
    narrative_tension: str,
    player_level: int,
    player_intel: int,
    trigger_type: str = "confrontation",
    enemy_library: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Compose a full encounter using DM composition rules.

    Returns:
    {
        "template": str,
        "enemies": [enemy_dict, ...],
        "difficulty": str,
        "difficulty_reason": str,
        "intel_report": dict,
        "terrain_notes": str,
        "reinforcements": bool,
        "objectives": [str, ...],
        "dm_notes": str,
    }
    """
    template = get_encounter_template(location_type)
    if template is None:
        # Fallback to a generic template
        template = {
            "description": f"Generic {location_type} encounter.",
            "tier_mix": [("gifted", 1, 3)],
            "trigger_types": ["confrontation"],
            "reinforcements": False,
            "terrain_notes": "Open ground. No special features.",
        }
        logger.warning("Unknown location_type '%s' — using generic fallback.", location_type)

    tier_mix_raw = template["tier_mix"]

    # ── Budget scaling by narrative_tension ────────────────────────────────────
    raw_counts: Dict[str, int] = {}
    for tier_name, count_min, count_max in tier_mix_raw:
        if narrative_tension == "low":
            count = count_min
        elif narrative_tension == "medium":
            count = (count_min + count_max) // 2
        elif narrative_tension == "high":
            count = count_max
        elif narrative_tension == "critical":
            count = count_max  # +1 extra applied below
        else:
            count = (count_min + count_max) // 2
        raw_counts[tier_name] = count

    # ── Player level scaling caps ──────────────────────────────────────────────
    # These caps limit enemy COUNTS, not tiers — the DM doesn't lower challenge,
    # it just keeps fights from being overwhelming at low level. A level-3 player
    # CAN face a commander; they should have scouted first.
    max_enemy_count: int
    if player_level <= 3:
        # Early levels: commoners and gifted only, capped at 4 total
        raw_counts = {k: v for k, v in raw_counts.items() if k in ("commoner", "gifted")}
        max_enemy_count = 4
    elif player_level <= 6:
        # Mid-low: allow specialists and commanders, cap at 6 total
        raw_counts = {k: v for k, v in raw_counts.items() if k in ("commoner", "gifted", "specialist", "commander")}
        max_enemy_count = 6
    elif player_level <= 10:
        # Mid: full tier access except mythic, cap at 8 total
        raw_counts = {k: v for k, v in raw_counts.items() if k in ("commoner", "gifted", "specialist", "commander")}
        max_enemy_count = 8
    else:
        # High level: all tiers including mythic
        max_enemy_count = 20

    # ── Coherence enforcement ──────────────────────────────────────────────────
    tier_mix_pairs = list(raw_counts.items())
    tier_mix_pairs = _coherence_enforce(tier_mix_pairs, location_type, player_level, narrative_tension)

    # Critical tension: +1 specialist or commander on top of maximum
    if narrative_tension == "critical":
        tier_mix_dict = dict(tier_mix_pairs)
        if "commander" in tier_mix_dict:
            tier_mix_dict["commander"] = tier_mix_dict["commander"] + 1
        elif "specialist" in tier_mix_dict:
            tier_mix_dict["specialist"] = tier_mix_dict["specialist"] + 1
        tier_mix_pairs = list(tier_mix_dict.items())

    # Cap total enemy count to max_enemy_count.
    # Strip lowest tiers first — preserve commanders and specialists.
    total_enemies = sum(c for _, c in tier_mix_pairs)
    if total_enemies > max_enemy_count:
        strip_order = ["commoner", "gifted", "specialist", "commander", "mythic"]
        tier_mix_dict = dict(tier_mix_pairs)
        while sum(tier_mix_dict.values()) > max_enemy_count:
            for t in strip_order:
                # Never reduce a tier below 1 if there's only 1 entry
                if tier_mix_dict.get(t, 0) > 1:
                    tier_mix_dict[t] -= 1
                    break
            else:
                # All tiers at 1 — must reduce from lowest to fit
                for t in strip_order:
                    if tier_mix_dict.get(t, 0) > 0:
                        tier_mix_dict[t] -= 1
                        break
        tier_mix_pairs = [(k, v) for k, v in tier_mix_dict.items() if v > 0]

    # ── Generate enemies ───────────────────────────────────────────────────────
    enemies: List[Dict[str, Any]] = []
    global_index = 0

    for tier_name, count in tier_mix_pairs:
        for i in range(count):
            # Try to find from enemy_library first
            matched = None
            if enemy_library:
                for eid, edata in enemy_library.items():
                    if edata.get("tier") == tier_name:
                        matched = dict(edata)
                        matched["id"] = f"{tier_name}_{eid}_{global_index}"
                        break

            if matched is None:
                matched = _generate_stat_block(
                    tier_name=tier_name,
                    role_name=tier_name,
                    index=global_index,
                    location_type=location_type,
                )
            enemies.append(matched)
            global_index += 1

    # ── Re-apply coherence post-generation ────────────────────────────────────
    # Commander without ≥2 specialists: remove commander if the constraint still fails
    commander_enemies = [e for e in enemies if e.get("tier") == "commander"]
    specialist_enemies = [e for e in enemies if e.get("tier") == "specialist"]
    if commander_enemies and len(specialist_enemies) < 2:
        enemies = [e for e in enemies if e.get("tier") != "commander"]

    # ── Intel report ──────────────────────────────────────────────────────────
    intel_level = max(0, min(3, player_intel))
    intel_report = _build_intel_report(intel_level, enemies, template)

    # ── Difficulty ─────────────────────────────────────────────────────────────
    difficulty, difficulty_reason = _compute_difficulty(enemies, player_level)

    # ── Objectives ─────────────────────────────────────────────────────────────
    objectives = _narrative_objectives(enemies, location_type)

    # ── DM notes ──────────────────────────────────────────────────────────────
    tier_summary = ", ".join(
        f"{c}x {t}" for t, c in
        sorted(((e.get("tier", "?"), 1) for e in enemies),
               key=lambda x: ["commoner","gifted","specialist","commander","mythic"].index(x[0]) if x[0] in ["commoner","gifted","specialist","commander","mythic"] else 99)
    )
    dm_notes = (
        f"Location: {location_type} | Tension: {narrative_tension} | "
        f"Player Level: {player_level} | Enemies: {len(enemies)} ({tier_summary}). "
        f"Difficulty: {difficulty}. "
        + (f"Trigger: {trigger_type}. " if trigger_type else "")
        + template.get("description", "")
    )

    return {
        "template": location_type,
        "enemies": enemies,
        "difficulty": difficulty,
        "difficulty_reason": difficulty_reason,
        "intel_report": intel_report,
        "terrain_notes": template.get("terrain_notes", ""),
        "reinforcements": template.get("reinforcements", False),
        "objectives": objectives,
        "dm_notes": dm_notes,
    }


def intel_from_investigation(investigation_total: int, encounter: Dict[str, Any]) -> Dict[str, Any]:
    """
    Given a post-composition investigation roll, return the intel report at the right level.
    DC 8 = intel 1, DC 12 = intel 2, DC 16 = intel 3.
    """
    if investigation_total >= 16:
        intel_level = 3
    elif investigation_total >= 12:
        intel_level = 2
    elif investigation_total >= 8:
        intel_level = 1
    else:
        intel_level = 0

    location_type = encounter.get("template", "")
    template = get_encounter_template(location_type) or {}
    enemies = encounter.get("enemies", [])

    report = _build_intel_report(intel_level, enemies, template)
    report["intel_level"] = intel_level
    return report


def describe_encounter_for_dm(encounter: Dict[str, Any]) -> str:
    """
    Returns a human-readable DM preparation summary.

    Example:
    'Guard Post: 4 Specialists + 1 Commander. Hard encounter for level 3 party.
     Commander at rear. Bell for reinforcements in round 3 if not silenced.
     Terrain: narrow corridor, arrow slits. No information given unless scouted.'
    """
    template_key = encounter.get("template", "Unknown")
    enemies = encounter.get("enemies", [])
    difficulty = encounter.get("difficulty", "unknown")
    terrain = encounter.get("terrain_notes", "")
    reinforcements = encounter.get("reinforcements", False)
    intel = encounter.get("intel_report", {})
    objectives = encounter.get("objectives", [])

    # Build enemy summary
    tier_counts: Dict[str, int] = {}
    for e in enemies:
        t = e.get("tier", "unknown")
        tier_counts[t] = tier_counts.get(t, 0) + 1

    tier_order = ["commoner", "gifted", "specialist", "commander", "mythic"]
    enemy_parts = []
    for t in tier_order:
        if t in tier_counts:
            c = tier_counts[t]
            label = NPC_TIERS.get(t, {}).get("name", t)
            enemy_parts.append(f"{c} {label}{'s' if c > 1 else ''}")

    enemy_summary = " + ".join(enemy_parts) if enemy_parts else "No enemies"

    lines = [
        f"{template_key.replace('_', ' ').title()}: {enemy_summary}.",
        f"Difficulty: {difficulty.upper()} encounter.",
    ]

    if difficulty in ("hard", "deadly"):
        lines.append("WARNING: High difficulty — consider party resources before engaging.")

    commander_loc = intel.get("commander_location")
    if commander_loc:
        lines.append(f"Commander: {commander_loc}.")

    if reinforcements:
        lines.append("Reinforcements: Available if alarm is raised. Silence the bell/signal in round 3.")

    if terrain:
        lines.append(f"Terrain: {terrain}")

    if objectives:
        lines.append("Objectives: " + " | ".join(objectives))

    scouted_desc = intel.get("visible", "")
    if scouted_desc and "shadows" in scouted_desc:
        lines.append("Intel: No information given unless party scouts first (DC 8/12/16 Investigation).")
    elif scouted_desc:
        lines.append(f"Intel available: {scouted_desc}")

    return "\n".join(lines)
