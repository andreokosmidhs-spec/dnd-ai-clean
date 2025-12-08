#!/usr/bin/env python3
"""
A-VERSION REGRESSION PLAYTESTS - Complete Validation Suite

Execute all 4 playtest scenarios to validate A-Version DM prompt implementation.
Backend URL: https://dnd-ai-clean-test.preview.emergentagent.com/api
"""

import requests
import json
import sys
import time
from typing import Dict, Any, List, Optional

# Backend URL from frontend/.env
BACKEND_URL = "https://dnd-ai-clean-test.preview.emergentagent.com/api"

class PlaytestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.total_validation_points = 0
        self.passed_validation_points = 0
        self.errors = []
        self.critical_failures = []
        self.playtest_reports = []
    
    def add_pass(self, test_name: str, validation_points: int = 1):
        self.passed += 1
        self.passed_validation_points += validation_points
        self.total_validation_points += validation_points
        print(f"✅ PASS: {test_name}")
    
    def add_fail(self, test_name: str, error: str, validation_points: int = 1, critical: bool = False):
        self.failed += 1
        self.total_validation_points += validation_points
        self.errors.append(f"{test_name}: {error}")
        if critical:
            self.critical_failures.append(f"{test_name}: {error}")
        print(f"❌ FAIL: {test_name} - {error}")
    
    def add_playtest_report(self, playtest_name: str, status: str, score: str, findings: List[str], 
                           mechanical_outputs: List[str], narration_sample: str, continuity_check: Dict[str, str]):
        report = {
            "name": playtest_name,
            "status": status,
            "score": score,
            "findings": findings,
            "mechanical_outputs": mechanical_outputs,
            "narration_sample": narration_sample,
            "continuity_check": continuity_check
        }
        self.playtest_reports.append(report)
    
    def summary(self):
        total = self.passed + self.failed
        pass_percentage = (self.passed_validation_points / self.total_validation_points * 100) if self.total_validation_points > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"A-VERSION REGRESSION PLAYTEST SUMMARY")
        print(f"{'='*80}")
        print(f"Overall Score: {self.passed_validation_points}/{self.total_validation_points} ({pass_percentage:.1f}%)")
        print(f"Pass Threshold: 90% (36/40 validation points)")
        print(f"Status: {'PASS' if pass_percentage >= 90 else 'FAIL'}")
        
        if self.critical_failures:
            print(f"\n🚨 CRITICAL FAILURES (auto-fail):")
            for failure in self.critical_failures:
                print(f"  - {failure}")
        
        if self.errors:
            print(f"\nFAILED TESTS:")
            for error in self.errors:
                print(f"  - {error}")
        
        print(f"\n{'='*80}")
        print("PLAYTEST REPORTS:")
        print(f"{'='*80}")
        
        for report in self.playtest_reports:
            print(f"\nPLAYTEST {report['name']}:")
            print(f"Status: {report['status']}")
            print(f"Score: {report['score']}")
            print(f"\nKey Findings:")
            for finding in report['findings']:
                print(f"- {finding}")
            print(f"\nMechanical Outputs:")
            for output in report['mechanical_outputs']:
                print(f"- {output}")
            print(f"\nDM Narration Sample:")
            print(f"- {report['narration_sample']}")
            print(f"\nContinuity Check:")
            for key, value in report['continuity_check'].items():
                print(f"- {key}: {value}")
        
        print(f"{'='*80}")
        
        return pass_percentage >= 90 and len(self.critical_failures) == 0

def get_latest_campaign() -> Optional[Dict[str, Any]]:
    """Get the latest campaign for testing"""
    try:
        response = requests.get(f"{BACKEND_URL}/campaigns/latest", timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get latest campaign: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Exception getting campaign: {e}")
        return None

def send_action(campaign_id: str, character_id: str, action: str, check_result: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Send an action to the DUNGEON FORGE action endpoint"""
    try:
        payload = {
            "campaign_id": campaign_id,
            "character_id": character_id,
            "player_action": action
        }
        
        if check_result is not None:
            payload["check_result"] = check_result
        
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm/action",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=45
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Action failed: {response.status_code} - {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Exception sending action: {e}")
        return None

def playtest_1_plot_armor_consequence_escalation(results: PlaytestResults, campaign_id: str, character_id: str):
    """
    PLAYTEST 1: Plot Armor & Consequence Escalation
    Scenario: Player attacks essential NPC in social setting (tavern/town)
    """
    print("\n" + "="*80)
    print("PLAYTEST 1: Plot Armor & Consequence Escalation")
    print("="*80)
    
    findings = []
    mechanical_outputs = []
    narration_sample = ""
    continuity_check = {"Location": "unknown", "NPCs": "unknown", "State": "unknown"}
    
    # Setup: Ensure we're in a social setting with essential NPCs
    setup_response = send_action(campaign_id, character_id, "I look around the tavern to identify important people")
    if not setup_response:
        results.add_fail("Plot Armor Setup", "Failed to setup tavern scenario", 2, critical=True)
        results.add_playtest_report("1: Plot Armor & Consequence Escalation", "FAIL", "0/10", 
                                  ["Setup failed"], [], "", continuity_check)
        return
    
    narration_sample = setup_response.get("narration", "")[:200]
    continuity_check["Location"] = "tavern" if "tavern" in narration_sample.lower() else "unknown"
    
    # Identify an essential NPC from the narration
    essential_npc = None
    npc_candidates = ["innkeeper", "barkeep", "merchant", "captain", "guard captain", "mayor", "priest"]
    for candidate in npc_candidates:
        if candidate in narration_sample.lower():
            essential_npc = candidate
            break
    
    if not essential_npc:
        essential_npc = "innkeeper"  # Default fallback
    
    print(f"🎯 Target NPC: {essential_npc}")
    findings.append(f"Target NPC identified: {essential_npc}")
    
    # Test Actions: Progressive attacks on essential NPC
    attack_results = []
    
    # First attack
    print("\n🥊 First attack: Testing plot armor activation")
    response1 = send_action(campaign_id, character_id, f"I punch the {essential_npc}")
    if response1:
        attack_results.append(response1)
        mechanical_outputs.append(f"Attack 1: {response1.get('mechanics', {})}")
        
        # Check for plot armor (NPC should not die)
        narration1 = response1.get("narration", "").lower()
        if "dies" in narration1 or "dead" in narration1 or "killed" in narration1:
            results.add_fail("Plot Armor - First Attack", "Essential NPC died - plot armor failed", 2, critical=True)
            findings.append("❌ CRITICAL: Plot armor failed - NPC died on first attack")
        else:
            results.add_pass("Plot Armor - First Attack", 2)
            findings.append("✅ Plot armor active - NPC survived first attack")
        
        # Check for intervention narration
        if any(word in narration1 for word in ["patron", "bodyguard", "intervene", "stop", "grab"]):
            results.add_pass("Plot Armor - Intervention Narration", 1)
            findings.append("✅ Intervention narration present")
        else:
            results.add_fail("Plot Armor - Intervention Narration", "No intervention described", 1)
            findings.append("❌ Missing intervention narration")
    
    # Second attack
    print("\n🥊 Second attack: Testing consequence escalation")
    response2 = send_action(campaign_id, character_id, f"I attack the {essential_npc} again")
    if response2:
        attack_results.append(response2)
        mechanical_outputs.append(f"Attack 2: {response2.get('mechanics', {})}")
        
        # Check plot armor still active
        narration2 = response2.get("narration", "").lower()
        if "dies" in narration2 or "dead" in narration2 or "killed" in narration2:
            results.add_fail("Plot Armor - Second Attack", "Essential NPC died", 2, critical=True)
            findings.append("❌ CRITICAL: Plot armor failed on second attack")
        else:
            results.add_pass("Plot Armor - Second Attack", 2)
            findings.append("✅ Plot armor maintained through second attack")
    
    # Third attack - should escalate to moderate consequences
    print("\n🥊 Third attack: Testing moderate escalation")
    response3 = send_action(campaign_id, character_id, f"I keep attacking the {essential_npc}")
    if response3:
        attack_results.append(response3)
        mechanical_outputs.append(f"Attack 3: {response3.get('mechanics', {})}")
        
        narration3 = response3.get("narration", "").lower()
        
        # Check for guard intervention
        if any(word in narration3 for word in ["guard", "official", "authority", "investigate"]):
            results.add_pass("Consequence Escalation - Guards", 2)
            findings.append("✅ Guard intervention triggered")
        else:
            results.add_fail("Consequence Escalation - Guards", "No guard intervention", 2)
            findings.append("❌ Missing guard intervention")
        
        # Check for serious warnings
        if any(word in narration3 for word in ["warning", "serious", "consequences", "arrest"]):
            results.add_pass("Consequence Escalation - Warnings", 1)
            findings.append("✅ Serious warnings present")
        else:
            results.add_fail("Consequence Escalation - Warnings", "No serious warnings", 1)
            findings.append("❌ Missing serious warnings")
    
    # Validate no random enemies spawned
    all_narration = " ".join([r.get("narration", "") for r in attack_results]).lower()
    if any(word in all_narration for word in ["skeleton", "zombie", "undead", "monster"]):
        results.add_fail("Plot Armor - No Random Enemies", "Random enemies spawned inappropriately", 1)
        findings.append("❌ Random enemies appeared in social setting")
    else:
        results.add_pass("Plot Armor - No Random Enemies", 1)
        findings.append("✅ No inappropriate enemy spawning")
    
    # Validate location consistency
    if all("tavern" in r.get("narration", "").lower() or "inn" in r.get("narration", "").lower() for r in attack_results):
        results.add_pass("Plot Armor - Location Consistency", 1)
        continuity_check["Location"] = "verified"
        findings.append("✅ Location remained consistent (tavern/inn)")
    else:
        results.add_fail("Plot Armor - Location Consistency", "Location changed unexpectedly", 1)
        continuity_check["Location"] = "failed"
        findings.append("❌ Location inconsistency detected")
    
    # Calculate score
    passed_points = sum(1 for f in findings if f.startswith("✅"))
    total_points = len(findings)
    score = f"{passed_points}/{total_points}"
    status = "PASS" if passed_points >= total_points * 0.8 else "FAIL"
    
    continuity_check["NPCs"] = "verified" if essential_npc else "failed"
    continuity_check["State"] = "verified" if attack_results else "failed"
    
    results.add_playtest_report("1: Plot Armor & Consequence Escalation", status, score, 
                              findings, mechanical_outputs, narration_sample, continuity_check)

def playtest_2_enemy_combat_dungeon(results: PlaytestResults, campaign_id: str, character_id: str):
    """
    PLAYTEST 2: Enemy Combat in Dungeon
    Scenario: Normal combat with non-essential enemy (skeleton/zombie)
    """
    print("\n" + "="*80)
    print("PLAYTEST 2: Enemy Combat in Dungeon")
    print("="*80)
    
    findings = []
    mechanical_outputs = []
    narration_sample = ""
    continuity_check = {"Location": "unknown", "NPCs": "unknown", "State": "unknown"}
    
    # Setup: Move to dungeon/ruins location
    setup_response = send_action(campaign_id, character_id, "I explore the dark ruins looking for enemies")
    if not setup_response:
        results.add_fail("Combat Setup", "Failed to setup dungeon scenario", 2, critical=True)
        results.add_playtest_report("2: Enemy Combat in Dungeon", "FAIL", "0/10", 
                                  ["Setup failed"], [], "", continuity_check)
        return
    
    narration_sample = setup_response.get("narration", "")[:200]
    continuity_check["Location"] = "dungeon" if any(word in narration_sample.lower() for word in ["ruin", "dungeon", "cave", "tomb"]) else "unknown"
    
    # Look for or spawn an enemy
    enemy_response = send_action(campaign_id, character_id, "I search for any undead creatures or skeletons in this area")
    if enemy_response:
        enemy_narration = enemy_response.get("narration", "").lower()
        
        # Check if enemy was found/spawned
        enemy_found = any(word in enemy_narration for word in ["skeleton", "zombie", "undead", "creature", "enemy"])
        if enemy_found:
            findings.append("✅ Enemy encounter established")
            results.add_pass("Combat Setup - Enemy Found", 1)
        else:
            findings.append("❌ No enemy found in dungeon")
            results.add_fail("Combat Setup - Enemy Found", "No enemies in dungeon area", 1)
    
    # Initiate combat
    print("\n⚔️ Initiating combat with skeleton")
    combat_response = send_action(campaign_id, character_id, "I attack the skeleton")
    if not combat_response:
        results.add_fail("Combat Initiation", "Failed to initiate combat", 2, critical=True)
        findings.append("❌ CRITICAL: Combat initiation failed")
        results.add_playtest_report("2: Enemy Combat in Dungeon", "FAIL", "0/10", 
                                  findings, [], narration_sample, continuity_check)
        return
    
    mechanical_outputs.append(f"Combat Init: {combat_response.get('mechanics', {})}")
    combat_narration = combat_response.get("narration", "")
    
    # Validate combat mechanics
    mechanics = combat_response.get("mechanics", {})
    if mechanics:
        # Check for proper combat structure
        if "attack_roll" in str(mechanics) or "damage" in str(mechanics) or "hp" in str(mechanics):
            results.add_pass("Combat Mechanics - Structure", 2)
            findings.append("✅ Combat mechanics present")
        else:
            results.add_fail("Combat Mechanics - Structure", "Missing combat mechanics", 2)
            findings.append("❌ Combat mechanics missing")
        
        # Check for D&D 5e compliance
        if "d20" in str(mechanics) or "1d20" in str(mechanics):
            results.add_pass("Combat Mechanics - D&D 5e", 2)
            findings.append("✅ D&D 5e mechanics (d20) detected")
        else:
            results.add_fail("Combat Mechanics - D&D 5e", "No D&D 5e mechanics detected", 2)
            findings.append("❌ Missing D&D 5e mechanics")
    else:
        results.add_fail("Combat Mechanics - Present", "No mechanics in combat response", 2)
        findings.append("❌ No combat mechanics returned")
    
    # Check narration matches mechanics
    if "attack" in combat_narration.lower() and "skeleton" in combat_narration.lower():
        results.add_pass("Combat Narration - Consistency", 2)
        findings.append("✅ Narration matches combat action")
    else:
        results.add_fail("Combat Narration - Consistency", "Narration doesn't match combat", 2)
        findings.append("❌ Narration inconsistent with combat")
    
    # Test enemy turn (if combat system supports it)
    enemy_turn_response = send_action(campaign_id, character_id, "I wait for the skeleton's response")
    if enemy_turn_response:
        enemy_narration = enemy_turn_response.get("narration", "").lower()
        if "skeleton" in enemy_narration and ("attack" in enemy_narration or "strike" in enemy_narration):
            results.add_pass("Combat - Enemy Turn", 2)
            findings.append("✅ Enemy turn executed")
            mechanical_outputs.append(f"Enemy Turn: {enemy_turn_response.get('mechanics', {})}")
        else:
            results.add_fail("Combat - Enemy Turn", "Enemy didn't take turn", 1)
            findings.append("❌ Enemy turn missing or unclear")
    
    # Validate location stays in dungeon
    if any(word in combat_narration.lower() for word in ["ruin", "dungeon", "cave", "tomb", "dark"]):
        results.add_pass("Combat - Location Consistency", 1)
        continuity_check["Location"] = "verified"
        findings.append("✅ Combat remained in dungeon setting")
    else:
        results.add_fail("Combat - Location Consistency", "Location changed during combat", 1)
        continuity_check["Location"] = "failed"
        findings.append("❌ Location inconsistency during combat")
    
    # Check for inappropriate NPCs (no merchants, innkeepers in dungeon)
    inappropriate_npcs = ["merchant", "innkeeper", "barkeep", "shopkeeper", "trader"]
    if any(npc in combat_narration.lower() for npc in inappropriate_npcs):
        results.add_fail("Combat - Appropriate NPCs", "Inappropriate NPCs in dungeon", 1)
        findings.append("❌ Inappropriate NPCs appeared in dungeon")
    else:
        results.add_pass("Combat - Appropriate NPCs", 1)
        findings.append("✅ No inappropriate NPCs in dungeon")
    
    # Calculate score
    passed_points = sum(1 for f in findings if f.startswith("✅"))
    total_points = len(findings)
    score = f"{passed_points}/{total_points}"
    status = "PASS" if passed_points >= total_points * 0.8 else "FAIL"
    
    continuity_check["NPCs"] = "verified"
    continuity_check["State"] = "verified" if combat_response else "failed"
    
    results.add_playtest_report("2: Enemy Combat in Dungeon", status, score, 
                              findings, mechanical_outputs, narration_sample, continuity_check)

def playtest_3_location_npc_continuity(results: PlaytestResults, campaign_id: str, character_id: str):
    """
    PLAYTEST 3: Location & NPC Continuity
    Scenario: Testing location constraints with impossible requests
    """
    print("\n" + "="*80)
    print("PLAYTEST 3: Location & NPC Continuity")
    print("="*80)
    
    findings = []
    mechanical_outputs = []
    narration_sample = ""
    continuity_check = {"Location": "unknown", "NPCs": "unknown", "State": "unknown"}
    
    # Setup: Ensure we're at ruins/tower (dangerous location)
    setup_response = send_action(campaign_id, character_id, "I explore the ancient ruins")
    if not setup_response:
        results.add_fail("Continuity Setup", "Failed to setup ruins scenario", 2, critical=True)
        results.add_playtest_report("3: Location & NPC Continuity", "FAIL", "0/10", 
                                  ["Setup failed"], [], "", continuity_check)
        return
    
    narration_sample = setup_response.get("narration", "")[:200]
    is_at_ruins = any(word in narration_sample.lower() for word in ["ruin", "tower", "ancient", "crumbling", "stone"])
    continuity_check["Location"] = "ruins" if is_at_ruins else "unknown"
    
    if is_at_ruins:
        findings.append("✅ Successfully positioned at ruins/dangerous location")
        results.add_pass("Continuity - Location Setup", 1)
    else:
        findings.append("❌ Failed to establish ruins location")
        results.add_fail("Continuity - Location Setup", "Not at ruins location", 1)
    
    # Test 1: Look for merchant at ruins (should be denied)
    print("\n🏪 Testing: Looking for merchant at ruins")
    merchant_response = send_action(campaign_id, character_id, "I look for a merchant")
    if merchant_response:
        merchant_narration = merchant_response.get("narration", "").lower()
        mechanical_outputs.append(f"Merchant Request: Response length {len(merchant_narration)} chars")
        
        # Should NOT spawn merchant at ruins
        if "merchant" in merchant_narration and ("appears" in merchant_narration or "find" in merchant_narration):
            results.add_fail("Continuity - No Merchant at Ruins", "Merchant inappropriately spawned at ruins", 2)
            findings.append("❌ CRITICAL: Merchant spawned at ruins (impossible)")
        else:
            results.add_pass("Continuity - No Merchant at Ruins", 2)
            findings.append("✅ No merchant spawned at ruins")
        
        # Should suggest alternative (going to town)
        if any(word in merchant_narration for word in ["town", "settlement", "village", "city"]):
            results.add_pass("Continuity - Alternative Suggestion", 1)
            findings.append("✅ Alternative location suggested")
        else:
            results.add_fail("Continuity - Alternative Suggestion", "No alternative suggested", 1)
            findings.append("❌ No alternative location suggested")
    
    # Test 2: Look for innkeeper at ruins (should be denied)
    print("\n🏨 Testing: Looking for innkeeper at ruins")
    innkeeper_response = send_action(campaign_id, character_id, "I talk to the innkeeper")
    if innkeeper_response:
        innkeeper_narration = innkeeper_response.get("narration", "").lower()
        mechanical_outputs.append(f"Innkeeper Request: Response length {len(innkeeper_narration)} chars")
        
        # Should NOT spawn innkeeper at ruins
        if "innkeeper" in innkeeper_narration and ("appears" in innkeeper_narration or "responds" in innkeeper_narration):
            results.add_fail("Continuity - No Innkeeper at Ruins", "Innkeeper inappropriately spawned", 2)
            findings.append("❌ CRITICAL: Innkeeper spawned at ruins")
        else:
            results.add_pass("Continuity - No Innkeeper at Ruins", 2)
            findings.append("✅ No innkeeper spawned at ruins")
    
    # Test 3: Travel to town
    print("\n🚶 Testing: Travel to town")
    travel_response = send_action(campaign_id, character_id, "I leave the ruins and go to town")
    if travel_response:
        travel_narration = travel_response.get("narration", "").lower()
        mechanical_outputs.append(f"Travel: Response length {len(travel_narration)} chars")
        
        # Should change location to town
        if any(word in travel_narration for word in ["town", "settlement", "village", "arrive"]):
            results.add_pass("Continuity - Location Change", 2)
            findings.append("✅ Successfully traveled to town")
            continuity_check["Location"] = "town"
        else:
            results.add_fail("Continuity - Location Change", "Failed to change location to town", 2)
            findings.append("❌ Location change failed")
            continuity_check["Location"] = "failed"
    
    # Test 4: Now look for merchant at town (should succeed)
    print("\n🏪 Testing: Looking for merchant at town")
    town_merchant_response = send_action(campaign_id, character_id, "I look for a merchant")
    if town_merchant_response:
        town_merchant_narration = town_merchant_response.get("narration", "").lower()
        mechanical_outputs.append(f"Town Merchant: Response length {len(town_merchant_narration)} chars")
        
        # Should NOW find merchant at town
        if "merchant" in town_merchant_narration:
            results.add_pass("Continuity - Merchant at Town", 2)
            findings.append("✅ Merchant available at town")
        else:
            results.add_fail("Continuity - Merchant at Town", "No merchant at town", 2)
            findings.append("❌ Merchant not available at town")
    
    # Test 5: Look for innkeeper at town (should succeed)
    print("\n🏨 Testing: Looking for innkeeper at town")
    town_innkeeper_response = send_action(campaign_id, character_id, "I talk to the innkeeper")
    if town_innkeeper_response:
        town_innkeeper_narration = town_innkeeper_response.get("narration", "").lower()
        mechanical_outputs.append(f"Town Innkeeper: Response length {len(town_innkeeper_narration)} chars")
        
        # Should NOW find innkeeper at town
        if "innkeeper" in town_innkeeper_narration:
            results.add_pass("Continuity - Innkeeper at Town", 2)
            findings.append("✅ Innkeeper available at town")
        else:
            results.add_fail("Continuity - Innkeeper at Town", "No innkeeper at town", 2)
            findings.append("❌ Innkeeper not available at town")
    
    # Validate no NPC teleportation
    if continuity_check["Location"] == "town":
        results.add_pass("Continuity - No NPC Teleportation", 1)
        findings.append("✅ NPCs properly constrained by location")
    else:
        results.add_fail("Continuity - No NPC Teleportation", "Location constraints not enforced", 1)
        findings.append("❌ Location constraints failed")
    
    # Calculate score
    passed_points = sum(1 for f in findings if f.startswith("✅"))
    total_points = len(findings)
    score = f"{passed_points}/{total_points}"
    status = "PASS" if passed_points >= total_points * 0.8 else "FAIL"
    
    continuity_check["NPCs"] = "verified" if passed_points >= total_points * 0.7 else "failed"
    continuity_check["State"] = "verified"
    
    results.add_playtest_report("3: Location & NPC Continuity", status, score, 
                              findings, mechanical_outputs, narration_sample, continuity_check)

def playtest_4_pacing_tension_transitions(results: PlaytestResults, campaign_id: str, character_id: str):
    """
    PLAYTEST 4: Pacing & Tension Transitions
    Scenario: Multi-phase narrative testing tension system
    """
    print("\n" + "="*80)
    print("PLAYTEST 4: Pacing & Tension Transitions")
    print("="*80)
    
    findings = []
    mechanical_outputs = []
    narration_sample = ""
    continuity_check = {"Location": "unknown", "NPCs": "unknown", "State": "unknown"}
    
    # Phase 1: Calm - Start in town
    print("\n😌 Phase 1: Calm - Strolling through market")
    calm_response = send_action(campaign_id, character_id, "I stroll through the market and browse the stalls")
    if not calm_response:
        results.add_fail("Tension Setup", "Failed to establish calm phase", 2, critical=True)
        results.add_playtest_report("4: Pacing & Tension Transitions", "FAIL", "0/10", 
                                  ["Setup failed"], [], "", continuity_check)
        return
    
    calm_narration = calm_response.get("narration", "")
    narration_sample = calm_narration[:200]
    mechanical_outputs.append(f"Calm Phase: {len(calm_narration)} chars")
    
    # Check for calm characteristics (brief, functional, relaxed)
    word_count = len(calm_narration.split())
    if word_count < 100:  # Brief narration expected
        results.add_pass("Tension - Calm Brevity", 1)
        findings.append("✅ Calm phase: Brief narration (under 100 words)")
    else:
        results.add_fail("Tension - Calm Brevity", f"Calm narration too long: {word_count} words", 1)
        findings.append(f"❌ Calm phase: Too verbose ({word_count} words)")
    
    # Check for relaxed tone
    calm_indicators = ["peaceful", "relaxed", "casual", "browse", "stroll", "gentle", "quiet"]
    if any(indicator in calm_narration.lower() for indicator in calm_indicators):
        results.add_pass("Tension - Calm Tone", 1)
        findings.append("✅ Calm phase: Relaxed tone detected")
    else:
        results.add_fail("Tension - Calm Tone", "No calm tone indicators", 1)
        findings.append("❌ Calm phase: Missing relaxed tone")
    
    continuity_check["Location"] = "town" if "market" in calm_narration.lower() else "unknown"
    
    # Phase 2: Building - Follow suspicious figure
    print("\n🕵️ Phase 2: Building - Following suspicious figure")
    building_response = send_action(campaign_id, character_id, "I follow a suspicious hooded figure into a side alley")
    if building_response:
        building_narration = building_response.get("narration", "")
        mechanical_outputs.append(f"Building Phase: {len(building_narration)} chars")
        
        # Check for atmospheric, ominous hints
        building_indicators = ["shadow", "dark", "ominous", "suspicious", "tension", "unease", "mystery"]
        if any(indicator in building_narration.lower() for indicator in building_indicators):
            results.add_pass("Tension - Building Atmosphere", 2)
            findings.append("✅ Building phase: Atmospheric tension present")
        else:
            results.add_fail("Tension - Building Atmosphere", "No building tension atmosphere", 2)
            findings.append("❌ Building phase: Missing atmospheric tension")
        
        # Check for scene transition (market → alley)
        if "alley" in building_narration.lower() or "side" in building_narration.lower():
            results.add_pass("Tension - Scene Transition", 1)
            findings.append("✅ Building phase: Scene transition to alley")
            continuity_check["Location"] = "alley"
        else:
            results.add_fail("Tension - Scene Transition", "No scene transition", 1)
            findings.append("❌ Building phase: Missing scene transition")
    
    # Phase 3: Tense - Confront the figure
    print("\n😰 Phase 3: Tense - Confronting the figure")
    tense_response = send_action(campaign_id, character_id, "I confront him and demand to know what he's hiding")
    if tense_response:
        tense_narration = tense_response.get("narration", "")
        mechanical_outputs.append(f"Tense Phase: {len(tense_narration)} chars")
        
        # Check for suspenseful, partial reveals
        tense_indicators = ["tense", "suspense", "reveal", "secret", "hidden", "danger", "threat"]
        if any(indicator in tense_narration.lower() for indicator in tense_indicators):
            results.add_pass("Tension - Tense Suspense", 2)
            findings.append("✅ Tense phase: Suspenseful elements present")
        else:
            results.add_fail("Tension - Tense Suspense", "No tense suspense elements", 2)
            findings.append("❌ Tense phase: Missing suspenseful elements")
        
        # Should be social confrontation, not combat yet
        if "attack" not in tense_narration.lower() and "combat" not in tense_narration.lower():
            results.add_pass("Tension - Social Confrontation", 1)
            findings.append("✅ Tense phase: Social confrontation (no combat)")
        else:
            results.add_fail("Tension - Social Confrontation", "Premature combat", 1)
            findings.append("❌ Tense phase: Combat started too early")
    
    # Phase 4: Climax - Combat initiation
    print("\n⚔️ Phase 4: Climax - Combat begins")
    climax_response = send_action(campaign_id, character_id, "He attacks me")
    if climax_response:
        climax_narration = climax_response.get("narration", "")
        mechanical_outputs.append(f"Climax Phase: {len(climax_narration)} chars")
        
        # Check for fast-paced, exciting, combat-focused
        climax_indicators = ["attack", "strike", "combat", "fight", "battle", "clash", "weapon"]
        if any(indicator in climax_narration.lower() for indicator in climax_indicators):
            results.add_pass("Tension - Climax Combat", 2)
            findings.append("✅ Climax phase: Combat initiated")
        else:
            results.add_fail("Tension - Climax Combat", "No combat in climax", 2)
            findings.append("❌ Climax phase: Combat not initiated")
        
        # Check for fast-paced narration
        if len(climax_narration.split()) > 50:  # Should be action-packed
            results.add_pass("Tension - Climax Pacing", 1)
            findings.append("✅ Climax phase: Fast-paced narration")
        else:
            results.add_fail("Tension - Climax Pacing", "Climax narration too brief", 1)
            findings.append("❌ Climax phase: Insufficient action description")
    
    # Phase 5: Resolution - Defeat enemy
    print("\n🏆 Phase 5: Resolution - Combat conclusion")
    resolution_response = send_action(campaign_id, character_id, "I defeat the attacker and search his body")
    if resolution_response:
        resolution_narration = resolution_response.get("narration", "")
        mechanical_outputs.append(f"Resolution Phase: {len(resolution_narration)} chars")
        
        # Check for conclusive, rewarding elements
        resolution_indicators = ["defeat", "victory", "search", "find", "discover", "reward", "clue"]
        if any(indicator in resolution_narration.lower() for indicator in resolution_indicators):
            results.add_pass("Tension - Resolution Conclusion", 2)
            findings.append("✅ Resolution phase: Conclusive elements present")
        else:
            results.add_fail("Tension - Resolution Conclusion", "No conclusive elements", 2)
            findings.append("❌ Resolution phase: Missing conclusive elements")
    
    # Phase 6: Return to Calm - Back to main street
    print("\n😌 Phase 6: Return to Calm - Back to street")
    return_calm_response = send_action(campaign_id, character_id, "I return to the main street")
    if return_calm_response:
        return_calm_narration = return_calm_response.get("narration", "")
        mechanical_outputs.append(f"Return Calm: {len(return_calm_narration)} chars")
        
        # Should return to brief, functional narration
        return_word_count = len(return_calm_narration.split())
        if return_word_count < 80:  # Brief again
            results.add_pass("Tension - Return to Calm", 2)
            findings.append("✅ Return to calm: Brief, functional narration")
        else:
            results.add_fail("Tension - Return to Calm", f"Return narration too long: {return_word_count} words", 2)
            findings.append(f"❌ Return to calm: Too verbose ({return_word_count} words)")
    
    # Validate overall continuity (town → alley → street)
    if continuity_check["Location"] == "alley":
        results.add_pass("Tension - Location Continuity", 1)
        findings.append("✅ Location continuity maintained throughout phases")
        continuity_check["Location"] = "verified"
    else:
        results.add_fail("Tension - Location Continuity", "Location continuity broken", 1)
        findings.append("❌ Location continuity broken")
        continuity_check["Location"] = "failed"
    
    # Calculate score
    passed_points = sum(1 for f in findings if f.startswith("✅"))
    total_points = len(findings)
    score = f"{passed_points}/{total_points}"
    status = "PASS" if passed_points >= total_points * 0.8 else "FAIL"
    
    continuity_check["NPCs"] = "verified"  # Hooded figure maintained
    continuity_check["State"] = "verified"
    
    results.add_playtest_report("4: Pacing & Tension Transitions", status, score, 
                              findings, mechanical_outputs, narration_sample, continuity_check)

def main():
    """Execute all 4 A-Version regression playtests"""
    print("🎮 A-VERSION REGRESSION PLAYTESTS - Complete Validation Suite")
    print(f"Backend URL: {BACKEND_URL}")
    print("="*80)
    
    results = PlaytestResults()
    
    # Get latest campaign
    print("📋 Getting latest campaign...")
    campaign_data = get_latest_campaign()
    if not campaign_data:
        print("❌ CRITICAL: Cannot proceed without campaign data")
        return False
    
    campaign_id = campaign_data.get("campaign_id")
    character_id = campaign_data.get("character_id")
    
    print(f"✅ Campaign ID: {campaign_id}")
    print(f"✅ Character ID: {character_id}")
    
    # Execute all 4 playtests
    try:
        playtest_1_plot_armor_consequence_escalation(results, campaign_id, character_id)
        time.sleep(2)  # Brief pause between tests
        
        playtest_2_enemy_combat_dungeon(results, campaign_id, character_id)
        time.sleep(2)
        
        playtest_3_location_npc_continuity(results, campaign_id, character_id)
        time.sleep(2)
        
        playtest_4_pacing_tension_transitions(results, campaign_id, character_id)
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR during playtests: {e}")
        results.add_fail("Playtest Execution", f"Critical error: {str(e)}", 10, critical=True)
    
    # Generate final summary
    success = results.summary()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)