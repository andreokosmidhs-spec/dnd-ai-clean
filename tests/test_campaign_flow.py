"""
Backend API Tests for D&D RPG Forge Campaign Generation Flow
Tests the complete flow: Character Creation → Campaign Draft → World Generation → Adventure
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://dragon-quest-58.preview.emergentagent.com')


class TestBackendHealth:
    """Basic health check tests"""
    
    def test_api_root(self):
        """Test API root endpoint returns expected response"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Sentient RPG Engine" in data["message"]


class TestCharacterV2API:
    """Tests for Character V2 API endpoints"""
    
    def test_list_characters(self):
        """Test listing characters"""
        response = requests.get(f"{BASE_URL}/api/v2/characters/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} characters in database")
    
    def test_create_character(self):
        """Test creating a new character"""
        character_data = {
            "identity": {
                "name": f"TEST_Hero_{uuid.uuid4().hex[:6]}",
                "sex": "male",
                "genderExpression": 50,
                "age": 25
            },
            "race": {
                "key": "Human",
                "variantKey": ""
            },
            "class": {
                "key": "Fighter",
                "subclassKey": "",
                "level": 1,
                "skillProficiencies": ["Athletics", "Intimidation"]
            },
            "abilityScores": {
                "str": 15,
                "dex": 14,
                "con": 13,
                "int": 12,
                "wis": 10,
                "cha": 8,
                "method": "standard_array"
            },
            "background": {
                "key": "acolyte",
                "variantKey": ""
            },
            "appearance": {
                "ageCategory": "Adult",
                "heightCm": 175,
                "build": "Average",
                "skinTone": "Fair",
                "hairColor": "Brown",
                "eyeColor": "Blue",
                "notableFeatures": []
            },
            "meta": {
                "version": 2
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/characters/v2/create",
            json=character_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["identity"]["name"].startswith("TEST_Hero_")
        print(f"Created character with ID: {data['id']}")
        return data["id"]
    
    def test_get_character_by_id(self):
        """Test getting a specific character by ID"""
        # First create a character
        char_id = self.test_create_character()
        
        # Then fetch it
        response = requests.get(f"{BASE_URL}/api/v2/characters/{char_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == char_id


class TestCampaignAPI:
    """Tests for Campaign API endpoints - the main flow being tested"""
    
    @pytest.fixture
    def test_character_id(self):
        """Create a test character and return its ID"""
        character_data = {
            "identity": {
                "name": f"TEST_CampaignHero_{uuid.uuid4().hex[:6]}",
                "sex": "male",
                "genderExpression": 50,
                "age": 25
            },
            "race": {"key": "Human", "variantKey": ""},
            "class": {
                "key": "Fighter",
                "subclassKey": "",
                "level": 1,
                "skillProficiencies": ["Athletics", "Intimidation"]
            },
            "abilityScores": {
                "str": 15, "dex": 14, "con": 13,
                "int": 12, "wis": 10, "cha": 8,
                "method": "standard_array"
            },
            "background": {"key": "acolyte", "variantKey": ""},
            "appearance": {
                "ageCategory": "Adult",
                "heightCm": 175,
                "build": "Average",
                "skinTone": "Fair",
                "hairColor": "Brown",
                "eyeColor": "Blue",
                "notableFeatures": []
            },
            "meta": {"version": 2}
        }
        
        response = requests.post(
            f"{BASE_URL}/api/characters/v2/create",
            json=character_data
        )
        assert response.status_code == 200
        return response.json()["id"]
    
    def test_campaign_draft_creation(self, test_character_id):
        """Test creating a campaign draft - Step 1 of the flow"""
        draft_data = {
            "characterId": test_character_id,
            "intent": {
                "tone": "Balanced",
                "focus": "Story",
                "scope": "City",
                "danger": "Medium"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/draft",
            json=draft_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "campaignId" in data
        assert data["status"] == "draft"
        print(f"Created campaign draft: {data['campaignId']}")
        return data["campaignId"]
    
    def test_campaign_draft_requires_character(self):
        """Test that campaign draft fails without valid character"""
        draft_data = {
            "characterId": "invalid-character-id-12345",
            "intent": {
                "tone": "Balanced",
                "focus": "Story",
                "scope": "City",
                "danger": "Medium"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/draft",
            json=draft_data
        )
        # Should return error for invalid character
        data = response.json()
        # The API wraps errors in a standard format
        assert response.status_code == 200 or "error" in data or data.get("success") == False
    
    def test_generate_world_endpoint(self, test_character_id):
        """Test world generation - Step 2 of the flow (CRITICAL TEST)"""
        # First create a campaign draft
        draft_data = {
            "characterId": test_character_id,
            "intent": {
                "tone": "Balanced",
                "focus": "Story",
                "scope": "City",
                "danger": "Medium"
            }
        }
        
        draft_response = requests.post(
            f"{BASE_URL}/api/campaigns/draft",
            json=draft_data
        )
        assert draft_response.status_code == 200
        campaign_id = draft_response.json()["campaignId"]
        
        # Now generate the world - THIS IS THE ENDPOINT THAT WAS FAILING
        response = requests.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/generate-world"
        )
        
        # CRITICAL: This should return 200, not error
        assert response.status_code == 200, f"generate-world failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "ready"
        assert "world" in data
        assert "startingScene" in data
        
        # Verify world structure
        world = data["world"]
        assert "summary" in world
        assert "startingLocation" in world
        
        print(f"World generated successfully: {world['summary'][:100]}...")
        return campaign_id
    
    def test_knowledge_cards_endpoint(self, test_character_id):
        """Test knowledge cards loading - Step 3 of the flow"""
        # Create campaign and generate world first
        draft_data = {
            "characterId": test_character_id,
            "intent": {
                "tone": "Balanced",
                "focus": "Story",
                "scope": "City",
                "danger": "Medium"
            }
        }
        
        draft_response = requests.post(
            f"{BASE_URL}/api/campaigns/draft",
            json=draft_data
        )
        campaign_id = draft_response.json()["campaignId"]
        
        # Generate world
        requests.post(f"{BASE_URL}/api/campaigns/{campaign_id}/generate-world")
        
        # Get knowledge cards
        response = requests.get(
            f"{BASE_URL}/api/campaigns/{campaign_id}/log/cards"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "cards" in data
        assert isinstance(data["cards"], list)
        assert len(data["cards"]) > 0, "Should have at least one knowledge card"
        
        # Verify card structure
        card = data["cards"][0]
        assert "id" in card
        assert "type" in card
        assert "title" in card
        
        print(f"Found {len(data['cards'])} knowledge cards")


class TestFullCampaignFlow:
    """End-to-end test of the complete campaign generation flow"""
    
    def test_complete_campaign_flow(self):
        """
        Test the complete flow that was reported as broken:
        1. Create character
        2. Create campaign draft
        3. Generate world
        4. Load knowledge cards
        
        This should NOT return to main menu - it should complete successfully
        """
        print("\n=== TESTING COMPLETE CAMPAIGN FLOW ===\n")
        
        # Step 1: Create character
        print("Step 1: Creating character...")
        character_data = {
            "identity": {
                "name": f"TEST_FlowHero_{uuid.uuid4().hex[:6]}",
                "sex": "male",
                "genderExpression": 50,
                "age": 25
            },
            "race": {"key": "Human", "variantKey": ""},
            "class": {
                "key": "Fighter",
                "subclassKey": "",
                "level": 1,
                "skillProficiencies": ["Athletics", "Intimidation"]
            },
            "abilityScores": {
                "str": 15, "dex": 14, "con": 13,
                "int": 12, "wis": 10, "cha": 8,
                "method": "standard_array"
            },
            "background": {"key": "acolyte", "variantKey": ""},
            "appearance": {
                "ageCategory": "Adult",
                "heightCm": 175,
                "build": "Average",
                "skinTone": "Fair",
                "hairColor": "Brown",
                "eyeColor": "Blue",
                "notableFeatures": []
            },
            "meta": {"version": 2}
        }
        
        char_response = requests.post(
            f"{BASE_URL}/api/characters/v2/create",
            json=character_data
        )
        assert char_response.status_code == 200
        character_id = char_response.json()["id"]
        print(f"  ✓ Character created: {character_id}")
        
        # Step 2: Create campaign draft
        print("Step 2: Creating campaign draft...")
        draft_data = {
            "characterId": character_id,
            "intent": {
                "tone": "Balanced",
                "focus": "Story",
                "scope": "City",
                "danger": "Medium"
            }
        }
        
        draft_response = requests.post(
            f"{BASE_URL}/api/campaigns/draft",
            json=draft_data
        )
        assert draft_response.status_code == 200
        campaign_id = draft_response.json()["campaignId"]
        print(f"  ✓ Campaign draft created: {campaign_id}")
        
        # Step 3: Generate world (THIS WAS THE FAILING STEP)
        print("Step 3: Generating world blueprint...")
        world_response = requests.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/generate-world"
        )
        
        # CRITICAL ASSERTION - This is what was failing before
        assert world_response.status_code == 200, f"World generation failed: {world_response.text}"
        
        world_data = world_response.json()
        assert world_data["status"] == "ready"
        print(f"  ✓ World generated: {world_data['world']['summary'][:50]}...")
        
        # Step 4: Load knowledge cards
        print("Step 4: Loading knowledge cards...")
        cards_response = requests.get(
            f"{BASE_URL}/api/campaigns/{campaign_id}/log/cards"
        )
        assert cards_response.status_code == 200
        cards_data = cards_response.json()
        assert len(cards_data["cards"]) > 0
        print(f"  ✓ Knowledge cards loaded: {len(cards_data['cards'])} cards")
        
        print("\n=== CAMPAIGN FLOW COMPLETED SUCCESSFULLY ===")
        print(f"Campaign ID: {campaign_id}")
        print(f"Status: {world_data['status']}")
        print("The adventure screen should now load (not return to main menu)")
        
        return {
            "character_id": character_id,
            "campaign_id": campaign_id,
            "status": world_data["status"],
            "world": world_data["world"],
            "cards_count": len(cards_data["cards"])
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
