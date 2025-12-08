import React, { useState } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Sparkles, Flame, Zap } from 'lucide-react';

/**
 * Cantrip Selection Component
 * For racial traits that grant cantrip choices (e.g., High Elf)
 */
const CantripSelection = ({ cantrips, count = 1, selectedCantrips = [], onSelect, source }) => {
  const [selected, setSelected] = useState(selectedCantrips);

  const toggleCantrip = (cantrip) => {
    let newSelected;
    
    if (selected.find(c => c.name === cantrip.name)) {
      // Deselect
      newSelected = selected.filter(c => c.name !== cantrip.name);
    } else if (selected.length < count) {
      // Select (if under limit)
      newSelected = [...selected, cantrip];
    } else {
      // At limit, replace last selection
      newSelected = [...selected.slice(0, -1), cantrip];
    }
    
    setSelected(newSelected);
    onSelect(newSelected);
  };

  const isSelected = (cantrip) => {
    return selected.some(c => c.name === cantrip.name);
  };

  const getDamageIcon = (damage) => {
    if (damage.includes('fire')) return <Flame className="h-4 w-4 text-red-400" />;
    if (damage.includes('lightning')) return <Zap className="h-4 w-4 text-yellow-400" />;
    if (damage.includes('cold')) return <Sparkles className="h-4 w-4 text-blue-400" />;
    return <Sparkles className="h-4 w-4 text-purple-400" />;
  };

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-purple-400" />
          <h4 className="text-purple-400 font-semibold">Choose {count} Cantrip{count > 1 ? 's' : ''}</h4>
        </div>
        <Badge className={selected.length === count ? "bg-green-600" : "bg-amber-600"}>
          {selected.length} / {count} selected
        </Badge>
      </div>

      {source && (
        <p className="text-sm text-gray-400">
          From: <span className="text-purple-300">{source}</span>
        </p>
      )}

      {/* Cantrip Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {cantrips.map((cantrip) => {
          const selected = isSelected(cantrip);
          
          return (
            <Card
              key={cantrip.name}
              className={`cursor-pointer transition-all ${
                selected
                  ? 'border-purple-600 bg-purple-600/20'
                  : 'border-gray-600 bg-gray-800/30 hover:border-purple-600/50'
              }`}
              onClick={() => toggleCantrip(cantrip)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getDamageIcon(cantrip.damage)}
                    <h5 className="font-semibold text-white">{cantrip.name}</h5>
                  </div>
                  {selected && (
                    <Badge className="bg-purple-600">Selected</Badge>
                  )}
                </div>

                <p className="text-sm text-gray-300 mb-2">{cantrip.description}</p>

                <div className="flex flex-wrap gap-2 text-xs text-gray-400">
                  <span>⚡ {cantrip.castingTime}</span>
                  <span>📏 {cantrip.range}</span>
                  {cantrip.damage !== "None (utility)" && (
                    <span className="text-red-400">💥 {cantrip.damage}</span>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Selected Cantrips Summary */}
      {selected.length > 0 && (
        <div className="p-3 bg-purple-900/20 rounded border border-purple-600/50">
          <p className="text-purple-400 text-sm font-semibold mb-1">Your Cantrips:</p>
          <div className="flex flex-wrap gap-2">
            {selected.map(cantrip => (
              <Badge key={cantrip.name} className="bg-purple-600">
                {cantrip.name}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CantripSelection;
