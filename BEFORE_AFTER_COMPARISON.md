# Before & After: Intro Narration Fix

## User's Reported Issue
"This narration filter is broken"

The intro text was still in AI novel-writing mode with:
- Flowery metaphors and purple prose
- Long, complex sentences
- AI filler phrases
- "Cinematic" atmospheric writing

---

## BEFORE THE FIX

### What the Old Prompt Asked For:
```
- 500–900 words for full intros
- 6 sections: World Scale, Continent Scale, Political Conflict, Starting Region, Starting City, Final Pinpoint
- "Use sensory detail sparingly and purposefully"
- "cinematic zoom from macro → micro"
```

### What the User Actually Got:
```
"In the tumultuous expanse of The Realm of Adventure, we find ourselves in an 
era profoundly marked by the Shattering of the Veil. This cataclysmic event, 
a rupture in the barrier separating the world from mystical dimensions beyond, 
has seeped rare and potent magic into the very bones of the land. The world 
feels its scars; rifts sporadically release bizarre creatures, ancient ruins 
cradle untapped power, and shadowy cults pledge allegiance to entities from 
foreign realms. The realm navigates a delicate balance, where hope coexists 
with haunting memories of chaos. The kingdom of Greyhold stands resilient, 
amidst these changes, its lands shaped by the ancient chaos. The northern 
border is watched over by the Sunspire Mountains, a daunting collection of 
peaks inhabited by fierce clans, protective of their isolation and wary of 
southern influence."
```

**Problems:**
- ❌ 6 sentences but each is 30-50 words
- ❌ "tumultuous expanse", "profoundly marked", "delicate balance" (AI metaphors)
- ❌ "we find ourselves", "seeped into the very bones" (flowery language)
- ❌ Reads like a fantasy novel, not a human DM
- ❌ Multiple complex clauses with semicolons
- ❌ Overly descriptive and atmospheric

**Why the Filter Didn't Help:**
The post-processing filter could count sentences and remove some phrases, but it couldn't fix the fundamental writing style. The LLM was generating novel-style prose because that's what the prompt asked for.

---

## AFTER THE FIX

### What the New Prompt Asks For:
```
🔥 CRITICAL: MAXIMUM 6 SENTENCES TOTAL FOR THE ENTIRE INTRO 🔥

BANNED WORDS/PHRASES (NEVER USE):
❌ "profoundly", "tumultuous expanse", "delicate balance", "haunting memories"
❌ "mystical dimensions", "very bones of the land"
❌ "we find ourselves", "marked by", "seeped into"

WRITING RULES:
✅ Short, punchy sentences (max 15-20 words each)
✅ Use simple, direct language
✅ ONE sensory detail maximum
✅ Sound like a human DM speaking aloud, NOT a narrator writing a book
```

### What the User Should Get Now:
```
"You're in Thornhaven, a logging town at the edge of the Darkwood. The tavern 
behind you is loud with evening drinkers. Rain drips from the inn's awning 
onto muddy streets. A town guard eyes you from across the square. The local 
baron's men have been asking about strangers. Your adventure begins here."
```

**Improvements:**
- ✅ 6 short sentences (10-15 words each)
- ✅ Simple, direct language
- ✅ Grounded in immediate sensory details
- ✅ Sounds like a human DM at a table
- ✅ No metaphors or purple prose
- ✅ Creates immediate tension and context

---

## The Key Insight

**Problem:** We were trying to fix AI novel-writing **after** generation using a simple filter.

**Solution:** Change the prompt to **prevent** AI novel-writing in the first place.

The filter is now a **safety net** for edge cases, not the primary solution. The LLM should generate human-like narration from the start.

---

## Testing Checklist

To verify the fix works:

1. **Create a new character**
   - The intro should be 6 short sentences
   - No AI phrases like "tumultuous", "delicate balance", "profoundly marked"
   - Should sound like someone speaking at a table

2. **Check backend logs**
   ```bash
   tail -f /var/log/supervisor/backend.out.log | grep "Intro"
   ```
   Look for:
   - "✅ Intro filtered to X sentences" (should be ≤6)
   - "🔍 DEBUG: First 200 chars" (should be simple language)

3. **Load an existing campaign**
   - Old intros should be filtered down to 6 sentences
   - Should be readable, even if not perfect (since it's truncating old prose)

---

## Why This Is the Right Approach

**Filtering AI output is like trying to remove salt from soup after you've added too much.**

It's better to not add the salt in the first place.

By rewriting the prompt to explicitly ban AI writing patterns and require human-like speech, we solve the problem at the source instead of trying to fix it after generation.
