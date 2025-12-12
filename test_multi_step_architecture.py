#!/usr/bin/env python3
"""
Manual test to demonstrate the Multi-Step Architecture
Shows: Intent Tagger → DM → Repair pipeline in action
"""

import requests
import json

BACKEND_URL = "https://dnd-wizard.preview.emergentagent.com/api"

def test_scenario(scenario_name, player_message):
    """Test a single scenario and show the complete pipeline"""
    
    print(f"\n{'='*80}")
    print(f"SCENARIO: {scenario_name}")
    print(f"{'='*80}")
    print(f"Player action: \"{player_message}\"")
    print()
    
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
        "proficiencies": ["Stealth", "Investigation", "Perception", "Deception", "Insight"]
    }
    
    test_world = {
        "location": "Raven's Hollow Market Square",
        "settlement": "Raven's Hollow",
        "region": "Northern Territories",
        "time_of_day": "Midday",
        "weather": "Clear, warm"
    }
    
    payload = {
        "session_id": f"test-multi-step-{scenario_name.lower().replace(' ', '-')}",
        "player_message": player_message,
        "message_type": "action",
        "character_state": test_character,
        "world_state": test_world,
        "threat_level": 2
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        
        print("RESPONSE ANALYSIS:")
        print("-" * 80)
        
        # Check narration
        narration = data.get("narration", "")
        print(f"\n📖 NARRATION ({len(narration)} chars):")
        print(narration)
        
        # Check for ability check
        print(f"\n🎲 ABILITY CHECK:")
        if "mechanics" in data and data["mechanics"] and data["mechanics"].get("check_request"):
            check = data["mechanics"]["check_request"]
            print(f"✅ CHECK TRIGGERED")
            print(f"   Ability: {check.get('ability')}")
            print(f"   Skill: {check.get('skill')}")
            print(f"   DC: {check.get('dc')}")
            print(f"   Reason: {check.get('reason')}")
            print(f"   On Success: {check.get('on_success')}")
            print(f"   On Fail: {check.get('on_fail')}")
        else:
            print(f"ℹ️  No ability check (may be auto-success)")
        
        # Check for NPC actions
        print(f"\n🎭 NPC BEHAVIOR ANALYSIS:")
        action_verbs = [
            "steps", "moves", "turns", "looks", "glances", "shifts", "leans",
            "reaches", "crosses", "narrows", "widens", "raises", "lowers",
            "approaches", "backs", "straightens", "calls", "shouts", "whispers"
        ]
        
        found_actions = []
        narration_lower = narration.lower()
        for verb in action_verbs:
            if verb in narration_lower:
                found_actions.append(verb)
        
        if found_actions:
            print(f"✅ NPC action verbs found: {', '.join(found_actions)}")
        else:
            print(f"⚠️  No strong NPC action verbs detected")
        
        # Check for forbidden patterns
        forbidden = ["seems willing", "remains available", "waits for", "appears open"]
        found_forbidden = [p for p in forbidden if p in narration_lower]
        if found_forbidden:
            print(f"❌ Forbidden passive patterns found: {', '.join(found_forbidden)}")
        else:
            print(f"✅ No forbidden passive patterns")
        
        # Check options
        print(f"\n🎯 OPTIONS:")
        options = data.get("options", [])
        if options:
            for i, option in enumerate(options, 1):
                print(f"   {i}. {option}")
        else:
            print(f"   (No options provided)")
        
        print()
        
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("MULTI-STEP ARCHITECTURE TEST SUITE")
    print("Testing: Intent Tagger → DM → Repair pipeline")
    print("="*80)
    
    # Test the 4 critical scenarios
    test_scenario(
        "Stealth Action",
        "I try to follow the hooded figure discreetly without being noticed"
    )
    
    test_scenario(
        "Social Deception",
        "I lie to the guard and say I'm investigating on behalf of the city council"
    )
    
    test_scenario(
        "NPC Action",
        "I approach the merchant to ask about strange activity"
    )
    
    test_scenario(
        "Insight Check",
        "I watch the guard's body language for signs of deception"
    )
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
