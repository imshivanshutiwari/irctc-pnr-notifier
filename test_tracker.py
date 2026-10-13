"""
test_tracker.py — Automated verification test suite for IRCTC PNR Tracker.
Tests:
1. Baseline state initialization
2. Waiting list reduction detection (e.g., RLWL 10 -> RLWL 9)
3. No-change scenario (no spurious alert)
4. Promotion to RAC and CNF
5. Message formatting integrity
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
        if os.path.exists(TEST_STATE_FILE):
            os.remove(TEST_STATE_FILE)

    def tearDown(self):
        if os.path.exists(TEST_STATE_FILE):
            os.remove(TEST_STATE_FILE)

    def test_first_run_records_baseline_and_alerts(self):
        initial_mock = {
            "train_number": "12952",
            "train_name": "MUMBAI RAJDHANI",
            "date_of_journey": "25-10-2026",
            "from_station": "NDLS",
            "to_station": "MMCT",
            "passengers": [
                {"passenger_number": 1, "booking_status": "RLWL 15", "current_status": "RLWL 10"}
            ]
        }
        client = PNRClient(mock_data=initial_mock)
        notifier = Notifier(dry_run=True)
        tracker = PNRTracker(
            pnr="2456789012",
            client=client,
            notifier=notifier,
            state_file=TEST_STATE_FILE,
            notify_on_first_run=True
        )

        alerted, msg = tracker.check_once()
        self.assertTrue(alerted)
        self.assertIn("Baseline recorded", msg)
        self.assertTrue(os.path.exists(TEST_STATE_FILE))

        # Check saved state
        with open(TEST_STATE_FILE, "r") as f:
            saved = json.load(f)
            self.assertEqual(saved["passengers"][0]["current_status"], "RLWL 10")

    def test_waiting_list_drop_triggers_alert(self):
        # 1. First run: RLWL 10
        baseline_mock = {
            "train_number": "12952",
            "train_name": "MUMBAI RAJDHANI",
            "date_of_journey": "25-10-2026",
            "passengers": [
                {"passenger_number": 1, "booking_status": "RLWL 15", "current_status": "RLWL 10"}
            ]
        }
        client = PNRClient(mock_data=baseline_mock)
        notifier = Notifier(dry_run=True)
        tracker = PNRTracker(
            pnr="2456789012",
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
            "date_of_journey": "25-10-2026",
            "passengers": [
                {"passenger_number": 1, "booking_status": "RLWL 15", "current_status": "RLWL 9"}
            ]
        }
        tracker.client = PNRClient(mock_data=updated_mock)
        changed, msg = tracker.check_once()

        self.assertTrue(changed)
        self.assertIn("Status changed for 1 passenger", msg)

        # Check updated state
        with open(TEST_STATE_FILE, "r") as f:
            saved = json.load(f)
            self.assertEqual(saved["passengers"][0]["current_status"], "RLWL 9")

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
            pnr="2456789012",
            client=client,
            notifier=notifier,
            state_file=TEST_STATE_FILE,
            notify_on_first_run=False
        )
        tracker.check_once()

        # Check again with same status
        changed, msg = tracker.check_once()
        self.assertFalse(changed)
        self.assertEqual(msg, "No status change.")

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
            pnr="2456789012",
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
        self.assertIn("Status changed for 2 passenger(s)", msg)

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
        self.assertIn("RLWL 10 ➔ *RLWL 9*", msg)
        self.assertIn("WL Reduced!", msg)
        self.assertIn("CONFIRMED!", msg)

if __name__ == "__main__":
    unittest.main()
