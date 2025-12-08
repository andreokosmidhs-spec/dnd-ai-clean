# QA Playtest Script - P3.5 Validation
**Duration**: 30-45 minutes
**Goal**: Validate game feel, not just functionality

---

## Pre-Session Setup

1. **Clear State**:
   - Browser: F12 → Console → `localStorage.clear()`
   - Refresh page
   - Confirm: No existing campaigns

2. **Tracking Sheet** (keep notes):
   ```
   Combat #  | XP Gained | Total XP | Level | HP | Notes
   ---------|-----------|----------|-------|----|-----------------
   Start    | 0         | 0/150    | 1     | 10 | Fresh character
   ```

---

## SEGMENT 1: Early Pacing (L1 → L2)
**Goal**: Does L2 feel earned or handed out?

### Actions:
1. **Create Character**:
   - Pick any class/race
   - Note starting: Level 1, HP 10, XP 0/150

2. **Play Intro**:
   - Read intro narration
   - **Feel Check**: Does it give you a clear hook? (yes/no/vague)

3. **First 3 Encounters**:
   - Trigger 3 combats naturally (attack guards, investigate, etc.)
   - For each combat:
     - Count turns to victory
     - Note XP gained (should be ~70 for 2 standard enemies)
     - Track: Total XP / 150

### Data to Collect:
```
Combat 1: ___ XP → Total: ___/150
Combat 2: ___ XP → Total: ___/150  
Combat 3: ___ XP → Total: ___/150
```

### Feel Questions (answer AFTER L2):
1. **Pacing**: How many combats to L2? ____
   - ⚠️ If 2 or less: TOO FAST (need to increase thresholds)
   - ✅ If 3: GOOD (target hit)
   - ⚠️ If 4+: TOO SLOW (enemies not worth enough XP)

2. **Emotional beat**: When you dinged L2, what did you feel?
   - [ ] "Already? That was fast."
   - [ ] "Nice, I earned that."
   - [ ] "About time, felt like a grind."

3. **HP increase visible?** 10 → 16 (+6) clear in UI? (yes/no)

4. **XP bar rollover smooth?** Did it animate correctly? (yes/no)

### Red Flags:
- ❌ L2 after 1-2 combats → XP curve still too generous
- ❌ L2 after only non-combat actions → Non-combat XP too high
- ❌ No visual feedback on level-up → UI bug

---

## SEGMENT 2: Defeat Mechanics (Sting Test)
**Goal**: Does defeat have emotional weight?

### Setup:
- Continue from L2 (or use dev tools to set HP to 3)
- **Intentionally lose a fight**

### Actions:
1. **Trigger Defeat**:
   - Enter combat with low HP (3-5 HP)
   - Don't defend, let enemies kill you

2. **Observe Defeat Flow**:
   - Combat ends with "player_defeated"
   - DefeatModal appears

3. **Check Defeat Consequences**:
   - HP restored to ___% of max (should be ~50%)
   - XP penalty shown: `-___ XP`
   - Injury count: ____

### Data to Collect:
```
Before Defeat:
  XP: ___/___
  HP: ___/___
  Injury Count: ___

After Defeat:
  XP: ___/___ (check if bar moved backward)
  HP: ___/___ (should be ~50% max)
  Injury Count: ___ (should be +1)
  XP Lost: -___ XP
```

### Feel Questions:
1. **XP bar regression visible?** Did you SEE the bar move backward? (yes/no)

2. **Emotional impact**: What did you feel?
   - [ ] "Fuck, that cost me" (GOOD - penalty has teeth)
   - [ ] "Meh, whatever" (BAD - penalty too soft)
   - [ ] "I want to quit" (BAD - penalty too harsh)

3. **Penalty amount fair?**
   - If you had 100/150 XP and lost 15 → feels: ____
   - If you had 10/150 XP and lost 5 → feels: ____

4. **DefeatModal clarity**: Was the feedback clear? (yes/no)
   - Shows HP restored? ____
   - Shows XP lost? ____
   - Flavor text compelling? ____

5. **Second Defeat** (optional): Lose again on purpose
   - Does it feel worse? (accumulating pain)
   - Or does it feel numbing? (penalty meaningless)

### Red Flags:
- ❌ XP bar didn't move → UI not updating
- ❌ Felt nothing → Penalty too small or UI not selling it
- ❌ Felt demoralized → Penalty too harsh
- ❌ Modal stuck/crashy → Bug in defeat handling

---

## SEGMENT 3: Power Spike (L3 Attack Bonus)
**Goal**: Does L3 feel like a meaningful upgrade?

### Setup:
- Continue playing from L2
- Goal: Reach L3 (need ~300 total XP from start)

### Actions:
1. **Combat BEFORE L3** (at L2):
   - Fight 2-3 combats
   - **Pay attention**: How often are you missing?
   - Count hits vs misses (rough mental tally)

2. **Reach L3**:
   - Confirm: attack_bonus = 1 in character sheet (if visible)
   - HP increase: 16 → 22 (+6)

3. **Combat AFTER L3**:
   - Fight 2-3 more combats
   - **Pay attention**: Does it FEEL like you hit more often?
   - Count hits vs misses again

### Data to Collect:
```
L2 Combats (3 fights):
  Rough hit rate: ___/___  (e.g., 5 hits out of 8 attacks)
  Feeling: [ ] Missing a lot  [ ] Hitting often  [ ] Mixed

L3 Combats (3 fights):
  Rough hit rate: ___/___
  Feeling: [ ] Same as L2  [ ] Noticeably better  [ ] Dominating
```

### Feel Questions:
1. **Power spike perceptible?**
   - [ ] "Yeah, I'm hitting more now" (GOOD)
   - [ ] "Can't tell any difference" (BAD - either AC too low or bonus too small)
   - [ ] "I'm crushing everything" (BAD - enemies too weak)

2. **Combat length at L3**: Still 3-5 turns? Or trivializing fights?
   - Avg turns at L2: ____
   - Avg turns at L3: ____
   - **Target**: Should stay in 3-5 turn range, not drop to 1-2

3. **Log visibility**: Can you see attack_bonus in combat logs? (yes/no)
   - If yes, does it show: `modifier=3+2+1`? (ability + prof + attack_bonus)

### Red Flags:
- ❌ No perceptible difference → Attack bonus not wired OR enemies too easy already
- ❌ Fights now trivial → Enemy scaling needs adjustment
- ❌ Combat logs don't show bonus → Missing from log output

---

## SEGMENT 4: Quest & Non-Combat XP (AI Intelligence)
**Goal**: Is the DM using quests/XP intelligently?

### Setup:
- Continue playing (any level)
- **Play NON-violently for this segment**

### Actions:
1. **Social/Sneaky Route** (3-5 actions):
   - Negotiate with NPCs
   - Investigate clues
   - Sneak past guards
   - Solve problems without combat

2. **Watch for**:
   - Quest proposals (should appear in QuestLogPanel)
   - XP awards with reasons (e.g., `+20 XP: Clever negotiation`)
   - Toast notifications

### Data to Collect:
```
Action 1: _______________________________
  XP Award: ___ (reason: _______________)
  Quest Offered? (yes/no)

Action 2: _______________________________
  XP Award: ___ (reason: _______________)
  Quest Offered? (yes/no)

Action 3: _______________________________
  XP Award: ___ (reason: _______________)
  Quest Offered? (yes/no)
```

### Feel Questions:
1. **Quest frequency**:
   - [ ] Too many (every other action)
   - [ ] About right (1-2 per session)
   - [ ] Too few (none seen)

2. **Quest quality**:
   - Do quests reference actual NPCs/places from world blueprint? (yes/no)
   - Are objectives clear? (e.g., "Kill 3 cultists" vs vague "do something")
   - QuestLogPanel displays correctly? (yes/no)

3. **Non-combat XP appropriateness**:
   - Minor actions (10 XP): Appropriate? ____
   - Moderate actions (20 XP): Appropriate? ____
   - Major breakthroughs (40 XP): Appropriate? ____

4. **XP spam check**:
   - Did you get XP for trivial actions? (e.g., "I sit down" → 10 XP)
   - Did you get XP for EVERY action? (spam)
   - Or only meaningful ones? (good)

### Red Flags:
- ❌ No quests at all → AI not using quest system
- ❌ Quests reference "NPC_Bob" (not in blueprint) → Hallucination
- ❌ XP for breathing → Non-combat XP too liberal
- ❌ QuestLogPanel empty despite quests mentioned → UI not updating

---

## SEGMENT 5: Edge Cases (Break Things)
**Goal**: Probe system boundaries

### Test 1: Double Level-Up
**Setup**: Get close to a level threshold, then do a big XP action

**Actions**:
1. Get to ~140/150 XP (almost L2)
2. Complete a quest worth 40 XP OR win a big combat (~70 XP)
3. Should cross TWO thresholds (L1→L2→L3 if conditions right)

**Check**:
- Did both level-ups apply? ____
- HP increased twice? (+6 → +6) ____
- No skipped levels? ____
- XP correctly rolled over? ____

---

### Test 2: Defeat After Big XP Gain
**Setup**: Gain a lot of XP in current level, then lose

**Actions**:
1. Get to e.g., 120/150 XP
2. Trigger defeat

**Check**:
- XP penalty: ~18 (120 * 0.15) or min 5? ____
- XP doesn't underflow (go negative)? ____
- Modal shows correct penalty? ____

---

### Test 3: Quest + Combat XP Same Turn
**Setup**: Kill a quest target in combat

**Actions**:
1. Accept quest: "Kill 3 bandits"
2. Fight 2 bandits, check progress: 2/3
3. Fight final bandit

**Check**:
- Got combat XP? (~35 for standard enemy) ____
- Quest completed? ____
- Got quest XP? (~100 typical) ____
- Total XP = combat + quest? ____
- No double-grant or skip? ____

---

## POST-SESSION SUMMARY

### Overall Feel (answer honestly, not defensively):

1. **Pacing grade** (A/B/C/D/F):
   - L1 → L2 felt: ____
   - L2 → L3 felt: ____

2. **Defeat impact grade** (A/B/C/D/F):
   - Did losing hurt? ____
   - Would you play more carefully to avoid it? ____

3. **Power progression grade** (A/B/C/D/F):
   - Did L3 feel stronger? ____
   - Was it too much or too little? ____

4. **Quest/non-combat grade** (A/B/C/D/F):
   - Did quests add direction? ____
   - Was non-combat XP rewarding? ____

### What felt BEST:
- ___________________________________________

### What felt WORST / needs adjustment:
- ___________________________________________

### Immediate tuning needed (if any):
- [ ] XP curve (too fast / too slow)
- [ ] Defeat penalty (too soft / too harsh)
- [ ] Attack bonus (invisible / trivializing)
- [ ] Quest frequency (too many / too few / none)
- [ ] Non-combat XP (spam / stingy / good)

---

## DONE

You now have:
- Concrete data points (XP, combats, HP)
- Gut feelings (pacing, difficulty, progression)
- Edge case validation (no crashes, correct math)

**Next step**: Report findings. Don't defend the code - just share what felt good and what felt off.
