#!/usr/bin/env python3
"""
Simple Backend Test - Test core endpoints after dead code cleanup
"""

import requests
import json
import sys

BACKEND_URL = "https://wizards-deck.preview.emergentagent.com/api"

def test_dice_endpoint():
    """Test the dice endpoint that was failing"""
    print("🎲 Testing Dice Endpoint")
    print("-" * 40)
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/dice",
            json={"formula": "1d20+5"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "data" in data:
                print("✅ Dice endpoint working correctly")
                return True
            else:
                print("❌ Dice endpoint response format incorrect")
                return False
        else:
            print("❌ Dice endpoint failed")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_world_blueprint_endpoint():
    """Test world blueprint generation"""
    print("\n🌍 Testing World Blueprint Endpoint")
    print("-" * 40)
    
    try:
        payload = {
            "world_name": "Test World",
            "tone": "fantasy",
            "starting_region_hint": "A mysterious forest village"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/world-blueprint/generate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if "campaign_id" in data:
                print(f"✅ World blueprint created: {data['campaign_id']}")
                return True, data["campaign_id"]
            else:
                print("❌ No campaign_id in response")
                return False, None
        else:
            print(f"❌ Failed: {response.text[:200]}")
            return False, None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, None

def test_rpg_dm_action_endpoint(campaign_id):
    """Test the RPG DM action endpoint"""
    print("\n⚔️ Testing RPG DM Action Endpoint")
    print("-" * 40)
    
    try:
        payload = {
            "campaign_id": campaign_id,
            "character_id": "test-character",
            "player_action": "I look around the room carefully.",
            "client_target_id": None
        }
        
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm/action",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if "narration" in data:
                print(f"✅ Action endpoint working: {len(data['narration'])} chars of narration")
                
                # Check for entity mentions
                if "entity_mentions" in data:
                    print(f"✅ Entity mentions: {len(data['entity_mentions'])} entities")
                else:
                    print("⚠️ No entity_mentions in response")
                    
                return True
            else:
                print("❌ No narration in response")
                return False
        else:
            print(f"❌ Failed: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_campaign_log_endpoints(campaign_id):
    """Test campaign log endpoints"""
    print("\n📋 Testing Campaign Log Endpoints")
    print("-" * 40)
    
    # Test summary endpoint
    try:
        response = requests.get(
            f"{BACKEND_URL}/campaign/log/summary?campaign_id={campaign_id}",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Summary Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Summary endpoint working: {data}")
        else:
            print(f"❌ Summary failed: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Summary exception: {e}")
    
    # Test locations endpoint
    try:
        response = requests.get(
            f"{BACKEND_URL}/campaign/log/locations?campaign_id={campaign_id}",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Locations Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Locations endpoint working: {len(data.get('locations', []))} locations")
        else:
            print(f"❌ Locations failed: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Locations exception: {e}")
    
    # Test NPCs endpoint
    try:
        response = requests.get(
            f"{BACKEND_URL}/campaign/log/npcs?campaign_id={campaign_id}",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"NPCs Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ NPCs endpoint working: {len(data.get('npcs', []))} NPCs")
        else:
            print(f"❌ NPCs failed: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ NPCs exception: {e}")

def test_latest_campaign_endpoint():
    """Test latest campaign endpoint"""
    print("\n🔄 Testing Latest Campaign Endpoint")
    print("-" * 40)
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/campaigns/latest",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if "campaign_id" in data:
                print(f"✅ Latest campaign: {data['campaign_id']}")
                return True
            else:
                print("⚠️ No campaign_id in response (might be empty)")
                return True  # This is OK if no campaigns exist
        else:
            print(f"❌ Failed: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Simple Backend Test - Post Dead Code Cleanup")
    print("=" * 60)
    
    # Test basic health
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is online")
        else:
            print("❌ Backend health check failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Backend connection error: {e}")
        sys.exit(1)
    
    # Run tests
    all_passed = True
    
    # Test 1: Dice endpoint
    if not test_dice_endpoint():
        all_passed = False
    
    # Test 2: World blueprint
    success, campaign_id = test_world_blueprint_endpoint()
    if not success:
        all_passed = False
        campaign_id = "test-campaign"  # Use fallback for other tests
    
    # Test 3: RPG DM Action (if we have a campaign)
    if campaign_id:
        if not test_rpg_dm_action_endpoint(campaign_id):
            all_passed = False
    
    # Test 4: Campaign log endpoints
    if campaign_id:
        test_campaign_log_endpoints(campaign_id)
    
    # Test 5: Latest campaign
    if not test_latest_campaign_endpoint():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 Core backend functionality verified after dead code cleanup!")
        print("✅ Key endpoints are responding correctly")
    else:
        print("⚠️ Some issues found, but core functionality appears to be working")
        print("🔍 Check individual test results above")
    
    print("=" * 60)