import React from 'react';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { Star, Sparkles } from 'lucide-react';
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
      
      {/* Color-coded header */}
      <div className={`h-12 bg-gradient-to-r ${config.gradient} flex items-center justify-between px-4`}>
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-white/90" />
          <span className="text-xs font-semibold text-white/90 uppercase tracking-wider">
            {config.label}
          </span>
        </div>
        <Sparkles className="w-4 h-4 text-white/40 group-hover:text-white/70 transition-colors" />
      </div>
      
      {/* Card content */}
      <CardContent className="p-4 space-y-3">
        <h3 className="font-semibold text-white text-base leading-tight line-clamp-2">
          {title}
        </h3>
        
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
