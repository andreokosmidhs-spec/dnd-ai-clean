# JARVIS MASTER PLAN — dnd-ai-clean
*Updated: June 2026 | Sentient RPG Engine — D&D 5e AI Platform*

---

## 1. CURRENT STATE

### What Exists
- **Backend:** FastAPI (Python) with 30+ mounted routers in `backend/api/`
- **AI Stack:** Claude Sonnet as primary DM brain, GPT-4o-mini for intent tagging, OpenAI TTS + Kokoro fallback for voice
- **Database:** MongoDB (Motor async) with in-memory fallback for local dev
- **Deployment:** Render (cloud hosting), GitHub Actions CI/CD pipeline
- **Frontend:** Separate repo connecting via `/api` prefix
- **Test Suite:** Multiple test files — `backend_test.py`, `combat_mechanics_test.py`, `combat_test.py`, `comprehensive_playtest.py`, `dungeon_forge_test.py`, and more
- **Docs:** Extensive markdown documentation — DM prompt architecture (V6), DC system, combat mechanics, cinematic intro structure, entity links

### What Works
- Core FastAPI server boots and deploys to Render
- JWT authentication system
- Combat mechanics engine (multiple test files confirm iteration)
- TTS narration (OpenAI + Kokoro fallback)
- DC (Difficulty Class) system implemented and tested
- DM Agent prompt architecture at V6.0
- DungeonForge procedural content (v4.1 tested)
- Character creation system
- Mobile pinch-zoom and pan support

### What Is Missing / Needs Work
- Frontend repo is separate — no unified monorepo or shared CI
- No confirmed end-to-end integration test suite
- No public demo or web storefront presence
- Marketing materials, trailer, and press kit not started
- Multiplayer / co-op session support not implemented
- Performance benchmarks under load not documented
- Analytics and telemetry not confirmed
- No public demo or early access build

---

## 2. DEVELOPMENT PLAN

### Phase 1 — Stabilisation & MVP Polish (Weeks 1–3)
**Goal:** Make the current build bulletproof, fully tested, and demo-ready.
- Fix any remaining Render deploy crashes (JWT, startup errors)
- Write a unified end-to-end integration test: login → character creation → DM narration → combat round → loot
- Audit all 30+ routers for unhandled exceptions and missing input validation
- Confirm TTS pipeline works on Render (OpenAI primary + Kokoro fallback)
- Stabilise DungeonForge v4.1 procedural generation
- Write a clean README.md with setup, env vars, and API overview
- Complexity: M | Estimated time: 2–3 weeks

### Phase 2 — Feature Expansion (Weeks 4–8)
**Goal:** Add the high-impact features that make the game feel complete.
- Inventory & loot system (items, equipment slots, gold)
- Spell system — full PHB spell list integration with AI narration
- NPC memory — persistent NPC relationship tracking per campaign
- World State persistence — campaign saves survive server restarts
- Character progression — level up, ASI, feat selection via AI dialogue
- Party system — multiple characters in one session (foundation for co-op)
- Complexity: L | Estimated time: 4–5 weeks

### Phase 3 — Co-op Multiplayer & Voice (Weeks 9–14)
**Goal:** Allow 2–4 players to share a session with live DM narration.
- WebSocket session rooms (FastAPI WebSocket support)
- Turn-order synchronisation across clients
- Shared combat log and DM narration broadcast
- Voice input (Whisper STT) so players can speak actions
- Mobile-first UI refinements
- Complexity: L | Estimated time: 5–6 weeks

### Phase 4 — Polish, Launch Prep & Monetisation (Weeks 15–18)
**Goal:** Prepare for public web launch with a sustainable subscription model.
- Onboarding flow — tutorial campaign for new players
- Campaign marketplace — share/sell community dungeons
- Stripe subscription integration (no middlemen, full margin)
- Analytics dashboard (session length, player actions, retention)
- Press kit and trailer
- Complexity: M | Estimated time: 3–4 weeks

---

## 3. MARKETING PLAN — HONEST STRATEGY

### What This Product Actually Is
This is a **web-based AI SaaS product**, not a downloadable game. It runs in a browser, requires a live backend, and charges per usage or subscription. Treating it like a Steam game is a mistake — it creates friction, costs $100 upfront, and puts it in the wrong marketplace in front of the wrong audience.

### Real Target Audience
- Solo D&D / TTRPG players who want to play without needing a human DM
- Tabletop groups who want an AI DM to run one-shots between sessions
- D&D curious people who have never played but want to try
- Content creators who stream tabletop RPG sessions

### Honest Platform Assessment

**DO:**
- **Own domain + Stripe** — your primary revenue channel. No platform cut beyond Stripe's 2.9%. Full control. This is the business.
- **Patreon** — excellent for TTRPG audience. Run tiers: free (limited sessions), $5/mo (unlimited), $15/mo (voice + co-op beta). Patreon communities are loyal and vocal.
- **DriveThruRPG** — the #1 marketplace for tabletop RPG content. List premium campaign packs as digital products. The audience is exactly your user base.
- **Discord** — not optional. TTRPG communities live here. Build a server, run public sessions, let people watch the AI DM in action. Word of mouth starts here.
- **Reddit** — r/DnD (4M members), r/rpg, r/DungeonMasters, r/artificial. A single honest "I built an AI DM" post with a demo clip can drive thousands of signups overnight.
- **TikTok / YouTube Shorts** — short clips of the AI narrating dramatic combat moments. This content is highly shareable and costs nothing to produce.

**DO NOT (yet):**
- **Steam** — $100 fee, requires a downloadable executable, wrong audience for a web app, long review process. Revisit only if you build an offline Electron wrapper in Phase 4.
- **itch.io** — fine for downloadable indie games, poor fit for a live web service. Not worth the effort until there is a standalone offline mode.
- **App stores** — too early, too expensive to maintain, approval risk.

### Launch Strategy (Honest Sequence)
1. **Week 1:** Set up custom domain, Stripe paywall, free tier with 3 sessions
2. **Week 2:** Post in r/DnD, r/rpg, r/artificial with a 60-second demo clip showing the AI DM narrating a combat scene
3. **Week 3:** Reach out to 5 TTRPG YouTubers (10K–100K subs) — offer free lifetime access in exchange for a video
4. **Week 4:** Launch Patreon with $5 / $15 tiers, link from every social post
5. **Week 6:** List first premium campaign pack on DriveThruRPG ($4.99)
6. **Ongoing:** Weekly TikTok/Shorts clips of memorable AI DM moments — this is your cheapest and highest-ROI marketing channel

### Pricing Model
- **Free tier:** 3 sessions, no TTS voice, basic character options
- **Adventurer ($6.99/mo):** Unlimited sessions, all classes, TTS narration
- **Hero ($14.99/mo):** Everything + voice input, co-op (up to 4 players), campaign saves, priority AI speed
- **Lifetime ($59.99):** One-time Hero access — sell limited slots at launch for cash injection

---

## 4. TESTING PLAN

### Phase 1 Testing
- Unit tests for all API routers (pytest, target 80% coverage)
- Integration test: full session flow (auth → campaign → combat → end)
- Render deploy smoke test after every push (GitHub Actions)
- Manual QA: 3 full playthroughs of starter dungeon

### Phase 2 Testing
- Combat regression suite — all existing combat_mechanics_test files must pass
- Spell system unit tests — 50 most common spells verified
- NPC memory stress test — 100 interactions per NPC without state corruption
- Save/load round-trip test for campaign state

### Phase 3 Testing
- WebSocket load test — 4 simultaneous players, 100 messages/min
- Latency benchmark — DM response under 3 seconds at p95
- Mobile browser testing (iOS Safari, Android Chrome)
- Voice input accuracy test — 20 spoken commands, target 90% correct intent

### Phase 4 Testing
- Stripe payment flow end-to-end (test mode + live mode)
- Onboarding funnel — 5 new users complete tutorial without help
- Load test — 100 concurrent sessions on Render
- Cross-browser: Chrome, Firefox, Safari, Edge

---

## 5. IMPLEMENTATION ORDER

1. **Stabilise deploy** — Render crashes kill demos and kill trust. Fix first.
2. **End-to-end integration test** — proves the product works before showing anyone
3. **Stripe + free tier** — revenue infra before marketing push
4. **Reddit + Discord launch** — cheapest possible distribution with highest TTRPG density
5. **Inventory + spells + progression** — these are the features players ask about first
6. **Patreon tiers go live** — once there is an engaged audience
7. **DriveThruRPG campaign pack** — passive income, reaches new audience
8. **Co-op WebSocket multiplayer** — biggest technical lift, save for after revenue is flowing
9. **Voice input (Whisper)** — high-impact premium feature, justifies Hero tier price
10. **Press kit + trailer** — only after the product is polished enough to be proud of

---

## 6. EXPENSES FORECAST

### Phase 1 (Stabilisation) — $0–$50
- Render hobby plan: free or $7/mo
- Domain name (if not owned): ~$12/yr
- Dev tools: $0 (all open source)

### Phase 2 (Feature Expansion) — $50–$150
- Claude API usage during development/testing: ~$30–$80
- OpenAI TTS testing: ~$20–$50

### Phase 3 (Multiplayer + Voice) — $100–$200
- Render upgrade for WebSocket support: ~$25/mo
- Whisper API testing: ~$30–$50
- Load testing tools: $0 (Locust is free)

### Phase 4 (Launch) — $150–$400
- Stripe setup: free (2.9% + $0.30 per transaction)
- Video editing / trailer: $0–$200 (DIY vs. contractor)
- DriveThruRPG publisher account: free
- Patreon: free (takes 5–12% of earnings)
- Social media ads (optional): $100–$200 for targeted Reddit/Facebook ads to r/DnD audience

### Total Estimated Pre-Revenue Cost: $300–$800
### Break-even: ~43 Adventurer subscribers or ~21 Hero subscribers per month
