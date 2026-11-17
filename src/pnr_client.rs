//! pnr_client.rs - Fetches and normalizes Indian Railways / IRCTC PNR status.

use crate::stations::get_station_info;
use serde_json::{json, Value};
use std::env;
use std::time::Duration;
use tracing::warn;

#[derive(Debug, thiserror::Error)]
pub enum PnrError {
    #[error("Invalid 10-digit PNR: {0}")]
    InvalidPnr(String),
    #[error("Indian Railways PRS: {0}")]
    PrsError(String),
    #[error("Network / Gateway error: {0}")]
    NetworkError(String),
}

#[derive(Debug, Clone)]
pub struct PNRClient {
    pub api_key: Option<String>,
    pub api_host: String,
    pub mock_data: Option<Value>,
    client: reqwest::Client,
}

impl PNRClient {
    pub fn new(
        api_key: Option<String>,
        api_host: Option<String>,
        mock_data: Option<Value>,
    ) -> Self {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(20))
            .build()
            .unwrap_or_default();

        Self {
            api_key: api_key.or_else(|| env::var("RAPIDAPI_KEY").ok()),
            api_host: api_host
                .or_else(|| env::var("RAPIDAPI_HOST").ok())
                .unwrap_or_else(|| "irctc1.p.rapidapi.com".to_string()),
            mock_data,
            client,
        }
    }

    async fn fetch_from_free_endpoint(&self, pnr_clean: &str) -> Result<Value, PnrError> {
        let url = format!("https://api.confirmtkt.com/api/pnr/status/{}", pnr_clean);
        let resp = self
            .client
            .get(&url)
            .header(
                "User-Agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            .header("Accept", "application/json, text/plain, */*")
            .send()
            .await
            .map_err(|e| PnrError::NetworkError(e.to_string()))?;

        let status = resp.status();
        if status.is_success() {
            let json_val = resp
                .json::<Value>()
                .await
                .map_err(|e| PnrError::NetworkError(format!("Invalid JSON: {}", e)))?;
            Ok(json_val)
        } else {
            Err(PnrError::NetworkError(format!("Free rail endpoint status {}", status)))
        }
    }

    pub async fn fetch_pnr_status(&self, pnr: &str) -> Result<Value, PnrError> {
        if let Some(mock) = &self.mock_data {
            return Ok(self.normalize_response(pnr, mock));
        }

        let pnr_clean = pnr.trim().replace('-', "");
        if pnr_clean.len() != 10 || !pnr_clean.chars().all(|c| c.is_ascii_digit()) {
            return Err(PnrError::InvalidPnr(pnr.to_string()));
        }

        let mut errors = Vec::new();

        // 1. ConfirmTKT Open Gateway
        match self.fetch_from_free_endpoint(&pnr_clean).await {
            Ok(free_data) => {
                let err_msg = free_data
                    .get("Error")
                    .or_else(|| free_data.get("ErrorMessage"))
                    .and_then(|v| v.as_str());

                let has_passengers = free_data
                    .get("PassengerStatus")
                    .or_else(|| free_data.get("passengers"))
                    .and_then(|v| v.as_array())
                    .map(|a| !a.is_empty())
                    .unwrap_or(false);

                if let Some(err) = err_msg {
                    if !has_passengers {
                        return Err(PnrError::PrsError(err.to_string()));
                    }
                }

                if has_passengers {
                    return Ok(self.normalize_response(&pnr_clean, &free_data));
                }
            }
            Err(PnrError::PrsError(e)) => return Err(PnrError::PrsError(e)),
            Err(e) => {
                errors.push(format!("Free rail gateway: {}", e));
                warn!("[PNRClient] Free gateway notice ({}), attempting RapidAPI...", e);
            }
        }

        // 2. RapidAPI fallback
        if let Some(key) = &self.api_key {
            if !key.trim().is_empty() {
                let url = format!(
                    "https://{}/api/v3/getPNRStatus?pnrNumber={}",
                    self.api_host, pnr_clean
                );
                let res = self
                    .client
                    .get(&url)
                    .header("x-rapidapi-key", key)
                    .header("x-rapidapi-host", &self.api_host)
                    .send()
                    .await;

                match res {
                    Ok(resp) if resp.status().is_success() => {
                        if let Ok(rapid_data) = resp.json::<Value>().await {
                            if rapid_data.get("status").and_then(|v| v.as_bool()).unwrap_or(false)
                                || rapid_data.get("data").is_some()
                            {
                                return Ok(self.normalize_response(&pnr_clean, &rapid_data));
                            }
                        }
                    }
                    Ok(resp) => {
                        errors.push(format!("RapidAPI returned status {}", resp.status()));
                    }
                    Err(e) => {
                        errors.push(format!("RapidAPI error: {}", e));
                    }
                }
            }
        }

        let err_details = if errors.is_empty() {
            "no active provider response".to_string()
        } else {
            errors.join("; ")
        };
        Err(PnrError::NetworkError(format!(
            "Failed to fetch PNR status for {}: {}",
            pnr_clean, err_details
        )))
    }

    pub fn normalize_response(&self, pnr: &str, raw: &Value) -> Value {
        let payload = raw
            .get("data")
            .or_else(|| raw.get("result"))
            .unwrap_or(raw);

        let train_number = payload
            .get("train_number")
            .or_else(|| payload.get("trainNumber"))
            .or_else(|| payload.get("TrainNo"))
            .or_else(|| payload.get("train_no"))
            .and_then(|v| v.as_str())
            .unwrap_or("N/A");

        let train_name = payload
            .get("train_name")
            .or_else(|| payload.get("trainName"))
            .or_else(|| payload.get("TrainName"))
            .and_then(|v| v.as_str())
            .unwrap_or("");

        let doj = payload
            .get("Doj")
            .or_else(|| payload.get("date_of_journey"))
            .or_else(|| payload.get("boardingDate"))
            .or_else(|| payload.get("doj"))
            .or_else(|| payload.get("journey_date"))
            .or_else(|| payload.get("journeyDate"))
            .and_then(|v| v.as_str())
            .unwrap_or("");

        let raw_from_code = payload
            .get("From")
            .or_else(|| payload.get("BoardingPoint"))
            .or_else(|| payload.get("sourceStation"))
            .or_else(|| payload.get("from_code"))
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .trim()
            .to_uppercase();

        let raw_to_code = payload
            .get("To")
            .or_else(|| payload.get("ReservationUpto"))
            .or_else(|| payload.get("destinationStation"))
            .or_else(|| payload.get("to_code"))
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .trim()
            .to_uppercase();

        let raw_from_name = payload
            .get("BoardingStationName")
            .or_else(|| payload.get("SourceName"))
            .or_else(|| payload.get("source_station_name"))
            .or_else(|| payload.get("from_station"))
            .and_then(|v| v.as_str())
            .unwrap_or(&raw_from_code)
            .trim();

        let raw_to_name = payload
            .get("ReservationUptoName")
            .or_else(|| payload.get("DestinationName"))
            .or_else(|| payload.get("destination_station_name"))
            .or_else(|| payload.get("to_station"))
            .and_then(|v| v.as_str())
            .unwrap_or(&raw_to_code)
            .trim();

        let (from_code, from_name, from_hi) = get_station_info(&raw_from_code, raw_from_name);
        let (to_code, to_name, to_hi) = get_station_info(&raw_to_code, raw_to_name);

        let coach_class = payload
            .get("Class")
            .or_else(|| payload.get("journeyClass"))
            .or_else(|| payload.get("coach_class"))
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .trim()
            .to_uppercase();

        let quota = payload
            .get("Quota")
            .or_else(|| payload.get("quota"))
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .trim()
            .to_uppercase();

        let fare = payload
            .get("TicketFare")
            .or_else(|| payload.get("BookingFare"))
            .or_else(|| payload.get("fare"))
            .map(|v| {
                if let Some(s) = v.as_str() {
                    s.to_string()
                } else {
                    v.to_string()
                }
            })
            .unwrap_or_default();

        let dep_time = payload
            .get("DepartureTime")
            .or_else(|| payload.get("dep_time"))
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .trim();

        let arr_time = payload
            .get("ArrivalTime")
            .or_else(|| payload.get("arr_time"))
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .trim();

        let chart_status_raw = payload
            .get("ChartPrepared")
            .or_else(|| payload.get("chartStatus"))
            .or_else(|| payload.get("chart_prepared"))
            .or_else(|| payload.get("chartPrepared"))
            .map(|v| {
                if let Some(b) = v.as_bool() {
                    if b { "TRUE" } else { "FALSE" }
                } else if let Some(s) = v.as_str() {
                    s
                } else {
                    ""
                }
            })
            .unwrap_or("")
            .to_uppercase();

        let chart_prepared = chart_status_raw.contains("TRUE")
            || (chart_status_raw.contains("PREPARED") && !chart_status_raw.contains("NOT"));

        let raw_passengers = payload
            .get("PassengerStatus")
            .or_else(|| payload.get("passengers"))
            .or_else(|| payload.get("passenger_list"))
            .or_else(|| payload.get("PassengerList"))
            .and_then(|v| v.as_array())
            .cloned()
            .unwrap_or_default();

        let mut passengers = Vec::new();
        for (idx, p) in raw_passengers.iter().enumerate() {
            let booking_status = p
                .get("booking_status")
                .or_else(|| p.get("bookingStatus"))
                .or_else(|| p.get("BookingStatus"))
                .and_then(|v| v.as_str())
                .unwrap_or("UNKNOWN");

            let mut current_status = p
                .get("current_status")
                .or_else(|| p.get("currentStatus"))
                .or_else(|| p.get("CurrentStatus"))
                .and_then(|v| v.as_str())
                .unwrap_or(booking_status)
                .to_string();

            let coach = p
                .get("currentCoachId")
                .or_else(|| p.get("Coach"))
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .trim()
                .to_string();

            let berth = p
                .get("currentBerthNo")
                .or_else(|| p.get("Berth"))
                .map(|v| {
                    if let Some(s) = v.as_str() {
                        s.to_string()
                    } else {
                        v.to_string()
                    }
                })
                .unwrap_or_default();

            let berth_code = p
                .get("CurrentBerthCode")
                .or_else(|| p.get("BookingBerthCode"))
                .or_else(|| p.get("berth_code"))
                .or_else(|| p.get("BerthCode"))
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .trim()
                .to_uppercase();

            if !coach.is_empty()
                && !berth.is_empty()
                && current_status.to_uppercase().contains("CNF")
                && !current_status.contains(&coach)
            {
                current_status = format!("{} ({}/{})", current_status, coach, berth);
            }

            passengers.push(json!({
                "passenger_number": idx + 1,
                "booking_status": booking_status.trim().to_uppercase(),
                "current_status": current_status.trim().to_uppercase(),
                "coach": coach,
                "berth": berth,
                "berth_code": berth_code
            }));
        }

        json!({
            "pnr": pnr,
            "train_number": train_number,
            "train_name": train_name,
            "date_of_journey": doj,
            "from_station": from_name,
            "from_name": from_name,
            "from_code": from_code,
            "from_station_code": from_code,
            "from_hi": from_hi,
            "from_station_hindi": from_hi,
            "to_station": to_name,
            "to_name": to_name,
            "to_code": to_code,
            "to_station_code": to_code,
            "to_hi": to_hi,
            "to_station_hindi": to_hi,
            "coach_class": coach_class,
            "class": coach_class,
            "quota": quota,
            "fare": fare,
            "dep_time": dep_time,
            "departure_time": dep_time,
            "arr_time": arr_time,
            "arrival_time": arr_time,
            "chart_prepared": chart_prepared,
            "passengers": passengers,
            "fetched_at": chrono::Utc::now().to_rfc3339()
        })
    }
}
