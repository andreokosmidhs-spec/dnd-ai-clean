import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

class GameService {
  constructor() {
    this.sessionId = null;
    this.characterId = null;
  }

  // Character Management
  async createCharacter(characterData) {
    try {
      const response = await axios.post(`${API}/characters/`, characterData);
      this.characterId = response.data.id;
      return response.data;
    } catch (error) {
      console.error('Error creating character:', error);
      throw error;
    }
  }

  async getCharacter(characterId) {
    try {
      const response = await axios.get(`${API}/characters/${characterId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching character:', error);
      throw error;
    }
  }

  async updateCharacter(characterId, updates) {
    try {
      const response = await axios.put(`${API}/characters/${characterId}`, updates);
      return response.data;
    } catch (error) {
      console.error('Error updating character:', error);
      throw error;
    }
  }

  async makeAbilityCheck(characterId, ability, actionContext, dc = null) {
    try {
      const response = await axios.post(`${API}/characters/${characterId}/ability-check`, {
        ability,
        dc,
        context: { action: actionContext }
      });
      return response.data;
    } catch (error) {
      console.error('Error making ability check:', error);
      throw error;
    }
  }

  async getCharacterStats(characterId) {
    try {
      const response = await axios.get(`${API}/characters/${characterId}/stats`);
      return response.data;
    } catch (error) {
      console.error('Error fetching character stats:', error);
      throw error;
    }
  }

  async levelUpCharacter(characterId) {
    try {
      const response = await axios.post(`${API}/characters/${characterId}/level-up`);
      return response.data;
    } catch (error) {
      console.error('Error leveling up character:', error);
      throw error;
    }
  }

  async restCharacter(characterId, restType = 'short') {
    try {
      const response = await axios.post(`${API}/characters/${characterId}/rest`, null, {
        params: { rest_type: restType }
      });
      return response.data;
    } catch (error) {
      console.error('Error resting character:', error);
      throw error;
    }
  }

  // Game Session Management
  async startGameSession(characterId) {
    try {
      const response = await axios.post(`${API}/game/session/start`, {
        character_id: characterId
      });
      this.sessionId = response.data.session_id;
      this.characterId = characterId;
      return response.data;
    } catch (error) {
      console.error('Error starting game session:', error);
      throw error;
    }
  }

  async processGameAction(action, context = {}) {
    if (!this.sessionId) {
      throw new Error('No active game session');
    }

    try {
      const response = await axios.post(
        `${API}/game/session/${this.sessionId}/action`,
        { action, context }
      );
      return response.data;
    } catch (error) {
      console.error('Error processing game action:', error);
      throw error;
    }
  }

  async getSessionStatus() {
    if (!this.sessionId) {
      throw new Error('No active game session');
    }

    try {
      const response = await axios.get(`${API}/game/session/${this.sessionId}/status`);
      return response.data;
    } catch (error) {
      console.error('Error fetching session status:', error);
      throw error;
    }
  }

  async triggerAbilityCheck(ability, actionContext, dc = null) {
    if (!this.sessionId) {
      throw new Error('No active game session');
    }

    try {
      const response = await axios.post(
        `${API}/game/session/${this.sessionId}/ability-check`,
        { ability, action_context: actionContext, dc }
      );
      return response.data;
    } catch (error) {
      console.error('Error triggering ability check:', error);
      throw error;
    }
  }

  // NPC Management
  async getNPCsByLocation(locationId) {
    try {
      const response = await axios.get(`${API}/npcs/location/${locationId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching NPCs:', error);
      throw error;
    }
  }

  async interactWithNPC(npcId, characterId, interactionType, playerAction, location) {
    try {
      const response = await axios.post(`${API}/npcs/interact`, {
        npc_id: npcId,
        character_id: characterId,
        interaction_type: interactionType,
        player_action: playerAction,
        location
      });
      return response.data;
    } catch (error) {
      console.error('Error interacting with NPC:', error);
      throw error;
    }
  }

  async generateNPCDialogue(npcId, playerMessage, context = {}) {
    try {
      const response = await axios.post(`${API}/npcs/${npcId}/dialogue`, {
        player_message: playerMessage,
        context
      });
      return response.data;
    } catch (error) {
      console.error('Error generating NPC dialogue:', error);
      throw error;
    }
  }

  async getNPCRelationship(npcId, characterId) {
    try {
      const response = await axios.get(`${API}/npcs/${npcId}/relationship/${characterId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching NPC relationship:', error);
      throw error;
    }
  }

  // World Management
  async getAllLocations() {
    try {
      const response = await axios.get(`${API}/world/locations`);
      return response.data;
    } catch (error) {
      console.error('Error fetching locations:', error);
      throw error;
    }
  }

  async getLocation(locationId) {
    try {
      const response = await axios.get(`${API}/world/locations/${locationId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching location:', error);
      throw error;
    }
  }

  async visitLocation(locationId, characterId, action = 'arrive') {
    try {
      const response = await axios.post(
        `${API}/world/locations/${locationId}/visit`,
        { character_id: characterId, action }
      );
      return response.data;
    } catch (error) {
      console.error('Error visiting location:', error);
      throw error;
    }
  }

  async getLocationDescription(locationId, characterPerspective = 'neutral') {
    try {
      const response = await axios.get(
        `${API}/world/locations/${locationId}/description`,
        { params: { character_perspective: characterPerspective } }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching location description:', error);
      throw error;
    }
  }

  async getActiveEvents() {
    try {
      const response = await axios.get(`${API}/world/events/active`);
      return response.data;
    } catch (error) {
      console.error('Error fetching active events:', error);
      throw error;
    }
  }

  async getLocationEvents(locationId) {
    try {
      const response = await axios.get(`${API}/world/events/location/${locationId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching location events:', error);
      throw error;
    }
  }

  async generateDynamicEvent(locationId, context = {}) {
    try {
      const response = await axios.post(
        `${API}/world/locations/${locationId}/generate-event`,
        { context }
      );
      return response.data;
    } catch (error) {
      console.error('Error generating dynamic event:', error);
      throw error;
    }
  }

  async updateCharacterReputation(locationId, characterId, action, reputationChange) {
    try {
      const response = await axios.post(
        `${API}/world/locations/${locationId}/reputation`,
        {
          character_id: characterId,
          action,
          reputation_change: reputationChange
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error updating reputation:', error);
      throw error;
    }
  }

  // Content Generation
  async generateWorldContent(contentType, context = {}) {
    try {
      const response = await axios.post(`${API}/world/generate-content`, {
        content_type: contentType,
        context
      });
      return response.data;
    } catch (error) {
      console.error('Error generating world content:', error);
      throw error;
    }
  }

  // Utility Methods
  setCharacterId(characterId) {
    this.characterId = characterId;
  }

  getCharacterId() {
    return this.characterId;
  }

  getSessionId() {
    return this.sessionId;
  }

  clearSession() {
    this.sessionId = null;
    this.characterId = null;
  }
}

// Create singleton instance
const gameService = new GameService();
export default gameService;