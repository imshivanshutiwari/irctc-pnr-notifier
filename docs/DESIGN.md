# Product and Notification Design

This is a CLI-first monitoring utility rather than a web application.

## Notification content
- Identify the PNR only as needed; logs should mask it to the final four digits.
- Include train number/name, journey date, passenger index, old status, and new status when available.
- Avoid passenger names unless a provider and user requirement explicitly need them.
- State that railway status is provider-reported and can change; final chart status is authoritative.

## UX / operational behavior
- Missing configuration fails with a clear message.
- Fetch failure is visible and must not be interpreted as a status transition.
- Notification failure preserves the old baseline for retry.
- Dry-run mode must not call external notification services.
