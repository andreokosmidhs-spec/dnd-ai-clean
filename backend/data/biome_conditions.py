"""Battlefield condition cards organised by biome.

Each condition is a *narrative description* — no hard mechanical values.
The player clicks a card, proposes how they want to use or react to the
environment, and the AI DM adjudicates based on:
  - The condition's description
  - The player's creative approach
  - The dice roll result

High roll (15+) → creative bonus (extra damage, advantage, special moment)
Mid  roll (8-14) → it works, no bonus / no penalty
Low  roll (1-7)  → risky gambit backfires (drop weapon, prone, worse position)
Nat 1            → DM invents an entertaining catastrophe
Nat 20           → DM invents a spectacular triumph
"""
from __future__ import annotations
from typing import Dict, List

# ── Schema for a single condition ────────────────────────────────────────────
# {
#   "key":         unique string id within the biome list
#   "title":       short card title
#   "description": narrative paragraph the player reads
#   "tags":        list of gameplay-hint tags (terrain, hazard, cover, etc.)
#   "biomes":      list of biome keys this condition belongs to
#   "rarity":      "common" | "uncommon" | "rare"
# }

CONDITIONS: List[Dict] = [

    # ─────────── FOREST ──────────────────────────────────────────────────────
    {
        "key": "forest_dense_undergrowth",
        "title": "Dense Undergrowth",
        "description": (
            "Thick brambles and tangled roots choke the forest floor. "
            "Movement is slow and noisy — but the foliage is deep enough to "
            "swallow a person whole if they know how to use it."
        ),
        "tags": ["terrain", "cover", "movement", "stealth"],
        "biomes": ["forest", "jungle"],
        "rarity": "common",
    },
    {
        "key": "forest_fallen_log",
        "title": "Massive Fallen Log",
        "description": (
            "A centuries-old tree has collapsed across the clearing, bark "
            "slick with moss and rot. It blocks the direct path but offers "
            "high ground to anyone brave enough to climb it mid-fight."
        ),
        "tags": ["terrain", "high_ground", "obstacle"],
        "biomes": ["forest", "jungle"],
        "rarity": "common",
    },
    {
        "key": "forest_canopy_gap",
        "title": "Shaft of Sunlight",
        "description": (
            "A break in the canopy sends a single column of bright light "
            "cutting through the gloom. Anything standing in it is clearly "
            "visible — illuminated, exposed, but also strangely dramatic."
        ),
        "tags": ["light", "visibility"],
        "biomes": ["forest"],
        "rarity": "uncommon",
    },

    # ─────────── PLAINS ──────────────────────────────────────────────────────
    {
        "key": "plains_tall_grass",
        "title": "Waist-High Grass",
        "description": (
            "The grass reaches your waist and sways in the wind. "
            "You can barely see past a few feet — neither can they. "
            "The rustling makes it impossible to move silently, "
            "but also impossible to track precisely."
        ),
        "tags": ["cover", "stealth", "visibility"],
        "biomes": ["plains", "grassland"],
        "rarity": "common",
    },
    {
        "key": "plains_open_killing_field",
        "title": "Open Killing Ground",
        "description": (
            "Nothing for miles in any direction. The sky is enormous and "
            "merciless. Every move you make is visible to everyone. "
            "There is nowhere to hide — only the courage to hold your ground "
            "or the speed to close the distance."
        ),
        "tags": ["visibility", "exposure", "ranged"],
        "biomes": ["plains", "grassland", "desert"],
        "rarity": "common",
    },

    # ─────────── MOUNTAIN / ROCKY ────────────────────────────────────────────
    {
        "key": "mountain_loose_scree",
        "title": "Loose Scree Slope",
        "description": (
            "The hillside is covered in small, sharp stones that shift "
            "underfoot without warning. Moving quickly is like trying to "
            "run on ball-bearings — but a clever fighter might send "
            "a cascade of rocks downhill deliberately."
        ),
        "tags": ["terrain", "hazard", "movement"],
        "biomes": ["mountain", "rocky"],
        "rarity": "common",
    },
    {
        "key": "mountain_ledge",
        "title": "Precarious Ledge",
        "description": (
            "One side drops away sharply into nothing. The edge is only a "
            "few feet from the combat. Anyone shoved or knocked off-balance "
            "has to make peace with gravity very quickly."
        ),
        "tags": ["hazard", "terrain", "fall"],
        "biomes": ["mountain", "rocky", "ruins"],
        "rarity": "uncommon",
    },
    {
        "key": "mountain_boulder",
        "title": "Enormous Boulder",
        "description": (
            "A man-sized boulder squats in the middle of the fighting space. "
            "It offers solid cover to whoever can get behind it first — "
            "but it also blocks sightlines, splits the battlefield, "
            "and could be climbed."
        ),
        "tags": ["cover", "terrain", "obstacle"],
        "biomes": ["mountain", "rocky", "ruins", "cave"],
        "rarity": "common",
    },

    # ─────────── CAVE / DUNGEON ──────────────────────────────────────────────
    {
        "key": "cave_stalactites",
        "title": "Stalactite Field",
        "description": (
            "Stone teeth hang from the ceiling like a frozen jaw. Some are "
            "already cracked. A well-placed strike — or a badly landed blow — "
            "might bring one crashing down. They don't discriminate."
        ),
        "tags": ["hazard", "terrain", "ceiling"],
        "biomes": ["cave", "dungeon"],
        "rarity": "uncommon",
    },
    {
        "key": "cave_underground_stream",
        "title": "Underground Stream",
        "description": (
            "A fast-moving stream of black water cuts through the chamber "
            "floor. It's knee-deep but shockingly cold. Crossing it is "
            "possible — staying upright while crossing is another matter."
        ),
        "tags": ["terrain", "hazard", "movement", "water"],
        "biomes": ["cave", "dungeon", "swamp"],
        "rarity": "uncommon",
    },
    {
        "key": "cave_narrow_passage",
        "title": "Choke-Point Passage",
        "description": (
            "The chamber narrows to a shoulder-width gap in one direction. "
            "One person can hold it against many — but one person can also "
            "be bottled up in it with nowhere to go."
        ),
        "tags": ["terrain", "chokepoint", "movement"],
        "biomes": ["cave", "dungeon"],
        "rarity": "common",
    },

    # ─────────── SWAMP / MARSH ───────────────────────────────────────────────
    {
        "key": "swamp_muddy_terrain",
        "title": "Clinging Mud",
        "description": (
            "The ground is a soup of dark mud that sucks at every step. "
            "Pulling your feet free takes real effort. The mud makes "
            "footing treacherous — but it also records every movement, "
            "and something thrown into it might sink and be lost forever."
        ),
        "tags": ["terrain", "movement", "hazard"],
        "biomes": ["swamp", "marsh", "beach"],
        "rarity": "common",
    },
    {
        "key": "swamp_mist",
        "title": "Thick Swamp Mist",
        "description": (
            "A low mist hangs over the water, thick enough to hide in but "
            "thin enough to move through. Sounds travel strangely here — "
            "your voice might come from the wrong direction entirely."
        ),
        "tags": ["visibility", "stealth", "sound"],
        "biomes": ["swamp", "marsh", "coastal"],
        "rarity": "uncommon",
    },

    # ─────────── DESERT ──────────────────────────────────────────────────────
    {
        "key": "desert_blinding_sun",
        "title": "Blinding Midday Sun",
        "description": (
            "The sun is directly overhead and everything glints. "
            "Polished armour, a blade, even sand crystals catch the light "
            "and throw it into eyes. A well-timed reflection could be "
            "a weapon — or an invitation."
        ),
        "tags": ["light", "visibility", "dazzle"],
        "biomes": ["desert"],
        "rarity": "common",
    },
    {
        "key": "desert_sandstorm_edge",
        "title": "Wall of Sand",
        "description": (
            "A curtain of driven sand advances across the flats. It hasn't "
            "hit yet — but you can see the brown wall rolling in. "
            "Whatever happens next will happen in seconds, before visibility "
            "drops to nothing."
        ),
        "tags": ["visibility", "hazard", "weather"],
        "biomes": ["desert"],
        "rarity": "rare",
    },
    {
        "key": "desert_ancient_pillar",
        "title": "Shattered Pillar",
        "description": (
            "A broken stone column juts from the sand at an angle, "
            "half-buried and crumbling. It's head-height and solid enough "
            "to hide behind — for now. The top could be stood on, "
            "if you're quick and the stone holds."
        ),
        "tags": ["cover", "terrain", "high_ground"],
        "biomes": ["desert", "ruins"],
        "rarity": "common",
    },

    # ─────────── COASTAL / BEACH ─────────────────────────────────────────────
    {
        "key": "coastal_crashing_waves",
        "title": "Crashing Shoreline",
        "description": (
            "Waves surge in from the sea with irregular rhythm — sometimes "
            "ankle-deep, sometimes chest-high. The timing is unpredictable. "
            "If you know when to move, the water becomes your ally; "
            "if you don't, it hits you like a wall."
        ),
        "tags": ["hazard", "terrain", "water", "movement"],
        "biomes": ["coastal", "beach"],
        "rarity": "common",
    },

    # ─────────── URBAN / CITY ────────────────────────────────────────────────
    {
        "key": "urban_market_stalls",
        "title": "Overturned Market Stalls",
        "description": (
            "Crates of fruit, bolts of cloth, and scattered merchant wares "
            "litter the cobblestones. Anything here is a potential weapon, "
            "a potential shield, or a tripping hazard — it depends on "
            "who gets there first."
        ),
        "tags": ["improvised_weapon", "cover", "terrain"],
        "biomes": ["urban", "market"],
        "rarity": "common",
    },
    {
        "key": "urban_rooftop_edge",
        "title": "Rooftop Edge",
        "description": (
            "You're three storeys up and the ledge is closer than comfort "
            "allows. The drop to the alley below is survivable — barely. "
            "The height advantage is real, and the threat of going over "
            "the edge is realer."
        ),
        "tags": ["high_ground", "hazard", "fall", "terrain"],
        "biomes": ["urban"],
        "rarity": "uncommon",
    },
    {
        "key": "urban_barrel_stack",
        "title": "Stack of Heavy Barrels",
        "description": (
            "A precarious tower of oak barrels stands to one side — "
            "full of something, given how heavily they sit. One hard shove "
            "and they roll. Where they end up is anyone's guess."
        ),
        "tags": ["improvised_weapon", "hazard", "terrain"],
        "biomes": ["urban", "tavern", "warehouse"],
        "rarity": "common",
    },

    # ─────────── TAVERN ──────────────────────────────────────────────────────
    {
        "key": "tavern_chandelier",
        "title": "Iron Chandelier",
        "description": (
            "A heavy iron chandelier hangs from the ceiling by a chain, "
            "candles still burning. It sways slightly. The chain anchor "
            "in the beam looks like it's held on through pure stubbornness "
            "and old wax."
        ),
        "tags": ["improvised_weapon", "hazard", "high_ground"],
        "biomes": ["tavern", "indoor"],
        "rarity": "uncommon",
    },
    {
        "key": "tavern_broken_furniture",
        "title": "Smashed Furniture",
        "description": (
            "Chairs, table legs, and shattered tankards are everywhere. "
            "The floor is slick with spilled ale. Anything not nailed "
            "down can be thrown, swung, or used as a makeshift shield — "
            "or you could slip on the ale at exactly the wrong moment."
        ),
        "tags": ["improvised_weapon", "terrain", "hazard"],
        "biomes": ["tavern", "indoor"],
        "rarity": "common",
    },

    # ─────────── RUINS / TEMPLE ──────────────────────────────────────────────
    {
        "key": "ruins_crumbling_ceiling",
        "title": "Crumbling Ceiling",
        "description": (
            "Cracks spider-web across the stone above you, and small "
            "pieces of masonry fall with every vibration. A loud enough "
            "sound — or a heavy enough impact — might bring more down. "
            "The ceiling doesn't pick sides."
        ),
        "tags": ["hazard", "terrain", "collapse"],
        "biomes": ["ruins", "dungeon", "cave"],
        "rarity": "uncommon",
    },
    {
        "key": "ruins_altar",
        "title": "Cracked Stone Altar",
        "description": (
            "A massive stone altar dominates the room, waist-high and "
            "solid as the mountain it was carved from. It's a barrier, "
            "a vantage point, and — if the old runes still hold any power — "
            "perhaps something more."
        ),
        "tags": ["cover", "high_ground", "magical", "obstacle"],
        "biomes": ["ruins", "dungeon", "temple"],
        "rarity": "rare",
    },

    # ─────────── GRAVEYARD ───────────────────────────────────────────────────
    {
        "key": "graveyard_headstones",
        "title": "Field of Headstones",
        "description": (
            "Rows of weathered stones, some toppled, some intact. "
            "The spacing is awkward — too close to sprint between, "
            "perfect to duck behind. The ground between them is soft, "
            "uneven, and in places suspiciously hollow-sounding."
        ),
        "tags": ["cover", "terrain", "movement", "hazard"],
        "biomes": ["graveyard", "necropolis"],
        "rarity": "common",
    },
    {
        "key": "graveyard_open_grave",
        "title": "Freshly Dug Grave",
        "description": (
            "A rectangular pit, freshly turned earth piled beside it. "
            "It's deep enough to stand in. Whether that's an opportunity "
            "or a threat depends entirely on who ends up in it."
        ),
        "tags": ["terrain", "hazard", "trap"],
        "biomes": ["graveyard", "necropolis"],
        "rarity": "uncommon",
    },

    # ─────────── ARCTIC / TUNDRA ─────────────────────────────────────────────
    {
        "key": "arctic_ice_sheet",
        "title": "Frozen Ice Sheet",
        "description": (
            "The ground is a mirror of dark ice beneath a thin layer of snow. "
            "Running is gambling. Sliding is possible — deliberate or not. "
            "A weapon dropped here won't stay where it lands."
        ),
        "tags": ["terrain", "hazard", "movement"],
        "biomes": ["arctic", "tundra", "mountain"],
        "rarity": "common",
    },
    {
        "key": "arctic_snowdrift",
        "title": "Deep Snowdrift",
        "description": (
            "A mound of compacted snow rises chest-high to one side. "
            "It's soft enough to dive into, solid enough to hide behind, "
            "and cold enough to be a very unpleasant surprise "
            "if someone gets shoved face-first into it."
        ),
        "tags": ["cover", "terrain", "hazard"],
        "biomes": ["arctic", "tundra"],
        "rarity": "common",
    },

    # ─────────── VOLCANIC ────────────────────────────────────────────────────
    {
        "key": "volcanic_lava_crack",
        "title": "Molten Fissure",
        "description": (
            "A crack in the basalt floor glows with orange light from below. "
            "The heat radiates up like an oven door left open. "
            "The crack is jumpable — barely — and anything that falls in "
            "is not coming back."
        ),
        "tags": ["hazard", "terrain", "fire", "fall"],
        "biomes": ["volcanic"],
        "rarity": "rare",
    },
    {
        "key": "volcanic_ash_cloud",
        "title": "Ash Cloud",
        "description": (
            "A drift of grey ash obscures part of the battlefield, stirred "
            "by the heat. Moving through it means emerging on the other side "
            "coughing and half-blind — but also completely unseen "
            "for the few seconds you're inside it."
        ),
        "tags": ["visibility", "stealth", "hazard"],
        "biomes": ["volcanic"],
        "rarity": "uncommon",
    },

    # ─────────── UNDERWATER ──────────────────────────────────────────────────
    {
        "key": "underwater_current",
        "title": "Strong Undercurrent",
        "description": (
            "The water doesn't sit still — an invisible force pulls "
            "sideways and down. Fighting it takes energy; using it "
            "takes nerve. Whoever reads the current first has "
            "a second or two of unexpected momentum."
        ),
        "tags": ["movement", "terrain", "water"],
        "biomes": ["underwater"],
        "rarity": "rare",
    },

    # ─────────── FEYWILD ─────────────────────────────────────────────────────
    {
        "key": "feywild_shifting_ground",
        "title": "Reality Hiccup",
        "description": (
            "The ground shimmers and then is somewhere slightly different. "
            "Distance means nothing here — you could be five feet away, "
            "you could be fifty. The rules that usually apply are "
            "suggestions at best."
        ),
        "tags": ["magical", "terrain", "movement", "reality"],
        "biomes": ["feywild"],
        "rarity": "rare",
    },
    {
        "key": "feywild_glamour_mirror",
        "title": "Glamour Mirror Pool",
        "description": (
            "A pool of still water on the forest floor reflects everything — "
            "but slightly wrong. Your reflection moves a half-second late. "
            "An attacker might strike at your reflection instead of you, "
            "or you might lose track of which one is real."
        ),
        "tags": ["magical", "visibility", "confusion"],
        "biomes": ["feywild"],
        "rarity": "rare",
    },

    # ─────────── SHADOWFELL ──────────────────────────────────────────────────
    {
        "key": "shadowfell_living_shadows",
        "title": "Living Shadows",
        "description": (
            "The shadows here move on their own. Not attacking — not yet — "
            "but sliding against the light in ways shadows shouldn't. "
            "Something that knows how to command them might find "
            "an ally in the dark."
        ),
        "tags": ["magical", "stealth", "darkness", "shadow"],
        "biomes": ["shadowfell"],
        "rarity": "rare",
    },

    # ─────────── SHIP DECK ───────────────────────────────────────────────────
    {
        "key": "ship_rigging",
        "title": "Tangled Rigging",
        "description": (
            "Ropes and lines hang everywhere — some taut, some loose. "
            "Climbing is possible if reckless. Swinging is possible if mad. "
            "Getting a line around someone's neck is possible if ruthless."
        ),
        "tags": ["terrain", "movement", "improvised_weapon", "high_ground"],
        "biomes": ["ship"],
        "rarity": "uncommon",
    },
    {
        "key": "ship_rolling_deck",
        "title": "Pitching Deck",
        "description": (
            "The deck lurches with every wave. Footing is a constant "
            "negotiation. The sea wants you horizontal. "
            "A badly timed roll could send anything — anyone — "
            "sliding toward the rail."
        ),
        "tags": ["terrain", "hazard", "movement"],
        "biomes": ["ship"],
        "rarity": "common",
    },

    # ─────────── CASTLE / FORTRESS ───────────────────────────────────────────
    {
        "key": "castle_battlement",
        "title": "Crenellated Battlements",
        "description": (
            "Stone merlons and embrasures line the wall-walk. "
            "Whoever holds the wall holds the advantage — high ground, "
            "cover, and the drop to the courtyard below as a final threat "
            "that cuts both ways."
        ),
        "tags": ["high_ground", "cover", "terrain", "fall"],
        "biomes": ["castle", "fortress"],
        "rarity": "uncommon",
    },
    {
        "key": "castle_portcullis",
        "title": "Half-Raised Portcullis",
        "description": (
            "The iron gate hangs halfway, chain still attached to the "
            "winch above. It's wide enough to roll under — barely. "
            "And the winch is right there, if someone wanted to "
            "drop several tons of iron at exactly the right moment."
        ),
        "tags": ["terrain", "obstacle", "hazard", "improvised_weapon"],
        "biomes": ["castle", "fortress", "dungeon"],
        "rarity": "rare",
    },
]

# ── Biome → condition key lookup ─────────────────────────────────────────────
BIOME_CONDITION_KEYS: Dict[str, List[str]] = {}
for _c in CONDITIONS:
    for _b in _c["biomes"]:
        BIOME_CONDITION_KEYS.setdefault(_b, []).append(_c["key"])

# ── By key lookup ─────────────────────────────────────────────────────────────
CONDITIONS_BY_KEY: Dict[str, Dict] = {c["key"]: c for c in CONDITIONS}


def conditions_for_biome(biome: str, max_count: int = 3) -> List[Dict]:
    """Return up to `max_count` condition dicts for the given biome."""
    keys = BIOME_CONDITION_KEYS.get(biome.lower(), [])
    return [CONDITIONS_BY_KEY[k] for k in keys[:max_count]]


def detect_biome(location_name: str) -> str:
    """Best-effort biome detection from a location name string."""
    loc = (location_name or "").lower()
    checks = [
        (["forest", "wood", "grove", "thicket", "copse"], "forest"),
        (["jungle", "rainforest", "tropical"], "jungle"),
        (["cave", "cavern", "grotto", "burrow"], "cave"),
        (["dungeon", "corridor", "cell", "crypt", "tomb", "catacombs", "vault", "sewer"], "dungeon"),
        (["swamp", "marsh", "bog", "fen", "mire"], "swamp"),
        (["desert", "dune", "wasteland", "arid", "salt flat"], "desert"),
        (["mountain", "peak", "ridge", "cliff", "highland", "rocky", "scree"], "mountain"),
        (["beach", "coast", "shore", "shoreline", "dunes"], "coastal"),
        (["ocean", "sea", "ship", "deck", "vessel", "galleon", "boat"], "ship"),
        (["tundra", "arctic", "glacier", "frozen", "ice", "snow"], "arctic"),
        (["volcanic", "volcano", "magma", "lava", "caldera", "ash"], "volcanic"),
        (["ruins", "temple", "shrine", "ancient", "crumbling", "abandoned"], "ruins"),
        (["graveyard", "cemetery", "necropolis", "burial", "tomb"], "graveyard"),
        (["feywild", "fey", "faerie", "enchanted", "magical grove"], "feywild"),
        (["shadowfell", "shadow", "underdark", "void"], "shadowfell"),
        (["underwater", "submerged", "lake bed", "sea floor"], "underwater"),
        (["tavern", "inn", "bar", "alehouse", "pub"], "tavern"),
        (["castle", "fortress", "citadel", "keep", "battlement", "rampart"], "castle"),
        (["city", "town", "village", "street", "alley", "market", "plaza", "square"], "urban"),
        (["plains", "grassland", "meadow", "field", "savanna", "steppe", "prairie"], "plains"),
    ]
    for keywords, biome in checks:
        if any(kw in loc for kw in keywords):
            return biome
    return "plains"  # default fallback
