# JARVIS Plan — dnd-ai-clean

## 0. Mechanics

- **Character Creation (V2 Wizard)** — Multi-step guided wizard for creating a new character including race, class, background, stats, and cantrips. | `frontend\src\components\CharacterCreation.jsx` approx. line 22; `frontend\src\App.js` route `/character-v2`
- **Race Selection** — Player selects a race (and optional subrace) which applies racial traits and language bonuses to the character. | `frontend\src\components\CharacterCreation.jsx` approx. line 283, 289
- **Class Selection** — Player selects a character class that determines abilities, hit dice, and spell access. | `frontend\src\components\CharacterCreation.jsx` approx. line 262
- **Ability Score / Stat Generation (StatForge)** — Rolls 4d6-drop-lowest arrays, allows assignment of rolled scores to the six core ability scores (STR/DEX/CON/INT/WIS/CHA). | `frontend\src\components\StatForge.jsx` approx. line 32, 39, 86
- **Stat Modifier Calculation** — Derives standard D&D ability score modifiers (floor((score-10)/2)) and proficiency bonus from level. | `frontend\src\components\CharacterSheet.jsx` approx. line 12; `frontend\src\components\CharacterSidebar.jsx` approx. line 44
- **Cantrip Selection** — Player picks a fixed number of cantrips from a class list during character creation. | `frontend\src\components\CantripSelection.jsx` approx. line 11
- **Relationship Generation** — AI-generates NPC relationships for the new character during creation. | `frontend\src\components\CharacterCreation.jsx` approx. line 217
- **Instant Start / Skip Character Creation** — Allows skipping detailed setup and jumping directly to adventure with a pre-built character. | `frontend\src\components\StartScreen.jsx` approx. line 76, 80
- **AI-Generated Character (Guided Mode)** — Backend generates a character automatically based on guided prompts. | `frontend\src\components\StartScreen.jsx` approx. line 31
- **Character Reroll** — Re-randomises the auto-generated character without leaving the start screen. | `frontend\src\components\StartScreen.jsx` approx. line 72
- **Campaign Setup & Generation** — Wizard that sets up a new campaign and triggers AI generation of the campaign world/storyline. | `frontend\src\App.js` routes `/campaign-setup`, `/campaign-generate`
- **Mission Type Selection** — Player/DM picks a structured mission archetype (e.g. Heist) which provides phased beats for the storyline. | `frontend\src\components\MissionTypePicker.jsx` approx. line 22, 62, 66
- **Mission Phase Tracking** — Displays the current mission type and active phase/beat index within the running storyline. | `frontend\src\components\MissionPhaseBadge.jsx` approx. line 19
- **AI Narrative Engine (AdventureLogWithDM)** — Sends player actions to the backend AI and streams the DM narration response into the adventure log. | `frontend\src\components\AdventureLogWithDM.jsx` approx. line 979, 1340
- **Player Action / Intent Toggle** — Player switches between Roleplay, Explore, and Combat intent modes to shape AI responses. | `frontend\src\components\AdventureLogWithDM.jsx` approx. line 2748 (`IntentToggle`); `frontend\src\components\FocusedRPG.jsx` approx. line 160
- **Action Dock (Quick Actions)** — Provides hotkey-driven primary and secondary action chips (e.g. Attack, Search, Talk, Rest) that trigger predefined commands. | `frontend\src\components\ActionDock.jsx` approx. line 22, 43, 63, 92
- **Free-Text Player Input** — Player types arbitrary commands/messages in a chat input that are sent to the AI DM. | `frontend\src\components\AdventureLogWithDM.jsx` approx. line 511; `frontend\src\components\GameChat.jsx` approx. line 268
- **Narrative Option Clicks** — AI response includes clickable narrative options that the player can select to advance the story. | `frontend\src\components\AdventureLogWithDM.jsx` approx. line 1499
- **Cinematic Intro Sequence** — Triggers an AI-generated opening cinematic narration at the start of a new campaign. | `frontend\src\components\AdventureLogWithDM.jsx` approx. line 891
- **Ability / Skill Check Requests** — AI DM requests a specific ability or skill check from the player mid-narrative. | `frontend\src\components\CheckRequestCard.jsx` approx. line 9; `frontend\src\components\CheckRollPanel.jsx` approx. line 8
- **Dice Roll (d20 + Modifier)** — Player rolls a d20 with their relevant modifier; supports advantage/disadvantage; result is sent back to the AI. | `frontend\src\components\CheckRollPanel.jsx` approx. line 38, 99, 146; `frontend\src\components\AdventureLogWithDM.jsx` approx. line 1575
- **Auto-Roll** — Automatically performs a dice roll on behalf of the player for a requested check. | `frontend\src\components\CheckRequestCard.jsx` approx. line 60
- **Manual Roll Override** — Player may enter a custom roll value instead of using the in-app roller. | `frontend\src\components\CheckRequestCard.jsx` approx. line 69; `frontend\src\components\CheckRollPanel.jsx` approx. line 99
- **Roll Result Card** — Displays the outcome of a completed dice roll including the roll total, DC, and pass/fail. | `frontend\src\components\RollResultCard.jsx` approx. line 7
- **Advantage / Disadvantage** — Check roll panel supports rolling twice and taking the higher or lower result. | `frontend\src\components\CheckRollPanel.jsx` approx. line 154
- **Combat System (CombatScreen)** — Full turn-based combat with initiative order, participant tokens, action menus, and narration. | `frontend\src\components\CombatScreen.jsx` approx. line 118
- **Combat HUD** — Real-time display of HP, conditions, spell slots, and short-rest pips during combat. | `frontend\src\components\CombatHUD.jsx` approx. line 68
- **Battlefield Grid** — Visual grid displaying combatant tokens, movement range, AoO ring, and distance calculations. | `frontend\src\components\BattlefieldGrid.jsx` approx. line 45, 49, 54, 65, 84
- **Combat Narration Popup** — Shows AI-generated flavour narration and mechanical breakdown after each combat action. | `frontend\src\components\CombatNarrationPopup.jsx` approx. line 11
- **Battlefield Condition Cards** — Draggable/inspectable cards representing battlefield environmental conditions affecting combat. | `frontend\src\components\BattlefieldConditionCard.jsx` approx. line 97
- **Enemy Library** — DM-facing panel listing available enemies with CR, HP bars, and a button to add them to the encounter. | `frontend\src\components\EnemyLibraryPanel.jsx` approx. line 61, 132
- **Target Mode** — Player enters a targeting mode (with a banner) to select a specific enemy or entity for an action. | `frontend\src\components\TargetModeBanner.jsx` approx. line 15, 52
- **Targeted Search** — Player submits a directed search query targeting a specific entity or location in the narrative. | `frontend\src\components\AdventureLogWithDM.jsx` approx. line 178
- **Defeat / Death Modal** — Shown when the player character reaches 0 HP; applies HP restore to 50%, injury, and optional XP penalty. | `frontend\src\components\DefeatModal.jsx` approx. line (component body)
- **Conditions System** — Characters can gain/lose status conditions (e.g. Poisoned, Blinded) that affect gameplay; editable via StateModifierPanel. | `frontend\src\components\StateModifierPanel.jsx` approx. line 35, 43; `frontend\src\components\CombatHUD.jsx` approx. line 19
- **Condition Interaction Modal** — Modal allowing a d20 roll to interact with or attempt to remove an active condition. | `frontend\src\components\ConditionInteractionModal.jsx` approx. line 59, 73
- **HP / Damage / Healing** — Player can take damage or be healed; HP tracked in state, visualised in sidebar and HUD. | `frontend\src\components\StateModifierPanel.jsx` approx. line 10, 17; `frontend\src\components\CombatHUD.jsx` approx. line 76
- **Long Rest** — Restores HP and resets certain abilities/spell slots for the character. | `frontend\src\components\CharacterDeck.jsx` approx. line 57
- **Short Rest (Rest Pips)** — Tracked short-rest uses displayed as pips in the Combat HUD. | `frontend\src\components\CombatHUD.jsx` approx. line 48
- **Spell Slot Tracking** — Remaining and maximum spell slots per level displayed as pips in the Combat HUD. | `frontend\src\components\CombatHUD.jsx` approx. line 25
- **Character Deck (Ability Cards)** — Card-based ability system where each character ability is a usable card; supports use, art upload/clear. | `frontend\src\components\CharacterDeck.jsx` approx. line 32, 74, 90, 118
- **Inventory Management** — Player can view, use, and track items; calculates item weight vs carry capacity. | `frontend\src\components\Inventory.jsx` approx. line 11, 68, 105, 117, 125
- **Loot Panel** — After combat/events, player sees enemy loot and can selectively claim items. | `frontend\src\components\LootPanel.jsx` approx. line 145
- **Experience Points (XP) & Levelling** — XP is tracked and displayed on an XP bar; reaching thresholds triggers level-up flow. | `frontend\src\components\XPBar.jsx` approx. line 8
- **Level-Up Screen** — Player chooses HP increase method (roll or average), allocates Ability Score Improvements (ASIs), and applies new level stats. | `frontend\src\components\LevelUpScreen.jsx` approx. line 19, 34, 41, 47
- **HP Roll on Level-Up** — Player rolls their class hit die for HP increase or chooses the average. | `frontend\src\components\LevelUpScreen.jsx` approx. line 34, 41
- **Ability Score Improvement (ASI)** — At eligible levels, player allocates +1/+2 to ability scores. | `frontend\src\components\LevelUpScreen.jsx` approx. line 47, 59
- **World Map (Region Graph)** — Interactive graph of world regions; player can travel to regions and view/accept/dismiss regional events. | `frontend\src\components\WorldMapGraph.jsx` approx. line 41, 72, 113, 169
- **Travel / Location Change** — Player selects a region to travel to; supports walk and other travel modes; updates current location. | `frontend\src\components\WorldMapGraph.jsx` approx. line 72; `frontend\src\components\GameChat.jsx` approx. line 179
- **World Map (Visual)** — Alternative visual world map showing region types with icons and colour coding. | `frontend\src\components\WorldMap.jsx` approx. line 9
- **Regional Events (Accept/Dismiss)** — Dynamic events appear in regions; player can accept (start quest) or dismiss them. | `frontend\src\components\WorldMapGraph.jsx` approx. line 113, 169, 537
- **Quest Log** — Tracks active, completed, and failed quests with objectives and progress indicators. | `frontend\src\components\QuestLogPanel.jsx` approx. line 7, 16
- **Quest Detail Modal** — Full-detail view for a quest including leads, entity links, and status management. | `frontend\src\components\QuestDetailModal.jsx` approx. line 28
- **Pin as Quest** — Player can pin a narrative beat directly from the adventure log as a new quest entry. | `frontend\src\components\AdventureLogWithDM.jsx` approx. line 818
- **Quest Status Update** — Player or system can update a quest's status (e.g. active → completed). | `frontend\src\components\AdventureLogWithDM.jsx` approx. line 869; `frontend\src\components\QuestLogPanel.jsx` approx. line (onUpdateStatus prop)
- **Campaign Log Panel** — Tabbed log of narrative leads, knowledge cards, and campaign events with filter pills and pinning. | `frontend\src\components\CampaignLogPanel.jsx` approx. line 213
- **Knowledge Cards / Pinned Cards** — Narrative knowledge items (NPCs, locations, lore) that can be pinned for quick reference. | `frontend\src\components\campaignLog\index.js` (exports `KnowledgeCard`, `usePinnedCards`)
- **NPC Dialogue Stream** — Dedicated streaming dialogue panel for conversations with specific NPCs. | `frontend\src\components\NpcDialogueStream.jsx` approx. line 30, 44
- **NPC Mention Highlighting** — Parses `[[npc_name]]` tags in narration text and renders them as clickable NPC badges. | `frontend\src\components\NPCMentionHighlighter.jsx` approx. line (component body)
- **Entity Profile Panel** — Full profile view for an entity (NPC, location, faction, item) loaded from the backend; supports notes CRUD. | `frontend\src\components\EntityProfilePanel.jsx` approx. line 54, 89, 116, 137
- **Entity Quick Inspect** — Hover/inline quick-view panel for entities (NPC, location, faction, item) without leaving the current screen. | `frontend\src\components\EntityQuickInspect.jsx` approx. line 28, 68, 108, 166, 211
- **Entity Link / Hook Span** — Inline clickable text spans for entities and narrative hooks within narration text. | `frontend\src\components\EntityLink.jsx` approx. line 50, 86
- **Active Investigation Panel** — Dedicated panel for resolving structured investigation storylines with roll-based outcomes, press-on, push-through, and creative approach options. | `frontend\src\components\ActiveInvestigationPanel.jsx` approx. line 150, 228, 363, 380, 390
- **Storyline Reward Modal** — Modal shown when an investigation/storyline completes, displaying rewards. | `frontend\src\components\ActiveInvestigationPanel.jsx` approx. line 672
- **Paused Threads Panel** — Shows paused/expired storyline threads that can be resumed by the player. | `frontend\src\components\PausedThreadsPanel.jsx` approx. line 44, 93
- **Canon Timeline** — Visual timeline of canonised campaign scenes; scenes can be viewed and referenced. | `frontend\src\components\CanonTimelinePanel.jsx` approx. line 83
- **Canon Bar** — Compact top bar showing the current canon scene count, updating live. | `frontend\src\components\CanonBar.jsx` approx. line 19
- **Canon References Footer** — Footer under each DM narration beat listing the canon scenes the narration honours, with clickable chips. | `frontend\src\components\CanonReferences.jsx` approx. line (component body)
- **Remember Beat (Canonisation)** — Player marks a narrative beat as canon, giving it a title and type for the canon timeline. | `frontend\src\components\AdventureLogWithDM.jsx` approx. line 704, 714; `frontend\src\components\RememberCardDialog.jsx` approx. line 42
- **Beat Reaction** — Player can react (e.g. like/dislike) to individual DM narration beats to provide feedback signals. | `frontend\src\components\AdventureLogWithDM.jsx` approx. line 764
- **Scene Report** — Player can report a scene with notes and tags for DM review or moderation. | `frontend\src\components\AdventureLogWithDM.jsx` approx. line 650, 660; `frontend\src\components\SceneReportDialog.jsx` approx. line 49
- **Narration Audio Playback (TTS)** — Generates and plays AI text-to-speech narration audio for adventure log messages. | `frontend\src\components\NarrationAudioPlayer.jsx` approx. line (component body); `frontend\src\components\AdventureLogWithDM.jsx` approx. line 613
- **TTS Enable/Disable Toggle** — In-game escape menu setting to enable or disable text-to-speech narration. | `frontend\src\components\GameEscapeMenu.jsx` approx. line (ttsEnabled/onTTSToggle props)
- **Narrator Tone Selection** — Player selects the narrative tone (Balanced, Heroic, Gritty, Dark, Comedic); some tones locked behind paid plan. | `frontend\src\components\ToneSelector.jsx` approx. line (component body); `frontend\src\components\GameEscapeMenu.jsx` approx. line (narratorTone prop)
- **Font Size Settings** — In-game escape menu setting to switch between font-size presets for accessibility. | `frontend\src\components\GameEscapeMenu.jsx` approx. line (FontSizeContext usage)
- **DM Notebook** — DM-facing panel for storing, editing, and deleting lesson/note cards tied to a campaign. | `frontend\src\components\DMNotebookPanel.jsx` approx. line 309, 333, 348
- **DM Tools Panel (CombatScreen)** — In-combat DM tooling panel for managing enemies and battlefield conditions. | `frontend\src\components\CombatScreen.jsx` approx. line 361
- **Behavior Tree Editor** — Visual node-based editor for authoring and simulating NPC AI behavior trees. | `frontend\src\components\BehaviorTreeEditor.jsx` approx. line 403, 460
- **Behavior Tree Simulation** — Runs a simulation of a saved behavior tree to test NPC AI logic. | `frontend\src\components\BehaviorTreeEditor.jsx` approx. line 330, 336
- **Pressure Dashboard** — DM-facing dashboard showing the Living Campaign Pressure Engine metrics for a campaign. | `frontend\src\App.js` route `/pressure-dashboard`
- **Campaign Deck Preview** — Preview panel for the cards/deck associated with a campaign intent. | `frontend\src\components\CampaignDeckPreview.jsx` approx. line 20
- **Session Recap Modal** — Shows an AI-generated recap of the current campaign session. | `frontend\src\components\SessionRecapModal.jsx` approx. line 6
- **Auto-Save** — Game state is automatically saved to the server after actions/events/scenes; indicator pulses briefly. | `frontend\src\components\AutoSaveIndicator.jsx` approx. line (component body); `frontend\src\components\RPGGame.jsx` approx. line 571
- **Save / Load (Session Core / Legacy Hydration)** — Zustand store is hydrated from legacy localStorage on app mount; campaign can be continued from the main menu. | `frontend\src\App.js` approx. line (useEffect hydrateFromLegacyStorage); `frontend\src\components\RPGGame.jsx` approx. line 222
- **Continue Campaign / Load Last Campaign** — Main menu allows resuming an existing campaign by loading its saved state from the server. | `frontend\src\components\MainMenu.jsx` approx. line 103; `frontend\src\components\RPGGame.jsx` approx. line 628
- **New Campaign Confirmation** — Main menu prompts the player to confirm before overwriting an existing campaign with a new one. | `frontend\src\components\MainMenu.jsx` approx. line 65
- **Character Portrait Generation (AI)** — Triggers AI generation of a character portrait; polls until the image is ready. | `frontend\src\components\RPGGame.jsx` approx. line 421
- **Portrait Refresh / Upload** — Player can refresh or upload custom artwork for their character portrait. | `frontend\src\components\CharacterDeck.jsx` approx. line 90; `frontend\src\components\FocusedRPG.jsx` approx. line 35
- **Character Sidebar** — Collapsible panel showing full character stats, modifiers, skills, and conditions during play. | `frontend\src\components\CharacterSidebar.jsx` approx. line 22, 53
- **Character Sheet View** — Read-only stat block view of the character including ability scores, proficiency bonus, and skills. | `frontend\src\components\CharacterSheet.jsx` approx. line 9
- **Info Drawer** — Slide-out drawer giving access to character stats, inventory, and game log from a single panel. | `frontend\src\components\InfoDrawer.jsx` approx. line 12
- **World Info Panel** — Displays world blueprint details and current location description. | `frontend\src\components\WorldInfoPanel.jsx` approx. line 4
- **Time of Day / Weather State** — StateModifier panel exposes controls to change in-game time and weather, affecting light level and atmosphere. | `frontend\src\components\StateModifierPanel.jsx` approx. line 49, 53; `frontend\src\components\CombatScreen.jsx` approx. line 26
- **Light Level Derivation** — Derives a light-level chip (e.g. bright/dim/dark) from time of day and location name for combat atmosphere. | `frontend\src\components\CombatScreen.jsx` approx. line 26, 42
- **Lantern / Equipment State** — Player can equip a lantern (and presumably other items) which modifies world state. | `frontend\src\components\StateModifierPanel.jsx` approx. line 24
- **Tutorial Overlay** — Step-by-step tutorial overlay driven by a TutorialContext, triggered by custom events. | `frontend\src\components\TutorialOverlay.jsx` approx. line 108; `frontend\src\App.js` (TutorialProvider)
- **Game Escape Menu (Pause)** — ESC-key pause menu with Continue, Settings (font size, tone, TTS), DM Notebook, Canon Timeline, Session Recap, and Main Menu options. | `frontend\src\components\GameEscapeMenu.jsx` approx. line (component body)
- **Turn Limit / Usage Metering** — Tracks turns used vs plan limit; fires a `dnd:turn_limit` event at the 402 threshold and shows an upgrade modal. | `frontend\src\App.js` approx. line (TurnLimitModal); `frontend\src\components\UsageBanner.jsx` approx. line (component body)
- **Usage Banner** — Displays remaining turns and a colour-coded progress bar with an upgrade button when nearing the limit. | `frontend\src\components\UsageBanner.jsx` approx. line (component body)
- **Pricing / Plan Upgrade** — Navigates to a Pricing page where players can upgrade their subscription plan. | `frontend\src\App.js` route `/pricing`
- **Authentication (Login / Auth Context)** — Login page and AuthContext provide user identity and plan information used throughout the app. | `frontend\src\App.js` route `/login`; `frontend\src\components\UsageBanner.jsx` approx. line (useAuth)
- **Feedback Submission** — Global feedback button lets players submit feedback from anywhere in the app. | `frontend\src\components\FeedbackButton.jsx` approx. line 36, 70
- **Error Boundary / Crash Recovery** — Wraps the entire app; on error

## 4. Test Cases

### TC-001 — Onboarding / Initial Navigation
- Precondition: Browser opens the game URL (landing page visible)
- Steps: 1. Observe the Landing page is displayed 2. Click "Play" or primary CTA button 3. Navigate through any login/character selection to reach MainMenu
- Expected result: MainMenu is visible with options for "New Campaign" and "Continue Campaign"
- Assertion: VISUAL_CHECK: MainMenu component is rendered with visible campaign action buttons, not the Landing page

---

### TC-002 — Character Creation Workflow
- Precondition: User has completed TC-001 and is on MainMenu
- Steps: 1. Click "New Campaign" button 2. Follow CharacterCreationV2 wizard (select class, stats, abilities, cantrips) 3. Complete the character creation form
- Expected result: Character is created and user is navigated to campaign setup or character preview
- Assertion: VISUAL_CHECK: CharacterSheet or CharacterPreview is displayed showing created character name, class, and stats

---

### TC-003 — Campaign Generation and Setup
- Precondition: User has completed TC-002 (character created)
- Steps: 1. Proceed through CampaignSetup page 2. Enter campaign details (name, tone, mission type) 3. Click "Generate Campaign" to trigger CampaignGenerate
- Expected result: Campaign is generated and user enters the game adventure
- Assertion: VISUAL_CHECK: RPGGame/AdventureRoute loads with BattlefieldGrid, CombatHUD, and adventure narrative visible

---

### TC-004 — Combat Round Execution
- Precondition: User has completed TC-003 and is in active adventure (CombatScreen visible)
- Steps: 1. Observe enemy on BattlefieldGrid 2. Click or select target using ActionDock 3. Select action (spell, attack, ability) and execute
- Expected result: Roll dialog appears, roll result is displayed, enemy takes damage or effect applies
- Assertion: VISUAL_CHECK: RollResultCard displays roll total; enemy health or condition updates on BattlefieldGrid or CombatHUD

---

### TC-005 — Inventory and Loot Management
- Precondition: User has completed TC-003 and defeated at least one enemy
- Steps: 1. Observe LootPanel popup after combat victory 2. Review offered loot items 3. Click "Accept" or select specific items to add to inventory
- Expected result: Items are added to player Inventory; loot panel closes
- Assertion: VISUAL_CHECK: Inventory component shows new items; item count or equipment slots reflect the loot acquisition

---

### TC-006 — Adventure Log and Narrative Review
- Precondition: User has completed TC-003 and performed at least one major action (dialogue, combat, discovery)
- Steps: 1. Click AdventureLog or narrative history panel 2. Scroll through past narration entries 3. Observe NPC mentions and story progression
- Expected result: Complete narrative history is visible with formatted dialogue, DM narration, and quest updates
- Assertion: VISUAL_CHECK: AdventureLogWithDM displays timestamped entries; NPC names are highlighted via NPCMentionHighlighter; no truncated or missing text
