"""Dungeon generation service.

Dungeons are compact (4-6 rooms), themed, purposeful spaces discovered during
travel or awarded as quest leads. Every dungeon ends with a boss room and
special loot.

THEMES:
  undead      — crypts, plague vaults, necromancer lairs
  bandits     — hideouts, toll-forts, raid bases
  goblins     — warrens, trap-maker dens, shamanic caves
  cave_beasts — owlbear dens, troll lairs, spider nests
  animals     — bear dens, wolf territories, giant insect hives
  smugglers   — underground warehouses, hidden waterways, guild vaults
  cultists    — altar chambers, ritual circles, forbidden libraries
  dwarven     — abandoned mines, sealed vaults, collapsed forges

LIGHT LEVELS: bright | dim | dark

ROOM STRUCTURE:
  Room 0     → entrance (minimal defenses, establishes atmosphere)
  Rooms 1-N  → exploration (monsters, traps, lore, decisions)
  Last room  → boss room (custom enemy, special loot)
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional
from uuid import uuid4


# ---------------------------------------------------------------------------
# Theme tables
# ---------------------------------------------------------------------------

_THEMES: Dict[str, Dict] = {
    "undead": {
        "label": "Undead Crypt",
        "purpose_templates": [
            "A minor noble attempted a ritual to achieve immortality. His servants were the first subjects.",
            "A plague killed a settlement; no one came to give them rites. They rose on their own terms.",
            "A necromancer used this place as a laboratory before abandoning it when the work grew out of hand.",
        ],
        "atmosphere": [
            "The cold here is different — bone-deep, not weather-cold. The air smells of old stone and older things.",
            "Dust disturbed only by the dead. Silence that isn't quite silence.",
            "Thin sounds — not quite moans, not quite wind — move through the walls.",
        ],
        "room_types": [
            {"name": "Antechamber of Bones",    "light": "dim",    "monsters": ["skeleton warriors"], "trap": None,         "lore": "Inscriptions on the wall — burial prayers, now twisted."},
            {"name": "The Charnel Gallery",     "light": "dark",   "monsters": ["zombie horde"],      "trap": "bone trap",  "lore": "Portraits on the walls; the eyes were painted over."},
            {"name": "Crypt of the Faithful",   "light": "dim",    "monsters": ["wights"],            "trap": None,         "lore": "Sarcophagi — several pried open from the inside."},
            {"name": "The Lich's Antechamber",  "light": "dark",   "monsters": ["ghasts"],            "trap": "necrotic sigil", "lore": "A phylactery shelf — one compartment empty."},
            {"name": "The Whispering Vault",    "light": "dark",   "monsters": ["shadows"],           "trap": "life drain circle", "lore": "Names carved into the floor — the living, not the dead."},
        ],
        "boss_templates": [
            {"name": "Lord {name} the Withered", "type": "Wight Lord",    "hp_range": (52, 70),  "abilities": ["Life Drain", "Create Undead", "Commanding Howl"]},
            {"name": "The Pale Matron",          "type": "Vampire Spawn", "hp_range": (82, 110), "abilities": ["Charm", "Spider Climb", "Blood Drain"]},
            {"name": "The Bound Scholar",        "type": "Lich Fragment", "hp_range": (78, 90),  "abilities": ["Chill Touch", "Shield", "Counterspell", "Paralyzing Touch"]},
        ],
        "loot_templates": [
            {"name": "Soul Cage Amulet",     "description": "An amulet that captures the last spoken word of anyone slain while wearing it."},
            {"name": "Necrotic Tome",        "description": "A bound journal of ritual notes — dangerous knowledge, valuable to the right scholar."},
            {"name": "Ring of False Life",   "description": "A silver ring set with a black pearl. Once per day, grants temporary hit points equal to your level."},
            {"name": "Grave-Robber's Lantern","description": "A lantern that burns blue in the presence of undead within 60 feet."},
        ],
    },
    "bandits": {
        "label": "Bandit Stronghold",
        "purpose_templates": [
            "A former soldier turned the old watch-tower into an operation controlling three road segments.",
            "A thieves' guild uses this as a dead-drop point and extraction route for stolen goods.",
            "Deserters from a collapsed army unit, organized under a ruthless captain, prey on the trade road.",
        ],
        "atmosphere": [
            "The smell of woodsmoke, unwashed men, and something cooking badly. Voices somewhere ahead.",
            "Alert eyes at the entrance, arrow slits at odd angles, and the distinct sense of being watched since before you arrived.",
            "A working hideout — dirty, efficient, paranoid. Everything is positioned for a fast exit.",
        ],
        "room_types": [
            {"name": "The Watch Post",        "light": "bright", "monsters": ["bandit sentries"],  "trap": "alarm wire",     "lore": "A duty roster — names, schedules, a list of wanted posters."},
            {"name": "The Common Room",       "light": "bright", "monsters": ["bandit rabble"],    "trap": None,             "lore": "A map of the road with marks — ambush sites, patrol gaps."},
            {"name": "The Holding Cell",      "light": "dim",    "monsters": ["bandit guard"],     "trap": "tripwire alarm", "lore": "A prisoner, or evidence of one recently moved."},
            {"name": "The Quartermaster's Den","light":"bright",  "monsters": ["veteran thug"],     "trap": None,             "lore": "Crates of stolen goods, some marked with merchant guild seals."},
            {"name": "The Armory",            "light": "dim",    "monsters": ["bandit archers"],   "trap": "oil flask rigged","lore": "Better weapons than bandits should have — someone is supplying them."},
        ],
        "boss_templates": [
            {"name": "Captain {name} Ironhand", "type": "Bandit Captain",   "hp_range": (65, 85),  "abilities": ["Multiattack", "Parry", "Rally Troops"]},
            {"name": "The Quartermaster",       "type": "Veteran Mercenary", "hp_range": (58, 75),  "abilities": ["Multiattack", "Disarming Strike", "Shield Bash"]},
            {"name": "{name} of the Black Road","type": "Assassin Leader",  "hp_range": (72, 90),  "abilities": ["Sneak Attack", "Uncanny Dodge", "Poison Blade"]},
        ],
        "loot_templates": [
            {"name": "The Black Ledger",      "description": "A record of everyone who has paid protection to this gang — names, amounts, leverage notes."},
            {"name": "Stolen Signet Ring",    "description": "A noble's ring taken in a raid. Returning it could earn significant favor."},
            {"name": "Guild Contact List",    "description": "Names and meeting-places for the gang's fence network — information worth selling."},
            {"name": "The Captain's Key",     "description": "A master key that opens three specific locks in the nearest major city. The question is: which three?"},
        ],
    },
    "goblins": {
        "label": "Goblin Warren",
        "purpose_templates": [
            "A shaman led her tribe here after their forest was cleared. They've been expanding ever since.",
            "Goblins are using an old dwarven mine as a base for raiding surrounding farmsteads.",
            "A hobgoblin officer organized several goblin clans into a single fighting force with a single objective.",
        ],
        "atmosphere": [
            "Stink first — rotting food, unwashed bodies, and the chemical smell of hobgoblin-made explosives.",
            "Small handprints in mud at foot-level. Giggling somewhere behind the walls. Trip hazards at ankle height.",
            "A worked space poorly converted — too many ropes, too many holes in the walls, too many things hanging from the ceiling.",
        ],
        "room_types": [
            {"name": "The Trap Gallery",      "light": "dim",  "monsters": ["goblin trappers"],   "trap": "multiple pit traps",    "lore": "Diagrams scratched into the walls — better traps being designed."},
            {"name": "The Pen",               "light": "dark", "monsters": ["hobgoblin warden"],  "trap": None,                    "lore": "Stolen livestock, or things that once were livestock."},
            {"name": "The War Room",          "light": "bright","monsters": ["goblin war-band"],  "trap": "tripwire alarm",        "lore": "A mud map of the region with target farmsteads marked."},
            {"name": "The Shaman's Den",      "light": "dim",  "monsters": ["goblin shaman"],     "trap": "hex circle",            "lore": "Ritual totems — one still active and doing something you don't understand."},
            {"name": "The Clutch",            "light": "dark", "monsters": ["goblin bodyguards"], "trap": "explosive rigged ceiling","lore": "Eggs. A lot of them. Disturbing them has consequences."},
        ],
        "boss_templates": [
            {"name": "Shaman {name} Boneweave","type": "Goblin Shaman Boss","hp_range": (48, 62),  "abilities": ["Hex", "Bestow Curse", "Summon Spirits", "Goblin Stampede"]},
            {"name": "Warchief {name}",        "type": "Hobgoblin Warchief","hp_range": (85, 110), "abilities": ["Multiattack", "Battle Cry", "Leadership", "Martial Advantage"]},
            {"name": "The Boom-Maker",         "type": "Goblin Engineer",   "hp_range": (42, 58),  "abilities": ["Throw Flask", "Rigged Floor", "Smokescreen", "Explosive Exit"]},
        ],
        "loot_templates": [
            {"name": "Shaman's Skull Bowl",    "description": "A divination tool — ask it a question once per long rest. It answers in guttural Goblin, always partially true."},
            {"name": "Warchief's War Horn",    "description": "Blowing it once causes nearby goblins to flee. Blowing it twice causes them to charge whatever is closest."},
            {"name": "Trap Schematics",        "description": "Detailed drawings of three novel trap designs. Someone with the right tools could build them."},
            {"name": "Hobgoblin Seal",         "description": "An officer's seal from a hobgoblin military unit. Could be forged, could be returned for reward, could be dangerous to carry."},
        ],
    },
    "cave_beasts": {
        "label": "Beast Den",
        "purpose_templates": [
            "A predator claimed an old mine as territory and has been expanding outward as its hunting range grows.",
            "A nest of something large has been here for decades. The locals know to avoid it. You didn't know.",
            "A creature was driven here when its original territory was destroyed. It brought its young.",
        ],
        "atmosphere": [
            "Bones. Recent and older. Something has been eating here and leaving the remains.",
            "The smell is animal — musky, raw, wet. Something large breathed this air not long ago.",
            "Scratch marks on the walls at head height. Claw marks, not tool marks. Made by something big.",
        ],
        "room_types": [
            {"name": "The Kill Zone",         "light": "dark",  "monsters": ["cave bears"],        "trap": None,              "lore": "Carcasses stripped to the bone — prey items, not humanoid."},
            {"name": "The Nest Perimeter",    "light": "dark",  "monsters": ["giant spiders"],     "trap": "web net",         "lore": "Silk-wrapped shapes on the ceiling. Some of them are moving."},
            {"name": "The Feeding Ground",    "light": "dim",   "monsters": ["owlbear pack"],      "trap": None,              "lore": "A tended midden — the creature sorts its kills by type."},
            {"name": "The Burrow",            "light": "dark",  "monsters": ["young wyvern"],      "trap": None,              "lore": "A nesting hollow, lined with stolen soft goods. Something is tending it."},
            {"name": "The Deep Den",          "light": "dark",  "monsters": ["troll"],             "trap": "pressure plate floor","lore": "Troll-kept treasure — not hoarding, just things that caught the light."},
        ],
        "boss_templates": [
            {"name": "The Old Owlbear",        "type": "Elder Owlbear",      "hp_range": (95, 130), "abilities": ["Multiattack", "Screech", "Rend", "Protective Fury"]},
            {"name": "The Stone Troll",        "type": "Cave Troll",         "hp_range": (84, 115), "abilities": ["Regeneration", "Multiattack", "Rock Throw", "Trampling Charge"]},
            {"name": "The Brood Mother",       "type": "Giant Spider Queen", "hp_range": (68, 88),  "abilities": ["Web", "Poison Bite", "Spawn Broodlings", "Wall Crawl"]},
        ],
        "loot_templates": [
            {"name": "Beast Claw Talisman",   "description": "A claw from the boss creature, shaped by natural forces into something almost like a hook. Advantage on Intimidation when displayed."},
            {"name": "Predator's Eye",        "description": "A preserved eye from the boss. Someone knowledgeable about bestiary will pay significantly for it."},
            {"name": "Troll Hoard Relic",     "description": "Something valuable the troll kept — not because it was valuable, but because it was shiny. The shine is more significant than it looks."},
            {"name": "Venom Gland",           "description": "A spider's intact venom gland — enough for three doses of Giant Spider Poison."},
        ],
    },
    "animals": {
        "label": "Wild Animal Territory",
        "purpose_templates": [
            "A herd of large animals has nested here seasonally for generations. This is their ground, not yours.",
            "A single dominant predator has cleared this area. Other animals live here in the shadow of its territory.",
            "A druid's failed attempt to establish a sanctuary left the animals here semi-sentient and territorial.",
        ],
        "atmosphere": [
            "Birdsong stops as you enter. Then sounds resume, but different — alarm calls, movement signals.",
            "Animal sign everywhere — tracks, markings, scat. You're in a very active territory.",
            "Everything here is alive and paying attention to you.",
        ],
        "room_types": [
            {"name": "The Watering Hole",     "light": "bright","monsters": ["giant boars"],       "trap": None,               "lore": "Multiple species' tracks. Something feeds everything else here."},
            {"name": "The Canopy Nesting",    "light": "dim",   "monsters": ["giant wasps"],       "trap": "hive alarm",       "lore": "A hive the size of a wagon. The workers are agitated."},
            {"name": "The Pack Territory",    "light": "bright","monsters": ["dire wolf pack"],     "trap": None,               "lore": "Marking trees, ranging patterns — this pack has sentience that shouldn't be possible."},
            {"name": "The Gestation Cave",    "light": "dark",  "monsters": ["giant anacondas"],   "trap": "pressure vibration","lore": "Eggs. Dozens of them. The mother is in here with them."},
            {"name": "The Dominant's Ground", "light": "dim",   "monsters": ["bear + wolves"],     "trap": None,               "lore": "Two species sharing territory — something is coordinating them."},
        ],
        "boss_templates": [
            {"name": "The Alpha",              "type": "Dire Wolf Alpha",    "hp_range": (72, 95),  "abilities": ["Pack Tactics", "Bite", "Terrifying Howl", "Call Pack"]},
            {"name": "The Old Boar",           "type": "Giant Boar Ancient", "hp_range": (85, 110), "abilities": ["Charge", "Gore", "Relentless", "Shake Ground"]},
            {"name": "The Druid's Champion",   "type": "Awakened Bear",      "hp_range": (78, 100), "abilities": ["Multiattack", "Frightful Presence", "Speak with Animals", "Nature's Fury"]},
        ],
        "loot_templates": [
            {"name": "Alpha's Fang",           "description": "A fang from the dominant animal. Wearable as a pendant — it carries an old ward against that creature's species."},
            {"name": "Druid's Mark",           "description": "A carved stone left by whoever established this territory. A druid circle would recognize it."},
            {"name": "Territorial Chart",      "description": "Animal tracks interpreted by an expert — a map of every major creature's range in this region, accurate within a mile."},
            {"name": "Venom Gland",            "description": "A functional venom gland from a serpent or insect — enough for two doses of the creature's specific poison."},
        ],
    },
    "smugglers": {
        "label": "Smuggler's Den",
        "purpose_templates": [
            "A thieves' guild maintains this as a transit hub between two cities — untaxed goods, unmarked routes.",
            "A merchant who runs legal businesses by day routes contraband through here at night.",
            "A criminal organization uses this as a dead drop, a storage facility, and an extraction point.",
        ],
        "atmosphere": [
            "Too quiet for a working operation — either they knew you were coming, or the last shift ended badly.",
            "Professionally arranged. Every crate labeled in code, every exit clear. This is run by competent people.",
            "The smell of tar, rope, and something expensive being poorly stored in the wrong conditions.",
        ],
        "room_types": [
            {"name": "The Loading Dock",      "light": "dim",   "monsters": ["dockworker thugs"], "trap": "concealed alarm bell","lore": "Manifest ledgers in code — cargo descriptions, client initials."},
            {"name": "The Counting Room",     "light": "bright","monsters": ["accountant guard"], "trap": None,                 "lore": "Two sets of books. One is for the guild. One is for someone else."},
            {"name": "The Holding Cache",     "light": "dark",  "monsters": ["veteran smugglers"],"trap": "rigged shelf",       "lore": "Crates of goods that don't match their labels. Some of it's alive."},
            {"name": "The Passage",           "light": "dark",  "monsters": ["assassin pair"],    "trap": "blade spring",       "lore": "A tunnel leading somewhere you weren't supposed to find."},
            {"name": "The Vault Room",        "light": "dim",   "monsters": ["enforcer"],         "trap": "trapped floor safe", "lore": "High-value items kept separately. Very deliberately kept separately."},
        ],
        "boss_templates": [
            {"name": "The Factor",             "type": "Guild Enforcer",     "hp_range": (78, 98),  "abilities": ["Multiattack", "Disarming Strike", "Counteroffer (charm)", "Network: call backup"]},
            {"name": "{name} the Quiet",       "type": "Master Assassin",    "hp_range": (65, 85),  "abilities": ["Sneak Attack", "Evasion", "Poison Coated Blade", "Vanish"]},
            {"name": "The Merchant Prince",    "type": "Crime Lord",         "hp_range": (55, 72),  "abilities": ["Command", "Bribery (impose disadvantage)", "Hidden Weapon", "Protected by Secrets"]},
        ],
        "loot_templates": [
            {"name": "The Ledger",             "description": "The real ledger — transactions, client names, quantities. Political dynamite."},
            {"name": "Guild Token",            "description": "A guild membership token that grants access to certain establishments. Very useful, very dangerous to be caught with."},
            {"name": "Contraband Sample",      "description": "A sealed container of whatever the guild was moving. Valuable to the right buyer, illegal to the wrong authority."},
            {"name": "Dead Drop Location Map", "description": "A cipher map of all dead-drop locations in the region's guild network."},
        ],
    },
    "cultists": {
        "label": "Cult Sanctuary",
        "purpose_templates": [
            "A cult devoted to a forgotten deity has been building toward a ritual that the texts said would end three centuries ago.",
            "An academic discovered something in an old text and followed it to its logical conclusion. Others joined.",
            "A corrupted temple whose clergy slowly converted to the service of something that was listening through the walls.",
        ],
        "atmosphere": [
            "Chanting — low, rhythmic, almost subsonic. It changes your breathing without you noticing.",
            "The candles burn wrong colors. The shadows lean the wrong way. Something here is paying attention.",
            "Symbols you've seen before in different contexts, combined here into something new and unpleasant.",
        ],
        "room_types": [
            {"name": "The Antechamber",        "light": "dim",   "monsters": ["cult initiates"],   "trap": "glyph of warding",   "lore": "Initiation texts — what they were promised, what they gave."},
            {"name": "The Scripture Hall",     "light": "bright","monsters": ["cult zealots"],      "trap": None,                 "lore": "Sacred texts — the old version crossed out, the new written over it."},
            {"name": "The Ritual Chamber",     "light": "dim",   "monsters": ["cult priests"],     "trap": "summoning circle",   "lore": "An ongoing ritual — if interrupted, something may be released. Or not. Hard to say."},
            {"name": "The Sanctum Archive",    "light": "dark",  "monsters": ["cult mage"],        "trap": "necrotic ward",      "lore": "Forbidden research — dangerous to read, dangerous to destroy."},
            {"name": "The High Chamber",       "light": "dim",   "monsters": ["corrupted guards"], "trap": "divine punishment trap","lore": "The center of it all — what they were actually building toward."},
        ],
        "boss_templates": [
            {"name": "High Priest {name}",     "type": "Cult Fanatic Leader", "hp_range": (72, 95), "abilities": ["Invoke Patron", "Hold Person", "Spiritual Weapon", "Mass Suggestion"]},
            {"name": "The Bound Prophet",      "type": "Warlock Archpriest",  "hp_range": (68, 88), "abilities": ["Hex", "Eldritch Blast", "Misty Step", "Patron Manifestation"]},
            {"name": "The Vessel",             "type": "Half-Possessed Mage", "hp_range": (85, 108),"abilities": ["Counterspell", "Dominate Person", "Possession Strike", "Reality Fracture"]},
        ],
        "loot_templates": [
            {"name": "The High Priest's Codex","description": "The ritual manual — not fully readable, but chapters describe the patron's nature clearly enough to be useful and disturbing."},
            {"name": "Sanctified Focus",       "description": "A ritual focus still holding a charge from the cult's ceremonies. Usable as a spellcasting focus with a side effect yet to be determined."},
            {"name": "Patron Shard",           "description": "A crystallized fragment of divine — or infernal — essence. Extremely valuable to scholars. Attracts attention."},
            {"name": "Cult Roster",            "description": "Names of every initiated member, including several that would surprise local authorities."},
        ],
    },
    "dwarven": {
        "label": "Abandoned Dwarven Delve",
        "purpose_templates": [
            "A mining operation sealed after the workers hit something they shouldn't have and not all of them came back.",
            "A forge complex abandoned during a war, the dwarves never returned. Whatever they were making is still here.",
            "A clan vault sealed by the last living member. The lock is still functional. Something else got in another way.",
        ],
        "atmosphere": [
            "Engineered silence — the dwarven stonework absorbs sound in ways natural caves don't. Footsteps land flat.",
            "The dust is undisturbed for decades in places. In others, something has been walking recently.",
            "Architecture that was meant to last forever — and is. The damage done here was not by time.",
        ],
        "room_types": [
            {"name": "The Entry Hall",         "light": "dim",   "monsters": ["dwarven construct"], "trap": "runic pressure plate","lore": "An inscription above the door: what this place was called, when it was built, why it was sealed."},
            {"name": "The Mineshaft",          "light": "dark",  "monsters": ["derro scouts"],      "trap": None,                   "lore": "The ore vein — something was discovered here that changed the plan."},
            {"name": "The Forging Floor",      "light": "dim",   "monsters": ["iron golem remnant"],"trap": "falling forge hammer",  "lore": "Half-finished weapons. What they were making and why it was stopped."},
            {"name": "The Clan Hall",          "light": "bright","monsters": ["undead dwarves"],    "trap": "sealed gas chamber",    "lore": "Who these dwarves were. How they died."},
            {"name": "The Deep Vault",         "light": "dark",  "monsters": ["deep dweller"],     "trap": "mechanical lock trap",  "lore": "What was being kept secure here, and why it still needs to be."},
        ],
        "boss_templates": [
            {"name": "The Forge Warden",       "type": "Iron Golem Warden",   "hp_range": (108, 145),"abilities": ["Immutable Form", "Slam", "Fire Breath", "Sword Integration"]},
            {"name": "The Deepwatcher",        "type": "Elder Duergar",       "hp_range": (82, 105), "abilities": ["Enlarge", "Invisibility", "War Pick Mastery", "Psychic Torment"]},
            {"name": "Clan Elder {name}",      "type": "Undead Thane",        "hp_range": (95, 125), "abilities": ["Legendary Resistance", "Ancestral Call", "Rune Strike", "Death Ward"]},
        ],
        "loot_templates": [
            {"name": "Clan Rune Token",         "description": "A clan seal — opens certain dwarven strongholds and grants access to clan merchant networks."},
            {"name": "Masterwork Blueprint",    "description": "Schematics for a dwarven-engineered item of significant quality. A skilled smith could build from this."},
            {"name": "The Sealed Vault's Contents","description": "What the dwarves were protecting — the nature of this item should be determined by the DM based on the campaign's needs."},
            {"name": "Forgemaster's Hammer",    "description": "A dwarven artisan's hammer of exceptional quality. Grants advantage on relevant Artisan tool checks and deals extra damage to constructs."},
        ],
    },
}

# Default theme if unknown
_DEFAULT_THEME = "bandits"

# ---------------------------------------------------------------------------
# Name components for boss generation
# ---------------------------------------------------------------------------

_BOSS_NAMES = [
    "Malachar", "Vorath", "Sevik", "Grenn", "Torvald", "Ulsara",
    "Drek", "Morvan", "Ashara", "Belnor", "Craveth", "Durna",
]

_NOBLE_NAMES = [
    "Aldric", "Maren", "Sevara", "Galvan", "Oreth", "Tirel",
]

# ---------------------------------------------------------------------------
# Room count selection
# ---------------------------------------------------------------------------

def _room_count() -> int:
    """Return a room count between 4 and 6."""
    return random.randint(4, 6)


# ---------------------------------------------------------------------------
# Dungeon generation
# ---------------------------------------------------------------------------

def generate_dungeon(
    theme: str = "bandits",
    biome: str = "plains",
    region_name: str = "the wilderness",
    quest_context: str = "",
) -> Dict:
    """Generate a complete dungeon object.

    Returns a dict ready to be stored in campaign world_state.active_dungeon.
    """
    theme = theme if theme in _THEMES else _DEFAULT_THEME
    td = _THEMES[theme]
    room_count = _room_count()

    dungeon_id = f"dng_{uuid4().hex[:8]}"
    purpose = random.choice(td["purpose_templates"])
    atmosphere = random.choice(td["atmosphere"])

    # Pick room pool and boss
    room_pool = list(td["room_types"])
    random.shuffle(room_pool)
    rooms_data = room_pool[:room_count - 1]  # All but boss room

    boss_tmpl = random.choice(td["boss_templates"])
    loot_tmpl = random.choice(td["loot_templates"])

    boss_name_base = random.choice(_BOSS_NAMES)
    noble_name = random.choice(_NOBLE_NAMES)
    boss_name = boss_tmpl["name"].replace("{name}", boss_name_base).replace("{noble}", noble_name)

    hp_min, hp_max = boss_tmpl["hp_range"]
    boss_hp = random.randint(hp_min, hp_max)

    # Build room objects
    rooms = []
    for i, rd in enumerate(rooms_data):
        rooms.append({
            "index": i,
            "name": rd["name"],
            "light_level": rd["light"],
            "atmosphere": atmosphere if i == 0 else _vary_atmosphere(atmosphere, i),
            "monsters": rd.get("monsters") or [],
            "trap": rd.get("trap"),
            "lore": rd.get("lore") or "",
            "items": [],
            "completed": False,
            "is_boss_room": False,
        })

    # Boss room (last)
    boss_room = {
        "index": room_count - 1,
        "name": f"Lair of {boss_name}",
        "light_level": random.choice(["dim", "dark"]),
        "atmosphere": f"The final chamber. Something heavy in the air — anticipation or dread, and no difference between them here.",
        "monsters": [boss_tmpl["type"]],
        "trap": None,
        "lore": purpose,
        "items": [],
        "completed": False,
        "is_boss_room": True,
        "boss": {
            "name": boss_name,
            "type": boss_tmpl["type"],
            "hp": boss_hp,
            "hp_max": boss_hp,
            "abilities": boss_tmpl["abilities"],
            "condition": "alive",
        },
        "special_loot": {
            "name": loot_tmpl["name"],
            "description": loot_tmpl["description"],
        },
    }
    rooms.append(boss_room)

    dungeon = {
        "dungeon_id": dungeon_id,
        "name": _generate_dungeon_name(theme, region_name),
        "theme": theme,
        "theme_label": td["label"],
        "purpose": purpose,
        "atmosphere": atmosphere,
        "biome": biome,
        "region": region_name,
        "total_rooms": room_count,
        "current_room": -1,       # -1 = not entered yet
        "completed": False,
        "rooms": rooms,
        "created_for_quest": quest_context or "",
    }
    return dungeon


def _vary_atmosphere(base: str, index: int) -> str:
    """Return a slightly different atmospheric note for deeper rooms."""
    deeper = [
        "Deeper in, the architecture grows older — or the damage grows newer.",
        "The sounds from the entrance are gone. What's ahead is the only thing left.",
        "The air changes here. Colder, or warmer, or wrong in a way that's harder to name.",
        "Something changed when you crossed this threshold. You're past the point where anyone would have turned back.",
    ]
    return deeper[(index - 1) % len(deeper)]


_DUNGEON_NAME_PARTS = {
    "undead":      [("The Sunken", "Crypt of"), ("The Hollowed", "Tomb of"), ("Barrow of", "the Forgotten"), ("Vault of", "the Pale")],
    "bandits":     [("The Irongate", "Hideout"), ("Fort", "Rancor"), ("The Cut-Road", "Den"), ("Crossbones", "Hold")],
    "goblins":     [("The Stinking", "Warren"), ("Clawhole", "Depths"), ("The Gob-Pit", ""), ("Rattlebone", "Cave")],
    "cave_beasts": [("The Howling", "Den"), ("Bones-and-", "Dark"), ("The Feeding", "Hollow"), ("Clawmark", "Cave")],
    "animals":     [("The Old", "Territory"), ("The Brood", "Hollow"), ("Wild-Den", "of the Ridge"), ("The Pack", "Ground")],
    "smugglers":   [("The Black", "Vault"), ("Dead Drop", "Seven"), ("The Quiet", "Cache"), ("Merchant's", "Secret")],
    "cultists":    [("The Sealed", "Sanctum"), ("Altar of", "the Wound"), ("The Pale", "Gathering"), ("Chamber of", "the Muted God")],
    "dwarven":     [("The Forsaken", "Delve"), ("Ironroot", "Mine"), ("The Sealed", "Vault of"), ("Dwarven", "Ruin")],
}

def _generate_dungeon_name(theme: str, region_name: str) -> str:
    parts = _DUNGEON_NAME_PARTS.get(theme, _DUNGEON_NAME_PARTS["bandits"])
    prefix, suffix = random.choice(parts)
    if suffix:
        return f"{prefix} {suffix}"
    return prefix.strip()


# ---------------------------------------------------------------------------
# DM prompt block for dungeon room
# ---------------------------------------------------------------------------

def build_dungeon_room_block(dungeon: Dict, room_index: int) -> str:
    """Build a DUNGEON ROOM block for the DM system prompt."""
    rooms = dungeon.get("rooms") or []
    if room_index < 0 or room_index >= len(rooms):
        return ""

    room = rooms[room_index]
    total = dungeon.get("total_rooms", len(rooms))
    theme = dungeon.get("theme_label", dungeon.get("theme", "dungeon"))

    light_map = {
        "bright": "Fully lit — torches, magical light, or natural illumination.",
        "dim":    "Dim light — partial torches, embers, faint cracks. Perception checks are made at disadvantage.",
        "dark":   "Total darkness. Darkvision required to see. Light sources alert everything nearby.",
    }
    light_desc = light_map.get(room["light_level"], "Unknown lighting.")

    lines = [
        f"=== DUNGEON: {dungeon['name']} ===",
        f"Theme: {theme} | Room {room_index + 1} of {total} | {'BOSS ROOM' if room.get('is_boss_room') else ''}",
        f"",
        f"ROOM: {room['name']}",
        f"ATMOSPHERE: {room['atmosphere']}",
        f"LIGHT: {room['light_level'].upper()} — {light_desc}",
    ]

    if room.get("trap"):
        lines.append(f"TRAP PRESENT: {room['trap']} — embed it naturally in the environment, don't announce it. The player discovers it through observation or by triggering it.")

    if room.get("monsters"):
        monster_list = ", ".join(room["monsters"])
        lines.append(f"OCCUPANTS: {monster_list}")
        if room.get("is_boss_room") and room.get("boss"):
            boss = room["boss"]
            lines += [
                f"",
                f"BOSS: {boss['name']} ({boss['type']}, {boss['hp']} HP)",
                f"ABILITIES: {', '.join(boss['abilities'])}",
                "▸ This is the final confrontation. Give it weight. Don't rush the reveal.",
                "▸ The boss should react to the players' approach — if they were loud getting here, the boss is ready.",
                "▸ Use the boss's abilities throughout the fight, not just in the first round.",
            ]

    if room.get("lore"):
        lines.append(f"ENVIRONMENTAL LORE: {room['lore']} — surface this through objects, markings, or NPC dialogue. Never as exposition.")

    lines += [
        "",
        "NARRATION RULES FOR THIS ROOM:",
        "▸ Describe what the players sense first: sound, smell, light level, then sight.",
        "▸ The room should feel lived-in (or used, or abandoned) — not a stage waiting for players.",
        "▸ Give the players a moment to assess before anything happens. Dungeon rooms are not ambushes unless they set off the trap or make noise.",
    ]

    if room.get("is_boss_room") and room.get("special_loot"):
        loot = room["special_loot"]
        lines += [
            "",
            f"SPECIAL LOOT (after boss is defeated): {loot['name']}",
            f"Description: {loot['description']}",
            "▸ Present the loot as something the player finds — don't itemize it mechanically. Describe it physically first.",
        ]

    if room_index < total - 1:
        lines.append(f"\nFORWARD: One visible exit points deeper into the dungeon. What lies beyond is not visible from here.")
    else:
        lines.append(f"\nEXIT: The dungeon is complete. Describe an exit route or a changed entrance — the place feels different now that the threat is resolved.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helper: count completed quests from campaign data
# ---------------------------------------------------------------------------

def count_completed_quests(campaign: Dict) -> int:
    """Count completed quests from knowledge cards."""
    cards = (campaign.get("world_state") or {}).get("knowledge_cards") or []
    return sum(1 for c in cards if (c.get("status") or "").lower() == "completed")


# ---------------------------------------------------------------------------
# Theme detection from region/context
# ---------------------------------------------------------------------------

_THEME_FROM_BIOME = {
    "underdark": ["cave_beasts", "dwarven", "cultists"],
    "shadow":    ["undead", "cultists"],
    "forest":    ["bandits", "goblins", "animals", "cave_beasts"],
    "mountain":  ["dwarven", "cave_beasts", "bandits"],
    "swamp":     ["cultists", "undead", "animals"],
    "plains":    ["bandits", "smugglers", "animals"],
    "desert":    ["cultists", "cave_beasts", "bandits"],
    "coast":     ["smugglers", "bandits", "animals"],
    "urban":     ["smugglers", "cultists", "bandits"],
    "volcanic":  ["cave_beasts", "cultists", "dwarven"],
    "tundra":    ["animals", "cave_beasts", "dwarven"],
    "fey":       ["animals", "cultists", "goblins"],
}

def pick_theme_for_biome(biome: str) -> str:
    """Pick a dungeon theme appropriate for the given biome."""
    options = _THEME_FROM_BIOME.get(biome, ["bandits", "cave_beasts"])
    return random.choice(options)
