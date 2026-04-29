from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4
import logging

from models.campaign_models import CampaignIntent, KnowledgeCard

logger = logging.getLogger(__name__)


def _format_title(text: str) -> str:
    return text.replace("_", " ").title()


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
        import os
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return fallback

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

        chat = LlmChat(
            api_key=api_key,
            session_id=f"campaign-setting-{uuid4()}",
            system_message=(
                "You are a senior D&D worldbuilder. You produce specific, grounded setting bibles "
                "with factions in real conflict and recent events that shape the day. Output strict JSON only."
            ),
        )
        chat.with_model("openai", "gpt-4o-mini")
        raw = (await chat.send_message(UserMessage(text=prompt))) or ""

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
    """Macro-zoom narration: geography, history, political climate, cultures,
    powers at play. Read like a chronicler's preface — the lay of the land
    BEFORE the camera zooms onto the hero. Falls back to a coherent template.
    """
    realm_name = (world.get("world_core", {}) or {}).get("name", "the realm")
    location_name = (world.get("startingLocation", {}) or {}).get("name", "a town")

    setting = setting or {}
    era = (setting.get("era") or "").strip()
    factions = setting.get("factions") or []
    events = setting.get("recent_events") or []
    tension = (setting.get("current_tension") or "").strip()

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
        import os
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return fallback

        faction_lines = "\n".join(
            f"- {f.get('name','')}: {f.get('domain','')}; {f.get('stance','')}"
            for f in factions[:3] if f.get("name")
        ) or "(none provided — invent two plausible powers)"
        event_lines = "\n".join(
            f"- {e.get('title','')}: {e.get('summary','')}"
            for e in events[:2] if e.get("title")
        ) or "(none provided)"

        prompt = (
            "Write a CHRONICLER'S PREFACE for the start of a Dungeons & Dragons 5e campaign. "
            "This is the MACRO view — the lay of the land BEFORE the camera zooms onto the hero. "
            "It will be displayed as a separate opening text, then a second narration zooms into "
            "the hero's specific arrival.\n\n"
            "=== REALM ===\n"
            f"Name: {realm_name}\n"
            f"Tone: {intent.tone} | Focus: {intent.focus} | Scope: {intent.scope}\n"
            f"Era: {era or '(unspecified — establish one)'}\n\n"
            "=== POWERS AT PLAY ===\n"
            f"{faction_lines}\n\n"
            "=== RECENT EVENTS ===\n"
            f"{event_lines}\n\n"
            "=== CURRENT TENSION ===\n"
            f"{tension or '(unspecified)'}\n\n"
            f"=== THE STORY TURNS TO === \n{location_name}\n\n"
            "=== STYLE ===\n"
            "- 130-180 words, ONE paragraph, third-person omniscient (a chronicler's voice).\n"
            "- Cover four things briefly, in order: (1) GEOGRAPHY — where this realm sits, its terrain, "
            "key neighbors; (2) RECENT HISTORY — the recent events compressed into one sentence of cause "
            "and effect; (3) POLITICAL CLIMATE — who holds power, who opposes them, the current balance; "
            "(4) CULTURE — one specific custom or texture of daily life that distinguishes this realm.\n"
            "- ONE concrete sensory detail allowed (a banner color, a dialect phrase, the sound of a "
            "particular bell). One simile maximum. No purple prose.\n"
            f"- Match the campaign tone ({intent.tone}). Gritty = scarcity, tired institutions, "
            "wariness; Heroic = banners returning, hopeful but uncertain; Mystery = secrets, secretive "
            "guilds, things unsaid in public.\n"
            "- Do NOT mention or address the hero. The hero does not yet enter the scene.\n"
            f"- End with EXACTLY ONE short transitional sentence that tilts the camera toward {location_name}, "
            f"e.g., \"And it is to {location_name}, on this evening, that our story turns.\" Do not invent a "
            "new transitional location.\n"
            "- HARD-BAN PHRASES: \"once upon a time\", \"in a land far away\", \"legends speak\", "
            "\"ancient prophecy\", \"chosen one\", \"dark lord\", \"destiny\", \"in a world\".\n"
            "- No headings, no quotes around the passage, no OOC. Output ONLY the chronicle paragraph."
        )

        chat = LlmChat(
            api_key=api_key,
            session_id=f"world-brief-{uuid4()}",
            system_message=(
                "You are a chronicler of fantasy realms in the tradition of Tolkien's prologues "
                "and Critical Role's opening world primers — concise, grounded, specific. "
                "You compress history, geography, politics, and culture into a single tight paragraph."
            ),
        )
        chat.with_model("openai", "gpt-4o-mini")

        response = await chat.send_message(UserMessage(text=prompt))
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
        import os
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("No LLM key for intro generation; using fallback")
            return fallback

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
            eyes = appearance.get("eyeColor") or ""
            notable = appearance.get("notableFeatures") or []
            if build:
                appearance_bits.append(f"{build} build")
            if hair:
                appearance_bits.append(f"{hair} hair")
            if eyes:
                appearance_bits.append(f"{eyes} eyes")
            if notable:
                appearance_bits.append("notable: " + ", ".join(notable[:3]))
            personality = bg.get("personality") or {}
            ideal = (personality.get("ideal") or "").strip()
            bond = (personality.get("bond") or "").strip()
            flaw = (personality.get("flaw") or "").strip()

        class_flavor = _CLASS_FLAVOR.get(class_key, _CLASS_FLAVOR["_default"])
        appearance_line = "; ".join(appearance_bits) if appearance_bits else "unremarkable at first glance"
        hero_header = f"{name} — a {age_category or 'adult'} {sex or ''} {race_name} {class_name}, {bg_name} background".replace("  ", " ").strip()

        personality_lines: List[str] = []
        if ideal:
            personality_lines.append(f"- Ideal: {ideal}")
        if bond:
            personality_lines.append(f"- Bond: {bond}")
        if flaw:
            personality_lines.append(f"- Flaw: {flaw}")
        personality_block = "\n".join(personality_lines) if personality_lines else "- (no personality hooks set)"

        # Active quest hook (the opening lead). When present, the intro MUST
        # plant this concretely so the ending choices tie back to it.
        quest_title = ""
        quest_desc = ""
        if active_quest:
            quest_title = (active_quest.get("title") or "").strip()
            quest_desc = (active_quest.get("description") or "").strip()
        has_quest = bool(quest_title and quest_desc)
        quest_block = (
            f"- Title: {quest_title}\n- Details: {quest_desc}"
            if has_quest
            else "- (no opening lead set; invent a subtle hook aligned with the campaign focus)"
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
            "You are a master Dungeons & Dragons 5e storyteller in the tradition of "
            "Matthew Mercer: cinematic but restrained, grounded in concrete sensory "
            "detail, never melodramatic. You set scenes that HAPPEN AROUND the hero "
            "while the hero is still — never telling the player what their character "
            "thinks, perceives, decides, or does. The player owns those choices. "
            "Your job is to make a place feel real and hand agency back."
        )

        prompt = (
            "Write the OPENING narration of a new D&D 5e campaign in the style of "
            "Matthew Mercer (Critical Role): cinematic, grounded, restrained.\n\n"
            "=== CAMPAIGN ===\n"
            f"Tone: {intent.tone} | Focus: {intent.focus} | Scope: {intent.scope} | Danger: {intent.danger}\n"
            f"World theme: {world.get('theme', 'mixed')} | World tone: {world.get('tone', 'mixed')}\n\n"
            "=== LOCATION (use this exact name; do NOT invent a different place) ===\n"
            f"{location_name} — {location_desc}\n\n"
            "=== HERO (the player controls them — you do NOT) ===\n"
            f"{hero_header}\n"
            f"Appearance cues: {appearance_line}\n"
            f"Class flavor (subtle, optional): {class_flavor}\n"
            "Personality hooks (may color how an NPC reacts to them — never quote, "
            "never narrate the hero's inner monologue):\n"
            f"{personality_block}\n\n"
            "=== ACTIVE OPENING LEAD (plant as a fact in the world; do NOT hijack the hero into investigating it) ===\n"
            f"{quest_block}\n\n"
            "=== WORLD SETTING (ground truth — the player must feel they're in this specific world, not generic fantasy) ===\n"
            f"{setting_block}\n\n"
            "=== MERCER STYLE — STRICT ===\n"
            "0) STRUCTURE (Mercer's character-arrival opening, two beats):\n"
            "   • BEAT ONE — ARRIVAL CONTEXT (1-2 sentences): explain WHY this specific hero is in "
            "this specific place RIGHT NOW. Anchor it in the hero's BACKGROUND (a soldier mustered out "
            "with last pay; an entertainer on a circuit between towns; an outlander drawn by a market "
            "rumor; an acolyte sent on an errand by their order; a criminal lying low after a job), "
            "their RACE (an elf far from the deep woods, a dwarf among humans, a halfling slipping "
            "between knees) and their PERSONALITY HOOKS if any (the bond pulls them here, the flaw "
            "got them here). One concrete who-or-what brought them — a writ, a coin, a letter, a "
            "rumor, a debt, a pilgrimage — keep it specific. Reference the hero by name once.\n"
            "   • BEAT TWO — STATIC SCENE (3-4 sentences): now describe the immediate place around "
            "the still hero — weather, light, time of day, sound, smell, texture. Plant the active "
            "opening lead as an observable fact in this specific moment. Do NOT repeat material from "
            "the world brief.\n"
            "1) STATIC SCENE. The hero is still — arrived, standing, sitting, watching. "
            "The scene HAPPENS AROUND them after the arrival is established. Show the place: weather, "
            "light, time of day, a sound, a smell, one specific texture.\n"
            "2) NEVER narrate what the hero DOES. Forbidden patterns: \"you scan\", \"you step\", "
            "\"you reach\", \"you decide\", \"you wonder\", \"you feel\" (followed by an emotion), "
            "\"your eyes\" (eyes are a perception verb in disguise), \"your hand moves\", "
            "\"you draw\", \"you turn\", \"you smile\", \"you nod\". The PLAYER decides actions.\n"
            "3) NEVER narrate what the hero THINKS or PERCEIVES as inner state. The narrator does not "
            "have access to their head. No rhetorical questions to the hero (\"What better place...?\"). "
            "No \"thoughts\", no \"in the back of your mind\", no \"a part of you...\".\n"
            "4) ONE simile MAXIMUM in the entire passage. Prefer none. NEVER chain similes "
            "(\"like X, like Y, like Z\"). Cut metaphor density by 80% from a typical AI default.\n"
            "5) NPCs appear as silhouettes / voices / postures — \"a hooded figure at the well\", "
            "\"a man's frantic voice\", \"a watchman thumbing the hilt of his sword\". Do NOT name "
            "anyone unless the lead already named them. Description first, name later.\n"
            "6) TIME, WEATHER, LIGHT carry mood. \"Late afternoon. The market is winding down.\" "
            "Beats \"a heavy weight settles over the square\" every time.\n"
            "7) TONE-MATCHED PROSE.\n"
            f"   • Gritty/Grim: short sentences, cold details, working-class smells (smoke, sweat, lamp oil).\n"
            f"   • Heroic: open vistas, banners, a horn in the distance, but never saccharine.\n"
            f"   • Mystery: emphasize what is OUT of place — a closed door at midday, a quiet that shouldn't be quiet.\n"
            f"   Match the campaign tone ({intent.tone}) without naming it.\n"
            "8) APPEARANCE may surface ONLY through (a) physical sensation the hero would feel "
            "(weight of armor, cool of a bracer), (b) a reflection they actually see, or "
            "(c) another character reacting to them. NEVER describe the hero's own face or build "
            "from outside.\n"
            "9) HARD-BAN PHRASES: \"a chill runs down your spine\", \"destiny awaits\", \"the adventure begins\", "
            "\"little did you know\", \"a mysterious stranger\", \"feels personal\", \"pulls at you\", "
            "\"tugs at your heart\", \"weighs on your soul\", \"stirs something deep\", \"swirl like autumn leaves\", "
            "\"like fingers across\", \"gleam and promise fortune\", \"ye olde\".\n"
            "10) Use the location name once naturally. Reference the hero's name once if it fits — never twice.\n\n"
            "=== LENGTH & FORM ===\n"
            "- 130-180 words, ONE paragraph, second-person present tense.\n"
            "- 5-8 sentences across both beats; mix sentence lengths (short, longer, short).\n"
            "- No headings, no quotes around the passage, no OOC, no stats.\n\n"
            "=== ENDING (Mercer's signature — hand agency back) ===\n"
            "End by presenting the WORLD'S facts, not the hero's autopilot. Choose one:\n"
            "  (A) State 2-3 concrete observable things that are present in THIS scene "
            "(unique to this location and lead — DO NOT reuse the example below). "
            "Phrase them as plain world-observations. Schematic example only: "
            "\"Three things draw the eye: <a specific door/window/figure>, <a specific "
            "movement or sound>, and <a specific person doing a specific thing>.\" "
            "Replace each placeholder with details true to THIS opening lead and place. "
            "Then nothing. Let the player choose.\n"
            "  (B) End with a single short, plain sentence handing it over: \"What do you do?\" "
            "Never embellish that line.\n"
            "Do NOT suggest specific actions phrased as the hero's choices (\"You can duck into...\"). "
            "List facts; the player invents the verb. NEVER reuse a previous reply's three facts.\n\n"
            "Output ONLY the narration paragraph."
        )

        chat = LlmChat(
            api_key=api_key,
            session_id=f"campaign-intro-{campaign_id}",
            system_message=system_message,
        )
        chat.with_model("openai", "gpt-4o-mini")

        response = await chat.send_message(UserMessage(text=prompt))
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
        import os
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return fallback

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

        prompt = (
            "Design a SPECIFIC, INTRIGUING opening quest hook for a Dungeons & Dragons 5e campaign. "
            "The player should see this on their Knowledge Deck the moment the campaign begins.\n\n"
            "=== CAMPAIGN ===\n"
            f"Tone: {intent.tone} | Focus: {intent.focus} | Scope: {intent.scope} | Danger: {intent.danger}\n"
            f"Starting location: {location_name} — {starting.get('description', '')}\n\n"
            "=== HERO ===\n"
            f"{hero_name} ({_format_title(class_key)}, {_format_title(bg_key)} background)\n"
            f"Class flavor: {class_flavor}\n\n"
            "=== REQUIREMENTS ===\n"
            f"- The hook MUST feel {intent.focus.lower()}-flavored (e.g., Political Intrigue → a sealed letter, a "
            "missing witness, a suspicious alliance; Exploration → unmapped ruin, trade route gone silent; "
            "Combat → raiders hitting caravans; Mystery → a body with no wound).\n"
            f"- It must be plausible for a level-1 hero to investigate; no epic-tier threats.\n"
            f"- It must anchor to {location_name} or a specific nearby place the player can reach on foot.\n"
            "- Give it TEETH: name a concrete first step the player can take (find X, meet Y at Z, inspect Q before dawn).\n"
            "- No clichés (\"mysterious stranger\", \"ancient prophecy\", \"chosen one\", \"a tavern\").\n"
            "- Do NOT name NPCs unless essential; if named, give them 1-2 vivid details.\n\n"
            "=== OUTPUT (strict JSON, no prose, no code fence) ===\n"
            "{\n"
            "  \"title\": \"Short evocative title, 3-6 words, no quotation marks\",\n"
            "  \"description\": \"1-3 sentences (<=280 chars) describing the hook + the concrete first step.\",\n"
            "  \"tags\": [\"2-4 lowercase tags, e.g. 'murder', 'dockside', 'political']\"\n"
            "}\n"
        )

        chat = LlmChat(
            api_key=api_key,
            session_id=f"campaign-opening-quest-{uuid4()}",
            system_message=(
                "You are a senior D&D campaign designer. You generate specific, grounded, player-ready "
                "quest hooks tailored to the campaign's tone, focus, and hero. Output strict JSON only."
            ),
        )
        chat.with_model("openai", "gpt-4o-mini")
        raw = (await chat.send_message(UserMessage(text=prompt))) or ""

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
        tags = data.get("tags") or []
        if not isinstance(tags, list):
            tags = []
        tags = [str(t).strip().lower() for t in tags if t]
        # Always include an 'opening' tag so the UI/DM can find THE active lead
        if "opening" not in tags:
            tags = [*tags, "opening"]
        if "quest" not in tags:
            tags = [*tags, "quest"]
        # Trim
        if len(description) > 360:
            description = description[:360].rstrip() + "…"

        return KnowledgeCard(
            id=str(uuid4()),
            type="quest",
            title=title[:80],
            description=description,
            tags=tags[:6],
            status="active",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"AI opening quest generation failed, using template: {exc}")
        return fallback
