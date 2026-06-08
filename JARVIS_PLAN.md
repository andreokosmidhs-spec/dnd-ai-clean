Here is the complete JARVIS_PLAN.md:

# JARVIS Plan —

## Table of Contents

* [Overview](#overview)
* [Core Features](#core-features)
	+ [Knowledge Deck](#knowledge-deck)
	+ [Target Mode](#target-mode)
	+ [Search Target Modal](#search-target-modal)
	+ [Remember Card Dialog](#remember-card-dialog)
	+ [Target Mode Banner](#target-mode-banner)
* [Technical Requirements](#technical-requirements)
* [Implementation Roadmap](#implementation-roadmap)

## Overview

JARVIS (Just Another Roleplaying Interface for Storytelling) is a web-based platform designed to enhance the tabletop role-playing game experience. It aims to provide a seamless and immersive environment for players and Dungeon Masters (DMs) to collaborate, share knowledge, and create engaging stories.

## Core Features

### Knowledge Deck

* A digital repository of world-building information, character backstories, and other relevant details.
* Players can contribute to the deck by adding new entries or editing existing ones.
* DMs can access and manage the deck to keep track of game lore and settings.

### Target Mode

* A feature that allows players to focus on specific aspects of the game world during exploration.
* When in target mode, players can click on words in the DM's narration to inspect them, revealing additional information about the environment, NPCs, or objects.
* The target mode banner provides a visual indicator and affordance for players to cancel this feature.

### Search Target Modal

* A modal window that appears when a player clicks on a word while in search mode.
* It prompts the player to enter what they are looking for, allowing them to specify their investigation goals.
* The DM can then receive this information and respond accordingly.

### Remember Card Dialog

* A dialog box that allows players to save important beats or events from the game session.
* Players can add a title, type (e.g., event, NPC, location), and description for each entry.
* Saved entries are stored in the Knowledge Deck and can be accessed by both players and DMs.

### Target Mode Banner

* A small floating banner that appears at the top of the chat surface when target mode is active.
* It displays a visual indicator and provides an affordance to cancel target mode.

## Technical Requirements

* Frontend: Build using React, with a focus on accessibility and responsive design.
* Backend: Utilize a Node.js server with a database (e.g., MongoDB) for storing game data and user interactions.
* APIs: Establish RESTful APIs for communication between the frontend and backend components.
* Security: Implement authentication and authorization mechanisms to ensure secure access to game data.

## Implementation Roadmap

1. **Week 1-2:** Design and implement the Knowledge Deck feature, including user interface and database schema.
2. **Week 3-4:** Develop Target Mode functionality, including word inspection and search target modal.
3. **Week 5-6:** Implement Remember Card Dialog and integrate it with the Knowledge Deck.
4. **Week 7-8:** Complete Target Mode Banner feature and refine overall user experience.
5. **Week 9-10:** Conduct thorough testing and debugging of all features.
6. **Week 11:** Launch JARVIS platform and gather feedback from users.

Note: This roadmap is a rough estimate and may be adjusted based on the team's progress and any unforeseen challenges that arise during development.

## 4. Test Cases

### TC-001 — Character Creation
- Precondition: User is on the landing page and has not created a character yet.
- Steps: 
  1. Click on the "Create Character" button.
  2. Fill out the character creation form with valid input.
  3. Submit the form.
- Expected result: The user sees their newly created character's profile panel.
- Assertion: VISUAL_CHECK: Verify that the character's name, class, and level are displayed correctly on the profile panel.

### TC-002 — Character Selection
- Precondition: User has multiple characters in their account.
- Steps:
  1. Click on the "Characters" tab in the top navigation menu.
  2. Select a character from the list of available characters.
  3. Click on the "View" button next to the selected character.
- Expected result: The user sees the selected character's profile panel with their stats and equipment.
- Assertion: VISUAL_CHECK: Verify that the character's name, class, level, and equipment are displayed correctly on the profile panel.

### TC-003 — Combat Round
- Precondition: User is in a combat scenario with an enemy NPC.
- Steps:
  1. Click on the "Initiate Combat" button to start the combat round.
  2. Select an action (e.g., attack, cast spell) from the available options.
  3. Confirm the action by clicking the "Confirm" button.
- Expected result: The user sees the outcome of their action, including any damage dealt or effects applied.
- Assertion: VISUAL_CHECK: Verify that the combat log displays the correct outcome of the user's action.

### TC-004 — Inventory Management
- Precondition: User has items in their inventory.
- Steps:
  1. Click on the "Inventory" tab in the top navigation menu.
  2. Select an item from the list of available items.
  3. Click on the "Use" button next to the selected item.
- Expected result: The user sees the effects of using the item, including any changes to their stats or equipment.
- Assertion: VISUAL_CHECK: Verify that the inventory displays the correct quantity and effects of the used item.

### TC-005 — Save/Load
- Precondition: User has saved a game session previously.
- Steps:
  1. Click on the "Save" button to save the current game session.
  2. Close the browser or navigate away from the page.
  3. Return to the page and click on the "Load" button.
- Expected result: The user sees their saved game session loaded, including any progress made since saving.
- Assertion: VISUAL_CHECK: Verify that the game state is restored correctly, including character stats and inventory.

### TC-006 — AI Behavior
- Precondition: User has enabled AI behavior for an NPC in the combat scenario.
- Steps:
  1. Click on the "Initiate Combat" button to start the combat round.
  2. Observe the AI-controlled NPC's actions, including any attacks or spells cast.
  3. Verify that the NPC's behavior is consistent with its programmed AI script.
- Expected result: The user sees the AI-controlled NPC behaving as intended, including any scripted behaviors or patterns.
- Assertion: VISUAL_CHECK: Verify that the NPC's actions are consistent with its AI script and do not deviate from expected behavior.
