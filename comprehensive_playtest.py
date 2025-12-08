#!/usr/bin/env python3
"""
Comprehensive A-Version Regression Playtest
Tests plot armor, combat mechanics, location continuity, and pacing
"""

import requests
import json
import time
from typing import Dict, Any, List

API_URL = "http://localhost:8001/api"
CAMPAIGN_ID = "bb90306f-7eb3-4bf2-97a5-928b234d56c4"
CHARACTER_ID = "4beab239-48e9-4fee-996e-0c5515aee533"

class PlaytestRunner:
    def __init__(self):
        self.results = []
        self.pass_count = 0
        self.fail_count = 0
        self.partial_count = 0
    
    def send_action(self, action: str, target_id: str = None) -> Dict[str, Any]:
        """Send an action to the DM"""
        payload = {
            "campaign_id": CAMPAIGN_ID,
            "character_id": CHARACTER_ID,
            "player_action": action,
            "client_target_id": target_id
        }
        
        response = requests.post(f"{API_URL}/rpg_dm/action", json=payload)
        return response.json()
    
    def log_result(self, test_name: str, status: str, details: str):
        """Log a test result"""
        self.results.append({
            "test": test_name,
            "status": status,
            "details": details
        })
        
        if status == "✅ PASS":
            self.pass_count += 1
        elif status == "❌ FAIL":
            self.fail_count += 1
        else:
            self.partial_count += 1
    
    def print_section(self, title: str):
        """Print a section header"""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70 + "\n")
    
    def run_playtest_1(self):
        """PLAYTEST 1: Plot Armor & Consequences"""
        self.print_section("PLAYTEST SCRIPT 1: Plot Armor & Consequences")
        
        # Attack 1
        print("--- Attack 1: First punch to elder ---")
        response1 = self.send_action("I punch the village elder in the face.")
        
        narration1 = response1.get('narration', '')
        world_update1 = response1.get('world_state_update', {})
        
        print(f"Narration: {narration1[:200]}...")
        print(f"World State Update: {world_update1}")
        print(f"Combat Started: {response1.get('starts_combat', False)}")
        
        # Check: NPC should not die, consequences recorded
        elder_alive = "die" not in narration1.lower() and "dead" not in narration1.lower() and "killed" not in narration1.lower()
        consequences_recorded = any(key in world_update1 for key in ['guard_alert', 'last_offense', 'transgressions'])
        
        if elder_alive and consequences_recorded:
            self.log_result("Plot Armor - Attack 1", "✅ PASS", "NPC survived, consequences recorded")
            print("✅ PASS: NPC survived, consequences recorded\n")
        elif elder_alive:
            self.log_result("Plot Armor - Attack 1", "⚠️ PARTIAL", "NPC survived but no clear consequence tracking")
            print("⚠️ PARTIAL: NPC survived but no clear consequence tracking\n")
        else:
            self.log_result("Plot Armor - Attack 1", "❌ FAIL", "NPC may have died")
            print("❌ FAIL: NPC may have died\n")
        
        time.sleep(1)
        
        # Attack 2
        print("--- Attack 2: Second punch (escalation expected) ---")
        response2 = self.send_action("I punch the elder again!")
        
        narration2 = response2.get('narration', '')
        world_update2 = response2.get('world_state_update', {})
        
        print(f"Narration: {narration2[:200]}...")
        print(f"World State Update: {world_update2}")
        
        # Check for escalation
        escalation_keywords = ['guard', 'arrest', 'weapon', 'stop', 'restrain', 'combat']
        has_escalation = any(keyword in narration2.lower() for keyword in escalation_keywords)
        
        if has_escalation:
            self.log_result("Plot Armor - Attack 2", "✅ PASS", "Escalation detected")
            print("✅ PASS: Escalation detected\n")
        else:
            self.log_result("Plot Armor - Attack 2", "⚠️ PARTIAL", "No clear escalation")
            print("⚠️ PARTIAL: No clear escalation in response\n")
        
        time.sleep(1)
        
        # Attack 3
        print("--- Attack 3: Third punch (severe consequences expected) ---")
        response3 = self.send_action("I punch the elder a third time!")
        
        narration3 = response3.get('narration', '')
        combat_started = response3.get('starts_combat', False)
        
        print(f"Narration: {narration3[:200]}...")
        print(f"Combat Started: {combat_started}")
        
        if combat_started:
            self.log_result("Plot Armor - Attack 3", "✅ PASS", "Combat initiated after repeated assault")
            print("✅ PASS: Combat initiated after repeated assault\n")
        else:
            self.log_result("Plot Armor - Attack 3", "⚠️ PARTIAL", "No combat yet despite 3 attacks")
            print("⚠️ PARTIAL: No combat yet despite 3 attacks\n")
    
    def run_playtest_3(self):
        """PLAYTEST 3: Location & NPC Continuity"""
        self.print_section("PLAYTEST SCRIPT 3: Location & NPC Continuity")
        
        # First, travel to ruins
        print("--- Step 1: Travel to ruins ---")
        travel_response = self.send_action("I travel to the Shattered Tower ruins.")
        
        narration = travel_response.get('narration', '')
        location = travel_response.get('world_state_update', {}).get('current_location', 'Unknown')
        
        print(f"Narration: {narration[:300]}...")
        print(f"Location: {location}\n")
        
        time.sleep(1)
        
        # Test: Look for merchant in ruins (should fail)
        print("--- Test A: Look for merchant in ruins (SHOULD FAIL) ---")
        merchant_response = self.send_action("I look for a merchant to buy supplies.")
        
        merchant_narration = merchant_response.get('narration', '')
        active_npcs = merchant_response.get('world_state_update', {}).get('active_npcs', [])
        
        print(f"Narration: {merchant_narration[:300]}...")
        print(f"Active NPCs: {active_npcs}")
        
        # Check if DM correctly rejected merchant
        rejection_keywords = ['no merchant', 'not here', 'no shop', 'ruins', 'abandoned', 'return to', 'back to town']
        merchant_spawned = 'merchant' in str(active_npcs).lower() or any(word in merchant_narration.lower() for word in ['sells', 'shop is', 'merchant greets'])
        correctly_rejected = any(keyword in merchant_narration.lower() for keyword in rejection_keywords)
        
        if correctly_rejected and not merchant_spawned:
            self.log_result("Location Continuity - Merchant in Ruins", "✅ PASS", "DM correctly rejected merchant in ruins")
            print("✅ PASS: DM correctly rejected merchant in ruins\n")
        elif not merchant_spawned:
            self.log_result("Location Continuity - Merchant in Ruins", "⚠️ PARTIAL", "No merchant spawned but unclear rejection")
            print("⚠️ PARTIAL: No merchant spawned but rejection unclear\n")
        else:
            self.log_result("Location Continuity - Merchant in Ruins", "❌ FAIL", "Merchant inappropriately spawned in ruins")
            print("❌ FAIL: Merchant inappropriately spawned in ruins\n")
        
        time.sleep(1)
        
        # Test: Look for innkeeper in ruins (should fail)
        print("--- Test B: Talk to innkeeper in ruins (SHOULD FAIL) ---")
        innkeeper_response = self.send_action("I talk to the innkeeper.")
        
        innkeeper_narration = innkeeper_response.get('narration', '')
        
        print(f"Narration: {innkeeper_narration[:300]}...")
        
        # Check if DM correctly rejected innkeeper
        innkeeper_rejection = ['no inn', 'no innkeeper', 'not here', "isn't an inn", 'ruins', 'no tavern']
        innkeeper_spawned = any(word in innkeeper_narration.lower() for word in ['innkeeper says', 'innkeeper greets', 'behind the bar', 'wipes the counter'])
        correctly_rejected_inn = any(keyword in innkeeper_narration.lower() for keyword in innkeeper_rejection)
        
        if correctly_rejected_inn and not innkeeper_spawned:
            self.log_result("Location Continuity - Innkeeper in Ruins", "✅ PASS", "DM correctly rejected innkeeper in ruins")
            print("✅ PASS: DM correctly rejected innkeeper in ruins\n")
        elif not innkeeper_spawned:
            self.log_result("Location Continuity - Innkeeper in Ruins", "⚠️ PARTIAL", "No innkeeper spawned but unclear rejection")
            print("⚠️ PARTIAL: No innkeeper spawned but rejection unclear\n")
        else:
            self.log_result("Location Continuity - Innkeeper in Ruins", "❌ FAIL", "Innkeeper inappropriately spawned in ruins")
            print("❌ FAIL: Innkeeper inappropriately spawned in ruins\n")
        
        time.sleep(1)
        
        # Return to town and verify merchant CAN appear
        print("--- Step 2: Return to town ---")
        return_response = self.send_action("I return to the village.")
        
        print(f"Narration: {return_response.get('narration', '')[:200]}...")
        print(f"Location: {return_response.get('world_state_update', {}).get('current_location', 'Unknown')}\n")
        
        time.sleep(1)
        
        # Now merchant should be available
        print("--- Test C: Look for merchant in town (SHOULD SUCCEED) ---")
        town_merchant_response = self.send_action("I look for a merchant.")
        
        town_merchant_narration = town_merchant_response.get('narration', '')
        
        print(f"Narration: {town_merchant_narration[:300]}...")
        
        merchant_found = any(word in town_merchant_narration.lower() for word in ['merchant', 'shop', 'stall', 'goods', 'wares'])
        
        if merchant_found:
            self.log_result("Location Continuity - Merchant in Town", "✅ PASS", "Merchant correctly available in town")
            print("✅ PASS: Merchant correctly available in town\n")
        else:
            self.log_result("Location Continuity - Merchant in Town", "⚠️ PARTIAL", "Merchant response unclear in town")
            print("⚠️ PARTIAL: Merchant response unclear in town\n")
    
    def run_playtest_4(self):
        """PLAYTEST 4: Pacing & Tension"""
        self.print_section("PLAYTEST SCRIPT 4: Pacing, Tension & Information")
        
        # Calm observation
        print("--- Step 1: Calm observation in town ---")
        calm_response = self.send_action("I quietly sit and observe the room.")
        
        calm_narration = calm_response.get('narration', '')
        
        print(f"Narration: {calm_narration[:300]}...")
        print(f"Narration Length: {len(calm_narration)} characters")
        
        # Check for calm, descriptive style
        calm_indicators = ['peaceful', 'quiet', 'calm', 'observe', 'notice', 'see']
        is_calm = any(indicator in calm_narration.lower() for indicator in calm_indicators)
        
        if is_calm and len(calm_narration) > 100:
            self.log_result("Pacing - Calm Phase", "✅ PASS", "Calm, descriptive narration")
            print("✅ PASS: Calm, descriptive narration style detected\n")
        else:
            self.log_result("Pacing - Calm Phase", "⚠️ PARTIAL", "Narration unclear or too brief")
            print("⚠️ PARTIAL: Narration style unclear\n")
        
        time.sleep(1)
        
        # Building tension
        print("--- Step 2: Explore dangerous area (tension building) ---")
        danger_response = self.send_action("I explore the dark outskirts where danger is rumored.")
        
        danger_narration = danger_response.get('narration', '')
        
        print(f"Narration: {danger_narration[:300]}...")
        
        # Check for suspenseful language
        tension_indicators = ['dark', 'shadow', 'danger', 'careful', 'cautious', 'ominous', 'eerie', 'tense']
        has_tension = any(indicator in danger_narration.lower() for indicator in tension_indicators)
        
        if has_tension:
            self.log_result("Pacing - Building Tension", "✅ PASS", "Suspenseful narration detected")
            print("✅ PASS: Suspenseful, tense narration detected\n")
        else:
            self.log_result("Pacing - Building Tension", "⚠️ PARTIAL", "Tension not clearly conveyed")
            print("⚠️ PARTIAL: Tension not clearly conveyed\n")
    
    def print_summary(self):
        """Print test summary"""
        self.print_section("TEST SUMMARY")
        
        print(f"Total Tests: {len(self.results)}")
        print(f"✅ Passed: {self.pass_count}")
        print(f"⚠️ Partial: {self.partial_count}")
        print(f"❌ Failed: {self.fail_count}")
        print()
        
        print("Detailed Results:")
        print("-" * 70)
        for result in self.results:
            print(f"{result['status']} {result['test']}")
            print(f"   Details: {result['details']}")
        print()
    
    def run_all(self):
        """Run all playtests"""
        try:
            self.run_playtest_1()
            self.run_playtest_3()
            self.run_playtest_4()
            self.print_summary()
        except Exception as e:
            print(f"\n❌ Error during playtest execution: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    runner = PlaytestRunner()
    runner.run_all()
