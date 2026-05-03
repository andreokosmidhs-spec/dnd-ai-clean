import React, { useState } from 'react';
import { Scroll, ChevronDown, ChevronRight, ChevronUp, Check, X, Circle } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

const QuestLogPanel = ({ quests = [], onUpdateStatus, embedded = false }) => {
  const [expandedQuests, setExpandedQuests] = useState({});
  const [showCompleted, setShowCompleted] = useState(false);
  // Whole panel collapses to a single header bar so the narration can sit
  // at the top of the screen. Defaults to collapsed (matches WorldInfoPanel).
  // When embedded inside a Sheet, the header chrome is owned by the caller and
  // the body is always visible.
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  const toggleQuest = (questId) => {
    setExpandedQuests(prev => ({
      ...prev,
      [questId]: !prev[questId]
    }));
  };

  const activeQuests = quests.filter(q => q.status === 'active');
  const completedQuests = quests.filter(q => q.status === 'completed');
  const failedQuests = quests.filter(q => q.status === 'failed');

  const getObjectiveIcon = (objective) => {
    const isComplete = objective.progress >= (objective.count || 1);
    if (isComplete) {
      return <Check className="h-3 w-3 text-green-400" />;
    }
    return <Circle className="h-3 w-3 text-gray-400" />;
  };

  const getObjectiveProgress = (objective) => {
    if (objective.type === 'kill' || (objective.count && objective.count > 1)) {
      return `${objective.progress}/${objective.count || 1}`;
    }
    return objective.progress >= (objective.count || 1) ? 'Complete' : 'Incomplete';
  };

  const getObjectiveDescription = (objective) => {
    const descriptions = {
      'kill': `Defeat ${objective.target}`,
      'go_to': `Travel to ${objective.target}`,
      'interact': `Talk to ${objective.target}`,
      'discover': `Discover ${objective.target}`
    };
    return descriptions[objective.type] || objective.target;
  };

  const QuestCard = ({ quest }) => {
    const isExpanded = expandedQuests[quest.quest_id];
    const objectives = Array.isArray(quest.objectives) ? quest.objectives : [];
    return (
      <div className="bg-gray-800/50 border border-amber-600/30 rounded-lg p-3 mb-2">
        {/* Quest Header */}
        <div 
          className="flex items-start justify-between cursor-pointer"
          onClick={() => toggleQuest(quest.quest_id)}
        >
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              {isExpanded ? (
                <ChevronDown className="h-4 w-4 text-amber-400" />
              ) : (
                <ChevronRight className="h-4 w-4 text-amber-400" />
              )}
              <h4 className="text-amber-300 font-semibold text-sm">
                {quest.name}
              </h4>
              {quest.status === 'completed' && (
                <Badge variant="outline" className="text-xs border-green-400/50 text-green-300">
                  <Check className="h-3 w-3 mr-1" />
                  Complete
                </Badge>
              )}
              {quest.status === 'failed' && (
                <Badge variant="outline" className="text-xs border-red-400/50 text-red-300">
                  <X className="h-3 w-3 mr-1" />
                  Failed
                </Badge>
              )}
            </div>
            <p className="text-gray-300 text-xs ml-6">{quest.summary}</p>
          </div>
          {quest.rewards_xp > 0 && (
            <Badge variant="outline" className="text-xs border-purple-400/50 text-purple-300 ml-2">
              {quest.rewards_xp} XP
            </Badge>
          )}
        </div>

        {/* Quest Details (Expanded) */}
        {isExpanded && (
          <div className="mt-3 ml-6 space-y-2">
            {/* Objectives */}
            <div>
              <p className="text-amber-400 text-xs font-semibold mb-2">Objectives:</p>
              {objectives.length === 0 && (
                <p className="text-xs text-gray-400 italic">
                  Follow this lead in the story; the DM will advance it as you act on it.
                </p>
              )}
              {objectives.map((obj, idx) => (
                <div key={idx} className="flex items-center gap-2 mb-1">
                  {getObjectiveIcon(obj)}
                  <span className={`text-xs ${
                    obj.progress >= (obj.count || 1) ? 'text-green-300 line-through' : 'text-gray-300'
                  }`}>
                    {getObjectiveDescription(obj)}
                  </span>
                  <span className="text-xs text-gray-400 ml-auto">
                    {getObjectiveProgress(obj)}
                  </span>
                </div>
              ))}
            </div>

            {/* Quest Metadata */}
            <div className="text-xs text-gray-400 pt-2 border-t border-gray-700">
              {quest.giver_npc_id && (
                <p>Given by: {quest.giver_npc_id}</p>
              )}
              {quest.location_id && (
                <p>Location: {quest.location_id}</p>
              )}
            </div>

            {/* Status actions — shown only when editable */}
            {onUpdateStatus && quest.status === 'active' && (
              <div className="flex gap-2 pt-2">
                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    onUpdateStatus(quest.quest_id, 'completed');
                  }}
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs border-green-500/40 text-green-300 hover:bg-green-600/10"
                  data-testid={`quest-complete-btn-${quest.quest_id}`}
                >
                  <Check className="h-3 w-3 mr-1" /> Mark complete
                </Button>
                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    onUpdateStatus(quest.quest_id, 'failed');
                  }}
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs border-red-500/40 text-red-300 hover:bg-red-600/10"
                  data-testid={`quest-fail-btn-${quest.quest_id}`}
                >
                  <X className="h-3 w-3 mr-1" /> Mark failed
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const body = (
    <>
      {/* Active Quests */}
      {activeQuests.length > 0 ? (
        <div className="space-y-2 mb-3">
          {activeQuests.map(quest => (
            <QuestCard key={quest.quest_id} quest={quest} />
          ))}
        </div>
      ) : (
        <div className="text-gray-400 text-xs italic text-center py-4">
          No active quests. Explore and talk to NPCs to find new adventures!
        </div>
      )}

      {/* Completed/Failed Quests Toggle */}
      {(completedQuests.length > 0 || failedQuests.length > 0) && (
        <div className="mt-3 pt-3 border-t border-gray-700">
          <Button
            onClick={() => setShowCompleted(!showCompleted)}
            variant="ghost"
            size="sm"
            className="w-full h-7 text-xs text-gray-400 hover:text-gray-200"
          >
            {showCompleted ? 'Hide' : 'Show'} Completed Quests ({completedQuests.length + failedQuests.length})
          </Button>
          {showCompleted && (
            <div className="mt-2 space-y-2">
              {completedQuests.map(quest => (
                <QuestCard key={quest.quest_id} quest={quest} />
              ))}
              {failedQuests.map(quest => (
                <QuestCard key={quest.quest_id} quest={quest} />
              ))}
            </div>
          )}
        </div>
      )}
    </>
  );

  if (embedded) {
    return <div className="space-y-2">{body}</div>;
  }

  return (
    <Card className="bg-black/90 border-amber-600/30 backdrop-blur-sm">
      <CardContent className="p-3">
        {/* Header — click anywhere to fold/unfold the entire panel. */}
        <button
          type="button"
          onClick={() => setIsPanelOpen((v) => !v)}
          className={`w-full flex items-center justify-between ${isPanelOpen ? 'mb-3 pb-2 border-b border-amber-600/20' : ''}`}
          data-testid="quest-log-toggle-btn"
          aria-expanded={isPanelOpen}
        >
          <div className="flex items-center gap-2">
            <Scroll className="h-4 w-4 text-amber-400" />
            <h3 className="text-amber-400 font-semibold text-sm">Quest Log</h3>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs border-amber-400/50 text-amber-300">
              {activeQuests.length} Active
            </Badge>
            {isPanelOpen ? (
              <ChevronUp className="h-4 w-4 text-amber-400/70" />
            ) : (
              <ChevronDown className="h-4 w-4 text-amber-400/70" />
            )}
          </div>
        </button>

        {isPanelOpen && body}
      </CardContent>
    </Card>
  );
};

export default QuestLogPanel;
