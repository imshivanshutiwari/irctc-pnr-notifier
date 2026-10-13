# SPEC.md — IRCTC PNR Waiting List WhatsApp Alert Automation

**Status: FINALIZED**  
**Version:** 1.0.0  
**Owner:** Shivanshu  
**Date:** 2026-10-13  

---

## 1. Problem Statement & Objective
When travelers book train tickets on Indian Railways (IRCTC) with a waiting list status (such as `RLWL 10`, `GNWL 25`), they frequently have to manually open IRCTC or enquiry apps to check if cancellations have moved their waiting list up. 

**Objective:** Build an autonomous, free 24/7 automation running in the cloud that checks a 10-digit IRCTC PNR every 5 hours and immediately sends a WhatsApp message to the traveler's mobile phone whenever the waiting list drops (e.g. `RLWL 10` → `RLWL 9`, or to `RAC`, or to `CNF`).

---

## 2. Requirements & Constraints

### 2.1 Functional Requirements
- **FR-1: PNR Polling**: Fetch real-time PNR status for a specified 10-digit PNR using a free-tier RapidAPI Indian Railway / IRCTC endpoint.
- **FR-2: Diff & Change Detection**: Compare each passenger's current status against the previously recorded status (`status_state.json`). Trigger an alert if and only if:
  - Waiting list position decreases (e.g. `RLWL 10` → `RLWL 9`)
  - Status improves to `RAC` (Reservation Against Cancellation)
  - Status confirms to `CNF` (Confirmed with Coach & Berth)
  - Any passenger status change occurs.
- **FR-3: WhatsApp Notification**: Deliver an instant, well-formatted WhatsApp alert to the user's mobile number containing:
  - Train Name / Number
  - Journey Date
  - Passenger ID / Name
  - Previous Status vs New Status
  - Confirmation status indicator (CNF for confirmed, WL drop for reduction)
- **FR-4: 24/7 Cloud Runner**: Automate execution via GitHub Actions with a cron schedule (`0 */5 * * *`) so it runs without keeping the user's laptop powered on. Support `workflow_dispatch` for on-demand trigger.
- **FR-5: State Persistence**: Persist current PNR state between runs so status changes are accurately tracked across scheduled intervals.
- **FR-6: Test / Simulation Mode**: Provide a test mode that can simulate waiting list movements (`RLWL 10` -> `RLWL 9` -> `CNF`) and test WhatsApp connectivity without waiting 5 hours.

### 2.2 Non-Functional Requirements
- **Cost**: 100% Free (GitHub Actions free minutes + RapidAPI free tier + CallMeBot free WhatsApp API).
- **Security**: Sensitive credentials (`PNR_NUMBER`, `RAPIDAPI_KEY`, `WHATSAPP_PHONE`, `CALLMEBOT_API_KEY`) configured via `.env` locally and GitHub Secrets in the cloud.
- **Reliability**: Graceful handling of API timeouts, network glitches, or temporary IRCTC server downtime without wiping existing state.

---

## 3. Architecture & Data Flow

```
[GitHub Actions Cron (Every 5h)] OR [Local CLI]
             │
             ▼
   [fetch_pnr_status()] ──► RapidAPI IRCTC Endpoint
             │
             ▼
   [compare_status()]  ◄──► Read/Write status_state.json
             │
      (Has Status Changed?)
        ├── NO  ──► Exit cleanly
        └── YES ──► [send_whatsapp()] ──► CallMeBot API ──► User WhatsApp
```

---

## 4. Acceptance Criteria
1. Script queries PNR status and extracts passenger-level current status.
2. Script detects when `RLWL` decreases or status becomes `RAC`/`CNF`.
3. Script formats and sends WhatsApp message via CallMeBot API.
4. GitHub Actions workflow (`.github/workflows/pnr_monitor.yml`) is configured for 5-hour cron.
5. Unit and mock tests pass verifying status transition detection and WhatsApp dispatch logic.
