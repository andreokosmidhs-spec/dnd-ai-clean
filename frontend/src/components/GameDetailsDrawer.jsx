import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Separator } from './ui/separator';
import { Heart, Shield, Zap, MapPin, Cloud, Clock, Flame, Package, Scroll, AlertTriangle, ChevronRight, ChevronLeft } from 'lucide-react';
import { useGameState } from '../contexts/GameStateContext';
import { normalizeCharacter } from '../utils/normalizers';

const GameDetailsDrawer = ({ synced = false }) => {
  const { characterState: rawCharacter, worldState, sessionNotes, threatLevel, isDirty } = useGameState();
  
  // Normalize character at the boundary - hp is ALWAYS present after this
  const characterState = rawCharacter ? normalizeCharacter(rawCharacter) : null;
  const [isOpen, setIsOpen] = useState(false);
  
  // Don't render if no character
  if (!characterState) {
    return null;
  }

  const getStatModifier = (stat) => {
    const mod = Math.floor((stat - 10) / 2);
    return mod >= 0 ? `+${mod}` : `${mod}`;
  };

  const getThreatColor = (level) => {
    const colors = ['text-green-400', 'text-blue-400', 'text-yellow-400', 'text-orange-400', 'text-red-400', 'text-red-600'];
    return colors[level] || colors[2];
  };

  const getThreatLabel = (level) => {
    const labels = ['Peaceful', 'Calm', 'Moderate', 'Tense', 'Dangerous', 'Dire'];
    return labels[level] || labels[2];
  };

  return (
    <>
      {/* Toggle Button */}
      <div className={`fixed top-1/2 -translate-y-1/2 transition-all duration-300 z-40 ${
        isOpen ? 'right-80' : 'right-0'
      }`}>
        <Button
          onClick={() => setIsOpen(!isOpen)}
          size="sm"
          className="rounded-l-lg rounded-r-none bg-violet-700/90 hover:bg-violet-600 text-white border-l border-t border-b border-violet-400/50 shadow-lg"
        >
          {isOpen ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      {/* Drawer */}
      <div className={`fixed top-0 right-0 h-screen w-80 bg-black/95 border-l border-violet-600/30 backdrop-blur-sm transition-transform duration-300 z-30 overflow-y-auto ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}>
        <div className="p-4 space-y-4">
          
          {/* Sync Status */}
          {synced && !isDirty && (
            <div className="flex items-center justify-center gap-2 text-green-400 text-sm animate-in fade-in duration-300">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span>State Synced</span>
            </div>
          )}

          {isDirty && (
            <div className="flex items-center justify-center gap-2 text-yellow-400 text-sm">
              <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
              <span>Changes Pending</span>
            </div>
          )}

          {/* Character Vitals */}
          <Card className="bg-gray-900/50 border-red-600/30">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-red-400 flex items-center gap-2">
                <Heart className="h-4 w-4" />
                Vitals
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-gray-400 text-sm">HP</span>
                <span className="text-white font-semibold">
                  {characterState.hp.current}/{characterState.hp.max}
                  {characterState.hp.temp > 0 && (
                    <span className="text-blue-400 ml-1">+{characterState.hp.temp}</span>
                  )}
                </span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div 
                  className="bg-red-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(characterState.hp.current / characterState.hp.max) * 100}%` }}
                />
              </div>
              <div className="flex justify-between text-sm pt-1">
                <div className="flex items-center gap-2">
                  <Shield className="h-3 w-3 text-blue-400" />
                  <span className="text-gray-400">AC:</span>
                  <span className="text-white font-semibold">{characterState.ac}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Zap className="h-3 w-3 text-yellow-400" />
                  <span className="text-gray-400">Speed:</span>
                  <span className="text-white font-semibold">{characterState.speed}ft</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Conditions */}
          {characterState.conditions && characterState.conditions.length > 0 && (
            <Card className="bg-gray-900/50 border-orange-600/30">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-orange-400 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Conditions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1">
                  {characterState.conditions.map((condition, idx) => (
                    <Badge key={idx} variant="outline" className="border-orange-400/50 text-orange-300 text-xs">
                      {condition}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Equipped Items */}
          <Card className="bg-gray-900/50 border-amber-600/30">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-amber-400 flex items-center gap-2">
                <Package className="h-4 w-4" />
                Equipped
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1 text-sm">
                {characterState.inventory.filter(item => item.equipped).map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className="text-gray-300">{item.name}</span>
                    <div className="flex gap-1">
                      {item.tags.slice(0, 2).map((tag, tagIdx) => (
                        <Badge key={tagIdx} variant="outline" className="border-amber-400/30 text-amber-400 text-xs px-1">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                ))}
                {(!characterState.inventory || characterState.inventory.filter(item => item.equipped).length === 0) && (
                  <span className="text-gray-500 text-xs">No items equipped</span>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Spell Slots */}
          {characterState.spell_slots && Object.keys(characterState.spell_slots).length > 0 && (
            <Card className="bg-gray-900/50 border-cyan-600/30">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-cyan-400 flex items-center gap-2">
                  <Scroll className="h-4 w-4" />
                  Spell Slots
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-1 text-sm">
                  {Object.entries(characterState.spell_slots).map(([level, slots]) => (
                    <div key={level} className="flex justify-between items-center">
                      <span className="text-gray-400">Level {level}</span>
                      <div className="flex gap-1">
                        {Array.from({ length: slots }).map((_, idx) => (
                          <div key={idx} className="w-3 h-3 rounded-full bg-cyan-500"></div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* World State */}
          <Card className="bg-gray-900/50 border-purple-600/30">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-purple-400 flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                World
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div>
                <span className="text-gray-400">Location: </span>
                <span className="text-white">{worldState.location}</span>
              </div>
              <div>
                <span className="text-gray-400">Settlement: </span>
                <span className="text-white">{worldState.settlement}</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-3 w-3 text-purple-400" />
                <span className="text-gray-300">{worldState.time_of_day}</span>
              </div>
              <div className="flex items-center gap-2">
                <Cloud className="h-3 w-3 text-purple-400" />
                <span className="text-gray-300">{worldState.weather}</span>
              </div>
            </CardContent>
          </Card>

          {/* Threat Level */}
          <Card className={`bg-gray-900/50 border-${getThreatColor(threatLevel).replace('text-', '')}/30`}>
            <CardHeader className="pb-3">
              <CardTitle className={`text-sm ${getThreatColor(threatLevel)} flex items-center gap-2`}>
                <Flame className="h-4 w-4" />
                Threat Level
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex justify-between items-center">
                <span className={`${getThreatColor(threatLevel)} font-semibold`}>
                  {getThreatLabel(threatLevel)}
                </span>
                <span className={`${getThreatColor(threatLevel)} text-lg font-bold`}>
                  {threatLevel}/5
                </span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2 mt-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${
                    getThreatColor(threatLevel).replace('text-', 'bg-')
                  }`}
                  style={{ width: `${(threatLevel / 5) * 100}%` }}
                />
              </div>
            </CardContent>
          </Card>

          {/* Session Notes */}
          {sessionNotes && sessionNotes.length > 0 && (
            <Card className="bg-gray-900/50 border-gray-600/30">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-gray-400">Recent Events</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-1 text-xs text-gray-400">
                  {sessionNotes.slice(-5).reverse().map((note, idx) => (
                    <div key={idx} className="flex items-start gap-2">
                      <div className="w-1 h-1 bg-gray-500 rounded-full mt-1.5"></div>
                      <span>{note.text}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

        </div>
      </div>
    </>
  );
};

export default GameDetailsDrawer;
