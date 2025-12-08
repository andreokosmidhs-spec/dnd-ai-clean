import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { X, Loader2, MapPin, Users, Shield, Package } from 'lucide-react';
import apiClient from '../lib/apiClient';

/**
 * EntityQuickInspect - Right-side sliding panel for quick entity info
 * Backed by the Campaign Log system (not the old KnowledgeFacts)
 */
export const EntityQuickInspect = ({ 
  entity, // {type, id, name}
  campaignId,
  characterId,
  onClose 
}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    if (entity) {
      loadEntity();
    }
  }, [entity?.id]);
  
  const loadEntity = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = { campaign_id: campaignId };
      if (characterId) params.character_id = characterId;
      
      console.log('🔍 Loading entity from campaign log:', entity.type, entity.id);
      
      // Call the new campaign log API
      const response = await apiClient.get(
        `/api/campaign/log/${entity.type}s/${entity.id}`,
        { params }
      );
      
      console.log('✅ Entity loaded:', response.data);
      setData(response.data);
    } catch (err) {
      console.error('❌ Failed to load entity:', err);
      if (err.response?.status === 404) {
        setError('No information known about this entity yet. Keep exploring!');
      } else {
        setError(`Failed to load entity: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };
  
  const getIcon = () => {
    switch (entity.type) {
      case 'location': return <MapPin className="h-5 w-5 text-orange-400" />;
      case 'npc': return <Users className="h-5 w-5 text-orange-400" />;
      case 'faction': return <Shield className="h-5 w-5 text-orange-400" />;
      case 'item': return <Package className="h-5 w-5 text-orange-400" />;
      default: return null;
    }
  };
  
  const renderLocationContent = () => {
    if (!data) return null;
    
    return (
      <div className="space-y-4">
        {data.geography && (
          <div>
            <h4 className="text-sm font-semibold text-orange-400 mb-2">Location</h4>
            <p className="text-sm text-gray-300">{data.geography}</p>
          </div>
        )}
        
        {data.notable_places && data.notable_places.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-orange-400 mb-2">Notable Places</h4>
            <ul className="list-disc list-inside space-y-1">
              {data.notable_places.slice(0, 3).map((place, idx) => (
                <li key={idx} className="text-sm text-gray-300">{place}</li>
              ))}
            </ul>
          </div>
        )}
        
        {data.architecture && (
          <div>
            <h4 className="text-sm font-semibold text-orange-400 mb-2">Architecture</h4>
            <p className="text-sm text-gray-300">{data.architecture}</p>
          </div>
        )}
        
        {data.culture_notes && (
          <div>
            <h4 className="text-sm font-semibold text-orange-400 mb-2">Culture</h4>
            <p className="text-sm text-gray-300">{data.culture_notes}</p>
          </div>
        )}
      </div>
    );
  };
  
  const renderNpcContent = () => {
    if (!data) return null;
    
    return (
      <div className="space-y-4">
        {data.role && (
          <Badge variant="outline" className="border-orange-400/50 text-orange-300">
            {data.role}
          </Badge>
        )}
        
        {data.appearance && (
          <div>
            <h4 className="text-sm font-semibold text-orange-400 mb-2">Appearance</h4>
            <p className="text-sm text-gray-300">{data.appearance}</p>
          </div>
        )}
        
        {data.personality && (
          <div>
            <h4 className="text-sm font-semibold text-orange-400 mb-2">Personality</h4>
            <p className="text-sm text-gray-300">{data.personality}</p>
          </div>
        )}
        
        {data.wants && (
          <div>
            <h4 className="text-sm font-semibold text-orange-400 mb-2">Wants</h4>
            <p className="text-sm text-gray-300">{data.wants}</p>
          </div>
        )}
        
        {data.offered && (
          <div>
            <h4 className="text-sm font-semibold text-orange-400 mb-2">Offered</h4>
            <p className="text-sm text-gray-300">{data.offered}</p>
          </div>
        )}
        
        {data.relationship_to_party && (
          <div>
            <h4 className="text-sm font-semibold text-orange-400 mb-2">Relationship</h4>
            <Badge 
              variant="outline"
              className={
                data.relationship_to_party === 'friendly' || data.relationship_to_party === 'ally' ? 'border-green-400 text-green-300' :
                data.relationship_to_party === 'hostile' ? 'border-red-400 text-red-300' :
                'border-gray-400 text-gray-300'
              }
            >
              {data.relationship_to_party}
            </Badge>
          </div>
        )}
      </div>
    );
  };
  
  const renderFactionContent = () => {
    if (!data) return null;
    
    return (
      <div className="space-y-4">
        {data.stated_purpose && (
          <div>
            <h4 className="text-sm font-semibold text-orange-400 mb-2">Stated Purpose</h4>
            <p className="text-sm text-gray-300">{data.stated_purpose}</p>
          </div>
        )}
        
        {data.suspected_purpose && (
          <div>
            <h4 className="text-sm font-semibold text-yellow-400 mb-2">Suspected Purpose</h4>
            <p className="text-sm text-yellow-200">{data.suspected_purpose}</p>
          </div>
        )}
        
        {data.symbols && (
          <div>
            <h4 className="text-sm font-semibold text-orange-400 mb-2">Symbol</h4>
            <p className="text-sm text-gray-300">{data.symbols}</p>
          </div>
        )}
        
        {data.relationship_to_party && (
          <div>
            <h4 className="text-sm font-semibold text-orange-400 mb-2">Relationship</h4>
            <Badge 
              variant="outline"
              className={
                data.relationship_to_party === 'ally' ? 'border-green-400 text-green-300' :
                data.relationship_to_party === 'hostile' ? 'border-red-400 text-red-300' :
                'border-gray-400 text-gray-300'
              }
            >
              {data.relationship_to_party}
            </Badge>
          </div>
        )}
      </div>
    );
  };
  
  const renderItemContent = () => {
    if (!data) return null;
    
    return (
      <div className="space-y-4">
        {data.appearance && (
          <div>
            <h4 className="text-sm font-semibold text-orange-400 mb-2">Appearance</h4>
            <p className="text-sm text-gray-300">{data.appearance}</p>
          </div>
        )}
        
        {data.known_properties && (
          <div>
            <h4 className="text-sm font-semibold text-orange-400 mb-2">Properties</h4>
            <p className="text-sm text-gray-300">{data.known_properties}</p>
          </div>
        )}
        
        {data.suspected_properties && (
          <div>
            <h4 className="text-sm font-semibold text-yellow-400 mb-2">Suspected</h4>
            <p className="text-sm text-yellow-200">{data.suspected_properties}</p>
          </div>
        )}
        
        {data.currently_held && (
          <Badge variant="outline" className="border-green-400/50 text-green-300">
            In Inventory
          </Badge>
        )}
      </div>
    );
  };
  
  const renderContent = () => {
    switch (entity.type) {
      case 'location': return renderLocationContent();
      case 'npc': return renderNpcContent();
      case 'faction': return renderFactionContent();
      case 'item': return renderItemContent();
      default: return <p className="text-gray-400">Unknown entity type</p>;
    }
  };
  
  if (!entity) return null;
  
  return (
    <div className="fixed right-4 top-20 bottom-4 w-96 z-50 animate-in slide-in-from-right duration-300">
      <Card className="h-full bg-gray-900/95 border-orange-600/30 backdrop-blur-sm flex flex-col shadow-2xl shadow-orange-600/20">
        <CardHeader className="border-b border-orange-600/20 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getIcon()}
              <div className="flex-1 min-w-0">
                <CardTitle className="text-orange-400 text-lg truncate">{entity.name}</CardTitle>
                <Badge variant="outline" className="mt-1 text-xs border-orange-400/50 text-orange-300 capitalize">
                  {entity.type}
                </Badge>
              </div>
            </div>
            <Button
              onClick={onClose}
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 text-orange-400 hover:text-orange-200 hover:bg-orange-600/20 flex-shrink-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center h-full text-gray-400">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              Loading...
            </div>
          ) : error ? (
            <div className="text-center text-gray-400 p-4">
              <p>{error}</p>
            </div>
          ) : (
            renderContent()
          )}
        </CardContent>
        
        <div className="border-t border-orange-600/20 p-3 flex-shrink-0">
          <p className="text-xs text-gray-500 text-center">
            Open full Campaign Log for more details
          </p>
        </div>
      </Card>
    </div>
  );
};

export default EntityQuickInspect;
