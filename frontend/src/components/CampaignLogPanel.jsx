import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
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
  Calendar,
  Compass,
  CheckCircle,
  XCircle,
  Play,
  Eye
} from 'lucide-react';
import apiClient from '../lib/apiClient';
import { useOpenLeads, useUpdateLeadStatus } from '../hooks/useLeads';
import { QuestDetailModal } from './QuestDetailModal';

/**
 * CampaignLogPanel - Full-page tabbed view of all campaign knowledge
 * Replaces the simple entity profile system with structured categories
 */
export const CampaignLogPanel = ({ campaignId, characterId, onClose }) => {
  const [summary, setSummary] = useState(null);
  const [activeTab, setActiveTab] = useState('locations');
  const [categoryData, setCategoryData] = useState({});
  const [loading, setLoading] = useState(true);
  const [categoryLoading, setCategoryLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Quest Detail Modal State
  const [selectedQuest, setSelectedQuest] = useState(null);
  const [selectedQuestLead, setSelectedQuestLead] = useState(null);
  const [showQuestModal, setShowQuestModal] = useState(false);
  const [fullLog, setFullLog] = useState(null); // For entity resolution in modal
  
  // Move useOpenLeads hook to top level to avoid conditional hook usage
  const { data: leads, isLoading: leadsLoading, error: leadsError } = useOpenLeads(campaignId, characterId);
  
  useEffect(() => {
    if (campaignId) {
      loadSummary();
    }
  }, [campaignId]);
  
  useEffect(() => {
    if (activeTab && campaignId) {
      loadCategoryData(activeTab);
    }
  }, [activeTab, campaignId]);
  
  // CRITICAL FIX: Guard against undefined campaignId
  if (!campaignId) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
        <Card className="w-full max-w-4xl mx-4 bg-gradient-to-br from-gray-900 to-gray-800 border-2 border-red-500/50">
          <CardContent className="p-8 text-center space-y-4">
            <div className="text-red-400 text-lg font-semibold">
              ⚠️ Campaign ID Missing
            </div>
            <p className="text-gray-300">
              Cannot load Campaign Log without a valid campaign ID.
            </p>
            <p className="text-sm text-gray-400">
              Please start or load a campaign first.
            </p>
            <Button onClick={onClose} variant="outline" className="mt-4">
              Close
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  const loadSummary = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = { campaign_id: campaignId };
      if (characterId) params.character_id = characterId;
      
      const response = await apiClient.get('/api/campaign/log/summary', { params });
      setSummary(response.data);
    } catch (err) {
      console.error('❌ Failed to load campaign log summary:', err);
      setError('Failed to load campaign log');
    } finally {
      setLoading(false);
    }
  };
  
  const loadCategoryData = async (category) => {
    if (categoryData[category]) {
      return; // Already loaded
    }
    
    setCategoryLoading(true);
    
    try {
      const params = { campaign_id: campaignId };
      if (characterId) params.character_id = characterId;
      
      const response = await apiClient.get(`/api/campaign/log/${category}`, { params });
      setCategoryData(prev => ({
        ...prev,
        [category]: response.data[category] || []
      }));
    } catch (err) {
      console.error(`❌ Failed to load ${category}:`, err);
    } finally {
      setCategoryLoading(false);
    }
  };
  
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };
  
  // Handle opening quest detail modal
  const handleViewQuestDetails = async (quest) => {
    setSelectedQuest(quest);
    
    // Fetch full log for entity resolution if not already loaded
    if (!fullLog) {
      try {
        const params = { campaign_id: campaignId };
        if (characterId) params.character_id = characterId;
        
        const response = await apiClient.get('/api/campaign/log/full', { params });
        setFullLog(response.data);
      } catch (err) {
        console.error('❌ Failed to load full campaign log:', err);
      }
    }
    
    // Fetch lead details if quest has source_lead_id
    if (quest.source_lead_id) {
      try {
        const params = { campaign_id: campaignId };
        if (characterId) params.character_id = characterId;
        
        const response = await apiClient.get(`/api/campaign/log/leads/${quest.source_lead_id}`, { params });
        setSelectedQuestLead(response.data);
      } catch (err) {
        console.error('❌ Failed to load quest lead:', err);
        setSelectedQuestLead(null);
      }
    } else {
      setSelectedQuestLead(null);
    }
    
    setShowQuestModal(true);
  };
  
  // Handle closing quest detail modal
  const handleCloseQuestModal = () => {
    setShowQuestModal(false);
    setSelectedQuest(null);
    setSelectedQuestLead(null);
  };
  
  const renderLocations = () => {
    const locations = categoryData?.locations || [];
    
    if (categoryLoading) {
      return <div className="flex justify-center p-8"><Loader2 className="h-6 w-6 animate-spin text-orange-400" /></div>;
    }
    
    if (locations.length === 0) {
      return <p className="text-gray-400 text-center p-8">No locations discovered yet. Explore the world!</p>;
    }
    
    return (
      <div className="grid gap-4">
        {locations.map((loc) => (
          <Card key={loc.id} className="bg-gray-800/50 border-orange-600/30">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-orange-400 text-lg">{loc.name}</CardTitle>
                  {loc.geography && (
                    <p className="text-sm text-gray-400 mt-1">{loc.geography}</p>
                  )}
                </div>
                <MapPin className="h-5 w-5 text-orange-400" />
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {loc.climate && (
                <div>
                  <span className="text-xs font-semibold text-gray-400">Climate:</span>
                  <p className="text-sm text-gray-300">{loc.climate}</p>
                </div>
              )}
              
              {loc.notable_places && loc.notable_places.length > 0 && (
                <div>
                  <span className="text-xs font-semibold text-gray-400">Notable Places:</span>
                  <ul className="list-disc list-inside mt-1 space-y-1">
                    {loc.notable_places.map((place, idx) => (
                      <li key={idx} className="text-sm text-gray-300">{place}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {loc.architecture && (
                <div>
                  <span className="text-xs font-semibold text-gray-400">Architecture:</span>
                  <p className="text-sm text-gray-300">{loc.architecture}</p>
                </div>
              )}
              
              {loc.culture_notes && (
                <div>
                  <span className="text-xs font-semibold text-gray-400">Culture:</span>
                  <p className="text-sm text-gray-300">{loc.culture_notes}</p>
                </div>
              )}
              
              <div className="flex items-center gap-2 text-xs text-gray-500 pt-2 border-t border-gray-700">
                <Calendar className="h-3 w-3" />
                First visited: {formatDate(loc.first_visited)}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };
  
  const renderNpcs = () => {
    const npcs = categoryData?.npcs || [];
    
    if (categoryLoading) {
      return <div className="flex justify-center p-8"><Loader2 className="h-6 w-6 animate-spin text-orange-400" /></div>;
    }
    
    if (npcs.length === 0) {
      return <p className="text-gray-400 text-center p-8">No NPCs met yet. Start your adventure!</p>;
    }
    
    return (
      <div className="grid gap-4">
        {npcs.map((npc) => (
          <Card key={npc.id} className="bg-gray-800/50 border-orange-600/30">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-orange-400 text-lg">{npc.name}</CardTitle>
                  {npc.role && (
                    <Badge variant="outline" className="mt-2 text-xs border-orange-400/50 text-orange-300">
                      {npc.role}
                    </Badge>
                  )}
                </div>
                <Users className="h-5 w-5 text-orange-400" />
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {npc.appearance && (
                <div>
                  <span className="text-xs font-semibold text-gray-400">Appearance:</span>
                  <p className="text-sm text-gray-300">{npc.appearance}</p>
                </div>
              )}
              
              {npc.personality && (
                <div>
                  <span className="text-xs font-semibold text-gray-400">Personality:</span>
                  <p className="text-sm text-gray-300">{npc.personality}</p>
                </div>
              )}
              
              {npc.wants && (
                <div>
                  <span className="text-xs font-semibold text-gray-400">Wants:</span>
                  <p className="text-sm text-gray-300">{npc.wants}</p>
                </div>
              )}
              
              {npc.offered && (
                <div>
                  <span className="text-xs font-semibold text-gray-400">Offered:</span>
                  <p className="text-sm text-gray-300">{npc.offered}</p>
                </div>
              )}
              
              {npc.relationship_to_party && (
                <div>
                  <Badge 
                    variant="outline"
                    className={
                      npc.relationship_to_party === 'friendly' || npc.relationship_to_party === 'ally' ? 'border-green-400 text-green-300' :
                      npc.relationship_to_party === 'hostile' ? 'border-red-400 text-red-300' :
                      'border-gray-400 text-gray-300'
                    }
                  >
                    {npc.relationship_to_party}
                  </Badge>
                </div>
              )}
              
              <div className="flex items-center gap-2 text-xs text-gray-500 pt-2 border-t border-gray-700">
                <Calendar className="h-3 w-3" />
                First met: {formatDate(npc.first_met)}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };
  
  const renderQuests = () => {
    const quests = categoryData?.quests || [];
    
    if (categoryLoading) {
      return <div className="flex justify-center p-8"><Loader2 className="h-6 w-6 animate-spin text-orange-400" /></div>;
    }
    
    if (quests.length === 0) {
      return <p className="text-gray-400 text-center p-8">No quests yet. Seek adventure!</p>;
    }
    
    return (
      <div className="grid gap-4">
        {quests.map((quest) => (
          <Card key={quest.id} className="bg-gray-800/50 border-orange-600/30">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-orange-400 text-lg">{quest.title}</CardTitle>
                  <Badge 
                    variant="outline" 
                    className={
                      quest.status === 'completed' ? 'mt-2 border-green-400 text-green-300' :
                      quest.status === 'failed' ? 'mt-2 border-red-400 text-red-300' :
                      'mt-2 border-orange-400/50 text-orange-300'
                    }
                  >
                    {quest.status}
                  </Badge>
                </div>
                <Scroll className="h-5 w-5 text-orange-400" />
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {quest.description && (
                <p className="text-sm text-gray-300 line-clamp-2">{quest.description}</p>
              )}
              
              {quest.objectives && quest.objectives.length > 0 && (
                <div>
                  <span className="text-xs font-semibold text-gray-400">Objectives:</span>
                  <ul className="list-disc list-inside mt-1 space-y-1">
                    {quest.objectives.slice(0, 3).map((obj, idx) => (
                      <li key={idx} className="text-sm text-gray-300">{obj}</li>
                    ))}
                    {quest.objectives.length > 3 && (
                      <li className="text-sm text-gray-400 italic">+{quest.objectives.length - 3} more...</li>
                    )}
                  </ul>
                </div>
              )}
              
              {quest.promised_rewards && quest.promised_rewards.length > 0 && (
                <div>
                  <span className="text-xs font-semibold text-gray-400">Rewards:</span>
                  <ul className="list-disc list-inside mt-1 space-y-1">
                    {quest.promised_rewards.slice(0, 2).map((reward, idx) => (
                      <li key={idx} className="text-sm text-green-300">{reward}</li>
                    ))}
                    {quest.promised_rewards.length > 2 && (
                      <li className="text-sm text-gray-400 italic">+{quest.promised_rewards.length - 2} more...</li>
                    )}
                  </ul>
                </div>
              )}
              
              {/* View Details Button */}
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => handleViewQuestDetails(quest)}
                className="w-full mt-2 border-orange-600/50 text-orange-400 hover:bg-orange-950/30 hover:border-orange-500"
              >
                <Eye className="h-4 w-4 mr-2" />
                View Details
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };
  
  const renderFactions = () => {
    const factions = categoryData?.factions || [];
    
    if (categoryLoading) {
      return <div className="flex justify-center p-8"><Loader2 className="h-6 w-6 animate-spin text-orange-400" /></div>;
    }
    
    if (factions.length === 0) {
      return <p className="text-gray-400 text-center p-8">No factions discovered yet.</p>;
    }
    
    return (
      <div className="grid gap-4">
        {factions.map((faction) => (
          <Card key={faction.id} className="bg-gray-800/50 border-orange-600/30">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-orange-400 text-lg">{faction.name}</CardTitle>
                  {faction.symbols && (
                    <p className="text-xs text-gray-400 mt-1">Symbol: {faction.symbols}</p>
                  )}
                </div>
                <Shield className="h-5 w-5 text-orange-400" />
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {faction.stated_purpose && (
                <div>
                  <span className="text-xs font-semibold text-gray-400">Stated Purpose:</span>
                  <p className="text-sm text-gray-300">{faction.stated_purpose}</p>
                </div>
              )}
              
              {faction.suspected_purpose && (
                <div>
                  <span className="text-xs font-semibold text-yellow-400">Suspected Purpose:</span>
                  <p className="text-sm text-yellow-200">{faction.suspected_purpose}</p>
                </div>
              )}
              
              {faction.relationship_to_party && (
                <div>
                  <Badge 
                    variant="outline"
                    className={
                      faction.relationship_to_party === 'ally' ? 'border-green-400 text-green-300' :
                      faction.relationship_to_party === 'hostile' ? 'border-red-400 text-red-300' :
                      'border-gray-400 text-gray-300'
                    }
                  >
                    {faction.relationship_to_party}
                  </Badge>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };
  
  const renderRumors = () => {
    const rumors = categoryData?.rumors || [];
    
    if (categoryLoading) {
      return <div className="flex justify-center p-8"><Loader2 className="h-6 w-6 animate-spin text-orange-400" /></div>;
    }
    
    if (rumors.length === 0) {
      return <p className="text-gray-400 text-center p-8">No rumors heard yet.</p>;
    }
    
    return (
      <div className="grid gap-3">
        {rumors.map((rumor) => (
          <Card key={rumor.id} className="bg-gray-800/50 border-purple-600/30">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <MessageCircle className="h-5 w-5 text-purple-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-gray-300">{rumor.content}</p>
                  {rumor.confirmed && (
                    <Badge variant="outline" className="mt-2 border-green-400 text-green-300 text-xs">
                      Confirmed
                    </Badge>
                  )}
                  {rumor.contradicted && (
                    <Badge variant="outline" className="mt-2 border-red-400 text-red-300 text-xs">
                      Contradicted
                    </Badge>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };
  
  const renderItems = () => {
    const items = categoryData?.items || [];
    
    if (categoryLoading) {
      return <div className="flex justify-center p-8"><Loader2 className="h-6 w-6 animate-spin text-orange-400" /></div>;
    }
    
    if (items.length === 0) {
      return <p className="text-gray-400 text-center p-8">No significant items discovered yet.</p>;
    }
    
    return (
      <div className="grid gap-4">
        {items.map((item) => (
          <Card key={item.id} className="bg-gray-800/50 border-orange-600/30">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-orange-400 text-lg">{item.name}</CardTitle>
                  {item.currently_held && (
                    <Badge variant="outline" className="mt-2 text-xs border-green-400/50 text-green-300">
                      In Inventory
                    </Badge>
                  )}
                </div>
                <Package className="h-5 w-5 text-orange-400" />
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {item.appearance && (
                <div>
                  <span className="text-xs font-semibold text-gray-400">Appearance:</span>
                  <p className="text-sm text-gray-300">{item.appearance}</p>
                </div>
              )}
              
              {item.known_properties && (
                <div>
                  <span className="text-xs font-semibold text-gray-400">Properties:</span>
                  <p className="text-sm text-gray-300">{item.known_properties}</p>
                </div>
              )}
              
              {item.suspected_properties && (
                <div>
                  <span className="text-xs font-semibold text-yellow-400">Suspected:</span>
                  <p className="text-sm text-yellow-200">{item.suspected_properties}</p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };
  
  const renderDecisions = () => {
    const decisions = categoryData?.decisions || [];
    
    if (categoryLoading) {
      return <div className="flex justify-center p-8"><Loader2 className="h-6 w-6 animate-spin text-orange-400" /></div>;
    }
    
    if (decisions.length === 0) {
      return <p className="text-gray-400 text-center p-8">No major decisions recorded yet.</p>;
    }
    
    return (
      <div className="grid gap-4">
        {decisions.map((decision) => (
          <Card key={decision.id} className="bg-gray-800/50 border-blue-600/30">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <GitBranch className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1 space-y-2">
                  <p className="text-sm text-gray-300 font-medium">{decision.description}</p>
                  
                  {decision.immediate_outcome && (
                    <div>
                      <span className="text-xs font-semibold text-gray-400">Result:</span>
                      <p className="text-sm text-gray-300">{decision.immediate_outcome}</p>
                    </div>
                  )}
                  
                  {decision.potential_consequences && decision.potential_consequences.length > 0 && (
                    <div>
                      <span className="text-xs font-semibold text-yellow-400">Potential Consequences:</span>
                      <ul className="list-disc list-inside mt-1 space-y-1">
                        {decision.potential_consequences.map((consequence, idx) => (
                          <li key={idx} className="text-sm text-yellow-200">{consequence}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  <div className="text-xs text-gray-500 pt-2 border-t border-gray-700">
                    {formatDate(decision.decided_when)}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };
  
  const LeadCard = ({ lead }) => {
    const updateStatus = useUpdateLeadStatus();
    
    const handleStatusUpdate = (newStatus) => {
      updateStatus.mutate({
        campaignId,
        leadId: lead.id,
        newStatus,
        characterId
      });
    };
    
    const getStatusBadgeClass = (status) => {
      switch (status) {
        case 'unexplored':
          return 'border-gray-400 text-gray-300';
        case 'active':
          return 'border-blue-400 text-blue-300';
        case 'resolved':
          return 'border-green-400 text-green-300';
        case 'abandoned':
          return 'border-red-400/50 text-red-300';
        default:
          return 'border-gray-400 text-gray-300';
      }
    };
    
    const getSourceTypeIcon = (sourceType) => {
      switch (sourceType) {
        case 'environmental':
          return '🌿';
        case 'conversation':
          return '💬';
        case 'observation':
          return '👁️';
        case 'rumor':
          return '🗣️';
        default:
          return '📍';
      }
    };
    
    return (
      <Card className="bg-gray-800/50 border-cyan-600/30">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Compass className="h-5 w-5 text-cyan-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1 space-y-3">
              {/* Lead text */}
              <div>
                <p className="text-sm text-gray-300 font-medium">{lead.short_text}</p>
              </div>
              
              {/* Metadata */}
              <div className="flex flex-wrap gap-2 items-center">
                <Badge variant="outline" className={`text-xs ${getStatusBadgeClass(lead.status)}`}>
                  {lead.status}
                </Badge>
                
                {lead.source_type && (
                  <span className="text-xs text-gray-500">
                    {getSourceTypeIcon(lead.source_type)} {lead.source_type}
                  </span>
                )}
                
                {lead.location_id && (
                  <span className="text-xs text-gray-500">
                    <MapPin className="h-3 w-3 inline mr-1" />
                    {lead.location_id.replace('location_', '')}
                  </span>
                )}
              </div>
              
              {/* Player notes */}
              {lead.player_notes && (
                <div className="text-xs text-gray-400 italic bg-gray-900/30 p-2 rounded">
                  📝 {lead.player_notes}
                </div>
              )}
              
              {/* Action buttons */}
              {lead.status !== 'resolved' && lead.status !== 'abandoned' && (
                <div className="flex gap-2 pt-2 border-t border-gray-700">
                  {lead.status === 'unexplored' && (
                    <Button
                      onClick={() => handleStatusUpdate('active')}
                      disabled={updateStatus.isPending}
                      size="sm"
                      variant="outline"
                      className="text-xs h-7 border-blue-400/50 text-blue-300 hover:bg-blue-400/10"
                    >
                      <Play className="h-3 w-3 mr-1" />
                      Mark Active
                    </Button>
                  )}
                  
                  <Button
                    onClick={() => handleStatusUpdate('resolved')}
                    disabled={updateStatus.isPending}
                    size="sm"
                    variant="outline"
                    className="text-xs h-7 border-green-400/50 text-green-300 hover:bg-green-400/10"
                  >
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Mark Resolved
                  </Button>
                  
                  <Button
                    onClick={() => handleStatusUpdate('abandoned')}
                    disabled={updateStatus.isPending}
                    size="sm"
                    variant="outline"
                    className="text-xs h-7 border-red-400/50 text-red-300 hover:bg-red-400/10"
                  >
                    <XCircle className="h-3 w-3 mr-1" />
                    Abandon
                  </Button>
                </div>
              )}
              
              {/* Timestamp */}
              <div className="text-xs text-gray-500">
                <Calendar className="h-3 w-3 inline mr-1" />
                Discovered: {formatDate(lead.created_at)}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };
  
  const renderLeads = () => {
    if (leadsLoading) {
      return <div className="flex justify-center p-8"><Loader2 className="h-6 w-6 animate-spin text-orange-400" /></div>;
    }
    
    if (leadsError) {
      return <p className="text-red-400 text-center p-8">Failed to load leads: {leadsError.message}</p>;
    }
    
    if (!leads || leads.length === 0) {
      return (
        <div className="text-center p-8 space-y-2">
          <Compass className="h-12 w-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">No leads yet.</p>
          <p className="text-sm text-gray-500">Explore the world to discover rumors and hooks!</p>
        </div>
      );
    }
    
    return (
      <div className="grid gap-3">
        {leads.map((lead) => (
          <LeadCard key={lead.id} lead={lead} />
        ))}
      </div>
    );
  };
  
  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-orange-400" />
      </div>
    );
  }
  
  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-4xl h-[90vh] bg-gray-900/95 border-orange-600/30 flex flex-col">
        <CardHeader className="border-b border-orange-600/20 flex-shrink-0">
          <div className="flex items-center justify-between">
            <CardTitle className="text-orange-400 text-2xl">Campaign Log</CardTitle>
            <Button
              onClick={onClose}
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 text-orange-400 hover:text-orange-200 hover:bg-orange-600/20"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
          {summary && (
            <div className="flex gap-4 mt-4 text-sm text-gray-400">
              <span>Locations: {summary.counts.locations}</span>
              <span>NPCs: {summary.counts.npcs}</span>
              <span>Quests: {summary.counts.quests}</span>
              <span>Leads: {summary.counts.leads || 0}</span>
              <span>Factions: {summary.counts.factions}</span>
            </div>
          )}
        </CardHeader>
        
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
          <TabsList className="grid w-full grid-cols-8 bg-gray-800/50 flex-shrink-0">
            <TabsTrigger value="locations" className="text-xs">
              <MapPin className="h-4 w-4" />
            </TabsTrigger>
            <TabsTrigger value="npcs" className="text-xs">
              <Users className="h-4 w-4" />
            </TabsTrigger>
            <TabsTrigger value="quests" className="text-xs">
              <Scroll className="h-4 w-4" />
            </TabsTrigger>
            <TabsTrigger value="leads" className="text-xs">
              <Compass className="h-4 w-4" />
            </TabsTrigger>
            <TabsTrigger value="factions" className="text-xs">
              <Shield className="h-4 w-4" />
            </TabsTrigger>
            <TabsTrigger value="rumors" className="text-xs">
              <MessageCircle className="h-4 w-4" />
            </TabsTrigger>
            <TabsTrigger value="items" className="text-xs">
              <Package className="h-4 w-4" />
            </TabsTrigger>
            <TabsTrigger value="decisions" className="text-xs">
              <GitBranch className="h-4 w-4" />
            </TabsTrigger>
          </TabsList>
          
          <div className="flex-1 overflow-hidden">
            <ScrollArea className="h-full">
              <div className="p-6">
                <TabsContent value="locations" className="mt-0">{renderLocations()}</TabsContent>
                <TabsContent value="npcs" className="mt-0">{renderNpcs()}</TabsContent>
                <TabsContent value="quests" className="mt-0">{renderQuests()}</TabsContent>
                <TabsContent value="leads" className="mt-0">{renderLeads()}</TabsContent>
                <TabsContent value="factions" className="mt-0">{renderFactions()}</TabsContent>
                <TabsContent value="rumors" className="mt-0">{renderRumors()}</TabsContent>
                <TabsContent value="items" className="mt-0">{renderItems()}</TabsContent>
                <TabsContent value="decisions" className="mt-0">{renderDecisions()}</TabsContent>
              </div>
            </ScrollArea>
          </div>
        </Tabs>
      </Card>
      
      {/* Quest Detail Modal */}
      {showQuestModal && selectedQuest && (
        <QuestDetailModal 
          quest={selectedQuest}
          lead={selectedQuestLead}
          onClose={handleCloseQuestModal}
          campaignLog={fullLog}
        />
      )}
    </div>
  );
};

export default CampaignLogPanel;
