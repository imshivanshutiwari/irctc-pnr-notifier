"""
pnr_client.py - Fetches and normalizes Indian Railways / IRCTC PNR status.
Supports:
1. RapidAPI Indian Railway / IRCTC PNR status endpoints
2. Mock data provider for testing/simulation
"""

import os
import requests
from typing import Dict, Any, Optional
from stations import get_station_info

class PNRClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_host: Optional[str] = None,
        mock_data: Optional[Dict[str, Any]] = None
    ):
        self.api_key = api_key or os.getenv("RAPIDAPI_KEY")
        self.api_host = api_host or os.getenv("RAPIDAPI_HOST", "irctc1.p.rapidapi.com")
        self.mock_data = mock_data

    def _fetch_from_free_endpoint(self, pnr_clean: str) -> Dict[str, Any]:
        """
        Direct zero-key, unlimited free endpoint used by mobile rail apps.
        """
        url = f"https://api.confirmtkt.com/api/pnr/status/{pnr_clean}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        }
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 200:
            return resp.json()
        raise RuntimeError(f"Free rail endpoint returned {resp.status_code}: {resp.text[:100]}")

    def fetch_pnr_status(self, pnr: str) -> Dict[str, Any]:
        """
        Retrieves real-time PNR status and returns a normalized dictionary.
        Supports automatic fallback between free open rail gateway and RapidAPI.
        """
        if self.mock_data is not None:
            return self._normalize_response(pnr, self.mock_data)

        # Clean PNR
        pnr_clean = str(pnr).strip().replace("-", "")
        if len(pnr_clean) != 10 or not pnr_clean.isdigit():
            raise ValueError(f"Invalid 10-digit PNR: {pnr}")

        # Attempt 1: Free Unlimited Open Gateway (Zero quota limits)
        try:
            free_data = self._fetch_from_free_endpoint(pnr_clean)
            if free_data and (free_data.get("PassengerStatus") or free_data.get("passengers")):
                return self._normalize_response(pnr_clean, free_data)
        except Exception as e:
            print(f"[PNRClient] Free gateway notice ({e}), attempting RapidAPI fallback...")

        # Attempt 2: RapidAPI (if key is configured)
        if self.api_key:
            headers = {
                "x-rapidapi-key": self.api_key,
                "x-rapidapi-host": self.api_host
            }

            if "irctc1.p.rapidapi.com" in self.api_host:
                url = f"https://{self.api_host}/api/v3/getPNRStatus"
                params = {"pnrNumber": pnr_clean}
                response = requests.get(url, headers=headers, params=params, timeout=20)
            else:
                url = f"https://{self.api_host}/pnr-status/{pnr_clean}"
                response = requests.get(url, headers=headers, timeout=20)

            if response.status_code == 200:
                data = response.json()
                if not (data.get("status") is False and "message" in data):
                    return self._normalize_response(pnr_clean, data)

        raise RuntimeError(f"Failed to fetch PNR status for {pnr_clean} across all providers.")

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
            payload.get("Doj") or
            payload.get("date_of_journey") or
            payload.get("boardingDate") or
            payload.get("doj") or
            payload.get("journey_date") or
            payload.get("journeyDate") or
            ""
        )
        # Station codes from API
        raw_from_code = str(
            payload.get("From") or
            payload.get("BoardingPoint") or
            payload.get("sourceStation") or
            payload.get("from_code") or
            ""
        ).strip().upper()
        raw_to_code = str(
            payload.get("To") or
            payload.get("ReservationUpto") or
            payload.get("destinationStation") or
            payload.get("to_code") or
            ""
        ).strip().upper()

        # Station names from API
        raw_from_name = str(
            payload.get("BoardingStationName") or
            payload.get("SourceName") or
            payload.get("source_station_name") or
            payload.get("from_station") or
            raw_from_code
        ).strip()
        raw_to_name = str(
            payload.get("ReservationUptoName") or
            payload.get("DestinationName") or
            payload.get("destination_station_name") or
            payload.get("to_station") or
            raw_to_code
        ).strip()

        # Get authentic station code, full English name, and authentic Hindi name
        from_code, from_name, from_hi = get_station_info(raw_from_code, raw_from_name)
        to_code, to_name, to_hi = get_station_info(raw_to_code, raw_to_name)

        coach_class = str(payload.get("Class") or payload.get("journeyClass") or payload.get("coach_class") or "").strip().upper()
        quota = str(payload.get("Quota") or payload.get("quota") or "").strip().upper()
        fare = str(payload.get("TicketFare") or payload.get("BookingFare") or payload.get("fare") or "").strip()
        dep_time = str(payload.get("DepartureTime") or payload.get("dep_time") or "").strip()
        arr_time = str(payload.get("ArrivalTime") or payload.get("arr_time") or "").strip()

        chart_status_raw = str(payload.get("ChartPrepared") or payload.get("chartStatus") or payload.get("chart_prepared") or payload.get("chartPrepared") or "").upper()
        chart_prepared = "TRUE" in chart_status_raw or ("PREPARED" in chart_status_raw and "NOT" not in chart_status_raw)

        raw_passengers = (
            payload.get("PassengerStatus") or
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
            coach = str(p.get("currentCoachId") or p.get("Coach") or "").strip()
            berth = str(p.get("currentBerthNo") or p.get("Berth") or "").strip()
            if coach and berth and "CNF" in str(current_status).upper() and coach not in str(current_status):
                current_status = f"{current_status} ({coach}/{berth})"

            passengers.append({
                "passenger_number": p.get("passenger_number") or p.get("passengerSerialNumber") or p.get("Number") or p.get("number") or idx,
                "booking_status": str(booking_status).strip().upper(),
                "current_status": str(current_status).strip().upper()
            })

        return {
            "pnr": pnr,
            "train_number": str(train_number),
            "train_name": str(train_name),
            "date_of_journey": str(doj),
            "from_station": from_name,
            "to_station": to_name,
            "from_name": from_name,
            "to_name": to_name,
            "from_code": from_code,
            "to_code": to_code,
            "from_hi": from_hi,
            "to_hi": to_hi,
            "coach_class": coach_class,
            "quota": quota,
            "fare": fare,
            "dep_time": dep_time,
            "arr_time": arr_time,
            "chart_prepared": bool(chart_prepared),
            "passengers": passengers
        }
