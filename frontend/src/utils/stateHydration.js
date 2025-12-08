export function hydrateFromLegacyStorage() {
  console.log("🔄 Hydrating from legacy localStorage...");

  const hydratedState = {
    version: "1.0.0",
    lastUpdated: new Date().toISOString(),
  };

  try {
    const sessionId = localStorage.getItem("game-state-session-id");
    const campaignId = localStorage.getItem("game-state-campaign-id");
    
    if (sessionId || campaignId) {
      hydratedState.session = {
        sessionId: sessionId || null,
        campaignId: campaignId || null,
        createdAt: null,
        lastSavedAt: null,
      };
      console.log("✅ Loaded session:", { sessionId, campaignId });
    }

    const characterStr = localStorage.getItem("rpg-campaign-character");
    if (characterStr) {
      try {
        const legacyChar = JSON.parse(characterStr);
        hydratedState.character = {
          id: legacyChar.id || "",
          name: legacyChar.name || "",
          race: legacyChar.race || "",
          class: legacyChar.class || "",
          level: legacyChar.level || 1,
          background: legacyChar.background || "",
          backgroundVariant: null,
          alignment: legacyChar.alignment || "",
          aspiration: legacyChar.aspiration || "",
          stats: legacyChar.stats || {
            STR: 10, DEX: 10, CON: 10, INT: 10, WIS: 10, CHA: 10,
          },
          hp: {
            current: legacyChar.hitPoints || 10,
            max: legacyChar.hitPoints || 10,
          },
          ac: 10,
          speed: 30,
          proficiency_bonus: 2,
          attack_bonus: 0,
          current_xp: 0,
          xp_to_next: 150,
          injury_count: 0,
          spell_slots: {},
          prepared_spells: [],
          conditions: [],
          virtues: [],
          flaws: [],
          goals: [],
          proficiencies: [],
          inventory: [],
          gold: 0,
          active_quests: [],
          reputation: {},
          notes: "",
        };
        console.log("✅ Loaded character:", hydratedState.character.name);
      } catch (e) {
        console.error("❌ Failed to parse character:", e);
      }
    }

    const gameStateStr = localStorage.getItem("rpg-campaign-gamestate");
    if (gameStateStr) {
      try {
        const legacyGameState = JSON.parse(gameStateStr);
        
        if (legacyGameState.currentLocation) {
          const loc = legacyGameState.currentLocation;
          hydratedState.world = {
            blueprint: null,
            state: {
              current_location: {
                name: loc.name || "",
                region: loc.region || "",
                description: loc.description || "",
              },
              time_of_day: "midday",
              weather: "clear",
              active_npcs: [],
              faction_states: {},
              quest_flags: {},
              recent_events: [],
            },
          };
        }

        if (legacyGameState.inventory && hydratedState.character) {
          hydratedState.character.inventory = legacyGameState.inventory.map((item, idx) => ({
            id: `item-${idx}`,
            name: item.name || item,
            type: item.type || "item",
            quantity: item.quantity || 1,
          }));
        }

        console.log("✅ Loaded game state");
      } catch (e) {
        console.error("❌ Failed to parse game state:", e);
      }
    }

    if (sessionId) {
      const messagesKey = `dm-log-messages-${sessionId}`;
      const messagesStr = localStorage.getItem(messagesKey);
      if (messagesStr) {
        try {
          const legacyMessages = JSON.parse(messagesStr);
          const byId = {};
          const allIds = [];

          legacyMessages.forEach((msg, idx) => {
            const id = msg.id || `msg-${msg.timestamp || idx}`;
            byId[id] = {
              id,
              type: msg.type || "dm",
              text: msg.text || "",
              timestamp: msg.timestamp || Date.now(),
              isCinematic: msg.isCinematic,
              source: msg.source,
            };
            allIds.push(id);
          });

          hydratedState.messages = {
            byId,
            allIds,
            count: allIds.length,
          };
          console.log(`✅ Loaded ${allIds.length} messages`);
        } catch (e) {
          console.error("❌ Failed to parse messages:", e);
        }
      }
    }

    const dmIntroPlayed = localStorage.getItem("dm-intro-played");
    if (dmIntroPlayed === "1") {
      hydratedState.audio = {
        isTTSEnabled: false,
        currentlyPlaying: null,
        queue: [],
      };
    }

    hydratedState.persistence = {
      hasUnsavedChanges: false,
      lastLocalSaveAt: null,
      lastDBSaveAt: null,
      canSave: !!(hydratedState.session?.campaignId && hydratedState.character),
      canContinue: !!(characterStr && gameStateStr),
      canLoadFromDB: true,
    };

  } catch (error) {
    console.error("❌ Hydration error:", error);
  }

  console.log("✅ Hydration complete:", hydratedState);
  return hydratedState;
}

export function cleanupLegacyStorage() {
  console.log("🧹 Cleaning up legacy localStorage keys...");
  
  const legacyKeys = [
    "dm-session-id",
    "dm-intent-mode",
  ];

  legacyKeys.forEach((key) => {
    if (localStorage.getItem(key)) {
      localStorage.removeItem(key);
      console.log(`🗑️ Removed: ${key}`);
    }
  });
}
