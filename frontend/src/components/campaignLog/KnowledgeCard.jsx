import React from 'react';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { Star, Sparkles, MapPin } from 'lucide-react';
import { CARD_TYPE_CONFIG, getCardTitle, getCardDescription, getCardTags, normalizeCardType } from './cardTypeConfig';

/**
 * Knowledge Card Component - MTG-style card design
 */
export const KnowledgeCard = ({ data, type, onSelect, isSelected, isPinned }) => {
  const config = CARD_TYPE_CONFIG[normalizeCardType(type)] || CARD_TYPE_CONFIG.locations;
  const Icon = config.icon;
  const title = getCardTitle(data, type);
  const description = getCardDescription(data, type);
  const tags = getCardTags(data, type);
  // Location-origin badge — shown on auto-seeded cards so the player can
  // tell at a glance where each entity / item / spell came from.
  const origin = data?.location_origin || data?.locationOrigin || null;
  const isAutoSeeded = !!data?.auto_seeded;

  // Biome metadata (only set on location-type cards). When present we
  // override the header gradient with the biome's accent so a Forest place
  // looks distinct from a Desert place at a glance — even though both are
  // "locations" green-framed under MTG type rules.
  const biome = data?.biome || null;
  const biomeLabel = data?.biome_label || data?.biomeLabel || null;
  const biomeAccent = data?.biome_accent || data?.biomeAccent || null;
  const headerGradient = (type === 'locations' || normalizeCardType(type) === 'locations') && biomeAccent
    ? biomeAccent
    : config.gradient;

  return (
    <Card 
      className={`bg-gray-900/80 ${config.border} overflow-hidden transition-all duration-300 hover:shadow-lg ${config.glow} hover:-translate-y-1 cursor-pointer group relative ${
        isSelected ? 'ring-2 ring-orange-500 ring-offset-2 ring-offset-gray-950' : ''
      }`}
      onClick={() => onSelect(data, type)}
    >
      {/* Pinned indicator */}
      {isPinned && (
        <div className="absolute top-2 right-2 z-10">
          <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
        </div>
      )}
      
      {/* Color-coded header — biome accent overrides the type gradient
          for location cards so each biome reads visually distinct. */}
      <div className={`h-12 bg-gradient-to-r ${headerGradient} flex items-center justify-between px-4`}>
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-white/90" />
          <span className="text-xs font-semibold text-white/90 uppercase tracking-wider">
            {biomeLabel ? `${config.label} · ${biomeLabel}` : config.label}
          </span>
        </div>
        <Sparkles className="w-4 h-4 text-white/40 group-hover:text-white/70 transition-colors" />
      </div>
      
      {/* Card content */}
      <CardContent className="p-4 space-y-3">
        <h3 className="font-semibold text-white text-base leading-tight line-clamp-2">
          {title}
        </h3>

        {origin && (
          <div
            className="flex items-center gap-1 text-[11px] text-slate-400"
            data-testid="card-location-origin"
            title="Location where this card was added"
          >
            <MapPin className="w-3 h-3" />
            <span>from <span className="text-slate-300 italic">{origin}</span></span>
            {isAutoSeeded && (
              <Badge variant="outline" className="ml-1 px-1 py-0 h-4 text-[9px] border-slate-700 text-slate-400">
                auto
              </Badge>
            )}
          </div>
        )}

        {description && (
          <p className="text-gray-400 text-sm line-clamp-3 leading-relaxed">
            {description}
          </p>
        )}
        
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {tags.map((tag, idx) => (
              <Badge 
                key={idx} 
                variant="outline" 
                className={`text-xs px-2 py-0.5 ${config.badge}`}
              >
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default KnowledgeCard;
