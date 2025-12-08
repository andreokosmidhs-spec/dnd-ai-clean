/**
 * D&D 5e Race Data with Complete Mechanics
 * Includes: ASI, Size, Speed, Languages, Racial Traits
 */

export const raceData = {
  Human: {
    name: "Human",
    size: "Medium",
    speed: 30,
    asi: [
      { ability: "ALL", value: 1 } // All ability scores increase by 1
    ],
    languages: {
      base: ["Common"],
      choices: 1 // One extra language of choice
    },
    traits: [
      {
        name: "Versatile",
        summary: "Humans adapt to any environment and excel at many skills.",
        description: "Humans are adaptable and ambitious, able to thrive in many environments. All ability scores increase by 1, and you gain one extra language of your choice.",
        mechanical_effect: "+1 to all ability scores, +1 language choice"
      }
    ]
  },

  Elf: {
    name: "Elf",
    size: "Medium",
    speed: 30,
    asi: [
      { ability: "DEX", value: 2 }
    ],
    languages: {
      base: ["Common", "Elvish"],
      choices: 0
    },
    traits: [
      {
        name: "Darkvision",
        summary: "See in darkness up to 60 feet.",
        description: "Accustomed to twilit forests and the night sky, you have superior vision in dark and dim conditions. You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray.",
        mechanical_effect: "60 ft. darkvision"
      },
      {
        name: "Keen Senses",
        summary: "Proficiency in the Perception skill.",
        description: "You have proficiency in the Perception skill, reflecting your acute awareness of your surroundings.",
        mechanical_effect: "Proficiency: Perception"
      },
      {
        name: "Fey Ancestry",
        summary: "Advantage against being charmed, immune to magical sleep.",
        description: "You have advantage on saving throws against being charmed, and magic can't put you to sleep.",
        mechanical_effect: "Advantage vs. charm, immune to magical sleep"
      },
      {
        name: "Trance",
        summary: "4-hour rest instead of 8-hour sleep.",
        description: "Elves don't need to sleep. Instead, they meditate deeply, remaining semiconscious, for 4 hours a day. After resting in this way, you gain the same benefit that a human does from 8 hours of sleep.",
        mechanical_effect: "4-hour long rest"
      }
    ],
    subraces: {
      "High Elf": {
        name: "High Elf",
        asi: [
          { ability: "INT", value: 1 }
        ],
        traits: [
          {
            name: "Elf Weapon Training",
            summary: "Proficiency with longsword, shortsword, shortbow, and longbow.",
            description: "You have proficiency with the longsword, shortsword, shortbow, and longbow.",
            mechanical_effect: "Weapon proficiencies: longsword, shortsword, shortbow, longbow"
          },
          {
            name: "Cantrip",
            summary: "You know one cantrip from the wizard spell list.",
            description: "You know one cantrip of your choice from the wizard spell list. Intelligence is your spellcasting ability for it.",
            mechanical_effect: "1 wizard cantrip (INT-based)"
          },
          {
            name: "Extra Language",
            summary: "You can speak, read, and write one extra language of your choice.",
            description: "You can speak, read, and write one extra language of your choice.",
            mechanical_effect: "+1 language choice"
          }
        ]
      },
      "Wood Elf": {
        name: "Wood Elf",
        asi: [
          { ability: "WIS", value: 1 }
        ],
        traits: [
          {
            name: "Elf Weapon Training",
            summary: "Proficiency with longsword, shortsword, shortbow, and longbow.",
            description: "You have proficiency with the longsword, shortsword, shortbow, and longbow.",
            mechanical_effect: "Weapon proficiencies: longsword, shortsword, shortbow, longbow"
          },
          {
            name: "Fleet of Foot",
            summary: "Your base walking speed increases to 35 feet.",
            description: "Your base walking speed increases to 35 feet.",
            mechanical_effect: "Speed: 35 ft."
          },
          {
            name: "Mask of the Wild",
            summary: "You can attempt to hide when lightly obscured by natural phenomena.",
            description: "You can attempt to hide even when you are only lightly obscured by foliage, heavy rain, falling snow, mist, and other natural phenomena.",
            mechanical_effect: "Can hide in light natural cover"
          }
        ]
      },
      "Dark Elf (Drow)": {
        name: "Dark Elf (Drow)",
        asi: [
          { ability: "CHA", value: 1 }
        ],
        traits: [
          {
            name: "Superior Darkvision",
            summary: "Your darkvision has a radius of 120 feet.",
            description: "Your darkvision has a radius of 120 feet.",
            mechanical_effect: "120 ft. darkvision"
          },
          {
            name: "Sunlight Sensitivity",
            summary: "Disadvantage on attack rolls and Perception checks in sunlight.",
            description: "You have disadvantage on attack rolls and Wisdom (Perception) checks that rely on sight when you, the target of your attack, or whatever you are trying to perceive is in direct sunlight.",
            mechanical_effect: "Disadvantage in sunlight"
          },
          {
            name: "Drow Magic",
            summary: "You know the dancing lights cantrip. At 3rd level, cast faerie fire once per long rest. At 5th level, cast darkness once per long rest.",
            description: "You know the dancing lights cantrip. When you reach 3rd level, you can cast the faerie fire spell once with this trait and regain the ability to do so when you finish a long rest. When you reach 5th level, you can cast the darkness spell once with this trait and regain the ability to do so when you finish a long rest. Charisma is your spellcasting ability for these spells.",
            mechanical_effect: "Dancing Lights cantrip, Faerie Fire 1/day (3rd level), Darkness 1/day (5th level)"
          },
          {
            name: "Drow Weapon Training",
            summary: "Proficiency with rapiers, shortswords, and hand crossbows.",
            description: "You have proficiency with rapiers, shortswords, and hand crossbows.",
            mechanical_effect: "Weapon proficiencies: rapier, shortsword, hand crossbow"
          }
        ]
      }
    }
  },

  Dwarf: {
    name: "Dwarf",
    size: "Medium",
    speed: 25,
    asi: [
      { ability: "CON", value: 2 }
    ],
    languages: {
      base: ["Common", "Dwarvish"],
      choices: 0
    },
    traits: [
      {
        name: "Darkvision",
        summary: "See in darkness up to 60 feet.",
        description: "Accustomed to life underground, you have superior vision in dark and dim conditions. You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray.",
        mechanical_effect: "60 ft. darkvision"
      },
      {
        name: "Dwarven Resilience",
        summary: "Advantage on saves vs. poison, resistance to poison damage.",
        description: "You have advantage on saving throws against poison, and you have resistance against poison damage.",
        mechanical_effect: "Advantage vs. poison, resistance to poison damage"
      },
      {
        name: "Dwarven Combat Training",
        summary: "Proficiency with battleaxe, handaxe, light hammer, and warhammer.",
        description: "You have proficiency with the battleaxe, handaxe, light hammer, and warhammer.",
        mechanical_effect: "Weapon proficiencies: battleaxe, handaxe, light hammer, warhammer"
      },
      {
        name: "Tool Proficiency",
        summary: "Gain proficiency with one artisan's tool.",
        description: "You gain proficiency with the artisan's tools of your choice: smith's tools, brewer's supplies, or mason's tools.",
        mechanical_effect: "Proficiency: 1 artisan's tool (smith's tools, brewer's supplies, or mason's tools)"
      },
      {
        name: "Stonecunning",
        summary: "Double proficiency bonus on History checks related to stone.",
        description: "Whenever you make an Intelligence (History) check related to the origin of stonework, you are considered proficient in the History skill and add double your proficiency bonus to the check, instead of your normal proficiency bonus.",
        mechanical_effect: "Expertise: History (stonework only)"
      }
    ],
    subraces: {
      "Hill Dwarf": {
        name: "Hill Dwarf",
        asi: [
          { ability: "WIS", value: 1 }
        ],
        traits: [
          {
            name: "Dwarven Toughness",
            summary: "Your hit point maximum increases by 1 per level.",
            description: "Your hit point maximum increases by 1, and it increases by 1 every time you gain a level.",
            mechanical_effect: "+1 HP per level"
          }
        ]
      },
      "Mountain Dwarf": {
        name: "Mountain Dwarf",
        asi: [
          { ability: "STR", value: 2 }
        ],
        traits: [
          {
            name: "Dwarven Armor Training",
            summary: "Proficiency with light and medium armor.",
            description: "You have proficiency with light and medium armor.",
            mechanical_effect: "Armor proficiencies: light, medium"
          }
        ]
      }
    }
  },

  Halfling: {
    name: "Halfling",
    size: "Small",
    speed: 25,
    asi: [
      { ability: "DEX", value: 2 }
    ],
    languages: {
      base: ["Common", "Halfling"],
      choices: 0
    },
    traits: [
      {
        name: "Lucky",
        summary: "Reroll natural 1s on attack rolls, ability checks, and saving throws.",
        description: "When you roll a 1 on an attack roll, ability check, or saving throw, you can reroll the die and must use the new roll.",
        mechanical_effect: "Reroll natural 1s (once per roll)"
      },
      {
        name: "Brave",
        summary: "Advantage on saving throws against being frightened.",
        description: "You have advantage on saving throws against being frightened.",
        mechanical_effect: "Advantage vs. frightened condition"
      },
      {
        name: "Halfling Nimbleness",
        summary: "Move through spaces of larger creatures.",
        description: "You can move through the space of any creature that is of a size larger than yours.",
        mechanical_effect: "Can move through larger creatures' spaces"
      }
    ],
    subraces: {
      "Lightfoot Halfling": {
        name: "Lightfoot Halfling",
        asi: [
          { ability: "CHA", value: 1 }
        ],
        traits: [
          {
            name: "Naturally Stealthy",
            summary: "You can attempt to hide even when obscured only by a creature one size larger than you.",
            description: "You can attempt to hide even when you are obscured only by a creature that is at least one size larger than you.",
            mechanical_effect: "Can hide behind larger creatures"
          }
        ]
      },
      "Stout Halfling": {
        name: "Stout Halfling",
        asi: [
          { ability: "CON", value: 1 }
        ],
        traits: [
          {
            name: "Stout Resilience",
            summary: "Advantage on saves vs. poison, resistance to poison damage.",
            description: "You have advantage on saving throws against poison, and you have resistance against poison damage.",
            mechanical_effect: "Advantage vs. poison, resistance to poison damage"
          }
        ]
      }
    }
  },

  Dragonborn: {
    name: "Dragonborn",
    size: "Medium",
    speed: 30,
    asi: [
      { ability: "STR", value: 2 },
      { ability: "CHA", value: 1 }
    ],
    languages: {
      base: ["Common", "Draconic"],
      choices: 0
    },
    traits: [
      {
        name: "Draconic Ancestry",
        summary: "Choose a dragon type for your breath weapon and damage resistance.",
        description: "You have draconic ancestry. Choose one type of dragon from the Draconic Ancestry table. Your breath weapon and damage resistance are determined by the dragon type, as shown in the table. (Common choices: Red/Gold for fire, Blue/Bronze for lightning, White/Silver for cold)",
        mechanical_effect: "Choose dragon type (determines breath weapon element and resistance)"
      },
      {
        name: "Breath Weapon",
        summary: "Exhale destructive energy matching your draconic ancestry.",
        description: "You can use your action to exhale destructive energy. Your draconic ancestry determines the size, shape, and damage type of the exhalation. When you use your breath weapon, each creature in the area of the exhalation must make a saving throw (DC = 8 + your Constitution modifier + your proficiency bonus). On a failed save, the creature takes 2d6 damage, or half as much damage on a successful one. You can use this feature once per short or long rest.",
        mechanical_effect: "Action: 15 ft. cone or 30 ft. line, 2d6 damage (Dex or Con save DC 8 + CON + Prof), 1/rest"
      },
      {
        name: "Damage Resistance",
        summary: "Resistance to the damage type of your draconic ancestry.",
        description: "You have resistance to the damage type associated with your draconic ancestry.",
        mechanical_effect: "Resistance to 1 damage type (matches breath weapon)"
      }
    ]
  },

  Gnome: {
    name: "Gnome",
    size: "Small",
    speed: 25,
    asi: [
      { ability: "INT", value: 2 }
    ],
    languages: {
      base: ["Common", "Gnomish"],
      choices: 0
    },
    traits: [
      {
        name: "Darkvision",
        summary: "See in darkness up to 60 feet.",
        description: "Accustomed to life underground, you have superior vision in dark and dim conditions. You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray.",
        mechanical_effect: "60 ft. darkvision"
      },
      {
        name: "Gnome Cunning",
        summary: "Advantage on INT, WIS, and CHA saving throws against magic.",
        description: "You have advantage on all Intelligence, Wisdom, and Charisma saving throws against magic.",
        mechanical_effect: "Advantage on INT/WIS/CHA saves vs. magic"
      }
    ],
    subraces: {
      "Forest Gnome": {
        name: "Forest Gnome",
        asi: [
          { ability: "DEX", value: 1 }
        ],
        traits: [
          {
            name: "Natural Illusionist",
            summary: "You know the minor illusion cantrip.",
            description: "You know the minor illusion cantrip. Intelligence is your spellcasting ability for it.",
            mechanical_effect: "Minor Illusion cantrip (INT-based)"
          },
          {
            name: "Speak with Small Beasts",
            summary: "You can communicate simple ideas with Small or smaller beasts.",
            description: "Through sounds and gestures, you can communicate simple ideas with Small or smaller beasts. Forest gnomes love animals and often keep squirrels, badgers, rabbits, moles, woodpeckers, and other creatures as beloved pets.",
            mechanical_effect: "Communicate with Small beasts"
          }
        ]
      },
      "Rock Gnome": {
        name: "Rock Gnome",
        asi: [
          { ability: "CON", value: 1 }
        ],
        traits: [
          {
            name: "Artificer's Lore",
            summary: "Add double proficiency to History checks for magic items, alchemical objects, and technological devices.",
            description: "Whenever you make an Intelligence (History) check related to magic items, alchemical objects, or technological devices, you can add twice your proficiency bonus, instead of any proficiency bonus you normally apply.",
            mechanical_effect: "Expertise: History (magic/tech items only)"
          },
          {
            name: "Tinker",
            summary: "Proficiency with artisan's tools (tinker's tools) and can craft clockwork devices.",
            description: "You have proficiency with artisan's tools (tinker's tools). Using those tools, you can spend 1 hour and 10 gp worth of materials to construct a Tiny clockwork device (AC 5, 1 hp). The device ceases to function after 24 hours (unless you spend 1 hour repairing it to keep the device functioning), or when you use your action to dismantle it.",
            mechanical_effect: "Tinker's tools proficiency, craft clockwork toys"
          }
        ]
      }
    }
  },

  "Half-Elf": {
    name: "Half-Elf",
    size: "Medium",
    speed: 30,
    asi: [
      { ability: "CHA", value: 2 },
      { ability: "CHOICE", value: 1 }, // Player chooses 2 different abilities
      { ability: "CHOICE", value: 1 }
    ],
    languages: {
      base: ["Common", "Elvish"],
      choices: 1
    },
    traits: [
      {
        name: "Darkvision",
        summary: "See in darkness up to 60 feet.",
        description: "Thanks to your elf blood, you have superior vision in dark and dim conditions. You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray.",
        mechanical_effect: "60 ft. darkvision"
      },
      {
        name: "Fey Ancestry",
        summary: "Advantage against being charmed, immune to magical sleep.",
        description: "You have advantage on saving throws against being charmed, and magic can't put you to sleep.",
        mechanical_effect: "Advantage vs. charm, immune to magical sleep"
      },
      {
        name: "Skill Versatility",
        summary: "Proficiency in two skills of your choice.",
        description: "You gain proficiency in two skills of your choice.",
        mechanical_effect: "Proficiency: 2 skills (player's choice)"
      }
    ]
  },

  "Half-Orc": {
    name: "Half-Orc",
    size: "Medium",
    speed: 30,
    asi: [
      { ability: "STR", value: 2 },
      { ability: "CON", value: 1 }
    ],
    languages: {
      base: ["Common", "Orc"],
      choices: 0
    },
    traits: [
      {
        name: "Darkvision",
        summary: "See in darkness up to 60 feet.",
        description: "Thanks to your orc blood, you have superior vision in dark and dim conditions. You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray.",
        mechanical_effect: "60 ft. darkvision"
      },
      {
        name: "Menacing",
        summary: "Proficiency in the Intimidation skill.",
        description: "You gain proficiency in the Intimidation skill.",
        mechanical_effect: "Proficiency: Intimidation"
      },
      {
        name: "Relentless Endurance",
        summary: "Drop to 1 HP instead of 0 once per long rest.",
        description: "When you are reduced to 0 hit points but not killed outright, you can drop to 1 hit point instead. You can't use this feature again until you finish a long rest.",
        mechanical_effect: "1/long rest: survive at 1 HP when reduced to 0"
      },
      {
        name: "Savage Attacks",
        summary: "Add one extra weapon damage die on critical hits with melee weapons.",
        description: "When you score a critical hit with a melee weapon attack, you can roll one of the weapon's damage dice one additional time and add it to the extra damage of the critical hit.",
        mechanical_effect: "Critical hits: roll 1 extra weapon damage die"
      }
    ]
  },

  Tiefling: {
    name: "Tiefling",
    size: "Medium",
    speed: 30,
    asi: [
      { ability: "CHA", value: 2 },
      { ability: "INT", value: 1 }
    ],
    languages: {
      base: ["Common", "Infernal"],
      choices: 0
    },
    traits: [
      {
        name: "Darkvision",
        summary: "See in darkness up to 60 feet.",
        description: "Thanks to your infernal heritage, you have superior vision in dark and dim conditions. You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray.",
        mechanical_effect: "60 ft. darkvision"
      },
      {
        name: "Hellish Resistance",
        summary: "Resistance to fire damage.",
        description: "You have resistance to fire damage.",
        mechanical_effect: "Resistance: fire damage"
      },
      {
        name: "Infernal Legacy",
        summary: "You know thaumaturgy. At 3rd level, cast hellish rebuke once per long rest. At 5th level, cast darkness once per long rest.",
        description: "You know the thaumaturgy cantrip. When you reach 3rd level, you can cast the hellish rebuke spell as a 2nd-level spell once with this trait and regain the ability to do so when you finish a long rest. When you reach 5th level, you can cast the darkness spell once with this trait and regain the ability to do so when you finish a long rest. Charisma is your spellcasting ability for these spells.",
        mechanical_effect: "Thaumaturgy cantrip, Hellish Rebuke 1/day (3rd level), Darkness 1/day (5th level)"
      }
    ]
  }
};

/**
 * Get race data by name
 * @param {string} raceName - Name of the race
 * @returns {object|null} Race data object or null if not found
 */
export function getRaceData(raceName) {
  return raceData[raceName] || null;
}

/**
 * Get all available races
 * @returns {string[]} Array of race names
 */
export function getAvailableRaces() {
  return Object.keys(raceData);
}

/**
 * Check if a race has subraces
 * @param {string} raceName - Name of the race
 * @returns {boolean} True if race has subraces
 */
export function hasSubraces(raceName) {
  const race = getRaceData(raceName);
  return race && race.subraces && Object.keys(race.subraces).length > 0;
}

/**
 * Get available subraces for a race
 * @param {string} raceName - Name of the race
 * @returns {string[]} Array of subrace names, or empty array if none
 */
export function getSubraces(raceName) {
  const race = getRaceData(raceName);
  if (!race || !race.subraces) return [];
  return Object.keys(race.subraces);
}

/**
 * Get subrace data
 * @param {string} raceName - Name of the race
 * @param {string} subraceName - Name of the subrace
 * @returns {object|null} Subrace data or null if not found
 */
export function getSubraceData(raceName, subraceName) {
  const race = getRaceData(raceName);
  if (!race || !race.subraces) return null;
  return race.subraces[subraceName] || null;
}

/**
 * Get combined race and subrace data with all ASI and traits
 * @param {string} raceName - Name of the race
 * @param {string} subraceName - Name of the subrace (optional)
 * @returns {object} Combined race data with subrace bonuses applied
 */
export function getCombinedRaceData(raceName, subraceName = null) {
  const race = getRaceData(raceName);
  if (!race) return null;

  // Start with base race data
  const combined = {
    name: raceName,
    size: race.size,
    speed: race.speed,
    asi: [...race.asi],
    languages: { ...race.languages },
    traits: [...race.traits]
  };

  // Add subrace data if provided
  if (subraceName) {
    const subrace = getSubraceData(raceName, subraceName);
    if (subrace) {
      combined.subrace = subraceName;
      combined.asi = [...combined.asi, ...subrace.asi];
      combined.traits = [...combined.traits, ...subrace.traits];
      
      // Override speed if subrace provides it (e.g., Wood Elf)
      if (subrace.speed) {
        combined.speed = subrace.speed;
      }
    }
  }

  return combined;
}

/**
 * Calculate total ASI for a race (including subrace)
 * @param {string} raceName - Name of the race
 * @param {string} subraceName - Name of the subrace (optional)
 * @returns {object} Object with ability names as keys and bonuses as values
 */
export function calculateRacialASI(raceName, subraceName = null) {
  const combined = getCombinedRaceData(raceName, subraceName);
  if (!combined) return {};

  const asiTotals = {
    STR: 0,
    DEX: 0,
    CON: 0,
    INT: 0,
    WIS: 0,
    CHA: 0
  };

  combined.asi.forEach(bonus => {
    if (bonus.ability === "ALL") {
      // Human gets +1 to all
      Object.keys(asiTotals).forEach(ability => {
        asiTotals[ability] += bonus.value;
      });
    } else if (bonus.ability !== "CHOICE") {
      // Standard ability bonus
      asiTotals[bonus.ability] += bonus.value;
    }
    // CHOICE bonuses need to be handled by character creation UI
  });

  return asiTotals;
}
