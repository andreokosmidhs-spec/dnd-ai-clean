#!/usr/bin/env python3
"""
Focused Combat Mechanics Test - With Specific Target
"""

import requests
import json

BACKEND_URL = "https://dnd-ai-clean-test.preview.emergentagent.com/api"

def test_combat_with_target():
    """Test combat mechanics with specific target"""
    print("🗡️ Testing Combat Mechanics with Specific Target")
    print("="*60)
    
    # Get latest campaign
    response = requests.get(f"{BACKEND_URL}/campaigns/latest", timeout=30)
    if response.status_code != 200:
        print(f"❌ Failed to get campaign: {response.status_code}")
        return
    
    campaign_data = response.json()
    campaign_id = campaign_data["campaign_id"]
    character_id = campaign_data["character_id"]
    
    print(f"Campaign: {campaign_id}")
    print(f"Character: {character_id}")
    
    # First, set up a combat scenario in a dungeon
    setup_payload = {
        "campaign_id": campaign_id,
        "character_id": character_id,
        "player_action": "I enter the dark dungeon and encounter a skeleton warrior"
    }
    
    print(f"\n🏰 Setting up dungeon encounter...")
    response = requests.post(
        f"{BACKEND_URL}/rpg_dm/action",
        json=setup_payload,
        headers={"Content-Type": "application/json"},
        timeout=45
    )
    
    if response.status_code == 200:
        setup_data = response.json()
        print(f"Setup narration: {setup_data.get('narration', '')[:200]}...")
    
    # Test combat action with specific target
    combat_payload = {
        "campaign_id": campaign_id,
        "character_id": character_id,
        "player_action": "I attack the skeleton warrior with my sword",
        "client_target_id": "skeleton_warrior"  # Try with explicit target
    }
    
    print(f"\n🗡️ Testing combat action with specific target...")
    response = requests.post(
        f"{BACKEND_URL}/rpg_dm/action",
        json=combat_payload,
        headers={"Content-Type": "application/json"},
        timeout=45
    )
    
    if response.status_code != 200:
        print(f"❌ Combat action failed: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    data = response.json()
    
    print(f"\n📊 Combat Response Analysis:")
    print(f"Status Code: {response.status_code}")
    print(f"Response Keys: {list(data.keys())}")
    
    if "narration" in data:
        narration = data["narration"]
        print(f"Narration Length: {len(narration)} chars")
        print(f"Narration: {narration}")
    
    # Check for mechanics field
    if "mechanics" in data:
        mechanics = data["mechanics"]
        print(f"✅ Mechanics field present: {mechanics}")
    else:
        print("❌ No mechanics field in response")
    
    # Check for combat_state
    if "combat_state" in data:
        combat_state = data["combat_state"]
        print(f"✅ Combat state present: {combat_state}")
    else:
        print("❌ No combat_state field in response")
    
    # Check for player_updates (might contain combat info)
    if "player_updates" in data:
        player_updates = data["player_updates"]
        print(f"Player Updates: {player_updates}")
        
        if player_updates and "hp" in str(player_updates):
            print("✅ HP changes detected in player_updates")
    
    # Check for world_state_update (might contain enemy info)
    if "world_state_update" in data:
        world_state_update = data["world_state_update"]
        print(f"World State Update: {world_state_update}")
        
        if world_state_update and ("enemy" in str(world_state_update) or "combat" in str(world_state_update)):
            print("✅ Combat info detected in world_state_update")
    
    print(f"\n📋 Full Response:")
    print(json.dumps(data, indent=2))
    
    # Test another combat action to see if combat continues
    print(f"\n🗡️ Testing second combat action...")
    combat_payload2 = {
        "campaign_id": campaign_id,
        "character_id": character_id,
        "player_action": "I strike again at the skeleton"
    }
    
    response2 = requests.post(
        f"{BACKEND_URL}/rpg_dm/action",
        json=combat_payload2,
        headers={"Content-Type": "application/json"},
        timeout=45
    )
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"Second attack narration: {data2.get('narration', '')}")
        print(f"Second attack has mechanics: {'mechanics' in data2}")
        if "mechanics" in data2:
            print(f"Second attack mechanics: {data2['mechanics']}")

if __name__ == "__main__":
    test_combat_with_target()