"""Tests for rest_service — short rest, long rest, detection, narration."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.rest_service import (
    detect_rest_intent,
    compute_short_rest,
    compute_long_rest,
    build_rest_narration,
)


# ── detect_rest_intent ────────────────────────────────────────────────────────

class TestDetectRestIntent:
    def test_long_rest_explicit(self):
        assert detect_rest_intent("I want to take a long rest") == "long"

    def test_long_rest_sleep(self):
        assert detect_rest_intent("I sleep through the night") == "long"

    def test_long_rest_make_camp(self):
        assert detect_rest_intent("We make camp for the night") == "long"

    def test_long_rest_until_morning(self):
        assert detect_rest_intent("Rest until morning") == "long"

    def test_short_rest_explicit(self):
        assert detect_rest_intent("I take a short rest") == "short"

    def test_short_rest_catch_breath(self):
        assert detect_rest_intent("Let me catch my breath") == "short"

    def test_short_rest_bind_wounds(self):
        assert detect_rest_intent("I bind my wounds") == "short"

    def test_no_rest_intent(self):
        assert detect_rest_intent("I attack the goblin") is None

    def test_no_rest_intent_exploration(self):
        assert detect_rest_intent("I walk to the market") is None

    def test_long_rest_takes_priority_over_short(self):
        # "rest through the night" is long, not short
        assert detect_rest_intent("I rest through the night") == "long"

    def test_case_insensitive(self):
        assert detect_rest_intent("LONG REST") == "long"
        assert detect_rest_intent("Short Rest") == "short"


# ── compute_short_rest ────────────────────────────────────────────────────────

def make_char(cls="fighter", level=3, hp=5, max_hp=10, con=12, conditions=None, spell_slots=None, spell_slots_max=None,
              hit_dice_remaining=None, hit_dice_max=None):
    char = {
        "class": cls,
        "level": level,
        "hp": hp,
        "max_hp": max_hp,
        "abilities": {"str": 10, "dex": 10, "con": con, "int": 10, "wis": 10, "cha": 10},
        "conditions": conditions or [],
        "spell_slots": spell_slots or {},
        "spell_slots_max": spell_slots_max or {},
    }
    if hit_dice_remaining is not None:
        char["hit_dice_remaining"] = hit_dice_remaining
    if hit_dice_max is not None:
        char["hit_dice_max"] = hit_dice_max
    return char


class TestComputeShortRest:
    def test_hp_increases(self):
        char = make_char(hp=5, max_hp=10)
        result = compute_short_rest(char)
        assert result["hp"] >= 5

    def test_hp_capped_at_max(self):
        char = make_char(hp=9, max_hp=10, con=14)
        result = compute_short_rest(char)
        assert result["hp"] <= 10

    def test_hp_not_decreased(self):
        char = make_char(hp=10, max_hp=10)
        result = compute_short_rest(char)
        assert result["hp"] == 10  # already full

    def test_rest_type_is_short(self):
        result = compute_short_rest(make_char())
        assert result["rest_type"] == "short"

    def test_hit_die_roll_is_valid(self):
        char = make_char(cls="fighter")  # d10
        result = compute_short_rest(char)
        assert 1 <= result["hit_die_roll"] <= 10
        assert result["hit_die_type"] == 10

    def test_wizard_uses_d6(self):
        char = make_char(cls="wizard")
        result = compute_short_rest(char)
        assert result["hit_die_type"] == 6
        assert 1 <= result["hit_die_roll"] <= 6

    def test_barbarian_uses_d12(self):
        char = make_char(cls="barbarian")
        result = compute_short_rest(char)
        assert result["hit_die_type"] == 12

    def test_hp_gained_is_accurate(self):
        char = make_char(hp=5, max_hp=10)
        result = compute_short_rest(char)
        assert result["hp"] == 5 + result["hp_gained"]

    def test_warlock_recovers_slots(self):
        char = make_char(cls="warlock", level=3, spell_slots={"2": 0})
        result = compute_short_rest(char)
        # Warlock level 3 has 2 pact slots at level 2
        assert result["spell_slots"].get("2", 0) == 2
        assert "2" in result["slots_recovered"]

    def test_fighter_does_not_recover_slots(self):
        char = make_char(cls="fighter", spell_slots={"1": 0})
        result = compute_short_rest(char)
        # Fighter has no spell slots — existing empty slot stays empty
        assert result["slots_recovered"] == {}

    def test_frightened_cleared_on_short_rest(self):
        char = make_char(conditions=["frightened", "poisoned"])
        result = compute_short_rest(char)
        assert "frightened" not in result["conditions"]
        assert "poisoned" in result["conditions"]  # persists

    def test_conditions_cleared_list(self):
        char = make_char(conditions=["frightened"])
        result = compute_short_rest(char)
        assert "frightened" in result["conditions_cleared"]

    def test_con_mod_applied(self):
        char = make_char(hp=1, max_hp=20, con=18)  # +4 CON mod
        # With +4 CON even a roll of 1 gives 5 HP gain minimum
        result = compute_short_rest(char)
        assert result["hp_gained"] >= 5


# ── compute_long_rest ─────────────────────────────────────────────────────────

class TestComputeLongRest:
    def test_hp_fully_restored(self):
        char = make_char(hp=3, max_hp=10)
        result = compute_long_rest(char)
        assert result["hp"] == 10

    def test_hp_gained_matches(self):
        char = make_char(hp=3, max_hp=10)
        result = compute_long_rest(char)
        assert result["hp_gained"] == 7

    def test_hp_gained_zero_when_full(self):
        char = make_char(hp=10, max_hp=10)
        result = compute_long_rest(char)
        assert result["hp_gained"] == 0
        assert result["hp"] == 10

    def test_rest_type_is_long(self):
        result = compute_long_rest(make_char())
        assert result["rest_type"] == "long"

    def test_wizard_slots_restored(self):
        char = make_char(cls="wizard", level=3, spell_slots={"1": 0, "2": 0})
        result = compute_long_rest(char)
        # Wizard level 3: 4x 1st level, 2x 2nd level
        assert result["spell_slots"]["1"] == 4
        assert result["spell_slots"]["2"] == 2

    def test_cleric_slots_restored(self):
        char = make_char(cls="cleric", level=2, spell_slots={"1": 0})
        result = compute_long_rest(char)
        assert result["spell_slots"]["1"] == 3  # Level 2 cleric has 3x 1st level

    def test_warlock_slots_restored(self):
        char = make_char(cls="warlock", level=5, spell_slots={"3": 0})
        result = compute_long_rest(char)
        assert result["spell_slots"]["3"] == 2  # Warlock level 5: 2x 3rd level pact

    def test_fighter_no_slots_on_long_rest(self):
        char = make_char(cls="fighter", level=3)
        result = compute_long_rest(char)
        assert result["spell_slots"] == {}

    def test_spell_slots_max_set_on_long_rest(self):
        char = make_char(cls="wizard", level=3)
        result = compute_long_rest(char)
        assert "spell_slots_max" in result
        assert result["spell_slots_max"]["1"] == 4

    def test_poisoned_cleared_on_long_rest(self):
        char = make_char(conditions=["poisoned", "frightened", "blinded"])
        result = compute_long_rest(char)
        assert "poisoned" not in result["conditions"]
        assert "frightened" not in result["conditions"]

    def test_curse_not_cleared_on_long_rest(self):
        char = make_char(conditions=["cursed", "poisoned"])
        result = compute_long_rest(char)
        assert "cursed" in result["conditions"]
        assert "poisoned" not in result["conditions"]

    def test_cleared_conditions_listed(self):
        char = make_char(conditions=["poisoned"])
        result = compute_long_rest(char)
        assert "poisoned" in result["conditions_cleared"]

    def test_partial_slot_recovery(self):
        char = make_char(cls="wizard", level=3, spell_slots={"1": 2, "2": 2})
        result = compute_long_rest(char)
        # Only slots BELOW max are counted as recovered
        assert result["slots_recovered"].get("1", 0) == 2  # was 2, max 4
        assert result["slots_recovered"].get("2", 0) == 0  # was 2, max 2 (already full)


# ── build_rest_narration ──────────────────────────────────────────────────────

class TestBuildRestNarration:
    def _short_result(self, hp_gained=3, roll=3, die=8, con_mod=0, slots=None, cleared=None):
        return {
            "rest_type": "short", "hp": 8, "hp_gained": hp_gained,
            "hit_die_roll": roll, "hit_die_type": die, "con_mod": con_mod,
            "slots_recovered": slots or {}, "conditions_cleared": cleared or [],
        }

    def _long_result(self, hp_gained=7, hp=10, slots=None, cleared=None):
        return {
            "rest_type": "long", "hp": hp, "hp_gained": hp_gained,
            "slots_recovered": slots or {}, "conditions_cleared": cleared or [],
        }

    def test_short_rest_mentions_hp(self):
        result = _n = build_rest_narration("short", self._short_result(hp_gained=3))
        assert "3" in result or "hit point" in result

    def test_short_rest_mentions_die(self):
        result = build_rest_narration("short", self._short_result(roll=5, die=8))
        assert "d8" in result or "5" in result

    def test_short_rest_zero_gain_handled(self):
        result = build_rest_narration("short", self._short_result(hp_gained=0))
        assert "rest" in result.lower()

    def test_long_rest_mentions_night(self):
        result = build_rest_narration("long", self._long_result())
        assert "night" in result.lower() or "rest" in result.lower()

    def test_long_rest_mentions_hp_gained(self):
        result = build_rest_narration("long", self._long_result(hp_gained=7))
        assert "7" in result

    def test_long_rest_mentions_spell_slots(self):
        result = build_rest_narration("long", self._long_result(slots={"1": 2}))
        assert "spell slot" in result.lower() or "2" in result

    def test_location_included_when_provided(self):
        result = build_rest_narration("long", self._long_result(), location="The Rusty Flagon Inn")
        assert "Rusty Flagon" in result

    def test_no_location_for_unknown(self):
        result = build_rest_narration("short", self._short_result(), location="Unknown")
        assert "Unknown" not in result


# ── hit dice tracking ─────────────────────────────────────────────────────────

class TestHitDiceTracking:
    def test_short_rest_decrements_hit_dice(self):
        char = make_char(level=3, hit_dice_remaining=3, hit_dice_max=3)
        result = compute_short_rest(char)
        assert result["hit_dice_remaining"] == 2

    def test_short_rest_no_dice_available(self):
        char = make_char(level=3, hit_dice_remaining=0, hit_dice_max=3)
        result = compute_short_rest(char)
        assert result["no_hit_dice"] is True
        assert result["hp_gained"] == 0
        assert result["hit_dice_remaining"] == 0

    def test_short_rest_no_dice_no_hp_recovery(self):
        char = make_char(hp=5, max_hp=10, hit_dice_remaining=0, hit_dice_max=3)
        result = compute_short_rest(char)
        assert result["hp"] == 5  # no change

    def test_short_rest_with_last_die(self):
        char = make_char(level=2, hit_dice_remaining=1, hit_dice_max=2)
        result = compute_short_rest(char)
        assert result["hit_dice_remaining"] == 0
        assert result["no_hit_dice"] is False

    def test_short_rest_result_includes_hit_dice_max(self):
        char = make_char(level=4, hit_dice_remaining=2, hit_dice_max=4)
        result = compute_short_rest(char)
        assert result["hit_dice_max"] == 4

    def test_long_rest_recovers_half_level(self):
        # Level 4: recover max(1, 4//2) = 2 dice
        char = make_char(level=4, hit_dice_remaining=0, hit_dice_max=4)
        result = compute_long_rest(char)
        assert result["hit_dice_remaining"] == 2
        assert result["hit_dice_recovered"] == 2

    def test_long_rest_level_1_recovers_at_least_1(self):
        # Level 1: max(1, 1//2) = max(1, 0) = 1
        char = make_char(level=1, hit_dice_remaining=0, hit_dice_max=1)
        result = compute_long_rest(char)
        assert result["hit_dice_remaining"] == 1
        assert result["hit_dice_recovered"] == 1

    def test_long_rest_level_3_recovers_1(self):
        # Level 3: max(1, 3//2) = max(1, 1) = 1
        char = make_char(level=3, hit_dice_remaining=1, hit_dice_max=3)
        result = compute_long_rest(char)
        assert result["hit_dice_remaining"] == 2
        assert result["hit_dice_recovered"] == 1

    def test_long_rest_does_not_exceed_max(self):
        char = make_char(level=4, hit_dice_remaining=3, hit_dice_max=4)
        result = compute_long_rest(char)
        assert result["hit_dice_remaining"] <= 4

    def test_long_rest_already_full_dice(self):
        char = make_char(level=4, hit_dice_remaining=4, hit_dice_max=4)
        result = compute_long_rest(char)
        assert result["hit_dice_remaining"] == 4
        assert result["hit_dice_recovered"] == 0

    def test_default_remaining_equals_level(self):
        # Character without hit_dice_remaining tracked defaults to level
        char = make_char(level=3)  # no hit_dice_remaining key
        result = compute_short_rest(char)
        # Defaults to level=3, so spending 1 gives 2
        assert result["hit_dice_remaining"] == 2

    def test_narration_shows_remaining_dice(self):
        char = make_char(level=3, hit_dice_remaining=3, hit_dice_max=3)
        result = compute_short_rest(char)
        narration = build_rest_narration("short", result)
        assert "2/3" in narration  # decremented from 3 to 2

    def test_narration_no_dice_message(self):
        char = make_char(level=3, hit_dice_remaining=0, hit_dice_max=3)
        result = compute_short_rest(char)
        narration = build_rest_narration("short", result)
        assert "no hit dice" in narration.lower() or "long rest" in narration.lower()

    def test_narration_long_rest_shows_dice_recovered(self):
        char = make_char(level=4, hit_dice_remaining=0, hit_dice_max=4)
        result = compute_long_rest(char)
        narration = build_rest_narration("long", result)
        assert "hit di" in narration.lower()  # "hit die" or "hit dice"


# ── short rest limit (D&D 5e: 2 per long rest) ───────────────────────────────

class TestShortRestLimit:
    def test_first_short_rest_allowed(self):
        char = make_char()
        result = compute_short_rest(char)
        assert result.get("no_short_rests") is False
        assert result["short_rests_taken"] == 1
        assert result["short_rests_remaining"] == 1

    def test_second_short_rest_allowed(self):
        char = make_char()
        char["short_rests_taken"] = 1
        result = compute_short_rest(char)
        assert result.get("no_short_rests") is False
        assert result["short_rests_taken"] == 2
        assert result["short_rests_remaining"] == 0

    def test_third_short_rest_blocked(self):
        char = make_char()
        char["short_rests_taken"] = 2
        result = compute_short_rest(char)
        assert result["no_short_rests"] is True
        assert result["hp_gained"] == 0
        assert result["short_rests_remaining"] == 0

    def test_long_rest_resets_counter(self):
        char = make_char()
        char["short_rests_taken"] = 2
        result = compute_long_rest(char)
        assert result["short_rests_taken"] == 0
        assert result["short_rests_remaining"] == 2

    def test_no_short_rests_result_includes_all_fields(self):
        char = make_char()
        char["short_rests_taken"] = 2
        result = compute_short_rest(char)
        for key in ("rest_type", "no_short_rests", "hp", "hp_gained", "hit_die_type",
                    "con_mod", "hit_dice_remaining", "short_rests_taken", "spell_slots"):
            assert key in result, f"missing key: {key}"
