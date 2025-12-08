import React from 'react';

/**
 * EntityLink - Clickable entity name in narration
 * All entities use ORANGE color as per user requirement
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
 * EntityNarrationParser - Renders narration with clickable entity links
 * Uses entity_mentions array from backend (start/end positions)
 */
export const EntityNarrationParser = ({ 
  text, 
  entityMentions = [], 
  onEntityClick 
}) => {
  // If no mentions, return plain text
  if (!entityMentions || entityMentions.length === 0) {
    return <span>{text}</span>;
  }
  
  const parts = [];
  let cursor = 0;
  
  // Sort mentions by start position (should already be sorted, but just in case)
  const sortedMentions = [...entityMentions].sort((a, b) => a.start - b.start);
  
  sortedMentions.forEach((mention, idx) => {
    // Add text before this mention
    if (mention.start > cursor) {
      parts.push({
        type: 'text',
        content: text.substring(cursor, mention.start),
        key: `text-${idx}-before`
      });
    }
    
    // Add the entity link
    parts.push({
      type: 'entity',
      entityType: mention.entity_type,
      entityId: mention.entity_id,
      displayText: mention.display_text,
      key: `entity-${idx}`
    });
    
    cursor = mention.end;
  });
  
  // Add remaining text after last mention
  if (cursor < text.length) {
    parts.push({
      type: 'text',
      content: text.substring(cursor),
      key: `text-final`
    });
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
        return <span key={part.key}>{part.content}</span>;
      })}
    </span>
  );
};

export default EntityLink;
