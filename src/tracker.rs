//! tracker.rs - Main orchestration engine for PNR tracking and alert generation.

use crate::cadence::{is_journey_completed, parse_journey_date};
use crate::notifier::{Notifier, StatusChange};
use crate::pnr_client::PNRClient;
use chrono::Utc;
use chrono_tz::Asia::Kolkata;
use regex::Regex;
use serde_json::Value;
use std::collections::{HashMap, HashSet};
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::sync::LazyLock;
use tracing::{info, warn};

pub const DEFAULT_STATE_FILE: &str = "status_state.json";
pub const DEFAULT_ARCHIVE_FILE: &str = "archived_pnrs.json";

static WAITLIST_RE: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)\b(GNWL|RLWL|PQWL|RQWL|TQWL|WL|W/L)\s*[- ]*\s*(\d+)\b").unwrap()
});
static RAC_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?i)\bRAC\s*[- ]*\s*(\d+)?\b").unwrap());
static CNF_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?i)\bCNF|CONFIRMED\b").unwrap());

pub fn classify_status(value: &str) -> (String, Option<i64>) {
    let text = value.trim().to_uppercase();
    if let Some(caps) = WAITLIST_RE.captures(&text) {
        let cat = caps[1].replace("W/L", "WL");
        let pos = caps[2].parse::<i64>().ok();
        return (cat, pos);
    }
    if let Some(caps) = RAC_RE.captures(&text) {
        let pos = caps.get(1).and_then(|m| m.as_str().parse::<i64>().ok());
        return ("RAC".to_string(), pos);
    }
    if CNF_RE.is_match(&text) {
        return ("CNF".to_string(), None);
    }
    ("UNKNOWN".to_string(), None)
}

pub fn is_improvement(old_status: &str, new_status: &str) -> bool {
    let (old_kind, old_pos) = classify_status(old_status);
    let (new_kind, new_pos) = classify_status(new_status);

    if new_kind == "UNKNOWN" {
        return false;
    }
    if new_kind == "CNF" {
        return old_kind != "CNF";
    }
    if new_kind == "RAC" {
        if old_kind != "RAC" && old_kind != "CNF" {
            return true;
        }
        if old_kind == "RAC" {
            if let (Some(o), Some(n)) = (old_pos, new_pos) {
                return n < o;
            }
        }
        return false;
    }
    if old_kind == new_kind {
        if let (Some(o), Some(n)) = (old_pos, new_pos) {
            return n < o;
        }
    }
    false
}

pub fn load_state_file(path: &Path) -> Result<HashMap<String, Value>, String> {
    if !path.exists() {
        return Ok(HashMap::new());
    }
    let content = fs::read_to_string(path)
        .map_err(|e| format!("Cannot safely read state file {:?}: {}", path, e))?;
    let val: Value = serde_json::from_str(&content)
        .map_err(|e| format!("Cannot safely read state file {:?}: {}", path, e))?;

    if !val.is_object() {
        return Err(format!("State file {:?} must contain a JSON object.", path));
    }

    let obj = val.as_object().unwrap();
    if let Some(pnr) = obj.get("pnr").and_then(|v| v.as_str()) {
        let mut map = HashMap::new();
        map.insert(pnr.to_string(), val.clone());
        return Ok(map);
    }

    let mut map = HashMap::new();
    for (k, v) in obj {
        map.insert(k.clone(), v.clone());
    }
    Ok(map)
}

pub fn save_state_file(path: &Path, states: &HashMap<String, Value>) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        let _ = fs::create_dir_all(parent);
    }
    let parent_dir = path.parent().unwrap_or_else(|| Path::new("."));
    let mut temp = tempfile::Builder::new()
        .prefix(&format!(".{}.", path.file_name().unwrap().to_str().unwrap()))
        .suffix(".tmp")
        .tempfile_in(parent_dir)
        .map_err(|e| format!("Failed to create tempfile: {}", e))?;

    let json_bytes = serde_json::to_vec_pretty(states)
        .map_err(|e| format!("Serialization error: {}", e))?;
    temp.write_all(&json_bytes)
        .map_err(|e| format!("Write error: {}", e))?;
    temp.flush()
        .map_err(|e| format!("Flush error: {}", e))?;

    temp.persist(path)
        .map_err(|e| format!("Persist rename error: {}", e))?;
    Ok(())
}

#[derive(Clone)]
pub struct PNRTracker {
    pub pnrs: Vec<String>,
    pub client: PNRClient,
    pub notifier: Notifier,
    pub state_file: PathBuf,
    pub archive_file: PathBuf,
    pub notify_on_first_run: bool,
}

impl PNRTracker {
    pub fn new(
        pnrs: Option<Vec<String>>,
        pnr_str: Option<&str>,
        client: Option<PNRClient>,
        notifier: Option<Notifier>,
        state_file: Option<&Path>,
        archive_file: Option<&Path>,
        notify_on_first_run: bool,
    ) -> Result<Self, String> {
        let mut raw_list = Vec::new();

        if let Some(s) = pnr_str {
            for part in s.replace(',', " ").split_whitespace() {
                let cleaned = part.trim().replace('-', "");
                if !cleaned.is_empty() {
                    raw_list.push(cleaned);
                }
            }
        }
        if let Some(list) = pnrs {
            for item in list {
                for part in item.replace(',', " ").split_whitespace() {
                    let cleaned = part.trim().replace('-', "");
                    if !cleaned.is_empty() {
                        raw_list.push(cleaned);
                    }
                }
            }
        }

        if raw_list.is_empty() {
            return Err("At least one PNR must be specified.".to_string());
        }

        let mut unique_pnrs = Vec::new();
        let mut seen = HashSet::new();
        for p in raw_list {
            if p.len() != 10 || !p.chars().all(|c| c.is_ascii_digit()) {
                return Err("Every PNR must contain exactly 10 digits.".to_string());
            }
            if seen.insert(p.clone()) {
                unique_pnrs.push(p);
            }
        }

        let s_path = state_file
            .map(|p| p.to_path_buf())
            .unwrap_or_else(|| PathBuf::from(DEFAULT_STATE_FILE));
        let a_path = archive_file
            .map(|p| p.to_path_buf())
            .unwrap_or_else(|| PathBuf::from(DEFAULT_ARCHIVE_FILE));

        Ok(Self {
            pnrs: unique_pnrs,
            client: client.unwrap_or_else(|| PNRClient::new(None, None, None)),
            notifier: notifier.unwrap_or_else(|| Notifier::new(None, None, None, None, None, None)),
            state_file: s_path,
            archive_file: a_path,
            notify_on_first_run,
        })
    }

    pub fn load_archived_pnrs(&self) -> HashSet<String> {
        if !self.archive_file.exists() {
            return HashSet::new();
        }
        if let Ok(content) = fs::read_to_string(&self.archive_file) {
            if let Ok(Value::Array(arr)) = serde_json::from_str(&content) {
                return arr
                    .into_iter()
                    .filter_map(|v| v.as_str().map(|s| s.trim().to_string()))
                    .collect();
            }
        }
        HashSet::new()
    }

    pub fn archive_pnr(&self, pnr: &str) {
        let mut archived = self.load_archived_pnrs();
        archived.insert(pnr.trim().to_string());
        let mut sorted: Vec<String> = archived.into_iter().collect();
        sorted.sort();
        if let Some(parent) = self.archive_file.parent() {
            let _ = fs::create_dir_all(parent);
        }
        let _ = fs::write(
            &self.archive_file,
            serde_json::to_string_pretty(&sorted).unwrap_or_default(),
        );
    }

    pub async fn check_all_pnrs(&self, allow_transient_errors: bool) -> Result<bool, String> {
        let mut all_states = load_state_file(&self.state_file)?;
        let archived = self.load_archived_pnrs();
        let mut any_alert_sent = false;

        for pnr in &self.pnrs {
            if archived.contains(pnr) {
                info!("[Tracker] PNR {} journey completed/archived. Skipping.", pnr);
                continue;
            }

            let status_res = self.client.fetch_pnr_status(pnr).await;
            let current_status = match status_res {
                Ok(st) => st,
                Err(e) => {
                    if allow_transient_errors {
                        warn!("[Tracker] Transient fetch failure for PNR {}: {}", pnr, e);
                        continue;
                    } else {
                        return Err(format!("Fetch failed for PNR ending {}: {}", &pnr[pnr.len().saturating_sub(4)..], e));
                    }
                }
            };

            // Check if journey is already completed
            let doj = current_status.get("date_of_journey").and_then(|v| v.as_str());
            let dep = current_status.get("departure_time").and_then(|v| v.as_str());
            let arr = current_status.get("arrival_time").and_then(|v| v.as_str());

            let (completed, _) = is_journey_completed(doj, dep, arr, 60, None);
            if completed {
                // If it finished a long time ago, archive without alert
                let now_ist = Utc::now().with_timezone(&Kolkata);
                let days_ago = doj
                    .and_then(|d| parse_journey_date(Some(d)))
                    .map(|jd| (now_ist.date_naive() - jd).num_days())
                    .unwrap_or(0);

                if days_ago > 2 {
                    info!("[Tracker] Journey for PNR {} completed {} days ago. Archiving without alert.", pnr, days_ago);
                    self.archive_pnr(pnr);
                    continue;
                }

                // If recently completed and previous state existed, alert and archive
                if all_states.contains_key(pnr) {
                    let change = StatusChange {
                        passenger: "All Passengers".to_string(),
                        old_status: "Active Tracking".to_string(),
                        new_status: "JOURNEY COMPLETED".to_string(),
                    };
                    self.notifier
                        .send_alert(pnr, &current_status, &[change], &current_status)
                        .await;
                    any_alert_sent = true;
                }
                self.archive_pnr(pnr);
                continue;
            }

            let prev_state = all_states.get(pnr);
            let mut genuine_improvements = Vec::new();

            let current_passengers = current_status
                .get("passengers")
                .and_then(|v| v.as_array())
                .cloned()
                .unwrap_or_default();

            if let Some(prev) = prev_state {
                let prev_passengers = prev
                    .get("passengers")
                    .and_then(|v| v.as_array())
                    .cloned()
                    .unwrap_or_default();

                for (idx, p_curr) in current_passengers.iter().enumerate() {
                    let p_curr_st = p_curr
                        .get("current_status")
                        .and_then(|v| v.as_str())
                        .unwrap_or("UNKNOWN");

                    let p_prev_st = prev_passengers
                        .get(idx)
                        .and_then(|p| p.get("current_status"))
                        .and_then(|v| v.as_str())
                        .unwrap_or("UNKNOWN");

                    if is_improvement(p_prev_st, p_curr_st) {
                        genuine_improvements.push(StatusChange {
                            passenger: format!("Passenger {}", idx + 1),
                            old_status: p_prev_st.to_string(),
                            new_status: p_curr_st.to_string(),
                        });
                    }
                }
            } else if self.notify_on_first_run {
                for (idx, p_curr) in current_passengers.iter().enumerate() {
                    let p_curr_st = p_curr
                        .get("current_status")
                        .and_then(|v| v.as_str())
                        .unwrap_or("UNKNOWN");

                    genuine_improvements.push(StatusChange {
                        passenger: format!("Passenger {}", idx + 1),
                        old_status: "INITIAL MONITORING".to_string(),
                        new_status: p_curr_st.to_string(),
                    });
                }
            }

            if !genuine_improvements.is_empty() {
                let alert_success = self
                    .notifier
                    .send_alert(pnr, &current_status, &genuine_improvements, &current_status)
                    .await;

                if alert_success || self.notifier.dry_run {
                    all_states.insert(pnr.clone(), current_status);
                    any_alert_sent = true;
                }
            } else {
                all_states.insert(pnr.clone(), current_status);
            }
        }

        save_state_file(&self.state_file, &all_states)?;
        Ok(any_alert_sent)
    }
}
