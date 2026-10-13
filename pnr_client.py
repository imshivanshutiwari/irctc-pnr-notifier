"""
pnr_client.py — Fetches and normalizes Indian Railways / IRCTC PNR status.
Supports:
1. RapidAPI Indian Railway / IRCTC PNR status endpoints
2. Mock data provider for testing/simulation
"""

import os
import requests
from typing import Dict, Any, Optional

class PNRClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_host: Optional[str] = None,
        mock_data: Optional[Dict[str, Any]] = None
    ):
        self.api_key = api_key or os.getenv("RAPIDAPI_KEY")
        self.api_host = api_host or os.getenv("RAPIDAPI_HOST", "irctc-indian-railway-pnr-status.p.rapidapi.com")
        self.mock_data = mock_data

    def fetch_pnr_status(self, pnr: str) -> Dict[str, Any]:
        """
        Retrieves real-time PNR status and returns a normalized dictionary.
        """
        if self.mock_data is not None:
            return self._normalize_response(pnr, self.mock_data)

        if not self.api_key:
            raise ValueError("RAPIDAPI_KEY is not set. Set it in .env or provide mock_data.")

        # Clean PNR
        pnr_clean = str(pnr).strip().replace("-", "")
        if len(pnr_clean) != 10 or not pnr_clean.isdigit():
            raise ValueError(f"Invalid 10-digit PNR: {pnr}")

        url = f"https://{self.api_host}/pnr-status/{pnr_clean}"
        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.api_host
        }

        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            raise RuntimeError(f"RapidAPI request failed with code {response.status_code}: {response.text}")

        data = response.json()
        return self._normalize_response(pnr_clean, data)

    def _normalize_response(self, pnr: str, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes varying response schemas from different PNR APIs into a standard structure.
        """
        # If wrapped in 'data' or 'result'
        payload = raw.get("data") or raw.get("result") or raw

        train_number = (
            payload.get("train_number") or
            payload.get("trainNumber") or
            payload.get("TrainNo") or
            payload.get("train_no") or
            "N/A"
        )
        train_name = (
            payload.get("train_name") or
            payload.get("trainName") or
            payload.get("TrainName") or
            ""
        )
        doj = (
            payload.get("date_of_journey") or
            payload.get("doj") or
            payload.get("journey_date") or
            payload.get("journeyDate") or
            ""
        )
        from_stn = (
            payload.get("from_station") or
            payload.get("from") or
            payload.get("boarding_station") or
            payload.get("source") or
            ""
        )
        to_stn = (
            payload.get("to_station") or
            payload.get("to") or
            payload.get("reservation_upto") or
            payload.get("destination") or
            ""
        )
        chart_prepared = (
            payload.get("chart_prepared") or
            payload.get("chartPrepared") or
            False
        )

        raw_passengers = (
            payload.get("passengers") or
            payload.get("passenger_list") or
            payload.get("PassengerList") or
            []
        )

        passengers = []
        for idx, p in enumerate(raw_passengers, start=1):
            booking_status = (
                p.get("booking_status") or
                p.get("bookingStatus") or
                p.get("BookingStatus") or
                "UNKNOWN"
            )
            current_status = (
                p.get("current_status") or
                p.get("currentStatus") or
                p.get("CurrentStatus") or
                booking_status
            )
            passengers.append({
                "passenger_number": p.get("passenger_number") or p.get("number") or idx,
                "booking_status": str(booking_status).strip().upper(),
                "current_status": str(current_status).strip().upper()
            })

        return {
            "pnr": pnr,
            "train_number": str(train_number),
            "train_name": str(train_name),
            "date_of_journey": str(doj),
            "from_station": str(from_stn),
            "to_station": str(to_stn),
            "chart_prepared": bool(chart_prepared),
            "passengers": passengers
        }
