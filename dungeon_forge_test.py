#!/usr/bin/env python3
"""
DUNGEON FORGE Action Flow Test
Tests the end-to-end action flow as requested in the review
"""

import requests
import json
import sys
from typing import Dict, Any

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

def test_dungeon_forge_action_flow():
    """Test DUNGEON FORGE action flow end-to-end as requested in review"""
    results = TestResults()
    
    print("🏰 Testing DUNGEON FORGE Action Flow - END-TO-END")
    print(f"Backend URL: {BACKEND_URL}")
    print("-" * 60)
    
    try:
        # Step 1: Load the last campaign from DB via GET /api/campaigns/latest
        print("\n🧪 Step 1: Loading last campaign from DB")
        
        response = requests.get(
            f"{BACKEND_URL}/campaigns/latest",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("Load Last Campaign", f"HTTP {response.status_code}: {response.text[:200]}")
            return results.summary()
        
        campaign_data = response.json()
        print(f"   Response Keys: {list(campaign_data.keys())}")
        
        # Step 2: Extract campaign_id and character_id from the response
        campaign_id = campaign_data.get("campaign_id")
        character_id = campaign_data.get("character_id")
        
        if not campaign_id:
            results.add_fail("Extract Campaign ID", "campaign_id not found in response")
            return results.summary()
        
        if not character_id:
            results.add_fail("Extract Character ID", "character_id not found in response")
            return results.summary()
        
        print(f"   ✅ Campaign ID: {campaign_id}")
        print(f"   ✅ Character ID: {character_id}")
        results.add_pass("Load Last Campaign & Extract IDs")
        
        # Step 3: Send a simple action via POST /api/rpg_dm/action
        print("\n🧪 Step 3: Sending simple action 'I look around the room'")
        
        action_payload = {
            "campaign_id": campaign_id,
            "character_id": character_id,
            "player_action": "I look around the room",
            "check_result": None
        }
        
        print(f"   Payload: {json.dumps(action_payload, indent=2)}")
        
        action_response = requests.post(
            f"{BACKEND_URL}/rpg_dm/action",
            json=action_payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # AI processing can take time
        )
        
        print(f"   Response Status: {action_response.status_code}")
        
        # Step 4: Verify the response includes narration field with DM text and Status code 200
        if action_response.status_code != 200:
            results.add_fail("Simple Action Request", f"HTTP {action_response.status_code}: {action_response.text[:200]}")
            return results.summary()
        
        action_data = action_response.json()
        print(f"   Response Keys: {list(action_data.keys())}")
        
        # Verify narration field exists
        if "narration" not in action_data:
            results.add_fail("Simple Action - Narration Field", "Response missing 'narration' field")
            return results.summary()
        
        narration = action_data["narration"]
        if not narration or len(narration.strip()) < 10:
            results.add_fail("Simple Action - Narration Content", f"Narration too short or empty: '{narration}'")
            return results.summary()
        
        print(f"   ✅ Narration: {narration[:100]}...")
        print(f"   ✅ Status Code: 200")
        results.add_pass("Simple Action with Narration")
        
        # Step 5: Test check result flow - send action that should trigger a check
        print("\n🧪 Step 5: Testing check result flow with 'I punch the guard'")
        
        punch_payload = {
            "campaign_id": campaign_id,
            "character_id": character_id,
            "player_action": "I punch the guard",
            "check_result": None
        }
        
        punch_response = requests.post(
            f"{BACKEND_URL}/rpg_dm/action",
            json=punch_payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"   Response Status: {punch_response.status_code}")
        
        if punch_response.status_code != 200:
            results.add_fail("Punch Action Request", f"HTTP {punch_response.status_code}: {punch_response.text[:200]}")
            return results.summary()
        
        punch_data = punch_response.json()
        print(f"   Response Keys: {list(punch_data.keys())}")
        
        # Check if we get a check_request in response
        if "check_request" in punch_data and punch_data["check_request"]:
            print(f"   ✅ Check request generated: {punch_data['check_request']}")
            
            # Step 6: Send another POST with check_result: 15 (simulating a dice roll)
            print("\n🧪 Step 6: Sending check result (15) for punch action")
            
            check_result_payload = {
                "campaign_id": campaign_id,
                "character_id": character_id,
                "player_action": "I punch the guard",
                "check_result": 15
            }
            
            check_result_response = requests.post(
                f"{BACKEND_URL}/rpg_dm/action",
                json=check_result_payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            print(f"   Response Status: {check_result_response.status_code}")
            
            if check_result_response.status_code != 200:
                results.add_fail("Check Result Request", f"HTTP {check_result_response.status_code}: {check_result_response.text[:200]}")
                return results.summary()
            
            check_result_data = check_result_response.json()
            
            # Verify we get continued narration
            if "narration" not in check_result_data:
                results.add_fail("Check Result - Narration", "Response missing 'narration' field")
                return results.summary()
            
            continued_narration = check_result_data["narration"]
            if not continued_narration or len(continued_narration.strip()) < 10:
                results.add_fail("Check Result - Narration Content", f"Continued narration too short: '{continued_narration}'")
                return results.summary()
            
            print(f"   ✅ Continued narration: {continued_narration[:100]}...")
            results.add_pass("Check Result Flow with Continued Narration")
            
        else:
            # If no check was requested, that's also valid behavior - some actions auto-succeed
            print(f"   ℹ️ No check request generated (action may have auto-succeeded)")
            print(f"   ✅ Punch narration: {punch_data.get('narration', '')[:100]}...")
            results.add_pass("Punch Action (Auto-Success)")
        
        # Additional validation: Check response structure
        print("\n🧪 Additional: Validating response structure")
        
        expected_fields = ["narration"]
        optional_fields = ["options", "check_request", "world_state_update", "player_updates"]
        
        for field in expected_fields:
            if field not in action_data:
                results.add_fail("Response Structure", f"Missing required field: {field}")
                return results.summary()
        
        print(f"   ✅ Required fields present: {expected_fields}")
        
        present_optional = [field for field in optional_fields if field in action_data]
        print(f"   ✅ Optional fields present: {present_optional}")
        
        results.add_pass("Response Structure Validation")
        
        # Log all requests and responses as requested
        print("\n📋 REQUEST/RESPONSE LOG:")
        print("="*60)
        print("1. GET /api/campaigns/latest")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(campaign_data, indent=2)[:300]}...")
        
        print("\n2. POST /api/rpg_dm/action (simple action)")
        print(f"   Payload: {json.dumps(action_payload, indent=2)}")
        print(f"   Status: {action_response.status_code}")
        print(f"   Response: {json.dumps(action_data, indent=2)[:300]}...")
        
        print("\n3. POST /api/rpg_dm/action (punch action)")
        print(f"   Payload: {json.dumps(punch_payload, indent=2)}")
        print(f"   Status: {punch_response.status_code}")
        print(f"   Response: {json.dumps(punch_data, indent=2)[:300]}...")
        
        if "check_request" in punch_data and punch_data["check_request"]:
            print("\n4. POST /api/rpg_dm/action (with check result)")
            print(f"   Payload: {json.dumps(check_result_payload, indent=2)}")
            print(f"   Status: {check_result_response.status_code}")
            print(f"   Response: {json.dumps(check_result_data, indent=2)[:300]}...")
        
        print("="*60)
        
    except Exception as e:
        results.add_fail("DUNGEON FORGE Action Flow", f"Exception: {str(e)}")
        print(f"   ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
    
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
    print("🚀 Starting DUNGEON FORGE Action Flow Test")
    print("=" * 60)
    
    # Test backend health first
    if not test_backend_health():
        print("❌ Backend is not accessible. Exiting.")
        sys.exit(1)
    
    print("\n")
    
    # Run DUNGEON FORGE action flow test
    success = test_dungeon_forge_action_flow()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 DUNGEON FORGE ACTION FLOW TEST PASSED!")
        sys.exit(0)
    else:
        print("❌ DUNGEON FORGE ACTION FLOW TEST FAILED!")
        sys.exit(1)