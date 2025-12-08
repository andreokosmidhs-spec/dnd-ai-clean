#!/bin/bash

# A-Version Regression Playtest Script
# Tests plot armor, combat mechanics, location continuity, and pacing

API_URL="http://localhost:8001/api"
TEST_LOG="/app/playtest_results.txt"

echo "========================================" > "$TEST_LOG"
echo "A-VERSION REGRESSION PLAYTEST" >> "$TEST_LOG"
echo "Started: $(date)" >> "$TEST_LOG"
echo "========================================" >> "$TEST_LOG"
echo "" >> "$TEST_LOG"

# Step 1: Create a test campaign with world blueprint
echo "STEP 1: Creating test campaign..." | tee -a "$TEST_LOG"
CAMPAIGN_RESPONSE=$(curl -s -X POST "$API_URL/world-blueprint/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "world_name": "Test World - A-Version",
    "tone": "classic fantasy",
    "starting_region_hint": "A peaceful village called Greendale with nearby dangerous ruins called The Shattered Tower"
  }')

CAMPAIGN_ID=$(echo "$CAMPAIGN_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('campaign_id', ''))" 2>/dev/null)

if [ -z "$CAMPAIGN_ID" ]; then
  echo "❌ Failed to create campaign" | tee -a "$TEST_LOG"
  echo "Response: $CAMPAIGN_RESPONSE" >> "$TEST_LOG"
  exit 1
fi

echo "✅ Campaign created: $CAMPAIGN_ID" | tee -a "$TEST_LOG"
echo "" >> "$TEST_LOG"

# Step 2: Create a fighter character
echo "STEP 2: Creating test character..." | tee -a "$TEST_LOG"
CHAR_RESPONSE=$(curl -s -X POST "$API_URL/characters/create" \
  -H "Content-Type: application/json" \
  -d "{
    \"campaign_id\": \"$CAMPAIGN_ID\",
    \"character\": {
      \"name\": \"Thorin Testfighter\",
      \"race\": \"Human\",
      \"class\": \"Fighter\",
      \"background\": \"Soldier\",
      \"level\": 1,
      \"hitPoints\": 12,
      \"stats\": {
        \"strength\": 16,
        \"dexterity\": 14,
        \"constitution\": 15,
        \"intelligence\": 10,
        \"wisdom\": 12,
        \"charisma\": 8
      },
      \"aspiration\": {
        \"goal\": \"Test the A-Version systems\"
      },
      \"proficiencies\": [\"Athletics\", \"Intimidation\"],
      \"languages\": [\"Common\"],
      \"inventory\": [\"Longsword\", \"Shield\"],
      \"racial_traits\": []
    }
  }")

CHARACTER_ID=$(echo "$CHAR_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('character_id', ''))" 2>/dev/null)

if [ -z "$CHARACTER_ID" ]; then
  echo "❌ Failed to create character" | tee -a "$TEST_LOG"
  echo "Response: $CHAR_RESPONSE" >> "$TEST_LOG"
  exit 1
fi

echo "✅ Character created: $CHARACTER_ID" | tee -a "$TEST_LOG"
echo "" >> "$TEST_LOG"

# Step 3: Generate intro to set initial location
echo "STEP 3: Generating intro..." | tee -a "$TEST_LOG"
INTRO_RESPONSE=$(curl -s -X POST "$API_URL/intro/generate" \
  -H "Content-Type: application/json" \
  -d "{
    \"campaign_id\": \"$CAMPAIGN_ID\",
    \"character_id\": \"$CHARACTER_ID\"
  }")

echo "$INTRO_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print('Intro:', d.get('intro', 'N/A')[:200])" >> "$TEST_LOG" 2>/dev/null
echo "" >> "$TEST_LOG"

# ========================================
# PLAYTEST SCRIPT 1: Plot Armor & Consequences
# ========================================
echo "" | tee -a "$TEST_LOG"
echo "========================================" | tee -a "$TEST_LOG"
echo "PLAYTEST SCRIPT 1: Plot Armor & Consequences" | tee -a "$TEST_LOG"
echo "========================================" | tee -a "$TEST_LOG"
echo "" | tee -a "$TEST_LOG"

# Attack 1
echo "--- Attack 1: First punch to essential NPC ---" | tee -a "$TEST_LOG"
ACTION1=$(curl -s -X POST "$API_URL/rpg_dm/action" \
  -H "Content-Type: application/json" \
  -d "{
    \"campaign_id\": \"$CAMPAIGN_ID\",
    \"player_action\": \"I punch the village elder in the face.\",
    \"client_target_id\": null
  }")

echo "Response:" >> "$TEST_LOG"
echo "$ACTION1" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('Narration:', d.get('narration', 'N/A'))
    print('World State Update:', d.get('world_state_update', {}))
    if 'mechanical_summary' in d:
        print('Mechanical Summary:', json.dumps(d['mechanical_summary'], indent=2))
except:
    print('Failed to parse JSON')
" | tee -a "$TEST_LOG"
echo "" >> "$TEST_LOG"

# Attack 2
echo "--- Attack 2: Second punch ---" | tee -a "$TEST_LOG"
ACTION2=$(curl -s -X POST "$API_URL/rpg_dm/action" \
  -H "Content-Type: application/json" \
  -d "{
    \"campaign_id\": \"$CAMPAIGN_ID\",
    \"player_action\": \"I punch the elder again!\",
    \"client_target_id\": null
  }")

echo "$ACTION2" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('Narration:', d.get('narration', 'N/A'))
    print('Escalation Check:', d.get('world_state_update', {}).get('transgressions', 'N/A'))
except:
    print('Failed to parse')
" | tee -a "$TEST_LOG"
echo "" >> "$TEST_LOG"

# Attack 3
echo "--- Attack 3: Third punch (severe escalation expected) ---" | tee -a "$TEST_LOG"
ACTION3=$(curl -s -X POST "$API_URL/rpg_dm/action" \
  -H "Content-Type: application/json" \
  -d "{
    \"campaign_id\": \"$CAMPAIGN_ID\",
    \"player_action\": \"I punch the elder a third time!\",
    \"client_target_id\": null
  }")

echo "$ACTION3" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('Narration:', d.get('narration', 'N/A'))
    print('Combat Started:', d.get('starts_combat', False))
    print('Transgressions:', d.get('world_state_update', {}).get('transgressions', 'N/A'))
except:
    print('Failed to parse')
" | tee -a "$TEST_LOG"
echo "" >> "$TEST_LOG"

# ========================================
# PLAYTEST SCRIPT 3: Location & NPC Continuity
# ========================================
echo "" | tee -a "$TEST_LOG"
echo "========================================" | tee -a "$TEST_LOG"
echo "PLAYTEST SCRIPT 3: Location & NPC Continuity" | tee -a "$TEST_LOG"
echo "========================================" | tee -a "$TEST_LOG"
echo "" | tee -a "$TEST_LOG"

# Travel to ruins
echo "--- Traveling to ruins ---" | tee -a "$TEST_LOG"
TRAVEL=$(curl -s -X POST "$API_URL/rpg_dm/action" \
  -H "Content-Type: application/json" \
  -d "{
    \"campaign_id\": \"$CAMPAIGN_ID\",
    \"player_action\": \"I travel to the Shattered Tower ruins.\",
    \"client_target_id\": null
  }")

echo "$TRAVEL" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('Narration:', d.get('narration', 'N/A')[:300])
    print('Location:', d.get('world_state_update', {}).get('current_location', 'N/A'))
except:
    print('Failed to parse')
" | tee -a "$TEST_LOG"
echo "" >> "$TEST_LOG"

# Test: Look for merchant in ruins
echo "--- Test: Looking for merchant in ruins (should fail) ---" | tee -a "$TEST_LOG"
MERCHANT_TEST=$(curl -s -X POST "$API_URL/rpg_dm/action" \
  -H "Content-Type: application/json" \
  -d "{
    \"campaign_id\": \"$CAMPAIGN_ID\",
    \"player_action\": \"I look for a merchant to buy supplies.\",
    \"client_target_id\": null
  }")

echo "$MERCHANT_TEST" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('Narration:', d.get('narration', 'N/A'))
    print('Active NPCs:', d.get('world_state_update', {}).get('active_npcs', 'N/A'))
    
    narration = d.get('narration', '').lower()
    if 'merchant' in narration and ('no' in narration or 'not' in narration or 'ruins' in narration):
        print('✅ PASS: DM correctly rejected merchant in ruins')
    elif 'merchant' in narration and ('shop' in narration or 'sells' in narration):
        print('❌ FAIL: DM spawned merchant in ruins')
    else:
        print('⚠️ PARTIAL: Response unclear')
except:
    print('Failed to parse')
" | tee -a "$TEST_LOG"
echo "" >> "$TEST_LOG"

# Test: Talk to innkeeper in ruins
echo "--- Test: Looking for innkeeper in ruins (should fail) ---" | tee -a "$TEST_LOG"
INNKEEPER_TEST=$(curl -s -X POST "$API_URL/rpg_dm/action" \
  -H "Content-Type: application/json" \
  -d "{
    \"campaign_id\": \"$CAMPAIGN_ID\",
    \"player_action\": \"I talk to the innkeeper.\",
    \"client_target_id\": null
  }")

echo "$INNKEEPER_TEST" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('Narration:', d.get('narration', 'N/A'))
    
    narration = d.get('narration', '').lower()
    if 'innkeeper' in narration and ('no' in narration or 'not' in narration or \"isn't\" in narration):
        print('✅ PASS: DM correctly rejected innkeeper in ruins')
    elif 'innkeeper' in narration and ('greet' in narration or 'smile' in narration or 'says' in narration):
        print('❌ FAIL: DM spawned innkeeper in ruins')
    else:
        print('⚠️ PARTIAL: Response unclear')
except:
    print('Failed to parse')
" | tee -a "$TEST_LOG"
echo "" >> "$TEST_LOG"

echo "========================================" | tee -a "$TEST_LOG"
echo "Playtest completed: $(date)" | tee -a "$TEST_LOG"
echo "Full results saved to: $TEST_LOG" | tee -a "$TEST_LOG"
echo "========================================" | tee -a "$TEST_LOG"

echo ""
echo "✅ Playtest execution complete. Check $TEST_LOG for full results."
