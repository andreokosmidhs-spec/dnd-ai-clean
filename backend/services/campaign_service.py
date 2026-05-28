from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4
import logging

from models.campaign_models import CampaignIntent, KnowledgeCard
from utils.entity_mentions import extract_entity_mentions

logger = logging.getLogger(__name__)


def build_v2_entity_index(world: Dict, cards: Optional[List[Dict]] = None) -> List[Dict]:
    """Build an entity index from a V2 `world` dict + optional knowledge cards.

    The V2 shape differs from the legacy `world_blueprint` (single
    starting_town as a string name, factions nested under `setting`), so we
    can't use `build_entity_index_from_world_blueprint` directly.

    Output shape matches what `extract_entity_mentions` expects:
    `[{entity_type, entity_id, name}, ...]`.
    """
    index: List[Dict] = []
    seen: set = set()  # lowercase-name de-dupe

    def add(entity_type: str, name: str, entity_id_prefix: str):
        if not name:
            return
        key = (entity_type, name.lower())
        if key in seen:
            return
        seen.add(key)
        slug = name.lower().replace(" ", "_").replace("'", "")
        index.append({
            "entity_type": entity_type,
            "entity_id": f"{entity_id_prefix}_{slug}",
            "name": name,
        })

    world = world or {}
    # Realm
    realm = (world.get("world_core") or {}).get("name")
    if realm and realm.lower() != "unknown realm":
        add("location", realm, "loc")
    # Starting town
    town = (world.get("starting_town") or {}).get("name")
    if town and town.lower() != "unknown town":
        add("location", town, "loc")
    # Starting location (legacy shape carried through `build_world_blueprint`)
    start_loc = world.get("startingLocation") or {}
    if isinstance(start_loc, dict) and start_loc.get("name"):
        add("location", start_loc["name"], "loc")
    # Points of interest
    for poi in world.get("points_of_interest", []) or []:
        if isinstance(poi, dict) and poi.get("name"):
            add("location", poi["name"], "loc")
        elif isinstance(poi, str):
            add("location", poi, "loc")
    # Factions (setting.factions preferred, legacy factions fallback)
    factions = (world.get("setting") or {}).get("factions") or world.get("factions") or []
    for f in factions:
        if isinstance(f, dict) and f.get("name"):
            add("faction", f["name"], "faction")
    # Key NPCs (legacy / future-seeded)
    for npc in world.get("key_npcs", []) or world.get("npcs", []) or []:
        if isinstance(npc, dict) and npc.get("name"):
            add("npc", npc["name"], "npc")
    # Knowledge cards: pull named entity cards so pinned NPCs/locations stay
    # linkable in subsequent turns even if they were invented during play.
    for card in cards or []:
        card_type = (card.get("type") or "").lower()
        title = card.get("title") or card.get("name") or ""
        if not title:
            continue
        # Map both new-schema ("location") and legacy-schema ("place")
        # type tags onto the unified entity types.
        if card_type in {"npc", "character"}:
            add("npc", title, "npc")
        elif card_type in {"location", "place", "landmark", "city", "region"}:
            add("location", title, "loc")
        elif card_type in {"faction", "guild", "organization"}:
            add("faction", title, "faction")
        elif card_type in {"item", "artifact"}:
            add("item", title, "item")

    # Sort by descending name length so longer names win over shorter ones
    # (e.g., "Black Market Syndicate" before "Black Market").
    index.sort(key=lambda e: len(e["name"]), reverse=True)
    return index


def _format_title(text: str) -> str:
    return text.replace("_", " ").title()


def _extract_personality(character: Optional[Dict]) -> Dict:
    """Extract ideal, bond, flaw from V2 (ideals[]/bonds[]/flaws_detailed[])
    or legacy (background.personality.*) character format."""
    empty = {"ideal": "", "bond": "", "flaw": ""}
    if not character:
        return empty

    ideal = bond = flaw = ""

    # V2 arrays
    ideals = character.get("ideals") or []
    if ideals and isinstance(ideals[0], dict):
        ideal = (ideals[0].get("principle") or "").strip()

    bonds = character.get("bonds") or []
    if bonds and isinstance(bonds[0], dict):
        bond = (bonds[0].get("person_or_cause") or "").strip()

    flaws = character.get("flaws_detailed") or []
    if flaws and isinstance(flaws[0], dict):
        flaw = (flaws[0].get("habit") or "").strip()

    # Legacy fallback
    if not ideal or not bond or not flaw:
        personality = (character.get("background") or {}).get("personality") or {}
        ideal = ideal or (personality.get("ideal") or "").strip()
        bond = bond or (personality.get("bond") or "").strip()
        flaw = flaw or (personality.get("flaw") or "").strip()

    return {"ideal": ideal, "bond": bond, "flaw": flaw}


# Short flavor guidance per D&D class — keeps the AI narrator's language
# tonally consistent with the hero's archetype without stereotyping.
_CLASS_FLAVOR = {
    "barbarian": "visceral, physical, raw — think breath, heartbeat, primal instincts",
    "bard": "performative, observant of social undercurrents, attuned to rumor and rhythm",
    "cleric": "reverent and disciplined; the divine is quiet pressure, not constant miracle",
    "druid": "rooted in weather, animal signs, the smell of earth; nature as a character",
    "fighter": "practical, trained eye for terrain, weapons, exits, and threats",
    "monk": "spare, precise, attentive to breath, balance, and the stillness between sounds",
    "paladin": "moral weight and conviction; oaths color how the world is seen",
    "ranger": "tracker's eye — footprints, broken twigs, wind direction, animal silence",
    "rogue": "shadows, sightlines, escape routes, pockets, locks — always reading the room",
    "sorcerer": "magic is in the blood; subtle currents, intuition, flickers of the uncanny",
    "warlock": "a patron's presence lurks at the edge; whispered debts, unsettling omens",
    "wizard": "cerebral, analytical — arcane patterns, etymology, cataloged observation",
    "artificer": "tinker's eye — materials, mechanisms, opportunities to improvise",
    "_default": "grounded, observant, driven by the hero's own reasons",
}


def _build_starting_location(intent: CampaignIntent) -> Dict:
    scope_names = {
        "City": "Gate of Emberfall",
        "Wilderness": "Trail of Whispering Pines",
        "Dungeon": "Vault of Forgotten Echoes",
        "Mixed": "Crossroads of Twin Lanterns",
    }
    return {
        "name": scope_names.get(intent.scope, "Frontier Outpost"),
        "description": f"A {intent.scope.lower()} starting point shaped by a {intent.tone.lower()} tone.",
        "danger": intent.danger,
        "focus": intent.focus,
    }


def build_world_blueprint(intent: CampaignIntent, character: Dict | None) -> Dict:
    hero_desc = "adventurer"
    if character:
        race = character.get("race", {})
        class_info = character.get("class", {}) or character.get("class_", {})
        background = character.get("background", {})
        race_name = _format_title(race.get("key", "wanderer"))
        class_name = _format_title(class_info.get("key", "hero"))
        bg_name = _format_title(background.get("key", "drifter"))
        hero_desc = f"{race_name} {class_name} from a {bg_name} background"

    starting_location = _build_starting_location(intent)

    summary = (
        f"A {intent.tone.lower()} campaign focused on {intent.focus.lower()} begins in the {starting_location['name']}, "
        f"tailored for a {hero_desc}."
    )

    realm_name = f"Realm of {_format_title(intent.focus)}"

    return {
        "summary": summary,
        "tags": [intent.tone.lower(), intent.focus.lower(), intent.scope.lower(), intent.danger.lower()],
        "startingLocation": starting_location,
        "theme": intent.focus,
        "tone": intent.tone,
        # Legacy-compatible aliases so the frontend WorldInfoPanel shows real names
        # instead of "Unknown Realm / Unknown Town".
        "world_core": {
            "name": realm_name,
            "summary": summary,
            "tone": intent.tone,
        },
        "starting_town": {
            "name": starting_location["name"],
            "summary": starting_location["description"],
        },
    }


def _template_world_setting(intent: CampaignIntent, world: Dict) -> Dict:
    """Deterministic fallback used when the LLM is unavailable.
    Provides minimal but coherent setting context.
    """
    realm_name = world.get("world_core", {}).get("name", "the realm")
    return {
        "era": "An age where steel rules the field, magic is real but uncommon, and most folk distrust both.",
        "factions": [
            {
                "name": "The Crown's Council",
                "domain": "the law of the realm",
                "stance": "publicly benevolent, privately overreaching",
            },
            {
                "name": "The Merchant Concord",
                "domain": "trade routes and lending",
                "stance": "wealth-first; will tolerate any flag that pays",
            },
            {
                "name": "The Hollow Order",
                "domain": "old magics and forbidden lore",
                "stance": "outlawed in cities; tolerated in border towns",
            },
        ],
        "recent_events": [
            {
                "title": "The Long Drought",
                "summary": f"Three poor harvests have hardened {realm_name}; bread is scarce and tempers shorter.",
            },
            {
                "title": "The Sealed Pact",
                "summary": "A treaty between the Crown and the Merchant Concord shifted power; some call it a betrayal.",
            },
        ],
        "current_tension": (
            f"Power tilts uneasily in {realm_name}. The streets feel watched, "
            "and small loyalties matter more than grand titles right now."
        ),
    }


async def generate_world_setting_with_ai(
    intent: CampaignIntent,
    world: Dict,
    character: Optional[Dict],
) -> Dict:
    """Generate a campaign-specific SETTING block: era, factions, recent
    events, current tension. Falls back to a coherent template on any failure.
    """
    fallback = _template_world_setting(intent, world)
    try:
        import json as _json
        from services.claude_client import call_haiku_async

        starting = world.get("startingLocation", {})
        realm_name = world.get("world_core", {}).get("name", "the realm")
        location_name = starting.get("name", "the starting area")

        race_key = "human"
        class_key = "adventurer"
        bg_key = "wanderer"
        if character:
            race_key = (character.get("race") or {}).get("key", race_key)
            cls = character.get("class") or character.get("class_") or {}
            class_key = (cls.get("key") or class_key).lower()
            bg_key = ((character.get("background") or {}).get("key") or bg_key).lower()

        prompt = (
            "Design the SETTING for a Dungeons & Dragons 5e campaign. The hero will see this on "
            "their world panel; the DM will use it on every turn. It must feel like a real place "
            "with real history and real factions in conflict — not generic fantasy soup.\n\n"
            "=== CAMPAIGN PARAMETERS ===\n"
            f"Tone: {intent.tone} | Focus: {intent.focus} | Scope: {intent.scope} | Danger: {intent.danger}\n"
            f"Realm name: {realm_name}\n"
            f"Starting location: {location_name} — {starting.get('description', '')}\n"
            f"Hero: {_format_title(race_key)} {_format_title(class_key)} ({_format_title(bg_key)} background)\n\n"
            "=== STRICT REQUIREMENTS ===\n"
            f"- The era must clearly match the {intent.tone} tone (gritty = post-war, scarcity, "
            "broken institutions; heroic = rising kingdoms, banners returning; mystery = secretive "
            "guilds, occult rumors).\n"
            f"- All three factions must have a clear DOMAIN (what they control or do) and a "
            "STANCE (their attitude or method). They must be in conflict, openly or quietly.\n"
            "- Recent events are events that happened RECENTLY (months to a few years ago), not "
            "ancient history. They must shape the current mood of the streets.\n"
            "- Current tension must be a concrete, palpable problem the player would notice "
            "walking around — bread shortage, curfew, missing tax barge, watch arresting "
            "songsmiths, something specific.\n"
            "- NO clichés (no 'ancient evil awakens', 'chosen one', 'dark lord rises'). Real history.\n"
            "- Names should feel earned, not Tolkien-pastiche. Avoid apostrophes.\n\n"
            "=== OUTPUT (strict JSON, no prose, no code fence) ===\n"
            "{\n"
            "  \"era\": \"1-2 sentences capturing the time period and the dominant feel of life right now\",\n"
            "  \"factions\": [\n"
            "    {\"name\": \"...\", \"domain\": \"what they control or do, 4-10 words\", \"stance\": \"their attitude/method, 4-10 words\"},\n"
            "    ... (exactly 3 factions, in active tension)\n"
            "  ],\n"
            "  \"recent_events\": [\n"
            "    {\"title\": \"3-6 word event name\", \"summary\": \"1 sentence describing what happened and how it changed things\"},\n"
            "    ... (exactly 2 recent events)\n"
            "  ],\n"
            "  \"current_tension\": \"1-2 sentence summary of the concrete pressure on the streets right now\"\n"
            "}\n"
        )

        raw = await call_haiku_async(
            "You are a senior D&D worldbuilder. You produce specific, grounded setting bibles "
            "with factions in real conflict and recent events that shape the day. Output strict JSON only.",
            prompt,
            max_tokens=500,
            temperature=0,
        ) or ""

        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        try:
            data = _json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end > start:
                data = _json.loads(text[start : end + 1])
            else:
                raise

        # Light validation: keep what's there, fall back on anything missing
        era = (data.get("era") or "").strip()
        factions_raw = data.get("factions") or []
        events_raw = data.get("recent_events") or []
        tension = (data.get("current_tension") or "").strip()

        factions = []
        for f in factions_raw[:3]:
            if isinstance(f, dict) and f.get("name"):
                factions.append({
                    "name": str(f.get("name")).strip()[:60],
                    "domain": str(f.get("domain") or "").strip()[:120],
                    "stance": str(f.get("stance") or "").strip()[:120],
                })
        events = []
        for e in events_raw[:2]:
            if isinstance(e, dict) and e.get("title"):
                events.append({
                    "title": str(e.get("title")).strip()[:60],
                    "summary": str(e.get("summary") or "").strip()[:200],
                })

        return {
            "era": era or fallback["era"],
            "factions": factions or fallback["factions"],
            "recent_events": events or fallback["recent_events"],
            "current_tension": tension or fallback["current_tension"],
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"AI world-setting generation failed, using template: {exc}")
        return fallback


def setting_knowledge_cards(setting: Dict) -> List[KnowledgeCard]:
    """Convert the world setting into knowledge cards so factions, events,
    and the current tension show up on the player's deck AND get fed into
    the DM prompt every turn.
    """
    cards: List[KnowledgeCard] = []
    for f in (setting.get("factions") or [])[:3]:
        if not f.get("name"):
            continue
        desc = "; ".join(p for p in [f.get("domain"), f.get("stance")] if p)
        cards.append(
            KnowledgeCard(
                id=str(uuid4()),
                type="faction",
                title=f["name"],
                description=desc or "An active faction in the realm.",
                tags=["faction", "setting"],
            )
        )
    for e in (setting.get("recent_events") or [])[:2]:
        if not e.get("title"):
            continue
        cards.append(
            KnowledgeCard(
                id=str(uuid4()),
                type="event",
                title=e["title"],
                description=e.get("summary") or "A recent event that shapes the realm.",
                tags=["history", "setting", "recent"],
            )
        )
    tension = (setting.get("current_tension") or "").strip()
    if tension:
        cards.append(
            KnowledgeCard(
                id=str(uuid4()),
                type="belief",
                title="What the streets feel like",
                description=tension,
                tags=["tension", "setting", "mood"],
            )
        )
    return cards


def build_starting_scene(campaign_id: str, world: Dict) -> Dict:
    starting_location = world.get("startingLocation", {})
    location_name = starting_location.get("name", "the starting point")
    intro_text = (
        f"You arrive at {location_name}, a place colored by {world.get('tone', 'mixed')} tales. "
        "Locals watch curiously as your journey begins."
    )
    return {
        "seed": f"scene_{campaign_id[:8]}",
        "introText": intro_text,
    }


async def generate_world_brief_with_ai(
    intent: CampaignIntent,
    world: Dict,
    character: Optional[Dict],
    setting: Optional[Dict] = None,
) -> str:
    """World-state text: the macro view that opens the campaign.
    Shows the lay of the land and powers at play through the wound they create —
    not as a geography lecture but as a living system already in motion.
    The arrival narration zooms into this world immediately after.
    Falls back to a coherent template on failure.
    """
    realm_name = (world.get("world_core", {}) or {}).get("name", "the realm")
    location_name = (world.get("startingLocation", {}) or {}).get("name", "a town")

    setting = setting or {}
    era = (setting.get("era") or "").strip()
    factions = setting.get("factions") or []
    events = setting.get("recent_events") or []
    tension = (setting.get("current_tension") or "").strip()

    personality = _extract_personality(character)
    ideal = personality["ideal"]
    bond = personality["bond"]

    class_key = "adventurer"
    class_name = "adventurer"
    bg_name = "drifter"
    if character:
        cls = character.get("class") or character.get("class_") or {}
        class_key = (cls.get("key") or "adventurer").lower()
        class_name = _format_title(class_key)
        bg_name = _format_title((character.get("background") or {}).get("key", "drifter"))

    fallback = (
        f"The {realm_name} sits at a crossroads of trade and trouble. "
        f"{era or 'The age is one of unsteady alliances and uneasy peace.'} "
        f"Power is divided: {', '.join(f.get('name', '') for f in factions[:3] if f.get('name')) or 'rival factions'} "
        "hold sway in different quarters, each pulling the realm in their own direction. "
        f"{(events[0].get('summary') if events and events[0].get('summary') else 'Recent troubles have left the common folk wary.')} "
        f"{tension or 'The streets feel watched; small loyalties matter more than grand titles right now.'} "
        f"And it is to {location_name} that our story turns."
    )

    try:
        from services.claude_client import call_haiku_async

        faction_lines = "\n".join(
            f"- {f.get('name','')}: {f.get('domain','')}; {f.get('stance','')}"
            for f in factions[:3] if f.get("name")
        ) or "(none provided — invent two plausible powers in conflict)"
        event_lines = "\n".join(
            f"- {e.get('title','')}: {e.get('summary','')}"
            for e in events[:2] if e.get("title")
        ) or "(none provided — invent one recent event that produced the current tension)"

        prompt = (
            "Write the WORLD STATE TEXT for the opening of a D&D 5e campaign.\n\n"
            "This is the MACRO VIEW — the lay of the land and powers at play before the "
            "camera zooms onto the protagonist. Think of the Lord of the Rings prologue: "
            "you are establishing what the world IS, what is broken in it, and who holds the "
            "pieces. The hero does not appear here.\n\n"
            "This text will be immediately followed by an arrival narration that zooms into "
            f"{location_name} with the protagonist present. Your final sentence must tilt the "
            f"camera toward {location_name} so the transition feels like a continuous zoom.\n\n"
            "=== THE WORLD ===\n"
            f"Realm: {realm_name}\n"
            f"Starting location: {location_name}\n"
            f"Tone: {intent.tone} | Focus: {intent.focus} | Scope: {intent.scope}\n"
            f"Era: {era or '(establish one)'}\n\n"
            "=== POWERS AT PLAY ===\n"
            f"{faction_lines}\n\n"
            "=== RECENT EVENTS ===\n"
            f"{event_lines}\n\n"
            "=== CURRENT TENSION ===\n"
            f"{tension or '(establish one that fits the tone)'}\n\n"
            "=== THIS CHARACTER'S STAKE (do NOT mention the character — use this to make "
            "the wound specific to what a person with these values would care about) ===\n"
            f"Class: {class_name} | Background: {bg_name}\n"
            f"Ideal: {ideal or '(none — write a wound that any person could care about)'}\n"
            f"Bond destination: {location_name} — "
            f"{bond or '(someone or something in this place)'}\n\n"
            "=== THREE-PART STRUCTURE — FOLLOW EXACTLY ===\n\n"
            "PART 1 — Geography as stage (2-3 sentences):\n"
            "Not a map. The terrain, the resources, the economy — as the physical reality the "
            "struggle is playing out on. What this land produces, who depends on it, what moves "
            "through it. Ground the reader in a specific place with weight and texture.\n\n"
            "PART 2 — The wound operating (2-3 sentences):\n"
            "Who holds power and what it costs everyone else — shown through the mechanism, "
            "not named as injustice. Name the specific instrument: the tax, the licensing law, "
            "the debt contract, the conscription order. Show it operating normally, not "
            "dramatically. The most effective wound is the kind no one bothers to protest "
            "because it has become the weather. The reader should feel the stakes without "
            "being told what they are.\n\n"
            "PART 3 — The camera tilts (1 sentence):\n"
            f"A single transitional sentence pointing at {location_name}. This closes the "
            "macro view and begins the zoom toward the arrival narration. "
            f"Pattern: 'It is to [location], on [time/condition], that this story turns.' "
            "Vary the phrasing. Use the exact location name.\n\n"
            "=== RULES ===\n"
            "- Third-person omniscient. The hero does NOT appear.\n"
            "- 120-160 words. One paragraph.\n"
            f"- Match tone: {intent.tone}. Gritty = scarcity, exhausted institutions, "
            "working-class texture. Heroic = real stakes but not hopeless. "
            "Mystery = what is unsaid matters as much as what is said.\n"
            "- The wound is shown through its effect on ordinary life — not stated as "
            "'the stakes are' or 'injustice reigns.' Show the mechanism; let the reader "
            "feel the consequence.\n"
            "- One concrete sensory detail allowed (a color, a sound, a smell).\n"
            "- Short declarative sentences land harder than complex ones.\n"
            "- BANNED: 'once upon a time', 'in a land far away', 'legends speak', "
            "'ancient prophecy', 'chosen one', 'dark lord', 'destiny', 'in a world', "
            "'the stakes are', 'injustice', 'evil forces'.\n"
            "- No headings, no quotes around the passage, no OOC.\n"
            "Output ONLY the paragraph."
        )

        response = await call_haiku_async(
            "You are a world-state narrator opening a D&D campaign. You establish the lay of "
            "the land and the powers at play by showing the wound in the world — not through "
            "exposition but through the mechanism of power operating on ordinary life. "
            "You write like the Lord of the Rings prologue: grounded, specific, ending with "
            "the camera beginning its zoom toward where the story starts.",
            prompt,
            max_tokens=400,
            temperature=0.3,
        )
        text = (response or "").strip()
        if text.startswith('"') and text.endswith('"') and len(text) > 2:
            text = text[1:-1].strip()
        return text or fallback
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"World brief generation failed, using template: {exc}")
        return fallback



async def build_starting_scene_with_ai(
    campaign_id: str,
    world: Dict,
    intent: CampaignIntent,
    character: Optional[Dict],
    active_quest: Optional[Dict] = None,
    setting: Optional[Dict] = None,
) -> Dict:
    """Produce a cinematic second-person campaign intro using the LLM.
    Falls back to the template intro on any failure.
    `active_quest` (optional): a dict with `title`, `description` — the opening
    quest card that should be planted as the concrete hook in the intro.
    `setting` (optional): a dict with `era`, `factions`, `recent_events`,
    `current_tension` — the world's situation that should ground the player
    BEFORE the personal scene zooms in.
    """
    fallback = build_starting_scene(campaign_id, world)
    try:
        from services.claude_client import call_haiku_async

        starting_location = world.get("startingLocation", {})
        location_name = starting_location.get("name", "the starting point")
        location_desc = starting_location.get("description", "")

        # Collect hero details
        name = "the adventurer"
        race_name = "human"
        class_name = "adventurer"
        class_key = "adventurer"
        bg_name = "drifter"
        appearance_bits: List[str] = []
        age_category = ""
        sex = ""
        ideal = ""
        bond = ""
        flaw = ""

        if character:
            identity = character.get("identity") or {}
            race = character.get("race") or {}
            class_info = character.get("class") or character.get("class_") or {}
            bg = character.get("background") or {}
            appearance = character.get("appearance") or {}
            name = identity.get("name") or name
            sex = identity.get("sex") or ""
            race_name = _format_title(race.get("key", "human"))
            class_key = (class_info.get("key") or "adventurer").lower()
            class_name = _format_title(class_key)
            bg_name = _format_title(bg.get("key", "drifter"))
            age_category = appearance.get("ageCategory") or ""
            build = appearance.get("build") or ""
            hair = appearance.get("hairColor") or ""
            hair_style = appearance.get("hairStyle") or ""
            facial_hair = appearance.get("facialHair") or ""
            eyes = appearance.get("eyeColor") or ""
            notable = appearance.get("notableFeatures") or []
            if build:
                appearance_bits.append(f"{build} build")
            hair_phrase = " ".join(filter(None, [hair_style, hair])).strip()
            if hair_phrase:
                appearance_bits.append(f"{hair_phrase} hair")
            if facial_hair:
                appearance_bits.append(f"{facial_hair} facial hair")
            if eyes:
                appearance_bits.append(f"{eyes} eyes")
            if notable:
                appearance_bits.append("notable: " + ", ".join(notable[:3]))
        # Use _extract_personality to handle both V2 and legacy character formats
        _p = _extract_personality(character)
        ideal = _p["ideal"]
        bond = _p["bond"]
        flaw = _p["flaw"]

        class_flavor = _CLASS_FLAVOR.get(class_key, _CLASS_FLAVOR["_default"])
        appearance_line = "; ".join(appearance_bits) if appearance_bits else "unremarkable at first glance"
        hero_header = f"{name} — a {age_category or 'adult'} {sex or ''} {race_name} {class_name}, {bg_name} background".replace("  ", " ").strip()

        # Active quest hook (the opening lead). When present, the intro MUST
        # plant this concretely so the ending choices tie back to it.
        quest_title = ""
        quest_desc = ""
        quest_scene_hook = ""
        if active_quest:
            quest_title = (active_quest.get("title") or "").strip()
            quest_desc = (active_quest.get("description") or "").strip()
            quest_scene_hook = (active_quest.get("scene_hook") or "").strip()
        has_quest = bool(quest_title and quest_desc)
        quest_block = (
            f"- Title: {quest_title}\n"
            f"- Description: {quest_desc}\n"
            f"- Scene hook (embed this detail naturally in the scene — do NOT label it): "
            f"{quest_scene_hook or '(derive from the bond destination and world setting)'}"
            if has_quest
            else "- (no opening lead — embed one subtle scene detail tied to the bond and world wound)"
        )

        # Setting block: the world's actual situation (era, factions, recent
        # events, current tension). The intro MUST use these as ground truth
        # so the player feels they're stepping into a real place with real
        # history — not a generic fantasy backdrop.
        setting_lines: List[str] = []
        if setting:
            era = (setting.get("era") or "").strip()
            tension = (setting.get("current_tension") or "").strip()
            factions = setting.get("factions") or []
            events = setting.get("recent_events") or []
            if era:
                setting_lines.append(f"- Era: {era}")
            for f in factions[:3]:
                if not f.get("name"):
                    continue
                detail = "; ".join(p for p in [f.get("domain"), f.get("stance")] if p)
                setting_lines.append(f"- Faction — {f['name']}: {detail}")
            for e in events[:2]:
                if not e.get("title"):
                    continue
                setting_lines.append(f"- Recent event — {e['title']}: {e.get('summary', '')}")
            if tension:
                setting_lines.append(f"- Current tension: {tension}")
        setting_block = "\n".join(setting_lines) if setting_lines else "(no setting context provided)"

        system_message = (
            "You are the opening narrator of a D&D 5e campaign. You pick up where the "
            "world-state text left off — the macro view has zoomed to the starting location "
            "and now the protagonist is present. Your job is to land the camera at street "
            "level, show the character arriving with a reason, and describe a scene where "
            "the world's wound is visible in the details. You do not tell the player what "
            "to do. You do not label what is interesting. You trust the player's eye. "
            "The scene happens around the still protagonist — they arrived, they are here, "
            "the world is moving. Hand agency back with a closing window and a single question."
        )

        prompt = (
            "Write the ARRIVAL NARRATION — the second opening text of a D&D 5e campaign.\n\n"
            "The world-state text has just established the macro view and ended by pointing "
            f"at {location_name}. This narration picks up that zoom and lands inside it. "
            "The protagonist is now present. The world's wound from the first text is "
            "visible here at street level.\n\n"
            "=== CAMPAIGN ===\n"
            f"Tone: {intent.tone} | Focus: {intent.focus} | Scope: {intent.scope} | Danger: {intent.danger}\n\n"
            "=== LOCATION ===\n"
            f"{location_name} — {location_desc}\n\n"
            "=== THE PROTAGONIST ===\n"
            f"{hero_header}\n"
            f"Appearance cues (surface only — never describe their face from outside): {appearance_line}\n"
            f"Class lens (subtle coloring — how they read the world): {class_flavor}\n"
            f"Bond — THIS IS WHY THEY ARE HERE: {bond or '(none set — invent a concrete specific reason tied to this location)'}\n"
            f"Ideal: {ideal or '(none set)'}\n"
            f"Flaw: {flaw or '(none set)'}\n\n"
            "=== THE QUEST HOOK (this is what the bond leads them toward — embed it naturally in the scene) ===\n"
            f"{quest_block}\n\n"
            "=== WORLD SETTING (what the wound looks like from street level) ===\n"
            f"{setting_block}\n\n"
            "=== FOUR BEATS — FOLLOW THIS STRUCTURE EXACTLY ===\n\n"
            "BEAT 1 — ARRIVAL WITH REASON (1-2 sentences):\n"
            "The bond brought them here. Name the specific destination — the address, the "
            "building, the institution the bond points toward. One sensory detail specific "
            "to this place at this moment. Reference the hero by name once. "
            "The protagonist is still — arrived, standing, looking. They do not move yet.\n\n"
            "BEAT 2 — WHAT IS WRONG (1 sentence):\n"
            "Something at or near the bond destination is not what it should be. "
            "Describe it exactly as a visible fact — no interpretation, no 'something seems off.' "
            "Show the thing. Let the player's brain supply the meaning. "
            "Define by negation if it helps: the thing that should be there and isn't, "
            "or the thing that is there and shouldn't be. "
            "This detail must be specific to the world's wound and this character's bond.\n\n"
            "BEAT 3 — THE WORLD MOVING (2-3 sentences):\n"
            "Two things happening in the scene simultaneously. "
            "At least one is a person doing something with an unclear purpose. "
            "At least one connects visibly to the world's wound from the first text. "
            "Do NOT label these as significant. Do NOT say 'you notice' or 'you see' or "
            "'three things draw the eye.' Just describe what is there, doing what it is doing. "
            "The player's brain will find them. These are open loops — the player will want "
            "to investigate. Investigating one closes it and opens the next. "
            "Do not resolve any of them.\n\n"
            "BEAT 4 — THE CLOSING WINDOW (1 sentence, then line break, then the question):\n"
            "One short sentence that makes one of the loops time-sensitive. Something is "
            "about to be gone — a person reaching a corner, a door starting to close, "
            "a moment about to resolve without the player. Specific. Present tense. "
            "No explanation. Then a line break. Then on its own line: What do you do?\n\n"
            "=== ABSOLUTE RULES ===\n"
            "1. Second-person present tense throughout.\n"
            "2. NEVER narrate what the protagonist thinks, feels, decides, or does. "
            "Forbidden: 'you notice', 'you see', 'you feel', 'you sense', 'your eyes', "
            "'you realize', 'you wonder', 'you scan', 'you decide', 'you step'.\n"
            "3. NPCs are posture and motion before face and name — 'a woman crossing fast' "
            "before any name or face detail.\n"
            "4. Hooks are in the description. NEVER label them. No 'three things draw the eye', "
            "no 'stands out', no 'catches your attention'. Describe the scene; let the player hunt.\n"
            "5. ONE simile maximum across the entire passage. Prefer none.\n"
            "6. 'What do you do?' stands on its own line after a line break. Never embellish it.\n"
            "7. The opening should feel like a continuous zoom from the world-state text — "
            f"reference the same landmark or street that text used to point toward {location_name}.\n\n"
            f"=== TONE ===\n"
            f"Gritty: short sentences, cold details, working-class textures (smoke, lamp oil, worn stone).\n"
            f"Heroic: specific physical detail, space and light, but never saccharine.\n"
            f"Mystery: what is OUT of place matters most — a silence that shouldn't be there.\n"
            f"Match tone '{intent.tone}' without naming it.\n\n"
            "=== BANNED PHRASES ===\n"
            "'a chill runs down your spine', 'destiny', 'the adventure begins', "
            "'little did you know', 'weighs on your soul', 'stirs something inside you', "
            "'you can't shake the feeling', 'something is wrong', 'three things draw the eye', "
            "'stands out', 'catches your attention', 'mysterious stranger', 'ye olde'.\n\n"
            "=== LENGTH ===\n"
            "6-9 sentences across beats 1-4. Beat 4 ends with 'What do you do?' on its own line.\n"
            "Mix sentence lengths — short sentences land harder than long ones.\n\n"
            "Output ONLY the narration. No headings. No explanation."
        )

        response = await call_haiku_async(
            system_message,
            prompt,
            max_tokens=500,
            temperature=0.7,
        )
        text = (response or "").strip()
        # Strip accidental wrapping quotes if the model added them
        if text.startswith('"') and text.endswith('"') and len(text) > 2:
            text = text[1:-1].strip()
        if text:
            return {"seed": f"scene_{campaign_id[:8]}", "introText": text}
        logger.warning("AI intro returned empty text; using template fallback")
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"AI intro generation failed, using template fallback: {exc}")
    return fallback


def generate_initial_cards(campaign_id: str, intent: CampaignIntent, world: Dict, character: Dict | None) -> List[KnowledgeCard]:
    """Generate the non-quest seed cards. The opening quest card is produced
    separately (async) by `generate_opening_quest_card_with_ai` so it can be
    properly personalized by the LLM.
    """
    starting_location = world.get("startingLocation", {})
    race_name = _format_title(character.get("race", {}).get("key", "traveler")) if character else "traveler"
    background_name = _format_title(character.get("background", {}).get("key", "wanderer")) if character else "wanderer"

    cards: List[KnowledgeCard] = [
        KnowledgeCard(
            id=str(uuid4()),
            type="place",
            title=starting_location.get("name", "Starting Point"),
            description=starting_location.get(
                "description",
                "The place where your journey begins, shaped by your chosen tone and scope.",
            ),
            tags=[intent.scope.lower(), "starting-location"],
        ),
        KnowledgeCard(
            id=str(uuid4()),
            type="npc",
            title="Local Steward",
            description=(
                "A pragmatic contact assigned to greet new arrivals and keep order. "
                f"They appreciate {intent.focus.lower()}-driven heroes."
            ),
            tags=["contact", intent.focus.lower()],
        ),
        KnowledgeCard(
            id=str(uuid4()),
            type="belief",
            title="Cultural Thread",
            description=(
                f"Stories of {race_name} traditions blend with your {background_name} upbringing, "
                "creating shared expectations about honor and duty."
            ),
            tags=[race_name.lower(), background_name.lower()],
        ),
    ]

    return cards


def _template_opening_quest(intent: CampaignIntent, world: Dict, character: Dict | None) -> KnowledgeCard:
    """Deterministic fallback used when the LLM is unavailable."""
    starting_location = world.get("startingLocation", {})
    class_name = _format_title((character.get("class", {}) or character.get("class_", {})).get("key", "adventurer")) if character else "adventurer"
    return KnowledgeCard(
        id=str(uuid4()),
        type="quest",
        title="Opening Lead",
        description=(
            f"Rumors speak of a task suited for a {class_name}: safeguard the {starting_location.get('name', 'outpost')} "
            f"as tension rises ({intent.danger.lower()} danger)."
        ),
        tags=["quest", intent.danger.lower(), "opening"],
        status="active",
    )


async def generate_opening_quest_card_with_ai(
    intent: CampaignIntent,
    world: Dict,
    character: Optional[Dict],
) -> KnowledgeCard:
    """Produce a juicy, campaign-specific opening quest card via the LLM.
    Falls back to the deterministic template on any failure.
    """
    fallback = _template_opening_quest(intent, world, character)
    try:
        import json as _json
        from services.claude_client import call_haiku_async

        starting = world.get("startingLocation", {})
        location_name = starting.get("name", "the starting area")
        class_key = "adventurer"
        bg_key = "wanderer"
        hero_name = "the hero"
        if character:
            identity = character.get("identity") or {}
            hero_name = identity.get("name") or hero_name
            cls = character.get("class") or character.get("class_") or {}
            class_key = (cls.get("key") or "adventurer").lower()
            bg_key = ((character.get("background") or {}).get("key") or "wanderer").lower()

        class_flavor = _CLASS_FLAVOR.get(class_key, _CLASS_FLAVOR["_default"])

        personality = _extract_personality(character)
        ideal = personality["ideal"]
        bond = personality["bond"]
        flaw = personality["flaw"]

        prompt = (
            "Design the OPENING QUEST for a D&D 5e campaign.\n\n"
            "A quest is a chain of questions, not a task. Each answer reveals the world's "
            "wound more completely. The title is a question. The first thread is something "
            "the player can see in the arrival scene. Investigating it closes one loop and "
            "opens the next — and the next answer is always worse (and more interesting) "
            "than the surface.\n\n"
            "=== CAMPAIGN ===\n"
            f"Tone: {intent.tone} | Focus: {intent.focus} | Scope: {intent.scope} | Danger: {intent.danger}\n"
            f"Starting location: {location_name} — {starting.get('description', '')}\n\n"
            "=== HERO ===\n"
            f"{hero_name} ({_format_title(class_key)}, {_format_title(bg_key)} background)\n"
            f"Class: what NPCs see and ask for — {class_flavor}\n"
            f"Bond (why they are here): {bond or '(none set — invent one tied to this location)'}\n"
            f"Ideal (what the world must oppose): {ideal or '(none set)'}\n"
            f"Flaw: {flaw or '(none set)'}\n\n"
            "=== QUEST DESIGN RULES ===\n"
            "1. TITLE: a question, 3-5 words. Not a task ('Find the missing priest') — "
            "a question ('Where Is Father Aldric?'). The player's brain starts predicting "
            "the answer immediately.\n\n"
            "2. DESCRIPTION: 2 sentences maximum.\n"
            "   Sentence 1: The scene-visible surface hook — something the player can see "
            "or find in the arrival narration (a notice on a door, a person moving fast, "
            "a building with the wrong sign). Name the specific thing. Root it in the bond "
            "destination.\n"
            "   Sentence 2: The first thread — the specific action the player takes to "
            "start pulling (ask the person at the garrison office, go into the alley after "
            "the woman, read the notice on the door). Concrete. Achievable immediately.\n\n"
            "3. SCENE_HOOK: one short phrase — the literal thing visible in the arrival "
            "scene that connects to this quest. This exact phrase (or close to it) should "
            "appear naturally in the arrival narration. Keep it under 10 words. "
            "Example: 'a licensing notice nailed to a stripped door'\n\n"
            "4. WOUND LAYERS (for context — not shown to player, used by DM to generate "
            "consistent follow-up):\n"
            "   Layer 1 (surface): what the player finds when they pull the first thread.\n"
            "   Layer 2 (mechanism): what that reveals about HOW the world's wound works.\n"
            "   Layer 3 (structure): what the mechanism reveals about WHO benefits and WHY "
            "it persists.\n"
            "The wound layers should escalate — each one is more systemic than the last, "
            "and harder to fight than the one before.\n\n"
            "5. No clichés: no 'mysterious stranger', 'ancient prophecy', 'chosen one', "
            "'dark lord', 'a tavern brawl'.\n"
            "6. Level-1 appropriate: no epic threats. The first thread is something a "
            "single person can investigate on foot in one afternoon.\n\n"
            "=== OUTPUT (strict JSON, no prose, no code fence) ===\n"
            "{\n"
            "  \"title\": \"Question-form title, 3-5 words, ends with ?\",\n"
            "  \"description\": \"2 sentences: scene-visible hook + immediate first thread. <=300 chars.\",\n"
            "  \"scene_hook\": \"the specific visible thing in the arrival scene, <10 words\",\n"
            "  \"wound_layers\": {\n"
            "    \"surface\": \"what the first thread reveals\",\n"
            "    \"mechanism\": \"how the system works\",\n"
            "    \"structure\": \"who benefits and why it persists\"\n"
            "  },\n"
            "  \"tags\": [\"2-4 lowercase tags\"]\n"
            "}\n"
        )

        raw = await call_haiku_async(
            "You are a senior D&D campaign designer. You build opening quests as chains of "
            "questions — each answer reveals the world's wound more completely. "
            "The title is a question. The first thread is visible in the arrival scene. "
            "Output strict JSON only.",
            prompt,
            max_tokens=500,
            temperature=0.5,
        ) or ""

        # Best-effort JSON extraction (strip code fences if the model ignored the instruction)
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            # drop a leading 'json' language tag if present
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        try:
            data = _json.loads(text)
        except Exception:
            # Try to locate the first {...} block
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end > start:
                data = _json.loads(text[start : end + 1])
            else:
                raise

        title = str(data.get("title") or "").strip() or fallback.title
        description = str(data.get("description") or "").strip() or fallback.description
        scene_hook = str(data.get("scene_hook") or "").strip()
        wound_layers = data.get("wound_layers") or {}
        tags = data.get("tags") or []
        if not isinstance(tags, list):
            tags = []
        tags = [str(t).strip().lower() for t in tags if t]
        # Always include an 'opening' tag so the UI/DM can find THE active lead
        if "opening" not in tags:
            tags = [*tags, "opening"]
        if "quest" not in tags:
            tags = [*tags, "quest"]
        if len(description) > 360:
            description = description[:360].rstrip() + "…"

        # Build metadata block for DM context (not shown to player directly)
        metadata: dict = {}
        if scene_hook:
            metadata["scene_hook"] = scene_hook
        if wound_layers and isinstance(wound_layers, dict):
            metadata["wound_layers"] = wound_layers

        card = KnowledgeCard(
            id=str(uuid4()),
            type="quest",
            title=title[:80],
            description=description,
            tags=tags[:6],
            status="active",
        )
        # Attach metadata if the model supports extra fields
        if metadata:
            try:
                object.__setattr__(card, "metadata", metadata)
            except Exception:
                pass
        return card
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"AI opening quest generation failed, using template: {exc}")
        return fallback
