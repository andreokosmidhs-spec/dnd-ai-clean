# CHANGELOG - P2.5 Hardening Release

## ✅ P2.5 – Hardening Release

**Focus:** Make combat feel grounded in the world, stop lore auto-mangling, and keep combat visible after reload.

### Changes

- **World-aware enemies:** Combat now pulls enemy archetypes from world context (POI type + tone). Shrines spawn cultists, barracks spawn guards, docks spawn criminals, ruins in dark worlds spawn undead. Bandits are now only the fallback, not the default.

- **Lore Checker in soft mode:** The Lore Checker no longer rewrites narration. It detects unknown entities and logs warnings but returns the original text unchanged, with a much smarter stopword filter to avoid false positives.

- **Persistent combat UI:** CombatHUD state survives page reloads via `localStorage`. If combat is active in the backend, the HUD appears immediately on reload for that campaign/character and is cleared automatically when combat ends.

### Technical Details

**Files Added:**
- `/app/backend/services/enemy_sourcing_service.py` - Context-aware enemy selection system

**Files Modified:**
- `/app/backend/routers/dungeon_forge.py` - Enemy sourcing integration, lore checker soft mode
- `/app/backend/services/lore_checker_service.py` - Expanded stopwords, auto_correct parameter
- `/app/frontend/src/components/AdventureLogWithDM.jsx` - Combat state persistence

### Compatibility

All API shapes remain unchanged. P0/P1/P2 behavior is preserved; P2.5 just makes the game harder to break and more coherent to play.
