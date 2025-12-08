# 🧪 DUNGEON FORGE - Smoke Test Checklist

## Purpose
Run this checklist after any changes to:
- State management
- Combat engine
- Character/Enemy data models
- Campaign loading/saving
- Critical UI components

## ✅ Test Flows

### 1. Campaign Loading
- [ ] Click "New Campaign" → Character creation starts
- [ ] Click "Load Last Campaign" → Campaign loads without errors
- [ ] Campaign loads → Intro narration displays in adventure log
- [ ] Campaign loads → Character sheet shows correct stats
- [ ] Campaign loads → World info panel displays
- [ ] Page refresh → Reload campaign → All data persists

**Expected**: No "Maximum update depth" errors, all data visible

---

### 2. Basic Actions
- [ ] Type simple action: "I look around"
- [ ] Press Enter or click Send
- [ ] DM response appears within 5 seconds
- [ ] Response contains narration text
- [ ] Options/suggestions appear (if provided)

**Expected**: No HTTP 500 errors, narration displays

---

### 3. Ability Checks
- [ ] Send action that triggers check: "I try to sneak past the guard"
- [ ] Check request card appears with:
  - [ ] Ability name (e.g., "Stealth")
  - [ ] DC value
  - [ ] Character modifiers shown
- [ ] Click "Roll" button
- [ ] Dice result displays
- [ ] Check outcome shown (Success/Failure)
- [ ] DM continues narration based on result

**Expected**: No crashes, full check flow completes

---

### 4. Combat Initiation
- [ ] Send combat action: "I attack the goblin"
- [ ] Combat initiates
- [ ] Combat HUD appears showing:
  - [ ] Character HP bar
  - [ ] Enemy list with HP
  - [ ] Turn order
- [ ] Ability check requested (if applicable)
- [ ] Roll dice
- [ ] Combat result narration appears

**Expected**: No KeyError for attack_bonus or damage_die

---

### 5. Combat Targeting
- [ ] Multiple enemies present (e.g., "Skeleton" and "Zombie")
- [ ] Send: "I punch the Zombie"
- [ ] Combat result shows attack on **Zombie**, not other enemy
- [ ] Send: "I attack the Skeleton"  
- [ ] Combat result shows attack on **Skeleton**

**Expected**: Correct target selection, no default-to-first-enemy behavior

---

### 6. Combat Rounds
- [ ] Player attacks enemy → Damage applied
- [ ] Enemy HP updates correctly
- [ ] Enemy attacks back → Player HP decreases
- [ ] Player HP bar updates in UI
- [ ] Combat continues for 2-3 rounds
- [ ] No crashes or HTTP 500 errors

**Expected**: HP calculations work, no undefined errors

---

### 7. Character Stats Display
- [ ] Open character drawer/sheet
- [ ] HP displays as "X/Y" format (e.g., "8/10")
- [ ] HP bar renders correctly
- [ ] AC, level, class all visible
- [ ] No "Cannot read property 'current' of undefined" errors

**Expected**: All stats display with fallbacks if data missing

---

### 8. Message Persistence
- [ ] Send 3-4 actions
- [ ] Messages display in adventure log
- [ ] Refresh page
- [ ] Load campaign again
- [ ] All previous messages still visible
- [ ] Scroll works correctly

**Expected**: localStorage hydration works, no message loss

---

### 9. Error Handling
- [ ] Send invalid action (gibberish)
- [ ] Error message displays (if applicable)
- [ ] App doesn't crash
- [ ] Can send another action after error
- [ ] Backend returns 200 or handles gracefully

**Expected**: Graceful degradation, no white screen

---

### 10. TTS (Optional)
- [ ] Enable TTS toggle
- [ ] DM narration appears
- [ ] Audio player icon shows on message
- [ ] Click play → Audio plays
- [ ] Disable TTS → No auto-generation

**Expected**: TTS works without blocking gameplay

---

## 🚨 Critical Failure Indicators

Stop testing and investigate immediately if:
- ❌ "Maximum update depth exceeded" error
- ❌ White screen / app crash
- ❌ HTTP 500 errors on action submission
- ❌ "Cannot read property X of undefined" (especially for `hp`, `attack_bonus`)
- ❌ Combat doesn't start or crashes mid-turn
- ❌ Messages don't appear after actions
- ❌ Campaign fails to load

---

## 📊 Quick Status Check

After running all tests, mark overall status:

- [ ] ✅ All tests pass - Ready for production
- [ ] ⚠️ Minor issues - Document and fix non-blocking bugs
- [ ] ❌ Critical failures - Do not deploy, fix immediately

---

## 🔧 Post-Test Actions

If tests fail:
1. Check browser console for errors
2. Check backend logs: `tail -100 /var/log/supervisor/backend.err.log`
3. Verify normalizers are applied at entry points
4. Check if data models have changed
5. Review recent commits for state management changes

---

## 📝 Notes Section

Date: ___________  
Tester: ___________  
Branch/Commit: ___________

Issues Found:
- 
- 
- 

Passed:  ____ / 10 flows  
Status: ✅ / ⚠️ / ❌
