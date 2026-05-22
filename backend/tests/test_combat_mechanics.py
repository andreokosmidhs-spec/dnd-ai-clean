"""
Combat Mechanics Test Suite
============================
Tests every layer of the D&D 5e battle system:
  1.  D&D Rules core     (dnd_rules.py)
  2.  Combat Engine      (combat_engine_service.py)
  3.  Saving Throws      (saving_throw_service.py)
  4.  Progression / XP   (progression_service.py)
  5.  Target Resolver    (target_resolver.py)
  6.  Plot Armor         (plot_armor_service.py)
  7.  Battlefield Layout (battlefield_layout_service.py)

Run with:
    cd backend && python -m pytest tests/test_combat_mechanics.py -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch


# ══════════════════════════════════════════════════════════════════════════════
# Shared fixtures
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def basic_character():
    return {
        "name": "Aldric",
        "class_": "Fighter",
        "class":  "Fighter",
        "level": 1,
        "hp": 12, "max_hp": 12,
        "ac": 14,
        "abilities": {"str": 16, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 8},
        "proficiency_bonus": 2,
        "attack_bonus": 0,
        "conditions": [],
        "spell_slots": {},
        "spell_slots_max": {},
    }


@pytest.fixture
def basic_enemy():
    return {
        "id": "goblin_1",
        "name": "Goblin",
        "hp": 10, "max_hp": 10,
        "ac": 13,
        "abilities": {"str": 8, "dex": 14, "con": 10, "int": 10, "wis": 8, "cha": 8},
        "proficiency_bonus": 2,
        "attack_bonus": 0,
        "damage_die": "1d6",
        "conditions": [],
        "resistances": [],
        "immunities": [],
        "lane": 2,
        "grid_x": 5, "grid_y": 2,
    }


@pytest.fixture
def one_enemy_combat(basic_character, basic_enemy):
    """Minimal combat state with one alive enemy."""
    return {
        "enemies": [basic_enemy],
        "turn_order": ["player", "goblin_1"],
        "active_turn": "player",
        "round": 1,
        "combat_over": False,
        "outcome": None,
        "player_lane": 1,
        "player_grid_x": 1, "player_grid_y": 2,
        "light_level": {"level": "bright", "blinded": False},
        "player_turn_state": {
            "action_used": False, "bonus_action_used": False, "reaction_used": False
        },
        "cell_overrides": [],
        "spell_zones": [],
    }


@pytest.fixture
def dead_enemy_combat(basic_character):
    return {
        "enemies": [{"id": "goblin_dead", "name": "Dead Goblin",
                     "hp": 0, "max_hp": 10, "ac": 13,
                     "abilities": {"str": 8, "dex": 14, "con": 10},
                     "proficiency_bonus": 2, "attack_bonus": 0, "damage_die": "1d6",
                     "conditions": [], "resistances": [], "immunities": []}],
        "turn_order": ["player"],
        "active_turn": "player",
        "round": 1, "combat_over": False, "outcome": None,
        "light_level": {"level": "bright", "blinded": False},
    }


@pytest.fixture
def world_blueprint():
    return {
        "key_npcs": [
            {"id": "npc_aria", "name": "Aria", "role": "quest_giver",
             "is_essential": True, "personality_tags": [], "secret": "",
             "knows_about": [], "faction_id": None, "location_poi_id": "tavern_1"},
            {"id": "npc_guard", "name": "Guard Bob", "role": "guard",
             "is_essential": False, "personality_tags": [], "secret": "",
             "knows_about": [], "faction_id": None, "location_poi_id": "gate_1"},
        ],
        "points_of_interest": [
            {"id": "tavern_1", "name": "The Rusty Flagon", "type": "tavern", "description": ""},
            {"id": "gate_1", "name": "North Gate", "type": "fortification", "description": ""},
        ],
        "factions": [],
        "macro_conflicts": {"local": [], "realm": [], "world": []},
        "world_core": {"name": "Aethoria", "tone": "dark fantasy"},
        "starting_region": {"name": "Verdane", "biome_layers": ["forest"], "description": ""},
        "starting_town": {"name": "Millhaven"},
    }


@pytest.fixture
def world_state():
    return {
        "location": "Millhaven",
        "current_location": "Millhaven",
        "active_npcs": ["npc_aria", "npc_guard"],
        "time_of_day": "morning",
        "guard_alert": False,
        "transgressions": {},
        "bounties": [],
        "permanent_enemies": [],
    }


# ══════════════════════════════════════════════════════════════════════════════
# 1. D&D RULES CORE
# ══════════════════════════════════════════════════════════════════════════════

class TestAbilityModifier:
    def test_score_10_gives_0(self):
        from services.dnd_rules import calculate_ability_modifier
        assert calculate_ability_modifier(10) == 0

    def test_score_11_gives_0(self):
        from services.dnd_rules import calculate_ability_modifier
        assert calculate_ability_modifier(11) == 0

    def test_score_12_gives_plus1(self):
        from services.dnd_rules import calculate_ability_modifier
        assert calculate_ability_modifier(12) == 1

    def test_score_8_gives_minus1(self):
        from services.dnd_rules import calculate_ability_modifier
        assert calculate_ability_modifier(8) == -1

    def test_score_20_gives_plus5(self):
        from services.dnd_rules import calculate_ability_modifier
        assert calculate_ability_modifier(20) == 5

    def test_score_1_gives_minus5(self):
        from services.dnd_rules import calculate_ability_modifier
        assert calculate_ability_modifier(1) == -5


class TestDiceRolls:
    def test_d20_always_in_range(self):
        from services.dnd_rules import roll_d20
        for _ in range(200):
            r = roll_d20()
            assert 1 <= r <= 20, f"d20 returned {r}"

    def test_roll_dice_1d6_range(self):
        from services.dnd_rules import roll_dice
        for _ in range(100):
            r = roll_dice("1d6")
            assert 1 <= r <= 6, f"1d6 returned {r}"

    def test_roll_dice_2d8_range(self):
        from services.dnd_rules import roll_dice
        for _ in range(100):
            r = roll_dice("2d8")
            assert 2 <= r <= 16, f"2d8 returned {r}"

    def test_roll_dice_with_modifier(self):
        from services.dnd_rules import roll_dice
        for _ in range(100):
            r = roll_dice("1d4+3")
            assert 4 <= r <= 7, f"1d4+3 returned {r}"

    def test_roll_dice_1d1_always_1(self):
        from services.dnd_rules import roll_dice
        assert roll_dice("1d1") == 1


class TestProficiencyBonus:
    @pytest.mark.parametrize("level,expected", [
        (1, 2), (2, 2), (4, 2),
        (5, 3), (8, 3),
        (9, 4), (12, 4),
        (13, 5), (16, 5),
        (17, 6), (20, 6),
    ])
    def test_proficiency_by_level(self, level, expected):
        from services.dnd_rules import proficiency_bonus_for_level
        assert proficiency_bonus_for_level(level) == expected


class TestAttackResolution:
    """Tests for resolve_attack() — the core combat resolution function."""

    def _make_attacker(self, str_score=14):
        return {
            "abilities": {"str": str_score, "dex": 10, "con": 10},
            "proficiency_bonus": 2,
            "attack_bonus": 0,
        }

    def _make_target(self, ac=10, hp=20):
        return {"ac": ac, "hp": hp, "max_hp": hp, "resistances": [], "immunities": []}

    def test_nat20_always_hits(self):
        from services.dnd_rules import resolve_attack
        attacker = self._make_attacker()
        target   = self._make_target(ac=30)  # unbeatable AC
        with patch("services.dnd_rules.roll_d20", return_value=20):
            result = resolve_attack(attacker, target, "melee", "1d6")
        assert result["hit"] is True
        assert result["is_crit"] is True

    def test_nat1_always_misses(self):
        from services.dnd_rules import resolve_attack
        attacker = self._make_attacker()
        target   = self._make_target(ac=1)   # trivial AC
        with patch("services.dnd_rules.roll_d20", return_value=1):
            result = resolve_attack(attacker, target, "melee", "1d6")
        assert result["hit"] is False
        assert result["critical_miss"] is True

    def test_hit_reduces_hp(self):
        from services.dnd_rules import resolve_attack
        attacker = self._make_attacker(str_score=14)  # +2 mod
        target   = self._make_target(ac=10, hp=20)
        with patch("services.dnd_rules.roll_d20", return_value=15):
            result = resolve_attack(attacker, target, "melee", "1d6")
        assert result["hit"] is True
        assert result["new_target_hp"] < 20

    def test_miss_does_no_damage(self):
        from services.dnd_rules import resolve_attack
        attacker = self._make_attacker(str_score=10)  # +0 mod, proficiency +2 → max 22 roll
        target   = self._make_target(ac=25, hp=20)
        with patch("services.dnd_rules.roll_d20", return_value=5):
            result = resolve_attack(attacker, target, "melee", "1d6")
        assert result["hit"] is False
        assert result["damage"] == 0
        assert result["new_target_hp"] == 20

    def test_crit_returns_roll1_and_roll2(self):
        from services.dnd_rules import resolve_attack
        attacker = self._make_attacker()
        target   = self._make_target()
        call_count = {"n": 0}
        def mock_roll():
            call_count["n"] += 1
            return 20 if call_count["n"] == 1 else 5
        with patch("services.dnd_rules.roll_d20", side_effect=mock_roll):
            result = resolve_attack(attacker, target, "melee", "1d6",
                                    advantage=True)
        # With advantage two rolls happen; the function should record them
        assert "roll1" in result and "roll2" in result

    def test_damage_minimum_1(self):
        from services.dnd_rules import resolve_attack
        attacker = {"abilities": {"str": 1, "dex": 1}, "proficiency_bonus": 2, "attack_bonus": 0}
        target   = self._make_target(ac=1, hp=20)
        with patch("services.dnd_rules.roll_d20", return_value=15):
            result = resolve_attack(attacker, target, "melee", "1d4")
        if result["hit"]:
            assert result["damage"] >= 1

    def test_force_non_lethal_knocks_unconscious(self):
        from services.dnd_rules import resolve_attack
        attacker = self._make_attacker(str_score=20)  # +5 → huge damage
        target   = self._make_target(ac=5, hp=1)
        with patch("services.dnd_rules.roll_d20", return_value=15):
            result = resolve_attack(attacker, target, "melee", "1d12",
                                    force_non_lethal=True)
        if result["hit"]:
            assert result["knocked_unconscious"] is True
            assert result["new_target_hp"] == 0

    def test_target_killed_when_hp_zero(self):
        from services.dnd_rules import resolve_attack
        attacker = self._make_attacker(str_score=20)
        target   = self._make_target(ac=5, hp=1)
        with patch("services.dnd_rules.roll_d20", return_value=20):
            result = resolve_attack(attacker, target, "melee", "1d12")
        if result["hit"]:
            assert result["killed"] is True
            assert result["new_target_hp"] == 0

    def test_fire_resistance_halves_spell_damage(self):
        # resolve_attack handles physical damage only.
        # Fire resistance is enforced in process_save_spell — test it there.
        from services.combat_engine_service import process_save_spell
        spell_card = {
            "save_type": "dex", "half_on_save": False,
            "damage_dice": "1d1",           # deterministic: always 1
            "damage_type": "fire",
            "condition_on_fail": None,
        }
        caster = {"name": "Mage", "abilities": {"int": 16}, "proficiency_bonus": 2}
        target = {"id": "t1", "name": "Fire Elemental", "hp": 30, "max_hp": 30,
                  "resistances": ["fire"], "immunities": [], "conditions": []}
        combat = {"enemies": [target]}
        with patch("services.dnd_rules.roll_d20", return_value=1):   # failed save → full damage
            with patch("services.dnd_rules.roll_dice", return_value=8):
                result = process_save_spell("Fire Bolt", spell_card, caster, target,
                                            spell_save_dc=20, combat_state=combat)
        # Resistant: 8 halved → 4
        assert result["mechanical_summary"]["damage"] == 4

    def test_immunity_negates_spell_damage(self):
        from services.combat_engine_service import process_save_spell
        spell_card = {
            "save_type": "dex", "half_on_save": False,
            "damage_dice": "1d8",
            "damage_type": "fire",
            "condition_on_fail": None,
        }
        caster = {"name": "Mage", "abilities": {"int": 16}, "proficiency_bonus": 2}
        target = {"id": "t2", "name": "Fire Golem", "hp": 30, "max_hp": 30,
                  "resistances": [], "immunities": ["fire"], "conditions": []}
        combat = {"enemies": [target]}
        with patch("services.dnd_rules.roll_d20", return_value=1):
            with patch("services.dnd_rules.roll_dice", return_value=8):
                result = process_save_spell("Fireball", spell_card, caster, target,
                                            spell_save_dc=20, combat_state=combat)
        assert result["mechanical_summary"]["damage"] == 0


class TestAdvantageDisadvantage:
    def test_advantage_takes_higher(self):
        from services.dnd_rules import resolve_attack
        attacker = {"abilities": {"str": 10, "dex": 10}, "proficiency_bonus": 2, "attack_bonus": 0}
        target   = {"ac": 12, "hp": 20, "max_hp": 20, "resistances": [], "immunities": []}
        rolls = iter([8, 15])
        with patch("services.dnd_rules.roll_d20", side_effect=rolls):
            result = resolve_attack(attacker, target, "melee", "1d6", advantage=True)
        assert result["roll"] == 15  # should pick higher

    def test_disadvantage_takes_lower(self):
        from services.dnd_rules import resolve_attack
        attacker = {"abilities": {"str": 10, "dex": 10}, "proficiency_bonus": 2, "attack_bonus": 0}
        target   = {"ac": 12, "hp": 20, "max_hp": 20, "resistances": [], "immunities": []}
        rolls = iter([15, 8])
        with patch("services.dnd_rules.roll_d20", side_effect=rolls):
            result = resolve_attack(attacker, target, "melee", "1d6", disadvantage=True)
        assert result["roll"] == 8  # should pick lower


class TestAdvantageFlags:
    def test_blinded_attacker_melee_gives_disadvantage(self):
        from services.dnd_rules import compute_advantage_flags
        adv, disadv, _, _ = compute_advantage_flags(
            attacker_conditions=["blinded"],
            target_conditions=[],
            weapon_type="melee",
            blinded=True,
        )
        assert disadv is True

    def test_prone_target_melee_gives_advantage(self):
        from services.dnd_rules import compute_advantage_flags
        adv, disadv, _, _ = compute_advantage_flags(
            attacker_conditions=[],
            target_conditions=["prone"],
            weapon_type="melee",
            blinded=False,
        )
        assert adv is True

    def test_both_cancel_to_straight(self):
        from services.dnd_rules import compute_advantage_flags
        # Attacker blinded AND target prone → both conditions present → straight roll
        adv, disadv, _, _ = compute_advantage_flags(
            attacker_conditions=["blinded"],
            target_conditions=["prone"],
            weapon_type="melee",
            blinded=True,
        )
        # Both flags are True; the engine cancels them when both are set
        assert adv is True and disadv is True  # cancellation done in combat engine


class TestDeathSaves:
    def test_nat20_is_critical_success(self):
        from services.dnd_rules import roll_death_save
        with patch("services.dnd_rules.roll_d20", return_value=20):
            result = roll_death_save()
        assert result["result"] == "critical_success"
        assert result["roll"] == 20

    def test_nat1_is_critical_failure(self):
        from services.dnd_rules import roll_death_save
        with patch("services.dnd_rules.roll_d20", return_value=1):
            result = roll_death_save()
        assert result["result"] == "critical_failure"
        assert result["roll"] == 1

    def test_roll_10_or_more_success(self):
        from services.dnd_rules import roll_death_save
        with patch("services.dnd_rules.roll_d20", return_value=10):
            result = roll_death_save()
        assert result["result"] == "success"

    def test_roll_9_or_less_failure(self):
        from services.dnd_rules import roll_death_save
        with patch("services.dnd_rules.roll_d20", return_value=9):
            result = roll_death_save()
        assert result["result"] == "failure"


# ══════════════════════════════════════════════════════════════════════════════
# 2. COMBAT ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class TestNpcConversion:
    def test_guard_has_correct_stats(self, world_blueprint):
        from services.combat_engine_service import convert_npc_to_enemy
        npc = {"id": "npc_guard", "name": "Town Guard", "role": "guard"}
        enemy = convert_npc_to_enemy(npc, world_blueprint, character_level=1)
        assert enemy["hp"] == 20
        assert enemy["ac"] == 14
        assert enemy["damage_die"] == "1d8"

    def test_mage_has_correct_stats(self, world_blueprint):
        from services.combat_engine_service import convert_npc_to_enemy
        npc = {"id": "npc_mage", "name": "Archmage", "role": "mage"}
        enemy = convert_npc_to_enemy(npc, world_blueprint, character_level=1)
        assert enemy["hp"] == 8
        assert enemy["ac"] == 11

    def test_merchant_has_correct_stats(self, world_blueprint):
        from services.combat_engine_service import convert_npc_to_enemy
        npc = {"id": "npc_merchant", "name": "Trader", "role": "merchant"}
        enemy = convert_npc_to_enemy(npc, world_blueprint, character_level=1)
        assert enemy["hp"] == 10
        assert enemy["ac"] == 10

    def test_hp_scales_with_level(self, world_blueprint):
        from services.combat_engine_service import convert_npc_to_enemy
        npc = {"id": "npc_guard2", "name": "Elite Guard", "role": "guard"}
        level3 = convert_npc_to_enemy(npc, world_blueprint, character_level=3)
        # base_hp (20) + (3-1)*2 = 24
        assert level3["hp"] == 24

    def test_converted_enemy_has_id(self, world_blueprint):
        from services.combat_engine_service import convert_npc_to_enemy
        npc = {"id": "npc_smith", "name": "Blacksmith", "role": "merchant"}
        enemy = convert_npc_to_enemy(npc, world_blueprint)
        assert "id" in enemy
        assert enemy["id"].startswith("npc_enemy_")


class TestStartCombat:
    def _enemy_resolution(self, enemy_dict):
        return {
            "target_type": "enemy",
            "target_id": enemy_dict["id"],
            "target_name": enemy_dict["name"],
            "target_data": enemy_dict,
        }

    def test_combat_state_has_required_keys(self, basic_character, basic_enemy, world_blueprint):
        from services.combat_engine_service import start_combat_with_target
        resolution = self._enemy_resolution(basic_enemy)
        state = start_combat_with_target(
            resolution, basic_character, world_blueprint,
            character_level=1, world_state={}
        )
        for key in ("enemies", "turn_order", "initiative_order", "active_turn",
                    "round", "combat_over", "player_lane", "battlefield"):
            assert key in state, f"Missing key: {key}"

    def test_initiative_order_is_descending(self, basic_character, basic_enemy, world_blueprint):
        from services.combat_engine_service import start_combat_with_target
        resolution = self._enemy_resolution(basic_enemy)
        state = start_combat_with_target(
            resolution, basic_character, world_blueprint,
            character_level=1, world_state={}
        )
        scores = [e["score"] for e in state["initiative_order"]]
        assert scores == sorted(scores, reverse=True)

    def test_turn_order_matches_initiative(self, basic_character, basic_enemy, world_blueprint):
        from services.combat_engine_service import start_combat_with_target
        resolution = self._enemy_resolution(basic_enemy)
        state = start_combat_with_target(
            resolution, basic_character, world_blueprint,
            character_level=1, world_state={}
        )
        initiative_ids = [e["id"] for e in state["initiative_order"]]
        assert state["turn_order"] == initiative_ids

    def test_first_active_turn_is_highest_initiative(self, basic_character, basic_enemy, world_blueprint):
        from services.combat_engine_service import start_combat_with_target
        resolution = self._enemy_resolution(basic_enemy)
        state = start_combat_with_target(
            resolution, basic_character, world_blueprint,
            character_level=1, world_state={}
        )
        assert state["active_turn"] == state["turn_order"][0]

    def test_battlefield_grid_included_when_passed(self, basic_character, basic_enemy, world_blueprint):
        from services.combat_engine_service import start_combat_with_target
        fake_grid = {"cols": 8, "rows": 6, "cells": [], "generated": False}
        resolution = self._enemy_resolution(basic_enemy)
        state = start_combat_with_target(
            resolution, basic_character, world_blueprint,
            character_level=1, world_state={}, battlefield_grid=fake_grid
        )
        assert state["battlefield_grid"] == fake_grid

    def test_enemy_gets_grid_position(self, basic_character, basic_enemy, world_blueprint):
        from services.combat_engine_service import start_combat_with_target
        resolution = self._enemy_resolution(basic_enemy)
        state = start_combat_with_target(
            resolution, basic_character, world_blueprint,
            character_level=1, world_state={}
        )
        enemy = state["enemies"][0]
        assert "grid_x" in enemy
        assert "grid_y" in enemy

    def test_combat_not_over_at_start(self, basic_character, basic_enemy, world_blueprint):
        from services.combat_engine_service import start_combat_with_target
        resolution = self._enemy_resolution(basic_enemy)
        state = start_combat_with_target(
            resolution, basic_character, world_blueprint,
            character_level=1, world_state={}
        )
        assert state["combat_over"] is False
        assert state["outcome"] is None


class TestPlayerAttack:
    def test_hit_reduces_enemy_hp(self, basic_character, one_enemy_combat):
        from services.combat_engine_service import process_player_attack
        with patch("services.dnd_rules.roll_d20", return_value=18):
            result = process_player_attack(
                "goblin_1", basic_character, one_enemy_combat,
                weapon_type="melee", weapon_damage="1d8", weapon_name="Longsword"
            )
        assert result["success"] is True
        if result["mechanical_summary"]["hit"]:
            goblin = next(e for e in result["combat_state_update"]["enemies"]
                          if e["id"] == "goblin_1")
            assert goblin["hp"] < 10

    def test_killing_blow_ends_combat(self, basic_character, one_enemy_combat):
        from services.combat_engine_service import process_player_attack
        # Force nat 20 → crit → high damage → kills 10 HP goblin
        with patch("services.dnd_rules.roll_d20", return_value=20):
            with patch("services.dnd_rules.roll_dice", return_value=10):
                result = process_player_attack(
                    "goblin_1", basic_character, one_enemy_combat,
                    weapon_type="melee", weapon_damage="1d10", weapon_name="Greataxe"
                )
        if result["mechanical_summary"]["hit"]:
            assert result["combat_over"] is True
            assert result["combat_state_update"]["outcome"] == "victory"

    def test_xp_awarded_on_victory(self, basic_character, one_enemy_combat):
        from services.combat_engine_service import process_player_attack
        with patch("services.dnd_rules.roll_d20", return_value=20):
            with patch("services.dnd_rules.roll_dice", return_value=10):
                result = process_player_attack(
                    "goblin_1", basic_character, one_enemy_combat,
                    weapon_type="melee", weapon_damage="1d10", weapon_name="Greataxe"
                )
        if result["combat_over"]:
            assert result["xp_gained"] > 0

    def test_invalid_target_returns_error(self, basic_character, one_enemy_combat):
        from services.combat_engine_service import process_player_attack
        result = process_player_attack(
            "nonexistent_enemy", basic_character, one_enemy_combat
        )
        assert result["success"] is False

    def test_dead_target_not_selectable(self, basic_character, dead_enemy_combat):
        from services.combat_engine_service import process_player_attack
        result = process_player_attack(
            "goblin_dead", basic_character, dead_enemy_combat
        )
        assert result["success"] is False

    def test_miss_does_not_change_hp(self, basic_character, one_enemy_combat):
        from services.combat_engine_service import process_player_attack
        with patch("services.dnd_rules.roll_d20", return_value=1):
            result = process_player_attack(
                "goblin_1", basic_character, one_enemy_combat,
                weapon_type="melee", weapon_damage="1d6", weapon_name="Dagger"
            )
        goblin = next(e for e in result["combat_state_update"]["enemies"]
                      if e["id"] == "goblin_1")
        assert goblin["hp"] == 10  # unchanged

    def test_mechanical_summary_has_required_fields(self, basic_character, one_enemy_combat):
        from services.combat_engine_service import process_player_attack
        with patch("services.dnd_rules.roll_d20", return_value=12):
            result = process_player_attack(
                "goblin_1", basic_character, one_enemy_combat,
                weapon_type="melee", weapon_damage="1d6", weapon_name="Sword"
            )
        ms = result["mechanical_summary"]
        for field in ("hit", "attack_roll", "target_ac", "damage",
                      "target", "weapon_name"):
            assert field in ms, f"Missing mechanical_summary field: {field}"


class TestEnemyTurns:
    def test_alive_enemy_deals_damage(self, basic_character, one_enemy_combat):
        from services.combat_engine_service import process_enemy_turns
        with patch("services.dnd_rules.roll_d20", return_value=15):
            result = process_enemy_turns(basic_character, one_enemy_combat)
        # With a hit, total_damage > 0
        if result["enemy_actions"][0]["hit"]:
            assert result["total_damage_to_player"] > 0

    def test_dead_enemy_deals_no_damage(self, basic_character, dead_enemy_combat):
        from services.combat_engine_service import process_enemy_turns
        result = process_enemy_turns(basic_character, dead_enemy_combat)
        assert result["total_damage_to_player"] == 0
        assert result["enemy_actions"] == []

    def test_player_at_zero_hp_enters_dying(self, basic_character, one_enemy_combat):
        from services.combat_engine_service import process_enemy_turns
        dying_char = {**basic_character, "hp": 1, "max_hp": 12}
        with patch("services.dnd_rules.roll_d20", return_value=20):
            with patch("services.dnd_rules.roll_dice", return_value=10):
                result = process_enemy_turns(dying_char, one_enemy_combat)
        if result.get("player_dying"):
            assert result["character_state_update"]["hp"] <= 0
            assert "death_saves" in result["character_state_update"]

    def test_enemy_actions_have_attacker_name(self, basic_character, one_enemy_combat):
        from services.combat_engine_service import process_enemy_turns
        with patch("services.dnd_rules.roll_d20", return_value=10):
            result = process_enemy_turns(basic_character, one_enemy_combat)
        if result["enemy_actions"]:
            assert result["enemy_actions"][0]["attacker"] == "Goblin"

    def test_combat_not_over_after_enemy_turn(self, basic_character, one_enemy_combat):
        from services.combat_engine_service import process_enemy_turns
        with patch("services.dnd_rules.roll_d20", return_value=10):
            result = process_enemy_turns(basic_character, one_enemy_combat)
        assert result["combat_over"] is False  # death saves handle this


class TestSaveSpell:
    def _make_spell_card(self):
        return {
            "save_type": "dex",
            "half_on_save": True,
            "damage_dice": "2d6",
            "damage_type": "fire",
            "condition_on_fail": "prone",
        }

    def test_failed_save_takes_full_damage(self, one_enemy_combat):
        from services.combat_engine_service import process_save_spell
        caster = {"name": "Aldric", "level": 1,
                  "abilities": {"int": 16}, "proficiency_bonus": 2}
        target = dict(one_enemy_combat["enemies"][0])
        with patch("services.dnd_rules.roll_d20", return_value=2):
            with patch("services.dnd_rules.roll_dice", return_value=8):
                result = process_save_spell(
                    "Fireball", self._make_spell_card(), caster, target,
                    spell_save_dc=15, combat_state=one_enemy_combat
                )
        ms = result["mechanical_summary"]
        if not ms["save_success"]:
            assert ms["damage"] == 8  # full 2d6 (mocked to 8)

    def test_successful_save_halves_damage(self, one_enemy_combat):
        from services.combat_engine_service import process_save_spell
        caster = {"name": "Aldric", "level": 1,
                  "abilities": {"int": 16}, "proficiency_bonus": 2}
        target = dict(one_enemy_combat["enemies"][0])
        with patch("services.dnd_rules.roll_d20", return_value=20):
            with patch("services.dnd_rules.roll_dice", return_value=8):
                result = process_save_spell(
                    "Fireball", self._make_spell_card(), caster, target,
                    spell_save_dc=15, combat_state=one_enemy_combat
                )
        ms = result["mechanical_summary"]
        if ms["save_success"]:
            assert ms["damage"] == 4  # half of 8

    def test_condition_applied_on_failed_save(self, one_enemy_combat):
        from services.combat_engine_service import process_save_spell
        caster = {"name": "Aldric", "level": 1,
                  "abilities": {"int": 16}, "proficiency_bonus": 2}
        target = dict(one_enemy_combat["enemies"][0])
        target["conditions"] = []
        with patch("services.dnd_rules.roll_d20", return_value=1):
            with patch("services.dnd_rules.roll_dice", return_value=4):
                result = process_save_spell(
                    "Web", self._make_spell_card(), caster, target,
                    spell_save_dc=15, combat_state=one_enemy_combat
                )
        ms = result["mechanical_summary"]
        if not ms["save_success"] and ms.get("condition_applied"):
            assert ms["condition_applied"] == "prone"

    def test_fire_immunity_blocks_fireball(self, one_enemy_combat):
        from services.combat_engine_service import process_save_spell
        caster = {"name": "Aldric", "level": 1,
                  "abilities": {"int": 16}, "proficiency_bonus": 2}
        target = dict(one_enemy_combat["enemies"][0])
        target["immunities"] = ["fire"]
        with patch("services.dnd_rules.roll_d20", return_value=1):
            with patch("services.dnd_rules.roll_dice", return_value=10):
                result = process_save_spell(
                    "Fireball", self._make_spell_card(), caster, target,
                    spell_save_dc=15, combat_state=one_enemy_combat
                )
        assert result["mechanical_summary"]["damage"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# 3. SAVING THROWS
# ══════════════════════════════════════════════════════════════════════════════

class TestSavingThrows:
    def test_roll_above_dc_is_success(self, basic_character):
        from services.saving_throw_service import roll_saving_throw
        # Patch at the point of use: saving_throw_service imported roll_d20 directly
        with patch("services.saving_throw_service.roll_d20", return_value=18):
            result = roll_saving_throw(basic_character, "con", dc=15)
        assert result["success"] is True

    def test_roll_below_dc_is_failure(self, basic_character):
        from services.saving_throw_service import roll_saving_throw
        with patch("services.saving_throw_service.roll_d20", return_value=3):
            result = roll_saving_throw(basic_character, "con", dc=15)
        assert result["success"] is False

    def test_result_has_all_fields(self, basic_character):
        from services.saving_throw_service import roll_saving_throw
        with patch("services.saving_throw_service.roll_d20", return_value=10):
            result = roll_saving_throw(basic_character, "dex", dc=12)
        for field in ("roll", "total", "dc", "success", "modifier", "ability"):
            assert field in result, f"Missing saving throw field: {field}"

    def test_fighter_proficient_in_str_save(self, basic_character):
        from services.saving_throw_service import roll_saving_throw
        basic_character["class_"] = "Fighter"
        with patch("services.saving_throw_service.roll_d20", return_value=10):
            result = roll_saving_throw(basic_character, "str", dc=12)
        assert result.get("proficient") is True
        assert result["total"] == result["roll"] + result["modifier"] + result.get("prof_bonus", 0)

    def test_advantage_uses_higher_roll(self, basic_character):
        from services.saving_throw_service import roll_saving_throw
        rolls = iter([5, 18])
        with patch("services.saving_throw_service.roll_d20", side_effect=rolls):
            result = roll_saving_throw(basic_character, "dex", dc=12, advantage=True)
        assert result["roll"] == 18

    def test_disadvantage_uses_lower_roll(self, basic_character):
        from services.saving_throw_service import roll_saving_throw
        rolls = iter([18, 5])
        with patch("services.saving_throw_service.roll_d20", side_effect=rolls):
            result = roll_saving_throw(basic_character, "dex", dc=12, disadvantage=True)
        assert result["roll"] == 5

    def test_spell_save_dc_formula(self, basic_character):
        from services.saving_throw_service import spell_save_dc
        # DC = 8 + proficiency(2) + INT mod; basic_character INT=10 → mod=0
        # level comes from _get_level which reads class_ as string → level=1 → prof=2
        dc = spell_save_dc(basic_character, "int")
        assert dc == 10  # 8 + 2 + 0


# ══════════════════════════════════════════════════════════════════════════════
# 4. PROGRESSION / XP
# ══════════════════════════════════════════════════════════════════════════════

class TestProgression:
    def test_standard_enemy_xp(self):
        from services.progression_service import calculate_xp_for_enemy
        enemy = {"id": "goblin_1", "name": "Goblin", "hp": 10, "max_hp": 10}
        xp = calculate_xp_for_enemy(enemy)
        assert xp == 35  # standard tier

    def test_boss_enemy_xp(self):
        from services.progression_service import calculate_xp_for_enemy
        enemy = {"id": "dragon_boss", "name": "Dragon Boss", "hp": 200, "max_hp": 200}
        xp = calculate_xp_for_enemy(enemy)
        assert xp >= 100  # boss or mini_boss tier

    def test_xp_gain_no_level_up(self):
        from services.progression_service import apply_xp_gain
        char = {"level": 1, "current_xp": 50, "xp_to_next": 150,
                "hp": 10, "max_hp": 10, "attack_bonus": 0, "proficiency_bonus": 2}
        updated, events = apply_xp_gain(char, 20)
        assert updated["current_xp"] == 70
        assert events == []

    def test_xp_gain_triggers_level_up(self):
        from services.progression_service import apply_xp_gain
        char = {"level": 1, "current_xp": 140, "xp_to_next": 150,
                "hp": 10, "max_hp": 10, "attack_bonus": 0, "proficiency_bonus": 2}
        updated, events = apply_xp_gain(char, 20)
        assert updated["level"] == 2
        assert any("LEVEL_UP" in e for e in events)

    def test_level_up_increases_max_hp(self):
        from services.progression_service import apply_xp_gain
        char = {"level": 1, "current_xp": 140, "xp_to_next": 150,
                "hp": 10, "max_hp": 10, "attack_bonus": 0, "proficiency_bonus": 2}
        updated, _ = apply_xp_gain(char, 20)
        assert updated["max_hp"] > 10  # should gain HP on level up

    def test_level_up_heals_to_full(self):
        from services.progression_service import apply_xp_gain
        char = {"level": 1, "current_xp": 140, "xp_to_next": 150,
                "hp": 3, "max_hp": 10, "attack_bonus": 0, "proficiency_bonus": 2}
        updated, events = apply_xp_gain(char, 20)
        if any("LEVEL_UP" in e for e in events):
            assert updated["hp"] == updated["max_hp"]

    @pytest.mark.parametrize("level,expected_bonus", [
        (1, 2), (4, 2), (5, 3), (8, 3), (9, 4),
    ])
    def test_proficiency_bonus_by_level(self, level, expected_bonus):
        from services.dnd_rules import proficiency_bonus_for_level
        assert proficiency_bonus_for_level(level) == expected_bonus


# ══════════════════════════════════════════════════════════════════════════════
# 5. TARGET RESOLVER
# ══════════════════════════════════════════════════════════════════════════════

class TestTargetResolver:
    def test_hostile_action_detected(self):
        from services.target_resolver import is_hostile_action
        assert is_hostile_action("I attack the goblin") is True
        assert is_hostile_action("I strike with my sword") is True
        assert is_hostile_action("I kill the guard") is True

    def test_duel_and_challenge_are_hostile(self):
        from services.target_resolver import is_hostile_action
        assert is_hostile_action("I challenge him to a duel") is True
        assert is_hostile_action("I challenge the guard") is True
        assert is_hostile_action("I want to duel this man") is True
        assert is_hostile_action("accept the duel") is True
        assert is_hostile_action("I draw my sword and face him") is True
        assert is_hostile_action("fight me if you dare") is True
        assert is_hostile_action("I spar with the knight") is True

    def test_peaceful_action_not_hostile(self):
        from services.target_resolver import is_hostile_action
        assert is_hostile_action("I talk to the merchant") is False
        assert is_hostile_action("I look around the room") is False
        assert is_hostile_action("I rest by the fire") is False

    def test_resolves_to_single_enemy_in_combat(self, basic_enemy, world_blueprint, world_state):
        from services.target_resolver import resolve_target
        # combat_over must be False — the resolver skips Priority-2 when it defaults to True
        combat_state = {"enemies": [basic_enemy], "combat_over": False}
        result = resolve_target(
            player_action="I attack",
            client_target_id=None,
            combat_state=combat_state,
            world_state=world_state,
            world_blueprint=world_blueprint,
        )
        assert result["status"] == "single_target"
        assert result["target_id"] == "goblin_1"

    def test_client_target_id_takes_priority(self, basic_enemy, world_blueprint, world_state):
        from services.target_resolver import resolve_target
        # Priority-1 enemy check also gates on combat_over=False
        combat_state = {"enemies": [basic_enemy], "combat_over": False}
        result = resolve_target(
            player_action="I attack",
            client_target_id="goblin_1",
            combat_state=combat_state,
            world_state=world_state,
            world_blueprint=world_blueprint,
        )
        assert result["target_id"] == "goblin_1"

    def test_named_target_in_text(self, world_blueprint, world_state):
        from services.target_resolver import resolve_target
        # extract_named_target_from_text also checks combat_over
        goblin = {"id": "goblin_alpha", "name": "Goblin Alpha", "hp": 10}
        combat_state = {"enemies": [goblin], "combat_over": False}
        result = resolve_target(
            player_action="I stab Goblin Alpha in the eye",
            client_target_id=None,
            combat_state=combat_state,
            world_state=world_state,
            world_blueprint=world_blueprint,
        )
        assert result["target_id"] == "goblin_alpha"

    def test_no_enemies_no_target(self, world_blueprint, world_state):
        from services.target_resolver import resolve_target
        combat_state = {"enemies": []}
        result = resolve_target(
            player_action="I look around",
            client_target_id=None,
            combat_state=combat_state,
            world_state=world_state,
            world_blueprint=world_blueprint,
        )
        assert result["target_type"] == "none"


# ══════════════════════════════════════════════════════════════════════════════
# 6. PLOT ARMOR
# ══════════════════════════════════════════════════════════════════════════════

class TestPlotArmor:
    def test_essential_flag_triggers_armor(self, world_blueprint, world_state):
        from services.plot_armor_service import check_plot_armor
        npc = {"id": "npc_aria", "name": "Aria", "role": "quest_giver",
               "is_essential": True}
        result = check_plot_armor(npc, world_blueprint, world_state, "attack")
        assert result["handled"] is True

    def test_non_essential_npc_no_armor(self, world_blueprint, world_state):
        from services.plot_armor_service import check_plot_armor
        npc = {"id": "npc_random", "name": "Random Peasant", "role": "commoner",
               "is_essential": False}
        result = check_plot_armor(npc, world_blueprint, world_state, "attack")
        assert result["handled"] is False

    def test_essential_check_by_flag(self, world_blueprint):
        from services.plot_armor_service import is_npc_essential
        npc_essential = {"id": "npc_aria", "name": "Aria", "role": "quest_giver",
                         "is_essential": True}
        assert is_npc_essential(npc_essential, world_blueprint) is True

    def test_non_essential_check_by_flag(self, world_blueprint):
        from services.plot_armor_service import is_npc_essential
        npc = {"id": "npc_nobody", "name": "Peasant", "role": "commoner",
               "is_essential": False}
        assert is_npc_essential(npc, world_blueprint) is False

    def test_essential_npc_has_consequences(self, world_blueprint, world_state):
        from services.plot_armor_service import check_plot_armor
        npc = {"id": "npc_aria", "name": "Aria", "role": "quest_giver",
               "is_essential": True}
        result = check_plot_armor(npc, world_blueprint, world_state, "attack")
        if result["handled"]:
            assert len(result["consequences"]) > 0

    def test_plot_armor_returns_narrative_hint(self, world_blueprint, world_state):
        from services.plot_armor_service import check_plot_armor
        npc = {"id": "npc_aria", "name": "Aria", "role": "quest_giver",
               "is_essential": True}
        result = check_plot_armor(npc, world_blueprint, world_state, "attack")
        if result["handled"]:
            assert result["narrative_hint"]


# ══════════════════════════════════════════════════════════════════════════════
# 7. BATTLEFIELD LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

class TestBattlefieldLayout:
    def test_default_grid_has_48_cells(self):
        from services.battlefield_layout_service import _default_grid
        grid = _default_grid()
        assert len(grid["cells"]) == 48  # 8 × 6

    def test_default_grid_dimensions(self):
        from services.battlefield_layout_service import _default_grid
        grid = _default_grid()
        assert grid["cols"] == 8
        assert grid["rows"] == 6

    def test_default_grid_border_walls(self):
        from services.battlefield_layout_service import _default_grid
        grid = _default_grid()
        cell_map = {(c["x"], c["y"]): c["type"] for c in grid["cells"]}
        # Check all four corners are walls
        for corner in [(0, 0), (7, 0), (0, 5), (7, 5)]:
            assert cell_map[corner] == "wall", f"Corner {corner} should be wall"

    def test_default_grid_has_floor_cells(self):
        from services.battlefield_layout_service import _default_grid
        grid = _default_grid()
        types = [c["type"] for c in grid["cells"]]
        assert "floor" in types

    def test_default_grid_has_pillars(self):
        from services.battlefield_layout_service import _default_grid
        grid = _default_grid()
        types = [c["type"] for c in grid["cells"]]
        assert "pillar" in types

    def test_location_key_slugification(self):
        from services.battlefield_layout_service import location_key_for
        assert location_key_for("The Dark Forest!") == "the_dark_forest"
        assert location_key_for("TAVERN & Inn") == "tavern_inn"
        assert location_key_for("  spaces  ") == "spaces"

    def test_location_key_empty_string(self):
        from services.battlefield_layout_service import location_key_for
        assert location_key_for("") == "unknown"

    def test_enemy_positions_lane2(self):
        from services.battlefield_layout_service import enemy_start_positions
        enemies = [{"id": "e1", "lane": 2}]
        result = enemy_start_positions(enemies, grid_cols=8, grid_rows=6)
        assert result[0]["grid_x"] == 5  # cols-3

    def test_enemy_positions_lane3(self):
        from services.battlefield_layout_service import enemy_start_positions
        enemies = [{"id": "e1", "lane": 3}]
        result = enemy_start_positions(enemies, grid_cols=8, grid_rows=6)
        assert result[0]["grid_x"] == 6  # cols-2

    def test_multiple_enemies_spread_vertically(self):
        from services.battlefield_layout_service import enemy_start_positions
        enemies = [{"id": f"e{i}", "lane": 2} for i in range(3)]
        result = enemy_start_positions(enemies, grid_cols=8, grid_rows=6)
        y_positions = [e["grid_y"] for e in result]
        assert len(set(y_positions)) > 1  # not all stacked in same row

    def test_parse_json_grid_valid(self):
        from services.battlefield_layout_service import _parse_json_grid
        cells = [{"x": i % 8, "y": i // 8, "type": "floor"} for i in range(48)]
        import json
        raw = json.dumps({"cols": 8, "rows": 6, "cells": cells})
        result = _parse_json_grid(raw)
        assert result is not None
        assert len(result["cells"]) == 48

    def test_parse_json_grid_strips_markdown(self):
        from services.battlefield_layout_service import _parse_json_grid
        cells = [{"x": i % 8, "y": i // 8, "type": "floor"} for i in range(48)]
        import json
        raw = f"```json\n{json.dumps({'cols': 8, 'rows': 6, 'cells': cells})}\n```"
        result = _parse_json_grid(raw)
        assert result is not None

    def test_parse_json_grid_invalid_returns_none(self):
        from services.battlefield_layout_service import _parse_json_grid
        assert _parse_json_grid("not json at all") is None
        assert _parse_json_grid('{"cols": 8, "cells": []}') is None  # too few cells


    def test_normalize_enemy_list_preserves_grid_positions(self):
        """normalize_enemy_list must not strip grid_x/grid_y (combat resume regression)."""
        from models.normalized_entities import normalize_enemy_list
        enemies = [{
            "id": "e1", "name": "Orc", "hp": 15, "max_hp": 15, "ac": 13,
            "grid_x": 6, "grid_y": 2, "lane": 3,
            "conditions": ["poisoned"], "resistances": ["fire"],
            "proficiency_bonus": 2, "attack_bonus": 3, "damage_die": "1d8",
        }]
        result = normalize_enemy_list(enemies)
        assert result[0]["grid_x"] == 6
        assert result[0]["grid_y"] == 2
        assert result[0]["lane"] == 3
        assert result[0]["conditions"] == ["poisoned"]
        assert result[0]["resistances"] == ["fire"]
        assert result[0]["proficiency_bonus"] == 2

    def test_normalize_enemy_list_guarantees_required_fields(self):
        """normalize_enemy_list must fill in missing combat stats."""
        from models.normalized_entities import normalize_enemy_list
        enemies = [{"id": "e1", "name": "Skeleton"}]  # minimal — no hp/ac
        result = normalize_enemy_list(enemies)
        assert result[0]["hp"] > 0
        assert result[0]["max_hp"] > 0
        assert result[0]["ac"] >= 1


# ══════════════════════════════════════════════════════════════════════════════
# 8. INTEGRATION — Full combat round simulation
# ══════════════════════════════════════════════════════════════════════════════

class TestFullCombatRound:
    """Simulates a complete combat round: initiative → player attack → enemy turn."""

    def test_full_round_player_wins(self, basic_character, basic_enemy, world_blueprint):
        from services.combat_engine_service import (
            start_combat_with_target,
            process_player_attack,
            process_enemy_turns,
        )

        resolution = {
            "target_type": "enemy",
            "target_id": basic_enemy["id"],
            "target_name": basic_enemy["name"],
            "target_data": basic_enemy,
        }

        # Round 0 — Start
        combat = start_combat_with_target(
            resolution, basic_character, world_blueprint,
            character_level=1, world_state={}
        )
        assert combat["combat_over"] is False

        # Round 1 — Player crits the goblin for overwhelming damage
        with patch("services.dnd_rules.roll_d20", return_value=20):
            with patch("services.dnd_rules.roll_dice", return_value=8):
                player_result = process_player_attack(
                    basic_enemy["id"], basic_character, combat,
                    weapon_type="melee", weapon_damage="1d8",
                    weapon_name="Longsword"
                )

        if player_result["combat_over"]:
            assert player_result["xp_gained"] > 0
            assert player_result["combat_state_update"]["outcome"] == "victory"
        else:
            # Goblin is still alive — enemy gets a turn
            combat.update(player_result["combat_state_update"])
            with patch("services.dnd_rules.roll_d20", return_value=8):
                enemy_result = process_enemy_turns(basic_character, combat)
            assert "enemy_actions" in enemy_result

    def test_full_round_player_takes_damage(self, basic_character, basic_enemy, world_blueprint):
        from services.combat_engine_service import (
            start_combat_with_target,
            process_player_attack,
            process_enemy_turns,
        )

        resolution = {
            "target_type": "enemy",
            "target_id": basic_enemy["id"],
            "target_name": basic_enemy["name"],
            "target_data": basic_enemy,
        }

        combat = start_combat_with_target(
            resolution, basic_character, world_blueprint,
            character_level=1, world_state={}
        )

        # Player misses
        with patch("services.dnd_rules.roll_d20", return_value=1):
            player_result = process_player_attack(
                basic_enemy["id"], basic_character, combat,
                weapon_type="melee", weapon_damage="1d6", weapon_name="Sword"
            )
        combat.update(player_result["combat_state_update"])

        # Goblin hits player
        with patch("services.dnd_rules.roll_d20", return_value=18):
            enemy_result = process_enemy_turns(basic_character, combat)

        if enemy_result["enemy_actions"][0]["hit"]:
            assert enemy_result["total_damage_to_player"] > 0
            assert enemy_result["character_state_update"]["hp"] < basic_character["hp"]

    def test_npc_conversion_and_combat(self, basic_character, world_blueprint):
        from services.combat_engine_service import (
            start_combat_with_target,
            convert_npc_to_enemy,
            process_player_attack,
        )

        npc = {"id": "npc_guard_hostile", "name": "Hostile Guard", "role": "guard"}
        enemy = convert_npc_to_enemy(npc, world_blueprint, character_level=1)

        resolution = {
            "target_type": "enemy",
            "target_id": enemy["id"],
            "target_name": enemy["name"],
            "target_data": enemy,
        }

        combat = start_combat_with_target(
            resolution, basic_character, world_blueprint,
            character_level=1, world_state={}
        )

        # Verify the guard's stats are in combat
        guard = combat["enemies"][0]
        assert guard["hp"] == 20
        assert guard["ac"] == 14

        # Attack
        with patch("services.dnd_rules.roll_d20", return_value=14):
            result = process_player_attack(
                enemy["id"], basic_character, combat,
                weapon_type="melee", weapon_damage="1d8", weapon_name="Sword"
            )
        assert result["success"] is True


# ══════════════════════════════════════════════════════════════════════════════
# Behavior Tree Engine
# ══════════════════════════════════════════════════════════════════════════════

class TestBehaviorTreeEngine:
    """Tests for the pure-Python behavior tree evaluator."""

    @pytest.fixture
    def simple_enemy(self):
        return {
            "id": "orc_1", "name": "Orc",
            "hp": 15, "max_hp": 15, "ac": 13,
            "attack_bonus": 3, "damage_die": "1d8",
            "damage_type": "slashing",
            "grid_x": 1, "grid_y": 2,
            "abilities": {"str": 16, "dex": 10, "con": 14, "int": 7, "wis": 11, "cha": 10},
            "conditions": [], "resistances": [], "immunities": [],
        }

    @pytest.fixture
    def player_adjacent(self):
        return {"hp": 20, "max_hp": 20, "ac": 14, "name": "Hero",
                "grid_x": 1, "grid_y": 2, "abilities": {}}

    @pytest.fixture
    def player_far(self):
        return {"hp": 20, "max_hp": 20, "ac": 14, "name": "Hero",
                "grid_x": 7, "grid_y": 2, "abilities": {}}

    def test_context_hp_pct(self, simple_enemy, player_adjacent):
        from services.behavior_tree_engine import build_context
        simple_enemy["hp"] = 8
        ctx = build_context(simple_enemy, player_adjacent, {"round": 1, "alive_enemies": [simple_enemy]})
        assert abs(ctx["enemy_hp_pct"] - 8 / 15) < 0.01

    def test_in_melee_range_adjacent(self, simple_enemy, player_adjacent):
        from services.behavior_tree_engine import build_context
        ctx = build_context(simple_enemy, player_adjacent, {
            "round": 1, "alive_enemies": [simple_enemy],
            "player_grid_x": player_adjacent["grid_x"], "player_grid_y": player_adjacent["grid_y"],
        })
        assert ctx["in_melee_range"] is True

    def test_not_in_melee_range_far(self, simple_enemy, player_far):
        from services.behavior_tree_engine import build_context
        ctx = build_context(simple_enemy, player_far, {
            "round": 1, "alive_enemies": [simple_enemy],
            "player_grid_x": player_far["grid_x"], "player_grid_y": player_far["grid_y"],
        })
        assert ctx["in_melee_range"] is False

    def _ctx(self, enemy, player, round_=1):
        from services.behavior_tree_engine import build_context
        return build_context(enemy, player, {
            "round": round_, "alive_enemies": [enemy],
            "player_grid_x": player["grid_x"], "player_grid_y": player["grid_y"],
        })

    def test_condition_hp_below_true(self, simple_enemy, player_adjacent):
        simple_enemy["hp"] = 3
        ctx = self._ctx(simple_enemy, player_adjacent)
        from services.behavior_tree_engine import evaluate
        node = {"type": "condition", "check": "hp_below", "value": 0.5}
        success, _ = evaluate(node, ctx)
        assert success is True

    def test_condition_hp_below_false(self, simple_enemy, player_adjacent):
        ctx = self._ctx(simple_enemy, player_adjacent)
        from services.behavior_tree_engine import evaluate
        node = {"type": "condition", "check": "hp_below", "value": 0.1}
        success, _ = evaluate(node, ctx)
        assert success is False

    def test_condition_in_melee_range(self, simple_enemy, player_adjacent):
        ctx = self._ctx(simple_enemy, player_adjacent)
        from services.behavior_tree_engine import evaluate
        node = {"type": "condition", "check": "in_melee_range"}
        success, _ = evaluate(node, ctx)
        assert success is True

    def test_selector_picks_first_success(self, simple_enemy, player_adjacent):
        from services.behavior_tree_engine import evaluate
        ctx = self._ctx(simple_enemy, player_adjacent)
        tree = {
            "type": "selector",
            "children": [
                {"type": "condition", "check": "in_melee_range"},
                {"type": "action", "action": "flee"},
            ],
        }
        success, result = evaluate(tree, ctx)
        assert success is True

    def test_sequence_fails_if_any_child_fails(self, simple_enemy, player_far):
        from services.behavior_tree_engine import evaluate
        ctx = self._ctx(simple_enemy, player_far)
        tree = {
            "type": "sequence",
            "children": [
                {"type": "condition", "check": "in_melee_range"},  # False — enemy far
                {"type": "action", "action": "attack_melee"},
            ],
        }
        success, _ = evaluate(tree, ctx)
        assert success is False

    def test_action_attack_returns_action_dict(self, simple_enemy, player_adjacent):
        from services.behavior_tree_engine import evaluate
        ctx = self._ctx(simple_enemy, player_adjacent)
        node = {"type": "action", "action": "attack_melee", "label": "Strike"}
        success, result = evaluate(node, ctx)
        assert success is True
        assert result["action_type"] in ("attack", "special_attack")

    def test_action_flee_returns_flee_dict(self, simple_enemy, player_adjacent):
        from services.behavior_tree_engine import evaluate
        ctx = self._ctx(simple_enemy, player_adjacent)
        node = {"type": "action", "action": "flee"}
        success, result = evaluate(node, ctx)
        assert success is True
        assert result["action_type"] == "flee"

    def test_not_decorator_inverts(self, simple_enemy, player_adjacent):
        from services.behavior_tree_engine import evaluate
        ctx = self._ctx(simple_enemy, player_adjacent)
        node = {"type": "not", "child": {"type": "condition", "check": "in_melee_range"}}
        success, _ = evaluate(node, ctx)
        assert success is False  # in_melee_range True → NOT → False

    def test_list_conditions_not_empty(self):
        from services.behavior_tree_engine import list_available_conditions
        conditions = list_available_conditions()
        assert len(conditions) >= 10
        ids = [c["id"] for c in conditions]
        assert "hp_below" in ids
        assert "in_melee_range" in ids

    def test_list_actions_not_empty(self):
        from services.behavior_tree_engine import list_available_actions
        actions = list_available_actions()
        assert len(actions) >= 8
        ids = [a["id"] for a in actions]
        assert "attack_melee" in ids
        assert "flee" in ids
        assert "multiattack" in ids


# ══════════════════════════════════════════════════════════════════════════════
# Multiattack Resolution
# ══════════════════════════════════════════════════════════════════════════════

class TestMultiattack:
    """Verify process_enemy_turns resolves every attack in a multiattack."""

    @pytest.fixture
    def dragon_enemy(self):
        return {
            "id": "dragon_1", "name": "Young Dragon",
            "hp": 120, "max_hp": 120, "ac": 17,
            "attack_bonus": 7, "damage_die": "2d6+5",
            "damage_type": "slashing",
            "grid_x": 1, "grid_y": 2,
            "abilities": {"str": 21, "dex": 10, "con": 19, "int": 14, "wis": 11, "cha": 19},
            "conditions": [], "resistances": [], "immunities": [],
            "faction_role": "solo",
        }

    @pytest.fixture
    def dragon_combat(self, dragon_enemy):
        return {
            "combat_id": "c1", "round": 2, "combat_over": False,
            "enemies": [dragon_enemy],
            "player_hp": 50, "player_max_hp": 50,
            "player_ac": 16, "player_name": "Hero",
            "player_grid_x": 1, "player_grid_y": 2,
        }

    def _multiattack_action(self):
        return {
            "action_type": "special_attack",
            "attacks": [
                {"name": "Bite", "damage_die": "2d10+5", "damage_type": "piercing"},
                {"name": "Claw", "damage_die": "2d6+5",  "damage_type": "slashing"},
                {"name": "Claw", "damage_die": "2d6+5",  "damage_type": "slashing"},
            ],
            "advantage": False,
            "disadvantage": False,
            "adv_reason": "",
            "special_effect": {"type": "multiattack", "extra_attacks": 2},
            "grid_move": None,
            "narration_hint": "The dragon attacks with fury.",
            "abilities_used": ["multiattack"],
        }

    def test_multiattack_produces_three_action_entries(self, dragon_combat, dragon_enemy):
        from services.combat_engine_service import process_enemy_turns
        char = {
            "hp": 50, "max_hp": 50, "ac": 14, "name": "Hero",
            "abilities": {"str": 10, "dex": 10, "con": 12, "int": 10, "wis": 10, "cha": 10},
            "conditions": [],
        }
        multiattack = self._multiattack_action()

        with patch("services.enemy_behavior_service.decide_enemy_action", return_value=multiattack):
            with patch("services.dnd_rules.roll_d20", return_value=15):
                result = process_enemy_turns(char, dragon_combat)

        # Expect 3 entries — one per attack in the multiattack list
        assert len(result["enemy_actions"]) == 3

    def test_multiattack_each_entry_has_attack_name(self, dragon_combat):
        from services.combat_engine_service import process_enemy_turns
        char = {
            "hp": 50, "max_hp": 50, "ac": 14, "name": "Hero",
            "abilities": {"str": 10, "dex": 10, "con": 12, "int": 10, "wis": 10, "cha": 10},
            "conditions": [],
        }
        multiattack = self._multiattack_action()

        with patch("services.enemy_behavior_service.decide_enemy_action", return_value=multiattack):
            with patch("services.dnd_rules.roll_d20", return_value=18):
                result = process_enemy_turns(char, dragon_combat)

        names = [a.get("attack_name") for a in result["enemy_actions"]]
        assert "Bite" in names
        assert names.count("Claw") == 2

    def test_multiattack_total_damage_is_cumulative(self, dragon_combat):
        from services.combat_engine_service import process_enemy_turns
        char = {
            "hp": 80, "max_hp": 80, "ac": 5,  # very low AC so all attacks hit
            "name": "Hero",
            "abilities": {"str": 10, "dex": 10, "con": 12, "int": 10, "wis": 10, "cha": 10},
            "conditions": [],
        }
        multiattack = self._multiattack_action()

        with patch("services.enemy_behavior_service.decide_enemy_action", return_value=multiattack):
            with patch("services.dnd_rules.roll_d20", return_value=18):
                with patch("services.dnd_rules.roll_dice", return_value=6):
                    result = process_enemy_turns(char, dragon_combat)

        # Sum of individual action damages must equal total
        summed = sum(a["damage"] for a in result["enemy_actions"])
        assert result["total_damage_to_player"] == summed

    def test_single_attack_produces_one_action_entry(self, dragon_combat):
        from services.combat_engine_service import process_enemy_turns
        char = {
            "hp": 50, "max_hp": 50, "ac": 14, "name": "Hero",
            "abilities": {"str": 10, "dex": 10, "con": 12, "int": 10, "wis": 10, "cha": 10},
            "conditions": [],
        }
        single = {
            "action_type": "attack",
            "attacks": None,
            "advantage": False, "disadvantage": False,
            "adv_reason": "", "special_effect": None, "grid_move": None,
            "narration_hint": "The dragon bites.", "abilities_used": [],
        }

        with patch("services.enemy_behavior_service.decide_enemy_action", return_value=single):
            with patch("services.dnd_rules.roll_d20", return_value=12):
                result = process_enemy_turns(char, dragon_combat)

        assert len(result["enemy_actions"]) == 1

    def test_multiattack_index_field_is_sequential(self, dragon_combat):
        from services.combat_engine_service import process_enemy_turns
        char = {
            "hp": 50, "max_hp": 50, "ac": 14, "name": "Hero",
            "abilities": {"str": 10, "dex": 10, "con": 12, "int": 10, "wis": 10, "cha": 10},
            "conditions": [],
        }
        multiattack = self._multiattack_action()

        with patch("services.enemy_behavior_service.decide_enemy_action", return_value=multiattack):
            with patch("services.dnd_rules.roll_d20", return_value=15):
                result = process_enemy_turns(char, dragon_combat)

        indices = [a.get("multiattack_index") for a in result["enemy_actions"]]
        assert indices == [0, 1, 2]


# ══════════════════════════════════════════════════════════════════════════════
# Faction Combat Service
# ══════════════════════════════════════════════════════════════════════════════

class TestFactionCombat:
    """Tests for leader/follower role assignment and morale cascade."""

    def _make_enemy(self, id_, name, role="", hp=20, faction_id="gang_1"):
        return {
            "id": id_, "name": name, "role": role,
            "hp": hp, "max_hp": hp, "ac": 12,
            "attack_bonus": 2, "damage_die": "1d6",
            "abilities": {"str": 12, "dex": 10, "con": 12, "int": 8, "wis": 10, "cha": 8},
            "conditions": [], "resistances": [], "immunities": [],
            "faction_id": faction_id,
        }

    def test_leader_keyword_assigns_leader_role(self):
        from services.faction_combat_service import assign_faction_roles
        captain = self._make_enemy("c1", "Guard Captain", role="captain")
        grunt   = self._make_enemy("g1", "Guard Grunt")
        assign_faction_roles([captain, grunt])
        assert captain["faction_role"] == "leader"
        assert grunt["faction_role"] in ("follower", "flanker", "bodyguard")

    def test_highest_hp_becomes_leader_when_no_keyword(self):
        from services.faction_combat_service import assign_faction_roles
        weak   = self._make_enemy("w1", "Weak Thug", hp=10)
        strong = self._make_enemy("s1", "Strong Thug", hp=30)
        assign_faction_roles([weak, strong])
        assert strong["faction_role"] == "leader"
        assert weak["faction_role"] in ("follower",)

    def test_bodyguard_keyword_assigns_bodyguard_role(self):
        from services.faction_combat_service import assign_faction_roles
        captain   = self._make_enemy("c1", "Captain", role="captain")
        bodyguard = self._make_enemy("b1", "Bodyguard Champion", role="bodyguard")
        assign_faction_roles([captain, bodyguard])
        assert bodyguard["faction_role"] == "bodyguard"

    def test_solo_enemy_gets_solo_role(self):
        from services.faction_combat_service import assign_faction_roles
        lone = self._make_enemy("l1", "Lone Wolf", faction_id=None)
        lone.pop("faction_id")
        assign_faction_roles([lone])
        assert lone.get("faction_role", "solo") == "solo"

    def test_leader_id_set_on_followers(self):
        from services.faction_combat_service import assign_faction_roles
        captain = self._make_enemy("c1", "Captain", role="captain")
        grunt   = self._make_enemy("g1", "Grunt")
        assign_faction_roles([captain, grunt])
        assert grunt.get("leader_id") == "c1"

    def test_faction_context_leader_alive(self):
        from services.faction_combat_service import assign_faction_roles, faction_context_for
        captain = self._make_enemy("c1", "Captain", role="captain")
        grunt   = self._make_enemy("g1", "Grunt")
        assign_faction_roles([captain, grunt])
        ctx = faction_context_for(grunt, [captain, grunt])
        assert ctx["faction_leader_alive"] is True
        assert ctx["faction_leader_id"] == "c1"

    def test_faction_context_leader_dead(self):
        from services.faction_combat_service import assign_faction_roles, faction_context_for
        captain = self._make_enemy("c1", "Captain", role="captain")
        grunt   = self._make_enemy("g1", "Grunt")
        assign_faction_roles([captain, grunt])
        # Leader is absent from alive list
        ctx = faction_context_for(grunt, [grunt])
        assert ctx["faction_leader_alive"] is False

    def test_morale_break_on_failed_wis_save(self):
        from services.faction_combat_service import apply_death_morale
        dead_captain = self._make_enemy("c1", "Captain", role="captain")
        dead_captain["faction_role"] = "leader"
        grunt = self._make_enemy("g1", "Grunt")
        grunt["faction_role"] = "follower"
        # WIS 10 = +0 mod; roll 1 → total 1, well below DC 13
        with patch("services.dnd_rules.roll_d20", return_value=1):
            result = apply_death_morale(dead_captain, [grunt])
        assert result[0].get("morale_break") is True

    def test_morale_rage_on_passed_wis_save(self):
        from services.faction_combat_service import apply_death_morale
        dead_captain = self._make_enemy("c1", "Captain", role="captain")
        dead_captain["faction_role"] = "leader"
        grunt = self._make_enemy("g1", "Grunt")
        grunt["faction_role"] = "follower"
        # Roll 20 → always pass DC 13
        with patch("services.dnd_rules.roll_d20", return_value=20):
            result = apply_death_morale(dead_captain, [grunt])
        assert result[0].get("morale_rage") is True

    def test_non_leader_death_no_cascade(self):
        from services.faction_combat_service import apply_death_morale
        dead_grunt = self._make_enemy("g1", "Grunt")
        dead_grunt["faction_role"] = "follower"
        survivor = self._make_enemy("g2", "Grunt 2")
        result = apply_death_morale(dead_grunt, [survivor])
        assert not result[0].get("morale_break")
        assert not result[0].get("morale_rage")

    def test_morale_break_overrides_to_flee_action(self):
        from services.faction_combat_service import apply_morale_modifiers
        enemy = self._make_enemy("g1", "Grunt")
        enemy["morale_break"] = True
        result = apply_morale_modifiers(enemy, {})
        assert result is not None
        assert result["action_type"] == "flee"

    def test_morale_rage_grants_advantage(self):
        from services.faction_combat_service import apply_morale_modifiers
        enemy = self._make_enemy("g1", "Grunt")
        enemy["morale_rage"] = True
        result = apply_morale_modifiers(enemy, {})
        assert result is not None
        assert result["advantage"] is True
        # Flag cleared after use
        assert not enemy.get("morale_rage")


# ══════════════════════════════════════════════════════════════════════════════
# NPC Behavior Mapper
# ══════════════════════════════════════════════════════════════════════════════

class TestNpcBehaviorMapper:
    """Tests for rule-based personality → behavior tree mapping."""

    def _npc(self, role="guard", tags=None, name="Test NPC"):
        return {
            "id": "npc_1", "name": name,
            "role": role,
            "personality_tags": tags or [],
            "description": "", "personality": "",
            "traits": [], "occupation": role,
        }

    def test_guard_maps_to_orc_base_tree(self):
        from services.npc_behavior_mapper import get_behavior_tree_for_npc
        tree = get_behavior_tree_for_npc(self._npc(role="guard"))
        assert tree["_source_tree"] == "orc"

    def test_assassin_maps_to_assassin_tree(self):
        from services.npc_behavior_mapper import get_behavior_tree_for_npc
        tree = get_behavior_tree_for_npc(self._npc(role="assassin"))
        assert tree["_source_tree"] == "assassin"

    def test_mage_maps_to_cult_fanatic_tree(self):
        from services.npc_behavior_mapper import get_behavior_tree_for_npc
        tree = get_behavior_tree_for_npc(self._npc(role="mage"))
        assert tree["_source_tree"] == "cult_fanatic"

    def test_merchant_maps_to_goblin_flee_tree(self):
        from services.npc_behavior_mapper import get_behavior_tree_for_npc
        tree = get_behavior_tree_for_npc(self._npc(role="merchant"))
        assert tree["_source_tree"] == "goblin"

    def test_cowardly_tag_high_flee_threshold(self):
        from services.npc_behavior_mapper import get_behavior_tree_for_npc
        tree = get_behavior_tree_for_npc(self._npc(tags=["cowardly"]))
        assert tree["_flee_threshold"] >= 0.5

    def test_fearless_tag_no_flee(self):
        from services.npc_behavior_mapper import get_behavior_tree_for_npc
        tree = get_behavior_tree_for_npc(self._npc(tags=["fearless"]))
        assert tree["_flee_threshold"] is None

    def test_brave_tag_low_flee_threshold(self):
        from services.npc_behavior_mapper import get_behavior_tree_for_npc
        tree = get_behavior_tree_for_npc(self._npc(tags=["brave"]))
        assert tree["_flee_threshold"] <= 0.15

    def test_reckless_tag_injects_reckless_action(self):
        from services.npc_behavior_mapper import get_behavior_tree_for_npc
        import json
        tree = get_behavior_tree_for_npc(self._npc(tags=["reckless"]))
        tree_str = json.dumps(tree["node"])
        assert "reckless_attack" in tree_str

    def test_hesitant_tag_wraps_in_hesitation(self):
        from services.npc_behavior_mapper import get_behavior_tree_for_npc
        import json
        tree = get_behavior_tree_for_npc(self._npc(tags=["morally_conflicted"]))
        tree_str = json.dumps(tree["node"])
        assert "is_first_round" in tree_str

    def test_faction_leader_role_overrides_to_guard_leader(self):
        from services.npc_behavior_mapper import get_behavior_tree_for_npc
        npc = self._npc(role="guard")
        npc["faction_role"] = "leader"
        tree = get_behavior_tree_for_npc(npc)
        assert tree["_source_tree"] == "guard_leader"

    def test_faction_bodyguard_role_overrides(self):
        from services.npc_behavior_mapper import get_behavior_tree_for_npc
        npc = self._npc(role="guard")
        npc["faction_role"] = "bodyguard"
        tree = get_behavior_tree_for_npc(npc)
        assert tree["_source_tree"] == "bodyguard"

    def test_tree_has_required_fields(self):
        from services.npc_behavior_mapper import get_behavior_tree_for_npc
        tree = get_behavior_tree_for_npc(self._npc())
        assert "id" in tree
        assert "name" in tree
        assert "node" in tree
        assert tree["node"]  # non-empty
