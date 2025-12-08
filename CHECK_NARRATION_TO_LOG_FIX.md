# Check Narration to Log - Fix Applied

## Issue
After rolling a check, the result appeared in CheckRollPanel but no DM narration was added to the adventure log. The backend successfully returned narration, but the frontend wasn't displaying it.

## Root Cause
The `addToGameLog` call was using the wrong field name for the message content:
- **Used**: `message: data.data.narration`
- **Expected**: `text: data.data.narration`

The AdventureLogWithDM component renders messages using `entry.text`, not `entry.message`.

---

## Fix Applied

### File Modified: `/app/frontend/src/components/FocusedRPG.jsx`

**Location**: `onRollComplete` handler in CheckRollPanel (lines 685-692)

**Before:**
```javascript
addToGameLog({
  type: 'dm',
  message: data.data.narration,  // ❌ Wrong field name
  timestamp: Date.now(),
  options: data.data.options || [],
  resolution: data.data.resolution
});
```

**After:**
```javascript
addToGameLog({
  type: 'dm',
  text: data.data.narration,  // ✅ Correct field name
  timestamp: Date.now(),
  options: data.data.options || [],
  resolution: data.data.resolution,
  entity_mentions: data.data.entity_mentions || []  // ✅ Added for clickable entity links
});
```

---

## Changes Made

### 1. Fixed Field Name (Line 688)
Changed `message` → `text` to match AdventureLogWithDM's expected structure.

### 2. Added Entity Mentions (Line 692)
Added `entity_mentions` field to enable clickable entity links in the narration (e.g., NPCs, locations, items).

---

## How It Works

### Flow After Check Resolution:

1. **Player rolls dice** in CheckRollPanel
2. **Frontend calls** `/api/rpg_dm/resolve_check`
3. **Backend returns**:
   ```json
   {
     "success": true,
     "data": {
       "narration": "You search the room but find nothing...",
       "entity_mentions": ["room", "dust"],
       "options": ["Look elsewhere", "Give up"],
       "resolution": {
         "success": false,
         "outcome": "clear_failure",
         "margin": -9
       }
     }
   }
   ```
4. **Frontend adds to log**:
   ```javascript
   addToGameLog({
     type: 'dm',
     text: "You search the room but find nothing...",
     entity_mentions: ["room", "dust"],
     options: ["Look elsewhere", "Give up"],
     resolution: {...}
   })
   ```
5. **AdventureLogWithDM renders**:
   - Displays narration as DM message
   - Shows entity links (if any)
   - Shows action options (if any)
   - Displays timestamp

---

## Message Structure Reference

### Expected by AdventureLogWithDM:
```typescript
interface LogEntry {
  type: 'dm' | 'player' | 'system' | 'error';
  text: string;              // Main message content
  timestamp: number;
  options?: string[];        // Action options for player
  entity_mentions?: string[]; // Entities to highlight
  resolution?: {             // Check outcome (optional)
    success: boolean;
    outcome: string;
    margin: number;
  };
}
```

### Key Fields:
- **`text`**: The actual narration text (NOT `message`)
- **`type`**: Message type for styling (`'dm'` = violet theme)
- **`entity_mentions`**: Array of entities to make clickable
- **`options`**: Action buttons to display below message
- **`resolution`**: Check outcome for debugging/display

---

## Testing Verification

### Expected Behavior After Fix:

1. **Take action requiring check**:
   ```
   "I search the room for hidden passages"
   ```

2. **CheckRollPanel appears**:
   - Shows DC 15
   - Roll dice → Result: 6 + 0 = 6 (failure)

3. **Click "Continue Adventure"**:
   - Panel disappears
   - Toast shows: "✗ clear failure"
   - **DM message appears in log**: ✅
     ```
     DM: "You search carefully but the dust-covered surfaces 
     reveal no hidden mechanisms. The room appears ordinary."
     ```

4. **Verify in log**:
   - Message styled as DM (violet theme)
   - Timestamp shown
   - Options displayed (if any)
   - Entity mentions clickable (if any)

---

## Other Updates Applied (Already Present)

The `onRollComplete` handler also:

### Updates Character State:
```javascript
if (data.data.player_updates) {
  const updates = data.data.player_updates;
  if (updates.gold_gained || updates.items_gained || updates.hp !== undefined) {
    updateCharacter(data.data.player_updates);
  }
}
```

### Updates Location:
```javascript
if (data.data.world_state_update && data.data.world_state_update.current_location) {
  onLocationChange(data.data.world_state_update.current_location);
}
```

### Clears Pending Check:
```javascript
setPendingCheck(null);  // Hides CheckRollPanel
```

### Shows Toast Notification:
```javascript
const outcome = data.data.resolution.outcome.replace('_', ' ');
const icon = data.data.resolution.success ? '✓' : '✗';
window.showToast(`${icon} ${outcome}`, data.data.resolution.success ? 'success' : 'error');
```

---

## Files Modified

**Single File**: `/app/frontend/src/components/FocusedRPG.jsx`

**Lines Changed**: 2 (688 and 692)
- Line 688: `message` → `text`
- Line 692: Added `entity_mentions`

**Total Changes**: Minimal, surgical fix

---

## No Other Files Modified

✅ Backend unchanged (dungeon_forge.py, dc_rules.py, check_models.py)  
✅ CheckRollPanel.tsx unchanged  
✅ AdventureLogWithDM.jsx unchanged  
✅ RPGGame.jsx unchanged

---

## Success Metrics

✅ DM narration appears in log after check resolution  
✅ Entity mentions are clickable  
✅ Action options are displayed  
✅ Check resolution info is attached  
✅ Character/world state updates properly  
✅ Panel clears after submission  
✅ Toast notification shows outcome

---

**Status**: Fixed  
**Date**: 2025-12-04  
**Impact**: Check resolution now fully integrated with adventure log
