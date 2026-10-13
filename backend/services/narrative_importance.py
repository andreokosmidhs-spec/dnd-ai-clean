"""Narrative importance scoring helpers.

Batch 1 scope:
- compute reusable importance factors
- no cleanup/deletion behavior
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional


WEIGHTS = {
    "player_interest": 0.25,
    "emotional_weight": 0.20,
    "plot_relevance": 0.20,
    "recency": 0.15,
    "faction_relevance": 0.10,
    "protected_from_cleanup": 0.10,
}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _norm_count(values: Optional[Iterable[Any]], cap: int = 5) -> float:
    if not values:
        return 0.0
    if isinstance(values, str):
        return 1.0 if values.strip() else 0.0
    count = len(list(values))
    return _clamp01(count / max(1, cap))


def _days_since(dt: Optional[datetime], now: datetime) -> float:
    if not dt:
        return 9999.0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (now - dt).total_seconds() / 86400.0


def _recency_score(updated_at: Optional[datetime], now: datetime) -> float:
    days = _days_since(updated_at, now)
    if days <= 1:
        return 1.0
    if days <= 3:
        return 0.8
    if days <= 7:
        return 0.6
    if days <= 14:
        return 0.4
    if days <= 30:
        return 0.2
    return 0.05


def score_narrative_importance(
    *,
    content_type: str,
    player_interest: float,
    emotional_weight: float,
    plot_relevance: float,
    recency: float,
    faction_relevance: float,
    protected_from_cleanup: bool,
) -> Dict[str, Any]:
    factors = {
        "content_type": content_type,
        "player_interest": _clamp01(player_interest),
        "emotional_weight": _clamp01(emotional_weight),
        "plot_relevance": _clamp01(plot_relevance),
        "recency": _clamp01(recency),
        "faction_relevance": _clamp01(faction_relevance),
        "protected_from_cleanup": 1.0 if protected_from_cleanup else 0.0,
    }
    weighted = sum(factors[k] * WEIGHTS[k] for k in WEIGHTS)
    # Explicit protection bonus so interacted content survives future cleanup.
    if protected_from_cleanup:
        weighted = min(1.0, weighted + 0.15)
    factors["score"] = round(weighted, 4)
    return factors


def score_lead(lead: Any, now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    interacted = bool(getattr(lead, "player_notes", "").strip()) or getattr(lead, "status", "") in {"active", "resolved"}
    emotional = 0.8 if getattr(lead, "status", "") == "active" else 0.45
    plot = 0.8 if getattr(lead, "linked_quest_id", None) else 0.55
    return score_narrative_importance(
        content_type="lead",
        player_interest=max(0.35, _norm_count(getattr(lead, "related_npc_ids", []))),
        emotional_weight=emotional,
        plot_relevance=plot,
        recency=_recency_score(getattr(lead, "updated_at", None), now),
        faction_relevance=max(0.1, _norm_count(getattr(lead, "related_faction_ids", []))),
        protected_from_cleanup=interacted,
    )


def score_quest(quest: Any, now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    status = getattr(quest, "status", "active")
    interacted = status in {"active", "completed"} or bool(getattr(quest, "completed_objectives", []))
    return score_narrative_importance(
        content_type="quest",
        player_interest=max(0.4, _norm_count(getattr(quest, "completed_objectives", []), cap=4)),
        emotional_weight=0.9 if status == "completed" else 0.7,
        plot_relevance=0.85 if status in {"active", "completed"} else 0.45,
        recency=_recency_score(getattr(quest, "last_updated", None), now),
        faction_relevance=max(0.1, _norm_count(getattr(quest, "related_faction_ids", []), cap=3)),
        protected_from_cleanup=interacted,
    )


def score_knowledge_card(card: Dict[str, Any], now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    tags = card.get("tags") or []
    card_type = card.get("type", "unknown")
    interacted = bool(card.get("player_interacted", False)) or card.get("status") in {"active", "completed"}
    return score_narrative_importance(
        content_type=f"knowledge_card:{card_type}",
        player_interest=max(0.3, _norm_count(tags, cap=6)),
        emotional_weight=0.75 if "relationship" in tags or card_type == "npc" else 0.45,
        plot_relevance=0.85 if card_type in {"quest", "lead", "npc", "knowledge"} else 0.5,
        recency=_recency_score(card.get("updatedAt"), now),
        faction_relevance=1.0 if "faction" in tags else 0.2,
        protected_from_cleanup=interacted,
    )
