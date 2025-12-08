# DUNGEON FORGE Quest System Architecture
## Complete Design Specification

**Document Version:** 1.0  
**Date:** November 24, 2025  
**Status:** ARCHITECTURAL SPECIFICATION  
**Author:** Quest-Architect Agent

---

## Executive Summary

This document defines a complete Quest System for DUNGEON FORGE that generates, persists, tracks, and resolves quests dynamically based on world context, character traits, and gameplay events.

**Design Goals:**
1. ✅ Dynamic quest generation tied to world_blueprint and character context
2. ✅ Clean separation: Quests as first-class MongoDB documents (not embedded in world_state)
3. ✅ Rich quest lifecycle state machine
4. ✅ Integration with existing world_state for objective tracking
5. ✅ REST API for quest management
6. ✅ MongoDB write reliability (verification reads, logging)

---

## 1. QUEST DATA MODEL

### MongoDB Schema: `quests` Collection

**Primary Document Structure:**
```json
{
  "_id": ObjectId("..."),
  "quest_id": "uuid-v4-string",
  "campaign_id": "uuid-v4-string",
  "character_id": "uuid-v4-string | null",
  
  "name": "The Lost Artifact of Thalassar",
  "summary": "The merchant guild needs someone to recover an ancient relic from the sunken ruins.",
  "description": "Long-form quest description with lore and context",
  
  "status": "available",
  "lifecycle_state": {
    "generated_at": "ISO timestamp",
    "accepted_at": "ISO timestamp | null",
    "started_at": "ISO timestamp | null",
    "completed_at": "ISO timestamp | null",
    "failed_at": "ISO timestamp | null"
  },
  
  "giver": {
    "type": "npc | faction | environment",
    "npc_id": "npc_merchant_guild_leader | null",
    "faction_id": "merchant_guild | null",
    "location_id": "poi_marketplace"
  },
  
  "objectives": [
    {
      "objective_id": "uuid-v4-string",
      "type": "go_to | kill | interact | discover | deliver | escort | investigate",
      "description": "Travel to the Sunken Ruins of Thalassar",
      "target": "poi_sunken_ruins",
      "target_type": "location | npc | enemy | item",
      "count": 1,
      "progress": 0,
      "completed": false,
      "order": 1
    },
    {
      "objective_id": "uuid-v4-string",
      "type": "kill",
      "description": "Defeat the guardian serpent",
      "target": "sea_serpent",
      "target_type": "enemy",
      "count": 1,
      "progress": 0,
      "completed": false,
      "order": 2
    }
  ],
  
  "rewards": {
    "xp": 250,
    "gold": 100,
    "items": ["Ancient Medallion", "Scroll of Water Breathing"],
    "reputation": {
      "merchant_guild": 10,
      "city_guard": 5
    },
    "unlocks": ["poi_secret_passage"]
  },
  
  "requirements": {
    "min_level": 2,
    "required_items": [],
    "required_quests": [],
    "reputation_gates": {}
  },
  
  "generation_context": {
    "source_type": "world_blueprint | character_background | faction | threat",
    "source_poi_id": "poi_marketplace",
    "source_npc_id": "npc_merchant_leader",
    "source_faction": "merchant_guild",
    "character_goal_alignment": "wealth",
    "character_background": "criminal",
    "threat_level": 2
  },
  
  "failure_conditions": [
    "npc_merchant_leader_killed",
    "faction_merchant_guild_hostile",
    "time_limit_exceeded"
  ],
  
  "time_limit": {
    "type": "turns | days | none",
    "value": 10,
    "started_at": "ISO timestamp | null"
  },
  
  "tags": ["main", "faction", "timed", "dungeon", "combat"],
  "difficulty": "medium",
  "archetype": "fetch | kill | escort | investigation | social | exploration",
  
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp"
}
```

### Pydantic Models

**Quest Objective Model:**
```python
class QuestObjective(BaseModel):
    objective_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # go_to, kill, interact, discover, deliver, escort, investigate
    description: str
    target: str
    target_type: str  # location, npc, enemy, item
    count: int = 1
    progress: int = 0
    completed: bool = False
    order: int = 1
```

**Quest Giver Model:**
```python
class QuestGiver(BaseModel):
    type: str  # npc, faction, environment
    npc_id: Optional[str] = None
    faction_id: Optional[str] = None
    location_id: Optional[str] = None
```

**Quest Rewards Model:**
```python
class QuestRewards(BaseModel):
    xp: int = 0
    gold: int = 0
    items: List[str] = Field(default_factory=list)
    reputation: Dict[str, int] = Field(default_factory=dict)
    unlocks: List[str] = Field(default_factory=list)
```

**Quest Lifecycle State Model:**
```python
class QuestLifecycleState(BaseModel):
    generated_at: datetime
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
```

**Quest Requirements Model:**
```python
class QuestRequirements(BaseModel):
    min_level: int = 1
    required_items: List[str] = Field(default_factory=list)
    required_quests: List[str] = Field(default_factory=list)
    reputation_gates: Dict[str, int] = Field(default_factory=dict)
```

**Quest Time Limit Model:**
```python
class QuestTimeLimit(BaseModel):
    type: str = "none"  # turns, days, none
    value: int = 0
    started_at: Optional[datetime] = None
```

**Quest Generation Context Model:**
```python
class QuestGenerationContext(BaseModel):
    source_type: str  # world_blueprint, character_background, faction, threat
    source_poi_id: Optional[str] = None
    source_npc_id: Optional[str] = None
    source_faction: Optional[str] = None
    character_goal_alignment: Optional[str] = None
    character_background: Optional[str] = None
    threat_level: int = 1
```

**Main Quest Model:**
```python
class Quest(BaseModel):
    quest_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    campaign_id: str
    character_id: Optional[str] = None
    
    name: str
    summary: str
    description: str
    
    status: str = "available"  # available, accepted, in_progress, completed, failed, abandoned
    lifecycle_state: QuestLifecycleState = Field(default_factory=QuestLifecycleState)
    
    giver: QuestGiver
    objectives: List[QuestObjective] = Field(default_factory=list)
    rewards: QuestRewards = Field(default_factory=QuestRewards)
    requirements: QuestRequirements = Field(default_factory=QuestRequirements)
    
    generation_context: QuestGenerationContext
    failure_conditions: List[str] = Field(default_factory=list)
    time_limit: QuestTimeLimit = Field(default_factory=QuestTimeLimit)
    
    tags: List[str] = Field(default_factory=list)
    difficulty: str = "medium"  # easy, medium, hard, deadly
    archetype: str = "fetch"  # fetch, kill, escort, investigation, social, exploration
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Quest Document Model (MongoDB):**
```python
class QuestDoc(BaseModel):
    quest_id: str
    campaign_id: str
    character_id: Optional[str]
    quest_data: Quest
    created_at: datetime
    updated_at: datetime
```

---

## 2. QUEST LIFECYCLE STATE MACHINE

### States

```
available → accepted → in_progress → completed
                ↓            ↓
            abandoned     failed
```

**State Definitions:**

1. **available**: Quest generated, not yet accepted by character
   - Visible in quest board/NPC dialogue
   - Can check requirements
   - Can accept if requirements met

2. **accepted**: Character has accepted quest, objectives not started
   - Assigned to character_id
   - Waiting for first objective progress
   - Can abandon

3. **in_progress**: At least one objective has progress > 0
   - Active gameplay
   - Tracking objective progress
   - Can abandon or fail

4. **completed**: All objectives complete, rewards pending
   - XP/gold/items awarded
   - Reputation updated
   - Unlocks activated
   - Quest archived

5. **failed**: Quest failed due to failure condition
   - Failure condition triggered (NPC killed, time expired, etc.)
   - No rewards
   - Quest archived

6. **abandoned**: Player chose to abandon quest
   - No rewards
   - Quest archived
   - Can potentially re-accept if available again

### State Transitions

| From | To | Trigger | Validation |
|------|-----|---------|------------|
| available | accepted | POST /quests/accept | Requirements met, character exists |
| accepted | in_progress | First objective progress | Automatic on first update_quest_progress() |
| accepted | abandoned | POST /quests/abandon | Character owns quest |
| in_progress | completed | All objectives complete | Automatic check on objective update |
| in_progress | failed | Failure condition | Check failure conditions |
| in_progress | abandoned | POST /quests/abandon | Character owns quest |

### Lifecycle Tracking Fields

```python
lifecycle_state = {
    "generated_at": datetime,      # When quest was created
    "accepted_at": datetime|None,  # When character accepted
    "started_at": datetime|None,   # When first objective progress made
    "completed_at": datetime|None, # When all objectives complete
    "failed_at": datetime|None     # When quest failed
}
```

---

## 3. QUEST OBJECTIVES SYSTEM

### Objective Types

**1. go_to (Travel to Location)**
```python
{
    "type": "go_to",
    "description": "Travel to the Sunken Ruins",
    "target": "poi_sunken_ruins",
    "target_type": "location",
    "count": 1,
    "progress": 0
}
```
**Completion:** `update_quest_progress(event={"type": "entered_location", "location_id": "poi_sunken_ruins"})`

**2. kill (Defeat Enemies)**
```python
{
    "type": "kill",
    "description": "Defeat 3 cultists",
    "target": "cultist",
    "target_type": "enemy",
    "count": 3,
    "progress": 0
}
```
**Completion:** `update_quest_progress(event={"type": "enemy_killed", "enemy_archetype": "cultist"})` (called 3 times)

**3. interact (Talk to NPC)**
```python
{
    "type": "interact",
    "description": "Speak with the Elder",
    "target": "npc_elder",
    "target_type": "npc",
    "count": 1,
    "progress": 0
}
```
**Completion:** `update_quest_progress(event={"type": "talked_to", "npc_id": "npc_elder"})`

**4. discover (Find Hidden Thing)**
```python
{
    "type": "discover",
    "description": "Find the hidden passage",
    "target": "secret_passage",
    "target_type": "item",
    "count": 1,
    "progress": 0
}
```
**Completion:** `update_quest_progress(event={"type": "discovered", "discovery_id": "secret_passage"})`

**5. deliver (Bring Item to NPC)**
```python
{
    "type": "deliver",
    "description": "Deliver the letter to Captain Ilya",
    "target": "npc_captain_ilya",
    "target_type": "npc",
    "count": 1,
    "progress": 0,
    "required_item": "sealed_letter"
}
```
**Completion:** `update_quest_progress(event={"type": "delivered", "npc_id": "npc_captain_ilya", "item": "sealed_letter"})`

**6. escort (Protect NPC to Location)**
```python
{
    "type": "escort",
    "description": "Escort merchant to marketplace",
    "target": "poi_marketplace",
    "target_type": "location",
    "count": 1,
    "progress": 0,
    "escort_npc_id": "npc_merchant"
}
```
**Completion:** `update_quest_progress(event={"type": "escorted", "npc_id": "npc_merchant", "location_id": "poi_marketplace"})`

**7. investigate (Search Location for Clues)**
```python
{
    "type": "investigate",
    "description": "Search the warehouse for evidence",
    "target": "poi_warehouse",
    "target_type": "location",
    "count": 3,
    "progress": 0
}
```
**Completion:** `update_quest_progress(event={"type": "clue_found", "location_id": "poi_warehouse"})` (called 3 times)

### Objective Ordering

Objectives have an `order` field to support:
- **Sequential quests:** Objective 2 unlocks only after objective 1 completes
- **Parallel quests:** All objectives available simultaneously (order just for UI display)

**Implementation:**
```python
if quest.requires_sequential_completion:
    # Only show objectives where all previous objectives are complete
    available_objectives = [obj for obj in objectives if all(
        prev_obj.completed for prev_obj in objectives if prev_obj.order < obj.order
    )]
else:
    # All objectives available
    available_objectives = objectives
```

---

## 4. QUEST GENERATION ALGORITHM

### Input Sources

**1. world_blueprint:**
- `key_npcs`: Quest givers with secrets, knows_about
- `points_of_interest`: Quest locations with hidden_function
- `factions`: Faction quests, reputation requirements
- `global_threat`: Main storyline quests
- `macro_conflicts`: Regional conflict quests

**2. character_state:**
- `goal`: Tailor quests to character motivation (vengeance, wealth, knowledge)
- `background`: Criminal → thieves guild quests; Noble → court intrigue
- `level`: Scale quest difficulty
- `reputation`: Lock quests behind faction reputation

**3. world_state:**
- `current_location`: Generate location-specific quests
- `active_npcs`: Use present NPCs as quest givers
- `transgressions`: Redemption quests, "clear your name"
- `bounties`: Turn tables with counter-quests

### Generation Algorithm (High-Level)

**Step 1: Select Quest Source**
```python
def select_quest_source(world_blueprint, character_state, world_state):
    sources = []
    
    # NPC-based quests (from NPCs with secrets)
    for npc in world_blueprint["key_npcs"]:
        if npc.get("secret") and npc["location_poi_id"] == world_state["current_location"]:
            sources.append({"type": "npc", "npc": npc, "weight": 3})
    
    # Faction quests (from factions with goals)
    for faction in world_blueprint["factions"]:
        if faction["representative_npc_idea"] in world_state["active_npcs"]:
            sources.append({"type": "faction", "faction": faction, "weight": 2})
    
    # POI-based quests (from locations with hidden functions)
    for poi in world_blueprint["points_of_interest"]:
        if poi.get("hidden_function"):
            sources.append({"type": "poi", "poi": poi, "weight": 1})
    
    # Threat-based quests (from global threat)
    if world_blueprint.get("global_threat"):
        sources.append({"type": "threat", "threat": world_blueprint["global_threat"], "weight": 4})
    
    # Character background quests (tailored to background)
    if character_state["background"] == "criminal":
        sources.append({"type": "background", "background": "criminal", "weight": 2})
    
    return weighted_random_choice(sources)
```

**Step 2: Generate Quest from Source**
```python
def generate_quest_from_npc(npc, world_blueprint, character_state):
    quest_name = f"{npc['secret']} - {npc['name']}'s Request"
    
    # Use NPC's secret as quest hook
    secret = npc["secret"]
    
    # Use NPC's knows_about as quest objectives
    objectives = []
    for knowledge in npc.get("knows_about", []):
        if "location" in knowledge:
            objectives.append({
                "type": "go_to",
                "description": f"Travel to {knowledge}",
                "target": extract_location_id(knowledge, world_blueprint),
                "target_type": "location"
            })
        elif "cult" in knowledge or "threat" in knowledge:
            objectives.append({
                "type": "investigate",
                "description": f"Investigate {knowledge}",
                "target": extract_location_id(knowledge, world_blueprint),
                "target_type": "location"
            })
    
    # Add combat objective if threat-related
    if "threat" in secret.lower() or "cult" in secret.lower():
        objectives.append({
            "type": "kill",
            "description": "Defeat the cultists",
            "target": "cultist",
            "target_type": "enemy",
            "count": 3
        })
    
    # Calculate rewards based on objectives and character level
    xp_reward = len(objectives) * 50 * character_state["level"]
    gold_reward = len(objectives) * 20 * character_state["level"]
    
    return Quest(
        name=quest_name,
        summary=f"{npc['name']} needs help with: {secret}",
        giver=QuestGiver(type="npc", npc_id=npc["id"], location_id=npc["location_poi_id"]),
        objectives=objectives,
        rewards=QuestRewards(xp=xp_reward, gold=gold_reward),
        generation_context=QuestGenerationContext(
            source_type="world_blueprint",
            source_npc_id=npc["id"],
            character_background=character_state["background"],
            threat_level=len(objectives)
        )
    )
```

**Step 3: Validate Quest**
```python
def validate_quest(quest, world_blueprint):
    # Ensure all objective targets exist in world_blueprint
    for objective in quest.objectives:
        if objective.target_type == "location":
            assert objective.target in [poi["id"] for poi in world_blueprint["points_of_interest"]]
        elif objective.target_type == "npc":
            assert objective.target in [npc["id"] for npc in world_blueprint["key_npcs"]]
        # Enemy targets are valid if they match expected archetypes (not pre-defined in blueprint)
    
    return True
```

### Quest Templates by Character Background

**Criminal:**
- Fetch quests for thieves guild
- Heist objectives (steal item)
- Escape/evade objectives
- Underworld contacts

**Acolyte:**
- Religious artifact retrieval
- Purify corrupted locations
- Convert/redeem NPCs
- Divine revelation investigations

**Soldier:**
- Tactical combat missions
- Escort military NPCs
- Capture strategic locations
- Defeat specific enemy commanders

**Noble:**
- Social intrigue (persuade NPCs)
- Faction diplomacy
- Protect reputation
- Attend/infiltrate events

**Folk Hero:**
- Defend village/townspeople
- Defeat oppressors (tyrants, bandits)
- Rally allies
- Expose corruption

---

## 5. REST API ENDPOINTS

### 5.1. Generate Quests

**Endpoint:** `POST /api/quests/generate`

**Request:**
```json
{
  "campaign_id": "uuid",
  "character_id": "uuid | null",
  "count": 3,
  "filters": {
    "difficulty": "medium | hard",
    "archetype": "fetch | kill | escort",
    "source_location": "poi_marketplace"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "quests": [
      {
        "quest_id": "uuid",
        "name": "The Lost Artifact",
        "summary": "...",
        "status": "available",
        "giver": {...},
        "objectives": [...],
        "rewards": {...},
        "requirements": {...}
      }
    ],
    "count": 3
  },
  "error": null
}
```

### 5.2. List Quests

**Endpoint:** `GET /api/quests/by-campaign/{campaign_id}`

**Query Params:**
- `status`: Filter by status (available, accepted, in_progress, completed)
- `character_id`: Filter by character
- `archetype`: Filter by archetype

**Response:**
```json
{
  "success": true,
  "data": {
    "quests": [...],
    "count": 10
  },
  "error": null
}
```

**Endpoint:** `GET /api/quests/by-character/{character_id}`

Returns quests assigned to character (accepted, in_progress, completed, failed).

### 5.3. Get Quest Details

**Endpoint:** `GET /api/quests/{quest_id}`

**Response:**
```json
{
  "success": true,
  "data": {
    "quest": {...}
  },
  "error": null
}
```

### 5.4. Accept Quest

**Endpoint:** `POST /api/quests/accept`

**Request:**
```json
{
  "quest_id": "uuid",
  "character_id": "uuid"
}
```

**Validation:**
- Quest status must be "available"
- Character must meet requirements (level, reputation, items)
- Character must exist

**Response:**
```json
{
  "success": true,
  "data": {
    "quest": {...},
    "status": "accepted"
  },
  "error": null
}
```

### 5.5. Update Quest Progress

**Endpoint:** `POST /api/quests/advance`

**Request:**
```json
{
  "quest_id": "uuid",
  "event": {
    "type": "enemy_killed | entered_location | talked_to | discovered",
    "target": "enemy_archetype | location_id | npc_id | item_id",
    "context": {}
  }
}
```

**Logic:**
- Match event to objectives
- Increment progress
- Check if objective completed
- Check if all objectives completed → auto-complete quest
- Check failure conditions

**Response:**
```json
{
  "success": true,
  "data": {
    "quest": {...},
    "objectives_updated": [
      {
        "objective_id": "uuid",
        "progress": 2,
        "completed": false
      }
    ],
    "quest_completed": false
  },
  "error": null
}
```

### 5.6. Complete Quest

**Endpoint:** `POST /api/quests/complete`

**Request:**
```json
{
  "quest_id": "uuid",
  "character_id": "uuid"
}
```

**Logic:**
- Verify all objectives complete
- Award rewards (XP, gold, items)
- Update character reputation
- Unlock new quests/locations
- Set status to "completed"

**Response:**
```json
{
  "success": true,
  "data": {
    "quest": {...},
    "rewards_applied": {
      "xp": 250,
      "gold": 100,
      "items": ["Ancient Medallion"],
      "reputation": {"merchant_guild": 10}
    },
    "character_updates": {
      "current_xp": 350,
      "level": 2,
      "level_up": true
    }
  },
  "error": null
}
```

### 5.7. Fail Quest

**Endpoint:** `POST /api/quests/fail`

**Request:**
```json
{
  "quest_id": "uuid",
  "reason": "time_expired | npc_killed | faction_hostile"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "quest": {...},
    "status": "failed",
    "failure_reason": "time_expired"
  },
  "error": null
}
```

### 5.8. Abandon Quest

**Endpoint:** `POST /api/quests/abandon`

**Request:**
```json
{
  "quest_id": "uuid",
  "character_id": "uuid"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "quest": {...},
    "status": "abandoned"
  },
  "error": null
}
```

---

## 6. INTEGRATION WITH EXISTING SYSTEMS

### 6.1. Integration with world_state

**Current:** `world_state.quests` stores quest dicts embedded in world_state document.

**New:** Quests are separate documents in `quests` collection.

**Migration Strategy:**
- Keep `world_state.quests` for backward compatibility (deprecated)
- New quests go to `quests` collection
- Add `world_state.active_quest_ids` array to reference quest documents

**Quest Objective Updates:**
When DM response includes `world_state_update`, check for events:
```python
async def check_quest_events(world_state_update, campaign_id, character_id):
    events = []
    
    # Location change → go_to objective
    if "current_location" in world_state_update:
        events.append({
            "type": "entered_location",
            "location_id": world_state_update["current_location"]
        })
    
    # Active NPCs change → interact objective
    if "active_npcs" in world_state_update:
        for npc_id in world_state_update["active_npcs"]:
            # Check if player action was "talk to X"
            if player_action_mentions_npc(npc_id):
                events.append({
                    "type": "talked_to",
                    "npc_id": npc_id
                })
    
    # Combat victory → kill objective
    if combat_just_ended and combat_outcome == "victory":
        for enemy in defeated_enemies:
            events.append({
                "type": "enemy_killed",
                "enemy_archetype": enemy["archetype"]
            })
    
    # Update all active quests for character
    for event in events:
        await update_quest_progress(campaign_id, character_id, event)
```

### 6.2. Integration with Campaigns

**Campaign Document Extension:**
```python
class Campaign(BaseModel):
    # ... existing fields ...
    
    # NEW: Quest metadata
    generated_quest_count: int = 0
    completed_quest_count: int = 0
    failed_quest_count: int = 0
```

### 6.3. Integration with Characters

**Character Document Extension:**
```python
class CharacterState(BaseModel):
    # ... existing fields ...
    
    # NEW: Quest-related fields
    active_quest_ids: List[str] = Field(default_factory=list)
    completed_quest_ids: List[str] = Field(default_factory=list)
    failed_quest_ids: List[str] = Field(default_factory=list)
```

### 6.4. Integration with Combat System

**After combat ends:**
```python
if combat_state.combat_over and combat_state.outcome == "victory":
    for enemy in combat_state.enemies:
        # Trigger quest event
        await update_quest_progress(
            campaign_id,
            character_id,
            event={
                "type": "enemy_killed",
                "enemy_archetype": enemy.name.lower(),
                "enemy_id": enemy.id
            }
        )
```

---

## 7. LOGGING & VERIFICATION

### Write Operations (All require verification reads)

**1. Quest Creation:**
```python
try:
    result = await db.quests.insert_one(quest_dict)
    logger.info(f"✅ Quest created: {quest_dict['name']} ({quest_dict['quest_id']})")
    
    # Verification read
    verify = await db.quests.find_one({"quest_id": quest_dict["quest_id"]})
    if not verify:
        raise RuntimeError(f"Quest insert verification failed: {quest_dict['quest_id']}")
    logger.info(f"✅ VERIFIED: Quest {quest_dict['quest_id']} exists in MongoDB")
    
except Exception as e:
    logger.error(f"❌ Quest creation failed: {e}")
    raise
```

**2. Quest Status Update:**
```python
try:
    result = await db.quests.update_one(
        {"quest_id": quest_id},
        {"$set": {
            "status": new_status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    logger.info(f"✅ Quest status updated: {quest_id} → {new_status}")
    
    # Verification read
    verify = await db.quests.find_one({"quest_id": quest_id})
    if not verify or verify["status"] != new_status:
        raise RuntimeError(f"Quest update verification failed: {quest_id}")
    
except Exception as e:
    logger.error(f"❌ Quest update failed: {e}")
    raise
```

**3. Objective Progress Update:**
```python
logger.info(f"📈 Quest '{quest['name']}' objective progress: {objective['description']} → {objective['progress']}/{objective['count']}")

if objective["progress"] >= objective["count"]:
    objective["completed"] = True
    logger.info(f"✅ Objective completed: {objective['description']}")
```

---

## 8. PERFORMANCE & SCALABILITY

### Indexing Strategy

**MongoDB Indexes:**
```javascript
db.quests.createIndex({ "quest_id": 1 }, { unique: true })
db.quests.createIndex({ "campaign_id": 1, "status": 1 })
db.quests.createIndex({ "character_id": 1, "status": 1 })
db.quests.createIndex({ "status": 1 })
db.quests.createIndex({ "created_at": -1 })
```

**Query Optimization:**
- Use projection to exclude large fields when listing quests
- Paginate quest listings (default 50 per page)
- Cache frequently accessed quests in application memory

---

## 9. TESTING STRATEGY

### Unit Tests

**Test Quest Generation:**
```python
def test_generate_quest_from_npc():
    npc = {
        "id": "npc_1",
        "name": "Elder Sage",
        "secret": "Knows location of ancient temple",
        "knows_about": ["temple ruins", "cult activities"]
    }
    quest = generate_quest_from_npc(npc, world_blueprint, character_state)
    assert quest.name == "Knows location of ancient temple - Elder Sage's Request"
    assert len(quest.objectives) >= 1
```

**Test Quest Lifecycle:**
```python
def test_quest_lifecycle():
    quest = create_quest()
    assert quest.status == "available"
    
    quest = accept_quest(quest, character_id)
    assert quest.status == "accepted"
    
    quest = update_progress(quest, event={"type": "entered_location", "location_id": "poi_1"})
    assert quest.status == "in_progress"
    
    quest = complete_all_objectives(quest)
    assert quest.status == "completed"
```

### Integration Tests

**Test Quest Creation + Persistence:**
```python
async def test_create_quest_endpoint():
    response = await client.post("/api/quests/generate", json={
        "campaign_id": campaign_id,
        "character_id": character_id,
        "count": 1
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert len(data["data"]["quests"]) == 1
    
    # Verify in database
    quest = await db.quests.find_one({"quest_id": data["data"]["quests"][0]["quest_id"]})
    assert quest is not None
```

---

## 10. FUTURE ENHANCEMENTS

**Phase 2 Features:**
1. **Dynamic Quest Chains:** Completing quest A unlocks quest B
2. **Branching Quests:** Player choices affect quest outcomes
3. **Timed Quests:** Real-time deadlines (not turn-based)
4. **Faction Reputation Quests:** Quests that dramatically affect faction standing
5. **Quest Journal UI:** Frontend quest log with filtering/sorting
6. **Quest Hints System:** NPCs provide hints for stuck players
7. **Quest Rewards Preview:** Show rewards before accepting
8. **Quest Difficulty Scaling:** Auto-scale based on character level
9. **Quest Failure Recovery:** Some failed quests can be retried with penalties

---

## ARCHITECTURAL SUMMARY

**Design Principles:**
1. ✅ **Separation of Concerns:** Quests are first-class documents, not embedded in world_state
2. ✅ **Event-Driven Updates:** Quest progress updates via event system
3. ✅ **Dynamic Generation:** Quests generated from world_blueprint + character context
4. ✅ **Rich Lifecycle:** 6-state state machine with timestamps
5. ✅ **Type Safety:** Pydantic models for all data structures
6. ✅ **Verification:** All writes include verification reads
7. ✅ **Integration:** Seamless integration with existing systems
8. ✅ **Scalability:** Indexed queries, pagination, efficient updates

**API Summary:**
- 8 RESTful endpoints
- Standard request/response envelope
- Error handling + logging
- Backward compatible

**Data Model:**
- 1 MongoDB collection: `quests`
- 9 Pydantic models
- 7 objective types
- 6 lifecycle states

**Generation Algorithm:**
- 5 quest sources (NPC, faction, POI, threat, background)
- Character-tailored quest selection
- World context integration
- Validation + fallback logic

---

**End of Architectural Specification**

**Next Phase:** Quest-Engineer will implement backend code based on this spec.
