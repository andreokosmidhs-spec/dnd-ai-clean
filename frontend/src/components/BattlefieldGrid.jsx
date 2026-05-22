/**
 * BattlefieldGrid — tactical combat map with DM editing tools.
 *
 * Features:
 *  - Terrain cell rendering (floor / wall / pillar / difficult / cover / …)
 *  - DM cell-paint mode: click to apply a terrain type
 *  - Spell zone overlays: circular / square radius with colour tint + label
 *  - Range-measure mode: every cell shows distance in feet from the chosen origin
 *  - Attack-of-Opportunity zone: highlights the 8 cells adjacent to the player
 *  - Hover preview: spell zone shape shown before the DM commits a placement
 *  - Light-level darkness overlay (dim / dark columns)
 */
import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence, LayoutGroup } from 'framer-motion';

// ── Terrain visual config ─────────────────────────────────────────────────────
export const TERRAIN_TYPES = [
  { type: 'floor',     label: '',   glyph: '·',  name: 'Floor',     bg: 'bg-slate-800',      border: 'border-slate-700/30' },
  { type: 'wall',      label: '▪',  glyph: '▪',  name: 'Wall',      bg: 'bg-slate-950',      border: 'border-slate-600/50' },
  { type: 'pillar',    label: '◼',  glyph: '◼',  name: 'Pillar',    bg: 'bg-slate-700',      border: 'border-slate-500/60' },
  { type: 'difficult', label: '~',  glyph: '~',  name: 'Difficult', bg: 'bg-yellow-950/70',  border: 'border-yellow-800/40' },
  { type: 'cover',     label: '▤',  glyph: '▤',  name: 'Cover',     bg: 'bg-green-950/80',   border: 'border-green-800/50' },
  { type: 'door',      label: '▭',  glyph: '▭',  name: 'Door',      bg: 'bg-amber-900/70',   border: 'border-amber-700/60' },
  { type: 'water',     label: '≈',  glyph: '≈',  name: 'Water',     bg: 'bg-blue-950/80',    border: 'border-blue-800/50' },
  { type: 'tree',      label: '♣',  glyph: '♣',  name: 'Tree',      bg: 'bg-green-900/80',   border: 'border-green-700/50' },
  { type: 'rock',      label: '◇',  glyph: '◇',  name: 'Rock',      bg: 'bg-stone-800/90',   border: 'border-stone-600/50' },
  { type: 'rubble',    label: '∴',  glyph: '∴',  name: 'Rubble',    bg: 'bg-stone-900/60',   border: 'border-stone-700/40' },
  { type: 'altar',     label: '✦',  glyph: '✦',  name: 'Altar',     bg: 'bg-purple-950/80',  border: 'border-purple-700/50' },
  { type: 'chest',     label: '▣',  glyph: '▣',  name: 'Chest',     bg: 'bg-yellow-900/70',  border: 'border-yellow-600/60' },
];

const TERRAIN_MAP = Object.fromEntries(TERRAIN_TYPES.map(t => [t.type, t]));
const DEFAULT_CELL = TERRAIN_MAP['floor'];
const IMPASSABLE = new Set(['wall', 'pillar', 'tree', 'rock']);

// Cover tooltip for status bar
export const COVER_HINT = {
  cover:     '½ Cover: +2 AC & DEX saves',
  wall:      "Full Cover: can't be targeted",
  pillar:    '¾ Cover: +5 AC & DEX saves',
};

// ── Distance helpers ─────────────────────────────────────────────────────────
/** Chebyshev distance (D&D 5e: diagonal = 5ft) */
function chebDist(ax, ay, bx, by) {
  return Math.max(Math.abs(bx - ax), Math.abs(by - ay));
}

function distFt(ax, ay, bx, by) {
  return chebDist(ax, ay, bx, by) * 5;
}

/** Cells within `radius` squares (Chebyshev circle) of (cx,cy) in an cols×rows grid */
function cellsInZone(cx, cy, radius, cols, rows) {
  const set = new Set();
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      if (chebDist(cx, cy, x, y) <= radius) set.add(`${x},${y}`);
    }
  }
  return set;
}

/** 8-cell AoO ring around (px,py) */
function aooRing(px, py) {
  const set = new Set();
  for (let dy = -1; dy <= 1; dy++) {
    for (let dx = -1; dx <= 1; dx++) {
      if (dx === 0 && dy === 0) continue;
      set.add(`${px + dx},${py + dy}`);
    }
  }
  return set;
}

// ── Distance colour coding ───────────────────────────────────────────────────
function distColor(ft) {
  if (ft <= 5)  return '#22c55e';   // green  — melee
  if (ft <= 30) return '#eab308';   // yellow — close/medium
  return '#ef4444';                 // red    — far
}

// ── Participant token ─────────────────────────────────────────────────────────
const GridToken = ({ participant, isActive, isTarget, isPlayer, inAoO, onClick }) => {
  const hp    = participant.hp ?? 0;
  const maxHp = participant.max_hp ?? hp;
  const pct   = maxHp > 0 ? Math.max(0, (hp / maxHp) * 100) : 0;
  const hpBg  = pct > 60 ? 'bg-green-500' : pct > 30 ? 'bg-yellow-500' : 'bg-red-500';
  const tokenId = participant.id || (isPlayer ? '__player__' : participant.name || 'unknown');

  return (
    <motion.div
      layoutId={`token-${tokenId}`}
      layout
      initial={{ opacity: 0, scale: 0.5 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.3 }}
      transition={{
        layout:   { type: 'spring', stiffness: 380, damping: 28 },
        opacity:  { duration: 0.18 },
        scale:    { duration: 0.18 },
      }}
      onClick={e => { e.stopPropagation(); onClick && onClick(); }}
      className={`
        absolute inset-0.5 rounded flex flex-col items-center justify-center
        cursor-pointer select-none z-10
        ${isPlayer
          ? 'bg-violet-900/85 border border-violet-500/80'
          : isTarget
            ? 'bg-red-950/85 border border-red-400/80 ring-1 ring-red-500/50'
            : 'bg-slate-900/85 border border-slate-600/60 hover:border-slate-400/80'}
        ${isActive ? 'shadow-[0_0_8px_2px_rgba(167,139,250,0.4)]' : ''}
      `}
    >
      <span className="text-base leading-none">{isPlayer ? '🧙' : '💀'}</span>
      <span className="text-[9px] text-white font-semibold leading-tight truncate max-w-full px-0.5 text-center">
        {(participant.name || '').split(' ')[0] || (isPlayer ? 'You' : '?')}
      </span>
      <div className="w-full px-1 mt-0.5">
        <div className="h-1 bg-slate-700 rounded-full overflow-hidden">
          <motion.div
            className={`h-full rounded-full ${hpBg}`}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
          />
        </div>
      </div>
      {/* AoO badge on enemy when in player's threat range */}
      {inAoO && !isPlayer && (
        <div className="absolute -top-1.5 -right-1 px-0.5 rounded bg-amber-500 text-[7px] font-black text-slate-900 leading-tight z-20">
          AoO
        </div>
      )}
      {isActive && (
        <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-violet-500 border border-slate-900 flex items-center justify-center z-20">
          <span className="text-[7px] text-white font-black">▶</span>
        </div>
      )}
    </motion.div>
  );
};

// ── Main component ────────────────────────────────────────────────────────────
const BattlefieldGrid = ({
  // Grid data
  grid,
  cellOverrides = [],
  spellZones    = [],

  // Participants
  enemies,
  playerGridX,
  playerGridY,
  playerData,
  activeTurn,
  selectedTarget,
  onSelectTarget,

  // Visual
  lightLevel,
  characterState,

  // DM edit
  editMode     = null,   // 'terrain' | 'spell' | 'measure' | 'erase' | null
  activeBrush  = 'wall',
  pendingSpell = null,   // { name, radius, color, shape } when about to place a zone
  measureFrom  = null,   // { x, y } for range ruler
  showAoO      = false,
  onCellClick,           // (x, y) => void
}) => {
  const [hoverCell, setHoverCell] = useState(null);

  const cols = grid?.cols ?? 8;
  const rows = grid?.rows ?? 6;

  // ── Merge base cells + DM overrides ──────────────────────────────────────
  const baseCellMap = {};
  (grid?.cells ?? []).forEach(c => { baseCellMap[`${c.x},${c.y}`] = c.type; });
  const overrideMap = {};
  cellOverrides.forEach(c => { overrideMap[`${c.x},${c.y}`] = c.type; });
  const cellType = (x, y) => overrideMap[`${x},${y}`] ?? baseCellMap[`${x},${y}`] ?? 'floor';

  // ── Spell zone coverage ───────────────────────────────────────────────────
  const zonesByCell = {};   // key → { color, name }[]
  spellZones.forEach(zone => {
    const covered = cellsInZone(zone.cx, zone.cy, zone.radius, cols, rows);
    covered.forEach(key => {
      if (!zonesByCell[key]) zonesByCell[key] = [];
      zonesByCell[key].push({ color: zone.color, name: zone.name, id: zone.id });
    });
  });

  // Hover preview for pending spell placement
  const previewCells = (editMode === 'spell' && pendingSpell && hoverCell)
    ? cellsInZone(hoverCell.x, hoverCell.y, pendingSpell.radius, cols, rows)
    : new Set();

  // ── AoO zone ─────────────────────────────────────────────────────────────
  const px = playerGridX ?? 1;
  const py = playerGridY ?? 2;
  const aoo = (showAoO || editMode === null) ? aooRing(px, py) : new Set();

  // ── Token map ────────────────────────────────────────────────────────────
  const tokenMap = {};
  const player = playerData ?? {
    id: 'player',
    name: characterState?.identity?.name || characterState?.name || 'You',
    hp:     characterState?.hp?.current ?? characterState?.hp ?? 10,
    max_hp: characterState?.hp?.max     ?? characterState?.max_hp ?? 10,
    _isPlayer: true,
  };
  tokenMap[`${px},${py}`] = { ...player, _isPlayer: true };

  (enemies ?? []).forEach(e => {
    const ex = e.grid_x ?? 5;
    const ey = e.grid_y ?? 2;
    let key = `${ex},${ey}`;
    let off = 0;
    while (tokenMap[key] && off < rows) { off++; key = `${ex},${Math.min(rows - 1, ey + off)}`; }
    tokenMap[key] = e;
  });

  // ── Light ─────────────────────────────────────────────────────────────────
  const isDark = lightLevel?.overlay === 'dark';
  const isDim  = lightLevel?.overlay === 'dim';

  // ── Cell click handler ────────────────────────────────────────────────────
  const handleClick = useCallback((x, y, e) => {
    e.stopPropagation();
    if (onCellClick) onCellClick(x, y);
  }, [onCellClick]);

  // ── Cursor style per mode ────────────────────────────────────────────────
  const cursorStyle = editMode ? 'cursor-crosshair' : 'cursor-default';

  return (
    <LayoutGroup>
    <div
      className={`relative w-full h-full ${cursorStyle}`}
      style={{ minHeight: 0 }}
      onMouseLeave={() => setHoverCell(null)}
    >
      <div
        className="grid w-full h-full"
        style={{
          gridTemplateColumns: `repeat(${cols}, 1fr)`,
          gridTemplateRows:    `repeat(${rows}, 1fr)`,
          gap: '1px',
          background: '#0f172a',
        }}
      >
        {Array.from({ length: rows }).map((_, y) =>
          Array.from({ length: cols }).map((_, x) => {
            const key        = `${x},${y}`;
            const terrain    = TERRAIN_MAP[cellType(x, y)] ?? DEFAULT_CELL;
            const isPass     = !IMPASSABLE.has(cellType(x, y));
            const token      = tokenMap[key];
            const zones      = zonesByCell[key] ?? [];
            const isPreview  = previewCells.has(key);
            const isAoO      = aoo.has(key);
            const tokenInAoO = token && !token._isPlayer && aoo.has(key);

            // Range measure
            const measureFt  = (editMode === 'measure' && measureFrom)
              ? distFt(measureFrom.x, measureFrom.y, x, y)
              : null;

            // Paint-mode hover highlight
            const isPaintHover = (editMode === 'terrain' || editMode === 'erase') && hoverCell?.x === x && hoverCell?.y === y;

            const darkened = isDark && x >= Math.floor(cols / 2);
            const dimmed   = isDim  && x >= Math.floor(cols * 0.7);

            return (
              <div
                key={key}
                className={`relative ${terrain.bg} border ${terrain.border} transition-colors`}
                onClick={e => handleClick(x, y, e)}
                onMouseEnter={() => setHoverCell({ x, y })}
              >
                {/* Terrain glyph (no token) */}
                {!token && terrain.label && (
                  <span className="absolute inset-0 flex items-center justify-center text-[10px] text-slate-500 select-none pointer-events-none">
                    {terrain.label}
                  </span>
                )}

                {/* Coord hint on empty floor */}
                {!token && !terrain.label && isPass && (
                  <span className="absolute bottom-0 right-0.5 text-[6px] text-slate-700/60 select-none pointer-events-none leading-tight">
                    {x},{y}
                  </span>
                )}

                {/* Spell zone colour overlays */}
                {zones.map((z, i) => (
                  <div
                    key={z.id + i}
                    className="absolute inset-0 pointer-events-none z-[5]"
                    style={{ backgroundColor: z.color + '55', borderRadius: 1 }}
                  />
                ))}
                {/* Zone label on centre cell */}
                {zones.length > 0 && spellZones.some(z => z.cx === x && z.cy === y) && (
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-[6]">
                    <span className="text-[8px] font-bold text-white/80 leading-tight text-center px-0.5">
                      {spellZones.filter(z => z.cx === x && z.cy === y).map(z => z.name).join('\n')}
                    </span>
                  </div>
                )}

                {/* Spell hover preview */}
                {isPreview && !zones.length && pendingSpell && (
                  <div
                    className="absolute inset-0 pointer-events-none z-[5]"
                    style={{ backgroundColor: pendingSpell.color + '33', borderRadius: 1 }}
                  />
                )}
                {isPreview && pendingSpell && hoverCell?.x === x && hoverCell?.y === y && (
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-[6]">
                    <span className="text-[8px] font-bold text-white/60">{pendingSpell.name}</span>
                  </div>
                )}

                {/* AoO ring (subtle amber tint) */}
                {isAoO && showAoO && !token && (
                  <div className="absolute inset-0 pointer-events-none z-[4] border border-amber-500/40 rounded-sm" />
                )}

                {/* Paint-mode hover highlight */}
                {isPaintHover && (
                  <div className="absolute inset-0 pointer-events-none z-[8] bg-white/10 rounded-sm" />
                )}

                {/* Participant token */}
                <AnimatePresence>
                  {token && (
                    <GridToken
                      key={token._isPlayer ? '__player__' : token.id}
                      participant={token}
                      isPlayer={token._isPlayer}
                      isActive={activeTurn === (token._isPlayer ? 'player' : token.id)}
                      isTarget={!token._isPlayer && token.id === selectedTarget}
                      inAoO={tokenInAoO}
                      onClick={!token._isPlayer && token.hp > 0 ? () => onSelectTarget?.(token.id) : undefined}
                    />
                  )}
                </AnimatePresence>

                {/* Range measure label */}
                {measureFt !== null && (
                  <div
                    className="absolute top-0.5 left-0.5 text-[8px] font-bold leading-tight pointer-events-none z-[15] px-0.5 rounded"
                    style={{ color: distColor(measureFt), background: 'rgba(0,0,0,0.5)' }}
                  >
                    {measureFt}ft
                  </div>
                )}

                {/* Darkness overlay */}
                {darkened && <div className="absolute inset-0 bg-slate-950/55 pointer-events-none z-[20] rounded-sm" />}
                {dimmed   && <div className="absolute inset-0 bg-slate-900/30 pointer-events-none z-[20] rounded-sm" />}
              </div>
            );
          })
        )}
      </div>

      {/* Legend strip */}
      <div className="absolute bottom-1 left-1 flex items-center gap-2 pointer-events-none select-none">
        <span className="text-[8px] text-slate-600 font-mono">5ft/cell</span>
        {grid?.generated === false && (
          <span className="text-[8px] text-slate-600 italic">default map</span>
        )}
        {showAoO && (
          <span className="text-[8px] text-amber-600">AoO zone active</span>
        )}
        {editMode && (
          <span className="text-[8px] text-violet-400 font-semibold uppercase">
            {editMode === 'terrain' ? `Paint: ${activeBrush}` :
             editMode === 'spell'   ? (pendingSpell ? `Place: ${pendingSpell.name}` : 'Select spell…') :
             editMode === 'measure' ? (measureFrom ? `Origin: ${measureFrom.x},${measureFrom.y}` : 'Click origin') :
             editMode === 'erase'   ? 'Erase' : ''}
          </span>
        )}
      </div>
    </div>
    </LayoutGroup>
  );
};

export default BattlefieldGrid;
