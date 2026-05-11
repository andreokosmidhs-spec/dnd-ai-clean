import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import MainMenu from './MainMenu';
import FocusedRPG from './FocusedRPG';
import WorldMap from './WorldMap';
import WorldMapGraph from './WorldMapGraph';
import Inventory from './Inventory';
import LevelUpScreen from './LevelUpScreen';
import XPBar from './XPBar';
import { mockData } from '../data/mockData';
import { useGameState } from '../contexts/GameStateContext';
import { generateWorldBlueprint, createCharacter, getLastCampaign } from '../api/rpgClient';
import sessionManager from '../state/SessionManager';
import GameEscapeMenu from './GameEscapeMenu';
import DMNotebookPanel from './DMNotebookPanel';
import { checkLevelUp, getLevelFromXP, getXPForNextLevel } from '../data/levelingData';
import { useSessionCore } from '../store/useSessionCore';
import { raceData as RACE_DATA } from '../data/raceData';
import { BACKGROUNDS_BY_KEY } from '../data/backgroundData';
import { computeMaxHp } from '../utils/hp';
import { computeArmorClass } from '../utils/ac';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Deterministic index from string (so the same character keeps the same seeded roleplay picks)
const hashIndex = (seed, modulo) => {
  if (!seed || modulo <= 0) return 0;
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  }
  return hash % modulo;
};

// Enrich the character for the legacy RPG UI with roleplay details pulled
// from the chosen race + background data (ideals / bonds / flaws / traits).
// If the player explicitly picked an Ideal/Bond/Flaw in the wizard, those are
// preferred; otherwise we fall back to a deterministic pick from the pool so
// the sidebar still has something to show.
const enrichRoleplay = (character, raceKey, backgroundKey, persistedPersonality = null) => {
  const raceEntry = raceKey ? RACE_DATA[raceKey] : null;
  const raceTraits = (raceEntry?.traits || []).map((t) => ({
    name: t?.name || '',
    text: t?.summary || t?.description || t?.mechanical_effect || '',
  })).filter((t) => t.name);

  const bg = backgroundKey ? BACKGROUNDS_BY_KEY[backgroundKey] : null;
  const personality = bg?.personality || {};
  const idealsPool = personality.ideals || [];
  const bondsPool = personality.bonds || [];
  const flawsPool = personality.flaws || [];
  const seed = character?.id || character?.name || '';

  // Player-chosen values win when present — but only when they are real,
  // non-empty, trimmed strings (not stray defaults from older schemas).
  const isSet = (v) => typeof v === 'string' && v.trim().length > 0;
  const playerIdeal = isSet(persistedPersonality?.ideal) ? persistedPersonality.ideal.trim() : '';
  const playerBond = isSet(persistedPersonality?.bond) ? persistedPersonality.bond.trim() : '';
  const playerFlaw = isSet(persistedPersonality?.flaw) ? persistedPersonality.flaw.trim() : '';

  const idealPick = playerIdeal || (idealsPool.length ? idealsPool[hashIndex(seed + ':ideal', idealsPool.length)] : null);
  const bondPick = playerBond || (bondsPool.length ? bondsPool[hashIndex(seed + ':bond', bondsPool.length)] : null);
  const flawPick = playerFlaw || (flawsPool.length ? flawsPool[hashIndex(seed + ':flaw', flawsPool.length)] : null);

  return {
    ...character,
    traits: raceTraits,
    ideals: idealPick
      ? [{ principle: idealPick, inspiration: bg?.feature?.description || '', playerChosen: !!playerIdeal }]
      : [],
    bonds: bondPick
      ? [{ person_or_cause: bondPick, playerChosen: !!playerBond }]
      : [],
    flaws_detailed: flawPick
      ? [{ habit: flawPick, interference: '', playerChosen: !!playerFlaw }]
      : [],
    aspiration: bg?.feature
      ? { goal: bg.feature.name, motivation: bg.feature.description }
      : null,
  };
};

const RPGGame = () => {
  const navigate = useNavigate();
  const { updateCharacter, updateWorld, resetSession, setCampaignId, campaignId, worldBlueprint, setWorldBlueprint, setSessionId } = useGameState();
  
  // CRITICAL FIX: Restore campaignId from localStorage if missing
  useEffect(() => {
    if (!campaignId) {
      const storedCampaignId = localStorage.getItem('game-state-campaign-id');
      if (storedCampaignId) {
        console.log('🔧 RPGGame: Restoring campaignId from localStorage:', storedCampaignId);
        setCampaignId(storedCampaignId);
      }
    }
  }, [campaignId, setCampaignId]);
  
  // gameState tracks only the main menu vs. in-game experience; new campaigns now flow through CharacterCreationV2.
  const [gameState, setGameState] = useState('main-menu'); // main-menu, playing
  // ESC pause menu — only meaningful in-game.
  const [escMenuOpen, setEscMenuOpen] = useState(false);
  // DM Notebook — opened from the ESC pause menu, shows persistent lessons.
  const [dmNotebookOpen, setDmNotebookOpen] = useState(false);
  const [character, setCharacter] = useState(null);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [worldData, setWorldData] = useState(mockData.world);
  const [inventory, setInventory] = useState([]);
  const [currentRegion, setCurrentRegion] = useState('temperate-forest');
  const [activeTab, setActiveTab] = useState('game');
  const [showLevelUp, setShowLevelUp] = useState(false);
  const [pendingLevel, setPendingLevel] = useState(null);

  const [gameLog, setGameLog] = useState([
    {
      type: 'system',
      message: 'Welcome to the Realm of Shadows and Steel. Your adventure begins now...',
      timestamp: Date.now()
    }
  ]);

  // Check for existing campaign on mount
  useEffect(() => {
    const savedChar = localStorage.getItem('rpg-campaign-character');
    if (savedChar) {
      try {
        const parsed = JSON.parse(savedChar);
        setCharacter(parsed);
        
        // Load saved game state if exists
        const savedGameState = localStorage.getItem('rpg-campaign-gamestate');
        if (savedGameState) {
          const gameData = JSON.parse(savedGameState);
          setCurrentLocation(gameData.currentLocation || null);
          setInventory(gameData.inventory || []);
          
          // P3.5 Fix: Ensure gameLog has intro, fetch if missing
          if (gameData.gameLog && gameData.gameLog.length > 0) {
            setGameLog(gameData.gameLog);
            console.log('📜 Loaded gameLog with', gameData.gameLog.length, 'entries');
          } else {
            console.warn('⚠️ GameLog empty, intro might be missing');
            setGameLog([]);
          }
        }
      } catch (e) {
        console.error('Failed to load campaign:', e);
      }
    }
  }, []);

  // ESC opens the in-game pause menu when actively playing. We toggle so a
  // second ESC closes it (standard game UX). Ignore ESC while we're on the
  // main menu — the user has nothing to pause out of.
  useEffect(() => {
    if (gameState !== 'playing') return;
    const handler = (e) => {
      if (e.key !== 'Escape') return;
      // If the user is mid-typing in an input/textarea, let ESC blur first
      // and don't open the menu — common chat-input expectation.
      const tag = (e.target && e.target.tagName) || '';
      const editable = (e.target && e.target.isContentEditable) || false;
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tag) || editable) {
        return;
      }
      e.preventDefault();
      setEscMenuOpen((open) => !open);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [gameState]);


  // SESSION-CORE BRIDGE: Detect when new flow has a ready campaign
  // This bridges the new CharacterCreationV2 → CampaignGenerate flow into RPGGame
  const { activeCharacterId, activeCampaignId, campaignStatus } = useSessionCore();
  const sessionCoreBridgeRan = useRef(false);
  
  useEffect(() => {
    // Only run once per mount when session-core indicates a ready campaign
    if (sessionCoreBridgeRan.current) return;
    
    // Check if session-core has a ready campaign from new flow
    if (campaignStatus === 'ready' && activeCharacterId && activeCampaignId) {
      console.log('🌉 Session-Core Bridge: Detected ready campaign from new flow');
      console.log('   - characterId:', activeCharacterId);
      console.log('   - campaignId:', activeCampaignId);
      console.log('   - status:', campaignStatus);
      
      // Mark bridge as ran to prevent infinite loops
      sessionCoreBridgeRan.current = true;
      
      // Fetch campaign data and transition to playing state
      const loadFromSessionCore = async () => {
        let characterForRPG = null;
        
        try {
          // Fetch character by ID (this is the main data we need)
          const characterRes = await fetch(`${BACKEND_URL}/api/v2/characters/${activeCharacterId}`);
          const characterData = await characterRes.json();
          
          console.log('🌉 Bridge: Fetched character:', characterData?.identity?.name || characterData?.name || 'Unknown');
          
          // Build character object for RPGGame from CharacterCreationV2 format
          const identity = characterData?.identity || {};
          const raceField = characterData?.race || {};
          const classData = characterData?.class || {};
          // Backend returns abilityScores (camelCase) with lowercase keys (str, dex, con, int, wis, cha)
          // Fallback to legacy abilities shape just in case
          const abilities = characterData?.abilityScores || characterData?.abilities || {};
          const bgData = characterData?.background || {};
          
          // Spread characterData first, then override with properly extracted values
          // This ensures object fields like background are converted to strings
          // Compute max HP from class + CON using the 5e fixed-average rule.
          const conForHp = abilities.con ?? abilities.CON ?? abilities.constitution ?? 10;
          const computedMaxHp =
            computeMaxHp(classData.key, conForHp, classData.level || 1) ?? 10;
          // Compute AC from class starting equipment (armor + shield) +
          // ability scores + Unarmored Defense (Barbarian/Monk).
          const acResult = computeArmorClass({
            abilityScores: abilities,
            class: classData,
          });
          const baseCharacter = {
            ...characterData,
            id: activeCharacterId,
            name: identity.name || characterData?.name || 'Adventurer',
            class: classData.key || characterData?.class_ || 'Unknown',
            subclass: classData.subclassKey || '',
            race: raceField.key || characterData?.race || 'Unknown',
            level: classData.level || characterData?.level || 1,
            hp: characterData?.hitPoints?.current || characterData?.hp || computedMaxHp,
            maxHp: characterData?.hitPoints?.max || characterData?.max_hp || computedMaxHp,
            // Legacy sidebars/sheets read character.hitPoints directly (flat int).
            // Keep this in sync with computedMaxHp so the Health panel is never blank.
            hitPoints: computedMaxHp,
            // Mechanical AC (10 + DEX + armor + shield + class features).
            armorClass: acResult.ac,
            acBreakdown: acResult.breakdown,
            stats: (() => {
              const str = abilities.str ?? abilities.STR ?? abilities.strength ?? 10;
              const dex = abilities.dex ?? abilities.DEX ?? abilities.dexterity ?? 10;
              const con = abilities.con ?? abilities.CON ?? abilities.constitution ?? 10;
              const intel = abilities.int ?? abilities.INT ?? abilities.intelligence ?? 10;
              const wis = abilities.wis ?? abilities.WIS ?? abilities.wisdom ?? 10;
              const cha = abilities.cha ?? abilities.CHA ?? abilities.charisma ?? 10;
              return {
                // Short uppercase keys (used by newer components)
                STR: str, DEX: dex, CON: con, INT: intel, WIS: wis, CHA: cha,
                // Full lowercase names (used by CharacterSheet, CharacterSidebar, InfoDrawer, Inventory, LevelUpScreen)
                strength: str,
                dexterity: dex,
                constitution: con,
                intelligence: intel,
                wisdom: wis,
                charisma: cha,
              };
            })(),
            // Ensure background is a string, not an object
            background: bgData.key || bgData.name || '',
            skills: characterData?.skills || [],
            equipment: characterData?.equipment || [],
            spells: characterData?.spells || [],
            // Portrait (AI-generated via Nano Banana, may be null until ready)
            portrait: characterData?.portraitDataUrl || characterData?.portrait || null,
          };

          characterForRPG = enrichRoleplay(baseCharacter, raceField.key, bgData.key, bgData?.personality);
          
          console.log('🌉 Bridge: Built character:', characterForRPG.name, characterForRPG.race, characterForRPG.class);
        } catch (err) {
          console.warn('🌉 Bridge: Failed to fetch character, using fallback:', err);
          characterForRPG = {
            id: activeCharacterId,
            name: 'Adventurer',
            class: 'Unknown',
            race: 'Unknown',
            level: 1,
            hp: 10,
            maxHp: 10,
            stats: {
              STR: 10, DEX: 10, CON: 10, INT: 10, WIS: 10, CHA: 10,
              strength: 10, dexterity: 10, constitution: 10,
              intelligence: 10, wisdom: 10, charisma: 10,
            }
          };
        }
        
        // Set character state
        setCharacter(characterForRPG);
        
        // Bridge to legacy storage for compatibility with other components
        localStorage.setItem('rpg-campaign-character', JSON.stringify(characterForRPG));
        console.log('🌉 Bridge: Character data set and saved to legacy storage');

        // If the portrait isn't ready yet (Nano Banana generation runs in the
        // background), trigger generation (self-healing in case the initial
        // fire-and-forget from ReviewStep was dropped) and poll to pick it up.
        if (!characterForRPG.portrait && activeCharacterId) {
          // Kick off (or re-kick) generation — backend overwrites if already running
          fetch(`${BACKEND_URL}/api/characters/v2/${activeCharacterId}/generate-portrait`, {
            method: 'POST',
          }).then(async (r) => {
            if (r.ok) {
              const d = await r.json();
              if (d?.portraitDataUrl) {
                setCharacter((prev) => (prev ? { ...prev, portrait: d.portraitDataUrl } : prev));
              }
            }
          }).catch((err) => {
            console.warn('Bridge portrait generation failed:', err);
          });

          // Poll as a fallback in case the POST above was kicked off earlier and
          // is mid-flight on another client.
          const pollPortrait = async (attempts = 0) => {
            if (attempts >= 8) return;
            await new Promise((r) => setTimeout(r, 5000));
            try {
              const res = await fetch(`${BACKEND_URL}/api/v2/characters/${activeCharacterId}`);
              const d = await res.json();
              const url = d?.portraitDataUrl || d?.portrait;
              if (url) {
                setCharacter((prev) => (prev && !prev.portrait ? { ...prev, portrait: url } : prev));
                return;
              }
            } catch (_) { /* ignore */ }
            pollPortrait(attempts + 1);
          };
          pollPortrait();
        }
        
        // Set campaign ID in GameStateContext
        setCampaignId(activeCampaignId);
        localStorage.setItem('game-state-campaign-id', activeCampaignId);
        
        // Fetch the campaign's starting scene intro (generated by the world builder)
        // and use it as the opening narration. Falls back to a generic welcome.
        let introMessage = `Welcome, ${characterForRPG.name}! As a ${characterForRPG.race} ${characterForRPG.class}, your adventure in this realm begins now. The world awaits your exploration...`;
        let worldBriefMessage = '';
        let introMentions = [];
        let worldBriefMentions = [];
        let campaignWorld = null;
        try {
          const campRes = await fetch(`${BACKEND_URL}/api/campaigns/${activeCampaignId}`);
          if (campRes.ok) {
            const campData = await campRes.json();
            const startingIntro =
              campData?.starting_scene?.introText ||
              campData?.startingScene?.introText;
            if (startingIntro && startingIntro.trim()) {
              introMessage = startingIntro;
            }
            // Macro chronicler preface (geography / history / political / cultures)
            // — displayed as a separate adventure-log entry BEFORE the personal arrival.
            worldBriefMessage =
              campData?.starting_scene?.worldBrief ||
              campData?.startingScene?.worldBrief ||
              campData?.world?.world_brief ||
              '';
            // Entity highlights — backend extracts these so locations, factions,
            // and NPCs are clickable in the chronicle and arrival scenes.
            introMentions =
              campData?.starting_scene?.entity_mentions ||
              campData?.startingScene?.entity_mentions ||
              [];
            worldBriefMentions =
              campData?.starting_scene?.world_brief_entity_mentions ||
              campData?.startingScene?.world_brief_entity_mentions ||
              campData?.world?.world_brief_entity_mentions ||
              [];
            campaignWorld = campData?.world || null;
          }
        } catch (err) {
          console.warn('Failed to fetch campaign intro, using fallback:', err);
        }

        // Build the seed entries: [chronicler preface (if any)] then the personal arrival.
        const realmName =
          (campaignWorld?.world_core?.name) ||
          (campaignWorld?.theme ? `Realm of ${campaignWorld.theme}` : 'The Known Realm');
        const seedEntries = [];
        if (worldBriefMessage && worldBriefMessage.trim()) {
          seedEntries.push({
            type: 'dm',
            text: worldBriefMessage,
            message: worldBriefMessage,
            timestamp: Date.now(),
            isCinematic: true,
            isWorldBrief: true,
            chronicleTitle: `A Chronicle of ${realmName}`,
            source: 'world-brief',
            entity_mentions: worldBriefMentions,
          });
        }
        seedEntries.push({
          type: 'dm',
          text: introMessage,
          message: introMessage,
          timestamp: Date.now() + 1,
          isCinematic: true,
          source: 'intro',
          entity_mentions: introMentions,
        });
        setGameLog(seedEntries);

        // Create session for AdventureLogWithDM
        const newSessionId = sessionManager.createNewSessionId(activeCampaignId);
        setSessionId(newSessionId);
        localStorage.setItem('game-state-session-id', newSessionId);

        // CRITICAL: Seed AdventureLogWithDM's per-session message store so both
        // the chronicle preface AND personal intro are visible in the Adventure
        // Log, and mark intro as played so the auto-generation path stays off.
        localStorage.setItem(
          `dm-log-messages-${newSessionId}`,
          JSON.stringify(seedEntries)
        );
        localStorage.removeItem(`dm-log-options-${newSessionId}`);
        localStorage.setItem('dm-intro-played', '1');

        // Provide a worldBlueprint so AdventureLogWithDM's auto-intro guard
        // passes AND the top-bar WorldInfoPanel shows the real realm / town
        // name instead of "Unknown Realm / Unknown Town". We pull world_core
        // and starting_town from the campaign record (populated by
        // backend/services/campaign_service.build_world_blueprint).
        if (setWorldBlueprint) {
          const startingLocation = campaignWorld?.startingLocation || {};
          const worldCore = campaignWorld?.world_core || {
            name: campaignWorld?.theme
              ? `Realm of ${campaignWorld.theme}`
              : 'The Known Realm',
            summary: campaignWorld?.summary || '',
            tone: campaignWorld?.tone || '',
          };
          const startingTown = campaignWorld?.starting_town || {
            name: startingLocation.name || 'Starting Area',
            summary: startingLocation.description || '',
          };
          setWorldBlueprint({
            intro: introMessage,
            entity_mentions: [],
            world_core: worldCore,
            starting_town: startingTown,
            startingLocation,
            // Pass the rich setting (era, factions, recent_events, current_tension)
            // through so WorldInfoPanel can render era, faction details, history,
            // and tension. Falls back to undefined if a legacy campaign without it.
            setting: campaignWorld?.setting,
          });
        }
        
        // Transition to playing state
        setGameState('playing');
        console.log('🌉 Bridge: Transitioned to playing state');
        
        if (window.showToast) {
          window.showToast(`Welcome, ${characterForRPG.name}! Your adventure begins...`, 'success');
        }
      };
      
      loadFromSessionCore();
    }
  }, [campaignStatus, activeCharacterId, activeCampaignId, setCampaignId, setWorldBlueprint, setSessionId]);

  const saveGame = () => {
    // Save character
    localStorage.setItem('rpg-campaign-character', JSON.stringify(character));
    
    // Save game state
    const gameData = {
      currentLocation,
      inventory,
      gameLog
    };
    localStorage.setItem('rpg-campaign-gamestate', JSON.stringify(gameData));
    
    if (window.showToast) {
      window.showToast('💾 Campaign saved!', 'success');
    } else {
      alert('Campaign saved!');
    }
  };

  const startNewGame = () => {
    setGameState('main-menu');
  };

  const handleNewCampaign = () => {
    console.log('🔥 NUCLEAR RESET - CLEARING ALL DATA INCLUDING ARIS');

    // NUCLEAR OPTION: Clear absolutely everything
    localStorage.clear();
    sessionStorage.clear();
    
    // Clear ALL localStorage items related to adventure log
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && (key.startsWith('dm-log-') || key.startsWith('dm-intro-') || key === 'dm-session-id' || key === 'dm-intent-mode' || key === 'check_attempts')) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach(key => localStorage.removeItem(key));
    console.log('🧹 Cleared adventure log storage:', keysToRemove);
    
    // Reset game state context for new campaign
    resetSession();
    
    // Force complete character reset
    setCharacter(null);
    setCurrentLocation(null);
    setInventory([]);
    setGameLog([
      { type: 'system', message: 'Welcome to RPG Forge! Create your character to begin your adventure.' }
    ]);

    navigate('/character-v2');

    console.log('🗑️ COMPLETE DATA WIPE - NEW CAMPAIGN STARTED!');
  };

  const handleContinueCampaign = () => {
    if (character) {
      // CRITICAL FIX: Ensure sessionId is set for AdventureLogWithDM to load messages
      const existingSessionId = localStorage.getItem('game-state-session-id');
      
      if (existingSessionId) {
        // Session already exists, just transition to playing
        console.log('📋 Continue campaign with existing session:', existingSessionId);
        setSessionId(existingSessionId); // Ensure context is updated
      } else {
        // No session found, create one based on campaign
        console.log('🆕 Creating new session for continue game');
        const newSessionId = sessionManager.createNewSessionId(campaignId);
        setSessionId(newSessionId);
      }
      
      setGameState('playing');
      if (window.showToast) {
        window.showToast(`Welcome back, ${character.name}!`, 'success');
      }
    }
  };

  // Helper function to safely extract narration text from any response structure
  const extractNarration = (data) => {
    // If data is null/undefined, return empty string
    if (!data) return '';
    
    // If data is a string, check if it's JSON
    if (typeof data === 'string') {
      let trimmed = data.trim();
      
      // Remove code fence markers if present
      if (trimmed.startsWith('```json') || trimmed.startsWith('```')) {
        trimmed = trimmed.replace(/^```(json)?/g, '').replace(/```$/g, '').trim();
      }
      
      // Remove 'json' prefix if present (e.g., "json{...}")
      if (trimmed.startsWith('json{') || trimmed.startsWith('json[')) {
        trimmed = trimmed.substring(4).trim();
      }
      
      // Check if it looks like JSON (starts with { or [)
      if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
        try {
          const parsed = JSON.parse(trimmed);
          return extractNarration(parsed);
        } catch (e) {
          // Not valid JSON, return as-is
          console.warn('Failed to parse JSON intro:', e);
          return data;
        }
      }
      return data;
    }
    
    // If data is an object, try to extract narration field
    if (typeof data === 'object') {
      return data.narration || data.intro_markdown || data.text || '';
    }
    
    return String(data);
  };

  const handleLoadLastCampaign = (campaignData) => {
    console.log('🔄 Loading campaign from database:', campaignData.campaign_id);
    console.log('🔄 campaignData keys:', Object.keys(campaignData));
    
    // CRITICAL: Clear old data FIRST to force fresh load
    const tempSessionId = `sess-${campaignData.campaign_id}`;
    localStorage.removeItem(`dm-log-messages-${tempSessionId}`);
    localStorage.removeItem('dm-intro-played');
    console.log('🧹 Cleared old localStorage data for fresh load');
    
    try {
      const { campaign_id, world_blueprint, intro, entity_mentions, scene_description, starting_location, character, character_id, world_state } = campaignData;
      console.log('🔄 Extracted scene_description:', scene_description);
      console.log('🔄 Extracted entity_mentions:', entity_mentions ? entity_mentions.length : 'MISSING');
      
      // CRITICAL: Set sessionId FIRST before updating character
      // This ensures localStorage saves work correctly
      const newSessionId = `sess-${campaign_id}`;
      setSessionId(newSessionId);
      console.log('✅ Set sessionId FIRST:', newSessionId);
      
      // Set campaign ID and world blueprint in context
      setCampaignId(campaign_id);
      setWorldBlueprint(world_blueprint);
      
      // Create full character object from loaded data
      // CRITICAL FIX: Backend returns "abilities" but frontend expects "stats"
      const characterStats = character.abilities || character.stats || {
        str: 10, dex: 10, con: 10, int: 10, wis: 10, cha: 10
      };
      
      console.log('🔍 Backend character.abilities:', character.abilities);
      console.log('🔍 Mapped to stats:', characterStats);
      console.log('🔍 Character stats should be:', characterStats);
      
      // Force alert to confirm code is actually running
      if (!characterStats || !characterStats.str) {
        console.error('❌ CRITICAL: Stats mapping failed!', { 
          abilities: character.abilities, 
          stats: character.stats,
          mapped: characterStats 
        });
      } else {
        console.log('✅ Stats mapped successfully:', characterStats);
      }
      
      const loadedCharacter = {
        id: character_id,
        name: character.name,
        race: character.race,
        class: character.class_,
        level: character.level,
        background: character.background,
        alignment: character.alignment,
        stats: characterStats,
        hitPoints: character.hp?.max || character.max_hp || character.hp || 10,
        aspiration: character.aspiration || character.goal
      };
      
      setCharacter(loadedCharacter);
      
      // Update GameStateContext with character data
      const contextCharacterData = {
        id: character_id,
        name: character.name,
        race: character.race,
        class: character.class_,
        level: character.level,
        background: character.background,
        alignment: character.alignment,
        stats: characterStats,
        proficiency_bonus: character.proficiency_bonus || 2,
        hp: {
          current: character.hp || character.hp?.current || 10,
          max: character.max_hp || character.hp?.max || 10
        },
        ac: character.ac,
        speed: character.speed,
        spell_slots: character.spell_slots || {},
        prepared_spells: character.prepared_spells || [],
        cantrips: character.cantrips || [],
        conditions: character.conditions || [],
        traits: character.traits || [],
        ideals: character.ideals || [],
        bonds: character.bonds || [],
        flaws: character.flaws || character.flaws_detailed || [],
        aspiration: character.aspiration || { goal: '', motivation: '' },
        proficiencies: character.proficiencies || [],
        inventory: character.inventory || [],
        gold: character.gold || 0,
        active_quests: character.active_quests || [],
        reputation: character.reputation || {},
        notes: character.notes || '',
        attack_bonus: character.attack_bonus || 0,
        current_xp: character.current_xp || 0,
        xp_to_next: character.xp_to_next || 100,
        injury_count: character.injury_count || 0
      };
      
      console.log('📊 Character data to update:', {
        name: contextCharacterData.name,
        level: contextCharacterData.level,
        stats: contextCharacterData.stats
      });
      
      updateCharacter(contextCharacterData);
      console.log('✅ Character data updated in context');
      
      // Update world state in context
      const startingLocationName = world_state.current_location || world_blueprint.starting_town?.name || 'Unknown Town';
      
      const worldStateData = {
        region: world_blueprint.starting_region?.name || 'Unknown Region',
        settlement: startingLocationName,
        location: startingLocationName,
        current_location: startingLocationName,
        time_of_day: world_state.time_of_day || 'midday',
        weather: world_state.weather || 'clear',
        active_npcs: world_state.active_npcs || [],
        faction_states: world_state.faction_states || {},
        quest_flags: world_state.quest_flags || {},
        recent_events: world_state.recent_events || []
      };
      
      updateWorld(worldStateData);
      
      // Set location
      setCurrentLocation({
        name: startingLocationName,
        region: currentRegion,
        description: world_blueprint.starting_town?.summary || 'A place of adventure'
      });
      
      // Create intro message for game log with entity mentions
      // Use extractNarration to safely handle any response structure
      const cleanIntro = extractNarration(intro);
      console.log('🧹 Cleaned intro:', cleanIntro.substring(0, 100));
      
      const initialLog = [{
        type: 'dm',
        text: cleanIntro || 'Your adventure continues...',
        timestamp: Date.now(),
        isCinematic: true,
        source: 'intro',
        entity_mentions: entity_mentions || []  // Entity mentions from backend
      }];
      
      // Add scene description if available
      if (scene_description) {
        const sceneText = `📍 **${scene_description.location}**\n\n${scene_description.description}\n\n*${scene_description.why_here}*`;
        initialLog.push({
          type: 'dm',
          text: sceneText,
          timestamp: Date.now() + 1,
          source: 'scene_description'
        });
        console.log('✅ Added scene description for:', scene_description.location);
      }
      
      console.log('✅ Loaded intro with', entity_mentions ? entity_mentions.length : 0, 'entity mentions');
      setGameLog(initialLog);
      
      // ====================================================================
      // CRITICAL FIX: Set up AdventureLogWithDM localStorage properly
      // ====================================================================
      
      // CRITICAL: Save intro to localStorage (DIRECT - more reliable)
      // NOTE: sessionId already set earlier
      localStorage.removeItem(`dm-log-messages-${newSessionId}`);
      localStorage.removeItem(`dm-log-options-${newSessionId}`);
      localStorage.setItem('game-state-session-id', newSessionId);
      localStorage.setItem(`dm-log-messages-${newSessionId}`, JSON.stringify(initialLog));
      localStorage.setItem('dm-intro-played', '1');
      
      console.log('🆔 Saved intro for continue game:', newSessionId);
      console.log('✅ Loaded intro with', entity_mentions ? entity_mentions.length : 0, 'entity mentions');
      
      // Set sessionId in context
      setSessionId(newSessionId);
      console.log('🆔 SessionId set in context:', newSessionId);
      
      // ====================================================================
      
      // Save to RPGGame localStorage
      localStorage.setItem('rpg-campaign-character', JSON.stringify(loadedCharacter));
      
      const gameData = {
        currentLocation: { name: startingLocationName, region: currentRegion },
        inventory: character.inventory || [],
        gameLog: initialLog
      };
      localStorage.setItem('rpg-campaign-gamestate', JSON.stringify(gameData));
      
      // Transition to playing state
      setGameState('playing');
      
      console.log('✅ Campaign loaded successfully');
      
    } catch (error) {
      console.error('❌ Error loading campaign:', error);
      if (window.showToast) {
        window.showToast('❌ Failed to load campaign data', 'error');
      }
    }
  };

  const onCharacterCreated = async (newCharacter, progressCallback) => {
    console.log('🎭 [FLOW START] Character created:', newCharacter);
    
    // Progress callback helper
    const updateProgress = (progress) => {
      if (progressCallback) {
        progressCallback(progress);
      }
    };
    
    // Show loading toast
    if (window.showToast) {
      window.showToast('🌍 Generating your world...', 'info');
    }
    
    // Clear intro played flag so the intro will load
    localStorage.removeItem('dm-intro-played');
    console.log('🎬 Cleared dm-intro-played flag for new character');
    
    try {
      // Step 1: Generate world blueprint with context (0% -> 30%)
      updateProgress(5);
      console.log('🌍 [FLOW] Calling generateWorldBlueprint...');
      const worldPayload = {
        world_name: newCharacter.aspiration?.goal || 'The Realm of Adventure',
        tone: 'Dark fantasy with rare magic',
        starting_region_hint: `A ${newCharacter.background} from ${newCharacter.race} heritage begins their journey`
      };
      console.log('🌍 [FLOW] World payload:', worldPayload);
      
      const worldData = await generateWorldBlueprint(worldPayload);
      const { campaign_id, world_blueprint, world_state } = worldData;
      updateProgress(30);
      
      if (!campaign_id) {
        throw new Error('❌ No campaign_id returned from world generation');
      }
      
      console.log('✅ [FLOW] World generated! Campaign ID:', campaign_id);
      console.log('✅ [FLOW] Campaign should now exist in MongoDB campaigns collection');
      
      // Store campaign_id and world_blueprint in context
      setCampaignId(campaign_id);
      setWorldBlueprint(world_blueprint);
      
      // Step 2: Persist character to backend (30% -> 50%)
      updateProgress(35);
      console.log('🎭 [FLOW] Calling createCharacter...');
      const characterPayload = {
        campaign_id: campaign_id,
        character: newCharacter
      };
      console.log('🎭 [FLOW] Character payload:', characterPayload);
      
      const characterData = await createCharacter(characterPayload);
      const { character_id, intro_markdown, starting_location, entity_mentions, scene_description } = characterData;
      updateProgress(50);
      
      if (!character_id) {
        throw new Error('❌ No character_id returned from character creation');
      }
      
      console.log('✅ [FLOW] Character persisted! Character ID:', character_id);
      console.log('✅ [FLOW] Character should now exist in MongoDB characters collection');
      console.log('✅ [FLOW] Intro included in response:', intro_markdown ? intro_markdown.length + ' chars' : 'MISSING');
      console.log('✅ [FLOW] Entity mentions in intro:', entity_mentions ? entity_mentions.length : 0);
      
      // Step 3: Process intro (50% -> 70%)
      updateProgress(55);
      
      // Extract and clean intro narration
      const cleanIntro = extractNarration(intro_markdown);
      console.log('🧹 Cleaned intro:', cleanIntro.substring(0, 100));
      
      // CRITICAL: Store intro in worldBlueprint so AdventureLogWithDM can find it
      const worldBlueprintWithIntro = {
        ...world_blueprint,
        intro: cleanIntro,
        entity_mentions: entity_mentions || []
      };
      setWorldBlueprint(worldBlueprintWithIntro);
      console.log('📝 [FLOW] Stored intro in worldBlueprint for AdventureLogWithDM');
      updateProgress(70);
      
      // Update character with backend ID
      const updatedCharacter = { ...newCharacter, id: character_id };
      setCharacter(updatedCharacter);
      
      // ==================================================================
      // END DUNGEON FORGE WIRING
      // ==================================================================
      
      // Use world_blueprint data for starting location
      const startingLocationName = starting_location || world_blueprint.starting_town?.name || 'Unknown Town';
      
      setCurrentLocation({
        name: startingLocationName,
        region: currentRegion,
        description: world_blueprint.starting_town?.summary || 'A place of new beginnings'
      });
    
    // UPDATE GAME STATE CONTEXT with new character data
    const contextCharacterData = {
      id: character_id, // Use backend ID
      name: newCharacter.name,
      race: newCharacter.race,
      class: newCharacter.class,
      level: newCharacter.level || 1,
      background: newCharacter.background,
      alignment: newCharacter.alignment || 'Neutral',
      stats: newCharacter.stats,
      proficiency_bonus: Math.ceil((newCharacter.level || 1) / 4) + 1,
      hp: { 
        current: newCharacter.hitPoints, 
        max: newCharacter.hitPoints, 
        temp: 0 
      },
      ac: newCharacter.armorClass != null
        ? newCharacter.armorClass
        : computeArmorClass(newCharacter).ac, // Base AC + DEX + armor + shield + class features
      speed: 30,
      spell_slots: newCharacter.spellSlots ? { 1: newCharacter.spellSlots.length } : {},
      prepared_spells: newCharacter.spells || [],
      cantrips: newCharacter.cantrips || [], // Racial/class cantrips
      conditions: [],
      traits: newCharacter.traits || [], // Personality traits
      ideals: newCharacter.ideals || [],
      bonds: newCharacter.bonds || [],
      flaws: newCharacter.flaws_detailed || [],
      aspiration: newCharacter.aspiration || { goal: '', motivation: '' },
      proficiencies: newCharacter.proficiencies || [],
      inventory: [
        { id: 'item-1', name: 'Starting Gear', qty: 1, tags: ['equipment'], equipped: true, notes: 'Basic adventuring equipment' }
      ],
      gold: 25,
      active_quests: [],
      reputation: {},
      notes: `${newCharacter.background} turned adventurer`
    };
    
    console.log('🔥 FORCING CHARACTER UPDATE TO CONTEXT:');
    console.log('📝 Character being sent to GameStateContext:', contextCharacterData);
    console.log('🎭 Name:', contextCharacterData.name);
    console.log('🏛️ Background:', contextCharacterData.background);
    console.log('🏹 Class:', contextCharacterData.class);
    
    // Force complete character replacement in context
    updateCharacter(contextCharacterData);
    
    // Update world state with DUNGEON FORGE data
    const worldStateData = {
      region: world_blueprint.starting_region?.name || 'Unknown Region',
      settlement: startingLocationName,
      location: startingLocationName,
      current_location: startingLocationName, // DUNGEON FORGE format
      time_of_day: world_state.time_of_day || 'midday',
      weather: world_state.weather || 'clear',
      active_npcs: world_state.active_npcs || [],
      faction_states: world_state.faction_states || {},
      quest_flags: world_state.quest_flags || {},
      recent_events: [
        `${newCharacter.name} begins their adventure in ${world_blueprint.world_core?.name || 'the realm'}`
      ]
    };
    
    updateWorld(worldStateData);
    
    // Save the new campaign character
    localStorage.setItem('rpg-campaign-character', JSON.stringify(updatedCharacter));
    
    // Initialize starting inventory
    const startingItems = [];
    if (newCharacter.class) {
      // Could add class-specific starting equipment here
    }
    setInventory(startingItems);
    
    // Use the INTRO-NARRATOR generated markdown as the first message
    // cleanIntro was already extracted above at line 479
    console.log('🧹 Using cleaned intro for initialLog:', cleanIntro.substring(0, 100));
    
    const initialLog = [{
      type: 'dm',  // P3.5 Fix: Use 'dm' type so AdventureLogWithDM renders it
      text: cleanIntro,  // P3.5 Fix: Use cleaned narration text only
      timestamp: Date.now(),
      isCinematic: true,  // Mark as cinematic intro
      source: 'intro',
      entity_mentions: entity_mentions || []  // Add entity mentions for clickable entities
    }];
    
    // Add scene description message after intro
    if (scene_description) {
      initialLog.push({
        type: 'dm',
        text: `📍 **${scene_description.location}**\n\n${scene_description.description}\n\n*${scene_description.why_here}*`,
        timestamp: Date.now() + 1,
        source: 'scene_description',
        entity_mentions: []
      });
    }
    
    setGameLog(initialLog);
    console.log('🎭 Intro markdown set:', intro_markdown.substring(0, 100));
    console.log('🎭 GameLog length:', initialLog.length);
    console.log('🎭 GameLog[0] type:', initialLog[0].type);
    console.log('🎭 GameLog[0] text length:', initialLog[0].text.length);
    console.log('🎭 GameLog[0] entity_mentions:', entity_mentions ? entity_mentions.length : 0);

    // Save initial game state with intro
    const gameData = {
      currentLocation: { name: startingLocationName, region: currentRegion },
      inventory: startingItems,
      gameLog: initialLog
    };
    localStorage.setItem('rpg-campaign-gamestate', JSON.stringify(gameData));
    console.log('💾 Saved gamestate to localStorage');
    
    // CRITICAL: Save intro to localStorage (DIRECT - SessionManager caused timing issues)
    const newSessionId = `sess-${campaign_id}`;
    localStorage.setItem('game-state-session-id', newSessionId);
    localStorage.setItem(`dm-log-messages-${newSessionId}`, JSON.stringify(initialLog));
    localStorage.setItem('dm-intro-played', '1');
    console.log('💾 Saved intro with entity_mentions to localStorage:', newSessionId);
    console.log('📊 Entity mentions count:', entity_mentions ? entity_mentions.length : 0);
    
    // Set sessionId in context
    setSessionId(newSessionId);
    console.log('🆔 SessionId set in context:', newSessionId);
    
    // Verify it was saved
    const verify = localStorage.getItem('rpg-campaign-gamestate');
    console.log('✅ Verified gamestate in localStorage:', !!verify);
    
    // Step 4: Final setup (70% -> 100%)
    updateProgress(85);
    
    setGameState('playing');
    console.log('🎮 Game state set to: playing');
    updateProgress(100);
    
    if (window.showToast) {
      window.showToast(`🎉 Welcome to ${world_blueprint.world_core?.name || 'your adventure'}, ${newCharacter.name}!`, 'success');
    }
      
    } catch (error) {
      console.error('❌ Failed to initialize DUNGEON FORGE campaign:', error);
      console.error('❌ Error details:', error.message);
      console.error('❌ Error stack:', error.stack);
      
      // More detailed error message
      let errorMessage = 'Failed to create character';
      if (error.message.includes('campaign_id')) {
        errorMessage = 'World generation failed';
      } else if (error.message.includes('character_id')) {
        errorMessage = 'Character creation failed';
      } else if (error.message.includes('intro')) {
        errorMessage = 'Intro generation failed';
      } else {
        errorMessage = `Error: ${error.message}`;
      }
      
      if (window.showToast) {
        window.showToast(`❌ ${errorMessage}. Check browser console for details.`, 'error');
      }
      
      alert(`Character creation failed!\n\nError: ${error.message}\n\nPlease check the browser console (F12) for more details, or try creating a simpler character (Human Fighter).`);
      
      // Rollback to main menu
      setGameState('main-menu');
      updateProgress(0);
    }
  };

  const addToGameLog = (entry) => {
    setGameLog(prev => [...prev, { ...entry, timestamp: Date.now() }]);
  };

  const changeLocation = (newLocation) => {
    setCurrentLocation(newLocation);
    setCurrentRegion(newLocation.region);
    addToGameLog({
      type: 'system',
      message: `You arrive at ${newLocation.name}. ${newLocation.description}`
    });
  };

  const getBackgroundStyle = () => {
    const backgrounds = {
      'temperate-forest': 'linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)',
      'desert': 'linear-gradient(135deg, #2c1810 0%, #8b4513 50%, #daa520 100%)',
      'arctic': 'linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #87ceeb 100%)',
      'mountains': 'linear-gradient(135deg, #2c3e50 0%, #34495e 50%, #7f8c8d 100%)',
      'swamp': 'linear-gradient(135deg, #1a3a2e 0%, #16423c 50%, #0d2818 100%)'
    };
    return backgrounds[currentRegion] || backgrounds['temperate-forest'];
  };

  // Render Main Menu
  if (gameState === 'main-menu') {
    return (
      <MainMenu
        onNewCampaign={handleNewCampaign}
        onContinueCampaign={handleContinueCampaign}
        onLoadLastCampaign={handleLoadLastCampaign}
      />
    );
  }

  return (
    <div 
      className="min-h-screen transition-all duration-1000 ease-in-out overflow-hidden"
      style={{ background: getBackgroundStyle() }}
    >
      {/* Game Controls - Floating */}
      <div className="absolute top-4 left-4 z-30 flex gap-2">
        <Button 
          onClick={saveGame} 
          size="sm" 
          className="bg-amber-700/80 hover:bg-amber-600 text-black font-semibold backdrop-blur-sm"
        >
          Save Game
        </Button>
        <Button 
          onClick={startNewGame} 
          variant="outline" 
          size="sm" 
          className="border-red-600/50 text-red-400 hover:bg-red-600/20 backdrop-blur-sm"
        >
          New Game
        </Button>
      </div>

      {/* Top Tabs - For switching between views */}
      <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-30">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="bg-black/20 rounded-lg p-1 backdrop-blur-sm">
          <TabsList className="bg-black/50 border border-amber-600/30">
            <TabsTrigger 
              value="game" 
              className="data-[state=active]:bg-amber-600/30 data-[state=active]:text-amber-400 text-sm"
            >
              Adventure
            </TabsTrigger>
            <TabsTrigger 
              value="world" 
              className="data-[state=active]:bg-blue-600/30 data-[state=active]:text-blue-400 text-sm"
            >
              World Map
            </TabsTrigger>
            <TabsTrigger 
              value="inventory" 
              className="data-[state=active]:bg-green-600/30 data-[state=active]:text-green-400 text-sm"
            >
              Full Inventory
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Main Content */}
      <div className="h-screen">
        {activeTab === 'game' && (
          <FocusedRPG
            gameLog={gameLog}
            addToGameLog={addToGameLog}
            character={character}
            currentLocation={currentLocation}
            onLocationChange={changeLocation}
            inventory={inventory}
            setInventory={setInventory}
          />
        )}
        
        {activeTab === 'world' && (
          <div className="h-full p-4">
            {campaignId ? (
              <WorldMapGraph campaignId={campaignId} />
            ) : (
              <WorldMap 
                worldData={worldData}
                currentLocation={currentLocation}
                onLocationSelect={changeLocation}
              />
            )}
          </div>
        )}
        
        {activeTab === 'inventory' && (
          <div className="h-full p-4">
            <Inventory 
              inventory={inventory}
              setInventory={setInventory}
              character={character}
            />
          </div>
        )}
      </div>

      {/* ESC pause menu — Continue · Settings · DM Notebook · Main Menu */}
      <GameEscapeMenu
        open={escMenuOpen}
        onClose={() => setEscMenuOpen(false)}
        onMainMenu={() => {
          setEscMenuOpen(false);
          startNewGame();
        }}
        onOpenDMNotebook={() => setDmNotebookOpen(true)}
      />

      {/* DM Notebook — persistent learned lessons */}
      <DMNotebookPanel
        open={dmNotebookOpen}
        onClose={() => setDmNotebookOpen(false)}
        campaignId={campaignId}
        characterId={character?.id || null}
      />
    </div>
  );
};

export default RPGGame;
