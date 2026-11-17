//! notifier.rs - Notification dispatch engine for IRCTC PNR status alerts.

use serde::Serialize;
use serde_json::Value;
use std::env;
use std::time::Duration;
use tracing::{error, info, warn};

#[derive(Debug, Clone)]
pub struct Notifier {
    pub whatsapp_phone: Option<String>,
    pub callmebot_api_key: Option<String>,
    pub telegram_bot_token: Option<String>,
    pub telegram_chat_id: Option<String>,
    pub ntfy_topic: Option<String>,
    pub dry_run: bool,
    client: reqwest::Client,
}

#[derive(Debug, Serialize, Clone)]
pub struct StatusChange {
    pub passenger: String,
    pub old_status: String,
    pub new_status: String,
}

impl Notifier {
    pub fn new(
        whatsapp_phone: Option<String>,
        callmebot_api_key: Option<String>,
        telegram_bot_token: Option<String>,
        telegram_chat_id: Option<String>,
        ntfy_topic: Option<String>,
        dry_run: Option<bool>,
    ) -> Self {
        let is_dry_run = dry_run.unwrap_or_else(|| {
            env::var("DRY_RUN")
                .map(|v| v.trim().eq_ignore_ascii_case("true"))
                .unwrap_or(false)
        });

        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(15))
            .build()
            .unwrap_or_default();

        Self {
            whatsapp_phone: whatsapp_phone.or_else(|| env::var("WHATSAPP_PHONE").ok()),
            callmebot_api_key: callmebot_api_key.or_else(|| env::var("CALLMEBOT_API_KEY").ok()),
            telegram_bot_token: telegram_bot_token.or_else(|| env::var("TELEGRAM_BOT_TOKEN").ok()),
            telegram_chat_id: telegram_chat_id.or_else(|| env::var("TELEGRAM_CHAT_ID").ok()),
            ntfy_topic: ntfy_topic.or_else(|| env::var("NTFY_TOPIC").ok()),
            dry_run: is_dry_run,
            client,
        }
    }

    pub fn format_alert_message(
        &self,
        pnr: &str,
        train_info: &Value,
        changes: &[StatusChange],
        current_state: &Value,
    ) -> String {
        let train_num = train_info
            .get("train_number")
            .and_then(|v| v.as_str())
            .unwrap_or("Unknown");
        let train_name = train_info
            .get("train_name")
            .and_then(|v| v.as_str())
            .unwrap_or("");
        let doj = train_info
            .get("date_of_journey")
            .and_then(|v| v.as_str())
            .unwrap_or("");
        let from_stn = train_info
            .get("from_station")
            .and_then(|v| v.as_str())
            .unwrap_or("");
        let to_stn = train_info
            .get("to_station")
            .and_then(|v| v.as_str())
            .unwrap_or("");

        let mut lines = vec![
            "*IRCTC WAITING LIST UPDATE*".to_string(),
            "-------------------".to_string(),
            format!("*PNR:* `{}`", pnr),
        ];

        if !train_num.is_empty() || !train_name.is_empty() {
            lines.push(format!("*Train:* {} - {}", train_num, train_name).trim().to_string());
        }
        if !doj.is_empty() {
            lines.push(format!("*Journey Date:* {}", doj));
        }
        if !from_stn.is_empty() && !to_stn.is_empty() {
            lines.push(format!("*Route:* {} -> {}", from_stn, to_stn));
        }

        lines.push("-------------------".to_string());
        lines.push("*Status Changes:*".to_string());

        for change in changes {
            let p_id = &change.passenger;
            let old_st = &change.old_status;
            let new_st = &change.new_status;

            let tag = if new_st.contains("CNF") || new_st.contains("CONFIRMED") {
                "CONFIRMED"
            } else if new_st.contains("RAC") {
                "RAC"
            } else {
                "UPDATED"
            };

            lines.push(format!(
                "- *{}*: {} -> *{}* [{}]",
                p_id, old_st, new_st, tag
            ));
        }

        if let Some(chart_prep) = current_state.get("chart_prepared").and_then(|v| v.as_bool()) {
            lines.push("-------------------".to_string());
            let chart_status = if chart_prep {
                "CHART PREPARED"
            } else {
                "CHART NOT PREPARED"
            };
            lines.push(format!("*Chart Status:* {}", chart_status));
        }

        lines.join("\n")
    }

    pub async fn send_alert(
        &self,
        pnr: &str,
        train_info: &Value,
        changes: &[StatusChange],
        current_state: &Value,
    ) -> bool {
        let message = self.format_alert_message(pnr, train_info, changes, current_state);

        if self.dry_run {
            println!("\n========== [DRY RUN ALERT PREVIEW] ==========");
            println!("{}", message);
            println!("=============================================\n");
            return true;
        }

        let mut dispatched_any = false;
        let mut overall_success = false;

        // 1. ntfy.sh
        if let Some(topic) = &self.ntfy_topic {
            if !topic.trim().is_empty() {
                dispatched_any = true;
                let title = format!("IRCTC PNR Alert: {}", pnr);
                if self.send_ntfy(topic, &message, &title).await {
                    overall_success = true;
                }
            }
        }

        // 2. Telegram
        if let (Some(token), Some(chat_id)) = (&self.telegram_bot_token, &self.telegram_chat_id) {
            if !token.trim().is_empty() && !chat_id.trim().is_empty() {
                dispatched_any = true;
                if self.send_telegram(token, chat_id, &message).await {
                    overall_success = true;
                }
            }
        }

        // 3. WhatsApp (CallMeBot)
        if let (Some(phone), Some(key)) = (&self.whatsapp_phone, &self.callmebot_api_key) {
            if !phone.trim().is_empty() && !key.trim().is_empty() {
                dispatched_any = true;
                if self.send_whatsapp_callmebot(phone, key, &message).await {
                    overall_success = true;
                }
            }
        }

        if !dispatched_any {
            warn!("[Notifier] No alert channels configured! Displaying alert on console.");
            println!("\n[UNCONFIGURED NOTIFIER FALLBACK]");
            println!("{}", message);
            println!("--------------------------------\n");
            return false;
        }

        overall_success
    }

    async fn send_ntfy(&self, topic: &str, message: &str, title: &str) -> bool {
        let url = format!("https://ntfy.sh/{}", topic.trim());
        let res = self
            .client
            .post(&url)
            .header("Title", title)
            .header("Priority", "high")
            .header("Tags", "train,ticket")
            .body(message.to_string())
            .send()
            .await;

        match res {
            Ok(resp) if resp.status().is_success() => {
                info!("[Notifier] ntfy push delivered successfully to topic: {}", topic);
                true
            }
            Ok(resp) => {
                error!("[Notifier] ntfy returned status: {}", resp.status());
                false
            }
            Err(e) => {
                error!("[Notifier] ntfy delivery failed: {}", e);
                false
            }
        }
    }

    async fn send_telegram(&self, token: &str, chat_id: &str, message: &str) -> bool {
        let url = format!("https://api.telegram.org/bot{}/sendMessage", token.trim());
        let body = serde_json::json!({
            "chat_id": chat_id.trim(),
            "text": message,
            "parse_mode": "Markdown"
        });

        match self.client.post(&url).json(&body).send().await {
            Ok(resp) if resp.status().is_success() => {
                info!("[Notifier] Telegram message delivered successfully.");
                true
            }
            Ok(resp) => {
                error!("[Notifier] Telegram returned status: {}", resp.status());
                false
            }
            Err(e) => {
                error!("[Notifier] Telegram delivery failed: {}", e);
                false
            }
        }
    }

    async fn send_whatsapp_callmebot(&self, phone: &str, api_key: &str, message: &str) -> bool {
        let encoded_text = urlencoding::encode(message);
        let url = format!(
            "https://api.callmebot.com/whatsapp.php?phone={}&text={}&apikey={}",
            phone.trim(),
            encoded_text,
            api_key.trim()
        );

        match self.client.get(&url).send().await {
            Ok(resp) if resp.status().is_success() => {
                info!("[Notifier] WhatsApp message delivered successfully.");
                true
            }
            Ok(resp) => {
                error!("[Notifier] WhatsApp CallMeBot returned status: {}", resp.status());
                false
            }
            Err(e) => {
                error!("[Notifier] WhatsApp delivery failed: {}", e);
                false
            }
        }
    }

    pub async fn send_simple_alert(&self, message: &str) -> bool {
        if self.dry_run {
            println!("\n========== [TEST ALERT PREVIEW] ==========");
            println!("{}", message);
            println!("==========================================\n");
            return true;
        }

        let mut dispatched_any = false;
        let mut overall_success = false;

        if let Some(topic) = &self.ntfy_topic {
            if !topic.trim().is_empty() {
                dispatched_any = true;
                if self.send_ntfy(topic, message, "RailPulse Test Alert").await {
                    overall_success = true;
                }
            }
        }

        if let (Some(token), Some(chat_id)) = (&self.telegram_bot_token, &self.telegram_chat_id) {
            if !token.trim().is_empty() && !chat_id.trim().is_empty() {
                dispatched_any = true;
                if self.send_telegram(token, chat_id, message).await {
                    overall_success = true;
                }
            }
        }

        if let (Some(phone), Some(key)) = (&self.whatsapp_phone, &self.callmebot_api_key) {
            if !phone.trim().is_empty() && !key.trim().is_empty() {
                dispatched_any = true;
                if self.send_whatsapp_callmebot(phone, key, message).await {
                    overall_success = true;
                }
            }
        }

        if !dispatched_any {
            println!("\n[TEST ALERT LOCAL SIMULATION]");
            println!("{}", message);
            println!("-----------------------------\n");
            return true;
        }

        overall_success
    }
}
