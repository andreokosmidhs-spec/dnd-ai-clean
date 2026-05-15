"""Backend tests for Iter 19 — Storyline reward XP applied to character.

Covers:
  * resolve endpoint returns `player_updates` with normalized xp/level fields
    on completion, and null when storyline does not complete.
  * creative endpoint also returns `player_updates` on completion.
  * characters_v2 doc is updated with new current_xp / xp_to_next / level /
    cumulative `experience` after a completing resolve.
  * Level-up rollover: a 200 XP gain at L1 (threshold 150) increments level
    to 2 with current_xp = 50 remainder and level_up_events=['LEVEL_UP:2'].
  * No reward / reward.xp == 0 → player_updates is None and character doc
    untouched.
  * Unit-level smoke: services.progression_service exports the function the
    storylines router imports.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict

import pytest
import requests
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://dragon-quest-58.preview.emergentagent.com",
).rstrip("/")
CAMPAIGN_ID = "a19b5ff2-e859-4cef-9019-b36e2dbfdd39"
CHARACTER_ID = "69f2985e0999201c3edfaa3a"

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "dnd_ai_db")


# ----------------------- helpers / fixtures -----------------------

@pytest.fixture(scope="module")
def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _read_character_doc(char_id: str) -> Dict[str, Any]:
    """Direct mongo read of the characters_v2 document.

    Returns {} if not found. Uses a fresh event loop so it's safe to call
    from sync pytest tests.
    """
    async def _go() -> Dict[str, Any]:
        client = AsyncIOMotorClient(MONGO_URL)
        try:
            db = client[DB_NAME]
            doc = await db.characters_v2.find_one({"_id": ObjectId(char_id)})
            return doc or {}
        finally:
            client.close()

    return asyncio.new_event_loop().run_until_complete(_go())


def _patch_character_doc(char_id: str, patch: Dict[str, Any]) -> None:
    async def _go() -> None:
        client = AsyncIOMotorClient(MONGO_URL)
        try:
            db = client[DB_NAME]
            await db.characters_v2.update_one(
                {"_id": ObjectId(char_id)}, {"$set": patch}
            )
        finally:
            client.close()

    asyncio.new_event_loop().run_until_complete(_go())


# ----------------------- 0. unit smoke (catches ImportError) -----------------------


class TestProgressionServiceExport:
    """The storylines router imports `apply_xp_to_character` from
    services.progression_service. If that import fails, _apply_storyline_reward_xp
    swallows the exception and silently returns None, so we'd never apply XP.
    Catch that contract violation here before any HTTP testing."""

    def test_apply_xp_to_character_is_importable(self):
        import importlib
        import sys

        mod = importlib.import_module("services.progression_service")
        # Force reload to make sure we hit current source
        mod = importlib.reload(mod)
        assert hasattr(mod, "apply_xp_to_character"), (
            "services.progression_service must export apply_xp_to_character "
            "(the storylines router imports this name). Currently only "
            f"exports: {[n for n in dir(mod) if not n.startswith('_')]}"
        )

    def test_apply_xp_to_character_level_up_rollover(self):
        """Direct unit-level: 200 XP at L1 → L2, remainder 50."""
        mod = pytest.importorskip("services.progression_service")
        if not hasattr(mod, "apply_xp_to_character"):
            pytest.skip("apply_xp_to_character missing (covered by export test)")
        char = {"level": 1, "current_xp": 0, "max_hp": 10}
        updated, events = mod.apply_xp_to_character(char, 200)
        assert updated["level"] == 2
        assert updated["current_xp"] == 50  # 200 - 150 threshold
        assert updated["xp_to_next"] == 300  # L2->L3 threshold
        assert "LEVEL_UP:2" in events


# ----------------------- shared seed character helpers -----------------------


@pytest.fixture
def fresh_character_seed():
    """Snapshot the test character's pre-test XP fields and restore on
    teardown — keeps the test suite idempotent against the shared character."""
    pre = _read_character_doc(CHARACTER_ID)
    snapshot = {
        "level": pre.get("level", 1),
        "current_xp": pre.get("current_xp", 0),
        "xp_to_next": pre.get("xp_to_next", 150),
        "experience": pre.get("experience", 0),
        "max_hp": pre.get("max_hp", 10),
        "attack_bonus": pre.get("attack_bonus", 0),
    }
    # Reset to a clean L1 baseline so level-up math is predictable.
    _patch_character_doc(CHARACTER_ID, {
        "level": 1,
        "current_xp": 0,
        "xp_to_next": 150,
        "experience": 0,
    })
    yield snapshot
    # Restore original
    _patch_character_doc(CHARACTER_ID, snapshot)


def _draft_storyline(session: requests.Session, hook_topic: str) -> str:
    body = {
        "character_id": CHARACTER_ID,
        "hook_text": f"TEST_xp_{hook_topic}",
        "hook_topic": f"TEST_xp_{hook_topic}",
        "hook_verb": "examine",
    }
    r = session.post(
        f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/draft",
        json=body, timeout=90,
    )
    assert r.status_code == 200, r.text
    return r.json()["storyline"]["id"]


def _resolve_until_complete(session: requests.Session, sid: str, max_iter: int = 10):
    """Resolve passed beats until storyline completes. Returns the final
    /resolve response body (the one where completed=True)."""
    last_payload = None
    for _ in range(max_iter):
        r = session.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}/resolve",
            json={"outcome": "passed", "outcome_text": "TEST cleared"},
            timeout=120,
        )
        assert r.status_code == 200, r.text
        last_payload = r.json()
        if last_payload.get("completed"):
            return last_payload
    raise AssertionError(f"Storyline {sid} did not complete in {max_iter} iterations")


# ----------------------- 1. resolve: player_updates shape & persistence -----------------------


class TestResolvePlayerUpdates:
    def test_resolve_non_completion_returns_null_player_updates(
        self, session, fresh_character_seed
    ):
        sid = _draft_storyline(session, "noncomplete")
        # The very first resolve almost certainly won't complete (scenes grow).
        r = session.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}/resolve",
            json={"outcome": "passed", "outcome_text": "TEST step 1"},
            timeout=120,
        )
        assert r.status_code == 200, r.text
        payload = r.json()
        # If by chance it completed on first call, skip this assertion — the
        # contract is just "null when not completed"; covered in the other test.
        if not payload.get("completed"):
            assert payload.get("player_updates") is None, (
                f"Expected player_updates=null on in-progress resolve, got: "
                f"{payload.get('player_updates')}"
            )

    def test_resolve_completion_returns_player_updates_and_persists(
        self, session, fresh_character_seed
    ):
        sid = _draft_storyline(session, "completes")
        final = _resolve_until_complete(session, sid)
        reward = final.get("reward") or {}
        pu = final.get("player_updates")

        # Contract: if reward.xp > 0, player_updates must be populated.
        xp_award = int(reward.get("xp") or 0)
        if xp_award <= 0:
            # Reward generator chose 0 XP — player_updates must be null and
            # character doc must NOT be mutated.
            assert pu is None, f"player_updates must be null when xp=0, got: {pu}"
            doc = _read_character_doc(CHARACTER_ID)
            assert doc.get("current_xp", 0) == 0
            assert doc.get("experience", 0) == 0
            return

        assert isinstance(pu, dict), (
            f"player_updates must be a dict when reward.xp>0; "
            f"reward={reward}, player_updates={pu}"
        )
        # Shape
        for key in ("xp_gained", "current_xp", "xp_to_next", "level",
                    "level_up_events", "xp_reason"):
            assert key in pu, f"player_updates missing '{key}': {pu}"
        assert pu["xp_gained"] == xp_award
        assert isinstance(pu["level"], int) and pu["level"] >= 1
        assert isinstance(pu["current_xp"], int) and pu["current_xp"] >= 0
        assert isinstance(pu["xp_to_next"], int) and pu["xp_to_next"] >= 0
        assert isinstance(pu["level_up_events"], list)

        # Persistence: read the characters_v2 doc directly.
        doc = _read_character_doc(CHARACTER_ID)
        assert doc, "character doc disappeared"
        assert doc.get("current_xp") == pu["current_xp"], (
            f"mongo current_xp ({doc.get('current_xp')}) != "
            f"player_updates.current_xp ({pu['current_xp']})"
        )
        assert doc.get("xp_to_next") == pu["xp_to_next"]
        assert doc.get("level") == pu["level"]
        # Cumulative experience bumped by xp_gained from the seeded 0 baseline.
        assert doc.get("experience") == xp_award, (
            f"cumulative experience expected {xp_award}, got {doc.get('experience')}"
        )

    def test_levelup_rollover_via_resolve_chain(
        self, session, fresh_character_seed
    ):
        """Drive multiple storylines to completion and assert that once
        cumulative XP crosses the 150 L1→L2 threshold, the character's level
        becomes >= 2 and current_xp resets. This is the integration mirror of
        the unit-level rollover test above."""
        total_xp = 0
        observed_level_up = False
        for i in range(3):
            sid = _draft_storyline(session, f"rollover{i}")
            final = _resolve_until_complete(session, sid)
            pu = final.get("player_updates") or {}
            xp_g = int(pu.get("xp_gained") or 0)
            total_xp += xp_g
            if pu.get("level_up_events"):
                observed_level_up = True
                assert pu["level"] >= 2
                # On level up, current_xp must be < new threshold (the remainder).
                assert pu["current_xp"] < pu["xp_to_next"] or pu["xp_to_next"] == 0
            if total_xp >= 150:
                # Mongo state must reflect level-up by this point.
                doc = _read_character_doc(CHARACTER_ID)
                assert doc.get("level", 1) >= 2, (
                    f"cumulative XP {total_xp} crossed L1→L2 threshold but "
                    f"character level is {doc.get('level')}"
                )
                observed_level_up = True
                break
        if not observed_level_up:
            pytest.skip(
                f"Reward generator awarded too little XP across 3 storylines "
                f"(total={total_xp}); cannot exercise level-up rollover via "
                f"the public API in this environment."
            )


# ----------------------- 2. creative endpoint returns player_updates -----------------------


class TestCreativePlayerUpdates:
    def test_creative_response_shape_includes_player_updates_field(
        self, session, fresh_character_seed
    ):
        """Smoke: /creative response must include the `player_updates` key
        (None on non-completion, dict on completion). We don't necessarily
        drive it to completion since LLM behavior is non-deterministic; just
        assert the key is in the schema."""
        sid = _draft_storyline(session, "creative")
        r = session.post(
            f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/storylines/{sid}/creative",
            json={
                "approach_text": (
                    "TEST: I carefully inspect the seal, looking for maker's marks."
                ),
                "character_id": CHARACTER_ID,
            },
            timeout=120,
        )
        assert r.status_code == 200, r.text
        payload = r.json()
        assert "player_updates" in payload, (
            f"creative response missing player_updates key: {list(payload.keys())}"
        )
        # If completed, must be a dict (or None when xp==0); else must be None.
        if payload.get("completed"):
            pu = payload.get("player_updates")
            reward = payload.get("reward") or {}
            if int(reward.get("xp") or 0) > 0:
                assert isinstance(pu, dict)
                assert pu.get("xp_gained") == int(reward["xp"])
        else:
            assert payload.get("player_updates") is None


# ----------------------- 3. helper-level: zero-XP path -----------------------


class TestApplyStorylineRewardXpHelper:
    """Direct call into the helper so we can exercise edge cases without
    needing the LLM reward generator to produce a 0-XP path."""

    @pytest.mark.asyncio
    async def test_no_reward_returns_none(self):
        from routers import storylines as st_router

        # Need a db handle attached to the router for the persist branch.
        client = AsyncIOMotorClient(MONGO_URL)
        try:
            st_router.set_database(client[DB_NAME])
            character = {
                "id": CHARACTER_ID,
                "level": 1,
                "current_xp": 0,
                "experience": 0,
            }
            assert await st_router._apply_storyline_reward_xp(character, None) is None
            assert await st_router._apply_storyline_reward_xp(character, {}) is None
            assert await st_router._apply_storyline_reward_xp(
                character, {"xp": 0}
            ) is None
        finally:
            client.close()

    @pytest.mark.asyncio
    async def test_helper_applies_and_persists(self):
        from routers import storylines as st_router

        client = AsyncIOMotorClient(MONGO_URL)
        try:
            st_router.set_database(client[DB_NAME])
            # Reset doc to L1 / 0xp baseline
            await client[DB_NAME].characters_v2.update_one(
                {"_id": ObjectId(CHARACTER_ID)},
                {"$set": {"level": 1, "current_xp": 0, "xp_to_next": 150,
                          "experience": 0}},
            )
            char = await client[DB_NAME].characters_v2.find_one(
                {"_id": ObjectId(CHARACTER_ID)}
            )
            char["id"] = str(char.pop("_id"))
            pu = await st_router._apply_storyline_reward_xp(
                char, {"xp": 200, "title": "Test Reward"}
            )
            assert pu is not None, (
                "_apply_storyline_reward_xp returned None for a 200 XP reward "
                "— likely the underlying import/apply failed silently."
            )
            assert pu["xp_gained"] == 200
            assert pu["level"] == 2
            assert pu["current_xp"] == 50
            assert pu["xp_to_next"] == 300
            assert "LEVEL_UP:2" in pu["level_up_events"]
            assert pu["xp_reason"] == "Test Reward"

            # Persistence
            doc = await client[DB_NAME].characters_v2.find_one(
                {"_id": ObjectId(CHARACTER_ID)}
            )
            assert doc["level"] == 2
            assert doc["current_xp"] == 50
            assert doc["xp_to_next"] == 300
            assert doc["experience"] == 200
        finally:
            # Cleanup baseline
            await client[DB_NAME].characters_v2.update_one(
                {"_id": ObjectId(CHARACTER_ID)},
                {"$set": {"level": 1, "current_xp": 0, "xp_to_next": 150,
                          "experience": 0}},
            )
            client.close()
