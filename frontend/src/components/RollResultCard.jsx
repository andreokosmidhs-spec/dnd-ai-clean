import React from 'react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Dice6, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { getCheckOutcome } from '../utils/dndMechanics';

const RollResultCard = ({ rollData, checkRequest }) => {
  if (!rollData || !checkRequest) return null;

  const { formula, rolls, kept, modifier, total } = rollData;
  const { dc, mode, advantage_reason, disadvantage_reason, modifier_breakdown } = checkRequest;
  
  const outcome = getCheckOutcome(total, dc);
  
  // Parse modifier breakdown for transparent display
  const hasAdvantage = mode === 'advantage' || (rolls && rolls.length > 1 && formula.includes('kh'));
  const hasDisadvantage = mode === 'disadvantage' || (rolls && rolls.length > 1 && formula.includes('kl'));
  
  const outcomeConfig = {
    critical_success: {
      icon: CheckCircle,
      color: 'text-green-400',
      bgColor: 'bg-green-600/20',
      borderColor: 'border-green-400/50',
      label: 'Critical Success!'
    },
    success: {
      icon: CheckCircle,
      color: 'text-green-400',
      bgColor: 'bg-green-600/20',
      borderColor: 'border-green-400/50',
      label: 'Success'
    },
    partial: {
      icon: AlertCircle,
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-600/20',
      borderColor: 'border-yellow-400/50',
      label: 'Partial Success'
    },
    fail: {
      icon: XCircle,
      color: 'text-red-400',
      bgColor: 'bg-red-600/20',
      borderColor: 'border-red-400/50',
      label: 'Failure'
    }
  };

  const config = outcomeConfig[outcome];
  const Icon = config.icon;

  return (
    <Card className={`${config.bgColor} border-2 ${config.borderColor} animate-in slide-in-from-bottom-5 duration-300`}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Dice6 className={`h-5 w-5 ${config.color}`} />
            <div>
              <div className="flex items-center gap-2">
                <span className={`font-bold ${config.color}`}>Roll Result</span>
                <Icon className={`h-4 w-4 ${config.color}`} />
              </div>
              <div className="text-sm text-gray-300 mt-1 font-mono">
                {/* Dice Roll Display */}
                {rolls && rolls.length > 1 ? (
                  <div className="flex flex-col gap-1">
                    <div>
                      <span className="text-gray-400">Rolled: [{rolls.join(', ')}]</span>
                      {hasAdvantage && <span className="text-green-400 ml-2">(Advantage)</span>}
                      {hasDisadvantage && <span className="text-red-400 ml-2">(Disadvantage)</span>}
                    </div>
                    <div>
                      <span className="text-gray-400">Kept: </span>
                      <span className={config.color}>[{kept.join(', ')}]</span>
                    </div>
                  </div>
                ) : (
                  <div>
                    <span className="text-gray-400">d20: </span>
                    <span className={config.color}>{rolls?.[0] || rollData.d20}</span>
                  </div>
                )}
                
                {/* Modifier Breakdown */}
                {modifier !== 0 && (
                  <div className="text-xs text-gray-400 mt-1">
                    {modifier_breakdown || `Modifier: ${modifier >= 0 ? '+' : ''}${modifier}`}
                  </div>
                )}
                
                {/* Final Total */}
                <div className="mt-1">
                  <span className="text-white font-bold">Total: {total}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="text-right">
            <Badge 
              variant="outline" 
              className={`${config.borderColor} ${config.color} bg-black/20 font-bold`}
            >
              {config.label}
            </Badge>
            <div className="text-xs text-gray-400 mt-1">
              vs DC {dc}
            </div>
            
            {/* Advantage/Disadvantage Reason */}
            {(hasAdvantage || hasDisadvantage) && (
              <div className="text-xs text-gray-300 mt-2 max-w-32">
                <div className={hasAdvantage ? 'text-green-400' : 'text-red-400'}>
                  {hasAdvantage ? 'Advantage' : 'Disadvantage'}:
                </div>
                <div className="text-gray-400 text-wrap">
                  {advantage_reason || disadvantage_reason || 'Situational modifier'}
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default RollResultCard;
