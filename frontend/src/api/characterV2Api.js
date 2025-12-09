// API function for creating V2 characters
import axios from './axiosConfig';

export const createCharacterV2 = async (characterData) => {
  const res = await axios.post('/api/characters_v2/create', characterData);
  return res.data;
};