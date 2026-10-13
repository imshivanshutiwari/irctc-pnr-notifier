"""
tracker.py — Main orchestration engine for PNR tracking and alert generation.
Compares historical PNR state against current status and alerts on waiting list movements.
"""

import os
import json
import argparse
from typing import Dict, Any, List, Tuple

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from pnr_client import PNRClient
from notifier import Notifier

DEFAULT_STATE_FILE = "status_state.json"

class PNRTracker:
    def __init__(
        self,
        pnr: str,
        client: PNRClient,
        notifier: Notifier,
        state_file: str = DEFAULT_STATE_FILE,
        notify_on_first_run: bool = False
    ):
        self.pnr = str(pnr).strip().replace("-", "")
        self.client = client
        self.notifier = notifier
        self.state_file = state_file
        self.notify_on_first_run = notify_on_first_run

    def load_state(self) -> Dict[str, Any]:
        """Loads cached PNR state from disk."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Tracker] Warning: Failed to read state file: {e}")
        return {}

    def save_state(self, state: Dict[str, Any]):
        """Persists latest PNR state to disk."""
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            print(f"[Tracker] Updated state saved to {self.state_file}")
        except Exception as e:
            print(f"[Tracker] Error saving state: {e}")

    def detect_changes(
        self,
        previous_passengers: List[Dict[str, Any]],
        current_passengers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Compares passenger list states and returns detected changes.
        """
        changes = []
        prev_map = {
            p.get("passenger_number", i + 1): p.get("current_status")
            for i, p in enumerate(previous_passengers)
        }

        for i, curr in enumerate(current_passengers):
            p_num = curr.get("passenger_number", i + 1)
            curr_status = curr.get("current_status", "").strip().upper()
            prev_status = prev_map.get(p_num)

            if prev_status is None:
                continue

            if curr_status != prev_status.strip().upper():
                changes.append({
                    "passenger": f"Passenger {p_num}",
                    "old_status": prev_status,
                    "new_status": curr_status
                })

        return changes

    def check_once(self) -> Tuple[bool, str]:
        """
        Executes a single check cycle.
        Returns (has_changed_or_alerted, summary_message).
        """
        print(f"[Tracker] Checking PNR: {self.pnr}...")
        current_data = self.client.fetch_pnr_status(self.pnr)
        current_passengers = current_data.get("passengers", [])

        if not current_passengers:
            msg = f"[Tracker] No passenger data found for PNR {self.pnr}."
            print(msg)
            return False, msg

        previous_state = self.load_state()
        previous_passengers = previous_state.get("passengers", [])

        # Case 1: First time running (no prior state)
        if not previous_passengers:
            print("[Tracker] First run detected. Saving baseline status.")
            self.save_state(current_data)
            
            if self.notify_on_first_run:
                # Send welcome/baseline confirmation
                status_summary = ", ".join(
                    [f"P{p.get('passenger_number')}: {p.get('current_status')}" for p in current_passengers]
                )
                first_msg = (
                    f"🚂 *IRCTC Tracker Activated!*\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"📍 *PNR:* `{self.pnr}`\n"
                    f"🚆 *Train:* {current_data.get('train_number')} {current_data.get('train_name')}\n"
                    f"📅 *Date:* {current_data.get('date_of_journey')}\n"
                    f"📊 *Current Status:* {status_summary}\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"✅ You will receive instant WhatsApp alerts every time this waiting list moves!"
                )
                self.notifier.send_alert(first_msg)
                return True, "Baseline recorded and welcome alert dispatched."
            return False, "Baseline state recorded silently."

        # Case 2: Subsequent runs — check for changes
        changes = self.detect_changes(previous_passengers, current_passengers)

        if changes:
            print(f"[Tracker] STATUS CHANGE DETECTED: {changes}")
            alert_msg = self.notifier.format_alert_message(
                pnr=self.pnr,
                train_info=current_data,
                changes=changes,
                current_state=current_data
            )
            self.notifier.send_alert(alert_msg)
            self.save_state(current_data)
            return True, f"Status changed for {len(changes)} passenger(s)."
        else:
            print("[Tracker] No status change detected. Waiting list remains the same.")
            # Still update train metadata/chart status in case it changed
            self.save_state(current_data)
            return False, "No status change."

def main():
    parser = argparse.ArgumentParser(description="IRCTC PNR Waiting List Notifier")
    parser.add_argument("--pnr", type=str, default=os.getenv("PNR_NUMBER"), help="10-digit PNR")
    parser.add_argument("--state-file", type=str, default=DEFAULT_STATE_FILE, help="Path to state JSON")
    parser.add_argument("--dry-run", action="store_true", help="Run without sending real WhatsApp message")
    parser.add_argument("--alert-on-first-run", action="store_true", help="Send a message even on first run baseline")
    args = parser.parse_args()

    pnr = args.pnr or os.getenv("PNR_NUMBER")
    if not pnr:
        raise ValueError("PNR number is required. Provide via --pnr or PNR_NUMBER environment variable.")

    client = PNRClient()
    notifier = Notifier(dry_run=args.dry_run)
    tracker = PNRTracker(
        pnr=pnr,
        client=client,
        notifier=notifier,
        state_file=args.state_file,
        notify_on_first_run=args.alert_on_first_run
    )

    tracker.check_once()

if __name__ == "__main__":
    main()
