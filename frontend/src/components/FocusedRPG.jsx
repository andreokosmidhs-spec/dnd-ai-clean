import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Textarea } from './ui/textarea';
import { Card, CardContent } from './ui/card';
import { HelpCircle, Send, Loader2 } from 'lucide-react';
import AdventureLogWithDM, { IntentToggle } from './AdventureLogWithDM';
import ActionDock from './ActionDock';
import InfoDrawer from './InfoDrawer';
import CharacterSidebar from './CharacterSidebar';
import GameDetailsDrawer from './GameDetailsDrawer';
import XPBar from './XPBar';
import CheckRollPanel from './checks/CheckRollPanel.tsx';
import { useGameState } from '../contexts/GameStateContext';
import gameService from '../services/gameService';
import { calculateXpForNextLevel } from '../utils/xpCalculator';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const FocusedRPG = ({ 
  gameLog, 
  addToGameLog, 
  character, 
  currentLocation, 
  onLocationChange, 
  inventory, 
  setInventory 
}) => {
  const adventureLogRef = useRef();
  const [input, setInput] = useState('');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [infoDrawerOpen, setInfoDrawerOpen] = useState(false);
  const [pendingCheck, setPendingCheck] = useState(null);
  const [showHelp, setShowHelp] = useState(false);
  const [intentMode, setIntentMode] = useState('action');
  const [isAdventureLoading, setIsAdventureLoading] = useState(false);
  const inputRef = useRef();
  
  const { isDirty, updateCharacter, campaignId } = useGameState();
  
  // Callback to receive loading state from AdventureLog
  const handleAdventureLoadingChange = (loading) => {
    console.log('🔄 Adventure loading state changed:', loading);
    setIsAdventureLoading(loading);
  };
  
  // SAFETY NET: Continuous textarea monitoring to prevent stuck disabled state
  useEffect(() => {
    const monitorTextarea = setInterval(() => {
      const textarea = document.querySelector('textarea');
      if (textarea && textarea.disabled && !isAdventureLoading) {
        console.warn('⚠️ Textarea stuck in disabled state! Forcing restoration...');
        textarea.disabled = false;
        textarea.removeAttribute('disabled');
        textarea.style.opacity = '1';
        textarea.style.pointerEvents = 'auto';
      }
    }, 1000); // Check every second
    
    return () => clearInterval(monitorTextarea);
  }, [isAdventureLoading]);
  
  // Store adventure log messaging ref
  const [adventureMessagingRef, setAdventureMessagingRef] = useState(null);

  // ENHANCED INTERCEPTOR: Prevent loops AND execute actual dice rolls
  useEffect(() => {
    const handleGlobalClick = async (event) => {
      // Don't intercept clicks on textarea or input elements
      if (event.target.tagName === 'TEXTAREA' || 
          event.target.tagName === 'INPUT' || 
          event.target.closest('textarea') || 
          event.target.closest('input')) {
        return; // Allow normal input functionality
      }
      
      const button = event.target.closest('button');
      if (button && button.textContent) {
        const text = button.textContent.toLowerCase();
        
        // Check if this is a proceed button (more specific to avoid false positives)
        if ((text.includes('proceed') && text.includes('check')) || 
            (text.includes('check') && text.length < 50) ||
            text.includes('stealth check') ||
            text.includes('investigation check') ||
            text.includes('perception check')) {
          
          console.log('🎲 GLOBAL INTERCEPTOR: Executing dice roll for:', button.textContent);
          
          // Prevent the loop
          event.preventDefault();
          event.stopPropagation();
          
          try {
            // Determine check type from button text
            let ability = 'DEX';
            let skill = 'Stealth';
            let dc = 15;
            
            if (text.includes('stealth') || text.includes('dexterity')) {
              ability = 'DEX';
              skill = 'Stealth';
            } else if (text.includes('investigation') || text.includes('intelligence')) {
              ability = 'INT';
              skill = 'Investigation';
            } else if (text.includes('perception') || text.includes('wisdom')) {
              ability = 'WIS';
              skill = 'Perception';
            }
            
            // Build dice formula (1d20 + modifiers)
            const dexMod = Math.floor((15 - 10) / 2); // Assume DEX 15 for now
            const profBonus = 2; // Level-based proficiency
            const totalMod = dexMod + profBonus;
            const formula = `1d20+${totalMod}`;
            
            console.log('🎲 Rolling:', formula, 'for', skill, 'check, DC:', dc);
            
            // Call dice API
            const diceResponse = await fetch('https://dnd-ai-clean-test.preview.emergentagent.com/api/dice', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ formula })
            });
            
            if (!diceResponse.ok) throw new Error('Dice API failed');
            
            const rollData = await diceResponse.json();
            console.log('🎲 Roll result:', rollData);
            
            // Determine success/failure
            const outcome = rollData.total >= dc ? 'SUCCESS' : 'FAILURE';
            
            // Show roll result to user
            if (window.showToast) {
              window.showToast(`🎲 ${skill} Check: ${rollData.total} vs DC ${dc} - ${outcome}`, 
                outcome === 'SUCCESS' ? 'success' : 'error');
            }
            
            // Track failed attempts for DC escalation
            const attemptKey = `${skill.toLowerCase()}_attempt`;
            let attemptHistory = JSON.parse(localStorage.getItem('check_attempts') || '{}');
            
            if (outcome === 'FAILURE') {
              attemptHistory[attemptKey] = (attemptHistory[attemptKey] || 0) + 1;
              localStorage.setItem('check_attempts', JSON.stringify(attemptHistory));
            } else if (outcome === 'SUCCESS') {
              // Reset failed attempts on success
              if (attemptHistory[attemptKey]) {
                delete attemptHistory[attemptKey];
                localStorage.setItem('check_attempts', JSON.stringify(attemptHistory));
              }
            }
            
            // Build immediate consequence message
            const failureContext = attemptHistory[attemptKey] > 0 ? 
              ` This was my ${attemptHistory[attemptKey] + 1} attempt at this type of action.` : '';
            
            // Simplified, direct consequence request
            const outcomeMessage = `My ${skill} check result: ${rollData.total} vs DC ${dc} = ${outcome}.${failureContext} What happens immediately as a result?`;
            
            console.log('🚀 Preparing to send outcome message:', outcomeMessage);
            
            // DIRECT REACT MESSAGING: Access the adventure log component directly
            console.log('🚀 Sending outcome message via React component...');
            
            // Ensure textarea functionality is preserved with persistent monitoring
            const preserveTextareaFunction = () => {
              let attempts = 0;
              const maxAttempts = 20;
              
              const restoreInterval = setInterval(() => {
                attempts++;
                const textarea = document.querySelector('textarea');
                
                if (textarea && textarea.disabled) {
                  console.log(`🔧 Restoration attempt ${attempts}: textarea is disabled, fixing...`);
                  
                  // Aggressive restoration
                  textarea.removeAttribute('disabled');
                  textarea.disabled = false;
                  textarea.readOnly = false;
                  textarea.style.pointerEvents = 'auto';
                  textarea.style.userSelect = 'text';
                  textarea.style.opacity = '1';
                  textarea.placeholder = "What do you do next?";
                  
                  // Multiple React event triggers
                  const events = ['input', 'change', 'focus', 'blur'];
                  events.forEach(eventType => {
                    const event = new Event(eventType, { bubbles: true });
                    textarea.dispatchEvent(event);
                  });
                } else if (textarea && !textarea.disabled) {
                  console.log(`✅ Textarea restored successfully after ${attempts} attempts`);
                  clearInterval(restoreInterval);
                  return;
                }
                
                if (attempts >= maxAttempts) {
                  console.log(`⚠️ Max restoration attempts (${maxAttempts}) reached`);
                  clearInterval(restoreInterval);
                }
              }, 500); // Check every 500ms
            };
            
            if (adventureMessagingRef && adventureMessagingRef.sendPlayerMessage) {
              console.log('✅ Found adventure log ref, sending message directly');
              adventureMessagingRef.sendPlayerMessage(outcomeMessage, 'action');
              preserveTextareaFunction();
            } else {
              console.log('⚠️ No adventure log ref, using window callback approach');
              
              // Set up a callback that the AdventureLog can use
              window.sendDiceOutcome = (sendMessageFn) => {
                console.log('📤 Executing dice outcome message via callback');
                sendMessageFn(outcomeMessage, 'action');
                // Clean up the callback
                window.sendDiceOutcome = null;
                preserveTextareaFunction();
              };
              
              // Fallback DOM manipulation with proper cleanup
              setTimeout(() => {
                if (window.sendDiceOutcome) {
                  console.log('⚠️ Callback not used, trying DOM manipulation');
                  
                  const textarea = document.querySelector('textarea');
                  if (textarea && !textarea.disabled) {
                    // Store original state
                    const originalValue = textarea.value;
                    const originalReadOnly = textarea.readOnly;
                    
                    // Temporarily set message
                    textarea.value = outcomeMessage;
                    
                    // Trigger React events
                    const inputEvent = new Event('input', { bubbles: true });
                    textarea.dispatchEvent(inputEvent);
                    
                    // Send immediately
                    setTimeout(() => {
                      const enterEvent = new KeyboardEvent('keydown', {
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        bubbles: true
                      });
                      textarea.dispatchEvent(enterEvent);
                      
                      // CRITICAL: Restore normal textarea functionality (multiple attempts)
                      const restoreTextarea = () => {
                        const textarea = document.querySelector('textarea');
                        if (textarea) {
                          textarea.removeAttribute('disabled');
                          textarea.disabled = false;
                          textarea.readOnly = false;
                          textarea.value = '';
                          textarea.style.pointerEvents = 'auto';
                          textarea.style.userSelect = 'text';
                          textarea.style.opacity = '1';
                          
                          // Force React to update
                          const changeEvent = new Event('change', { bubbles: true });
                          textarea.dispatchEvent(changeEvent);
                          
                          const inputEvent = new Event('input', { bubbles: true });
                          textarea.dispatchEvent(inputEvent);
                          
                          console.log('🔧 Textarea restored:', !textarea.disabled);
                        }
                      };
                      
                      // Multiple restoration attempts
                      setTimeout(restoreTextarea, 1000);
                      setTimeout(restoreTextarea, 3000);
                      setTimeout(restoreTextarea, 5000);
                    }, 200);
                  }
                  
                  // Clean up callback
                  window.sendDiceOutcome = null;
                }
              }, 3000);
            }
            
          } catch (error) {
            console.error('❌ Dice roll execution failed:', error);
            if (window.showToast) {
              window.showToast('❌ Dice roll failed, but loop prevented', 'error');
            }
          }
          
          return false;
        }
      }
    };

    document.addEventListener('click', handleGlobalClick, true);
    return () => {
      document.removeEventListener('click', handleGlobalClick, true);
    };
  }, []);

  // Track last synced character to prevent infinite loops
  const [lastSyncedCharacter, setLastSyncedCharacter] = useState(null);

  // CRITICAL FIX: Sync character prop with GameStateContext whenever character changes
  useEffect(() => {
    if (character && character !== lastSyncedCharacter) { // Only sync if character actually changed
      console.log('🔥 CHARACTER CHANGED - SYNCING TO GAMESTATECONTEXT:');
      console.log('📝 Character from RPGGame:', character);
      console.log('🎭 Name:', character.name);
      console.log('🏛️ Background:', character.background);
      console.log('🏹 Class:', character.class);
      
      // Convert character prop to GameStateContext format
      const contextCharacterData = {
        id: character.id || `char-${Date.now()}`,
        name: character.name || 'Unknown Character',
        race: character.race || 'Human',
        class: character.class || 'Fighter',
        level: character.level || 1,
        background: character.background || 'Folk Hero',
        alignment: character.alignment || 'Neutral',
        stats: character.stats || {
          str: 10, dex: 10, con: 10, int: 10, wis: 10, cha: 10
        },
        proficiency_bonus: Math.ceil((character.level || 1) / 4) + 1,
        hp: { 
          current: character.hitPoints || 20, 
          max: character.hitPoints || 20, 
          temp: 0 
        },
        ac: character.armorClass || 10,
        speed: 30,
        spell_slots: character.spellSlots ? { 1: character.spellSlots.length } : {},
        prepared_spells: character.spells || [],
        conditions: [],
        virtues: character.virtues || [],
        flaws: character.flaws || [],
        goals: character.goals || [],
        proficiencies: character.proficiencies || [],
        inventory: [
          { id: 'item-1', name: 'Starting Gear', qty: 1, tags: ['equipment'], equipped: true, notes: 'Basic adventuring equipment' }
        ],
        gold: 25,
        active_quests: [],
        reputation: {},
        notes: `${character.background || 'Adventurer'} ready for action`
      };
      
      console.log('🚀 SYNCING CHARACTER TO GAMESTATE:', contextCharacterData);
      
      // Update character state
      updateCharacter(contextCharacterData);
      
      // Remember this character to prevent re-sync
      setLastSyncedCharacter(character);
    }
  }, [character]); // Remove updateCharacter from dependencies to prevent loop

  // Sync intent mode from AdventureLog
  useEffect(() => {
    if (adventureLogRef.current) {
      setIntentMode(adventureLogRef.current.intentMode);
    }
  }, [adventureLogRef.current?.intentMode]);

  // Store ref to sendPlayerMessage function from AdventureLogWithDM
  const sendPlayerMessageRef = useRef(null);

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Check for Ctrl+Shift+R (Reset Adventure)
      if (e.ctrlKey && e.shiftKey && e.key === 'R') {
        e.preventDefault();
        if (adventureLogRef.current && adventureLogRef.current.resetAdventure) {
          adventureLogRef.current.resetAdventure();
        }
        return;
      }

      // Don't trigger shortcuts when typing in inputs
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        // Allow Escape to blur inputs
        if (e.key === 'Escape') {
          e.target.blur();
        }
        return;
      }

      switch (e.key) {
        case '/':
          e.preventDefault();
          inputRef.current?.focus();
          break;
        case '?':
          setShowHelp(!showHelp);
          break;
        case 'c':
        case 'C':
          setSidebarCollapsed(!sidebarCollapsed);
          break;
        case 'Escape':
          setShowHelp(false);
          setInfoDrawerOpen(false);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [showHelp, sidebarCollapsed, infoDrawerOpen]);

  // DM system handles all commands now via AdventureLogWithDM

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && adventureLogRef.current && !isAdventureLoading) {
      adventureLogRef.current.sendMessage(input.trim(), intentMode);
      setInput('');
    }
  };

  const handleIntentChange = (newMode) => {
    setIntentMode(newMode);
    if (adventureLogRef.current) {
      adventureLogRef.current.setIntentMode(newMode);
    }
  };

  const handleActionSelect = (actionId) => {
    const actionCommands = {
      'look': 'I look around carefully',
      'search': 'I search the area thoroughly',
      'inventory': 'I check my inventory and equipment',
      'character': 'I review my character abilities and condition',
      'talk': 'I look for someone to talk to',
      'move': 'I look for ways to move to a new location',
      'attack': 'I prepare to engage in combat',
      'defend': 'I take a defensive stance',
      'cast': 'I prepare to cast a spell',
      'rest': 'I find a safe place to rest and recover',
      'map': 'I consult my map and surroundings',
      'wait': 'I wait and observe my surroundings'
    };

    const command = actionCommands[actionId] || actionId;
    if (adventureLogRef.current && !isAdventureLoading) {
      adventureLogRef.current.sendMessage(command);
    }
  };

  const gameContext = {
    npcs: currentLocation?.npcs || [],
    inCombat: false,
    character: character
  };

  return (
    <div className="h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 overflow-hidden">
      <div className="h-full flex">
        {/* Left Sidebar - Character (Collapsible) */}
        <div className={`transition-all duration-300 ${sidebarCollapsed ? 'w-16' : 'w-72'} flex-shrink-0`}>
          <CharacterSidebar 
            character={character}
            isCollapsed={sidebarCollapsed}
            onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          />
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden h-full">
          {/* Adventure Log with DM Integration - Fixed height with internal scroll */}
          <div className="flex-1 p-4 overflow-hidden">
            <AdventureLogWithDM 
              ref={adventureLogRef} 
              onLoadingChange={handleAdventureLoadingChange}
              onCheckRequest={(checkRequest) => {
                console.log('🎲 Check request received in FocusedRPG:', checkRequest);
                setPendingCheck(checkRequest);
              }}
            />
          </div>

          {/* XP Bar - Between narration and actions */}
          {character && (
            <div className="flex-shrink-0 px-8 py-2">
              <XPBar 
                level={character.level || 1}
                currentXp={character.experience || 0}
                xpForNextLevel={calculateXpForNextLevel(character.level || 1)}
              />
            </div>
          )}

          {/* Action Dock - Fixed at bottom */}
          <div className="flex-shrink-0">
            <ActionDock 
              onActionSelect={handleActionSelect}
              isProcessing={false}
              gameContext={gameContext}
            />
          </div>

          {/* Input Bar - Always visible at bottom */}
          <div className="flex-shrink-0 p-4 bg-black/20 border-t border-amber-600/20">
            <form onSubmit={handleSubmit} className="flex gap-3 max-w-4xl mx-auto">
              {/* Intent Toggle */}
              <IntentToggle mode={intentMode} onChange={handleIntentChange} />
              
              <div className="flex-1 relative">
                <Textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit(e);
                    }
                  }}
                  placeholder={
                    intentMode === 'dm-question'
                      ? "Ask the DM (out-of-character): rules, mechanics, lore, or clarifications"
                      : intentMode === 'say'
                      ? "What do you say? (e.g., 'We come in peace.' or 'Tell me about the ruins.')"
                      : "What do you do? (e.g., search the alley, climb the wall, draw my sword)"
                  }
                  className="min-h-[2.5rem] max-h-20 resize-none bg-gray-900/80 border-amber-600/30 
                           text-white placeholder-gray-400 focus:border-amber-400 focus:ring-1 focus:ring-amber-400"
                  disabled={isAdventureLoading}
                  rows={1}
                />
                <div className="absolute bottom-2 right-2 flex items-center gap-2">
                  <Badge variant="secondary" className="text-xs bg-gray-700 text-gray-300">
                    Alt+D/A/S • / to focus
                  </Badge>
                </div>
              </div>
              
              <div className="flex items-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowHelp(!showHelp)}
                  className="border-gray-600 text-gray-400 hover:bg-gray-600/20 h-10"
                >
                  <HelpCircle className="h-4 w-4" />
                </Button>
                
                <Button
                  type="submit"
                  disabled={!input.trim() || isAdventureLoading}
                  className="bg-amber-700 hover:bg-amber-600 text-black font-semibold h-10 px-6"
                >
                  {isAdventureLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      Send
                    </>
                  )}
                </Button>
              </div>
            </form>

            {/* Help Overlay */}
            {showHelp && (
              <Card className="absolute bottom-20 left-4 right-4 bg-black/95 border-amber-600/50 backdrop-blur-sm z-50">
                <CardContent className="p-4">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-amber-400 font-semibold">Quick Help</h3>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowHelp(false)}
                      className="text-gray-400 hover:text-white"
                    >
                      ✕
                    </Button>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <h4 className="text-white font-medium mb-2">Keyboard Shortcuts</h4>
                      <div className="space-y-1 text-gray-300">
                        <div><Badge variant="secondary" className="text-xs mr-2">1-9</Badge>Quick actions</div>
                        <div><Badge variant="secondary" className="text-xs mr-2">/</Badge>Focus input</div>
                        <div><Badge variant="secondary" className="text-xs mr-2">?</Badge>Toggle help</div>
                        <div><Badge variant="secondary" className="text-xs mr-2">C</Badge>Toggle character panel</div>
                        <div><Badge variant="secondary" className="text-xs mr-2">I</Badge>Toggle info drawer</div>
                        <div><Badge variant="secondary" className="text-xs mr-2">Esc</Badge>Close overlays</div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="text-white font-medium mb-2">Example Commands</h4>
                      <div className="space-y-1 text-gray-300 text-xs">
                        <div>• "I examine the ancient door"</div>
                        <div>• "I talk to the innkeeper about rumors"</div>
                        <div>• "I search for hidden passages"</div>
                        <div>• "I go north toward the mountains"</div>
                        <div>• "I cast detect magic"</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Info Drawer */}
      <InfoDrawer 
        character={character}
        currentLocation={currentLocation}
        inventory={inventory}
        gameLog={gameLog}
        isOpen={infoDrawerOpen}
        onOpenChange={setInfoDrawerOpen}
      />

      {/* Game State Details Drawer */}
      <GameDetailsDrawer synced={isDirty === false} />

      {/* Check Roll Panel */}
      {pendingCheck && (
        <CheckRollPanel
          checkRequest={pendingCheck}
          character={character}
          onRollComplete={async (rollResult) => {
            try {
              // Get campaign_id and character_id
              const currentCampaignId = campaignId || localStorage.getItem('game-state-campaign-id');
              const characterId = character?.id || character?.character_id || localStorage.getItem('character-id');

              console.log('🎲 Submitting roll:', {
                campaignId: currentCampaignId,
                characterId,
                rollResult,
                pendingCheck
              });

              if (!currentCampaignId || !characterId) {
                console.error('Missing campaign_id or character_id', {
                  campaignId: currentCampaignId,
                  characterId,
                  character
                });
                if (window.showToast) {
                  window.showToast('❌ Missing session information', 'error');
                }
                return;
              }

              // Call resolve_check endpoint
              console.log('📤 Calling /api/rpg_dm/resolve_check...');
              const response = await fetch(`${BACKEND_URL}/api/rpg_dm/resolve_check`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  campaign_id: currentCampaignId,
                  character_id: characterId,
                  player_roll: rollResult,
                  check_request: pendingCheck
                })
              });

              console.log('📥 Response status:', response.status);
              const data = await response.json();
              console.log('📥 Response data:', data);

              if (data.success) {
                console.log('✅ Check resolved successfully');
                
                // Add DM narration to game log
                addToGameLog({
                  type: 'dm',
                  text: data.data.narration,  // Changed from 'message' to 'text'
                  timestamp: Date.now(),
                  options: data.data.options || [],
                  resolution: data.data.resolution,
                  entity_mentions: data.data.entity_mentions || []  // Include entity mentions for clickable links
                });

                // Update character if needed
                if (data.data.player_updates) {
                  const updates = data.data.player_updates;
                  console.log('📝 Updating character:', updates);
                  if (updates.gold_gained || updates.items_gained || updates.hp !== undefined) {
                    updateCharacter(data.data.player_updates);
                  }
                }

                // Update location if changed
                if (data.data.world_state_update && data.data.world_state_update.current_location) {
                  console.log('📍 Updating location:', data.data.world_state_update.current_location);
                  onLocationChange(data.data.world_state_update.current_location);
                }

                // Clear pending check
                setPendingCheck(null);

                if (window.showToast) {
                  const outcome = data.data.resolution.outcome.replace('_', ' ');
                  const icon = data.data.resolution.success ? '✓' : '✗';
                  window.showToast(`${icon} ${outcome}`, data.data.resolution.success ? 'success' : 'error');
                }
              } else {
                console.error('❌ Check resolution failed:', data.error);
                if (window.showToast) {
                  window.showToast(`❌ ${data.error?.message || 'Check resolution failed'}`, 'error');
                }
              }
            } catch (error) {
              console.error('❌ Error resolving check:', error);
              if (window.showToast) {
                window.showToast(`❌ Network error: ${error.message}`, 'error');
              }
              // Don't clear pending check on error so user can retry
            }
          }}
          onDismiss={() => setPendingCheck(null)}
        />
      )}
    </div>
  );
};

export default FocusedRPG;