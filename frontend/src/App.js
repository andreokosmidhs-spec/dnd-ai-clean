import CharacterCreationV2 from './pages/CharacterCreationV2';
import MainMenu from "./components/MainMenu";
import { useEffect } from "react";
import "./App.css";
import "./styles/chat-fixes.css";
import "./styles/focus-first.css";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
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

const MainMenuPage = () => {
  const navigate = useNavigate();

  const handleNewCampaign = () => {
    navigate("/character-v2");
  };

  const handleContinueCampaign = () => {
    navigate("/game");
  };

  return (
    <MainMenu
      onNewCampaign={handleNewCampaign}
      onContinueCampaign={handleContinueCampaign}
    />
  );
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
<<<<<<< HEAD
            {/* Root redirects to adventure (MainMenu → Character Creation V2 flow) */}
            <Route path="/" element={<Navigate to="/adventure" replace />} />
            
            {/* Standalone Character Creation V2 Wizard (direct access) */}
            <Route path="/character-v2" element={<CharacterCreationV2 />} />
            
            {/* Main game flow: MainMenu → CharacterCreationV2 → Adventure */}
=======
            {/* Root now lands on the legacy Main Menu (RPGGame entry) */}
            <Route path="/" element={<MainMenuPage />} />

            {/* New Character Creation V2 Wizard */}
            <Route path="/character-v2" element={<CharacterCreationV2 />} />

            {/* Legacy CharacterCreation component is retained in the repo but no longer routed; V2 is canonical. */}

            {/* Old game/adventure flow (keep for existing campaigns) */}
>>>>>>> origin/codex/replace-in-memory-store-with-mongodb-persistence
            <Route path="/adventure" element={<Home />} />
            <Route path="/game" element={<Home />} />
          </Routes>
        </BrowserRouter>
        <Toast />
      </GameStateProvider>
    </div>
  );
}

export default App;
