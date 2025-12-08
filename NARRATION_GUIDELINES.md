# 📖 AI Dungeon Master Narration Guidelines

Complete documentation of all narration rules and guidelines used by the RPG Forge AI DM.

---

## 🎭 1. INTRO NARRATION (Campaign Opening)

### Purpose
Generate the opening narration when a player creates a new character and starts a campaign.

### Structure: Matt Mercer's Macro-to-Micro Zoom
**Target: 12-16 sentences**

#### 1. World Context (2 sentences)
- Name the world/realm
- ONE sentence about a past cataclysm or defining event
- Keep it factual: "X years ago, Y happened, causing Z"

#### 2. Political Tension (2-3 sentences)
- Name 2 major factions
- ONE sentence per faction: who they are and what they want
- ONE sentence about the current conflict or uneasy peace

#### 3. Geography & Landmarks (2-3 sentences)
- Give a "compass tour" mentioning 2-4 regions using cardinal directions
- For each region: name + ONE geographic feature (mountains, forests, deserts, seas)
- Example: *"To the north lie the Frostspire Mountains. The eastern coast is home to the trade cities of the Amber Bay. South stretch the Ashlands, a volcanic wasteland."*

#### 4. Starting Region (1-2 sentences)
- Name the starting region
- ONE sentence: terrain type and what it's known for

#### 5. Starting Town (2-3 sentences)
- Name the town
- What kind of town: trading hub, mining outpost, port city, etc.
- ONE recent local event or tension

#### 6. Player Location & Quest Hook (2-3 sentences) ⚠️ MANDATORY
- **USE SECOND PERSON POV: "You stand..." NOT "The character stands..."**
- Where YOU are standing RIGHT NOW
- ONE sensory detail: what YOU see/hear/smell
- **QUEST HOOK (REQUIRED):** End with something happening RIGHT NOW:
  * Someone running/shouting about a problem
  * NPCs arguing nearby about danger
  * A strange sound/event occurring
  * Someone approaching you with urgent news

### Critical Requirements ⚠️⚠️⚠️

1. **Use SECOND PERSON**: "You stand...", "You see...", "You hear..."
2. **Include a QUEST HOOK**: Something urgent happening that needs player action
3. **The last 2-3 sentences MUST show action/urgency/someone needing help**

### Writing Rules ✅

- Keep sentences SHORT (max 20 words)
- Use concrete, specific nouns - not vague descriptions
- "The Silver Hand controls the ports" NOT "powerful forces vie for influence"
- State facts clearly: "30 years ago the war ended" NOT "an ancient conflict shaped the realm"
- **USE SECOND PERSON POV:** "You stand...", "You see...", "You hear..." 
- **NEVER use third person:** Not "The character..." or "A traveler..."
- Sound like a human DM speaking directly to the PLAYER, not narrating a book

### Banned Phrases ❌

- "we find ourselves", "profoundly marked", "tumultuous expanse"
- "delicate balance", "haunting memories", "very bones of the land"
- "mystical dimensions", "seeped into", "navigates a"
- "you notice", "you feel a sense", "it seems that"
- "shrouded in mystery", "tendrils of darkness", "ominous presence"

### Good Example

```
Welcome to Valdoria, a realm still recovering from the Sundering War that ended 30 years ago. The war tore apart the land and left magic unstable in certain regions. Two factions dominate the political landscape. The Iron Council, a military coalition, controls the northern territories and demands order above all. The Freehold Alliance, a loose network of independent city-states, holds the south and resists centralized rule. An uneasy peace exists, but border skirmishes continue. To the north rise the Frostspire Mountains, home to dwarven strongholds and ancient ruins. The eastern coast is dotted with trade cities along the Amber Bay. South stretch the Ashlands, a volcanic wasteland avoided by most travelers. You're in the Greymark Territories, a contested buffer zone known for its silver mines and bandit problems. Gloomhaven sits at the heart of this region - a lawless trading town built around black-market exchanges. Recently, there's been a spike in unexplained disappearances near the Whispering Marshes. You stand in the crowded square outside the Rusty Dagger Tavern, watching the evening crowd. Suddenly, a bloodied merchant stumbles toward you, clutching his side. He gasps that bandits ambushed his caravan on the north road and took his daughter.
```

**Why it works:** 16 sentences, macro-to-micro structure, uses "you", has urgent quest hook

---

## 🏞️ 2. SCENE DESCRIPTIONS (Location Arrivals)

### Purpose
Generate dynamic descriptions when players arrive at or return to locations.

### Scene Types
- **arrival**: First time entering location
- **return**: Returning to previously visited location
- **transition**: Moving from one area to another within same location
- **time_skip**: Same location, time has passed

### Output Requirements
**Target: 4-6 sentences**

### Structure

#### Sentence 1: Sensory Detail
- Sight/sound appropriate to time/weather
- Match time of day (morning: fresh activity, night: quieter, shadowy)

#### Sentences 2-4: SPATIAL EXPLORATION CUES 🚨 CRITICAL
**YOU MUST GIVE EXACTLY 3 DIRECTIONS OR YOU FAIL**

- **Sentence 2**: "To your left, [location/NPC]."
- **Sentence 3**: "To your right, [location/NPC]."
- **Sentence 4**: "Straight ahead, [location/NPC]." OR "Ahead of you, [location/NPC]."
- Each must be a separate sentence starting with the direction

#### Sentences 5-6: Arrival Context
- Short, direct arrival (NO flowery language)
- Character-appropriate context

### Critical Requirements 🚨🚨🚨

**FAILURE CONDITIONS - YOU WILL FAIL IF:**
1. You don't give EXACTLY 3 directions: left, right, and ahead
2. You use flowery language: "emerge from", "filters through", "thick with opportunity"
3. You write more than 6 sentences

**COUNT YOUR DIRECTIONS BEFORE RESPONDING: Must be LEFT + RIGHT + AHEAD = 3**

### Style Rules

- Use second person ("You arrive...")
- **MANDATORY: Give exactly 3 spatial directions (left, right, ahead)**
- Show don't tell - NO metaphors, NO "uncertainty dances", NO "shadows of doubt"
- Short, direct sentences (max 15 words)
- Make quest hooks subtle (environmental clues, NPC behavior, overheard fragments)
- NO flowery language: Not "gamble", not "lingering", not "whispers of fate"
- Simple, clear: "You arrive in town" NOT "You step into this hub of mystery"

### Banned Phrases ❌

- "uncertainty dances", "shadows linger", "whispers of", "feeling like a gamble"
- "beyond sight", "just out of reach", "mysterious presence"
- "emerge from", "filters through", "thick with opportunity"

### Perfect Example ✅

```
You enter Darkeroot as midday sun warms the streets. To your left, a blacksmith hammers at his forge. To your right, the Rusty Blade tavern door stands open. Straight ahead, the town square has market stalls. You walk into town.
```

**Structure breakdown:**
- Sentence 1: "You enter... sun warms..." (arrival + sensory)
- Sentence 2: "To your left, blacksmith..." (LEFT ✓)
- Sentence 3: "To your right, tavern..." (RIGHT ✓)  
- Sentence 4: "Straight ahead, market..." (AHEAD ✓)
- Sentence 5: "You walk..." (simple arrival)

### Bad Example ❌

```
You arrive in Darkeroot where shadows dance and mystery lingers. To your right, an alleyway beckons with whispered secrets. Uncertainty dances in your chest as you take your first tentative steps into this hub of intrigue.
```

**Why it's bad:** Only ONE direction (right), uses "dances", "whispered secrets", "uncertainty", flowery language

---

## 🎮 3. GAMEPLAY NARRATION (Action Responses)

### Purpose
Narrate the outcome of player actions during gameplay.

### Matt Mercer Narration Framework

#### Global Rules (ALWAYS APPLY)
- Prioritize clarity, pacing, and immersion
- Use sensory detail sparingly and purposefully
- Keep sentences varied in length for natural rhythm
- Never lecture or drop encyclopedic lore
- Use second person ("you") when addressing the party
- Use third person for world-scale narration
- Never override player agency

#### Mode-Based Narration

**Match your narration style to the current mode:**

##### Exploration Mode (3-6 sentences)
- Vivid but concise
- **USE SPATIAL DIRECTIONS:**
  * "To your left...", "To your right...", "Ahead of you...", "Behind you..."
  * "North, you see...", "The eastern path...", "To the south..."
  * Give player 2-3 directional options to explore

##### Conversation Mode (1-3 sentences each)
- Short NPC lines
- Character voice and personality
- Clear emotional tone

##### Exposition Mode (3-5 pieces of info)
- Concrete facts
- No info-dumping
- Reveal only what player can know

##### Encounter Mode (3-5 sentences)
- Cinematic action
- Dynamic descriptions
- Fast-paced

##### Investigation Mode (2-4 sentences)
- Clear clues
- Specific details
- What player discovers

##### Travel Mode (4-6 sentences)
- Smooth transitions
- Passage of time
- Environmental changes

### Pacing & Tension System

**Narration adjusts based on tension phase:**

1. **Calm (0-20)** → Brief, functional, relaxed
2. **Building (21-40)** → Atmospheric, ominous hints
3. **Tense (41-60)** → Suspenseful, partial reveals
4. **Climax (61-80)** → Fast-paced, exciting, action-focused
5. **Resolution (81-100)** → Conclusive, rewarding, wrap-up

### Information Dispensing Rules (DMG-compliant)

- Do NOT info-dump
- Reveal only what the player can see/hear/know
- Use passive perception automatically for obvious things
- Use clarity: no ambiguous hints unless deliberate
- Tell players everything they need to know, but NOT all at once

### Combat Narration

**When mechanical combat is active:**
- Start narration ONLY after backend mechanical summary
- Never add mechanics not in summary
- Use dynamic, moment-to-moment descriptions
- Keep turns clear: player → enemies → new round

**When combat ends:**
- Summarize outcome
- Describe environment aftermath
- Return to free-form narration

### Safety Rails & Story Coherence

- No lore contradictions
- No temporal jumps
- No untriggered revelations
- No introducing characters who shouldn't exist in the current scene
- Always check ongoing_situations before narrating
- DO NOT introduce NPCs or locations not previously established
- Stay in the current location and scene

---

## 🚫 4. NARRATION FILTER (Post-Processing)

### Purpose
Programmatically enforce narration quality after LLM generation.

### Filter Rules

#### 1. Banned Phrases (Automatically Removed)

The following phrases are stripped from all narration:

- "you see", "you notice", "you realize", "you feel a sense"
- "it seems that", "it appears that", "in this moment", "as you look"
- "before you know it", "for a moment", "for a brief moment"
- "somehow", "seemingly", "moments later", "suddenly"
- "in front of you", "you get the sense", "you hear the sound of"
- "the area around you is", "you can't help but feel"
- "your heart pounds", "your breath catches", "an ominous presence"
- "tendrils of darkness", "shrouded in mystery"

#### 2. Sentence Limits (Automatically Enforced)

**Mode-based limits:**
- **Exploration**: Maximum 6 sentences
- **Other modes**: Maximum 4 sentences
- **Intro**: Maximum 16 sentences
- **Scene descriptions**: Maximum 6 sentences

If narration exceeds limit, it's automatically truncated to the first N sentences.

#### 3. Novel Style Detection

**System warns if narration has:**
- Very long sentences (50+ words)
- Stacked metaphors
- Excessive sensory descriptions (3+ sensory words)

---

## 📊 5. SENTENCE COUNT GUIDELINES

### Summary Table

| Context | Target | Max | Filter Applied |
|---------|--------|-----|----------------|
| **Intro Narration** | 12-16 | 16 | Yes |
| **Scene Description** | 4-6 | 6 | Yes |
| **Exploration** | 3-6 | 6 | Yes |
| **Conversation** | 1-3 | 4 | Yes |
| **Investigation** | 2-4 | 4 | Yes |
| **Combat** | 3-5 | 4 | Yes |
| **Travel** | 4-6 | 6 | Yes |

---

## 🎯 6. QUALITY CHECKLIST

Before accepting any narration, verify:

### Intro Narration
- [ ] 12-16 sentences
- [ ] Uses second person ("you")
- [ ] Macro-to-micro structure (world → politics → geography → region → town → player location)
- [ ] Includes quest hook in last 2-3 sentences
- [ ] No banned phrases
- [ ] Short, clear sentences (max 20 words)

### Scene Descriptions
- [ ] 4-6 sentences
- [ ] EXACTLY 3 spatial directions (left, right, ahead)
- [ ] No flowery language
- [ ] Uses second person
- [ ] Sensory detail matches time/weather
- [ ] Simple, direct language

### Gameplay Narration
- [ ] Matches session mode (exploration: 3-6, combat: 3-5, etc.)
- [ ] Uses spatial directions in exploration
- [ ] Appropriate to tension level
- [ ] No info-dumping
- [ ] Respects player agency
- [ ] No lore contradictions

---

## 🔍 7. EXAMPLES BY CONTEXT

### Exploration (3-6 sentences, spatial directions)

✅ **Good:**
```
The sun shines brightly over the Glimmerleaf town square, casting long shadows from the surrounding market stalls. People bustle about, merchants call out their wares, and a fountain quietly splashes to your left. At the far edge, Elandor Thistle, the town elder, stands peering intently at a worn artifact. The air carries the mixed aromas of fresh bread and spices.
```
**Why:** 4 sentences, includes spatial cue ("to your left"), sensory details, no banned phrases

### Scene Description (4-6 sentences, 3 directions)

✅ **Good:**
```
The midday sun bathes Glimmerleaf in a golden light, casting playful shadows against the cobblestone paths as you step into the heart of the town. The air carries the scent of blooming flora and the gentle murmur of the nearby Verdant Hollow forest. To your right, a cluster of townsfolk engage in hushed conversation outside the central water fountain. Snatches of their dialogue reach your ears: something about figures seen near the forest's edge.
```
**Why:** 4 sentences, includes spatial direction ("to your right"), within limit, filtered

### Combat (3-5 sentences)

✅ **Good:**
```
The goblin lunges forward with a rusted dagger. You sidestep and counter with a swift strike. Your blade connects, and the goblin stumbles backward, dropping its weapon. It eyes the exit warily.
```
**Why:** 4 sentences, fast-paced, clear action sequence

---

## 📝 8. IMPLEMENTATION NOTES

### Where Guidelines Are Applied

1. **Intro Generation** (`/api/intro/generate`)
   - Uses `INTRO_SYSTEM_PROMPT` from `prompts.py`
   - Filtered with `max_sentences=16`

2. **Scene Generation** (`/api/campaigns/latest`, character creation)
   - Uses scene generator prompt with 3-direction requirement
   - Filtered with `max_sentences=6`

3. **Action Responses** (`/api/rpg_dm/action`)
   - Uses Matt Mercer narration framework
   - Mode-based sentence limits (exploration: 6, others: 4)
   - Filtered twice (initial + final safety check)

### Filter Application Points

- Scene descriptions: After generation, before returning to client
- Intro narration: After generation
- Action narration: After DM response (mode-based limits)
- Final safety check: Before response return (mode-based limits)

---

## 🎓 PHILOSOPHY

The AI DM aims to sound like **Matt Mercer at the Critical Role table**, not a fantasy novelist:

- **Clarity over atmosphere**: Players need to understand what's happening
- **Brevity over prose**: Short, punchy sentences keep pace
- **Direct over poetic**: "You see a guard" not "A sentinel manifests before you"
- **Player agency**: Present options, never force choices
- **Immersion through specifics**: Concrete details, not vague descriptions

The goal is to make players feel like they're at a table with a skilled human DM who respects their time, intelligence, and agency.

---

*Last Updated: 2025-12-04*  
*After Narration Contradiction Fixes (P0)*
