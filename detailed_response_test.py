#!/usr/bin/env python3
"""
Get detailed response from one test scenario to analyze what the AI is actually generating
"""

import requests
import json

# Backend URL from frontend/.env
BACKEND_URL = "https://dnd-ai-clean-test.preview.emergentagent.com/api"

def get_detailed_response():
    """Get a detailed response to analyze the AI output"""
    
    print("🔍 DETAILED RESPONSE ANALYSIS")
    print("=" * 50)
    
    # Test character
    test_character = {
        "name": "Lyra Nightwhisper",
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
        "proficiencies": ["Stealth", "Investigation", "Perception", "Deception"]
    }
    
    test_world = {
        "location": "Market Square",
        "settlement": "Raven's Hollow",
        "region": "Northern Territories",
        "time_of_day": "Midday",
        "weather": "Clear, warm"
    }
    
    # Test the stealth scenario that should trigger a check
    payload = {
        "session_id": "detailed-test",
        "player_message": "I try to follow the hooded figure discreetly without being noticed",
        "message_type": "action",
        "character_state": test_character,
        "world_state": test_world,
        "threat_level": 2
    }
    
    print("Testing: 'I try to follow the hooded figure discreetly without being noticed'")
    print("Expected: Stealth check should be triggered")
    print()
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=45
        )
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        
        print("FULL RESPONSE:")
        print("=" * 50)
        print(json.dumps(data, indent=2))
        print("=" * 50)
        
        # Analyze the response
        print("\nANALYSIS:")
        print("-" * 30)
        
        narration = data.get("narration", "")
        print(f"Narration length: {len(narration)} characters")
        print(f"Narration: {narration}")
        print()
        
        # Check mechanics
        if "mechanics" in data:
            mechanics = data["mechanics"]
            print(f"Mechanics field present: {mechanics is not None}")
            
            if mechanics and "check_request" in mechanics:
                check_request = mechanics["check_request"]
                print(f"Check request present: {check_request is not None}")
                
                if check_request:
                    print(f"Check details: {json.dumps(check_request, indent=2)}")
                else:
                    print("❌ check_request is null")
            else:
                print("❌ No check_request in mechanics")
        else:
            print("❌ No mechanics field in response")
        
        # Check options
        if "options" in data:
            options = data["options"]
            print(f"\nOptions count: {len(options) if options else 0}")
            if options:
                for i, option in enumerate(options, 1):
                    print(f"  {i}. {option}")
        
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    get_detailed_response()