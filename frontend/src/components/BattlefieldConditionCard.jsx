/**
 * BattlefieldConditionCard
 *
 * MTG-inspired card design for battlefield environment conditions.
 * - Art panel top (AI-generated, or gradient placeholder while loading)
 * - Title bar with rarity accent
 * - Description text (narrative, not mechanical)
 * - Tag chips
 * - Animated rarity glow + 3D mouse-tilt hover
 * - "Click to use" affordance
 */
import React, { useState, useRef, useCallback } from 'react';
import { Loader2, Wand2, MousePointerClick, ImageOff } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// ── Rarity config ─────────────────────────────────────────────────────────────
const RARITY = {
  common: {
    glow:       'animate-glow-common',
    border:     'border-slate-500/70',
    title_bg:   'bg-slate-800/90',
    accent:     'bg-slate-500',
    label:      'text-slate-400',
    gradient:   'from-slate-800 via-slate-700 to-slate-800',
  },
  uncommon: {
    glow:       'animate-glow-uncommon',
    border:     'border-emerald-600/70',
    title_bg:   'bg-emerald-950/90',
    accent:     'bg-emerald-500',
    label:      'text-emerald-400',
    gradient:   'from-emerald-950 via-emerald-900 to-emerald-950',
  },
  rare: {
    glow:       'animate-glow-rare',
    border:     'border-blue-500/70',
    title_bg:   'bg-blue-950/90',
    accent:     'bg-blue-500',
    label:      'text-blue-400',
    gradient:   'from-blue-950 via-blue-900 to-blue-950',
  },
  epic: {
    glow:       'animate-glow-epic',
    border:     'border-violet-500/70',
    title_bg:   'bg-violet-950/90',
    accent:     'bg-violet-500',
    label:      'text-violet-400',
    gradient:   'from-violet-950 via-purple-900 to-violet-950',
  },
};

const TAG_COLORS = {
  terrain:           'bg-amber-900/60 text-amber-300',
  hazard:            'bg-red-900/60 text-red-300',
  cover:             'bg-blue-900/60 text-blue-300',
  stealth:           'bg-slate-700 text-slate-300',
  movement:          'bg-orange-900/60 text-orange-300',
  improvised_weapon: 'bg-yellow-900/60 text-yellow-300',
  high_ground:       'bg-cyan-900/60 text-cyan-300',
  visibility:        'bg-purple-900/60 text-purple-300',
  magical:           'bg-pink-900/60 text-pink-300',
  water:             'bg-blue-900/60 text-blue-200',
  fall:              'bg-red-950/70 text-red-400',
  light:             'bg-yellow-900/60 text-yellow-200',
  shadow:            'bg-slate-800 text-slate-400',
  sound:             'bg-indigo-900/60 text-indigo-300',
};

// ── 3-D tilt hook ─────────────────────────────────────────────────────────────
function useTilt(strength = 12) {
  const ref = useRef(null);
  const [tilt, setTilt] = useState({ rx: 0, ry: 0, gx: 50, gy: 50 });

  const onMouseMove = useCallback((e) => {
    const el = ref.current;
    if (!el) return;
    const { left, top, width, height } = el.getBoundingClientRect();
    const x = (e.clientX - left) / width;
    const y = (e.clientY - top)  / height;
    setTilt({
      rx:  (y - 0.5) * -strength,
      ry:  (x - 0.5) *  strength,
      gx:  Math.round(x * 100),
      gy:  Math.round(y * 100),
    });
  }, [strength]);

  const onMouseLeave = useCallback(() => {
    setTilt({ rx: 0, ry: 0, gx: 50, gy: 50 });
  }, []);

  return { ref, tilt, onMouseMove, onMouseLeave };
}

// ── Art placeholder ───────────────────────────────────────────────────────────
const ArtPlaceholder = ({ rarity = 'common', title }) => {
  const r = RARITY[rarity] || RARITY.common;
  return (
    <div className={`w-full h-full bg-gradient-to-br ${r.gradient} flex flex-col items-center justify-center gap-2`}>
      <ImageOff size={22} className="text-slate-600" />
      <span className="text-slate-600 text-[10px] text-center px-2 leading-tight">{title}</span>
    </div>
  );
};

// ── Shimmer skeleton ──────────────────────────────────────────────────────────
const ArtShimmer = () => (
  <div
    className="w-full h-full animate-shimmer rounded-t-2xl"
    style={{
      background: 'linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%)',
      backgroundSize: '400px 100%',
    }}
  />
);

// ── Main card ─────────────────────────────────────────────────────────────────
const BattlefieldConditionCard = ({
  condition,
  onClick,
  compact = false,
  campaignId,
  onArtGenerated,
}) => {
  const rarity  = condition.rarity || 'common';
  const R       = RARITY[rarity] || RARITY.common;
  const tags    = (condition.tags || []).slice(0, 3);
  const source  = condition.source || 'biome';

  const [artUrl,        setArtUrl]        = useState(condition.art_data_url || null);
  const [artLoading,    setArtLoading]    = useState(false);
  const [artError,      setArtError]      = useState(false);
  const { ref, tilt, onMouseMove, onMouseLeave } = useTilt(compact ? 6 : 10);

  const conditionId = condition.condition_id || condition.id;

  // ── Generate art ────────────────────────────────────────────────────────────
  const handleGenerateArt = useCallback(async (e) => {
    e.stopPropagation();
    if (!campaignId || !conditionId || artLoading) return;
    setArtLoading(true);
    setArtError(false);
    try {
      const res  = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/combat/conditions/${conditionId}/art`,
        { method: 'POST' }
      );
      const data = await res.json();
      if (data.art_url) {
        setArtUrl(data.art_url);
        if (onArtGenerated) onArtGenerated(conditionId, data.art_url);
      } else {
        setArtError(true);
      }
    } catch {
      setArtError(true);
    } finally {
      setArtLoading(false);
    }
  }, [campaignId, conditionId, artLoading, onArtGenerated]);

  // ── Card sizes ───────────────────────────────────────────────────────────────
  const artH     = compact ? 'h-24'  : 'h-44';
  const cardW    = compact ? 'w-40'  : 'w-56';
  const titleSz  = compact ? 'text-[11px]' : 'text-sm';
  const descSz   = compact ? 'hidden'      : 'text-[11px]';

  return (
    <div
      ref={ref}
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
      onClick={onClick}
      className={`
        animate-card-enter relative flex-shrink-0 rounded-2xl border cursor-pointer
        overflow-hidden select-none transition-all duration-200
        ${R.border} ${R.glow} ${cardW}
        bg-slate-950/95
      `}
      style={{
        transform: `perspective(600px) rotateX(${tilt.rx}deg) rotateY(${tilt.ry}deg)`,
        transformStyle: 'preserve-3d',
        willChange: 'transform',
      }}
    >
      {/* ── rarity accent top bar ─────────────────────────────────────── */}
      <div className={`h-0.5 w-full ${R.accent}`} />

      {/* ── art panel ─────────────────────────────────────────────────── */}
      <div className={`relative ${artH} overflow-hidden`}>
        {artLoading ? (
          <ArtShimmer />
        ) : artUrl ? (
          <img
            src={artUrl}
            alt={condition.title}
            className="w-full h-full object-cover animate-art-reveal"
          />
        ) : (
          <ArtPlaceholder rarity={rarity} title={condition.title} />
        )}

        {/* tilt glare overlay */}
        <div
          className="absolute inset-0 pointer-events-none rounded-t-2xl"
          style={{
            background: `radial-gradient(circle at ${tilt.gx}% ${tilt.gy}%, rgba(255,255,255,0.08) 0%, transparent 70%)`,
          }}
        />

        {/* generate art button (bottom-right of art area) */}
        {!artUrl && !artLoading && campaignId && (
          <button
            onClick={handleGenerateArt}
            title="Generate card art"
            className="absolute bottom-1.5 right-1.5 flex items-center gap-1 px-2 py-1 rounded-lg
                       bg-black/60 border border-white/10 text-white/70 hover:text-white
                       hover:bg-black/80 text-[10px] transition-all backdrop-blur-sm"
          >
            <Wand2 size={10} />
            {!compact && <span>Generate art</span>}
          </button>
        )}

        {artLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/40">
            <Loader2 size={20} className="animate-spin text-violet-400" />
          </div>
        )}

        {/* DM badge */}
        {source === 'dm' && (
          <span className="absolute top-1.5 left-1.5 text-[9px] px-1.5 py-0.5 rounded
                           bg-amber-800/80 text-amber-300 border border-amber-600/50
                           font-bold uppercase backdrop-blur-sm">
            DM
          </span>
        )}
      </div>

      {/* ── title bar ─────────────────────────────────────────────────── */}
      <div className={`px-2.5 py-1.5 ${R.title_bg} border-t border-white/5`}>
        <div className="flex items-center justify-between gap-1">
          <span className={`text-white font-bold leading-tight truncate ${titleSz}`}>
            {condition.title}
          </span>
          <span className={`flex-shrink-0 text-[9px] uppercase font-semibold ${R.label}`}>
            {rarity}
          </span>
        </div>
      </div>

      {/* ── description ───────────────────────────────────────────────── */}
      {!compact && (
        <div className="px-2.5 pt-1.5 pb-1">
          <p className={`${descSz} text-slate-400 leading-relaxed line-clamp-3`}>
            {condition.description}
          </p>
        </div>
      )}

      {/* ── tags ──────────────────────────────────────────────────────── */}
      {tags.length > 0 && (
        <div className="px-2.5 py-1.5 flex flex-wrap gap-1">
          {tags.map(tag => (
            <span
              key={tag}
              className={`text-[9px] px-1.5 py-0.5 rounded-full capitalize
                ${TAG_COLORS[tag] || 'bg-slate-800 text-slate-400'}`}
            >
              {tag.replace('_', ' ')}
            </span>
          ))}
        </div>
      )}

      {/* ── interact hint ─────────────────────────────────────────────── */}
      <div className="px-2.5 pb-2 flex items-center gap-1 text-[9px] text-slate-600
                      group-hover:text-violet-400 transition-colors">
        <MousePointerClick size={9} />
        <span>Click to interact</span>
      </div>
    </div>
  );
};

export default BattlefieldConditionCard;
