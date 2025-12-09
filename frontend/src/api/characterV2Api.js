import axios from './axiosConfig';

// Create a new character using the V2 schema
export const createCharacterV2 = async (characterData) => {
  const res = await axios.post('/api/characters_v2/create', characterData);
  return res.data;
};

// Get all V2 characters (temporary debug endpoint)
export const getCharactersV2 = async () => {
  const res = await axios.get('/api/characters_v2');
  return res.data;
};
