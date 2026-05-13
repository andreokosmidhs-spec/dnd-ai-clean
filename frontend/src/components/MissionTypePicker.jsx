import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import { Sparkles, Loader2, Wand2, Compass } from "lucide-react";
import api from "../api/axiosConfig";

/**
 * MissionTypePicker
 *
 * Lets the player pick a mission blueprint (Heist / Rescue / Assassination /
 * Political Intrigue / custom) that will shape every storyline in the
 * campaign.
 *
 * Props:
 *   value:      { id?: string, slug?: string } | null
 *   onChange:   ({ id, slug, name }) => void
 *   campaignId: string | null   // when present, custom drafts are saved
 *                                // owned by this campaign
 */
const MissionTypePicker = ({ value, onChange, campaignId = null }) => {
  const [types, setTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [prompt, setPrompt] = useState("");
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState(null);
  const promptRef = useRef(null);

  const fetchTypes = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const url = campaignId
        ? `/api/mission-types?campaign_id=${encodeURIComponent(campaignId)}`
        : "/api/mission-types";
      const res = await api.get(url);
      setTypes(res.data?.mission_types || []);
    } catch (err) {
      console.error("Failed to load mission types", err);
      setError("Couldn't load mission types. Please retry.");
    } finally {
      setLoading(false);
    }
  }, [campaignId]);

  useEffect(() => {
    fetchTypes();
  }, [fetchTypes]);

  const selected = useMemo(() => {
    if (!value) return null;
    return (
      types.find((t) =>
        (value.id && t.id === value.id) ||
        (value.slug && t.slug === value.slug)
      ) || null
    );
  }, [value, types]);

  const handleSelect = (type) => {
    onChange({ id: type.id, slug: type.slug, name: type.name, icon: type.icon });
  };

  const handleGenerate = async () => {
    const text = (prompt || "").trim();
    if (!text || generating) return;
    setGenerating(true);
    setGenerateError(null);
    try {
      const res = await api.post("/api/mission-types/from-prompt", {
        prompt: text,
        campaign_id: campaignId || undefined,
        auto_save: true,
      });
      const saved = res.data?.saved;
      if (!saved || !saved.id) {
        // Backend returned a draft but couldn't save (likely no campaign_id and
        // user isn't system admin). Surface a friendly error.
        setGenerateError(
          "Custom missions can only be saved once a campaign exists. Try picking a default first or proceed — a campaign will be created."
        );
        return;
      }
      setPrompt("");
      // Refresh list & auto-select the new one.
      await fetchTypes();
      onChange({ id: saved.id, slug: saved.slug, name: saved.name, icon: saved.icon });
    } catch (err) {
      console.error("Mission type generation failed", err);
      setGenerateError("The generator stumbled. Try a clearer description (e.g. 'a heist on a moving sky-train').");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Card
      className="border-slate-800 bg-slate-900/70"
      data-testid="mission-type-picker"
    >
      <CardHeader>
        <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
          <div>
            <CardTitle className="text-xl text-amber-300 flex items-center gap-2">
              <Compass className="h-5 w-5" />
              Mission Type
            </CardTitle>
            <CardDescription className="text-slate-300">
              Shape every storyline around a structured arc — or prompt your own.
            </CardDescription>
          </div>
          <p className="text-xs text-slate-400">Optional · pick one</p>
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        {/* Default mission types */}
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading mission blueprints…
          </div>
        ) : error ? (
          <div className="text-sm text-red-300 flex items-center gap-2">
            <span>{error}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchTypes}
              data-testid="mission-type-retry-btn"
            >
              Retry
            </Button>
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {/* "No structure" option */}
            <button
              type="button"
              onClick={() => onChange(null)}
              data-testid="mission-type-option-none"
              className={`group h-full rounded-xl border p-4 text-left transition focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-1 focus:ring-offset-slate-950 ${
                !selected
                  ? "border-amber-400 bg-amber-400/10 shadow-[0_0_0_1px_rgba(251,191,36,0.3)]"
                  : "border-slate-800 bg-slate-900/70 hover:border-amber-400/60 hover:bg-slate-900"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-lg font-semibold text-slate-100">
                  <span className="mr-2">🎲</span>Freeform
                </span>
                {!selected && (
                  <span className="text-xs font-semibold text-amber-300">Selected</span>
                )}
              </div>
              <p className="mt-2 text-sm text-slate-300">
                Let the DM craft storylines without a fixed arc. Best for open sandbox play.
              </p>
            </button>

            {types.map((type) => {
              const isSelected = selected?.id === type.id || selected?.slug === type.slug;
              const phaseNames = (type.phases || []).map((p) => p.name);
              return (
                <button
                  type="button"
                  key={type.id || type.slug}
                  onClick={() => handleSelect(type)}
                  data-testid={`mission-type-option-${type.slug}`}
                  className={`group h-full rounded-xl border p-4 text-left transition focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-1 focus:ring-offset-slate-950 ${
                    isSelected
                      ? "border-amber-400 bg-amber-400/10 shadow-[0_0_0_1px_rgba(251,191,36,0.3)]"
                      : "border-slate-800 bg-slate-900/70 hover:border-amber-400/60 hover:bg-slate-900"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-lg font-semibold text-slate-100">
                      <span className="mr-2">{type.icon}</span>
                      {type.name}
                    </span>
                    {isSelected && (
                      <span className="text-xs font-semibold text-amber-300">Selected</span>
                    )}
                    {!isSelected && !type.is_system && (
                      <Badge variant="outline" className="text-[10px] text-purple-300 border-purple-500/40">
                        Custom
                      </Badge>
                    )}
                  </div>
                  <p className="mt-2 text-sm text-slate-300 line-clamp-3">
                    {type.description || "—"}
                  </p>
                  {phaseNames.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {phaseNames.map((name, i) => (
                        <span
                          key={`${type.id}-phase-${i}`}
                          className="text-[10px] font-medium uppercase tracking-wider text-amber-200/80 bg-amber-500/10 border border-amber-500/30 rounded px-1.5 py-0.5"
                        >
                          {i + 1}. {name}
                        </span>
                      ))}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {/* Prompt-to-generate custom mission type */}
        <div className="rounded-xl border border-purple-500/30 bg-purple-500/5 p-4 space-y-3">
          <div className="flex items-center gap-2 text-purple-200">
            <Wand2 className="h-4 w-4" />
            <p className="text-sm font-semibold">Or prompt a custom mission type</p>
          </div>
          <p className="text-xs text-slate-400">
            Describe the arc in your own words — e.g. <em>"smuggle a refugee priest across a sealed border"</em>{" "}
            or <em>"win a forbidden duel without dishonouring your house"</em>.
          </p>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input
              ref={promptRef}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleGenerate();
                }
              }}
              placeholder="Describe a mission type…"
              className="bg-slate-950/80 border-slate-700 text-slate-100 placeholder:text-slate-500"
              data-testid="mission-type-prompt-input"
              disabled={generating}
            />
            <Button
              type="button"
              onClick={handleGenerate}
              disabled={generating || !prompt.trim()}
              className="bg-purple-500 hover:bg-purple-400 text-slate-950 font-semibold"
              data-testid="mission-type-generate-btn"
            >
              {generating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
                  Crafting…
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-1.5" />
                  Generate
                </>
              )}
            </Button>
          </div>
          {generateError && (
            <p className="text-xs text-red-300" data-testid="mission-type-generate-error">
              {generateError}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default MissionTypePicker;
