Here is the complete JARVIS_PLAN.md:

# JARVIS Plan —

## Overview

JARVIS (Just Another Roleplaying Interface for Storytelling) is a web-based platform designed to facilitate collaborative storytelling and role-playing games. The goal of this project is to create an immersive, interactive environment that enables players to engage with each other and the game world in a more engaging and dynamic way.

## Features

### Core Features

1. **Character Management**: Players can create and manage their characters, including attributes, skills, and equipment.
2. **Storytelling Interface**: A user-friendly interface for creating and managing storylines, including character interactions, plot twists, and world-building elements.
3. **Real-time Collaboration**: Multiple players can collaborate on the same storyline in real-time, using a shared workspace to discuss and plan their actions.
4. **Dynamic World-Building**: The game world is dynamic and responsive, with NPCs (non-player characters) that react to player actions and decisions.

### Advanced Features

1. **Target Mode**: A special mode that allows players to focus on specific words or phrases in the narrative, providing additional context and information.
2. **Search Target Modal**: A modal window that appears when a player selects a word or phrase in target mode, allowing them to search for related information.
3. **Remember Card Dialog**: A dialog box that enables players to save important information about their characters, NPCs, or the game world.

### Technical Requirements

1. **Frontend Framework**: Use a modern frontend framework (e.g., React) to build the user interface and manage state changes.
2. **Backend API**: Develop a RESTful API using a suitable programming language (e.g., Node.js) to handle data storage, retrieval, and manipulation.
3. **Database Management**: Design a database schema to store game data, including character information, storylines, and world-building elements.

### User Experience

1. **User-Friendly Interface**: Ensure that the interface is intuitive and easy to use, with clear instructions and minimal cognitive load.
2. **Real-Time Feedback**: Provide immediate feedback to players on their actions and decisions, using visual cues and notifications.
3. **Customization Options**: Offer customization options for players to personalize their experience, including character appearance and abilities.

### Development Roadmap

1. **Phase 1: Core Features** (Weeks 1-4)
	* Develop the core features of JARVIS, including character management and storytelling interface.
2. **Phase 2: Advanced Features** (Weeks 5-8)
	* Implement target mode, search target modal, and remember card dialog.
3. **Phase 3: Technical Requirements** (Weeks 9-12)
	* Develop the frontend framework, backend API, and database management system.

### Team Structure

1. **Project Lead**: Oversee the development process, ensure timely completion of milestones, and make key decisions.
2. **Frontend Developer**: Focus on building the user interface and managing state changes using a modern frontend framework.
3. **Backend Developer**: Develop the RESTful API and database management system using a suitable programming language.
4. **UX/UI Designer**: Design the user experience, create wireframes and prototypes, and ensure that the interface is intuitive and easy to use.

### Timeline

* Week 1-4: Core features development
* Week 5-8: Advanced feature implementation
* Week 9-12: Technical requirements development
* Week 13-16: Testing and debugging
* Week 17-20: Launch preparation and deployment

## 4. Test Cases

### TC-001 — Onboarding / Initial Navigation
- Precondition: Browser opens the game URL (landing page visible)
- Steps:
  1. Click the primary CTA button (e.g. 'Play Free', 'Start', 'Enter')
  2. Click 'Next' or 'Continue' through any wizard/tutorial steps
  3. Dismiss any welcome modals
- Expected result: Main game UI is visible (not the landing/marketing page)
- Assertion: VISUAL_CHECK: Main game interface is shown, not a marketing page

### TC-002 — Character Creation
- Precondition: User has completed TC-001 (inside the game)
- Steps:
  1. Navigate to the character creation page
  2. Fill out the required fields for character creation
  3. Submit the character creation form
- Expected result: Character sheet is visible with created character's details
- Assertion: VISUAL_CHECK: Character sheet displays correct character information

### TC-003 — Campaign Setup
- Precondition: User has completed TC-002 (character created)
- Steps:
  1. Navigate to the campaign setup page
  2. Fill out the required fields for campaign setup
  3. Submit the campaign setup form
- Expected result: Campaign details are visible and character is assigned to campaign
- Assertion: VISUAL_CHECK: Campaign details display correct information, character is listed in campaign

### TC-004 — RPG Game Interface
- Precondition: User has completed TC-003 (campaign set up)
- Steps:
  1. Navigate to the RPG game interface page
  2. Verify that all necessary components are visible (e.g. character sheet, map, controls)
  3. Interact with the game interface to ensure it functions as expected
- Expected result: Game interface is fully functional and displays correct information
- Assertion: VISUAL_CHECK: All necessary components are visible and interactive

### TC-005 — Error Handling
- Precondition: User has completed TC-004 (game interface accessible)
- Steps:
  1. Intentionally trigger an error in the game (e.g. invalid input, network failure)
  2. Verify that the error is properly handled and displayed to the user
- Expected result: Error message is visible and provides clear instructions for resolution
- Assertion: VISUAL_CHECK: Error message is displayed with correct information

### TC-006 — Toast Notifications
- Precondition: User has completed TC-005 (error handling tested)
- Steps:
  1. Trigger a toast notification to be displayed (e.g. successful action, warning)
  2. Verify that the toast notification is properly displayed and dismissible
- Expected result: Toast notification is visible with correct information and can be dismissed
- Assertion: VISUAL_CHECK: Toast notification displays correct information and can be closed
