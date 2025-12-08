#!/usr/bin/env python3
"""
Combat Mechanics Test - Attack Active NPC
"""

import requests
import json

BACKEND_URL = "https://prompt-architect-23.preview.emergentagent.com/api"

def test_combat_with_active_npc():
    """Test combat mechanics with an active NPC"""
    print("🗡️ Testing Combat Mechanics with Active NPC")
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
    
    # Test combat action with one of the active NPCs
    combat_payload = {
        "campaign_id": campaign_id,
        "character_id": character_id,
        "player_action": "I attack Marek the Shadow with my sword"
    }
    
    print(f"\n🗡️ Testing combat action against Marek the Shadow...")
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
    
    # Check all possible fields that might contain combat mechanics
    fields_to_check = ["mechanics", "combat_state", "combat_data", "dice_roll", "attack_result"]
    
    for field in fields_to_check:
        if field in data:
            print(f"✅ {field} field present: {data[field]}")
        else:
            print(f"❌ No {field} field in response")
    
    # Check for combat keywords in narration
    if "narration" in data:
        narration_lower = data["narration"].lower()
        combat_keywords = ["attack", "hit", "miss", "damage", "sword", "weapon", "strike", "combat", "roll", "d20"]
        found_keywords = [kw for kw in combat_keywords if kw in narration_lower]
        print(f"Combat Keywords in Narration: {found_keywords}")
        
        # Check if it mentions dice or numbers
        import re
        numbers = re.findall(r'\d+', narration)
        if numbers:
            print(f"Numbers in narration: {numbers}")
    
    # Check player_updates for HP changes
    if "player_updates" in data and data["player_updates"]:
        player_updates = data["player_updates"]
        print(f"Player Updates: {player_updates}")
        
        if "hp" in str(player_updates).lower():
            print("✅ HP changes detected")
    
    # Check world_state_update for combat state
    if "world_state_update" in data and data["world_state_update"]:
        world_state_update = data["world_state_update"]
        print(f"World State Update: {world_state_update}")
        
        if "combat" in str(world_state_update).lower():
            print("✅ Combat state changes detected")
    
    print(f"\n📋 Full Response:")
    print(json.dumps(data, indent=2))
    
    # Try with explicit client_target_id
    print(f"\n🎯 Testing with explicit target ID...")
    combat_payload_targeted = {
        "campaign_id": campaign_id,
        "character_id": character_id,
        "player_action": "I attack with my sword",
        "client_target_id": "marek_the_shadow"
    }
    
    response_targeted = requests.post(
        f"{BACKEND_URL}/rpg_dm/action",
        json=combat_payload_targeted,
        headers={"Content-Type": "application/json"},
        timeout=45
    )
    
    if response_targeted.status_code == 200:
        data_targeted = response_targeted.json()
        print(f"Targeted attack narration: {data_targeted.get('narration', '')}")
        print(f"Targeted attack has mechanics: {'mechanics' in data_targeted}")
        if "mechanics" in data_targeted:
            print(f"Targeted attack mechanics: {data_targeted['mechanics']}")
        
        # Check if this triggers combat
        narration_targeted = data_targeted.get('narration', '').lower()
        if any(word in narration_targeted for word in ['attack', 'hit', 'miss', 'damage', 'combat']):
            print("✅ Combat-related content in targeted attack")
        else:
            print("❌ No combat content in targeted attack")

if __name__ == "__main__":
    test_combat_with_active_npc()