# RailPulse Security & Hardening Report

## 1. Threat Profile & Boundaries

RailPulse is designed as a local-first railway telemetry monitor and alerting server.
- Bind Address: `127.0.0.1` (localhost only). Never exposed to public internet without reverse proxy and authentication.
- Outbound Destinations:
  - `api.confirmtkt.com` (HTTPS, read-only status query)
  - `irctc1.p.rapidapi.com` (HTTPS, read-only status query)
  - `ntfy.sh` (HTTPS, push alerts)
  - `api.telegram.org` (HTTPS, Telegram bot API)
- Persistence: Local filesystem `status_state.json`.

---

## 2. Secrets Management Audit

| Credential | Tracked in Git? | Environment Variable | Status |
|---|---|---|---|
| RAPIDAPI_KEY | No (`.env` in `.gitignore`) | `RAPIDAPI_KEY` | Secured locally |
| NTFY_TOPIC | No | `NTFY_TOPIC` | Topic redacted from API output |
| TELEGRAM_BOT_TOKEN | No | `TELEGRAM_BOT_TOKEN` | Optional, unset by default |
| TELEGRAM_CHAT_ID | No | `TELEGRAM_CHAT_ID` | Optional, unset by default |
| WHATSAPP / CALLMEBOT | No | `CALLMEBOT_API_KEY` | Optional, unset by default |

### Hardening Applied
1. Verified that `.env` is ignored by git and has never been committed into repository revision history.
2. Verified `.env.example` contains placeholders only with safe descriptions.
3. Removed internal `ntfy_topic` value from `/api/status` telemetry responses to avoid leaking topic endpoints to external clients or browser devtools.

---

## 3. Input Validation & Injection Risks

1. **PNR Validation:**
   - Enforces strict 10-digit numerical constraint (`re.compile` or length + `.isdigit()` check).
   - Rejects empty, non-digit, or oversized strings with HTTP 422 Unprocessable Entity.
   - Normalizes hyphens and surrounding whitespace.

2. **Command / SQL Injection:**
   - No SQL databases are utilized; state is stored in structured JSON.
   - No `eval()`, `exec()`, or untrusted `subprocess` invocations exist in codebase.

3. **Path Traversal:**
   - All state file operations reference fixed paths resolved via `os.path.dirname(__file__)` or standard library `tempfile`.
   - Static asset serving uses FastAPI's `StaticFiles` mounted securely on `/static`.

4. **Cross-Site Scripting (XSS):**
   - Frontend renders railway ticket telemetry using standard DOM property updates and numeric formatting.
   - PNR numbers and station strings are sanitized and length-bounded before insertion into dashboard templates.

---

## 4. State File Atomicity & Concurrency

State synchronization uses atomic write replacements to prevent race conditions or partial file corruption during system crashes or power interruptions:
1. Data is written to a unique temporary file (`NamedTemporaryFile`) on the same filesystem partition.
2. Changes are flushed and forced to disk with `os.fsync(handle.fileno())`.
3. The temporary file replaces `status_state.json` via atomic OS-level rename (`os.replace`).
4. Read failures due to malformed JSON raise structured `RuntimeError` rather than silently clearing user state.
