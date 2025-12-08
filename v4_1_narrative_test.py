#!/usr/bin/env python3
"""
v4.1 Unified Narrative Specification Test Suite
Tests the full D&D game loop with the newly implemented v4.1 Unified Narrative Specification

CRITICAL VALIDATIONS:
- No "options" field anywhere in JSON responses
- All narration ends with open prompts, never enumerated lists
- Sentence counts match v4.1 context limits
- Strict second-person POV throughout
- No AI banned phrases
- DC system still works correctly
- All JSON responses are valid
"""

import requests
import json
import sys
import re
from typing import Dict, Any, List

# Backend URL from frontend/.env
BACKEND_URL = "https://dnd-ai-clean-test.preview.emergentagent.com/api"

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.critical_failures = []
    
    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"✅ PASS: {test_name}")
    
    def add_fail(self, test_name: str, error: str, critical: bool = False):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        if critical:
            self.critical_failures.append(f"{test_name}: {error}")
        print(f"❌ FAIL: {test_name} - {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*80}")
        print(f"v4.1 UNIFIED NARRATIVE SPECIFICATION TEST SUMMARY")
        print(f"{'='*80}")
        print(f"TOTAL TESTS: {self.passed}/{total} passed")
        
        if self.critical_failures:
            print(f"\n🚨 CRITICAL FAILURES (v4.1 Violations):")
            for error in self.critical_failures:
                print(f"  - {error}")
        
        if self.errors and not self.critical_failures:
            print(f"\nFAILED TESTS:")
            for error in self.errors:
                print(f"  - {error}")
        
        print(f"{'='*80}")
        return self.failed == 0

def count_sentences(text: str) -> int:
    """Count sentences in text using multiple delimiters"""
    # Remove markdown formatting and clean text
    clean_text = re.sub(r'\*\*.*?\*\*', '', text)  # Remove bold
    clean_text = re.sub(r'\*.*?\*', '', clean_text)  # Remove italic
    clean_text = re.sub(r'`.*?`', '', clean_text)    # Remove code
    clean_text = re.sub(r'\n+', ' ', clean_text)     # Replace newlines with spaces
    clean_text = clean_text.strip()
    
    if not clean_text:
        return 0
    
    # Split on sentence endings
    sentences = re.split(r'[.!?]+', clean_text)
    # Filter out empty strings and very short fragments
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 3]
    
    return len(sentences)

def check_second_person_pov(text: str) -> tuple[bool, List[str]]:
    """Check if text uses strict second-person POV"""
    violations = []
    
    # Check for first person violations
    first_person_patterns = [
        r'\bI\s+(?:am|was|will|have|had|do|did|can|could|should|would|might|may)',
        r'\bmy\s+\w+',
        r'\bme\s+(?:and|or|,)',
        r'\bmine\b',
        r'\bmyself\b'
    ]
    
    for pattern in first_person_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            violations.extend([f"First person: '{match}'" for match in matches])
    
    # Check for third person violations (should be minimal)
    third_person_patterns = [
        r'\bhe\s+(?:is|was|will|has|had|does|did|can|could|should|would)',
        r'\bshe\s+(?:is|was|will|has|had|does|did|can|could|should|would)',
        r'\bthey\s+(?:are|were|will|have|had|do|did|can|could|should|would)'
    ]
    
    for pattern in third_person_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            violations.extend([f"Third person: '{match}'" for match in matches])
    
    return len(violations) == 0, violations

def check_banned_ai_phrases(text: str) -> tuple[bool, List[str]]:
    """Check for banned AI phrases"""
    banned_phrases = [
        r'you notice',
        r'you feel a sense',
        r'you can\'t help but',
        r'you find yourself',
        r'it seems',
        r'appears to be',
        r'seems to be',
        r'you realize',
        r'you become aware'
    ]
    
    violations = []
    for phrase in banned_phrases:
        matches = re.findall(phrase, text, re.IGNORECASE)
        if matches:
            violations.extend(matches)
    
    return len(violations) == 0, violations

def check_open_prompt_ending(text: str) -> tuple[bool, str]:
    """Check if text ends with open prompt instead of enumerated options"""
    # Remove trailing whitespace and punctuation
    clean_text = text.strip().rstrip('.')
    
    # Check for enumerated list endings (violations)
    enumerated_patterns = [
        r'1\.\s*\w+.*?2\.\s*\w+',  # 1. ... 2. ...
        r'a\)\s*\w+.*?b\)\s*\w+',  # a) ... b) ...
        r'•\s*\w+.*?•\s*\w+',      # • ... • ...
        r'-\s*\w+.*?-\s*\w+'       # - ... - ...
    ]
    
    for pattern in enumerated_patterns:
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            return False, "Ends with enumerated list (violation)"
    
    # Check for good open prompt endings
    open_prompt_patterns = [
        r'what do you do\?',
        r'where do you go\?',
        r'how do you respond\?',
        r'what is your next move\?',
        r'what do you choose\?',
        r'how do you proceed\?',
        r'what action do you take\?'
    ]
    
    for pattern in open_prompt_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True, "Ends with open prompt"
    
    # Check if it ends with a question (general open prompt)
    if text.strip().endswith('?'):
        return True, "Ends with question (open prompt)"
    
    return False, "Does not end with clear open prompt"

def test_campaign_creation_and_intro():
    """Test Campaign Creation & Intro with v4.1 validation"""
    results = TestResults()
    
    print("🏰 Testing Campaign Creation & Intro (v4.1 Validation)")
    print(f"Backend URL: {BACKEND_URL}")
    print("-" * 80)
    
    campaign_id = None
    character_id = None
    
    try:
        # Step 1: Create campaign with world name "TestWorld"
        print("\n🌍 Step 1: Creating campaign with TestWorld...")
        
        world_payload = {
            "world_name": "TestWorld",
            "tone": "dark fantasy",
            "starting_region_hint": "Darkwood Forest"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/world-blueprint/generate",
            json=world_payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            campaign_id = data.get("campaign_id")
            
            if campaign_id:
                results.add_pass("Campaign creation")
                print(f"   ✅ Campaign created: {campaign_id}")
            else:
                results.add_fail("Campaign creation", "No campaign_id returned", critical=True)
                return results.summary()
        else:
            results.add_fail("Campaign creation", f"HTTP {response.status_code}: {response.text[:200]}", critical=True)
            return results.summary()
            
    except Exception as e:
        results.add_fail("Campaign creation", f"Exception: {str(e)}", critical=True)
        return results.summary()
    
    try:
        # Step 2: Create character in campaign
        print("\n👤 Step 2: Creating character in campaign...")
        
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
                "aspiration": {"goal": "Protect the Darkwood Forest from the spreading corruption"}
            }
        }
        
        response = requests.post(
            f"{BACKEND_URL}/characters/create",
            json=char_payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            character_id = data.get("character_id")
            
            if character_id:
                results.add_pass("Character creation")
                print(f"   ✅ Character created: {character_id}")
            else:
                results.add_fail("Character creation", "No character_id returned", critical=True)
                return results.summary()
        else:
            results.add_fail("Character creation", f"HTTP {response.status_code}: {response.text[:200]}", critical=True)
            return results.summary()
            
    except Exception as e:
        results.add_fail("Character creation", f"Exception: {str(e)}", critical=True)
        return results.summary()
    
    try:
        # Step 3: Generate intro narration and validate v4.1 compliance
        print("\n📖 Step 3: Generating intro narration (v4.1 validation)...")
        
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
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for intro generation
            if "intro" in data:
                intro_text = data["intro"]
                results.add_pass("Intro generation")
                print("   ✅ Intro generated successfully")
                
                # v4.1 VALIDATION: Check sentence count (12-16 for intro)
                sentence_count = count_sentences(intro_text)
                print(f"   📊 Sentence count: {sentence_count}")
                
                if 12 <= sentence_count <= 16:
                    results.add_pass("v4.1 Intro sentence count (12-16)")
                    print(f"   ✅ Sentence count within v4.1 limits: {sentence_count}")
                else:
                    results.add_fail("v4.1 Intro sentence count", f"Expected 12-16, got {sentence_count}", critical=True)
                
                # v4.1 VALIDATION: Check second-person POV
                pov_valid, pov_violations = check_second_person_pov(intro_text)
                if pov_valid:
                    results.add_pass("v4.1 Second-person POV")
                    print("   ✅ Uses second-person POV throughout")
                else:
                    results.add_fail("v4.1 Second-person POV", f"POV violations: {pov_violations[:3]}", critical=True)
                
                # v4.1 VALIDATION: Check for quest hook ending
                if "quest" in intro_text.lower() or "adventure" in intro_text.lower() or "danger" in intro_text.lower():
                    results.add_pass("v4.1 Quest hook ending")
                    print("   ✅ Ends with quest hook")
                else:
                    results.add_fail("v4.1 Quest hook ending", "No clear quest hook found", critical=True)
                
                # v4.1 VALIDATION: Check for banned AI phrases
                phrases_valid, banned_found = check_banned_ai_phrases(intro_text)
                if phrases_valid:
                    results.add_pass("v4.1 No banned AI phrases")
                    print("   ✅ No banned AI phrases detected")
                else:
                    results.add_fail("v4.1 Banned AI phrases", f"Found: {banned_found[:3]}", critical=True)
                
            else:
                results.add_fail("Intro generation", "No intro in response", critical=True)
            
            # v4.1 VALIDATION: Check for NO "options" field
            if "options" in data:
                results.add_fail("v4.1 No options field", "Response contains deprecated 'options' field", critical=True)
            else:
                results.add_pass("v4.1 No options field")
                print("   ✅ No deprecated 'options' field found")
                
        else:
            results.add_fail("Intro generation", f"HTTP {response.status_code}: {response.text[:200]}", critical=True)
            
    except Exception as e:
        results.add_fail("Intro generation", f"Exception: {str(e)}", critical=True)
    
    # Store campaign and character IDs for next tests
    if campaign_id and character_id:
        return results, campaign_id, character_id
    else:
        return results, None, None

def test_exploration_action(campaign_id: str, character_id: str):
    """Test Exploration Action with v4.1 validation"""
    results = TestResults()
    
    print("\n🔍 Testing Exploration Action (v4.1 Validation)")
    print("-" * 80)
    
    try:
        # Take exploration action
        print("\n🚶 Taking exploration action...")
        
        action_payload = {
            "campaign_id": campaign_id,
            "character_id": character_id,
            "player_action": "I look around the town square and examine my surroundings carefully, taking note of any interesting details or potential threats.",
            "client_target_id": None
        }
        
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm/action",
            json=action_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "narration" in data:
                narration = data["narration"]
                results.add_pass("Exploration action response")
                print("   ✅ Exploration action processed successfully")
                
                # v4.1 VALIDATION: Check sentence count (6-10 for exploration)
                sentence_count = count_sentences(narration)
                print(f"   📊 Sentence count: {sentence_count}")
                
                if 6 <= sentence_count <= 10:
                    results.add_pass("v4.1 Exploration sentence count (6-10)")
                    print(f"   ✅ Sentence count within v4.1 limits: {sentence_count}")
                else:
                    results.add_fail("v4.1 Exploration sentence count", f"Expected 6-10, got {sentence_count}", critical=True)
                
                # v4.1 VALIDATION: Check second-person POV
                pov_valid, pov_violations = check_second_person_pov(narration)
                if pov_valid:
                    results.add_pass("v4.1 Second-person POV in exploration")
                    print("   ✅ Uses second-person POV throughout")
                else:
                    results.add_fail("v4.1 Second-person POV", f"POV violations: {pov_violations[:3]}", critical=True)
                
                # v4.1 VALIDATION: Check for open prompt ending
                prompt_valid, prompt_reason = check_open_prompt_ending(narration)
                if prompt_valid:
                    results.add_pass("v4.1 Open prompt ending")
                    print(f"   ✅ {prompt_reason}")
                else:
                    results.add_fail("v4.1 Open prompt ending", prompt_reason, critical=True)
                
                # v4.1 VALIDATION: Check for banned AI phrases
                phrases_valid, banned_found = check_banned_ai_phrases(narration)
                if phrases_valid:
                    results.add_pass("v4.1 No banned AI phrases in exploration")
                    print("   ✅ No banned AI phrases detected")
                else:
                    results.add_fail("v4.1 Banned AI phrases", f"Found: {banned_found[:3]}", critical=True)
                
            else:
                results.add_fail("Exploration action", "No narration in response", critical=True)
            
            # v4.1 VALIDATION: Check for NO "options" field
            if "options" in data:
                results.add_fail("v4.1 No options field in exploration", "Response contains deprecated 'options' field", critical=True)
            else:
                results.add_pass("v4.1 No options field in exploration")
                print("   ✅ No deprecated 'options' field found")
                
        else:
            results.add_fail("Exploration action", f"HTTP {response.status_code}: {response.text[:200]}", critical=True)
            
    except Exception as e:
        results.add_fail("Exploration action", f"Exception: {str(e)}", critical=True)
    
    return results

def test_ability_check_request(campaign_id: str, character_id: str):
    """Test Ability Check Request with v4.1 validation"""
    results = TestResults()
    
    print("\n🎲 Testing Ability Check Request (v4.1 Validation)")
    print("-" * 80)
    
    try:
        # Take action that should trigger ability check
        print("\n🔓 Taking action that triggers ability check...")
        
        action_payload = {
            "campaign_id": campaign_id,
            "character_id": character_id,
            "player_action": "I try to pick the lock on the mysterious door, using my skills to carefully manipulate the mechanism.",
            "client_target_id": None
        }
        
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm/action",
            json=action_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "narration" in data:
                narration = data["narration"]
                results.add_pass("Ability check action response")
                print("   ✅ Ability check action processed successfully")
                
                # v4.1 VALIDATION: Check sentence count (6-10 for exploration context)
                sentence_count = count_sentences(narration)
                print(f"   📊 Sentence count: {sentence_count}")
                
                if 6 <= sentence_count <= 10:
                    results.add_pass("v4.1 Ability check sentence count (6-10)")
                    print(f"   ✅ Sentence count within v4.1 limits: {sentence_count}")
                else:
                    results.add_fail("v4.1 Ability check sentence count", f"Expected 6-10, got {sentence_count}", critical=True)
                
                # Check for ability check request
                if "mechanics" in data and data["mechanics"] and "check_request" in data["mechanics"]:
                    check_request = data["mechanics"]["check_request"]
                    results.add_pass("Ability check request generated")
                    print("   ✅ Ability check request generated")
                    
                    # Validate check request structure
                    required_fields = ["dc", "ability", "skill", "reason"]
                    missing_fields = [field for field in required_fields if field not in check_request]
                    
                    if not missing_fields:
                        results.add_pass("Check request structure")
                        print(f"   ✅ DC: {check_request['dc']}, Ability: {check_request['ability']}, Skill: {check_request['skill']}")
                        print(f"   ✅ Reason: {check_request['reason'][:50]}...")
                    else:
                        results.add_fail("Check request structure", f"Missing fields: {missing_fields}")
                        
                else:
                    results.add_fail("Ability check request", "No check_request generated for lock picking action")
                
            else:
                results.add_fail("Ability check action", "No narration in response", critical=True)
            
            # v4.1 VALIDATION: Check for NO "options" field
            if "options" in data:
                results.add_fail("v4.1 No options field in ability check", "Response contains deprecated 'options' field", critical=True)
            else:
                results.add_pass("v4.1 No options field in ability check")
                print("   ✅ No deprecated 'options' field found")
                
        else:
            results.add_fail("Ability check action", f"HTTP {response.status_code}: {response.text[:200]}", critical=True)
            
    except Exception as e:
        results.add_fail("Ability check action", f"Exception: {str(e)}", critical=True)
    
    return results

def test_check_resolution(campaign_id: str, character_id: str):
    """Test Check Resolution with v4.1 validation"""
    results = TestResults()
    
    print("\n⚡ Testing Check Resolution (v4.1 Validation)")
    print("-" * 80)
    
    try:
        # Resolve check with roll result
        print("\n🎯 Resolving check with roll result...")
        
        # First, make a dice roll
        dice_response = requests.post(
            f"{BACKEND_URL}/dice",
            json={"formula": "1d20+3"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if dice_response.status_code == 200:
            dice_data = dice_response.json()
            roll_total = dice_data["total"]
            print(f"   🎲 Rolled: {roll_total}")
            
            # Now resolve the check
            resolve_payload = {
                "campaign_id": campaign_id,
                "character_id": character_id,
                "check_result": roll_total,
                "check_type": "Sleight of Hand",
                "dc": 15
            }
            
            response = requests.post(
                f"{BACKEND_URL}/rpg_dm/resolve_check",
                json=resolve_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "narration" in data:
                    narration = data["narration"]
                    results.add_pass("Check resolution response")
                    print("   ✅ Check resolution processed successfully")
                    
                    # v4.1 VALIDATION: Check sentence count (should stay within limits)
                    sentence_count = count_sentences(narration)
                    print(f"   📊 Sentence count: {sentence_count}")
                    
                    if sentence_count <= 10:  # Should not exceed exploration limits
                        results.add_pass("v4.1 Check resolution sentence count")
                        print(f"   ✅ Sentence count within limits: {sentence_count}")
                    else:
                        results.add_fail("v4.1 Check resolution sentence count", f"Exceeded limits: {sentence_count}", critical=True)
                    
                    # Check for success/failure consequences
                    if roll_total >= 15:
                        if "success" in narration.lower() or "manage" in narration.lower() or "accomplish" in narration.lower():
                            results.add_pass("Success consequences described")
                            print("   ✅ Success consequences properly described")
                        else:
                            results.add_fail("Success consequences", "Success not clearly described")
                    else:
                        if "fail" in narration.lower() or "unable" in narration.lower() or "difficulty" in narration.lower():
                            results.add_pass("Failure consequences described")
                            print("   ✅ Failure consequences properly described")
                        else:
                            results.add_fail("Failure consequences", "Failure not clearly described")
                    
                    # v4.1 VALIDATION: No softening of failure
                    if roll_total < 15:
                        softening_phrases = ["almost", "nearly", "close", "partial success"]
                        has_softening = any(phrase in narration.lower() for phrase in softening_phrases)
                        if not has_softening:
                            results.add_pass("v4.1 No softening of failure")
                            print("   ✅ Failure not softened")
                        else:
                            results.add_fail("v4.1 Failure softening", "Failure was softened with qualifying language", critical=True)
                    
                else:
                    results.add_fail("Check resolution", "No narration in response", critical=True)
                
                # v4.1 VALIDATION: Check for NO "options" field
                if "options" in data:
                    results.add_fail("v4.1 No options field in check resolution", "Response contains deprecated 'options' field", critical=True)
                else:
                    results.add_pass("v4.1 No options field in check resolution")
                    print("   ✅ No deprecated 'options' field found")
                    
            else:
                results.add_fail("Check resolution", f"HTTP {response.status_code}: {response.text[:200]}", critical=True)
                
        else:
            results.add_fail("Dice roll for check resolution", f"HTTP {dice_response.status_code}")
            
    except Exception as e:
        results.add_fail("Check resolution", f"Exception: {str(e)}", critical=True)
    
    return results

def test_combat_scene(campaign_id: str, character_id: str):
    """Test Combat Scene with v4.1 validation"""
    results = TestResults()
    
    print("\n⚔️ Testing Combat Scene (v4.1 Validation)")
    print("-" * 80)
    
    try:
        # Trigger combat action
        print("\n🗡️ Taking combat action...")
        
        action_payload = {
            "campaign_id": campaign_id,
            "character_id": character_id,
            "player_action": "I draw my sword and attack the hostile bandit with a swift strike, aiming for his torso.",
            "client_target_id": None
        }
        
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm/action",
            json=action_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "narration" in data:
                narration = data["narration"]
                results.add_pass("Combat action response")
                print("   ✅ Combat action processed successfully")
                
                # v4.1 VALIDATION: Check sentence count (4-8 for combat)
                sentence_count = count_sentences(narration)
                print(f"   📊 Sentence count: {sentence_count}")
                
                if 4 <= sentence_count <= 8:
                    results.add_pass("v4.1 Combat sentence count (4-8)")
                    print(f"   ✅ Sentence count within v4.1 combat limits: {sentence_count}")
                else:
                    results.add_fail("v4.1 Combat sentence count", f"Expected 4-8, got {sentence_count}", critical=True)
                
                # v4.1 VALIDATION: Check second-person POV in combat
                pov_valid, pov_violations = check_second_person_pov(narration)
                if pov_valid:
                    results.add_pass("v4.1 Second-person POV in combat")
                    print("   ✅ Uses second-person POV throughout combat")
                else:
                    results.add_fail("v4.1 Combat POV", f"POV violations: {pov_violations[:3]}", critical=True)
                
                # Check for combat mechanics (if implemented)
                if "mechanics" in data and data["mechanics"]:
                    results.add_pass("Combat mechanics present")
                    print("   ✅ Combat mechanics generated")
                else:
                    # This might be expected if combat is not fully implemented
                    print("   ⚠️ No combat mechanics (may be expected if not implemented)")
                
            else:
                results.add_fail("Combat action", "No narration in response", critical=True)
            
            # v4.1 VALIDATION: Check for NO "options" field
            if "options" in data:
                results.add_fail("v4.1 No options field in combat", "Response contains deprecated 'options' field", critical=True)
            else:
                results.add_pass("v4.1 No options field in combat")
                print("   ✅ No deprecated 'options' field found")
                
        else:
            results.add_fail("Combat action", f"HTTP {response.status_code}: {response.text[:200]}", critical=True)
            
    except Exception as e:
        results.add_fail("Combat action", f"Exception: {str(e)}", critical=True)
    
    return results

def validate_json_responses():
    """Test that all JSON responses are valid"""
    results = TestResults()
    
    print("\n🔍 Testing JSON Response Validity")
    print("-" * 80)
    
    # Test basic endpoint for JSON validity
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=10)
        if response.status_code == 200:
            try:
                data = response.json()
                results.add_pass("JSON response validity")
                print("   ✅ Backend returns valid JSON")
            except json.JSONDecodeError as e:
                results.add_fail("JSON response validity", f"Invalid JSON: {str(e)}", critical=True)
        else:
            results.add_fail("Backend connectivity", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("Backend connectivity", f"Exception: {str(e)}", critical=True)
    
    return results

def main():
    """Run the complete v4.1 Unified Narrative Specification test suite"""
    print("🎯 v4.1 UNIFIED NARRATIVE SPECIFICATION TEST SUITE")
    print("=" * 80)
    print("Testing the full D&D game loop with v4.1 unified narrative guidelines")
    print("CRITICAL VALIDATIONS:")
    print("- No 'options' field anywhere in JSON responses")
    print("- All narration ends with open prompts, never enumerated lists")
    print("- Sentence counts match v4.1 context limits")
    print("- Strict second-person POV throughout")
    print("- No AI banned phrases")
    print("- DC system still works correctly")
    print("=" * 80)
    
    all_results = TestResults()
    
    # Test 1: JSON Response Validity
    json_results = validate_json_responses()
    all_results.passed += json_results.passed
    all_results.failed += json_results.failed
    all_results.errors.extend(json_results.errors)
    all_results.critical_failures.extend(json_results.critical_failures)
    
    # Test 2: Campaign Creation & Intro
    intro_results, campaign_id, character_id = test_campaign_creation_and_intro()
    all_results.passed += intro_results.passed
    all_results.failed += intro_results.failed
    all_results.errors.extend(intro_results.errors)
    all_results.critical_failures.extend(intro_results.critical_failures)
    
    if not campaign_id or not character_id:
        print("\n❌ Cannot continue tests without campaign and character IDs")
        return all_results.summary()
    
    # Test 3: Exploration Action
    exploration_results = test_exploration_action(campaign_id, character_id)
    all_results.passed += exploration_results.passed
    all_results.failed += exploration_results.failed
    all_results.errors.extend(exploration_results.errors)
    all_results.critical_failures.extend(exploration_results.critical_failures)
    
    # Test 4: Ability Check Request
    check_results = test_ability_check_request(campaign_id, character_id)
    all_results.passed += check_results.passed
    all_results.failed += check_results.failed
    all_results.errors.extend(check_results.errors)
    all_results.critical_failures.extend(check_results.critical_failures)
    
    # Test 5: Check Resolution
    resolution_results = test_check_resolution(campaign_id, character_id)
    all_results.passed += resolution_results.passed
    all_results.failed += resolution_results.failed
    all_results.errors.extend(resolution_results.errors)
    all_results.critical_failures.extend(resolution_results.critical_failures)
    
    # Test 6: Combat Scene
    combat_results = test_combat_scene(campaign_id, character_id)
    all_results.passed += combat_results.passed
    all_results.failed += combat_results.failed
    all_results.errors.extend(combat_results.errors)
    all_results.critical_failures.extend(combat_results.critical_failures)
    
    # Final summary
    success = all_results.summary()
    
    if all_results.critical_failures:
        print(f"\n🚨 CRITICAL v4.1 VIOLATIONS DETECTED: {len(all_results.critical_failures)}")
        print("The v4.1 Unified Narrative Specification is NOT properly implemented.")
    elif success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print("The v4.1 Unified Narrative Specification is working correctly.")
    else:
        print(f"\n⚠️ Some tests failed, but no critical v4.1 violations detected.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)