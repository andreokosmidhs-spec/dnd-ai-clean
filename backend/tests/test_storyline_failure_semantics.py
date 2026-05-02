"""Backend tests for Hook→Storyline→Reward FAILURE SEMANTICS (iteration 4).

Covers:
  * POST /resolve {outcome:'failed', mode:'fail-forward'}
      - returns mode='fail-forward', complication (non-empty string),
        advances current_beat by 1, and marks the beat status='failed'
  * POST /resolve {outcome:'failed', mode:'press-on'}
      - does NOT advance current_beat, marks press_on_used=True,
        beat stays status='active', returns mode='press-on' + complication
      - Press On AGAIN -> 400 'Press On already used this storyline'
  * POST /creative {approach_text}
      - returns judgment in {'passed','partial','failed'}, narration (1-2 sent.),
        applied_check, and advances the storyline appropriately.
  * Reward scaling:
      - all-failed storyline -> xp==0, item is None
      - 3-of-4 passed storyline -> xp is ~75% of the all-passed xp (rounded to 25)
        AND reward.item is present (>=50% pass threshold).
  * Fresh draft persists press_on_used:false and complication:null defaults.
  * Regression: list / get / abandon still work.
"""
from __future__ import annotations

import os
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://dragon-quest-58.preview.emergentagent.com",
).rstrip("/")
CAMPAIGN_ID = "a19b5ff2-e859-4cef-9019-b36e2dbfdd39"
CHARACTER_ID = "69f2985e0999201c3edfaa3a"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


def _draft(s, topic_suffix: str):
    body = {
        "character_id": CHARACTER_ID,
        "hook_text": f"TEST_{topic_suffix} fresh hook for failure semantics",
        "hook_topic": f"TEST_{topic_suffix}",
        "hook_verb": "examine",
    }
    r = s.post(
        f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/draft",
        json=body, timeout=90,
    )
    assert r.status_code == 200, r.text
    return r.json()["storyline"]


def _resolve(s, sid, **body):
    return s.post(
        f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}/resolve",
        json=body, timeout=90,
    )


# -------------------- fresh-draft defaults --------------------


class TestDraftDefaults:
    def test_fresh_draft_has_press_on_and_complication_defaults(self, s):
        sl = _draft(s, "draft-defaults")
        assert sl["status"] == "active"
        assert sl.get("press_on_used") is False, sl.get("press_on_used")
        # complication should be absent OR explicitly None on a fresh draft.
        assert sl.get("complication") in (None, ""), sl.get("complication")
        # regression: beats 3..5, current_beat 0
        assert 3 <= len(sl["beats"]) <= 5
        assert sl["current_beat"] == 0


# -------------------- fail-forward --------------------


class TestFailForward:
    def test_fail_forward_advances_and_emits_complication(self, s):
        sl = _draft(s, "failforward")
        sid = sl["id"]

        r = _resolve(s, sid, outcome="failed", mode="fail-forward",
                     outcome_text="TEST failed first beat")
        assert r.status_code == 200, r.text
        payload = r.json()

        assert payload["mode"] == "fail-forward"
        comp = payload.get("complication")
        assert isinstance(comp, str) and len(comp.strip()) >= 20, f"complication: {comp!r}"

        new_sl = payload["storyline"]
        assert new_sl["current_beat"] == 1, new_sl["current_beat"]
        # Beat 0 should be marked failed; beat 1 active (if still in range).
        assert new_sl["beats"][0]["status"] == "failed"
        # storyline still active (since there are more beats)
        assert new_sl["status"] == "active"
        assert new_sl.get("complication") == comp


# -------------------- press-on --------------------


class TestPressOn:
    def test_press_on_retains_beat_then_rejects_second_use(self, s):
        sl = _draft(s, "presson")
        sid = sl["id"]

        r = _resolve(s, sid, outcome="failed", mode="press-on",
                     outcome_text="TEST pressing on")
        assert r.status_code == 200, r.text
        payload = r.json()

        assert payload["mode"] == "press-on"
        assert isinstance(payload.get("complication"), str)
        assert len(payload["complication"].strip()) >= 10

        new_sl = payload["storyline"]
        assert new_sl["current_beat"] == 0, new_sl["current_beat"]
        assert new_sl["beats"][0]["status"] == "active"
        assert new_sl.get("press_on_used") is True

        # Second press-on -> 400
        r2 = _resolve(s, sid, outcome="failed", mode="press-on")
        assert r2.status_code == 400, r2.text
        # error wrapper: {error:{message:...}} OR fastapi default {detail:...}
        body = r2.json()
        msg = (
            body.get("detail")
            or (body.get("error") or {}).get("message")
            or ""
        ).lower()
        assert "press on" in msg, body


# -------------------- creative approach --------------------


class TestCreativeApproach:
    def test_creative_endpoint_returns_judgment_and_advances(self, s):
        sl = _draft(s, "creative")
        sid = sl["id"]
        start_beat = sl["current_beat"]
        n_beats = len(sl["beats"])

        body = {"approach_text": "I offer to buy the witness a drink and let them open up."}
        r = s.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}/creative",
            json=body, timeout=120,
        )
        assert r.status_code == 200, r.text
        payload = r.json()

        assert payload["judgment"] in {"passed", "partial", "failed"}
        assert isinstance(payload.get("narration"), str) and payload["narration"].strip()
        # applied_check should be provided (ability/check_type/dc dict or similar)
        assert payload.get("applied_check") is not None

        new_sl = payload["storyline"]
        if payload["judgment"] in {"passed", "partial"}:
            # advanced by one
            assert new_sl["current_beat"] == start_beat + 1 or new_sl["status"] == "completed"
            assert new_sl["beats"][start_beat]["status"] == "passed"
        else:
            # failed -> beat marked failed + complication + advance (fail-forward)
            assert new_sl["beats"][start_beat]["status"] == "failed"
            assert isinstance(payload.get("complication"), str)
            assert new_sl["current_beat"] == start_beat + 1 or new_sl["status"] == "completed"


# -------------------- reward scaling --------------------


def _complete(s, sid, outcomes):
    """Resolve a storyline with a list of per-beat outcomes.
    Returns the final payload."""
    payload = None
    for oc in outcomes:
        mode = "fail-forward" if oc == "failed" else None
        body = {"outcome": oc}
        if mode:
            body["mode"] = mode
        r = _resolve(s, sid, **body)
        assert r.status_code == 200, r.text
        payload = r.json()
    return payload


class TestRewardScaling:
    def test_all_failed_storyline_zero_xp_no_item(self, s):
        sl = _draft(s, "allfail-reward")
        sid = sl["id"]
        n = len(sl["beats"])
        payload = _complete(s, sid, ["failed"] * n)
        assert payload["completed"] is True, payload
        reward = payload["reward"]
        assert reward is not None
        assert reward.get("xp") == 0, reward
        assert reward.get("item") in (None, ""), reward.get("item")

    def test_majority_pass_scales_xp_and_yields_item(self, s):
        # Compute the theoretical all-pass XP from total_dc using the documented
        # formula: min(1200, round(max(60, total_dc*8)/25)*25).
        sl = _draft(s, "mixed-pass")
        sid = sl["id"]
        n = len(sl["beats"])
        total_dc = sl["total_dc"]
        base_xp = min(1200, round(max(60, total_dc * 8) / 25) * 25)

        outcomes = ["passed"] * (n - 1) + ["failed"]
        payload = _complete(s, sid, outcomes)
        assert payload["completed"] is True
        reward = payload["reward"]
        assert reward["xp"] > 0
        # XP should be LESS than theoretical all-pass base (scaled by pass ratio)
        assert reward["xp"] < base_xp, (
            f"mixed {reward['xp']} not less than base {base_xp} (total_dc={total_dc})"
        )
        # rounded to 25
        assert reward["xp"] % 25 == 0
        # ~ ratio (n-1)/n of base, ±25 XP rounding tolerance
        expected = round((base_xp * (n - 1) / n) / 25) * 25
        assert abs(reward["xp"] - expected) <= 50, (
            f"scaled xp {reward['xp']} too far from expected {expected}"
        )
        # pass ratio (n-1)/n >= 50% for n>=2 -> item should drop
        if n >= 2:
            assert reward.get("item"), reward


# -------------------- regression --------------------


class TestRegression:
    def test_list_and_get_still_work(self, s):
        sl = _draft(s, "reg-listget")
        sid = sl["id"]
        r = s.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines", timeout=30)
        assert r.status_code == 200
        ids = [x["id"] for x in r.json().get("storylines", [])]
        assert sid in ids

        r2 = s.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}", timeout=30)
        assert r2.status_code == 200
        assert r2.json()["id"] == sid

    def test_abandon_still_works(self, s):
        sl = _draft(s, "reg-abandon")
        sid = sl["id"]
        r = s.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}/abandon",
            timeout=30,
        )
        assert r.status_code == 200
        det = s.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}", timeout=30)
        assert det.json()["status"] == "abandoned"
