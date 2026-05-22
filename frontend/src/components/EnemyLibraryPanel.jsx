/**
 * EnemyLibraryPanel — DM modal for browsing and adding enemies to active combat.
 *
 * Features:
 *  - Searchable, filterable list (by CR and creature type)
 *  - Enemy cards: name, CR, type, HP/AC, behavior profile badge, tactics note
 *  - "Add to Combat" button that POSTs to /api/enemy-library/add-to-combat
 *  - onEnemyAdded callback so CombatScreen can refresh
 */
import React, { useState, useEffect, useCallback } from 'react';
import { X, Search, Plus, ChevronDown } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// ── Behavior profile badge colors ────────────────────────────────────────────

const PROFILE_COLORS = {
  brute:           'bg-red-900/60 text-red-200 border-red-700/50',
  skirmisher:      'bg-green-900/60 text-green-200 border-green-700/50',
  berserker:       'bg-orange-900/60 text-orange-200 border-orange-700/50',
  pack_hunter:     'bg-yellow-900/60 text-yellow-200 border-yellow-700/50',
  undead_mindless: 'bg-violet-900/60 text-violet-200 border-violet-700/50',
  undead_cunning:  'bg-purple-900/60 text-purple-200 border-purple-700/50',
  ambusher:        'bg-slate-700/60 text-slate-200 border-slate-500/50',
  spellcaster:     'bg-blue-900/60 text-blue-200 border-blue-700/50',
};

function profileBadge(profile) {
  const cls = PROFILE_COLORS[profile] || 'bg-slate-800 text-slate-300 border-slate-600';
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${cls}`}>
      {profile.replace(/_/g, ' ')}
    </span>
  );
}

// ── CR sort helper ─────────────────────────────────────────────────────────

function crToNum(cr) {
  if (cr === '0') return 0;
  if (cr === '1/8') return 0.125;
  if (cr === '1/4') return 0.25;
  if (cr === '1/2') return 0.5;
  return parseFloat(cr) || 0;
}

// ── HP bar ────────────────────────────────────────────────────────────────

function HpBar({ hp, maxHp }) {
  const pct = maxHp > 0 ? Math.round((hp / maxHp) * 100) : 0;
  const color = pct > 60 ? 'bg-green-500' : pct > 30 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div className="w-full h-1 bg-slate-700 rounded-full mt-1">
      <div className={`h-1 rounded-full ${color}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

// ── Enemy Card ────────────────────────────────────────────────────────────

function EnemyCard({ enemy, onAdd, adding }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-xl border border-slate-700/60 bg-slate-900/60 p-3 flex flex-col gap-2 hover:border-slate-500/70 transition-all">
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-white text-sm font-bold truncate">{enemy.name}</span>
            <span className="text-slate-400 text-[10px] font-mono">CR {enemy.cr}</span>
            <span className="text-slate-500 text-[10px] capitalize">{enemy.type}</span>
          </div>
          <div className="mt-1">{profileBadge(enemy.behavior_profile)}</div>
        </div>
        <button
          onClick={() => onAdd(enemy.id)}
          disabled={adding}
          className="flex-shrink-0 flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-bold
                     border border-violet-600/60 bg-violet-900/40 text-violet-200
                     hover:bg-violet-700/60 hover:border-violet-400 disabled:opacity-40
                     transition-all"
        >
          <Plus size={12} />
          {adding ? '…' : 'Add'}
        </button>
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-3 text-xs text-slate-300">
        <span className="flex items-center gap-1">
          <span className="text-red-400 font-semibold">HP</span>
          <span>{enemy.hp}</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="text-blue-400 font-semibold">AC</span>
          <span>{enemy.ac}</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="text-yellow-400 font-semibold">XP</span>
          <span>{enemy.xp}</span>
        </span>
      </div>
      <HpBar hp={enemy.hp} maxHp={enemy.hp} />

      {/* Description */}
      <p className="text-slate-400 text-[11px] leading-relaxed line-clamp-2">
        {enemy.description}
      </p>

      {/* Expandable tactics note */}
      {enemy.tactics_note && (
        <button
          onClick={() => setExpanded(p => !p)}
          className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-slate-300 transition-colors"
        >
          <ChevronDown size={11} className={`transition-transform ${expanded ? 'rotate-180' : ''}`} />
          Tactics
        </button>
      )}
      {expanded && enemy.tactics_note && (
        <p className="text-slate-400 text-[11px] italic leading-relaxed border-l-2 border-slate-700 pl-2">
          {enemy.tactics_note}
        </p>
      )}
    </div>
  );
}

// ── Main Panel ────────────────────────────────────────────────────────────

export default function EnemyLibraryPanel({
  campaignId,
  characterId,
  onClose,
  onEnemyAdded,
}) {
  const [enemies, setEnemies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [search, setSearch] = useState('');
  const [filterCR, setFilterCR] = useState('all');
  const [filterType, setFilterType] = useState('all');

  const [addingId, setAddingId] = useState(null);
  const [addSuccess, setAddSuccess] = useState(null);
  const [addError, setAddError] = useState(null);

  // Load library
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch(`${BACKEND_URL}/api/enemy-library`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(data => {
        if (!cancelled) {
          // Sort by CR
          const sorted = [...data].sort((a, b) => crToNum(a.cr) - crToNum(b.cr));
          setEnemies(sorted);
        }
      })
      .catch(err => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, []);

  // Derived filter options
  const allCRs = [...new Set(enemies.map(e => e.cr))].sort((a, b) => crToNum(a) - crToNum(b));
  const allTypes = [...new Set(enemies.map(e => e.type))].sort();

  // Filtered list
  const filtered = enemies.filter(e => {
    const matchSearch = !search
      || e.name.toLowerCase().includes(search.toLowerCase())
      || e.behavior_profile.toLowerCase().includes(search.toLowerCase())
      || e.type.toLowerCase().includes(search.toLowerCase());
    const matchCR = filterCR === 'all' || e.cr === filterCR;
    const matchType = filterType === 'all' || e.type === filterType;
    return matchSearch && matchCR && matchType;
  });

  const handleAdd = useCallback(async (enemyId) => {
    if (!campaignId || !characterId) {
      setAddError('Campaign or character not set.');
      return;
    }
    setAddingId(enemyId);
    setAddError(null);
    setAddSuccess(null);

    try {
      const resp = await fetch(`${BACKEND_URL}/api/enemy-library/add-to-combat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_id: campaignId,
          character_id: characterId,
          enemy_id: enemyId,
        }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || `HTTP ${resp.status}`);
      }
      setAddSuccess(data.message || 'Enemy added!');
      if (onEnemyAdded) onEnemyAdded(data.enemy);
    } catch (err) {
      setAddError(err.message);
    } finally {
      setAddingId(null);
    }
  }, [campaignId, characterId, onEnemyAdded]);

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      {/* Modal */}
      <div className="relative w-full max-w-2xl max-h-[90vh] mx-4 flex flex-col
                      bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700/60 flex-shrink-0">
          <div>
            <h2 className="text-white font-bold text-base">Enemy Library</h2>
            <p className="text-slate-400 text-xs mt-0.5">
              {filtered.length} of {enemies.length} enemies
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-500 hover:text-white transition-colors p-1 rounded-lg hover:bg-slate-800"
          >
            <X size={18} />
          </button>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-800/60 flex-shrink-0 flex-wrap">
          {/* Search */}
          <div className="flex items-center gap-1.5 flex-1 min-w-[160px] bg-slate-800 rounded-lg
                          border border-slate-700/60 px-2.5 py-1.5">
            <Search size={12} className="text-slate-500 flex-shrink-0" />
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search enemies…"
              className="bg-transparent text-xs text-white placeholder-slate-500 outline-none flex-1 min-w-0"
            />
          </div>

          {/* CR filter */}
          <select
            value={filterCR}
            onChange={e => setFilterCR(e.target.value)}
            className="bg-slate-800 border border-slate-700/60 rounded-lg text-xs text-slate-300
                       px-2 py-1.5 outline-none cursor-pointer hover:border-slate-500 transition-colors"
          >
            <option value="all">All CRs</option>
            {allCRs.map(cr => (
              <option key={cr} value={cr}>CR {cr}</option>
            ))}
          </select>

          {/* Type filter */}
          <select
            value={filterType}
            onChange={e => setFilterType(e.target.value)}
            className="bg-slate-800 border border-slate-700/60 rounded-lg text-xs text-slate-300
                       px-2 py-1.5 outline-none cursor-pointer hover:border-slate-500 transition-colors"
          >
            <option value="all">All Types</option>
            {allTypes.map(t => (
              <option key={t} value={t} className="capitalize">{t}</option>
            ))}
          </select>
        </div>

        {/* Status messages */}
        {(addSuccess || addError) && (
          <div className={`flex-shrink-0 px-4 py-2 text-xs font-semibold ${
            addError ? 'bg-red-950/40 text-red-300 border-b border-red-800/40'
                     : 'bg-green-950/40 text-green-300 border-b border-green-800/40'
          }`}>
            {addError || addSuccess}
          </div>
        )}

        {/* Enemy list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {loading && (
            <div className="flex items-center justify-center py-16 text-slate-400 text-sm">
              Loading library…
            </div>
          )}
          {!loading && error && (
            <div className="flex items-center justify-center py-16 text-red-400 text-sm">
              Error: {error}
            </div>
          )}
          {!loading && !error && filtered.length === 0 && (
            <div className="flex items-center justify-center py-16 text-slate-500 text-sm">
              No enemies match your filters.
            </div>
          )}
          {!loading && !error && filtered.map(enemy => (
            <EnemyCard
              key={enemy.id}
              enemy={enemy}
              onAdd={handleAdd}
              adding={addingId === enemy.id}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
