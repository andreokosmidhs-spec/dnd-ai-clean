"""Backend tests for the silent Session Review feature (Jan 2026 expansion).

Covers:
- POST /api/campaigns/{cid}/dm-lessons/session-review emits lessons across the
  five new craft categories (challenge_tuning / npc_craft / narration_craft /
  reward_balance / villain_craft) — single LLM call via Emergent LLM key.
- Idempotency: calling twice doesn't explode lesson count (dedupe merges).
- Manual create endpoint accepts the 5 new types; rejects invalid types.
- list endpoint returns lessons grouped/sorted correctly with new types.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
CAMPAIGN_ID = "29feef57-a81d-4799-a988-88d644406acc"
CHARACTER_ID = "69fc667f579c1db376ac58db"

NEW_TYPES = [
    "challenge_tuning", "npc_craft", "narration_craft",
    "reward_balance", "villain_craft",
]
ALL_TYPES = NEW_TYPES + ["rule_correction", "dc_calibration", "style_preference", "taboo"]


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _list_lessons(api):
    r = api.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons", timeout=30)
    return r


def _cleanup_test_lessons(api):
    try:
        r = _list_lessons(api)
        if r.status_code != 200:
            return
        for ls in r.json().get("lessons", []):
            if "TEST_SR" in (ls.get("text") or ""):
                api.delete(
                    f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/{ls['id']}",
                    timeout=15,
                )
    except Exception:
        pass


@pytest.fixture(scope="module", autouse=True)
def cleanup(api):
    _cleanup_test_lessons(api)
    yield
    _cleanup_test_lessons(api)


# ===== Manual create endpoint accepts all 5 new types =====
class TestNewLessonTypesAccepted:
    @pytest.mark.parametrize("ltype", NEW_TYPES)
    def test_create_new_lesson_type(self, api, ltype):
        payload = {
            "type": ltype,
            "text": f"TEST_SR — {ltype} sample lesson for type validation.",
            "trigger_keywords": [f"TEST_SR_{ltype}_kw1", f"TEST_SR_{ltype}_kw2"],
            "weight": 3,
        }
        r = api.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons",
            json=payload, timeout=30,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "lesson" in data
        lsn = data["lesson"]
        assert lsn["type"] == ltype
        assert lsn["text"].startswith("TEST_SR")
        assert lsn["id"].startswith("lsn_")
        # Verify persistence via GET
        r2 = _list_lessons(api)
        assert r2.status_code == 200
        ids = [l["id"] for l in r2.json()["lessons"]]
        assert lsn["id"] in ids

    def test_invalid_type_still_rejected(self, api):
        payload = {"type": "totally_bogus", "text": "TEST_SR invalid"}
        r = api.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons",
            json=payload, timeout=15,
        )
        assert r.status_code == 400


# ===== Session-review endpoint =====
class TestSessionReview:
    def test_session_review_response_shape(self, api):
        body = {"character_id": CHARACTER_ID}
        r = api.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/session-review",
            json=body, timeout=180,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "lessons" in data
        assert "count" in data
        assert isinstance(data["lessons"], list)
        assert isinstance(data["count"], int)
        assert data["count"] == len(data["lessons"])
        # Cap at 10
        assert data["count"] <= 10
        # Each lesson should match the allowed enum (likely new types but original 4 are OK too)
        for lsn in data["lessons"]:
            assert lsn["type"] in ALL_TYPES, f"unexpected type: {lsn['type']}"
            assert isinstance(lsn["text"], str) and lsn["text"]
            assert isinstance(lsn["trigger_keywords"], list)
            assert 1 <= lsn["weight"] <= 5
            assert lsn["source"] in {"session_review", "manual", "like", "dislike", "dm_feedback"}
            assert lsn["id"].startswith("lsn_")
        # Stash for idempotency test
        pytest.first_review_count = data["count"]
        pytest.first_lesson_ids = [l["id"] for l in data["lessons"]]

    def test_session_review_persists_to_db(self, api):
        if not getattr(pytest, "first_lesson_ids", None):
            pytest.skip("first review yielded no lessons")
        r = _list_lessons(api)
        assert r.status_code == 200
        all_ids = [l["id"] for l in r.json()["lessons"]]
        # at least one of the freshly produced lesson ids should now be in the db
        overlap = set(pytest.first_lesson_ids) & set(all_ids)
        assert len(overlap) > 0, "session-review lessons not visible in GET"

    def test_session_review_idempotency_no_explosion(self, api):
        """Calling session-review twice must not double the lesson count.

        Because merge_or_create_lesson dedupes via Jaccard >= 0.4, the second
        call's lessons should largely merge with existing ones. Total
        lesson count must not grow by more than the per-call cap (10).
        """
        # Baseline total
        r0 = _list_lessons(api)
        assert r0.status_code == 200
        baseline_total = len(r0.json()["lessons"])

        # 2nd call
        r = api.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/session-review",
            json={"character_id": CHARACTER_ID}, timeout=180,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["count"] <= 10

        # Check final total: should not grow unboundedly. Allow at most
        # +(per-call cap) new lessons even in worst case where LLM produces
        # entirely novel keywords every time.
        r1 = _list_lessons(api)
        new_total = len(r1.json()["lessons"])
        assert new_total <= baseline_total + 10, (
            f"lessons exploded: {baseline_total} -> {new_total}"
        )

    def test_session_review_empty_character(self, api):
        """When no character_id is passed, should return empty (gather corpus
        bails when character_id missing)."""
        r = api.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm-lessons/session-review",
            json={}, timeout=60,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 0
        assert data["lessons"] == []
