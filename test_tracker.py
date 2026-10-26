"""
test_tracker.py - Automated verification test suite for IRCTC PNR Tracker.
Tests:
1. Baseline state initialization
2. Waiting list reduction detection (e.g., RLWL 10 -> RLWL 9)
3. No-change scenario (no spurious alert)
4. Promotion to RAC and CNF
5. Message formatting integrity
6. Multi-PNR concurrent tracking
"""

import os
import json
import unittest
from notifier import Notifier
from pnr_client import PNRClient
from tracker import PNRTracker

TEST_STATE_FILE = "test_status_state.json"

class TestPNRTracker(unittest.TestCase):
    def setUp(self):
        for f in (TEST_STATE_FILE, f"archived_{TEST_STATE_FILE}"):
            if os.path.exists(f):
                os.remove(f)

    def tearDown(self):
        for f in (TEST_STATE_FILE, f"archived_{TEST_STATE_FILE}"):
            if os.path.exists(f):
                os.remove(f)

    def test_first_run_records_baseline_and_alerts(self):
        initial_mock = {
            "train_number": "12952",
            "train_name": "MUMBAI RAJDHANI",
            "date_of_journey": "25-10-2027",
            "from_station": "NDLS",
            "to_station": "MMCT",
            "passengers": [
                {"passenger_number": 1, "booking_status": "RLWL 15", "current_status": "RLWL 10"}
            ]
        }
        client = PNRClient(mock_data=initial_mock)
        notifier = Notifier(dry_run=True)
        tracker = PNRTracker(
            pnrs="2456789012",
            client=client,
            notifier=notifier,
            state_file=TEST_STATE_FILE,
            notify_on_first_run=True
        )

        alerted, msg = tracker.check_once()
        self.assertTrue(alerted)
        self.assertIn("Baseline saved for PNR", msg)
        self.assertTrue(os.path.exists(TEST_STATE_FILE))

        # Check saved state
        with open(TEST_STATE_FILE, "r") as f:
            saved = json.load(f)
            pnr_state = saved.get("2456789012", saved)
            self.assertEqual(pnr_state["passengers"][0]["current_status"], "RLWL 10")

    def test_waiting_list_drop_triggers_alert(self):
        # 1. First run: RLWL 10
        baseline_mock = {
            "train_number": "12952",
            "train_name": "MUMBAI RAJDHANI",
            "date_of_journey": "25-10-2027",
            "passengers": [
                {"passenger_number": 1, "booking_status": "RLWL 15", "current_status": "RLWL 10"}
            ]
        }
        client = PNRClient(mock_data=baseline_mock)
        notifier = Notifier(dry_run=True)
        tracker = PNRTracker(
            pnrs="2456789012",
            client=client,
            notifier=notifier,
            state_file=TEST_STATE_FILE,
            notify_on_first_run=False
        )
        tracker.check_once()

        # 2. Second run: Waiting list dropped to RLWL 9!
        updated_mock = {
            "train_number": "12952",
            "train_name": "MUMBAI RAJDHANI",
            "date_of_journey": "25-10-2027",
            "passengers": [
                {"passenger_number": 1, "booking_status": "RLWL 15", "current_status": "RLWL 9"}
            ]
        }
        tracker.client = PNRClient(mock_data=updated_mock)
        changed, msg = tracker.check_once()

        self.assertTrue(changed)
        self.assertIn("Status changed for PNR 2456789012", msg)

        # Check updated state
        with open(TEST_STATE_FILE, "r") as f:
            saved = json.load(f)
            pnr_state = saved.get("2456789012", saved)
            self.assertEqual(pnr_state["passengers"][0]["current_status"], "RLWL 9")

    def test_no_change_does_not_alert(self):
        baseline_mock = {
            "train_number": "12952",
            "passengers": [
                {"passenger_number": 1, "booking_status": "RLWL 15", "current_status": "RLWL 9"}
            ]
        }
        client = PNRClient(mock_data=baseline_mock)
        notifier = Notifier(dry_run=True)
        tracker = PNRTracker(
            pnrs="2456789012",
            client=client,
            notifier=notifier,
            state_file=TEST_STATE_FILE,
            notify_on_first_run=False
        )
        tracker.check_once()

        # Check again with same status
        changed, msg = tracker.check_once()
        self.assertFalse(changed)
        self.assertIn("No change for PNR 2456789012", msg)

    def test_promotion_to_rac_and_cnf(self):
        baseline_mock = {
            "train_number": "12952",
            "passengers": [
                {"passenger_number": 1, "current_status": "RLWL 1"},
                {"passenger_number": 2, "current_status": "RLWL 2"}
            ]
        }
        client = PNRClient(mock_data=baseline_mock)
        notifier = Notifier(dry_run=True)
        tracker = PNRTracker(
            pnrs="2456789012",
            client=client,
            notifier=notifier,
            state_file=TEST_STATE_FILE,
            notify_on_first_run=False
        )
        tracker.check_once()

        # Both get promoted: P1 to RAC 5, P2 to CNF B3 45
        updated_mock = {
            "train_number": "12952",
            "passengers": [
                {"passenger_number": 1, "current_status": "RAC 5"},
                {"passenger_number": 2, "current_status": "CNF / B3 / 45"}
            ]
        }
        tracker.client = PNRClient(mock_data=updated_mock)
        changed, msg = tracker.check_once()

        self.assertTrue(changed)
        self.assertIn("Status changed for PNR 2456789012", msg)

    def test_message_formatter_content(self):
        notifier = Notifier(dry_run=True)
        train_info = {
            "train_number": "12004",
            "train_name": "LUCKNOW SHATABDI",
            "date_of_journey": "28-10-2026",
            "from_station": "NDLS",
            "to_station": "LKO"
        }
        changes = [
            {"passenger": "Passenger 1", "old_status": "RLWL 10", "new_status": "RLWL 9"},
            {"passenger": "Passenger 2", "old_status": "RLWL 11", "new_status": "CNF"}
        ]
        msg = notifier.format_alert_message("1234567890", train_info, changes, train_info)

        self.assertIn("1234567890", msg)
        self.assertIn("LUCKNOW SHATABDI", msg)
        self.assertIn("RLWL 10 -> *RLWL 9*", msg)
        self.assertIn("WL Reduced!", msg)
        self.assertIn("CONFIRMED!", msg)

    def test_multi_pnr_tracking(self):
        mock_data = {
            "train_number": "12791",
            "passengers": [{"passenger_number": 1, "current_status": "RLWL 8"}]
        }
        client = PNRClient(mock_data=mock_data)
        notifier = Notifier(dry_run=True)
        tracker = PNRTracker(
            pnrs="1111111111, 2222222222, 3333333333",
            client=client,
            notifier=notifier,
            state_file=TEST_STATE_FILE,
            notify_on_first_run=False
        )
        self.assertEqual(len(tracker.pnrs), 3)
        alerted, msg = tracker.check_once()
        self.assertFalse(alerted)

        with open(TEST_STATE_FILE, "r") as f:
            saved = json.load(f)
            self.assertIn("1111111111", saved)
            self.assertIn("2222222222", saved)
            self.assertIn("3333333333", saved)

    def test_invalid_pnr_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            PNRTracker(pnrs="123")
        with self.assertRaises(ValueError):
            PNRTracker(pnrs="ABCDE12345")
        with self.assertRaises(ValueError):
            PNRTracker(pnrs="12345678901")

    def test_empty_passenger_list_does_not_alert(self):
        """Upstream returning empty passengers must not produce a spurious alert and must retain previous state."""
        baseline_mock = {
            "train_number": "12952",
            "passengers": [
                {"passenger_number": 1, "booking_status": "RLWL 5", "current_status": "RLWL 5"}
            ]
        }
        client = PNRClient(mock_data=baseline_mock)
        notifier = Notifier(dry_run=True)
        tracker = PNRTracker(
            pnrs="2456789012",
            client=client,
            notifier=notifier,
            state_file=TEST_STATE_FILE,
            notify_on_first_run=False
        )
        tracker.check_once()

        # Upstream returns empty passenger list
        empty_mock = {"train_number": "12952", "passengers": []}
        tracker.client = PNRClient(mock_data=empty_mock)
        with self.assertRaises(RuntimeError) as ctx:
            tracker.check_once()

        self.assertIn("No valid passenger data", str(ctx.exception))
        # Ensure previous state was not overwritten by empty response
        with open(TEST_STATE_FILE, "r") as f:
            saved = json.load(f)
            self.assertEqual(saved["2456789012"]["passengers"][0]["current_status"], "RLWL 5")

    def test_degraded_status_does_not_trigger_alert(self):
        """WL position getting worse (higher number) must not trigger an alert."""
        baseline_mock = {
            "train_number": "12952",
            "passengers": [{"passenger_number": 1, "booking_status": "GNWL 5", "current_status": "GNWL 5"}]
        }
        client = PNRClient(mock_data=baseline_mock)
        notifier = Notifier(dry_run=True)
        tracker = PNRTracker(
            pnrs="2456789012",
            client=client,
            notifier=notifier,
            state_file=TEST_STATE_FILE,
            notify_on_first_run=False
        )
        tracker.check_once()

        worse_mock = {
            "train_number": "12952",
            "passengers": [{"passenger_number": 1, "booking_status": "GNWL 5", "current_status": "GNWL 8"}]
        }
        tracker.client = PNRClient(mock_data=worse_mock)
        alerted, msg = tracker.check_once()
        self.assertFalse(alerted)


if __name__ == "__main__":
    unittest.main()
