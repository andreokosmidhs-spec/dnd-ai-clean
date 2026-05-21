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
  Sword, Shield, Zap, Heart, ChevronRight, Loader2, Send, Plus, X
} from 'lucide-react';
import { useGameState } from '../contexts/GameStateContext';
import { useSessionCore } from '../store/useSessionCore';
import CombatNarrationPopup from './CombatNarrationPopup';
import BattlefieldConditionCard from './BattlefieldConditionCard';
import ConditionInteractionModal from './ConditionInteractionModal';

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
  const [conditions, setConditions] = useState([]);
  const [selectedCondition, setSelectedCondition] = useState(null); // opens interaction modal
  const [showAddCondition, setShowAddCondition] = useState(false);
  const [newCondTitle, setNewCondTitle] = useState('');
  const [newCondDesc, setNewCondDesc] = useState('');
  const [savingCondition, setSavingCondition] = useState(false);
  // Death saves state
  const [deathSaves, setDeathSaves] = useState({ successes: 0, failures: 0, stable: false, dead: false });
  const [deathSaveResult, setDeathSaveResult] = useState(null); // last roll result
  const [rollingDeathSave, setRollingDeathSave] = useState(false);
  // Saving throw modal
  const [showSavingThrowModal, setShowSavingThrowModal] = useState(false);
  const [savingThrowAbility, setSavingThrowAbility] = useState('con');
  const [savingThrowDC, setSavingThrowDC] = useState(15);
  const [savingThrowResult, setSavingThrowResult] = useState(null);
  const [rollingSavingThrow, setRollingSavingThrow] = useState(false);
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

  // Death saves / dying state
  const isPlayerDying = (localCombat.player_dying === true) && !deathSaves.stable && !deathSaves.dead;
  // Action economy
  const playerTurnState = localCombat.player_turn_state || { action_used: false, bonus_action_used: false, reaction_used: false };

  // ── Fetch character deck for action bar ────────────────────────────────────
  useEffect(() => {
    if (!activeCharacterId) return;
    fetch(`${BACKEND_URL}/api/characters/${activeCharacterId}/deck`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.cards) setDeckCards(d.cards.filter(c => c.status === 'active')); })
      .catch(() => {});
  }, [activeCharacterId]);

  // ── Fetch + seed battlefield conditions ────────────────────────────────────
  useEffect(() => {
    if (!campaignId) return;
    const location = worldState?.current_location || worldState?.location || '';
    fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/combat/conditions?location=${encodeURIComponent(location)}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.conditions) setConditions(d.conditions); })
      .catch(() => {});
  }, [campaignId, worldState]);

  // ── Add DM condition ───────────────────────────────────────────────────────
  const handleAddCondition = useCallback(async () => {
    if (!newCondTitle.trim() || !newCondDesc.trim() || !campaignId) return;
    setSavingCondition(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/combat/conditions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newCondTitle.trim(), description: newCondDesc.trim() }),
      });
      const data = await res.json();
      if (data?.condition) {
        setConditions(prev => [...prev, data.condition]);
        setNewCondTitle('');
        setNewCondDesc('');
        setShowAddCondition(false);
      }
    } catch (e) { /* silent */ }
    finally { setSavingCondition(false); }
  }, [campaignId, newCondTitle, newCondDesc]);

  // ── Remove condition ───────────────────────────────────────────────────────
  const handleRemoveCondition = useCallback(async (conditionId) => {
    if (!campaignId) return;
    setConditions(prev => prev.filter(c => (c.condition_id || c.id) !== conditionId));
    fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/combat/conditions/${conditionId}`, { method: 'DELETE' })
      .catch(() => {});
  }, [campaignId]);

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

      // Update local combat state first (round, HP, enemies)
      if (data.combat_state) {
        setLocalCombat(prev => ({ ...prev, ...data.combat_state }));
      }

      // Sync death saves if backend sent them
      if (data.death_saves) {
        setDeathSaves(data.death_saves);
      }

      // Queue player attack popup
      if (data.narration) {
        setNarrationQueue(q => [...q, {
          narration: data.narration,
          mechanics: data.mechanical_summary?.player_attack || data.mechanics || null,
          isEnemy: false,
        }]);
      }

      // Queue individual enemy attack popups (one per enemy, shown sequentially)
      const enemyNarrations = data.enemy_narrations || [];
      enemyNarrations.forEach(en => {
        setNarrationQueue(q => [...q, {
          narration: en.text,
          mechanics: en.mechanics,
          isEnemy: true,
        }]);
      });

      // Combat end checks
      if (data.combat_state?.enemies) {
        const anyAlive = data.combat_state.enemies.some(e => (e.hp ?? 0) > 0);
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
        isEnemy: false,
      }]);
    } finally {
      setLoading(false);
    }
  }, [loading, campaignId, characterState, worldState, localCombat, selectedTarget, allEnemies, onCombatEnd]);

  // ── Death save ────────────────────────────────────────────────────────────
  const handleDeathSave = useCallback(async () => {
    if (rollingDeathSave || !campaignId || !activeCharacterId) return;
    setRollingDeathSave(true);
    setDeathSaveResult(null);
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/combat/death-save`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ character_id: activeCharacterId }),
        }
      );
      const data = await res.json();
      if (data.ok) {
        setDeathSaves(data.death_saves);
        setDeathSaveResult(data.save);
        if (data.combat_state) setLocalCombat(prev => ({ ...prev, ...data.combat_state }));
        if (data.outcome === 'dead' || data.outcome === 'stable' || data.outcome === 'revived') {
          if (data.outcome === 'dead' || data.outcome === 'revived') {
            setTimeout(() => {
              onCombatEnd({
                outcome: data.outcome === 'dead' ? 'player_defeated' : 'victory',
                narration: data.outcome === 'dead'
                  ? 'Your wounds are too great. You breathe your last...'
                  : 'A surge of life-force jolts you back from the edge!',
              });
            }, 1200);
          }
        }
      }
    } catch (e) {
      console.error('Death save failed:', e);
    } finally {
      setRollingDeathSave(false);
    }
  }, [rollingDeathSave, campaignId, activeCharacterId, onCombatEnd]);

  // ── Saving throw ─────────────────────────────────────────────────────────
  const handleSavingThrow = useCallback(async () => {
    if (rollingSavingThrow || !campaignId || !activeCharacterId) return;
    setRollingSavingThrow(true);
    setSavingThrowResult(null);
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/combat/saving-throw`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            character_id: activeCharacterId,
            ability: savingThrowAbility,
            dc: savingThrowDC,
          }),
        }
      );
      const data = await res.json();
      if (data.ok) setSavingThrowResult(data.result);
    } catch (e) {
      console.error('Saving throw failed:', e);
    } finally {
      setRollingSavingThrow(false);
    }
  }, [rollingSavingThrow, campaignId, activeCharacterId, savingThrowAbility, savingThrowDC]);

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

      {/* ── BATTLEFIELD CONDITIONS ────────────────────────────────────────── */}
      {(conditions.length > 0 || true) && (
        <div className="flex-shrink-0 bg-slate-900/60 border-b border-slate-700/40 px-4 py-2">
          <div className="flex items-center gap-2 overflow-x-auto scrollbar-none pb-0.5">
            <span className="flex-shrink-0 text-[10px] uppercase tracking-wider text-slate-500 font-bold">
              Battlefield
            </span>

            {/* condition cards */}
            {conditions.map(c => (
              <div key={c.condition_id || c.id} className="flex-shrink-0 relative group">
                <BattlefieldConditionCard
                  condition={c}
                  compact
                  campaignId={campaignId}
                  onArtGenerated={(condId, url) => {
                    setConditions(prev => prev.map(x =>
                      (x.condition_id || x.id) === condId ? { ...x, art_data_url: url } : x
                    ));
                  }}
                  onClick={() => setSelectedCondition(c)}
                />
                {/* remove button (DM-created only) */}
                {c.source === 'dm' && (
                  <button
                    onClick={e => { e.stopPropagation(); handleRemoveCondition(c.condition_id || c.id); }}
                    className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-700 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <X size={9} />
                  </button>
                )}
              </div>
            ))}

            {/* add condition button */}
            {!showAddCondition && (
              <button
                onClick={() => setShowAddCondition(true)}
                className="flex-shrink-0 flex items-center gap-1 px-2.5 py-1.5 rounded-xl border border-dashed border-slate-600 text-slate-500 hover:border-violet-500 hover:text-violet-400 text-xs transition-all"
              >
                <Plus size={11} /> Add condition
              </button>
            )}

            {/* inline add form */}
            {showAddCondition && (
              <div
                className="flex-shrink-0 flex items-center gap-2 bg-slate-800 border border-violet-700/60 rounded-xl px-3 py-2"
                onClick={e => e.stopPropagation()}
              >
                <div className="flex flex-col gap-1">
                  <input
                    value={newCondTitle}
                    onChange={e => setNewCondTitle(e.target.value)}
                    placeholder="Title (e.g. Oil Slick)"
                    className="bg-slate-700 border border-slate-600 rounded-lg px-2 py-1 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 w-36"
                  />
                  <input
                    value={newCondDesc}
                    onChange={e => setNewCondDesc(e.target.value)}
                    placeholder="Describe the environment..."
                    className="bg-slate-700 border border-slate-600 rounded-lg px-2 py-1 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 w-52"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <button
                    onClick={handleAddCondition}
                    disabled={savingCondition || !newCondTitle.trim() || !newCondDesc.trim()}
                    className="px-2.5 py-1 rounded-lg bg-violet-700 hover:bg-violet-600 text-white text-xs font-semibold disabled:opacity-40 transition-all"
                  >
                    {savingCondition ? <Loader2 size={11} className="animate-spin" /> : 'Add'}
                  </button>
                  <button
                    onClick={() => { setShowAddCondition(false); setNewCondTitle(''); setNewCondDesc(''); }}
                    className="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white text-xs transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

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
        <div className="flex-shrink-0 w-44 bg-slate-900/60 border-l border-slate-700/60 p-3 flex flex-col gap-1.5">
          <div className="text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-1">
            Initiative — Round {round}
          </div>
          {(localCombat.initiative_order || localCombat.turn_order?.map(id => ({ id, name: id, score: null })) || []).map((entry) => {
            const id = entry.id || entry;
            const isP = id === 'player';
            const enemy = allEnemies.find(e => e.id === id);
            const name = entry.name || (isP
              ? (characterState?.identity?.name || characterState?.name || 'You')
              : (enemy?.name || id));
            const score = entry.score ?? null;
            const isActive = activeTurn === id;
            const isDead = !isP && !enemies.find(e => e.id === id);
            return (
              <div
                key={id}
                className={`flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs transition-all ${
                  isActive ? 'bg-violet-800/60 text-white ring-1 ring-violet-500/50' :
                  isDead ? 'opacity-25 line-through text-slate-600' :
                  'text-slate-300 hover:bg-slate-800/40'
                }`}
              >
                <span className="text-sm">{isP ? '🧙' : '💀'}</span>
                <span className="truncate flex-1 leading-tight">{name}</span>
                {score !== null && (
                  <span className={`flex-shrink-0 text-[10px] font-bold tabular-nums ${
                    isActive ? 'text-violet-300' : isDead ? 'text-slate-600' : 'text-slate-500'
                  }`}>
                    {score}
                  </span>
                )}
                {isActive && <ChevronRight size={10} className="text-violet-300 flex-shrink-0" />}
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

        {/* ── Action economy pips ─────────────────────────────────────── */}
        <div className="flex items-center gap-3 text-xs">
          <span className="text-slate-500 text-[10px] uppercase tracking-wider font-bold">Economy</span>
          <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full border transition-all ${
            playerTurnState.action_used
              ? 'border-slate-700 bg-slate-900 text-slate-600'
              : 'border-violet-600 bg-violet-950/40 text-violet-300'
          }`}>
            <Zap size={10} /> Action
          </span>
          <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full border transition-all ${
            playerTurnState.bonus_action_used
              ? 'border-slate-700 bg-slate-900 text-slate-600'
              : 'border-amber-600 bg-amber-950/30 text-amber-300'
          }`}>
            <Sword size={10} /> Bonus
          </span>
          <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full border transition-all ${
            playerTurnState.reaction_used
              ? 'border-slate-700 bg-slate-900 text-slate-600'
              : 'border-blue-600 bg-blue-950/30 text-blue-300'
          }`}>
            <Shield size={10} /> Reaction
          </span>
          <div className="flex-1" />
          {/* Saving Throw button */}
          <button
            onClick={() => { setShowSavingThrowModal(true); setSavingThrowResult(null); }}
            disabled={loading || !isPlayerTurn}
            className="flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-600 text-slate-300 hover:border-violet-500 hover:text-violet-300 transition-all disabled:opacity-40"
          >
            🎲 Save
          </button>
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
          {combatCards.map(card => {
            const actionIcon = card.action_cost === 'bonus_action' ? '✦'
              : card.action_cost === 'reaction' ? '⚙'
              : card.action_cost === 'free' ? '∅'
              : card.action_cost === 'action' ? '⚡'
              : null;
            const comps = card.components || {};
            // M badge is amber when it has a gp cost (costly component)
            const mText = typeof comps.M === 'string' ? comps.M : '';
            const mIsCostly = /\d+\s*(?:,\d+)?\s*gp/i.test(mText);
            const compBadges = [
              comps.V && { label: 'V', costly: false },
              comps.S && { label: 'S', costly: false },
              comps.M && { label: 'M', costly: mIsCostly, title: mText },
            ].filter(Boolean);
            return (
            <button
              key={card.id}
              onClick={() => handleCardClick(card)}
              disabled={loading || !isPlayerTurn || card.status === 'spent'}
              className={`
                flex-shrink-0 flex flex-col items-start px-3 py-2 rounded-xl border text-left
                transition-all min-w-[110px] max-w-[160px]
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
              {/* title + action cost */}
              <div className="flex items-center gap-1 w-full">
                {actionIcon && (
                  <span className={`text-[11px] font-bold shrink-0 ${
                    card.action_cost === 'bonus_action' ? 'text-yellow-400'
                    : card.action_cost === 'reaction' ? 'text-orange-400'
                    : card.action_cost === 'free' ? 'text-slate-400'
                    : 'text-violet-400'
                  }`}>{actionIcon}</span>
                )}
                <span className="text-white text-xs font-semibold leading-tight truncate">{card.title}</span>
              </div>
              {/* component badges + concentration */}
              {(compBadges.length > 0 || card.concentration || card.ritual) && (
                <div className="flex items-center gap-0.5 mt-0.5 flex-wrap">
                  {compBadges.map(b => (
                    <span
                      key={b.label}
                      title={b.title || undefined}
                      className={`text-[9px] font-bold px-1 rounded leading-tight ${
                        b.costly
                          ? 'bg-amber-900/60 text-amber-300 ring-1 ring-amber-600/50'
                          : 'bg-slate-700/60 text-slate-300'
                      }`}
                    >{b.label}</span>
                  ))}
                  {card.concentration && (
                    <span className="text-[9px] font-bold px-1 rounded bg-blue-900/60 text-blue-300 leading-tight">C</span>
                  )}
                  {card.ritual && (
                    <span className="text-[9px] font-bold px-1 rounded bg-amber-900/60 text-amber-300 leading-tight">R</span>
                  )}
                </div>
              )}
              {/* range */}
              {card.range && (
                <span className="text-slate-500 text-[9px] mt-0.5 leading-tight">{card.range}</span>
              )}
              {/* uses */}
              {card.uses_max > 0 && (
                <span className={`text-[10px] mt-0.5 font-bold ${
                  card.uses_remaining === 0 ? 'text-red-400' : 'text-green-400'
                }`}>
                  {card.uses_remaining}/{card.uses_max}
                </span>
              )}
            </button>
            );
          })}

          {combatCards.length === 0 && (
            <div className="text-slate-600 text-xs py-2">No usable cards — type an action below</div>
          )}
        </div>

        {/* ── Death Save UI (shown when player is dying) or normal actions ── */}
        {isPlayerDying ? (
          <div className="flex flex-col gap-2">
            <div className="text-center text-red-400 text-xs font-bold uppercase tracking-wider animate-pulse">
              Dying — Roll Death Saving Throws
            </div>
            <div className="flex items-center justify-center gap-6">
              {/* Successes */}
              <div className="flex flex-col items-center gap-1">
                <span className="text-green-400 text-[10px] font-bold">Successes</span>
                <div className="flex gap-1.5">
                  {[0, 1, 2].map(i => (
                    <div key={i} className={`w-5 h-5 rounded-full border-2 flex items-center justify-center text-[11px] ${
                      i < deathSaves.successes
                        ? 'border-green-500 bg-green-900/60 text-green-300'
                        : 'border-slate-600 bg-slate-900'
                    }`}>
                      {i < deathSaves.successes ? '✓' : ''}
                    </div>
                  ))}
                </div>
              </div>

              {/* Roll button + last result */}
              <div className="flex flex-col items-center gap-1">
                <button
                  onClick={handleDeathSave}
                  disabled={rollingDeathSave}
                  className="px-4 py-2 rounded-xl bg-red-800 hover:bg-red-700 text-white text-sm font-bold border border-red-600 transition-all disabled:opacity-50"
                >
                  {rollingDeathSave
                    ? <Loader2 size={16} className="animate-spin inline" />
                    : '🎲 Roll Death Save'}
                </button>
                {deathSaveResult && (
                  <span className={`text-xs font-bold ${
                    deathSaveResult.result === 'critical_success' ? 'text-green-300' :
                    deathSaveResult.result === 'success' ? 'text-green-400' :
                    deathSaveResult.result === 'critical_failure' ? 'text-red-300' : 'text-red-400'
                  }`}>
                    Rolled {deathSaveResult.roll} — {
                      deathSaveResult.result === 'critical_success' ? 'NAT 20! Revived!' :
                      deathSaveResult.result === 'critical_failure' ? 'NAT 1! −2 failures' :
                      deathSaveResult.result === 'success' ? 'Success' : 'Failure'
                    }
                  </span>
                )}
              </div>

              {/* Failures */}
              <div className="flex flex-col items-center gap-1">
                <span className="text-red-400 text-[10px] font-bold">Failures</span>
                <div className="flex gap-1.5">
                  {[0, 1, 2].map(i => (
                    <div key={i} className={`w-5 h-5 rounded-full border-2 flex items-center justify-center text-[11px] ${
                      i < deathSaves.failures
                        ? 'border-red-500 bg-red-900/60 text-red-300'
                        : 'border-slate-600 bg-slate-900'
                    }`}>
                      {i < deathSaves.failures ? '✕' : ''}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
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
        )}
      </div>

      {/* ── NARRATION POPUP ──────────────────────────────────────────────── */}
      {narrationQueue.length > 0 && (
        <CombatNarrationPopup
          narration={narrationQueue[0].narration}
          mechanics={narrationQueue[0].mechanics}
          isEnemy={narrationQueue[0].isEnemy || false}
          onDismiss={dismissPopup}
        />
      )}

      {/* ── CONDITION INTERACTION MODAL ──────────────────────────────────── */}
      {selectedCondition && (
        <ConditionInteractionModal
          condition={selectedCondition}
          campaignId={campaignId}
          characterState={characterState}
          combatState={localCombat}
          characterId={activeCharacterId}
          onClose={() => setSelectedCondition(null)}
          onNarration={(narration, outcome) => {
            setSelectedCondition(null);
            setNarrationQueue(q => [...q, { narration, mechanics: { light_note: outcome?.description } }]);
          }}
        />
      )}

      {/* ── SAVING THROW MODAL ───────────────────────────────────────────── */}
      {showSavingThrowModal && (
        <div className="fixed inset-0 z-60 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-violet-700/60 rounded-2xl p-6 w-80 shadow-2xl">
            <div className="text-white font-bold text-lg mb-4 flex items-center gap-2">
              🎲 Saving Throw
            </div>

            {!savingThrowResult ? (
              <>
                {/* Ability selector */}
                <div className="mb-4">
                  <label className="text-slate-400 text-xs mb-1.5 block">Ability</label>
                  <div className="grid grid-cols-3 gap-1.5">
                    {['str', 'dex', 'con', 'int', 'wis', 'cha'].map(ab => (
                      <button
                        key={ab}
                        onClick={() => setSavingThrowAbility(ab)}
                        className={`py-1 rounded-lg text-xs font-bold uppercase transition-all ${
                          savingThrowAbility === ab
                            ? 'bg-violet-700 text-white border border-violet-500'
                            : 'bg-slate-800 text-slate-400 border border-slate-700 hover:border-violet-500'
                        }`}
                      >
                        {ab}
                      </button>
                    ))}
                  </div>
                </div>

                {/* DC input */}
                <div className="mb-5">
                  <label className="text-slate-400 text-xs mb-1.5 block">DC (Difficulty Class)</label>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setSavingThrowDC(d => Math.max(5, d - 1))}
                      className="w-8 h-8 rounded-lg bg-slate-800 text-white hover:bg-slate-700 font-bold text-lg leading-none"
                    >−</button>
                    <span className="flex-1 text-center text-white font-bold text-xl">{savingThrowDC}</span>
                    <button
                      onClick={() => setSavingThrowDC(d => Math.min(30, d + 1))}
                      className="w-8 h-8 rounded-lg bg-slate-800 text-white hover:bg-slate-700 font-bold text-lg leading-none"
                    >+</button>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={handleSavingThrow}
                    disabled={rollingSavingThrow}
                    className="flex-1 py-2 rounded-xl bg-violet-700 hover:bg-violet-600 text-white font-bold text-sm transition-all disabled:opacity-50"
                  >
                    {rollingSavingThrow ? <Loader2 size={16} className="animate-spin inline" /> : 'Roll'}
                  </button>
                  <button
                    onClick={() => { setShowSavingThrowModal(false); setSavingThrowResult(null); }}
                    className="px-4 py-2 rounded-xl bg-slate-800 text-slate-400 hover:text-white text-sm transition-all"
                  >
                    Cancel
                  </button>
                </div>
              </>
            ) : (
              <div className="text-center">
                <div className={`text-5xl font-black mb-2 ${savingThrowResult.success ? 'text-green-400' : 'text-red-400'}`}>
                  {savingThrowResult.roll}
                </div>
                <div className={`text-lg font-bold mb-1 ${savingThrowResult.success ? 'text-green-300' : 'text-red-300'}`}>
                  {savingThrowResult.success ? 'Success!' : 'Failure'}
                </div>
                <div className="text-slate-400 text-sm mb-1">
                  {savingThrowResult.ability} save — total {savingThrowResult.total} vs DC {savingThrowResult.dc}
                </div>
                <div className="text-slate-500 text-xs mb-5">
                  Roll {savingThrowResult.roll} + {savingThrowResult.modifier} mod
                  {savingThrowResult.proficient ? ` + ${savingThrowResult.prof_bonus} prof` : ''}
                  {' '}= {savingThrowResult.total}
                </div>
                <button
                  onClick={() => { setShowSavingThrowModal(false); setSavingThrowResult(null); }}
                  className="px-6 py-2 rounded-xl bg-slate-800 text-white hover:bg-slate-700 text-sm transition-all"
                >
                  Done
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CombatScreen;
