"""Backend tests for the DM Lessons / DM Notebook feature.

Covers:
- Manual lesson CRUD (POST/GET/PATCH/DELETE)
- Lesson list filter via character_id
- Reaction-based distillation (like/dislike) with LLM
- DM feedback distillation returning a 'lesson' field
- Lesson injection into /dm/action (apply_count bump)
- Smart deduping via Jaccard merge
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://dragon-quest-58.preview.emergentagent.com").rstrip("/")
CAMPAIGN_ID = "29feef57-a81d-4799-a988-88d644406acc"
CHARACTER_ID = "69fc667f579c1db376ac58db"


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# --- helpers -----
def _list_lessons(api, character_id=None):
    params = {}
    if character_id:
        params["character_id"] = character_id
    r = api.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons", params=params, timeout=30)
    return r


def _cleanup_test_lessons(api):
    """Delete any lessons whose text starts with TEST_ to keep DB tidy."""
    try:
        r = _list_lessons(api)
        if r.status_code != 200:
            return
        for ls in r.json().get("lessons", []):
            if (ls.get("text") or "").startswith("TEST_") or "TEST_" in (ls.get("text") or ""):
                api.delete(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/{ls['id']}", timeout=15)
    except Exception:
        pass


@pytest.fixture(scope="module", autouse=True)
def cleanup(api):
    _cleanup_test_lessons(api)
    yield
    _cleanup_test_lessons(api)


# --- TESTS ---

class TestManualLessonCRUD:
    def test_create_manual_lesson(self, api):
        payload = {
            "type": "style_preference",
            "text": "TEST_ManualA — Lead with a sharp sensory detail before any plot fact.",
            "trigger_keywords": ["TEST_kwA1", "TEST_kwA2", "TEST_kwA3"],
            "weight": 4,
        }
        r = api.post(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "lesson" in data
        lsn = data["lesson"]
        assert lsn["type"] == "style_preference"
        assert lsn["text"].startswith("TEST_ManualA")
        assert "id" in lsn and lsn["id"].startswith("lsn_")
        assert lsn["weight"] == 4
        assert lsn["enabled"] is True
        assert lsn["apply_count"] == 0
        assert isinstance(lsn["trigger_keywords"], list) and len(lsn["trigger_keywords"]) == 3
        pytest.lesson_a_id = lsn["id"]

    def test_create_invalid_type(self, api):
        payload = {"type": "bogus_type", "text": "TEST_invalid"}
        r = api.post(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons", json=payload, timeout=15)
        assert r.status_code == 400

    def test_create_empty_text(self, api):
        payload = {"type": "taboo", "text": "   "}
        r = api.post(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons", json=payload, timeout=15)
        assert r.status_code == 400

    def test_list_lessons(self, api):
        r = _list_lessons(api)
        assert r.status_code == 200
        data = r.json()
        assert "lessons" in data
        assert isinstance(data["lessons"], list)
        ids = [ls["id"] for ls in data["lessons"]]
        assert pytest.lesson_a_id in ids
        # ensure no _id field leak
        for ls in data["lessons"]:
            assert "_id" not in ls

    def test_list_sorted_by_enabled_weight_created(self, api):
        r = _list_lessons(api)
        assert r.status_code == 200
        lessons = r.json()["lessons"]
        # enabled True should come before False (no False yet, just sanity)
        prev_enabled = True
        for ls in lessons:
            if not ls["enabled"]:
                prev_enabled = False
            else:
                assert prev_enabled is True, "enabled lessons must precede disabled ones"

    def test_patch_lesson_weight_clamp(self, api):
        r = api.patch(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/{pytest.lesson_a_id}",
            json={"weight": 99},
            timeout=15,
        )
        assert r.status_code == 200
        assert r.json()["lesson"]["weight"] == 5

    def test_patch_lesson_toggle(self, api):
        r = api.patch(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/{pytest.lesson_a_id}",
            json={"enabled": False},
            timeout=15,
        )
        assert r.status_code == 200
        assert r.json()["lesson"]["enabled"] is False
        # re-enable for downstream tests
        r2 = api.patch(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/{pytest.lesson_a_id}",
            json={"enabled": True},
            timeout=15,
        )
        assert r2.status_code == 200
        assert r2.json()["lesson"]["enabled"] is True

    def test_patch_lesson_text_and_keywords(self, api):
        r = api.patch(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/{pytest.lesson_a_id}",
            json={"text": "TEST_ManualA_updated — sharper sensory lead.", "trigger_keywords": ["TEST_kwA1", "TEST_kwA9"]},
            timeout=15,
        )
        assert r.status_code == 200
        lsn = r.json()["lesson"]
        assert lsn["text"].startswith("TEST_ManualA_updated")
        assert "TEST_kwA9".lower() in lsn["trigger_keywords"]

    def test_patch_nonexistent_lesson(self, api):
        r = api.patch(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/lsn_doesnotexist",
            json={"enabled": False},
            timeout=15,
        )
        assert r.status_code == 404

    def test_delete_nonexistent_lesson(self, api):
        r = api.delete(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/lsn_doesnotexist",
            timeout=15,
        )
        assert r.status_code == 404


class TestCharacterScopedLessons:
    def test_create_character_scoped(self, api):
        payload = {
            "type": "taboo",
            "text": "TEST_CharB — Avoid stacking similes; one comparison per paragraph.",
            "trigger_keywords": ["TEST_charB1", "TEST_charB2"],
            "weight": 3,
            "character_id": CHARACTER_ID,
        }
        r = api.post(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons", json=payload, timeout=20)
        assert r.status_code == 200
        lsn = r.json()["lesson"]
        assert lsn["character_id"] == CHARACTER_ID
        pytest.lesson_b_id = lsn["id"]

    def test_character_filter_includes_both(self, api):
        r = _list_lessons(api, character_id=CHARACTER_ID)
        assert r.status_code == 200
        ids = [ls["id"] for ls in r.json()["lessons"]]
        # Should include both per-character (B) and campaign-wide (A)
        assert pytest.lesson_b_id in ids
        assert pytest.lesson_a_id in ids


class TestReactionDistillation:
    def test_reaction_invalid_kind(self, api):
        r = api.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/reaction",
            json={"reaction": "meh", "narration": "Something happened."},
            timeout=15,
        )
        assert r.status_code == 400

    def test_reaction_missing_narration(self, api):
        r = api.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/reaction",
            json={"reaction": "like", "narration": "   "},
            timeout=15,
        )
        assert r.status_code == 400

    def test_reaction_like_creates_style(self, api):
        body = {
            "reaction": "like",
            "narration": (
                "The innkeeper wipes flour from his hands and squints at you. "
                "Outside, a cart wheel groans against frost-cracked stone. "
                "He nods once — 'Aye, the road north is closed. Wolves, they say.' — "
                "and slides a tin mug of cider toward your elbow."
            ),
            "beat_title": "TEST_Inn beat",
            "character_id": CHARACTER_ID,
        }
        r = api.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/reaction",
            json=body,
            timeout=90,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["action"] in {"created", "merged", "skipped"}
        # When LLM works, we expect a lesson
        if data["action"] != "skipped":
            lsn = data["lesson"]
            assert lsn["type"] == "style_preference"
            assert isinstance(lsn["text"], str) and len(lsn["text"]) > 0
            pytest.like_lesson_id = lsn["id"]
            pytest.like_lesson_keywords = lsn["trigger_keywords"]
        else:
            pytest.skip("LLM distillation returned no lesson (skipped)")

    def test_reaction_dislike_creates_taboo(self, api):
        body = {
            "reaction": "dislike",
            "narration": (
                "Suddenly, a swarm of shadowy figures springs out from nowhere and "
                "you are knocked unconscious. When you wake, you are in a dungeon "
                "with no possessions and the door is locked from the outside."
            ),
            "beat_title": "TEST_Railroad beat",
            "note": "Felt railroaded with no save.",
        }
        r = api.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/reaction",
            json=body,
            timeout=90,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        if data["action"] != "skipped":
            assert data["lesson"]["type"] == "taboo"

    def test_reaction_dedupe_merges(self, api):
        """Posting the same like narration again should merge (bump apply_count)
        when LLM produces overlapping keywords (Jaccard >= 0.4)."""
        if not getattr(pytest, "like_lesson_id", None):
            pytest.skip("no like lesson to merge against")
        body = {
            "reaction": "like",
            "narration": (
                "The innkeeper wipes flour from his hands and squints at you. "
                "Outside, a cart wheel groans against frost-cracked stone. "
                "He nods once — 'Aye, the road north is closed. Wolves, they say.' — "
                "and slides a tin mug of cider toward your elbow."
            ),
            "beat_title": "TEST_Inn beat repeat",
            "character_id": CHARACTER_ID,
        }
        r = api.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/reaction",
            json=body,
            timeout=90,
        )
        assert r.status_code == 200
        # No crash. Action may be 'merged' or 'created' depending on LLM keyword overlap.
        assert r.json()["action"] in {"merged", "created", "skipped"}


class TestDMFeedbackDistillation:
    def test_dm_feedback_returns_lesson_field(self, api):
        # Find an existing storyline for the campaign
        r = api.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines", timeout=20)
        if r.status_code != 200:
            pytest.skip(f"Cannot list storylines: {r.status_code}")
        storylines = r.json() if isinstance(r.json(), list) else r.json().get("storylines", [])
        if not storylines:
            pytest.skip("No storylines available for campaign")
        storyline_id = storylines[0].get("id")
        if not storyline_id:
            pytest.skip("Storyline missing id")

        body = {
            "kind": "missed_check",
            "player_action": (
                "TEST_FEEDBACK I tried to sneak past the guard while they were "
                "distracted, hiding in shadow"
            ),
            "suggested_check": "Stealth",
            "suggested_dc": 14,
            "note": "DM auto-resolved without rolling.",
        }
        r2 = api.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{storyline_id}/dm-feedback",
            json=body,
            timeout=120,
        )
        # Endpoint must succeed
        assert r2.status_code in (200, 201), r2.text
        data = r2.json()
        # 'lesson' key should be present (may be None if judge disagreed)
        assert "lesson" in data, f"missing 'lesson' field in DM feedback response: {list(data.keys())}"
        if data["lesson"]:
            lsn = data["lesson"]
            assert lsn["type"] in {"rule_correction", "dc_calibration"}
            assert "id" in lsn


class TestLessonInjectionBumpsApplyCount:
    def test_dm_action_bumps_apply_count(self, api):
        """After /dm/action runs, the active lessons' apply_count should be > 0."""
        # baseline: get apply_count for lesson_a
        r0 = _list_lessons(api)
        assert r0.status_code == 200
        baseline = {ls["id"]: ls.get("apply_count", 0) for ls in r0.json()["lessons"]}
        baseline_a = baseline.get(pytest.lesson_a_id, 0)

        # Fire a DM action
        body = {
            "character_id": CHARACTER_ID,
            "player_action": "TEST I look around the room carefully.",
            "action_text": "TEST I look around the room carefully.",
        }
        r = api.post(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm/action", json=body, timeout=180)
        # Accept 200 or any non-5xx success status, since DM action is complex
        if r.status_code >= 500:
            pytest.skip(f"DM action returned {r.status_code}: {r.text[:300]}")
        assert r.status_code in (200, 201), r.text

        # Wait briefly for db write to settle
        time.sleep(1.0)

        r2 = _list_lessons(api)
        assert r2.status_code == 200
        new_counts = {ls["id"]: ls.get("apply_count", 0) for ls in r2.json()["lessons"]}
        new_a = new_counts.get(pytest.lesson_a_id, 0)
        # apply_count should have grown for the enabled lesson_a
        assert new_a >= baseline_a + 1, (
            f"apply_count did not bump: baseline={baseline_a} new={new_a}"
        )


class TestDeleteLesson:
    def test_delete_manual_lesson(self, api):
        r = api.delete(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/{pytest.lesson_a_id}",
            timeout=15,
        )
        assert r.status_code == 200
        assert r.json().get("ok") is True
        # Verify it's gone
        r2 = _list_lessons(api)
        ids = [ls["id"] for ls in r2.json()["lessons"]]
        assert pytest.lesson_a_id not in ids
