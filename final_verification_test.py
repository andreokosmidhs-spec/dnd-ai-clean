#!/usr/bin/env python3
"""
Final Verification Test for All 3 Fixes
"""

import requests
import json
import time

API_URL = "http://localhost:8001/api"

print("="*70)
print("FINAL VERIFICATION TEST - P0 & P1 FIXES")
print("="*70)

# Create a NEW campaign for fresh test
print("\n1. Creating NEW test campaign...")
campaign_response = requests.post(f"{API_URL}/world-blueprint/generate", json={
    "world_name": "Fix Verification World",
    "tone": "classic fantasy",
    "starting_region_hint": "The character starts in dangerous ruins called The Cursed Temple"
})

campaign_data = campaign_response.json()
CAMPAIGN_ID = campaign_data.get('campaign_id')
print(f"✅ Campaign created: {CAMPAIGN_ID}")

# Create character
print("\n2. Creating test character...")
char_response = requests.post(f"{API_URL}/characters/create", json={
    "campaign_id": CAMPAIGN_ID,
    "character": {
        "name": "Test Hero",
        "race": "Human",
        "class": "Fighter",
        "background": "Soldier",
        "level": 1,
        "hitPoints": 12,
        "stats": {
            "strength": 16,
            "dexterity": 14,
            "constitution": 15,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8
        },
        "aspiration": {"goal": "Test fixes"},
        "proficiencies": ["Athletics"],
        "languages": ["Common"],
        "inventory": [],
        "racial_traits": []
    }
})

char_data = char_response.json()
CHARACTER_ID = char_data.get('character_id')
print(f"✅ Character created: {CHARACTER_ID}")

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

print("\n" + "="*70)
print("TEST 1: P0 FIX - Location Continuity in Ruins")
print("="*70)

# Try to spawn innkeeper in ruins
print("\nAction: 'I talk to the innkeeper' (in ruins - SHOULD BE REJECTED)")
response = send_action("I talk to the innkeeper")

narration = response.get('narration', '')
print(f"\nNarration:\n{narration}\n")

# Check validation
rejection_phrases = ['no inn', 'no innkeeper', 'not here', "isn't an inn", "aren't any", "no tavern", "look around for", "there is none here"]
innkeeper_spawned = 'innkeeper' in narration.lower() and any(word in narration.lower() for word in ['behind the counter', 'tankard', 'polishes'])

if any(phrase in narration.lower() for phrase in rejection_phrases):
    print("✅ P0 FIX VERIFIED: Innkeeper correctly rejected in ruins!")
    print(f"   Detected rejection phrase")
elif innkeeper_spawned:
    print("❌ P0 BUG: Innkeeper spawned despite validator")
else:
    print("⚠️  UNCLEAR: Manual check needed")

time.sleep(2)

# Try merchant
print("\n--- Test: Merchant in ruins ---")
print("Action: 'I look for a merchant'")
response2 = send_action("I look for a merchant")
narration2 = response2.get('narration', '')
print(f"Narration: {narration2[:200]}...")

if any(phrase in narration2.lower() for phrase in ['no merchant', 'not here', "aren't any", 'no shop']):
    print("✅ Merchant correctly rejected")
elif 'merchant' in narration2.lower() and any(w in narration2.lower() for w in ['shop', 'wares', 'sells']):
    print("❌ Merchant inappropriately spawned")

print("\n" + "="*70)
print("TEST 2: P1 FIX - Consequence Escalation & Combat Trigger")
print("="*70)

# Create a fresh campaign in a TOWN to test consequence escalation
print("\nCreating town-based campaign for consequence test...")
campaign2_response = requests.post(f"{API_URL}/world-blueprint/generate", json={
    "world_name": "Consequence Test World",
    "tone": "classic fantasy",
    "starting_region_hint": "A peaceful village with an elder"
})

campaign2_data = campaign2_response.json()
CAMPAIGN_ID2 = campaign2_data.get('campaign_id')

char2_response = requests.post(f"{API_URL}/characters/create", json={
    "campaign_id": CAMPAIGN_ID2,
    "character": {
        "name": "Test Fighter",
        "race": "Human",
        "class": "Fighter",
        "background": "Soldier",
        "level": 1,
        "hitPoints": 12,
        "stats": {"strength": 16, "dexterity": 14, "constitution": 15, "intelligence": 10, "wisdom": 12, "charisma": 8},
        "aspiration": {"goal": "Test combat"},
        "proficiencies": [],
        "languages": ["Common"],
        "inventory": [],
        "racial_traits": []
    }
})

char2_data = char2_response.json()
CHARACTER_ID2 = char2_data.get('character_id')

intro2 = requests.post(f"{API_URL}/intro/generate", json={
    "campaign_id": CAMPAIGN_ID2,
    "character_id": CHARACTER_ID2
})

time.sleep(2)

def send_action2(action: str):
    payload = {
        "campaign_id": CAMPAIGN_ID2,
        "character_id": CHARACTER_ID2,
        "player_action": action,
        "client_target_id": None
    }
    response = requests.post(f"{API_URL}/rpg_dm/action", json=payload)
    return response.json()

# Attack sequence
for i in range(1, 5):
    print(f"\n--- Attack {i} ---")
    response = send_action2(f"I punch the elder{' again' if i > 1 else ''}!")
    
    narration = response.get('narration', '')[:200]
    combat_started = response.get('starts_combat', False)
    
    print(f"Narration: {narration}...")
    print(f"Combat Started: {combat_started}")
    
    if combat_started:
        print(f"\n✅ P1 FIX VERIFIED: Combat triggered after {i} attacks!")
        break
    
    time.sleep(2)
else:
    print("\n⚠️  PARTIAL: Combat not triggered after 4 attacks - check logs")

print("\n" + "="*70)
print("VERIFICATION COMPLETE")
print("="*70)
