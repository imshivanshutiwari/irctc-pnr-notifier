"""
notifier.py — Notification dispatch engine for IRCTC PNR status alerts.
Supports:
1. WhatsApp via CallMeBot (100% Free personal WhatsApp gateway)
2. Telegram Bot (Free alternative)
3. Console logging fallback / Dry-run
"""

import os
import sys
import urllib.parse
import requests
from typing import Optional, Dict, Any

def safe_print(text: str):
    """Prints text safely even on consoles that do not support full UTF-8 / emojis (like Windows cp1252)."""
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            print(text.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8"))
        except Exception:
            print(text.encode("ascii", errors="replace").decode("ascii"))


class Notifier:
    def __init__(
        self,
        whatsapp_phone: Optional[str] = None,
        callmebot_api_key: Optional[str] = None,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        dry_run: bool = False
    ):
        self.whatsapp_phone = whatsapp_phone or os.getenv("WHATSAPP_PHONE")
        self.callmebot_api_key = callmebot_api_key or os.getenv("CALLMEBOT_API_KEY")
        self.telegram_bot_token = telegram_bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.dry_run = dry_run or os.getenv("DRY_RUN", "false").lower() == "true"

    def format_alert_message(
        self,
        pnr: str,
        train_info: Dict[str, Any],
        changes: list,
        current_state: Dict[str, Any]
    ) -> str:
        """
        Formats a clean, eye-catching notification message for WhatsApp/Telegram.
        """
        train_num = train_info.get("train_number", "Unknown")
        train_name = train_info.get("train_name", "")
        doj = train_info.get("date_of_journey", "")
        from_stn = train_info.get("from_station", "")
        to_stn = train_info.get("to_station", "")

        lines = [
            "🚂 *IRCTC WAITING LIST UPDATE!*",
            f"━━━━━━━━━━━━━━━━━━━",
            f"📍 *PNR:* `{pnr}`",
        ]

        if train_num or train_name:
            lines.append(f"🚆 *Train:* {train_num} - {train_name}".strip())
        if doj:
            lines.append(f"📅 *Journey Date:* {doj}")
        if from_stn and to_stn:
            lines.append(f"🛤️ *Route:* {from_stn} ➔ {to_stn}")

        lines.append(f"━━━━━━━━━━━━━━━━━━━")
        lines.append("⚡ *Status Changes:*")

        for change in changes:
            p_id = change.get("passenger", "Passenger")
            old_st = change.get("old_status", "N/A")
            new_st = change.get("new_status", "N/A")
            
            # Add celebratory icon if confirmed or RAC
            icon = "📈"
            if "CNF" in new_st.upper():
                icon = "🎉 *CONFIRMED!*"
            elif "RAC" in new_st.upper():
                icon = "🎫 *RAC!*"
            elif "WL" in new_st.upper() and "WL" in old_st.upper():
                icon = "🔻 *WL Reduced!*"

            lines.append(f"• *{p_id}:* {old_st} ➔ *{new_st}* ({icon})")

        lines.append(f"━━━━━━━━━━━━━━━━━━━")
        lines.append("⏰ Check irctc.co.in for final chart confirmation.")
        
        return "\n".join(lines)

    def send_whatsapp(self, message: str) -> bool:
        """
        Sends WhatsApp message via CallMeBot API.
        """
        if not self.whatsapp_phone or not self.callmebot_api_key:
            print("[Notifier] WhatsApp phone or CallMeBot API key missing.")
            return False

        if self.dry_run:
            safe_print(f"[Notifier - Dry Run] WhatsApp message simulated:\n{message}")
            return True

        encoded_text = urllib.parse.quote(message)
        # Ensure phone has + prefix for international format
        phone = self.whatsapp_phone if self.whatsapp_phone.startswith("+") else f"+{self.whatsapp_phone}"
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_text}&apikey={self.callmebot_api_key}"

        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                print("[Notifier] WhatsApp notification sent successfully.")
                return True
            else:
                print(f"[Notifier] CallMeBot API returned status {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            print(f"[Notifier] Failed to send WhatsApp message: {e}")
            return False

    def send_telegram(self, message: str) -> bool:
        """
        Sends Telegram message via Bot API.
        """
        if not self.telegram_bot_token or not self.telegram_chat_id:
            return False

        if self.dry_run:
            safe_print(f"[Notifier - Dry Run] Telegram message simulated:\n{message}")
            return True

        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code == 200:
                print("[Notifier] Telegram notification sent successfully.")
                return True
            else:
                print(f"[Notifier] Telegram returned status {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            print(f"[Notifier] Failed to send Telegram message: {e}")
            return False

    def send_alert(self, message: str) -> bool:
        """
        Sends alert to all configured channels (WhatsApp and/or Telegram).
        """
        sent = False
        if self.whatsapp_phone and self.callmebot_api_key:
            if self.send_whatsapp(message):
                sent = True

        if self.telegram_bot_token and self.telegram_chat_id:
            if self.send_telegram(message):
                sent = True

        if not sent:
            safe_print("[Notifier] No external delivery channels succeeded. Alert message:")
            safe_print(message)
            return self.dry_run

        return sent
