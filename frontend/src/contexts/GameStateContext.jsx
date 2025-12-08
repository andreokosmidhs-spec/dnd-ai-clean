import React, { createContext, useContext, useState, useEffect } from 'react';

const GameStateContext = createContext();

export const useGameState = () => {
  const context = useContext(GameStateContext);
  if (!context) {
    throw new Error('useGameState must be used within GameStateProvider');
  }
  return context;
};

export const GameStateProvider = ({ children }) => {
  const [sessionId, setSessionId] = useState('');
  const [campaignId, setCampaignId] = useState(''); // NEW: DUNGEON FORGE campaign ID
  const [worldBlueprint, setWorldBlueprint] = useState(null); // NEW: World blueprint for UI
  const [lastSentState, setLastSentState] = useState(null);
  
  const [characterState, setCharacterState] = useState({
    id: null,
    name: 'Unnamed Character',
    race: 'Unknown',
    class: 'Unknown',
    level: 1,
    background: 'Unknown',
    alignment: 'Neutral',
    stats: {
      str: 10,
      dex: 10,
      con: 10,
      int: 10,
      wis: 10,
      cha: 10
    },
    proficiency_bonus: 2,
    hp: { current: 10, max: 10, temp: 0 },
    ac: 10,
    speed: 30,
    spell_slots: {},
    prepared_spells: [],
    conditions: [],
    virtues: [],
    flaws: [],
    goals: [],
    proficiencies: [],
    inventory: [],
    gold: 0,
    active_quests: [],
    reputation: {},
    notes: 'Character not yet created',
    // P3: Progression fields
    current_xp: 0,
    xp_to_next: 100,
    attack_bonus: 0,
    injury_count: 0
  });

  const [worldState, setWorldState] = useState({
    region: 'Ravenswood',
    settlement: 'Ravens Hollow',
    location: 'Town Square',
    time_of_day: 'late afternoon',
    weather: 'overcast, distant rain approaching',
    current_location: 'Town Square', // NEW: for DUNGEON FORGE
    active_npcs: [], // NEW: for DUNGEON FORGE
    faction_states: {}, // NEW: for DUNGEON FORGE
    quest_flags: {}, // NEW: for DUNGEON FORGE
    recent_events: [
      'Arrived in town square',
      'Noticed wary glances from townsfolk'
    ]
  });

  const [sessionNotes, setSessionNotes] = useState([]);
  const [threatLevel, setThreatLevel] = useState(2); // 0=cozy, 5=dire
  const [isDirty, setIsDirty] = useState(false);

  // DM-ENGINE v1 State
  const [dmEngineState, setDmEngineState] = useState({
    world: { pantheon: [], regions: [], factions: [] },
    npc_templates: [],
    encounters: [],
    rulebook: { 
      dice: "d20", 
      proficiency_bonus: "2 + floor(level/5)", 
      rule_of_cool: 0.2 
    },
    runtime: {
      emotion_levels: { Joy: 0, Love: 0, Anger: 0, Sadness: 0, Fear: 0, Peace: 0 },
      roc_events: [],
      faction_clocks: {},
      chosen_emotion: null,
      chosen_ideal: null,
      activeEncounter: null
    }
  });

  // Load state from localStorage on mount
  useEffect(() => {
    const savedSessionId = localStorage.getItem('game-state-session-id');
    const savedCampaignId = localStorage.getItem('game-state-campaign-id'); // NEW
    
    if (savedSessionId) {
      setSessionId(savedSessionId);
      
      const savedCharacter = localStorage.getItem(`game-state-character-${savedSessionId}`);
      const savedWorld = localStorage.getItem(`game-state-world-${savedSessionId}`);
      const savedNotes = localStorage.getItem(`game-state-notes-${savedSessionId}`);
      const savedThreat = localStorage.getItem(`game-state-threat-${savedSessionId}`);
      const savedDmEngine = localStorage.getItem(`game-state-dmengine-${savedSessionId}`);
      
      if (savedCharacter) setCharacterState(JSON.parse(savedCharacter));
      if (savedWorld) setWorldState(JSON.parse(savedWorld));
      if (savedNotes) setSessionNotes(JSON.parse(savedNotes));
      if (savedThreat) setThreatLevel(parseInt(savedThreat));
      if (savedDmEngine) setDmEngineState(JSON.parse(savedDmEngine));
    }
    
    if (savedCampaignId) {
      setCampaignId(savedCampaignId);
    }
  }, []);

  // Save state to localStorage when it changes
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem('game-state-session-id', sessionId);
      localStorage.setItem(`game-state-character-${sessionId}`, JSON.stringify(characterState));
      localStorage.setItem(`game-state-world-${sessionId}`, JSON.stringify(worldState));
      localStorage.setItem(`game-state-notes-${sessionId}`, JSON.stringify(sessionNotes));
      localStorage.setItem(`game-state-threat-${sessionId}`, threatLevel.toString());
      localStorage.setItem(`game-state-dmengine-${sessionId}`, JSON.stringify(dmEngineState));
    }
    if (campaignId) {
      localStorage.setItem('game-state-campaign-id', campaignId);
    }
  }, [sessionId, campaignId, characterState, worldState, sessionNotes, threatLevel, dmEngineState]);

  const updateCharacter = (updates) => {
    console.log('🔥 GameStateContext: REPLACING character completely with:', updates);
    console.log('📊 Stats being set:', updates.stats);
    console.log('📊 Level being set:', updates.level);
    console.log('📊 Proficiency bonus being set:', updates.proficiency_bonus);
    
    // COMPLETE REPLACEMENT, not merge - this ensures no old data persists
    setCharacterState(updates);
    
    console.log('✅ GameStateContext: Character COMPLETELY REPLACED');
    console.log('📝 New character name:', updates.name);
    console.log('🎭 New character background:', updates.background);
    console.log('🏹 New character class:', updates.class);
    console.log('🆔 New character ID:', updates.id);
    console.log('📊 New character stats:', updates.stats);
    
    setIsDirty(true);
  };

  const updateWorld = (updates) => {
    setWorldState(prev => ({ ...prev, ...updates }));
    setIsDirty(true);
  };

  const addSessionNote = (note) => {
    setSessionNotes(prev => {
      const updated = [...prev, { text: note, timestamp: Date.now() }];
      return updated.slice(-30); // Keep last 30 notes
    });
  };

  const updateThreatLevel = (level) => {
    setThreatLevel(Math.max(0, Math.min(5, level)));
    setIsDirty(true);
  };

  const resetSession = () => {
    console.log('🔄 GameStateContext: Resetting session and clearing character data');
    
    // Clear current session data
    if (sessionId) {
      localStorage.removeItem(`game-state-character-${sessionId}`);
      localStorage.removeItem(`game-state-world-${sessionId}`);
      localStorage.removeItem(`game-state-notes-${sessionId}`);
      localStorage.removeItem(`game-state-threat-${sessionId}`);
    }
    
    // Clear campaign ID
    localStorage.removeItem('game-state-campaign-id');
    setCampaignId('');
    
    // Clear ALL game-state related localStorage items to prevent conflicts
    Object.keys(localStorage).forEach(key => {
      if (key.includes('game-state-session-id') || key.includes('game-state-character') || key.includes('game-state-world') || key.includes('game-state-campaign')) {
        localStorage.removeItem(key);
        console.log(`🗑️ Cleared localStorage: ${key}`);
      }
    });
    
    // Reset character state to placeholder
    setCharacterState({
      id: null,
      name: 'Unnamed Character',
      race: 'Unknown',
      class: 'Unknown',
      level: 1,
      background: 'Unknown',
      alignment: 'Neutral',
      stats: { str: 10, dex: 10, con: 10, int: 10, wis: 10, cha: 10 },
      proficiency_bonus: 2,
      hp: { current: 10, max: 10, temp: 0 },
      ac: 10,
      speed: 30,
      spell_slots: {},
      prepared_spells: [],
      conditions: [],
      virtues: [],
      flaws: [],
      goals: [],
      proficiencies: [],
      inventory: [],
      gold: 0,
      active_quests: [],
      reputation: {},
      notes: 'Character not yet created',
      current_xp: 0,
      xp_to_next: 100,
      attack_bonus: 0,
      injury_count: 0
    });
    
    const newSessionId = `sess-${Date.now()}`;
    setSessionId(newSessionId);
    setSessionNotes([]);
    setThreatLevel(2);
    setIsDirty(true);
    setLastSentState(null);
  };

  // Build minimal character state for API
  const getCharacterStateMin = () => {
    // Only return character data if a valid character is loaded (has ID)
    if (!characterState.id || characterState.name === 'Unnamed Character') {
      console.warn('⚠️ No valid character loaded - using placeholder data');
      return {
        name: 'Adventurer',
        class: 'Fighter',
        level: 1,
        race: 'Human',
        background: 'Folk Hero',
        stats: { str: 10, dex: 10, con: 10, int: 10, wis: 10, cha: 10 },
        hp: { current: 10, max: 10, temp: 0 },
        ac: 10,
        equipped: [],
        conditions: [],
        spell_slots: {},
        prepared_spells: [],
        proficiencies: [],
        virtues: [],
        flaws: [],
        goals: [],
        gold: 0
      };
    }
    
    return {
      name: characterState.name,
      class: characterState.class,
      level: characterState.level,
      race: characterState.race,
      background: characterState.background,
      stats: characterState.stats,
      hp: characterState.hp,
      ac: characterState.ac,
      equipped: characterState.inventory
        .filter(item => item.equipped)
        .map(item => ({ name: item.name, tags: item.tags })),
      conditions: characterState.conditions,
      spell_slots: characterState.spell_slots,
      prepared_spells: characterState.prepared_spells,
      proficiencies: characterState.proficiencies,
      virtues: characterState.virtues,
      flaws: characterState.flaws,
      goals: characterState.goals,
      gold: characterState.gold
    };
  };

  // Build minimal world state for API
  const getWorldStateMin = () => ({
    location: worldState.location,
    settlement: worldState.settlement,
    region: worldState.region,
    time_of_day: worldState.time_of_day,
    weather: worldState.weather
  });

  // Compute deltas since last sent state
  const getDeltas = () => {
    if (!lastSentState) return null;
    
    const deltas = {};
    const current = getCharacterStateMin();
    
    Object.keys(current).forEach(key => {
      if (JSON.stringify(current[key]) !== JSON.stringify(lastSentState[key])) {
        deltas[key] = current[key];
      }
    });
    
    return Object.keys(deltas).length > 0 ? deltas : null;
  };

  // Build complete payload for API (LEGACY - for old /api/rpg_dm)
  const buildTurnPayload = (playerMessage) => {
    const characterStateMin = getCharacterStateMin();
    const worldStateMin = getWorldStateMin();
    const deltas = getDeltas();
    
    console.log('🚀🚀🚀 CRITICAL API PAYLOAD DEBUG 🚀🚀🚀');
    console.log('🎭 Character Name BEING SENT:', characterStateMin.name);
    console.log('🏛️ Character Background BEING SENT:', characterStateMin.background);
    console.log('🏹 Character Class BEING SENT:', characterStateMin.class);
    console.log('🌟 Character Race BEING SENT:', characterStateMin.race);
    console.log('📊 COMPLETE CHARACTER STATE BEING SENT:', characterStateMin);
    
    setLastSentState(characterStateMin);
    setIsDirty(false);
    
    return {
      session_id: sessionId,
      player_message: playerMessage,
      character_state: characterStateMin,
      world_state: worldStateMin,
      session_notes: sessionNotes.slice(-5).map(n => n.text),
      threat_level: threatLevel,
      deltas: deltas
    };
  };

  // NEW: Build action payload for DUNGEON FORGE /api/rpg_dm/action
  const buildActionPayload = (playerAction, checkResult = null, clientTargetId = null) => {
    if (!campaignId) {
      console.error('❌ Cannot build action payload: no campaign_id');
      return null;
    }
    if (!characterState.id) {
      console.error('❌ Cannot build action payload: no character_id');
      return null;
    }
    
    const payload = {
      campaign_id: campaignId,
      character_id: characterState.id,
      player_action: playerAction,
      check_result: checkResult
    };
    
    // Phase 1: Add client_target_id if provided
    if (clientTargetId) {
      payload.client_target_id = clientTargetId;
    }
    
    return payload;
  };

  // DM-ENGINE v1 functions
  const updateDmEngineState = (updates) => {
    setDmEngineState(prev => ({ ...prev, ...updates }));
  };

  const updateRuleOfCool = (value) => {
    setDmEngineState(prev => ({
      ...prev,
      rulebook: { ...prev.rulebook, rule_of_cool: value }
    }));
  };

  const addRocEvent = (event) => {
    setDmEngineState(prev => ({
      ...prev,
      runtime: {
        ...prev.runtime,
        roc_events: [...prev.runtime.roc_events, event]
      }
    }));
  };

  const value = {
    sessionId,
    setSessionId,
    campaignId, // NEW
    setCampaignId, // NEW
    worldBlueprint, // NEW
    setWorldBlueprint, // NEW
    characterState,
    worldState,
    sessionNotes,
    threatLevel,
    isDirty,
    updateCharacter,
    updateWorld,
    addSessionNote,
    updateThreatLevel,
    resetSession,
    buildTurnPayload, // LEGACY
    buildActionPayload, // NEW for DUNGEON FORGE
    getCharacterStateMin,
    getWorldStateMin,
    dmEngineState,
    updateDmEngineState,
    updateRuleOfCool,
    addRocEvent
  };

  return (
    <GameStateContext.Provider value={value}>
      {children}
    </GameStateContext.Provider>
  );
};
