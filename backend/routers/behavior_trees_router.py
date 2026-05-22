"""
Behavior Trees Router
=====================
GET  /api/behavior-trees          — list all trees (custom in MongoDB + defaults not overridden)
GET  /api/behavior-trees/meta     — list available conditions + actions (for editor UI)
GET  /api/behavior-trees/{id}     — get one tree (custom overrides default)
PUT  /api/behavior-trees/{id}     — upsert custom tree in MongoDB behavior_trees collection
POST /api/behavior-trees          — create new custom tree
DELETE /api/behavior-trees/{id}   — delete custom tree (restores default if one exists)
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from data.behavior_trees import DEFAULT_TREES, list_default_trees
from services.behavior_tree_engine import (
    list_available_actions,
    list_available_conditions,
    run_tree,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/behavior-trees", tags=["behavior-trees"])

# Injected by server.py
_db: Optional[AsyncIOMotorDatabase] = None

COLLECTION = "behavior_trees"


def set_database(db: Optional[AsyncIOMotorDatabase]) -> None:
    global _db
    _db = db


def get_db() -> Optional[AsyncIOMotorDatabase]:
    return _db


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _strip_mongo(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Remove MongoDB _id so the dict is JSON-serialisable."""
    doc.pop("_id", None)
    return doc


async def _get_custom_trees() -> Dict[str, Dict[str, Any]]:
    """Fetch all custom trees from MongoDB, keyed by id."""
    if _db is None:
        return {}
    try:
        cursor = _db[COLLECTION].find({})
        docs = await cursor.to_list(length=500)
        return {doc["id"]: _strip_mongo(doc) for doc in docs if "id" in doc}
    except Exception as exc:
        logger.warning("Failed to fetch custom trees: %s", exc)
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/behavior-trees
# ─────────────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[Dict[str, Any]])
async def list_trees():
    """
    Return all behavior trees.
    Custom trees override defaults with the same id.
    Summary list (id, name, description) — no node body.
    """
    custom = await _get_custom_trees()

    result = {}
    # Start with defaults
    for tree_id, tree in DEFAULT_TREES.items():
        result[tree_id] = {
            "id": tree["id"],
            "name": tree["name"],
            "description": tree.get("description", ""),
            "is_custom": False,
        }
    # Override/add custom trees
    for tree_id, tree in custom.items():
        result[tree_id] = {
            "id": tree.get("id", tree_id),
            "name": tree.get("name", tree_id),
            "description": tree.get("description", ""),
            "is_custom": True,
            "updated_at": tree.get("updated_at"),
        }

    return list(result.values())


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/behavior-trees/meta
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/meta")
async def get_meta():
    """Return available conditions and actions for the editor UI."""
    return {
        "conditions": list_available_conditions(),
        "actions": list_available_actions(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/behavior-trees/{tree_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{tree_id}")
async def get_tree(tree_id: str):
    """Return a single tree (custom if exists, else default)."""
    # Check custom first
    if _db is not None:
        try:
            doc = await _db[COLLECTION].find_one({"id": tree_id})
            if doc:
                return _strip_mongo(doc)
        except Exception as exc:
            logger.warning("DB lookup failed for tree %s: %s", tree_id, exc)

    # Fall back to default
    default = DEFAULT_TREES.get(tree_id)
    if default:
        return default

    raise HTTPException(status_code=404, detail=f"Behavior tree '{tree_id}' not found.")


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/behavior-trees/{tree_id}  — upsert
# ─────────────────────────────────────────────────────────────────────────────

@router.put("/{tree_id}")
async def upsert_tree(tree_id: str, body: Dict[str, Any] = Body(...)):
    """
    Create or replace a custom tree.
    Body should contain: id, name, description, node.
    """
    body["id"] = tree_id
    body["updated_at"] = datetime.utcnow().isoformat()

    # Validate minimal structure
    if "node" not in body:
        raise HTTPException(status_code=400, detail="Tree body must contain a 'node' field.")

    if _db is None:
        # No DB: return the tree as-is
        logger.warning("No database configured — tree not persisted.")
        return {"success": True, "tree": body, "persisted": False}

    try:
        await _db[COLLECTION].replace_one(
            {"id": tree_id},
            body,
            upsert=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    return {"success": True, "tree": body, "persisted": True}


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/behavior-trees  — create new
# ─────────────────────────────────────────────────────────────────────────────

@router.post("")
async def create_tree(body: Dict[str, Any] = Body(...)):
    """
    Create a new custom behavior tree.
    Body must contain: id, name, node. Description is optional.
    """
    tree_id = body.get("id")
    if not tree_id:
        raise HTTPException(status_code=400, detail="'id' field is required.")
    if "node" not in body:
        raise HTTPException(status_code=400, detail="'node' field is required.")

    body["updated_at"] = datetime.utcnow().isoformat()

    if _db is None:
        logger.warning("No database configured — tree not persisted.")
        return {"success": True, "tree": body, "persisted": False}

    # Check for duplicate
    try:
        existing = await _db[COLLECTION].find_one({"id": tree_id})
        if existing:
            raise HTTPException(
                status_code=409, detail=f"Tree '{tree_id}' already exists. Use PUT to update."
            )
        await _db[COLLECTION].insert_one(body)
        body.pop("_id", None)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    return {"success": True, "tree": body, "persisted": True}


# ─────────────────────────────────────────────────────────────────────────────
# DELETE /api/behavior-trees/{tree_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/{tree_id}")
async def delete_tree(tree_id: str):
    """
    Delete the custom tree. If a default exists with this id, it is restored.
    """
    if _db is None:
        return {"success": True, "message": "No database — nothing to delete."}

    try:
        result = await _db[COLLECTION].delete_one({"id": tree_id})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    has_default = tree_id in DEFAULT_TREES
    if result.deleted_count == 0 and not has_default:
        raise HTTPException(status_code=404, detail=f"Tree '{tree_id}' not found.")

    msg = f"Custom tree '{tree_id}' deleted."
    if has_default:
        msg += " Default tree restored."

    return {"success": True, "message": msg, "restored_default": has_default}


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/behavior-trees/{tree_id}/simulate  — quick 3-round simulation
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{tree_id}/simulate")
async def simulate_tree(tree_id: str, body: Dict[str, Any] = Body(default={})):
    """
    Run a 3-round simulation against a test enemy/player to preview the tree.

    Optional body fields:
      - enemy_hp_pct: float (0-1), default 1.0
      - player_hp: int, default 30
    """
    # Load tree
    custom_tree = None
    if _db is not None:
        try:
            doc = await _db[COLLECTION].find_one({"id": tree_id})
            if doc:
                custom_tree = _strip_mongo(doc)
        except Exception:
            pass

    tree = custom_tree or DEFAULT_TREES.get(tree_id)
    if tree is None:
        raise HTTPException(status_code=404, detail=f"Tree '{tree_id}' not found.")

    node = tree.get("node")
    if not node:
        raise HTTPException(status_code=400, detail="Tree has no 'node' field.")

    # Build test combatants
    enemy_hp_pct = float(body.get("enemy_hp_pct", 1.0))
    player_hp = int(body.get("player_hp", 30))

    test_enemy = {
        "id": "test_enemy",
        "name": tree.get("name", "Test Enemy"),
        "hp": int(50 * enemy_hp_pct),
        "max_hp": 50,
        "ac": 14,
        "attack_bonus": 5,
        "damage_die": "1d8+3",
        "damage_type": "slashing",
        "type": "humanoid",
        "special_abilities": [],
        "ability_charges": {"breath_weapon": 1},
        "grid_x": 5, "grid_y": 2,
        "took_fire_damage_last_turn": False,
        "took_acid_damage_last_turn": False,
    }
    test_player = {
        "hp": player_hp,
        "max_hp": 40,
        "ac": 14,
        "conditions": [],
    }

    rounds = []
    for round_num in range(1, 4):
        combat_ctx = {
            "round": round_num,
            "alive_enemies": [test_enemy],
            "player_grid_x": 4,
            "player_grid_y": 2,
        }
        action = run_tree(node, test_enemy, test_player, combat_ctx)
        rounds.append({
            "round": round_num,
            "action_type": action.get("action_type"),
            "damage_die": action.get("damage_die"),
            "damage_type": action.get("damage_type"),
            "advantage": action.get("advantage"),
            "narration_hint": action.get("narration_hint"),
            "abilities_used": action.get("abilities_used"),
        })
        # Simulate HP loss to test transitions
        if action.get("action_type") == "attack":
            test_enemy["hp"] = max(1, test_enemy["hp"] - 5)

    return {
        "tree_id": tree_id,
        "tree_name": tree.get("name"),
        "rounds": rounds,
    }
