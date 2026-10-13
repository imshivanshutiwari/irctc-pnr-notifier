# Security Architecture and Audit Checklist

This document details the security posture of RailPulse, identifying implemented controls and clarifying out-of-scope enterprise web paradigms.

---

## 1. Implemented Security Controls

### Control 1: Server-Side Secret Isolation (Checklist Item 8)
* All credentials (`RAPIDAPI_KEY`, `WHATSAPP_PHONE`, `CALLMEBOT_API_KEY`, `TELEGRAM_BOT_TOKEN`, `NTFY_TOPIC`) are stored exclusively in ignored `.env` files locally or encrypted GitHub Actions Secrets in CI.
* No API keys or authorization headers exist in repository files or commit history.
* Secrets are accessed via environment variables at runtime only.

### Control 2: Sensitive Data and PNR Log Scrubbing (Checklist Item 19)
* Terminal and GitHub Actions logs mask active PNRs (`******1979`) during execution to prevent booking identities from appearing in build output.
* Runtime JSON states (`status_state.json`) are untracked in `.gitignore`.
* Cloud persistence utilizes private GitHub Actions Caching rather than public git commits.
* Passenger names are never collected, logged, or retained.

### Control 3: Input Validation and SSRF Prevention (Checklist Item 16)
* Every PNR input is strictly validated with regex and length constraints:
  ```python
  if len(pnr_clean) != 10 or not pnr_clean.isdigit():
      raise ValueError("Invalid 10-digit PNR format.")
  ```
* Dynamic URL redirection is prohibited; requests are hardcoded to whitelisted railway APIs (`api.confirmtkt.com` and `irctc1.p.rapidapi.com`).
* Path traversal sequences (`../`), scheme injections, and arbitrary host queries are rejected prior to network dispatch.

### Control 4: Rate Limiting and Timeout Safety (Checklist Item 6)
* Network requests have strict timeout thresholds (15-20 seconds) to prevent hanging worker threads.
* Multi-PNR checks enforce pacing delays (`time.sleep(1)`) between consecutive upstream queries to avoid bursting railway endpoints.
* Cloud polling is interval-gated (every 5 hours) to respect upstream service capacity.

### Control 5: Minimal Dependency Attack Surface (Checklist Item 20)
* Core production execution relies exclusively on two well-audited packages: `requests` and `python-dotenv`.
* No bloated native C-extensions or abandoned transitive packages.
* Automated CI runs execute unit tests before performing any live checks.

---

## 2. Clarification on Out-of-Scope Items

The following items from standard SaaS security audits do not apply to this architecture:

| SaaS Checklist Item | Reason Out-of-Scope |
|---|---|
| **SQL Injection (Item 1)** | RailPulse uses a stateless architecture with local/cache JSON storage. No SQL database (PostgreSQL, MySQL, SQLite) is present. |
| **Row-Level Security / RLS (Item 14)** | No relational database or Supabase/PostgREST engine is utilized. |
| **Password Hashing (Item 9) & MFA (Item 10)** | No user registration or authentication subsystem exists. The engine is self-hosted and credential-isolated per runner. |
| **JWT Secrets (Item 7) & Auth Tokens (Item 12)** | No session tokens or JSON Web Tokens are generated or stored. |
| **File Upload Validation (Item 4)** | The application accepts no binary, image, or document uploads. |
| **CORS & CSRF (Items 3, 11)** | The CLI and background runner operate headless in GitHub Actions without cross-origin browser endpoints. |
| **Broken Object-Level Authorization (Item 5)** | Single-tenant, self-hosted operational model. Multi-tenant access boundaries are not applicable. |

---

## 3. Incident Response and Rotation

If an external API key or topic name is inadvertently published:
1. Immediately rotate the credential with the provider (CallMeBot, Telegram, RapidAPI).
2. Update the encrypted secret in **Settings -> Secrets and variables -> Actions**.
3. Re-run tests to confirm authentication against the new secret.
