#!/usr/bin/env python3
"""
Test stealth scenario that should trigger ability check
"""

import requests
import json

BACKEND_URL = "https://dnd-wizard.preview.emergentagent.com/api"

def test_stealth_scenario():
    """Test stealth scenario that should definitely trigger a check"""
    
    test_character = {
        "name": "Kael Nightwhisper",
        "class": "Rogue",
        "level": 3,
        "race": "Half-Elf", 
        "background": "Criminal",
        "stats": {
            "STR": 10,
            "DEX": 16,
            "CON": 12,
            "INT": 14,
            "WIS": 13,
            "CHA": 15
        },
        "hp": {"current": 20, "max": 20},
        "ac": 15,
        "equipped": [
            {"name": "Leather Armor", "tags": ["armor", "light"]},
            {"name": "Shortsword", "tags": ["weapon", "finesse"]}
        ],
        "conditions": [],
        "proficiencies": ["Stealth", "Investigation", "Perception"]
    }
    
    test_world = {
        "location": "Raven's Hollow Market Square",
        "settlement": "Raven's Hollow",
        "region": "Northern Territories",
        "time_of_day": "Midday",
        "weather": "Clear, with a slight breeze"
    }
    
    payload = {
        "session_id": "test-stealth-check",
        "player_message": "I try to follow the hooded figure without being noticed",
        "message_type": "action",
        "character_state": test_character,
        "world_state": test_world,
        "threat_level": 2
    }
    
    print("🧪 Testing Stealth Scenario - Should Trigger Ability Check")
    print(f"Player Action: {payload['player_message']}")
    print("-" * 80)
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        
        print("✅ Response received successfully")
        
        narration = data.get("narration", "")
        print(f"\n📖 NARRATION:")
        print(f"Content: {narration}")
        
        # Check for ability checks
        print(f"\n🎲 ABILITY CHECK ANALYSIS:")
        if "mechanics" in data and data["mechanics"] and data["mechanics"]["check_request"]:
            check = data["mechanics"]["check_request"]
            print(f"✅ Ability check triggered: {check.get('skill', 'Unknown')} DC {check.get('dc', 'Unknown')}")
            print(f"   Ability: {check.get('ability', 'Unknown')}")
            print(f"   Reason: {check.get('reason', 'No reason provided')}")
            print(f"   On Success: {check.get('on_success', 'No success text')}")
            print(f"   On Fail: {check.get('on_fail', 'No fail text')}")
        else:
            print(f"❌ NO ABILITY CHECK TRIGGERED - This is a problem!")
            print(f"   Stealth actions should always trigger checks")
        
        # Analyze for NPC reactions
        print(f"\n🎭 NPC REACTION ANALYSIS:")
        npc_reactions = [
            "quickens", "glances back", "stops", "turns", "looks over",
            "ducks", "weaves", "slips", "moves", "changes direction"
        ]
        
        found_reactions = []
        for reaction in npc_reactions:
            if reaction in narration.lower():
                found_reactions.append(reaction)
        
        if found_reactions:
            print(f"✅ NPC reactions found: {found_reactions}")
        else:
            print(f"❌ No NPC reactions found - figure should react to being followed")
        
        print(f"\n📋 FULL RESPONSE:")
        print(json.dumps(data, indent=2))
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")

if __name__ == "__main__":
    test_stealth_scenario()