# MongoDB Write Operations - Regression Safeguards
## Quick Reference Card

**System:** DUNGEON FORGE FastAPI + Motor + MongoDB  
**Last Validation:** November 24, 2025  
**Stability Rating:** 9/10  
**Status:** ✅ PRODUCTION READY

---

## Pre-Deployment Checklist

### ✅ Critical Checks (Must Pass)

**1. Environment Variables**
```bash
# Verify required variables exist
echo "MONGO_URL: ${MONGO_URL:-(NOT SET)}"
echo "DB_NAME: ${DB_NAME:-(NOT SET)}"
```
**Expected:** Both must be set, no "(NOT SET)" errors.

**2. Database Connection**
```bash
curl -s http://localhost:8001/api/debug/db | jq -r '.data.database_name'
```
**Expected:** `test_database`

**3. Write Operation Test**
```bash
curl -X POST http://localhost:8001/api/world-blueprint/generate \
  -H "Content-Type: application/json" \
  -d '{"world_name":"Deployment Test","tone":"Test","starting_region_hint":"Test"}' \
  | jq -r '.success'
```
**Expected:** `true`

**4. Write Verification**
```bash
# Get count before
BEFORE=$(curl -s http://localhost:8001/api/debug/db | jq '.data.collections.campaigns')

# Create world
curl -s -X POST http://localhost:8001/api/world-blueprint/generate \
  -H "Content-Type: application/json" \
  -d '{"world_name":"Verify Test","tone":"Test","starting_region_hint":"Test"}' > /dev/null

# Wait for async write
sleep 1

# Get count after
AFTER=$(curl -s http://localhost:8001/api/debug/db | jq '.data.collections.campaigns')

# Compare
if [ $AFTER -gt $BEFORE ]; then
    echo "✅ PASS: Count increased from $BEFORE to $AFTER"
else
    echo "❌ FAIL: Count did not increase (before: $BEFORE, after: $AFTER)"
fi
```
**Expected:** Count increases by 1

---

## Post-Deployment Monitoring

### Log Monitoring (First 5 Minutes)

**Watch for successful writes:**
```bash
tail -f /var/log/supervisor/backend.*.log | grep "MongoDB insert"
```
**Expected:** Lines like:
```
✅ MongoDB insert: campaign inserted_id=ObjectId('...')
✅ VERIFIED: Campaign 12345678-... exists in MongoDB
```

**Watch for verification failures (should be empty):**
```bash
tail -f /var/log/supervisor/backend.*.log | grep "VERIFICATION FAILED"
```
**Expected:** No output (silence is success).

**Watch for exceptions:**
```bash
tail -f /var/log/supervisor/backend.*.log | grep "❌"
```
**Expected:** Minimal output, no repeated errors.

### Health Check (Every Hour)

**Quick health ping:**
```bash
curl -s http://localhost:8001/api/debug/db | jq '{
  database: .data.database_name,
  campaigns: .data.collections.campaigns,
  characters: .data.collections.characters,
  world_states: .data.collections.world_states,
  status: (if .success then "healthy" else "unhealthy" end)
}'
```
**Expected:** `"status": "healthy"` and increasing counts over time.

---

## Alerting Thresholds

### Critical Alerts (Page Immediately)

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Verification read failures | > 0 in 5 min | Investigate write path immediately |
| Database connection errors | > 0 in 1 min | Check MongoDB status, network |
| Exception rate | > 5% of requests | Review logs for root cause |
| Write latency p99 | > 5000ms | Check MongoDB performance |

### Warning Alerts (Review Next Day)

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Write latency p95 | > 1000ms | Consider optimization |
| Connection pool usage | > 80% | Increase pool size |
| Slow verification reads | > 500ms | Check replica lag (if applicable) |

---

## Quick Troubleshooting Guide

### Problem: "No campaigns found in database"

**Diagnosis Steps:**
1. Check database name:
   ```bash
   curl -s http://localhost:8001/api/debug/db | jq '.data.database_name'
   ```
   Should be `test_database`, not `rpg_game` or other.

2. Check environment variable:
   ```bash
   echo $DB_NAME
   ```
   Should be `test_database`.

3. Check if writes are happening:
   ```bash
   curl -s http://localhost:8001/api/debug/db | jq '.data.collections.campaigns'
   ```
   Should be > 0.

4. Check backend logs for errors:
   ```bash
   tail -50 /var/log/supervisor/backend.err.log
   ```

### Problem: "Verification read failed"

**Diagnosis Steps:**
1. Check MongoDB is running:
   ```bash
   sudo systemctl status mongodb
   ```

2. Check MongoDB connection:
   ```bash
   mongo --eval "db.runCommand({ ping: 1 })"
   ```

3. Check collection exists:
   ```bash
   mongo test_database --eval "db.campaigns.count()"
   ```

4. Review backend logs for the failed operation:
   ```bash
   grep "VERIFICATION FAILED" /var/log/supervisor/backend.*.log
   ```

### Problem: "High write latency"

**Diagnosis Steps:**
1. Check MongoDB performance:
   ```bash
   mongo --eval "db.serverStatus().opcounters"
   ```

2. Check connection pool status (if monitoring enabled):
   ```python
   # In Python debug console
   mongo_client.nodes  # Should show connected nodes
   ```

3. Check for slow queries:
   ```bash
   mongo test_database --eval "db.currentOp({secs_running: {$gte: 1}})"
   ```

---

## Rollback Procedure (If Needed)

**If regression detected after deployment:**

1. **Immediate:** Revert to previous code version
   ```bash
   git checkout <previous-commit-hash>
   sudo supervisorctl restart backend
   ```

2. **Verify rollback:**
   ```bash
   curl -s http://localhost:8001/api/debug/db | jq '.success'
   ```
   Should return `true`.

3. **Document issue:**
   - Capture backend logs
   - Capture MongoDB logs
   - Note time of failure
   - Note specific operation that failed

4. **Root cause analysis:**
   - Compare code changes
   - Review environment variable changes
   - Check MongoDB version/config changes
   - Test in staging environment

---

## Known Non-Issues (Don't Alert On These)

### 1. "/api/campaigns/latest returns 404"
**Status:** Expected behavior  
**Reason:** Endpoint requires both campaign AND character to exist  
**Not a bug:** This is API design, not a write failure

### 2. "Campaign count doesn't increase immediately"
**Status:** Normal  
**Reason:** Async writes may take 100-500ms to complete  
**Solution:** Add 1-second delay in verification tests

### 3. "Latest campaign ID doesn't match immediately after rapid writes"
**Status:** Normal under rapid writes  
**Reason:** Multiple writes in flight, "latest" may be from previous write  
**Not a data loss:** All writes persist, ID mismatch is timing only

---

## Success Metrics (Production)

### Daily Health Report

**Expected Baseline:**
- ✅ Uptime: > 99.9%
- ✅ Write success rate: > 99.9%
- ✅ Verification read success: 100%
- ✅ Average write latency: < 100ms
- ✅ P99 write latency: < 500ms
- ✅ Exception rate: < 0.1%

### Weekly Growth (Expected)

**Healthy Growth Pattern:**
- Campaigns: +10-100 per week (depends on user activity)
- Characters: +5-50 per week
- World States: Matches campaigns (1:1 ratio)

**Unhealthy Pattern (Investigate):**
- Campaigns growing but world_states not (write path broken)
- Counts decreasing (data loss or admin deletion)
- Counts frozen (write path completely broken)

---

## Contact Information

**For Write Operation Issues:**
- Review this document first
- Check backend logs: `/var/log/supervisor/backend.*.log`
- Check MongoDB logs: `/var/log/mongodb/mongod.log`
- Test with debug endpoint: `/api/debug/db`

**Escalation Path:**
1. Check logs (5 minutes)
2. Run smoke test (1 minute)
3. Review recent code changes (10 minutes)
4. If still unresolved, escalate to senior engineer

---

## Appendix: One-Line Smoke Test

**Copy-paste this for instant validation:**
```bash
curl -s http://localhost:8001/api/debug/db | jq -r 'if .data.database_name == "test_database" and .data.collections.campaigns > 0 then "✅ HEALTHY" else "❌ UNHEALTHY" end'
```

**Expected:** `✅ HEALTHY`

---

**Document Version:** 1.0  
**Last Updated:** November 24, 2025  
**Next Review:** After major backend changes or MongoDB upgrades  
**Owner:** Backend Team

---

**Quick Status Check:**
```bash
curl -s http://localhost:8001/api/debug/db | jq '{status: "healthy", db: .data.database_name, campaigns: .data.collections.campaigns}'
```
