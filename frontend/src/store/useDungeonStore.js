import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

// ----- INITIAL STATE -----

const initialSession = {
  sessionId: null,
  campaignId: null,
  createdAt: null,
  lastSavedAt: null,
};

const initialUI = {
  activeView: "main-menu",
  isLoadingWorld: false,
  isLoadingCharacter: false,
  isLoadingAction: false,
  isLoadingTTS: false,
  showDefeatModal: false,
  defeatReason: null,
  isTTSEnabled: false,
  currentlyPlayingMessageIndex: null,
  inputMessage: "",
  selectedCombatAction: null,
  selectedCombatTarget: null,
  intentMode: "action",
  selectedNpc: null,
  showIntro: false,
  currentOptions: [],
};

const initialWorld = {
  blueprint: null,
  state: null,
};

const initialQuests = {
  byId: {},
  allIds: [],
  activeIds: [],
  completedIds: [],
};

const initialCombat = {
  isActive: false,
  combatId: null,
  participants: [],
  turnOrder: [],
  currentTurnIndex: 0,
  roundNumber: 0,
  outcome: null,
};

const initialChecks = {
  pending: null,
  history: [],
};

const initialMessages = {
  byId: {},
  allIds: [],
  count: 0,
};

const initialAudio = {
  isTTSEnabled: false,
  currentlyPlaying: null,
  queue: [],
};

const initialPersistence = {
  hasUnsavedChanges: false,
  lastLocalSaveAt: null,
  lastDBSaveAt: null,
  canSave: false,
  canContinue: false,
  canLoadFromDB: true,
};

const makeDerived = (base) => {
  const level = base.character?.level ?? 1;
  const currentXP = base.character?.current_xp ?? 0;
  const nextXP = base.character?.xp_to_next ?? 1;
  const xpProgress = nextXP > 0 ? currentXP / nextXP : 0;

  return {
    isGameReady:
      !!base.session.campaignId &&
      !!base.session.sessionId &&
      !!base.character &&
      !!base.world.blueprint,
    isInCombat: base.combat.isActive,
    hasPendingCheck: base.checks.pending != null,
    currentTurnNumber: base.combat.roundNumber,
    characterLevel: level,
    nextLevelXP: nextXP,
    xpProgress,
  };
};

const initialState = {
  version: "1.0.0",
  lastUpdated: null,
  session: initialSession,
  ui: initialUI,
  character: null,
  world: initialWorld,
  quests: initialQuests,
  combat: initialCombat,
  checks: initialChecks,
  messages: initialMessages,
  audio: initialAudio,
  persistence: initialPersistence,
  derived: makeDerived({
    session: initialSession,
    character: null,
    world: initialWorld,
    combat: initialCombat,
    checks: initialChecks,
  }),
};

const withDerived = (state) => ({
  ...state,
  derived: makeDerived({
    session: state.session,
    character: state.character,
    world: state.world,
    combat: state.combat,
    checks: state.checks,
  }),
  lastUpdated: new Date().toISOString(),
});

export const useDungeonStore = create(
  devtools(
    persist(
      immer((set, get) => ({
        ...initialState,

        setGlobalState: (next) => {
          set(() => withDerived(next), false, "global/setGlobalState");
        },

        updateSession: (partial) => {
          set(
            (state) => withDerived({ ...state, session: { ...state.session, ...partial } }),
            false,
            "session/update"
          );
        },

        updateUI: (partial) => {
          set(
            (state) => ({
              ...state,
              ui: { ...state.ui, ...partial },
              lastUpdated: new Date().toISOString(),
            }),
            false,
            "ui/update"
          );
        },

        setCharacter: (char) => {
          set(
            (state) => withDerived({ ...state, character: char }),
            false,
            "character/set"
          );
        },

        updateCharacter: (partial) => {
          set(
            (state) => {
              if (!state.character) return state;
              return withDerived({
                ...state,
                character: { ...state.character, ...partial },
                persistence: {
                  ...state.persistence,
                  hasUnsavedChanges: true,
                },
              });
            },
            false,
            "character/update"
          );
        },

        setWorld: (world) => {
          set(
            (state) => withDerived({ ...state, world }),
            false,
            "world/set"
          );
        },

        updateWorldState: (partial) => {
          set(
            (state) => {
              if (!state.world.state) return state;
              return withDerived({
                ...state,
                world: {
                  ...state.world,
                  state: {
                    ...state.world.state,
                    ...partial,
                  },
                },
              });
            },
            false,
            "world/updateState"
          );
        },

        setQuests: (quests) => {
          set(
            (state) => withDerived({ ...state, quests }),
            false,
            "quests/set"
          );
        },

        updateCombat: (partial) => {
          set(
            (state) =>
              withDerived({
                ...state,
                combat: { ...state.combat, ...partial },
              }),
            false,
            "combat/update"
          );
        },

        setPendingCheck: (pending) => {
          set(
            (state) =>
              withDerived({
                ...state,
                checks: { ...state.checks, pending },
              }),
            false,
            "checks/setPending"
          );
        },

        pushCheckHistory: (entry) => {
          set(
            (state) =>
              withDerived({
                ...state,
                checks: {
                  ...state.checks,
                  history: [...state.checks.history, entry],
                },
              }),
            false,
            "checks/pushHistory"
          );
        },

        addMessage: (msg) => {
          set(
            (state) => {
              const messageExists = state.messages.byId[msg.id];
              
              state.messages.byId[msg.id] = msg;
              
              if (!messageExists) {
                state.messages.allIds.push(msg.id);
                state.messages.count += 1;
              }
              
              if (state.messages.allIds.length > 500) {
                const removed = state.messages.allIds.shift();
                delete state.messages.byId[removed];
                state.messages.count -= 1;
              }
              
              state.persistence.hasUnsavedChanges = true;
              state.lastUpdated = new Date().toISOString();
            },
            false,
            "messages/add"
          );
        },

        updateMessage: (msgId, partial) => {
          set(
            (state) => {
              if (!state.messages.byId[msgId]) return;
              state.messages.byId[msgId] = { ...state.messages.byId[msgId], ...partial };
              state.persistence.hasUnsavedChanges = true;
              state.lastUpdated = new Date().toISOString();
            },
            false,
            "messages/update"
          );
        },

        addMessages: (msgs) => {
          set(
            (state) => {
              const byId = { ...state.messages.byId };
              const allIds = [...state.messages.allIds];

              msgs.forEach((m) => {
                if (!byId[m.id]) {
                  byId[m.id] = m;
                  allIds.push(m.id);
                } else {
                  byId[m.id] = m;
                }
              });

              return {
                ...state,
                messages: {
                  byId,
                  allIds,
                  count: allIds.length,
                },
                persistence: {
                  ...state.persistence,
                  hasUnsavedChanges: true,
                },
                lastUpdated: new Date().toISOString(),
              };
            },
            false,
            "messages/addMany"
          );
        },

        clearMessages: () => {
          set(
            (state) => ({
              ...state,
              messages: initialMessages,
              lastUpdated: new Date().toISOString(),
            }),
            false,
            "messages/clear"
          );
        },

        updateAudio: (partial) => {
          set(
            (state) => ({
              ...state,
              audio: { ...state.audio, ...partial },
              lastUpdated: new Date().toISOString(),
            }),
            false,
            "audio/update"
          );
        },

        updatePersistence: (partial) => {
          set(
            (state) => ({
              ...state,
              persistence: { ...state.persistence, ...partial },
              lastUpdated: new Date().toISOString(),
            }),
            false,
            "persistence/update"
          );
        },

        markDirty: () => {
          set(
            (state) => ({
              ...state,
              persistence: {
                ...state.persistence,
                hasUnsavedChanges: true,
              },
              lastUpdated: new Date().toISOString(),
            }),
            false,
            "persistence/markDirty"
          );
        },

        markSavedToLocal: (isoDate) => {
          set(
            (state) => ({
              ...state,
              persistence: {
                ...state.persistence,
                hasUnsavedChanges: false,
                lastLocalSaveAt: isoDate,
              },
              lastUpdated: isoDate,
            }),
            false,
            "persistence/markSavedLocal"
          );
        },

        markSavedToDB: (isoDate) => {
          set(
            (state) => ({
              ...state,
              persistence: {
                ...state.persistence,
                hasUnsavedChanges: false,
                lastDBSaveAt: isoDate,
              },
              lastUpdated: isoDate,
            }),
            false,
            "persistence/markSavedDB"
          );
        },
      })),
      {
        name: "dungeon-forge-storage",
        partialize: (state) => ({
          version: state.version,
          lastUpdated: state.lastUpdated,
          session: state.session,
          ui: state.ui,
          character: state.character,
          world: state.world,
          quests: state.quests,
          combat: state.combat,
          checks: state.checks,
          messages: state.messages,
          audio: state.audio,
          persistence: state.persistence,
        }),
      }
    )
  )
);
