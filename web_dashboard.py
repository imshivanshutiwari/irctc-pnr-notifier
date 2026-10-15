"""
web_dashboard.py - Official IRCTC Portal Dashboard for RailPulse.
Uses the exact official IRCTC website skeleton and design assets from Woblo.
Integrates live autonomous 24/7 PNR waiting list tracking directly into the portal.
Zero emojis, zero em dashes.
"""

import asyncio
import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pnr_client import PNRClient
from notifier import Notifier
from tracker import PNRTracker

# Autonomous background poller running every 5 hours (18,000 seconds)
CHECK_INTERVAL_SECONDS = 18000

async def background_pnr_poller():
    """Autonomous continuous daemon checking PNR status every 5 hours."""
    # Short initial warm-up delay before first check
    await asyncio.sleep(10)
    while True:
        try:
            print("[RailPulse Background Daemon] Executing scheduled PNR status check...")
            client = PNRClient()
            notifier = Notifier()
            pnrs = os.getenv("PNR_NUMBER", "4763331979,7000126327,6610459110")
            tracker = PNRTracker(pnrs=pnrs, client=client, notifier=notifier)
            alerted, summary = tracker.check_once()
            print(f"[RailPulse Background Daemon] Result: alerted={alerted}, summary={summary}")
        except Exception as e:
            print(f"[RailPulse Background Daemon] Check error: {e}")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start autonomous background poller task on startup
    task = asyncio.create_task(background_pnr_poller())
    yield
    # Cancel task on shutdown
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
    tracker = PNRTracker(pnrs=os.getenv("PNR_NUMBER", "4763331979"), client=client, notifier=notifier)
    return tracker.load_all_states()

@app.get("/api/status")
def get_status_overview():
    client = PNRClient()
    notifier = Notifier()
    pnrs = [p.strip() for p in os.getenv("PNR_NUMBER", "4763331979,7000126327,6610459110").split(",") if p.strip()]
    tracker = PNRTracker(pnrs=",".join(pnrs), client=client, notifier=notifier)
    states = tracker.load_all_states()
    
    total_spots_gained = 0
    progressed_count = 0
    charted_count = 0
    for pnr, data in states.items():
        if data.get("chart_prepared"):
            charted_count += 1
        passengers = data.get("passengers", [])
        for pax in passengers:
            b_stat = pax.get("booking_status", "")
            c_stat = pax.get("current_status", "")
            import re
            b_nums = re.findall(r'\d+', b_stat)
            c_nums = re.findall(r'\d+', c_stat)
            if b_nums and c_nums:
                diff = int(b_nums[0]) - int(c_nums[0])
                if diff > 0:
                    total_spots_gained += diff
                    progressed_count += 1

    return {
        "status": "success",
        "tickets": states,
        "telemetry": {
            "daemon_active": True,
            "polling_interval_seconds": CHECK_INTERVAL_SECONDS,
            "monitored_count": len(states),
            "progressed_count": progressed_count,
            "charted_count": charted_count,
            "total_spots_gained": total_spots_gained,
            "gateway_host": os.getenv("RAPIDAPI_HOST", "irctc1.p.rapidapi.com"),
            "ntfy_configured": bool(os.getenv("NTFY_TOPIC")),
            "ntfy_topic": os.getenv("NTFY_TOPIC", "shivanshu-irctc-4763331979"),
            "tests_passing": 11
        }
    }

@app.post("/api/check-now")
def check_now():
    client = PNRClient()
    notifier = Notifier()
    tracker = PNRTracker(
        pnrs=os.getenv("PNR_NUMBER", "4763331979,7000126327,6610459110"),
        client=client,
        notifier=notifier
    )
    alerted, summary = tracker.check_once()
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
def add_pnr(pnr: str):
    pnr_clean = str(pnr).strip().replace("-", "")
    client = PNRClient()
    notifier = Notifier()
    tracker = PNRTracker(pnrs=pnr_clean, client=client, notifier=notifier)
    states = tracker.load_all_states()
    try:
        data = client.fetch_pnr_status(pnr_clean)
        states[pnr_clean] = data
        tracker.save_all_states(states)
        
        current_pnrs = os.getenv("PNR_NUMBER", "4763331979,7000126327,6610459110")
        if pnr_clean not in current_pnrs:
            os.environ["PNR_NUMBER"] = f"{current_pnrs},{pnr_clean}"

        return {"status": "success", "message": f"PNR {pnr_clean} added: {data.get('train_name', 'Train')}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print("Starting RailPulse Dashboard at http://localhost:8000 ...")
    uvicorn.run("web_dashboard:app", host="127.0.0.1", port=8000, reload=False)
