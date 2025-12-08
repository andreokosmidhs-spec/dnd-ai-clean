#!/usr/bin/env python3
"""
Focused Combat Mechanics Test
Test the specific issue with combat mechanics not being returned
"""

import requests
import json

BACKEND_URL = "https://dnd-ai-clean-test.preview.emergentagent.com/api"

def test_combat_mechanics():
    """Test combat mechanics specifically"""
    print("🗡️ Testing Combat Mechanics")
    print("="*50)
    
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
    
    # Test combat action
    combat_payload = {
        "campaign_id": campaign_id,
        "character_id": character_id,
        "player_action": "I attack the skeleton with my sword"
    }
    
    print(f"\n🗡️ Testing combat action...")
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
    
    print(f"\n📊 Response Analysis:")
    print(f"Status Code: {response.status_code}")
    print(f"Response Keys: {list(data.keys())}")
    
    if "narration" in data:
        narration = data["narration"]
        print(f"Narration Length: {len(narration)} chars")
        print(f"Narration Sample: {narration[:200]}...")
    
    if "mechanics" in data:
        mechanics = data["mechanics"]
        print(f"Mechanics: {mechanics}")
        
        if mechanics and isinstance(mechanics, dict):
            print(f"Mechanics Keys: {list(mechanics.keys())}")
            
            # Check for combat-specific fields
            combat_fields = ["attack_roll", "damage", "hit", "miss", "hp_change", "ac_check"]
            found_combat = [field for field in combat_fields if field in str(mechanics)]
            print(f"Combat Fields Found: {found_combat}")
        else:
            print("❌ Mechanics is empty or not a dict")
    else:
        print("❌ No mechanics field in response")
    
    if "options" in data:
        options = data["options"]
        print(f"Options: {len(options) if options else 0} provided")
        if options:
            for i, option in enumerate(options[:3]):
                print(f"  {i+1}. {option}")
    
    # Check for combat-related keywords in narration
    if "narration" in data:
        narration_lower = data["narration"].lower()
        combat_keywords = ["attack", "hit", "miss", "damage", "sword", "weapon", "strike", "combat"]
        found_keywords = [kw for kw in combat_keywords if kw in narration_lower]
        print(f"Combat Keywords in Narration: {found_keywords}")
    
    print(f"\n📋 Full Response:")
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    test_combat_mechanics()