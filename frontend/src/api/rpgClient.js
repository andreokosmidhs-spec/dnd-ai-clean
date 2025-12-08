/**
 * RPG API Client with Request/Response Logging
 * Centralized API calls for world generation, character creation, and campaigns
 */

import apiClient from '../lib/apiClient';

// Enhanced logging wrapper
function logRequest(endpoint, method, data) {
  console.log(`[API REQUEST] ${method} ${endpoint}`, data);
}

function logResponse(endpoint, response) {
  console.log(`[API RESPONSE] ${endpoint}`, response);
}

function logError(endpoint, error) {
  console.error(`[API ERROR] ${endpoint}`, error);
}

/**
 * Generate world blueprint and create campaign
 */
export async function generateWorldBlueprint(payload) {
  const endpoint = '/api/world-blueprint/generate';
  logRequest(endpoint, 'POST', payload);
  
  try {
    const response = await apiClient.post(endpoint, payload);
    logResponse(endpoint, response);
    
    if (response.success && response.data) {
      console.log(`[DB WRITE] Campaign created with ID: ${response.data.campaign_id}`);
      return response.data;
    } else {
      throw new Error(response.error?.message || 'Failed to generate world');
    }
  } catch (error) {
    logError(endpoint, error);
    throw error;
  }
}

/**
 * Create character for a campaign
 */
export async function createCharacter(payload) {
  const endpoint = '/api/characters/create';
  logRequest(endpoint, 'POST', payload);
  
  try {
    const response = await apiClient.post(endpoint, payload);
    logResponse(endpoint, response);
    
    if (response.success && response.data) {
      console.log(`[DB WRITE] Character created with ID: ${response.data.character_id}`);
      return response.data;
    } else {
      throw new Error(response.error?.message || 'Failed to create character');
    }
  } catch (error) {
    logError(endpoint, error);
    throw error;
  }
}

/**
 * Get last campaign from database
 */
export async function getLastCampaign() {
  const endpoint = '/api/campaigns/latest';
  logRequest(endpoint, 'GET', null);
  
  try {
    const response = await apiClient.get(endpoint);
    logResponse(endpoint, response);
    
    if (response.success && response.data) {
      console.log(`[DB READ] Loaded campaign: ${response.data.campaign_id}`);
      return response.data;
    } else {
      throw new Error(response.error?.message || 'Failed to load campaign');
    }
  } catch (error) {
    logError(endpoint, error);
    throw error;
  }
}

/**
 * Process DM action
 */
export async function processAction(payload) {
  const endpoint = '/api/rpg_dm/action';
  logRequest(endpoint, 'POST', payload);
  
  try {
    const response = await apiClient.post(endpoint, payload);
    logResponse(endpoint, response);
    
    if (response.success && response.data) {
      return response.data;
    } else {
      throw new Error(response.error?.message || 'Failed to process action');
    }
  } catch (error) {
    logError(endpoint, error);
    throw error;
  }
}

export default {
  generateWorldBlueprint,
  createCharacter,
  getLastCampaign,
  processAction
};
