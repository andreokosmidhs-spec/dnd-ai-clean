// Dev-only helper to expose Zustand store in browser console
import { useDungeonStore } from "./store/useDungeonStore";

// Attach zustand store to window in dev for debugging
if (typeof window !== "undefined") {
  window.dungeonStore = useDungeonStore;
  console.log("🧪 dungeonStore attached to window.dungeonStore");
  console.log("   Try: dungeonStore.getState()");
  console.log("   Or:  dungeonStore.getState().messages");
}
