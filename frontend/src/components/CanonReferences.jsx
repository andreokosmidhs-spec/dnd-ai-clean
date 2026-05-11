/**
 * CanonReferences — compact footer beneath a DM narration beat showing
 * which CANON scenes the narration just touched. Each chip:
 *   • pulsing emerald dot (the visible "DM is honoring canon" signal)
 *   • Scene number + title
 *   • Clickable → opens the CanonTimelinePanel
 *
 * Renders nothing when the narration references no canonized entities.
 * Designed to coexist with the existing EntityNarrationParser /
 * NPCMentionHighlighter — this is a footer, not an inline replacement.
 */
import React, { useState } from 'react';
import { Anchor } from 'lucide-react';
import CanonTimelinePanel from './CanonTimelinePanel';

const CanonReferenceChip = ({ scene, terms, onOpen }) => (
  <button
    type="button"
    onClick={onOpen}
    className="group inline-flex items-center gap-1.5 max-w-full px-2 py-0.5 rounded-full
               border border-emerald-500/40 hover:border-emerald-400/80
               bg-emerald-950/30 hover:bg-emerald-900/50
               text-[10.5px] text-emerald-100 hover:text-emerald-50
               transition-all"
    data-testid={`canon-ref-chip-${scene.scene_number}`}
    title={`Canonized in Scene ${scene.scene_number}: ${scene.title}`}
  >
    <span className="relative flex items-center justify-center w-2 h-2 shrink-0">
      <span className="absolute inset-0 rounded-full bg-emerald-400 animate-ping opacity-60" />
      <span className="relative w-1.5 h-1.5 rounded-full bg-emerald-300" />
    </span>
    <Anchor className="w-3 h-3 text-emerald-300 shrink-0" />
    <span className="font-bold text-emerald-200">
      Scene {scene.scene_number}
    </span>
    <span className="opacity-80 truncate max-w-[140px] sm:max-w-[200px]">
      {scene.title}
    </span>
    {terms && terms.length > 0 && (
      <span className="hidden md:inline opacity-60 italic truncate max-w-[160px]">
        · {terms.slice(0, 2).join(', ')}
      </span>
    )}
  </button>
);

const CanonReferences = ({ campaignId, mentions }) => {
  const [timelineOpen, setTimelineOpen] = useState(false);

  if (!mentions || mentions.length === 0) return null;

  return (
    <>
      <div
        className="mt-2 flex flex-wrap gap-1.5 items-center"
        data-testid="canon-references-row"
      >
        <span className="text-[9.5px] uppercase tracking-[0.18em] text-emerald-400/80 font-bold mr-1">
          ✦ honoring canon
        </span>
        {mentions.map(({ scene, terms }) => (
          <CanonReferenceChip
            key={scene.id}
            scene={scene}
            terms={terms}
            onOpen={() => setTimelineOpen(true)}
          />
        ))}
      </div>
      <CanonTimelinePanel
        open={timelineOpen}
        onClose={() => setTimelineOpen(false)}
        campaignId={campaignId}
      />
    </>
  );
};

export default CanonReferences;
