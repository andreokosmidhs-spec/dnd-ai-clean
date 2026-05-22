"""
Enemy Behavior Tree Service — priority-ordered decision logic per behavior profile.

Behavior profiles:
  brute           — charge, always attack, never retreat
  skirmisher      — ranged/cover, retreat below 25% HP
  berserker       — reckless, Frenzy below 50% HP
  pack_hunter     — Pack Tactics, targets wounded player
  undead_mindless — always attacks nearest, Undead Fortitude
  undead_cunning  — Undead Fortitude + Life Drain
  ambusher        — advantage on first attack, retreats to reset
  spellcaster     — spells, keeps distance, Multiattack alternatives

Special abilities:
  nimble_escape, pack_tactics, undead_fortitude, aggressive,
  reckless_attack, regeneration, multiattack, life_drain,
  spider_climb, surprise_attack
"""
from __future__ import annotations

import copy
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _pct_hp(entity: Dict[str, Any]) -> float:
    """Return current HP as fraction of max HP (0.0–1.0)."""
    cur = entity.get("hp", 0)
    mx = entity.get("max_hp", 1) or 1
    return max(0.0, cur / mx)


def _has_ability(enemy: Dict[str, Any], ability_id: str) -> bool:
    return ability_id in (enemy.get("special_abilities") or [])


def _ally_count(combat_context: Dict[str, Any]) -> int:
    alive = combat_context.get("alive_enemies") or []
    return len(alive)


def _default_action(enemy: Dict[str, Any]) -> Dict[str, Any]:
    """Build a plain attack action from enemy stats."""
    return {
        "action_type": "attack",
        "attack_bonus": enemy.get("attack_bonus", 3),
        "damage_die": enemy.get("damage_die", "1d6"),
        "damage_type": enemy.get("damage_type", "slashing"),
        "advantage": False,
        "disadvantage": False,
        "adv_reason": "",
        "special_effect": None,
        "grid_move": None,
        "narration_hint": f"The {enemy.get('name', 'enemy')} attacks.",
        "abilities_used": [],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIOR PROFILES
# ═══════════════════════════════════════════════════════════════════════════════

def _profile_brute(enemy: Dict[str, Any], player_target: Dict[str, Any],
                   ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Charge in, always attacks, never retreats."""
    action = _default_action(enemy)
    action["narration_hint"] = (
        f"The {enemy.get('name', 'enemy')} charges forward and strikes without hesitation."
    )
    if _has_ability(enemy, "multiattack"):
        action["action_type"] = "special_attack"
        action["special_effect"] = {"type": "multiattack", "extra_attacks": 1}
        action["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} presses the attack with a flurry of blows."
        )
        action["abilities_used"].append("multiattack")
    return action


def _profile_skirmisher(enemy: Dict[str, Any], player_target: Dict[str, Any],
                         ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Use cover, attack from range, retreat below 25% HP."""
    action = _default_action(enemy)
    hp_pct = _pct_hp(enemy)
    name = enemy.get("name", "enemy")

    # Priority 1: Retreat when critically wounded
    if hp_pct <= 0.25:
        if _has_ability(enemy, "nimble_escape"):
            action["action_type"] = "flee"
            action["narration_hint"] = (
                f"The {name} darts away using Nimble Escape, vanishing from sight."
            )
            action["abilities_used"].append("nimble_escape")
            return action
        # No nimble_escape — still try to disengage
        action["action_type"] = "flee"
        action["narration_hint"] = f"The {name} breaks and runs, retreating from combat."
        return action

    # Priority 2: Attack from range if possible — move back a step first
    enemy_x = enemy.get("grid_x", 2)
    if enemy_x <= 2:
        action["grid_move"] = {"dx": 1, "dy": 0}   # move back toward range
        action["action_type"] = "move_and_attack"
        action["narration_hint"] = (
            f"The {name} sidesteps to get some distance and fires a quick attack."
        )
    else:
        action["narration_hint"] = f"The {name} attacks from a safe distance."

    return action


def _profile_berserker(enemy: Dict[str, Any], player_target: Dict[str, Any],
                        ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Reckless (advantage + grants adv to attackers); Frenzy below 50% HP."""
    action = _default_action(enemy)
    hp_pct = _pct_hp(enemy)
    name = enemy.get("name", "enemy")

    use_reckless = _has_ability(enemy, "reckless_attack") or hp_pct < 0.5

    if use_reckless:
        action["advantage"] = True
        action["adv_reason"] = "Reckless Attack"
        # Signal to combat engine: attackers gain advantage against this enemy
        action["special_effect"] = {
            "type": "reckless_attack",
            "grants_advantage_to_attackers": True,
        }
        action["abilities_used"].append("reckless_attack")
        action["narration_hint"] = (
            f"The {name} attacks with reckless abandon, leaving itself open!"
        )
    else:
        action["narration_hint"] = f"The {name} charges and swings with raw fury."

    if _has_ability(enemy, "multiattack"):
        action["action_type"] = "special_attack"
        if action.get("special_effect"):
            # Extend existing effect
            action["special_effect"]["extra_attacks"] = 1
        else:
            action["special_effect"] = {"type": "multiattack", "extra_attacks": 1}
        action["abilities_used"].append("multiattack")

    return action


def _profile_pack_hunter(enemy: Dict[str, Any], player_target: Dict[str, Any],
                          ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Pack Tactics (advantage when ally adjacent), targets wounded player."""
    action = _default_action(enemy)
    name = enemy.get("name", "enemy")
    ally_count = _ally_count(ctx)

    # Pack Tactics: advantage if at least one ally alive
    if _has_ability(enemy, "pack_tactics") and ally_count >= 2:
        action["advantage"] = True
        action["adv_reason"] = "Pack Tactics"
        action["abilities_used"].append("pack_tactics")
        action["narration_hint"] = (
            f"The {name} coordinates with its packmates and lunges for an exposed flank."
        )
    else:
        action["narration_hint"] = f"The {name} snarls and snaps at you."

    return action


def _profile_undead_mindless(enemy: Dict[str, Any], player_target: Dict[str, Any],
                               ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Mindless: always attacks nearest, Undead Fortitude when reduced to 0."""
    action = _default_action(enemy)
    name = enemy.get("name", "enemy")
    action["narration_hint"] = (
        f"The {name} shambles forward with blank, dead eyes and strikes."
    )

    # Undead Fortitude is applied reactively (in combat engine on taking damage)
    # but we flag its presence here for the engine
    if _has_ability(enemy, "undead_fortitude"):
        action["special_effect"] = {"type": "undead_fortitude_passive"}

    return action


def _profile_undead_cunning(enemy: Dict[str, Any], player_target: Dict[str, Any],
                              ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Undead Fortitude + Life Drain (reduces max HP)."""
    action = _default_action(enemy)
    name = enemy.get("name", "enemy")

    # Life Drain takes priority over plain attacks
    if _has_ability(enemy, "life_drain"):
        action["action_type"] = "special_attack"
        action["special_effect"] = {
            "type": "life_drain",
            "save_ability": "con",
            "save_dc": 13,
        }
        action["abilities_used"].append("life_drain")
        action["narration_hint"] = (
            f"The {name} reaches out with a withered claw — you feel your life force being drained."
        )
    else:
        action["narration_hint"] = f"The {name} advances with predatory hunger."

    if _has_ability(enemy, "multiattack"):
        if action.get("special_effect"):
            action["special_effect"]["extra_attacks"] = 1
        else:
            action["special_effect"] = {"type": "multiattack", "extra_attacks": 1}
        action["abilities_used"].append("multiattack")

    # Undead Fortitude passive flag
    if _has_ability(enemy, "undead_fortitude"):
        if action.get("special_effect"):
            action["special_effect"]["undead_fortitude"] = True
        else:
            action["special_effect"] = {"type": "undead_fortitude_passive"}

    return action


def _profile_ambusher(enemy: Dict[str, Any], player_target: Dict[str, Any],
                       ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Advantage on first attack (Surprise Attack), retreats to reset."""
    action = _default_action(enemy)
    name = enemy.get("name", "enemy")
    rnd = ctx.get("round", 1)

    # Surprise Attack on round 1 or after a retreat
    if rnd == 1 or enemy.get("_retreated_last_turn", False):
        action["advantage"] = True
        action["adv_reason"] = "Surprise Attack"

        if _has_ability(enemy, "surprise_attack"):
            action["action_type"] = "special_attack"
            action["special_effect"] = {
                "type": "surprise_attack",
                "bonus_damage_die": "2d6",
            }
            action["abilities_used"].append("surprise_attack")
            action["narration_hint"] = (
                f"The {name} lunges from the shadows with a devastating surprise attack!"
            )
        else:
            action["narration_hint"] = f"The {name} strikes from ambush with advantage."

        # Mark retreated flag as consumed
        enemy["_retreated_last_turn"] = False
    elif _pct_hp(enemy) < 0.5:
        # Retreat to try to reset surprise
        if _has_ability(enemy, "nimble_escape"):
            action["action_type"] = "flee"
            action["narration_hint"] = (
                f"The {name} disengages and melts back into the darkness to reset its ambush."
            )
            action["abilities_used"].append("nimble_escape")
            enemy["_retreated_last_turn"] = True
            return action
        # Still try normal attack if can't flee
        action["narration_hint"] = f"The {name} strikes quickly and looks for an opening to vanish."
    else:
        action["narration_hint"] = (
            f"The {name} attacks from an angle, probing for weakness."
        )

    if _has_ability(enemy, "multiattack"):
        action["action_type"] = "special_attack"
        if action.get("special_effect"):
            action["special_effect"]["extra_attacks"] = 1
        else:
            action["special_effect"] = {"type": "multiattack", "extra_attacks": 1}
        action["abilities_used"].append("multiattack")

    return action


def _profile_spellcaster(enemy: Dict[str, Any], player_target: Dict[str, Any],
                          ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Use spells from list, keep distance, Multiattack alternatives."""
    action = _default_action(enemy)
    name = enemy.get("name", "enemy")
    rnd = ctx.get("round", 1)
    spells = enemy.get("spell_list", [])

    # Move toward ranged distance if too close
    enemy_x = enemy.get("grid_x", 2)
    if enemy_x <= 1:
        action["grid_move"] = {"dx": 1, "dy": 0}
        action["action_type"] = "move_and_attack"

    # Alternate: use a spell on even rounds if available
    if spells and (rnd % 2 == 0):
        chosen_spell = spells[0]  # Use first available; future enhancement: prioritize
        action["action_type"] = "special_attack"
        action["special_effect"] = {
            "type": "spell",
            "spell_id": chosen_spell,
        }
        action["abilities_used"].append(chosen_spell)
        action["narration_hint"] = (
            f"The {name} raises its hands and calls upon dark power, unleashing {chosen_spell.replace('_', ' ')}."
        )
    elif _has_ability(enemy, "multiattack"):
        action["action_type"] = "special_attack"
        action["special_effect"] = {"type": "multiattack", "extra_attacks": 1}
        action["abilities_used"].append("multiattack")
        action["narration_hint"] = (
            f"The {name} strikes with practiced precision, landing multiple blows."
        )
    else:
        action["narration_hint"] = f"The {name} channels dark energy and attacks."

    return action


# Map profile name → function
_PROFILE_MAP: Dict[str, Callable] = {
    "brute": _profile_brute,
    "skirmisher": _profile_skirmisher,
    "berserker": _profile_berserker,
    "pack_hunter": _profile_pack_hunter,
    "undead_mindless": _profile_undead_mindless,
    "undead_cunning": _profile_undead_cunning,
    "ambusher": _profile_ambusher,
    "spellcaster": _profile_spellcaster,
}


# ═══════════════════════════════════════════════════════════════════════════════
# REGENERATION CHECK (applied at start of turn before action decision)
# ═══════════════════════════════════════════════════════════════════════════════

def _maybe_regenerate(enemy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    If enemy has regeneration and is below max HP and did NOT take fire/acid
    last turn, return a regenerate action instead of attacking.
    Returns action dict or None if regeneration doesn't apply this turn.
    """
    if not _has_ability(enemy, "regeneration"):
        return None
    if enemy.get("hp", 0) >= enemy.get("max_hp", 0):
        return None
    # Check if suppressed by fire/acid damage last turn
    if enemy.get("_regen_suppressed", False):
        enemy["_regen_suppressed"] = False  # Reset for next turn
        return None

    regen_amount = 10
    old_hp = enemy.get("hp", 0)
    new_hp = min(enemy.get("max_hp", old_hp), old_hp + regen_amount)
    enemy["hp"] = new_hp

    return {
        "action_type": "regenerate",
        "attack_bonus": 0,
        "damage_die": "",
        "damage_type": "",
        "advantage": False,
        "disadvantage": False,
        "adv_reason": "",
        "special_effect": {"type": "regeneration", "healed": new_hp - old_hp},
        "grid_move": None,
        "narration_hint": (
            f"The {enemy.get('name', 'enemy')} shudders as grotesque flesh knits itself back together."
        ),
        "abilities_used": ["regeneration"],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN DECISION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def decide_enemy_action(
    enemy: Dict[str, Any],
    player_target: Dict[str, Any],
    combat_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Decide what the enemy does on its turn using the behavior tree.

    Args:
        enemy: Enemy dict with hp, stats, behavior_profile, special_abilities, etc.
        player_target: Dict with at minimum {"ac", "hp", "max_hp"}.
        combat_context: {
            "round": int,
            "alive_enemies": list,       # all enemies still alive including self
            "grid_cells": list,          # optional grid state
            "player_grid_x": int,
            "player_grid_y": int,
        }

    Returns:
        Action dict with keys:
            action_type, attack_bonus, damage_die, damage_type,
            advantage, disadvantage, adv_reason, special_effect,
            grid_move, narration_hint, abilities_used
    """
    # Priority 0: Regeneration (heals before acting; skip attack if full heal brings over threshold)
    regen_action = _maybe_regenerate(enemy)
    if regen_action:
        return regen_action

    profile = enemy.get("behavior_profile", "brute")
    profile_fn = _PROFILE_MAP.get(profile, _profile_brute)

    try:
        action = profile_fn(enemy, player_target, combat_context)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Enemy behavior profile '%s' raised %s; falling back to brute.",
            profile, exc
        )
        action = _profile_brute(enemy, player_target, combat_context)

    # Ensure required keys are always present
    defaults = _default_action(enemy)
    for key, val in defaults.items():
        action.setdefault(key, val)

    return action


# ═══════════════════════════════════════════════════════════════════════════════
# SPECIAL EFFECT APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

def apply_special_effect(
    effect: Dict[str, Any],
    target: Dict[str, Any],
    roller_fn: Callable[[], int],
) -> Dict[str, Any]:
    """
    Apply a special effect to a target and return a result dict.

    Args:
        effect: {"type": "life_drain"|"undead_fortitude"|..., ...params}
        target: The entity being affected (mutated in-place for HP/max_hp).
        roller_fn: Callable that returns a d20 roll (int 1–20).

    Returns:
        {
            "effect_type": str,
            "triggered": bool,
            "roll": int | None,
            "dc": int | None,
            "saved": bool | None,
            "hp_change": int,
            "max_hp_change": int,
            "description": str,
        }
    """
    effect_type = effect.get("type", "")
    result: Dict[str, Any] = {
        "effect_type": effect_type,
        "triggered": False,
        "roll": None,
        "dc": None,
        "saved": None,
        "hp_change": 0,
        "max_hp_change": 0,
        "description": "",
    }

    if effect_type == "undead_fortitude":
        # Called when enemy would drop to 0 HP
        damage_dealt = effect.get("damage_dealt", 0)
        dc = max(5, 5 + damage_dealt)
        roll = roller_fn()

        # CON save: roll + CON modifier vs DC
        abilities = target.get("abilities", {})
        con = abilities.get("con", 10)
        con_mod = (con - 10) // 2
        total = roll + con_mod

        result["triggered"] = True
        result["roll"] = roll
        result["dc"] = dc
        result["saved"] = total >= dc

        if result["saved"]:
            # Drop to 1 HP instead of 0
            target["hp"] = 1
            result["hp_change"] = 1 - 0  # net from 0 to 1
            result["description"] = (
                f"Undead Fortitude! {target.get('name', 'enemy')} rolled {roll}+{con_mod}={total} vs DC {dc} "
                f"— survives with 1 HP!"
            )
        else:
            result["description"] = (
                f"Undead Fortitude failed: {target.get('name', 'enemy')} rolled {roll}+{con_mod}={total} vs DC {dc}."
            )

    elif effect_type == "life_drain":
        # On hit, target makes CON save DC 13 or max HP reduced by damage dealt
        dc = effect.get("save_dc", 13)
        damage = effect.get("damage_dealt", 0)
        roll = roller_fn()

        abilities = target.get("abilities", {})
        con = abilities.get("con", 10)
        con_mod = (con - 10) // 2
        total = roll + con_mod

        result["triggered"] = True
        result["roll"] = roll
        result["dc"] = dc
        result["saved"] = total >= dc

        if not result["saved"] and damage > 0:
            old_max = target.get("max_hp", target.get("hp", 1))
            new_max = max(1, old_max - damage)
            target["max_hp"] = new_max
            # Also cap current HP
            if target.get("hp", 0) > new_max:
                target["hp"] = new_max
            result["max_hp_change"] = new_max - old_max
            result["description"] = (
                f"Life Drain! {target.get('name', 'target')} rolled {roll}+{con_mod}={total} vs DC {dc} "
                f"— max HP reduced by {damage} to {new_max}."
            )
        else:
            result["description"] = (
                f"Life Drain resisted: rolled {roll}+{con_mod}={total} vs DC {dc}."
            )

    elif effect_type == "surprise_attack":
        # Bonus damage — the actual dice are rolled by the caller
        bonus_die = effect.get("bonus_damage_die", "2d6")
        result["triggered"] = True
        result["description"] = f"Surprise Attack! Roll an extra {bonus_die} damage."

    elif effect_type == "reckless_attack":
        result["triggered"] = True
        result["description"] = (
            "Reckless Attack: attacker has advantage this turn but attackers gain advantage against it."
        )

    elif effect_type == "regeneration":
        healed = effect.get("healed", 10)
        result["triggered"] = True
        result["hp_change"] = healed
        result["description"] = f"Regeneration: {target.get('name', 'enemy')} heals {healed} HP."

    elif effect_type == "multiattack":
        extra = effect.get("extra_attacks", 1)
        result["triggered"] = True
        result["description"] = f"Multiattack: {extra} extra attack(s) this turn."

    elif effect_type == "spell":
        spell_id = effect.get("spell_id", "unknown")
        result["triggered"] = True
        result["description"] = f"Spell cast: {spell_id.replace('_', ' ')}."

    else:
        result["description"] = f"Unknown effect type: {effect_type}"

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# LIBRARY HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_enemy_from_library(enemy_id: str) -> Optional[Dict[str, Any]]:
    """Fetch enemy template from ENEMY_LIBRARY. Returns None if not found."""
    try:
        from data.enemy_library import ENEMY_LIBRARY
        return ENEMY_LIBRARY.get(enemy_id)
    except ImportError:
        logger.error("Cannot import ENEMY_LIBRARY from data.enemy_library")
        return None


def build_combat_enemy(
    enemy_id: str,
    name_override: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Build a combat-ready enemy dict from a library template.
    Generates a unique instance ID so multiple copies can coexist.

    Returns None if enemy_id not found in library.
    """
    template = get_enemy_from_library(enemy_id)
    if template is None:
        return None

    enemy = copy.deepcopy(template)
    # Give a unique instance ID
    enemy["instance_id"] = str(uuid.uuid4())
    enemy["id"] = enemy["instance_id"]   # combat engine uses "id" field

    if name_override:
        enemy["name"] = name_override

    # Ensure runtime fields are present
    enemy.setdefault("hp", enemy.get("max_hp", 10))
    enemy.setdefault("conditions", [])
    enemy.setdefault("grid_x", enemy.get("lane", 2))
    enemy.setdefault("grid_y", 2)

    return enemy
