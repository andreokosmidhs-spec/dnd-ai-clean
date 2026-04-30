import React, { useEffect, useRef, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import { MessageSquarePlus, Send, Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { Label } from "./ui/label";
import { useSessionCore } from "../store/useSessionCore";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

const FEEDBACK_TYPES = [
  { value: "bug", label: "🐛 Bug report" },
  { value: "feature", label: "✨ Feature request" },
  { value: "other", label: "💬 Other" },
];

/**
 * Floating "Send Feedback" button shown on every screen (except the
 * Adventure Log, where it would clash with the in-game UI). Opens a
 * Shadcn dialog with a small form. On submit POSTs to /api/feedback/
 * which forwards the payload to the developer's inbox via Resend.
 *
 * Auto-attaches a snapshot of the player's current campaign / character
 * IDs (from useSessionCore + URL) and the user-agent so bug reports
 * are debuggable without a back-and-forth.
 */
const FeedbackButton = () => {
  const location = useLocation();
  const params = useParams();
  const { activeCampaignId, activeCharacterId } = useSessionCore();
  const [open, setOpen] = useState(false);
  const [type, setType] = useState("bug");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [fromEmail, setFromEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const dialogTriggerRef = useRef(null);

  // Persist the player's email between submissions for convenience.
  // (Hook must run unconditionally — early-return below would otherwise
  // change hook order on /game route.)
  useEffect(() => {
    const cached = localStorage.getItem("rpg-feedback-email");
    if (cached) setFromEmail(cached);
  }, []);

  // Hide on the in-game adventure screen so the floating button doesn't
  // sit on top of the input row. Players can still send feedback from any
  // other screen (main menu, characters list, wizard, etc.).
  const isInGame = location.pathname.startsWith("/game");
  if (isInGame) return null;

  const reset = () => {
    setTitle("");
    setDescription("");
    setSubmitError(null);
    setType("bug");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (submitting) return;
    setSubmitError(null);

    if (title.trim().length < 3) {
      setSubmitError("Title must be at least 3 characters.");
      return;
    }
    if (description.trim().length < 5) {
      setSubmitError("Description must be at least 5 characters.");
      return;
    }

    setSubmitting(true);
    try {
      const context = {
        campaignId: activeCampaignId || params.campaignId || null,
        characterId: activeCharacterId || params.characterId || null,
        currentUrl:
          typeof window !== "undefined" ? window.location.href : null,
        userAgent:
          typeof navigator !== "undefined" ? navigator.userAgent : null,
      };

      const res = await fetch(`${BACKEND_URL}/api/feedback/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type,
          title: title.trim(),
          description: description.trim(),
          fromEmail: fromEmail.trim() || undefined,
          context,
        }),
      });

      if (!res.ok) {
        const detail = await res
          .json()
          .then((j) => j?.detail || `HTTP ${res.status}`)
          .catch(() => `HTTP ${res.status}`);
        throw new Error(detail);
      }

      if (fromEmail.trim()) {
        localStorage.setItem("rpg-feedback-email", fromEmail.trim());
      }

      if (typeof window !== "undefined" && window.showToast) {
        window.showToast("✅ Feedback sent — thank you!", "success");
      }
      reset();
      setOpen(false);
    } catch (err) {
      setSubmitError(err.message || "Failed to send feedback");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <button
        type="button"
        ref={dialogTriggerRef}
        onClick={() => setOpen(true)}
        data-testid="feedback-floating-btn"
        title="Send feedback to the developer"
        className="fixed top-4 right-4 z-40 flex items-center gap-2 px-3 py-2 rounded-full
          bg-amber-600 hover:bg-amber-500 text-black font-semibold text-sm
          shadow-lg shadow-amber-900/30 border border-amber-300/30
          transition-transform hover:scale-105 active:scale-95"
      >
        <MessageSquarePlus className="h-4 w-4" />
        <span className="hidden sm:inline">Feedback</span>
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent
          className="bg-slate-950 border-amber-700/50 text-slate-100 max-w-lg"
          data-testid="feedback-dialog"
        >
          <DialogHeader>
            <DialogTitle className="text-amber-300 flex items-center gap-2">
              <MessageSquarePlus className="h-5 w-5" />
              Send Feedback
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Bug, feature idea, or anything else? It lands directly in the
              developer's inbox.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4 mt-2">
            <div>
              <Label className="text-sm text-slate-300 mb-2 block">Type</Label>
              <div className="flex gap-2 flex-wrap">
                {FEEDBACK_TYPES.map((t) => (
                  <button
                    key={t.value}
                    type="button"
                    onClick={() => setType(t.value)}
                    data-testid={`feedback-type-${t.value}`}
                    className={`px-3 py-2 rounded-md text-sm border transition-colors ${
                      type === t.value
                        ? "bg-amber-600 text-black border-amber-400 font-semibold"
                        : "bg-slate-900 text-slate-300 border-slate-700 hover:border-amber-500/50"
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <Label htmlFor="fb-title" className="text-sm text-slate-300 mb-1 block">
                Title
              </Label>
              <Input
                id="fb-title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Short summary…"
                maxLength={140}
                className="bg-slate-900 border-slate-700 text-slate-100"
                data-testid="feedback-title-input"
              />
            </div>

            <div>
              <Label htmlFor="fb-desc" className="text-sm text-slate-300 mb-1 block">
                Description
              </Label>
              <Textarea
                id="fb-desc"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What happened, what you expected, anything else…"
                rows={5}
                maxLength={4000}
                className="bg-slate-900 border-slate-700 text-slate-100 resize-y"
                data-testid="feedback-description-input"
              />
              <div className="text-right text-xs text-slate-500 mt-1">
                {description.length}/4000
              </div>
            </div>

            <div>
              <Label htmlFor="fb-email" className="text-sm text-slate-300 mb-1 block">
                Your email <span className="text-slate-500">(optional — for replies)</span>
              </Label>
              <Input
                id="fb-email"
                type="email"
                value={fromEmail}
                onChange={(e) => setFromEmail(e.target.value)}
                placeholder="you@example.com"
                className="bg-slate-900 border-slate-700 text-slate-100"
                data-testid="feedback-email-input"
              />
            </div>

            {submitError && (
              <div
                className="text-red-300 text-sm bg-red-950/40 border border-red-800/60 rounded-md px-3 py-2"
                data-testid="feedback-error"
              >
                {submitError}
              </div>
            )}

            <DialogFooter className="gap-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  reset();
                  setOpen(false);
                }}
                disabled={submitting}
                className="text-slate-300 hover:text-slate-100"
                data-testid="feedback-cancel-btn"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={submitting}
                className="bg-amber-600 hover:bg-amber-500 text-black font-semibold"
                data-testid="feedback-submit-btn"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Sending…
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" /> Send
                  </>
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default FeedbackButton;
