"""Tests for loot_service — weapon/armor/scroll/material derivation and loot generation."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch
from services.loot_service import (
    weapon_from_enemy,
    armor_from_enemy,
    scroll_from_enemy,
    material_from_enemy,
    gold_from_enemy,
    generate_enemy_loot,
    generate_combat_loot,
    apply_loot,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_enemy(**kwargs):
    base = {
        "id": "bandit",
        "name": "Bandit",
        "type": "humanoid",
        "damage_type": "slashing",
        "damage_die": "1d6",
        "attack_bonus": 3,
        "ac": 11,
        "cr": "1/8",
        "behavior_profile": "aggressive",
    }
    base.update(kwargs)
    return base


def make_char(**kwargs):
    base = {
        "inventory": [],
        "gold": 0,
        "abilities": {"int": 10},
        "class_": "fighter",
        "proficiency_bonus": 2,
    }
    base.update(kwargs)
    return base


# ── weapon_from_enemy ─────────────────────────────────────────────────────────

class TestWeaponFromEnemy:
    def test_slashing_1d6_returns_shortsword(self):
        w = weapon_from_enemy(make_enemy(damage_type="slashing", damage_die="1d6"))
        assert w is not None
        assert w["name"] == "Shortsword"
        assert w["type"] == "weapon"

    def test_longsword_1d8_slashing(self):
        w = weapon_from_enemy(make_enemy(damage_type="slashing", damage_die="1d8"))
        assert w["name"] == "Longsword"

    def test_greatsword_2d6_slashing(self):
        w = weapon_from_enemy(make_enemy(damage_type="slashing", damage_die="2d6"))
        assert w["name"] == "Greatsword"

    def test_fire_damage_gives_flaming_prefix(self):
        w = weapon_from_enemy(make_enemy(damage_type="fire", damage_die="1d8"))
        assert w is not None
        assert w["name"].startswith("Flaming")
        assert w["magic"] is True
        assert w["rarity"] == "uncommon"

    def test_cold_damage_gives_frost_prefix(self):
        w = weapon_from_enemy(make_enemy(damage_type="cold", damage_die="1d8"))
        assert w["name"].startswith("Frost")

    def test_lightning_damage_gives_thunderstrike(self):
        w = weapon_from_enemy(make_enemy(damage_type="lightning", damage_die="1d6"))
        assert w["name"].startswith("Thunderstrike")

    def test_magic_bonus_1_on_attack_bonus_6(self):
        w = weapon_from_enemy(make_enemy(damage_type="slashing", damage_die="1d8", attack_bonus=6))
        assert "+1" in w["name"]
        assert w["magic_bonus"] == 1
        assert w["magic"] is True

    def test_magic_bonus_2_on_attack_bonus_8(self):
        w = weapon_from_enemy(make_enemy(damage_type="fire", damage_die="1d8", attack_bonus=8))
        assert "+2" in w["name"]
        assert w["magic_bonus"] == 2
        assert w["rarity"] == "rare"

    def test_magic_bonus_3_on_attack_bonus_10(self):
        w = weapon_from_enemy(make_enemy(damage_type="slashing", damage_die="1d8", attack_bonus=10))
        assert "+3" in w["name"]
        assert w["magic_bonus"] == 3

    def test_no_weapon_for_wolf(self):
        w = weapon_from_enemy(make_enemy(id="wolf", type="beast"))
        assert w is None

    def test_no_weapon_for_zombie(self):
        w = weapon_from_enemy(make_enemy(id="zombie", behavior_profile="undead_mindless"))
        assert w is None

    def test_skeleton_gets_corroded_suffix(self):
        w = weapon_from_enemy(make_enemy(id="skeleton", damage_type="slashing", damage_die="1d6"))
        assert "(Corroded)" in w["name"]

    def test_beast_type_returns_none(self):
        w = weapon_from_enemy(make_enemy(type="beast"))
        assert w is None

    def test_damage_die_with_plus_stripped(self):
        # "1d8+3" should be treated as "1d8"
        w = weapon_from_enemy(make_enemy(damage_type="slashing", damage_die="1d8+3"))
        assert w is not None
        assert w["damage_die"] == "1d8"

    def test_piercing_rapier(self):
        w = weapon_from_enemy(make_enemy(damage_type="piercing", damage_die="1d8"))
        assert w["name"] == "Rapier"

    def test_bludgeoning_warhammer(self):
        w = weapon_from_enemy(make_enemy(damage_type="bludgeoning", damage_die="1d8"))
        assert w["name"] == "Warhammer"

    def test_source_is_looted(self):
        w = weapon_from_enemy(make_enemy())
        assert w["source"] == "looted"

    def test_quantity_one(self):
        w = weapon_from_enemy(make_enemy())
        assert w["quantity"] == 1


# ── armor_from_enemy ──────────────────────────────────────────────────────────

class TestArmorFromEnemy:
    def test_low_ac_returns_none(self):
        assert armor_from_enemy(make_enemy(ac=12)) is None

    def test_ac13_leather(self):
        a = armor_from_enemy(make_enemy(ac=13))
        assert a is not None
        assert a["name"] == "Leather Armor"

    def test_ac15_chain_shirt(self):
        a = armor_from_enemy(make_enemy(ac=15))
        assert "Chain Shirt" in a["name"]

    def test_ac17_scale_mail(self):
        a = armor_from_enemy(make_enemy(ac=17))
        assert "Scale Mail" in a["name"]

    def test_ac19_plate_armor(self):
        a = armor_from_enemy(make_enemy(ac=19))
        assert a["name"] == "Plate Armor"
        assert a["value"] == 1500
        assert a["rarity"] == "uncommon"

    def test_ac21_mithral_plate(self):
        a = armor_from_enemy(make_enemy(ac=21))
        assert "Mithral" in a["name"]
        assert a["value"] == 5000
        assert a["rarity"] == "rare"

    def test_non_humanoid_returns_none(self):
        assert armor_from_enemy(make_enemy(type="beast", ac=18)) is None

    def test_armor_type_field(self):
        a = armor_from_enemy(make_enemy(ac=16))
        assert a["type"] == "armor"


# ── scroll_from_enemy ─────────────────────────────────────────────────────────

class TestScrollFromEnemy:
    def test_spellcaster_with_spell_list(self):
        e = make_enemy(behavior_profile="spellcaster", spell_list=["magic_missile", "fireball"])
        s = scroll_from_enemy(e)
        assert s is not None
        assert "Fireball" in s["name"]
        assert s["type"] == "consumable"

    def test_spellcaster_no_spell_list_returns_unknown(self):
        e = make_enemy(behavior_profile="spellcaster", spell_list=[])
        s = scroll_from_enemy(e)
        assert s is not None
        assert "Unknown" in s["name"]

    def test_non_caster_returns_none(self):
        e = make_enemy(behavior_profile="aggressive")
        assert scroll_from_enemy(e) is None

    def test_enemy_with_spell_list_is_treated_as_caster(self):
        e = make_enemy(behavior_profile="aggressive", spell_list=["cure_wounds"])
        s = scroll_from_enemy(e)
        assert s is not None
        assert "Cure Wounds" in s["name"]


# ── material_from_enemy ───────────────────────────────────────────────────────

class TestMaterialFromEnemy:
    def test_wolf_drops_pelt(self):
        m = material_from_enemy(make_enemy(id="wolf"))
        assert m is not None
        assert "Pelt" in m["name"]
        assert m["type"] == "material"

    def test_bear_drops_hide(self):
        m = material_from_enemy(make_enemy(id="bear"))
        assert "Hide" in m["name"]

    def test_dragon_drops_scale(self):
        m = material_from_enemy(make_enemy(id="young_dragon"))
        assert "Scale" in m["name"]
        assert m["value"] == 250

    def test_bandit_drops_nothing(self):
        assert material_from_enemy(make_enemy(id="bandit")) is None


# ── gold_from_enemy ───────────────────────────────────────────────────────────

class TestGoldFromEnemy:
    def test_cr_0_low_gold(self):
        g = gold_from_enemy(make_enemy(cr="0"))
        assert 0 <= g <= 5

    def test_cr_1_reasonable_gold(self):
        for _ in range(20):
            g = gold_from_enemy(make_enemy(cr="1"))
            assert 30 <= g <= 100

    def test_cr_5_large_gold(self):
        g = gold_from_enemy(make_enemy(cr="5"))
        assert 300 <= g <= 800

    def test_unknown_cr_uses_fallback(self):
        g = gold_from_enemy(make_enemy(cr="99"))
        assert g >= 0


# ── generate_enemy_loot ───────────────────────────────────────────────────────

class TestGenerateEnemyLoot:
    def test_guaranteed_has_weapon_for_humanoid(self):
        loot = generate_enemy_loot(make_enemy())
        names = [i["name"] for i in loot["guaranteed"]]
        assert any("Shortsword" in n or "Longsword" in n or "Dagger" in n for n in names)

    def test_gold_always_present(self):
        loot = generate_enemy_loot(make_enemy())
        assert loot["gold"] >= 0

    def test_no_investigation_means_no_hidden(self):
        loot = generate_enemy_loot(make_enemy(), investigation_total=None)
        assert loot["hidden"] == []
        assert loot["searched"] is False

    def test_low_investigation_reveals_only_basic_item(self):
        loot = generate_enemy_loot(make_enemy(cr="1"), investigation_total=13)
        assert len(loot["hidden"]) == 1

    def test_high_investigation_reveals_all_hidden(self):
        loot = generate_enemy_loot(make_enemy(cr="1"), investigation_total=18)
        assert len(loot["hidden"]) >= 2

    def test_too_low_investigation_reveals_nothing(self):
        loot = generate_enemy_loot(make_enemy(cr="1"), investigation_total=5)
        assert loot["hidden"] == []

    def test_flaming_sword_for_fire_enemy(self):
        enemy = make_enemy(damage_type="fire", damage_die="1d8", attack_bonus=5)
        loot = generate_enemy_loot(enemy)
        names = [i["name"] for i in loot["guaranteed"]]
        assert any("Flaming" in n for n in names)

    def test_result_fields_present(self):
        loot = generate_enemy_loot(make_enemy())
        for field in ("enemy_id", "enemy_name", "guaranteed", "hidden", "gold", "searched"):
            assert field in loot

    def test_wolf_drops_material_not_weapon(self):
        enemy = make_enemy(id="wolf", type="beast")
        loot = generate_enemy_loot(enemy)
        types = [i["type"] for i in loot["guaranteed"]]
        assert "material" in types
        assert "weapon" not in types


# ── generate_combat_loot ──────────────────────────────────────────────────────

class TestGenerateCombatLoot:
    def test_returns_one_entry_per_enemy(self):
        enemies = [make_enemy(id="bandit", name="Bandit"), make_enemy(id="guard", name="Guard")]
        char = make_char()
        with patch("services.dnd_rules.roll_d20", return_value=15):
            results = generate_combat_loot(enemies, char)
        assert len(results) == 2

    def test_wizard_gets_investigation_proficiency(self):
        char = make_char(class_="wizard", abilities={"int": 18}, proficiency_bonus=3)
        enemies = [make_enemy(cr="5")]
        with patch("services.dnd_rules.roll_d20", return_value=1):
            results = generate_combat_loot(enemies, char)
        # INT mod +4 + prof +3 + roll 1 = 8 → above DC 12 but below 16
        assert results[0]["investigation_total"] == 8

    def test_investigation_roll_attached_to_result(self):
        char = make_char()
        enemies = [make_enemy()]
        with patch("services.dnd_rules.roll_d20", return_value=12):
            results = generate_combat_loot(enemies, char)
        assert results[0]["investigation_roll"] == 12


# ── apply_loot ────────────────────────────────────────────────────────────────

class TestApplyLoot:
    def _loot_result(self):
        return {
            "enemy_id": "bandit",
            "enemy_name": "Bandit",
            "guaranteed": [
                {"name": "Shortsword", "type": "weapon", "quantity": 1, "source": "looted",
                 "equipped": False, "value": 10, "rarity": "common"},
            ],
            "hidden": [
                {"name": "Healing Potion", "type": "consumable", "quantity": 1, "source": "looted",
                 "equipped": False, "value": 50, "rarity": "common"},
            ],
            "gold": 45,
        }

    def test_take_all_adds_all_items(self):
        char = make_char(gold=10)
        patch = apply_loot([self._loot_result()], char)
        assert "Shortsword" in patch["_items_added"]
        assert "Healing Potion" in patch["_items_added"]
        assert patch["gold"] == 55

    def test_take_specific_item_only(self):
        char = make_char(gold=0)
        patch = apply_loot([self._loot_result()], char, take_item_names=["Shortsword"])
        assert "Shortsword" in patch["_items_added"]
        assert "Healing Potion" not in patch["_items_added"]

    def test_gold_always_added(self):
        char = make_char(gold=100)
        patch = apply_loot([self._loot_result()], char)
        assert patch["gold"] == 145
        assert patch["_gold_added"] == 45

    def test_items_appended_to_existing_inventory(self):
        existing = [{"name": "Torch", "type": "item"}]
        char = make_char(inventory=existing)
        patch = apply_loot([self._loot_result()], char)
        names = [i["name"] for i in patch["inventory"]]
        assert "Torch" in names
        assert "Shortsword" in names

    def test_empty_loot_returns_unchanged_inventory(self):
        char = make_char(gold=50, inventory=[])
        patch = apply_loot([], char)
        assert patch["inventory"] == []
        assert patch["gold"] == 50
        assert patch["_items_added"] == []
        assert patch["_gold_added"] == 0
