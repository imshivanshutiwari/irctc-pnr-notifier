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

### Phase 4: Full-Fledged Project Polish & Architecture Upgrade (GitHub & LinkedIn Showcase)
- **Goal:** Elevate codebase into an enterprise-grade open-source project with deterministic transition rules, private state caching, rich documentation, test automation, and web dashboard.
- **Tasks:**
  - Task 4.1: Merge Documentation Suite (`docs/`: `ARCHITECTURE.md`, `PRD.md`, `DESIGN.md`, `SECURITY.md`, `TEST_PLAN.md`, `DECISIONS.md`, `RULES.md`).
  - Task 4.2: Integrate regex-based status classification, atomic state persistence, and retry safety into `tracker.py`.
  - Task 4.3: Add `tests/test_status_rules.py` and verify all 11 unit tests pass across both suites.
  - Task 4.4: Configure GitHub Secrets (`PNR_NUMBER`, `NTFY_TOPIC`) and update `.gitignore` + `.github/workflows/pnr_monitor.yml` with private Actions cache.
  - Task 4.5: Design portfolio-grade `README.md`, MIT license, and web dashboard.
