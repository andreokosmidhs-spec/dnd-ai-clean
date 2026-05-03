"""Lead-card mechanic regression tests.

Covers:
  - Storyline draft now tags beats with reveal_type and (for knowledge beats)
    a non-empty `prompt` and `targets` list.
  - /resolve on a knowledge beat:
      passed       -> active lead with secret_content=None, tags include 'revealed'
      failed (FF)  -> sealed lead, secret_content holds revelation, tags include 'sealed'
  - /resolve on an action beat -> lead=None.
  - /creative on a knowledge beat -> lead is minted similarly.
  - /unseal:
      mode=roll, total>=DC      -> ok=True, unsealed=True, description swap, status='active'
      mode=roll, total<DC       -> ok=False, unsealed=False, stays sealed
      mode=creative, passed/partial -> ok=True, unsealed=True
      non-lead / non-sealed card -> 400
"""

import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
CAMPAIGN_ID = "a19b5ff2-e859-4cef-9019-b36e2dbfdd39"
CHARACTER_ID = "69f2985e0999201c3edfaa3a"


# ---- helpers ----

def _draft(hook_text="A scrap of parchment names a stranger you've never met."):
    payload = {
        "character_id": CHARACTER_ID,
        "hook_text": hook_text,
        "hook_id": f"TEST_lead_{uuid.uuid4().hex[:8]}",
        "hook_topic": "the parchment",
        "hook_verb": "examine",
        "narration_context": "TEST seed for lead cards",
    }
    r = requests.post(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/draft", json=payload, timeout=60)
    assert r.status_code == 200, r.text
    return r.json()["storyline"]


def _resolve(sid, outcome, mode=None, roll_total=None):
    body = {"outcome": outcome}
    if mode:
        body["mode"] = mode
    if roll_total is not None:
        body["roll_total"] = roll_total
    r = requests.post(
        f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}/resolve",
        json=body, timeout=60,
    )
    return r


def _find_index(beats, reveal_type):
    for i, b in enumerate(beats):
        if (b.get("reveal_type") or "") == reveal_type:
            return i
    return None


def _walk_to_beat(sid, beats, target_idx):
    """Resolve preceding beats with passed (action) so the target beat becomes active.
    Returns beats array of the storyline AT the target beat (i.e., after walking)."""
    for i in range(target_idx):
        # Pass the preceding beat with `passed` (cheap; doesn't matter what type)
        r = _resolve(sid, "passed")
        assert r.status_code == 200, f"walk step {i} failed: {r.text}"


# =========================================================
# 1. Draft tags beats with reveal_type / prompt / targets
# =========================================================

class TestDraftReveal:
    def test_draft_has_knowledge_beat_with_prompt(self):
        sl = _draft("An old etched medallion rests under the table.")
        beats = sl.get("beats") or []
        assert len(beats) >= 3
        # Every beat must have a reveal_type in the allowed set.
        for b in beats:
            assert b.get("reveal_type") in {"action", "knowledge"}, b
        # Find at least one knowledge beat with non-empty prompt.
        ks = [b for b in beats if b.get("reveal_type") == "knowledge"]
        assert ks, f"expected at least one knowledge beat; got {[b.get('reveal_type') for b in beats]}"
        for b in ks:
            assert (b.get("prompt") or "").strip(), f"knowledge beat missing prompt: {b}"
            # targets list must be a list (may be empty if LLM omitted)
            assert isinstance(b.get("targets"), list)

    def test_draft_action_beats_have_no_prompt(self):
        sl = _draft("A guard takes a cautious step back when she sees you.")
        beats = sl.get("beats") or []
        actions = [b for b in beats if b.get("reveal_type") == "action"]
        for b in actions:
            assert (b.get("prompt") or "") == "", f"action beat should have empty prompt: {b}"
            assert b.get("targets") == [], f"action beat should have empty targets: {b}"


# =========================================================
# 2. Lead card minting on /resolve
# =========================================================

class TestResolveLeadMinting:

    def test_passed_knowledge_mints_active_lead(self):
        sl = _draft("Soot streaks the doorframe in a pattern you almost recognize.")
        beats = sl["beats"]
        k_idx = _find_index(beats, "knowledge")
        if k_idx is None:
            pytest.skip("Draft produced no knowledge beat")
        _walk_to_beat(sl["id"], beats, k_idx)
        secret = beats[k_idx].get("description")
        r = _resolve(sl["id"], "passed")
        assert r.status_code == 200, r.text
        body = r.json()
        lead = body.get("lead")
        assert lead is not None, f"lead expected on knowledge passed; got {body}"
        assert lead["type"] == "lead"
        assert lead["status"] == "active"
        assert lead.get("secret_content") in (None, "")
        assert "revealed" in (lead.get("tags") or [])
        # description should be the secret revelation we just unlocked.
        assert lead["description"] == secret

    def test_failed_knowledge_mints_sealed_lead_persisted(self):
        sl = _draft("A torn flag lies half-buried in the snow outside the gate.")
        beats = sl["beats"]
        k_idx = _find_index(beats, "knowledge")
        if k_idx is None:
            pytest.skip("Draft produced no knowledge beat")
        _walk_to_beat(sl["id"], beats, k_idx)
        hidden = beats[k_idx].get("description")
        r = _resolve(sl["id"], "failed", mode="fail-forward")
        assert r.status_code == 200, r.text
        body = r.json()
        lead = body.get("lead")
        assert lead is not None, f"lead expected on knowledge failed; got {body}"
        assert lead["type"] == "lead"
        assert lead["status"] == "sealed"
        assert lead.get("secret_content") == hidden
        assert "sealed" in (lead.get("tags") or [])
        assert "find someone" in (lead.get("description") or "").lower()
        # verify persistence: GET cards endpoint via the campaign cards route
        cid = lead.get("id")
        rget = requests.get(f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/cards", timeout=30)
        if rget.status_code == 200:
            cards = rget.json() if isinstance(rget.json(), list) else rget.json().get("cards", [])
            assert any(c.get("id") == cid for c in cards), "sealed lead not persisted in cards collection"

    def test_action_beat_resolve_returns_no_lead(self):
        sl = _draft("Someone is following you down the alley with measured steps.")
        beats = sl["beats"]
        a_idx = _find_index(beats, "action")
        if a_idx is None:
            pytest.skip("Draft produced no action beat")
        _walk_to_beat(sl["id"], beats, a_idx)
        r = _resolve(sl["id"], "passed")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("lead") is None, f"lead should be None on action beat resolve: {body.get('lead')}"


# =========================================================
# 3. /creative endpoint also mints leads on knowledge beats
# =========================================================

class TestCreativeLead:
    def test_creative_on_knowledge_beat_returns_lead(self):
        sl = _draft("A rusted key turns in your palm, warm where it shouldn't be.")
        beats = sl["beats"]
        k_idx = _find_index(beats, "knowledge")
        if k_idx is None:
            pytest.skip("Draft produced no knowledge beat")
        _walk_to_beat(sl["id"], beats, k_idx)
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sl['id']}/creative",
            json={"approach_text": "I take the key to the loremaster who lives by the river to study its make."},
            timeout=90,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        # 'lead' key should exist; may be None only if judged_outcome=='failed' AND beat was action.
        assert "lead" in body
        if body.get("judgment") in {"passed", "partial"}:
            lead = body.get("lead")
            assert lead is not None
            assert lead["type"] == "lead"
            assert lead["status"] == "active"


# =========================================================
# 4. /unseal endpoint
# =========================================================

def _create_sealed_lead():
    """Helper: draft + fail a knowledge beat to obtain a sealed lead card."""
    sl = _draft("A coded prayer is scratched into the lintel above the door.")
    beats = sl["beats"]
    k_idx = _find_index(beats, "knowledge")
    if k_idx is None:
        pytest.skip("Draft produced no knowledge beat")
    _walk_to_beat(sl["id"], beats, k_idx)
    r = _resolve(sl["id"], "failed", mode="fail-forward")
    assert r.status_code == 200, r.text
    lead = r.json().get("lead")
    assert lead and lead.get("status") == "sealed"
    return lead


class TestUnseal:
    def test_unseal_roll_high_succeeds(self):
        lead = _create_sealed_lead()
        secret = lead["secret_content"]
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/cards/{lead['id']}/unseal",
            json={"mode": "roll", "roll_total": 25}, timeout=30,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is True and body["unsealed"] is True
        card = body["card"]
        assert card["status"] == "active"
        assert card["description"] == secret
        assert card.get("secret_content") in (None, "")
        tags = card.get("tags") or []
        assert "sealed" not in tags
        assert "revealed" in tags

    def test_unseal_roll_low_fails(self):
        lead = _create_sealed_lead()
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/cards/{lead['id']}/unseal",
            json={"mode": "roll", "roll_total": 3}, timeout=30,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is False and body["unsealed"] is False
        # Card still sealed: re-fetch via second unseal to confirm sealed state
        r2 = requests.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/cards/{lead['id']}/unseal",
            json={"mode": "roll", "roll_total": 25}, timeout=30,
        )
        assert r2.status_code == 200, r2.text  # still allowed -> means it was still sealed
        assert r2.json()["unsealed"] is True

    def test_unseal_creative_succeeds(self):
        lead = _create_sealed_lead()
        secret = lead["secret_content"]
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/cards/{lead['id']}/unseal",
            json={
                "mode": "creative",
                "creative_text": "I take the inscription to the loremaster who lives by the river and ask her to read the carving.",
            },
            timeout=90,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        # LLM should typically return passed/partial; if failed, accept and log.
        if body.get("ok") is True:
            assert body["unsealed"] is True
            card = body["card"]
            assert card["status"] == "active"
            assert card["description"] == secret
        else:
            pytest.skip(f"LLM judged creative attempt as failed; not a code bug: {body.get('narration')}")

    def test_unseal_on_non_sealed_card_returns_400(self):
        # First unseal a card to make it 'active', then try to unseal it again.
        lead = _create_sealed_lead()
        r1 = requests.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/cards/{lead['id']}/unseal",
            json={"mode": "roll", "roll_total": 25}, timeout=30,
        )
        assert r1.status_code == 200 and r1.json()["unsealed"] is True
        # Second attempt: card is now active, not sealed
        r2 = requests.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/cards/{lead['id']}/unseal",
            json={"mode": "roll", "roll_total": 25}, timeout=30,
        )
        assert r2.status_code == 400, r2.text
        # Body wrapped by global handler {error:{message:...}} or fastapi {detail:...}
        text = r2.text.lower()
        assert "not a sealed lead" in text

    def test_unseal_invalid_mode_returns_400(self):
        lead = _create_sealed_lead()
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/cards/{lead['id']}/unseal",
            json={"mode": "shenanigans"}, timeout=30,
        )
        assert r.status_code == 400
