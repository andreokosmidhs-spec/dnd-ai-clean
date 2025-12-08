#!/usr/bin/env python3
"""
Focused Backend Testing for Review Request Requirements
Tests the specific functionality mentioned in the review request after dead code cleanup
"""

import requests
import json
import sys
from typing import Dict, Any, List

# Backend URL from frontend/.env
BACKEND_URL = "https://dnd-ai-clean-test.preview.emergentagent.com/api"

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

def test_campaign_creation_flow():
    """Test Campaign Creation Flow as specified in review request"""
    results = TestResults()
    
    print("🏰 Testing Campaign Creation Flow")
    print(f"Backend URL: {BACKEND_URL}")
    print("-" * 60)
    
    campaign_id = None
    character_id = None
    
    try:
        # Step 1: Create campaign with random character
        print("\n🎭 Step 1: Creating campaign with world blueprint...")
        
        world_payload = {
            "world_name": "Test World After Cleanup",
            "character": {
                "name": "Lyra Nightwhisper",
                "class": "Rogue",
                "level": 1,
                "race": "Half-Elf",
                "background": "Criminal",
                "stats": {
                    "str": 10,
                    "dex": 16,
                    "con": 14,
                    "int": 12,
                    "wis": 13,
                    "cha": 15
                },
                "hp": {"current": 10, "max": 10},
                "ac": 13,
                "equipped": [
                    {"name": "Leather Armor", "tags": ["armor", "light"]},
                    {"name": "Shortsword", "tags": ["weapon", "finesse"]},
                    {"name": "Thieves' Tools", "tags": ["tool"]}
                ],
                "conditions": [],
                "proficiencies": ["Stealth", "Investigation", "Deception", "Sleight of Hand"],
                "goals": ["Find the Shadow Collective"]
            }
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
                
                # Check world blueprint exists
                if "world_blueprint" in data:
                    results.add_pass("World blueprint generation")
                    print("   ✅ World blueprint generated")
                else:
                    results.add_fail("World blueprint generation", "No world_blueprint in response")
                    
                # Check world state initialization
                if "world_state" in data:
                    results.add_pass("World state initialization")
                    print("   ✅ World state initialized")
                else:
                    results.add_fail("World state initialization", "No world_state in response")
                    
            else:
                results.add_fail("Campaign creation", "No campaign_id returned")
                
        else:
            results.add_fail("Campaign creation", f"HTTP {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        results.add_fail("Campaign creation", f"Exception: {str(e)}")
    
    if not campaign_id:
        print("❌ Cannot continue tests without campaign_id")
        return results.summary()
    
    try:
        # Step 2: Create character in campaign
        print("\n👤 Step 2: Creating character in campaign...")
        
        char_payload = {
            "campaign_id": campaign_id,
            "character": {
                "name": "Lyra Nightwhisper",
                "class": "Rogue",
                "level": 1,
                "race": "Half-Elf",
                "background": "Criminal",
                "stats": {
                    "strength": 10,
                    "dexterity": 16,
                    "constitution": 14,
                    "intelligence": 12,
                    "wisdom": 13,
                    "charisma": 15
                },
                "hitPoints": 10,
                "proficiencies": ["Stealth", "Investigation", "Deception", "Sleight of Hand"],
                "languages": ["Common", "Elvish"],
                "inventory": ["Leather Armor", "Shortsword", "Thieves' Tools", "Burglar's Pack"],
                "aspiration": {"goal": "Find the Shadow Collective and uncover their secrets"}
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
                results.add_pass("Character creation in campaign")
                print(f"   ✅ Character created: {character_id}")
            else:
                results.add_fail("Character creation in campaign", "No character_id returned")
                
        else:
            results.add_fail("Character creation in campaign", f"HTTP {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        results.add_fail("Character creation in campaign", f"Exception: {str(e)}")
    
    if not character_id:
        print("❌ Cannot continue tests without character_id")
        return results.summary()
    
    try:
        # Step 3: Generate intro and verify entity_mentions
        print("\n📖 Step 3: Generating intro and verifying entity_mentions...")
        
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
            
            # Check intro generation
            if "intro" in data:
                results.add_pass("Intro generation")
                print("   ✅ Intro generated successfully")
                
                # Check for entity_mentions
                if "entity_mentions" in data:
                    entity_mentions = data["entity_mentions"]
                    if len(entity_mentions) >= 4:
                        results.add_pass("Entity mentions extraction (4+ entities)")
                        print(f"   ✅ Entity mentions: {len(entity_mentions)} entities extracted")
                        for entity in entity_mentions[:3]:  # Show first 3
                            print(f"      - {entity.get('name', 'Unknown')}: {entity.get('type', 'Unknown')}")
                    else:
                        results.add_fail("Entity mentions extraction", f"Only {len(entity_mentions)} entities (need 4+)")
                        print(f"   ❌ Only {len(entity_mentions)} entities extracted (need 4+)")
                else:
                    results.add_fail("Entity mentions extraction", "No entity_mentions in response")
                    print("   ❌ No entity_mentions in intro response")
                    
                # Check for scene_description
                if "scene_description" in data:
                    results.add_pass("Scene description inclusion")
                    print("   ✅ Scene description included")
                else:
                    results.add_fail("Scene description inclusion", "No scene_description in response")
                    print("   ❌ No scene_description in intro response")
                    
            else:
                results.add_fail("Intro generation", "No intro in response")
                
        else:
            results.add_fail("Intro generation", f"HTTP {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        results.add_fail("Intro generation", f"Exception: {str(e)}")
    
    return results.summary()

def test_narration_pipeline():
    """Test Narration Pipeline as specified in review request"""
    results = TestResults()
    
    print("🎭 Testing Narration Pipeline")
    print(f"Backend URL: {BACKEND_URL}")
    print("-" * 60)
    
    # Use test campaign
    campaign_id = "test-narration-campaign"
    character_id = "test-narration-character"
    
    try:
        # Test /api/rpg_dm/action endpoint
        print("\n⚔️ Testing /api/rpg_dm/action endpoint...")
        
        action_payload = {
            "campaign_id": campaign_id,
            "character_id": character_id,
            "player_action": "I carefully examine the mysterious symbols carved into the ancient stone wall, looking for any clues about their meaning.",
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
            
            # Check basic response structure
            if "narration" in data:
                results.add_pass("Action endpoint response")
                print("   ✅ Action endpoint responding correctly")
                
                # Check for entity extraction
                if "entity_mentions" in data:
                    entity_mentions = data["entity_mentions"]
                    if len(entity_mentions) > 0:
                        results.add_pass("Entity extraction in action")
                        print(f"   ✅ Entity extraction working: {len(entity_mentions)} entities")
                        for entity in entity_mentions[:2]:  # Show first 2
                            print(f"      - {entity.get('name', 'Unknown')}: {entity.get('type', 'Unknown')}")
                    else:
                        results.add_fail("Entity extraction in action", "No entities extracted")
                        print("   ❌ No entities extracted from action")
                else:
                    results.add_fail("Entity extraction in action", "No entity_mentions field")
                    print("   ❌ No entity_mentions field in response")
                
                # Check for world state update
                if "world_state_update" in data:
                    results.add_pass("World state update")
                    print("   ✅ World state update present")
                else:
                    results.add_fail("World state update", "No world_state_update in response")
                    print("   ❌ No world_state_update in response")
                    
            else:
                results.add_fail("Action endpoint response", "No narration in response")
                
        else:
            results.add_fail("Action endpoint", f"HTTP {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        results.add_fail("Action endpoint", f"Exception: {str(e)}")
    
    return results.summary()

def test_campaign_log_api():
    """Test Campaign Log API endpoints as specified in review request"""
    results = TestResults()
    
    print("📋 Testing Campaign Log API")
    print(f"Backend URL: {BACKEND_URL}")
    print("-" * 60)
    
    campaign_id = "test-log-campaign"
    
    # Test 1: GET /api/campaign/log/summary
    try:
        print("\n📊 Testing GET /api/campaign/log/summary...")
        
        response = requests.get(
            f"{BACKEND_URL}/campaign/log/summary?campaign_id={campaign_id}",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify structure and counts
            required_fields = ["total_entries", "locations_count", "npcs_count", "events_count"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                results.add_pass("Campaign log summary structure")
                print("   ✅ Summary structure correct")
                print(f"      Total entries: {data.get('total_entries', 0)}")
                print(f"      Locations: {data.get('locations_count', 0)}")
                print(f"      NPCs: {data.get('npcs_count', 0)}")
                print(f"      Events: {data.get('events_count', 0)}")
            else:
                results.add_fail("Campaign log summary structure", f"Missing fields: {missing_fields}")
                print(f"   ❌ Missing fields: {missing_fields}")
                
        else:
            results.add_fail("Campaign log summary", f"HTTP {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        results.add_fail("Campaign log summary", f"Exception: {str(e)}")
    
    # Test 2: GET /api/campaign/log/locations
    try:
        print("\n🗺️ Testing GET /api/campaign/log/locations...")
        
        response = requests.get(
            f"{BACKEND_URL}/campaign/log/locations?campaign_id={campaign_id}",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify structure
            if "locations" in data and isinstance(data["locations"], list):
                results.add_pass("Campaign log locations structure")
                print(f"   ✅ Locations structure correct: {len(data['locations'])} locations")
                
                # Check location entry structure if any exist
                if len(data["locations"]) > 0:
                    location = data["locations"][0]
                    location_fields = ["name", "type", "description", "first_mentioned"]
                    missing_loc_fields = [field for field in location_fields if field not in location]
                    
                    if not missing_loc_fields:
                        results.add_pass("Location entry structure")
                        print("   ✅ Location entry structure correct")
                    else:
                        results.add_fail("Location entry structure", f"Missing fields: {missing_loc_fields}")
                        
            else:
                results.add_fail("Campaign log locations structure", "Invalid locations structure")
                
        else:
            results.add_fail("Campaign log locations", f"HTTP {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        results.add_fail("Campaign log locations", f"Exception: {str(e)}")
    
    # Test 3: GET /api/campaign/log/npcs
    try:
        print("\n👥 Testing GET /api/campaign/log/npcs...")
        
        response = requests.get(
            f"{BACKEND_URL}/campaign/log/npcs?campaign_id={campaign_id}",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify structure
            if "npcs" in data and isinstance(data["npcs"], list):
                results.add_pass("Campaign log NPCs structure")
                print(f"   ✅ NPCs structure correct: {len(data['npcs'])} NPCs")
                
                # Check NPC entry structure if any exist
                if len(data["npcs"]) > 0:
                    npc = data["npcs"][0]
                    npc_fields = ["name", "role", "location", "first_met", "relationship"]
                    missing_npc_fields = [field for field in npc_fields if field not in npc]
                    
                    if not missing_npc_fields:
                        results.add_pass("NPC entry structure")
                        print("   ✅ NPC entry structure correct")
                    else:
                        results.add_fail("NPC entry structure", f"Missing fields: {missing_npc_fields}")
                        
            else:
                results.add_fail("Campaign log NPCs structure", "Invalid NPCs structure")
                
        else:
            results.add_fail("Campaign log NPCs", f"HTTP {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        results.add_fail("Campaign log NPCs", f"Exception: {str(e)}")
    
    return results.summary()

def test_continue_game_flow():
    """Test Continue Game Flow as specified in review request"""
    results = TestResults()
    
    print("🔄 Testing Continue Game Flow")
    print(f"Backend URL: {BACKEND_URL}")
    print("-" * 60)
    
    try:
        # Step 1: Load latest campaign
        print("\n📂 Step 1: Loading latest campaign...")
        
        response = requests.get(
            f"{BACKEND_URL}/campaigns/latest",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "campaign_id" in data:
                campaign_id = data["campaign_id"]
                results.add_pass("Load latest campaign")
                print(f"   ✅ Latest campaign loaded: {campaign_id}")
                
                # Step 2: Verify entity_mentions are re-extracted from intro
                print("\n🔍 Step 2: Verifying entity_mentions re-extraction...")
                
                if "entity_mentions" in data:
                    entity_mentions = data["entity_mentions"]
                    if len(entity_mentions) > 0:
                        results.add_pass("Entity mentions re-extraction")
                        print(f"   ✅ Entity mentions re-extracted: {len(entity_mentions)} entities")
                        for entity in entity_mentions[:3]:  # Show first 3
                            print(f"      - {entity.get('name', 'Unknown')}: {entity.get('type', 'Unknown')}")
                    else:
                        results.add_fail("Entity mentions re-extraction", "No entities re-extracted")
                        print("   ❌ No entities re-extracted from intro")
                else:
                    results.add_fail("Entity mentions re-extraction", "No entity_mentions in response")
                    print("   ❌ No entity_mentions field in campaign data")
                
                # Step 3: Verify no data loss
                print("\n💾 Step 3: Verifying no data loss...")
                
                # Check for character data
                if "character_state" in data:
                    results.add_pass("No data loss - character state intact")
                    print("   ✅ Character state intact")
                else:
                    results.add_fail("Data loss check", "Character state missing")
                    print("   ❌ Character state missing")
                    
                # Check for world state
                if "world_state" in data:
                    results.add_pass("No data loss - world state intact")
                    print("   ✅ World state intact")
                else:
                    results.add_fail("Data loss check", "World state missing")
                    print("   ❌ World state missing")
                        
            else:
                results.add_fail("Load latest campaign", "No campaign_id in response")
                
        else:
            results.add_fail("Load latest campaign", f"HTTP {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        results.add_fail("Continue game flow", f"Exception: {str(e)}")
    
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

if __name__ == "__main__":
    print("🚀 Starting Focused Backend Testing - Review Request Requirements")
    print("=" * 80)
    
    # Test backend health first
    if not test_backend_health():
        print("❌ Backend is not responding. Exiting.")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    
    # Run focused tests based on review request
    all_passed = True
    
    # Test 1: Campaign Creation Flow
    print("🎯 PRIORITY TEST 1: Campaign Creation Flow")
    print("=" * 80)
    if not test_campaign_creation_flow():
        all_passed = False
    
    print("\n" + "=" * 80)
    
    # Test 2: Narration Pipeline
    print("🎯 PRIORITY TEST 2: Narration Pipeline")
    print("=" * 80)
    if not test_narration_pipeline():
        all_passed = False
    
    print("\n" + "=" * 80)
    
    # Test 3: Campaign Log API
    print("🎯 PRIORITY TEST 3: Campaign Log API")
    print("=" * 80)
    if not test_campaign_log_api():
        all_passed = False
    
    print("\n" + "=" * 80)
    
    # Test 4: Continue Game Flow
    print("🎯 PRIORITY TEST 4: Continue Game Flow")
    print("=" * 80)
    if not test_continue_game_flow():
        all_passed = False
    
    # Final summary
    print("\n" + "🏁" + "=" * 78)
    if all_passed:
        print("🎉 ALL PRIORITY TESTS PASSED! Backend core functionality verified after dead code cleanup.")
        print("✅ Campaign creation, narration pipeline, and campaign log APIs working correctly.")
        sys.exit(0)
    else:
        print("❌ SOME PRIORITY TESTS FAILED. Check the output above for details.")
        print("🔍 Focus on failed tests - these are the core requirements from the review request.")
        sys.exit(1)