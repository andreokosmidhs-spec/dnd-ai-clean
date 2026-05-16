"""Regional narrative tick service.

Ticks are backend-only world progression pulses fired when major time passes.
They update regional pressure state and emit debug summaries, but they do not
delete, archive, or hide any existing campaign content.
"""
from __future__ import annotations

import logging
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from services.narrative_importance import existing_or_score, score_knowledge_card

logger = logging.getLogger(__name__)


REGION_STATE_DEFAULTS = {
    "guard_presence": 0.2,
    "fear": 0.2,
    "rumor_density": 0.3,
    "faction_activity": 0.25,
    "scarcity": 0.15,
    "price_pressure": 0.15,
}

TRIGGER_INTENSITY = {
    "long_rest": 0.18,
    "travel": 0.12,
    "next_day": 0.20,
    "major_quest_completion": 0.24,
}

ACTIVE_QUEST_STATUSES = {"active", "accepted", "in_progress"}
INACTIVE_STATUSES = {"resolved", "abandoned", "failed", "dismissed", "completed"}


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _as_dict(value: Any) -> Dict[str, Any]:
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return dict(value)


def _iso(value: datetime) -> str:
    return value.isoformat()


def _region_name(region: Dict[str, Any], fallback: str) -> str:
    return region.get("name") or region.get("title") or fallback


class NarrativeTickService:
    """Compute and persist regional narrative progression."""

    async def run_tick(
        self,
        db,
        campaign_id: str,
        trigger: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        campaign = await db.campaigns.find_one({"campaign_id": campaign_id}, {"_id": 0})
        if not campaign:
            logger.warning("Narrative tick skipped; campaign not found: %s", campaign_id)
            return {"ok": False, "reason": "campaign_not_found"}

        cards = await db.campaign_cards.find({"campaign_id": campaign_id}, {"_id": 0}).to_list(250)
        log_doc = await db.campaign_logs.find_one({"campaign_id": campaign_id}, {"_id": 0}) or {}
        legacy_quests = await db.quests.find({"campaign_id": campaign_id}, {"_id": 0}).to_list(100)

        updated_campaign, result = self.tick_campaign_document(
            campaign=campaign,
            cards=cards,
            campaign_log=log_doc,
            legacy_quests=legacy_quests,
            trigger=trigger,
            context=context,
        )
        await db.campaigns.update_one(
            {"campaign_id": campaign_id},
            {"$set": {
                "world_state": updated_campaign.get("world_state", {}),
                "updated_at": updated_campaign.get("updated_at"),
            }},
        )
        try:
            await db.narrative_ticks.insert_one({**result, "campaign_id": campaign_id})
        except Exception as exc:  # noqa: BLE001
            logger.warning("Narrative tick debug insert failed: %s", exc)
        logger.info("Narrative tick complete: %s", result.get("debug_summary"))
        return result

    def tick_campaign_document(
        self,
        *,
        campaign: Dict[str, Any],
        cards: Optional[List[Dict[str, Any]]] = None,
        campaign_log: Optional[Dict[str, Any]] = None,
        legacy_quests: Optional[List[Dict[str, Any]]] = None,
        trigger: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        campaign_copy = deepcopy(campaign)
        cards = cards or []
        campaign_log = campaign_log or {}
        legacy_quests = legacy_quests or []
        context = context or {}

        region_id, region = self._target_region(campaign_copy, context)
        active_quests = self._active_quests(cards, campaign_log, legacy_quests, now)
        leads = self._leads(cards, campaign_log, now)
        factions = self._faction_activity(campaign_copy, campaign_log, active_quests, leads)
        antagonist_operations = self._antagonist_operations_stub(campaign_copy, context)

        decay_candidates = self._decay_candidates(cards, campaign_log, now)
        protected_content = self._protected_content(cards, campaign_log, now)

        world_state = campaign_copy.setdefault("world_state", {})
        region_states = world_state.setdefault("region_states", {})
        previous = dict(REGION_STATE_DEFAULTS)
        previous.update(region_states.get(region_id) or {})
        updated_state, state_delta = self._advance_region_state(
            previous=previous,
            trigger=trigger,
            active_quests=active_quests,
            leads=leads,
            factions=factions,
            antagonist_operations=antagonist_operations,
            now=now,
        )
        region_states[region_id] = updated_state

        summaries = self._summaries(
            region_name=_region_name(region, region_id),
            trigger=trigger,
            state_delta=state_delta,
            state=updated_state,
            active_quests=active_quests,
            leads=leads,
            factions=factions,
        )

        result = {
            "ok": True,
            "id": f"tick_{int(now.timestamp())}_{trigger}",
            "created_at": now,
            "trigger": trigger,
            "region_id": region_id,
            "region_name": _region_name(region, region_id),
            "region_state": updated_state,
            "region_state_delta": state_delta,
            "active_quest_count": len(active_quests),
            "lead_count": len(leads),
            "faction_activity": factions,
            "antagonist_operations": antagonist_operations,
            "protected_content": protected_content,
            "decay_candidates": decay_candidates,
            "summaries": summaries,
            "debug_summary": (
                f"{trigger} tick in {_region_name(region, region_id)}: "
                f"{len(active_quests)} active quests, {len(leads)} leads, "
                f"{len(decay_candidates)} decay candidates."
            ),
        }
        world_state["last_narrative_tick"] = {
            **result,
            "created_at": _iso(now),
        }
        world_state["narrative_tick_debug"] = result["debug_summary"]
        campaign_copy["updated_at"] = now
        return campaign_copy, result

    def _target_region(self, campaign: Dict[str, Any], context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        world = campaign.get("world") or {}
        graph = world.get("graph") or {}
        requested_id = context.get("region_id") or graph.get("current_region_id")
        regions = graph.get("regions") or []
        if requested_id:
            for region in regions:
                if region.get("id") == requested_id:
                    return requested_id, region
            return requested_id, {"id": requested_id, "name": str(requested_id)}
        starting = world.get("startingLocation") or world.get("starting_town") or {}
        region_id = starting.get("id") or starting.get("name") or "global"
        return str(region_id), starting if isinstance(starting, dict) else {"id": "global", "name": "Global"}

    def _active_quests(
        self,
        cards: List[Dict[str, Any]],
        campaign_log: Dict[str, Any],
        legacy_quests: List[Dict[str, Any]],
        now: datetime,
    ) -> List[Dict[str, Any]]:
        quests: List[Dict[str, Any]] = []
        for card in cards:
            if str(card.get("type") or "").lower() != "quest":
                continue
            status = str(card.get("status") or "active").lower()
            if status in ACTIVE_QUEST_STATUSES:
                item = dict(card)
                item["narrative_importance"] = existing_or_score("card", item, now)
                quests.append(item)
        for quest_id, quest in ((campaign_log.get("quests") or {}).items()):
            status = str(quest.get("status") or "active").lower()
            if status in ACTIVE_QUEST_STATUSES:
                item = {**quest, "id": quest.get("id") or quest_id}
                item["narrative_importance"] = existing_or_score("quest", item, now)
                quests.append(item)
        for quest in legacy_quests:
            status = str(quest.get("status") or "").lower()
            if status in ACTIVE_QUEST_STATUSES:
                item = dict(quest)
                item["id"] = item.get("id") or item.get("quest_id")
                item["narrative_importance"] = existing_or_score("quest", item, now)
                quests.append(item)
        return quests

    def _leads(
        self,
        cards: List[Dict[str, Any]],
        campaign_log: Dict[str, Any],
        now: datetime,
    ) -> List[Dict[str, Any]]:
        leads: List[Dict[str, Any]] = []
        for lead_id, lead in ((campaign_log.get("leads") or {}).items()):
            status = str(lead.get("status") or "unexplored").lower()
            if status not in {"resolved"}:
                item = {**lead, "id": lead.get("id") or lead_id}
                item["narrative_importance"] = existing_or_score("lead", item, now)
                leads.append(item)
        for card in cards:
            tags = [str(tag).lower() for tag in (card.get("tags") or [])]
            card_type = str(card.get("type") or "").lower()
            if card_type == "lead" or "lead" in tags:
                item = dict(card)
                item["narrative_importance"] = existing_or_score("card", item, now)
                leads.append(item)
        return leads

    def _faction_activity(
        self,
        campaign: Dict[str, Any],
        campaign_log: Dict[str, Any],
        active_quests: List[Dict[str, Any]],
        leads: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        world = campaign.get("world") or {}
        setting = world.get("setting") or {}
        factions: Dict[str, Dict[str, Any]] = {}
        for idx, faction in enumerate(setting.get("factions") or []):
            fid = str(faction.get("id") or faction.get("name") or f"faction_{idx}")
            factions[fid] = {
                "name": faction.get("name") or fid,
                "pressure": 0.25,
                "source": "world_setting",
            }
        for fid, faction in ((campaign_log.get("factions") or {}).items()):
            factions.setdefault(fid, {
                "name": faction.get("name") or fid,
                "pressure": 0.25,
                "source": "campaign_log",
            })
            relationship = str(faction.get("relationship_to_party") or "neutral").lower()
            if relationship == "hostile":
                factions[fid]["pressure"] += 0.25
            elif relationship == "ally":
                factions[fid]["pressure"] += 0.05
        for item in active_quests + leads:
            score = float((item.get("narrative_importance") or {}).get("score") or 0.0)
            for fid in item.get("related_faction_ids") or []:
                factions.setdefault(fid, {"name": fid, "pressure": 0.2, "source": "content_link"})
                factions[fid]["pressure"] += 0.15 + (0.15 * score)
        return {
            fid: {**data, "pressure": _clamp(data.get("pressure", 0.0))}
            for fid, data in factions.items()
        }

    def _antagonist_operations_stub(
        self,
        campaign: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        return []

    def _advance_region_state(
        self,
        *,
        previous: Dict[str, Any],
        trigger: str,
        active_quests: List[Dict[str, Any]],
        leads: List[Dict[str, Any]],
        factions: Dict[str, Dict[str, Any]],
        antagonist_operations: List[Dict[str, Any]],
        now: datetime,
    ) -> Tuple[Dict[str, Any], Dict[str, float]]:
        intensity = TRIGGER_INTENSITY.get(trigger, 0.1)
        quest_pressure = min(1.0, sum((q.get("narrative_importance") or {}).get("score", 0.0) for q in active_quests) / 3.0)
        lead_pressure = min(1.0, sum((l.get("narrative_importance") or {}).get("score", 0.0) for l in leads) / 4.0)
        faction_pressure = max([0.0] + [float(f.get("pressure") or 0.0) for f in factions.values()])
        antagonist_pressure = min(1.0, len(antagonist_operations) * 0.2)
        deltas = {
            "guard_presence": intensity * (0.25 + faction_pressure + 0.5 * antagonist_pressure),
            "fear": intensity * (0.2 + quest_pressure + 0.5 * antagonist_pressure),
            "rumor_density": intensity * (0.4 + lead_pressure + 0.25 * quest_pressure),
            "faction_activity": intensity * (0.3 + faction_pressure),
            "scarcity": intensity * (0.15 + 0.25 * antagonist_pressure + 0.15 * faction_pressure),
            "price_pressure": intensity * (0.1 + 0.25 * previous.get("scarcity", 0.0) + 0.2 * faction_pressure),
        }
        updated = {
            key: _clamp(float(previous.get(key, default)) + deltas[key])
            for key, default in REGION_STATE_DEFAULTS.items()
        }
        updated.update({
            "last_tick_at": _iso(now),
            "last_tick_trigger": trigger,
            "tick_count": int(previous.get("tick_count") or 0) + 1,
        })
        return updated, {key: round(value, 3) for key, value in deltas.items()}

    def _decay_candidates(
        self,
        cards: List[Dict[str, Any]],
        campaign_log: Dict[str, Any],
        now: datetime,
    ) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        for card in cards:
            importance = score_knowledge_card(card, now)
            status = str(card.get("status") or "").lower()
            tags = [str(tag).lower() for tag in (card.get("tags") or [])]
            inactive = status in INACTIVE_STATUSES or "dismissed" in tags
            if inactive and importance["score"] < 0.35 and not importance["protected_from_cleanup"]:
                candidates.append({
                    "kind": "card",
                    "id": card.get("id"),
                    "title": card.get("title"),
                    "score": importance["score"],
                    "reason": "low_importance_inactive",
                })
        for lead_id, lead in ((campaign_log.get("leads") or {}).items()):
            importance = existing_or_score("lead", lead, now)
            status = str(lead.get("status") or "unexplored").lower()
            if status in {"abandoned", "resolved"} and importance["score"] < 0.35 and not importance["protected_from_cleanup"]:
                candidates.append({
                    "kind": "lead",
                    "id": lead.get("id") or lead_id,
                    "title": lead.get("short_text"),
                    "score": importance["score"],
                    "reason": "low_importance_inactive",
                })
        return candidates

    def _protected_content(
        self,
        cards: List[Dict[str, Any]],
        campaign_log: Dict[str, Any],
        now: datetime,
    ) -> List[Dict[str, Any]]:
        protected: List[Dict[str, Any]] = []
        for card in cards:
            importance = existing_or_score("card", card, now)
            if importance["protected_from_cleanup"] or importance["score"] >= 0.65:
                protected.append({
                    "kind": "card",
                    "id": card.get("id"),
                    "title": card.get("title"),
                    "score": importance["score"],
                })
        for collection_name, kind in (("leads", "lead"), ("quests", "quest"), ("npcs", "npc")):
            for item_id, item in ((campaign_log.get(collection_name) or {}).items()):
                importance = existing_or_score(kind, item, now)
                if importance["protected_from_cleanup"] or importance["score"] >= 0.65:
                    protected.append({
                        "kind": kind,
                        "id": item.get("id") or item_id,
                        "title": item.get("title") or item.get("name") or item.get("short_text"),
                        "score": importance["score"],
                    })
        return protected

    def _summaries(
        self,
        *,
        region_name: str,
        trigger: str,
        state_delta: Dict[str, float],
        state: Dict[str, Any],
        active_quests: List[Dict[str, Any]],
        leads: List[Dict[str, Any]],
        factions: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        summaries: List[str] = []
        if state_delta.get("guard_presence", 0) >= 0.08:
            summaries.append(f"Patrols in {region_name} become more visible after the {trigger.replace('_', ' ')}.")
        if state_delta.get("fear", 0) >= 0.08:
            summaries.append(f"People in {region_name} speak more carefully, with fear edging into ordinary errands.")
        if state_delta.get("rumor_density", 0) >= 0.08:
            summaries.append(f"Rumors thicken in {region_name}; old leads are retold with new urgency.")
        if state_delta.get("faction_activity", 0) >= 0.08 and factions:
            faction_name = max(factions.values(), key=lambda f: f.get("pressure", 0)).get("name")
            summaries.append(f"{faction_name} activity is easier to spot around {region_name}.")
        if state_delta.get("price_pressure", 0) >= 0.05 or state.get("price_pressure", 0) >= 0.5:
            summaries.append(f"Merchants in {region_name} start adjusting prices as tension affects supply.")
        if not summaries:
            summaries.append(f"{region_name} shifts subtly; nothing breaks, but the pressure has moved.")
        if active_quests:
            title = active_quests[0].get("title") or active_quests[0].get("name")
            summaries.append(f"The active thread around {title} continues to shape what locals notice.")
        elif leads:
            title = leads[0].get("short_text") or leads[0].get("title")
            summaries.append(f"An unresolved lead still circulates: {title}")
        return summaries[:4]


narrative_tick_service = NarrativeTickService()
