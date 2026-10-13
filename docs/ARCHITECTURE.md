# Architecture

## MVP components
- `pnr_client.py`: fetches provider data and normalizes it into a stable schema.
- `tracker.py`: validates configured PNRs, loads state, classifies transitions, and coordinates alerts.
- `notifier.py`: dispatches messages to configured ntfy, WhatsApp, and Telegram adapters.
- GitHub Actions: scheduled runner and test execution.
- Runtime state JSON: private and never committed to the repository.

## Data flow
Scheduled workflow or CLI -> PNR client -> response normalization -> transition rules -> notifier -> private state persistence.

## Boundaries
- Provider-specific response parsing belongs in `pnr_client.py`.
- Status classification must be deterministic and unit-tested.
- Credentials are environment variables / GitHub Actions secrets only.
- A notification is successful only when the notifier reports success.
- State writes must be atomic; malformed state must stop the run rather than reset the baseline.

## State persistence
The workflow caches the state file between runs and explicitly refuses to run in a public repository. GitHub Actions caches are an operational compromise, not a database: cache availability/retention is not guaranteed. For stronger guarantees, use a private durable database or private state service and test restore/write behavior.
