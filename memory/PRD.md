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

#### NPC Identity Sheets — Roleplay Anchors + Social-Action Gating + Redacted UI (Feb 2026)
Player flagged that the DM auto-resolved a knife-to-throat threat without an Intimidation check, and that NPCs felt like puppets without consistent identities. Massive cross-cutting fix:

**1. Hidden NPC Identity Sheets (auto-generated on mint)** — `routers/storylines.py`:
- New `_generate_npc_identity_sheet` LLM helper. When `_mint_target_cards_if_revealed` mints a `character` card it now ALSO generates a hidden sheet with:
  - Stats: AC, HP, Intimidation DC, Persuasion DC, Deception DC, Insight DC, passive Insight
  - Personality: trait, ideal, bond, flaw
  - Background, mannerisms[], speech_style, secrets[], allegiances[], current_motivation (scene-specific)
- Sheet is stored on the card under `secret_content`. New `revealed_fields` array tracks what the player has actually learned (defaults to `["title","description"]` — name + role; everything else stays redacted).
- Verified live: minting *Hester Crane* produces a full sheet with `intimidation_dc: 13`, speech style "rapid-fire, slightly breathless", concrete background and 2 hidden secrets she'll only volunteer under pressure.

**2. DM Roleplay Anchors + Social-Action Gating** — `routers/lean_dm.py::_build_system_prompt`:
- New "NPC ROLEPLAY ANCHORS" block in the system prompt — pulls each in-deck NPC's hidden sheet (speech style, mannerisms, motive, social DCs, secrets) so the DM can voice them consistently across turns.
- New rule **4b** "IN-CHARACTER NPC ROLEPLAY (HARD RULE)": once an NPC has a sheet, they MUST stay in character every turn — same speech style, mannerisms, motives. They never volunteer their listed secrets; those must be EXTRACTED via successful Intimidation/Persuasion/Deception/Insight. Multiple NPCs in a scene must have distinct voices.
- New rule **7b** "SOCIAL-ACTION GATING (HARD RULE)": when the player's input contains threat / weapon-draw / persuasion / deception / insight cues, the DM must NARRATE THE BEAT (NPC's pupils tighten, hand drifts to belt) but NOT auto-resolve the reaction — instead end with a natural prompt for the appropriate ability check. The system layer rolls; the DM narrates fallout next turn. Auto-confessing NPCs without checks is now explicitly forbidden.

**3. Frontend NPC Card with Redacted Fields** — `components/campaignLog/`:
- New `NPCIdentityPanel.jsx` — renders the secret sheet on NPC card details. Public fields (in `revealed_fields`) show clearly; everything else gets a `blur-[5px]` stencil with a Lock icon overlay and a contextual hint ("Read them to learn this", "Buried deep — extract via skill or pressure").
- Sections: Personality (trait/ideal/bond/flaw) · Manner (speech/tics/background) · Stats (AC/HP/4 social DCs as a grid) · Allegiances & Secrets.
- Wired into `CardDetailsDrawer.jsx` above the Metadata section. Only renders for character/npc cards with a generated sheet.

End-to-end verified: minted Hester Crane has all sheet sections filled, only `title`+`description` are visible to the player, the rest blurred behind locks.

#### ESC Pause Menu + Font-Size Settings (Feb 2026)
Press **Esc** anywhere in-game to open a small pause menu with three options: **Continue · Settings · Go Back to Main Menu**. The Settings entry opens an inline panel with three font-size presets (Comfortable / Large / Extra Large) — applies globally and persists across sessions.

- **`contexts/FontSizeContext.jsx`** (new) — three-preset provider (1.0 / 1.15 / 1.30 scale). Sets `--app-font-scale` CSS variable + `data-font-size` attr on `<html>` and adjusts the root font-size so all rem-based Tailwind text classes scale cleanly. Persisted to `localStorage` under `rpg-font-size-preset`. Defaults to `comfortable`.
- **`components/GameEscapeMenu.jsx`** (new) — paused overlay with backdrop-blur + amber-edged stone-950 panel.
  - **Continue** (emerald, primary) → resumes the scene.
  - **Settings** → swaps to inline panel listing the 3 presets, each rendering a live italic-serif preview of *"The wooden sign hangs at eye level, ink still wet…"* at the chosen scale and a percentage chip (100 / 115 / 130).
  - **Main Menu** (rose-edged) → confirm dialog ("Your campaign is auto-saved on the server"), then triggers `startNewGame()` to flip `gameState` back to the main menu.
  - Click backdrop, X icon, or press Esc again to dismiss. Back chevron returns from Settings → root.
  - All buttons carry `data-testid` slugs (`escape-menu-continue-btn`, `escape-menu-settings-btn`, `escape-menu-main-menu-btn`, `escape-menu-fontsize-{key}`).
- **`App.js`** — wraps app tree in `<FontSizeProvider>` (above `GameStateProvider`) so the scale is live everywhere from boot.
- **`components/RPGGame.jsx`** — added `escMenuOpen` state + a global `keydown` listener that toggles it on Esc *only while `gameState === 'playing'`*. Listener is inert while typing in inputs/textareas/contentEditable so the chat box keeps native blur-on-Esc behavior. Renders `<GameEscapeMenu>` at the bottom of the in-game tree.

Lint clean.

#### Smart DC Gating — Public Info vs Hidden Knowledge (Feb 2026)
Player flagged that reading a public sign should never require a DC roll — only hidden meanings/deductions deserve gating. Fixed across the storyline pipeline:
- **`services/storyline_service.py::_story_fact_rules`** — added Rule #6: a clear DM decision tree the LLM must follow.
  - **NO ROLL** (`reveal_type='action'`, `dc=0`, description openly visible): reading a public sign or notice, observing what's openly displayed, hearing open speech, reading a tavern menu, asking a merchant their price.
  - **CHECK NEEDED** (`reveal_type='knowledge'`, dc 10-18): deciphering coded text, reading body language (Insight), spotting a hidden compartment, recalling lore (History), eavesdropping unnoticed (Stealth), tracking marks (Survival).
  - "When in doubt, default to NO ROLL — making players roll for things they could just READ kills momentum."
- **`_finalize_beat`** — now keeps `targets[]` for action beats too (so a public sign reveal still auto-mints the named NPC/location/faction cards). Previously stripped them as "knowledge-only".
- **`draft_initial_scene` + `generate_next_scene`** — JSON output spec annotated so the LLM knows `dc=0` means no roll. Initial-scene path now preserves `dc=0` instead of clamping to 12. Both paths set `roll_optional=true` when `dc==0`.
- **`routers/storylines.py::_mint_target_cards_if_revealed`** — now mints on `outcome=passed` for any beat AND on `outcome=skipped` for action beats with `dc<=0` or `roll_optional` (the description was already public; clicking Continue means "I read it"). Knowledge-beat skips still mint nothing — the player chose not to engage.
- **Frontend `ActiveInvestigationPanel.jsx`**:
  - Card type-row chip now renders **"OPEN"** (emerald) instead of "DC 0" when no roll is needed.
  - Bottom-bar primary CTA changes from "Skip · Proceed" (ghost) to **"Continue"** (solid emerald) when the beat is `roll_optional`.
  - `rollOptional` now also returns true when `beat.dc <= 0`, in addition to the explicit `beat.roll_optional` flag.

**Verified live**:
- Hook *"a faded wooden sign about a lost heirloom"* → `reveal_type: action`, `dc: 0`, `roll_optional: True`, full sign text in description, task "Read the sign", 3 targets. Player clicks Continue → 3 cards auto-mint.
- Hook *"subtle scratches on the brickwork"* → `reveal_type: action`, dc: 0 — observation is free; the deeper deduction about what the map means becomes the next gated beat.
- Direct unit test: skipping an action-beat (dc=0) with targets mints 2 cards; skipping a knowledge-beat (dc=14) mints 0 (gated content stays gated).

#### Auto-Mint Knowledge Cards from Storyline Reveals (Feb 2026)
When you pass a knowledge beat, every named entity the DM revealed (NPCs, locations, factions) is now auto-pinned to your Knowledge Deck — no manual "Remember this" required. So after passing the wooden-sign Investigation, the deck immediately gains:
- Character card → **Hester Crane** ("Inquiries to Hester Crane at the Anvil & Cup, by the south gate, before sundown.")
- Location card → **Anvil & Cup** (same sentence as context)
- Faction card → **House Veillane** ("The locket bears the House Veillane crest.")

Implementation:
- **Backend `routers/storylines.py`** — new `_mint_target_cards_if_revealed` helper:
  - Reads `beat.targets[]` (npc | location | faction) and maps to KnowledgeCard types `character / location / faction`.
  - Picks the most relevant sentence from the revelation as each card's description.
  - De-dupes against existing cards by case-insensitive type+title match.
  - LLM fallback (`_extract_targets_from_description_llm`) catches scenes where the LLM forgot to populate `targets[]` — extracts proper-noun NPCs/places/factions verbatim from the description.
  - Cards tagged `source: "storyline-target"`, `auto-minted`, `from-storyline`, `<storyline-title>`.
- Wired into both the `/resolve` (roll path) and `/creative` endpoints. Only fires on `outcome=passed` — failed leads stay sealed and don't expose the entities.
- Response payload now includes `target_cards: [...]` so the frontend can surface them.

Frontend wiring:
- **`ActiveInvestigationPanel.jsx`** — new `onTargetCardsMinted` callback prop fired when the response includes target cards.
- **`AdventureLogWithDM.jsx`** — handler logs an Adventure-Log beat listing the new cards by type/title, fires a success toast (`+N cards added to your deck`), and broadcasts a `rpg:cards-refreshed` window event so any open panel picks up the change immediately.
- **`CampaignLogPanel.jsx`** — listens for `rpg:cards-refreshed` and reloads via `loadAllData()` so the Knowledge Deck displays the freshly-pinned cards in real time.

E2E verified: hook → engagement → opening scene → roll passes → API returns `lead` + `target_cards: 3` → all 3 persist in `campaign_cards` collection with `source=storyline-target`. Re-running the same beat dedupes to 0 new mints.

#### POV-Anchored Storyline Exposition (Feb 2026)
Player reported the DM was fact-dumping in third person ("Lady Selene of Emberfall, noble known for her battles…", "the locket holds the key to an ancient map…") instead of running the table like a real DM — read the sign aloud, name who's recruiting, tell the player where to go to claim the bounty. Major prompt rewrite in `services/storyline_service.py::_story_fact_rules`:
- **Rule 1 — POV exposition**: descriptions must use second-person ("you see / read / hear"). Forbidden phrases now explicit: "a memory ignites", "a flash of insight", "you somehow know", "fate stirs". The character is not psychic.
- **Rule 2 — Source every fact**: every claim must be tied to an in-fiction source the player can point to (literal text on the sign, an inscription, an overheard remark, a known bystander).
- **Rule 3 — Read posted text aloud**: when the hook is a sign/notice/letter/scroll/inscription, the description MUST include the literal posted text in quotes, written like real medieval signage with a contact + place + deadline.
- **Rule 4 — Answer "how do I claim this?"**: every bounty/quest must tell the player WHERE to go, WHO to ask for, and WHEN — by name and address.
- **Rule 5 — End with a directional choice**: last sentence plants a concrete next move, not vague urgency.
- Story-fact requirements raised from 3-of-6 to 4-of-6 with a hard "APPLICATION ROUTE" requirement.
- Description budgets: 800 → 1100 chars to fit the literal sign-text quote.
- System messages rewritten to frame the LLM as "a senior D&D Dungeon Master running a live session at the table" instead of generic narrator.
- **Verified live**: hook *"a faded, wooden sign about a lost family heirloom"* now opens with: *"You read it aloud: 'REWARD — 50 gp for the safe return of a lost family heirloom, intricately designed locket. Inquiries to **Hester Crane, posting clerk at the Anvil & Cup, by the south gate, before sundown**.' … To claim the reward and gather more details, you must head to Hester Crane at the Anvil & Cup by the south gate before sundown."* Task: *"Visit Hester Crane"*. Next-scene after a passed roll keeps the sign quote, names the patron at the Anvil & Cup, and ends with *"Head to the Anvil & Cup and ask for Hester Crane."*

#### Investigation Panel Contrast Pass (Feb 2026)
Player reported the active Insight beat's locked-prompt panel and target chips were unreadable on the dark theme (low-opacity amber on dim stone backgrounds). Pass-through fix in `ActiveInvestigationPanel.jsx`:
- **Locked knowledge prompt** — was `border-dashed border-amber-500/50 bg-stone-950/60` with `text-amber-200/95`. Now solid `border-2 border-amber-400/70 bg-stone-900` with `text-amber-50` (max brightness).
- **Target chips** (LOCATION/FACTION/NPC pills) — were ghost pills `bg-amber-500/20 text-amber-100`. Now solid `bg-amber-500 text-stone-950 font-bold` so they pop like Wizards-of-the-Coast set symbols.
- **Card type header strip** (INVESTIGATION/INSIGHT) — bumped to `bg-stone-700 text-amber-50 font-semibold` for stronger separation from the body.
- **Card title** — size bumped 14px → 15px.
- **Card status footer row** — bumped from `text-amber-100` to `text-amber-50 font-bold`.
- **Modal header badges** (Beat counter, time-of-day, passed/failed counts) — opacity removed, full-saturation borders, `font-bold`.
- **Empty-description fallback** — when a resolved beat has no description (rare LLM gap), the card now shows the outcome text in a muted "—" line instead of rendering a blank body.

#### Story Depth + Resolved Card Readability (Feb 2026)
Three issues fixed after the user reported a passed Investigation card showing only generic atmospheric prose with no concrete leads, plus the PASSED stamp obscuring the description text.

**1. Concrete Story Facts (backend `services/storyline_service.py`)**
- New `_world_facts_block(world, cards)` helper compiles a "WORLD FACTS" reference (realm, town, factions, NPCs, plus the 8 most recent active knowledge cards) so the LLM REUSES established names instead of inventing fresh ones every turn.
- New `_story_fact_rules()` helper produces a hard-rule block that every storyline beat description MUST plant at least 3 of: named NPC + role/location, named place, item history (when/who/value), stakes/reward (concrete numbers), time/circumstance, faction tension. Phrases like "a fragment of thought" / "something more outside" / "whispers in the wind" are explicitly forbidden as empty stand-ins.
- Both `draft_initial_scene` and `generate_next_scene` prompts now inject the WORLD FACTS block + story-fact requirements + a TARGETS-required clause. Description budget bumped 480 → 800 chars to fit richer content. Beat descriptions now run 3-5 sentences instead of 2-4. System messages updated to forbid empty atmospheric writing.
- **Routers `storylines.py` + `lean_dm.py`**: every call to `draft_initial_scene` / `generate_next_scene` now loads up to 20 recent active knowledge cards from `campaign_cards` and passes them on `campaign["_recent_cards"]`.
- **Verified live**: hook *"a faded, wooden sign advertising a lost family heirloom"* now produces:
  - Opening: *"It details a locket belonging to **Lady Mirelle of House Veillane**, reportedly lost just last week during a chaotic market scramble. The sign promises a reward of **50 gold coins** for its return … Close by, **Marielle the herbalist** peruses her wares…"* — 4 named entities, reward, history, factions in one card.
  - Next scene after pass: *"…last known to surface at a clandestine gathering hosted by **Old Hadrick at Garrick's Pier**, just a fortnight ago … rumored to hold a map to an ancient treasure, making it a coveted piece for rival factions like **The Iron Watch**, who are now circling around the docks."* — concrete lead (NPC + location) + stakes + faction pressure.

**2. Resolved Card Readability (frontend `ActiveInvestigationPanel.jsx`)**
- The giant centered "PASSED" stamp watermark (`text-3xl` rotated overlay over the description) was replaced with a small corner badge (`top-1.5 right-1.5`, `text-[10px]`, color-coded background pill) so the revealed text stays fully readable.
- Resolved cards no longer use `opacity-85` (kept only for unresolved-non-active rows). Border now color-codes the outcome (emerald/rose/amber border tint).
- Description color brightened `text-amber-100 → text-amber-50` for higher contrast on the dark card.
- Resolved cards now use the same scrollable `max-h-[260px] sm:max-h-[320px]` overflow as active cards so the player can scroll the full revelation.

#### Robust Hook Engagement — Merged Extractor + Re-extract Fallback (Feb 2026)
Fixed "I walk to the wooden sign and nothing happens" — players engaging with concrete narrative objects that the regex pass missed (because it stopped at the canonical "Three things draw the eye" enumeration) now correctly draft a storyline.
- **Backend `services/hook_extractor.py`**:
  - `extract_hooks` no longer short-circuits when the regex pass returns hits. It now ALWAYS runs the LLM pass too and merges (regex first, then LLM hooks for non-overlapping spans), sorted by character position. New `_hooks_overlap` helper dedupes by span intersection or topic-word containment. Cap raised to `max_hooks * 2` so the engagement detector has enough surface area.
  - Verified live: opening narration with both "Three things draw the eye" enumeration AND a "wooden sign about a lost family heirloom" mention now produces 6 hooks (3 regex + 3 LLM); the wooden sign appears as topic `"lost family heirloom"`, verb `investigate`.
- **Backend `routers/lean_dm.py`**:
  - After the initial engagement check fails, the endpoint now re-extracts hooks on the fly from the most recent DM narration text (last 1-2 turns or `starting_scene.introText` on turn 1), merges any newly-discovered hooks with the cached `active_hooks`, and retries `detect_engaged_hook`. This rescues OLD campaigns whose `starting_scene.hooks` was saved with only the canonical enumeration before this fix shipped.
  - Verified live: cached 3-hook list (no wooden sign) + player action *"I walk to the wooden sign…"* → initial engagement returns NONE → re-extraction finds `"sign"` → engagement succeeds → storyline drafts.

#### Hook-Anchored Opening Scene + Readable Beat Cards (Feb 2026)
Fixed two related bugs in the open-ended investigation flow:
1. **Opening scene was generic** — Engaging a hook like *"wooden sign about a lost family heirloom"* used to draft a beat titled *"Curious Marketplace"* with marketplace ambient. The hook subject was never named.
2. **Beat description was clipped** — `line-clamp-6` cut the active beat's text mid-sentence ("…As you scan the area, a…").

- **Backend `services/storyline_service.py`** (`draft_initial_scene`):
  - System message rewritten to forbid generic ambient openings and require the scene to foreground the literal hook subject.
  - Prompt body now includes a HARD GROUNDING RULES block: title must reference the hook, description's FIRST sentence must name the hook object directly, task must be a verb phrase aimed at the hook subject (e.g. "Read the sign"), and ambient detail can only be texture *around* the subject.
  - Verified live with hook *"wooden sign about a lost family heirloom"* → `title: "The Heirloom Notice"`, beat `title: "The Posted Sign"`, description opens *"The wooden sign hangs at eye level, ink still wet from the morning…"*, task *"Read the sign"*.
- **Frontend `components/ActiveInvestigationPanel.jsx`** (`BeatCard`):
  - Active beat description now uses `overflow-y-auto pr-1 max-h-[260px] sm:max-h-[320px]` so the player can scroll the full text inside the card.
  - Inactive cards keep `line-clamp-6` for visual rhythm.
  - Added `data-testid="beat-description-active"` for testing.

#### Proficiency + Item Cards in the Player's Deck (Feb 2026)
The deck now includes every proficiency and starting item the character owns — not just race/class/background features. Avon's Rogue went from 9 cards → **27 cards**, capturing his full mechanical identity in deck form.
- **Backend `data/character_features.py`**:
  - `CLASS_PROFICIENCIES` — armor / weapons / tools / saving-throw proficiencies for all 12 classes (Rogue gets Light Armor + Simple+Finesse weapons + Thieves' Tools + DEX/INT saves; Fighter gets All Armor + All Weapons + STR/CON saves; etc.).
  - `CLASS_STARTING_EQUIPMENT` — default starter pack for all 12 classes (~5-7 items + gold) mirrored from the frontend `startingEquipment.js`.
  - `SKILL_INFO` — 18 D&D 5e skills with their ability + a one-line evocative blurb for each card description.
- **Backend `services/character_deck.py`**:
  - New deck source: **`proficiency`**. Seeder mints:
    - 1 card per skill in `class.skillProficiencies` (rare, "Skill: Acrobatics — Stay on your feet…").
    - 1 card per saving throw in `CLASS_PROFICIENCIES.saves` (rare, "Save: Dexterity — Add prof bonus…").
    - 1 card per armor type (common, "Armor: Light Armor — Wear without penalty").
    - 1 consolidated weapon-proficiency card (common; full list in description, top 3 in mechanical line).
    - 1 card per tool (deduped from class default + background tool choices).
  - New mints under existing **`item`** source:
    - 1 card per item from `CLASS_STARTING_EQUIPMENT.items` (Rapier, Burglar's Pack, Thieves' Tools, etc.).
    - 1 currency card "Coin Purse — N gp" with the starter gold amount.
  - DM context block adds a new "Proficiencies" line and reorders to keep proficiencies after class features.
- **Frontend `utils/deckRarity.js`**: Added `proficiency` source meta (🎯 teal label "Proficiencies"). Display order: race → language → background → trait → class → proficiency → spell → item → contact → quest → reputation → curse.
- **Verified live (avon — Human Rogue Criminal)** — full 27-card deck:
  - Race (1) · Language (1) · Background (1: Criminal Contact rare) · Trait (3: Ideal/Bond/Flaw) · Class (3: Sneak Attack epic + Thieves' Cant + Expertise) · **Proficiency (10)** · **Item (8)**.
  - All cards mint with stable `art_key` so the player's uploaded art persists across characters/campaigns.
  - DM now sees a proficiency-aware context block every turn — knows the character can speak Common, sneak in light armor, force a door (Athletics), pick a lock (Thieves' Tools), parry with a Rapier, etc.

#### Intent-Driven Campaign Deck + Preview Button (Feb 2026)
The Tone / Focus / Scope / Danger picks on the Campaign Setup screen now actively shape which event templates the DM has available to draft. Each event TYPE (encounter, faction, cultural, etc.) has an affinity weight against each axis, so a Combat-Heroic-City-High game gets a deck heavy on Encounters / Factions / Quests, while a Story-Balanced-Mixed-Medium one leans into Faction / Lore / Quest / Cultural. A new "Preview Campaign Deck" button on the setup screen shows the player exactly what they'll get before committing.
- **Backend `data/event_catalog.py`**:
  - New `TYPE_INTENT_AFFINITY` matrix: 4 axes × 3-4 values × 8 event types = ~104 weighted multipliers (0-2 scale).
  - New `DIFFICULTY_BY_DANGER` table biases card difficulty (Low → easy×2; High → hard×2).
  - `intent_affinity_for(template, intent)` — multiplies all 4 axis weights × difficulty bias for one template.
  - `preview_campaign_deck(intent, top_n=24)` — returns the highest-affinity templates with metadata.
  - `deck_summary_for_intent(intent)` — wraps the preview + per-type counts + catalog totals + EVENT_TYPES metadata.
  - `filter_eligible(...)` extended to accept `intent` and use weighted sampling instead of plain shuffle.
- **Backend `services/world_graph.py`**: `_make_region` and `_seed_events_for_region` now accept `intent` and pass it through to `filter_eligible`. Both `_template_graph` (fallback path) and the LLM-enhanced graph builder thread the intent through. Hint titles for unvisited regions also use intent weighting so even the previews on the world map respect the player's picks.
- **Backend `routers/campaigns.py`**: New `GET /api/campaigns/deck-preview?tone=&focus=&scope=&danger=` endpoint returning the deck summary.
- **Frontend `components/CampaignDeckPreview.jsx`** (NEW): modal showing the live deck. Auto-refetches when any of the 4 intent picks change. Renders intent chips, per-type composition badges, and the top 24 cards with type-styled borders + difficulty + affinity scores + biome / required-faction-race lines.
- **Frontend `pages/CampaignSetup.jsx`**: New **👁️ Preview Campaign Deck** button alongside Generate Campaign. Disabled until all 4 picks are selected. Opens the modal in place.
- **Verified live (Heroic / Combat / City / High)**:
  - `GET /api/campaigns/deck-preview` → 24 cards, composition: 6 Faction · 5 Encounter · 5 Quest · 4 Hazard · 4 Mystery, top card "Frostbitten Raiders" affinity 6.6 (Hard).
  - Switched to Story-Balanced-Mixed-Medium → composition shifted to 6 Faction · 5 Quest · 5 Lore · 3 Cultural · 3 Discovery · 2 Mystery (no Encounters/Hazards), confirming intent affinity flows end-to-end.
  - UI: Click "Preview Campaign Deck" on setup → modal opens with intent chips, type counts, and the affinity-sorted card list with full styling.

#### Roleplay Anchors + Chaos Meter + Curse Drafts (Feb 2026)
The character's Ideal / Bond / Flaw are now first-class deck cards AND drive an always-on chaos meter. Aligned roleplay keeps chaos low; violations raise it. High chaos rolls draft a curse card into the player's deck — concrete narrative consequences for breaking character.
- **Backend `services/character_deck.py`**:
  - New deck source: **`trait`**. The seeder reads `character.background.personality.{ideal, bond, flaw}` and emits 3 rare trait cards titled `Ideal: …`, `Bond: …`, `Flaw: …` with descriptions explaining the chaos consequence.
  - `SOURCES` extended; `deck_context_block` adds a `Roleplay Anchors (Ideal · Bond · Flaw)` section so the DM sees them every turn.
- **Backend `services/roleplay_chaos.py`** (NEW):
  - `evaluate_alignment(character, player_action)` — small `gpt-4o-mini` call that returns `{severity 0-3, axis: ideal|bond|flaw|null, reason: short text}`. Conservative — most actions return 0; only clear contradictions return >0. Honest flaw indulgence (a "Sticky fingers" rogue stealing) is severity 0 by design.
  - `apply_alignment_delta(chaos, severity)` — severity 0 cools chaos by 3; 1/2/3 raise by 4/9/16. Capped 0..100.
  - `chaos_tier(chaos)` — 6 buckets (Calm → Stirring → Agitated → Turbulent → Perilous → Consuming) for UI coloring.
  - `roll_for_curse(chaos)` — chance = `chaos / 200` capped at 35%, no roll below chaos 30. Keeps curses scene-bound rather than drip-fed.
  - `_CURSE_CATALOG` — 12 curse templates (4 common at low chaos, 4 rare, 3 epic, 1 legendary). Descriptions are concrete (Restless Sleep, Witnessed, Hunted by Fate, The Curse of Hollow Sleep, Geas of the Wronged Powers, …) with mechanical effects.
  - `chaos_block_for_dm(chaos)` — tight prompt block telling the DM to subtly tilt the world's reactions to the character based on chaos tier.
- **Backend `routers/lean_dm.py`** (after narration):
  1. `evaluate_alignment` runs against the player's action.
  2. `apply_alignment_delta` updates chaos.
  3. If `severity > 0` AND `roll_for_curse` succeeds → mint a curse card into the player's deck (rarity scaled to chaos tier), attach saved art if any, then **cool chaos by 12** ("punishment landed, pressure released").
  4. Persist new chaos to `world_state.chaos`.
  5. Inject `chaos_block_for_dm` into the system prompt so future turns reflect the meter.
  6. Surface in `world_state_update.chaos = {value, delta, tier, alignment, drafted_curse}`.
- **Frontend `components/CampaignTopBar.jsx`**:
  - New **🔥 Chaos N · Tier** chip with color escalation: emerald (Calm) → lime (Stirring) → amber (Agitated) → orange (Turbulent) → red+pulse (Perilous) → rose+glow+pulse (Consuming).
- **Frontend `components/AdventureLogWithDM.jsx`**:
  - On every turn response, reads `data.world_state_update.chaos`:
    - Violation toast: red `🩸 Bond broken — <reason> (Chaos +N)`.
    - Curse draft toast: `☠️ Curse drafted: <title> (rarity) — <description>` for 8s.
- **End-to-end verified live** (avon Rogue: Honor among thieves / Crew members / Sticky fingers):
  - Aligned theft turn ("help my crew lift a few coins") → severity 0, chaos 0, no curse.
  - Crew betrayal #1 → severity 3, axis=bond, chaos 16, "Betraying the crew profoundly violates their bond".
  - Continued betrayals → chaos climbed 16 → 32 → 48 → 52, tier moved through Stirring → Agitated.
  - At chaos 52 → curse roll succeeded → **`Hunted by Fate (epic)` minted into deck**, chaos cooled to ~40.
  - Frontend: red Bond-broken toast appeared, deck section `deck-section-trait` rendered the 3 trait cards, `chaos-chip` updated live.

#### Player-Uploaded Card Art (MTG-Style Frames) (Feb 2026)
Deck cards now use an MTG-style layout with player-uploaded art in the middle. The title, rarity border, type line, and rules box are auto-generated; the art panel is fully customizable. **Saved art persists across all the player's future characters and campaigns** — once you upload art for "Sneak Attack" or "Criminal Contact", every Rogue or Criminal you'll ever play sees it.
- **Backend `services/character_deck.py`**:
  - New `art_key_for(source, title)` — stable lowercase+slug key (e.g. `class::sneak-attack`, `background::criminal-contact`) so art is shared across all cards with the same identity.
  - DeckCard normalization includes `art_key` and `art_data_url` fields.
  - `attach_saved_art(cards, library)` — mutates cards to attach saved data URLs by key.
- **Backend `routers/character_deck.py`**:
  - New global `card_art_library` MongoDB collection: `{art_key, data_url, source, title, created_at, updated_at}`.
  - `_load_art_library(db)` pulls the full {art_key: data_url} dict on every deck fetch.
  - **`POST /api/characters/{id}/deck/cards/{cardId}/art`** — accepts `{data_url}` (or null to clear). Validates `data:image/...` prefix, enforces ~600 KB cap, upserts into library, propagates the new art to ALL cards in the deck sharing the art_key.
  - GET deck and POST draw both attach saved art on the way out.
- **Frontend `components/CharacterDeck.jsx`** (rewritten with MTG-style frame):
  - Title bar (rarity-colored) with card name + rarity chip.
  - **5:4 aspect-ratio art panel**: when empty, click to upload (`📷 UPLOAD ART · Saved across every character you play`); when filled, hover reveals Replace + Clear buttons.
  - Type line ("🪶 Common Race", "📜 Rare Background", etc.) + per-day badge + uses badge + Use button if applicable.
  - Rules box with description + `⌬ mechanical` line.
  - **Image processing on the frontend** (`fileToResizedDataUrl`): resizes any uploaded file to 512×512 cover-cropped JPEG @ 0.82 quality before upload (~80-200 KB) so payload stays small regardless of input size.
- **End-to-end verified**: Sneak Attack art uploaded + persisted across page reloads via the global library; future Rogue characters in new campaigns will inherit the same artwork without re-upload.

#### Character Deck (Identity & Resources) — Phase 1 (Feb 2026)
The player now has a personal deck of cards built from their character's identity, with rarity tiers, per-day consumables, and DM context injection. Cards auto-seed from race traits, languages, background features, and level-1 class features; the DM reads a compact deck summary every turn to weave features into narration naturally.
- **Backend `data/character_features.py`** (NEW): catalog mirroring 5e — race traits (Darkvision, Fey Ancestry, Relentless Endurance, Breath Weapon, Hellish Resistance, …), background features (Criminal Contact, Position of Privilege, Researcher, Military Rank, …), level-1 class features for all 12 classes (Sneak Attack, Rage, Spellcasting, Lay on Hands, Bardic Inspiration, Pact Magic, …), and 18 D&D languages — each tagged with rarity (`common` / `rare` / `epic` / `legendary`) and `per_day`/`uses_max` where applicable.
- **Backend `services/character_deck.py`** (NEW):
  - `seed_deck_for_character(character)` — pulls race / class / background / languages from the character doc and emits normalized DeckCard dicts.
  - `merge_deck(existing, fresh)` — union by `(source, title)` so re-seeding on every turn is idempotent; auto-source cards that disappear get marked `lost` (audit trail).
  - `deck_context_block(deck)` — tight one-paragraph summary the DM gets every turn ("Race: Versatile · Languages: Common · Background: Criminal Contact · Class: Sneak Attack (epic) · Expertise · Thieves' Cant"). Calls out epic/legendary rarity, per-day uses, and reminds the LLM to weave them naturally instead of reciting.
- **Backend `routers/character_deck.py`** (NEW):
  - `GET  /api/characters/{id}/deck` — auto-seeds + returns the deck + context block.
  - `POST /api/characters/{id}/deck/cards/{cardId}/use` — decrement uses_remaining or mark spent.
  - `POST /api/characters/{id}/deck/long-rest` — restore per-day uses.
  - `POST /api/characters/{id}/deck/draw` — append a new card from a quest/curse/item event (any source from the taxonomy).
- **Backend `routers/lean_dm.py`**: every turn loads (or seeds) the character's deck, merges with current character state (handles level-up additions), persists, and injects `deck_context_block` into the system prompt right after passive Perception. The DM now reads what the character has every turn.
- **Frontend `utils/deckRarity.js`** (NEW): rarity → Tailwind chip + border + glow mapping (common=stone, rare=sky+glow, epic=fuchsia+strong-glow, legendary=amber+huge-glow); source → icon + label mapping.
- **Frontend `components/CharacterDeck.jsx`** (NEW): right-side Sheet opened from a new fuchsia **🪶 Deck ✦ N** pill on the `CampaignTopBar`. Cards are grouped by source (Race / Languages / Background / Class / Spells / Items / Contacts / Rewards / Reputation / Curses), sorted by rarity (legendary first), and rendered with rarity-tinted borders + glows. Per-day cards show `X/Y` uses; `Use` button spends one. **Long Rest** button at the top restores per-day uses with a toast.
- **End-to-end verified live (avon — Human Rogue Criminal)**:
  - Auto-seeded deck: 6 cards (Versatile, Common, Criminal Contact, Sneak Attack, Thieves' Cant, Expertise) — every rarity tier visible.
  - Player turn "I look for thieves cant marks on the alley walls and ask my contact in the syndicate" → DM narration weaves in Thieves' Cant ("subtle blend of lines and curves that signify safe passage and hidden dealings") AND Criminal Contact ("Your contact in the Black Market Syndicate, a wiry figure with a quick smile") — both flowing naturally from the deck context.

#### Passive Perception–Aware Narration (Feb 2026)
The DM now reads the character's 5e passive Perception and calibrates how informative the scene narration is. Sharp-eyed characters get more cues + opportunity flags; average characters see the obvious + one modest detail; oblivious characters need active checks for almost everything.
- **Backend `services/dnd_rules.py`**:
  - `proficiency_bonus_for_level(level)` — standard 5e PB scale (lvl 1-4: +2, 5-8: +3, …, 17-20: +6).
  - `compute_passive_perception(character)` → `{score, wis_mod, proficient, prof_bonus, tier}`. Formula = 10 + WIS mod + (PB if proficient in Perception). Tier buckets:
    - oblivious  (<=10), average (11-13), sharp (14-16), keen (17-19), uncanny (>=20)
  - `passive_perception_block(character)` — tight DM-prompt section telling the LLM how dense the narration should be for this tier (specific guidance per tier on what cues to include and when to flag opportunities).
- **Backend `routers/lean_dm.py`**: `_build_system_prompt` injects `passive_perception_block` into the DM prompt right after time-of-day. `world_state_update` in the response now carries `passive_perception: {score, tier, …}` so the UI can display it.
- **Backend `services/storyline_service.py`**: Both `draft_initial_scene` and `generate_next_scene` inject the same passive-perception block into their prompts so storyline scene cards inherit the same calibration.
- **Frontend `components/CampaignTopBar.jsx`**: New chip (`data-testid="passive-perception-chip"`) showing **👁️ PP 13 · Average** with tier-tinted color (oblivious=stone, average=sky, sharp=cyan, keen=emerald, uncanny=fuchsia). Tooltip reveals the formula breakdown ("10 + WIS mod (+1) + proficiency (+2)").
- **End-to-end verified live (avon — WIS 12, Perception-proficient Rogue, PP 13 "average")**: DM narration of Avon scanning rooftops surfaced obvious details (formations, moss, shadows) AND 1-2 modest cues (loose tiles indicating a route, distant scuffle, figure disappearing) — exactly the "average" tier prescription. No active check was needed for those cues; subtler ones still require rolls.

#### Typed Event Cards + Region Presence (Feb 2026)
The world deck now has 8 distinct event types, each with unique color + border styling, drafted from a static catalog filtered by per-region presence (factions + dominant races) so cards stay thematically tied to who actually operates in each region.
- **Backend `data/event_catalog.py`** (NEW):
  - 8 `EVENT_TYPES` with color/border/icon: encounter (red, solid-thick) · faction (purple, dashed) · cultural (emerald, double) · discovery (amber, solid-glow) · mystery (indigo, dotted) · hazard (slate, jagged-dashed) · lore (sky, solid-thin) · quest (rose, solid-bold).
  - ~38-template static catalog spread across the 8 types and 11 biomes. Each template carries `requires` tags (e.g. `faction:criminal`, `race:tiefling`, `race:any-non-human`).
  - `filter_eligible(region_tags, count)` — subset-match filter that biases toward type variety.
- **Backend `services/world_graph.py`**:
  - **Region presence**: each region now carries `present_factions: [{name, description, archetypes}]` and `dominant_races: [...]` fields. Picked at world generation by `_pick_region_factions` (1-2 from world.factions, starter gets up to 3) + `_pick_region_races` (player's race + biome-biased extras). Factions live at `world.setting.factions` in current campaigns; archetype is heuristically inferred from name/description (criminal / merchant / military / religious / scholarly / arcane / smuggler / guild / noble / native).
  - **Region-aware event seeding**: `_seed_events_for_region` filters the catalog by region tags (biome + factions + races) and picks `count` typed events with type-variety bias. Each card carries `drafted_because: [reasons]` (e.g. "The Black Market Syndicate operates here", "Tiefling community in this region").
  - **LLM path** updated to ask for `event_type` per event and to top-up via the region-aware seeder; `hydrate_region` (lazy expansion on first visit) gets a faction+race context block so neighbor events involve those entities.
- **Frontend `utils/eventTypes.js`** (NEW): mirrors the 8 types with Tailwind classes for border + ring + chip styling.
- **Frontend `components/WorldMapGraph.jsx`**:
  - Region panel shows two new chip rows: purple Faction badges + emerald Race badges (top of detail card).
  - Each `EventCard` now uses its type's distinctive left border + colored type chip with icon + accent title color; below the description a small italic "Drafted because: …" line surfaces the reasons the catalog picked this card for this region.
- **End-to-end verified live (Gate of Emberfall starter)**: All 3 world factions present (Black Market Syndicate · Guild of Scribes · Wardens of Emberfall) + 3 races (Human · Tiefling · Half-elf). Drafted deck spread perfectly across 5 types: Quest Hook · Cultural · Mystery · Faction Plot · Discovery — each with its unique border style.

#### Time-of-Day Tracking (Feb 2026)
Lightweight, single-integer time-of-day system: each campaign carries a `world_state.clock_hour` (0-23) that's mapped to 9 named periods (Dawn / Morning / Midday / Afternoon / Late Afternoon / Dusk / Evening / Night / Midnight). The DM is fed the current period in its system prompt so narration matches the hour, and the clock auto-advances based on a regex of the player's action.
- **Backend `services/time_service.py`** (NEW):
  - `bucket_for_hour(h)` → `{key, label, icon, hour}` (e.g. `{'morning', 'Morning', '☀️', 9}`).
  - `time_context_block(h)` → tight DM-prompt section telling the LLM to ground sensory cues in this period (lanterns being lit, market full, grey light, etc.) — never quote the hour as a number.
  - `estimate_time_advance(player_action, narration)` → 0..8h heuristic: long-rest/sleep keywords = 8h; travel = 3h; thorough/stake-out = 2h; short rest = 1h; default = 0 (chat/glance/single check). No extra LLM call.
  - `advance_clock(cur, delta)` → wraps mod-24 with a 12h-per-turn safety clamp.
- **Backend `routers/lean_dm.py`**:
  - `_build_system_prompt` now takes `clock_hour` and injects `time_context_block` into the DM prompt right after the biome block.
  - `dm_action`: reads `clock_hour` from campaign, builds the prompt, runs the LLM, then applies `estimate_time_advance` to the player's action + the narration → updates campaign `world_state.clock_hour` → returns `world_state_update: {clock_hour, time_of_day (string key, legacy compat), time_bucket (full object), time_advanced_hours}` so the frontend can display it without breaking legacy code.
- **Backend `services/storyline_service.py`**:
  - `draft_initial_scene` and `generate_next_scene` both now read the campaign's clock and inject `time_context_block` into their prompts so storyline scene cards match the same period as the DM.
  - Each generated beat is tagged with a `time_of_day` object (key/label/icon/hour) for the UI.
- **Frontend `components/CampaignTopBar.jsx`**:
  - New compact indigo pill (`data-testid="time-of-day-chip"`) sitting alongside Realm + Quests, showing the icon + label (e.g. `🌆 Dusk`). Tooltip reveals the in-fiction hour for the curious.
- **Frontend `components/ActiveInvestigationPanel.jsx`**:
  - Each scene card's header now shows a Time-of-Day badge alongside the Beat counter.
- **End-to-end verified live**:
  - Turn 1 ("I glance around the alley") → `time_advanced_hours: 0` — clock holds at 9:00 Morning ☀️.
  - Turn 2 ("I travel to the docks") → `+3h` → 12:00 Midday 🌞.
  - Turn 3 ("I take a long rest until morning") → `+8h` → 20:00 Dusk 🌆.
  - Storyline draft at 9am with hook "a metal latch on a rotting door" → DM grounded the description in morning light naturally; beat tagged `time_of_day: {key:'morning', label:'Morning', icon:'☀️', hour:9}`.

#### Scene-Driven Open-Ended Storylines (Feb 2026)
Replaced the pre-scripted "draft 3-5 forced-check beats" model with a dynamic scene-loop where the DM generates each next beat based on what the player actually does. Player drives via "What do you do?" textarea — the DM narrates the consequence + new situation, and only requests a check when the action genuinely calls for one.
- **Backend `services/storyline_service.py`**:
  - **New `draft_initial_scene(...)`** — drafts ONLY Beat 1 from the engaged hook. The card is a Mercer-cinematic SCENE the player has stepped into (what they see/hear/smell), with a single OPTIONAL suggested check. Replaces `draft_storyline` for new storylines (legacy multi-beat draft kept for backward compat).
  - **New `generate_next_scene(campaign, character, storyline, player_action_summary)`** — after the current beat resolves (via roll, creative approach, or skip), the DM judges: resolve the storyline now (returns `is_final: true` + epilogue) OR draft the NEXT scene card (narrates the consequence of the just-played action AND the new situation). Suggested check is optional per scene; `dc=0` with `roll_optional=true` for pure narrative beats. Hard cap of 7 beats.
  - **`advance_storyline()`** updated: open-ended storylines no longer auto-complete on "last beat" — the caller (router) is responsible for either appending the next dynamic beat or marking complete.
- **Backend `routers/storylines.py` + `lean_dm.py`**:
  - `POST /draft` and the engagement-detection auto-draft both now call `draft_initial_scene` and tag the storyline `open_ended: True`.
  - `POST /resolve` and `POST /creative` chain into `generate_next_scene` for open-ended storylines: append new beat or finalize. Total DC accumulates dynamically for reward scaling.
  - New `_format_action_summary` helper feeds the LLM a tight one-paragraph view of "Beat just resolved + outcome + roll/creative/skip detail + complication" so the next scene is grounded in actual play.
  - Quest card description drops "Beat X of N" framing for open-ended storylines.
- **Frontend `ActiveInvestigationPanel.jsx`**:
  - Action bar reordered: **"What do you do?"** (fuchsia, primary CTA) → **"Roll d20+X · suggested"** (amber, optional) → **"Skip · Proceed"** (new, action beats only).
  - Roll button auto-disables and re-labels to "No check needed" when the LLM marked the beat `roll_optional=true`.
  - Skip button calls `/resolve` with `outcome: "skipped"`; the DM narrates a trivial outcome and generates the next scene.
  - Creative dialog reframed as "What do you do?" with prompt: "Describe your action in this scene. The DM will narrate the outcome and continue the story — a check only triggers if your action genuinely calls for one."
- **End-to-end verified live (avon Rogue)**:
  - Player engaged hook → drafted exactly **1 scene card** ("Investigation at the Warehouse" with mood narration + DC 12 Investigation suggested).
  - Resolved with `passed/15` → DM generated **Beat 2: "Threshold of Secrets"** ("With a firm grasp, Avon pulls the rotting door open, revealing…") with **Perception** picked as the natural follow-up.
  - Used creative approach "I quietly slip behind the crates and listen" → DM judged `partial`, narrated the gleam of eyes through the gaps, generated **Beat 3: "Eyes in the Shadows"** with **Stealth** as the natural next check (driven by player's stealth action, not a forced random check).
- **Tests**: `test_storylines.py` updated — `test_draft_returns_storyline_with_beats` expects 1 beat + `open_ended: True`; new `test_resolve_grows_beats_until_complete` resolves up to 8 times and asserts the chain grows or completes naturally with proper reward shape (8/9 storyline tests pass; 1 pre-existing flaky engagement-matcher test unrelated to this rewrite).

#### Compact Realm + Quests Top Bar (Feb 2026)
Replaced the chunky inline collapsible `WorldInfoPanel` and `QuestLogPanel` cards with two compact pill buttons in a top bar above the Adventure Log narration. Each opens a right-side slide-over `Sheet` containing the full panel content, freeing ~270-400px of vertical real-estate for the chat.
- **New `components/CampaignTopBar.jsx`** — renders two pills:
  - **Realm pill** (`data-testid="realm-button"`): Globe icon + realm name + starting town subtitle. Clicking opens the Realm Sheet with the full WorldInfoPanel body.
  - **Quests pill** (`data-testid="quests-button"`): Scroll icon + active-count badge. Clicking opens the Quest Log Sheet with the full QuestLogPanel body (active + completed/failed toggle, mark-complete/mark-failed actions preserved).
- **`WorldInfoPanel.jsx` + `QuestLogPanel.jsx`** got an `embedded` prop that skips the inline header/toggle chrome and always renders the body — caller (the Sheet) owns the title/close.
- **`AdventureLogWithDM.jsx`** now mounts `CampaignTopBar` instead of the two inline panels. The compact bar sits flush above the chronicler card.
- The papyrus theme assimilates the buttons aesthetically (parchment-tan backgrounds, sepia ink, blue/amber accents preserved on icons via wildcard CSS).
- Verified live on the avon Rogue's loaded campaign: Realm Sheet renders Era / Tension / 3 Factions / 2 Recent History entries; Quest Sheet renders 52 active quests with full expand/collapse behavior. Vertical real-estate freed — the Chronicle sits right below the top bar instead of being pushed below two card stacks.

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
