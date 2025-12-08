import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { Send, Dice6, Swords, Eye, MessageSquare, Loader2 } from 'lucide-react';
import gameService from '../services/gameService';

const GameChat = ({ gameLog, addToGameLog, character, currentLocation, onLocationChange, inventory, setInventory }) => {
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [hasGameSession, setHasGameSession] = useState(false);
  const scrollAreaRef = useRef();
  const inputRef = useRef();

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [gameLog]);

  useEffect(() => {
    // Initialize game session when character is available
    if (character && !hasGameSession) {
      initializeGameSession();
    }
  }, [character, hasGameSession]);

  const initializeGameSession = async () => {
    try {
      await gameService.startGameSession(character.id);
      setHasGameSession(true);
      addToGameLog({
        type: 'system',
        message: `Game session initialized for ${character.name}. The AI consciousness is now active...`
      });
    } catch (error) {
      console.error('Failed to initialize game session:', error);
      addToGameLog({
        type: 'system',
        message: 'Warning: Game session could not be initialized. Some features may not work properly.'
      });
    }
  };

  const processCommand = async (command) => {
    setIsProcessing(true);
    
    // Add user input to log
    addToGameLog({
      type: 'player',
      message: command
    });

    try {
      // Prepare context for AI processing
      const context = {
        location_id: currentLocation?.id || 'ravens-hollow',
        npcs: currentLocation?.npcs || [],
        current_location: currentLocation,
        character_stats: character?.stats,
        inventory_count: inventory?.length || 0
      };

      let response;

      if (hasGameSession) {
        // Use AI-powered game engine
        response = await gameService.processGameAction(command, context);
        await handleAIResponse(response);
      } else {
        // Fallback to mock responses
        await handleMockCommand(command);
      }

    } catch (error) {
      console.error('Error processing command:', error);
      addToGameLog({
        type: 'system',
        message: 'An error occurred while processing your action. Please try again.'
      });
    }

    setIsProcessing(false);
  };

  const handleAIResponse = async (response) => {
    // Handle different types of AI responses
    switch (response.type) {
      case 'dialogue':
        if (response.response.type === 'npc_dialogue') {
          addToGameLog({
            type: 'npc',
            speaker: response.response.npc_name,
            message: response.response.npc_response
          });
          
          if (response.response.relationship_change) {
            addToGameLog({
              type: 'system',
              message: `Your relationship with ${response.response.npc_name} has changed.`
            });
          }
        } else {
          addToGameLog({
            type: 'system',
            message: response.response.message
          });
        }
        break;

      case 'description':
        addToGameLog({
          type: 'system',
          message: response.response.description
        });
        
        if (response.response.investigation_needed) {
          addToGameLog({
            type: 'system',
            message: `This seems to require closer investigation. Try making a ${response.response.suggested_check} check.`
          });
        }
        break;

      case 'movement':
        if (response.response.type === 'movement') {
          addToGameLog({
            type: 'system',
            message: response.response.description
          });
          
          if (response.response.requires_check) {
            await handleMovementCheck(response.response);
          }
        } else {
          addToGameLog({
            type: 'system',
            message: response.response.message
          });
        }
        break;

      case 'combat':
        addToGameLog({
          type: 'combat',
          message: response.response.scenario
        });
        
        if (response.response.initiative_required) {
          addToGameLog({
            type: 'system',
            message: 'Combat has begun! Roll for initiative.'
          });
        }
        break;

      case 'search':
        addToGameLog({
          type: 'system',
          message: response.response.results
        });
        
        if (response.response.ability_check_needed) {
          await handleAbilityCheck(response.response.suggested_ability, 'searching');
        }
        break;

      default:
        addToGameLog({
          type: 'system',
          message: response.response.message || 'The world responds to your action...'
        });
    }
  };

  const handleMovementCheck = async (movementData) => {
    try {
      const checkResult = await gameService.triggerAbilityCheck(
        movementData.check_type,
        `traveling ${movementData.direction}`
      );
      
      addToGameLog({
        type: 'dice',
        message: `${movementData.check_type.charAt(0).toUpperCase() + movementData.check_type.slice(1)} Check: ${checkResult.ability_check.roll} + ${checkResult.ability_check.base_modifier} = ${checkResult.ability_check.total}`,
        success: checkResult.ability_check.success
      });
      
      addToGameLog({
        type: 'system',
        message: checkResult.narrative
      });
      
    } catch (error) {
      console.error('Error with movement check:', error);
      addToGameLog({
        type: 'system',
        message: 'You manage to travel, though the journey is more challenging than expected.'
      });
    }
  };

  const handleAbilityCheck = async (ability, context) => {
    try {
      const checkResult = await gameService.triggerAbilityCheck(ability, context);
      
      addToGameLog({
        type: 'dice',
        message: `${ability.charAt(0).toUpperCase() + ability.slice(1)} Check: ${checkResult.ability_check.roll} + ${checkResult.ability_check.base_modifier} = ${checkResult.ability_check.total} (DC ${checkResult.ability_check.dc})`,
        success: checkResult.ability_check.success
      });
      
      addToGameLog({
        type: checkResult.ability_check.success ? 'success' : 'system',
        message: checkResult.narrative
      });
      
      return checkResult.ability_check.success;
      
    } catch (error) {
      console.error('Error with ability check:', error);
      return false;
    }
  };

  const handleMockCommand = async (command) => {
    // Fallback mock responses (same as before)
    const lowerCommand = command.toLowerCase().trim();
    
    if (lowerCommand.includes('look') || lowerCommand.includes('examine')) {
      addToGameLog({
        type: 'system',
        message: `You are in ${currentLocation.name}. ${currentLocation.description}`
      });
    } else if (lowerCommand.includes('talk') || lowerCommand.includes('speak')) {
      const npcNames = currentLocation.npcs?.map(npc => npc.name.toLowerCase()) || [];
      const foundNpc = npcNames.find(name => command.includes(name.split(' ')[0].toLowerCase()));
      
      if (foundNpc) {
        const npc = currentLocation.npcs.find(npc => npc.name.toLowerCase().includes(foundNpc));
        const responses = [
          `${npc.name} looks at you with interest. "Greetings, traveler. What brings you to ${currentLocation.name}?"`,
          `${npc.name} nods respectfully. "I've heard tales of your arrival. Perhaps we can help each other."`,
        ];
        
        addToGameLog({
          type: 'npc',
          speaker: npc.name,
          message: responses[Math.floor(Math.random() * responses.length)]
        });
      } else {
        addToGameLog({
          type: 'system',
          message: "There's no one here by that name to talk to."
        });
      }
    } else {
      addToGameLog({
        type: 'system',
        message: "I don't understand that command. Try 'look', 'talk to [NPC]', 'go [direction]', or 'search'."
      });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isProcessing) {
      processCommand(input.trim());
      setInput('');
    }
  };

  const getMessageStyle = (entry) => {
    switch (entry.type) {
      case 'player':
        return 'bg-blue-600/20 border-l-4 border-blue-400 text-blue-100';
      case 'npc':
        return 'bg-purple-600/20 border-l-4 border-purple-400 text-purple-100';
      case 'system':
        return 'bg-gray-600/20 border-l-4 border-gray-400 text-gray-100';
      case 'dice':
        return `${entry.success ? 'bg-green-600/20 border-l-4 border-green-400 text-green-100' : 'bg-red-600/20 border-l-4 border-red-400 text-red-100'}`;
      case 'combat':
        return 'bg-red-600/20 border-l-4 border-red-400 text-red-100';
      case 'success':
        return 'bg-yellow-600/20 border-l-4 border-yellow-400 text-yellow-100';
      default:
        return 'bg-gray-600/20 border-l-4 border-gray-400 text-gray-100';
    }
  };

  const getMessageIcon = (entry) => {
    switch (entry.type) {
      case 'dice':
        return <Dice6 className="h-4 w-4" />;
      case 'combat':
        return <Swords className="h-4 w-4" />;
      case 'npc':
        return <MessageSquare className="h-4 w-4" />;
      default:
        return <Eye className="h-4 w-4" />;
    }
  };

  return (
    <Card className="h-full bg-black/90 border-amber-600/30 backdrop-blur-sm flex flex-col w-full max-w-full overflow-hidden">
      <CardHeader className="pb-3 flex-shrink-0">
        <CardTitle className="text-amber-400 text-lg flex items-center gap-2 break-words">
          <MessageSquare className="h-5 w-5 flex-shrink-0" />
          <span className="truncate">Adventure Log</span>
          {hasGameSession && (
            <Badge variant="outline" className="text-xs border-green-400/50 text-green-300 ml-auto flex-shrink-0">
              AI Active
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col gap-4 overflow-hidden w-full max-w-full">
        {/* Game Log */}
        <ScrollArea className="flex-1 h-[400px] w-full" ref={scrollAreaRef}>
          <div className="space-y-3 pr-4 w-full">
            {gameLog.map((entry, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg ${getMessageStyle(entry)} animate-in slide-in-from-left-5 duration-300 w-full max-w-full`}
              >
                <div className="flex items-start gap-2 w-full">
                  <div className="flex-shrink-0">
                    {getMessageIcon(entry)}
                  </div>
                  <div className="flex-1 min-w-0 w-full">
                    {entry.speaker && (
                      <div className="font-semibold text-sm mb-1 break-words">{entry.speaker}:</div>
                    )}
                    <div className="text-sm leading-relaxed break-words whitespace-pre-wrap overflow-wrap-anywhere word-break-break-word">
                      {entry.message}
                    </div>
                    {entry.timestamp && (
                      <div className="text-xs opacity-60 mt-1 break-words">
                        {new Date(entry.timestamp).toLocaleTimeString()}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {isProcessing && (
              <div className="flex items-center gap-2 text-amber-400 p-3 w-full max-w-full">
                <Loader2 className="animate-spin h-4 w-4 flex-shrink-0" />
                <span className="text-sm break-words">
                  {hasGameSession ? 'AI is thinking...' : 'Processing your action...'}
                </span>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Quick Actions */}
        <div className="flex flex-wrap gap-2 mb-4 w-full">
          <Button
            size="sm"
            variant="outline"
            onClick={() => processCommand('look around')}
            className="border-amber-600/50 text-amber-300 hover:bg-amber-600/20 text-xs flex-shrink-0"
            disabled={isProcessing}
          >
            Look Around
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => processCommand('search')}
            className="border-blue-600/50 text-blue-300 hover:bg-blue-600/20 text-xs flex-shrink-0"
            disabled={isProcessing}
          >
            Search
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => processCommand('inventory')}
            className="border-green-600/50 text-green-300 hover:bg-green-600/20 text-xs flex-shrink-0"
            disabled={isProcessing}
          >
            Inventory
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => processCommand('stats')}
            className="border-purple-600/50 text-purple-300 hover:bg-purple-600/20 text-xs flex-shrink-0"
            disabled={isProcessing}
          >
            Character
          </Button>
        </div>

        {/* Input Area */}
        <form onSubmit={handleSubmit} className="flex gap-2 w-full">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={hasGameSession ? 
              "What do you want to do? (AI will understand natural language)" : 
              "What do you want to do? (e.g., 'look around', 'talk to Gareth', 'go north')"
            }
            className="flex-1 bg-gray-800/50 border-amber-600/30 text-white placeholder-gray-400 focus:border-amber-400 min-w-0"
            disabled={isProcessing}
          />
          <Button
            type="submit"
            disabled={!input.trim() || isProcessing}
            className="bg-amber-700 hover:bg-amber-600 text-black font-semibold flex-shrink-0"
          >
            {isProcessing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </form>

        {/* Help Text */}
        <div className="text-xs text-gray-400 text-center break-words px-2">
          {hasGameSession ? 
            "AI understands natural language. Try: \"I want to talk to the blacksmith about rare metals\" or \"Search for hidden passages\"" :
            "Try commands like: \"look around\", \"talk to [NPC name]\", \"go north\", \"search\", \"use [item]\", \"attack\""
          }
        </div>
      </CardContent>
    </Card>
  );
};

export default GameChat;