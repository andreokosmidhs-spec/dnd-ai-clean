"""
Entity Mention Extraction Utility
Simple deterministic substring matching for V1.
Can be upgraded to LLM-based detection later without changing the API shape.
"""
from typing import List, Dict, Literal, TypedDict


EntityType = Literal["npc", "location", "faction", "item"]


class EntityIndexEntry(TypedDict):
    entity_type: EntityType
    entity_id: str
    name: str  # display name


class EntityMention(TypedDict):
    entity_type: EntityType
    entity_id: str
    display_text: str
    start: int
    end: int


def build_entity_index_from_world_blueprint(
    world_blueprint: Dict,
    world_state: Dict = None
) -> List[EntityIndexEntry]:
    """
    Build entity index from DUNGEON FORGE world blueprint structure.
    Extracts NPCs, locations, factions, and quest items.
    """
    index: List[EntityIndexEntry] = []
    
    # Extract NPCs from world blueprint
    if "npcs" in world_blueprint:
        for npc in world_blueprint["npcs"]:
            if "name" in npc and npc["name"]:
                index.append({
                    "entity_type": "npc",
                    "entity_id": npc.get("id", f"npc_{npc['name'].lower().replace(' ', '_')}"),
                    "name": npc["name"]
                })
    
    # Extract locations
    # Starting town
    if "starting_town" in world_blueprint:
        town = world_blueprint["starting_town"]
        if "name" in town and town["name"]:
            index.append({
                "entity_type": "location",
                "entity_id": f"loc_{town['name'].lower().replace(' ', '_')}",
                "name": town["name"]
            })
    
    # Regions
    if "regions" in world_blueprint:
        for region in world_blueprint["regions"]:
            if "name" in region and region["name"]:
                index.append({
                    "entity_type": "location",
                    "entity_id": f"loc_{region['name'].lower().replace(' ', '_')}",
                    "name": region["name"]
                })
            
            # Locations within region
            if "locations" in region:
                for loc in region["locations"]:
                    if isinstance(loc, str):
                        index.append({
                            "entity_type": "location",
                            "entity_id": f"loc_{loc.lower().replace(' ', '_')}",
                            "name": loc
                        })
                    elif isinstance(loc, dict) and "name" in loc:
                        index.append({
                            "entity_type": "location",
                            "entity_id": f"loc_{loc['name'].lower().replace(' ', '_')}",
                            "name": loc["name"]
                        })
    
    # Extract factions
    if "factions" in world_blueprint:
        for faction in world_blueprint["factions"]:
            if "name" in faction and faction["name"]:
                index.append({
                    "entity_type": "faction",
                    "entity_id": f"faction_{faction['name'].lower().replace(' ', '_')}",
                    "name": faction["name"]
                })
    
    # Extract quest items from world state (if available)
    if world_state:
        if "inventory" in world_state:
            for item in world_state.get("inventory", []):
                if isinstance(item, dict) and "name" in item:
                    index.append({
                        "entity_type": "item",
                        "entity_id": item.get("id", f"item_{item['name'].lower().replace(' ', '_')}"),
                        "name": item["name"]
                    })
        
        # Quest items from quests
        if "quests" in world_state:
            for quest in world_state.get("quests", []):
                if "rewards" in quest:
                    for reward in quest.get("rewards", []):
                        if isinstance(reward, dict) and "name" in reward:
                            index.append({
                                "entity_type": "item",
                                "entity_id": reward.get("id", f"item_{reward['name'].lower().replace(' ', '_')}"),
                                "name": reward["name"]
                            })
    
    # Sort by descending name length to avoid short-name collisions
    # (e.g., match "Thieves Haven" before "Haven")
    index.sort(key=lambda e: len(e["name"]), reverse=True)
    
    return index


def extract_entity_mentions(
    narration: str,
    entity_index: List[EntityIndexEntry],
) -> List[EntityMention]:
    """
    Simple substring-based mention extractor.
    - Case-insensitive search
    - Returns non-overlapping mentions (longest names win)
    - V1: Deterministic, no LLM needed
    - V2: Can upgrade to LLM-based detection without changing API shape
    """
    mentions: List[EntityMention] = []
    used_ranges: List[range] = []
    
    lower_text = narration.lower()
    
    def overlaps(start: int, end: int) -> bool:
        """Check if this range overlaps with any already-used range"""
        for r in used_ranges:
            if not (end <= r.start or start >= r.stop):
                return True
        return False
    
    for entry in entity_index:
        name = entry["name"]
        name_lower = name.lower()
        
        # Find first occurrence
        pos = lower_text.find(name_lower)
        if pos == -1:
            continue
        
        start = pos
        end = pos + len(name)
        
        if overlaps(start, end):
            # Already covered by another (longer) mention
            continue
        
        used_ranges.append(range(start, end))
        
        mentions.append({
            "entity_type": entry["entity_type"],
            "entity_id": entry["entity_id"],
            "display_text": narration[start:end],  # Preserve original case
            "start": start,
            "end": end,
        })
    
    # Sort by start index for frontend convenience
    mentions.sort(key=lambda m: m["start"])
    return mentions


def should_create_knowledge_fact(
    entity_type: str,
    entity_id: str,
    campaign_id: str,
    existing_facts: List[Dict]
) -> bool:
    """
    Check if we should create a new KnowledgeFact for this entity.
    Returns True if this is the first mention (no existing fact).
    """
    for fact in existing_facts:
        if (fact.get("entity_type") == entity_type and 
            fact.get("entity_id") == entity_id and
            fact.get("campaign_id") == campaign_id):
            return False
    return True

