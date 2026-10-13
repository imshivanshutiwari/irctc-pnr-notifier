# Test Plan

## Status classification
- Parse GNWL, RLWL, PQWL, RQWL, TQWL, WL, W/L, RAC, and CNF.
- Unknown values remain unknown.
- A smaller waitlist number in the same category is an improvement.
- Do not compare positions across different waitlist categories.
- A transition to RAC/CNF is an improvement; CNF-to-CNF metadata changes are not.

## Failure behavior
- Provider exceptions do not overwrite stored state.
- Empty/malformed passenger data does not overwrite stored state.
- Failed notification preserves the previous state so a later run can retry.
- Corrupt JSON state fails visibly and does not reset to an empty baseline.
- State writes replace the file atomically.

## Configuration and privacy
- Invalid PNR input is rejected.
- Duplicate PNR values are deduplicated.
- No test uses live API credentials or sends external notifications.
- Workflow uses secrets rather than hard-coded PNRs or keys.

## Commands
`python -m unittest discover -s tests -v`
