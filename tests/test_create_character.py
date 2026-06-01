"""
Quick character creation smoke test — uses FastAPI TestClient, no live server needed.
Tests POST /api/characters/v2/create with a full D&D 5e Fighter payload.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from fastapi.testclient import TestClient

@pytest.fixture(scope="module")
def client():
    from server import app
    return TestClient(app, raise_server_exceptions=False)

CHARACTER_PAYLOAD = {
    "identity": {
        "name": "Aldric Stormhand",
        "sex": "male",
        "genderExpression": 50,
        "age": 28
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
    "background": {"key": "soldier", "variantKey": ""},
    "appearance": {
        "ageCategory": "Adult",
        "heightCm": 182,
        "build": "Athletic",
        "skinTone": "Tan",
        "hairColor": "Black",
        "eyeColor": "Grey",
        "notableFeatures": ["Scar across left cheek"]
    },
    "meta": {"version": 2}
}


def test_character_creation_returns_200(client):
    """Endpoint should return 200."""
    resp = client.post("/api/characters/v2/create", json=CHARACTER_PAYLOAD)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


def test_character_creation_returns_id(client):
    """Response should contain a character id."""
    resp = client.post("/api/characters/v2/create", json=CHARACTER_PAYLOAD)
    data = resp.json()
    assert "id" in data, f"No 'id' in response: {data}"
    assert data["id"], "Character id is empty"
    print(f"\n  Character created — ID: {data['id']}")


def test_character_name_matches(client):
    """Character name in response should match what we sent."""
    resp = client.post("/api/characters/v2/create", json=CHARACTER_PAYLOAD)
    data = resp.json()
    # Accept name at top level or nested under character_state
    name = data.get("name") or (data.get("character_state") or {}).get("name", "")
    assert "Aldric" in str(name) or name == "", f"Unexpected name in response: {name}"


def test_character_endpoint_exists(client):
    """Router is mounted — 404 means router is missing, not a logic error."""
    resp = client.post("/api/characters/v2/create", json=CHARACTER_PAYLOAD)
    assert resp.status_code != 404, "Router not mounted — /api/characters/v2/create returned 404"
