"""End-to-end tests for the paused-storyline resumption ruling endpoint.

Covers:
  - 400 on empty player_action
  - 404 on unknown storyline
  - 409 on active storyline
  - 409 on already-expired storyline (re-attempt blocked)
  - PLAUSIBLE recent attempt -> ruling='active'/'cold', status flips to 'active'
  - IMPLAUSIBLE attempt on 5-day-old CRITICAL rescue -> ruling='expired',
    storyline status='expired', new_lead occasionally minted as quest/rumor card
    with source='resume-fallback-lead' and tags including 'lead'+'resumption'
  - storyline.last_resume_ruling persisted on doc
  - pending_obligation REMAINS on campaign after expiry (3a permanent grudges)
"""
from __future__ import annotations

import os
import time
import uuid
import pytest
import requests
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Frontend env may not be loaded; pytest fixtures will skip in that case.
    BASE_URL = "https://dragon-quest-58.preview.emergentagent.com"

CHARACTER_ID = "69f2985e0999201c3edfaa3a"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "dnd_ai_db")


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def mongo_db():
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000)
    return client[DB_NAME]


def _make_campaign(api) -> str:
    """Create a throwaway campaign and return its campaign_id."""
    body = {
        "characterId": CHARACTER_ID,
        "intent": {
            "tone": "gritty",
            "focus": "intrigue",
            "scope": "city",
            "danger": "medium",
        },
        "mission_type_slug": "rescue",
    }
    r = api.post(f"{BASE_URL}/api/campaigns/draft", json=body, timeout=60)
    assert r.status_code in (200, 201), f"campaign draft failed: {r.status_code} {r.text[:200]}"
    data = r.json()
    cid = data.get("campaignId") or data.get("campaign_id") or (data.get("campaign") or {}).get("campaign_id")
    assert cid, f"no campaign_id in response: {data}"
    return cid


def _draft_storyline(api, cid: str, hook_text: str, mission_slug: str = "rescue") -> dict:
    body = {
        "character_id": CHARACTER_ID,
        "hook_text": hook_text,
        "hook_topic": "TEST_resume",
        "mission_type_slug": mission_slug,
    }
    r = api.post(f"{BASE_URL}/api/campaigns/{cid}/storylines/draft", json=body, timeout=120)
    assert r.status_code == 200, f"draft failed: {r.status_code} {r.text[:300]}"
    return r.json()["storyline"]


def _pause_via_spawn(api, cid: str, storyline_id: str) -> dict:
    """Trigger an off-hook spawn so the storyline gets paused with an obligation."""
    body = {
        "character_id": CHARACTER_ID,
        "player_action": "I leave the inn entirely and head to the docks to look for smugglers about a totally different matter.",
        "current_storyline_id": storyline_id,
    }
    r = api.post(f"{BASE_URL}/api/campaigns/{cid}/storylines/spawn-from-action", json=body, timeout=120)
    assert r.status_code == 200, f"spawn failed: {r.status_code} {r.text[:300]}"
    return r.json()


# ============= Negative cases =============

def test_empty_player_action_returns_400(api):
    cid = _make_campaign(api)
    sl = _draft_storyline(api, cid, "TEST_resume Hester the herbalist needs rescue from kidnappers")
    _pause_via_spawn(api, cid, sl["id"])
    r = api.post(
        f"{BASE_URL}/api/campaigns/{cid}/storylines/{sl['id']}/attempt-resume",
        json={"character_id": CHARACTER_ID, "player_action": "   "},
        timeout=30,
    )
    assert r.status_code == 400
    assert "player_action" in r.text.lower()


def test_unknown_storyline_returns_404(api):
    cid = _make_campaign(api)
    r = api.post(
        f"{BASE_URL}/api/campaigns/{cid}/storylines/sl_doesnotexist/attempt-resume",
        json={"character_id": CHARACTER_ID, "player_action": "I head back."},
        timeout=30,
    )
    assert r.status_code == 404


def test_active_storyline_returns_409(api):
    cid = _make_campaign(api)
    sl = _draft_storyline(api, cid, "TEST_resume active storyline cannot be resumed")
    r = api.post(
        f"{BASE_URL}/api/campaigns/{cid}/storylines/{sl['id']}/attempt-resume",
        json={"character_id": CHARACTER_ID, "player_action": "I try."},
        timeout=30,
    )
    assert r.status_code == 409
    assert "active" in r.text.lower()


def test_expired_storyline_returns_409(api, mongo_db):
    """An already-expired storyline should reject re-attempts."""
    cid = _make_campaign(api)
    sl = _draft_storyline(api, cid, "TEST_resume already expired")
    # Directly mark expired in DB.
    mongo_db.campaign_storylines.update_one(
        {"campaign_id": cid, "id": sl["id"]},
        {"$set": {"status": "expired"}},
    )
    r = api.post(
        f"{BASE_URL}/api/campaigns/{cid}/storylines/{sl['id']}/attempt-resume",
        json={"character_id": CHARACTER_ID, "player_action": "Try again."},
        timeout=30,
    )
    assert r.status_code == 409
    assert "expired" in r.text.lower()


# ============= Plausible attempt (active/cold ruling) =============

def test_plausible_recent_attempt_activates(api, mongo_db):
    cid = _make_campaign(api)
    sl = _draft_storyline(
        api, cid,
        "TEST_resume Hester the herbalist has been kidnapped — last seen at the Anvil & Cup tavern in Brindle.",
    )
    _pause_via_spawn(api, cid, sl["id"])

    # Confirm pause status before attempting resume.
    paused_doc = mongo_db.campaign_storylines.find_one({"campaign_id": cid, "id": sl["id"]})
    assert paused_doc and paused_doc.get("status") == "paused"

    action = (
        "I head back to the Anvil & Cup tavern in Brindle right now to find Hester "
        "the herbalist — I ask the barkeep if anyone has seen her or her kidnappers since yesterday."
    )
    r = api.post(
        f"{BASE_URL}/api/campaigns/{cid}/storylines/{sl['id']}/attempt-resume",
        json={"character_id": CHARACTER_ID, "player_action": action},
        timeout=60,
    )
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    ruling = data["ruling"]
    assert ruling["ruling"] in {"active", "cold"}, f"unexpected ruling: {ruling}"
    # 2-4 sentences of narration
    narration = ruling.get("narration", "")
    sentence_count = sum(narration.count(c) for c in ".!?")
    assert sentence_count >= 2, f"narration too short: {narration!r}"

    # storyline status flips to active
    refreshed = mongo_db.campaign_storylines.find_one({"campaign_id": cid, "id": sl["id"]})
    assert refreshed["status"] == "active"

    # last_resume_ruling persisted on storyline
    lrr = refreshed.get("last_resume_ruling") or {}
    assert lrr.get("ruling") in {"active", "cold"}
    assert lrr.get("narration")
    assert "ruled_at" in lrr
    assert "player_action" in lrr
    assert "hours_elapsed" in lrr


# ============= Implausible attempt on critical 5-day-old rescue (expired) =============

def test_implausible_old_critical_rescue_expires(api, mongo_db):
    cid = _make_campaign(api)
    sl = _draft_storyline(
        api, cid,
        "TEST_resume Greta has been kidnapped by goblin slavers from the Vermillion Gate — must rescue within 48 hours.",
        mission_slug="rescue",
    )
    _pause_via_spawn(api, cid, sl["id"])

    # Backdate paused_at to ~5 days ago, force urgency=critical.
    five_days_ago = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    res = mongo_db.campaigns.update_one(
        {"campaign_id": cid, "pending_obligations.storyline_id": sl["id"]},
        {"$set": {
            "pending_obligations.$.paused_at": five_days_ago,
            "pending_obligations.$.urgency": "critical",
            "pending_obligations.$.deadline_hours": 48,
        }},
    )
    assert res.modified_count == 1, "failed to backdate pending_obligation"

    # Also bump the storyline's paused_at so internal accounting agrees.
    mongo_db.campaign_storylines.update_one(
        {"campaign_id": cid, "id": sl["id"]},
        {"$set": {"paused_at": datetime.now(timezone.utc) - timedelta(days=5)}},
    )

    # Implausible attempt — far away and vague.
    action = (
        "I travel to a faraway city I've never been to, completely unrelated to Greta, "
        "and ask random strangers if they've heard of slavers."
    )
    r = api.post(
        f"{BASE_URL}/api/campaigns/{cid}/storylines/{sl['id']}/attempt-resume",
        json={"character_id": CHARACTER_ID, "player_action": action},
        timeout=60,
    )
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    ruling = data["ruling"]
    assert ruling["ruling"] == "expired", f"expected expired, got {ruling}"

    # storyline status is expired
    refreshed = mongo_db.campaign_storylines.find_one({"campaign_id": cid, "id": sl["id"]})
    assert refreshed["status"] == "expired"
    assert refreshed.get("expired_at") is not None

    # last_resume_ruling persisted
    lrr = refreshed.get("last_resume_ruling") or {}
    assert lrr.get("ruling") == "expired"

    # pending_obligation REMAINS on campaign (3a — permanent grudge)
    camp = mongo_db.campaigns.find_one({"campaign_id": cid})
    obligations = camp.get("pending_obligations") or []
    matching = [o for o in obligations if (o or {}).get("storyline_id") == sl["id"]]
    assert len(matching) >= 1, "pending_obligation must remain after expiry (permanent grudge)"

    # If a new_lead was emitted, a rumor card with the right metadata must exist.
    new_lead = ruling.get("new_lead")
    new_lead_card_id = data.get("new_lead_card_id")
    if new_lead and new_lead_card_id:
        card = mongo_db.campaign_cards.find_one({"campaign_id": cid, "id": new_lead_card_id})
        assert card is not None, "new_lead_card_id present but no card in DB"
        assert card.get("type") == "rumor"
        assert card.get("source") == "resume-fallback-lead"
        tags = card.get("tags") or []
        assert "lead" in tags
        assert "resumption" in tags

    # Re-attempting an expired storyline must now return 409
    r2 = api.post(
        f"{BASE_URL}/api/campaigns/{cid}/storylines/{sl['id']}/attempt-resume",
        json={"character_id": CHARACTER_ID, "player_action": "I try once more anyway."},
        timeout=30,
    )
    assert r2.status_code == 409
