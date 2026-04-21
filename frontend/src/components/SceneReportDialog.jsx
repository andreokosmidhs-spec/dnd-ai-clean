import React, { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { Label } from "./ui/label";
import { Badge } from "./ui/badge";
import { Flag, Loader2 } from "lucide-react";

// Quick-reason chips (multi-select). Purely for filtering later.
const REASON_TAGS = [
  { value: "pov-leak", label: "POV leak" },
  { value: "cliche", label: "Cliché / bland" },
  { value: "ignores-context", label: "Ignored context" },
  { value: "personality-miss", label: "Personality miss" },
  { value: "quest-off", label: "Off the quest" },
  { value: "wrong-location", label: "Wrong location" },
  { value: "stalling", label: "Stalling" },
  { value: "other", label: "Other" },
];

const SceneReportDialog = ({
  open,
  onOpenChange,
  beatText = "",
  playerActionText = "",
  saving = false,
  onConfirm,
}) => {
  const [note, setNote] = useState("");
  const [tags, setTags] = useState([]);

  useEffect(() => {
    if (open) {
      setNote("");
      setTags([]);
    }
  }, [open]);

  const toggleTag = (t) =>
    setTags((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));

  const submit = () => {
    onConfirm?.({ note, tags });
  };

  const beatPreview =
    beatText.length > 260 ? beatText.slice(0, 260).trimEnd() + "…" : beatText;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="bg-slate-900 border-slate-800 text-slate-100 sm:max-w-xl"
        data-testid="scene-report-dialog"
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-rose-300">
            <Flag className="h-5 w-5" />
            Report this scene
          </DialogTitle>
          <DialogDescription className="text-slate-400">
            Captures this DM reply + your character state, active quests, and
            world context so we can debug what went wrong. Nothing is shared
            outside your campaign.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div>
            <Label className="text-slate-200">The DM beat being reported</Label>
            <div
              className="mt-1 text-sm text-slate-300 italic bg-slate-950/60 border border-slate-800 rounded-md p-3 leading-relaxed max-h-32 overflow-y-auto"
              data-testid="scene-report-beat-preview"
            >
              {beatPreview || "(empty)"}
            </div>
          </div>

          {playerActionText && (
            <div>
              <Label className="text-slate-200">Your action that triggered it</Label>
              <div className="mt-1 text-xs text-slate-400 bg-slate-950/60 border border-slate-800 rounded-md p-2">
                {playerActionText.length > 200
                  ? playerActionText.slice(0, 200).trimEnd() + "…"
                  : playerActionText}
              </div>
            </div>
          )}

          <div>
            <Label className="text-slate-200">What was wrong? (quick reasons)</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {REASON_TAGS.map((r) => {
                const active = tags.includes(r.value);
                return (
                  <Badge
                    key={r.value}
                    variant={active ? "default" : "outline"}
                    onClick={() => toggleTag(r.value)}
                    className={`cursor-pointer select-none transition-colors ${
                      active
                        ? "bg-rose-600 hover:bg-rose-500 text-white border-rose-500"
                        : "border-slate-700 text-slate-300 hover:border-rose-500/50"
                    }`}
                    data-testid={`scene-report-tag-${r.value}`}
                  >
                    {r.label}
                  </Badge>
                );
              })}
            </div>
          </div>

          <div>
            <Label htmlFor="scene-report-note" className="text-slate-200">
              Your note (optional)
            </Label>
            <Textarea
              id="scene-report-note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              placeholder="e.g. 'POV leak — narrator described my eye color again'"
              className="mt-1 bg-slate-950 border-slate-700"
              data-testid="scene-report-note-input"
              maxLength={500}
            />
            <p className="text-xs text-slate-500 mt-1">{note.length}/500</p>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange?.(false)}
            disabled={saving}
            className="border-slate-700 text-slate-200"
            data-testid="scene-report-cancel-btn"
          >
            Cancel
          </Button>
          <Button
            onClick={submit}
            disabled={saving}
            className="bg-rose-600 hover:bg-rose-500 text-white font-semibold"
            data-testid="scene-report-submit-btn"
          >
            {saving ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Flag className="h-4 w-4 mr-2" />
            )}
            File report
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default SceneReportDialog;
