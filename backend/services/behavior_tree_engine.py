"""
Behavior Tree Engine — pure Python, no LLM, no new deps.
Evaluates recursive JSON/dict behavior trees each combat turn.

Public API:
    build_context(enemy, player_target, combat_context) -> dict
    evaluate(node, ctx) -> (bool, dict | None)
    run_tree(tree_node, enemy, player_target, combat_context) -> dict
    list_available_conditions() -> list[dict]
    list_available_actions() -> list[dict]
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_MAX_DEPTH = 20  # guard against circular/deeply-nested trees


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def build_context(
    enemy: Dict[str, Any],
    player_target: Dict[str, Any],
    combat_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Build the evaluation context dict from raw game state."""
    enemy_hp = enemy.get("hp", 0)
    enemy_max_hp = enemy.get("max_hp", 1) or 1
    enemy_hp_pct = max(0.0, enemy_hp / enemy_max_hp)

    player_hp = player_target.get("hp", 10)
    player_max_hp = player_target.get("max_hp", 10) or 10
    player_hp_pct = max(0.0, player_hp / player_max_hp)

    # Grid position / distance
    enemy_x = enemy.get("grid_x", 0)
    enemy_y = enemy.get("grid_y", 0)
    player_x = combat_context.get("player_grid_x", 0)
    player_y = combat_context.get("player_grid_y", 0)

    # Chebyshev distance (works even if grids are 0,0)
    distance = max(abs(enemy_x - player_x), abs(enemy_y - player_y))
    in_melee_range = distance <= 1

    # Ally adjacency: any alive enemy within 1 Chebyshev cell of player
    alive_enemies: List[Dict] = combat_context.get("alive_enemies") or []
    ally_adjacent = False
    for ally in alive_enemies:
        if ally.get("id") == enemy.get("id"):
            continue
        ax = ally.get("grid_x", 0)
        ay = ally.get("grid_y", 0)
        if max(abs(ax - player_x), abs(ay - player_y)) <= 1:
            ally_adjacent = True
            break

    ability_charges: Dict[str, int] = enemy.get("ability_charges") or {}

    return {
        "enemy_hp_pct": enemy_hp_pct,
        "player_hp_pct": player_hp_pct,
        "player_hp": player_hp,
        "player_ac": player_target.get("ac", 10),
        "player_conditions": player_target.get("conditions") or [],
        "round": combat_context.get("round", 1),
        "alive_enemies": alive_enemies,
        "distance_to_player": distance,
        "ally_adjacent_to_player": ally_adjacent,
        "in_melee_range": in_melee_range,
        "enemy_type": enemy.get("type", "humanoid"),
        "special_abilities": enemy.get("special_abilities") or [],
        "ability_charges": ability_charges,
        "took_fire_damage_last_turn": bool(enemy.get("took_fire_damage_last_turn", False)),
        "took_acid_damage_last_turn": bool(enemy.get("took_acid_damage_last_turn", False)),
        "is_first_attack_this_turn": bool(enemy.get("is_first_attack_this_turn", True)),
        "enemy": enemy,
        # Faction / team context — populated by faction_combat_service if present
        "enemy_faction_role":   combat_context.get("enemy_faction_role", "solo"),
        "faction_leader_alive": combat_context.get("faction_leader_alive", True),
        "faction_leader_hp_pct": combat_context.get("faction_leader_hp_pct", 1.0),
        "faction_leader_id":    combat_context.get("faction_leader_id"),
        "faction_followers":    combat_context.get("faction_followers", []),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CONDITION EVALUATORS
# ═══════════════════════════════════════════════════════════════════════════════

def _eval_condition(node: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
    check = node.get("check", "")
    value = node.get("value")

    if check == "hp_below":
        return ctx["enemy_hp_pct"] < float(value or 0)

    if check == "hp_above":
        return ctx["enemy_hp_pct"] > float(value or 0)

    if check == "player_hp_below":
        return ctx["player_hp_pct"] < float(value or 0)

    if check == "player_hp_above":
        return ctx["player_hp_pct"] > float(value or 0)

    if check == "in_melee_range":
        return ctx["in_melee_range"]

    if check == "ally_adjacent":
        return ctx["ally_adjacent_to_player"]

    if check == "round_above":
        return ctx["round"] > int(value or 0)

    if check == "is_first_round":
        return ctx["round"] == 1

    if check == "took_fire_damage":
        return ctx["took_fire_damage_last_turn"]

    if check == "took_acid_damage":
        return ctx["took_acid_damage_last_turn"]

    if check == "player_has_condition":
        return str(value or "") in (ctx["player_conditions"] or [])

    if check == "enemy_count_above":
        return len(ctx["alive_enemies"]) > int(value or 0)

    if check == "ability_ready":
        charges = ctx["ability_charges"]
        return charges.get(str(value or ""), 0) > 0

    if check == "has_special":
        return str(value or "") in (ctx["special_abilities"] or [])

    if check == "is_enemy_type":
        return ctx["enemy_type"].lower() == str(value or "").lower()

    # ── Faction / team conditions ────────────────────────────────────────────
    if check == "leader_alive":
        return ctx.get("faction_leader_alive", True)

    if check == "leader_hp_below":
        return ctx.get("faction_leader_hp_pct", 1.0) < float(value or 0)

    if check == "is_leader":
        return ctx.get("enemy_faction_role") == "leader"

    if check == "is_bodyguard":
        return ctx.get("enemy_faction_role") == "bodyguard"

    if check == "ally_count_below":
        return len(ctx.get("alive_enemies", [])) < int(value or 1)

    if check == "ally_count_above":
        return len(ctx.get("alive_enemies", [])) > int(value or 0)

    if check == "has_followers":
        return len(ctx.get("faction_followers", [])) > 0

    logger.warning("Unknown condition check: %s", check)
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# ACTION BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def _action_base(enemy: Dict[str, Any]) -> Dict[str, Any]:
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
        "attacks": None,
        "meta": {},
    }


def _build_action(node: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Convert an action node to a full action result dict."""
    enemy = ctx.get("enemy", {})
    action_id = node.get("action", "")
    label = node.get("label", action_id)
    result = _action_base(enemy)
    result["meta"] = node.copy()

    # ── MELEE ATTACK ──────────────────────────────────────────────────────────
    if action_id == "attack_melee":
        result["action_type"] = "attack"
        result["damage_die"] = node.get("damage_die", enemy.get("damage_die", "1d6"))
        result["damage_type"] = node.get("damage_type", enemy.get("damage_type", "slashing"))
        result["advantage"] = bool(node.get("advantage", False))
        result["disadvantage"] = bool(node.get("disadvantage", False))
        result["adv_reason"] = node.get("adv_reason", "")
        se = node.get("special_effect")
        if se:
            result["special_effect"] = {"type": se} if isinstance(se, str) else se
        result["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} attacks with {label}."
        )

    # ── RANGED ATTACK ─────────────────────────────────────────────────────────
    elif action_id == "attack_ranged":
        result["action_type"] = "attack"
        result["damage_die"] = node.get("damage_die", enemy.get("damage_die", "1d6"))
        result["damage_type"] = node.get("damage_type", "piercing")
        result["advantage"] = bool(node.get("advantage", False))
        result["disadvantage"] = bool(node.get("disadvantage", False))
        result["adv_reason"] = node.get("adv_reason", "")
        result["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} fires a ranged attack with {label}."
        )

    # ── MULTIATTACK ───────────────────────────────────────────────────────────
    elif action_id == "multiattack":
        attacks = node.get("attacks", [])
        result["action_type"] = "special_attack"
        result["attacks"] = attacks
        result["special_effect"] = {"type": "multiattack", "extra_attacks": len(attacks) - 1}
        result["abilities_used"].append("multiattack")
        # Use first attack's stats for the primary roll
        if attacks:
            result["damage_die"] = attacks[0].get("damage_die", enemy.get("damage_die", "1d6"))
            result["damage_type"] = attacks[0].get("damage_type", "slashing")
        result["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} lashes out with {label or 'multiple strikes'}."
        )

    # ── RECKLESS ATTACK ───────────────────────────────────────────────────────
    elif action_id == "reckless_attack":
        result["action_type"] = "attack"
        result["damage_die"] = enemy.get("damage_die", "1d6")
        result["damage_type"] = enemy.get("damage_type", "slashing")
        result["advantage"] = True
        result["adv_reason"] = "Reckless Attack"
        result["special_effect"] = {
            "type": "reckless_attack",
            "grants_advantage_to_attackers": True,
        }
        result["abilities_used"].append("reckless_attack")
        result["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} attacks recklessly, leaving itself open!"
        )

    # ── FLEE ─────────────────────────────────────────────────────────────────
    elif action_id == "flee":
        result["action_type"] = "flee"
        result["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} breaks and flees from combat! {label}"
        ).strip()

    # ── MOVE TO COVER ─────────────────────────────────────────────────────────
    elif action_id == "move_to_cover":
        result["action_type"] = "move_and_attack"
        result["grid_move"] = {"dx": 1, "dy": 0}
        result["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} repositions toward cover."
        )

    # ── MOVE TOWARD PLAYER ───────────────────────────────────────────────────
    elif action_id == "move_toward_player":
        result["action_type"] = "move_and_attack"
        result["grid_move"] = {"dx": -1, "dy": 0}
        result["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} moves toward you."
        )

    # ── MOVE AWAY FROM PLAYER ────────────────────────────────────────────────
    elif action_id == "move_away_from_player":
        result["action_type"] = "move_and_attack"
        result["grid_move"] = {"dx": 1, "dy": 0}
        result["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} backs away."
        )

    # ── BREATH WEAPON ─────────────────────────────────────────────────────────
    elif action_id == "breath_weapon":
        damage_die = node.get("damage_die", "6d6")
        damage_type = node.get("damage_type", "fire")
        dc = node.get("dc", 14)
        shape = node.get("shape", "cone")
        result["action_type"] = "special_attack"
        result["damage_die"] = damage_die
        result["damage_type"] = damage_type
        result["special_effect"] = {
            "type": "breath_weapon",
            "dc": dc,
            "shape": shape,
            "damage_die": damage_die,
            "damage_type": damage_type,
        }
        result["abilities_used"].append("breath_weapon")
        # Decrement charge
        enemy_charges = enemy.get("ability_charges") or {}
        if "breath_weapon" in enemy_charges:
            enemy["ability_charges"]["breath_weapon"] = max(
                0, enemy_charges["breath_weapon"] - 1
            )
        result["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} unleashes its {label}! "
            f"DC {dc} DEX save or take {damage_die} {damage_type} damage."
        )

    # ── USE ABILITY ───────────────────────────────────────────────────────────
    elif action_id == "use_ability":
        ability_id = node.get("ability_id", "")
        result["action_type"] = "special_attack"
        result["special_effect"] = {"type": "use_ability", "ability_id": ability_id}
        result["abilities_used"].append(ability_id)
        result["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} uses {label or ability_id}."
        )

    # ── DEFEND ────────────────────────────────────────────────────────────────
    elif action_id == "defend":
        result["action_type"] = "defend"
        result["special_effect"] = {"type": "dodge"}
        result["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} takes the Dodge action."
        )

    # ── REGENERATE ────────────────────────────────────────────────────────────
    elif action_id == "regenerate":
        # Suppressed if took fire or acid damage
        if ctx.get("took_fire_damage_last_turn") or ctx.get("took_acid_damage_last_turn"):
            # Fall through — return None to signal suppression
            return None  # type: ignore[return-value]
        amount = int(node.get("amount", 10))
        old_hp = enemy.get("hp", 0)
        max_hp = enemy.get("max_hp", old_hp)
        new_hp = min(max_hp, old_hp + amount)
        enemy["hp"] = new_hp
        healed = new_hp - old_hp
        result["action_type"] = "regenerate"
        result["special_effect"] = {"type": "regeneration", "healed": healed}
        result["abilities_used"].append("regeneration")
        result["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} shudders as its wounds knit closed "
            f"({healed} HP restored)."
        )

    # ── FRIGHTEN ──────────────────────────────────────────────────────────────
    elif action_id == "frighten":
        dc = node.get("dc", 13)
        save = node.get("save", "wis")
        result["action_type"] = "special_attack"
        result["special_effect"] = {
            "type": "frightful_presence",
            "dc": dc,
            "save": save,
        }
        result["abilities_used"].append("frightful_presence")
        result["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} exerts its {label}! "
            f"DC {dc} {save.upper()} save or become Frightened."
        )

    # ── GRAPPLE ───────────────────────────────────────────────────────────────
    elif action_id == "grapple":
        result["action_type"] = "special_attack"
        result["special_effect"] = {"type": "grapple"}
        result["abilities_used"].append("grapple")
        result["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} attempts to grapple you!"
        )

    # ── PROTECT LEADER ────────────────────────────────────────────────────────
    elif action_id == "protect_leader":
        leader_id = ctx.get("faction_leader_id")
        alive = ctx.get("alive_enemies", [])
        leader = next((e for e in alive if e.get("id") == leader_id), None)
        if leader:
            # Move adjacent to leader; if leader is low HP also attack player
            result["action_type"] = "move_and_attack"
            result["grid_move"] = {"dx": 0, "dy": 0, "target_id": leader_id}
            result["abilities_used"].append("protect_leader")
            result["narration_hint"] = (
                f"The {enemy.get('name', 'enemy')} moves to shield "
                f"{leader.get('name', 'their leader')}!"
            )
        else:
            # Leader gone — attack player instead
            result["action_type"] = "attack"
            result["narration_hint"] = (
                f"The {enemy.get('name', 'enemy')} roars in fury at their leader's fall!"
            )
            result["advantage"] = True
            result["adv_reason"] = "Enraged by leader's death"

    # ── COMMAND FOLLOWERS ─────────────────────────────────────────────────────
    elif action_id == "command_followers":
        result["action_type"] = "special_attack"
        result["special_effect"] = {"type": "command_followers", "bonus": 2}
        result["abilities_used"].append("command_followers")
        result["narration_hint"] = (
            f"{enemy.get('name', 'The leader')} barks orders, rallying their allies!"
        )

    # ── RALLY ─────────────────────────────────────────────────────────────────
    elif action_id == "rally":
        result["action_type"] = "defend"
        result["special_effect"] = {"type": "rally", "morale_bonus": 2}
        result["abilities_used"].append("rally")
        result["narration_hint"] = (
            f"{enemy.get('name', 'The leader')} steadies their allies — "
            f"\"Hold the line! Don't break!\""
        )

    # ── FOCUS FIRE ────────────────────────────────────────────────────────────
    elif action_id == "focus_fire":
        # Attack with advantage (flanking with leader)
        result["action_type"] = "attack"
        result["advantage"] = True
        result["adv_reason"] = "Flanking with ally"
        result["abilities_used"].append("focus_fire")
        result["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} flanks alongside their ally!"
        )

    else:
        logger.warning("Unknown action type: %s", action_id)
        result["narration_hint"] = (
            f"The {enemy.get('name', 'enemy')} acts ({action_id})."
        )

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# TREE EVALUATOR
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate(
    node: Dict[str, Any],
    ctx: Dict[str, Any],
    _depth: int = 0,
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Recursively evaluate a behavior tree node.

    Returns:
        (success: bool, action_dict | None)
        action_dict is non-None only when an action node fires.
    """
    if _depth > _MAX_DEPTH:
        logger.error("Behavior tree depth limit (%d) exceeded — aborting branch", _MAX_DEPTH)
        return False, None

    if not isinstance(node, dict):
        return False, None

    node_type = node.get("type", "")

    # ── SELECTOR (OR) ─────────────────────────────────────────────────────────
    if node_type == "selector":
        for child in (node.get("children") or []):
            ok, action = evaluate(child, ctx, _depth + 1)
            if ok:
                return True, action
        return False, None

    # ── SEQUENCE (AND) ────────────────────────────────────────────────────────
    if node_type == "sequence":
        last_action: Optional[Dict] = None
        for child in (node.get("children") or []):
            ok, action = evaluate(child, ctx, _depth + 1)
            if not ok:
                return False, None
            if action is not None:
                last_action = action
        return True, last_action

    # ── NOT (decorator) ───────────────────────────────────────────────────────
    if node_type == "not":
        child = node.get("child")
        if child is None:
            return True, None
        ok, _ = evaluate(child, ctx, _depth + 1)
        return (not ok), None

    # ── CONDITION ─────────────────────────────────────────────────────────────
    if node_type == "condition":
        try:
            result = _eval_condition(node, ctx)
        except Exception as exc:
            logger.warning("Condition eval error: %s", exc)
            result = False
        return result, None

    # ── ACTION ────────────────────────────────────────────────────────────────
    if node_type == "action":
        try:
            action = _build_action(node, ctx)
        except Exception as exc:
            logger.warning("Action build error: %s", exc)
            action = None

        if action is None:
            # e.g. regenerate suppressed — treat as failure so tree falls through
            return False, None
        return True, action

    # ── UNKNOWN ───────────────────────────────────────────────────────────────
    logger.warning("Unknown node type: %s", node_type)
    return False, None


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC run_tree
# ═══════════════════════════════════════════════════════════════════════════════

def _default_action_from_enemy(enemy: Dict[str, Any]) -> Dict[str, Any]:
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
        "attacks": None,
        "meta": {},
    }


def run_tree(
    tree_node: Dict[str, Any],
    enemy: Dict[str, Any],
    player_target: Dict[str, Any],
    combat_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build context, evaluate the tree, return a complete action dict.
    Always returns a valid action dict (falls back to default attack).
    """
    ctx = build_context(enemy, player_target, combat_context)

    try:
        ok, action = evaluate(tree_node, ctx)
    except Exception as exc:
        logger.error("run_tree evaluation crashed: %s", exc, exc_info=True)
        ok, action = False, None

    if ok and action is not None:
        # Ensure all required keys are present
        defaults = _default_action_from_enemy(enemy)
        for key, val in defaults.items():
            action.setdefault(key, val)
        return action

    # Fallback: plain attack
    return _default_action_from_enemy(enemy)


# ═══════════════════════════════════════════════════════════════════════════════
# METADATA: list_available_conditions / list_available_actions
# ═══════════════════════════════════════════════════════════════════════════════

def list_available_conditions() -> List[Dict[str, Any]]:
    return [
        {
            "id": "hp_below",
            "label": "Enemy HP Below",
            "has_value": True,
            "value_type": "float",
            "description": "True if enemy HP percentage is below the given threshold (0.0–1.0).",
        },
        {
            "id": "hp_above",
            "label": "Enemy HP Above",
            "has_value": True,
            "value_type": "float",
            "description": "True if enemy HP percentage is above the given threshold.",
        },
        {
            "id": "player_hp_below",
            "label": "Player HP Below",
            "has_value": True,
            "value_type": "float",
            "description": "True if player HP percentage is below the given threshold.",
        },
        {
            "id": "player_hp_above",
            "label": "Player HP Above",
            "has_value": True,
            "value_type": "float",
            "description": "True if player HP percentage is above the given threshold.",
        },
        {
            "id": "in_melee_range",
            "label": "In Melee Range",
            "has_value": False,
            "value_type": None,
            "description": "True if distance to player is <= 1 cell.",
        },
        {
            "id": "ally_adjacent",
            "label": "Ally Adjacent to Player",
            "has_value": False,
            "value_type": None,
            "description": "True if any alive ally is within 1 cell of the player.",
        },
        {
            "id": "round_above",
            "label": "Round Above",
            "has_value": True,
            "value_type": "int",
            "description": "True if current round number is greater than given value.",
        },
        {
            "id": "is_first_round",
            "label": "Is First Round",
            "has_value": False,
            "value_type": None,
            "description": "True if this is round 1 of combat.",
        },
        {
            "id": "took_fire_damage",
            "label": "Took Fire Damage Last Turn",
            "has_value": False,
            "value_type": None,
            "description": "True if the enemy took fire damage on the previous turn.",
        },
        {
            "id": "took_acid_damage",
            "label": "Took Acid Damage Last Turn",
            "has_value": False,
            "value_type": None,
            "description": "True if the enemy took acid damage on the previous turn.",
        },
        {
            "id": "player_has_condition",
            "label": "Player Has Condition",
            "has_value": True,
            "value_type": "str",
            "description": "True if the player currently has the given condition (e.g. 'frightened').",
        },
        {
            "id": "enemy_count_above",
            "label": "Alive Enemy Count Above",
            "has_value": True,
            "value_type": "int",
            "description": "True if the number of alive allies (including self) is greater than the value.",
        },
        {
            "id": "ability_ready",
            "label": "Ability Ready",
            "has_value": True,
            "value_type": "str",
            "description": "True if the named ability has remaining charges.",
        },
        {
            "id": "has_special",
            "label": "Has Special Ability",
            "has_value": True,
            "value_type": "str",
            "description": "True if the enemy has the named special ability in its list.",
        },
        {
            "id": "is_enemy_type",
            "label": "Is Enemy Type",
            "has_value": True,
            "value_type": "str",
            "description": "True if the enemy type matches the given string (e.g. 'undead').",
        },
    ]


def list_available_actions() -> List[Dict[str, Any]]:
    return [
        {
            "id": "attack_melee",
            "label": "Melee Attack",
            "params": [
                {"name": "damage_die", "type": "str", "default": "1d6+2"},
                {"name": "damage_type", "type": "str", "default": "slashing"},
                {"name": "advantage", "type": "bool", "default": False},
                {"name": "disadvantage", "type": "bool", "default": False},
                {"name": "special_effect", "type": "str", "default": None},
                {"name": "label", "type": "str", "default": "Attack"},
                {"name": "adv_reason", "type": "str", "default": ""},
            ],
            "description": "Standard melee weapon attack.",
        },
        {
            "id": "attack_ranged",
            "label": "Ranged Attack",
            "params": [
                {"name": "damage_die", "type": "str", "default": "1d6+2"},
                {"name": "damage_type", "type": "str", "default": "piercing"},
                {"name": "range_ft", "type": "int", "default": 60},
                {"name": "label", "type": "str", "default": "Ranged Attack"},
            ],
            "description": "Ranged weapon attack (bow, crossbow, etc.).",
        },
        {
            "id": "multiattack",
            "label": "Multiattack",
            "params": [
                {"name": "attacks", "type": "list", "default": []},
                {"name": "label", "type": "str", "default": "Multiattack"},
            ],
            "description": "Make multiple attacks in one action. Each attack is {name, damage_die, damage_type}.",
        },
        {
            "id": "reckless_attack",
            "label": "Reckless Attack",
            "params": [],
            "description": "Attack with advantage but grant advantage to attackers until next turn.",
        },
        {
            "id": "flee",
            "label": "Flee",
            "params": [{"name": "label", "type": "str", "default": "Flee"}],
            "description": "Move away and end combat participation for this enemy.",
        },
        {
            "id": "move_to_cover",
            "label": "Move to Cover",
            "params": [],
            "description": "Move toward the nearest cover cell.",
        },
        {
            "id": "move_toward_player",
            "label": "Move Toward Player",
            "params": [],
            "description": "Move one step closer to the player.",
        },
        {
            "id": "move_away_from_player",
            "label": "Move Away from Player",
            "params": [],
            "description": "Move one step away from the player.",
        },
        {
            "id": "breath_weapon",
            "label": "Breath Weapon",
            "params": [
                {"name": "damage_die", "type": "str", "default": "6d6"},
                {"name": "damage_type", "type": "str", "default": "fire"},
                {"name": "dc", "type": "int", "default": 14},
                {"name": "shape", "type": "str", "default": "cone"},
                {"name": "label", "type": "str", "default": "Breath Weapon"},
            ],
            "description": "Area breath weapon. Decrements ability_charges['breath_weapon'].",
        },
        {
            "id": "use_ability",
            "label": "Use Special Ability",
            "params": [
                {"name": "ability_id", "type": "str", "default": ""},
                {"name": "label", "type": "str", "default": "Special Ability"},
            ],
            "description": "Generic ability use.",
        },
        {
            "id": "defend",
            "label": "Defend (Dodge)",
            "params": [],
            "description": "Take the Dodge action — no attack, grants disadvantage to attackers.",
        },
        {
            "id": "regenerate",
            "label": "Regenerate",
            "params": [
                {"name": "amount", "type": "int", "default": 10},
                {"name": "label", "type": "str", "default": "Regeneration"},
            ],
            "description": "Heal HP; suppressed if enemy took fire or acid damage last turn.",
        },
        {
            "id": "frighten",
            "label": "Frightful Presence",
            "params": [
                {"name": "dc", "type": "int", "default": 13},
                {"name": "save", "type": "str", "default": "wis"},
                {"name": "label", "type": "str", "default": "Frightful Presence"},
            ],
            "description": "Force WIS save or target becomes Frightened. No attack this turn.",
        },
        {
            "id": "grapple",
            "label": "Grapple",
            "params": [],
            "description": "STR contest; on success player is restrained/grappled.",
        },
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST  (python behavior_tree_engine.py)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    PASS = 0
    FAIL = 0

    def check(name: str, condition: bool):
        global PASS, FAIL
        if condition:
            print(f"  PASS  {name}")
            PASS += 1
        else:
            print(f"  FAIL  {name}")
            FAIL += 1

    print("=== Behavior Tree Engine Self-Test ===\n")

    # ── Fixtures ──────────────────────────────────────────────────────────────
    _enemy = {
        "id": "goblin_1",
        "name": "Goblin",
        "hp": 7,
        "max_hp": 7,
        "ac": 15,
        "attack_bonus": 4,
        "damage_die": "1d6+2",
        "damage_type": "slashing",
        "type": "humanoid",
        "special_abilities": ["nimble_escape"],
        "ability_charges": {},
        "grid_x": 5, "grid_y": 2,
    }
    _player = {"hp": 10, "max_hp": 30, "ac": 14, "conditions": []}
    _ctx_base = {
        "round": 1,
        "alive_enemies": [_enemy],
        "player_grid_x": 4, "player_grid_y": 2,
    }

    # ── 1. build_context ─────────────────────────────────────────────────────
    print("1. build_context")
    ctx = build_context(_enemy, _player, _ctx_base)
    check("enemy_hp_pct=1.0 when full", abs(ctx["enemy_hp_pct"] - 1.0) < 0.001)
    check("player_hp_pct correct", abs(ctx["player_hp_pct"] - (10/30)) < 0.001)
    check("in_melee_range True when dist==1", ctx["in_melee_range"] is True)
    check("distance_to_player==1", ctx["distance_to_player"] == 1)

    # ── 2. Conditions ─────────────────────────────────────────────────────────
    print("\n2. Conditions")
    check("hp_below 0.25 → False (full HP)", _eval_condition({"check": "hp_below", "value": 0.25}, ctx) is False)
    check("hp_above 0.5 → True (full HP)", _eval_condition({"check": "hp_above", "value": 0.5}, ctx) is True)
    check("in_melee_range → True", _eval_condition({"check": "in_melee_range"}, ctx) is True)
    check("is_first_round → True", _eval_condition({"check": "is_first_round"}, ctx) is True)
    check("round_above 0 → True", _eval_condition({"check": "round_above", "value": 0}, ctx) is True)
    check("round_above 5 → False", _eval_condition({"check": "round_above", "value": 5}, ctx) is False)
    check("took_fire_damage → False", _eval_condition({"check": "took_fire_damage"}, ctx) is False)
    check("has_special nimble_escape → True", _eval_condition({"check": "has_special", "value": "nimble_escape"}, ctx) is True)
    check("has_special life_drain → False", _eval_condition({"check": "has_special", "value": "life_drain"}, ctx) is False)
    check("is_enemy_type humanoid → True", _eval_condition({"check": "is_enemy_type", "value": "humanoid"}, ctx) is True)
    check("ability_ready breath_weapon → False", _eval_condition({"check": "ability_ready", "value": "breath_weapon"}, ctx) is False)

    # ── 3. Action: attack_melee ───────────────────────────────────────────────
    print("\n3. Actions")
    action_node = {
        "type": "action",
        "action": "attack_melee",
        "damage_die": "1d6+2",
        "damage_type": "slashing",
        "label": "Scimitar",
    }
    ok, act = evaluate(action_node, ctx)
    check("attack_melee fires", ok is True and act is not None)
    check("correct damage_die", act["damage_die"] == "1d6+2")
    check("action_type == attack", act["action_type"] == "attack")

    flee_node = {"type": "action", "action": "flee"}
    ok, act = evaluate(flee_node, ctx)
    check("flee fires", ok is True and act["action_type"] == "flee")

    # ── 4. Goblin tree (selector) ─────────────────────────────────────────────
    print("\n4. Goblin tree")
    goblin_tree = {
        "type": "selector",
        "children": [
            {"type": "sequence", "children": [
                {"type": "condition", "check": "hp_below", "value": 0.25},
                {"type": "action", "action": "flee", "label": "Nimble Escape"},
            ]},
            {"type": "sequence", "children": [
                {"type": "condition", "check": "in_melee_range"},
                {"type": "action", "action": "attack_melee", "damage_die": "1d6+2", "damage_type": "slashing", "label": "Scimitar"},
            ]},
            {"type": "action", "action": "move_toward_player"},
        ],
    }
    # Full HP + in melee → attack
    ok, act = evaluate(goblin_tree, ctx)
    check("goblin in melee → attack", ok and act["action_type"] == "attack")
    # Wounded goblin → flee
    wounded_enemy = dict(_enemy, hp=1)
    wounded_ctx = build_context(wounded_enemy, _player, _ctx_base)
    ok, act = evaluate(goblin_tree, wounded_ctx)
    check("goblin <25% HP → flee", ok and act["action_type"] == "flee")

    # ── 5. NOT decorator ──────────────────────────────────────────────────────
    print("\n5. NOT decorator")
    not_node = {"type": "not", "child": {"type": "condition", "check": "took_fire_damage"}}
    ok, _ = evaluate(not_node, ctx)
    check("NOT took_fire_damage → True", ok is True)

    # ── 6. Regenerate suppression ─────────────────────────────────────────────
    print("\n6. Regeneration suppression")
    regen_enemy = dict(_enemy, hp=60, max_hp=84, took_fire_damage_last_turn=True)
    regen_ctx = build_context(regen_enemy, _player, _ctx_base)
    regen_node = {"type": "action", "action": "regenerate", "amount": 10}
    ok, act = evaluate(regen_node, regen_ctx)
    check("regenerate suppressed by fire → returns False", ok is False and act is None)
    # Without fire damage
    clean_enemy = dict(_enemy, hp=60, max_hp=84, took_fire_damage_last_turn=False)
    clean_ctx = build_context(clean_enemy, _player, _ctx_base)
    ok, act = evaluate(regen_node, clean_ctx)
    check("regenerate not suppressed → fires", ok is True and act is not None)

    # ── 7. Breath weapon + charge decrement ───────────────────────────────────
    print("\n7. Breath weapon")
    dragon_enemy = dict(
        _enemy, name="Young Dragon", hp=136, max_hp=136,
        ability_charges={"breath_weapon": 1},
        type="dragon"
    )
    dragon_ctx = build_context(dragon_enemy, _player, _ctx_base)
    breath_node = {
        "type": "action",
        "action": "breath_weapon",
        "damage_die": "10d10",
        "damage_type": "fire",
        "dc": 18,
        "shape": "cone",
        "label": "Fire Breath",
    }
    ok, act = evaluate(breath_node, dragon_ctx)
    check("breath_weapon fires", ok and act["action_type"] == "special_attack")
    check("charge decremented to 0", dragon_enemy["ability_charges"]["breath_weapon"] == 0)

    # ── 8. run_tree ───────────────────────────────────────────────────────────
    print("\n8. run_tree")
    result = run_tree(goblin_tree, _enemy, _player, _ctx_base)
    check("run_tree returns attack dict", result.get("action_type") == "attack")
    check("run_tree has all required keys", all(
        k in result for k in ("action_type", "attack_bonus", "damage_die", "damage_type",
                               "advantage", "disadvantage", "adv_reason", "special_effect",
                               "grid_move", "narration_hint", "abilities_used")
    ))

    # ── 9. Metadata lists ─────────────────────────────────────────────────────
    print("\n9. Metadata")
    conds = list_available_conditions()
    acts = list_available_actions()
    check("conditions non-empty", len(conds) >= 15)
    check("actions non-empty", len(acts) >= 14)
    check("all conditions have id+label+description", all("id" in c and "label" in c and "description" in c for c in conds))

    # ── 10. Depth guard ───────────────────────────────────────────────────────
    print("\n10. Depth guard")
    deep_node: Dict[str, Any] = {"type": "selector", "children": []}
    cur = deep_node
    for _ in range(25):
        child: Dict[str, Any] = {"type": "selector", "children": []}
        cur["children"].append(child)
        cur = child
    cur["children"].append({"type": "action", "action": "attack_melee", "damage_die": "1d6", "damage_type": "slashing"})
    ok, act = evaluate(deep_node, ctx)
    check("depth guard prevents crash (returns False)", ok is False)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*40}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    if FAIL:
        sys.exit(1)
    print("All tests passed.")
