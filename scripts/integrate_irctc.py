import os
import re

SKELETON_HTML = r"E:\irctc-pnr-notifier\irctc_skeleton\index.html"
OUTPUT_HTML = r"E:\irctc-pnr-notifier\static\index.html"

with open(SKELETON_HTML, "r", encoding="utf-8", errors="ignore") as f:
    html = f.read()

# 1. Update base href and ensure stylesheet links
html = re.sub(r'<base\s+href="[^"]*">', '<base href="/">', html)
if '<link rel="stylesheet" href="/static/styles.css">' not in html:
    html = html.replace('<link rel="stylesheet" href="styles.css">', '<link rel="stylesheet" href="/static/styles.css"><link rel="stylesheet" href="/styles.css">')

# 2. Strip broken external JS bundles from original Angular build
dead_scripts = [
    r'<script\s+src="runtime-es2015[^"]*"\s+type="module"></script>',
    r'<script\s+src="runtime-es5[^"]*"\s+nomodule=""\s+defer=""></script>',
    r'<script\s+src="polyfills-es5[^"]*"\s+nomodule=""\s+defer=""></script>',
    r'<script\s+src="polyfills-es2015[^"]*"\s+type="module"></script>',
    r'<script\s+src="main-es2015[^"]*"\s+type="module"></script>',
    r'<script\s+src="main-es5[^"]*"\s+nomodule=""\s+defer=""></script>',
    r'<script\s+type="text/javascript"\s+src="/RTTaZ-[^"]*"></script>',
    r'<script\s+defer=""\s+type="text/javascript"\s+id="interactive_js_adcode"[^>]*></script>',
    r'<script\s+async=\'async\'\s+src="https://cdn\.truenotify\.co\.in[^"]*"></script>',
]
for ds in dead_scripts:
    html = re.sub(ds, '', html, flags=re.I)

# 3. Create the RailPulse Live Monitoring UI section embedded directly into IRCTC layout
RAILPULSE_SECTION = """
<section id="railpulse-monitor" style="background: #f0f4f9; border-top: 3px solid #fb792b; border-bottom: 2px solid #cbd5e9; padding: 30px 15px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <div style="max-w: 1200px; margin: 0 auto; max-width: 1200px;">
    
    <!-- Header Strip -->
    <div style="background: #213d77; color: #ffffff; padding: 14px 20px; border-radius: 7px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
      <div style="display: flex; align-items: center; gap: 12px;">
        <div style="background: #fb792b; color: #ffffff; font-weight: 800; font-size: 11px; padding: 4px 8px; border-radius: 4px; text-transform: uppercase;">
          LIVE MONITOR
        </div>
        <div>
          <h2 style="margin: 0; font-size: 17px; font-weight: 700; color: #ffffff; letter-spacing: -0.3px;">
            IRCTC Autonomous PNR Waiting List Watcher
          </h2>
          <div style="font-size: 11px; color: #dcefff; font-family: monospace;">
            24/7 Cloud Background Engine &bull; Push Notification Alerts
          </div>
        </div>
      </div>
      
      <div style="display: flex; align-items: center; gap: 8px;">
        <button id="refreshBtn" onclick="triggerCheck()" style="background: #ffffff; color: #213d77; font-weight: 700; font-size: 12px; padding: 7px 14px; border: 1px solid #cbd5e9; border-radius: 5px; cursor: pointer;">
          Check Now
        </button>
        <button id="pingBtn" onclick="testNotification()" style="background: #fb792b; color: #ffffff; font-weight: 700; font-size: 12px; padding: 7px 14px; border: none; border-radius: 5px; cursor: pointer;">
          Test Push Alert
        </button>
      </div>
    </div>

    <!-- PNR Input Form & Telemetry -->
    <div style="background: #ffffff; border: 1px solid #cbd5e9; border-radius: 7px; padding: 16px 20px; margin-top: 14px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 14px;">
      <form id="addPnrForm" onsubmit="addPNR(event)" style="display: flex; flex-wrap: wrap; align-items: center; gap: 8px; flex: 1; min-width: 280px;">
        <label for="pnrInput" style="font-size: 12px; font-weight: 700; color: #213d77; white-space: nowrap;">
          Track New PNR:
        </label>
        <input type="text" id="pnrInput" placeholder="Enter 10-digit PNR Number..." required pattern="[0-9]{10}" maxlength="10"
               style="background: #f8fafc; border: 1px solid #cbd5e9; border-radius: 4px; padding: 7px 12px; font-size: 13px; font-family: monospace; flex: 1; min-width: 180px; outline: none;">
        <button type="submit" style="background: #213d77; color: #ffffff; font-size: 12px; font-weight: 700; padding: 7px 14px; border: none; border-radius: 4px; cursor: pointer;">
          Start Tracking
        </button>
      </form>

      <div style="display: flex; gap: 16px; font-size: 11px; font-family: monospace; color: #475569;">
        <div>Scheduler: <b style="color: #0f172a;">Every 5 Hours</b></div>
        <div>Channel: <b style="color: #15803d;">ntfy Webhook</b></div>
        <div>Spam Filter: <b style="color: #d26700;">100% Silent on No Change</b></div>
      </div>
    </div>

    <!-- Active Monitored Tickets Grid -->
    <div style="margin-top: 20px;">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; border-bottom: 1px solid #cbd5e9; padding-bottom: 6px;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <h3 style="margin: 0; font-size: 14px; font-weight: 700; color: #213d77; text-transform: uppercase;">
            Active Monitored Tickets
          </h3>
          <span id="ticketCountBadge" style="background: #213d77; color: #ffffff; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 12px; font-family: monospace;">
            3
          </span>
        </div>
        <div style="font-size: 11px; color: #64748b; font-family: monospace;">
          Seat Movement &bull; Waiting List Progression &bull; Chart Status
        </div>
      </div>

      <div id="ticketsGrid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 16px;">
        <!-- Loaded dynamically via JavaScript -->
      </div>
    </div>

    <!-- Real-time Operational Event Log -->
    <div style="background: #ffffff; border: 1px solid #cbd5e9; border-radius: 7px; padding: 14px 18px; margin-top: 20px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid #f1f5f9; padding-bottom: 6px;">
        <span style="font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase; font-family: monospace;">
          Operational Event Log
        </span>
        <span style="font-size: 10px; color: #94a3b8; font-family: monospace;">
          Topic: shivanshu-irctc-4763331979
        </span>
      </div>
      <div id="eventLogBox" style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 5px; padding: 10px; height: 90px; overflow-y: auto; font-family: monospace; font-size: 11px; color: #334155; line-height: 1.5;">
        <div style="color: #2563eb;">[Init] RailPulse Engine connected to IRCTC Portal.</div>
        <div style="color: #64748b;">[Status] Direct Open Rail Gateway operational without quota limitations.</div>
      </div>
    </div>

  </div>
</section>
"""

# 4. Inject RailPulse Section right after </app-jp-input>
if "</app-jp-input>" in html:
    html = html.replace("</app-jp-input>", "</app-jp-input>" + RAILPULSE_SECTION)
else:
    # Fallback before app-footer
    html = html.replace("<app-footer", RAILPULSE_SECTION + "<app-footer")

# 5. Inject Client Integration Script before </body>
CLIENT_SCRIPT = """
<script>
  function logEvent(msg) {
    const box = document.getElementById("eventLogBox");
    if (!box) return;
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
      logEvent("Failed to load tickets: " + e);
    }
  }

  function renderTickets(tickets) {
    const grid = document.getElementById("ticketsGrid");
    if (!grid) return;
    grid.innerHTML = "";
    const pnrList = Object.keys(tickets);
    const badge = document.getElementById("ticketCountBadge");
    if (badge) badge.textContent = pnrList.length;

    if (pnrList.length === 0) {
      grid.innerHTML = '<div style="grid-column: 1/-1; padding: 30px; text-align: center; color: #64748b; font-family: monospace; font-size: 12px;">No active tickets tracked. Enter a 10-digit PNR above!</div>';
      return;
    }

    pnrList.forEach(pnr => {
      const t = tickets[pnr];
      const passengers = t.passengers || [];

      const card = document.createElement("div");
      card.style.cssText = "background: #ffffff; border: 1px solid #cbd5e9; border-radius: 7px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 3px rgba(0,0,0,0.05);";

      const passengerRows = passengers.map(p => {
        const isCNF = p.current_status.includes("CNF");
        const isRAC = p.current_status.includes("RAC");

        let badgeStyle = "background: #dcefff; color: #1e3a8a; border: 1px solid #bfdbfe;";
        if (isCNF) badgeStyle = "background: #dcfce7; color: #166534; border: 1px solid #bbf7d0;";
        else if (isRAC) badgeStyle = "background: #fef3c7; color: #92400e; border: 1px solid #fde68a;";

        return `
          <div style="display: flex; align-items: center; justify-content: space-between; font-size: 11px; padding: 6px 10px; border-radius: 5px; background: #f8fafc; border: 1px solid #e2e8f0; margin-bottom: 6px;">
            <span style="font-weight: 600; color: #334155;">Passenger ${p.passenger_number}</span>
            <div style="display: flex; align-items: center; gap: 8px; font-family: monospace;">
              <span style="color: #94a3b8; text-decoration: line-through; font-size: 10px;">${p.booking_status}</span>
              <span style="font-weight: 700; font-size: 11px; padding: 2px 7px; border-radius: 3px; ${badgeStyle}">${p.current_status}</span>
            </div>
          </div>
        `;
      }).join("");

      card.innerHTML = `
        <div>
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
            <div>
              <span style="font-size: 11px; font-family: monospace; font-weight: 700; color: #213d77;">PNR: ${t.pnr}</span>
              <h4 style="margin: 2px 0 0 0; font-size: 14px; font-weight: 700; color: #0f172a;">${t.train_number} - ${t.train_name}</h4>
            </div>
            <span style="font-size: 10px; font-family: monospace; background: #f1f5f9; color: #475569; padding: 3px 8px; border-radius: 4px; border: 1px solid #e2e8f0;">${t.date_of_journey || "Scheduled"}</span>
          </div>

          <!-- Route Info -->
          <div style="display: flex; align-items: center; justify-content: space-between; font-size: 11px; font-family: monospace; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 5px; padding: 8px 10px; margin-bottom: 10px;">
            <span style="font-weight: 700; color: #1e293b;">${t.from_station || "ORIGIN"}</span>
            <span style="color: #64748b; font-weight: bold;">&rarr;</span>
            <span style="font-weight: 700; color: #1e293b;">${t.to_station || "DESTINATION"}</span>
          </div>

          <div style="margin-bottom: 10px;">
            <div style="font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; font-family: monospace; margin-bottom: 4px;">Passenger Seat Movement</div>
            ${passengerRows}
          </div>
        </div>

        <div style="border-top: 1px dashed #cbd5e9; padding-top: 8px; display: flex; justify-content: space-between; align-items: center; font-size: 10px; font-family: monospace; color: #64748b;">
          <span>Chart: <b style="color: #1e293b;">${t.chart_prepared ? 'Prepared' : 'Not Prepared'}</b></span>
          <span style="color: #166534; font-weight: 700;">Live Monitored</span>
        </div>
      `;

      grid.appendChild(card);
    });
  }

  async function triggerCheck() {
    const btn = document.getElementById("refreshBtn");
    if (btn) btn.disabled = true;
    logEvent("Checking active PNR status via live Railway Gateway...");
    try {
      const res = await fetch("/api/check-now", { method: "POST" });
      const d = await res.json();
      logEvent(d.message);
      loadTickets();
    } catch (e) {
      logEvent("Check error: " + e);
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  async function testNotification() {
    const btn = document.getElementById("pingBtn");
    if (btn) btn.disabled = true;
    logEvent("Dispatching test alert to configured device...");
    try {
      const res = await fetch("/api/test-notify", { method: "POST" });
      const d = await res.json();
      logEvent("Notification alert dispatched successfully.");
    } catch (e) {
      logEvent("Notification error: " + e);
    } finally {
      if (btn) btn.disabled = false;
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

  // Load tickets on ready
  window.addEventListener("DOMContentLoaded", loadTickets);
</script>
"""

html = html.replace("</body>", CLIENT_SCRIPT + "</body>")

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("Successfully generated", OUTPUT_HTML, "(Length:", len(html), ")")
