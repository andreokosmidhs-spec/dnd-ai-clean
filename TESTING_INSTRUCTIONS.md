# Testing Instructions: Narration Length Fix v6.1

## Overview
These tests verify that the backend now respects v6.1 sentence-count rules and no longer force-truncates narration to 4-6 sentences.

## Prerequisites
1. Have a test campaign and character created
2. Backend must be running on port 8001
3. Install `jq` for JSON parsing: `apt-get install -y jq` (optional but helpful)

## Quick Sentence Counter
```bash
# Helper function to count sentences in a JSON response
count_sentences() {
    echo "$1" | jq -r '.narration // .intro_markdown' | grep -o '[.!?]' | wc -l
}
```

## Test 1: Intro Generation (12-16 sentences expected)

### Setup
First, get your latest campaign ID:
```bash
CAMPAIGN_ID=$(curl -s "http://localhost:8001/api/campaigns/latest" | jq -r '.data.campaign_id')
CHARACTER_ID=$(curl -s "http://localhost:8001/api/campaigns/latest" | jq -r '.data.character_id')
echo "Campaign: $CAMPAIGN_ID"
echo "Character: $CHARACTER_ID"
```

### Test Intro Regeneration
```bash
# Call intro generation endpoint
INTRO_RESPONSE=$(curl -s -X POST "http://localhost:8001/api/intro/generate" \
  -H "Content-Type: application/json" \
  -d "{\"campaign_id\": \"$CAMPAIGN_ID\", \"character_id\": \"$CHARACTER_ID\"}")

# Extract and display intro
echo "$INTRO_RESPONSE" | jq -r '.intro_markdown' > /tmp/intro_test.txt
cat /tmp/intro_test.txt

# Count sentences
SENTENCE_COUNT=$(grep -o '[.!?]' /tmp/intro_test.txt | wc -l)
echo ""
echo "Sentence count: $SENTENCE_COUNT"
echo "Expected: 12-16 sentences"

if [ $SENTENCE_COUNT -ge 12 ] && [ $SENTENCE_COUNT -le 16 ]; then
    echo "✅ PASS: Intro length is within v6.1 limits"
else
    echo "❌ FAIL: Intro length is outside v6.1 limits (12-16)"
fi
```

### Expected Result
- ✅ Intro has 12-16 sentences
- ✅ No truncation warning in backend logs
- ❌ If intro has exactly 6 sentences → truncation still happening

## Test 2: Exploration Narration (6-10 sentences expected)

```bash
# Make an exploration action
EXPLORATION_RESPONSE=$(curl -s -X POST "http://localhost:8001/api/rpg_dm/action" \
  -H "Content-Type: application/json" \
  -d "{
    \"campaign_id\": \"$CAMPAIGN_ID\",
    \"character_id\": \"$CHARACTER_ID\",
    \"player_action\": \"I carefully explore the town square, looking for interesting shops and people\"
  }")

# Extract narration
echo "$EXPLORATION_RESPONSE" | jq -r '.data.narration' > /tmp/exploration_test.txt
cat /tmp/exploration_test.txt

# Count sentences
SENTENCE_COUNT=$(grep -o '[.!?]' /tmp/exploration_test.txt | wc -l)
echo ""
echo "Sentence count: $SENTENCE_COUNT"
echo "Expected: 6-10 sentences (exploration mode)"

if [ $SENTENCE_COUNT -ge 6 ] && [ $SENTENCE_COUNT -le 10 ]; then
    echo "✅ PASS: Exploration narration is within v6.1 limits"
else
    echo "⚠️  CHECK: Exploration narration is $SENTENCE_COUNT sentences"
    echo "    Expected 6-10, but DM may have chosen a different mode"
fi
```

### Expected Result
- ✅ Narration has 6-10 sentences
- ✅ Backend logs show: `scene_mode: exploration`
- ❌ If narration has exactly 6 sentences → may be truncated

## Test 3: Combat Narration (4-8 sentences expected)

```bash
# Trigger combat if not already in combat
# This requires a specific action that starts combat
COMBAT_RESPONSE=$(curl -s -X POST "http://localhost:8001/api/rpg_dm/action" \
  -H "Content-Type: application/json" \
  -d "{
    \"campaign_id\": \"$CAMPAIGN_ID\",
    \"character_id\": \"$CHARACTER_ID\",
    \"player_action\": \"I attack the nearest enemy with my weapon\"
  }")

# Extract narration
echo "$COMBAT_RESPONSE" | jq -r '.data.narration' > /tmp/combat_test.txt
cat /tmp/combat_test.txt

# Count sentences
SENTENCE_COUNT=$(grep -o '[.!?]' /tmp/combat_test.txt | wc -l)
echo ""
echo "Sentence count: $SENTENCE_COUNT"
echo "Expected: 4-8 sentences (combat mode)"

if [ $SENTENCE_COUNT -ge 4 ] && [ $SENTENCE_COUNT -le 8 ]; then
    echo "✅ PASS: Combat narration is within v6.1 limits"
else
    echo "⚠️  CHECK: Combat narration is $SENTENCE_COUNT sentences"
fi
```

### Expected Result
- ✅ Narration has 4-8 sentences
- ✅ Backend logs show: `scene_mode: combat`
- ❌ If narration has exactly 4 sentences → may be truncated

## Test 4: Backend Log Verification

Check backend logs for filter messages:

```bash
# Check last 100 lines for narration filter logs
tail -n 100 /var/log/supervisor/backend.err.log | grep -E "Narration|sentence|filtered"

# Expected good signs:
# ✅ "✂️ [intro] 14→14 sentences, 0% reduction"
# ✅ "✅ Narration filtered: 9 sentences"
# ✅ "scene_mode: exploration"

# Expected bad signs (if truncation still happening):
# ❌ "⚠️ Narration truncated from 14 to 6 sentences"
# ❌ "⚠️ LLM VIOLATED 16-SENTENCE LIMIT for intro: Generated 14, truncated to 6"
# ❌ "✂️ [intro] 14→6 sentences, 57% reduction"
```

## Test 5: Full Workflow Test

Create a complete new character and verify intro generation:

```bash
# 1. Create new campaign
NEW_CAMPAIGN=$(curl -s -X POST "http://localhost:8001/api/world-blueprint/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "world_name": "Test World",
    "tone": "heroic",
    "starting_region_hint": "A bustling medieval city"
  }')

NEW_CAMPAIGN_ID=$(echo "$NEW_CAMPAIGN" | jq -r '.data.campaign_id')
echo "Created campaign: $NEW_CAMPAIGN_ID"

# 2. Create character
NEW_CHAR=$(curl -s -X POST "http://localhost:8001/api/characters/create" \
  -H "Content-Type: application/json" \
  -d "{
    \"campaign_id\": \"$NEW_CAMPAIGN_ID\",
    \"character\": {
      \"name\": \"Test Hero\",
      \"race\": \"Human\",
      \"class\": \"Fighter\",
      \"background\": \"Soldier\",
      \"stats\": {
        \"strength\": 16,
        \"dexterity\": 14,
        \"constitution\": 15,
        \"intelligence\": 10,
        \"wisdom\": 12,
        \"charisma\": 8
      },
      \"hitPoints\": 12,
      \"proficiencies\": [\"Athletics\", \"Intimidation\"],
      \"inventory\": [\"Longsword\", \"Shield\"]
    }
  }")

# 3. Extract intro
echo "$NEW_CHAR" | jq -r '.data.intro_markdown' > /tmp/full_test_intro.txt
cat /tmp/full_test_intro.txt

# 4. Count sentences
INTRO_COUNT=$(grep -o '[.!?]' /tmp/full_test_intro.txt | wc -l)
echo ""
echo "=== FULL WORKFLOW TEST RESULTS ==="
echo "Campaign ID: $NEW_CAMPAIGN_ID"
echo "Intro sentence count: $INTRO_COUNT"
echo "Expected: 12-16 sentences"

if [ $INTRO_COUNT -ge 12 ] && [ $INTRO_COUNT -le 16 ]; then
    echo "✅ PASS: Full workflow intro respects v6.1 limits"
else
    echo "❌ FAIL: Full workflow intro outside v6.1 limits"
fi
```

## Manual Verification Checklist

After running tests, manually verify:

- [ ] Backend logs show `MODE_LIMITS` being used (no errors about missing dict)
- [ ] No "Narration truncated from X to 6 sentences" warnings
- [ ] Intro narrations are longer than before (12-16 vs 6)
- [ ] Exploration narrations can reach 10 sentences (not stuck at 6)
- [ ] Combat narrations can reach 8 sentences (not stuck at 4)
- [ ] Scene descriptions can be up to 10 sentences (not stuck at 6)
- [ ] No duplicate filtering warnings (two filters on same text)

## Troubleshooting

### If tests fail with "6 sentences" consistently:

1. Check if changes were applied:
```bash
grep -n "MODE_LIMITS" /app/backend/routers/dungeon_forge.py
# Should show the dictionary definition around line 42-51
```

2. Verify backend restarted:
```bash
sudo supervisorctl status backend
# Should show uptime after your changes
```

3. Check for syntax errors:
```bash
tail -50 /var/log/supervisor/backend.err.log | grep ERROR
```

### If intro still truncated:

Check line 661 in dungeon_forge.py:
```bash
grep -A2 -B2 "intro_generate_endpoint" /app/backend/routers/dungeon_forge.py
# Should show max_sentences=16 (already correct)
```

### If exploration narration stuck at 6:

Check line 2715 in dungeon_forge.py:
```bash
sed -n '2710,2720p' /app/backend/routers/dungeon_forge.py
# Should show context-based filtering using scene_mode
```

## Success Criteria

✅ **Fix is successful if:**
- Intro narrations reach 12-16 sentences
- Exploration narrations reach 6-10 sentences  
- Combat narrations reach 4-8 sentences
- No double-filtering warnings in logs
- Backend logs show "mode-aware" limit usage

❌ **Fix failed if:**
- All narrations still truncated to 6 sentences
- Backend shows errors about MODE_LIMITS not found
- Logs still show "truncated from X to 6" messages
- Double-filtering still occurring

## Next Steps After Testing

If tests pass:
1. Update test_result.md with results
2. Call testing agent for comprehensive E2E testing
3. Monitor production logs for any edge cases

If tests fail:
1. Check rollback plan in NARRATION_LENGTH_FIX_v61.md
2. Review backend error logs
3. Verify Python syntax in dungeon_forge.py
