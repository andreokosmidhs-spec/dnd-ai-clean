import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient, { isSuccess, getErrorMessage } from '../lib/apiClient';

/**
 * Hook to create a character
 */
export function useCreateCharacter() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request) => {
      const response = await apiClient.post('/api/characters/create', request);
      
      if (isSuccess(response)) {
        return response.data;
      }
      
      throw new Error(getErrorMessage(response.error));
    },
    onSuccess: () => {
      // Invalidate campaigns (character is part of campaign)
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });
}
