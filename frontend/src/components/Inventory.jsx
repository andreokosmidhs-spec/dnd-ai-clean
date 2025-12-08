import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Package, Sword, Shield, Zap, Coins, Search } from 'lucide-react';

const Inventory = ({ inventory, setInventory, character }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItem, setSelectedItem] = useState(null);

  const getItemIcon = (type) => {
    switch (type) {
      case 'weapon':
        return <Sword className="h-4 w-4 text-red-400" />;
      case 'armor':
        return <Shield className="h-4 w-4 text-blue-400" />;
      case 'consumable':
        return <Zap className="h-4 w-4 text-green-400" />;
      case 'currency':
        return <Coins className="h-4 w-4 text-yellow-400" />;
      default:
        return <Package className="h-4 w-4 text-gray-400" />;
    }
  };

  const getItemRarity = (item) => {
    // Mock rarity system
    if (item.name.includes('Magic') || item.name.includes('Enchanted')) return 'rare';
    if (item.name.includes('Master') || item.name.includes('Superior')) return 'uncommon';
    return 'common';
  };

  const getRarityColor = (rarity) => {
    switch (rarity) {
      case 'common':
        return 'border-gray-400/50 text-gray-300';
      case 'uncommon':
        return 'border-green-400/50 text-green-300';
      case 'rare':
        return 'border-blue-400/50 text-blue-300';
      case 'epic':
        return 'border-purple-400/50 text-purple-300';
      case 'legendary':
        return 'border-orange-400/50 text-orange-300';
      default:
        return 'border-gray-400/50 text-gray-300';
    }
  };

  const filteredInventory = inventory.filter(item =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const groupedInventory = {
    weapons: filteredInventory.filter(item => item.type === 'weapon'),
    armor: filteredInventory.filter(item => item.type === 'armor'),
    consumables: filteredInventory.filter(item => item.type === 'consumable'),
    equipment: filteredInventory.filter(item => item.type === 'equipment'),
    currency: filteredInventory.filter(item => item.type === 'currency'),
    misc: filteredInventory.filter(item => !['weapon', 'armor', 'consumable', 'equipment', 'currency'].includes(item.type))
  };

  const useItem = (item) => {
    if (item.type === 'consumable') {
      // Mock healing effect
      if (item.name.includes('Healing')) {
        // Would actually heal the character
        console.log(`Used ${item.name} - Character healed!`);
      }
      
      // Remove or decrease quantity
      if (item.quantity && item.quantity > 1) {
        setInventory(prev => 
          prev.map(inv => 
            inv.name === item.name 
              ? { ...inv, quantity: inv.quantity - 1 }
              : inv
          )
        );
      } else {
        setInventory(prev => prev.filter(inv => inv.name !== item.name));
      }
    } else if (item.type === 'weapon' || item.type === 'armor') {
      // Toggle equipped status
      setInventory(prev =>
        prev.map(inv => {
          if (inv.name === item.name) {
            return { ...inv, equipped: !inv.equipped };
          }
          // Unequip other items of the same type
          if (inv.type === item.type && inv.equipped) {
            return { ...inv, equipped: false };
          }
          return inv;
        })
      );
    }
  };

  const getItemWeight = (item) => {
    // Mock weight system
    const weights = {
      'weapon': Math.floor(Math.random() * 5) + 1,
      'armor': Math.floor(Math.random() * 10) + 5,
      'consumable': 0.5,
      'equipment': Math.floor(Math.random() * 3) + 1,
      'currency': 0.02
    };
    return weights[item.type] || 1;
  };

  const getTotalWeight = () => {
    return inventory.reduce((total, item) => {
      const weight = getItemWeight(item);
      const quantity = item.quantity || 1;
      return total + (weight * quantity);
    }, 0).toFixed(1);
  };

  const getCarryCapacity = () => {
    return character ? character.stats.strength * 15 : 150; // STR * 15 lbs
  };

  return (
    <Card className="h-full bg-black/90 border-green-600/30 backdrop-blur-sm flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-green-400 text-lg flex items-center gap-2">
          <Package className="h-5 w-5" />
          Inventory & Equipment
        </CardTitle>
        
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search items..."
            className="pl-10 bg-gray-800/50 border-green-600/30 text-white placeholder-gray-400"
          />
        </div>

        {/* Carry Capacity */}
        <div className="space-y-1">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Carry Capacity:</span>
            <span className="text-white">{getTotalWeight()} / {getCarryCapacity()} lbs</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                getTotalWeight() / getCarryCapacity() > 0.8 ? 'bg-red-500' :
                getTotalWeight() / getCarryCapacity() > 0.6 ? 'bg-yellow-500' :
                'bg-green-500'
              }`}
              style={{ width: `${Math.min(100, (getTotalWeight() / getCarryCapacity()) * 100)}%` }}
            />
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col gap-4">
        <Tabs defaultValue="all" className="flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-4 bg-black/50 border-green-600/30">
            <TabsTrigger value="all" className="data-[state=active]:bg-green-600/20 data-[state=active]:text-green-400">
              All
            </TabsTrigger>
            <TabsTrigger value="equipped" className="data-[state=active]:bg-blue-600/20 data-[state=active]:text-blue-400">
              Equipped
            </TabsTrigger>
            <TabsTrigger value="consumables" className="data-[state=active]:bg-purple-600/20 data-[state=active]:text-purple-400">
              Consumables
            </TabsTrigger>
            <TabsTrigger value="misc" className="data-[state=active]:bg-amber-600/20 data-[state=active]:text-amber-400">
              Misc
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="all" className="flex-1">
            <ScrollArea className="h-[400px]">
              <div className="space-y-3 pr-4">
                {Object.entries(groupedInventory).map(([category, items]) => (
                  items.length > 0 && (
                    <div key={category} className="space-y-2">
                      <h4 className="text-sm font-semibold text-gray-400 capitalize border-b border-gray-700 pb-1">
                        {category}
                      </h4>
                      {items.map((item, idx) => (
                        <div
                          key={idx}
                          className={`p-3 rounded-lg border transition-all duration-200 cursor-pointer hover:bg-gray-800/50 ${
                            item.equipped ? 'border-amber-600/50 bg-amber-600/10' : 'border-gray-600/50 bg-gray-800/30'
                          } ${selectedItem?.name === item.name ? 'ring-2 ring-green-400' : ''}`}
                          onClick={() => setSelectedItem(item)}
                        >
                          <div className="flex items-center gap-3 mb-2">
                            {getItemIcon(item.type)}
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="text-white font-medium">{item.name}</span>
                                {item.quantity && item.quantity > 1 && (
                                  <Badge variant="outline" className="text-xs border-gray-400/50 text-gray-300">
                                    x{item.quantity}
                                  </Badge>
                                )}
                                {item.equipped && (
                                  <Badge className="text-xs bg-amber-600 text-black">
                                    Equipped
                                  </Badge>
                                )}
                              </div>
                              <div className="flex items-center gap-2 mt-1">
                                <Badge 
                                  variant="outline" 
                                  className={`text-xs ${getRarityColor(getItemRarity(item))}`}
                                >
                                  {getItemRarity(item)}
                                </Badge>
                                {item.damage && (
                                  <Badge variant="outline" className="text-xs border-red-400/50 text-red-300">
                                    {item.damage}
                                  </Badge>
                                )}
                                {item.armorClass && (
                                  <Badge variant="outline" className="text-xs border-blue-400/50 text-blue-300">
                                    AC {item.armorClass}
                                  </Badge>
                                )}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-xs text-gray-400">{getItemWeight(item)} lbs</div>
                              {(item.type === 'consumable' || item.type === 'weapon' || item.type === 'armor') && (
                                <Button
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    useItem(item);
                                  }}
                                  className="mt-1 h-6 px-2 text-xs bg-green-700 hover:bg-green-600"
                                >
                                  {item.type === 'consumable' ? 'Use' : 
                                   item.equipped ? 'Unequip' : 'Equip'}
                                </Button>
                              )}
                            </div>
                          </div>
                          <p className="text-gray-400 text-sm">{item.description}</p>
                          {item.contents && (
                            <div className="mt-2 text-xs text-gray-500">
                              Contains: {item.contents.join(', ')}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )
                ))}
                
                {filteredInventory.length === 0 && (
                  <div className="text-center py-8 text-gray-400">
                    {searchTerm ? 'No items match your search' : 'Your inventory is empty'}
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="equipped" className="flex-1">
            <ScrollArea className="h-[400px]">
              <div className="space-y-3 pr-4">
                {inventory.filter(item => item.equipped).map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg border border-amber-600/50 bg-amber-600/10"
                  >
                    <div className="flex items-center gap-3 mb-2">
                      {getItemIcon(item.type)}
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium">{item.name}</span>
                          <Badge className="text-xs bg-amber-600 text-black">
                            Equipped
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          {item.damage && (
                            <Badge variant="outline" className="text-xs border-red-400/50 text-red-300">
                              {item.damage}
                            </Badge>
                          )}
                          {item.armorClass && (
                            <Badge variant="outline" className="text-xs border-blue-400/50 text-blue-300">
                              AC {item.armorClass}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => useItem(item)}
                        variant="outline"
                        className="h-6 px-2 text-xs border-red-600 text-red-400 hover:bg-red-600/20"
                      >
                        Unequip
                      </Button>
                    </div>
                    <p className="text-gray-400 text-sm">{item.description}</p>
                  </div>
                ))}
                
                {inventory.filter(item => item.equipped).length === 0 && (
                  <div className="text-center py-8 text-gray-400">
                    No items currently equipped
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="consumables" className="flex-1">
            <ScrollArea className="h-[400px]">
              <div className="space-y-3 pr-4">
                {groupedInventory.consumables.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg border border-green-600/50 bg-green-600/10"
                  >
                    <div className="flex items-center gap-3 mb-2">
                      {getItemIcon(item.type)}
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium">{item.name}</span>
                          {item.quantity && item.quantity > 1 && (
                            <Badge variant="outline" className="text-xs border-gray-400/50 text-gray-300">
                              x{item.quantity}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => useItem(item)}
                        className="h-6 px-2 text-xs bg-green-700 hover:bg-green-600"
                      >
                        Use
                      </Button>
                    </div>
                    <p className="text-gray-400 text-sm">{item.description}</p>
                  </div>
                ))}
                
                {groupedInventory.consumables.length === 0 && (
                  <div className="text-center py-8 text-gray-400">
                    No consumable items
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="misc" className="flex-1">
            <ScrollArea className="h-[400px]">
              <div className="space-y-3 pr-4">
                {[...groupedInventory.equipment, ...groupedInventory.currency, ...groupedInventory.misc].map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg border border-gray-600/50 bg-gray-800/30"
                  >
                    <div className="flex items-center gap-3 mb-2">
                      {getItemIcon(item.type)}
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium">{item.name}</span>
                          {item.quantity && item.quantity > 1 && (
                            <Badge variant="outline" className="text-xs border-gray-400/50 text-gray-300">
                              x{item.quantity}
                            </Badge>
                          )}
                        </div>
                        <div className="text-xs text-gray-400 mt-1 capitalize">{item.type}</div>
                      </div>
                      <div className="text-xs text-gray-400">{getItemWeight(item)} lbs</div>
                    </div>
                    <p className="text-gray-400 text-sm">{item.description}</p>
                    {item.contents && (
                      <div className="mt-2 text-xs text-gray-500">
                        Contains: {item.contents.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
                
                {[...groupedInventory.equipment, ...groupedInventory.currency, ...groupedInventory.misc].length === 0 && (
                  <div className="text-center py-8 text-gray-400">
                    No miscellaneous items
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>

        {/* Item Details Panel */}
        {selectedItem && (
          <div className="border-t border-green-600/30 pt-4">
            <div className="bg-gray-800/50 p-3 rounded space-y-2">
              <div className="flex items-center gap-2">
                {getItemIcon(selectedItem.type)}
                <h4 className="text-white font-semibold">{selectedItem.name}</h4>
                <Badge 
                  variant="outline" 
                  className={`text-xs ${getRarityColor(getItemRarity(selectedItem))}`}
                >
                  {getItemRarity(selectedItem)}
                </Badge>
              </div>
              <p className="text-gray-300 text-sm">{selectedItem.description}</p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-400">Type:</span>
                  <span className="text-white ml-1 capitalize">{selectedItem.type}</span>
                </div>
                <div>
                  <span className="text-gray-400">Weight:</span>
                  <span className="text-white ml-1">{getItemWeight(selectedItem)} lbs</span>
                </div>
                {selectedItem.damage && (
                  <div>
                    <span className="text-gray-400">Damage:</span>
                    <span className="text-white ml-1">{selectedItem.damage}</span>
                  </div>
                )}
                {selectedItem.armorClass && (
                  <div>
                    <span className="text-gray-400">AC:</span>
                    <span className="text-white ml-1">{selectedItem.armorClass}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default Inventory;