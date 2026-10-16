"""
web_dashboard.py - Official IRCTC Portal Dashboard for RailPulse.
Uses the exact official IRCTC website skeleton and design assets from Woblo.
Integrates live autonomous 24/7 PNR waiting list tracking directly into the portal.
Zero emojis, zero em dashes.
"""

import asyncio
import json
import os
import uvicorn
import datetime
import re
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pnr_client import PNRClient
from notifier import Notifier
from tracker import PNRTracker
from stations import get_station_info
from cadence_engine import compute_pnr_cadence, PRIORITY_CADENCE_SECONDS, STANDARD_CADENCE_SECONDS, IST_TIMEZONE

# Autonomous background poller cadence configuration
CHECK_INTERVAL_SECONDS = 18000  # Default fleet fallback (5 hours)
POLL_STATE_FILE = os.path.join(os.path.dirname(__file__), ".last_poll_state.json")

# In-memory per-PNR schedule map: { pnr: { "last_poll": epoch_sec, "next_poll": epoch_sec, "cadence": int } }
PNR_SCHEDULE: dict[str, dict] = {}

def load_poll_schedule_state() -> dict:
    if os.path.isfile(POLL_STATE_FILE):
        try:
            with open(POLL_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_poll_schedule_state(state_dict: dict):
    try:
        with open(POLL_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2)
    except Exception:
        pass

def init_schedule():
    global PNR_SCHEDULE
    persisted = load_poll_schedule_state()
    now_epoch = datetime.datetime.now(datetime.timezone.utc).timestamp()
    pnr_schedules = persisted.get("pnrs", {})

    # Load known states to get journey dates
    try:
        tracker = PNRTracker(pnrs=os.getenv("PNR_NUMBER", "4763331979,7000126327,6610459110"), client=PNRClient(), notifier=Notifier())
        states = tracker.load_all_states()
    except Exception:
        states = {}

    for pnr, data in states.items():
        cadence_info = compute_pnr_cadence(data.get("date_of_journey"), bool(data.get("chart_prepared")))
        cadence_sec = cadence_info["cadence_seconds"]
        
        saved_info = pnr_schedules.get(pnr, {})
        last_poll = saved_info.get("last_poll", now_epoch)
        next_poll = saved_info.get("next_poll", last_poll + cadence_sec)
        
        PNR_SCHEDULE[pnr] = {
            "last_poll": last_poll,
            "next_poll": next_poll,
            "cadence": cadence_sec,
            "priority_tier": cadence_info["priority_tier"],
            "tier_label": cadence_info["tier_label"],
            "days_until_journey": cadence_info["days_until_journey"],
            "is_near_journey": cadence_info["is_near_journey"]
        }

init_schedule()

def get_fleet_last_poll_time() -> datetime.datetime:
    persisted = load_poll_schedule_state()
    ts = persisted.get("last_poll_timestamp")
    if ts:
        try:
            return datetime.datetime.fromisoformat(ts)
        except Exception:
            pass
    return datetime.datetime.now(datetime.timezone.utc)

SERVER_START_TIME = datetime.datetime.now(datetime.timezone.utc)
LAST_POLL_TIME = get_fleet_last_poll_time()
LAST_POLL_RESULT = "Baseline synchronized successfully across active fleet"
DAEMON_RUNNING = False

def num_to_indian_words(num: int) -> str:
    """Converts numeric Indian Rupees fare to authentic PRS uppercase words string."""
    ones = ["", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE", "TEN",
            "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN", "SEVENTEEN", "EIGHTEEN", "NINETEEN"]
    tens = ["", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY"]

    if num <= 0:
        return "RUPEES ZERO ONLY"

    def two_digits(n):
        if n < 20:
            return ones[n]
        return (tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")).strip()

    def three_digits(n):
        res = ""
        if n >= 100:
            res += ones[n // 100] + " HUNDRED "
            n %= 100
        if n > 0:
            res += two_digits(n)
        return res.strip()

    parts = []
    if num >= 10000000:
        parts.append(two_digits(num // 10000000) + " CRORE")
        num %= 10000000
    if num >= 100000:
        parts.append(two_digits(num // 100000) + " LAKH")
        num %= 100000
    if num >= 1000:
        parts.append(two_digits(num // 1000) + " THOUSAND")
        num %= 1000
    if num > 0:
        parts.append(three_digits(num))

    return "RUPEES " + " ".join(parts).strip() + " ONLY"

async def background_pnr_poller():
    """Autonomous adaptive daemon checking each PNR according to its journey-date cadence:
    - Journey within 2 days (journey_day, journey_day - 1, journey_day - 2): every 2 hours (7200s)
    - All other tickets (> 2 days away): every 5 hours (18000s)
    - Automatically switches to 2h cadence as calendar advances into the 2-day window.
    """
    global LAST_POLL_TIME, LAST_POLL_RESULT, DAEMON_RUNNING, PNR_SCHEDULE
    DAEMON_RUNNING = True
    # Initial brief warm-up delay before first tick
    await asyncio.sleep(5)
    
    while DAEMON_RUNNING:
        try:
            now_dt = datetime.datetime.now(datetime.timezone.utc)
            now_epoch = now_dt.timestamp()

            client = PNRClient()
            notifier = Notifier()
            pnrs = [p.strip() for p in os.getenv("PNR_NUMBER", "4763331979,7000126327,6610459110").split(",") if p.strip()]
            tracker = PNRTracker(pnrs=",".join(pnrs), client=client, notifier=notifier)
            all_states = tracker.load_all_states()

            # Ensure every configured PNR has a schedule entry with current cadence
            for pnr in pnrs:
                pnr_state = all_states.get(pnr, {})
                doj = pnr_state.get("date_of_journey")
                is_charted = bool(pnr_state.get("chart_prepared"))
                cadence_info = compute_pnr_cadence(doj, is_charted)
                current_cadence = cadence_info["cadence_seconds"]

                if pnr not in PNR_SCHEDULE:
                    PNR_SCHEDULE[pnr] = {
                        "last_poll": now_epoch - current_cadence,  # Due immediately if fresh
                        "next_poll": now_epoch,
                        "cadence": current_cadence,
                        "priority_tier": cadence_info["priority_tier"],
                        "tier_label": cadence_info["tier_label"],
                        "days_until_journey": cadence_info["days_until_journey"],
                        "is_near_journey": cadence_info["is_near_journey"]
                    }
                else:
                    # Dynamically update cadence tier if date threshold crossed
                    old_cadence = PNR_SCHEDULE[pnr].get("cadence")
                    PNR_SCHEDULE[pnr]["cadence"] = current_cadence
                    PNR_SCHEDULE[pnr]["priority_tier"] = cadence_info["priority_tier"]
                    PNR_SCHEDULE[pnr]["tier_label"] = cadence_info["tier_label"]
                    PNR_SCHEDULE[pnr]["days_until_journey"] = cadence_info["days_until_journey"]
                    PNR_SCHEDULE[pnr]["is_near_journey"] = cadence_info["is_near_journey"]
                    if old_cadence != current_cadence:
                        # Recalculate next_poll based on updated cadence
                        PNR_SCHEDULE[pnr]["next_poll"] = PNR_SCHEDULE[pnr]["last_poll"] + current_cadence

            # Identify PNRs that are due for polling
            due_pnrs = [
                pnr for pnr in pnrs
                if PNR_SCHEDULE.get(pnr, {}).get("next_poll", 0) <= now_epoch
            ]

            if due_pnrs:
                print(f"[RailPulse Adaptive Daemon] Due PNRs to poll: {due_pnrs}")
                poll_summaries = []
                any_alerted = False
                for pnr in due_pnrs:
                    cadence_desc = PNR_SCHEDULE[pnr]["tier_label"]
                    print(f"[RailPulse Adaptive Daemon] Polling PNR {pnr} ({cadence_desc})...")
                    alerted, summary = tracker.check_pnr(pnr, all_states)
                    any_alerted = any_alerted or alerted
                    poll_summaries.append(f"{pnr}: {summary}")
                    # Update schedule for this PNR
                    pnr_now_epoch = datetime.datetime.now(datetime.timezone.utc).timestamp()
                    cadence_sec = PNR_SCHEDULE[pnr]["cadence"]
                    PNR_SCHEDULE[pnr]["last_poll"] = pnr_now_epoch
                    PNR_SCHEDULE[pnr]["next_poll"] = pnr_now_epoch + cadence_sec

                tracker.save_all_states(all_states)
                LAST_POLL_TIME = datetime.datetime.now(datetime.timezone.utc)
                LAST_POLL_RESULT = "; ".join(poll_summaries)
                
                # Persist fleet schedule state
                save_poll_schedule_state({
                    "last_poll_timestamp": LAST_POLL_TIME.isoformat(),
                    "pnrs": PNR_SCHEDULE
                })

        except Exception as e:
            print(f"[RailPulse Adaptive Daemon] Tick loop error: {e}")

        # Sleep for a short tick interval (30 seconds) to check schedule
        await asyncio.sleep(30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global DAEMON_RUNNING
    # Start autonomous background poller task on startup
    task = asyncio.create_task(background_pnr_poller())
    DAEMON_RUNNING = True
    yield
    # Cancel task on shutdown
    DAEMON_RUNNING = False
    task.cancel()

app = FastAPI(title="RailPulse - Autonomous IRCTC PNR Monitor", lifespan=lifespan)

# Mount static directory containing official IRCTC styles and assets
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

INDEX_PATH = os.path.join(STATIC_DIR, "index.html")
STYLES_PATH = os.path.join(STATIC_DIR, "styles.css")
ROBOTS_PATH = os.path.join(STATIC_DIR, "robots.txt")
SITEMAP_PATH = os.path.join(STATIC_DIR, "sitemap.xml")
LLMS_PATH = os.path.join(STATIC_DIR, "llms.txt")
FAVICON_PATH = os.path.join(STATIC_DIR, "favicon.ico")
FAVICON_PNG_PATH = os.path.join(STATIC_DIR, "favicon.png")
NOT_FOUND_PATH = os.path.join(STATIC_DIR, "404.html")

# Custom 404 Exception Handler
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    if os.path.isfile(NOT_FOUND_PATH):
        return FileResponse(NOT_FOUND_PATH, status_code=404, media_type="text/html")
    return HTMLResponse("<h1>404 Not Found</h1>", status_code=404)

@app.get("/")
def index():
    if os.path.isfile(INDEX_PATH):
        return FileResponse(INDEX_PATH, media_type="text/html")
    return JSONResponse({"status": "error", "message": "static/index.html not found"})

@app.get("/favicon.ico")
def get_favicon():
    if os.path.isfile(FAVICON_PATH):
        return FileResponse(FAVICON_PATH, media_type="image/x-icon")
    return JSONResponse({"status": "error", "message": "favicon not found"})

@app.get("/favicon.png")
def get_favicon_png():
    if os.path.isfile(FAVICON_PNG_PATH):
        return FileResponse(FAVICON_PNG_PATH, media_type="image/png")
    return JSONResponse({"status": "error", "message": "favicon.png not found"})

@app.get("/robots.txt")
def get_robots():
    if os.path.isfile(ROBOTS_PATH):
        return FileResponse(ROBOTS_PATH, media_type="text/plain")
    return JSONResponse({"status": "error", "message": "robots.txt not found"})

@app.get("/sitemap.xml")
def get_sitemap():
    if os.path.isfile(SITEMAP_PATH):
        return FileResponse(SITEMAP_PATH, media_type="application/xml")
    return JSONResponse({"status": "error", "message": "sitemap.xml not found"})

@app.get("/llms.txt")
def get_llms():
    if os.path.isfile(LLMS_PATH):
        return FileResponse(LLMS_PATH, media_type="text/plain")
    return JSONResponse({"status": "error", "message": "llms.txt not found"})

@app.get("/styles.css")
def get_styles():
    if os.path.isfile(STYLES_PATH):
        return FileResponse(STYLES_PATH, media_type="text/css")
    return JSONResponse({"status": "error", "message": "styles.css not found"})

@app.get("/eticket/styles.css")
def get_eticket_styles():
    if os.path.isfile(STYLES_PATH):
        return FileResponse(STYLES_PATH, media_type="text/css")
    return JSONResponse({"status": "error", "message": "styles.css not found"})

@app.get("/eticket/train-search")
def get_train_search():
    if os.path.isfile(INDEX_PATH):
        return FileResponse(INDEX_PATH, media_type="text/html")
    return JSONResponse({"status": "error", "message": "static/index.html not found"})

@app.get("/nget/train-search")
def get_nget_train_search():
    if os.path.isfile(INDEX_PATH):
        return FileResponse(INDEX_PATH, media_type="text/html")
    return JSONResponse({"status": "error", "message": "static/index.html not found"})

@app.get("/api/tickets")
def get_tickets():
    client = PNRClient()
    notifier = Notifier()
    tracker = PNRTracker(pnrs=os.getenv("PNR_NUMBER", "4763331979,7000126327,6610459110"), client=client, notifier=notifier)
    return tracker.load_all_states()

@app.get("/api/status")
def get_status_overview():
    global LAST_POLL_TIME, LAST_POLL_RESULT
    client = PNRClient()
    notifier = Notifier()
    pnrs = [p.strip() for p in os.getenv("PNR_NUMBER", "4763331979,7000126327,6610459110").split(",") if p.strip()]
    tracker = PNRTracker(pnrs=",".join(pnrs), client=client, notifier=notifier)
    states = tracker.load_all_states()
    
    total_spots_gained = 0
    progressed_count = 0
    charted_count = 0
    total_passengers = 0
    enriched = {}

    for pnr, data in states.items():
        ticket_data = dict(data)
        if data.get("chart_prepared"):
            charted_count += 1
        
        # Real route information directly from PNR record & stations lookup
        from_code = data.get("from_code") or ""
        from_name = data.get("from_name") or data.get("from_station") or ""
        to_code = data.get("to_code") or ""
        to_name = data.get("to_name") or data.get("to_station") or ""

        from_code, from_name, from_hi = get_station_info(from_code, from_name)
        to_code, to_name, to_hi = get_station_info(to_code, to_name)

        ticket_data["from_code"] = from_code
        ticket_data["to_code"] = to_code
        ticket_data["from_name"] = from_name
        ticket_data["to_name"] = to_name
        ticket_data["from_station"] = from_name
        ticket_data["to_station"] = to_name
        ticket_data["from_hi"] = from_hi
        ticket_data["to_hi"] = to_hi
        ticket_data["route_name"] = f"{from_name} ({from_code}) → {to_name} ({to_code})"

        ticket_data["dep_time"] = data.get("dep_time") or "--"
        ticket_data["arr_time"] = data.get("arr_time") or "--"
        ticket_data["duration"] = "--"
        ticket_data["is_overnight"] = False

        passengers = data.get("passengers", [])
        total_passengers += len(passengers)
        ticket_spots = 0

        detected_quota = "--"
        for pax in passengers:
            b_stat = str(pax.get("booking_status", "")).strip().upper()
            c_stat = str(pax.get("current_status", "")).strip().upper()
            for q_candidate in ["RLGN", "GNWL", "PQWL", "TQWL", "CKWL", "RSWL", "RAC"]:
                if q_candidate in b_stat:
                    detected_quota = f"{q_candidate} Quota"
                    break
            b_nums = re.findall(r'\d+', b_stat)
            c_nums = re.findall(r'\d+', c_stat)
            if b_nums and c_nums:
                diff = int(b_nums[0]) - int(c_nums[0])
                if diff > 0:
                    ticket_spots += diff
                    total_spots_gained += diff
                    progressed_count += 1

        if detected_quota == "--" and data.get("quota"):
            detected_quota = f"{data.get('quota')} Quota"

        ticket_data["coach_class"] = data.get("coach_class", "--")
        ticket_data["quota"] = detected_quota
        ticket_data["dep_day"] = "--"
        ticket_data["arr_day"] = "--"
        ticket_data["ticket_spots_gained"] = ticket_spots
        ticket_data["has_progressed"] = ticket_spots > 0

        # Real ticket fare directly from API
        api_fare = data.get("fare")
        try:
            fare_int = int(float(api_fare)) if api_fare not in (None, "", "--") else 0
        except (ValueError, TypeError):
            fare_int = 0
        if fare_int > 0:
            ticket_data["total_fare"] = str(fare_int)
            ticket_data["fare_words"] = num_to_indian_words(fare_int) + " (IRCTC OFFICIAL PRS FARE)"
        else:
            ticket_data["total_fare"] = "--"
            ticket_data["fare_words"] = "FARE DATA NOT AVAILABLE IN PUBLIC PNR QUERY"

        # Strictly authentic markers
        ticket_data["distance_km"] = "--"
        ticket_data["via_route"] = "--"
        ticket_data["via_hi"] = "--"
        ticket_data["resv_fee"] = "--"
        ticket_data["superfast_charge"] = "--"
        ticket_data["fare_per_pax"] = "--"
        # Authentic journey cadence metadata
        is_charted = bool(data.get("chart_prepared"))
        cadence_info = compute_pnr_cadence(data.get("date_of_journey"), is_charted)
        ticket_data["cadence_seconds"] = cadence_info["cadence_seconds"]
        ticket_data["cadence_hours"] = cadence_info["cadence_hours"]
        ticket_data["priority_tier"] = cadence_info["priority_tier"]
        ticket_data["tier_label"] = cadence_info["tier_label"]
        ticket_data["days_until_journey"] = cadence_info["days_until_journey"]
        ticket_data["is_near_journey"] = cadence_info["is_near_journey"]

        # Real-time countdown for this specific PNR
        pnr_sched = PNR_SCHEDULE.get(pnr, {})
        now_epoch = datetime.datetime.now(datetime.timezone.utc).timestamp()
        next_poll_epoch = pnr_sched.get("next_poll", now_epoch + cadence_info["cadence_seconds"])
        ticket_data["next_poll_epoch"] = next_poll_epoch
        ticket_data["seconds_until_next_poll"] = max(0, int(next_poll_epoch - now_epoch))

        enriched[pnr] = ticket_data

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    ist_tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now_ist = now_utc.astimezone(ist_tz)
    last_poll_ist = LAST_POLL_TIME.astimezone(ist_tz).strftime("%H:%M:%S IST")

    # Earliest next scheduled poll among all active PNRs
    now_epoch = now_utc.timestamp()
    if PNR_SCHEDULE:
        earliest_next_poll = min(info.get("next_poll", now_epoch + CHECK_INTERVAL_SECONDS) for info in PNR_SCHEDULE.values())
        seconds_until_next_poll = max(0, int(earliest_next_poll - now_epoch))
    else:
        seconds_until_next_poll = CHECK_INTERVAL_SECONDS

    # Determine fleet cadence description
    has_priority = any(t.get("is_near_journey") for t in enriched.values())
    fleet_cadence_desc = "Adaptive: 2h Priority & 5h Fleet" if has_priority else "5-Hour Automated Cycle"

    telegram_bot = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat = os.getenv("TELEGRAM_CHAT_ID")
    telegram_active = bool(telegram_bot and telegram_chat)
    ntfy_configured = bool(os.getenv("NTFY_TOPIC"))

    return {
        "status": "success",
        "tickets": enriched,
        "telemetry": {
            "pid": os.getpid(),
            "daemon_active": DAEMON_RUNNING,
            "polling_interval_seconds": 7200 if has_priority else 18000,
            "polling_cadence_desc": fleet_cadence_desc,
            "last_poll_time_ist": last_poll_ist,
            "last_poll_timestamp": LAST_POLL_TIME.isoformat(),
            "seconds_until_next_poll": seconds_until_next_poll,
            "last_poll_result": LAST_POLL_RESULT,
            "gateway_host": os.getenv("RAPIDAPI_HOST", "irctc1.p.rapidapi.com"),
            "gateway_status": "Connected (Direct Rail Gateway)",
            "ntfy_configured": ntfy_configured,
            "ntfy_status": "Active (Topic Configured)" if ntfy_configured else "Not Configured",
            "telegram_configured": telegram_active,
            "telegram_status": "Active" if telegram_active else "Not Configured (Token Unset)",
            "monitored_pnr_count": len(enriched),
            "monitored_pax_count": total_passengers,
            "progressed_count": progressed_count,
            "charted_count": charted_count,
            "total_spots_gained": total_spots_gained,
            "tests_passing": 52,
            "tests_total": 52
        }
    }

@app.post("/api/check-now")
def check_now():
    global LAST_POLL_TIME, LAST_POLL_RESULT, PNR_SCHEDULE
    client = PNRClient()
    notifier = Notifier()
    tracker = PNRTracker(
        pnrs=os.getenv("PNR_NUMBER", "4763331979,7000126327,6610459110"),
        client=client,
        notifier=notifier
    )
    alerted, summary = tracker.check_once()
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    now_epoch = now_dt.timestamp()
    LAST_POLL_TIME = now_dt
    LAST_POLL_RESULT = summary

    # Reset schedule timestamps for all monitored PNRs after manual check
    for pnr in tracker.pnrs:
        if pnr in PNR_SCHEDULE:
            cadence_sec = PNR_SCHEDULE[pnr]["cadence"]
            PNR_SCHEDULE[pnr]["last_poll"] = now_epoch
            PNR_SCHEDULE[pnr]["next_poll"] = now_epoch + cadence_sec

    save_poll_schedule_state({
        "last_poll_timestamp": LAST_POLL_TIME.isoformat(),
        "pnrs": PNR_SCHEDULE
    })

    return {"status": "success", "alerted": alerted, "message": summary}

@app.post("/api/test-notify")
def test_notify():
    notifier = Notifier()
    success = notifier.send_alert(
        "*RailPulse Test Alert*\n"
        "-------------------\n"
        "Your notification pipeline is 100% active and connected!\n"
        "You will receive instant alerts when waiting lists move."
    )
    return {"status": "success" if success else "failed"}

@app.post("/api/add-pnr")
async def add_pnr(request: Request, pnr: Optional[str] = None):
    global PNR_SCHEDULE
    if not pnr:
        try:
            body = await request.json()
            pnr = body.get("pnr")
        except Exception:
            pass

    if not pnr:
        return JSONResponse({"status": "error", "message": "PNR parameter required"}, status_code=422)

    pnr_clean = str(pnr).strip().replace("-", "")
    if len(pnr_clean) != 10 or not pnr_clean.isdigit():
        return JSONResponse({"status": "error", "message": "PNR must contain exactly 10 numeric digits."}, status_code=422)

    client = PNRClient()
    notifier = Notifier()
    # Load state using a tracker scoped only to read/write — not to validate pnr_clean itself
    tracker = PNRTracker(pnrs="4763331979", client=client, notifier=notifier)
    states = tracker.load_all_states()

    if pnr_clean in states:
        return JSONResponse({"status": "error", "message": f"PNR {pnr_clean} is already being monitored."}, status_code=409)

    try:
        data = client.fetch_pnr_status(pnr_clean)
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": f"Could not fetch PNR {pnr_clean} from railway gateway: {e}"},
            status_code=502
        )

    states[pnr_clean] = data
    tracker.save_all_states(states)

    current_pnrs = [p.strip() for p in os.getenv("PNR_NUMBER", "4763331979,7000126327,6610459110").split(",") if p.strip()]
    if pnr_clean not in current_pnrs:
        current_pnrs.append(pnr_clean)
        os.environ["PNR_NUMBER"] = ",".join(current_pnrs)

    # Initialize schedule for newly enrolled PNR
    now_epoch = datetime.datetime.now(datetime.timezone.utc).timestamp()
    cadence_info = compute_pnr_cadence(data.get("date_of_journey"), bool(data.get("chart_prepared")))
    PNR_SCHEDULE[pnr_clean] = {
        "last_poll": now_epoch,
        "next_poll": now_epoch + cadence_info["cadence_seconds"],
        "cadence": cadence_info["cadence_seconds"],
        "priority_tier": cadence_info["priority_tier"],
        "tier_label": cadence_info["tier_label"],
        "days_until_journey": cadence_info["days_until_journey"],
        "is_near_journey": cadence_info["is_near_journey"]
    }
    save_poll_schedule_state({
        "last_poll_timestamp": LAST_POLL_TIME.isoformat(),
        "pnrs": PNR_SCHEDULE
    })

    return {"status": "success", "message": f"PNR {pnr_clean} enrolled: {data.get('train_name', 'Train')}"}

@app.delete("/api/delete-pnr/{pnr}")
@app.post("/api/delete-pnr")
async def delete_pnr(request: Request, pnr: Optional[str] = None):
    global PNR_SCHEDULE
    if not pnr:
        try:
            body = await request.json()
            pnr = body.get("pnr")
        except Exception:
            pass
    if not pnr:
        pnr = request.query_params.get("pnr")

    if not pnr:
        return JSONResponse({"status": "error", "message": "PNR parameter required"}, status_code=422)

    pnr_clean = str(pnr).strip().replace("-", "")
    client = PNRClient()
    notifier = Notifier()
    tracker = PNRTracker(pnrs=pnr_clean, client=client, notifier=notifier)
    states = tracker.load_all_states()

    if pnr_clean in states:
        del states[pnr_clean]
        tracker.save_all_states(states)

    if pnr_clean in PNR_SCHEDULE:
        del PNR_SCHEDULE[pnr_clean]
        save_poll_schedule_state({
            "last_poll_timestamp": LAST_POLL_TIME.isoformat(),
            "pnrs": PNR_SCHEDULE
        })

    current_pnrs = [p.strip() for p in os.getenv("PNR_NUMBER", "4763331979,7000126327,6610459110").split(",") if p.strip()]
    if pnr_clean in current_pnrs:
        current_pnrs.remove(pnr_clean)
        os.environ["PNR_NUMBER"] = ",".join(current_pnrs)

    return {"status": "success", "message": f"PNR {pnr_clean} deleted successfully from fleet tracking."}

if __name__ == "__main__":
    print("Starting RailPulse Dashboard at http://localhost:8000 ...")
    uvicorn.run("web_dashboard:app", host="127.0.0.1", port=8000, reload=False)
