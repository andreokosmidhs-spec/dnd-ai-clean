# SCENE GENERATION ARCHITECTURE REPORT
## Technical Deep-Dive for Quest System Development

**Document Version:** 1.0  
**Date:** November 24, 2025  
**Purpose:** Provide complete technical documentation of DUNGEON FORGE's scene generation pipeline to inform development of a full quest system with multi-hook narratives.

---

## 1. SCENE GENERATION PIPELINE

### Overview
The scene generation system in DUNGEON FORGE follows a **multi-agent orchestration pattern** where player actions flow through a series of specialized services before reaching the AI DM, which generates narrative scenes with embedded game state updates.

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                  PLAYER ACTION INPUT                             │
│          (via /api/rpg_dm/action endpoint)                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: STATE LOADING (Parallelized MongoDB Queries)            │
│ - Campaign document (world_blueprint)                            │
│ - Character document (character_state)                           │
│ - World state document (world_state)                             │
│ - Combat document (combat_state)                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: NPC ACTIVATION                                           │
│ Service: npc_activation_service.py                               │
│ - Populates active_npcs for current location                     │
│ - Ensures NPCs have unique IDs in world_blueprint                │
│ - Stores active NPC list in world_state                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: PHASE 1 DMG SYSTEMS (Pacing, Info, Consequences)        │
│                                                                   │
│ A. TENSION MANAGER (pacing_service.py)                           │
│    - Calculates tension score (0-100)                            │
│    - Determines phase: calm/building/tense/climax/resolution     │
│    - Provides pacing instructions for DM narration style         │
│                                                                   │
│ B. INFORMATION DISPENSER (information_service.py)                │
│    - Applies passive Perception auto-reveals                     │
│    - Clarifies active conditions                                 │
│    - Drip-feeds information based on tension                     │
│                                                                   │
│ C. CONSEQUENCE ESCALATION (consequence_service.py)               │
│    - Tracks transgressions by target NPC                         │
│    - Escalates consequences (minor → moderate → severe)          │
│    - Triggers guards/bounties/combat when thresholds met         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: PHASE 2 DMG SYSTEMS (Session Flow, Improvisation, NPCs) │
│                                                                   │
│ A. SESSION FLOW MANAGER (session_flow_service.py)                │
│    - Detects game mode: exploration/conversation/encounter/etc   │
│    - Provides mode-specific narration guidelines                 │
│                                                                   │
│ B. IMPROVISATION ENGINE (improvisation_service.py)               │
│    - Classifies player action: creative/risky/impossible         │
│    - Applies "Yes, and..." / "Yes, but..." / "No, but..."        │
│    - Grants advantage for creativity or adds complications       │
│                                                                   │
│ C. NPC PERSONALITY ENGINE (npc_personality_service.py)           │
│    - Loads personalities for active NPCs (limit 3 for prompt)    │
│    - Includes mannerisms, traits, emotional state, role behavior │
│    - Tracks interaction history                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: CONTEXT MEMORY (context_memory_service.py)              │
│ - Enforces location constraints (no merchants in ruins)          │
│ - Enforces active NPC constraints (only present NPCs)            │
│ - Summarizes ongoing situations (combat, guards, bounties)       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6A: HOSTILE ACTION ROUTING (if applicable)                 │
│ Service: target_resolver.py                                      │
│ - Detects hostile actions (attack keywords)                      │
│ - Resolves target (NPC, enemy, or needs clarification)           │
│ - Checks plot armor (essential NPCs protected)                   │
│ - May trigger combat initiation or consequence escalation        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6B: COMBAT ROUTING (if combat active)                      │
│ Service: combat_engine_service.py                                │
│ - Resolves player attack/action mechanically                     │
│ - Rolls for enemy attacks                                        │
│ - Applies damage, checks HP, updates combat_state                │
│ - Determines if combat ends (victory/defeat)                     │
│ - Passes mechanical_summary to DM for narration                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: INTENT TAGGER (run_intent_tagger)                       │
│ Model: gpt-4o-mini                                               │
│ Input: player_action, character proficiencies                    │
│ Output: {                                                         │
│   needs_check: boolean,                                          │
│   ability: "STR|DEX|CON|INT|WIS|CHA" or null,                   │
│   skill: "Stealth|Perception|..." or null,                       │
│   action_type: "stealth|social|investigation|combat|...",        │
│   risk_level: 0-3                                                │
│ }                                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: BUILD A-VERSION DM PROMPT (build_a_version_dm_prompt)   │
│                                                                   │
│ Assembles comprehensive system prompt with:                      │
│ 1. Mechanical Authority (backend results are law)                │
│ 2. Location & Scene Continuity (location_constraints)            │
│ 3. NPC Personality Engine (npc_personalities formatted)          │
│ 4. Consequence System (transgression summary)                    │
│ 5. Player Agency & Improvisation (improvisation_result)          │
│ 6. Information Dispensing Rules (auto_revealed_info)             │
│ 7. Pacing & Tension System (pacing_instructions)                 │
│ 8. Matt Mercer Narration Framework (session_mode formatted)      │
│ 9. Combat Narration Rules (mechanical_summary if combat)         │
│ 10. Safety Rails & Story Coherence (ongoing_situations)          │
│                                                                   │
│ Character State, World State, World Blueprint embedded           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 9: DUNGEON FORGE (run_dungeon_forge)                       │
│ Model: gpt-4o                                                    │
│ Temperature: 0.7                                                 │
│                                                                   │
│ Input:                                                            │
│ - System Prompt (A-Version, ~6000 tokens)                        │
│ - User Message: player_action + check_result                     │
│                                                                   │
│ Output (JSON):                                                    │
│ {                                                                 │
│   "narration": "string (1-3 paragraphs)",                        │
│   "options": ["string", "string", "string"],                     │
│   "world_state_update": {},                                      │
│   "starts_combat": false,                                        │
│   "check_request": null                                          │
│ }                                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 10: DM RESPONSE VALIDATION (dm_response_validator.py)      │
│ - Checks location continuity (validates against current_location)│
│ - Checks NPC consistency (active_npcs vs mentioned NPCs)         │
│ - Corrects violations automatically                              │
│ - Logs warnings if inconsistencies detected                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 11: WORLD STATE MUTATION                                   │
│ - Merges dm_response.world_state_update into world_state         │
│ - Updates tension_state                                          │
│ - Saves updated world_state to MongoDB                           │
│ - Updates character_state if HP/conditions changed               │
│ - Stores combat_state if combat initiated/updated                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   RESPONSE TO FRONTEND                           │
│ {                                                                 │
│   "narration": "...",                                            │
│   "options": [...],                                              │
│   "world_state_update": {...},                                   │
│   "player_updates": {xp_gained, level_up_events, etc}           │
│ }                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architectural Notes

1. **Parallelized Data Loading:** Campaign, character, world_state, and combat_state are fetched simultaneously using `asyncio.gather()` for performance.

2. **Multi-Agent System:** Each service (pacing, information, consequences, session flow, improvisation, NPC personality) acts as a specialized sub-agent that provides guidance to the central DM agent.

3. **Prompt Assembly:** The "A-Version DM Prompt" is the integration point for all 10 DMG-compliant systems, creating a comprehensive instruction set for the AI DM.

4. **Validation Layer:** After DM response, a validator checks for narrative continuity errors and auto-corrects them.

5. **State Persistence:** World state updates are immediately persisted to MongoDB, maintaining continuity across turns.

---

## 2. INPUT SOURCES USED IN SCENE CREATION

### A. World Blueprint (Immutable Campaign Data)
**Source:** `campaigns` collection, `world_blueprint` field  
**Generated by:** `world_forge_service.py` using `WORLD_FORGE_SYSTEM_PROMPT`  
**Model:** gpt-4o  
**Structure:**
```json
{
  "world_core": {
    "name": "string",
    "tone": "string",
    "magic_level": "string",
    "ancient_event": {
      "name": "string",
      "description": "string",
      "current_legacies": ["string"]
    }
  },
  "starting_region": {
    "name": "string",
    "description": "string",
    "biome_layers": ["string"],
    "notable_features": ["string"]
  },
  "starting_town": {
    "name": "string",
    "role": "string",
    "summary": "string",
    "population_estimate": int,
    "building_estimate": int,
    "signature_products": ["string"]
  },
  "points_of_interest": [
    {
      "id": "string",
      "name": "string",
      "type": "string",
      "description": "string",
      "hidden_function": "string"
    }
  ],
  "key_npcs": [
    {
      "id": "string (added by npc_activation_service)",
      "name": "string",
      "role": "string",
      "location_poi_id": "string",
      "personality_tags": ["string"],
      "secret": "string",
      "knows_about": ["string"]
    }
  ],
  "local_realm": {
    "lord_name": "string",
    "lord_holding_name": "string",
    "distance_from_town": "string",
    "capital_name": "string",
    "capital_distance": "string",
    "local_tensions": ["string"]
  },
  "factions": [
    {
      "name": "string",
      "type": "string",
      "influence_scope": "string",
      "public_goal": "string",
      "secret_goal": "string",
      "representative_npc_idea": "string"
    }
  ],
  "macro_conflicts": {
    "local": ["string"],
    "realm": ["string"],
    "world": ["string"]
  },
  "external_regions": [
    {
      "name": "string",
      "direction": "string",
      "summary": "string",
      "relationship_to_kingdom": "string"
    }
  ],
  "exotic_sites": [
    {
      "name": "string",
      "type": "string",
      "summary": "string",
      "rumors": ["string"]
    }
  ],
  "global_threat": {
    "name": "string",
    "description": "string",
    "early_signs_near_starting_town": ["string"]
  }
}
```

**Usage in Scene Generation:**
- **Location metadata:** Determines what NPCs, mobs, and features are plausible at current location
- **NPC pool:** Provides list of key NPCs that can be activated for scenes
- **Faction context:** Informs consequence escalations (which faction responds)
- **World lore:** Referenced by DM for consistency in narration
- **Hooks and secrets:** POIs contain "hidden_function" and NPCs have "secret" fields (currently underutilized for quest generation)

### B. Campaign Document
**Source:** `campaigns` collection  
**Fields Used:**
- `campaign_id`: Unique identifier
- `world_name`: World name for context
- `world_blueprint`: (see above)
- `intro`: Cinematic intro markdown (generated once, stored for persistence)
- `created_at`, `updated_at`: Timestamps

**Usage:**
- Loaded at start of every action
- `world_blueprint` is passed to DM prompt as immutable world context
- `intro` is retrieved separately for initial game load

### C. World State Document (Mutable Game State)
**Source:** `world_states` collection  
**Structure:**
```json
{
  "campaign_id": "string",
  "world_state": {
    "location": "string (legacy, same as current_location)",
    "current_location": "string (authoritative)",
    "active_npcs": ["npc_id_1", "npc_id_2"],
    "active_conflicts": ["string"],
    "discovered_locations": ["string"],
    "time_of_day": "morning|midday|evening|night",
    "weather": "clear|rain|storm|fog|snow",
    
    // Phase 1: DMG Systems
    "tension_state": {
      "score": 0-100,
      "phase": "calm|building|tense|climax|resolution",
      "previous_phase": "string",
      "phase_changed": boolean,
      "last_updated": "ISO timestamp",
      "phase_duration_minutes": int
    },
    
    // Consequence Tracking (DMG p.32)
    "transgressions": {
      "target_npc_id": [
        {
          "action": "string",
          "severity": "minor|moderate|severe|critical",
          "is_violent": boolean,
          "timestamp": "ISO",
          "escalation_triggered": boolean
        }
      ]
    },
    "consequence_escalations": [
      {
        "from_severity": "string",
        "to_severity": "string",
        "type": "investigation|bounty_and_combat|faction_war",
        "description": "string",
        "mechanical_effect": {},
        "narrative_hint": "string",
        "should_trigger_combat": boolean,
        "escalation_timestamp": "ISO"
      }
    ],
    
    // Guard/Law Enforcement State
    "guard_alert": boolean,
    "guard_suspicion": boolean,
    "guards_hostile": boolean,
    "city_hostile": boolean,
    "bounties": [
      {
        "amount": int,
        "target": "npc_id",
        "reason": "string",
        "active": boolean,
        "posted_at": "ISO"
      }
    ],
    "permanent_enemies": ["faction_id_1"],
    
    // Information System (DMG p.26)
    "location_secrets": [
      {
        "dc": int,
        "information": "string",
        "revealed": boolean
      }
    ],
    
    // Phase 2: NPC Personalities
    "npc_personalities": {
      "npc_id": {
        "name": "string",
        "role": "string",
        "mannerisms": ["string", "string"],
        "personality_trait": "string",
        "ideal": "string",
        "bond": "string",
        "flaw": "string",
        "emotional_state": "friendly|neutral|suspicious|hostile|afraid",
        "role_behavior": {},
        "interaction_history": [],
        "created_at": "ISO"
      }
    },
    
    // Quest System (P3, underutilized)
    "quests": [
      {
        "quest_id": "string",
        "name": "string",
        "status": "active|completed|failed",
        "giver_npc_id": "string",
        "location_id": "string",
        "summary": "string",
        "objectives": [
          {
            "type": "go_to|kill|interact|discover",
            "target": "string (npc_id, location_id, enemy_archetype)",
            "count": int,
            "progress": int
          }
        ],
        "rewards_xp": int,
        "rewards_items": ["string"]
      }
    ]
  },
  "created_at": "ISO",
  "updated_at": "ISO"
}
```

**Usage in Scene Generation:**
- **current_location:** Determines which NPCs, POIs, and environmental details are valid
- **active_npcs:** List of NPC IDs currently present in the scene (enforced strictly by context_memory_service)
- **time_of_day, weather:** Environmental context for DM narration
- **tension_state:** Dictates pacing and narration style (calm vs climax)
- **transgressions, bounties, guards_hostile:** Determines if guards/enemies appear, affects NPC behavior
- **npc_personalities:** Loaded for active NPCs (max 3) and formatted into DM prompt
- **quests:** Quest objectives can auto-update based on scene events (e.g., "talked_to" NPC)

### D. Character State
**Source:** `characters` collection, `character_state` field  
**Structure:**
```json
{
  "name": "string",
  "race": "string",
  "class": "string",
  "background": "string",
  "goal": "string",
  "level": int,
  "hp": int,
  "max_hp": int,
  "ac": int,
  "abilities": {
    "str": int,
    "dex": int,
    "con": int,
    "int": int,
    "wis": int,
    "cha": int
  },
  "proficiencies": ["string"],
  "languages": ["string"],
  "inventory": ["string"],
  "features": ["string"],
  "conditions": ["string"],
  "reputation": {},
  "current_xp": int,
  "xp_to_next": int,
  "proficiency_bonus": int,
  "attack_bonus": int,
  "injury_count": int
}
```

**Usage in Scene Generation:**
- **HP/max_hp:** Used by tension manager to calculate danger level
- **abilities, proficiencies:** Used by intent tagger to determine skill checks
- **conditions:** Clarified by information_service (e.g., "You are poisoned: disadvantage on attacks")
- **level, proficiency_bonus:** Used in combat mechanics
- **inventory, features:** Referenced in narration if relevant
- **goal:** Can be used to tailor quest hooks (underutilized currently)

### E. Last Player Action
**Source:** Request body to `/api/rpg_dm/action`  
**Field:** `player_action` (string)

**Usage:**
- Analyzed by `intent_tagger` to determine action type and skill check needs
- Analyzed by `session_flow_service` to detect game mode
- Analyzed by `improvisation_service` to classify as creative/risky/impossible
- Passed to DM prompt as the primary input for narration

### F. DM Prompt Templates
**Source Files:**
- `prompts.py`: Contains `WORLD_FORGE_SYSTEM_PROMPT` and `INTRO_SYSTEM_PROMPT`
- `dungeon_forge.py`: Contains `build_a_version_dm_prompt()` function (main DM prompt builder)
- `matt_mercer_narration.py`: Contains narration style guidelines
- Various services provide formatted prompt blocks

**Key Prompt Components:**

1. **WORLD_FORGE_SYSTEM_PROMPT:**
   - Used only during world generation
   - Instructs AI to create world_blueprint JSON
   - Not used in scene generation

2. **INTRO_SYSTEM_PROMPT:**
   - Used only during cinematic intro generation
   - Instructs AI to write Matt Mercer-style campaign intro
   - Not used in ongoing scene generation

3. **A-VERSION DM PROMPT (build_a_version_dm_prompt):**
   - **Primary scene generation prompt**
   - ~6000 tokens when fully assembled
   - 10 major sections (see Step 8 in pipeline)
   - Integrates outputs from all services
   - Enforces mechanical authority, location continuity, NPC consistency
   - Provides pacing instructions based on tension
   - Includes Matt Mercer narration guidelines for current mode
   - Specifies JSON output format

### G. Mechanical Combat Results (if combat active)
**Source:** `combat_engine_service.py`  
**Structure:**
```json
{
  "player_attack": {
    "target": "string",
    "total_attack": int,
    "target_ac": int,
    "hit": boolean,
    "critical": boolean,
    "critical_miss": boolean,
    "damage": int,
    "target_hp_remaining": int,
    "target_max_hp": int,
    "target_killed": boolean
  },
  "enemy_turns": [
    {
      "attacker": "string",
      "total_attack": int,
      "hit": boolean,
      "critical": boolean,
      "critical_miss": boolean,
      "damage": int
    }
  ],
  "total_damage_to_player": int,
  "combat_over": boolean,
  "outcome": "victory|player_defeated|null"
}
```

**Usage:**
- Passed to DM as `mechanical_summary` in prompt
- DM **must** narrate results exactly as provided (no overriding)
- Used by `generate_combat_narration_from_mechanical()` to create fallback narration

---

## 3. EXACT SCENE DATA STRUCTURES

### A. DM Response Schema (Primary Scene Output)
**Generated by:** `run_dungeon_forge()` in `dungeon_forge.py`  
**Format:** JSON  
**Fields:**

```json
{
  "narration": "string (1-3 paragraphs of narrative text)",
  "options": [
    "string (suggested player action 1)",
    "string (suggested player action 2)",
    "string (suggested player action 3)"
  ],
  "world_state_update": {
    "active_npcs": ["npc_id_1", "npc_id_2"],
    "current_location": "string (if location changed)",
    "time_of_day": "string (if time advanced)",
    "weather": "string (if weather changed)",
    "discovered_locations": ["string"],
    "quest_flags": {},
    "ANY_OTHER_FIELD": "DM can add arbitrary fields"
  },
  "starts_combat": boolean,
  "check_request": {
    "ability": "STR|DEX|CON|INT|WIS|CHA",
    "dc": int,
    "description": "string (what check is for)"
  } | null
}
```

**Field Semantics:**

- **narration:** Cinematic description of what happens, following Matt Mercer style guidelines for the current session mode. Length varies by mode (encounter: 3-5 sentences, exploration: 3-6 sentences, exposition: 100-250 words).

- **options:** 3-5 suggested next actions. Should be context-appropriate and forward-momentum focused. In combat, these are generated by `generate_combat_options()` based on alive enemies.

- **world_state_update:** Sparse delta update. DM only includes fields that changed. This is merged into `world_state` by the backend. Can include arbitrary new fields.

- **starts_combat:** Boolean flag. If true, backend initiates combat using `combat_engine_service.py` and spawns enemies appropriate to the context.

- **check_request:** If the DM determines a skill check is needed and one hasn't been made yet, this is populated. Frontend will prompt player to roll, then re-submit action with `check_result`.

### B. Combat State Schema
**Generated by:** `combat_engine_service.py`  
**Stored in:** `combats` collection  
**Structure:**

```json
{
  "campaign_id": "string",
  "character_id": "string",
  "combat_state": {
    "enemies": [
      {
        "id": "string",
        "name": "string",
        "hp": int,
        "max_hp": int,
        "ac": int,
        "conditions": ["string"],
        "faction_id": "string",
        "abilities": {"str": int, "dex": int, "con": int},
        "proficiency_bonus": int,
        "attack_bonus": int,
        "damage_die": "string"
      }
    ],
    "participants": [
      {
        "id": "string",
        "name": "string",
        "hp": int,
        "max_hp": int,
        "ac": int,
        "participant_type": "player|enemy|npc",
        "abilities": {},
        "proficiency_bonus": int,
        "attack_bonus": int,
        "damage_die": "string",
        "conditions": [],
        "faction_id": "string",
        "is_essential": boolean,
        "plot_armor_attempts": int
      }
    ],
    "turn_order": ["player", "enemy_1", "enemy_2"],
    "active_turn": "string",
    "round": int,
    "combat_over": boolean,
    "outcome": "victory|fled|player_defeated|null",
    "converted_npcs": ["npc_id_1"]
  },
  "created_at": "ISO",
  "updated_at": "ISO"
}
```

**Usage:**
- Created when `starts_combat: true` or hostile action triggers combat
- Updated each combat turn
- `combat_over` set to true when all enemies dead or player defeated
- NPCs can be converted to enemies via `convert_npc_to_enemy()` function
- `is_essential` NPCs have plot armor (attacks may be blocked or forced non-lethal)

### C. Campaign Intro Schema
**Generated by:** `intro_service.py` using `INTRO_SYSTEM_PROMPT`  
**Stored in:** `campaigns` collection, `intro` field  
**Format:** Markdown string  
**Structure:** 5-section cinematic intro following Matt Mercer Continental Intro pattern:

1. World Scale (2-3 sentences): Name world, ancient event, overall tone
2. Continent/Realm Scale (3-5 sentences): Realm name, geography, compass tour of regions
3. Recent Political/Cultural Conflict (2-4 sentences): Factions, conflict summary, unresolved tension
4. Zoom to Starting Region (2-3 sentences): "Our story begins..." terrain, mood
5. Zoom to Starting City (3-5 sentences): Settlement description, leadership, key NPCs
6. Final Pinpoint (1-2 sentences): "Here, in [CITY NAME]... is where our story begins."

**Usage:**
- Generated once when character is created
- Displayed in frontend before first action
- Stored in campaign document for persistence
- **Not regenerated or used in ongoing scene generation**

### D. Narrative Text Structure (within narration field)
**No enforced schema**, but narration follows these patterns based on session mode:

- **Exploration:** 3-6 sentences. Sensory details, visual anchors, crowd density, notable features. Second person ("You see...").

- **Conversation:** 1-3 sentence NPC dialogue in quotes. Brief action beats. Distinct personalities through tone and mannerisms.

- **Exposition:** 100-250 words. 3-5 concrete facts (who, what, where, when, why). Direct and informative, no purple prose.

- **Encounter (Combat):** 3-5 sentences. Acknowledge roll, describe outcome, add flair (sound/motion/impact), apply conditions. Specific verbs (cleaves, pierces).

- **Investigation:** 2-4 sentences per discovery. Clear clues, layered details (obvious → hidden → secret).

- **Travel:** 4-6 sentences. Compress time (1 sentence), establish new location (2-3 sentences), NPC intro if present (1-2 sentences), end with hook.

---

## 4. SCENE TRANSITION LOGIC

### How the App Decides Scene Changes

**Current Implementation:** Scene transitions are **implicit** rather than explicit. There is no "scene_id" or "scene" object. Instead, scenes are defined by the **state of world_state**, particularly:
- `current_location`
- `active_npcs`
- `time_of_day`
- `tension_state.phase`

**Transition Triggers:**

1. **Location Change:**
   - **Trigger:** DM includes `"current_location": "new_location_name"` in `world_state_update`
   - **Effect:** 
     - `active_npcs` is cleared or updated
     - `npc_activation_service` repopulates NPCs for new location
     - Context memory enforces new location constraints
     - Tension may reset depending on location danger level

2. **Combat Start:**
   - **Trigger:** DM sets `"starts_combat": true` in response
   - **Effect:**
     - Backend calls `combat_engine_service.initiate_combat()`
     - Enemies are spawned based on context (location, world_blueprint, escalation level)
     - `combat_state` document created
     - Subsequent actions route through combat engine until `combat_over: true`

3. **Combat End:**
   - **Trigger:** `combat_state.combat_over` set to true by combat engine
   - **Effect:**
     - XP awarded (via `progression_service.apply_xp_gain()`)
     - Dead enemies removed from scene
     - Tension decreases
     - DM generates "resolution" narration
     - Returns to exploration mode

4. **Time Advancement:**
   - **Trigger:** DM includes `"time_of_day": "evening"` in `world_state_update`
   - **Effect:**
     - Environmental descriptions change (lighting, NPC availability)
     - Certain NPCs may no longer be active (e.g., merchants close shops)
     - No explicit logic currently enforces this; DM decides contextually

5. **Tension Phase Transition:**
   - **Trigger:** Tension score crosses phase threshold (e.g., 40 → 41 = "building" to "tense")
   - **Effect:**
     - `pacing_service` updates `tension_state.phase`
     - `tension_state.phase_changed` set to true
     - Optional transition narration generated (e.g., "The air grows heavy with anticipation...")
     - DM narration style changes (concise → atmospheric → fast-paced)

6. **Session Mode Transition:**
   - **Trigger:** Player action keywords change detected mode (e.g., "I talk to the merchant" → conversation mode)
   - **Effect:**
     - `session_flow_service` updates mode
     - DM receives different narration guidelines
     - No explicit scene break; smooth transition

7. **Quest Objective Completion:**
   - **Trigger:** Event matches quest objective (e.g., player kills required enemy, talks to quest NPC)
   - **Effect:**
     - `quest_service.update_quest_progress()` increments objective progress
     - If all objectives complete, quest status → "completed"
     - XP awarded via `quest_service.complete_quest()`
     - **No automatic scene transition or DM notification** (this is a gap)

8. **Consequence Escalation:**
   - **Trigger:** Transgression count exceeds threshold (e.g., 3 violent actions)
   - **Effect:**
     - `consequence_service` escalates severity
     - May set `world_state.guards_hostile = true`
     - May spawn guards as enemies
     - May start combat automatically
     - Scene shifts from peaceful to hostile encounter

### What Determines Scene Types

**Current System:** Scenes are implicitly typed by **session mode** rather than explicit scene types.

Session modes detected by `session_flow_service.detect_session_mode()`:
- **exploration:** Default. Moving through environment, making decisions.
- **conversation:** Detected by keywords: talk, speak, ask, tell, negotiate, persuade.
- **encounter:** Combat is active.
- **investigation:** Detected by keywords: search, investigate, examine, inspect, look for.
- **travel:** Detected by keywords: travel, journey, go to, head to, walk to.
- **downtime:** Detected by keywords: rest, sleep, shop, buy, sell, prepare, plan.
- **exposition:** Detected by keywords: wait, listen, hear, let them talk, explain, what's going on.

**How it works:**
1. Player submits action
2. `session_flow_service.detect_session_mode()` analyzes action text
3. Mode-specific narration guidelines formatted into DM prompt
4. DM adjusts narration style, length, detail level, and focus accordingly

**Gap:** No explicit "scene start" or "scene end" events. Scenes are continuous, defined by state changes.

---

## 5. LOCATION-BASED LOGIC

### Available Locations

**Source:** `world_blueprint.points_of_interest` + `world_blueprint.starting_town`

**Structure:**
```json
{
  "starting_town": {
    "name": "string",
    "type": "town|city|village",
    "role": "string",
    "summary": "string",
    "population_estimate": int,
    "building_estimate": int,
    "signature_products": ["string"]
  },
  "points_of_interest": [
    {
      "id": "poi_1",
      "name": "The Cracked Tower",
      "type": "ruins|dungeon|landmark|structure|natural_feature",
      "description": "string",
      "hidden_function": "string (e.g., 'thieves guild hideout', 'cult meeting place')"
    }
  ]
}
```

**Dynamic Location Addition:**
- DM can mention new locations in narration
- If player travels there, DM can set `current_location` to new name
- No validation against world_blueprint (DM has creative freedom)
- New locations persist in `world_state.discovered_locations`

### How Scene Interprets Current Location

**Authoritative Field:** `world_state.current_location` (string)

**Location Enforcement Mechanism:**
`context_memory_service.enforce_location_context()` generates strict constraints based on location name keywords:

1. **DANGEROUS RUINS** (keywords: ruin, tower, dungeon, cave, crypt)
   - Constraints: NO merchants/shopkeepers/traders
   - NPCs: Only monsters, undead, dungeon inhabitants, explorers, trapped victims
   - Atmosphere: Dark, dangerous, abandoned

2. **TAVERN/INN** (keywords: tavern, inn, bar)
   - Constraints: Innkeeper, patrons, travelers
   - Atmosphere: Social, busy, public
   - NO dungeon monsters or random merchants

3. **MARKETPLACE** (keywords: market, shop, bazaar, store)
   - NPCs: Merchants, shopkeepers, customers
   - Atmosphere: Commercial, busy, public
   - Focus: Buying/selling

4. **WILDERNESS** (keywords: forest, woods, wilderness, road)
   - NPCs: Travelers, bandits, druids, animals
   - Atmosphere: Natural, isolated
   - NO city NPCs or buildings

5. **GENERAL LOCATION** (fallback)
   - Stay consistent with location type
   - Only introduce NPCs appropriate for setting

**Enforcement Method:**
- Constraints formatted into DM prompt
- DM **must** follow constraints (violation would be flagged by validator)
- Prevents DM from hallucinating merchants in ruins or monsters in taverns

### How Mobs, NPCs, Rumors, Events Tie to Location

**NPCs:**
- `world_blueprint.key_npcs` each have `location_poi_id` field
- When player enters location, `npc_activation_service.populate_active_npcs_for_location()` finds NPCs with matching `location_poi_id`
- NPCs are added to `world_state.active_npcs`
- Only active NPCs are included in scene

**Mobs (Enemies):**
- **Static definition:** `world_blueprint` does NOT contain enemy spawn tables
- **Dynamic spawning:** When `starts_combat: true`, backend calls `enemy_sourcing_service.generate_appropriate_enemies()`
- Enemies are sourced based on:
  - `current_location` (ruins → undead, forest → beasts, town → bandits/guards)
  - `character_state.level` (CR-appropriate enemies)
  - `world_blueprint.world_core.magic_level` (affects enemy types)
  - Escalation context (guards if bounty, cultists if global_threat faction)

**Rumors:**
- Stored in `world_blueprint.exotic_sites[].rumors` and `world_blueprint.global_threat.early_signs_near_starting_town`
- **Not automatically revealed**
- DM can reference them if player talks to NPCs or investigates
- No structured "rumor system" (DM decides contextually)

**Events:**
- No structured event system currently
- `world_state.active_conflicts` exists but is rarely populated
- `world_blueprint.macro_conflicts` provides conflict hooks but is not actively used in scene generation
- Events are driven by DM narration and consequence escalations

### Seeded Hooks/Hints Based on Location

**Current State: Underutilized**

**Available hooks:**
- `world_blueprint.points_of_interest[].hidden_function` (e.g., "thieves guild hideout")
- `world_blueprint.key_npcs[].secret` (e.g., "knows location of cursed artifact")
- `world_blueprint.key_npcs[].knows_about` (e.g., ["cult activities", "hidden tunnel"])
- `world_blueprint.global_threat.early_signs_near_starting_town`

**Problem:**
- These hooks are stored in world_blueprint but **not actively surfaced** by DM
- DM prompt does not include instructions to seed hints or introduce quest hooks
- No system to trigger "curiosity events" or "NPC mentions rumor"
- Players must explicitly ask NPCs questions to trigger information reveals

**Gap for Quest System:**
This is a critical missing piece. A quest system would need:
1. **Hook injection logic:** When player enters location, select relevant hooks from world_blueprint
2. **NPC dialogue seeding:** Format hooks as NPC rumors/comments in DM prompt
3. **Environmental clues:** Instruct DM to include subtle hints in exploration narration
4. **Curiosity triggers:** Passive Perception can reveal quest-related clues

---

## 6. DM PROMPT ANALYSIS

### Full DM Prompt Structure

The `build_a_version_dm_prompt()` function in `/app/backend/routers/dungeon_forge.py` (lines 573-867) constructs the complete system prompt. Here's the breakdown:

#### Section 1: Mechanical Authority
```
Purpose: Ensure DM never overrides backend's mechanical combat results
Content:
- "Backend results are LAW"
- Never override: attack rolls, damage rolls, AC checks, combat results, plot armor, target resolution
- Narration must describe what backend decided
- If mechanical_summary provided, include it with warning: "YOUR NARRATION MUST MATCH THESE RESULTS EXACTLY"
```

#### Section 2: Location & Scene Continuity
```
Purpose: Prevent DM from spawning NPCs/locations not in scene
Content:
- Use ONLY: world_state.current_location, world_state.active_npcs, location metadata
- Rules:
  - Do NOT spawn NPCs/monsters not listed as present
  - Do NOT move player unless player explicitly moves
  - Do NOT introduce new setting, time skip, or teleportation
  - If player searches for impossible ("merchant in ruins"), respond with plausible failure or suggestion
  - Maintain mood, tone, hazards, atmosphere of location
- Includes: location_constraints (formatted by context_memory_service)
```

#### Section 3: NPC Personality Engine
```
Purpose: Make NPCs memorable with distinct personalities
Content:
- Formatted personality blocks for active NPCs (max 3)
- Each includes: name, role, personality trait, mannerisms, ideal, bond, flaw, emotional state, role behavior, interaction history
- CRITICAL RULES:
  - NEVER let essential NPC die unless plot armor allows
  - Use NPC's mannerisms in EVERY dialogue
  - Reflect personality trait and emotional state
  - Speak in role-appropriate style
  - Remember interaction history
- Formatted by: npc_personality_service.format_for_dm_prompt()
```

#### Section 4: Consequence System
```
Purpose: Ensure actions have appropriate, escalating consequences
Content:
- DMG p.32, p.74 guidance
- All actions must have consequences appropriate to: location, social norms, NPC motivations, player reputation
- Levels: Minor → Moderate → Severe → Critical
- Plot armor prevents instant story collapse, NOT consequences
- Current transgression status (e.g., "MODERATE - Under investigation")
- Warning: "Consequences must ESCALATE with repeated offenses"
```

#### Section 5: Player Agency & Improvisation
```
Purpose: "Say Yes" principle - build on player actions
Content:
- Current player action quoted
- Improvisation classification: creative_and_plausible / risky_but_possible / impossible
- Formatted guidance from improvisation_service
- DMG p.28-29 principle: "Say Yes"
- Rules:
  - Build on player actions and ideas
  - Reward creativity with advantage
  - Allow risky actions but add complications
  - Suggest alternatives for impossible actions
- Use phrasing: "Yes, and..." / "Yes, but..." / "No, but you could..."
```

#### Section 6: Information Dispensing Rules
```
Purpose: Control information flow following DMG p.26-27
Content:
- Do NOT info-dump
- Reveal only what player can see/hear/know
- Use passive Perception automatically for obvious things
- Use clarity: no ambiguous hints unless deliberate
- If auto_revealed_info exists: "**PASSIVE PERCEPTION AUTO-REVEALS:** ..."
- If condition_explanations exists: "**ACTIVE CONDITIONS:** ..."
- Warning: "Tell players everything they need to know, but NOT all at once"
```

#### Section 7: Pacing & Tension System
```
Purpose: Adjust narration style based on tension phase
Content:
- Current tension score (0-100) with emoji
- Phase: CALM / BUILDING / TENSE / CLIMAX / RESOLUTION
- Narration style: relaxed / atmospheric / suspenseful / fast-paced / conclusive
- Guidance: (e.g., "Brief, functional narration" for calm, "Fast-paced, exciting, action-focused" for climax)
- Phase descriptions:
  1. Calm → Brief, functional, relaxed
  2. Building → Atmospheric, ominous hints
  3. Tense → Suspenseful, partial reveals
  4. Climax → Fast-paced, exciting, action-focused
  5. Resolution → Conclusive, rewarding, wrap-up
- Instruction: "Adjust your tone, pacing, sentence length, and detail accordingly"
```

#### Section 8: Matt Mercer Narration Framework
```
Purpose: Provide mode-specific narration guidelines
Content:
- Session mode formatted by session_flow_service.format_for_dm_prompt()
- GLOBAL RULES (always apply):
  - Prioritize clarity, pacing, immersion
  - Use sensory detail sparingly and purposefully
  - Keep sentences varied in length
  - Never lecture or drop encyclopedic lore
  - Use second person ("you") for party
  - Use third person for world-scale narration
  - Never override player agency
- Mode-specific guidelines (from matt_mercer_narration.py):
  - exploration → vivid but concise (3-6 sentences)
  - conversation → short NPC lines (1-3 sentences each)
  - exposition → concrete facts (3-5 pieces of info)
  - encounter → cinematic action (3-5 sentences)
  - investigation → clear clues (2-4 sentences)
  - travel → smooth transitions (4-6 sentences)
```

#### Section 9: Combat Narration Rules
```
Purpose: Ensure combat narration matches mechanical results
Content:
- When mechanical combat is active:
  - Start narration ONLY after backend mechanical summary
  - Never add mechanics not in summary
  - Use dynamic, moment-to-moment descriptions
  - Keep turns clear: player → enemies → new round
- When combat ends:
  - Summarize outcome
  - Describe environment aftermath
  - Return to free-form narration
- Combat state: "ACTIVE - Follow mechanical summary above" or "NOT ACTIVE"
```

#### Section 10: Safety Rails & Story Coherence
```
Purpose: Prevent DM from breaking continuity
Content:
- No lore contradictions
- No temporal jumps
- No untriggered revelations
- No introducing characters who shouldn't exist in current scene
- Always check ongoing_situations before narrating
- Includes: ongoing_situations (formatted by context_memory_service)
- WARNING: "DO NOT introduce NPCs or locations not listed above!"
- WARNING: "Stay in the current location and scene!"
```

#### Embedded Context
```
Content:
- CURRENT WORLD STATE: location, time, weather
- CHARACTER STATE: name, class, HP/max_HP, level
- INTENT FLAGS: JSON from intent_tagger
- CORE OUTPUT FORMAT:
  {
    "narration": "string (1-3 paragraphs, cinematic and grounded)",
    "options": ["array of 3-5 suggested actions"],
    "world_state_update": {},
    "starts_combat": boolean
  }
```

### Which Parts Set Environmental Details

**Location & Scene Continuity (Section 2):**
- `current_location` (e.g., "The Cracked Tower")
- `time_of_day` (e.g., "evening")
- `weather` (e.g., "rain")
- Location constraints (e.g., "RUINS/DUNGEON - Dark, dangerous, abandoned")

**Pacing & Tension (Section 7):**
- Atmosphere direction (e.g., "Atmospheric, ominous hints" for building phase)

**Matt Mercer Guidelines (Section 8):**
- Sensory detail instructions ("sparingly and purposefully")
- Mode-specific focus (exploration mode: "vivid but concise", "sensory, not encyclopedic")

**DM Autonomy:**
- DM has creative freedom to generate specific environmental descriptions within constraints
- No pre-defined "room descriptions" or "location details" in world_blueprint
- DM extrapolates from `world_blueprint.points_of_interest[].description` and location type

### Which Parts Set NPC Behavior

**NPC Personality Engine (Section 3):**
- **Primary driver of NPC behavior**
- Includes: personality trait (e.g., "suspicious"), mannerisms (e.g., "whispers even when not necessary"), emotional state (e.g., "hostile"), role behavior (e.g., guard: "formal and direct")
- Interaction history: Shows previous player actions and NPC emotional state changes
- Directive: "Use NPC's mannerisms in EVERY dialogue interaction"

**Consequence System (Section 4):**
- If player has transgressions against NPC, affects NPC emotional state
- Guards become hostile if `world_state.guards_hostile = true`

**Location Constraints (Section 2):**
- Limits which NPCs can appear (e.g., no merchants in ruins)

**Matt Mercer Conversation Mode (Section 8):**
- In conversation mode: "Focus on NPC personality and dialogue"
- "Use NPC's voice, mannerisms, emotional state"
- "Don't make it a skill challenge - let it flow naturally"

### Which Parts Determine Possible Events

**No Explicit Event System.** Events emerge from:

1. **Consequence Escalation (Section 4):**
   - Repeated transgressions → guards investigate → bounty posted → guards attack
   - This is the primary "event trigger" mechanism

2. **Tension System (Section 7):**
   - High tension (climax phase) → DM likely to introduce combat or crisis
   - Low tension (calm phase) → DM focuses on social/exploration

3. **Improvisation Classification (Section 5):**
   - Risky actions → DM adds complication (event: "attention drawn", "unforeseen consequence")

4. **Combat Initiation:**
   - If `starts_combat: true`, combat event begins

5. **DM Creative Freedom:**
   - DM can introduce events based on world_blueprint context (e.g., `global_threat`, `macro_conflicts`)
   - No structured "event table" or "random encounter" system

### Which Parts Determine Hooks/Leads

**Current State: NO EXPLICIT HOOK SYSTEM**

**Potential Hook Sources (underutilized):**
- `world_blueprint.key_npcs[].secret` - Not currently surfaced by DM
- `world_blueprint.key_npcs[].knows_about` - Not currently surfaced by DM
- `world_blueprint.points_of_interest[].hidden_function` - Not currently surfaced by DM
- `world_blueprint.global_threat.early_signs_near_starting_town` - Occasionally referenced by DM but not systematically

**Why Hooks Don't Surface:**
- DM prompt does not include instructions to "seed quest hooks"
- No section dedicated to "introduce plot leads" or "mention rumors"
- NPCs share information only when player explicitly asks
- No proactive "curiosity triggers" or "overheard conversation" mechanics

**Gap:** This is the biggest architectural gap for a quest system.

### Which Parts Structure Output Scene

**Core Output Format (Section 10, bottom):**
Specifies JSON schema for DM response.

**Matt Mercer Guidelines (Section 8):**
- Defines sentence count per mode (e.g., exploration: 3-6 sentences, encounter: 3-5 sentences)
- Defines structure for each mode (e.g., travel: 1 sentence time compression + 2-3 sentences new location + 1 line NPC + hook)

**Pacing & Tension (Section 7):**
- Influences narration length and detail level
- Calm: brief, functional
- Climax: fast-paced, exciting

**No "Scene Template":**
- DM has full creative control over narration structure
- Guidelines provide constraints (length, focus, style) but not rigid templates

### Literal Prompt Template Excerpts

**Example: NPC Personality Block**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTIVE NPC: Elara Moonwhisper (merchant)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Personality Trait: suspicious
Mannerisms: avoids eye contact, fidgets with coins or jewelry
Ideal: greed
Bond: debt
Flaw: prejudice

Current Emotional State: neutral

Role Behavior (merchant):
- Speech Style: persuasive and business-like
- Typical Actions: displays wares, haggles prices, appraises items, seeks profit

Recent Interactions:
No previous interactions

DMG p.186 DIRECTIVE: Make this NPC memorable through:
1. Using their mannerisms in dialogue and actions
2. Reflecting their personality trait in responses
3. Speaking in their role-appropriate style
4. Reacting according to their emotional state
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Example: Exposition Mode Instructions**
```
🎯 EXPOSITION MODE INSTRUCTIONS (PHASE 2.5 - CRITICAL):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ PLAYER IS EXPLICITLY SEEKING INFORMATION ⚠️

Your job is to ADVANCE THE PLOT, not just set mood.

MANDATORY REQUIREMENTS:
1. Deliver 3-5 concrete pieces of NEW information
2. Reveal facts about: who, what, where, why, stakes
3. Present clear choices or next possible actions
4. NO purple prose or atmospheric filler
5. Be direct and informative

GOOD EXPOSITION:
✓ "The merchant leans in: 'The cult operates from the old mill. 
   They're planning something for the new moon—three days from now. 
   My contact saw them move crates of black powder there last night.'"

BAD EXPOSITION:
✗ "The atmosphere grows tense as they continue speaking..."
✗ "You sense there's more to this story..."

CRITICAL: If player is listening/waiting, NPCs MUST actively share 
information. Don't make them ask again. Give answers NOW.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 7. MISSING ARCHITECTURE

### Multi-Hook Scenes
**Status:** NOT IMPLEMENTED

**Current Behavior:**
- Scenes are linear: player action → DM response → player action
- No system to present multiple simultaneous quest hooks in a single scene
- DM may mention multiple NPCs or locations, but they're not structured as "hooks"

**Required for Quest System:**
1. **Hook Data Structure:**
   ```json
   {
     "hook_id": "string",
     "type": "conversation|observation|rumor|event",
     "source_npc_id": "string (optional)",
     "description": "string (player-facing tease)",
     "quest_id": "string (links to quest)",
     "trigger_condition": "string (e.g., 'talk to NPC', 'investigate object')"
   }
   ```

2. **Hook Injection in DM Prompt:**
   - New section: "AVAILABLE QUEST HOOKS"
   - List hooks relevant to current location
   - Instruct DM to weave 1-3 hooks into narration subtly

3. **Hook Tracking:**
   - Add `world_state.active_hooks` array
   - Add `world_state.discovered_hooks` array
   - Track which hooks player has noticed/pursued

### Curiosity Triggers
**Status:** NOT IMPLEMENTED

**Current Behavior:**
- Information only revealed when player explicitly asks
- No proactive "something catches your eye" moments
- Passive Perception auto-reveals are limited to `world_state.location_secrets` (rarely populated)

**Required for Quest System:**
1. **Curiosity Event Generator:**
   - Function: `generate_curiosity_trigger(location, world_blueprint, character_state)`
   - Returns: String describing subtle clue (e.g., "You notice a cloaked figure watching you from across the square")

2. **Integration with Passive Perception:**
   - Expand `information_service.apply_passive_perception()` to include quest-related clues
   - Add quest hooks to `world_state.location_secrets` with DC values

3. **Randomized Triggers:**
   - 20-30% chance per scene to introduce curiosity event
   - Higher chance in "building" tension phase (foreshadowing)

### Quest-Related Hints
**Status:** PARTIALLY IMPLEMENTED (but not quest-integrated)

**Current Implementation:**
- `information_service` can auto-reveal clues via passive Perception
- `world_blueprint.key_npcs[].knows_about` exists but unused
- `world_blueprint.points_of_interest[].hidden_function` exists but unused

**Gap:**
- No system to convert `knows_about` into active hints
- No structured "hint delivery" tied to quest objectives
- No breadcrumb trail system

**Required for Quest System:**
1. **Hint Data Structure:**
   ```json
   {
     "hint_id": "string",
     "quest_id": "string",
     "objective_id": "string",
     "hint_text": "string (e.g., 'You hear rumors of strange lights near the old mill')",
     "reveal_condition": {
       "location": "string (optional)",
       "npc_id": "string (optional)",
       "passive_perception_dc": int (optional)
     },
     "revealed": boolean
   }
   ```

2. **Hint Delivery Service:**
   - Function: `select_relevant_hints(quest_objectives, current_location, active_npcs)`
   - Returns: List of hints to include in DM prompt
   - Hints formatted as "overheard conversation" or "environmental clue"

3. **Integration with NPC Dialogue:**
   - When talking to NPC, check if NPC `knows_about` current quest objectives
   - Auto-inject hint into NPC dialogue if relevant

### Narrative Seeds
**Status:** NOT IMPLEMENTED

**Current Behavior:**
- No system to plant future plot threads
- `world_blueprint.macro_conflicts` and `global_threat` exist but are static
- DM has no instructions to foreshadow or plant seeds

**Required for Quest System:**
1. **Seed Data Structure:**
   ```json
   {
     "seed_id": "string",
     "type": "foreshadowing|red_herring|future_quest",
     "description": "string (DM-facing instruction)",
     "trigger_time": "string (e.g., 'after 3 sessions', 'when player reaches level 5')",
     "payoff_quest_id": "string (optional)",
     "planted": boolean,
     "triggered": boolean
   }
   ```

2. **Seed Injection:**
   - Add section to DM prompt: "NARRATIVE SEEDS TO PLANT"
   - Randomly select 0-1 seeds per session
   - Instruct DM to weave seed into narration subtly (e.g., "You notice the mayor seems distracted, glancing nervously at the door")

3. **Seed Tracking:**
   - Add `world_state.planted_seeds` array
   - When seed triggers, generate quest or event

### Reactive Storytelling
**Status:** PARTIALLY IMPLEMENTED (via consequence system)

**Current Implementation:**
- Consequence escalation reacts to player transgressions
- NPC emotional state changes based on player actions
- Combat initiation reacts to hostile actions

**Gap:**
- No system to react to **positive** player actions (e.g., helping NPC → NPC offers quest)
- No faction reputation system (partially present but unused)
- No "remembered actions" beyond transgressions

**Required for Quest System:**
1. **Reputation System:**
   - Track player reputation with each faction (currently `character_state.reputation` exists but unused)
   - Update reputation based on quest completions, NPC interactions, combat outcomes
   - Reputation affects: quest availability, NPC emotional states, pricing, faction behavior

2. **Action Memory:**
   - Expand `world_state.location_memories` to track significant player actions per location
   - NPCs reference past actions in dialogue (e.g., "You're the one who saved the merchant from bandits!")

3. **Quest Gating:**
   - Quests require minimum reputation or completed prerequisite quests
   - Add `quest.prerequisites` field

### Player-Intent Tailored Quests
**Status:** NOT IMPLEMENTED

**Current Behavior:**
- Quests are generic, not tied to character background/goal
- `character_state.goal` exists (e.g., "Seek vengeance for murdered family") but unused in quest generation

**Required for Quest System:**
1. **Goal-Quest Mapping:**
   - Analyze `character_state.goal` keywords (e.g., "vengeance", "wealth", "knowledge")
   - Generate quests aligned with goal (e.g., vengeance → track down villain; knowledge → find ancient library)

2. **Background Integration:**
   - `character_state.background` (e.g., "criminal", "noble", "scholar") affects quest types
   - Criminal background → thieves guild quests; noble background → political intrigue quests

3. **Dynamic Quest Generation:**
   - Function: `generate_tailored_quest(character_goal, character_background, world_blueprint)`
   - Uses LLM to create quest that feels personalized

---

## 8. FINAL SUMMARY

### How Scenes Currently Work

**DUNGEON FORGE's scene generation is a sophisticated multi-agent system** that orchestrates 10+ specialized services to build comprehensive AI DM prompts. The process:

1. **Loads game state** from MongoDB (campaign, character, world_state, combat_state)
2. **Activates NPCs** for current location from world_blueprint
3. **Runs Phase 1 DMG systems** (tension/pacing, information dispensing, consequence tracking)
4. **Runs Phase 2 DMG systems** (session mode detection, improvisation classification, NPC personality generation)
5. **Generates context memory** (location constraints, NPC constraints, ongoing situations)
6. **Routes through combat or hostile action handlers** if applicable
7. **Classifies player intent** using gpt-4o-mini
8. **Assembles A-Version DM prompt** (~6000 tokens) integrating all service outputs
9. **Sends to DM (gpt-4o)** for narrative scene generation
10. **Validates DM response** for continuity errors
11. **Updates world_state** with DM's world_state_update delta

**Strengths:**
- ✅ Robust mechanical authority (combat results are law)
- ✅ Strong NPC personality system with emotional states and mannerisms
- ✅ Sophisticated pacing system (5 tension phases, mode-based narration)
- ✅ Consequence escalation system (transgressions → guards → bounties → combat)
- ✅ Location continuity enforcement (prevents DM from hallucinating merchants in ruins)
- ✅ Matt Mercer-style narration guidelines for cinematic quality
- ✅ Improvisation framework ("Yes, and..." / "Yes, but..." for creative actions)

**Weaknesses:**
- ❌ No structured quest system (quests exist but rarely used)
- ❌ No multi-hook scene generation (can't present 3 simultaneous quest leads)
- ❌ No curiosity triggers (player must explicitly ask for everything)
- ❌ No quest-hint integration (NPC `knows_about` field unused)
- ❌ No narrative seed planting (no foreshadowing system)
- ❌ No positive reputation tracking (only transgressions tracked)
- ❌ No player-intent tailored quest generation (character `goal` unused)
- ❌ No event system (events emerge organically but unpredictably)

### What is Missing for a Full Quest Engine

**1. Quest Generation Agent:**
- LLM-based service that analyzes world_blueprint, character_state, and world_state
- Generates 3-5 quest options tailored to character goal and background
- Creates multi-step objectives with hints and narrative beats
- Stores quests in `world_state.quests` with rich metadata

**2. Hook Injection System:**
- At scene start, select 1-3 relevant quest hooks from available quests
- Format hooks as subtle narrative elements in DM prompt
- Instruct DM to weave hooks into NPC dialogue, environmental descriptions, or overheard conversations
- Track which hooks player noticed (`world_state.discovered_hooks`)

**3. Hint Delivery Pipeline:**
- Map quest objectives to hints (breadcrumb trail)
- Integrate hints with passive Perception system
- Format hints for NPCs who `knows_about` relevant topics
- Randomized hint delivery (20-30% chance per relevant scene)

**4. Curiosity Trigger Generator:**
- Function that generates "something catches your eye" moments
- Tied to quest hooks or narrative seeds
- Higher frequency during "building" tension phase
- Format: Environmental clue or NPC behavior quirk

**5. Narrative Seed Planter:**
- System to inject future plot threads into current scenes
- Seeds defined in `mission_profiles.json` (future file)
- DM instructed to plant 0-1 seed per session subtly
- Seeds tracked in `world_state.planted_seeds` with trigger conditions

**6. Reputation & Relationship System:**
- Expand `character_state.reputation` to track faction relationships
- Update reputation based on quest outcomes and NPC interactions
- Reputation affects quest availability, NPC behavior, and dialog options
- Display reputation in UI (not currently shown)

**7. Dynamic Event System:**
- Time-based events (e.g., "cult ritual in 3 days")
- Location-based events (e.g., "merchant caravan arrives")
- Consequence-triggered events (already partially implemented)
- Event scheduler that checks `world_state.scheduled_events` each turn

**8. Quest Objective Automation:**
- Expand `quest_service.update_quest_progress()` to detect more event types
- Add automatic quest objective detection (e.g., "entered_location", "defeated_enemy_type", "learned_secret")
- Notify DM when quest objective completed (currently silent)

**9. Twist & Complication System:**
- Define quest twists in `twist_profiles.json` (future file)
- Trigger twists at mid-quest points (e.g., "quest giver was lying", "target is innocent")
- Integrate with improvisation system (risky actions trigger twists)

### What Needs to Change in DM Prompts

**NEW SECTION: Quest & Hook Integration (to be added after Section 10):**
```
========================================================
= 11. QUEST SYSTEM & HOOK DELIVERY
========================================================
You are responsible for subtly introducing quest hooks and advancing active quests.

ACTIVE QUESTS:
[List of active quests with objectives and progress]

AVAILABLE QUEST HOOKS (weave 1-2 into this scene):
[List of hooks with source NPC and tease description]

QUEST HINTS TO DELIVER:
[List of relevant hints for current location/NPCs]

RULES:
- DO NOT explicitly say "This is a quest" or "Here's a quest hook"
- Weave hooks naturally into NPC dialogue, environmental clues, or overheard conversations
- Example: Instead of "The merchant offers you a quest", say: "The merchant leans in, glancing nervously. 'Strange things happening at the old mill lately... might be worth investigating.'"
- If player completes quest objective, acknowledge it in narration (e.g., "You've gathered the information the elder requested")
- Use curiosity language: "You notice...", "Something catches your eye...", "You overhear..."

HOOK TYPES:
- Conversation: NPC mentions problem or opportunity in dialogue
- Observation: Player notices suspicious activity or environmental clue
- Rumor: Overheard conversation between NPCs
- Event: Something happens that creates urgency (e.g., scream, explosion)
```

**MODIFY SECTION 3 (NPC Personality):**
Add to each NPC personality block:
```
Quest-Related Knowledge:
- Knows about: [list from world_blueprint.key_npcs[].knows_about]
- Can provide hints for: [list of relevant quest objectives]

INSTRUCTION: If player talks to this NPC and has relevant active quest, this NPC should share information from "knows_about" list naturally in dialogue.
```

**MODIFY SECTION 7 (Pacing & Tension):**
Add quest urgency factor:
```
QUEST URGENCY:
- Active quests with deadlines: [list]
- Time-sensitive hints to deliver: [list]

If quest deadline is approaching, increase tension and add urgency to narration.
```

### What Needs to Change in Backend Models

**1. Expand WorldState Model:**
```python
class WorldState(BaseModel):
    # ... existing fields ...
    
    # NEW: Quest System Fields
    active_quests: List[Dict[str, Any]] = Field(default_factory=list)
    completed_quests: List[str] = Field(default_factory=list)  # quest_ids
    failed_quests: List[str] = Field(default_factory=list)
    
    # NEW: Hook System Fields
    available_hooks: List[Dict[str, Any]] = Field(default_factory=list)
    discovered_hooks: List[str] = Field(default_factory=list)  # hook_ids
    active_hooks: List[str] = Field(default_factory=list)  # Currently pursuing
    
    # NEW: Narrative Seed Fields
    planted_seeds: List[Dict[str, Any]] = Field(default_factory=list)
    triggered_seeds: List[str] = Field(default_factory=list)  # seed_ids
    
    # NEW: Event System Fields
    scheduled_events: List[Dict[str, Any]] = Field(default_factory=list)
    active_events: List[Dict[str, Any]] = Field(default_factory=list)
    
    # NEW: Reputation Tracking (expand existing)
    faction_reputations: Dict[str, int] = Field(default_factory=dict)  # faction_id -> reputation (-100 to +100)
    npc_reputations: Dict[str, int] = Field(default_factory=dict)  # npc_id -> reputation
    
    # NEW: Memory System
    location_memories: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)  # location -> memories
    significant_actions: List[Dict[str, Any]] = Field(default_factory=list)
```

**2. Create Dedicated Quest Models:**
```python
class QuestHook(BaseModel):
    hook_id: str
    quest_id: str
    type: str  # "conversation", "observation", "rumor", "event"
    source_npc_id: Optional[str] = None
    source_location: str
    description: str  # Player-facing tease
    trigger_condition: Optional[str] = None
    discovered: bool = False
    pursued: bool = False

class QuestHint(BaseModel):
    hint_id: str
    quest_id: str
    objective_id: str
    hint_text: str
    reveal_condition: Dict[str, Any]  # {location, npc_id, passive_perception_dc}
    revealed: bool = False

class NarrativeSeed(BaseModel):
    seed_id: str
    type: str  # "foreshadowing", "red_herring", "future_quest"
    description: str  # DM-facing instruction
    trigger_time: str  # "after_3_sessions", "when_level_5", "immediate"
    payoff_quest_id: Optional[str] = None
    planted: bool = False
    planted_at: Optional[datetime] = None
    triggered: bool = False

class QuestObjective(BaseModel):
    objective_id: str
    type: str  # "go_to", "kill", "interact", "discover", "deliver", "escort"
    target: str
    count: int = 1
    progress: int = 0
    hints: List[QuestHint] = Field(default_factory=list)
    completed: bool = False

class Quest(BaseModel):
    quest_id: str
    name: str
    summary: str
    status: str = "available"  # "available", "active", "completed", "failed"
    giver_npc_id: Optional[str] = None
    location_id: Optional[str] = None
    objectives: List[QuestObjective]
    hooks: List[QuestHook]
    prerequisites: List[str] = Field(default_factory=list)  # quest_ids
    rewards_xp: int
    rewards_items: List[str] = Field(default_factory=list)
    rewards_reputation: Dict[str, int] = Field(default_factory=dict)  # faction_id -> reputation change
    deadline: Optional[Dict[str, Any]] = None  # {type: "turns", value: 10}
    failure_conditions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**3. Create Mission Profile Schema:**
```python
class MissionProfile(BaseModel):
    """Template for generating quests"""
    profile_id: str
    name: str
    archetype: str  # "investigation", "combat", "escort", "fetch", "social"
    themes: List[str]  # e.g., ["mystery", "betrayal", "redemption"]
    character_goals: List[str]  # e.g., ["vengeance", "knowledge"]
    character_backgrounds: List[str]  # e.g., ["criminal", "noble"]
    min_level: int
    max_level: int
    objective_templates: List[Dict[str, Any]]
    hook_templates: List[Dict[str, Any]]
    twist_templates: List[Dict[str, Any]]
    hint_templates: List[Dict[str, Any]]
```

### What Can Integrate Cleanly with Quest/Twist/Hint Pipeline

**✅ ALREADY COMPATIBLE:**

1. **NPC Personality System:**
   - `npc_personalities` can store quest-related knowledge
   - Emotional states can change based on quest progress
   - Interaction history tracks quest-related conversations

2. **Information Dispensing System:**
   - `apply_passive_perception()` can reveal quest hints
   - `drip_feed_information()` can control hint pacing
   - `clarify_conditions()` can explain quest mechanics

3. **Consequence System:**
   - Quest failure can trigger consequences
   - Transgression against quest giver → quest fails
   - Escalation events can spawn quests (e.g., "Clear your name" quest after false accusation)

4. **Session Flow System:**
   - Different modes handle quest interactions differently
   - Exposition mode perfect for quest briefings
   - Investigation mode perfect for quest clue gathering

5. **Improvisation System:**
   - Creative quest solutions rewarded with advantage
   - Risky quest approaches add complications/twists
   - Impossible quest shortcuts suggest alternatives

6. **Tension System:**
   - Quest deadlines increase tension
   - Quest combat encounters trigger climax phase
   - Quest completion triggers resolution phase

**🔧 REQUIRES MINOR MODIFICATION:**

1. **Location Constraints:**
   - Add quest-specific location data (e.g., "This location has active quest objective")
   - Include quest hints in location secrets

2. **Active NPC System:**
   - Tag NPCs with `relevant_quests` field
   - Prioritize quest-relevant NPCs for activation

3. **World Blueprint:**
   - Add `quest_seeds` field to POIs
   - Expand NPC `knows_about` with quest-specific knowledge

**🆕 REQUIRES NEW SERVICE:**

1. **Quest Generation Service:**
   - Function: `generate_quest_from_profile(mission_profile, character, world_blueprint)`
   - Consumes `mission_profiles.json`
   - Returns complete Quest object

2. **Hook Injection Service:**
   - Function: `select_relevant_hooks(active_quests, current_location, active_npcs)`
   - Formats hooks for DM prompt
   - Tracks which hooks were presented

3. **Hint Delivery Service:**
   - Function: `get_relevant_hints(quest_objectives, current_location, active_npcs)`
   - Checks reveal conditions
   - Marks hints as revealed

4. **Quest Progression Tracker:**
   - Function: `check_quest_objective_completion(player_action, world_state_update, active_quests)`
   - Auto-detects objective completion
   - Updates quest progress
   - Returns completion notifications for DM

5. **Narrative Seed Manager:**
   - Function: `select_seed_to_plant(world_state, session_count, character_level)`
   - Checks trigger conditions
   - Returns seed for DM prompt
   - Marks seed as planted

---

## CONCLUSION

**DUNGEON FORGE has a sophisticated scene generation pipeline** built on DMG-compliant systems, but it currently operates as a **reactive sandbox** rather than a **quest-driven narrative engine**. 

The architecture is **90% ready** for a full quest system. The missing 10% consists of:
1. **Quest generation logic** (mission profiles → quests)
2. **Hook injection system** (quests → scene hooks)
3. **Hint delivery pipeline** (quest objectives → breadcrumb hints)
4. **Curiosity triggers** (proactive clue reveals)
5. **Narrative seed planting** (foreshadowing system)

**All existing systems can integrate cleanly** with these additions. The DM prompt structure is flexible enough to accommodate new sections, and the world_state/quest models already have placeholder fields for quest data.

**Next Steps for PHANERON DEV ARCHITECT:**
1. Design `mission_profiles.json` schema with 20-30 quest archetypes
2. Design `twist_profiles.json` schema with 15-20 quest complications
3. Design `hint_profiles.json` schema with hint delivery strategies
4. Write Quest Generation Agent prompt (LLM-based quest builder)
5. Modify `build_a_version_dm_prompt()` to include quest/hook section
6. Create Hook Injection Service
7. Create Hint Delivery Service
8. Integrate Quest Progression Tracker into action endpoint
9. Build Narrative Seed Manager
10. Expand world_state model with quest fields

---

**Report End**
