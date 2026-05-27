import React, { useState, useRef, useCallback } from 'react';
import { Star } from 'lucide-react';
import {
  CARD_TYPE_CONFIG,
  getCardTitle,
  normalizeCardType,
  getRarity,
  RARITY_CONFIG,
  getMechanicalRows,
  getStatusStyle,
} from './cardTypeConfig';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const KIND_CLASS = {
  status: '',   // handled separately as a pill
  info:   'text-gray-300',
  warn:   'text-amber-400',
  stat:   'text-cyan-300 font-mono',
  delta:  'text-gray-400 italic',
};

export const KnowledgeCard = ({ data, type, onSelect, isSelected, isPinned, campaignId }) => {
  const normalized = normalizeCardType(type);
  const config = CARD_TYPE_CONFIG[normalized] || CARD_TYPE_CONFIG.locations;
  const Icon = config.icon;
  const title = getCardTitle(data, type);
  const rarity = getRarity(data, normalized);
  const rarityConf = RARITY_CONFIG[rarity];
  const mechRows = getMechanicalRows(data, normalized);
  const [statusRow, ...infoRows] = mechRows;

  const biomeAccent = data?.biome_accent || null;
  const headerGradient = normalized === 'locations' && biomeAccent ? biomeAccent : config.gradient;

  const [isNew, setIsNew] = useState(!!data?.is_new);
  const flaggedRef = useRef(false);

  const handleMouseEnter = useCallback(() => {
    if (!isNew || flaggedRef.current) return;
    flaggedRef.current = true;
    setIsNew(false);
    if (campaignId && data?.id) {
      fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/cards/${data.id}/seen`, { method: 'POST' }).catch(() => {});
      try { window.dispatchEvent(new CustomEvent('rpg:cards-seen', { detail: { campaignId, cardId: data.id } })); } catch {}
    }
  }, [isNew, campaignId, data?.id]);

  // Rarity border override for non-common cards
  const rarityBorder =
    rarity === 'legendary' ? 'border-yellow-500/60' :
    rarity === 'rare'      ? 'border-blue-500/50'   :
    rarity === 'uncommon'  ? 'border-green-500/40'  :
    config.border;

  return (
    <div
      className={`relative aspect-[5/7] rounded-xl overflow-hidden cursor-pointer select-none
        bg-gray-900 border-2 ${rarityBorder}
        transition-all duration-200 hover:-translate-y-1 hover:shadow-xl ${config.glow}
        ${isSelected ? 'ring-2 ring-orange-400 ring-offset-2 ring-offset-gray-950' : ''}
        ${isNew ? 'ring-2 ring-emerald-400 shadow-[0_0_24px_rgba(16,185,129,0.5)]' : ''}
      `}
      onClick={() => onSelect(data, type)}
      onMouseEnter={handleMouseEnter}
      data-testid="knowledge-card"
    >
      {/* NEW ribbon */}
      {isNew && (
        <div className="absolute top-0 left-0 z-20 px-2 py-0.5 bg-emerald-500 text-stone-950 text-[8px] font-black uppercase tracking-widest rounded-br-md">
          New
        </div>
      )}

      {/* Pin star */}
      {isPinned && (
        <div className="absolute top-1.5 right-1.5 z-10">
          <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
        </div>
      )}

      {/* Quantity badge — shown for stackable items (potions, gold, materials) */}
      {(data?.quantity || 0) > 1 && (
        <div className={`absolute z-10 px-1 leading-tight rounded text-[7px] font-bold bg-orange-600/90 text-white ${isPinned ? 'top-1.5 right-5' : 'top-1.5 right-1.5'}`}>
          ×{data.quantity}
        </div>
      )}

      {/* ── Header strip ── */}
      <div className={`h-6 bg-gradient-to-r ${headerGradient} flex items-center justify-between px-2 border-b border-black/40`}>
        <div className="flex items-center gap-1 min-w-0">
          <Icon className="w-3 h-3 text-white/90 shrink-0" />
          <span className="text-[8px] font-bold text-white/90 uppercase tracking-wider truncate">
            {config.label}
          </span>
        </div>
        {/* Rarity gem */}
        <span className={`text-[10px] leading-none ${rarityConf.color}`} title={rarityConf.label}>
          {rarityConf.gem}
        </span>
      </div>

      {/* ── Art well (25% height) ── */}
      <div
        className={`relative h-[25%] bg-gradient-to-br ${headerGradient} overflow-hidden`}
        style={data?.image_url ? { backgroundImage: `url(${data.image_url})`, backgroundSize: 'cover', backgroundPosition: 'center' } : undefined}
      >
        {!data?.image_url && (
          <div className="absolute inset-0 flex items-center justify-center opacity-20">
            <Icon className="w-8 h-8 text-white" />
          </div>
        )}
      </div>

      {/* ── Title / type-line ── */}
      <div className="px-2 py-1 bg-stone-950/70 border-t border-b border-black/30">
        <h3 className="font-bold text-white text-[11px] leading-tight truncate" title={title}>
          {title}
        </h3>
      </div>

      {/* ── Mechanical body ── */}
      <div className="px-2 py-1.5 flex flex-col gap-1 overflow-hidden">
        {/* Status pill */}
        {statusRow && (
          <span className={`self-start px-1.5 py-0 rounded text-[8px] font-semibold uppercase tracking-wide ${getStatusStyle(data?.status)}`}>
            {statusRow.label}
          </span>
        )}

        {/* Info rows */}
        {infoRows.slice(0, 3).map((row, i) => (
          <p key={i} className={`text-[9px] leading-snug truncate ${KIND_CLASS[row.kind] || 'text-gray-300'}`}>
            {row.label}
          </p>
        ))}
      </div>

      {/* ── Footer: rarity label ── */}
      <div className="absolute bottom-0 inset-x-0 px-2 py-1 bg-black/40 flex items-center justify-between">
        <span className={`text-[7px] uppercase tracking-widest font-semibold ${rarityConf.color}`}>
          {rarityConf.label}
        </span>
        {data?.auto_seeded === false && (
          <span className="text-[7px] text-gray-500 italic">pinned</span>
        )}
      </div>
    </div>
  );
};

export default KnowledgeCard;
