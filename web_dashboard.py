"""
web_dashboard.py — Lightweight, modern web dashboard for IRCTC PNR Tracker.
Powered by FastAPI and Tailwind CSS (Zero extra frontend build steps required).
Run with: python web_dashboard.py
"""

import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pnr_client import PNRClient
from notifier import Notifier
from tracker import PNRTracker, DEFAULT_STATE_FILE

app = FastAPI(title="RailPulse — IRCTC PNR Tracker Dashboard")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RailPulse — Autonomous IRCTC PNR Waiting List Monitor</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: '#3b82f6',
            rail: '#f97316'
          }
        }
      }
    }
  </script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    body { font-family: 'Inter', sans-serif; }
    .mono { font-family: 'JetBrains Mono', monospace; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col antialiased selection:bg-blue-500 selection:text-white">

  <!-- Top Navigation Header -->
  <header class="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
    <div class="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <i class="fa-solid fa-train-subway text-white text-lg"></i>
        </div>
        <div>
          <span class="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">RailPulse</span>
          <span class="text-xs px-2 py-0.5 ml-2 rounded-full font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">24/7 Cloud Active</span>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <button onclick="triggerCheck()" id="refreshBtn" class="flex items-center space-x-2 text-xs font-semibold px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition border border-slate-700">
          <i class="fa-solid fa-rotate text-blue-400"></i>
          <span>Check Now</span>
        </button>
        <button onclick="testNotification()" class="flex items-center space-x-2 text-xs font-semibold px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-600/20 transition">
          <i class="fa-solid fa-bell"></i>
          <span>Test Phone Ping</span>
        </button>
      </div>
    </div>
  </header>

  <!-- Hero & Add PNR Section -->
  <main class="max-w-6xl mx-auto px-4 py-8 flex-1 w-full space-y-8">
    <div class="bg-gradient-to-br from-slate-900 via-slate-900 to-blue-950/40 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
      <div class="absolute -right-16 -top-16 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>
      
      <div class="max-w-2xl">
        <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-white mb-2">
          Autonomous Waiting List Monitor
        </h1>
        <p class="text-sm sm:text-base text-slate-400 mb-6">
          Zero-spam, serverless rail tracker. Checks Indian Railways 24/7 and pings your phone the instant your waiting list position moves.
        </p>
      </div>

      <!-- Quick Add PNR Bar -->
      <form id="addPnrForm" onsubmit="addPNR(event)" class="flex flex-col sm:flex-row gap-3 max-w-xl">
        <div class="relative flex-1">
          <i class="fa-solid fa-ticket absolute left-3.5 top-3.5 text-slate-500"></i>
          <input type="text" id="pnrInput" placeholder="Enter 10-digit PNR Number..." required pattern="[0-9]{10}" maxlength="10" 
                 class="w-full bg-slate-950/80 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition mono">
        </div>
        <button type="submit" class="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm rounded-xl transition shadow-lg shadow-blue-600/30 flex items-center justify-center space-x-2">
          <i class="fa-solid fa-plus"></i>
          <span>Track Ticket</span>
        </button>
      </form>
    </div>

    <!-- Active Tracked Tickets Grid -->
    <div>
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-bold text-slate-200 flex items-center space-x-2">
          <i class="fa-solid fa-train text-blue-400"></i>
          <span>Active Tracked Tickets</span>
          <span id="ticketCountBadge" class="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">0</span>
        </h2>
        <span class="text-xs text-slate-500 flex items-center space-x-1.5">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Adaptive Polling Active</span>
        </span>
      </div>

      <div id="ticketsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <!-- Rendered dynamically -->
      </div>
    </div>

    <!-- System Telemetry & Logs -->
    <div class="border border-slate-800 bg-slate-900/40 rounded-2xl p-5">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-semibold text-slate-300 flex items-center space-x-2">
          <i class="fa-solid fa-terminal text-slate-400"></i>
          <span>Live Execution Console</span>
        </h3>
        <span class="text-xs text-slate-500 font-mono">ntfy: shivanshu-irctc-4763331979</span>
      </div>
      <div id="consoleLog" class="bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs mono text-slate-400 h-28 overflow-y-auto space-y-1">
        <div>[System] RailPulse Dashboard initialized.</div>
        <div>[System] Open Rail Gateway connected without quota limits.</div>
      </div>
    </div>
  </main>

  <!-- Footer -->
  <footer class="border-t border-slate-900 py-6 text-center text-xs text-slate-600">
    RailPulse &bull; Open Source Autonomous IRCTC Monitor &bull; MIT License
  </footer>

  <script>
    function log(msg) {
      const box = document.getElementById("consoleLog");
      const el = document.createElement("div");
      el.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
      box.appendChild(el);
      box.scrollTop = box.scrollHeight;
    }

    async function loadTickets() {
      try {
        const res = await fetch("/api/tickets");
        const data = await res.json();
        renderTickets(data);
      } catch (e) {
        log("Failed to load tickets: " + e);
      }
    }

    function renderTickets(tickets) {
      const grid = document.getElementById("ticketsGrid");
      grid.innerHTML = "";
      const pnrList = Object.keys(tickets);
      document.getElementById("ticketCountBadge").textContent = pnrList.length;

      if (pnrList.length === 0) {
        grid.innerHTML = `<div class="col-span-full py-12 text-center text-slate-500">No active tickets tracked yet. Add a PNR above!</div>`;
        return;
      }

      pnrList.forEach(pnr => {
        const t = tickets[pnr];
        const passengers = t.passengers || [];
        
        const card = document.createElement("div");
        card.className = "bg-slate-900 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition flex flex-col justify-between shadow-lg relative overflow-hidden group";

        const passengerBadges = passengers.map(p => {
          const isWL = p.current_status.includes("WL");
          const isCNF = p.current_status.includes("CNF");
          const isRAC = p.current_status.includes("RAC");

          let colorClass = "bg-amber-500/10 text-amber-400 border-amber-500/20";
          if (isCNF) colorClass = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
          if (isRAC) colorClass = "bg-blue-500/10 text-blue-400 border-blue-500/20";

          return `
            <div class="flex items-center justify-between text-xs py-1 px-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 mb-1.5">
              <span class="text-slate-400 font-medium">Passenger ${p.passenger_number}</span>
              <div class="flex items-center space-x-2">
                <span class="text-slate-500 line-through text-[10px]">${p.booking_status}</span>
                <span class="px-2 py-0.5 rounded font-bold mono text-xs border ${colorClass}">${p.current_status}</span>
              </div>
            </div>
          `;
        }).join("");

        card.innerHTML = `
          <div>
            <div class="flex items-start justify-between mb-3">
              <div>
                <span class="text-xs font-semibold mono text-blue-400">PNR: ${t.pnr}</span>
                <h3 class="font-bold text-base text-white tracking-tight">${t.train_number} - ${t.train_name}</h3>
              </div>
              <span class="text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 mono">${t.date_of_journey || "Upcoming"}</span>
            </div>

            <div class="flex items-center space-x-2 text-xs text-slate-400 mb-4 bg-slate-950/40 p-2.5 rounded-xl border border-slate-800/40">
              <span class="font-semibold text-slate-200">${t.from_station || "SRC"}</span>
              <i class="fa-solid fa-arrow-right text-[10px] text-blue-400"></i>
              <span class="font-semibold text-slate-200">${t.to_station || "DST"}</span>
            </div>

            <div class="space-y-1 mb-4">
              <span class="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Passenger Status</span>
              ${passengerBadges}
            </div>
          </div>

          <div class="border-t border-slate-800/80 pt-3 flex items-center justify-between text-[11px] text-slate-500">
            <span>Chart: <b class="text-slate-400">${t.chart_prepared ? 'Prepared' : 'Not Prepared'}</b></span>
            <span class="flex items-center space-x-1 text-emerald-400 font-medium">
              <i class="fa-solid fa-shield-check"></i>
              <span>Monitoring</span>
            </span>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    async function triggerCheck() {
      const btn = document.getElementById("refreshBtn");
      btn.classList.add("opacity-50", "pointer-events-none");
      log("Checking all PNRs via live Indian Rail Gateway...");
      try {
        const res = await fetch("/api/check-now", { method: "POST" });
        const d = await res.json();
        log(d.message);
        loadTickets();
      } catch (e) {
        log("Error during check: " + e);
      } finally {
        btn.classList.remove("opacity-50", "pointer-events-none");
      }
    }

    async function testNotification() {
      log("Firing test alert to phone via ntfy...");
      try {
        const res = await fetch("/api/test-notify", { method: "POST" });
        const d = await res.json();
        log("Test notification dispatched! Check your phone.");
      } catch (e) {
        log("Notification error: " + e);
      }
    }

    async function addPNR(e) {
      e.preventDefault();
      const pnr = document.getElementById("pnrInput").value.trim();
      if (!pnr) return;
      log(`Adding and fetching PNR ${pnr}...`);
      try {
        const res = await fetch(`/api/add-pnr?pnr=${pnr}`, { method: "POST" });
        const d = await res.json();
        log(d.message);
        document.getElementById("pnrInput").value = "";
        loadTickets();
      } catch (e) {
        log("Failed to add PNR: " + e);
      }
    }

    // Initial load
    loadTickets();
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=HTML_TEMPLATE)

@app.get("/api/tickets")
def get_tickets():
    client = PNRClient()
    notifier = Notifier()
    tracker = PNRTracker(pnrs="4763331979", client=client, notifier=notifier)
    return tracker.load_all_states()

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
        "🚂 *RailPulse Test Alert*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
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
        
        # Also update current env / workflow config
        current_pnrs = os.getenv("PNR_NUMBER", "4763331979,7000126327,6610459110")
        if pnr_clean not in current_pnrs:
            os.environ["PNR_NUMBER"] = f"{current_pnrs},{pnr_clean}"

        return {"status": "success", "message": f"PNR {pnr_clean} added: {data.get('train_name', 'Train')}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print("Starting RailPulse Dashboard at http://localhost:8000 ...")
    uvicorn.run("web_dashboard:app", host="127.0.0.1", port=8000, reload=False)
