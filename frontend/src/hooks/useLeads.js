import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient, { isSuccess, getErrorMessage } from '../lib/apiClient';

/**
 * Hook to fetch all leads for a campaign
 */
export function useLeads(campaignId, characterId = null, status = null) {
  return useQuery({
    queryKey: ['campaign-leads', 'all', campaignId, characterId, status],
    queryFn: async () => {
      const params = { campaign_id: campaignId };
      if (characterId) params.character_id = characterId;
      if (status) params.status = status;
      
      const response = await apiClient.get('/api/campaign/log/leads', { params });
      
      if (isSuccess(response)) {
        return response.data.leads || [];
      }
      
      throw new Error(getErrorMessage(response.error));
    },
    enabled: !!campaignId,
  });
}

/**
 * Hook to fetch open leads (not resolved/abandoned)
 */
export function useOpenLeads(campaignId, characterId = null, includeAbandoned = false) {
  return useQuery({
    queryKey: ['campaign-leads', 'open', campaignId, characterId, includeAbandoned],
    queryFn: async () => {
      const params = { 
        campaign_id: campaignId,
        include_abandoned: includeAbandoned
      };
      if (characterId) params.character_id = characterId;
      
      const response = await apiClient.get('/api/campaign/log/leads/open', { params });
      
      if (isSuccess(response)) {
        return response.data.leads || [];
      }
      
      throw new Error(getErrorMessage(response.error));
    },
    enabled: !!campaignId,
  });
}

/**
 * Hook to fetch a single lead by ID
 */
export function useLead(campaignId, leadId, characterId = null) {
  return useQuery({
    queryKey: ['campaign-leads', 'detail', campaignId, leadId, characterId],
    queryFn: async () => {
      const params = { campaign_id: campaignId };
      if (characterId) params.character_id = characterId;
      
      const response = await apiClient.get(`/api/campaign/log/leads/${leadId}`, { params });
      
      if (isSuccess(response)) {
        return response.data;
      }
      
      throw new Error(getErrorMessage(response.error));
    },
    enabled: !!campaignId && !!leadId,
  });
}

/**
 * Hook to update lead status
 */
export function useUpdateLeadStatus() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ campaignId, leadId, newStatus, characterId = null, playerNotes = null }) => {
      const params = { 
        campaign_id: campaignId,
        new_status: newStatus
      };
      if (characterId) params.character_id = characterId;
      if (playerNotes) params.player_notes = playerNotes;
      
      const response = await apiClient.patch(
        `/api/campaign/log/leads/${leadId}/status`,
        null,
        { params }
      );
      
      if (isSuccess(response)) {
        return response.data;
      }
      
      throw new Error(getErrorMessage(response.error));
    },
    onSuccess: () => {
      // Invalidate all lead queries to refetch updated data
      queryClient.invalidateQueries({ queryKey: ['campaign-leads'] });
    },
  });
}
