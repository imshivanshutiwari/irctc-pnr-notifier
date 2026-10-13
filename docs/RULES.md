# Development Rules

## Before coding
1. Read `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/TEST_PLAN.md`, and `TASKS.md`.
2. Inspect existing code and reuse its provider and notifier adapters.
3. Propose a small plan before broad changes.

## Code
- Keep provider parsing, transition rules, persistence, and delivery separated.
- Do not add unrelated frameworks or rewrite working components without evidence.
- Validate PNRs as exactly 10 digits.
- Treat provider responses as untrusted input.
- Do not log complete PNRs, tokens, or API keys.
- Never hard-code credentials or personal PNRs.
- State updates must be atomic and must not discard the previous valid state on errors.
- Notification delivery failures must be observable and retryable.

## Tests
- Mock provider and notification calls.
- Test both positive and negative transitions.
- Run `python -m unittest discover -s tests -v` before declaring success.
- Do not claim tests passed unless they were actually executed.

## Git
- Work on a feature/fix branch.
- Keep changes small and reviewable.
- Do not force-push or rewrite history without explicit approval.
