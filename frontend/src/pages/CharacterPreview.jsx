import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { ChevronLeft, Play, Pencil, Trash2, Loader2, User, Heart } from "lucide-react";
import { useSessionCore } from "../store/useSessionCore";
import { computeMaxHp } from "../utils/hp";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

const titleCase = (s) =>
  (s || "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

const StatCell = ({ label, value }) => (
  <div className="bg-slate-800/60 rounded-md px-3 py-2 text-center">
    <div className="text-[10px] uppercase tracking-wide text-slate-400">{label}</div>
    <div className="text-white font-semibold">{value ?? "—"}</div>
  </div>
);

const CharacterPreview = () => {
  const navigate = useNavigate();
  const { characterId } = useParams();
  const [character, setCharacter] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const { setSession } = useSessionCore();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/characters/v2/${characterId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!cancelled) setCharacter(data);
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

  const handleStartNewCampaign = () => {
    if (!character) return;
    setSession({
      activeCharacterId: character.id,
      activeCampaignId: null,
      campaignStatus: "none",
    });
    navigate("/campaign-setup");
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/characters/v2/${characterId}`, {
        method: "DELETE",
      });
      if (!res.ok && res.status !== 204) throw new Error(`HTTP ${res.status}`);
      if (window.showToast) window.showToast("Character deleted.", "success");
      navigate("/characters");
    } catch (e) {
      if (window.showToast) window.showToast(`Delete failed: ${e.message}`, "error");
      setDeleting(false);
      setConfirmDelete(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-300 flex items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin mr-2" /> Loading character…
      </div>
    );
  }

  if (error || !character) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 py-10 px-4">
        <div className="max-w-3xl mx-auto">
          <Button
            variant="ghost"
            onClick={() => navigate("/characters")}
            className="text-slate-400"
            data-testid="character-preview-back-btn"
          >
            <ChevronLeft className="h-4 w-4 mr-1" /> Back
          </Button>
          <Card className="mt-6 bg-red-900/20 border-red-700/50">
            <CardContent className="p-6 text-red-300">
              {error || "Character not found."}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const identity = character.identity || {};
  const race = character.race || {};
  const klass = character.class || character.class_ || {};
  const bg = character.background || {};
  const appearance = character.appearance || {};
  const abilities = character.abilityScores || {};
  const personality = bg.personality || {};

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-10 px-4">
      <div className="max-w-3xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => navigate("/characters")}
          className="text-slate-400 hover:text-slate-100 mb-4"
          data-testid="character-preview-back-btn"
        >
          <ChevronLeft className="h-4 w-4 mr-1" /> Back to heroes
        </Button>

        <Card className="bg-slate-900/70 border-slate-800">
          <CardContent className="p-6">
            <div className="flex items-start gap-5 mb-6">
              <div className="w-28 h-28 rounded-lg bg-slate-800 overflow-hidden flex-shrink-0 flex items-center justify-center">
                {character.portraitDataUrl ? (
                  <img
                    src={character.portraitDataUrl}
                    alt={identity.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <User className="h-10 w-10 text-slate-600" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <h1 className="text-2xl font-bold text-amber-300" data-testid="preview-name">
                  {identity.name || "Unnamed hero"}
                </h1>
                <p className="text-slate-300 mt-1">
                  Level {klass.level || 1} {titleCase(race.key)}{" "}
                  {titleCase(klass.subclassKey) || ""} {titleCase(klass.key)}
                </p>
                <div className="flex flex-wrap gap-2 mt-3">
                  {bg.key && (
                    <Badge variant="outline" className="border-slate-700 text-slate-300">
                      {titleCase(bg.key)}
                    </Badge>
                  )}
                  {identity.sex && (
                    <Badge variant="outline" className="border-slate-700 text-slate-300">
                      {titleCase(identity.sex)}
                    </Badge>
                  )}
                  {identity.age != null && (
                    <Badge variant="outline" className="border-slate-700 text-slate-300">
                      {identity.age} yrs
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            {/* Ability scores */}
            <div className="mb-6">
              <div className="text-xs uppercase tracking-wide text-slate-400 mb-2">Abilities</div>
              <div className="grid grid-cols-6 gap-2">
                <StatCell label="STR" value={abilities.str} />
                <StatCell label="DEX" value={abilities.dex} />
                <StatCell label="CON" value={abilities.con} />
                <StatCell label="INT" value={abilities.int} />
                <StatCell label="WIS" value={abilities.wis} />
                <StatCell label="CHA" value={abilities.cha} />
              </div>
              {(() => {
                const maxHp = computeMaxHp(klass.key, abilities.con, klass.level || 1);
                if (maxHp == null) return null;
                return (
                  <div
                    className="mt-3 flex items-center gap-2 text-sm text-rose-300"
                    data-testid="preview-max-hp"
                  >
                    <Heart className="h-4 w-4" />
                    <span>
                      Max HP: <span className="font-semibold text-rose-200">{maxHp}</span>
                      <span className="text-slate-500 ml-2 text-xs">
                        (hit die + CON modifier)
                      </span>
                    </span>
                  </div>
                );
              })()}
            </div>

            {/* Appearance */}
            {(appearance.build || appearance.hairColor || appearance.eyeColor || appearance.notableFeatures?.length) && (
              <div className="mb-6">
                <div className="text-xs uppercase tracking-wide text-slate-400 mb-2">Appearance</div>
                <div className="text-sm text-slate-300 space-y-1">
                  {appearance.ageCategory && <div>Age: {appearance.ageCategory}</div>}
                  {appearance.heightCm && <div>Height: {appearance.heightCm} cm</div>}
                  {appearance.build && <div>Build: {appearance.build}</div>}
                  {appearance.hairColor && <div>Hair: {appearance.hairColor}</div>}
                  {appearance.eyeColor && <div>Eyes: {appearance.eyeColor}</div>}
                  {appearance.notableFeatures?.length > 0 && (
                    <div>Notable: {appearance.notableFeatures.join(", ")}</div>
                  )}
                </div>
              </div>
            )}

            {/* Personality */}
            {(personality.ideal || personality.bond || personality.flaw) && (
              <div className="mb-6">
                <div className="text-xs uppercase tracking-wide text-slate-400 mb-2">Personality</div>
                <div className="space-y-2 text-sm">
                  {personality.ideal && (
                    <div>
                      <span className="text-amber-300 font-semibold">Ideal: </span>
                      <span className="text-slate-200" data-testid="preview-ideal">{personality.ideal}</span>
                    </div>
                  )}
                  {personality.bond && (
                    <div>
                      <span className="text-amber-300 font-semibold">Bond: </span>
                      <span className="text-slate-200" data-testid="preview-bond">{personality.bond}</span>
                    </div>
                  )}
                  {personality.flaw && (
                    <div>
                      <span className="text-amber-300 font-semibold">Flaw: </span>
                      <span className="text-slate-200" data-testid="preview-flaw">{personality.flaw}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-wrap gap-3 pt-4 border-t border-slate-800">
              <Button
                onClick={handleStartNewCampaign}
                className="bg-gradient-to-r from-amber-700 to-orange-700 hover:from-amber-600 hover:to-orange-600 text-black font-semibold"
                data-testid="preview-start-campaign-btn"
              >
                <Play className="h-4 w-4 mr-2" /> Start new campaign
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate(`/characters/${characterId}/edit`)}
                className="border-slate-700 text-slate-200 hover:bg-slate-800"
                data-testid="preview-edit-btn"
              >
                <Pencil className="h-4 w-4 mr-2" /> Edit
              </Button>
              <Button
                variant="outline"
                onClick={() => setConfirmDelete(true)}
                className="border-red-700/50 text-red-400 hover:bg-red-600/10"
                data-testid="preview-delete-btn"
              >
                <Trash2 className="h-4 w-4 mr-2" /> Delete
              </Button>
            </div>
          </CardContent>
        </Card>

        {confirmDelete && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <Card className="max-w-md w-full bg-slate-900 border-red-700/50">
              <CardContent className="p-6 space-y-4">
                <h2 className="text-red-400 font-bold text-lg flex items-center gap-2">
                  <Trash2 className="h-5 w-5" /> Delete {identity.name}?
                </h2>
                <p className="text-slate-300 text-sm">
                  This permanently removes the character. Campaigns started with this hero will keep their saved narrations but you won't be able to start new ones.
                </p>
                <div className="flex gap-3">
                  <Button
                    onClick={handleDelete}
                    disabled={deleting}
                    className="flex-1 bg-red-700 hover:bg-red-600 text-white"
                    data-testid="preview-confirm-delete-btn"
                  >
                    {deleting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                    Yes, delete
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setConfirmDelete(false)}
                    className="flex-1 border-slate-700 text-slate-300"
                    data-testid="preview-cancel-delete-btn"
                  >
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default CharacterPreview;
