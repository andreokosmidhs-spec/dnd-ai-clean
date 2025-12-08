# DC System Fix - Session Mode Error

## Issue Fixed

### Error Message:
```
KeyError: 'narration_style'
```

### Root Cause:
When calling `run_dungeon_forge` from the `resolve_check` endpoint, we passed:
```python
session_mode={"mode": "check_resolution"}
```

But the `format_session_prompt` function expected a fully-formed session mode dict with fields like `narration_style`, `pacing`, etc.

### Fix Applied:
Changed to:
```python
session_mode=None  # No specific mode for check resolution
```

**Location**: `/app/backend/routers/dungeon_forge.py`, line 2093

---

## Why This Works

The `session_mode` parameter is optional in `run_dungeon_forge`. When it's `None`, the system doesn't try to format session-specific prompts, avoiding the KeyError.

Check resolution doesn't need session mode because:
1. The check has already been defined (DC, ability, skill set)
2. The roll has already happened (we have the result)
3. We just need the DM to narrate the outcome

---

## Testing Instructions

### Prerequisites:
1. **Must be in an active game session** (not just on landing page)
2. **Must have a valid character created**
3. **Browser console must be open** (F12 → Console tab)

### Step-by-Step Test:

#### 1. Start or Load Game
```
Option A: Click "New Campaign" → Create character
Option B: Click "Continue" → Select existing character
```

#### 2. Verify Session Active
Check console should show:
```
✅ Character loaded
✅ Campaign loaded
```

Check localStorage (Console):
```javascript
localStorage.getItem('game-state-campaign-id')
// Should return a campaign ID like "abc-123-def-456"
```

#### 3. Take Action That Requires Check
Examples:
- "I search the room carefully"
- "I try to sneak past the guard"
- "I attempt to climb the cliff"
- "I try to pick the lock"

#### 4. Watch Console Logs
Should see:
```
🎯 Check request received in FocusedRPG: {
  ability: "intelligence",
  skill: "Investigation",
  dc: 15,
  dc_band: "moderate",
  ...
}
```

#### 5. Check Panel Appears
- Bottom-right corner
- Shows DC and modifier
- Roll button enabled

#### 6. Roll Dice
Click "Roll Dice"
- Animation plays
- Result shows (e.g., "16 + 3 = 19")
- Success/failure displayed

#### 7. Continue Adventure
Click "Continue Adventure"

**Console should show:**
```
🎲 Submitting roll: {
  campaignId: "abc-123-def-456",
  characterId: "char-789",
  rollResult: {...},
  pendingCheck: {...}
}
📤 Calling /api/rpg_dm/resolve_check...
📥 Response status: 200
📥 Response data: {success: true, data: {...}}
✅ Check resolved successfully
```

**Backend logs should show:**
```
🎲 Check Resolution: Investigation check
   Roll: 16 + 3 = 19
   DC: 15 | Result: clear_success (margin: +4)
```

#### 8. Verify UI Updates
- Panel disappears
- DM narration appears in chat
- Toast notification shows (e.g., "✓ clear success")

---

## Common Errors & Fixes

### Error: "Missing session information"
**Console shows:**
```
❌ Missing campaign_id or character_id
```

**Cause**: Not in an active game session

**Fix**: 
1. Make sure you started a new campaign or loaded an existing one
2. Verify localStorage has campaign ID:
   ```javascript
   localStorage.getItem('game-state-campaign-id')
   ```
3. If null, reload page and start/load game again

---

### Error: "Campaign not found"
**Response shows:**
```json
{
  "success": false,
  "error": {
    "type": "not_found",
    "message": "Campaign xyz not found"
  }
}
```

**Cause**: Campaign ID from frontend doesn't match any campaign in database

**Debug**:
```javascript
// In console, check what's being sent:
localStorage.getItem('game-state-campaign-id')
```

**Fix**:
1. Start a fresh campaign
2. Make sure you don't navigate away mid-game
3. If persists, clear localStorage and restart:
   ```javascript
   localStorage.clear()
   location.reload()
   ```

---

### Error: "Character not found"
**Similar to campaign not found**

**Cause**: Character ID mismatch

**Check**:
```javascript
// In console
console.log(character)
// Should show character object with id or character_id
```

**Fix**: Create a new character

---

### Error: Backend 500 Error
**Console shows:**
```
📥 Response status: 500
```

**Check backend logs:**
```bash
tail -f /var/log/supervisor/backend.err.log
```

**Common causes:**
1. Missing imports
2. Type errors in data
3. Database connection issues

---

## Verification Checklist

Before testing, verify:

- [ ] Backend service running: `sudo supervisorctl status backend`
- [ ] Frontend service running: `sudo supervisorctl status frontend`
- [ ] Browser console open (F12)
- [ ] In an active game (not landing page)
- [ ] Character created and loaded

During test:

- [ ] Check panel appears after appropriate action
- [ ] DC value is shown (not undefined)
- [ ] Modifier is calculated correctly
- [ ] Roll animation works
- [ ] Success/failure determined correctly
- [ ] "Continue Adventure" triggers console logs
- [ ] Response status is 200 (not 404, 500, etc.)
- [ ] DM narration appears in chat
- [ ] Panel disappears after submission
- [ ] Toast notification shows

---

## Backend Endpoint Test (Direct)

To test the endpoint without the frontend:

```bash
# First, get a real campaign_id and character_id from the database
mongo rpg_forge --eval "db.campaigns.findOne({}, {campaign_id: 1})"
mongo rpg_forge --eval "db.characters.findOne({}, {character_id: 1})"

# Then test with real IDs:
curl -X POST http://localhost:8001/api/rpg_dm/resolve_check \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "REAL_CAMPAIGN_ID_HERE",
    "character_id": "REAL_CHARACTER_ID_HERE",
    "player_roll": {
      "d20_roll": 15,
      "modifier": 5,
      "total": 20,
      "advantage_state": "normal",
      "advantage_rolls": null,
      "ability_modifier": 3,
      "proficiency_bonus": 2,
      "other_bonuses": 0
    },
    "check_request": {
      "ability": "strength",
      "skill": "Athletics",
      "dc": 15,
      "dc_band": "moderate",
      "advantage_state": "normal",
      "reason": "Test check",
      "action_context": "Climbing"
    }
  }'
```

**Expected response:**
```json
{
  "success": true,
  "data": {
    "narration": "You successfully climb...",
    "entity_mentions": [...],
    "options": [...],
    "resolution": {
      "success": true,
      "outcome": "clear_success",
      "margin": 5
    }
  }
}
```

---

## Files Modified

1. **`/app/backend/routers/dungeon_forge.py`**
   - Line 2093: Changed `session_mode={"mode": "check_resolution"}` → `session_mode=None`

---

**Status**: ✅ Fixed  
**Date**: 2025-12-04  
**Ready for**: Live session testing
