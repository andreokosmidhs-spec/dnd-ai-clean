import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { ScrollArea } from './ui/scroll-area';
import { User, Heart, Zap, Shield, Sword } from 'lucide-react';
import { mockData } from '../data/mockData';

const CharacterSheet = ({ character }) => {
  if (!character) return null;

  const getStatModifier = (stat) => {
    return Math.floor((stat - 10) / 2);
  };

  const getStatModifierString = (stat) => {
    const mod = getStatModifier(stat);
    return mod >= 0 ? `+${mod}` : `${mod}`;
  };

  const getProficiencyBonus = (level) => {
    return Math.ceil(level / 4) + 1;
  };

  return (
    <Card className="bg-black/80 border-blue-600/30 backdrop-blur-sm">
      <CardHeader className="pb-3">
        <CardTitle className="text-blue-400 text-sm flex items-center gap-2">
          <User className="h-4 w-4" />
          Character Sheet
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Basic Info */}
        <div className="space-y-2">
          <div className="text-center">
            <h3 className="text-white font-semibold text-lg">{character.name}</h3>
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
                <Badge variant="outline" className="mt-1 border-blue-400/50 text-blue-300 text-xs">
                  {displayText}
                </Badge>
              );
            })()}
          </div>
        </div>

        {/* Health & Resources */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Heart className="h-4 w-4 text-red-400" />
            <span className="text-red-400 text-sm font-medium">Hit Points</span>
          </div>
          <div className="bg-gray-800/50 p-2 rounded">
            <div className="flex justify-between items-center mb-1">
              <span className="text-white text-sm">{character.hitPoints}/{character.hitPoints}</span>
              <span className="text-gray-400 text-xs">Full Health</span>
            </div>
            <Progress value={100} className="h-2 bg-gray-700" />
          </div>
        </div>

        {/* Spell Slots (if applicable) */}
        {character.spellSlots && character.spellSlots.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-cyan-400" />
              <span className="text-cyan-400 text-sm font-medium">Spell Slots</span>
            </div>
            <div className="bg-gray-800/50 p-2 rounded">
              <div className="text-white text-sm">
                Level 1: {character.spellSlots.filter(slot => slot === 1).length} available
              </div>
            </div>
          </div>
        )}

        {/* Ability Scores */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-green-400" />
            <span className="text-green-400 text-sm font-medium">Abilities</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(character.stats).map(([stat, value]) => (
              <div key={stat} className="bg-gray-800/50 p-2 rounded text-center">
                <div className="text-gray-400 text-xs capitalize">{stat.slice(0, 3)}</div>
                <div className="text-white font-semibold">{value}</div>
                <div className="text-gray-300 text-xs">{getStatModifierString(value)}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Combat Stats */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Sword className="h-4 w-4 text-amber-400" />
            <span className="text-amber-400 text-sm font-medium">Combat</span>
          </div>
          <div className="bg-gray-800/50 p-2 rounded space-y-1">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Armor Class:</span>
              <span className="text-white">
                {10 + getStatModifier(character.stats.dexterity)} 
                {/* Base AC + Dex modifier, would be more complex with armor */}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Proficiency:</span>
              <span className="text-white">+{getProficiencyBonus(character.level)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Initiative:</span>
              <span className="text-white">{getStatModifierString(character.stats.dexterity)}</span>
            </div>
          </div>
        </div>

        {/* Traits & Features */}
        {character.traits && character.traits.length > 0 && (
          <div className="space-y-2">
            <span className="text-purple-400 text-sm font-medium">Racial Traits</span>
            <ScrollArea className="h-16">
              <div className="flex flex-wrap gap-1">
                {character.traits.map((trait, idx) => (
                  <Badge 
                    key={idx} 
                    variant="outline" 
                    className="text-xs border-purple-400/50 text-purple-300"
                  >
                    {typeof trait === 'string' ? trait : trait?.text || 'Trait'}
                  </Badge>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}

        {/* Experience */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-yellow-400 text-sm font-medium">Experience</span>
            <span className="text-gray-400 text-xs">{character.experience}/300 XP</span>
          </div>
          <Progress 
            value={(character.experience / 300) * 100} 
            className="h-2 bg-gray-700"
          />
        </div>
      </CardContent>
    </Card>
  );
};

export default CharacterSheet;