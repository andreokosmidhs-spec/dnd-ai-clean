"""
Quest Generator Service
Dynamically generates quests based on world context and character traits
"""
import logging
import random
from typing import Dict, List, Any, Optional
from models.quest_models import (
    Quest, QuestObjective, QuestGiver, QuestRewards,
    QuestRequirements, QuestGenerationContext
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# QUEST GENERATION ALGORITHMS
# ═══════════════════════════════════════════════════════════════

def generate_quests(
    world_blueprint: Dict[str, Any],
    character_state: Optional[Dict[str, Any]],
    world_state: Dict[str, Any],
    campaign_id: str,
    count: int = 3
) -> List[Quest]:
    """
    Generate multiple quests based on world context
    
    Args:
        world_blueprint: Immutable world blueprint from campaign
        character_state: Character state (optional for character-specific quests)
        world_state: Current mutable world state
        campaign_id: Campaign ID
        count: Number of quests to generate
    
    Returns:
        List of generated Quest objects
    """
    logger.info(f"🎲 Generating {count} quests for campaign {campaign_id}")
    
    quests = []
    sources = _select_quest_sources(world_blueprint, character_state, world_state)
    
    for i in range(count):
        # Select quest source with weighted randomization
        source = _weighted_random_choice(sources)
        
        # Generate quest based on source type
        if source["type"] == "npc":
            quest = _generate_npc_quest(source["data"], world_blueprint, character_state, campaign_id)
        elif source["type"] == "faction":
            quest = _generate_faction_quest(source["data"], world_blueprint, character_state, campaign_id)
        elif source["type"] == "poi":
            quest = _generate_poi_quest(source["data"], world_blueprint, character_state, campaign_id)
        elif source["type"] == "threat":
            quest = _generate_threat_quest(source["data"], world_blueprint, character_state, campaign_id)
        elif source["type"] == "background":
            quest = _generate_background_quest(source["data"], world_blueprint, character_state, campaign_id)
        else:
            logger.warning(f"Unknown quest source type: {source['type']}")
            continue
        
        if quest:
            quests.append(quest)
            logger.info(f"✅ Generated quest: {quest.name} ({quest.archetype}, {quest.difficulty})")
    
    logger.info(f"🎊 Generated {len(quests)} quests successfully")
    return quests


def _select_quest_sources(
    world_blueprint: Dict[str, Any],
    character_state: Optional[Dict[str, Any]],
    world_state: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Select potential quest sources from world context
    
    Returns:
        List of quest sources with weights: [{type, data, weight}, ...]
    """
    sources = []
    current_location = world_state.get("current_location", "")
    
    # NPC-based quests
    for npc in world_blueprint.get("key_npcs", []):
        if npc.get("secret"):
            # Higher weight if NPC is at current location
            weight = 4 if npc.get("location_poi_id") == current_location else 2
            sources.append({"type": "npc", "data": npc, "weight": weight})
    
    # Faction quests
    for faction in world_blueprint.get("factions", []):
        if faction.get("secret_goal"):
            sources.append({"type": "faction", "data": faction, "weight": 2})
    
    # POI-based quests
    for poi in world_blueprint.get("points_of_interest", []):
        if poi.get("hidden_function"):
            # Higher weight if POI is current location or nearby
            weight = 3 if poi.get("id") == current_location else 1
            sources.append({"type": "poi", "data": poi, "weight": weight})
    
    # Threat-based quests (main storyline)
    if world_blueprint.get("global_threat"):
        sources.append({"type": "threat", "data": world_blueprint["global_threat"], "weight": 5})
    
    # Character background quests
    if character_state and character_state.get("background"):
        sources.append({"type": "background", "data": character_state["background"], "weight": 2})
    
    logger.info(f"📋 Found {len(sources)} potential quest sources")
    return sources


def _weighted_random_choice(sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Select random source based on weights"""
    if not sources:
        return {"type": "generic", "data": {}, "weight": 1}
    
    total_weight = sum(s["weight"] for s in sources)
    rand = random.uniform(0, total_weight)
    
    current = 0
    for source in sources:
        current += source["weight"]
        if rand <= current:
            return source
    
    return sources[-1]  # Fallback


# ═══════════════════════════════════════════════════════════════
# QUEST GENERATION BY SOURCE TYPE
# ═══════════════════════════════════════════════════════════════

def _generate_npc_quest(
    npc: Dict[str, Any],
    world_blueprint: Dict[str, Any],
    character_state: Optional[Dict[str, Any]],
    campaign_id: str
) -> Quest:
    """Generate quest from NPC with secret"""
    secret = npc.get("secret", "unknown secret")
    npc_name = npc.get("name", "Unknown NPC")
    npc_id = npc.get("id", f"npc_{random.randint(1000, 9999)}")
    location_id = npc.get("location_poi_id", "unknown_location")
    
    # Generate quest name
    quest_name = f"{npc_name}'s Request: {secret[:50]}"
    
    # Generate objectives based on NPC's "knows_about"
    objectives = []
    knows_about = npc.get("knows_about", [])
    
    for i, knowledge in enumerate(knows_about[:3]):  # Max 3 objectives
        if "location" in knowledge.lower() or "ruins" in knowledge.lower() or "temple" in knowledge.lower():
            # Go to location objective
            target_location = _extract_location_from_text(knowledge, world_blueprint)
            objectives.append(QuestObjective(
                type="go_to",
                description=f"Travel to {knowledge}",
                target=target_location,
                target_type="location",
                order=i+1
            ))
        elif "cult" in knowledge.lower() or "threat" in knowledge.lower() or "enemy" in knowledge.lower():
            # Investigate or kill objective
            if "investigate" in secret.lower():
                objectives.append(QuestObjective(
                    type="investigate",
                    description=f"Investigate {knowledge}",
                    target=location_id,
                    target_type="location",
                    count=2,
                    order=i+1
                ))
            else:
                objectives.append(QuestObjective(
                    type="kill",
                    description=f"Defeat enemies related to {knowledge}",
                    target=_guess_enemy_type(knowledge),
                    target_type="enemy",
                    count=3,
                    order=i+1
                ))
        else:
            # Generic interact objective
            objectives.append(QuestObjective(
                type="interact",
                description=f"Speak with {npc_name} about {knowledge}",
                target=npc_id,
                target_type="npc",
                order=i+1
            ))
    
    # If no objectives from knows_about, create generic fetch quest
    if not objectives:
        objectives.append(QuestObjective(
            type="interact",
            description=f"Return to {npc_name} for more information",
            target=npc_id,
            target_type="npc",
            order=1
        ))
    
    # Calculate rewards based on objectives and character level
    char_level = character_state.get("level", 1) if character_state else 1
    xp_reward = len(objectives) * 50 * char_level
    gold_reward = len(objectives) * 25 * char_level
    
    # Determine difficulty and archetype
    difficulty = "easy" if len(objectives) <= 1 else ("medium" if len(objectives) <= 2 else "hard")
    archetype = _determine_archetype(objectives)
    
    return Quest(
        campaign_id=campaign_id,
        name=quest_name,
        summary=f"{npc_name} needs help with: {secret}",
        description=f"{npc_name} has approached you with urgent news. {secret}. They need someone trustworthy to handle this delicate matter.",
        giver=QuestGiver(type="npc", npc_id=npc_id, location_id=location_id),
        objectives=objectives,
        rewards=QuestRewards(xp=xp_reward, gold=gold_reward),
        requirements=QuestRequirements(min_level=max(1, char_level - 1)),
        generation_context=QuestGenerationContext(
            source_type="world_blueprint",
            source_npc_id=npc_id,
            character_background=character_state.get("background") if character_state else None,
            threat_level=len(objectives)
        ),
        difficulty=difficulty,
        archetype=archetype,
        tags=["npc", "story"]
    )


def _generate_faction_quest(
    faction: Dict[str, Any],
    world_blueprint: Dict[str, Any],
    character_state: Optional[Dict[str, Any]],
    campaign_id: str
) -> Quest:
    """Generate quest from faction"""
    faction_name = faction.get("name", "Unknown Faction")
    faction_id = faction_name.lower().replace(" ", "_")
    secret_goal = faction.get("secret_goal", "unknown goal")
    public_goal = faction.get("public_goal", "help the people")
    
    quest_name = f"{faction_name} Mission: {public_goal[:50]}"
    
    # Faction quests typically involve multiple objectives
    objectives = [
        QuestObjective(
            type="interact",
            description=f"Meet with {faction_name} representative",
            target=f"npc_{faction_id}_rep",
            target_type="npc",
            order=1
        ),
        QuestObjective(
            type="investigate",
            description=f"Gather intelligence for {faction_name}",
            target="poi_faction_interest",
            target_type="location",
            count=3,
            order=2
        )
    ]
    
    # Add faction-specific objective based on type
    faction_type = faction.get("type", "guild")
    if "military" in faction_type.lower() or "guard" in faction_type.lower():
        objectives.append(QuestObjective(
            type="kill",
            description="Eliminate hostile forces",
            target="bandit",
            target_type="enemy",
            count=5,
            order=3
        ))
    elif "merchant" in faction_type.lower() or "guild" in faction_type.lower():
        objectives.append(QuestObjective(
            type="deliver",
            description="Deliver important goods",
            target=f"npc_{faction_id}_contact",
            target_type="npc",
            order=3
        ))
    
    char_level = character_state.get("level", 1) if character_state else 1
    xp_reward = 100 * char_level
    gold_reward = 75 * char_level
    
    return Quest(
        campaign_id=campaign_id,
        name=quest_name,
        summary=f"{faction_name} needs assistance with their operations.",
        description=f"The {faction_name} has been working towards: {public_goal}. They need capable individuals to help advance their cause.",
        giver=QuestGiver(type="faction", faction_id=faction_id),
        objectives=objectives,
        rewards=QuestRewards(
            xp=xp_reward,
            gold=gold_reward,
            reputation={faction_id: 15}
        ),
        requirements=QuestRequirements(min_level=char_level),
        generation_context=QuestGenerationContext(
            source_type="faction",
            source_faction=faction_id,
            character_background=character_state.get("background") if character_state else None,
            threat_level=2
        ),
        difficulty="medium",
        archetype="investigation",
        tags=["faction", "reputation"]
    )


def _generate_poi_quest(
    poi: Dict[str, Any],
    world_blueprint: Dict[str, Any],
    character_state: Optional[Dict[str, Any]],
    campaign_id: str
) -> Quest:
    """Generate quest from point of interest"""
    poi_name = poi.get("name", "Unknown Location")
    poi_id = poi.get("id", f"poi_{random.randint(1000, 9999)}")
    poi_type = poi.get("type", "ruins")
    hidden_function = poi.get("hidden_function", "unknown secret")
    
    quest_name = f"Explore {poi_name}"
    
    # POI quests are exploration-focused
    objectives = [
        QuestObjective(
            type="go_to",
            description=f"Travel to {poi_name}",
            target=poi_id,
            target_type="location",
            order=1
        ),
        QuestObjective(
            type="discover",
            description=f"Uncover the secret of {poi_name}",
            target=f"{poi_id}_secret",
            target_type="item",
            order=2
        )
    ]
    
    # Add combat if dangerous location
    if poi_type in ["ruins", "dungeon", "cave", "crypt"]:
        objectives.append(QuestObjective(
            type="kill",
            description=f"Clear {poi_name} of threats",
            target=_guess_enemy_type_from_poi(poi_type),
            target_type="enemy",
            count=4,
            order=3
        ))
    
    char_level = character_state.get("level", 1) if character_state else 1
    xp_reward = len(objectives) * 60 * char_level
    gold_reward = len(objectives) * 30 * char_level
    
    return Quest(
        campaign_id=campaign_id,
        name=quest_name,
        summary=f"Investigate the mysterious {poi_name}.",
        description=f"{poi_name} has long been a source of rumors and mystery. Recent reports suggest: {hidden_function}. It's time someone investigated.",
        giver=QuestGiver(type="environment", location_id=poi_id),
        objectives=objectives,
        rewards=QuestRewards(
            xp=xp_reward,
            gold=gold_reward,
            unlocks=[poi_id]
        ),
        requirements=QuestRequirements(min_level=char_level),
        generation_context=QuestGenerationContext(
            source_type="world_blueprint",
            source_poi_id=poi_id,
            character_background=character_state.get("background") if character_state else None,
            threat_level=3
        ),
        difficulty="hard" if poi_type in ["dungeon", "crypt"] else "medium",
        archetype="exploration",
        tags=["exploration", "dungeon", "discovery"]
    )


def _generate_threat_quest(
    threat: Dict[str, Any],
    world_blueprint: Dict[str, Any],
    character_state: Optional[Dict[str, Any]],
    campaign_id: str
) -> Quest:
    """Generate quest from global threat (main storyline)"""
    threat_name = threat.get("name", "Unknown Threat")
    threat_description = threat.get("description", "A great danger approaches")
    early_signs = threat.get("early_signs_near_starting_town", [])
    
    quest_name = f"Investigate: {threat_name}"
    
    objectives = []
    for i, sign in enumerate(early_signs[:3]):
        if "disappear" in sign.lower() or "missing" in sign.lower():
            objectives.append(QuestObjective(
                type="investigate",
                description=f"Investigate: {sign}",
                target="poi_investigation_site",
                target_type="location",
                count=2,
                order=i+1
            ))
        elif "sighting" in sign.lower() or "creature" in sign.lower():
            objectives.append(QuestObjective(
                type="kill",
                description=f"Deal with threat: {sign}",
                target="threat_creature",
                target_type="enemy",
                count=2,
                order=i+1
            ))
    
    if not objectives:
        objectives.append(QuestObjective(
            type="investigate",
            description=f"Gather information about {threat_name}",
            target="poi_starting_town",
            target_type="location",
            count=3,
            order=1
        ))
    
    char_level = character_state.get("level", 1) if character_state else 1
    xp_reward = 150 * char_level
    gold_reward = 100 * char_level
    
    return Quest(
        campaign_id=campaign_id,
        name=quest_name,
        summary=f"The threat of {threat_name} looms. Investigation is needed.",
        description=f"{threat_description}. Recent signs near town suggest this threat is growing. Someone must investigate before it's too late.",
        giver=QuestGiver(type="environment"),
        objectives=objectives,
        rewards=QuestRewards(xp=xp_reward, gold=gold_reward),
        requirements=QuestRequirements(min_level=char_level),
        generation_context=QuestGenerationContext(
            source_type="threat",
            character_background=character_state.get("background") if character_state else None,
            threat_level=4
        ),
        difficulty="hard",
        archetype="investigation",
        tags=["main", "threat", "story", "urgent"]
    )


def _generate_background_quest(
    background: str,
    world_blueprint: Dict[str, Any],
    character_state: Optional[Dict[str, Any]],
    campaign_id: str
) -> Quest:
    """Generate quest tailored to character background"""
    char_level = character_state.get("level", 1) if character_state else 1
    
    # Background-specific quest templates
    if background.lower() == "criminal":
        return _generate_criminal_quest(campaign_id, char_level)
    elif background.lower() == "acolyte":
        return _generate_acolyte_quest(campaign_id, char_level)
    elif background.lower() == "soldier":
        return _generate_soldier_quest(campaign_id, char_level)
    elif background.lower() == "noble":
        return _generate_noble_quest(campaign_id, char_level)
    elif background.lower() == "folk hero":
        return _generate_folk_hero_quest(campaign_id, char_level)
    else:
        return _generate_generic_quest(campaign_id, char_level, background)


# ═══════════════════════════════════════════════════════════════
# BACKGROUND-SPECIFIC QUEST GENERATORS
# ═══════════════════════════════════════════════════════════════

def _generate_criminal_quest(campaign_id: str, char_level: int) -> Quest:
    """Generate criminal/thieves guild quest"""
    return Quest(
        campaign_id=campaign_id,
        name="The Midnight Heist",
        summary="The thieves guild needs someone to acquire a valuable item.",
        description="Word on the street is that a wealthy merchant has acquired a rare artifact. The guild wants it, and they're willing to pay well for someone with light fingers and quick wits.",
        giver=QuestGiver(type="faction", faction_id="thieves_guild"),
        objectives=[
            QuestObjective(
                type="go_to",
                description="Scout the merchant's warehouse",
                target="poi_warehouse",
                target_type="location",
                order=1
            ),
            QuestObjective(
                type="discover",
                description="Find the artifact without raising alarm",
                target="rare_artifact",
                target_type="item",
                order=2
            )
        ],
        rewards=QuestRewards(xp=80*char_level, gold=100*char_level, reputation={"thieves_guild": 10}),
        requirements=QuestRequirements(min_level=char_level),
        generation_context=QuestGenerationContext(
            source_type="character_background",
            character_background="criminal",
            threat_level=2
        ),
        difficulty="medium",
        archetype="fetch",
        tags=["stealth", "thieves", "background"]
    )


def _generate_acolyte_quest(campaign_id: str, char_level: int) -> Quest:
    """Generate religious/acolyte quest"""
    return Quest(
        campaign_id=campaign_id,
        name="Purify the Sacred Shrine",
        summary="A sacred shrine has been defiled and needs cleansing.",
        description="The local temple has received troubling reports of dark energies emanating from an ancient shrine. The priests need someone faithful to investigate and cleanse the corruption.",
        giver=QuestGiver(type="npc", npc_id="npc_high_priest", location_id="poi_temple"),
        objectives=[
            QuestObjective(
                type="go_to",
                description="Travel to the defiled shrine",
                target="poi_shrine",
                target_type="location",
                order=1
            ),
            QuestObjective(
                type="kill",
                description="Banish the corrupted spirits",
                target="undead",
                target_type="enemy",
                count=3,
                order=2
            ),
            QuestObjective(
                type="interact",
                description="Return to the high priest",
                target="npc_high_priest",
                target_type="npc",
                order=3
            )
        ],
        rewards=QuestRewards(xp=90*char_level, gold=60*char_level, items=["Blessed Amulet"]),
        requirements=QuestRequirements(min_level=char_level),
        generation_context=QuestGenerationContext(
            source_type="character_background",
            character_background="acolyte",
            threat_level=2
        ),
        difficulty="medium",
        archetype="kill",
        tags=["religious", "undead", "background"]
    )


def _generate_soldier_quest(campaign_id: str, char_level: int) -> Quest:
    """Generate military/soldier quest"""
    return Quest(
        campaign_id=campaign_id,
        name="Secure the Border Outpost",
        summary="Military command needs the border outpost secured.",
        description="Enemy forces have been spotted near the border outpost. Command needs experienced soldiers to assess the situation and eliminate any threats.",
        giver=QuestGiver(type="faction", faction_id="city_guard"),
        objectives=[
            QuestObjective(
                type="go_to",
                description="Travel to the border outpost",
                target="poi_outpost",
                target_type="location",
                order=1
            ),
            QuestObjective(
                type="kill",
                description="Eliminate hostile forces",
                target="bandit",
                target_type="enemy",
                count=5,
                order=2
            )
        ],
        rewards=QuestRewards(xp=100*char_level, gold=80*char_level, reputation={"city_guard": 15}),
        requirements=QuestRequirements(min_level=char_level),
        generation_context=QuestGenerationContext(
            source_type="character_background",
            character_background="soldier",
            threat_level=3
        ),
        difficulty="medium",
        archetype="kill",
        tags=["military", "combat", "background"]
    )


def _generate_noble_quest(campaign_id: str, char_level: int) -> Quest:
    """Generate noble/court intrigue quest"""
    return Quest(
        campaign_id=campaign_id,
        name="Navigate the Court Politics",
        summary="A noble house needs assistance with delicate political matters.",
        description="The noble families are engaged in subtle warfare of words and influence. Your connection to nobility makes you uniquely positioned to navigate these treacherous waters.",
        giver=QuestGiver(type="npc", npc_id="npc_lord", location_id="poi_manor"),
        objectives=[
            QuestObjective(
                type="interact",
                description="Speak with Lady Ravencrest",
                target="npc_lady_ravencrest",
                target_type="npc",
                order=1
            ),
            QuestObjective(
                type="interact",
                description="Negotiate with Lord Blackwood",
                target="npc_lord_blackwood",
                target_type="npc",
                order=2
            )
        ],
        rewards=QuestRewards(xp=70*char_level, gold=120*char_level, reputation={"noble_house": 10}),
        requirements=QuestRequirements(min_level=char_level),
        generation_context=QuestGenerationContext(
            source_type="character_background",
            character_background="noble",
            threat_level=1
        ),
        difficulty="easy",
        archetype="social",
        tags=["social", "intrigue", "background"]
    )


def _generate_folk_hero_quest(campaign_id: str, char_level: int) -> Quest:
    """Generate folk hero/defender quest"""
    return Quest(
        campaign_id=campaign_id,
        name="Defend the Village",
        summary="Bandits are threatening a helpless village.",
        description="A small farming village is being terrorized by bandits. The people are defenseless and need a hero to stand up for them.",
        giver=QuestGiver(type="npc", npc_id="npc_village_elder", location_id="poi_village"),
        objectives=[
            QuestObjective(
                type="interact",
                description="Speak with the village elder",
                target="npc_village_elder",
                target_type="npc",
                order=1
            ),
            QuestObjective(
                type="kill",
                description="Drive off the bandits",
                target="bandit",
                target_type="enemy",
                count=4,
                order=2
            )
        ],
        rewards=QuestRewards(xp=85*char_level, gold=50*char_level, items=["Villager's Gratitude Token"]),
        requirements=QuestRequirements(min_level=char_level),
        generation_context=QuestGenerationContext(
            source_type="character_background",
            character_background="folk hero",
            threat_level=2
        ),
        difficulty="medium",
        archetype="kill",
        tags=["heroic", "village", "background"]
    )


def _generate_generic_quest(campaign_id: str, char_level: int, background: str) -> Quest:
    """Generate generic quest for any background"""
    return Quest(
        campaign_id=campaign_id,
        name="A Call for Adventurers",
        summary="Standard adventuring work available.",
        description="The local tavern has a job board with various opportunities for capable adventurers.",
        giver=QuestGiver(type="npc", npc_id="npc_innkeeper", location_id="poi_tavern"),
        objectives=[
            QuestObjective(
                type="go_to",
                description="Check the location mentioned on the job board",
                target="poi_job_site",
                target_type="location",
                order=1
            ),
            QuestObjective(
                type="investigate",
                description="Complete the job",
                target="poi_job_site",
                target_type="location",
                count=2,
                order=2
            )
        ],
        rewards=QuestRewards(xp=60*char_level, gold=40*char_level),
        requirements=QuestRequirements(min_level=char_level),
        generation_context=QuestGenerationContext(
            source_type="character_background",
            character_background=background,
            threat_level=1
        ),
        difficulty="easy",
        archetype="fetch",
        tags=["generic", "background"]
    )


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _extract_location_from_text(text: str, world_blueprint: Dict[str, Any]) -> str:
    """Extract location ID from text using world_blueprint POIs"""
    pois = world_blueprint.get("points_of_interest", [])
    
    # Try to match POI names in text
    for poi in pois:
        if poi.get("name", "").lower() in text.lower():
            return poi.get("id", "unknown_location")
    
    # Fallback: generate generic location ID
    return f"poi_{text.lower().replace(' ', '_')[:20]}"


def _guess_enemy_type(text: str) -> str:
    """Guess enemy archetype from text"""
    text_lower = text.lower()
    
    if "cult" in text_lower or "cultist" in text_lower:
        return "cultist"
    elif "undead" in text_lower or "zombie" in text_lower or "skeleton" in text_lower:
        return "undead"
    elif "bandit" in text_lower or "thief" in text_lower or "raider" in text_lower:
        return "bandit"
    elif "beast" in text_lower or "wolf" in text_lower or "bear" in text_lower:
        return "beast"
    elif "dragon" in text_lower or "serpent" in text_lower:
        return "dragon"
    else:
        return "hostile_creature"


def _guess_enemy_type_from_poi(poi_type: str) -> str:
    """Guess enemy type based on POI type"""
    poi_type_lower = poi_type.lower()
    
    if poi_type_lower in ["ruins", "temple", "shrine"]:
        return "undead"
    elif poi_type_lower in ["cave", "lair"]:
        return "beast"
    elif poi_type_lower in ["dungeon", "fortress"]:
        return "bandit"
    elif poi_type_lower in ["crypt", "tomb"]:
        return "undead"
    else:
        return "hostile_creature"


def _determine_archetype(objectives: List[QuestObjective]) -> str:
    """Determine quest archetype from objectives"""
    objective_types = [obj.type for obj in objectives]
    
    if "escort" in objective_types:
        return "escort"
    elif "kill" in objective_types and len([o for o in objectives if o.type == "kill"]) >= 2:
        return "kill"
    elif "investigate" in objective_types:
        return "investigation"
    elif "interact" in objective_types and len(objectives) == 1:
        return "social"
    elif "discover" in objective_types or "go_to" in objective_types:
        return "exploration"
    else:
        return "fetch"
