# RailPulse Test Report

## 1. Overview

- **Test Framework:** pytest 8.2.0 (compatible with Python standard library `unittest`)
- **Total Tests:** 18
- **Passing:** 18
- **Failing:** 0
- **Duration:** 2.27s
- **Network Access During Tests:** None (100% isolated unit mocks and temporary directory state files)

---

## 2. Test Breakdown

### Test File: `test_tracker.py` (9 Tests)
1. `test_first_run_records_baseline_and_alerts` - Verifies initial state baseline creation and opt-in first run alerting.
2. `test_waiting_list_drop_triggers_alert` - Verifies detection of genuine WL improvements (e.g. RLWL 10 -> RLWL 9).
3. `test_no_change_does_not_alert` - Proves identical status polling suppresses duplicate alert delivery.
4. `test_promotion_to_rac_and_cnf` - Verifies multi-passenger status advancement from WL to RAC and CNF.
5. `test_message_formatter_content` - Validates alert structure, formatting tags, and absence of synthetic text.
6. `test_multi_pnr_tracking` - Validates fleet monitoring across multiple PNRs in a single pass.
7. `test_invalid_pnr_rejected_at_construction` - Rejects short, alphanumeric, or oversized PNR numbers.
8. `test_empty_passenger_list_does_not_alert` - Verifies malformed/empty passenger responses raise RuntimeError and retain prior state.
9. `test_degraded_status_does_not_trigger_alert` - Confirms that waitlist regression (e.g. GNWL 5 -> GNWL 8) does not send false positive improvement alerts.

### Test File: `tests/test_status_rules.py` (9 Tests)
1. `test_classification` - Checks regex categorization of GNWL, RLWL, RAC, and CNF strings.
2. `test_only_improvements_alert` - Validates directional improvement logic across all status classes.
3. `test_failed_alert_keeps_previous_state_for_retry` - Ensures delivery failures retain previous state for automatic retry on next poll.
4. `test_corrupt_state_is_not_silently_reset` - Verifies malformed JSON on disk triggers errors instead of silently erasing state.
5. `test_pnr_validation_and_deduplication` - Tests comma-separated PNR splitting and duplicate removal.
6. `test_known_code_lookup` - Verifies exact station code match (NDLS -> New Delhi / नई दिल्ली).
7. `test_unknown_code_returns_passthrough` - Ensures unmapped codes degrade safely without exceptions.
8. `test_name_lookup_falls_back_correctly` - Checks reverse lookup from full station name to code and Hindi label.
9. `test_junction_suffix_fallback_transliteration` - Verifies automated suffix recognition for Junction/Cantt stations.

---

## 3. Test Runner Output Evidence

```
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-8.2.0, pluggy-1.6.0 -- C:\Program Files\Python310\python.exe
cachedir: .pytest_cache
rootdir: E:\irctc-pnr-notifier
plugins: anyio-4.15.1, dash-4.0.0, langsmith-0.7.22, requests-mock-1.12.1
collecting ... collected 18 items

test_tracker.py::TestPNRTracker::test_degraded_status_does_not_trigger_alert PASSED [  5%]
test_tracker.py::TestPNRTracker::test_empty_passenger_list_does_not_alert PASSED [ 11%]
test_tracker.py::TestPNRTracker::test_first_run_records_baseline_and_alerts PASSED [ 16%]
test_tracker.py::TestPNRTracker::test_invalid_pnr_rejected_at_construction PASSED [ 22%]
test_tracker.py::TestPNRTracker::test_message_formatter_content PASSED   [ 27%]
test_tracker.py::TestPNRTracker::test_multi_pnr_tracking PASSED          [ 33%]
test_tracker.py::TestPNRTracker::test_no_change_does_not_alert PASSED    [ 38%]
test_tracker.py::TestPNRTracker::test_promotion_to_rac_and_cnf PASSED    [ 44%]
test_tracker.py::TestPNRTracker::test_waiting_list_drop_triggers_alert PASSED [ 50%]
tests/test_status_rules.py::TestStatusRules::test_classification PASSED  [ 55%]
tests/test_status_rules.py::TestStatusRules::test_corrupt_state_is_not_silently_reset PASSED [ 61%]
tests/test_status_rules.py::TestStatusRules::test_failed_alert_keeps_previous_state_for_retry PASSED [ 66%]
tests/test_status_rules.py::TestStatusRules::test_only_improvements_alert PASSED [ 72%]
tests/test_status_rules.py::TestStatusRules::test_pnr_validation_and_deduplication PASSED [ 77%]
tests/test_status_rules.py::TestStationsModule::test_junction_suffix_fallback_transliteration PASSED [ 83%]
tests/test_status_rules.py::TestStationsModule::test_known_code_lookup PASSED [ 88%]
tests/test_status_rules.py::TestStationsModule::test_name_lookup_falls_back_correctly PASSED [ 94%]
tests/test_status_rules.py::TestStationsModule::test_unknown_code_returns_passthrough PASSED [100%]

============================= 18 passed in 2.27s ==============================
```
