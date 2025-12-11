from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.character_v2_routes import FAKE_CHAR_STORE, router


def build_valid_payload():
    return {
        "identity": {
            "name": "Aria Brightwood",
            "sex": "female",
            "age": 24,
            "genderExpression": 60,
        },
        "race": {"key": "human"},
        "class": {"key": "wizard", "level": 1, "skillProficiencies": ["arcana", "history"]},
        "abilityScores": {
            "method": "standard_array",
            "str": 15,
            "dex": 14,
            "con": 13,
            "int": 12,
            "wis": 10,
            "cha": 8,
        },
        "background": {"key": "sage"},
        "appearance": {
            "ageCategory": "adult",
            "heightCm": 170,
            "build": "slim",
            "skinTone": "fair",
            "hairColor": "brown",
            "eyeColor": "green",
            "notableFeatures": ["tattoo"],
        },
    }


def test_create_character_v2_round_trip():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    FAKE_CHAR_STORE.clear()
    payload = build_valid_payload()

    response = client.post("/api/characters/v2/create", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["id"]
    assert data["identity"]["name"] == payload["identity"]["name"]
    assert data["identity"]["genderExpression"] == payload["identity"]["genderExpression"]
    assert data["class"]["key"] == payload["class"]["key"]
    assert data["abilityScores"]["str"] == payload["abilityScores"]["str"]

    list_response = client.get("/api/characters/v2")
    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed) == 1
    assert listed[0]["id"] == data["id"]
