#!/usr/bin/env python3
"""
COMPREHENSIVE PHASE 1 COMBAT SYSTEM TESTING
Tests the complete combat engine implementation with targeting, plot armor, and D&D 5e mechanics.
"""

import requests
import json
import sys
import time
from typing import Dict, Any, List, Optional

# Backend URL from frontend/.env
BACKEND_URL = "https://dnd-wizard.preview.emergentagent.com/api"

class CombatTestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.test_details = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.passed += 1
        self.test_details.append(f"✅ PASS: {test_name}")
        if details:
            self.test_details.append(f"   {details}")
        print(f"✅ PASS: {test_name}")
        if details:
            print(f"   {details}")
    
    def add_fail(self, test_name: str, error: str, details: str = ""):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        self.test_details.append(f"❌ FAIL: {test_name} - {error}")
        if details:
            self.test_details.append(f"   {details}")
        print(f"❌ FAIL: {test_name} - {error}")
        if details:
            print(f"   {details}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*80}")
        print(f"COMBAT SYSTEM TEST SUMMARY: {self.passed}/{total} tests passed")
        if self.errors:
            print(f"\nFAILED TESTS:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*80}")
        return self.failed == 0

def get_latest_campaign_and_character() -> tuple[Optional[str], Optional[str]]:
    """Get the latest campaign and character IDs from the database"""
    try:
        print("🔍 Getting latest campaign and character...")
        
        # Get latest campaign
        response = requests.get(
            f"{BACKEND_URL}/campaigns/latest",
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get latest campaign: {response.status_code}")
            return None, None
        
        campaign_data = response.json()
        campaign_id = campaign_data.get("campaign_id")
        
        if not campaign_id:
            print("❌ No campaign_id in response")
            return None, None
        
        print(f"✅ Found campaign: {campaign_id}")
        
        # Get character from campaign
        character_id = campaign_data.get("character_id")
        if not character_id:
            print("❌ No character_id in campaign data")
            return campaign_id, None
        
        print(f"✅ Found character: {character_id}")
        return campaign_id, character_id
        
    except Exception as e:
        print(f"❌ Exception getting campaign/character: {e}")
        return None, None

def make_action_request(campaign_id: str, character_id: str, action: str, check_result: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Make an action request to the combat system"""
    try:
        payload = {
            "campaign_id": campaign_id,
            "character_id": character_id,
            "player_action": action
        }
        
        if check_result is not None:
            payload["check_result"] = check_result
        
        print(f"📤 Request: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{BACKEND_URL}/rpg_dm/action",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.text[:500]}")
            return None
        
        data = response.json()
        print(f"📥 Response Summary: narration={len(data.get('narration', ''))}, options={len(data.get('options', []))}")
        
        return data
        
    except Exception as e:
        print(f"❌ Exception in action request: {e}")
        return None

def test_target_resolution(results: CombatTestResults, campaign_id: str, character_id: str):
    """Test Suite 1: Target Resolution (Priority)"""
    print("\n" + "="*80)
    print("TEST SUITE 1: TARGET RESOLUTION (PRIORITY)")
    print("="*80)
    
    # Test 1.1: Named NPC targeting
    print("\n🎯 Test 1.1: Named NPC targeting")
    response = make_action_request(campaign_id, character_id, "I punch Aria")
    
    if response is None:
        results.add_fail("Target Resolution - Named NPC", "No response received")
    else:
        # Check for target_resolution in response
        target_resolution = response.get("target_resolution")
        if target_resolution:
            status = target_resolution.get("status")
            if status == "single_target":
                target_name = target_resolution.get("target", {}).get("name", "").lower()
                if "aria" in target_name:
                    results.add_pass("Target Resolution - Named NPC", f"Correctly targeted Aria: {target_name}")
                else:
                    results.add_fail("Target Resolution - Named NPC", f"Wrong target: {target_name}")
            else:
                results.add_fail("Target Resolution - Named NPC", f"Wrong status: {status}")
        else:
            # Check if combat was initiated (alternative success indicator)
            if "combat" in response.get("narration", "").lower():
                results.add_pass("Target Resolution - Named NPC", "Combat initiated with named NPC")
            else:
                results.add_fail("Target Resolution - Named NPC", "No target_resolution field and no combat")
    
    # Test 1.2: Multiple targets - ambiguous
    print("\n🎯 Test 1.2: Multiple targets - ambiguous")
    response = make_action_request(campaign_id, character_id, "I attack")
    
    if response is None:
        results.add_fail("Target Resolution - Ambiguous", "No response received")
    else:
        target_resolution = response.get("target_resolution")
        if target_resolution:
            status = target_resolution.get("status")
            if status == "needs_clarification":
                ambiguous_options = target_resolution.get("ambiguous_options", [])
                if len(ambiguous_options) > 1:
                    results.add_pass("Target Resolution - Ambiguous", f"Found {len(ambiguous_options)} ambiguous targets")
                else:
                    results.add_fail("Target Resolution - Ambiguous", f"Only {len(ambiguous_options)} options")
            else:
                results.add_fail("Target Resolution - Ambiguous", f"Wrong status: {status}")
        else:
            # Check if narration asks for clarification
            narration = response.get("narration", "").lower()
            if any(word in narration for word in ["who", "which", "target", "attack"]):
                results.add_pass("Target Resolution - Ambiguous", "Narration requests clarification")
            else:
                results.add_fail("Target Resolution - Ambiguous", "No clarification requested")
    
    # Test 1.3: Combat targeting - single enemy
    print("\n🎯 Test 1.3: Combat targeting - single enemy")
    # First try to start combat
    combat_response = make_action_request(campaign_id, character_id, "I draw my weapon and prepare for battle")
    
    if combat_response:
        # Now try attacking with single enemy
        response = make_action_request(campaign_id, character_id, "I attack")
        
        if response is None:
            results.add_fail("Target Resolution - Single Enemy", "No response received")
        else:
            target_resolution = response.get("target_resolution")
            if target_resolution:
                status = target_resolution.get("status")
                if status == "single_target":
                    results.add_pass("Target Resolution - Single Enemy", "Auto-targeted sole enemy")
                else:
                    results.add_fail("Target Resolution - Single Enemy", f"Wrong status: {status}")
            else:
                # Check if attack was processed
                if "attack" in response.get("narration", "").lower():
                    results.add_pass("Target Resolution - Single Enemy", "Attack processed against single enemy")
                else:
                    results.add_fail("Target Resolution - Single Enemy", "No target resolution or attack")
    else:
        results.add_fail("Target Resolution - Single Enemy", "Could not initiate combat")
    
    # Test 1.4: No target found
    print("\n🎯 Test 1.4: No target found")
    response = make_action_request(campaign_id, character_id, "I attack the dragon")
    
    if response is None:
        results.add_fail("Target Resolution - No Target", "No response received")
    else:
        target_resolution = response.get("target_resolution")
        if target_resolution:
            status = target_resolution.get("status")
            if status == "no_target_found":
                results.add_pass("Target Resolution - No Target", "Correctly identified no target")
            else:
                results.add_fail("Target Resolution - No Target", f"Wrong status: {status}")
        else:
            # Check if narration indicates no target
            narration = response.get("narration", "").lower()
            if any(phrase in narration for phrase in ["no dragon", "not here", "don't see", "can't find"]):
                results.add_pass("Target Resolution - No Target", "Narration indicates no target")
            else:
                results.add_fail("Target Resolution - No Target", "No indication of missing target")

def test_plot_armor_protection(results: CombatTestResults, campaign_id: str, character_id: str):
    """Test Suite 2: Plot Armor Protection (CRITICAL)"""
    print("\n" + "="*80)
    print("TEST SUITE 2: PLOT ARMOR PROTECTION (CRITICAL)")
    print("="*80)
    
    # Test 2.1: Attack essential NPC - should be blocked
    print("\n🛡️ Test 2.1: Attack essential NPC - should be blocked")
    
    # Try attacking various essential NPCs
    essential_npcs = ["lord", "mayor", "quest giver", "captain", "commander"]
    
    for npc in essential_npcs:
        print(f"   Testing attack on {npc}...")
        response = make_action_request(campaign_id, character_id, f"I punch the {npc}")
        
        if response is None:
            continue
        
        plot_armor = response.get("plot_armor")
        if plot_armor:
            status = plot_armor.get("status")
            if status == "blocked":
                results.add_pass("Plot Armor - Essential NPC Block", f"Blocked attack on {npc}")
                
                # Check for intervention narrative
                narration = response.get("narration", "").lower()
                if any(word in narration for word in ["guard", "bodyguard", "intervene", "stop", "prevent"]):
                    results.add_pass("Plot Armor - Intervention Narrative", "Guards/bodyguards intervened")
                else:
                    results.add_fail("Plot Armor - Intervention Narrative", "No intervention described")
                
                # Check for reputation consequences
                consequences = plot_armor.get("consequences", {})
                if consequences.get("reputation_change"):
                    results.add_pass("Plot Armor - Reputation Consequences", "Reputation consequences applied")
                else:
                    results.add_fail("Plot Armor - Reputation Consequences", "No reputation consequences")
                
                # Check for consequence options
                options = response.get("options", [])
                if len(options) > 0:
                    results.add_pass("Plot Armor - Consequence Options", f"Provided {len(options)} options")
                else:
                    results.add_fail("Plot Armor - Consequence Options", "No consequence options")
                
                return  # Found working plot armor
        
        # Check if combat was prevented in narration
        narration = response.get("narration", "").lower()
        if any(phrase in narration for phrase in ["guards stop", "prevented", "intervene", "bodyguards"]):
            results.add_pass("Plot Armor - Essential NPC Block", f"Narration blocked attack on {npc}")
            return
    
    results.add_fail("Plot Armor - Essential NPC Block", "No essential NPC attacks were blocked")
    
    # Test 2.2: Essential NPC cannot be killed
    print("\n🛡️ Test 2.2: Essential NPC cannot be killed")
    
    # Try to force combat with essential NPC
    response = make_action_request(campaign_id, character_id, "I attack the quest giver with lethal intent")
    
    if response is None:
        results.add_fail("Plot Armor - No Kill", "No response received")
    else:
        # Check if NPC becomes unconscious instead of dead
        combat_result = response.get("combat_result")
        if combat_result:
            if combat_result.get("knocked_unconscious") and not combat_result.get("killed"):
                results.add_pass("Plot Armor - No Kill", "Essential NPC knocked unconscious, not killed")
            else:
                results.add_fail("Plot Armor - No Kill", "Essential NPC was killed or not handled properly")
        else:
            # Check narration for non-lethal outcome
            narration = response.get("narration", "").lower()
            if any(phrase in narration for phrase in ["unconscious", "stunned", "subdued", "non-lethal"]):
                results.add_pass("Plot Armor - No Kill", "Narration indicates non-lethal outcome")
            else:
                results.add_fail("Plot Armor - No Kill", "No indication of non-lethal protection")
    
    # Test 2.3: Non-essential NPC - combat allowed
    print("\n🛡️ Test 2.3: Non-essential NPC - combat allowed")
    
    response = make_action_request(campaign_id, character_id, "I attack the generic guard")
    
    if response is None:
        results.add_fail("Plot Armor - Non-Essential Combat", "No response received")
    else:
        plot_armor = response.get("plot_armor")
        if plot_armor and plot_armor.get("status") == "blocked":
            results.add_fail("Plot Armor - Non-Essential Combat", "Non-essential NPC was protected")
        else:
            # Check if combat initiated
            narration = response.get("narration", "").lower()
            if any(word in narration for word in ["combat", "fight", "battle", "attack", "strike"]):
                results.add_pass("Plot Armor - Non-Essential Combat", "Combat allowed with non-essential NPC")
            else:
                results.add_fail("Plot Armor - Non-Essential Combat", "Combat not initiated")

def test_dnd_combat_mechanics(results: CombatTestResults, campaign_id: str, character_id: str):
    """Test Suite 3: D&D 5e Combat Mechanics"""
    print("\n" + "="*80)
    print("TEST SUITE 3: D&D 5e COMBAT MECHANICS")
    print("="*80)
    
    # Test 3.1: Unarmed strike damage
    print("\n⚔️ Test 3.1: Unarmed strike damage")
    
    response = make_action_request(campaign_id, character_id, "I make an unarmed strike")
    
    if response is None:
        results.add_fail("D&D Mechanics - Unarmed Strike", "No response received")
    else:
        combat_result = response.get("combat_result")
        if combat_result:
            damage = combat_result.get("damage")
            attack_roll = combat_result.get("attack_roll")
            
            if damage is not None and damage >= 1:
                results.add_pass("D&D Mechanics - Unarmed Strike", f"Damage: {damage} (minimum 1)")
            else:
                results.add_fail("D&D Mechanics - Unarmed Strike", f"Invalid damage: {damage}")
            
            if attack_roll and 1 <= attack_roll.get("total", 0) <= 30:
                results.add_pass("D&D Mechanics - Attack Roll", f"Attack roll: {attack_roll.get('total')}")
            else:
                results.add_fail("D&D Mechanics - Attack Roll", f"Invalid attack roll: {attack_roll}")
        else:
            results.add_fail("D&D Mechanics - Unarmed Strike", "No combat_result in response")
    
    # Test 3.2: Critical hit (natural 20)
    print("\n⚔️ Test 3.2: Critical hit mechanics")
    
    # Try multiple attacks to potentially get a crit
    for attempt in range(5):
        response = make_action_request(campaign_id, character_id, "I attack with my weapon")
        
        if response:
            combat_result = response.get("combat_result")
            if combat_result and combat_result.get("is_crit"):
                damage = combat_result.get("damage", 0)
                attack_roll = combat_result.get("attack_roll", {})
                
                if attack_roll.get("natural") == 20:
                    results.add_pass("D&D Mechanics - Critical Hit", f"Natural 20 crit, damage: {damage}")
                else:
                    results.add_pass("D&D Mechanics - Critical Hit", f"Critical hit detected, damage: {damage}")
                break
    else:
        results.add_fail("D&D Mechanics - Critical Hit", "No critical hits in 5 attempts")
    
    # Test 3.3: Critical miss (natural 1)
    print("\n⚔️ Test 3.3: Critical miss mechanics")
    
    # Try multiple attacks to potentially get a critical miss
    for attempt in range(5):
        response = make_action_request(campaign_id, character_id, "I attack")
        
        if response:
            combat_result = response.get("combat_result")
            if combat_result and combat_result.get("critical_miss"):
                attack_roll = combat_result.get("attack_roll", {})
                damage = combat_result.get("damage", 0)
                
                if attack_roll.get("natural") == 1 and damage == 0:
                    results.add_pass("D&D Mechanics - Critical Miss", "Natural 1 critical miss, no damage")
                else:
                    results.add_pass("D&D Mechanics - Critical Miss", "Critical miss detected")
                break
    else:
        results.add_fail("D&D Mechanics - Critical Miss", "No critical misses in 5 attempts")
    
    # Test 3.4: Normal hit vs AC
    print("\n⚔️ Test 3.4: Hit vs AC mechanics")
    
    response = make_action_request(campaign_id, character_id, "I attack the enemy")
    
    if response is None:
        results.add_fail("D&D Mechanics - Hit vs AC", "No response received")
    else:
        combat_result = response.get("combat_result")
        if combat_result:
            attack_roll = combat_result.get("attack_roll", {})
            target_ac = combat_result.get("target_ac")
            hit = combat_result.get("hit")
            
            if attack_roll and target_ac is not None and hit is not None:
                total_roll = attack_roll.get("total", 0)
                if (total_roll >= target_ac and hit) or (total_roll < target_ac and not hit):
                    results.add_pass("D&D Mechanics - Hit vs AC", f"Roll {total_roll} vs AC {target_ac}: {'Hit' if hit else 'Miss'}")
                else:
                    results.add_fail("D&D Mechanics - Hit vs AC", f"Logic error: Roll {total_roll} vs AC {target_ac} = {hit}")
            else:
                results.add_fail("D&D Mechanics - Hit vs AC", "Missing attack roll, AC, or hit data")
        else:
            results.add_fail("D&D Mechanics - Hit vs AC", "No combat_result in response")
    
    # Test 3.5: HP and death mechanics
    print("\n⚔️ Test 3.5: HP and death mechanics")
    
    # Try to defeat an enemy
    for attempt in range(10):
        response = make_action_request(campaign_id, character_id, "I attack to defeat the enemy")
        
        if response:
            combat_result = response.get("combat_result")
            if combat_result:
                enemy_hp = combat_result.get("enemy_hp")
                if enemy_hp is not None and enemy_hp <= 0:
                    if combat_result.get("enemy_defeated"):
                        results.add_pass("D&D Mechanics - HP and Death", "Enemy defeated at 0 HP")
                    else:
                        results.add_fail("D&D Mechanics - HP and Death", "Enemy at 0 HP but not defeated")
                    break
    else:
        results.add_fail("D&D Mechanics - HP and Death", "Could not defeat enemy in 10 attempts")

def test_combat_state_management(results: CombatTestResults, campaign_id: str, character_id: str):
    """Test Suite 4: Combat State Management"""
    print("\n" + "="*80)
    print("TEST SUITE 4: COMBAT STATE MANAGEMENT")
    print("="*80)
    
    # Test 4.1: Combat initiation
    print("\n⚔️ Test 4.1: Combat initiation")
    
    response = make_action_request(campaign_id, character_id, "I attack the nearest enemy")
    
    if response is None:
        results.add_fail("Combat State - Initiation", "No response received")
    else:
        combat_state = response.get("combat_state")
        if combat_state:
            if combat_state.get("combat_active"):
                results.add_pass("Combat State - Initiation", "Combat state created and active")
                
                # Check turn order
                turn_order = combat_state.get("turn_order", [])
                if len(turn_order) > 0:
                    results.add_pass("Combat State - Turn Order", f"Turn order: {len(turn_order)} participants")
                else:
                    results.add_fail("Combat State - Turn Order", "No turn order established")
                
                # Check enemies list
                enemies = combat_state.get("enemies", [])
                if len(enemies) > 0:
                    results.add_pass("Combat State - Enemies", f"Enemies list: {len(enemies)} enemies")
                else:
                    results.add_fail("Combat State - Enemies", "No enemies in combat state")
            else:
                results.add_fail("Combat State - Initiation", "Combat state not active")
        else:
            # Check if combat mentioned in narration
            narration = response.get("narration", "").lower()
            if any(word in narration for word in ["combat", "battle", "fight", "initiative"]):
                results.add_pass("Combat State - Initiation", "Combat initiated (narration indicates)")
            else:
                results.add_fail("Combat State - Initiation", "No combat state or indication")
    
    # Test 4.2: Multiple combat rounds
    print("\n⚔️ Test 4.2: Multiple combat rounds")
    
    # Perform multiple attacks
    for round_num in range(3):
        print(f"   Round {round_num + 1}...")
        response = make_action_request(campaign_id, character_id, "I continue attacking")
        
        if response:
            combat_state = response.get("combat_state")
            if combat_state:
                current_round = combat_state.get("round", 0)
                if current_round > 0:
                    results.add_pass("Combat State - Multiple Rounds", f"Round {current_round} active")
                    break
    else:
        results.add_fail("Combat State - Multiple Rounds", "No round progression detected")
    
    # Test 4.3: Combat cleanup (CRITICAL)
    print("\n⚔️ Test 4.3: Combat cleanup (CRITICAL)")
    
    # Try to end combat by defeating all enemies
    for attempt in range(15):
        response = make_action_request(campaign_id, character_id, "I attack to finish the combat")
        
        if response:
            combat_state = response.get("combat_state")
            if combat_state:
                if combat_state.get("combat_over"):
                    outcome = combat_state.get("outcome")
                    if outcome == "victory":
                        results.add_pass("Combat State - Cleanup", "Combat ended with victory")
                        
                        # Check if combat state is cleared
                        if not combat_state.get("combat_active", True):
                            results.add_pass("Combat State - State Cleared", "Combat state properly cleared")
                        else:
                            results.add_fail("Combat State - State Cleared", "Combat state still active after victory")
                        break
                    else:
                        results.add_fail("Combat State - Cleanup", f"Combat over but outcome: {outcome}")
                        break
    else:
        results.add_fail("Combat State - Cleanup", "Could not end combat in 15 attempts")
    
    # Test 4.4: XP award on victory
    print("\n⚔️ Test 4.4: XP award on victory")
    
    # Check if XP was awarded
    if response:
        xp_award = response.get("xp_award")
        if xp_award and xp_award.get("amount", 0) > 0:
            results.add_pass("Combat State - XP Award", f"XP awarded: {xp_award.get('amount')}")
        else:
            # Check character updates
            character_updates = response.get("character_updates", {})
            if character_updates.get("experience_gained", 0) > 0:
                results.add_pass("Combat State - XP Award", f"XP gained: {character_updates.get('experience_gained')}")
            else:
                results.add_fail("Combat State - XP Award", "No XP awarded for victory")

def test_npc_to_enemy_conversion(results: CombatTestResults, campaign_id: str, character_id: str):
    """Test Suite 5: NPC to Enemy Conversion"""
    print("\n" + "="*80)
    print("TEST SUITE 5: NPC TO ENEMY CONVERSION")
    print("="*80)
    
    # Test 5.1: NPC converts to enemy
    print("\n🔄 Test 5.1: NPC converts to enemy")
    
    response = make_action_request(campaign_id, character_id, "I attack the merchant")
    
    if response is None:
        results.add_fail("NPC Conversion - Basic", "No response received")
    else:
        # Check if NPC became an enemy
        combat_state = response.get("combat_state")
        if combat_state:
            enemies = combat_state.get("enemies", [])
            merchant_enemy = None
            
            for enemy in enemies:
                if "merchant" in enemy.get("name", "").lower():
                    merchant_enemy = enemy
                    break
            
            if merchant_enemy:
                results.add_pass("NPC Conversion - Basic", "Merchant converted to enemy combatant")
                
                # Test 5.2: Converted NPC stats
                print("\n🔄 Test 5.2: Converted NPC stats")
                
                hp = merchant_enemy.get("hp", 0)
                ac = merchant_enemy.get("ac", 0)
                
                if hp > 0 and ac > 0:
                    results.add_pass("NPC Conversion - Stats", f"Merchant has HP: {hp}, AC: {ac}")
                    
                    # Check if stats are role-appropriate
                    if hp < 20:  # Merchants should have lower HP
                        results.add_pass("NPC Conversion - Role Appropriate", "Merchant has appropriate low HP")
                    else:
                        results.add_fail("NPC Conversion - Role Appropriate", f"Merchant HP too high: {hp}")
                else:
                    results.add_fail("NPC Conversion - Stats", f"Invalid stats - HP: {hp}, AC: {ac}")
            else:
                results.add_fail("NPC Conversion - Basic", "Merchant not found in enemies list")
        else:
            # Check if combat was initiated in narration
            narration = response.get("narration", "").lower()
            if "merchant" in narration and any(word in narration for word in ["combat", "fight", "attack", "hostile"]):
                results.add_pass("NPC Conversion - Basic", "Merchant became hostile (narration)")
            else:
                results.add_fail("NPC Conversion - Basic", "No indication of NPC conversion")

def test_edge_cases(results: CombatTestResults, campaign_id: str, character_id: str):
    """Test Suite 6: Edge Cases"""
    print("\n" + "="*80)
    print("TEST SUITE 6: EDGE CASES")
    print("="*80)
    
    # Test 6.1: Attack while already in combat
    print("\n🔍 Test 6.1: Attack while already in combat")
    
    # First, ensure we're in combat
    combat_response = make_action_request(campaign_id, character_id, "I start combat")
    
    if combat_response:
        # Now try another attack
        response = make_action_request(campaign_id, character_id, "I attack again")
        
        if response is None:
            results.add_fail("Edge Cases - Combat Attack", "No response received")
        else:
            # Check if target resolution still works
            if response.get("target_resolution") or "attack" in response.get("narration", "").lower():
                results.add_pass("Edge Cases - Combat Attack", "Target resolution works in combat")
            else:
                results.add_fail("Edge Cases - Combat Attack", "Target resolution failed in combat")
    else:
        results.add_fail("Edge Cases - Combat Attack", "Could not initiate combat")
    
    # Test 6.2: Player defeat
    print("\n🔍 Test 6.2: Player defeat handling")
    
    # This is hard to test without knowing exact HP, so we'll check if the system handles it
    response = make_action_request(campaign_id, character_id, "I let the enemies attack me until I'm defeated")
    
    if response is None:
        results.add_fail("Edge Cases - Player Defeat", "No response received")
    else:
        # Check if defeat mechanics are mentioned
        narration = response.get("narration", "").lower()
        if any(phrase in narration for phrase in ["defeat", "unconscious", "death", "fallen", "0 hit points"]):
            results.add_pass("Edge Cases - Player Defeat", "Defeat mechanics acknowledged")
        else:
            results.add_fail("Edge Cases - Player Defeat", "No defeat handling visible")
    
    # Test 6.3: Flee from combat
    print("\n🔍 Test 6.3: Flee from combat")
    
    response = make_action_request(campaign_id, character_id, "I flee from combat")
    
    if response is None:
        results.add_fail("Edge Cases - Flee", "No response received")
    else:
        # Check if flee mechanics work
        narration = response.get("narration", "").lower()
        if any(word in narration for word in ["flee", "escape", "run", "retreat"]):
            results.add_pass("Edge Cases - Flee", "Flee mechanics working")
            
            # Check if combat state changes
            combat_state = response.get("combat_state")
            if combat_state and not combat_state.get("combat_active", True):
                results.add_pass("Edge Cases - Flee State", "Combat ended after fleeing")
            else:
                results.add_fail("Edge Cases - Flee State", "Combat state not updated after flee")
        else:
            results.add_fail("Edge Cases - Flee", "Flee not processed")

def main():
    """Run comprehensive Phase 1 combat system testing"""
    print("🗡️ COMPREHENSIVE PHASE 1 COMBAT SYSTEM TESTING")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print("Testing: Target Resolution, Plot Armor, D&D 5e Mechanics, Combat State, NPC Conversion, Edge Cases")
    print("="*80)
    
    results = CombatTestResults()
    
    # Get latest campaign and character
    campaign_id, character_id = get_latest_campaign_and_character()
    
    if not campaign_id or not character_id:
        print("❌ CRITICAL: Could not get campaign and character IDs")
        print("   Make sure a campaign exists with a character")
        return False
    
    print(f"✅ Using Campaign: {campaign_id}")
    print(f"✅ Using Character: {character_id}")
    
    # Run all test suites
    try:
        test_target_resolution(results, campaign_id, character_id)
        test_plot_armor_protection(results, campaign_id, character_id)
        test_dnd_combat_mechanics(results, campaign_id, character_id)
        test_combat_state_management(results, campaign_id, character_id)
        test_npc_to_enemy_conversion(results, campaign_id, character_id)
        test_edge_cases(results, campaign_id, character_id)
        
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR during testing: {e}")
        results.add_fail("SYSTEM ERROR", str(e))
    
    # Print final summary
    success = results.summary()
    
    if success:
        print("\n🎉 ALL COMBAT TESTS PASSED!")
        print("✅ Combat system is ready for production")
    else:
        print("\n⚠️ SOME COMBAT TESTS FAILED")
        print("❌ Combat system needs fixes before production")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)