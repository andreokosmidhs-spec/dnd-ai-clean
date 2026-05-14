"""Backend tests for the "Active Mission Phase" badge feature.

Verifies that:
  * POST /api/campaigns/draft persists mission_type_slug='heist'
  * POST /api/campaigns/{id}/storylines/draft  (no mission_type in body)
    returns a storyline whose response includes a mission_type snapshot
    (slug/name/icon/phases) AND whose first beat has phase_index=0 and
    phase_name='Discovery'.
  * GET /api/campaigns/{id}/storylines/{sid} returns the same snapshot
    persisted to the storyline doc.
  * Regression: a campaign drafted WITHOUT a mission_type still works.
    Storyline doc has mission_type=null and beats have no phase_index.
  * mission_type_slug='rescue' -> first beat phase_name='Locate'.

This file is a regression artefact for future testing iterations.
"""
from __future__ import annotations

import os
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL", "https://dragon-quest-58.preview.emergentagent.com"
).rstrip("/")
CHARACTER_ID = "69f2985e0999201c3edfaa3a"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _intent():
    # Required by CampaignDraftRequest.
    return {
        "tone": "gritty",
        "focus": "intrigue",
        "scope": "city",
        "danger": "medium",
    }


def _create_campaign(session, *, mission_type_slug=None):
    payload = {
        "characterId": CHARACTER_ID,
        "intent": _intent(),
    }
    if mission_type_slug:
        payload["mission_type_slug"] = mission_type_slug
    r = session.post(f"{BASE_URL}/api/campaigns/draft", json=payload, timeout=60)
    assert r.status_code == 200, r.text
    body = r.json()
    cid = body.get("campaignId") or body.get("campaign_id")
    assert cid, f"missing campaignId in response: {body}"
    return cid


def _draft_storyline(session, campaign_id, *, hook_text, hook_topic, hook_verb="examine"):
    body = {
        "character_id": CHARACTER_ID,
        "hook_text": hook_text,
        "hook_topic": hook_topic,
        "hook_verb": hook_verb,
    }
    r = session.post(
        f"{BASE_URL}/api/campaigns/{campaign_id}/storylines/draft",
        json=body, timeout=120,
    )
    assert r.status_code == 200, r.text
    return r.json()


# -------------------- campaign persistence --------------------


class TestCampaignMissionTypePersistence:
    def test_campaign_draft_with_heist_persists(self, session):
        cid = _create_campaign(session, mission_type_slug="heist")
        # GET campaign and verify slug stored on doc
        r = session.get(f"{BASE_URL}/api/campaigns/{cid}", timeout=30)
        assert r.status_code == 200, r.text
        doc = r.json()
        assert doc.get("mission_type_slug") == "heist", (
            f"expected mission_type_slug='heist', got: {doc.get('mission_type_slug')}"
        )


# -------------------- heist storyline draft --------------------


class TestHeistStorylineMissionSnapshot:
    @pytest.fixture(scope="class")
    def heist_draft(self, session):
        cid = _create_campaign(session, mission_type_slug="heist")
        drafted = _draft_storyline(
            session, cid,
            hook_text="TEST_missing courier never reached the rendezvous",
            hook_topic="TEST_missing courier",
            hook_verb="investigate",
        )
        return {"campaign_id": cid, "drafted": drafted}

    def test_draft_response_includes_mission_type_snapshot(self, heist_draft):
        sl = heist_draft["drafted"]["storyline"]
        mt = sl.get("mission_type")
        assert mt, f"expected mission_type snapshot on storyline, got: {sl.get('mission_type')}"
        assert mt.get("slug") == "heist"
        assert mt.get("name") == "Heist"
        assert mt.get("icon") == "🎯"
        phases = mt.get("phases") or []
        names = [(p or {}).get("name") for p in phases]
        assert names == [
            "Discovery", "Scouting", "Tools & Allies", "Plan & Execution",
        ], f"unexpected phases: {names}"

    def test_first_beat_tagged_phase_discovery(self, heist_draft):
        sl = heist_draft["drafted"]["storyline"]
        beats = sl.get("beats") or []
        assert beats, "expected at least one beat"
        b0 = beats[0]
        assert b0.get("phase_index") == 0, f"phase_index={b0.get('phase_index')}"
        assert b0.get("phase_name") == "Discovery", f"phase_name={b0.get('phase_name')}"

    def test_get_storyline_persists_snapshot(self, session, heist_draft):
        cid = heist_draft["campaign_id"]
        sid = heist_draft["drafted"]["storyline"]["id"]
        r = session.get(f"{BASE_URL}/api/campaigns/{cid}/storylines/{sid}", timeout=30)
        assert r.status_code == 200, r.text
        doc = r.json()
        mt = doc.get("mission_type")
        assert mt and mt.get("slug") == "heist"
        assert mt.get("name") == "Heist"
        assert mt.get("icon") == "🎯"
        phase_names = [(p or {}).get("name") for p in (mt.get("phases") or [])]
        assert phase_names == ["Discovery", "Scouting", "Tools & Allies", "Plan & Execution"]
        beats = doc.get("beats") or []
        assert beats[0].get("phase_index") == 0
        assert beats[0].get("phase_name") == "Discovery"


# -------------------- rescue storyline draft --------------------


class TestRescueStorylineMissionSnapshot:
    def test_rescue_first_beat_phase_locate(self, session):
        cid = _create_campaign(session, mission_type_slug="rescue")
        drafted = _draft_storyline(
            session, cid,
            hook_text="TEST_a child has vanished from the riverside market",
            hook_topic="TEST_missing child",
            hook_verb="investigate",
        )
        sl = drafted["storyline"]
        mt = sl.get("mission_type")
        assert mt, f"expected mission_type snapshot on storyline, got: {sl.get('mission_type')}"
        assert mt.get("slug") == "rescue"
        assert mt.get("name") in {"Rescue", "Rescue Mission", "Rescue Op"}, (
            f"unexpected name: {mt.get('name')}"
        )
        # First beat phase
        beats = sl.get("beats") or []
        assert beats, "expected at least one beat"
        b0 = beats[0]
        assert b0.get("phase_index") == 0
        assert b0.get("phase_name") == "Locate", (
            f"expected phase_name='Locate', got: {b0.get('phase_name')}"
        )


# -------------------- regression: no mission_type --------------------


class TestStorylineWithoutMissionType:
    def test_freeform_campaign_storyline_has_null_mission(self, session):
        cid = _create_campaign(session, mission_type_slug=None)
        drafted = _draft_storyline(
            session, cid,
            hook_text="TEST_a faint chalk mark beside the cellar door",
            hook_topic="TEST_chalk mark",
            hook_verb="examine",
        )
        sl = drafted["storyline"]
        # mission_type should be None/null
        assert sl.get("mission_type") in (None, {}), (
            f"expected null mission_type, got: {sl.get('mission_type')}"
        )
        # beats should not carry phase_index
        beats = sl.get("beats") or []
        assert beats, "expected at least one beat"
        b0 = beats[0]
        assert "phase_index" not in b0 or b0.get("phase_index") is None, (
            f"beat unexpectedly tagged with phase_index: {b0}"
        )
        assert "phase_name" not in b0 or not b0.get("phase_name"), (
            f"beat unexpectedly tagged with phase_name: {b0}"
        )
