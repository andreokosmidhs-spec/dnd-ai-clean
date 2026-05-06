import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { Badge } from '../components/ui/badge';
import { Loader2, Eye, X } from 'lucide-react';
import { eventTypeMeta } from '../utils/eventTypes';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * CampaignDeckPreview — modal showing the campaign event deck for the
 * currently-selected Tone/Focus/Scope/Danger intent. Auto-refreshes on
 * intent change so the player can see how their picks reshape the deck
 * before locking in.
 *
 * The deck shown here is the affinity-weighted top of the catalog. When
 * the campaign is generated, the world graph filters this same deck by
 * each region's biome + present factions + dominant races to draft the
 * actual events the DM uses.
 */
const CampaignDeckPreview = ({ open, onOpenChange, intent }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open || !intent) return;
    const ctrl = new AbortController();
    setLoading(true);
    setData(null);
    const params = new URLSearchParams({
      tone: intent.tone || 'Balanced',
      focus: intent.focus || 'Story',
      scope: intent.scope || 'Mixed',
      danger: intent.danger || 'Medium',
    });
    fetch(`${BACKEND_URL}/api/campaigns/deck-preview?${params}`, { signal: ctrl.signal })
      .then((r) => r.json())
      .then((d) => setData(d))
      .catch(() => {})
      .finally(() => setLoading(false));
    return () => ctrl.abort();
  }, [open, intent?.tone, intent?.focus, intent?.scope, intent?.danger]);

  const counts = data?.type_counts || {};
  const cards = data?.cards || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="bg-stone-950 border-2 border-amber-500/40 text-amber-50 max-w-3xl max-h-[85vh] overflow-y-auto"
        data-testid="campaign-deck-preview"
      >
        <DialogHeader>
          <DialogTitle className="text-amber-300 flex items-center gap-2">
            <Eye className="h-5 w-5" />
            Campaign Deck Preview
          </DialogTitle>
          <DialogDescription className="text-amber-100/85">
            Top {data?.total_in_deck || '…'} of {data?.total_in_catalog || '…'} catalog templates
            will be available to the DM under your current Tone / Focus / Scope / Danger picks.
            Region biome + present factions + dominant races filter this further when each region's
            event deck gets drafted.
          </DialogDescription>
        </DialogHeader>

        {/* Selected intent chips */}
        <div className="flex flex-wrap gap-1.5 mt-1">
          {['tone', 'focus', 'scope', 'danger'].map((k) => (
            <Badge
              key={k}
              variant="outline"
              className="text-[11px] border-amber-400/40 bg-amber-950/30 text-amber-100"
            >
              <span className="opacity-70 mr-1 capitalize">{k}:</span>
              {intent?.[k] || '—'}
            </Badge>
          ))}
        </div>

        {/* Counts by type */}
        {!loading && cards.length > 0 && (
          <div className="mt-3">
            <p className="text-[11px] uppercase tracking-wider text-stone-300/70 mb-1.5">
              Deck Composition
            </p>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(counts)
                .sort((a, b) => b[1] - a[1])
                .map(([type, n]) => {
                  const meta = eventTypeMeta(type);
                  return (
                    <Badge
                      key={type}
                      className={`text-[10px] ${meta.chipBg} ${meta.chipText} border-0 px-1.5 py-0.5`}
                    >
                      <span className="mr-1" aria-hidden="true">{meta.icon}</span>
                      {meta.label} · {n}
                    </Badge>
                  );
                })}
            </div>
          </div>
        )}

        {/* Card list */}
        <div className="mt-3 space-y-2">
          {loading && (
            <div className="text-stone-300/80 italic flex items-center gap-2 py-6 justify-center text-sm">
              <Loader2 className="h-4 w-4 animate-spin" /> Counting the deck…
            </div>
          )}

          {!loading && cards.length === 0 && (
            <div className="text-stone-300/80 italic text-sm text-center py-6">
              No cards match this combination — try a different intent.
            </div>
          )}

          {!loading && cards.map((c, i) => {
            const meta = eventTypeMeta(c.type);
            const reqText = (c.requires || [])
              .map((t) => {
                if (t.startsWith('faction:')) return `🏛️ ${t.replace('faction:', '')}`;
                if (t.startsWith('race:')) return `🪶 ${t.replace('race:', '')}`;
                return t;
              })
              .join(' · ');
            return (
              <div
                key={`${c.type}-${i}`}
                className={`rounded-md p-2.5 bg-stone-900/70 ${meta.borderClass} ${meta.ringClass}`}
                data-testid={`deck-preview-card-${i}`}
              >
                <div className="flex items-center gap-1.5 flex-wrap">
                  <Badge className={`text-[10px] ${meta.chipBg} ${meta.chipText} border-0 px-1.5 py-0`}>
                    <span className="mr-1" aria-hidden="true">{meta.icon}</span>
                    {meta.label}
                  </Badge>
                  <Badge
                    variant="outline"
                    className={`text-[10px] border-stone-500/50 text-stone-200 capitalize ${
                      c.difficulty === 'hard' ? 'border-red-500/60 text-red-200' :
                      c.difficulty === 'easy' ? 'border-emerald-500/40 text-emerald-200' : ''
                    }`}
                  >
                    {c.difficulty}
                  </Badge>
                  <Badge
                    variant="outline"
                    className="text-[10px] border-amber-500/40 text-amber-200 bg-amber-950/30"
                    title="Affinity weight under your current intent"
                  >
                    aff {c.affinity}
                  </Badge>
                </div>
                <h5 className={`mt-1 text-sm font-semibold ${meta.accent}`}>{c.title}</h5>
                <p className="text-[12px] text-amber-100/85 mt-1 leading-snug">{c.description}</p>
                {(c.biomes?.length > 0 || reqText) && (
                  <p className="mt-1.5 text-[10px] italic text-stone-300/70">
                    {c.biomes?.length > 0 && (
                      <>biomes: {(c.biomes || []).join(', ')}</>
                    )}
                    {reqText && <> · requires: {reqText}</>}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default CampaignDeckPreview;
