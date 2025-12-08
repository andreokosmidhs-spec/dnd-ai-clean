# ✅ v6.0 Story Consistency Layer Agent - Implemented

## Overview
Successfully implemented the v6.0 Story Consistency Layer Agent as a **new validation service** that runs on top of the DM Agent to enforce narrative consistency and world continuity.

**Date**: December 2024  
**Status**: ✅ IMPLEMENTED  
**Type**: **Additional Layer** (not a replacement)

---

## What is the Story Consistency Layer?

### Architecture Position

```
Player Action
      ↓
[DM Agent v5.1] ← Generates narration
      ↓
[Story Consistency Agent v6.0] ← Validates & corrects
      ↓
Final Output to Player
```

**Key Point**: This is NOT a replacement for the DM Agent. It's a validation layer that:
1. Receives DM output
2. Checks it against canonical data
3. Decides: approve / revise_required / hard_block
4. Returns corrected output if needed

---

## Core Mission

**Primary Goals**:
1. Enforce narrative consistency across all DM outputs
2. Protect canonical world blueprint, quest state, and NPC state
3. Ensure DM respects v5.x System Prompt rules
4. Prevent accidental contradictions in long campaigns

**What It Does**:
- ✅ Validates world canon (regions, factions, global threats)
- ✅ Checks NPC consistency (location, relationships, knowledge)
- ✅ Verifies quest continuity (no disappearing quests)
- ✅ Enforces POV rules (second person, no omniscience)
- ✅ Confirms mechanics alignment (narration matches HP, conditions, check results)

**What It Does NOT Do**:
- ❌ Generate fresh storytelling from scratch
- ❌ Act as a Dungeon Master
- ❌ Override DM creative intent unnecessarily
- ❌ Rewrite narration style/tone (only fixes violations)

---

## Key Features

### 1. Three-Tier Decision System

**Decision Types**:

**approve**
- No issues with severity "error"
- DM output is consistent and safe
- Original narration used as-is (or minimally edited)

**revise_required**
- One or more "error" issues detected
- Issues can be fixed with minimal corrections
- Returns `corrected_narration` with targeted fixes

**hard_block**
- Critical data missing
- Severe contradictions unfixable
- DM output must not be shown to player
- `corrected_narration` is null

### 2. Comprehensive Issue Detection

**Issue Types**:
- `world_canon` - World naming errors, geographic contradictions, faction changes
- `npc_consistency` - NPC location/attitude conflicts, impossible knowledge
- `quest_continuity` - Quests disappearing, premature resolution, missing follow-up
- `thread_continuity` - Story threads contradicted or dropped
- `pov_violation` - Breaking second-person POV, omniscient narration
- `information_boundary` - Revealing hidden info, NPC thoughts, off-screen actions
- `style_violation` - Forbidden phrases, sentence limit violations
- `mechanical_mismatch` - Narration contradicts HP, conditions, check results
- `missing_context` - Required canonical data missing
- `other` - Miscellaneous issues

**Severity Levels**:
- `info` - Informational, no action needed
- `warning` - Soft issue, doesn't block
- `error` - Hard issue, requires correction or block

### 3. Minimal-Edit Philosophy

**Principles**:
- Prefer smallest possible change that fixes the issue
- Do not rewrite narration style, tone, or flavor
- Do not lengthen/shorten unnecessarily
- Respect DM System Prompt sentence limits
- Preserve DM's creative intent

**Example**:
```
DM Output: "The wizard Eldrin greets you warmly from his tower in Northport."
Issue: Eldrin is canonically in Southport
Correction: "The wizard Eldrin greets you warmly from his tower in Southport."
```
(Only the location is changed)

### 4. Canonical Hierarchy

**Priority Order** (highest to lowest):
1. DM System Prompt v5.x (master DM behavior & schema rules)
2. world_blueprint (static world canon)
3. world_state / quest_state / npc_registry / story_threads (evolving canon)
4. Story Consistency Layer Agent v6.0 (this validator)
5. DM draft intent (creative output to be minimally preserved)
6. Style references (Matt Mercer framework, etc.)

### 5. No Retroactive Retconning

**Rules**:
- Cannot silently retcon prior established facts
- If DM contradicts established canon → flag issue and suggest correction
- Cannot erase or rewrite past events
- New canonical facts only allowed if:
  - DM marked them as `new_seed`, or
  - Backend declares world-expansion operation

### 6. State Delta Tracking

**world_state_delta**:
- NPC updates (location, knowledge flags, relationship changes)
- Quest updates (state transitions with reasons)
- Story thread updates (status changes)
- Global threat progress flags

**story_state_delta**:
- New hooks (with source: npc/location/event)
- Closed hooks (with reason)

---

## Implementation Details

### File Created
**Location**: `/app/backend/services/story_consistency_agent.py`

**Key Components**:
1. `STORY_CONSISTENCY_PROMPT` - Full v6.0 system prompt
2. `build_consistency_context()` - Builds context for validation
3. `validate_dm_output()` - Main validation function

### Function Signature

```python
async def validate_dm_output(
    dm_draft: Dict[str, Any],           # DM's proposed output
    world_blueprint: Dict[str, Any],    # Static world definition
    world_state: Dict[str, Any],        # Current world state
    quest_state: Optional[Dict[str, Any]] = None,
    npc_registry: Optional[Dict[str, Any]] = None,
    story_threads: Optional[List[Dict[str, Any]]] = None,
    scene_history: Optional[List[Dict[str, Any]]] = None,
    mechanical_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate DM output through Story Consistency Layer Agent.
    
    Returns:
        {
            "decision": "approve | revise_required | hard_block",
            "issues": [...],
            "corrected_narration": "string or null",
            "narration_changes_summary": [...],
            "world_state_delta": {...},
            "story_state_delta": {...}
        }
    """
```

### LLM Configuration
- **Model**: `gpt-4o` (same as DM)
- **Temperature**: `0.3` (lower than DM's 0.7 for more consistent validation)

---

## Usage Pattern

### Basic Integration

```python
from services.story_consistency_agent import validate_dm_output

# 1. DM generates output
dm_response = await run_dungeon_forge(
    player_action=action,
    character_state=char_state,
    world_blueprint=blueprint,
    world_state=state,
    # ... other context
)

# 2. Validate through consistency layer
validation = await validate_dm_output(
    dm_draft={
        "narration": dm_response["narration"],
        "scene_mode": dm_response["scene_mode"],
        "requested_check": dm_response.get("requested_check"),
        "world_state_update": dm_response.get("world_state_update", {}),
        "player_updates": dm_response.get("player_updates", {})
    },
    world_blueprint=blueprint,
    world_state=state,
    quest_state=quests,
    npc_registry=npcs,
    # ... other canonical data
)

# 3. Act on validation result
if validation["decision"] == "approve":
    # Use original DM output (or minimally corrected version)
    final_narration = validation["corrected_narration"] or dm_response["narration"]
    
elif validation["decision"] == "revise_required":
    # Use corrected narration
    final_narration = validation["corrected_narration"]
    logger.warning(f"DM output revised: {validation['narration_changes_summary']}")
    
elif validation["decision"] == "hard_block":
    # DM output blocked - need to regenerate or error
    logger.error(f"DM output blocked: {validation['issues']}")
    # Implement fallback strategy
```

### Error Handling

```python
try:
    validation = await validate_dm_output(...)
except Exception as e:
    # Fallback: approve with warning
    logger.error(f"Consistency validation failed: {e}")
    validation = {
        "decision": "approve",
        "issues": [{
            "type": "other",
            "severity": "warning",
            "message": f"Validation error: {e}. Using DM output as-is."
        }],
        "corrected_narration": None
    }
```

---

## Output Schema

### Full Response Structure

```json
{
  "decision": "approve | revise_required | hard_block",
  "issues": [
    {
      "type": "world_canon | npc_consistency | quest_continuity | ...",
      "severity": "info | warning | error",
      "message": "Human-readable description",
      "location_hint": "narration line 3",
      "related_ids": ["npc_123", "quest_456"],
      "origin": "existing_canon | new_seed | dm_draft"
    }
  ],
  "corrected_narration": "Minimally edited narration string or null",
  "narration_changes_summary": [
    "Changed location from Northport to Southport",
    "Removed NPC thought revelation"
  ],
  "world_state_delta": {
    "npc_updates": [
      {
        "npc_id": "npc_eldrin",
        "location": "southport_tower",
        "knowledge_flags": ["knows_player_quest"],
        "relationship_changes": [
          {
            "target": "player",
            "change": "friendly",
            "reason": "Player helped with research"
          }
        ]
      }
    ],
    "quest_updates": [
      {
        "quest_id": "quest_bandits",
        "new_state": "active",
        "reason": "Player accepted from merchant"
      }
    ],
    "story_thread_updates": [
      {
        "thread_id": "thread_cult",
        "status": "escalated",
        "reason": "Cultists spotted in town"
      }
    ],
    "flags": {
      "global_threat_progress": "hint"
    }
  },
  "story_state_delta": {
    "new_hooks": [
      {
        "id": "hook_missing_daughter",
        "description": "Merchant's daughter missing after bandit attack",
        "source": "npc"
      }
    ],
    "closed_hooks": []
  }
}
```

---

## Task Loop (8 Steps)

### Step 1: Validate Inputs
- Check required fields present
- Verify structural validity
- Hard block if critical data missing

### Step 2: Check Canonical World & Lore
- Verify world/region/faction names
- Check geographic consistency
- Validate faction goals/alignment
- Ensure global threat consistency

### Step 3: Check NPC & Relationship Consistency
- Verify NPC locations
- Check role/attitude consistency
- Validate NPC knowledge

### Step 4: Check Quest & Story Thread Continuity
- Verify quest state transitions
- Check for dropped quests
- Validate story thread progress

### Step 5: Check POV & Information Boundaries
- Enforce second-person POV
- Check for omniscient narration
- Validate information revelations
- Check sentence limits

### Step 6: Check Mechanics Alignment
- Compare narration vs HP/conditions
- Verify check result alignment
- Validate combat state match

### Step 7: Decide
- approve (no errors)
- revise_required (fixable errors)
- hard_block (critical issues)

### Step 8: Produce State Deltas
- Safe NPC/quest/thread updates
- New/closed story hooks

---

## Integration Strategy

### Phase 1: Optional (Recommended Start)
```python
# Add as optional validation
USE_CONSISTENCY_LAYER = True  # Feature flag

if USE_CONSISTENCY_LAYER:
    validation = await validate_dm_output(...)
    if validation["decision"] != "approve":
        logger.warning(f"Consistency issues: {validation['issues']}")
        # Use corrected version
        final_narration = validation["corrected_narration"] or dm_response["narration"]
else:
    # Use DM output directly
    final_narration = dm_response["narration"]
```

### Phase 2: Always-On (Production)
```python
# Always validate
validation = await validate_dm_output(...)

if validation["decision"] == "hard_block":
    # Regenerate DM output with corrected context
    # Or show error to user
    raise Exception("DM output blocked by consistency layer")

# Use corrected or original
final_narration = validation["corrected_narration"] or dm_response["narration"]
```

### Phase 3: Feedback Loop
```python
# Use state deltas to update canonical data
if validation["world_state_delta"]["npc_updates"]:
    for update in validation["world_state_delta"]["npc_updates"]:
        # Update NPC registry
        await update_npc_state(update)

if validation["world_state_delta"]["quest_updates"]:
    for update in validation["world_state_delta"]["quest_updates"]:
        # Update quest state
        await update_quest_state(update)
```

---

## Benefits

### 1. **Prevents Canon Drift** ⭐
- Long campaigns stay consistent
- NPCs maintain coherent behavior
- Quests don't disappear
- World geography stays stable

### 2. **Enforces DM Rules**
- Second-person POV always maintained
- No accidental omniscience
- Sentence limits respected
- Mechanics stay aligned with narration

### 3. **Minimal Performance Impact**
- Only validates, doesn't regenerate
- Fast decision (approve/revise/block)
- Can be disabled with feature flag

### 4. **Debugging Aid**
- Issues logged with severity and location
- Clear explanations of problems
- Helps identify DM prompt issues

### 5. **Campaign Memory**
- Tracks state deltas
- Maintains story thread continuity
- Records NPC knowledge and relationships

---

## Testing Status

### ✅ Implementation Complete
- Service file created
- Validation function implemented
- Error handling in place
- Logging configured

### ⏳ Integration Pending
Need to:
1. Add validation call in main DM pipeline
2. Wire up canonical data sources (quest_state, npc_registry, etc.)
3. Implement state delta application
4. Add feature flag for optional use

### ⏳ Testing Needed
1. Test with various DM outputs
2. Verify issue detection works
3. Validate correction quality
4. Check performance impact

---

## Configuration

### Environment Variables (Suggested)
```
ENABLE_STORY_CONSISTENCY_LAYER=true
CONSISTENCY_LAYER_MODEL=gpt-4o
CONSISTENCY_LAYER_TEMPERATURE=0.3
CONSISTENCY_LAYER_LOG_LEVEL=INFO
```

### Feature Flags
```python
# In app config
FEATURES = {
    "story_consistency_layer": True,
    "consistency_hard_block": False,  # Only warn, don't block
    "consistency_auto_correct": True   # Auto-apply corrections
}
```

---

## Rollback Plan

If v6.0 causes issues:

**Option 1: Disable via Feature Flag**
```python
USE_CONSISTENCY_LAYER = False
```
DM outputs pass through without validation.

**Option 2: Soft Mode**
```python
CONSISTENCY_HARD_BLOCK = False
```
Validation runs but only logs warnings, never blocks.

**Option 3: Remove Service**
Simply don't import or call `validate_dm_output()`.

---

## Version Architecture Summary

| Component | Version | Role |
|-----------|---------|------|
| **DM Agent** | v5.1 | Primary narration engine |
| **Story Consistency Layer** | v6.0 | Validation & correction layer |
| **Narration Filter** | v4.1+ | Post-processing (sentence limits, banned phrases) |
| **Check System** | Current | Mechanics resolution |

**Pipeline**:
```
Player → DM v5.1 → Consistency v6.0 → Filter v4.1 → Player
```

---

## Next Steps

### Immediate (P0)
1. ⏳ **Wire up validation** in main DM pipeline
2. ⏳ **Add canonical data sources** (quest_state, npc_registry, story_threads)
3. ⏳ **Test with sample outputs** to validate behavior

### Future Enhancements (P1)
1. **State Delta Application**: Auto-apply world_state_delta and story_state_delta
2. **Metrics**: Track approval/revision/block rates
3. **Learning**: Analyze common issues to improve DM prompt
4. **UI**: Show consistency warnings to developers

---

**Status**: v6.0 Story Consistency Layer implemented ✅  
**Type**: Additional validation layer (not a DM replacement)  
**Ready for**: Integration into DM pipeline and testing  
**Backward Compatible**: ✅ Can be disabled or made optional
