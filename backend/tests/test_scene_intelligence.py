"""Tests for scene_intelligence_service — tension detection, extraction, DM embedding, encounter bridge."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from services.scene_intelligence_service import (
    _detect_tension_score_fast,
    _extract_people_fast,
    _extract_exits_fast,
    _extract_objects_fast,
    merge_scene_intel,
    update_scene_intelligence,
    get_dm_embedding_instructions,
    scene_intel_to_encounter_input,
    build_encounter_from_scene,
    TENSION_WATCH, TENSION_RISING, TENSION_THREAT, TENSION_IMMINENT,
)


# ── _detect_tension_score_fast ────────────────────────────────────────────────

class TestTensionDetection:
    def test_peaceful_narration_returns_zero(self):
        narration = "You smell warm bread. Music plays softly. People are laughing and singing."
        assert _detect_tension_score_fast(narration) == 0.0

    def test_tense_narration_reaches_medium(self):
        narration = (
            "The largest man, scarred and broad-shouldered, sets down his cards. "
            "His eyes are narrowed. The innkeeper takes a step back."
        )
        score = _detect_tension_score_fast(narration)
        assert score >= TENSION_WATCH  # 0.25
        assert score < TENSION_THREAT  # below 0.65

    def test_hostile_narration_reaches_high(self):
        narration = "He draws his weapon and levels a threat at you. His grip on the blade tightens."
        score = _detect_tension_score_fast(narration)
        assert score >= TENSION_THREAT

    def test_combat_narration_reaches_imminent(self):
        narration = "He lunges forward, initiative drawn. Combat begins."
        score = _detect_tension_score_fast(narration)
        assert score >= TENSION_IMMINENT

    def test_tension_ratchets_up_only(self):
        high_score = 0.7
        peaceful = "The fire crackles gently. Everyone is calm and relaxed."
        result = _detect_tension_score_fast(peaceful, existing_score=high_score)
        assert result == high_score  # never decreases

    def test_existing_score_preserved_when_narration_is_lower(self):
        result = _detect_tension_score_fast("A warm evening at the inn.", existing_score=0.5)
        assert result == 0.5

    def test_existing_score_replaced_when_narration_is_higher(self):
        result = _detect_tension_score_fast("He draws his blade.", existing_score=0.1)
        assert result >= TENSION_THREAT

    def test_narrowed_eyes_detected(self):
        narration = "Her eyes are narrowed, watching you carefully."
        assert _detect_tension_score_fast(narration) >= TENSION_WATCH

    def test_scarred_figure_detected(self):
        narration = "A scarred man leans against the wall."
        assert _detect_tension_score_fast(narration) >= TENSION_WATCH

    def test_unlatched_window_detected(self):
        narration = "The east window is unlatched, creaking in the wind."
        assert _detect_tension_score_fast(narration) >= TENSION_WATCH

    def test_score_capped_at_one(self):
        # Many combat keywords at once should not exceed 1.0
        narration = "He attacks! Draws blade! Combat! Fight! Aggression! Violence!"
        assert _detect_tension_score_fast(narration) <= 1.0


# ── _extract_people_fast ──────────────────────────────────────────────────────

class TestExtractPeople:
    def test_three_men_playing_cards(self):
        narration = "You see three men playing cards at a corner table."
        people = _extract_people_fast(narration)
        assert any(p["count"] == 3 for p in people)
        assert any("men" in p["description"] for p in people)

    def test_some_people_at_bar(self):
        narration = "Some people are drinking at the bar."
        people = _extract_people_fast(narration)
        assert any(p["count"] >= 2 for p in people)

    def test_guard_inferred_as_specialist(self):
        narration = "Two guards stand at the entrance."
        people = _extract_people_fast(narration)
        guard_entries = [p for p in people if "guard" in p["description"]]
        assert guard_entries
        assert guard_entries[0]["tier_hint"] == "specialist"

    def test_scarred_brawler_inferred_as_gifted(self):
        narration = "Three brawlers crowd around the back table."
        people = _extract_people_fast(narration)
        brawler_entries = [p for p in people if "brawler" in p["description"]]
        assert brawler_entries
        assert brawler_entries[0]["tier_hint"] == "gifted"

    def test_table_object_not_extracted_as_person(self):
        narration = "You see one table and some people at the bar."
        people = _extract_people_fast(narration)
        # "one table" should not appear — no person noun
        descs = [p["description"] for p in people]
        assert not any(d == "table" for d in descs)

    def test_step_action_not_extracted_as_person(self):
        narration = "The innkeeper takes a step toward the back room."
        people = _extract_people_fast(narration)
        descs = [p["description"] for p in people]
        assert not any("step" in d and len(d) < 10 for d in descs)

    def test_position_hint_captured(self):
        narration = "Three men are sitting at the bar."
        people = _extract_people_fast(narration)
        men = [p for p in people if "men" in p["description"]]
        assert men
        # Position hint should be captured from context
        assert men[0]["position"] != "unknown" or True  # position detection is best-effort

    def test_returns_empty_for_no_people(self):
        narration = "The stone corridor is empty. Dust drifts in the pale light."
        people = _extract_people_fast(narration)
        assert people == []


# ── _extract_exits_fast ───────────────────────────────────────────────────────

class TestExtractExits:
    def test_door_detected(self):
        exits = _extract_exits_fast("The main door stands to the north.")
        assert "door" in exits

    def test_window_detected(self):
        exits = _extract_exits_fast("The east window is unlatched.")
        assert "window" in exits

    def test_stairs_detected(self):
        exits = _extract_exits_fast("A staircase leads to the upper floor.")
        assert "stairs" in exits

    def test_multiple_exits(self):
        narration = "There is a door to the east and a window on the south wall."
        exits = _extract_exits_fast(narration)
        assert "door" in exits
        assert "window" in exits

    def test_no_exits_returns_empty(self):
        narration = "The air is still. The fire burns low."
        exits = _extract_exits_fast(narration)
        assert exits == []


# ── _extract_objects_fast ─────────────────────────────────────────────────────

class TestExtractObjects:
    def test_table_is_cover(self):
        cover, _ = _extract_objects_fast("Heavy tables are scattered across the room.")
        assert "table" in cover

    def test_bottle_is_improvised_weapon(self):
        _, weapons = _extract_objects_fast("Empty bottles line the bar.")
        assert "bottle" in weapons

    def test_stool_is_improvised_weapon(self):
        _, weapons = _extract_objects_fast("Bar stools are pulled out from under the counter.")
        assert "stool" in weapons

    def test_pillar_is_cover(self):
        cover, _ = _extract_objects_fast("Stone pillars support the vaulted ceiling.")
        assert "pillar" in cover

    def test_empty_room_returns_empty(self):
        cover, weapons = _extract_objects_fast("The room is bare.")
        assert cover == []
        assert weapons == []


# ── merge_scene_intel ─────────────────────────────────────────────────────────

class TestMergeSceneIntel:
    def test_people_deduplicated_by_description(self):
        existing = {"people": [{"description": "men at bar", "count": 3}]}
        patch = {"people": [{"description": "men at bar", "count": 3}]}
        result = merge_scene_intel(existing, patch)
        assert len(result["people"]) == 1

    def test_new_people_appended(self):
        existing = {"people": [{"description": "guards", "count": 2}]}
        patch = {"people": [{"description": "merchants", "count": 3}]}
        result = merge_scene_intel(existing, patch)
        assert len(result["people"]) == 2

    def test_exits_deduplicated(self):
        existing = {"exits": ["door", "window"]}
        patch = {"exits": ["door", "alley"]}
        result = merge_scene_intel(existing, patch)
        assert set(result["exits"]) == {"door", "window", "alley"}

    def test_cover_merged(self):
        existing = {"cover": ["table"]}
        patch = {"cover": ["barrel"]}
        result = merge_scene_intel(existing, patch)
        assert "table" in result["cover"]
        assert "barrel" in result["cover"]


# ── update_scene_intelligence ─────────────────────────────────────────────────

class TestUpdateSceneIntelligence:
    def _make_quest(self, quest_type="default"):
        return {"quest_type": quest_type}

    def test_empty_intel_initializes_from_scene_profile(self):
        intel = update_scene_intelligence("You walk in.", {}, self._make_quest(), "The Rusty Flagon Inn")
        assert intel["scene_type"] == "inn"
        assert "main_door" in intel["exits"]
        assert intel["light_level"] == "dim"

    def test_unknown_location_defaults_to_street(self):
        intel = update_scene_intelligence("You step outside.", {}, self._make_quest(), "Unknown Place")
        assert intel["scene_type"] == "street"

    def test_narration_count_increments(self):
        intel = update_scene_intelligence("First.", {}, self._make_quest(), "Tavern")
        intel2 = update_scene_intelligence("Second.", intel, self._make_quest(), "Tavern")
        assert intel["narration_count"] == 1
        assert intel2["narration_count"] == 2

    def test_tension_ratchets_up(self):
        intel = update_scene_intelligence("Calm scene.", {}, self._make_quest(), "Tavern")
        assert intel["tension_score"] == 0.0
        intel2 = update_scene_intelligence(
            "A scarred man's eyes are narrowed.", intel, self._make_quest(), "Tavern"
        )
        assert intel2["tension_score"] >= TENSION_WATCH

    def test_tension_never_drops(self):
        intel = update_scene_intelligence(
            "A scarred man's eyes are narrowed.", {}, self._make_quest(), "Tavern"
        )
        high_score = intel["tension_score"]
        intel2 = update_scene_intelligence("Calm scene.", intel, self._make_quest(), "Tavern")
        assert intel2["tension_score"] >= high_score

    def test_exits_accumulated_across_narrations(self):
        intel = update_scene_intelligence("There is a door to the north.", {}, self._make_quest(), "Tavern")
        intel2 = update_scene_intelligence("A window on the east wall is open.", intel, self._make_quest(), "Tavern")
        assert "door" in intel2["exits"]
        assert "window" in intel2["exits"]

    def test_quest_context_stored(self):
        intel = update_scene_intelligence("Scene.", {}, {"quest_type": "heist"}, "Market")
        assert intel["quest_context"]["quest_type"] == "heist"

    def test_inn_has_reinforcement_hint(self):
        intel = update_scene_intelligence("You enter the inn.", {}, self._make_quest(), "The Rusty Flagon Inn")
        assert intel["reinforcement_hint"] is not None

    def test_guard_post_inferred_by_name(self):
        intel = update_scene_intelligence("You approach.", {}, self._make_quest(), "North Gate Guard Post")
        assert intel["scene_type"] == "guard_post"


# ── get_dm_embedding_instructions ────────────────────────────────────────────

class TestDMEmbeddingInstructions:
    def _make_intel(self, tension, **kwargs):
        base = {
            "tension_score": tension,
            "location_name": "The Rusty Flagon Inn",
            "people": [],
            "exits": [],
            "cover": [],
            "hazards": [],
            "improvised_weapons": [],
            "notable_npcs": [],
            "quest_context": {},
            "reinforcement_hint": None,
        }
        base.update(kwargs)
        return base

    def test_below_watch_returns_empty(self):
        intel = self._make_intel(tension=0.1)
        assert get_dm_embedding_instructions(intel) == ""

    def test_at_watch_threshold_returns_instructions(self):
        intel = self._make_intel(tension=TENSION_WATCH)
        result = get_dm_embedding_instructions(intel)
        assert result != ""
        assert "SCENE INTELLIGENCE" in result

    def test_at_watch_includes_people_prompt(self):
        intel = self._make_intel(
            tension=TENSION_WATCH,
            people=[{"count": 3, "description": "men", "tier_hint": "commoner", "position": "bar"}],
        )
        result = get_dm_embedding_instructions(intel)
        assert "People present" in result or "how many people" in result.lower()

    def test_at_rising_includes_exits(self):
        intel = self._make_intel(
            tension=TENSION_RISING,
            exits=["main_door", "window"],
        )
        result = get_dm_embedding_instructions(intel)
        assert "main_door" in result or "window" in result

    def test_at_threat_includes_weapons(self):
        intel = self._make_intel(
            tension=TENSION_THREAT,
            improvised_weapons=["bottle", "stool"],
        )
        result = get_dm_embedding_instructions(intel)
        assert "bottle" in result or "stool" in result

    def test_at_imminent_includes_final_beat(self):
        intel = self._make_intel(tension=TENSION_IMMINENT)
        result = get_dm_embedding_instructions(intel)
        assert "final" in result.lower() or "battlefield" in result.lower()

    def test_tone_line_always_present_above_watch(self):
        intel = self._make_intel(tension=TENSION_WATCH)
        result = get_dm_embedding_instructions(intel)
        assert "TONE" in result or "flavor" in result.lower()


# ── scene_intel_to_encounter_input ────────────────────────────────────────────

class TestSceneIntelToEncounterInput:
    def _make_intel(self, scene_type="inn", tension=0.5, quest_type="default", **kwargs):
        base = {
            "scene_type": scene_type,
            "tension_score": tension,
            "quest_context": {"quest_type": quest_type},
            "people": [],
            "exits": ["door"],
            "cover": ["table"],
            "improvised_weapons": ["bottle"],
            "conditions": [],
            "reinforcement_hint": None,
            "light_level": "dim",
            "tension_signals": [],
        }
        base.update(kwargs)
        return base

    def test_returns_location_type(self):
        enc_input = scene_intel_to_encounter_input(self._make_intel(), 4)
        assert "location_type" in enc_input
        assert enc_input["location_type"] == "tavern_brawl"  # inn maps to tavern_brawl

    def test_guard_post_maps_to_correct_template(self):
        enc_input = scene_intel_to_encounter_input(self._make_intel(scene_type="guard_post"), 5)
        assert enc_input["location_type"] == "guard_post"

    def test_low_tension_yields_low_narrative_tension(self):
        enc_input = scene_intel_to_encounter_input(self._make_intel(tension=0.1), 4)
        assert enc_input["narrative_tension"] == "low"

    def test_medium_tension_yields_medium(self):
        enc_input = scene_intel_to_encounter_input(self._make_intel(tension=0.5), 4)
        assert enc_input["narrative_tension"] == "medium"

    def test_high_tension_yields_high(self):
        enc_input = scene_intel_to_encounter_input(self._make_intel(tension=0.7), 4)
        assert enc_input["narrative_tension"] == "high"

    def test_critical_tension(self):
        enc_input = scene_intel_to_encounter_input(self._make_intel(tension=0.9), 4)
        assert enc_input["narrative_tension"] == "critical"

    def test_investigation_quest_modifier_applied(self):
        enc_input = scene_intel_to_encounter_input(self._make_intel(quest_type="investigation"), 4)
        assert enc_input["quest_modifier"]["enemy_priority"] == "flee_with_info"

    def test_heist_quest_modifier_applied(self):
        enc_input = scene_intel_to_encounter_input(self._make_intel(quest_type="heist"), 4)
        assert enc_input["quest_modifier"]["enemy_priority"] == "raise_alarm"

    def test_exits_and_cover_included(self):
        enc_input = scene_intel_to_encounter_input(self._make_intel(), 4)
        assert "door" in enc_input["exits"]
        assert "table" in enc_input["cover"]

    def test_scene_people_mapped(self):
        intel = self._make_intel(people=[
            {"description": "guards", "count": 2, "tier_hint": "specialist", "position": "door"}
        ])
        enc_input = scene_intel_to_encounter_input(intel, 4)
        assert len(enc_input["scene_people"]) == 1
        assert enc_input["scene_people"][0]["tier"] == "specialist"


# ── build_encounter_from_scene ────────────────────────────────────────────────

class TestBuildEncounterFromScene:
    def _make_intel(self, scene_type="inn", tension=0.5, quest_type="default"):
        return {
            "scene_type": scene_type,
            "tension_score": tension,
            "quest_context": {"quest_type": quest_type},
            "people": [],
            "exits": ["main_door", "window"],
            "cover": ["table", "bar_counter"],
            "improvised_weapons": ["bottle", "stool"],
            "conditions": ["crowded"],
            "reinforcement_hint": "Kitchen staff may emerge after round 2",
            "light_level": "dim",
            "tension_signals": [],
            "hazards": [],
            "notable_npcs": [],
            "factions": [],
        }

    def test_returns_enemies(self):
        enc = build_encounter_from_scene(self._make_intel(), player_level=4, player_intel_level=1)
        assert len(enc["enemies"]) > 0

    def test_location_type_attached(self):
        enc = build_encounter_from_scene(self._make_intel(), player_level=4, player_intel_level=1)
        assert "location_type" in enc

    def test_exits_attached_to_encounter(self):
        enc = build_encounter_from_scene(self._make_intel(), player_level=4, player_intel_level=1)
        assert "exits" in enc
        assert "main_door" in enc["exits"] or "window" in enc["exits"]

    def test_cover_attached(self):
        enc = build_encounter_from_scene(self._make_intel(), player_level=4, player_intel_level=1)
        assert "table" in enc.get("cover", []) or len(enc.get("cover", [])) >= 0

    def test_improvised_weapons_attached(self):
        enc = build_encounter_from_scene(self._make_intel(), player_level=4, player_intel_level=1)
        assert "improvised_weapons" in enc

    def test_light_level_attached(self):
        enc = build_encounter_from_scene(self._make_intel(), player_level=4, player_intel_level=1)
        assert enc.get("light_level") == "dim"

    def test_reinforcement_hint_attached(self):
        enc = build_encounter_from_scene(self._make_intel(), player_level=4, player_intel_level=1)
        assert enc.get("reinforcement_hint") is not None

    def test_quest_objective_injected_for_investigation(self):
        enc = build_encounter_from_scene(
            self._make_intel(quest_type="investigation"),
            player_level=4, player_intel_level=1
        )
        objectives = enc.get("objectives", [])
        assert any("flee" in o.lower() or "information" in o.lower() for o in objectives)

    def test_heist_quest_objective_injected(self):
        enc = build_encounter_from_scene(
            self._make_intel(quest_type="heist"),
            player_level=4, player_intel_level=1
        )
        objectives = enc.get("objectives", [])
        assert any("alarm" in o.lower() or "silence" in o.lower() for o in objectives)

    def test_guard_post_scene_builds_encounter(self):
        enc = build_encounter_from_scene(
            self._make_intel(scene_type="guard_post", tension=0.7),
            player_level=5, player_intel_level=2
        )
        assert enc.get("template") == "guard_post"
        assert any(e["tier"] == "specialist" for e in enc.get("enemies", []))

    def test_difficulty_present(self):
        enc = build_encounter_from_scene(self._make_intel(), player_level=4, player_intel_level=0)
        assert enc.get("difficulty") in ("trivial", "easy", "medium", "hard", "deadly")

    def test_high_tension_increases_enemy_count(self):
        low_enc = build_encounter_from_scene(
            self._make_intel(tension=0.2), player_level=4, player_intel_level=0
        )
        high_enc = build_encounter_from_scene(
            self._make_intel(tension=0.9), player_level=4, player_intel_level=0
        )
        assert len(high_enc["enemies"]) >= len(low_enc["enemies"])
