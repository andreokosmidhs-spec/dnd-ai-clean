import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { MapPin, Compass, Trees, Mountain, Sun } from 'lucide-react';
import { mockData } from '../data/mockData';

const WorldMap = ({ worldData, currentLocation, onLocationSelect }) => {
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [viewMode, setViewMode] = useState('regions'); // 'regions' or 'locations'

  const getRegionIcon = (type) => {
    switch (type) {
      case 'temperate-forest':
        return <Trees className="h-4 w-4 text-green-400" />;
      case 'desert':
        return <Sun className="h-4 w-4 text-yellow-400" />;
      case 'arctic':
        return <Mountain className="h-4 w-4 text-blue-400" />;
      default:
        return <MapPin className="h-4 w-4 text-gray-400" />;
    }
  };

  const getRegionColor = (type) => {
    switch (type) {
      case 'temperate-forest':
        return 'border-green-600/50 bg-green-600/10 hover:bg-green-600/20';
      case 'desert':
        return 'border-yellow-600/50 bg-yellow-600/10 hover:bg-yellow-600/20';
      case 'arctic':
        return 'border-blue-600/50 bg-blue-600/10 hover:bg-blue-600/20';
      default:
        return 'border-gray-600/50 bg-gray-600/10 hover:bg-gray-600/20';
    }
  };

  const availableLocations = mockData.locations;

  return (
    <Card className="h-full bg-black/90 border-green-600/30 backdrop-blur-sm flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-green-400 text-lg flex items-center gap-2">
          <Compass className="h-5 w-5" />
          World of {worldData.name}
        </CardTitle>
        <div className="flex gap-2 mt-2">
          <Button
            size="sm"
            variant={viewMode === 'regions' ? 'default' : 'outline'}
            onClick={() => setViewMode('regions')}
            className={viewMode === 'regions' ? 
              'bg-green-600 text-black' : 
              'border-green-600/50 text-green-300 hover:bg-green-600/20'
            }
          >
            Regions
          </Button>
          <Button
            size="sm"
            variant={viewMode === 'locations' ? 'default' : 'outline'}
            onClick={() => setViewMode('locations')}
            className={viewMode === 'locations' ? 
              'bg-green-600 text-black' : 
              'border-green-600/50 text-green-300 hover:bg-green-600/20'
            }
          >
            Locations
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col gap-4">
        
        {viewMode === 'regions' && (
          <div className="space-y-4">
            <h3 className="text-green-400 font-semibold">Known Regions</h3>
            <ScrollArea className="flex-1">
              <div className="space-y-3">
                {worldData.regions.map((region, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-lg border cursor-pointer transition-all duration-200 ${getRegionColor(region.type)} ${
                      selectedRegion?.name === region.name ? 'ring-2 ring-green-400' : ''
                    }`}
                    onClick={() => setSelectedRegion(region)}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      {getRegionIcon(region.type)}
                      <h4 className="text-white font-semibold">{region.name}</h4>
                      <Badge variant="outline" className="text-xs border-gray-400/50 text-gray-300 ml-auto">
                        {region.climate}
                      </Badge>
                    </div>
                    <p className="text-gray-300 text-sm mb-3">{region.description}</p>
                    
                    <div className="space-y-2">
                      <div className="text-xs text-gray-400">Primary Resources:</div>
                      <div className="flex flex-wrap gap-1">
                        {region.resources.map((resource, ridx) => (
                          <Badge 
                            key={ridx} 
                            variant="outline" 
                            className="text-xs border-amber-400/50 text-amber-300"
                          >
                            {resource}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}

        {viewMode === 'locations' && (
          <div className="space-y-4">
            <h3 className="text-green-400 font-semibold">Known Locations</h3>
            <ScrollArea className="flex-1">
              <div className="space-y-3">
                {availableLocations.map((location, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-lg border transition-all duration-200 cursor-pointer ${
                      currentLocation?.id === location.id ? 
                        'border-amber-600/50 bg-amber-600/10 ring-2 ring-amber-400' : 
                        'border-gray-600/50 bg-gray-600/10 hover:bg-gray-600/20'
                    }`}
                    onClick={() => onLocationSelect(location)}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <MapPin className="h-4 w-4 text-purple-400" />
                      <h4 className="text-white font-semibold">{location.name}</h4>
                      {currentLocation?.id === location.id && (
                        <Badge className="text-xs bg-amber-600 text-black ml-auto">
                          Current
                        </Badge>
                      )}
                    </div>
                    
                    <p className="text-gray-300 text-sm mb-3">{location.description}</p>
                    
                    <div className="space-y-2">
                      <div className="text-xs text-gray-400">Features:</div>
                      <div className="flex flex-wrap gap-1">
                        {location.features?.map((feature, fidx) => (
                          <Badge 
                            key={fidx} 
                            variant="outline" 
                            className="text-xs border-purple-400/50 text-purple-300"
                          >
                            {feature}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {location.npcs && location.npcs.length > 0 && (
                      <div className="mt-3 space-y-1">
                        <div className="text-xs text-gray-400">Notable NPCs:</div>
                        <div className="text-xs text-cyan-300">
                          {location.npcs.map(npc => npc.name).join(', ')}
                        </div>
                      </div>
                    )}

                    {location.resources && location.resources.length > 0 && (
                      <div className="mt-3 space-y-1">
                        <div className="text-xs text-gray-400">Resources:</div>
                        <div className="flex flex-wrap gap-1">
                          {location.resources.map((resource, ridx) => (
                            <Badge 
                              key={ridx} 
                              variant="outline" 
                              className="text-xs border-green-400/50 text-green-300"
                            >
                              {resource}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {currentLocation?.id !== location.id && (
                      <Button
                        size="sm"
                        className="mt-3 w-full bg-purple-700 hover:bg-purple-600 text-white"
                        onClick={(e) => {
                          e.stopPropagation();
                          onLocationSelect(location);
                        }}
                      >
                        Travel Here
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}

        {/* Region Details Panel */}
        {selectedRegion && viewMode === 'regions' && (
          <div className="border-t border-green-600/30 pt-4">
            <h4 className="text-green-400 font-semibold mb-2">Region Details</h4>
            <div className="bg-gray-800/50 p-3 rounded space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-400 text-sm">Climate:</span>
                <span className="text-white text-sm">{selectedRegion.climate}</span>
              </div>
              <div className="text-gray-300 text-sm">{selectedRegion.description}</div>
              <div className="text-xs text-gray-500 mt-2">
                Click "Locations" to see specific places you can visit in this region.
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default WorldMap;