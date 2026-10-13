"""
tracker.py — Main orchestration engine for PNR tracking and alert generation.
Supports tracking single or multiple PNRs, regex status classification,
detecting genuine waiting list improvements, atomic state writes,
and delivery over ntfy, WhatsApp, or Telegram.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from pnr_client import PNRClient
from notifier import Notifier

DEFAULT_STATE_FILE = "status_state.json"
WAITLIST_RE = re.compile(r"\b(GNWL|RLWL|PQWL|RQWL|TQWL|WL|W/L)\s*[- ]*\s*(\d+)\b", re.I)
RAC_RE = re.compile(r"\bRAC\s*[- ]*\s*(\d+)?\b", re.I)
CNF_RE = re.compile(r"\bCNF|CONFIRMED\b", re.I)


def classify_status(value: Any) -> Tuple[str, Optional[int]]:
    """Return (kind, position) for a known status; unknown values stay unknown."""
    text = str(value or "").strip().upper()
    match = WAITLIST_RE.search(text)
    if match:
        category = match.group(1).replace("W/L", "WL")
        return category, int(match.group(2))
    match = RAC_RE.search(text)
    if match:
        return "RAC", int(match.group(1)) if match.group(1) else None
    if CNF_RE.search(text):
        return "CNF", None
    return "UNKNOWN", None


def is_improvement(old_status: Any, new_status: Any) -> bool:
    """Return True only for a genuine booking-status improvement."""
    old_kind, old_pos = classify_status(old_status)
    new_kind, new_pos = classify_status(new_status)

    if new_kind == "UNKNOWN":
        return False
    if new_kind == "CNF":
        return old_kind != "CNF"
    if new_kind == "RAC":
        if old_kind not in ("RAC", "CNF"):
            return True
        if old_kind == "RAC" and old_pos is not None and new_pos is not None:
            return new_pos < old_pos
        return False
    if old_kind == new_kind and old_pos is not None and new_pos is not None:
        return new_pos < old_pos
    return False


class PNRTracker:
    def __init__(
        self,
        pnrs: Union[List[str], str, None] = None,
        client: Optional[PNRClient] = None,
        notifier: Optional[Notifier] = None,
        state_file: Union[str, Path] = DEFAULT_STATE_FILE,
        notify_on_first_run: bool = False,
        pnr: Optional[str] = None,
    ):
        raw_target = pnrs if pnrs is not None else pnr
        if not raw_target:
            raise ValueError("At least one PNR must be specified.")

        if isinstance(raw_target, str):
            raw_list = [p.strip().replace("-", "") for p in raw_target.replace(",", " ").split()]
        else:
            raw_list = [str(p).strip().replace("-", "") for p in raw_target if str(p).strip()]

        invalid = [p for p in raw_list if len(p) != 10 or not p.isdigit()]
        if invalid:
            raise ValueError("Every PNR must contain exactly 10 digits.")
        self.pnrs = list(dict.fromkeys(raw_list))
        self.client = client or PNRClient()
        self.notifier = notifier or Notifier()
        self.state_file = Path(state_file)
        self.notify_on_first_run = notify_on_first_run

    def load_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Loads cached states from disk safely without resetting corrupted state."""
        if not self.state_file.exists():
            return {}
        try:
            content = self.state_file.read_text(encoding="utf-8")
            data = json.loads(content)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Cannot safely read state file {self.state_file}: {exc}") from exc

        if not isinstance(data, dict):
            raise RuntimeError(f"State file {self.state_file} must contain a JSON object.")
        if "pnr" in data:  # legacy single-PNR format
            return {str(data["pnr"]): data}
        return data

    def save_all_states(self, all_states: Dict[str, Dict[str, Any]]) -> None:
        """Write state atomically using temp file and rename."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=str(self.state_file.parent),
                prefix=f".{self.state_file.name}.", suffix=".tmp", delete=False
            ) as handle:
                temp_name = handle.name
                json.dump(all_states, handle, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.state_file)
        except OSError as exc:
            if temp_name:
                try:
                    os.unlink(temp_name)
                except OSError:
                    pass
            raise RuntimeError(f"Could not safely save state file {self.state_file}: {exc}") from exc

    def detect_changes(
        self,
        previous_passengers: List[Dict[str, Any]],
        current_passengers: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        previous = {
            str(p.get("passenger_number", i + 1)): p.get("current_status")
            for i, p in enumerate(previous_passengers)
        }
        changes = []
        for i, current in enumerate(current_passengers):
            number = str(current.get("passenger_number", i + 1))
            old = previous.get(number)
            new = str(current.get("current_status") or "").strip().upper()
            if old is not None and is_improvement(old, new):
                changes.append({
                    "passenger": f"Passenger {number}",
                    "old_status": str(old),
                    "new_status": new,
                })
        return changes

    def check_pnr(self, pnr: str, all_states: Dict[str, Dict[str, Any]]) -> Tuple[bool, str]:
        masked = pnr[-4:].rjust(len(pnr), '*')
        print(f"[Tracker] Checking configured PNR {masked}...")
        try:
            current_data = self.client.fetch_pnr_status(pnr)
        except Exception as exc:
            return False, f"Fetch failed for PNR ending {pnr[-4:]}: {exc}"

        current_passengers = current_data.get("passengers", [])
        if not isinstance(current_passengers, list) or not current_passengers:
            return False, f"No valid passenger data returned for PNR ending {pnr[-4:]}."

        previous_state = all_states.get(pnr, {})
        previous_passengers = previous_state.get("passengers", [])

        if not previous_passengers:
            if self.notify_on_first_run:
                summary = ", ".join(
                    f"P{p.get('passenger_number', i + 1)}: {p.get('current_status', 'UNKNOWN')}"
                    for i, p in enumerate(current_passengers)
                )
                message = (
                    "IRCTC tracker activated\n"
                    f"PNR: {pnr}\n"
                    f"Train: {current_data.get('train_number', '')} {current_data.get('train_name', '')}\n"
                    f"Journey date: {current_data.get('date_of_journey', '')}\n"
                    f"Current status: {summary}"
                )
                if not self.notifier.send_alert(message):
                    return False, f"Initial notification failed for PNR ending {pnr[-4:]}; baseline not saved."
                all_states[pnr] = current_data
                return True, f"Baseline saved for PNR {pnr} and alert delivered."
            all_states[pnr] = current_data
            return False, f"Baseline saved for PNR {pnr}."

        changes = self.detect_changes(previous_passengers, current_passengers)
        if changes:
            message = self.notifier.format_alert_message(
                pnr=pnr, train_info=current_data, changes=changes, current_state=current_data
            )
            if not self.notifier.send_alert(message):
                # Keep old state so the same transition is retried next run.
                return False, f"Notification failed for PNR ending {pnr[-4:]}; previous state retained."
            all_states[pnr] = current_data
            return True, f"Status changed for PNR {pnr}: Delivered {len(changes)} improvement alert(s)."

        all_states[pnr] = current_data
        return False, f"No change for PNR {pnr}."

    def check_once(self) -> Tuple[bool, str]:
        if not self.pnrs:
            return False, "No PNRs configured."

        all_states = self.load_all_states()
        any_alerts = False
        summaries = []
        errors = []

        for pnr in self.pnrs:
            alerted, summary = self.check_pnr(pnr, all_states)
            any_alerts = any_alerts or alerted
            summaries.append(summary)
            if "fetch failed" in summary.lower() or "no valid passenger" in summary.lower():
                errors.append(summary)

        self.save_all_states(all_states)
        if errors and len(errors) == len(self.pnrs):
            raise RuntimeError("; ".join(errors))
        return any_alerts, "; ".join(summaries)


def main() -> int:
    parser = argparse.ArgumentParser(description="IRCTC PNR status improvement notifier")
    parser.add_argument("--pnr", type=str, default=os.getenv("PNR_NUMBER"), help="Comma-separated 10-digit PNRs")
    parser.add_argument("--state-file", type=str, default=DEFAULT_STATE_FILE, help="Path to private state JSON")
    parser.add_argument("--dry-run", action="store_true", help="Simulate notifications")
    parser.add_argument("--alert-on-first-run", action="store_true", help="Notify when recording initial baseline")
    args = parser.parse_args()

    if not args.pnr:
        parser.error("PNR number is required. Configure the PNR_NUMBER environment variable or use --pnr.")

    tracker = PNRTracker(
        pnrs=args.pnr,
        client=PNRClient(),
        notifier=Notifier(dry_run=args.dry_run),
        state_file=args.state_file,
        notify_on_first_run=args.alert_on_first_run,
    )
    try:
        _, summary = tracker.check_once()
        print(summary)
        return 0
    except Exception as exc:
        print(f"[Tracker] Check failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
