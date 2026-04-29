import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { PlusCircle, ChevronLeft, User, Loader2, Trash2 } from "lucide-react";
import { canCreateCharacter, CHARACTER_POOL_LIMIT } from "../utils/characterPool";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

const titleCase = (s) =>
  (s || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

const CharactersList = () => {
  const navigate = useNavigate();
  const [characters, setCharacters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [confirmDeleteAll, setConfirmDeleteAll] = useState(false);
  const [deletingAll, setDeletingAll] = useState(false);

  const isPoolFull = characters.length >= CHARACTER_POOL_LIMIT;

  const handleForgeNew = async () => {
    if (!(await canCreateCharacter())) return;
    navigate("/character-v2");
  };

  const handleDeleteAll = async () => {
    setDeletingAll(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/characters/v2/`, { method: "DELETE" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setCharacters([]);
      setConfirmDeleteAll(false);
      if (typeof window !== "undefined" && window.showToast) {
        window.showToast(`Deleted ${data.deleted ?? 0} character${data.deleted === 1 ? "" : "s"}.`, "success");
      }
    } catch (e) {
      if (typeof window !== "undefined" && window.showToast) {
        window.showToast(`Delete all failed: ${e.message}`, "error");
      }
    } finally {
      setDeletingAll(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/characters/v2/`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!cancelled) {
          // Newest first (fallback-safe)
          const sorted = [...(data || [])].sort((a, b) => {
            const aT = a?.meta?.createdAt || "";
            const bT = b?.meta?.createdAt || "";
            return bT.localeCompare(aT);
          });
          setCharacters(sorted);
        }
      } catch (e) {
        if (!cancelled) setError(e.message || "Failed to load characters");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-10 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <Button
            variant="ghost"
            onClick={() => navigate("/")}
            className="text-slate-400 hover:text-slate-100"
            data-testid="characters-list-back-btn"
          >
            <ChevronLeft className="h-4 w-4 mr-1" /> Back to menu
          </Button>
          <div className="flex items-center gap-2">
            {characters.length > 0 && (
              <Button
                onClick={() => setConfirmDeleteAll(true)}
                variant="outline"
                className="border-red-600/60 text-red-300 hover:bg-red-600/20 hover:text-red-200"
                data-testid="characters-list-delete-all-btn"
                title="Permanently delete every hero in your pool"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete All
              </Button>
            )}
            <Button
              onClick={handleForgeNew}
              disabled={isPoolFull}
              className="bg-amber-600 hover:bg-amber-500 text-black font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="characters-list-create-btn"
              title={isPoolFull ? `Pool full (${characters.length}/${CHARACTER_POOL_LIMIT}) — delete a hero first.` : undefined}
            >
              <PlusCircle className="h-4 w-4 mr-2" />
              Forge new hero
              <span className="ml-2 text-xs opacity-80" data-testid="characters-pool-count">
                {characters.length}/{CHARACTER_POOL_LIMIT}
              </span>
            </Button>
          </div>
        </div>

        {confirmDeleteAll && (
          <Card
            className="mb-6 bg-red-950/40 border-red-700/60"
            data-testid="characters-list-delete-all-confirm"
          >
            <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="text-red-200">
                <div className="font-semibold">Delete all {characters.length} characters?</div>
                <div className="text-sm text-red-300/80">
                  This cannot be undone. Campaigns referencing these heroes will keep their snapshots, but the character records will be gone forever.
                </div>
              </div>
              <div className="flex gap-2 flex-shrink-0">
                <Button
                  onClick={() => setConfirmDeleteAll(false)}
                  variant="ghost"
                  className="text-slate-300 hover:text-slate-100"
                  disabled={deletingAll}
                  data-testid="characters-list-delete-all-cancel"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleDeleteAll}
                  className="bg-red-600 hover:bg-red-500 text-white font-semibold"
                  disabled={deletingAll}
                  data-testid="characters-list-delete-all-confirm-btn"
                >
                  {deletingAll ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Deleting...
                    </>
                  ) : (
                    <>
                      <Trash2 className="h-4 w-4 mr-2" /> Yes, delete all
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold text-amber-400">Your Heroes</h1>
          <p className="text-sm text-slate-400">Pick one to preview, edit, or start a new campaign.</p>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-20 text-slate-400">
            <Loader2 className="h-5 w-5 animate-spin mr-2" /> Loading characters…
          </div>
        )}

        {!loading && error && (
          <Card className="bg-red-900/20 border-red-700/50">
            <CardContent className="p-6 text-red-300">Failed to load: {error}</CardContent>
          </Card>
        )}

        {!loading && !error && characters.length === 0 && (
          <Card className="bg-slate-900/60 border-slate-800">
            <CardContent className="p-10 text-center space-y-4">
              <User className="h-10 w-10 mx-auto text-slate-500" />
              <p className="text-slate-300">No heroes yet. Forge your first one.</p>
              <Button
                onClick={handleForgeNew}
                className="bg-amber-600 hover:bg-amber-500 text-black font-semibold"
                data-testid="characters-list-empty-create-btn"
              >
                <PlusCircle className="h-4 w-4 mr-2" /> Forge new hero
              </Button>
            </CardContent>
          </Card>
        )}

        {!loading && !error && characters.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {characters.map((c) => {
              const name = c?.identity?.name || "Unnamed hero";
              const race = titleCase(c?.race?.key);
              const klass = titleCase(c?.class?.key);
              const level = c?.class?.level || 1;
              const bg = titleCase(c?.background?.key);
              const portrait = c?.portraitDataUrl;
              return (
                <Card
                  key={c.id}
                  className="bg-slate-900/70 border-slate-800 hover:border-amber-500/60 transition-colors cursor-pointer"
                  onClick={() => navigate(`/characters/${c.id}`)}
                  data-testid={`character-card-${c.id}`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <div className="w-16 h-16 rounded-md bg-slate-800 overflow-hidden flex-shrink-0 flex items-center justify-center">
                        {portrait ? (
                          <img src={portrait} alt={name} className="w-full h-full object-cover" />
                        ) : (
                          <User className="h-6 w-6 text-slate-600" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-white font-semibold truncate">{name}</div>
                        <div className="text-xs text-slate-400 truncate">
                          Level {level} {race} {klass}
                        </div>
                        {bg && (
                          <Badge
                            variant="outline"
                            className="mt-2 text-[10px] border-slate-700 text-slate-300"
                          >
                            {bg}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default CharactersList;
