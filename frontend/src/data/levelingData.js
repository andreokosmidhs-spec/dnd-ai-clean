/**
 * D&D 5e Leveling and XP Data
 */

// XP thresholds for each level (PHB p.15)
export const XP_THRESHOLDS = {
  1: 0,
  2: 300,
  3: 900,
  4: 2700,
  5: 6500,
  6: 14000,
  7: 23000,
  8: 34000,
  9: 48000,
  10: 64000,
  11: 85000,
  12: 100000,
  13: 120000,
  14: 140000,
  15: 165000,
  16: 195000,
  17: 225000,
  18: 265000,
  19: 305000,
  20: 355000
};

// Hit dice by class
export const HIT_DICE = {
  Barbarian: 12,
  Fighter: 10,
  Paladin: 10,
  Ranger: 10,
  Bard: 8,
  Cleric: 8,
  Druid: 8,
  Monk: 8,
  Rogue: 8,
  Warlock: 8,
  Sorcerer: 6,
  Wizard: 6
};

// Proficiency bonus by level
export const PROFICIENCY_BONUS = {
  1: 2, 2: 2, 3: 2, 4: 2,
  5: 3, 6: 3, 7: 3, 8: 3,
  9: 4, 10: 4, 11: 4, 12: 4,
  13: 5, 14: 5, 15: 5, 16: 5,
  17: 6, 18: 6, 19: 6, 20: 6
};

// ASI (Ability Score Improvement) levels
export const ASI_LEVELS = [4, 8, 12, 16, 19];

// Fighter gets extra ASIs
export const FIGHTER_ASI_LEVELS = [4, 6, 8, 12, 14, 16, 19];

// Rogue gets extra ASIs
export const ROGUE_ASI_LEVELS = [4, 8, 10, 12, 16, 19];

/**
 * Get XP needed for next level
 */
export function getXPForNextLevel(currentLevel) {
  if (currentLevel >= 20) return null; // Max level
  return XP_THRESHOLDS[currentLevel + 1];
}

/**
 * Get current level from XP
 */
export function getLevelFromXP(xp) {
  for (let level = 20; level >= 1; level--) {
    if (xp >= XP_THRESHOLDS[level]) {
      return level;
    }
  }
  return 1;
}

/**
 * Calculate XP progress percentage
 */
export function getXPProgress(currentXP, currentLevel) {
  if (currentLevel >= 20) return 100; // Max level

  const currentThreshold = XP_THRESHOLDS[currentLevel];
  const nextThreshold = XP_THRESHOLDS[currentLevel + 1];
  const xpIntoLevel = currentXP - currentThreshold;
  const xpNeededForLevel = nextThreshold - currentThreshold;

  return Math.min(100, (xpIntoLevel / xpNeededForLevel) * 100);
}

/**
 * Check if character leveled up
 */
export function checkLevelUp(currentXP, currentLevel) {
  const newLevel = getLevelFromXP(currentXP);
  return newLevel > currentLevel;
}

/**
 * Get class features for a given level
 */
export const CLASS_FEATURES = {
  Fighter: {
    1: ["Fighting Style", "Second Wind"],
    2: ["Action Surge (1 use)"],
    3: ["Martial Archetype (choose subclass)"],
    4: ["Ability Score Improvement"],
    5: ["Extra Attack"],
    6: ["Ability Score Improvement"],
    7: ["Martial Archetype feature"],
    8: ["Ability Score Improvement"],
    9: ["Indomitable (1 use)"],
    10: ["Martial Archetype feature"],
    11: ["Extra Attack (2)"],
    12: ["Ability Score Improvement"]
  },
  
  Wizard: {
    1: ["Spellcasting", "Arcane Recovery"],
    2: ["Arcane Tradition (choose subclass)"],
    3: ["2nd-level spells"],
    4: ["Ability Score Improvement"],
    5: ["3rd-level spells"],
    6: ["Arcane Tradition feature"],
    7: ["4th-level spells"],
    8: ["Ability Score Improvement"],
    9: ["5th-level spells"],
    10: ["Arcane Tradition feature"],
    11: ["6th-level spells"],
    12: ["Ability Score Improvement"]
  },

  Rogue: {
    1: ["Expertise (2 skills)", "Sneak Attack (1d6)", "Thieves' Cant"],
    2: ["Cunning Action"],
    3: ["Roguish Archetype (choose subclass)", "Sneak Attack (2d6)"],
    4: ["Ability Score Improvement"],
    5: ["Uncanny Dodge", "Sneak Attack (3d6)"],
    6: ["Expertise (2 more skills)"],
    7: ["Evasion", "Sneak Attack (4d6)"],
    8: ["Ability Score Improvement"],
    9: ["Roguish Archetype feature", "Sneak Attack (5d6)"],
    10: ["Ability Score Improvement"],
    11: ["Reliable Talent", "Sneak Attack (6d6)"],
    12: ["Ability Score Improvement"]
  },

  Cleric: {
    1: ["Spellcasting", "Divine Domain (choose subclass)"],
    2: ["Channel Divinity (1 use)", "Divine Domain feature"],
    3: ["2nd-level spells"],
    4: ["Ability Score Improvement"],
    5: ["Destroy Undead (CR 1/2)", "3rd-level spells"],
    6: ["Channel Divinity (2 uses)", "Divine Domain feature"],
    7: ["4th-level spells"],
    8: ["Ability Score Improvement", "Destroy Undead (CR 1)", "Divine Domain feature"],
    9: ["5th-level spells"],
    10: ["Divine Intervention"],
    11: ["Destroy Undead (CR 2)", "6th-level spells"],
    12: ["Ability Score Improvement"]
  }
};

/**
 * Get features gained at a specific level
 */
export function getFeaturesForLevel(characterClass, level) {
  return CLASS_FEATURES[characterClass]?.[level] || [];
}

/**
 * Check if level grants ASI
 */
export function grantsASI(characterClass, level) {
  if (characterClass === "Fighter") {
    return FIGHTER_ASI_LEVELS.includes(level);
  }
  if (characterClass === "Rogue") {
    return ROGUE_ASI_LEVELS.includes(level);
  }
  return ASI_LEVELS.includes(level);
}

/**
 * Calculate average HP gain for class
 */
export function getAverageHPGain(characterClass) {
  const hitDie = HIT_DICE[characterClass];
  return Math.floor(hitDie / 2) + 1;
}
