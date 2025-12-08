/**
 * SessionManager - Single Source of Truth for Session Data
 * 
 * CRITICAL: This is the ONLY place that should write to core session localStorage keys.
 * All other components should use these methods instead of direct localStorage access.
 * 
 * Prevents:
 * - Race conditions from multiple components writing same keys
 * - Data overwrites
 * - Inconsistent state
 */

import { KEYS, storage } from '../lib/localStorageKeys';

class SessionManager {
  constructor() {
    this.debug = true; // Set to false in production
  }

  log(message, ...args) {
    if (this.debug) {
      console.log(`[SessionManager] ${message}`, ...args);
    }
  }

  warn(message, ...args) {
    console.warn(`[SessionManager] ⚠️ ${message}`, ...args);
  }

  // ═══════════════════════════════════════════════════════════════════
  // SESSION ID MANAGEMENT
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Get current session ID
   * @returns {string|null}
   */
  getSessionId() {
    return storage.get(KEYS.SESSION_ID);
  }

  /**
   * Set session ID (should only be called once per session)
   * @param {string} sessionId
   */
  setSessionId(sessionId) {
    const existing = this.getSessionId();
    if (existing && existing !== sessionId) {
      this.warn(`Overwriting existing sessionId "${existing}" with "${sessionId}"`);
    }
    
    storage.set(KEYS.SESSION_ID, sessionId);
    this.log(`Session ID set: ${sessionId}`);
  }

  /**
   * Create new session ID
   * @param {string} campaignId - Optional campaign ID to include
   * @returns {string}
   */
  createNewSessionId(campaignId = null) {
    const sessionId = campaignId 
      ? `sess-${campaignId}` 
      : `sess-${Date.now()}`;
    
    this.setSessionId(sessionId);
    return sessionId;
  }

  /**
   * Clear session ID
   */
  clearSessionId() {
    storage.remove(KEYS.SESSION_ID);
    this.log('Session ID cleared');
  }

  // ═══════════════════════════════════════════════════════════════════
  // CAMPAIGN ID MANAGEMENT
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Get current campaign ID
   * @returns {string|null}
   */
  getCampaignId() {
    return storage.get(KEYS.CAMPAIGN_ID);
  }

  /**
   * Set campaign ID
   * @param {string} campaignId
   */
  setCampaignId(campaignId) {
    storage.set(KEYS.CAMPAIGN_ID, campaignId);
    this.log(`Campaign ID set: ${campaignId}`);
  }

  /**
   * Clear campaign ID
   */
  clearCampaignId() {
    storage.remove(KEYS.CAMPAIGN_ID);
    this.log('Campaign ID cleared');
  }

  // ═══════════════════════════════════════════════════════════════════
  // INTRO STATE MANAGEMENT
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Check if intro has been played (global flag)
   * @returns {boolean}
   */
  isIntroPlayed() {
    return storage.get(KEYS.INTRO_PLAYED) === '1';
  }

  /**
   * Mark intro as played (global flag)
   */
  markIntroPlayed() {
    storage.set(KEYS.INTRO_PLAYED, '1');
    this.log('Intro marked as played (global)');
  }

  /**
   * Check if intro has been played for specific session
   * @param {string} sessionId
   * @returns {boolean}
   */
  isIntroPlayedForSession(sessionId) {
    return storage.get(KEYS.INTRO_PLAYED_SESSION(sessionId)) === 'true';
  }

  /**
   * Mark intro as played for specific session
   * @param {string} sessionId
   */
  markIntroPlayedForSession(sessionId) {
    storage.set(KEYS.INTRO_PLAYED_SESSION(sessionId), 'true');
    this.log(`Intro marked as played for session: ${sessionId}`);
  }

  /**
   * Reset intro state
   */
  resetIntroState() {
    storage.remove(KEYS.INTRO_PLAYED);
    this.log('Intro state reset');
  }

  // ═══════════════════════════════════════════════════════════════════
  // DM LOG MESSAGES MANAGEMENT
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Get DM log messages for session
   * @param {string} sessionId
   * @returns {Array}
   */
  getDMLogMessages(sessionId) {
    if (!sessionId) {
      this.warn('getDMLogMessages called without sessionId');
      return [];
    }
    return storage.get(KEYS.DM_LOG_MESSAGES(sessionId), []);
  }

  /**
   * Save DM log messages for session
   * CRITICAL: This should be the ONLY place that writes to dm-log-messages
   * @param {string} sessionId
   * @param {Array} messages
   * @param {Object} options - { skipTrim: boolean, source: string }
   */
  saveDMLogMessages(sessionId, messages, options = {}) {
    if (!sessionId) {
      this.warn('saveDMLogMessages called without sessionId');
      return;
    }

    const { skipTrim = false, source = 'unknown' } = options;
    
    // Trim to last 200 messages to prevent localStorage overflow
    const messagesToSave = skipTrim ? messages : messages.slice(-200);
    
    storage.set(KEYS.DM_LOG_MESSAGES(sessionId), messagesToSave);
    this.log(`Saved ${messagesToSave.length} messages for session ${sessionId} (source: ${source})`);

    // Warn if we're saving a lot of messages
    if (messagesToSave.length > 150) {
      this.warn(`Large message count (${messagesToSave.length}) - consider cleanup`);
    }
  }

  /**
   * Append message to DM log (safer than overwriting entire array)
   * @param {string} sessionId
   * @param {Object} message
   */
  appendDMLogMessage(sessionId, message) {
    const existing = this.getDMLogMessages(sessionId);
    const updated = [...existing, message];
    this.saveDMLogMessages(sessionId, updated, { source: 'append' });
  }

  /**
   * Clear DM log messages for session
   * @param {string} sessionId
   */
  clearDMLogMessages(sessionId) {
    if (!sessionId) return;
    storage.remove(KEYS.DM_LOG_MESSAGES(sessionId));
    this.log(`Cleared DM log messages for session: ${sessionId}`);
  }

  /**
   * Get DM log options for session
   * @param {string} sessionId
   * @returns {Array}
   */
  getDMLogOptions(sessionId) {
    if (!sessionId) return [];
    return storage.get(KEYS.DM_LOG_OPTIONS(sessionId), []);
  }

  /**
   * Save DM log options for session
   * @param {string} sessionId
   * @param {Array} options
   */
  saveDMLogOptions(sessionId, options) {
    if (!sessionId) return;
    storage.set(KEYS.DM_LOG_OPTIONS(sessionId), options);
    this.log(`Saved ${options.length} options for session: ${sessionId}`);
  }

  // ═══════════════════════════════════════════════════════════════════
  // GAME STATE MANAGEMENT (Legacy keys)
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Get legacy campaign gamestate
   * @returns {Object|null}
   */
  getLegacyCampaignGamestate() {
    return storage.get(KEYS.CAMPAIGN_GAMESTATE);
  }

  /**
   * Save legacy campaign gamestate
   * @param {Object} gamestate
   */
  saveLegacyCampaignGamestate(gamestate) {
    storage.set(KEYS.CAMPAIGN_GAMESTATE, gamestate);
    this.log('Saved legacy campaign gamestate');
  }

  /**
   * Get legacy campaign character
   * @returns {Object|null}
   */
  getLegacyCampaignCharacter() {
    return storage.get(KEYS.CAMPAIGN_CHARACTER);
  }

  /**
   * Save legacy campaign character
   * @param {Object} character
   */
  saveLegacyCampaignCharacter(character) {
    storage.set(KEYS.CAMPAIGN_CHARACTER, character);
    this.log('Saved legacy campaign character');
  }

  // ═══════════════════════════════════════════════════════════════════
  // INTENT MODE MANAGEMENT
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Get current intent mode
   * @returns {string|null}
   */
  getIntentMode() {
    return storage.get(KEYS.DM_INTENT_MODE);
  }

  /**
   * Set intent mode
   * @param {string} mode - 'action', 'say', 'dm-question'
   */
  setIntentMode(mode) {
    storage.set(KEYS.DM_INTENT_MODE, mode);
    this.log(`Intent mode set: ${mode}`);
  }

  /**
   * Clear intent mode
   */
  clearIntentMode() {
    storage.remove(KEYS.DM_INTENT_MODE);
    this.log('Intent mode cleared');
  }

  // ═══════════════════════════════════════════════════════════════════
  // SESSION LIFECYCLE
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Initialize a new session
   * @param {Object} options
   * @param {string} options.campaignId
   * @param {Array} options.initialMessages - Initial DM log messages
   * @returns {string} sessionId
   */
  initializeSession({ campaignId, initialMessages = [] }) {
    this.log('Initializing new session...', { campaignId });
    
    // Create session ID
    const sessionId = this.createNewSessionId(campaignId);
    
    // Set campaign ID
    if (campaignId) {
      this.setCampaignId(campaignId);
    }
    
    // Save initial messages if provided
    if (initialMessages.length > 0) {
      this.saveDMLogMessages(sessionId, initialMessages, { 
        skipTrim: true, 
        source: 'initialization' 
      });
    }
    
    // Mark intro as played
    this.markIntroPlayed();
    
    this.log('✅ Session initialized:', sessionId);
    return sessionId;
  }

  /**
   * Clear entire session (use with caution!)
   * @param {string} sessionId
   */
  clearSession(sessionId) {
    this.warn(`Clearing session: ${sessionId}`);
    
    if (sessionId) {
      this.clearDMLogMessages(sessionId);
      storage.remove(KEYS.DM_LOG_OPTIONS(sessionId));
      storage.remove(KEYS.INTRO_PLAYED_SESSION(sessionId));
    }
    
    this.clearSessionId();
    this.clearCampaignId();
    this.resetIntroState();
    this.clearIntentMode();
    
    this.log('✅ Session cleared');
  }

  /**
   * Get session summary (for debugging)
   * @returns {Object}
   */
  getSessionSummary() {
    const sessionId = this.getSessionId();
    const campaignId = this.getCampaignId();
    const introPlayed = this.isIntroPlayed();
    const messages = sessionId ? this.getDMLogMessages(sessionId) : [];
    const intentMode = this.getIntentMode();
    
    return {
      sessionId,
      campaignId,
      introPlayed,
      messageCount: messages.length,
      intentMode,
      hasMessages: messages.length > 0
    };
  }
}

// Export singleton instance
const sessionManager = new SessionManager();
export default sessionManager;
