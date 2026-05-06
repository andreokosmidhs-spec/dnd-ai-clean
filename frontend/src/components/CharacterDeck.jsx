import React, { useEffect, useState, useCallback } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from './ui/sheet';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Layers, Loader2, Moon } from 'lucide-react';
import { toast } from 'sonner';
import { rarityMeta, sourceMeta, SOURCE_ORDER } from '../utils/deckRarity';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * CharacterDeck — a Sheet that shows the player's personal deck.
 * Cards are auto-seeded server-side from race / language / background / class
 * + any draws picked up from quests / curses / items.
 *
 * Cards are grouped by `source` and sorted by rarity (legendary first).
 * Per-day cards show their X/Y uses; "Long Rest" button refreshes them.
 */
const CharacterDeck = ({ characterId, characterName }) => {
  const [open, setOpen] = useState(false);
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(false);
  const [resting, setResting] = useState(false);

  const fetchDeck = useCallback(async () => {
    if (!characterId) return;
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/characters/${characterId}/deck`);
      const data = await res.json();
      setCards(data.cards || []);
    } catch (err) {
      console.error('Deck fetch failed', err);
      toast.error('Could not load deck');
    } finally {
      setLoading(false);
    }
  }, [characterId]);

  useEffect(() => {
    if (open) fetchDeck();
  }, [open, fetchDeck]);

  const handleLongRest = async () => {
    setResting(true);
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/characters/${characterId}/deck/long-rest`,
        { method: 'POST' }
      );
      const data = await res.json();
      setCards(data.cards || []);
      toast.success(`Long rest complete — ${data.restored || 0} card${data.restored === 1 ? '' : 's'} refreshed.`);
    } catch (err) {
      toast.error('Long rest failed');
    } finally {
      setResting(false);
    }
  };

  const handleUseCard = async (cardId) => {
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/characters/${characterId}/deck/cards/${cardId}/use`,
        { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }
      );
      const data = await res.json();
      if (data.ok) {
        setCards((prev) => prev.map((c) => (c.id === cardId ? data.card : c)));
        toast.success('Card spent');
      }
    } catch (err) {
      toast.error('Could not spend card');
    }
  };

  // Group + sort
  const grouped = SOURCE_ORDER.reduce((acc, src) => {
    const list = (cards || [])
      .filter((c) => c.source === src && c.status === 'active')
      .sort((a, b) => {
        const order = { legendary: 0, epic: 1, rare: 2, common: 3 };
        return (order[a.rarity] ?? 9) - (order[b.rarity] ?? 9);
      });
    if (list.length) acc[src] = list;
    return acc;
  }, {});

  const totalActive = cards.filter((c) => c.status === 'active').length;
  const epicLegendary = cards.filter(
    (c) => c.status === 'active' && (c.rarity === 'epic' || c.rarity === 'legendary')
  ).length;

  if (!characterId) return null;

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <button
          type="button"
          data-testid="deck-button"
          className="group inline-flex items-center gap-2 rounded-full border border-fuchsia-500/40 bg-fuchsia-950/30 hover:bg-fuchsia-900/40 hover:border-fuchsia-400/60 transition-colors px-3 py-1.5 text-xs font-medium text-fuchsia-100 shadow-sm"
        >
          <Layers size={14} className="text-fuchsia-300" />
          <span>Deck</span>
          {epicLegendary > 0 && (
            <Badge
              variant="outline"
              className="h-5 px-1.5 text-[10px] border-amber-400/60 text-amber-200 bg-amber-900/30"
            >
              ✦ {epicLegendary}
            </Badge>
          )}
        </button>
      </SheetTrigger>
      <SheetContent
        side="right"
        className="w-full sm:max-w-lg bg-stone-950 border-stone-700 text-amber-50 overflow-y-auto"
        data-testid="deck-sheet"
      >
        <SheetHeader>
          <SheetTitle className="text-fuchsia-300 flex items-center gap-2">
            <Layers size={18} />
            {characterName ? `${characterName}'s Deck` : 'Character Deck'}
            <Badge
              variant="outline"
              className="ml-1 text-xs border-fuchsia-400/50 text-fuchsia-200"
            >
              {totalActive} active
            </Badge>
          </SheetTitle>
          <p className="text-xs text-stone-300/80 italic mt-1">
            Your character's identity & resources. The DM consults this deck to
            shape narration — what you can perceive, speak, call upon, or do.
          </p>
        </SheetHeader>

        <div className="mt-3 flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={handleLongRest}
            disabled={loading || resting}
            className="h-8 border-indigo-500/50 text-indigo-100 hover:bg-indigo-900/30"
            data-testid="deck-long-rest-btn"
          >
            {resting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
            ) : (
              <Moon className="h-3.5 w-3.5 mr-1" />
            )}
            Long Rest
          </Button>
          <span className="text-[11px] text-stone-400">
            Restores per-day uses on Rage, spell slots, Lay on Hands, etc.
          </span>
        </div>

        <div className="mt-4 space-y-4">
          {loading && (
            <div className="text-stone-400 italic text-sm flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" /> Drawing cards…
            </div>
          )}

          {!loading && totalActive === 0 && (
            <div className="text-stone-400 italic text-sm">
              Your deck is empty. Cards seed automatically from your race,
              class, background, and languages.
            </div>
          )}

          {!loading && Object.entries(grouped).map(([src, list]) => {
            const meta = sourceMeta(src);
            return (
              <section key={src} data-testid={`deck-section-${src}`}>
                <h4 className={`text-xs font-bold tracking-wide uppercase mb-2 flex items-center gap-1.5 ${meta.color}`}>
                  <span className="text-base leading-none" aria-hidden="true">{meta.icon}</span>
                  {meta.label}
                  <span className="text-stone-500 ml-1 normal-case font-normal">({list.length})</span>
                </h4>
                <div className="space-y-2">
                  {list.map((card) => (
                    <DeckCard
                      key={card.id}
                      card={card}
                      onUse={() => handleUseCard(card.id)}
                    />
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      </SheetContent>
    </Sheet>
  );
};

const DeckCard = ({ card, onUse }) => {
  const r = rarityMeta(card.rarity);
  const hasUses = !!(card.uses_max && card.uses_max > 0);
  const usesText = hasUses ? `${card.uses_remaining}/${card.uses_max}` : '';
  const canSpend = hasUses && card.uses_remaining > 0;

  return (
    <div
      className={`rounded-md border-2 ${r.borderClass} ${r.glow} bg-stone-900/85 p-3`}
      data-testid={`deck-card-${card.id}`}
      data-rarity={card.rarity}
    >
      <div className="flex items-start gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            <Badge
              className={`text-[10px] ${r.chipBg} ${r.chipText} border-0 px-1.5 py-0 leading-tight uppercase tracking-wide`}
              data-testid={`deck-rarity-${card.rarity}`}
            >
              {r.label}
            </Badge>
            {card.per_day && (
              <Badge
                variant="outline"
                className="text-[10px] border-indigo-400/50 text-indigo-200 bg-indigo-950/40"
              >
                per day
              </Badge>
            )}
            {hasUses && (
              <Badge
                variant="outline"
                className="text-[10px] border-amber-400/50 text-amber-200 bg-amber-950/40"
              >
                {usesText}
              </Badge>
            )}
          </div>
          <h5 className={`mt-1 text-sm font-semibold ${r.accentText}`}>
            {card.title}
          </h5>
          <p className="text-[12px] text-stone-300/85 mt-1 leading-snug">
            {card.description}
          </p>
          {card.mechanical && (
            <p className="text-[10.5px] mt-1 italic text-stone-400/85">
              ⌬ {card.mechanical}
            </p>
          )}
        </div>
        {canSpend && (
          <Button
            size="sm"
            variant="outline"
            className="h-7 border-amber-500/40 text-amber-200 hover:bg-amber-900/30 text-[11px] shrink-0"
            onClick={onUse}
            data-testid={`deck-use-${card.id}`}
            title="Spend one use"
          >
            Use
          </Button>
        )}
      </div>
    </div>
  );
};

export default CharacterDeck;
