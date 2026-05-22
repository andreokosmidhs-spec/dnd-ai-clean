"""
Faction Combat Service — team tactics, leader/follower roles, morale.

Assigns combat roles to groups of enemies sharing a faction_id, then
provides per-turn context so behavior trees can make coordinated decisions.
Zero LLM calls.

Roles
-----
leader    — commands followers, may rally; high morale, low flee threshold
bodyguard — prioritises staying adjacent to leader; enrages if leader falls
follower  — attacks player, flees or enrages on leader death
flanker   — skirmisher that flanks for advantage; loose loyalty
solo      — default; no faction coordination
"""
from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# ── Role detection ────────────────────────────────────────────────────────────

_LEADER_KEYWORDS = {
    "captain", "chief", "boss", "commander", "general",
    "lieutenant", "sergeant", "leader", "warlord", "elder",
    "master", "overlord", "king", "queen", "prince", "lord",
}
_BODYGUARD_KEYWORDS = {
    "bodyguard", "guardian", "champion", "protector",
    "honor guard", "knight", "paladin",
}
_FLANKER_KEYWORDS = {
    "scout", "ranger", "rogue", "assassin", "skirmisher",
}


def _role_from_name_and_type(enemy: Dict[str, Any]) -> str:
    text = " ".join([
        enemy.get("name", ""),
        enemy.get("role", ""),
        enemy.get("participant_type", ""),
    ]).lower()
    if any(k in text for k in _LEADER_KEYWORDS):
        return "leader"
    if any(k in text for k in _BODYGUARD_KEYWORDS):
        return "bodyguard"
    if any(k in text for k in _FLANKER_KEYWORDS):
        return "flanker"
    return "follower"


# ── Public: assign roles at combat start ─────────────────────────────────────

def assign_faction_roles(enemies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Group enemies by faction_id and assign leader/bodyguard/follower/flanker
    roles. Enemies with no faction_id (or unique ones) get role "solo".
    Mutates enemies in-place and returns the list.
    """
    # Group by faction
    factions: Dict[str, List[Dict]] = {}
    for e in enemies:
        fid = e.get("faction_id")
        if fid:
            factions.setdefault(fid, []).append(e)

    for fid, members in factions.items():
        if len(members) < 2:
            # Solo in a faction — no team dynamics
            members[0]["faction_role"] = "solo"
            continue

        # Detect who leads
        leader = None
        for m in members:
            role = _role_from_name_and_type(m)
            if role == "leader":
                leader = m
                break

        # Fall back: highest HP is the de-facto leader
        if not leader:
            leader = max(members, key=lambda m: m.get("max_hp", 0))

        leader["faction_role"] = "leader"
        leader_id = leader["id"]

        for m in members:
            if m is leader:
                continue
            role = _role_from_name_and_type(m)
            if role == "bodyguard":
                m["faction_role"] = "bodyguard"
            elif role == "flanker":
                m["faction_role"] = "flanker"
            else:
                m["faction_role"] = "follower"
            m["leader_id"] = leader_id

        logger.info(
            "⚔️ Faction '%s': leader=%s, members=%s",
            fid,
            leader.get("name"),
            [m.get("name") for m in members if m is not leader],
        )

    # Enemies without a shared faction get "solo"
    for e in enemies:
        e.setdefault("faction_role", "solo")

    return enemies


# ── Public: per-turn faction context ─────────────────────────────────────────

def faction_context_for(enemy: Dict[str, Any], alive_enemies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Return faction-specific keys to merge into the behavior tree context
    for this enemy's turn.
    """
    role = enemy.get("faction_role", "solo")
    faction_id = enemy.get("faction_id")
    leader_id = enemy.get("leader_id")

    ctx: Dict[str, Any] = {
        "enemy_faction_role": role,
        "faction_leader_alive": True,
        "faction_leader_hp_pct": 1.0,
        "faction_leader_id": None,
        "faction_followers": [],
    }

    if not faction_id:
        return ctx

    faction_members = [e for e in alive_enemies if e.get("faction_id") == faction_id and e["id"] != enemy["id"]]

    # Find leader in alive list
    leader: Optional[Dict] = None
    if role == "leader":
        ctx["faction_leader_alive"] = True
        ctx["faction_leader_hp_pct"] = enemy.get("hp", 1) / max(enemy.get("max_hp", 1), 1)
        ctx["faction_leader_id"] = enemy["id"]
        ctx["faction_followers"] = [e for e in faction_members]
    else:
        if leader_id:
            leader = next((e for e in alive_enemies if e.get("id") == leader_id), None)
        if leader:
            ctx["faction_leader_alive"] = True
            ctx["faction_leader_hp_pct"] = leader.get("hp", 1) / max(leader.get("max_hp", 1), 1)
            ctx["faction_leader_id"] = leader_id
        else:
            ctx["faction_leader_alive"] = False
            ctx["faction_leader_hp_pct"] = 0.0
            ctx["faction_leader_id"] = leader_id

    return ctx


# ── Public: morale cascade on enemy death ────────────────────────────────────

def apply_death_morale(
    dead_enemy: Dict[str, Any],
    survivors: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Called when an enemy dies. If they were a leader, faction members must
    make a morale check (WIS save DC 13). Failures are marked for fleeing;
    survivors become enraged (reckless attack next turn).

    Returns list of (survivor_enemy) dicts, possibly modified with
    "morale_break": True  or  "morale_rage": True.
    """
    from services.dnd_rules import roll_d20, calculate_ability_modifier

    dead_role = dead_enemy.get("faction_role", "solo")
    if dead_role != "leader":
        return survivors  # only leader deaths trigger morale cascade

    faction_id = dead_enemy.get("faction_id")
    if not faction_id:
        return survivors

    MORALE_DC = 13

    for s in survivors:
        if s.get("faction_id") != faction_id:
            continue
        wis = s.get("abilities", {}).get("wis", 10)
        roll = roll_d20() + calculate_ability_modifier(wis)
        if roll < MORALE_DC:
            s["morale_break"] = True
            logger.info("💔 %s breaks morale (rolled %d < DC %d) — will flee", s.get("name"), roll, MORALE_DC)
        else:
            s["morale_rage"] = True
            logger.info("😡 %s rages at leader's death (rolled %d ≥ DC %d)", s.get("name"), roll, MORALE_DC)

    return survivors


# ── Public: inject morale state into behavior tree context ────────────────────

def apply_morale_modifiers(enemy: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    If the enemy has a morale_break or morale_rage flag, override the
    action before the tree is even evaluated.
    Returns None to let tree proceed normally, or an override action dict.
    """
    if enemy.get("morale_break"):
        return {
            "action_type": "flee",
            "attack_bonus": 0,
            "damage_die": "1d4",
            "damage_type": "none",
            "advantage": False,
            "disadvantage": False,
            "adv_reason": "",
            "special_effect": None,
            "grid_move": None,
            "narration_hint": (
                f"{enemy.get('name', 'The enemy')} breaks ranks, fleeing in terror "
                f"at the loss of their leader!"
            ),
            "abilities_used": ["morale_break"],
            "attacks": None,
            "meta": {},
        }
    if enemy.get("morale_rage"):
        # One-shot rage: grant advantage, then clear the flag
        enemy.pop("morale_rage", None)
        return {
            "action_type": "attack",
            "attack_bonus": enemy.get("attack_bonus", 2),
            "damage_die": enemy.get("damage_die", "1d6"),
            "damage_type": enemy.get("damage_type", "slashing"),
            "advantage": True,
            "disadvantage": False,
            "adv_reason": "Enraged by leader's death",
            "special_effect": None,
            "grid_move": None,
            "narration_hint": (
                f"{enemy.get('name', 'The enemy')} screams in fury and attacks recklessly!"
            ),
            "abilities_used": ["morale_rage"],
            "attacks": None,
            "meta": {},
        }
    return None  # proceed normally
