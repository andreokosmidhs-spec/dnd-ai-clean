# DC System Integration Notes

## Current Flow (As of Implementation)

### 1. Action → Check Flow

**Entry Point:** Player submits action via `/api/dungeon-forge/action`

**Flow:**
```
1. Player Action → dungeon_forge.py process_action()
2. Intent Tagger analyzes action → determines if check needed
3. Build DM Prompt → includes intent_flags with check requirements
4. DM LLM generates response → includes check_request with DC
5. Response sent to frontend → displays CheckRequestCard
6. Player rolls dice → RollResultCard shows result vs DC
```

**Key Files:**
- `/app/backend/routers/dungeon_forge.py` - Main action processing
- `/app/backend/services/dc_calculator.py` - DC calculation logic (NEW)
- `/app/frontend/src/components/CheckRequestCard.jsx` - Shows check prompt
- `/app/frontend/src/components/RollResultCard.jsx` - Shows roll result

### 2. Check Request Structure

**Backend Model** (server.py):
```python
class CheckRequest(BaseModel):
    kind: str  # "check" | "save"
    ability: str  # "str", "dex", "con", "int", "wis", "cha"
    skill: Optional[str]  # "Stealth", "Perception", etc.
    dc: int  # REQUIRED - difficulty class
    mode: str = "normal"  # "normal" | "advantage" | "disadvantage"
    situational_bonus: int = 0
    reason: str
    on_success: str
    on_partial: Optional[str] = None
    on_fail: str
    ask_player_to_roll: bool = True
```

### 3. DC Determination (HYBRID APPROACH)

**Backend Suggestion:**
- `dc_calculator.py` provides suggested DC based on:
  - Action keywords ("quietly", "quickly", "carefully")
  - World state (combat, darkness, noise)
  - Character level
  - D&D 5e guidelines

**LLM Decision:**
- DM system prompt includes DC guidelines
- LLM sees suggested_dc (if calculated)
- LLM can accept or adjust ±5 with reasoning
- Final DC must be 5-30

**Current State:**
- ✅ DC guidelines added to DM prompt
- ✅ dc_calculator.py created with logic
- ⏳ Need to integrate dc_calculator into action flow
- ⏳ Need to add suggested_dc field to flow

---

## Integration Points

### A. DM Prompt (COMPLETED)
**File:** `/app/backend/routers/dungeon_forge.py`
**Function:** `build_a_version_dm_prompt()`
**Lines:** ~1029-1080

Added DC guidelines section with:
- DC 5-30 scale
- Circumstance modifiers
- Examples
- Output format

### B. DC Calculator Service (COMPLETED)
**File:** `/app/backend/services/dc_calculator.py`

**Functions:**
1. `calculate_dc(action, base_difficulty, context, character_level)` - Manual calculation
2. `infer_dc_from_action(action, world_state, character_level)` - Automatic inference
3. `get_dc_guidelines_for_prompt()` - Guidelines text for prompts

**Example Usage:**
```python
from services.dc_calculator import infer_dc_from_action

suggested_dc = infer_dc_from_action(
    action="I quietly sneak past the guard",
    world_state={"in_combat": False, "visibility": "normal"},
    character_level=character_state.get("level", 1)
)
# Returns: 15 (medium difficulty for stealth)
```

### C. Action Processing (TODO)
**File:** `/app/backend/routers/dungeon_forge.py`
**Function:** `process_action()`
**Line:** ~1460

**Needed Changes:**
1. Import dc_calculator
2. Calculate suggested_dc when check needed
3. Pass suggested_dc to DM prompt
4. Store suggested_dc in response

### D. Frontend Display (COMPLETED - No changes needed)
**Files:**
- `/app/frontend/src/components/CheckRequestCard.jsx` - Already displays DC
- `/app/frontend/src/components/RollResultCard.jsx` - Already shows "vs DC"

**Current:** Works if DC is provided in check_request
**Issue:** DC often undefined because LLM doesn't generate it consistently
**Fix:** Backend will suggest DC, LLM will use it

---

## DC Calculation Examples

### Example 1: Stealth
```python
# Action: "I sneak past the guard quietly"
infer_dc_from_action(
    action="I sneak past the guard quietly",
    world_state={"visibility": "normal"},
    character_level=3
)
# Result: DC 15 (medium - standard stealth check)
```

### Example 2: Combat Stealth
```python
# Action: "I quickly hide behind the crate"
infer_dc_from_action(
    action="I quickly hide behind the crate",
    world_state={"in_combat": True},
    character_level=3
)
# Result: DC 17 (15 base + 2 combat)
```

### Example 3: Difficult Conditions
```python
# Action: "I sneak through the dark alley"
infer_dc_from_action(
    action="I sneak through the dark alley",
    world_state={"visibility": "dark"},
    character_level=3
)
# Result: DC 20 (15 base + 5 darkness)
```

---

## Known Issues & Solutions

### Issue 1: DC is undefined in rolls
**Symptom:** Roll result shows "vs DC: (blank)"
**Root Cause:** LLM not generating DC values consistently
**Solution:** 
- ✅ Add DC guidelines to prompt (DONE)
- ⏳ Add backend DC suggestion (TODO)
- ⏳ Validate DC always present (TODO)

### Issue 2: Modifier undefined
**Symptom:** Roll result shows "Modifier: undefined"
**Root Cause:** Character stats not loaded properly
**Solution:**
- ✅ Added error handling in dndMechanics.js (DONE)
- ⏳ Need to debug character state loading (TODO)

---

## Next Steps

1. **Integrate DC Calculator into Action Flow**
   - Import dc_calculator in process_action()
   - Calculate suggested_dc when intent_flags.needs_check = true
   - Pass suggested_dc to DM prompt builder

2. **Add suggested_dc Field**
   - Extend check context passed to LLM
   - Store suggested_dc alongside final DC
   - Log when LLM adjusts DC from suggestion

3. **Validation & Fallbacks**
   - If LLM doesn't provide DC, use suggested_dc as final_dc
   - Clamp all DCs to 5-30 range
   - Log warnings for unusual DCs

4. **Testing**
   - Test various action types
   - Verify DCs are consistent
   - Check modifier display
   - Ensure no crashes

---

## Maintenance Notes

**To adjust DC difficulty:**
- Edit `DC_GUIDELINES` dict in `dc_calculator.py`
- Modify `CONTEXT_MODIFIERS` for circumstance bonuses
- Update DM prompt guidelines if needed

**To add new check types:**
- Add keywords to `infer_dc_from_action()` detection
- Consider adding new context modifiers

**To debug DC issues:**
- Check backend logs for "📊 Calculated DC" messages
- Check frontend console for "🎯 Check request received" logs
- Verify check_request.dc is not null/undefined
