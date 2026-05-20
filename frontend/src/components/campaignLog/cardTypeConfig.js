import { 
  MapPin,
  Users,
  Scroll,
  Shield,
  MessageCircle,
  Package,
  GitBranch,
  Compass,
  Sparkles,
  HeartHandshake,
  Skull,
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
  // Magic spells the player learns (Sparkles icon, mystic violet so it sits
  // between the cool/cerebral NPCs and the multicolor factions).
  spells: {
    label: 'Spell',
    icon: Sparkles,
    gradient: 'from-violet-600 to-fuchsia-800',
    border: 'border-violet-500/40',
    glow: 'hover:shadow-violet-500/30',
    badge: 'bg-violet-500/20 text-violet-300 border-violet-400/50',
    headerBg: 'bg-gradient-to-r from-violet-600 to-fuchsia-800',
  },
  // Favors / debts owed to the player by NPCs (HeartHandshake, warm gold).
  favors: {
    label: 'Favor',
    icon: HeartHandshake,
    gradient: 'from-yellow-500 to-amber-700',
    border: 'border-yellow-500/40',
    glow: 'hover:shadow-yellow-500/25',
    badge: 'bg-yellow-500/20 text-yellow-300 border-yellow-400/50',
    headerBg: 'bg-gradient-to-r from-yellow-500 to-amber-700',
  },
  // Curses afflicting the player (Skull, blood-red — visceral warning tone).
  curses: {
    label: 'Curse',
    icon: Skull,
    gradient: 'from-red-700 to-rose-900',
    border: 'border-red-600/50',
    glow: 'hover:shadow-red-700/30',
    badge: 'bg-red-700/30 text-red-300 border-red-500/60',
    headerBg: 'bg-gradient-to-r from-red-700 to-rose-900',
  },
};

/**
 * Normalize any legacy / singular / alternate card-type tag onto the
 * MTG palette keys (plural forms). Backend data currently uses a mix:
 *   - Auto-seeded cards: "location" / "npc" / "faction" / "item"
 *   - Legacy seeds:     "place" / "character" / "guild" / "landmark" / ...
 *   - Palette keys:     "locations" / "npcs" / "factions" / "items" / ...
 *
 * All UI components should route the raw card `type` field through this
 * before indexing into CARD_TYPE_CONFIG.
 */
const TYPE_ALIASES = {
  // Locations
  location: 'locations',
  place: 'locations',
  places: 'locations',
  landmark: 'locations',
  landmarks: 'locations',
  city: 'locations',
  cities: 'locations',
  region: 'locations',
  regions: 'locations',
  area: 'locations',
  dungeon: 'locations',
  dungeons: 'locations',
  // NPCs
  npc: 'npcs',
  character: 'npcs',
  characters: 'npcs',
  person: 'npcs',
  creature: 'npcs',
  // Quests
  quest: 'quests',
  objective: 'quests',
  mission: 'quests',
  // Leads
  lead: 'leads',
  clue: 'leads',
  clues: 'leads',
  // Factions
  faction: 'factions',
  guild: 'factions',
  guilds: 'factions',
  organization: 'factions',
  organizations: 'factions',
  order: 'factions',
  // Rumors
  rumor: 'rumors',
  belief: 'rumors',
  beliefs: 'rumors',
  gossip: 'rumors',
  // Items
  item: 'items',
  artifact: 'items',
  artifacts: 'items',
  equipment: 'items',
  treasure: 'items',
  loot: 'items',
  // Decisions
  decision: 'decisions',
  choice: 'decisions',
  event: 'decisions',
  events: 'decisions',
  // Spells
  spell: 'spells',
  ability: 'spells',
  abilities: 'spells',
  cantrip: 'spells',
  ritual: 'spells',
  prayer: 'spells',
  // Favors
  favor: 'favors',
  boon: 'favors',
  blessing: 'favors',
  pact: 'favors',
  debt: 'favors',
  // Curses
  curse: 'curses',
  cursed: 'curses',
  hex: 'curses',
  affliction: 'curses',
  malediction: 'curses',
};

export const normalizeCardType = (type) => {
  if (!type) return 'locations';
  const lower = String(type).toLowerCase();
  if (CARD_TYPE_CONFIG[lower]) return lower;
  return TYPE_ALIASES[lower] || 'locations';
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

// ── Status display ─────────────────────────────────────────────────
export const STATUS_STYLE = {
  introduced:  'bg-gray-700/80 text-gray-300',
  active:      'bg-amber-700/80 text-amber-200',
  acquired:    'bg-emerald-700/80 text-emerald-200',
  completed:   'bg-blue-700/80 text-blue-200',
  failed:      'bg-red-900/80 text-red-300',
  hostile:     'bg-red-700/80 text-red-100',
  friendly:    'bg-green-700/80 text-green-100',
  dead:        'bg-stone-800/80 text-stone-500',
  cold:        'bg-slate-700/80 text-slate-300',
  sealed:      'bg-indigo-800/80 text-indigo-200',
  open:        'bg-cyan-700/80 text-cyan-200',
  neutral:     'bg-gray-700/80 text-gray-300',
  wary:        'bg-yellow-800/80 text-yellow-200',
  suspicious:  'bg-yellow-800/80 text-yellow-200',
  grateful:    'bg-green-700/80 text-green-100',
  // Item lifecycle
  equipped:    'bg-green-600/80 text-green-100',
  unequipped:  'bg-gray-600/80 text-gray-300',
  consumed:    'bg-stone-800/80 text-stone-400',
  expended:    'bg-stone-800/80 text-stone-400',
};

export const getStatusStyle = (status) =>
  STATUS_STYLE[String(status || 'introduced').toLowerCase()] || STATUS_STYLE.introduced;

// ── Rarity ─────────────────────────────────────────────────────────
export const RARITY_CONFIG = {
  common:    { label: 'Common',    gem: '◆', color: 'text-gray-500'   },
  uncommon:  { label: 'Uncommon',  gem: '◆', color: 'text-green-400'  },
  rare:      { label: 'Rare',      gem: '◆', color: 'text-blue-400'   },
  legendary: { label: 'Legendary', gem: '◆', color: 'text-yellow-400' },
};

export const getRarity = (data, normalizedType) => {
  if (normalizedType === 'curses') return 'legendary';
  if (normalizedType === 'favors') return 'rare';
  if (data?.secret_content && Object.keys(data.secret_content).length > 0) return 'rare';
  // Items with active bonuses are rare; equipped items are at least uncommon
  if (normalizedType === 'items') {
    if ((data?.grants_bonus || []).length > 0) return 'rare';
    if ((data?.status || '').toLowerCase() === 'equipped') return 'uncommon';
  }
  if (data?.source === 'world_event') return 'uncommon';
  if (data?.auto_seeded === false) return 'uncommon';
  return 'common';
};

// ── Per-type mechanical rows shown on card face ─────────────────────
// Returns array of { label, kind } where kind = 'status'|'info'|'warn'|'stat'|'delta'
export const getMechanicalRows = (data, normalizedType) => {
  const rows = [];
  const status = (data?.status || 'introduced').toLowerCase();
  const statusLabel = status.charAt(0).toUpperCase() + status.slice(1);

  switch (normalizedType) {
    case 'npcs': {
      rows.push({ label: statusLabel, kind: 'status' });
      const loc = data?.at_location;
      if (loc) rows.push({ label: `📍 ${loc}`, kind: 'info' });
      const deltas = data?.character_deltas || [];
      const lastAtt = [...deltas].reverse().find(d => d.type === 'attitude');
      if (lastAtt?.fact) rows.push({ label: lastAtt.fact.slice(0, 38), kind: 'delta' });
      const stats = data?.secret_content?.stats;
      if (stats) rows.push({
        label: `P${stats.persuasion_dc || 12} · I${stats.intimidation_dc || 10} · D${stats.deception_dc || 11}`,
        kind: 'stat',
      });
      break;
    }
    case 'locations': {
      rows.push({ label: statusLabel, kind: 'status' });
      if (data?.biome_label) rows.push({ label: data.biome_label, kind: 'info' });
      const survMod = data?.biome_survival_dc_mod;
      if (survMod !== undefined && survMod !== null) rows.push({
        label: `Survival DC ${survMod >= 0 ? '+' : ''}${survMod}`,
        kind: 'info',
      });
      const threats = (data?.biome_monsters || []).slice(0, 2).join(', ');
      if (threats) rows.push({ label: `⚠ ${threats}`, kind: 'warn' });
      break;
    }
    case 'quests': {
      rows.push({ label: statusLabel, kind: 'status' });
      const dcMatch = (data?.content || data?.description || '').match(/DC\s*(\d+)/i);
      if (dcMatch) rows.push({ label: `Check DC: ${dcMatch[1]}`, kind: 'stat' });
      const tags = (data?.tags || []).slice(0, 2);
      if (tags.length) rows.push({ label: tags.join(' · '), kind: 'info' });
      break;
    }
    case 'leads': {
      rows.push({ label: statusLabel, kind: 'status' });
      const src = data?.source_type || data?.source;
      if (src) rows.push({ label: src, kind: 'info' });
      break;
    }
    case 'items': {
      rows.push({ label: statusLabel, kind: 'status' });
      const itemType = data?.item_type;
      const slot = data?.equip_slot;
      const bonuses = data?.grants_bonus || [];
      const qty = data?.quantity;
      // Type + slot line
      if (itemType) {
        const typeStr = slot ? `${itemType} · ${slot}` : itemType;
        rows.push({ label: typeStr.charAt(0).toUpperCase() + typeStr.slice(1), kind: 'info' });
      }
      // Bonus line (equipment) or description (other)
      if (bonuses.length > 0) {
        rows.push({
          label: bonuses.map(b => `+${b.modifier} ${b.check}`).join(' · '),
          kind: 'stat',
        });
      } else if (!itemType) {
        const props = data?.known_properties || data?.content;
        if (props) rows.push({ label: props.slice(0, 40), kind: 'info' });
      }
      // Quantity for stackables
      if (qty && qty > 1) {
        rows.push({ label: `Qty ×${qty}`, kind: 'info' });
      }
      break;
    }
    case 'favors': {
      rows.push({ label: statusLabel, kind: 'status' });
      const txt = data?.content || '';
      if (txt) rows.push({ label: txt.slice(0, 40), kind: 'info' });
      break;
    }
    case 'curses': {
      rows.push({ label: statusLabel, kind: 'status' });
      const tags = (data?.tags || []).slice(0, 2);
      if (tags.length) rows.push({ label: tags.join(' · '), kind: 'warn' });
      const mech = data?.mechanical;
      if (mech) rows.push({ label: mech.slice(0, 40), kind: 'warn' });
      break;
    }
    case 'factions': {
      rows.push({ label: statusLabel, kind: 'status' });
      const rel = data?.relationship_to_party || data?.content;
      if (rel) rows.push({ label: rel.slice(0, 40), kind: 'info' });
      break;
    }
    case 'spells': {
      rows.push({ label: statusLabel, kind: 'status' });
      const tags = (data?.tags || []).slice(0, 2);
      if (tags.length) rows.push({ label: tags.join(' · '), kind: 'info' });
      break;
    }
    default: {
      rows.push({ label: statusLabel, kind: 'status' });
      break;
    }
  }
  return rows;
};
