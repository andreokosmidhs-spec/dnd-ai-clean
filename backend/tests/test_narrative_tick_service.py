from datetime import datetime, timezone

from services.narrative_importance import score_lead
from services.narrative_tick_service import NarrativeTickService


def test_tick_advances_region_state_and_writes_summary():
    service = NarrativeTickService()
    campaign = {
        "campaign_id": "camp_1",
        "world": {
            "graph": {
                "current_region_id": "dockward",
                "regions": [{"id": "dockward", "name": "Dockward"}],
            },
            "setting": {
                "factions": [{"id": "watch", "name": "Harbor Watch"}],
            },
        },
        "world_state": {},
    }
    cards = [
        {
            "id": "quest_1",
            "type": "quest",
            "title": "Find the Smuggler Ledger",
            "description": "A missing ledger threatens the harbor.",
            "status": "active",
            "tags": ["quest", "active", "faction-watch"],
            "updatedAt": datetime.now(timezone.utc),
        }
    ]
    log = {
        "leads": {
            "lead_1": {
                "id": "lead_1",
                "short_text": "A lantern signal flashed from the old pier.",
                "status": "active",
                "related_faction_ids": ["watch"],
                "updated_at": datetime.now(timezone.utc),
            }
        }
    }

    updated, result = service.tick_campaign_document(
        campaign=campaign,
        cards=cards,
        campaign_log=log,
        legacy_quests=[],
        trigger="travel",
        context={},
    )

    region_state = updated["world_state"]["region_states"]["dockward"]
    assert result["ok"] is True
    assert result["active_quest_count"] == 1
    assert result["lead_count"] == 1
    assert region_state["guard_presence"] > 0.2
    assert region_state["rumor_density"] > 0.3
    assert result["summaries"]
    assert "travel tick in Dockward" in result["debug_summary"]


def test_high_importance_lead_is_protected_not_decay_candidate():
    service = NarrativeTickService()
    now = datetime.now(timezone.utc)
    important_lead = {
        "id": "lead_protected",
        "short_text": "The missing heir asked the party for help.",
        "status": "active",
        "player_notes": "We promised to return.",
        "related_npc_ids": ["npc_heir"],
        "updated_at": now,
    }
    abandoned_lead = {
        "id": "lead_abandoned",
        "short_text": "A stale rumor about a closed bakery.",
        "status": "abandoned",
        "updated_at": now,
    }
    log = {"leads": {"lead_protected": important_lead, "lead_abandoned": abandoned_lead}}

    _, result = service.tick_campaign_document(
        campaign={"campaign_id": "camp_2", "world": {}, "world_state": {}},
        cards=[],
        campaign_log=log,
        legacy_quests=[],
        trigger="next_day",
        context={},
    )

    protected_ids = {item["id"] for item in result["protected_content"]}
    decay_ids = {item["id"] for item in result["decay_candidates"]}

    assert score_lead(important_lead)["protected_from_cleanup"] is True
    assert "lead_protected" in protected_ids
    assert "lead_protected" not in decay_ids
    assert "lead_abandoned" in decay_ids
