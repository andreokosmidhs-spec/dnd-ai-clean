"""
COMPLETE COMBAT ENGINE Service - D&D 5e combat with target resolution, NPC conversion, and plot armor.

Features:
- Priority-based target resolution
- NPC-to-enemy conversion for hostile actions
- Plot armor protection for essential NPCs
- Strict D&D 5e mechanical combat resolution
- Proper combat state cleanup (combat_over = true)
- Non-lethal damage for protected NPCs
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from services.target_resolver import resolve_target, is_hostile_action
from services.plot_armor_service import check_plot_armor, apply_plot_armor_consequences
from services.dnd_rules import (
    resolve_attack,
    apply_damage_to_target,
    calculate_ability_modifier,
    compute_advantage_flags,
)

logger = logging.getLogger(__name__)


def convert_npc_to_enemy(
    npc_data: Dict[str, Any],
    world_blueprint: Dict[str, Any],
    character_level: int = 1
) -> Dict[str, Any]:
    """
    Convert an NPC to an enemy combatant.
    
    Args:
        npc_data: NPC data from world_blueprint
        world_blueprint: Full world blueprint
        character_level: Player character level (for scaling)
    
    Returns:
        Enemy dict compatible with CombatParticipant model
    """
    # Basic stats based on NPC role
    role = npc_data.get('role', '').lower()
    
    # Default stats
    base_hp = 15
    ac = 12
    abilities = {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10}
    damage_die = "1d6"
    proficiency_bonus = 2
    
    # Adjust stats based on role
    if 'guard' in role or 'soldier' in role:
        base_hp = 20
        ac = 14
        abilities["str"] = 14
        abilities["con"] = 12
        damage_die = "1d8"
    elif 'merchant' in role or 'innkeeper' in role:
        base_hp = 10
        ac = 10
        abilities["dex"] = 12
        abilities["cha"] = 14
        damage_die = "1d4"
    elif 'thief' in role or 'rogue' in role:
        base_hp = 12
        ac = 13
        abilities["dex"] = 16
        abilities["str"] = 8
        damage_die = "1d6"
    elif 'mage' in role or 'wizard' in role:
        base_hp = 8
        ac = 11
        abilities["int"] = 16
        abilities["dex"] = 12
        damage_die = "1d4"
    
    # Scale HP for character level
    scaled_hp = base_hp + (character_level - 1) * 2

    # Create enemy ID
    enemy_id = f"npc_enemy_{npc_data.get('id', npc_data.get('name', 'unknown').lower().replace(' ', '_'))}"

    enemy = {
        "id": enemy_id,
        "name": npc_data.get('name', 'Hostile NPC'),
        "hp": scaled_hp,
        "max_hp": scaled_hp,
        "ac": ac,
        "abilities": abilities,
        "proficiency_bonus": proficiency_bonus,
        "attack_bonus": 0,
        "damage_die": damage_die,
        "conditions": [],
        "faction_id": None,
        "participant_type": "npc",
        "is_essential": False,
        "plot_armor_attempts": 0,
    }

    # Derive behavior tree from NPC character card (role + personality_tags)
    try:
        from services.npc_behavior_mapper import get_behavior_tree_for_npc
        npc_tree = get_behavior_tree_for_npc({**npc_data, "damage_die": damage_die})
        enemy["behavior_tree"] = npc_tree
        enemy["behavior_tree_id"] = npc_tree["id"]
        logger.info(f"🎭 {enemy['name']} behavior tree: {npc_tree['_source_tree']} (flee@{npc_tree.get('_flee_threshold')})")
    except Exception as e:
        logger.warning(f"⚠️ Could not map NPC behavior for {enemy['name']}: {e}")

    return enemy


def start_combat_with_target(
    target_resolution: Dict[str, Any],
    character_state: Dict[str, Any],
    world_blueprint: Dict[str, Any],
    character_level: int = 1,
    world_state: Optional[Dict[str, Any]] = None,
    battlefield_grid: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Initialize combat state with a resolved target.

    Args:
        target_resolution: Result from target_resolver
        character_state: Player character state
        world_blueprint: World blueprint
        character_level: Player character level
        world_state: Optional world_state dict (time/location → light level)

    Returns:
        CombatState dict
    """
    from services.light_level_service import compute_light_level, passive_condition_chip
    from services.dnd_rules import roll_d20, calculate_ability_modifier

    ws = world_state or {}
    clock_hour = ws.get("clock_hour", 9)
    location_name = ws.get("current_location") or ws.get("location") or ""
    light_level = compute_light_level(clock_hour, location_name)
    battlefield = {
        "name": location_name or "Unknown Location",
        "light_level": light_level,
        "passive_conditions": [c for c in [passive_condition_chip(light_level)] if c],
    }

    enemies = []
    converted_npcs = []

    if target_resolution['target_type'] == 'npc':
        npc_enemy = convert_npc_to_enemy(
            target_resolution['target_data'],
            world_blueprint,
            character_level
        )
        name_lower = (npc_enemy.get("name") or "").lower()
        npc_enemy["lane"] = 3 if any(k in name_lower for k in ("mage", "wizard", "archer")) else 2
        enemies.append(npc_enemy)
        converted_npcs.append(target_resolution['target_id'])
        logger.info(f"⚔️ Converted NPC {target_resolution['target_name']} to enemy")
    elif target_resolution['target_type'] == 'enemy':
        enemies.append(target_resolution['target_data'])
        logger.info(f"⚔️ Starting combat with enemy {target_resolution['target_name']}")

    # Assign grid positions to enemies based on their lane
    from services.battlefield_layout_service import enemy_start_positions
    enemies = enemy_start_positions(enemies)

    # ── Roll initiative for every participant (d20 + DEX mod) ─────────────────
    def _dex(abilities_dict):
        return int((abilities_dict or {}).get("dex") or (abilities_dict or {}).get("DEX") or 10)

    char_abilities = character_state.get("abilities") or character_state.get("abilityScores") or {}
    player_dex = _dex(char_abilities)
    player_roll = roll_d20()
    player_init = player_roll + calculate_ability_modifier(player_dex)

    char_name = (
        character_state.get("identity", {}).get("name")
        or character_state.get("name", "You")
    )

    initiative_order = [{
        "id": "player",
        "name": char_name,
        "score": player_init,
        "roll": player_roll,
        "dex_mod": calculate_ability_modifier(player_dex),
        "type": "player",
    }]

    for enemy in enemies:
        enemy_dex = _dex(enemy.get("abilities"))
        e_roll = roll_d20()
        e_init = e_roll + calculate_ability_modifier(enemy_dex)
        initiative_order.append({
            "id": enemy["id"],
            "name": enemy["name"],
            "score": e_init,
            "roll": e_roll,
            "dex_mod": calculate_ability_modifier(enemy_dex),
            "type": "enemy",
        })

    initiative_order.sort(key=lambda x: x["score"], reverse=True)
    turn_order = [p["id"] for p in initiative_order]
    first_turn = turn_order[0]

    logger.info(
        f"⚔️ Initiative rolled — order: "
        + ", ".join(f"{p['name']} ({p['score']})" for p in initiative_order)
    )

    combat_state = {
        "enemies": enemies,
        "participants": [],
        "turn_order": turn_order,
        "initiative_order": initiative_order,
        "active_turn": first_turn,
        "round": 1,
        "combat_over": False,
        "outcome": None,
        "converted_npcs": converted_npcs,
        "battlefield": battlefield,
        "light_level": light_level,
        "player_lane": 1,
        "player_grid_x": 1,
        "player_grid_y": 2,
        "battlefield_grid": battlefield_grid,
        "player_turn_state": {
            "action_used": False,
            "bonus_action_used": False,
            "reaction_used": False,
        },
    }

    logger.info(f"⚔️ Combat initialized: {len(enemies)} enemies, light={light_level['level']}, first turn: {first_turn}")
    return combat_state


def process_player_attack(
    target_id: str,
    character_state: Dict[str, Any],
    combat_state: Dict[str, Any],
    force_non_lethal: bool = False,
    weapon_type: str = "melee",
    weapon_damage: str = "1d4",
    weapon_name: str = "Unarmed",
) -> Dict[str, Any]:
    """
    Process player's attack action with strict D&D 5e mechanics.

    Args:
        target_id: ID of the target to attack
        character_state: Player character data
        combat_state: Current combat state
        force_non_lethal: If True, target becomes unconscious instead of dying
        weapon_type: "melee", "finesse", or "ranged" (resolved by weapon_service)
        weapon_damage: Dice notation e.g. "1d8" (resolved by weapon_service)
        weapon_name: Display name for the weapon used

    Returns:
        {
            "success": bool,
            "mechanical_summary": dict,  # Structured combat results for DM
            "combat_state_update": dict,
            "character_state_update": dict,
            "combat_over": bool,
            "xp_gained": int
        }
    """
    # Find target enemy
    enemies = combat_state.get('enemies', [])
    target = None
    for enemy in enemies:
        if enemy['id'] == target_id and enemy['hp'] > 0:
            target = enemy
            break

    if not target:
        logger.error(f"❌ Target {target_id} not found or already defeated")
        return {
            "success": False,
            "mechanical_summary": {
                "error": f"Target {target_id} not found or already defeated"
            },
            "combat_state_update": {},
            "character_state_update": {},
            "combat_over": False,
            "xp_gained": 0
        }

    # is_unarmed determined from weapon name
    is_unarmed = weapon_name.lower() in ("unarmed", "unarmed strike")

    # Prepare attacker data (player)
    attacker = {
        "abilities": character_state.get('abilities', {}),
        "proficiency_bonus": character_state.get('proficiency_bonus', 2),
        "attack_bonus": character_state.get('attack_bonus', 0)
    }

    # Compute advantage / disadvantage flags from conditions
    attacker_conditions = character_state.get("conditions", [])
    target_conditions = target.get("conditions", [])
    blinded = combat_state.get("light_level", {}).get("blinded", False)
    mech_adv, mech_disadv, adv_sources, disadv_sources = compute_advantage_flags(
        attacker_conditions, target_conditions, weapon_type, blinded
    )

    # Merge with DM-granted narrative advantage/disadvantage
    dm_adv    = combat_state.get("_dm_advantage", False)
    dm_disadv = combat_state.get("_dm_disadvantage", False)
    dm_reason = combat_state.get("_dm_advantage_reason", "")
    if dm_adv:
        adv_sources.append(f"DM: {dm_reason}" if dm_reason else "DM: scene context")
    if dm_disadv:
        disadv_sources.append(f"DM: {dm_reason}" if dm_reason else "DM: scene context")

    advantage    = mech_adv    or dm_adv
    disadvantage = mech_disadv or dm_disadv

    # PHB: any combination of adv+disadv cancels to straight roll
    if advantage and disadvantage:
        adv_sources.append("(cancelled by opposing disadvantage)")
        disadv_sources.append("(cancelled by opposing advantage)")

    # Resolve attack using strict D&D 5e rules
    attack_result = resolve_attack(
        attacker=attacker,
        target=target,
        weapon_type=weapon_type,
        weapon_damage=weapon_damage,
        is_unarmed=is_unarmed,
        force_non_lethal=force_non_lethal,
        advantage=advantage,
        disadvantage=disadvantage,
    )

    # Update target HP
    target['hp'] = attack_result['new_target_hp']

    # Handle unconscious state
    if attack_result['knocked_unconscious']:
        target['conditions'] = target.get('conditions', [])
        if 'unconscious' not in target['conditions']:
            target['conditions'].append('unconscious')
        logger.info(f"😴 {target['name']} knocked unconscious")

    # Check if all enemies are defeated
    alive_enemies = [e for e in enemies if e['hp'] > 0]
    combat_over = len(alive_enemies) == 0

    # Morale cascade if a leader was just killed
    if attack_result.get('killed'):
        try:
            from services.faction_combat_service import apply_death_morale
            apply_death_morale(target, alive_enemies)
        except Exception:
            pass

    # Update combat state - CRITICAL: Always set combat_over correctly
    combat_state_update = {
        "enemies": enemies,
        "combat_over": combat_over,
        "outcome": "victory" if combat_over else None
    }

    # Calculate XP if combat ended in victory
    xp_gained = 0
    if combat_over:
        try:
            from services.progression_service import calculate_xp_for_enemy
            xp_gained = sum(calculate_xp_for_enemy(e) for e in enemies)
            logger.info(f"💰 Combat victory! Awarding {xp_gained} XP")
        except Exception as e:
            logger.warning(f"⚠️ Could not calculate XP: {e}")
            xp_gained = 0

    return {
        "success": True,
        "mechanical_summary": {
            "attacker": character_state.get('name', 'You'),
            "target": target['name'],
            "weapon_name": weapon_name,
            "weapon_damage": weapon_damage,
            "attack_roll": attack_result['roll'],
            "total_attack": attack_result['total_attack'],
            "target_ac": attack_result['target_ac'],
            "hit": attack_result['hit'],
            "critical": attack_result['is_crit'],
            "critical_miss": attack_result['critical_miss'],
            "damage": attack_result['damage'],
            "target_hp_remaining": attack_result['new_target_hp'],
            "target_max_hp": target['max_hp'],
            "target_killed": attack_result['killed'],
            "knocked_unconscious": attack_result['knocked_unconscious'],
            "ability_used": attack_result['ability_used'],
            "advantage": advantage,
            "disadvantage": disadvantage,
            "adv_sources": adv_sources,
            "disadv_sources": disadv_sources,
            "roll1": attack_result.get("roll1"),
            "roll2": attack_result.get("roll2"),
        },
        "combat_state_update": combat_state_update,
        "character_state_update": {},
        "combat_over": combat_over,
        "xp_gained": xp_gained
    }


def process_save_spell(
    spell_name: str,
    spell_card: Dict[str, Any],
    caster_state: Dict[str, Any],
    target: Dict[str, Any],
    spell_save_dc: int,
    combat_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Resolve a saving-throw based spell attack (e.g. Fireball, Sacred Flame).

    Returns same shape as process_player_attack for easy substitution.
    """
    from services.dnd_rules import roll_dice, roll_d20, calculate_ability_modifier, proficiency_bonus_for_level
    from services.saving_throw_service import roll_saving_throw

    save_type      = spell_card.get("save_type", "dex")
    half_on_save   = bool(spell_card.get("half_on_save", True))
    damage_dice    = spell_card.get("damage_dice") or "1d6"
    damage_type    = spell_card.get("damage_type") or "force"
    cond_on_fail   = spell_card.get("condition_on_fail")

    # Roll the save for the target
    target_state_for_save = {
        "abilities": target.get("abilities", {}),
        "class_": target.get("type", "enemy"),
        "level": 1,
    }
    save_result = roll_saving_throw(
        character_state=target_state_for_save,
        ability=save_type,
        dc=spell_save_dc,
    )

    # Roll damage
    raw_damage = roll_dice(damage_dice)
    damage = raw_damage // 2 if (save_result["success"] and half_on_save) else raw_damage
    if save_result["success"] and not half_on_save:
        damage = 0

    # Apply resistances / immunities
    resistances = [r.lower() for r in target.get("resistances", [])]
    immunities  = [i.lower() for i in target.get("immunities", [])]
    dt = damage_type.lower()
    if dt in immunities:
        damage = 0
    elif dt in resistances:
        damage = damage // 2

    # Apply damage
    old_hp = target["hp"]
    target["hp"] = max(0, old_hp - damage)
    killed = target["hp"] <= 0

    # Apply condition on failed save
    if cond_on_fail and not save_result["success"]:
        conditions = target.get("conditions", [])
        if cond_on_fail not in conditions:
            conditions.append(cond_on_fail)
            target["conditions"] = conditions

    enemies = combat_state.get("enemies", [])
    for i, e in enumerate(enemies):
        if e["id"] == target["id"]:
            enemies[i] = target
            break
    alive_enemies = [e for e in enemies if e["hp"] > 0]
    combat_over = len(alive_enemies) == 0

    # Morale cascade when a leader is killed
    if killed:
        try:
            from services.faction_combat_service import apply_death_morale
            apply_death_morale(target, alive_enemies)
        except Exception:
            pass

    xp_gained = 0
    if combat_over:
        try:
            from services.progression_service import calculate_xp_for_enemy
            xp_gained = sum(calculate_xp_for_enemy(e) for e in enemies)
        except Exception:
            pass

    return {
        "success": True,
        "mechanical_summary": {
            "attacker": caster_state.get("name", "You"),
            "target": target["name"],
            "spell_name": spell_name,
            "save_type": save_type.upper(),
            "spell_save_dc": spell_save_dc,
            "save_roll": save_result["total"],
            "save_success": save_result["success"],
            "half_on_save": half_on_save,
            "damage_dice": damage_dice,
            "damage": damage,
            "damage_type": damage_type,
            "condition_applied": cond_on_fail if cond_on_fail and not save_result["success"] else None,
            "target_hp_remaining": target["hp"],
            "target_max_hp": target["max_hp"],
            "target_killed": killed,
            "is_save_spell": True,
        },
        "combat_state_update": {
            "enemies": enemies,
            "combat_over": combat_over,
            "outcome": "victory" if combat_over else None,
        },
        "character_state_update": {},
        "combat_over": combat_over,
        "xp_gained": xp_gained,
    }


def process_enemy_turns(
    character_state: Dict[str, Any],
    combat_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process all enemy turns using D&D 5e mechanics with behavior-tree decisions.

    Each alive enemy consults decide_enemy_action() to choose how to act this
    turn, then the chosen action is resolved through the standard attack pipeline.

    Args:
        character_state: Player character state
        combat_state: Current combat state

    Returns:
        {
            "enemy_actions": list of mechanical summaries,
            "total_damage_to_player": int,
            "character_state_update": dict,
            "combat_over": bool
        }
    """
    from services.enemy_behavior_service import decide_enemy_action, apply_special_effect
    from services.dnd_rules import roll_d20 as _roll_d20
    from services.faction_combat_service import (
        assign_faction_roles, faction_context_for, apply_morale_modifiers
    )

    enemies = combat_state.get('enemies', [])
    alive_enemies = [e for e in enemies if e.get('hp', 0) > 0]

    if not alive_enemies:
        return {
            "enemy_actions": [],
            "total_damage_to_player": 0,
            "character_state_update": {},
            "combat_over": False
        }

    # Assign faction roles if not already done (idempotent — skips if role set)
    if any("faction_role" not in e for e in alive_enemies):
        assign_faction_roles(alive_enemies)

    enemy_actions = []
    total_damage = 0
    player_hp = character_state.get('hp', 10)
    player_max_hp = character_state.get('max_hp', 10)

    # Prepare mutable target dict (player)
    player_target = {
        "ac": character_state.get('ac', 10),
        "hp": player_hp,
        "max_hp": player_max_hp,
        "name": character_state.get('name', 'Player'),
        "abilities": character_state.get('abilities', {}),
        "conditions": character_state.get('conditions', []),
    }

    # Build base combat context for behavior decisions
    base_combat_context: Dict[str, Any] = {
        "round": combat_state.get('round', 1),
        "alive_enemies": alive_enemies,
        "grid_cells": (combat_state.get('battlefield_grid') or {}).get('cells', []),
        "player_grid_x": combat_state.get('player_grid_x', 1),
        "player_grid_y": combat_state.get('player_grid_y', 2),
    }

    for enemy in alive_enemies:
        enemy_name = enemy.get('name', 'Unknown Enemy')

        # ── Faction context (per-enemy) ───────────────────────────────────────
        faction_ctx = faction_context_for(enemy, alive_enemies)
        combat_context = {**base_combat_context, **faction_ctx}

        # ── Morale override (leader death) ────────────────────────────────────
        morale_action = apply_morale_modifiers(enemy, combat_context)

        # ── Behavior tree decision ────────────────────────────────────────────
        try:
            action = morale_action or decide_enemy_action(enemy, player_target, combat_context)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Behavior tree failed for %s: %s — using plain attack", enemy_name, exc)
            action = {
                "action_type": "attack",
                "attack_bonus": enemy.get("attack_bonus", 3),
                "damage_die": enemy.get("damage_die", "1d6"),
                "damage_type": enemy.get("damage_type", "slashing"),
                "advantage": False,
                "disadvantage": False,
                "adv_reason": "",
                "special_effect": None,
                "grid_move": None,
                "narration_hint": f"The {enemy_name} attacks.",
                "abilities_used": [],
            }

        action_type = action.get("action_type", "attack")

        # ── Apply grid move first (if any) ───────────────────────────────────
        grid_move = action.get("grid_move")
        if grid_move:
            enemy["grid_x"] = enemy.get("grid_x", 2) + grid_move.get("dx", 0)
            enemy["grid_y"] = enemy.get("grid_y", 2) + grid_move.get("dy", 0)

        # ── Fled / Regenerated — no attack ───────────────────────────────────
        if action_type == "flee":
            enemy["hp"] = 0  # Mark as out of combat (fled)
            enemy_actions.append({
                "attacker": enemy_name,
                "action_type": "flee",
                "attack_roll": 0,
                "total_attack": 0,
                "target_ac": player_target["ac"],
                "hit": False,
                "critical": False,
                "critical_miss": False,
                "damage": 0,
                "narration_hint": action.get("narration_hint", f"{enemy_name} fled."),
                "abilities_used": action.get("abilities_used", []),
            })
            continue

        if action_type == "regenerate":
            enemy_actions.append({
                "attacker": enemy_name,
                "action_type": "regenerate",
                "attack_roll": 0,
                "total_attack": 0,
                "target_ac": player_target["ac"],
                "hit": False,
                "critical": False,
                "critical_miss": False,
                "damage": 0,
                "healed": action.get("special_effect", {}).get("healed", 0),
                "narration_hint": action.get("narration_hint", f"{enemy_name} regenerates."),
                "abilities_used": action.get("abilities_used", []),
            })
            continue

        # ── Resolve the attack ────────────────────────────────────────────────
        adv = action.get("advantage", False)
        disadv = action.get("disadvantage", False)
        weapon_damage = action.get("damage_die") or enemy.get("damage_die", "1d6")

        attack_result = resolve_attack(
            attacker=enemy,
            target=player_target,
            weapon_type="melee",
            weapon_damage=weapon_damage,
            is_unarmed=False,
            advantage=adv,
            disadvantage=disadv,
        )

        hit = attack_result.get("hit", False)
        damage_dealt = attack_result.get("damage", 0)
        total_damage += damage_dealt
        player_target["hp"] = attack_result["target_hp_remaining"]

        # ── Apply special effect on hit ───────────────────────────────────────
        special_effect_result = None
        special_effect = action.get("special_effect")
        if special_effect and hit and action_type in ("special_attack",):
            eff_type = special_effect.get("type", "")

            if eff_type in ("life_drain", "undead_fortitude"):
                special_effect["damage_dealt"] = damage_dealt
                special_effect_result = apply_special_effect(
                    special_effect, player_target, _roll_d20
                )
            elif eff_type == "surprise_attack":
                # Roll extra damage dice
                from services.dnd_rules import roll_dice as _roll_dice
                bonus_die = special_effect.get("bonus_damage_die", "2d6")
                try:
                    bonus_dmg = _roll_dice(bonus_die)
                except Exception:
                    bonus_dmg = 0
                damage_dealt += bonus_dmg
                total_damage += bonus_dmg
                player_target["hp"] = max(0, player_target["hp"] - bonus_dmg)
                special_effect_result = {
                    "effect_type": "surprise_attack",
                    "triggered": True,
                    "bonus_damage": bonus_dmg,
                    "description": f"Surprise Attack deals {bonus_dmg} extra damage.",
                }
            elif eff_type == "reckless_attack":
                # Flag enemy for advantage-to-attackers this turn
                enemy["_reckless_this_turn"] = True
                special_effect_result = apply_special_effect(
                    special_effect, enemy, _roll_d20
                )

        # ── Undead Fortitude check (enemy would die from player damage) ───────
        # NOTE: This is only for when the enemy itself is at 0 HP after being hit,
        # but here we're resolving enemy attacks on the player. The symmetric check
        # (player reducing enemy to 0) happens in the caller's damage-apply step.
        # We leave the enemy UF check to be called by apply_damage_to_enemy helper
        # if added by callers. For now we track the flag in the enemy dict.

        action_summary: Dict[str, Any] = {
            "attacker": enemy_name,
            "action_type": action_type,
            "attack_roll": attack_result.get("attack_roll", 0),
            "total_attack": attack_result.get("total_attack", 0),
            "target_ac": player_target["ac"],
            "hit": hit,
            "critical": attack_result.get("critical", False),
            "critical_miss": attack_result.get("critical_miss", False),
            "damage": damage_dealt,
            "advantage": adv,
            "disadvantage": disadv,
            "adv_reason": action.get("adv_reason", ""),
            "narration_hint": action.get("narration_hint", ""),
            "abilities_used": action.get("abilities_used", []),
        }
        if special_effect_result:
            action_summary["special_effect_result"] = special_effect_result

        enemy_actions.append(action_summary)

    # ── Update player HP ──────────────────────────────────────────────────────
    new_player_hp = player_target["hp"]
    player_dying = new_player_hp <= 0

    char_state_update: Dict[str, Any] = {"hp": new_player_hp}
    if player_dying:
        char_state_update["death_saves"] = {
            "successes": 0, "failures": 0, "stable": False, "dead": False
        }
        logger.warning("Player HP dropped to 0 — entering dying state (death saves)")

    return {
        "enemy_actions": enemy_actions,
        "total_damage_to_player": total_damage,
        "character_state_update": char_state_update,
        "combat_over": False,   # Wait for death saves
        "player_dying": player_dying,
        "death_saves": char_state_update.get("death_saves"),
        "outcome": None,
    }


def check_and_apply_plot_armor(
    npc_data: Dict[str, Any],
    world_blueprint: Dict[str, Any],
    world_state: Dict[str, Any],
    character_state: Dict[str, Any],
    action_type: str = "attack"
) -> Dict[str, Any]:
    """
    Check if NPC has plot armor and handle consequences.
    
    Returns:
        {
            "status": "blocked" | "allowed" | "forced_non_lethal",
            "plot_armor_outcome": PlotArmorOutcome dict,
            "world_state_update": dict,
            "character_state_update": dict,
            "narrative_hint": str
        }
    """
    # Check plot armor
    plot_armor_outcome = check_plot_armor(
        npc_data=npc_data,
        world_blueprint=world_blueprint,
        world_state=world_state,
        action_type=action_type
    )
    
    if not plot_armor_outcome['handled']:
        return {
            "status": "allowed",
            "plot_armor_outcome": plot_armor_outcome,
            "world_state_update": {},
            "character_state_update": {},
            "narrative_hint": None
        }
    
    # Plot armor triggered - apply consequences
    logger.warning(f"🛡️ Plot armor activated for {npc_data.get('name')}")
    
    consequence_result = apply_plot_armor_consequences(
        world_state=world_state,
        character_state=character_state,
        consequences=plot_armor_outcome['consequences']
    )
    
    # Determine status
    if plot_armor_outcome['allow_combat']:
        if plot_armor_outcome['mechanical_override'] == 'forced_non_lethal':
            status = "forced_non_lethal"
        else:
            status = "allowed"
    else:
        status = "blocked"
    
    return {
        "status": status,
        "plot_armor_outcome": plot_armor_outcome,
        "world_state_update": consequence_result['world_state_update'],
        "character_state_update": consequence_result['character_state_update'],
        "narrative_hint": plot_armor_outcome['narrative_hint']
    }
