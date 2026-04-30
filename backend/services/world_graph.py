"""World Graph generator — builds a node-graph of Regions for the campaign map.

Each region is a biome-themed node with:
  - coordinates (x, y) normalized 0..1 for SVG rendering
  - a deck of Event Cards (quest hooks) tied to its biome
  - connection edges to neighboring regions

Hybrid generation strategy:
  - ALL regions get name, biome, short description, hint
  - The STARTING region is fully hydrated with 5 full event cards
  - Neighbor regions ship with 2-3 hint teasers; on first visit we
    lazily expand them into full events via `hydrate_region`.

The generator uses the LLM for flavor when available, with a deterministic
fallback that still respects biome catalog / campaign intent / character.
"""
from __future__ import annotations

import json as _json
import logging
import math
import os
import random
from typing import Dict, List, Optional
from uuid import uuid4

from data.biomes import BIOMES, list_biome_keys
from models.campaign_models import CampaignIntent

logger = logging.getLogger(__name__)


# -------------------- deterministic fallback --------------------

_REGION_NAME_PARTS = {
    "forest": [("Whispering", "Wilds"), ("Ashen", "Grove"), ("Hollowroot", "Thicket"),
               ("Greenmoss", "Vale"), ("Elderwood", "Fringe")],
    "plains": [("Amber", "Flats"), ("Longwind", "March"), ("Sunbent", "Steppe"),
               ("Grainfield", "Basin"), ("Broken", "Meadow")],
    "desert": [("Copper", "Dunes"), ("Redsand", "Waste"), ("Bleached", "Reach"),
               ("Glassgale", "Expanse")],
    "mountain": [("Ironspine", "Peaks"), ("Frostbrow", "Range"), ("Ashfoot", "Heights"),
                 ("Stonebreak", "Ridge")],
    "swamp": [("Drowned", "Fen"), ("Peatbog", "Mire"), ("Gloomwater", "Marsh"),
              ("Willowrot", "Bog")],
    "coast": [("Saltmere", "Shore"), ("Tidebreak", "Coast"), ("Gulls", "Cape"),
              ("Driftspar", "Harbor")],
    "tundra": [("Pale", "Tundra"), ("Frostshorn", "Waste"), ("Northwind", "Expanse")],
    "underdark": [("Deepway", "Underhall"), ("Blackvein", "Caverns"), ("Umbral", "Reach")],
    "volcanic": [("Ember", "Caldera"), ("Cinderspire", "Reach"), ("Smolder", "Rift")],
    "urban": [("Old Quarter", ""), ("Lanternside", ""), ("Gatewalk", "Ward"),
              ("Coinmarket", "Ward")],
    "fey": [("Twinbloom", "Grove"), ("Moondrop", "Hollow"), ("Crownlace", "Meadow")],
    "shadow": [("Sorrow", "March"), ("Palemist", "Reach"), ("Blackveil", "Fringe")],
}

_EVENT_TEMPLATES = {
    "forest": [
        ("The Silent Grove", "Birdsong has vanished from a stretch of woods; something is driving them off."),
        ("The Charcoal Camp", "A burner's camp was abandoned mid-work. His tools lay untouched, the coals still warm."),
        ("The Antler Shrine", "Hunters report a ring of stag skulls piled at a crossroads that was empty a day ago."),
        ("Rootwalker Sign", "Treants have left claw-marks on the bark of old oaks — a warning no one understands."),
        ("Honey from Nowhere", "Wild honey combs are appearing in hollows that hold no bees."),
    ],
    "plains": [
        ("The Scattered Herd", "A rancher's bison broke through their fence at midnight; none have returned."),
        ("Caravan Silence", "The weekly caravan from the next town hasn't arrived; its beacon fires are dark."),
        ("Circling Hawks", "Hawks are circling a single point in the grass for the third day running."),
        ("Burned Mile", "A mile-long stretch of grass is scorched in a perfect line — no smoke, no fire seen."),
        ("The Lost Shepherd", "A shepherd girl's dog came home alone, dragging her cloak."),
    ],
    "desert": [
        ("The Dry Well", "A trading post's well ran dry overnight in a year of good rain."),
        ("Sandstep Song", "Nomads heard wordless singing from a dune that wasn't there the previous dawn."),
        ("The Glass Tear", "A pane of fused glass, desert-shaped, has appeared where nothing lived."),
        ("Scorpion Tide", "Scorpions are migrating in a straight line toward the horizon."),
        ("The Unmelted Snow", "A patch of ice persists through noon on open sand."),
    ],
    "mountain": [
        ("The Quiet Pass", "The goat track above town has stopped showing tracks — neither goat nor otherwise."),
        ("Fallen Cairn", "A traveler's cairn has been disassembled stone by stone along the ridge."),
        ("The Watching Stone", "A boulder is said to turn on its base each night by a hand's breadth."),
        ("Eagles Below", "Mountain eagles are nesting at the treeline, not the peaks."),
        ("The Buried Bell", "Miners struck metal; it rings when the wind crosses the shaft."),
    ],
    "swamp": [
        ("The Lantern in the Reeds", "A lit lantern hangs in the reeds each midnight, unlit by morning."),
        ("The Silent Frogs", "The frogs have stopped calling across a league of marsh."),
        ("The Weeping Willow", "A willow is dripping saltwater in fresh water country."),
        ("The Hag's Offering", "A basket of clean bread has been left on a stump no one tends."),
        ("The Bubble Trail", "A trail of bubbles follows a walker along the bank, below the surface."),
    ],
    "coast": [
        ("The Lighthouse Dark", "The harbor lighthouse has gone dark on clear nights; the keeper insists it is lit."),
        ("Empty Nets", "Three crews in a row returned with nets cleaner than when they left."),
        ("The Drifting Boat", "A fishing boat has been circling the same cove for a day and a night."),
        ("Salt Weeping", "Wooden door frames in the dockside ward are weeping brine."),
        ("The Gull's Warning", "The gulls are flying inland at dusk — all of them, every day."),
    ],
    "tundra": [
        ("The Thaw Patch", "A circle of grass is growing in midwinter tundra."),
        ("Footprints Going Nowhere", "A single set of boot prints stops in the middle of an open flat."),
        ("The Quiet Wind", "The wind has not blown for three days. Elders say it means a debt is due."),
        ("The Blue Bear", "A bear of unusual blue color has been sighted but not tracked."),
    ],
    "underdark": [
        ("The Fungal Bloom", "A new species of glowing fungus is spreading too quickly for natural growth."),
        ("Silent Stone", "A tunnel echoes no sound — not even your own breath."),
        ("The Lost Mapmaker", "A cartographer's apprentice never came back from a routine survey."),
    ],
    "volcanic": [
        ("The Cold Vent", "A steam vent has gone cold and dry overnight."),
        ("Glass Rain", "Obsidian shards rained from a clear sky over the quarry."),
        ("The Hissing Stone", "A black rock the size of a fist is hissing despite the cool ground."),
    ],
    "urban": [
        ("The Ward Curfew", "A new curfew has been posted in one ward only, with no stated reason."),
        ("Bread Shortage", "The bakers' guild claims someone is buying all the rye flour at triple price."),
        ("The Night Thief", "Five houses have been entered; nothing was taken but keepsakes."),
        ("The Empty Courtroom", "Today's docket was emptied without record; witnesses were turned away at the gate."),
        ("Songsmith Arrested", "A street singer was taken for a song she refuses to repeat."),
    ],
    "fey": [
        ("The Wrong Hour", "A bell that has not been rung in a century tolled once, before dawn."),
        ("The Mirror Pool", "A pond now shows the other bank — at another time of day."),
        ("The Blue Rose", "A rose of pure blue has opened where no rose was planted."),
    ],
    "shadow": [
        ("The Sorrow Bell", "A tolling is heard at funerals even when no bell is rung."),
        ("The Shadow Market", "A market has set up in an alley that was a wall yesterday."),
        ("Missing Reflection", "A child's reflection no longer follows them in still water."),
    ],
}

_HINT_TEMPLATES = {
    "forest": "Hunters whisper of a silent grove where no birds sing.",
    "plains": "A caravan hasn't made its weekly run — people are starting to notice.",
    "desert": "The wells to the east are drying — too early in the season.",
    "mountain": "The pass above the treeline has gone strangely quiet.",
    "swamp": "A lantern lights itself each midnight in the reeds.",
    "coast": "The harbor lighthouse has been dark on clear nights.",
    "tundra": "A patch of green grass is growing where none should.",
    "underdark": "Miners speak of a tunnel that eats sound.",
    "volcanic": "A steam vent has gone cold without warning.",
    "urban": "A curfew has been posted in a single ward, with no reason given.",
    "fey": "A pond now reflects a different sky.",
    "shadow": "A tolling is heard at funerals even when no bell is rung.",
}

# A safe biome set the fallback will deal from. Excludes "underdark" /
# "volcanic" / "fey" / "shadow" as starter defaults (they tend to be
# theme-specific and can still be chosen by the LLM pass).
_DEFAULT_BIOME_POOL = ["forest", "plains", "coast", "mountain", "swamp", "tundra", "urban", "desert"]


def _choose_starting_biome(world: Dict) -> str:
    """Infer starter biome from the world's starting-location description."""
    desc = (
        (world.get("startingLocation") or {}).get("description", "")
        + " "
        + (world.get("starting_town") or {}).get("summary", "")
    ).lower()
    hints = {
        "forest": ["forest", "wood", "grove", "pine"],
        "coast": ["coast", "shore", "harbor", "dock", "sea", "port"],
        "mountain": ["mountain", "ridge", "peak", "pass"],
        "desert": ["desert", "sand", "dune"],
        "swamp": ["swamp", "marsh", "bog", "fen"],
        "tundra": ["tundra", "frost", "ice", "snow"],
        "urban": ["city", "ward", "street", "lantern", "market", "crossroad"],
        "plains": ["plain", "meadow", "field", "road"],
    }
    for biome, keywords in hints.items():
        if any(k in desc for k in keywords):
            return biome
    return "urban" if "gate" in desc else "plains"


def _place_nodes_circle(count: int, center: tuple = (0.5, 0.5), radius: float = 0.32,
                        start_angle: float = -math.pi / 2) -> List[Dict]:
    """Lay the starter region at the center, the rest on a loose ring.
    Small jitter keeps nodes from looking mechanical."""
    coords = [{"x": center[0], "y": center[1]}]  # starter at center
    if count <= 1:
        return coords
    step = (2 * math.pi) / (count - 1)
    for i in range(count - 1):
        angle = start_angle + i * step + random.uniform(-0.08, 0.08)
        r = radius + random.uniform(-0.04, 0.05)
        x = center[0] + r * math.cos(angle)
        y = center[1] + r * math.sin(angle)
        # Clamp inside the [0.05, 0.95] safe box so pills never clip edges.
        x = max(0.08, min(0.92, x))
        y = max(0.12, min(0.88, y))
        coords.append({"x": round(x, 3), "y": round(y, 3)})
    return coords


def _make_event(biome: str, title: str, description: str) -> Dict:
    return {
        "id": f"evt_{uuid4().hex[:8]}",
        "title": title,
        "description": description,
        "biome": biome,
        "difficulty": random.choice(["easy", "medium", "medium", "hard"]),
        "status": "available",
        "tags": ["event", biome],
    }


def _seed_events_for_biome(biome: str, count: int) -> List[Dict]:
    templates = _EVENT_TEMPLATES.get(biome) or _EVENT_TEMPLATES["plains"]
    chosen = random.sample(templates, k=min(count, len(templates)))
    return [_make_event(biome, title, desc) for title, desc in chosen]


def _make_region(biome: str, name: str, description: str, coord: Dict,
                 is_starting: bool, events_full: int, events_hint_count: int) -> Dict:
    hydrated = is_starting
    events = _seed_events_for_biome(biome, events_full) if hydrated else []
    hint_templates = (_EVENT_TEMPLATES.get(biome) or _EVENT_TEMPLATES["plains"])[:events_hint_count]
    hints = [t[0] for t in hint_templates] if not hydrated else []
    return {
        "id": f"reg_{uuid4().hex[:8]}",
        "name": name,
        "biome": biome,
        "description": description,
        "x": coord["x"],
        "y": coord["y"],
        "is_starting": is_starting,
        "hydrated": hydrated,
        "visited": is_starting,
        "hints": hints,
        "events": events,
    }


def _template_graph(intent: CampaignIntent, world: Dict, character: Optional[Dict],
                    region_count: int = 6, events_per_region: int = 5) -> Dict:
    """Deterministic fallback graph when the LLM is unavailable."""
    start_biome = _choose_starting_biome(world)

    # Starter region: name it after the starting town; reuse its description.
    starting = world.get("startingLocation") or {}
    starter_name = starting.get("name") or "Home Crossroads"
    starter_desc = starting.get("description") or "Where your story begins."

    # Pick neighbor biomes: a mix that always includes at least one "travel"
    # biome different from the start.
    pool = [b for b in _DEFAULT_BIOME_POOL if b != start_biome]
    random.shuffle(pool)
    neighbor_biomes = pool[: region_count - 1]

    coords = _place_nodes_circle(region_count)
    regions: List[Dict] = []
    regions.append(_make_region(
        biome=start_biome,
        name=starter_name,
        description=starter_desc,
        coord=coords[0],
        is_starting=True,
        events_full=events_per_region,
        events_hint_count=0,
    ))
    for i, b in enumerate(neighbor_biomes):
        parts = _REGION_NAME_PARTS.get(b) or _REGION_NAME_PARTS["plains"]
        first, last = random.choice(parts)
        name = f"{first} {last}".strip() or first or b.title()
        hint = _HINT_TEMPLATES.get(b, "Rumors reach you from beyond the horizon.")
        regions.append(_make_region(
            biome=b,
            name=name,
            description=hint,
            coord=coords[i + 1],
            is_starting=False,
            events_full=events_per_region,
            events_hint_count=min(3, events_per_region),
        ))

    # Edges: starter connects to every neighbor; neighbors loosely chain.
    edges: List[Dict] = []
    for r in regions[1:]:
        edges.append({"from": regions[0]["id"], "to": r["id"], "difficulty": "medium"})
    for i in range(1, len(regions) - 1):
        # 50% chance to chain neighbor-to-neighbor for a less radial feel
        if random.random() < 0.6:
            edges.append({"from": regions[i]["id"], "to": regions[i + 1]["id"], "difficulty": "easy"})

    return {
        "regions": regions,
        "edges": edges,
        "current_region_id": regions[0]["id"],
    }


# -------------------- LLM-enhanced generation --------------------


async def generate_world_graph(
    intent: CampaignIntent,
    world: Dict,
    character: Optional[Dict],
    region_count: int = 6,
    events_per_region: int = 5,
) -> Dict:
    """Generate the campaign's region graph. Uses the LLM to name and flavor
    regions + seed the starter deck; falls back to deterministic templates.
    """
    region_count = max(3, min(8, int(region_count)))
    events_per_region = max(3, min(8, int(events_per_region)))

    fallback = _template_graph(intent, world, character, region_count, events_per_region)

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return fallback

        start_biome = _choose_starting_biome(world)
        starter_name = (world.get("startingLocation") or {}).get("name", "the starting area")
        starter_desc = (world.get("startingLocation") or {}).get("description", "")
        realm = (world.get("world_core") or {}).get("name", "the realm")
        biome_keys = ", ".join(list_biome_keys())

        prompt = (
            "Design a CAMPAIGN MAP as a small graph of regions for a Dungeons & Dragons 5e campaign. "
            "Regions are BIG places (a forest district, a coastal ward, a swamp basin), not single villages.\n\n"
            f"=== WORLD ===\nRealm: {realm}\nStarter biome: {start_biome}\n"
            f"Starting region is centered on: {starter_name} — {starter_desc}\n"
            f"Campaign tone: {intent.tone} | focus: {intent.focus} | scope: {intent.scope} | danger: {intent.danger}\n\n"
            f"=== BIOMES (pick from these keys only) ===\n{biome_keys}\n\n"
            f"=== REQUIREMENTS ===\n"
            f"- Produce EXACTLY {region_count} regions including the starter.\n"
            f"- The first region in the output array MUST be the starter, with `is_starting=true`,\n"
            f"  using the name \"{starter_name}\" and biome \"{start_biome}\".\n"
            f"- The other {region_count - 1} regions should use DIFFERENT biomes where plausible;\n"
            f"  they are NEIGHBORS reachable on foot or short travel. Mix biomes so the map feels varied.\n"
            f"- For each region: name (no apostrophes), biome (one of the keys above),\n"
            f"  description (1 sentence, grounded, no cliche), and a 'hint' (1 short teaser line of a rumor\n"
            f"  the player might hear about that region).\n"
            f"- For the STARTER region ONLY, ALSO output {events_per_region} event hooks (quest seeds): each with\n"
            f"  a title (3-6 words, no quotes, no clichés like 'ancient evil'), a 1-sentence description,\n"
            f"  and a difficulty (easy|medium|hard). Events must be biome-flavored (forest event ≠ desert event),\n"
            f"  plausible for a level-1 party.\n"
            f"- NO cliches: no 'chosen one', 'ancient evil', 'dark lord', 'prophecy', 'mysterious stranger'.\n"
            f"- HARD-BAN phrases: 'a veil falls', 'darkness stirs', 'whispers of fate'.\n\n"
            "=== OUTPUT (strict JSON only, no code fence, no prose) ===\n"
            "{\n"
            "  \"regions\": [\n"
            "    { \"name\": \"...\", \"biome\": \"<biome_key>\", \"description\": \"...\", \"hint\": \"...\",\n"
            "      \"is_starting\": true,\n"
            "      \"events\": [\n"
            "        { \"title\": \"...\", \"description\": \"...\", \"difficulty\": \"easy|medium|hard\" }\n"
            "      ]\n"
            "    },\n"
            "    { \"name\": \"...\", \"biome\": \"<biome_key>\", \"description\": \"...\", \"hint\": \"...\",\n"
            "      \"is_starting\": false, \"events\": [] }\n"
            "  ]\n"
            "}\n"
        )

        chat = LlmChat(
            api_key=api_key,
            session_id=f"world-graph-{uuid4()}",
            system_message=(
                "You are a senior D&D worldbuilder. You design tight, biome-varied campaign "
                "maps with grounded region names and specific, flavorful quest seeds. Output strict JSON only."
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
            s, e = text.find("{"), text.rfind("}")
            if s != -1 and e > s:
                data = _json.loads(text[s : e + 1])
            else:
                raise

        raw_regions = data.get("regions") or []
        if not isinstance(raw_regions, list) or len(raw_regions) < 3:
            return fallback

        # Build regions from AI output, keeping deterministic coords & ids.
        coords = _place_nodes_circle(min(region_count, len(raw_regions)))
        regions: List[Dict] = []
        starter_written = False
        for i, r in enumerate(raw_regions[:region_count]):
            biome = str(r.get("biome") or "").strip().lower()
            if biome not in BIOMES:
                biome = start_biome if not starter_written else random.choice(_DEFAULT_BIOME_POOL)
            is_starting = bool(r.get("is_starting")) and not starter_written
            if is_starting:
                starter_written = True
            name = str(r.get("name") or "").strip() or (starter_name if is_starting else f"Region {i+1}")
            description = str(r.get("description") or r.get("hint") or "").strip() or starter_desc
            hint = str(r.get("hint") or "").strip()
            coord = coords[i] if i < len(coords) else {"x": 0.5, "y": 0.5}
            events: List[Dict] = []
            if is_starting:
                raw_events = r.get("events") or []
                for ev in raw_events[:events_per_region]:
                    if not isinstance(ev, dict):
                        continue
                    title = str(ev.get("title") or "").strip()
                    desc = str(ev.get("description") or "").strip()
                    if not title or not desc:
                        continue
                    diff = str(ev.get("difficulty") or "medium").lower()
                    if diff not in {"easy", "medium", "hard"}:
                        diff = "medium"
                    events.append({
                        "id": f"evt_{uuid4().hex[:8]}",
                        "title": title[:60],
                        "description": desc[:260],
                        "biome": biome,
                        "difficulty": diff,
                        "status": "available",
                        "tags": ["event", biome],
                    })
                if len(events) < events_per_region:
                    # top up with biome-flavored templates
                    events.extend(_seed_events_for_biome(biome, events_per_region - len(events)))

            regions.append({
                "id": f"reg_{uuid4().hex[:8]}",
                "name": name[:48],
                "biome": biome,
                "description": description[:260],
                "x": coord["x"],
                "y": coord["y"],
                "is_starting": is_starting,
                "hydrated": is_starting,
                "visited": is_starting,
                "hints": [hint] if hint and not is_starting else [],
                "events": events,
            })

        # Guarantee exactly one starter
        if not starter_written and regions:
            regions[0]["is_starting"] = True
            regions[0]["hydrated"] = True
            regions[0]["visited"] = True
            if not regions[0]["events"]:
                regions[0]["events"] = _seed_events_for_biome(regions[0]["biome"], events_per_region)

        # Edges: starter→each neighbor, plus 60% neighbor chain
        starter = next((r for r in regions if r["is_starting"]), regions[0])
        edges: List[Dict] = []
        for r in regions:
            if r["id"] == starter["id"]:
                continue
            edges.append({"from": starter["id"], "to": r["id"], "difficulty": "medium"})
        others = [r for r in regions if r["id"] != starter["id"]]
        for i in range(len(others) - 1):
            if random.random() < 0.6:
                edges.append({"from": others[i]["id"], "to": others[i + 1]["id"], "difficulty": "easy"})

        return {
            "regions": regions,
            "edges": edges,
            "current_region_id": starter["id"],
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"AI world-graph generation failed, using template: {exc}")
        return fallback


# -------------------- hydration (lazy) --------------------


async def hydrate_region(
    intent: CampaignIntent,
    world: Dict,
    region: Dict,
    events_count: int = 5,
) -> Dict:
    """Expand a hinted (non-starter) region into a full event deck on first visit.

    Uses the LLM when available, otherwise deterministic biome templates.
    Mutates a COPY and returns it (caller persists).
    """
    if region.get("hydrated") and region.get("events"):
        return region

    biome = (region.get("biome") or "plains").lower()
    fallback_events = _seed_events_for_biome(biome, events_count)

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("no LLM key")

        realm = (world.get("world_core") or {}).get("name", "the realm")
        prompt = (
            f"Seed {events_count} event hooks for a D&D 5e region the player has just entered.\n\n"
            f"=== REGION ===\nName: {region.get('name')}\nBiome: {biome}\n"
            f"Description: {region.get('description')}\nRealm: {realm}\n"
            f"Campaign tone: {intent.tone} | focus: {intent.focus} | danger: {intent.danger}\n\n"
            "Each event must feel native to this biome and distinct from the others. "
            "No cliches (no 'ancient evil', no 'chosen one'). Level-1 plausible.\n\n"
            "=== OUTPUT (strict JSON) ===\n"
            "{ \"events\": [ { \"title\": \"...\", \"description\": \"...\", "
            "\"difficulty\": \"easy|medium|hard\" } ] }"
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"region-hydrate-{uuid4()}",
            system_message="You are a senior D&D campaign designer. Output strict JSON only.",
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
            s, e = text.find("{"), text.rfind("}")
            data = _json.loads(text[s : e + 1]) if s != -1 and e > s else {}

        events = []
        for ev in (data.get("events") or [])[:events_count]:
            if not isinstance(ev, dict):
                continue
            title = str(ev.get("title") or "").strip()
            desc = str(ev.get("description") or "").strip()
            if not title or not desc:
                continue
            diff = str(ev.get("difficulty") or "medium").lower()
            if diff not in {"easy", "medium", "hard"}:
                diff = "medium"
            events.append({
                "id": f"evt_{uuid4().hex[:8]}",
                "title": title[:60],
                "description": desc[:260],
                "biome": biome,
                "difficulty": diff,
                "status": "available",
                "tags": ["event", biome],
            })
        if len(events) < max(3, events_count - 1):
            events = fallback_events
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Region hydrate failed, using template: {exc}")
        events = fallback_events

    new_region = dict(region)
    new_region["events"] = events
    new_region["hydrated"] = True
    new_region["visited"] = True
    new_region["hints"] = []
    return new_region
