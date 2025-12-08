import React from 'react';
import { Badge } from './ui/badge';

/**
 * Highlights NPC names in narration text and makes them clickable
 * Parses [[npc_name]] tags from DM narration
 * @param {string} text - The narration text with [[npc_name]] tags
 * @param {Array} npcMentions - Array of {id, name, role} objects (for metadata)
 * @param {Function} onNPCClick - Callback when NPC is clicked
 * @param {string} selectedNpcId - Currently selected NPC ID
 */
const NPCMentionHighlighter = ({ text, npcMentions = [], onNPCClick, selectedNpcId }) => {
  // Parse [[npc_name]] tags from text
  const pattern = /\[\[([^\]]+)\]\]/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  // Create a map of NPC names to their metadata for quick lookup
  const npcMap = {};
  npcMentions.forEach(npc => {
    npcMap[npc.name.toLowerCase()] = npc;
  });

  while ((match = pattern.exec(text)) !== null) {
    // Add text before the match
    if (match.index > lastIndex) {
      parts.push({
        type: 'text',
        content: text.substring(lastIndex, match.index),
        key: `text-${lastIndex}`
      });
    }

    // Extract NPC name from [[npc_name]]
    const npcName = match[1];
    
    // Find metadata for this NPC (if available)
    const npcData = npcMap[npcName.toLowerCase()] || {
      id: `npc_${npcName.toLowerCase().replace(/\s+/g, '_')}`,
      name: npcName,
      role: 'secondary' // Default to secondary if no metadata
    };

    parts.push({
      type: 'npc',
      content: npcName, // Display name without brackets
      npcData: npcData,
      key: `npc-${match.index}`
    });

    lastIndex = pattern.lastIndex;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push({
      type: 'text',
      content: text.substring(lastIndex),
      key: `text-${lastIndex}`
    });
  }

  // If no NPC tags found, return plain text
  if (parts.length === 0) {
    return <span>{text}</span>;
  }

  return (
    <span>
      {parts.map((part) => {
        if (part.type === 'npc') {
          const isSelected = part.npcData.id === selectedNpcId;
          const isPrimary = part.npcData.role === 'primary';

          return (
            <Badge
              key={part.key}
              variant="outline"
              className={`cursor-pointer inline-flex mx-0.5 ${
                isSelected
                  ? 'bg-blue-600/30 border-blue-400 text-blue-200'
                  : isPrimary
                  ? 'border-purple-400/50 text-purple-300 hover:bg-purple-600/20'
                  : 'border-gray-400/50 text-gray-300 hover:bg-gray-600/20'
              }`}
              onClick={() => onNPCClick(part.npcData)}
              title={`Talk to ${part.npcData.name}`}
            >
              {part.content}
            </Badge>
          );
        }
        return <span key={part.key}>{part.content}</span>;
      })}
    </span>
  );
};

export default NPCMentionHighlighter;
