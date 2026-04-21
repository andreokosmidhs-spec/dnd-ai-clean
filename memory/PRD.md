# RPG Forge - Product Requirements Document

## Overview
RPG Forge is an AI-powered text RPG adventure application that allows users to create D&D-style characters and embark on AI-generated campaigns.

## Tech Stack
- **Frontend**: React (CRA + Craco), TailwindCSS, Zustand, react-router-dom
- **Backend**: FastAPI, Pydantic
- **Database**: MongoDB
- **AI**: OpenAI via emergentintegrations library

## Core Features

### ✅ Completed Features

#### Character Creation V2 (7-Step Wizard)
- Step 1: Identity (name, sex, age, appearance expression)
- Step 2: Race selection
- Step 3: Class selection with skill proficiencies
- Step 4: Ability Scores (standard array, point buy, or roll)
- Step 5: Background selection
- Step 6: Appearance customization
- Step 7: Review and confirm

#### Campaign Generation Flow
- Campaign draft creation with intent settings (tone, focus, scope, danger)
- AI-powered world generation via OpenAI
- Knowledge cards system (MTG-style card deck UI)
- Session bridge connecting Zustand store with legacy game engine

#### Campaign Log UI (MTG-Style)
- Filterable card grid with categories (Character, Location, Faction, Lore, Quest, Rumor)
- Card details drawer with pin functionality
- Responsive design with loading/empty states

### 🔄 In Progress
- None currently

### 📋 Backlog (Future Tasks)
- P1: Character Portrait upload/selection (AppearanceStep)
- P2: Load/Edit Character functionality
- P2: Auto-calculate Hit Points based on class & Constitution
- P3: Refactor RPGGame.jsx to consume useSessionCore directly (remove dual state system)

## Key API Endpoints
- `POST /api/characters/v2/create` - Create new character
- `GET /api/v2/characters/{id}` - Get character by ID
- `POST /api/campaigns/draft` - Create campaign draft
- `POST /api/campaigns/{id}/generate-world` - Generate AI world
- `GET /api/campaigns/{id}/log/cards` - Get knowledge cards

## Architecture Notes
- **State Management**: Hybrid system with Zustand (`useSessionCore`) and legacy useState in RPGGame.jsx
- **Session Bridge**: Critical `useEffect` in RPGGame.jsx syncs modern Zustand store with legacy game engine
- **Environment**: Backend requires `OPENAI_API_KEY` for campaign generation

## Changelog

### 2026-04-21
- **Feature**: Cinematic AI-generated campaign intro narration (`services/campaign_service.py::build_starting_scene_with_ai`)
  - Uses `emergentintegrations` + `gpt-4o-mini`. Produces a 110-160 word second-person opening tuned to tone/focus/scope/danger + character details. Persisted to `campaign.starting_scene.introText`.
  - New endpoint: `GET /api/campaigns/{campaignId}` returns the campaign doc (including `starting_scene`).
  - `RPGGame.jsx` bridge fetches the campaign and uses the intro as the first Adventure Log entry. Falls back to a template intro if AI generation fails.
- **Feature**: AI-generated character portraits via Gemini Nano Banana
  - Backend: `backend/api/character_portrait.py`; endpoint `POST /api/characters/v2/{id}/generate-portrait` (+ alias).
  - Frontend: fired from `ReviewStep.jsx` after character creation; the bridge self-heals by retrying + polling if not ready. Portrait displayed at 192x192 in `CharacterSidebar.jsx`.
- **Feature**: Role Play panel populates from D&D data
  - `RPGGame.jsx` bridge enriches character with traits (race), ideals/bonds/flaws (background), and aspiration (background feature); seeded deterministically by character id.
- **Bug Fix (partial)**: DM `Character not found` 404
  - `dungeon_forge.py::get_character_doc` auto-mirrors V2 characters into the legacy `characters` collection on demand. Unblocks character-lookup but DM actions still fail on `world_states` lookup (see Known Issues).
- **Bug Fix (P0)**: Duplicate ability scores in sidebar/sheet/InfoDrawer (iterators now whitelist 6 canonical keys)
- **Bug Fix (P0)**: CloudFront 403 on character creation (relative fetch → full backend URL)
- **Bug Fix (P0)**: Ability scores defaulting to 10 in-game (bridge now reads `abilityScores` camelCase)

## Known Issues
- **DM actions fail with `World state not found`** — the `dungeon_forge` DM pipeline requires `world_states` + richly-structured `world_blueprint` that the new V2 → `campaigns.py` flow does not produce. Requires architectural work to bridge the two subsystems (or retire `dungeon_forge.py` and build a leaner DM on top of `campaigns.py` + knowledge cards).

### 2026-01-17
- **Bug Fix**: Fixed campaign generation flow returning to main menu
  - Root cause: `...characterData` spread in session bridge was overwriting extracted string values
  - Fix: Moved spread to beginning of object so extracted values take precedence
- **Verification**: Full end-to-end testing passed (100% backend, 100% frontend)

### Previous Session
- Implemented MTG-style Campaign Log UI
- Added Card Details Drawer with pin functionality
- Refactored CampaignLogPanel into smaller components
- Created session bridge in RPGGame.jsx
- Configured backend with OPENAI_API_KEY and emergentintegrations

## Files of Reference
- `frontend/src/components/RPGGame.jsx` - Main game component with session bridge
- `frontend/src/store/useSessionCore.js` - Zustand session store
- `frontend/src/pages/CampaignGenerate.jsx` - Campaign generation page
- `frontend/src/components/CampaignLogPanel.jsx` - Knowledge deck UI
- `backend/server.py` - FastAPI backend
- `backend/.env` - Contains OPENAI_API_KEY
