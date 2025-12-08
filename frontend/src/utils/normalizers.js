/**
 * Frontend normalizers - ensure data has guaranteed shape.
 * Accept partial data at boundaries, normalize once, treat as stable everywhere.
 */

/**
 * Normalize character state from API/DB
 * @param {Object} raw - Raw character data
 * @returns {Object} Normalized character with guaranteed HP shape
 */
export function normalizeCharacter(raw) {
  if (!raw) {
    return null;
  }

  // Handle HP normalization
  const hp = raw.hp || {};
  const normalizedHP = {
    current: hp.current ?? raw.current_hp ?? 10,
    max: hp.max ?? raw.max_hp ?? 10,
    temp: hp.temp ?? 0,
  };

  return {
    id: raw.id || 'unknown',
    name: raw.name || 'Unknown',
    race: raw.race || 'Human',
    class: raw.class || 'Fighter',
    level: raw.level || 1,
    hp: normalizedHP,
    ac: raw.ac || 10,
    proficiency_bonus: raw.proficiency_bonus || 2,
    attack_bonus: raw.attack_bonus || 0,
    abilities: raw.abilities || {
      str: 10,
      dex: 10,
      con: 10,
      int: 10,
      wis: 10,
      cha: 10,
    },
    stats: raw.stats || raw.abilities || {},
    current_xp: raw.current_xp || 0,
    xp_to_next: raw.xp_to_next || 300,
    proficiencies: raw.proficiencies || [],
    conditions: raw.conditions || [],
    inventory: raw.inventory || [],
    spell_slots: raw.spell_slots || null,
    // Preserve other fields
    ...raw,
    // But override with normalized values
    hp: normalizedHP,
    conditions: raw.conditions || [],
    inventory: raw.inventory || [],
  };
}

/**
 * Normalize enemy data for combat
 * @param {Object} raw - Raw enemy data
 * @returns {Object} Normalized enemy with guaranteed combat stats
 */
export function normalizeEnemy(raw) {
  if (!raw) {
    return null;
  }

  return {
    id: raw.id || `enemy-${raw.name || 'unknown'}`,
    name: raw.name || 'Unknown Enemy',
    hp: raw.hp ?? 10,
    max_hp: raw.max_hp ?? 10,
    ac: raw.ac ?? 10,
    attack_bonus: raw.attack_bonus ?? 2,
    damage_die: raw.damage_die || '1d6',
    type: raw.type || null,
    abilities: raw.abilities || null,
    special_abilities: raw.special_abilities || [],
    // Preserve other fields
    ...raw,
  };
}

/**
 * Normalize message for adventure log
 * @param {Object} raw - Raw message data
 * @returns {Object} Normalized message
 */
export function normalizeMessage(raw) {
  if (!raw) {
    return null;
  }

  return {
    id: raw.id || `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    type: raw.type || 'dm',
    text: raw.text || '',
    timestamp: raw.timestamp || Date.now(),
    options: raw.options || [],
    checkRequest: raw.checkRequest || null,
    npcMentions: raw.npcMentions || [],
    isCinematic: raw.isCinematic || false,
    audioUrl: raw.audioUrl || null,
    isGeneratingAudio: raw.isGeneratingAudio || false,
    messageType: raw.messageType || null,
    rollData: raw.rollData || null,
    retry: raw.retry || false,
  };
}

/**
 * Normalize world state
 * @param {Object} raw - Raw world state
 * @returns {Object} Normalized world state
 */
export function normalizeWorldState(raw) {
  if (!raw) {
    return null;
  }

  return {
    current_location: raw.current_location || raw.location || 'Unknown',
    time_of_day: raw.time_of_day || 'day',
    weather: raw.weather || 'clear',
    party_status: raw.party_status || 'exploring',
    quests: raw.quests || [],
    npcs: raw.npcs || [],
    // Preserve other fields
    ...raw,
  };
}

/**
 * Normalize combat state
 * @param {Object} raw - Raw combat state
 * @returns {Object} Normalized combat state with normalized enemies
 */
export function normalizeCombatState(raw) {
  if (!raw) {
    return null;
  }

  return {
    isActive: raw.isActive || raw.active || false,
    combatId: raw.combatId || raw.combat_id || null,
    participants: (raw.participants || []).map(normalizeEnemy),
    enemies: (raw.enemies || []).map(normalizeEnemy),
    turnOrder: raw.turnOrder || raw.turn_order || [],
    currentTurnIndex: raw.currentTurnIndex ?? raw.current_turn_index ?? 0,
    roundNumber: raw.roundNumber ?? raw.round_number ?? 0,
    outcome: raw.outcome || null,
    // Preserve other fields
    ...raw,
  };
}

/**
 * Type definitions for reference (JSDoc style for JS projects)
 */

/**
 * @typedef {Object} NormalizedCharacter
 * @property {string} id
 * @property {string} name
 * @property {string} race
 * @property {string} class
 * @property {number} level
 * @property {Object} hp - ALWAYS present
 * @property {number} hp.current
 * @property {number} hp.max
 * @property {number} hp.temp
 * @property {number} ac
 * @property {number} proficiency_bonus
 * @property {number} attack_bonus
 * @property {Object} abilities
 * @property {number} current_xp
 * @property {number} xp_to_next
 * @property {string[]} proficiencies
 */

/**
 * @typedef {Object} NormalizedEnemy
 * @property {string} id
 * @property {string} name
 * @property {number} hp
 * @property {number} max_hp
 * @property {number} ac
 * @property {number} attack_bonus - ALWAYS present
 * @property {string} damage_die - ALWAYS present
 * @property {string|null} type
 * @property {Object|null} abilities
 * @property {string[]} special_abilities
 */

/**
 * @typedef {Object} NormalizedMessage
 * @property {string} id
 * @property {string} type - 'dm' | 'player' | 'roll_result' | 'error'
 * @property {string} text
 * @property {number} timestamp
 * @property {string[]} options
 * @property {Object|null} checkRequest
 * @property {Object[]} npcMentions
 * @property {boolean} isCinematic
 * @property {string|null} audioUrl
 * @property {boolean} isGeneratingAudio
 * @property {string|null} messageType
 * @property {Object|null} rollData
 * @property {boolean} retry
 */
