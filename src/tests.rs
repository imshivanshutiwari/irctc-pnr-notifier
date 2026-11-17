//! tests.rs - Complete QA test suite for RailPulse Rust edition (Equivalent to all 62 Python tests).

use crate::cadence::*;
use crate::notifier::*;
use crate::stations::*;
use crate::tracker::*;
use chrono::{NaiveDate, TimeZone};
use chrono_tz::Asia::Kolkata;
use serde_json::json;
use tempfile::NamedTempFile;

#[test]
fn test_parse_journey_date() {
    assert_eq!(
        parse_journey_date(Some("17-10-2026")),
        Some(NaiveDate::from_ymd_opt(2026, 10, 17).unwrap())
    );
    assert_eq!(
        parse_journey_date(Some("2026-10-18")),
        Some(NaiveDate::from_ymd_opt(2026, 10, 18).unwrap())
    );
    assert_eq!(
        parse_journey_date(Some("15/11/2026")),
        Some(NaiveDate::from_ymd_opt(2026, 11, 15).unwrap())
    );
    assert_eq!(parse_journey_date(None), None);
    assert_eq!(parse_journey_date(Some("invalid-date")), None);
}

#[test]
fn test_user_three_pnr_scenarios() {
    let simulated_now = Kolkata
        .with_ymd_and_hms(2026, 10, 16, 19, 30, 0)
        .single()
        .unwrap();

    // 1. Tomorrow
    let res1 = compute_pnr_cadence(Some("17-10-2026"), false, Some(simulated_now));
    assert_eq!(res1.cadence_seconds, 7200);
    assert_eq!(res1.priority_tier, "priority-2h");
    assert_eq!(res1.days_until_journey, Some(1));
    assert!(res1.is_near_journey);

    // 2. Day after tomorrow
    let res2 = compute_pnr_cadence(Some("18-10-2026"), false, Some(simulated_now));
    assert_eq!(res2.cadence_seconds, 7200);
    assert_eq!(res2.priority_tier, "priority-2h");
    assert_eq!(res2.days_until_journey, Some(2));
    assert!(res2.is_near_journey);

    // 3. 30 days away
    let res3 = compute_pnr_cadence(Some("15-11-2026"), false, Some(simulated_now));
    assert_eq!(res3.cadence_seconds, 18000);
    assert_eq!(res3.priority_tier, "standard-5h");
    assert_eq!(res3.days_until_journey, Some(30));
    assert!(!res3.is_near_journey);
}

#[test]
fn test_journey_today_is_priority() {
    let simulated_now = Kolkata
        .with_ymd_and_hms(2026, 10, 17, 8, 0, 0)
        .single()
        .unwrap();
    let res = compute_pnr_cadence(Some("17-10-2026"), false, Some(simulated_now));
    assert_eq!(res.cadence_seconds, 7200);
    assert_eq!(res.days_until_journey, Some(0));
    assert!(res.is_near_journey);

    // Also priority even if chart is prepared
    let res_charted = compute_pnr_cadence(Some("17-10-2026"), true, Some(simulated_now));
    assert_eq!(res_charted.cadence_seconds, 7200);
    assert!(res_charted.is_near_journey);
}

#[test]
fn test_past_journey_fallback() {
    let simulated_now = Kolkata
        .with_ymd_and_hms(2026, 10, 20, 8, 0, 0)
        .single()
        .unwrap();
    let res = compute_pnr_cadence(Some("17-10-2026"), false, Some(simulated_now));
    assert_eq!(res.cadence_seconds, 18000);
    assert!(!res.is_near_journey);
}

#[test]
fn test_invalid_date_fallback() {
    let res = compute_pnr_cadence(None, false, None);
    assert_eq!(res.cadence_seconds, 18000);
    assert_eq!(res.priority_tier, "standard-5h");
}

#[test]
fn test_destination_arrival_calculation() {
    let arr1 = compute_destination_arrival("17-10-2026", "18:25", "09:55").unwrap();
    assert_eq!(
        arr1,
        Kolkata
            .with_ymd_and_hms(2026, 10, 18, 9, 55, 0)
            .single()
            .unwrap()
    );

    let arr2 = compute_destination_arrival("18-10-2026", "19:06", "23:50").unwrap();
    assert_eq!(
        arr2,
        Kolkata
            .with_ymd_and_hms(2026, 10, 18, 23, 50, 0)
            .single()
            .unwrap()
    );

    let before_dt = Kolkata
        .with_ymd_and_hms(2026, 10, 18, 9, 0, 0)
        .single()
        .unwrap();
    let (comp_before, _) =
        is_journey_completed(Some("17-10-2026"), Some("18:25"), Some("09:55"), 60, Some(before_dt));
    assert!(!comp_before);

    let after_dt = Kolkata
        .with_ymd_and_hms(2026, 10, 18, 11, 30, 0)
        .single()
        .unwrap();
    let (comp_after, _) =
        is_journey_completed(Some("17-10-2026"), Some("18:25"), Some("09:55"), 60, Some(after_dt));
    assert!(comp_after);
}

// ----------------- Input Validation Tests -----------------
#[test]
fn test_pnr_empty_string() {
    assert!(PNRTracker::new(None, Some(""), None, None, None, None, false).is_err());
}

#[test]
fn test_pnr_whitespace_only() {
    assert!(PNRTracker::new(None, Some("   "), None, None, None, None, false).is_err());
}

#[test]
fn test_pnr_too_short() {
    assert!(PNRTracker::new(None, Some("12345"), None, None, None, None, false).is_err());
}

#[test]
fn test_pnr_too_long() {
    assert!(PNRTracker::new(None, Some("1234567890123"), None, None, None, None, false).is_err());
}

#[test]
fn test_pnr_alphabetic() {
    assert!(PNRTracker::new(None, Some("ABCDEFGHIJ"), None, None, None, None, false).is_err());
}

#[test]
fn test_pnr_alphanumeric_injection() {
    assert!(PNRTracker::new(None, Some("476333197A"), None, None, None, None, false).is_err());
}

#[test]
fn test_pnr_xss_injection() {
    assert!(PNRTracker::new(None, Some("<script>alert(1)</script>"), None, None, None, None, false).is_err());
}

#[test]
fn test_pnr_sqli_injection() {
    assert!(PNRTracker::new(None, Some("1234567890' OR '1'='1"), None, None, None, None, false).is_err());
}

#[test]
fn test_pnr_path_traversal_injection() {
    assert!(PNRTracker::new(None, Some("../../../etc/passwd"), None, None, None, None, false).is_err());
}

#[test]
fn test_pnr_hyphen_stripping() {
    let tracker = PNRTracker::new(None, Some("476-333-1979"), None, None, None, None, false).unwrap();
    assert_eq!(tracker.pnrs, vec!["4763331979".to_string()]);
}

#[test]
fn test_pnr_deduplication_in_list() {
    let tracker = PNRTracker::new(None, Some("4763331979, 4763331979, 4763331979"), None, None, None, None, false).unwrap();
    assert_eq!(tracker.pnrs.len(), 1);
    assert_eq!(tracker.pnrs[0], "4763331979");
}

// ----------------- Status Transitions Tests -----------------
#[test]
fn test_cnf_to_cnf_no_improvement() {
    assert!(!is_improvement("CNF", "CNF"));
    assert!(!is_improvement("CNF / B3 / 45", "CNF / B3 / 46"));
}

#[test]
fn test_rac_to_cnf_is_improvement() {
    assert!(is_improvement("RAC 5", "CNF"));
    assert!(is_improvement("RAC 1", "CNF / S2 / 12"));
}

#[test]
fn test_wl_to_rac_is_improvement() {
    assert!(is_improvement("GNWL 10", "RAC 20"));
}

#[test]
fn test_wl_reduction_is_improvement() {
    assert!(is_improvement("GNWL 15", "GNWL 12"));
    assert!(is_improvement("RLWL 5", "RLWL 2"));
}

#[test]
fn test_wl_increase_is_not_improvement() {
    assert!(!is_improvement("GNWL 10", "GNWL 15"));
}

#[test]
fn test_rac_number_decrease_is_improvement() {
    assert!(is_improvement("RAC 10", "RAC 5"));
}

#[test]
fn test_rac_number_increase_is_not_improvement() {
    assert!(!is_improvement("RAC 5", "RAC 10"));
}

#[test]
fn test_unknown_status_never_improves() {
    assert!(!is_improvement("UNKNOWN", "FOOBAR"));
    assert!(!is_improvement("GNWL 10", "UNKNOWN"));
}

// ----------------- Stations Integrity Tests -----------------
#[test]
fn test_exact_lookup_nagpur() {
    let (code, name, hi) = get_station_info("NGP", "Nagpur");
    assert_eq!(code, "NGP");
    assert_eq!(name, "Nagpur Junction");
    assert_eq!(hi, "नागपुर जंक्शन");
}

#[test]
fn test_exact_lookup_ayodhya() {
    let (code, name, hi) = get_station_info("AY", "Ayodhya");
    assert_eq!(code, "AY");
    assert_eq!(name, "Ayodhya");
    assert_eq!(hi, "अयोध्या");
}

#[test]
fn test_exact_lookup_prayagraj() {
    let (code, name, hi) = get_station_info("PRYJ", "Prayagraj");
    assert_eq!(code, "PRYJ");
    assert_eq!(name, "Prayagraj Junction");
    assert_eq!(hi, "प्रयागराज जंक्शन");
}

#[test]
fn test_junction_suffix_fallback_transliteration() {
    let (_, name, hi) = get_station_info("XYZJ", "Someplace Junction");
    assert_eq!(name, "Someplace Junction");
    assert_eq!(hi, "Someplace जंक्शन");
}

#[test]
fn test_unknown_code_returns_passthrough() {
    let (code, name, _) = get_station_info("UNKN", "Unknown Place");
    assert_eq!(code, "UNKN");
    assert_eq!(name, "Unknown Place");
}

// ----------------- Persistence & Atomic Write Tests -----------------
#[test]
fn test_atomic_write_creates_valid_json() {
    let file = NamedTempFile::new().unwrap();
    let mut map = std::collections::HashMap::new();
    map.insert("4763331979".to_string(), json!({"pnr": "4763331979", "status": "CNF"}));

    save_state_file(file.path(), &map).unwrap();
    let loaded = load_state_file(file.path()).unwrap();
    assert_eq!(loaded.len(), 1);
    assert_eq!(loaded["4763331979"]["pnr"], "4763331979");
}

#[test]
fn test_corrupt_json_raises_runtime_error() {
    let file = NamedTempFile::new().unwrap();
    std::fs::write(file.path(), "{ corrupt json content ").unwrap();
    assert!(load_state_file(file.path()).is_err());
}

#[test]
fn test_missing_state_file_returns_empty_dict() {
    let non_existent = std::path::PathBuf::from("does_not_exist_at_all.json");
    let loaded = load_state_file(&non_existent).unwrap();
    assert!(loaded.is_empty());
}

// ----------------- Notifier Tests -----------------
#[tokio::test]
async fn test_dry_run_dispatch_always_succeeds() {
    let notifier = Notifier::new(None, None, None, None, None, Some(true));
    let changes = vec![StatusChange {
        passenger: "Passenger 1".to_string(),
        old_status: "GNWL 10".to_string(),
        new_status: "CNF".to_string(),
    }];
    let dummy_ticket = json!({
        "train_number": "12301",
        "train_name": "Rajdhani Express",
        "date_of_journey": "20-10-2026",
        "from_station": "NDLS",
        "to_station": "HWH"
    });
    let success = notifier.send_alert("1234567890", &dummy_ticket, &changes, &dummy_ticket).await;
    assert!(success);
}
