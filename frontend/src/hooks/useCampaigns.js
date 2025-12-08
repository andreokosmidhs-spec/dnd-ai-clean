import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient, { isSuccess, getErrorMessage } from '../lib/apiClient';

/**
 * Hook to fetch latest campaign
 */
export function useLatestCampaign() {
  return useQuery({
    queryKey: ['campaigns', 'latest'],
    queryFn: async () => {
      const response = await apiClient.get('/api/campaigns/latest');
      
      if (isSuccess(response)) {
        return response.data;
      }
      
      throw new Error(getErrorMessage(response.error));
    },
  });
}

/**
 * Hook to generate world blueprint
 */
export function useGenerateWorldBlueprint() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request) => {
      const response = await apiClient.post('/api/world-blueprint/generate', request);
      
      if (isSuccess(response)) {
        return response.data;
      }
      
      throw new Error(getErrorMessage(response.error));
    },
    onSuccess: () => {
      // Invalidate campaigns list
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });
}
