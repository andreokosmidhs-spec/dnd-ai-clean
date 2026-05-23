"""
NPC Tier System — D&D 5e NPC tier templates and encounter composition data.

Five tiers define the power/role spectrum of NPCs encountered in combat.
Each tier is a template dict with stat ranges, behavior profile, loot class,
and signature mechanics.

Also exports COMMONER_OCCUPATIONS (per-occupation stat overrides) and
ENCOUNTER_TEMPLATES (location-type → tier-mix encounter blueprints).
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple


NPC_TIERS: Dict[str, dict] = {
    "commoner": {
        "tier": 1,
        "name": "Commoner",
        "cr_range": ("0", "1/8"),
        "hp_range": (4, 8),
        "ac_range": (10, 11),
        "attack_bonus_range": (0, 1),
        "damage_die": "1d4",
        "proficiency_bonus": 2,
        "behavior_profile": "commoner",
        "flee_threshold": 0.5,    # panic check triggers
        "loot_class": "personal_effects",
        "xp_range": (10, 25),
        "signature_mechanics": ["panic_check", "mob_courage", "surrender", "crowd_scatter"],
        "description": "No combat training. Panics, flees or surrenders. Fights only when cornered.",
    },
    "gifted": {
        "tier": 2,
        "name": "Gifted",
        "cr_range": ("1/4", "1"),
        "hp_range": (10, 22),
        "ac_range": (12, 13),
        "attack_bonus_range": (2, 4),
        "damage_die": "1d8",
        "proficiency_bonus": 2,
        "behavior_profile": "aggressive",
        "flee_threshold": 0.25,
        "loot_class": "standard",
        "xp_range": (25, 200),
        "signature_mechanics": ["gift_trait"],
        "description": "Natural talent, zero tactics. One powerful trick, raw aggression.",
    },
    "specialist": {
        "tier": 3,
        "name": "Specialist",
        "cr_range": ("1", "4"),
        "hp_range": (22, 52),
        "ac_range": (14, 17),
        "attack_bonus_range": (4, 6),
        "damage_die": "1d8",
        "proficiency_bonus": 3,
        "behavior_profile": "tactical",
        "flee_threshold": 0.15,
        "loot_class": "military_gear",
        "xp_range": (200, 1100),
        "signature_mechanics": ["formation_bonus", "tactical_call", "suppression"],
        "description": "Trained, equipped, coordinated. Fights in formations. Gear matches role.",
    },
    "commander": {
        "tier": 4,
        "name": "Commander",
        "cr_range": ("3", "8"),
        "hp_range": (45, 110),
        "ac_range": (16, 18),
        "attack_bonus_range": (6, 8),
        "damage_die": "1d10",
        "proficiency_bonus": 4,
        "behavior_profile": "leader",
        "flee_threshold": 0.10,
        "loot_class": "quality_gear",
        "xp_range": (700, 3900),
        "signature_mechanics": ["command_aura", "tactical_order", "objective_focus", "interrupt_flee"],
        "description": "Multiplier. Command aura buffs all lower-tier allies. Has objectives beyond survival.",
    },
    "mythic": {
        "tier": 5,
        "name": "Mythic",
        "cr_range": ("8", "20"),
        "hp_range": (120, 400),
        "ac_range": (17, 22),
        "attack_bonus_range": (8, 14),
        "damage_die": "2d8",
        "proficiency_bonus": 5,
        "behavior_profile": "mythic",
        "flee_threshold": 0.0,
        "loot_class": "legendary",
        "xp_range": (3900, 25000),
        "signature_mechanics": ["damage_immunity_phase", "weakness_system", "phase_transition", "environmental_presence"],
        "description": "Supernatural puzzle boss. Immune until weakness found. Phases at HP thresholds.",
    },
}


# Occupation stat overrides for commoners
COMMONER_OCCUPATIONS: Dict[str, dict] = {
    "farmer":     {"weapon_name": "Pitchfork",     "damage_die": "1d6", "damage_type": "piercing",    "personal_effects": ["Seed Pouch",      "Worn Boot",       "Farmer's Almanac"]},
    "merchant":   {"weapon_name": "Walking Cane",  "damage_die": "1d4", "damage_type": "bludgeoning", "personal_effects": ["Merchant Ledger",  "Small Coin Purse", "Trade Seal"]},
    "barkeep":    {"weapon_name": "Bottle",        "damage_die": "1d4", "damage_type": "bludgeoning", "personal_effects": ["Tavern Key",       "IOU Note",        "Half-Full Flask"]},
    "fisherman":  {"weapon_name": "Gutting Knife", "damage_die": "1d4", "damage_type": "slashing",    "personal_effects": ["Fish Hook Set",    "Rope (10ft)",     "Smoked Fish"]},
    "laborer":    {"weapon_name": "Crowbar",       "damage_die": "1d6", "damage_type": "bludgeoning", "personal_effects": ["Work Gloves",      "Copper Coins",    "Lunch Pail"]},
    "dockworker": {"weapon_name": "Marlin Spike",  "damage_die": "1d4", "damage_type": "piercing",    "personal_effects": ["Dock Token",       "Rope (20ft)",     "Sailor's Knife"]},
    "guard":      {"weapon_name": "Club",          "damage_die": "1d4", "damage_type": "bludgeoning", "personal_effects": ["Guard Roster",     "Whistle",         "Sergeant's Orders"]},
    "default":    {"weapon_name": "Fist",          "damage_die": "1d3", "damage_type": "bludgeoning", "personal_effects": ["Tattered Cloth",   "Copper Coin",     "Lucky Stone"]},
}


# Encounter composition rules: location_type → tier_mix as list of (tier_name, count_min, count_max)
ENCOUNTER_TEMPLATES: Dict[str, dict] = {
    "tavern_brawl": {
        "description": "Bar fight. Commoners everywhere, maybe a gifted brawler.",
        "tier_mix": [("commoner", 3, 6), ("gifted", 0, 2)],
        "trigger_types": ["confrontation", "defense"],
        "reinforcements": False,
        "terrain_notes": "Tables and bottles as improvised cover. No escape for cornered targets.",
    },
    "bandit_road": {
        "description": "Road ambush. Mix of opportunists and a hardened veteran.",
        "tier_mix": [("commoner", 1, 3), ("gifted", 2, 4), ("specialist", 0, 1)],
        "trigger_types": ["ambush"],
        "reinforcements": False,
        "terrain_notes": "Trees and ditches for cover. Clear escape routes.",
    },
    "guard_post": {
        "description": "City guard response. Trained, coordinated, disciplined.",
        "tier_mix": [("specialist", 3, 5), ("commander", 1, 1)],
        "trigger_types": ["confrontation", "ambush"],
        "reinforcements": True,
        "terrain_notes": "Fortified position. Narrow chokepoints. Bell to call reinforcements.",
    },
    "military_assault": {
        "description": "Organized military force. Two commanders, multiple specialists.",
        "tier_mix": [("gifted", 1, 2), ("specialist", 4, 7), ("commander", 1, 2)],
        "trigger_types": ["raid", "confrontation"],
        "reinforcements": True,
        "terrain_notes": "Formation fighting. Archers in back, melee in front.",
    },
    "cult_ritual": {
        "description": "Cult ceremony. Fanatic commoners, trained guards, a leader, maybe something worse.",
        "tier_mix": [("commoner", 2, 5), ("gifted", 1, 2), ("specialist", 1, 3), ("commander", 1, 1)],
        "trigger_types": ["raid", "defense"],
        "reinforcements": False,
        "terrain_notes": "Ritual altar. Candles and braziers. Symbol of power in center.",
    },
    "ancient_dungeon": {
        "description": "Deep dungeon encounter. Specialists serving something ancient. Possibly mythic.",
        "tier_mix": [("specialist", 2, 4), ("commander", 0, 1), ("mythic", 0, 1)],
        "trigger_types": ["confrontation", "ambush"],
        "reinforcements": False,
        "terrain_notes": "Crumbling halls. Traps. Limited light.",
    },
    "village_defense": {
        "description": "Villagers driven to fight. Desperate commoners, no real soldiers.",
        "tier_mix": [("commoner", 4, 8), ("gifted", 1, 2)],
        "trigger_types": ["defense"],
        "reinforcements": False,
        "terrain_notes": "Pitchforks and farm tools. Home terrain advantage.",
    },
    "mercenary_camp": {
        "description": "Hired swords. Professional but mercenary — they'll flee if it goes badly.",
        "tier_mix": [("gifted", 2, 4), ("specialist", 2, 4), ("commander", 1, 1)],
        "trigger_types": ["ambush", "raid", "confrontation"],
        "reinforcements": False,
        "terrain_notes": "Fortified camp. Sentries on perimeter. Multiple escape routes.",
    },
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_tier(tier_name: str) -> dict:
    """Return the tier template dict for the given tier name (defaults to commoner)."""
    return NPC_TIERS.get(tier_name, NPC_TIERS["commoner"])


def get_occupation(occupation: str) -> dict:
    """Return commoner occupation overrides (defaults to 'default')."""
    return COMMONER_OCCUPATIONS.get(occupation.lower(), COMMONER_OCCUPATIONS["default"])


def get_encounter_template(template_key: str) -> Optional[dict]:
    """Return an encounter template by key, or None if not found."""
    return ENCOUNTER_TEMPLATES.get(template_key)
