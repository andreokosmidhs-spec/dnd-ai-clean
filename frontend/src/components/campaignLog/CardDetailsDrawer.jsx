import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Textarea } from '../ui/textarea';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '../ui/sheet';
import { Star, Calendar, Hash, Info, Lock, Unlock, Dice5, Wand2, Loader2 } from 'lucide-react';
import { CARD_TYPE_CONFIG, getCardFullTitle, getCardTags, getCardFullDetails, normalizeCardType } from './cardTypeConfig';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Card Details Drawer Component
 */
export const CardDetailsDrawer = ({ card, type, isOpen, onClose, isPinned, onTogglePin, campaignId, onCardUpdated }) => {
  const [unsealBusy, setUnsealBusy] = useState(false);
  const [unsealMode, setUnsealMode] = useState(null); // 'roll' | 'creative' | null
  const [creativeText, setCreativeText] = useState('');
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

          {/* Sealed Lead — second-chance UI. The player can roll a check
              (d20 + mod) OR describe a creative approach to unravel it. */}
          {card.type === 'lead' && card.status === 'sealed' && (
            <div className="border-t border-gray-800 pt-4 mt-4 space-y-3" data-testid="sealed-lead-panel">
              <div className="flex items-center gap-2 text-xs text-rose-300">
                <Lock className="w-3.5 h-3.5" />
                <span className="uppercase tracking-wider font-bold">
                  Sealed Lead — {card.reveal_check_type || 'Investigation'} DC {card.reveal_dc || 12}
                </span>
              </div>
              <div className="text-xs text-gray-400 italic">
                You couldn't piece this together in the moment. Try again — roll a fresh
                check, or describe a creative angle.
              </div>

              {unsealMode === null && (
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    className="flex-1 h-9 bg-amber-500 hover:bg-amber-400 text-black font-bold"
                    onClick={async () => {
                      setUnsealBusy(true);
                      try {
                        const die = 1 + Math.floor(Math.random() * 20);
                        const res = await fetch(
                          `${BACKEND_URL}/api/campaigns/${campaignId}/cards/${card.id}/unseal`,
                          {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ mode: 'roll', roll_total: die }),
                          }
                        );
                        const data = await res.json();
                        if (data.unsealed) {
                          toast.success(`Rolled ${die} — unsealed.`);
                          onCardUpdated && onCardUpdated(data.card);
                        } else {
                          toast.error(`Rolled ${die} — still sealed.`);
                        }
                      } catch {
                        toast.error('Unseal failed.');
                      } finally {
                        setUnsealBusy(false);
                      }
                    }}
                    disabled={unsealBusy}
                    data-testid="unseal-roll-btn"
                  >
                    {unsealBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Dice5 className="h-4 w-4 mr-1" />}
                    Roll d20
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1 h-9 border-fuchsia-400/70 text-fuchsia-200 bg-fuchsia-950/40 hover:bg-fuchsia-700/30 font-semibold"
                    onClick={() => setUnsealMode('creative')}
                    disabled={unsealBusy}
                    data-testid="unseal-creative-open-btn"
                  >
                    <Wand2 className="h-4 w-4 mr-1" /> Try a Different Angle
                  </Button>
                </div>
              )}

              {unsealMode === 'creative' && (
                <div className="space-y-2">
                  <Textarea
                    rows={4}
                    value={creativeText}
                    onChange={(e) => setCreativeText(e.target.value)}
                    placeholder='e.g. "I take the medallion to the old loremaster who lives by the river — he might recognize the mark."'
                    className="bg-stone-900 border-fuchsia-500/40 text-amber-50 placeholder:text-amber-100/40 text-sm"
                    data-testid="unseal-creative-input"
                  />
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      className="flex-1 h-9 bg-fuchsia-500 hover:bg-fuchsia-400 text-black font-bold"
                      disabled={unsealBusy || !creativeText.trim()}
                      onClick={async () => {
                        setUnsealBusy(true);
                        try {
                          const res = await fetch(
                            `${BACKEND_URL}/api/campaigns/${campaignId}/cards/${card.id}/unseal`,
                            {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ mode: 'creative', creative_text: creativeText }),
                            }
                          );
                          const data = await res.json();
                          if (data.unsealed) {
                            toast.success('Unsealed.');
                            onCardUpdated && onCardUpdated(data.card);
                            setUnsealMode(null);
                            setCreativeText('');
                          } else {
                            toast.error(data.narration || 'Approach didn\'t work — try another angle.');
                          }
                        } catch {
                          toast.error('Unseal failed.');
                        } finally {
                          setUnsealBusy(false);
                        }
                      }}
                      data-testid="unseal-creative-submit-btn"
                    >
                      {unsealBusy ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Wand2 className="h-4 w-4 mr-1" />}
                      Submit
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-9 text-amber-200"
                      onClick={() => { setUnsealMode(null); setCreativeText(''); }}
                      disabled={unsealBusy}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}

              {Array.isArray(card.targets) && card.targets.length > 0 && (
                <div className="text-xs text-gray-500 mt-1">
                  <span className="uppercase tracking-wider text-gray-400 mr-1">Lead points to:</span>
                  {card.targets.map((t, i) => (
                    <span key={i} className="inline-block mr-1.5 px-1.5 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-200">
                      {t.type}: {t.name}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {card.type === 'lead' && card.status === 'active' && (
            <div className="border-t border-gray-800 pt-4 mt-4">
              <div className="flex items-center gap-2 text-xs text-emerald-300">
                <Unlock className="w-3.5 h-3.5" />
                <span className="uppercase tracking-wider font-bold">Lead revealed</span>
              </div>
            </div>
          )}
          
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
