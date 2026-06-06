# JARVIS Plan — dnd-ai-clean

## Game Overview
The game is a text-based implementation of Dungeons & Dragons, where the player inputs commands to navigate and interact with the game world.

## Mechanics Inventory
### **Combat System**
- **Name**: Handles combat logic between the player and monsters.
- **File**: `game.js:23`
- **Expected behaviour**: When the player attacks a monster, the monster's HP should decrease by the player's attack value. If the monster's HP reaches 0, it should be defeated.
- **Failure modes**:
	+ Monster's HP does not decrease when attacked.
	+ Defeated monster still exists in the game world.

### **Player Movement**
- **Name**: Handles player movement between rooms.
- **File**: `game.js:42`
- **Expected behaviour**: When the player inputs a direction command (e.g., "north"), they should move to the adjacent room.
- **Failure modes**:
	+ Player does not move when inputting valid direction commands.
	+ Player gets stuck in an infinite loop of movement.

### **Item Management**
- **Name**: Handles item pickup, use, and inventory management.
- **File**: `game.js:67`
- **Expected behaviour**: When the player picks up an item, it should be added to their inventory. When they use an item, its effects should be applied.
- **Failure modes**:
	+ Item is not picked up when inputting valid pickup commands.
	+ Used item does not apply its intended effect.

## Test Cases
### TC-001 — Combat System
- Precondition: Player has a monster in combat range.
- Steps:
	1. Input "attack" command to attack the monster.
	2. Verify that the monster's HP decreases by the player's attack value.
- Expected result: Monster's HP decreases by the player's attack value.
- State assertion: `window.gameState.monster.hp` should decrease by the player's attack value.

### TC-002 — Player Movement
- Precondition: Player is in a room with adjacent rooms.
- Steps:
	1. Input "north" command to move north.
	2. Verify that the player has moved to the adjacent room.
- Expected result: Player has moved to the adjacent room.
- State assertion: `window.gameState.player.room` should change to the adjacent room's ID.

### TC-003 — Item Management
- Precondition: Player is in a room with items.
- Steps:
	1. Input "pick up" command to pick up an item.
	2. Verify that the item has been added to the player's inventory.
- Expected result: Item has been added to the player's inventory.
- State assertion: `window.gameState.player.inventory` should contain the picked-up item.

## Incomplete / Broken Code
* `game.js:120`: The combat logic for monsters with multiple attacks is not implemented correctly, causing them to deal inconsistent damage.
* `game.js:150`: The item use logic has a bug that causes items to be used incorrectly when their effects are applied.

## Cannot Test
* **Monster AI**: There is no browser entry point for testing monster AI behavior.
