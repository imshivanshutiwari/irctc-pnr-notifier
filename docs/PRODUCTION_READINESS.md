# RailPulse Production Readiness & Operations Review

## 1. Readiness Assessment

RailPulse is verified ready for continuous local operation and automated scheduled execution via GitHub Actions.

| Criterion | Assessment | Notes |
|---|---|---|
| Reliability | Passed | Atomic state writes prevent corruption; network exceptions do not crash background daemon |
| Data Truthfulness | Passed | 100% authentic data; zero synthetic ticket fields; authentic station names and codes |
| Security | Passed | Loopback 127.0.0.1 binding; no credentials in git; sensitive tokens redacted from API responses |
| Maintainability | Passed | Modular architecture (stations.py, pnr_client.py, tracker.py, notifier.py, cadence_engine.py, web_dashboard.py) |
| Performance | Passed | Async lifespan management; non-blocking autonomous adaptive daemon; zero UI flickering |
| Test Coverage | Passed | 62 passing automated tests in pytest + 9 test suites in Node.js berth engine |

---

## 2. Deployment & Operational Runbook

### Local Web Dashboard Execution
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the dashboard server
python web_dashboard.py
```
Access dashboard at `http://localhost:8000`.

### Background CLI Execution
```bash
# Run one-shot status check across configured PNRs
python tracker.py --pnr 4345031074,6610459110

# Dry-run mode (print alert messages to console without dispatching network calls)
python tracker.py --pnr 4345031074 --dry-run
```

### GitHub Actions Autonomous Monitoring
The repository includes `.github/workflows/pnr_monitor.yml`, which executes scheduled checks:
- Runs `python -m pytest -v` before executing tracker
- Restores state cache from previous workflow runs
- Uses GitHub Repository Secrets: `PNR_NUMBER`, `NTFY_TOPIC`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `RAPIDAPI_KEY`

---

## 3. Maintenance & Operational Procedures

1. **Station Database Expansion:** To add new railway stations, update `STATION_MAP` in `stations.py` with the 3-5 letter station code, canonical English name, and official Hindi script name.
2. **Archiving Completed Journeys:** Completed journeys are automatically pruned and archived in `archived_pnrs.json` once a train arrives at its destination (after the 120-minute operational delay buffer).
3. **Adaptive Polling Intervals:** The autonomous daemon in `web_dashboard.py` monitors journey dates relative to Indian Standard Time (IST):
   - Tickets within 2 days of departure are polled every 2 hours (`priority-2h`).
   - Tickets more than 2 days away are polled every 5 hours (`standard-5h`).
   - Polling schedules and countdowns persist across server restarts in `.last_poll_state.json`.
