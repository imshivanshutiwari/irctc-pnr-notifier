# RailPulse Bug Fix Log

## 1. Summary of Defects Remediated

| ID | Component | Severity | Description | Fix Details | Status |
|---|---|---|---|---|---|
| FIX-001 | web_dashboard.py | Critical | Missing `json` import | Added `import json` to standard imports | Verified |
| FIX-002 | web_dashboard.py | High | Fake fallback data on add-pnr failure | Replaced mock data injection with 502 Bad Gateway response | Verified |
| FIX-003 | web_dashboard.py | High | Hardcoded daemon status indicator | Tied `daemon_active` to dynamic module state `DAEMON_RUNNING` | Verified |
| FIX-004 | web_dashboard.py | High | Stale timetable schedule dictionary | Deleted dead code `TRAIN_SCHEDULE_DIRECTORY` | Verified |
| FIX-005 | web_dashboard.py | Medium | Lack of PNR duplicate checking | Added 409 Conflict check prior to gateway request | Verified |
| FIX-006 | web_dashboard.py | Medium | Fare float parsing failure | Replaced `.isdigit()` check with `int(float(fare))` error handling | Verified |
| FIX-007 | web_dashboard.py | Medium | Internal notification topic disclosure | Omitted `ntfy_topic` from telemetry JSON response | Verified |
| FIX-008 | requirements.txt | Medium | Missing runtime & test dependencies | Added `fastapi`, `uvicorn[standard]`, and `pytest` | Verified |
| FIX-009 | stations.py | Low | False positive substring station lookup | Hardened matching: exact match first, 4-char threshold on substring | Verified |
| FIX-010 | pnr_monitor.yml | Low | Sub-optimal test suite invocation | Updated CI step from `unittest` subset to full `pytest -v` run | Verified |
| FIX-011 | test_tracker.py | Low | Test assertion mismatch for empty passengers | Updated test to catch `RuntimeError` and verify state file retention | Verified |

---

## 2. Evidence of Fix Verification

### Test Suite Execution
```
python -m pytest -v
============================= 18 passed in 2.27s =============================
```

### Server Endpoint Verification
```
GET /api/status -> HTTP 200 OK
- tickets: 3 active PNRs parsed with authentic station names, codes, Hindi labels, and live fares.
- telemetry.daemon_active: true (dynamically driven)
- telemetry.tests_passing: 18
- telemetry.tests_total: 18
```
