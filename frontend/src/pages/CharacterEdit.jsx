import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { ChevronLeft, Save, Sparkles, Loader2, User } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

/**
 * Lean edit form — ONLY identity / appearance / personality / portrait.
 * Race, class, ability scores, and background key are intentionally locked
 * to avoid breaking downstream game state (HP, proficiencies, campaign context).
 */
const CharacterEdit = () => {
  const navigate = useNavigate();
  const { characterId } = useParams();
  const [character, setCharacter] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState(null);

  // Editable fields
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [build, setBuild] = useState("");
  const [skinTone, setSkinTone] = useState("");
  const [hairColor, setHairColor] = useState("");
  const [eyeColor, setEyeColor] = useState("");
  const [notableFeatures, setNotableFeatures] = useState("");
  const [ideal, setIdeal] = useState("");
  const [bond, setBond] = useState("");
  const [flaw, setFlaw] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/characters/v2/${characterId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (cancelled) return;
        setCharacter(data);
        setName(data?.identity?.name || "");
        setAge(String(data?.identity?.age ?? ""));
        setBuild(data?.appearance?.build || "");
        setSkinTone(data?.appearance?.skinTone || "");
        setHairColor(data?.appearance?.hairColor || "");
        setEyeColor(data?.appearance?.eyeColor || "");
        setNotableFeatures((data?.appearance?.notableFeatures || []).join(", "));
        setIdeal(data?.background?.personality?.ideal || "");
        setBond(data?.background?.personality?.bond || "");
        setFlaw(data?.background?.personality?.flaw || "");
      } catch (e) {
        if (!cancelled) setError(e.message || "Failed to load character");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [characterId]);

  const handleSave = async () => {
    if (!character) return;
    setSaving(true);
    setError(null);
    try {
      const patch = {
        identity: {
          ...character.identity,
          name: name.trim() || character.identity.name,
          age: Number.parseInt(age, 10) || character.identity.age,
        },
        appearance: {
          ...character.appearance,
          build: build.trim(),
          skinTone: skinTone.trim(),
          hairColor: hairColor.trim(),
          eyeColor: eyeColor.trim(),
          notableFeatures: notableFeatures
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
        },
        background: {
          ...character.background,
          personality: {
            ideal: ideal.trim(),
            bond: bond.trim(),
            flaw: flaw.trim(),
          },
        },
      };
      const res = await fetch(`${BACKEND_URL}/api/characters/v2/${characterId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }
      if (window.showToast) window.showToast("Character updated.", "success");
      navigate(`/characters/${characterId}`);
    } catch (e) {
      setError(e.message || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleRegenPortrait = async () => {
    setRegenerating(true);
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/characters/v2/${characterId}/generate-portrait`,
        { method: "POST" }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      // Refetch to show the new portrait
      const refetch = await fetch(`${BACKEND_URL}/api/characters/v2/${characterId}`);
      if (refetch.ok) {
        const data = await refetch.json();
        setCharacter(data);
      }
      if (window.showToast) window.showToast("Portrait regenerated.", "success");
    } catch (e) {
      if (window.showToast) window.showToast(`Portrait failed: ${e.message}`, "error");
    } finally {
      setRegenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-300 flex items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin mr-2" /> Loading…
      </div>
    );
  }

  if (!character) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 py-10 px-4 max-w-3xl mx-auto">
        <p className="text-red-400">{error || "Character not found."}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-10 px-4">
      <div className="max-w-3xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => navigate(`/characters/${characterId}`)}
          className="text-slate-400 hover:text-slate-100 mb-4"
          data-testid="edit-back-btn"
        >
          <ChevronLeft className="h-4 w-4 mr-1" /> Back
        </Button>

        <Card className="bg-slate-900/70 border-slate-800">
          <CardContent className="p-6 space-y-6">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-bold text-amber-300">Edit hero</h1>
              <p className="text-xs text-slate-500">
                Race, class, abilities, and background are locked to protect campaign state.
              </p>
            </div>

            {/* Portrait */}
            <div className="flex items-start gap-4">
              <div className="w-24 h-24 rounded-lg bg-slate-800 overflow-hidden flex items-center justify-center flex-shrink-0">
                {character.portraitDataUrl ? (
                  <img
                    src={character.portraitDataUrl}
                    alt={name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <User className="h-8 w-8 text-slate-600" />
                )}
              </div>
              <div>
                <div className="text-sm text-slate-300 mb-2">Portrait</div>
                <Button
                  variant="outline"
                  onClick={handleRegenPortrait}
                  disabled={regenerating}
                  className="border-slate-700 text-slate-200"
                  data-testid="edit-regen-portrait-btn"
                >
                  {regenerating ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Generating…
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4 mr-2" /> Regenerate portrait
                    </>
                  )}
                </Button>
              </div>
            </div>

            {/* Identity */}
            <section className="space-y-3">
              <h2 className="text-amber-300 font-semibold text-sm uppercase tracking-wide">
                Identity
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="edit-name">Name</Label>
                  <Input
                    id="edit-name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    data-testid="edit-name-input"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-age">Age</Label>
                  <Input
                    id="edit-age"
                    type="number"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    data-testid="edit-age-input"
                  />
                </div>
              </div>
            </section>

            {/* Appearance */}
            <section className="space-y-3">
              <h2 className="text-amber-300 font-semibold text-sm uppercase tracking-wide">
                Appearance
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="edit-build">Build</Label>
                  <Input id="edit-build" value={build} onChange={(e) => setBuild(e.target.value)} />
                </div>
                <div>
                  <Label htmlFor="edit-skin">Skin tone</Label>
                  <Input
                    id="edit-skin"
                    value={skinTone}
                    onChange={(e) => setSkinTone(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="edit-hair">Hair color</Label>
                  <Input
                    id="edit-hair"
                    value={hairColor}
                    onChange={(e) => setHairColor(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="edit-eyes">Eye color</Label>
                  <Input
                    id="edit-eyes"
                    value={eyeColor}
                    onChange={(e) => setEyeColor(e.target.value)}
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="edit-notable">Notable features (comma-separated)</Label>
                <Input
                  id="edit-notable"
                  value={notableFeatures}
                  onChange={(e) => setNotableFeatures(e.target.value)}
                  placeholder="e.g. burn scar on jaw, silver bracer on left arm"
                  data-testid="edit-notable-input"
                />
              </div>
            </section>

            {/* Personality */}
            <section className="space-y-3">
              <h2 className="text-amber-300 font-semibold text-sm uppercase tracking-wide">
                Personality
              </h2>
              <p className="text-xs text-slate-500">
                These drive how the DM narrates reactions and NPC friction. Be specific.
              </p>
              <div>
                <Label htmlFor="edit-ideal">Ideal</Label>
                <Textarea
                  id="edit-ideal"
                  value={ideal}
                  onChange={(e) => setIdeal(e.target.value)}
                  rows={2}
                  data-testid="edit-ideal-input"
                />
              </div>
              <div>
                <Label htmlFor="edit-bond">Bond</Label>
                <Textarea
                  id="edit-bond"
                  value={bond}
                  onChange={(e) => setBond(e.target.value)}
                  rows={2}
                  data-testid="edit-bond-input"
                />
              </div>
              <div>
                <Label htmlFor="edit-flaw">Flaw</Label>
                <Textarea
                  id="edit-flaw"
                  value={flaw}
                  onChange={(e) => setFlaw(e.target.value)}
                  rows={2}
                  data-testid="edit-flaw-input"
                />
              </div>
            </section>

            {error && <p className="text-red-400 text-sm">{error}</p>}

            <div className="flex gap-3 pt-2 border-t border-slate-800">
              <Button
                onClick={handleSave}
                disabled={saving}
                className="bg-amber-600 hover:bg-amber-500 text-black font-semibold"
                data-testid="edit-save-btn"
              >
                {saving ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                Save changes
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate(`/characters/${characterId}`)}
                className="border-slate-700 text-slate-300"
                data-testid="edit-cancel-btn"
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CharacterEdit;
