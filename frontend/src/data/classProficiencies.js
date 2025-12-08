/**
 * D&D 5e Class Proficiencies
 * Tool, Weapon, and Armor proficiencies by class
 */

export const CLASS_PROFICIENCIES = {
  "Barbarian": {
    armor: ["Light Armor", "Medium Armor", "Shields"],
    weapons: ["Simple Weapons", "Martial Weapons"],
    tools: [],
    savingThrows: ["Strength", "Constitution"]
  },
  "Bard": {
    armor: ["Light Armor"],
    weapons: ["Simple Weapons", "Hand Crossbow", "Longsword", "Rapier", "Shortsword"],
    tools: ["Three Musical Instruments of choice"],
    savingThrows: ["Dexterity", "Charisma"]
  },
  "Cleric": {
    armor: ["Light Armor", "Medium Armor", "Shields"],
    weapons: ["Simple Weapons"],
    tools: [],
    savingThrows: ["Wisdom", "Charisma"]
  },
  "Druid": {
    armor: ["Light Armor", "Medium Armor", "Shields"],
    weapons: ["Club", "Dagger", "Dart", "Javelin", "Mace", "Quarterstaff", "Scimitar", "Sickle", "Sling", "Spear"],
    tools: ["Herbalism Kit"],
    savingThrows: ["Intelligence", "Wisdom"],
    restrictions: ["Cannot wear metal armor"]
  },
  "Fighter": {
    armor: ["Light Armor", "Medium Armor", "Heavy Armor", "Shields"],
    weapons: ["Simple Weapons", "Martial Weapons"],
    tools: [],
    savingThrows: ["Strength", "Constitution"]
  },
  "Monk": {
    armor: [],
    weapons: ["Simple Weapons", "Shortsword"],
    tools: ["One type of artisan's tools or one musical instrument"],
    savingThrows: ["Strength", "Dexterity"],
    restrictions: ["Cannot wear armor or use shields while using Unarmored Defense"]
  },
  "Paladin": {
    armor: ["Light Armor", "Medium Armor", "Heavy Armor", "Shields"],
    weapons: ["Simple Weapons", "Martial Weapons"],
    tools: [],
    savingThrows: ["Wisdom", "Charisma"]
  },
  "Ranger": {
    armor: ["Light Armor", "Medium Armor", "Shields"],
    weapons: ["Simple Weapons", "Martial Weapons"],
    tools: [],
    savingThrows: ["Strength", "Dexterity"]
  },
  "Rogue": {
    armor: ["Light Armor"],
    weapons: ["Simple Weapons", "Hand Crossbow", "Longsword", "Rapier", "Shortsword"],
    tools: ["Thieves' Tools"],
    savingThrows: ["Dexterity", "Intelligence"],
    special: "Expertise in Thieves' Tools (double proficiency bonus)"
  },
  "Sorcerer": {
    armor: [],
    weapons: ["Dagger", "Dart", "Sling", "Quarterstaff", "Light Crossbow"],
    tools: [],
    savingThrows: ["Constitution", "Charisma"]
  },
  "Warlock": {
    armor: ["Light Armor"],
    weapons: ["Simple Weapons"],
    tools: [],
    savingThrows: ["Wisdom", "Charisma"]
  },
  "Wizard": {
    armor: [],
    weapons: ["Dagger", "Dart", "Sling", "Quarterstaff", "Light Crossbow"],
    tools: [],
    savingThrows: ["Intelligence", "Wisdom"]
  }
};

// Weapon categories
export const WEAPON_CATEGORIES = {
  "Simple Melee": ["Club", "Dagger", "Greatclub", "Handaxe", "Javelin", "Light Hammer", "Mace", "Quarterstaff", "Sickle", "Spear"],
  "Simple Ranged": ["Light Crossbow", "Dart", "Shortbow", "Sling"],
  "Martial Melee": ["Battleaxe", "Flail", "Glaive", "Greataxe", "Greatsword", "Halberd", "Lance", "Longsword", "Maul", "Morningstar", "Pike", "Rapier", "Scimitar", "Shortsword", "Trident", "War Pick", "Warhammer", "Whip"],
  "Martial Ranged": ["Blowgun", "Hand Crossbow", "Heavy Crossbow", "Longbow"]
};

// Armor categories
export const ARMOR_CATEGORIES = {
  "Light Armor": ["Padded", "Leather", "Studded Leather"],
  "Medium Armor": ["Hide", "Chain Shirt", "Scale Mail", "Breastplate", "Half Plate"],
  "Heavy Armor": ["Ring Mail", "Chain Mail", "Splint", "Plate"]
};
