/**
 * CanonBar — slim always-visible anchor strip at the top of the Adventure
 * Log. Shows the player WHICH canon scene the DM is currently anchored to.
 * Click expands into the full CanonTimelinePanel.
 *
 * Auto-updates on:
 *   - mount / campaignId change
 *   - `rpg:canon-updated` window event (dispatched from ActiveInvestigationPanel
 *     after a passed beat creates a new checkpoint)
 *
 * Empty state: gentle prompt encouraging the player to pass a check.
 */
import React, { useEffect, useState, useCallback } from 'react';
import { Anchor, Scroll, ChevronRight } from 'lucide-react';
import CanonTimelinePanel from './CanonTimelinePanel';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const CanonBar = ({ campaignId }) => {
  const [current, setCurrent] = useState(null);
  const [timelineOpen, setTimelineOpen] = useState(false);

  const fetchCurrent = useCallback(async () => {
    if (!campaignId) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/canon/current`);
      if (!res.ok) return;
      const data = await res.json();
      setCurrent(data || null);
    } catch {
      // Silent — empty state will render
    }
  }, [campaignId]);

  useEffect(() => { fetchCurrent(); }, [fetchCurrent]);

  // Refresh when a new canon scene gets minted elsewhere in the app.
  useEffect(() => {
    const onCanonUpdate = () => fetchCurrent();
    window.addEventListener('rpg:canon-updated', onCanonUpdate);
    return () => window.removeEventListener('rpg:canon-updated', onCanonUpdate);
  }, [fetchCurrent]);

  if (!campaignId) return null;

  return (
    <>
      <button
        onClick={() => setTimelineOpen(true)}
        className={`group w-full flex items-center gap-3 px-3 py-2 border-b transition-all
          ${current
            ? 'bg-emerald-950/30 border-emerald-500/30 hover:bg-emerald-950/50 hover:border-emerald-500/50'
            : 'bg-stone-900/60 border-stone-700/40 hover:bg-stone-900 hover:border-amber-500/30'}
        `}
        data-testid="canon-bar"
        aria-label={current ? `Current scene: ${current.title}` : 'No canon scene yet'}
      >
        {current ? (
          <>
            <div className="shrink-0 w-7 h-7 rounded-full border-2 border-emerald-400 bg-emerald-600 text-stone-950 font-bold flex items-center justify-center text-xs">
              {current.scene_number}
            </div>
            <Anchor className="h-3.5 w-3.5 text-emerald-300 shrink-0" />
            <div className="flex-1 min-w-0 text-left">
              <div className="text-[10px] uppercase tracking-[0.18em] text-emerald-400 font-bold leading-none">
                Current canon
              </div>
              <div className="text-emerald-50 font-bold text-sm truncate leading-tight mt-0.5">
                {current.title}
              </div>
            </div>
            {current.check_passed?.check_type && Number(current.check_passed?.dc) > 0 && (
              <span
                className="hidden sm:inline-flex text-[10px] px-2 py-0.5 rounded-full border border-emerald-400/50 text-emerald-200 bg-stone-950/60 shrink-0"
                data-testid="canon-bar-check-chip"
              >
                {current.check_passed.check_type} DC {current.check_passed.dc}
              </span>
            )}
            <ChevronRight className="h-4 w-4 text-emerald-300/70 group-hover:text-emerald-200 group-hover:translate-x-0.5 transition-all shrink-0" />
          </>
        ) : (
          <>
            <Scroll className="h-4 w-4 text-stone-500 shrink-0" />
            <div className="flex-1 min-w-0 text-left">
              <div className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-bold leading-none">
                No canon yet
              </div>
              <div className="text-stone-400 text-sm italic truncate leading-tight mt-0.5">
                Pass a check to lock in your first scene
              </div>
            </div>
            <ChevronRight className="h-4 w-4 text-stone-500 group-hover:text-amber-300 transition-colors shrink-0" />
          </>
        )}
      </button>

      <CanonTimelinePanel
        open={timelineOpen}
        onClose={() => setTimelineOpen(false)}
        campaignId={campaignId}
      />
    </>
  );
};

export default CanonBar;
