import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Sword, Play, PlusCircle, Trash2, User, Crown, Database } from 'lucide-react';
import apiClient, { isSuccess, getErrorMessage } from '../lib/apiClient';

const MainMenu = ({ onNewCampaign, onContinueCampaign, onLoadLastCampaign }) => {
  const navigate = useNavigate();
  const [hasSavedCampaign, setHasSavedCampaign] = useState(false);
  const [savedCharacter, setSavedCharacter] = useState(null);
  const [showConfirmDelete, setShowConfirmDelete] = useState(false);
  const [isLoadingCampaign, setIsLoadingCampaign] = useState(false);

  useEffect(() => {
    // Check for existing campaign
    const savedChar = localStorage.getItem('rpg-campaign-character');
    const savedSession = localStorage.getItem('dm-session-id');
    
    if (savedChar) {
      try {
        const character = JSON.parse(savedChar);
        setSavedCharacter(character);
        setHasSavedCampaign(true);
      } catch (e) {
        console.error('Failed to load saved campaign:', e);
      }
    }
  }, []);

  const handleNewCampaign = () => {
    if (hasSavedCampaign) {
      setShowConfirmDelete(true);
    } else {
      if (onNewCampaign) {
        onNewCampaign();
      } else {
        navigate('/character-v2');
      }
    }
  };

  const handleConfirmNewCampaign = () => {
    // Clear all campaign data
    localStorage.removeItem('rpg-campaign-character');
    localStorage.removeItem('rpg-campaign-gamestate');
    localStorage.removeItem('dm-session-id');
    localStorage.removeItem('dm-intro-played');
    localStorage.removeItem('game-state-session-id');
    
    // Clear all session-specific data
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith('dm-log-') || key.startsWith('game-state-')) {
        localStorage.removeItem(key);
      }
    });
    
    setHasSavedCampaign(false);
    setSavedCharacter(null);
    setShowConfirmDelete(false);
    
    if (window.showToast) {
      window.showToast('🗑️ Previous campaign deleted. Starting fresh!', 'success');
    }
    
    if (onNewCampaign) {
      onNewCampaign();
    } else {
      navigate('/character-v2');
    }
  };

  const handleLoadLastCampaign = async () => {
    setIsLoadingCampaign(true);
    
    if (window.showToast) {
      window.showToast('🔍 Loading last campaign from database...', 'info');
    }
    
    console.log('[FLOW] Load last campaign clicked');
    
    try {
      const response = await apiClient.get('/api/campaigns/latest');
      
      if (isSuccess(response)) {
        const { campaign_id, world_blueprint, intro, entity_mentions, scene_description, starting_location, character, character_id, world_state } = response.data;
        
        console.log('✅ [FLOW] Loaded campaign from DB:', campaign_id);
        console.log('📜 [FLOW] Character:', character.name);
        console.log('🔗 [FLOW] Entity mentions:', entity_mentions ? entity_mentions.length : 0);
        console.log('📍 [FLOW] Scene description:', scene_description ? scene_description.location : 'none');
        console.log('✅ [FLOW] Campaign and character exist in MongoDB');
        
        // Call the callback to handle the loaded data
        if (onLoadLastCampaign) {
          onLoadLastCampaign({
            campaign_id,
            world_blueprint,
            intro,
            entity_mentions,
            scene_description,
            starting_location,
            character,
            character_id,
            world_state
          });
        }
        
        if (window.showToast) {
          window.showToast(`✅ Loaded campaign: ${character.name}`, 'success');
        }
      } else {
        // Handle error response
        const errorMessage = response.error?.type === 'not_found' 
          ? 'No campaigns found in database. Create a new campaign first.'
          : getErrorMessage(response.error);
        
        console.error('❌ [FLOW] Load campaign failed:', errorMessage);
        
        if (window.showToast) {
          window.showToast(`❌ ${errorMessage}`, 'error');
        } else {
          alert(errorMessage);
        }
      }
    } catch (error) {
      console.error('❌ [FLOW] Load campaign exception:', error);
      
      if (window.showToast) {
        window.showToast(`❌ Failed to load campaign`, 'error');
      } else {
        alert('Failed to load campaign');
      }
    } finally {
      setIsLoadingCampaign(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-gray-900 to-black flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzMzMzMzMyIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-20"></div>
      
      <Card className="max-w-2xl w-full bg-black/90 border-amber-600/30 backdrop-blur-sm relative z-10 shadow-2xl">
        <CardHeader className="text-center pb-8 pt-12">
          <div className="flex justify-center mb-6">
            <div className="relative">
              <Sword className="h-20 w-20 text-amber-400 animate-pulse" />
              <div className="absolute -top-2 -right-2">
                <Crown className="h-10 w-10 text-amber-500" />
              </div>
            </div>
          </div>
          <CardTitle className="text-5xl text-amber-400 font-bold mb-2">
            RPG Forge
          </CardTitle>
          <p className="text-gray-400 text-lg">AI-Powered Text RPG Adventure</p>
        </CardHeader>

        <CardContent className="space-y-6 pb-12">
          {/* Saved Campaign Info */}
          {hasSavedCampaign && savedCharacter && (
            <div className="p-4 bg-gradient-to-r from-violet-600/20 to-purple-600/20 border-2 border-violet-400/50 rounded-lg">
              <div className="flex items-center gap-3 mb-2">
                <User className="h-5 w-5 text-violet-400" />
                <span className="text-violet-400 font-semibold">Saved Campaign</span>
              </div>
              <div className="text-white ml-8">
                <div className="font-bold text-lg">{savedCharacter.name}</div>
                <div className="text-sm text-gray-300">
                  Level {savedCharacter.level} {savedCharacter.race} {savedCharacter.class}
                </div>
                {savedCharacter.background && (
                  <div className="text-xs text-gray-400">
                    Background: {savedCharacter.background}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Main Buttons */}
          <div className="space-y-4">
            {hasSavedCampaign ? (
              <Button
                onClick={onContinueCampaign}
                className="w-full bg-gradient-to-r from-green-700 to-emerald-700 hover:from-green-600 hover:to-emerald-600 text-white font-bold text-xl py-8 shadow-lg shadow-green-600/50 border-2 border-green-400/50"
                size="lg"
              >
                <Play className="h-6 w-6 mr-3" />
                Continue Campaign
              </Button>
            ) : (
              <Button
                onClick={handleNewCampaign}
                className="w-full bg-gradient-to-r from-amber-700 to-orange-700 hover:from-amber-600 hover:to-orange-600 text-black font-bold text-xl py-8 shadow-lg shadow-amber-600/50 border-2 border-amber-400/50"
                size="lg"
              >
                <PlusCircle className="h-6 w-6 mr-3" />
                New Campaign
              </Button>
            )}

            {hasSavedCampaign && (
              <Button
                onClick={handleNewCampaign}
                variant="outline"
                className="w-full border-red-600/50 text-red-400 hover:bg-red-600/20 font-semibold py-6"
                size="lg"
              >
                <Trash2 className="h-5 w-5 mr-2" />
                Start New Campaign (Delete Current)
              </Button>
            )}
            
            {/* Load Last Campaign Button */}
            <Button
              onClick={handleLoadLastCampaign}
              disabled={isLoadingCampaign}
              variant="outline"
              className="w-full border-blue-600/50 text-blue-400 hover:bg-blue-600/20 font-semibold py-4 disabled:opacity-50 disabled:cursor-not-allowed"
              size="sm"
            >
              {isLoadingCampaign ? (
                <>
                  <div className="animate-spin h-4 w-4 mr-2 border-2 border-blue-400 border-t-transparent rounded-full"></div>
                  Loading...
                </>
              ) : (
                <>
                  <Database className="h-4 w-4 mr-2" />
                  🧪 Load Last Campaign from DB
                </>
              )}
            </Button>
          </div>

          {/* Confirm Delete Dialog */}
          {showConfirmDelete && (
            <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
              <Card className="max-w-md w-full bg-gray-900 border-red-600/50">
                <CardHeader>
                  <CardTitle className="text-red-400 flex items-center gap-2">
                    <Trash2 className="h-6 w-6" />
                    Delete Current Campaign?
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-gray-300">
                    Are you sure you want to delete your current campaign with{' '}
                    <span className="font-bold text-white">{savedCharacter?.name}</span>?
                  </p>
                  <p className="text-red-400 text-sm">
                    ⚠️ This action cannot be undone. All progress will be lost.
                  </p>
                  <div className="flex gap-3">
                    <Button
                      onClick={handleConfirmNewCampaign}
                      className="flex-1 bg-red-700 hover:bg-red-600 text-white"
                    >
                      Yes, Delete
                    </Button>
                    <Button
                      onClick={() => setShowConfirmDelete(false)}
                      variant="outline"
                      className="flex-1 border-gray-600 text-gray-300"
                    >
                      Cancel
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Info */}
          <div className="text-center text-gray-500 text-sm space-y-2 pt-6 border-t border-gray-700">
            <p>✨ Create your character and embark on an epic adventure</p>
            <p>🎭 AI-powered Dungeon Master guides your story</p>
            <p>🎲 D&D-style mechanics and ability checks</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MainMenu;
