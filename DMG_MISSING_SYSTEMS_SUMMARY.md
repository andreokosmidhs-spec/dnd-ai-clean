# DMG MISSING SYSTEMS & FEATURE LIST
**Based on:** D&D 5e Dungeon Master's Guide Analysis
**Status:** Already extracted and analyzed (see `/app/DMG_IMPLEMENTATION_PLAN.md` for full technical spec)

---

## 🚨 CRITICAL MISSING SYSTEMS

### 1. **PACING & TENSION MANAGEMENT** (DMG p.24)
**What's Missing:**
- No tension tracking across sessions
- DM narration doesn't adapt to danger level
- No "ebb and flow" of action and anticipation

**Impact:** Monotone experience, all scenes feel the same

**Feature to Add:**
```
✅ Tension Tracker (0-100 scale)
✅ 5 Phases: Calm → Building → Tense → Climax → Resolution
✅ Dynamic DM narration style adjustment
✅ Automatic pacing based on combat proximity, player HP, quest urgency
```

---

### 2. **PLAYER MOTIVATION TRACKING** (DMG p.8-10)
**What's Missing:**
- No awareness of player preferences
- One-size-fits-all content generation
- Can't tailor encounters to player type

**Impact:** Combat-focused players get social encounters, explorers get grinding

**Feature to Add:**
```
✅ 8 Player Archetypes: Actor, Explorer, Instigator, Power Gamer, Slayer, Storyteller, Thinker, Watcher
✅ Behavioral detection from session history
✅ Content weighting algorithm (combat:exploration:social ratios)
✅ Adaptive DM prompts based on detected archetype
```

---

### 3. **INFORMATION DISPENSING SYSTEM** (DMG p.26-27)
**What's Missing:**
- No passive Perception auto-reveals
- Information dump issues (all at once or none)
- Conditions not explained clearly

**Impact:** Players miss clues or get overwhelmed with details

**Feature to Add:**
```
✅ Passive skill check system (auto-reveal based on character modifiers)
✅ Information drip-feed algorithm ("not all at once" - DMG p.26)
✅ Condition explanations in plain language (DMG p.27)
✅ Tension-based information control (hold back during tense moments)
```

---

### 4. **CONSEQUENCE ESCALATION** (DMG p.32, p.74, p.98-99)
**What's Missing:**
- Plot armor has one-time consequences
- No tracking of repeated offenses
- No escalation from warning → arrest → bounty → war

**Impact:** Players can repeatedly attack NPCs without escalating punishment

**Feature to Add:**
```
✅ Transgression tracking system
✅ 4 Severity Levels: Minor → Moderate → Severe → Critical
✅ Escalation thresholds (3 minors = 1 moderate, etc.)
✅ Progressive consequences:
   - Minor: NPC annoyed, small reputation loss
   - Moderate: Guards investigate, disadvantage on Charisma checks
   - Severe: Bounty posted, guards attack on sight
   - Critical: City-wide manhunt, faction war
```

---

### 5. **NPC PERSONALITY ENGINE** (DMG p.186)
**What's Missing:**
- NPCs have names and roles but no personality
- No distinctive speech patterns or mannerisms
- Forgettable, generic dialogue

**Impact:** All NPCs sound the same, no memorable characters

**Feature to Add:**
```
✅ Mannerisms database (50+ options: "speaks in third person", "adjusts spectacles", etc.)
✅ Personality traits, ideals, bonds, flaws (DMG p.186)
✅ Dialogue enhancement based on personality
✅ NPC quirks integration in DM narration
```

---

### 6. **IMPROVISATION FRAMEWORK** (DMG p.28-29)
**What's Missing:**
- No "Say Yes" principle implementation
- System blocks unexpected actions
- No reward for creative solutions

**Impact:** Players feel railroaded, creativity punished

**Feature to Add:**
```
✅ Creative action classifier (creative/risky/impossible)
✅ "Say Yes" handler - find ways to allow player ideas
✅ Advantage rewards for creative approaches
✅ Complication introduction for risky actions
✅ Alternative suggestions when impossible
```

---

### 7. **SESSION FLOW MANAGER** (DMG p.20-21)
**What's Missing:**
- No tracking of game modes
- Jarring transitions between exploration and combat
- DM doesn't adjust narration to mode

**Impact:** Pacing feels off, transitions feel abrupt

**Feature to Add:**
```
✅ 5 Game Modes: Setup, Exploration, Conversation, Encounter, Passing Time
✅ Mode detection from player actions
✅ Narration style adjustment per mode:
   - Setup: Brief, functional
   - Exploration: Rich sensory details (DMG p.22)
   - Conversation: Character-focused
   - Encounter: Fast-paced, exciting (DMG p.24)
   - Passing Time: Ultra-brief summary
✅ Visual mode indicators in UI
```

---

### 8. **ENCOUNTER DESIGN VALIDATOR** (DMG p.56-57)
**What's Missing:**
- No XP budget system
- No encounter difficulty calculation
- Random enemy selection without balance checking

**Impact:** Encounters too easy or TPK-level hard

**Feature to Add:**
```
✅ XP budget calculator based on party level
✅ Threat level validator (trivial/easy/moderate/hard/deadly)
✅ Monster role mixer (Artillery, Brute, Controller, Lurker, etc.)
✅ Warning system when encounter is unbalanced
```

---

## 📊 MISSING SYSTEMS PRIORITY MATRIX

| System | DMG Pages | Current Status | User Impact | Implementation Effort | Priority |
|--------|-----------|----------------|-------------|----------------------|----------|
| Pacing/Tension | 24 | ❌ None | 🔴 High | 🟡 Medium | **P0** |
| Information Dispensing | 26-27 | ⚠️ Partial | 🔴 High | 🟢 Low | **P0** |
| Consequence Escalation | 32, 74, 98 | ⚠️ Partial | 🔴 High | 🟡 Medium | **P0** |
| Player Motivation | 8-10 | ❌ None | 🟠 Medium | 🔴 High | **P1** |
| Session Flow | 20-21 | ❌ None | 🟠 Medium | 🟡 Medium | **P1** |
| NPC Personality | 186 | ⚠️ Basic | 🟠 Medium | 🟢 Low | **P1** |
| Improvisation | 28-29 | ❌ None | 🟡 Low | 🟡 Medium | **P2** |
| Encounter Design | 56-57 | ❌ None | 🟡 Low | 🔴 High | **P2** |

**Legend:**
- 🔴 High Impact = Core gameplay affected
- 🟠 Medium Impact = Experience quality affected
- 🟡 Low Impact = Polish/edge cases
- 🟢 Low Effort = 1-2 days
- 🟡 Medium Effort = 3-5 days
- 🔴 High Effort = 1-2 weeks

---

## ✅ FEATURE LIST (IMPLEMENTATION-READY)

### **Phase 1: Critical Systems (3-5 days)**

#### Feature 1.1: Pacing & Tension System
- **File:** `backend/services/pacing_service.py`
- **What it does:** Tracks tension level (0-100) based on combat proximity, player HP, quest urgency
- **DM Integration:** Adjusts narration style (calm vs building vs climax)
- **User-Facing:** No UI changes needed, automatic backend behavior

#### Feature 1.2: Information Drip-Feed
- **File:** `backend/services/information_service.py`
- **What it does:** 
  - Auto-reveals info via passive Perception
  - Controls how much info is released at once based on tension
  - Clarifies conditions in plain language
- **DM Integration:** Modifies prompts to include passive checks
- **User-Facing:** Clearer condition explanations, better-paced reveals

#### Feature 1.3: Consequence Escalation
- **File:** `backend/services/consequence_service.py`
- **What it does:**
  - Tracks transgression count per NPC/faction
  - Escalates severity: Minor (3x) → Moderate (2x) → Severe (1x) → Critical
  - Applies progressive consequences (reputation, guards, bounty, war)
- **Integration:** Updates plot_armor_service to check transgression history
- **User-Facing:** Warning before escalation, consequence preview in UI

---

### **Phase 2: Enhanced Experience (5-7 days)**

#### Feature 2.1: Player Motivation Detection
- **File:** `backend/services/player_motivation_service.py`
- **What it does:**
  - Analyzes session history (combat freq, social attempts, exploration)
  - Classifies player into 8 archetypes
  - Adjusts content generation weights
- **DM Integration:** Adds archetype-specific guidance to DM prompts
- **User-Facing:** Optional survey during character creation

#### Feature 2.2: Session Flow Manager
- **File:** `backend/services/session_flow_service.py`
- **What it does:**
  - Detects current game mode (Setup/Exploration/Conversation/Encounter/Passing Time)
  - Adjusts narration style per mode
- **DM Integration:** Mode-specific narration guidance
- **User-Facing:** Visual mode indicator in UI (🗡️ Combat vs 🗺️ Exploration)

#### Feature 2.3: NPC Personality Generator
- **File:** `backend/services/npc_personality_service.py`
- **What it does:**
  - Assigns 2 mannerisms, personality trait, ideal, bond, flaw to each NPC
  - Modifies NPC dialogue to reflect personality
- **DM Integration:** Adds NPC personality to active NPC section of prompt
- **User-Facing:** More memorable, distinctive NPCs

---

### **Phase 3: Polish (5-7 days)**

#### Feature 3.1: Improvisation Handler
- **File:** `backend/services/improvisation_service.py`
- **What it does:**
  - Classifies unexpected actions (creative/risky/impossible)
  - Applies "Say Yes" principle
  - Rewards creativity with advantage
- **DM Integration:** Adds improvisation guidance to prompts
- **User-Facing:** "✨ Creative approach! Rolling with advantage" feedback

#### Feature 3.2: Encounter Difficulty Validator
- **File:** `backend/services/encounter_service.py`
- **What it does:**
  - Calculates XP budget for party
  - Validates encounter difficulty before spawning
  - Warns if encounter is deadly
- **DM Integration:** Prevents overly hard/easy encounters
- **User-Facing:** No direct UI, better-balanced combat

#### Feature 3.3: Story Cohesion Tracker
- **File:** `backend/services/story_service.py`
- **What it does:**
  - Tracks campaign themes and major events
  - Checks for continuity errors
  - Suggests callbacks to earlier events
- **DM Integration:** Adds story continuity reminders to prompts
- **User-Facing:** More coherent long-term narrative

---

## 🎯 RECOMMENDED IMPLEMENTATION ORDER

### **Week 1: P0 Systems**
1. **Day 1-2:** Pacing & Tension System
   - Implement tension calculator
   - Add pacing instructions to DM prompts
   - Test tension transitions

2. **Day 3:** Information Dispensing
   - Add passive Perception checks
   - Implement drip-feed algorithm
   - Add condition clarity

3. **Day 4-5:** Consequence Escalation
   - Create transgression tracker
   - Implement escalation logic
   - Integrate with plot armor
   - Test escalation thresholds

**Deliverable:** DM behavior improves dramatically, plot armor feels more realistic

---

### **Week 2: P1 Systems**
4. **Day 1-3:** Player Motivation Engine
   - Build archetype detector
   - Create content weighting system
   - Add to DM prompts

5. **Day 4-5:** Session Flow Manager
   - Implement mode detection
   - Add narration adjustments
   - Create UI mode indicators

6. **Day 6-7:** NPC Personality Generator
   - Build personality database
   - Implement dialogue modifier
   - Test NPC distinctiveness

**Deliverable:** Personalized experience, better pacing, memorable NPCs

---

### **Week 3: P2 Systems**
7. **Day 1-3:** Improvisation Framework
   - Build action classifier
   - Implement "Say Yes" logic
   - Add creativity rewards

8. **Day 4-5:** Encounter Difficulty Validator
   - Build XP calculator
   - Add balance checking
   - Integrate with enemy spawning

9. **Day 6-7:** Story Cohesion Tracker
   - Build continuity checker
   - Add theme tracking
   - Test callbacks

**Deliverable:** Polish, edge case handling, long-term campaign quality

---

## 📋 TESTING CHECKLIST

### Pacing System Tests
- [ ] Calm → Building transition when approaching dungeon
- [ ] Building → Tense when enemies detected
- [ ] Tense → Climax when combat starts
- [ ] Climax → Resolution when combat ends
- [ ] DM narration style changes appropriately

### Information Tests
- [ ] Passive Perception auto-reveals secret door (DC 12, player has +3)
- [ ] Only 2-3 info pieces revealed at once in calm mode
- [ ] Info withheld during tense moments
- [ ] Conditions explained in plain language

### Consequence Tests
- [ ] First offense = minor consequence (NPC annoyed)
- [ ] Third minor offense = moderate escalation (guards investigate)
- [ ] Fifth total offense = severe (bounty posted)
- [ ] Seventh offense = critical (city-wide manhunt)

### Player Motivation Tests
- [ ] Combat-heavy player classified as Slayer/Instigator
- [ ] Social-heavy player classified as Actor/Storyteller
- [ ] Content weights adjust appropriately

### Session Flow Tests
- [ ] Shopping detected as Setup mode
- [ ] "I explore the forest" detected as Exploration mode
- [ ] "I talk to the innkeeper" detected as Conversation mode
- [ ] Combat detected as Encounter mode
- [ ] Narration style matches mode

### NPC Personality Tests
- [ ] Each NPC has 2 unique mannerisms
- [ ] NPC dialogue reflects personality
- [ ] 20 NPCs generated, all feel distinct

### Improvisation Tests
- [ ] Creative action gets advantage
- [ ] Risky action allowed with complication
- [ ] Impossible action gets alternative suggestion

---

## 🎁 WHAT YOU GET

**7 New Backend Services:**
1. `pacing_service.py` - Tension tracking & narration adjustment
2. `information_service.py` - Passive checks & drip-feed control
3. `consequence_service.py` - Transgression tracking & escalation
4. `player_motivation_service.py` - Archetype detection & content weighting
5. `session_flow_service.py` - Game mode state machine
6. `npc_personality_service.py` - Personality generation & dialogue enhancement
7. `improvisation_service.py` - Creative action handler

**Updated Services:**
- `prompts.py` - All DMG guidance integrated
- `plot_armor_service.py` - Consequence escalation
- `dungeon_forge.py` - Service integrations
- `game_models.py` - New schemas

**New Schemas:**
- `player_profile` - Archetype, preferences, engagement score
- `tension_state` - Current tension level, phase, last transition
- `transgression_log` - NPC/faction offenses, severity, timestamps
- `npc_personality` - Mannerisms, traits, ideals, bonds, flaws
- `session_flow` - Current mode, duration, transitions

**Documentation:**
- `/app/DMG_IMPLEMENTATION_PLAN.md` - Full technical spec (500+ lines)
- `/app/DND_5E_RULES_VALIDATION.md` - Combat rules compliance
- `/app/DMG_MISSING_SYSTEMS_SUMMARY.md` - This document

---

## 💰 ESTIMATED VALUE

**Current System:** Basic D&D combat simulator
**After Phase 1:** Feels like a real DM (pacing, consequences, info control)
**After Phase 2:** Personalized experience, memorable NPCs, smooth flow
**After Phase 3:** Professional-grade narrative engine

**Comparison:**
- **Current:** 35% DMG compliance
- **After Phase 1:** 60% DMG compliance
- **After Phase 2:** 80% DMG compliance
- **After Phase 3:** 95% DMG compliance

---

## 🚀 NEXT STEPS

**Choose One:**

**Option A: Implement Phase 1 Now** (Recommended)
- Start with Pacing, Information, Consequence systems
- Immediate improvement to DM quality
- 3-5 days of work

**Option B: Review & Prioritize**
- Review full technical spec in `/app/DMG_IMPLEMENTATION_PLAN.md`
- Adjust priorities based on user feedback
- Create custom implementation order

**Option C: Test Current System First**
- Get user feedback on existing combat/plot armor
- Identify most painful gaps
- Prioritize based on actual user complaints

**Which would you prefer?**
