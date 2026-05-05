/**
 * Event card type metadata — color + border styling for the 8 event types.
 * Mirrors `/app/backend/data/event_catalog.py:EVENT_TYPES`.
 *
 * Each entry returns Tailwind-compatible classes for:
 *   border    — left rule (4-5px) that distinguishes the card at a glance
 *   ring      — subtle outline / glow color
 *   chipText  — type-badge text color
 *   chipBg    — type-badge background
 *   accent    — title accent color
 *
 * `borderClass` chooses the actual Tailwind border style (solid/dashed/double/dotted).
 * Combined with the color it yields the unique look per type.
 */

export const EVENT_TYPE_META = {
  encounter: {
    label: 'Encounter',
    icon: '⚔️',
    borderClass: 'border-l-[5px] border-l-red-500',
    ringClass: 'ring-1 ring-red-900/40',
    chipText: 'text-red-50',
    chipBg: 'bg-red-700/80',
    accent: 'text-red-200',
  },
  faction: {
    label: 'Faction Plot',
    icon: '🏛️',
    borderClass: 'border-l-[4px] border-l-purple-500 border-dashed',
    ringClass: 'ring-1 ring-purple-900/40',
    chipText: 'text-purple-50',
    chipBg: 'bg-purple-700/80',
    accent: 'text-purple-200',
  },
  cultural: {
    label: 'Cultural',
    icon: '🪶',
    borderClass: 'border-l-[6px] border-l-emerald-500 border-double',
    ringClass: 'ring-1 ring-emerald-900/40',
    chipText: 'text-emerald-50',
    chipBg: 'bg-emerald-700/80',
    accent: 'text-emerald-200',
  },
  discovery: {
    label: 'Discovery',
    icon: '🌟',
    borderClass: 'border-l-[5px] border-l-amber-400',
    ringClass: 'ring-1 ring-amber-500/30 shadow-[0_0_12px_rgba(251,191,36,0.18)]',
    chipText: 'text-amber-50',
    chipBg: 'bg-amber-600/90',
    accent: 'text-amber-200',
  },
  mystery: {
    label: 'Mystery',
    icon: '🔍',
    borderClass: 'border-l-[5px] border-l-indigo-500 border-dotted',
    ringClass: 'ring-1 ring-indigo-900/40',
    chipText: 'text-indigo-50',
    chipBg: 'bg-indigo-700/80',
    accent: 'text-indigo-200',
  },
  hazard: {
    label: 'Travel Hazard',
    icon: '🏔️',
    borderClass: 'border-l-[5px] border-l-slate-400 border-dashed',
    ringClass: 'ring-1 ring-slate-700/40',
    chipText: 'text-slate-50',
    chipBg: 'bg-slate-700/85',
    accent: 'text-slate-200',
  },
  lore: {
    label: 'Lore',
    icon: '📜',
    borderClass: 'border-l-[3px] border-l-sky-400',
    ringClass: 'ring-1 ring-sky-900/40',
    chipText: 'text-sky-50',
    chipBg: 'bg-sky-700/80',
    accent: 'text-sky-200',
  },
  quest: {
    label: 'Quest Hook',
    icon: '🎯',
    borderClass: 'border-l-[6px] border-l-rose-500',
    ringClass: 'ring-1 ring-rose-900/45 shadow-[0_0_10px_rgba(244,63,94,0.18)]',
    chipText: 'text-rose-50',
    chipBg: 'bg-rose-700/85',
    accent: 'text-rose-200',
  },
};

export function eventTypeMeta(type) {
  return EVENT_TYPE_META[type] || EVENT_TYPE_META.mystery;
}
