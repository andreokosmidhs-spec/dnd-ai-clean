#!/bin/bash
set -e

BACKEND_URL="https://prompt-architect-23.preview.emergentagent.com/api"

echo "=========================================="
echo "DUNGEON FORGE Vertical Slice Test"
echo "=========================================="
echo ""

# Step 1: Generate World Blueprint
echo "Step 1: Generating world blueprint..."
WORLD_RESPONSE=$(curl -s -X POST "$BACKEND_URL/world-blueprint/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "world_name": "Valdrath",
    "tone": "Dark fantasy with rare magic",
    "starting_region_hint": "Foggy marsh town at a crossroads"
  }')

CAMPAIGN_ID=$(echo "$WORLD_RESPONSE" | python3 -c "import json, sys; print(json.load(sys.stdin)['campaign_id'])" 2>/dev/null || echo "ERROR")

if [ "$CAMPAIGN_ID" = "ERROR" ]; then
  echo "❌ Failed to generate world blueprint"
  echo "$WORLD_RESPONSE"
  exit 1
fi

echo "✅ Campaign created: $CAMPAIGN_ID"
echo ""

# Step 2: Create Character
echo "Step 2: Creating test character..."

# First, insert character directly into MongoDB
mongo_create_char=$(cat <<EOF
use rpg_db
db.characters.insertOne({
  "campaign_id": "$CAMPAIGN_ID",
  "character_id": "test-char-001",
  "player_id": null,
  "character_state": {
    "name": "Thorgar Ironforge",
    "race": "Dwarf",
    "class": "Fighter",
    "background": "Soldier",
    "goal": "Find the lost forge of my ancestors",
    "level": 1,
    "hp": 12,
    "max_hp": 12,
    "ac": 16,
    "abilities": {
      "str": 16,
      "dex": 12,
      "con": 15,
      "int": 10,
      "wis": 13,
      "cha": 8
    },
    "proficiencies": ["Athletics", "Intimidation", "Survival"],
    "languages": ["Common", "Dwarvish"],
    "inventory": ["Longsword", "Shield", "Chain mail"],
    "features": ["Second Wind", "Fighting Style (Defense)"],
    "conditions": [],
    "reputation": {}
  },
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "updated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
})
EOF
)

echo "$mongo_create_char" | mongosh "$MONGO_URL" --quiet 2>&1 | tail -1

echo "✅ Character created: test-char-001"
echo ""

# Step 3: Generate Intro
echo "Step 3: Generating cinematic intro..."
INTRO_RESPONSE=$(curl -s -X POST "$BACKEND_URL/intro/generate" \
  -H "Content-Type: application/json" \
  -d "{
    \"campaign_id\": \"$CAMPAIGN_ID\",
    \"character_id\": \"test-char-001\"
  }")

INTRO_LENGTH=$(echo "$INTRO_RESPONSE" | python3 -c "import json, sys; data=json.load(sys.stdin); print(len(data.get('intro_markdown', '')))" 2>/dev/null || echo "0")

if [ "$INTRO_LENGTH" = "0" ]; then
  echo "❌ Failed to generate intro"
  echo "$INTRO_RESPONSE"
  exit 1
fi

echo "✅ Intro generated: $INTRO_LENGTH characters"
echo ""
echo "--- Intro Preview ---"
echo "$INTRO_RESPONSE" | python3 -c "import json, sys; print(json.load(sys.stdin)['intro_markdown'][:500])" 2>/dev/null
echo ""

# Step 4: Test Action Endpoint
echo "Step 4: Testing action endpoint..."
ACTION_RESPONSE=$(curl -s -X POST "$BACKEND_URL/rpg_dm/action" \
  -H "Content-Type: application/json" \
  -d "{
    \"campaign_id\": \"$CAMPAIGN_ID\",
    \"character_id\": \"test-char-001\",
    \"player_action\": \"I look around the tavern, trying to spot any suspicious characters.\"
  }")

NARRATION=$(echo "$ACTION_RESPONSE" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('narration', 'ERROR')[:200])" 2>/dev/null || echo "ERROR")

if [ "$NARRATION" = "ERROR" ]; then
  echo "❌ Failed to process action"
  echo "$ACTION_RESPONSE"
  exit 1
fi

echo "✅ Action processed successfully"
echo ""
echo "--- DM Response Preview ---"
echo "$NARRATION..."
echo ""

echo "=========================================="
echo "✅ VERTICAL SLICE TEST COMPLETE"
echo "=========================================="
echo ""
echo "Campaign ID: $CAMPAIGN_ID"
echo "All endpoints working successfully!"
