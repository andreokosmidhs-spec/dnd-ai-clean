import CharacterCreationV2 from './pages/CharacterCreationV2';
import CharactersList from './pages/CharactersList';
import CharacterPreview from './pages/CharacterPreview';
import CharacterEdit from './pages/CharacterEdit';
import MainMenu from "./components/MainMenu";
import Login from "./pages/Login";
import Pricing from "./pages/Pricing";
import BillingSuccess from "./pages/BillingSuccess";
import { useEffect, useState } from "react";
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
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { useDungeonStore } from "./store/useDungeonStore";
import { useSessionCore } from "./store/useSessionCore";
import CampaignSetup from "./pages/CampaignSetup";
import CampaignGenerate from "./pages/CampaignGenerate";
import DevCampaignLogPreview from "./pages/DevCampaignLogPreview";
import PressureDashboard from "./pages/PressureDashboard";
import BehaviorTreePage from "./pages/BehaviorTreePage";
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

// Modal shown when the 402 turn-limit event fires
const TurnLimitModal = () => {
  const [show, setShow] = useState(false);
  const [detail, setDetail] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    const handler = (e) => { setDetail(e.detail || {}); setShow(true); };
    window.addEventListener("dnd:turn_limit", handler);
    return () => window.removeEventListener("dnd:turn_limit", handler);
  }, []);

  if (!show) return null;

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 9999,
    }}>
      <div style={{
        background: "#1e1b4b", border: "1px solid rgba(139,92,246,0.4)",
        borderRadius: 16, padding: "36px 40px", maxWidth: 400, textAlign: "center",
        fontFamily: "'Segoe UI', sans-serif",
      }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>⚔️</div>
        <h2 style={{ color: "#e2d9f3", margin: "0 0 8px", fontSize: 22 }}>
          Turn Limit Reached
        </h2>
        <p style={{ color: "#94a3b8", fontSize: 14, margin: "0 0 8px" }}>
          You've used all {detail.turns_limit} turns on your{" "}
          <strong style={{ color: "#c4b5fd" }}>{detail.plan}</strong> plan this month.
        </p>
        <p style={{ color: "#64748b", fontSize: 13, margin: "0 0 24px" }}>
          Resets {detail.period ? `on the 1st of next month` : "monthly"}.
        </p>
        <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
          <button onClick={() => setShow(false)} style={{
            padding: "10px 20px", background: "transparent",
            border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8,
            color: "#94a3b8", cursor: "pointer", fontSize: 14,
          }}>
            Dismiss
          </button>
          <button onClick={() => { setShow(false); navigate("/pricing"); }} style={{
            padding: "10px 24px", background: "#8b5cf6",
            border: "none", borderRadius: 8,
            color: "#fff", cursor: "pointer", fontSize: 14, fontWeight: 600,
          }}>
            Upgrade Plan
          </button>
        </div>
      </div>
    </div>
  );
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
        <AuthProvider>
          <GameStateProvider>
          <BrowserRouter>
            <TurnLimitModal />
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

              {/* DM Tool: Behavior Tree Editor */}
              <Route path="/behavior-trees" element={<BehaviorTreePage />} />

              {/* Auth & Billing */}
              <Route path="/login" element={<Login />} />
              <Route path="/pricing" element={<Pricing />} />
              <Route path="/billing/success" element={<BillingSuccess />} />
            </Routes>
            <FeedbackButton />
          </BrowserRouter>
          <Toast />
          </GameStateProvider>
        </AuthProvider>
      </FontSizeProvider>
    </div>
  );
}

export default App;
