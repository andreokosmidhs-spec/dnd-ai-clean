const KEYS = {
  SESSION_ID: "session_id",
  CAMPAIGN_ID: "campaign_id",
  INTRO_PLAYED: "intro_played",
  INTRO_PLAYED_SESSION: (sessionId) => `intro_played_${sessionId}`,
  DM_LOG_MESSAGES: (sessionId) => `dm_log_messages_${sessionId}`,
  DM_LOG_OPTIONS: (sessionId) => `dm_log_options_${sessionId}`,
  CAMPAIGN_GAMESTATE: "campaign_gamestate",
  CAMPAIGN_CHARACTER: "campaign_character",
  DM_INTENT_MODE: "dm_intent_mode",
};

const storage = {
  get: (key, defaultValue = null) => {
    if (typeof localStorage === "undefined") return defaultValue;
    const raw = localStorage.getItem(key);
    if (raw == null) return defaultValue;
    try {
      return JSON.parse(raw);
    } catch (err) {
      return raw;
    }
  },
  set: (key, value) => {
    if (typeof localStorage === "undefined") return;
    const storedValue = typeof value === "string" ? value : JSON.stringify(value);
    localStorage.setItem(key, storedValue);
  },
  remove: (key) => {
    if (typeof localStorage === "undefined") return;
    localStorage.removeItem(key);
  },
};

export { KEYS, storage };
