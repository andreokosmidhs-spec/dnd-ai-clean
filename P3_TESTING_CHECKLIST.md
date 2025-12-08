# P3 Testing Checklist

## Pre-Testing Setup

1. Ensure services running: `sudo supervisorctl status`
2. Clear browser localStorage: `localStorage.clear(); location.reload();`
3. Create new character via UI

---

## PART 1: XP & Level System

### Test 1.1: Initial State
- ✅ Character starts: level 1, XP 0/100, attack_bonus 0

### Test 1.2: Combat XP Gain
- ✅ Win combat → XP toast shows
- ✅ XP bar updates correctly
- ✅ CombatHUD shows level badge and XP bar

### Test 1.3: Level-Up
- ✅ Gain 100+ XP → Level-up toast appears
- ✅ Level increases to 2
- ✅ Max HP increases by +6
- ✅ HP fully restored
- ✅ XP bar resets with new threshold (250)

### Test 1.4: Attack Bonus
- ✅ Level 3: attack_bonus = 1
- ✅ Level 5: attack_bonus = 2

### Test 1.5: Level Cap
- ✅ Level 5: xp_to_next = 0, no further levels

---

## PART 2: Quest System

### Test 2.1: Quest UI Rendering
- ✅ QuestLogPanel appears when quests exist
- ✅ Shows quest name, summary, XP reward
- ✅ Expandable to show objectives

### Test 2.2: Objective Progress
- ✅ Progress displayed: "2/3 cultists defeated"
- ✅ Checkmark when complete
- ✅ Strikethrough on completed objectives

### Test 2.3: Quest Completion
- ✅ Completed badge shows
- ✅ Quest moves to completed section

---

## PART 3: Defeat Handling

### Test 3.1: Player Defeat
- ✅ HP drops to 0 → combat ends without crash
- ✅ DefeatModal appears with flavor text
- ✅ Shows HP restored (50% max)
- ✅ Shows injury count

### Test 3.2: Continue After Defeat
- ✅ Click "Continue" → modal closes
- ✅ HP updated to 50% max
- ✅ injury_count incremented
- ✅ Game continues normally

### Test 3.3: No XP on Defeat
- ✅ Defeated in combat → no XP gained

---

## PART 4: Enemy Scaling

### Test 4.1: Scaling at Different Levels
- ✅ Level 1: Base enemy stats (Bandit 15 HP, +3 attack)
- ✅ Level 3: Scaled stats (Bandit 21 HP, +4 attack)
- ✅ Level 5: Max scaling (Bandit 27 HP, +5 attack)

### Test 4.2: Combat Balance
- ✅ Enemies appropriately challenging at all levels
- ✅ 3-5 hits to defeat enemy

---

## Integration Tests

### INT-1: Full P3 Flow
1. Create character (level 1)
2. Win combat → gain XP
3. Level up → HP increases
4. Get defeated → modal shows
5. Continue → play normally
6. Reach level 3 → attack bonus increases

**Expected:** All features work together without crashes

### INT-2: P0-P2.5 Compatibility
- ✅ World generation works
- ✅ Intro narration works
- ✅ Action mode works
- ✅ Combat works
- ✅ No regressions

### INT-3: State Persistence
- ✅ Reload page → level, XP, injury_count persist

---

## Backend Unit Tests

```python
# XP Calculation
from services.progression_service import calculate_xp_for_enemy
assert calculate_xp_for_enemy({"name": "Bandit"}) == 35

# Level-Up
from services.progression_service import apply_xp_gain
char = {"level": 1, "current_xp": 90, "max_hp": 10, "xp_to_next": 100}
char, events = apply_xp_gain(char, 20)
assert char["level"] == 2
assert char["current_xp"] == 10
assert char["max_hp"] == 16

# Enemy Scaling
from services.enemy_sourcing_service import scale_enemy_for_level
enemy = {"name": "Bandit", "hp": 15, "attack_bonus": 3}
scaled = scale_enemy_for_level(enemy, 3)
assert scaled["hp"] == 21
assert scaled["attack_bonus"] == 4
```

---

## Critical Path Tests (Must Pass)

1. ✅ XP gain from combat
2. ✅ Level-up with stat increases
3. ✅ XP bar visible in UI
4. ✅ Defeat doesn't crash game
5. ✅ DefeatModal shows and dismisses
6. ✅ Enemy scaling works
7. ✅ Quest UI renders
8. ✅ All P0-P2.5 features still work

---

## Test Summary

- **Total Tests:** 30+
- **Critical:** 8 (must pass 100%)
- **High Priority:** 15 (must pass 90%+)
- **Medium Priority:** 7 (should pass 80%+)

Mark each test: ✅ Pass / ❌ Fail / ⏭️ Skip
