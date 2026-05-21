/**
 * ConditionInteractionModal
 *
 * Appears when a player clicks a battlefield condition card.
 * Player describes how they want to use/react to the environment,
 * rolls d20, and sends the proposal to the AI DM for adjudication.
 */
import React, { useState, useRef, useEffect } from 'react';
import { X, Dice6, Loader2, Sparkles, AlertTriangle, Minus } from 'lucide-react';

const OUTCOME_STYLE = {
  bonus:   { icon: Sparkles,      color: 'text-yellow-300', bg: 'bg-yellow-900/30 border-yellow-700/50', label: 'Success' },
  penalty: { icon: AlertTriangle, color: 'text-red-300',    bg: 'bg-red-900/30 border-red-700/50',    label: 'Backfired' },
  neutral: { icon: Minus,         color: 'text-slate-300',  bg: 'bg-slate-800/60 border-slate-600/50', label: 'Neutral' },
};

function rollD20() {
  return Math.floor(Math.random() * 20) + 1;
}

function rollColor(r) {
  if (r === 20) return 'text-yellow-300 font-black';
  if (r >= 15)  return 'text-green-300 font-bold';
  if (r >= 8)   return 'text-slate-200 font-semibold';
  if (r >= 2)   return 'text-orange-300 font-bold';
  return 'text-red-400 font-black';
}

function rollLabel(r) {
  if (r === 20) return 'Natural 20!';
  if (r >= 15)  return 'High roll';
  if (r >= 8)   return 'Solid roll';
  if (r >= 2)   return 'Low roll';
  return 'Natural 1!';
}

const ConditionInteractionModal = ({
  condition,
  campaignId,
  characterState,
  combatState,
  characterId,
  onClose,
  onNarration,   // (narration, outcome) → feed back to CombatScreen
}) => {
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  const [action, setAction] = useState('');
  const [roll, setRoll] = useState(null);
  const [rolling, setRolling] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null); // { narration, outcome }
  const textRef = useRef();

  useEffect(() => {
    textRef.current?.focus();
  }, []);

  const handleRoll = () => {
    setRolling(true);
    // Animate through a few random numbers then land
    let ticks = 0;
    const interval = setInterval(() => {
      setRoll(rollD20());
      ticks++;
      if (ticks >= 10) {
        clearInterval(interval);
        setRolling(false);
      }
    }, 60);
  };

  const handleSend = async () => {
    if (!action.trim()) return;
    const finalRoll = roll ?? rollD20();
    if (!roll) setRoll(finalRoll);
    setLoading(true);

    try {
      const res = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/combat/conditions/${condition.condition_id || condition.id}/interact`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            player_action: action,
            roll: finalRoll,
            character_state: characterState,
            combat_state: combatState,
            character_id: characterId,
          }),
        }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Request failed');
      setResult(data);
      if (onNarration) onNarration(data.narration, data.outcome);
    } catch (e) {
      setResult({
        narration: 'The environment resists your attempt — try something else.',
        outcome: { type: 'neutral', description: 'NEUTRAL: no effect', roll: finalRoll },
      });
    } finally {
      setLoading(false);
    }
  };

  const outcomeStyle = result
    ? (OUTCOME_STYLE[result.outcome?.type] || OUTCOME_STYLE.neutral)
    : null;

  return (
    <div
      className="fixed inset-0 z-[300] flex items-center justify-center"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/75 backdrop-blur-sm" />

      <div
        className="relative z-10 max-w-lg w-full mx-4 rounded-2xl border border-slate-600/60 bg-slate-900/98 shadow-2xl overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* top accent */}
        <div className="h-0.5 w-full bg-gradient-to-r from-violet-600 via-blue-500 to-violet-600" />

        <div className="p-5">
          <button onClick={onClose} className="absolute top-3 right-3 text-slate-500 hover:text-white transition-colors">
            <X size={18} />
          </button>

          {/* condition info */}
          <div className="mb-4">
            <div className="text-[10px] uppercase tracking-wider text-violet-400 font-bold mb-1">
              Battlefield Condition
            </div>
            <h3 className="text-white font-bold text-lg mb-1">{condition.title}</h3>
            <p className="text-slate-300 text-sm leading-relaxed">{condition.description}</p>
          </div>

          {/* result area */}
          {result ? (
            <div className="space-y-3">
              <p className="text-slate-100 leading-relaxed text-sm">{result.narration}</p>

              {outcomeStyle && (
                <div className={`flex items-start gap-2 p-3 rounded-xl border ${outcomeStyle.bg}`}>
                  <outcomeStyle.icon size={15} className={`mt-0.5 flex-shrink-0 ${outcomeStyle.color}`} />
                  <div>
                    <div className={`text-xs font-bold ${outcomeStyle.color}`}>{outcomeStyle.label}</div>
                    <div className="text-slate-300 text-xs mt-0.5">{result.outcome?.description}</div>
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-1">
                <button
                  onClick={onClose}
                  className="px-4 py-1.5 rounded-lg bg-violet-700 hover:bg-violet-600 text-white text-sm font-semibold transition-colors"
                >
                  Back to Combat
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {/* player prompt */}
              <div>
                <label className="text-slate-400 text-xs font-semibold uppercase tracking-wider block mb-1.5">
                  How do you use this environment?
                </label>
                <textarea
                  ref={textRef}
                  value={action}
                  onChange={e => setAction(e.target.value)}
                  placeholder={`e.g. "I try to slide through the mud to reach the enemy in the back lane"`}
                  rows={3}
                  className="w-full bg-slate-800 border border-slate-600 rounded-xl px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 resize-none leading-relaxed"
                />
              </div>

              {/* roll section */}
              <div className="flex items-center gap-3">
                <button
                  onClick={handleRoll}
                  disabled={rolling}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 border border-slate-600 hover:border-violet-500 hover:bg-slate-700 text-white text-sm font-semibold transition-all disabled:opacity-50"
                >
                  <Dice6 size={16} className={rolling ? 'animate-spin' : ''} />
                  {roll ? 'Re-roll d20' : 'Roll d20'}
                </button>

                {roll !== null && (
                  <div className="flex flex-col">
                    <span className={`text-2xl leading-none ${rollColor(roll)}`}>{roll}</span>
                    <span className="text-slate-500 text-[10px]">{rollLabel(roll)}</span>
                  </div>
                )}

                {roll === null && (
                  <span className="text-slate-600 text-xs">(auto-rolls if you skip)</span>
                )}
              </div>

              {/* send */}
              <div className="flex justify-end gap-2 pt-1">
                <button
                  onClick={onClose}
                  className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white text-sm transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSend}
                  disabled={loading || !action.trim()}
                  className="flex items-center gap-2 px-5 py-1.5 rounded-lg bg-violet-700 hover:bg-violet-600 text-white text-sm font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {loading && <Loader2 size={14} className="animate-spin" />}
                  {loading ? 'The DM considers...' : 'Send to DM'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConditionInteractionModal;
