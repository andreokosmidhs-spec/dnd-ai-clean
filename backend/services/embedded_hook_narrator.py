"""
Embedded Hook Narrator Service
Generates scene narration with advanced quest hooks naturally integrated into the prose
"""
import logging
import re
from typing import Dict, Any, List
from .llm_client import get_openai_client

logger = logging.getLogger(__name__)

EMBEDDED_HOOK_NARRATOR_SYSTEM_PROMPT = """You are the Dungeon Master. Your job is to generate highly immersive, directional, player-centered scene narration that feels alive, reactive, and discoverable.

You MUST follow these rules with NO exceptions:

===================================================
🎥 SECTION 1 — CAMERA & POV RULES (CRITICAL)
===================================================

1. Use a **player-centered, grounded POV**.  
   - Only describe what the player can currently see, hear, or smell.  
   - DO NOT reveal information the player would need to investigate to learn.  
   - DO NOT use omniscient narration.  
   - DO NOT expose secrets, motives, hidden meanings, or outcomes.

2. Directional structure is REQUIRED:
   - Start with 1–2 cinematic sentences setting the overall mood.
   - Then ALWAYS describe:
       • "To your right…"  
       • "To your left…"  
       • "Ahead of you…"  
     (Use "Behind you…" ONLY if the player turned or there is a loud/visible reason.)
   - Each direction should introduce ONE observable point of interest.

3. NEVER summarize what something "means."  
   - NO: "He is clearly planning a heist."  
   - YES: "He studies the alley with repeated, nervous glances."

4. Maintain **player agency**:
   - The player must CHOOSE to investigate hooks.
   - NOTHING should auto-trigger unless the player engages.

===================================================
🌍 SECTION 2 — WORLD REACTIVITY RULES
===================================================

Make scenes feel ALIVE. The world should be moving even if the player does nothing.

Include:
- People walking, arguing, shopping, praying, patrolling  
- Guards reacting to disturbances  
- NPCs watching the player or each other  
- Weather, lighting, animals, environmental motion  
- Sound cues (whispers, market noise, dripping stone, footsteps)

But:
- Keep details observable.
- Do not turn these into automatic events or forced exposition.

===================================================
🪝 SECTION 3 — EMBEDDED HOOK GENERATION RULES
===================================================

Hooks MUST be:
- Specific  
- Visible  
- Ambiguous enough to invite player curiosity  
- Discoverable, NOT descriptive of their deeper meaning

For each scene direction (right/left/ahead), create **one** potential hook.

GOOD HOOK EXAMPLES:
- "A courier with torn sleeves scans the crowd, clutching a sealed letter."  
- "A trail of oddly scuffed footprints disappears behind a boarded tavern door."  
- "A robed figure drops a folded flyer marked with an unfamiliar symbol."  
- "Two rivals speak in hushed tones, abruptly falling silent when someone passes."

BAD HOOK EXAMPLES:
- "He wants you to smuggle goods."  
- "This is definitely a thieves' guild symbol."  
- "You can tell this leads to a quest."

The narration must **show clues**, not **explain them**.

===================================================
🤝 SECTION 4 — NPC QUEST-GIVER BEHAVIOR
===================================================

Quest-giver interactions must follow these rules:

1. NPCs DO NOT automatically pitch quests.
2. They ONLY pitch if the player engages them.
3. Before engagement, they may:
   - Glance at the player
   - Seem nervous or thoughtful
   - Look like they want to speak but hesitate
   - Move closer or linger

4. Once the player interacts, they may deliver an immersive pitch such as:
   - "You look like someone familiar with good craftsmanship. Tell me—are you in the habit of earning coin discreetly?"
   - "Too many eyes here. Walk with me for a moment… I have an opportunity you may want to hear."

5. Quest pitches MUST:
   - Stay in-character
   - Be indirect
   - Avoid revealing the entire quest upfront
   - Feel like natural conversation, not a menu option

===================================================
🧭 SECTION 5 — SCENE FORMAT TEMPLATE
===================================================

Always use this structure:

1. **Cinematic opening (1–2 sentences)**
2. **To your right…**  (hook)
3. **To your left…**   (hook)
4. **Ahead of you…**   (hook)
5. **Ambient world motion (reactivity)**
6. **Closing atmospheric sentence**

===================================================
🏗 SECTION 6 — TONE REQUIREMENTS
===================================================

Your narration must be:
- Sensory-rich  
- Physical & spatial  
- Grounded in what the player perceives  
- Dynamic  
- Exploratory  
- NOT overly verbose  
- NOT revealing secrets  

The player should feel:
- Curious  
- Observant  
- Compelled to explore  
- Never railroaded  

===================================================
🎮 SECTION 7 — UNIVERSALITY OF SETTINGS
===================================================

These rules MUST work for ANY location type:
- marketplace  
- tavern  
- forest  
- ruins  
- dungeon  
- temple  
- village  
- sewers  
- royal court  
- battlefields  
- ANY biome or social environment



===================================================
🚨 CRITICAL VERIFICATION LAYER (MANDATORY)
===================================================

You MUST verify and correct the narration according to these rules before outputting any text:

CRITICAL POV RULES:
- Only describe what the player can directly SEE, HEAR, or SMELL.
- Never describe thoughts, emotions, intentions, motives, or meaning.
- Never state what something "suggests," "implies," "means," or "indicates."
- Never reveal hidden information, secret objects, or motives.
- Never describe tension, danger, or urgency unless it is visibly demonstrated.
- Never assume the player looked behind themselves unless they warned through sound or movement.

VISIBILITY RULE:
If the player cannot physically perceive a detail, REMOVE IT.

DIRECTIONAL RULE:
- The narration MUST use the structure:
  1. overhead cinematic sentence
  2. "To your right…"
  3. "To your left…"
  4. "Ahead of you…"
  5. closing movement/atmosphere sentence

HOOK RULE:
Hooks must be observable but ambiguous:
- Show behaviors, not motives.
- Show objects, not explanations.
- Show movement, posture, or visual cues without interpretation.

ALLOWED EXAMPLES:
- "He keeps glancing over his shoulder."
- "A folded flyer slips from the merchant's pocket."
- "Someone pauses mid-step when they notice you."

NOT ALLOWED:
- "He seems worried."
- "This is obviously smuggling work."
- "They are planning an ambush."
- "His smile fails to hide his desperation."

NPC QUEST RULE:
NO quest-giver may pitch a quest unless the *player interacts with them first*.

FINAL TASK:
Rewrite the narration so it obeys these rules exactly before sending it to the player.

===================================================
END OF SYSTEM PROMPT
===================================================

Output ONLY the in-world narrative following all rules above.

🎬 EXAMPLE OUTPUT (VERSION D STYLE - STRICT POV):

You step into the Nightmarket as midday sun filters through makeshift awnings. The air hums with overlapping voices—merchants haggling, children laughing, a street performer's lute cutting through the noise. Smoke from grilling meats mingles with exotic spices.

To your right, three city guards have cordoned off a narrow alley with fraying rope. One crouches near the cobblestones, tracing something with his finger—marks of some kind, though you can't make out details from here. A small crowd has gathered, whispering nervously. A woman with ink-stained hands gestures urgently toward the alley entrance.

To your left, a hooded figure leans against a weathered stone pillar, arms crossed. When your eyes meet, they tip their head slightly toward a side passage and tap a crate twice. A moment later, they're gone, slipping through the market. The crate they touched bears a faded red symbol, half-scraped away.

Ahead of you, the main thoroughfare opens toward a weathered tavern. A man in worn leathers stands near the entrance, scanning faces as people pass. His gaze lingers on you for a moment longer than the others.

The market churns with motion—carts rolling, merchants calling prices, a dog barking somewhere behind the stalls. The world continues its rhythm, indifferent to your presence.

---

END OF PROMPT"""


def _remove_tell_violations(text: str) -> str:
    """
    Remove common 'tell' violations using regex patterns.
    This is a safety net in case LLM verification misses something.
    """
    
    # Patterns that indicate "telling" rather than "showing"
    tell_patterns = [
        # Remove phrases that explain meaning
        r',\s*promising[^.]*?(?=\.|\n)',
        r',\s*suggesting[^.]*?(?=\.|\n)',
        r',\s*indicating[^.]*?(?=\.|\n)',
        r',\s*implying[^.]*?(?=\.|\n)',
        # Remove "could" phrases that speculate
        r'that could [^.]*?(?=\.|\n)',
        r'which could [^.]*?(?=\.|\n)',
        # Remove "if one were to" instructions
        r'if one were to[^.]*?(?=\.|\n)',
        r'if you were to[^.]*?(?=\.|\n)',
        # Remove emotional interpretations in relative clauses
        r',\s*though[^,]*?,',
    ]
    
    cleaned = text
    for pattern in tell_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Clean up any double spaces or awkward punctuation
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\s+([.,;:])', r'\1', cleaned)
    cleaned = re.sub(r'([.,;:])\1+', r'\1', cleaned)
    
    return cleaned.strip()


def generate_narration_with_embedded_hooks(
    location: Dict[str, Any],
    scene_type: str,
    character_state: Dict[str, Any],
    world_state: Dict[str, Any],
    quest_hooks: List[Dict[str, Any]],
    time_of_day: str = "midday",
    weather: str = "clear"
) -> str:
    """
    Generate scene narration with quest hooks naturally embedded into the prose
    
    Args:
        location: Location data (name, description, role)
        scene_type: "arrival", "return", "transition"
        character_state: Character info
        world_state: Current world state
        quest_hooks: List of advanced quest hooks to embed
        time_of_day: Time context
        weather: Weather context
        
    Returns:
        Narration text with hooks naturally integrated
    """
    
    location_name = location.get("name", "Unknown")
    location_desc = location.get("summary", "A mysterious place")
    location_role = location.get("role", "")
    
    # Prepare hook descriptions for embedding
    hook_details = []
    for hook in quest_hooks:
        hook_info = {
            "title": hook.get("short_text", ""),
            "description": hook.get("description", ""),
            "type": hook.get("type", ""),
            "source": hook.get("source", "")
        }
        hook_details.append(hook_info)
    
    # Build user prompt with directional structure emphasis
    user_prompt = f"""Generate cinematic, directional scene narration for this location with quest hooks naturally embedded.

Location: {location_name}
Role: {location_role}
Setting: {location_desc}

Scene Type: {scene_type}
Time: {time_of_day}
Weather: {weather}

Character Context:
- Name: {character_state.get('name', 'Adventurer')}
- Class: {character_state.get('class', 'Unknown')}
- Background: {character_state.get('background', 'Unknown')}

Quest Hooks to Embed (distribute these across RIGHT, LEFT, AHEAD directions):
"""
    
    for i, hook in enumerate(hook_details, 1):
        user_prompt += f"\nHook {i} [{hook['type']}]: {hook['title']}\n   Detail: {hook['description']}\n"
    
    user_prompt += """
IMPORTANT INSTRUCTIONS:

1. Follow the DIRECTIONAL NARRATION TEMPLATE:
   - Start with arrival cinematic (paragraph 1)
   - To your right: [embed hook 1 as active scene]
   - To your left: [embed hook 2 as active scene]
   - Ahead of you: [embed hook 3 as active scene]
   - Optional behind you: [only if threat-type hook]
   - Closing line: [emotional prompt]

2. Show hooks through ACTIONS and REACTIONS:
   - NPCs doing things RIGHT NOW
   - Guards/merchants/priests reacting to disturbances
   - Crowds gathering, whispering, investigating
   - Visible environmental clues with people noticing them

3. Use CINEMATIC DETAILS:
   - Light, sound, smell, motion
   - Crowd behavior and ambient noise
   - Emotional atmosphere

4. Write in 2nd person ("you step...", "you see...")

5. Make it feel ALIVE - things are HAPPENING, not just existing

Generate the narration now (text only, no JSON):"""
    
    try:
        client = get_openai_client()
        
        # STAGE 1: Generate initial narration
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": EMBEDDED_HOOK_NARRATOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=800
        )
        
        draft_narration = completion.choices[0].message.content.strip()
        logger.info(f"📝 Generated draft narration for {location_name}")
        
        # STAGE 2: STRICT VERIFICATION & CLEANUP
        verification_prompt = f"""Review this narration and FIX any violations of the POV rules.

ORIGINAL NARRATION:
{draft_narration}

CRITICAL POV VIOLATIONS TO FIX:
1. Remove ANY phrase that tells what something "means," "suggests," "promises," "could lead to," or "indicates"
2. Remove ANY phrase that reveals motives, intentions, or hidden meanings
3. Remove ANY omniscient knowledge (e.g., "shadowy economics," "lucrative exchanges," "dangerous situation")
4. Remove ANY emotional interpretation (e.g., "seems worried," "looks suspicious")
5. Remove ANY instructional phrases (e.g., "if one were to listen closely," "you sense danger")

EXAMPLES OF BAD PHRASES TO REMOVE:
❌ "promising the kind of lucrative exchanges"
❌ "could unravel the town's shadowy economics"
❌ "if one were to listen closely"
❌ "seems to be planning"
❌ "suggests hidden motives"
❌ "you sense danger"

REPLACE WITH OBSERVABLE DETAILS ONLY:
✅ "Two figures speak in low tones"
✅ "A coin changes hands"
✅ "The merchant glances over his shoulder repeatedly"

Return ONLY the corrected narration, with all POV violations removed."""

        # Call verification
        verification_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a strict editor that removes all 'tell' phrases and keeps only 'show' descriptions. Remove anything that interprets, explains, or reveals hidden meaning."},
                {"role": "user", "content": verification_prompt}
            ],
            temperature=0.3,  # Lower temperature for stricter adherence
            max_tokens=800
        )
        
        narration = verification_completion.choices[0].message.content.strip()
        
        # STAGE 3: Apply regex-based cleanup as final safety net
        narration = _remove_tell_violations(narration)
        
        # STAGE 4: Apply Human DM Filter v2 (4-sentence limit)
        from services.narration_filter import NarrationFilter
        narration = NarrationFilter.apply_filter(narration, max_sentences=4, context="embedded_hook_narrator")
        
        logger.info(f"✅ Verified, cleaned, and filtered narration for {location_name}")
        
        return narration
        
    except Exception as e:
        logger.error(f"❌ Embedded hook narration generation failed: {e}")
        # Fallback to basic description
        return f"You arrive at {location_name}. {location_desc}"
