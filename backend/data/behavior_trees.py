"""
Pre-built Behavior Trees for D&D 5e enemy archetypes.

Each entry follows the schema:
  {
    "id": str,
    "name": str,
    "description": str,
    "node": dict   # root BT node
  }

Stored in DEFAULT_TREES keyed by tree_id.
"""
from __future__ import annotations
from typing import Dict, Any

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS (shorthand constructors — NOT stored in dicts, only used here)
# ──────────────────────────────────────────────────────────────────────────────

def _sel(*children): return {"type": "selector", "children": list(children)}
def _seq(*children): return {"type": "sequence", "children": list(children)}
def _not(child): return {"type": "not", "child": child}
def _cond(check, value=None):
    n = {"type": "condition", "check": check}
    if value is not None:
        n["value"] = value
    return n


# ══════════════════════════════════════════════════════════════════════════════
# DEFAULT TREES
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_TREES: Dict[str, Dict[str, Any]] = {

    # ─────────────────────────────────────────────────────────────────────────
    # GOBLIN — Skirmisher: Nimble Escape to flee when hurt, attack in melee
    # ─────────────────────────────────────────────────────────────────────────
    "goblin": {
        "id": "goblin",
        "name": "Goblin",
        "description": "Skirmisher. Flees below 25% HP using Nimble Escape. Attacks with scimitar in melee. Moves toward player otherwise.",
        "node": _sel(
            # Flee when critically wounded
            _seq(
                _cond("hp_below", 0.25),
                {"type": "action", "action": "flee", "label": "Nimble Escape"},
            ),
            # Attack in melee
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "1d6+2", "damage_type": "slashing", "label": "Scimitar"},
            ),
            # Default: close the gap
            {"type": "action", "action": "move_toward_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # SKELETON — Mindless undead: always attacks, never retreats
    # ─────────────────────────────────────────────────────────────────────────
    "skeleton": {
        "id": "skeleton",
        "name": "Skeleton",
        "description": "Mindless undead. Always attacks the nearest enemy. Uses shortsword or shortbow.",
        "node": _sel(
            # In melee: shortsword
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "1d6+2", "damage_type": "piercing", "label": "Shortsword"},
            ),
            # At range: shortbow
            {"type": "action", "action": "attack_ranged",
             "damage_die": "1d6+2", "damage_type": "piercing", "range_ft": 80,
             "label": "Shortbow"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # ZOMBIE — Mindless: slam, Undead Fortitude
    # ─────────────────────────────────────────────────────────────────────────
    "zombie": {
        "id": "zombie",
        "name": "Zombie",
        "description": "Mindless undead. Slams the nearest foe. Undead Fortitude may negate a killing blow.",
        "node": _sel(
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "1d6+1", "damage_type": "bludgeoning",
                 "special_effect": "undead_fortitude", "label": "Slam"},
            ),
            {"type": "action", "action": "move_toward_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # WOLF — Pack Tactics: advantage when ally adjacent, trip on hit
    # ─────────────────────────────────────────────────────────────────────────
    "wolf": {
        "id": "wolf",
        "name": "Wolf",
        "description": "Pack predator. Uses Pack Tactics for advantage when an ally is adjacent. Bite may trip target.",
        "node": _sel(
            # Pack Tactics attack
            _seq(
                _cond("ally_adjacent"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "2d4+2", "damage_type": "piercing",
                 "advantage": True, "special_effect": "trip",
                 "label": "Bite (Pack Tactics)", "adv_reason": "Pack Tactics"},
            ),
            # Normal bite
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "2d4+2", "damage_type": "piercing",
                 "special_effect": "trip", "label": "Bite"},
            ),
            {"type": "action", "action": "move_toward_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # ORC — Berserker: Aggressive charge, Reckless below 50% HP
    # ─────────────────────────────────────────────────────────────────────────
    "orc": {
        "id": "orc",
        "name": "Orc",
        "description": "Aggressive berserker. Charges in immediately. Goes Reckless when below 50% HP.",
        "node": _sel(
            # Reckless when bloodied
            _seq(
                _cond("hp_below", 0.5),
                {"type": "action", "action": "reckless_attack"},
            ),
            # Normal greataxe attack
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "1d12+3", "damage_type": "slashing", "label": "Greataxe"},
            ),
            {"type": "action", "action": "move_toward_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # GNOLL — Pack hunter: Pack Tactics + Rampage (bonus bite after kill)
    # ─────────────────────────────────────────────────────────────────────────
    "gnoll": {
        "id": "gnoll",
        "name": "Gnoll",
        "description": "Pack hunter with Rampage. Advantage via Pack Tactics when allies are adjacent. Targets wounded prey.",
        "node": _sel(
            # Pack Tactics
            _seq(
                _cond("ally_adjacent"),
                _cond("in_melee_range"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "2d4+2", "damage_type": "piercing",
                 "advantage": True, "label": "Spear (Pack Tactics)", "adv_reason": "Pack Tactics"},
            ),
            # Normal attack
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "2d4+2", "damage_type": "piercing", "label": "Spear"},
            ),
            {"type": "action", "action": "move_toward_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # BUGBEAR — Ambusher: Surprise Attack bonus on first round, then normal
    # ─────────────────────────────────────────────────────────────────────────
    "bugbear": {
        "id": "bugbear",
        "name": "Bugbear",
        "description": "Ambush predator. Deals Surprise Attack bonus damage on the first round. Repositions below 50% HP.",
        "node": _sel(
            # First round: Surprise Attack (always in melee)
            _seq(
                _cond("is_first_round"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "2d8+2", "damage_type": "piercing",
                 "advantage": True, "special_effect": "surprise_attack",
                 "label": "Surprise Attack", "adv_reason": "Ambush"},
            ),
            # Bloodied: reposition
            _seq(
                _cond("hp_below", 0.5),
                {"type": "action", "action": "move_to_cover", "label": "Reposition"},
            ),
            # Normal attack
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "2d8+2", "damage_type": "piercing", "label": "Morningstar"},
            ),
            {"type": "action", "action": "move_toward_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # GHOUL — Paralyzing Claw + Bite multiattack
    # ─────────────────────────────────────────────────────────────────────────
    "ghoul": {
        "id": "ghoul",
        "name": "Ghoul",
        "description": "Ravenous undead. Multiattack with paralyzing Claws and Bite. Prioritizes paralyzed targets.",
        "node": _sel(
            # If player is paralyzed, advantage on bite
            _seq(
                _cond("player_has_condition", "paralyzed"),
                _cond("in_melee_range"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "2d8+2", "damage_type": "piercing",
                 "advantage": True, "label": "Bite (Paralyzed prey)", "adv_reason": "Target is paralyzed"},
            ),
            # Normal multiattack
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "multiattack",
                 "attacks": [
                     {"name": "Bite", "damage_die": "2d6+2", "damage_type": "piercing"},
                     {"name": "Claw", "damage_die": "2d4+2", "damage_type": "slashing"},
                 ],
                 "label": "Multiattack"},
            ),
            {"type": "action", "action": "move_toward_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # SHADOW — Strength Drain, stays mobile
    # ─────────────────────────────────────────────────────────────────────────
    "shadow": {
        "id": "shadow",
        "name": "Shadow",
        "description": "Living shadow that drains Strength. Flanks and drains; never retreats.",
        "node": _sel(
            # Ally adjacent: advantage attack with strength drain
            _seq(
                _cond("ally_adjacent"),
                _cond("in_melee_range"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "2d6+2", "damage_type": "necrotic",
                 "advantage": True, "special_effect": "strength_drain",
                 "label": "Strength Drain (flanking)", "adv_reason": "Flanking"},
            ),
            # Normal strength drain
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "2d6+2", "damage_type": "necrotic",
                 "special_effect": "strength_drain", "label": "Strength Drain"},
            ),
            {"type": "action", "action": "move_toward_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # ORC BERSERKER — Pure Reckless Attack every turn
    # ─────────────────────────────────────────────────────────────────────────
    "orc_berserker": {
        "id": "orc_berserker",
        "name": "Orc Berserker",
        "description": "Battle-mad orc. Always Reckless Attacks — gains advantage but grants it to enemies too.",
        "node": _sel(
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "reckless_attack"},
            ),
            {"type": "action", "action": "move_toward_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # TROLL — Regeneration (suppressed by fire/acid), Multiattack
    # ─────────────────────────────────────────────────────────────────────────
    "troll": {
        "id": "troll",
        "name": "Troll",
        "description": "Regenerates 10 HP/turn unless it took fire or acid damage. Multiattacks with Bite and 2 Claws.",
        "node": _sel(
            # Regenerate if bloodied AND didn't take fire/acid damage
            _seq(
                _cond("hp_below", 0.7),
                _not(_cond("took_fire_damage")),
                _not(_cond("took_acid_damage")),
                {"type": "action", "action": "regenerate", "amount": 10, "label": "Regeneration"},
            ),
            # Multiattack: bite + 2 claws
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "multiattack",
                 "attacks": [
                     {"name": "Bite", "damage_die": "1d6+4", "damage_type": "piercing"},
                     {"name": "Claw", "damage_die": "1d6+4", "damage_type": "slashing"},
                     {"name": "Claw", "damage_die": "1d6+4", "damage_type": "slashing"},
                 ],
                 "label": "Multiattack"},
            ),
            {"type": "action", "action": "move_toward_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # OGRE — Dumb brute: charge and club
    # ─────────────────────────────────────────────────────────────────────────
    "ogre": {
        "id": "ogre",
        "name": "Ogre",
        "description": "Massive dim-witted giant. Always charges and smashes with its greatclub.",
        "node": _sel(
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "2d8+4", "damage_type": "bludgeoning", "label": "Greatclub"},
            ),
            {"type": "action", "action": "move_toward_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # MINOTAUR — Reckless charge, multiattack
    # ─────────────────────────────────────────────────────────────────────────
    "minotaur": {
        "id": "minotaur",
        "name": "Minotaur",
        "description": "Charges to gore with Reckless Attack. Multiattacks (Greataxe + Gore) when adjacent.",
        "node": _sel(
            # Reckless multiattack
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "multiattack",
                 "attacks": [
                     {"name": "Greataxe", "damage_die": "2d12+4", "damage_type": "slashing"},
                     {"name": "Gore", "damage_die": "2d8+4", "damage_type": "piercing"},
                 ],
                 "label": "Reckless Multiattack"},
            ),
            # Charge from range
            {"type": "action", "action": "move_toward_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # WIGHT — Life Drain, multiattack, never retreats
    # ─────────────────────────────────────────────────────────────────────────
    "wight": {
        "id": "wight",
        "name": "Wight",
        "description": "Cunning undead warrior. Life Drain reduces max HP. Multiattacks with Longsword + Life Drain.",
        "node": _sel(
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "multiattack",
                 "attacks": [
                     {"name": "Longsword", "damage_die": "1d8+2", "damage_type": "slashing"},
                     {"name": "Life Drain", "damage_die": "2d6+2", "damage_type": "necrotic"},
                 ],
                 "label": "Multiattack"},
            ),
            {"type": "action", "action": "move_toward_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # VAMPIRE SPAWN — Regen (suppressed by radiant), Life Drain multiattack
    # ─────────────────────────────────────────────────────────────────────────
    "vampire_spawn": {
        "id": "vampire_spawn",
        "name": "Vampire Spawn",
        "description": "Regenerates 10 HP/turn unless it took radiant damage. Multiattacks with Claws and Bite (Life Drain).",
        "node": _sel(
            # Regenerate if bloodied and not suppressed (we treat fire as radiant analog here)
            _seq(
                _cond("hp_below", 0.8),
                _not(_cond("took_fire_damage")),
                {"type": "action", "action": "regenerate", "amount": 10, "label": "Regeneration"},
            ),
            # Multiattack
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "multiattack",
                 "attacks": [
                     {"name": "Claws", "damage_die": "2d4+3", "damage_type": "slashing"},
                     {"name": "Bite (Life Drain)", "damage_die": "1d6+3", "damage_type": "piercing"},
                 ],
                 "label": "Multiattack"},
            ),
            {"type": "action", "action": "move_toward_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # ASSASSIN — Surprise round assassinate, then Sneak Attack when flanking
    # ─────────────────────────────────────────────────────────────────────────
    "assassin": {
        "id": "assassin",
        "name": "Assassin",
        "description": "Professional killer. Assassinate with advantage on first round. Sneak Attack when flanking. Repositions otherwise.",
        "node": _sel(
            # Round 1: Assassinate
            _seq(
                _cond("is_first_round"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "1d6+5", "damage_type": "piercing",
                 "advantage": True, "special_effect": "sneak_attack_6d6",
                 "label": "Assassinate", "adv_reason": "Surprise Attack"},
            ),
            # Later rounds with flanking
            _seq(
                _cond("ally_adjacent"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "1d6+5", "damage_type": "piercing",
                 "advantage": True, "special_effect": "sneak_attack_4d6",
                 "label": "Sneak Attack", "adv_reason": "Flanking"},
            ),
            # Reposition
            {"type": "action", "action": "move_to_cover", "label": "Reposition"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # YOUNG DRAGON — Breath Weapon priority, Frightful Presence round 1, Multiattack
    # ─────────────────────────────────────────────────────────────────────────
    "young_dragon": {
        "id": "young_dragon",
        "name": "Young Dragon",
        "description": "Uses Fire Breath when charged. Frightful Presence on first round. Multiattacks otherwise.",
        "node": _sel(
            # Breath weapon if charged
            _seq(
                _cond("ability_ready", "breath_weapon"),
                {"type": "action", "action": "breath_weapon",
                 "damage_die": "10d10", "damage_type": "fire",
                 "dc": 18, "shape": "cone", "label": "Fire Breath"},
            ),
            # Frightful Presence first round
            _seq(
                _cond("is_first_round"),
                {"type": "action", "action": "frighten",
                 "dc": 16, "save": "wis", "label": "Frightful Presence"},
            ),
            # Multiattack
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "multiattack",
                 "attacks": [
                     {"name": "Bite", "damage_die": "2d10+6", "damage_type": "piercing"},
                     {"name": "Claw", "damage_die": "2d6+6", "damage_type": "slashing"},
                     {"name": "Claw", "damage_die": "2d6+6", "damage_type": "slashing"},
                 ],
                 "label": "Multiattack"},
            ),
            {"type": "action", "action": "move_toward_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # GOBLIN BOSS — Commands others, multiattack + nimble escape
    # ─────────────────────────────────────────────────────────────────────────
    "goblin_boss": {
        "id": "goblin_boss",
        "name": "Goblin Boss",
        "description": "The biggest, meanest goblin. Multiattacks. Retreats below 30% HP using Nimble Escape.",
        "node": _sel(
            # Retreat when low
            _seq(
                _cond("hp_below", 0.3),
                {"type": "action", "action": "flee", "label": "Nimble Escape"},
            ),
            # Multiattack
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "multiattack",
                 "attacks": [
                     {"name": "Scimitar", "damage_die": "2d6+2", "damage_type": "slashing"},
                     {"name": "Scimitar", "damage_die": "2d6+2", "damage_type": "slashing"},
                 ],
                 "label": "Multiattack"},
            ),
            {"type": "action", "action": "move_toward_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # CULT FANATIC — Spellcaster: dark blessings, keeps distance
    # ─────────────────────────────────────────────────────────────────────────
    "cult_fanatic": {
        "id": "cult_fanatic",
        "name": "Cult Fanatic",
        "description": "Zealous spellcaster. Uses Inflict Wounds on first round. Keeps distance when possible. Multiattacks up close.",
        "node": _sel(
            # First round: Inflict Wounds up close
            _seq(
                _cond("is_first_round"),
                _cond("in_melee_range"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "3d10", "damage_type": "necrotic",
                 "label": "Inflict Wounds"},
            ),
            # If player is frightened, use advantage
            _seq(
                _cond("player_has_condition", "frightened"),
                _cond("in_melee_range"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "1d6+2", "damage_type": "piercing",
                 "advantage": True, "label": "Sacred Flame (frightened)", "adv_reason": "Target frightened"},
            ),
            # Normal ranged attack if not in melee
            _seq(
                _not(_cond("in_melee_range")),
                {"type": "action", "action": "attack_ranged",
                 "damage_die": "1d6+2", "damage_type": "piercing",
                 "label": "Sacred Flame"},
            ),
            # Multiattack in melee
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "multiattack",
                 "attacks": [
                     {"name": "Dagger", "damage_die": "1d4+2", "damage_type": "piercing"},
                     {"name": "Dagger", "damage_die": "1d4+2", "damage_type": "piercing"},
                 ],
                 "label": "Multiattack"},
            ),
            {"type": "action", "action": "move_away_from_player"},
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # GENERIC BRUTE — Simple charge-and-attack fallback
    # ─────────────────────────────────────────────────────────────────────────
    "generic_brute": {
        "id": "generic_brute",
        "name": "Generic Brute",
        "description": "Default fallback AI. Charges in and attacks. Goes Reckless below 50% HP.",
        "node": _sel(
            # Reckless when bloodied
            _seq(
                _cond("hp_below", 0.5),
                _cond("in_melee_range"),
                {"type": "action", "action": "reckless_attack"},
            ),
            # Normal melee
            _seq(
                _cond("in_melee_range"),
                {"type": "action", "action": "attack_melee",
                 "damage_die": "1d8+3", "damage_type": "slashing", "label": "Weapon Strike"},
            ),
            {"type": "action", "action": "move_toward_player"},
        ),
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Convenience accessor
# ──────────────────────────────────────────────────────────────────────────────

def get_tree(tree_id: str) -> Dict[str, Any] | None:
    """Return a default behavior tree by ID, or None."""
    return DEFAULT_TREES.get(tree_id)


def list_default_trees() -> list:
    """Return all default trees as a list (without node bodies for summary use)."""
    return [
        {"id": v["id"], "name": v["name"], "description": v["description"]}
        for v in DEFAULT_TREES.values()
    ]
