"""
Pressure context builder — converts CampaignPressureState into a compact
DM-readable narrative block that can be injected into both DM system prompts.

Also applies the narrative beat directives from the 4-act story structure,
giving the DM act-phase-specific pacing guidance derived from:
  Act 1 Shadow     → Hero's Journey: Ordinary World / Call to Adventure
  Act 2 Pressure   → Challenge format: Escalating Obstacles
  Act 3 Confrontation → Before & After: the false showdown
  Act 4 Resolution → Lesson From Others: consequences and meaning
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ── Narrative beat instructions per act phase ─────────────────────────────────

_ACT_BEAT_INSTRUCTIONS: Dict[str, str] = {
    "act1_shadow": (
        "NARRATIVE BEAT — ACT 1 (SHADOW): The antagonist has not yet been seen. "
        "Plant visible but unexplained signs of their presence: a missing person, "
        "a strange symbol, an NPC who \"changed\" recently. Do NOT name or describe "
        "the antagonist. Build unease through environmental texture — something is "
        "wrong but the player can't yet name it. Reward curiosity, not heroics. "
        "One hook hint per 2-3 turns is the right cadence."
    ),
    "act2_pressure": (
        "NARRATIVE BEAT — ACT 2 (PRESSURE): The antagonist's signature has been "
        "revealed. Their MO (see ANTAGONIST block) is now a pattern the player can "
        "track. Show systemic effects: multiple regions feel it, NPCs are scared, "
        "factions are reacting. Every third turn, surface one visible consequence "
        "of the antagonist's most recent operation. Do NOT yet reveal motive or "
        "full network. Let the player piece it together. Raise stakes through "
        "NPC pressure and resource scarcity, not monologues."
    ),
    "act3_confrontation": (
        "NARRATIVE BEAT — ACT 3 (CONFRONTATION): The player is strong enough to "
        "fight back. Build toward a confrontation. The antagonist begins to "
        "acknowledge the player — perhaps a message, a trap, a decoy. A FALSE "
        "SHOWDOWN is available: the player may defeat a lieutenant or proxy, "
        "believing the war is won, before the true threat reasserts. If the player "
        "seeks the antagonist, give them breadcrumbs that lead to a meaningful but "
        "incomplete resolution. Do NOT end the antagonist arc prematurely — the "
        "full network is not yet exposed."
    ),
    "act4_resolution": (
        "NARRATIVE BEAT — ACT 4 (RESOLUTION): The final confrontation arc. The "
        "antagonist's motive is now fully revealable when earned. Show the human "
        "cost of the conflict — NPCs who suffered, regions that changed, decisions "
        "that cannot be undone. Let the player's prior choices have weight: did "
        "they save the informant? Did they destroy the evidence? The world "
        "remembers. After defeat, leave one meaningful consequence standing — "
        "resolution means scars, not erasure."
    ),
}


async def build_pressure_context_block(
    campaign_id: str,
    db: Any,
) -> str:
    """
    Read CampaignPressureState from MongoDB and return a compact
    DM-readable narrative context block.

    Returns an empty string if no pressure state exists (graceful degradation).
    """
    try:
        doc = await db.campaign_pressure_states.find_one({"campaign_id": campaign_id})
        if not doc:
            return ""

        act_phase: str = doc.get("act_phase", "act1_shadow")
        player_level: int = doc.get("player_level", 1)
        antagonists: list = doc.get("antagonists", [])
        regional_pressures: dict = doc.get("regional_pressures", {})
        hooks: list = doc.get("hooks", [])

        lines: list[str] = []
        lines.append("=== LIVING CAMPAIGN PRESSURE ===")
        lines.append(f"Act Phase: {_fmt_phase(act_phase)} | Player Level: {player_level}")

        # ── Antagonist block ───────────────────────────────────────────────
        if antagonists:
            lines.append("")
            lines.append("ANTAGONIST(S):")
            for ant in antagonists[:2]:  # cap at 2 to keep prompt tight
                name = ant.get("name", "Unknown")
                mo = ant.get("mo", "secretive")
                pressure_style = ant.get("pressure_style", "")
                escalation = ant.get("escalation_level", 0.0)
                ant_phase = ant.get("act_phase", act_phase)
                revealed_sig = ant.get("revealed_signature", False)
                revealed_motive = ant.get("revealed_motive", False)
                ideology = ant.get("ideology", "")

                ant_line = (
                    f"- {name} | MO: {mo} | Escalation: {_fmt_escalation(escalation)} | "
                    f"Phase: {_fmt_phase(ant_phase)}"
                )
                if pressure_style:
                    ant_line += f" | Style: {pressure_style}"

                if revealed_motive:
                    ant_line += f"\n  Ideology (REVEALABLE): {ideology}"
                elif revealed_sig:
                    ant_line += "\n  Signature revealed — player knows something is operating but NOT who/why"
                else:
                    ant_line += "\n  Identity hidden — DO NOT hint at name, ideology, or full network"

                # Most recent visible operation
                ops: list = ant.get("operations", [])
                if ops:
                    last_op = ops[-1]
                    visible = last_op.get("visible_effects", [])
                    if visible:
                        ant_line += f"\n  Last operation visible effect: {visible[0]}"
                lines.append(ant_line)

        # ── Regional pressure hotspots ─────────────────────────────────────
        if regional_pressures:
            hot_regions = []
            for rid, region in regional_pressures.items():
                axes = {k: region.get(k, 0.0) for k in
                        ["crime", "war", "scarcity", "corruption",
                         "cult_activity", "magical_instability", "social_unrest"]}
                total = round(sum(axes.values()) / max(len(axes), 1), 2)
                if total >= 0.25:
                    hot_axes = sorted(
                        [(k, v) for k, v in axes.items() if v >= 0.3],
                        key=lambda x: -x[1]
                    )
                    hot_regions.append((region.get("region_name", rid), total, hot_axes))

            if hot_regions:
                hot_regions.sort(key=lambda x: -x[1])
                lines.append("")
                lines.append("WORLD PRESSURE (regions with active tension):")
                for rname, total, hot_axes in hot_regions[:3]:
                    label = _pressure_label(total)
                    axis_str = ", ".join(
                        f"{k.replace('_', ' ')} {v:.0%}" for k, v in hot_axes[:3]
                    )
                    lines.append(f"- {rname}: {label}" + (f" [{axis_str}]" if axis_str else ""))

        # ── Visible hooks the player could notice ─────────────────────────
        visible_hooks = [h for h in hooks if h.get("status") == "visible"][:3]
        if visible_hooks:
            lines.append("")
            lines.append("VISIBLE HOOKS (surface naturally — do NOT monologue):")
            for h in visible_hooks:
                lines.append(f"- {h.get('description', h.get('title', ''))[:120]}")

        # ── Narrative beat directive for this act phase ────────────────────
        beat = _ACT_BEAT_INSTRUCTIONS.get(act_phase, "")
        if beat:
            lines.append("")
            lines.append(beat)

        lines.append("=== END PRESSURE ===")
        return "\n".join(lines)

    except Exception as exc:
        logger.warning(f"pressure_context_service: failed to build block (non-fatal): {exc}")
        return ""


def _fmt_phase(phase: str) -> str:
    return {
        "act1_shadow": "Act 1 — Shadow (hidden threat)",
        "act2_pressure": "Act 2 — Pressure (signature revealed)",
        "act3_confrontation": "Act 3 — Confrontation (false showdown available)",
        "act4_resolution": "Act 4 — Resolution (final arc)",
    }.get(phase, phase)


def _fmt_escalation(level: float) -> str:
    if level >= 0.8:
        return "CRITICAL"
    if level >= 0.6:
        return "HIGH"
    if level >= 0.4:
        return "MODERATE"
    if level >= 0.2:
        return "LOW"
    return "DORMANT"


def _pressure_label(total: float) -> str:
    if total >= 0.7:
        return "CRITICAL"
    if total >= 0.5:
        return "HIGH"
    if total >= 0.35:
        return "MODERATE"
    return "LOW"
