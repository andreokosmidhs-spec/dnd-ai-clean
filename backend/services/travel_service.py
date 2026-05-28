"""Travel service — inter-region travel mechanics.

Travel speeds (PHB):
  walk → 3 mph   |   ride → 6 mph

Edge difficulty → distance:
  easy   → 12 miles (4h walk / 2h ride)
  medium → 24 miles (8h walk / 4h ride)
  hard   → 36 miles (12h walk / 6h ride)

Each segment = 6 miles. Rolls happen per segment:
  - Random encounter: 20% base, modified by biome hazard rating
  - Dungeon discovery: 10% + 10% per 3 completed quests (max 60%)
  - Lost check: only on hard edges, DC 15 Survival vs character Survival score
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Speed and distance tables
# ---------------------------------------------------------------------------

SPEED_MPH = {"walk": 3, "ride": 6}

DIFFICULTY_MILES = {"easy": 12, "medium": 24, "hard": 36}

SEGMENT_MILES = 6  # one "---" segment on the map

# Encounter probability per segment (base)
BASE_ENCOUNTER_CHANCE = 0.20

# Biome encounter modifiers (added to base)
BIOME_ENCOUNTER_MOD = {
    "forest":    0.05,
    "plains":    0.00,
    "desert":    0.05,
    "mountain":  0.10,
    "swamp":     0.15,
    "coast":     0.05,
    "tundra":    0.10,
    "underdark": 0.20,
    "volcanic":  0.15,
    "urban":     -0.10,
    "fey":       0.10,
    "shadow":    0.25,
}

# Lost check DC (only on hard edges, vs character Survival modifier)
LOST_DC = 15

# ---------------------------------------------------------------------------
# Biome encounter tables
# ---------------------------------------------------------------------------

_ENCOUNTERS: Dict[str, List[Dict]] = {
    "forest": [
        {"type": "combat", "tag": "wolves",    "summary": "A wolf pack emerges from the treeline — they move with unusual coordination, as if following a directive, not hunger."},
        {"type": "combat", "tag": "bandits",   "summary": "Rope pulls taut across the path. Crossbows click from the branches above. 'Toll road,' someone calls down."},
        {"type": "social", "tag": "smugglers", "summary": "Two figures with bulging sacks freeze at the sight of you. They glance at each other. The sacks are moving."},
        {"type": "social", "tag": "poacher",   "summary": "A man crouches over a snare, his back to you. He has more pelts than any legal hunt produces."},
        {"type": "discovery", "tag": "shrine", "summary": "A hunting shrine — antlers, bones, small offerings. Someone has left it recently. The candle is still warm."},
        {"type": "hazard", "tag": "deadfall",  "summary": "The ground ahead is soft and webbed with roots. One wrong step and the crust gives way into a ten-foot pit."},
        {"type": "social", "tag": "travelers", "summary": "A family with a cart, going the wrong direction. They look like they haven't stopped in two days."},
        {"type": "combat", "tag": "goblin_scouts", "summary": "Tracks first, then laughter from the canopy. Three goblins — a scout unit, and where there are scouts there is something following them."},
    ],
    "plains": [
        {"type": "combat", "tag": "bandits",    "summary": "Riders on the horizon, moving to cut you off. Four of them, spread wide. They've done this before."},
        {"type": "social", "tag": "merchant",   "summary": "A merchant's wagon with a broken axle. The merchant is calm in the way people are when they are very frightened and very tired of showing it."},
        {"type": "discovery", "tag": "camp",    "summary": "An abandoned campsite — fire long cold, a boot left behind, no explanation for the haste."},
        {"type": "social", "tag": "militia",    "summary": "A patrol of local militia stops you. They're young, they're armed, and they have a list of questions someone told them to ask."},
        {"type": "hazard", "tag": "storm",      "summary": "The sky turns the color of a bruise. Hail starts. You have maybe five minutes to find shelter before it becomes something worse."},
        {"type": "social", "tag": "pilgrims",   "summary": "A line of pilgrims moving in silence, hoods up. They don't acknowledge you. One near the back watches you pass."},
        {"type": "combat", "tag": "gnolls",     "summary": "Cackling from the long grass. The sound circles you before the shapes emerge."},
        {"type": "discovery", "tag": "monument","summary": "A stone marker, old enough that the inscription is half-gone. What remains is a name and a warning."},
    ],
    "desert": [
        {"type": "hazard", "tag": "sandstorm",  "summary": "The wind picks up. The horizon turns orange-brown. A sandstorm, moving fast — you have minutes to prepare."},
        {"type": "combat", "tag": "gnoll_raiders","summary": "Three gnolls charge from behind a dune. They have already chosen who to take."},
        {"type": "social", "tag": "nomads",     "summary": "A nomadic family with two camels. They offer water. They also ask questions about where you came from that seem like more than curiosity."},
        {"type": "discovery", "tag": "ruin",    "summary": "Stones emerging from the sand — the corner of something large. A building, buried. The entrance is a darkness you could walk into."},
        {"type": "hazard", "tag": "heat",       "summary": "By midday the air shimmers and your water consumption doubles. Someone in the group will need to make a Constitution save by tonight."},
        {"type": "combat", "tag": "scorpions",  "summary": "Giant scorpions — a mated pair, territorial. They're not hunting. You walked into their nest."},
        {"type": "social", "tag": "hermit",     "summary": "A hermit who has clearly been here too long. They know something useful. Getting it out of them is the problem."},
        {"type": "discovery", "tag": "oasis",   "summary": "An oasis — real, not a mirage. Someone else has found it first. Their camp is on the far bank."},
    ],
    "mountain": [
        {"type": "hazard", "tag": "rockslide",  "summary": "The crack above is followed by a rumble. Boulders are coming down. You have seconds to decide which way to run."},
        {"type": "combat", "tag": "harpies",    "summary": "Screeching from above. They dive in formation — a hunting pattern. The one that's circling is the one that scares you."},
        {"type": "social", "tag": "dwarves",    "summary": "A dwarven survey team, mapping something. They're friendly but cagey about what they've found."},
        {"type": "combat", "tag": "mountain_goats","summary": "Giant goats, territorial, charging down the switchback. Not monsters — just very large animals that have decided you are a threat."},
        {"type": "hazard", "tag": "bridge",     "summary": "The rope bridge sways over a two-hundred-foot drop. One of the anchor posts is rotted through. It will hold — probably — but not at speed."},
        {"type": "social", "tag": "hermit",     "summary": "A cave-hermit who has been watching you from a ledge. They know the passes better than any map."},
        {"type": "combat", "tag": "ogre",       "summary": "An ogre squats across the path. It's not hungry — it's bored, and you look like entertainment."},
        {"type": "discovery", "tag": "cairn",   "summary": "A summit cairn with a metal box buried beneath it. Inside: a map, a note, and something that should not be here."},
    ],
    "swamp": [
        {"type": "hazard", "tag": "quicksand",  "summary": "The ground gives. One foot, then the other, sinking faster than expected. The more you struggle, the faster it takes you."},
        {"type": "combat", "tag": "lizardfolk", "summary": "Spears level out of the reeds. Lizardfolk — a border patrol for their village. Whether this is a fight or a conversation depends on the next ten seconds."},
        {"type": "combat", "tag": "crocodile",  "summary": "The log isn't a log. It waited until you were close."},
        {"type": "social", "tag": "witch",      "summary": "A hut on stilts. An old woman who knows your name before you say it, and charges for answers."},
        {"type": "discovery", "tag": "ruins",   "summary": "Half-sunken walls from something old. The inside is above water. Something lives there — the bones say it doesn't eat everything."},
        {"type": "hazard", "tag": "fog",        "summary": "Thick fog rolls in. The path you came in on is no longer visible. You're not lost yet. You're about to be."},
        {"type": "combat", "tag": "will_o_wisp","summary": "A blue light, moving. Then three. They lead you slightly off course before you realize it."},
        {"type": "social", "tag": "refugees",   "summary": "People who fled something, camped on a dry hummock. They won't say what they fled from, but they left in a hurry."},
    ],
    "coast": [
        {"type": "combat", "tag": "pirates",    "summary": "A longboat runs aground ahead of you. Twelve sailors, armed, blocking the coastal road. This is a toll or a fight."},
        {"type": "social", "tag": "smugglers",  "summary": "A rowboat grounded in a cove, crates being unloaded into a hidden space in the cliff. They see you. Everyone stops."},
        {"type": "hazard", "tag": "tide",       "summary": "The sea road you're following — the tide charts say it's passable. The charts were made before the storm last week."},
        {"type": "discovery", "tag": "wreck",   "summary": "A shipwreck, recent. Cargo still in the hold. No bodies yet — either they swam, or something else came first."},
        {"type": "combat", "tag": "merrow",     "summary": "A shape in the shallows, then another. Merrow, dragging something heavy toward the water. It's still alive."},
        {"type": "social", "tag": "fishermen",  "summary": "Three fishermen in a state of particular quiet. Their catch is odd — something in the net that shouldn't be there."},
        {"type": "hazard", "tag": "rogue_wave", "summary": "The water retreats unnaturally fast. Then it comes back."},
        {"type": "discovery", "tag": "cave",    "summary": "A sea cave visible at low tide, carved steps leading down into it from a different era entirely."},
    ],
    "tundra": [
        {"type": "hazard", "tag": "blizzard",   "summary": "White-out conditions. In ten minutes you won't be able to see five feet ahead. You need shelter or you're going to lose someone."},
        {"type": "combat", "tag": "dire_wolves","summary": "A pack of dire wolves, winter-hungry, moving with the wind behind them."},
        {"type": "social", "tag": "hunters",    "summary": "Tribal hunters tracking a herd — they're annoyed you've crossed the trail. This could be resolved diplomatically, or not."},
        {"type": "discovery", "tag": "cairn",   "summary": "A cairn of black stones, pattern-arranged. A warning or a marker from people who knew something about this place."},
        {"type": "hazard", "tag": "thin_ice",   "summary": "The frozen lake looks solid. The sound it makes when you step on it does not inspire confidence."},
        {"type": "combat", "tag": "frost_giant_scout","summary": "Not the giant — its sled dog equivalent. A creature the size of a horse, used as a ranging animal. Its owner isn't far."},
        {"type": "social", "tag": "hermit",     "summary": "A trapper who's been out here through three winters. They know the terrain better than any map. They also want company badly enough to be dangerous about it."},
        {"type": "discovery", "tag": "ruins",   "summary": "Something ancient below the ice — a structure, visible through clear sections. The door to it is above the surface."},
    ],
    "underdark": [
        {"type": "combat", "tag": "drow_scouts","summary": "A Drow patrol — they knew you were coming before you turned the corner. The torchlight didn't help."},
        {"type": "combat", "tag": "hook_horror","summary": "The clicking is the warning. By the time you know what the clicking means, it's already in the tunnel with you."},
        {"type": "hazard", "tag": "spores",     "summary": "Yellow myconid spores in the air. Breathe them and roll a Constitution save. Failure means eight hours of waking hallucinations."},
        {"type": "discovery", "tag": "ruins",   "summary": "A door in the tunnel wall, sealed, with markings that predate the Underdark settlements. Someone sealed it from outside."},
        {"type": "combat", "tag": "cave_fisher","summary": "The sticky filament hits your shoulder before you see the cave fisher above. It's reeling you in."},
        {"type": "social", "tag": "deep_gnomes","summary": "Svirfneblin miners. They're going the same direction you are, faster, and they're frightened. They'll talk if you keep pace."},
        {"type": "hazard", "tag": "tunnel_collapse","summary": "The ground shudders. A section of ceiling ahead drops — a partial collapse, leaving a gap you can cross, barely."},
        {"type": "combat", "tag": "darkmantles","summary": "They drop from above. The light goes out. The sounds continue in the dark."},
    ],
    "volcanic": [
        {"type": "hazard", "tag": "eruption",   "summary": "The mountain rumbles and a vent opens in the ground thirty feet ahead. Gas and heat. The path is still passable but not for long."},
        {"type": "combat", "tag": "fire_elementals","summary": "A fire elemental detached from a rift vent — it doesn't want anything, it just destroys what's in its radius."},
        {"type": "social", "tag": "cultists",   "summary": "Robed figures performing a ritual at a lava pool. They are very calm about your arrival, which is more frightening than anger would be."},
        {"type": "hazard", "tag": "ash_cloud",  "summary": "Ash falls heavy enough to block sight and clog breathing. You'll need cloth over your faces or make it quick."},
        {"type": "discovery", "tag": "forge",   "summary": "An ancient forge built into the mountain — cold now, but the metalwork inside is from a civilization that mastered something you don't recognize."},
        {"type": "combat", "tag": "salamanders","summary": "Salamanders — fire newts, the size of horses — basking in a lava pool that crosses your only path."},
        {"type": "hazard", "tag": "lava_flow",  "summary": "Slow-moving lava crossed the road since the last traveler came through. It's cooling but not yet solid. The alternative route adds two hours."},
        {"type": "social", "tag": "dwarves",    "summary": "A dwarven reclamation team, salvaging metal from a buried forge complex. They're not supposed to be here. Neither, technically, are you."},
    ],
    "urban": [
        {"type": "social", "tag": "pickpockets","summary": "Someone jostles you in the crowd. A second later you notice your coin purse has changed weight."},
        {"type": "social", "tag": "city_watch", "summary": "Two city watch officers fall into step beside you. 'Just keeping you company,' one says. The questions start a minute later."},
        {"type": "combat", "tag": "thugs",      "summary": "A crew following you from the market district. They're waiting for a quieter street."},
        {"type": "social", "tag": "informant",  "summary": "Someone slips you a folded note and walks away without looking back. The note names a place, a time, and your name."},
        {"type": "discovery", "tag": "crime",   "summary": "An alley, a body, fresh. Someone who either ran very recently or is very well hidden saw what happened."},
        {"type": "social", "tag": "guild_rep",  "summary": "A Guild representative with a proposition — they're politely insistent and know more about your recent activities than they should."},
        {"type": "social", "tag": "beggar",     "summary": "A beggar who says one specific thing to you before asking for coin. The specific thing is either coincidence or something else entirely."},
        {"type": "hazard", "tag": "fire",       "summary": "Smoke ahead. A building fire, recently caught. People outside, some still inside, and a crowd doing very little about it."},
    ],
    "fey": [
        {"type": "social", "tag": "pixies",     "summary": "Laughter from everywhere and nowhere. Your equipment moves. A pixie holds your coin purse at arm's length, grinning."},
        {"type": "combat", "tag": "redcaps",    "summary": "Red-capped figures, quick, with iron boots and iron rakes. They stop smiling when you stop running."},
        {"type": "social", "tag": "dryad",      "summary": "A dryad who blocks your path politely but completely. She has a price for passage and it is strange but not dangerous."},
        {"type": "hazard", "tag": "time_loop",  "summary": "You've passed this tree before. And this stone. The path is looping and the loops are getting shorter."},
        {"type": "discovery", "tag": "ring",    "summary": "A fairy ring — mushrooms in a perfect circle. Something is inside it that wasn't there this morning. Something that looks like a door."},
        {"type": "combat", "tag": "satyrs",     "summary": "A satyr troupe that doesn't take no for an answer about the party they're having, and has increasingly firm ways of making their point."},
        {"type": "social", "tag": "archfey",    "summary": "Something you can't quite look at directly. It tells you something true. You can tell it's true because it hurts."},
        {"type": "hazard", "tag": "glamour",    "summary": "The path looks safe. The path is not safe. A glamour over a ravine, a bog, something. Your Wisdom saves you if it can."},
    ],
    "shadow": [
        {"type": "combat", "tag": "shadows",    "summary": "They're in the shadows, which means they're everywhere. They drain Strength on touch and they want your shadow to add to their number."},
        {"type": "combat", "tag": "wraith",     "summary": "A wraith, moving in silence, drawn to the heat of life in this cold place."},
        {"type": "hazard", "tag": "despair",    "summary": "The Shadowfell's ambient despair works on you. Make a Wisdom save or spend the next hour convinced that nothing matters and no one is coming."},
        {"type": "social", "tag": "shade",      "summary": "A shade — a person who didn't quite make it through the Raven Queen's domain. They have a message for someone still alive. They need you to deliver it."},
        {"type": "discovery", "tag": "fortress","summary": "A fortress that shouldn't be here — a shadow duplicate of a real building somewhere. Whatever is inside is a mirror of what that building contains."},
        {"type": "combat", "tag": "banshee",    "summary": "A wail cuts the air. Everyone makes a Constitution save. Failure means unconscious. Success means you still have to fight her."},
        {"type": "hazard", "tag": "darkness",   "summary": "Magical darkness, absolute. No light source works here. You navigate by sound and feeling until it lifts — if it lifts."},
        {"type": "social", "tag": "death_knight","summary": "It rides a pale horse and it watches you pass. It does not attack. It does not speak. The fact that it lets you go will bother you for a long time."},
    ],
}


# ---------------------------------------------------------------------------
# Travel calculation
# ---------------------------------------------------------------------------

def calculate_travel(edge_difficulty: str, mode: str = "walk") -> Dict:
    """Return travel metadata for an edge crossing.

    Returns:
        segments     — number of ~6-mile segments
        miles        — total distance
        hours        — travel time in game-hours
        speed_mph    — actual travel speed
    """
    miles = DIFFICULTY_MILES.get(edge_difficulty, 24)
    speed = SPEED_MPH.get(mode, 3)
    segments = max(1, round(miles / SEGMENT_MILES))
    hours = miles / speed
    return {
        "segments": segments,
        "miles": miles,
        "hours": round(hours, 1),
        "speed_mph": speed,
        "mode": mode,
        "difficulty": edge_difficulty,
    }


# ---------------------------------------------------------------------------
# Encounter rolling
# ---------------------------------------------------------------------------

def roll_encounter(biome: str, segment_index: int) -> Optional[Dict]:
    """Roll for a random encounter on a single travel segment.

    Returns an encounter dict or None.
    """
    chance = BASE_ENCOUNTER_CHANCE + BIOME_ENCOUNTER_MOD.get(biome, 0.0)
    if random.random() > chance:
        return None

    table = _ENCOUNTERS.get(biome, _ENCOUNTERS["plains"])
    encounter = random.choice(table)
    return {
        "segment": segment_index,
        "type": encounter["type"],     # combat | social | discovery | hazard
        "tag": encounter["tag"],
        "summary": encounter["summary"],
        "biome": biome,
    }


def roll_all_encounters(biome: str, segments: int) -> List[Dict]:
    """Roll encounters for every segment of a journey. Returns list of encounters (may be empty)."""
    results = []
    for i in range(segments):
        enc = roll_encounter(biome, i + 1)
        if enc:
            results.append(enc)
    return results


# ---------------------------------------------------------------------------
# Dungeon discovery
# ---------------------------------------------------------------------------

def roll_dungeon_discovery(quests_completed: int) -> bool:
    """Roll for dungeon discovery. Returns True if a dungeon is found.

    Base 10%, +10% per 3 quests completed. Maximum 60%.
    """
    chance = min(0.60, 0.10 + (quests_completed // 3) * 0.10)
    return random.random() < chance


# ---------------------------------------------------------------------------
# Lost check
# ---------------------------------------------------------------------------

def check_lost(edge_difficulty: str, survival_mod: int = 0) -> Optional[Dict]:
    """Roll a Survival check against getting lost (only on hard terrain).

    Returns dict with result, or None if no check needed.
    """
    if edge_difficulty != "hard":
        return None

    roll = random.randint(1, 20) + survival_mod
    success = roll >= LOST_DC
    return {
        "dc": LOST_DC,
        "roll": roll,
        "survival_mod": survival_mod,
        "success": success,
        "time_penalty_hours": 0 if success else 2.0,  # 2 extra hours if lost
    }


# ---------------------------------------------------------------------------
# Full travel resolution
# ---------------------------------------------------------------------------

def resolve_travel(
    edge_difficulty: str,
    biome: str,
    mode: str = "walk",
    quests_completed: int = 0,
    survival_mod: int = 0,
) -> Dict:
    """Resolve a complete travel leg in one call.

    Returns:
        travel_info   — distance/time data
        encounters    — list of encounter dicts (may be empty)
        dungeon_found — True if a dungeon is discovered at the destination
        lost_check    — dict with Survival check result, or None
        total_hours   — actual hours spent (including lost time)
        summary       — brief string for DM context
    """
    travel = calculate_travel(edge_difficulty, mode)
    encounters = roll_all_encounters(biome, travel["segments"])
    dungeon_found = roll_dungeon_discovery(quests_completed)
    lost = check_lost(edge_difficulty, survival_mod)

    total_hours = travel["hours"] + (lost["time_penalty_hours"] if lost and not lost["success"] else 0.0)

    enc_types = [e["type"] for e in encounters]
    parts = [f"The journey covers {travel['miles']} miles ({travel['hours']}h at {travel['speed_mph']} mph)."]
    if encounters:
        parts.append(f"{'and '.join(set(enc_types)).capitalize()} encounter(s) on the road.")
    if lost and not lost["success"]:
        parts.append(f"The group loses the path; {lost['time_penalty_hours']}h added.")
    if dungeon_found:
        parts.append("A dungeon entrance is spotted near the destination.")

    return {
        "travel_info": travel,
        "encounters": encounters,
        "dungeon_found": dungeon_found,
        "lost_check": lost,
        "total_hours": round(total_hours, 1),
        "summary": " ".join(parts),
    }


# ---------------------------------------------------------------------------
# DM prompt block
# ---------------------------------------------------------------------------

def build_travel_block(travel_result: Dict, from_name: str, to_name: str) -> str:
    """Build a TRAVEL CONTEXT block for the DM system prompt."""
    info = travel_result["travel_info"]
    enc = travel_result["encounters"]
    lost = travel_result["lost_check"]
    dungeon = travel_result["dungeon_found"]

    lines = [
        "=== TRAVEL CONTEXT ===",
        f"JOURNEY: {from_name} → {to_name}",
        f"Distance: {info['miles']} miles | Mode: {info['mode']} | Time: {travel_result['total_hours']}h",
        "",
        "NARRATION RULES FOR TRAVEL:",
        "▸ Narrate the journey as passing time — not instant. Show the road, the light changing, the miles accumulating.",
        "▸ Environmental details should match the biome. No random hooks unless they arise from the encounters below.",
        "▸ Each encounter listed below must be narrated in order. Give each one a scene, not just a line.",
        "▸ The player may engage, avoid, or pass through each encounter. Respect their choice.",
    ]

    if lost and not lost["success"]:
        lines += [
            "",
            f"NAVIGATION FAILURE: The party lost the path (Survival DC {lost['dc']}, rolled {lost['roll']}).",
            "▸ Narrate a period of confusion — wrong turns, landmarks that don't match, a growing unease.",
            f"▸ The delay costs {lost['time_penalty_hours']} hours. Night may fall. Camp may be necessary.",
        ]

    if enc:
        lines.append("\nENCOUNTERS ALONG THE ROAD (narrate in order):")
        for i, e in enumerate(enc, 1):
            lines.append(f"  {i}. [{e['type'].upper()}] Segment {e['segment']}: {e['summary']}")
    else:
        lines.append("\nNo encounters on this road. The journey is quiet — but quiet has its own texture. Use it.")

    if dungeon:
        lines += [
            "",
            "DUNGEON DISCOVERED: As the destination comes into view, something else does too.",
            "▸ An entrance — a cave mouth, a cellar door, a collapsed tower — is visible near the road.",
            "▸ Describe it briefly and let the player decide: investigate now, or continue to the destination?",
            "▸ The entrance shows signs of use. Something is inside.",
        ]

    lines += [
        "",
        "ARRIVAL: Once all encounters are resolved, the party arrives at the destination.",
        "▸ Give a single arrival beat — what they see first, what hits them first (sound, smell, sight).",
        "▸ Then hand control back to the player.",
    ]

    return "\n".join(lines)
