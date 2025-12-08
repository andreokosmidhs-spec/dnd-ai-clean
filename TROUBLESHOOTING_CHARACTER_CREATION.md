# Troubleshooting Character Creation Issues

## Current Status
- ✅ Backend is working (returning 200 OK)
- ✅ Emergent LLM key is active
- ✅ No budget/quota issues detected
- ❌ Frontend shows "something went wrong"

## What We've Fixed So Far

### Fix 1: Cantrip Serialization
- Issue: Cantrips array had non-serializable data
- Solution: Serialize to plain objects before sending

### Fix 2: Field Mapping
- Issue: RPGGame looking for `virtues`, `flaws`, `goals` that don't exist
- Solution: Map to correct fields (`traits`, `flaws_detailed`, `aspiration`)

### Fix 3: Racial ASI Mapping
- Issue: DEX/CHA codes not mapping to dexterity/charisma
- Solution: Added ability code mapping

## Possible Remaining Issues

### Issue 1: Timeout During Generation
**Symptoms:** Long wait, then "something went wrong"

**Cause:** World/intro generation takes 30-60 seconds, might timeout

**Solution:**
1. Increase timeout in API calls
2. Add loading messages to show progress
3. Try with simpler character first

**Test:**
- Create Human Fighter (simple, no cantrips)
- If works: Issue is with complex races
- If fails: Issue is with core flow

---

### Issue 2: localStorage Size Limit
**Symptoms:** Works first time, fails on subsequent attempts

**Cause:** localStorage has 5-10MB limit, character data might be too large

**Solution:**
```javascript
// Clear old data
localStorage.clear();
// Or specifically:
localStorage.removeItem('rpg-campaign-character');
localStorage.removeItem('dm-intro-played');
```

**Test:**
Open browser console (F12) and run:
```javascript
localStorage.clear();
location.reload();
```

---

### Issue 3: Browser Console Errors
**Need:** Actual error message from browser

**How to Check:**
1. Press F12 to open DevTools
2. Go to Console tab
3. Look for red error messages
4. Screenshot or copy the error
5. Share with developer

**Common Errors:**
- `TypeError: Cannot read property 'X' of undefined` → Missing field
- `QuotaExceededError` → localStorage full
- `NetworkError` → API timeout
- `JSON.parse error` → Bad data format

---

### Issue 4: Race-Specific Data Issues
**Symptoms:** Works for some races, not others

**Possible Causes:**
- Drow subrace data malformed
- racial_asi not calculating correctly
- cantrips array structure wrong

**Test Each Race:**
- ✅ Human (no special features)
- ❓ Elf → High Elf (cantrip choice)
- ❓ Elf → Dark Elf (automatic cantrip)
- ❓ Dwarf → Mountain Dwarf (+2 STR, +2 CON)
- ❓ Tiefling (automatic Thaumaturgy)

---

### Issue 5: Stats Not Assigned
**Symptoms:** Error mentions stats or abilities

**Cause:** StatForge completion not properly saved

**Check:**
- Are all 6 stats assigned in StatForge?
- Is character.stats object populated?
- Are racial bonuses applied?

**Debug:**
```javascript
console.log('Character stats:', character.stats);
console.log('Racial ASI:', character.racial_asi);
```

---

### Issue 6: Background/Proficiency Issues
**Symptoms:** Error during final character assembly

**Cause:** Missing background data or proficiency arrays

**Check:**
- Background selected?
- Proficiencies array populated?
- Starting equipment calculated?

---

### Issue 7: API Response Format Changed
**Symptoms:** Backend returns 200 but frontend errors

**Cause:** Response structure doesn't match expected format

**Check Backend Response:**
```javascript
// In onCharacterCreated function
const worldData = await generateWorldBlueprint(worldPayload);
console.log('World response:', worldData);

const characterData = await createCharacter(characterPayload);
console.log('Character response:', characterData);
```

**Expected Format:**
```json
{
  "campaign_id": "uuid",
  "world_blueprint": { ... },
  "character_id": "uuid",
  "intro_markdown": "text...",
  "starting_location": "town name"
}
```

---

## Debugging Steps

### Step 1: Check Browser Console
```
1. Open browser (Chrome/Firefox)
2. Press F12
3. Go to Console tab
4. Try creating character
5. Look for red errors
6. Take screenshot
```

### Step 2: Check Network Tab
```
1. In DevTools, go to Network tab
2. Try creating character
3. Look for failed requests (red)
4. Click on failed request
5. Check Response tab
6. Take screenshot
```

### Step 3: Check localStorage
```javascript
// In browser console
console.log('Character:', localStorage.getItem('rpg-campaign-character'));
console.log('Size:', JSON.stringify(localStorage).length + ' bytes');
```

### Step 4: Test Simple Character
```
1. Create Human Fighter
2. Use random stats
3. Skip optional features
4. Minimal background
5. Try to complete
```

### Step 5: Test in Incognito/Private Mode
```
1. Open browser in private mode
2. Go to app
3. Try creating character
4. If works: Issue is cached data
5. If fails: Issue is code
```

---

## Quick Fixes to Try

### Fix 1: Clear All Data
```javascript
// In browser console (F12)
localStorage.clear();
sessionStorage.clear();
location.reload();
```

### Fix 2: Use Simple Character
Create:
- Human
- Fighter
- Neutral alignment
- Any background
- Random stats
- No optional features

### Fix 3: Check API Credits
You confirmed Emergent LLM key exists. To verify it's working:
1. Go to Profile → Universal Key
2. Check balance
3. Check usage logs
4. If low, add balance

### Fix 4: Check Backend Status
```bash
# SSH into container
sudo supervisorctl status

# Should show:
# backend    RUNNING
# frontend   RUNNING
```

---

## If Nothing Works

### Nuclear Option: Fresh Start
```bash
# In container
cd /app
git stash
sudo supervisorctl restart all
```

Then try creating simplest possible character.

---

## Information Needed for Further Debug

Please provide:

1. **Browser Console Errors:**
   - Screenshot of Console tab (F12)
   - Any red error messages
   - Last 10-20 lines of logs

2. **Network Errors:**
   - Screenshot of Network tab
   - Any failed (red) requests
   - Response from failed requests

3. **Character Details:**
   - What race/subrace selected?
   - What class selected?
   - Did you select cantrip? (if High Elf)
   - Did you complete all steps?

4. **When Does It Fail:**
   - Immediately after "Begin Adventure"?
   - After loading screen appears?
   - After "Generating world..."?
   - After "Creating character..."?

5. **Does It Work For:**
   - Human Fighter? (simplest case)
   - Other races?
   - Same race different class?

---

## Current Best Guess

Based on:
- Backend returns 200 OK ✅
- No API credit issues ✅  
- Code fixes applied ✅
- Still getting error ❌

**Most Likely Issues:**
1. **JavaScript error in browser** (check console)
2. **localStorage quota exceeded** (clear storage)
3. **Specific race/subrace data issue** (try different race)
4. **Timeout during LLM calls** (world gen takes 30-60s)

**Next Action:**
Please open browser console (F12) and share what error appears when you try to create character. That will tell us exactly what's failing.
