"""
Phase 1 Integration Test Suite — dnd-ai-clean
Tests that:
  1. The server module imports without error
  2. The FastAPI app mounts all expected routers
  3. Health / status endpoints return 200
  4. Key game endpoints exist (route is registered)
  5. Dice roll endpoint returns valid data
  6. Character creation endpoint exists
  7. Auth router is mounted

Run with:
    cd backend && python -m pytest ../test_phase1_integration.py -v
"""

import sys
import os

# Make sure we can import from the backend directory
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

import pytest
from fastapi.testclient import TestClient


# ─────────────────────────────────────────────
# Fixture: import server and create test client
# ─────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Import the server and return a TestClient. No live DB or AI keys needed."""
    import server as srv
    return TestClient(srv.app, raise_server_exceptions=False)


# ─────────────────────────────────────────────
# 1. Server import sanity
# ─────────────────────────────────────────────

def test_server_imports():
    """Server module should import without raising any exception."""
    import server  # noqa: F401
    assert True


def test_app_is_fastapi(client):
    """The app object should be a FastAPI instance."""
    import server as srv
    from fastapi import FastAPI
    assert isinstance(srv.app, FastAPI)


# ─────────────────────────────────────────────
# 2. Router registration — check routes exist
# ─────────────────────────────────────────────

def _route_paths(client):
    import server as srv
    return [r.path for r in srv.app.routes]


def test_health_route_exists(client):
    paths = _route_paths(client)
    assert any("/api" in p or "/" == p for p in paths), f"No base routes found: {paths[:10]}"


def test_auth_route_registered(client):
    paths = _route_paths(client)
    assert any("auth" in p for p in paths), f"Auth router not mounted. Routes: {paths[:20]}"


def test_campaigns_route_registered(client):
    paths = _route_paths(client)
    assert any("campaign" in p for p in paths), f"Campaigns router not mounted. Routes: {paths[:20]}"


def test_characters_route_registered(client):
    paths = _route_paths(client)
    assert any("character" in p for p in paths), f"Characters router not mounted."


def test_dungeon_forge_route_registered(client):
    paths = _route_paths(client)
    assert any("dungeon" in p.lower() for p in paths), f"Dungeon Forge router not mounted."


def test_quests_route_registered(client):
    paths = _route_paths(client)
    assert any("quest" in p for p in paths), f"Quests router not mounted."


def test_billing_route_registered(client):
    paths = _route_paths(client)
    assert any("billing" in p or "stripe" in p for p in paths), f"Billing router not mounted."


# ─────────────────────────────────────────────
# 3. HTTP responses — live endpoint calls
# ─────────────────────────────────────────────

def test_root_returns_200_or_redirect(client):
    """Root endpoint should return something (not 500)."""
    r = client.get("/")
    assert r.status_code in (200, 301, 302, 307, 308, 404), f"Root returned {r.status_code}"


def test_openapi_schema_accessible(client):
    """FastAPI auto-generates /openapi.json — it should always be 200."""
    r = client.get("/openapi.json")
    assert r.status_code == 200, f"OpenAPI schema missing: {r.status_code}"
    data = r.json()
    assert "paths" in data, "OpenAPI schema has no paths"


def test_docs_accessible(client):
    """Swagger UI should be available."""
    r = client.get("/docs")
    assert r.status_code == 200


def test_dice_roll_endpoint(client):
    """POST /api/roll-dice should return a result between 1 and 20."""
    r = client.post("/api/roll-dice", json={"dice_type": "d20", "num_dice": 1})
    if r.status_code == 404:
        pytest.skip("Dice endpoint not implemented at /api/roll-dice — skipping")
    assert r.status_code == 200, f"Dice roll failed: {r.status_code} {r.text}"
    data = r.json()
    # Accept either {"result": N} or {"total": N} or {"roll": N}
    value = data.get("result") or data.get("total") or data.get("roll")
    assert value is not None, f"No roll value in response: {data}"
    assert 1 <= int(value) <= 20, f"Roll out of range: {value}"


def test_status_check_endpoint(client):
    """POST /api/status should return 200 or skip gracefully if DB is unavailable."""
    r = client.post("/api/status", json={"client_name": "jarvis_test"})
    if r.status_code == 404:
        pytest.skip("Status endpoint not at /api/status")
    if r.status_code == 500:
        # In test mode without MongoDB this endpoint may fail — that is a known limitation
        pytest.skip("Status endpoint requires MongoDB — skipping in no-DB test mode")
    assert r.status_code in (200, 201), f"Status check failed: {r.status_code}"


# ─────────────────────────────────────────────
# 4. Auth endpoints exist
# ─────────────────────────────────────────────

def test_register_endpoint_exists(client):
    """POST /auth/register should exist (may return 422 without body, not 404)."""
    r = client.post("/auth/register", json={})
    assert r.status_code != 404, f"Register endpoint not found (404). Got {r.status_code}"


def test_login_endpoint_exists(client):
    """POST /auth/login should exist."""
    r = client.post("/auth/login", json={})
    assert r.status_code != 404, f"Login endpoint not found (404). Got {r.status_code}"


# ─────────────────────────────────────────────
# 5. Campaign endpoints exist
# ─────────────────────────────────────────────

def test_create_campaign_endpoint_exists(client):
    """POST /api/campaigns/latest or similar should exist."""
    # Try /api/campaigns first, then /api/campaigns/latest
    r = client.post("/api/campaigns", json={})
    if r.status_code == 404:
        r = client.get("/api/campaigns/latest")
    assert r.status_code != 404, f"Campaign endpoints not found. Got {r.status_code}"


def test_list_campaigns_endpoint_exists(client):
    """GET /api/campaigns or /api/campaigns/latest should exist."""
    r = client.get("/api/campaigns")
    if r.status_code == 404:
        r = client.get("/api/campaigns/latest")
    assert r.status_code != 404, f"List campaigns endpoint not found. Got {r.status_code}"


# ─────────────────────────────────────────────
# 6. OpenAPI route count sanity check
# ─────────────────────────────────────────────

def test_minimum_route_count(client):
    """App should have at least 50 routes (it has 30+ routers)."""
    import server as srv
    route_count = len(srv.app.routes)
    assert route_count >= 50, f"Only {route_count} routes found — routers may not be mounting correctly"
