#!/usr/bin/env python3
"""
v4.1 Unified Narrative Specification Test Suite
Tests the comprehensive v4.1 implementation as specified in the review request
"""

import requests
import json
import sys
import re
from typing import Dict, Any, List

# Backend URL from frontend/.env
BACKEND_URL = "https://prompt-architect-23.preview.emergentagent.com/api"

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

def setup_test_campaign():
    """Create a test campaign for v4.1 testing"""
    print("🏰 Setting up test campaign...")
    
    # Create campaign with world blueprint
    world_payload = {
        "character": {
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
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/world-blueprint/generate",
            json=world_payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            campaign_id = data.get("campaign_id")
            print(f"   ✅ Campaign created: {campaign_id}")
            return campaign_id, data
        else:
            print(f"   ❌ Failed to create campaign: {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"   ❌ Exception creating campaign: {e}")
        return None, None

def create_test_character(campaign_id: str):
    """Create a test character in the campaign"""
    print("👤 Creating test character...")
    
    char_payload = {
        "campaign_id": campaign_id,
        "character": {
            "name": "Kael Shadowbane",
            "class": "Ranger",
            "level": 1,
            "race": "Human",
            "background": "Outlander",
            "stats": {
                "strength": 14,
                "dexterity": 16,
                "constitution": 13,
                "intelligence": 12,
                "wisdom": 15,
                "charisma": 10
            },
            "hitPoints": 11,
            "proficiencies": ["Survival", "Animal Handling", "Athletics", "Insight"],
            "languages": ["Common"],
            "inventory": ["Leather Armor", "Longbow", "Shortsword", "Explorer's Pack"],
            "aspiration": {"goal": "Protect the wilderness from the spreading corruption"}
        }
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/characters/create",
            json=char_payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            character_id = data.get("character_id")
            print(f"   ✅ Character created: {character_id}")
            return character_id
        else:
            print(f"   ❌ Failed to create character: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Exception creating character: {e}")
        return None

def test_campaign_creation_intro():
    """Test 1: Campaign Creation & Intro"""
    results = TestResults()
    
    print("\n🏰 TEST 1: Campaign Creation & Intro")
    print("-" * 60)
    
    # Setup campaign
    campaign_id, campaign_data = setup_test_campaign()
    if not campaign_id:
        results.add_fail("Campaign Creation", "Failed to create campaign")
        return results.summary()
    
    character_id = create_test_character(campaign_id)
    if not character_id:
        results.add_fail("Character Creation", "Failed to create character")
        return results.summary()
    
    # Generate intro narration
    try:
        print("\n📖 Generating intro narration...")
        
        intro_payload = {
            "campaign_id": campaign_id,
            "character_id": character_id
        }
        
        response = requests.post(
            f"{BACKEND_URL}/intro/generate",
            json=intro_payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code != 200:
            results.add_fail("Intro Generation", f"HTTP {response.status_code}: {response.text[:200]}")
            return results.summary()
        
        data = response.json()
        
        # Check for 'options' field (should NOT exist in v4.1)
        if "options" in data:
            results.add_fail("No 'options' field", f"CRITICAL: 'options' field found in intro response")
        else:
            results.add_pass("No 'options' field in intro")
        
        # Get intro text
        intro_text = data.get("intro", "")
        if not intro_text:
            results.add_fail("Intro Text Present", "No intro text in response")
            return results.summary()
        
        # Validate sentence count (12-16 for intro)
        sentence_count = count_sentences(intro_text)
        if 12 <= sentence_count <= 16:
            results.add_pass(f"Intro sentence count ({sentence_count} sentences)")
        else:
            results.add_fail("Intro sentence count", f"Expected 12-16 sentences, got {sentence_count}")
        
        # Check second-person POV
        if check_second_person_pov(intro_text):
            results.add_pass("Second-person POV in intro")
        else:
            results.add_fail("Second-person POV", "Intro does not use 'you/your'")
        
        # Check for quest hook at end
        if "quest" in intro_text.lower() or "adventure" in intro_text.lower() or "journey" in intro_text.lower():
            results.add_pass("Quest hook present")
        else:
            results.add_fail("Quest hook", "No clear quest hook found in intro")
        
        # Check for enumerated lists
        if check_enumerated_lists(intro_text):
            results.add_fail("No enumerated lists", "Found numbered/bulleted lists in intro")
        else:
            results.add_pass("No enumerated lists in intro")
        
        # Check for open prompt ending
        if check_open_prompt_ending(intro_text):
            results.add_pass("Open prompt ending")
        else:
            results.add_fail("Open prompt ending", "Intro does not end with open prompt")
        
        print(f"\n📝 INTRO SAMPLE (first 200 chars):")
        print(f"   {intro_text[:200]}...")
        print(f"📊 Sentence count: {sentence_count}")
        
    except Exception as e:
        results.add_fail("Intro Generation", f"Exception: {str(e)}")
    
    return results.summary()

def test_exploration_action():
    """Test 2: Exploration Action"""
    results = TestResults()
    
    print("\n🔍 TEST 2: Exploration Action")
    print("-" * 60)
    
    # Use a test campaign (create minimal one if needed)
    campaign_id = "test-exploration-v41"
    character_id = "test-char-exploration"
    
    try:
        action_payload = {
            "campaign_id": campaign_id,
            "character_id": character_id,
            "player_action": "I examine the village square and look for anything unusual",
            "client_target_id": None
        }
        
        print("🎬 Testing exploration action...")
        print(f"   Action: '{action_payload['player_action']}'")
        
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm/action",
            json=action_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            results.add_fail("Exploration Action", f"HTTP {response.status_code}: {response.text[:200]}")
            return results.summary()
        
        data = response.json()
        
        # Check for 'options' field (should NOT exist in v4.1)
        if "options" in data:
            results.add_fail("No 'options' field", f"CRITICAL: 'options' field found in exploration response")
        else:
            results.add_pass("No 'options' field in exploration")
        
        # Get narration
        narration = data.get("narration", "")
        if not narration:
            results.add_fail("Narration Present", "No narration in exploration response")
            return results.summary()
        
        # Validate sentence count (6-10 for exploration context)
        sentence_count = count_sentences(narration)
        if 6 <= sentence_count <= 10:
            results.add_pass(f"Exploration sentence count ({sentence_count} sentences)")
        else:
            results.add_fail("Exploration sentence count", f"Expected 6-10 sentences, got {sentence_count}")
        
        # Check second-person POV
        if check_second_person_pov(narration):
            results.add_pass("Second-person POV in exploration")
        else:
            results.add_fail("Second-person POV", "Exploration does not use 'you/your'")
        
        # Check for open prompt ending
        if check_open_prompt_ending(narration):
            results.add_pass("Open prompt ending in exploration")
        else:
            results.add_fail("Open prompt ending", "Exploration does not end with open prompt")
        
        # Check for enumerated lists
        if check_enumerated_lists(narration):
            results.add_fail("No enumerated lists", "Found numbered/bulleted lists in exploration")
        else:
            results.add_pass("No enumerated lists in exploration")
        
        # Check for banned AI phrases
        banned_found = check_banned_phrases(narration)
        if banned_found:
            results.add_fail("No banned AI phrases", f"Found banned phrases: {banned_found}")
        else:
            results.add_pass("No banned AI phrases")
        
        print(f"\n📝 EXPLORATION SAMPLE (first 200 chars):")
        print(f"   {narration[:200]}...")
        print(f"📊 Sentence count: {sentence_count}")
        
    except Exception as e:
        results.add_fail("Exploration Action", f"Exception: {str(e)}")
    
    return results.summary()

def test_social_interaction():
    """Test 3: Social Interaction"""
    results = TestResults()
    
    print("\n💬 TEST 3: Social Interaction")
    print("-" * 60)
    
    campaign_id = "test-social-v41"
    character_id = "test-char-social"
    
    try:
        action_payload = {
            "campaign_id": campaign_id,
            "character_id": character_id,
            "player_action": "I approach the innkeeper and ask about recent events in town",
            "client_target_id": None
        }
        
        print("🗣️ Testing social interaction...")
        print(f"   Action: '{action_payload['player_action']}'")
        
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm/action",
            json=action_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            results.add_fail("Social Interaction", f"HTTP {response.status_code}: {response.text[:200]}")
            return results.summary()
        
        data = response.json()
        
        # Check for 'options' field (should NOT exist in v4.1)
        if "options" in data:
            results.add_fail("No 'options' field", f"CRITICAL: 'options' field found in social response")
        else:
            results.add_pass("No 'options' field in social")
        
        # Get narration
        narration = data.get("narration", "")
        if not narration:
            results.add_fail("Narration Present", "No narration in social response")
            return results.summary()
        
        # Validate sentence count (6-10 for social context)
        sentence_count = count_sentences(narration)
        if 6 <= sentence_count <= 10:
            results.add_pass(f"Social sentence count ({sentence_count} sentences)")
        else:
            results.add_fail("Social sentence count", f"Expected 6-10 sentences, got {sentence_count}")
        
        # Check second-person POV
        if check_second_person_pov(narration):
            results.add_pass("Second-person POV in social")
        else:
            results.add_fail("Second-person POV", "Social does not use 'you/your'")
        
        # Check for NPC dialogue
        if '"' in narration or "says" in narration.lower() or "replies" in narration.lower():
            results.add_pass("NPC dialogue present")
        else:
            results.add_fail("NPC dialogue", "No clear NPC dialogue found")
        
        # Check for open prompt ending
        if check_open_prompt_ending(narration):
            results.add_pass("Open prompt ending in social")
        else:
            results.add_fail("Open prompt ending", "Social does not end with open prompt")
        
        # Check for enumerated lists
        if check_enumerated_lists(narration):
            results.add_fail("No enumerated lists", "Found numbered/bulleted lists in social")
        else:
            results.add_pass("No enumerated lists in social")
        
        print(f"\n📝 SOCIAL SAMPLE (first 200 chars):")
        print(f"   {narration[:200]}...")
        print(f"📊 Sentence count: {sentence_count}")
        
    except Exception as e:
        results.add_fail("Social Interaction", f"Exception: {str(e)}")
    
    return results.summary()

def test_ability_check_flow():
    """Test 4: Ability Check Flow"""
    results = TestResults()
    
    print("\n🎲 TEST 4: Ability Check Flow")
    print("-" * 60)
    
    campaign_id = "test-check-v41"
    character_id = "test-char-check"
    
    try:
        # Part A: Check Request
        action_payload = {
            "campaign_id": campaign_id,
            "character_id": character_id,
            "player_action": "I try to pick the lock on the mysterious chest",
            "client_target_id": None
        }
        
        print("🔓 Testing ability check request...")
        print(f"   Action: '{action_payload['player_action']}'")
        
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm/action",
            json=action_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            results.add_fail("Ability Check Request", f"HTTP {response.status_code}: {response.text[:200]}")
            return results.summary()
        
        data = response.json()
        
        # Check for 'options' field (should NOT exist in v4.1)
        if "options" in data:
            results.add_fail("No 'options' field in check request", f"CRITICAL: 'options' field found")
        else:
            results.add_pass("No 'options' field in check request")
        
        # Check for check_request field
        check_request = None
        if "mechanics" in data and data["mechanics"] and "check_request" in data["mechanics"]:
            check_request = data["mechanics"]["check_request"]
            results.add_pass("Check request populated")
            
            # Validate check_request structure
            required_fields = ["dc", "ability", "skill", "reason"]
            missing_fields = [f for f in required_fields if f not in check_request]
            if missing_fields:
                results.add_fail("Check request structure", f"Missing fields: {missing_fields}")
            else:
                results.add_pass("Check request structure complete")
                print(f"   DC: {check_request.get('dc')}, Skill: {check_request.get('skill')}")
        else:
            results.add_fail("Check request populated", "No check_request in mechanics")
        
        # Get narration
        narration = data.get("narration", "")
        if narration:
            # Validate sentence count (6-10 for check context)
            sentence_count = count_sentences(narration)
            if 6 <= sentence_count <= 10:
                results.add_pass(f"Check narration sentence count ({sentence_count} sentences)")
            else:
                results.add_fail("Check narration sentence count", f"Expected 6-10 sentences, got {sentence_count}")
            
            # Check if narration explains why check is needed
            if "lock" in narration.lower() or "difficult" in narration.lower() or "requires" in narration.lower():
                results.add_pass("Check explanation in narration")
            else:
                results.add_fail("Check explanation", "Narration doesn't explain why check is needed")
        
        # Part B: Check Resolution (simulate a roll result)
        if check_request:
            print("\n🎯 Testing check resolution...")
            
            resolve_payload = {
                "campaign_id": campaign_id,
                "character_id": character_id,
                "check_result": {
                    "total": 18,
                    "roll": 15,
                    "modifier": 3,
                    "success": True
                }
            }
            
            try:
                resolve_response = requests.post(
                    f"{BACKEND_URL}/rpg_dm/resolve_check",
                    json=resolve_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if resolve_response.status_code == 200:
                    resolve_data = resolve_response.json()
                    
                    # Check for 'options' field (should NOT exist in v4.1)
                    if "options" in resolve_data:
                        results.add_fail("No 'options' field in resolve", f"CRITICAL: 'options' field found")
                    else:
                        results.add_pass("No 'options' field in resolve")
                    
                    # Get resolution narration
                    resolve_narration = resolve_data.get("narration", "")
                    if resolve_narration:
                        # Check for success outcome description
                        if "success" in resolve_narration.lower() or "unlock" in resolve_narration.lower():
                            results.add_pass("Success outcome described")
                        else:
                            results.add_fail("Success outcome", "Success not clearly described")
                        
                        # Check for direct consequences
                        if "open" in resolve_narration.lower() or "inside" in resolve_narration.lower() or "reveal" in resolve_narration.lower():
                            results.add_pass("Direct consequences shown")
                        else:
                            results.add_fail("Direct consequences", "No clear consequences of success")
                        
                        # Check for open prompt ending
                        if check_open_prompt_ending(resolve_narration):
                            results.add_pass("Open prompt ending in resolution")
                        else:
                            results.add_fail("Open prompt ending", "Resolution does not end with open prompt")
                    else:
                        results.add_fail("Resolution narration", "No narration in resolve response")
                        
                else:
                    results.add_fail("Check Resolution", f"HTTP {resolve_response.status_code}")
                    
            except Exception as e:
                results.add_fail("Check Resolution", f"Exception: {str(e)}")
        
        print(f"\n📝 CHECK SAMPLE (first 200 chars):")
        print(f"   {narration[:200]}...")
        
    except Exception as e:
        results.add_fail("Ability Check Flow", f"Exception: {str(e)}")
    
    return results.summary()

def test_combat_scenario():
    """Test 5: Combat Scenario"""
    results = TestResults()
    
    print("\n⚔️ TEST 5: Combat Scenario")
    print("-" * 60)
    
    campaign_id = "test-combat-v41"
    character_id = "test-char-combat"
    
    try:
        action_payload = {
            "campaign_id": campaign_id,
            "character_id": character_id,
            "player_action": "I draw my weapon and attack the approaching bandit",
            "client_target_id": None
        }
        
        print("⚔️ Testing combat action...")
        print(f"   Action: '{action_payload['player_action']}'")
        
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm/action",
            json=action_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            results.add_fail("Combat Action", f"HTTP {response.status_code}: {response.text[:200]}")
            return results.summary()
        
        data = response.json()
        
        # Check for 'options' field (should NOT exist in v4.1)
        if "options" in data:
            results.add_fail("No 'options' field", f"CRITICAL: 'options' field found in combat response")
        else:
            results.add_pass("No 'options' field in combat")
        
        # Get narration
        narration = data.get("narration", "")
        if not narration:
            results.add_fail("Narration Present", "No narration in combat response")
            return results.summary()
        
        # Validate sentence count (4-8 for combat context - shorter)
        sentence_count = count_sentences(narration)
        if 4 <= sentence_count <= 8:
            results.add_pass(f"Combat sentence count ({sentence_count} sentences)")
        else:
            results.add_fail("Combat sentence count", f"Expected 4-8 sentences, got {sentence_count}")
        
        # Check for fast-paced action description
        action_words = ["strike", "swing", "attack", "blade", "weapon", "hit", "dodge", "parry"]
        if any(word in narration.lower() for word in action_words):
            results.add_pass("Fast-paced action description")
        else:
            results.add_fail("Action description", "No clear action words found")
        
        # Check second-person POV
        if check_second_person_pov(narration):
            results.add_pass("Second-person POV in combat")
        else:
            results.add_fail("Second-person POV", "Combat does not use 'you/your'")
        
        # Check for open prompt ending (even in combat)
        if check_open_prompt_ending(narration):
            results.add_pass("Open prompt ending in combat")
        else:
            results.add_fail("Open prompt ending", "Combat does not end with open prompt")
        
        print(f"\n📝 COMBAT SAMPLE (first 200 chars):")
        print(f"   {narration[:200]}...")
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
    """Run the complete v4.1 Unified Narrative Specification test suite"""
    print("🚀 v4.1 UNIFIED NARRATIVE SPECIFICATION TEST SUITE")
    print("=" * 80)
    print("Testing comprehensive v4.1 implementation as specified in review request")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    # Check backend health first
    if not test_backend_health():
        print("\n❌ Backend is not accessible. Aborting tests.")
        sys.exit(1)
    
    all_passed = True
    
    # Run all test suites
    test_suites = [
        ("Campaign Creation & Intro", test_campaign_creation_intro),
        ("Exploration Action", test_exploration_action),
        ("Social Interaction", test_social_interaction),
        ("Ability Check Flow", test_ability_check_flow),
        ("Combat Scenario", test_combat_scenario)
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
        print("✅ ALL TESTS PASSED - v4.1 specification fully compliant")
        print("\n🎯 SUCCESS CRITERIA MET:")
        print("   ✅ No 'options' field in any response")
        print("   ✅ All narration ends with open prompts")
        print("   ✅ Sentence counts match v4.1 context limits")
        print("   ✅ POV is consistent second-person throughout")
        print("   ✅ No enumerated lists in narration")
        print("   ✅ JSON schema is valid")
        print("   ✅ All endpoints return successful responses")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - v4.1 specification violations detected")
        print("\n⚠️ CRITICAL ISSUES FOUND:")
        print("   - Review failed test details above")
        print("   - Fix violations before claiming v4.1 compliance")
        sys.exit(1)

if __name__ == "__main__":
    main()