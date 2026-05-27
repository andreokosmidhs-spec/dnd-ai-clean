"""
Faction mechanics — perk requirement checking, reputation tiers,
DM prompt formatting, and NPC-to-faction cross-linking.

Faction cards store: purpose, values, tenets, hierarchy (list of tiers with
role/function/min_level/filled_by), known_members (player-discovered NPCs),
resources (income_gp, treasury_gp, controlled_areas, hideout, important_items,
recruitment_rate), tier_perks (bonuses with typed requirements), reputation int.

Perk requirements can be:
  area_control   — faction.controlled_areas contains value
  npc_position   — hierarchy[tier].filled_by is set (alive NPC in slot)
  income_min     — faction.income_gp >= value
  treasury_min   — faction.treasury_gp >= value
  item_held      — faction.important_items contains value

When any requirement fails, the perk is SUSPENDED (not removed).
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Reputation tier
# ---------------------------------------------------------------------------

_REPUTATION_TIERS: list[dict[str, Any]] = [
    {
        "min": -100,
        "max": -60,
        "label": "reviled",
        "status": "hostile",
        "description": "Members attack on sight.",
    },
    {
        "min": -59,
        "max": -20,
        "label": "hostile",
        "status": "hostile",
        "description": "Refuse cooperation; may report the player to authorities.",
    },
    {
        "min": -19,
        "max": 19,
        "label": "neutral",
        "status": "neutral",
        "description": "No special treatment; standard social interactions.",
    },
    {
        "min": 20,
        "max": 49,
        "label": "respected",
        "status": "friendly",
        "description": "Cooperate willingly and offer basic help.",
    },
    {
        "min": 50,
        "max": 79,
        "label": "honored",
        "status": "friendly",
        "description": "Go out of their way to assist the player.",
    },
    {
        "min": 80,
        "max": 100,
        "label": "exalted",
        "status": "friendly",
        "description": "Leadership treats the player as a trusted ally; all perks accessible.",
    },
]


def reputation_tier(rep: int) -> dict[str, str]:
    """Map a reputation score (-100..+100) to one of six named tiers.

    Returns a dict with keys:
      label       — tier name string
      status      — "hostile" | "neutral" | "friendly"
      description — short prose description of how faction members behave
    """
    clamped = max(-100, min(100, rep))
    for tier in _REPUTATION_TIERS:
        if tier["min"] <= clamped <= tier["max"]:
            return {
                "label": tier["label"],
                "status": tier["status"],
                "description": tier["description"],
            }
    # Fallback — should never be reached given the ranges above cover -100..+100
    return {
        "label": "neutral",
        "status": "neutral",
        "description": "No special treatment; standard social interactions.",
    }


# ---------------------------------------------------------------------------
# Requirement checking
# ---------------------------------------------------------------------------

def _check_requirement(req: dict[str, Any], faction: dict[str, Any]) -> tuple[bool, str]:
    """Evaluate a single perk requirement against the current faction state.

    Args:
        req:     Requirement dict. Must have at least a "type" key plus a
                 type-specific "value" or "tier" key.
        faction: Faction card dict (resources are stored at the top level or
                 under a "resources" sub-dict — both layouts are handled).

    Returns:
        (is_met, failure_reason) where failure_reason is "" when is_met is True.
    """
    req_type: str = req.get("type", "")

    # Resources may live directly on faction or under faction["resources"].
    resources: dict[str, Any] = faction.get("resources", {})

    def _res(key: str, default: Any = None) -> Any:
        """Return faction[key] falling back to faction["resources"][key]."""
        if key in faction:
            return faction[key]
        return resources.get(key, default)

    if req_type == "area_control":
        value: str = req.get("value", "")
        controlled: list[str] = _res("controlled_areas", [])
        if value not in controlled:
            return False, f"Area not controlled: {value!r}"
        return True, ""

    if req_type == "npc_position":
        tier_name: str = req.get("tier", "")
        hierarchy: list[dict[str, Any]] = faction.get("hierarchy", [])
        for tier_entry in hierarchy:
            role: str = tier_entry.get("role", "")
            if role == tier_name or tier_entry.get("function", "") == tier_name:
                filled_by = tier_entry.get("filled_by")
                if not filled_by:
                    return False, f"Hierarchy position unfilled: {tier_name!r}"
                return True, ""
        # Tier name not found in hierarchy at all — treat as unmet
        return False, f"Hierarchy tier not found: {tier_name!r}"

    if req_type == "income_min":
        minimum: float = float(req.get("value", 0))
        income: float = float(_res("income_gp", 0))
        if income < minimum:
            return False, f"Income {income} gp < required {minimum} gp"
        return True, ""

    if req_type == "treasury_min":
        minimum = float(req.get("value", 0))
        treasury: float = float(_res("treasury_gp", 0))
        if treasury < minimum:
            return False, f"Treasury {treasury} gp < required {minimum} gp"
        return True, ""

    if req_type == "item_held":
        item: str = req.get("value", "")
        items: list[str] = _res("important_items", [])
        if item not in items:
            return False, f"Item not held: {item!r}"
        return True, ""

    # Unknown requirement type — do not block the perk
    return True, ""


# ---------------------------------------------------------------------------
# Perk state computation
# ---------------------------------------------------------------------------

def compute_perk_states(faction: dict[str, Any]) -> list[dict[str, Any]]:
    """Return each perk in faction["tier_perks"] annotated with its live state.

    Each returned dict is a shallow copy of the original perk dict extended
    with:
      active            — True if all requirements are met
      suspended_reasons — list of failure reason strings (empty when active)
    """
    results: list[dict[str, Any]] = []
    tier_perks: list[dict[str, Any]] = faction.get("tier_perks", [])

    for perk in tier_perks:
        requirements: list[dict[str, Any]] = perk.get("requirements", [])
        suspended_reasons: list[str] = []

        for req in requirements:
            met, reason = _check_requirement(req, faction)
            if not met:
                suspended_reasons.append(reason)

        annotated = dict(perk)
        annotated["active"] = len(suspended_reasons) == 0
        annotated["suspended_reasons"] = suspended_reasons
        results.append(annotated)

    return results


# ---------------------------------------------------------------------------
# DM prompt formatting
# ---------------------------------------------------------------------------

def fmt_faction_for_dm(faction: dict[str, Any]) -> str:
    """Produce a compact multi-line string describing a faction for the DM prompt.

    Format (all sections are included only when data exists):

        FACTION: <name> | Rep: <+/-score> (<tier>) | Areas: <area1>, <area2>
          Purpose: <purpose, max 120 chars>
          ACTIVE PERKS: <name> (<bonus>); ...
          SUSPENDED PERKS: <name> [<first reason>]; ...
          Known members: <Name> [<role>], ...
          Hideout: <hideout>
          Tenets: <tenet1>; <tenet2>  (label: "Tenets — use for social manipulation DCs")
    """
    name: str = faction.get("title") or faction.get("name") or "Unknown Faction"

    # Reputation
    rep: int = int(faction.get("reputation", 0))
    rep_sign = "+" if rep >= 0 else ""
    tier_info = reputation_tier(rep)
    tier_label: str = tier_info["label"]

    # Resources sub-dict or top-level keys
    resources: dict[str, Any] = faction.get("resources", {})

    def _res(key: str, default: Any = None) -> Any:
        if key in faction:
            return faction[key]
        return resources.get(key, default)

    # Controlled areas
    controlled_areas: list[str] = _res("controlled_areas", [])
    areas_str = ", ".join(controlled_areas) if controlled_areas else "none"

    # Header line
    header = (
        f"FACTION: {name} | Rep: {rep_sign}{rep} ({tier_label}) | Areas: {areas_str}"
    )

    lines: list[str] = [header]

    # Purpose (truncated)
    purpose: str = faction.get("purpose", "").strip()
    if purpose:
        if len(purpose) > 120:
            purpose = purpose[:117].rstrip() + "..."
        lines.append(f"  Purpose: {purpose}")

    # Perk states
    perk_states = compute_perk_states(faction)

    active_parts: list[str] = []
    suspended_parts: list[str] = []

    for ps in perk_states:
        perk_name: str = ps.get("name", "Unnamed Perk")
        bonus: str = ps.get("bonus", "")
        shorthand = f"{perk_name} ({bonus})" if bonus else perk_name

        if ps["active"]:
            active_parts.append(shorthand)
        else:
            first_reason = ps["suspended_reasons"][0] if ps["suspended_reasons"] else "requirement unmet"
            suspended_parts.append(f"{shorthand} [{first_reason}]")

    if active_parts:
        lines.append(f"  ACTIVE PERKS: {'; '.join(active_parts)}")
    if suspended_parts:
        lines.append(f"  SUSPENDED PERKS: {'; '.join(suspended_parts)}")

    # Known members
    known_members: list[dict[str, Any]] = faction.get("known_members", [])
    if known_members:
        member_strs: list[str] = []
        for m in known_members:
            m_name: str = m.get("name", "Unknown")
            m_role: str = m.get("role", "")
            if m_role:
                member_strs.append(f"{m_name} [{m_role}]")
            else:
                member_strs.append(m_name)
        lines.append(f"  Known members: {', '.join(member_strs)}")

    # Hideout
    hideout: str = _res("hideout", "")
    if hideout:
        lines.append(f"  Hideout: {hideout}")

    # Tenets
    tenets: list[str] = faction.get("tenets", [])
    if tenets:
        tenets_str = "; ".join(tenets)
        lines.append(
            f"  Tenets — use for social manipulation DCs: {tenets_str}"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Multi-faction block builder
# ---------------------------------------------------------------------------

def build_factions_block(cards: list[dict[str, Any]]) -> str:
    """Build a formatted block of faction summaries for the DM system prompt.

    Filters cards where type == "faction", formats up to 6 of them, and joins
    the results with double newlines.

    Returns "(no faction cards)" when no faction cards are present.
    """
    faction_cards = [c for c in cards if c.get("type") == "faction"]

    if not faction_cards:
        return "(no faction cards)"

    # Cap at 6 to keep the DM context prompt lean
    faction_cards = faction_cards[:6]

    formatted = [fmt_faction_for_dm(fc) for fc in faction_cards]
    return "\n\n".join(formatted)
