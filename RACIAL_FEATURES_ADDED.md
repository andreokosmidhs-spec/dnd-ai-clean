# Racial Features Implementation

## What Was Added

Complete D&D 5e racial features including:
- ✅ Ability Score Improvements (ASI)
- ✅ Racial traits with mechanical effects
- ✅ Race variants (subraces)
- ✅ Speed, size, darkvision, and special abilities
- ✅ Helper functions for subrace handling

---

## Races Implemented

### 1. **Human**
- **ASI:** +1 to ALL ability scores
- **Speed:** 30 ft
- **Languages:** Common + 1 choice
- **Traits:** Versatile (adaptability)

---

### 2. **Elf** (3 subraces)
**Base Race:**
- **ASI:** +2 DEX
- **Speed:** 30 ft
- **Languages:** Common, Elvish
- **Traits:** Darkvision (60 ft), Keen Senses (Perception proficiency), Fey Ancestry (advantage vs charm), Trance (4-hour rest)

**Subraces:**

#### High Elf
- **Additional ASI:** +1 INT
- **Traits:** 
  - Elf Weapon Training (longsword, shortsword, shortbow, longbow)
  - Cantrip (1 wizard cantrip)
  - Extra Language (+1 choice)

#### Wood Elf
- **Additional ASI:** +1 WIS
- **Speed:** 35 ft (faster!)
- **Traits:**
  - Elf Weapon Training
  - Fleet of Foot (35 ft speed)
  - Mask of the Wild (hide in light natural cover)

#### Dark Elf (Drow)
- **Additional ASI:** +1 CHA
- **Traits:**
  - Superior Darkvision (120 ft)
  - Sunlight Sensitivity (disadvantage in sunlight)
  - Drow Magic (Dancing Lights, Faerie Fire at 3rd, Darkness at 5th)
  - Drow Weapon Training (rapier, shortsword, hand crossbow)

---

### 3. **Dwarf** (2 subraces)
**Base Race:**
- **ASI:** +2 CON
- **Speed:** 25 ft
- **Languages:** Common, Dwarvish
- **Traits:** 
  - Darkvision (60 ft)
  - Dwarven Resilience (advantage vs poison, resistance to poison damage)
  - Dwarven Combat Training (battleaxe, handaxe, light hammer, warhammer)
  - Tool Proficiency (1 artisan's tool: smith's, brewer's, or mason's)
  - Stonecunning (expertise on History for stonework)

**Subraces:**

#### Hill Dwarf
- **Additional ASI:** +1 WIS
- **Traits:**
  - Dwarven Toughness (+1 HP per level)

#### Mountain Dwarf
- **Additional ASI:** +2 STR (total +2 CON, +2 STR!)
- **Traits:**
  - Dwarven Armor Training (light and medium armor proficiency)

---

### 4. **Halfling** (2 subraces)
**Base Race:**
- **ASI:** +2 DEX
- **Speed:** 25 ft
- **Size:** Small
- **Languages:** Common, Halfling
- **Traits:**
  - Lucky (reroll natural 1s)
  - Brave (advantage vs frightened)
  - Halfling Nimbleness (move through larger creatures' spaces)

**Subraces:**

#### Lightfoot Halfling
- **Additional ASI:** +1 CHA
- **Traits:**
  - Naturally Stealthy (hide behind larger creatures)

#### Stout Halfling
- **Additional ASI:** +1 CON
- **Traits:**
  - Stout Resilience (advantage vs poison, resistance to poison damage)

---

### 5. **Dragonborn**
- **ASI:** +2 STR, +1 CHA
- **Speed:** 30 ft
- **Languages:** Common, Draconic
- **Traits:**
  - Draconic Ancestry (choose dragon type)
  - Breath Weapon (15 ft cone or 30 ft line, 2d6 damage, 1/rest)
  - Damage Resistance (matches breath weapon element)

---

### 6. **Gnome** (2 subraces)
**Base Race:**
- **ASI:** +2 INT
- **Speed:** 25 ft
- **Size:** Small
- **Languages:** Common, Gnomish
- **Traits:**
  - Darkvision (60 ft)
  - Gnome Cunning (advantage on INT/WIS/CHA saves vs magic)

**Subraces:**

#### Forest Gnome
- **Additional ASI:** +1 DEX
- **Traits:**
  - Natural Illusionist (Minor Illusion cantrip)
  - Speak with Small Beasts

#### Rock Gnome
- **Additional ASI:** +1 CON
- **Traits:**
  - Artificer's Lore (expertise on History for magic/tech items)
  - Tinker (tinker's tools proficiency, craft clockwork devices)

---

### 7. **Half-Elf**
- **ASI:** +2 CHA, +1 to TWO abilities of your choice
- **Speed:** 30 ft
- **Languages:** Common, Elvish + 1 choice
- **Traits:**
  - Darkvision (60 ft)
  - Fey Ancestry (advantage vs charm, immune to magical sleep)
  - Skill Versatility (proficiency in 2 skills of your choice)

---

### 8. **Half-Orc**
- **ASI:** +2 STR, +1 CON
- **Speed:** 30 ft
- **Languages:** Common, Orc
- **Traits:**
  - Darkvision (60 ft)
  - Menacing (Intimidation proficiency)
  - Relentless Endurance (drop to 1 HP instead of 0, 1/long rest)
  - Savage Attacks (extra damage die on critical hits)

---

### 9. **Tiefling**
- **ASI:** +2 CHA, +1 INT
- **Speed:** 30 ft
- **Languages:** Common, Infernal
- **Traits:**
  - Darkvision (60 ft)
  - Hellish Resistance (fire damage resistance)
  - Infernal Legacy (Thaumaturgy, Hellish Rebuke at 3rd, Darkness at 5th)

---

## New Helper Functions

### In `/app/frontend/src/data/raceData.js`:

```javascript
// Check if race has subraces
hasSubraces(raceName)

// Get list of subraces for a race
getSubraces(raceName)  // Returns ["High Elf", "Wood Elf", "Dark Elf (Drow)"]

// Get subrace data
getSubraceData(raceName, subraceName)

// Get combined race + subrace data
getCombinedRaceData(raceName, subraceName)

// Calculate total ASI from race + subrace
calculateRacialASI(raceName, subraceName)
```

### In `/app/frontend/src/utils/raceHelpers.js`:

```javascript
// Updated to support subraces
applyRaceToCharacter(raceName, character, subraceName = null)

// Re-exported for convenience
hasSubraces(raceName)
getSubraces(raceName)
```

---

## How to Use in Character Creation

### Example: Creating a High Elf

```javascript
import { applyRaceToCharacter, hasSubraces, getSubraces } from '../utils/raceHelpers';

// Check if race has subraces
if (hasSubraces("Elf")) {
  const subraces = getSubraces("Elf");
  // Show subrace selection UI: ["High Elf", "Wood Elf", "Dark Elf (Drow)"]
}

// Apply race and subrace
const updatedCharacter = applyRaceToCharacter("Elf", character, "High Elf");

// Result:
// - Base stats: +2 DEX (from Elf), +1 INT (from High Elf)
// - Speed: 30 ft
// - Traits: Darkvision, Keen Senses, Fey Ancestry, Trance,
//           Elf Weapon Training, Cantrip, Extra Language
```

---

## Integration Checklist

To fully integrate subrace selection into character creation:

### Step 1: Add Subrace Selection UI
In `CharacterCreation.jsx`, after race selection:

```jsx
{/* Show subrace dropdown if race has subraces */}
{character.race && hasSubraces(character.race) && (
  <div>
    <Label>Subrace</Label>
    <Select 
      value={character.subrace || ""} 
      onValueChange={(subrace) => {
        const updated = applyRaceToCharacter(character.race, character, subrace);
        setCharacter(updated);
      }}
    >
      <SelectTrigger>
        <SelectValue placeholder="Choose subrace..." />
      </SelectTrigger>
      <SelectContent>
        {getSubraces(character.race).map(subrace => (
          <SelectItem key={subrace} value={subrace}>
            {subrace}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  </div>
)}
```

### Step 2: Update Race Change Handler
```javascript
const updateCharacterRace = (selectedRace) => {
  // Reset subrace when race changes
  setCharacter(prev => applyRaceToCharacter(selectedRace, { ...prev, subrace: null }));
};
```

### Step 3: Display Racial Traits
Show all traits (base + subrace) in the character sheet:

```jsx
{character.racial_traits && character.racial_traits.map((trait, index) => (
  <div key={index}>
    <strong>{trait.name}:</strong> {trait.summary}
    <p className="text-sm">{trait.mechanical_effect}</p>
  </div>
))}
```

---

## ASI Examples

### Mountain Dwarf (Best for Fighters)
```
+2 CON (base) + +2 STR (subrace) = +2 CON, +2 STR
Great for melee fighters!
```

### High Elf (Best for Wizards)
```
+2 DEX (base) + +1 INT (subrace) = +2 DEX, +1 INT
Plus wizard cantrip for extra magic!
```

### Half-Elf (Most Flexible)
```
+2 CHA + +1 to TWO abilities of your choice
Perfect for Paladins, Bards, Sorcerers, Warlocks
```

---

## Mechanical Advantages by Subrace

### Best for Combat:
- **Mountain Dwarf:** +2 STR, +2 CON, armor proficiency
- **Half-Orc:** +2 STR, +1 CON, Relentless Endurance, Savage Attacks
- **Dragonborn:** +2 STR, +1 CHA, Breath Weapon

### Best for Stealth:
- **Wood Elf:** +2 DEX, +1 WIS, 35 ft speed, Mask of the Wild
- **Lightfoot Halfling:** +2 DEX, +1 CHA, Naturally Stealthy
- **Dark Elf (Drow):** +2 DEX, +1 CHA, Superior Darkvision (but sunlight sensitivity)

### Best for Magic:
- **High Elf:** +2 DEX, +1 INT, wizard cantrip
- **Tiefling:** +2 CHA, +1 INT, Infernal Legacy spells
- **Rock Gnome:** +2 INT, +1 CON, Artificer's Lore

### Best for Social:
- **Half-Elf:** +2 CHA, +2 flexible, Skill Versatility
- **Tiefling:** +2 CHA, +1 INT, Infernal Legacy
- **Lightfoot Halfling:** +2 DEX, +1 CHA

---

## Testing

To test the racial features:

1. **Create a character with each race**
2. **Check ASI is applied correctly:**
   - Base stats + racial bonuses = final stats
   - Subraces add additional bonuses
3. **Verify traits appear in character sheet**
4. **Test subrace selection UI:**
   - Dropdown only shows for races with subraces
   - Changing subrace updates traits and ASI
5. **Confirm special features:**
   - Wood Elf gets 35 ft speed
   - Mountain Dwarf gets +2 STR (not +1)
   - Half-Elf gets flexible +1s

---

## Files Modified

1. `/app/frontend/src/data/raceData.js` - Added subraces and helper functions
2. `/app/frontend/src/utils/raceHelpers.js` - Updated to support subraces

---

## Next Steps

**To complete the integration:**
1. Add subrace selection UI to `CharacterCreation.jsx`
2. Update character creation flow to save subrace to database
3. Display all racial traits in character sheet
4. Test with backend character creation API

The data structure and helper functions are ready to use!
