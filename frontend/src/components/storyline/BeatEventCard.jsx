/**
 * BeatEventCard — investigation event presented as a TCG-style card.
 *
 * STATES:
 *   - Sealed (status='pending'): card back, no info, padlock emblem, no click.
 *   - Closed (active or resolved): peek face with title at top, glowing
 *     rarity crystal centered, category-colored frame, info chips at the
 *     bottom. Click anywhere on the body to flip+expand.
 *   - Expanded: centered overlay, same color theme, reveals the full
 *     description + Pitch input + action buttons. After the player acts
 *     or rolls, the overlay closes and the carousel auto-advances.
 *
 * The CLOSED face deliberately HIDES the description text — opening the
 * card is the player's small ritual that mirrors flipping a card in a
 * tabletop game. Resolved beats keep the same flip affordance so you can
 * re-read the resolution narration any time.
 */
import React, { useEffect, useState } from 'react';
import { Lock, X, Wand2, Dice6, Eye, Clock, ShieldCheck, MapPin, Users, Shield as ShieldIcon, Compass } from 'lucide-react';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import PitchInput from './PitchInput';
import DMFeedbackButton from './DMFeedbackButton';
import { categoryPaletteFor, rarityFor } from './beatCardUtils';

const CATEGORY_ICONS = {
  npcs: Users,
  locations: MapPin,
  factions: ShieldIcon,
  leads: Compass,
};

const STATUS_TONE = {
  pending: { label: 'Sealed', dot: 'bg-stone-500' },
  active: { label: 'In play', dot: 'bg-amber-400 animate-pulse' },
  passed: { label: 'Passed', dot: 'bg-emerald-400' },
  failed: { label: 'Failed', dot: 'bg-rose-400' },
  skipped: { label: 'Skipped', dot: 'bg-amber-300' },
};

const RarityCrystal = ({ rarity, size = 'lg' }) => {
  // Hexagonal-feeling crystal: stacked diamonds with the rarity gradient,
  // an outer pulse ring, and a soft inner highlight. Pure CSS.
  const dims =
    size === 'lg' ? 'w-20 h-20'
    : size === 'md' ? 'w-14 h-14'
    : 'w-10 h-10';
  return (
    <div
      className={`relative ${dims} flex items-center justify-center`}
      data-testid={`beat-rarity-${rarity.key}`}
      title={`Rarity: ${rarity.label}`}
    >
      {/* Outer pulse halo */}
      <div className={`absolute inset-0 rounded-full bg-gradient-to-br ${rarity.crystal} opacity-30 blur-xl animate-pulse`} />
      {/* Crystal diamond */}
      <div
        className={`relative rotate-45 ${dims} bg-gradient-to-br ${rarity.crystal}
                    ${rarity.glow} ring-2 ${rarity.ring}
                    border border-white/40
                    rounded-md`}
      >
        {/* Inner shine */}
        <div className="absolute inset-1 rounded bg-gradient-to-tr from-white/40 via-white/5 to-transparent" />
      </div>
    </div>
  );
};

const InfoChip = ({ children, color = 'amber', testId }) => {
  const palette = {
    amber:   'border-amber-400/60 text-amber-100 bg-stone-900/70',
    emerald: 'border-emerald-400/60 text-emerald-100 bg-stone-900/70',
    indigo:  'border-indigo-300/60 text-indigo-100 bg-stone-900/70',
    rose:    'border-rose-400/60 text-rose-100 bg-stone-900/70',
    slate:   'border-slate-400/60 text-slate-100 bg-stone-900/70',
  }[color] || 'border-amber-400/60 text-amber-100 bg-stone-900/70';
  return (
    <span
      className={`inline-flex items-center gap-1 text-[10.5px] uppercase tracking-wider font-bold px-1.5 py-0.5 rounded border ${palette}`}
      data-testid={testId}
    >
      {children}
    </span>
  );
};

/** Closed/peek face — visible in the carousel row */
const PeekFace = ({ beat, index, total, isActive, palette, rarity, onOpen, sealed, resolved, hasComplication }) => {
  const CatIcon = CATEGORY_ICONS[palette.key] || Compass;
  const tone = STATUS_TONE[beat.status] || STATUS_TONE.pending;

  return (
    <button
      type="button"
      onClick={sealed ? undefined : onOpen}
      disabled={sealed}
      className={`group relative shrink-0 w-[230px] sm:w-[250px] h-[340px] sm:h-[360px] rounded-xl border-2 overflow-hidden
        flex flex-col text-left
        transition-all duration-300
        bg-gradient-to-b from-stone-950 via-stone-900 to-stone-950
        shadow-[inset_0_0_24px_rgba(0,0,0,0.6)]
        ${sealed ? 'cursor-not-allowed opacity-90' : 'cursor-pointer hover:-translate-y-1 hover:shadow-[0_8px_32px_rgba(0,0,0,0.6)]'}
        ${isActive
          ? `${hasComplication ? 'border-rose-500/80 shadow-[0_0_24px_rgba(244,63,94,0.45)]' : palette.border + ' shadow-[0_0_24px_rgba(245,158,11,0.25)]'} scale-[1.03]`
          : sealed
            ? 'border-stone-700/70'
            : resolved
              ? (beat.status === 'passed' ? 'border-emerald-500/40'
                 : beat.status === 'failed' ? 'border-rose-500/40'
                 : 'border-amber-500/40')
              : `${palette.border} opacity-85`}
      `}
      data-testid={`beat-card-${index}`}
      data-beat-status={beat.status}
      aria-label={`Beat ${index + 1}: ${beat.title || 'Sealed scene'}. Click to ${sealed ? 'view (locked)' : 'reveal narration'}.`}
    >
      {/* Category color header band (matches Knowledge Deck headerBg) */}
      <div
        className={`${sealed ? 'bg-stone-800' : palette.headerBg}
          px-3 py-2 flex items-center gap-2 border-b border-black/30`}
      >
        <CatIcon className="h-3.5 w-3.5 text-white/90 shrink-0" />
        <span className="text-[10px] uppercase tracking-[0.18em] font-bold text-white/95 truncate">
          {sealed ? `Beat ${index + 1}` : (palette.label || 'Lead')}
        </span>
        <span className="ml-auto text-[10px] uppercase tracking-wider font-bold text-white/80">
          {index + 1}/{total}
        </span>
      </div>

      {/* Card title — top-aligned per user spec */}
      <div className="px-3 pt-3 pb-1">
        <div className="text-amber-50 font-bold text-[15px] leading-tight font-serif line-clamp-2 min-h-[2.2em]">
          {sealed ? 'A Sealed Beat' : (beat.title || (resolved ? 'Resolved scene' : 'New scene'))}
        </div>
      </div>

      {/* Center emblem — rarity crystal */}
      <div className="flex-1 flex flex-col items-center justify-center px-3 gap-2">
        {sealed ? (
          <div className="relative flex items-center justify-center">
            <div className="absolute inset-0 rounded-full bg-stone-700 opacity-20 blur-xl" />
            <div className="relative w-20 h-20 rounded-full border-2 border-stone-600 bg-stone-900 flex items-center justify-center">
              <Lock className="h-9 w-9 text-stone-500" />
            </div>
          </div>
        ) : (
          <RarityCrystal rarity={rarity} size="lg" />
        )}
        {!sealed && (
          <div className={`text-[10px] uppercase tracking-[0.22em] font-bold ${rarity.text}`}>
            {rarity.label}
          </div>
        )}
        {!sealed && !resolved && (
          <div className="text-[10.5px] text-amber-200/70 italic mt-1">
            Tap to reveal
          </div>
        )}
        {resolved && (
          <div
            className={`text-[10px] font-black uppercase tracking-widest -rotate-6 inline-block
              border-2 px-2 py-0.5 rounded mt-1
              ${beat.status === 'passed' ? 'border-emerald-400 text-emerald-200 bg-emerald-950/70' :
                beat.status === 'failed' ? 'border-rose-400 text-rose-200 bg-rose-950/70' :
                'border-amber-400 text-amber-200 bg-amber-950/70'}`}
            data-testid={`beat-resolved-stamp-${beat.status}`}
          >
            {beat.status}
          </div>
        )}
      </div>

      {/* Bottom info chips */}
      <div className="px-2.5 py-2 border-t border-black/40 bg-stone-950/80 flex flex-wrap gap-1 items-center">
        {sealed ? (
          <span className="text-[10px] uppercase tracking-[0.18em] text-stone-400 font-bold">
            Locked
          </span>
        ) : (
          <>
            {beat.check_type && Number(beat.dc) > 0 && !beat.roll_optional ? (
              <InfoChip color="amber" testId="beat-check-chip">
                <ShieldCheck className="h-3 w-3" />
                {beat.check_type} DC {beat.dc}
              </InfoChip>
            ) : (
              <InfoChip color="emerald" testId="beat-no-roll-chip">
                <Eye className="h-3 w-3" /> Open
              </InfoChip>
            )}
            {beat.time_of_day?.label && (
              <InfoChip color="indigo">
                <Clock className="h-3 w-3" /> {beat.time_of_day.label}
              </InfoChip>
            )}
            <div className="flex items-center gap-1 ml-auto">
              <span className={`w-1.5 h-1.5 rounded-full ${tone.dot}`} />
              <span className="text-[10px] uppercase tracking-wider text-amber-100/80 font-bold">
                {tone.label}
              </span>
            </div>
          </>
        )}
      </div>

      {/* Carry-forward complication ribbon */}
      {hasComplication && (
        <div
          className="absolute top-0 left-0 right-0 z-10 px-2.5 py-1 text-[10px] bg-rose-950/90 border-b border-rose-500/60 text-rose-100 flex items-center gap-1.5"
          data-testid="beat-complication-ribbon"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
          <span className="uppercase tracking-wider font-bold text-[9px]">Carrying forward</span>
        </div>
      )}
    </button>
  );
};

/** Expanded overlay — centered, larger, action surface */
const ExpandedFace = ({
  beat, index, total, palette, rarity, complication, pressOnUsed,
  campaignId, storylineId, onCorrectionApplied, onClose,
  // action callbacks (wired from ActiveInvestigationPanel)
  onCreative, onRoll, onContinue, busy, rollOptional, lastRoll, formatMod, mod,
}) => {
  const resolved = ['passed', 'failed', 'skipped'].includes(beat.status);
  const sealed = beat.status === 'pending';
  const isKnowledgeLocked = beat.reveal_type === 'knowledge' && !resolved;
  const CatIcon = CATEGORY_ICONS[palette.key] || Compass;

  // ESC to close
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-[140] flex items-center justify-center p-3 sm:p-6 bg-stone-950/70 backdrop-blur-sm"
      onClick={onClose}
      data-testid="beat-card-expanded-overlay"
      role="dialog"
      aria-modal="true"
      aria-label={`Beat: ${beat.title || 'Scene'}`}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className={`relative w-full max-w-2xl max-h-[92vh] flex flex-col rounded-2xl border-4 ${palette.border}
          bg-gradient-to-br from-stone-950 via-stone-900 to-amber-950/30
          shadow-[0_20px_60px_rgba(0,0,0,0.7)] overflow-hidden
          animate-in fade-in zoom-in-95 duration-300`}
        data-testid="beat-card-expanded"
      >
        {/* Header band — same color as peek face */}
        <div className={`${palette.headerBg} px-4 py-3 flex items-center gap-2.5 border-b border-black/40`}>
          <CatIcon className="h-4 w-4 text-white shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="text-[10px] uppercase tracking-[0.2em] font-bold text-white/85 leading-none">
              {palette.label || 'Lead'} · Beat {index + 1} of {total}
            </div>
            <h3 className="text-white font-bold text-lg leading-tight font-serif truncate mt-0.5">
              {beat.title || 'New scene'}
            </h3>
          </div>
          <RarityCrystal rarity={rarity} size="sm" />
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white p-1 rounded-full hover:bg-white/10 transition-colors"
            aria-label="Close (Esc)"
            data-testid="beat-expanded-close-btn"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Complication ribbon (active card only) */}
        {complication && complication.trim() && (
          <div className="px-4 py-2 bg-rose-950/70 border-b border-rose-500/60">
            <div className="flex items-center gap-1.5 text-rose-300 uppercase tracking-wider font-bold text-[10px] mb-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
              {pressOnUsed ? 'Pressing On — Cost Paid' : 'Carrying Forward'}
            </div>
            <div className="italic font-serif text-rose-50 leading-snug text-sm">
              {complication}
            </div>
          </div>
        )}

        {/* Body — narration */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {sealed ? (
            <div className="flex flex-col items-center justify-center py-8 text-stone-300">
              <Lock className="h-10 w-10 mb-2 text-stone-400" />
              <div className="text-sm uppercase tracking-widest font-bold">Sealed</div>
              <div className="text-[12px] text-stone-400 mt-1">
                This beat unlocks after the current one resolves.
              </div>
            </div>
          ) : isKnowledgeLocked ? (
            <div className="rounded-md border-2 border-amber-400/70 bg-stone-900/70 p-4 shadow-inner">
              <div className="flex items-center justify-center gap-2 mb-2">
                <Lock className="h-5 w-5 text-amber-200" />
                <span className="text-[11px] uppercase tracking-widest font-bold text-amber-200">
                  Sealed knowledge
                </span>
              </div>
              <div className="text-[15px] text-amber-50 italic font-serif leading-relaxed text-center">
                {beat.prompt || `Roll ${beat.check_type} (DC ${beat.dc}) to reveal what you can piece together.`}
              </div>
              {Array.isArray(beat.targets) && beat.targets.length > 0 && (
                <div className="mt-3 flex flex-wrap justify-center gap-1.5">
                  {beat.targets.slice(0, 4).map((t, ti) => (
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
          ) : (
            <div
              className="text-[15.5px] text-amber-50 italic font-serif leading-relaxed tracking-wide"
              data-testid="beat-description-expanded"
            >
              {beat.description || (resolved
                ? <span className="not-italic text-amber-200/80">— {beat.outcome_text || 'No revelation recorded.'}</span>
                : 'The scene unfolds before you…')}
            </div>
          )}

          {beat.outcome_text && !isKnowledgeLocked && (
            <div className="mt-2 text-[13.5px] text-amber-200 border-l-2 border-amber-400/70 pl-3 italic">
              {beat.outcome_text}
            </div>
          )}

          {beat.reveal_type === 'knowledge' && beat.status === 'failed' && (
            <div className="rounded-md border-2 border-rose-400/70 bg-stone-900/70 p-3">
              <div className="flex items-center gap-1.5 text-rose-200 text-[11px] uppercase tracking-wider font-bold mb-1">
                <Lock className="h-3 w-3" /> Sealed Lead
              </div>
              <div className="text-[14px] text-amber-50 italic font-serif leading-snug">
                You couldn't piece it together. The lead is now in your deck — find someone who can help.
              </div>
            </div>
          )}

          {/* Pitch input — social or knowledge beats, only on active */}
          {beat.status === 'active' && Number(beat.dc) > 0 && campaignId && storylineId && (
            <PitchInput
              campaignId={campaignId}
              storylineId={storylineId}
              beat={beat}
              beatIndex={index}
              onAdjusted={onCorrectionApplied}
            />
          )}

          {lastRoll && !lastRoll.passed && (
            <div className="text-[13px] text-rose-200 italic">
              Last roll: {lastRoll.die}{formatMod(lastRoll.mod)} = {lastRoll.total} vs DC {lastRoll.dc} — failed.
            </div>
          )}
        </div>

        {/* Action bar — visible only on the active beat */}
        {beat.status === 'active' && !sealed && (
          <div className="px-4 py-3 border-t border-amber-500/30 bg-stone-950/80 flex flex-wrap gap-2 items-center">
            <Button
              size="sm"
              className="h-9 bg-fuchsia-500 hover:bg-fuchsia-400 text-black font-bold"
              onClick={onCreative}
              disabled={busy}
              data-testid="storyline-creative-btn-expanded"
            >
              <Wand2 className="h-4 w-4 mr-1" /> What do you do?
            </Button>
            <Button
              size="sm" variant="outline"
              className="h-9 border-amber-400/70 text-amber-100 bg-amber-950/30 hover:bg-amber-700/30"
              onClick={onRoll}
              disabled={busy || rollOptional}
              data-testid="storyline-roll-btn-expanded"
              title={rollOptional ? 'No check suggested for this scene' : undefined}
            >
              <Dice6 className="h-4 w-4 mr-1" />
              {rollOptional ? 'No check needed' : <>Roll d20{formatMod(mod)}<span className="ml-1 text-[10px] uppercase tracking-wider opacity-70">suggested</span></>}
            </Button>
            <Button
              size="sm"
              className={beat.reveal_type === 'knowledge'
                ? 'h-9 bg-amber-600 hover:bg-amber-500 text-stone-950 font-bold border border-amber-300'
                : 'h-9 bg-emerald-600 hover:bg-emerald-500 text-stone-950 font-bold border border-emerald-300'}
              onClick={onContinue}
              disabled={busy}
              data-testid="storyline-continue-btn-expanded"
            >
              {beat.reveal_type === 'knowledge' ? 'Skip lead' : 'Continue'}
            </Button>
            <div className="ml-auto">
              {campaignId && storylineId && (
                <DMFeedbackButton
                  campaignId={campaignId}
                  storylineId={storylineId}
                  beatIndex={index}
                  onCorrectionApplied={onCorrectionApplied}
                />
              )}
            </div>
          </div>
        )}

        {/* Footer on resolved beats — still allow Ask the DM for retro contests */}
        {resolved && campaignId && storylineId && (
          <div className="px-4 py-2.5 border-t border-amber-500/20 bg-stone-950/80 flex justify-end">
            <DMFeedbackButton
              campaignId={campaignId}
              storylineId={storylineId}
              beatIndex={index}
              onCorrectionApplied={onCorrectionApplied}
            />
          </div>
        )}
      </div>
    </div>
  );
};

const BeatEventCard = ({
  beat, index, total, isActive, complication, pressOnUsed,
  campaignId, storylineId, onCorrectionApplied,
  // action props forwarded from the parent panel
  onCreative, onRoll, onContinue, busy, rollOptional, lastRoll, formatMod, mod,
  expandedIndex, setExpandedIndex,
}) => {
  const palette = categoryPaletteFor(beat);
  const rarity = rarityFor(beat);
  const sealed = beat.status === 'pending';
  const resolved = ['passed', 'failed', 'skipped'].includes(beat.status);
  const hasComplication = isActive && !!(complication && complication.trim());
  const isOpen = expandedIndex === index;

  // Auto-open the active beat the first time it appears in this card,
  // so the player isn't forced to click before acting on a new beat.
  const [autoOpened, setAutoOpened] = useState(false);
  useEffect(() => {
    if (isActive && !sealed && !autoOpened && expandedIndex === null) {
      setAutoOpened(true);
      setExpandedIndex(index);
    }
    if (!isActive) {
      setAutoOpened(false);
    }
  }, [isActive, sealed, autoOpened, expandedIndex, index, setExpandedIndex]);

  return (
    <>
      <PeekFace
        beat={beat}
        index={index}
        total={total}
        isActive={isActive}
        palette={palette}
        rarity={rarity}
        sealed={sealed}
        resolved={resolved}
        hasComplication={hasComplication}
        onOpen={() => setExpandedIndex(index)}
      />
      {isOpen && (
        <ExpandedFace
          beat={beat}
          index={index}
          total={total}
          palette={palette}
          rarity={rarity}
          complication={complication}
          pressOnUsed={pressOnUsed}
          campaignId={campaignId}
          storylineId={storylineId}
          onCorrectionApplied={onCorrectionApplied}
          onClose={() => setExpandedIndex(null)}
          onCreative={onCreative}
          onRoll={onRoll}
          onContinue={onContinue}
          busy={busy}
          rollOptional={rollOptional}
          lastRoll={lastRoll}
          formatMod={formatMod}
          mod={mod}
        />
      )}
    </>
  );
};

export default BeatEventCard;
