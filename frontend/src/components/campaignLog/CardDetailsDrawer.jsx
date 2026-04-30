import React from 'react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '../ui/sheet';
import { Star, Calendar, Hash, Info } from 'lucide-react';
import { CARD_TYPE_CONFIG, getCardFullTitle, getCardTags, getCardFullDetails, normalizeCardType } from './cardTypeConfig';

/**
 * Card Details Drawer Component
 */
export const CardDetailsDrawer = ({ card, type, isOpen, onClose, isPinned, onTogglePin }) => {
  if (!card || !type) return null;
  
  const config = CARD_TYPE_CONFIG[normalizeCardType(type)] || CARD_TYPE_CONFIG.locations;
  const Icon = config.icon;
  const title = getCardFullTitle(card, type);
  const tags = getCardTags(card, type);
  const details = getCardFullDetails(card, type);
  
  // Format date for display
  const formatDate = (dateStr) => {
    if (!dateStr) return null;
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };
  
  const createdAt = formatDate(card.created_at || card.first_visited || card.first_met || card.decided_when);
  const updatedAt = formatDate(card.updated_at);

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent 
        side="right" 
        className="w-full sm:max-w-[400px] bg-gray-950 border-gray-800 p-0 overflow-hidden"
      >
        {/* Color-coded header */}
        <div className={`${config.headerBg} p-4`}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Icon className="w-5 h-5 text-white/90" />
              <span className="text-sm font-semibold text-white/90 uppercase tracking-wider">
                {config.label}
              </span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onTogglePin(card.id)}
              className={`h-8 w-8 p-0 ${isPinned ? 'text-yellow-400' : 'text-white/60 hover:text-yellow-400'}`}
            >
              <Star className={`w-5 h-5 ${isPinned ? 'fill-yellow-400' : ''}`} />
            </Button>
          </div>
          <SheetHeader className="text-left">
            <SheetTitle className="text-xl font-bold text-white">
              {title}
            </SheetTitle>
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {tags.map((tag, idx) => (
                  <Badge 
                    key={idx} 
                    variant="outline" 
                    className="text-xs px-2 py-0.5 bg-white/10 text-white/90 border-white/30"
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
          </SheetHeader>
        </div>
        
        {/* Scrollable content */}
        <div className="overflow-y-auto h-[calc(100vh-140px)] p-4 space-y-4">
          {/* Full details */}
          {details.map((detail, idx) => (
            <div key={idx} className="space-y-1">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                {detail.label}
              </label>
              <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                {detail.prefix || ''}{detail.value}
              </p>
            </div>
          ))}
          
          {/* Biome panel — present only on location cards. Surfaces the
              survival/nature DC modifiers and the resources/animals/
              monsters the player can encounter or harvest there, so
              skill checks and exploration feel grounded. */}
          {(card.biome || card.biome_label) && (
            <div className="border-t border-gray-800 pt-4 mt-4 space-y-3">
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Info className="w-3.5 h-3.5" />
                <span className="uppercase tracking-wider font-medium">
                  Biome · {card.biome_label || card.biome}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs">
                {typeof card.biome_survival_dc_mod === "number" && (
                  <div className="bg-slate-900 border border-slate-800 rounded p-2">
                    <div className="text-slate-500 uppercase text-[10px]">Survival DC</div>
                    <div className="text-slate-200 font-semibold">
                      {card.biome_survival_dc_mod >= 0 ? `+${card.biome_survival_dc_mod}` : card.biome_survival_dc_mod}
                    </div>
                  </div>
                )}
                {typeof card.biome_nature_dc_mod === "number" && (
                  <div className="bg-slate-900 border border-slate-800 rounded p-2">
                    <div className="text-slate-500 uppercase text-[10px]">Nature DC</div>
                    <div className="text-slate-200 font-semibold">
                      {card.biome_nature_dc_mod >= 0 ? `+${card.biome_nature_dc_mod}` : card.biome_nature_dc_mod}
                    </div>
                  </div>
                )}
              </div>
              {[
                ["Resources", card.biome_resources, "text-emerald-300"],
                ["Animals", card.biome_animals, "text-sky-300"],
                ["Monsters", card.biome_monsters, "text-red-300"],
              ].map(([label, list, klass]) =>
                Array.isArray(list) && list.length > 0 ? (
                  <div key={label}>
                    <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">{label}</div>
                    <div className="flex flex-wrap gap-1">
                      {list.map((item) => (
                        <span
                          key={item}
                          className={`text-xs ${klass} bg-slate-900 border border-slate-800 rounded px-2 py-0.5`}
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null
              )}
            </div>
          )}

          {/* Metadata section */}
          <div className="border-t border-gray-800 pt-4 mt-4 space-y-3">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Info className="w-3.5 h-3.5" />
              <span className="uppercase tracking-wider font-medium">Metadata</span>
            </div>
            
            {card.id && (
              <div className="flex items-center gap-2 text-xs">
                <Hash className="w-3 h-3 text-gray-600" />
                <span className="text-gray-600">ID:</span>
                <code className="text-gray-400 font-mono text-xs truncate">{card.id}</code>
              </div>
            )}
            
            {createdAt && (
              <div className="flex items-center gap-2 text-xs">
                <Calendar className="w-3 h-3 text-gray-600" />
                <span className="text-gray-600">Created:</span>
                <span className="text-gray-400">{createdAt}</span>
              </div>
            )}
            
            {updatedAt && (
              <div className="flex items-center gap-2 text-xs">
                <Calendar className="w-3 h-3 text-gray-600" />
                <span className="text-gray-600">Updated:</span>
                <span className="text-gray-400">{updatedAt}</span>
              </div>
            )}
          </div>
        </div>
        
        {/* Hidden description for accessibility */}
        <SheetDescription className="sr-only">
          Details for {config.label}: {title}
        </SheetDescription>
      </SheetContent>
    </Sheet>
  );
};

export default CardDetailsDrawer;
