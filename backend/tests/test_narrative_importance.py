from datetime import datetime, timedelta, timezone

from models.log_models import LeadEntry, QuestKnowledge
from services.narrative_importance import score_lead, score_quest, score_knowledge_card


def test_lead_player_interaction_increases_protection():
    stale = datetime.now(timezone.utc) - timedelta(days=10)
    base = LeadEntry(id="l1", short_text="dock rumor", updated_at=stale)
    interacted = LeadEntry(id="l2", short_text="dock rumor", updated_at=stale, player_notes="check this", status="active")

    base_score = score_lead(base)
    interacted_score = score_lead(interacted)

    assert interacted_score["protected_from_cleanup"] == 1.0
    assert interacted_score["score"] > base_score["score"]


def test_quest_completed_scores_higher_than_rumored():
    now = datetime.now(timezone.utc)
    rumored = QuestKnowledge(id="q1", title="Rumor", status="rumored", last_updated=now)
    completed = QuestKnowledge(id="q2", title="Done", status="completed", completed_objectives=["x"], last_updated=now)

    rumored_score = score_quest(rumored)
    completed_score = score_quest(completed)

    assert completed_score["score"] > rumored_score["score"]


def test_knowledge_card_faction_and_active_boosts_score():
    now = datetime.now(timezone.utc)
    active_card = {
        "type": "quest",
        "tags": ["faction", "urgent"],
        "status": "active",
        "updatedAt": now,
    }
    low_card = {
        "type": "lore",
        "tags": [],
        "updatedAt": now - timedelta(days=45),
    }

    assert score_knowledge_card(active_card)["score"] > score_knowledge_card(low_card)["score"]
