"""Ration and water supply tracking.

Looks for ration/food/water items in the character's game-state inventory
and consumes one unit when the character eats or drinks.

Item names matched (case-insensitive): "ration", "trail ration", "iron ration",
"food", "waterskin", "water flask", "canteen", "water".
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

_RATION_RE = re.compile(
    r"\b(rations?|trail\s+rations?|iron\s+rations?|emergency\s+rations?|hardtack|jerky|"
    r"dried\s+food|provisions?)\b",
    re.IGNORECASE,
)

_WATER_RE = re.compile(
    r"\b(water|waterskin|water\s+flask|canteen|jug\s+of\s+water|fresh\s+water)\b",
    re.IGNORECASE,
)


def _find_item(inventory: List[Dict], pattern: re.Pattern) -> Optional[Tuple[int, Dict]]:
    """Return (index, item) for the first inventory item whose name matches pattern."""
    for i, item in enumerate(inventory):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        if pattern.search(name):
            return i, item
    return None


def _deduct_one(inventory: List[Dict], idx: int) -> List[Dict]:
    """Reduce quantity of item at idx by 1; remove if qty reaches 0."""
    item = dict(inventory[idx])
    qty = int(item.get("quantity") or item.get("qty") or 1)
    if qty <= 1:
        return inventory[:idx] + inventory[idx + 1:]
    item["quantity"] = qty - 1
    return inventory[:idx] + [item] + inventory[idx + 1:]


def ration_count(inventory: List[Dict]) -> int:
    """Return total ration units in inventory."""
    total = 0
    for item in inventory:
        if not isinstance(item, dict):
            continue
        if _RATION_RE.search(str(item.get("name") or "")):
            total += int(item.get("quantity") or item.get("qty") or 1)
    return total


def water_count(inventory: List[Dict]) -> int:
    """Return total water units in inventory."""
    total = 0
    for item in inventory:
        if not isinstance(item, dict):
            continue
        if _WATER_RE.search(str(item.get("name") or "")):
            total += int(item.get("quantity") or item.get("qty") or 1)
    return total


def consume_ration(inventory: List[Dict]) -> Tuple[List[Dict], bool]:
    """Consume one ration. Returns (updated_inventory, consumed_bool)."""
    hit = _find_item(inventory, _RATION_RE)
    if hit is None:
        return inventory, False
    idx, _ = hit
    return _deduct_one(inventory, idx), True


def consume_water(inventory: List[Dict]) -> Tuple[List[Dict], bool]:
    """Consume one water unit. Returns (updated_inventory, consumed_bool)."""
    hit = _find_item(inventory, _WATER_RE)
    if hit is None:
        return inventory, False
    idx, _ = hit
    return _deduct_one(inventory, idx), True


def consume_ration_from_state(char_state: Dict) -> Tuple[List[Dict], bool]:
    """Convenience wrapper that reads and writes inventory on char_state dict."""
    inv = list(char_state.get("inventory") or [])
    new_inv, consumed = consume_ration(inv)
    return new_inv, consumed


def consume_water_from_state(char_state: Dict) -> Tuple[List[Dict], bool]:
    """Convenience wrapper that reads and writes inventory on char_state dict."""
    inv = list(char_state.get("inventory") or [])
    new_inv, consumed = consume_water(inv)
    return new_inv, consumed


def ration_status(char_state: Dict) -> Dict:
    """Return a summary of food and water supplies."""
    inv = char_state.get("inventory") or []
    return {
        "rations": ration_count(inv),
        "water_units": water_count(inv),
        "has_food": ration_count(inv) > 0,
        "has_water": water_count(inv) > 0,
    }
