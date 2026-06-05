# JARVIS Plan — DND-AI-Clean

## Game Overview
The game is a text-based implementation of Dungeons & Dragons, where the player interacts with a monster using a command-line interface.

## Mechanics Inventory

### **Monster Combat**
- **Name**: Engage in combat with a monster.
- **File**: `monster.js:10`
- **Expected behaviour**: When the player attacks the monster, the monster's current HP should decrease by 1. The game state should be updated to reflect this change.
- **Failure modes**: If the player's attack roll is less than or equal to the monster's AC, the attack should miss and no damage should be dealt.

### **Player Turn**
- **Name**: Take a turn in combat with the monster.
- **File**: `player.js:20`
- **Expected behaviour**: When the player takes their turn, they should be prompted to enter an action (e.g. "attack", "heal"). The game state should be updated based on the player's input.
- **Failure modes**: If the player enters an invalid action, the game should display an error message and prompt the player to try again.

### **Monster Turn**
- **Name**: Take a turn in combat with the monster.
- **File**: `monster.js:30`
- **Expected behaviour**: When it's the monster's turn, it should attack the player. The player's current HP should decrease by 1 if the attack hits.
- **Failure modes**: If the monster misses its attack, no damage should be dealt to the player.

## Test Cases

### TC-001 — Monster Combat
- Precondition: Player and monster are in combat.
- Steps:
  1. Player attacks the monster with a roll of 10.
  2. Verify that the monster's current HP has decreased by 1.
- Expected result: Monster's current HP is 9.
- State assertion: `window.gameState?.monster?.hp === 9`

### TC-002 — Player Turn
- Precondition: Player and monster are in combat, player's turn.
- Steps:
  1. Player enters an action of "attack".
  2. Verify that the game state has been updated to reflect the player's attack.
- Expected result: Game state reflects player's attack.
- State assertion: `window.gameState?.player?.action === 'attack'`

### TC-003 — Monster Turn
- Precondition: Player and monster are in combat, monster's turn.
- Steps:
  1. Verify that the monster attacks the player with a roll of 10.
  2. Verify that the player's current HP has decreased by 1 if the attack hits.
- Expected result: Player's current HP is 9 if the attack hits.
- State assertion: `window.gameState?.player?.hp === 9`

## Incomplete / Broken Code

* `monster.js:40`: The monster's AI logic is incomplete and does not handle all possible scenarios.

## Cannot Test
None. All mechanics have a browser entry point.
