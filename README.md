# 🚂 IRCTC PNR Waiting List WhatsApp Notifier

An automated, 24/7 cloud notification system that monitors your Indian Railways (IRCTC) ticket and immediately sends you a WhatsApp message whenever your waiting list reduces (e.g. from `RLWL 10` ➔ `RLWL 9`, or gets promoted to `RAC` / `CNF`).

---

## ✨ Features
- **Instant WhatsApp Alerts**: Delivers formatted alerts directly to your phone via CallMeBot (100% Free).
- **WL Reduction Tracking**: Detects when your waitlist position improves, or when seats confirm (`RAC`, `CNF`).
- **Free 24/7 Cloud Automation**: Runs on GitHub Actions on a schedule (every 5 hours) without needing your computer to be turned on.
- **State Persistence**: Tracks historical status in `status_state.json` so you only get alerted when there is an actual change.
- **Offline / Dry-run Mode**: Test everything locally with mock data before connecting real APIs.

---

## 📲 Step 1: Get Free WhatsApp API Key (30 Seconds)

We use **CallMeBot**, a free gateway that sends messages directly to your WhatsApp without needing Twilio or business accounts:

1. Add the phone number **`+34 911 06 14 99`** to your phone contacts (e.g., name it "CallMeBot").
2. Open WhatsApp and send this message to that contact:
   ```text
   I allow callmebot to send me messages
   ```
3. Within 10–20 seconds, the bot will reply with your personal **`apikey`** (e.g., `123456`).
4. Keep your phone number (in international format with country code, e.g., `+919876543210`) and API key ready.

---

## 🔑 Step 2: Get Free RapidAPI PNR Key

1. Go to [RapidAPI](https://rapidapi.com/) and create a free account.
2. Search for **"IRCTC Indian Railway PNR Status"** (e.g., `irctc-indian-railway-pnr-status`).
3. Click **Subscribe to Test** (choose the Free tier with free monthly calls).
4. Copy your `X-RapidAPI-Key`.

---

## 💻 Step 3: Local Setup & Testing

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and fill in your details:
```ini
PNR_NUMBER=1234567890
RAPIDAPI_KEY=your_rapidapi_key
WHATSAPP_PHONE=+919876543210
CALLMEBOT_API_KEY=your_callmebot_api_key
```

### 3. Test Run
To test without calling external APIs (Dry Run):
```bash
python tracker.py --dry-run
```

To run a live check:
```bash
python tracker.py
```

---

## ☁️ Step 4: Run 24/7 in the Cloud (Free via GitHub Actions)

To let it run every 5 hours automatically even when your laptop is turned off:

1. Create a **Private** repository on GitHub and push this code:
   ```bash
   git remote add origin https://github.com/<your-username>/irctc-pnr-notifier.git
   git branch -M main
   git push -u origin main
   ```
2. In your GitHub repository, go to **Settings** ➔ **Secrets and variables** ➔ **Actions**.
3. Under **Repository secrets**, click **New repository secret** and add:
   - `PNR_NUMBER`: Your 10-digit PNR
   - `RAPIDAPI_KEY`: Your RapidAPI key
   - `WHATSAPP_PHONE`: Your WhatsApp number (e.g., `+919876543210`)
   - `CALLMEBOT_API_KEY`: Your CallMeBot API key
4. Enable workflow write permissions so it can save `status_state.json`:
   - Go to **Settings** ➔ **Actions** ➔ **General**.
   - Under **Workflow permissions**, select **"Read and write permissions"** and click **Save**.
5. Done! The workflow in `.github/workflows/pnr_monitor.yml` will automatically run every 5 hours. You can also trigger it manually anytime under the **Actions** tab by clicking **"Run workflow"**.

---

## 🧪 Running the Automated Test Suite

```bash
python -m unittest test_tracker.py
```
This runs 5 automated unit tests verifying:
- Baseline state detection
- RLWL reduction (e.g. `RLWL 10` ➔ `RLWL 9`)
- RAC and CNF promotion alerts
- WhatsApp message formatting
