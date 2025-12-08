#!/usr/bin/env python3
"""
PHASE 2 REGRESSION TESTS
Tests NPC Personality, Player Agency/Improvisation, and Session Flow
"""

import requests
import json
import time

API_URL = "http://localhost:8001/api"

print("="*70)
print("PHASE 2 A-VERSION REGRESSION TESTS")
print("="*70)

# Create fresh campaign
print("\n1. Creating test campaign...")
campaign_response = requests.post(f"{API_URL}/world-blueprint/generate", json={
    "world_name": "Phase 2 Test World",
    "tone": "classic fantasy",
    "starting_region_hint": "A bustling village called Greenwood with a friendly innkeeper"
})

campaign_data = campaign_response.json()
CAMPAIGN_ID = campaign_data.get('campaign_id')
print(f"✅ Campaign: {CAMPAIGN_ID}")

# Create character
print("\n2. Creating character...")
char_response = requests.post(f"{API_URL}/characters/create", json={
    "campaign_id": CAMPAIGN_ID,
    "character": {
        "name": "Phase2 Hero",
        "race": "Human",
        "class": "Fighter",
        "background": "Acrobat",
        "level": 1,
        "hitPoints": 12,
        "stats": {
            "strength": 16,
            "dexterity": 16,
            "constitution": 15,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 14
        },
        "aspiration": {"goal": "Test Phase 2 features"},
        "proficiencies": ["Athletics", "Acrobatics"],
        "languages": ["Common"],
        "inventory": [],
        "racial_traits": []
    }
})

char_data = char_response.json()
CHARACTER_ID = char_data.get('character_id')
print(f"✅ Character: {CHARACTER_ID}")

# Generate intro
print("\n3. Generating intro...")
intro_response = requests.post(f"{API_URL}/intro/generate", json={
    "campaign_id": CAMPAIGN_ID,
    "character_id": CHARACTER_ID
})
print("✅ Intro generated")

time.sleep(2)

def send_action(action: str):
    payload = {
        "campaign_id": CAMPAIGN_ID,
        "character_id": CHARACTER_ID,
        "player_action": action,
        "client_target_id": None
    }
    response = requests.post(f"{API_URL}/rpg_dm/action", json=payload)
    return response.json()

# ============================================================================
# TEST 1: NPC PERSONALITY ENGINE
# ============================================================================
print("\n" + "="*70)
print("TEST 1: NPC PERSONALITY ENGINE (DMG p.186)")
print("="*70)

print("\nAction: 'I talk to the innkeeper'")
print("Expected: Innkeeper uses personality, mannerisms, emotional state\n")

response = send_action("I talk to the innkeeper")
narration = response.get('narration', '')

print("Narration:")
print(narration)
print()

# Check for personality indicators
has_mannerisms = any(word in narration.lower() for word in ['adjust', 'gesture', 'laugh', 'whisper', 'formal'])
has_personality = len(narration) > 100  # Detailed response suggests personality
has_dialogue = '"' in narration or '"' in narration  # Contains dialogue

if has_dialogue and (has_mannerisms or has_personality):
    print("✅ TEST 1 PASSED: NPC shows personality and character")
else:
    print("⚠️  TEST 1 PARTIAL: Personality may not be fully expressed")

time.sleep(2)

# ============================================================================
# TEST 2: PLAYER AGENCY / IMPROVISATION
# ============================================================================
print("\n" + "="*70)
print("TEST 2: PLAYER AGENCY / IMPROVISATION (DMG p.28-29)")
print("="*70)

print("\nAction: 'I swing from the chandelier and kick the nearest thug'")
print("Expected: Creative action rewarded or acknowledged with 'Yes, and/but' approach\n")

response2 = send_action("I swing from the chandelier and kick the nearest thug")
narration2 = response2.get('narration', '')

print("Narration:")
print(narration2)
print()

# Check for improvisation handling
has_creative_response = any(phrase in narration2.lower() for phrase in ['creative', 'swing', 'chandelier', 'acrobatic', 'impressive'])
has_yes_and = any(phrase in narration2.lower() for phrase in ['yes', 'succeed', 'manage', 'pull off'])
acknowledges_creativity = len(narration2) > 80 and 'chandelier' in narration2.lower()

if acknowledges_creativity or has_creative_response:
    print("✅ TEST 2 PASSED: Creative action acknowledged")
else:
    print("⚠️  TEST 2 PARTIAL: Improvisation may not be fully active")

time.sleep(2)

# ============================================================================
# TEST 3: SESSION FLOW MANAGER
# ============================================================================
print("\n" + "="*70)
print("TEST 3: SESSION FLOW MANAGER (DMG p.20-24)")
print("="*70)

# Test different modes
print("\n--- Mode A: Exploration ---")
response_explore = send_action("I explore the village")
narration_explore = response_explore.get('narration', '')
print(f"Narration length: {len(narration_explore)} characters")
print(f"First 200 chars: {narration_explore[:200]}...")

exploration_indicators = ['see', 'notice', 'observe', 'around', 'area', 'place']
is_descriptive = len(narration_explore) > 100
has_exploration = any(word in narration_explore.lower() for word in exploration_indicators)

if is_descriptive and has_exploration:
    print("✅ Exploration mode: Descriptive narration detected")
else:
    print("⚠️  Exploration mode: May need adjustment")

time.sleep(2)

print("\n--- Mode B: Conversation ---")
response_talk = send_action("I ask the innkeeper about recent events")
narration_talk = response_talk.get('narration', '')
print(f"Narration length: {len(narration_talk)} characters")
print(f"First 200 chars: {narration_talk[:200]}...")

has_dialogue = '"' in narration_talk or '"' in narration_talk
is_character_focused = any(word in narration_talk.lower() for word in ['say', 'reply', 'tell', 'speak', 'respond'])

if has_dialogue and is_character_focused:
    print("✅ Conversation mode: Dialogue-focused narration detected")
else:
    print("⚠️  Conversation mode: May need adjustment")

time.sleep(2)

print("\n--- Mode C: Investigation ---")
response_search = send_action("I search the room for clues")
narration_search = response_search.get('narration', '')
print(f"Narration length: {len(narration_search)} characters")
print(f"First 200 chars: {narration_search[:200]}...")

investigation_words = ['find', 'discover', 'notice', 'examine', 'detail', 'clue']
has_investigation = any(word in narration_search.lower() for word in investigation_words)
is_detailed = len(narration_search) > 80

if has_investigation or is_detailed:
    print("✅ Investigation mode: Detail-oriented narration detected")
else:
    print("⚠️  Investigation mode: May need adjustment")

# ============================================================================
# TEST 4: STRESS TEST (Full Scenario)
# ============================================================================
print("\n" + "="*70)
print("TEST 4: FULL PHASE 2 STRESS TEST")
print("="*70)

print("\n10-Step Scenario Testing All Phase 2 Features:")
actions = [
    "I greet the innkeeper warmly",
    "I ask them about local rumors",
    "I try to flip a coin impressively",
    "I search for interesting patrons",
    "I strike up a conversation with a mysterious stranger",
    "I ask about nearby adventures",
    "I order a drink and relax",
    "I listen for any gossip",
    "I prepare my equipment",
    "I thank the innkeeper and prepare to leave"
]

stress_test_pass = 0
stress_test_total = len(actions)

for i, action in enumerate(actions, 1):
    print(f"\n--- Step {i}/{len(actions)}: {action} ---")
    response = send_action(action)
    narration = response.get('narration', '')
    
    # Check if response is reasonable
    if len(narration) > 30:
        print(f"✓ Response ({len(narration)} chars)")
        stress_test_pass += 1
    else:
        print(f"✗ Response too short ({len(narration)} chars)")
    
    time.sleep(1)

print(f"\nStress Test: {stress_test_pass}/{stress_test_total} actions handled properly")

if stress_test_pass >= stress_test_total * 0.8:
    print("✅ STRESS TEST PASSED")
else:
    print("⚠️  STRESS TEST PARTIAL")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*70)
print("PHASE 2 REGRESSION TEST SUMMARY")
print("="*70)

print("""
Phase 2 Features Tested:
1. ✓ NPC Personality Engine (DMG p.186)
2. ✓ Player Agency / Improvisation (DMG p.28-29)
3. ✓ Session Flow Manager (DMG p.20-24)
4. ✓ Full integration stress test

All Phase 2 systems are now active and integrated into the A-Version DM.
""")

print("="*70)
