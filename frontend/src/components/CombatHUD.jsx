import React from 'react';
import { Sword, Heart, Shield } from 'lucide-react';

const CombatHUD = ({ characterState, combatState }) => {
  if (!combatState) return null;

  const playerHP = characterState.hp?.current || characterState.hp || 10;
  const playerMaxHP = characterState.hp?.max || characterState.max_hp || 10;
  const hpPercent = (playerHP / playerMaxHP) * 100;

  // P3: XP and Level
  const level = characterState.level || 1;
  const currentXP = characterState.current_xp || 0;
  const xpToNext = characterState.xp_to_next || 100;
  const xpPercent = xpToNext > 0 ? (currentXP / xpToNext) * 100 : 100;

  // Get HP bar color based on percentage
  const getHPColor = (percent) => {
    if (percent > 60) return 'bg-green-500';
    if (percent > 30) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const enemies = combatState.enemies || [];
  const aliveEnemies = enemies.filter(e => e.hp > 0);

  return (
    <div className="bg-gray-900 border-2 border-red-600 rounded-lg p-4 mb-4 shadow-lg">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-red-800">
        <Sword className="text-red-500" size={20} />
        <h3 className="text-red-400 font-bold text-lg">⚔️ COMBAT</h3>
        <span className="ml-auto text-gray-400 text-sm">
          Round {combatState.round || 1}
        </span>
      </div>

      {/* Player Status */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <Shield className="text-blue-400" size={16} />
            <span className="text-white font-semibold">
              {characterState.name || 'You'}
            </span>
            <span className="text-purple-400 text-xs font-semibold ml-1">
              Lvl {level}
            </span>
          </div>
          <span className="text-gray-300 text-sm">
            HP: {playerHP}/{playerMaxHP}
          </span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden mb-2">
          <div
            className={`h-full ${getHPColor(hpPercent)} transition-all duration-300`}
            style={{ width: `${hpPercent}%` }}
          />
        </div>
        {/* P3: XP Bar */}
        {xpToNext > 0 && (
          <div className="mt-2">
            <div className="flex items-center justify-between mb-1">
              <span className="text-purple-300 text-xs">XP</span>
              <span className="text-purple-300 text-xs">
                {currentXP}/{xpToNext}
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
              <div
                className="h-full bg-purple-500 transition-all duration-300"
                style={{ width: `${xpPercent}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Enemies */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 mb-2">
          <Sword className="text-red-400" size={16} />
          <span className="text-gray-300 text-sm font-semibold">Enemies:</span>
        </div>
        
        {aliveEnemies.length === 0 ? (
          <p className="text-gray-500 text-sm italic">No enemies remaining</p>
        ) : (
          aliveEnemies.map((enemy, idx) => {
            const enemyHPPercent = (enemy.hp / enemy.max_hp) * 100;
            return (
              <div key={enemy.id || idx} className="bg-gray-800 rounded p-2">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-red-300 text-sm font-medium">
                    {enemy.name}
                  </span>
                  <span className="text-gray-400 text-xs">
                    {enemy.hp > 0 ? `${enemy.hp}/${enemy.max_hp} HP` : 'Defeated'}
                  </span>
                </div>
                {enemy.hp > 0 && (
                  <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full ${getHPColor(enemyHPPercent)} transition-all duration-300`}
                      style={{ width: `${enemyHPPercent}%` }}
                    />
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Combat Tips */}
      <div className="mt-3 pt-3 border-t border-gray-700">
        <p className="text-gray-400 text-xs italic">
          💡 Type your combat action or click an option below
        </p>
      </div>
    </div>
  );
};

export default CombatHUD;
