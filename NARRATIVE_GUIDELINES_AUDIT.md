# Narrative Guidelines Audit - Conflicts & Recommendations

## Summary
**YES, we have multiple narrative guidelines that may conflict.** However, they're used for different purposes.

---

## Current Guidelines Locations

### 1. Campaign Intro Prompt ✅ (Separate - OK for now)
**File**: `/app/backend/services/prompts.py` (Line 122-242)  
**Name**: `INTRO_SYSTEM_PROMPT`  
**Style**: Matt Mercer macro-to-micro zoom  
**Target**: 12-16 sentences  
**Structure**:
- World context (2 sentences)
- Political tension (2-3 sentences)
- Geography & landmarks (2-3 sentences)
- Starting region (1-2 sentences)
- Starting town (2-3 sentences)
- Player location & quest hook (2-3 sentences)

**Used For**: Initial campaign introduction only  
**Called By**: `/api/intro/generate` endpoint  
**Frequency**: Once per campaign

**Status**: ⚠️ Different from v3.1 but acceptable for intro

---

### 2. Main DM Prompt (Gameplay) ✅ (v3.1 Integrated)
**File**: `/app/backend/routers/dungeon_forge.py` (Lines 848-1067)  
**Name**: `build_a_version_dm_prompt()`  
**Style**: v3.1 Production Build - Strict D&D 5e  
**Target**: 6-10 sentences (exploration), 4-8 (combat)  
**Structure**:
- Behavior rules (POV, boundaries, pacing)
- Task rules (DM logic loop)
- Context injection
- Output schema

**Used For**: All gameplay actions after intro  
**Called By**: `/api/rpg_dm/action` endpoint  
**Frequency**: Every player action

**Status**: ✅ Correctly implemented

---

### 3. Scene Generator Prompt ⚠️ (May Conflict)
**File**: `/app/backend/services/scene_generator.py`  
**Used For**: Generating scene descriptions when player moves to new locations  
**Frequency**: When location changes

**Current Guidelines** (from NARRATION_GUIDELINES.md):
- Target: 4-6 sentences
- Must include 3 spatial directions (left, right, ahead)
- Simple, direct language
- No flowery prose

**Status**: ⚠️ Should align with v3.1 style

---

### 4. Narration Filter 🔧 (Post-Processing)
**File**: `/app/backend/services/narration_filter.py`  
**Purpose**: Enforce sentence limits AFTER generation  
**Limits**:
- Default: 4 sentences
- Exploration: 6 sentences (updated)
- Scene descriptions: 6 sentences

**Status**: ⚠️ Limits may conflict with prompts

---

## Conflicts Identified

### Conflict 1: Sentence Limits
| Context | Prompt Says | Filter Applies | Conflict? |
|---------|-------------|----------------|-----------|
| Intro | 12-16 sentences | 16 max | ⚠️ Could be cut |
| Exploration | 6-10 sentences | 6 max | ⚠️ Upper range cut |
| Combat | 4-8 sentences | 4 max | ⚠️ Upper range cut |
| Scene | 4-6 sentences | 6 max | ✅ OK |

**Problem**: Filter truncates to lower end, prompt suggests upper range.

---

### Conflict 2: Style Differences
| Guideline | Intro Prompt | v3.1 DM Prompt |
|-----------|--------------|----------------|
| POV | Second person ✅ | Second person ✅ |
| Length | 12-16 sentences | 6-10 sentences |
| Style | Narrative, descriptive | Strict, factual |
| Geography | Compass tour required | Only if perceived |
| Quest Hook | Mandatory | Not required |

**Problem**: Intro is more cinematic, gameplay is stricter.

---

### Conflict 3: Scene Generator Independence
Scene generator has its own prompt in `scene_generator.py` that may not follow v3.1 rules.

**Status**: Needs audit

---

## Recommendations

### Priority 1: Align Filter with Prompts 🔥
**Issue**: Filter truncates narration at lower end of prompt range.

**Fix**:
```python
# In narration_filter.py
if context == "exploration":
    max_sentences = 10  # Not 6
elif context == "combat":
    max_sentences = 8   # Not 4
elif context == "intro":
    max_sentences = 16  # Allow full intro
```

**Impact**: Allows prompts to use full range without truncation.

---

### Priority 2: Keep Intro Separate (For Now) ℹ️
**Reason**: Campaign intro SHOULD be longer and more cinematic. This is the player's first impression.

**Recommendation**: Keep `INTRO_SYSTEM_PROMPT` as-is for now. It's only used once and sets the stage.

**Future**: Consider v3.1-ifying it later for consistency.

---

### Priority 3: Update Scene Generator ⚠️
**Issue**: Scene generator may not follow v3.1 style.

**Fix**: Update `scene_generator.py` prompt to match v3.1:
- Second person POV only
- Observable facts only
- 4-6 sentences strict
- 3 spatial directions
- No omniscience

---

### Priority 4: Create Single Source of Truth 📖
**Long-term**: All prompts should reference v3.1 as the canonical style guide.

**Structure**:
```
/app/backend/services/
  ├── prompts/
  │   ├── base_rules.py        # v3.1 core rules
  │   ├── intro_prompt.py      # Intro-specific (extends base)
  │   ├── gameplay_prompt.py   # Gameplay (extends base)
  │   └── scene_prompt.py      # Scene gen (extends base)
  └── narration_filter.py      # Enforces limits
```

---

## Immediate Action Items

### Must Do Now: 🔥
1. **Update Narration Filter** - Increase sentence limits to match prompt upper bounds
   - exploration: 6 → 10
   - combat: 4 → 8
   - intro: keep 16

### Should Do Soon: ⚠️
2. **Audit Scene Generator** - Check if it follows v3.1 style
3. **Test Intro Generation** - Verify it's not being truncated
4. **Document Prompt Locations** - Create index of all prompts

### Nice to Have: ℹ️
5. **Unify Prompts** - Create shared v3.1 base rules
6. **Add Prompt Versioning** - Track changes systematically

---

## Current State Summary

### ✅ Working Correctly:
- v3.1 DM prompt for gameplay
- Schema compatibility (check_request/requested_check)
- DC system integration
- Check resolution pipeline

### ⚠️ Needs Attention:
- Narration filter limits too restrictive
- Scene generator style may differ
- No single source of truth for style

### ℹ️ Acceptable for Now:
- Intro prompt uses different style (longer, more cinematic)
- This is intentional for first impression

---

## Testing Checklist

- [ ] Generate campaign intro
  - [ ] Verify 12-16 sentences
  - [ ] Check for quest hook
  - [ ] Verify not truncated

- [ ] Take exploration action
  - [ ] Verify 6-10 sentences (not cut at 6)
  - [ ] Check v3.1 style compliance
  - [ ] Verify POV discipline

- [ ] Enter combat
  - [ ] Verify 4-8 sentences (not cut at 4)
  - [ ] Check fast-paced style
  - [ ] Verify no omniscience

- [ ] Move to new location
  - [ ] Verify scene description
  - [ ] Check for 3 spatial directions
  - [ ] Verify style matches v3.1

---

## Conclusion

**Yes, we have multiple narrative guidelines**, but:
1. **Intro prompt** is intentionally different (longer, more cinematic)
2. **v3.1 gameplay prompt** is correctly implemented
3. **Narration filter** is too restrictive and needs updating
4. **Scene generator** needs audit for v3.1 compliance

**Recommended Next Steps**:
1. Update narration filter sentence limits
2. Audit scene generator
3. Test all generation paths
4. Consider long-term unification

**Priority**: Update narration filter NOW to prevent truncation issues.
