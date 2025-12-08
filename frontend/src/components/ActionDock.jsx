import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { Input } from './ui/input';
import { 
  Eye, 
  Search, 
  Package, 
  User, 
  MoreHorizontal, 
  Compass, 
  MessageSquare,
  Sword,
  Shield,
  Zap,
  Map,
  Clock,
  Heart
} from 'lucide-react';

const ActionDock = ({ onActionSelect, isProcessing, gameContext }) => {
  const [moreOpen, setMoreOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Define all available actions
  const allActions = [
    { id: 'look', label: 'Look Around', icon: Eye, category: 'exploration', hotkey: '1' },
    { id: 'search', label: 'Search', icon: Search, category: 'exploration', hotkey: '2' },
    { id: 'inventory', label: 'Inventory', icon: Package, category: 'character', hotkey: '3' },
    { id: 'character', label: 'Character', icon: User, category: 'character', hotkey: '4' },
    { id: 'talk', label: 'Talk', icon: MessageSquare, category: 'social', hotkey: '5', contextual: true },
    { id: 'move', label: 'Move', icon: Compass, category: 'exploration', hotkey: '6' },
    { id: 'attack', label: 'Attack', icon: Sword, category: 'combat', hotkey: '7', contextual: true },
    { id: 'defend', label: 'Defend', icon: Shield, category: 'combat', hotkey: '8', contextual: true },
    { id: 'cast', label: 'Cast Spell', icon: Zap, category: 'magic', hotkey: '9', contextual: true },
    { id: 'rest', label: 'Rest', icon: Heart, category: 'character' },
    { id: 'map', label: 'Map', icon: Map, category: 'exploration' },
    { id: 'wait', label: 'Wait', icon: Clock, category: 'time' },
  ];

  // Determine primary actions based on context
  const getPrimaryActions = () => {
    const base = ['look', 'search', 'inventory', 'character'];
    const contextual = [];

    // Add contextual actions based on game state
    if (gameContext?.npcs?.length > 0) {
      contextual.push('talk');
    }
    if (gameContext?.inCombat) {
      contextual.push('attack', 'defend');
    }
    if (gameContext?.character?.spellSlots?.length > 0) {
      contextual.push('cast');
    }

    // Combine base + contextual, limit to 5 total
    const primary = [...base, ...contextual].slice(0, 5);
    return allActions.filter(action => primary.includes(action.id));
  };

  const getMoreActions = () => {
    const primaryIds = getPrimaryActions().map(a => a.id);
    return allActions.filter(action => !primaryIds.includes(action.id));
  };

  const filteredMoreActions = getMoreActions().filter(action =>
    action.label.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Don't trigger if typing in input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      
      const num = parseInt(e.key);
      if (num >= 1 && num <= 9) {
        const primaryActions = getPrimaryActions();
        const action = primaryActions[num - 1];
        if (action) {
          onActionSelect(action.id);
        }
      }
    };

    window.addEventListener('keypress', handleKeyPress);
    return () => window.removeEventListener('keypress', handleKeyPress);
  }, [onActionSelect, gameContext]);

  const handleActionClick = (actionId) => {
    onActionSelect(actionId);
    setMoreOpen(false);
  };

  const ActionChip = ({ action, showHotkey = false }) => {
    const IconComponent = action.icon;
    
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleActionClick(action.id)}
        disabled={isProcessing}
        className="action-chip relative flex items-center gap-2 px-3 py-2 h-auto min-w-0 
                   bg-gray-900/50 border-amber-600/30 text-amber-300 hover:bg-amber-600/20 
                   hover:border-amber-400 transition-all duration-200 text-xs
                   focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400"
      >
        <IconComponent className="h-3.5 w-3.5 flex-shrink-0" />
        <span className="truncate font-medium">{action.label}</span>
        {showHotkey && action.hotkey && (
          <Badge 
            variant="secondary" 
            className="absolute -top-1 -right-1 h-4 w-4 p-0 text-xs bg-amber-600 text-black font-bold"
          >
            {action.hotkey}
          </Badge>
        )}
      </Button>
    );
  };

  return (
    <div className="action-dock flex items-center justify-center gap-2 p-3 bg-black/20 border-t border-amber-600/20">
      <div className="flex items-center gap-2 flex-wrap justify-center max-w-full">
        {/* Primary Actions */}
        {getPrimaryActions().map((action) => (
          <ActionChip key={action.id} action={action} showHotkey />
        ))}

        {/* More Actions Popover */}
        <Popover open={moreOpen} onOpenChange={setMoreOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className="action-chip flex items-center gap-2 px-3 py-2 h-auto
                         bg-gray-900/50 border-gray-600/30 text-gray-300 hover:bg-gray-600/20 
                         hover:border-gray-400 transition-all duration-200 text-xs"
            >
              <MoreHorizontal className="h-3.5 w-3.5" />
              <span className="font-medium">More</span>
            </Button>
          </PopoverTrigger>
          <PopoverContent 
            className="w-64 p-3 bg-gray-900/95 border-amber-600/30 backdrop-blur-sm"
            align="center"
          >
            <div className="space-y-3">
              <div>
                <Input
                  placeholder="Search actions..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="h-8 text-xs bg-gray-800/50 border-amber-600/30"
                />
              </div>
              
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {filteredMoreActions.map((action) => (
                  <Button
                    key={action.id}
                    variant="ghost"
                    size="sm"
                    onClick={() => handleActionClick(action.id)}
                    className="w-full justify-start gap-2 h-8 px-2 text-xs text-gray-300 hover:text-white hover:bg-amber-600/20"
                  >
                    <action.icon className="h-3.5 w-3.5" />
                    {action.label}
                  </Button>
                ))}
                
                {filteredMoreActions.length === 0 && (
                  <p className="text-gray-400 text-xs text-center py-2">
                    No actions found
                  </p>
                )}
              </div>
            </div>
          </PopoverContent>
        </Popover>
      </div>
    </div>
  );
};

export default ActionDock;