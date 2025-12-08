import { useDungeonStore } from "../store/useDungeonStore";
import { useSyncExternalStore } from "react";

// SESSION

export const useSessionInfo = () =>
  useDungeonStore((s) => s.session);

export const useSessionIds = () =>
  useDungeonStore((s) => ({
    sessionId: s.session.sessionId,
    campaignId: s.session.campaignId,
  }));

// UI

export const useUIState = () =>
  useDungeonStore((s) => s.ui);

export const useActiveView = () =>
  useDungeonStore((s) => s.ui.activeView);

export const useIsAnyLoading = () =>
  useDungeonStore((s) =>
    s.ui.isLoadingWorld ||
    s.ui.isLoadingCharacter ||
    s.ui.isLoadingAction ||
    s.ui.isLoadingTTS
  );

export const useDefeatModal = () =>
  useDungeonStore((s) => ({
    showDefeatModal: s.ui.showDefeatModal,
    defeatReason: s.ui.defeatReason,
  }));

// CHARACTER

export const useCharacter = () =>
  useDungeonStore((s) => s.character);

export const useCharacterSummary = () =>
  useDungeonStore((s) => {
    const c = s.character;
    if (!c) return null;
    return {
      name: c.name,
      race: c.race,
      class: c.class,
      level: c.level,
      hp: c.hp,
      ac: c.ac,
    };
  });

export const useCharacterXP = () =>
  useDungeonStore((s) => ({
    current_xp: s.character?.current_xp ?? 0,
    xp_to_next: s.character?.xp_to_next ?? 1,
    xpProgress: s.derived.xpProgress,
  }));

// WORLD

export const useWorld = () =>
  useDungeonStore((s) => s.world);

export const useCurrentLocation = () =>
  useDungeonStore((s) => s.world.state?.current_location ?? null);

export const useWorldMeta = () =>
  useDungeonStore((s) => s.world.blueprint?.world_core ?? null);

// QUESTS

export const useQuests = () =>
  useDungeonStore((s) => s.quests);

export const useActiveQuests = () =>
  useDungeonStore((s) =>
    s.quests.activeIds.map((id) => s.quests.byId[id]).filter(Boolean)
  );

export const useCompletedQuests = () =>
  useDungeonStore((s) =>
    s.quests.completedIds.map((id) => s.quests.byId[id]).filter(Boolean)
  );

// COMBAT

export const useCombatState = () =>
  useDungeonStore((s) => s.combat);

export const useIsInCombat = () =>
  useDungeonStore((s) => s.derived.isInCombat);

// CHECKS

export const usePendingCheck = () =>
  useDungeonStore((s) => s.checks.pending);

export const useCheckHistory = () =>
  useDungeonStore((s) => s.checks.history);

// MESSAGES - STABLE IMPLEMENTATION

export const useMessages = () => {
  return useSyncExternalStore(
    (callback) => {
      // Subscribe only to message changes
      return useDungeonStore.subscribe(
        (state) => state.messages,
        () => callback()
      );
    },
    () => {
      const state = useDungeonStore.getState();
      return state.messages.allIds.map((id) => state.messages.byId[id]).filter(Boolean);
    },
    () => []
  );
};

export const useLastMessage = () =>
  useDungeonStore((s) => {
    const { allIds, byId } = s.messages;
    if (allIds.length === 0) return null;
    const lastId = allIds[allIds.length - 1];
    return byId[lastId] ?? null;
  });

export const useMessageCount = () =>
  useDungeonStore((s) => s.messages.count);

// AUDIO

export const useAudioState = () =>
  useDungeonStore((s) => s.audio);

// PERSISTENCE / DERIVED

export const usePersistence = () =>
  useDungeonStore((s) => s.persistence);

export const useDerived = () =>
  useDungeonStore((s) => s.derived);

export const useIsGameReady = () =>
  useDungeonStore((s) => s.derived.isGameReady);
