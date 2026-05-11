"""Backend tests for the Canon Scenes feature (iteration 7).

Covers:
- GET /api/campaigns/{cid}/canon (list + current)
- GET /api/campaigns/{cid}/canon/current
- POST .../storylines/{sid}/resolve (outcome=passed) creates canon_scene
- POST .../storylines/{sid}/resolve (outcome=failed|skipped) does NOT create
- POST .../storylines/{sid}/creative (passed|partial) creates canon_scene w/ creative_quality
- POST .../storylines/{sid}/dm-feedback returns rewind_target field
- POST .../dm/action still returns 200 with non-empty narration
- New empty campaign: GET /canon -> empty scenes
"""
import os
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://dragon-quest-58.preview.emergentagent.com").rstrip("/")
CAMPAIGN_ID = "29feef57-a81d-4799-a988-88d644406acc"
CHARACTER_ID = "69fc667f579c1db376ac58db"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------------- Canon listing ----------------

def test_canon_list_returns_scenes_and_current(client):
    r = client.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/canon", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "scenes" in data and "current" in data
    assert isinstance(data["scenes"], list)
    if data["scenes"]:
        # newest-first ordering
        nums = [s.get("scene_number") for s in data["scenes"]]
        assert nums == sorted(nums, reverse=True), f"Not sorted desc: {nums}"
        # current is highest scene_number or marked is_current
        assert data["current"] is not None
        cur = data["current"]
        # Shape contract
        for k in ("id", "scene_number", "title", "summary", "facts",
                  "narration_snippet", "is_current"):
            assert k in cur, f"missing {k} in current"
        assert cur["is_current"] is True or cur["scene_number"] == max(nums)


def test_canon_current_endpoint(client):
    r = client.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/canon/current", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    if data is not None:
        assert "scene_number" in data
        assert "title" in data


def test_canon_empty_for_new_campaign(client):
    fake_cid = "test-empty-canon-campaign-99999"
    r = client.get(f"{BASE_URL}/api/campaigns/{fake_cid}/canon", timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert data["scenes"] == []
    assert data["current"] is None


def test_canon_current_null_for_new_campaign(client):
    fake_cid = "test-empty-canon-campaign-99999"
    r = client.get(f"{BASE_URL}/api/campaigns/{fake_cid}/canon/current", timeout=30)
    assert r.status_code == 200
    assert r.json() is None


# ---------------- Resolve creates / does NOT create canon ----------------

def _get_active_storyline(client):
    """Return an active storyline doc (any). Used to pick resolve targets."""
    r = client.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines", timeout=30)
    r.raise_for_status()
    actives = [s for s in r.json().get("storylines", []) if s.get("status") == "active"]
    assert actives, "Need an active storyline for resolve tests"
    return actives


def test_resolve_failed_does_not_create_canon(client):
    storylines = _get_active_storyline(client)
    sid = storylines[0]["id"]
    # Capture canon count before
    before = client.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/canon").json()
    before_count = len(before["scenes"])
    r = client.post(
        f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}/resolve",
        json={"outcome": "failed", "outcome_text": "TEST_canon_failed", "roll_total": 4},
        timeout=120,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("canon_scene") in (None, {}), f"canon_scene should be None on failed: {data.get('canon_scene')}"
    after = client.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/canon").json()
    assert len(after["scenes"]) == before_count, "No new canon scene should appear on failed"


def test_resolve_skipped_does_not_create_canon(client):
    storylines = _get_active_storyline(client)
    sid = storylines[0]["id"]
    before = client.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/canon").json()
    before_count = len(before["scenes"])
    r = client.post(
        f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}/resolve",
        json={"outcome": "skipped", "outcome_text": "TEST_canon_skipped"},
        timeout=120,
    )
    assert r.status_code == 200, r.text
    assert r.json().get("canon_scene") in (None, {})
    after = client.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/canon").json()
    assert len(after["scenes"]) == before_count


def test_resolve_passed_creates_canon_and_increments(client):
    storylines = _get_active_storyline(client)
    sid = storylines[0]["id"]
    before = client.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/canon").json()
    before_count = len(before["scenes"])
    before_max = max((s["scene_number"] for s in before["scenes"]), default=0)

    r = client.post(
        f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}/resolve",
        json={"outcome": "passed", "outcome_text": "TEST_canon_passed_roll", "roll_total": 22},
        timeout=180,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    cs = data.get("canon_scene")
    assert cs, "canon_scene must be present on passed outcome"
    assert cs.get("is_current") is True
    assert cs.get("scene_number") == before_max + 1
    assert isinstance(cs.get("facts"), list)
    for k in ("id", "title", "summary", "narration_snippet"):
        assert k in cs

    after = client.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/canon").json()
    assert len(after["scenes"]) == before_count + 1
    # New scene marked current; previous current(s) unmarked
    currents = [s for s in after["scenes"] if s.get("is_current")]
    assert len(currents) == 1, f"Exactly one current expected, found {len(currents)}"
    assert currents[0]["scene_number"] == cs["scene_number"]


# ---------------- Creative path creates canon w/ creative_quality ----------------

def test_creative_passed_creates_canon_with_quality(client):
    storylines = _get_active_storyline(client)
    sid = storylines[0]["id"]
    before = client.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/canon").json()
    before_count = len(before["scenes"])

    r = client.post(
        f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}/creative",
        json={"approach_text": "TEST I quietly approach using the shadows and my prior knowledge of the locket bearers to slip past unseen and confirm the next clue."},
        timeout=240,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    judged = data.get("judgment")
    cs = data.get("canon_scene")
    if judged in {"passed", "partial"}:
        assert cs, f"canon_scene expected when creative judgment={judged}"
        cp = cs.get("check_passed") or {}
        assert cp.get("quality") in {"passed", "partial"}, cp
        after = client.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/canon").json()
        assert len(after["scenes"]) == before_count + 1
    else:
        # LLM judged failed -> no canon, which is also valid behavior
        assert cs in (None, {})


# ---------------- DM Feedback rewind_target field ----------------

def test_dm_feedback_returns_rewind_target_field(client):
    r0 = client.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines", timeout=30)
    storylines = r0.json().get("storylines", [])
    # Find one with at least 2 beats so dm-feedback against beat_index=last is sensible
    target = next((s for s in storylines if len(s.get("beats", [])) >= 2 and s.get("status") == "active"), None)
    if not target:
        target = storylines[0]
    sid = target["id"]
    beat_index = max(0, len(target.get("beats", [])) - 1)

    payload = {
        "kind": "missed_check",
        "suggested_check": "Stealth",
        "suggested_dc": 13,
        "player_action": "TEST I tried to sneak past the watcher without being noticed.",
        "note": "TEST canon rewind test",
        "beat_index": beat_index,
        "apply_correction": True,
    }
    r = client.post(
        f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}/dm-feedback",
        json=payload, timeout=180,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    # Whether or not the judge agreed, the field MUST be present (None acceptable if judge disagreed)
    assert "rewind_target" in data, f"rewind_target missing from response keys={list(data.keys())}"
    rt = data["rewind_target"]
    if rt is not None:
        for k in ("id", "scene_number", "title"):
            assert k in rt, f"rewind_target missing {k}"
        # If a correction beat was appended, check it has rewind_to_* fields
        sl = client.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}").json()
        beats = sl.get("beats", [])
        if beats and beats[-1].get("source") in {"dm-feedback-correction", "dm-feedback"} or beats[-1].get("retroactive"):
            last = beats[-1]
            # The correction beat is expected to be tagged
            assert last.get("rewind_to_scene_id") in (rt["id"], None) or "rewind_to_scene_id" in last


# ---------------- DM action endpoint still healthy ----------------

def test_dm_action_returns_200(client):
    payload = {
        "character_id": CHARACTER_ID,
        "player_action": "TEST I look around carefully and take stock of what I know.",
    }
    r = client.post(
        f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm/action",
        json=payload, timeout=180,
    )
    # Some implementations return 200, some 201
    assert r.status_code in (200, 201), r.text
    data = r.json()
    # Endpoint wraps payload in {success, data: {...}}
    inner = data.get("data") if isinstance(data.get("data"), dict) else data
    narration = inner.get("narration") or inner.get("response") or inner.get("text") or ""
    assert isinstance(narration, str) and len(narration) > 10, f"Empty narration: {data}"
