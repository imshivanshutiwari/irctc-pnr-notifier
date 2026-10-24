# RailPulse Security & Hardening Report

## 1. Threat Profile & Boundaries

RailPulse is designed as a secure, local-first railway telemetry monitor and alerting daemon.
- Bind Address: `127.0.0.1` (localhost only). Never exposed to public internet without authenticated reverse proxy.
- Outbound Destinations:
  - `api.confirmtkt.com` (HTTPS, read-only status query)
  - `irctc1.p.rapidapi.com` (HTTPS, read-only status query)
  - `ntfy.sh` (HTTPS, push alerts)
  - `api.telegram.org` (HTTPS, Telegram bot API)
- Persistence: Local filesystem `status_state.json` and `archived_pnrs.json`.

---

## 2. Secrets Management & Git History Audit

| Credential | Tracked in Git? | Environment Variable | Status |
|---|---|---|---|
| RAPIDAPI_KEY | No (`.env` in `.gitignore`) | `RAPIDAPI_KEY` | Secured locally |
| NTFY_TOPIC | No | `NTFY_TOPIC` | Topic redacted from API output |
| TELEGRAM_BOT_TOKEN | No | `TELEGRAM_BOT_TOKEN` | Optional, unset by default |
| TELEGRAM_CHAT_ID | No | `TELEGRAM_CHAT_ID` | Optional, unset by default |
| WHATSAPP / CALLMEBOT | No | `CALLMEBOT_API_KEY` | Optional, unset by default |

### Hardening Applied
1. Git full-history inspection (`git log --all --full-history -- .env`) confirmed `.env` has NEVER been committed to git.
2. Verified `.gitignore` actively ignores `.env`, `.env.*`, `status_state.json`, `archived_pnrs.json`, `.last_poll_state.json`, and bytecode caches.
3. Verified `.env.example` contains placeholders only with zero real keys or tokens.
4. Telemetry endpoint `/api/status` returns boolean configuration flags (`ntfy_configured`, `telegram_configured`) rather than leaking actual secret topic strings or tokens to the browser.
5. All hardcoded mock tickets and dummy PNRs were purged from backend route handlers.

---

## 3. Input Validation & Injection Hardening

1. **PNR Validation:**
   - Enforces strict 10-digit numerical constraint (`len == 10 and isdigit()`).
   - Rejects empty, non-digit, or oversized strings with HTTP 422 Unprocessable Entity.
   - Strips hyphens and leading/trailing whitespace safely.

2. **Command / SQL Injection:**
   - No SQL databases are utilized; state is stored in structured JSON.
   - Zero `eval()`, `exec()`, or untrusted shell invocations exist in the codebase.

3. **Path Traversal Protection:**
   - All state file operations reference explicit paths anchored to `os.path.dirname(__file__)` or temporary directories during testing.
   - Static asset serving uses FastAPI's `StaticFiles` mounted securely on `/static`.

4. **Cross-Site Scripting (XSS):**
   - Frontend renders ticket telemetry using standard DOM property assignments and template literals.
   - PNR numbers, coach labels, and station codes are sanitized and validated before DOM insertion.

---

## 4. Operational Safety & Denial-of-Service Defense

1. **Atomic State File Operations:**
   - `PNRTracker.save_all_states()` writes to a temporary file via `tempfile.NamedTemporaryFile` in the same directory, followed by atomic `os.replace`.
   - Protects against power outages, crashes, and concurrency race conditions.

2. **Spam & Notification Flooding Defense:**
   - `archived_pnrs.json` persists completed journeys so that trains arriving at their destination are permanently marked.
   - A strict 6-hour alert suppression window ensures historical tickets never trigger repeated notifications.

3. **Autonomous Polling Adaptive Cadence:**
   - Per-PNR adaptive scheduling ensures low network overhead: tickets > 2 days away are queried once every 5 hours; tickets within 2 days of journey are queried every 2 hours.
