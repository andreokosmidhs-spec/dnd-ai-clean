# Advanced Quest Hook Generation System

**Date:** 2025-12-02  
**Status:** Implemented  
**Purpose:** Replace vague atmospheric hooks with concrete, actionable quest hooks using multi-stage LLM reasoning

---

## Problem Statement

**Original Issue:**
The previous hook generation system produced vague, atmospheric descriptions like:
- "You hear locals whisper about strange happenings near the ruins"
- "The atmosphere is thick with secrecy and opportunity"
- "You notice someone acting strangely"

**What Was Missing:**
- ❌ No specific visible details (who, where, what they look like)
- ❌ No immediate actionable prompts (what can player DO right now)
- ❌ No concrete scene elements (blood trail, dropped letter, argument)
- ❌ Hooks felt like generic templates, not scene-specific

**Player Experience Impact:**
- Players couldn't visualize the scene
- Unclear what to investigate or who to talk to
- Hooks felt disconnected from narrative
- DM had to improvise all details

---

## Solution: Multi-Stage Hook Generation Pipeline

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Generate Scene Description (Atmospheric)            │
│ Service: scene_generator.py                                 │
│ Output: Narrative text setting mood, time, weather          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Generate Advanced Hooks FROM Scene                  │
│ Service: advanced_hook_generator.py                         │
│ Process: Multi-stage LLM reasoning (5 stages)               │
│ Output: 2-5 concrete, actionable quest hooks                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Convert Hooks to Leads                              │
│ Service: scene_hook_integration.py                          │
│ Output: LeadDelta objects for Campaign Log                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Display in Campaign Log - Leads Tab                 │
│ UI: CampaignLogPanel.jsx                                    │
│ Player sees concrete, actionable leads to pursue            │
└─────────────────────────────────────────────────────────────┘
```

---

## Multi-Stage Reasoning Process

The advanced hook generator follows a **5-stage internal reasoning pipeline**:

### Stage 1: Extract Scene Signals

The LLM identifies:
- **Tensions:** fear, secrecy, unrest, wealth, danger, hope
- **Entities:** NPCs, factions, POIs, creatures, world forces
- **Environmental anomalies:** blood, graffiti, tracks, smells, sounds
- **Social patterns:** whispers, crowds, arguments, evasive behavior
- **Opportunity vectors:** jobs, bargains, secrets, vulnerabilities
- **Implied danger:** ambush points, predators, traps, watchers
- **Factional dynamics:** power struggles, territory, recruitment

### Stage 2: Transform Signals Into Hook Types

Each signal is categorized as:
- **investigation** - something to inspect or uncover
- **opportunity** - chance for profit, alliance, advantage
- **threat** - immediate or emerging danger
- **social** - negotiation, influence, deception, diplomacy
- **exploration** - hidden routes, secret places, unknown areas

Hooks are **diversified** to avoid repetition.

### Stage 3: Materialize Hooks Into Actionable Prompts

Each hook must include:
1. **Concrete trigger** - "hooded courier drops sealed letter" NOT "people are secretive"
2. **Reason to care** - why is it valuable/urgent/dangerous?
3. **Target** - specific NPC, faction, POI, or location
4. **Minimal lore invention** - simple placeholders if needed (npc:mysterious_courier)

### Stage 4: Difficulty Assessment

Based on:
- **easy** → Social encounters, simple investigations, minor tasks
- **medium** → Tensions, danger signs, criminal activity, stealth
- **hard** → Combat, conspiracies, faction conflict, supernatural

### Stage 5: Output Clean JSON

Structured format for integration into Campaign Log.

---

## Hook Schema

```json
{
  "type": "investigation | opportunity | threat | social | exploration",
  "short_text": "6-12 word actionable hook title",
  "description": "One-sentence concrete description with visible details",
  "source": "npc:{id} | faction:{id} | poi:{id} | world:{keyword}",
  "difficulty": "easy | medium | hard",
  "related_npcs": ["npc_id"],
  "related_locations": ["location_id"],
  "related_factions": ["faction_id"]
}
```

---

## Example Transformation

### Before (Vague Hook):
```json
{
  "type": "rumor",
  "description": "You overhear someone mentioning something suspicious.",
  "source": "npc:unknown",
  "difficulty": "medium"
}
```

**Problems:**
- Who is "someone"? What do they look like?
- Where are they standing?
- What EXACTLY did they say?
- What can I do RIGHT NOW?

### After (Advanced Hook):
```json
{
  "type": "investigation",
  "short_text": "Blood trail vanishes behind sealed warehouse",
  "description": "A thin streak of blood leads to a locked warehouse door with fresh scrape marks on the cobblestones.",
  "source": "poi:old_warehouse",
  "difficulty": "medium",
  "related_npcs": [],
  "related_locations": ["old_warehouse", "market_district"],
  "related_factions": []
}
```

**Improvements:**
✅ **Visible:** "thin streak of blood", "locked door", "fresh scrape marks"  
✅ **Location:** "warehouse door", "cobblestones"  
✅ **Actionable:** Player can immediately investigate the door, follow the trail, or look for witnesses  
✅ **Concrete:** Specific details create mental image

---

## Implementation Files

### New Files Created:

1. **`/app/backend/services/advanced_hook_generator.py`**
   - Core multi-stage hook generation logic
   - LLM-powered analysis with structured reasoning
   - Fallback system for robustness
   - Validation and error handling

2. **`/app/backend/services/scene_hook_integration.py`**
   - Orchestrates scene generation + hook generation flow
   - Converts hooks to LeadDelta format
   - Handles integration with Campaign Log

3. **`/app/meta/ADVANCED_HOOK_SYSTEM.md`**
   - This documentation file

### Modified Files:

*None yet - system is ready for integration*

---

## Integration Points

### Where to Integrate:

The advanced hook system is designed to integrate at scene generation points:

**1. Character Creation / Arrival Scene:**
```python
# In dungeon_forge.py - character creation flow
from services.scene_hook_integration import generate_scene_with_advanced_hooks

scene_data = await generate_scene_with_advanced_hooks(
    scene_type="arrival",
    location=starting_town,
    character_state=character_state,
    world_state=world_state,
    world_blueprint=world_blueprint
)

# scene_data contains:
# - description: atmospheric scene text
# - quest_hooks: advanced actionable hooks
```

**2. During Gameplay - Location Changes:**
```python
# When player moves to new location
scene_data = await generate_scene_with_advanced_hooks(
    scene_type="return",  # or "transition"
    location=new_location,
    character_state=character_state,
    world_state=world_state,
    world_blueprint=world_blueprint
)

# Convert hooks to leads
from services.scene_hook_integration import convert_hooks_to_lead_deltas

lead_deltas = convert_hooks_to_lead_deltas(
    hooks=scene_data["quest_hooks"],
    location_id=new_location["id"],
    scene_id=f"scene_{timestamp}"
)

# Apply leads to Campaign Log
await campaign_log_service.apply_delta(
    campaign_id=campaign_id,
    delta=CampaignLogDelta(leads=lead_deltas),
    character_id=character_id
)
```

---

## Testing Strategy

### Manual Testing:

1. **Test Scene Generation:**
   ```python
   # Create test scene
   scene_data = await generate_scene_with_advanced_hooks(
       scene_type="arrival",
       location={"name": "Dark Hollow", "role": "criminal haven"},
       character_state={"class": "Rogue", "level": 1},
       world_state={"time_of_day": "night"},
       world_blueprint={...}
   )
   
   # Verify hooks are concrete
   for hook in scene_data["quest_hooks"]:
       assert len(hook["description"]) > 20
       assert "you notice" not in hook["description"].lower() or "visible detail" in hook["description"]
       assert hook["difficulty"] in ["easy", "medium", "hard"]
   ```

2. **Test Hook Quality:**
   - Each hook should answer: WHO, WHERE, WHAT (visible)
   - Each hook should be immediately actionable
   - No generic phrases like "something strange" or "people whisper"

3. **Test Campaign Log Integration:**
   - Hooks should appear in Leads tab after scene generation
   - Lead status should be "unexplored"
   - Lead details should match hook details

---

## Configuration

### LLM Model Selection:

**Advanced Hook Generator:**
- Model: `gpt-4o` (full model, not mini)
- Reason: Sophisticated multi-stage reasoning requires full model capabilities
- Temperature: 0.8 (higher for creative hook generation)
- Max Tokens: 1500 (enough for 4-5 detailed hooks)

**Scene Generator:**
- Model: `gpt-4o-mini` (unchanged)
- Reason: Scene description is simpler, mini is sufficient
- Temperature: 0.7
- Max Tokens: 300

### Cost Considerations:

- Advanced hooks only generated at key moments (arrivals, major transitions)
- Not generated for every action (too expensive)
- Fallback system prevents failures from blocking gameplay

---

## Examples

### Example 1: Dark Hollow (Criminal Haven)

**Scene Description:**
> "You arrive in Dark Hollow as the misty sun pours through the narrow gaps between tall, crooked buildings. The distant murmur of hushed conversations and the occasional clinking of coins rise like a low hum in the air. The atmosphere is thick with a mix of secrecy and opportunity, where every dark corner can hide a chance for escape or danger."

**Generated Advanced Hooks:**

```json
[
  {
    "type": "social",
    "short_text": "Desperate courier seeks discreet escort",
    "description": "A trembling courier with torn sleeves clutches a sealed parcel, scanning the alley for someone trustworthy.",
    "source": "npc:frantic_courier",
    "difficulty": "easy"
  },
  {
    "type": "investigation",
    "short_text": "Blood trail vanishes into sealed storehouse",
    "description": "A thin streak of blood leads to a locked storehouse door with fresh scrape marks.",
    "source": "poi:abandoned_storehouse",
    "difficulty": "medium"
  },
  {
    "type": "opportunity",
    "short_text": "Smuggler whispers offer of profitable work",
    "description": "A hooded figure in the shadowed archway signals you with promises of lucrative, discreet work.",
    "source": "faction:local_smugglers",
    "difficulty": "medium"
  },
  {
    "type": "threat",
    "short_text": "Silent watcher tracks movement from rooftops",
    "description": "A silhouette crouched on the rooftop mirrors your every step with predatory stillness.",
    "source": "npc:unknown_lookout",
    "difficulty": "hard"
  }
]
```

**Player Experience:**
- ✅ Clear visuals: "trembling courier with torn sleeves", "thin streak of blood"
- ✅ Actionable: Can talk to courier, investigate door, approach smuggler, confront watcher
- ✅ Diverse: Social, investigation, opportunity, threat
- ✅ Grounded: All hooks arise from the Dark Hollow setting

---

## Future Enhancements

### Potential Improvements:

1. **Dynamic Hook Refresh:**
   - Regenerate hooks when player returns to location after time skip
   - Some hooks may resolve automatically (courier leaves)
   - New hooks emerge based on player actions

2. **Hook Dependencies:**
   - Completing Hook A unlocks Hook B
   - Example: Investigating blood trail → leads to smuggler hideout → reveals faction conflict

3. **NPC Memory of Hooks:**
   - If player ignores courier, courier remembers and acts differently later
   - Consequences for missed opportunities

4. **Faction-Aware Hooks:**
   - Hooks change based on player reputation
   - Hostile factions generate threat hooks
   - Friendly factions generate opportunity hooks

5. **Time-Sensitive Hooks:**
   - Some hooks expire if not pursued quickly
   - "Courier disappears if not helped within 1 hour"
   - Creates urgency and decision pressure

---

## Debugging

### Common Issues:

**Issue: Hooks are still vague**
- Check LLM model (must be gpt-4o, not mini)
- Check temperature (should be 0.8)
- Verify system prompt is correctly loaded
- Check if fallback hooks are being used (error in LLM call)

**Issue: Hooks don't match scene**
- Ensure scene_description is passed correctly
- Check world_blueprint context is complete
- Verify location_name matches actual location

**Issue: Too many hooks or too few**
- Adjust max_hooks parameter (default: 4)
- Check if hook validation is rejecting valid hooks
- Review LLM output raw JSON for parsing errors

### Logging:

```python
logger.info(f"✅ Generated {len(validated_hooks)} advanced quest hooks for {location_name}")
logger.warning(f"⚠️ Invalid hook structure, skipping: {hook}")
logger.error(f"❌ Advanced hook generation failed: {str(e)}")
```

---

## Success Criteria

**Hook Quality Checklist:**

For each generated hook, verify:
- [ ] Short text is 6-12 words
- [ ] Description contains specific visible details
- [ ] Player can act on it immediately
- [ ] Type matches content (investigation/opportunity/threat/social/exploration)
- [ ] Difficulty makes sense for content
- [ ] Source is properly formatted (npc:id, faction:name, poi:name)
- [ ] Related entities are populated if relevant

**System Integration Checklist:**

- [ ] Hooks appear in Campaign Log - Leads tab
- [ ] Hooks can be converted to quests
- [ ] Hooks display with proper formatting
- [ ] Player can update lead status
- [ ] Hooks integrate with existing game flow

---

## Conclusion

The Advanced Hook Generation System transforms vague atmospheric hooks into concrete, actionable quest prompts that enhance player immersion and clarity. By using multi-stage LLM reasoning, the system generates hooks that:

- **Show, don't tell** - Visible details instead of abstract concepts
- **Are immediately actionable** - Player knows what to do RIGHT NOW
- **Arise from the scene** - Not generic templates
- **Create vivid mental images** - Specific details paint the picture

This system is ready for integration into the main game loop and will significantly improve the quest discovery experience.

---

**Implementation Status:** ✅ Complete and ready for integration  
**Next Steps:** Integrate into dungeon_forge.py at scene generation points  
**Testing:** Manual testing recommended before production deployment
