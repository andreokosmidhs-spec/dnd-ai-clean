import React, { useEffect, useState, useCallback } from 'react';
import { Globe, Scroll, Eye, Flame, Hourglass } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from './ui/sheet';
import { Badge } from './ui/badge';
import WorldInfoPanel from './WorldInfoPanel';
import QuestLogPanel from './QuestLogPanel';
import CharacterDeck from './CharacterDeck';
import PausedThreadsPanel from './PausedThreadsPanel';
import api from '../api/axiosConfig';

/**
 * Compact top-bar with two pill buttons (Realm + Quests). Each opens a
 * right-side slide-over Sheet that hosts the full WorldInfoPanel /
 * QuestLogPanel content. Replaces the chunky inline collapsibles so the
 * narration scroll gets the vertical real-estate it deserves.
 */
const CampaignTopBar = ({
  worldBlueprint,
  currentLocation,
  quests = [],
  onUpdateQuestStatus,
  campaignId,
  worldState,
  characterId,
  characterName,
  onPausedThreadResumed,
}) => {
  const [realmOpen, setRealmOpen] = useState(false);
  const [questsOpen, setQuestsOpen] = useState(false);
  const [pausedOpen, setPausedOpen] = useState(false);
  const [pausedCount, setPausedCount] = useState(0);

  // Lightweight poll for the paused-thread count so the pill shows a live
  // badge even when the slide-over is closed. Refreshes when the sheet
  // closes (player just acted) and every 30s as a fallback.
  const refreshPausedCount = useCallback(async () => {
    if (!campaignId) return;
    try {
      const res = await api.get(`/api/campaigns/${campaignId}/storylines`);
      const list = res.data?.storylines || [];
      setPausedCount(list.filter((s) => s?.status === 'paused').length);
    } catch {
      // Non-fatal — leave the count at its previous value.
    }
  }, [campaignId]);

  useEffect(() => {
    refreshPausedCount();
    if (!campaignId) return undefined;
    const id = setInterval(refreshPausedCount, 30000);
    return () => clearInterval(id);
  }, [campaignId, refreshPausedCount]);

  useEffect(() => {
    if (!pausedOpen) refreshPausedCount();
  }, [pausedOpen, refreshPausedCount]);

  const realmLabel =
    worldBlueprint?.world_core?.name ||
    worldBlueprint?.starting_town?.name ||
    'Realm';
  const locationLabel =
    currentLocation || worldBlueprint?.starting_town?.name || null;
  const activeCount = quests.filter((q) => q.status === 'active').length;
  // Time-of-day chip: prefer the rich `time_bucket` object from the lean DM
  // response; fall back to legacy string `time_of_day` if that's all we have.
  const timeBucket = worldState?.time_bucket || (
    typeof worldState?.time_of_day === 'object' ? worldState.time_of_day : null
  );
  const timeLabel = timeBucket?.label || (
    typeof worldState?.time_of_day === 'string' && worldState.time_of_day
      ? worldState.time_of_day.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
      : null
  );
  const timeIcon = timeBucket?.icon || '🕰️';

  // Passive Perception chip — shows the character's PP score + tier so the
  // player can see at a glance how informative the DM's narration will be.
  const pp = worldState?.passive_perception || null;
  const ppLabel = (pp?.tier || '').replace(/^./, (c) => c.toUpperCase());
  const ppTierColor = {
    oblivious: 'border-stone-500/50 bg-stone-900/30 text-stone-200',
    average:   'border-sky-500/40 bg-sky-950/30 text-sky-100',
    sharp:     'border-cyan-500/50 bg-cyan-950/30 text-cyan-100',
    keen:      'border-emerald-500/50 bg-emerald-950/30 text-emerald-100',
    uncanny:   'border-fuchsia-500/60 bg-fuchsia-950/30 text-fuchsia-100',
  }[pp?.tier] || 'border-sky-500/40 bg-sky-950/30 text-sky-100';

  // Chaos meter — escalates color from emerald (calm) → rose (consuming).
  const chaos = worldState?.chaos || null;
  const chaosVal = Number.isFinite(chaos?.value) ? chaos.value : null;
  const chaosTier = chaos?.tier;
  const chaosTierColor = {
    calm:       'border-emerald-500/50 bg-emerald-950/30 text-emerald-100',
    stirring:   'border-lime-500/50 bg-lime-950/30 text-lime-100',
    agitated:   'border-amber-500/60 bg-amber-950/40 text-amber-100',
    turbulent:  'border-orange-500/70 bg-orange-950/40 text-orange-100',
    perilous:   'border-red-500/80 bg-red-950/45 text-red-100 animate-pulse',
    consuming:  'border-rose-500/90 bg-rose-950/55 text-rose-100 shadow-[0_0_14px_rgba(244,63,94,0.45)] animate-pulse',
  }[chaosTier?.key] || 'border-emerald-500/50 bg-emerald-950/30 text-emerald-100';

  const showRealm = !!worldBlueprint;
  const showQuests = !!campaignId;
  const showTime = !!timeLabel;
  const showPP = pp && Number.isFinite(pp.score);
  const showDeck = !!characterId;
  const showChaos = chaosVal !== null;

  if (!showRealm && !showQuests && !showTime && !showPP && !showDeck && !showChaos) return null;

  return (
    <div
      className="px-3 pt-3 flex items-center gap-2 flex-wrap"
      data-testid="campaign-top-bar"
    >
      {showRealm && (
        <Sheet open={realmOpen} onOpenChange={setRealmOpen}>
          <SheetTrigger asChild>
            <button
              type="button"
              data-testid="realm-button"
              className="group inline-flex items-center gap-2 rounded-full border border-blue-500/40 bg-blue-950/40 hover:bg-blue-900/50 hover:border-blue-400/60 transition-colors px-3 py-1.5 text-xs font-medium text-blue-100 shadow-sm"
            >
              <Globe size={14} className="text-blue-300" />
              <span className="max-w-[10rem] truncate">{realmLabel}</span>
              {locationLabel && (
                <span className="text-blue-300/70 hidden sm:inline">·</span>
              )}
              {locationLabel && (
                <span className="max-w-[8rem] truncate text-blue-300/80 hidden sm:inline">
                  {locationLabel}
                </span>
              )}
            </button>
          </SheetTrigger>
          <SheetContent
            side="right"
            className="w-full sm:max-w-md bg-gray-900 border-gray-700 text-white overflow-y-auto"
            data-testid="realm-sheet"
          >
            <SheetHeader>
              <SheetTitle className="text-blue-300 flex items-center gap-2">
                <Globe size={18} />
                {realmLabel}
              </SheetTitle>
              {locationLabel && (
                <p className="text-sm text-gray-400">{locationLabel}</p>
              )}
            </SheetHeader>
            <div className="mt-4">
              <WorldInfoPanel
                worldBlueprint={worldBlueprint}
                currentLocation={currentLocation}
                embedded
              />
            </div>
          </SheetContent>
        </Sheet>
      )}

      {showQuests && (
        <Sheet open={questsOpen} onOpenChange={setQuestsOpen}>
          <SheetTrigger asChild>
            <button
              type="button"
              data-testid="quests-button"
              className="group inline-flex items-center gap-2 rounded-full border border-amber-500/40 bg-amber-950/30 hover:bg-amber-900/40 hover:border-amber-400/60 transition-colors px-3 py-1.5 text-xs font-medium text-amber-100 shadow-sm"
            >
              <Scroll size={14} className="text-amber-300" />
              <span>Quests</span>
              <Badge
                variant="outline"
                className="h-5 px-1.5 text-[10px] border-amber-400/50 text-amber-200 bg-amber-900/30"
              >
                {activeCount}
              </Badge>
            </button>
          </SheetTrigger>
          <SheetContent
            side="right"
            className="w-full sm:max-w-md bg-gray-900 border-gray-700 text-white overflow-y-auto"
            data-testid="quests-sheet"
          >
            <SheetHeader>
              <SheetTitle className="text-amber-300 flex items-center gap-2">
                <Scroll size={18} />
                Quest Log
                <Badge
                  variant="outline"
                  className="ml-1 text-xs border-amber-400/50 text-amber-200"
                >
                  {activeCount} Active
                </Badge>
              </SheetTitle>
            </SheetHeader>
            <div className="mt-4">
              <QuestLogPanel
                quests={quests}
                onUpdateStatus={onUpdateQuestStatus}
                embedded
              />
            </div>
          </SheetContent>
        </Sheet>
      )}

      {showDeck && (
        <CharacterDeck characterId={characterId} characterName={characterName} />
      )}

      {campaignId && pausedCount > 0 && (
        <Sheet open={pausedOpen} onOpenChange={setPausedOpen}>
          <SheetTrigger asChild>
            <button
              type="button"
              data-testid="paused-threads-button"
              className="group inline-flex items-center gap-2 rounded-full border border-rose-500/40 bg-rose-950/30 hover:bg-rose-900/40 hover:border-rose-400/60 transition-colors px-3 py-1.5 text-xs font-medium text-rose-100 shadow-sm"
              title="Paused storylines — try to find your way back to them"
            >
              <Hourglass size={14} className="text-rose-300" />
              <span>Paused</span>
              <Badge
                variant="outline"
                className="h-5 px-1.5 text-[10px] border-rose-400/50 text-rose-200 bg-rose-900/30"
              >
                {pausedCount}
              </Badge>
            </button>
          </SheetTrigger>
          <SheetContent
            side="right"
            className="w-full sm:max-w-md bg-gray-900 border-gray-700 text-white overflow-y-auto"
            data-testid="paused-threads-sheet"
          >
            <SheetHeader>
              <SheetTitle className="text-rose-300 flex items-center gap-2">
                <Hourglass size={18} />
                Paused Threads
                <span className="ml-1 text-[11px] font-normal text-stone-400">
                  The DM will rule whether each is still alive.
                </span>
              </SheetTitle>
            </SheetHeader>
            <div className="mt-4">
              <PausedThreadsPanel
                campaignId={campaignId}
                characterId={characterId}
                onResumed={(payload) => {
                  if (onPausedThreadResumed) onPausedThreadResumed(payload);
                  refreshPausedCount();
                }}
                embedded
              />
            </div>
          </SheetContent>
        </Sheet>
      )}

      {showTime && (
        <span
          data-testid="time-of-day-chip"
          title={timeBucket?.hour != null ? `Hour ${timeBucket.hour}/24 in-fiction` : timeLabel}
          className="inline-flex items-center gap-1.5 rounded-full border border-indigo-500/40 bg-indigo-950/30 px-3 py-1.5 text-xs font-medium text-indigo-100 shadow-sm"
        >
          <span className="text-sm leading-none" aria-hidden="true">{timeIcon}</span>
          <span className="max-w-[8rem] truncate">{timeLabel}</span>
        </span>
      )}

      {showPP && (
        <span
          data-testid="passive-perception-chip"
          title={
            `Passive Perception ${pp.score} · ${ppLabel} tier\n` +
            `10 + WIS mod (${pp.wis_mod >= 0 ? '+' : ''}${pp.wis_mod})` +
            (pp.proficient ? ` + proficiency (+${pp.prof_bonus})` : ' (no Perception proficiency)') +
            `\nDM calibrates narration density to this score.`
          }
          className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium shadow-sm ${ppTierColor}`}
        >
          <Eye size={13} className="opacity-90" />
          <span className="font-semibold">PP {pp.score}</span>
          <span className="opacity-70">·</span>
          <span className="text-[11px] tracking-wide">{ppLabel}</span>
        </span>
      )}

      {showChaos && (
        <span
          data-testid="chaos-chip"
          title={
            `Chaos ${chaosVal}/100 — ${chaosTier?.label || ''}\n` +
            `Acting against your Ideal/Bond/Flaw raises this. ` +
            `At 30+ it can draft a curse card on a violation turn.`
          }
          className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium shadow-sm ${chaosTierColor}`}
        >
          <Flame size={13} className="opacity-90" />
          <span className="font-semibold">Chaos {chaosVal}</span>
          {chaosTier?.label && (
            <>
              <span className="opacity-70">·</span>
              <span className="text-[11px] tracking-wide">{chaosTier.label}</span>
            </>
          )}
        </span>
      )}
    </div>
  );
};

export default CampaignTopBar;
