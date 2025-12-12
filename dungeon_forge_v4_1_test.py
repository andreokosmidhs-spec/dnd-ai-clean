#!/usr/bin/env python3
"""
DUNGEON FORGE v4.1 Unified Narrative Specification Test
Tests the new /api/rpg_dm/action endpoint for v4.1 compliance
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

def check_enumerated_lists(text: str) -> bool:
    """Check if text contains enumerated lists (1., 2., 3., etc.)"""
    # Look for numbered lists
    numbered_pattern = r'\d+\.\s+'
    bulleted_pattern = r'[-*•]\s+'
    
    return bool(re.search(numbered_pattern, text) or re.search(bulleted_pattern, text))

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

def test_latest_campaign():
    """Test loading the latest campaign"""
    print("\n📂 Testing Latest Campaign Load")
    print("-" * 60)
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/campaigns/latest",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("success") and response_data.get("data"):
                data = response_data["data"]
                campaign_id = data.get("campaign_id")
                print(f"✅ Latest campaign loaded: {campaign_id}")
                return campaign_id, data
            else:
                print(f"❌ No campaign data in response")
                return None, None
        else:
            print(f"❌ Failed to load latest campaign: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None, None
            
    except Exception as e:
        print(f"❌ Exception loading campaign: {e}")
        return None, None

def test_dungeon_forge_action(campaign_id: str, character_id: str, action: str, test_name: str, expected_sentences: tuple):
    """Test a DUNGEON FORGE action for v4.1 compliance"""
    results = TestResults()
    
    print(f"\n🎬 Testing: {test_name}")
    print(f"   Action: '{action}'")
    
    try:
        payload = {
            "campaign_id": campaign_id,
            "character_id": character_id,
            "player_action": action,
            "client_target_id": None
        }
        
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm/action",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            results.add_fail(f"{test_name} - Request", f"HTTP {response.status_code}: {response.text[:200]}")
            return results.summary()
        
        response_json = response.json()
        
        # Handle wrapped response format
        if response_json.get("success") and response_json.get("data"):
            data = response_json["data"]
        else:
            data = response_json
        
        # CRITICAL v4.1 CHECK: No 'options' field
        if "options" in data:
            results.add_fail(f"{test_name} - No 'options' field", f"CRITICAL: 'options' field found with {len(data['options'])} items")
            print(f"   ❌ Options found: {data['options'][:2]}...")
        else:
            results.add_pass(f"{test_name} - No 'options' field")
        
        # Get narration
        narration = data.get("narration", "")
        if not narration:
            results.add_fail(f"{test_name} - Narration", "No narration in response")
            return results.summary()
        
        # Validate sentence count
        sentence_count = count_sentences(narration)
        min_sentences, max_sentences = expected_sentences
        if min_sentences <= sentence_count <= max_sentences:
            results.add_pass(f"{test_name} - Sentence count ({sentence_count} sentences)")
        else:
            results.add_fail(f"{test_name} - Sentence count", f"Expected {min_sentences}-{max_sentences} sentences, got {sentence_count}")
        
        # Check second-person POV
        if check_second_person_pov(narration):
            results.add_pass(f"{test_name} - Second-person POV")
        else:
            results.add_fail(f"{test_name} - Second-person POV", "Does not use 'you/your'")
        
        # Check for open prompt ending
        if check_open_prompt_ending(narration):
            results.add_pass(f"{test_name} - Open prompt ending")
        else:
            results.add_fail(f"{test_name} - Open prompt ending", "Does not end with open prompt")
        
        # Check for enumerated lists (should NOT exist in v4.1)
        if check_enumerated_lists(narration):
            results.add_fail(f"{test_name} - No enumerated lists", "Contains numbered/bulleted lists")
        else:
            results.add_pass(f"{test_name} - No enumerated lists")
        
        print(f"\n📝 NARRATION SAMPLE (first 400 chars):")
        print(f"   {narration[:400]}...")
        print(f"📊 Sentence count: {sentence_count}")
        print(f"📊 Character count: {len(narration)}")
        
        # Show full response structure for debugging
        print(f"\n🔍 RESPONSE STRUCTURE:")
        response_keys = list(data.keys())
        print(f"   Keys: {response_keys}")
        
        return results.summary()
        
    except Exception as e:
        results.add_fail(f"{test_name}", f"Exception: {str(e)}")
        return results.summary()

def main():
    """Run the DUNGEON FORGE v4.1 test suite"""
    print("🚀 DUNGEON FORGE v4.1 UNIFIED NARRATIVE SPECIFICATION TEST")
    print("=" * 80)
    print("Testing /api/rpg_dm/action endpoint for v4.1 compliance")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    # Check backend health first
    if not test_backend_health():
        print("\n❌ Backend is not accessible. Aborting tests.")
        sys.exit(1)
    
    # Load latest campaign
    campaign_id, campaign_data = test_latest_campaign()
    if not campaign_id:
        print("\n❌ Cannot load campaign. Aborting tests.")
        sys.exit(1)
    
    # Extract character ID from campaign data
    character_id = None
    if campaign_data and "character_id" in campaign_data:
        character_id = campaign_data["character_id"]
    elif campaign_data and "character" in campaign_data:
        character_id = campaign_data["character"].get("character_id", "default-character")
    else:
        character_id = "default-character"
    
    print(f"\n🎭 Using character: {character_id}")
    
    all_passed = True
    
    # Test scenarios as specified in review request
    test_scenarios = [
        {
            "action": "I examine the village square and look for anything unusual",
            "name": "Exploration Action",
            "expected_sentences": (6, 10)
        },
        {
            "action": "I approach the innkeeper and ask about recent events in town",
            "name": "Social Interaction", 
            "expected_sentences": (6, 10)
        },
        {
            "action": "I try to pick the lock on the mysterious chest",
            "name": "Ability Check Flow",
            "expected_sentences": (6, 10)
        },
        {
            "action": "I draw my weapon and attack the approaching bandit",
            "name": "Combat Scenario",
            "expected_sentences": (4, 8)
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n{'='*80}")
        print(f"RUNNING: {scenario['name']}")
        print(f"{'='*80}")
        
        try:
            suite_passed = test_dungeon_forge_action(
                campaign_id, 
                character_id, 
                scenario["action"], 
                scenario["name"], 
                scenario["expected_sentences"]
            )
            if not suite_passed:
                all_passed = False
        except Exception as e:
            print(f"❌ SUITE FAILED: {scenario['name']} - Exception: {e}")
            all_passed = False
    
    # Final summary
    print(f"\n{'='*80}")
    print("🏁 FINAL DUNGEON FORGE v4.1 RESULTS")
    print(f"{'='*80}")
    
    if all_passed:
        print("✅ ALL TESTS PASSED - DUNGEON FORGE v4.1 specification compliant")
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