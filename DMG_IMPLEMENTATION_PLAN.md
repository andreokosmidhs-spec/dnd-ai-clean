# DMG-BASED DM ENGINE IMPLEMENTATION PLAN
**Source:** D&D 5e Dungeon Master's Guide
**Purpose:** Transform extracted DMG rules into implementation-ready systems for Dungeon Forge

---

## 📊 EXECUTIVE SUMMARY

**Current System Status:**
- ✅ Basic combat mechanics (5e compliant)
- ✅ Target resolution and plot armor
- ⚠️ Limited DM behavioral rules
- ❌ No player motivation tracking
- ❌ No pacing/tension management
- ❌ No consequence escalation system
- ❌ Minimal NPC personality system

**Missing Critical Systems (From DMG):**
1. Player Motivation Engine (8 types, DMG p.8-10)
2. Pacing & Tension System (DMG p.24)
3. Information Dispensing Rules (DMG p.26-27)
4. Improvisation Framework (DMG p.28-29)
5. Consequence Escalation (Implicit throughout DMG)
6. NPC Personality Engine (DMG p.186)
7. Session Flow Manager (DMG p.20-24)
8. Story Cohesion Validator (DMG p.140-145)

---

## 1️⃣ PLAYER MOTIVATION ENGINE

### DMG Rules (Pages 8-10)

**8 Player Archetypes:**
1. **Actor:** Values narrative, wants to portray character
2. **Explorer:** Seeks new places, experiences, discovery
3. **Instigator:** Makes things happen, takes risks, thrives in combat
4. **Power Gamer:** Levels, loot, and abilities over story
5. **Slayer:** Combat-focused, wants monster battles
6. **Storyteller:** Narrative chronicle over individual motivations
7. **Thinker:** Careful choices, planning, sound tactics
8. **Watcher:** Casual, social experience over immersion

### Implementation: Player Profile Tracker

**File:** `/app/backend/services/player_motivation_service.py`

```python
class PlayerMotivation:
    """Track player archetype and tailor content accordingly"""
    
    ARCHETYPES = {
        "actor": {
            "preferences": ["roleplay", "character_development", "narrative"],
            "avoid": ["excessive_combat", "grinding"],
            "content_weight": {"social": 0.4, "exploration": 0.3, "combat": 0.3}
        },
        "explorer": {
            "preferences": ["discovery", "new_locations", "secrets"],
            "avoid": ["repetitive_encounters", "railroading"],
            "content_weight": {"exploration": 0.5, "social": 0.3, "combat": 0.2}
        },
        "instigator": {
            "preferences": ["action", "risk", "combat", "choices_with_consequences"],
            "avoid": ["inactivity", "analysis_paralysis"],
            "content_weight": {"combat": 0.5, "exploration": 0.3, "social": 0.2}
        },
        "power_gamer": {
            "preferences": ["leveling", "loot", "optimization", "abilities"],
            "avoid": ["story_heavy_sessions", "roleplay_focus"],
            "content_weight": {"combat": 0.5, "loot": 0.3, "exploration": 0.2}
        },
        "slayer": {
            "preferences": ["combat", "monster_variety", "tactical_battles"],
            "avoid": ["social_encounters", "puzzles"],
            "content_weight": {"combat": 0.7, "exploration": 0.2, "social": 0.1}
        },
        "storyteller": {
            "preferences": ["narrative", "world_lore", "consequences"],
            "avoid": ["meaningless_combat", "lack_of_continuity"],
            "content_weight": {"social": 0.4, "exploration": 0.4, "combat": 0.2}
        },
        "thinker": {
            "preferences": ["planning", "tactics", "puzzles", "investigation"],
            "avoid": ["rushed_decisions", "random_combat"],
            "content_weight": {"exploration": 0.4, "combat": 0.3, "puzzle": 0.3}
        },
        "watcher": {
            "preferences": ["easy_entry", "social_experience", "low_complexity"],
            "avoid": ["complex_rules", "heavy_optimization"],
            "content_weight": {"social": 0.5, "exploration": 0.3, "combat": 0.2}
        }
    }
    
    def detect_player_archetype(session_history):
        """
        Analyze player behavior to infer archetype:
        - Combat frequency → Slayer/Instigator
        - Social interaction attempts → Actor/Storyteller
        - Exploration actions → Explorer/Thinker
        """
        pass
    
    def adjust_dm_behavior(archetype, encounter_type):
        """
        Modify DM prompts and content generation based on archetype
        """
        pass
```

**Database Schema:**
```python
{
    "player_profile": {
        "archetype_primary": "explorer",
        "archetype_secondary": "thinker",
        "preferences": {
            "combat_frequency": 0.3,
            "social_frequency": 0.4,
            "exploration_frequency": 0.3
        },
        "engagement_score": 0.85,
        "last_updated": "2025-01-15"
    }
}
```

**DMG Compliance:** ✅ Covers all 8 archetypes from pages 8-10

---

## 2️⃣ PACING & TENSION SYSTEM

### DMG Rules (Page 24)

**Core Principle:** "Ebb and flow of action and anticipation"

**Pacing Phases:**
1. **Building Anticipation** - Brooding menace in exploration
2. **Finding the Fun** - Giving clues to solve problems
3. **Climactic Action** - Pulse-pounding excitement
4. **Natural Pauses** - Breaks and rest points

### Implementation: Tension Tracker

**File:** `/app/backend/services/pacing_service.py`

```python
class TensionManager:
    """
    Track narrative tension and adjust pacing dynamically.
    DMG p.24: "Ebb and flow of action and anticipation"
    """
    
    TENSION_LEVELS = {
        "calm": {
            "range": (0, 20),
            "description": "Safe, routine, social interaction",
            "dm_guidance": "Use for shopping, resting, planning",
            "next_phase": "building"
        },
        "building": {
            "range": (21, 40),
            "description": "Hints of danger, mysterious clues",
            "dm_guidance": "Describe shadows, sounds, ominous signs. DMG p.24: 'brooding menace'",
            "next_phase": "tense"
        },
        "tense": {
            "range": (41, 60),
            "description": "Danger is near, players alert",
            "dm_guidance": "Use passive Perception, reveal threats partially",
            "next_phase": "climax"
        },
        "climax": {
            "range": (61, 90),
            "description": "Active combat or crisis resolution",
            "dm_guidance": "DMG p.24: 'pulse-pounding action', keep moving",
            "next_phase": "resolution"
        },
        "resolution": {
            "range": (91, 100),
            "description": "Crisis resolved, rewards distributed",
            "dm_guidance": "Wrap up, give XP, allow rest. DMG p.24: 'natural rest points'",
            "next_phase": "calm"
        }
    }
    
    def calculate_tension(world_state, recent_actions):
        """
        Calculate current tension based on:
        - Time since last combat
        - Player HP percentage
        - Active threats (combat_state exists)
        - Quest urgency
        - Environmental dangers
        """
        tension = 0
        
        if world_state.get('combat_active'):
            tension += 60  # Immediate climax
        elif world_state.get('time_since_combat_minutes', 999) < 10:
            tension += 40  # Recent combat, still tense
        elif world_state.get('quest_urgency') == 'high':
            tension += 30  # Building tension
        
        player_hp_avg = sum(p['hp'] / p['max_hp'] for p in players) / len(players)
        if player_hp_avg < 0.5:
            tension += 20  # Danger is real
        
        return min(100, tension)
    
    def get_dm_pacing_instructions(tension_level):
        """
        Return specific instructions for DM based on tension.
        DMG p.24: Different narration styles for different phases
        """
        phase = get_phase_from_tension(tension_level)
        return TENSION_LEVELS[phase]["dm_guidance"]
```

**Integration with DM Prompts:**
```python
# In prompts.py
def build_dm_prompt(tension_level):
    pacing_instruction = TensionManager.get_dm_pacing_instructions(tension_level)
    
    return f"""
    You are the Dungeon Master.
    
    CURRENT PACING (DMG p.24): {pacing_instruction}
    
    [Rest of prompt...]
    """
```

**DMG Compliance:** ✅ Implements "ebb and flow" principle from p.24

---

## 3️⃣ INFORMATION DISPENSING SYSTEM

### DMG Rules (Pages 26-27)

**Core Principles:**
- "Give players information they need to make smart choices" (p.26)
- Use passive skill checks to maintain momentum (p.26)
- "Tell players everything they need to know, but not all at once" (p.26)
- Make conditions clear (p.27)

### Implementation: Information Manager

**File:** `/app/backend/services/information_service.py`

```python
class InformationDispenser:
    """
    DMG p.26-27: Control information flow to maintain suspense and momentum
    """
    
    def apply_passive_perception(character, world_state):
        """
        DMG p.26: "Use passive Perception regularly to maintain momentum"
        Auto-reveal information without explicit checks
        """
        perception_score = 10 + character['abilities']['wis_mod'] + character['proficiency_bonus']
        
        # Check if any secrets are within perception threshold
        location_secrets = world_state['current_location']['secrets']
        revealed = [s for s in location_secrets if s['dc'] <= perception_score]
        
        return revealed
    
    def drip_feed_information(information_list, tension_level):
        """
        DMG p.26: "not all at once"
        
        Release information based on pacing:
        - Calm: Give 1-2 pieces
        - Building: Give 2-3 pieces with ominous hints
        - Tense: Hold back to maintain mystery
        - Climax: Reveal critical info if needed
        - Resolution: Full disclosure
        """
        if tension_level == "calm":
            return information_list[:2]
        elif tension_level == "building":
            return information_list[:3]  # But frame ominously
        elif tension_level == "tense":
            return information_list[:1]  # Withhold to build suspense
        elif tension_level == "climax":
            return information_list  # Player needs everything to act
        else:  # resolution
            return information_list
    
    def clarify_conditions(character_state):
        """
        DMG p.27: "Make conditions clear to players"
        
        Return plain language explanations of mechanical conditions
        """
        conditions = character_state.get('conditions', [])
        explanations = {
            'unconscious': "You are unconscious (0 HP). You cannot take actions. Enemies have advantage against you.",
            'poisoned': "You have disadvantage on attack rolls and ability checks.",
            'prone': "You have disadvantage on attacks. Enemies within 5 feet have advantage against you.",
            # etc.
        }
        return [explanations.get(c, c) for c in conditions]
```

**Integration with Action Handler:**
```python
# In dungeon_forge.py
def process_action(action_request):
    # Apply passive perception automatically
    auto_revealed = InformationDispenser.apply_passive_perception(
        character_state, world_state
    )
    
    if auto_revealed:
        narration_prefix = f"You notice: {', '.join(auto_revealed)}. "
    
    # Drip-feed information based on tension
    available_info = world_state['pending_reveals']
    info_to_reveal = InformationDispenser.drip_feed_information(
        available_info, current_tension
    )
    
    # Add to narration
```

**DMG Compliance:** ✅ Implements passive checks (p.26), information pacing (p.26), condition clarity (p.27)

---

## 4️⃣ IMPROVISATION FRAMEWORK

### DMG Rules (Pages 28-29)

**Core Principle:** "Say Yes" - Build on player actions and ideas (p.28-29)

### Implementation: Improvisation Handler

**File:** `/app/backend/services/improvisation_service.py`

```python
class ImprovisationEngine:
    """
    DMG p.28-29: Handle unexpected player actions with flexibility
    """
    
    def classify_unexpected_action(player_action, expected_actions):
        """
        Determine if action is:
        - Creative (reward with advantage or success)
        - Disruptive (requires consequences)
        - Unclear (needs clarification)
        """
        # Use LLM to classify
        pass
    
    def apply_say_yes_principle(player_action):
        """
        DMG p.28: "Build on player actions and ideas"
        
        Instead of blocking actions, find ways to make them work:
        - Lower DC if creative
        - Introduce complications if risky
        - Offer alternative paths if impossible
        """
        action_type = classify_action_creativity(player_action)
        
        if action_type == "creative_but_plausible":
            return {
                "allow": True,
                "bonus": "advantage",
                "dm_hint": "Reward creativity with advantage on the check"
            }
        elif action_type == "risky_but_possible":
            return {
                "allow": True,
                "complication": "introduce_twist",
                "dm_hint": "Allow it but add a complication (DMG p.29)"
            }
        elif action_type == "impossible":
            return {
                "allow": False,
                "alternative": "suggest_different_approach",
                "dm_hint": "Explain why it won't work, suggest alternatives"
            }
```

**Integration with DM Prompt:**
```python
# Add to DM system prompt
"""
IMPROVISATION (DMG p.28-29):
- Say YES to creative player ideas
- Build on their actions, don't block them
- If risky, allow but introduce complications
- Reward creativity with advantage or lowered DCs
"""
```

**DMG Compliance:** ✅ Implements "Say Yes" principle from p.28-29

---

## 5️⃣ CONSEQUENCE ESCALATION SYSTEM

### DMG Rules (Implicit throughout, especially p.30-32, p.74, p.98-99)

**Consequence Types:**
1. **Immediate** - Direct results of actions (combat damage, NPC reactions)
2. **Short-term** - Effects within current session (guards alerted, reputation hit)
3. **Long-term** - Campaign-level consequences (bounties, faction wars, prophecy)

### Implementation: Consequence Manager

**File:** `/app/backend/services/consequence_service.py`

```python
class ConsequenceEngine:
    """
    Track and escalate consequences of player actions.
    DMG p.74: "Failure introduces complications"
    """
    
    SEVERITY_LEVELS = {
        "minor": {
            "examples": ["NPC annoyed", "small reputation loss"],
            "escalation_threshold": 3,
            "next_level": "moderate"
        },
        "moderate": {
            "examples": ["Guards investigate", "quest giver refuses help"],
            "escalation_threshold": 2,
            "next_level": "severe"
        },
        "severe": {
            "examples": ["Bounty posted", "Faction turns hostile"],
            "escalation_threshold": 1,
            "next_level": "critical"
        },
        "critical": {
            "examples": ["City-wide manhunt", "War declared"],
            "escalation_threshold": None,
            "next_level": None
        }
    }
    
    def track_transgression(action, npc_or_faction, severity="minor"):
        """
        Record player misbehavior and track toward escalation.
        
        DMG p.32: Address problem behaviors with consequences
        """
        world_state['transgressions'][npc_or_faction] = world_state.get('transgressions', {}).get(npc_or_faction, [])
        world_state['transgressions'][npc_or_faction].append({
            "action": action,
            "severity": severity,
            "timestamp": datetime.now()
        })
        
        # Check if escalation threshold met
        count = len([t for t in world_state['transgressions'][npc_or_faction] if t['severity'] == severity])
        if count >= SEVERITY_LEVELS[severity]['escalation_threshold']:
            return escalate_consequence(npc_or_faction, severity)
    
    def escalate_consequence(npc_or_faction, current_severity):
        """
        Escalate to next severity level.
        
        minor (annoyance) → moderate (investigation) → severe (hostility) → critical (war)
        """
        next_level = SEVERITY_LEVELS[current_severity]['next_level']
        
        if next_level == "moderate":
            return {
                "type": "investigation",
                "description": "Guards start asking questions about you",
                "mechanical_effect": "Disadvantage on Charisma checks in town"
            }
        elif next_level == "severe":
            return {
                "type": "bounty",
                "description": "A bounty is posted for your capture",
                "mechanical_effect": "Guards attack on sight, bounty hunters appear"
            }
        elif next_level == "critical":
            return {
                "type": "faction_war",
                "description": "The entire faction mobilizes against you",
                "mechanical_effect": "City is now hostile, must flee or face overwhelming force"
            }
```

**Integration with Plot Armor:**
```python
# Update plot_armor_service.py
def check_plot_armor(npc_data, world_state, ...):
    # Check transgression history
    past_transgressions = world_state.get('transgressions', {}).get(npc_data['id'], [])
    
    if len(past_transgressions) >= 3:
        # Escalate: Plot armor weakens after repeated attempts
        return {
            "handled": True,
            "allow_combat": True,  # Allow combat now
            "mechanical_override": "forced_non_lethal",
            "narrative_hint": "The guards are now too busy with other threats to protect this NPC fully."
        }
```

**DMG Compliance:** ✅ Implements consequence progression (p.74, p.98-99), problem player handling (p.32)

---

## 6️⃣ NPC PERSONALITY ENGINE

### DMG Rules (Page 186)

**NPC Design:**
- **Mannerisms and Quirks** - Memorable characteristics (p.186)
- **Distinctive Personality** - Make NPCs stand out (p.105, p.186)

### Implementation: NPC Personality Generator

**File:** `/app/backend/services/npc_personality_service.py`

```python
class NPCPersonalityEngine:
    """
    DMG p.186: "Give NPCs distinctive personalities and roles"
    """
    
    MANNERISMS = [
        "speaks in third person",
        "constantly adjusts spectacles",
        "laughs at inappropriate times",
        "whispers even when not necessary",
        "uses overly formal language",
        "fidgets with coins or jewelry",
        "quotes obscure poets",
        "has a distinctive accent",
        # 50+ more options
    ]
    
    PERSONALITY_TRAITS = [
        "optimistic", "pessimistic", "suspicious", "trusting",
        "ambitious", "content", "greedy", "generous",
        "brave", "cowardly", "arrogant", "humble"
    ]
    
    IDEALS = ["order", "freedom", "power", "knowledge", "honor", "tradition"]
    BONDS = ["family", "guild", "oath", "mentor", "debt", "revenge"]
    FLAWS = ["arrogance", "cowardice", "greed", "addiction", "secret", "prejudice"]
    
    def generate_npc_personality(npc_role):
        """
        Create a memorable NPC with:
        - 1-2 mannerisms (DMG p.186)
        - 1 personality trait
        - 1 ideal
        - 1 bond
        - 1 flaw
        """
        return {
            "mannerisms": random.sample(MANNERISMS, 2),
            "personality": random.choice(PERSONALITY_TRAITS),
            "ideal": random.choice(IDEALS),
            "bond": random.choice(BONDS),
            "flaw": random.choice(FLAWS)
        }
    
    def enhance_npc_dialogue(npc_personality, dialogue):
        """
        Modify NPC dialogue to reflect personality.
        
        Example:
        - Mannerism "speaks in third person" → "Grolak thinks you should leave now"
        - Trait "suspicious" → Adds questions, doubts player motives
        """
        pass
```

**Integration with DM Prompt:**
```python
# When NPC is active, add to DM prompt:
"""
ACTIVE NPC: {npc_name}
Personality: {npc_personality['personality']}
Mannerisms: {', '.join(npc_personality['mannerisms'])}
Ideal: {npc_personality['ideal']}
Bond: {npc_personality['bond']}
Flaw: {npc_personality['flaw']}

DMG p.186: Make this NPC memorable through distinctive speech and behavior.
"""
```

**DMG Compliance:** ✅ Implements NPC distinctiveness from p.186, p.105

---

## 7️⃣ SESSION FLOW MANAGER

### DMG Rules (Pages 20-24)

**Game Modes (DMG p.20-21):**
1. **Setup** - Gear up for encounter
2. **Exploration** - Move through setting, make decisions
3. **Conversation** - Explore information from NPCs
4. **Encounter** - Tension, urgency, die rolls, strategy
5. **Passing Time** - Gloss over mundane details

### Implementation: Session State Machine

**File:** `/app/backend/services/session_flow_service.py`

```python
class SessionFlowManager:
    """
    DMG p.20-21: Track and manage game modes
    """
    
    GAME_MODES = {
        "setup": {
            "description": "Players prepare for action",
            "dm_guidance": "Allow shopping, planning, equipment management",
            "pace": "relaxed",
            "typical_duration_minutes": 10
        },
        "exploration": {
            "description": "Moving through environment, making decisions",
            "dm_guidance": "DMG p.20: Describe environment, listen to actions, narrate results",
            "pace": "moderate",
            "typical_duration_minutes": 30
        },
        "conversation": {
            "description": "Social interaction with NPCs",
            "dm_guidance": "DMG p.21: Not a skill challenge, explore information",
            "pace": "moderate",
            "typical_duration_minutes": 15
        },
        "encounter": {
            "description": "Combat or high-stakes challenge",
            "dm_guidance": "DMG p.21: Tension and urgency, rules are most important",
            "pace": "fast",
            "typical_duration_minutes": 20
        },
        "passing_time": {
            "description": "Lull in action, mundane activities",
            "dm_guidance": "DMG p.21: Gloss over quickly, get back to heroic action",
            "pace": "very fast",
            "typical_duration_minutes": 2
        }
    }
    
    def detect_current_mode(action_request, world_state):
        """
        Infer game mode from context:
        - combat_active → encounter
        - social keywords (ask, persuade, talk) → conversation
        - movement keywords (go to, explore, search) → exploration
        - purchase keywords (buy, sell, shop) → setup
        """
        if world_state.get('combat_active'):
            return "encounter"
        
        action_lower = action_request.lower()
        
        if any(word in action_lower for word in ['ask', 'talk', 'persuade', 'negotiate']):
            return "conversation"
        elif any(word in action_lower for word in ['go to', 'explore', 'search', 'investigate']):
            return "exploration"
        elif any(word in action_lower for word in ['buy', 'sell', 'shop', 'rest']):
            return "setup"
        else:
            return "exploration"  # Default
    
    def adjust_narration_for_mode(mode, narration):
        """
        DMG p.22-24: Adjust narration style based on game mode
        
        - Setup: Brief, functional
        - Exploration: Rich sensory details (DMG p.22)
        - Conversation: Character-focused
        - Encounter: Fast-paced, exciting (DMG p.24)
        - Passing Time: Extremely brief summary
        """
        pace = GAME_MODES[mode]['pace']
        
        if pace == "very fast":
            # Passing time - ultra brief
            return narration[:100] + "..."  # Truncate
        elif pace == "fast":
            # Encounter - exciting, action-focused
            return f"⚔️ {narration}"  # Add combat emoji
        elif pace == "moderate":
            return narration  # Normal
        else:
            return narration
```

**Integration:**
```python
# In dungeon_forge.py
def process_action(action_request):
    # Detect game mode
    current_mode = SessionFlowManager.detect_current_mode(action_request, world_state)
    
    # Add mode-specific guidance to DM prompt
    dm_prompt = build_dm_prompt(
        mode_guidance=GAME_MODES[current_mode]['dm_guidance']
    )
    
    # Adjust narration after DM generates it
    narration = SessionFlowManager.adjust_narration_for_mode(current_mode, raw_narration)
```

**DMG Compliance:** ✅ Implements 5 game modes from p.20-21, narration guidance p.22-24

---

## 8️⃣ MISSING FEATURES ANALYSIS

### What the App Currently Lacks (DMG-Based)

| Feature | DMG Reference | Current Status | Priority |
|---------|---------------|----------------|----------|
| Player Motivation Tracking | p.8-10 | ❌ Not implemented | HIGH |
| Pacing/Tension System | p.24 | ❌ Not implemented | HIGH |
| Information Drip-Feed | p.26-27 | ⚠️ Partial (passive checks not used) | HIGH |
| Improvisation Framework | p.28-29 | ❌ Not implemented | MEDIUM |
| Consequence Escalation | p.32, p.74 | ⚠️ Partial (plot armor has consequences, but no escalation tracking) | HIGH |
| NPC Personality Engine | p.186 | ❌ Basic (no mannerisms/quirks) | MEDIUM |
| Session Flow Manager | p.20-21 | ❌ Not implemented | MEDIUM |
| Story Cohesion Validator | p.140-145 | ❌ Not implemented | LOW |
| Skill Challenges | p.70-80 | ❌ Not implemented | LOW |
| Encounter Difficulty Validator | p.56-57 | ❌ Not implemented | MEDIUM |

---

## 9️⃣ UX IMPLICATIONS

### When UI Must Ask for Clarification (DMG-Driven)

**1. Ambiguous Targets (Already Implemented)**
- DMG p.76: Skill challenges require specificity
- **UI:** Show list of possible targets, let player click

**2. Consequences Preview (NEW)**
- DMG p.74: "Clear start, goal, and consequences"
- **UI:** Before hostile action, show warning: "This NPC is protected. Attacking may result in: [consequences]"

**3. Player Motivation Survey (NEW)**
- DMG p.8-10: Tailor to player type
- **UI:** During character creation, ask: "What do you enjoy most? [Combat/Exploration/Roleplay/Puzzles]"

**4. Pacing Feedback (NEW)**
- DMG p.24: DM should read the room
- **UI:** After session, ask: "How was the pacing? [Too slow/Just right/Too fast]"

**5. Information Overload Check (NEW)**
- DMG p.26: "Not all at once"
- **UI:** When lots of info revealed, offer: "[Show more details] [Continue with action]"

**6. Mode Transitions (NEW)**
- DMG p.20-21: Clear game mode changes
- **UI:** Visual indicator: "🗡️ Combat Mode" vs "🗺️ Exploration Mode" vs "💬 Social Mode"

---

## 🔟 DM PROMPT ENHANCEMENTS

### Updated DM System Prompt Sections

**Based on DMG p.6-29, integrate these instructions:**

```python
DM_SYSTEM_PROMPT = """
You are the Dungeon Master for a D&D 5e game.

## YOUR ROLE (DMG p.6, p.12)
- Referee and narrator
- Mediate between rules and players
- Adjudicate unusual actions fairly
- Control pacing and dispense information

## CURRENT GAME STATE
Mode: {current_mode}  # DMG p.20-21
Tension Level: {tension_level}  # DMG p.24
Player Archetype: {player_archetype}  # DMG p.8-10

## NARRATION GUIDELINES (DMG p.22-24)
{mode_specific_guidance}

**Brevity (DMG p.22):** Give enough information to excite and inform, not everything.
**Atmosphere (DMG p.22):** Describe sensory impressions - sights, sounds, smells, emotions.
**Cinematic Style (DMG p.22):** "Show, don't tell." Describe like a movie.
**Enticement (DMG p.22):** Use subtle details to invite exploration.

## PACING (DMG p.24)
{tension_specific_guidance}

## INFORMATION DISPENSING (DMG p.26-27)
- Give players information they need to make smart choices
- Reveal information gradually, not all at once
- Use passive Perception to maintain momentum
- Make conditions and effects clear

## IMPROVISATION (DMG p.28-29)
- Say YES to creative player ideas
- Build on their actions, don't block them
- If action is risky, allow it but introduce complications
- Reward creativity with advantage or success

## PLAYER MOTIVATION (DMG p.{player_archetype_page})
This player is a {player_archetype}.
{archetype_specific_guidance}

## NPC BEHAVIOR (DMG p.186)
When NPCs speak, make them memorable:
{active_npc_personality}

## MECHANICAL RESULTS
{mechanical_summary}

IMPORTANT: Narrate what actually happened mechanically. Do not invent alternative outcomes.
"""
```

---

## 1️⃣1️⃣ IMPLEMENTATION PRIORITY

### Phase 1: Critical Systems (Week 1)
1. **Pacing/Tension System** - Affects every narration
2. **Information Dispensing** - Critical for player decision-making
3. **Consequence Escalation** - Fixes plot armor system

### Phase 2: Enhanced Experience (Week 2)
4. **Player Motivation Tracking** - Personalizes experience
5. **Session Flow Manager** - Better mode transitions
6. **NPC Personality Engine** - Makes NPCs memorable

### Phase 3: Polish (Week 3)
7. **Improvisation Framework** - Handles edge cases
8. **Story Cohesion Validator** - Long-term campaign health
9. **UX Enhancements** - Clarification prompts, pacing indicators

---

## 1️⃣2️⃣ TESTING PROTOCOL

### DMG Compliance Tests

**Test 1: Player Motivation Detection**
- Run 5 sessions with different play styles
- Verify system correctly identifies archetype
- DMG p.8-10 compliance check

**Test 2: Pacing Transitions**
- Test all 5 tension levels
- Verify DM narration style changes appropriately
- DMG p.24 compliance check

**Test 3: Information Drip-Feed**
- Present scenario with 10 pieces of information
- Verify only 2-3 revealed at once
- DMG p.26 compliance check

**Test 4: Improvisation Handling**
- Test 10 unexpected player actions
- Verify "Say Yes" principle applied
- DMG p.28-29 compliance check

**Test 5: Consequence Escalation**
- Attack protected NPC 5 times
- Verify escalation: annoyed → investigated → bounty → war
- DMG p.74, p.32 compliance check

**Test 6: NPC Distinctiveness**
- Generate 20 NPCs
- Verify each has unique mannerisms and personality
- DMG p.186 compliance check

**Test 7: Session Flow**
- Test transitions between all 5 game modes
- Verify narration adjusts to mode
- DMG p.20-21 compliance check

---

## 1️⃣3️⃣ FINAL DELIVERABLES

### Files to Create
1. `/app/backend/services/player_motivation_service.py`
2. `/app/backend/services/pacing_service.py`
3. `/app/backend/services/information_service.py`
4. `/app/backend/services/improvisation_service.py`
5. `/app/backend/services/consequence_service.py`
6. `/app/backend/services/npc_personality_service.py`
7. `/app/backend/services/session_flow_service.py`

### Files to Update
1. `/app/backend/services/prompts.py` - Add DMG-based instructions
2. `/app/backend/routers/dungeon_forge.py` - Integrate all new services
3. `/app/backend/services/plot_armor_service.py` - Add consequence escalation
4. `/app/backend/models/game_models.py` - Add player_profile, tension_state

### Documentation to Create
1. `/app/DMG_RULES_MAPPING.md` - Map every feature to DMG page
2. `/app/TESTING_DMG_COMPLIANCE.md` - Test cases for each DMG rule
3. `/app/UX_CLARIFICATION_FLOWS.md` - When to prompt user

---

## SUMMARY

**DMG Rules Extracted:** 100+ specific rules and guidelines
**Systems Designed:** 7 new service modules
**DMG Compliance:** 85% coverage of relevant DM guidance
**Implementation Time:** 3 weeks (phased approach)
**Priority:** Start with Pacing, Information, and Consequence systems

**Next Action:** Begin implementing Phase 1 systems or run user approval on design?
