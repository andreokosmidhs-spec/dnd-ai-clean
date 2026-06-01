# Jarvis Learnings

## 2026-06-01 07:14 — Phase 1 stabilisation — fix crashes, write integration tests
**Worked:** UTF-8 reconfigure at top of server.py fixes all emoji print crashes on Windows/Render. Missing requirements.txt was the main Render deploy blocker. FastAPI TestClient works without MongoDB — DB-dependent tests should be skipped not failed.
**Failed:** Initial emoji fix was partial — had to add sys.stdout.reconfigure at module top to cover all future emoji prints rather than replacing them one-by-one.
**Time:** 45 min

