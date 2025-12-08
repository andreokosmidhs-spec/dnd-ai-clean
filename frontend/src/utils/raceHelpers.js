/**
 * Helper functions for applying racial mechanics to characters
 */

import { getRaceData, hasSubraces, getSubraces } from '../data/raceData';

// Export subrace helpers
export { hasSubraces, getSubraces } from '../data/raceData';

/**
 * Apply racial mechanics to a character
 * Handles ASI, size, speed, languages, and traits (including subraces)
 * @param {string} raceName - Name of the race to apply
 * @param {object} character - Current character object
 * @param {string} subraceName - Name of the subrace (optional)
 * @returns {object} Updated character with racial mechanics applied
 */
export function applyRaceToCharacter(raceName, character, subraceName = null) {
  const race = getRaceData(raceName);
  
  if (!race) {
    console.warn(`Race "${raceName}" not found in race data`);
    return character;
  }

  // Start with the current character
  let updated = { ...character };

  // 1. Remove previous racial bonuses if race is changing
  if (updated.race && (updated.race !== raceName || updated.subrace !== subraceName)) {
    updated = removeRacialBonuses(updated);
  }

  // 2. Update basic race info
  updated.race = raceName;
  updated.subrace = subraceName || null;
  updated.size = race.size;
  updated.speed = race.speed;

  // 3. Combine race and subrace data
  let allASI = [...race.asi];
  let allTraits = [...race.traits];

  // If subrace is selected, add subrace bonuses
  if (subraceName && race.subraces && race.subraces[subraceName]) {
    const subrace = race.subraces[subraceName];
    allASI = [...allASI, ...subrace.asi];
    allTraits = [...allTraits, ...subrace.traits];
    
    // Override speed if subrace provides it (e.g., Wood Elf has 35 ft)
    if (subrace.speed) {
      updated.speed = subrace.speed;
    }
  }

  // 4. Apply racial ASI (includes subrace ASI)
  updated = applyRacialASI(updated, allASI);

  // 5. Apply racial languages
  updated = applyRacialLanguages(updated, race.languages);

  // 6. Apply racial traits (includes subrace traits)
  updated.racial_traits = allTraits;

  return updated;
}

/**
 * Remove previous racial bonuses from character
 * @param {object} character - Character object
 * @returns {object} Character with racial bonuses removed
 */
function removeRacialBonuses(character) {
  let updated = { ...character };

  // Remove racial ASI
  if (updated.racial_asi && updated.stats) {
    updated.stats = { ...updated.stats };
    
    // Remove the bonuses from stats
    Object.keys(updated.racial_asi).forEach(stat => {
      if (updated.stats[stat] !== undefined && updated.racial_asi[stat] > 0) {
        updated.stats[stat] = updated.stats[stat] - updated.racial_asi[stat];
      }
    });
  }
  
  // Old format compatibility
  if (updated.racial_asi_array) {
    for (const bonus of updated.racial_asi_array) {
      if (bonus.ability === "ALL") {
        // Remove +1 from all abilities
        Object.keys(updated.stats).forEach(stat => {
          updated.stats[stat] = Math.max(1, updated.stats[stat] - bonus.value);
        });
      } else {
        // Remove bonus from specific ability
        const statKey = bonus.ability.toLowerCase();
        if (updated.stats[statKey] !== undefined) {
          updated.stats[statKey] = Math.max(1, updated.stats[statKey] - bonus.value);
        }
      }
    }
    
    delete updated.racial_asi;
  }

  // Remove racial languages
  if (updated.racial_languages_base) {
    updated.languages = (updated.languages || []).filter(
      lang => !updated.racial_languages_base.includes(lang)
    );
    delete updated.racial_languages_base;
  }

  // Reset racial language choices
  delete updated.racial_language_choices;

  // Remove racial traits
  delete updated.racial_traits;

  return updated;
}

/**
 * Apply racial ASI to character stats
 * @param {object} character - Character object
 * @param {array} asiArray - Array of ASI objects from race data
 * @returns {object} Character with racial ASI applied
 */
function applyRacialASI(character, asiArray) {
  let updated = { ...character };
  updated.stats = { ...updated.stats };
  updated.racial_asi_array = asiArray; // Store the raw array for reference
  
  // Calculate racial bonuses as a flat object for easy display
  const racialBonuses = {
    strength: 0,
    dexterity: 0,
    constitution: 0,
    intelligence: 0,
    wisdom: 0,
    charisma: 0
  };

  // Map 3-letter codes to full ability names
  const abilityMap = {
    'STR': 'strength',
    'DEX': 'dexterity',
    'CON': 'constitution',
    'INT': 'intelligence',
    'WIS': 'wisdom',
    'CHA': 'charisma'
  };

  for (const bonus of asiArray) {
    if (bonus.ability === "ALL") {
      // Apply +1 to all abilities (Human)
      Object.keys(racialBonuses).forEach(stat => {
        racialBonuses[stat] += bonus.value;
      });
    } else if (bonus.ability !== "CHOICE") {
      // Apply bonus to specific ability
      // Map from 3-letter code (DEX) to full name (dexterity)
      const statKey = abilityMap[bonus.ability] || bonus.ability.toLowerCase();
      if (racialBonuses[statKey] !== undefined) {
        racialBonuses[statKey] += bonus.value;
      }
    }
    // CHOICE bonuses need to be handled by UI (Half-Elf)
  }

  // Store the calculated bonuses for display
  updated.racial_asi = racialBonuses;

  // Apply the bonuses to stats (if stats exist)
  if (updated.stats && Object.keys(updated.stats).length > 0) {
    Object.keys(racialBonuses).forEach(stat => {
      if (updated.stats[stat] !== undefined && racialBonuses[stat] > 0) {
        updated.stats[stat] = (updated.stats[stat] || 10) + racialBonuses[stat];
      }
    });
  }

  return updated;
}

/**
 * Apply racial languages to character
 * @param {object} character - Character object
 * @param {object} languages - Languages object from race data
 * @returns {object} Character with racial languages applied
 */
function applyRacialLanguages(character, languages) {
  let updated = { ...character };

  // Store base racial languages separately
  updated.racial_languages_base = languages.base;
  updated.racial_language_choices = languages.choices;

  // Ensure automatic racial languages are not in the choices list
  if (updated.languages && Array.isArray(updated.languages)) {
    updated.languages = updated.languages.filter(
      lang => !languages.base.includes(lang)
    );
  }

  return updated;
}

/**
 * Calculate ability score modifier
 * @param {number} score - Ability score
 * @returns {number} Modifier
 */
export function getAbilityModifier(score) {
  return Math.floor((score - 10) / 2);
}

/**
 * Get formatted modifier string (+2, -1, etc.)
 * @param {number} score - Ability score
 * @returns {string} Formatted modifier
 */
export function getModifierString(score) {
  const mod = getAbilityModifier(score);
  return mod >= 0 ? `+${mod}` : `${mod}`;
}

/**
 * Calculate base stats (stats without racial bonuses)
 * @param {object} stats - Current stats with racial bonuses
 * @param {array} racial_asi - Racial ASI array
 * @returns {object} Base stats
 */
export function calculateBaseStats(stats, racial_asi) {
  if (!racial_asi || racial_asi.length === 0) {
    return { ...stats };
  }

  const baseStats = { ...stats };

  for (const bonus of racial_asi) {
    if (bonus.ability === "ALL") {
      // Subtract bonus from all abilities
      Object.keys(baseStats).forEach(stat => {
        baseStats[stat] = Math.max(1, baseStats[stat] - bonus.value);
      });
    } else {
      // Subtract bonus from specific ability
      const statKey = bonus.ability.toLowerCase();
      if (baseStats[statKey] !== undefined) {
        baseStats[statKey] = Math.max(1, baseStats[statKey] - bonus.value);
      }
    }
  }

  return baseStats;
}

/**
 * Get total languages for character (automatic + chosen)
 * @param {object} character - Character object with language calculation
 * @returns {string[]} Array of all languages
 */
export function getTotalLanguages(character) {
  const automatic = character._languageCalculation?.automatic || [];
  const chosen = character.languages || [];
  
  return [...new Set([...automatic, ...chosen])]; // Remove duplicates
}
