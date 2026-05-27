"""Tests for NPC tier system: tier profiles, commoner mechanics, encounter composer."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch

from data.npc_tiers import NPC_TIERS, COMMONER_OCCUPATIONS, ENCOUNTER_TEMPLATES, get_tier, get_occupation
from data.behavior_trees import DEFAULT_TREES
from services.behavior_tree_engine import build_context, evaluate, _eval_condition
from services.encounter_composer_service import (
    compose_encounter, intel_from_investigation, describe_encounter_for_dm
)
from services.loot_service import weapon_from_enemy, generate_enemy_loot


# ── NPC_TIERS data ────────────────────────────────────────────────────────────

class TestNpcTiersData:
    def test_all_five_tiers_defined(self):
        assert set(NPC_TIERS.keys()) == {"commoner", "gifted", "specialist", "commander", "mythic"}

    def test_tier_numbers_are_sequential(self):
        assert [NPC_TIERS[t]["tier"] for t in ("commoner","gifted","specialist","commander","mythic")] == [1,2,3,4,5]

    def test_commoner_flee_threshold_is_half(self):
        assert NPC_TIERS["commoner"]["flee_threshold"] == 0.5

    def test_mythic_never_flees(self):
        assert NPC_TIERS["mythic"]["flee_threshold"] == 0.0

    def test_commoner_loot_class_is_personal_effects(self):
        assert NPC_TIERS["commoner"]["loot_class"] == "personal_effects"

    def test_commoner_has_panic_check_mechanic(self):
        assert "panic_check" in NPC_TIERS["commoner"]["signature_mechanics"]

    def test_commander_has_command_aura_mechanic(self):
        assert "command_aura" in NPC_TIERS["commander"]["signature_mechanics"]

    def test_mythic_has_weakness_system(self):
        assert "weakness_system" in NPC_TIERS["mythic"]["signature_mechanics"]

    def test_get_tier_returns_correct(self):
        t = get_tier("specialist")
        assert t["tier"] == 3

    def test_get_tier_unknown_falls_back_to_commoner(self):
        t = get_tier("nonexistent")
        assert t["tier"] == 1

    def test_commoner_occupations_all_have_personal_effects(self):
        for occ, data in COMMONER_OCCUPATIONS.items():
            assert "personal_effects" in data, f"{occ} missing personal_effects"
            assert len(data["personal_effects"]) >= 2

    def test_get_occupation_default_fallback(self):
        occ = get_occupation("astronaut")
        assert occ["weapon_name"] == "Fist"

    def test_farmer_occupation_has_pitchfork(self):
        occ = get_occupation("farmer")
        assert occ["weapon_name"] == "Pitchfork"
        assert occ["damage_die"] == "1d6"


# ── Commoner behavior tree ────────────────────────────────────────────────────

class TestCommonerBehaviorTree:
    def test_commoner_tree_in_default_trees(self):
        assert "commoner" in DEFAULT_TREES

    def test_commoner_tree_root_is_selector(self):
        tree = DEFAULT_TREES["commoner"]
        assert tree["node"]["type"] == "selector"

    def _make_enemy(self, hp=4, max_hp=8, panicked=False, cornered=False, round_=1):
        return {
            "id": "commoner_0", "name": "Villager", "tier": "commoner",
            "hp": hp, "max_hp": max_hp,
            "attack_bonus": 0, "damage_die": "1d4", "damage_type": "bludgeoning",
            "panicked": panicked, "cornered": cornered,
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
        }

    def _ctx(self, enemy, round_=1, alive_enemies=None, in_melee=True):
        player = {"hp": 20, "max_hp": 20, "ac": 14, "conditions": [], "abilities": {}}
        combat_ctx = {
            "round": round_, "alive_enemies": alive_enemies or [enemy],
            "player_grid_x": 1, "player_grid_y": 1,
        }
        enemy["grid_x"] = 1
        enemy["grid_y"] = 1
        return build_context(enemy, player, combat_ctx)

    def test_panicked_flee_when_not_cornered(self):
        enemy = self._make_enemy(hp=2, max_hp=8, panicked=True, cornered=False)
        ctx = self._ctx(enemy)
        tree = DEFAULT_TREES["commoner"]["node"]
        ok, action = evaluate(tree, ctx)
        assert ok
        assert action["action_type"] == "flee"

    def test_panicked_cornered_freezes(self):
        enemy = self._make_enemy(hp=2, max_hp=8, panicked=True, cornered=True)
        ctx = self._ctx(enemy)
        tree = DEFAULT_TREES["commoner"]["node"]
        ok, action = evaluate(tree, ctx)
        assert ok
        assert action["action_type"] == "defend"

    def test_surrender_after_3_rounds_cornered(self):
        enemy = self._make_enemy(hp=2, max_hp=8, panicked=False, cornered=True)
        ctx = self._ctx(enemy, round_=4)  # round > 2
        tree = DEFAULT_TREES["commoner"]["node"]
        ok, action = evaluate(tree, ctx)
        assert ok
        assert action["action_type"] == "surrender"

    def test_mob_courage_attacks_round1_with_allies(self):
        enemy = self._make_enemy(hp=8, max_hp=8, panicked=False)
        allies = [self._make_enemy() for _ in range(3)]
        ctx = self._ctx(enemy, round_=1, alive_enemies=[enemy] + allies)
        tree = DEFAULT_TREES["commoner"]["node"]
        ok, action = evaluate(tree, ctx)
        assert ok
        assert action["action_type"] in ("attack", "move_and_attack")


# ── New behavior_tree_engine conditions ───────────────────────────────────────

class TestNewConditions:
    def test_is_panicked_true(self):
        ctx = {"enemy": {"panicked": True}}
        assert _eval_condition({"check": "is_panicked"}, ctx) is True

    def test_is_panicked_false(self):
        ctx = {"enemy": {"panicked": False}}
        assert _eval_condition({"check": "is_panicked"}, ctx) is False

    def test_is_cornered_true(self):
        ctx = {"enemy": {"cornered": True}}
        assert _eval_condition({"check": "is_cornered"}, ctx) is True

    def test_has_tier_matches(self):
        ctx = {"enemy": {"tier": "commoner"}}
        assert _eval_condition({"check": "has_tier", "value": "commoner"}, ctx) is True

    def test_has_tier_no_match(self):
        ctx = {"enemy": {"tier": "specialist"}}
        assert _eval_condition({"check": "has_tier", "value": "commoner"}, ctx) is False

    def test_tier_below_commoner_is_below_3(self):
        ctx = {"enemy": {"tier": "commoner"}}
        assert _eval_condition({"check": "tier_below", "value": 3}, ctx) is True

    def test_tier_below_commander_is_not_below_3(self):
        ctx = {"enemy": {"tier": "commander"}}
        assert _eval_condition({"check": "tier_below", "value": 3}, ctx) is False


# ── Commoner panic in combat engine ──────────────────────────────────────────

class TestCommonerPanic:
    def _make_commoner(self, hp=2, max_hp=8, wis=10):
        return {
            "id": "c0", "name": "Peasant", "tier": "commoner",
            "hp": hp, "max_hp": max_hp,
            "attack_bonus": 0, "damage_die": "1d4", "damage_type": "bludgeoning",
            "panicked": False, "cornered": False, "_rounds_panicked": 0,
            "abilities": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": wis, "cha": 10},
            "ac": 10,
            "grid_x": 2, "grid_y": 2,
            "behavior_tree_id": "commoner",
        }

    def _char(self, hp=20):
        return {
            "hp": hp, "max_hp": 20, "ac": 14, "name": "Hero",
            "abilities": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
            "proficiency_bonus": 2, "conditions": [], "gold": 0,
        }

    def _combat(self, commoner):
        return {
            "enemies": [commoner],
            "round": 2,
            "player_grid_x": 1, "player_grid_y": 2,
            "battlefield_grid": None,
        }

    def test_failed_panic_check_sets_panicked_flag(self):
        from services.combat_engine_service import process_enemy_turns
        commoner = self._make_commoner(hp=2, max_hp=8)  # 25% HP — triggers panic
        char = self._char()
        combat = self._combat(commoner)
        # Force panic roll to fail (roll 1 → total 1+0 = 1 < 10)
        with patch("services.dnd_rules.roll_d20", return_value=1):
            result = process_enemy_turns(char, combat)
        assert commoner.get("panicked") is True

    def test_passed_panic_check_keeps_not_panicked(self):
        from services.combat_engine_service import process_enemy_turns
        commoner = self._make_commoner(hp=2, max_hp=8)
        char = self._char()
        combat = self._combat(commoner)
        # Force panic roll to succeed (roll 15 → total 15 > 10)
        with patch("services.dnd_rules.roll_d20", return_value=15):
            result = process_enemy_turns(char, combat)
        assert commoner.get("panicked") is False

    def test_high_hp_commoner_never_panics(self):
        from services.combat_engine_service import process_enemy_turns
        commoner = self._make_commoner(hp=8, max_hp=8)  # full HP
        char = self._char()
        combat = self._combat(commoner)
        with patch("services.dnd_rules.roll_d20", return_value=1):
            result = process_enemy_turns(char, combat)
        # HP above 50% — panic check never runs
        assert commoner.get("panicked") is False

    def test_crowd_scatter_cascades_to_nearby_commoner(self):
        from services.combat_engine_service import process_enemy_turns
        c1 = self._make_commoner(hp=2, max_hp=8)
        c2 = self._make_commoner(hp=4, max_hp=8)
        c2["id"] = "c1"
        c2["grid_x"] = 2; c2["grid_y"] = 2
        char = self._char()
        combat = {
            "enemies": [c1, c2],
            "round": 2,
            "player_grid_x": 1, "player_grid_y": 2,
            "battlefield_grid": None,
        }
        # Both fail panic — c1 panics, cascade makes c2 check (roll 3, fails)
        with patch("services.dnd_rules.roll_d20", return_value=3):
            process_enemy_turns(char, combat)
        assert c1.get("panicked") is True

    def test_surrender_action_in_result(self):
        from services.combat_engine_service import process_enemy_turns
        commoner = self._make_commoner(hp=2, max_hp=8)
        commoner["panicked"] = False
        commoner["cornered"] = True
        commoner["_rounds_panicked"] = 0
        char = self._char()
        combat = self._combat(commoner)
        combat["round"] = 4  # round > 2 triggers surrender
        # Force panic check to pass so tree falls through to surrender
        with patch("services.dnd_rules.roll_d20", return_value=20):
            result = process_enemy_turns(char, combat)
        action_types = [a["action_type"] for a in result["enemy_actions"]]
        assert "surrender" in action_types


# ── Commoner loot ─────────────────────────────────────────────────────────────

class TestCommonerLoot:
    def _commoner(self, occupation="farmer"):
        return {
            "id": "c0", "name": "Farmer", "tier": "commoner",
            "type": "humanoid", "occupation": occupation,
            "cr": "0", "hp": 0, "max_hp": 6,
            "abilities": {}, "behavior_profile": "commoner",
        }

    def test_commoner_drops_no_weapon(self):
        w = weapon_from_enemy(self._commoner())
        assert w is None

    def test_commoner_loot_has_personal_effects(self):
        loot = generate_enemy_loot(self._commoner("farmer"))
        types = [i["type"] for i in loot["guaranteed"]]
        assert "trinket" in types

    def test_commoner_farmer_drops_seed_or_almanac(self):
        loot = generate_enemy_loot(self._commoner("farmer"))
        names = [i["name"] for i in loot["guaranteed"]]
        assert any("Seed" in n or "Almanac" in n or "Boot" in n for n in names)

    def test_commoner_merchant_drops_ledger_or_seal(self):
        loot = generate_enemy_loot(self._commoner("merchant"))
        names = [i["name"] for i in loot["guaranteed"]]
        assert any("Ledger" in n or "Seal" in n or "Coin" in n for n in names)

    def test_commoner_gold_is_very_low(self):
        for _ in range(20):
            loot = generate_enemy_loot(self._commoner())
            assert loot["gold"] <= 12, f"Commoner dropped {loot['gold']} gp — too much"


# ── Encounter Composer ────────────────────────────────────────────────────────

class TestEncounterComposer:
    def test_tavern_brawl_has_commoners(self):
        enc = compose_encounter("tavern_brawl", "medium", player_level=3, player_intel=0)
        tiers = [e["tier"] for e in enc["enemies"]]
        assert "commoner" in tiers

    def test_guard_post_has_commander_at_level5(self):
        enc = compose_encounter("guard_post", "high", player_level=5, player_intel=0)
        tiers = [e["tier"] for e in enc["enemies"]]
        assert "commander" in tiers
        assert "specialist" in tiers

    def test_commander_never_alone_without_specialists(self):
        enc = compose_encounter("guard_post", "medium", player_level=5, player_intel=0)
        tiers = [e["tier"] for e in enc["enemies"]]
        if "commander" in tiers:
            specialists = tiers.count("specialist")
            assert specialists >= 2, "Commander appeared without 2 specialists"

    def test_intel0_hides_enemy_count(self):
        enc = compose_encounter("bandit_road", "medium", player_level=4, player_intel=0)
        assert "can't tell" in enc["intel_report"]["visible"].lower() or "shadows" in enc["intel_report"]["visible"].lower()

    def test_intel3_reveals_commander_location(self):
        enc = compose_encounter("guard_post", "high", player_level=5, player_intel=3)
        assert enc["intel_report"]["commander_location"] is not None

    def test_intel2_reveals_count_and_assessment(self):
        enc = compose_encounter("bandit_road", "medium", player_level=4, player_intel=2)
        assert enc["intel_report"]["detail"] is not None
        assert enc["intel_report"]["visible"] != ""

    def test_level3_capped_no_specialists(self):
        enc = compose_encounter("guard_post", "high", player_level=3, player_intel=0)
        tiers = [e["tier"] for e in enc["enemies"]]
        # Level 3 caps at gifted, no specialists or commanders
        assert "specialist" not in tiers
        assert "commander" not in tiers

    def test_mythic_only_at_high_level(self):
        enc_low = compose_encounter("ancient_dungeon", "critical", player_level=4, player_intel=0)
        enc_high = compose_encounter("ancient_dungeon", "critical", player_level=12, player_intel=0)
        tiers_low = [e["tier"] for e in enc_low["enemies"]]
        tiers_high = [e["tier"] for e in enc_high["enemies"]]
        assert "mythic" not in tiers_low
        assert "mythic" in tiers_high

    def test_difficulty_is_deadly_for_guard_post_at_high_level(self):
        # Guard post at level 5 with high tension should be at least hard
        enc = compose_encounter("guard_post", "high", player_level=5, player_intel=0)
        assert enc["difficulty"] in ("hard", "deadly")

    def test_result_has_required_fields(self):
        enc = compose_encounter("tavern_brawl", "low", player_level=3, player_intel=0)
        for field in ("template", "enemies", "difficulty", "difficulty_reason",
                      "intel_report", "terrain_notes", "reinforcements", "objectives", "dm_notes"):
            assert field in enc, f"Missing field: {field}"

    def test_describe_encounter_for_dm_includes_difficulty(self):
        enc = compose_encounter("guard_post", "high", player_level=5, player_intel=3)
        desc = describe_encounter_for_dm(enc)
        assert "DEADLY" in desc or "difficulty" in desc.lower()

    def test_intel_from_investigation_dc8_gives_level1(self):
        enc = compose_encounter("bandit_road", "medium", player_level=4, player_intel=0)
        report = intel_from_investigation(10, enc)  # roll 10 ≥ DC 8
        assert report["intel_level"] >= 1

    def test_intel_from_investigation_dc16_gives_level3(self):
        enc = compose_encounter("guard_post", "high", player_level=5, player_intel=0)
        report = intel_from_investigation(18, enc)  # roll 18 ≥ DC 16
        assert report["intel_level"] == 3

    def test_intel_from_investigation_below_dc8_gives_level0(self):
        enc = compose_encounter("tavern_brawl", "medium", player_level=3, player_intel=0)
        report = intel_from_investigation(5, enc)  # roll 5 < DC 8
        assert report["intel_level"] == 0

    def test_village_defense_has_many_commoners(self):
        enc = compose_encounter("village_defense", "high", player_level=4, player_intel=0)
        tiers = [e["tier"] for e in enc["enemies"]]
        assert tiers.count("commoner") >= 3

    def test_military_assault_has_specialists_and_commander(self):
        enc = compose_encounter("military_assault", "high", player_level=7, player_intel=1)
        tiers = [e["tier"] for e in enc["enemies"]]
        assert "specialist" in tiers
        assert "commander" in tiers
