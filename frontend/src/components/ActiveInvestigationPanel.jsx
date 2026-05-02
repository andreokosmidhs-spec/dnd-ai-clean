import React, { useEffect, useState } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Search, Check, X, Dice5, Loader2, Trophy, Scroll, Lock } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const checkColors = {
  Investigation:  { chip: 'bg-sky-500/20 text-sky-200 border-sky-400/40',         border: 'border-sky-400/60'        },
  Perception:     { chip: 'bg-cyan-500/20 text-cyan-200 border-cyan-400/40',      border: 'border-cyan-400/60'       },
  Insight:        { chip: 'bg-violet-500/20 text-violet-200 border-violet-400/40', border: 'border-violet-400/60'    },
  Persuasion:     { chip: 'bg-amber-500/20 text-amber-200 border-amber-400/40',    border: 'border-amber-400/60'     },
  Deception:      { chip: 'bg-purple-500/20 text-purple-200 border-purple-400/40', border: 'border-purple-400/60'    },
  Intimidation:   { chip: 'bg-red-500/20 text-red-200 border-red-400/40',          border: 'border-red-400/60'       },
  Stealth:        { chip: 'bg-slate-500/20 text-slate-200 border-slate-400/40',    border: 'border-slate-400/60'     },
  'Sleight of Hand': { chip: 'bg-zinc-500/20 text-zinc-200 border-zinc-400/40',    border: 'border-zinc-400/60'      },
  Athletics:      { chip: 'bg-orange-500/20 text-orange-200 border-orange-400/40', border: 'border-orange-400/60'    },
  Arcana:         { chip: 'bg-fuchsia-500/20 text-fuchsia-200 border-fuchsia-400/40', border: 'border-fuchsia-400/60' },
  History:        { chip: 'bg-yellow-500/20 text-yellow-200 border-yellow-400/40', border: 'border-yellow-400/60'    },
  Nature:         { chip: 'bg-emerald-500/20 text-emerald-200 border-emerald-400/40', border: 'border-emerald-400/60' },
  Survival:       { chip: 'bg-lime-500/20 text-lime-200 border-lime-400/40',       border: 'border-lime-400/60'      },
};

const colorsFor = (k) => checkColors[k] || checkColors.Investigation;

const STATUS_TONE = {
  passed:  { dot: 'bg-emerald-400', label: 'passed'    },
  failed:  { dot: 'bg-rose-500',    label: 'failed'    },
  skipped: { dot: 'bg-amber-400',   label: 'skipped'   },
  active:  { dot: 'bg-amber-300',   label: 'in play'   },
  pending: { dot: 'bg-stone-600',   label: 'sealed'    },
};

/**
 * ActiveInvestigationPanel — centered modal with a card-draft layout.
 *
 *   ┌──────── BLURRED BACKDROP ────────┐
 *   │   ┌─ Card 1 ─┬─ Card 2 ─┬─ ─┐    │
 *   │   │   live   │  sealed  │ … │    │
 *   │   └──────────┴──────────┴───┘    │
 *   │       Roll d20 · Pass · Fail     │
 *   └──────────────────────────────────┘
 *
 * The active beat sits center, future beats render face-down (sealed) to
 * the right, resolved beats render face-up + dimmed to the left.
 *
 * Style is intentionally restrained right now — once the user shares the
 * card-draft reference image we'll do a tighter visual pass on the card
 * frames (border art, parchment grain, type-bar gradient, etc.).
 */
const ActiveInvestigationPanel = ({
  campaignId,
  storyline,
  onUpdate,
  onComplete,
  onClose,
}) => {
  const [busy, setBusy] = useState(false);
  const [lastRoll, setLastRoll] = useState(null);

  // Lock body scroll while the modal is up; close on Escape.
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKey = (e) => { if (e.key === 'Escape') onClose && onClose(); };
    window.addEventListener('keydown', onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener('keydown', onKey);
    };
  }, [onClose]);

  if (!storyline || storyline.status !== 'active') return null;

  const beats = storyline.beats || [];
  const idx = storyline.current_beat ?? 0;
  const beat = beats[idx];
  if (!beat) return null;

  const submitOutcome = async (outcome, outcomeText, rollTotal) => {
    setBusy(true);
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/storylines/${storyline.id}/resolve`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            outcome,
            outcome_text: outcomeText || null,
            roll_total: rollTotal ?? null,
          }),
        }
      );
      if (!res.ok) throw new Error(`Resolve failed: ${res.status}`);
      const data = await res.json();
      if (data.completed) {
        onComplete && onComplete(data.storyline, data.reward);
      } else {
        onUpdate && onUpdate(data.storyline);
      }
      setLastRoll(null);
    } catch (e) {
      toast.error('Could not advance the investigation. Try again.');
    } finally {
      setBusy(false);
    }
  };

  const handleRoll = () => {
    const die = 1 + Math.floor(Math.random() * 20);
    setLastRoll(die);
    const passed = die >= beat.dc;
    submitOutcome(
      passed ? 'passed' : 'failed',
      `Rolled ${die} vs DC ${beat.dc} — ${passed ? 'success' : 'failed'}.`,
      die
    );
  };

  const handleAbandon = async () => {
    if (!window.confirm('Abandon this investigation? The active quest card will be marked failed.')) {
      return;
    }
    setBusy(true);
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/storylines/${storyline.id}/abandon`,
        { method: 'POST' }
      );
      if (!res.ok) throw new Error();
      toast.success('Investigation abandoned.');
      onClose && onClose();
    } catch {
      toast.error('Could not abandon the investigation.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center p-4 sm:p-6"
      data-testid="active-investigation-panel"
      onClick={onClose}
    >
      {/* Blurred backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-md" aria-hidden="true" />

      {/* Frame — clicks inside don't close */}
      <div
        className="relative w-full max-w-5xl max-h-[88vh] flex flex-col gap-4 rounded-xl border border-amber-500/30 bg-gradient-to-b from-stone-950/95 via-stone-900/95 to-stone-950/95 p-4 sm:p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-3">
          <Search className="h-5 w-5 text-amber-300 shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="text-[10px] uppercase tracking-[0.18em] text-amber-300/70">
              Investigation
            </div>
            <div className="text-amber-100 font-semibold text-base sm:text-lg truncate" data-testid="storyline-title">
              {storyline.title}
            </div>
          </div>
          <Badge
            variant="outline"
            className="text-[10px] border-amber-300/40 text-amber-100/90"
            data-testid="beat-counter"
          >
            Beat {idx + 1} of {beats.length}
          </Badge>
          <Badge variant="outline" className="text-[10px] border-amber-300/30 text-amber-200/80">
            total DC {storyline.total_dc}
          </Badge>
          <Button
            size="sm"
            variant="ghost"
            className="h-7 w-7 p-0 text-amber-200/70 hover:text-amber-100"
            onClick={onClose}
            title="Close (Esc)"
            data-testid="storyline-close-btn"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Card draft row — horizontally scrollable on mobile */}
        <div className="flex-1 min-h-0 overflow-x-auto overflow-y-hidden">
          <div className="flex gap-3 sm:gap-4 px-1 pb-2 items-stretch min-w-min h-full">
            {beats.map((b, i) => (
              <BeatCard
                key={i}
                beat={b}
                index={i}
                total={beats.length}
                isActive={i === idx}
              />
            ))}
          </div>
        </div>

        {/* Active beat task line */}
        <div className="rounded-md border border-amber-500/30 bg-stone-950/80 px-3 py-2">
          <div className="text-[11px] uppercase tracking-[0.16em] text-amber-300/70 mb-0.5">
            Task
          </div>
          <div className="text-amber-100/95 text-sm italic">
            {beat.task}
          </div>
        </div>

        {/* Action bar */}
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            className="h-9 bg-amber-600 hover:bg-amber-500 text-black font-semibold"
            onClick={handleRoll}
            disabled={busy}
            data-testid="storyline-roll-btn"
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Dice5 className="h-4 w-4 mr-1" />}
            Roll d20{lastRoll != null ? ` · last: ${lastRoll}` : ''}
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-9 border-emerald-400/50 text-emerald-200 hover:bg-emerald-700/20"
            onClick={() => submitOutcome('passed', 'Resolved by player.', null)}
            disabled={busy}
            data-testid="storyline-pass-btn"
          >
            <Check className="h-4 w-4 mr-1" /> Pass
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-9 border-rose-400/50 text-rose-200 hover:bg-rose-700/20"
            onClick={() => submitOutcome('failed', 'Player accepted the failure.', null)}
            disabled={busy}
            data-testid="storyline-fail-btn"
          >
            <X className="h-4 w-4 mr-1" /> Fail
          </Button>
          <div className="flex-1" />
          <Button
            size="sm"
            variant="ghost"
            className="h-9 text-amber-200/60 hover:text-amber-100"
            onClick={handleAbandon}
            disabled={busy}
            data-testid="storyline-abandon-btn"
          >
            Abandon
          </Button>
        </div>
      </div>
    </div>
  );
};

/**
 * BeatCard — TCG-style card representation of a single beat.
 * Active beat is fully revealed; future beats are sealed (face-down with
 * just the index showing); resolved beats are dimmed and stamped.
 */
const BeatCard = ({ beat, index, total, isActive }) => {
  const c = colorsFor(beat.check_type);
  const tone = STATUS_TONE[beat.status] || STATUS_TONE.pending;
  const sealed = beat.status === 'pending';
  const resolved = ['passed', 'failed', 'skipped'].includes(beat.status);

  return (
    <div
      className={`relative shrink-0 w-[220px] sm:w-[240px] rounded-lg border-2 overflow-hidden flex flex-col
        transition-transform duration-300
        ${isActive
          ? `${c.border} bg-stone-900 shadow-xl scale-[1.04]`
          : sealed
            ? 'border-stone-700/60 bg-stone-950/80 opacity-80'
            : 'border-stone-700/50 bg-stone-950/60 opacity-70'}`}
      data-testid={`beat-card-${index}`}
      data-beat-status={beat.status}
    >
      {/* Top type bar */}
      <div
        className={`flex items-center justify-between px-2.5 py-1.5 text-[10.5px] uppercase tracking-wider
          ${sealed ? 'bg-stone-900 text-stone-500' : 'bg-stone-900/80 text-amber-200'}`}
      >
        <span className="font-semibold">
          {sealed ? `Beat ${index + 1}` : beat.check_type}
        </span>
        <span className={`px-1.5 py-0.5 rounded border ${
          sealed ? 'border-stone-700 text-stone-500' : c.chip
        }`}>
          DC {beat.dc}
        </span>
      </div>

      {/* Card body */}
      <div className="flex-1 px-3 py-2.5 flex flex-col gap-1.5">
        {sealed ? (
          <div className="flex-1 flex flex-col items-center justify-center text-stone-500 py-6">
            <Lock className="h-7 w-7 mb-1.5" />
            <div className="text-[11px] tracking-widest uppercase">Sealed</div>
            <div className="text-[10px] text-stone-600 mt-0.5">Beat {index + 1} of {total}</div>
          </div>
        ) : (
          <>
            <div className="text-amber-100 font-semibold text-sm leading-tight">
              {beat.title}
            </div>
            <div className="text-[12px] text-amber-100/80 italic font-serif leading-snug line-clamp-5">
              {beat.description}
            </div>
            {beat.outcome_text && (
              <div className="mt-1 text-[11px] text-amber-200/70 border-l-2 border-amber-500/40 pl-2 italic">
                {beat.outcome_text}
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer status */}
      <div
        className={`flex items-center gap-1.5 px-2.5 py-1.5 text-[10px] uppercase tracking-wider
          ${sealed ? 'bg-stone-900 text-stone-500' : 'bg-stone-950/80 text-amber-200/80'}`}
      >
        <span className={`w-1.5 h-1.5 rounded-full ${tone.dot}`} />
        <span>{tone.label}</span>
        <div className="flex-1" />
        <span className="text-stone-500">{index + 1}/{total}</span>
      </div>

      {/* Stamp for resolved cards */}
      {resolved && (
        <div
          className={`pointer-events-none absolute inset-0 flex items-center justify-center
            ${beat.status === 'passed' ? 'text-emerald-400/40' :
              beat.status === 'failed' ? 'text-rose-500/40' :
                                          'text-amber-400/40'}`}
        >
          <span className="text-3xl font-black uppercase tracking-widest -rotate-12 border-4 border-current px-3 py-0.5">
            {beat.status}
          </span>
        </div>
      )}
    </div>
  );
};

/**
 * StorylineRewardModal — celebration card on completion. Shows XP, tone-flavored
 * description, and an item if the LLM produced one.
 */
export const StorylineRewardModal = ({ open, reward, onClose }) => {
  if (!reward) return null;
  return (
    <Dialog open={!!open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent
        className="bg-stone-950 border-amber-500/40 text-amber-100 max-w-md"
        data-testid="storyline-reward-modal"
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-amber-200">
            <Trophy className="h-5 w-5 text-amber-300" />
            Investigation Resolved — {reward.title}
          </DialogTitle>
          <DialogDescription className="text-amber-100/80 italic font-serif pt-2">
            {reward.description}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-2">
          <div className="flex items-center gap-2" data-testid="reward-xp">
            <Badge className="bg-amber-500 text-black px-3 py-1 text-sm">
              + {reward.xp} XP
            </Badge>
            {reward.tone && (
              <Badge variant="outline" className="border-amber-300/40 text-amber-100/80">
                tone · {reward.tone}
              </Badge>
            )}
          </div>

          {reward.item && (
            <div className="rounded-md border border-amber-500/30 bg-stone-900/80 p-3" data-testid="reward-item">
              <div className="flex items-center gap-2">
                <Scroll className="h-4 w-4 text-amber-300" />
                <span className="font-semibold text-amber-100">{reward.item.name}</span>
                <Badge variant="outline" className="text-[10px] border-amber-300/40 text-amber-100/70 ml-auto">
                  {reward.item.kind || 'item'}
                </Badge>
              </div>
              <p className="text-[12.5px] text-amber-100/80 mt-1.5 leading-snug">
                {reward.item.description}
              </p>
            </div>
          )}
        </div>

        <div className="flex justify-end pt-1">
          <Button
            size="sm"
            className="bg-amber-600 hover:bg-amber-500 text-black"
            onClick={onClose}
            data-testid="reward-close-btn"
          >
            Continue
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ActiveInvestigationPanel;
