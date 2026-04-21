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
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Loader2, Bookmark } from "lucide-react";

const TYPES = [
  { value: "event", label: "Event — something that happened" },
  { value: "npc", label: "NPC — a person" },
  { value: "place", label: "Place — a location" },
  { value: "item", label: "Item — an object" },
  { value: "lore", label: "Lore — world fact or rumor" },
  { value: "belief", label: "Belief — hero's conviction" },
];

// Derive a short, readable title from the first sentence of the beat.
const deriveTitle = (text, max = 60) => {
  const s = (text || "").trim();
  if (!s) return "Remembered beat";
  for (const delim of [". ", "! ", "? ", "\n"]) {
    const idx = s.indexOf(delim);
    if (idx >= 10 && idx <= 70) return s.slice(0, idx).trim();
  }
  return s.length > max ? s.slice(0, max).trimEnd() + "…" : s;
};

const RememberCardDialog = ({ open, onOpenChange, beatText = "", saving = false, onConfirm }) => {
  const [title, setTitle] = useState("");
  const [type, setType] = useState("event");

  // Re-derive defaults each time the dialog opens for a new beat
  useEffect(() => {
    if (open) {
      setTitle(deriveTitle(beatText));
      setType("event");
    }
  }, [open, beatText]);

  const handleSubmit = () => {
    const finalTitle = title.trim() || deriveTitle(beatText);
    onConfirm?.({ title: finalTitle, type });
  };

  const preview =
    beatText.length > 220 ? beatText.slice(0, 220).trimEnd() + "…" : beatText;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="bg-slate-900 border-slate-800 text-slate-100 sm:max-w-lg"
        data-testid="remember-dialog"
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-amber-300">
            <Bookmark className="h-5 w-5" />
            Pin this beat
          </DialogTitle>
          <DialogDescription className="text-slate-400">
            Saved to the Knowledge Deck and fed to the DM on every future turn.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div>
            <Label htmlFor="remember-title" className="text-slate-200">
              Title
            </Label>
            <Input
              id="remember-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Kethra the fence at the Iron Gull"
              className="mt-1 bg-slate-950 border-slate-700"
              data-testid="remember-dialog-title-input"
              maxLength={80}
              autoFocus
            />
            <p className="text-xs text-slate-500 mt-1">{title.length}/80</p>
          </div>

          <div>
            <Label htmlFor="remember-type" className="text-slate-200">
              Type
            </Label>
            <Select value={type} onValueChange={setType}>
              <SelectTrigger
                id="remember-type"
                className="mt-1 bg-slate-950 border-slate-700"
                data-testid="remember-dialog-type-select"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-900 border-slate-700 text-slate-100">
                {TYPES.map((t) => (
                  <SelectItem
                    key={t.value}
                    value={t.value}
                    data-testid={`remember-dialog-type-${t.value}`}
                  >
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label className="text-slate-200">What will be saved</Label>
            <div
              className="mt-1 text-sm text-slate-300 italic bg-slate-950/60 border border-slate-800 rounded-md p-3 leading-relaxed"
              data-testid="remember-dialog-preview"
            >
              {preview || "(empty)"}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange?.(false)}
            disabled={saving}
            className="border-slate-700 text-slate-200"
            data-testid="remember-dialog-cancel-btn"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={saving}
            className="bg-amber-600 hover:bg-amber-500 text-black font-semibold"
            data-testid="remember-dialog-save-btn"
          >
            {saving ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Bookmark className="h-4 w-4 mr-2" />
            )}
            Save to deck
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default RememberCardDialog;
