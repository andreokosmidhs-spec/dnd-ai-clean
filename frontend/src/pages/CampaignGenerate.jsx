import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { useSessionCore } from "../store/useSessionCore";

const CampaignGenerate = () => {
  const navigate = useNavigate();
  const { activeCharacterId } = useSessionCore();

  useEffect(() => {
    if (!activeCharacterId) {
      navigate("/", { replace: true });
    }
  }, [activeCharacterId, navigate]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-slate-100">
      <div className="w-full max-w-xl space-y-4 text-center">
        <p className="text-xs uppercase tracking-[0.3em] text-amber-300">Campaign Draft</p>
        <h1 className="text-3xl font-bold text-amber-400">Generating campaign…</h1>
        <p className="text-sm text-slate-300">
          Stand by while we prepare your world. This placeholder screen will update once generation is wired up.
        </p>
        <div className="flex justify-center">
          <Button variant="outline" onClick={() => navigate("/campaign-setup")}>Back</Button>
        </div>
      </div>
    </div>
  );
};

export default CampaignGenerate;
