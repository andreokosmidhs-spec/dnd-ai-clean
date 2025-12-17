import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Skeleton } from './ui/skeleton';
import { 
  X, 
  MapPin,
  Users,
  Scroll,
  Shield,
  MessageCircle,
  Package,
  GitBranch,
  Loader2,
  Search,
  Compass,
  Sparkles,
  BookOpen
} from 'lucide-react';
import apiClient from '../lib/apiClient';
import { useOpenLeads, useUpdateLeadStatus } from '../hooks/useLeads';
import { QuestDetailModal } from './QuestDetailModal';

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
  },
  npcs: {
    label: 'NPC',
    icon: Users,
    gradient: 'from-blue-600 to-blue-800',
    border: 'border-blue-500/40',
    glow: 'hover:shadow-blue-500/20',
    badge: 'bg-blue-500/20 text-blue-300 border-blue-400/50',
  },
  quests: {
    label: 'Quest',
    icon: Scroll,
    gradient: 'from-amber-500 to-amber-700',
    border: 'border-amber-500/40',
    glow: 'hover:shadow-amber-500/20',
    badge: 'bg-amber-500/20 text-amber-300 border-amber-400/50',
  },
  leads: {
    label: 'Lead',
    icon: Compass,
    gradient: 'from-cyan-600 to-cyan-800',
    border: 'border-cyan-500/40',
    glow: 'hover:shadow-cyan-500/20',
    badge: 'bg-cyan-500/20 text-cyan-300 border-cyan-400/50',
  },
  factions: {
    label: 'Faction',
    icon: Shield,
    gradient: 'from-purple-600 to-purple-800',
    border: 'border-purple-500/40',
    glow: 'hover:shadow-purple-500/20',
    badge: 'bg-purple-500/20 text-purple-300 border-purple-400/50',
  },
  rumors: {
    label: 'Rumor',
    icon: MessageCircle,
    gradient: 'from-pink-600 to-pink-800',
    border: 'border-pink-500/40',
    glow: 'hover:shadow-pink-500/20',
    badge: 'bg-pink-500/20 text-pink-300 border-pink-400/50',
  },
  items: {
    label: 'Item',
    icon: Package,
    gradient: 'from-orange-500 to-orange-700',
    border: 'border-orange-500/40',
    glow: 'hover:shadow-orange-500/20',
    badge: 'bg-orange-500/20 text-orange-300 border-orange-400/50',
  },
  decisions: {
    label: 'Decision',
    icon: GitBranch,
    gradient: 'from-indigo-600 to-indigo-800',
    border: 'border-indigo-500/40',
    glow: 'hover:shadow-indigo-500/20',
    badge: 'bg-indigo-500/20 text-indigo-300 border-indigo-400/50',
  },
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
const KnowledgeCard = ({ data, type, onViewDetails }) => {
  const config = CARD_TYPE_CONFIG[type] || CARD_TYPE_CONFIG.locations;
  const Icon = config.icon;
  
  // Get title based on card type
  const getTitle = () => {
    if (type === 'rumors') return data.content?.slice(0, 50) + '...' || 'Unknown Rumor';
    if (type === 'decisions') return data.description?.slice(0, 50) + '...' || 'Unknown Decision';
    return data.name || data.title || 'Unknown';
  };
  
  // Get description based on card type
  const getDescription = () => {
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
  
  // Get tags/badges based on card type
  const getTags = () => {
    const tags = [];
    
    switch (type) {
      case 'locations':
        if (data.geography) tags.push(data.geography);
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
      case 'decisions':
        break;
      default:
        break;
    }
    
    return tags;
  };

  const title = getTitle();
  const description = getDescription();
  const tags = getTags();

  return (
    <Card 
      className={`bg-gray-900/80 ${config.border} overflow-hidden transition-all duration-300 hover:shadow-lg ${config.glow} hover:-translate-y-1 cursor-pointer group`}
      onClick={() => onViewDetails && onViewDetails(data, type)}
    >
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
        {/* Title */}
        <h3 className="font-semibold text-white text-base leading-tight line-clamp-2">
          {title}
        </h3>
        
        {/* Description */}
        {description && (
          <p className="text-gray-400 text-sm line-clamp-3 leading-relaxed">
            {description}
          </p>
        )}
        
        {/* Tags */}
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
const LeadCard = ({ lead, campaignId, characterId, config }) => {
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
      className={`bg-gray-900/80 ${config.border} overflow-hidden transition-all duration-300 hover:shadow-lg ${config.glow} hover:-translate-y-1`}
    >
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
      
      {/* Card content */}
      <CardContent className="p-4 space-y-3">
        <p className="text-white text-sm leading-relaxed">
          {lead.short_text}
        </p>
        
        {lead.source_type && (
          <Badge variant="outline" className={`text-xs ${config.badge}`}>
            {lead.source_type}
          </Badge>
        )}
        
        {lead.player_notes && (
          <p className="text-xs text-gray-500 italic bg-gray-800/50 p-2 rounded">
            {lead.player_notes}
          </p>
        )}
        
        {/* Action buttons */}
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
 * CampaignLogPanel - MTG-style Card Deck UI
 */
export const CampaignLogPanel = ({ campaignId, characterId, onClose }) => {
  const [allCards, setAllCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');
  const [counts, setCounts] = useState({});
  
  // Quest Detail Modal State
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedItemType, setSelectedItemType] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  
  // Move useOpenLeads hook to top level
  const { data: leads, isLoading: leadsLoading } = useOpenLeads(campaignId, characterId);
  
  const loadAllData = useCallback(async () => {
    if (!campaignId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const params = { campaign_id: campaignId };
      if (characterId) params.character_id = characterId;
      
      // Load summary for counts
      // Note: apiClient returns response.data directly, not wrapped
      const summaryRes = await apiClient.get('/api/campaign/log/summary', { params });
      setCounts(summaryRes?.counts || {});
      
      // Load all categories in parallel
      const categories = ['locations', 'npcs', 'quests', 'factions', 'rumors', 'items', 'decisions'];
      const responses = await Promise.all(
        categories.map(cat => 
          apiClient.get(`/api/campaign/log/${cat}`, { params }).catch(() => ({ [cat]: [] }))
        )
      );
      
      // Combine all cards with their types
      // Note: apiClient returns response.data directly
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
    
    // Apply type filter
    if (activeFilter !== 'all') {
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
  }, [allCardsWithLeads, activeFilter, searchQuery]);
  
  const handleViewDetails = (item, type) => {
    setSelectedItem(item);
    setSelectedItemType(type);
    if (type === 'quests') {
      setShowDetailModal(true);
    }
  };
  
  const handleCloseDetailModal = () => {
    setShowDetailModal(false);
    setSelectedItem(null);
    setSelectedItemType(null);
  };
  
  // Calculate total counts
  const totalCount = Object.values(counts).reduce((a, b) => a + b, 0) + (leads?.length || 0);
  
  // Filter options
  const filterOptions = [
    { key: 'all', label: 'All', icon: Sparkles, count: totalCount },
    { key: 'locations', label: 'Places', icon: MapPin, count: counts.locations || 0 },
    { key: 'npcs', label: 'NPCs', icon: Users, count: counts.npcs || 0 },
    { key: 'quests', label: 'Quests', icon: Scroll, count: counts.quests || 0 },
    { key: 'leads', label: 'Leads', icon: Compass, count: leads?.length || 0 },
    { key: 'factions', label: 'Factions', icon: Shield, count: counts.factions || 0 },
    { key: 'rumors', label: 'Rumors', icon: MessageCircle, count: counts.rumors || 0 },
    { key: 'items', label: 'Items', icon: Package, count: counts.items || 0 },
    { key: 'decisions', label: 'Decisions', icon: GitBranch, count: counts.decisions || 0 },
  ];
  
  // Guard against undefined campaignId - placed after all hooks
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
            {/* Search input */}
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
            
            {/* Filter pills */}
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
            // Loading skeletons
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {[...Array(8)].map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : error ? (
            // Error state
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
            // Empty state
            <EmptyState type={activeFilter} />
          ) : (
            // Card grid
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredCards.map((card, idx) => (
                card._type === 'leads' ? (
                  <LeadCard 
                    key={card.id || idx}
                    lead={card}
                    campaignId={campaignId}
                    characterId={characterId}
                    config={CARD_TYPE_CONFIG.leads}
                  />
                ) : (
                  <KnowledgeCard
                    key={card.id || idx}
                    data={card}
                    type={card._type}
                    onViewDetails={handleViewDetails}
                  />
                )
              ))}
            </div>
          )}
        </div>
      </div>
      
      {/* Quest Detail Modal */}
      {showDetailModal && selectedItem && selectedItemType === 'quests' && (
        <QuestDetailModal 
          quest={selectedItem}
          onClose={handleCloseDetailModal}
        />
      )}
    </div>
  );
};

export default CampaignLogPanel;
