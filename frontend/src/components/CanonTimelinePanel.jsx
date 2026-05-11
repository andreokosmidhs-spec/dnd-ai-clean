/**
 * CanonTimelinePanel — chronological list of "canon scenes": beats the
 * player passed and locked in as immutable truth. The DM is told never to
 * contradict these. The most recent scene is the DM's current anchor.
 *
 * Opens from the DM Notebook → Canon Timeline button (or directly via
 * keyboard if wired). Read-only — canon is earned, not edited.
 */
import React, { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { X, Anchor, Scroll, ShieldCheck, Loader2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const CanonSceneCard = ({ scene, isCurrent }) => {
  const cp = scene.check_passed || null;
  return (
    <div
      className={`rounded-lg border-2 p-4 bg-gradient-to-br from-stone-900 via-stone-900 to-amber-950/30 shadow-inner shadow-amber-900/30 ${
        isCurrent
          ? 'border-emerald-500/60 ring-1 ring-emerald-400/30'
          : 'border-amber-500/30'
      }`}
      data-testid={`canon-scene-${scene.scene_number}`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`shrink-0 w-10 h-10 rounded-full border-2 flex items-center justify-center font-bold ${
            isCurrent
              ? 'border-emerald-300 bg-emerald-600 text-stone-950'
              : 'border-amber-500/60 bg-stone-950 text-amber-200'
          }`}
        >
          {scene.scene_number}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h4 className="font-bold text-base text-amber-50 font-serif">
              {scene.title}
            </h4>
            {isCurrent && (
              <span className="text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded-full border border-emerald-300 bg-emerald-600 text-stone-950 flex items-center gap-1">
                <Anchor className="h-3 w-3" /> Current anchor
              </span>
            )}
            {cp?.check_type && Number(cp.dc) > 0 && (
              <span className="text-[10px] px-2 py-0.5 rounded-full border border-amber-500/50 text-amber-200 bg-stone-950/60 flex items-center gap-1">
                <ShieldCheck className="h-3 w-3" />
                {cp.check_type} DC {cp.dc}
                {cp.roll_total != null && <span className="opacity-70"> · roll {cp.roll_total}</span>}
              </span>
            )}
          </div>
          {scene.storyline_title && (
            <div className="text-[11px] text-amber-300/70 italic mt-0.5">
              from "{scene.storyline_title}"
            </div>
          )}
          <p className="mt-2 text-sm leading-relaxed italic font-serif text-amber-50/90 tracking-wide">
            {scene.summary}
          </p>
          {scene.facts && scene.facts.length > 0 && (
            <ul className="mt-3 space-y-1">
              {scene.facts.slice(0, 5).map((f, i) => (
                <li key={i} className="text-[12px] text-amber-100/85 flex gap-2 leading-snug font-serif">
                  <span className="text-amber-400 shrink-0">•</span>
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          )}
          {scene.pitch_text && (
            <div className="mt-2 text-[11px] text-amber-200/70 italic border-l-2 border-amber-500/40 pl-2">
              Your pitch: "{scene.pitch_text}"
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const CanonTimelinePanel = ({ open, onClose, campaignId }) => {
  const [scenes, setScenes] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchScenes = useCallback(async () => {
    if (!campaignId) return;
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/canon`);
      if (!res.ok) throw new Error(`Load failed: ${res.status}`);
      const data = await res.json();
      setScenes(data.scenes || []);
    } catch (e) {
      toast.error(e.message || 'Could not load canon');
    } finally {
      setLoading(false);
    }
  }, [campaignId]);

  useEffect(() => {
    if (open) fetchScenes();
  }, [open, fetchScenes]);

  if (!open) return null;

  const currentId = scenes.find((s) => s.is_current)?.id || (scenes[0] || {}).id;

  return (
    <div
      className="fixed inset-0 z-[130] bg-stone-950/85 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
      data-testid="canon-timeline-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Canon Timeline"
    >
      <div
        className="relative w-full max-w-3xl max-h-[90vh] rounded-xl border-2 border-amber-500/70 bg-stone-950 shadow-[0_0_60px_rgba(245,158,11,0.35)] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
        data-testid="canon-timeline-panel"
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-amber-500/30 bg-stone-900">
          <div className="flex items-center gap-3">
            <Scroll className="h-6 w-6 text-amber-300" />
            <div>
              <div className="text-[11px] uppercase tracking-[0.2em] text-amber-400 font-bold">
                Locked-In Truth
              </div>
              <div className="text-amber-50 font-bold text-lg">Canon Timeline</div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-stone-400 hover:text-amber-100 transition-colors"
            aria-label="Close canon timeline"
            data-testid="canon-timeline-close-btn"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="px-5 py-3 border-b border-amber-500/20 bg-stone-900/50">
          <p className="text-amber-100/90 text-xs leading-relaxed italic font-serif">
            Every check you pass becomes a locked-in scene — the DM treats these
            as immutable truth. The current scene is the DM's anchor; new
            narration always flows from it. If the DM contradicts canon, flag
            it via DM Feedback and the system will rewind to the right scene.
          </p>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {loading ? (
            <div className="text-stone-400 text-center py-8" data-testid="canon-timeline-loading">
              <Loader2 className="h-5 w-5 inline-block animate-spin mr-2" />
              Loading canon…
            </div>
          ) : scenes.length === 0 ? (
            <div className="text-center py-12 px-6 text-stone-400" data-testid="canon-timeline-empty">
              <Anchor className="h-10 w-10 mx-auto mb-3 text-stone-600" />
              <p className="text-sm italic">
                No canon yet. Pass a check to lock in your first scene.
              </p>
              <p className="text-[11px] mt-2 text-stone-500">
                When you succeed a roll or a creative approach, the moment becomes
                permanent — the DM can never contradict it.
              </p>
            </div>
          ) : (
            scenes.map((scene) => (
              <CanonSceneCard
                key={scene.id}
                scene={scene}
                isCurrent={scene.id === currentId}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default CanonTimelinePanel;
