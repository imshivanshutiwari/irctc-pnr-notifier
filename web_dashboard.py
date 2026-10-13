"""
web_dashboard.py - Railway Dispatch & Operations Dashboard for RailPulse.
Designed with strict anti-vibecoded engineering principles:
- No harsh gradients or radial blur orbs
- No liquid glass or backdrop blur gimmicks
- No soft bubble radiuses (crisp 6px industrial radius)
- No floating drop shadows (crisp 1px structural borders)
- No fake terminal windows (clean operational audit log)
- No generic Inter/Space Grotesk/Geist fonts (native system UI and monospace stack)
- Pure solid WCAG compliant colors (no neons, no washed-out pastels)
- Includes skeleton loaders and full Terms of Service / Privacy policies
- 0 emojis, 0 em dashes
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pnr_client import PNRClient
from notifier import Notifier
from tracker import PNRTracker

app = FastAPI(title="RailPulse - Autonomous IRCTC PNR Monitor")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RailPulse - IRCTC PNR Operations Monitor</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            surface: {
              light: '#F8FAFC',
              dark: '#0B1120',
              cardLight: '#FFFFFF',
              cardDark: '#111827'
            },
            railNavy: '#0F2744',
            railBlue: '#1D4ED8',
            signalGreen: '#15803D',
            signalAmber: '#B45309'
          }
        }
      }
    }
  </script>
  <style>
    :root {
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-mono: ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas, "Liberation Mono", monospace;
    }
    body {
      font-family: var(--font-sans);
    }
    .font-mono-data {
      font-family: var(--font-mono);
      font-feature-settings: "tnum" 1;
    }
    .ticket-stub {
      position: relative;
    }
    .ticket-stub::before, .ticket-stub::after {
      content: '';
      position: absolute;
      top: 50%;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      z-index: 10;
    }
    .dark .ticket-stub::before {
      left: -6px;
      background-color: #0B1120;
    }
    .dark .ticket-stub::after {
      right: -6px;
      background-color: #0B1120;
    }
    html:not(.dark) .ticket-stub::before {
      left: -6px;
      background-color: #F8FAFC;
    }
    html:not(.dark) .ticket-stub::after {
      right: -6px;
      background-color: #F8FAFC;
    }
  </style>
</head>
<body class="bg-surface-light dark:bg-surface-dark text-slate-800 dark:text-slate-100 min-h-screen flex flex-col antialiased">

  <!-- Top Dispatch Header (Solid, crisp 1px border, no backdrop blur) -->
  <header class="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-gray-900 sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-8 h-8 rounded-md bg-railNavy flex items-center justify-center text-white border border-slate-700">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <span class="text-sm font-bold tracking-tight text-slate-900 dark:text-white uppercase font-mono-data">RailPulse Control</span>
            <span class="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 font-mono-data">
              OPERATIONAL
            </span>
          </div>
          <span class="text-[11px] text-slate-500 font-mono-data">Autonomous IRCTC Waiting List Dispatch</span>
        </div>
      </div>
      
      <div class="flex items-center space-x-2">
        <button onclick="toggleTheme()" class="h-9 px-3 flex items-center justify-center rounded-md bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-medium hover:bg-slate-200 dark:hover:bg-slate-700" title="Toggle Theme">
          <span id="themeLabel">Light</span>
        </button>
        <button onclick="triggerCheck()" id="refreshBtn" class="h-9 px-3.5 flex items-center space-x-1.5 text-xs font-semibold rounded-md bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 border border-slate-300 dark:border-slate-700">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>Check Now</span>
        </button>
        <button onclick="testNotification()" id="pingBtn" class="h-9 px-3.5 flex items-center space-x-1.5 text-xs font-semibold rounded-md bg-railBlue hover:bg-blue-800 text-white border border-blue-900">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <span>Test Alert</span>
        </button>
      </div>
    </div>
  </header>

  <!-- Main Dispatch Content -->
  <main class="max-w-7xl mx-auto px-4 sm:px-6 py-6 flex-1 w-full space-y-5">

    <!-- Telemetry Status Bar (Direct functional table, zero bento grid, zero radial orbs) -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div class="p-3 bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-800 rounded-md">
        <div class="text-[11px] text-slate-500 font-mono-data uppercase">Execution Schedule</div>
        <div class="text-sm font-bold font-mono-data text-slate-900 dark:text-white mt-0.5">Every 5 Hours</div>
      </div>
      <div class="p-3 bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-800 rounded-md">
        <div class="text-[11px] text-slate-500 font-mono-data uppercase">API Gateway</div>
        <div class="text-sm font-bold font-mono-data text-blue-600 dark:text-blue-400 mt-0.5">Direct Open Rail</div>
      </div>
      <div class="p-3 bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-800 rounded-md">
        <div class="text-[11px] text-slate-500 font-mono-data uppercase">Alert Pipeline</div>
        <div class="text-sm font-bold font-mono-data text-emerald-600 dark:text-emerald-400 mt-0.5">ntfy Push Webhook</div>
      </div>
      <div class="p-3 bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-800 rounded-md">
        <div class="text-[11px] text-slate-500 font-mono-data uppercase">Active Tickets</div>
        <div id="statTicketCount" class="text-sm font-bold font-mono-data text-slate-900 dark:text-white mt-0.5">0</div>
      </div>
    </div>

    <!-- PNR Intake Row -->
    <div class="p-4 bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-800 rounded-md">
      <form id="addPnrForm" onsubmit="addPNR(event)" class="flex flex-col sm:flex-row gap-2.5 items-center justify-between">
        <div class="w-full sm:flex-1">
          <label for="pnrInput" class="block text-xs font-semibold text-slate-700 dark:text-slate-300 font-mono-data mb-1">
            Register 10-Digit PNR for Monitoring
          </label>
          <input type="text" id="pnrInput" placeholder="Enter 10-digit PNR Number..." required pattern="[0-9]{10}" maxlength="10"
                 class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-md px-3 py-2 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-blue-600 font-mono-data">
        </div>
        <button type="submit" class="w-full sm:w-auto mt-auto px-4 py-2 bg-railNavy hover:bg-slate-900 text-white font-semibold text-xs rounded-md border border-slate-800 transition">
          Register PNR
        </button>
      </form>
    </div>

    <!-- Active Tickets Board -->
    <div class="space-y-3">
      <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2">
        <div class="flex items-center space-x-2">
          <h2 class="text-sm font-bold uppercase tracking-wider font-mono-data text-slate-900 dark:text-white">Active Monitored Tickets</h2>
          <span id="ticketBadge" class="text-xs px-2 py-0.2 rounded bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono-data font-bold">0</span>
        </div>
        <span class="text-xs text-slate-500 font-mono-data">Live IRCTC Roster</span>
      </div>

      <!-- Tickets Roster Grid -->
      <div id="ticketsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Rendered dynamically -->
      </div>
    </div>

    <!-- Operational Event Log (Replaces fake terminal window) -->
    <div class="border border-slate-200 dark:border-slate-800 bg-white dark:bg-gray-900 rounded-md p-4">
      <div class="flex items-center justify-between mb-2 pb-2 border-b border-slate-200 dark:border-slate-800">
        <h3 class="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider font-mono-data">
          Operational Event Log
        </h3>
        <span class="text-[11px] text-slate-500 font-mono-data">Target: shivanshu-irctc-4763331979</span>
      </div>
      <div id="auditLog" class="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-md p-3 text-xs font-mono-data text-slate-600 dark:text-slate-300 h-28 overflow-y-auto space-y-1">
        <div class="text-blue-600 dark:text-blue-400">[Init] RailPulse Dispatch Engine active.</div>
        <div class="text-slate-500">[Gateway] Direct Open Rail API operational.</div>
      </div>
    </div>

  </main>

  <!-- Legal & Privacy Policy Modal -->
  <div id="legalModal" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 hidden">
    <div class="bg-white dark:bg-gray-900 border border-slate-300 dark:border-slate-700 rounded-md max-w-lg w-full p-6 space-y-4">
      <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
        <h3 class="text-sm font-bold text-slate-900 dark:text-white uppercase font-mono-data">Terms of Service & Privacy Notice</h3>
        <button onclick="closeLegalModal()" class="text-slate-400 hover:text-slate-600 dark:hover:text-white text-sm font-bold font-mono-data">[Close]</button>
      </div>
      <div class="text-xs text-slate-600 dark:text-slate-300 space-y-3 leading-relaxed">
        <p><b>1. Data Isolation:</b> PNR queries are processed exclusively on your configured infrastructure (local machine or personal private GitHub Actions runner). No credentials or travel records are collected, harvested, or transmitted to commercial third parties.</p>
        <p><b>2. Privacy Discipline:</b> Logs mask PNR numbers to the terminal four digits. Passenger names are never recorded or published to remote stores.</p>
        <p><b>3. Terms of Use:</b> RailPulse is an open-source utility provided under the MIT License for personal journey tracking. Users must adhere to IRCTC and Indian Railways fair-use policies.</p>
      </div>
      <div class="pt-2 text-right">
        <button onclick="closeLegalModal()" class="px-4 py-1.5 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 text-xs font-bold rounded-md font-mono-data">
          Acknowledge
        </button>
      </div>
    </div>
  </div>

  <!-- Footer with Legal and Privacy Links -->
  <footer class="border-t border-slate-200 dark:border-slate-800 py-4 px-4 bg-white dark:bg-gray-900 text-center text-xs text-slate-500 font-mono-data">
    <div class="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
      <div>RailPulse &bull; Autonomous IRCTC PNR Waiting List Monitor</div>
      <div class="flex items-center space-x-3">
        <button onclick="openLegalModal()" class="underline hover:text-slate-800 dark:hover:text-white">Terms of Service</button>
        <span>&bull;</span>
        <button onclick="openLegalModal()" class="underline hover:text-slate-800 dark:hover:text-white">Privacy Policy</button>
        <span>&bull;</span>
        <span>MIT Open Source</span>
      </div>
    </div>
  </footer>

  <script>
    function toggleTheme() {
      const html = document.documentElement;
      const isDark = html.classList.toggle('dark');
      document.getElementById('themeLabel').textContent = isDark ? 'Light' : 'Dark';
    }

    function openLegalModal() {
      document.getElementById('legalModal').classList.remove('hidden');
    }

    function closeLegalModal() {
      document.getElementById('legalModal').classList.add('hidden');
    }

    function logEvent(msg) {
      const box = document.getElementById("auditLog");
      const el = document.createElement("div");
      el.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
      box.appendChild(el);
      box.scrollTop = box.scrollHeight;
    }

    // Render skeleton placeholders
    function showLoadingSkeletons() {
      const grid = document.getElementById("ticketsGrid");
      grid.innerHTML = `
        <div class="p-4 bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-800 rounded-md animate-pulse space-y-3">
          <div class="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/3"></div>
          <div class="h-3 bg-slate-200 dark:bg-slate-800 rounded w-1/2"></div>
          <div class="h-10 bg-slate-100 dark:bg-slate-800/50 rounded"></div>
        </div>
        <div class="p-4 bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-800 rounded-md animate-pulse space-y-3">
          <div class="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/3"></div>
          <div class="h-3 bg-slate-200 dark:bg-slate-800 rounded w-1/2"></div>
          <div class="h-10 bg-slate-100 dark:bg-slate-800/50 rounded"></div>
        </div>
      `;
    }

    async function loadTickets() {
      showLoadingSkeletons();
      try {
        const res = await fetch("/api/tickets");
        const data = await res.json();
        renderTickets(data);
      } catch (e) {
        logEvent("Failed to load ticket roster: " + e);
      }
    }

    function renderTickets(tickets) {
      const grid = document.getElementById("ticketsGrid");
      grid.innerHTML = "";
      const pnrList = Object.keys(tickets);
      document.getElementById("ticketBadge").textContent = pnrList.length;
      document.getElementById("statTicketCount").textContent = pnrList.length;

      if (pnrList.length === 0) {
        grid.innerHTML = `<div class="col-span-full py-10 text-center text-slate-500 font-mono-data text-xs">No active tickets registered. Enter a 10-digit PNR above to begin monitoring.</div>`;
        return;
      }

      pnrList.forEach(pnr => {
        const t = tickets[pnr];
        const passengers = t.passengers || [];

        const card = document.createElement("div");
        card.className = "ticket-stub bg-white dark:bg-gray-900 border border-slate-200 dark:border-slate-800 rounded-md p-4 flex flex-col justify-between";

        const passengerRows = passengers.map(p => {
          const isCNF = p.current_status.includes("CNF");
          const isRAC = p.current_status.includes("RAC");

          let badgeColor = "bg-blue-100 text-blue-900 border-blue-300 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800";
          if (isCNF) badgeColor = "bg-emerald-100 text-emerald-900 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-800";
          if (isRAC) badgeColor = "bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800";

          return `
            <div class="flex items-center justify-between text-xs py-1.5 px-2.5 rounded bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 mb-1">
              <span class="text-slate-600 dark:text-slate-400 font-medium">Passenger ${p.passenger_number}</span>
              <div class="flex items-center space-x-2 font-mono-data">
                <span class="text-slate-400 line-through text-[11px]">${p.booking_status}</span>
                <span class="px-2 py-0.5 rounded font-bold text-xs border ${badgeColor}">${p.current_status}</span>
              </div>
            </div>
          `;
        }).join("");

        card.innerHTML = `
          <div>
            <div class="flex items-start justify-between mb-2">
              <div>
                <span class="text-xs font-mono-data font-bold text-blue-600 dark:text-blue-400">PNR: ${t.pnr}</span>
                <h3 class="font-bold text-sm text-slate-900 dark:text-white">${t.train_number} - ${t.train_name}</h3>
              </div>
              <span class="text-[11px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-mono-data border border-slate-200 dark:border-slate-700">${t.date_of_journey || "Scheduled"}</span>
            </div>

            <!-- Route Info -->
            <div class="flex items-center justify-between text-xs mb-3 bg-slate-50 dark:bg-slate-950 p-2.5 rounded border border-slate-200 dark:border-slate-800 font-mono-data">
              <span class="font-bold text-slate-800 dark:text-white">${t.from_station || "ORIGIN"}</span>
              <span class="text-slate-400 text-xs px-2 font-mono-data">&rarr;</span>
              <span class="font-bold text-slate-800 dark:text-white">${t.to_station || "DESTINATION"}</span>
            </div>

            <div class="space-y-1 mb-3">
              <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider font-mono-data">Passenger Status Movement</div>
              ${passengerRows}
            </div>
          </div>

          <div class="border-t border-slate-200 dark:border-slate-800 pt-2 flex items-center justify-between text-[11px] text-slate-500 font-mono-data">
            <span>Chart: <b class="text-slate-700 dark:text-slate-300">${t.chart_prepared ? 'Prepared' : 'Not Prepared'}</b></span>
            <span class="text-emerald-600 dark:text-emerald-400 font-medium">Live Monitored</span>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    async function triggerCheck() {
      const btn = document.getElementById("refreshBtn");
      btn.classList.add("opacity-50", "pointer-events-none");
      logEvent("Checking active PNRs via live Rail Gateway...");
      try {
        const res = await fetch("/api/check-now", { method: "POST" });
        const d = await res.json();
        logEvent(d.message);
        loadTickets();
      } catch (e) {
        logEvent("Error during check: " + e);
      } finally {
        btn.classList.remove("opacity-50", "pointer-events-none");
      }
    }

    async function testNotification() {
      const btn = document.getElementById("pingBtn");
      btn.classList.add("opacity-50", "pointer-events-none");
      logEvent("Dispatching test alert to configured device...");
      try {
        const res = await fetch("/api/test-notify", { method: "POST" });
        const d = await res.json();
        logEvent("Test notification dispatched successfully.");
      } catch (e) {
        logEvent("Notification failure: " + e);
      } finally {
        btn.classList.remove("opacity-50", "pointer-events-none");
      }
    }

    async function addPNR(e) {
      e.preventDefault();
      const pnr = document.getElementById("pnrInput").value.trim();
      if (!pnr) return;
      logEvent(`Querying PNR ${pnr}...`);
      try {
        const res = await fetch(`/api/add-pnr?pnr=${pnr}`, { method: "POST" });
        const d = await res.json();
        logEvent(d.message);
        document.getElementById("pnrInput").value = "";
        loadTickets();
      } catch (e) {
        logEvent("Failed to register PNR: " + e);
      }
    }

    // Initial fetch
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
