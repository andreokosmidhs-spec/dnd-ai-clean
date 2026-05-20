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
    CLASS_FEATURES_BY_LEVEL,
    CLASS_PROFICIENCIES,
    CLASS_STARTING_EQUIPMENT,
    LANGUAGE_INFO,
    RACE_TRAITS,
    RARITY_ORDER,
    SKILL_INFO,
    get_level_up_cards,
)

logger = logging.getLogger(__name__)

# `source` taxonomy — also drives UI grouping.
SOURCES = ("race", "language", "background", "class", "trait", "proficiency",
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
        "art_key": art_key_for(source, title),
        "art_data_url": None,      # populated by attach_saved_art
        "added_at": datetime.now(timezone.utc),
        "used_at": None,
        "removed_at": None,
    }


def art_key_for(source: str, title: str) -> str:
    """Stable, case-normalized key for the art library so a card's chosen
    artwork follows the player across characters and campaigns ('Sneak Attack'
    art reused on every Rogue, 'Criminal Contact' on every Criminal, etc.)."""
    s = (source or "").strip().lower()
    t = (title or "").strip().lower()
    # collapse whitespace + punctuation for stability
    import re as _re
    t = _re.sub(r"[^\w\s-]", "", t)
    t = _re.sub(r"\s+", "-", t)
    return f"{s}::{t}"


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

    # === IDEAL / BOND / FLAW (trait cards — drive the chaos system) ===
    bg = (character or {}).get("background") or {}
    personality = bg.get("personality") or {}
    trait_specs = [
        ("ideal", "Ideal", "rare",
         "Your guiding principle. Acting in line with it keeps your roleplay aligned; betraying it raises Chaos."),
        ("bond", "Bond", "rare",
         "What you hold close. Defending or honoring it keeps your roleplay aligned; betraying it raises Chaos."),
        ("flaw", "Flaw", "rare",
         "Your defining weakness. Indulging it within reason is your nature; resisting takes effort."),
    ]
    for key, label, rarity, helper in trait_specs:
        text = (personality.get(key) or "").strip()
        if not text:
            continue
        cards.append(_new_card(
            source="trait",
            title=f"{label}: {text[:40]}",
            description=f"{text} — {helper}",
            rarity=rarity,
            mechanical="Roleplay anchor · drives Chaos meter",
            tags=["trait", key, "roleplay"],
            metadata={"trait_kind": key, "trait_text": text},
        ))

    # === CLASS features: level 1 plus every gained level up to current ===
    cls_key = _class_key(character)
    cls_block = (character or {}).get("class_") or (character or {}).get("class") or {}
    character_level = max(1, int((cls_block.get("level") or 1)))

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

    for lvl in range(2, character_level + 1):
        for feat in get_level_up_cards(cls_key, lvl):
            if feat.get("upgrades") is not None:
                # Upgrade marker — not a new card; carries patch data for merge_deck.
                cards.append({
                    "_upgrade": True,
                    "upgrades": feat["upgrades"],
                    "source": "class",
                    "title": feat["name"],
                    "description": feat["description"],
                    "mechanical": feat.get("mechanical", ""),
                    "rarity": feat.get("rarity", "common"),
                    "uses_max": feat.get("uses_max"),
                    "per_day": feat.get("per_day"),
                    "tags": ["class", cls_key.lower(), f"level-{lvl}"],
                    "metadata": {"gained_at_level": lvl},
                })
            else:
                cards.append(_new_card(
                    source="class",
                    title=feat["name"],
                    description=feat["description"],
                    rarity=feat.get("rarity", "common"),
                    mechanical=feat.get("mechanical", ""),
                    per_day=feat.get("per_day", False),
                    uses_max=feat.get("uses_max", 0),
                    tags=["class", cls_key.lower(), f"level-{lvl}"],
                    metadata={"gained_at_level": lvl},
                ))

    # === PROFICIENCIES (skills · saves · armor · weapons · tools) ===
    cls = (character or {}).get("class_") or (character or {}).get("class") or {}
    skill_profs = cls.get("skillProficiencies") or [] if isinstance(cls, dict) else []
    for skill in skill_profs:
        info = SKILL_INFO.get(skill, {"ability": "", "blurb": ""})
        ability = info.get("ability") or ""
        cards.append(_new_card(
            source="proficiency",
            title=f"Skill: {skill}",
            description=info.get("blurb") or f"Proficient in {skill}.",
            rarity="rare",
            mechanical=f"Add prof bonus to {skill} ({ability})" if ability else f"Proficient: {skill}",
            tags=["proficiency", "skill", skill.lower().replace(" ", "-")],
            metadata={"kind": "skill", "skill": skill, "ability": ability},
        ))

    profs = CLASS_PROFICIENCIES.get(cls_key, {})
    for save in profs.get("saves", []):
        cards.append(_new_card(
            source="proficiency",
            title=f"Save: {save}",
            description=f"Proficient on {save} saving throws — add your proficiency bonus when this save is called for.",
            rarity="rare",
            mechanical=f"+prof on {save} saves",
            tags=["proficiency", "save", save.lower()],
            metadata={"kind": "save", "ability": save},
        ))
    for armor in profs.get("armor", []):
        cards.append(_new_card(
            source="proficiency",
            title=f"Armor: {armor}",
            description=f"You can wear and fight effectively in {armor.lower()} without disadvantage on STR/DEX checks.",
            rarity="common",
            mechanical=f"Wear {armor} without penalty",
            tags=["proficiency", "armor", armor.lower().replace(" ", "-")],
            metadata={"kind": "armor"},
        ))
    weapons = profs.get("weapons", [])
    if weapons:
        # Compact: one card listing weapon proficiencies (otherwise classes
        # like Fighter would have 30+ cards just for weapons).
        cards.append(_new_card(
            source="proficiency",
            title="Weapon Proficiencies",
            description="Weapons you can wield without disadvantage and with full proficiency bonus to attack rolls: " + ", ".join(weapons) + ".",
            rarity="common",
            mechanical=", ".join(weapons[:3]) + ("…" if len(weapons) > 3 else ""),
            tags=["proficiency", "weapon"],
            metadata={"kind": "weapon", "list": weapons},
        ))
    # Tools — class default tools + background tool choices, deduped.
    class_tools = profs.get("tools", []) or []
    bg_tools = (character or {}).get("background", {}).get("toolChoices") or []
    seen_tools = set()
    for tool in list(class_tools) + list(bg_tools):
        key = tool.lower().strip()
        if not key or key in seen_tools:
            continue
        seen_tools.add(key)
        cards.append(_new_card(
            source="proficiency",
            title=f"Tool: {tool}",
            description=f"Trained with {tool} — add your proficiency bonus on relevant checks.",
            rarity="common",
            mechanical=f"Use {tool} skillfully",
            tags=["proficiency", "tool", key.replace(" ", "-")],
            metadata={"kind": "tool", "tool": tool},
        ))

    # === STARTING EQUIPMENT (items + gold) ===
    starter = CLASS_STARTING_EQUIPMENT.get(cls_key) or {}
    for item_name in starter.get("items") or []:
        cards.append(_new_card(
            source="item",
            title=item_name,
            description="Standard starting gear granted at character creation.",
            rarity="common",
            mechanical="",
            tags=["item", "starter", cls_key.lower()],
            metadata={"kind": "starter", "starter_class": cls_key},
        ))
    if starter.get("gold"):
        cards.append(_new_card(
            source="item",
            title=f"Coin Purse — {starter['gold']} gp",
            description=f"You begin with {starter['gold']} gold pieces in coin and small valuables.",
            rarity="common",
            mechanical=f"{starter['gold']} gp",
            tags=["item", "currency"],
            metadata={"kind": "currency", "gold": starter["gold"]},
        ))

    return cards


# -------------------- merging (for diffs) --------------------


def merge_deck(existing: List[Dict], freshly_seeded: List[Dict]) -> List[Dict]:
    """Union by (source, title): keep existing card state if present, append
    new ones. Entries with "_upgrade": True patch the matching existing card
    in-place (description, mechanical, rarity, uses_max) instead of creating
    a duplicate. Existing auto cards not present in the fresh set are marked
    lost instead of deleted."""
    auto_sources = {"race", "language", "background", "class"}
    # Live dict — updated as we add or rename cards so later upgrades see them.
    by_key: Dict = {(c["source"], c["title"]): c for c in existing}

    seen_keys: set = set()

    for fresh in freshly_seeded:
        if fresh.get("_upgrade"):
            upgrades_val = fresh["upgrades"]
            old_title = fresh["title"] if upgrades_val is True else upgrades_val
            old_key = (fresh["source"], old_title)
            new_key = (fresh["source"], fresh["title"])
            seen_keys.add(old_key)
            seen_keys.add(new_key)

            target = by_key.get(old_key) or by_key.get(new_key)
            if target is not None:
                # Patch stats; preserve uses_remaining, status, id, timestamps.
                target["description"] = fresh["description"]
                if fresh.get("mechanical") is not None:
                    target["mechanical"] = fresh["mechanical"]
                if fresh.get("rarity"):
                    target["rarity"] = fresh["rarity"]
                if fresh.get("per_day") is not None:
                    target["per_day"] = fresh["per_day"]
                new_max = fresh.get("uses_max")
                if new_max is not None:
                    old_max = target.get("uses_max", 0)
                    old_rem = target.get("uses_remaining", 0)
                    target["uses_max"] = int(new_max)
                    if int(new_max) == 0:
                        target["uses_remaining"] = 0
                    elif old_max > 0:
                        # Scale remaining by same ratio.
                        target["uses_remaining"] = max(0, old_rem + (int(new_max) - old_max))
                    else:
                        target["uses_remaining"] = int(new_max)
                # Rename if title changed.
                if fresh["title"] != old_title:
                    by_key.pop(old_key, None)
                    target["title"] = fresh["title"]
                    target["art_key"] = art_key_for(target["source"], fresh["title"])
                target.setdefault("metadata", {})["last_upgraded_at_level"] = (
                    (fresh.get("metadata") or {}).get("gained_at_level")
                )
                by_key[new_key] = target
            else:
                # No existing card to upgrade — add a real card as fallback.
                card = _new_card(
                    source=fresh["source"],
                    title=fresh["title"],
                    description=fresh["description"],
                    rarity=fresh.get("rarity", "common"),
                    mechanical=fresh.get("mechanical", ""),
                    per_day=bool(fresh.get("per_day", False)),
                    uses_max=int(fresh.get("uses_max") or 0),
                    tags=fresh.get("tags", []),
                    metadata=fresh.get("metadata", {}),
                )
                existing.append(card)
                by_key[new_key] = card
        else:
            key = (fresh["source"], fresh["title"])
            seen_keys.add(key)
            if key not in by_key:
                existing.append(fresh)
                by_key[key] = fresh  # keep by_key live for subsequent upgrades

    # Mark missing auto cards as lost.
    for card in existing:
        if card.get("_upgrade"):
            continue
        card_key = (card.get("source", ""), card.get("title", ""))
        if (card.get("source") in auto_sources
                and card.get("status") == "active"
                and card_key not in seen_keys
                and not freshly_seeded_was_empty(freshly_seeded, card.get("source", ""))):
            card["status"] = "lost"
            card["removed_at"] = datetime.now(timezone.utc)

    # Backfill art_key on any pre-existing cards (added before art support).
    for card in existing:
        if not card.get("_upgrade") and not card.get("art_key"):
            card["art_key"] = art_key_for(card.get("source", ""), card.get("title", ""))
    return existing


def attach_saved_art(cards: List[Dict], art_library: Dict[str, str]) -> List[Dict]:
    """Mutate `cards` in place: for any card whose art_key is in the library,
    set its art_data_url. `art_library` is a {art_key: data_url} dict."""
    for card in cards:
        key = card.get("art_key") or art_key_for(card.get("source", ""), card.get("title", ""))
        card["art_key"] = key
        if key in art_library:
            card["art_data_url"] = art_library[key]
    return cards


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
        "trait": "Roleplay Anchors (Ideal · Bond · Flaw)",
        "proficiency": "Proficiencies (skills · saves · armor · weapons · tools)",
        "quest": "Quest Rewards",
        "curse": "Curses & Afflictions",
        "item": "Notable Items",
        "spell": "Active Spells",
        "contact": "Contacts & Allies",
        "reputation": "Reputation",
    }
    order = ["race", "language", "background", "trait", "class", "proficiency",
             "spell", "item", "contact", "quest", "reputation", "curse"]
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


# -------------------- Quest card rewards --------------------


async def draw_quest_card_rewards(db, character_id: str, card_rewards: List[Dict]) -> List[Dict]:
    """Draw a list of card-reward specs into the character's deck.

    `card_rewards` entries follow the same shape accepted by `_new_card`:
      {source, title, description, rarity?, mechanical?, per_day?,
       consumable?, uses_max?, tags?}

    Missing / invalid source values fall back to "quest".
    Returns the list of newly-created deck-card dicts (may be empty).
    """
    if not card_rewards:
        return []

    drawn: List[Dict] = []
    for spec in card_rewards:
        src = (spec.get("source") or "quest").strip().lower()
        if src not in SOURCES:
            src = "quest"
        title = (spec.get("title") or "").strip()
        if not title:
            continue
        card = _new_card(
            source=src,
            title=title,
            description=(spec.get("description") or "").strip(),
            rarity=spec.get("rarity") or "common",
            mechanical=spec.get("mechanical") or "",
            per_day=bool(spec.get("per_day", False)),
            consumable=bool(spec.get("consumable", False)),
            uses_max=int(spec.get("uses_max") or 0),
            tags=list(spec.get("tags") or []) + ["quest-reward"],
        )
        drawn.append(card)

    if not drawn:
        return []

    # Attach art from the shared library if available.
    art_library: Dict[str, str] = {}
    try:
        cursor = db.card_art_library.find({}, {"art_key": 1, "data_url": 1, "_id": 0})
        async for doc in cursor:
            if doc.get("art_key") and doc.get("data_url"):
                art_library[doc["art_key"]] = doc["data_url"]
    except Exception:  # noqa: BLE001
        pass
    attach_saved_art(drawn, art_library)

    # Upsert into the character's deck (seed first if deck is missing).
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    deck_doc = await db.character_decks.find_one({"character_id": character_id})
    if deck_doc and isinstance(deck_doc.get("cards"), list):
        await db.character_decks.update_one(
            {"character_id": character_id},
            {"$push": {"cards": {"$each": drawn}}, "$set": {"updated_at": now}},
        )
    else:
        await db.character_decks.insert_one({
            "character_id": character_id,
            "cards": drawn,
            "created_at": now,
            "updated_at": now,
        })

    return drawn
