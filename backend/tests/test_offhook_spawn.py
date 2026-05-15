"""Backend tests for the OFF-HOOK storyline spawner feature.

Verifies POST /api/campaigns/{id}/storylines/spawn-from-action:
  * OFF-HOOK action ('look for a beggar' while current beat is about a
    whispering merchant) returns spawned=true, picks the closest existing
    mission_type, drafts a NEW storyline rooted in the action, pauses
    the previous storyline, records a pending_obligation on the campaign.
  * ON-HOOK action returns spawned=false WITHOUT pausing the storyline.
  * Empty player_action -> 400.
  * Missing character -> 404.
  * Spawned storyline has `spawned_from` provenance.
  * First beat of rescue-typed spawn is tagged Phase 1 'Locate'.
  * lean_dm system prompt includes the PENDING OBLIGATIONS block.
  * Existing /creative + /draft endpoints continue to work (regression).

Regression artefact for future testing iterations.
"""
from __future__ import annotations

import os
import time
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
    return {
        "tone": "gritty",
        "focus": "intrigue",
        "scope": "city",
        "danger": "medium",
    }


def _create_campaign(session, *, mission_type_slug=None):
    payload = {"characterId": CHARACTER_ID, "intent": _intent()}
    if mission_type_slug:
        payload["mission_type_slug"] = mission_type_slug
    r = session.post(f"{BASE_URL}/api/campaigns/draft", json=payload, timeout=60)
    assert r.status_code == 200, r.text
    body = r.json()
    cid = body.get("campaignId") or body.get("campaign_id")
    assert cid, f"missing campaignId: {body}"
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
        json=body, timeout=180,
    )
    assert r.status_code == 200, r.text
    return r.json()


def _spawn(session, campaign_id, *, player_action, current_storyline_id=None,
           character_id=CHARACTER_ID, narration_context=None):
    body = {"character_id": character_id, "player_action": player_action}
    if current_storyline_id:
        body["current_storyline_id"] = current_storyline_id
    if narration_context:
        body["narration_context"] = narration_context
    return session.post(
        f"{BASE_URL}/api/campaigns/{campaign_id}/storylines/spawn-from-action",
        json=body, timeout=180,
    )


# -------------------- validation: 400 / 404 --------------------


class TestSpawnValidation:
    def test_empty_player_action_returns_400(self, session):
        cid = _create_campaign(session, mission_type_slug="heist")
        r = _spawn(session, cid, player_action="   ")
        assert r.status_code == 400, r.text

    def test_unknown_character_returns_404(self, session):
        cid = _create_campaign(session, mission_type_slug="heist")
        r = _spawn(
            session, cid,
            player_action="I look for a beggar near the south gate",
            character_id="000000000000000000000000",
        )
        assert r.status_code == 404, r.text


# -------------------- OFF-HOOK: rescue spawn --------------------


class TestOffHookSpawnsRescue:
    """Player walks away from a 'whispering merchant' beat to look for a
    beggar — should pause the old storyline and spawn a NEW one using
    the rescue (or other closest) mission blueprint."""

    @pytest.fixture(scope="class")
    def spawned(self, session):
        cid = _create_campaign(session, mission_type_slug="heist")
        # First storyline: about a whispering merchant.
        drafted = _draft_storyline(
            session, cid,
            hook_text=(
                "TEST_a whispering merchant at the Guild stall is muttering "
                "about a planned shipment heist"
            ),
            hook_topic="TEST_whispering merchant",
            hook_verb="overhear",
        )
        sl_old = drafted["storyline"]
        # Off-hook action that has NOTHING to do with the merchant scene.
        r = _spawn(
            session, cid,
            current_storyline_id=sl_old["id"],
            player_action="I look for a ragged beggar near the south gate",
            narration_context=(
                "The merchant leans across the stall, whispering about "
                "the Guild's plans tonight."
            ),
        )
        assert r.status_code == 200, r.text
        data = r.json()
        return {"campaign_id": cid, "old": sl_old, "resp": data}

    def test_spawned_true(self, spawned):
        d = spawned["resp"]
        assert d.get("spawned") is True, f"expected spawned=true, got: {d}"
        assert d.get("storyline"), "expected storyline in response"
        assert d.get("storyline", {}).get("id") != spawned["old"]["id"]

    def test_mission_type_is_closest_existing_slug(self, spawned):
        d = spawned["resp"]
        mt = d.get("mission_type") or {}
        slug = mt.get("slug")
        # Must be one of the canonical mission types — never invented.
        valid = {"heist", "rescue", "assassination", "political_intrigue"}
        assert slug in valid, f"unexpected mission_type slug: {slug}"
        # The new storyline's mission_type snapshot should agree.
        sl_mt = (d.get("storyline") or {}).get("mission_type") or {}
        assert sl_mt.get("slug") == slug

    def test_old_storyline_paused(self, session, spawned):
        cid, sid = spawned["campaign_id"], spawned["old"]["id"]
        r = session.get(f"{BASE_URL}/api/campaigns/{cid}/storylines/{sid}", timeout=30)
        assert r.status_code == 200, r.text
        doc = r.json()
        assert doc.get("status") == "paused", (
            f"old storyline expected status=paused, got: {doc.get('status')}"
        )
        assert doc.get("paused_at"), "paused_at timestamp not set"

    def test_campaign_has_pending_obligation(self, session, spawned):
        cid, old = spawned["campaign_id"], spawned["old"]
        r = session.get(f"{BASE_URL}/api/campaigns/{cid}", timeout=30)
        assert r.status_code == 200, r.text
        camp = r.json()
        obs = camp.get("pending_obligations") or []
        assert obs, f"expected pending_obligations to be populated, got: {obs}"
        match = [o for o in obs if o.get("storyline_id") == old["id"]]
        assert match, f"no obligation for old storyline id={old['id']}: {obs}"
        ob = match[0]
        # Required keys.
        for key in ("storyline_title", "summary", "npc_names",
                    "location_names", "paused_at", "paused_at_beat"):
            assert key in ob, f"obligation missing key '{key}': {ob}"
        assert isinstance(ob["npc_names"], list)
        assert isinstance(ob["location_names"], list)

    def test_spawned_storyline_has_provenance(self, spawned):
        d = spawned["resp"]
        sl = d.get("storyline") or {}
        sf = sl.get("spawned_from")
        assert sf, f"expected spawned_from on new storyline, got: {sl}"
        assert sf.get("trigger") == "off_hook_player_action"
        assert sf.get("paused_storyline_id") == spawned["old"]["id"]
        assert "beggar" in (sf.get("player_action") or "").lower()
        assert sf.get("reasoning"), "expected non-empty reasoning"

    def test_spawned_storyline_first_beat_is_phase_1(self, spawned):
        d = spawned["resp"]
        sl = d.get("storyline") or {}
        beats = sl.get("beats") or []
        assert beats, "expected at least one beat on the spawned storyline"
        b0 = beats[0]
        # The new storyline should be Phase 1 of the chosen mission type.
        # Phase 1 names vary by mission_type slug — confirm phase_index=0
        # and phase_name is non-empty.
        mt_slug = ((sl.get("mission_type") or {}).get("slug") or "")
        assert b0.get("phase_index") == 0, f"phase_index={b0.get('phase_index')}"
        assert b0.get("phase_name"), f"missing phase_name: {b0}"
        # Specifically for rescue, Phase 1 must be 'Locate'.
        if mt_slug == "rescue":
            assert b0["phase_name"] == "Locate", (
                f"rescue Phase 1 expected 'Locate', got '{b0['phase_name']}'"
            )


# -------------------- ON-HOOK: no spawn --------------------


class TestOnHookDoesNotSpawn:
    def test_on_hook_returns_spawned_false_and_keeps_storyline_active(self, session):
        cid = _create_campaign(session, mission_type_slug="heist")
        drafted = _draft_storyline(
            session, cid,
            hook_text=(
                "TEST_a whispering merchant at the Guild stall is muttering "
                "about a planned shipment heist"
            ),
            hook_topic="TEST_whispering merchant",
            hook_verb="overhear",
        )
        sl = drafted["storyline"]
        # ON-HOOK: literally engaging with the merchant the beat is about.
        r = _spawn(
            session, cid,
            current_storyline_id=sl["id"],
            player_action="I lean closer and listen carefully to the merchant whispering",
            narration_context=(
                "The merchant leans across the stall, whispering about "
                "the Guild's plans tonight."
            ),
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("spawned") is False, f"expected spawned=false, got: {data}"
        # Old storyline must remain active.
        g = session.get(f"{BASE_URL}/api/campaigns/{cid}/storylines/{sl['id']}", timeout=30)
        assert g.status_code == 200, g.text
        assert g.json().get("status") == "active", (
            f"on-hook should NOT pause storyline, got: {g.json().get('status')}"
        )


# -------------------- prompt injection (unit test) --------------------


class TestPendingObligationsPromptBlock:
    """Unit-level: render_pending_obligations_for_prompt produces the
    PENDING OBLIGATIONS block expected by _build_system_prompt."""

    def test_render_empty_returns_empty_string(self):
        from services.storyline_spawner import render_pending_obligations_for_prompt
        assert render_pending_obligations_for_prompt([]) == ""
        assert render_pending_obligations_for_prompt(None) == ""

    def test_render_includes_header_and_npc_names(self):
        from services.storyline_spawner import render_pending_obligations_for_prompt
        obs = [{
            "storyline_id": "sl_test123",
            "storyline_title": "The Whispering Merchant",
            "summary": "You walked away mid-conversation with a Guild informant.",
            "npc_names": ["Halric the Merchant", "Sera"],
            "location_names": ["Guild Stall"],
            "paused_at": "2026-01-01T00:00:00+00:00",
            "paused_at_beat": 1,
        }]
        block = render_pending_obligations_for_prompt(obs)
        assert "PENDING OBLIGATIONS" in block
        assert "The Whispering Merchant" in block
        assert "Halric the Merchant" in block
        assert "Sera" in block
        assert "Guild Stall" in block
        # Should instruct the DM the NPCs remember.
        assert "REMEMBER" in block.upper()

    def test_extract_pending_obligations_from_storyline_shape(self):
        from services.storyline_spawner import extract_pending_obligations_from_storyline
        sl = {
            "id": "sl_xyz",
            "title": "Whispering Merchant",
            "current_beat": 1,
            "beats": [
                {
                    "title": "Overhear the Guild",
                    "description": "The merchant whispers.",
                    "outcome_text": "You caught the name 'Halric'.",
                    "targets": [
                        {"type": "npc", "name": "Halric"},
                        {"type": "location", "name": "Guild Stall"},
                    ],
                },
                {"title": "Confront Halric", "description": "...", "targets": []},
            ],
            "mission_type": {"slug": "political_intrigue"},
        }
        ob = extract_pending_obligations_from_storyline(sl)
        assert ob["storyline_id"] == "sl_xyz"
        assert ob["storyline_title"] == "Whispering Merchant"
        assert "Halric" in ob["npc_names"]
        assert "Guild Stall" in ob["location_names"]
        assert ob["paused_at_beat"] == 1
        assert ob["paused_at"]  # iso-string set
        assert ob["mission_type_slug"] == "political_intrigue"


# -------------------- regression: /draft + /creative still work --------------------


class TestExistingEndpointsRegression:
    def test_storylines_draft_still_works(self, session):
        cid = _create_campaign(session, mission_type_slug="heist")
        d = _draft_storyline(
            session, cid,
            hook_text="TEST_regression a courier's body washed up under the bridge",
            hook_topic="TEST_drowned courier",
            hook_verb="investigate",
        )
        sl = d.get("storyline") or {}
        assert sl.get("id"), f"missing storyline id: {d}"
        assert sl.get("status") == "active"
        beats = sl.get("beats") or []
        assert beats, "expected at least one beat"

    def test_storylines_creative_endpoint_still_works(self, session):
        cid = _create_campaign(session, mission_type_slug="heist")
        d = _draft_storyline(
            session, cid,
            hook_text="TEST_regression an iron-bound ledger left atop the desk",
            hook_topic="TEST_iron ledger",
            hook_verb="examine",
        )
        sid = d["storyline"]["id"]
        # On-hook creative approach — engaging directly with the active beat.
        r = session.post(
            f"{BASE_URL}/api/campaigns/{cid}/storylines/{sid}/creative",
            json={"approach_text": (
                "I crack open the iron-bound ledger on the desk and "
                "page through the most recent entries."
            )},
            timeout=180,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # Expected shape (per existing contract).
        assert "storyline" in data
        assert "judgment" in data
        assert data["judgment"] in {"passed", "partial", "failed"}
