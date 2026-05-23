"""
Scene type profiles — each scene type defines the default tactical landscape.
Used by scene_intelligence_service.py to fill in gaps when LLM extraction is sparse.
"""
from __future__ import annotations
from typing import Dict, Any, List

# Each scene_type maps to a profile with:
#   encounter_template: str  — key into ENCOUNTER_TEMPLATES
#   people_archetypes: list  — typical groups present
#   exits: list              — typical exit options
#   cover: list              — available cover types
#   hazards: list            — environmental hazards
#   improvised_weapons: list — things that can be grabbed
#   light_level: str         — "bright" | "dim" | "dark"
#   conditions: list         — battlefield conditions to apply
#   reinforcement_hint: str | None  — who might join late
#   crowd_density: str       — "sparse" | "moderate" | "crowded"

SCENE_TYPES: Dict[str, Dict[str, Any]] = {

    "inn": {
        "encounter_template": "tavern_brawl",
        "people_archetypes": [
            {"group": "bar patrons", "count_range": (3, 8), "tier_hint": "commoner", "position": "bar and tables"},
            {"group": "card players", "count_range": (2, 4), "tier_hint": "gifted",   "position": "corner table"},
            {"group": "barkeep",     "count_range": (1, 1), "tier_hint": "commoner", "position": "behind bar"},
        ],
        "exits": ["main_door", "back_door", "window_east", "stairs_up"],
        "cover": ["heavy_tables", "bar_counter", "fireplace_pillar", "support_beam"],
        "hazards": ["open_fireplace", "oil_lanterns", "boiling_kettle_in_kitchen"],
        "improvised_weapons": ["bottles", "bar_stools", "iron_skillet", "firewood", "mug"],
        "light_level": "dim",
        "conditions": ["crowded", "dim_candlelight", "improvised_weapons_available"],
        "reinforcement_hint": "Kitchen staff (1-2 commoners) may emerge from the back after round 2",
        "crowd_density": "moderate",
    },

    "tavern": {
        "encounter_template": "tavern_brawl",
        "people_archetypes": [
            {"group": "drinking crowd", "count_range": (4, 10), "tier_hint": "commoner", "position": "scattered tables"},
            {"group": "barmaid",        "count_range": (1, 2),  "tier_hint": "commoner", "position": "floor"},
            {"group": "veteran drinker","count_range": (1, 2),  "tier_hint": "gifted",   "position": "corner"},
        ],
        "exits": ["main_door", "side_door", "window_west"],
        "cover": ["heavy_tables", "bar_counter", "stone_pillar"],
        "hazards": ["open_hearth", "scattered_oil_lamps"],
        "improvised_weapons": ["bottles", "stools", "tankard", "broken_chair_leg"],
        "light_level": "dim",
        "conditions": ["crowded", "dim_candlelight", "improvised_weapons_available", "drunk_crowd"],
        "reinforcement_hint": "Barkeep may send for the town watch after round 3",
        "crowd_density": "crowded",
    },

    "market": {
        "encounter_template": "bandit_road",
        "people_archetypes": [
            {"group": "market crowd",  "count_range": (5, 15), "tier_hint": "commoner",  "position": "scattered"},
            {"group": "merchant",      "count_range": (2, 5),  "tier_hint": "commoner",  "position": "stalls"},
            {"group": "market guard",  "count_range": (1, 3),  "tier_hint": "specialist","position": "patrol"},
        ],
        "exits": ["north_street", "south_alley", "west_gate", "between_stalls"],
        "cover": ["market_stalls", "stone_fountain", "merchant_cart", "awning_post"],
        "hazards": ["fire_braziers", "livestock", "merchant_carts_for_knockover"],
        "improvised_weapons": ["market_produce", "tool_handles", "rope", "chain"],
        "light_level": "bright",
        "conditions": ["crowded", "open_ground", "civilians_present"],
        "reinforcement_hint": "City watch patrols (2 specialists) may respond to noise within 3 rounds",
        "crowd_density": "crowded",
    },

    "guard_post": {
        "encounter_template": "guard_post",
        "people_archetypes": [
            {"group": "city guard",     "count_range": (3, 6), "tier_hint": "specialist", "position": "post"},
            {"group": "guard sergeant", "count_range": (1, 1), "tier_hint": "commander",  "position": "command_post"},
        ],
        "exits": ["main_gate", "side_passage"],
        "cover": ["gatehouse_wall", "guard_post_structure", "crates"],
        "hazards": ["portcullis", "arrow_slits", "alarm_bell"],
        "improvised_weapons": ["torch_sconce", "guard_equipment"],
        "light_level": "bright",
        "conditions": ["fortified_position", "chokepoint", "alarm_bell_present"],
        "reinforcement_hint": "Bell summons 4 more specialists in round 3 if not silenced",
        "crowd_density": "sparse",
    },

    "dungeon": {
        "encounter_template": "ancient_dungeon",
        "people_archetypes": [
            {"group": "dungeon guardians", "count_range": (2, 5), "tier_hint": "specialist", "position": "patrol"},
            {"group": "dungeon lord",       "count_range": (0, 1), "tier_hint": "commander",  "position": "deeper_room"},
        ],
        "exits": ["stone_door_north", "collapsed_passage", "iron_gate"],
        "cover": ["stone_pillars", "crumbling_walls", "sarcophagi"],
        "hazards": ["pressure_plates", "pit_traps", "crumbling_ceiling"],
        "improvised_weapons": ["loose_stone", "torch_bracket", "chain"],
        "light_level": "dark",
        "conditions": ["darkness", "confined_space", "echoing_acoustics"],
        "reinforcement_hint": "Creatures from adjacent rooms may investigate loud combat after round 4",
        "crowd_density": "sparse",
    },

    "forest_road": {
        "encounter_template": "bandit_road",
        "people_archetypes": [
            {"group": "bandits",  "count_range": (3, 6), "tier_hint": "gifted",   "position": "ambush_trees"},
            {"group": "bandit lookout", "count_range": (1, 2), "tier_hint": "gifted", "position": "tree_line"},
        ],
        "exits": ["road_north", "road_south", "forest_left", "forest_right"],
        "cover": ["large_trees", "fallen_log", "roadside_ditch", "boulder"],
        "hazards": ["muddy_ground", "low_visibility"],
        "improvised_weapons": ["branches", "rocks", "mud"],
        "light_level": "dim",
        "conditions": ["natural_cover", "ambush_terrain", "difficult_ground"],
        "reinforcement_hint": None,
        "crowd_density": "sparse",
    },

    "street": {
        "encounter_template": "bandit_road",
        "people_archetypes": [
            {"group": "passersby",  "count_range": (2, 6), "tier_hint": "commoner",  "position": "scattered"},
            {"group": "thugs",      "count_range": (2, 4), "tier_hint": "gifted",    "position": "ambush_point"},
        ],
        "exits": ["street_north", "street_south", "side_alley", "building_doorway"],
        "cover": ["market_cart", "stone_wall_alcove", "rain_barrel", "doorstep"],
        "hazards": ["cobblestone_trip", "crowds_blocking_movement"],
        "improvised_weapons": ["cobblestone", "rain_barrel", "cart_wheel"],
        "light_level": "dim",
        "conditions": ["urban_terrain", "civilians_present"],
        "reinforcement_hint": "Watch patrol may respond after 3 rounds",
        "crowd_density": "moderate",
    },

    "wilderness": {
        "encounter_template": "bandit_road",
        "people_archetypes": [
            {"group": "creatures", "count_range": (1, 4), "tier_hint": "gifted", "position": "scattered"},
        ],
        "exits": ["path_north", "path_south", "open_terrain"],
        "cover": ["boulders", "thick_brush", "ravine_edge"],
        "hazards": ["rough_terrain", "weather"],
        "improvised_weapons": ["rock", "branch"],
        "light_level": "bright",
        "conditions": ["open_terrain", "difficult_ground"],
        "reinforcement_hint": None,
        "crowd_density": "sparse",
    },

    "cult_shrine": {
        "encounter_template": "cult_ritual",
        "people_archetypes": [
            {"group": "cult members",   "count_range": (3, 6), "tier_hint": "commoner",  "position": "ritual_circle"},
            {"group": "cult enforcers", "count_range": (1, 3), "tier_hint": "specialist","position": "perimeter"},
            {"group": "high cultist",   "count_range": (1, 1), "tier_hint": "commander", "position": "altar"},
        ],
        "exits": ["ritual_chamber_door", "escape_passage"],
        "cover": ["stone_altar", "ritual_pillars", "incense_braziers"],
        "hazards": ["ritual_fire", "cursed_ground", "collapsing_ritual"],
        "improvised_weapons": ["ritual_knife", "candlestick", "ceremonial_urn"],
        "light_level": "dim",
        "conditions": ["ritual_active", "cursed_ground", "dim_firelight"],
        "reinforcement_hint": "Ritual completion (round 5) may summon additional entity",
        "crowd_density": "moderate",
    },

    "castle_hall": {
        "encounter_template": "military_assault",
        "people_archetypes": [
            {"group": "palace guard",   "count_range": (4, 8), "tier_hint": "specialist", "position": "patrol"},
            {"group": "captain",        "count_range": (1, 1), "tier_hint": "commander",  "position": "entrance"},
        ],
        "exits": ["main_hall_door", "side_corridor", "servants_passage", "balcony"],
        "cover": ["stone_columns", "tapestry_alcove", "heavy_furniture"],
        "hazards": ["alert_system", "portcullis"],
        "improvised_weapons": ["display_weapons_on_wall", "candelabra", "vase"],
        "light_level": "bright",
        "conditions": ["fortified_position", "alert_possible"],
        "reinforcement_hint": "Horn summons 4 guards from upper floors in round 2",
        "crowd_density": "sparse",
    },
}

# Tier hints from narrative language — keyword → tier inference
TIER_LANGUAGE_HINTS: Dict[str, str] = {
    # Commoner hints
    "farmer": "commoner", "merchant": "commoner", "innkeeper": "commoner",
    "barkeep": "commoner", "villager": "commoner", "peasant": "commoner",
    "drunk": "commoner", "bystander": "commoner", "civilian": "commoner",
    "patron": "commoner", "dockworker": "commoner", "laborer": "commoner",

    # Gifted hints
    "brawler": "gifted", "brute": "gifted", "veteran": "gifted",
    "scarred": "gifted", "fighter": "gifted", "pit fighter": "gifted",
    "rough": "gifted", "muscled": "gifted", "thug": "gifted",
    "duelist": "gifted", "wanderer": "gifted", "mercenary": "gifted",

    # Specialist hints
    "guard": "specialist", "soldier": "specialist", "watchman": "specialist",
    "trained": "specialist", "disciplined": "specialist", "patrol": "specialist",
    "formation": "specialist", "armored": "specialist", "equipped": "specialist",

    # Commander hints
    "captain": "commander", "sergeant": "commander", "commander": "commander",
    "leader": "commander", "officer": "commander", "lieutenant": "commander",
    "boss": "commander", "chief": "commander",
}

# Quest type → encounter flavor modifiers
QUEST_ENCOUNTER_MODIFIERS: Dict[str, Dict[str, Any]] = {
    "investigation": {
        "enemy_priority": "flee_with_info",   # enemies try to escape
        "loot_tags": ["documents", "ledger", "cipher", "key", "letter"],
        "faction_tags": ["informant", "guild_connected", "bribed"],
        "objective_hint": "One enemy will attempt to flee — they carry information you need",
        "commander_note": "The commander will sacrifice allies to escape with the evidence",
    },
    "bounty": {
        "enemy_priority": "protect_target",   # one named NPC is the bounty
        "loot_tags": ["bounty_token", "personal_effects", "wanted_item"],
        "faction_tags": ["criminal", "hired", "loyal_to_target"],
        "objective_hint": "The bounty target is present — allies will sacrifice themselves to protect them",
        "commander_note": "The target IS the commander — capture or eliminate them to end the fight",
    },
    "escort": {
        "enemy_priority": "target_escort",    # enemies focus the protected NPC
        "loot_tags": ["ambush_payment", "hired_contract", "assassin_token"],
        "faction_tags": ["assassin", "hired_killer", "interceptor"],
        "objective_hint": "Enemies are targeting your escort charge, not you — protect them first",
        "commander_note": "The commander will direct all attacks toward the escorted NPC",
    },
    "exploration": {
        "enemy_priority": "territorial",      # enemies defend their space
        "loot_tags": ["map_fragment", "explorer_notes", "artifact_piece"],
        "faction_tags": ["territorial", "guardian", "indigenous"],
        "objective_hint": "Enemies will fall back to defend a specific location — pressing them risks reinforcements",
        "commander_note": "The commander defends from a chokepoint — flanking is more effective than frontal assault",
    },
    "heist": {
        "enemy_priority": "raise_alarm",      # enemies try to trigger alert
        "loot_tags": ["security_key", "patrol_schedule", "safe_contents"],
        "faction_tags": ["security", "guard", "patrol"],
        "objective_hint": "Silence enemies quickly — noise triggers the alarm system",
        "commander_note": "The commander controls the alarm — neutralize them first or the whole complex activates",
    },
    "political": {
        "enemy_priority": "non_lethal",       # avoid killing, prefer capture/negotiation
        "loot_tags": ["political_document", "seal", "correspondence"],
        "faction_tags": ["noble", "diplomat", "faction_agent"],
        "objective_hint": "Killing here has political consequences — subdue if possible",
        "commander_note": "The commander may be open to negotiation at low HP — offer terms before the killing blow",
    },
    "main_quest": {
        "enemy_priority": "fight_to_death",
        "loot_tags": ["quest_item", "key_item", "artifact"],
        "faction_tags": ["villain_agent", "cult", "army"],
        "objective_hint": "These enemies know why you are here — expect no mercy and give none",
        "commander_note": "The commander carries a key quest item or information — do not let them die without taking it",
    },
    "default": {
        "enemy_priority": "fight_normally",
        "loot_tags": [],
        "faction_tags": [],
        "objective_hint": "",
        "commander_note": "",
    },
}


def get_scene_type(location_name: str) -> Dict[str, Any]:
    """Infer scene type from location name. Returns full profile."""
    name_lower = location_name.lower()
    for key in ("inn", "tavern", "market", "guard_post", "dungeon", "forest_road",
                "street", "wilderness", "cult_shrine", "castle_hall"):
        if key.replace("_", " ") in name_lower or key in name_lower:
            return {**SCENE_TYPES[key], "scene_type_key": key}
    # Default: street-level encounter
    return {**SCENE_TYPES["street"], "scene_type_key": "street"}


def get_quest_modifier(quest_type: str) -> Dict[str, Any]:
    """Return encounter modifier for a quest type."""
    return QUEST_ENCOUNTER_MODIFIERS.get(quest_type, QUEST_ENCOUNTER_MODIFIERS["default"])


def infer_tier_from_description(description: str) -> str:
    """Infer NPC tier from narrative language."""
    desc_lower = description.lower()
    for keyword, tier in TIER_LANGUAGE_HINTS.items():
        if keyword in desc_lower:
            return tier
    return "commoner"
