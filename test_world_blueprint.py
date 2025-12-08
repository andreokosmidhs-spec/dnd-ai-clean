#!/usr/bin/env python3
"""
Test the new world blueprint generation system.
"""
import requests
import json

BACKEND_URL = "https://prompt-architect-23.preview.emergentagent.com/api"

def test_world_blueprint_generation():
    """Test generating a world blueprint"""
    print("\n" + "="*80)
    print("TEST 1: World Blueprint Generation")
    print("="*80)
    
    payload = {
        "world_name": "Valdrath",
        "tone": "Dark, grounded fantasy with rare but dangerous magic",
        "starting_region_hint": "Raven's Hollow, a fog-bound trade hub full of secrets and thieves"
    }
    
    print(f"\nGenerating world blueprint...")
    print(f"Input: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/world-blueprint/generate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text)
            return None
        
        data = response.json()
        world_blueprint = data.get("world_blueprint")
        
        print(f"\n✅ World blueprint generated!")
        print(f"World name: {world_blueprint['world_core']['name']}")
        print(f"Tone: {world_blueprint['world_core']['tone']}")
        print(f"Ancient event: {world_blueprint['world_core']['ancient_event']['name']}")
        print(f"Starting town: {world_blueprint['starting_town']['name']}")
        print(f"Points of interest: {len(world_blueprint['points_of_interest'])}")
        print(f"Key NPCs: {len(world_blueprint['key_npcs'])}")
        print(f"Factions: {len(world_blueprint['factions'])}")
        
        return world_blueprint
        
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_intro_generation(world_blueprint):
    """Test generating an intro with the world blueprint"""
    print("\n" + "="*80)
    print("TEST 2: Intro Generation")
    print("="*80)
    
    payload = {
        "character": {
            "name": "Avon",
            "race": "Human",
            "class": "Rogue",
            "background": "Criminal",
            "goal": "Track down Vexis the Shattering"
        },
        "region": {
            "name": "Raven's Hollow",
            "description": "A fog-bound trade hub full of secrets and thieves"
        },
        "world_blueprint": world_blueprint
    }
    
    print(f"\nGenerating intro for Avon...")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/intro/generate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        intro_md = data.get("intro_markdown")
        
        print(f"\n✅ Intro generated ({len(intro_md)} chars)")
        print("\n" + "-"*80)
        print("INTRO CONTENT:")
        print("-"*80)
        print(intro_md)
        print("-"*80)
        
        # Validate structure
        required_sections = [
            "### 1) WORLD SCALE",
            "### 2) REGION SCALE",
            "### 3) CITY/TOWN SCALE",
            "### 4) CHARACTER HOOK",
            "### 5) CHOICE PROMPT"
        ]
        
        print("\n" + "="*80)
        print("STRUCTURE VALIDATION:")
        print("="*80)
        for section in required_sections:
            if section in intro_md:
                print(f"✅ {section}")
            else:
                print(f"❌ {section} MISSING")
        
        # Check for numbered options
        import re
        options_found = len(re.findall(r'\n\d+\.', intro_md))
        print(f"\n{'✅' if options_found >= 3 else '❌'} Found {options_found} numbered options (need 3-5)")
        
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("WORLD BLUEPRINT SYSTEM TEST")
    print("="*80)
    
    # Test 1: Generate world blueprint
    world_blueprint = test_world_blueprint_generation()
    
    if world_blueprint:
        # Test 2: Generate intro using the blueprint
        test_intro_generation(world_blueprint)
    else:
        print("\n❌ Skipping intro test due to world blueprint generation failure")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
