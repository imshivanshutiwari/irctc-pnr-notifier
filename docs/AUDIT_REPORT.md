# RailPulse Full Codebase Audit Report

## 1. Executive Summary

This report documents the comprehensive, evidence-driven audit, bug remediation, security hardening, and test expansion conducted across the entire RailPulse codebase. RailPulse is an Indian Railways PNR waiting-list and RAC status monitoring application with real-time alerting via ntfy and Telegram.

All audit targets and constraints have been satisfied:
- Zero emojis across all files, code, templates, and reports.
- Zero synthetic or fake data fields displayed in PRS tickets.
- 18 automated tests passing cleanly (expanded from 11).
- 100% authentic station code, station name, Hindi transliteration, and live booking telemetry.
- Root cause fixes applied to functional defects, runtime errors, and information disclosures.

---

## 2. Architecture & Discovery Findings

| Component | Technology | Implementation Details |
|---|---|---|
| Runtime | Python 3.10.11 / 3.11 | Modern typing, asyncio lifespan management |
| Web Framework | FastAPI + Uvicorn | Port 8000, 127.0.0.1 loopback binding |
| Gateways | ConfirmTKT API + RapidAPI | Primary zero-key public gateway with RapidAPI fallback |
| Station Index | stations.py | 80+ major railway junction codes, English names, Hindi names |
| Persistence | status_state.json | Atomic file-writes using NamedTemporaryFile and os.replace |
| Notifications | Notifier (ntfy + Telegram) | State-diff improvement alerting only |
| Test Suite | pytest 8.2.0 | 18 unit and integration tests passing |
| CI Pipeline | GitHub Actions | Ubuntu runner, pytest runner, automated workflow |

---

## 3. Discovered Vulnerabilities & Remediations

### CRITICAL-001: Missing `json` Import in `web_dashboard.py`
- **Location:** `web_dashboard.py:8-13`
- **Impact:** NameError crash upon server startup when reading or writing poll state timestamp.
- **Remediation:** Added `import json` to standard library imports.

### HIGH-001: Synthetic / Fake Fallback Data in PNR Enrollment
- **Location:** `web_dashboard.py:469-490`
- **Impact:** Failed or unknown PNR lookups returned mock train numbers (12424 Rajdhani), fake stations, and hardcoded passenger status.
- **Remediation:** Removed synthetic fallback completely. The `/api/add-pnr` endpoint returns a clear 502 Bad Gateway error with upstream detail if the railway gateway cannot retrieve authentic data.

### HIGH-002: Hardcoded Daemon Health Indicator
- **Location:** `web_dashboard.py:331`
- **Impact:** `telemetry.daemon_active` was hardcoded to `True` regardless of actual asyncio poller thread state.
- **Remediation:** Tied telemetry to dynamic module variable `DAEMON_RUNNING`, updated in lifespan and background poller lifecycle.

### HIGH-003: Unused Static Timetable Directory
- **Location:** `web_dashboard.py:53-124`
- **Impact:** Hardcoded static schedules (`TRAIN_SCHEDULE_DIRECTORY`) polluted runtime memory and conflicted with live API telemetry.
- **Remediation:** Deleted dead schedule dictionary in favor of dynamic `stations.py` queries and live API payloads.

### MED-001: Missing PNR Duplicate Enrollment Check
- **Location:** `web_dashboard.py:460-475`
- **Impact:** Submitting an already monitored PNR re-triggered external gateway calls and created duplicate tracking attempts.
- **Remediation:** Added duplicate PNR validation check returning HTTP 409 Conflict if already present in state.

### MED-002: Fare Numeric Parsing Incompatibility
- **Location:** `web_dashboard.py:360-366`
- **Impact:** Fare parsing used `str(fare).isdigit()`, failing when upstream gateways returned float-formatted fare strings like `"1305.0"`.
- **Remediation:** Implemented safe conversion using `int(float(api_fare))` wrapped in exception handling, correctly translating to uppercase Indian currency words.

### MED-003: Internal Notification Topic Disclosure
- **Location:** `web_dashboard.py:408-410`
- **Impact:** `telemetry.ntfy_topic` was exposing the full internal topic name over unauthenticated API responses.
- **Remediation:** Removed raw topic string from telemetry response; replaced with boolean `ntfy_configured` and status string.

### LOW-001: Missing Dependencies in `requirements.txt`
- **Location:** `requirements.txt`
- **Impact:** `fastapi`, `uvicorn`, and `pytest` were omitted, causing potential build failures in clean environments and CI.
- **Remediation:** Appended `fastapi>=0.111.0`, `uvicorn[standard]>=0.29.0`, and `pytest>=8.0.0`.

### LOW-002: Substring Collisions in Station Lookup
- **Location:** `stations.py:123-130`
- **Impact:** Short substrings could map unrelated station names erroneously.
- **Remediation:** Prioritized exact case-insensitive matches, enforced minimum 4-character length threshold for fallback matching.

---

## 4. Verification Evidence

- Full Test Run: `pytest -v` -> 18 passed in 2.27s
- Live Telemetry: Verified active on `http://127.0.0.1:8000/api/status`
- State File: Atomically synchronized across active fleet PNRs (4763331979, 7000126327, 6610459110)
- PRS Display: All 16 synthetic fields removed and replaced with authentic markers (`--`) or genuine values.
