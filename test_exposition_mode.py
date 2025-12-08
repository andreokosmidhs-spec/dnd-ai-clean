#!/usr/bin/env python3
"""
Test Phase 2.5: Exposition Mode
Verify that info-seeking actions trigger exposition mode and deliver concrete information
"""

import requests
import json
import time

API_URL = "http://localhost:8001/api"

print("="*70)
print("PHASE 2.5: EXPOSITION MODE TEST")
print("="*70)

# Create test campaign
print("\n1. Creating test campaign...")
campaign_response = requests.post(f"{API_URL}/world-blueprint/generate", json={
    "world_name": "Exposition Test World",
    "tone": "mystery",
    "starting_region_hint": "A tavern where mysterious travelers discuss a hidden cult"
})

campaign_data = campaign_response.json()
CAMPAIGN_ID = campaign_data.get('campaign_id')
print(f"✅ Campaign: {CAMPAIGN_ID}")

# Create character
print("\n2. Creating character...")
char_response = requests.post(f"{API_URL}/characters/create", json={
    "campaign_id": CAMPAIGN_ID,
    "character": {
        "name": "Info Seeker",
        "race": "Human",
        "class": "Rogue",
        "background": "Spy",
        "level": 1,
        "hitPoints": 10,
        "stats": {
            "strength": 10,
            "dexterity": 16,
            "constitution": 12,
            "intelligence": 14,
            "wisdom": 14,
            "charisma": 12
        },
        "aspiration": {"goal": "Uncover secrets"},
        "proficiencies": ["Stealth", "Insight", "Investigation"],
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
# TEST 1: Baseline Conversation (Should NOT be exposition)
# ============================================================================
print("\n" + "="*70)
print("TEST 1: Baseline Conversation")
print("="*70)

print("\nAction: 'I approach the travelers and introduce myself'")
print("Expected Mode: conversation\n")

response1 = send_action("I approach the travelers and introduce myself")
narration1 = response1.get('narration', '')

print(f"Narration ({len(narration1)} chars):")
print(narration1[:300] + "...\n")

time.sleep(2)

# ============================================================================
# TEST 2: Explicit Listening (SHOULD trigger exposition)
# ============================================================================
print("="*70)
print("TEST 2: Explicit Listening for Information")
print("="*70)

print("\nAction: 'I listen to what they're saying'")
print("Expected Mode: exposition")
print("Expected: Concrete facts, plot details, new information\n")

response2 = send_action("I listen to what they're saying")
narration2 = response2.get('narration', '')

print(f"Narration ({len(narration2)} chars):")
print(narration2)
print()

# Check for concrete information
has_names = any(char.isupper() for word in narration2.split() for char in word if len(word) > 3)
has_numbers = any(char.isdigit() for char in narration2)
has_places = any(word in narration2.lower() for word in ['temple', 'mill', 'cave', 'forest', 'town', 'city', 'building'])
has_quotes = '"' in narration2 or '"' in narration2
is_long_enough = len(narration2) > 200

if has_quotes and (has_names or has_places or has_numbers) and is_long_enough:
    print("✅ EXPOSITION MODE WORKING: Contains dialogue with concrete details")
elif len(narration2) > 300 and has_quotes:
    print("⚠️  PARTIAL: Has dialogue but check for concrete facts")
else:
    print("❌ MAY NOT BE EXPOSITION: Response seems atmospheric rather than informative")

time.sleep(2)

# ============================================================================
# TEST 3: Waiting for Information (SHOULD trigger exposition)
# ============================================================================
print("\n" + "="*70)
print("TEST 3: Waiting for More Information")
print("="*70)

print("\nAction: 'I wait for the conversation to unfold more information'")
print("Expected Mode: exposition")
print("Expected: New revelations, plot advancement\n")

response3 = send_action("I wait for the conversation to unfold more information")
narration3 = response3.get('narration', '')

print(f"Narration ({len(narration3)} chars):")
print(narration3)
print()

# Check for plot advancement
mood_words = ['atmosphere', 'tension', 'grows', 'unfolds', 'mysterious', 'subtle']
fact_words = ['plan', 'tomorrow', 'tonight', 'secret', 'meet', 'leader', 'name', 'place']

has_mood_only = sum(1 for word in mood_words if word in narration3.lower()) >= 2
has_facts = sum(1 for word in fact_words if word in narration3.lower()) >= 2

if has_facts and len(narration3) > 200:
    print("✅ EXPOSITION MODE WORKING: Delivers concrete plot information")
elif has_mood_only and not has_facts:
    print("❌ NOT EXPOSITION: Still in atmospheric/mood mode")
else:
    print("⚠️  PARTIAL: Check if information is concrete enough")

time.sleep(2)

# ============================================================================
# TEST 4: Direct Question (Control Test)
# ============================================================================
print("\n" + "="*70)
print("TEST 4: Control Test - Direct Question")
print("="*70)

print("\nAction: 'I ask them what they're planning'")
print("Expected Mode: conversation (not exposition)")
print("Expected: Dialogue response\n")

response4 = send_action("I ask them what they're planning")
narration4 = response4.get('narration', '')

print(f"Narration ({len(narration4)} chars):")
print(narration4[:300] + "...\n")

# ============================================================================
# SUMMARY
# ============================================================================
print("="*70)
print("EXPOSITION MODE TEST SUMMARY")
print("="*70)

print("""
Key Tests:
1. Baseline conversation: Should use conversation mode
2. "I listen": Should trigger EXPOSITION mode with concrete facts
3. "I wait for info": Should trigger EXPOSITION mode with plot advancement
4. "I ask": Should use conversation mode (control)

Expected Behavior in Exposition Mode:
✓ 3-5 concrete pieces of information
✓ Names, places, times, stakes
✓ Direct dialogue with facts
✓ NO atmospheric filler
✓ Clear next actions

Check the narrations above to verify exposition mode is working.
""")

print("="*70)
