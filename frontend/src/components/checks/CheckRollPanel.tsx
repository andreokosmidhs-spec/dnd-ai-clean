import React, { useState } from 'react';
import { Dices, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { CheckRequest, Character, PlayerRoll, DifficultyBand, CheckOutcome } from '../../types/checks';

interface CheckRollPanelProps {
  checkRequest: CheckRequest;
  character: Character;
  onRollComplete: (rollResult: PlayerRoll) => void;
  onDismiss?: () => void;
}

const CheckRollPanel: React.FC<CheckRollPanelProps> = ({
  checkRequest,
  character,
  onRollComplete,
  onDismiss,
}) => {
  const [rolling, setRolling] = useState(false);
  const [rollResult, setRollResult] = useState<PlayerRoll | null>(null);
  const [customRoll, setCustomRoll] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);

  // Calculate modifier for this check
  const getModifier = () => {
    const abilityScore = character?.stats?.[checkRequest.ability as keyof typeof character.stats] || 10;
    const abilityMod = Math.floor((abilityScore - 10) / 2);
    
    // Check if proficient in skill
    const isProficient = checkRequest.skill && 
      character?.skills?.includes(checkRequest.skill);
    
    const proficiencyBonus = isProficient ? 
      (Math.floor(((character?.level || 1) - 1) / 4) + 2) : 0;
    
    return {
      ability: abilityMod,
      proficiency: proficiencyBonus,
      total: abilityMod + proficiencyBonus
    };
  };

  const modifier = getModifier();

  // Roll dice with advantage/disadvantage
  const rollDice = () => {
    setRolling(true);
    
    // Simulate dice roll animation
    setTimeout(() => {
      let roll1 = Math.floor(Math.random() * 20) + 1;
      let roll2 = checkRequest.advantage_state !== 'normal' 
        ? Math.floor(Math.random() * 20) + 1 
        : null;
      
      let finalRoll = roll1;
      
      if (checkRequest.advantage_state === 'advantage' && roll2 !== null) {
        finalRoll = Math.max(roll1, roll2);
      } else if (checkRequest.advantage_state === 'disadvantage' && roll2 !== null) {
        finalRoll = Math.min(roll1, roll2);
      }
      
      const total = finalRoll + modifier.total;
      
      const result: PlayerRoll = {
        d20_roll: finalRoll,
        advantage_rolls: roll2 !== null ? [roll1, roll2] : null,
        modifier: modifier.total,
        ability_modifier: modifier.ability,
        proficiency_bonus: modifier.proficiency,
        other_bonuses: 0,
        total,
        advantage_state: checkRequest.advantage_state
      };
      
      setRollResult(result);
      setRolling(false);
    }, 800);
  };

  // Handle custom roll input
  const handleCustomRoll = () => {
    const roll = parseInt(customRoll);
    if (isNaN(roll) || roll < 1 || roll > 20) {
      alert('Please enter a valid d20 roll (1-20)');
      return;
    }
    
    const total = roll + modifier.total;
    
    const result: PlayerRoll = {
      d20_roll: roll,
      advantage_rolls: null,
      modifier: modifier.total,
      ability_modifier: modifier.ability,
      proficiency_bonus: modifier.proficiency,
      other_bonuses: 0,
      total,
      advantage_state: checkRequest.advantage_state
    };
    
    setRollResult(result);
  };

  // Submit roll result to backend
  const submitRoll = () => {
    if (rollResult && onRollComplete) {
      onRollComplete(rollResult);
    }
    setRollResult(null);
  };

  // Get advantage icon
  const getAdvantageIcon = () => {
    if (checkRequest.advantage_state === 'advantage') {
      return <TrendingUp className="w-5 h-5 text-green-400" />;
    } else if (checkRequest.advantage_state === 'disadvantage') {
      return <TrendingDown className="w-5 h-5 text-red-400" />;
    }
    return <Minus className="w-5 h-5 text-gray-400" />;
  };

  // Get DC color
  const getDCColor = (): string => {
    switch(checkRequest.dc_band) {
      case 'trivial': return 'text-green-400';
      case 'easy': return 'text-blue-400';
      case 'moderate': return 'text-yellow-400';
      case 'hard': return 'text-orange-400';
      case 'very_hard': return 'text-red-400';
      case 'nearly_impossible': return 'text-purple-400';
      default: return 'text-gray-400';
    }
  };

  // Get outcome info for display
  const getOutcomeInfo = () => {
    if (!rollResult) return null;
    
    const margin = rollResult.total - checkRequest.dc;
    const success = margin >= 0;
    const isNat20 = rollResult.d20_roll === 20;
    const isNat1 = rollResult.d20_roll === 1;
    
    let outcome: CheckOutcome;
    let outcomeColor: string;
    
    if (isNat20 || margin >= 10) {
      outcome = 'critical_success';
      outcomeColor = 'bg-green-500/20 border-green-500';
    } else if (margin >= 5) {
      outcome = 'clear_success';
      outcomeColor = 'bg-green-600/20 border-green-600';
    } else if (margin >= 0) {
      outcome = 'marginal_success';
      outcomeColor = 'bg-blue-500/20 border-blue-500';
    } else if (margin >= -4) {
      outcome = 'marginal_failure';
      outcomeColor = 'bg-yellow-500/20 border-yellow-500';
    } else if (margin >= -9) {
      outcome = 'clear_failure';
      outcomeColor = 'bg-orange-500/20 border-orange-500';
    } else {
      outcome = 'critical_failure';
      outcomeColor = 'bg-red-500/20 border-red-500';
    }
    
    if (isNat1) {
      outcome = 'critical_failure';
      outcomeColor = 'bg-red-500/20 border-red-500';
    }
    
    return { success, margin, outcome, outcomeColor };
  };

  const outcomeInfo = getOutcomeInfo();

  return (
    <div className="fixed bottom-4 right-4 w-96 bg-gray-900 border-2 border-amber-500 rounded-lg shadow-2xl z-50">
      {/* Header */}
      <div className="bg-amber-500 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Dices className="w-5 h-5" />
          <span className="font-bold uppercase text-sm">Ability Check</span>
        </div>
        {onDismiss && (
          <button 
            onClick={onDismiss}
            className="text-gray-900 hover:text-gray-700 font-bold"
          >
            ✕
          </button>
        )}
      </div>

      {/* Content */}
      <div className="p-4 space-y-3">
        {/* Action Context */}
        <div className="bg-gray-800 p-3 rounded border border-gray-700">
          <div className="text-xs text-gray-400 uppercase mb-1">Action</div>
          <div className="text-sm text-white">{checkRequest.action_context}</div>
        </div>

        {/* Check Info */}
        <div className="grid grid-cols-2 gap-3">
          {/* Ability + Skill */}
          <div className="bg-gray-800 p-3 rounded border border-gray-700">
            <div className="text-xs text-gray-400 uppercase mb-1">Check Type</div>
            <div className="text-sm font-bold text-amber-400 capitalize">
              {checkRequest.skill || checkRequest.ability}
            </div>
            <div className="text-xs text-gray-500 capitalize">
              ({checkRequest.ability})
            </div>
          </div>

          {/* DC */}
          <div className="bg-gray-800 p-3 rounded border border-gray-700">
            <div className="text-xs text-gray-400 uppercase mb-1">Difficulty</div>
            <div className={`text-2xl font-bold ${getDCColor()}`}>
              DC {checkRequest.dc}
            </div>
            <div className="text-xs text-gray-500 capitalize">
              {checkRequest.dc_band.replace('_', ' ')}
            </div>
          </div>
        </div>

        {/* Modifier Info */}
        <div className="bg-gray-800 p-3 rounded border border-gray-700">
          <div className="text-xs text-gray-400 uppercase mb-1">Your Modifier</div>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold text-white">
              {modifier.total >= 0 ? '+' : ''}{modifier.total}
            </div>
            <div className="text-xs text-gray-400 space-y-1">
              <div>Ability: {modifier.ability >= 0 ? '+' : ''}{modifier.ability}</div>
              {modifier.proficiency > 0 && (
                <div>Proficiency: +{modifier.proficiency}</div>
              )}
            </div>
          </div>
        </div>

        {/* Advantage/Disadvantage */}
        {checkRequest.advantage_state !== 'normal' && (
          <div className="bg-gray-800 p-3 rounded border border-gray-700">
            <div className="flex items-center gap-2">
              {getAdvantageIcon()}
              <span className="text-sm font-bold capitalize">
                {checkRequest.advantage_state}
              </span>
            </div>
            <div className="text-xs text-gray-400 mt-1">
              {checkRequest.reason}
            </div>
          </div>
        )}

        {/* Roll Result */}
        {rollResult && outcomeInfo && (
          <div className={`p-4 rounded border-2 ${outcomeInfo.outcomeColor}`}>
            {/* Dice Rolls */}
            <div className="text-center mb-3">
              {rollResult.advantage_rolls ? (
                <div className="flex items-center justify-center gap-3">
                  <div className={`text-4xl font-bold ${
                    rollResult.d20_roll === rollResult.advantage_rolls[0] 
                      ? 'text-white' 
                      : 'text-gray-600 line-through'
                  }`}>
                    {rollResult.advantage_rolls[0]}
                  </div>
                  <div className="text-gray-400">/</div>
                  <div className={`text-4xl font-bold ${
                    rollResult.d20_roll === rollResult.advantage_rolls[1] 
                      ? 'text-white' 
                      : 'text-gray-600 line-through'
                  }`}>
                    {rollResult.advantage_rolls[1]}
                  </div>
                </div>
              ) : (
                <div className="text-5xl font-bold text-white">
                  {rollResult.d20_roll}
                </div>
              )}
            </div>

            {/* Total */}
            <div className="text-center border-t border-gray-700 pt-3">
              <div className="text-xs text-gray-400 uppercase mb-1">Total</div>
              <div className="text-3xl font-bold text-white">
                {rollResult.total}
                <span className="text-sm text-gray-400 ml-2">
                  (vs DC {checkRequest.dc})
                </span>
              </div>
            </div>

            {/* Outcome */}
            <div className="text-center mt-3 pt-3 border-t border-gray-700">
              <div className={`text-lg font-bold uppercase ${
                outcomeInfo.success ? 'text-green-400' : 'text-red-400'
              }`}>
                {outcomeInfo.success ? '✓ Success' : '✗ Failure'}
              </div>
              <div className="text-xs text-gray-400 mt-1 capitalize">
                {outcomeInfo.outcome.replace('_', ' ')}
                {outcomeInfo.margin !== 0 && (
                  <span> ({outcomeInfo.margin > 0 ? '+' : ''}{outcomeInfo.margin})</span>
                )}
              </div>
            </div>

            {/* Submit Button */}
            <button
              onClick={submitRoll}
              className="w-full mt-4 bg-amber-500 hover:bg-amber-600 text-gray-900 font-bold py-2 px-4 rounded transition-colors"
            >
              Continue Adventure
            </button>
          </div>
        )}

        {/* Roll Buttons */}
        {!rollResult && (
          <div className="space-y-2">
            <button
              onClick={rollDice}
              disabled={rolling}
              className="w-full bg-amber-500 hover:bg-amber-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-gray-900 font-bold py-3 px-4 rounded transition-colors flex items-center justify-center gap-2"
            >
              <Dices className="w-5 h-5" />
              {rolling ? 'Rolling...' : 'Roll Dice'}
            </button>

            {!showCustomInput ? (
              <button
                onClick={() => setShowCustomInput(true)}
                className="w-full bg-gray-700 hover:bg-gray-600 text-gray-300 font-medium py-2 px-4 rounded transition-colors text-sm"
              >
                Enter Custom Roll
              </button>
            ) : (
              <div className="flex gap-2">
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={customRoll}
                  onChange={(e) => setCustomRoll(e.target.value)}
                  placeholder="1-20"
                  className="flex-1 bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white"
                />
                <button
                  onClick={handleCustomRoll}
                  className="bg-amber-500 hover:bg-amber-600 text-gray-900 font-bold py-2 px-4 rounded"
                >
                  Submit
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CheckRollPanel;
