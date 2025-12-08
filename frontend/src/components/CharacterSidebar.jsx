import React, { useState } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip';
import { Progress } from './ui/progress';
import { 
  ChevronRight, 
  ChevronLeft, 
  User, 
  Heart, 
  Zap, 
  Shield,
  TrendingUp
} from 'lucide-react';
import { mockData } from '../data/mockData';

const CharacterSidebar = ({ character, isCollapsed, onToggle }) => {
  const [showMore, setShowMore] = useState({});

  if (!character) return null;

  const getStatModifier = (stat) => {
    return Math.floor((stat - 10) / 2);
  };

  const getStatModifierString = (stat) => {
    const mod = getStatModifier(stat);
    return mod >= 0 ? `+${mod}` : `${mod}`;
  };

  const toggleShowMore = (section) => {
    setShowMore(prev => ({ ...prev, [section]: !prev[section] }));
  };

  if (isCollapsed) {
    return (
      <TooltipProvider>
        <div className="w-16 bg-black/80 border-r border-amber-600/20 backdrop-blur-sm h-full flex flex-col">
          <div className="p-2 space-y-3 flex-1">
            {/* Expand Button */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onToggle}
                  className="w-full h-10 p-2 text-amber-400 hover:bg-amber-600/20"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">
                <p>Expand Character Panel (C)</p>
              </TooltipContent>
            </Tooltip>

            {/* Quick Stats Icons */}
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="p-2 bg-red-600/20 rounded-lg text-center">
                  <Heart className="h-4 w-4 text-red-400 mx-auto mb-1" />
                  <div className="text-xs text-white font-medium">
                    {character.hitPoints}
                  </div>
                </div>
              </TooltipTrigger>
              <TooltipContent side="right">
                <p>Hit Points: {character.hitPoints}/{character.hitPoints}</p>
              </TooltipContent>
            </Tooltip>

            {character.spellSlots && character.spellSlots.length > 0 && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="p-2 bg-blue-600/20 rounded-lg text-center">
                    <Zap className="h-4 w-4 text-blue-400 mx-auto mb-1" />
                    <div className="text-xs text-white font-medium">
                      {character.spellSlots.length}
                    </div>
                  </div>
                </TooltipTrigger>
                <TooltipContent side="right">
                  <p>Spell Slots: {character.spellSlots.length} available</p>
                </TooltipContent>
              </Tooltip>
            )}

            <Tooltip>
              <TooltipTrigger asChild>
                <div className="p-2 bg-green-600/20 rounded-lg text-center">
                  <TrendingUp className="h-4 w-4 text-green-400 mx-auto mb-1" />
                  <div className="text-xs text-white font-medium">
                    {character.level}
                  </div>
                </div>
              </TooltipTrigger>
              <TooltipContent side="right">
                <p>Level {character.level} {character.race} {character.class}</p>
              </TooltipContent>
            </Tooltip>
          </div>
        </div>
      </TooltipProvider>
    );
  }

  return (
    <Card className="w-72 bg-black/90 border-amber-600/30 backdrop-blur-sm h-full overflow-hidden">
      <CardContent className="p-0 h-full flex flex-col">
        {/* Header */}
        <div className="p-3 border-b border-amber-600/20 flex items-center justify-between">
          <h2 className="text-amber-400 font-semibold text-sm flex items-center gap-2">
            <User className="h-4 w-4" />
            Character
          </h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggle}
            className="h-6 w-6 p-1 text-amber-400 hover:bg-amber-600/20"
          >
            <ChevronLeft className="h-3 w-3" />
          </Button>
        </div>

        {/* Character Info */}
        <div className="p-3 space-y-4 flex-1 overflow-y-auto">
          {/* Basic Info */}
          <div className="bg-gray-900/50 rounded-lg p-3">
            <h3 className="text-white font-semibold text-lg mb-1">{character.name}</h3>
            <p className="text-gray-400 text-sm">
              Level {character.level} {character.race} {character.class}
            </p>
            {character.background && (() => {
              const bg = mockData.backgrounds.find(b => b.name === character.background);
              let displayText = character.background;
              
              if (bg?.variants && character.backgroundVariantKey) {
                const variant = bg.variants[character.backgroundVariantKey];
                if (variant && variant.label !== character.background) {
                  displayText = `${character.background} (${variant.label})`;
                }
              }
              
              return (
                <Badge variant="outline" className="mt-2 border-blue-400/50 text-blue-300 text-xs">
                  {displayText}
                </Badge>
              );
            })()}
          </div>

          {/* Health */}
          <div className="bg-gray-900/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Heart className="h-4 w-4 text-red-400" />
              <span className="text-red-400 text-sm font-medium">Health</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Hit Points</span>
                <span className="text-white">{character.hitPoints}/{character.hitPoints}</span>
              </div>
              <Progress value={100} className="h-2 bg-gray-700" />
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">AC</span>
                <span className="text-white">
                  {10 + getStatModifier(character.stats?.dexterity || 10)}
                </span>
              </div>
            </div>
          </div>

          {/* Spell Slots */}
          {character.spellSlots && character.spellSlots.length > 0 && (
            <div className="bg-gray-900/50 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="h-4 w-4 text-cyan-400" />
                <span className="text-cyan-400 text-sm font-medium">Spell Slots</span>
              </div>
              <div className="text-white text-sm">
                Level 1: {character.spellSlots.length} available
              </div>
            </div>
          )}

          {/* Ability Scores */}
          <div className="bg-gray-900/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="h-4 w-4 text-green-400" />
              <span className="text-green-400 text-sm font-medium">Abilities</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {character.stats && Object.entries(character.stats).map(([stat, value]) => (
                <div key={stat} className="bg-gray-800/50 p-2 rounded text-center">
                  <div className="text-gray-400 text-xs capitalize">{stat.slice(0, 3)}</div>
                  <div className="text-white font-semibold text-sm">{value}</div>
                  <div className="text-gray-300 text-xs">{getStatModifierString(value)}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Role Play */}
          <div className="bg-gray-900/50 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-purple-400 text-sm font-medium">Role Play</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleShowMore('roleplay')}
                className="h-6 px-2 text-xs text-purple-400 hover:bg-purple-600/20"
              >
                {showMore.roleplay ? 'Show Less' : 'Show More'}
              </Button>
            </div>
            
            {/* Guiding Ideal (Aspiration) */}
            {character.aspiration && character.aspiration.goal && (
              <div className="mb-3">
                <span className="text-xs text-gray-400 font-semibold block mb-1">Guiding Ideal</span>
                <p className="text-xs text-yellow-300 font-semibold">{character.aspiration.goal}</p>
                {showMore.roleplay && character.aspiration.motivation && (
                  <p className="text-xs text-gray-400 mt-1">{character.aspiration.motivation}</p>
                )}
              </div>
            )}
            
            {/* Racial Traits */}
            {character.traits && character.traits.length > 0 && (
              <div className="mb-3">
                <span className="text-xs text-gray-400 font-semibold block mb-1">Racial Traits</span>
                <div className="flex flex-wrap gap-1">
                  {(showMore.roleplay ? character.traits : character.traits.slice(0, 2)).map((trait, idx) => (
                    <Badge 
                      key={idx} 
                      variant="outline" 
                      className="text-xs border-purple-400/50 text-purple-300"
                    >
                      {typeof trait === 'string' ? trait : trait?.text || 'Trait'}
                    </Badge>
                  ))}
                  {!showMore.roleplay && character.traits.length > 2 && (
                    <Badge variant="outline" className="text-xs border-gray-400/50 text-gray-400">
                      +{character.traits.length - 2} more
                    </Badge>
                  )}
                </div>
              </div>
            )}
            
            {/* Ideal */}
            {character.ideals && character.ideals.length > 0 && character.ideals[0]?.principle && (
              <div className="mb-3">
                <span className="text-xs text-gray-400 font-semibold block mb-1">Ideal</span>
                <p className="text-xs text-purple-200">{character.ideals[0].principle}</p>
                {showMore.roleplay && character.ideals[0].inspiration && (
                  <p className="text-xs text-gray-400 mt-1">{character.ideals[0].inspiration}</p>
                )}
              </div>
            )}
            
            {/* Bond */}
            {character.bonds && character.bonds.length > 0 && character.bonds[0]?.person_or_cause && (
              <div className="mb-3">
                <span className="text-xs text-gray-400 font-semibold block mb-1">Bond</span>
                <p className="text-xs text-purple-200">{character.bonds[0].person_or_cause}</p>
              </div>
            )}
            
            {/* Flaw */}
            {character.flaws_detailed && character.flaws_detailed.length > 0 && character.flaws_detailed[0]?.habit && (
              <div>
                <span className="text-xs text-gray-400 font-semibold block mb-1">Flaw</span>
                <p className="text-xs text-purple-200">{character.flaws_detailed[0].habit}</p>
                {showMore.roleplay && character.flaws_detailed[0].interference && (
                  <p className="text-xs text-gray-400 mt-1">{character.flaws_detailed[0].interference}</p>
                )}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default CharacterSidebar;