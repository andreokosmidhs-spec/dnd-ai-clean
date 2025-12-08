# IMMEDIATE FIXES REQUIRED - Phase 1 Combat System

## Issues Found in Testing (0/19 tests passed)

### ISSUE #1: NPCs Not Discoverable (CRITICAL)
**Problem:** `world_state.active_npcs` is always empty
**Root Cause:** NPCs exist only in `world_blueprint.key_npcs`, never populated to active state
**Impact:** Cannot target any NPCs, plot armor never triggers

**FIX:** Create NPC activation system

### ISSUE #2: Target Resolution KeyError
**Problem:** Code checks wrong field `needs_clarification` instead of `status == 'needs_clarification'`
**Location:** `dungeon_forge.py` line ~941

**FIX:** Update conditional checks

### ISSUE #3: Combat Initialization Import Error
**Problem:** Calls `start_combat` but should call `start_combat_with_target`
**Location:** `dungeon_forge.py` line ~1408

**FIX:** Update function name

### ISSUE #4: Missing force_non_lethal Variable
**Problem:** Variable `force_non_lethal` not defined in scope before use
**Location:** `dungeon_forge.py` line ~1009

**FIX:** Initialize variable properly

---

## D&D 5E COMPLIANCE ISSUES

### ISSUE #5: Player Death System (Priority 1)
**Problem:** Players die instantly at 0 HP (incorrect per D&D 5e)
**D&D Rule:** Players make death saving throws, monsters die instantly

**FIX:** Implement death saves for players

---

## IMPLEMENTATION PLAN

1. Create `npc_activation_service.py` to populate active NPCs
2. Fix all target resolution conditionals in `dungeon_forge.py`
3. Fix combat initialization imports
4. Fix force_non_lethal scope issue
5. Implement player death saves system
6. Re-run all tests
