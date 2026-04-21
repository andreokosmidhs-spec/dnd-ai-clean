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
- **Bug Fix (P0)**: CloudFront 403 during character creation submit
  - Root cause: `ReviewStep.jsx` used a relative `fetch("/api/characters/v2/create")`. The CRA `"proxy"` in `package.json` only works in dev. In the deployed preview, the relative POST hit the frontend CloudFront distribution (GET/HEAD only) → 403.
  - Fix: Prefix with `${process.env.REACT_APP_BACKEND_URL}` in `ReviewStep.jsx` (line 109).
- **Bug Fix (P0)**: Ability scores showing as default 10s in the in-game UI
  - Root cause: Session-core bridge in `RPGGame.jsx` read `characterData.abilities.STR`, but the backend returns `abilityScores` (camelCase) with lowercase keys (`str/dex/con/int/wis/cha`). Additionally, UI components (`CharacterSheet`, `CharacterSidebar`, `InfoDrawer`, `Inventory`, `LevelUpScreen`) read full lowercase names (`strength/dexterity/...`).
  - Fix: Bridge now reads `characterData.abilityScores` with lowercase keys and emits `character.stats` with BOTH short uppercase keys (STR/DEX/...) AND full lowercase names (strength/dexterity/...).
- **Verification**: Backend round-trip via curl confirms `{str:15,dex:14,con:13,int:12,wis:10,cha:8}` persists correctly. Endpoint returns 422 schema validation (not 403) when called from full URL.

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
