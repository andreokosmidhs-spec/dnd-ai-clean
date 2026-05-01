import React, { useState } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Search, Check, X, Dice5, Loader2, Trophy, Scroll, ChevronDown } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const checkColors = {
  Investigation: 'bg-sky-500/20 text-sky-200 border-sky-400/40',
  Perception:    'bg-cyan-500/20 text-cyan-200 border-cyan-400/40',
  Insight:       'bg-violet-500/20 text-violet-200 border-violet-400/40',
  Persuasion:    'bg-amber-500/20 text-amber-200 border-amber-400/40',
  Deception:     'bg-purple-500/20 text-purple-200 border-purple-400/40',
  Intimidation:  'bg-red-500/20 text-red-200 border-red-400/40',
  Stealth:       'bg-slate-500/20 text-slate-200 border-slate-400/40',
  Athletics:     'bg-orange-500/20 text-orange-200 border-orange-400/40',
  Arcana:        'bg-fuchsia-500/20 text-fuchsia-200 border-fuchsia-400/40',
  History:       'bg-yellow-500/20 text-yellow-200 border-yellow-400/40',
  Nature:        'bg-emerald-500/20 text-emerald-200 border-emerald-400/40',
  Survival:      'bg-lime-500/20 text-lime-200 border-lime-400/40',
};

/**
 * ActiveInvestigationPanel — collapsible top bar showing the player's current
 * multi-beat investigation. Only visible when an `activeStoryline` is set.
 *
 *   ┌─────────────────────────────────────────────────────────────┐
 *   │ 🔎  Crate of Secrets   Beat 2 of 5            [▾ collapse]  │
 *   │     Beat 2: A Witness                                      │
 *   │     "Someone nearby saw what happened…"                    │
 *   │     Persuasion DC 13                                       │
 *   │     [ Roll d20 ]   [ Pass ]   [ Fail ]   [ Abandon ]       │
 *   └─────────────────────────────────────────────────────────────┘
 */
const ActiveInvestigationPanel = ({
  campaignId,
  storyline,
  onUpdate,
  onComplete,
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [lastRoll, setLastRoll] = useState(null);

  if (!storyline || storyline.status !== 'active') return null;

  const beats = storyline.beats || [];
  const idx = storyline.current_beat ?? 0;
  const beat = beats[idx];
  if (!beat) return null;

  const checkChip = checkColors[beat.check_type] || checkColors.Investigation;
  const totalBeats = beats.length;

  const rollDice = () => {
    const die = 1 + Math.floor(Math.random() * 20);
    setLastRoll(die);
    return die;
  };

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

  const handleRollAndResolve = () => {
    const die = rollDice();
    // For the first pass we treat the raw d20 vs DC; richer mod-based rolling
    // can be wired into the existing skill-check system later.
    const passed = die >= beat.dc;
    const text = `Rolled ${die} vs DC ${beat.dc} — ${passed ? 'success' : 'failed'}.`;
    submitOutcome(passed ? 'passed' : 'failed', text, die);
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
      onUpdate && onUpdate({ ...storyline, status: 'abandoned' });
      toast.success('Investigation abandoned.');
    } catch {
      toast.error('Could not abandon the investigation.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card
      className="border-amber-500/40 bg-gradient-to-r from-stone-950/95 via-amber-950/40 to-stone-950/95 shadow-lg"
      data-testid="active-investigation-panel"
    >
      <div
        className="flex items-center gap-3 px-3 py-2 cursor-pointer select-none"
        onClick={() => setCollapsed((c) => !c)}
      >
        <Search className="h-4 w-4 text-amber-300 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-amber-100 text-sm truncate" data-testid="storyline-title">
              {storyline.title}
            </span>
            <Badge
              variant="outline"
              className="text-[10px] border-amber-300/40 text-amber-100/90"
              data-testid="beat-counter"
            >
              Beat {idx + 1} of {totalBeats}
            </Badge>
            <Badge className={`text-[10px] ${checkChip}`} data-testid="check-chip">
              {beat.check_type} DC {beat.dc}
            </Badge>
          </div>
        </div>
        <ChevronDown className={`h-4 w-4 text-amber-300/80 transition-transform ${collapsed ? '' : 'rotate-180'}`} />
      </div>

      {!collapsed && (
        <div className="px-3 pb-3 pt-0 space-y-2">
          <div className="text-amber-100/95 text-sm leading-relaxed font-serif" data-testid="storyline-beat-text">
            <span className="font-semibold text-amber-200">{beat.title}.</span>{' '}
            {beat.description}
          </div>
          <div className="text-[12.5px] text-amber-200/85 italic">
            <span className="text-amber-300/70 not-italic font-semibold mr-1.5">Task:</span>
            {beat.task}
          </div>

          {/* Mini rail of beat dots */}
          <div className="flex items-center gap-1.5 mt-1" data-testid="beat-dot-rail">
            {beats.map((b, i) => {
              const tone =
                b.status === 'passed'   ? 'bg-emerald-400'  :
                b.status === 'failed'   ? 'bg-rose-500'    :
                b.status === 'skipped'  ? 'bg-amber-400'    :
                b.status === 'active'   ? 'bg-amber-300 ring-2 ring-amber-200/60' :
                                          'bg-stone-600';
              return (
                <div
                  key={i}
                  className={`w-2 h-2 rounded-full ${tone}`}
                  title={`Beat ${i+1}: ${b.title} (${b.status})`}
                  data-testid={`beat-dot-${i}`}
                  data-beat-status={b.status}
                />
              );
            })}
            <span className="ml-2 text-[11px] text-amber-200/60">
              total DC {storyline.total_dc}
            </span>
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            <Button
              size="sm"
              className="h-8 bg-amber-600 hover:bg-amber-500 text-black"
              onClick={handleRollAndResolve}
              disabled={busy}
              data-testid="storyline-roll-btn"
            >
              {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Dice5 className="h-3.5 w-3.5 mr-1" />}
              Roll d20{lastRoll != null ? ` · last: ${lastRoll}` : ''}
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="h-8 border-emerald-400/50 text-emerald-200 hover:bg-emerald-700/20"
              onClick={() => submitOutcome('passed', 'Resolved by player.', null)}
              disabled={busy}
              data-testid="storyline-pass-btn"
            >
              <Check className="h-3.5 w-3.5 mr-1" /> Pass
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="h-8 border-rose-400/50 text-rose-200 hover:bg-rose-700/20"
              onClick={() => submitOutcome('failed', 'Player accepted the failure.', null)}
              disabled={busy}
              data-testid="storyline-fail-btn"
            >
              <X className="h-3.5 w-3.5 mr-1" /> Fail
            </Button>
            <div className="flex-1" />
            <Button
              size="sm"
              variant="ghost"
              className="h-8 text-amber-200/60 hover:text-amber-100"
              onClick={handleAbandon}
              disabled={busy}
              data-testid="storyline-abandon-btn"
            >
              Abandon
            </Button>
          </div>
        </div>
      )}
    </Card>
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
