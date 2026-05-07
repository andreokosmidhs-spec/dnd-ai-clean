/**
 * DMFeedbackButton — small "Ask the DM" widget that lives on each beat
 * card. Lets the player contest a missed/wrong check call, ask "why no
 * check?", or freeform note. The judge response renders inline so the
 * player sees the DM's reasoning + the corrective beat (if any) in real
 * time. The judge's ruling is also persisted server-side so future DM
 * turns apply the same logic.
 */
import React, { useState } from 'react';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { Gavel, Loader2, MessageCircleQuestion, Check, X } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const FEEDBACK_KINDS = [
  { key: 'missed_check',  label: 'You missed a check', hint: 'I tried something that should have required a roll' },
  { key: 'why_no_check',  label: 'Why no check?',      hint: 'Explain your reasoning' },
  { key: 'wrong_check',   label: 'Wrong check / DC',   hint: 'This is the wrong skill or difficulty' },
  { key: 'general',       label: 'Freeform note',      hint: 'Any other DM feedback' },
];

const SUGGESTED_CHECKS = [
  'Stealth', 'Deception', 'Performance', 'Intimidation', 'Persuasion',
  'Insight', 'Athletics', 'Acrobatics', 'Perception', 'Investigation',
  'Sleight of Hand', 'Arcana', 'History', 'Nature', 'Religion', 'Survival',
];

export const DMFeedbackButton = ({ campaignId, storylineId, beatIndex, onCorrectionApplied }) => {
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState('missed_check');
  const [check, setCheck] = useState('');
  const [dc, setDc] = useState('');
  const [action, setAction] = useState('');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [judgment, setJudgment] = useState(null);

  const reset = () => {
    setKind('missed_check'); setCheck(''); setDc(''); setAction(''); setNote('');
    setJudgment(null); setBusy(false);
  };

  const submit = async () => {
    if (kind === 'missed_check' && !action.trim()) {
      toast.error('Tell the DM what you actually tried to do.');
      return;
    }
    setBusy(true);
    try {
      const body = {
        kind,
        suggested_check: check || null,
        suggested_dc: dc ? Number(dc) : null,
        player_action: action || null,
        note: note || null,
        beat_index: typeof beatIndex === 'number' ? beatIndex : null,
        apply_correction: kind !== 'why_no_check', // 'why_no_check' is purely informational
      };
      const res = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/storylines/${storylineId}/dm-feedback`,
        { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
      );
      if (!res.ok) throw new Error(`Feedback submission failed: ${res.status}`);
      const data = await res.json();
      setJudgment(data.judgment);
      if (data.correction_applied && onCorrectionApplied) {
        onCorrectionApplied(data.storyline);
        toast.success('DM agreed — corrective check added.');
      } else if (data.judgment?.agrees_with_player) {
        toast.success('DM agreed with you.');
      } else {
        toast('DM explained their reasoning.', { duration: 4000 });
      }
    } catch (e) {
      toast.error(e.message || 'Could not reach the DM.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Button
        size="sm"
        variant="ghost"
        className="h-7 px-2 text-[10px] text-amber-200/80 hover:text-amber-50 hover:bg-amber-900/30 border border-amber-400/30 gap-1"
        onClick={() => { reset(); setOpen(true); }}
        title="Ask the DM about this beat or contest a missed check"
        data-testid="dm-feedback-button"
      >
        <MessageCircleQuestion className="h-3 w-3" />
        Ask the DM
      </Button>

      <Dialog open={open} onOpenChange={(o) => { if (!o) reset(); setOpen(o); }}>
        <DialogContent
          className="bg-stone-950 border-2 border-amber-500/60 max-w-lg"
          data-testid="dm-feedback-dialog"
        >
          <DialogHeader>
            <DialogTitle className="text-amber-50 flex items-center gap-2">
              <Gavel className="h-5 w-5 text-amber-300" /> DM Feedback
            </DialogTitle>
            <DialogDescription className="text-stone-400">
              Train the DM. If you tried something the rules require a check for, flag
              it here — the judge weighs in and can rewind so you can roll properly.
            </DialogDescription>
          </DialogHeader>

          {!judgment ? (
            <div className="space-y-4">
              {/* Kind picker */}
              <div className="space-y-1.5">
                <div className="text-[10px] uppercase tracking-wider text-amber-300 font-bold">
                  What's the issue?
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {FEEDBACK_KINDS.map((k) => (
                    <button
                      key={k.key}
                      onClick={() => setKind(k.key)}
                      className={`text-left rounded-md border-2 px-3 py-2 transition-all
                        ${kind === k.key
                          ? 'border-amber-400 bg-amber-950/50'
                          : 'border-stone-700 bg-stone-900 hover:border-amber-500/40'}`}
                      data-testid={`feedback-kind-${k.key}`}
                    >
                      <div className={`text-sm font-bold ${kind === k.key ? 'text-amber-50' : 'text-amber-100'}`}>
                        {k.label}
                      </div>
                      <div className="text-[11px] text-stone-400 mt-0.5">{k.hint}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* What did you actually try? */}
              {kind !== 'why_no_check' && (
                <div className="space-y-1.5">
                  <div className="text-[10px] uppercase tracking-wider text-amber-300 font-bold">
                    What did you actually try? (be specific)
                  </div>
                  <Textarea
                    value={action}
                    onChange={(e) => setAction(e.target.value)}
                    placeholder='e.g. "I pretended not to see Kellan and walked past the stalls to lure him close, then planned to surprise him from behind"'
                    className="bg-stone-900 border-stone-700 text-amber-50 placeholder:text-stone-500 min-h-[80px]"
                    data-testid="feedback-action-input"
                  />
                </div>
              )}

              {/* Suggested check + DC */}
              {kind !== 'why_no_check' && (
                <div className="grid grid-cols-3 gap-2">
                  <div className="col-span-2 space-y-1.5">
                    <div className="text-[10px] uppercase tracking-wider text-amber-300 font-bold">
                      Suggested check (optional)
                    </div>
                    <select
                      value={check}
                      onChange={(e) => setCheck(e.target.value)}
                      className="w-full h-9 rounded bg-stone-900 border border-stone-700 text-amber-50 px-2 text-sm focus:border-amber-400 focus:outline-none"
                      data-testid="feedback-check-select"
                    >
                      <option value="">— let the DM decide —</option>
                      {SUGGESTED_CHECKS.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <div className="text-[10px] uppercase tracking-wider text-amber-300 font-bold">
                      DC
                    </div>
                    <input
                      type="number"
                      value={dc}
                      onChange={(e) => setDc(e.target.value)}
                      placeholder="auto"
                      min={5} max={25}
                      className="w-full h-9 rounded bg-stone-900 border border-stone-700 text-amber-50 px-2 text-sm focus:border-amber-400 focus:outline-none"
                      data-testid="feedback-dc-input"
                    />
                  </div>
                </div>
              )}

              {/* Note */}
              <div className="space-y-1.5">
                <div className="text-[10px] uppercase tracking-wider text-amber-300 font-bold">
                  Anything else? (optional)
                </div>
                <Textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="extra context or your reasoning"
                  className="bg-stone-900 border-stone-700 text-amber-50 placeholder:text-stone-500 min-h-[60px]"
                  data-testid="feedback-note-input"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button variant="ghost" onClick={() => { reset(); setOpen(false); }} disabled={busy}>
                  Cancel
                </Button>
                <Button
                  onClick={submit}
                  disabled={busy}
                  className="bg-amber-600 hover:bg-amber-500 text-stone-950 font-bold border border-amber-300"
                  data-testid="feedback-submit-btn"
                >
                  {busy ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Gavel className="h-4 w-4 mr-1" />}
                  Submit to the DM
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-3" data-testid="dm-feedback-result">
              <div
                className={`flex items-center gap-2 px-3 py-2 rounded border-2 ${
                  judgment.agrees_with_player
                    ? 'bg-emerald-950/40 border-emerald-500/60 text-emerald-100'
                    : 'bg-rose-950/30 border-rose-500/40 text-rose-100'
                }`}
              >
                {judgment.agrees_with_player ? (
                  <><Check className="h-4 w-4" /><span className="font-bold">DM agrees with you.</span></>
                ) : (
                  <><X className="h-4 w-4" /><span className="font-bold">DM holds the call.</span></>
                )}
              </div>

              <div className="space-y-1.5">
                <div className="text-[10px] uppercase tracking-wider text-amber-300 font-bold">
                  Reasoning
                </div>
                <p className="text-amber-50 italic font-serif text-sm leading-relaxed">
                  {judgment.explanation}
                </p>
              </div>

              {judgment.check_type && judgment.dc != null && (
                <div className="space-y-1.5 border-t border-amber-500/20 pt-3">
                  <div className="text-[10px] uppercase tracking-wider text-amber-300 font-bold">
                    Ruling
                  </div>
                  <div className="text-amber-100 text-sm">
                    <span className="font-bold">{judgment.check_type}</span>
                    {' '}<span className="text-amber-300">DC {judgment.dc}</span>
                    {judgment.dc_reasoning && (
                      <span className="text-stone-400 italic"> — {judgment.dc_reasoning}</span>
                    )}
                  </div>
                </div>
              )}

              <div className="flex justify-end pt-2">
                <Button
                  onClick={() => setOpen(false)}
                  className="bg-amber-600 hover:bg-amber-500 text-stone-950 font-bold border border-amber-300"
                  data-testid="feedback-close-btn"
                >
                  Got it
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};

export default DMFeedbackButton;
