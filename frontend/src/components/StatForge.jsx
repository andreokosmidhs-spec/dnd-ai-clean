import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Dice6, Flame, Sparkles, Zap } from 'lucide-react';

const ABILITIES = [
  { key: 'strength', name: 'Strength', short: 'STR', description: 'Physical power and athletic ability' },
  { key: 'dexterity', name: 'Dexterity', short: 'DEX', description: 'Agility, reflexes, and hand-eye coordination' },
  { key: 'constitution', name: 'Constitution', short: 'CON', description: 'Health, stamina, and vital force' },
  { key: 'intelligence', name: 'Intelligence', short: 'INT', description: 'Reasoning ability and memory' },
  { key: 'wisdom', name: 'Wisdom', short: 'WIS', description: 'Awareness, insight, and intuition' },
  { key: 'charisma', name: 'Charisma', short: 'CHA', description: 'Force of personality and leadership' }
];

const StatForge = ({ onComplete, character, setCharacter }) => {
  const [statPool, setStatPool] = useState([]);
  const [assignments, setAssignments] = useState({
    strength: null,
    dexterity: null,
    constitution: null,
    intelligence: null,
    wisdom: null,
    charisma: null
  });
  const [selectedStat, setSelectedStat] = useState(null);
  const [isRolling, setIsRolling] = useState(false);
  const [showCompletionEffect, setShowCompletionEffect] = useState(false);

  // Generate a single stat using 4d6 drop lowest
  const roll4d6DropLowest = () => {
    const rolls = Array.from({ length: 4 }, () => Math.floor(Math.random() * 6) + 1);
    rolls.sort((a, b) => b - a); // Sort descending
    return rolls.slice(0, 3).reduce((sum, roll) => sum + roll, 0); // Take top 3
  };

  // Generate complete stat array
  const generateStatArray = () => {
    const stats = [];
    for (let i = 0; i < 6; i++) {
      stats.push(roll4d6DropLowest());
    }
    return stats.sort((a, b) => b - a);
  };

  // Initialize stats on component mount
  useEffect(() => {
    const initialStats = generateStatArray();
    console.log('Generated stats:', initialStats); // Debug log
    console.log('Character racial_asi:', character.racial_asi); // Debug racial bonuses
    console.log('Character race:', character.race, 'subrace:', character.subrace); // Debug race
    setStatPool(initialStats);
  }, []);

  // Check if all abilities are assigned
  const isComplete = () => {
    return Object.values(assignments).every(val => val !== null);
  };

  // Reroll all stats
  const rerollStats = async () => {
    setIsRolling(true);
    setSelectedStat(null);
    
    // Reset assignments
    setAssignments({
      strength: null,
      dexterity: null,
      constitution: null,
      intelligence: null,
      wisdom: null,
      charisma: null
    });

    // Animate the rolling
    setTimeout(() => {
      const newStats = generateStatArray();
      console.log('Rerolled stats:', newStats); // Debug log
      setStatPool(newStats);
      setIsRolling(false);
    }, 1000);
  };

  // Assign a stat to an ability
  const assignStat = (stat, abilityKey) => {
    if (!stat || assignments[abilityKey] !== null) return;
    
    // Find the index of this exact stat value (in case of duplicates)
    const statIndex = statPool.findIndex(s => s === stat);
    if (statIndex === -1) return;
    
    setAssignments(prev => ({ ...prev, [abilityKey]: stat }));
    
    // Remove only the first occurrence of this stat
    setStatPool(prev => {
      const newPool = [...prev];
      newPool.splice(statIndex, 1);
      return newPool;
    });
    
    setSelectedStat(null);
  };

  // Unassign a stat from an ability
  const unassignStat = (abilityKey) => {
    const stat = assignments[abilityKey];
    if (!stat) return;
    
    // Add the stat back to the pool and sort
    setStatPool(prev => [...prev, stat].sort((a, b) => b - a));
    setAssignments(prev => ({ ...prev, [abilityKey]: null }));
  };

  // Get stat modifier
  const getStatModifier = (stat) => {
    if (!stat) return 0;
    return Math.floor((stat - 10) / 2);
  };

  // Get stat modifier string
  const getStatModifierString = (stat) => {
    const mod = getStatModifier(stat);
    return mod >= 0 ? `+${mod}` : `${mod}`;
  };

  // Get stat quality class
  const getStatQuality = (stat) => {
    if (stat >= 16) return 'legendary';
    if (stat >= 14) return 'excellent';
    if (stat >= 12) return 'good';
    if (stat >= 10) return 'average';
    return 'poor';
  };

  // Complete stat assignment
  const completeAssignment = () => {
    if (!isComplete()) return;
    
    setShowCompletionEffect(true);
    
    // Update character stats
    const newStats = {};
    Object.entries(assignments).forEach(([key, value]) => {
      newStats[key] = value;
    });
    
    setCharacter(prev => ({
      ...prev,
      stats: newStats
    }));

    setTimeout(() => {
      setShowCompletionEffect(false);
      onComplete(newStats);
    }, 2000);
  };

  return (
    <div className="space-y-6 relative">
      {/* Completion Effect Overlay */}
      {showCompletionEffect && (
        <div className="absolute inset-0 bg-gradient-to-r from-amber-600/20 via-orange-600/30 to-red-600/20 rounded-lg border-2 border-amber-400 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="text-center">
            <Flame className="h-16 w-16 text-amber-400 mx-auto mb-4 animate-pulse" />
            <h3 className="text-2xl font-bold text-amber-400 mb-2">Legend Forged!</h3>
            <p className="text-amber-300">Your destiny has been shaped by fire and will...</p>
          </div>
        </div>
      )}

      <Card className="bg-black/90 border-amber-600/50 backdrop-blur-sm">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl text-amber-400 flex items-center justify-center gap-2">
            <Flame className="h-6 w-6" />
            The Legendary Stat Forge
            <Flame className="h-6 w-6" />
          </CardTitle>
          <p className="text-gray-300 text-sm">
            Roll the dice of fate, then forge your legend by assigning each score to the ability of your choice
          </p>
          
          {/* Racial Bonus Info */}
          {character.race && character.racial_asi && Object.values(character.racial_asi).some(v => v > 0) && (
            <div className="mt-3 p-3 bg-amber-600/20 rounded border border-amber-600/40">
              <p className="text-amber-400 text-sm font-semibold mb-1">
                {character.race} {character.subrace && `(${character.subrace})`} Racial Bonuses:
              </p>
              <div className="flex flex-wrap gap-2 justify-center text-xs">
                {Object.entries(character.racial_asi).map(([stat, bonus]) => 
                  bonus > 0 && (
                    <span key={stat} className="text-amber-300">
                      {stat.toUpperCase().slice(0, 3)} +{bonus}
                    </span>
                  )
                )}
              </div>
              <p className="text-gray-400 text-xs mt-1">
                These bonuses will be added to your assigned scores
              </p>
            </div>
          )}
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Stat Pool */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-amber-400 font-semibold">Available Ability Scores</h4>
              <Button
                onClick={rerollStats}
                disabled={isRolling}
                className="bg-red-700 hover:bg-red-600 text-white"
                size="sm"
              >
                <Dice6 className={`h-4 w-4 mr-2 ${isRolling ? 'animate-spin' : ''}`} />
                {isRolling ? 'Rolling...' : 'Reroll All'}
              </Button>
            </div>
            
            <div className="grid grid-cols-3 gap-3">
              {statPool.map((stat, idx) => (
                <Button
                  key={`${stat}-${idx}`}
                  onClick={() => setSelectedStat(stat)}
                  variant={selectedStat === stat ? "default" : "outline"}
                  className={`h-16 text-xl font-bold transition-all duration-300 ${
                    selectedStat === stat ? 'ring-2 ring-amber-400 bg-amber-600 text-black' : ''
                  } ${
                    getStatQuality(stat) === 'legendary' ? 'border-green-400 text-green-300 hover:bg-green-600/20' :
                    getStatQuality(stat) === 'excellent' ? 'border-blue-400 text-blue-300 hover:bg-blue-600/20' :
                    getStatQuality(stat) === 'poor' ? 'border-red-400 text-red-300 hover:bg-red-600/20' :
                    'border-gray-400 text-gray-300 hover:bg-gray-600/20'
                  }`}
                >
                  <div className="flex flex-col items-center">
                    <span>{stat}</span>
                    {getStatQuality(stat) === 'legendary' && <Sparkles className="h-4 w-4 text-green-400" />}
                    {getStatQuality(stat) === 'excellent' && <Zap className="h-4 w-4 text-blue-400" />}
                  </div>
                </Button>
              ))}
            </div>
            
            {selectedStat && (
              <div className="text-center p-2 bg-amber-600/20 rounded border border-amber-600/50">
                <span className="text-amber-300 text-sm">
                  Selected: <span className="font-bold text-white">{selectedStat}</span> 
                  ({getStatModifierString(selectedStat)} modifier) - Click an ability below to assign
                </span>
              </div>
            )}
          </div>

          <Separator className="bg-amber-600/30" />

          {/* Ability Assignment Grid */}
          <div className="space-y-3">
            <h4 className="text-amber-400 font-semibold">Assign to Abilities</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {ABILITIES.map((ability) => (
                <div
                  key={ability.key}
                  className={`p-4 rounded-lg border transition-all duration-200 ${
                    assignments[ability.key] 
                      ? 'border-green-600/50 bg-green-600/10' 
                      : selectedStat 
                        ? 'border-amber-600/50 bg-amber-600/10 cursor-pointer hover:bg-amber-600/20' 
                        : 'border-gray-600/50 bg-gray-800/30'
                  }`}
                  onClick={() => selectedStat && !assignments[ability.key] && assignStat(selectedStat, ability.key)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-white">{ability.short}</span>
                      <span className="text-gray-400 text-sm">{ability.name}</span>
                    </div>
                    
                    {assignments[ability.key] ? (
                      <div className="flex items-center gap-2">
                        <div className="flex items-center gap-1">
                          <Badge className="bg-green-600 text-white">
                            {assignments[ability.key]}
                          </Badge>
                          {character.racial_asi && character.racial_asi[ability.key] && (
                            <>
                              <span className="text-amber-400 text-sm">+{character.racial_asi[ability.key]}</span>
                              <span className="text-gray-400">=</span>
                              <Badge className="bg-amber-600 text-white">
                                {assignments[ability.key] + character.racial_asi[ability.key]}
                              </Badge>
                            </>
                          )}
                          <span className="text-gray-400 text-sm ml-1">
                            ({getStatModifierString(
                              assignments[ability.key] + (character.racial_asi?.[ability.key] || 0)
                            )})
                          </span>
                        </div>
                        <Button
                          onClick={(e) => {
                            e.stopPropagation();
                            unassignStat(ability.key);
                          }}
                          size="sm"
                          variant="outline"
                          className="h-6 px-2 text-xs border-red-600 text-red-400 hover:bg-red-600/20"
                        >
                          Undo
                        </Button>
                      </div>
                    ) : (
                      <Button
                        disabled={!selectedStat}
                        size="sm"
                        className="h-6 px-2 text-xs bg-amber-700 hover:bg-amber-600 disabled:opacity-50"
                      >
                        {selectedStat ? `Assign ${selectedStat}` : 'Select Score'}
                      </Button>
                    )}
                  </div>
                  
                  <p className="text-gray-400 text-xs">{ability.description}</p>
                </div>
              ))}
            </div>
          </div>

          <Separator className="bg-amber-600/30" />

          {/* Completion */}
          {isComplete() && (
            <div className="text-center space-y-4">
              <div className="p-4 bg-green-600/20 rounded border border-green-600/50">
                <h4 className="text-green-400 font-semibold mb-2">Your Legend is Forged!</h4>
                <div className="grid grid-cols-3 gap-2 text-sm">
                  {ABILITIES.map((ability) => {
                    const baseStat = assignments[ability.key];
                    const racialBonus = character.racial_asi?.[ability.key] || 0;
                    const finalStat = baseStat + racialBonus;
                    
                    return (
                      <div key={ability.key} className="text-white">
                        <span className="text-gray-400">{ability.short}:</span> 
                        {racialBonus > 0 ? (
                          <span>
                            {baseStat} <span className="text-amber-400">+{racialBonus}</span> = 
                            <span className="font-bold"> {finalStat}</span> ({getStatModifierString(finalStat)})
                          </span>
                        ) : (
                          <span> {baseStat} ({getStatModifierString(baseStat)})</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
              
              <Button
                onClick={completeAssignment}
                className="bg-green-700 hover:bg-green-600 text-white font-semibold px-8 py-3"
                size="lg"
              >
                <Flame className="h-5 w-5 mr-2" />
                Forge My Destiny
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default StatForge;