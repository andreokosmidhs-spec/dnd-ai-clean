"""
Spell component enforcement service.

Two tiers:
  1. Costly material components — specific valuable items that must be in
     inventory and are consumed (or held) on cast.
  2. Non-costly material components — covered by a component pouch or any
     spellcasting focus; block cast only when the character has neither.
  3. V / S components — not enforced here; handled via conditions (Silence,
     Restrained, etc.) in the narrative layer.
"""
from __future__ import annotations
import re
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Costly material components: spell → requirements
# consumed=True  means the item is destroyed on cast
# consumed=False means it must be present but survives (e.g. a scrying focus)
# ---------------------------------------------------------------------------
COSTLY_COMPONENTS: Dict[str, Dict] = {
    "Nondetection":  {
        "label": "diamond dust (25+ gp)",
        "keywords": ["diamond dust", "diamond"],
        "min_gp": 25,
        "consumed": True,
    },
    "Revivify":  {
        "label": "diamond (300+ gp)",
        "keywords": ["diamond"],
        "min_gp": 300,
        "consumed": True,
    },
    "Raise Dead":  {
        "label": "diamond (500+ gp)",
        "keywords": ["diamond"],
        "min_gp": 500,
        "consumed": True,
    },
    "Scrying":  {
        "label": "scrying focus (1,000+ gp)",
        "keywords": ["mirror", "crystal ball", "font", "ruby"],
        "min_gp": 1000,
        "consumed": False,
    },
    "Awaken":  {
        "label": "agate (1,000+ gp)",
        "keywords": ["agate"],
        "min_gp": 1000,
        "consumed": True,
    },
}

# Items that serve as a spellcasting focus or component pouch —
# any one of these covers all non-costly M components.
_FOCUS_KEYWORDS = [
    "component pouch",
    "arcane focus",
    "druidic focus",
    "holy symbol",
    "orb", "crystal", "staff", "wand", "rod",
    "amulet", "totem",
    "lute", "lyre", "flute",  # bard instruments double as foci
]


def _item_name(item: Dict) -> str:
    return str(item.get("name") or item.get("title") or "").lower()


def _item_value(item: Dict) -> float:
    """Return the item's gp value, trying multiple encodings."""
    # Explicit numeric field
    v = item.get("value") or item.get("gp") or item.get("gold")
    if v is not None:
        try:
            return float(v)
        except (TypeError, ValueError):
            pass
    # Parse from name, e.g. "Diamond (500 gp)" or "300gp diamond"
    name = _item_name(item)
    m = re.search(r"(\d[\d,]*)\s*gp", name)
    if m:
        return float(m.group(1).replace(",", ""))
    return 0.0


def has_focus_or_pouch(inventory: List[Dict]) -> bool:
    """Return True if the inventory contains a component pouch or spellcasting focus."""
    for item in inventory:
        name = _item_name(item)
        if any(kw in name for kw in _FOCUS_KEYWORDS):
            return True
    return False


def _find_component_item(
    inventory: List[Dict],
    keywords: List[str],
    min_gp: float,
) -> Optional[int]:
    """Return the index of the first inventory item that matches the component
    keywords and meets the minimum gp threshold, or None if not found."""
    for idx, item in enumerate(inventory):
        name = _item_name(item)
        if not any(kw in name for kw in keywords):
            continue
        if min_gp > 0 and _item_value(item) < min_gp:
            continue
        return idx
    return None


def _consume_item(inventory: List[Dict], idx: int) -> List[Dict]:
    """Remove one quantity of the item at idx; drop the entry if qty reaches 0."""
    item = dict(inventory[idx])
    qty = int(item.get("quantity") or item.get("qty") or 1)
    if qty <= 1:
        return inventory[:idx] + inventory[idx + 1:]
    item["quantity"] = qty - 1
    return inventory[:idx] + [item] + inventory[idx + 1:]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_costly_component(
    spell_name: str,
    inventory: List[Dict],
) -> Tuple[bool, Optional[str], Optional[int]]:
    """Check whether a costly material component is available.

    Returns (ok, error_message, item_index).
      ok=True  → cast allowed; item_index is set iff the item will be consumed.
      ok=False → cast blocked; error_message explains why.
    """
    req = COSTLY_COMPONENTS.get(spell_name)
    if req is None:
        return True, None, None  # no costly component

    idx = _find_component_item(inventory, req["keywords"], req["min_gp"])
    if idx is None:
        return (
            False,
            f"You need {req['label']} to cast {spell_name}, but you don't have it in your inventory.",
            None,
        )
    # Found — return index only if we'll consume it
    return True, None, (idx if req["consumed"] else None)


def check_noncostly_component(
    spell_name: str,
    card_components: Dict,
    inventory: List[Dict],
) -> Tuple[bool, Optional[str]]:
    """Warn (but don't block) if a non-costly M component needs a focus/pouch
    and the character has neither.

    Returns (ok, warning_message). ok is always True — this is advisory only.
    """
    m_comp = card_components.get("M")
    if not m_comp:
        return True, None  # no material component

    # Already handled as costly — skip
    if spell_name in COSTLY_COMPONENTS:
        return True, None

    if not has_focus_or_pouch(inventory):
        return (
            True,
            f"⚠ {spell_name} needs a material component — you have no component pouch or spellcasting focus. The DM may rule you cannot cast it.",
        )
    return True, None


def consume_component_if_needed(
    spell_name: str,
    inventory: List[Dict],
    item_idx: Optional[int],
) -> List[Dict]:
    """Remove the consumed component from inventory. Returns the updated list."""
    if item_idx is None:
        return inventory
    req = COSTLY_COMPONENTS.get(spell_name)
    if req and req["consumed"]:
        return _consume_item(inventory, item_idx)
    return inventory
