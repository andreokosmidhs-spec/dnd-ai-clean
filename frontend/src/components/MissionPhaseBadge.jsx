import React from "react";

/**
 * MissionPhaseBadge
 *
 * Compact badge that shows the active mission-type + current phase of the
 * running storyline, e.g. "🎯 Heist · Phase 2: Scouting". Renders nothing
 * when the active storyline isn't bound to a mission type.
 *
 * Props:
 *   storyline: the active storyline doc from /api/.../storylines/draft
 *              or /storylines/{id}. Must carry `.mission_type` snapshot
 *              and `.beats[current_beat].phase_index` / `.phase_name`.
 */
const MissionPhaseBadge = ({ storyline }) => {
  const mt = storyline?.mission_type;
  if (!mt || !mt.name) return null;

  const beats = storyline?.beats || [];
  const cur = beats[storyline?.current_beat ?? 0] || {};
  const phases = mt.phases || [];

  // Best phase signal: explicit on the beat, else 0.
  let phaseIdx =
    typeof cur.phase_index === "number" ? cur.phase_index : 0;
  if (phaseIdx < 0) phaseIdx = 0;
  if (phaseIdx > phases.length - 1) phaseIdx = Math.max(0, phases.length - 1);

  const phaseName =
    cur.phase_name || (phases[phaseIdx] && phases[phaseIdx].name) || "";

  const totalPhases = phases.length || 0;

  return (
    <div
      className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/40 bg-amber-500/10 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-amber-200 shadow-[0_0_8px_rgba(251,191,36,0.15)]"
      title={`Mission: ${mt.name}${
        phaseName ? ` — Phase ${phaseIdx + 1} of ${totalPhases || "?"}: ${phaseName}` : ""
      }`}
      data-testid="mission-phase-badge"
    >
      <span aria-hidden="true">{mt.icon || "🎲"}</span>
      <span className="normal-case text-amber-100 font-bold">{mt.name}</span>
      {phaseName && (
        <>
          <span className="text-amber-500/60">·</span>
          <span className="normal-case text-amber-200/90 font-medium">
            Phase {phaseIdx + 1}
            {totalPhases ? `/${totalPhases}` : ""}: {phaseName}
          </span>
        </>
      )}
    </div>
  );
};

export default MissionPhaseBadge;
