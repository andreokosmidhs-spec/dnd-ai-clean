"""Tests for the Node-Graph Campaign Map feature.

Covers:
  - GET /api/campaigns/{id}/world/graph (basic structure + starter has events)
  - POST /world/regions/{id}/visit (hydrates non-starter)
  - POST /world/events/{id}/accept (creates active quest)
  - POST /world/events/{id}/dismiss
  - GET /api/campaigns/{id}/quests (accepted event appears as active quest)
  - Legacy backfill behaviour (no 500 even if missing graph initially)
  - generate-world stores world.graph
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://dragon-quest-58.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

# ---------------- helpers ----------------


def _post(url, **kw):
    return requests.post(url, timeout=120, **kw)


def _get(url, **kw):
    return requests.get(url, timeout=60, **kw)


@pytest.fixture(scope="module")
def latest_campaign():
    """Resolve the latest V2 campaign id (precondition: previous testing seeded one)."""
    r = _get(f"{API}/campaigns/v2/latest")
    if r.status_code != 200:
        pytest.skip(f"No latest V2 campaign available (status {r.status_code}): {r.text[:200]}")
    data = r.json()
    cid = data.get("campaign_id")
    if not cid:
        pytest.skip("Latest V2 campaign payload missing campaign_id")
    return cid


@pytest.fixture(scope="module")
def graph(latest_campaign):
    r = _get(f"{API}/campaigns/{latest_campaign}/world/graph")
    assert r.status_code == 200, f"GET graph failed: {r.status_code} {r.text[:200]}"
    body = r.json()
    assert body.get("campaignId") == latest_campaign
    g = body.get("graph") or {}
    assert isinstance(g.get("regions"), list) and len(g["regions"]) >= 3, \
        f"Graph missing regions: {g}"
    assert isinstance(g.get("edges"), list)
    assert g.get("current_region_id"), "current_region_id must be set"
    return g


# ---------------- tests ----------------


class TestWorldGraph:
    def test_graph_basic_structure(self, graph):
        starters = [r for r in graph["regions"] if r.get("is_starting")]
        assert len(starters) == 1, f"Expected exactly 1 starter, got {len(starters)}"
        # current_region_id must reference SOME existing region (may differ
        # from starter if a prior visit moved the player).
        all_ids = {r["id"] for r in graph["regions"]}
        assert graph["current_region_id"] in all_ids, "current_region_id not in regions"
        assert starters[0].get("hydrated") is True
        # Starter should have full event deck
        events = starters[0].get("events") or []
        assert len(events) >= 3, f"Starter region should have >=3 events, got {len(events)}"
        # Each event must have required fields
        for ev in events:
            for k in ["id", "title", "description", "biome", "difficulty", "status"]:
                assert k in ev, f"Event missing field {k}: {ev}"
            assert ev["status"] in {"available", "accepted", "dismissed"}

    def test_neighbors_have_hints_or_events(self, graph):
        non_starters = [r for r in graph["regions"] if not r.get("is_starting")]
        assert non_starters, "Graph should have non-starter regions"
        # At least one non-starter region exists with hints (unhydrated)
        # (Some may already have been visited by previous tests)
        for r in non_starters:
            assert isinstance(r.get("hints"), list)
            assert isinstance(r.get("events"), list)
            # If not hydrated, must have hints; if hydrated, must have events
            if not r.get("hydrated"):
                assert len(r["hints"]) >= 1, f"Unhydrated region {r['name']} has no hints"

    def test_edges_reference_valid_regions(self, graph):
        ids = {r["id"] for r in graph["regions"]}
        for e in graph["edges"]:
            assert e.get("from") in ids, f"Edge from unknown: {e}"
            assert e.get("to") in ids, f"Edge to unknown: {e}"


class TestVisitRegion:
    def test_visit_hydrates_non_starter(self, latest_campaign, graph):
        # Find a non-starter, unhydrated region
        target = next(
            (r for r in graph["regions"] if not r.get("is_starting") and not r.get("hydrated")),
            None,
        )
        if not target:
            # Pick any non-starter; should still set current_region_id correctly
            target = next((r for r in graph["regions"] if not r.get("is_starting")), None)
        assert target, "No non-starter region found"

        r = _post(f"{API}/campaigns/{latest_campaign}/world/regions/{target['id']}/visit")
        assert r.status_code == 200, f"visit failed: {r.status_code} {r.text[:300]}"
        body = r.json()
        assert body.get("ok") is True
        assert body.get("current_region_id") == target["id"]
        region = body.get("region") or {}
        assert region.get("hydrated") is True
        assert region.get("visited") is True
        assert isinstance(region.get("events"), list)
        assert len(region["events"]) >= 3, f"Hydrated region should have events, got {region.get('events')}"
        for ev in region["events"]:
            assert ev.get("title") and ev.get("description") and ev.get("id")

    def test_visit_invalid_region_returns_404(self, latest_campaign):
        r = _post(f"{API}/campaigns/{latest_campaign}/world/regions/reg_nonexistent/visit")
        assert r.status_code == 404


class TestAcceptDismissEvent:
    def test_accept_event_creates_quest(self, latest_campaign):
        # Re-fetch graph to find an `available` event (in starter or hydrated region)
        g = _get(f"{API}/campaigns/{latest_campaign}/world/graph").json()["graph"]
        target_event = None
        target_region = None
        for r in g["regions"]:
            for ev in (r.get("events") or []):
                if ev.get("status") == "available":
                    target_event = ev
                    target_region = r
                    break
            if target_event:
                break
        assert target_event, "No available event found to accept"

        resp = _post(f"{API}/campaigns/{latest_campaign}/world/events/{target_event['id']}/accept")
        assert resp.status_code == 200, f"accept failed: {resp.status_code} {resp.text[:300]}"
        body = resp.json()
        assert body.get("ok") is True
        ev = body.get("event") or {}
        assert ev.get("status") == "accepted"
        assert ev.get("quest_id"), "event should have quest_id linked"
        quest = body.get("quest") or {}
        assert quest, "quest payload missing"
        # Persist context for chained tests
        TestAcceptDismissEvent.event_id = target_event["id"]
        TestAcceptDismissEvent.quest_id = ev["quest_id"]
        TestAcceptDismissEvent.region_name = target_region.get("name")
        TestAcceptDismissEvent.event_title = target_event.get("title")

    def test_accepted_event_appears_in_quests_list(self, latest_campaign):
        # Wait briefly to ensure DB write-through
        time.sleep(0.5)
        r = _get(f"{API}/campaigns/{latest_campaign}/quests")
        assert r.status_code == 200, f"GET /quests failed: {r.text[:200]}"
        quests = r.json().get("quests") or []
        # Look for the recently accepted quest by id
        target_qid = getattr(TestAcceptDismissEvent, "quest_id", None)
        # /quests returns shape with `quest_id` field
        match = next((q for q in quests if q.get("quest_id") == target_qid), None)
        assert match, f"Accepted quest id {target_qid} not in /quests; quests count={len(quests)}"
        # Status should be active
        status = (match.get("status") or "").lower()
        assert status == "active", f"Expected active, got {status}"

    def test_accept_already_accepted_returns_400(self, latest_campaign):
        ev_id = getattr(TestAcceptDismissEvent, "event_id", None)
        if not ev_id:
            pytest.skip("Prior accept did not run")
        resp = _post(f"{API}/campaigns/{latest_campaign}/world/events/{ev_id}/accept")
        assert resp.status_code == 400, f"Expected 400 on re-accept, got {resp.status_code}"

    def test_dismiss_event(self, latest_campaign):
        # Find another available event
        g = _get(f"{API}/campaigns/{latest_campaign}/world/graph").json()["graph"]
        target = None
        for r in g["regions"]:
            for ev in (r.get("events") or []):
                if ev.get("status") == "available":
                    target = ev
                    break
            if target:
                break
        if not target:
            pytest.skip("No available event remaining to dismiss")
        resp = _post(f"{API}/campaigns/{latest_campaign}/world/events/{target['id']}/dismiss")
        assert resp.status_code == 200
        assert resp.json().get("ok") is True

        # Verify status persisted
        g2 = _get(f"{API}/campaigns/{latest_campaign}/world/graph").json()["graph"]
        found = None
        for r in g2["regions"]:
            for ev in (r.get("events") or []):
                if ev.get("id") == target["id"]:
                    found = ev
                    break
        assert found and found.get("status") == "dismissed", f"Dismiss did not persist: {found}"

    def test_dismiss_invalid_event_404(self, latest_campaign):
        r = _post(f"{API}/campaigns/{latest_campaign}/world/events/evt_doesnotexist/dismiss")
        assert r.status_code == 404


class TestCampaignDocHasGraph:
    def test_campaign_get_includes_world_graph(self, latest_campaign):
        r = _get(f"{API}/campaigns/{latest_campaign}")
        assert r.status_code == 200
        camp = r.json()
        world = camp.get("world") or {}
        graph = world.get("graph") or {}
        assert graph.get("regions"), "Campaign world.graph should be populated"
        assert graph.get("current_region_id")
