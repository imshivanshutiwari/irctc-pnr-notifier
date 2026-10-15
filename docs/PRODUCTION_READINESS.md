# RailPulse Production Readiness & Operations Review

## 1. Readiness Assessment

RailPulse is verified ready for continuous local operation and automated scheduled execution via GitHub Actions.

| Criterion | Assessment | Notes |
|---|---|---|
| Reliability | Passed | Atomic state writes prevent corruption; network exceptions do not crash background daemon |
| Data Truthfulness | Passed | 100% authentic data; zero synthetic ticket fields; authentic station names and codes |
| Security | Passed | Loopback 127.0.0.1 binding; no credentials in git; sensitive tokens redacted from API responses |
| Maintainability | Passed | Modular architecture (stations.py, pnr_client.py, tracker.py, notifier.py, web_dashboard.py) |
| Performance | Passed | Async lifespan management; 30-second frontend polling with DOM diffing to prevent UI flickering |
| Test Coverage | Passed | 18 passing tests covering status classification, progression, deduplication, and edge cases |

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
python tracker.py --pnr 4763331979,7000126327,6610459110

# Dry-run mode (print alert messages to console without dispatching network calls)
python tracker.py --pnr 4763331979 --dry-run
```

### GitHub Actions Autonomous 24/7 Monitoring
The repository includes `.github/workflows/pnr_monitor.yml`, which executes scheduled checks every 5 hours:
- Cron schedule: `0 */5 * * *`
- Runs `python -m pytest -v` before executing tracker
- Restores state cache from previous workflow runs
- Uses GitHub Repository Secrets: `PNR_NUMBER`, `NTFY_TOPIC`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `RAPIDAPI_KEY`

---

## 3. Maintenance Checklist

1. **Station Database Expansion:** To add new railway stations, update `STATION_MAP` in `stations.py` with the 3-5 letter station code, canonical English name, and official Hindi script name.
2. **Gateway Monitoring:** If the free ConfirmTKT endpoint introduces rate limits or schema changes, the client automatically falls back to RapidAPI if `RAPIDAPI_KEY` is configured in `.env`.
3. **State Backup:** The `status_state.json` file is ignored in git to preserve user privacy and contains the latest serialized booking state. Back up this file if migrating servers.
