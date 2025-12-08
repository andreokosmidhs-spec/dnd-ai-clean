import React, { useState } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Dice6, TrendingUp, TrendingDown, Target, AlertCircle } from 'lucide-react';
import { getCheckModifier, buildDiceFormula, formatModifier, inferAdvantageReasons } from '../utils/dndMechanics';

const CheckRequestCard = ({ checkRequest, characterState, worldState, onRoll }) => {
  const [manualMode, setManualMode] = useState(false);
  const [manualRoll, setManualRoll] = useState('');
  const [isRolling, setIsRolling] = useState(false);

  if (!checkRequest) return null;

  // CRITICAL: Wait for character state to load before rendering
  if (!characterState || !characterState.stats || !characterState.level) {
    console.warn('⏳ CheckRequestCard waiting for characterState to load...', {
      hasCharacterState: !!characterState,
      hasStats: !!characterState?.stats,
      hasLevel: !!characterState?.level
    });
    return (
      <Card className="bg-gradient-to-r from-amber-600/20 to-yellow-600/20 border-2 border-amber-400/50">
        <CardContent className="p-4">
          <div className="text-amber-400 text-center">
            <AlertCircle className="h-5 w-5 mx-auto mb-2 animate-pulse" />
            <p className="text-sm">Loading character data...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const { kind, ability, skill, dc, mode, reason, situational_bonus = 0 } = checkRequest;
  
  // Debug logging
  console.log('🎯 CheckRequestCard - characterState:', characterState);
  console.log('🎯 CheckRequestCard - characterState.stats:', characterState?.stats);
  console.log('🎯 CheckRequestCard - characterState.level:', characterState?.level);
  console.log('🎯 CheckRequestCard - situational_bonus:', situational_bonus);
  
  // Compute modifier
  const modifier = getCheckModifier(checkRequest, characterState);
  const formula = buildDiceFormula(mode, modifier);
  
  console.log('🎲 Calculated modifier:', modifier);
  console.log('🎲 Formula:', formula);
  
  // Get advantage/disadvantage reasons
  const advReasons = inferAdvantageReasons(characterState, worldState, checkRequest);
  
  // Build title
  const title = skill 
    ? `${skill} (${ability})` 
    : kind === 'save'
    ? `${ability} Save`
    : `${ability} Check`;

  const handleAutoRoll = async () => {
    setIsRolling(true);
    try {
      await onRoll({ mode: 'auto', formula });
    } finally {
      setIsRolling(false);
    }
  };

  const handleManualSubmit = () => {
    const d20Result = parseInt(manualRoll);
    if (isNaN(d20Result) || d20Result < 1 || d20Result > 20) {
      alert('Please enter a valid d20 roll (1-20)');
      return;
    }
    
    const total = d20Result + modifier;
    onRoll({ 
      mode: 'manual', 
      d20: d20Result, 
      modifier, 
      total,
      formula: `1d20${formatModifier(modifier)}`
    });
    setManualMode(false);
    setManualRoll('');
  };

  return (
    <Card className="bg-gradient-to-r from-amber-600/20 to-yellow-600/20 border-2 border-amber-400/50 animate-in slide-in-from-bottom-5 duration-300">
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5 text-amber-400" />
            <div>
              <h3 className="text-amber-400 font-bold text-lg">{title}</h3>
              <p className="text-amber-300 text-sm">DC {dc}</p>
            </div>
          </div>
          
          <Badge 
            variant="outline" 
            className={`${
              mode === 'advantage' 
                ? 'border-green-400/50 text-green-300 bg-green-600/10' 
                : mode === 'disadvantage'
                ? 'border-red-400/50 text-red-300 bg-red-600/10'
                : 'border-amber-400/50 text-amber-300 bg-amber-600/10'
            }`}
          >
            {mode === 'advantage' && <TrendingUp className="h-3 w-3 mr-1" />}
            {mode === 'disadvantage' && <TrendingDown className="h-3 w-3 mr-1" />}
            {mode === 'advantage' ? 'Advantage' : mode === 'disadvantage' ? 'Disadvantage' : 'Normal'}
          </Badge>
        </div>

        {/* Reason */}
        <div className="mb-3 p-3 bg-black/30 rounded-lg border border-amber-600/20">
          <p className="text-amber-100 text-sm italic">"{reason}"</p>
        </div>

        {/* Modifiers Breakdown */}
        <div className="mb-3 p-3 bg-black/20 rounded-lg space-y-2">
          <div className="text-amber-300 text-sm font-semibold">Modifier Breakdown:</div>
          <div className="text-amber-100 text-sm space-y-1">
            <div>Roll: <span className="font-mono text-amber-400">{formula}</span></div>
            <div>Total Modifier: <span className="font-mono text-amber-400">{formatModifier(modifier)}</span></div>
            {situational_bonus && situational_bonus !== 0 && (
              <div className="text-xs text-amber-300">
                (includes {formatModifier(situational_bonus)} situational)
              </div>
            )}
          </div>
        </div>

        {/* Advantage/Disadvantage Reasons */}
        {advReasons.length > 0 && (
          <div className="mb-3 space-y-1">
            {advReasons.map((r, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs">
                {r.type === 'advantage' ? (
                  <TrendingUp className="h-3 w-3 text-green-400" />
                ) : (
                  <TrendingDown className="h-3 w-3 text-red-400" />
                )}
                <span className={r.type === 'advantage' ? 'text-green-300' : 'text-red-300'}>
                  {r.reason}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Roll Buttons */}
        {!manualMode ? (
          <div className="flex gap-2">
            <Button
              onClick={handleAutoRoll}
              disabled={isRolling}
              className="flex-1 bg-amber-700 hover:bg-amber-600 text-black font-semibold"
            >
              <Dice6 className="h-4 w-4 mr-2" />
              {isRolling ? 'Rolling...' : 'Roll (Auto)'}
            </Button>
            <Button
              onClick={() => setManualMode(true)}
              variant="outline"
              className="border-amber-400/50 text-amber-300 hover:bg-amber-600/20"
            >
              I rolled manually
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-amber-300 text-sm">Enter your d20 result:</div>
            <div className="flex gap-2">
              <Input
                type="number"
                min="1"
                max="20"
                value={manualRoll}
                onChange={(e) => setManualRoll(e.target.value)}
                placeholder="1-20"
                className="flex-1 bg-gray-900/80 border-amber-600/30 text-white"
                autoFocus
              />
              <Button
                onClick={handleManualSubmit}
                className="bg-amber-700 hover:bg-amber-600 text-black"
              >
                Submit
              </Button>
              <Button
                onClick={() => {
                  setManualMode(false);
                  setManualRoll('');
                }}
                variant="outline"
                className="border-amber-400/50 text-amber-300"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default CheckRequestCard;
