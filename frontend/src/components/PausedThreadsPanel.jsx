import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, Scroll, Clock, Skull, AlertTriangle, Hourglass, MapPin, Users, Send } from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Textarea } from "./ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { toast } from "sonner";
import api from "../api/axiosConfig";

const URGENCY_STYLES = {
  critical: { label: "Critical", color: "bg-rose-500/20 text-rose-100 border-rose-500/50", icon: Skull },
  high: { label: "High", color: "bg-amber-500/20 text-amber-100 border-amber-500/50", icon: AlertTriangle },
  medium: { label: "Medium", color: "bg-yellow-500/15 text-yellow-100 border-yellow-500/40", icon: Hourglass },
  patient: { label: "Patient", color: "bg-emerald-500/15 text-emerald-100 border-emerald-500/40", icon: Clock },
};

const RULING_STYLES = {
  active: { label: "Reconnected", color: "text-emerald-300", icon: Send },
  cold: { label: "Cold Trail", color: "text-amber-300", icon: Hourglass },
  expired: { label: "Expired", color: "text-rose-300", icon: Skull },
};

const formatHoursElapsed = (pausedAtIso) => {
  if (!pausedAtIso) return "—";
  try {
    const then = new Date(pausedAtIso).getTime();
    const now = Date.now();
    const hours = Math.max(0, (now - then) / (1000 * 60 * 60));
    if (hours < 1) return `${Math.round(hours * 60)}m ago`;
    if (hours < 48) return `${hours.toFixed(1)}h ago`;
    return `${(hours / 24).toFixed(1)}d ago`;
  } catch {
    return "—";
  }
};

const PausedThreadsPanel = ({ campaignId, characterId, onResumed, embedded = false }) => {
  const [storylines, setStorylines] = useState([]);
  const [obligations, setObligations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [resumeTarget, setResumeTarget] = useState(null); // { storyline, obligation }
  const [resumeText, setResumeText] = useState("");
  const [resumeBusy, setResumeBusy] = useState(false);

  const fetchData = useCallback(async () => {
    if (!campaignId) return;
    setLoading(true);
    try {
      const [slRes, campRes] = await Promise.all([
        api.get(`/api/campaigns/${campaignId}/storylines`),
        api.get(`/api/campaigns/${campaignId}`).catch(() => ({ data: { pending_obligations: [] } })),
      ]);
      setStorylines((slRes.data?.storylines || []));
      setObligations(campRes.data?.pending_obligations || []);
    } catch (err) {
      console.error("PausedThreadsPanel fetch failed", err);
    } finally {
      setLoading(false);
    }
  }, [campaignId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Group storylines by status: paused (resumable) + expired (read-only memorial).
  const grouped = useMemo(() => {
    const paused = [];
    const expired = [];
    for (const sl of storylines) {
      if (sl.status === "paused") paused.push(sl);
      else if (sl.status === "expired") expired.push(sl);
    }
    return { paused, expired };
  }, [storylines]);

  const obligationForStoryline = (storylineId) =>
    obligations.find((o) => o?.storyline_id === storylineId) || null;

  const openResumeDialog = (storyline) => {
    const obligation = obligationForStoryline(storyline.id);
    setResumeTarget({ storyline, obligation });
    setResumeText("");
  };

  const submitResume = async () => {
    if (!resumeTarget || !resumeText.trim() || resumeBusy) return;
    setResumeBusy(true);
    try {
      const res = await api.post(
        `/api/campaigns/${campaignId}/storylines/${resumeTarget.storyline.id}/attempt-resume`,
        { character_id: characterId, player_action: resumeText.trim() }
      );
      const ruling = res.data?.ruling || {};
      const sl = res.data?.storyline;
      const styling = RULING_STYLES[ruling.ruling] || RULING_STYLES.cold;
      toast.success(
        `${styling.label}: ${resumeTarget.storyline.title}`,
        {
          description: ruling.narration?.slice(0, 240) || "",
          duration: 8000,
        }
      );
      // Push the narration to the adventure log via the optional callback.
      if (onResumed && ruling.narration) {
        onResumed({
          storyline: sl,
          ruling,
          new_lead_card_id: res.data?.new_lead_card_id,
          new_lead_card: res.data?.new_lead_card || null,
        });
      }
      setResumeTarget(null);
      setResumeText("");
      await fetchData();
    } catch (err) {
      console.error("Resume attempt failed", err);
      toast.error("The DM couldn't rule on that — try a clearer approach.");
    } finally {
      setResumeBusy(false);
    }
  };

  const PausedRow = ({ storyline }) => {
    const obligation = obligationForStoryline(storyline.id);
    const urgency = obligation?.urgency || "medium";
    const ustyle = URGENCY_STYLES[urgency] || URGENCY_STYLES.medium;
    const UIcon = ustyle.icon;
    const mt = storyline.mission_type;
    return (
      <div
        className="rounded-lg border border-amber-500/20 bg-stone-900/60 p-3"
        data-testid={`paused-thread-${storyline.id}`}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h4 className="text-amber-200 font-semibold text-sm truncate">
              {mt?.icon || "🎲"} {storyline.title}
            </h4>
            {mt?.name && (
              <p className="text-[11px] uppercase tracking-wider text-amber-400/70 mt-0.5">
                {mt.name}
              </p>
            )}
          </div>
          <Badge variant="outline" className={`text-[10px] gap-1 ${ustyle.color}`}>
            <UIcon className="h-3 w-3" />
            {ustyle.label}
          </Badge>
        </div>

        <p className="text-xs text-stone-300 mt-2 line-clamp-3">
          {obligation?.summary || storyline.hook_text || "—"}
        </p>

        <div className="flex flex-wrap items-center gap-3 mt-2 text-[11px] text-stone-400">
          <span className="inline-flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Paused {formatHoursElapsed(obligation?.paused_at)}
          </span>
          {(obligation?.npc_names || []).length > 0 && (
            <span className="inline-flex items-center gap-1">
              <Users className="h-3 w-3" />
              {obligation.npc_names.slice(0, 2).join(", ")}
              {obligation.npc_names.length > 2 ? ` +${obligation.npc_names.length - 2}` : ""}
            </span>
          )}
          {(obligation?.location_names || []).length > 0 && (
            <span className="inline-flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              {obligation.location_names[0]}
            </span>
          )}
        </div>

        <Button
          onClick={() => openResumeDialog(storyline)}
          size="sm"
          variant="outline"
          className="mt-3 w-full h-7 text-xs border-amber-500/40 text-amber-200 hover:bg-amber-500/10"
          data-testid={`paused-thread-resume-btn-${storyline.id}`}
        >
          Try to find them →
        </Button>
      </div>
    );
  };

  const ExpiredRow = ({ storyline }) => {
    const obligation = obligationForStoryline(storyline.id);
    const mt = storyline.mission_type;
    return (
      <div
        className="rounded-lg border border-rose-500/20 bg-stone-900/40 p-3 opacity-80"
        data-testid={`expired-thread-${storyline.id}`}
      >
        <div className="flex items-start justify-between gap-2">
          <h4 className="text-rose-200 font-semibold text-sm truncate line-through decoration-rose-500/40">
            {mt?.icon || "🎲"} {storyline.title}
          </h4>
          <Badge variant="outline" className="text-[10px] gap-1 bg-rose-500/15 text-rose-200 border-rose-500/40">
            <Skull className="h-3 w-3" />
            Expired
          </Badge>
        </div>
        <p className="text-xs text-stone-400 mt-2 line-clamp-2">
          {obligation?.summary || storyline.hook_text || "Thread lost to time."}
        </p>
        {storyline.last_resume_ruling?.narration && (
          <p className="text-[11px] italic text-stone-500 mt-2 border-l-2 border-rose-500/30 pl-2">
            {storyline.last_resume_ruling.narration.slice(0, 200)}
          </p>
        )}
      </div>
    );
  };

  const body = loading ? (
    <div className="flex items-center justify-center py-10 text-stone-400 text-sm">
      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
      Loading paused threads…
    </div>
  ) : grouped.paused.length === 0 && grouped.expired.length === 0 ? (
    <div className="text-center text-stone-400 text-xs italic py-6">
      No paused threads — every storyline you've opened is still active.
    </div>
  ) : (
    <div className="space-y-4">
      {grouped.paused.length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-[0.25em] text-amber-400 mb-2">
            Paused — recoverable
          </p>
          <div className="space-y-2" data-testid="paused-threads-list">
            {grouped.paused.map((sl) => (
              <PausedRow key={sl.id} storyline={sl} />
            ))}
          </div>
        </div>
      )}
      {grouped.expired.length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-[0.25em] text-rose-400 mb-2">
            Expired — lost to time
          </p>
          <div className="space-y-2" data-testid="expired-threads-list">
            {grouped.expired.map((sl) => (
              <ExpiredRow key={sl.id} storyline={sl} />
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const sharedDialog = (
    <Dialog
      open={!!resumeTarget}
      onOpenChange={(open) => {
        if (!open) {
          setResumeTarget(null);
          setResumeText("");
        }
      }}
    >
      <DialogContent className="bg-stone-950 border-2 border-amber-500/50 text-amber-50 max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-amber-300">
            <Scroll className="h-5 w-5" />
            How do you try to find them?
          </DialogTitle>
          <DialogDescription className="text-stone-300">
            The DM rules whether this thread is still alive based on what
            you do — where you go, who you ask, and how. No teleporting back.
          </DialogDescription>
        </DialogHeader>

        {resumeTarget?.obligation && (
          <div className="rounded-lg border border-amber-500/20 bg-stone-900/60 p-3 mb-2 text-xs">
            <p className="text-amber-200 font-semibold mb-1">
              {resumeTarget.storyline.title}
            </p>
            <p className="text-stone-300">{resumeTarget.obligation.summary}</p>
            {(resumeTarget.obligation.npc_names || []).length > 0 && (
              <p className="text-stone-400 mt-1.5">
                <Users className="h-3 w-3 inline mr-1" />
                Last known: {resumeTarget.obligation.npc_names.join(", ")}
              </p>
            )}
          </div>
        )}

        <Textarea
          value={resumeText}
          onChange={(e) => setResumeText(e.target.value)}
          placeholder='e.g. "I head back to the Anvil & Cup at dusk and ask the bartender if Hester is still posted there."'
          className="min-h-[100px] bg-stone-900/80 border-stone-700 text-amber-50"
          data-testid="resume-attempt-input"
          disabled={resumeBusy}
        />

        <DialogFooter>
          <Button
            variant="ghost"
            onClick={() => setResumeTarget(null)}
            disabled={resumeBusy}
          >
            Cancel
          </Button>
          <Button
            onClick={submitResume}
            disabled={resumeBusy || !resumeText.trim()}
            className="bg-amber-500 hover:bg-amber-400 text-stone-950 font-semibold"
            data-testid="resume-attempt-submit-btn"
          >
            {resumeBusy ? (
              <>
                <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
                The DM is ruling…
              </>
            ) : (
              <>
                <Send className="h-4 w-4 mr-1.5" />
                Make the attempt
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );

  return (
    <>
      {embedded ? body : <div className="p-3">{body}</div>}
      {sharedDialog}
    </>
  );
};

export default PausedThreadsPanel;
