import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Skeleton } from './ui/skeleton';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from './ui/sheet';
import { 
  X, 
  MapPin,
  Users,
  Scroll,
  Shield,
  MessageCircle,
  Package,
  GitBranch,
  Search,
  Compass,
  Sparkles,
  BookOpen,
  Star,
  Calendar,
  Hash,
  Info
} from 'lucide-react';
import apiClient from '../lib/apiClient';
import { useOpenLeads, useUpdateLeadStatus } from '../hooks/useLeads';

// localStorage key for pinned cards
const PINNED_CARDS_KEY = 'pinned-campaign-cards';

/**
 * Card type configurations with MTG-inspired color schemes
 */
const CARD_TYPE_CONFIG = {
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
const getCardTitle = (data, type) => {
  if (type === 'rumors') return data.content?.slice(0, 50) + (data.content?.length > 50 ? '...' : '') || 'Unknown Rumor';
  if (type === 'decisions') return data.description?.slice(0, 50) + (data.description?.length > 50 ? '...' : '') || 'Unknown Decision';
  return data.name || data.title || 'Unknown';
};

const getCardFullTitle = (data, type) => {
  if (type === 'rumors') return 'Rumor';
  if (type === 'decisions') return 'Decision';
  return data.name || data.title || 'Unknown';
};

const getCardDescription = (data, type) => {
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

const getCardTags = (data, type) => {
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

/**
 * Get all details for drawer display
 */
const getCardFullDetails = (data, type) => {
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

/**
 * Loading Skeleton Card Component
 */
const SkeletonCard = () => (
  <Card className="bg-gray-800/60 border-gray-700/50 overflow-hidden">
    <div className="h-12 bg-gray-700/50">
      <Skeleton className="h-full w-full bg-gray-600/30" />
    </div>
    <CardContent className="p-4 space-y-3">
      <Skeleton className="h-5 w-3/4 bg-gray-600/30" />
      <Skeleton className="h-4 w-full bg-gray-600/30" />
      <Skeleton className="h-4 w-5/6 bg-gray-600/30" />
      <div className="flex gap-2 pt-2">
        <Skeleton className="h-5 w-16 rounded-full bg-gray-600/30" />
        <Skeleton className="h-5 w-20 rounded-full bg-gray-600/30" />
      </div>
    </CardContent>
  </Card>
);

/**
 * Empty State Component
 */
const EmptyState = ({ type }) => {
  const config = CARD_TYPE_CONFIG[type] || CARD_TYPE_CONFIG.locations;
  const Icon = config.icon;
  
  const messages = {
    locations: "No places discovered yet. Explore the world to uncover new locations!",
    npcs: "No characters met yet. Venture forth and make new acquaintances!",
    quests: "No quests yet. Seek adventure and purpose!",
    leads: "No leads yet. Investigate rumors and follow clues!",
    factions: "No factions discovered. Uncover the powers that shape this world!",
    rumors: "No rumors heard. Listen closely in taverns and markets!",
    items: "No significant items found. Search for treasures and artifacts!",
    decisions: "No major decisions recorded yet. Your choices shape destiny!",
    pinned: "No pinned cards yet. Click the star on any card to pin it!",
    all: "Your adventure journal awaits. Begin your journey to fill these pages!",
  };

  return (
    <div className="col-span-full flex flex-col items-center justify-center py-16 px-4">
      <div className={`w-20 h-20 rounded-full bg-gradient-to-br ${config.gradient} flex items-center justify-center mb-6 opacity-50`}>
        <Icon className="w-10 h-10 text-white/80" />
      </div>
      <p className="text-gray-400 text-center text-base max-w-md">
        {messages[type] || messages.all}
      </p>
    </div>
  );
};

/**
 * Knowledge Card Component - MTG-style card design
 */
const KnowledgeCard = ({ data, type, onSelect, isSelected, isPinned }) => {
  const config = CARD_TYPE_CONFIG[type] || CARD_TYPE_CONFIG.locations;
  const Icon = config.icon;
  const title = getCardTitle(data, type);
  const description = getCardDescription(data, type);
  const tags = getCardTags(data, type);

  return (
    <Card 
      className={`bg-gray-900/80 ${config.border} overflow-hidden transition-all duration-300 hover:shadow-lg ${config.glow} hover:-translate-y-1 cursor-pointer group relative ${
        isSelected ? 'ring-2 ring-orange-500 ring-offset-2 ring-offset-gray-950' : ''
      }`}
      onClick={() => onSelect(data, type)}
    >
      {/* Pinned indicator */}
      {isPinned && (
        <div className="absolute top-2 right-2 z-10">
          <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
        </div>
      )}
      
      {/* Color-coded header */}
      <div className={`h-12 bg-gradient-to-r ${config.gradient} flex items-center justify-between px-4`}>
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-white/90" />
          <span className="text-xs font-semibold text-white/90 uppercase tracking-wider">
            {config.label}
          </span>
        </div>
        <Sparkles className="w-4 h-4 text-white/40 group-hover:text-white/70 transition-colors" />
      </div>
      
      {/* Card content */}
      <CardContent className="p-4 space-y-3">
        <h3 className="font-semibold text-white text-base leading-tight line-clamp-2">
          {title}
        </h3>
        
        {description && (
          <p className="text-gray-400 text-sm line-clamp-3 leading-relaxed">
            {description}
          </p>
        )}
        
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {tags.map((tag, idx) => (
              <Badge 
                key={idx} 
                variant="outline" 
                className={`text-xs px-2 py-0.5 ${config.badge}`}
              >
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * Lead Card Component with status actions
 */
const LeadCard = ({ lead, campaignId, characterId, config, onSelect, isSelected, isPinned }) => {
  const updateStatus = useUpdateLeadStatus();
  
  const handleStatusUpdate = (e, newStatus) => {
    e.stopPropagation();
    updateStatus.mutate({
      campaignId,
      leadId: lead.id,
      newStatus,
      characterId
    });
  };

  return (
    <Card 
      className={`bg-gray-900/80 ${config.border} overflow-hidden transition-all duration-300 hover:shadow-lg ${config.glow} hover:-translate-y-1 cursor-pointer relative ${
        isSelected ? 'ring-2 ring-orange-500 ring-offset-2 ring-offset-gray-950' : ''
      }`}
      onClick={() => onSelect(lead, 'leads')}
    >
      {/* Pinned indicator */}
      {isPinned && (
        <div className="absolute top-2 right-2 z-10">
          <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
        </div>
      )}
      
      {/* Color-coded header */}
      <div className={`h-12 bg-gradient-to-r ${config.gradient} flex items-center justify-between px-4`}>
        <div className="flex items-center gap-2">
          <Compass className="w-4 h-4 text-white/90" />
          <span className="text-xs font-semibold text-white/90 uppercase tracking-wider">
            Lead
          </span>
        </div>
        <Badge 
          variant="outline" 
          className={`text-xs ${
            lead.status === 'active' ? 'bg-blue-500/30 text-blue-200 border-blue-400/50' :
            lead.status === 'resolved' ? 'bg-green-500/30 text-green-200 border-green-400/50' :
            lead.status === 'abandoned' ? 'bg-red-500/30 text-red-200 border-red-400/50' :
            'bg-gray-500/30 text-gray-200 border-gray-400/50'
          }`}
        >
          {lead.status}
        </Badge>
      </div>
      
      <CardContent className="p-4 space-y-3">
        <p className="text-white text-sm leading-relaxed line-clamp-3">
          {lead.short_text}
        </p>
        
        {lead.source_type && (
          <Badge variant="outline" className={`text-xs ${config.badge}`}>
            {lead.source_type}
          </Badge>
        )}
        
        {lead.status !== 'resolved' && lead.status !== 'abandoned' && (
          <div className="flex gap-2 pt-2 border-t border-gray-700/50">
            {lead.status === 'unexplored' && (
              <Button
                onClick={(e) => handleStatusUpdate(e, 'active')}
                disabled={updateStatus.isPending}
                size="sm"
                variant="outline"
                className="text-xs h-7 flex-1 border-blue-400/50 text-blue-300 hover:bg-blue-400/10"
              >
                Investigate
              </Button>
            )}
            <Button
              onClick={(e) => handleStatusUpdate(e, 'resolved')}
              disabled={updateStatus.isPending}
              size="sm"
              variant="outline"
              className="text-xs h-7 flex-1 border-green-400/50 text-green-300 hover:bg-green-400/10"
            >
              Resolved
            </Button>
            <Button
              onClick={(e) => handleStatusUpdate(e, 'abandoned')}
              disabled={updateStatus.isPending}
              size="sm"
              variant="outline"
              className="text-xs h-7 border-red-400/50 text-red-300 hover:bg-red-400/10"
            >
              Drop
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * Filter Pill Component
 */
const FilterPill = ({ label, icon: Icon, isActive, onClick, count }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 ${
      isActive 
        ? 'bg-orange-500/30 text-orange-300 border border-orange-400/50 shadow-lg shadow-orange-500/10' 
        : 'bg-gray-800/60 text-gray-400 border border-gray-700/50 hover:bg-gray-700/60 hover:text-gray-300'
    }`}
  >
    {Icon && <Icon className="w-3.5 h-3.5" />}
    <span>{label}</span>
    {count > 0 && (
      <span className={`ml-1 text-xs px-1.5 py-0.5 rounded-full ${
        isActive ? 'bg-orange-500/40' : 'bg-gray-700'
      }`}>
        {count}
      </span>
    )}
  </button>
);

/**
 * Card Details Drawer Component
 */
const CardDetailsDrawer = ({ card, type, isOpen, onClose, isPinned, onTogglePin }) => {
  if (!card || !type) return null;
  
  const config = CARD_TYPE_CONFIG[type] || CARD_TYPE_CONFIG.locations;
  const Icon = config.icon;
  const title = getCardFullTitle(card, type);
  const tags = getCardTags(card, type);
  const details = getCardFullDetails(card, type);
  
  // Format date for display
  const formatDate = (dateStr) => {
    if (!dateStr) return null;
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };
  
  const createdAt = formatDate(card.created_at || card.first_visited || card.first_met || card.decided_when);
  const updatedAt = formatDate(card.updated_at);

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent 
        side="right" 
        className="w-full sm:max-w-[400px] bg-gray-950 border-gray-800 p-0 overflow-hidden"
      >
        {/* Color-coded header */}
        <div className={`${config.headerBg} p-4`}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Icon className="w-5 h-5 text-white/90" />
              <span className="text-sm font-semibold text-white/90 uppercase tracking-wider">
                {config.label}
              </span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onTogglePin(card.id)}
              className={`h-8 w-8 p-0 ${isPinned ? 'text-yellow-400' : 'text-white/60 hover:text-yellow-400'}`}
            >
              <Star className={`w-5 h-5 ${isPinned ? 'fill-yellow-400' : ''}`} />
            </Button>
          </div>
          <SheetHeader className="text-left">
            <SheetTitle className="text-xl font-bold text-white">
              {title}
            </SheetTitle>
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {tags.map((tag, idx) => (
                  <Badge 
                    key={idx} 
                    variant="outline" 
                    className="text-xs px-2 py-0.5 bg-white/10 text-white/90 border-white/30"
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
          </SheetHeader>
        </div>
        
        {/* Scrollable content */}
        <div className="overflow-y-auto h-[calc(100vh-140px)] p-4 space-y-4">
          {/* Full details */}
          {details.map((detail, idx) => (
            <div key={idx} className="space-y-1">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                {detail.label}
              </label>
              <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                {detail.prefix || ''}{detail.value}
              </p>
            </div>
          ))}
          
          {/* Metadata section */}
          <div className="border-t border-gray-800 pt-4 mt-4 space-y-3">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Info className="w-3.5 h-3.5" />
              <span className="uppercase tracking-wider font-medium">Metadata</span>
            </div>
            
            {card.id && (
              <div className="flex items-center gap-2 text-xs">
                <Hash className="w-3 h-3 text-gray-600" />
                <span className="text-gray-600">ID:</span>
                <code className="text-gray-400 font-mono text-xs truncate">{card.id}</code>
              </div>
            )}
            
            {createdAt && (
              <div className="flex items-center gap-2 text-xs">
                <Calendar className="w-3 h-3 text-gray-600" />
                <span className="text-gray-600">Created:</span>
                <span className="text-gray-400">{createdAt}</span>
              </div>
            )}
            
            {updatedAt && (
              <div className="flex items-center gap-2 text-xs">
                <Calendar className="w-3 h-3 text-gray-600" />
                <span className="text-gray-600">Updated:</span>
                <span className="text-gray-400">{updatedAt}</span>
              </div>
            )}
          </div>
        </div>
        
        {/* Hidden description for accessibility */}
        <SheetDescription className="sr-only">
          Details for {config.label}: {title}
        </SheetDescription>
      </SheetContent>
    </Sheet>
  );
};

/**
 * CampaignLogPanel - MTG-style Card Deck UI with Details Drawer
 */
export const CampaignLogPanel = ({ campaignId, characterId, onClose }) => {
  const [allCards, setAllCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');
  const [counts, setCounts] = useState({});
  
  // Selected card for drawer
  const [selectedCard, setSelectedCard] = useState(null);
  const [selectedType, setSelectedType] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  
  // Pinned cards state (from localStorage)
  const [pinnedIds, setPinnedIds] = useState(() => {
    try {
      const stored = localStorage.getItem(PINNED_CARDS_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });
  
  // Leads hook
  const { data: leads, isLoading: leadsLoading } = useOpenLeads(campaignId, characterId);
  
  // Save pinned IDs to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(PINNED_CARDS_KEY, JSON.stringify(pinnedIds));
    } catch (err) {
      console.warn('Failed to save pinned cards:', err);
    }
  }, [pinnedIds]);
  
  const togglePin = useCallback((cardId) => {
    setPinnedIds(prev => {
      if (prev.includes(cardId)) {
        return prev.filter(id => id !== cardId);
      }
      return [...prev, cardId];
    });
  }, []);
  
  const loadAllData = useCallback(async () => {
    if (!campaignId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const params = { campaign_id: campaignId };
      if (characterId) params.character_id = characterId;
      
      const summaryRes = await apiClient.get('/api/campaign/log/summary', { params });
      setCounts(summaryRes?.counts || {});
      
      const categories = ['locations', 'npcs', 'quests', 'factions', 'rumors', 'items', 'decisions'];
      const responses = await Promise.all(
        categories.map(cat => 
          apiClient.get(`/api/campaign/log/${cat}`, { params }).catch(() => ({ [cat]: [] }))
        )
      );
      
      const combined = [];
      categories.forEach((cat, idx) => {
        const items = responses[idx]?.[cat] || [];
        items.forEach(item => {
          combined.push({ ...item, _type: cat });
        });
      });
      
      setAllCards(combined);
    } catch (err) {
      console.error('Failed to load campaign log:', err);
      setError('Failed to load campaign log');
    } finally {
      setLoading(false);
    }
  }, [campaignId, characterId]);
  
  useEffect(() => {
    loadAllData();
  }, [loadAllData]);
  
  // Combine cards with leads
  const allCardsWithLeads = useMemo(() => {
    const leadCards = (leads || []).map(lead => ({ ...lead, _type: 'leads' }));
    return [...allCards, ...leadCards];
  }, [allCards, leads]);
  
  // Filter and search cards
  const filteredCards = useMemo(() => {
    let result = allCardsWithLeads;
    
    // Apply pinned filter
    if (activeFilter === 'pinned') {
      result = result.filter(card => pinnedIds.includes(card.id));
    }
    // Apply type filter
    else if (activeFilter !== 'all') {
      result = result.filter(card => card._type === activeFilter);
    }
    
    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(card => {
        const searchableText = [
          card.name,
          card.title,
          card.content,
          card.description,
          card.short_text,
          card.personality,
          card.role,
          card.stated_purpose,
        ].filter(Boolean).join(' ').toLowerCase();
        
        return searchableText.includes(query);
      });
    }
    
    return result;
  }, [allCardsWithLeads, activeFilter, searchQuery, pinnedIds]);
  
  const handleSelectCard = useCallback((card, type) => {
    setSelectedCard(card);
    setSelectedType(type);
    setDrawerOpen(true);
  }, []);
  
  const handleCloseDrawer = useCallback(() => {
    setDrawerOpen(false);
  }, []);
  
  // Calculate total counts
  const totalCount = Object.values(counts).reduce((a, b) => a + b, 0) + (leads?.length || 0);
  const pinnedCount = pinnedIds.filter(id => allCardsWithLeads.some(c => c.id === id)).length;
  
  // Filter options
  const filterOptions = [
    { key: 'all', label: 'All', icon: Sparkles, count: totalCount },
    { key: 'pinned', label: 'Pinned', icon: Star, count: pinnedCount },
    { key: 'locations', label: 'Places', icon: MapPin, count: counts.locations || 0 },
    { key: 'npcs', label: 'NPCs', icon: Users, count: counts.npcs || 0 },
    { key: 'quests', label: 'Quests', icon: Scroll, count: counts.quests || 0 },
    { key: 'leads', label: 'Leads', icon: Compass, count: leads?.length || 0 },
    { key: 'factions', label: 'Factions', icon: Shield, count: counts.factions || 0 },
    { key: 'rumors', label: 'Rumors', icon: MessageCircle, count: counts.rumors || 0 },
    { key: 'items', label: 'Items', icon: Package, count: counts.items || 0 },
    { key: 'decisions', label: 'Decisions', icon: GitBranch, count: counts.decisions || 0 },
  ];
  
  // Guard against undefined campaignId
  if (!campaignId) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm">
        <Card className="w-full max-w-md mx-4 bg-gray-900 border-red-500/50">
          <CardContent className="p-8 text-center space-y-4">
            <div className="w-16 h-16 mx-auto rounded-full bg-red-500/20 flex items-center justify-center">
              <BookOpen className="w-8 h-8 text-red-400" />
            </div>
            <p className="text-gray-300">
              Cannot load Campaign Log without a valid campaign.
            </p>
            <Button onClick={onClose} variant="outline" className="border-gray-600">
              Close
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  return (
    <div className="fixed inset-0 z-50 bg-black/95 backdrop-blur-md overflow-hidden">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-gray-900/95 border-b border-gray-800 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          {/* Title row */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Knowledge Deck</h1>
                <p className="text-sm text-gray-500">{totalCount} cards collected</p>
              </div>
            </div>
            <Button
              onClick={onClose}
              variant="ghost"
              size="sm"
              className="h-10 w-10 p-0 text-gray-400 hover:text-white hover:bg-gray-800"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
          
          {/* Search and filters */}
          <div className="space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <Input
                type="text"
                placeholder="Search your knowledge..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-gray-800/60 border-gray-700 text-white placeholder:text-gray-500 focus:border-orange-500/50 focus:ring-orange-500/20"
              />
            </div>
            
            <div className="flex flex-wrap gap-2">
              {filterOptions.map(option => (
                <FilterPill
                  key={option.key}
                  label={option.label}
                  icon={option.icon}
                  isActive={activeFilter === option.key}
                  onClick={() => setActiveFilter(option.key)}
                  count={option.count}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
      
      {/* Content */}
      <div className="overflow-y-auto h-[calc(100vh-180px)] px-6 py-6">
        <div className="max-w-7xl mx-auto">
          {loading || leadsLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {[...Array(8)].map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mb-4">
                <X className="w-8 h-8 text-red-400" />
              </div>
              <p className="text-gray-400 text-center">{error}</p>
              <Button onClick={loadAllData} variant="outline" className="mt-4 border-gray-600">
                Try Again
              </Button>
            </div>
          ) : filteredCards.length === 0 ? (
            <EmptyState type={activeFilter} />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredCards.map((card, idx) => (
                card._type === 'leads' ? (
                  <LeadCard 
                    key={card.id || idx}
                    lead={card}
                    campaignId={campaignId}
                    characterId={characterId}
                    config={CARD_TYPE_CONFIG.leads}
                    onSelect={handleSelectCard}
                    isSelected={selectedCard?.id === card.id && drawerOpen}
                    isPinned={pinnedIds.includes(card.id)}
                  />
                ) : (
                  <KnowledgeCard
                    key={card.id || idx}
                    data={card}
                    type={card._type}
                    onSelect={handleSelectCard}
                    isSelected={selectedCard?.id === card.id && drawerOpen}
                    isPinned={pinnedIds.includes(card.id)}
                  />
                )
              ))}
            </div>
          )}
        </div>
      </div>
      
      {/* Card Details Drawer */}
      <CardDetailsDrawer
        card={selectedCard}
        type={selectedType}
        isOpen={drawerOpen}
        onClose={handleCloseDrawer}
        isPinned={selectedCard ? pinnedIds.includes(selectedCard.id) : false}
        onTogglePin={togglePin}
      />
    </div>
  );
};

export default CampaignLogPanel;
