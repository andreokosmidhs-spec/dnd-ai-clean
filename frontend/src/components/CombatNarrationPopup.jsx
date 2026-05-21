import React, { useEffect, useRef } from 'react';
import { X, Sword, Shield, Zap } from 'lucide-react';

const MechanicLine = ({ label, value, highlight }) => (
  <div className="flex justify-between items-center text-sm">
    <span className="text-slate-400">{label}</span>
    <span className={`font-bold ${highlight ? 'text-yellow-300' : 'text-white'}`}>{value}</span>
  </div>
);

const CombatNarrationPopup = ({ narration, mechanics, isEnemy = false, onDismiss, autoDismissMs = 0 }) => {
  const timerRef = useRef(null);

  useEffect(() => {
    if (!narration) return;
    if (autoDismissMs > 0) {
      timerRef.current = setTimeout(onDismiss, autoDismissMs);
    }
    return () => clearTimeout(timerRef.current);
  }, [narration, autoDismissMs, onDismiss]);

  if (!narration) return null;

  const m = mechanics || {};
  const hasMechanics = m.attack_roll != null || m.damage != null;

  // Top bar colour — enemy attacks use red/orange, player uses violet/yellow/green
  const topBarColor = isEnemy
    ? (m.critical ? 'bg-orange-500' : m.hit === false ? 'bg-slate-600' : 'bg-red-600')
    : (m.critical ? 'bg-yellow-400' : m.hit === false ? 'bg-slate-600' : m.target_killed ? 'bg-red-500' : 'bg-violet-500');

  const borderColor = isEnemy ? 'border-red-900/60' : 'border-slate-600/60';

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center"
      onClick={onDismiss}
    >
      {/* backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

      {/* panel */}
      <div
        className={`relative z-10 max-w-lg w-full mx-4 rounded-2xl border ${borderColor} bg-slate-900/95 shadow-2xl overflow-hidden`}
        onClick={e => e.stopPropagation()}
      >
        {/* coloured top bar */}
        <div className={`h-1 w-full ${topBarColor}`} />

        <div className="p-5">
          {/* close */}
          <button
            onClick={onDismiss}
            className="absolute top-3 right-3 text-slate-500 hover:text-white transition-colors"
          >
            <X size={18} />
          </button>

          {/* turn label */}
          <div className={`text-[10px] font-bold uppercase tracking-widest mb-2 ${
            isEnemy ? 'text-red-400' : 'text-violet-400'
          }`}>
            {isEnemy ? '⚔ Enemy Attack' : '🗡 Your Attack'}
          </div>

          {/* narration text */}
          <p className="text-slate-100 leading-relaxed text-[0.95rem] pr-6 mb-4">
            {narration}
          </p>

          {/* mechanical summary */}
          {hasMechanics && (
            <div className="border-t border-slate-700 pt-3 space-y-1.5">
              {/* advantage / disadvantage badge */}
              {(m.advantage || m.disadvantage) && !(m.advantage && m.disadvantage) && (
                <div className={`flex flex-col gap-1 px-2 py-1.5 rounded-lg text-xs ${
                  m.advantage && !m.disadvantage
                    ? 'bg-green-950/60 border border-green-700/40'
                    : 'bg-red-950/60 border border-red-700/40'
                }`}>
                  <div className={`font-bold flex items-center gap-1 ${
                    m.advantage && !m.disadvantage ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {m.advantage && !m.disadvantage
                      ? <>🎲🎲↑ Advantage — rolling 2d20, taking higher</>
                      : <>🎲🎲↓ Disadvantage — rolling 2d20, taking lower</>}
                    {m.roll2 != null && (
                      <span className="ml-2 font-normal text-slate-400">
                        ({m.roll1} / {m.roll2})
                      </span>
                    )}
                  </div>
                  {/* source chips */}
                  <div className="flex flex-wrap gap-1">
                    {(m.advantage && !m.disadvantage ? m.adv_sources : m.disadv_sources || []).map((src, i) => (
                      <span key={i} className={`px-1.5 py-0.5 rounded text-[10px] ${
                        m.advantage && !m.disadvantage
                          ? 'bg-green-900/60 text-green-300'
                          : 'bg-red-900/60 text-red-300'
                      }`}>{src}</span>
                    ))}
                  </div>
                </div>
              )}
              {/* cancelled — both advantage and disadvantage */}
              {m.advantage && m.disadvantage && (
                <div className="text-slate-500 text-xs px-2 py-1 rounded-lg bg-slate-800/60 border border-slate-700/40">
                  ⚖ Advantage and disadvantage cancel — straight roll
                  {m.adv_sources?.length > 0 && <span className="ml-1 text-green-700">({m.adv_sources.join(', ')})</span>}
                  {m.disadv_sources?.length > 0 && <span className="ml-1 text-red-700">({m.disadv_sources.join(', ')})</span>}
                </div>
              )}

              {/* attack roll line */}
              {m.attack_roll != null && (
                <MechanicLine
                  label={isEnemy ? `${m.attacker || 'Enemy'} attacks you` : `${m.attacker || 'You'} → ${m.target || 'Enemy'}`}
                  value={`Roll ${m.attack_roll} + mods = ${m.total_attack ?? m.attack_roll} vs AC ${m.target_ac}`}
                  highlight={m.critical}
                />
              )}
              {m.critical && (
                <div className="text-yellow-300 text-sm font-bold flex items-center gap-1">
                  <Zap size={14} /> Critical Hit!
                </div>
              )}
              {m.critical_miss && (
                <div className="text-slate-400 text-sm font-bold">Critical Miss — attack fumbled!</div>
              )}
              {m.hit && m.damage != null && (
                <MechanicLine label="Damage dealt" value={`${m.damage} hp`} highlight />
              )}
              {m.hit === false && !m.critical_miss && (
                <div className="text-slate-400 text-sm">Attack missed.</div>
              )}
              {!isEnemy && m.target_hp_remaining != null && m.target_max_hp != null && (
                <div className="mt-2">
                  <div className="flex justify-between text-xs text-slate-500 mb-1">
                    <span>{m.target}</span>
                    <span>{m.target_hp_remaining}/{m.target_max_hp} HP</span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        m.target_hp_remaining / m.target_max_hp > 0.6 ? 'bg-green-500' :
                        m.target_hp_remaining / m.target_max_hp > 0.3 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.max(0, (m.target_hp_remaining / m.target_max_hp) * 100)}%` }}
                    />
                  </div>
                </div>
              )}
              {m.target_killed && (
                <div className="text-red-400 text-sm font-semibold flex items-center gap-1">
                  <Sword size={13} /> {m.target} defeated!
                </div>
              )}
              {m.light_note && (
                <div className="text-orange-400 text-xs flex items-center gap-1 mt-1">
                  🌙 {m.light_note}
                </div>
              )}
            </div>
          )}

          {/* continue button */}
          <div className="mt-4 flex justify-end">
            <button
              onClick={onDismiss}
              className={`px-4 py-1.5 rounded-lg text-white text-sm font-semibold transition-colors ${
                isEnemy ? 'bg-red-800 hover:bg-red-700' : 'bg-violet-700 hover:bg-violet-600'
              }`}
            >
              Continue
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CombatNarrationPopup;
