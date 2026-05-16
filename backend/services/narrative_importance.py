"""Backend-only narrative importance scoring.

The score is intentionally deterministic and side-effect free. It gives later
world progression/cleanup systems a shared way to reason about what should be
protected without deleting or archiving anything by itself.
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

PROTECTION_BOOST = 0.15


def _clamp(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:  # noqa: BLE001
        return default


def _as_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return {
        key: getattr(obj, key)
        for key in dir(obj)
        if not key.startswith("_") and not callable(getattr(obj, key, None))
    }


def _parse_dt(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except Exception:  # noqa: BLE001
            return None
    return None


def recency_score(value: Any, now: Optional[datetime] = None) -> float:
    dt = _parse_dt(value)
    if not dt:
        return 0.2
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    days = max(0, (current - dt).days)
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


def build_importance(
    *,
    player_interest: float,
    emotional_weight: float,
    plot_relevance: float,
    recency: float,
    faction_relevance: float,
    protected_from_cleanup: bool,
    reasons: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    factors = {
        "player_interest": _clamp(player_interest),
        "emotional_weight": _clamp(emotional_weight),
        "plot_relevance": _clamp(plot_relevance),
        "recency": _clamp(recency),
        "faction_relevance": _clamp(faction_relevance),
        "protected_from_cleanup": 1.0 if protected_from_cleanup else 0.0,
    }
    score = sum(factors[key] * weight for key, weight in WEIGHTS.items())
    if protected_from_cleanup:
        score += PROTECTION_BOOST
    score = round(_clamp(score), 3)
    return {
        "score": score,
        "factors": factors,
        "protected_from_cleanup": bool(protected_from_cleanup),
        "reasons": list(reasons or []),
    }


def score_lead(lead: Any, now: Optional[datetime] = None) -> Dict[str, Any]:
    data = _as_dict(lead)
    status = str(data.get("status") or "unexplored").lower()
    related_npcs = data.get("related_npc_ids") or []
    related_factions = data.get("related_faction_ids") or []
    player_notes = (data.get("player_notes") or "").strip()
    linked_quest = bool(data.get("linked_quest_id"))
    interacted = bool(player_notes) or status in {"active", "resolved"}
    reasons = []
    if interacted:
        reasons.append("player_interacted")
    if linked_quest:
        reasons.append("linked_quest")
    if related_npcs:
        reasons.append("npc_linked")
    if related_factions:
        reasons.append("faction_linked")
    return build_importance(
        player_interest=0.75 if interacted else (0.45 if related_npcs else 0.25),
        emotional_weight=0.65 if status == "active" else (0.45 if related_npcs else 0.25),
        plot_relevance=0.8 if linked_quest else (0.55 if status == "active" else 0.3),
        recency=recency_score(data.get("updated_at") or data.get("created_at"), now),
        faction_relevance=min(1.0, 0.25 + 0.2 * len(related_factions)),
        protected_from_cleanup=interacted,
        reasons=reasons,
    )


def score_quest(quest: Any, now: Optional[datetime] = None) -> Dict[str, Any]:
    data = _as_dict(quest)
    status = str(data.get("status") or "active").lower()
    objectives = data.get("objectives") or []
    completed = data.get("completed_objectives") or []
    related_npcs = data.get("related_npc_ids") or []
    related_factions = data.get("related_faction_ids") or []
    interacted = status in {"active", "accepted", "in_progress", "completed"} or bool(completed)
    reasons = ["quest"]
    if interacted:
        reasons.append("player_interacted")
    if related_npcs or data.get("quest_giver_npc_id"):
        reasons.append("npc_linked")
    return build_importance(
        player_interest=0.85 if status in {"active", "accepted", "in_progress"} else 0.55,
        emotional_weight=0.75 if status == "completed" else (0.55 if interacted else 0.25),
        plot_relevance=0.85 if status in {"active", "accepted", "in_progress"} else 0.6,
        recency=recency_score(data.get("updated_at") or data.get("last_updated") or data.get("created_at"), now),
        faction_relevance=min(1.0, 0.2 + 0.2 * len(related_factions)),
        protected_from_cleanup=interacted,
        reasons=reasons + (["has_objectives"] if objectives else []),
    )


def score_npc(npc: Any, now: Optional[datetime] = None) -> Dict[str, Any]:
    data = _as_dict(npc)
    relationship = str(data.get("relationship_to_party") or "neutral").lower()
    related_quests = data.get("related_quest_ids") or []
    faction_id = data.get("faction_id")
    has_story_role = bool(data.get("wants") or data.get("offered") or related_quests)
    interacted = bool(data.get("first_met") or data.get("last_updated"))
    emotional = 0.75 if relationship in {"ally", "hostile", "suspicious"} else 0.4
    return build_importance(
        player_interest=0.7 if interacted else 0.35,
        emotional_weight=emotional,
        plot_relevance=0.75 if related_quests or has_story_role else 0.35,
        recency=recency_score(data.get("last_updated") or data.get("first_met"), now),
        faction_relevance=0.65 if faction_id else 0.2,
        protected_from_cleanup=interacted or relationship in {"ally", "hostile"},
        reasons=[
            reason
            for reason, enabled in (
                ("player_met", interacted),
                ("quest_linked", bool(related_quests)),
                ("faction_linked", bool(faction_id)),
                ("charged_relationship", relationship in {"ally", "hostile", "suspicious"}),
            )
            if enabled
        ],
    )


def score_knowledge_card(card: Any, now: Optional[datetime] = None) -> Dict[str, Any]:
    data = _as_dict(card)
    card_type = str(data.get("type") or "").lower()
    status = str(data.get("status") or "").lower()
    tags = [str(tag).lower() for tag in (data.get("tags") or [])]
    player_marked = data.get("source") == "player-remember" or "remembered" in tags
    is_quest = card_type == "quest" or "quest" in tags
    is_lead = card_type == "lead" or "lead" in tags
    is_npc = card_type == "npc" or "npc" in tags
    faction_tags = [tag for tag in tags if "faction" in tag]
    interacted = player_marked or status in {"active", "completed"} or is_quest
    return build_importance(
        player_interest=0.9 if player_marked else (0.7 if interacted else 0.35),
        emotional_weight=0.65 if is_npc or status == "completed" else 0.35,
        plot_relevance=0.85 if is_quest else (0.6 if is_lead else 0.4),
        recency=recency_score(data.get("updatedAt") or data.get("updated_at"), now),
        faction_relevance=min(1.0, 0.2 + 0.25 * len(faction_tags)),
        protected_from_cleanup=interacted,
        reasons=[
            reason
            for reason, enabled in (
                ("player_interacted", interacted),
                ("player_remembered", player_marked),
                ("quest_card", is_quest),
                ("lead_card", is_lead),
                ("npc_card", is_npc),
                ("faction_linked", bool(faction_tags)),
            )
            if enabled
        ],
    )


def existing_or_score(kind: str, item: Any, now: Optional[datetime] = None) -> Dict[str, Any]:
    data = _as_dict(item)
    existing = data.get("narrative_importance")
    if isinstance(existing, dict) and "score" in existing:
        return existing
    if kind == "lead":
        return score_lead(item, now)
    if kind == "quest":
        return score_quest(item, now)
    if kind == "npc":
        return score_npc(item, now)
    if kind == "card":
        return score_knowledge_card(item, now)
    return build_importance(
        player_interest=0.2,
        emotional_weight=0.2,
        plot_relevance=0.2,
        recency=0.2,
        faction_relevance=0.1,
        protected_from_cleanup=False,
        reasons=["fallback"],
    )
