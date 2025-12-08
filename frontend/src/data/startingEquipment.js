/**
 * D&D 5e Starting Equipment by Class
 * Each class gets specific starting gear and gold
 */

export const STARTING_EQUIPMENT = {
  "Barbarian": {
    gold: 50,
    items: [
      "Greataxe",
      "Handaxe (2)",
      "Javelin (4)",
      "Explorer's Pack",
      "Leather Armor"
    ]
  },
  "Bard": {
    gold: 100,
    items: [
      "Rapier",
      "Dagger",
      "Lute",
      "Leather Armor",
      "Diplomat's Pack"
    ]
  },
  "Cleric": {
    gold: 100,
    items: [
      "Mace",
      "Shield",
      "Scale Mail",
      "Light Crossbow",
      "Crossbow Bolts (20)",
      "Priest's Pack",
      "Holy Symbol"
    ]
  },
  "Druid": {
    gold: 50,
    items: [
      "Wooden Shield",
      "Scimitar",
      "Leather Armor",
      "Explorer's Pack",
      "Druidic Focus"
    ]
  },
  "Fighter": {
    gold: 100,
    items: [
      "Longsword",
      "Shield",
      "Chain Mail",
      "Light Crossbow",
      "Crossbow Bolts (20)",
      "Dungeoneer's Pack"
    ]
  },
  "Monk": {
    gold: 25,
    items: [
      "Shortsword",
      "Dart (10)",
      "Explorer's Pack"
    ]
  },
  "Paladin": {
    gold: 100,
    items: [
      "Longsword",
      "Shield",
      "Javelin (5)",
      "Chain Mail",
      "Priest's Pack",
      "Holy Symbol"
    ]
  },
  "Ranger": {
    gold: 100,
    items: [
      "Longbow",
      "Arrows (20)",
      "Shortsword (2)",
      "Scale Mail",
      "Explorer's Pack"
    ]
  },
  "Rogue": {
    gold: 100,
    items: [
      "Rapier",
      "Shortbow",
      "Arrows (20)",
      "Dagger (2)",
      "Leather Armor",
      "Burglar's Pack",
      "Thieves' Tools"
    ]
  },
  "Sorcerer": {
    gold: 75,
    items: [
      "Light Crossbow",
      "Crossbow Bolts (20)",
      "Dagger (2)",
      "Component Pouch",
      "Dungeoneer's Pack"
    ]
  },
  "Warlock": {
    gold: 100,
    items: [
      "Light Crossbow",
      "Crossbow Bolts (20)",
      "Dagger (2)",
      "Leather Armor",
      "Scholar's Pack",
      "Arcane Focus"
    ]
  },
  "Wizard": {
    gold: 100,
    items: [
      "Quarterstaff",
      "Dagger",
      "Component Pouch",
      "Scholar's Pack",
      "Spellbook"
    ]
  }
};

// Item properties for mechanical use
export const ITEM_PROPERTIES = {
  // Weapons
  "Greataxe": { type: "weapon", damage: "1d12", damageType: "slashing", properties: ["heavy", "two-handed"] },
  "Longsword": { type: "weapon", damage: "1d8", damageType: "slashing", properties: ["versatile"] },
  "Shortsword": { type: "weapon", damage: "1d6", damageType: "piercing", properties: ["finesse", "light"] },
  "Rapier": { type: "weapon", damage: "1d8", damageType: "piercing", properties: ["finesse"] },
  "Dagger": { type: "weapon", damage: "1d4", damageType: "piercing", properties: ["finesse", "light", "thrown"] },
  "Handaxe": { type: "weapon", damage: "1d6", damageType: "slashing", properties: ["light", "thrown"] },
  "Mace": { type: "weapon", damage: "1d6", damageType: "bludgeoning", properties: [] },
  "Quarterstaff": { type: "weapon", damage: "1d6", damageType: "bludgeoning", properties: ["versatile"] },
  "Scimitar": { type: "weapon", damage: "1d6", damageType: "slashing", properties: ["finesse", "light"] },
  "Shortbow": { type: "weapon", damage: "1d6", damageType: "piercing", properties: ["ammunition", "ranged"], range: "80/320" },
  "Longbow": { type: "weapon", damage: "1d8", damageType: "piercing", properties: ["ammunition", "heavy", "ranged", "two-handed"], range: "150/600" },
  "Light Crossbow": { type: "weapon", damage: "1d8", damageType: "piercing", properties: ["ammunition", "loading", "ranged", "two-handed"], range: "80/320" },
  "Javelin": { type: "weapon", damage: "1d6", damageType: "piercing", properties: ["thrown"], range: "30/120" },
  "Dart": { type: "weapon", damage: "1d4", damageType: "piercing", properties: ["finesse", "thrown"], range: "20/60" },
  
  // Armor
  "Leather Armor": { type: "armor", ac: 11, acType: "light", stealthDisadvantage: false },
  "Scale Mail": { type: "armor", ac: 14, acType: "medium", stealthDisadvantage: true },
  "Chain Mail": { type: "armor", ac: 16, acType: "heavy", stealthDisadvantage: true, strengthRequired: 13 },
  "Shield": { type: "armor", ac: 2, acType: "shield", stealthDisadvantage: false },
  
  // Tools & Equipment
  "Thieves' Tools": { type: "tool", use: "lockpicking" },
  "Holy Symbol": { type: "focus", class: "Cleric/Paladin" },
  "Druidic Focus": { type: "focus", class: "Druid" },
  "Arcane Focus": { type: "focus", class: "Sorcerer/Warlock/Wizard" },
  "Component Pouch": { type: "focus", class: "spellcaster" },
  "Spellbook": { type: "tool", class: "Wizard", use: "spell preparation" },
  "Lute": { type: "tool", class: "Bard", use: "spellcasting focus" },
  
  // Packs
  "Explorer's Pack": { type: "pack", contains: ["Backpack", "Bedroll", "Tinderbox", "Torch (10)", "Rations (10 days)", "Waterskin", "Rope (50 ft)"] },
  "Dungeoneer's Pack": { type: "pack", contains: ["Backpack", "Crowbar", "Hammer", "Piton (10)", "Torch (10)", "Tinderbox", "Rations (10 days)", "Waterskin", "Rope (50 ft)"] },
  "Priest's Pack": { type: "pack", contains: ["Backpack", "Blanket", "Candle (10)", "Tinderbox", "Alms Box", "Incense (2 blocks)", "Censer", "Vestments", "Rations (2 days)", "Waterskin"] },
  "Scholar's Pack": { type: "pack", contains: ["Backpack", "Book", "Ink", "Ink Pen", "Parchment (10 sheets)", "Sand", "Small Knife"] },
  "Diplomat's Pack": { type: "pack", contains: ["Chest", "Maps", "Fine Clothes", "Ink", "Ink Pen", "Lamp", "Oil (2 flasks)", "Parchment (5 sheets)", "Perfume", "Sealing Wax", "Soap"] },
  "Burglar's Pack": { type: "pack", contains: ["Backpack", "Ball Bearings (1,000)", "String (10 ft)", "Bell", "Candle (5)", "Crowbar", "Hammer", "Piton (10)", "Lantern", "Oil (2 flasks)", "Rations (5 days)", "Tinderbox", "Waterskin", "Rope (50 ft)"] },
  
  // Ammunition
  "Arrows": { type: "ammunition", for: "bow", count: 20 },
  "Crossbow Bolts": { type: "ammunition", for: "crossbow", count: 20 }
};
