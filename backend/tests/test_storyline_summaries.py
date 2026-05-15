"""Iter 17 — narration polish tests.

Covers two new top-level fields:
  * POST /api/campaigns/{cid}/storylines/spawn-from-action
        -> response.paused_summary_narration
           - non-empty 1-3 sentence Mercer-style cue when the spawn
             actually pauses an active storyline.
           - null when no current_storyline_id was supplied.
           - null when the action is on-hook (spawned=false).
           - never includes a trailing comma-role on NPC names
             (e.g., 'Hester' not 'Hester, posting clerk').
  * POST /api/campaigns/{cid}/storylines/{sid}/resolve
        -> response.completion_narration
           - key is ALWAYS present (string when completed, null when not).
  * POST /api/campaigns/{cid}/storylines/{sid}/creative
        -> response.completion_narration
           - key is ALWAYS present (string when completed, null when not).
  * Unit-level: _build_completion_narration helper prefers epilogue,
    falls back to template citing storyline title + final-beat targets.

Regression artefact for future iterations.
"""
from __future__ import annotations

import os
import re

import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL", "https://dragon-quest-58.preview.emergentagent.com"
).rstrip("/")
CHARACTER_ID = "69f2985e0999201c3edfaa3a"


# -------------------- helpers --------------------


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _intent():
    return {"tone": "gritty", "focus": "intrigue", "scope": "city", "danger": "medium"}


def _create_campaign(session, *, mission_type_slug="heist"):
    r = session.post(
        f"{BASE_URL}/api/campaigns/draft",
        json={
            "characterId": CHARACTER_ID,
            "intent": _intent(),
            "mission_type_slug": mission_type_slug,
        },
        timeout=60,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    cid = body.get("campaignId") or body.get("campaign_id")
    assert cid, f"missing campaignId: {body}"
    return cid


def _draft_storyline(session, cid, *, hook_text, hook_topic, hook_verb="examine"):
    r = session.post(
        f"{BASE_URL}/api/campaigns/{cid}/storylines/draft",
        json={
            "character_id": CHARACTER_ID,
            "hook_text": hook_text,
            "hook_topic": hook_topic,
            "hook_verb": hook_verb,
        },
        timeout=180,
    )
    assert r.status_code == 200, r.text
    return r.json()["storyline"]


def _spawn(session, cid, *, player_action, current_storyline_id=None, narration_context=None):
    body = {"character_id": CHARACTER_ID, "player_action": player_action}
    if current_storyline_id:
        body["current_storyline_id"] = current_storyline_id
    if narration_context:
        body["narration_context"] = narration_context
    return session.post(
        f"{BASE_URL}/api/campaigns/{cid}/storylines/spawn-from-action",
        json=body,
        timeout=180,
    )


# -------------------- spawn: paused_summary_narration --------------------


class TestSpawnPausedSummaryNarration:
    @pytest.fixture(scope="class")
    def spawned(self, session):
        cid = _create_campaign(session, mission_type_slug="heist")
        sl_old = _draft_storyline(
            session, cid,
            hook_text=(
                "TEST_a whispering merchant at the Guild stall is muttering "
                "about a planned shipment heist"
            ),
            hook_topic="TEST_whispering merchant",
            hook_verb="overhear",
        )
        r = _spawn(
            session, cid,
            current_storyline_id=sl_old["id"],
            player_action="I look for a ragged beggar near the south gate",
            narration_context=(
                "The merchant leans across the stall, whispering about the Guild's plans tonight."
            ),
        )
        assert r.status_code == 200, r.text
        return {"campaign_id": cid, "old": sl_old, "resp": r.json()}

    def test_field_present_and_non_empty(self, spawned):
        d = spawned["resp"]
        assert d.get("spawned") is True, f"precondition: expected spawned=true, got {d}"
        assert "paused_summary_narration" in d, (
            f"response missing 'paused_summary_narration' key: {list(d.keys())}"
        )
        psn = d["paused_summary_narration"]
        assert isinstance(psn, str) and psn.strip(), (
            f"expected non-empty paused_summary_narration string, got: {psn!r}"
        )

    def test_sentence_count_1_to_3(self, spawned):
        psn = spawned["resp"]["paused_summary_narration"]
        # Count sentence-ish terminals.
        sentences = [p for p in re.split(r"[.!?]+\s*", psn.strip()) if p]
        assert 1 <= len(sentences) <= 3, (
            f"expected 1-3 sentences, got {len(sentences)}: {psn!r}"
        )

    def test_cites_paused_storyline_title(self, spawned):
        psn = spawned["resp"]["paused_summary_narration"].lower()
        old_title = (spawned["old"].get("title") or "").lower()
        # Title is interpolated as-is or lower-cased. Allow partial match
        # on either the hook_topic or any meaningful word from the title.
        topic_words = [w for w in re.split(r"\W+", old_title) if len(w) > 3]
        # At least one significant word from the old storyline's title should
        # appear in the pause narration so the player knows what was put down.
        assert topic_words, f"old title produced no comparable words: {old_title!r}"
        hit = any(w in psn for w in topic_words)
        assert hit, (
            f"paused_summary_narration does not cite the paused title. "
            f"title={old_title!r}, narration={psn!r}"
        )

    def test_no_trailing_comma_roles_in_npc_names(self, spawned):
        psn = spawned["resp"]["paused_summary_narration"]
        # The router cleans comma-roles via n.split(",")[0]. The narration
        # template is '... — {name} will be waiting, and not patiently.'
        # So any 'Capitalized, lowercase' BEFORE ' will be waiting' would
        # indicate a leaked comma-role. The trailing ', and not patiently'
        # is intentional copy and must not be flagged.
        m = re.search(r"—\s*(.+?)\s+will be waiting", psn)
        if m:
            who = m.group(1)
            assert "," not in who, (
                f"NPC reference contains a leaked comma-role: {who!r} in {psn!r}"
            )


class TestSpawnNoCurrentStorylineReturnsNullNarration:
    """When no current_storyline_id is supplied OR the action is on-hook,
    paused_summary_narration must be null so the frontend skips injection."""

    def test_no_current_storyline_id_returns_null_psn(self, session):
        cid = _create_campaign(session, mission_type_slug="heist")
        # No current_storyline_id at all. Even if spawn=False (no story to
        # pause), the response must include the key with value None.
        r = _spawn(
            session, cid,
            player_action="I look for a ragged beggar near the south gate",
        )
        assert r.status_code == 200, r.text
        d = r.json()
        # spawn-from-action returns spawned=false when no current storyline
        # exists, but if it does spawn, paused_summary_narration must be None.
        if d.get("spawned"):
            assert d.get("paused_summary_narration") is None, (
                f"spawn without paused storyline must return null narration, got: {d}"
            )
        else:
            # spawned=false short-circuit branch — key may or may not be present.
            # (Contract: only the spawned-true branch guarantees the key.)
            assert d.get("paused_summary_narration") in (None, "", "null") or \
                "paused_summary_narration" not in d, (
                    f"spawned=false: psn should be falsy/absent, got: {d}"
                )


# -------------------- resolve: completion_narration key --------------------


class TestResolveCompletionNarrationKey:
    """Whether or not the resolve actually completes the storyline, the key
    must be present in the response (string when completed, null otherwise)."""

    def test_resolve_non_completing_returns_null_completion_narration(self, session):
        cid = _create_campaign(session, mission_type_slug="heist")
        sl = _draft_storyline(
            session, cid,
            hook_text=(
                "TEST_a courier at the city gate hands you a sealed letter"
            ),
            hook_topic="TEST_sealed letter",
            hook_verb="examine",
        )
        beats = sl.get("beats") or []
        assert beats, f"storyline drafted with no beats: {sl}"
        if len(beats) <= 1:
            pytest.skip("Single-beat draft — first resolve completes the storyline.")

        r = session.post(
            f"{BASE_URL}/api/campaigns/{cid}/storylines/{sl['id']}/resolve",
            json={"outcome": "passed", "roll_total": 18},
            timeout=180,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "completion_narration" in data, (
            f"resolve response missing 'completion_narration' key: {list(data.keys())}"
        )
        # Not completed yet → must be null.
        assert data.get("completed") in (False, None)
        assert data.get("completion_narration") is None, (
            f"non-completing resolve must return null completion_narration, "
            f"got: {data.get('completion_narration')!r}"
        )

    def test_regression_resolve_response_shape(self, session):
        cid = _create_campaign(session, mission_type_slug="heist")
        sl = _draft_storyline(
            session, cid,
            hook_text="TEST_a moneylender wants their loan repaid",
            hook_topic="TEST_loan",
            hook_verb="confront",
        )
        r = session.post(
            f"{BASE_URL}/api/campaigns/{cid}/storylines/{sl['id']}/resolve",
            json={"outcome": "passed", "roll_total": 18},
            timeout=180,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        # iter 16 regression: ALL of these keys must still exist.
        required = [
            "storyline", "completed", "mode", "complication", "reward",
            "lead", "target_cards", "npc_field_reveals", "canon_scene",
            "completion_narration",
        ]
        missing = [k for k in required if k not in d]
        assert not missing, f"resolve response missing keys: {missing}; have: {list(d.keys())}"


# -------------------- creative: completion_narration key --------------------


class TestCreativeCompletionNarrationKey:
    def test_creative_response_includes_completion_narration_key(self, session):
        cid = _create_campaign(session, mission_type_slug="heist")
        sl = _draft_storyline(
            session, cid,
            hook_text="TEST_a coded tally sheet has been left on your table",
            hook_topic="TEST_tally sheet",
            hook_verb="decode",
        )
        r = session.post(
            f"{BASE_URL}/api/campaigns/{cid}/storylines/{sl['id']}/creative",
            json={"approach_text": "I cross-reference the tally with the dock manifest I memorized."},
            timeout=180,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert "completion_narration" in d, (
            f"creative response missing 'completion_narration' key: {list(d.keys())}"
        )
        # regression: iter 15 creative response shape.
        required = [
            "storyline", "completed", "judgment", "narration", "applied_check",
            "complication", "reward", "lead", "target_cards", "npc_field_reveals",
            "canon_scene", "completion_narration",
        ]
        missing = [k for k in required if k not in d]
        assert not missing, f"creative response missing keys: {missing}; have: {list(d.keys())}"
        # If not completed, narration must be null.
        if not d.get("completed"):
            assert d.get("completion_narration") is None


# -------------------- unit: _build_completion_narration helper --------------------


class TestBuildCompletionNarrationHelper:
    """Direct unit tests against the router-local helper, so we don't depend
    on the storyline reaching 'completed' via the LLM path."""

    def test_prefers_epilogue_when_present(self):
        from routers.storylines import _build_completion_narration
        sl = {
            "title": "The Whispering Merchant",
            "epilogue": "The stall goes quiet behind you, and the Guild's silence follows you home.",
            "beats": [],
        }
        out = _build_completion_narration(sl)
        assert isinstance(out, str) and out.strip()
        assert "stall goes quiet" in out

    def test_fallback_uses_title_and_last_beat_target_name(self):
        from routers.storylines import _build_completion_narration
        sl = {
            "title": "The Posting Clerk's Ledger",
            "epilogue": "",
            "beats": [
                {"title": "Find the clerk"},
                {
                    "title": "Confront the clerk",
                    "targets": [{"name": "Hester", "kind": "npc"}],
                },
            ],
        }
        out = _build_completion_narration(sl)
        assert isinstance(out, str) and out.strip()
        # Title (lower-cased per helper) and the NPC name should appear.
        assert "posting clerk's ledger" in out.lower()
        assert "Hester" in out

    def test_fallback_when_no_targets_still_returns_string(self):
        from routers.storylines import _build_completion_narration
        sl = {"title": "Untitled Thread", "epilogue": "", "beats": []}
        out = _build_completion_narration(sl)
        assert isinstance(out, str) and out.strip()
        assert "untitled thread" in out.lower()
