/**
 * AutoSaveIndicator — tiny status pip that pulses "Saved ✓" briefly
 * whenever the global `rpg:autosaved` event fires. Lives at the top of
 * the Adventure Log so the player has a constant signal that their
 * progress is safe. Falls silent after 2.5 seconds.
 *
 * Trigger the indicator from anywhere via:
 *   window.dispatchEvent(new CustomEvent('rpg:autosaved', { detail: { reason: 'action'|'event'|'scene' } }))
 */
import React, { useEffect, useState } from 'react';
import { Check, Loader2 } from 'lucide-react';

const REASON_LABEL = {
  action: 'Action saved',
  event: 'Event saved',
  scene: 'Scene saved',
  manual: 'Saved',
};

const AutoSaveIndicator = () => {
  const [state, setState] = useState({ visible: false, reason: 'manual', flashing: false });

  useEffect(() => {
    let hideTimer;
    let flashTimer;
    const onSave = (e) => {
      const reason = (e?.detail?.reason) || 'manual';
      clearTimeout(hideTimer);
      clearTimeout(flashTimer);
      setState({ visible: true, reason, flashing: true });
      // 250ms "flashing" → green check; 2.25s later → fade away.
      flashTimer = setTimeout(() => setState((s) => ({ ...s, flashing: false })), 250);
      hideTimer = setTimeout(() => setState((s) => ({ ...s, visible: false })), 2500);
    };
    window.addEventListener('rpg:autosaved', onSave);
    return () => {
      window.removeEventListener('rpg:autosaved', onSave);
      clearTimeout(hideTimer);
      clearTimeout(flashTimer);
    };
  }, []);

  if (!state.visible) return null;

  return (
    <div
      className={`inline-flex items-center gap-1 text-[10.5px] uppercase tracking-[0.18em] font-bold px-2 py-0.5 rounded-full border transition-opacity duration-500
        ${state.flashing
          ? 'border-amber-400/70 text-amber-100 bg-amber-950/60'
          : 'border-emerald-400/60 text-emerald-200 bg-emerald-950/40'}
      `}
      data-testid="autosave-indicator"
      role="status"
      aria-live="polite"
    >
      {state.flashing
        ? <Loader2 className="h-2.5 w-2.5 animate-spin" />
        : <Check className="h-2.5 w-2.5" />}
      <span>{REASON_LABEL[state.reason] || REASON_LABEL.manual}</span>
    </div>
  );
};

export default AutoSaveIndicator;
