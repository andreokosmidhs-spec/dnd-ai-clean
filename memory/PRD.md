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

### 2026-04-22 (later)
- **Feature: Personality hooks (Ideal / Bond / Flaw) now persisted and drive the DM.**
  - `CharacterV2` schema extended: `BackgroundInfo` now carries a `Personality { ideal, bond, flaw }` block + `toolChoices`. Frontend `buildCharacterPayload` sends them; Pydantic persists them round-trip.
  - Both the campaign intro prompt and the Lean DM system prompt inject the Ideal/Bond/Flaw with explicit instructions to weave them in subtly (never quote verbatim) — using them to color reactions, create friction via the flaw, or give NPCs leverage via the bond.
  - Verified with a Soldier Paladin (bond: "failed my squad once — never again"; flaw: "little respect for anyone who is not a proven warrior"): the AI intro wove the silver bracer into "a constant reminder of your oaths and the blunder that left your squad vulnerable," and the next DM turn opened with "Despite your instinct to dismiss the boy…" — organic personality-driven narration.

### 2026-04-22 (continued)
- **Feature: "Remember this" button on DM messages** — players can promote any DM narration beat into a pinned Knowledge Card so the DM keeps referencing it:
  - New endpoint `POST /api/campaigns/{id}/log/cards/remember` (title auto-derived from first sentence, type default `event`, tagged `remembered`).
  - Button added to every DM message in `AdventureLogWithDM.jsx` (Bookmark icon, flips to BookmarkCheck after save, spinner while saving, disabled when no campaign).
  - **Collection mismatch fixed**: Lean DM was reading from `campaign_log_cards` while cards were being written to `campaign_cards` — remembered cards now reach the DM prompt. Verified: after remembering a fence named Kethra at the Iron Gull, the very next DM turn wove Kethra and the Iron Gull into the narration organically.

### 2026-04-22
- **Feature**: AI prompt overhaul for both the campaign intro (`services/campaign_service.py::build_starting_scene_with_ai`) and the Lean DM system prompt (`routers/lean_dm.py::_build_system_prompt`):
  - Personalizes by hero name, race, class, background, appearance cues; honors class flavor (rogue = shadows/sightlines, wizard = cerebral, etc.).
  - Bans common clichés (tavern, "chill runs down your spine", "destiny awaits", "mysterious stranger", "ye olde", etc.).
  - Requires ≥1 concrete sensory detail; matches campaign tone; uses starting location by name.
  - Mandatory ending: 2–3 tangible actionable choices OR one sharp pressing question — no more vague "adventure begins" closers.
- **Fix**: Top-bar UI showing "Unknown Realm / Unknown Town". `build_world_blueprint` now emits `world_core` (e.g., "Realm of Exploration") and `starting_town` (matches `startingLocation.name`), and the `WorldBlueprint` Pydantic model allows them through. No frontend change needed — `WorldInfoPanel` now has real names to render.
- Verified via curl: intro and DM narrations reference hero by name, honor class flavor, and end with concrete choices.

### 2026-04-21
- **Feature**: Lean DM endpoint (`POST /api/campaigns/{campaign_id}/dm/action`)
  - New module: `backend/routers/lean_dm.py`. Uses emergentintegrations + gpt-4o-mini. Pulls context from the campaign (world, intent), V2 character (`characters_v2`), and active knowledge cards (`campaign_log_cards`). Session id = `{campaign_id}:{character_id}`, last 10 messages persisted in new `campaign_messages` collection for multi-turn memory.
  - Response shape compatible with `AdventureLogWithDM` (`{success, data:{narration, options, entity_mentions, world_state_update, player_updates}}`).
  - `AdventureLogWithDM.jsx` now uses the lean endpoint whenever a `campaignId` is in scope; falls back to legacy `/api/rpg_dm/action` otherwise.
  - Verified: ~3s latency for ~170-word cinematic narration; second turn correctly references entities from turn 1 (multi-turn memory works).
- **Fix**: Adventure Log intro now visible
  - The bridge in `RPGGame.jsx` writes the AI-generated intro into `localStorage[dm-log-messages-{sessionId}]` (which `AdventureLogWithDM` reads) and sets `dm-intro-played=1` to bypass the legacy auto-intro path.
- **Feature**: Cinematic AI-generated campaign intro narration (`services/campaign_service.py::build_starting_scene_with_ai`, via emergentintegrations + gpt-4o-mini). New `GET /api/campaigns/{id}` endpoint.
- **Feature**: AI-generated character portraits via Gemini Nano Banana. Portrait 192×192 in sidebar. Self-healing generation + polling in the bridge.
- **Feature**: Role Play panel populated from D&D data (race traits, background ideals/bonds/flaws, deterministic seed per character).
- **Fix (DM character 404, now superseded)**: `dungeon_forge.py` auto-mirrors V2 characters into legacy `characters` collection. Still useful as a safety net for the legacy path; the new V2 flow goes through the lean DM.
- **Fix**: Duplicate ability scores whitelisted to 6 canonical keys.
- **Fix**: CloudFront 403 on character creation (full backend URL).
- **Fix**: Ability scores defaulting to 10 in-game (bridge now reads `abilityScores` camelCase with lowercase keys).

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
