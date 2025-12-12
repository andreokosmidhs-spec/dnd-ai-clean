#!/usr/bin/env python3
"""
NPC REACTION ENGINE ANALYSIS
Detailed analysis of specific NPC responses to understand implementation issues
"""

import requests
import json

BACKEND_URL = "https://dnd-wizard.preview.emergentagent.com/api"

def test_single_scenario():
    """Test a single scenario and analyze the response in detail"""
    
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
        "session_id": "test-npc-analysis",
        "player_message": "I approach the merchant to ask about the disturbance",
        "message_type": "action",
        "character_state": test_character,
        "world_state": test_world,
        "threat_level": 2
    }
    
    print("🧪 Testing NPC Reaction Engine - Merchant Approach Scenario")
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
        print(f"📝 Full Response Structure:")
        print(json.dumps(data, indent=2))
        
        narration = data.get("narration", "")
        print(f"\n📖 NARRATION ANALYSIS:")
        print(f"Length: {len(narration)} characters, {len(narration.split())} words")
        print(f"Content: {narration}")
        
        # Analyze for NPC actions
        print(f"\n🎭 NPC ACTION ANALYSIS:")
        action_verbs = [
            "steps", "moves", "turns", "looks", "glances", "shifts", "leans",
            "reaches", "crosses", "narrows", "widens", "raises", "lowers",
            "approaches", "backs", "straightens", "hunches", "tilts"
        ]
        
        found_actions = []
        for verb in action_verbs:
            if verb in narration.lower():
                found_actions.append(verb)
        
        if found_actions:
            print(f"✅ Action verbs found: {found_actions}")
        else:
            print(f"❌ No action verbs found in narration")
        
        # Check for ability checks
        print(f"\n🎲 ABILITY CHECK ANALYSIS:")
        if "mechanics" in data and data["mechanics"] and data["mechanics"]["check_request"]:
            check = data["mechanics"]["check_request"]
            print(f"✅ Ability check triggered: {check.get('skill', 'Unknown')} DC {check.get('dc', 'Unknown')}")
            print(f"   Reason: {check.get('reason', 'No reason provided')}")
        else:
            print(f"ℹ️ No ability check triggered (may be auto-success)")
        
        # Check for NPC tagging
        print(f"\n🏷️ NPC TAGGING ANALYSIS:")
        if "[[" in narration and "]]" in narration:
            import re
            npc_tags = re.findall(r'\[\[([^\]]+)\]\]', narration)
            print(f"✅ NPC tags found: {npc_tags}")
        else:
            print(f"❌ No NPC tags found in narration")
        
        # Check options
        print(f"\n🎯 OPTIONS ANALYSIS:")
        options = data.get("options", [])
        if options:
            print(f"✅ {len(options)} options provided:")
            for i, option in enumerate(options, 1):
                print(f"   {i}. {option}")
        else:
            print(f"ℹ️ No options provided")
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")

if __name__ == "__main__":
    test_single_scenario()