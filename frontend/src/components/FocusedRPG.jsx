import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Textarea } from './ui/textarea';
import { Card, CardContent } from './ui/card';
import { HelpCircle, Send, Loader2 } from 'lucide-react';
import AdventureLogWithDM, { IntentToggle } from './AdventureLogWithDM';
import CharacterSidebar from './CharacterSidebar';
import XPBar from './XPBar';
import CheckRollPanel from './checks/CheckRollPanel.tsx';
import { useGameState } from '../contexts/GameStateContext';
import gameService from '../services/gameService';
import { calculateXpForNextLevel } from '../utils/xpCalculator';
import { TargetModeProvider, useTargetMode } from '../contexts/TargetModeContext';
import { TargetModeBanner } from './TargetModeBanner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const FocusedRPGInner = ({
  gameLog,
  addToGameLog,
  character,
  setCharacter,
  currentLocation,
  onLocationChange,
  inventory,
  setInventory,
  onCombatStart,
}) => {
  const adventureLogRef = useRef();
  const [input, setInput] = useState('');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [pendingCheck, setPendingCheck] = useState(null);

  const handlePortraitRefresh = (newPortraitDataUrl) => {
    if (setCharacter) setCharacter(prev => ({ ...prev, portrait: newPortraitDataUrl }));
  };
  const [showHelp, setShowHelp] = useState(false);
  const [intentMode, setIntentMode] = useState('action');
  const [isAdventureLoading, setIsAdventureLoading] = useState(false);
  const inputRef = useRef();

  const { isDirty, updateCharacter, campaignId, characterState } = useGameState();

  const handleAdventureLoadingChange = (loading) => {
    setIsAdventureLoading(loading);
  };

  // Safety net: prevent textarea from getting stuck disabled
  useEffect(() => {
    const monitorTextarea = setInterval(() => {
      const textarea = document.querySelector('textarea');
      if (textarea && textarea.disabled && !isAdventureLoading) {
        textarea.disabled = false;
        textarea.removeAttribute('disabled');
        textarea.style.opacity = '1';
        textarea.style.pointerEvents = 'auto';
      }
    }, 1000);
    return () => clearInterval(monitorTextarea);
  }, [isAdventureLoading]);

  // Track last synced character to prevent infinite loops
  const [lastSyncedCharacter, setLastSyncedCharacter] = useState(null);

  // Sync character prop with GameStateContext whenever character changes
  useEffect(() => {
    if (character && character !== lastSyncedCharacter) {
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
      updateCharacter(contextCharacterData);
      setLastSyncedCharacter(character);
    }
  }, [character]); // eslint-disable-line

  // Sync intent mode from AdventureLog
  useEffect(() => {
    if (adventureLogRef.current) {
      setIntentMode(adventureLogRef.current.intentMode);
    }
  }, [adventureLogRef.current?.intentMode]);

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'R') {
        e.preventDefault();
        if (adventureLogRef.current && adventureLogRef.current.resetAdventure) {
          adventureLogRef.current.resetAdventure();
        }
        return;
      }
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        if (e.key === 'Escape') e.target.blur();
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
          break;
        default:
          break;
      }
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [showHelp, sidebarCollapsed]);

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

  return (
    <div className="h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 overflow-hidden">
      <TargetModeBanner />
      <div className="h-full flex">
        {/* Left Sidebar - Character (Collapsible) */}
        <div className={`transition-all duration-300 ${sidebarCollapsed ? 'w-16' : 'w-72'} flex-shrink-0`}>
          <CharacterSidebar
            character={character}
            isCollapsed={sidebarCollapsed}
            onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
            onPortraitRefresh={handlePortraitRefresh}
          />
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden h-full">
          {/* Adventure Log */}
          <div className="flex-1 p-4 overflow-hidden">
            <AdventureLogWithDM
              ref={adventureLogRef}
              onLoadingChange={handleAdventureLoadingChange}
              onCheckRequest={(checkRequest) => {
                setPendingCheck(checkRequest);
              }}
              onCombatStart={onCombatStart}
            />
          </div>

          {/* XP Bar */}
          {(character || characterState?.id) && (
            <div className="flex-shrink-0 px-8 py-2">
              <XPBar
                level={characterState?.level ?? character?.level ?? 1}
                currentXp={
                  characterState?.current_xp ??
                  character?.current_xp ??
                  character?.experience ??
                  0
                }
                xpForNextLevel={
                  characterState?.xp_to_next ??
                  calculateXpForNextLevel(characterState?.level ?? character?.level ?? 1)
                }
              />
            </div>
          )}

          {/* Input Bar */}
          <div className="flex-shrink-0 p-4 bg-black/20 border-t border-amber-600/20">
            <form onSubmit={handleSubmit} className="flex gap-3 max-w-4xl mx-auto">
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
                        <div><Badge variant="secondary" className="text-xs mr-2">/</Badge>Focus input</div>
                        <div><Badge variant="secondary" className="text-xs mr-2">?</Badge>Toggle help</div>
                        <div><Badge variant="secondary" className="text-xs mr-2">C</Badge>Toggle character panel</div>
                        <div><Badge variant="secondary" className="text-xs mr-2">Esc</Badge>Close overlays</div>
                        <div><Badge variant="secondary" className="text-xs mr-2">Alt+D/A/S</Badge>Switch intent mode</div>
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

      {/* Check Roll Panel */}
      {pendingCheck && (
        <CheckRollPanel
          checkRequest={pendingCheck}
          character={character}
          onRollComplete={async (rollResult) => {
            try {
              const currentCampaignId = campaignId || localStorage.getItem('game-state-campaign-id');
              const characterId = character?.id || character?.character_id || localStorage.getItem('character-id');

              if (!currentCampaignId || !characterId) {
                if (window.showToast) window.showToast('❌ Missing session information', 'error');
                return;
              }

              const response = await fetch(`${BACKEND_URL}/api/rpg_dm/resolve_check`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  campaign_id: currentCampaignId,
                  character_id: characterId,
                  player_roll: rollResult,
                  check_request: pendingCheck
                })
              });

              const data = await response.json();

              if (data.success) {
                addToGameLog({
                  type: 'dm',
                  text: data.data.narration,
                  timestamp: Date.now(),
                  options: data.data.options || [],
                  resolution: data.data.resolution,
                  entity_mentions: data.data.entity_mentions || []
                });

                if (data.data.player_updates) {
                  const updates = data.data.player_updates;
                  if (updates.gold_gained || updates.items_gained || updates.hp !== undefined) {
                    updateCharacter(data.data.player_updates);
                  }
                }

                if (data.data.world_state_update?.current_location) {
                  onLocationChange(data.data.world_state_update.current_location);
                }

                setPendingCheck(null);

                if (window.showToast) {
                  const outcome = data.data.resolution.outcome.replace('_', ' ');
                  const icon = data.data.resolution.success ? '✓' : '✗';
                  window.showToast(`${icon} ${outcome}`, data.data.resolution.success ? 'success' : 'error');
                }
              } else {
                if (window.showToast) {
                  window.showToast(`❌ ${data.error?.message || 'Check resolution failed'}`, 'error');
                }
              }
            } catch (error) {
              if (window.showToast) {
                window.showToast(`❌ Network error: ${error.message}`, 'error');
              }
            }
          }}
          onDismiss={() => setPendingCheck(null)}
        />
      )}
    </div>
  );
};

const FocusedRPG = (props) => (
  <TargetModeProvider>
    <FocusedRPGInner {...props} />
  </TargetModeProvider>
);

export default FocusedRPG;
