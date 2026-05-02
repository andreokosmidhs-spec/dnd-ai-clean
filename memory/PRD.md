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

### ✅ Recent Additions (Feb 2026)

#### Failure Semantics for Investigations
Properly defined what happens when a beat's check fails — until now a fail still advanced, making the DC pointless.
- **Backend** (`services/storyline_service.py`, `routers/storylines.py`):
  - `/resolve` now accepts `mode: "fail-forward" | "press-on"`. Fail-forward marks the beat failed, advances, and emits a `complication` (1-2 sentence Mercer-style narration). Press-on keeps the beat active, sets `press_on_used=true` (one-time per storyline), emits a cost-of-retry complication. Second press-on returns `400 — Press On already used`.
  - New `POST /storylines/{sid}/creative` — body `{approach_text}`. Calls `judge_creative_approach` (LLM judge that's generous to inventive thinking); returns `{judgment: 'passed'|'partial'|'failed', narration, applied_check, complication?}`. Pass/partial → beat passed (player gets credit); fail → beat failed + complication generated.
  - **Reward scales linearly** with passed beats (XP rounded to 25, items only awarded if ≥50% of beats passed). All-fail storylines yield 0 XP, no item.
  - Storyline drafts now persist `press_on_used:false`, `complication:null` defaults.
- **Frontend** (`components/ActiveInvestigationPanel.jsx`, `AdventureLogWithDM.jsx`):
  - Roll button shows `Roll d20+<mod>`; ability mod is derived from character's stats per check type (Investigation→INT, Persuasion→CHA, etc.).
  - On a failed roll → `FailurePrompt` dialog opens with three choices: **Press On** (greyed if already used), **Push Through** (fail forward), **Try a Different Approach** (opens a `CreativeApproachDialog` with a Textarea for the player to describe an alternative strategy).
  - `Try Different Approach` is also available as a top-level button on the panel (not gated behind a fail).
  - Header shows live `passed` / `failed` count badges.
  - Complications and creative-approach narrations land in the Adventure Log under their own card titles: **"⚠️ Complication — &lt;Storyline&gt;"** and **"✨ A Different Approach (judgment)"** — both persisted to localStorage.
  - Reward modal shows `passed · failed` chip and an honest "No item this run" line when the threshold wasn't met.
- **Tests**: `/app/backend/tests/test_storyline_failure_semantics.py` (8/8 passing) covering all four mechanics + reward scaling + regressions.

#### Hook → Storyline → Reward (Procedural Investigation Generator)
- **Backend**:
  - `services/hook_extractor.py` — extracts up to 3 "points of interest" from any DM narration (regex fast-path for "Three things draw the eye:" enumerations + LLM fallback for free-form scenes). Each hook ships with literal text + char span + topic + verb_hint. `detect_engaged_hook` decides whether a player's action targets one of the active hooks (idle-verb stoplist + LLM nuance).
  - `services/storyline_service.py` — drafts a 3-5 beat linear investigation chain rooted in the engaged hook (LLM-generated; deterministic fallback). Each beat carries title, description, task, dc 8-20, check_type+ability, status. `advance_storyline` flips the current beat, activates the next, marks completed on the last beat. `generate_storyline_reward` returns LLM-themed reward {xp, title, description, item, tone}; XP scales with collective DC (rounded to 25, max 1200).
  - `routers/storylines.py` — endpoints: `POST /storylines/draft`, `GET /storylines`, `GET /storylines/{id}`, `POST /storylines/{id}/resolve`, `POST /storylines/{id}/abandon`. Each storyline draft seeds a linked Quest KnowledgeCard tagged `storyline`.
  - `routers/lean_dm.py` — every DM turn now extracts hooks from the new narration (persisted to message metadata), and tries to detect engagement against the previous turn's hooks (or `starting_scene.hooks` on turn 1). Engagement auto-drafts a storyline that lands on the response.
  - `routers/campaigns.py` — backfills `starting_scene.hooks` on legacy campaign loads.
- **Frontend**:
  - `components/EntityLink.jsx` — new `HookSpan` (italic dashed underline + verb tooltip). `EntityNarrationParser` now merges `entity_mentions` + `hooks` into a single sorted span list, dropping hooks that overlap an entity range so proper-noun links always win.
  - `components/ActiveInvestigationPanel.jsx` — collapsible top-bar panel showing active investigation (storyline title, beat counter, check-type+DC chip, beat description, task, beat-dot rail with status colors, Roll d20 / Pass / Fail / Abandon buttons, `data-testid` coverage). `StorylineRewardModal` shows XP + tone + themed item on completion.
  - `components/AdventureLogWithDM.jsx` — wires hooks into DM messages, attaches active-storyline state (loaded on mount + auto-drafted from `/dm/action`), renders the panel + reward modal + a "POINT OF INTEREST" hint popover when an inline hook is clicked.
- **Tests**: `/app/backend/tests/test_storylines.py` (10/10 pass) covering hook backfill, draft, list/get, sequential resolve advancing current_beat, completion reward formula (xp = round(max(60, total_dc*8)/25)*25, capped 1200), abandon, lean-DM engagement positive + negative cases. Frontend Playwright run covered hook spans, hook-hint popover, panel mount, full Pass-through-to-completion + reward modal, world-map regression intact.

#### Node-Graph Campaign Map with Regional Event Decks
- **Backend**: `services/world_graph.py` generates 5-7 biome-themed regions per campaign with normalized x/y coords and edges. Starter region is fully hydrated with 5 LLM-generated event hooks; neighbor regions ship with rumor hints and lazily hydrate on first visit (`hydrate_region`).
- **Endpoints** (all under `/api/campaigns/{id}/world/*`):
  - `GET /graph` — returns regions, edges, current_region_id (auto-backfills legacy campaigns)
  - `POST /regions/{rid}/visit` — hydrates hints into 5 full events, marks visited, updates current_region_id
  - `POST /events/{eid}/accept` — converts an event into an active quest KnowledgeCard (tagged with biome + difficulty), marks event `accepted`, AND returns a Mercer-style `arrival_beat` (1-2 sentence narration of how the hook arrives in fiction — a courier, a rumor, a bell, a letter).
  - `POST /events/{eid}/dismiss` — removes event from the deck
- **Frontend**: `components/WorldMapGraph.jsx` — pure-SVG node graph with biome-colored nodes, pulsing "you are here" marker, dashed edges, event-count pips, a right-side RegionPanel showing rumors (unvisited) or the hydrated event deck with Accept / Dismiss / Travel buttons. Integrated into `RPGGame.jsx` World Map tab (falls back to legacy WorldMap when no campaignId).
- **Adventure-Log Bridge**: When a player accepts an event on the map, the arrival beat is dispatched as a `rpg:dm-beat` window event AND queued in `localStorage` (so it survives the World-Map → Adventure tab unmount). The `AdventureLogWithDM` listens live and drains the queue on mount; new beats render under a dedicated **"🪶 A Lead Reaches You — &lt;Quest Title&gt;"** card so the quest enters the fiction as narrative, not just a silent card.
- **Tests**: `/app/backend/tests/test_world_graph.py` (11/11 passing) covering graph structure, visit/hydration, accept → quest wiring, dismiss, and /quests integration. Frontend smoke-tested end-to-end via Playwright (accept → tab switch → beat appears in log with proper title).

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

### 2026-04-29 (biome system: location cards colored by terrain + DC modifiers)
- **Feature: Location cards now classify into one of 12 biomes**, each with a distinct color, resources / animals / monsters list, and Survival/Nature DC modifiers.
  - **New `/app/backend/data/biomes.py`** catalog: `forest`, `plains`, `desert`, `mountain`, `swamp`, `coast`, `tundra`, `underdark`, `volcanic`, `urban`, `fey`, `shadow`. Each defines:
    - `accent` — Tailwind gradient for the card header (e.g., desert = `from-amber-500 to-orange-700`, swamp = `from-teal-700 to-emerald-900`).
    - `chip` / `icon` — UI styling.
    - `survival_dc_mod` / `nature_dc_mod` — `+N` harder, `−N` easier (forest forage = −2, underdark = +4).
    - `resources`, `animals`, `monsters` — lore lists for grounding play.
  - **New `GET /api/campaigns/biomes`** endpoint serves the public catalog so the frontend can mirror it without duplication.
  - **`auto_cards.py`** got a third LLM call (`_classify_biome`) — every newly-seeded location card is classified and decorated with the full biome payload (key, label, accent, chip, lists, DC mods).
  - **`lean_dm.py`** now injects a "CURRENT BIOME" section into the DM system prompt when at least one location card has biome data, with the biome's name, DC mods, and lists. The DM organically tunes check difficulty + scenery to the terrain (no dice talk, just narrative consequences).
  - **`KnowledgeCard.jsx`** uses the biome's accent gradient for location-type headers (overrides the type-based green) and prints `PLACE · {biome}` so the player sees both the type AND the biome at a glance.
  - **`CardDetailsDrawer.jsx`** renders a biome panel with the survival/nature DC chips and color-coded chips for Resources (emerald), Animals (sky), Monsters (red).
  - **End-to-end verified** on the avon campaign: a single DM turn ("travel to the scorching dunes of the Anvil Wastes, then into the foul mires of the Drowning Marshes") produced two new location cards, **Anvil Wastes → desert** (cactus water, sand worms, +3 survival DC) and **Drowning Marshes → swamp** (peat, hags, +2 survival DC). Cards render with sand-orange and dark-teal headers respectively, distinct from emerald forest locations.

### 2026-04-29 (3 new card types: Spells, Favors, Curses + location origin)
- **Feature: DM now auto-generates 7 distinct card types** (was 4: NPCs, Locations, Factions, Items). Each gets its own MTG color and lucide icon.
  - **New types added to `cardTypeConfig.js`**:
    - 🟣 **Spells** (`spells`) — `Sparkles` icon, violet→fuchsia gradient (mystic). Aliases: `spell, ability, cantrip, ritual, prayer`.
    - 🟡 **Favors** (`favors`) — `HeartHandshake` icon, yellow→amber gradient. Aliases: `favor, boon, blessing, pact, debt`.
    - 🔴 **Curses** (`curses`) — `Skull` icon, red→rose gradient (visceral warning). Aliases: `curse, hex, affliction, malediction`.
  - **Backend `services/auto_cards.py`** got a SECOND LLM pass (`_detect_narrative_events`) that scans each DM turn for narrative happenings — items the player ACQUIRED, spells LEARNED, favors OWED, curses RECEIVED. Strict JSON output, capped at 6 events/turn, runs in addition to the existing proper-noun classifier. Items / spells / favors / curses get status `acquired` or `active`; npc/loc/faction stay `introduced`.
  - **Location-origin tagging**: every auto-seeded card now carries `location_origin` (the campaign's current `starting_town` or `world_core.name`). Threaded through `auto_seed_cards_from_narration()` and rendered as a small `📍 from {Origin}  [auto]` badge under the card title in `KnowledgeCard.jsx`.
  - **`CampaignLogPanel.jsx`** now also pulls the flat `campaign_cards` collection (`/api/campaigns/{cid}/log/cards`) so the new types surface alongside the structured-log content. De-duped on (title, type). Live counts replace the static `counts` object → filter pills "Spells", "Favors", "Curses" appear automatically when ≥1 card of that type exists.
  - **End-to-end verified on the avon campaign**: a single player turn ("I help the wizard, he teaches me Fire Bolt, gifts me a Silver Ring of Warding, owes me a favor, and curses me with Hex of Wyrmsbane") produced **all 4 event-type cards in one shot** plus the location card "Emberfall" — origins all tagged `Gate of Emberfall`. Knowledge Deck now shows 20 cards with proper MTG headers (green PLACE, blue NPC, purple FACTION, pink RUMOR, amber QUEST, indigo DECISION) + new filter pills for Spells/Favors/Curses.

### 2026-04-29 (MTG color coding extended end-to-end)
- **Feature: All knowledge cards AND inline entity hyperlinks now use the MTG palette** consistently — single visual language across the Campaign Log deck and the Adventure Log narration.
  - **Card type normalizer (`campaignLog/cardTypeConfig.js`)**: new `normalizeCardType(type)` maps the wild variety of backend card types onto the 8 MTG palette keys:
    - `location | place | landmark | city | region | dungeon` → `locations` (emerald)
    - `npc | character | person | creature` → `npcs` (blue)
    - `quest | objective | mission` → `quests` (amber)
    - `lead | clue` → `leads` (cyan)
    - `faction | guild | organization | order` → `factions` (purple)
    - `rumor | belief | gossip` → `rumors` (pink)
    - `item | artifact | equipment | treasure | loot` → `items` (orange)
    - `decision | choice | event` → `decisions` (indigo)
    - **Wired into all 3 consumers**: `CampaignLogPanel.jsx`, `KnowledgeCard.jsx`, `CardDetailsDrawer.jsx`. Auto-seeded cards (singular `location`/`npc`/`faction`) and legacy seeds (`place`/`belief`/`event`) now color-code identically to the new schema.
  - **Inline entity hyperlinks** (`EntityLink.jsx` + `adventurePapyrus.css`):
    - Added `data-entity-type="{npc|location|faction|item|other}"` attribute on every `EntityLink` span.
    - Parchment CSS retinted per-type with sepia-friendly hues: `npc → blue #1e40af` / `location → emerald #047857` / `faction → purple #6b21a8` / `item → burnt-orange #c2410c` / other → burnt-amber `#9a3412`. Each gets a matching hover wash.
  - **Verified live** on the avon campaign: chronicle and arrival render Realm of Story + Gate of Emberfall in green (`rgb(4,120,87)`), Guild of Scribes + Black Market Syndicate + Wardens of Emberfall in purple (`rgb(107,33,168)`) — colors propagate to clickable inline text and to deck cards seamlessly.

### 2026-04-29 (auto-seeding knowledge cards from DM narration)
- **Feature: Every DM turn now auto-creates `campaign_cards` entries for brand-new NPCs / locations / factions** the AI invents mid-scene. Subsequent mentions become clickable entities *in the same response* — no one-turn lag.
  - **New `/app/backend/services/auto_cards.py`**:
    - **Regex extractor `_extract_candidates`** finds sequences of 1-4 capitalized words (allowing "of/the/and" connectors). Strips trailing connectors and trailing possessive `'s`. Skips single-word matches at sentence starts (filters "Dawn breaks…", "Ahead…"). Blocklist of 80+ D&D terms, pronouns, days, months, titles, common verbs.
    - **LLM micro-classifier `_classify_candidates`** (gpt-4o-mini, temperature 0, JSON-only response) tags each unknown as `npc | location | faction | none`. Strips markdown fences defensively, handles JSON parse failures gracefully. Caps at 12 candidates per call to bound cost.
    - **`auto_seed_cards_from_narration`** orchestrates: builds known-names set from the entity index (including possessive forms), filters candidates, calls classifier ONLY when ≥1 unknowns, inserts minimal `{id, title, type, content: <grounding-sentence-snippet>, status: "introduced", auto_seeded: true, source: "dm_narration", createdAt, updatedAt}` into `campaign_cards`. Race-safe (checks DB before insert).
  - **`routers/lean_dm.py`**: calls the seeder AFTER the narration is generated, then re-builds the entity index with the new cards merged in, so mentions returned to the frontend already include the just-seeded entities. Same-turn clickability.
  - **`services/campaign_service.py`**: `build_v2_entity_index` widened to recognize both new-schema card types (`location`, `faction`, `npc`, `item`) AND legacy-schema types (`place`, `landmark`, `city`, `region`, `guild`, `organization`, `character`, `artifact`) so pre-existing cards prevent duplicate seeding.
  - **Cost control**: the classifier runs only when there ARE unknown candidates. A turn with zero new entities = zero LLM calls for this feature.
  - **Verified end-to-end** on legacy "avon" campaign (Half-Orc Rogue):
    - Turn 1 ("I ask for help from a passing merchant. What is his name and the bandit leader's name?") → DM invents "Zarek" + "Caldera" → 2 auto-cards created → 2 mentions in the same response.
    - Turn 2 ("I ask Zarek about Caldera. Where does she hide?") → Zarek + Caldera recognized from cards → DM also invents "Garren" + "Great Hollow Ruins" → both auto-seeded AND clickable in the same response.
    - Total auto-seeded after 2 turns: 4 clean cards, no duplicates, no possessive forms, content snippets faithfully grounded in the introducing dialogue.

### 2026-04-29 (entity highlighting now active for V2 campaigns)
- **Fix: Locations / factions / NPCs are now hyperlinked in the chronicle and arrival narration** for every V2 campaign (new + legacy backfilled). Previously only the legacy `dungeon_forge` flow extracted entity mentions; the V2 Lean DM path returned `entity_mentions: []`, so nothing was clickable.
  - **Backend**:
    - **New `build_v2_entity_index(world, cards)`** in `services/campaign_service.py` — adapter that reads the V2 world shape (realm name, starting town, points of interest, `setting.factions`, knowledge cards) and emits the index format `extract_entity_mentions` expects. De-dupes by `(type, lowercase-name)`, sorts by descending name length so "Black Market Syndicate" wins over "Black Market".
    - **`routers/campaigns.py`**:
      - Generation path: extracts mentions for both `world.world_brief` and `starting_scene.introText`, surfaces them on the response as `world_brief_entity_mentions` and `entity_mentions`.
      - Backfill path: same extraction runs when a legacy campaign is opened; pulls existing `campaign_cards` so pinned entities also become linkable. Persists once.
    - **`routers/lean_dm.py`**: every DM turn now passes `narration` through `extract_entity_mentions` against `build_v2_entity_index(world, cards)` so the response's `entity_mentions` field is populated. Frontend already renders these via `EntityNarrationParser`.
  - **Frontend**:
    - **`RPGGame.jsx`**: campaign-fetch on game-start now reads `entity_mentions` + `world_brief_entity_mentions` from the API and seeds them onto the chronicle / arrival messages instead of always-empty arrays.
    - **`AdventureLogWithDM.jsx`**: idempotent backfill effect — when the component mounts with a `campaignId` and finds chronicle/intro entries with empty `entity_mentions`, it fetches the campaign once and patches mentions in. Saves stale localStorage caches without forcing a session reset.
    - **`adventurePapyrus.css`**: retinted entity highlights for parchment — `text-orange-*` spans (used by `EntityLink`) now render as burnt-sepia `#9a3412` with a 2px underline of the same hue at 55% opacity, hover fills with `rgba(154,52,18,0.12)`. Stays clickable, blends into the manuscript aesthetic.
  - **Verified live** on legacy "avon" campaign: the chronicle bubble now hyperlinks **5 entities** (Realm of Story · Guild of Scribes · Black Market Syndicate · Wardens of Emberfall · Gate of Emberfall) and the arrival scene hyperlinks **1** (Black Market Syndicate). Computed color of the first entity: `rgb(154, 52, 18)` ✓. Total of 6 amber-underlined entity spans visible in the manuscript.

### 2026-04-29 (player feedback channel via Resend)
- **Feature: Floating "Send Feedback" button** appears top-right on every screen except the in-game adventure (where it would clash with the input row). Players can submit Bug / Feature / Other reports that land directly in `andreo.kosmidhs@gmail.com`.
  - **Backend `POST /api/feedback/`** in new `routers/feedback.py`:
    - Pydantic `FeedbackRequest` model (type/title/description/optional fromEmail/optional context snapshot).
    - Renders an inline-styled HTML email with a colored type badge, the title/description/from fields, and a debug-context table (campaign ID, character ID, current URL, user-agent — auto-attached by the frontend).
    - Sends via **Resend** (`resend>=2.0.0` added to `requirements.txt`) using `asyncio.to_thread` to keep FastAPI non-blocking.
    - `from = onboarding@resend.dev` (Resend sandbox sender, no domain verification needed for sending to the account owner's inbox).
    - `reply_to = payload.fromEmail` when provided, so a single click in Gmail replies to the player.
    - Subject formatted as `[RPG Forge · BUG|FEATURE|OTHER] {title}` for easy mailbox filtering.
  - **Frontend `FeedbackButton.jsx`**:
    - Floating amber pill in the top-right (responsive: icon-only on mobile, "Feedback" label on `sm+`).
    - Shadcn dialog with Bug/Feature/Other chip selector, title input, multi-line description with `{n}/4000` counter, optional email (cached in localStorage between sessions).
    - Auto-attaches `campaignId` (from `useSessionCore.activeCampaignId` or URL params), `characterId`, `currentUrl`, `userAgent`.
    - Toasts "✅ Feedback sent — thank you!" on success; surfaces inline error on failure.
    - Hidden on `/game/*` so it doesn't sit on top of the in-game UI.
    - Mounted globally inside `<BrowserRouter>` in `App.js`.
  - **Env**: added `RESEND_API_KEY`, `FEEDBACK_RECIPIENT_EMAIL`, `RESEND_SENDER_EMAIL` to `/app/backend/.env`.
  - **Verified end-to-end**: curl POST returned `{"ok": true, "email_id": "a2e0a3ac-…"}`; Playwright UI submit returned HTTP 200; both emails delivered via Resend with the inline-HTML template (badge + description + context table).

### 2026-04-29 (full portrait visibility — no head clipping)
- **Fix: Sidebar portrait was clipping the top of the head** when resuming a campaign because of the prior `object-cover origin-top scale-[1.35]` zoom. Switched to `object-contain` so the entire painted portrait is always visible inside the amber frame; the gray-900 frame background letterboxes gracefully when the source isn't a perfect square. Verified live on the avon Rogue — head, hair, shoulders, and chest all visible end-to-end.

### 2026-04-29 (bulk delete all characters)
- **Feature: "Delete All" button on `/characters`** to mass-wipe the hero pool in one confirmed action. Useful for pruning the pool down under the 10-character limit.
  - **Backend `DELETE /api/characters/v2/`** (bulk) added in `character_v2_routes.py` — registered BEFORE the `{character_id}` route so it doesn't get shadowed. Uses `collection.delete_many({})`; returns `{"deleted": N}`. Works for both Mongo and in-memory fallback.
  - **Frontend `CharactersList.jsx`**: red outlined "Delete All" button appears in the header (only when `characters.length > 0`) next to "Forge new hero". Clicking opens a destructive confirm card at the top: *"Delete all {N} characters? This cannot be undone."* with Cancel and "Yes, delete all" actions. On success → list refreshes to empty state + green toast "Deleted N characters."
  - Verified live with 2 seeded Fighters: button appears, confirm card slides in, backend returns `{"deleted": 2}`, list clears, toast fires, pool badge resets to `0/10`, Forge button re-enables. Single-delete on a missing id still returns 404 (route ordering correct).

### 2026-04-29 (papyrus/calligraphy theme for Adventure Log)
- **Feature: Full visual redesign of the Adventure Log screen** — the former black/amber/violet dark theme is now a handmade **parchment + black-ink calligraphy manuscript**.
  - **New `/app/frontend/src/styles/adventurePapyrus.css`** — a scoped theme applied via the `adventure-papyrus` class on the root `<Card>` of `AdventureLogWithDM.jsx`:
    - Layered parchment background (cream `#f1e4c3` + 4 corner vignettes + aged blotches + SVG noise) with an inset box-shadow that mimics burnt edges.
    - Ink color forced to warm sepia-black `#2b1810` for every descendant (text-white/gray/slate/amber/violet/purple utilities all overridden).
    - Fonts: **Tangerine** (flourished calligraphic script, weight 700) for all headings and titles (Adventure Log, Realm of Story, Quest Log, A Chronicle of…, The Adventure Begins, timestamps). **IM Fell English** (revived 17th-century roman) for body narration, justified with 1.05rem/1.6 line-height.
    - Message bubbles: violet/purple/blue/indigo backgrounds → same warm tan parchment with sepia borders; Tailwind gradient custom properties (`--tw-gradient-from/to/via/stops`) are also neutralized so `bg-gradient-to-r` utilities don't leak purple through.
    - World-brief card keeps a slightly warmer tint + thicker border + inset shadow so it still reads as "special chronicle".
    - Scrollbar, icons (SVG currentColor), and interactive buttons all tuned to the sepia palette.
  - **Wired** via `import '../styles/adventurePapyrus.css'` and `className="adventure-papyrus ..."` on the root Card.
  - **Gotcha caught & fixed**: initial CSS had a comment containing `text-gray-*/` which PostCSS read as the closing `*/` of the comment, breaking the whole file. Rewrote the comment. The bundle now compiles clean.
  - Verified live: the Chronicle, Quest Log, Realm of Story, and "The Adventure Begins" cards all render as warm parchment with Tangerine headlines and IM Fell English body — no visible purple or dark surfaces inside the Adventure Log.

### 2026-04-29 (character pool capacity guard)
- **Feature: Prevent new-character creation when the saved pool is full** (limit = **10 heroes**), with a clear toast guiding the user to delete one first.
  - **New `/app/frontend/src/utils/characterPool.js`** — single source of truth: `CHARACTER_POOL_LIMIT = 10`, `fetchCharacterCount()` (fail-open: returns `-1` on network error so a transient backend hiccup never bricks the wizard), and `canCreateCharacter()` which fires `window.showToast(...)` and returns `false` when at capacity.
  - **MainMenu.jsx**: `handleNewCampaign` and `handleConfirmNewCampaign` both `await canCreateCharacter()` before navigating to `/character-v2`. If full → red toast top-right ("Character pool full (50/10). Delete one of your existing heroes to forge a new one."), URL stays put.
  - **CharactersList.jsx**: "Forge new hero" button is **disabled** when `characters.length >= 10`, gets `disabled:opacity-50 disabled:cursor-not-allowed`, shows a `{count}/{LIMIT}` badge inside the button (e.g. `50/10`), and a hover-`title` tooltip ("Pool full — delete a hero first."). Both the header button and the empty-state CTA route through `handleForgeNew()`, which also calls `canCreateCharacter()` as a final guard.
  - Verified live with the current 50-character pool: red toast appears on "New Campaign" click and the "Forge new hero" button is disabled with the `50/10` badge visible on `/characters`.

### 2026-04-29 (collapsible Quest Log)
- **Feature: Quest Log now folds to a single header bar by default** (matching the existing collapsible Realm panel), so the DM narration sits near the top of the screen.
  - `QuestLogPanel.jsx`: header is now a `<button>` (`data-testid="quest-log-toggle-btn"`, `aria-expanded`) that flips a single `isPanelOpen` state. When closed, only the row "📜 Quest Log · {N} Active · ▼" shows; when open, the active quests, completed-toggle, and inner cards render below. Defaults to **collapsed**.
  - `Chevron(Up|Down)` icons mirror state, identical to the WorldInfoPanel UX.
  - Verified live (avon Cleric, "The Frayed Rope" active quest): `aria-expanded` cycles `false → true → false` on click; default load lands collapsed; the Chronicle bubble now starts ~270px higher on the screen.

### 2026-04-29 (smarter character-create error reporting)
- **Fix: "Couldn't reach the backend" submit failures now tell the user EXACTLY what to do** instead of a vague "(All endpoints failed)".
  - **Diagnosis:** the user's repeated submit failures with the new reference-image upload were traced to TWO real causes:
    1. The Emergent platform paused the preview ("You're viewing a static preview. Resume Preview" overlay) — outgoing fetches from the iframe are blocked.
    2. The 12s per-attempt timeout could trip on slow uplinks when a reference image (~200-600KB data URL) is in the payload.
  - **Fix in `ReviewStep.jsx` (handleSubmit)**:
    - **Adaptive timeout**: 30s per attempt when `appearance.referenceImage` is present, 12s otherwise. Catches the "submit hangs while uploading" case.
    - **Reachability probe on status=0**: when both POST attempts fail with a network error, runs a 5s GET against `/api/characters/v2/` to determine whether the backend is reachable AT ALL. Branches the user-facing message:
      - `navigator.onLine === false` → "Your browser reports it's OFFLINE. Reconnect …"
      - probe succeeds → "The backend is reachable, but submitting timed out. If you uploaded a reference image, try removing it and submit again — then re-upload after the character is created."
      - probe fails → "We couldn't reach the backend at all. If you see a black bar at the bottom saying 'You're viewing a static preview' with a 'Resume Preview' button, click it and try again. Otherwise hard-refresh (Ctrl/Cmd+Shift+R)."
  - **Verified deployment**: live bundle contains the new `OFFLINE` / `Resume Preview` / `hasReferenceImage` markers; `bundleSize: 4.47MB`. End-to-end browser POST with a 17KB reference image returned HTTP 200 in 88ms.
  - **Important**: the original failure was NOT a backend bug. Backend handles 17KB-600KB reference-image payloads in <300ms; from a real browser, character creation works perfectly. The screenshot's "static preview" overlay was the actual cause.

### 2026-04-29 (portrait frame: face-centered, larger)
- **Feature: Sidebar portrait now zooms onto the face and fills the sidebar width**, replacing the small fixed 192×192 thumbnail.
  - **`CharacterSidebar.jsx`**: portrait wrapped in a clipping `<div>` sized `w-full aspect-square` (~264×264 in the 288px-wide sidebar). The `<img>` inside applies `object-cover origin-top scale-[1.35]` — the transform anchors to the top of the image and zooms in, so the face fills the visible frame and the chest/arms crop out.
  - Border + amber glow preserved (`border-2 border-amber-500/60 shadow-[0_0_24px_rgba(245,158,11,0.4)]`). Placeholder state matched in size with bigger icon for parity.
  - Verified live on the loaded "avon" Cleric — face/hair/beard fill the frame, no awkward chest/arm space.

### 2026-04-29 (portrait reference image upload)
- **Feature: Players can upload a reference image** (face / artwork / mood board) in Step 6 (Appearance) and Nano Banana uses it as visual inspiration alongside the written description when generating the portrait.
  - **Frontend (`AppearanceStep.jsx`)**: Amber-bordered "Portrait Reference (optional)" card with an `Upload reference image` button. After upload: 240px-wide preview + `Replace` and `Remove` buttons. Errors surface inline. `data-testid` on every interactive control.
  - **New `/app/frontend/src/utils/imageUpload.js`**: `fileToCompressedDataUrl(file)` — validates MIME (image/*), reads via `FileReader`, draws onto a `<canvas>` clamped to 1024px on the longest side, exports as JPEG quality 0.85. Keeps payloads under ~600 KB so JSON round-trip stays fast.
  - **Wizard plumbing**: `useWizardState.js` initial state and `payload.js` build carry `referenceImage` (data URL). Persisted on `characters_v2.appearance.referenceImage`.
  - **Backend**:
    - `AppearanceInfo` adds `referenceImage: Optional[str] = None`.
    - **`character_portrait.py`** parses the data URL into `(mime, base64)`, validates `image/jpeg|png|webp`, and attaches a `FileContent(content_type, file_content_base64)` onto the `UserMessage` via the `file_contents` kwarg. Augments the text prompt with: *"A reference image is provided; use it as visual inspiration … but adapt it to the described race, class, gear, and fantasy setting. The output must be a fresh painted portrait, not a copy of the reference."*
    - Falls back gracefully (logs warning, skips attachment) if the data URL is malformed or MIME unsupported. Replaced legacy `print(...)` with `logger.warning(...)`.
  - Verified live: `POST /api/characters/v2/create` with a tiny PNG data URL round-trips through MongoDB → `GET /api/characters/v2/{id}` returns the same data URL. AppearanceStep + portrait generator both lint clean.

### 2026-04-29 (facial hair + hair style fields)
- **Feature: Players can now describe Hair Style and Facial Hair separately from Hair Color** in Step 6 (Appearance), and the values flow through to the portrait artist (Nano Banana) and the DM prompts.
  - **Frontend (`AppearanceStep.jsx`)**: Two new free-text inputs with `<datalist>` autocomplete suggestions (HAIR_STYLE_SUGGESTIONS: Buzz cut → Bald, 15 entries; FACIAL_HAIR_SUGGESTIONS: Clean-shaven → Forked beard, 12 entries). Players can pick a preset or type anything (e.g. "Topknot with shaved sides", "Forked beard with iron rings"). Help text under each input. `data-testid` on both for testing.
  - **Wizard plumbing**: `useWizardState.js` initial state, `payload.js` build, `CharacterPreview.jsx` summary block all carry `hairStyle` + `facialHair`.
  - **Backend**: `AppearanceInfo` Pydantic model adds `hairStyle: Optional[str]` and `facialHair: Optional[str]` (no migration needed — pre-existing chars just get None).
  - **Portrait prompt** (`character_portrait.py`): builds a single hair phrase ("long braided auburn hair") and appends a separate `"facial hair: …"` clause to the Nano Banana prompt body. Portraits now render the requested style and beard.
  - **DM prompts** (`lean_dm.py` + `campaign_service.py`): appearance bits include the merged hair phrase AND a dedicated facial-hair line, so cinematic narration can reference them naturally without leaking outside-perspective ("you").
  - Verified live: Round-tripped a Dwarf Fighter "BeardMaster" with `Long braided` + `Forked beard with iron rings` through `POST /api/characters/v2/create` → MongoDB → `GET /api/characters/v2/{id}` → CharacterPreview screen renders both fields cleanly.

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
