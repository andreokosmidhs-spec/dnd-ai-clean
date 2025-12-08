# Balanced Intro Structure: Matt Mercer + Human DM Style

## User Feedback
"The intro is too word-restricted and doesn't follow the guidelines like macro-to-micro, political tension, and the Matt Mercer model."

## The Solution: Balanced Approach

We need **BOTH**:
1. ✅ Matt Mercer's macro-to-micro structure with world-building
2. ✅ Human DM conversational style without AI novel prose

---

## NEW PROMPT STRUCTURE (8-12 sentences)

### 1. WORLD CONTEXT (2 sentences)
- Name the world/realm
- One sentence about past cataclysm or defining event
- **Style:** Factual, not flowery

**Example:**
```
"Welcome to Valdoria, a realm still recovering from the Sundering War that ended 30 years ago.
The war tore apart the land and left magic unstable in certain regions."
```

---

### 2. POLITICAL TENSION (2-3 sentences)
- Name 2 major factions
- One sentence per faction: who they are and what they want
- One sentence about current conflict or peace

**Example:**
```
"Two factions dominate the political landscape.
The Iron Council, a military coalition, controls the northern territories and demands order.
The Freehold Alliance holds the south and resists centralized rule.
An uneasy peace exists, but border skirmishes continue."
```

---

### 3. STARTING REGION (1-2 sentences)
- Name the region
- What it's known for

**Example:**
```
"You're in the Greymark Territories, a contested buffer zone known for its silver mines and bandit problems."
```

---

### 4. STARTING TOWN (2-3 sentences)
- Name the town
- Type of town (trading hub, mining town, port city)
- One recent local event or tension

**Example:**
```
"Gloomhaven sits at the heart of this region - a lawless trading town built around black-market exchanges.
Recently, there's been a spike in unexplained disappearances near the Whispering Marshes."
```

---

### 5. PLAYER LOCATION (1-2 sentences)
- Where character is standing RIGHT NOW
- One sensory detail
- Call to action

**Example:**
```
"You're standing in the crowded square outside the Rusty Dagger Tavern.
The air is thick with smoke and the scent of damp earth.
Your adventure begins here."
```

---

## COMPLETE EXAMPLE (11 sentences)

```
Welcome to Valdoria, a realm still recovering from the Sundering War that ended 30 years ago. 
The war tore apart the land and left magic unstable in certain regions. 
Two factions dominate the political landscape. 
The Iron Council, a military coalition, controls the northern territories and demands order above all. 
The Freehold Alliance, a loose network of independent city-states, holds the south and resists centralized rule. 
An uneasy peace exists, but border skirmishes continue. 
You're in the Greymark Territories, a contested buffer zone known for its silver mines and bandit problems. 
Gloomhaven sits at the heart of this region - a lawless trading town built around black-market exchanges. 
Recently, there's been a spike in unexplained disappearances near the Whispering Marshes. 
You're standing in the crowded square outside the Rusty Dagger Tavern. 
The air is thick with smoke and the scent of damp earth. 
Your adventure begins here.
```

**Analysis:**
- ✅ 12 sentences
- ✅ Macro-to-micro zoom (world → factions → region → town → player)
- ✅ Political tension (Iron Council vs Freehold Alliance)
- ✅ World context (Sundering War)
- ✅ Short, clear sentences (10-20 words each)
- ✅ No AI novel prose
- ✅ Sounds like a human DM speaking

---

## WHAT WAS WRONG BEFORE

### Version 1: Too Flowery (AI Novel Prose) ❌
```
"In the tumultuous expanse of The Realm of Adventure, we find ourselves in an era 
profoundly marked by the Shattering of the Veil. This cataclysmic event, a rupture 
in the barrier separating the world from mystical dimensions beyond, has seeped rare 
and potent magic into the very bones of the land..."
```

**Problems:**
- ❌ Metaphorical language ("tumultuous expanse", "very bones of the land")
- ❌ Long, complex sentences (30-50 words each)
- ❌ AI filler phrases ("we find ourselves", "profoundly marked")
- ❌ Reads like a fantasy novel, not a DM speaking

---

### Version 2: Too Short (No World Context) ❌
```
"You're in Thornhaven, a logging town at the edge of the Darkwood. The tavern behind 
you is loud with evening drinkers. Rain drips from the awning onto muddy streets. 
A town guard eyes you from across the square. The baron's men have been asking about 
strangers. Your adventure begins here."
```

**Problems:**
- ❌ Only 6 sentences
- ❌ No world context or history
- ❌ No political factions or tension
- ❌ Doesn't zoom from macro to micro
- ❌ Missing the "Critical Role" feel

---

### Version 3: BALANCED (NEW) ✅
Uses the 11-sentence example above.

**Why it works:**
- ✅ Provides world context (Sundering War)
- ✅ Shows political tension (Iron Council vs Freehold Alliance)
- ✅ Zooms from macro (world) to micro (player location)
- ✅ Uses short, clear sentences (15-20 words each)
- ✅ No AI novel prose
- ✅ Sounds like Matt Mercer introducing Critical Role

---

## TECHNICAL CHANGES

### Prompt Changes
- **Target length:** 8-12 sentences (was 6)
- **Structure:** Added explicit Matt Mercer macro-to-micro sections
- **Requirements:** Must include world context, factions, and political tension
- **Style:** Short sentences, no AI phrases, human DM voice

### Filter Changes
- **Max sentences:** 12 (was 6)
- **Purpose:** Safety net for overly long outputs, not primary constraint
- **Applied to:** All intro generation endpoints

### Files Modified
- `/app/backend/services/prompts.py` - INTRO_SYSTEM_PROMPT completely rewritten
- `/app/backend/routers/dungeon_forge.py` - Filter limits changed to 12
- `/app/backend/services/intro_service.py` - Docstring updated

---

## VERIFICATION

To test the new balanced approach:

1. **Create a new character**
2. **Check the intro for:**
   - ✅ 8-12 sentences
   - ✅ World name and past event mentioned
   - ✅ At least 2 factions named with their goals
   - ✅ Current political situation (war, peace, tension)
   - ✅ Region and town named with characteristics
   - ✅ Player's immediate location and sensory detail
   - ✅ Short sentences (15-20 words each)
   - ✅ No AI phrases like "tumultuous expanse" or "delicate balance"

3. **Should sound like:**
   - A human DM introducing a campaign
   - Matt Mercer's Continental Arc intros from Critical Role
   - Clear, direct storytelling with world context

4. **Should NOT sound like:**
   - A fantasy novel
   - Flowery, metaphorical prose
   - AI-generated blog content

---

## REFERENCES

**Matt Mercer's Intro Style:**
- Starts with world/continent name and history
- Introduces major factions and conflicts
- Zooms to specific region and town
- Grounds player in immediate location
- Uses clear, conversational language
- Provides context without info-dumping

**Human DM at a Table:**
- Speaks in complete but concise sentences
- Uses concrete nouns and specific details
- Avoids metaphors and flowery language
- Creates atmosphere through facts, not adjectives
- Keeps momentum - doesn't lecture

**This balanced approach gives you BOTH.**
