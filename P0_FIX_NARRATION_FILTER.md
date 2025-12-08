# P0 FIX: Human DM Narration Filter Not Working for Intro

## Problem Statement
The "Human DM Filter v2" was not being applied to introductory narration when creating new characters or loading existing campaigns. Users reported seeing long, multi-paragraph intros (9+ sentences) despite the filter being designed to limit narration to 4-6 sentences.

**User's Actual Experience:**
Even with the filter in place, intros were still in "AI novel-writing mode":
- 6 very long sentences (50+ words each)
- Flowery metaphors ("mystical dimensions beyond", "very bones of the land", "haunting memories of chaos")
- AI filler phrases ("we find ourselves in", "profoundly marked by", "navigates a delicate balance")
- Novel-style atmospheric writing instead of human DM speech

## Root Cause Analysis

### THE REAL PROBLEM: Wrong System Prompt
**Location:** `/app/backend/services/prompts.py` line 122

The `INTRO_SYSTEM_PROMPT` was designed for **500-900 word cinematic intros** with a "macro to micro" zoom structure. This prompt was:
- Telling the LLM to write 500-900 words
- Requesting 6 separate sections with multiple sentences each
- Encouraging "sensory detail" and "cinematic" writing
- Creating novel-style prose by design

**The filter couldn't fix this** because it was receiving 900-word outputs and trying to truncate them to 6 sentences. The resulting text was still in AI novel-writing style, just shorter.

### Issue 1: `/intro/generate` Endpoint Missing Filter
**Location:** `/app/backend/routers/dungeon_forge.py` lines 587-748

The `/intro/generate` endpoint was:
1. Generating the intro via LLM (`generate_intro_markdown`)
2. Saving the UNFILTERED intro directly to the database
3. Returning the UNFILTERED intro to the frontend

**Impact:** Any character created through the standalone intro generation flow would have unfiltered narration.

### Issue 2: `/campaigns/latest` Endpoint Not Filtering Existing Data
**Location:** `/app/backend/routers/dungeon_forge.py` lines 465-585

The `/campaigns/latest` endpoint was:
1. Retrieving the `intro` field directly from the database
2. Returning it to the frontend WITHOUT applying the filter

**Impact:** Loading existing campaigns would return old, unfiltered intros that were saved before the filter was implemented.

### Issue 3: System Prompt Contradicted Filter Goals
**Location:** `/app/backend/services/prompts.py` line 122

The `INTRO_SYSTEM_PROMPT` was asking for the opposite of what we wanted:
- Asked for: 500-900 words, cinematic prose, sensory details
- Needed: 6 sentences max, direct language, human DM speech

**Impact:** Even with the filter applied, the base output was AI novel-writing that couldn't be salvaged by simple truncation.

## The Fix

### Fix 1: REWROTE THE INTRO SYSTEM PROMPT (CRITICAL)
**File:** `/app/backend/services/prompts.py`
**Lines:** 122-176 (completely replaced)

**Old Prompt:**
- Requested 500-900 words
- 6 sections with multiple sentences each
- Cinematic, atmospheric prose
- "Use sensory detail sparingly and purposefully"

**New Prompt:**
- **MAXIMUM 6 SENTENCES TOTAL** (emphasized in caps)
- Banned all AI phrases explicitly
- Banned metaphorical/flowery language
- Required short sentences (15-20 words max)
- Gave a GOOD example and a BAD example
- "Sound like a human DM speaking aloud, NOT a narrator writing a book"

Key additions to new prompt:
```
🔥 CRITICAL: MAXIMUM 6 SENTENCES TOTAL FOR THE ENTIRE INTRO 🔥

BANNED WORDS/PHRASES (NEVER USE):
❌ "profoundly", "tumultuous expanse", "delicate balance", "haunting memories"
❌ "mystical dimensions", "very bones of the land", "navigates a delicate balance"
❌ "we find ourselves", "marked by", "seeped into"
❌ ANY metaphorical or flowery language

WRITING RULES:
✅ Short, punchy sentences (max 15-20 words each)
✅ Sound like a human DM speaking aloud, NOT a narrator writing a book
```

This is the **primary fix** - the filter is now a safety net, not the main solution.

### Fix 2: Added Filter to `/intro/generate`
**File:** `/app/backend/routers/dungeon_forge.py`
**Lines:** After line 626

```python
# P0 FIX: Apply narration filter to intro (THIS WAS MISSING!)
from services.narration_filter import NarrationFilter
intro_md = NarrationFilter.apply_filter(intro_md, max_sentences=6, context="intro_generate_endpoint")
logger.info(f"✅ Intro filtered to {NarrationFilter.count_sentences(intro_md)} sentences")
```

Now the intro is filtered BEFORE being saved to the database and returned to the frontend.

### Fix 3: Added Filter to `/campaigns/latest`
**File:** `/app/backend/routers/dungeon_forge.py`
**Lines:** After line 500

```python
# P0 FIX: Apply filter to existing intros (in case they were saved before filter was added)
if intro_text:
    from services.narration_filter import NarrationFilter
    intro_text = NarrationFilter.apply_filter(intro_text, max_sentences=6, context="campaigns_latest_load")
    logger.info(f"✅ Filtered loaded intro to {NarrationFilter.count_sentences(intro_text)} sentences")
```

This ensures that even OLD intros saved before the filter was implemented will be filtered when loaded.

### Fix 4: Added Debug Logging to `/characters/create`
**File:** `/app/backend/routers/dungeon_forge.py`
**Lines:** Before line 1862

```python
# P0 FIX: Log the exact intro being returned to verify filter is working
intro_sentence_count = NarrationFilter.count_sentences(intro_md)
logger.info(f"🔍 DEBUG: intro_md has {intro_sentence_count} sentences")
logger.info(f"🔍 DEBUG: First 200 chars of intro_md being returned: {intro_md[:200]}")
```

This helps trace exactly what's being sent to the frontend for debugging.

## How the Filter Works

The `NarrationFilter` class (`/app/backend/services/narration_filter.py`) implements the "Human DM Filter v2" rules:

1. **Remove banned phrases**: Strips AI-style filler like "you notice", "it seems that", "suddenly"
2. **Enforce sentence limit**: Truncates text to a maximum number of sentences (default 4, 6 for intros)
3. **Detect novel-style writing**: Logs warnings for overly long sentences or excessive sensory descriptions

### Example
```python
# Before filtering
original = """
You stand at the weathered gates of Thornhaven, a modest settlement clinging to the edge of the Whispering Wood. The sun hangs low in the sky, casting long shadows across the cobblestone streets and timber-framed buildings that huddle together as if seeking warmth. A cool breeze carries the scent of pine and distant rain, while the faint clatter of a blacksmith's hammer echoes from somewhere within the town. The journey here has been long and arduous, but as you take in the sight before you, a sense of purpose stirs in your chest. This is where your story begins. Beyond the gates, you can see townsfolk going about their evening routines—a merchant packing up his wares, children chasing each other through the streets, and an old woman sweeping her doorstep. The town may be small, but it feels alive, full of stories waiting to be uncovered. You take a deep breath, adjust your pack, and step forward through the gates, ready to carve your name into the tapestry of this world's history. The adventure awaits, and Thornhaven is just the beginning.
"""
# 9 sentences, 1058 chars

# After filtering (max_sentences=6)
filtered = """
You stand at the weathered gates of Thornhaven, a modest settlement clinging to the edge of the Whispering Wood. The sun hangs low in the sky, casting long shadows across the cobblestone streets and timber-framed buildings that huddle together as if seeking warmth. A cool breeze carries the scent of pine and distant rain, while the faint clatter of a blacksmith's hammer echoes from somewhere within the town. The journey here has been long and arduous, but as you take in the sight before you, a sense of purpose stirs in your chest. This is where your story begins. Beyond the gates, you can see townsfolk going about their evening routines—a merchant packing up his wares, children chasing each other through the streets, and an old woman sweeping her doorstep.
"""
# 6 sentences, 766 chars (27% reduction)
```

## Testing Plan

### Manual Testing
1. **New Character Creation:**
   - Create a new campaign and character
   - Observe the intro narration
   - **Expected:** Intro should be 6 sentences or less
   - **How to verify:** Check backend logs for "Intro filtered to X sentences"

2. **Loading Existing Campaign:**
   - Click "Load Last Campaign from DB"
   - Observe the intro narration
   - **Expected:** Even old intros should be filtered to 6 sentences
   - **How to verify:** Check backend logs for "Filtered loaded intro to X sentences"

3. **In-Game Narration:**
   - Take an action in-game
   - Observe the DM's response
   - **Expected:** Narration should be 4 sentences or less
   - **How to verify:** Check backend logs for "Narration filtered: X sentences"

### Backend Logs to Monitor
```bash
# Watch for filter application
tail -f /var/log/supervisor/backend.out.log | grep "filtered\|Intro"

# Expected log entries:
# ✅ Intro filtered to 6 sentences
# ✅ Filtered loaded intro to 6 sentences
# ✅ Narration filtered: 4 sentences
```

## Related Files
- `/app/backend/routers/dungeon_forge.py` - Main router with 3 fixes
- `/app/backend/services/narration_filter.py` - Filter implementation (unchanged)
- `/app/backend/services/intro_service.py` - Raw intro generation (unchanged, filter applied in router)

## Verification Status
- [x] Code changes implemented
- [x] Backend restarted
- [ ] Manual testing with new character (requires user to test)
- [ ] Manual testing with existing campaign (requires user to test)

## Notes for User
After this fix:
1. **New characters** will have filtered intros (6 sentences max)
2. **Loaded campaigns** will have their intros filtered on-the-fly (even if they were saved before the fix)
3. **In-game narration** continues to use the filter (already working, 4 sentences max)

The fix is retroactive for loading campaigns, so you don't need to delete old data.
