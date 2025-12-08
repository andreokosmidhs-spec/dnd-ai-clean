#!/usr/bin/env python3
"""
Detailed Combat & Targeting Tests
"""

import requests
import json

API_URL = "http://localhost:8001/api"
CAMPAIGN_ID = "bb90306f-7eb3-4bf2-97a5-928b234d56c4"
CHARACTER_ID = "4beab239-48e9-4fee-996e-0c5515aee533"

def send_action(action: str, target_id: str = None):
    payload = {
        "campaign_id": CAMPAIGN_ID,
        "character_id": CHARACTER_ID,
        "player_action": action,
        "client_target_id": target_id
    }
    response = requests.post(f"{API_URL}/rpg_dm/action", json=payload)
    return response.json()

print("="*70)
print("DETAILED INSPECTION: Location Continuity Issue")
print("="*70)
print()

# Test the innkeeper issue more carefully
print("Step 1: Travel explicitly to ruins")
response = send_action("I leave the village and travel to the Shattered Tower ruins. I want to explore the abandoned structure.")
print(f"Response:")
print(json.dumps(response, indent=2))
print("\n" + "="*70 + "\n")

import time
time.sleep(2)

print("Step 2: In the ruins, I talk to the innkeeper (SHOULD FAIL)")
response = send_action("I talk to the innkeeper.")
print(f"Full Response:")
print(json.dumps(response, indent=2))

narration = response.get('narration', '')
location = response.get('world_state_update', {}).get('current_location', 'NOT SET')

print(f"\n--- ANALYSIS ---")
print(f"Location returned: {location}")
print(f"Full narration:\n{narration}")

# Check for failure
if "inn" in narration.lower() and any(word in narration.lower() for word in ['behind the counter', 'innkeeper', 'tankards', 'warm bread']):
    print("\n❌ CRITICAL BUG: Innkeeper spawned in wrong location!")
    print("Expected: DM should say there's no inn/innkeeper here")
    print("Actual: DM spawned an innkeeper with full tavern description")
elif "no inn" in narration.lower() or "isn't an inn" in narration.lower():
    print("\n✅ CORRECT: DM properly rejected innkeeper request")
else:
    print("\n⚠️ UNCLEAR: Response doesn't clearly accept or reject")

print("\n" + "="*70 + "\n")

