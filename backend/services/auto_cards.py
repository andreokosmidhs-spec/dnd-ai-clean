"""Auto-Card seeder — detects brand-new NPCs / locations / factions that the
DM invents mid-scene and auto-creates `campaign_cards` entries so subsequent
mentions become clickable entities.

Design (hybrid — regex candidates → LLM classifier):
  1. Regex-extract proper-noun candidates from the narration (sequences of
     1–4 capitalized words, excluding sentence-starters and a D&D/English
     blocklist).
  2. Filter out names we already know (`known_names` from the entity index,
     case-insensitive).
  3. If ≥1 unknown candidates remain, call a small LLM micro-classifier
     (gpt-4o-mini, structured JSON response) that tags each candidate as
     `npc`, `location`, `faction`, or `none`.
  4. Create minimal `KnowledgeCard` entries (status="introduced") in the
     `campaign_cards` collection for each classified candidate.

Cost: ~300 tokens in / ~100 tokens out per turn that introduces new names
(fractions of a cent). Zero calls when narration only uses existing names.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from services.claude_client import call_haiku_async
from data.biomes import BIOMES, get_biome, list_biome_keys

logger = logging.getLogger(__name__)

# Words that sometimes appear capitalized mid-sentence but are NOT entities.
# Mostly D&D / game terminology + common pronouns + days / months / titles.
_BLOCKLIST: Set[str] = {
    # Game terms
    "strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma",
    "str", "dex", "con", "int", "wis", "cha",
    "ac", "hp", "dc", "cr", "xp", "dm", "gm", "pc", "npc", "d4", "d6", "d8",
    "d10", "d12", "d20", "d100",
    "fighter", "wizard", "cleric", "rogue", "ranger", "paladin", "barbarian",
    "monk", "bard", "druid", "sorcerer", "warlock", "artificer",
    "human", "elf", "dwarf", "halfling", "gnome", "tiefling", "dragonborn",
    "orc", "half-elf", "half-orc",
    "attack", "action", "bonus", "reaction", "movement", "perception",
    "check", "save", "roll", "advantage", "disadvantage", "critical",
    "initiative", "surprise", "concentration", "proficiency",
    # Common English
    "the", "a", "an", "and", "or", "but", "if", "then", "so", "as", "at",
    "on", "in", "to", "of", "for", "with", "by", "from", "up", "down",
    "out", "off", "over", "under", "again", "yet", "still",
    "you", "your", "yours", "he", "she", "they", "it", "we", "us", "i",
    "me", "my", "mine", "who", "what", "where", "when", "why", "how",
    # Days / months
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december",
    # Misc titles / verbs that often get capitalized
    "sir", "lady", "lord", "captain", "master", "mister", "mrs", "ms",
    "yes", "no", "okay", "alright",
}


def _strip_prefix_articles(phrase: str) -> str:
    """Strip leading 'The/A/An ' (case-insensitive) so 'The Guild of Scribes'
    and 'Guild of Scribes' match known entries."""
    words = phrase.split()
    while words and words[0].lower() in {"the", "a", "an"}:
        words = words[1:]
    return " ".join(words)


# Matches a sequence of 1–4 capitalized words (optionally lowercase connectors
# like "of", "the", "and" allowed in the middle). Examples:
#   "Black Market Syndicate", "Wardens of Emberfall", "Lord Argus",
#   "River of Tears", "Old Greywater Road"
_CANDIDATE_RE = re.compile(
    r"\b([A-Z][a-zA-Z'\-]+(?:\s+(?:of|the|and|de|von|du|von|[A-Z][a-zA-Z'\-]+)){0,3})\b"
)


def _extract_candidates(text: str) -> List[str]:
    """Return distinct proper-noun candidate phrases from the narration.

    Filters out sentence-starting capitalization (the first word after '.?!'
    is ambiguous — we keep it only if it's multi-word so "Dawn breaks" is
    skipped but "Black Market Syndicate" is kept)."""
    if not text:
        return []
    candidates: List[str] = []
    seen: Set[str] = set()

    # Find every boundary that a sentence can start at (index+1)
    sentence_starts: Set[int] = {0}
    for m in re.finditer(r"[.!?]\s+", text):
        sentence_starts.add(m.end())

    for m in _CANDIDATE_RE.finditer(text):
        phrase = m.group(1).strip()
        # Strip any trailing connector word (of / the / and / de / von / du)
        # — the regex permits them mid-phrase but they shouldn't terminate it.
        parts = phrase.split()
        while len(parts) > 1 and parts[-1].lower() in {"of", "the", "and", "de", "von", "du"}:
            parts.pop()
        phrase = " ".join(parts)
        word_count = len(parts)

        # Skip single-word matches at sentence starts — too noisy (Dawn, The,
        # Ahead, etc. all get capitalized but are rarely entities).
        if word_count == 1 and m.start() in sentence_starts:
            continue

        lower = phrase.lower()
        if lower in _BLOCKLIST:
            continue
        # Tiny single-word entries that are in the blocklist or too short
        if word_count == 1 and (len(phrase) < 4 or lower in _BLOCKLIST):
            continue

        # Drop prefix article for de-dup
        canon = _strip_prefix_articles(phrase)
        if not canon or len(canon) < 3:
            continue
        key = canon.lower()
        if key in seen:
            continue
        seen.add(key)
        candidates.append(phrase)

    return candidates


async def _classify_candidates(
    narration: str,
    candidates: List[str],
) -> Dict[str, str]:
    """Ask a small LLM to classify each candidate as npc / location /
    faction / none. Returns a dict of `{name_lowercase: entity_type}`.

    Returns an empty dict on any failure — the caller simply skips auto-
    seeding and the scene still works (just no new clickable entities).
    """
    if not candidates:
        return {}

    # Build the prompt — keep it short and strictly structured
    candidates_json = json.dumps(candidates)
    snippet = narration[:1200]  # context is enough — no need to send the whole scene
    prompt = (
        "You are classifying fantasy RPG proper nouns found in a narrative "
        "passage. For each candidate, decide if it is:\n"
        "  - \"npc\": a named character (person or creature).\n"
        "  - \"location\": a specific place, landmark, city, region, building.\n"
        "  - \"faction\": a named group, guild, order, or organization.\n"
        "  - \"none\": anything else (greetings, game terms, generic phrases, "
        "      misfires of the regex, names that are not truly proper entities).\n\n"
        "Also provide an interaction_hint for npc/location/faction entities — "
        "a single lowercase word describing the most likely player interaction:\n"
        "  NPC hints: vendor, questgiver, enemy, ally, lore, service, guard, "
        "              mystery, informant\n"
        "  Location hints: hub, dungeon, rest, wilderness, landmark, shop, "
        "                   temple, ruins, danger\n"
        "  Faction hints: questgiver, enemy, ally, trade, information, guild, "
        "                  threat, neutral\n"
        "Use \"none\" for interaction_hint when entity type is \"none\".\n\n"
        f"Narration excerpt:\n'''{snippet}'''\n\n"
        f"Candidates to classify:\n{candidates_json}\n\n"
        "Respond with ONLY valid JSON in this shape (no extra commentary):\n"
        '{"results": [{"name": "...", "type": "npc|location|faction|none", '
        '"interaction_hint": "vendor|questgiver|enemy|..."}, ...]}'
    )

    try:
        response = await call_haiku_async(
            "You classify fantasy proper nouns. "
            "Output STRICT JSON only — no prose, no code fence.",
            prompt,
            max_tokens=300,
            temperature=0,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[auto-cards] classifier call failed: {exc}")
        return {}

    # The LLM sometimes wraps JSON in markdown fences; strip them defensively.
    text = (response or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        # After stripping backticks we may still have a "json\n" language tag
        if text.lower().startswith("json"):
            text = text[4:].lstrip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"[auto-cards] non-JSON classifier output: {text[:200]!r}")
        return {}

    # Returns {name_lower: {"type": etype, "interaction_hint": hint}}
    results: Dict[str, Dict[str, str]] = {}
    for item in parsed.get("results", []) or []:
        name = (item.get("name") or "").strip()
        etype = (item.get("type") or "").strip().lower()
        if not name:
            continue
        if etype in {"npc", "location", "faction"}:
            hint = (item.get("interaction_hint") or "none").strip().lower()
            results[name.lower()] = {"type": etype, "interaction_hint": hint}
    return results


def _card_description(name: str, entity_type: str, narration: str) -> str:
    """Snip the sentence(s) around the first mention of `name` as the
    card's content. Keeps the auto-card grounded in how the entity was
    actually introduced."""
    if not narration:
        return f"{name} — recently introduced in the narrative."
    idx = narration.lower().find(name.lower())
    if idx == -1:
        return f"{name} — recently introduced in the narrative."
    # Grab the sentence boundary on each side
    start = max(0, narration.rfind(".", 0, idx) + 1)
    end = narration.find(".", idx + len(name))
    if end == -1:
        end = min(len(narration), idx + len(name) + 200)
    snippet = narration[start:end].strip()
    return snippet or f"{name} — recently introduced in the narrative."


async def _detect_narrative_events(narration: str) -> List[Dict]:
    """Second LLM pass — detects narrative events that should become cards
    but aren't always proper-noun candidates:
       - items the player just acquired
       - spells/abilities the player learned
       - favors/boons/debts owed to or by the player
       - curses/hexes afflicting the player

    Returns a list of dicts with at least {title, type, content}. Empty list on
    failure or when nothing eventful happened (most turns).
    """
    if not narration:
        return []

    snippet = narration[:1500]
    prompt = (
        "You are reviewing a fantasy RPG scene to extract MEMORABLE EVENTS "
        "that should become permanent campaign cards. Only emit events that "
        "REALLY happened in this scene — do NOT invent.\n\n"
        "Card types to extract:\n"
        '  - "item": the player physically acquired or was given an item. '
        "Skip items the player merely sees but doesn't take.\n"
        '  - "spell": the player learned a new spell, ritual, prayer, or '
        "magical ability. Skip spells they merely cast that they already knew.\n"
        '  - "favor": someone explicitly OWES the player a favor / debt / '
        "boon, OR the player owes someone. Mutual implies two cards.\n"
        '  - "curse": the player was cursed, hexed, or afflicted with a '
        "magical malady. Skip mundane wounds.\n\n"
        "For ITEM events, also provide:\n"
        '  - "item_type": "equipment" (worn/held gear that grants bonuses), '
        '"consumable" (potions, food, single-use items), "material" (crafting '
        'components, reagents), or "currency" (gold, silver, gems as wealth)\n'
        '  - "equip_slot": for equipment only — "weapon", "armor", "accessory", '
        '"offhand", or null if not applicable\n'
        '  - "grants_bonus": for equipment only — list of {"check": "stealth", '
        '"modifier": 2} objects. Use D&D 5e skill names. Empty list if no bonus.\n'
        '  - "quantity": integer — 1 for most items; higher for potions (bundle), '
        "gold pouches (estimated gp value), arrows, rations, etc.\n\n"
        f"Scene:\n'''{snippet}'''\n\n"
        "Output STRICT JSON only:\n"
        '{"events": [{"title": "Short Name", "type": "item|spell|favor|curse", '
        '"content": "1-2 sentence summary", "item_type": "...", "equip_slot": null, '
        '"grants_bonus": [], "quantity": 1}]}\n\n'
        'If nothing eventful happened, return: {"events": []}'
    )

    try:
        response = await call_haiku_async(
            "You extract memorable RPG events. "
            "Output STRICT JSON only — no prose, no code fence.",
            prompt,
            max_tokens=400,
            temperature=0,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[auto-cards/events] call failed: {exc}")
        return []

    text = (response or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].lstrip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"[auto-cards/events] non-JSON: {text[:200]!r}")
        return []

    valid: List[Dict] = []
    for ev in parsed.get("events", []) or []:
        title = (ev.get("title") or "").strip()
        etype = (ev.get("type") or "").strip().lower()
        content = (ev.get("content") or "").strip()
        if not title or len(title) < 2:
            continue
        if etype not in {"item", "spell", "favor", "curse"} or not content:
            continue
        entry: Dict = {"title": title, "type": etype, "content": content}
        if etype == "item":
            raw_type = (ev.get("item_type") or "equipment").lower().strip()
            entry["item_type"] = raw_type if raw_type in {"equipment", "consumable", "material", "currency"} else "equipment"
            raw_slot = (ev.get("equip_slot") or "").lower().strip()
            entry["equip_slot"] = raw_slot if raw_slot in {"weapon", "armor", "accessory", "offhand"} else None
            raw_bonuses = ev.get("grants_bonus") or []
            entry["grants_bonus"] = [
                {"check": str(b.get("check", "")).lower().strip(), "modifier": int(b.get("modifier", 0))}
                for b in raw_bonuses if isinstance(b, dict) and b.get("check") and b.get("modifier") is not None
            ]
            raw_qty = ev.get("quantity")
            try:
                entry["quantity"] = max(1, int(raw_qty)) if raw_qty is not None else 1
            except (TypeError, ValueError):
                entry["quantity"] = 1
        valid.append(entry)
    # Cap so a runaway scene doesn't generate 20 cards in one turn
    return valid[:6]


# ---------------------------------------------------------------------------
# INFO-CARD DETECTION (Pass 3)
# ---------------------------------------------------------------------------

# Supported interaction hints for validation
_VALID_HINTS = {
    # NPC
    "vendor", "questgiver", "enemy", "ally", "lore", "service",
    "guard", "mystery", "informant",
    # Location
    "hub", "dungeon", "rest", "wilderness", "landmark", "shop",
    "temple", "ruins", "danger",
    # Faction / generic
    "trade", "information", "guild", "threat", "neutral",
}


async def _detect_info_clues(narration: str) -> List[Dict]:
    """Third LLM pass — detects secrets, rumors, intel, and environmental
    clues that the player perceived but hasn't fully investigated yet.

    Returns a list of info-card dicts:
      {title, hint_text, full_text, reveal_type, check_type, dc, interaction_hint}

    Empty list on failure or when nothing clue-like happened.
    Info cards start unrevealed — the player must meet the reveal condition
    (skill check or quest completion) to see the full_text.
    """
    if not narration:
        return []

    snippet = narration[:1400]
    prompt = (
        "You are scanning a fantasy RPG scene for HIDDEN INFORMATION — clues, "
        "rumors, secrets, or intel that the player can sense but hasn't fully "
        "uncovered yet. These become info cards with a reveal condition.\n\n"
        "Only emit a card when the scene ACTUALLY CONTAINS a hint of something "
        "hidden. Do NOT invent mysteries. Typical examples:\n"
        "  - An NPC drops a cryptic comment about a hidden room (Investigation)\n"
        "  - A worn notice-board mentions a missing person (free reveal)\n"
        "  - A locked chest with unusual markings is visible (Perception/Arcana)\n"
        "  - A contact whispers that a faction has a secret agenda (Insight)\n"
        "  - A completed quest would reveal the identity of a hooded figure\n\n"
        "For each clue, output:\n"
        '  "title": short label visible to the player (max 8 words)\n'
        '  "hint_text": 1 sentence the player sees BEFORE revealing — a teaser '
        "that makes them want to investigate (no spoilers)\n"
        '  "full_text": 2-3 sentences shown AFTER reveal — the actual intel\n'
        '  "reveal_type": "check" (skill roll) | "quest" (quest completion) | '
        '"free" (no condition)\n'
        '  "check_type": D&D 5e skill if reveal_type=="check", else null. '
        "Choose from: investigation, perception, insight, arcana, history, "
        "nature, religion, medicine, stealth\n"
        '  "dc": integer DC if reveal_type=="check", else null (typical 10–20)\n'
        '  "interaction_hint": single word from: vendor, questgiver, enemy, ally, '
        "lore, service, guard, mystery, informant, hub, dungeon, rest, wilderness, "
        "landmark, shop, temple, ruins, danger, trade, information, guild, threat, "
        "neutral — pick what best describes the clue's subject\n\n"
        f"Scene:\n'''{snippet}'''\n\n"
        "Output STRICT JSON only:\n"
        '{"clues": [{"title": "...", "hint_text": "...", "full_text": "...", '
        '"reveal_type": "check|quest|free", "check_type": "investigation|null", '
        '"dc": 14, "interaction_hint": "mystery"}]}\n\n'
        'If nothing clue-like is in the scene, return: {"clues": []}'
    )

    try:
        response = await call_haiku_async(
            "You detect hidden information in RPG scenes. "
            "Output STRICT JSON only — no prose, no code fence.",
            prompt,
            max_tokens=500,
            temperature=0,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[auto-cards/info] call failed: {exc}")
        return []

    text = (response or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].lstrip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"[auto-cards/info] non-JSON: {text[:200]!r}")
        return []

    valid: List[Dict] = []
    for clue in parsed.get("clues", []) or []:
        title = (clue.get("title") or "").strip()
        hint_text = (clue.get("hint_text") or "").strip()
        full_text = (clue.get("full_text") or "").strip()
        reveal_type = (clue.get("reveal_type") or "free").strip().lower()
        if not title or not hint_text or not full_text:
            continue
        if reveal_type not in {"check", "quest", "free"}:
            reveal_type = "free"

        entry: Dict = {
            "title": title[:60],
            "hint_text": hint_text[:300],
            "full_text": full_text[:480],
            "reveal_type": reveal_type,
            "check_type": None,
            "dc": None,
            "interaction_hint": None,
        }
        if reveal_type == "check":
            raw_ct = (clue.get("check_type") or "investigation").strip().lower()
            valid_checks = {
                "investigation", "perception", "insight", "arcana", "history",
                "nature", "religion", "medicine", "stealth",
            }
            entry["check_type"] = raw_ct if raw_ct in valid_checks else "investigation"
            raw_dc = clue.get("dc")
            try:
                entry["dc"] = max(5, min(30, int(raw_dc))) if raw_dc is not None else 13
            except (TypeError, ValueError):
                entry["dc"] = 13

        raw_hint = (clue.get("interaction_hint") or "mystery").strip().lower()
        entry["interaction_hint"] = raw_hint if raw_hint in _VALID_HINTS else "mystery"
        valid.append(entry)

    return valid[:4]  # cap at 4 info cards per turn


async def _classify_biome(name: str, content: str) -> str:
    """One-shot LLM call: pick the closest biome key for a location card.
    Returns a biome key from `data.biomes.BIOMES`. Falls back to 'forest'
    on any failure."""
    keys = list_biome_keys()
    keys_str = ", ".join(keys)
    prompt = (
        f"You classify fantasy RPG locations into biome categories.\n"
        f"Available biomes: {keys_str}\n\n"
        f"Location name: {name!r}\n"
        f"Description: {content[:400]!r}\n\n"
        f"Pick exactly ONE biome key from the list above that best fits "
        f"this place. If unsure, pick the closest match (e.g., a town in "
        f"a forested kingdom = 'urban' if the city itself dominates the "
        f"description, or 'forest' if it's a hamlet in the woods).\n\n"
        f'Reply with STRICT JSON only: {{"biome": "<key>"}}'
    )

    try:
        response = await call_haiku_async(
            "You classify locations. Output STRICT JSON only.",
            prompt,
            max_tokens=100,
            temperature=0,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[biome] classifier failed for {name!r}: {exc}")
        return "forest"

    text = (response or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].lstrip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return "forest"
    biome = (parsed.get("biome") or "").lower().strip()
    if biome in BIOMES:
        return biome
    return "forest"


async def _enrich_faction_identity(name: str, narration: str) -> dict:
    """Make one gpt-4o-mini call to generate faction identity fields from the
    narration context.

    Returns a dict with keys:
      purpose        — str
      values         — list[str] (2-3 items)
      values_attract — str
      tenets         — list[str] (2-3 items)
      hierarchy      — list[dict] (2-4 entries, keys: tier/role/function/min_level)
      tier_perks     — list[dict] (1-2 starter perks matching the perk schema)

    Falls back to {} on any error so callers stay non-fatal.
    """
    if not name or not narration:
        return {}

    snippet = narration[:1200]
    prompt = (
        f"You are generating faction identity details for a fantasy RPG campaign.\n\n"
        f"Faction name: {name!r}\n"
        f"Narration context:\n'''{snippet}'''\n\n"
        "Based on the narration, generate identity fields for this faction.\n\n"
        "Respond with ONLY valid JSON (no prose, no code fences) in this exact shape:\n"
        "{\n"
        '  "purpose": "one sentence describing what this faction exists to do",\n'
        '  "values": ["value1", "value2", "value3"],\n'
        '  "values_attract": "one sentence on what kind of person this faction draws in",\n'
        '  "tenets": ["tenet1", "tenet2", "tenet3"],\n'
        '  "hierarchy": [\n'
        '    {"tier": 1, "role": "Leader Title", "function": "What they do", "min_level": 1},\n'
        '    {"tier": 2, "role": "Mid Title", "function": "What they do", "min_level": 1}\n'
        "  ],\n"
        '  "tier_perks": [\n'
        '    {\n'
        '      "tier": 1,\n'
        '      "perk_id": "slug-name",\n'
        '      "name": "Perk Name",\n'
        '      "description": "What this perk grants",\n'
        '      "bonus_check": "persuasion",\n'
        '      "bonus_modifier": 2,\n'
        '      "requirements": [{"type": "area_control", "value": "area name"}]\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    try:
        response = await call_haiku_async(
            "You generate fantasy RPG faction identity data. "
            "Output STRICT JSON only — no prose, no code fence.",
            prompt,
            max_tokens=600,
            temperature=0,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[faction-identity] LLM call failed for {name!r}: {exc}")
        return {}

    text = (response or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].lstrip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"[faction-identity] non-JSON response for {name!r}: {text[:200]!r}")
        return {}

    # Validate the expected top-level keys are present before returning
    expected_keys = {"purpose", "values", "values_attract", "tenets", "hierarchy", "tier_perks"}
    if not expected_keys.issubset(parsed.keys()):
        logger.warning(f"[faction-identity] incomplete response for {name!r}: missing keys")
        return {}

    return parsed


async def auto_seed_cards_from_narration(
    *,
    campaign_id: str,
    narration: str,
    entity_index: List[Dict],
    cards_collection,
    location_origin: Optional[str] = None,
    current_location_name: Optional[str] = None,
) -> List[Dict]:
    """Main entry point.

    Returns a list of the new cards that were inserted (empty on no-op).
    Safe to call with `cards_collection is None` — it will just no-op.
    """
    if not narration or not campaign_id or cards_collection is None:
        return []

    # Build a set of known names (case-insensitive) from the current index
    known: Set[str] = set()
    for entry in entity_index or []:
        name = entry.get("name")
        if not name:
            continue
        known.add(name.lower())
        known.add(_strip_prefix_articles(name).lower())
        # Also include the possessive form so "Emberfall" in the index
        # prevents "Emberfall's" from being re-seeded.
        known.add(f"{name.lower()}'s")
        known.add(f"{_strip_prefix_articles(name).lower()}'s")

    # Candidates
    candidates = _extract_candidates(narration)
    # Strip trailing possessive apostrophe-s ("Emberfall's" -> "Emberfall")
    # so we don't create duplicate cards for grammatical variants.
    normalized: List[str] = []
    seen_norm: Set[str] = set()
    for c in candidates:
        clean = c.rstrip(".,;:!?")
        if clean.endswith("'s") or clean.endswith("\u2019s"):
            clean = clean[:-2].strip()
        if not clean or len(clean) < 3:
            continue
        key = clean.lower()
        if key in seen_norm:
            continue
        seen_norm.add(key)
        normalized.append(clean)
    unknowns = [c for c in normalized if _strip_prefix_articles(c).lower() not in known]
    if not unknowns:
        return []

    # Cap so a runaway regex never balloons LLM cost
    unknowns = unknowns[:12]

    classifications = await _classify_candidates(narration, unknowns)
    if not classifications:
        return []

    now = datetime.now(timezone.utc)
    new_cards: List[Dict] = []

    # Pass 1 — proper-noun entities (NPCs / locations / factions)
    for phrase in unknowns:
        canon = _strip_prefix_articles(phrase)
        entry = classifications.get(phrase.lower()) or classifications.get(canon.lower())
        if not entry:
            continue
        etype = entry.get("type") if isinstance(entry, dict) else entry
        interaction_hint = entry.get("interaction_hint", "none") if isinstance(entry, dict) else "none"
        if not etype or etype == "none":
            continue

        # Double-check against DB (race-safe if multiple turns overlap)
        existing = await cards_collection.find_one(
            {"campaign_id": campaign_id, "title": canon, "type": etype}
        )
        if existing:
            continue

        card = {
            "id": str(uuid.uuid4()),
            "campaign_id": campaign_id,
            "title": canon,
            "type": etype,
            "content": _card_description(canon, etype, narration),
            "status": "introduced",
            "auto_seeded": True,
            "source": "dm_narration",
            "pinned": False,
            "interaction_hint": interaction_hint if interaction_hint != "none" else None,
            "revealed": True,   # entity cards are always visible
            "location_origin": location_origin or None,
            # Stamp character/NPC cards with where they were first encountered
            # so the DM knows who is reachable at the current location.
            "at_location": current_location_name if etype == "character" and current_location_name else None,
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }
        # If this is a location card, classify its biome so the UI can
        # render the right accent color and so future Survival/Nature
        # checks know what creatures and resources are available.
        if etype == "location":
            biome_key = await _classify_biome(canon, card["content"])
            biome = get_biome(biome_key)
            card["biome"] = biome_key
            card["biome_label"] = biome["label"]
            card["biome_accent"] = biome["accent"]
            card["biome_chip"] = biome["chip"]
            card["biome_resources"] = biome["resources"]
            card["biome_animals"] = biome["animals"]
            card["biome_monsters"] = biome["monsters"]
            card["biome_survival_dc_mod"] = biome["survival_dc_mod"]
            card["biome_nature_dc_mod"] = biome["nature_dc_mod"]
        try:
            await cards_collection.insert_one(card)
            new_cards.append(card)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[auto-cards] insert failed for {canon!r}: {exc}")
            continue

        # For newly seeded faction cards, enrich with generated identity fields.
        if etype == "faction":
            try:
                identity = await _enrich_faction_identity(canon, narration)
                if identity:
                    await cards_collection.update_one(
                        {"campaign_id": campaign_id, "id": card["id"]},
                        {"$set": identity},
                    )
                    # Keep the in-memory copy consistent for this turn's entity index
                    card.update(identity)
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[auto-cards] faction identity enrich failed for {canon!r}: {exc}")

    # Pass 2 — narrative events (items / spells / favors / curses).
    # These are NOT always proper nouns, so a separate LLM pass scans the
    # scene for event-shaped happenings the player should remember.
    events = await _detect_narrative_events(narration)
    for ev in events:
        title = ev["title"]
        etype = ev["type"]
        # De-dupe within campaign on (title, type)
        existing = await cards_collection.find_one(
            {"campaign_id": campaign_id, "title": title, "type": etype}
        )
        if existing:
            continue
        card = {
            "id": str(uuid.uuid4()),
            "campaign_id": campaign_id,
            "title": title,
            "type": etype,
            "content": ev["content"],
            "status": "active" if etype in {"favor", "curse"} else "acquired",
            "auto_seeded": True,
            "source": "dm_event",
            "pinned": False,
            "location_origin": location_origin or None,
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }
        if etype == "item":
            card["item_type"] = ev.get("item_type") or "equipment"
            card["equip_slot"] = ev.get("equip_slot") or None
            card["grants_bonus"] = ev.get("grants_bonus") or []
            card["quantity"] = ev.get("quantity") or 1
        try:
            await cards_collection.insert_one(card)
            new_cards.append(card)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[auto-cards/event] insert failed for {title!r}: {exc}")

    # Pass 3 — info/clue cards (hidden intel with reveal conditions).
    clues = await _detect_info_clues(narration)
    for clue in clues:
        title = clue["title"]
        # De-dupe within campaign on title+type
        existing = await cards_collection.find_one(
            {"campaign_id": campaign_id, "title": title, "type": "info"}
        )
        if existing:
            continue

        reveal_condition: Optional[Dict] = None
        if clue["reveal_type"] == "check":
            reveal_condition = {
                "type": "check",
                "check_type": clue["check_type"],
                "dc": clue["dc"],
            }
        elif clue["reveal_type"] == "quest":
            reveal_condition = {"type": "quest", "quest_id": None}
        else:
            reveal_condition = {"type": "free"}

        card = {
            "id": str(uuid.uuid4()),
            "campaign_id": campaign_id,
            "title": title,
            "type": "info",
            "content": clue["hint_text"],       # visible before reveal
            "full_content": clue["full_text"],  # revealed only
            "status": "hidden",
            "revealed": False,
            "reveal_condition": reveal_condition,
            "interaction_hint": clue.get("interaction_hint"),
            "auto_seeded": True,
            "source": "dm_narration",
            "pinned": False,
            "location_origin": location_origin or None,
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }
        try:
            await cards_collection.insert_one(card)
            new_cards.append(card)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[auto-cards/info] insert failed for {title!r}: {exc}")

    if new_cards:
        logger.info(
            f"[auto-cards] seeded {len(new_cards)} new card(s) for campaign {campaign_id}: "
            f"{[(c['type'], c['title']) for c in new_cards]}"
        )
    return new_cards
