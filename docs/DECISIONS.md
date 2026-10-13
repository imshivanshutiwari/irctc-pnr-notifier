# Architecture Decisions

## ADR-001 — Keep the current Python engine
Decision: retain the current Python CLI and provider/notifier modules for the reliability release.
Reason: the current scope is security and correctness, not a rewrite.

## ADR-002 — Do not commit live state
Decision: runtime PNR state must not be stored in a public repository.
Reason: the state includes travel dates, routes, and ticket status.

## ADR-003 — Alert on meaningful improvements
Decision: alert only on a lower position in the same waitlist category, movement to RAC, movement to CNF, and lower RAC position.
Reason: arbitrary status text changes can be corrections or non-improvements.

## ADR-004 — Failed alert does not advance baseline
Decision: preserve the prior state when delivery of an improvement alert fails.
Reason: the next run must be able to retry the same transition.
