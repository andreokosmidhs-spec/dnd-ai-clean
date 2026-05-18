"""
LIVING CAMPAIGN PRESSURE ENGINE

World wound → pressure → hook → lead → quest → NPC reaction
→ consequence → narrative tick → cleanse/escalation
→ campaign memory → new world state → antagonist adapts → new pressure

Everything cycles. Nothing important disappears without meaning.
"""
from __future__ import annotations

import logging
import random
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from models.pressure_models import (
    Antagonist, AntagonistOperation, AntagonistMO,
    CampaignPressureState, CleansingEvent, CleansingType,
    Hook, HookType, Lead, LeadStatus, RegionalPressure, WorldWound,
)
from services.narrative_importance import build_importance, recency_score

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

PRESSURE_TICK_INTENSITY = {
    "long_rest": 0.08,
    "travel": 0.06,
    "next_day": 0.10,
    "major_quest_completion": 0.14,
}

# How each pressure axis flows into derived world state
PRESSURE_TO_STATE = {
    "crime":               {"fear": 0.4, "rumor_density": 0.3, "guard_presence": 0.3},
    "war":                 {"fear": 0.5, "guard_presence": 0.4, "price_pressure": 0.1},
    "scarcity":            {"price_pressure": 0.5, "social_unrest": 0.3, "fear": 0.2},
    "corruption":          {"faction_activity": 0.4, "rumor_density": 0.3, "guard_presence": -0.1},
    "cult_activity":       {"fear": 0.4, "rumor_density": 0.4, "magical_instability": 0.2},
    "magical_instability": {"fear": 0.3, "rumor_density": 0.2, "faction_activity": 0.1},
    "social_unrest":       {"rumor_density": 0.3, "faction_activity": 0.3, "fear": 0.2},
}

HOOK_TEMPLATES: Dict[str, List[str]] = {
    "crime":     [
        "A merchant's wagon was found stripped and burning outside the east gate",
        "Three guild members vanished in one night — no bodies, no ransom note",
        "Someone is marking doors with a black handprint. The watch won't say why",
    ],
    "war":       [
        "Refugees are flooding the south road, speaking of columns of smoke on the horizon",
        "A conscription notice appeared on the temple board overnight",
        "Soldiers with unfamiliar colors are asking questions at the taverns",
    ],
    "scarcity":  [
        "The grain merchant's stall has been bare for three days and she won't say why",
        "Livestock are disappearing from outlying farms — no tracks, no noise",
        "A healer is rationing medicine. She's paying over market for herbs, urgently",
    ],
    "corruption":[
        "The city clerk was seen meeting a known fence at midnight",
        "Fines have tripled for minor offenses, but only in the poor quarter",
        "A watchman paid off a witness in broad daylight and nobody moved",
    ],
    "cult_activity":[
        "Symbols were carved into foundation stones of the old mill — nobody knows the script",
        "Three people reported the same dream: a white tower, a red moon, and silence",
        "A shrine was found in the sewer, recently lit, with fresh offerings",
    ],
    "magical_instability":[
        "Candles in the temple district have been burning green for two nights",
        "A child drew a map of a place that doesn't exist — in perfect detail",
        "Animals are refusing to enter the market square since the storm",
    ],
    "social_unrest":[
        "Someone nailed a list of names to the lord's gate. The names are nobles",
        "A crowd gathered at the well, then dispersed without a word when a guard appeared",
        "A pamphlet is circulating with no author — it knows things it shouldn't",
    ],
}

CLEANSING_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "gang_war": {
        "title": "Gang War Erupts",
        "description": "Rival factions settle old scores violently. Streets are unsafe after dark.",
        "warning_signs": ["Unusual silence in the thieves' quarter", "Old rivals spotted at the same tavern"],
        "pressure_trigger": "crime",
        "threshold": 0.7,
    },
    "fire": {
        "title": "Warehouse District Fire",
        "description": "A fire sweeps through the warehouse district, erasing secrets and records.",
        "warning_signs": ["Smell of lamp oil on dry timber", "A nervous arsonist selling his tools"],
        "pressure_trigger": "crime",
        "threshold": 0.65,
    },
    "political_crackdown": {
        "title": "Crackdown Declared",
        "description": "Authorities purge known criminals and dissidents. Leads go cold, informants disappear.",
        "warning_signs": ["Extra guards posted at city gates", "Pamphlets confiscated without comment"],
        "pressure_trigger": "corruption",
        "threshold": 0.75,
    },
    "plague": {
        "title": "Plague Breaks Out",
        "description": "A sickness spreads, closing markets and sending the desperate to the temple.",
        "warning_signs": ["Healer refuses new patients", "Dead rats piling near the docks"],
        "pressure_trigger": "scarcity",
        "threshold": 0.8,
    },
    "monster_outbreak": {
        "title": "Creature Outbreak",
        "description": "Something has driven beasts from their territory. Roads are cut off.",
        "warning_signs": ["Tracks outside the normal hunting grounds", "Livestock deaths with no explanation"],
        "pressure_trigger": "magical_instability",
        "threshold": 0.7,
    },
    "magical_storm": {
        "title": "Magical Storm",
        "description": "Wild magic tears through a district, reshaping buildings and erasing memories.",
        "warning_signs": ["Ley line fluctuations", "Compasses spinning without cause"],
        "pressure_trigger": "magical_instability",
        "threshold": 0.75,
    },
    "famine": {
        "title": "Famine Tightens",
        "description": "Food stores collapse. People leave, hoard, and turn on each other.",
        "warning_signs": ["Bakers cutting loaf size", "Soup kitchens overwhelmed"],
        "pressure_trigger": "scarcity",
        "threshold": 0.85,
    },
}

ANTAGONIST_OPERATIONS: Dict[AntagonistMO, List[str]] = {
    "secretive":   ["disappearance", "coded_message_interception", "cell_activation", "evidence_destruction"],
    "spectacle":   ["public_execution", "symbol_display", "dramatic_proclamation", "theatrical_murder"],
    "manipulative":["blackmail", "faction_infiltration", "rumor_campaign", "betrayal_setup"],
    "chaotic":     ["unstable_magic_release", "unpredictable_attack", "madness_spread", "reality_distortion"],
    "brute_force": ["district_occupation", "trade_route_raid", "resource_seizure", "forced_tribute"],
    "dramatic":    ["personal_challenge", "theatrical_clue_drop", "emotional_pressure", "public_speech"],
}


def _clamp(v: float) -> float:
    return round(max(0.0, min(1.0, float(v))), 3)

def _now() -> datetime:
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════
# PRESSURE TICK — world progresses when time passes
# ═══════════════════════════════════════════════════════════════════

def tick_region_pressure(
    region: RegionalPressure,
    trigger: str,
    active_quest_count: int = 0,
    antagonist_influence: float = 0.0,
) -> Tuple[RegionalPressure, List[str]]:
    """
    Advance a region's pressure state.
    Returns updated region + list of narrative changes for the DM log.
    """
    intensity = PRESSURE_TICK_INTENSITY.get(trigger, 0.08)
    region = deepcopy(region)
    changes: List[str] = []

    # Active quests reduce pressure slightly — the player is doing something
    quest_dampener = min(0.03 * active_quest_count, 0.12)

    # Antagonist influence amplifies pressure
    antag_boost = antagonist_influence * 0.15

    def drift(current: float, base_drift: float) -> float:
        return _clamp(current + (base_drift + antag_boost - quest_dampener) * intensity)

    # Natural pressure drift (unresolved wounds accumulate slowly)
    old = region.dict()
    region.crime           = drift(region.crime,           0.04)
    region.scarcity        = drift(region.scarcity,        0.03)
    region.social_unrest   = drift(region.social_unrest,   0.03)
    region.corruption      = drift(region.corruption,      0.02)
    region.cult_activity   = drift(region.cult_activity,   0.01)
    region.magical_instability = drift(region.magical_instability, 0.01)
    region.war             = _clamp(region.war + antag_boost * intensity * 0.5)

    # Derived state: recompute from pressure axes
    derived = {k: 0.0 for k in ["guard_presence", "fear", "rumor_density", "faction_activity", "price_pressure"]}
    for axis, flows in PRESSURE_TO_STATE.items():
        axis_val = getattr(region, axis, 0.0)
        for state_key, weight in flows.items():
            if state_key in derived:
                derived[state_key] += axis_val * weight

    region.guard_presence  = _clamp(derived["guard_presence"])
    region.fear            = _clamp(derived["fear"])
    region.rumor_density   = _clamp(derived["rumor_density"])
    region.faction_activity= _clamp(derived["faction_activity"])
    region.price_pressure  = _clamp(derived["price_pressure"])
    region.last_ticked     = _now()

    # Narrate significant changes
    for axis in ["crime","war","scarcity","corruption","cult_activity","magical_instability","social_unrest"]:
        delta = getattr(region, axis) - old.get(axis, 0.0)
        if delta >= 0.05:
            changes.append(f"{region.region_name}: {axis.replace('_',' ')} pressure rising ({getattr(region,axis):.2f})")

    logger.info(f"🌍 Tick [{trigger}] {region.region_name} — pressure: {region.total_pressure:.2f} [{region.pressure_label}]")
    return region, changes


# ═══════════════════════════════════════════════════════════════════
# HOOK GENERATION — pressure made visible
# ═══════════════════════════════════════════════════════════════════

def generate_hooks_from_pressure(
    campaign_id: str,
    region: RegionalPressure,
    existing_hook_count: int = 0,
) -> List[Hook]:
    """
    Generate 0–3 new hooks from a region's pressure state.
    High-pressure axes that exceed thresholds spawn visible events.
    """
    hooks: List[Hook] = []
    max_new = max(0, 3 - existing_hook_count)
    if max_new == 0:
        return hooks

    # Axes above 0.35 are "hot" — they can spawn hooks
    hot_axes = sorted(
        [(axis, getattr(region, axis)) for axis in
         ["crime","war","scarcity","corruption","cult_activity","magical_instability","social_unrest"]
         if getattr(region, axis, 0.0) >= 0.35],
        key=lambda x: -x[1]
    )

    for axis, pressure_val in hot_axes[:max_new]:
        templates = HOOK_TEMPLATES.get(axis, [])
        if not templates:
            continue

        desc = random.choice(templates)
        importance = _clamp(pressure_val * 0.8 + random.uniform(0.05, 0.15))

        hook = Hook(
            campaign_id=campaign_id,
            region_id=region.region_id,
            hook_type=_axis_to_hook_type(axis),
            title=f"[{axis.replace('_',' ').title()}] Disturbance in {region.region_name}",
            description=desc,
            hidden_truth=f"This is a symptom of {axis.replace('_',' ')} pressure (level {pressure_val:.2f}).",
            source_pressure_axes=[axis],
            importance_score=importance,
        )
        hooks.append(hook)
        logger.info(f"🪝 Hook generated: {hook.title}")

    return hooks


def _axis_to_hook_type(axis: str) -> HookType:
    mapping = {
        "crime": "visible_clue",
        "war": "faction_movement",
        "scarcity": "npc_warning",
        "corruption": "strange_behavior",
        "cult_activity": "environmental_sign",
        "magical_instability": "environmental_sign",
        "social_unrest": "rumor",
    }
    return mapping.get(axis, "rumor")


# ═══════════════════════════════════════════════════════════════════
# LEAD SYSTEM — player engages with a hook
# ═══════════════════════════════════════════════════════════════════

def hook_to_lead(hook: Hook, character_id: str, player_notes: str = "") -> Lead:
    """Convert a noticed hook into a trackable lead."""
    importance = build_importance(
        player_interest=0.7,
        emotional_weight=0.4,
        plot_relevance=0.6 if hook.source_antagonist_operation_id else 0.4,
        recency=1.0,
        faction_relevance=0.3,
        protected_from_cleanup=True,
        reasons=["player_noticed_hook"],
    )
    lead = Lead(
        campaign_id=hook.campaign_id,
        character_id=character_id,
        title=hook.title,
        summary=hook.description,
        player_notes=player_notes,
        source_hook_id=hook.id,
        importance_score=importance["score"],
        narrative_importance=importance,
    )
    logger.info(f"📋 Lead created: {lead.title} (importance: {importance['score']})")
    return lead


def score_lead_importance(lead: Lead) -> float:
    """Recompute importance score for an existing lead."""
    data = lead.dict()
    interacted = bool(data.get("player_notes") or lead.status in {"active", "resolved"})
    linked_quest = bool(data.get("linked_quest_id"))

    importance = build_importance(
        player_interest=0.85 if interacted else 0.3,
        emotional_weight=0.65 if lead.status == "active" else 0.3,
        plot_relevance=0.85 if linked_quest else (0.55 if lead.status == "active" else 0.3),
        recency=recency_score(lead.updated_at),
        faction_relevance=min(1.0, 0.2 + 0.2 * len(lead.related_faction_ids)),
        protected_from_cleanup=interacted,
        reasons=["lead"],
    )
    return importance["score"]


# ═══════════════════════════════════════════════════════════════════
# ANTAGONIST ENGINE — living pressure source
# ═══════════════════════════════════════════════════════════════════

def generate_antagonist_operation(
    antagonist: Antagonist,
    region_id: str,
    player_level: int = 1,
) -> AntagonistOperation:
    """
    The antagonist acts. Each operation creates visible effects and hook seeds.
    """
    op_types = ANTAGONIST_OPERATIONS.get(antagonist.mo, ["unknown_operation"])
    op_type = random.choice(op_types)

    # Escalation value grows with antagonist level and player progress
    escalation = _clamp(antagonist.escalation_level * 0.6 + (player_level / 20) * 0.4)

    visible, hidden, seeds = _build_operation_effects(op_type, antagonist)

    operation = AntagonistOperation(
        antagonist_id=antagonist.id,
        operation_type=op_type,
        target_region_id=region_id,
        description=f"{antagonist.name} executes a {op_type.replace('_',' ')} operation in the region.",
        visible_effects=visible,
        hidden_effects=hidden,
        generated_hook_seeds=seeds,
        escalation_value=escalation,
    )

    logger.info(f"👁️ Antagonist operation: {antagonist.name} → {op_type} in {region_id}")
    return operation


def _build_operation_effects(
    op_type: str,
    antagonist: Antagonist,
) -> Tuple[List[str], List[str], List[str]]:
    effects = {
        "disappearance":        (["A prominent figure has gone missing without notice"], ["Abducted by the antagonist's agents"], ["missing_person"]),
        "evidence_destruction": (["Records in the archive are charred and unreadable"], ["Evidence linking the antagonist was destroyed"], ["strange_behavior"]),
        "blackmail":            (["A local official reversed a long-standing policy overnight"], ["Official is being coerced"], ["strange_behavior", "rumor"]),
        "public_execution":     (["A body was displayed in the square with a symbol carved into it"], ["Warning to anyone who opposes them"], ["visible_clue", "faction_movement"]),
        "rumor_campaign":       (["Ugly rumors circulate about a respected figure; no one can trace the source"], ["Deliberate disinformation from the antagonist"], ["rumor"]),
        "district_occupation":  (["Armed figures in foreign dress control access to the docks"], ["The antagonist seizes a strategic resource point"], ["faction_movement", "visible_clue"]),
        "unstable_magic_release":(["Arcane energy warped a building overnight — stones are wrong"], ["The antagonist tests a weapon"], ["environmental_sign"]),
        "personal_challenge":   (["A sealed letter arrived — addressed to the adventurer by name"], ["The antagonist is aware of the player and is sending a message"], ["npc_warning"]),
    }
    default = (
        [f"Something changed in the district overnight — people are quieter"],
        [f"The antagonist's influence is spreading"],
        ["rumor"]
    )
    return effects.get(op_type, default)


def advance_antagonist_phase(antagonist: Antagonist, player_level: int) -> Antagonist:
    """
    Update the antagonist's act phase and escalation based on player level.
    Handles the false showdown and act structure from the design doc.
    """
    antagonist = deepcopy(antagonist)

    if player_level >= 9 and antagonist.act_phase != "act4_resolution":
        antagonist.act_phase = "act4_resolution"
        antagonist.escalation_level = _clamp(antagonist.escalation_level + 0.1)
        logger.info(f"🎭 {antagonist.name} enters ACT 4 — Resolution")

    elif player_level >= 5 and antagonist.act_phase in ("act1_shadow", "act2_pressure"):
        antagonist.act_phase = "act3_confrontation"
        antagonist.escalation_level = _clamp(antagonist.escalation_level + 0.15)
        logger.info(f"🎭 {antagonist.name} enters ACT 3 — False Showdown available")

    elif player_level >= 3 and antagonist.act_phase == "act1_shadow":
        antagonist.act_phase = "act2_pressure"
        # Introduce the antagonist signature: they're here but not fully revealed
        antagonist.revealed_signature = True
        antagonist.escalation_level = _clamp(antagonist.escalation_level + 0.1)
        logger.info(f"🎭 {antagonist.name} enters ACT 2 — pressure becomes systemic")

    antagonist.updated_at = _now()
    return antagonist


def get_antagonist_reveal_text(antagonist: Antagonist) -> Optional[str]:
    """
    Generate the Act 2 introduction text — what the player perceives.
    Does NOT reveal motive, full network, or final plan.
    """
    if not antagonist.revealed_signature:
        return None

    mo_intros = {
        "secretive":    "Something methodical is moving beneath the surface. People disappear. Evidence vanishes. Whatever is operating here has been doing it for a long time.",
        "spectacle":    "The act was deliberate. Theatrical. Whoever did this wanted it seen — wanted it remembered. This is not a criminal. This is a statement.",
        "manipulative": "Three unrelated people made the same decision this week, all against their interest. Someone is pulling threads. Someone with patience and reach.",
        "chaotic":      "There is no pattern that makes sense — and that itself is the pattern. Whatever is operating here thrives on your confusion.",
        "brute_force":  "They came with enough force to make refusal impossible. This isn't desperation. This is a show of what they can afford to spend.",
        "dramatic":     "The letter was addressed to you by name. They know who you are. They want you to know they know. This just became personal.",
    }
    return mo_intros.get(antagonist.mo, "Something serious just entered the world.")


# ═══════════════════════════════════════════════════════════════════
# CLEANSING ENGINE — narrative garbage collection
# ═══════════════════════════════════════════════════════════════════

def check_cleansing_conditions(
    region: RegionalPressure,
    leads: List[Lead],
    campaign_id: str,
) -> Optional[CleansingEvent]:
    """
    Evaluate whether pressure is high enough to trigger a cleansing event.
    Stale, low-importance content may be recycled into new hooks.
    High-importance content becomes story escalation instead.
    """
    for event_key, template in CLEANSING_TEMPLATES.items():
        trigger_axis = template["pressure_trigger"]
        threshold = template["threshold"]
        axis_val = getattr(region, trigger_axis, 0.0)

        if axis_val < threshold:
            continue

        # Separate stale low-importance leads from important ones
        stale_leads = [
            l for l in leads
            if l.status in ("ignored", "abandoned")
            and l.importance_score < 0.35
            and ((_now() - l.updated_at).days > 5 if l.updated_at else True)
        ]
        important_leads = [
            l for l in leads
            if l.importance_score >= 0.5 or l.status == "active"
        ]

        archived_ids = [l.id for l in stale_leads[:4]]
        transformed_ids = [l.id for l in important_leads[:2]]

        # New hook seeds born from the chaos
        new_seeds = template.get("new_hook_seeds") or list(template.get("warning_signs", []))[:2]

        cleansing = CleansingEvent(
            campaign_id=campaign_id,
            region_id=region.region_id,
            cleansing_type=event_key,  # type: ignore
            title=template["title"],
            description=template["description"],
            warning_signs=template.get("warning_signs", []),
            archived_lead_ids=archived_ids,
            transformed_lead_ids=transformed_ids,
            new_hook_seeds=new_seeds,
            player_intervention_possible=len(important_leads) > 0,
        )

        logger.warning(
            f"🌪️ Cleansing condition met: [{event_key}] in {region.region_name} "
            f"(axis={trigger_axis}, val={axis_val:.2f})"
        )
        return cleansing

    return None


def apply_cleansing_to_leads(
    leads: List[Lead],
    cleansing: CleansingEvent,
) -> List[Lead]:
    """
    Apply cleansing: archive stale leads, transform important ones.
    Important leads become new hooks, not silent deletions.
    """
    updated: List[Lead] = []
    for lead in leads:
        if lead.id in cleansing.archived_lead_ids:
            lead = deepcopy(lead)
            lead.status = "sealed"
            lead.player_notes = (
                lead.player_notes + f"\n[Sealed by: {cleansing.title}]"
            ).strip()
            lead.updated_at = _now()
            logger.info(f"📦 Lead sealed by cleansing: {lead.title}")

        elif lead.id in cleansing.transformed_lead_ids:
            lead = deepcopy(lead)
            lead.status = "transformed"
            lead.player_notes = (
                lead.player_notes + f"\n[Transformed by: {cleansing.title} — this became something else]"
            ).strip()
            lead.updated_at = _now()
            logger.info(f"🔄 Lead transformed by cleansing: {lead.title}")

        updated.append(lead)
    return updated


# ═══════════════════════════════════════════════════════════════════
# CAMPAIGN MEMORY — compress what mattered
# ═══════════════════════════════════════════════════════════════════

def compress_to_campaign_memory(
    state: CampaignPressureState,
) -> CampaignPressureState:
    """
    Compress old, resolved content into campaign memory.
    Protects emotionally important content from being silently lost.
    """
    state = deepcopy(state)
    memory_entries: List[Dict[str, Any]] = list(state.campaign_memory)

    # Archive resolved leads that have high importance (they become history, not noise)
    for lead in state.leads:
        if lead.status in ("resolved",) and lead.importance_score >= 0.5:
            memory_entries.append({
                "type": "resolved_lead",
                "title": lead.title,
                "summary": lead.summary,
                "importance": lead.importance_score,
                "character_id": lead.character_id,
                "compressed_at": _now().isoformat(),
            })

    # Archive completed antagonist operations
    for ant in state.antagonists:
        for op in ant.operations:
            if op.player_interfered:
                memory_entries.append({
                    "type": "antagonist_operation_interfered",
                    "antagonist": ant.name,
                    "operation": op.operation_type,
                    "region": op.target_region_id,
                    "compressed_at": _now().isoformat(),
                })

    # Limit memory to last 50 entries (older entries become world history flavor)
    state.campaign_memory = memory_entries[-50:]
    state.updated_at = _now()

    return state


# ═══════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATION — full pressure cycle
# ═══════════════════════════════════════════════════════════════════

def run_pressure_cycle(
    state: CampaignPressureState,
    trigger: str,
    region_id: Optional[str] = None,
    active_quest_count: int = 0,
) -> Tuple[CampaignPressureState, Dict[str, Any]]:
    """
    Run one full pressure cycle for the campaign.
    Returns updated state + a summary dict for logging/frontend.
    """
    state = deepcopy(state)
    summary: Dict[str, Any] = {
        "trigger": trigger,
        "tick_changes": [],
        "new_hooks": [],
        "cleansing_events": [],
        "antagonist_actions": [],
        "phase_changes": [],
    }

    # 1. Tick regional pressures
    regions_to_tick = (
        [state.regional_pressures[region_id]] if region_id and region_id in state.regional_pressures
        else list(state.regional_pressures.values())
    )

    for region in regions_to_tick:
        # Find antagonist influence on this region
        antag_influence = max(
            (a.regional_influence.get(region.region_id, 0.0) for a in state.antagonists),
            default=0.0
        )
        updated_region, changes = tick_region_pressure(
            region, trigger, active_quest_count, antag_influence
        )
        state.regional_pressures[region.region_id] = updated_region
        summary["tick_changes"].extend(changes)

        # 2. Generate new hooks from pressure
        existing_visible = [
            h for h in state.hooks
            if h.region_id == region.region_id and h.status == "visible"
        ]
        new_hooks = generate_hooks_from_pressure(
            state.campaign_id, updated_region, len(existing_visible)
        )
        state.hooks.extend(new_hooks)
        summary["new_hooks"].extend([h.title for h in new_hooks])

        # 3. Check cleansing conditions
        region_leads = [l for l in state.leads if True]  # all leads for now
        cleansing = check_cleansing_conditions(updated_region, region_leads, state.campaign_id)
        if cleansing:
            state.cleansing_events.append(cleansing)
            state.leads = apply_cleansing_to_leads(state.leads, cleansing)
            summary["cleansing_events"].append({
                "type": cleansing.cleansing_type,
                "title": cleansing.title,
                "archived": len(cleansing.archived_lead_ids),
                "transformed": len(cleansing.transformed_lead_ids),
            })

    # 4. Antagonist phase advancement and operations
    for i, antagonist in enumerate(state.antagonists):
        updated_ant = advance_antagonist_phase(antagonist, state.player_level)
        if updated_ant.act_phase != antagonist.act_phase:
            reveal_text = get_antagonist_reveal_text(updated_ant)
            summary["phase_changes"].append({
                "antagonist": updated_ant.name,
                "new_phase": updated_ant.act_phase,
                "reveal_text": reveal_text,
            })

        # Antagonist acts on major triggers
        if trigger in ("major_quest_completion", "next_day") and updated_ant.act_phase != "act1_shadow":
            if state.regional_pressures:
                target_region = random.choice(list(state.regional_pressures.keys()))
                operation = generate_antagonist_operation(updated_ant, target_region, state.player_level)
                updated_ant.operations.append(operation)

                # Operation affects region pressure
                if target_region in state.regional_pressures:
                    r = state.regional_pressures[target_region]
                    r.crime = _clamp(r.crime + operation.escalation_value * 0.3)
                    r.faction_activity = _clamp(r.faction_activity + operation.escalation_value * 0.2)

                summary["antagonist_actions"].append({
                    "antagonist": updated_ant.name,
                    "operation": operation.operation_type,
                    "region": target_region,
                    "visible_effects": operation.visible_effects,
                })

        state.antagonists[i] = updated_ant

    # 5. Compress old content to campaign memory
    state = compress_to_campaign_memory(state)

    state.updated_at = _now()
    logger.info(f"✅ Pressure cycle complete — trigger: {trigger}, hooks: {len(summary['new_hooks'])}, cleansing: {len(summary['cleansing_events'])}")
    return state, summary


# ═══════════════════════════════════════════════════════════════════
# WORLD STATE SUMMARY — for DM / frontend
# ═══════════════════════════════════════════════════════════════════

def build_world_pressure_summary(state: CampaignPressureState) -> Dict[str, Any]:
    """Build a human-readable summary of the current pressure state."""
    regions = []
    for rid, region in state.regional_pressures.items():
        regions.append({
            "id": rid,
            "name": region.region_name,
            "pressure_label": region.pressure_label,
            "total_pressure": region.total_pressure,
            "axes": {
                "crime": region.crime,
                "war": region.war,
                "scarcity": region.scarcity,
                "corruption": region.corruption,
                "cult_activity": region.cult_activity,
                "magical_instability": region.magical_instability,
                "social_unrest": region.social_unrest,
            },
            "derived": {
                "guard_presence": region.guard_presence,
                "fear": region.fear,
                "rumor_density": region.rumor_density,
                "faction_activity": region.faction_activity,
                "price_pressure": region.price_pressure,
            },
        })

    active_leads = [l for l in state.leads if l.status == "active"]
    visible_hooks = [h for h in state.hooks if h.status == "visible"]
    antagonist_phases = [
        {"name": a.name, "phase": a.act_phase, "escalation": a.escalation_level}
        for a in state.antagonists
    ]

    return {
        "campaign_id": state.campaign_id,
        "act_phase": state.act_phase,
        "player_level": state.player_level,
        "regions": regions,
        "active_leads": len(active_leads),
        "visible_hooks": len(visible_hooks),
        "active_cleansing": len([c for c in state.cleansing_events if not c.resolved]),
        "antagonists": antagonist_phases,
        "campaign_memory_entries": len(state.campaign_memory),
    }
