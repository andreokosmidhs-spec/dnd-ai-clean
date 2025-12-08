# DC System Testing Guide

## Fixes Applied

### Issue 1: AttributeError on resolution.outcome.value
**Problem**: `resolution.outcome` was already a string (due to `use_enum_values = True`), but code was trying to access `.value`

**Fixed in** `/app/backend/routers/dungeon_forge.py`:
- Line 2036: `resolution.outcome.value` → `resolution.outcome`
- Line 2067: `resolution.outcome.value.upper()` → `resolution.outcome.upper()`
- Line 2144: `resolution.outcome.value` → `resolution.outcome`

### Issue 2: Missing campaign_id/character_id
**Problem**: Frontend wasn't properly accessing campaign_id from context

**Fixed in** `/app/frontend/src/components/FocusedRPG.jsx`:
- Added `campaignId` from `useGameState()` context
- Added fallback to `character.character_id`
- Added comprehensive logging for debugging
- Added better error messages

---

## How to Test

### Step 1: Open Browser Console
1. Open app at http://localhost:3000
2. Press F12 to open developer tools
3. Go to Console tab

### Step 2: Start Game
1. Click "New Campaign"
2. Create a character (any class/race)
3. Wait for intro narration

### Step 3: Trigger a Check
Try one of these actions:
- "I search the room for hidden doors" (Investigation check)
- "I try to sneak past the guard" (Stealth check)
- "I attempt to climb the wall" (Athletics check)
- "I try to persuade the merchant" (Persuasion check)

### Step 4: Watch Console Logs
You should see:
```
🎯 Check request received in FocusedRPG: {...}
```

### Step 5: Use Check Panel
1. **CheckRollPanel appears** (bottom-right corner)
2. **Verify displays**:
   - Action context
   - Check type (e.g., "Investigation (intelligence)")
   - DC value with color (e.g., "DC 15" in yellow)
   - Your modifier (e.g., "+3")
3. **Click "Roll Dice"**
4. **Wait for animation** (800ms)
5. **Verify roll result**:
   - D20 roll shown
   - Total calculated
   - Success/failure status
   - Outcome tier (e.g., "marginal success")

### Step 6: Submit Roll
1. **Click "Continue Adventure"**
2. **Watch console logs**:
   ```
   🎲 Submitting roll: {campaignId, characterId, rollResult, pendingCheck}
   📤 Calling /api/rpg_dm/resolve_check...
   📥 Response status: 200
   📥 Response data: {...}
   ✅ Check resolved successfully
   ```
3. **Verify UI updates**:
   - Panel disappears
   - DM narration appears in chat
   - Toast notification shows (e.g., "✓ clear success")

---

## Console Logs to Watch For

### Success Flow:
```
🎯 Check request received in FocusedRPG: {ability, skill, dc, ...}
🎲 Submitting roll: {campaignId: "...", characterId: "...", ...}
📤 Calling /api/rpg_dm/resolve_check...
📥 Response status: 200
📥 Response data: {success: true, data: {...}}
✅ Check resolved successfully
```

### Error: Missing Session Info:
```
❌ Missing campaign_id or character_id {campaignId: null, characterId: null}
```
**Fix**: Make sure you're in an active game session

### Error: Network/Backend:
```
❌ Error resolving check: [error message]
```
**Check**: Backend logs at `/var/log/supervisor/backend.err.log`

---

## Backend Logs

### Check backend logs:
```bash
tail -f /var/log/supervisor/backend.err.log
```

### Successful check resolution:
```
🎲 Check Resolution: Investigation check
   Roll: 14 + 3 = 17
   DC: 15 | Result: marginal_success (margin: +2)
```

### Error logs:
- Look for "resolve_check" errors
- Look for Python tracebacks

---

## Common Issues

### 1. Panel doesn't appear
**Cause**: DM didn't return check_request in response  
**Debug**: Check backend logs for DC calculation  
**Fix**: Make sure action requires a check (e.g., search, climb, persuade)

### 2. "Missing session information" error
**Cause**: campaignId or characterId not found  
**Debug**: Check console logs for actual values  
**Fix**: 
- Verify you're in an active game (not just on landing page)
- Check localStorage: `localStorage.getItem('game-state-campaign-id')`
- Check character object: `console.log(character)`

### 3. Button click does nothing
**Cause**: JavaScript error or network failure  
**Debug**: Check browser console for errors  
**Fix**: See console error message

### 4. Backend 500 error
**Cause**: Python exception in resolve_check endpoint  
**Debug**: Check `/var/log/supervisor/backend.err.log`  
**Fix**: Check for missing imports or type errors

---

## Expected DC Calculations

### Easy Actions:
- "I jump over the small stream" → DC 10 (easy)
- "I climb a tree with good handholds" → DC 11 (easy)

### Moderate Actions:
- "I search the room" → DC 15 (moderate)
- "I persuade the merchant" → DC 15 (moderate)
- "I climb the wall" → DC 15 (moderate)

### Hard Actions:
- "I pick the complex lock" → DC 18-20 (hard)
- "I sneak past the alert guards" → DC 20 (hard)

### Very Hard Actions:
- "I climb the icy cliff in a storm" → DC 22-25 (very hard)
- "I persuade the hostile king" → DC 25 (very hard)

### Modifiers:
- Rain: +2 DC
- Darkness: +5 DC
- Combat/guards nearby: +2-5 DC (high/critical risk)
- Ideal conditions: -2 DC

---

## Success Criteria

✅ Check panel appears after appropriate action  
✅ DC is calculated systematically (not random)  
✅ Modifier shown matches character stats  
✅ Roll animation works  
✅ Success/failure calculated correctly  
✅ "Continue Adventure" submits roll  
✅ Backend resolves check  
✅ DM narrates based on outcome  
✅ Panel disappears after submission  
✅ Toast notification shows outcome  
✅ Game state updates (HP, location, etc.)

---

## Troubleshooting Commands

### Check services:
```bash
sudo supervisorctl status
```

### Restart services:
```bash
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

### View logs:
```bash
# Backend errors
tail -f /var/log/supervisor/backend.err.log

# Backend output
tail -f /var/log/supervisor/backend.out.log

# Frontend errors
tail -f /var/log/supervisor/frontend.err.log
```

### Test backend directly:
```bash
curl -X POST http://localhost:8001/api/rpg_dm/resolve_check \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "test",
    "character_id": "test",
    "player_roll": {
      "d20_roll": 15,
      "modifier": 5,
      "total": 20,
      "advantage_state": "normal",
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
      "action_context": "Testing"
    }
  }'
```

---

**Last Updated**: 2025-12-04  
**Status**: Ready for testing with enhanced logging
