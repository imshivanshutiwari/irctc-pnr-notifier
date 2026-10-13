# ROADMAP.md — IRCTC PNR Waiting List Automation

## Phases

### Phase 1: Core Engine Implementation
- **Goal:** Build the PNR status fetcher, diff comparator, and WhatsApp notification module.
- **Tasks:**
  - Task 1.1: Create `notifier.py` supporting WhatsApp (via CallMeBot) and console fallback.
  - Task 1.2: Create `pnr_client.py` to query Indian Railway / RapidAPI PNR status with clean error handling.
  - Task 1.3: Create `tracker.py` to manage state persistence (`status_state.json`) and detect waiting list reductions (e.g. RLWL 10 -> RLWL 9, RAC, CNF).

### Phase 2: Verification & Test Suite
- **Goal:** Verify change detection, diff logic, and notification generation via automated tests.
- **Tasks:**
  - Task 2.1: Write unit tests `test_tracker.py` testing waiting list transitions, no-change scenarios, and multiple passenger tickets.
  - Task 2.2: Execute test suite and capture empirical proof.

### Phase 3: Cloud 24/7 Automation & Documentation
- **Goal:** Configure GitHub Actions cron runner (runs every 5 hours for free), environment templates, and documentation.
- **Tasks:**
  - Task 3.1: Create `.github/workflows/pnr_monitor.yml` with 5-hour cron schedule and artifact/commit state persistence.
  - Task 3.2: Create `.env.example`, `requirements.txt`, and comprehensive `README.md` with step-by-step CallMeBot setup and GitHub Actions deployment instructions.
