"""
Equipment loadout service.

Equipment state lives in character_state["equipment"]:
    {
        "main_hand": str | None,   # item name
        "off_hand":  str | None,   # item name (shield, weapon, focus, or None)
        "armor":     str | None,   # item name
        "two_handed": bool,        # True when using 2H weapon OR versatile 2H grip
    }

A "free hand" exists when two_handed=False AND off_hand is None.
War Caster feat overrides the free-hand requirement for somatic components.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any

# ---------------------------------------------------------------------------
# Weapon catalog
# hands: "one" | "two" | "versatile"
# category: "melee" | "ranged" | "thrown"
# properties: finesse, light, heavy, thrown, loading, reach
# damage / damage_2h only on versatile
# ---------------------------------------------------------------------------
WEAPON_PROPERTIES: Dict[str, Dict] = {
    # ── Simple Melee ───────────────────────────────────────────────────────
    "Club":          {"hands": "one",       "damage": "1d4",  "type": "bludgeoning", "properties": ["light"]},
    "Dagger":        {"hands": "one",       "damage": "1d4",  "type": "piercing",    "properties": ["finesse", "light", "thrown"]},
    "Dagger (2)":    {"hands": "one",       "damage": "1d4",  "type": "piercing",    "properties": ["finesse", "light", "thrown"]},
    "Greatclub":     {"hands": "two",       "damage": "1d8",  "type": "bludgeoning", "properties": []},
    "Handaxe":       {"hands": "one",       "damage": "1d6",  "type": "slashing",    "properties": ["light", "thrown"]},
    "Handaxe (2)":   {"hands": "one",       "damage": "1d6",  "type": "slashing",    "properties": ["light", "thrown"]},
    "Javelin":       {"hands": "one",       "damage": "1d6",  "type": "piercing",    "properties": ["thrown"]},
    "Javelin (4)":   {"hands": "one",       "damage": "1d6",  "type": "piercing",    "properties": ["thrown"]},
    "Javelin (5)":   {"hands": "one",       "damage": "1d6",  "type": "piercing",    "properties": ["thrown"]},
    "Mace":          {"hands": "one",       "damage": "1d6",  "type": "bludgeoning", "properties": []},
    "Quarterstaff":  {"hands": "versatile", "damage": "1d6",  "damage_2h": "1d8",    "type": "bludgeoning", "properties": []},
    "Sickle":        {"hands": "one",       "damage": "1d4",  "type": "slashing",    "properties": ["light"]},
    "Spear":         {"hands": "versatile", "damage": "1d6",  "damage_2h": "1d8",    "type": "piercing",    "properties": ["thrown"]},
    "Dart":          {"hands": "one",       "damage": "1d4",  "type": "piercing",    "properties": ["finesse", "thrown"]},
    "Dart (10)":     {"hands": "one",       "damage": "1d4",  "type": "piercing",    "properties": ["finesse", "thrown"]},
    # ── Martial Melee ──────────────────────────────────────────────────────
    "Battleaxe":     {"hands": "versatile", "damage": "1d8",  "damage_2h": "1d10",   "type": "slashing",    "properties": []},
    "Flail":         {"hands": "one",       "damage": "1d8",  "type": "bludgeoning", "properties": []},
    "Glaive":        {"hands": "two",       "damage": "1d10", "type": "slashing",    "properties": ["heavy", "reach"]},
    "Greataxe":      {"hands": "two",       "damage": "1d12", "type": "slashing",    "properties": ["heavy"]},
    "Greatsword":    {"hands": "two",       "damage": "2d6",  "type": "slashing",    "properties": ["heavy"]},
    "Halberd":       {"hands": "two",       "damage": "1d10", "type": "slashing",    "properties": ["heavy", "reach"]},
    "Longsword":     {"hands": "versatile", "damage": "1d8",  "damage_2h": "1d10",   "type": "slashing",    "properties": []},
    "Maul":          {"hands": "two",       "damage": "2d6",  "type": "bludgeoning", "properties": ["heavy"]},
    "Morningstar":   {"hands": "one",       "damage": "1d8",  "type": "piercing",    "properties": []},
    "Pike":          {"hands": "two",       "damage": "1d10", "type": "piercing",    "properties": ["heavy", "reach"]},
    "Rapier":        {"hands": "one",       "damage": "1d8",  "type": "piercing",    "properties": ["finesse"]},
    "Scimitar":      {"hands": "one",       "damage": "1d6",  "type": "slashing",    "properties": ["finesse", "light"]},
    "Shortsword":    {"hands": "one",       "damage": "1d6",  "type": "piercing",    "properties": ["finesse", "light"]},
    "Two Shortswords":{"hands": "one",      "damage": "1d6",  "type": "piercing",    "properties": ["finesse", "light"]},
    "Trident":       {"hands": "versatile", "damage": "1d6",  "damage_2h": "1d8",    "type": "piercing",    "properties": ["thrown"]},
    "War Pick":      {"hands": "one",       "damage": "1d8",  "type": "piercing",    "properties": []},
    "Warhammer":     {"hands": "versatile", "damage": "1d8",  "damage_2h": "1d10",   "type": "bludgeoning", "properties": []},
    # ── Ranged ─────────────────────────────────────────────────────────────
    "Hand Crossbow": {"hands": "one",       "damage": "1d6",  "type": "piercing",    "category": "ranged",  "properties": ["light", "loading"]},
    "Heavy Crossbow":{"hands": "two",       "damage": "1d10", "type": "piercing",    "category": "ranged",  "properties": ["heavy", "loading"]},
    "Light Crossbow":{"hands": "two",       "damage": "1d8",  "type": "piercing",    "category": "ranged",  "properties": ["loading"]},
    "Longbow":       {"hands": "two",       "damage": "1d8",  "type": "piercing",    "category": "ranged",  "properties": ["heavy"]},
    "Shortbow":      {"hands": "two",       "damage": "1d6",  "type": "piercing",    "category": "ranged",  "properties": []},
}

# Items that can go in the off-hand but are NOT weapons
OFFHAND_ITEMS = {
    "Shield":         {"ac_bonus": 2, "category": "shield"},
    "Wooden Shield":  {"ac_bonus": 2, "category": "shield"},
    "Druidic Focus":  {"ac_bonus": 0, "category": "focus"},
    "Holy Symbol":    {"ac_bonus": 0, "category": "focus"},
    "Component Pouch":{"ac_bonus": 0, "category": "focus"},
    # Musical instruments double as bard foci
    "Lute":           {"ac_bonus": 0, "category": "focus"},
    "Lyre":           {"ac_bonus": 0, "category": "focus"},
    "Flute":          {"ac_bonus": 0, "category": "focus"},
}

# A spellcasting focus in off-hand counts as a free hand for somatic components
CASTING_FOCUSES = {"focus", "instrument"}

# ---------------------------------------------------------------------------
# Armor catalog
# type: "light" | "medium" | "heavy" | "none"
# max_dex: None = unlimited, 0 = no dex bonus, 2 = medium cap
# ---------------------------------------------------------------------------
ARMOR_PROPERTIES: Dict[str, Dict] = {
    # Light
    "Padded Armor":   {"ac_base": 11, "type": "light",  "max_dex": None, "stealth_disadv": True,  "str_req": 0},
    "Leather Armor":  {"ac_base": 11, "type": "light",  "max_dex": None, "stealth_disadv": False, "str_req": 0},
    "Studded Leather":{"ac_base": 12, "type": "light",  "max_dex": None, "stealth_disadv": False, "str_req": 0},
    # Medium
    "Hide Armor":     {"ac_base": 12, "type": "medium", "max_dex": 2,    "stealth_disadv": False, "str_req": 0},
    "Chain Shirt":    {"ac_base": 13, "type": "medium", "max_dex": 2,    "stealth_disadv": False, "str_req": 0},
    "Scale Mail":     {"ac_base": 14, "type": "medium", "max_dex": 2,    "stealth_disadv": True,  "str_req": 0},
    "Breastplate":    {"ac_base": 14, "type": "medium", "max_dex": 2,    "stealth_disadv": False, "str_req": 0},
    "Half Plate":     {"ac_base": 15, "type": "medium", "max_dex": 2,    "stealth_disadv": True,  "str_req": 0},
    # Heavy
    "Ring Mail":      {"ac_base": 14, "type": "heavy",  "max_dex": 0,    "stealth_disadv": True,  "str_req": 0},
    "Chain Mail":     {"ac_base": 16, "type": "heavy",  "max_dex": 0,    "stealth_disadv": True,  "str_req": 13},
    "Splint Armor":   {"ac_base": 17, "type": "heavy",  "max_dex": 0,    "stealth_disadv": True,  "str_req": 15},
    "Plate Armor":    {"ac_base": 18, "type": "heavy",  "max_dex": 0,    "stealth_disadv": True,  "str_req": 15},
}


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _stat_mod(score: int) -> int:
    return (score - 10) // 2


def _dex_mod(character_state: Dict) -> int:
    stats = character_state.get("stats") or character_state.get("abilities") or {}
    dex = stats.get("dexterity") or stats.get("dex") or 10
    return _stat_mod(int(dex))


def _str_mod(character_state: Dict) -> int:
    stats = character_state.get("stats") or character_state.get("abilities") or {}
    str_ = stats.get("strength") or stats.get("str") or 10
    return _stat_mod(int(str_))


def _con_mod(character_state: Dict) -> int:
    stats = character_state.get("stats") or character_state.get("abilities") or {}
    con = stats.get("constitution") or stats.get("con") or 10
    return _stat_mod(int(con))


def _wis_mod(character_state: Dict) -> int:
    stats = character_state.get("stats") or character_state.get("abilities") or {}
    wis = stats.get("wisdom") or stats.get("wis") or 10
    return _stat_mod(int(wis))


def get_equipment(character_state: Dict) -> Dict:
    """Return the equipment dict, creating a default if missing."""
    return character_state.get("equipment") or {
        "main_hand": None,
        "off_hand": None,
        "armor": None,
        "two_handed": False,
    }


def has_free_hand(character_state: Dict) -> bool:
    """True if at least one hand is unoccupied for spellcasting / item use."""
    eq = get_equipment(character_state)
    if eq.get("two_handed"):
        return False
    if eq.get("off_hand"):
        return False
    return True


def has_spellcasting_hand(character_state: Dict) -> bool:
    """True if the character can cast somatic components — either they have a
    free hand, or their off-hand holds a spellcasting focus (War Caster also
    counts but is checked separately via the card deck)."""
    if has_free_hand(character_state):
        return True
    eq = get_equipment(character_state)
    off = eq.get("off_hand") or ""
    offhand_info = OFFHAND_ITEMS.get(off, {})
    return offhand_info.get("category") in CASTING_FOCUSES


def compute_ac(character_state: Dict) -> int:
    """Compute AC from equipped armor, off-hand shield, and class features."""
    eq = get_equipment(character_state)
    armor_name = eq.get("armor") or ""
    off_name   = eq.get("off_hand") or ""
    dex = _dex_mod(character_state)
    cls_key = _class_key(character_state)

    shield_bonus = OFFHAND_ITEMS.get(off_name, {}).get("ac_bonus", 0)

    if armor_name in ARMOR_PROPERTIES:
        a = ARMOR_PROPERTIES[armor_name]
        max_dex = a["max_dex"]
        dex_contrib = dex if max_dex is None else min(dex, max_dex)
        return a["ac_base"] + dex_contrib + shield_bonus

    # Unarmored — check class features
    if cls_key == "Barbarian":
        con = _con_mod(character_state)
        return 10 + dex + con + shield_bonus
    if cls_key == "Monk":
        wis = _wis_mod(character_state)
        return 10 + dex + wis  # monks can't use shields
    # Sorcerer origin (Draconic): 13 + DEX if no armor — left as default for now
    return 10 + dex + shield_bonus


def _class_key(character_state: Dict) -> str:
    cls = character_state.get("class_") or character_state.get("class") or {}
    if isinstance(cls, dict):
        return (cls.get("key") or cls.get("name") or "").strip().title()
    return str(cls).strip().title()


# ---------------------------------------------------------------------------
# Equip / unequip
# ---------------------------------------------------------------------------

def _normalize_item_name(name: str) -> str:
    """Strip trailing quantity annotations like '(2)' or '(20)'."""
    import re
    return re.sub(r"\s*\(\d+\)$", "", name.strip())


def equip_item(
    character_state: Dict,
    slot: str,          # "main_hand" | "off_hand" | "armor"
    item_name: Optional[str],
    two_handed: bool = False,
) -> Tuple[Dict, Optional[str]]:
    """Return (updated_character_state, error_message).
    Pass item_name=None to unequip the slot."""
    eq = dict(get_equipment(character_state))
    inv: List[Dict] = list(character_state.get("inventory") or [])

    if item_name is None:
        # Unequip
        prev = eq.get(slot)
        eq[slot] = None
        if slot == "main_hand":
            eq["two_handed"] = False
        # Mark unequipped in inventory
        for item in inv:
            if _normalize_item_name(item.get("name", "")) == _normalize_item_name(prev or ""):
                if item.get("slot") == slot:
                    item.pop("equipped", None)
                    item.pop("slot", None)
                    break
        updated = {**character_state, "equipment": eq, "inventory": inv}
        return updated, None

    norm = _normalize_item_name(item_name)

    if slot == "armor":
        if norm not in ARMOR_PROPERTIES:
            return character_state, f"'{item_name}' is not a known armor type."
        # Remove old armor equipped flag
        for item in inv:
            if item.get("slot") == "armor":
                item.pop("equipped", None); item.pop("slot", None)
        eq["armor"] = norm
        for item in inv:
            if _normalize_item_name(item.get("name", "")) == norm:
                item["equipped"] = True; item["slot"] = "armor"; break

    elif slot == "main_hand":
        wpn = WEAPON_PROPERTIES.get(norm) or WEAPON_PROPERTIES.get(item_name)
        if wpn is None:
            return character_state, f"'{item_name}' is not a known weapon."
        hands = wpn["hands"]
        use_two = two_handed or hands == "two"
        if use_two:
            eq["off_hand"] = None  # 2H clears off-hand
        eq["two_handed"] = use_two
        # Clear previous main_hand equipped flag
        for item in inv:
            if item.get("slot") == "main_hand":
                item.pop("equipped", None); item.pop("slot", None)
        eq["main_hand"] = item_name
        for item in inv:
            if _normalize_item_name(item.get("name", "")) == norm:
                item["equipped"] = True; item["slot"] = "main_hand"; break

    elif slot == "off_hand":
        if eq.get("two_handed"):
            return character_state, "Can't equip an off-hand item while wielding a two-handed weapon."
        if norm not in OFFHAND_ITEMS and norm not in WEAPON_PROPERTIES:
            return character_state, f"'{item_name}' can't be equipped in the off-hand."
        # Clear previous off_hand equipped flag
        for item in inv:
            if item.get("slot") == "off_hand":
                item.pop("equipped", None); item.pop("slot", None)
        eq["off_hand"] = item_name
        for item in inv:
            if _normalize_item_name(item.get("name", "")) == norm:
                item["equipped"] = True; item["slot"] = "off_hand"; break

    else:
        return character_state, f"Unknown slot '{slot}'."

    updated = {**character_state, "equipment": eq, "inventory": inv}
    return updated, None


# ---------------------------------------------------------------------------
# Auto-equip sensible defaults from starting inventory
# ---------------------------------------------------------------------------

# Item name fragments → slot and priority (lower = prefer first)
_ARMOR_NAMES = set(ARMOR_PROPERTIES.keys())
_SHIELD_NAMES = {"Shield", "Wooden Shield"}
_FOCUS_NAMES  = {"Holy Symbol", "Druidic Focus", "Component Pouch",
                 "Lute", "Lyre", "Flute", "Orb", "Arcane Focus"}

def auto_equip_defaults(character_state: Dict) -> Dict:
    """Equip a sensible starting loadout from the character's inventory.
    Only runs when character_state has no equipment set yet."""
    existing = character_state.get("equipment") or {}
    if any(existing.get(k) for k in ("main_hand", "off_hand", "armor")):
        return character_state  # already configured, don't override

    inv: List[Dict] = list(character_state.get("inventory") or [])
    item_names = [_normalize_item_name(i.get("name", "")) for i in inv]

    eq = {"main_hand": None, "off_hand": None, "armor": None, "two_handed": False}

    # 1. Armor — prefer the heaviest piece available
    for aname in ["Plate Armor", "Splint Armor", "Chain Mail", "Breastplate",
                  "Half Plate", "Scale Mail", "Chain Shirt", "Hide Armor",
                  "Studded Leather", "Leather Armor", "Padded Armor"]:
        if aname in item_names:
            eq["armor"] = aname
            break

    # 2. Main hand — prefer best weapon
    weapon_priority = [
        "Longsword", "Rapier", "Scimitar", "Shortsword", "Mace",
        "Greataxe", "Greatsword", "Maul", "Warhammer", "Battleaxe",
        "Glaive", "Halberd", "Quarterstaff", "Handaxe", "Dagger",
        "Light Crossbow", "Longbow", "Shortbow", "Shortbow",
        "Two Shortswords",
    ]
    for wname in weapon_priority:
        if wname in item_names:
            wpn = WEAPON_PROPERTIES.get(wname, {})
            eq["main_hand"] = wname
            if wpn.get("hands") == "two":
                eq["two_handed"] = True
            break

    # 3. Off-hand — shield (if not two-handed) else focus
    if not eq["two_handed"]:
        for sname in ["Shield", "Wooden Shield"]:
            if sname in item_names:
                eq["off_hand"] = sname
                break
        if not eq["off_hand"]:
            for fname in ["Holy Symbol", "Druidic Focus", "Component Pouch",
                          "Lute", "Lyre", "Flute"]:
                if fname in item_names:
                    eq["off_hand"] = fname
                    break

    # Mark equipped items in inventory
    for item in inv:
        norm = _normalize_item_name(item.get("name", ""))
        for slot_key in ("main_hand", "off_hand", "armor"):
            sv = eq.get(slot_key)
            if sv and _normalize_item_name(sv) == norm and not item.get("equipped"):
                item["equipped"] = True
                item["slot"] = slot_key
                break

    return {**character_state, "equipment": eq, "inventory": inv}


# ---------------------------------------------------------------------------
# DM summary line
# ---------------------------------------------------------------------------

def equipment_context_line(character_state: Dict) -> str:
    """One-line equipment summary for the DM context block."""
    eq = get_equipment(character_state)
    parts = []

    mh = eq.get("main_hand")
    if mh:
        wpn = WEAPON_PROPERTIES.get(_normalize_item_name(mh)) or {}
        grip = "2H" if eq.get("two_handed") else "1H"
        parts.append(f"[main] {mh} ({grip})")
    else:
        parts.append("[main] empty")

    oh = eq.get("off_hand")
    if oh:
        parts.append(f"[off] {oh}")
    else:
        parts.append("[off] empty")

    armor = eq.get("armor")
    if armor:
        ac = compute_ac(character_state)
        parts.append(f"[armor] {armor} (AC {ac})")
    else:
        ac = compute_ac(character_state)
        parts.append(f"[armor] none (AC {ac})")

    free = has_free_hand(character_state)
    spell_hand = has_spellcasting_hand(character_state)
    parts.append(f"Free hand: {'YES' if free else 'NO'}")
    if not free and spell_hand:
        parts.append("(focus in off-hand — somatic OK)")

    return "Equipment: " + " · ".join(parts)
