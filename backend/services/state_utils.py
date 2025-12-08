"""
State mutation utilities for world_state and character_state updates.
"""
from typing import Dict, Any


def apply_world_state_update(world_state: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply world_state_update diff to world_state.
    
    Handles:
    - npc_updates: location, disposition, alive, flags, conditions, secrets_known_to_player
    - faction_updates: influence_score, hostility_to_player, active_plots
    - location_updates: state changes (locked/unlocked/damaged/safe/unsafe)
    """
    ws = dict(world_state)  # shallow copy, we'll modify nested dicts
    
    # NPC updates
    for u in update.get("npc_updates", []):
        npc_id = u.get("npc_id")
        if not npc_id:
            continue
        
        npc_state = ws.setdefault("npc_state", {})
        npc_entry = npc_state.setdefault(npc_id, {"npc_id": npc_id})
        
        for key in ["location", "disposition", "alive", "flags", "conditions", "secrets_known_to_player"]:
            if key in u and u[key] is not None:
                npc_entry[key] = u[key]
    
    # Faction updates
    for u in update.get("faction_updates", []):
        faction_id = u.get("faction_id")
        if not faction_id:
            continue
        
        faction_state = ws.setdefault("faction_state", {})
        faction_entry = faction_state.setdefault(faction_id, {"faction_id": faction_id})
        
        for key in ["influence_score", "hostility_to_player", "active_plots", "plot_progress"]:
            if key in u and u[key] is not None:
                faction_entry[key] = u[key]
    
    # Location updates
    for u in update.get("location_updates", []):
        location_id = u.get("location_id")
        if not location_id:
            continue
        
        location_state = ws.setdefault("location_state", {})
        location_entry = location_state.setdefault(location_id, {"location_id": location_id})
        
        if "state" in u:
            location_entry["state"] = u["state"]
    
    return ws


def apply_player_updates(character_state: Dict[str, Any], player_updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply player_updates to character_state.
    
    Handles:
    - inventory_add/inventory_remove
    - conditions_add/conditions_remove
    - reputation_changes (faction_id -> delta)
    """
    cs = dict(character_state)
    
    inv = cs.setdefault("inventory", [])
    cond = cs.setdefault("conditions", [])
    rep = cs.setdefault("reputation", {})
    
    # Inventory
    for item in player_updates.get("inventory_add", []):
        if item not in inv:
            inv.append(item)
    
    for item in player_updates.get("inventory_remove", []):
        if item in inv:
            inv.remove(item)
    
    # Conditions
    for c in player_updates.get("conditions_add", []):
        if c not in cond:
            cond.append(c)
    
    for c in player_updates.get("conditions_remove", []):
        if c in cond:
            cond.remove(c)
    
    # Reputation
    for faction_id, delta in player_updates.get("reputation_changes", {}).items():
        rep[faction_id] = rep.get(faction_id, 0) + delta
    
    cs["inventory"] = inv
    cs["conditions"] = cond
    cs["reputation"] = rep
    
    return cs


def apply_combat_player_update(character_state: Dict[str, Any], player_update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply combat player_update to character_state.
    
    Handles:
    - hp changes
    - conditions changes
    - status (alive/down/dead)
    """
    cs = dict(character_state)
    
    if "hp" in player_update and player_update["hp"] is not None:
        cs["hp"] = player_update["hp"]
    
    if "conditions" in player_update and player_update["conditions"] is not None:
        cs["conditions"] = player_update["conditions"]
    
    # status can be used later for death/unconsciousness mechanics
    
    return cs
