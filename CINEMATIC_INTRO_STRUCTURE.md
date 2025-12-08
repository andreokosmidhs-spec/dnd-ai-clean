# 🎬 INTRODUCTION MODE — REQUIRED STRUCTURE

## Overview
When generating the campaign introduction, you MUST follow these steps EXACTLY, in this precise order.

**Do NOT skip any steps. Do NOT shorten them. Do NOT collapse them together.**

---

## STEP 1 — WORLD INTRO (CINEMATIC ZOOM-OUT)

**Purpose:** Give a sweeping, cinematic introduction to the entire world.

**Must Include:**
- Name of the world or continent
- Ancient conflicts or calamities that shaped it
- Current political tensions, empires, factions, guilds, or powers
- Tone and mood of the era

**Style:** Matthew Mercer, sweeping, mythic, poetic but clear.

**Example Tone:** "The world of X is a land of old scars and new ambitions..."

**Example:**
> "The continent of Valdrath stretches across a scarred landscape, torn by the Cataclysm Wars three centuries past. To the north lie the Frostspire Mountains, jagged peaks where dragons once ruled before the mortals rose against them. To the south, the Ashlands burn eternal, a wasteland of volcanic fury and forgotten gods. Between these extremes, kingdoms cling to survival, their borders ever-shifting as power, magic, and ambition clash in the shadows."

---

## STEP 2 — REGION INTRO (ZOOM INTO THE AREA)

**Purpose:** Describe the specific region where the story begins.

**Must Include:**
- Terrain (mountains, deserts, forests, jungle, coastline, etc.)
- Cultures and powers influencing the region
- Trade routes, guild activity, criminal networks, magical phenomena
- A few local tensions or rumors that set the stage

**Example Tone:** "To the west lies the Verdant Coast, a place of travelers, secrets, and uneasy alliances..."

**Example:**
> "Here, in the eastern territories known as the Shadowmarches, mist clings to the land like a living thing. Once ruled by merchant lords, the region now teeters on the edge of chaos—bandits control the roads, ancient ruins call to treasure hunters, and whispers of a rising cult spread through every tavern. The crown's authority is a distant memory. In the Shadowmarches, power belongs to those bold—or foolish—enough to seize it."

---

## STEP 3 — TOWN / STARTING LOCATION INTRO

**Purpose:** Zoom into the exact town or city.

**Must Include:**
- Streets, sounds, smells, atmosphere
- Social tension or mood
- What the locals whisper about
- What danger or opportunity hangs in the air tonight

**Example:** "Raven's Hollow sits like a shadowed jewel between the cliffs..."

**Full Example:**
> "You step into Raven's Hollow as twilight deepens into night. Lanternlight flickers across rain-slick cobblestones, casting dancing shadows on the crooked buildings that lean in like conspirators. The air smells of woodsmoke, wet stone, and something sharper—danger, perhaps, or opportunity. A bell tolls somewhere in the distance, muffled by the low murmur of voices from the market square ahead."

---

## STEP 4 — CHARACTER INTEGRATION

**Purpose:** Integrate the PLAYER CHARACTER directly into the world.

**Must Include (ALL required):**
- **Name** (use the character's actual name)
- Class + Race (e.g., "You, Avon, Human Rogue...")
- Background (Criminal, etc.)
- Why they arrived in this town
- What rumor, danger, or goal brought them here
- What weighs on their mind or heart
- What past event pushes them forward

**This MUST feel personal and specific.**

**Example:** "You, Avon, Human Rogue shaped by a Criminal past..."

**Full Example:**
> "You, Kael, a Human Rogue shaped by a Criminal past, came here fleeing Silverport where the Ironhand Syndicate put a price on your head after you stole the wrong ledger. Three weeks on the road, sleeping with one eye open, following whispers that Raven's Hollow was a place where people could disappear—or start over. But the guilt lingers, and Marcus 'the Hound' Greystone is two days behind you. You need leverage, coin, or allies before he arrives."

---

## STEP 5 — SCENE HOOKS (3–4 CHOICES)

**Purpose:** Present EXACTLY 3–4 choices for the player.

Each must be rooted in the scene AND tied to different types of opportunities.

**REQUIRED PATTERN:**
1. **A social lead** (merchant, local, guard)
2. **A suspicious or shadowy figure** (rogue, watcher, hooded figure)
3. **A public information or rumor source** (notice board, crowd)
4. **A wildcard / criminal instinct / danger lead** (alley, strange noise, hidden path)

**Format:** Populates the `options` field in the response

**Example:**
```json
"options": [
  "Approach the nervous merchant and ask about unusual activity",
  "Watch the cloaked figure observing from the tavern doorway",
  "Join the gathering crowd to hear what rumor has them stirred",
  "Trust your instincts—something about that dark alley calls to you"
]
```

---

## STEP 6 — DM PERSONALITY TAG

**Purpose:** End the introduction with a short DM prompt that:
- Encourages action
- Teases the player
- Feels alive and immersive

**Examples:**
✅ "Your move, rogue... what do you do?"  
✅ "So then... where does fate pull you next?"  
✅ "Well now... shall we begin?"

❌ "What would you like to do?" (too generic)  
❌ "I'll wait for your response." (breaks DM character)  
❌ "Please select an option." (robotic)

---

## 🚨 Critical Enforcement

**THESE SIX STEPS MUST ALWAYS BE PRESENT IN ORDER.**  
**FAILURE TO FOLLOW THIS ORDER IS NOT ALLOWED.**

**All 6 Steps Are Mandatory:**
1. WORLD INTRO (cinematic zoom-out)
2. REGION INTRO (zoom into the area)
3. TOWN/LOCATION INTRO (zoom into exact starting point)
4. CHARACTER INTEGRATION (name, class, race, background, personal story)
5. SCENE HOOKS (exactly 3-4 choices following the required pattern)
6. DM PERSONALITY TAG (encouraging/teasing final line)

**Do NOT:**
- ❌ Skip STEP 1 or STEP 2 (World and Region MUST be present)
- ❌ Collapse steps together or shorten them
- ❌ Omit the character's NAME in STEP 4
- ❌ Provide fewer than 3 or more than 4 options in STEP 5
- ❌ Forget the DM personality line in STEP 6

**Required Pattern for Step 5 (Scene Hooks):**
- Choice 1: Social lead (merchant, guard, local)
- Choice 2: Suspicious figure (cloaked, shadowy, watching)
- Choice 3: Public info (crowd, notice board, rumor)
- Choice 4: Wildcard (criminal instinct, danger, hidden path)

---

## Complete Example

**STEP 1 (World):**
> The continent of Valdrath stretches across a scarred landscape, torn by the Cataclysm Wars three centuries past. To the north lie the Frostspire Mountains, jagged peaks where dragons once ruled. To the south, the Ashlands burn eternal. Between these extremes, kingdoms cling to survival, their borders ever-shifting as power and ambition clash in the shadows.

**STEP 2 (Region):**
> Here, in the eastern territories known as the Shadowmarches, mist clings to the land like a living thing. Once ruled by merchant lords, the region now teeters on the edge of chaos—bandits control the roads, ancient ruins call to treasure hunters, and whispers of a rising cult spread through every tavern. Power belongs to those bold enough to seize it.

**STEP 3 (Town):**
> You step into Raven's Hollow as twilight deepens. Lanternlight flickers across rain-slick cobblestones, casting dancing shadows on crooked buildings that lean in like conspirators. The air smells of woodsmoke, wet stone, and danger. A bell tolls in the distance, muffled by the low murmur of voices from the market square ahead.

**STEP 4 (Character):**
> You came here fleeing Silverport, where the Ironhand Syndicate put a price on your head after you stole the wrong ledger. Three weeks on the road, following whispers that Raven's Hollow was a place to disappear—or start over. But the guilt lingers, and Marcus 'the Hound' Greystone is two days behind you. You need leverage, coin, or allies before he arrives.

**STEP 5 (Choices):**
- Approach the cloaked figures in the alley—your Criminal instincts tell you they're up to something
- Enter The Hollow's Crown tavern and listen for rumors about the artifact
- Seek out the local guild representative to gauge their interest in hiring someone discreet
- Find a quiet corner to watch and assess before making your move

**STEP 6 (DM Personality):**
> Your move, traveler. Where does fate pull you next?

---

## Implementation Location

**File:** `/app/backend/server.py`  
**Lines:** 2888-3050 (Cinematic Introduction Rules section)  
**Status:** ✅ Active and enforced

---

Last Updated: 2025-11-14
