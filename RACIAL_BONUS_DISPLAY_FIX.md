# Racial Bonus Display Fix

## Issue
User selected Human race but couldn't see the +1 to all stats being applied in the StatForge component.

## Root Cause
The StatForge component was only showing the base rolled stats without indicating that racial bonuses would be (or were) applied. The racial ASI data structure was also stored as an array, making it difficult to display bonuses per ability.

## Changes Made

### 1. **Restructured Racial ASI Storage** (`/app/frontend/src/utils/raceHelpers.js`)

**Before:**
```javascript
updated.racial_asi = asiArray; // Array format: [{ability: "ALL", value: 1}]
```

**After:**
```javascript
updated.racial_asi = {
  strength: 1,
  dexterity: 1,
  constitution: 1,
  intelligence: 1,
  wisdom: 1,
  charisma: 1
}; // Flat object for easy access
```

**Benefits:**
- Easy to check bonus for any ability: `character.racial_asi.strength`
- Simple to display in UI
- Works for all races (Human, Elf, Dwarf, etc.)

---

### 2. **Added Racial Bonus Display in StatForge** (`/app/frontend/src/components/StatForge.jsx`)

#### A. Header Info Box
Shows which race is selected and what bonuses will be applied:

```jsx
Human (no subrace) Racial Bonuses:
STR +1  DEX +1  CON +1  INT +1  WIS +1  CHA +1
These bonuses will be added to your assigned scores
```

#### B. Stat Assignment Display
Shows base stat + racial bonus = final stat:

**Before:**
```
STR: 13 (+1)  // Just shows final value
```

**After:**
```
STR: 13 +1 = 14 (+2)  // Shows: base + racial = final (modifier)
```

#### C. Summary Section
The "Your Legend is Forged!" box now shows the math:

**For Human with STR 13:**
```
STR: 13 +1 = 14 (+2)
DEX: 16 +1 = 17 (+3)
CON: 13 +1 = 14 (+2)
INT: 14 +1 = 15 (+2)
WIS: 14 +1 = 15 (+2)
CHA: 14 +1 = 15 (+2)
```

---

### 3. **Updated removeRacialBonuses** (`/app/frontend/src/utils/raceHelpers.js`)

Now properly removes bonuses using the new flat object structure:

```javascript
Object.keys(updated.racial_asi).forEach(stat => {
  if (updated.stats[stat] !== undefined && updated.racial_asi[stat] > 0) {
    updated.stats[stat] = updated.stats[stat] - updated.racial_asi[stat];
  }
});
```

---

## Visual Examples

### Human Character (All +1)
```
┌─────────────────────────────────────────┐
│ Human Racial Bonuses:                    │
│ STR +1  DEX +1  CON +1                   │
│ INT +1  WIS +1  CHA +1                   │
│ These bonuses will be added to scores   │
└─────────────────────────────────────────┘

STR: [13] +1 = [14] (+2)  ← Base + Racial = Final
DEX: [16] +1 = [17] (+3)
CON: [13] +1 = [14] (+2)
INT: [14] +1 = [15] (+2)
WIS: [14] +1 = [15] (+2)
CHA: [14] +1 = [15] (+2)
```

### Mountain Dwarf (+2 CON, +2 STR)
```
┌─────────────────────────────────────────┐
│ Dwarf (Mountain Dwarf) Racial Bonuses:  │
│ STR +2  CON +2                           │
│ These bonuses will be added to scores   │
└─────────────────────────────────────────┘

STR: [13] +2 = [15] (+2)  ← Gets +2 from subrace
DEX: [16] (no racial bonus) (+3)
CON: [16] +2 = [18] (+4)  ← Gets +2 from base race
INT: [14] (+2)
WIS: [12] (+1)
CHA: [10] (+0)
```

### High Elf (+2 DEX, +1 INT)
```
┌─────────────────────────────────────────┐
│ Elf (High Elf) Racial Bonuses:          │
│ DEX +2  INT +1                           │
│ These bonuses will be added to scores   │
└─────────────────────────────────────────┘

STR: [10] (+0)
DEX: [16] +2 = [18] (+4)  ← Gets +2 from base race
CON: [14] (+2)
INT: [14] +1 = [15] (+2)  ← Gets +1 from subrace
WIS: [12] (+1)
CHA: [13] (+1)
```

---

## How It Works Now

### Step 1: Race Selection
When user selects a race (e.g., Human):
```javascript
applyRaceToCharacter("Human", character)
```

This calculates and stores:
```javascript
character.racial_asi = {
  strength: 1,
  dexterity: 1,
  constitution: 1,
  intelligence: 1,
  wisdom: 1,
  charisma: 1
}
```

### Step 2: StatForge Display
When StatForge component loads, it:
1. Shows info box: "Human Racial Bonuses: STR +1, DEX +1, ..."
2. As stats are assigned, shows: "Base + Racial = Final"
3. Summary shows full calculation for all stats

### Step 3: Stat Assignment
When user assigns a stat (e.g., 13 to STR):
- Base stat stored: `assignments.strength = 13`
- Racial bonus read: `character.racial_asi.strength = 1`
- Final displayed: `13 + 1 = 14 (+2)`

### Step 4: Character Completion
When stats are finalized:
- Base stats are stored
- Racial bonuses are applied to create final stats
- Final stats sent to backend

---

## Testing Checklist

### Test with Human (All +1)
- [ ] Create new character, select Human
- [ ] In StatForge, see "Human Racial Bonuses: STR +1 DEX +1 CON +1 INT +1 WIS +1 CHA +1"
- [ ] Assign stat 13 to STR
- [ ] See "13 +1 = 14 (+2)" displayed
- [ ] Complete all assignments
- [ ] Summary shows all stats with +1 bonus visible
- [ ] Final stats are correct: base + 1 for each

### Test with Mountain Dwarf (+2 CON, +2 STR)
- [ ] Select Dwarf, then Mountain Dwarf subrace
- [ ] See "Dwarf (Mountain Dwarf) Racial Bonuses: STR +2 CON +2"
- [ ] Assign stat 16 to CON
- [ ] See "16 +2 = 18 (+4)"
- [ ] Stats without bonuses (DEX, INT, WIS, CHA) show no racial bonus

### Test with High Elf (+2 DEX, +1 INT)
- [ ] Select Elf, then High Elf subrace
- [ ] See "Elf (High Elf) Racial Bonuses: DEX +2 INT +1"
- [ ] Assign stat 16 to DEX
- [ ] See "16 +2 = 18 (+4)"
- [ ] Assign stat 14 to INT
- [ ] See "14 +1 = 15 (+2)"

### Test Race Change
- [ ] Select Human (all +1)
- [ ] Assign some stats
- [ ] Change to Elf
- [ ] Bonuses update correctly (DEX +2, others 0)
- [ ] Previous stat assignments reset or update correctly

---

## Files Modified

1. `/app/frontend/src/utils/raceHelpers.js`
   - Changed `applyRacialASI()` to store bonuses as flat object
   - Updated `removeRacialBonuses()` for new structure

2. `/app/frontend/src/components/StatForge.jsx`
   - Added racial bonus info box in header
   - Updated stat display to show "base + racial = final"
   - Updated summary to show full calculation

---

## Benefits

✅ **Transparency:** Players can see exactly where their stats come from
✅ **Clarity:** No confusion about whether racial bonuses are applied
✅ **Education:** New players learn how D&D racial bonuses work
✅ **Verification:** Easy to spot if bonuses are wrong
✅ **Flexibility:** Works for all races and subraces

---

## Before vs After

### Before (User's Issue)
```
Human selected
StatForge shows:
STR: 13 (+1)  ← Where's my +1 racial bonus?
DEX: 16 (+3)
...
```
User thinks: "Did it apply the +1 or not? I can't tell!"

### After (Fixed)
```
Human Racial Bonuses: STR +1 DEX +1 CON +1 INT +1 WIS +1 CHA +1
These bonuses will be added to your assigned scores

STR: 13 +1 = 14 (+2)  ← Clear! Base 13 + Racial 1 = Final 14
DEX: 16 +1 = 17 (+3)
...
```
User thinks: "Perfect! I can see my Human bonuses are applied!"

---

This fix ensures players always know what their racial bonuses are and can verify they're being applied correctly! 🎲
