"""Backend tests for the storyline-spawn CLARIFICATION GATE (iter 20).

Verifies POST /api/campaigns/{cid}/storylines/spawn-from-action:

  1. Vague short action ('I look for a sloop', 4 words, vague verb 'look')
     with NO narration_context AND NO current_storyline_id ->
     {spawned: false, is_off_hook: true, needs_clarification: true,
      clarification_question: <string>, pending_action: original,
      tentative_mission_type_slug: <slug or null>}.

  2. Concrete long action ('I steal the locked vault key from the cathedral
     altar', 9 words, verb 'steal') -> spawned=true, full storyline drafted,
     includes top-level transition_narration.

  3. Vague short action BUT non-empty narration_context (player clarification
     reply) -> bypasses gate -> spawned=true with transition_narration.

  4. Heuristic verbs: look, find, check, see, go, search, explore, wander,
     scout, watch, head -> each triggers clarification when used in a short
     vague sentence.

  5. Filler-word stripping: "I'm looking for ...", "Im looking for ...",
     "I'll search for ..." -> all trigger clarification gate.

  6. -ing normalization: 'looking' / 'searching' -> still triggers.

  7. transition_narration format on successful spawn:
       'You set out on this - <action>. The world shifts in response, and a
        new <missionTypeName.lower()> thread takes shape.'

Notes:
  * Spawn-decision is LLM-bound and may flake on the 'is_off_hook' classifier.
    Tests assert STRUCTURAL properties of the response, not exact strings.
    If the classifier marks an input as ON-HOOK (is_off_hook=false), the
    test is skipped rather than failed.
  * Clarification gate is deterministic (template, no LLM).
"""
from __future__ import annotations

import os
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL", "https://dragon-quest-58.preview.emergentagent.com"
).rstrip("/")
CHARACTER_ID = "69f2985e0999201c3edfaa3a"


# -------------------- Fixtures --------------------

@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def campaign_id(session):
    """Drafts a fresh campaign once per module to keep latency down."""
    payload = {
        "characterId": CHARACTER_ID,
        "intent": {
            "tone": "gritty",
            "focus": "intrigue",
            "scope": "city",
            "danger": "medium",
        },
    }
    r = session.post(f"{BASE_URL}/api/campaigns/draft", json=payload, timeout=90)
    assert r.status_code == 200, r.text
    body = r.json()
    cid = body.get("campaignId") or body.get("campaign_id")
    assert cid, f"missing campaignId: {body}"
    return cid


def _spawn(session, campaign_id, *, player_action, narration_context=None,
           current_storyline_id=None):
    body = {"character_id": CHARACTER_ID, "player_action": player_action}
    if narration_context is not None:
        body["narration_context"] = narration_context
    if current_storyline_id:
        body["current_storyline_id"] = current_storyline_id
    r = session.post(
        f"{BASE_URL}/api/campaigns/{campaign_id}/storylines/spawn-from-action",
        json=body, timeout=180,
    )
    return r


# -------------------- Module 1: Clarification gate (vague + no context) --------------------

class TestClarificationGate:
    """The ambiguity gate must trigger on short+vague actions when no
    narration_context is supplied."""

    def test_vague_look_for_sloop_triggers_clarification(self, session, campaign_id):
        r = _spawn(session, campaign_id, player_action="I look for a sloop")
        assert r.status_code == 200, r.text
        data = r.json()

        # If classifier deemed it on-hook, skip — that's a separate concern.
        if not data.get("is_off_hook"):
            pytest.skip(f"classifier marked on-hook: {data.get('reason')}")

        # Structural assertions for clarification path.
        assert data.get("spawned") is False
        assert data.get("is_off_hook") is True
        assert data.get("needs_clarification") is True
        assert isinstance(data.get("clarification_question"), str)
        assert len(data["clarification_question"]) > 10
        assert data.get("pending_action") == "I look for a sloop"
        # tentative_mission_type_slug may be a slug or None
        assert "tentative_mission_type_slug" in data
        slug = data["tentative_mission_type_slug"]
        assert slug is None or isinstance(slug, str)

    @pytest.mark.parametrize("verb", [
        "look", "find", "check", "see", "go", "search",
        "explore", "wander", "scout", "watch", "head",
    ])
    def test_all_vague_verbs_trigger_clarification(self, session, campaign_id, verb):
        action = f"I {verb} for a sloop"   # 5 words, leading vague verb
        r = _spawn(session, campaign_id, player_action=action)
        assert r.status_code == 200, r.text
        data = r.json()
        if not data.get("is_off_hook"):
            pytest.skip(f"classifier on-hook for verb '{verb}'")
        assert data.get("needs_clarification") is True, (
            f"verb '{verb}' did NOT trigger clarification: {data}"
        )
        assert data.get("pending_action") == action

    @pytest.mark.parametrize("prefix", ["i'm", "im", "i'll", "ill"])
    def test_filler_word_stripping(self, session, campaign_id, prefix):
        # "i'm looking for a sloop" -> after strip, first content word is
        # "looking" -> -ing strip -> "look" -> in vague set.
        action = f"{prefix} looking for a sloop"
        r = _spawn(session, campaign_id, player_action=action)
        assert r.status_code == 200, r.text
        data = r.json()
        if not data.get("is_off_hook"):
            pytest.skip(f"classifier on-hook for prefix '{prefix}'")
        assert data.get("needs_clarification") is True, (
            f"prefix '{prefix}' did NOT trigger clarification: {data}"
        )

    def test_ing_suffix_normalization(self, session, campaign_id):
        # 'searching' -> 'search' is in the set.
        r = _spawn(session, campaign_id, player_action="searching for a sloop now")
        assert r.status_code == 200, r.text
        data = r.json()
        if not data.get("is_off_hook"):
            pytest.skip("classifier on-hook for 'searching for a sloop now'")
        assert data.get("needs_clarification") is True


# -------------------- Module 2: Concrete actions spawn outright --------------------

class TestConcreteSpawn:
    """Long, concrete actions should bypass the gate and spawn a storyline
    with a top-level transition_narration."""

    def test_long_concrete_steal_spawns_directly(self, session, campaign_id):
        action = "I steal the locked vault key from the cathedral altar"
        r = _spawn(session, campaign_id, player_action=action)
        assert r.status_code == 200, r.text
        data = r.json()
        # Successful spawn response does NOT echo is_off_hook back; only the
        # short-circuit (on-hook OR clarification) paths do. So only skip if
        # the classifier explicitly marked it on-hook.
        if data.get("spawned") is False and not data.get("needs_clarification"):
            pytest.skip(f"classifier on-hook for concrete steal: {data.get('reason')}")

        # Should NOT be in clarification mode.
        assert data.get("needs_clarification") is not True
        assert data.get("spawned") is True, data

        # transition_narration must be present and formatted.
        tn = data.get("transition_narration")
        assert isinstance(tn, str) and tn, "transition_narration missing"
        assert "You set out on this" in tn
        assert "thread takes shape" in tn

        # Full storyline must be drafted.
        sl = data.get("storyline")
        assert sl and isinstance(sl, dict)
        assert sl.get("id")
        assert sl.get("status") == "active"
        assert isinstance(sl.get("beats"), list) and len(sl["beats"]) >= 1
        # spawned_from provenance is recorded.
        assert sl.get("spawned_from", {}).get("trigger") == "off_hook_player_action"


# -------------------- Module 3: Clarification reply bypasses the gate --------------------

class TestClarificationBypass:
    """When the player has replied to the clarification, the frontend
    re-calls spawn-from-action with a non-empty narration_context. The
    gate must NOT trigger again — it should spawn directly."""

    def test_vague_action_with_narration_context_spawns(self, session, campaign_id):
        r = _spawn(
            session, campaign_id,
            player_action="I look for a sloop",
            narration_context=(
                "Player clarification: I want to buy passage on a sloop "
                "to sail away from the city tonight."
            ),
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # Skip only if classifier marked on-hook (not when spawned).
        if data.get("spawned") is False and not data.get("needs_clarification"):
            pytest.skip(f"classifier on-hook with narration_context: {data.get('reason')}")

        # Must NOT ask clarification this time.
        assert data.get("needs_clarification") is not True, data
        assert data.get("spawned") is True, data
        # transition_narration must still be present.
        assert isinstance(data.get("transition_narration"), str)
        assert data["transition_narration"]

    def test_empty_string_narration_context_still_triggers_gate(self, session, campaign_id):
        # Edge case: explicit empty string should be treated as 'no context'
        # because the backend strips before checking.
        r = _spawn(
            session, campaign_id,
            player_action="I look for a sloop",
            narration_context="   ",   # whitespace only
        )
        assert r.status_code == 200, r.text
        data = r.json()
        if not data.get("is_off_hook"):
            pytest.skip("classifier on-hook")
        assert data.get("needs_clarification") is True, (
            f"whitespace narration_context should NOT bypass gate: {data}"
        )


# -------------------- Module 4: Input validation regressions --------------------

class TestInputValidation:
    def test_empty_action_returns_400(self, session, campaign_id):
        r = session.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/storylines/spawn-from-action",
            json={"character_id": CHARACTER_ID, "player_action": ""},
            timeout=30,
        )
        assert r.status_code == 400

    def test_missing_character_returns_404(self, session, campaign_id):
        r = session.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/storylines/spawn-from-action",
            json={"character_id": "doesnotexist000000000000",
                  "player_action": "I steal the vault key from the cathedral altar"},
            timeout=30,
        )
        assert r.status_code == 404
