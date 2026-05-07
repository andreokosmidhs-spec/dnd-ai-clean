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
  Search,
  Compass,
  Sparkles,
  BookOpen,
  Star,
} from 'lucide-react';
import apiClient from '../lib/apiClient';
import { useOpenLeads, useUpdateLeadStatus } from '../hooks/useLeads';

// Import extracted components
import { KnowledgeCard } from './campaignLog/KnowledgeCard';
import { CardDetailsDrawer } from './campaignLog/CardDetailsDrawer';
import { usePinnedCards } from './campaignLog/usePinnedCards';
import { CARD_TYPE_CONFIG, normalizeCardType } from './campaignLog/cardTypeConfig';

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
  const config = CARD_TYPE_CONFIG[normalizeCardType(type)] || CARD_TYPE_CONFIG.locations;
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
 * CampaignLogPanel - MTG-style Card Deck UI with Details Drawer
 * Orchestrator component that manages state and renders child components
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
  
  // Use extracted pinned cards hook
  const { pinnedIds, togglePin, isPinned } = usePinnedCards();
  
  // Leads hook
  const { data: leads, isLoading: leadsLoading } = useOpenLeads(campaignId, characterId);
  
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

      // ALSO pull the flat `campaign_cards` collection (auto-seeded cards
      // from DM narration + manually-pinned "Remember this" cards). These
      // include the new `spell` / `favor` / `curse` types that the
      // structured /api/campaign/log/* endpoints don't expose.
      try {
        const cardsRes = await apiClient.get(`/api/campaigns/${campaignId}/log/cards`);
        const flatCards = Array.isArray(cardsRes) ? cardsRes : (cardsRes?.cards || []);
        flatCards.forEach((card) => {
          const normalized = normalizeCardType(card.type);
          // De-dupe vs. the structured-log results on (title, type) so we
          // don't double-list cards that exist in both systems.
          const dupe = combined.find(
            (c) =>
              (c.name || c.title) === (card.title || card.name) &&
              c._type === normalized
          );
          if (dupe) return;
          combined.push({ ...card, _type: normalized });
        });
      } catch (err) {
        console.warn('Failed to fetch campaign_cards (flat):', err);
      }

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

  // Live refresh when the storyline auto-mints new cards (NPCs / locations /
  // factions revealed by passing a knowledge beat).
  useEffect(() => {
    const handler = (e) => {
      if (!campaignId) return;
      if (e?.detail?.campaignId && e.detail.campaignId !== campaignId) return;
      loadAllData();
    };
    window.addEventListener('rpg:cards-refreshed', handler);
    return () => window.removeEventListener('rpg:cards-refreshed', handler);
  }, [campaignId, loadAllData]);
  
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
  const totalCount = allCardsWithLeads.length;
  const pinnedCount = pinnedIds.filter(id => allCardsWithLeads.some(c => c.id === id)).length;

  // Live counts per normalized type so the new auto-seeded categories
  // (spells / favors / curses) get accurate badge numbers without
  // needing a backend summary endpoint update.
  const liveCounts = {};
  allCardsWithLeads.forEach((c) => {
    const t = c._type || normalizeCardType(c.type);
    liveCounts[t] = (liveCounts[t] || 0) + 1;
  });

  // Filter options — include the 3 new MTG-palette types (spells/favors/
  // curses) when at least one card of that kind exists, so the filter row
  // doesn't bloat for campaigns that haven't accumulated them yet.
  const filterOptions = [
    { key: 'all', label: 'All', icon: Sparkles, count: totalCount },
    { key: 'pinned', label: 'Pinned', icon: Star, count: pinnedCount },
    { key: 'locations', label: 'Places', icon: MapPin, count: liveCounts.locations || 0 },
    { key: 'npcs', label: 'NPCs', icon: Users, count: liveCounts.npcs || 0 },
    { key: 'quests', label: 'Quests', icon: Scroll, count: liveCounts.quests || 0 },
    { key: 'leads', label: 'Leads', icon: Compass, count: leads?.length || 0 },
    { key: 'factions', label: 'Factions', icon: Shield, count: liveCounts.factions || 0 },
    { key: 'rumors', label: 'Rumors', icon: MessageCircle, count: liveCounts.rumors || 0 },
    { key: 'items', label: 'Items', icon: Package, count: liveCounts.items || 0 },
    { key: 'decisions', label: 'Decisions', icon: GitBranch, count: liveCounts.decisions || 0 },
    ...(liveCounts.spells ? [{
      key: 'spells', label: 'Spells',
      icon: CARD_TYPE_CONFIG.spells.icon, count: liveCounts.spells,
    }] : []),
    ...(liveCounts.favors ? [{
      key: 'favors', label: 'Favors',
      icon: CARD_TYPE_CONFIG.favors.icon, count: liveCounts.favors,
    }] : []),
    ...(liveCounts.curses ? [{
      key: 'curses', label: 'Curses',
      icon: CARD_TYPE_CONFIG.curses.icon, count: liveCounts.curses,
    }] : []),
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
      <div className="overflow-y-auto h-[calc(100vh-180px)] px-6 py-6 pb-24">
        <div className="max-w-[1600px] mx-auto">
          {loading || leadsLoading ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7 gap-3">
              {[...Array(14)].map((_, i) => (
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
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7 gap-3" data-testid="deck-library-grid">
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
                    isPinned={isPinned(card.id)}
                  />
                ) : (
                  <KnowledgeCard
                    key={card.id || idx}
                    data={card}
                    type={card._type}
                    onSelect={handleSelectCard}
                    isSelected={selectedCard?.id === card.id && drawerOpen}
                    isPinned={isPinned(card.id)}
                    campaignId={campaignId}
                  />
                )
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Return-to-Game button — fixed to the bottom-right of the deck library
          so it's always reachable without scrolling. Mirrors the "minimize"
          gesture the player intuited from the screenshot. */}
      <Button
        onClick={onClose}
        className="fixed bottom-6 right-6 z-50 bg-amber-600 hover:bg-amber-500 text-stone-950 font-bold border-2 border-amber-300 shadow-[0_0_24px_rgba(245,158,11,0.45)] h-12 px-5"
        data-testid="deck-library-return-btn"
      >
        ← Return to Game
      </Button>
      
      {/* Card Details Drawer */}
      <CardDetailsDrawer
        card={selectedCard}
        type={selectedType}
        isOpen={drawerOpen}
        onClose={handleCloseDrawer}
        isPinned={selectedCard ? isPinned(selectedCard.id) : false}
        onTogglePin={togglePin}
        campaignId={campaignId}
        onCardUpdated={(updated) => {
          // Refresh just the selected card; the deck list re-fetches on close.
          setSelectedCard(updated);
        }}
      />
    </div>
  );
};

export default CampaignLogPanel;
