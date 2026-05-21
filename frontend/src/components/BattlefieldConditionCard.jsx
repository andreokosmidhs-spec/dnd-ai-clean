import React from 'react';
import { Sparkles, MousePointerClick } from 'lucide-react';

const RARITY_STYLE = {
  common:   'border-slate-600/60 bg-slate-900/70',
  uncommon: 'border-emerald-700/60 bg-emerald-950/40',
  rare:     'border-blue-600/60 bg-blue-950/40',
  epic:     'border-violet-600/60 bg-violet-950/40',
};

const RARITY_ACCENT = {
  common:   'bg-slate-600',
  uncommon: 'bg-emerald-500',
  rare:     'bg-blue-500',
  epic:     'bg-violet-500',
};

const TAG_COLORS = {
  terrain:           'bg-amber-900/50 text-amber-300 border-amber-700/40',
  hazard:            'bg-red-900/50 text-red-300 border-red-700/40',
  cover:             'bg-blue-900/50 text-blue-300 border-blue-700/40',
  stealth:           'bg-slate-800 text-slate-300 border-slate-600/40',
  movement:          'bg-orange-900/50 text-orange-300 border-orange-700/40',
  improvised_weapon: 'bg-yellow-900/50 text-yellow-300 border-yellow-700/40',
  high_ground:       'bg-cyan-900/50 text-cyan-300 border-cyan-700/40',
  visibility:        'bg-purple-900/50 text-purple-300 border-purple-700/40',
  magical:           'bg-pink-900/50 text-pink-300 border-pink-700/40',
  water:             'bg-blue-900/50 text-blue-200 border-blue-600/40',
  fall:              'bg-red-950/60 text-red-400 border-red-800/40',
};

const BattlefieldConditionCard = ({ condition, onClick, compact = false }) => {
  const rarity = condition.rarity || 'common';
  const tags = (condition.tags || []).slice(0, 3);
  const source = condition.source || 'biome';

  return (
    <div
      onClick={onClick}
      className={`
        group relative rounded-xl border cursor-pointer transition-all duration-150
        hover:scale-[1.02] hover:shadow-lg hover:shadow-black/40
        ${RARITY_STYLE[rarity] || RARITY_STYLE.common}
        ${compact ? 'p-2.5 min-w-[160px] max-w-[200px]' : 'p-3 w-full'}
      `}
      title="Click to interact with this environment"
    >
      {/* rarity accent bar */}
      <div className={`absolute top-0 left-0 right-0 h-0.5 rounded-t-xl ${RARITY_ACCENT[rarity] || RARITY_ACCENT.common}`} />

      <div className="flex items-start justify-between gap-2 mb-1.5">
        <span className={`text-white font-semibold leading-tight ${compact ? 'text-xs' : 'text-sm'}`}>
          {condition.title}
        </span>
        {/* DM badge */}
        {source === 'dm' && (
          <span className="flex-shrink-0 text-[9px] px-1.5 py-0.5 rounded bg-amber-800/60 text-amber-300 border border-amber-700/50 font-bold uppercase">
            DM
          </span>
        )}
      </div>

      {!compact && (
        <p className="text-slate-400 text-[11px] leading-relaxed line-clamp-3 mb-2">
          {condition.description}
        </p>
      )}

      {/* tags */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {tags.map(tag => (
            <span
              key={tag}
              className={`text-[9px] px-1.5 py-0.5 rounded border capitalize
                ${TAG_COLORS[tag] || 'bg-slate-800 text-slate-400 border-slate-700/40'}`}
            >
              {tag.replace('_', ' ')}
            </span>
          ))}
        </div>
      )}

      {/* interact hint */}
      <div className={`
        flex items-center gap-1 text-[10px] text-slate-500
        group-hover:text-violet-400 transition-colors
      `}>
        <MousePointerClick size={10} />
        <span>Click to use this environment</span>
      </div>
    </div>
  );
};

export default BattlefieldConditionCard;
