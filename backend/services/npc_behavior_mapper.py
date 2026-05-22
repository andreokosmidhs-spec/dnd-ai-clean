"""
NPC Behavior Mapper — maps NPC character card data to a behavior tree.

Pure rule-based keyword matching against personality_tags and role.
Zero LLM calls. Called once when an NPC is converted to a combat enemy.
"""
from __future__ import annotations
import copy
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# ── Role → base tree id ───────────────────────────────────────────────────────

ROLE_TREE_MAP: Dict[str, str] = {
    # Fighters
    "guard":          "orc",
    "guard_captain":  "orc",
    "soldier":        "orc",
    "warrior":        "orc_berserker",
    "knight":         "generic_brute",
    "mercenary":      "orc",
    "fighter":        "orc",
    "gladiator":      "orc_berserker",
    "berserker":      "orc_berserker",
    # Stealthy
    "assassin":       "assassin",
    "rogue":          "assassin",
    "thief":          "assassin",
    "spy":            "assassin",
    "scout":          "goblin",
    "ranger":         "assassin",
    # Casters
    "mage":           "cult_fanatic",
    "wizard":         "cult_fanatic",
    "sorcerer":       "cult_fanatic",
    "warlock":        "cult_fanatic",
    "cleric":         "cult_fanatic",
    "priest":         "cult_fanatic",
    "shaman":         "cult_fanatic",
    "cultist":        "cult_fanatic",
    "witch":          "cult_fanatic",
    "druid":          "cult_fanatic",
    # Brutes
    "blacksmith":     "generic_brute",
    "thug":           "generic_brute",
    "enforcer":       "generic_brute",
    "bouncer":        "generic_brute",
    # Skirmishers / civilians (flee-prone)
    "bandit":         "goblin",
    "criminal":       "goblin",
    "smuggler":       "goblin",
    "merchant":       "goblin",
    "innkeeper":      "goblin",
    "traveler":       "goblin",
    "mayor":          "goblin",
    "noble":          "goblin",
    "scholar":        "goblin",
    "advisor":        "goblin",
    "farmer":         "goblin",
}

# ── Personality tag → flee HP threshold ──────────────────────────────────────
# Higher = cowards flee earlier; None = never flee

FLEE_THRESHOLDS: List[tuple] = [
    # (keywords,                       threshold)
    (["never_retreats", "fearless", "undead", "construct", "golem", "fanatical", "zealous"],   None),
    (["brave", "bold", "proud", "stoic", "duty", "honor", "vengeful"],                        0.10),
    (["loyal", "disciplined", "protective", "haunted", "guilt_ridden"],                       0.15),
    (["gruff", "aggressive", "hostile", "violent", "wrathful", "stubborn"],                   0.20),
    # default (cautious / neutral)
    (["cautious", "prudent", "methodical", "overworked", "tired"],                            0.30),
    (["nervous", "paranoid", "secretive", "scheming", "corrupt", "easily_bribed"],            0.40),
    (["cowardly", "fearful", "timid", "desperate", "weak", "soft_spoken"],                    0.50),
]

# ── Personality tag → attack modifiers ──────────────────────────────────────

# Tags that grant reckless_attack (advantage both ways)
RECKLESS_TAGS = {"reckless", "berserk", "frenzied", "rage", "savage", "unhinged", "wrathful", "frenzied"}
# Tags that give advantage on first strike (ambush instinct)
AMBUSH_TAGS   = {"cunning", "scheming", "paranoid", "stealthy", "deceptive", "calculating", "cold"}
# Tags that cause hesitation (disadvantage first attack)
HESITANT_TAGS = {"morally_conflicted", "soft_spoken", "reluctant", "merciful", "uncertain"}


def _all_text(npc: Dict[str, Any]) -> str:
    """Collapse all string fields into one lowercase blob for keyword scanning."""
    parts = [
        npc.get("role", ""),
        npc.get("occupation", ""),
        npc.get("description", ""),
        npc.get("personality", ""),
        " ".join(npc.get("personality_tags", [])),
        " ".join(t if isinstance(t, str) else t.get("trait", "") for t in npc.get("traits", [])),
    ]
    return " ".join(parts).lower()


def _pick_flee_threshold(tags: List[str], full_text: str) -> Optional[float]:
    """Return flee HP threshold (0-1) or None if this enemy never flees."""
    tag_set = {t.lower().replace("-", "_") for t in tags}
    # Also scan free-text for single-word signals
    for keywords, threshold in FLEE_THRESHOLDS:
        if any(kw in tag_set or kw in full_text for kw in keywords):
            return threshold
    return 0.25  # default


def _base_tree_id(npc: Dict[str, Any]) -> str:
    """Map NPC role to the closest base behavior tree."""
    role = npc.get("role", npc.get("occupation", "")).lower().strip()
    # Try exact match first, then partial
    if role in ROLE_TREE_MAP:
        return ROLE_TREE_MAP[role]
    for key, tree_id in ROLE_TREE_MAP.items():
        if key in role or role in key:
            return tree_id
    return "generic_brute"


def _patch_flee_threshold(node: Dict[str, Any], threshold: Optional[float]) -> Dict[str, Any]:
    """
    Walk the tree and update any hp_below condition used in a flee sequence.
    If threshold is None, remove flee sequences entirely.
    """
    node = copy.deepcopy(node)

    def _walk(n: Dict) -> Optional[Dict]:
        if n.get("type") == "sequence":
            children = n.get("children", [])
            # Detect flee sequence: has a condition(hp_below) AND an action(flee)
            has_hp_cond = any(c.get("type") == "condition" and c.get("check") == "hp_below" for c in children)
            has_flee    = any(c.get("type") == "action"    and c.get("action") == "flee"    for c in children)
            if has_hp_cond and has_flee:
                if threshold is None:
                    return None  # remove this branch
                # Patch the threshold
                for c in children:
                    if c.get("type") == "condition" and c.get("check") == "hp_below":
                        c["value"] = threshold
            # Recurse into remaining children
            n["children"] = [_walk(c) for c in n.get("children", [])]
            n["children"] = [c for c in n["children"] if c is not None]
        elif n.get("type") in ("selector",):
            n["children"] = [_walk(c) for c in n.get("children", [])]
            n["children"] = [c for c in n["children"] if c is not None]
        elif n.get("type") == "not":
            child = _walk(n.get("child", {}))
            if child is None:
                return None
            n["child"] = child
        return n

    return _walk(node) or node


def _inject_reckless(node: Dict[str, Any], damage_die: str) -> Dict[str, Any]:
    """Prepend a reckless_attack option before the first melee attack in a selector."""
    if node.get("type") != "selector":
        return node
    reckless_node = {
        "type": "action",
        "action": "reckless_attack",
        "label": "Reckless Attack",
        "damage_die": damage_die,
        "adv_reason": "Reckless",
    }
    children = node.get("children", [])
    # Insert after any flee branch, before the first attack
    insert_at = 0
    for i, c in enumerate(children):
        is_flee = (c.get("type") == "sequence" and
                   any(x.get("action") == "flee" for x in c.get("children", [])))
        if is_flee:
            insert_at = i + 1
    children.insert(insert_at, reckless_node)
    node["children"] = children
    return node


def _inject_hesitation(node: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap the whole tree in a first-round hesitation branch."""
    hesitate = {
        "type": "sequence",
        "label": "Hesitate (first round)",
        "children": [
            {"type": "condition", "check": "is_first_round"},
            {"type": "action", "action": "defend", "label": "Hesitate"},
        ]
    }
    return {
        "type": "selector",
        "children": [hesitate, node]
    }


def get_behavior_tree_for_npc(npc_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Given an NPC character card, return a behavior tree dict tailored to
    their personality and role. Pure rule-based — no LLM calls.

    Returns a full tree dict {id, name, description, node} ready to embed
    in the enemy's combat state.
    """
    from data.behavior_trees import DEFAULT_TREES, get_tree

    tags: List[str] = npc_data.get("personality_tags", [])
    tag_set = {t.lower().replace("-", "_") for t in tags}
    full_text = _all_text(npc_data)

    # 1. Pick base tree from role — check faction_role first (set by assign_faction_roles)
    faction_role = npc_data.get("faction_role", "solo")
    if faction_role == "leader":
        tree_id = "guard_leader"
    elif faction_role == "bodyguard":
        tree_id = "bodyguard"
    elif faction_role == "follower":
        tree_id = "loyal_follower"
    else:
        tree_id = _base_tree_id(npc_data)

    base = get_tree(tree_id)
    if not base:
        base = DEFAULT_TREES.get("generic_brute", {})

    npc_name = npc_data.get("name", "NPC")
    logger.info(f"🎭 NPC behavior: {npc_name} → base_tree={tree_id}, tags={tags}")

    # Deep copy so we don't mutate the default
    tree = copy.deepcopy(base)
    node = tree.get("node", {})
    damage_die = npc_data.get("damage_die", "1d6")

    # 2. Adjust flee threshold
    threshold = _pick_flee_threshold(tags, full_text)
    node = _patch_flee_threshold(node, threshold)
    logger.info(f"🎭 {npc_name} flee threshold: {threshold}")

    # 3. Reckless attack for hot-headed personalities
    if tag_set & RECKLESS_TAGS or any(kw in full_text for kw in RECKLESS_TAGS):
        node = _inject_reckless(node, damage_die)
        logger.info(f"🎭 {npc_name} → injected reckless_attack")

    # 4. First-round hesitation for conflicted characters
    if tag_set & HESITANT_TAGS or any(kw in full_text for kw in HESITANT_TAGS):
        node = _inject_hesitation(node)
        logger.info(f"🎭 {npc_name} → injected first-round hesitation")

    return {
        "id": f"npc_{npc_data.get('id', npc_name.lower().replace(' ', '_'))}",
        "name": f"{npc_name} (NPC)",
        "description": (
            f"Auto-generated from character card. "
            f"Role: {npc_data.get('role', '?')}. Tags: {', '.join(tags) or 'none'}."
        ),
        "node": node,
        "_source_tree": tree_id,
        "_flee_threshold": threshold,
    }
