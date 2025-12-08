import React, { useState, useRef, useEffect, useImperativeHandle, forwardRef } from 'react';
import { Card, CardContent } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Dice6, MessageSquare, Loader2, User, Sparkles, Volume2, X, BookOpen } from 'lucide-react';
import { useGameState } from '../contexts/GameStateContext';
// CheckRequestCard and RollResultCard removed - CheckRollPanel handles all rolls now
import NarrationAudioPlayer from './NarrationAudioPlayer';
import NPCMentionHighlighter from './NPCMentionHighlighter';
import { EntityNarrationParser } from './EntityLink';
import { EntityQuickInspect } from './EntityQuickInspect';
import { CampaignLogPanel } from './CampaignLogPanel';
import CombatHUD from './CombatHUD';
import WorldInfoPanel from './WorldInfoPanel';
import QuestLogPanel from './QuestLogPanel';
import DefeatModal from './DefeatModal';
import { getCheckOutcome, getAbilityModifier, isProficient } from '../utils/dndMechanics';
import { useTTS } from '../hooks/useTTS';
import sessionManager from '../state/SessionManager';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AdventureLogWithDM = forwardRef(({ onLoadingChange, ...props }, ref) => {
  // Get the entire context object to ensure fresh reads
  const gameStateContext = useGameState();
  const {
    sessionId,
    setSessionId,
    campaignId,
    worldBlueprint,
    buildActionPayload,
    worldState,
    updateWorld,
    updateCharacter: updateCharContext
  } = gameStateContext;
  
  const [messages, setMessages] = useState([]);
  const [currentOptions, setCurrentOptions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [intentMode, setIntentMode] = useState('action');
  const [pendingCheck, setPendingCheck] = useState(null);
  const [combatState, setCombatState] = useState(null);
  const [isCombatActive, setIsCombatActive] = useState(false);
  const [quests, setQuests] = useState([]);
  const [showDefeatModal, setShowDefeatModal] = useState(false);
  const [defeatInfo, setDefeatInfo] = useState(null);
  const [selectedNpc, setSelectedNpc] = useState(null);
  const [showIntro, setShowIntro] = useState(false);
  
  // Entity Profile Panel state
  const [selectedEntity, setSelectedEntity] = useState(null);
  
  // Campaign Log Panel state
  const [showCampaignLog, setShowCampaignLog] = useState(false);
  
  // TTS Hook
  const { 
    audioRef, 
    isLoading: isTTSLoading, 
    isTTSEnabled, 
    generateSpeech, 
    toggleTTS 
  } = useTTS();
  
  const scrollRef = useRef();
  const introStartedRef = useRef(false);
  
  // Notify parent of loading state changes
  useEffect(() => {
    if (onLoadingChange) {
      onLoadingChange(isLoading);
    }
  }, [isLoading, onLoadingChange]);

  // DUNGEON FORGE: Use new action endpoint
  const apiEndpoint = `${BACKEND_URL}/api/rpg_dm/action`;
  const diceEndpoint = `${BACKEND_URL}/api/dice`;

  // Auto-scroll to bottom (with message count instead of array reference)
  const messageCount = messages.length;
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messageCount]);

  // Initialize session and load messages
  useEffect(() => {
    const storedIntent = localStorage.getItem('dm-intent-mode');
    if (storedIntent) setIntentMode(storedIntent);
    
    // Load messages and options from localStorage (DIRECT)
    const storedMessages = localStorage.getItem(`dm-log-messages-${sessionId}`);
    const storedOptions = localStorage.getItem(`dm-log-options-${sessionId}`);
    
    // Load messages if they exist (regardless of intro played flag)
    if (sessionId && storedMessages) {
      try {
        const parsed = JSON.parse(storedMessages);
        console.log(`📜 Loaded ${parsed.length} messages from localStorage for session:`, sessionId);
        setMessages(parsed);
      } catch (error) {
        console.error('Failed to parse stored messages:', error);
      }
    }
    
    if (sessionId && storedOptions) {
      try {
        const parsedOptions = JSON.parse(storedOptions);
        setCurrentOptions(parsedOptions);
      } catch (error) {
        console.error('Failed to parse stored options:', error);
      }
    }
  }, [sessionId, setSessionId]);
  
  // Auto-load intro on first game load
  useEffect(() => {
    const introPlayed = localStorage.getItem('dm-intro-played');
    
    // Only load intro if we have all required data
    if (
      campaignId && 
      worldBlueprint && 
      !introPlayed && 
      messages.length === 0 && 
      !introStartedRef.current
    ) {
      console.log('🎬 Auto-loading intro for new campaign');
      // Small delay to ensure all data is loaded
      setTimeout(() => {
        startCinematicIntro();
      }, 500);
    }
  }, [campaignId, worldBlueprint, messages.length]);

  // Save messages whenever they change (DIRECT localStorage)
  useEffect(() => {
    if (messages.length > 0 && sessionId) {
      // Trim to last 200 messages to prevent localStorage overflow
      const trimmed = messages.slice(-200);
      localStorage.setItem(`dm-log-messages-${sessionId}`, JSON.stringify(trimmed));
    }
  }, [messages.length, sessionId]);

  // Save options whenever they change (DIRECT localStorage)
  useEffect(() => {
    if (currentOptions.length > 0 && sessionId) {
      localStorage.setItem(`dm-log-options-${sessionId}`, JSON.stringify(currentOptions));
    }
  }, [currentOptions, sessionId]);

  // Keyboard shortcuts for intent toggle
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.altKey && e.key === 'd') {
        e.preventDefault();
        setIntentMode('dm-question');
      } else if (e.altKey && e.key === 'a') {
        e.preventDefault();
        setIntentMode('action');
      } else if (e.altKey && e.key === 's') {
        e.preventDefault();
        setIntentMode('say');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Generate TTS for a specific message
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

  const generateAudioForMessage = async (messageIndex) => {
    const message = messages[messageIndex];
    if (!message || message.type !== 'dm' || message.audioUrl) {
      return;
    }

    setIsLoading(true);

    try {
      const audioUrl = await generateSpeech(message.text, 'onyx', false);
      
      // Update message in local state
      const updatedMessages = [...messages];
      updatedMessages[messageIndex] = { ...message, audioUrl, isGeneratingAudio: false };
      setMessages(updatedMessages);
    } catch (err) {
      console.error('Failed to generate audio:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const startCinematicIntro = async () => {
    console.log('🎬 Checking for intro...');
    
    if (introStartedRef.current) {
      console.log('⏭️ Intro already played');
      return;
    }
    
    introStartedRef.current = true;
    setIsLoading(true);
    
    try {
      // CRITICAL: Check if intro already exists in localStorage with entity_mentions
      // This prevents overwriting the properly formatted intro from RPGGame
      const storedMessages = localStorage.getItem(`dm-log-messages-${sessionId}`);
      if (storedMessages) {
        try {
          const parsed = JSON.parse(storedMessages);
          if (parsed.length > 0 && parsed[0].text) {
            console.log('✅ Intro already in localStorage with', parsed[0].entity_mentions?.length || 0, 'entity mentions');
            console.log('⏭️ Using stored intro instead of worldBlueprint.intro');
            setMessages(parsed);
            localStorage.setItem('dm-intro-played', '1');
            setIsLoading(false);
            return;
          }
        } catch (e) {
          console.warn('Failed to parse stored messages:', e);
        }
      }
      
      // Safety check: ensure worldBlueprint and intro exist
      if (!worldBlueprint) {
        console.warn('⚠️ worldBlueprint not loaded yet');
        localStorage.setItem('dm-intro-played', '1');
        return;
      }
      
      const intro = worldBlueprint.intro;
      
      // Use extractNarration to safely handle any response structure
      const cleanIntro = extractNarration(intro);
      
      if (!cleanIntro || cleanIntro.trim().length === 0) {
        console.warn('⚠️ No valid intro found in worldBlueprint');
        localStorage.setItem('dm-intro-played', '1');
        return;
      }
      
      // Intro is valid, display it (FALLBACK PATH - should rarely be used)
      console.log('⚠️ Loading intro from worldBlueprint (no entity_mentions):', cleanIntro.substring(0, Math.min(100, cleanIntro.length)) + '...');
      
      // Add intro as first message
      const introMessage = {
        type: 'dm',
        text: cleanIntro,
        timestamp: Date.now(),
        isIntro: true,
        entity_mentions: [] // Empty array - this is fallback path
      };
      
      setMessages([introMessage]);
      
      // Mark intro as played
      localStorage.setItem('dm-intro-played', '1');
      
      // Generate TTS if enabled
      if (isTTSEnabled && generateSpeech) {
        try {
          const audioUrl = await generateSpeech(cleanIntro, 'onyx', false);
          if (audioUrl) {
            const updatedIntroMessage = { ...introMessage, audioUrl };
            setMessages([updatedIntroMessage]);
          }
        } catch (err) {
          console.error('Failed to generate intro audio:', err);
        }
      }
    } catch (error) {
      console.error('❌ Failed to load intro:', error);
      // Mark as played to avoid infinite retry
      localStorage.setItem('dm-intro-played', '1');
    } finally {
      setIsLoading(false);
      setShowIntro(false);
    }
  };

  const sendToAPI = async (payload, isCinematic = false) => {
    const startTime = performance.now();
    console.log('📤 Sending to DM API:', payload);

    setIsLoading(true);

    try {
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const duration = Math.round(performance.now() - startTime);
      console.log(`⏱️ DM responded in ${duration}ms`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const response_envelope = await response.json();
      console.log('📥 DUNGEON FORGE Response:', response_envelope);

      // Extract data from standard envelope {success, data, error}
      const data = response_envelope.data || response_envelope;
      
      // DUNGEON FORGE: Handle world_state_update
      if (data.world_state_update && Object.keys(data.world_state_update).length > 0) {
        console.log('🗺️ WORLD STATE UPDATE:', data.world_state_update);
        updateWorld(data.world_state_update);
      }

      // P3: Update quests from world_state
      if (data.world_state_update && data.world_state_update.quests) {
        setQuests(data.world_state_update.quests);
      }

      // P3: Handle player_updates (XP, level-ups, defeat)
      if (data.player_updates && Object.keys(data.player_updates).length > 0) {
        console.log('✨ PLAYER UPDATES:', data.player_updates);
        
        // Update character stats
        if (data.player_updates.xp_gained) {
          updateCharContext({ 
            current_xp: (gameStateContext.characterState?.current_xp || 0) + data.player_updates.xp_gained 
          });
        }
        
        // XP gained notification
        if (data.player_updates.xp_gained > 0) {
          const xpReason = data.player_updates.xp_reason || '';
          const xpMsg = xpReason 
            ? `+${data.player_updates.xp_gained} XP: ${xpReason}`
            : `+${data.player_updates.xp_gained} XP`;
          if (window.showToast) {
            window.showToast(xpMsg, 'success');
          }
        }
        
        // Level up notifications
        if (data.player_updates.level_up_events && data.player_updates.level_up_events.length > 0) {
          for (const event of data.player_updates.level_up_events) {
            const level = event.split(':')[1];
            const levelMsg = `🎉 LEVEL UP! You are now level ${level}!`;
            if (window.showToast) {
              window.showToast(levelMsg, 'info');
            }
          }
        }
        
        // Defeat handled - show modal
        if (data.player_updates.defeat_handled) {
          setShowDefeatModal(true);
          setDefeatInfo({
            currentHP: data.player_updates.hp_restored,
            maxHP: gameStateContext.characterState?.hp?.max || gameStateContext.characterState?.max_hp || 10,
            injuryCount: data.player_updates.injury_count,
            xpPenalty: data.player_updates.xp_penalty || 0
          });
          
          // Update character HP
          if (data.player_updates.hp_restored !== undefined) {
            updateCharContext({ 
              hp: { ...gameStateContext.characterState?.hp, current: data.player_updates.hp_restored } 
            });
          }
          
          // P3.5: Show XP penalty toast if any
          if (data.player_updates.xp_penalty > 0 && window.showToast) {
            window.showToast(`-${data.player_updates.xp_penalty} XP`, 'error');
          }
        }
      }

      // DUNGEON FORGE: Handle check_request (v3.1 compatibility: also handles requested_check)
      const checkRequest = data.check_request || data.requested_check;
      if (checkRequest) {
        console.log('🎯 NEW CHECK REQUEST:', checkRequest);
        console.log('🎯 Check request received:', checkRequest);
        console.log('🎯 DC value:', checkRequest.dc);
        setPendingCheck(checkRequest);
        
        // Notify parent component (FocusedRPG)
        if (props.onCheckRequest) {
          props.onCheckRequest(checkRequest);
        }
      }

      // DUNGEON FORGE: Handle combat
      if (data.combat_started) {
        console.log('⚔️ Combat started!');
        setIsCombatActive(true);
        setCombatState({ isActive: true, combatId: `combat-${Date.now()}` });
      }
      
      if (data.combat_active && data.combat_state) {
        console.log('⚔️ Combat continues...');
        setIsCombatActive(true);
        setCombatState({ isActive: true, ...data.combat_state });
      }
      
      if (data.combat_over) {
        console.log('⚔️ Combat ended:', data.outcome);
        setIsCombatActive(false);
        setCombatState({ 
          isActive: false, 
          outcome: data.outcome,
          combatId: null,
          participants: [],
          turnOrder: [],
          currentTurnIndex: 0
        });
      }

      // Add DM message to log
      if (data.narration) {
        console.log('💬 Received DM narration:', data.narration.substring(0, 100) + '...');
        const msgId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const dmMsg = {
          id: msgId,
          type: 'dm',
          text: data.narration,
          options: data.options || [],
          checkRequest: data.check_request || data.requested_check || null,
          npcMentions: data.npc_mentions || [],
          entity_mentions: data.entity_mentions || [],
          timestamp: Date.now(),
          isCinematic: isCinematic,
          audioUrl: null,
          isGeneratingAudio: false
        };
        
        console.log('📝 Adding DM message to state, current message count:', messages.length);
        setMessages(prev => {
          const updated = [...prev, dmMsg];
          console.log('📝 New message count will be:', updated.length);
          return updated;
        });

        // Auto-generate TTS if enabled (non-blocking)
        if (isTTSEnabled && !isCinematic) {
          setTimeout(async () => {
            try {
              const audioUrl = await generateSpeech(data.narration, 'onyx', true);
              setMessages(prev => prev.map(msg => 
                msg.id === msgId ? { ...msg, audioUrl } : msg
              ));
            } catch (err) {
              console.error('TTS auto-generation failed:', err);
            }
          }, 100);
        }

        if (isCinematic) {
          setShowIntro(false);
        }
        
        setCurrentOptions(data.options || []);
      }

    } catch (error) {
      console.error('❌ DM API Error:', error);
      const errorMsg = {
        id: `error-${Date.now()}`,
        type: 'error',
        text: `Connection error: ${error.message}`,
        timestamp: Date.now(),
        retry: true
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // buildActionPayload is now provided by GameStateContext

  const sendPlayerMessage = async (playerMessage, messageType = null, checkResult = null) => {
    if (!playerMessage.trim() || !sessionId) return;

    const actualType = messageType || intentMode || 'action';

    // Add player message to log with intent
    const msgId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const playerMsg = {
      id: msgId,
      type: 'player',
      text: playerMessage,
      messageType: actualType,
      timestamp: Date.now()
    };
    setMessages(prev => [...prev, playerMsg]);
    setCurrentOptions([]);

    // DUNGEON FORGE: Use buildActionPayload from context
    const actionPayload = buildActionPayload(playerMessage, checkResult);
    
    if (!actionPayload) {
      console.error('❌ Cannot send action: missing campaign_id or character_id');
      const errorMsg = {
        id: `error-${Date.now()}`,
        type: 'error',
        text: 'Cannot send action: Campaign not initialized. Please create a new character.',
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, errorMsg]);
      return;
    }

    console.log('🚀 Sending DUNGEON FORGE action payload:', actionPayload);
    await sendToAPI(actionPayload);
  };

  const handleOptionClick = (option) => {
    console.log('🎯 OPTION CLICKED:', option);
    
    // AGGRESSIVE PROCEED DETECTION
    const isProceedAction = (
      option.toLowerCase().includes('proceed') || 
      option.toLowerCase().includes('stealth check') ||
      option.toLowerCase().includes('investigation check') ||
      option.toLowerCase().includes('perception check') ||
      option.toLowerCase().includes('athletics check') ||
      option.toLowerCase().includes('dexterity') ||
      option.toLowerCase().includes('strength') ||
      option.toLowerCase().includes('constitution') ||
      option.toLowerCase().includes('intelligence') ||
      option.toLowerCase().includes('wisdom') ||
      option.toLowerCase().includes('charisma') ||
      (option.toLowerCase().includes('check') && option.length < 50) ||
      option.toLowerCase().includes('roll')
    );
    
    // OLD: Auto-roll logic removed - CheckRollPanel handles all rolls now
    // if (isProceedAction && pendingCheck) {
    //   console.log('🎲 DETECTED CHECK CONFIRMATION - EXECUTING DICE ROLL');
    //   ...
    // }
    
    console.log('📤 SENDING AS REGULAR MESSAGE');
    sendPlayerMessage(option, 'action');
  };

  const getCheckFormula = (checkRequest) => {
    if (!checkRequest) {
      console.error('No checkRequest provided to getCheckFormula');
      return '1d20+0';
    }
    
    const { mode = 'normal', situational_bonus = 0, ability = 'DEX', skill = 'Stealth' } = checkRequest;
    
    console.log('🎲 Building formula for:', checkRequest);
    console.log('🎲 Character stats:', gameStateContext.characterState?.stats);
    console.log('🎲 Character proficiencies:', gameStateContext.characterState?.proficiencies);
    
    // Calculate modifier from character state and skill
    const abilityModifier = getAbilityModifier(gameStateContext.characterState?.stats, ability.toLowerCase()) || 0;
    const proficiencyBonus = isProficient(gameStateContext.characterState?.proficiencies, skill) ? (gameStateContext.characterState?.proficiency_bonus || 2) : 0;
    const totalModifier = abilityModifier + proficiencyBonus + situational_bonus;
    
    console.log('🎲 Ability modifier:', abilityModifier);
    console.log('🎲 Proficiency bonus:', proficiencyBonus);
    console.log('🎲 Total modifier:', totalModifier);
    
    // Build formula based on advantage/disadvantage
    if (mode === 'advantage') {
      return `2d20kh1${totalModifier >= 0 ? '+' : ''}${totalModifier}`;
    } else if (mode === 'disadvantage') {
      return `2d20kl1${totalModifier >= 0 ? '+' : ''}${totalModifier}`;
    } else {
      return `1d20${totalModifier >= 0 ? '+' : ''}${totalModifier}`;
    }
  };

  const handleRetry = (messageIndex) => {
    const allMsgs = messages.slice(0, messageIndex);
    const lastPlayerMsg = allMsgs.reverse().find(m => m.type === 'player');
    if (lastPlayerMsg) {
      sendPlayerMessage(lastPlayerMsg.text);
    }
  };

  // OLD: handleDiceRoll function removed - CheckRollPanel handles all rolls now
  /*
  const handleDiceRoll = async ({ mode, formula, d20, modifier, total }) => {
    console.log('🎲 Processing dice roll:', { mode, formula, d20, modifier, total });
    
    if (!pendingCheck) {
      console.error('❌ No pending check found for dice roll');
      const errorMsg = {
        id: `error-${Date.now()}`,
        type: 'error',
        text: 'No active ability check to roll for. Please request a check first.',
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, errorMsg]);
      return;
    }
    
    if (mode === 'auto') {
      try {
        const response = await fetch(diceEndpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ formula })
        });

        if (!response.ok) {
          throw new Error(`Dice API error: ${response.status}`);
        }

        const responseData = await response.json();
        console.log('🎲 Dice API response:', responseData);
        
        // Extract data from API wrapper {success, data, error}
        const rollData = responseData.data || responseData;
        console.log('🎲 Extracted roll data:', rollData);
        console.log('🎲 Modifier from API:', rollData.modifier);

        // Add roll result message
        const msgId = `roll-${Date.now()}`;
        const rollMsg = {
          id: msgId,
          type: 'roll_result',
          rollData: rollData,
          checkRequest: pendingCheck,
          timestamp: Date.now()
        };
        setMessages(prev => [...prev, rollMsg]);
        
        // Process check outcome
        const outcome = getCheckOutcome(rollData.total, pendingCheck.dc);
        console.log(`📊 Check outcome: ${outcome} (${rollData.total} vs DC ${pendingCheck.dc})`);
        
        // Send outcome to DM for continued narration
        const outcomeMessage = `I rolled ${rollData.total} for the ${pendingCheck.ability} check (DC ${pendingCheck.dc}). Result: ${outcome}.`;
        console.log('🎯 Building outcome payload with message:', outcomeMessage);
        const outcomePayload = buildActionPayload(outcomeMessage, rollData.total);
        console.log('📦 Outcome payload:', outcomePayload);
        
        if (!outcomePayload) {
          console.error('❌ Failed to build outcome payload!');
          const errorMsg = {
            id: `error-${Date.now()}`,
            type: 'error',
            text: 'Failed to send check result to DM. Campaign may not be initialized.',
            timestamp: Date.now()
          };
          setMessages(prev => [...prev, errorMsg]);
          return;
        }
        
        // Clear pending check and continue story
        setPendingCheck(null);
        console.log('🚀 Sending outcome to DM API...');
        await sendToAPI(outcomePayload);
        console.log('✅ DM response should now be visible');
        
      } catch (error) {
        console.error('❌ Dice roll error:', error);
        const errorMsg = {
          id: `error-${Date.now()}`,
          type: 'error',
          text: `Dice roll failed: ${error.message}`,
          timestamp: Date.now()
        };
        setMessages(prev => [...prev, errorMsg]);
      }
    } else {
      // Handle manual roll
      const rollData = {
        formula,
        rolls: [d20],
        kept: [d20],
        sum_kept: d20,
        modifier,
        total
      };

      const msgId = `roll-${Date.now()}`;
      const rollMsg = {
        id: msgId,
        type: 'roll_result',
        rollData: rollData,
        checkRequest: pendingCheck,
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, rollMsg]);
      
      const outcome = getCheckOutcome(total, pendingCheck.dc);
      console.log(`📊 Manual check outcome: ${outcome} (${total} vs DC ${pendingCheck.dc})`);
      
      const outcomeMessage = `I rolled ${total} for the ${pendingCheck.ability} check (DC ${pendingCheck.dc}). Result: ${outcome}.`;
      const outcomePayload = buildActionPayload(outcomeMessage, total);
      
      setPendingCheck(null);
      await sendToAPI(outcomePayload);
    }
  };
  */

  const resetAdventureHandler = () => {
    console.log('🔄 Resetting adventure...');
    
    setMessages([]);
    setPendingCheck(null);
    setIsCombatActive(false);
    setCombatState({ 
      isActive: false, 
      combatId: null, 
      participants: [], 
      turnOrder: [], 
      currentTurnIndex: 0 
    });
    setShowIntro(false);
    setCurrentOptions([]);
    setShowDefeatModal(false);
    setDefeatInfo(null);
    
    if (window.showToast) {
      window.showToast('🔄 Adventure reset!', 'success');
    }
  };

  // Expose sendPlayerMessage to parent via ref
  useImperativeHandle(ref, () => ({
    sendMessage: sendPlayerMessage,
    isLoading: isLoading,
    intentMode: intentMode || 'action',
    setIntentMode: (mode) => setIntentMode(mode),
    resetAdventure: resetAdventureHandler
  }));

  const formatMessage = (message) => {
    if (typeof message !== 'string') return message;
    
    // Handle both actual newlines and literal \n sequences
    // First, replace literal \n\n with actual newlines
    let cleanedMessage = message.replace(/\\n\\n/g, '\n\n').replace(/\\n/g, '\n');
    
    // Split on double newlines to create paragraphs
    const paragraphs = cleanedMessage.split(/\n\s*\n/).filter(p => p.trim());
    
    // If only one paragraph, just return it
    if (paragraphs.length <= 1) return cleanedMessage;
    
    // Return paragraphs with proper spacing
    return paragraphs.map((paragraph, idx) => (
      <p key={idx} className={idx > 0 ? 'mt-3' : ''}>
        {paragraph.split('\n').map((line, lineIdx) => (
          <React.Fragment key={lineIdx}>
            {lineIdx > 0 && <br />}
            {line}
          </React.Fragment>
        ))}
      </p>
    ));
  };

  return (
    <Card className="h-full bg-black/95 border-amber-600/30 backdrop-blur-sm overflow-hidden flex flex-col">
      <CardContent className="p-0 flex-1 flex flex-col overflow-hidden">
        
        {/* Header */}
        <div className="p-3 border-b border-amber-600/20 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h2 className="text-amber-400 font-semibold text-sm flex items-center gap-2">
              <Dice6 className="h-4 w-4" />
              Adventure Log
            </h2>
            <div className="flex items-center gap-2">
              {/* TTS Toggle */}
              <Button
                onClick={toggleTTS}
                variant="ghost"
                size="sm"
                className={`h-7 px-2 ${isTTSEnabled ? 'bg-purple-600/20 text-purple-400' : 'text-gray-400'}`}
                title={isTTSEnabled ? 'Disable narration audio' : 'Enable narration audio'}
              >
                <Volume2 className="h-4 w-4 mr-1" />
                <span className="text-xs">TTS</span>
              </Button>
            </div>
          </div>
        </div>

        {/* Selected NPC Indicator */}
        {selectedNpc && intentMode === 'say' && (
          <div className="px-3 py-2 bg-purple-900/30 border-b border-purple-600/30 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-purple-400" />
              <span className="text-purple-300 text-sm">
                Talking to: <span className="font-semibold">{selectedNpc.name}</span>
              </span>
              {selectedNpc.role === 'primary' && (
                <Badge variant="outline" className="text-xs border-purple-400/50 text-purple-300">Primary</Badge>
              )}
            </div>
            <Button
              onClick={() => setSelectedNpc(null)}
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 text-purple-400 hover:text-purple-200"
              title="Clear NPC selection"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Combat HUD - Show when combat is active */}
        {isCombatActive && combatState && (
          <div className="px-3 pt-3">
            <CombatHUD characterState={gameStateContext.characterState} combatState={combatState} />
          </div>
        )}

        {/* World Info Panel - Collapsible */}
        {worldBlueprint && (
          <div className="px-3 pt-3">
            <WorldInfoPanel 
              worldBlueprint={worldBlueprint} 
              currentLocation={worldState?.current_location || worldState?.location}
            />
          </div>
        )}

        {/* Quest Log Panel - P3 */}
        {quests.length > 0 && (
          <div className="px-3 pt-3">
            <QuestLogPanel quests={quests} />
          </div>
        )}

        {/* Campaign Log Button - Only show when campaignId exists */}
        {campaignId && (
          <div className="px-3 pt-3">
            <Button
              onClick={() => setShowCampaignLog(true)}
              variant="outline"
              className="w-full bg-orange-600/10 border-orange-600/30 hover:bg-orange-600/20 text-orange-400 hover:text-orange-300"
            >
              <BookOpen className="h-4 w-4 mr-2" />
              Campaign Log
            </Button>
          </div>
        )}

        {/* Messages */}
        <ScrollArea className="flex-1" ref={scrollRef}>
          <div className="p-3 space-y-3">
            {messages.map((entry, idx) => (
              <div key={idx}>
                {/* DM Message */}
                {entry.type === 'dm' && (
                  <div className={`p-4 rounded-lg ${
                    entry.isCinematic 
                      ? 'bg-gradient-to-r from-violet-600/30 to-purple-600/30 border-2 border-violet-400/50' 
                      : 'bg-violet-600/20 border-l-4 border-violet-400'
                  } animate-in slide-in-from-left-5 duration-300`}>
                    <div className="flex items-start gap-3">
                      <Dice6 className="h-5 w-5 text-violet-400 flex-shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-violet-400 font-semibold text-sm">
                            {entry.isCinematic ? '🎭 The Adventure Begins' : 'Dungeon Master'}
                          </span>
                          {entry.isCinematic && (
                            <Sparkles className="h-3 w-3 text-violet-400 animate-pulse" />
                          )}
                          {/* TTS Audio Player - Available for ALL DM messages including cinematic */}
                          <div className="ml-auto flex items-center gap-2">
                            <NarrationAudioPlayer
                              text={entry.text}
                              audioUrl={entry.audioUrl}
                              onGenerateAudio={() => generateAudioForMessage(idx)}
                              isGenerating={entry.isGeneratingAudio}
                            />
                            {/* Regenerate Intro Button (only for first cinematic message) */}
                            {entry.isCinematic && idx === 0 && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={startCinematicIntro}
                                disabled={isLoading}
                                className="text-xs border-violet-400/50 text-violet-300 hover:bg-violet-600/20 hover:text-violet-200"
                              >
                                {isLoading ? (
                                  <>
                                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                    Generating...
                                  </>
                                ) : (
                                  <>
                                    <Sparkles className="h-3 w-3 mr-1" />
                                    Regenerate Intro
                                  </>
                                )}
                              </Button>
                            )}
                          </div>
                        </div>
                        <div className="text-violet-50 text-sm leading-relaxed">
                          {/* Entity Links: Parse entity markup and make clickable */}
                          {entry.entity_mentions && entry.entity_mentions.length > 0 ? (
                            <EntityNarrationParser
                              text={entry.text}
                              entityMentions={entry.entity_mentions}
                              onEntityClick={(entity) => setSelectedEntity(entity)}
                            />
                          ) : entry.npcMentions && entry.npcMentions.length > 0 ? (
                            <NPCMentionHighlighter
                              text={entry.text}
                              npcMentions={entry.npcMentions}
                              onNPCClick={(npc) => setSelectedNpc(npc)}
                              selectedNpcId={selectedNpc?.id}
                            />
                          ) : (
                            formatMessage(entry.text)
                          )}
                        </div>
                        <div className="text-xs opacity-60 mt-2">
                          {new Date(entry.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Player Message */}
                {entry.type === 'player' && (
                  <div className="p-4 rounded-lg bg-cyan-600/20 border-l-4 border-cyan-400 ml-8 animate-in slide-in-from-right-5 duration-300">
                    <div className="flex items-start gap-3">
                      <User className="h-4 w-4 text-cyan-400 flex-shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <div className="text-cyan-400 font-semibold text-sm">You</div>
                          <Badge 
                            variant="outline" 
                            className={`text-xs px-2 ${
                              entry.messageType === 'say' 
                                ? 'border-purple-400/50 text-purple-300 bg-purple-600/10' 
                                : entry.messageType === 'dm-question'
                                ? 'border-blue-400/50 text-blue-300 bg-blue-600/10'
                                : 'border-cyan-400/50 text-cyan-300 bg-cyan-600/10'
                            }`}
                          >
                            {entry.messageType === 'say' ? '💬 Say' : entry.messageType === 'dm-question' ? '🎲 DM?' : '⚔️ Action'}
                          </Badge>
                        </div>
                        <div className="text-cyan-50 text-sm leading-relaxed">
                          {entry.messageType === 'say' ? (
                            <span className="italic">"{entry.text}"</span>
                          ) : entry.messageType === 'dm-question' ? (
                            <span className="text-blue-200">[Out of Character] {entry.text}</span>
                          ) : (
                            entry.text
                          )}
                        </div>
                        <div className="text-xs opacity-60 mt-2">
                          {new Date(entry.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Error Message */}
                {entry.type === 'error' && (
                  <div className="p-4 rounded-lg bg-red-600/20 border-l-4 border-red-400 animate-in fade-in duration-300">
                    <div className="flex items-start gap-3">
                      <div className="w-2 h-2 bg-red-400 rounded-full flex-shrink-0 mt-2"></div>
                      <div className="flex-1 min-w-0">
                        <div className="text-red-400 font-semibold text-sm mb-1">Connection Error</div>
                        <div className="text-red-50 text-sm">{entry.text}</div>
                        {entry.retry && (
                          <Button
                            onClick={() => handleRetry(idx)}
                            size="sm"
                            className="mt-2 bg-red-700 hover:bg-red-600 text-white"
                          >
                            Retry
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Roll Result Card */}
                {/* Roll results are now handled by CheckRollPanel, not inline */}

                {/* Check Summary (non-interactive - CheckRollPanel handles rolls) */}
                {entry.type === 'dm' && entry.checkRequest && idx === messages.length - 1 && !showIntro && (
                  <div className="ml-8 mt-3">
                    <div className="bg-gradient-to-r from-amber-600/10 to-yellow-600/10 border-2 border-amber-400/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Dice6 className="h-5 w-5 text-amber-400" />
                        <p className="text-amber-400 font-bold">
                          Ability Check: {entry.checkRequest.skill || entry.checkRequest.ability}
                        </p>
                      </div>
                      <div className="space-y-1 text-sm">
                        <p className="text-white">
                          <span className="text-gray-400">DC:</span> <span className="font-bold text-amber-300">{entry.checkRequest.dc}</span>
                        </p>
                        {entry.checkRequest.reason && (
                          <p className="text-gray-400 text-xs mt-2">{entry.checkRequest.reason}</p>
                        )}
                        <p className="text-amber-400/60 text-xs mt-3 italic">
                          Use the check panel to roll →
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Options (rendered after the last DM message if available and no check request card) */}
                {entry.type === 'dm' && idx === messages.length - 1 && (currentOptions || []).length > 0 && !showIntro && !entry.checkRequest && (
                  <div className="ml-8 mt-3 animate-in slide-in-from-bottom-5 duration-500">
                    <div className="text-amber-400 text-xs font-medium mb-2 flex items-center gap-2">
                      <MessageSquare className="h-3 w-3" />
                      Choose your action:
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {(currentOptions || []).map((option, optIdx) => (
                        <Button
                          key={optIdx}
                          onClick={() => handleOptionClick(option)}
                          disabled={isLoading}
                          size="sm"
                          className="bg-amber-700/80 hover:bg-amber-600 text-black font-medium text-xs h-auto p-2 text-left whitespace-normal hover:scale-105 transition-transform"
                        >
                          <span className="mr-1 text-amber-900 font-bold">{optIdx + 1}.</span>
                          {option}
                        </Button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
            
            {/* Loading State */}
            {isLoading && (
              <div className="flex items-center gap-3 text-violet-400 p-4">
                <Loader2 className="animate-spin h-4 w-4 flex-shrink-0" />
                <span className="text-sm">
                  {showIntro ? 'The Dungeon Master weaves your tale...' : 'The Dungeon Master considers your action...'}
                </span>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
      
      {/* Hidden Audio Element for TTS Playback */}
      <audio ref={audioRef} style={{ display: 'none' }} />
      
      {/* P3: Defeat Modal */}
      {showDefeatModal && defeatInfo && (
        <DefeatModal
          isOpen={showDefeatModal}
          onContinue={() => {
            setShowDefeatModal(false);
            setDefeatInfo(null);
          }}
          playerName={gameStateContext.characterState?.name}
          currentHP={defeatInfo.currentHP}
          maxHP={defeatInfo.maxHP}
          injuryCount={defeatInfo.injuryCount}
          xpPenalty={defeatInfo.xpPenalty || 0}
        />
      )}
      
      {/* Entity Quick Inspect Panel - Opens when clicking entity links */}
      {selectedEntity && (
        <EntityQuickInspect
          entity={selectedEntity}
          campaignId={campaignId}
          characterId={gameStateContext.characterState?.id}
          onClose={() => setSelectedEntity(null)}
        />
      )}
      
      {/* Campaign Log Panel - Full-page modal */}
      {showCampaignLog && (
        <CampaignLogPanel
          campaignId={campaignId}
          characterId={gameStateContext.characterState?.id}
          onClose={() => setShowCampaignLog(false)}
        />
      )}
    </Card>
  );
});

AdventureLogWithDM.displayName = 'AdventureLogWithDM';

// Export Intent Toggle Component for use in FocusedRPG
export const IntentToggle = ({ mode, onChange }) => {
  return (
    <div className="flex items-center gap-1 bg-gray-900/80 border border-amber-600/30 rounded-lg p-1">
      <Button
        type="button"
        size="sm"
        onClick={() => onChange('dm-question')}
        className={`h-8 px-3 text-xs font-medium transition-all ${
          mode === 'dm-question'
            ? 'bg-blue-700 text-white hover:bg-blue-600'
            : 'bg-transparent text-gray-400 hover:text-white hover:bg-gray-700/50'
        }`}
        title="Ask the DM (out-of-character) (Alt+D)"
      >
        🎲 DM?
      </Button>
      <Button
        type="button"
        size="sm"
        onClick={() => onChange('action')}
        className={`h-8 px-3 text-xs font-medium transition-all ${
          mode === 'action'
            ? 'bg-amber-700 text-black hover:bg-amber-600'
            : 'bg-transparent text-gray-400 hover:text-white hover:bg-gray-700/50'
        }`}
        title="Perform an action (Alt+A)"
      >
        ⚔️ Action
      </Button>
      <Button
        type="button"
        size="sm"
        onClick={() => onChange('say')}
        className={`h-8 px-3 text-xs font-medium transition-all ${
          mode === 'say'
            ? 'bg-purple-700 text-white hover:bg-purple-600'
            : 'bg-transparent text-gray-400 hover:text-white hover:bg-gray-700/50'
        }`}
        title="Speak in-character (Alt+S)"
      >
        💬 Say
      </Button>
    </div>
  );
};

export default AdventureLogWithDM;