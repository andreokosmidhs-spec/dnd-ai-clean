import React from 'react';

/**
 * EntityLink - Clickable entity name in narration.
 *
 * Carries `data-entity-type` so the parchment theme can recolor by type:
 *   npc      → blue (Island/Mind, MTG)
 *   location → emerald (Forest/Land)
 *   faction  → purple (Multicolor Guild)
 *   item     → orange (Artifact)
 *
 * The base utility classes still use `text-orange-400` so that the
 * non-parchment dark theme keeps its existing look. Parchment overrides
 * happen via `data-entity-type` selectors in `adventurePapyrus.css`.
 */
export const EntityLink = ({
  entityType,
  entityId,
  name,
  onClick,
  children
}) => {
  return (
    <span
      data-entity-type={entityType || 'other'}
      className="
        text-orange-400
        border-b-2 border-orange-400/50
        cursor-pointer inline-block mx-0.5 px-1.5 py-0.5 rounded
        transition-all duration-200
        hover:bg-orange-600/20
        hover:border-orange-400
        hover:shadow-sm hover:shadow-orange-400/30
        hover:text-orange-300
      "
      onClick={() => onClick({ type: entityType, id: entityId, name })}
      title={`View ${entityType}: ${name}`}
    >
      {children || name}
    </span>
  );
};

/**
 * HookSpan - Italic dashed underline rendering for a "point of interest"
 * planted by the DM in narration. Hovering shows the suggested verb;
 * clicking the wrapping container surfaces the hook in a larger UI
 * (the parent wires `onHookClick` for that).
 */
export const HookSpan = ({ hook, onClick, children }) => (
  <span
    data-hook-id={hook.id}
    data-hook-verb={hook.verb_hint || 'examine'}
    className="
      italic text-amber-200/90
      border-b border-dashed border-amber-300/60
      cursor-help inline-block mx-0.5 px-0.5
      transition-all duration-200
      hover:bg-amber-500/10
      hover:border-amber-200
      hover:text-amber-100
    "
    title={`Hook · ${hook.verb_hint || 'examine'}: ${hook.topic || hook.text}`}
    onClick={onClick ? () => onClick(hook) : undefined}
  >
    {children}
  </span>
);

/**
 * EntityNarrationParser - Renders narration with clickable entity links
 * Uses entity_mentions array from backend (start/end positions).
 * Optionally also overlays HOOK spans (italic dashed underline) for
 * DM-planted points of interest.
 */
export const EntityNarrationParser = ({
  text,
  entityMentions = [],
  hooks = [],
  onEntityClick,
  onHookClick,
}) => {
  // Merge entity mentions + hooks into a single sorted span list. When two
  // ranges overlap, ENTITY wins (the proper-noun link is more useful than
  // the hook hint).
  const ents = (entityMentions || []).map((m) => ({ ...m, _kind: 'entity' }));
  const hks = (hooks || []).map((h) => ({
    ...h, _kind: 'hook',
    start: h.start,
    end: h.end,
  }));

  const all = [...ents, ...hks].filter((s) => Number.isInteger(s.start) && Number.isInteger(s.end) && s.end > s.start);
  // Drop hooks that overlap any entity range
  const filtered = all.filter((s) => {
    if (s._kind !== 'hook') return true;
    return !ents.some((e) => !(s.end <= e.start || s.start >= e.end));
  });
  const sorted = filtered.sort((a, b) => a.start - b.start);

  if (sorted.length === 0) return <span>{text}</span>;

  const parts = [];
  let cursor = 0;
  sorted.forEach((sp, idx) => {
    if (sp.start > cursor) {
      parts.push({ type: 'text', content: text.substring(cursor, sp.start), key: `t-${idx}-pre` });
    }
    if (sp._kind === 'entity') {
      parts.push({
        type: 'entity',
        entityType: sp.entity_type,
        entityId: sp.entity_id,
        displayText: sp.display_text || text.substring(sp.start, sp.end),
        key: `e-${idx}`,
      });
    } else {
      parts.push({
        type: 'hook',
        hook: sp,
        displayText: text.substring(sp.start, sp.end),
        key: `h-${idx}`,
      });
    }
    cursor = sp.end;
  });
  if (cursor < text.length) {
    parts.push({ type: 'text', content: text.substring(cursor), key: 't-final' });
  }

  return (
    <span>
      {parts.map((part) => {
        if (part.type === 'entity') {
          return (
            <EntityLink
              key={part.key}
              entityType={part.entityType}
              entityId={part.entityId}
              name={part.displayText}
              onClick={onEntityClick}
            >
              {part.displayText}
            </EntityLink>
          );
        }
        if (part.type === 'hook') {
          return (
            <HookSpan key={part.key} hook={part.hook} onClick={onHookClick}>
              {part.displayText}
            </HookSpan>
          );
        }
        return <span key={part.key}>{part.content}</span>;
      })}
    </span>
  );
};

export default EntityLink;
