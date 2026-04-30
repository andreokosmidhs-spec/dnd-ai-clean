"""Biome catalog — every location card gets classified into one of these
biomes at creation. The biome determines:

  - The card's accent color (so a Forest place looks different from a
    Desert place at a glance, even though both share the "location" type).
  - The natural resources / animals / monsters the player can encounter
    or harvest there.
  - Modifiers to Survival and Nature check DCs (forests are easy to
    forage in; the Underdark is brutally hard).

The frontend mirrors `BIOMES_PUBLIC` so the UI doesn't need to keep its
own copy in sync.
"""

from __future__ import annotations

from typing import Dict, List, TypedDict


class BiomeDef(TypedDict):
    key: str
    label: str
    icon: str            # lucide-react icon name (used by the frontend)
    accent: str          # tailwind gradient `from-… to-…` (header color)
    chip: str            # tailwind classes for the biome chip on cards
    survival_dc_mod: int # +N harder, -N easier (default 10 = baseline)
    nature_dc_mod: int
    resources: List[str]
    animals: List[str]
    monsters: List[str]


BIOMES: Dict[str, BiomeDef] = {
    "forest": {
        "key": "forest",
        "label": "Forest",
        "icon": "Trees",
        "accent": "from-emerald-600 to-emerald-800",
        "chip": "bg-emerald-500/20 text-emerald-300 border-emerald-400/50",
        "survival_dc_mod": -2,    # easy to forage
        "nature_dc_mod": -1,
        "resources": ["timber", "wild herbs", "berries", "mushrooms", "honey"],
        "animals": ["deer", "boar", "rabbits", "owls", "foxes"],
        "monsters": ["wolves", "dire wolves", "owlbears", "treants", "goblins"],
    },
    "plains": {
        "key": "plains",
        "label": "Plains",
        "icon": "Wind",
        "accent": "from-yellow-500 to-amber-700",
        "chip": "bg-yellow-500/20 text-yellow-300 border-yellow-400/50",
        "survival_dc_mod": -1,
        "nature_dc_mod": 0,
        "resources": ["grain", "wild grass", "flax", "clay"],
        "animals": ["bison", "horses", "antelope", "hawks", "field mice"],
        "monsters": ["bandits", "manticores", "gnolls", "hippogriffs"],
    },
    "desert": {
        "key": "desert",
        "label": "Desert",
        "icon": "Sun",
        "accent": "from-amber-500 to-orange-700",
        "chip": "bg-amber-500/20 text-amber-300 border-amber-400/50",
        "survival_dc_mod": +3,    # brutal heat & no water
        "nature_dc_mod": +1,
        "resources": ["cactus water", "salt", "obsidian", "scorpion venom"],
        "animals": ["camels", "vultures", "lizards", "scorpions", "snakes"],
        "monsters": ["sand worms", "djinn", "mummies", "basilisks"],
    },
    "mountain": {
        "key": "mountain",
        "label": "Mountain",
        "icon": "Mountain",
        "accent": "from-stone-500 to-stone-800",
        "chip": "bg-stone-500/20 text-stone-300 border-stone-400/50",
        "survival_dc_mod": +2,
        "nature_dc_mod": 0,
        "resources": ["iron", "silver", "gemstones", "alpine herbs"],
        "animals": ["mountain goats", "eagles", "ibex", "snow leopards"],
        "monsters": ["giants", "rocs", "wyverns", "trolls", "duergar"],
    },
    "swamp": {
        "key": "swamp",
        "label": "Swamp",
        "icon": "Droplet",
        "accent": "from-teal-700 to-emerald-900",
        "chip": "bg-teal-500/20 text-teal-300 border-teal-400/50",
        "survival_dc_mod": +2,
        "nature_dc_mod": +1,
        "resources": ["peat", "swamp herbs", "leech bile", "rare fungi"],
        "animals": ["alligators", "frogs", "herons", "leeches", "snakes"],
        "monsters": ["hags", "lizardfolk", "shambling mounds", "will-o-wisps"],
    },
    "coast": {
        "key": "coast",
        "label": "Coast",
        "icon": "Waves",
        "accent": "from-sky-500 to-cyan-800",
        "chip": "bg-sky-500/20 text-sky-300 border-sky-400/50",
        "survival_dc_mod": 0,
        "nature_dc_mod": 0,
        "resources": ["fish", "seaweed", "salt", "pearls", "driftwood"],
        "animals": ["seabirds", "crabs", "seals", "schooling fish"],
        "monsters": ["sahuagin", "merrow", "kraken", "pirates", "sirens"],
    },
    "tundra": {
        "key": "tundra",
        "label": "Tundra",
        "icon": "Snowflake",
        "accent": "from-cyan-300 to-blue-700",
        "chip": "bg-cyan-300/20 text-cyan-200 border-cyan-300/50",
        "survival_dc_mod": +3,
        "nature_dc_mod": +1,
        "resources": ["ice", "lichen", "fur pelts", "mammoth ivory"],
        "animals": ["wolves", "caribou", "polar bears", "arctic foxes"],
        "monsters": ["yeti", "frost giants", "ice mephits", "remorhaz"],
    },
    "underdark": {
        "key": "underdark",
        "label": "Underdark",
        "icon": "Mountain",
        "accent": "from-purple-700 to-fuchsia-900",
        "chip": "bg-purple-500/20 text-purple-300 border-purple-400/50",
        "survival_dc_mod": +4,    # no sun, no plants
        "nature_dc_mod": +3,
        "resources": ["luminescent fungi", "cave crystals", "subterranean ore"],
        "animals": ["bats", "cave fish", "blind salamanders"],
        "monsters": ["drow", "mind flayers", "umber hulks", "beholders"],
    },
    "volcanic": {
        "key": "volcanic",
        "label": "Volcanic",
        "icon": "Flame",
        "accent": "from-red-600 to-orange-800",
        "chip": "bg-red-500/20 text-red-300 border-red-400/50",
        "survival_dc_mod": +3,
        "nature_dc_mod": +1,
        "resources": ["obsidian", "sulfur", "volcanic glass", "lava-forged ore"],
        "animals": ["fire newts", "ash crows"],
        "monsters": ["fire elementals", "salamanders", "red dragons", "magmin"],
    },
    "urban": {
        "key": "urban",
        "label": "Urban",
        "icon": "Building",
        "accent": "from-slate-500 to-slate-800",
        "chip": "bg-slate-400/20 text-slate-300 border-slate-400/50",
        "survival_dc_mod": +1,    # food yes, but it costs coin
        "nature_dc_mod": +2,
        "resources": ["market goods", "alchemical reagents", "rumors", "contraband"],
        "animals": ["stray dogs", "rats", "pigeons", "horses"],
        "monsters": ["thieves", "cult agents", "doppelgangers", "lycanthropes"],
    },
    "fey": {
        "key": "fey",
        "label": "Feywild",
        "icon": "Sparkle",
        "accent": "from-pink-500 to-fuchsia-700",
        "chip": "bg-pink-500/20 text-pink-300 border-pink-400/50",
        "survival_dc_mod": +2,    # time and distance behave strangely
        "nature_dc_mod": +2,
        "resources": ["faerie silk", "moondrop honey", "pixie dust", "everbloom petals"],
        "animals": ["unicorns", "owl-cats", "blink dogs"],
        "monsters": ["fey hags", "satyrs", "displacer beasts", "redcaps"],
    },
    "shadow": {
        "key": "shadow",
        "label": "Shadowfell",
        "icon": "Moon",
        "accent": "from-zinc-700 to-zinc-900",
        "chip": "bg-zinc-500/20 text-zinc-300 border-zinc-400/50",
        "survival_dc_mod": +3,
        "nature_dc_mod": +2,
        "resources": ["nightshade", "umbral salt", "sorrow-gems"],
        "animals": ["shadow ravens", "death dogs"],
        "monsters": ["wraiths", "shadows", "vampires", "specters"],
    },
}


# Frontend-safe public dict (drops Python types so it can be JSON-dumped).
BIOMES_PUBLIC = {k: dict(v) for k, v in BIOMES.items()}


def list_biome_keys() -> List[str]:
    return list(BIOMES.keys())


def get_biome(key: str) -> BiomeDef:
    """Return a biome by key, falling back to 'forest' (the safe default)."""
    return BIOMES.get((key or "").lower()) or BIOMES["forest"]
