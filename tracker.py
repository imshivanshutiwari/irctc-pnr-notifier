"""
tracker.py — Main orchestration engine for PNR tracking and alert generation.
Supports tracking single or multiple PNRs, diffing waiting list statuses,
and delivering instant alerts when positions decrease or seats confirm.
"""

import os
import json
import argparse
from typing import Dict, Any, List, Tuple, Union, Optional

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
        pnrs: Union[List[str], str, None] = None,
        client: PNRClient = None,
        notifier: Notifier = None,
        state_file: str = DEFAULT_STATE_FILE,
        notify_on_first_run: bool = False,
        pnr: Optional[str] = None
    ):
        raw_target = pnrs if pnrs is not None else pnr
        if not raw_target:
            raise ValueError("At least one PNR must be specified.")

        if isinstance(raw_target, str):
            raw_list = [p.strip().replace("-", "") for p in raw_target.replace(",", " ").split()]
            self.pnrs = [p for p in raw_list if p]
        else:
            self.pnrs = [str(p).strip().replace("-", "") for p in raw_target if str(p).strip()]

        self.client = client
        self.notifier = notifier
        self.state_file = state_file
        self.notify_on_first_run = notify_on_first_run

    def load_all_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Loads cached states from disk.
        Supports both multi-PNR dict format and legacy single-PNR dict format.
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # If legacy single-PNR format (has 'pnr' at root)
                    if isinstance(data, dict) and "pnr" in data:
                        return {data["pnr"]: data}
                    if isinstance(data, dict):
                        return data
            except Exception as e:
                print(f"[Tracker] Warning: Failed to read state file: {e}")
        return {}

    def save_all_states(self, all_states: Dict[str, Dict[str, Any]]):
        """Persists latest state mapping to disk."""
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(all_states, f, indent=2)
            print(f"[Tracker] Updated states saved to {self.state_file}")
        except Exception as e:
            print(f"[Tracker] Error saving states: {e}")

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

    def check_pnr(self, pnr: str, all_states: Dict[str, Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Checks a single PNR against its historical state in all_states.
        """
        print(f"[Tracker] Checking PNR: {pnr}...")
        try:
            current_data = self.client.fetch_pnr_status(pnr)
        except Exception as e:
            msg = f"[Tracker] Error fetching status for PNR {pnr}: {e}"
            print(msg)
            return False, msg

        current_passengers = current_data.get("passengers", [])
        if not current_passengers:
            msg = f"[Tracker] No passenger data found for PNR {pnr}."
            print(msg)
            return False, msg

        previous_state = all_states.get(pnr, {})
        previous_passengers = previous_state.get("passengers", [])

        # Case 1: First time running this PNR
        if not previous_passengers:
            print(f"[Tracker] First run for PNR {pnr}. Saving baseline.")
            all_states[pnr] = current_data
            if self.notify_on_first_run:
                status_summary = ", ".join(
                    [f"P{p.get('passenger_number')}: {p.get('current_status')}" for p in current_passengers]
                )
                first_msg = (
                    f"🚂 *IRCTC Tracker Activated!*\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"📍 *PNR:* `{pnr}`\n"
                    f"🚆 *Train:* {current_data.get('train_number')} {current_data.get('train_name')}\n"
                    f"📅 *Date:* {current_data.get('date_of_journey')}\n"
                    f"📊 *Current Status:* {status_summary}\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"✅ You will receive instant alerts when waiting list moves!"
                )
                self.notifier.send_alert(first_msg)
                return True, f"Baseline saved for PNR {pnr}."
            return False, f"Baseline state recorded silently for PNR {pnr}."

        # Case 2: Subsequent check — compare for changes
        changes = self.detect_changes(previous_passengers, current_passengers)
        if changes:
            print(f"[Tracker] STATUS CHANGE DETECTED for {pnr}: {changes}")
            alert_msg = self.notifier.format_alert_message(
                pnr=pnr,
                train_info=current_data,
                changes=changes,
                current_state=current_data
            )
            self.notifier.send_alert(alert_msg)
            all_states[pnr] = current_data
            return True, f"Status changed for PNR {pnr} ({len(changes)} passenger(s))."
        else:
            print(f"[Tracker] PNR {pnr}: No status change detected. Waiting list remains the same.")
            all_states[pnr] = current_data
            return False, f"No change for PNR {pnr}."

    def check_once(self) -> Tuple[bool, str]:
        """
        Executes a check cycle for all configured PNRs.
        """
        if not self.pnrs:
            print("[Tracker] No PNRs configured.")
            return False, "No PNRs configured."

        all_states = self.load_all_states()
        any_alerts = False
        summaries = []

        for pnr in self.pnrs:
            alerted, summary = self.check_pnr(pnr, all_states)
            if alerted:
                any_alerts = True
            summaries.append(summary)

        self.save_all_states(all_states)
        return any_alerts, "; ".join(summaries)


def main():
    parser = argparse.ArgumentParser(description="IRCTC PNR Waiting List Notifier")
    parser.add_argument("--pnr", type=str, default=os.getenv("PNR_NUMBER"), help="Comma-separated PNR(s)")
    parser.add_argument("--state-file", type=str, default=DEFAULT_STATE_FILE, help="Path to state JSON")
    parser.add_argument("--dry-run", action="store_true", help="Run without sending real external notifications")
    parser.add_argument("--alert-on-first-run", action="store_true", help="Send alert on first baseline run")
    args = parser.parse_args()

    pnr_input = args.pnr or os.getenv("PNR_NUMBER")
    if not pnr_input:
        raise ValueError("PNR number is required. Provide via --pnr or PNR_NUMBER environment variable.")

    client = PNRClient()
    notifier = Notifier(dry_run=args.dry_run)
    tracker = PNRTracker(
        pnrs=pnr_input,
        client=client,
        notifier=notifier,
        state_file=args.state_file,
        notify_on_first_run=args.alert_on_first_run
    )

    tracker.check_once()

if __name__ == "__main__":
    main()
