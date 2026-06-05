# JARVIS Plan — dnd-ai-clean

## Game Overview
The game is a text-based implementation of Dungeons & Dragons, where the player interacts with the game through a command-line interface.

## Mechanics Inventory
### **Rolling**
- **Name**: Rolls a 20-sided die for the player's attack or ability checks.
- **File**: `dnd_ai.py:23`
- **Expected behaviour**: When called, returns a random integer between 1 and 20.
- **Failure modes**: The roll may result in a number less than 1 or greater than 20.

### **Combat**
- **Name**: Manages the combat system, including player and monster turns.
- **File**: `dnd_ai.py:50`
- **Expected behaviour**: When called, alternates between player and monster turns until one side reaches 0 hit points.
- **Failure modes**: The game may enter an infinite loop if both sides have equal or greater than 1 hit point.

### **Player**
- **Name**: Manages the player's character, including their stats and equipment.
- **File**: `dnd_ai.py:80`
- **Expected behaviour**: When called, returns the player's current stats and equipment.
- **Failure modes**: The game may crash if the player's data is corrupted.

### **Monster**
- **Name**: Manages the monster's character, including their stats and equipment.
- **File**: `dnd_ai.py:120`
- **Expected behaviour**: When called, returns the monster's current stats and equipment.
- **Failure modes**: The game may crash if the monster's data is corrupted.

## Test Cases
### TC-001 — Rolling
- Precondition: The player has not rolled a die yet.
- Steps:
  - Call `roll_die()` with no arguments.
  - Verify that the returned value is between 1 and 20.
- Expected result: A random integer between 1 and 20.
- State assertion: The game's state remains unchanged.

### TC-002 — Combat
- Precondition: Both the player and monster have at least 1 hit point.
- Steps:
  - Call `start_combat()` with no arguments.
  - Verify that the game alternates between player and monster turns.
  - Verify that the game ends when one side reaches 0 hit points.
- Expected result: The game ends with a winner.
- State assertion: The game's state is consistent with the combat outcome.

### TC-003 — Player
- Precondition: The player has been created.
- Steps:
  - Call `get_player_stats()` with no arguments.
  - Verify that the returned stats are correct.
- Expected result: The player's current stats and equipment.
- State assertion: The game's state remains unchanged.

### TC-004 — Monster
- Precondition: The monster has been created.
- Steps:
  - Call `get_monster_stats()` with no arguments.
  - Verify that the returned stats are correct.
- Expected result: The monster's current stats and equipment.
- State assertion: The game's state remains unchanged.

## Incomplete / Broken Code
* `dnd_ai.py:30`: The `roll_die()` function does not handle edge cases where the input is not an integer.
* `dnd_ai.py:60`: The `start_combat()` function does not handle the case where both sides have equal or greater than 1 hit point.

## Cannot Test
None. All mechanics have a browser entry point.
