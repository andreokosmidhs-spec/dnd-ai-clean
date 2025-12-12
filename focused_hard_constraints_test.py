#!/usr/bin/env python3
"""
Focused HARD CONSTRAINTS Test for NPC Reaction Engine
Tests the specific scenarios from the review request
"""

import requests
import json
import sys

# Backend URL from frontend/.env
BACKEND_URL = "https://dnd-wizard.preview.emergentagent.com/api"

def test_critical_scenarios():
    """Test the 4 high-priority scenarios from the review request"""
    
    print("⚡ FOCUSED HARD CONSTRAINTS TEST - NPC REACTION ENGINE")
    print("=" * 70)
    
    # Test character for Raven's Hollow market scene
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
    
    # Raven's Hollow market scene setup
    test_world = {
        "location": "Market Square",
        "settlement": "Raven's Hollow",
        "region": "Northern Territories",
        "time_of_day": "Midday",
        "weather": "Clear, warm"
    }
    
    # HIGH-PRIORITY TEST SCENARIOS
    scenarios = [
        {
            "name": "High-Priority Test: Stealth Action",
            "message": "I try to follow the hooded figure discreetly without being noticed",
            "expected": "mechanics.check_request with skill='Stealth', dc=12-16",
            "constraint": "CONSTRAINT #2 - ABILITY CHECK ENGINE IS MANDATORY"
        },
        {
            "name": "High-Priority Test: Social Deception",
            "message": "I lie to the guard and say I'm investigating on behalf of the city council",
            "expected": "mechanics.check_request with skill='Deception', dc=12-16",
            "constraint": "CONSTRAINT #2 - ABILITY CHECK ENGINE IS MANDATORY"
        },
        {
            "name": "High-Priority Test: NPC Action",
            "message": "I approach the merchant to ask about strange activity",
            "expected": "Merchant MUST take concrete action (not just 'willing to talk')",
            "constraint": "CONSTRAINT #1 - NPC ACTION IS MANDATORY"
        },
        {
            "name": "Medium-Priority Test: Consequence Branches",
            "message": "I watch the guard's body language for signs of deception",
            "expected": "mechanics.check_request with skill='Insight' AND NPC reaction",
            "constraint": "CONSTRAINT #1 + #2 - NPC ACTION + ABILITY CHECK"
        }
    ]
    
    results = {"passed": 0, "failed": 0, "details": []}
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   Player: \"{scenario['message']}\"")
        print(f"   Expected: {scenario['expected']}")
        print(f"   Testing: {scenario['constraint']}")
        
        try:
            payload = {
                "session_id": f"test-constraint-{i}",
                "player_message": scenario["message"],
                "message_type": "action",
                "character_state": test_character,
                "world_state": test_world,
                "threat_level": 2
            }
            
            response = requests.post(
                f"{BACKEND_URL}/rpg_dm",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=45
            )
            
            if response.status_code != 200:
                print(f"   ❌ HTTP Error: {response.status_code}")
                results["failed"] += 1
                results["details"].append(f"FAIL: {scenario['name']} - HTTP {response.status_code}")
                continue
            
            data = response.json()
            narration = data.get("narration", "")
            
            print(f"   📝 Narration: {narration[:100]}...")
            
            # Check for ability check (Constraints #2)
            if "stealth" in scenario["message"].lower() or "lie" in scenario["message"].lower() or "deception" in scenario["message"].lower():
                has_check = (
                    "mechanics" in data and 
                    data["mechanics"] is not None and 
                    "check_request" in data["mechanics"] and
                    data["mechanics"]["check_request"] is not None
                )
                
                if has_check:
                    check = data["mechanics"]["check_request"]
                    skill = check.get("skill", "")
                    dc = check.get("dc", 0)
                    print(f"   ✅ Ability Check: {skill} DC {dc}")
                    
                    # Validate expected skill
                    if ("stealth" in scenario["message"].lower() and skill == "Stealth") or \
                       ("lie" in scenario["message"].lower() and skill == "Deception"):
                        print(f"   ✅ Correct skill triggered")
                        results["passed"] += 1
                        results["details"].append(f"PASS: {scenario['name']} - {skill} check triggered")
                    else:
                        print(f"   ❌ Wrong skill: expected Stealth/Deception, got {skill}")
                        results["failed"] += 1
                        results["details"].append(f"FAIL: {scenario['name']} - Wrong skill: {skill}")
                else:
                    print(f"   ❌ CRITICAL FAILURE: No ability check triggered")
                    results["failed"] += 1
                    results["details"].append(f"FAIL: {scenario['name']} - No ability check")
            
            # Check for NPC actions (Constraint #1)
            elif "approach" in scenario["message"].lower() or "merchant" in scenario["message"].lower():
                # Look for concrete NPC action words
                action_words = ["steps", "eyes narrow", "leans", "reaches", "turns", "crosses arms", 
                               "shifts", "glances", "moves", "speaks", "calls", "signals"]
                
                npc_actions_found = []
                for action in action_words:
                    if action.lower() in narration.lower():
                        npc_actions_found.append(action)
                
                # Check for forbidden passive patterns
                forbidden = ["seems willing to talk", "remains available", "waits for your response",
                           "appears open to conversation", "is ready to help"]
                
                passive_found = []
                for pattern in forbidden:
                    if pattern.lower() in narration.lower():
                        passive_found.append(pattern)
                
                if npc_actions_found and not passive_found:
                    print(f"   ✅ NPC Actions: {npc_actions_found}")
                    print(f"   ✅ No passive patterns")
                    results["passed"] += 1
                    results["details"].append(f"PASS: {scenario['name']} - NPC actions: {npc_actions_found}")
                elif passive_found:
                    print(f"   ❌ FORBIDDEN passive patterns: {passive_found}")
                    results["failed"] += 1
                    results["details"].append(f"FAIL: {scenario['name']} - Passive patterns: {passive_found}")
                else:
                    print(f"   ❌ No concrete NPC actions found")
                    results["failed"] += 1
                    results["details"].append(f"FAIL: {scenario['name']} - No NPC actions")
            
            # Check for both NPC action AND ability check
            elif "watch" in scenario["message"].lower() and "guard" in scenario["message"].lower():
                # Check for Insight check
                has_check = (
                    "mechanics" in data and 
                    data["mechanics"] is not None and 
                    "check_request" in data["mechanics"] and
                    data["mechanics"]["check_request"] is not None
                )
                
                # Check for NPC reaction
                reaction_words = ["shifts uncomfortably", "avoids eye contact", "tenses", "fidgets",
                                "defensive stance", "crosses arms", "steps back"]
                
                npc_reactions = []
                for reaction in reaction_words:
                    if reaction.lower() in narration.lower():
                        npc_reactions.append(reaction)
                
                if has_check and npc_reactions:
                    check = data["mechanics"]["check_request"]
                    skill = check.get("skill", "")
                    print(f"   ✅ Ability Check: {skill}")
                    print(f"   ✅ NPC Reactions: {npc_reactions}")
                    results["passed"] += 1
                    results["details"].append(f"PASS: {scenario['name']} - Both check and NPC reaction")
                elif has_check:
                    print(f"   ✅ Ability Check: {data['mechanics']['check_request'].get('skill')}")
                    print(f"   ❌ No NPC reactions found")
                    results["failed"] += 1
                    results["details"].append(f"FAIL: {scenario['name']} - Missing NPC reaction")
                elif npc_reactions:
                    print(f"   ❌ No ability check")
                    print(f"   ✅ NPC Reactions: {npc_reactions}")
                    results["failed"] += 1
                    results["details"].append(f"FAIL: {scenario['name']} - Missing ability check")
                else:
                    print(f"   ❌ No ability check AND no NPC reactions")
                    results["failed"] += 1
                    results["details"].append(f"FAIL: {scenario['name']} - Missing both")
            
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            results["failed"] += 1
            results["details"].append(f"FAIL: {scenario['name']} - Exception: {str(e)}")
    
    # Final Results
    print("\n" + "=" * 70)
    print("🎯 HARD CONSTRAINTS TEST RESULTS")
    print("=" * 70)
    
    total = results["passed"] + results["failed"]
    print(f"PASSED: {results['passed']}/{total}")
    print(f"FAILED: {results['failed']}/{total}")
    
    print(f"\nDETAILS:")
    for detail in results["details"]:
        if detail.startswith("PASS"):
            print(f"✅ {detail}")
        else:
            print(f"❌ {detail}")
    
    # SUCCESS METRICS from review request
    print(f"\n📊 SUCCESS METRICS:")
    if results["passed"] == 4:
        print("✅ PASS: 4/4 high-priority tests trigger expected behavior")
        print("✅ VERDICT: HARD CONSTRAINTS are working!")
        return True
    elif results["passed"] >= 2:
        print(f"⚠️ PARTIAL: {results['passed']}/4 high-priority tests pass")
        print("⚠️ VERDICT: HARD CONSTRAINTS partially working")
        return False
    else:
        print(f"❌ FAIL: {results['passed']}/4 high-priority tests pass")
        print("❌ VERDICT: HARD CONSTRAINTS not working")
        return False

if __name__ == "__main__":
    success = test_critical_scenarios()
    sys.exit(0 if success else 1)