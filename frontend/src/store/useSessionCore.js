import { create } from "zustand";
import { persist } from "zustand/middleware";

const initialState = {
  activeCharacterId: null,
  activeCampaignId: null,
  campaignStatus: "none",
  lastUpdatedAt: null,
};

export const useSessionCore = create(
  persist(
    (set) => ({
      ...initialState,
      setSession: (partial) =>
        set(() => ({
          ...initialState,
          ...partial,
          lastUpdatedAt: new Date().toISOString(),
        })),
      updateSession: (partial) =>
        set((state) => ({
          ...state,
          ...partial,
          lastUpdatedAt: new Date().toISOString(),
        })),
      resetSession: () => set(() => initialState),
    }),
    {
      name: "session-core",
      partialize: (state) => ({
        activeCharacterId: state.activeCharacterId,
        activeCampaignId: state.activeCampaignId,
        campaignStatus: state.campaignStatus,
        lastUpdatedAt: state.lastUpdatedAt,
      }),
    }
  )
);
