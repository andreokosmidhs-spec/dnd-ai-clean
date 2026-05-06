"""Character Deck — the player's personal card deck.

Each character has a deck of cards built from their identity:
  * race      — Darkvision, Fey Ancestry, …
  * language  — Common, Elvish, Thieves' Cant
  * background— Criminal Contact, Position of Privilege
  * class     — level-1 features (Sneak Attack, Rage, Spellcasting)

Future sources (stubbed): quest, curse, item, spell, contact, reputation.

Cards have a rarity (common / rare / epic / legendary) and may be:
  * `per_day=True`  → spent uses refresh on a long rest (Rage, spell slots)
  * `consumable=True` → permanent uses (one-time favor, single-use item)
  * neither           → passive trait (Darkvision, language)

The DM consumes a compact summary every turn (`deck_context_block`) so it can
naturally weave the character's features into narration: see-in-the-dark,
language-fluent, faction-connected, etc.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from data.character_features import (
    BACKGROUND_FEATURES,
    CLASS_FEATURES_LEVEL_1,
    LANGUAGE_INFO,
    RACE_TRAITS,
    RARITY_ORDER,
)

logger = logging.getLogger(__name__)

# `source` taxonomy — also drives UI grouping.
SOURCES = ("race", "language", "background", "class",
           "quest", "curse", "item", "spell", "contact", "reputation")


def _new_card(*, source: str, title: str, description: str,
              rarity: str = "common", mechanical: str = "",
              per_day: bool = False, consumable: bool = False,
              uses_max: int = 0, tags: Optional[List[str]] = None,
              metadata: Optional[Dict] = None) -> Dict:
    """Build a normalized DeckCard dict."""
    if rarity not in RARITY_ORDER:
        rarity = "common"
    return {
        "id": f"deck_{uuid4().hex[:10]}",
        "source": source,
        "title": title.strip()[:60],
        "description": description.strip()[:480],
        "rarity": rarity,
        "mechanical": mechanical[:120] if mechanical else "",
        "per_day": bool(per_day),
        "consumable": bool(consumable),
        "uses_max": int(uses_max or 0),
        "uses_remaining": int(uses_max or 0),
        "status": "active",        # active | spent | lost | cleared
        "tags": tags or [],
        "metadata": metadata or {},
        "added_at": datetime.now(timezone.utc),
        "used_at": None,
        "removed_at": None,
    }


# -------------------- seeding --------------------


def _race_key(character: Dict) -> str:
    """Resolve the race key the catalog uses ("Elf", "Half-Orc", …)."""
    race = (character or {}).get("race") or {}
    raw = race.get("key") or race.get("name") or ""
    if not raw:
        return ""
    # Normalize to title-case keys matching RACE_TRAITS.
    norm = raw.strip().title().replace("Half Elf", "Half-Elf").replace("Half Orc", "Half-Orc")
    return norm


def _class_key(character: Dict) -> str:
    cls = (character or {}).get("class_") or (character or {}).get("class") or {}
    raw = cls.get("key") or cls.get("name") or ""
    return raw.strip().title()


def _background_key(character: Dict) -> str:
    bg = (character or {}).get("background") or {}
    raw = bg.get("key") or bg.get("name") or ""
    return raw.strip().lower().replace(" ", "_")


def _languages(character: Dict) -> List[str]:
    """Pull the character's language list from the most likely fields. Falls
    back to the race's base languages when nothing explicit is stored."""
    out: List[str] = []
    for field in ("languages", "language_proficiencies"):
        val = (character or {}).get(field)
        if isinstance(val, list):
            out.extend(str(x).strip() for x in val if str(x).strip())
    bg = (character or {}).get("background") or {}
    bg_langs = bg.get("languages")
    if isinstance(bg_langs, list):
        out.extend(str(x).strip() for x in bg_langs if str(x).strip())
    elif isinstance(bg_langs, dict):
        for v in bg_langs.values():
            if isinstance(v, list):
                out.extend(str(x).strip() for x in v if str(x).strip())
    # de-dup while preserving order
    seen, ordered = set(), []
    for lang in out:
        key = lang.title()
        if key not in seen:
            seen.add(key)
            ordered.append(key)
    if not ordered:
        # Default to Common — every character knows it.
        ordered = ["Common"]
    return ordered


def seed_deck_for_character(character: Dict) -> List[Dict]:
    """Return the full auto-seeded deck for `character`. Idempotent in shape:
    given the same character snapshot, you'll get the same set of cards
    (with fresh ids — the caller is expected to compare on
    `(source, title)` to avoid duplicates)."""
    cards: List[Dict] = []

    # === RACE ===
    race_key = _race_key(character)
    for trait in RACE_TRAITS.get(race_key, []):
        cards.append(_new_card(
            source="race",
            title=trait["name"],
            description=trait["description"],
            rarity=trait.get("rarity", "common"),
            mechanical=trait.get("mechanical", ""),
            per_day=trait.get("per_day", False),
            uses_max=trait.get("uses_max", 0),
            tags=["race", race_key.lower()],
        ))

    # === LANGUAGES ===
    for lang in _languages(character):
        info = LANGUAGE_INFO.get(lang, {"description": f"You speak {lang} fluently.", "rarity": "common"})
        cards.append(_new_card(
            source="language",
            title=lang,
            description=info["description"],
            rarity=info.get("rarity", "common"),
            mechanical=f"Read · Speak · Write {lang}",
            tags=["language", lang.lower()],
        ))

    # === BACKGROUND ===
    bg_key = _background_key(character)
    bg_feat = BACKGROUND_FEATURES.get(bg_key)
    if bg_feat:
        cards.append(_new_card(
            source="background",
            title=bg_feat["name"],
            description=bg_feat["description"],
            rarity=bg_feat.get("rarity", "common"),
            mechanical=bg_feat.get("mechanical", ""),
            tags=["background", bg_key],
        ))

    # === CLASS (level-1 features) ===
    cls_key = _class_key(character)
    for feat in CLASS_FEATURES_LEVEL_1.get(cls_key, []):
        cards.append(_new_card(
            source="class",
            title=feat["name"],
            description=feat["description"],
            rarity=feat.get("rarity", "common"),
            mechanical=feat.get("mechanical", ""),
            per_day=feat.get("per_day", False),
            uses_max=feat.get("uses_max", 0),
            tags=["class", cls_key.lower()],
        ))

    return cards


# -------------------- merging (for diffs) --------------------


def merge_deck(existing: List[Dict], freshly_seeded: List[Dict]) -> List[Dict]:
    """Union by (source, title): keep existing card state if present, append
    new ones. Used when a character levels up or gains/loses a feature.
    Existing cards that are NOT in the freshly_seeded set (and are auto-source
    cards: race/language/background/class) get marked `lost` instead of
    deleted, so we keep an audit trail."""
    auto_sources = {"race", "language", "background", "class"}
    by_key = {(c["source"], c["title"]): c for c in existing}

    seen_keys: set = set()
    for fresh in freshly_seeded:
        key = (fresh["source"], fresh["title"])
        seen_keys.add(key)
        if key not in by_key:
            existing.append(fresh)

    # Mark missing auto cards as lost.
    for card in existing:
        if (card["source"] in auto_sources
                and card["status"] == "active"
                and (card["source"], card["title"]) not in seen_keys
                and not freshly_seeded_was_empty(freshly_seeded, card["source"])):
            card["status"] = "lost"
            card["removed_at"] = datetime.now(timezone.utc)
    return existing


def freshly_seeded_was_empty(freshly: List[Dict], source: str) -> bool:
    """Avoid marking auto cards as 'lost' when the seeder produced nothing for
    that source (e.g. no race catalog entry → don't nuke whatever already
    exists)."""
    return not any(c.get("source") == source for c in freshly)


# -------------------- DM context block --------------------


def deck_context_block(deck: List[Dict], max_chars: int = 900) -> str:
    """Tight one-paragraph summary the DM gets every turn. Lists active cards
    with rarity/per-day status so narration can naturally reflect them.
    Spent or lost cards are skipped."""
    if not deck:
        return "=== CHARACTER DECK ===\n(empty)"
    active = [c for c in deck if c.get("status") == "active"]
    # Sort by rarity (legendary first) then source.
    active.sort(key=lambda c: (RARITY_ORDER.get(c["rarity"], 99), c["source"], c["title"]))

    # Group by source for compact output.
    grouped: Dict[str, List[str]] = {}
    for c in active:
        bits = [c["title"]]
        if c.get("rarity") in {"epic", "legendary"}:
            bits.append(f"({c['rarity']})")
        if c.get("per_day") and c.get("uses_max"):
            bits.append(f"[{c.get('uses_remaining', 0)}/{c['uses_max']} per day]")
        elif c.get("consumable") and c.get("uses_max"):
            bits.append(f"[{c.get('uses_remaining', 0)}/{c['uses_max']} uses]")
        grouped.setdefault(c["source"], []).append(" ".join(bits))

    lines = ["=== CHARACTER DECK (player's identity & resources — weave naturally into narration) ==="]
    label = {
        "race": "Race",
        "language": "Languages",
        "background": "Background",
        "class": "Class",
        "quest": "Quest Rewards",
        "curse": "Curses & Afflictions",
        "item": "Notable Items",
        "spell": "Active Spells",
        "contact": "Contacts & Allies",
        "reputation": "Reputation",
    }
    order = ["race", "language", "background", "class", "spell", "item",
             "contact", "quest", "reputation", "curse"]
    for src in order:
        if src in grouped:
            lines.append(f"{label.get(src, src.title())}: {' · '.join(grouped[src])}")
    out = "\n".join(lines)
    if len(out) > max_chars:
        out = out[: max_chars - 3] + "..."
    out += (
        "\nUse this deck to gauge what the character can perceive (Darkvision), "
        "say (languages), call upon (Criminal Contact, Military Rank), or do "
        "(Sneak Attack, Rage, Spellcasting). Reference these naturally when "
        "they apply; do NOT recite them as a list."
    )
    return out
