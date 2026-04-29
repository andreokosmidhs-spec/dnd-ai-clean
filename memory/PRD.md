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

### 2026-04-29 (AC mechanical accuracy + chronicler auto-narration scaffold)
- **Feature: Armor Class is now derived per D&D 5e rules** instead of being hardcoded to `10 + DEX mod`.
  - **New `/app/frontend/src/utils/ac.js`** with `computeArmorClass(character)`:
    - Maps the V2 character's chosen starting equipment pack (`class.equipment.pack` → `CLASS_EQUIPMENT[class].packA|B`) to actual armor pieces.
    - Applies armor table (Padded/Leather = 11+full DEX, Studded = 12+full DEX, Hide/Chain Shirt/Scale/Breastplate = +DEX cap 2, Half Plate = 15+DEX cap 2, Ring/Chain Mail/Splint/Plate = heavy no DEX).
    - Adds `+2` for shields (`Shield` and `Wooden Shield`).
    - Honors **class Unarmored Defense**: Barbarian = `10 + DEX + CON` (shield allowed), Monk = `10 + DEX + WIS` (no armor, no shield).
    - Returns `{ ac, breakdown }` so the UI can show a tooltip ("Chain Mail + shield").
  - Wired into `RPGGame.jsx` bridge — sets `character.armorClass` + `character.acBreakdown` once on character load.
  - `CharacterSidebar.jsx` reads `character.armorClass` first and falls back to `computeArmorClass()` when absent.
  - `CharacterPreview.jsx` now also renders an AC line (with breakdown) next to Max HP.
  - Verified live: Fighter (Chain Mail + Shield) shows **AC 18** (was incorrectly 12). 7-case unit test (`/app/frontend/src/utils/__tests__/ac.test.js`) passes for Fighter, Cleric, Wizard, Barbarian, Monk, Druid pack combinations.
- **Scaffold: World-Brief auto-narration** — added a per-session, per-mount auto-trigger in `AdventureLogWithDM.jsx` that calls `generateSpeech(text, 'onyx', true)` on the chronicler card the first time a campaign opens, gated by `isTTSEnabled` and a `dm-world-brief-played-{sessionId}` flag. **Currently dormant** because the backend's `/api/tts/generate` endpoint requires `OPENAI_TTS_KEY` (the Emergent universal key doesn't cover OpenAI TTS). When the user supplies a key the chronicler will narrate itself on every campaign open.

### 2026-04-29 (legacy campaign backfill — P0 blocker fix)
- **Fix: Loading older V2 campaigns generated before the macro/micro intro split crashed/looked broken** (Unknown Realm/Town panel, missing chronicler card, missing or generic intro).
  - DB audit revealed three tiers of legacy docs: 100 missing `world.world_brief`, 58 missing `world_core` + `starting_town`, 4 missing the entire `world` block (very-old V1 schema with `world_blueprint`).
  - **New: `_backfill_legacy_campaign(campaign)` in `routers/campaigns.py`** runs transparently on every `GET /api/campaigns/{campaignId}`:
    1. Resolves a usable `intent` (defaults to Balanced/Story/Mixed/Medium for very-old docs with `intent: None`).
    2. Migrates legacy `world_blueprint` → `world` if `world` is missing entirely.
    3. Backfills missing `world_core` / `starting_town` / `startingLocation` via `build_world_blueprint(intent, character)`.
    4. Backfills missing `world.setting` via the deterministic `_template_world_setting` helper (factions / events / current tension).
    5. Backfills missing `world.world_brief` via `generate_world_brief_with_ai` (which has its own template fallback if the LLM is unavailable). Runs only once — result is persisted.
    6. Backfills missing `starting_scene` via `build_starting_scene` and propagates `worldBrief` onto it.
  - **Persists upgrades** via `_save_campaign_doc` so subsequent loads are instant (no LLM re-call).
  - Verified end-to-end: a legacy `040ae069…` campaign now loads in 0.2s on re-fetch and renders "Realm of Story / Town Square" + AI-generated chronicler preface ("Nestled between the jagged peaks of the Craggestone Mountains and the fertile expanse of the Larkfield Valley…") + personal arrival + abilities/HP/AC/personality. Three tiers (no-world, partial-world, missing-brief) all upgrade cleanly.

### 2026-04-29 (macro/micro intro split)
- **Major: Campaign opens with TWO distinct narration messages — macro chronicle, then micro arrival.**
  - **Macro Chronicle** (`generate_world_brief_with_ai`) — third-person omniscient chronicler's preface (130-180 words) covering, in order: GEOGRAPHY (where the realm sits, terrain, neighbors), RECENT HISTORY (compressed cause-and-effect from the setting's recent_events), POLITICAL CLIMATE (powers and balance, with factions named), CULTURE (one specific custom or texture). Ends with a single transitional sentence tilting the camera toward the starting location ("And it is to Gate of Emberfall, on this evening, that our story turns").
  - **Micro Arrival** (`build_starting_scene_with_ai` refocused) — Mercer-style two-beat opening but now beat ONE is character-specific: WHY this hero is in this place, derived from BACKGROUND, RACE, and PERSONALITY HOOKS (a soldier summoned by whispers; an entertainer touring; an outlander drawn by a market rumor). Beat TWO is the static scene + the active opening lead.
  - Backend: `world.world_brief` persisted on the campaign + `starting_scene.worldBrief` returned alongside `introText` from `/generate-world`.
  - Frontend: `RPGGame.jsx` bridge seeds TWO Adventure Log entries on intro — chronicler first (with `isWorldBrief: true`, `chronicleTitle: "A Chronicle of {realm}"`), personal arrival second (`isCinematic: true`).
  - `AdventureLogWithDM` renders the chronicler card distinctively: amber/stone gradient background with double border, BookOpen icon, italic serif body text (vs. the violet cinematic styling of the personal arrival).
  - **Verified live (Vael Brynn the Soldier Paladin in Political-Intrigue Emberfall):** macro covered the civil war, Ironstead/Dorrin Vale geography, three named factions, curfew + crimson banners; micro opened with *"Vael Brynn the Steady stands at the edge of a narrow alley behind the Iron Fist inn, summoned by whispers of a councilor gone missing"* — soldier-summoned arrival, lead planted, three observable things at end.

### 2026-04-29 (review submit auto-retry)
- **Fix: Transient 404 / 5xx during character-creation submit no longer surfaces as a hard error.**
  - Submit handler now runs a full failover pass (primary endpoint → alias) and, if BOTH fail with 404 / 5xx / network, **automatically waits 1.2s and runs the entire pass again** before showing an error. Catches backend-restart windows, brief proxy hiccups, transient network glitches.
  - Per-request 12-second timeout via `AbortController` so a hung request can't block the UX.
  - 400 / 422 (real validation errors) still skip retry — retrying won't change them.
  - Updated friendly message to mention the retry happened ("...even after a retry. Wait 10s and click Retry.") so users know it wasn't a fluke.
- Verified both endpoints are 200 OK in production. Most likely cause of the user's original error was hitting the submit during a backend supervisor restart from the previous turn.

### 2026-04-27 (world setting)
- **Major: Real world-setting context now generated and threaded through the entire narrative pipeline.**
  - **New service**: `generate_world_setting_with_ai(intent, world, character)` produces a structured setting bible per campaign — `era`, 3 named **factions** (with `domain` + `stance` and in active conflict), 2 **recent events** (with `title` + `summary`), and a concrete `current_tension` describing what the streets actually feel like right now. Tone-adapted: Gritty → post-war scarcity / corruption; Heroic → rising orders / bandit threats; Mystery → secret guilds. Has a coherent template fallback if the LLM is unavailable.
  - **Persisted on `world.setting`** so it loads back on every session — the DM uses it on every turn, not just the intro.
  - **Setting auto-seeded as Knowledge Cards** (faction + event + tension types) so factions and history surface in the player's deck and feed into the DM prompt automatically.
  - **Mercer two-beat opening** — intro prompt now requires:
    1. Beat ONE (1-2 sentences): grounds the player in the world's situation, naming a faction or recent event or evoking the current tension as a felt fact on the streets.
    2. Beat TWO (3-4 sentences): zooms into the static scene with concrete sensory details and plants the active opening lead.
  - **Lean DM** prompt now has a SETTING block (era + factions + recent events + current tension) injected after the location, so every turn references factions/history naturally.
  - **WorldInfoPanel** upgraded: new "The Age" (era), "What the Streets Feel Like" (current tension), "Factions in Play" (with domain + stance), and "Recent History" (events with summaries) sections — players can see the world they're in.
  - `RPGGame.jsx` bridge passes `setting` through to the panel.
  - **Verified live**: Gritty/Political-Intrigue campaign generated *Silver Council / Thorns of the Night / Ember Watch*, *Market Scandal*, *Disappearance of the Tax Barge*, *grain riots & curfew*. Intro opened with *"The streets bear the weight of recent turmoil…after the Market Scandal laid bare the council's greed."* Heroic/Wilderness produced completely different setting (Trail Wardens vs Cartographers Guild, bandit attacks); DM weaved them into NPC dialogue on turn 1.

### 2026-04-27 (Load Latest Campaign fix)
- **Fix: "Load Last Campaign from DB" button was wired to a legacy `dungeon_forge` endpoint that scans the OLD `characters` collection, while V2 data lives in `characters_v2`. Net effect: button always returned 404 ("No campaigns with characters found") even with 94 V2 campaigns in the DB.**
  - New endpoint **`GET /api/campaigns/v2/latest`** in `routers/campaigns.py` that finds the most-recently-updated V2 campaign whose character still exists in `characters_v2`. Returns `{campaign_id, character_id, status, updated_at, character_name}`.
  - Rewrote `handleLoadLastCampaign` in `MainMenu.jsx`: calls the new endpoint, seeds `useSessionCore` (`activeCharacterId`, `activeCampaignId`, `campaignStatus`), navigates to `/game`. From there the existing bridge does all the heavy lifting (intro, world, HP, personality, quest log) — no special "loaded campaign" code path needed.
  - Re-labeled button to **"Load Latest Campaign"** + added `data-testid`.
  - Verified: endpoint returns the Paladin campaign cleanly; click → adventure screen with full state restored.

### 2026-04-23 (Mercer style overhaul)
- **Major: Intro + Lean DM prompts rewritten in Matthew Mercer's narration style.**
  - Both system prompts now explicitly invoke "the tradition of Matthew Mercer (Critical Role)" and codify his hallmarks as 9 strict rules:
    1. **Static scene** — the hero is observing, the world happens AROUND them. Never auto-narrate "you scan / step / reach / decide / turn".
    2. Never override perception or judgment ("you wonder", "you know", "in the back of your mind" — banned).
    3. **One simile maximum** per reply (zero preferred). No "like X, like Y" chains.
    4. **NPCs as silhouettes/voices/postures** — "the hooded figure at the well", "a man's frantic voice" — names emerge naturally, never invented.
    5. Time, light, weather carry mood (no adjective stacks).
    6. Tone-matched prose — gritty = short sentences + cold details; heroic = open vistas, no saccharine; mystery = emphasize what's OUT of place.
    7. No dice/DC/check language.
    8. Appearance only via physical sensation, reflection, gear, or NPC reaction (never described from outside).
    9. Expanded hard-ban list: "swirl like autumn leaves", "like fingers across", "gleam and promise fortune", "What better place...?", and previous emotion-as-abstraction phrases.
  - **Endings hand agency back, Mercer-style**: state 2-3 concrete observable facts unique to THIS scene + "What do you do?" — schematic example so the model never reuses sample text. Verified across 3 fresh intros: each ended with a different set of facts tied to its unique opening lead (pier/sailors; royal envelope; altar/journal).
  - **Length tightened**: intro 90-140 words (was 110-160), DM turn 70-130 (was 80-160) — Mercer is concise, not verbose.

### 2026-04-23 (review resilience)
- **Fix: "404 page not found" in Review Step — defensive layer added.**
  - Proactive **backend-reachability ping** on Review mount. If the GET probe fails, an amber warning banner appears at the top of the Review step (with `data-testid="review-backend-unreachable-banner"`) telling the user to hard-refresh BEFORE they waste a click.
  - **Endpoint failover**: submit now tries `/api/characters/v2/create`, and on 404 falls back to the alias `/api/v2/characters/create`. Both routes share the same handler, so if one path is blocked by a stale cache or proxy rule the other still succeeds.
  - Cleaner error parser (JSON → `detail`; HTML → tag-stripped; network error → "Couldn't reach the backend").
  - Verified alias accepts the full wizard payload (including new personality + toolChoices fields).

### 2026-04-23 (review error handling)
- **Fix: Raw "404 page not found" HTML leaking into the Review Step error box.** `ReviewStep.jsx` was calling `await res.text()` and throwing the body verbatim, which exposed upstream HTML 404 pages (e.g. stale preview URL / proxy misses) as-is to the user. New parser:
  - Detects content-type: JSON → pull `detail`; HTML/text → strip tags and cap at 180 chars.
  - Status-specific friendly messages (404 suggests hard refresh + shows the target URL; 400/422 quote validation detail; 5xx suggests retry).
  - New red alert box with **Retry** and **Dismiss** buttons + `data-testid` tags, clean layout, role=alert.
- Verified that FastAPI 404s (JSON `{detail:"Not Found"}`) and proxy HTML 404s both render cleanly now.

### 2026-04-23 (scene reports)
- **Feature: "Report this scene" — one-click dev snapshot on DM messages.**
  - Backend:
    - `POST /api/campaigns/:id/scene-reports` — stores a rich snapshot in `db.scene_reports`: the reported DM text, the player's prior action (auto-detected from message history), user note, quick-reason tags (pov-leak, cliche, ignores-context, personality-miss, quest-off, wrong-location, stalling, other), plus full context: character snapshot, active/closed quests, up to 20 knowledge cards, campaign intent, world.
    - `GET /api/campaigns/:id/scene-reports?limit=N` — list newest first for later review/debugging.
  - Frontend:
    - New `SceneReportDialog.jsx` — clickable quick-reason badges, 500-char free-text note, beat + prior-action previews.
    - Red 🚩 Flag button next to Remember/Pin-as-quest on every DM message in `AdventureLogWithDM.jsx`. Once reported, button turns rose and disables.
  - **Verified end-to-end**: submitted a report referencing a fabricated POV-leak beat → Mongo persisted 1 doc in `dnd_ai_db.scene_reports` with full context (character name/class, 1 active quest, 3 knowledge cards, selected tags). `GET` returns it correctly.

### 2026-04-23 (direct fixes from user screenshot)
- **Fix: "Unknown Realm / Unknown Town" on the adventure top bar.** The bridge in `RPGGame.jsx` was hardcoding `starting_town: { name: 'Starting Area' }` and never consumed the campaign's real world data. Now reads `world` from the existing `GET /api/campaigns/:id` fetch and threads `world_core` (e.g., "Realm of Mystery") + `starting_town` (e.g., "Gate of Emberfall") into `setWorldBlueprint`.
- **Fix: Blank "Hit Points /" in the Health sidebar.** `CharacterSidebar` reads `character.hitPoints` (flat int) in three places; the bridge set only `hp` / `maxHp`. Added `hitPoints: computedMaxHp` to `baseCharacter` so both Quick Stats and the Health card render correctly.
- **Fix: False "✦ chosen" badge on placeholder personality values.** Hardened `playerChosen` check: now requires a non-empty, trimmed string (`typeof 'string' && v.trim().length > 0`). Empty-but-present fields from old schemas no longer pass.
- **Prompt hardening: expanded POV ban list.** Added "feels personal", "pulls at you", "pulls at your heart", "tugs at your heart", "weighs on your soul", "stirs something deep within", "a weight settles on your chest" — all emotion-as-abstraction tics the user spotted in live intros. Verified 5/5 fresh intros scan clean.

### 2026-04-23 (remember dialog)
- **Feature: Inline edit of a Remembered card's title/type before saving.**
  - New `RememberCardDialog.jsx`: clean shadcn Dialog with auto-derived title (first sentence, 60-char cap, editable), a type Select (event / npc / place / item / lore / belief), a live preview of the beat text, and a character counter.
  - `AdventureLogWithDM` now opens this dialog when the player clicks 🔖 Remember; the POST only fires on **Save to deck**, with the player's chosen title + type.
  - Backend `/remember` endpoint already accepted `title` and `type` — verified round-trip persists both ("Smith trusts me — 3rd stall" / type="npc").
  - Cancel leaves the beat un-pinned and re-enables the bookmark button.

### 2026-04-23 (quest connection — Tier D)
- **Feature: Quest Log fully wired to V2 — "Pin as quest" + live status management.**
  - Backend:
    - `KnowledgeCard.status` field added (`active` | `completed` | `failed`).
    - `GET /api/campaigns/:id/quests` — returns quest-type cards adapted to the UI shape (opening leads first, then active, then closed).
    - `POST /api/campaigns/:id/quests/:questId/status` — mark a quest active/completed/failed.
    - `POST /api/campaigns/:id/log/cards/remember-as-quest` — pins a DM beat as an active quest (title auto-derived, tagged `quest`/`remembered`/`active`).
    - Opening-lead cards (generator + template fallback) now ship with `status=active`.
  - Lean DM prompt now splits cards into ACTIVE OPENING LEAD(S), CLOSED LEADS ("do NOT push again; reference only if naturally relevant"), and OTHER KNOWLEDGE CARDS.
  - Frontend:
    - `QuestLogPanel` now renders the synthetic shape from the new endpoint, and accepts an `onUpdateStatus(questId, status)` handler to show inline "Mark complete" / "Mark failed" buttons on active quests.
    - `AdventureLogWithDM` fetches quests on mount + after pinning; added a Scroll 📜 "Pin as quest" button alongside the existing "Remember" bookmark on every DM message.
    - Quest Log panel now always renders inside an active campaign (shows empty-state copy until quests exist).
  - **Verified end-to-end**: Mystery campaign → opening lead "Shadows Over Emberfall" appears; pin a DM beat ("woman in a red shawl…") → now 2 active quests; mark one completed → sorted to bottom; next DM turn exclusively advances the remaining active lead without mentioning the closed one.

### 2026-04-23 (quest connection)
- **Feature: Quests now drive the narration end-to-end (Tiers A+B+C).**
  - **Tier C**: New `generate_opening_quest_card_with_ai(intent, world, character)` replaces the templated "Opening Lead" with a rich LLM-authored hook tailored to the campaign focus/tone/class. Returns JSON → `KnowledgeCard(type=quest, tags=[…, 'opening', 'quest'])`. Falls back to the old template on any failure.
  - **Tier A**: `build_starting_scene_with_ai` now accepts `active_quest` and plants it as the concrete hook in the intro. Ending instructions updated to require the 2-3 choices (or 1 question) to tie back to the lead.
  - **Tier B**: Lean DM prompt now splits "ACTIVE OPENING LEAD(S)" from "OTHER KNOWLEDGE CARDS" and instructs the DM to *advance or raise the stakes on the lead in the next 1-3 turns unless the player pivots hard*. Quest-type cards tagged `opening`/`active` are routed into the leads bucket.
  - `generate-world` endpoint wires them in order: quest card → intro (with the quest) → persist everything.
  - **Verified live**: Political Intrigue campaign → AI card "A Missing Silver Seal" + archives hook in intro + DM directly advanced into the archives, AND kept the lead alive (as one of three options) even when the player deliberately pivoted to a drink. 

### 2026-04-23 (later)
- **Feature: Auto-calc HP from class + CON modifier (5e fixed-average rule).**
  - New `utils/hp.js` with `computeMaxHp(classKey, conScore, level)` — case-insensitive on class key, floors at 1, uses standard 5e fixed-average per level (`floor(hit_die/2) + 1 + conMod`).
  - `RPGGame.jsx` bridge now computes max HP from class + CON instead of defaulting to 10 for every hero.
  - `CharacterPreview.jsx` surfaces "Max HP: X (hit die + CON modifier)" with a heart icon.
  - Verified with Playwright: Paladin (d10) with CON 14 → **Max HP: 12**. Unit-tested 9 cases including unknown class → null.

### 2026-04-23
- **Feature: Load / Preview / Edit / Delete existing hero flow.**
  - Main menu → **"Load existing hero"** → `/characters` grid listing all V2 heroes with portraits (50+ heroes render correctly).
  - `/characters/:id` — Character sheet preview: portrait, level/race/class, ability scores, appearance, personality, with **Start new campaign** / **Edit** / **Delete** actions.
  - `/characters/:id/edit` — Lean edit form: identity (name, age), appearance (build, skin, hair, eyes, notable features), personality (ideal/bond/flaw), plus **Regenerate portrait** button. Race, class, ability scores, and background.key are intentionally locked to protect campaign state.
  - **Delete** has a confirm modal and calls `DELETE /api/characters/v2/:id` (existing endpoint).
  - **Start new campaign** wires the selected hero into `useSessionCore` and navigates to `/campaign-setup` — same flow the wizard uses after creation, so no downstream changes needed.
  - Verified end-to-end with Playwright: preview → edit → save → preview now reflects the new flaw. Backend PATCH round-trip clean.

### 2026-04-22 (final)
- **Feature: Role Play sidebar now shows the player's chosen Ideal/Bond/Flaw with a ✦ chosen indicator.**
  - `enrichRoleplay(character, raceKey, bgKey, persistedPersonality)` in `RPGGame.jsx` now prefers the persisted wizard selection and only falls back to a deterministic pick from the background's pool if nothing was chosen.
  - `CharacterSidebar.jsx` shows a subtle amber "✦ chosen" badge with a tooltip ("Chosen during character creation — the DM weaves it into narration") next to player-selected Ideal/Bond/Flaw — closes the loop between what the player picked and what the DM is actually using.

### 2026-04-22 (even later)
- **Feature: Strict POV discipline in intro + Lean DM prompts.** Added a "POV DISCIPLINE (strict)" block that bans outside-the-head appearance descriptions (hero can't see their own "slim frame" or "keen green eyes") and meta-narrated thoughts ("you think…", "thoughts swirl in your mind", "in the back of your mind"). Appearance cues are only allowed via: (1) physical sensation, (2) a reflection the hero actually sees, (3) clothing/gear they can look at, or (4) another character reacting to them. The DM also may not narrate decisions the player didn't make.
- Verified: 5/5 fresh intros scanned clean against a regex panel of forbidden patterns; DM turns now describe weight of a dagger or cool leather on skin instead of eye color.

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
