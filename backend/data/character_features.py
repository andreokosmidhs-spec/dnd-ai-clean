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


# Rarity ordering for sorting + visual prominence.
RARITY_ORDER = {"legendary": 0, "epic": 1, "rare": 2, "common": 3}
