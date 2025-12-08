import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { useGameState } from '../contexts/GameStateContext';
import { Heart, Shield, Flame, MapPin, Package, AlertTriangle } from 'lucide-react';

const StateModifierPanel = () => {
  const { characterState, worldState, updateCharacter, updateWorld, updateThreatLevel, threatLevel } = useGameState();

  const takeDamage = () => {
    const newHP = Math.max(0, characterState.hp.current - 5);
    updateCharacter({
      hp: { ...characterState.hp, current: newHP }
    });
  };

  const heal = () => {
    const newHP = Math.min(characterState.hp.max, characterState.hp.current + 5);
    updateCharacter({
      hp: { ...characterState.hp, current: newHP }
    });
  };

  const equipLantern = () => {
    const hasLantern = characterState.inventory.some(item => item.name === 'Lantern');
    if (!hasLantern) {
      const newInventory = [
        ...characterState.inventory,
        { id: 'item-lantern', name: 'Lantern', qty: 1, tags: ['light', 'tool'], equipped: true, notes: 'Bright light 30ft, dim 60ft' }
      ];
      updateCharacter({ inventory: newInventory });
    }
  };

  const addCondition = (condition) => {
    if (!characterState.conditions.includes(condition)) {
      updateCharacter({
        conditions: [...characterState.conditions, condition]
      });
    }
  };

  const removeCondition = (condition) => {
    updateCharacter({
      conditions: characterState.conditions.filter(c => c !== condition)
    });
  };

  const changeTime = (time) => {
    updateWorld({ time_of_day: time });
  };

  const changeWeather = (weather) => {
    updateWorld({ weather });
  };

  return (
    <Card className="bg-black/90 border-amber-600/30 max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-amber-400 text-center">🧪 State Modifier - Test Adaptive Behavior</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        
        {/* HP Modifications */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-red-400 font-semibold">
            <Heart className="h-4 w-4" />
            HP Modifications
          </div>
          <div className="flex gap-2">
            <Button onClick={takeDamage} variant="outline" size="sm" className="border-red-600/50 text-red-400">
              Take 5 Damage
            </Button>
            <Button onClick={heal} variant="outline" size="sm" className="border-green-600/50 text-green-400">
              Heal 5 HP
            </Button>
          </div>
          <div className="text-xs text-gray-400">
            Current HP: {characterState.hp.current}/{characterState.hp.max}
          </div>
        </div>

        {/* Equipment Changes */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-amber-400 font-semibold">
            <Package className="h-4 w-4" />
            Equipment
          </div>
          <div className="flex gap-2">
            <Button onClick={equipLantern} variant="outline" size="sm" className="border-amber-600/50 text-amber-400">
              Equip Lantern
            </Button>
          </div>
        </div>

        {/* Conditions */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-orange-400 font-semibold">
            <AlertTriangle className="h-4 w-4" />
            Conditions
          </div>
          <div className="flex gap-2 flex-wrap">
            <Button onClick={() => addCondition('poisoned')} variant="outline" size="sm" className="border-orange-600/50 text-orange-400">
              Add Poisoned
            </Button>
            <Button onClick={() => addCondition('exhausted')} variant="outline" size="sm" className="border-orange-600/50 text-orange-400">
              Add Exhausted
            </Button>
            {characterState.conditions.length > 0 && (
              <Button onClick={() => removeCondition(characterState.conditions[0])} variant="outline" size="sm" className="border-green-600/50 text-green-400">
                Remove First Condition
              </Button>
            )}
          </div>
          <div className="text-xs text-gray-400">
            Active: {characterState.conditions.join(', ') || 'None'}
          </div>
        </div>

        {/* World State */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-purple-400 font-semibold">
            <MapPin className="h-4 w-4" />
            World State
          </div>
          <div className="flex gap-2 flex-wrap">
            <Button onClick={() => changeTime('night')} variant="outline" size="sm" className="border-purple-600/50 text-purple-400">
              → Night
            </Button>
            <Button onClick={() => changeTime('dawn')} variant="outline" size="sm" className="border-purple-600/50 text-purple-400">
              → Dawn
            </Button>
            <Button onClick={() => changeWeather('heavy rain')} variant="outline" size="sm" className="border-blue-600/50 text-blue-400">
              Heavy Rain
            </Button>
            <Button onClick={() => changeWeather('clear skies')} variant="outline" size="sm" className="border-blue-600/50 text-blue-400">
              Clear Skies
            </Button>
          </div>
          <div className="text-xs text-gray-400">
            {worldState.time_of_day} - {worldState.weather}
          </div>
        </div>

        {/* Threat Level */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-red-400 font-semibold">
            <Flame className="h-4 w-4" />
            Threat Level
          </div>
          <div className="flex gap-2">
            <Button onClick={() => updateThreatLevel(0)} variant="outline" size="sm" className="border-green-600/50 text-green-400">
              Peaceful (0)
            </Button>
            <Button onClick={() => updateThreatLevel(2)} variant="outline" size="sm" className="border-yellow-600/50 text-yellow-400">
              Moderate (2)
            </Button>
            <Button onClick={() => updateThreatLevel(4)} variant="outline" size="sm" className="border-red-600/50 text-red-400">
              Dangerous (4)
            </Button>
            <Button onClick={() => updateThreatLevel(5)} variant="outline" size="sm" className="border-red-700/50 text-red-600">
              Dire (5)
            </Button>
          </div>
          <div className="text-xs text-gray-400">
            Current: {threatLevel}/5
          </div>
        </div>

        <div className="text-center text-xs text-gray-500 pt-4 border-t border-gray-700">
          💡 Make changes above, then send a message in DM Chat to see adaptive narration and options!
        </div>
      </CardContent>
    </Card>
  );
};

export default StateModifierPanel;
