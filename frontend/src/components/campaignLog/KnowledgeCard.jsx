import React, { useState, useRef, useCallback } from 'react';
import { Badge } from '../ui/badge';
import { Star, MapPin, Sparkles } from 'lucide-react';
import { CARD_TYPE_CONFIG, getCardTitle, getCardDescription, getCardTags, normalizeCardType } from './cardTypeConfig';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * KnowledgeCard — uniform MTG-portrait card used in the deck library grid.
 * Aspect ratio matches the image the player referenced (~ 5:7) so any card
 * type (character / location / faction / lore / lead / quest) reads the
 * same shape and size across the whole library.
 *
 * Newly-minted cards stamp `is_new=true` server-side; this component shows
 * a glowing emerald highlight border until the player hovers (clearing
 * locally for immediate feedback and POSTing /seen to clear server-side
 * so the badge counter on the deck button drops too).
 */
export const KnowledgeCard = ({ data, type, onSelect, isSelected, isPinned, campaignId }) => {
  const config = CARD_TYPE_CONFIG[normalizeCardType(type)] || CARD_TYPE_CONFIG.locations;
  const Icon = config.icon;
  const title = getCardTitle(data, type);
  const description = getCardDescription(data, type);
  const tags = getCardTags(data, type);

  const origin = data?.location_origin || data?.locationOrigin || null;
  const isAutoSeeded = !!data?.auto_seeded;

  const biomeLabel = data?.biome_label || data?.biomeLabel || null;
  const biomeAccent = data?.biome_accent || data?.biomeAccent || null;
  const headerGradient = (normalizeCardType(type) === 'locations') && biomeAccent
    ? biomeAccent
    : config.gradient;

  // Local mirror of is_new so the highlight clears instantly on hover even
  // before the server PATCH lands. The server confirms via the `/seen`
  // endpoint and the deck refresh picks up the truth on next load.
  const [isNew, setIsNew] = useState(!!data?.is_new);
  const hasFlaggedRef = useRef(false);

  const handleMouseEnter = useCallback(() => {
    if (!isNew || hasFlaggedRef.current) return;
    hasFlaggedRef.current = true;
    setIsNew(false);
    if (campaignId && data?.id) {
      // Fire-and-forget; if it fails we'll just re-flag on next reload.
      fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/cards/${data.id}/seen`, {
        method: 'POST',
      }).catch(() => {});
      try {
        window.dispatchEvent(new CustomEvent('rpg:cards-seen', {
          detail: { campaignId, cardId: data.id },
        }));
      } catch {}
    }
  }, [isNew, campaignId, data?.id]);

  return (
    <div
      className={`relative aspect-[5/7] rounded-lg overflow-hidden cursor-pointer transition-all duration-200
        bg-gray-900/85 border-2 ${config.border}
        hover:-translate-y-0.5 hover:shadow-lg ${config.glow}
        ${isSelected ? 'ring-2 ring-orange-500 ring-offset-2 ring-offset-gray-950' : ''}
        ${isNew ? 'ring-2 ring-emerald-400 shadow-[0_0_24px_rgba(16,185,129,0.55)] animate-pulse-once' : ''}
      `}
      onClick={() => onSelect(data, type)}
      onMouseEnter={handleMouseEnter}
      data-testid="knowledge-card"
      data-is-new={isNew ? '1' : '0'}
    >
      {/* NEW corner ribbon — only while is_new */}
      {isNew && (
        <div
          className="absolute top-0 left-0 z-20 px-2 py-0.5 bg-emerald-500 text-stone-950 text-[9px] font-black uppercase tracking-widest rounded-br-md"
          data-testid="knowledge-card-new-ribbon"
        >
          New
        </div>
      )}

      {/* Pin indicator */}
      {isPinned && (
        <div className="absolute top-1.5 right-1.5 z-10">
          <Star className="w-3.5 h-3.5 text-yellow-400 fill-yellow-400" />
        </div>
      )}

      {/* Header strip — type label + icon */}
      <div className={`h-7 bg-gradient-to-r ${headerGradient} flex items-center justify-between px-2 border-b border-black/40`}>
        <div className="flex items-center gap-1 min-w-0">
          <Icon className="w-3 h-3 text-white/95 shrink-0" />
          <span className="text-[9px] font-bold text-white/95 uppercase tracking-wider truncate">
            {biomeLabel ? `${config.label} · ${biomeLabel}` : config.label}
          </span>
        </div>
        <Sparkles className="w-3 h-3 text-white/50" />
      </div>

      {/* Art well — gradient placeholder; replaced with custom image when present */}
      <div
        className={`relative h-[38%] w-full bg-gradient-to-br ${headerGradient} overflow-hidden`}
        style={data?.image_url ? { backgroundImage: `url(${data.image_url})`, backgroundSize: 'cover', backgroundPosition: 'center' } : undefined}
      >
        {!data?.image_url && (
          <div className="absolute inset-0 flex items-center justify-center opacity-30">
            <Icon className="w-10 h-10 text-white" />
          </div>
        )}
      </div>

      {/* Type-line */}
      <div className="px-2 py-1 bg-stone-950/60 border-t border-b border-black/30">
        <h3 className="font-bold text-white text-[12px] leading-tight truncate" title={title}>
          {title}
        </h3>
      </div>

      {/* Body */}
      <div className="px-2 py-1.5 space-y-1 flex-1 overflow-hidden">
        {description && (
          <p className="text-gray-300 text-[10.5px] leading-snug italic font-serif line-clamp-4">
            {description}
          </p>
        )}

        {origin && (
          <div className="flex items-center gap-1 text-[9px] text-slate-400" title="Location where this card was added">
            <MapPin className="w-2.5 h-2.5" />
            <span className="truncate">from <span className="text-slate-300">{origin}</span></span>
            {isAutoSeeded && (
              <Badge variant="outline" className="ml-0.5 px-1 py-0 h-3 text-[7px] border-slate-700 text-slate-400">
                auto
              </Badge>
            )}
          </div>
        )}

        {tags.length > 0 && (
          <div className="flex flex-wrap gap-0.5">
            {tags.slice(0, 2).map((tag, idx) => (
              <Badge
                key={idx}
                variant="outline"
                className={`text-[8px] px-1 py-0 leading-tight ${config.badge}`}
              >
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeCard;
