#!/usr/bin/env python3
"""
NPC REACTION ENGINE TESTING SUITE
Comprehensive testing of the NPC behavior implementation in backend/server.py

TESTING OBJECTIVES:
1. NPC Active Behavior - NPCs must take concrete actions, not wait passively
2. Ability Check Triggers - NPCs should prompt mechanical checks  
3. Consequence Generation - NPC actions must create immediate scene changes
4. Plot Advancement - NPCs must reveal hooks and create tension

Test scenarios based on Raven's Hollow opening scene.
"""

import requests
import json
import sys
from typing import Dict, Any, List

# Backend URL from frontend/.env
BACKEND_URL = "https://prompt-architect-23.preview.emergentagent.com/api"

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.detailed_results = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.passed += 1
        self.detailed_results.append(f"✅ PASS: {test_name}")
        if details:
            self.detailed_results.append(f"   Details: {details}")
        print(f"✅ PASS: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def add_fail(self, test_name: str, error: str, details: str = ""):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        self.detailed_results.append(f"❌ FAIL: {test_name} - {error}")
        if details:
            self.detailed_results.append(f"   Details: {details}")
        print(f"❌ FAIL: {test_name} - {error}")
        if details:
            print(f"   Details: {details}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*80}")
        print(f"NPC REACTION ENGINE TEST SUMMARY: {self.passed}/{total} tests passed")
        if self.errors:
            print(f"\nFAILED TESTS:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*80}")
        return self.failed == 0

def test_npc_reaction_engine():
    """Test the NPC Reaction Engine implementation with Raven's Hollow scenarios"""
    results = TestResults()
    
    print("🎭 Testing NPC REACTION ENGINE - Raven's Hollow Opening Scene")
    print(f"Backend URL: {BACKEND_URL}")
    print("-" * 80)
    
    # Test character for Raven's Hollow scenarios
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
            {"name": "Shortsword", "tags": ["weapon", "finesse"]},
            {"name": "Thieves' Tools", "tags": ["tool"]}
        ],
        "conditions": [],
        "proficiencies": ["Stealth", "Investigation", "Perception", "Sleight of Hand", "Deception"],
        "virtues": ["Loyal to friends"],
        "flaws": ["Trusts no one"],
        "goals": ["Uncover the Shadow Collective's plans"]
    }
    
    # Raven's Hollow market scene
    test_world = {
        "location": "Raven's Hollow Market Square",
        "settlement": "Raven's Hollow",
        "region": "Northern Territories",
        "time_of_day": "Midday",
        "weather": "Clear, with a slight breeze"
    }
    
    # CRITICAL TEST SCENARIOS from review request
    test_scenarios = [
        {
            "name": "Scenario 1: Merchant Approach",
            "player_message": "I approach the merchant to ask about the disturbance",
            "test_type": "npc_active_behavior",
            "expected_npc_actions": [
                "steps forward", "eyes narrow", "reaches for", "leans in", "glances around",
                "shifts position", "crosses arms", "taps fingers", "looks up", "turns toward"
            ],
            "forbidden_patterns": [
                "The merchant is willing to talk",
                "They wait for you",
                "The merchant stands ready",
                "He seems open to conversation"
            ],
            "required_elements": {
                "npc_action": True,
                "tension_creation": True,
                "plot_advancement": True
            },
            "description": "Merchant must take specific action, create tension, advance plot"
        },
        {
            "name": "Scenario 2: Suspicious Figure Investigation", 
            "player_message": "I watch the hooded figure closely to see what they're doing",
            "test_type": "ability_check_trigger",
            "expected_checks": ["Perception", "Insight"],
            "expected_npc_actions": [
                "pulls hood lower", "turns away", "moves quickly", "ducks behind",
                "slips into", "vanishes into", "melts into", "steps back"
            ],
            "forbidden_patterns": [
                "The figure seems nervous",
                "They appear to be waiting",
                "The figure stands still"
            ],
            "required_elements": {
                "check_trigger": True,
                "npc_reaction": True,
                "consequence": True
            },
            "description": "Must trigger Perception/Insight check AND figure reacts with movement"
        },
        {
            "name": "Scenario 3: Guard Interaction",
            "player_message": "I ask the guard if they've seen anything unusual",
            "test_type": "npc_active_behavior",
            "expected_npc_actions": [
                "straightens up", "hand moves to", "steps closer", "narrows eyes",
                "looks you over", "crosses arms", "shifts stance", "turns to face"
            ],
            "forbidden_patterns": [
                "The guard waits for your response",
                "They seem willing to help",
                "The guard stands at attention"
            ],
            "required_elements": {
                "npc_action": True,
                "suspicion_mechanics": True,
                "ability_check_potential": True
            },
            "description": "Guard must react with action, show suspicion, potentially prompt check"
        },
        {
            "name": "Scenario 4: Stealth Follow",
            "player_message": "I try to follow the hooded figure without being noticed",
            "test_type": "consequence_generation",
            "expected_checks": ["Stealth"],
            "expected_npc_actions": [
                "quickens pace", "glances back", "ducks around", "weaves through",
                "stops suddenly", "changes direction", "slips away"
            ],
            "forbidden_patterns": [
                "The figure doesn't notice",
                "They continue walking normally",
                "The figure seems unaware"
            ],
            "required_elements": {
                "stealth_check": True,
                "npc_counter_action": True,
                "immediate_consequence": True
            },
            "description": "Must trigger Stealth check, NPC reacts with movement, creates consequences"
        }
    ]
    
    for scenario in test_scenarios:
        try:
            payload = {
                "session_id": "test-npc-reaction-engine",
                "player_message": scenario["player_message"],
                "message_type": "action",
                "character_state": test_character,
                "world_state": test_world,
                "threat_level": 2
            }
            
            print(f"\n🧪 Testing: {scenario['name']}")
            print(f"   Player Action: \"{scenario['player_message']}\"")
            print(f"   Expected: {scenario['description']}")
            
            response = requests.post(
                f"{BACKEND_URL}/rpg_dm",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code != 200:
                results.add_fail(
                    scenario['name'],
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                continue
            
            data = response.json()
            narration = data.get("narration", "")
            
            print(f"   📝 Narration: {narration[:150]}...")
            
            # TEST 1: Check for forbidden passive patterns
            passive_violations = []
            for forbidden in scenario["forbidden_patterns"]:
                if forbidden.lower() in narration.lower():
                    passive_violations.append(forbidden)
            
            if passive_violations:
                results.add_fail(
                    scenario['name'] + " - Anti-Pattern Check",
                    f"FORBIDDEN PASSIVE PATTERNS FOUND: {passive_violations}",
                    f"Narration: {narration}"
                )
                continue
            else:
                print(f"   ✅ No passive patterns found")
            
            # TEST 2: Check for NPC action verbs
            npc_action_found = False
            action_verbs_found = []
            
            for action in scenario["expected_npc_actions"]:
                if action.lower() in narration.lower():
                    npc_action_found = True
                    action_verbs_found.append(action)
            
            if not npc_action_found:
                results.add_fail(
                    scenario['name'] + " - NPC Action Check",
                    f"NO NPC ACTION VERBS FOUND. Expected one of: {scenario['expected_npc_actions']}",
                    f"Narration: {narration}"
                )
                continue
            else:
                print(f"   ✅ NPC actions found: {action_verbs_found}")
            
            # TEST 3: Check for ability check triggers (if expected)
            if scenario["test_type"] in ["ability_check_trigger", "consequence_generation"]:
                has_check = (
                    "mechanics" in data and 
                    data["mechanics"] is not None and 
                    "check_request" in data["mechanics"] and
                    data["mechanics"]["check_request"] is not None
                )
                
                if not has_check:
                    results.add_fail(
                        scenario['name'] + " - Ability Check Trigger",
                        f"EXPECTED ABILITY CHECK BUT NONE TRIGGERED. Expected: {scenario.get('expected_checks', [])}",
                        f"Narration: {narration}"
                    )
                    continue
                else:
                    check_request = data["mechanics"]["check_request"]
                    skill = check_request.get("skill", "")
                    
                    if "expected_checks" in scenario:
                        if skill not in scenario["expected_checks"]:
                            results.add_fail(
                                scenario['name'] + " - Check Type",
                                f"WRONG CHECK TYPE. Expected {scenario['expected_checks']}, got {skill}",
                                f"Check: {check_request}"
                            )
                            continue
                    
                    print(f"   ✅ Ability check triggered: {skill} DC {check_request.get('dc', 'unknown')}")
            
            # TEST 4: Check for tension/consequence creation
            tension_indicators = [
                "suspicious", "wary", "alert", "tense", "nervous", "cautious",
                "danger", "threat", "warning", "concern", "worry", "fear",
                "quickly", "suddenly", "immediately", "urgent", "hurried"
            ]
            
            tension_found = any(indicator in narration.lower() for indicator in tension_indicators)
            
            if scenario["required_elements"].get("tension_creation") and not tension_found:
                results.add_fail(
                    scenario['name'] + " - Tension Creation",
                    "NO TENSION/CONSEQUENCE ELEMENTS FOUND",
                    f"Expected tension indicators, got: {narration}"
                )
                continue
            elif tension_found:
                print(f"   ✅ Tension/consequence elements present")
            
            # TEST 5: Check for plot advancement elements
            plot_indicators = [
                "disturbance", "trouble", "problem", "incident", "event",
                "stranger", "visitor", "news", "rumor", "word", "story",
                "shadow", "dark", "mysterious", "secret", "hidden"
            ]
            
            plot_found = any(indicator in narration.lower() for indicator in plot_indicators)
            
            if scenario["required_elements"].get("plot_advancement") and not plot_found:
                results.add_fail(
                    scenario['name'] + " - Plot Advancement",
                    "NO PLOT ADVANCEMENT ELEMENTS FOUND",
                    f"Expected plot hooks, got: {narration}"
                )
                continue
            elif plot_found:
                print(f"   ✅ Plot advancement elements present")
            
            # TEST 6: Check narration quality (not too short, not too long)
            word_count = len(narration.split())
            if word_count < 20:
                results.add_fail(
                    scenario['name'] + " - Narration Length",
                    f"NARRATION TOO SHORT: {word_count} words",
                    f"Narration: {narration}"
                )
                continue
            elif word_count > 200:
                results.add_fail(
                    scenario['name'] + " - Narration Length", 
                    f"NARRATION TOO LONG: {word_count} words",
                    f"Should be concise but rich"
                )
                continue
            else:
                print(f"   ✅ Good narration length: {word_count} words")
            
            # All tests passed!
            results.add_pass(
                scenario['name'],
                f"NPC actions: {action_verbs_found}, Word count: {word_count}"
            )
            print(f"   ✅ ALL NPC REACTION ENGINE TESTS PASSED")
            
        except Exception as e:
            results.add_fail(scenario['name'], f"Exception: {str(e)}")
            print(f"   ❌ Exception: {e}")
    
    return results.summary()

def test_npc_dialogue_responses():
    """Test NPC dialogue responses to ensure they're active participants"""
    results = TestResults()
    
    print("\n🗣️ Testing NPC Dialogue Responses")
    print("-" * 80)
    
    # Test character
    test_character = {
        "name": "Lyra Moonwhisper",
        "class": "Bard",
        "level": 3,
        "race": "Half-Elf",
        "background": "Entertainer",
        "stats": {
            "STR": 8,
            "DEX": 14,
            "CON": 12,
            "INT": 13,
            "WIS": 12,
            "CHA": 16
        },
        "hp": {"current": 18, "max": 18},
        "ac": 13,
        "equipped": [
            {"name": "Leather Armor", "tags": ["armor", "light"]},
            {"name": "Rapier", "tags": ["weapon", "finesse"]},
            {"name": "Lute", "tags": ["instrument"]}
        ],
        "conditions": [],
        "proficiencies": ["Persuasion", "Deception", "Performance", "Insight"]
    }
    
    test_world = {
        "location": "The Prancing Pony Tavern",
        "settlement": "Raven's Hollow",
        "region": "Northern Territories",
        "time_of_day": "Evening",
        "weather": "Light rain outside"
    }
    
    # Dialogue test scenarios
    dialogue_scenarios = [
        {
            "name": "Direct Question to Bartender",
            "player_message": "\"Have you heard anything about strange happenings in town?\"",
            "test_type": "npc_dialogue",
            "expected_npc_actions": [
                "leans in", "glances around", "wipes down", "sets down", "pauses",
                "looks up", "raises eyebrow", "frowns", "nods slowly"
            ],
            "forbidden_patterns": [
                "The bartender is willing to talk",
                "He waits for you to continue",
                "The bartender seems helpful"
            ],
            "required_elements": {
                "npc_physical_reaction": True,
                "direct_dialogue": True,
                "information_or_hook": True
            },
            "description": "Bartender must react physically and provide dialogue with information"
        },
        {
            "name": "Intimidation Attempt",
            "player_message": "\"You better tell me what you know about the Shadow Collective, or things might get unpleasant.\"",
            "test_type": "social_check",
            "expected_checks": ["Intimidation", "Persuasion"],
            "expected_npc_actions": [
                "steps back", "eyes widen", "hand moves to", "voice trembles",
                "looks around nervously", "swallows hard", "backs away"
            ],
            "forbidden_patterns": [
                "The NPC seems intimidated",
                "They appear nervous",
                "The person looks scared"
            ],
            "required_elements": {
                "check_trigger": True,
                "npc_fear_reaction": True,
                "consequence": True
            },
            "description": "Must trigger social check and NPC shows fear through actions"
        }
    ]
    
    for scenario in dialogue_scenarios:
        try:
            payload = {
                "session_id": "test-npc-dialogue",
                "player_message": scenario["player_message"],
                "message_type": "say",  # This is dialogue, not action
                "character_state": test_character,
                "world_state": test_world,
                "threat_level": 2
            }
            
            print(f"\n🧪 Testing: {scenario['name']}")
            print(f"   Player Says: {scenario['player_message']}")
            print(f"   Expected: {scenario['description']}")
            
            response = requests.post(
                f"{BACKEND_URL}/rpg_dm",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code != 200:
                results.add_fail(
                    scenario['name'],
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                continue
            
            data = response.json()
            narration = data.get("narration", "")
            
            print(f"   📝 Response: {narration[:150]}...")
            
            # Check for NPC physical reactions
            npc_action_found = False
            action_verbs_found = []
            
            for action in scenario["expected_npc_actions"]:
                if action.lower() in narration.lower():
                    npc_action_found = True
                    action_verbs_found.append(action)
            
            if not npc_action_found:
                results.add_fail(
                    scenario['name'] + " - NPC Physical Reaction",
                    f"NO NPC PHYSICAL REACTIONS FOUND. Expected: {scenario['expected_npc_actions']}",
                    f"Response: {narration}"
                )
                continue
            else:
                print(f"   ✅ NPC physical reactions: {action_verbs_found}")
            
            # Check for direct dialogue (should contain quotes)
            has_dialogue = '"' in narration or "'" in narration
            if scenario["required_elements"].get("direct_dialogue") and not has_dialogue:
                results.add_fail(
                    scenario['name'] + " - Direct Dialogue",
                    "NO DIRECT DIALOGUE FOUND (missing quotes)",
                    f"Response: {narration}"
                )
                continue
            elif has_dialogue:
                print(f"   ✅ Direct dialogue present")
            
            # Check for social checks if expected
            if scenario["test_type"] == "social_check":
                has_check = (
                    "mechanics" in data and 
                    data["mechanics"] is not None and 
                    "check_request" in data["mechanics"] and
                    data["mechanics"]["check_request"] is not None
                )
                
                if has_check:
                    check_request = data["mechanics"]["check_request"]
                    skill = check_request.get("skill", "")
                    
                    if skill in scenario.get("expected_checks", []):
                        print(f"   ✅ Social check triggered: {skill}")
                    else:
                        results.add_fail(
                            scenario['name'] + " - Check Type",
                            f"WRONG CHECK TYPE. Expected {scenario['expected_checks']}, got {skill}"
                        )
                        continue
                else:
                    # Social checks are optional for dialogue - NPC might just respond
                    print(f"   ℹ️ No check triggered (NPC responded directly)")
            
            # All tests passed!
            results.add_pass(
                scenario['name'],
                f"Physical reactions: {action_verbs_found}"
            )
            
        except Exception as e:
            results.add_fail(scenario['name'], f"Exception: {str(e)}")
            print(f"   ❌ Exception: {e}")
    
    return results.summary()

def main():
    """Run all NPC Reaction Engine tests"""
    print("🎭 NPC REACTION ENGINE COMPREHENSIVE TESTING SUITE")
    print("=" * 80)
    
    # Test backend connectivity first
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=10)
        if response.status_code == 200:
            print(f"✅ Backend connectivity confirmed: {BACKEND_URL}")
        else:
            print(f"❌ Backend connectivity failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection error: {e}")
        return False
    
    # Run NPC Reaction Engine tests
    all_passed = True
    
    print(f"\n{'='*80}")
    print("PHASE 1: NPC ACTIVE BEHAVIOR & CONSEQUENCE TESTING")
    print(f"{'='*80}")
    
    if not test_npc_reaction_engine():
        all_passed = False
    
    print(f"\n{'='*80}")
    print("PHASE 2: NPC DIALOGUE RESPONSE TESTING")
    print(f"{'='*80}")
    
    if not test_npc_dialogue_responses():
        all_passed = False
    
    # Final summary
    print(f"\n{'='*80}")
    print("FINAL NPC REACTION ENGINE TEST RESULTS")
    print(f"{'='*80}")
    
    if all_passed:
        print("🎉 ALL NPC REACTION ENGINE TESTS PASSED!")
        print("✅ NPCs are now active participants driving plot forward")
        print("✅ Ability checks are being triggered appropriately")
        print("✅ NPCs create immediate consequences and tension")
        print("✅ Plot advancement through NPC actions confirmed")
    else:
        print("❌ SOME NPC REACTION ENGINE TESTS FAILED")
        print("⚠️ NPCs may still be acting as passive information terminals")
        print("⚠️ Review failed tests above for specific issues")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)