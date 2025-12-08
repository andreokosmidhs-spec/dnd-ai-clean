/**
 * XP Calculation Utilities
 * Calculate XP thresholds for leveling up
 */

/**
 * Calculate total XP required to reach a specific level
 * Based on simplified D&D 5e progression
 * 
 * @param {number} level - Target level
 * @returns {number} Total XP required
 */
export const calculateXpForLevel = (level) => {
  if (level <= 1) return 0;
  
  // Simplified XP progression (similar to D&D 5e but scaled)
  const xpTable = {
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
  
  // For levels beyond 20, use exponential growth
  if (level > 20) {
    return xpTable[20] + (level - 20) * 60000;
  }
  
  return xpTable[level] || 0;
};

/**
 * Calculate XP needed for next level from current level
 * 
 * @param {number} currentLevel - Current character level
 * @returns {number} XP required for next level
 */
export const calculateXpForNextLevel = (currentLevel) => {
  const currentLevelXp = calculateXpForLevel(currentLevel);
  const nextLevelXp = calculateXpForLevel(currentLevel + 1);
  return nextLevelXp - currentLevelXp;
};

/**
 * Calculate current level based on total XP
 * 
 * @param {number} totalXp - Total accumulated XP
 * @returns {number} Current level
 */
export const calculateLevelFromXp = (totalXp) => {
  let level = 1;
  
  while (calculateXpForLevel(level + 1) <= totalXp && level < 20) {
    level++;
  }
  
  return level;
};

/**
 * Get XP progress within current level
 * 
 * @param {number} totalXp - Total accumulated XP
 * @param {number} currentLevel - Current level
 * @returns {Object} { currentXp, xpForNextLevel }
 */
export const getXpProgress = (totalXp, currentLevel) => {
  const currentLevelXp = calculateXpForLevel(currentLevel);
  const nextLevelXp = calculateXpForLevel(currentLevel + 1);
  
  return {
    currentXp: totalXp - currentLevelXp,
    xpForNextLevel: nextLevelXp - currentLevelXp
  };
};

/**
 * Format XP number with commas
 * 
 * @param {number} xp - XP value
 * @returns {string} Formatted XP string
 */
export const formatXp = (xp) => {
  return xp.toLocaleString();
};
