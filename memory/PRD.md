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
- **Feature**: AI-generated character portraits via Gemini Nano Banana (`gemini-3.1-flash-image-preview`)
  - New backend module: `backend/api/character_portrait.py` builds a prompt from identity/race/class/appearance and calls `emergentintegrations` with `EMERGENT_LLM_KEY`.
  - New endpoint: `POST /api/characters/v2/{id}/generate-portrait` (plus alias under `/api/v2/characters/*`). Returns `{portraitDataUrl}` and persists it to the character document.
  - Added `portraitDataUrl: Optional[str]` to `CharacterV2Base` model.
  - Frontend: `ReviewStep.jsx` kicks off portrait generation in the background after character creation (fire-and-forget). `CharacterSidebar.jsx` renders the portrait (or a "generating..." placeholder). `RPGGame.jsx` bridge polls every 5s (up to 30s) if the portrait isn't ready at campaign load.
- **Feature**: Role Play panel now populates from D&D data
  - `RPGGame.jsx` bridge now enriches the character with `traits` (from `raceData`), `ideals / bonds / flaws_detailed` (from `backgroundData.personality`), and `aspiration` (from `background.feature`). Picks are seeded deterministically by character ID so each character keeps a consistent persona.
- **Bug Fix (P0)**: Duplicate ability scores in sidebar/sheet/InfoDrawer
  - The bridge emits both `STR/DEX/…` and `strength/dexterity/…` for cross-component compatibility. The three iterators now whitelist only the 6 canonical uppercase keys.
- **Bug Fix (P0)**: CloudFront 403 during character creation submit
  - `ReviewStep.jsx` fetch now uses `${REACT_APP_BACKEND_URL}/api/characters/v2/create` instead of a relative path that hit the frontend CDN.
- **Bug Fix (P0)**: Ability scores defaulting to 10 in-game
  - Bridge reads `characterData.abilityScores` (camelCase) with lowercase keys (`str/dex/con/int/wis/cha`) instead of the non-existent `characterData.abilities.STR`.
- **Verification**: Full curl round-trip — character creation + portrait generation (~16s) + GET returns persisted 1.1MB data URL.

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
