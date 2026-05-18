import CharacterCreationV2 from './pages/CharacterCreationV2';
import CharactersList from './pages/CharactersList';
import CharacterPreview from './pages/CharacterPreview';
import CharacterEdit from './pages/CharacterEdit';
import MainMenu from "./components/MainMenu";
import { useEffect } from "react";
import "./App.css";
import "./styles/chat-fixes.css";
import "./styles/focus-first.css";
import { HashRouter as BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import axios from "axios";
import RPGGame from "./components/RPGGame";
import Toast from "./components/Toast";
import FeedbackButton from "./components/FeedbackButton";
import { GameStateProvider } from "./contexts/GameStateContext";
import { FontSizeProvider } from "./contexts/FontSizeContext";
import { useDungeonStore } from "./store/useDungeonStore";
import { useSessionCore } from "./store/useSessionCore";
import CampaignSetup from "./pages/CampaignSetup";
import CampaignGenerate from "./pages/CampaignGenerate";
import DevCampaignLogPreview from "./pages/DevCampaignLogPreview";
import PressureDashboard from "./pages/PressureDashboard";
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

const AdventureRoute = () => {
  const navigate = useNavigate();
  const { activeCharacterId, activeCampaignId, campaignStatus } = useSessionCore();

  useEffect(() => {
    if (!activeCharacterId || !activeCampaignId) {
      navigate("/", { replace: true });
      return;
    }

    if (campaignStatus !== "ready") {
      navigate("/", { replace: true });
    }
  }, [activeCampaignId, activeCharacterId, campaignStatus, navigate]);

  if (!activeCharacterId || !activeCampaignId || campaignStatus !== "ready") {
    return null;
  }

  return <Home />;
};

const PressureRoute = () => {
  const { activeCampaignId } = useSessionCore();
  if (!activeCampaignId) return <div style={{ color: "#94a3b8", padding: 40 }}>No active campaign.</div>;
  return <PressureDashboard campaignId={activeCampaignId} />;
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
      <FontSizeProvider>
        <GameStateProvider>
          <BrowserRouter>
            <Routes>
              {/* Root now lands on the legacy Main Menu (RPGGame entry) */}
              <Route path="/" element={<MainMenuPage />} />

              {/* New Character Creation V2 Wizard */}
              <Route path="/character-v2" element={<CharacterCreationV2 />} />

              {/* Load existing V2 characters */}
              <Route path="/characters" element={<CharactersList />} />
              <Route path="/characters/:characterId" element={<CharacterPreview />} />
              <Route path="/characters/:characterId/edit" element={<CharacterEdit />} />

              {/* Campaign setup and draft generation placeholder */}
              <Route path="/campaign-setup" element={<CampaignSetup />} />
              <Route path="/campaign-generate" element={<CampaignGenerate />} />

              {/* Legacy CharacterCreation component is retained in the repo but no longer routed; V2 is canonical. */}

              {/* Old game/adventure flow (keep for existing campaigns) */}
              <Route path="/adventure" element={<AdventureRoute />} />
              <Route path="/game" element={<AdventureRoute />} />

              {/* DEV ONLY: Preview CampaignLogPanel without adventure flow */}
              {/* TODO: Remove before production release */}
              <Route path="/dev/campaign-log" element={<DevCampaignLogPreview />} />

              {/* DM Tool: Living Campaign Pressure Engine dashboard */}
              <Route path="/pressure-dashboard" element={<PressureRoute />} />
            </Routes>
            <FeedbackButton />
          </BrowserRouter>
          <Toast />
        </GameStateProvider>
      </FontSizeProvider>
    </div>
  );
}

export default App;
