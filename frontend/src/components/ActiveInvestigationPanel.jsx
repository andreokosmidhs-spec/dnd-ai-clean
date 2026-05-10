import React, { useEffect, useState, useMemo } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Textarea } from './ui/textarea';
import { Search, Check, X, Dice5, Loader2, Trophy, Scroll, Lock, RotateCw, ArrowRight, Wand2 } from 'lucide-react';
import { toast } from 'sonner';
import { abilityMod } from '../utils/hp';
import { DMFeedbackButton } from './storyline/DMFeedbackButton';
import { PitchInput } from './storyline/PitchInput';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const checkColors = {
  Investigation:    { chip: 'bg-sky-500/20 text-sky-200 border-sky-400/40',         border: 'border-sky-400/60'        },
  Perception:       { chip: 'bg-cyan-500/20 text-cyan-200 border-cyan-400/40',      border: 'border-cyan-400/60'       },
  Insight:          { chip: 'bg-violet-500/20 text-violet-200 border-violet-400/40', border: 'border-violet-400/60'    },
  Persuasion:       { chip: 'bg-amber-500/20 text-amber-200 border-amber-400/40',    border: 'border-amber-400/60'     },
  Deception:        { chip: 'bg-purple-500/20 text-purple-200 border-purple-400/40', border: 'border-purple-400/60'    },
  Intimidation:     { chip: 'bg-red-500/20 text-red-200 border-red-400/40',          border: 'border-red-400/60'       },
  Stealth:          { chip: 'bg-slate-500/20 text-slate-200 border-slate-400/40',    border: 'border-slate-400/60'     },
  'Sleight of Hand':{ chip: 'bg-zinc-500/20 text-zinc-200 border-zinc-400/40',       border: 'border-zinc-400/60'      },
  Athletics:        { chip: 'bg-orange-500/20 text-orange-200 border-orange-400/40', border: 'border-orange-400/60'    },
  Arcana:           { chip: 'bg-fuchsia-500/20 text-fuchsia-200 border-fuchsia-400/40', border: 'border-fuchsia-400/60' },
  History:          { chip: 'bg-yellow-500/20 text-yellow-200 border-yellow-400/40', border: 'border-yellow-400/60'    },
  Nature:           { chip: 'bg-emerald-500/20 text-emerald-200 border-emerald-400/40', border: 'border-emerald-400/60' },
  Survival:         { chip: 'bg-lime-500/20 text-lime-200 border-lime-400/40',       border: 'border-lime-400/60'      },
};

const colorsFor = (k) => checkColors[k] || checkColors.Investigation;

const STATUS_TONE = {
  passed:  { dot: 'bg-emerald-400', label: 'passed'    },
  failed:  { dot: 'bg-rose-500',    label: 'failed'    },
  skipped: { dot: 'bg-amber-400',   label: 'skipped'   },
  active:  { dot: 'bg-amber-300',   label: 'in play'   },
  pending: { dot: 'bg-stone-600',   label: 'sealed'    },
};

const ABILITY_FOR_CHECK = {
  Investigation: 'int', Perception: 'wis',  Insight: 'wis',
  Persuasion: 'cha',    Deception: 'cha',   Intimidation: 'cha',
  Stealth: 'dex',       'Sleight of Hand': 'dex',
  Athletics: 'str',     Arcana: 'int',      History: 'int',
  Nature: 'wis',        Survival: 'wis',
};

const readAbilityScore = (character, key) => {
  if (!character) return 10;
  const a = character.abilityScores || character.stats || {};
  return Number(
    a[key] ??
    a[{ str: 'strength', dex: 'dexterity', con: 'constitution', int: 'intelligence', wis: 'wisdom', cha: 'charisma' }[key]] ??
    10
  );
};

const formatMod = (m) => (m >= 0 ? `+${m}` : `${m}`);

/**
 * ActiveInvestigationPanel — centered modal with a card-draft layout.
 * Failure semantics:
 *   - Default: "fail-forward" (advance with a complication beat)
 *   - One-time "Press On" per storyline (retry with a cost)
 *   - "Try a different approach" — player types a strategy, DM judges
 *
 * Rolls are d20 + ability modifier (Investigation→INT, etc.).
 */
const ActiveInvestigationPanel = ({
  campaignId,
  character,
  storyline,
  onUpdate,
  onComplete,
  onClose,
  onComplication,    // fired when the backend returns a complication beat
  onCreativeNarration, // fired when a creative approach lands a narration
  onLeadMinted,      // fired when a knowledge beat mints a Lead card (revealed or sealed)
  onTargetCardsMinted, // fired when a knowledge beat auto-mints Knowledge Cards for named entities
}) => {
  const [busy, setBusy] = useState(false);
  const [lastRoll, setLastRoll] = useState(null);  // { die, mod, total, dc, passed }
  const [failPrompt, setFailPrompt] = useState(false);
  const [creativeOpen, setCreativeOpen] = useState(false);
  const [creativeText, setCreativeText] = useState('');

  // Lock body scroll while the modal is up; close on Escape (only when
  // no nested dialogs are open).
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKey = (e) => {
      if (e.key === 'Escape' && !failPrompt && !creativeOpen) onClose && onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener('keydown', onKey);
    };
  }, [onClose, failPrompt, creativeOpen]);

  const beats = storyline?.beats || [];
  const idx = storyline?.current_beat ?? 0;
  const beat = beats[idx];

  const ability = useMemo(
    () => ABILITY_FOR_CHECK[beat?.check_type] || 'int',
    [beat?.check_type]
  );
  const mod = useMemo(
    () => abilityMod(readAbilityScore(character, ability)),
    [character, ability]
  );

  if (!storyline || storyline.status !== 'active' || !beat) return null;

  const pressOnAvailable = !storyline.press_on_used;
  // Roll is optional when:
  //   - the LLM explicitly marked the beat `roll_optional` (no natural check), OR
  //   - the beat's DC is 0 (action beat with public/visible content — no roll needed).
  const rollOptional = !!beat.roll_optional || Number(beat.dc) <= 0;

  // -------- API helpers --------

  const callResolve = async ({ outcome, mode = null, rollTotal = null, outcomeText = null }) => {
    setBusy(true);
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/storylines/${storyline.id}/resolve`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            outcome,
            mode,
            outcome_text: outcomeText,
            roll_total: rollTotal,
          }),
        }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.error?.message || `Resolve failed: ${res.status}`);
      }
      const data = await res.json();
      if (data.complication && onComplication) onComplication(data.complication, data.storyline);
      if (data.lead && onLeadMinted) onLeadMinted(data.lead);
      if (Array.isArray(data.target_cards) && data.target_cards.length > 0 && onTargetCardsMinted) {
        onTargetCardsMinted(data.target_cards);
      }
      if (data.completed) {
        onComplete && onComplete(data.storyline, data.reward);
      } else {
        onUpdate && onUpdate(data.storyline);
      }
    } catch (e) {
      toast.error(e.message || 'Could not advance the investigation.');
    } finally {
      setBusy(false);
      setFailPrompt(false);
    }
  };

  const callCreative = async (approach) => {
    if (!approach.trim()) {
      toast.error('Describe your approach first.');
      return;
    }
    setBusy(true);
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/storylines/${storyline.id}/creative`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ approach_text: approach }),
        }
      );
      if (!res.ok) throw new Error(`Creative failed: ${res.status}`);
      const data = await res.json();
      if (data.narration && onCreativeNarration) {
        onCreativeNarration(data.narration, data.judgment, data.storyline);
      }
      if (data.complication && onComplication) {
        onComplication(data.complication, data.storyline);
      }
      if (data.lead && onLeadMinted) onLeadMinted(data.lead);
      if (Array.isArray(data.target_cards) && data.target_cards.length > 0 && onTargetCardsMinted) {
        onTargetCardsMinted(data.target_cards);
      }
      if (data.completed) {
        onComplete && onComplete(data.storyline, data.reward);
      } else {
        onUpdate && onUpdate(data.storyline);
      }
      setCreativeOpen(false);
      setCreativeText('');
      toast.success(`DM judged: ${data.judgment}`);
    } catch (e) {
      toast.error('Could not submit your approach.');
    } finally {
      setBusy(false);
    }
  };

  // -------- Roll & resolve --------

  const handleRoll = () => {
    const die = 1 + Math.floor(Math.random() * 20);
    const total = die + mod;
    const passed = total >= beat.dc;
    setLastRoll({ die, mod, total, dc: beat.dc, passed });
    if (passed) {
      callResolve({
        outcome: 'passed',
        rollTotal: total,
        outcomeText: `Rolled ${die}${formatMod(mod)} = ${total} vs DC ${beat.dc} — success.`,
      });
    } else {
      // Don't advance yet — let the player choose: Press On / Push Through / Creative
      setFailPrompt(true);
    }
  };

  const handleSkip = () => {
    callResolve({
      outcome: 'skipped',
      outcomeText: 'You let the moment pass without forcing it — the scene moves on.',
    });
  };

  const passed = beats.filter((b) => b.status === 'passed').length;
  const failed = beats.filter((b) => b.status === 'failed').length;

  const handleAbandon = async () => {
    if (!window.confirm('Abandon this investigation? The active quest card will be marked failed.')) return;
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
      <div className="absolute inset-0 bg-black/75 backdrop-blur-md" aria-hidden="true" />

      <div
        className="relative w-full max-w-5xl max-h-[88vh] flex flex-col gap-4 rounded-xl border-2 border-amber-500/60 bg-stone-950 p-4 sm:p-6 shadow-[0_0_60px_rgba(245,158,11,0.25)]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-3">
          <Search className="h-5 w-5 text-amber-300 shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="text-[11px] uppercase tracking-[0.18em] text-amber-300 font-semibold">
              Investigation
            </div>
            <div className="text-amber-50 font-bold text-lg sm:text-xl truncate" data-testid="storyline-title">
              {storyline.title}
            </div>
          </div>
          <Badge variant="outline" className="text-[11px] border-amber-300 text-amber-50 bg-stone-800 font-bold" data-testid="beat-counter">
            Beat {idx + 1} of {beats.length}
          </Badge>
          {beat.time_of_day && (
            <Badge
              variant="outline"
              className="text-[11px] border-indigo-300 text-indigo-50 bg-stone-800 font-bold"
              data-testid="beat-time-of-day"
              title={`In-fiction time: ${beat.time_of_day.label}${beat.time_of_day.hour != null ? ` (hour ${beat.time_of_day.hour}/24)` : ''}`}
            >
              <span className="mr-1" aria-hidden="true">{beat.time_of_day.icon}</span>
              {beat.time_of_day.label}
            </Badge>
          )}
          <Badge variant="outline" className="text-[11px] border-emerald-300 text-emerald-100 bg-stone-800 font-bold">
            {passed} passed
          </Badge>
          <Badge variant="outline" className="text-[11px] border-rose-300 text-rose-100 bg-stone-800 font-bold">
            {failed} failed
          </Badge>
          <Button
            size="sm" variant="ghost"
            className="h-8 w-8 p-0 text-amber-100 hover:bg-amber-500/20 hover:text-amber-50"
            onClick={onClose} title="Close (Esc)"
            data-testid="storyline-close-btn"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Card draft row */}
        <div className="flex-1 min-h-0 overflow-x-auto overflow-y-hidden">
          <div className="flex gap-3 sm:gap-4 px-1 pb-2 items-stretch min-w-min h-full">
            {beats.map((b, i) => (
              <BeatCard
                key={i}
                beat={b}
                index={i}
                total={beats.length}
                isActive={i === idx}
                complication={i === idx ? storyline.complication : null}
                pressOnUsed={i === idx ? !!storyline.press_on_used : false}
                campaignId={campaignId}
                storylineId={storyline.id}
                onCorrectionApplied={onUpdate}
              />
            ))}
          </div>
        </div>

        {/* Active beat task line */}
        <div className="rounded-md border border-amber-500/50 bg-stone-900 px-3 py-2.5">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] uppercase tracking-[0.16em] text-amber-300 font-semibold">Task</span>
            <Badge variant="outline" className="text-[10.5px] border-amber-300/60 text-amber-100/95 ml-auto">
              {ability.toUpperCase()} mod {formatMod(mod)}
            </Badge>
          </div>
          <div className="text-amber-50 text-base italic font-serif leading-relaxed">{beat.task}</div>
          {lastRoll && !lastRoll.passed && (
            <div className="mt-2 text-[13px] text-rose-200 italic">
              Last roll: {lastRoll.die}{formatMod(lastRoll.mod)} = {lastRoll.total} vs DC {lastRoll.dc} — failed.
            </div>
          )}
        </div>

        {/* Action bar — creative approach is the primary path; roll is loose
            and skip lets the player proceed without forcing a check.
            Knowledge beats hide skip (the player NEEDS the reveal to advance). */}
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            className="h-9 bg-fuchsia-500 hover:bg-fuchsia-400 text-black font-bold"
            onClick={() => setCreativeOpen(true)} disabled={busy}
            data-testid="storyline-creative-btn"
            title="Type what you do — the DM will judge and continue the scene"
          >
            <Wand2 className="h-4 w-4 mr-1" /> What do you do?
          </Button>
          <Button
            size="sm" variant="outline"
            className="h-9 border-amber-400/70 text-amber-100 bg-amber-950/30 hover:bg-amber-700/30"
            onClick={handleRoll} disabled={busy || rollOptional}
            data-testid="storyline-roll-btn"
            title={rollOptional ? 'No check suggested for this scene' : undefined}
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Dice5 className="h-4 w-4 mr-1" />}
            {rollOptional
              ? 'No check needed'
              : (<>Roll d20{formatMod(mod)} <span className="ml-1 text-[10px] uppercase tracking-wider opacity-70">suggested</span></>)
            }
          </Button>
          {beat.reveal_type !== 'knowledge' && (
            <Button
              size="sm"
              variant={rollOptional ? 'default' : 'ghost'}
              className={
                rollOptional
                  ? 'h-9 bg-emerald-600 hover:bg-emerald-500 text-stone-950 font-bold border border-emerald-300'
                  : 'h-9 text-stone-200 hover:text-amber-50 hover:bg-stone-800/70 border border-stone-600'
              }
              onClick={handleSkip} disabled={busy}
              data-testid="storyline-skip-btn"
              title={rollOptional
                ? 'No check needed — continue the scene'
                : 'Proceed without rolling — the scene moves on'}
            >
              <ArrowRight className="h-4 w-4 mr-1" />
              {rollOptional ? 'Continue' : 'Skip · Proceed'}
            </Button>
          )}
          <div className="flex-1" />
          <Button
            size="sm" variant="ghost"
            className="h-9 text-amber-200 hover:text-amber-50 hover:bg-amber-500/10"
            onClick={handleAbandon} disabled={busy}
            data-testid="storyline-abandon-btn"
          >
            Abandon
          </Button>
        </div>

        {/* Failure resolution prompt */}
        <FailurePrompt
          open={failPrompt}
          beat={beat}
          lastRoll={lastRoll}
          pressOnAvailable={pressOnAvailable}
          busy={busy}
          onPressOn={() => callResolve({
            outcome: 'failed',
            mode: 'press-on',
            rollTotal: lastRoll?.total ?? null,
            outcomeText: lastRoll
              ? `Rolled ${lastRoll.die}${formatMod(lastRoll.mod)} = ${lastRoll.total} vs DC ${lastRoll.dc} — pressing on.`
              : 'Pressing on after a failed attempt.',
          })}
          onPushThrough={() => callResolve({
            outcome: 'failed',
            mode: 'fail-forward',
            rollTotal: lastRoll?.total ?? null,
            outcomeText: lastRoll
              ? `Rolled ${lastRoll.die}${formatMod(lastRoll.mod)} = ${lastRoll.total} vs DC ${lastRoll.dc} — failure carried forward.`
              : 'Failure carried forward.',
          })}
          onCreative={() => { setFailPrompt(false); setCreativeOpen(true); }}
          onCancel={() => setFailPrompt(false)}
        />

        {/* Creative-approach drawer */}
        <CreativeApproachDialog
          open={creativeOpen}
          beat={beat}
          busy={busy}
          text={creativeText}
          setText={setCreativeText}
          onSubmit={() => callCreative(creativeText)}
          onClose={() => { setCreativeOpen(false); setCreativeText(''); }}
        />
      </div>
    </div>
  );
};

const FailurePrompt = ({ open, beat, lastRoll, pressOnAvailable, busy, onPressOn, onPushThrough, onCreative, onCancel }) => (
  <Dialog open={open} onOpenChange={(o) => !o && onCancel()}>
    <DialogContent className="bg-stone-950 border-2 border-rose-500/50 text-amber-50 max-w-md" data-testid="failure-prompt">
      <DialogHeader>
        <DialogTitle className="text-rose-200 flex items-center gap-2">
          <X className="h-5 w-5" /> Failed: {beat.title}
        </DialogTitle>
        <DialogDescription className="text-amber-100/95 italic font-serif pt-1">
          {lastRoll
            ? `You rolled ${lastRoll.die}${formatMod(lastRoll.mod)} = ${lastRoll.total} vs DC ${lastRoll.dc}. Choose how to handle the failure.`
            : 'Choose how to handle the failure.'}
        </DialogDescription>
      </DialogHeader>

      <div className="space-y-2.5 py-1.5">
        <Button
          variant="outline"
          className="w-full h-auto py-2.5 px-3 justify-start text-left whitespace-normal border-amber-400/70 text-amber-100 bg-amber-950/30 hover:bg-amber-700/30"
          onClick={onPressOn} disabled={busy || !pressOnAvailable}
          data-testid="fail-press-on-btn"
        >
          <RotateCw className="h-4 w-4 mr-2 shrink-0" />
          <div className="flex-1">
            <div className="font-bold text-sm">
              Press On <span className="text-amber-300 text-[11px]">(once per investigation)</span>
            </div>
            <div className="text-[11.5px] text-amber-100/80 mt-0.5">
              {pressOnAvailable
                ? 'Retry the same beat at the cost of a complication.'
                : 'Already used this storyline.'}
            </div>
          </div>
        </Button>

        <Button
          variant="outline"
          className="w-full h-auto py-2.5 px-3 justify-start text-left whitespace-normal border-rose-400/70 text-rose-200 bg-rose-950/40 hover:bg-rose-700/30"
          onClick={onPushThrough} disabled={busy}
          data-testid="fail-push-through-btn"
        >
          <ArrowRight className="h-4 w-4 mr-2 shrink-0" />
          <div className="flex-1">
            <div className="font-bold text-sm">Push Through (fail forward)</div>
            <div className="text-[11.5px] text-rose-100/85 mt-0.5">
              The story moves on with the failure baked in. Your final reward will be reduced.
            </div>
          </div>
        </Button>

        <Button
          variant="outline"
          className="w-full h-auto py-2.5 px-3 justify-start text-left whitespace-normal border-fuchsia-400/70 text-fuchsia-200 bg-fuchsia-950/40 hover:bg-fuchsia-700/30"
          onClick={onCreative} disabled={busy}
          data-testid="fail-creative-btn"
        >
          <Wand2 className="h-4 w-4 mr-2 shrink-0" />
          <div className="flex-1">
            <div className="font-bold text-sm">Try a Different Approach</div>
            <div className="text-[11.5px] text-fuchsia-100/85 mt-0.5">
              Describe an alternative strategy. The DM will judge whether it works.
            </div>
          </div>
        </Button>
      </div>

      <div className="flex justify-end pt-1">
        <Button size="sm" variant="ghost" className="h-8 text-amber-200" onClick={onCancel} disabled={busy}>
          Cancel
        </Button>
      </div>
    </DialogContent>
  </Dialog>
);

const CreativeApproachDialog = ({ open, beat, busy, text, setText, onSubmit, onClose }) => (
  <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
    <DialogContent className="bg-stone-950 border-2 border-fuchsia-500/50 text-amber-50 max-w-lg" data-testid="creative-approach-dialog">
      <DialogHeader>
        <DialogTitle className="text-fuchsia-200 flex items-center gap-2">
          <Wand2 className="h-5 w-5" /> What do you do?
        </DialogTitle>
        <DialogDescription className="text-amber-100/90 italic font-serif pt-1">
          Describe your action in this scene. The DM will narrate the outcome and continue the story —
          a check only triggers if your action genuinely calls for one.
        </DialogDescription>
      </DialogHeader>

      <Textarea
        rows={5}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder='e.g. "I slip along the eastern wall toward the broken crate, watching for guards through the slats."'
        className="bg-stone-900 border-fuchsia-500/40 text-amber-50 placeholder:text-amber-100/40"
        data-testid="creative-approach-input"
        autoFocus
      />
      <div className="text-[11px] text-amber-100/70">
        Be specific about HOW you do it. Inventive thinking is rewarded; vague plans land partial outcomes.
      </div>

      <div className="flex justify-end gap-2 pt-1">
        <Button size="sm" variant="ghost" className="h-9 text-amber-200" onClick={onClose} disabled={busy}>
          Cancel
        </Button>
        <Button
          size="sm"
          className="h-9 bg-fuchsia-500 hover:bg-fuchsia-400 text-black font-bold"
          onClick={onSubmit} disabled={busy || !(text || '').trim()}
          data-testid="creative-submit-btn"
        >
          {busy ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Wand2 className="h-4 w-4 mr-1" />}
          Submit Action
        </Button>
      </div>
    </DialogContent>
  </Dialog>
);

const BeatCard = ({ beat, index, total, isActive, complication, pressOnUsed, campaignId, storylineId, onCorrectionApplied }) => {
  const c = colorsFor(beat.check_type);
  const tone = STATUS_TONE[beat.status] || STATUS_TONE.pending;
  const sealed = beat.status === 'pending';
  const resolved = ['passed', 'failed', 'skipped'].includes(beat.status);
  const hasComplication = isActive && !!(complication && complication.trim());

  return (
    <div
      className={`relative shrink-0 w-[270px] sm:w-[300px] rounded-lg border-2 overflow-hidden flex flex-col
        transition-transform duration-300
        ${isActive
          ? `${hasComplication ? 'border-rose-500/80 shadow-[0_0_24px_rgba(244,63,94,0.45)]' : c.border + ' shadow-xl'} bg-stone-800 scale-[1.04]`
          : sealed
            ? 'border-stone-600 bg-stone-900'
            : resolved
              ? `bg-stone-900 ${
                  beat.status === 'passed' ? 'border-emerald-500/40' :
                  beat.status === 'failed' ? 'border-rose-500/40' :
                  'border-amber-500/40'
                }`
              : 'border-stone-600 bg-stone-900 opacity-85'}`}
      data-testid={`beat-card-${index}`}
      data-beat-status={beat.status}
      data-has-complication={hasComplication ? '1' : '0'}
    >
      {/* Carry-forward complication ribbon (active card only) */}
      {hasComplication && (
        <div
          className="px-2.5 py-1.5 text-[11px] bg-rose-950/80 border-b border-rose-500/60 text-rose-100"
          data-testid="beat-complication-ribbon"
        >
          <div className="flex items-center gap-1.5 text-rose-300 uppercase tracking-wider font-bold text-[10px] mb-0.5">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
            {pressOnUsed ? 'Pressing On — Cost Paid' : 'Carrying Forward'}
          </div>
          <div className="italic font-serif text-rose-50 leading-snug line-clamp-3">
            {complication}
          </div>
        </div>
      )}

      <div
        className={`flex items-center justify-between px-2.5 py-1.5 text-[11px] uppercase tracking-wider border-b
          ${sealed ? 'bg-stone-800 border-stone-700 text-stone-300' : 'bg-stone-700 border-stone-500 text-amber-50 font-semibold'}`}
      >
        <span className="font-bold">{sealed ? `Beat ${index + 1}` : beat.check_type}</span>
        {sealed ? (
          <span className="px-1.5 py-0.5 rounded border font-bold border-stone-500 text-stone-200 bg-stone-900">
            DC {beat.dc}
          </span>
        ) : (Number(beat.dc) > 0 && !beat.roll_optional) ? (
          <span className={`px-1.5 py-0.5 rounded border font-bold ${c.chip}`}>
            DC {beat.dc}
          </span>
        ) : (
          <span
            className="px-1.5 py-0.5 rounded border font-bold border-emerald-400/70 text-emerald-100 bg-emerald-950/60"
            title="No roll required — the information is openly visible"
            data-testid="beat-no-roll-chip"
          >
            OPEN
          </span>
        )}
      </div>
      <div className="flex-1 px-3 py-3 flex flex-col gap-2">
        {sealed ? (
          <div className="flex-1 flex flex-col items-center justify-center text-stone-300 py-6">
            <Lock className="h-8 w-8 mb-2 text-stone-400" />
            <div className="text-[12px] tracking-widest uppercase font-bold text-stone-200">Sealed</div>
            <div className="text-[11px] text-stone-400 mt-0.5">Beat {index + 1} of {total}</div>
          </div>
        ) : (
          <>
            <div className="text-amber-50 font-bold text-[17px] leading-tight">
              {beat.title || (resolved ? 'Resolved beat' : 'New scene')}
            </div>

            {/* Knowledge beats: HIDE the description until the beat is resolved.
                Show the public-facing prompt + lock instead so the player
                doesn't see the answer before they roll. */}
            {beat.reveal_type === 'knowledge' && !resolved ? (
              <>
                <div className="rounded-md border-2 border-amber-400/70 bg-stone-900 p-3 text-center shadow-inner">
                  <Lock className="h-5 w-5 text-amber-200 mx-auto mb-1.5" />
                  <div className="text-[14px] text-amber-50 italic font-serif leading-snug font-medium">
                    {beat.prompt || `Roll ${beat.check_type} (DC ${beat.dc}) to reveal what you can piece together.`}
                  </div>
                  {Array.isArray(beat.targets) && beat.targets.length > 0 && (
                    <div className="mt-2 flex flex-wrap justify-center gap-1.5">
                      {beat.targets.slice(0, 3).map((t, ti) => (
                        <span
                          key={ti}
                          className="px-2 py-0.5 rounded bg-amber-500 border border-amber-300 text-[11px] uppercase tracking-wide text-stone-950 font-bold"
                        >
                          {t.type}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                {/* Pitch input — only social knowledge beats. The DM judges
                    the pitch, adjusts the DC, then the player rolls. */}
                {isActive && campaignId && storylineId && (
                  <PitchInput
                    campaignId={campaignId}
                    storylineId={storylineId}
                    beat={beat}
                    beatIndex={index}
                    onAdjusted={onCorrectionApplied}
                  />
                )}
              </>
            ) : beat.reveal_type === 'knowledge' && beat.status === 'failed' ? (
              <div className="rounded-md border-2 border-rose-400/70 bg-stone-900 p-3">
                <div className="flex items-center gap-1.5 text-rose-200 text-[11px] uppercase tracking-wider font-bold mb-1">
                  <Lock className="h-3 w-3" /> Sealed Lead
                </div>
                <div className="text-[14px] text-amber-50 italic font-serif leading-snug">
                  You couldn't piece it together. The lead is now in your deck — find someone who can help.
                </div>
              </div>
            ) : (
              <div
                className={`text-[14.5px] text-amber-50 italic font-serif leading-relaxed ${
                  isActive || resolved
                    ? 'overflow-y-auto pr-1 max-h-[260px] sm:max-h-[320px]'
                    : 'line-clamp-6'
                }`}
                data-testid={isActive ? 'beat-description-active' : (resolved ? `beat-description-resolved-${index}` : undefined)}
              >
                {beat.description || (
                  resolved
                    ? <span className="not-italic text-amber-200/80">— {beat.outcome_text || 'No revelation recorded.'}</span>
                    : ''
                )}
              </div>
            )}

            {/* Action beats with a SOCIAL check (Persuasion / Deception /
                Intimidation / Performance) — the player can also pitch
                what they say to adjust the DC before rolling. Knowledge
                beats already render PitchInput inside the locked panel
                above. */}
            {!resolved && isActive && beat.reveal_type !== 'knowledge'
              && Number(beat.dc) > 0 && campaignId && storylineId && (
              <PitchInput
                campaignId={campaignId}
                storylineId={storylineId}
                beat={beat}
                beatIndex={index}
                onAdjusted={onCorrectionApplied}
              />
            )}

            {beat.outcome_text && (
              <div className="mt-1 text-[13px] text-amber-200 border-l-2 border-amber-400/70 pl-2 italic">
                {beat.outcome_text}
              </div>
            )}
          </>
        )}
      </div>
      {/* "Ask the DM" button — only visible on the active beat or
          recently-resolved beats so the player can contest a missed check
          right when it matters. */}
      {!sealed && campaignId && storylineId && (isActive || resolved) && (
        <div className="px-2 pb-1.5 flex justify-end">
          <DMFeedbackButton
            campaignId={campaignId}
            storylineId={storylineId}
            beatIndex={index}
            onCorrectionApplied={onCorrectionApplied}
          />
        </div>
      )}
      <div
        className={`flex items-center gap-1.5 px-2.5 py-1.5 text-[10.5px] uppercase tracking-wider border-t font-bold
          ${sealed ? 'bg-stone-800 border-stone-700 text-stone-300' : 'bg-stone-800 border-stone-600 text-amber-50'}`}
      >
        <span className={`w-2 h-2 rounded-full ${tone.dot}`} />
        <span>{tone.label}</span>
        <div className="flex-1" />
        <span className="text-amber-100/90">{index + 1}/{total}</span>
      </div>
      {resolved && (
        <div
          className={`pointer-events-none absolute top-1.5 right-1.5 z-10
            ${beat.status === 'passed' ? 'text-emerald-300' :
              beat.status === 'failed' ? 'text-rose-300' : 'text-amber-300'}`}
          data-testid={`beat-resolved-stamp-${beat.status}`}
        >
          <span className={`text-[10px] font-black uppercase tracking-widest -rotate-6 inline-block
            border-2 border-current px-1.5 py-0.5 rounded
            ${beat.status === 'passed' ? 'bg-emerald-950/80' :
              beat.status === 'failed' ? 'bg-rose-950/80' : 'bg-amber-950/80'}`}>
            {beat.status}
          </span>
        </div>
      )}
    </div>
  );
};

export const StorylineRewardModal = ({ open, reward, onClose }) => {
  if (!reward) return null;
  return (
    <Dialog open={!!open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="bg-stone-950 border-amber-500/40 text-amber-100 max-w-md" data-testid="storyline-reward-modal">
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
          <div className="flex items-center gap-2 flex-wrap" data-testid="reward-xp">
            <Badge className="bg-amber-500 text-black px-3 py-1 text-sm">+ {reward.xp} XP</Badge>
            {(reward.passed != null && reward.failed != null) && (
              <Badge variant="outline" className="border-amber-300/40 text-amber-100/80">
                {reward.passed} passed · {reward.failed} failed
              </Badge>
            )}
            {reward.tone && (
              <Badge variant="outline" className="border-amber-300/40 text-amber-100/80">
                tone · {reward.tone}
              </Badge>
            )}
          </div>

          {reward.item ? (
            <div className="rounded-md border border-amber-500/30 bg-stone-900/80 p-3" data-testid="reward-item">
              <div className="flex items-center gap-2">
                <Scroll className="h-4 w-4 text-amber-300" />
                <span className="font-semibold text-amber-100">{reward.item.name}</span>
                <Badge variant="outline" className="text-[10px] border-amber-300/40 text-amber-100/70 ml-auto">
                  {reward.item.kind || 'item'}
                </Badge>
              </div>
              <p className="text-[12.5px] text-amber-100/80 mt-1.5 leading-snug">{reward.item.description}</p>
            </div>
          ) : (
            <div className="text-[12px] text-amber-100/65 italic">
              No item this run — too many threads slipped through your fingers.
            </div>
          )}
        </div>

        <div className="flex justify-end pt-1">
          <Button size="sm" className="bg-amber-600 hover:bg-amber-500 text-black" onClick={onClose} data-testid="reward-close-btn">
            Continue
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ActiveInvestigationPanel;
