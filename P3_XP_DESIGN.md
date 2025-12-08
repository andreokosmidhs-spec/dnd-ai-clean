# P3 XP & Level Design

## Goals

- **Fast early levels** → player feels growth quickly
- **No insane grind** → 1–2 sessions can see level 3–4
- **Simple enough** to implement without refactoring the whole system
- **Works with existing** enemy archetypes and combat pacing

---

## Scope

**Levels 1 → 5** (can expand later, but 1–5 is perfect for vertical slice)

---

## XP to Level Table

| Level | XP to Next | Total XP to Reach |
|-------|------------|-------------------|
| 1     | 100        | 0 → 100           |
| 2     | 250        | 100 → 350         |
| 3     | 450        | 350 → 800         |
| 4     | 700        | 800 → 1500        |
| 5     | –          | Soft cap for now  |

### Progression Pace

- **Lvl 1 → 2:** 100 XP (~2–3 medium encounters)
- **Lvl 2 → 3:** 250 XP (~6–8 encounters total)
- **Lvl 3 → 4:** 450 XP (~14–16 encounters total)

Assuming mixed combat + exploration XP, this feels rewarding but not trivial.

### Code Implementation

```python
xp_to_next = {
  1: 100,
  2: 250,
  3: 450,
  4: 700
}
```

---

## XP Rewards Per Action

### 1. Combat XP (Per Enemy)

Use existing enemy archetypes and assign base XP:

| Enemy Type | Examples | XP |
|------------|----------|-----|
| **Trash / Minor** | Weak Beast, Low-level Cultist | 20 XP |
| **Standard Enemy** | Bandit, Guard, Smuggler, Wolf | 35 XP |
| **Elite Enemy** | Guard Captain, Zealot, Undead Champion | 60 XP |
| **Mini-Boss** | Named quest enemy | 100 XP |
| **Boss** | Major arc / dungeon boss | 150–200 XP |

**Typical 2-enemy fight:**
- 2 × 35 XP = 70 XP → almost a full chunk of Lvl 1–2
- Elite + minions fights scale nicely without being absurd

### 2. Non-Combat XP

**Must reward non-violence** or the game funnels players into murderhobo mode.

| Success Type | XP | Examples |
|--------------|-----|----------|
| **Minor success** | 10 XP | Bribe a guard, get info |
| **Moderate success** | 20 XP | Sneak into restricted area |
| **Major narrative beat** | 40–60 XP | Quest objective, key clue |

**Can be attached to:**
- Successful ability checks (when flagged "important")
- Quest objectives (when P3 quests are implemented)

---

## Level-Up Effects

Keep it minimal and robust for now:

**At each level-up:**

1. `level += 1`
2. **Increase Max HP:**
   - `+6 HP` flat per level (simple, independent of class)
3. **Heal player:**
   - Set `current_hp = max_hp` on level-up (full heal)
4. **(Optional P3) Small offensive buff:**
   - At Level 3 and Level 5: `attack_bonus += 1`

### Required Character Sheet Fields

```python
{
  "level": int,
  "current_xp": int,
  "xp_to_next": int,
  "max_hp": int,
  "current_hp": int,
  "attack_bonus": int  # or incorporated into existing attack fields
}
```

---

## Balance Targets

### Combat Pacing
- **Level 1-3:** 2-4 hits to kill standard enemy
- **Level 4-6:** 3-5 hits to kill standard enemy
- **Level 7+:** 4-6 hits to kill standard enemy

### XP Distribution
- **~70% from combat** (encourages engagement)
- **~30% from exploration/quests** (rewards creativity)

### Level-Up Frequency
- **Level 2:** After 2-3 combats (quick win, player feels power)
- **Level 3:** After 6-8 total encounters (still fast)
- **Level 4:** After 14-16 encounters (slows down, but still achievable)
- **Level 5:** Soft cap (end of P3 scope)

---

## Implementation Notes

### XP Application Flow
```python
async def apply_xp_gain(character: CharacterState, xp_gain: int):
    character.current_xp += xp_gain
    
    level_ups = []
    while character.current_xp >= character.xp_to_next and character.level < 5:
        character.current_xp -= character.xp_to_next
        character.level += 1
        character.max_hp += 6
        character.current_hp = character.max_hp  # Full heal
        character.xp_to_next = get_xp_to_next(character.level)
        level_ups.append(character.level)
        
        # Optional: attack bonus at levels 3 and 5
        if character.level in [3, 5]:
            character.attack_bonus += 1
    
    return character, level_ups
```

### Enemy XP Assignment
```python
ENEMY_XP_TABLE = {
    "minor": 20,
    "standard": 35,
    "elite": 60,
    "mini_boss": 100,
    "boss": 150
}

def get_combat_xp(defeated_enemies: List[Enemy]) -> int:
    total_xp = 0
    for enemy in defeated_enemies:
        tier = get_enemy_tier(enemy)  # based on archetype
        total_xp += ENEMY_XP_TABLE[tier]
    return total_xp
```

---

## Testing Benchmarks

### Session 1 (2-3 hours play)
- **Expected:** 4-6 combat encounters + 2-3 social encounters
- **XP gain:** ~200-300 XP
- **Result:** Reach level 2, maybe close to level 3

### Session 2 (2-3 hours play)
- **Expected:** 6-8 more encounters
- **XP gain:** ~250-350 XP
- **Result:** Reach level 3, working toward level 4

### Session 3 (2-3 hours play)
- **Expected:** 8-10 encounters
- **XP gain:** ~400-500 XP
- **Result:** Reach level 4, maybe level 5

**Total to Level 5:** 3-4 play sessions (~8-12 hours)

This feels achievable for solo play without being a grind.

---

## Future Expansion (Post-P3)

- **Levels 6-10:** Double the XP requirements, add more meaningful perks
- **Class-specific bonuses:** Fighter gets +2 HP/level instead of +6 flat
- **Feat system:** Every 3 levels, choose a small perk
- **Multiclassing:** Way out of scope for now
