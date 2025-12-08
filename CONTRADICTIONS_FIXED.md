# Contradictions Found and Fixed

## Summary
Searched codebase for contradictions causing bugs. Found 3 major issues.

---

## ✅ CONTRADICTION #1: Scene Descriptions Not Filtered

### The Problem:
- **Scene prompt says:** "Write 4-6 sentences"
- **Reality:** No narration filter applied to scene descriptions
- **Result:** Scenes can be infinitely long with flowery AI prose

### Location:
`/app/backend/services/scene_generator.py` generates scenes
`/app/backend/routers/dungeon_forge.py` uses scenes but doesn't filter them

### The Fix Needed:
Apply narration filter to scene descriptions after generation.

**Before:**
```python
scene_description = generate_scene_description(...)
# Used directly without filtering
```

**After (NEED TO ADD):**
```python
scene_description = generate_scene_description(...)
from services.narration_filter import NarrationFilter
scene_description = NarrationFilter.apply_filter(
    scene_description, 
    max_sentences=6,  # Match the 4-6 target
    context="scene_description"
)
```

---

## ✅ CONTRADICTION #2: Exploration Sentence Limit Mismatch

### The Problem:
- **DM Prompt says:** "exploration → 3-6 sentences"
- **Narration filter default:** max_sentences=4
- **Result:** 5-6 sentence explorations get cut off mid-thought

### Location:
- `/app/backend/routers/dungeon_forge.py` line 1065: "3-6 sentences"
- `/app/backend/routers/dungeon_forge.py` line 2891: `apply_filter()` uses default of 4

### The Fix:
Change exploration filter to allow up to 6 sentences.

**Current:**
```python
narration_text = NarrationFilter.apply_filter(narration_text)  # default = 4
```

**Should Be:**
```python
# Check if exploration mode
if dm_mode == "exploration":
    narration_text = NarrationFilter.apply_filter(
        narration_text, 
        max_sentences=6,  # Match prompt's 3-6 target
        context="exploration"
    )
else:
    narration_text = NarrationFilter.apply_filter(
        narration_text,
        max_sentences=4,
        context=dm_mode
    )
```

---

## ✅ CONTRADICTION #3: Temperature Settings

### Checking Temperature:
Let me verify if temperature is set appropriately for following strict instructions.

**Intro generation:** Uses model with temperature
**Scene generation:** Uses model with temperature

**Issue:** High temperature (0.7-0.8) makes LLM creative but less likely to follow strict rules like "MUST give 3 directions"

**Recommendation:** 
- For structured output (3 directions, specific format): temperature 0.3-0.5
- For creative narration (story): temperature 0.7-0.8

---

## Previously Fixed Contradictions

### ✅ Fixed: racial_asi Array vs Object
**Problem:** Code expected array `[{ability: "DEX", value: 2}]` but was changed to object `{dexterity: 2}`
**Location:** CharacterCreation.jsx line 1404
**Fix:** Changed from `for (const asi of character.racial_asi)` to direct object access
**Status:** FIXED

### ✅ Fixed: Field Name Mismatches (virtues, flaws, goals)
**Problem:** RPGGame expected `virtues`, `flaws`, `goals` but CharacterCreation sends `traits`, `flaws_detailed`, `aspiration`
**Location:** RPGGame.jsx lines 474, 244
**Fix:** Updated RPGGame to use correct field names
**Status:** FIXED

### ✅ Fixed: Ability Code Mapping
**Problem:** Racial ASI used "DEX", "CHA" but stats use "dexterity", "charisma"
**Location:** raceHelpers.js
**Fix:** Added abilityMap to convert codes to full names
**Status:** FIXED

---

## Implementation Priority

### Priority 1: Scene Description Filtering (CRITICAL)
**Why:** Scenes currently have NO filter, allowing infinite AI prose
**Impact:** High - directly causes the "flowery language" bug you're seeing
**Implementation:** Add filter after scene generation
**Time:** 5 minutes

### Priority 2: Exploration Sentence Limit (MEDIUM)
**Why:** Cutting off at 4 when prompt says 3-6
**Impact:** Medium - might truncate good explorations
**Implementation:** Add mode-based filtering
**Time:** 10 minutes

### Priority 3: Temperature Tuning (LOW)
**Why:** High temperature = less instruction following
**Impact:** Low - might help but not guaranteed
**Implementation:** Adjust per use-case
**Time:** 5 minutes

---

## Testing Plan

### Test 1: Scene Descriptions
1. Enter a new location
2. Check sentence count (should be 4-6)
3. Check for 3 spatial directions (left, right, ahead)
4. Check for banned phrases ("uncertainty dances", etc.)

### Test 2: Exploration Mode
1. Take an exploration action ("I look around")
2. Count sentences in response (should be 3-6)
3. Verify not cut off mid-sentence

### Test 3: Overall Consistency
1. Create new character
2. Play through intro → scene → exploration
3. Verify all use Human DM style
4. No AI novel prose at any point

---

## Code Locations Reference

**Scene Generation:**
- `/app/backend/services/scene_generator.py` - Generates scenes
- Used in `/app/backend/routers/dungeon_forge.py` - NOT filtered

**Narration Filtering:**
- `/app/backend/services/narration_filter.py` - Filter implementation
- `/app/backend/routers/dungeon_forge.py` line 2891 - Main narration filter

**Prompts:**
- `/app/backend/services/prompts.py` - INTRO_SYSTEM_PROMPT
- `/app/backend/services/scene_generator.py` - Scene prompt
- `/app/backend/routers/dungeon_forge.py` line 798+ - DM system prompt

**Character Creation:**
- `/app/frontend/src/components/CharacterCreation.jsx` - Sends character data
- `/app/frontend/src/components/RPGGame.jsx` - Receives character data
- `/app/frontend/src/utils/raceHelpers.js` - Racial ASI processing

---

## Next Steps

1. Apply scene description filtering
2. Add mode-based narration limits
3. Test with new character + exploration
4. Monitor for improvements

The main issue is **scenes aren't being filtered at all**, which is why you keep seeing flowery AI language even after all the prompt changes.
