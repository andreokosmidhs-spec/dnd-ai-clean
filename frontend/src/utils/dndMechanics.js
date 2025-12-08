/**
 * D&D 5e Mechanics Utilities
 */

// Get ability modifier from ability score or stats object
export const getAbilityModifier = (statsOrScore, abilityKey = null) => {
  if (typeof statsOrScore === 'number') {
    return Math.floor((statsOrScore - 10) / 2);
  }
  
  if (typeof statsOrScore === 'object' && abilityKey) {
    const abilityScore = statsOrScore[abilityKey] || statsOrScore[abilityKey.toLowerCase()] || 10;
    return Math.floor((abilityScore - 10) / 2);
  }
  
  return 0;
};

// Get proficiency bonus from character level
export const getProficiencyBonus = (level) => {
  if (level >= 17) return 6;
  if (level >= 13) return 5;
  if (level >= 9) return 4;
  if (level >= 5) return 3;
  return 2;
};

// Skill to ability mapping
export const SKILL_ABILITIES = {
  'Acrobatics': 'dex',
  'Animal Handling': 'wis',
  'Arcana': 'int',
  'Athletics': 'str',
  'Deception': 'cha',
  'History': 'int',
  'Insight': 'wis',
  'Intimidation': 'cha',
  'Investigation': 'int',
  'Medicine': 'wis',
  'Nature': 'int',
  'Perception': 'wis',
  'Performance': 'cha',
  'Persuasion': 'cha',
  'Religion': 'int',
  'Sleight of Hand': 'dex',
  'Stealth': 'dex',
  'Survival': 'wis'
};

// Get the ability key (lowercase) from skill name
export const getSkillAbility = (skillName) => {
  return SKILL_ABILITIES[skillName] || null;
};

// Check if character is proficient in a skill
export const isProficient = (proficiencies, skillName) => {
  if (!proficiencies || !Array.isArray(proficiencies)) return false;
  
  const normalizedSkill = skillName.toLowerCase().replace(/\s+/g, '_');
  return proficiencies.some(prof => 
    prof.toLowerCase().replace(/\s+/g, '_') === normalizedSkill ||
    prof.toLowerCase() === skillName.toLowerCase()
  );
};

// Compute total modifier for a check
export const getCheckModifier = (checkRequest, characterState) => {
  console.log('🎲 getCheckModifier called with:', {
    checkRequest,
    characterState,
    hasStats: !!characterState?.stats,
    stats: characterState?.stats,
    level: characterState?.level
  });
  
  // Validate inputs
  if (!checkRequest || !characterState) {
    console.error('❌ getCheckModifier: Missing required parameters', { checkRequest, characterState });
    return 0;
  }
  
  const { kind, ability, skill } = checkRequest;
  const situationalBonus = checkRequest.situational_bonus || 0;
  
  // Validate characterState structure
  if (!characterState.stats || typeof characterState.stats !== 'object') {
    console.error('❌ getCheckModifier: characterState.stats is missing or invalid', {
      characterState,
      statsType: typeof characterState.stats,
      statsValue: characterState.stats,
      allKeys: Object.keys(characterState || {})
    });
    return 0;
  }
  
  if (!characterState.level || typeof characterState.level !== 'number') {
    console.error('❌ getCheckModifier: characterState.level is missing or invalid', characterState);
    return 0;
  }
  
  // Get ability score - handle both short (str, dex) and long (strength, dexterity) formats
  const abilityKey = ability ? ability.toLowerCase() : 'str';
  
  // Map short names to full names
  const abilityNameMap = {
    'str': 'strength',
    'dex': 'dexterity',
    'con': 'constitution',
    'int': 'intelligence',
    'wis': 'wisdom',
    'cha': 'charisma'
  };
  
  // Try short name first, then full name, then default to 10
  const abilityScore = characterState.stats[abilityKey] || 
                       characterState.stats[abilityNameMap[abilityKey]] || 
                       10;
  const abilityMod = getAbilityModifier(abilityScore);
  
  console.log('🎲 Modifier Calculation Details:', {
    ability,
    abilityKey,
    fullAbilityName: abilityNameMap[abilityKey],
    statsObject: characterState.stats,
    abilityScore,
    abilityMod,
    skill,
    proficiencies: characterState.proficiencies
  });
  
  // Get proficiency bonus
  const profBonus = getProficiencyBonus(characterState.level);
  
  let totalMod = abilityMod;
  
  // Add proficiency if applicable
  if (kind === 'skill' && skill) {
    // Check if proficient in this skill (from class or racial traits)
    const proficiencies = characterState.proficiencies || [];
    
    // Check racial traits for skill proficiencies (e.g., Keen Senses → Perception)
    const racialTraits = characterState.racial_traits || [];
    const hasRacialProficiency = racialTraits.some(trait => {
      const mechEffect = trait.mechanical_effect || '';
      return mechEffect.toLowerCase().includes('proficiency') && 
             mechEffect.toLowerCase().includes(skill.toLowerCase());
    });
    
    const isProficient = proficiencies.some(p => 
      p.toLowerCase().includes(skill.toLowerCase())
    ) || hasRacialProficiency;
    
    if (isProficient) {
      totalMod += profBonus;
      
      // Check for expertise (double proficiency)
      const expertise = characterState.expertise || [];
      const hasExpertise = expertise.some(e => 
        e.toLowerCase().includes(skill.toLowerCase())
      );
      
      if (hasExpertise) {
        totalMod += profBonus; // Add proficiency again for expertise
      }
    }
  } else if (kind === 'save') {
    // Saving throw proficiency
    const saveProficiencies = characterState.saving_throw_proficiencies || [];
    if (saveProficiencies.includes(ability)) {
      totalMod += profBonus;
    }
  }
  
  // Add situational bonus
  totalMod += situationalBonus;
  
  console.log('🎲 Final Modifier Calculation:', {
    abilityMod,
    profBonus,
    isProficient: kind === 'skill' && skill ? characterState.proficiencies?.some(p => p.toLowerCase().includes(skill.toLowerCase())) : false,
    situationalBonus,
    totalMod
  });
  
  return totalMod;
};

// Build dice formula based on check mode and modifier
export const buildDiceFormula = (mode, modifier) => {
  const modStr = modifier >= 0 ? `+${modifier}` : `${modifier}`;
  
  switch (mode) {
    case 'advantage':
      return `2d20kh1${modStr}`;
    case 'disadvantage':
      return `2d20kl1${modStr}`;
    default:
      return `1d20${modStr}`;
  }
};

// Determine check outcome
export const getCheckOutcome = (total, dc) => {
  if (total >= dc + 5) return 'critical_success';
  if (total >= dc) return 'success';
  if (total >= dc - 5) return 'partial';
  return 'fail';
};

// Format modifier with sign
export const formatModifier = (mod) => {
  return mod >= 0 ? `+${mod}` : `${mod}`;
};

// Parse advantage/disadvantage reasons
export const inferAdvantageReasons = (characterState, worldState, checkRequest) => {
  const reasons = [];
  
  // Check conditions
  if (characterState.conditions) {
    if (characterState.conditions.includes('poisoned')) {
      reasons.push({ type: 'disadvantage', reason: 'Poisoned condition' });
    }
    if (characterState.conditions.includes('exhausted')) {
      reasons.push({ type: 'disadvantage', reason: 'Exhaustion' });
    }
  }
  
  // Check environment
  if (worldState) {
    const isNight = worldState.time_of_day?.includes('night');
    const hasLight = characterState.inventory?.some(item => 
      item.equipped && item.tags?.includes('light')
    );
    
    if (checkRequest.skill === 'Perception' && isNight && !hasLight) {
      reasons.push({ type: 'disadvantage', reason: 'Darkness without light' });
    }
    
    if (checkRequest.skill === 'Stealth' && worldState.weather?.includes('rain')) {
      reasons.push({ type: 'advantage', reason: 'Rain covers sounds' });
    }
  }
  
  // Class/background advantages
  const isRanger = characterState.class?.toLowerCase().includes('ranger');
  const isAcolyte = characterState.background?.toLowerCase().includes('acolyte');
  
  if (isRanger && checkRequest.skill === 'Survival') {
    reasons.push({ type: 'advantage', reason: 'Ranger in natural terrain' });
  }
  
  if (isAcolyte && checkRequest.skill === 'Religion') {
    reasons.push({ type: 'advantage', reason: 'Acolyte background' });
  }
  
  // Equipment
  const hasHeavyArmor = characterState.inventory?.some(item => 
    item.equipped && item.tags?.includes('armor') && item.tags?.includes('heavy')
  );
  
  if (hasHeavyArmor && checkRequest.skill === 'Stealth') {
    reasons.push({ type: 'disadvantage', reason: 'Heavy armor' });
  }
  
  return reasons;
};
