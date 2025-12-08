import { useEffect } from "react";
import "./App.css";
import "./styles/chat-fixes.css";
import "./styles/focus-first.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import RPGGame from "./components/RPGGame";
import Toast from "./components/Toast";
import { GameStateProvider } from "./contexts/GameStateContext";
import { useDungeonStore } from "./store/useDungeonStore";
import { hydrateFromLegacyStorage, cleanupLegacyStorage } from "./utils/stateHydration";
import "./devStoreDebug"; // Dev-only: expose store in console

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = () => {
  const helloWorldApi = async () => {
    try {
      const response = await axios.get(`${API}/`);
      console.log(response.data.message);
    } catch (e) {
      console.error(e, `errored out requesting / api`);
    }
  };

  useEffect(() => {
    helloWorldApi();
  }, []);

  return <RPGGame />;
};

function App() {
  // Hydrate Zustand store from legacy localStorage once on mount
  useEffect(() => {
    console.log("🚀 App mounting - checking for legacy state...");
    const legacy = hydrateFromLegacyStorage();
    
    if (Object.keys(legacy).length > 0) {
      console.log("📦 Found legacy state, hydrating Zustand store...");
      const current = useDungeonStore.getState();
      
      // Merge partial legacy state into current, then push through setGlobalState
      useDungeonStore.getState().setGlobalState({
        ...current,
        ...legacy,
      });
      
      console.log("✅ Zustand store hydrated from legacy localStorage");
      
      // Clean up deprecated keys
      cleanupLegacyStorage();
    } else {
      console.log("ℹ️ No legacy state found, starting fresh");
    }
  }, []);

  return (
    <div className="App">
      <GameStateProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Home />}>
              <Route index element={<Home />} />
            </Route>
          </Routes>
        </BrowserRouter>
        <Toast />
      </GameStateProvider>
    </div>
  );
}

export default App;