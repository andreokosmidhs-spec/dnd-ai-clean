# Narration Length Fix - v6.1 Alignment

## Summary
Fixed the backend narration truncation issue where DM responses were being force-truncated to 4-6 sentences regardless of scene_mode, preventing the v6.1 sentence-count rules from taking effect.

## Problem
The backend was applying hardcoded sentence limits (4-6 sentences) through the NarrationFilter, overriding the DM Engine's v6.1 prompt instructions. This caused:
- Intro narrations truncated to 16→6 sentences
- Exploration narrations truncated to 10→6 sentences  
- Double-filtering: narration filtered twice in the same request
- Mode-agnostic limits that didn't respect scene context

## Solution Implemented

### 1. Added MODE_LIMITS Dictionary
Created a centralized mapping in `dungeon_forge.py` that matches the v6.1 spec:

```python
MODE_LIMITS = {
    "intro": {"min": 12, "max": 16},
    "exploration": {"min": 6, "max": 10},
    "social": {"min": 6, "max": 10},
    "combat": {"min": 4, "max": 8},
    "downtime": {"min": 4, "max": 8},
    "travel": {"min": 6, "max": 8},
    "rest": {"min": 3, "max": 6},
}
```

### 2. Replaced Hardcoded Limits
Changed all `NarrationFilter.apply_filter()` calls from hardcoded values to mode-aware limits:

**Before:**
```python
NarrationFilter.apply_filter(narration_text, max_sentences=6, context="exploration")
```

**After:**
```python
current_mode = session_mode.get("mode", "exploration")
limits = MODE_LIMITS.get(current_mode, {"min": 6, "max": 10})
NarrationFilter.apply_filter(narration_text, max_sentences=limits["max"], context=f"{current_mode}_narration")
```

### 3. Removed Double-Filtering
Eliminated duplicate filter passes that were cutting narration twice:
- Removed lines 2956-2963 (redundant filter after line 2715)
- Removed lines 3072-3075 (redundant final filter)
- Kept single filter pass per narration at line 2715

### 4. Scene Description Limits
Updated scene description filters to use exploration limits (scenes describe environments):
```python
exploration_limits = MODE_LIMITS.get("exploration", {"min": 6, "max": 10})
NarrationFilter.apply_filter(scene_data["description"], max_sentences=exploration_limits["max"], ...)
```

## Files Modified

### `/app/backend/routers/dungeon_forge.py`
- **Line 42-51**: Added MODE_LIMITS dictionary
- **Line 520**: Intro loading (already correct at 16)
- **Line 556**: Scene description (6 → 10 for exploration)
- **Line 661**: Intro generation (already correct at 16)
- **Line 738**: Scene description (6 → 10 for exploration)
- **Line 1549**: Character intro (already correct at 16)
- **Line 1621**: Scene description (6 → 10 for exploration)
- **Line 1802**: Check resolution (6 → 10 for exploration default)
- **Line 2715**: Main narration filter (uses scene_mode context - KEPT AS PRIMARY)
- **Line 2936**: Combat start (4 → 8 for combat mode)
- **Line 2956-2963**: REMOVED (duplicate filter)
- **Line 3061**: Scene injection (6 → mode-aware)
- **Line 3072-3075**: REMOVED (duplicate filter)

### `/app/backend/services/narration_filter.py`
- No changes needed (already has SENTENCE_LIMITS that match v6.1)

## Expected Behavior After Fix

| scene_mode   | Min Sentences | Max Sentences | Old Behavior | New Behavior |
|--------------|---------------|---------------|--------------|--------------|
| intro        | 12            | 16            | Truncated to 6 | Allows 12-16 |
| exploration  | 6             | 10            | Truncated to 6 | Allows 6-10  |
| social       | 6             | 10            | Truncated to 4 | Allows 6-10  |
| combat       | 4             | 8             | Truncated to 4 | Allows 4-8   |
| downtime     | 4             | 8             | Truncated to 4 | Allows 4-8   |
| travel       | 6             | 8             | Truncated to 6 | Allows 6-8   |
| rest         | 3             | 6             | Truncated to 4 | Allows 3-6   |

## Testing Instructions

### Manual Test
```bash
# 1. Test intro generation (should allow 12-16 sentences)
curl -X POST "http://localhost:8001/api/intro/generate" \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": "test_campaign", "character_id": "test_char"}'
# Count sentences in response - should be 12-16

# 2. Test exploration narration (should allow 6-10 sentences)  
curl -X POST "http://localhost:8001/api/rpg_dm/action" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "test_campaign",
    "character_id": "test_char", 
    "player_action": "I explore the town square",
    "scene_mode": "exploration"
  }'
# Count sentences in narration - should be 6-10

# 3. Test combat narration (should allow 4-8 sentences)
curl -X POST "http://localhost:8001/api/rpg_dm/action" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "test_campaign",
    "character_id": "test_char",
    "player_action": "I attack the goblin",
    "scene_mode": "combat"  
  }'
# Count sentences in narration - should be 4-8
```

### Automated Test Helper
Create `/app/backend/tests/test_narration_limits.py`:
```python
import re

def count_sentences(text: str) -> int:
    """Count sentences ending with . ! ?"""
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])

def test_intro_length(intro_response):
    narration = intro_response["intro_markdown"]
    count = count_sentences(narration)
    assert 12 <= count <= 16, f"Intro should be 12-16 sentences, got {count}"
    
def test_exploration_length(dm_response, scene_mode="exploration"):
    narration = dm_response["narration"]
    count = count_sentences(narration)
    assert 6 <= count <= 10, f"Exploration should be 6-10 sentences, got {count}"
    
def test_combat_length(dm_response, scene_mode="combat"):
    narration = dm_response["narration"]
    count = count_sentences(narration)
    assert 4 <= count <= 8, f"Combat should be 4-8 sentences, got {count}"
```

## Log Verification
After the fix, backend logs should show:
```
✅ Narration filtered: 14 sentences, 847 chars (intro mode)
✅ Narration filtered: 8 sentences, 412 chars (exploration mode)
✅ Narration filtered: 6 sentences, 298 chars (combat mode)
```

NOT:
```
⚠️ Narration truncated from 14 to 6 sentences
⚠️ LLM VIOLATED 16-SENTENCE LIMIT for intro: Generated 14, truncated to 6
```

## Rollback Plan
If this change causes issues:

```bash
# Revert MODE_LIMITS addition
git diff HEAD~1 /app/backend/routers/dungeon_forge.py
git checkout HEAD~1 -- /app/backend/routers/dungeon_forge.py

# Or manually restore:
# 1. Remove MODE_LIMITS dict (lines 42-51)
# 2. Restore hardcoded max_sentences=6 at all scene filter locations
# 3. Restore hardcoded max_sentences=4 for combat
# 4. Restore lines 2956-2963 (exploration filter)
# 5. Restore lines 3072-3075 (final safety filter)
```

## Notes
- Intro generation already correctly used `max_sentences=16` (no change needed)
- Scene descriptions now use exploration limits (10 max) since they describe environments
- Check resolution uses exploration limits (10 max) as a sensible default
- Clarification messages (3 sentences) unchanged - they're system messages, not narration
- The primary filter at line 2715 uses `scene_mode` from DM response for accurate context

## Next Steps
1. Test with backend testing agent to verify all modes respect limits
2. Monitor logs for any "VIOLATED SENTENCE LIMIT" warnings
3. If DM Engine still over-generates, the self-correction rules in v6.1 prompt should handle it
4. Consider extending NarrationFilter to support `min_sentences` enforcement (future enhancement)
