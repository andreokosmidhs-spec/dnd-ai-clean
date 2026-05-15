"""Backend tests for GLOBAL DM Lessons persistence (Iter 18).

User requirement: lessons learned by the DM must survive deletion of any
single character or campaign and apply across every campaign + character
the player runs. Existing legacy lessons (no `scope` field) must continue
to be returned for backward compatibility.

Covers:
  1. POST creates lessons with `scope='global'`.
  2. GET on campaign B returns lessons CREATED in campaign A
     (union of scope=global, missing-scope legacy, and own-campaign).
  3. PATCH from campaign B can toggle/edit a lesson born in campaign A
     (match-by-id only).
  4. DELETE from campaign B can delete a lesson born in campaign A.
  5. merge_or_create_lesson dedupes ACROSS campaigns (Jaccard >= 0.4).
  6. Legacy (no scope) + campaign-scoped lessons get promoted to
     scope='global' once reinforced.
  7. load_active_lessons returns global + legacy + matching-campaign
     lessons sorted by weight then created_at, capped at limit.
  8. Reaction endpoint creates lessons with scope='global' too.
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests

# Make backend importable for the direct-service tests (load_active_lessons,
# merge_or_create_lesson) — those exercise the union/dedupe logic that
# doesn't otherwise round-trip via HTTP.
sys.path.insert(0, "/app/backend")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "test_database")


# ---------- shared HTTP fixture ----------

@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# Two distinct campaign IDs — neither needs to actually exist as a Campaign
# document; the DM-lessons collection uses campaign_id only for provenance.
CAMP_A = f"TEST_camp_a_{uuid.uuid4().hex[:8]}"
CAMP_B = f"TEST_camp_b_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def db():
    """Direct Motor handle for fixture setup + assertions."""
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(MONGO_URL)
    return client[DB_NAME]


@pytest.fixture(scope="module")
def loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def _create_lesson(api, campaign_id: str, text: str, *, lesson_type="style_preference",
                   keywords=None, weight=3):
    payload = {
        "type": lesson_type,
        "text": text,
        "trigger_keywords": keywords or [],
        "weight": weight,
    }
    r = api.post(f"{BASE_URL}/api/campaigns/{campaign_id}/dm-lessons",
                 json=payload, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["lesson"]


def _list_ids(api, campaign_id: str):
    r = api.get(f"{BASE_URL}/api/campaigns/{campaign_id}/dm-lessons", timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["lessons"]


@pytest.fixture(scope="module", autouse=True)
def _cleanup(api, db, loop):
    """Remove TEST_ data before and after the module so reruns are clean."""
    async def _wipe():
        await db["dm_lessons"].delete_many({
            "$or": [
                {"campaign_id": {"$in": [CAMP_A, CAMP_B]}},
                {"text": {"$regex": "^TEST_GLOBAL_"}},
                {"id": {"$regex": "^TEST_LEGACY_"}},
            ]
        })
    loop.run_until_complete(_wipe())
    yield
    loop.run_until_complete(_wipe())


# ============================================================
# 1. POST stores scope='global'
# ============================================================

class TestPostScopeGlobal:
    def test_new_lesson_has_scope_global(self, api):
        lsn = _create_lesson(
            api, CAMP_A,
            "TEST_GLOBAL_A1 — lead with sharp sensory detail first.",
            keywords=["TEST_GLOBAL_kwA1", "TEST_GLOBAL_kwA2", "TEST_GLOBAL_kwA3"],
        )
        assert lsn.get("scope") == "global", (
            f"new lessons must default to scope='global'; got {lsn.get('scope')!r}"
        )
        assert lsn["campaign_id"] == CAMP_A
        pytest.global_a1_id = lsn["id"]


# ============================================================
# 2. GET from another campaign returns the global lesson (union)
# ============================================================

class TestCrossCampaignVisibility:
    def test_camp_b_sees_camp_a_global(self, api):
        # Lesson created in campaign A should be visible from campaign B
        lessons = _list_ids(api, CAMP_B)
        ids = [ls["id"] for ls in lessons]
        assert pytest.global_a1_id in ids, (
            "lesson created in camp A must be visible from camp B (scope=global)"
        )

    def test_legacy_lesson_returned(self, api, db, loop):
        """Insert a raw legacy doc (no `scope` field) and confirm it's
        returned by GET for BOTH campaigns."""
        legacy_id = f"TEST_LEGACY_{uuid.uuid4().hex[:8]}"
        async def _insert():
            await db["dm_lessons"].insert_one({
                "id": legacy_id,
                "campaign_id": "some_old_campaign_that_is_deleted",
                "character_id": None,
                # NO `scope` field — pre-iter18 record
                "type": "rule_correction",
                "text": "TEST_GLOBAL_legacy — always require Stealth checks vs passive Perception.",
                "trigger_keywords": ["test_legacy_kw1"],
                "weight": 4,
                "enabled": True,
                "source": "manual",
                "source_ref": {},
                "apply_count": 0,
                "created_at": datetime.now(timezone.utc),
                "last_applied_at": None,
            })
        loop.run_until_complete(_insert())

        for camp in (CAMP_A, CAMP_B):
            ids = [ls["id"] for ls in _list_ids(api, camp)]
            assert legacy_id in ids, (
                f"legacy lesson (no scope field) must be returned by GET on {camp}"
            )
        pytest.legacy_id = legacy_id

    def test_campaign_scoped_lesson_only_visible_to_owner(self, api, db, loop):
        """Insert a `scope='campaign'` doc tied to camp A.  It should be
        visible from camp A but NOT from camp B (it's not global)."""
        scoped_id = f"TEST_GLOBAL_scoped_{uuid.uuid4().hex[:8]}"
        async def _insert():
            await db["dm_lessons"].insert_one({
                "id": scoped_id,
                "campaign_id": CAMP_A,
                "character_id": None,
                "scope": "campaign",
                "type": "taboo",
                "text": "TEST_GLOBAL_campaign_scoped — do not railroad the player.",
                "trigger_keywords": ["TEST_scoped_kw"],
                "weight": 3,
                "enabled": True,
                "source": "manual",
                "source_ref": {},
                "apply_count": 0,
                "created_at": datetime.now(timezone.utc),
                "last_applied_at": None,
            })
        loop.run_until_complete(_insert())

        a_ids = [ls["id"] for ls in _list_ids(api, CAMP_A)]
        b_ids = [ls["id"] for ls in _list_ids(api, CAMP_B)]
        assert scoped_id in a_ids, "campaign-scoped lesson must show in its own campaign"
        # GET list endpoint returns the campaign-scoped lesson only for the
        # campaign that owns it.  From any OTHER campaign it should be hidden.
        assert scoped_id not in b_ids, (
            "campaign-scoped lesson must NOT leak into other campaigns via GET"
        )


# ============================================================
# 3. PATCH from another campaign works (match-by-id only)
# ============================================================

class TestCrossCampaignPatch:
    def test_patch_via_other_campaign_url(self, api):
        # Toggle the camp-A lesson off via the camp-B URL
        r = api.patch(
            f"{BASE_URL}/api/campaigns/{CAMP_B}/dm-lessons/{pytest.global_a1_id}",
            json={"enabled": False},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        assert r.json()["lesson"]["enabled"] is False
        # And re-enable via yet another campaign URL
        r2 = api.patch(
            f"{BASE_URL}/api/campaigns/some_third_campaign/dm-lessons/{pytest.global_a1_id}",
            json={"enabled": True, "weight": 5},
            timeout=15,
        )
        assert r2.status_code == 200, r2.text
        lsn = r2.json()["lesson"]
        assert lsn["enabled"] is True
        assert lsn["weight"] == 5

    def test_patch_unknown_id_returns_404(self, api):
        r = api.patch(
            f"{BASE_URL}/api/campaigns/{CAMP_B}/dm-lessons/lsn_does_not_exist_xyz",
            json={"enabled": False},
            timeout=10,
        )
        assert r.status_code == 404


# ============================================================
# 5. Cross-campaign dedupe via merge_or_create_lesson (Jaccard >= 0.4)
# ============================================================

class TestCrossCampaignDedupe:
    def test_duplicate_lesson_in_other_campaign_merges(self, api):
        """Create a near-duplicate (same type + overlapping keywords) from
        camp B and confirm it merges into the camp-A lesson rather than
        creating a 2nd record."""
        baseline = _list_ids(api, CAMP_B)
        before_ids = {ls["id"] for ls in baseline}

        # Same type, 3 of the same keywords as camp_a_id1 → Jaccard = 1.0
        dupe = {
            "type": "style_preference",
            "text": "TEST_GLOBAL_A1_dupe — slightly different wording, same idea.",
            "trigger_keywords": ["TEST_GLOBAL_kwA1", "TEST_GLOBAL_kwA2", "TEST_GLOBAL_kwA3"],
            "weight": 3,
        }
        r = api.post(f"{BASE_URL}/api/campaigns/{CAMP_B}/dm-lessons",
                     json=dupe, timeout=20)
        assert r.status_code == 200, r.text
        merged = r.json()["lesson"]
        # Merged into the existing lesson — same id, weight bumped to <= 5
        assert merged["id"] == pytest.global_a1_id, (
            f"cross-campaign dedupe failed: returned new id {merged['id']!r} "
            f"instead of merging into {pytest.global_a1_id!r}"
        )
        assert merged["scope"] == "global"
        assert merged["weight"] >= 5  # was already 5; capped

        after_ids = {ls["id"] for ls in _list_ids(api, CAMP_B)}
        # No NEW id appeared
        assert after_ids == before_ids, "duplicate POST from camp B leaked a new lesson"

    def test_reinforcing_legacy_promotes_to_global(self, api, db, loop):
        """Hit a legacy (no-scope) lesson with a similar POST and confirm
        the underlying doc is now scope='global'."""
        legacy_id = pytest.legacy_id
        dupe = {
            "type": "rule_correction",
            "text": "TEST_GLOBAL_reinforce — require Stealth vs passive Perception.",
            "trigger_keywords": ["test_legacy_kw1", "stealth"],
            "weight": 3,
        }
        r = api.post(f"{BASE_URL}/api/campaigns/{CAMP_B}/dm-lessons",
                     json=dupe, timeout=20)
        assert r.status_code == 200, r.text
        merged = r.json()["lesson"]
        assert merged["id"] == legacy_id, (
            f"legacy reinforcement should merge into {legacy_id!r}, got {merged['id']!r}"
        )

        # Re-fetch directly from Mongo and confirm scope is now 'global'.
        async def _fetch():
            return await db["dm_lessons"].find_one({"id": legacy_id}, {"_id": 0})
        doc = loop.run_until_complete(_fetch())
        assert doc is not None
        assert doc.get("scope") == "global", (
            f"reinforced legacy lesson must be promoted to scope='global'; "
            f"got {doc.get('scope')!r}"
        )


# ============================================================
# 6. load_active_lessons — direct service test
# ============================================================

class TestLoadActiveLessonsUnion:
    def test_union_and_sort_and_limit(self, db, loop):
        from services.dm_lessons import load_active_lessons

        # Seed a deterministic mix in a fresh sandbox campaign.
        sandbox = f"TEST_GLOBAL_sandbox_{uuid.uuid4().hex[:6]}"
        other = f"TEST_GLOBAL_other_{uuid.uuid4().hex[:6]}"
        now = datetime.now(timezone.utc)

        seeds = [
            # Global lesson born elsewhere — must be returned
            {"id": "lsn_test_g1", "campaign_id": other, "scope": "global",
             "type": "rule_correction", "text": "TEST_GLOBAL_union global",
             "trigger_keywords": [], "weight": 5, "enabled": True,
             "source": "manual", "apply_count": 0,
             "created_at": now - timedelta(minutes=5), "last_applied_at": None},
            # Legacy (no scope) — must be returned
            {"id": "lsn_test_legacy", "campaign_id": other,
             "type": "rule_correction", "text": "TEST_GLOBAL_union legacy",
             "trigger_keywords": [], "weight": 3, "enabled": True,
             "source": "manual", "apply_count": 0,
             "created_at": now - timedelta(minutes=4), "last_applied_at": None},
            # Campaign-scoped to sandbox — must be returned
            {"id": "lsn_test_camp", "campaign_id": sandbox, "scope": "campaign",
             "type": "taboo", "text": "TEST_GLOBAL_union camp",
             "trigger_keywords": [], "weight": 4, "enabled": True,
             "source": "manual", "apply_count": 0,
             "created_at": now - timedelta(minutes=3), "last_applied_at": None},
            # Campaign-scoped to OTHER campaign — must be FILTERED OUT
            {"id": "lsn_test_other_camp", "campaign_id": other, "scope": "campaign",
             "type": "taboo", "text": "TEST_GLOBAL_union other_camp",
             "trigger_keywords": [], "weight": 5, "enabled": True,
             "source": "manual", "apply_count": 0,
             "created_at": now - timedelta(minutes=2), "last_applied_at": None},
            # Disabled lesson — must be filtered out
            {"id": "lsn_test_disabled", "campaign_id": other, "scope": "global",
             "type": "rule_correction", "text": "TEST_GLOBAL_union disabled",
             "trigger_keywords": [], "weight": 5, "enabled": False,
             "source": "manual", "apply_count": 0,
             "created_at": now - timedelta(minutes=1), "last_applied_at": None},
        ]

        async def _run():
            await db["dm_lessons"].insert_many([dict(s) for s in seeds])
            try:
                # Use a very high limit so unrelated lessons in the real DB
                # don't push our seeded weight-3 legacy out of the result set.
                lessons = await load_active_lessons(db, campaign_id=sandbox, limit=500)
            finally:
                await db["dm_lessons"].delete_many(
                    {"id": {"$in": [s["id"] for s in seeds]}}
                )
            return lessons

        lessons = loop.run_until_complete(_run())
        ids = [ls["id"] for ls in lessons]
        assert "lsn_test_g1" in ids, "global lesson must be loaded"
        assert "lsn_test_legacy" in ids, "legacy (no-scope) lesson must be loaded"
        assert "lsn_test_camp" in ids, "campaign-scoped (own) lesson must be loaded"
        assert "lsn_test_other_camp" not in ids, (
            "campaign-scoped lesson from another campaign must be filtered out"
        )
        assert "lsn_test_disabled" not in ids, "disabled lesson must be filtered out"

        # Sort: weight desc, then created_at desc.  Verify ordering across
        # the three seeded ids (filter the global result set to just our seeds).
        seeded = [ls for ls in lessons if ls["id"] in {
            "lsn_test_g1", "lsn_test_legacy", "lsn_test_camp"
        }]
        weights = [ls["weight"] for ls in seeded]
        assert weights == sorted(weights, reverse=True), (
            f"seeded lessons not sorted by weight desc: {weights}"
        )

    def test_limit_enforced(self, db, loop):
        from services.dm_lessons import load_active_lessons
        sandbox = f"TEST_GLOBAL_lim_{uuid.uuid4().hex[:6]}"
        now = datetime.now(timezone.utc)
        seeds = [
            {"id": f"lsn_test_lim_{i}", "campaign_id": "elsewhere", "scope": "global",
             "type": "rule_correction", "text": f"TEST_GLOBAL_limit {i}",
             "trigger_keywords": [], "weight": 3, "enabled": True,
             "source": "manual", "apply_count": 0,
             "created_at": now - timedelta(seconds=i), "last_applied_at": None}
            for i in range(8)
        ]

        async def _run():
            await db["dm_lessons"].insert_many([dict(s) for s in seeds])
            try:
                return await load_active_lessons(db, campaign_id=sandbox, limit=3)
            finally:
                await db["dm_lessons"].delete_many(
                    {"id": {"$in": [s["id"] for s in seeds]}}
                )

        lessons = loop.run_until_complete(_run())
        assert len(lessons) == 3, f"limit not honored: {len(lessons)} returned"


# ============================================================
# 7. Reaction endpoint creates lessons with scope='global'
# ============================================================

class TestReactionScopeGlobal:
    def test_reaction_lesson_is_global(self, api):
        body = {
            "reaction": "like",
            "narration": (
                "TEST_GLOBAL_reaction The blacksmith pauses mid-strike, sweat "
                "tracing the soot on his brow.  'You want it sharper than a "
                "wolf's tongue?' he grunts, and the forge swallows his laugh."
            ),
            "beat_title": "TEST_GLOBAL_reaction_beat",
        }
        r = api.post(f"{BASE_URL}/api/campaigns/{CAMP_A}/dm-lessons/reaction",
                     json=body, timeout=120)
        assert r.status_code == 200, r.text
        data = r.json()
        if data.get("action") == "skipped" or not data.get("lesson"):
            pytest.skip("LLM unavailable — distillation skipped")
        lsn = data["lesson"]
        assert lsn.get("scope") == "global", (
            f"reaction-distilled lessons must default to scope='global'; "
            f"got {lsn.get('scope')!r}"
        )


# ============================================================
# 4 + 8. DELETE from another campaign (run LAST so the id stays around)
# ============================================================

class TestZCrossCampaignDelete:
    def test_delete_via_other_campaign_url(self, api):
        # Delete the camp-A lesson via the camp-B URL
        r = api.delete(
            f"{BASE_URL}/api/campaigns/{CAMP_B}/dm-lessons/{pytest.global_a1_id}",
            timeout=15,
        )
        assert r.status_code == 200, r.text
        assert r.json().get("ok") is True

        # Confirm it's gone from BOTH campaigns
        for camp in (CAMP_A, CAMP_B):
            ids = [ls["id"] for ls in _list_ids(api, camp)]
            assert pytest.global_a1_id not in ids, (
                f"lesson still visible from {camp} after cross-campaign delete"
            )

    def test_delete_unknown_id_returns_404(self, api):
        r = api.delete(
            f"{BASE_URL}/api/campaigns/{CAMP_A}/dm-lessons/lsn_does_not_exist_xyz",
            timeout=10,
        )
        assert r.status_code == 404
