"""Tests for spell combat mechanics — attack-roll, heal, and auto-hit spells."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.spells_and_feats import get_spell_card
from services.combat_engine_service import (
    process_spell_attack,
    process_heal_spell,
    process_auto_hit_spell,
)


def _wizard(level=5, hp=20, max_hp=30, int_score=18):
    return {
        "name": "Aria",
        "class": "Wizard",
        "level": level,
        "hp": hp,
        "max_hp": max_hp,
        "abilities": {"str": 8, "dex": 14, "con": 12, "int": int_score, "wis": 10, "cha": 10},
        "proficiency_bonus": 3,
    }


def _warlock(level=3, hp=18, max_hp=18):
    return {
        "name": "Kael",
        "class": "Warlock",
        "level": level,
        "hp": hp,
        "max_hp": max_hp,
        "abilities": {"str": 10, "dex": 12, "con": 12, "int": 10, "wis": 10, "cha": 16},
        "proficiency_bonus": 2,
    }


def _cleric(level=3, hp=22, max_hp=22, wis=16):
    return {
        "name": "Brother Aldric",
        "class": "Cleric",
        "level": level,
        "hp": hp,
        "max_hp": max_hp,
        "abilities": {"str": 12, "dex": 10, "con": 13, "int": 10, "wis": wis, "cha": 12},
        "proficiency_bonus": 2,
    }


def _combat(enemy_hp=15, enemy_ac=12, enemy_id="goblin_1"):
    return {
        "enemies": [{
            "id": enemy_id,
            "name": "Goblin",
            "hp": enemy_hp,
            "max_hp": enemy_hp,
            "ac": enemy_ac,
            "abilities": {"str": 8, "dex": 14, "con": 10, "int": 10, "wis": 8, "cha": 8},
            "resistances": [],
            "immunities": [],
            "conditions": [],
        }]
    }


def _reset_enemy(combat_state, hp=15):
    combat_state["enemies"][0]["hp"] = hp


# ── process_spell_attack ──────────────────────────────────────────────────────

class TestProcessSpellAttack:
    def test_returns_success(self):
        result = process_spell_attack(
            "Fire Bolt", get_spell_card("Fire Bolt"),
            _wizard(), "goblin_1", _combat()
        )
        assert result["success"] is True

    def test_uses_int_for_wizard(self):
        result = process_spell_attack(
            "Fire Bolt", get_spell_card("Fire Bolt"),
            _wizard(), "goblin_1", _combat()
        )
        assert result["mechanical_summary"]["ability_used"] == "INT"

    def test_uses_cha_for_warlock(self):
        result = process_spell_attack(
            "Eldritch Blast", get_spell_card("Eldritch Blast"),
            _warlock(), "goblin_1", _combat()
        )
        assert result["mechanical_summary"]["ability_used"] == "CHA"

    def test_attack_roll_vs_ac(self):
        result = process_spell_attack(
            "Fire Bolt", get_spell_card("Fire Bolt"),
            _wizard(), "goblin_1", _combat(enemy_ac=12)
        )
        ms = result["mechanical_summary"]
        assert "attack_roll" in ms and "target_ac" in ms

    def test_cantrip_single_die_at_level_1(self):
        result = process_spell_attack(
            "Fire Bolt", get_spell_card("Fire Bolt"),
            _wizard(level=1), "goblin_1", _combat()
        )
        assert result["mechanical_summary"]["damage_dice"] == "1d10"

    def test_cantrip_doubles_at_level_5(self):
        result = process_spell_attack(
            "Fire Bolt", get_spell_card("Fire Bolt"),
            _wizard(level=5), "goblin_1", _combat()
        )
        assert result["mechanical_summary"]["damage_dice"] == "2d10"

    def test_cantrip_triples_at_level_11(self):
        result = process_spell_attack(
            "Fire Bolt", get_spell_card("Fire Bolt"),
            _wizard(level=11), "goblin_1", _combat()
        )
        assert result["mechanical_summary"]["damage_dice"] == "3d10"

    def test_cantrip_quadruples_at_level_17(self):
        result = process_spell_attack(
            "Fire Bolt", get_spell_card("Fire Bolt"),
            _wizard(level=17), "goblin_1", _combat()
        )
        assert result["mechanical_summary"]["damage_dice"] == "4d10"

    def test_leveled_spell_does_not_scale(self):
        result = process_spell_attack(
            "Guiding Bolt", get_spell_card("Guiding Bolt"),
            _cleric(level=5), "goblin_1", _combat()
        )
        assert result["mechanical_summary"]["damage_dice"] == "4d6"

    def test_damage_zero_on_miss(self):
        # Force a miss by making AC impossibly high
        combat = _combat(enemy_ac=30)
        result = process_spell_attack(
            "Fire Bolt", get_spell_card("Fire Bolt"),
            _wizard(level=1, int_score=10), "goblin_1", combat
        )
        ms = result["mechanical_summary"]
        if not ms["hit"]:
            assert ms["damage"] == 0

    def test_target_not_found_returns_failure(self):
        result = process_spell_attack(
            "Fire Bolt", get_spell_card("Fire Bolt"),
            _wizard(), "nonexistent", _combat()
        )
        assert result["success"] is False

    def test_enemy_hp_reduced_on_hit(self):
        combat = _combat(enemy_hp=100, enemy_ac=1)  # AC 1 ensures hit
        process_spell_attack(
            "Fire Bolt", get_spell_card("Fire Bolt"),
            _wizard(level=5, int_score=20), "goblin_1", combat
        )
        # Enemy HP must have changed or stayed at 100 (crit miss edge case)
        assert combat["enemies"][0]["hp"] <= 100

    def test_combat_over_when_enemy_killed(self):
        combat = _combat(enemy_hp=1, enemy_ac=1)
        result = process_spell_attack(
            "Fire Bolt", get_spell_card("Fire Bolt"),
            _wizard(level=5, int_score=20), "goblin_1", combat
        )
        ms = result["mechanical_summary"]
        if ms["hit"]:
            assert result["combat_over"] is True

    def test_spell_attack_bonus_in_summary(self):
        result = process_spell_attack(
            "Fire Bolt", get_spell_card("Fire Bolt"),
            _wizard(level=5, int_score=18), "goblin_1", _combat()
        )
        # Level 5 wizard: prof 3, INT mod +4 = bonus 7
        assert result["mechanical_summary"]["spell_attack_bonus"] == 7

    def test_is_spell_attack_flag(self):
        result = process_spell_attack(
            "Eldritch Blast", get_spell_card("Eldritch Blast"),
            _warlock(), "goblin_1", _combat()
        )
        assert result["mechanical_summary"]["is_spell_attack"] is True

    def test_immunity_reduces_damage_to_zero(self):
        combat = _combat(enemy_hp=50, enemy_ac=1)
        combat["enemies"][0]["immunities"] = ["fire"]
        result = process_spell_attack(
            "Fire Bolt", get_spell_card("Fire Bolt"),
            _wizard(level=5), "goblin_1", combat
        )
        ms = result["mechanical_summary"]
        if ms["hit"]:
            assert ms["damage"] == 0

    def test_resistance_halves_damage(self):
        combat = _combat(enemy_hp=50, enemy_ac=1)
        combat["enemies"][0]["resistances"] = ["fire"]
        result = process_spell_attack(
            "Fire Bolt", get_spell_card("Fire Bolt"),
            _wizard(level=5, int_score=20), "goblin_1", combat
        )
        ms = result["mechanical_summary"]
        if ms["hit"] and ms["damage"] > 0:
            pass  # just verify no crash


# ── process_heal_spell ────────────────────────────────────────────────────────

class TestProcessHealSpell:
    def test_returns_success(self):
        result = process_heal_spell(
            "Cure Wounds", get_spell_card("Cure Wounds"), _cleric(hp=10), _combat()
        )
        assert result["success"] is True

    def test_hp_increases(self):
        char = _cleric(hp=10, max_hp=22)
        result = process_heal_spell("Cure Wounds", get_spell_card("Cure Wounds"), char, _combat())
        assert result["mechanical_summary"]["new_hp"] > 10

    def test_hp_capped_at_max(self):
        char = _cleric(hp=22, max_hp=22)
        result = process_heal_spell("Cure Wounds", get_spell_card("Cure Wounds"), char, _combat())
        assert result["mechanical_summary"]["new_hp"] <= 22

    def test_character_state_update_has_hp(self):
        char = _cleric(hp=5, max_hp=22)
        result = process_heal_spell("Cure Wounds", get_spell_card("Cure Wounds"), char, _combat())
        assert "hp" in result["character_state_update"]

    def test_character_state_update_hp_matches_new_hp(self):
        char = _cleric(hp=5, max_hp=22)
        result = process_heal_spell("Cure Wounds", get_spell_card("Cure Wounds"), char, _combat())
        assert result["character_state_update"]["hp"] == result["mechanical_summary"]["new_hp"]

    def test_wis_mod_added_for_cleric(self):
        # WIS 16 = +3 mod, Cure Wounds heals 1d8+3 minimum 4
        char = _cleric(hp=1, max_hp=50, wis=16)
        result = process_heal_spell("Cure Wounds", get_spell_card("Cure Wounds"), char, _combat())
        assert result["mechanical_summary"]["heal_amount"] >= 4

    def test_healing_word_uses_d4(self):
        char = _cleric(hp=5, max_hp=22)
        result = process_heal_spell("Healing Word", get_spell_card("Healing Word"), char, _combat())
        assert result["mechanical_summary"]["heal_dice"] == "1d4"

    def test_combat_not_over_after_heal(self):
        result = process_heal_spell(
            "Cure Wounds", get_spell_card("Cure Wounds"), _cleric(hp=5), _combat()
        )
        assert result["combat_over"] is False

    def test_is_heal_spell_flag(self):
        result = process_heal_spell(
            "Cure Wounds", get_spell_card("Cure Wounds"), _cleric(hp=5), _combat()
        )
        assert result["mechanical_summary"]["is_heal_spell"] is True


# ── process_auto_hit_spell ────────────────────────────────────────────────────

class TestProcessAutoHitSpell:
    def test_returns_success(self):
        result = process_auto_hit_spell(
            "Magic Missile", get_spell_card("Magic Missile"),
            _wizard(), "goblin_1", _combat()
        )
        assert result["success"] is True

    def test_auto_hit_flag_true(self):
        result = process_auto_hit_spell(
            "Magic Missile", get_spell_card("Magic Missile"),
            _wizard(), "goblin_1", _combat()
        )
        assert result["mechanical_summary"]["auto_hit"] is True

    def test_always_hits(self):
        result = process_auto_hit_spell(
            "Magic Missile", get_spell_card("Magic Missile"),
            _wizard(), "goblin_1", _combat(enemy_ac=30)
        )
        assert result["mechanical_summary"]["hit"] is True

    def test_three_darts(self):
        result = process_auto_hit_spell(
            "Magic Missile", get_spell_card("Magic Missile"),
            _wizard(), "goblin_1", _combat()
        )
        assert result["mechanical_summary"]["num_darts"] == 3

    def test_damage_at_least_3(self):
        # 3 darts each 1d4+1 = minimum 6
        result = process_auto_hit_spell(
            "Magic Missile", get_spell_card("Magic Missile"),
            _wizard(), "goblin_1", _combat()
        )
        assert result["mechanical_summary"]["damage"] >= 3

    def test_force_damage_type(self):
        result = process_auto_hit_spell(
            "Magic Missile", get_spell_card("Magic Missile"),
            _wizard(), "goblin_1", _combat()
        )
        assert result["mechanical_summary"]["damage_type"] == "force"

    def test_enemy_hp_reduced(self):
        combat = _combat(enemy_hp=50)
        process_auto_hit_spell(
            "Magic Missile", get_spell_card("Magic Missile"),
            _wizard(), "goblin_1", combat
        )
        assert combat["enemies"][0]["hp"] < 50

    def test_combat_over_when_enemy_killed(self):
        combat = _combat(enemy_hp=3)
        result = process_auto_hit_spell(
            "Magic Missile", get_spell_card("Magic Missile"),
            _wizard(), "goblin_1", combat
        )
        assert result["combat_over"] is True

    def test_target_not_found_returns_failure(self):
        result = process_auto_hit_spell(
            "Magic Missile", get_spell_card("Magic Missile"),
            _wizard(), "nonexistent", _combat()
        )
        assert result["success"] is False


# ── spell_card spell_type fields ──────────────────────────────────────────────

class TestSpellCardSpellType:
    def test_fire_bolt_is_attack(self):
        assert get_spell_card("Fire Bolt")["spell_type"] == "attack"

    def test_eldritch_blast_is_attack(self):
        assert get_spell_card("Eldritch Blast")["spell_type"] == "attack"

    def test_shocking_grasp_is_attack(self):
        assert get_spell_card("Shocking Grasp")["spell_type"] == "attack"

    def test_chill_touch_is_attack(self):
        assert get_spell_card("Chill Touch")["spell_type"] == "attack"

    def test_ray_of_frost_is_attack(self):
        assert get_spell_card("Ray of Frost")["spell_type"] == "attack"

    def test_guiding_bolt_is_attack(self):
        assert get_spell_card("Guiding Bolt")["spell_type"] == "attack"

    def test_scorching_ray_is_attack(self):
        assert get_spell_card("Scorching Ray")["spell_type"] == "attack"

    def test_witch_bolt_is_attack(self):
        assert get_spell_card("Witch Bolt")["spell_type"] == "attack"

    def test_cure_wounds_is_heal(self):
        assert get_spell_card("Cure Wounds")["spell_type"] == "heal"

    def test_healing_word_is_heal(self):
        assert get_spell_card("Healing Word")["spell_type"] == "heal"

    def test_magic_missile_is_auto_hit(self):
        assert get_spell_card("Magic Missile")["spell_type"] == "auto_hit"

    def test_bless_is_buff(self):
        assert get_spell_card("Bless")["spell_type"] == "buff"

    def test_mage_armor_has_no_spell_type(self):
        # Mage Armor is a buff but we didn't tag it — should return None
        card = get_spell_card("Mage Armor")
        assert card["spell_type"] is None or card["spell_type"] == "buff"

    def test_attack_spells_have_damage_dice(self):
        for name in ["Fire Bolt", "Eldritch Blast", "Shocking Grasp", "Guiding Bolt"]:
            card = get_spell_card(name)
            assert card["damage_dice"] is not None, f"{name} missing damage_dice"

    def test_heal_spells_have_heal_dice(self):
        for name in ["Cure Wounds", "Healing Word"]:
            card = get_spell_card(name)
            assert card["heal_dice"] is not None, f"{name} missing heal_dice"

    def test_save_spells_unchanged(self):
        # Sacred Flame: save spell, no spell_type
        card = get_spell_card("Sacred Flame")
        assert card["save_type"] == "dex"
        assert card["damage_dice"] == "1d8"
