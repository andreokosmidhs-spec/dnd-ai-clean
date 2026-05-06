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


# -------------------- Intent Affinity --------------------
# Each event TYPE has a natural fit to the campaign's tone / focus / scope /
# danger axes. When previewing the "campaign deck" for a given intent we use
# these affinities to weight which types appear more / fewer.
# Values are 0..2 multipliers (1 = normal weight, 2 = strongly favored,
# 0 = excluded / very rare).

TYPE_INTENT_AFFINITY: Dict[str, Dict[str, Dict[str, float]]] = {
    # tone
    "tone": {
        "Grim":     {"encounter": 1.4, "hazard": 1.5, "mystery": 1.3, "faction": 1.2,
                     "discovery": 0.7, "cultural": 0.6, "lore": 1.0, "quest": 1.0},
        "Balanced": {"encounter": 1.0, "hazard": 1.0, "mystery": 1.0, "faction": 1.0,
                     "discovery": 1.0, "cultural": 1.0, "lore": 1.0, "quest": 1.0},
        "Heroic":   {"encounter": 1.1, "hazard": 0.7, "mystery": 0.9, "faction": 0.9,
                     "discovery": 1.4, "cultural": 1.2, "lore": 1.1, "quest": 1.4},
    },
    # focus
    "focus": {
        "Story":       {"faction": 1.5, "lore": 1.4, "quest": 1.5, "cultural": 1.3,
                        "mystery": 1.1, "discovery": 1.0, "encounter": 0.8, "hazard": 0.6},
        "Combat":      {"encounter": 2.0, "hazard": 1.2, "faction": 0.9, "quest": 1.0,
                        "discovery": 0.7, "cultural": 0.5, "mystery": 0.7, "lore": 0.5},
        "Intrigue":    {"faction": 2.0, "mystery": 1.6, "lore": 1.0, "cultural": 1.0,
                        "encounter": 0.7, "hazard": 0.6, "discovery": 0.8, "quest": 1.1},
        "Exploration": {"discovery": 2.0, "hazard": 1.4, "lore": 1.3, "cultural": 1.2,
                        "mystery": 1.1, "encounter": 1.0, "faction": 0.7, "quest": 1.0},
    },
    # scope (already filters via biome too)
    "scope": {
        "City":       {"faction": 1.3, "mystery": 1.2, "cultural": 1.2,
                       "encounter": 1.0, "discovery": 0.8, "hazard": 0.6,
                       "lore": 1.0, "quest": 1.1},
        "Wilderness": {"hazard": 1.5, "discovery": 1.4, "encounter": 1.2,
                       "cultural": 1.0, "mystery": 0.9, "faction": 0.6,
                       "lore": 0.8, "quest": 1.0},
        "Dungeon":    {"encounter": 1.6, "discovery": 1.4, "hazard": 1.2,
                       "mystery": 1.2, "lore": 0.9, "faction": 0.5,
                       "cultural": 0.4, "quest": 1.0},
        "Mixed":      {"faction": 1.0, "mystery": 1.0, "cultural": 1.0,
                       "encounter": 1.0, "discovery": 1.0, "hazard": 1.0,
                       "lore": 1.0, "quest": 1.0},
    },
    # danger
    "danger": {
        "Low":    {"encounter": 0.6, "hazard": 0.6, "mystery": 1.0, "faction": 1.0,
                   "discovery": 1.2, "cultural": 1.3, "lore": 1.1, "quest": 1.0},
        "Medium": {"encounter": 1.0, "hazard": 1.0, "mystery": 1.0, "faction": 1.0,
                   "discovery": 1.0, "cultural": 1.0, "lore": 1.0, "quest": 1.0},
        "High":   {"encounter": 1.5, "hazard": 1.5, "mystery": 1.0, "faction": 1.1,
                   "discovery": 0.9, "cultural": 0.7, "lore": 0.8, "quest": 1.1},
    },
}

# Difficulty bias by danger tier
DIFFICULTY_BY_DANGER: Dict[str, Dict[str, float]] = {
    "Low":    {"easy": 2.0, "medium": 1.0, "hard": 0.4},
    "Medium": {"easy": 1.0, "medium": 1.4, "hard": 1.0},
    "High":   {"easy": 0.5, "medium": 1.2, "hard": 2.0},
}


def intent_affinity_for(template: Dict, intent: Dict) -> float:
    """Compute the combined affinity multiplier for a template under a given
    intent dict {tone, focus, scope, danger}. Multiplies type-affinity across
    the 4 axes plus a small difficulty kicker."""
    weight = 1.0
    etype = template.get("type", "mystery")
    for axis in ("tone", "focus", "scope", "danger"):
        v = intent.get(axis)
        if not v:
            continue
        bucket = TYPE_INTENT_AFFINITY.get(axis, {}).get(v, {})
        weight *= bucket.get(etype, 1.0)
    # difficulty bias
    diff = template.get("difficulty", "medium")
    weight *= DIFFICULTY_BY_DANGER.get(intent.get("danger", "Medium"), {}).get(diff, 1.0)
    return weight


def preview_campaign_deck(intent: Dict, top_n: int = 24) -> List[Dict]:
    """Return the top-N catalog templates for this intent, sorted by affinity
    weight then type. Used by the frontend preview button."""
    scored = []
    for tpl in _CATALOG:
        w = intent_affinity_for(tpl, intent)
        if w <= 0.05:  # effectively excluded
            continue
        scored.append((w, tpl))
    scored.sort(key=lambda x: (-x[0], x[1]["type"], x[1]["title"]))
    out: List[Dict] = []
    for w, tpl in scored[:top_n]:
        out.append({
            "type": tpl["type"],
            "title": tpl["title"],
            "description": tpl["description"],
            "biomes": tpl.get("biomes") or ["any"],
            "requires": tpl.get("requires") or [],
            "difficulty": tpl.get("difficulty", "medium"),
            "affinity": round(w, 2),
        })
    return out


def deck_summary_for_intent(intent: Dict) -> Dict:
    """Return a summary view of the campaign deck under a given intent.
    Used by the preview button to show counts per type + the top picks."""
    deck = preview_campaign_deck(intent, top_n=24)
    counts: Dict[str, int] = {}
    for c in deck:
        counts[c["type"]] = counts.get(c["type"], 0) + 1
    return {
        "intent": intent,
        "type_counts": counts,
        "total_in_deck": len(deck),
        "total_in_catalog": len(_CATALOG),
        "cards": deck,
        "type_metadata": EVENT_TYPES,
    }


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
                    rng: Optional[random.Random] = None,
                    intent: Optional[Dict] = None) -> List[Dict]:
    """Return up to `count` templates that pass the region's tags. Distribution
    is biased toward variety: we sample at most one of each `type` until the
    types run out, then duplicates are allowed.

    When `intent` is provided, eligible candidates are weighted by their
    intent-affinity score so a Combat-Heroic-High-danger campaign drafts
    more encounters than a Story-Heroic-Low-danger one."""
    rng = rng or random.Random()
    eligible = [t for t in _CATALOG if _matches(t, region_tags)]
    if intent:
        # Weight-aware shuffle: sample without replacement using affinities.
        weighted = [(intent_affinity_for(t, intent), t) for t in eligible]
        weighted = [(max(w, 0.01), t) for w, t in weighted]
        # Probabilistic pick
        chosen_w: List[Dict] = []
        pool = weighted[:]
        while pool and len(chosen_w) < count * 3:
            total = sum(w for w, _ in pool)
            r = rng.random() * total
            acc = 0.0
            picked_idx = 0
            for i, (w, _) in enumerate(pool):
                acc += w
                if acc >= r:
                    picked_idx = i
                    break
            chosen_w.append(pool.pop(picked_idx)[1])
        eligible = chosen_w
    else:
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
