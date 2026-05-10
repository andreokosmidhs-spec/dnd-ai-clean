/**
 * PitchInput — inline textarea + "Pitch & Set DC" button shown on social
 * knowledge beats (Persuasion / Deception / Intimidation / Performance).
 * The player types what they actually say or do; the backend judge sizes
 * up the pitch quality and adjusts the beat's DC up or down.
 *
 * The adjusted DC is stamped on the beat, so when the player rolls (via
 * Dice or Skip · Proceed) the result lands against the new DC. They can
 * revise the pitch up until they roll; each submit reanchors from the
 * original base DC, so a brilliant follow-up after a clumsy first try is
 * judged on its own merits.
 */
import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Loader2, Sparkles, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const SOCIAL_CHECKS = new Set([
  'Persuasion', 'Deception', 'Intimidation', 'Performance', 'Insight',
]);

const QUALITY_STYLE = {
  brilliant: 'bg-emerald-950/60 border-emerald-400 text-emerald-100',
  smart:     'bg-emerald-950/40 border-emerald-500/60 text-emerald-100',
  neutral:   'bg-stone-900 border-stone-600 text-amber-100',
  weak:      'bg-amber-950/40 border-amber-500/60 text-amber-100',
  foolish:   'bg-rose-950/40 border-rose-500/60 text-rose-100',
};

const MOD_LABEL = (mod) => (mod === 0 ? '±0' : (mod > 0 ? `+${mod}` : `${mod}`));

export const PitchInput = ({ campaignId, storylineId, beat, beatIndex, onAdjusted }) => {
  const [pitch, setPitch] = useState(beat?.pitch_text || '');
  const [busy, setBusy] = useState(false);
  const adj = beat?.dc_adjustment || null;

  const submit = async () => {
    const text = pitch.trim();
    if (text.length < 8) {
      toast.error('Say a bit more — give the DM something to size up.');
      return;
    }
    setBusy(true);
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/storylines/${storylineId}/adjust-dc`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ beat_index: beatIndex, approach_text: text }),
        }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `DC adjust failed (${res.status})`);
      }
      const data = await res.json();
      if (onAdjusted) onAdjusted(data.storyline);
      const j = data.judgment;
      const tone = j.modifier <= 0 ? 'success' : 'info';
      toast[tone === 'success' ? 'success' : 'info'](
        `${j.quality.toUpperCase()} pitch · DC ${j.adjusted_dc} (${MOD_LABEL(j.modifier)})`
      );
    } catch (e) {
      toast.error(e.message || 'Could not reach the DM.');
    } finally {
      setBusy(false);
    }
  };

  // Don't render for non-social checks — only social beats benefit from a
  // pitch (you can't really "smart-pitch" your way to a higher Investigation
  // roll). Stealth / Investigation / Athletics keep the standard flow.
  if (!SOCIAL_CHECKS.has(beat?.check_type)) return null;

  return (
    <div className="mt-2 space-y-2 rounded-md border border-amber-400/30 bg-stone-950/60 p-2.5">
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.18em] text-amber-300 font-bold">
        <Sparkles className="h-3 w-3" />
        Speak first — the DM sets the DC after hearing you out
      </div>
      <Textarea
        value={pitch}
        onChange={(e) => setPitch(e.target.value)}
        placeholder='e.g. "I tell him I know about his sister, slide a purse of 50gp across, and ask for the name."'
        className="bg-stone-900 border-stone-700 text-amber-50 placeholder:text-stone-500 min-h-[68px] text-[13px] leading-snug"
        data-testid="pitch-input-textarea"
        disabled={busy}
      />

      {adj && (
        <div
          className={`rounded border px-2.5 py-1.5 text-[12px] flex items-start gap-2 ${QUALITY_STYLE[adj.quality] || QUALITY_STYLE.neutral}`}
          data-testid="pitch-judgment"
        >
          <div className="flex flex-col items-center min-w-[58px]">
            <span className="text-[9px] uppercase font-bold tracking-wider opacity-80">DC</span>
            <span className="text-2xl font-black leading-none">{adj.adjusted_dc}</span>
            <span className="text-[10px] font-bold opacity-90">
              base {adj.base_dc} · {MOD_LABEL(adj.modifier)}
            </span>
          </div>
          <div className="flex-1 leading-snug">
            <div className="text-[10px] uppercase tracking-wider font-bold opacity-90 mb-0.5">
              {adj.quality} pitch
            </div>
            <div className="italic font-serif">{adj.rationale}</div>
          </div>
        </div>
      )}

      <div className="flex justify-end gap-1.5">
        <Button
          size="sm"
          variant="ghost"
          onClick={submit}
          disabled={busy || pitch.trim().length < 8}
          className="h-8 text-[12px] bg-amber-600 hover:bg-amber-500 text-stone-950 font-bold border border-amber-300"
          data-testid="pitch-submit-btn"
        >
          {busy ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
          ) : adj ? (
            <RefreshCw className="h-3.5 w-3.5 mr-1" />
          ) : (
            <Sparkles className="h-3.5 w-3.5 mr-1" />
          )}
          {adj ? 'Revise pitch' : 'Pitch & Set DC'}
        </Button>
      </div>
    </div>
  );
};

export default PitchInput;
