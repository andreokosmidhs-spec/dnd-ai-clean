/**
 * CombatScreen — full-screen takeover rendered by RPGGame when combat is active.
 *
 * Layout:
 *  TOP BAR  — battlefield name, light level, round counter, passive conditions
 *  LANE GRID — 4 columns (Melee / Close / Medium / Far) with participant tokens
 *  RIGHT SIDEBAR — initiative order
 *  BOTTOM BAR — player stats, available cards & actions, text input
 *  POPUP — CombatNarrationPopup overlaid when narration arrives
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Sword, Shield, Zap, Heart, Eye, Wind, FlameKindling,
  ChevronRight, Loader2, Send, SkipForward
} from 'lucide-react';
import { useGameState } from '../contexts/GameStateContext';
import { useSessionCore } from '../store/useSessionCore';
import CombatNarrationPopup from './CombatNarrationPopup';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// ── Light level helpers ───────────────────────────────────────────────────────
function deriveLightLevel(timeOfDay, locationName) {
  const t = (timeOfDay || '').toLowerCase();
  const loc = (locationName || '').toLowerCase();

  if (loc.match(/cave|cavern|dungeon|mine|crypt|tomb|sewer|underground|basement|cellar|vault/)) {
    return { level: 'dark', icon: '🌑', label: 'Darkness', overlay: 'dark' };
  }
  if (t.match(/^(night|midnight)/)) {
    return { level: 'dark', icon: '🌑', label: 'Darkness', overlay: 'dark' };
  }
  if (t.match(/dawn|dusk|evening|late.afternoon/)) {
    return { level: 'dim', icon: '🌙', label: 'Dim Light', overlay: 'dim' };
  }
  return { level: 'bright', icon: '☀️', label: 'Bright Light', overlay: null };
}

function lightChipColor(level) {
  if (level === 'dark') return 'bg-slate-800 text-orange-300 border-orange-800';
  if (level === 'dim') return 'bg-slate-800 text-yellow-300 border-yellow-800';
  return 'bg-slate-800 text-green-300 border-green-800';
}

// ── Lane config ───────────────────────────────────────────────────────────────
const LANES = [
  { id: 1, label: 'Melee', sub: '≤5 ft', color: 'border-red-900/40' },
  { id: 2, label: 'Close', sub: '5-30 ft', color: 'border-orange-900/40' },
  { id: 3, label: 'Medium', sub: '30-60 ft', color: 'border-yellow-900/40' },
  { id: 4, label: 'Far', sub: '60+ ft', color: 'border-blue-900/40' },
];

// ── Participant token ─────────────────────────────────────────────────────────
const ParticipantToken = ({ participant, isActive, isPlayer, isTarget, onClick }) => {
  const hp = participant.hp ?? participant.hp_current ?? 0;
  const maxHp = participant.max_hp ?? participant.hp_max ?? hp;
  const pct = maxHp > 0 ? Math.max(0, (hp / maxHp) * 100) : 0;
  const hpColor = pct > 60 ? 'bg-green-500' : pct > 30 ? 'bg-yellow-500' : 'bg-red-500';
  const conditions = participant.conditions || [];

  return (
    <div
      onClick={onClick}
      className={`
        relative rounded-xl border p-3 cursor-pointer select-none transition-all
        ${isPlayer
          ? 'border-violet-500/70 bg-violet-950/50'
          : isTarget
            ? 'border-red-400/80 bg-red-950/40 ring-2 ring-red-500/30'
            : 'border-slate-700/60 bg-slate-900/60 hover:border-slate-500/80'}
        ${isActive ? 'shadow-[0_0_12px_2px_rgba(167,139,250,0.3)]' : ''}
      `}
    >
      {/* type icon */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{isPlayer ? '🧙' : '💀'}</span>
        <span className="text-white text-sm font-semibold truncate flex-1">
          {participant.name || (isPlayer ? 'You' : 'Enemy')}
        </span>
        {isActive && (
          <span className="text-[10px] text-violet-300 font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-violet-900/60">
            Turn
          </span>
        )}
      </div>

      {/* HP bar */}
      <div className="mb-1">
        <div className="h-2 bg-slate-700/80 rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all duration-500 ${hpColor}`} style={{ width: `${pct}%` }} />
        </div>
        <div className="flex justify-between text-[11px] text-slate-400 mt-0.5">
          <span>{hp}</span>
          <span>{maxHp} HP</span>
        </div>
      </div>

      {/* conditions */}
      {conditions.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1">
          {conditions.map(c => (
            <span key={c} className="text-[10px] px-1.5 py-0.5 rounded bg-amber-900/60 text-amber-300 border border-amber-700/50">
              {c}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

// ── Main component ────────────────────────────────────────────────────────────
const CombatScreen = ({ combatState, onCombatEnd }) => {
  const { characterState, worldState, campaignId } = useGameState();
  const { activeCharacterId } = useSessionCore();

  const [localCombat, setLocalCombat] = useState(combatState || {});
  const [selectedTarget, setSelectedTarget] = useState(null);
  const [playerLane, setPlayerLane] = useState(combatState?.player_lane ?? 1);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [narrationQueue, setNarrationQueue] = useState([]); // [{narration, mechanics}]
  const [deckCards, setDeckCards] = useState([]);
  const [activeCardFilter, setActiveCardFilter] = useState('all'); // 'all'|'spell'|'class'|'item'
  const inputRef = useRef();

  // Light level — prefer backend data, fall back to client derivation
  const lightLevel = localCombat.light_level
    || deriveLightLevel(worldState?.time_of_day, worldState?.current_location || worldState?.location);

  const battlefield = localCombat.battlefield || {};
  const enemies = (localCombat.enemies || []).filter(e => (e.hp ?? e.hp_current ?? 1) > 0);
  const allEnemies = localCombat.enemies || [];
  const round = localCombat.round || 1;
  const activeTurn = localCombat.active_turn || 'player';
  const isPlayerTurn = activeTurn === 'player';

  // ── Fetch character deck for action bar ────────────────────────────────────
  useEffect(() => {
    if (!activeCharacterId) return;
    fetch(`${BACKEND_URL}/api/characters/${activeCharacterId}/deck`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.cards) setDeckCards(d.cards.filter(c => c.status === 'active')); })
      .catch(() => {});
  }, [activeCharacterId]);

  // ── Auto-select first enemy as target ─────────────────────────────────────
  useEffect(() => {
    if (!selectedTarget && enemies.length > 0) {
      setSelectedTarget(enemies[0].id);
    }
  }, [enemies, selectedTarget]);

  // ── Build lane → participants map ─────────────────────────────────────────
  const laneMap = { 1: [], 2: [], 3: [], 4: [] };
  laneMap[playerLane].push({
    id: 'player',
    name: characterState?.identity?.name || characterState?.name || 'You',
    hp: characterState?.hp?.current ?? characterState?.hp ?? 10,
    max_hp: characterState?.hp?.max ?? characterState?.max_hp ?? 10,
    ac: characterState?.ac ?? 10,
    conditions: characterState?.conditions || [],
    _isPlayer: true,
  });
  allEnemies.forEach(e => {
    const lane = Math.min(4, Math.max(1, e.lane || 2));
    laneMap[lane].push(e);
  });

  // ── Cards filtered for combat ─────────────────────────────────────────────
  const combatCards = deckCards.filter(c => {
    if (activeCardFilter === 'spell') return c.source === 'spell';
    if (activeCardFilter === 'class') return c.source === 'class';
    if (activeCardFilter === 'item') return c.source === 'item';
    // 'all': show anything with a mechanical effect that makes sense in combat
    return c.mechanical && c.source !== 'language' && c.source !== 'background';
  }).slice(0, 12);

  // ── Has darkvision ────────────────────────────────────────────────────────
  const hasDarkvision = deckCards.some(c =>
    (c.title || '').toLowerCase().includes('darkvision')
  );
  const effectiveLightLevel = (lightLevel.level === 'dark' && hasDarkvision)
    ? 'dim' : lightLevel.level;

  // ── Darkvision negates darkness penalty notice ────────────────────────────
  const lightNote = effectiveLightLevel === 'dark'
    ? 'No darkvision — attacks at disadvantage'
    : hasDarkvision && lightLevel.level === 'dark'
      ? 'Darkvision active — darkness treated as dim light'
      : null;

  // ── Send combat action ────────────────────────────────────────────────────
  const sendAction = useCallback(async (actionText, cardId = null) => {
    if (!actionText.trim() || loading) return;
    setLoading(true);
    setInput('');

    const endpoint = campaignId
      ? `${BACKEND_URL}/api/campaigns/${campaignId}/dm/action`
      : `${BACKEND_URL}/api/rpg_dm/action`;

    const targetEnemy = allEnemies.find(e => e.id === selectedTarget);
    const payload = {
      player_action: actionText,
      character_state: characterState,
      world_state: worldState,
      campaign_id: campaignId,
      combat_state: localCombat,
      target_id: selectedTarget,
      target_name: targetEnemy?.name,
      card_used: cardId,
      is_combat: true,
    };

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      // Queue narration popup
      if (data.narration) {
        setNarrationQueue(q => [...q, {
          narration: data.narration,
          mechanics: data.mechanical_summary || data.mechanics || null,
        }]);
      }

      // Update local combat state
      if (data.combat_state) {
        setLocalCombat(prev => ({ ...prev, ...data.combat_state }));
      }
      if (data.combat_state?.enemies) {
        const newEnemies = data.combat_state.enemies;
        const anyAlive = newEnemies.some(e => (e.hp ?? 0) > 0);
        if (!anyAlive || data.combat_over) {
          setTimeout(() => {
            onCombatEnd({
              outcome: data.outcome || (anyAlive ? 'fled' : 'victory'),
              narration: data.narration,
            });
          }, 800);
        }
      }
      if (data.combat_over) {
        setTimeout(() => {
          onCombatEnd({ outcome: data.outcome || 'victory', narration: data.narration });
        }, 800);
      }

      // Mark card spent if used
      if (cardId) {
        setDeckCards(prev => prev.map(c =>
          c.id === cardId ? { ...c, status: c.uses_max > 1 ? c.status : 'spent' } : c
        ));
      }
    } catch (e) {
      console.error('Combat action failed:', e);
      setNarrationQueue(q => [...q, {
        narration: 'The action could not be resolved. Try again.',
        mechanics: null,
      }]);
    } finally {
      setLoading(false);
    }
  }, [loading, campaignId, characterState, worldState, localCombat, selectedTarget, allEnemies, onCombatEnd]);

  // ── Card click → prefill action ───────────────────────────────────────────
  const handleCardClick = (card) => {
    const target = allEnemies.find(e => e.id === selectedTarget);
    const targetName = target?.name || 'enemy';
    const actionText = `I use ${card.title}${card.mechanical ? ` (${card.mechanical})` : ''} against ${targetName}`;
    sendAction(actionText, card.id);
  };

  // ── Dismiss first popup in queue ──────────────────────────────────────────
  const dismissPopup = () => setNarrationQueue(q => q.slice(1));

  // ── Overlay class by light level ──────────────────────────────────────────
  const overlayClass =
    lightLevel.overlay === 'dark' ? 'after:absolute after:inset-0 after:bg-slate-950/40 after:pointer-events-none after:rounded-lg' :
    lightLevel.overlay === 'dim'  ? 'after:absolute after:inset-0 after:bg-slate-900/20 after:pointer-events-none after:rounded-lg' :
    '';

  return (
    <div className="fixed inset-0 z-50 bg-slate-950 flex flex-col overflow-hidden">

      {/* ── TOP BAR ──────────────────────────────────────────────────────── */}
      <div className="flex-shrink-0 bg-slate-900/90 border-b border-slate-700/60 px-4 py-2.5">
        <div className="flex items-center gap-3 flex-wrap">
          {/* combat icon + battlefield name */}
          <div className="flex items-center gap-2">
            <Sword className="text-red-400" size={18} />
            <span className="text-white font-bold text-sm">
              {battlefield.name || worldState?.current_location || 'Combat'}
            </span>
          </div>

          {/* round */}
          <span className="text-slate-400 text-xs">Round {round}</span>

          <div className="flex-1" />

          {/* light level chip */}
          <span className={`text-xs px-2.5 py-1 rounded-full border ${lightChipColor(effectiveLightLevel)}`}>
            {lightLevel.icon} {lightLevel.label}
            {hasDarkvision && lightLevel.level === 'dark' && ' (Darkvision)'}
          </span>

          {/* turn indicator */}
          <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
            isPlayerTurn ? 'bg-violet-700/70 text-violet-200' : 'bg-slate-700/70 text-slate-300'
          }`}>
            {isPlayerTurn ? '⚡ Your Turn' : `⏳ ${activeTurn}'s Turn`}
          </span>
        </div>

        {/* passive conditions row */}
        {(battlefield.passive_conditions?.length > 0 || lightNote) && (
          <div className="flex flex-wrap gap-2 mt-1.5">
            {(battlefield.passive_conditions || []).map((c, i) => (
              <span key={i} className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-600/50">
                {c}
              </span>
            ))}
            {lightNote && (
              <span className="text-[11px] px-2 py-0.5 rounded bg-amber-900/40 text-amber-300 border border-amber-700/50">
                🌙 {lightNote}
              </span>
            )}
          </div>
        )}
      </div>

      {/* ── MAIN AREA: lanes + sidebar ────────────────────────────────────── */}
      <div className="flex flex-1 min-h-0 overflow-hidden">

        {/* Lane grid */}
        <div className={`flex flex-1 min-w-0 gap-0 p-3 relative ${overlayClass}`}>
          {LANES.map(lane => (
            <div
              key={lane.id}
              className={`flex-1 flex flex-col gap-2 px-2 border-r last:border-r-0 ${lane.color} relative`}
            >
              {/* lane header */}
              <div className="text-center pb-1 border-b border-slate-800/60">
                <div className="text-slate-300 text-xs font-bold">{lane.label}</div>
                <div className="text-slate-500 text-[10px]">{lane.sub}</div>
              </div>

              {/* lane darkness overlay for 'dark' */}
              {lightLevel.overlay === 'dark' && lane.id >= 3 && (
                <div className="absolute inset-0 top-10 bg-slate-950/50 rounded pointer-events-none z-10" />
              )}

              {/* participants in this lane */}
              {(laneMap[lane.id] || []).map(p => (
                <ParticipantToken
                  key={p.id}
                  participant={p}
                  isPlayer={p._isPlayer}
                  isActive={activeTurn === (p._isPlayer ? 'player' : p.id)}
                  isTarget={!p._isPlayer && p.id === selectedTarget}
                  onClick={() => !p._isPlayer && setSelectedTarget(p.id)}
                />
              ))}

              {/* empty lane hint */}
              {(laneMap[lane.id] || []).length === 0 && (
                <div className="text-slate-700 text-[11px] text-center py-4">— empty —</div>
              )}
            </div>
          ))}
        </div>

        {/* Initiative sidebar */}
        <div className="flex-shrink-0 w-44 bg-slate-900/60 border-l border-slate-700/60 p-3 flex flex-col gap-2">
          <div className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Initiative</div>
          {(localCombat.turn_order || ['player']).map((id, idx) => {
            const isP = id === 'player';
            const enemy = allEnemies.find(e => e.id === id);
            const name = isP
              ? (characterState?.identity?.name || characterState?.name || 'You')
              : (enemy?.name || id);
            const isActive = activeTurn === id;
            const isDead = !isP && !enemies.find(e => e.id === id);
            return (
              <div
                key={id}
                className={`flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm transition-all ${
                  isActive ? 'bg-violet-800/50 text-white' :
                  isDead ? 'opacity-30 line-through text-slate-500' :
                  'text-slate-300'
                }`}
              >
                <span className="text-base">{isP ? '🧙' : '💀'}</span>
                <span className="truncate flex-1">{name}</span>
                {isActive && <ChevronRight size={12} className="text-violet-300 flex-shrink-0" />}
                {idx === 0 && !isActive && <span className="text-[10px] text-slate-500">{idx + 1}</span>}
              </div>
            );
          })}
        </div>
      </div>

      {/* ── BOTTOM BAR ───────────────────────────────────────────────────── */}
      <div className="flex-shrink-0 bg-slate-900/95 border-t border-slate-700/60 px-4 py-3 space-y-3">

        {/* player mini-stats */}
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1.5">
            <Heart size={14} className="text-red-400" />
            <span className="text-white font-bold">
              {characterState?.hp?.current ?? characterState?.hp ?? '?'}/{characterState?.hp?.max ?? characterState?.max_hp ?? '?'}
            </span>
            <span className="text-slate-500 text-xs">HP</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Shield size={14} className="text-blue-400" />
            <span className="text-white font-bold">{characterState?.ac ?? '?'}</span>
            <span className="text-slate-500 text-xs">AC</span>
          </div>
          {(characterState?.conditions || []).map(c => (
            <span key={c} className="text-xs px-2 py-0.5 rounded bg-amber-900/50 text-amber-300 border border-amber-700/40">
              {c}
            </span>
          ))}
          {/* player lane control */}
          <div className="ml-auto flex items-center gap-1.5">
            <span className="text-slate-500 text-xs">Lane:</span>
            {LANES.map(l => (
              <button
                key={l.id}
                onClick={() => setPlayerLane(l.id)}
                className={`text-xs px-2 py-0.5 rounded transition-all ${
                  playerLane === l.id
                    ? 'bg-violet-700 text-white'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                {l.id}
              </button>
            ))}
          </div>
        </div>

        {/* card filter tabs */}
        <div className="flex items-center gap-2">
          {['all', 'spell', 'class', 'item'].map(f => (
            <button
              key={f}
              onClick={() => setActiveCardFilter(f)}
              className={`text-xs px-2.5 py-1 rounded-full capitalize transition-all ${
                activeCardFilter === f
                  ? 'bg-violet-700 text-white'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {f}
            </button>
          ))}
          <span className="text-slate-600 text-xs ml-auto">Click a card to use it</span>
        </div>

        {/* card chips */}
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-slate-700">
          {combatCards.map(card => (
            <button
              key={card.id}
              onClick={() => handleCardClick(card)}
              disabled={loading || !isPlayerTurn || card.status === 'spent'}
              className={`
                flex-shrink-0 flex flex-col items-start px-3 py-2 rounded-xl border text-left
                transition-all min-w-[110px] max-w-[150px]
                ${card.status === 'spent'
                  ? 'border-slate-700 bg-slate-900 opacity-40 cursor-not-allowed'
                  : card.source === 'spell'
                    ? 'border-blue-700/60 bg-blue-950/40 hover:border-blue-500 hover:bg-blue-900/40 cursor-pointer'
                    : card.source === 'class'
                      ? 'border-violet-700/60 bg-violet-950/40 hover:border-violet-500 cursor-pointer'
                      : 'border-slate-600/60 bg-slate-900/60 hover:border-slate-400 cursor-pointer'}
                ${!isPlayerTurn ? 'cursor-not-allowed opacity-60' : ''}
              `}
            >
              <span className="text-white text-xs font-semibold leading-tight">{card.title}</span>
              {card.mechanical && (
                <span className="text-slate-400 text-[10px] mt-0.5 line-clamp-2 leading-tight">
                  {card.mechanical}
                </span>
              )}
              {card.uses_max > 0 && (
                <span className={`text-[10px] mt-1 font-bold ${
                  card.uses_remaining === 0 ? 'text-red-400' : 'text-green-400'
                }`}>
                  {card.uses_remaining}/{card.uses_max}
                </span>
              )}
            </button>
          ))}

          {combatCards.length === 0 && (
            <div className="text-slate-600 text-xs py-2">No usable cards — type an action below</div>
          )}
        </div>

        {/* standard action buttons */}
        <div className="flex items-center gap-2">
          {[
            { label: '⚔ Attack', action: `I attack ${allEnemies.find(e => e.id === selectedTarget)?.name || 'the enemy'}` },
            { label: '🛡 Defend', action: 'I take the Dodge action, focusing on defense' },
            { label: '💨 Disengage', action: 'I disengage and move back a lane' },
            { label: '🔍 Dash', action: 'I dash forward to close the distance' },
            { label: '🚪 Flee', action: 'I try to flee from combat' },
          ].map(({ label, action }) => (
            <button
              key={label}
              onClick={() => sendAction(action)}
              disabled={loading || !isPlayerTurn}
              className="flex-shrink-0 text-xs px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {label}
            </button>
          ))}

          <div className="flex-1" />

          {/* free-form input */}
          <div className="flex items-center gap-2 flex-1 max-w-sm">
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), sendAction(input))}
              placeholder={isPlayerTurn ? 'Type an action...' : "Enemies are acting..."}
              disabled={loading || !isPlayerTurn}
              className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 disabled:opacity-50"
            />
            <button
              onClick={() => sendAction(input)}
              disabled={loading || !isPlayerTurn || !input.trim()}
              className="p-1.5 rounded-lg bg-violet-700 hover:bg-violet-600 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </div>
        </div>
      </div>

      {/* ── NARRATION POPUP ──────────────────────────────────────────────── */}
      {narrationQueue.length > 0 && (
        <CombatNarrationPopup
          narration={narrationQueue[0].narration}
          mechanics={narrationQueue[0].mechanics}
          onDismiss={dismissPopup}
        />
      )}
    </div>
  );
};

export default CombatScreen;
