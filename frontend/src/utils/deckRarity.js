/**
 * Deck card rarity styling — color + border per tier.
 * Mirrors the 4 rarity values used by the backend deck system.
 */

export const RARITY_META = {
  common: {
    label: 'Common',
    chipBg: 'bg-stone-700/70',
    chipText: 'text-stone-100',
    borderClass: 'border-stone-500/50',
    accentText: 'text-stone-200',
    glow: '',
  },
  rare: {
    label: 'Rare',
    chipBg: 'bg-sky-700/85',
    chipText: 'text-sky-50',
    borderClass: 'border-sky-400/70',
    accentText: 'text-sky-200',
    glow: 'shadow-[0_0_8px_rgba(56,189,248,0.18)]',
  },
  epic: {
    label: 'Epic',
    chipBg: 'bg-fuchsia-700/85',
    chipText: 'text-fuchsia-50',
    borderClass: 'border-fuchsia-400/70',
    accentText: 'text-fuchsia-200',
    glow: 'shadow-[0_0_12px_rgba(217,70,239,0.25)]',
  },
  legendary: {
    label: 'Legendary',
    chipBg: 'bg-amber-500/90',
    chipText: 'text-amber-950',
    borderClass: 'border-amber-300',
    accentText: 'text-amber-300',
    glow: 'shadow-[0_0_18px_rgba(251,191,36,0.4)]',
  },
};

export function rarityMeta(r) {
  return RARITY_META[r] || RARITY_META.common;
}

export const SOURCE_META = {
  race:       { label: 'Race',       icon: '🪶', color: 'text-emerald-300' },
  language:   { label: 'Languages',  icon: '🗣️', color: 'text-cyan-300' },
  background: { label: 'Background', icon: '📜', color: 'text-amber-300' },
  class:      { label: 'Class',      icon: '⚔️', color: 'text-rose-300' },
  spell:      { label: 'Spells',     icon: '✨', color: 'text-violet-300' },
  item:       { label: 'Items',      icon: '🎒', color: 'text-yellow-300' },
  contact:    { label: 'Contacts',   icon: '🤝', color: 'text-blue-300' },
  quest:      { label: 'Rewards',    icon: '🏆', color: 'text-amber-200' },
  reputation: { label: 'Reputation', icon: '⚜️', color: 'text-indigo-300' },
  curse:      { label: 'Curses',     icon: '☠️', color: 'text-red-400' },
};

export function sourceMeta(src) {
  return SOURCE_META[src] || { label: src, icon: '◆', color: 'text-stone-300' };
}

// Display order for sources in the deck modal.
export const SOURCE_ORDER = [
  'race', 'language', 'background', 'class',
  'spell', 'item', 'contact', 'quest', 'reputation', 'curse',
];
