# P3 Roadmap: Progression, Stakes, and Quests

## Theme
You've got moment-to-moment gameplay. Now you need:
- **Progression** (XP, levels, loot)
- **Stakes** (what happens when you lose)
- **Direction** (quests so it's not just wandering)

---

## P3.1 – Progression Skeleton

### Objective
Add basic XP/level system with meaningful progression.

### Backend Changes

**Update CharacterState model:**
```python
class CharacterState(BaseModel):
    # ... existing fields ...
    level: int = 1
    current_xp: int = 0
    xp_to_next: int = 100  # Dynamic based on level
```

**XP Award Rules:**
- Each enemy archetype → fixed XP value
  - Bandit/Thug: 25 XP
  - Guard/Criminal: 35 XP
  - Cultist/Undead: 40 XP
  - Boss/Special: 75 XP
- Exploration/social successes → 10-20 XP (optional)

**Level Up Logic:**
```python
def calculate_xp_for_level(level: int) -> int:
    return 100 * level  # Simple: level 1→2 needs 100, 2→3 needs 200, etc.

def level_up(character_state: dict) -> dict:
    character_state["level"] += 1
    character_state["current_xp"] = 0
    character_state["xp_to_next"] = calculate_xp_for_level(character_state["level"])
    character_state["max_hp"] += 5  # +5 HP per level
    if character_state["level"] % 4 == 0:
        character_state["proficiency_bonus"] += 1  # Every 4 levels
    return character_state
```

**Integration:**
- Combat Engine → returns `xp_gained` in combat result
- WORLD MUTATOR → updates character XP and handles level up
- `/api/rpg_dm/action` response includes `xp_gained` and `level_up: bool`

### Frontend Changes

**Add XP bar to UI:**
- Show in CharacterSidebar or CombatHUD
- Display: `Level 3 | XP: 150/300`
- Progress bar visualization

**Level up notification:**
- Show modal or toast when level increases
- Display stat changes (+5 HP, +1 proficiency, etc.)

---

## P3.2 – Basic Quest System

### Objective
Give players direction through simple, world-aware quests.

### Backend Changes

**Add quests to world_state:**
```python
{
  "quests": [
    {
      "quest_id": "string (uuid)",
      "name": "string",
      "status": "active | completed | failed",
      "giver_npc_id": "string",  # Must be from world_blueprint.key_npcs
      "location_id": "string",   # Must be from world_blueprint.points_of_interest
      "summary": "string",
      "objectives": [
        {
          "type": "kill",
          "target": "cultist",
          "count": 3,
          "progress": 0
        },
        {
          "type": "go_to",
          "location_id": "poi_shrine"
        },
        {
          "type": "talk_to",
          "npc_id": "npc_elder"
        }
      ],
      "rewards": {
        "xp": 100,
        "items": [],
        "flags": ["shrine_cleared"]
      }
    }
  ]
}
```

**Quest Rules (CRITICAL):**
- DUNGEON FORGE can only create quests using **existing** NPCs, POIs, factions from blueprint
- No inventing new gods/empires/locations
- Quest objectives must be verifiable from world_state changes

**Quest Lifecycle:**
1. **Quest Offer:** NPC offers quest in dialogue
2. **Quest Accept:** Player accepts, quest added to `world_state.quests` as "active"
3. **Quest Progress:** WORLD MUTATOR updates objective progress based on actions
4. **Quest Complete:** When all objectives met, status → "completed", rewards granted

**Integration:**
- DUNGEON FORGE checks active quests and references them in narration
- WORLD MUTATOR updates quest progress after each action
- Quest completion triggers XP/item rewards

### Frontend Changes

**Quest Log UI:**
- New panel: `QuestLog.jsx`
- Shows:
  - Active quests (name, summary, objectives with progress)
  - Completed quests (collapsible history)
- Access via sidebar tab or hotkey

**Quest markers:**
- Show `[Quest]` indicator next to relevant options
- Highlight NPCs/locations related to active quests

---

## P3.3 – Death Handling & Consequences

### Objective
Add meaningful stakes for combat defeat without full roguelike permadeath.

### Backend Changes

**When player HP ≤ 0 in combat:**
```python
def handle_player_defeat(character_state, world_state, location):
    # Mark defeat
    combat_state["outcome"] = "player_defeated"
    
    # Options for recovery:
    options = [
        "Wake up at the last safe location (lose progress)",
        "Accept a permanent scar (HP debuff, keep progress)",
        "Call for divine intervention (quest added, keep progress)"
    ]
    
    return {
        "narration": "Darkness closes in... but your story isn't over yet.",
        "options": options,
        "defeated": True
    }

def apply_defeat_consequence(choice: str, character_state, world_state):
    if "safe location" in choice:
        # Teleport to starting town
        world_state["current_location"] = starting_town
        # No stat loss
    elif "scar" in choice:
        # Add permanent debuff
        character_state["max_hp"] -= 5
        character_state["conditions"].append("scarred")
        # Keep location
    elif "divine intervention" in choice:
        # Add quest: "Repay the debt"
        # Keep everything but owe a favor
    
    # Always restore HP to 1/4 max
    character_state["hp"] = character_state["max_hp"] // 4
```

### Frontend Changes

**Defeat modal:**
- Show dramatic "Defeated" screen
- Present consequence choices
- Dim/blur background for impact

**Persistent consequences:**
- Show scars/debuffs in character sheet
- Remind player of divine debts in quest log

**Rules:**
- No permadeath (for now)
- Always a way forward
- Consequences feel meaningful but not punishing

---

## P3.4 – Enemy Scaling

### Objective
Keep combat challenging as player levels up.

### Backend Changes

**Simple scaling formula:**
```python
def scale_enemy_for_level(base_enemy: dict, character_level: int) -> dict:
    # Scale HP
    enemy["hp"] = base_enemy["hp"] + (character_level - 1) * 3
    enemy["max_hp"] = enemy["hp"]
    
    # Scale attack bonus
    enemy["attack_bonus"] = base_enemy["attack_bonus"] + (character_level - 1) // 2
    
    # Scale damage (add +1 per 3 levels)
    level_bonus = (character_level - 1) // 3
    if level_bonus > 0:
        # Convert "1d6" to "1d6+2" etc.
        enemy["damage_die"] = f"{base_enemy['damage_die']}+{level_bonus}"
    
    # Keep archetype identity (name, AC mostly unchanged)
    return enemy
```

**Integration:**
- Enemy sourcing service calls scaling before returning enemies
- Scaling is transparent to player (just tougher enemies)

**Balance targets:**
- Level 1-3: 2-4 hits to kill enemy
- Level 4-6: 3-5 hits to kill enemy
- Level 7+: 4-6 hits to kill enemy

---

## P3.5 – Lore Checker Upgrade (Optional)

### Objective
Add semantic validation without breaking deterministic layer.

### Backend Changes

**Two-tier validation:**
```python
def check_lore_consistency(narration, blueprint, state, auto_correct=False, semantic_check=False):
    # Tier 1: Deterministic (always runs)
    result = deterministic_check(narration, blueprint, state)
    
    # Tier 2: LLM semantic check (optional, feature flag)
    if semantic_check and result["valid"]:
        semantic_result = llm_semantic_check(narration, blueprint)
        if not semantic_result["valid"]:
            result["issues"].extend(semantic_result["issues"])
            result["semantic_risk"] = True
    
    return result
```

**LLM semantic check:**
- Only for major events (quest completion, important NPCs)
- Never auto-corrects, just flags "semantic risk"
- Examples caught:
  - "The desert is lush and green" (contradiction)
  - "You meet the king of [faction without monarchs]"
  - Timeline inconsistencies

**Integration:**
- Feature flag in world_state: `semantic_validation_enabled: bool`
- Default OFF for performance
- Player can toggle in settings

---

## Implementation Order

**Phase 1 (P3.1 + P3.2):**
1. Add XP/level system
2. Add quest structure
3. Wire both into existing pipeline

**Phase 2 (P3.3):**
4. Death handling
5. Consequence system

**Phase 3 (P3.4 + P3.5):**
6. Enemy scaling
7. (Optional) Semantic lore checker

---

## Success Metrics

After P3:
- [ ] Players gain XP and level up
- [ ] Leveling feels meaningful (+HP, +proficiency)
- [ ] Quests provide direction
- [ ] Quest objectives track correctly
- [ ] Death has consequences but isn't punishing
- [ ] Enemies scale with player level
- [ ] Combat remains challenging at all levels

---

## What NOT to Include

- ❌ Full D&D spell system (too complex)
- ❌ Multi-classing (scope creep)
- ❌ Crafting system (different phase)
- ❌ Multiplayer / co-op (way out of scope)
- ❌ Full loot tables (simple quest rewards only)
- ❌ Permadeath (harsh for solo play)

Keep scope tight. P3 is about **progression, stakes, and direction** - not feature bloat.
