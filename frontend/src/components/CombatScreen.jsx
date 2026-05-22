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
import BattlefieldGrid from './BattlefieldGrid';
import EnemyLibraryPanel from './EnemyLibraryPanel';

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

// Lane config retained for quick-action labels; visual rendering uses BattlefieldGrid
const LANES = [
  { id: 1, label: 'Melee', sub: '≤5 ft' },
  { id: 2, label: 'Close', sub: '5-30 ft' },
  { id: 3, label: 'Medium', sub: '30-60 ft' },
  { id: 4, label: 'Far', sub: '60+ ft' },
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
  const [playerGridX, setPlayerGridX] = useState(combatState?.player_grid_x ?? 1);
  const [playerGridY, setPlayerGridY] = useState(combatState?.player_grid_y ?? 2);
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
  // Spell slots
  const [spellSlots, setSpellSlots] = useState({});
  const [spellSlotsMax, setSpellSlotsMax] = useState({});
  // Concentration
  const [concentrationSpell, setConcentrationSpell] = useState(null);
  const [rollingDeathSave, setRollingDeathSave] = useState(false);
  // Saving throw modal
  const [showSavingThrowModal, setShowSavingThrowModal] = useState(false);
  const [savingThrowAbility, setSavingThrowAbility] = useState('con');
  const [savingThrowDC, setSavingThrowDC] = useState(15);
  const [savingThrowResult, setSavingThrowResult] = useState(null);
  const [rollingSavingThrow, setRollingSavingThrow] = useState(false);
  const inputRef = useRef();

  // ── DM grid-editing tools ─────────────────────────────────────────────────
  const [showEnemyLibrary, setShowEnemyLibrary] = useState(false);
  const [showDmTools, setShowDmTools]   = useState(false);
  const [editMode, setEditMode]         = useState(null);  // 'terrain'|'spell'|'measure'|'erase'|null
  const [activeBrush, setActiveBrush]   = useState('wall');
  const [cellOverrides, setCellOverrides] = useState(
    () => combatState?.cell_overrides ?? []
  );
  const [spellZones, setSpellZones]     = useState(
    () => combatState?.spell_zones ?? []
  );
  const [pendingSpell, setPendingSpell] = useState(null);  // { name, radius, color, shape }
  const [measureFrom, setMeasureFrom]   = useState(null);  // { x, y }
  const [showAoO, setShowAoO]           = useState(false);
  const [savingGrid, setSavingGrid]     = useState(false);
  const [customSpellRadius, setCustomSpellRadius] = useState(4);

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

  // ── Equipment state ────────────────────────────────────────────────────────
  const [equipment, setEquipment] = useState({ main_hand: null, off_hand: null, armor: null, two_handed: false });
  const [equipAC, setEquipAC] = useState(null);
  const [freeHand, setFreeHand] = useState(true);
  const [equipInventory, setEquipInventory] = useState([]);
  const [showEquipPanel, setShowEquipPanel] = useState(false);

  const fetchEquipment = useCallback(() => {
    if (!campaignId || !activeCharacterId) return;
    fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/characters/${activeCharacterId}/equipment`)
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!d) return;
        setEquipment(d.equipment || {});
        setEquipAC(d.ac);
        setFreeHand(d.free_hand);
        setEquipInventory(d.inventory || []);
      })
      .catch(() => {});
  }, [campaignId, activeCharacterId]);

  useEffect(() => { fetchEquipment(); }, [fetchEquipment]);

  // Initialise spell slots from characterState
  useEffect(() => {
    if (characterState?.spell_slots) setSpellSlots(characterState.spell_slots);
    if (characterState?.spell_slots_max) setSpellSlotsMax(characterState.spell_slots_max);
    if (characterState?.concentration_spell !== undefined)
      setConcentrationSpell(characterState.concentration_spell || null);
  }, [characterState]);

  const handleEquip = useCallback(async (slot, itemName, twoHanded = false) => {
    if (!campaignId || !activeCharacterId) return;
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/characters/${activeCharacterId}/equipment`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ slot, item_name: itemName, two_handed: twoHanded }),
        }
      );
      if (!res.ok) return;
      const d = await res.json();
      setEquipment(d.equipment || {});
      setEquipAC(d.ac);
      setFreeHand(d.free_hand);
      setEquipInventory(d.inventory || []);
    } catch (e) { /* ignore */ }
  }, [campaignId, activeCharacterId]);

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

  // ── DM grid handlers ─────────────────────────────────────────────────────
  const handleCellInteract = useCallback((x, y) => {
    if (editMode === 'terrain') {
      setCellOverrides(prev => {
        const filtered = prev.filter(c => !(c.x === x && c.y === y));
        return [...filtered, { x, y, type: activeBrush }];
      });
    } else if (editMode === 'erase') {
      setCellOverrides(prev => prev.filter(c => !(c.x === x && c.y === y)));
    } else if (editMode === 'spell' && pendingSpell) {
      setSpellZones(prev => [...prev, {
        id: `zone_${Date.now()}`,
        name: pendingSpell.name,
        cx: x, cy: y,
        radius: pendingSpell.radius,
        color:  pendingSpell.color,
        shape:  pendingSpell.shape || 'circle',
      }]);
    } else if (editMode === 'measure') {
      setMeasureFrom(prev => (prev?.x === x && prev?.y === y) ? null : { x, y });
    }
  }, [editMode, activeBrush, pendingSpell]);

  const saveGridChanges = useCallback(async () => {
    if (!campaignId || savingGrid) return;
    setSavingGrid(true);
    try {
      await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/combat/grid`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cell_overrides: cellOverrides,
          spell_zones: spellZones,
          character_id: activeCharacterId,
        }),
      });
    } catch (e) { /* silent */ }
    finally { setSavingGrid(false); }
  }, [campaignId, activeCharacterId, cellOverrides, spellZones, savingGrid]);

  const removeSpellZone = useCallback((id) => {
    setSpellZones(prev => prev.filter(z => z.id !== id));
  }, []);

  const closeDmTools = () => {
    setShowDmTools(false);
    setEditMode(null);
    setPendingSpell(null);
    setMeasureFrom(null);
  };

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
        if (data.combat_state.player_grid_x !== undefined) setPlayerGridX(data.combat_state.player_grid_x);
        if (data.combat_state.player_grid_y !== undefined) setPlayerGridY(data.combat_state.player_grid_y);
      }

      // Sync death saves if backend sent them
      if (data.death_saves) {
        setDeathSaves(data.death_saves);
      }

      // Sync spell slots + concentration
      if (data.player_updates?.spell_slots) setSpellSlots(data.player_updates.spell_slots);
      if (data.player_updates?.spell_slots_max) setSpellSlotsMax(data.player_updates.spell_slots_max);
      if ('concentration_spell' in (data.player_updates || {}))
        setConcentrationSpell(data.player_updates.concentration_spell || null);

      // Queue player attack popup
      if (data.narration) {
        const playerMechanics = data.mechanical_summary?.player_attack || data.mechanics || null;
        // Attach spell slot / concentration context to the popup mechanics
        const augmented = playerMechanics ? {
          ...playerMechanics,
          concentration_broken: data.mechanical_summary?.concentration_broken || null,
          concentration_save: data.mechanical_summary?.concentration_save || null,
          slot_used: data.mechanical_summary?.player_attack?.spell_name && data.player_updates?.spell_slots
            ? `${Object.entries(data.player_updates.spell_slots || {}).map(([k]) => k)[0] || ''}th-level`
            : null,
        } : null;
        setNarrationQueue(q => [...q, {
          narration: data.narration,
          mechanics: augmented,
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

      {/* ── DM GRID TOOLBAR ──────────────────────────────────────────────── */}
      {showDmTools && (
        <div className="flex-shrink-0 bg-slate-900/95 border-b border-violet-800/40 px-3 py-2 space-y-2">

          {/* Row 1: mode buttons + save + close */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] text-violet-400 font-bold uppercase tracking-wider mr-1">DM Map Tools</span>

            {[
              { mode: 'terrain', icon: '🖊', label: 'Terrain' },
              { mode: 'spell',   icon: '⭕', label: 'Zone' },
              { mode: 'measure', icon: '📏', label: 'Measure' },
              { mode: 'erase',   icon: '🗑', label: 'Erase' },
            ].map(({ mode, icon, label }) => (
              <button
                key={mode}
                onClick={() => setEditMode(prev => prev === mode ? null : mode)}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold border transition-all ${
                  editMode === mode
                    ? 'bg-violet-700 border-violet-500 text-white'
                    : 'bg-slate-800 border-slate-600 text-slate-300 hover:border-violet-500 hover:text-violet-300'
                }`}
              >
                {icon} {label}
              </button>
            ))}

            {/* AoO toggle */}
            <button
              onClick={() => setShowAoO(p => !p)}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold border transition-all ${
                showAoO
                  ? 'bg-amber-700/70 border-amber-500 text-amber-200'
                  : 'bg-slate-800 border-slate-600 text-slate-300 hover:border-amber-500 hover:text-amber-300'
              }`}
            >
              ⚡ AoO
            </button>

            {/* Undo last override */}
            <button
              onClick={() => setCellOverrides(prev => prev.slice(0, -1))}
              disabled={cellOverrides.length === 0}
              className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs border border-slate-600 bg-slate-800 text-slate-400 hover:text-white disabled:opacity-30 transition-all"
            >
              ↩ Undo
            </button>

            {/* Clear spell zones */}
            {spellZones.length > 0 && (
              <button
                onClick={() => setSpellZones([])}
                className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs border border-red-800/60 bg-slate-800 text-red-400 hover:border-red-500 transition-all"
              >
                ✕ Clear zones
              </button>
            )}

            <div className="flex-1" />

            {/* Add Enemy */}
            <button
              onClick={() => setShowEnemyLibrary(true)}
              className="flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-bold border border-violet-700/60 bg-violet-900/40 text-violet-300 hover:bg-violet-800/40 transition-all"
            >
              ➕ Enemy
            </button>

            {/* Save */}
            <button
              onClick={saveGridChanges}
              disabled={savingGrid}
              className="flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-bold border border-green-700/60 bg-green-900/40 text-green-300 hover:bg-green-800/40 disabled:opacity-40 transition-all"
            >
              {savingGrid ? '…' : '💾'} Save
            </button>
            <button onClick={closeDmTools} className="text-slate-500 hover:text-white text-xs px-1.5 transition-colors">✕</button>
          </div>

          {/* Row 2: terrain palette (when in terrain mode) */}
          {editMode === 'terrain' && (
            <div className="flex items-center gap-1 flex-wrap">
              <span className="text-[9px] text-slate-500 uppercase tracking-wider mr-0.5">Paint:</span>
              {[
                { type: 'floor',     bg: 'bg-slate-700',        label: 'Floor' },
                { type: 'wall',      bg: 'bg-slate-950',        label: 'Wall' },
                { type: 'pillar',    bg: 'bg-slate-600',        label: 'Pillar' },
                { type: 'difficult', bg: 'bg-yellow-900',       label: 'Difficult' },
                { type: 'cover',     bg: 'bg-green-900',        label: 'Cover ½' },
                { type: 'door',      bg: 'bg-amber-800',        label: 'Door' },
                { type: 'water',     bg: 'bg-blue-900',         label: 'Water' },
                { type: 'rock',      bg: 'bg-stone-700',        label: 'Rock' },
                { type: 'rubble',    bg: 'bg-stone-800',        label: 'Rubble' },
                { type: 'altar',     bg: 'bg-purple-900',       label: 'Altar' },
                { type: 'chest',     bg: 'bg-yellow-800',       label: 'Chest' },
              ].map(({ type, bg, label }) => (
                <button
                  key={type}
                  onClick={() => setActiveBrush(type)}
                  className={`flex items-center gap-1 px-2 py-0.5 rounded text-[10px] border transition-all ${
                    activeBrush === type
                      ? 'border-white text-white ring-1 ring-white/30'
                      : 'border-slate-600/60 text-slate-300 hover:border-slate-400'
                  } ${bg}`}
                >
                  {label}
                </button>
              ))}
            </div>
          )}

          {/* Row 2: spell palette (when in spell mode) */}
          {editMode === 'spell' && (
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[9px] text-slate-500 uppercase tracking-wider mr-0.5">Spell:</span>
              {[
                { name: 'Fireball',    radius: 4, color: '#f97316' },
                { name: 'Web',         radius: 4, color: '#9ca3af' },
                { name: 'Darkness',    radius: 3, color: '#7c3aed' },
                { name: 'Silence',     radius: 4, color: '#93c5fd' },
                { name: 'Fog Cloud',   radius: 4, color: '#e2e8f0' },
                { name: 'Entangle',    radius: 4, color: '#16a34a' },
                { name: 'Spirit Zone', radius: 3, color: '#a855f7' },
                { name: 'Burning Hands', radius: 2, color: '#ef4444' },
              ].map(sp => (
                <button
                  key={sp.name}
                  onClick={() => setPendingSpell(prev =>
                    prev?.name === sp.name ? null : { ...sp, shape: 'circle' }
                  )}
                  className={`flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] border transition-all ${
                    pendingSpell?.name === sp.name
                      ? 'border-white text-white'
                      : 'border-slate-600 text-slate-300 hover:border-slate-400 bg-slate-800'
                  }`}
                  style={pendingSpell?.name === sp.name ? { borderColor: sp.color, color: sp.color } : {}}
                >
                  <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: sp.color }} />
                  {sp.name} ({sp.radius * 5}ft)
                </button>
              ))}
              {/* Custom radius */}
              <div className="flex items-center gap-1">
                <span className="text-[9px] text-slate-500">Custom:</span>
                <input
                  type="number"
                  min={1} max={10}
                  value={customSpellRadius}
                  onChange={e => setCustomSpellRadius(Number(e.target.value))}
                  className="w-10 bg-slate-800 border border-slate-600 rounded px-1 text-xs text-white text-center"
                />
                <button
                  onClick={() => setPendingSpell(prev =>
                    prev?.name === 'Custom' ? null : { name: 'Custom', radius: customSpellRadius, color: '#a855f7', shape: 'circle' }
                  )}
                  className={`px-2 py-0.5 rounded text-[10px] border transition-all ${
                    pendingSpell?.name === 'Custom'
                      ? 'bg-violet-700 border-violet-500 text-white'
                      : 'bg-slate-800 border-slate-600 text-slate-300 hover:border-violet-500'
                  }`}
                >
                  Use
                </button>
              </div>
            </div>
          )}

          {/* Row 2: measure hint */}
          {editMode === 'measure' && (
            <div className="text-[10px] text-slate-400">
              Click any cell to set the range origin. Green ≤5ft (melee), Yellow ≤30ft (close), Red 30ft+.
              {measureFrom && (
                <button
                  onClick={() => setMeasureFrom(null)}
                  className="ml-2 text-red-400 hover:text-red-300 underline"
                >
                  Clear origin
                </button>
              )}
            </div>
          )}

          {/* Active spell zones list */}
          {spellZones.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[9px] text-slate-500 uppercase tracking-wider">Active zones:</span>
              {spellZones.map(z => (
                <span
                  key={z.id}
                  className="flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-semibold border"
                  style={{ borderColor: z.color + '80', color: z.color, background: z.color + '18' }}
                >
                  {z.name} ({z.cx},{z.cy})
                  <button onClick={() => removeSpellZone(z.id)} className="ml-0.5 opacity-60 hover:opacity-100 text-[8px]">✕</button>
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Battle Config (shown when toolbar is closed) ─────────────────────── */}
      {!showDmTools && (
        <div className="flex-shrink-0 flex items-center justify-end gap-2 px-4 py-1 bg-slate-900/70 border-b border-slate-800/40">
          <a
            href="#/behavior-trees"
            className="flex items-center gap-1.5 text-[10px] px-2.5 py-1 rounded-lg border border-slate-700/60 text-slate-500 hover:border-amber-500/60 hover:text-amber-400 transition-all"
            title="Edit enemy AI behavior trees"
          >
            AI Trees
          </a>
          <button
            onClick={() => setShowDmTools(true)}
            className="flex items-center gap-1.5 text-[10px] px-2.5 py-1 rounded-lg border border-slate-700/60 text-slate-500 hover:border-violet-500/60 hover:text-violet-400 transition-all"
          >
            Battle Config
          </button>
        </div>
      )}

      {/* ── MAIN AREA: lanes + sidebar ────────────────────────────────────── */}
      <div className="flex flex-1 min-h-0 overflow-hidden">

        {/* Battlefield grid */}
        <div className="flex flex-1 min-w-0 p-2 overflow-hidden">
          <BattlefieldGrid
            grid={localCombat.battlefield_grid}
            cellOverrides={cellOverrides}
            spellZones={spellZones}
            enemies={allEnemies}
            playerGridX={playerGridX}
            playerGridY={playerGridY}
            playerData={{
              id: 'player',
              name: characterState?.identity?.name || characterState?.name || 'You',
              hp: characterState?.hp?.current ?? characterState?.hp ?? 10,
              max_hp: characterState?.hp?.max ?? characterState?.max_hp ?? 10,
              conditions: characterState?.conditions || [],
              _isPlayer: true,
            }}
            activeTurn={activeTurn}
            selectedTarget={selectedTarget}
            onSelectTarget={setSelectedTarget}
            lightLevel={lightLevel}
            characterState={characterState}
            editMode={editMode}
            activeBrush={activeBrush}
            pendingSpell={pendingSpell}
            measureFrom={measureFrom}
            showAoO={showAoO}
            onCellClick={handleCellInteract}
          />
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
          <div className="ml-auto" />
        </div>

        {/* ── Equipment bar ───────────────────────────────────────────── */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500 text-[10px] uppercase tracking-wider font-bold shrink-0">Equipped</span>
          {/* Main hand */}
          <button
            onClick={() => setShowEquipPanel(p => !p)}
            title="Main hand — click to manage equipment"
            className="flex items-center gap-1 px-2 py-0.5 rounded-lg border border-slate-600/60 bg-slate-900/60 hover:border-slate-400 text-slate-300 transition-all"
          >
            ⚔ {equipment.main_hand
              ? `${equipment.main_hand}${equipment.two_handed ? ' (2H)' : ''}`
              : 'empty'}
          </button>
          {/* Off hand */}
          <button
            onClick={() => setShowEquipPanel(p => !p)}
            title="Off hand — click to manage equipment"
            className={`flex items-center gap-1 px-2 py-0.5 rounded-lg border transition-all ${
              equipment.off_hand
                ? equipment.off_hand.toLowerCase().includes('shield')
                  ? 'border-blue-700/60 bg-blue-950/40 text-blue-300 hover:border-blue-500'
                  : 'border-slate-600/60 bg-slate-900/60 text-slate-300 hover:border-slate-400'
                : freeHand
                  ? 'border-green-700/60 bg-green-950/40 text-green-400 hover:border-green-500'
                  : 'border-slate-700 text-slate-600'
            }`}
          >
            🤚 {equipment.off_hand || (freeHand ? 'free hand' : '—')}
          </button>
          {/* AC */}
          {equipAC !== null && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-lg border border-slate-600/60 bg-slate-900/40 text-slate-400">
              🛡 AC {equipAC}
            </span>
          )}
          {/* Armor */}
          {equipment.armor && (
            <span className="text-slate-500 text-[10px] truncate max-w-[80px]">{equipment.armor}</span>
          )}
        </div>

        {/* ── Equipment panel (inline dropdown) ─────────────────────── */}
        {showEquipPanel && (
          <div className="border border-slate-700 rounded-xl bg-slate-900/90 p-3 text-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-300 font-semibold">Equipment Loadout</span>
              <button onClick={() => setShowEquipPanel(false)} className="text-slate-500 hover:text-white">✕</button>
            </div>
            {/* Slot rows */}
            {(['main_hand', 'off_hand', 'armor']).map(slot => {
              const label = slot === 'main_hand' ? '⚔ Main Hand'
                : slot === 'off_hand' ? '🤚 Off Hand' : '🔰 Armor';
              const current = equipment[slot];
              // Filter inventory for this slot
              const candidates = equipInventory.filter(item => {
                const n = (item.name || '').toLowerCase();
                if (slot === 'armor') return item.slot === 'armor' || item.equipped && item.slot === 'armor' ||
                  ['leather','chain','scale','plate','mail','armor','hide','breastplate','splint','padded','studded','ring mail'].some(k => n.includes(k));
                if (slot === 'off_hand') return item.slot === 'off_hand' || item.equipped && item.slot === 'off_hand' ||
                  ['shield','holy symbol','component pouch','druidic focus','orb','lute','lyre','flute','wand','rod','arcane focus','crystal'].some(k => n.includes(k));
                // main_hand: anything weapon-ish
                return item.slot === 'main_hand' || item.equipped && item.slot === 'main_hand' ||
                  ['sword','axe','bow','staff','rapier','dagger','mace','spear','crossbow','club','dart','scimitar','hammer','pick','lance','glaive','halberd','pike','maul','flail','trident','morningstar','greatclub'].some(k => n.includes(k));
              });
              return (
                <div key={slot} className="flex items-center gap-2">
                  <span className="text-slate-500 w-24 shrink-0">{label}</span>
                  <span className="text-white truncate max-w-[100px]">{current || '—'}</span>
                  <select
                    className="ml-auto bg-slate-800 border border-slate-600 rounded px-1 py-0.5 text-slate-300 text-[10px] max-w-[140px]"
                    value=""
                    onChange={e => {
                      const val = e.target.value;
                      if (val === '__unequip__') handleEquip(slot, null);
                      else handleEquip(slot, val);
                    }}
                  >
                    <option value="">swap…</option>
                    {current && <option value="__unequip__">— Unequip</option>}
                    {candidates.filter(i => i.name !== current).map(item => (
                      <option key={item.name} value={item.name}>{item.name}</option>
                    ))}
                  </select>
                </div>
              );
            })}
            {/* 2H toggle for versatile weapons */}
            {equipment.main_hand && (
              <label className="flex items-center gap-2 text-slate-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={!!equipment.two_handed}
                  onChange={e => handleEquip('main_hand', equipment.main_hand, e.target.checked)}
                  className="rounded"
                />
                Use two-handed grip (versatile weapons get +1 damage die)
              </label>
            )}
          </div>
        )}

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
        <div className="flex items-center gap-2 flex-wrap">
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
          {/* Spell slot pips */}
          {Object.keys(spellSlotsMax).length > 0 && (
            <div className="flex items-center gap-2 ml-1 flex-wrap">
              {Object.entries(spellSlotsMax).sort(([a],[b]) => Number(a)-Number(b)).map(([lvl, max]) => {
                const rem = spellSlots[lvl] ?? max;
                return (
                  <div key={lvl} className="flex items-center gap-0.5">
                    <span className="text-[9px] text-slate-500 mr-0.5">L{lvl}</span>
                    {Array.from({length: Number(max)}).map((_, i) => (
                      <span key={i} className={`text-[10px] ${i < rem ? 'text-violet-400' : 'text-slate-700'}`}>●</span>
                    ))}
                  </div>
                );
              })}
            </div>
          )}
          {/* Active concentration */}
          {concentrationSpell && (
            <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-950/70 border border-indigo-700/50 text-[10px] text-indigo-300">
              ◉ {concentrationSpell}
            </div>
          )}
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

      {/* ── Enemy Library Panel (DM modal) ───────────────────────────────── */}
      {showEnemyLibrary && (
        <EnemyLibraryPanel
          campaignId={campaignId}
          characterId={activeCharacterId}
          onClose={() => setShowEnemyLibrary(false)}
          onEnemyAdded={(enemy) => {
            // Optimistically update local combat state so the grid reflects the new enemy
            if (enemy) {
              setLocalCombat(prev => ({
                ...prev,
                enemies: [...(prev.enemies || []), enemy],
              }));
            }
          }}
        />
      )}
    </div>
  );
};

export default CombatScreen;
