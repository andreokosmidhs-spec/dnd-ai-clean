"""
Example world blueprints for testing and development.
"""

VALDRATH_BLUEPRINT = {
    "world_core": {
        "name": "Valdrath",
        "tone": "Dark, grounded fantasy with rare but dangerous magic",
        "magic_level": "rare_but_powerful",
        "ancient_event": {
            "name": "The Sundering of the Velkhar Dominion",
            "description": "Three centuries ago, the Velkhar Dominion, a mighty arcane empire, tried to bind a god of secrets. The ritual shattered the Dominion overnight, cursing its cities into ruins and tearing veils between the mortal realm and stranger places.",
            "current_legacies": [
                "Velkhar ruins litter the continent, haunted by twisted magic.",
                "Cursed relics from the Dominion surface in black markets and temples.",
                "Old wards and forbidden sigils still slumber beneath major cities."
            ]
        }
    },
    "starting_region": {
        "name": "Raven's Hollow",
        "description": "A low, fog-choked basin on Valdrath's western rim, where trade roads converge through marshy ground and old battlefield soil.",
        "biome_layers": [
            "boggy lowlands",
            "fog-bound forests",
            "distant broken hills"
        ],
        "notable_features": [
            "Collapsed Velkhar watchtowers half-swallowed by the mire.",
            "An old causeway road raised above the wetlands.",
            "Whispering reed-beds where travelers swear they hear voices at night."
        ]
    },
    "starting_town": {
        "name": "Raven's Hollow",
        "role": "trade_hub_crossroads",
        "summary": "Raven's Hollow is a cramped riverside trade town built on pilings and old stone, serving as a fog-bound crossroads for caravans too desperate or too greedy to take safer routes.",
        "population_estimate": 1200,
        "building_estimate": 220,
        "signature_products": [
            "blackfog rum distilled from marsh reeds",
            "smoke-cured river eel",
            "illicit relics smuggled from nearby Velkhar ruins"
        ]
    },
    "points_of_interest": [
        {
            "id": "poi_tavern",
            "name": "The Drowned Lantern",
            "type": "tavern",
            "description": "A leaning riverside tavern whose warped floorboards slant toward the water. Lanterns in colored glass hang low, always wreathed in pipe smoke and fog drifting through cracked shutters.",
            "hidden_function": "quest_hub"
        },
        {
            "id": "poi_docks",
            "name": "Blackwater Docks",
            "type": "docks",
            "description": "A creaking maze of piers and ramshackle warehouses where flat-bottomed barges and low-slung riverboats load cargo in the mist.",
            "hidden_function": "thieves_meet"
        },
        {
            "id": "poi_smith",
            "name": "Greyhook Forge",
            "type": "blacksmith",
            "description": "A squat stone workshop wedged between taller timber buildings, its chimney coughing thin, acrid smoke into the fog.",
            "hidden_function": "faction_front"
        },
        {
            "id": "poi_temple",
            "name": "Shrine of the Veiled Tide",
            "type": "temple",
            "description": "A modest riverstone shrine to a local river-and-fate goddess, its interior thick with candles and votive charms carved from bone and driftwood.",
            "hidden_function": "thieves_meet"
        },
        {
            "id": "poi_market",
            "name": "Mistward Market",
            "type": "market",
            "description": "A cramped square where stalls lean against one another, awnings sagging with constant dew as merchants hawk cheap trinkets, marsh produce, and contraband.",
            "hidden_function": "faction_front"
        },
        {
            "id": "poi_forest",
            "name": "The Shattered Mire",
            "type": "wild_edge",
            "description": "A stretch of half-sunken woodland and bog just beyond town, riddled with broken Velkhar stones and whispering reeds.",
            "hidden_function": "none"
        }
    ],
    "key_npcs": [
        {
            "name": "Magda Crowell",
            "role": "mayor",
            "location_poi_id": "poi_market",
            "personality_tags": ["pragmatic", "overworked", "secretive"],
            "secret": "Magda quietly tolerates smuggling as long as it keeps Raven's Hollow alive and the lord's taxmen satisfied.",
            "knows_about": ["thieves_guild_activity", "recent_velkhar_relic_sightings"]
        },
        {
            "name": "Jorren Greyhook",
            "role": "blacksmith",
            "location_poi_id": "poi_smith",
            "personality_tags": ["gruff", "loyal", "haunted"],
            "secret": "Jorren once served as a soldier in a failed expedition to claim a nearby Velkhar fortress; he left comrades behind to die.",
            "knows_about": ["old_ruin_locations", "iron_vanguard_failures"]
        },
        {
            "name": "Sister Lysaen",
            "role": "priest",
            "location_poi_id": "poi_temple",
            "personality_tags": ["soft_spoken", "observant", "morally_conflicted"],
            "secret": "She launders coin and relics for the local Thieves' Guild through temple offerings, telling herself it keeps violence out of the streets.",
            "knows_about": ["thieves_guild_leaders", "smuggling_routes"]
        },
        {
            "name": "Verris Blackflag",
            "role": "traveler",
            "location_poi_id": "poi_tavern",
            "personality_tags": ["nervous", "paranoid", "desperate"],
            "secret": "The locked chest he guards contains a Velkhar shard tied to the ancient Sundering; several factions are hunting it.",
            "knows_about": ["velkhar_relic_value", "pursuing_faction_agents"]
        },
        {
            "name": "Captain Hadrik Thorne",
            "role": "guard_captain",
            "location_poi_id": "poi_docks",
            "personality_tags": ["tired", "proud", "easily_bribed"],
            "secret": "He accepts bribes from the Merchants' Guild to ignore certain cargo, but fears the Iron Vanguard will eventually investigate.",
            "knows_about": ["guild_influence", "border_skirmish_rumors"]
        }
    ],
    "local_realm": {
        "lord_name": "Lord Alaric Denswyrm",
        "lord_holding_name": "Denswyrm Keep",
        "distance_from_town": "1 day ride to the northeast",
        "capital_name": "Valdrath's Crown",
        "capital_distance": "3 to 4 days ride inland",
        "local_tensions": [
            "Increasing taxes imposed on Raven's Hollow to fund distant border defenses.",
            "Resentment among dockworkers and carters toward the lord's riders.",
            "Whispers that Lord Denswyrm sells relics to foreign buyers."
        ]
    },
    "factions": [
        {
            "name": "The Royal Court of Valdrath's Crown",
            "type": "political",
            "influence_scope": "kingdom",
            "public_goal": "Maintain stability and keep Valdrath unified under the king.",
            "secret_goal": "Manipulate succession to place a controllable heir on the throne.",
            "representative_npc_idea": "A silver-tongued chancellor who sponsors expeditions to Velkhar ruins."
        },
        {
            "name": "The Gilded Chain Merchants' Consortium",
            "type": "economic",
            "influence_scope": "kingdom",
            "public_goal": "Secure trade routes and maximize profit across Valdrath and beyond.",
            "secret_goal": "Monopolize the flow of Velkhar relics and strategic resources like Blackwater trade.",
            "representative_npc_idea": "An ambitious factor stationed near Raven's Hollow to buy relics and undercut local traders."
        },
        {
            "name": "Velkhar Remnant Circle",
            "type": "arcane",
            "influence_scope": "kingdom",
            "public_goal": "Study the ruins of the Velkhar Dominion to prevent another catastrophe.",
            "secret_goal": "Reconstruct fragments of the Dominion's god-binding ritual to control its power.",
            "representative_npc_idea": "A veiled scholar seeking a specific shard rumored to have reached Raven's Hollow."
        },
        {
            "name": "The Iron Vanguard",
            "type": "military",
            "influence_scope": "kingdom",
            "public_goal": "Defend Valdrath's borders and uphold royal law.",
            "secret_goal": "Secure strategic Velkhar sites before foreign powers or internal rivals can claim them.",
            "representative_npc_idea": "A hard-bitten captain moving through the region with too few soldiers and too many orders."
        }
    ],
    "macro_conflicts": {
        "local": [
            "Livestock and even people have gone missing near the Shattered Mire, with strange tracks leading toward old Velkhar ruins.",
            "Thieves' Guild smugglers are moving relics through the Shrine of the Veiled Tide, drawing dangerous attention.",
            "Dockside brawls between local carters and guild-backed merchants are turning bloodier each week."
        ],
        "realm": [
            "King Tristram III has no clear heir, and nobles quietly position themselves for a looming succession crisis.",
            "Border clashes with raiders from the Dusklands are increasing, stretching the Iron Vanguard thin.",
            "Rumors spread that some lords are secretly negotiating with foreign powers for protection."
        ],
        "world": [
            "Velkhar relics are awakening across the continent, causing magical anomalies from distant deserts to northern ice.",
            "Tensions rise between Valdrath and the Sapphire Coast over tariffs and relic smuggling.",
            "Whispers claim that an unknown power is collating Velkhar knowledge across borders."
        ]
    },
    "external_regions": [
        {
            "name": "The Dusklands",
            "direction": "east",
            "summary": "A war-scoured expanse of broken kingdoms and raider clans, where old siege engines rot on bloodstained plains.",
            "relationship_to_kingdom": "hostile"
        },
        {
            "name": "The Sapphire Coast",
            "direction": "south",
            "summary": "A chain of wealthy city-states glittering along a warm sea, thriving on trade, tariffs, and piracy by other names.",
            "relationship_to_kingdom": "tense"
        },
        {
            "name": "The Frozen Verge",
            "direction": "north",
            "summary": "An icy wilderness of glaciers, black cliffs, and lost fortresses where only mad explorers and exiles dare to go.",
            "relationship_to_kingdom": "ally"
        },
        {
            "name": "Eldertide Isles",
            "direction": "west",
            "summary": "Scattered storm-lashed islands haunted by pirates, exiled nobles, and strange sea cults.",
            "relationship_to_kingdom": "tense"
        }
    ],
    "exotic_sites": [
        {
            "name": "The Scorched Waste",
            "type": "desert",
            "summary": "A far desert of black glass dunes and half-buried Velkhar citadels, said to be where the first god-binding went wrong.",
            "rumors": [
                "Some dunes are made of fused bone and sand.",
                "At night, distant cities of light appear on the horizon and vanish by dawn."
            ]
        },
        {
            "name": "Shadowmere",
            "type": "ruins",
            "summary": "A vast marsh where drowned Velkhar libraries lie beneath peat and murky waters, guarded by warped fey and worse.",
            "rumors": [
                "Books in Shadowmere still whisper their contents into the dreams of those nearby.",
                "Those who drink its water sometimes wake speaking forgotten languages."
            ]
        },
        {
            "name": "The Aether Nexus",
            "type": "phenomenon",
            "summary": "A spiraling rift of light and shadow above the open sea, said to be a wound in the sky left by the Sundering.",
            "rumors": [
                "Ships passing too near return with days missing from their logs.",
                "Stars reflected in the Nexus's waters are not the same as those in the sky."
            ]
        }
    ],
    "global_threat": {
        "name": "The Second Binding",
        "description": "Scattered factions across Valdrath and beyond, knowingly or not, are reassembling the knowledge and relics needed to attempt the Velkhar god-binding ritual again—on a grander scale.",
        "early_signs_near_starting_town": [
            "Multiple unaffiliated agents have arrived in Raven's Hollow asking quiet questions about Velkhar shards.",
            "Minor magical anomalies flicker around relics moving through the Shattered Mire and the Shrine of the Veiled Tide.",
            "Refugees and traders report strange lights in the sky above distant ruins when the fog briefly parts."
        ]
    }
}
