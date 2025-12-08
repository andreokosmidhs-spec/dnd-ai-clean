# v4.1 Implementation Plan — Unified Narration System

## Overview
Replace all conflicting narrative prompts with a single unified v4.1 specification.

---

## Phase 1: Update Narration Filter ✅ (DO FIRST)

### File: `/app/backend/services/narration_filter.py`

**Current limits** (TOO RESTRICTIVE):
```python
max_sentences = 4  # Default
```

**Update to match v4.1**:
```python
# Mode-based limits matching v4.1 spec
SENTENCE_LIMITS = {
    "intro": 16,
    "exploration": 10,
    "social": 10,
    "investigation": 10,
    "combat": 8,
    "travel": 8,
    "rest": 8,
    "downtime": 8,
    "default": 10
}

def apply_filter(text, max_sentences=None, context="default"):
    if max_sentences is None:
        max_sentences = SENTENCE_LIMITS.get(context, 10)
    # ... rest of filter logic
```

**Impact**: Allows prompts to use full intended range without truncation.

---

## Phase 2: Replace Main DM Prompt ✅

### File: `/app/backend/routers/dungeon_forge.py`

**Function**: `build_a_version_dm_prompt()` (Lines 848-1067)

**Replace with**: v4.1 unified spec (from `/app/DM_AGENT_PROMPT_V4_1.md`)

**Key changes**:
1. Remove `"options"` field from output schema
2. Add "end with open prompt" section
3. Unified sentence limits (intro: 12-16, exploration: 6-10, combat: 4-8)
4. Single consistent style across all contexts

**Template variables to inject**:
- `{scene_mode}` - Current mode
- `{player_action}` - Player's action
- `{dc_info}` - System-calculated DC (if any)
- `{check_result_info}` - Check result (if rolled)
- All character/environment context

---

## Phase 3: Update Intro Prompt ✅

### File: `/app/backend/services/prompts.py`

**Current**: `INTRO_SYSTEM_PROMPT` (Lines 122-242)

**Replace with**: v4.1 intro section

**Changes**:
1. Keep Matt Mercer structure (world → politics → geography → town → player)
2. Update to 12-16 sentences (matches v4.1)
3. Remove "options" generation
4. End with open prompt: "What do you do?"
5. Align banned phrases with v4.1

---

## Phase 4: Update Scene Generator ✅

### File: `/app/backend/services/scene_generator.py`

**Update prompt to match v4.1**:
1. Second person POV only
2. 4-6 sentences (within exploration limit of 10)
3. Observable facts only
4. 3 spatial directions (left, right, ahead)
5. No omniscience
6. No flowery language
7. End with scene pause, not options

**Example v4.1 compliant scene**:
```
You step into the town square. Cobblestones stretch ahead under 
the midday sun. To your left, a blacksmith's forge glows with heat. 
To your right, the Rusty Blade tavern stands with its door open. 
Straight ahead, market stalls line the square. The air smells of 
bread and woodsmoke.
```

---

## Phase 5: Update Output Parsing ⚠️

### Files to check:
1. `/app/backend/routers/dungeon_forge.py` - DM response parsing
2. `/app/frontend/src/components/AdventureLogWithDM.jsx` - Message display

**Changes needed**:
1. Remove `options` field parsing (no longer generated)
2. Update UI to show narration without numbered options
3. Keep action input as free-form text

**Frontend display**:
```javascript
// OLD: Show enumerated options as buttons
{entry.options?.map((opt, i) => (
  <button key={i}>{i+1}. {opt}</button>
))}

// NEW: Just show narration ending with open prompt
// Player types response freely in text input
```

---

## Phase 6: Backend Response Validation ✅

### File: `/app/backend/routers/dungeon_forge.py`

**Add validation after DM response**:
```python
# Validate v4.1 compliance
dm_response = await run_dungeon_forge(...)

# Check for forbidden fields
if "options" in dm_response:
    logger.warning("⚠️ DM generated options field (v4.1 violation)")
    del dm_response["options"]  # Remove for v4.1 compliance

# Validate sentence count
narration = dm_response.get("narration", "")
sentence_count = count_sentences(narration)
mode = session_mode.get("mode", "exploration")
max_allowed = SENTENCE_LIMITS.get(mode, 10)

if sentence_count > max_allowed:
    logger.warning(f"⚠️ Narration exceeds limit: {sentence_count} > {max_allowed}")
```

---

## Phase 7: Create Unified Narration Spec File 📖

### File: `/app/backend/services/narration_spec_v1.py`

**Purpose**: Single source of truth for all narrative rules

```python
"""
Unified Narration Spec v1.0
Single source of truth for all DM narrative behavior
"""

NARRATION_SPEC_V1 = {
    "version": "1.0",
    "sentence_limits": {
        "intro": {"min": 12, "max": 16},
        "exploration": {"min": 6, "max": 10},
        "social": {"min": 6, "max": 10},
        "investigation": {"min": 6, "max": 10},
        "combat": {"min": 4, "max": 8},
        "travel": {"min": 4, "max": 8},
        "rest": {"min": 4, "max": 8},
        "downtime": {"min": 4, "max": 8}
    },
    "pov": "second_person",
    "forbidden": [
        "omniscience",
        "npc_thoughts",
        "hidden_reveals",
        "enumerated_options",
        "meta_commentary"
    ],
    "ending": "open_prompt",  # Not "options"
    "banned_phrases": [
        "you notice",
        "you feel a sense",
        "it seems that",
        # ... full list from v4.1
    ]
}
```

**All prompts import from this file** to ensure consistency.

---

## Implementation Order

### ✅ Step 1: Update Narration Filter (5 minutes)
Fix the truncation issue immediately.

### ✅ Step 2: Replace Main DM Prompt (15 minutes)
Update `build_a_version_dm_prompt()` with v4.1.

### ✅ Step 3: Update Intro Prompt (10 minutes)
Align `INTRO_SYSTEM_PROMPT` with v4.1.

### ✅ Step 4: Update Scene Generator (10 minutes)
Ensure scene descriptions match v4.1 style.

### ✅ Step 5: Remove Options Parsing (10 minutes)
Update backend and frontend to not expect `options` field.

### ✅ Step 6: Add Validation (5 minutes)
Warn if DM violates v4.1 rules.

### ✅ Step 7: Create Narration Spec File (10 minutes)
Single source of truth for future reference.

**Total time**: ~65 minutes

---

## Testing Checklist

### After Phase 1 (Filter Update):
- [ ] Generate intro - verify NOT truncated at 16 sentences
- [ ] Take exploration action - verify up to 10 sentences possible
- [ ] Enter combat - verify up to 8 sentences possible

### After Phase 2 (Main Prompt):
- [ ] Take action - verify no `options` field in response
- [ ] Check narration ends with open prompt
- [ ] Verify sentence limits respected

### After Phase 3 (Intro Prompt):
- [ ] Generate new campaign
- [ ] Verify 12-16 sentences
- [ ] Verify quest hook present
- [ ] Verify ends with "What do you do?" not options

### After Phase 4 (Scene Generator):
- [ ] Move to new location
- [ ] Verify 3 spatial directions
- [ ] Verify 4-6 sentences
- [ ] Verify v4.1 style (no flowery language)

### After Phase 5 (Parsing):
- [ ] Verify frontend doesn't show option buttons
- [ ] Verify player can type freely
- [ ] Verify narration displays correctly

---

## Rollback Plan

If v4.1 causes issues:

1. **Revert narration filter**:
   ```bash
   git checkout HEAD~1 -- backend/services/narration_filter.py
   ```

2. **Revert main prompt**:
   ```bash
   git checkout HEAD~1 -- backend/routers/dungeon_forge.py
   ```

3. **Restart services**:
   ```bash
   sudo supervisorctl restart backend frontend
   ```

---

## Success Metrics

### ✅ Unification Complete:
- Single narration spec used everywhere
- No conflicting guidelines
- Filter matches prompt limits

### ✅ Options Removed:
- DM outputs no `options` field
- Frontend shows no numbered choices
- Players type freely

### ✅ Sentence Limits Working:
- Intro: 12-16 sentences
- Exploration: 6-10 sentences
- Combat: 4-8 sentences
- No premature truncation

### ✅ Style Consistent:
- Second person POV everywhere
- Observable facts only
- No omniscience
- Open prompts at end

---

## Files Modified Summary

1. `/app/backend/services/narration_filter.py` - Update limits
2. `/app/backend/routers/dungeon_forge.py` - Replace main prompt
3. `/app/backend/services/prompts.py` - Update intro prompt
4. `/app/backend/services/scene_generator.py` - Update scene prompt
5. `/app/frontend/src/components/AdventureLogWithDM.jsx` - Remove options UI
6. `/app/backend/services/narration_spec_v1.py` - NEW: Single source of truth

**Total files**: 6 (5 modified, 1 new)

---

## Ready to Proceed?

**Quick win**: Start with Phase 1 (narration filter) - fixes truncation immediately.

**Full implementation**: All 7 phases in ~65 minutes.

**Confirmation needed**: Do you want me to proceed with implementation now?
