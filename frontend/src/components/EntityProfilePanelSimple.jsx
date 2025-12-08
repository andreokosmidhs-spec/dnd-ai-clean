import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { X, Loader2 } from 'lucide-react';
import apiClient from '../lib/apiClient';

/**
 * Simplified EntityProfilePanel for debugging
 * Shows just the basic profile without complex tabs
 */
export const EntityProfilePanelSimple = ({ 
  entity, 
  campaignId,
  characterId,
  onClose 
}) => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    if (entity && campaignId) {
      loadProfile();
    }
  }, [entity?.id, campaignId]);
  
  const loadProfile = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = { campaign_id: campaignId };
      if (characterId) params.character_id = characterId;
      
      const encodedEntityId = encodeURIComponent(entity.id);
      console.log('🔍 Loading profile:', `/api/knowledge/entity-profile/${entity.type}/${encodedEntityId}`);
      
      const response = await apiClient.get(
        `/api/knowledge/entity-profile/${entity.type}/${encodedEntityId}`,
        { params }
      );
      
      console.log('✅ Profile loaded:', response.data);
      setProfile(response.data);
    } catch (err) {
      console.error('❌ Profile load error:', err);
      if (err.response?.status === 404 || err.response?.status === 422) {
        setError('No information known about this entity yet.');
      } else {
        setError('Failed to load profile.');
      }
    } finally {
      setLoading(false);
    }
  };
  
  if (!entity) return null;
  
  return (
    <div className="fixed right-4 top-20 bottom-4 w-96 z-50">
      <Card className="h-full bg-gray-900/95 border-orange-600/30 backdrop-blur-sm flex flex-col">
        <CardHeader className="border-b border-orange-600/20">
          <div className="flex items-center justify-between">
            <CardTitle className="text-orange-400">{entity.name}</CardTitle>
            <Button
              onClick={onClose}
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <p className="text-sm text-gray-400 capitalize">{entity.type}</p>
        </CardHeader>
        
        <CardContent className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="h-6 w-6 animate-spin text-orange-400" />
            </div>
          ) : error ? (
            <div className="text-center text-gray-400 p-4">
              <p>{error}</p>
            </div>
          ) : profile ? (
            <div className="space-y-4">
              <div>
                <h3 className="text-orange-400 font-semibold mb-2">What You Know</h3>
                <p className="text-gray-300 text-sm">
                  {profile.known_summary || 'No details yet.'}
                </p>
              </div>
              
              {profile.total_facts > 0 && (
                <div className="text-xs text-gray-500">
                  {profile.total_facts} fact(s) known
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-gray-400">No data</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default EntityProfilePanelSimple;
