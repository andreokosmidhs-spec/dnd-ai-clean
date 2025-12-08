import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient, { isSuccess, getErrorMessage } from '../lib/apiClient';

/**
 * Hook to process DM action
 */
export function useProcessAction() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request) => {
      const response = await apiClient.post('/api/rpg_dm/action', request);
      
      if (isSuccess(response)) {
        return response.data;
      }
      
      throw new Error(getErrorMessage(response.error));
    },
    onSuccess: () => {
      // Invalidate world state after action
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });
}
