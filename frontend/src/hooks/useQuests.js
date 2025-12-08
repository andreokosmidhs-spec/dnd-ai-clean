import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient, { isSuccess, getErrorMessage } from '../lib/apiClient';

/**
 * Hook to fetch all quests for a campaign
 */
export function useQuests(campaignId, characterId = null, status = null) {
  return useQuery({
    queryKey: ['campaign-quests', campaignId, characterId, status],
    queryFn: async () => {
      const params = { campaign_id: campaignId };
      if (characterId) params.character_id = characterId;
      if (status) params.status = status;
      
      const response = await apiClient.get('/api/campaign/log/quests', { params });
      
      if (isSuccess(response)) {
        return response.data.quests || [];
      }
      
      throw new Error(getErrorMessage(response.error));
    },
    enabled: !!campaignId,
  });
}

/**
 * Hook to fetch a single quest by ID
 */
export function useQuest(campaignId, questId, characterId = null) {
  return useQuery({
    queryKey: ['campaign-quest', campaignId, questId, characterId],
    queryFn: async () => {
      const params = { campaign_id: campaignId };
      if (characterId) params.character_id = characterId;
      
      const response = await apiClient.get(`/api/campaign/log/quests/${questId}`, { params });
      
      if (isSuccess(response)) {
        return response.data;
      }
      
      throw new Error(getErrorMessage(response.error));
    },
    enabled: !!campaignId && !!questId,
  });
}

/**
 * Hook to fetch active quests
 */
export function useActiveQuests(campaignId, characterId = null) {
  return useQuests(campaignId, characterId, 'active');
}

/**
 * Hook to fetch completed quests
 */
export function useCompletedQuests(campaignId, characterId = null) {
  return useQuests(campaignId, characterId, 'completed');
}
