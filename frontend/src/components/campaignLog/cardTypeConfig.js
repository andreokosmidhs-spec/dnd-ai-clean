import { 
  MapPin,
  Users,
  Scroll,
  Shield,
  MessageCircle,
  Package,
  GitBranch,
  Compass,
} from 'lucide-react';

/**
 * Card type configurations with MTG-inspired color schemes
 */
export const CARD_TYPE_CONFIG = {
  locations: {
    label: 'Place',
    icon: MapPin,
    gradient: 'from-emerald-600 to-emerald-800',
    border: 'border-emerald-500/40',
    glow: 'hover:shadow-emerald-500/20',
    badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-400/50',
    headerBg: 'bg-gradient-to-r from-emerald-600 to-emerald-800',
  },
  npcs: {
    label: 'NPC',
    icon: Users,
    gradient: 'from-blue-600 to-blue-800',
    border: 'border-blue-500/40',
    glow: 'hover:shadow-blue-500/20',
    badge: 'bg-blue-500/20 text-blue-300 border-blue-400/50',
    headerBg: 'bg-gradient-to-r from-blue-600 to-blue-800',
  },
  quests: {
    label: 'Quest',
    icon: Scroll,
    gradient: 'from-amber-500 to-amber-700',
    border: 'border-amber-500/40',
    glow: 'hover:shadow-amber-500/20',
    badge: 'bg-amber-500/20 text-amber-300 border-amber-400/50',
    headerBg: 'bg-gradient-to-r from-amber-500 to-amber-700',
  },
  leads: {
    label: 'Lead',
    icon: Compass,
    gradient: 'from-cyan-600 to-cyan-800',
    border: 'border-cyan-500/40',
    glow: 'hover:shadow-cyan-500/20',
    badge: 'bg-cyan-500/20 text-cyan-300 border-cyan-400/50',
    headerBg: 'bg-gradient-to-r from-cyan-600 to-cyan-800',
  },
  factions: {
    label: 'Faction',
    icon: Shield,
    gradient: 'from-purple-600 to-purple-800',
    border: 'border-purple-500/40',
    glow: 'hover:shadow-purple-500/20',
    badge: 'bg-purple-500/20 text-purple-300 border-purple-400/50',
    headerBg: 'bg-gradient-to-r from-purple-600 to-purple-800',
  },
  rumors: {
    label: 'Rumor',
    icon: MessageCircle,
    gradient: 'from-pink-600 to-pink-800',
    border: 'border-pink-500/40',
    glow: 'hover:shadow-pink-500/20',
    badge: 'bg-pink-500/20 text-pink-300 border-pink-400/50',
    headerBg: 'bg-gradient-to-r from-pink-600 to-pink-800',
  },
  items: {
    label: 'Item',
    icon: Package,
    gradient: 'from-orange-500 to-orange-700',
    border: 'border-orange-500/40',
    glow: 'hover:shadow-orange-500/20',
    badge: 'bg-orange-500/20 text-orange-300 border-orange-400/50',
    headerBg: 'bg-gradient-to-r from-orange-500 to-orange-700',
  },
  decisions: {
    label: 'Decision',
    icon: GitBranch,
    gradient: 'from-indigo-600 to-indigo-800',
    border: 'border-indigo-500/40',
    glow: 'hover:shadow-indigo-500/20',
    badge: 'bg-indigo-500/20 text-indigo-300 border-indigo-400/50',
    headerBg: 'bg-gradient-to-r from-indigo-600 to-indigo-800',
  },
};

/**
 * Helper functions to extract card data
 */
export const getCardTitle = (data, type) => {
  if (type === 'rumors') return data.content?.slice(0, 50) + (data.content?.length > 50 ? '...' : '') || 'Unknown Rumor';
  if (type === 'decisions') return data.description?.slice(0, 50) + (data.description?.length > 50 ? '...' : '') || 'Unknown Decision';
  return data.name || data.title || 'Unknown';
};

export const getCardFullTitle = (data, type) => {
  if (type === 'rumors') return 'Rumor';
  if (type === 'decisions') return 'Decision';
  return data.name || data.title || 'Unknown';
};

export const getCardDescription = (data, type) => {
  switch (type) {
    case 'locations':
      return data.culture_notes || data.climate || data.geography || '';
    case 'npcs':
      return data.personality || data.appearance || '';
    case 'quests':
      return data.description || '';
    case 'leads':
      return data.short_text || '';
    case 'factions':
      return data.stated_purpose || '';
    case 'rumors':
      return data.content || '';
    case 'items':
      return data.known_properties || data.appearance || '';
    case 'decisions':
      return data.immediate_outcome || data.description || '';
    default:
      return '';
  }
};

export const getCardTags = (data, type) => {
  const tags = [];
  switch (type) {
    case 'locations':
      if (data.geography) tags.push(data.geography);
      if (data.climate) tags.push(data.climate);
      break;
    case 'npcs':
      if (data.role) tags.push(data.role);
      if (data.relationship_to_party) tags.push(data.relationship_to_party);
      break;
    case 'quests':
      if (data.status) tags.push(data.status);
      break;
    case 'leads':
      if (data.status) tags.push(data.status);
      if (data.source_type) tags.push(data.source_type);
      break;
    case 'factions':
      if (data.relationship_to_party) tags.push(data.relationship_to_party);
      break;
    case 'rumors':
      if (data.confirmed) tags.push('Confirmed');
      if (data.contradicted) tags.push('Contradicted');
      break;
    case 'items':
      if (data.currently_held) tags.push('In Inventory');
      break;
    default:
      break;
  }
  return tags;
};

export const getCardFullDetails = (data, type) => {
  const details = [];
  
  switch (type) {
    case 'locations':
      if (data.geography) details.push({ label: 'Geography', value: data.geography });
      if (data.climate) details.push({ label: 'Climate', value: data.climate });
      if (data.culture_notes) details.push({ label: 'Culture Notes', value: data.culture_notes });
      if (data.notable_places?.length) details.push({ label: 'Notable Places', value: data.notable_places.join(', ') });
      break;
    case 'npcs':
      if (data.role) details.push({ label: 'Role', value: data.role });
      if (data.appearance) details.push({ label: 'Appearance', value: data.appearance });
      if (data.personality) details.push({ label: 'Personality', value: data.personality });
      if (data.relationship_to_party) details.push({ label: 'Relationship', value: data.relationship_to_party });
      if (data.wants) details.push({ label: 'Wants', value: data.wants });
      if (data.offered) details.push({ label: 'Offered', value: data.offered });
      break;
    case 'quests':
      if (data.description) details.push({ label: 'Description', value: data.description });
      if (data.status) details.push({ label: 'Status', value: data.status });
      if (data.objectives?.length) details.push({ label: 'Objectives', value: data.objectives.join('\n• '), prefix: '• ' });
      if (data.promised_rewards?.length) details.push({ label: 'Rewards', value: data.promised_rewards.join(', ') });
      break;
    case 'leads':
      if (data.short_text) details.push({ label: 'Lead', value: data.short_text });
      if (data.status) details.push({ label: 'Status', value: data.status });
      if (data.source_type) details.push({ label: 'Source', value: data.source_type });
      if (data.player_notes) details.push({ label: 'Notes', value: data.player_notes });
      break;
    case 'factions':
      if (data.stated_purpose) details.push({ label: 'Purpose', value: data.stated_purpose });
      if (data.suspected_purpose) details.push({ label: 'Suspected Purpose', value: data.suspected_purpose });
      if (data.relationship_to_party) details.push({ label: 'Relationship', value: data.relationship_to_party });
      if (data.symbols) details.push({ label: 'Symbols', value: data.symbols });
      break;
    case 'rumors':
      if (data.content) details.push({ label: 'Content', value: data.content });
      details.push({ label: 'Status', value: data.confirmed ? 'Confirmed' : data.contradicted ? 'Contradicted' : 'Unverified' });
      break;
    case 'items':
      if (data.appearance) details.push({ label: 'Appearance', value: data.appearance });
      if (data.known_properties) details.push({ label: 'Properties', value: data.known_properties });
      if (data.suspected_properties) details.push({ label: 'Suspected Properties', value: data.suspected_properties });
      details.push({ label: 'In Inventory', value: data.currently_held ? 'Yes' : 'No' });
      break;
    case 'decisions':
      if (data.description) details.push({ label: 'Decision', value: data.description });
      if (data.immediate_outcome) details.push({ label: 'Outcome', value: data.immediate_outcome });
      if (data.potential_consequences?.length) details.push({ label: 'Consequences', value: data.potential_consequences.join(', ') });
      break;
    default:
      break;
  }
  
  return details;
};
