//! cadence.rs - Autonomous Per-PNR Adaptive Polling Cadence Engine for RailPulse

use chrono::{DateTime, Duration, NaiveDate, NaiveTime, TimeZone, Utc};
use chrono_tz::Asia::Kolkata;
use chrono_tz::Tz;
use serde::{Deserialize, Serialize};

pub const PRIORITY_CADENCE_SECONDS: i64 = 2 * 3600; // 7200 seconds (2 hours)
pub const STANDARD_CADENCE_SECONDS: i64 = 5 * 3600; // 18000 seconds (5 hours)

pub fn get_ist_timezone() -> Tz {
    Kolkata
}

pub fn parse_journey_date(doj_str: Option<&str>) -> Option<NaiveDate> {
    let s = doj_str?.trim();
    for fmt in ["%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"] {
        if let Ok(d) = NaiveDate::parse_from_str(s, fmt) {
            return Some(d);
        }
    }
    None
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CadenceInfo {
    pub cadence_seconds: i64,
    pub cadence_hours: f64,
    pub priority_tier: String,
    pub tier_label: String,
    pub days_until_journey: Option<i64>,
    pub is_near_journey: bool,
}

pub fn compute_pnr_cadence(
    date_of_journey: Option<&str>,
    _chart_prepared: bool,
    now_dt: Option<DateTime<Tz>>,
) -> CadenceInfo {
    let now = now_dt.unwrap_or_else(|| Utc::now().with_timezone(&Kolkata));
    let today_ist = now.date_naive();
    let j_date = parse_journey_date(date_of_journey);

    let (cadence_seconds, priority_tier, tier_label, days_until, is_near) = match j_date {
        Some(journey_date) => {
            let days = (journey_date - today_ist).num_days();
            if (0..=2).contains(&days) {
                (
                    PRIORITY_CADENCE_SECONDS,
                    "priority-2h".to_string(),
                    format!("Priority Journey Cadence (2h) ({}d to Journey)", days),
                    Some(days),
                    true,
                )
            } else {
                (
                    STANDARD_CADENCE_SECONDS,
                    "standard-5h".to_string(),
                    format!("Standard Fleet Cadence (5h) ({}d to Journey)", days),
                    Some(days),
                    false,
                )
            }
        }
        None => (
            STANDARD_CADENCE_SECONDS,
            "standard-5h".to_string(),
            "Standard Cadence (5h)".to_string(),
            None,
            false,
        ),
    };

    CadenceInfo {
        cadence_seconds,
        cadence_hours: cadence_seconds as f64 / 3600.0,
        priority_tier,
        tier_label,
        days_until_journey: days_until,
        is_near_journey: is_near,
    }
}

pub fn compute_destination_arrival(
    date_of_journey: &str,
    departure_time: &str,
    arrival_time: &str,
) -> Option<DateTime<Tz>> {
    let j_date = parse_journey_date(Some(date_of_journey))?;
    let dep_time = NaiveTime::parse_from_str(departure_time.trim(), "%H:%M").ok()?;
    let arr_time = NaiveTime::parse_from_str(arrival_time.trim(), "%H:%M").ok()?;

    let _dep_dt = j_date.and_time(dep_time);
    let mut arr_dt = j_date.and_time(arr_time);

    // If arrival time is earlier than departure time, arrival occurred next day
    if arr_time < dep_time {
        arr_dt += Duration::days(1);
    }

    Kolkata.from_local_datetime(&arr_dt).single()
}

pub fn is_journey_completed(
    date_of_journey: Option<&str>,
    departure_time: Option<&str>,
    arrival_time: Option<&str>,
    buffer_minutes: i64,
    now_dt: Option<DateTime<Tz>>,
) -> (bool, Option<DateTime<Tz>>) {
    let now = now_dt.unwrap_or_else(|| Utc::now().with_timezone(&Kolkata));
    let doj = match date_of_journey {
        Some(d) => d,
        None => return (false, None),
    };

    let dep_str = departure_time.unwrap_or("00:00");
    let arr_str = arrival_time.unwrap_or("23:59");

    let arrival_dt = match compute_destination_arrival(doj, dep_str, arr_str) {
        Some(dt) => dt,
        None => {
            // Fallback: midnight end of journey day
            match parse_journey_date(Some(doj)) {
                Some(d) => {
                    let fallback = d.and_hms_opt(23, 59, 59).unwrap();
                    Kolkata.from_local_datetime(&fallback).unwrap()
                }
                None => return (false, None),
            }
        }
    };

    let completion_threshold = arrival_dt + Duration::minutes(buffer_minutes);
    let completed = now >= completion_threshold;
    (completed, Some(arrival_dt))
}
