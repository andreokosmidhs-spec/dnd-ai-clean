"""Character feature catalogs for the player's personal deck.

Each entry produces one DeckCard. Cards have a rarity (common / rare / epic /
legendary) which the UI uses to color-code borders. The DM consumes a compact
summary every turn so it can naturally weave these features into narration
("you see clearly in the gloom thanks to your darkvision", "the guards
recognize your noble bearing", etc.).

Sources:
  * race      — racial traits (Darkvision, Fey Ancestry, …)
  * language  — language proficiencies
  * background— background feature (Criminal Contact, Position of Privilege)
  * class     — level-1 class features (Sneak Attack, Rage, Spellcasting)

`per_day` cards refresh on a long rest. `consumable` cards have explicit uses
that decrement per use (Sneak Attack is technically per-turn, not consumable;
Rage is per-day; spell slots are per-day).
"""
from __future__ import annotations

from typing import Dict, List


RACE_TRAITS: Dict[str, List[Dict]] = {
    "Human": [
        {"name": "Versatile", "rarity": "common",
         "description": "Adaptable and ambitious — +1 to all ability scores and one bonus language.",
         "mechanical": "+1 ALL · +1 language"},
    ],
    "Elf": [
        {"name": "Darkvision", "rarity": "rare",
         "description": "See clearly in dim light up to 60 ft; in darkness as if it were dim light (no color, only greys).",
         "mechanical": "60 ft. darkvision"},
        {"name": "Keen Senses", "rarity": "common",
         "description": "Acute awareness — proficiency in Perception.",
         "mechanical": "Proficiency: Perception"},
        {"name": "Fey Ancestry", "rarity": "rare",
         "description": "Advantage on saves vs. being charmed; magic cannot put you to sleep.",
         "mechanical": "Advantage vs. charm · sleep-immune"},
        {"name": "Trance", "rarity": "common",
         "description": "Meditate 4 hours instead of an 8-hour sleep — long-rest equivalent.",
         "mechanical": "4-hour long rest"},
    ],
    "Dwarf": [
        {"name": "Darkvision", "rarity": "rare",
         "description": "See clearly in dim light up to 60 ft; in darkness as if it were dim light.",
         "mechanical": "60 ft. darkvision"},
        {"name": "Dwarven Resilience", "rarity": "rare",
         "description": "Advantage on saves vs. poison; resistance to poison damage.",
         "mechanical": "Adv vs poison · poison resistance"},
        {"name": "Stonecunning", "rarity": "common",
         "description": "Add double proficiency to History checks about stonework.",
         "mechanical": "Stonework expertise"},
    ],
    "Halfling": [
        {"name": "Lucky", "rarity": "rare",
         "description": "When you roll a 1 on a d20 attack, ability check, or save, you can reroll once.",
         "mechanical": "Reroll natural 1s"},
        {"name": "Brave", "rarity": "common",
         "description": "Advantage on saves vs. being frightened.",
         "mechanical": "Adv vs frightened"},
        {"name": "Halfling Nimbleness", "rarity": "common",
         "description": "Move through the space of larger creatures.",
         "mechanical": "Move through bigger creatures"},
    ],
    "Tiefling": [
        {"name": "Darkvision", "rarity": "rare",
         "description": "See clearly in dim light up to 60 ft; in darkness as if it were dim light.",
         "mechanical": "60 ft. darkvision"},
        {"name": "Hellish Resistance", "rarity": "epic",
         "description": "Resistance to fire damage from any source.",
         "mechanical": "Fire resistance"},
        {"name": "Infernal Legacy", "rarity": "rare",
         "description": "Know the Thaumaturgy cantrip; at level 3 you can cast Hellish Rebuke once per long rest.",
         "mechanical": "Cantrip · Innate spells", "per_day": False},
    ],
    "Half-Elf": [
        {"name": "Darkvision", "rarity": "rare",
         "description": "See clearly in dim light up to 60 ft; in darkness as if it were dim light.",
         "mechanical": "60 ft. darkvision"},
        {"name": "Fey Ancestry", "rarity": "rare",
         "description": "Advantage vs. being charmed; magic cannot put you to sleep.",
         "mechanical": "Adv vs charm · sleep-immune"},
        {"name": "Skill Versatility", "rarity": "common",
         "description": "Proficiency in two skills of your choice.",
         "mechanical": "+2 skill proficiencies"},
    ],
    "Half-Orc": [
        {"name": "Darkvision", "rarity": "rare",
         "description": "See clearly in dim light up to 60 ft; in darkness as if it were dim light.",
         "mechanical": "60 ft. darkvision"},
        {"name": "Relentless Endurance", "rarity": "epic",
         "description": "When reduced to 0 HP, drop to 1 HP instead. Once per long rest.",
         "mechanical": "Survive a death blow", "per_day": True, "uses_max": 1},
        {"name": "Savage Attacks", "rarity": "rare",
         "description": "On a critical melee hit, roll one extra weapon damage die.",
         "mechanical": "+1 die on melee crit"},
        {"name": "Menacing", "rarity": "common",
         "description": "Proficiency in Intimidation.",
         "mechanical": "Proficiency: Intimidation"},
    ],
    "Gnome": [
        {"name": "Darkvision", "rarity": "rare",
         "description": "See clearly in dim light up to 60 ft; in darkness as if it were dim light.",
         "mechanical": "60 ft. darkvision"},
        {"name": "Gnome Cunning", "rarity": "epic",
         "description": "Advantage on INT, WIS, and CHA saves against magic.",
         "mechanical": "Adv on mental saves vs magic"},
    ],
    "Dragonborn": [
        {"name": "Draconic Ancestry", "rarity": "rare",
         "description": "Choose a chromatic or metallic ancestry; determines your damage type and breath weapon shape.",
         "mechanical": "Damage type: by ancestry"},
        {"name": "Breath Weapon", "rarity": "epic",
         "description": "Exhale destructive energy in a 15-ft cone or 5×30-ft line. DEX or CON save (DC 8+CON+prof) for half damage.",
         "mechanical": "AoE damage", "per_day": True, "uses_max": 1},
        {"name": "Damage Resistance", "rarity": "rare",
         "description": "Resistance to your ancestry's damage type.",
         "mechanical": "Resistance: ancestry damage"},
    ],
}

# Background features — each background has ONE feature card. Common
# backgrounds get common rarity; the few that grant networks/influence get rare.
BACKGROUND_FEATURES: Dict[str, Dict] = {
    "acolyte": {
        "name": "Shelter of the Faithful",
        "rarity": "rare",
        "description": "You and your companions can expect free healing and care at temples of your faith. Acolytes of the same faith provide aid and lodging.",
        "mechanical": "Free temple lodging · Faith network",
    },
    "criminal": {
        "name": "Criminal Contact",
        "rarity": "rare",
        "description": "You have a reliable contact who acts as your liaison to a network of other criminals — knows movement of people, news, and goods.",
        "mechanical": "Underground intel · Smuggling routes",
    },
    "folk_hero": {
        "name": "Rustic Hospitality",
        "rarity": "common",
        "description": "Common folk will hide you, give you simple food and shelter, and look the other way for the law on your behalf.",
        "mechanical": "Free lodging from common folk",
    },
    "noble": {
        "name": "Position of Privilege",
        "rarity": "epic",
        "description": "People assume you have the right to be where you are; nobles welcome you, common folk make way, you can get audiences with local nobles.",
        "mechanical": "Noble audience · Civic deference",
    },
    "sage": {
        "name": "Researcher",
        "rarity": "rare",
        "description": "When you don't know a piece of information, you usually know where to find it — colleagues, libraries, scriptoria, schools.",
        "mechanical": "Scholar network · Knowledge access",
    },
    "soldier": {
        "name": "Military Rank",
        "rarity": "rare",
        "description": "Soldiers of your former allegiance recognize your authority; you can use it to requisition simple equipment, mounts, or temporary use of soldiers.",
        "mechanical": "Military requisition · Rank deference",
    },
}


# Level-1 class features as deck cards. Spellcasting is a single card; spell
# slots will be added by a separate seeder once we wire spell-card support.
CLASS_FEATURES_LEVEL_1: Dict[str, List[Dict]] = {
    "Barbarian": [
        {"name": "Rage", "rarity": "epic",
         "description": "Bonus action: enter a rage for up to 1 minute. Advantage on STR checks/saves, +2 to melee damage, resistance to bludgeoning/piercing/slashing.",
         "mechanical": "2/long rest", "per_day": True, "uses_max": 2},
        {"name": "Unarmored Defense", "rarity": "rare",
         "description": "While not wearing armor, your AC = 10 + DEX mod + CON mod.",
         "mechanical": "AC = 10 + DEX + CON"},
    ],
    "Bard": [
        {"name": "Spellcasting", "rarity": "epic",
         "description": "Cast bard cantrips and spells (CHA-based). Spells slots refresh on a long rest.",
         "mechanical": "Cantrips · 2 first-level slots", "per_day": True, "uses_max": 2},
        {"name": "Bardic Inspiration (d6)", "rarity": "rare",
         "description": "Bonus action: grant an ally a d6 they can add to one ability check, attack, or save in the next 10 minutes.",
         "mechanical": "CHA-mod uses/long rest", "per_day": True, "uses_max": 3},
    ],
    "Cleric": [
        {"name": "Spellcasting", "rarity": "epic",
         "description": "Cast cleric cantrips and prepared spells (WIS-based). Spell slots refresh on a long rest.",
         "mechanical": "Cantrips · 2 first-level slots", "per_day": True, "uses_max": 2},
        {"name": "Divine Domain", "rarity": "rare",
         "description": "Your chosen domain grants extra spells and a domain-specific feature (Channel Divinity, etc.).",
         "mechanical": "Domain-specific"},
    ],
    "Druid": [
        {"name": "Druidic Language", "rarity": "rare",
         "description": "You know Druidic, a secret language only druids speak. Leave hidden messages no one else can decipher.",
         "mechanical": "Secret druidic communication"},
        {"name": "Spellcasting", "rarity": "epic",
         "description": "Cast druid cantrips and prepared spells (WIS-based). Spell slots refresh on a long rest.",
         "mechanical": "Cantrips · 2 first-level slots", "per_day": True, "uses_max": 2},
    ],
    "Fighter": [
        {"name": "Fighting Style", "rarity": "rare",
         "description": "Adopt a particular style of combat (Defense, Dueling, Great Weapon Fighting, Archery, etc.).",
         "mechanical": "Style-specific bonus"},
        {"name": "Second Wind", "rarity": "rare",
         "description": "Bonus action: regain 1d10 + fighter level HP. Once per short rest.",
         "mechanical": "1/short rest", "per_day": False, "uses_max": 1},
    ],
    "Monk": [
        {"name": "Martial Arts", "rarity": "rare",
         "description": "Use DEX for unarmed/monk weapon attacks; bonus-action unarmed strike when you attack.",
         "mechanical": "DEX-based fists"},
        {"name": "Unarmored Defense", "rarity": "rare",
         "description": "While not wearing armor or shield, AC = 10 + DEX mod + WIS mod.",
         "mechanical": "AC = 10 + DEX + WIS"},
    ],
    "Paladin": [
        {"name": "Divine Sense", "rarity": "rare",
         "description": "Action: detect celestial, fiend, or undead presence within 60 ft. Uses = 1 + CHA mod per long rest.",
         "mechanical": "Detect outsiders", "per_day": True, "uses_max": 2},
        {"name": "Lay on Hands", "rarity": "epic",
         "description": "Touch a creature to restore HP from a pool equal to 5 × paladin level. Refreshes on a long rest.",
         "mechanical": "5 HP healing pool/level", "per_day": True, "uses_max": 5},
    ],
    "Ranger": [
        {"name": "Favored Enemy", "rarity": "rare",
         "description": "Choose a creature type. Advantage on Survival to track them, INT checks to recall lore.",
         "mechanical": "Tracking advantage vs. type"},
        {"name": "Natural Explorer", "rarity": "rare",
         "description": "Choose a favored terrain. Move through it without penalty; track creatures here at near-supernatural skill.",
         "mechanical": "Terrain mastery"},
    ],
    "Rogue": [
        {"name": "Sneak Attack", "rarity": "epic",
         "description": "Once per turn deal +1d6 damage when you have advantage or an ally is adjacent to the target.",
         "mechanical": "+1d6 per turn"},
        {"name": "Thieves' Cant", "rarity": "rare",
         "description": "Secret slang only rogues understand. Leave coded messages, recognize criminal landmarks.",
         "mechanical": "Criminal cant"},
        {"name": "Expertise", "rarity": "rare",
         "description": "Double proficiency on two skills of your choice.",
         "mechanical": "2 skills doubled"},
    ],
    "Sorcerer": [
        {"name": "Spellcasting", "rarity": "epic",
         "description": "Cast sorcerer cantrips and known spells (CHA-based). Spell slots refresh on a long rest.",
         "mechanical": "Cantrips · 2 first-level slots", "per_day": True, "uses_max": 2},
        {"name": "Sorcerous Origin", "rarity": "rare",
         "description": "Your innate magical bloodline (Draconic, Wild Magic, etc.) grants signature features.",
         "mechanical": "Origin-specific"},
    ],
    "Warlock": [
        {"name": "Otherworldly Patron", "rarity": "epic",
         "description": "A pact with a powerful entity (Fiend, Archfey, Great Old One) grants signature features and spells.",
         "mechanical": "Patron-specific"},
        {"name": "Pact Magic", "rarity": "epic",
         "description": "Cast cantrips and known spells (CHA-based). 1 first-level slot, refreshes on a SHORT rest.",
         "mechanical": "1 slot/short rest", "per_day": False, "uses_max": 1},
    ],
    "Wizard": [
        {"name": "Spellcasting", "rarity": "epic",
         "description": "Cast wizard cantrips and prepared spells from your spellbook (INT-based). Slots refresh on a long rest.",
         "mechanical": "Cantrips · 2 first-level slots", "per_day": True, "uses_max": 2},
        {"name": "Arcane Recovery", "rarity": "rare",
         "description": "Once per day after a short rest, recover spell slots up to half your wizard level (rounded up).",
         "mechanical": "Slot recovery 1/day", "per_day": True, "uses_max": 1},
    ],
}


LANGUAGE_INFO: Dict[str, Dict] = {
    "Common":     {"description": "The trade tongue of humans, halflings, and most surface races.", "rarity": "common"},
    "Dwarvish":   {"description": "Spoken by dwarves; rich in stonework and craft terminology.",       "rarity": "common"},
    "Elvish":     {"description": "Fluid and song-like; spoken by elves and many fey.",                 "rarity": "common"},
    "Giant":      {"description": "The tongue of giants and giantkin; harsh, deliberate.",             "rarity": "rare"},
    "Gnomish":    {"description": "Spoken by gnomes; intricate, precise.",                              "rarity": "common"},
    "Goblin":     {"description": "Crude, fast-spoken trade tongue of goblinoid tribes.",              "rarity": "common"},
    "Halfling":   {"description": "Quiet, warm; halflings rarely teach it to outsiders.",              "rarity": "common"},
    "Orc":        {"description": "Blunt and forceful; spoken by orcs and half-orcs.",                  "rarity": "common"},
    "Abyssal":    {"description": "The chittering language of demons; few mortals know it safely.",   "rarity": "epic"},
    "Celestial":  {"description": "The melodic tongue of celestial beings.",                            "rarity": "epic"},
    "Draconic":   {"description": "The ancient language of dragons; foundation of arcane writing.",   "rarity": "rare"},
    "Deep Speech":{"description": "The wet, alien language of aberrations.",                            "rarity": "epic"},
    "Infernal":   {"description": "The contractual tongue of devils; precise and binding.",            "rarity": "rare"},
    "Primordial": {"description": "The elemental tongue (and its dialects: Aquan, Auran, Ignan, Terran).", "rarity": "rare"},
    "Sylvan":     {"description": "The language of fey creatures and feywild natives.",                 "rarity": "rare"},
    "Undercommon":{"description": "Trade tongue of the Underdark.",                                     "rarity": "rare"},
    "Druidic":    {"description": "Secret druidic cant — only druids may teach it.",                  "rarity": "epic"},
    "Thieves' Cant":{"description": "Secret rogue cant — coded slang and visual signs.",              "rarity": "epic"},
}


# Class-level proficiencies (armor / weapons / tools / saving throws). These
# differ from `CLASS_FEATURES_LEVEL_1` — they're the static prof grants every
# member of the class shares.
CLASS_PROFICIENCIES: Dict[str, Dict[str, List[str]]] = {
    "Barbarian":  {"armor": ["Light Armor", "Medium Armor", "Shields"], "weapons": ["Simple Weapons", "Martial Weapons"], "tools": [], "saves": ["Strength", "Constitution"]},
    "Bard":       {"armor": ["Light Armor"], "weapons": ["Simple Weapons", "Hand Crossbow", "Longsword", "Rapier", "Shortsword"], "tools": ["3 Musical Instruments"], "saves": ["Dexterity", "Charisma"]},
    "Cleric":     {"armor": ["Light Armor", "Medium Armor", "Shields"], "weapons": ["Simple Weapons"], "tools": [], "saves": ["Wisdom", "Charisma"]},
    "Druid":      {"armor": ["Light Armor", "Medium Armor", "Shields (non-metal)"], "weapons": ["Clubs", "Daggers", "Darts", "Javelins", "Maces", "Quarterstaffs", "Scimitars", "Sickles", "Slings", "Spears"], "tools": ["Herbalism Kit"], "saves": ["Intelligence", "Wisdom"]},
    "Fighter":    {"armor": ["All Armor", "Shields"], "weapons": ["Simple Weapons", "Martial Weapons"], "tools": [], "saves": ["Strength", "Constitution"]},
    "Monk":       {"armor": [], "weapons": ["Simple Weapons", "Shortswords"], "tools": ["1 Artisan Tool or Musical Instrument"], "saves": ["Strength", "Dexterity"]},
    "Paladin":    {"armor": ["All Armor", "Shields"], "weapons": ["Simple Weapons", "Martial Weapons"], "tools": [], "saves": ["Wisdom", "Charisma"]},
    "Ranger":     {"armor": ["Light Armor", "Medium Armor", "Shields"], "weapons": ["Simple Weapons", "Martial Weapons"], "tools": [], "saves": ["Strength", "Dexterity"]},
    "Rogue":      {"armor": ["Light Armor"], "weapons": ["Simple Weapons", "Hand Crossbow", "Longsword", "Rapier", "Shortsword"], "tools": ["Thieves' Tools"], "saves": ["Dexterity", "Intelligence"]},
    "Sorcerer":   {"armor": [], "weapons": ["Daggers", "Darts", "Slings", "Quarterstaffs", "Light Crossbows"], "tools": [], "saves": ["Constitution", "Charisma"]},
    "Warlock":    {"armor": ["Light Armor"], "weapons": ["Simple Weapons"], "tools": [], "saves": ["Wisdom", "Charisma"]},
    "Wizard":     {"armor": [], "weapons": ["Daggers", "Darts", "Slings", "Quarterstaffs", "Light Crossbows"], "tools": [], "saves": ["Intelligence", "Wisdom"]},
}


# Starting equipment per class (default flavor pack). Items are common-rarity
# and seeded as deck cards under the `item` source.
CLASS_STARTING_EQUIPMENT: Dict[str, Dict] = {
    "Barbarian":  {"gold": 50,  "items": ["Greataxe", "Handaxe (2)", "Javelin (4)", "Explorer's Pack", "Leather Armor"]},
    "Bard":       {"gold": 100, "items": ["Rapier", "Dagger", "Lute", "Leather Armor", "Diplomat's Pack"]},
    "Cleric":     {"gold": 100, "items": ["Mace", "Shield", "Scale Mail", "Light Crossbow", "Crossbow Bolts (20)", "Priest's Pack", "Holy Symbol"]},
    "Druid":      {"gold": 50,  "items": ["Wooden Shield", "Scimitar", "Leather Armor", "Explorer's Pack", "Druidic Focus"]},
    "Fighter":    {"gold": 100, "items": ["Longsword", "Shield", "Chain Mail", "Light Crossbow", "Crossbow Bolts (20)", "Dungeoneer's Pack"]},
    "Monk":       {"gold": 25,  "items": ["Shortsword", "Dart (10)", "Dungeoneer's Pack"]},
    "Paladin":    {"gold": 100, "items": ["Longsword", "Shield", "Chain Mail", "Javelin (5)", "Priest's Pack", "Holy Symbol"]},
    "Ranger":     {"gold": 75,  "items": ["Longbow", "Arrows (20)", "Two Shortswords", "Scale Mail", "Explorer's Pack"]},
    "Rogue":      {"gold": 100, "items": ["Rapier", "Shortbow", "Arrows (20)", "Dagger (2)", "Leather Armor", "Burglar's Pack", "Thieves' Tools"]},
    "Sorcerer":   {"gold": 75,  "items": ["Light Crossbow", "Crossbow Bolts (20)", "Dagger (2)", "Component Pouch", "Dungeoneer's Pack"]},
    "Warlock":    {"gold": 50,  "items": ["Light Crossbow", "Crossbow Bolts (20)", "Dagger (2)", "Leather Armor", "Component Pouch", "Scholar's Pack"]},
    "Wizard":     {"gold": 100, "items": ["Quarterstaff", "Component Pouch", "Spellbook", "Scholar's Pack"]},
}


# Skills metadata — used so the deck cards have proper ability + use hints.
SKILL_INFO: Dict[str, Dict] = {
    "Acrobatics":      {"ability": "DEX", "blurb": "Stay on your feet, balance on a tightrope, dive aside, slip a grapple."},
    "Animal Handling": {"ability": "WIS", "blurb": "Calm a frightened animal, intuit a creature's intent, ride one well."},
    "Arcana":          {"ability": "INT", "blurb": "Recall lore about spells, planes, magical traditions and creatures."},
    "Athletics":       {"ability": "STR", "blurb": "Climb, swim, jump, grapple, force a door."},
    "Deception":       {"ability": "CHA", "blurb": "Sell a lie, fast-talk a guard, conceal your real intent."},
    "History":         {"ability": "INT", "blurb": "Recall lore about wars, lineages, lost civilizations, kings."},
    "Insight":         {"ability": "WIS", "blurb": "Read a face, catch a tell, sense the truth behind words."},
    "Intimidation":    {"ability": "CHA", "blurb": "Threaten, glare, force compliance through pressure."},
    "Investigation":   {"ability": "INT", "blurb": "Search a room methodically, deduce from clues, find hidden things by reasoning."},
    "Medicine":        {"ability": "WIS", "blurb": "Stabilize the dying, diagnose an illness, identify a poison."},
    "Nature":          {"ability": "INT", "blurb": "Recall lore about terrain, plants, animals, the weather."},
    "Perception":      {"ability": "WIS", "blurb": "Spot, hear, otherwise notice — what others miss."},
    "Performance":     {"ability": "CHA", "blurb": "Entertain a crowd: music, dance, oration, tale-telling."},
    "Persuasion":      {"ability": "CHA", "blurb": "Win someone over with reason, charm, courtesy."},
    "Religion":        {"ability": "INT", "blurb": "Recall lore about gods, holy rites, sacred relics."},
    "Sleight of Hand": {"ability": "DEX", "blurb": "Pickpocket, plant something, palm a coin, conceal a weapon."},
    "Stealth":         {"ability": "DEX", "blurb": "Move unseen, unheard, vanish into shadow or crowd."},
    "Survival":        {"ability": "WIS", "blurb": "Track, forage, navigate, read the weather, weather a wilderness."},
}




# Rarity ordering for sorting + visual prominence.
RARITY_ORDER = {"legendary": 0, "epic": 1, "rare": 2, "common": 3}


# ---------------------------------------------------------------------------
# Class features by level (2-20)
#
# Keyed CLASS_FEATURES_BY_LEVEL[class_name][level] = [list of feature dicts].
# Levels with no new base-class features are omitted entirely.
# Pure numeric upgrades (rage uses, ki points, spell slot counts) are NOT
# separate cards — they are derivable from character level. Only genuinely
# new mechanics appear here.
# ---------------------------------------------------------------------------

_ASI = {
    "name": "Ability Score Improvement",
    "rarity": "common",
    "description": "Increase one ability score by 2, or two scores by 1 each. Alternatively, take a feat.",
    "mechanical": "+2 to one score, or +1 to two scores",
}

CLASS_FEATURES_BY_LEVEL: Dict[str, Dict[int, List[Dict]]] = {

    # ── BARBARIAN ─────────────────────────────────────────────────────────────
    "Barbarian": {
        2: [
            {"name": "Reckless Attack", "rarity": "rare",
             "description": "Gain advantage on melee attacks this turn — but attackers also have advantage against you until your next turn.",
             "mechanical": "Adv on melee · attackers get adv back"},
            {"name": "Danger Sense", "rarity": "rare",
             "description": "Advantage on DEX saves against visible effects (traps, spells). Not while blinded, deafened, or incapacitated.",
             "mechanical": "Adv on visible-threat DEX saves"},
        ],
        3: [
            {"name": "Primal Path", "rarity": "epic",
             "description": "Choose your barbarian subclass — Berserker, Totem Warrior, or another path. Shapes your rage and fighting identity.",
             "mechanical": "Subclass unlock"},
            {"name": "Rage", "upgrades": True, "rarity": "epic",
             "description": "Bonus action: enter a rage for up to 1 minute. Advantage on STR checks/saves, +2 to melee damage, resistance to bludgeoning/piercing/slashing.",
             "mechanical": "3/long rest · +2 melee dmg", "per_day": True, "uses_max": 3},
        ],
        4: [_ASI],
        5: [
            {"name": "Extra Attack", "rarity": "epic",
             "description": "Attack twice instead of once when you take the Attack action.",
             "mechanical": "2 attacks per Attack action"},
            {"name": "Fast Movement", "rarity": "rare",
             "description": "Your speed increases by 10 ft while not wearing heavy armor.",
             "mechanical": "+10 ft speed (no heavy armor)"},
        ],
        6: [
            {"name": "Primal Path Feature", "rarity": "rare",
             "description": "Your Primal Path grants an additional feature.",
             "mechanical": "Subclass feature"},
            {"name": "Rage", "upgrades": True, "rarity": "epic",
             "description": "Bonus action: enter a rage for up to 1 minute. Advantage on STR checks/saves, +2 to melee damage, resistance to bludgeoning/piercing/slashing.",
             "mechanical": "4/long rest · +2 melee dmg", "per_day": True, "uses_max": 4},
        ],
        7: [
            {"name": "Feral Instinct", "rarity": "rare",
             "description": "Advantage on Initiative rolls. If surprised, you can still act on your first turn by entering a rage immediately.",
             "mechanical": "Adv on Initiative · act through surprise while raging"},
        ],
        8: [_ASI],
        9: [
            {"name": "Brutal Critical", "rarity": "rare",
             "description": "Roll one extra weapon damage die on a melee critical hit. Grows to 2 extra dice at level 13, 3 at level 17.",
             "mechanical": "+1 weapon die on melee crit (scales)"},
            {"name": "Rage", "upgrades": True, "rarity": "epic",
             "description": "Bonus action: enter a rage for up to 1 minute. Advantage on STR checks/saves, +3 to melee damage, resistance to bludgeoning/piercing/slashing.",
             "mechanical": "4/long rest · +3 melee dmg", "per_day": True, "uses_max": 4},
        ],
        10: [
            {"name": "Primal Path Feature", "rarity": "rare",
             "description": "Your Primal Path grants another feature.",
             "mechanical": "Subclass feature"},
        ],
        11: [
            {"name": "Relentless Rage", "rarity": "epic",
             "description": "While raging and reduced to 0 HP, make a DC 10 CON save to drop to 1 HP instead. DC rises by 5 for each use until a long rest.",
             "mechanical": "CON save → survive at 1 HP while raging"},
        ],
        12: [
            _ASI,
            {"name": "Rage", "upgrades": True, "rarity": "epic",
             "description": "Bonus action: enter a rage for up to 1 minute. Advantage on STR checks/saves, +3 to melee damage, resistance to bludgeoning/piercing/slashing.",
             "mechanical": "5/long rest · +3 melee dmg", "per_day": True, "uses_max": 5},
        ],
        13: [
            {"name": "Brutal Critical", "upgrades": True, "rarity": "epic",
             "description": "Roll two extra weapon damage dice on a melee critical hit. Grows to 3 extra dice at level 17.",
             "mechanical": "+2 weapon dice on melee crit"},
        ],
        14: [
            {"name": "Primal Path Feature", "rarity": "epic",
             "description": "Your Primal Path grants its most powerful feature.",
             "mechanical": "Subclass capstone"},
        ],
        15: [
            {"name": "Persistent Rage", "rarity": "rare",
             "description": "Your rage no longer ends from not attacking — only from unconsciousness or your own choice.",
             "mechanical": "Rage won't expire from inaction"},
        ],
        16: [
            _ASI,
            {"name": "Rage", "upgrades": True, "rarity": "epic",
             "description": "Bonus action: enter a rage for up to 1 minute. Advantage on STR checks/saves, +4 to melee damage, resistance to bludgeoning/piercing/slashing.",
             "mechanical": "5/long rest · +4 melee dmg", "per_day": True, "uses_max": 5},
        ],
        17: [
            {"name": "Brutal Critical", "upgrades": True, "rarity": "epic",
             "description": "Roll three extra weapon damage dice on a melee critical hit.",
             "mechanical": "+3 weapon dice on melee crit"},
            {"name": "Rage", "upgrades": True, "rarity": "epic",
             "description": "Bonus action: enter a rage for up to 1 minute. Advantage on STR checks/saves, +4 to melee damage, resistance to bludgeoning/piercing/slashing.",
             "mechanical": "6/long rest · +4 melee dmg", "per_day": True, "uses_max": 6},
        ],
        18: [
            {"name": "Indomitable Might", "rarity": "rare",
             "description": "When a STR check total is less than your STR score, use your STR score instead.",
             "mechanical": "STR checks ≥ STR score always"},
        ],
        19: [_ASI],
        20: [
            {"name": "Primal Champion", "rarity": "legendary",
             "description": "Your STR and CON each increase by 4, and their maximums rise to 24.",
             "mechanical": "+4 STR · +4 CON · max score 24"},
            {"name": "Rage", "upgrades": True, "rarity": "legendary",
             "description": "Bonus action: enter a rage for up to 1 minute. Advantage on STR checks/saves, +4 to melee damage, resistance to bludgeoning/piercing/slashing. No limit on uses.",
             "mechanical": "Unlimited/long rest · +4 melee dmg", "per_day": True, "uses_max": 0},
        ],
    },

    # ── BARD ──────────────────────────────────────────────────────────────────
    "Bard": {
        2: [
            {"name": "Jack of All Trades", "rarity": "rare",
             "description": "Add half your proficiency bonus (rounded down) to any ability check that doesn't already use your proficiency.",
             "mechanical": "+½ prof to non-proficient checks"},
            {"name": "Song of Rest", "rarity": "common",
             "description": "Music or story during a short rest — allies who hear you regain an extra die of HP from their Hit Dice. Die grows with level (d6→d12).",
             "mechanical": "Allies +1 extra hit die on short rest"},
        ],
        3: [
            {"name": "Bard College", "rarity": "epic",
             "description": "Choose your Bard College (Lore, Valor, etc.) — grants Bonus Proficiencies and a signature feature.",
             "mechanical": "Subclass unlock"},
            {"name": "Expertise", "rarity": "rare",
             "description": "Double your proficiency bonus on two more skill checks of your choice.",
             "mechanical": "+2 skills doubled"},
        ],
        4: [_ASI],
        5: [
            {"name": "Font of Inspiration", "rarity": "rare",
             "description": "Regain all uses of Bardic Inspiration on a short or long rest (was long rest only).",
             "mechanical": "Bardic Inspiration refreshes on short rest"},
            {"name": "Bardic Inspiration (d8)", "upgrades": "Bardic Inspiration (d6)", "rarity": "rare",
             "description": "Bonus action: grant an ally a d8 they can add to one ability check, attack, or save in the next 10 minutes.",
             "mechanical": "CHA-mod uses/short rest · d8 die", "per_day": False, "uses_max": 3},
        ],
        6: [
            {"name": "Countercharm", "rarity": "rare",
             "description": "Action: perform until start of next turn — friendly creatures within 30 ft have advantage on saves vs. charmed and frightened.",
             "mechanical": "Action: 30 ft aura vs charm/frightened"},
            {"name": "Bard College Feature", "rarity": "rare",
             "description": "Your Bard College grants an additional feature.",
             "mechanical": "Subclass feature"},
        ],
        8: [_ASI],
        10: [
            {"name": "Magical Secrets", "rarity": "epic",
             "description": "Learn two spells from any class spell list — they count as bard spells for you.",
             "mechanical": "+2 spells from any class list"},
            {"name": "Expertise (2nd)", "rarity": "rare",
             "description": "Double proficiency bonus on two more skill checks.",
             "mechanical": "+2 more skills doubled"},
            {"name": "Bardic Inspiration (d10)", "upgrades": "Bardic Inspiration (d8)", "rarity": "rare",
             "description": "Bonus action: grant an ally a d10 they can add to one ability check, attack, or save in the next 10 minutes.",
             "mechanical": "CHA-mod uses/short rest · d10 die", "per_day": False, "uses_max": 3},
        ],
        12: [_ASI],
        14: [
            {"name": "Magical Secrets II", "rarity": "epic",
             "description": "Learn two more spells from any class spell list.",
             "mechanical": "+2 more spells from any class list"},
            {"name": "Bard College Feature", "rarity": "epic",
             "description": "Your Bard College grants its capstone feature.",
             "mechanical": "Subclass capstone"},
        ],
        15: [
            {"name": "Bardic Inspiration (d12)", "upgrades": "Bardic Inspiration (d10)", "rarity": "epic",
             "description": "Bonus action: grant an ally a d12 they can add to one ability check, attack, or save in the next 10 minutes.",
             "mechanical": "CHA-mod uses/short rest · d12 die", "per_day": False, "uses_max": 3},
        ],
        16: [_ASI],
        18: [
            {"name": "Magical Secrets III", "rarity": "epic",
             "description": "Learn two more spells from any class spell list.",
             "mechanical": "+2 more spells from any class list"},
        ],
        19: [_ASI],
        20: [
            {"name": "Superior Inspiration", "rarity": "legendary",
             "description": "When you roll Initiative with no Bardic Inspiration uses left, you regain one use immediately.",
             "mechanical": "Regain 1 Bardic Inspiration on initiative roll"},
        ],
    },

    # ── CLERIC ────────────────────────────────────────────────────────────────
    "Cleric": {
        2: [
            {"name": "Channel Divinity", "rarity": "epic",
             "description": "Channel divine energy to fuel magical effects — Turn Undead plus your domain option. Starts at 1 use/rest; increases to 3 by level 18.",
             "mechanical": "1/short rest (scales) · Turn Undead + domain option",
             "per_day": False, "uses_max": 1},
            {"name": "Turn Undead", "rarity": "rare",
             "description": "Channel Divinity: each undead within 30 ft that can hear you must succeed on a WIS save or be turned for 1 minute.",
             "mechanical": "WIS save · turned undead flee 30 ft"},
        ],
        4: [_ASI],
        5: [
            {"name": "Destroy Undead", "rarity": "rare",
             "description": "Turned undead of low CR are instantly destroyed instead of fleeing. CR threshold rises every few levels (½ → 1 → 2 → 3 → 4).",
             "mechanical": "Destroy turned undead CR ½ (scales)"},
        ],
        6: [
            {"name": "Divine Domain Feature", "rarity": "rare",
             "description": "Your chosen Domain grants a powerful feature.",
             "mechanical": "Subclass feature"},
            {"name": "Channel Divinity", "upgrades": True, "rarity": "epic",
             "description": "Channel divine energy to fuel magical effects — Turn Undead plus your domain option. 2 uses per rest.",
             "mechanical": "2/short rest · Turn Undead + domain option",
             "per_day": False, "uses_max": 2},
        ],
        8: [
            _ASI,
            {"name": "Divine Domain Feature", "rarity": "epic",
             "description": "Your domain grants its major feature (Divine Strike or Potent Spellcasting, depending on domain).",
             "mechanical": "Subclass major feature"},
        ],
        10: [
            {"name": "Divine Intervention", "rarity": "legendary",
             "description": "Call on your deity. Roll percentile — if the result ≤ your cleric level, the deity intervenes. Once per 7 days. Auto-succeeds at level 20.",
             "mechanical": "≤level% chance · 7-day cooldown", "per_day": True, "uses_max": 1},
        ],
        12: [_ASI],
        16: [_ASI],
        17: [
            {"name": "Divine Domain Capstone", "rarity": "epic",
             "description": "Your Divine Domain grants its ultimate feature.",
             "mechanical": "Subclass capstone"},
        ],
        18: [
            {"name": "Channel Divinity", "upgrades": True, "rarity": "epic",
             "description": "Channel divine energy to fuel magical effects — Turn Undead plus your domain option. 3 uses per rest.",
             "mechanical": "3/short rest · Turn Undead + domain option",
             "per_day": False, "uses_max": 3},
        ],
        19: [_ASI],
        20: [
            {"name": "Divine Intervention (Auto)", "rarity": "legendary",
             "description": "Your Divine Intervention call now automatically succeeds — no roll needed.",
             "mechanical": "Auto-succeeds · 7-day cooldown", "per_day": True, "uses_max": 1},
        ],
    },

    # ── DRUID ─────────────────────────────────────────────────────────────────
    "Druid": {
        2: [
            {"name": "Wild Shape", "rarity": "epic",
             "description": "Transform into a beast of CR ¼ or lower for up to half your druid level in hours. 2 uses per short rest. CR cap and allowed speeds grow with level.",
             "mechanical": "CR ¼ beast · 2/short rest (scales)", "per_day": False, "uses_max": 2},
            {"name": "Druid Circle", "rarity": "epic",
             "description": "Choose your Druid Circle (Land, Moon, etc.) — defines the nature of your Wild Shape and granted spells.",
             "mechanical": "Subclass unlock"},
        ],
        4: [
            {"name": "Wild Shape Improvement", "rarity": "rare",
             "description": "Wild Shape can now become beasts with a swimming speed, up to CR ½.",
             "mechanical": "CR ½ + swimming speed beasts"},
            _ASI,
        ],
        6: [
            {"name": "Druid Circle Feature", "rarity": "rare",
             "description": "Your Druid Circle grants an additional feature.",
             "mechanical": "Subclass feature"},
        ],
        8: [
            {"name": "Wild Shape Improvement (Flight)", "rarity": "rare",
             "description": "Wild Shape can now become beasts with a flying speed, up to CR 1.",
             "mechanical": "CR 1 + flying speed beasts"},
            _ASI,
        ],
        10: [
            {"name": "Druid Circle Feature", "rarity": "rare",
             "description": "Your Druid Circle grants another feature.",
             "mechanical": "Subclass feature"},
        ],
        12: [_ASI],
        14: [
            {"name": "Druid Circle Capstone", "rarity": "epic",
             "description": "Your Druid Circle grants its most powerful feature.",
             "mechanical": "Subclass capstone"},
        ],
        16: [_ASI],
        18: [
            {"name": "Timeless Body", "rarity": "rare",
             "description": "Primal magic sustains you — you age only 1 year per 10 and cannot be magically aged.",
             "mechanical": "1/10th aging · immune to magical aging"},
            {"name": "Beast Spells", "rarity": "epic",
             "description": "Cast druid spells while Wild Shaped, as long as the spell has no material components.",
             "mechanical": "Cast spells in Wild Shape (no material components)"},
        ],
        19: [_ASI],
        20: [
            {"name": "Archdruid", "rarity": "legendary",
             "description": "Unlimited uses of Wild Shape. Ignore the verbal and somatic components of spells while Wild Shaped.",
             "mechanical": "Unlimited Wild Shape · ignore V/S components while shifted"},
        ],
    },

    # ── FIGHTER ───────────────────────────────────────────────────────────────
    "Fighter": {
        2: [
            {"name": "Action Surge", "rarity": "epic",
             "description": "On your turn, take one additional action. Once per short rest. Becomes twice per short rest at level 17.",
             "mechanical": "1/short rest (2 at lvl 17)", "per_day": False, "uses_max": 1},
        ],
        3: [
            {"name": "Martial Archetype", "rarity": "epic",
             "description": "Choose your Martial Archetype (Champion, Battle Master, Eldritch Knight, etc.) — your advanced combat specialty.",
             "mechanical": "Subclass unlock"},
        ],
        4: [_ASI],
        5: [
            {"name": "Extra Attack (2)", "rarity": "epic",
             "description": "Attack twice when you take the Attack action.",
             "mechanical": "2 attacks per Attack action"},
        ],
        6: [_ASI],
        7: [
            {"name": "Martial Archetype Feature", "rarity": "rare",
             "description": "Your Martial Archetype grants a feature.",
             "mechanical": "Subclass feature"},
        ],
        8: [_ASI],
        9: [
            {"name": "Indomitable", "rarity": "rare",
             "description": "Reroll a failed saving throw — you must use the new result. Once per long rest; increases to 3 uses by level 17.",
             "mechanical": "1/long rest reroll (scales)", "per_day": True, "uses_max": 1},
        ],
        10: [
            {"name": "Martial Archetype Feature", "rarity": "rare",
             "description": "Your Martial Archetype grants another feature.",
             "mechanical": "Subclass feature"},
        ],
        11: [
            {"name": "Extra Attack (3)", "rarity": "epic",
             "description": "Attack three times when you take the Attack action.",
             "mechanical": "3 attacks per Attack action"},
        ],
        12: [_ASI],
        14: [_ASI],
        15: [
            {"name": "Martial Archetype Feature", "rarity": "epic",
             "description": "Your Martial Archetype grants a powerful feature.",
             "mechanical": "Subclass feature"},
        ],
        16: [_ASI],
        18: [
            {"name": "Martial Archetype Capstone", "rarity": "epic",
             "description": "Your Martial Archetype grants its ultimate feature.",
             "mechanical": "Subclass capstone"},
        ],
        19: [_ASI],
        20: [
            {"name": "Extra Attack (4)", "rarity": "legendary",
             "description": "Attack four times when you take the Attack action — the pinnacle of martial mastery.",
             "mechanical": "4 attacks per Attack action"},
        ],
    },

    # ── MONK ──────────────────────────────────────────────────────────────────
    "Monk": {
        2: [
            {"name": "Ki", "rarity": "epic",
             "description": "Channel mystic energy through Ki points (equal to monk level). Spend them on Flurry of Blows, Patient Defense, and Step of the Wind. Refresh on short rest.",
             "mechanical": "Ki pts = level · refresh short rest", "per_day": False, "uses_max": 2},
            {"name": "Flurry of Blows", "rarity": "rare",
             "description": "Spend 1 ki after the Attack action: make two unarmed strikes as a bonus action.",
             "mechanical": "1 ki: +2 unarmed strikes (bonus action)"},
            {"name": "Patient Defense", "rarity": "rare",
             "description": "Spend 1 ki as a bonus action: Dodge until the start of your next turn.",
             "mechanical": "1 ki: Dodge (bonus action)"},
            {"name": "Step of the Wind", "rarity": "rare",
             "description": "Spend 1 ki as a bonus action: Disengage or Dash, and your jump distance doubles this turn.",
             "mechanical": "1 ki: Disengage/Dash + 2× jump (bonus action)"},
            {"name": "Unarmored Movement", "rarity": "rare",
             "description": "Speed increases by 10 ft while unarmored and unshielded. Increases to +20 at level 9; lets you run on walls and water at level 9.",
             "mechanical": "+10 ft speed unarmored (scales)"},
        ],
        3: [
            {"name": "Monastic Tradition", "rarity": "epic",
             "description": "Choose your Monastic Tradition (Open Hand, Shadow, Four Elements, etc.) — shapes how you channel ki.",
             "mechanical": "Subclass unlock"},
            {"name": "Deflect Missiles", "rarity": "rare",
             "description": "React to reduce ranged weapon damage by 1d10 + DEX + monk level. If reduced to 0, catch it and throw it back (1 ki).",
             "mechanical": "React: −1d10+DEX+level missile dmg · catch & throw (1 ki)"},
        ],
        4: [
            {"name": "Slow Fall", "rarity": "common",
             "description": "React to reduce falling damage by 5 × monk level.",
             "mechanical": "React: −5×level fall damage"},
            _ASI,
        ],
        5: [
            {"name": "Extra Attack (2)", "rarity": "epic",
             "description": "Attack twice when you take the Attack action.",
             "mechanical": "2 attacks per Attack action"},
            {"name": "Stunning Strike", "rarity": "epic",
             "description": "Spend 1 ki when you hit with a melee attack: target makes a CON save (DC 8+prof+WIS) or is stunned until end of your next turn.",
             "mechanical": "1 ki: stun on hit · CON save DC 8+prof+WIS"},
            {"name": "Martial Arts", "upgrades": True, "rarity": "rare",
             "description": "Use DEX for unarmed/monk weapon attacks; bonus-action unarmed strike when you attack. Unarmed die: 1d6.",
             "mechanical": "DEX-based fists · 1d6 unarmed"},
        ],
        6: [
            {"name": "Ki-Empowered Strikes", "rarity": "rare",
             "description": "Your unarmed strikes count as magical for overcoming resistance and immunity.",
             "mechanical": "Unarmed strikes bypass nonmagical resistance"},
            {"name": "Monastic Tradition Feature", "rarity": "rare",
             "description": "Your Monastic Tradition grants a feature.",
             "mechanical": "Subclass feature"},
            {"name": "Unarmored Movement", "upgrades": True, "rarity": "rare",
             "description": "Speed increases by 15 ft while unarmored and unshielded.",
             "mechanical": "+15 ft speed unarmored"},
        ],
        7: [
            {"name": "Evasion", "rarity": "epic",
             "description": "Effects that deal half damage on a DEX save: take no damage on success, half on failure.",
             "mechanical": "DEX save success: no damage"},
            {"name": "Stillness of Mind", "rarity": "rare",
             "description": "Use your action to end one charmed or frightened condition on yourself.",
             "mechanical": "Action: remove charm or frightened"},
        ],
        8: [_ASI],
        9: [
            {"name": "Unarmored Movement (Surfaces)", "rarity": "rare",
             "description": "You can run up vertical surfaces and across liquids on your turn without falling.",
             "mechanical": "Run on walls and water"},
        ],
        10: [
            {"name": "Purity of Body", "rarity": "rare",
             "description": "Your ki cleanses your body — immune to disease and poison.",
             "mechanical": "Immune: disease · poison"},
            {"name": "Monastic Tradition Feature", "rarity": "rare",
             "description": "Your Monastic Tradition grants another feature.",
             "mechanical": "Subclass feature"},
            {"name": "Unarmored Movement", "upgrades": True, "rarity": "rare",
             "description": "Speed increases by 20 ft while unarmored and unshielded.",
             "mechanical": "+20 ft speed unarmored"},
        ],
        11: [
            {"name": "Tranquility", "rarity": "rare",
             "description": "End each long rest with the benefit of the Sanctuary spell on yourself. Breaks if you attack.",
             "mechanical": "Sanctuary effect after each long rest"},
            {"name": "Martial Arts", "upgrades": True, "rarity": "epic",
             "description": "Use DEX for unarmed/monk weapon attacks; bonus-action unarmed strike when you attack. Unarmed die: 1d8.",
             "mechanical": "DEX-based fists · 1d8 unarmed"},
        ],
        12: [_ASI],
        13: [
            {"name": "Tongue of Sun and Moon", "rarity": "rare",
             "description": "You understand and are understood by any creature that has a language.",
             "mechanical": "Comprehend and speak any language"},
        ],
        14: [
            {"name": "Diamond Soul", "rarity": "epic",
             "description": "Proficiency in all saving throws. Spend 1 ki to reroll any failed save.",
             "mechanical": "Prof in all saves · 1 ki: reroll failed save"},
            {"name": "Monastic Tradition Feature", "rarity": "epic",
             "description": "Your Monastic Tradition grants a powerful feature.",
             "mechanical": "Subclass feature"},
            {"name": "Unarmored Movement", "upgrades": True, "rarity": "rare",
             "description": "Speed increases by 25 ft while unarmored and unshielded.",
             "mechanical": "+25 ft speed unarmored"},
        ],
        15: [
            {"name": "Timeless Body", "rarity": "rare",
             "description": "Ki sustains you — no need for food or water; you age 1 year per 10.",
             "mechanical": "No food/water · 1/10th aging"},
        ],
        16: [_ASI],
        17: [
            {"name": "Monastic Tradition Feature", "rarity": "epic",
             "description": "Your Monastic Tradition grants its most powerful feature.",
             "mechanical": "Subclass capstone"},
            {"name": "Martial Arts", "upgrades": True, "rarity": "epic",
             "description": "Use DEX for unarmed/monk weapon attacks; bonus-action unarmed strike when you attack. Unarmed die: 1d10.",
             "mechanical": "DEX-based fists · 1d10 unarmed"},
        ],
        18: [
            {"name": "Empty Body", "rarity": "legendary",
             "description": "Spend 4 ki: become invisible for 1 minute with resistance to all damage except force. Or 8 ki to cast Astral Projection.",
             "mechanical": "4 ki: invisible+all resist 1 min · 8 ki: astral projection"},
            {"name": "Unarmored Movement", "upgrades": True, "rarity": "rare",
             "description": "Speed increases by 30 ft while unarmored and unshielded.",
             "mechanical": "+30 ft speed unarmored"},
        ],
        19: [_ASI],
        20: [
            {"name": "Perfect Self", "rarity": "legendary",
             "description": "When you roll Initiative and have no ki points, regain 4 ki points instantly.",
             "mechanical": "Regain 4 ki on initiative when empty"},
        ],
    },

    # ── PALADIN ───────────────────────────────────────────────────────────────
    "Paladin": {
        2: [
            {"name": "Fighting Style", "rarity": "rare",
             "description": "Adopt a combat style — Defense, Dueling, Great Weapon Fighting, or Protection.",
             "mechanical": "Style-specific bonus"},
            {"name": "Spellcasting", "rarity": "epic",
             "description": "Cast paladin spells (CHA-based). Prepare spells daily equal to CHA mod + half paladin level. Slots refresh on long rest.",
             "mechanical": "CHA-based · long rest slots", "per_day": True, "uses_max": 2},
            {"name": "Divine Smite", "rarity": "epic",
             "description": "When you hit with a melee weapon attack, expend a spell slot to deal bonus radiant damage: 2d8 + 1d8 per slot level above 1st. +1d8 vs undead/fiends. Max 5d8.",
             "mechanical": "Hit: spend slot → +2d8 radiant (scales, max 5d8)"},
        ],
        3: [
            {"name": "Divine Health", "rarity": "rare",
             "description": "Divine magic flowing through you makes you immune to disease.",
             "mechanical": "Immune to disease"},
            {"name": "Sacred Oath", "rarity": "epic",
             "description": "Swear your Sacred Oath (Devotion, Ancients, Vengeance, etc.) — Channel Divinity options and oath spells unlocked.",
             "mechanical": "Subclass unlock · oath spells · Channel Divinity"},
        ],
        4: [_ASI],
        5: [
            {"name": "Extra Attack (2)", "rarity": "epic",
             "description": "Attack twice when you take the Attack action.",
             "mechanical": "2 attacks per Attack action"},
        ],
        6: [
            {"name": "Aura of Protection", "rarity": "legendary",
             "description": "You and friendly creatures within 10 ft add your CHA modifier to all saving throws (min +1) while you are conscious. Extends to 30 ft at level 18.",
             "mechanical": "+CHA to all saves · allies within 10 ft (30 ft at lvl 18)"},
        ],
        7: [
            {"name": "Sacred Oath Feature", "rarity": "rare",
             "description": "Your Sacred Oath grants a feature.",
             "mechanical": "Subclass feature"},
        ],
        8: [_ASI],
        10: [
            {"name": "Aura of Courage", "rarity": "epic",
             "description": "You and friendly creatures within 10 ft cannot be frightened while you are conscious. Extends to 30 ft at level 18.",
             "mechanical": "Allies immune to frightened within 10 ft"},
        ],
        11: [
            {"name": "Improved Divine Smite", "rarity": "epic",
             "description": "All melee weapon hits automatically deal an extra 1d8 radiant damage, in addition to any expended-slot Divine Smite.",
             "mechanical": "All melee hits: +1d8 radiant (free)"},
        ],
        12: [_ASI],
        14: [
            {"name": "Cleansing Touch", "rarity": "rare",
             "description": "Action: end one spell effect on yourself or a willing creature. Uses = CHA modifier per long rest.",
             "mechanical": "CHA-mod uses/long rest · end a spell effect (action)",
             "per_day": True, "uses_max": 2},
        ],
        15: [
            {"name": "Sacred Oath Feature", "rarity": "epic",
             "description": "Your Sacred Oath grants a powerful feature.",
             "mechanical": "Subclass feature"},
        ],
        16: [_ASI],
        19: [_ASI],
        20: [
            {"name": "Sacred Oath Capstone", "rarity": "legendary",
             "description": "Your Sacred Oath grants its ultimate power — a transformation or supreme ability unique to your sworn path.",
             "mechanical": "Subclass capstone"},
        ],
    },

    # ── RANGER ────────────────────────────────────────────────────────────────
    "Ranger": {
        2: [
            {"name": "Fighting Style", "rarity": "rare",
             "description": "Adopt a combat style — Archery, Defense, Dueling, or Two-Weapon Fighting.",
             "mechanical": "Style-specific bonus"},
            {"name": "Spellcasting", "rarity": "epic",
             "description": "Cast ranger spells (WIS-based). Spells known; spell slots refresh on long rest.",
             "mechanical": "WIS-based spellcasting · long rest slots", "per_day": True, "uses_max": 2},
        ],
        3: [
            {"name": "Ranger Archetype", "rarity": "epic",
             "description": "Choose your Ranger Archetype (Hunter, Beast Master, Gloom Stalker, etc.) — your hunting and survival specialty.",
             "mechanical": "Subclass unlock"},
            {"name": "Primeval Awareness", "rarity": "rare",
             "description": "Spend a spell slot: sense the presence and direction of specific creature types within 1 mile (6 miles in your favored terrain) for 1 min per slot level.",
             "mechanical": "Spell slot: detect creature types within 1 mile"},
        ],
        4: [_ASI],
        5: [
            {"name": "Extra Attack (2)", "rarity": "epic",
             "description": "Attack twice when you take the Attack action.",
             "mechanical": "2 attacks per Attack action"},
        ],
        6: [
            {"name": "Favored Enemy (2nd)", "rarity": "rare",
             "description": "Choose a second Favored Enemy type. You now track two creature types.",
             "mechanical": "+1 Favored Enemy type"},
            {"name": "Natural Explorer (2nd)", "rarity": "rare",
             "description": "Choose a second Favored Terrain type.",
             "mechanical": "+1 Favored Terrain type"},
        ],
        7: [
            {"name": "Ranger Archetype Feature", "rarity": "rare",
             "description": "Your Ranger Archetype grants a feature.",
             "mechanical": "Subclass feature"},
        ],
        8: [
            {"name": "Land's Stride", "rarity": "rare",
             "description": "Move through nonmagical difficult terrain of plants without penalty or damage. Advantage on saves vs. magically created plants.",
             "mechanical": "Ignore plant terrain · adv vs magic plants"},
            _ASI,
        ],
        10: [
            {"name": "Natural Explorer (3rd)", "rarity": "rare",
             "description": "Choose a third Favored Terrain type.",
             "mechanical": "+1 Favored Terrain type"},
            {"name": "Hide in Plain Sight", "rarity": "epic",
             "description": "Spend 1 minute camouflaging yourself with natural materials — gain +10 to Stealth checks while motionless against creatures that pass by.",
             "mechanical": "+10 Stealth while motionless (1 min setup)"},
        ],
        11: [
            {"name": "Ranger Archetype Feature", "rarity": "rare",
             "description": "Your Ranger Archetype grants another feature.",
             "mechanical": "Subclass feature"},
        ],
        12: [_ASI],
        14: [
            {"name": "Favored Enemy (3rd)", "rarity": "rare",
             "description": "Choose a third Favored Enemy and learn one language they speak.",
             "mechanical": "+1 Favored Enemy type + language"},
            {"name": "Vanish", "rarity": "epic",
             "description": "Use Hide as a bonus action. You also can't be tracked by nonmagical means unless you choose to leave a trail.",
             "mechanical": "Bonus action Hide · untraceable by nonmagic means"},
        ],
        15: [
            {"name": "Ranger Archetype Feature", "rarity": "epic",
             "description": "Your Ranger Archetype grants a powerful feature.",
             "mechanical": "Subclass feature"},
        ],
        16: [_ASI],
        18: [
            {"name": "Feral Senses", "rarity": "epic",
             "description": "Can't be surprised while conscious. Attack invisible creatures without disadvantage — you sense their exact location.",
             "mechanical": "Can't be surprised · attack invisible without disadv"},
        ],
        19: [_ASI],
        20: [
            {"name": "Foe Slayer", "rarity": "legendary",
             "description": "Once per turn, add your WIS modifier to the attack roll or the damage roll of an attack against a Favored Enemy.",
             "mechanical": "+WIS mod once/turn vs Favored Enemy"},
        ],
    },

    # ── ROGUE ─────────────────────────────────────────────────────────────────
    "Rogue": {
        2: [
            {"name": "Cunning Action", "rarity": "epic",
             "description": "Bonus action on your turn: Dash, Disengage, or Hide.",
             "mechanical": "Bonus action: Dash / Disengage / Hide"},
        ],
        3: [
            {"name": "Roguish Archetype", "rarity": "epic",
             "description": "Choose your Roguish Archetype (Thief, Assassin, Arcane Trickster, etc.) — your criminal or shadow specialty.",
             "mechanical": "Subclass unlock"},
            {"name": "Sneak Attack", "upgrades": True, "rarity": "epic",
             "description": "Once per turn deal +2d6 damage when you have advantage or an ally is adjacent to the target.",
             "mechanical": "+2d6 per turn"},
        ],
        4: [_ASI],
        5: [
            {"name": "Uncanny Dodge", "rarity": "epic",
             "description": "When an attacker you can see hits you, use your reaction to halve the attack's damage.",
             "mechanical": "Reaction: halve one incoming attack's damage"},
            {"name": "Sneak Attack", "upgrades": True, "rarity": "epic",
             "description": "Once per turn deal +3d6 damage when you have advantage or an ally is adjacent to the target.",
             "mechanical": "+3d6 per turn"},
        ],
        6: [
            {"name": "Expertise (2nd)", "rarity": "rare",
             "description": "Double your proficiency bonus on two more skill checks.",
             "mechanical": "+2 more skills doubled"},
        ],
        7: [
            {"name": "Evasion", "rarity": "epic",
             "description": "Effects that deal half damage on a DEX save: take no damage on success, half on failure.",
             "mechanical": "DEX save success: no damage"},
            {"name": "Sneak Attack", "upgrades": True, "rarity": "epic",
             "description": "Once per turn deal +4d6 damage when you have advantage or an ally is adjacent to the target.",
             "mechanical": "+4d6 per turn"},
        ],
        8: [_ASI],
        9: [
            {"name": "Roguish Archetype Feature", "rarity": "rare",
             "description": "Your Roguish Archetype grants a feature.",
             "mechanical": "Subclass feature"},
            {"name": "Sneak Attack", "upgrades": True, "rarity": "epic",
             "description": "Once per turn deal +5d6 damage when you have advantage or an ally is adjacent to the target.",
             "mechanical": "+5d6 per turn"},
        ],
        10: [_ASI],
        11: [
            {"name": "Reliable Talent", "rarity": "epic",
             "description": "When you make a skill check you have proficiency in, treat any d20 result of 9 or lower as a 10.",
             "mechanical": "Prof skill checks: minimum roll of 10"},
            {"name": "Sneak Attack", "upgrades": True, "rarity": "epic",
             "description": "Once per turn deal +6d6 damage when you have advantage or an ally is adjacent to the target.",
             "mechanical": "+6d6 per turn"},
        ],
        12: [_ASI],
        13: [
            {"name": "Roguish Archetype Feature", "rarity": "rare",
             "description": "Your Roguish Archetype grants another feature.",
             "mechanical": "Subclass feature"},
            {"name": "Sneak Attack", "upgrades": True, "rarity": "epic",
             "description": "Once per turn deal +7d6 damage when you have advantage or an ally is adjacent to the target.",
             "mechanical": "+7d6 per turn"},
        ],
        14: [
            {"name": "Blindsense", "rarity": "rare",
             "description": "If you can hear, you are aware of the location of any hidden or invisible creature within 10 ft.",
             "mechanical": "Locate hidden/invisible creatures within 10 ft by sound"},
        ],
        15: [
            {"name": "Slippery Mind", "rarity": "rare",
             "description": "You gain proficiency in Wisdom saving throws.",
             "mechanical": "Proficiency: WIS saves"},
            {"name": "Sneak Attack", "upgrades": True, "rarity": "epic",
             "description": "Once per turn deal +8d6 damage when you have advantage or an ally is adjacent to the target.",
             "mechanical": "+8d6 per turn"},
        ],
        16: [_ASI],
        17: [
            {"name": "Roguish Archetype Feature", "rarity": "epic",
             "description": "Your Roguish Archetype grants a powerful feature.",
             "mechanical": "Subclass feature"},
            {"name": "Sneak Attack", "upgrades": True, "rarity": "epic",
             "description": "Once per turn deal +9d6 damage when you have advantage or an ally is adjacent to the target.",
             "mechanical": "+9d6 per turn"},
        ],
        18: [
            {"name": "Elusive", "rarity": "legendary",
             "description": "No attack roll ever has advantage against you while you aren't incapacitated.",
             "mechanical": "No attacker ever has advantage against you"},
        ],
        19: [
            _ASI,
            {"name": "Sneak Attack", "upgrades": True, "rarity": "legendary",
             "description": "Once per turn deal +10d6 damage when you have advantage or an ally is adjacent to the target.",
             "mechanical": "+10d6 per turn"},
        ],
        20: [
            {"name": "Stroke of Luck", "rarity": "legendary",
             "description": "Once per short rest: turn a missed attack into a hit, or treat a failed ability check as a natural 20.",
             "mechanical": "1/short rest: miss→hit OR fail→nat 20", "per_day": False, "uses_max": 1},
        ],
    },

    # ── SORCERER ──────────────────────────────────────────────────────────────
    "Sorcerer": {
        2: [
            {"name": "Font of Magic", "rarity": "epic",
             "description": "You have Sorcery Points equal to your level. Convert them to/from spell slots or spend them on Metamagic. Refresh on long rest.",
             "mechanical": "Sorcery pts = level · convert to/from spell slots", "per_day": True, "uses_max": 2},
        ],
        3: [
            {"name": "Metamagic", "rarity": "epic",
             "description": "Choose 2 Metamagic options to reshape your spells: Careful (protect allies), Distant, Empowered, Extended, Heightened, Quickened, Subtle, or Twinned.",
             "mechanical": "2 Metamagic options — spend sorcery pts to activate"},
        ],
        4: [_ASI],
        6: [
            {"name": "Sorcerous Origin Feature", "rarity": "rare",
             "description": "Your Sorcerous Origin grants a feature.",
             "mechanical": "Subclass feature"},
        ],
        8: [_ASI],
        10: [
            {"name": "Metamagic (3rd option)", "rarity": "rare",
             "description": "Learn a third Metamagic option.",
             "mechanical": "3 Metamagic options total"},
        ],
        12: [_ASI],
        14: [
            {"name": "Sorcerous Origin Feature", "rarity": "epic",
             "description": "Your Sorcerous Origin grants a major feature.",
             "mechanical": "Subclass feature"},
        ],
        16: [_ASI],
        17: [
            {"name": "Metamagic (4th option)", "rarity": "rare",
             "description": "Learn a fourth Metamagic option.",
             "mechanical": "4 Metamagic options total"},
        ],
        18: [
            {"name": "Sorcerous Origin Capstone", "rarity": "epic",
             "description": "Your Sorcerous Origin grants its ultimate feature.",
             "mechanical": "Subclass capstone"},
        ],
        19: [_ASI],
        20: [
            {"name": "Sorcerous Restoration", "rarity": "legendary",
             "description": "Regain 4 spent Sorcery Points whenever you finish a short rest.",
             "mechanical": "Regain 4 sorcery pts on short rest"},
        ],
    },

    # ── WARLOCK ───────────────────────────────────────────────────────────────
    "Warlock": {
        2: [
            {"name": "Eldritch Invocations", "rarity": "epic",
             "description": "Learn 2 Eldritch Invocations — permanent enhancements to your abilities (Agonizing Blast, Devil's Sight, Mask of Many Faces, etc.). Gain more at higher levels.",
             "mechanical": "2 invocations (scales with level)"},
        ],
        3: [
            {"name": "Pact Boon", "rarity": "epic",
             "description": "Your patron's gift: Pact of the Blade (summoned weapon), Pact of the Chain (powerful familiar), or Pact of the Tome (three cantrips + Book of Shadows).",
             "mechanical": "Blade · Chain · or Tome pact gift"},
        ],
        4: [_ASI],
        6: [
            {"name": "Otherworldly Patron Feature", "rarity": "rare",
             "description": "Your patron grants a feature tied to their nature.",
             "mechanical": "Subclass feature"},
        ],
        8: [_ASI],
        10: [
            {"name": "Otherworldly Patron Feature", "rarity": "epic",
             "description": "Your patron grants a major feature.",
             "mechanical": "Subclass feature"},
        ],
        11: [
            {"name": "Mystic Arcanum (6th)", "rarity": "epic",
             "description": "Your patron bestows knowledge of one 6th-level spell, castable once per long rest without a slot.",
             "mechanical": "1 sixth-level spell/long rest", "per_day": True, "uses_max": 1},
        ],
        12: [_ASI],
        13: [
            {"name": "Mystic Arcanum (7th)", "rarity": "epic",
             "description": "Your patron grants a 7th-level spell, once per long rest.",
             "mechanical": "1 seventh-level spell/long rest", "per_day": True, "uses_max": 1},
        ],
        14: [
            {"name": "Otherworldly Patron Capstone", "rarity": "epic",
             "description": "Your patron grants its most powerful feature.",
             "mechanical": "Subclass capstone"},
        ],
        15: [
            {"name": "Mystic Arcanum (8th)", "rarity": "epic",
             "description": "Your patron grants an 8th-level spell, once per long rest.",
             "mechanical": "1 eighth-level spell/long rest", "per_day": True, "uses_max": 1},
        ],
        16: [_ASI],
        17: [
            {"name": "Mystic Arcanum (9th)", "rarity": "legendary",
             "description": "Your patron grants a 9th-level spell — the most powerful magic in existence. Once per long rest.",
             "mechanical": "1 ninth-level spell/long rest", "per_day": True, "uses_max": 1},
        ],
        19: [_ASI],
        20: [
            {"name": "Eldritch Master", "rarity": "legendary",
             "description": "Spend 1 minute entreating your patron — regain all Pact Magic spell slots. Once per long rest.",
             "mechanical": "1 min ritual: restore all pact slots · 1/long rest", "per_day": True, "uses_max": 1},
        ],
    },

    # ── WIZARD ────────────────────────────────────────────────────────────────
    "Wizard": {
        2: [
            {"name": "Arcane Tradition", "rarity": "epic",
             "description": "Choose your Arcane Tradition (Evocation, Abjuration, Conjuration, Illusion, etc.) — your school of magical mastery.",
             "mechanical": "Subclass unlock"},
        ],
        4: [_ASI],
        6: [
            {"name": "Arcane Tradition Feature", "rarity": "rare",
             "description": "Your Arcane Tradition grants a feature.",
             "mechanical": "Subclass feature"},
        ],
        8: [_ASI],
        10: [
            {"name": "Arcane Tradition Feature", "rarity": "rare",
             "description": "Your Arcane Tradition grants another feature.",
             "mechanical": "Subclass feature"},
        ],
        12: [_ASI],
        14: [
            {"name": "Arcane Tradition Feature", "rarity": "epic",
             "description": "Your Arcane Tradition grants a major feature.",
             "mechanical": "Subclass feature"},
        ],
        16: [_ASI],
        18: [
            {"name": "Spell Mastery", "rarity": "legendary",
             "description": "Choose one 1st-level and one 2nd-level spell from your spellbook — cast them at minimum level without expending a spell slot.",
             "mechanical": "1 first + 1 second-level spell: free cast always"},
        ],
        19: [_ASI],
        20: [
            {"name": "Signature Spells", "rarity": "legendary",
             "description": "Choose two 3rd-level spells from your spellbook as signatures — always prepared, and each castable once per short rest for free.",
             "mechanical": "2 third-level spells: 1 free cast each/short rest",
             "per_day": False, "uses_max": 2},
        ],
    },
}


def get_level_up_cards(class_key: str, new_level: int) -> List[Dict]:
    """Return the feature cards granted when a character reaches `new_level`.

    Returns an empty list if the class has no defined features at that level.
    Cards use the same schema as CLASS_FEATURES_LEVEL_1 entries.
    """
    return list(CLASS_FEATURES_BY_LEVEL.get(class_key, {}).get(new_level, []))

