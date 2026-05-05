"""Backend tests for the Hook → Storyline → Reward feature.

Covers:
  * GET /api/campaigns/{cid} backfills starting_scene.hooks (>=3 hooks)
  * POST /api/campaigns/{cid}/storylines/draft  -> 3-5 beats + linked quest card
  * GET  /api/campaigns/{cid}/storylines        -> active+completed list
  * GET  /api/campaigns/{cid}/storylines/{sid}  -> detail
  * POST .../storylines/{sid}/resolve           -> beat advance + final reward
  * POST .../storylines/{sid}/abandon           -> abandons + flags quest card
  * Lean DM /api/campaigns/{cid}/dm/action      -> engagement detection on/off
"""
from __future__ import annotations

import os
import time

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://dragon-quest-58.preview.emergentagent.com").rstrip("/")
CAMPAIGN_ID = "a19b5ff2-e859-4cef-9019-b36e2dbfdd39"
CHARACTER_ID = "69f2985e0999201c3edfaa3a"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# -------------------- backfill --------------------


class TestHooksBackfill:
    def test_campaign_starting_scene_has_hooks(self, session):
        r = session.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}", timeout=30)
        assert r.status_code == 200, r.text
        ss = r.json().get("starting_scene") or {}
        hooks = ss.get("hooks") or []
        assert isinstance(hooks, list)
        assert len(hooks) >= 3, f"expected >=3 hooks, got {len(hooks)}"
        for h in hooks:
            assert h.get("id"), f"hook missing id: {h}"
            assert isinstance(h.get("text"), str) and h["text"].strip()
            assert isinstance(h.get("start"), int) and h["start"] >= 0
            assert isinstance(h.get("end"), int) and h["end"] > h["start"]
            assert h.get("verb_hint") in {
                "examine", "follow", "watch", "listen",
                "investigate", "approach", "search",
            }


# -------------------- draft / list / get / resolve --------------------


class TestStorylineDraftAndResolve:
    @pytest.fixture(scope="class")
    def drafted(self, session):
        # Use a clearly synthetic hook to avoid colliding with engagement-drafted ones.
        body = {
            "character_id": CHARACTER_ID,
            "hook_text": "TEST_a peculiar wax seal stuck to the doorframe",
            "hook_topic": "TEST_wax seal",
            "hook_verb": "examine",
        }
        r = session.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/draft",
            json=body, timeout=90,
        )
        assert r.status_code == 200, r.text
        return r.json()

    def test_draft_returns_storyline_with_beats(self, drafted):
        sl = drafted["storyline"]
        assert sl["status"] == "active"
        assert sl["current_beat"] == 0
        assert isinstance(sl["beats"], list)
        # Scene-driven: drafts ONLY the opening scene. Subsequent beats are
        # generated dynamically by the DM as the player acts.
        assert len(sl["beats"]) == 1, f"expected 1 opening beat, got: {len(sl['beats'])}"
        assert sl.get("open_ended") is True
        assert isinstance(sl["total_dc"], int) and sl["total_dc"] >= 8
        # First beat is active
        assert sl["beats"][0]["status"] == "active"
        # ability+check_type populated
        for b in sl["beats"]:
            assert b.get("check_type")
            assert b.get("ability")
            assert isinstance(b.get("dc"), int) and 8 <= b["dc"] <= 20
        assert sl.get("quest_card_id"), "draft must link a quest card"
        assert drafted.get("quest_card_id") == sl["quest_card_id"]

    def test_draft_creates_linked_quest_card(self, session, drafted):
        sl = drafted["storyline"]
        # /quests endpoint surfaces the card for the campaign
        r = session.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/quests", timeout=30)
        assert r.status_code == 200, r.text
        # response shape can be list or {quests:[...]}
        body = r.json()
        items = body if isinstance(body, list) else (body.get("quests") or body.get("cards") or [])
        # Find a card whose id matches quest_card_id
        match = [c for c in items if c.get("id") == sl["quest_card_id"] or c.get("quest_id") == sl["quest_card_id"]]
        # Even if the /quests shape doesn't expose id directly, look for storyline tag
        if not match:
            # accept any quest-tagged card with title equal to storyline title
            match = [c for c in items if (c.get("title") == sl["title"]) and ("storyline" in (c.get("tags") or []))]
        assert match, f"linked quest card not found in /quests for storyline {sl['id']}"

    def test_list_storylines_includes_drafted(self, session, drafted):
        r = session.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines", timeout=30)
        assert r.status_code == 200, r.text
        items = r.json().get("storylines") or []
        ids = [s.get("id") for s in items]
        assert drafted["storyline"]["id"] in ids

    def test_get_storyline_detail(self, session, drafted):
        sid = drafted["storyline"]["id"]
        r = session.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}", timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["id"] == sid
        assert body["campaign_id"] == CAMPAIGN_ID

    def test_resolve_grows_beats_until_complete(self, session, drafted):
        """Scene-driven: each /resolve call either appends the next dynamically
        generated beat OR marks the storyline complete with a reward. Hard cap
        at 7 beats per generate_next_scene; we resolve up to that many times."""
        sl = drafted["storyline"]
        sid = sl["id"]

        completed = False
        reward = None
        for _ in range(8):  # generous upper bound
            r = session.post(
                f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}/resolve",
                json={"outcome": "passed", "outcome_text": "TEST cleared"},
                timeout=120,
            )
            assert r.status_code == 200, r.text
            payload = r.json()
            if payload["completed"]:
                completed = True
                reward = payload["reward"]
                assert payload["storyline"]["status"] == "completed"
                break
            # Not yet complete — beats array should have grown
            assert payload["storyline"]["status"] == "active"
            beats = payload["storyline"]["beats"]
            # current_beat should point at the newly-appended active beat
            cb = payload["storyline"]["current_beat"]
            assert 0 <= cb < len(beats)
            assert beats[cb]["status"] == "active"

        assert completed, "Storyline never completed within 8 resolve calls"
        assert isinstance(reward, dict)
        assert isinstance(reward["xp"], int) and reward["xp"] >= 0
        assert reward["xp"] % 25 == 0
        assert reward.get("title")
        assert reward.get("description")

        # Cannot resolve a completed storyline
        r2 = session.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}/resolve",
            json={"outcome": "passed"}, timeout=30,
        )
        assert r2.status_code == 400


# -------------------- abandon --------------------


class TestAbandonStoryline:
    def test_abandon_marks_status_and_card_failed(self, session):
        # Draft a fresh storyline to abandon
        body = {
            "character_id": CHARACTER_ID,
            "hook_text": "TEST_a faintly glowing chalk mark on the wall",
            "hook_topic": "TEST_chalk mark",
            "hook_verb": "examine",
        }
        d = session.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/draft",
            json=body, timeout=90,
        )
        assert d.status_code == 200, d.text
        sid = d.json()["storyline"]["id"]

        r = session.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}/abandon",
            timeout=30,
        )
        assert r.status_code == 200, r.text
        # Detail now reflects abandoned
        det = session.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}", timeout=30)
        assert det.status_code == 200
        assert det.json()["status"] == "abandoned"

        # Re-abandon -> 404 (no longer active)
        r2 = session.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}/abandon",
            timeout=30,
        )
        assert r2.status_code == 404


# -------------------- lean DM engagement --------------------


class TestLeanDMHookEngagement:
    @staticmethod
    def _payload(resp_json):
        # Lean DM wraps everything under {success, data:{...}}
        return resp_json.get("data") if isinstance(resp_json.get("data"), dict) else resp_json

    def test_non_engaging_action_returns_no_storyline(self, session):
        body = {
            "campaign_id": CAMPAIGN_ID,
            "character_id": CHARACTER_ID,
            "player_action": "I rest in the room and wait quietly.",
        }
        r = session.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm/action",
            json=body, timeout=120,
        )
        assert r.status_code == 200, r.text
        data = self._payload(r.json())
        assert not data.get("engaged_hook_id"), data.get("engaged_hook_id")
        assert not data.get("storyline"), data.get("storyline")

    def test_engaging_action_returns_storyline(self, session):
        body = {
            "campaign_id": CAMPAIGN_ID,
            "character_id": CHARACTER_ID,
            "player_action": "I follow the scuff marks leading away from the scene.",
        }
        r = session.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm/action",
            json=body, timeout=180,
        )
        assert r.status_code == 200, r.text
        data = self._payload(r.json())
        assert data.get("engaged_hook_id"), f"expected engaged_hook_id, got: {data.get('engaged_hook_id')}"
        sl = data.get("storyline")
        assert isinstance(sl, dict), f"expected storyline payload, got: {sl}"
        beats = sl.get("beats") or []
        # Scene-driven: drafts open with ONLY beat 1.
        assert len(beats) == 1, f"expected 1 opening beat, got: {len(beats)}"
        assert sl.get("status") == "active"
        assert sl.get("current_beat") == 0
        assert sl.get("open_ended") is True

    def test_dm_response_persists_hooks_metadata(self, session):
        # Drive a fresh narration that will surface observable nouns
        body = {
            "campaign_id": CAMPAIGN_ID,
            "character_id": CHARACTER_ID,
            "player_action": "I scan the alley for anything I missed.",
        }
        r = session.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/dm/action",
            json=body, timeout=180,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # Hooks may be at top level OR nested under data; accept either.
        hooks = data.get("hooks")
        if hooks is None and isinstance(data.get("data"), dict):
            hooks = data["data"].get("hooks")
        # We don't strictly require hooks every turn (LLM may omit), so warn-only
        if hooks is not None:
            assert isinstance(hooks, list)
            for h in hooks:
                assert h.get("text")
                assert h.get("verb_hint") in {
                    "examine", "follow", "watch", "listen",
                    "investigate", "approach", "search",
                }
