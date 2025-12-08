import React, { useState, useEffect } from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from './ui/sheet';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/accordion';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import { Info, MapPin, User, Package, BookOpen, Heart, Zap, Shield } from 'lucide-react';
import { mockData } from '../data/mockData';

const InfoDrawer = ({ character, currentLocation, inventory, gameLog, isOpen, onOpenChange }) => {
  const [activeTab, setActiveTab] = useState(() => {
    return localStorage.getItem('rpg-info-drawer-tab') || 'overview';
  });

  useEffect(() => {
    localStorage.setItem('rpg-info-drawer-tab', activeTab);
  }, [activeTab]);

  // Keyboard shortcut
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      
      if (e.key === 'i' || e.key === 'I') {
        onOpenChange(!isOpen);
      }
    };

    window.addEventListener('keypress', handleKeyPress);
    return () => window.removeEventListener('keypress', handleKeyPress);
  }, [isOpen, onOpenChange]);

  const getStatModifier = (stat) => {
    return Math.floor((stat - 10) / 2);
  };

  const getStatModifierString = (stat) => {
    const mod = getStatModifier(stat);
    return mod >= 0 ? `+${mod}` : `${mod}`;
  };

  const StatBlock = ({ label, value, modifier }) => (
    <div className="flex justify-between items-center py-1">
      <span className="text-gray-400 text-sm">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-white font-medium">{value}</span>
        {modifier !== undefined && (
          <span className="text-gray-300 text-sm">({modifier})</span>
        )}
      </div>
    </div>
  );

  return (
    <Sheet open={isOpen} onOpenChange={onOpenChange}>
      <SheetTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="fixed top-4 right-4 z-40 bg-black/80 border-amber-600/30 text-amber-300 hover:bg-amber-600/20"
        >
          <Info className="h-4 w-4 mr-2" />
          Info
          <Badge variant="secondary" className="ml-2 h-4 px-1 text-xs">I</Badge>
        </Button>
      </SheetTrigger>
      
      <SheetContent className="w-96 bg-black/95 border-l border-amber-600/30 backdrop-blur-sm overflow-hidden">
        <SheetHeader className="pb-4">
          <SheetTitle className="text-amber-400 flex items-center gap-2">
            <Info className="h-5 w-5" />
            Adventure Info
          </SheetTitle>
        </SheetHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <TabsList className="grid w-full grid-cols-4 bg-gray-900/50 mb-4">
            <TabsTrigger value="overview" className="text-xs data-[state=active]:bg-amber-600/20">
              Overview
            </TabsTrigger>
            <TabsTrigger value="character" className="text-xs data-[state=active]:bg-blue-600/20">
              Character
            </TabsTrigger>
            <TabsTrigger value="inventory" className="text-xs data-[state=active]:bg-green-600/20">
              Items
            </TabsTrigger>
            <TabsTrigger value="log" className="text-xs data-[state=active]:bg-purple-600/20">
              Log
            </TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-hidden">
            {/* Overview Tab */}
            <TabsContent value="overview" className="mt-0 h-full">
              <ScrollArea className="h-full">
                <div className="space-y-4 pr-3">
                  <div className="bg-gray-900/50 rounded-lg p-3">
                    <h3 className="text-amber-400 font-semibold mb-2 flex items-center gap-2">
                      <MapPin className="h-4 w-4" />
                      Current Location
                    </h3>
                    {currentLocation ? (
                      <div>
                        <h4 className="text-white font-medium mb-1">{currentLocation.name}</h4>
                        <p className="text-gray-300 text-sm leading-relaxed mb-2">{currentLocation.description}</p>
                        {currentLocation.features && currentLocation.features.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {currentLocation.features.map((feature, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs border-purple-400/50 text-purple-300">
                                {feature}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-gray-400 text-sm">No current location data</p>
                    )}
                  </div>

                  {currentLocation?.npcs && currentLocation.npcs.length > 0 && (
                    <div className="bg-gray-900/50 rounded-lg p-3">
                      <h3 className="text-cyan-400 font-semibold mb-2">Nearby NPCs</h3>
                      <div className="space-y-2">
                        {currentLocation.npcs.map((npc, idx) => (
                          <div key={idx} className="bg-gray-800/50 rounded p-2">
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-white text-sm font-medium">{npc.name}</span>
                              <Badge variant="outline" className="text-xs border-cyan-400/50 text-cyan-300">
                                {npc.class}
                              </Badge>
                            </div>
                            <p className="text-gray-400 text-xs">{npc.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="bg-gray-900/50 rounded-lg p-3">
                    <h3 className="text-green-400 font-semibold mb-2">Quest Objectives</h3>
                    <p className="text-gray-400 text-sm">
                      Explore the world and interact with NPCs to discover quests and objectives.
                    </p>
                  </div>
                </div>
              </ScrollArea>
            </TabsContent>

            {/* Character Tab */}
            <TabsContent value="character" className="mt-0 h-full">
              <ScrollArea className="h-full">
                <div className="space-y-4 pr-3">
                  {character && (
                    <>
                      <div className="bg-gray-900/50 rounded-lg p-3">
                        <h3 className="text-blue-400 font-semibold mb-3 flex items-center gap-2">
                          <User className="h-4 w-4" />
                          {character.name}
                        </h3>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-400">Race:</span>
                            <span className="text-white">{character.race}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Class:</span>
                            <span className="text-white">{character.class}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Level:</span>
                            <span className="text-white">{character.level}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Background:</span>
                            <span className="text-white">
                              {character.background}
                              {(() => {
                                const bg = mockData.backgrounds.find(b => b.name === character.background);
                                if (bg?.variants && character.backgroundVariantKey) {
                                  const variant = bg.variants[character.backgroundVariantKey];
                                  if (variant && variant.label !== character.background) {
                                    return <span className="text-purple-300 text-xs ml-1">({variant.label})</span>;
                                  }
                                }
                                return null;
                              })()}
                            </span>
                          </div>
                        </div>
                      </div>

                      <Accordion type="single" collapsible className="space-y-2">
                        <AccordionItem value="stats" className="bg-gray-900/50 rounded-lg px-3">
                          <AccordionTrigger className="text-green-400 font-semibold hover:no-underline">
                            <div className="flex items-center gap-2">
                              <Heart className="h-4 w-4" />
                              Ability Scores
                            </div>
                          </AccordionTrigger>
                          <AccordionContent className="pb-3">
                            <div className="space-y-1">
                              {character.stats && Object.entries(character.stats).map(([stat, value]) => (
                                <StatBlock 
                                  key={stat}
                                  label={stat.charAt(0).toUpperCase() + stat.slice(1)}
                                  value={value}
                                  modifier={getStatModifierString(value)}
                                />
                              ))}
                            </div>
                          </AccordionContent>
                        </AccordionItem>

                        <AccordionItem value="health" className="bg-gray-900/50 rounded-lg px-3">
                          <AccordionTrigger className="text-red-400 font-semibold hover:no-underline">
                            <div className="flex items-center gap-2">
                              <Heart className="h-4 w-4" />
                              Health & Resources
                            </div>
                          </AccordionTrigger>
                          <AccordionContent className="pb-3">
                            <div className="space-y-1">
                              <StatBlock label="Hit Points" value={`${character.hitPoints}/${character.hitPoints}`} />
                              <StatBlock label="Armor Class" value={10 + getStatModifier(character.stats?.dexterity || 10)} />
                              {character.spellSlots && character.spellSlots.length > 0 && (
                                <StatBlock label="Spell Slots" value={character.spellSlots.length} />
                              )}
                            </div>
                          </AccordionContent>
                        </AccordionItem>

                        {character.traits && character.traits.length > 0 && (
                          <AccordionItem value="traits" className="bg-gray-900/50 rounded-lg px-3">
                            <AccordionTrigger className="text-purple-400 font-semibold hover:no-underline">
                              <div className="flex items-center gap-2">
                                <Zap className="h-4 w-4" />
                                Traits & Features
                              </div>
                            </AccordionTrigger>
                            <AccordionContent className="pb-3">
                              <div className="flex flex-wrap gap-1">
                                {character.traits.map((trait, idx) => (
                                  <Badge key={idx} variant="outline" className="text-xs border-purple-400/50 text-purple-300">
                                    {typeof trait === 'string' ? trait : trait?.text || 'Trait'}
                                  </Badge>
                                ))}
                              </div>
                            </AccordionContent>
                          </AccordionItem>
                        )}
                      </Accordion>
                    </>
                  )}
                </div>
              </ScrollArea>
            </TabsContent>

            {/* Inventory Tab */}
            <TabsContent value="inventory" className="mt-0 h-full">
              <ScrollArea className="h-full">
                <div className="space-y-4 pr-3">
                  <div className="bg-gray-900/50 rounded-lg p-3">
                    <h3 className="text-green-400 font-semibold mb-3 flex items-center gap-2">
                      <Package className="h-4 w-4" />
                      Inventory
                    </h3>
                    
                    {inventory && inventory.length > 0 ? (
                      <Accordion type="single" collapsible className="space-y-2">
                        {['weapon', 'armor', 'consumable', 'equipment', 'currency'].map(category => {
                          const items = inventory.filter(item => item.type === category);
                          if (items.length === 0) return null;
                          
                          return (
                            <AccordionItem key={category} value={category} className="bg-gray-800/50 rounded px-2">
                              <AccordionTrigger className="text-yellow-400 text-sm hover:no-underline capitalize">
                                {category} ({items.length})
                              </AccordionTrigger>
                              <AccordionContent className="pb-2">
                                <div className="space-y-2">
                                  {items.map((item, idx) => (
                                    <div key={idx} className="bg-gray-700/50 rounded p-2">
                                      <div className="flex justify-between items-center">
                                        <span className="text-white text-sm font-medium">{item.name}</span>
                                        {item.equipped && (
                                          <Badge className="text-xs bg-amber-600 text-black">Equipped</Badge>
                                        )}
                                      </div>
                                      <p className="text-gray-400 text-xs mt-1">{item.description}</p>
                                    </div>
                                  ))}
                                </div>
                              </AccordionContent>
                            </AccordionItem>
                          );
                        })}
                      </Accordion>
                    ) : (
                      <p className="text-gray-400 text-sm">Your inventory is empty.</p>
                    )}
                  </div>
                </div>
              </ScrollArea>
            </TabsContent>

            {/* Log Tab */}
            <TabsContent value="log" className="mt-0 h-full">
              <ScrollArea className="h-full">
                <div className="space-y-4 pr-3">
                  <div className="bg-gray-900/50 rounded-lg p-3">
                    <h3 className="text-purple-400 font-semibold mb-3 flex items-center gap-2">
                      <BookOpen className="h-4 w-4" />
                      Recent Events
                    </h3>
                    
                    {gameLog && gameLog.length > 0 ? (
                      <div className="space-y-2">
                        {gameLog.slice(-10).reverse().map((entry, idx) => (
                          <div key={idx} className="bg-gray-800/50 rounded p-2">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge variant="outline" className="text-xs capitalize">
                                {entry.type}
                              </Badge>
                              {entry.timestamp && (
                                <span className="text-gray-400 text-xs">
                                  {new Date(entry.timestamp).toLocaleTimeString()}
                                </span>
                              )}
                            </div>
                            <p className="text-gray-300 text-sm leading-relaxed line-clamp-3">
                              {entry.message}
                            </p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-400 text-sm">No recent events to display.</p>
                    )}
                  </div>
                </div>
              </ScrollArea>
            </TabsContent>
          </div>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
};

export default InfoDrawer;