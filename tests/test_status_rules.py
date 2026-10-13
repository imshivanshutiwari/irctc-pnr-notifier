import json
import tempfile
import unittest
from pathlib import Path

from tracker import PNRTracker, classify_status, is_improvement
from pnr_client import PNRClient


class RecordingNotifier:
    def __init__(self, succeeds=True):
        self.succeeds = succeeds
        self.messages = []

    def format_alert_message(self, pnr, train_info, changes, current_state):
        return f"{pnr}: {changes}"

    def send_alert(self, message):
        self.messages.append(message)
        return self.succeeds


class TestStatusRules(unittest.TestCase):
    def test_classification(self):
        self.assertEqual(classify_status("RLWL 10"), ("RLWL", 10))
        self.assertEqual(classify_status("W/L 22,RLGN"), ("WL", 22))
        self.assertEqual(classify_status("RAC 5"), ("RAC", 5))
        self.assertEqual(classify_status("CNF / B3 / 45"), ("CNF", None))
        self.assertEqual(classify_status("unknown"), ("UNKNOWN", None))

    def test_only_improvements_alert(self):
        self.assertTrue(is_improvement("RLWL 10", "RLWL 9"))
        self.assertTrue(is_improvement("GNWL 3", "RAC 2"))
        self.assertTrue(is_improvement("RAC 2", "CNF B3 45"))
        self.assertFalse(is_improvement("RLWL 9", "RLWL 10"))
        self.assertFalse(is_improvement("GNWL 10", "RLWL 2"))
        self.assertFalse(is_improvement("CNF B3 45", "CNF B3 46"))
        self.assertFalse(is_improvement("unknown", "RLWL 2"))
        self.assertFalse(is_improvement("RLWL 10", "unknown"))

    def test_failed_alert_keeps_previous_state_for_retry(self):
        pnr = "1234567890"
        old = {"pnr": pnr, "passengers": [{"passenger_number": 1, "current_status": "RLWL 10"}]}
        current = {"pnr": pnr, "passengers": [{"passenger_number": 1, "current_status": "RLWL 9"}]}
        notifier = RecordingNotifier(succeeds=False)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text(json.dumps({pnr: old}), encoding="utf-8")
            tracker = PNRTracker(pnrs=pnr, client=PNRClient(mock_data=current),
                                 notifier=notifier, state_file=str(path))
            _, message = tracker.check_pnr(pnr, tracker.load_all_states())
            self.assertIn("previous state retained", message)
            saved = tracker.load_all_states()
            self.assertEqual(saved[pnr]["passengers"][0]["current_status"], "RLWL 10")
            self.assertEqual(len(notifier.messages), 1)

    def test_corrupt_state_is_not_silently_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text("{broken", encoding="utf-8")
            tracker = PNRTracker(pnrs="1234567890", client=PNRClient(mock_data={}),
                                 notifier=RecordingNotifier(), state_file=str(path))
            with self.assertRaises(RuntimeError):
                tracker.load_all_states()

    def test_pnr_validation_and_deduplication(self):
        tracker = PNRTracker(pnrs="1234567890, 1234567890")
        self.assertEqual(tracker.pnrs, ["1234567890"])
        with self.assertRaises(ValueError):
            PNRTracker(pnrs="123")


if __name__ == "__main__":
    unittest.main()
