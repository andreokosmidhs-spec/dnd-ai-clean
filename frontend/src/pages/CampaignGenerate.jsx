import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { useSessionCore } from "../store/useSessionCore";
import api from "../api/axiosConfig";

const CampaignGenerate = () => {
  const navigate = useNavigate();
  const { activeCharacterId, campaignIntent, updateSession } = useSessionCore();
  const [status, setStatus] = useState("Starting campaign draft…");
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!activeCharacterId) {
      navigate("/", { replace: true });
      return;
    }

    const intentPayload = campaignIntent || {};
    if (!intentPayload.tone || !intentPayload.focus || !intentPayload.scope || !intentPayload.danger) {
      setError("Campaign intent is incomplete. Please return and set it up again.");
      updateSession({ campaignStatus: "none", activeCampaignId: null });
      return;
    }

    const runGeneration = async () => {
      try {
        setStatus("Creating campaign draft…");
        const draftRes = await api.post("/api/campaigns/draft", {
          characterId: activeCharacterId,
          intent: {
            tone: intentPayload.tone,
            focus: intentPayload.focus,
            scope: intentPayload.scope,
            danger: intentPayload.danger,
          },
        });

        const campaignId = draftRes.data.campaignId;
        updateSession({ activeCampaignId: campaignId, campaignStatus: "generating" });

        setStatus("Generating world blueprint…");
        await api.post(`/api/campaigns/${campaignId}/generate-world`);

        setStatus("Loading knowledge deck…");
        await api.get(`/api/campaigns/${campaignId}/log/cards`);

        updateSession({ campaignStatus: "ready", activeCampaignId: campaignId });
        navigate("/adventure", { replace: true });
      } catch (err) {
        console.error("Campaign generation failed", err);
        setError("We couldn't generate your campaign. Please try again.");
        updateSession({ campaignStatus: "none", activeCampaignId: null });
      }
    };

    runGeneration();
  }, [activeCharacterId, campaignIntent, navigate, updateSession]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-slate-100">
      <div className="w-full max-w-xl space-y-4 text-center">
        <p className="text-xs uppercase tracking-[0.3em] text-amber-300">Campaign Draft</p>
        <h1 className="text-3xl font-bold text-amber-400">Generating campaign…</h1>
        {error ? (
          <p className="text-sm text-red-300">{error}</p>
        ) : (
          <p className="text-sm text-slate-300">{status}</p>
        )}
        <div className="flex justify-center">
          <Button variant="outline" onClick={() => navigate("/campaign-setup")}>Back</Button>
        </div>
      </div>
    </div>
  );
};

export default CampaignGenerate;
