import React, { useState } from 'react';
import { Globe, MapPin, Users, ChevronDown, ChevronUp } from 'lucide-react';

const WorldInfoPanel = ({ worldBlueprint, currentLocation }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!worldBlueprint) {
    return null;
  }

  const worldCore = worldBlueprint.world_core || {};
  const startingRegion = worldBlueprint.starting_region || {};
  const startingTown = worldBlueprint.starting_town || {};
  const pois = worldBlueprint.points_of_interest || [];
  const npcs = worldBlueprint.key_npcs || [];
  const factions = worldBlueprint.factions || [];

  return (
    <div className="bg-gray-800 rounded-lg shadow-lg overflow-hidden border border-gray-700">
      {/* Header - Always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-750 transition-colors"
      >
        <div className="flex items-center gap-3">
          <Globe className="text-blue-400" size={24} />
          <div className="text-left">
            <h3 className="text-white font-bold text-lg">
              {worldCore.name || 'Unknown Realm'}
            </h3>
            <p className="text-gray-400 text-sm">
              {currentLocation || startingTown.name || 'Exploring...'}
            </p>
          </div>
        </div>
        {isExpanded ? (
          <ChevronUp className="text-gray-400" size={20} />
        ) : (
          <ChevronDown className="text-gray-400" size={20} />
        )}
      </button>

      {/* Expandable content */}
      {isExpanded && (
        <div className="p-4 pt-0 space-y-4 border-t border-gray-700">
          {/* World Info */}
          <div>
            <p className="text-gray-300 text-sm leading-relaxed">
              {worldCore.summary || 'A realm of mystery and adventure.'}
            </p>
            {worldCore.tone && (
              <p className="text-gray-500 text-xs mt-1 italic">
                Tone: {worldCore.tone}
              </p>
            )}
          </div>

          {/* Region */}
          {startingRegion.name && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <MapPin className="text-green-400" size={16} />
                <h4 className="text-green-400 font-semibold text-sm">
                  Region: {startingRegion.name}
                </h4>
              </div>
              <p className="text-gray-400 text-sm ml-6">
                {startingRegion.summary || startingRegion.description || 'A mysterious region.'}
              </p>
            </div>
          )}

          {/* Points of Interest */}
          {pois.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <MapPin className="text-yellow-400" size={16} />
                <h4 className="text-yellow-400 font-semibold text-sm">
                  Points of Interest
                </h4>
              </div>
              <div className="ml-6 space-y-3">
                {pois.slice(0, 5).map((poi, idx) => (
                  <div key={idx} className="text-sm leading-relaxed">
                    <span className="text-white font-semibold">{poi.name}:</span>
                    <span className="text-gray-300 ml-1">
                      {poi.summary || poi.description || 'A notable location.'}
                    </span>
                  </div>
                ))}
                {pois.length > 5 && (
                  <p className="text-gray-500 text-xs italic">
                    ...and {pois.length - 5} more locations to discover
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Key NPCs */}
          {npcs.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Users className="text-purple-400" size={16} />
                <h4 className="text-purple-400 font-semibold text-sm">
                  Notable Figures
                </h4>
              </div>
              <div className="space-y-1 ml-6">
                {npcs.slice(0, 4).map((npc, idx) => (
                  <div key={idx} className="flex items-start gap-2">
                    <span className="text-purple-300 text-sm">•</span>
                    <div>
                      <span className="text-white text-sm font-medium">
                        {npc.name}
                      </span>
                      {npc.role && (
                        <span className="text-gray-400 text-xs ml-2">
                          ({npc.role})
                        </span>
                      )}
                    </div>
                  </div>
                ))}
                {npcs.length > 4 && (
                  <p className="text-gray-500 text-xs italic ml-2">
                    ...and {npcs.length - 4} more
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Factions */}
          {factions.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Shield className="text-red-400" size={16} />
                <h4 className="text-red-400 font-semibold text-sm">
                  Factions
                </h4>
              </div>
              <div className="space-y-1 ml-6">
                {factions.slice(0, 3).map((faction, idx) => (
                  <div key={idx} className="flex items-start gap-2">
                    <span className="text-red-300 text-sm">•</span>
                    <span className="text-white text-sm">{faction.name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Missing import
import { Shield } from 'lucide-react';

export default WorldInfoPanel;
