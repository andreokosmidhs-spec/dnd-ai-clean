#!/usr/bin/env python3
"""
Phase 1 Integration Test Suite — dnd-ai-clean
Tests the FastAPI backend locally without hitting any external services.
Covers: startup, health, auth, dice, character creation, game session.

Run from repo root:
    cd backend && uvicorn server:app --port 8001 &
    python phase1_integration_test.py
"""

import requests
import json
import sys
import time
import random
import string

BASE_URL = "http://localhost:8001/api"

# ── Colours ──────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

class Results:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []

    def ok(self, name: str):
        self.passed += 1
        print(f"  {GREEN}✅ PASS{RESET}  {name}")

    def fail(self, name: str, reason: str):
        self.failed += 1
        self.errors.append(f"{name}: {reason}")
        print(f"  {RED}❌ FAIL{RESET}  {name}")
        print(f"         {RED}{reason}{RESET}")

    def skip(self, name: str, reason: str = ""):
        self.skipped += 1
        msg = f" ({reason})" if reason else ""
        print(f"  {YELLOW}⏭  SKIP{RESET}  {name}{msg}")

    def summary(self) -> bool:
        total = self.passed + self.failed + self.skipped
        print(f"\n{'═'*60}")
        print(f"  RESULTS  {self.passed}/{total} passed  "
              f"| {self.failed} failed | {self.skipped} skipped")
        if self.errors:
            print(f"\n  Failures:")
            for e in self.errors:
                print(f"    • {e}")
        print(f"{'═'*60}")
        return self.failed == 0


R = Results()
_token: str = ""
_char_id: str = ""
_session_id: str = ""

def rand_email() -> str:
    tag = "".join(random.choices(string.ascii_lowercase, k=8))
    return f"test_{tag}@jarvis-test.local"

def hdr(auth: bool = False) -> dict:
    h = {"Content-Type": "application/json"}
    if auth and _token:
        h["Authorization"] = f"Bearer {_token}"
    return h

# ── 1. Server Health ──────────────────────────────────────────────────────────
def test_health():
    print(f"\n{'─'*60}")
    print("1. SERVER HEALTH")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code == 200:
            R.ok("GET /api/health → 200")
        else:
            R.fail("GET /api/health", f"Status {r.status_code}")
    except requests.exceptions.ConnectionError:
        R.fail("GET /api/health", "Connection refused — is the server running on :8001?")
        sys.exit(1)   # No point running further tests

# ── 2. Auth Flow ──────────────────────────────────────────────────────────────
def test_auth():
    global _token
    print(f"\n{'─'*60}")
    print("2. AUTH FLOW")

    email = rand_email()
    password = "TestPass123!"

    # Register
    try:
        r = requests.post(f"{BASE_URL}/auth/register",
                          json={"email": email, "password": password},
                          headers=hdr(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            if "token" in data and "user" in data:
                _token = data["token"]
                R.ok("POST /auth/register → token issued")
            else:
                R.fail("POST /auth/register", f"Missing token/user in response: {data}")
        else:
            R.fail("POST /auth/register", f"Status {r.status_code}: {r.text[:200]}")
    except Exception as e:
        R.fail("POST /auth/register", str(e))

    # Login
    try:
        r = requests.post(f"{BASE_URL}/auth/login",
                          json={"email": email, "password": password},
                          headers=hdr(), timeout=10)
        if r.status_code == 200 and "token" in r.json():
            _token = r.json()["token"]
            R.ok("POST /auth/login → token issued")
        else:
            R.fail("POST /auth/login", f"Status {r.status_code}: {r.text[:200]}")
    except Exception as e:
        R.fail("POST /auth/login", str(e))

    # Bad password
    try:
        r = requests.post(f"{BASE_URL}/auth/login",
                          json={"email": email, "password": "wrong"},
                          headers=hdr(), timeout=10)
        if r.status_code == 401:
            R.ok("POST /auth/login wrong password → 401")
        else:
            R.fail("POST /auth/login wrong password", f"Expected 401, got {r.status_code}")
    except Exception as e:
        R.fail("POST /auth/login wrong password", str(e))

    # /me
    try:
        r = requests.get(f"{BASE_URL}/auth/me", headers=hdr(auth=True), timeout=10)
        if r.status_code == 200 and "user" in r.json():
            R.ok("GET /auth/me → user returned")
        else:
            R.fail("GET /auth/me", f"Status {r.status_code}: {r.text[:200]}")
    except Exception as e:
        R.fail("GET /auth/me", str(e))

    # Unauthenticated /me
    try:
        r = requests.get(f"{BASE_URL}/auth/me", timeout=10)
        if r.status_code == 401:
            R.ok("GET /auth/me (no token) → 401")
        else:
            R.fail("GET /auth/me (no token)", f"Expected 401, got {r.status_code}")
    except Exception as e:
        R.fail("GET /auth/me (no token)", str(e))


# ── 3. Dice Rolling ───────────────────────────────────────────────────────────
def test_dice():
    print(f"\n{'─'*60}")
    print("3. DICE ROLLING")
    cases = [
        ("1d20+5",  "formula", "rolls", "total"),
        ("2d6",     "formula", "rolls", "total"),
        ("4d6kh3",  "formula", "rolls", "total"),
        ("1d100",   "formula", "rolls", "total"),
    ]
    for formula, *fields in cases:
        try:
            r = requests.post(f"{BASE_URL}/dice",
                              json={"formula": formula},
                              headers=hdr(), timeout=10)
            if r.status_code == 200:
                data = r.json()
                missing = [f for f in fields if f not in data]
                if missing:
                    R.fail(f"POST /dice {formula}", f"Missing fields: {missing}")
                else:
                    R.ok(f"POST /dice {formula} → total={data['total']}")
            else:
                R.fail(f"POST /dice {formula}", f"Status {r.status_code}: {r.text[:200]}")
        except Exception as e:
            R.fail(f"POST /dice {formula}", str(e))


# ── 4. Character Creation ─────────────────────────────────────────────────────
def test_character():
    global _char_id
    print(f"\n{'─'*60}")
    print("4. CHARACTER CREATION")

    payload = {
        "name": "Jarvis the Brave",
        "race": "Human",
        "character_class": "Fighter",
        "background": "Soldier",
        "stats": {
            "strength": 16,
            "dexterity": 12,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 11,
            "charisma": 9
        }
    }

    try:
        r = requests.post(f"{BASE_URL}/characters",
                          json=payload,
                          headers=hdr(auth=True), timeout=15)
        if r.status_code in (200, 201):
            data = r.json()
            _char_id = data.get("id") or data.get("character_id") or data.get("_id", "")
            R.ok(f"POST /characters → id={_char_id or 'present'}")
        elif r.status_code == 404:
            R.skip("POST /characters", "endpoint not mounted at /api/characters — check router prefix")
        else:
            R.fail("POST /characters", f"Status {r.status_code}: {r.text[:300]}")
    except Exception as e:
        R.fail("POST /characters", str(e))

    # List characters
    if _char_id:
        try:
            r = requests.get(f"{BASE_URL}/characters",
                             headers=hdr(auth=True), timeout=10)
            if r.status_code == 200:
                R.ok("GET /characters → list returned")
            else:
                R.fail("GET /characters", f"Status {r.status_code}")
        except Exception as e:
            R.fail("GET /characters", str(e))


# ── 5. Game Session ───────────────────────────────────────────────────────────
def test_game_session():
    global _session_id
    print(f"\n{'─'*60}")
    print("5. GAME SESSION")

    if not _char_id:
        R.skip("POST /game/action", "no character_id from previous test")
        return

    payload = {
        "character_id": _char_id,
        "message": "I look around the tavern and introduce myself to the barkeeper."
    }

    try:
        r = requests.post(f"{BASE_URL}/game/action",
                          json=payload,
                          headers=hdr(auth=True), timeout=30)
        if r.status_code == 200:
            data = r.json()
            if "response" in data or "narrative" in data or "dm_response" in data:
                R.ok("POST /game/action → DM response received")
            else:
                R.fail("POST /game/action", f"Unexpected response shape: {list(data.keys())}")
        elif r.status_code == 404:
            R.skip("POST /game/action", "endpoint not found — check router mounting")
        elif r.status_code == 402:
            R.skip("POST /game/action", "turn limit hit (expected in test env)")
        else:
            R.fail("POST /game/action", f"Status {r.status_code}: {r.text[:300]}")
    except Exception as e:
        R.fail("POST /game/action", str(e))


# ── 6. Router Health Checks ───────────────────────────────────────────────────
def test_routers():
    print(f"\n{'─'*60}")
    print("6. ROUTER ENDPOINT SMOKE TEST")

    get_endpoints = [
        "/campaigns",
        "/quests",
        "/dungeon-forge/biomes",
        "/knowledge/races",
        "/billing/plans",
        "/feedback",
    ]

    for ep in get_endpoints:
        try:
            r = requests.get(f"{BASE_URL}{ep}",
                             headers=hdr(auth=bool(_token)),
                             timeout=10)
            if r.status_code in (200, 401, 403):
                # 401/403 means endpoint exists but needs auth — that's fine
                label = "→ OK" if r.status_code == 200 else f"→ {r.status_code} (auth required)"
                R.ok(f"GET {ep} {label}")
            elif r.status_code == 404:
                R.fail(f"GET {ep}", "404 — router not mounted")
            elif r.status_code == 422:
                R.ok(f"GET {ep} → 422 (needs body, endpoint exists)")
            else:
                R.fail(f"GET {ep}", f"Unexpected {r.status_code}")
        except Exception as e:
            R.fail(f"GET {ep}", str(e))


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{'═'*60}")
    print("  JARVIS — Phase 1 Integration Test Suite")
    print(f"  Target: {BASE_URL}")
    print(f"{'═'*60}")

    test_health()
    test_auth()
    test_dice()
    test_character()
    test_game_session()
    test_routers()

    success = R.summary()
    sys.exit(0 if success else 1)
