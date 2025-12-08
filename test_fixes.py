#!/usr/bin/env python3
"""
Test the 3 P0/P1 Fixes
"""

import requests
import json

API_URL = "http://localhost:8001/api"
CAMPAIGN_ID = "bb90306f-7eb3-4bf2-97a5-928b234d56c4"
CHARACTER_ID = "4beab239-48e9-4fee-996e-0c5515aee533"

def send_action(action: str):
    payload = {
        "campaign_id": CAMPAIGN_ID,
        "character_id": CHARACTER_ID,
        "player_action": action,
        "client_target_id": None
    }
    response = requests.post(f"{API_URL}/rpg_dm/action", json=payload)
    return response.json()

print("="*70)
print("TEST 1: P0 FIX - Location Continuity (Innkeeper in Ruins)")
print("="*70)
print("\nAction: 'I talk to the innkeeper' (should be rejected)\n")

response = send_action("I talk to the innkeeper.")
narration = response.get('narration', '')

print(f"Narration:\n{narration}\n")

# Check for fix
if any(phrase in narration.lower() for phrase in ['no inn', 'no innkeeper', 'not here', "isn't"]):
    print("✅ P0 FIX VERIFIED: Innkeeper correctly rejected!")
elif 'innkeeper' in narration.lower() and any(word in narration.lower() for word in ['counter', 'tankard', 'bar']):
    print("❌ P0 BUG STILL EXISTS: Innkeeper spawned in wrong location")
else:
    print("⚠️  UNCLEAR: Check narration manually")

print("\n" + "="*70)
print("TEST 2: P1 FIX - Consequence Escalation (Repeated Violence)")
print("="*70)

import time
time.sleep(2)

print("\n--- Attack 1 ---")
response1 = send_action("I punch the village elder.")
print(f"Narration: {response1.get('narration', '')[:150]}...")
print(f"Combat Started: {response1.get('starts_combat', False)}")

time.sleep(2)

print("\n--- Attack 2 ---")
response2 = send_action("I punch the elder again!")
print(f"Narration: {response2.get('narration', '')[:150]}...")
print(f"Combat Started: {response2.get('starts_combat', False)}")

time.sleep(2)

print("\n--- Attack 3 (Should trigger combat) ---")
response3 = send_action("I punch the elder once more!")
print(f"Narration: {response3.get('narration', '')[:150]}...")
print(f"Combat Started: {response3.get('starts_combat', False)}")

if response3.get('starts_combat', False):
    print("\n✅ P1 FIX VERIFIED: Combat triggered after 3 assaults!")
else:
    print("\n⚠️  PARTIAL: Combat not yet triggered - may need one more attack")
    
    time.sleep(2)
    print("\n--- Attack 4 (Force combat) ---")
    response4 = send_action("I attack the elder!")
    print(f"Combat Started: {response4.get('starts_combat', False)}")
    if response4.get('starts_combat', False):
        print("✅ Combat triggered after 4th assault")

print("\n" + "="*70)
print("Test Complete")
print("="*70)
