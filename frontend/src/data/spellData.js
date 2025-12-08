/**
 * D&D 5e Cantrip and Spell Data
 * Organized by spell level and class
 */

export const CANTRIPS = {
  // Wizard Cantrips (for High Elf racial choice)
  wizard: [
    {
      name: "Fire Bolt",
      description: "Hurl a mote of fire at a creature or object. Ranged spell attack, 1d10 fire damage.",
      castingTime: "1 action",
      range: "120 feet",
      damage: "1d10 fire"
    },
    {
      name: "Ray of Frost",
      description: "Ray of blue-white frost. Ranged spell attack, 1d8 cold damage, speed reduced by 10 ft.",
      castingTime: "1 action",
      range: "60 feet",
      damage: "1d8 cold"
    },
    {
      name: "Mage Hand",
      description: "Create a spectral floating hand that can manipulate objects, open doors, retrieve items.",
      castingTime: "1 action",
      range: "30 feet",
      damage: "None (utility)"
    },
    {
      name: "Minor Illusion",
      description: "Create a sound or image of an object. Great for distractions and deception.",
      castingTime: "1 action",
      range: "30 feet",
      damage: "None (utility)"
    },
    {
      name: "Prestidigitation",
      description: "Minor magical trick: light candles, clean items, chill/warm/flavor food, create trinkets.",
      castingTime: "1 action",
      range: "10 feet",
      damage: "None (utility)"
    },
    {
      name: "Light",
      description: "Touch an object to make it shed bright light in 20-ft radius, dim light for 20 ft more.",
      castingTime: "1 action",
      range: "Touch",
      damage: "None (utility)"
    },
    {
      name: "Shocking Grasp",
      description: "Lightning springs from your hand. Melee spell attack, 1d8 lightning, target can't take reactions.",
      castingTime: "1 action",
      range: "Touch",
      damage: "1d8 lightning"
    },
    {
      name: "Poison Spray",
      description: "Noxious gas cloud. Target must make CON save or take 1d12 poison damage.",
      castingTime: "1 action",
      range: "10 feet",
      damage: "1d12 poison"
    }
  ],

  // Racial automatic cantrips
  racial: {
    thaumaturgy: {
      name: "Thaumaturgy",
      description: "Manifest minor wonder: voice booms, flames flicker, ground trembles. Used for intimidation.",
      castingTime: "1 action",
      range: "30 feet",
      damage: "None (utility)",
      source: "Tiefling"
    },
    dancing_lights: {
      name: "Dancing Lights",
      description: "Create up to four torch-sized lights that hover and move. Great for exploration.",
      castingTime: "1 action",
      range: "120 feet",
      damage: "None (utility)",
      source: "Drow"
    },
    minor_illusion: {
      name: "Minor Illusion",
      description: "Create a sound or image of an object. Great for distractions and deception.",
      castingTime: "1 action",
      range: "30 feet",
      damage: "None (utility)",
      source: "Forest Gnome"
    }
  }
};

export const RACIAL_SPELLS = {
  // Tiefling Infernal Legacy
  tiefling: [
    {
      name: "Hellish Rebuke",
      level: 1,
      description: "Reaction: When damaged, surround attacker with hellfire. 2d10 fire damage (DEX save for half).",
      castingTime: "Reaction",
      range: "60 feet",
      damage: "2d10 fire",
      unlockLevel: 3
    },
    {
      name: "Darkness",
      level: 2,
      description: "Create magical darkness in 15-ft radius. Even darkvision can't penetrate it.",
      castingTime: "1 action",
      range: "60 feet",
      damage: "None (utility)",
      unlockLevel: 5
    }
  ],

  // Drow Magic
  drow: [
    {
      name: "Faerie Fire",
      level: 1,
      description: "Outline creatures in light. Attacks against them have advantage.",
      castingTime: "1 action",
      range: "60 feet",
      damage: "None (utility)",
      unlockLevel: 3
    },
    {
      name: "Darkness",
      level: 2,
      description: "Create magical darkness in 15-ft radius. Even darkvision can't penetrate it.",
      castingTime: "1 action",
      range: "60 feet",
      damage: "None (utility)",
      unlockLevel: 5
    }
  ]
};

/**
 * Get cantrips available for character creation
 */
export function getAvailableCantrips(race, subrace, characterClass) {
  const cantrips = [];

  // High Elf gets 1 wizard cantrip choice
  if (race === "Elf" && subrace === "High Elf") {
    return {
      type: "choice",
      count: 1,
      list: CANTRIPS.wizard,
      source: "High Elf racial trait"
    };
  }

  // Forest Gnome gets Minor Illusion automatically
  if (race === "Gnome" && subrace === "Forest Gnome") {
    return {
      type: "automatic",
      list: [CANTRIPS.racial.minor_illusion],
      source: "Forest Gnome racial trait"
    };
  }

  // Tiefling gets Thaumaturgy automatically
  if (race === "Tiefling") {
    return {
      type: "automatic",
      list: [CANTRIPS.racial.thaumaturgy],
      source: "Tiefling Infernal Legacy"
    };
  }

  // Drow gets Dancing Lights automatically
  if (race === "Elf" && subrace === "Dark Elf (Drow)") {
    return {
      type: "automatic",
      list: [CANTRIPS.racial.dancing_lights],
      source: "Drow Magic"
    };
  }

  // TODO: Add class-based cantrips (Wizard, Sorcerer, Warlock, etc.)

  return null;
}

/**
 * Get racial spells that unlock at higher levels
 */
export function getRacialSpells(race, subrace) {
  if (race === "Tiefling") {
    return RACIAL_SPELLS.tiefling;
  }

  if (race === "Elf" && subrace === "Dark Elf (Drow)") {
    return RACIAL_SPELLS.drow;
  }

  return [];
}
