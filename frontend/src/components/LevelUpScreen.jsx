import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Star, TrendingUp, Heart, Zap, Sparkles } from 'lucide-react';
import { 
  HIT_DICE, 
  getFeaturesForLevel, 
  grantsASI, 
  getAverageHPGain,
  PROFICIENCY_BONUS 
} from '../data/levelingData';

/**
 * Level Up Screen Component
 * Handles HP increase, ASI selection, and new feature display
 */
const LevelUpScreen = ({ character, newLevel, onComplete }) => {
  const [hpChoice, setHpChoice] = useState(null); // 'roll' or 'average'
  const [rolledHP, setRolledHP] = useState(null);
  const [asiChoices, setAsiChoices] = useState({}); // { strength: 1, dexterity: 1 } etc.
  const [asiPoints, setAsiPoints] = useState(2); // Remaining points to assign

  const characterClass = character.class || character.class_;
  const hitDie = HIT_DICE[characterClass];
  const averageHP = getAverageHPGain(characterClass);
  const conModifier = Math.floor((character.stats?.constitution || 10 - 10) / 2);
  const newFeatures = getFeaturesForLevel(characterClass, newLevel);
  const hasASI = grantsASI(characterClass, newLevel);
  const newProfBonus = PROFICIENCY_BONUS[newLevel];

  // Roll for HP
  const rollHP = () => {
    const roll = Math.floor(Math.random() * hitDie) + 1;
    setRolledHP(roll);
    setHpChoice('roll');
  };

  // Choose average HP
  const chooseAverage = () => {
    setHpChoice('average');
    setRolledHP(null);
  };

  // Apply ASI point to an ability
  const applyASI = (ability) => {
    if (asiPoints <= 0) return;
    if ((asiChoices[ability] || 0) >= 2) return; // Max +2 per ability

    setAsiChoices(prev => ({
      ...prev,
      [ability]: (prev[ability] || 0) + 1
    }));
    setAsiPoints(asiPoints - 1);
  };

  // Remove ASI point from an ability
  const removeASI = (ability) => {
    if (!asiChoices[ability]) return;

    setAsiChoices(prev => {
      const newChoices = { ...prev };
      newChoices[ability]--;
      if (newChoices[ability] === 0) delete newChoices[ability];
      return newChoices;
    });
    setAsiPoints(asiPoints + 1);
  };

  // Calculate final HP increase
  const getFinalHPIncrease = () => {
    if (hpChoice === 'roll' && rolledHP) {
      return rolledHP + conModifier;
    }
    if (hpChoice === 'average') {
      return averageHP + conModifier;
    }
    return 0;
  };

  // Check if ready to complete
  const canComplete = () => {
    // Must choose HP method
    if (!hpChoice) return false;
    
    // If has ASI, must spend all points
    if (hasASI && asiPoints > 0) return false;

    return true;
  };

  // Complete level up
  const completeLevelUp = () => {
    if (!canComplete()) return;

    const hpIncrease = getFinalHPIncrease();

    onComplete({
      newLevel,
      hpIncrease,
      asiChoices: hasASI ? asiChoices : {},
      newFeatures,
      newProfBonus
    });
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card className="bg-black/95 border-amber-600 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <CardHeader className="text-center bg-gradient-to-b from-amber-900/50 to-transparent">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Star className="h-8 w-8 text-amber-400 animate-pulse" fill="currentColor" />
            <CardTitle className="text-3xl text-amber-400">
              Level Up!
            </CardTitle>
            <Star className="h-8 w-8 text-amber-400 animate-pulse" fill="currentColor" />
          </div>
          <p className="text-gray-300">
            {character.name} has reached <span className="text-amber-400 font-bold">Level {newLevel}</span>!
          </p>
        </CardHeader>

        <CardContent className="space-y-6 mt-4">
          {/* New Features */}
          {newFeatures.length > 0 && (
            <div className="p-4 bg-blue-900/20 rounded border border-blue-600/50">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="h-5 w-5 text-blue-400" />
                <h3 className="text-blue-400 font-semibold">New {characterClass} Features</h3>
              </div>
              <ul className="space-y-2">
                {newFeatures.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-gray-300">
                    <Zap className="h-4 w-4 text-amber-400 mt-0.5 flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Proficiency Bonus Increase */}
          {newProfBonus > (character.proficiency_bonus || 2) && (
            <div className="p-3 bg-green-900/20 rounded border border-green-600/50">
              <p className="text-green-400 text-sm">
                <TrendingUp className="h-4 w-4 inline mr-1" />
                Proficiency Bonus increased to <span className="font-bold">+{newProfBonus}</span>
              </p>
            </div>
          )}

          <Separator className="bg-amber-600/30" />

          {/* HP Increase */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Heart className="h-5 w-5 text-red-400" />
              <h3 className="text-amber-400 font-semibold">Hit Point Increase</h3>
            </div>

            <p className="text-gray-400 text-sm">
              Choose to roll 1d{hitDie} or take the average ({averageHP}). 
              Your Constitution modifier (+{conModifier}) will be added.
            </p>

            <div className="grid grid-cols-2 gap-4">
              {/* Roll Option */}
              <div 
                className={`p-4 rounded border cursor-pointer transition-all ${
                  hpChoice === 'roll' 
                    ? 'border-green-600 bg-green-600/20' 
                    : 'border-gray-600 bg-gray-800/30 hover:border-amber-600/50'
                }`}
                onClick={rollHP}
              >
                <p className="text-white font-semibold mb-2">🎲 Roll</p>
                <p className="text-gray-400 text-sm mb-3">1d{hitDie} + {conModifier}</p>
                {hpChoice === 'roll' && rolledHP && (
                  <div className="text-center">
                    <Badge className="bg-green-600 text-white text-lg">
                      +{rolledHP + conModifier} HP
                    </Badge>
                    <p className="text-xs text-gray-400 mt-1">
                      (Rolled {rolledHP} + {conModifier} CON)
                    </p>
                  </div>
                )}
              </div>

              {/* Average Option */}
              <div 
                className={`p-4 rounded border cursor-pointer transition-all ${
                  hpChoice === 'average' 
                    ? 'border-green-600 bg-green-600/20' 
                    : 'border-gray-600 bg-gray-800/30 hover:border-amber-600/50'
                }`}
                onClick={chooseAverage}
              >
                <p className="text-white font-semibold mb-2">📊 Average (Safe)</p>
                <p className="text-gray-400 text-sm mb-3">{averageHP} + {conModifier}</p>
                {hpChoice === 'average' && (
                  <div className="text-center">
                    <Badge className="bg-green-600 text-white text-lg">
                      +{averageHP + conModifier} HP
                    </Badge>
                    <p className="text-xs text-gray-400 mt-1">
                      ({averageHP} avg + {conModifier} CON)
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* ASI (Ability Score Improvement) */}
          {hasASI && (
            <>
              <Separator className="bg-amber-600/30" />
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-amber-400 font-semibold">Ability Score Improvement</h3>
                  <Badge className={asiPoints > 0 ? "bg-amber-600" : "bg-green-600"}>
                    {asiPoints} points remaining
                  </Badge>
                </div>

                <p className="text-gray-400 text-sm">
                  Increase ability scores by a total of 2 points. You can add 2 to one ability, 
                  or 1 to two different abilities. No ability can increase by more than 2.
                </p>

                <div className="grid grid-cols-2 gap-3">
                  {['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'].map(ability => {
                    const currentValue = character.stats?.[ability] || 10;
                    const asiBonus = asiChoices[ability] || 0;
                    const newValue = currentValue + asiBonus;
                    const canAdd = asiPoints > 0 && asiBonus < 2;
                    const canRemove = asiBonus > 0;

                    return (
                      <div 
                        key={ability}
                        className="p-3 rounded border border-gray-600 bg-gray-800/30"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-white font-semibold capitalize">
                            {ability.slice(0, 3).toUpperCase()}
                          </span>
                          <div className="flex items-center gap-1">
                            {asiBonus > 0 && (
                              <>
                                <span className="text-gray-400">{currentValue}</span>
                                <span className="text-amber-400">+{asiBonus}</span>
                                <span className="text-gray-400">=</span>
                              </>
                            )}
                            <Badge className={asiBonus > 0 ? "bg-green-600" : "bg-gray-600"}>
                              {newValue}
                            </Badge>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            onClick={() => applyASI(ability)}
                            disabled={!canAdd}
                            size="sm"
                            className="flex-1 bg-green-700 hover:bg-green-600 disabled:opacity-30"
                          >
                            +1
                          </Button>
                          <Button
                            onClick={() => removeASI(ability)}
                            disabled={!canRemove}
                            size="sm"
                            variant="outline"
                            className="flex-1 border-red-600 text-red-400 hover:bg-red-600/20 disabled:opacity-30"
                          >
                            -1
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}

          <Separator className="bg-amber-600/30" />

          {/* Complete Button */}
          <div className="text-center">
            <Button
              onClick={completeLevelUp}
              disabled={!canComplete()}
              size="lg"
              className="bg-amber-700 hover:bg-amber-600 disabled:opacity-50 px-8 py-3 font-semibold"
            >
              {canComplete() ? (
                <>
                  <Star className="h-5 w-5 mr-2" />
                  Complete Level Up
                </>
              ) : (
                <>
                  {!hpChoice && "Choose HP Increase"}
                  {hpChoice && hasASI && asiPoints > 0 && `Assign ${asiPoints} more ASI points`}
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LevelUpScreen;
