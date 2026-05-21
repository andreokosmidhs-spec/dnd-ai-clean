/**
 * BattlefieldGrid — CSS-grid tactical map for D&D combat.
 *
 * The grid is generated once per location by the LLM and cached in MongoDB.
 * Each cell is coloured by terrain type; participant tokens are overlaid.
 */
import React from 'react';

// ── Terrain visual config ─────────────────────────────────────────────────────
const TERRAIN = {
  floor:     { bg: 'bg-slate-800',        border: 'border-slate-700/30', label: '' },
  wall:      { bg: 'bg-slate-950',        border: 'border-slate-600/50', label: '▪' },
  pillar:    { bg: 'bg-slate-700',        border: 'border-slate-500/60', label: '◼' },
  difficult: { bg: 'bg-yellow-950/70',    border: 'border-yellow-800/40', label: '~' },
  cover:     { bg: 'bg-green-950/80',     border: 'border-green-800/50', label: '▤' },
  door:      { bg: 'bg-amber-900/70',     border: 'border-amber-700/60', label: '▭' },
  water:     { bg: 'bg-blue-950/80',      border: 'border-blue-800/50', label: '≈' },
  tree:      { bg: 'bg-green-900/80',     border: 'border-green-700/50', label: '♣' },
  rock:      { bg: 'bg-stone-800/90',     border: 'border-stone-600/50', label: '◇' },
  rubble:    { bg: 'bg-stone-900/60',     border: 'border-stone-700/40', label: '∴' },
  altar:     { bg: 'bg-purple-950/80',    border: 'border-purple-700/50', label: '✦' },
  chest:     { bg: 'bg-yellow-900/70',    border: 'border-yellow-600/60', label: '▣' },
};

const DEFAULT_CELL = { bg: 'bg-slate-800', border: 'border-slate-700/30', label: '' };

// ── Participant token (compact, fits inside a grid cell) ──────────────────────
const GridToken = ({ participant, isActive, isTarget, isPlayer, onClick }) => {
  const hp    = participant.hp ?? 0;
  const maxHp = participant.max_hp ?? hp;
  const pct   = maxHp > 0 ? Math.max(0, (hp / maxHp) * 100) : 0;
  const hpColor = pct > 60 ? 'bg-green-500' : pct > 30 ? 'bg-yellow-500' : 'bg-red-500';

  return (
    <div
      onClick={onClick}
      className={`
        absolute inset-0.5 rounded flex flex-col items-center justify-center cursor-pointer
        select-none transition-all z-10
        ${isPlayer
          ? 'bg-violet-900/80 border border-violet-500/70'
          : isTarget
            ? 'bg-red-950/80 border border-red-400/80 ring-1 ring-red-500/50'
            : 'bg-slate-900/80 border border-slate-600/60 hover:border-slate-400/80'}
        ${isActive ? 'shadow-[0_0_8px_2px_rgba(167,139,250,0.35)]' : ''}
      `}
    >
      <span className="text-base leading-none">
        {isPlayer ? '🧙' : '💀'}
      </span>
      <span className="text-[9px] text-white font-semibold leading-tight truncate max-w-full px-0.5 text-center">
        {participant.name ? participant.name.split(' ')[0] : (isPlayer ? 'You' : '?')}
      </span>
      {/* HP bar */}
      <div className="w-full px-1 mt-0.5">
        <div className="h-1 bg-slate-700 rounded-full overflow-hidden">
          <div className={`h-full rounded-full ${hpColor}`} style={{ width: `${pct}%` }} />
        </div>
      </div>
      {isActive && (
        <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-violet-500 border border-slate-900 flex items-center justify-center">
          <span className="text-[7px] text-white font-black leading-none">▶</span>
        </div>
      )}
    </div>
  );
};

// ── Main component ────────────────────────────────────────────────────────────
const BattlefieldGrid = ({
  grid,              // BattlefieldGrid dict from combat_state.battlefield_grid
  enemies,           // allEnemies list from combat_state.enemies (including dead)
  playerGridX,       // int: player column
  playerGridY,       // int: player row
  playerData,        // { name, hp, max_hp, conditions, _isPlayer: true }
  activeTurn,        // id of participant whose turn it is
  selectedTarget,    // id of selected enemy
  onSelectTarget,    // (enemyId) => void
  lightLevel,        // { level, overlay }
  characterState,    // for player data fallback
}) => {
  const cols = grid?.cols ?? 8;
  const rows = grid?.rows ?? 6;

  // Build a map of (x,y) → terrain type
  const cellMap = {};
  (grid?.cells ?? []).forEach(c => {
    cellMap[`${c.x},${c.y}`] = c.type;
  });

  // Build a map of (x,y) → participant
  const tokenMap = {};

  // Player token
  const px = playerGridX ?? 1;
  const py = playerGridY ?? 2;
  const player = playerData ?? {
    id: 'player',
    name: characterState?.identity?.name || characterState?.name || 'You',
    hp: characterState?.hp?.current ?? characterState?.hp ?? 10,
    max_hp: characterState?.hp?.max ?? characterState?.max_hp ?? 10,
    _isPlayer: true,
  };
  tokenMap[`${px},${py}`] = { ...player, _isPlayer: true };

  // Enemy tokens
  (enemies ?? []).forEach(e => {
    const ex = e.grid_x ?? 5;
    const ey = e.grid_y ?? 2;
    // Offset collisions minimally
    let key = `${ex},${ey}`;
    let offset = 0;
    while (tokenMap[key] && offset < rows) {
      offset++;
      key = `${ex},${Math.min(rows - 1, ey + offset)}`;
    }
    tokenMap[key] = e;
  });

  // Dark overlay for distant columns when light is dark
  const isDark = lightLevel?.overlay === 'dark';
  const isDim  = lightLevel?.overlay === 'dim';

  return (
    <div
      className="relative w-full h-full"
      style={{ minHeight: 0 }}
    >
      <div
        className="grid w-full h-full"
        style={{
          gridTemplateColumns: `repeat(${cols}, 1fr)`,
          gridTemplateRows: `repeat(${rows}, 1fr)`,
          gap: '1px',
          background: '#0f172a',
        }}
      >
        {Array.from({ length: rows }).map((_, y) =>
          Array.from({ length: cols }).map((_, x) => {
            const terrainType = cellMap[`${x},${y}`] ?? 'floor';
            const terrain = TERRAIN[terrainType] ?? DEFAULT_CELL;
            const token = tokenMap[`${x},${y}`];
            const isWalkable = !['wall', 'pillar', 'tree', 'rock'].includes(terrainType);

            // Light darkening: cols >= half the grid get overlaid in darkness
            const darkened = isDark && x >= Math.floor(cols / 2);
            const dimmed   = isDim  && x >= Math.floor(cols * 0.7);

            return (
              <div
                key={`${x},${y}`}
                className={`
                  relative
                  ${terrain.bg} border ${terrain.border}
                  ${!isWalkable ? 'opacity-80' : ''}
                `}
              >
                {/* Terrain label (shown only when no token) */}
                {!token && terrain.label && (
                  <span className="absolute inset-0 flex items-center justify-center text-[10px] text-slate-500 select-none pointer-events-none">
                    {terrain.label}
                  </span>
                )}

                {/* Coordinate label for empty walkable cells (subtle) */}
                {!token && isWalkable && !terrain.label && (
                  <span className="absolute bottom-0 right-0.5 text-[7px] text-slate-700 select-none pointer-events-none leading-tight">
                    {x},{y}
                  </span>
                )}

                {/* Participant token */}
                {token && (
                  <GridToken
                    participant={token}
                    isPlayer={token._isPlayer}
                    isActive={activeTurn === (token._isPlayer ? 'player' : token.id)}
                    isTarget={!token._isPlayer && token.id === selectedTarget}
                    onClick={() => !token._isPlayer && token.hp > 0 && onSelectTarget(token.id)}
                  />
                )}

                {/* Darkness overlay */}
                {darkened && (
                  <div className="absolute inset-0 bg-slate-950/55 pointer-events-none z-20 rounded-sm" />
                )}
                {dimmed && (
                  <div className="absolute inset-0 bg-slate-900/30 pointer-events-none z-20 rounded-sm" />
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Legend strip */}
      <div className="absolute bottom-1 left-1 flex items-center gap-2 pointer-events-none">
        <span className="text-[8px] text-slate-600 font-mono">5ft/cell</span>
        {grid?.generated === false && (
          <span className="text-[8px] text-slate-600 italic">default map</span>
        )}
      </div>
    </div>
  );
};

export default BattlefieldGrid;
