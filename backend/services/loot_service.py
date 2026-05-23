"""
Loot Service — derives contextually accurate loot from defeated enemies.

Weapons and armor are inferred from the enemy's own combat stats, so a
fire-damage swordsman drops a Flaming Longsword, a heavily armoured knight
drops Plate Armor, a spellcaster drops a spell scroll. Gold scales with CR.
Hidden items (potions, trinkets) are gated behind an Investigation check.
"""
from __future__ import annotations
import random
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Physical weapon lookup (damage_die, damage_type) → weapon name ────────────

_PHY: Dict[str, Dict[str, str]] = {
    "1d4":  {"slashing": "Dagger",     "piercing": "Dart",        "bludgeoning": "Club"},
    "1d6":  {"slashing": "Shortsword", "piercing": "Spear",       "bludgeoning": "Mace"},
    "1d8":  {"slashing": "Longsword",  "piercing": "Rapier",      "bludgeoning": "Warhammer"},
    "1d10": {"slashing": "Battleaxe",  "piercing": "Halberd",     "bludgeoning": "War Pick"},
    "1d12": {"slashing": "Greataxe",   "piercing": "Lance",       "bludgeoning": "Maul"},
    "2d6":  {"slashing": "Greatsword", "piercing": "Pike",        "bludgeoning": "Maul"},
    "2d8":  {"slashing": "Greatsword", "piercing": "Pike",        "bludgeoning": "Maul"},
    "3d6":  {"slashing": "Greatsword", "piercing": "Pike",        "bludgeoning": "Maul"},
}

# Elemental damage_type → (adjective, flavour sentence)
_ELEM: Dict[str, Tuple[str, str]] = {
    "fire":      ("Flaming",        "The blade is wreathed in perpetual orange flame."),
    "cold":      ("Frost",          "The pale blade leaves frost wherever it cuts."),
    "lightning": ("Thunderstrike",  "Arcs of lightning crackle along the edge."),
    "poison":    ("Venomous",       "Coated in a greenish residue that never dries."),
    "acid":      ("Corrosive",      "The pocked blade hisses faintly against the air."),
    "necrotic":  ("Soul-Drinker",   "Black blade that glows dimly with stolen life."),
    "radiant":   ("Radiant",        "Gleaming blade that hums with holy light."),
    "psychic":   ("Mind-Rending",   "Inscribed with sigils that blur when stared at."),
    "thunder":   ("Thundering",     "Vibrates faintly and booms on impact."),
    "force":     ("Force-Imbued",   "Leaves ripples in the air with every swing."),
}

# CR string → (gold_min, gold_max)
_CR_GOLD: Dict[str, Tuple[int, int]] = {
    "0":   (0,    5),
    "1/8": (3,    12),
    "1/4": (8,    25),
    "1/2": (15,   50),
    "1":   (30,   100),
    "2":   (60,   175),
    "3":   (100,  300),
    "4":   (175,  500),
    "5":   (300,  800),
    "6":   (500,  1200),
    "7":   (750,  1800),
    "8":   (1000, 2500),
    "9":   (1500, 3500),
    "10":  (2000, 5000),
}

# Enemy IDs that drop no weapon (natural attacks only) or nothing at all
_NO_WEAPON = {
    "rat", "wolf", "bear",           # beasts
    "zombie", "shadow", "wight",     # dissolve / rot
    "vampire_spawn",                 # turns to ash
    "young_dragon",                  # natural weapons; drops scales instead
}

# Commoner occupation personal effects (replaces weapon loot)
_COMMONER_PERSONAL: Dict[str, List[Tuple[str, int, str]]] = {
    "farmer":     [("Seed Pouch", 1, "common"), ("Farmer's Almanac", 2, "common"), ("Worn Boot", 0, "common")],
    "merchant":   [("Merchant Ledger", 5, "common"), ("Small Coin Purse", 3, "common"), ("Trade Seal", 8, "common")],
    "barkeep":    [("Tavern Key", 2, "common"), ("IOU Note", 1, "common"), ("Half-Full Flask", 1, "common")],
    "fisherman":  [("Fish Hook Set", 2, "common"), ("Rope (10ft)", 1, "common"), ("Smoked Fish", 1, "common")],
    "laborer":    [("Work Gloves", 1, "common"), ("Copper Coins", 2, "common"), ("Lunch Pail", 1, "common")],
    "dockworker": [("Dock Token", 3, "common"), ("Rope (20ft)", 2, "common"), ("Sailor's Knife", 5, "common")],
    "guard":      [("Guard Roster", 5, "common"), ("Whistle", 1, "common"), ("Sergeant's Orders", 8, "common")],
    "default":    [("Tattered Cloth", 0, "common"), ("Copper Coin", 1, "common"), ("Lucky Stone", 0, "common")],
}

# Enemies that drop a special material instead of a weapon
_MATERIALS: Dict[str, Tuple[str, int, str]] = {
    "rat":          ("Rat Tail",          1,   "An alchemist might pay a copper for this."),
    "wolf":         ("Wolf Pelt",         8,   "Thick and warm — worth something to a trapper."),
    "bear":         ("Bear Hide",         30,  "A large, impressive pelt."),
    "ghoul":        ("Ghoul Claws",       15,  "Sharp bone-white claws, faintly cursed."),
    "troll":        ("Troll Hide Scrap",  50,  "Regenerates slowly — valuable to alchemists."),
    "young_dragon": ("Dragon Scale",      250, "A shimmering scale — an armorsmith's treasure."),
}

# Skeleton keeps its weapons but they're corroded
_SKELETON_SUFFIX = " (Corroded)"

# CR tier buckets for hidden-item tables
def _cr_tier(cr: str) -> str:
    try:
        v = eval(cr) if "/" in cr else float(cr)      # "1/2" → 0.5
    except Exception:
        v = 1.0
    if v <= 0.5: return "low"
    if v <= 3:   return "mid"
    return "high"

# Hidden items (name, gp_value, rarity) by tier
_HIDDEN: Dict[str, List[Tuple[str, int, str]]] = {
    "low":  [
        ("Healing Potion",          50,  "common"),
        ("Tinderbox",                1,  "common"),
        ("Lock Pick Set",           25,  "common"),
    ],
    "mid":  [
        ("Potion of Greater Healing", 100, "uncommon"),
        ("Antitoxin",                  50, "common"),
        ("Spell Scroll (1st Level)",   50, "common"),
    ],
    "high": [
        ("Potion of Superior Healing", 500, "rare"),
        ("Spell Scroll (3rd Level)",   300, "uncommon"),
        ("Gem (Topaz)",                500, "uncommon"),
    ],
}

# Investigation DCs
_DC_BASIC  = 12
_DC_HIDDEN = 16


# ── Helpers ────────────────────────────────────────────────────────────────────

def _base_die(notation: str) -> str:
    """'1d12+3' → '1d12'"""
    return notation.split("+")[0].split("-")[0].strip()


def _magic_plus(attack_bonus: int) -> int:
    """
    Derive the weapon's own +X bonus.
    Typical humanoid: proficiency 2 + STR +3 = attack_bonus 5 (no magic).
    Anything above baseline implies enchantment.
    """
    if attack_bonus >= 10: return 3
    if attack_bonus >= 8:  return 2
    if attack_bonus >= 6:  return 1
    return 0


def _item(name: str, itype: str, **kwargs) -> Dict[str, Any]:
    base = {
        "name":     name,
        "type":     itype,
        "equipped": False,
        "quantity": 1,
        "source":   "looted",
    }
    base.update(kwargs)
    return base


# ── Public: weapon derivation ──────────────────────────────────────────────────

def weapon_from_enemy(enemy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Derive the weapon this enemy fights with from its stats.
    Returns None for beasts, dissolving undead, and natural-attack creatures.
    """
    eid          = enemy.get("id", "")
    damage_type  = enemy.get("damage_type", "slashing").lower()
    damage_die   = enemy.get("damage_die",  "1d6")
    attack_bonus = int(enemy.get("attack_bonus", 2))
    etype        = enemy.get("type",  "humanoid").lower()
    behavior     = enemy.get("behavior_profile", "")

    # Commoners use improvised weapons that break — they drop personal effects, not weapons
    if enemy.get("tier") == "commoner":
        return None

    if eid in _NO_WEAPON:
        return None
    if etype in ("beast", "dragon"):
        return None
    if behavior == "undead_mindless" and eid not in ("skeleton",):
        return None

    base_die    = _base_die(damage_die)
    is_elemental = damage_type not in ("slashing", "piercing", "bludgeoning")
    plus         = _magic_plus(attack_bonus)

    if is_elemental:
        # Shape: pick a slashing base (swords feel right for most magic weapons)
        base_name = _PHY.get(base_die, _PHY["1d8"])["slashing"]
        prefix, flavour = _ELEM.get(damage_type, ("Enchanted", "Shimmers with arcane energy."))
        plus_str  = f" +{plus}" if plus else ""
        name      = f"{prefix} {base_name}{plus_str}"
        rarity    = "rare" if plus >= 2 else "uncommon"
        value     = 450 * (plus + 1) if plus else 300
        desc      = flavour
        magic     = True
    else:
        row       = _PHY.get(base_die, _PHY["1d8"])
        base_name = row.get(damage_type, row.get("slashing", "Shortsword"))
        if eid == "skeleton":
            base_name += _SKELETON_SUFFIX
        plus_str  = f" +{plus}" if plus else ""
        name      = f"{base_name}{plus_str}"
        rarity    = "uncommon" if plus >= 1 else "common"
        _gp       = {"1d4": 2, "1d6": 10, "1d8": 15, "1d10": 20,
                     "1d12": 30, "2d6": 50, "2d8": 50, "3d6": 50}
        value     = _gp.get(base_die, 15) * (10 ** plus)
        desc      = (f"A well-maintained {base_name.lower()}."
                     if not plus_str else
                     f"Runes of power run along the blade (+{plus} to attack and damage rolls).")
        magic     = plus > 0

    return _item(
        name, "weapon",
        damage_die=base_die,
        damage_type=damage_type,
        magic_bonus=plus,
        attack_bonus=plus,
        magic=magic,
        rarity=rarity,
        value=value,
        description=desc,
    )


def armor_from_enemy(enemy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return armor only for well-armoured humanoids (AC ≥ 13)."""
    if enemy.get("type", "humanoid").lower() != "humanoid":
        return None
    ac = int(enemy.get("ac", 10))
    if ac <= 12:
        return None
    if ac <= 13: n, v, base_ac, r = "Leather Armor",     10,   11, "common"
    elif ac <= 15: n, v, base_ac, r = "Chain Shirt",      50,   13, "common"
    elif ac <= 17: n, v, base_ac, r = "Scale Mail",       50,   14, "common"
    elif ac <= 19: n, v, base_ac, r = "Plate Armor",    1500,   18, "uncommon"
    else:          n, v, base_ac, r = "Mithral Plate",  5000,   20, "rare"
    return _item(n, "armor", ac_base=base_ac, rarity=r, value=v,
                 description=f"Standard {n.lower()} taken from the fallen enemy.")


def scroll_from_enemy(enemy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Spellcasters drop a scroll of their highest-level spell."""
    spells = enemy.get("spell_list") or []
    behavior = enemy.get("behavior_profile", "")
    is_caster = behavior in ("spellcaster",) or bool(spells)
    if not is_caster:
        return None
    if spells:
        spell = spells[-1].replace("_", " ").title()
        return _item(
            f"Spell Scroll ({spell})", "consumable",
            spell=spells[-1], rarity="uncommon", value=150,
            description=f"A scroll bearing the {spell} spell.",
        )
    return _item(
        "Spell Scroll (Unknown)", "consumable",
        rarity="common", value=50,
        description="A scroll with faded magical inscriptions.",
    )


def material_from_enemy(enemy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Beasts and certain creatures drop materials, not weapons."""
    drop = _MATERIALS.get(enemy.get("id", ""))
    if not drop:
        return None
    name, gp, desc = drop
    return _item(name, "material", rarity="common", value=gp, description=desc)


def gold_from_enemy(enemy: Dict[str, Any]) -> int:
    cr  = str(enemy.get("cr", "1/4"))
    lo, hi = _CR_GOLD.get(cr, (10, 50))
    return random.randint(lo, hi)


# ── Public: generate full loot ─────────────────────────────────────────────────

def generate_enemy_loot(
    enemy: Dict[str, Any],
    investigation_total: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build a complete loot result for one defeated enemy.

    guaranteed      — always findable (weapon, armor, scroll, material)
    hidden          — found only with investigation_total ≥ DC
    gold            — always dropped (coin purse / scattered coins)
    investigation_dc — DC to find basic hidden items (higher DC for rare)
    """
    guaranteed: List[Dict] = []
    hidden:     List[Dict] = []

    weapon = weapon_from_enemy(enemy)
    if weapon:
        guaranteed.append(weapon)

    armor = armor_from_enemy(enemy)
    if armor:
        guaranteed.append(armor)

    scroll = scroll_from_enemy(enemy)
    if scroll:
        guaranteed.append(scroll)

    mat = material_from_enemy(enemy)
    if mat:
        guaranteed.append(mat)

    # Commoner personal effects (narrative loot, not combat items)
    if enemy.get("tier") == "commoner":
        occupation = enemy.get("occupation", "default")
        effects_pool = _COMMONER_PERSONAL.get(occupation, _COMMONER_PERSONAL["default"])
        # Pick 1-2 personal effects randomly
        picks = random.sample(effects_pool, min(2, len(effects_pool)))
        for name, gp, rarity in picks:
            guaranteed.append(_item(name, "trinket", rarity=rarity, value=gp,
                                    description=f"A personal item — something {enemy.get('name', 'they')} carried."))

    gold = gold_from_enemy(enemy)

    # Hidden loot gated by Investigation
    tier = _cr_tier(str(enemy.get("cr", "1/4")))
    pool = _HIDDEN[tier]
    if investigation_total is not None:
        if investigation_total >= _DC_HIDDEN:
            # Both basic and rare hidden items
            for n, v, r in pool:
                hidden.append(_item(n, "consumable", rarity=r, value=v))
        elif investigation_total >= _DC_BASIC:
            # Only the basic item
            n, v, r = pool[0]
            hidden.append(_item(n, "consumable", rarity=r, value=v))

    logger.info(
        "💰 Loot for %s: %d guaranteed items, %d hidden, %d gp",
        enemy.get("name"), len(guaranteed), len(hidden), gold,
    )

    return {
        "enemy_id":          enemy.get("id", ""),
        "enemy_name":        enemy.get("name", "Enemy"),
        "guaranteed":        guaranteed,
        "hidden":            hidden,
        "gold":              gold,
        "searched":          investigation_total is not None,
        "investigation_total": investigation_total,
        "investigation_dc":  _DC_BASIC,
    }


def generate_combat_loot(
    enemies: List[Dict[str, Any]],
    character_state: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Generate loot for every enemy that was defeated, rolling the player's
    Investigation check automatically.

    investigation_total = d20 + INT modifier + proficiency if trained
    """
    from services.dnd_rules import roll_d20, calculate_ability_modifier

    int_mod = calculate_ability_modifier(
        character_state.get("abilities", {}).get("int", 10)
    )
    # Assume Investigation proficiency if Wizard/Rogue/Bard class
    cls = (character_state.get("class_") or character_state.get("class") or "").lower()
    prof_bonus = int(character_state.get("proficiency_bonus", 2))
    trained    = any(c in cls for c in ("wizard", "rogue", "bard", "ranger", "artificer"))
    inv_roll   = roll_d20()
    inv_total  = inv_roll + int_mod + (prof_bonus if trained else 0)

    logger.info("🔍 Investigation check: roll=%d, total=%d (int_mod=%d, trained=%s)",
                inv_roll, inv_total, int_mod, trained)

    results = []
    for enemy in enemies:
        loot = generate_enemy_loot(enemy, investigation_total=inv_total)
        loot["investigation_roll"] = inv_roll
        loot["investigation_total"] = inv_total
        results.append(loot)

    return results


def apply_loot(
    loot_results: List[Dict[str, Any]],
    character_state: Dict[str, Any],
    take_item_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Apply a list of loot results to character_state.
    If take_item_names is given, only those items are added to inventory.
    Returns a patch dict suitable for merging into character_state.
    """
    inventory  = list(character_state.get("inventory") or [])
    gold_total = int(character_state.get("gold", 0))
    items_added: List[str] = []
    gold_added  = 0

    for loot in loot_results:
        all_items = loot.get("guaranteed", []) + loot.get("hidden", [])
        for item in all_items:
            if take_item_names is None or item["name"] in take_item_names:
                inventory.append(item)
                items_added.append(item["name"])

        g = int(loot.get("gold", 0))
        gold_total += g
        gold_added += g

    return {
        "inventory":    inventory,
        "gold":         gold_total,
        "_items_added": items_added,
        "_gold_added":  gold_added,
    }
