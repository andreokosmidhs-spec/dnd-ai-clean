import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { useSessionCore } from "../store/useSessionCore";

const CATEGORY_CONFIG = [
  {
    key: "tone",
    title: "Tone",
    description: "Shape the mood of your campaign world.",
    options: [
      { value: "Grim", title: "Grim", description: "Dark stakes, hard choices, and harsh consequences." },
      { value: "Balanced", title: "Balanced", description: "Moments of levity balanced with danger and grit." },
      { value: "Heroic", title: "Heroic", description: "Bright optimism, daring heroics, and bold victories." },
    ],
  },
  {
    key: "focus",
    title: "Focus",
    description: "What drives the adventure moment to moment?",
    options: [
      { value: "Story", title: "Story", description: "Narrative arcs, character bonds, and dramatic reveals." },
      { value: "Combat", title: "Combat", description: "Tactical battles, enemy variety, and clever maneuvers." },
      { value: "Intrigue", title: "Intrigue", description: "Politics, secrets, and social manipulation." },
      { value: "Exploration", title: "Exploration", description: "Discovery, travel, and uncovering the unknown." },
    ],
  },
  {
    key: "scope",
    title: "Starting Scope",
    description: "Where does the party begin?",
    options: [
      { value: "City", title: "City", description: "Bustling streets, factions, and urban intrigue." },
      { value: "Wilderness", title: "Wilderness", description: "Roadside dangers, wandering monsters, and open skies." },
      { value: "Dungeon", title: "Dungeon", description: "Claustrophobic corridors and ancient traps." },
      { value: "Mixed", title: "Mixed", description: "A blend of urban hubs and the wilds between." },
    ],
  },
  {
    key: "danger",
    title: "Danger",
    description: "How lethal is the journey?",
    options: [
      { value: "Low", title: "Low", description: "Safer encounters with room to breathe." },
      { value: "Medium", title: "Medium", description: "Balanced peril with fair warning." },
      { value: "High", title: "High", description: "Deadly threats and sharp consequences." },
    ],
  },
];

const DEFAULT_INTENT = {
  tone: "Balanced",
  focus: "Story",
  scope: "City",
  danger: "Medium",
};

const CampaignSetup = () => {
  const navigate = useNavigate();
  const { activeCharacterId, campaignIntent, updateSession } = useSessionCore();
  const [selections, setSelections] = useState(() => ({
    ...DEFAULT_INTENT,
    ...campaignIntent,
  }));

  useEffect(() => {
    if (!activeCharacterId) {
      navigate("/", { replace: true });
    }
  }, [activeCharacterId, navigate]);

  useEffect(() => {
    if (!campaignIntent) return;
    const next = { ...DEFAULT_INTENT, ...campaignIntent };
    setSelections((prev) => {
      const changed = Object.keys(next).some((key) => prev[key] !== next[key]);
      return changed ? next : prev;
    });
  }, [campaignIntent]);

  const hasAllSelections = useMemo(
    () => selections.tone && selections.focus && selections.scope && selections.danger,
    [selections]
  );

  const handleSelect = (key, value) => {
    const updated = { ...selections, [key]: value };
    setSelections(updated);
    updateSession({
      campaignIntent: {
        ...updated,
        updatedAt: new Date().toISOString(),
      },
    });
  };

  const handleGenerate = () => {
    if (!hasAllSelections) return;
    const intentPayload = {
      ...selections,
      updatedAt: new Date().toISOString(),
    };
    updateSession({
      campaignIntent: intentPayload,
      campaignStatus: "draft",
      activeCampaignId: null,
    });
    navigate("/campaign-generate");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 px-4 py-10">
      <div className="mx-auto max-w-5xl space-y-8">
        <header className="space-y-2 text-center">
          <p className="text-xs uppercase tracking-[0.3em] text-amber-300">Campaign Setup</p>
          <h1 className="text-3xl font-bold text-amber-400">Define your world intent</h1>
          <p className="text-sm text-slate-300">
            Choose the guiding tone and focus for your next campaign. You can adjust these again before finalizing.
          </p>
        </header>

        <div className="grid gap-6">
          {CATEGORY_CONFIG.map((category) => (
            <Card key={category.key} className="border-slate-800 bg-slate-900/70">
              <CardHeader>
                <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
                  <div>
                    <CardTitle className="text-xl text-amber-300">{category.title}</CardTitle>
                    <CardDescription className="text-slate-300">
                      {category.description}
                    </CardDescription>
                  </div>
                  <p className="text-xs text-slate-400">Select one</p>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  {category.options.map((option) => {
                    const isSelected = selections[category.key] === option.value;
                    return (
                      <button
                        type="button"
                        key={option.value}
                        onClick={() => handleSelect(category.key, option.value)}
                        className={`group h-full rounded-xl border p-4 text-left transition focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-1 focus:ring-offset-slate-950 ${
                          isSelected
                            ? "border-amber-400 bg-amber-400/10 shadow-[0_0_0_1px_rgba(251,191,36,0.3)]"
                            : "border-slate-800 bg-slate-900/70 hover:border-amber-400/60 hover:bg-slate-900"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-lg font-semibold text-slate-100">{option.title}</span>
                          {isSelected && <span className="text-xs font-semibold text-amber-300">Selected</span>}
                        </div>
                        <p className="mt-2 text-sm text-slate-300">{option.description}</p>
                      </button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="flex justify-end">
          <Button
            onClick={handleGenerate}
            disabled={!hasAllSelections}
            className="bg-amber-500 text-slate-950 hover:bg-amber-400"
          >
            Generate Campaign
          </Button>
        </div>
      </div>
    </div>
  );
};

export default CampaignSetup;
