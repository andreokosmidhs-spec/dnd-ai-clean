import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from './ui/sheet';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Layers, Loader2, Moon, ImagePlus, X } from 'lucide-react';
import { toast } from 'sonner';
import { rarityMeta, sourceMeta, SOURCE_ORDER } from '../utils/deckRarity';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * CharacterDeck — slide-over showing the player's deck with MTG-style cards.
 *   ┌────────────────────────────┐
 *   │  Title              Rarity │  <- top bar (rarity-colored)
 *   ├────────────────────────────┤
 *   │     [art panel]            │  <- player-uploaded image (or upload prompt)
 *   ├────────────────────────────┤
 *   │  source — type-line        │  <- generated
 *   ├────────────────────────────┤
 *   │  description               │  <- rules box
 *   │  ⌬ mechanical              │
 *   └────────────────────────────┘
 * Card art is keyed on (source, title) and saved to a global library so the
 * player's chosen artwork follows them across characters and campaigns.
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

  const handleArtUpload = async (cardId, dataUrl) => {
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/characters/${characterId}/deck/cards/${cardId}/art`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ data_url: dataUrl }),
        }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Upload failed');
        return;
      }
      const data = await res.json();
      // Update every card in the deck that shares the same art_key.
      setCards((prev) =>
        prev.map((c) =>
          c.art_key === data.art_key ? { ...c, art_data_url: dataUrl } : c
        )
      );
      toast.success('Card art updated — saved across all your characters.');
    } catch (err) {
      toast.error('Upload failed');
    }
  };

  const handleArtClear = async (cardId) => {
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/characters/${characterId}/deck/cards/${cardId}/art`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ data_url: null }),
        }
      );
      const data = await res.json();
      if (data.ok) {
        setCards((prev) =>
          prev.map((c) =>
            c.art_key === data.art_key ? { ...c, art_data_url: null } : c
          )
        );
        toast.success('Art cleared');
      }
    } catch (err) {
      toast.error('Could not clear art');
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
            Click any art panel to upload your own image — saved across every
            character you'll ever play.
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

        <div className="mt-4 space-y-5">
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
                <div className="grid grid-cols-1 gap-3">
                  {list.map((card) => (
                    <DeckCard
                      key={card.id}
                      card={card}
                      onUse={() => handleUseCard(card.id)}
                      onArtUpload={(dataUrl) => handleArtUpload(card.id, dataUrl)}
                      onArtClear={() => handleArtClear(card.id)}
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

// ----------- Image helpers -----------

/** Resize a File to a 512x512 cover-cropped JPEG dataURL (~quality 0.82).
 * Keeps the upload payload reasonable (~80-200 KB) regardless of input size. */
async function fileToResizedDataUrl(file, target = 512, quality = 0.82) {
  const blobUrl = URL.createObjectURL(file);
  try {
    const img = await new Promise((resolve, reject) => {
      const i = new Image();
      i.onload = () => resolve(i);
      i.onerror = reject;
      i.src = blobUrl;
    });
    const canvas = document.createElement('canvas');
    canvas.width = target;
    canvas.height = target;
    const ctx = canvas.getContext('2d');
    // cover-crop: scale so the shorter side fills target, center the longer.
    const scale = Math.max(target / img.width, target / img.height);
    const sw = target / scale;
    const sh = target / scale;
    const sx = (img.width - sw) / 2;
    const sy = (img.height - sh) / 2;
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, target, target);
    return canvas.toDataURL('image/jpeg', quality);
  } finally {
    URL.revokeObjectURL(blobUrl);
  }
}

// ----------- DeckCard (MTG-style frame) -----------

const DeckCard = ({ card, onUse, onArtUpload, onArtClear }) => {
  const r = rarityMeta(card.rarity);
  const meta = sourceMeta(card.source);
  const fileRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const hasUses = !!(card.uses_max && card.uses_max > 0);
  const usesText = hasUses ? `${card.uses_remaining}/${card.uses_max}` : '';
  const canSpend = hasUses && card.uses_remaining > 0;

  const onFilePicked = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = ''; // allow re-select same file
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      toast.error('Pick an image file');
      return;
    }
    setUploading(true);
    try {
      const dataUrl = await fileToResizedDataUrl(file, 512, 0.82);
      await onArtUpload(dataUrl);
    } catch (err) {
      console.error(err);
      toast.error('Could not process image');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div
      className={`relative rounded-md overflow-hidden border-2 ${r.borderClass} ${r.glow} bg-stone-900`}
      data-testid={`deck-card-${card.id}`}
      data-rarity={card.rarity}
    >
      {/* Title bar */}
      <div className={`flex items-center justify-between gap-2 px-2.5 py-1.5 ${r.chipBg}`}>
        <h5 className={`text-sm font-bold truncate ${r.chipText}`}>
          {card.title}
        </h5>
        <Badge
          className={`text-[9px] bg-stone-950/40 ${r.chipText} border-0 px-1.5 py-0 leading-tight uppercase tracking-wider shrink-0`}
          data-testid={`deck-rarity-${card.rarity}`}
        >
          {r.label}
        </Badge>
      </div>

      {/* Art panel — click to upload */}
      <div className="relative aspect-[5/4] bg-gradient-to-br from-stone-800 to-stone-900 group">
        {card.art_data_url ? (
          <>
            <img
              src={card.art_data_url}
              alt={card.title}
              className="absolute inset-0 w-full h-full object-cover"
              data-testid={`deck-card-art-${card.id}`}
            />
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity bg-black/55 flex items-center justify-center gap-2">
              <Button
                size="sm"
                variant="outline"
                className="h-7 border-amber-400/60 text-amber-100 hover:bg-amber-900/40 text-[11px] bg-stone-950/80"
                onClick={() => fileRef.current?.click()}
                disabled={uploading}
                data-testid={`deck-art-replace-${card.id}`}
              >
                {uploading ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <ImagePlus className="h-3 w-3 mr-1" />}
                Replace
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-7 border-red-400/60 text-red-100 hover:bg-red-900/40 text-[11px] bg-stone-950/80"
                onClick={onArtClear}
                disabled={uploading}
                data-testid={`deck-art-clear-${card.id}`}
              >
                <X className="h-3 w-3 mr-1" /> Clear
              </Button>
            </div>
          </>
        ) : (
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            data-testid={`deck-art-upload-${card.id}`}
            className="absolute inset-0 flex flex-col items-center justify-center gap-1.5 text-stone-400 hover:text-amber-200 hover:bg-stone-800/60 transition-colors"
            title="Click to upload card art (saved for every future character)"
          >
            {uploading ? (
              <Loader2 className="h-6 w-6 animate-spin" />
            ) : (
              <ImagePlus className="h-7 w-7 opacity-80" />
            )}
            <span className="text-[10.5px] font-medium tracking-wide uppercase">
              {uploading ? 'Processing…' : 'Upload Art'}
            </span>
            <span className="text-[9px] opacity-70 italic max-w-[80%] text-center">
              Saved across every character you play
            </span>
          </button>
        )}
        <input
          type="file"
          ref={fileRef}
          accept="image/*"
          onChange={onFilePicked}
          className="hidden"
          data-testid={`deck-art-input-${card.id}`}
        />
      </div>

      {/* Type line */}
      <div className={`flex items-center justify-between gap-2 px-2.5 py-1 bg-stone-950/85 border-y ${r.borderClass}`}>
        <p className={`text-[11px] font-semibold ${meta.color}`}>
          <span className="mr-1.5" aria-hidden="true">{meta.icon}</span>
          {r.label} {meta.label}
          {card.mechanical && (
            <span className="text-stone-500 font-normal"> — {card.title.length > 0 ? '' : ''}</span>
          )}
        </p>
        <div className="flex items-center gap-1.5">
          {card.per_day && (
            <Badge
              variant="outline"
              className="text-[9px] border-indigo-400/50 text-indigo-200 bg-indigo-950/40 px-1 py-0 leading-tight"
            >
              per day
            </Badge>
          )}
          {hasUses && (
            <Badge
              variant="outline"
              className="text-[9px] border-amber-400/50 text-amber-200 bg-amber-950/40 px-1 py-0 leading-tight"
            >
              {usesText}
            </Badge>
          )}
          {canSpend && (
            <Button
              size="sm"
              variant="outline"
              className="h-5 border-amber-500/50 text-amber-200 hover:bg-amber-900/30 text-[10px] px-1.5 leading-tight"
              onClick={onUse}
              data-testid={`deck-use-${card.id}`}
              title="Spend one use"
            >
              Use
            </Button>
          )}
        </div>
      </div>

      {/* Rules box */}
      <div className="px-2.5 py-2 bg-stone-900/95 text-[12px] leading-snug text-stone-100/90">
        <p>{card.description}</p>
        {card.mechanical && (
          <p className="mt-1.5 italic text-stone-300/85 text-[10.5px]">
            ⌬ {card.mechanical}
          </p>
        )}
      </div>
    </div>
  );
};

export default CharacterDeck;
