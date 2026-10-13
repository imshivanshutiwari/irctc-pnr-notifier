# RailPulse - Autonomous IRCTC PNR Waiting List Monitor

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Zero Cost](https://img.shields.io/badge/Cost-%240%2Fmonth-brightgreen.svg)]()
[![CI Status](https://img.shields.io/badge/CI-Passing-success.svg)]()
[![Multi-Channel](https://img.shields.io/badge/Alerts-ntfy%20%7C%20WhatsApp%20%7C%20Telegram-orange.svg)]()

> Autonomous, zero-cost cloud monitoring engine that monitors Indian Railways (IRCTC) waiting list tickets 24/7 and sends instant mobile alerts when seat status improves or confirms.

---

## The Problem and The Solution

Travelers who book Indian Railways tickets often face long waiting lists (`WL 10`, `RLWL 5`). Checking IRCTC repeatedly is tedious, commercial apps can be ad-heavy, and paid SMS services add recurring costs.

**RailPulse** addresses this problem:
* **Autonomous and Serverless**: Runs in GitHub Actions cloud for free - no dedicated server or laptop uptime required ($0/month).
* **Zero Spam Guarantee**: Completely silent background checks. It triggers an alert if and only if ticket status improves (e.g. `RLWL 10` -> `RLWL 9`, promotion to `RAC`, or final `CNF`).
* **Zero API Key Quotas**: Uses direct railway endpoint integration with RapidAPI fallback to avoid quota exhaustion.
* **Multi-Channel Instant Alerts**: Mobile notifications delivered via **ntfy.sh**, **WhatsApp**, or **Telegram**.
* **Multi-Ticket Monitoring**: Concurrently tracks multiple 10-digit PNRs in a single run.

---

## Architecture and Data Flow

```mermaid
flowchart TD
    subgraph Cloud["GitHub Actions Cloud (Every 5 Hours)"]
        Cron["Cron Trigger / Manual Dispatch"] --> Engine["tracker.py Engine"]
    end

    subgraph RailAPI["Rail Gateway"]
        Engine --> Gateway{"Open Rail Gateway<br>(api.confirmtkt.com)"}
        Gateway -->|Fallback| RapidAPI["RapidAPI IRCTC"]
    end

    subgraph State["Private State Management"]
        Engine <--> Cache[("GitHub Actions Cache / Local JSON<br>(Zero Public Leaks)")]
    end

    subgraph Detection["Deterministic Transition Rules"]
        Engine --> Classifier["Regex Classifier<br>(GNWL, RLWL, PQWL, RAC, CNF)"]
        Classifier --> Diff{"Position Reduced<br>or Confirmed?"}
    end

    subgraph Alerts["Instant Mobile Notifications"]
        Diff -->|Yes (Improved)| Push["ntfy.sh (Instant Push)"]
        Diff -->|Yes (Improved)| WA["WhatsApp (CallMeBot)"]
        Diff -->|Yes (Improved)| TG["Telegram Bot"]
        Diff -->|No Change| Silent["Silent (Zero Spam)"]
    end
```

---

## Quick Start (Local Setup)

### 1. Clone and Install
```bash
git clone https://github.com/imshivanshutiwari/irctc-pnr-notifier.git
cd irctc-pnr-notifier
pip install -r requirements.txt
```

### 2. Configure Environment
Copy the example template:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
# Monitor single or multiple comma-separated PNRs
PNR_NUMBER=4763331979,7000126327,6610459110

# Choose your notification channel (ntfy is recommended - zero signup)
NTFY_TOPIC=my-private-train-topic

# Optional: WhatsApp / Telegram
WHATSAPP_PHONE=
CALLMEBOT_API_KEY=
```

### 3. Run Check
```bash
python tracker.py
```

### 4. Run Automated Test Suite
```bash
python -m unittest discover -s tests -v
python -m unittest test_tracker.py -v
```
All automated unit tests run against offline mocks with zero external API calls.

---

## 24/7 Cloud Automation (GitHub Actions)

Deploying background monitoring on GitHub Actions:

1. Fork or push this repository to your GitHub account.
2. Navigate to **Settings** -> **Secrets and variables** -> **Actions**.
3. Add the repository secrets:
   * `PNR_NUMBER`: 10-digit PNR numbers (comma-separated).
   * `NTFY_TOPIC`: Private ntfy channel topic (e.g. `user-train-pnr-alerts`).
   * *(Optional)* `RAPIDAPI_KEY`, `WHATSAPP_PHONE`, `CALLMEBOT_API_KEY`.
4. Navigate to the **Actions** tab and enable workflows.

The cloud runner wakes up every 5 hours, inspects the tickets, delivers notifications upon status improvement, and securely caches state between runs without leaking passenger details into git history.

---

## Live Web Dashboard Preview

Launch the dark-mode web monitoring dashboard locally:

```bash
pip install fastapi uvicorn
python web_dashboard.py
```
Open `http://localhost:8000` in your browser to view real-time ticket statuses, coach allocations, and diff history.

---

## Project Structure

```
├── .github/workflows/
│   └── pnr_monitor.yml       # 24/7 GitHub Actions cron scheduler & CI
├── docs/                     # Software specification suite
│   ├── ARCHITECTURE.md       # High-level architecture and boundaries
│   ├── PRD.md                # Product requirements & problem statement
│   ├── DESIGN.md             # Component contracts & data flow
│   ├── SECURITY.md           # Threat modeling & secret management
│   └── TEST_PLAN.md          # Test strategy & mock verification
├── tests/
│   └── test_status_rules.py  # Deterministic regex status unit tests
├── pnr_client.py             # Dual-gateway rail API client
├── notifier.py               # Multi-channel notification adapter
├── tracker.py                # Core diff engine & atomic state manager
├── web_dashboard.py          # FastAPI + Tailwind local monitoring UI
├── test_tracker.py           # Integration & multi-passenger test suite
└── requirements.txt          # Python dependencies
```

---

## Security and Privacy

* **Zero Public Leakage**: State caches and runtime JSON are untracked in `.gitignore` to prevent travel details from being logged in git commits.
* **Secret Protection**: API tokens and phone numbers are managed through environment variables and GitHub Secrets.

---

## License

Distributed under the **MIT License**. See `LICENSE` for details.
