/**
 * Beat-card helpers — derive category color (from target type), rarity tier
 * (from DC) and other visual metadata from a raw beat object. Centralizing
 * here keeps the BeatEventCard JSX clean and lets us reuse the mapping
 * elsewhere (carousel previews, recap, etc.).
 */
import { CARD_TYPE_CONFIG } from '../campaignLog/cardTypeConfig';

/**
 * Map a beat's primary target type onto an existing knowledge-deck
 * category palette so beat cards share the visual language of the
 * Knowledge Deck. Falls back to `leads` (cyan) for direction targets or
 * empty target lists.
 *
 *   targets[0].type 'npc'      -> npcs       (blue)
 *   targets[0].type 'location' -> locations  (emerald)
 *   targets[0].type 'faction'  -> factions   (purple)
 *   targets[0].type 'direction' / none      -> leads     (cyan)
 */
export function deriveBeatCategory(beat) {
  const first = Array.isArray(beat?.targets) ? beat.targets[0] : null;
  const t = first && typeof first === 'object' ? String(first.type || '').toLowerCase() : '';
  if (t === 'npc') return 'npcs';
  if (t === 'location') return 'locations';
  if (t === 'faction') return 'factions';
  // Action beats with no targets default to leads (cyan)
  return 'leads';
}

export function categoryPaletteFor(beat) {
  const key = deriveBeatCategory(beat);
  return { key, ...CARD_TYPE_CONFIG[key] };
}

/**
 * Rarity tier from DC band. The emblem in the centre of a beat card
 * pulses with the rarity colour — matches MTG / TCG conventions.
 *
 *   no check / DC 0      -> "open"      (slate)
 *   DC 1-12              -> "common"    (white)
 *   DC 13-15             -> "rare"      (blue)
 *   DC 16-19             -> "epic"      (purple)
 *   DC 20+               -> "legendary" (orange)
 */
export function rarityFor(beat) {
  const dc = Number(beat?.dc) || 0;
  const optional = !!beat?.roll_optional;
  if (dc <= 0 || optional) return RARITY.open;
  if (dc <= 12) return RARITY.common;
  if (dc <= 15) return RARITY.rare;
  if (dc <= 19) return RARITY.epic;
  return RARITY.legendary;
}

export const RARITY = {
  open: {
    key: 'open',
    label: 'Open',
    // Subdued slate crystal — there's nothing locked behind this beat.
    crystal: 'from-slate-200 to-slate-400',
    glow: 'shadow-[0_0_18px_rgba(203,213,225,0.45)]',
    ring: 'ring-slate-300/50',
    text: 'text-slate-200',
  },
  common: {
    key: 'common',
    label: 'Common',
    crystal: 'from-white via-stone-100 to-stone-300',
    glow: 'shadow-[0_0_22px_rgba(255,255,255,0.55)]',
    ring: 'ring-stone-200/60',
    text: 'text-stone-100',
  },
  rare: {
    key: 'rare',
    label: 'Rare',
    crystal: 'from-sky-200 via-sky-400 to-blue-600',
    glow: 'shadow-[0_0_28px_rgba(56,189,248,0.65)]',
    ring: 'ring-sky-300/70',
    text: 'text-sky-200',
  },
  epic: {
    key: 'epic',
    label: 'Epic',
    crystal: 'from-fuchsia-300 via-purple-500 to-violet-700',
    glow: 'shadow-[0_0_32px_rgba(168,85,247,0.75)]',
    ring: 'ring-purple-300/70',
    text: 'text-purple-200',
  },
  legendary: {
    key: 'legendary',
    label: 'Legendary',
    crystal: 'from-amber-200 via-orange-400 to-rose-600',
    glow: 'shadow-[0_0_38px_rgba(251,146,60,0.85)]',
    ring: 'ring-orange-300/70',
    text: 'text-orange-200',
  },
};
