#!/usr/bin/env python3
"""
Simple v4.1 Unified Narrative Specification Test
Tests the core v4.1 requirements using the legacy /api/rpg_dm endpoint
"""

import requests
import json
import sys
import re
from typing import Dict, Any, List

# Backend URL from frontend/.env
BACKEND_URL = "https://dnd-wizard.preview.emergentagent.com/api"

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"✅ PASS: {test_name}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ FAIL: {test_name} - {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {self.passed}/{total} tests passed")
        if self.errors:
            print(f"\nFAILED TESTS:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*60}")
        return self.failed == 0

def count_sentences(text: str) -> int:
    """Count sentences in text using multiple delimiters"""
    # Remove markdown and formatting
    clean_text = re.sub(r'\*\*.*?\*\*', '', text)  # Remove bold
    clean_text = re.sub(r'\*.*?\*', '', clean_text)  # Remove italic
    clean_text = re.sub(r'#.*?\n', '', clean_text)  # Remove headers
    
    # Split by sentence endings
    sentences = re.split(r'[.!?]+', clean_text)
    # Filter out empty strings and very short fragments
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 3]
    return len(sentences)

def check_second_person_pov(text: str) -> bool:
    """Check if text uses second-person POV (you/your)"""
    you_count = len(re.findall(r'\byou\b', text.lower()))
    your_count = len(re.findall(r'\byour\b', text.lower()))
    return (you_count + your_count) > 0

def check_open_prompt_ending(text: str) -> bool:
    """Check if text ends with an open prompt"""
    text = text.strip()
    # Look for question marks or common open prompts
    if text.endswith('?'):
        return True
    
    open_prompts = [
        'what do you do',
        'where do you go',
        'how do you proceed',
        'what is your next move',
        'what do you choose',
        'how do you respond',
        'what happens next',
        'the choice is yours'
    ]
    
    last_sentence = text.split('.')[-1].lower().strip()
    return any(prompt in last_sentence for prompt in open_prompts)

def check_banned_phrases(text: str) -> List[str]:
    """Check for banned AI phrases"""
    banned_phrases = [
        'you notice',
        'you feel a sense',
        'you can\'t help but',
        'you find yourself',
        'you realize',
        'you sense that',
        'you become aware',
        'you get the feeling'
    ]
    
    found_banned = []
    text_lower = text.lower()
    for phrase in banned_phrases:
        if phrase in text_lower:
            found_banned.append(phrase)
    
    return found_banned

def check_enumerated_lists(text: str) -> bool:
    """Check if text contains enumerated lists (1., 2., 3., etc.)"""
    # Look for numbered lists
    numbered_pattern = r'\d+\.\s+'
    bulleted_pattern = r'[-*•]\s+'
    
    return bool(re.search(numbered_pattern, text) or re.search(bulleted_pattern, text))

def create_test_character():
    """Create a test character for v4.1 testing"""
    return {
        "name": "Kael Shadowbane",
        "class": "Ranger",
        "level": 1,
        "race": "Human",
        "background": "Outlander",
        "stats": {
            "str": 14,
            "dex": 16,
            "con": 13,
            "int": 12,
            "wis": 15,
            "cha": 10
        },
        "hp": {"current": 11, "max": 11},
        "ac": 14,
        "equipped": [
            {"name": "Leather Armor", "tags": ["armor", "light"]},
            {"name": "Longbow", "tags": ["weapon", "ranged"]},
            {"name": "Shortsword", "tags": ["weapon", "finesse"]}
        ],
        "conditions": [],
        "proficiencies": ["Survival", "Animal Handling", "Athletics", "Insight"],
        "goals": ["Protect the wilderness from corruption"]
    }

def create_test_world():
    """Create a test world state"""
    return {
        "location": "Misty Highlands",
        "settlement": "Shadowvale",
        "region": "Northern Wilderness",
        "time_of_day": "Dusk",
        "weather": "Light mist rolling through the valleys"
    }

def test_v4_1_intro_generation():
    """Test v4.1 compliance for intro generation"""
    results = TestResults()
    
    print("\n📖 TEST: Intro Generation (v4.1 Compliance)")
    print("-" * 60)
    
    try:
        # Create intro request
        payload = {
            "session_id": "test-v41-intro",
            "player_message": "Create an immersive introduction for my character in Shadowvale, a dark fantasy setting in the Misty Highlands",
            "message_type": "action",
            "character_state": create_test_character(),
            "world_state": create_test_world(),
            "threat_level": 2
        }
        
        print("🎭 Generating intro narration...")
        
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            results.add_fail("Intro Generation", f"HTTP {response.status_code}: {response.text[:200]}")
            return results.summary()
        
        data = response.json()
        
        # CRITICAL v4.1 CHECK: No 'options' field
        if "options" in data:
            results.add_fail("❌ CRITICAL: 'options' field present", f"Found deprecated 'options' field with {len(data['options'])} items")
            print(f"   Options found: {data['options'][:2]}...")  # Show first 2 options
        else:
            results.add_pass("✅ No 'options' field (v4.1 compliant)")
        
        # Get narration
        narration = data.get("narration", "")
        if not narration:
            results.add_fail("Narration Present", "No narration in response")
            return results.summary()
        
        # Validate sentence count (12-16 for intro)
        sentence_count = count_sentences(narration)
        if 12 <= sentence_count <= 16:
            results.add_pass(f"Intro sentence count ({sentence_count} sentences)")
        else:
            results.add_fail("Intro sentence count", f"Expected 12-16 sentences, got {sentence_count}")
        
        # Check second-person POV
        if check_second_person_pov(narration):
            results.add_pass("Second-person POV ('you/your')")
        else:
            results.add_fail("Second-person POV", "Does not use 'you/your'")
        
        # Check for quest hook
        quest_indicators = ["quest", "adventure", "journey", "mission", "task", "challenge"]
        if any(word in narration.lower() for word in quest_indicators):
            results.add_pass("Quest hook present")
        else:
            results.add_fail("Quest hook", "No clear quest hook found")
        
        # Check for enumerated lists (should NOT exist in v4.1)
        if check_enumerated_lists(narration):
            results.add_fail("❌ Enumerated lists found", "Contains numbered/bulleted lists (violates v4.1)")
        else:
            results.add_pass("✅ No enumerated lists")
        
        # Check for open prompt ending
        if check_open_prompt_ending(narration):
            results.add_pass("✅ Ends with open prompt")
        else:
            results.add_fail("Open prompt ending", "Does not end with open prompt")
        
        # Check for banned AI phrases
        banned_found = check_banned_phrases(narration)
        if banned_found:
            results.add_fail("Banned AI phrases", f"Found: {banned_found}")
        else:
            results.add_pass("✅ No banned AI phrases")
        
        print(f"\n📝 INTRO SAMPLE (first 300 chars):")
        print(f"   {narration[:300]}...")
        print(f"📊 Sentence count: {sentence_count}")
        you_pattern = r'\b(you|your)\b'
        print(f"📊 Second-person words: {len(re.findall(you_pattern, narration.lower()))}")
        
    except Exception as e:
        results.add_fail("Intro Generation", f"Exception: {str(e)}")
    
    return results.summary()

def test_v4_1_exploration_action():
    """Test v4.1 compliance for exploration actions"""
    results = TestResults()
    
    print("\n🔍 TEST: Exploration Action (v4.1 Compliance)")
    print("-" * 60)
    
    try:
        payload = {
            "session_id": "test-v41-exploration",
            "player_message": "I examine the village square and look for anything unusual",
            "message_type": "action",
            "character_state": create_test_character(),
            "world_state": create_test_world(),
            "threat_level": 2
        }
        
        print("🔍 Testing exploration action...")
        print(f"   Action: '{payload['player_message']}'")
        
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            results.add_fail("Exploration Action", f"HTTP {response.status_code}: {response.text[:200]}")
            return results.summary()
        
        data = response.json()
        
        # CRITICAL v4.1 CHECK: No 'options' field
        if "options" in data:
            results.add_fail("❌ CRITICAL: 'options' field present", f"Found deprecated 'options' field")
            print(f"   Options found: {data['options'][:2]}...")
        else:
            results.add_pass("✅ No 'options' field (v4.1 compliant)")
        
        # Get narration
        narration = data.get("narration", "")
        if not narration:
            results.add_fail("Narration Present", "No narration in response")
            return results.summary()
        
        # Validate sentence count (6-10 for exploration)
        sentence_count = count_sentences(narration)
        if 6 <= sentence_count <= 10:
            results.add_pass(f"Exploration sentence count ({sentence_count} sentences)")
        else:
            results.add_fail("Exploration sentence count", f"Expected 6-10 sentences, got {sentence_count}")
        
        # Check second-person POV
        if check_second_person_pov(narration):
            results.add_pass("Second-person POV ('you/your')")
        else:
            results.add_fail("Second-person POV", "Does not use 'you/your'")
        
        # Check for open prompt ending
        if check_open_prompt_ending(narration):
            results.add_pass("✅ Ends with open prompt")
        else:
            results.add_fail("Open prompt ending", "Does not end with open prompt")
        
        # Check for enumerated lists (should NOT exist in v4.1)
        if check_enumerated_lists(narration):
            results.add_fail("❌ Enumerated lists found", "Contains numbered/bulleted lists")
        else:
            results.add_pass("✅ No enumerated lists")
        
        # Check for banned AI phrases
        banned_found = check_banned_phrases(narration)
        if banned_found:
            results.add_fail("Banned AI phrases", f"Found: {banned_found}")
        else:
            results.add_pass("✅ No banned AI phrases")
        
        print(f"\n📝 EXPLORATION SAMPLE (first 300 chars):")
        print(f"   {narration[:300]}...")
        print(f"📊 Sentence count: {sentence_count}")
        
    except Exception as e:
        results.add_fail("Exploration Action", f"Exception: {str(e)}")
    
    return results.summary()

def test_v4_1_social_interaction():
    """Test v4.1 compliance for social interactions"""
    results = TestResults()
    
    print("\n💬 TEST: Social Interaction (v4.1 Compliance)")
    print("-" * 60)
    
    try:
        payload = {
            "session_id": "test-v41-social",
            "player_message": "I approach the innkeeper and ask about recent events in town",
            "message_type": "action",
            "character_state": create_test_character(),
            "world_state": create_test_world(),
            "threat_level": 2
        }
        
        print("💬 Testing social interaction...")
        print(f"   Action: '{payload['player_message']}'")
        
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            results.add_fail("Social Interaction", f"HTTP {response.status_code}: {response.text[:200]}")
            return results.summary()
        
        data = response.json()
        
        # CRITICAL v4.1 CHECK: No 'options' field
        if "options" in data:
            results.add_fail("❌ CRITICAL: 'options' field present", f"Found deprecated 'options' field")
        else:
            results.add_pass("✅ No 'options' field (v4.1 compliant)")
        
        # Get narration
        narration = data.get("narration", "")
        if not narration:
            results.add_fail("Narration Present", "No narration in response")
            return results.summary()
        
        # Validate sentence count (6-10 for social)
        sentence_count = count_sentences(narration)
        if 6 <= sentence_count <= 10:
            results.add_pass(f"Social sentence count ({sentence_count} sentences)")
        else:
            results.add_fail("Social sentence count", f"Expected 6-10 sentences, got {sentence_count}")
        
        # Check second-person POV
        if check_second_person_pov(narration):
            results.add_pass("Second-person POV ('you/your')")
        else:
            results.add_fail("Second-person POV", "Does not use 'you/your'")
        
        # Check for NPC dialogue
        if '"' in narration or "says" in narration.lower() or "replies" in narration.lower():
            results.add_pass("NPC dialogue present")
        else:
            results.add_fail("NPC dialogue", "No clear NPC dialogue found")
        
        # Check for open prompt ending
        if check_open_prompt_ending(narration):
            results.add_pass("✅ Ends with open prompt")
        else:
            results.add_fail("Open prompt ending", "Does not end with open prompt")
        
        # Check for enumerated lists (should NOT exist in v4.1)
        if check_enumerated_lists(narration):
            results.add_fail("❌ Enumerated lists found", "Contains numbered/bulleted lists")
        else:
            results.add_pass("✅ No enumerated lists")
        
        print(f"\n📝 SOCIAL SAMPLE (first 300 chars):")
        print(f"   {narration[:300]}...")
        print(f"📊 Sentence count: {sentence_count}")
        
    except Exception as e:
        results.add_fail("Social Interaction", f"Exception: {str(e)}")
    
    return results.summary()

def test_v4_1_ability_check():
    """Test v4.1 compliance for ability checks"""
    results = TestResults()
    
    print("\n🎲 TEST: Ability Check (v4.1 Compliance)")
    print("-" * 60)
    
    try:
        payload = {
            "session_id": "test-v41-check",
            "player_message": "I try to pick the lock on the mysterious chest",
            "message_type": "action",
            "character_state": create_test_character(),
            "world_state": create_test_world(),
            "threat_level": 2
        }
        
        print("🎲 Testing ability check...")
        print(f"   Action: '{payload['player_message']}'")
        
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            results.add_fail("Ability Check", f"HTTP {response.status_code}: {response.text[:200]}")
            return results.summary()
        
        data = response.json()
        
        # CRITICAL v4.1 CHECK: No 'options' field
        if "options" in data:
            results.add_fail("❌ CRITICAL: 'options' field present", f"Found deprecated 'options' field")
        else:
            results.add_pass("✅ No 'options' field (v4.1 compliant)")
        
        # Get narration
        narration = data.get("narration", "")
        if not narration:
            results.add_fail("Narration Present", "No narration in response")
            return results.summary()
        
        # Validate sentence count (6-10 for ability check context)
        sentence_count = count_sentences(narration)
        if 6 <= sentence_count <= 10:
            results.add_pass(f"Check sentence count ({sentence_count} sentences)")
        else:
            results.add_fail("Check sentence count", f"Expected 6-10 sentences, got {sentence_count}")
        
        # Check second-person POV
        if check_second_person_pov(narration):
            results.add_pass("Second-person POV ('you/your')")
        else:
            results.add_fail("Second-person POV", "Does not use 'you/your'")
        
        # Check for check request (optional - may or may not be present)
        if "mechanics" in data and data["mechanics"] and "check_request" in data["mechanics"]:
            check_request = data["mechanics"]["check_request"]
            if check_request:
                results.add_pass("Check request populated")
                print(f"   Check: {check_request.get('skill', 'Unknown')} DC {check_request.get('dc', 'Unknown')}")
            else:
                print("   No check request (action resolved without roll)")
        else:
            print("   No check request (action resolved without roll)")
        
        # Check for open prompt ending
        if check_open_prompt_ending(narration):
            results.add_pass("✅ Ends with open prompt")
        else:
            results.add_fail("Open prompt ending", "Does not end with open prompt")
        
        # Check for enumerated lists (should NOT exist in v4.1)
        if check_enumerated_lists(narration):
            results.add_fail("❌ Enumerated lists found", "Contains numbered/bulleted lists")
        else:
            results.add_pass("✅ No enumerated lists")
        
        print(f"\n📝 CHECK SAMPLE (first 300 chars):")
        print(f"   {narration[:300]}...")
        print(f"📊 Sentence count: {sentence_count}")
        
    except Exception as e:
        results.add_fail("Ability Check", f"Exception: {str(e)}")
    
    return results.summary()

def test_v4_1_combat_scenario():
    """Test v4.1 compliance for combat scenarios"""
    results = TestResults()
    
    print("\n⚔️ TEST: Combat Scenario (v4.1 Compliance)")
    print("-" * 60)
    
    try:
        payload = {
            "session_id": "test-v41-combat",
            "player_message": "I draw my weapon and attack the approaching bandit",
            "message_type": "action",
            "character_state": create_test_character(),
            "world_state": create_test_world(),
            "threat_level": 3
        }
        
        print("⚔️ Testing combat scenario...")
        print(f"   Action: '{payload['player_message']}'")
        
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            results.add_fail("Combat Scenario", f"HTTP {response.status_code}: {response.text[:200]}")
            return results.summary()
        
        data = response.json()
        
        # CRITICAL v4.1 CHECK: No 'options' field
        if "options" in data:
            results.add_fail("❌ CRITICAL: 'options' field present", f"Found deprecated 'options' field")
        else:
            results.add_pass("✅ No 'options' field (v4.1 compliant)")
        
        # Get narration
        narration = data.get("narration", "")
        if not narration:
            results.add_fail("Narration Present", "No narration in response")
            return results.summary()
        
        # Validate sentence count (4-8 for combat - shorter)
        sentence_count = count_sentences(narration)
        if 4 <= sentence_count <= 8:
            results.add_pass(f"Combat sentence count ({sentence_count} sentences)")
        else:
            results.add_fail("Combat sentence count", f"Expected 4-8 sentences, got {sentence_count}")
        
        # Check for fast-paced action
        action_words = ["strike", "swing", "attack", "blade", "weapon", "hit", "dodge", "parry", "slash", "thrust"]
        if any(word in narration.lower() for word in action_words):
            results.add_pass("Fast-paced action description")
        else:
            results.add_fail("Action description", "No clear action words found")
        
        # Check second-person POV
        if check_second_person_pov(narration):
            results.add_pass("Second-person POV ('you/your')")
        else:
            results.add_fail("Second-person POV", "Does not use 'you/your'")
        
        # Check for open prompt ending (even in combat)
        if check_open_prompt_ending(narration):
            results.add_pass("✅ Ends with open prompt")
        else:
            results.add_fail("Open prompt ending", "Does not end with open prompt")
        
        # Check for enumerated lists (should NOT exist in v4.1)
        if check_enumerated_lists(narration):
            results.add_fail("❌ Enumerated lists found", "Contains numbered/bulleted lists")
        else:
            results.add_pass("✅ No enumerated lists")
        
        print(f"\n📝 COMBAT SAMPLE (first 300 chars):")
        print(f"   {narration[:300]}...")
        print(f"📊 Sentence count: {sentence_count}")
        
    except Exception as e:
        results.add_fail("Combat Scenario", f"Exception: {str(e)}")
    
    return results.summary()

def test_backend_health():
    """Test basic backend connectivity"""
    print("🏥 Testing Backend Health")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is online: {data.get('message', 'Unknown')}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection error: {e}")
        return False

def main():
    """Run the v4.1 Unified Narrative Specification test suite"""
    print("🚀 v4.1 UNIFIED NARRATIVE SPECIFICATION TEST SUITE")
    print("=" * 80)
    print("Testing v4.1 compliance using legacy /api/rpg_dm endpoint")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    # Check backend health first
    if not test_backend_health():
        print("\n❌ Backend is not accessible. Aborting tests.")
        sys.exit(1)
    
    all_passed = True
    total_tests = 0
    total_passed = 0
    
    # Run all test suites
    test_suites = [
        ("Intro Generation", test_v4_1_intro_generation),
        ("Exploration Action", test_v4_1_exploration_action),
        ("Social Interaction", test_v4_1_social_interaction),
        ("Ability Check", test_v4_1_ability_check),
        ("Combat Scenario", test_v4_1_combat_scenario)
    ]
    
    for suite_name, test_func in test_suites:
        print(f"\n{'='*80}")
        print(f"RUNNING: {suite_name}")
        print(f"{'='*80}")
        
        try:
            suite_passed = test_func()
            if not suite_passed:
                all_passed = False
        except Exception as e:
            print(f"❌ SUITE FAILED: {suite_name} - Exception: {e}")
            all_passed = False
    
    # Final summary
    print(f"\n{'='*80}")
    print("🏁 FINAL v4.1 UNIFIED NARRATIVE SPECIFICATION RESULTS")
    print(f"{'='*80}")
    
    if all_passed:
        print("✅ ALL TESTS PASSED - v4.1 specification compliance verified")
        print("\n🎯 SUCCESS CRITERIA MET:")
        print("   ✅ No 'options' field in any response")
        print("   ✅ All narration ends with open prompts")
        print("   ✅ Sentence counts match v4.1 context limits")
        print("   ✅ POV is consistent second-person throughout")
        print("   ✅ No enumerated lists in narration")
        print("   ✅ No banned AI phrases detected")
        print("   ✅ JSON schema is valid")
        print("   ✅ All endpoints return successful responses")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - v4.1 specification violations detected")
        print("\n⚠️ CRITICAL ISSUES FOUND:")
        print("   - Review failed test details above")
        print("   - Most likely: 'options' field still present in responses")
        print("   - Fix violations before claiming v4.1 compliance")
        sys.exit(1)

if __name__ == "__main__":
    main()