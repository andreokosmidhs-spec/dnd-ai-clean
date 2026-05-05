"""Event card catalog & taxonomy.

8 event types — each has a unique color + border style for the UI:

  encounter   ⚔️  red,    solid-thick     — combat / threats
  faction     🏛️  purple, dashed          — politics / faction plots
  cultural    🪶  emerald, double         — race/culture-tied events
  discovery   🌟  amber,  solid-glow      — find something
  mystery     🔍  indigo, dotted          — unexplained
  hazard      🏔️  slate,  jagged-dashed   — environment / travel danger
  lore        📜  sky,    solid-thin      — history / knowledge
  quest       🎯  rose,   solid-bold      — major quest hook

Each catalog template carries:
  - type           : one of the 8 keys above
  - title / desc   : narrative text
  - biomes         : list of allowed biomes (or ['any'])
  - requires       : list of tags that MUST be present in the region for this
                     template to be eligible (subset match, AND semantics).
                     Tag examples: 'faction:criminal', 'race:elf',
                     'race:any-non-human'.
  - difficulty     : easy | medium | hard

Region tags are produced by `world_graph.region_tags(region)` from the
region's biome + present_factions + dominant_races. We do simple subset
matching for filtering.
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional


# -------------------- Event Type Metadata --------------------

EVENT_TYPES: Dict[str, Dict] = {
    "encounter": {
        "label": "Encounter",
        "icon": "⚔️",
        "color": "red",
        "border": "solid-thick",   # 4px solid, sharp
        "tone": "danger",
    },
    "faction": {
        "label": "Faction Plot",
        "icon": "🏛️",
        "color": "purple",
        "border": "dashed",        # 3px dashed
        "tone": "intrigue",
    },
    "cultural": {
        "label": "Cultural",
        "icon": "🪶",
        "color": "emerald",
        "border": "double",        # 4px double
        "tone": "human",
    },
    "discovery": {
        "label": "Discovery",
        "icon": "🌟",
        "color": "amber",
        "border": "solid-glow",    # 4px solid w/ inner glow
        "tone": "wonder",
    },
    "mystery": {
        "label": "Mystery",
        "icon": "🔍",
        "color": "indigo",
        "border": "dotted",        # 4px dotted
        "tone": "uncanny",
    },
    "hazard": {
        "label": "Travel Hazard",
        "icon": "🏔️",
        "color": "slate",
        "border": "jagged-dashed", # 3px dashed + offset shadow
        "tone": "environmental",
    },
    "lore": {
        "label": "Lore",
        "icon": "📜",
        "color": "sky",
        "border": "solid-thin",    # 2px solid clean
        "tone": "scholarly",
    },
    "quest": {
        "label": "Quest Hook",
        "icon": "🎯",
        "color": "rose",
        "border": "solid-bold",    # 5px solid
        "tone": "major",
    },
}


# -------------------- Static Template Catalog --------------------
# Tag conventions:
#   - 'race:<key>'       — specific race must be in dominant_races (or 'race:any')
#   - 'faction:<archetype>' — faction archetype must be in present_factions
#   - archetypes: criminal, merchant, military, religious, scholarly, arcane,
#                 noble, native, smuggler, guild

_CATALOG: List[Dict] = [
    # ===== ENCOUNTER (red) =====
    {"type": "encounter", "biomes": ["forest", "plains", "swamp"], "requires": [],
     "title": "Wolves at the Treeline",
     "description": "A pack circles too close to a roadhouse — bolder than wolves should be.",
     "difficulty": "easy"},
    {"type": "encounter", "biomes": ["urban", "coast"], "requires": ["faction:criminal"],
     "title": "Knife in the Alley",
     "description": "Cutters from the local crew are pressing tribute on stallholders. They've already cut one.",
     "difficulty": "medium"},
    {"type": "encounter", "biomes": ["mountain", "tundra"], "requires": [],
     "title": "Frostbitten Raiders",
     "description": "A war-band of half-frozen marauders has come down from the ice — empty-eyed, hungry.",
     "difficulty": "hard"},
    {"type": "encounter", "biomes": ["any"], "requires": ["faction:military"],
     "title": "Patrol Out of Bounds",
     "description": "An armed patrol crosses a border they shouldn't, in colors that aren't theirs.",
     "difficulty": "medium"},
    {"type": "encounter", "biomes": ["desert", "plains"], "requires": ["race:orc"],
     "title": "Tusker Outriders",
     "description": "Orc outriders have made tracks visible from the road — circling, taking the measure of travelers.",
     "difficulty": "medium"},

    # ===== FACTION PLOT (purple) =====
    {"type": "faction", "biomes": ["any"], "requires": ["faction:criminal"],
     "title": "A Quiet War",
     "description": "Two crews are bleeding each other in the alleys. A merchant wants a third party who can't be traced.",
     "difficulty": "medium"},
    {"type": "faction", "biomes": ["urban"], "requires": ["faction:noble"],
     "title": "The Sealed Letter",
     "description": "A noble's private courier is missing. The letter she carried would ruin three houses if read.",
     "difficulty": "medium"},
    {"type": "faction", "biomes": ["any"], "requires": ["faction:religious"],
     "title": "Heretic in the Seminary",
     "description": "A prelate wants someone outside the order to ask questions no insider would risk.",
     "difficulty": "medium"},
    {"type": "faction", "biomes": ["coast", "urban"], "requires": ["faction:smuggler"],
     "title": "The Diverted Hold",
     "description": "A ship's manifest doesn't match its hold. Someone in the docks knows; nobody is talking.",
     "difficulty": "medium"},
    {"type": "faction", "biomes": ["any"], "requires": ["faction:guild", "faction:merchant"],
     "title": "Cracked Charter",
     "description": "Two guilds are about to come to blows over a charter neither will produce. There's a third paper.",
     "difficulty": "medium"},
    {"type": "faction", "biomes": ["mountain", "underdark"], "requires": ["faction:scholarly"],
     "title": "An Expedition Gone Quiet",
     "description": "A scholar's expedition stopped sending word a fortnight back. Their patron is preparing a recovery purse.",
     "difficulty": "hard"},

    # ===== CULTURAL / RACE-TIED (emerald) =====
    {"type": "cultural", "biomes": ["forest", "fey"], "requires": ["race:elf"],
     "title": "Names of the Last Tree",
     "description": "An elven elder is naming the names of trees that fell this generation. Outsiders who help carry the count are remembered.",
     "difficulty": "easy"},
    {"type": "cultural", "biomes": ["mountain", "underdark"], "requires": ["race:dwarf"],
     "title": "The Stonewright's Apology",
     "description": "A dwarven hold owes a debt of stone to a smaller hold. The repayment ceremony needs witnesses from outside.",
     "difficulty": "easy"},
    {"type": "cultural", "biomes": ["plains", "urban"], "requires": ["race:halfling"],
     "title": "Long Table, Short Folk",
     "description": "A halfling family is preparing a six-day Long Table; an outsider has been invited to seat the unspoken-of guest.",
     "difficulty": "easy"},
    {"type": "cultural", "biomes": ["any"], "requires": ["race:tiefling"],
     "title": "Ash on the Lintel",
     "description": "A tiefling family has marked their door with ash — an old sign of inheritance dispute. They will hire only outsiders to mediate.",
     "difficulty": "medium"},
    {"type": "cultural", "biomes": ["plains", "desert", "tundra"], "requires": ["race:orc"],
     "title": "The Counted Bones",
     "description": "An orc clan is preparing the season's bone-count — a ritual of ancestor-naming that requires unfamiliar witnesses.",
     "difficulty": "easy"},
    {"type": "cultural", "biomes": ["any"], "requires": ["race:dragonborn"],
     "title": "Scale-Touch",
     "description": "A dragonborn elder is choosing successors. The trial is small but specific, and they want a witness who owes no clan.",
     "difficulty": "medium"},

    # ===== DISCOVERY (amber) =====
    {"type": "discovery", "biomes": ["forest", "swamp"], "requires": [],
     "title": "The Sunken Wagon",
     "description": "A trader's wagon, half-eaten by moss, sits at the bottom of a clear creek. The seal on its strongbox is unbroken.",
     "difficulty": "easy"},
    {"type": "discovery", "biomes": ["mountain", "underdark"], "requires": [],
     "title": "Veined Door",
     "description": "A door of silver-veined stone sits in a cliff face. No one local remembers a road that led there.",
     "difficulty": "medium"},
    {"type": "discovery", "biomes": ["coast"], "requires": [],
     "title": "Driftwood Map",
     "description": "A plank washed up at low tide bears charcoal markings — a coastline, a circled point, four crosses.",
     "difficulty": "easy"},
    {"type": "discovery", "biomes": ["any"], "requires": ["faction:arcane"],
     "title": "An Unfinished Sigil",
     "description": "A chalk circle on the cellar floor has been only half drawn, as though the caster was interrupted. The chalk is still warm.",
     "difficulty": "medium"},
    {"type": "discovery", "biomes": ["desert", "tundra"], "requires": [],
     "title": "Bone Garden",
     "description": "A grid of hand-sized bones is laid out across a flat — perfectly even, recently arranged, no tracks around it.",
     "difficulty": "medium"},

    # ===== MYSTERY (indigo) =====
    {"type": "mystery", "biomes": ["forest"], "requires": [],
     "title": "The Silent Grove",
     "description": "Birdsong has vanished from a stretch of woods; something is driving them off. The locals walk around, never through.",
     "difficulty": "easy"},
    {"type": "mystery", "biomes": ["urban"], "requires": [],
     "title": "Wrong Bell",
     "description": "The town bell rang at a quarter-hour no one tolls. Three witnesses, three different counts of how many strikes.",
     "difficulty": "medium"},
    {"type": "mystery", "biomes": ["plains", "coast"], "requires": [],
     "title": "Footprints to a Door",
     "description": "Footprints lead across an open field to a door standing alone in the grass. Behind the door: more grass.",
     "difficulty": "hard"},
    {"type": "mystery", "biomes": ["any"], "requires": ["faction:religious"],
     "title": "The Saint Who Should Be Dead",
     "description": "A saint canonized two centuries past has been seen in a marketplace — twice, by sober people.",
     "difficulty": "hard"},
    {"type": "mystery", "biomes": ["swamp", "shadow"], "requires": [],
     "title": "Names in Reverse",
     "description": "Travelers report their own names being called from the mire — but spoken backwards, the way a child sounds them out.",
     "difficulty": "medium"},

    # ===== TRAVEL HAZARD (slate) =====
    {"type": "hazard", "biomes": ["mountain", "tundra"], "requires": [],
     "title": "Ice-Fall Pass",
     "description": "The pass east is glazed under a fortnight of freezing rain. One slip is the cliff; the alternative is two days extra.",
     "difficulty": "medium"},
    {"type": "hazard", "biomes": ["swamp", "forest"], "requires": [],
     "title": "Wet Rot",
     "description": "A mile of road is sinking — wagons are bedding down to the axles. Travelers are paying for shoulders to push.",
     "difficulty": "easy"},
    {"type": "hazard", "biomes": ["desert"], "requires": [],
     "title": "Glasswind",
     "description": "Sandstorms are lifting flakes of obsidian; anyone caught in the open without cover comes back bleeding from the face.",
     "difficulty": "hard"},
    {"type": "hazard", "biomes": ["coast", "swamp"], "requires": [],
     "title": "Tide That Won't Turn",
     "description": "The tide came in last week and didn't go out. The fishermen are reading every word of every old book they own.",
     "difficulty": "medium"},
    {"type": "hazard", "biomes": ["plains"], "requires": [],
     "title": "Locust Crown",
     "description": "A swarm has banded itself into a moving wall a mile across. It's going somewhere. You're between.",
     "difficulty": "medium"},

    # ===== LORE / HISTORY (sky) =====
    {"type": "lore", "biomes": ["any"], "requires": ["faction:scholarly"],
     "title": "The Library That Was Burned Twice",
     "description": "A scholar shows a list of titles with two dates of destruction beside each. He wants names of survivors.",
     "difficulty": "medium"},
    {"type": "lore", "biomes": ["mountain", "underdark"], "requires": ["race:dwarf"],
     "title": "A Forgotten Hall",
     "description": "A drinking-song mentions a hall of the line that no one alive can place. The song is older than the line.",
     "difficulty": "hard"},
    {"type": "lore", "biomes": ["forest", "fey"], "requires": ["race:elf"],
     "title": "The Year of Two Springs",
     "description": "An elven matron remembers the year that came twice. She would tell the story for someone willing to listen long enough.",
     "difficulty": "easy"},
    {"type": "lore", "biomes": ["any"], "requires": ["faction:arcane"],
     "title": "The Apprentice's Last Page",
     "description": "A burned spellbook has one intact page. The hand is a famous one, the spell on it impossible.",
     "difficulty": "medium"},
    {"type": "lore", "biomes": ["urban", "coast"], "requires": ["faction:guild"],
     "title": "Charter Lost in the Fire",
     "description": "A guild's founding charter was lost in a fire that didn't happen — every record agrees there was no fire.",
     "difficulty": "hard"},

    # ===== QUEST HOOK (rose, major) =====
    {"type": "quest", "biomes": ["any"], "requires": [],
     "title": "The Vanished Caravan",
     "description": "A merchant family's flagship caravan has not arrived. They are paying triple for anyone who'll go look — by tomorrow night.",
     "difficulty": "medium"},
    {"type": "quest", "biomes": ["urban"], "requires": ["faction:noble"],
     "title": "The Heir Who Won't Be Heir",
     "description": "A young heir has refused the seat. The old lord wants the reasons — quietly, before the council session in three days.",
     "difficulty": "hard"},
    {"type": "quest", "biomes": ["forest", "mountain"], "requires": [],
     "title": "Beast Beneath the Bridge",
     "description": "Something is breaking the bridge nightly. Whoever fixes it three nights in a row keeps the toll for a year.",
     "difficulty": "medium"},
    {"type": "quest", "biomes": ["coast"], "requires": ["faction:smuggler"],
     "title": "The Buyer in the Storm",
     "description": "A buyer has paid up front for a delivery in weather no one will sail. The cargo is light. The price is heavier.",
     "difficulty": "hard"},
    {"type": "quest", "biomes": ["any"], "requires": ["faction:religious"],
     "title": "The Pilgrim Who Won't Arrive",
     "description": "A holy pilgrimage is one rider short — and the missing pilgrim's name is being whispered far from the road.",
     "difficulty": "medium"},
]


# -------------------- Filtering & Selection --------------------


def _matches(template: Dict, region_tags: set) -> bool:
    """Template eligible iff every tag in `requires` is present in region_tags
    (or 'race:any' / 'faction:any' is requested), AND the biome matches."""
    biomes = template.get("biomes") or ["any"]
    if "any" not in biomes and not (region_tags & {f"biome:{b}" for b in biomes}):
        return False
    for tag in template.get("requires") or []:
        if tag.endswith(":any-non-human"):
            # special: any non-human race present
            non_human = {t for t in region_tags if t.startswith("race:") and t != "race:human"}
            if not non_human:
                return False
            continue
        if tag.endswith(":any"):
            prefix = tag.split(":")[0] + ":"
            if not any(t.startswith(prefix) for t in region_tags):
                return False
            continue
        if tag not in region_tags:
            return False
    return True


def filter_eligible(region_tags: set, count: int = 5,
                    rng: Optional[random.Random] = None) -> List[Dict]:
    """Return up to `count` templates that pass the region's tags. Distribution
    is biased toward variety: we sample at most one of each `type` until the
    types run out, then duplicates are allowed."""
    rng = rng or random.Random()
    eligible = [t for t in _CATALOG if _matches(t, region_tags)]
    rng.shuffle(eligible)

    seen_types: set = set()
    chosen: List[Dict] = []
    leftovers: List[Dict] = []
    for t in eligible:
        if len(chosen) >= count:
            break
        if t["type"] in seen_types:
            leftovers.append(t)
            continue
        chosen.append(t)
        seen_types.add(t["type"])
    while len(chosen) < count and leftovers:
        chosen.append(leftovers.pop(0))
    return chosen


def list_event_types() -> List[Dict]:
    """For the frontend: send the type metadata as a list."""
    return [{"key": k, **v} for k, v in EVENT_TYPES.items()]
