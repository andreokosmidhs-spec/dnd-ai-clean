import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { 
  X, 
  Scroll, 
  Target, 
  Award, 
  MapPin, 
  Users, 
  Shield,
  Lightbulb,
  CheckCircle,
  Circle
} from 'lucide-react';

/**
 * QuestDetailModal - Full-screen overlay modal displaying detailed quest information
 * 
 * @param {Object} props
 * @param {Object} props.quest - QuestKnowledge object with all quest details
 * @param {Object} props.lead - Optional LeadEntry object if quest originated from a lead
 * @param {Function} props.onClose - Callback to close the modal
 * @param {Object} props.campaignLog - Optional full campaign log for entity resolution
 */
export const QuestDetailModal = ({ quest, lead, onClose, campaignLog }) => {
  if (!quest) return null;

  // Helper to get entity name from ID
  const getEntityName = (entityMap, entityId) => {
    if (!entityMap || !entityId) return entityId || 'Unknown';
    const entity = entityMap[entityId];
    return entity?.name || entityId;
  };

  // Resolve related entity names
  const locations = quest.related_location_ids?.map(id => 
    getEntityName(campaignLog?.locations, id)
  ) || [];
  
  const npcs = quest.related_npc_ids?.map(id => 
    getEntityName(campaignLog?.npcs, id)
  ) || [];
  
  const factions = quest.related_faction_ids?.map(id => 
    getEntityName(campaignLog?.factions, id)
  ) || [];

  // Status color mapping
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'border-green-400 text-green-300 bg-green-950/30';
      case 'failed':
        return 'border-red-400 text-red-300 bg-red-950/30';
      case 'active':
        return 'border-orange-400 text-orange-300 bg-orange-950/30';
      case 'rumored':
        return 'border-purple-400 text-purple-300 bg-purple-950/30';
      default:
        return 'border-gray-400 text-gray-300 bg-gray-950/30';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <Card className="w-full max-w-3xl max-h-[90vh] mx-4 bg-gradient-to-br from-gray-900 to-gray-800 border-2 border-orange-600/50 shadow-2xl">
        {/* Header */}
        <CardHeader className="border-b border-orange-600/30 pb-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <Scroll className="h-6 w-6 text-orange-400" />
                <CardTitle className="text-2xl text-orange-400">{quest.title}</CardTitle>
              </div>
              <Badge 
                variant="outline" 
                className={`${getStatusColor(quest.status)} px-3 py-1`}
              >
                {quest.status.charAt(0).toUpperCase() + quest.status.slice(1)}
              </Badge>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="text-gray-400 hover:text-white hover:bg-gray-700/50"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
        </CardHeader>

        {/* Scrollable Content */}
        <ScrollArea className="max-h-[calc(90vh-200px)]">
          <CardContent className="pt-6 space-y-6">
            {/* Description */}
            {quest.description && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-wide">
                  Quest Description
                </h3>
                <p className="text-base text-gray-200 leading-relaxed">
                  {quest.description}
                </p>
              </div>
            )}

            {/* Motivation */}
            {quest.motivation && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-wide">
                  Why This Matters
                </h3>
                <p className="text-sm text-gray-300 italic">
                  {quest.motivation}
                </p>
              </div>
            )}

            {/* Objectives */}
            {quest.objectives && quest.objectives.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Target className="h-4 w-4 text-orange-400" />
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
                    Objectives
                  </h3>
                </div>
                <ul className="space-y-2">
                  {quest.objectives.map((objective, idx) => {
                    const isCompleted = quest.completed_objectives?.includes(objective);
                    return (
                      <li key={idx} className="flex items-start gap-3 text-sm">
                        {isCompleted ? (
                          <CheckCircle className="h-5 w-5 text-green-400 mt-0.5 flex-shrink-0" />
                        ) : (
                          <Circle className="h-5 w-5 text-gray-500 mt-0.5 flex-shrink-0" />
                        )}
                        <span className={isCompleted ? 'text-gray-400 line-through' : 'text-gray-200'}>
                          {objective}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {/* Rewards */}
            {quest.promised_rewards && quest.promised_rewards.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Award className="h-4 w-4 text-yellow-400" />
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
                    Promised Rewards
                  </h3>
                </div>
                <ul className="list-disc list-inside space-y-1">
                  {quest.promised_rewards.map((reward, idx) => (
                    <li key={idx} className="text-sm text-green-300">
                      {reward}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Origin Information */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Lightbulb className="h-4 w-4 text-blue-400" />
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
                  Origin
                </h3>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                {quest.source_lead_id && lead ? (
                  <div className="space-y-2">
                    <p className="text-sm text-gray-300">
                      <span className="text-blue-400 font-medium">Lead: </span>
                      {lead.short_text}
                    </p>
                    <div className="flex items-center gap-2">
                      <Badge 
                        variant="outline" 
                        className={`text-xs ${getStatusColor(lead.status)}`}
                      >
                        {lead.status}
                      </Badge>
                      {lead.source_type && (
                        <span className="text-xs text-gray-400">
                          via {lead.source_type}
                        </span>
                      )}
                    </div>
                  </div>
                ) : quest.source_lead_id ? (
                  <p className="text-sm text-gray-400">
                    Originated from Lead: <span className="text-blue-400">{quest.source_lead_id}</span>
                  </p>
                ) : quest.quest_giver_npc_id ? (
                  <p className="text-sm text-gray-300">
                    Quest Giver: <span className="text-purple-400">{getEntityName(campaignLog?.npcs, quest.quest_giver_npc_id)}</span>
                  </p>
                ) : (
                  <p className="text-sm text-gray-400 italic">
                    Direct quest (no specific lead or quest giver)
                  </p>
                )}
              </div>
            </div>

            {/* Related Entities */}
            {(locations.length > 0 || npcs.length > 0 || factions.length > 0) && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wide">
                  Related To
                </h3>
                <div className="space-y-3">
                  {/* Locations */}
                  {locations.length > 0 && (
                    <div className="flex items-start gap-2">
                      <MapPin className="h-4 w-4 text-green-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <span className="text-xs text-gray-400 block mb-1">Locations</span>
                        <div className="flex flex-wrap gap-2">
                          {locations.map((location, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs border-green-400/50 text-green-300">
                              {location}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* NPCs */}
                  {npcs.length > 0 && (
                    <div className="flex items-start gap-2">
                      <Users className="h-4 w-4 text-purple-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <span className="text-xs text-gray-400 block mb-1">NPCs</span>
                        <div className="flex flex-wrap gap-2">
                          {npcs.map((npc, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs border-purple-400/50 text-purple-300">
                              {npc}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Factions */}
                  {factions.length > 0 && (
                    <div className="flex items-start gap-2">
                      <Shield className="h-4 w-4 text-red-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <span className="text-xs text-gray-400 block mb-1">Factions</span>
                        <div className="flex flex-wrap gap-2">
                          {factions.map((faction, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs border-red-400/50 text-red-300">
                              {faction}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Timestamps */}
            <div className="text-xs text-gray-500 pt-4 border-t border-gray-700/50">
              <p>Discovered: {new Date(quest.discovered).toLocaleDateString()}</p>
              {quest.last_updated && (
                <p>Last Updated: {new Date(quest.last_updated).toLocaleDateString()}</p>
              )}
            </div>
          </CardContent>
        </ScrollArea>

        {/* Footer */}
        <div className="border-t border-orange-600/30 p-4">
          <Button 
            onClick={onClose}
            className="w-full bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700"
          >
            Close
          </Button>
        </div>
      </Card>
    </div>
  );
};
