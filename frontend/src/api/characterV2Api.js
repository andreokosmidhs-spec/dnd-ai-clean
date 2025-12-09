// API function for creating V2 characters
import apiClient from '../lib/apiClient';

export const createCharacterV2 = async (characterData) => {
  const response = await apiClient.post('/api/characters_v2/create', characterData);
  return response.data;
};