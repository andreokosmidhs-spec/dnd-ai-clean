# JARVIS Plan — dnd-ai-clean

## Game Overview
The game is a text-based implementation of Dungeons & Dragons, where players can create characters and engage in combat with monsters.

## Mechanics Inventory
### **Combat System**
- **Name**: Handles player and monster turns, damage calculation, and victory/defeat conditions.
- **File**: `combat.js:10`
- **Expected behaviour**: When a player attacks a monster, the monster's current HP is reduced by the attack's damage. If the monster's HP falls to 0 or below, it is defeated.
- **Failure modes**: Monster HP not updated correctly, incorrect damage calculation.

### **Character Creation**
- **Name**: Allows players to create characters with attributes and skills.
- **File**: `character.js:20`
- **Expected behaviour**: When a player creates a character, the character's attributes (e.g. strength, intelligence) are set to default values, and their skills are initialized as empty arrays.
- **Failure modes**: Character attributes not set correctly, skills not initialized.

### **Monster Generation**
- **Name**: Generates random monsters with attributes and HP.
- **File**: `monster.js:15`
- **Expected behaviour**: When a monster is generated, its attributes (e.g. strength, intelligence) are randomly assigned within certain ranges, and its HP is set to a value based on its attributes.
- **Failure modes**: Monster attributes not generated correctly, incorrect HP calculation.

## Test Cases
### TC-001 — Combat System
- Precondition: Player has a character with 10 HP, monster has 20 HP.
- Steps:
  1. Player attacks monster with 5 damage.
  2. Check if monster's current HP is 15.
- Expected result: Monster's current HP is 15.
- State assertion: `monster.currentHP === 15`

### TC-002 — Character Creation
- Precondition: No characters created.
- Steps:
  1. Create a character with default attributes and skills.
  2. Check if character's attributes are set correctly.
- Expected result: Character's attributes are set to default values, skills are initialized as empty arrays.
- State assertion: `character.attributes === { strength: 10, intelligence: 10 } && character.skills.length === 0`

### TC-003 — Monster Generation
- Precondition: No monsters generated.
- Steps:
  1. Generate a random monster with attributes and HP.
  2. Check if monster's attributes are within the correct ranges.
- Expected result: Monster's attributes are randomly assigned within certain ranges, HP is set correctly based on attributes.
- State assertion: `monster.attributes.strength >= 5 && monster.attributes.intelligence <= 15`

## Incomplete / Broken Code
* `combat.js:25`: Incorrect damage calculation formula, causing inconsistent results.

## Cannot Test
None. All mechanics have a browser entry point.
