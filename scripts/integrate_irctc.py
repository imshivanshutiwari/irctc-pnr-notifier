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

# 3. Create the RailPulse Live Monitoring UI section styled identically to official IRCTC portal hero card
RAILPULSE_SECTION = """
<section id="railpulse-monitor" style="background: #f4f6fa; padding: 40px 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <div style="max-width: 1240px; margin: 0 auto;">
    
    <!-- Hero Card Container -->
    <div style="background: #ffffff; border-radius: 20px; border: 1px solid #e2e8f0; box-shadow: 0 10px 30px rgba(0,0,0,0.06); padding: 26px 30px; position: relative;">
      
      <!-- Top Header Row -->
      <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 16px; padding-bottom: 22px; border-bottom: 1px solid #f1f5f9;">
        <div>
          <div style="display: inline-flex; align-items: center; gap: 6px; background: #fff7ed; border: 1px solid #ffedd5; color: #d26700; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
            <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #f37023;"></span>
            Live Autonomous Watcher
          </div>
          <h2 style="margin: 0; font-size: 24px; font-weight: 800; color: #0f172a; letter-spacing: -0.5px; line-height: 1.2;">
            Your Tickets, <span style="color: #f37023;">Monitored Live</span>
          </h2>
          <p style="margin: 4px 0 0 0; font-size: 13px; color: #64748b; font-weight: 500;">
            24/7 background engine watching waiting list seat movement with instant push notifications
          </p>
        </div>
        
        <!-- Action Buttons (Pill-shaped) -->
        <div style="display: flex; align-items: center; gap: 10px;">
          <button id="refreshBtn" onclick="triggerCheck()" style="background: #ffffff; color: #0066b2; font-weight: 700; font-size: 13px; padding: 10px 20px; border: 1.5px solid #0066b2; border-radius: 9999px; cursor: pointer; transition: all 0.2s ease; display: inline-flex; align-items: center; gap: 6px;">
            Check Now
          </button>
          <button id="pingBtn" onclick="testNotification()" style="background: #f37023; color: #ffffff; font-weight: 700; font-size: 13px; padding: 10px 22px; border: none; border-radius: 9999px; cursor: pointer; box-shadow: 0 4px 14px rgba(243, 112, 35, 0.28); transition: all 0.2s ease; display: inline-flex; align-items: center; gap: 6px;">
            Test Push Alert
          </button>
        </div>
      </div>

      <!-- PNR Tracking Input Bar (IRCTC Input Style) -->
      <div style="background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 16px; padding: 16px 20px; margin-top: 22px;">
        <form id="addPnrForm" onsubmit="addPNR(event)" style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 14px;">
          <div style="display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 280px;">
            <label for="pnrInput" style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; color: #64748b;">
              Track New PNR Number
            </label>
            <div style="display: flex; align-items: center; gap: 10px;">
              <input type="text" id="pnrInput" placeholder="Enter 10-digit PNR Number..." required pattern="[0-9]{10}" maxlength="10"
                     style="background: #ffffff; border: 1.5px solid #cbd5e9; border-radius: 10px; padding: 10px 14px; font-size: 14px; font-family: monospace; font-weight: 600; color: #0f172a; flex: 1; outline: none; transition: border-color 0.2s;">
              <button type="submit" style="background: #0066b2; color: #ffffff; font-size: 13px; font-weight: 700; padding: 10px 20px; border: none; border-radius: 10px; cursor: pointer; white-space: nowrap; transition: background 0.2s; box-shadow: 0 2px 8px rgba(0, 102, 178, 0.25);">
                Start Tracking
              </button>
            </div>
          </div>

          <!-- Telemetry Badges -->
          <div style="display: flex; flex-wrap: wrap; gap: 12px; align-items: center;">
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 8px 14px; text-align: left;">
              <div style="font-size: 10px; color: #94a3b8; font-weight: 600; text-transform: uppercase;">Scheduler</div>
              <div style="font-size: 12px; font-weight: 700; color: #0f172a; font-family: monospace;">Every 5 Hours</div>
            </div>
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 8px 14px; text-align: left;">
              <div style="font-size: 10px; color: #94a3b8; font-weight: 600; text-transform: uppercase;">Channel</div>
              <div style="font-size: 12px; font-weight: 700; color: #15803d; font-family: monospace;">ntfy Webhook</div>
            </div>
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 8px 14px; text-align: left;">
              <div style="font-size: 10px; color: #94a3b8; font-weight: 600; text-transform: uppercase;">Spam Filter</div>
              <div style="font-size: 12px; font-weight: 700; color: #d26700; font-family: monospace;">100% Silent on No Change</div>
            </div>
          </div>
        </form>
      </div>

      <!-- Active Monitored Tickets Section -->
      <div style="margin-top: 28px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <h3 style="margin: 0; font-size: 16px; font-weight: 800; color: #0f172a; letter-spacing: -0.3px;">
              Active Monitored Tickets
            </h3>
            <span id="ticketCountBadge" style="background: #0066b2; color: #ffffff; font-size: 11px; font-weight: 800; padding: 2px 9px; border-radius: 9999px; font-family: monospace;">
              3
            </span>
          </div>
          <div style="font-size: 12px; color: #64748b; font-weight: 500;">
            Seat Movement &bull; Waiting List Progression &bull; Chart Status
          </div>
        </div>

        <div id="ticketsGrid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 18px;">
          <!-- Loaded dynamically via JavaScript -->
        </div>
      </div>

      <!-- Operational Event Log (Soft IRCTC Container) -->
      <div style="margin-top: 24px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 14px; padding: 14px 18px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <span style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; font-family: monospace;">
            Operational Event Log
          </span>
          <span style="font-size: 11px; color: #94a3b8; font-family: monospace;">
            Topic: shivanshu-irctc-4763331979
          </span>
        </div>
        <div id="eventLogBox" style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 14px; height: 90px; overflow-y: auto; font-family: monospace; font-size: 11px; color: #334155; line-height: 1.6;">
          <div style="color: #0066b2; font-weight: 600;">[Init] RailPulse Engine connected to IRCTC Portal.</div>
          <div style="color: #64748b;">[Status] Direct Open Rail Gateway operational without quota limitations.</div>
        </div>
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
      grid.innerHTML = '<div style="grid-column: 1/-1; padding: 40px; text-align: center; color: #64748b; font-family: monospace; font-size: 13px; background: #ffffff; border-radius: 14px; border: 1px dashed #cbd5e9;">No active tickets tracked. Enter a 10-digit PNR above!</div>';
      return;
    }

    pnrList.forEach(pnr => {
      const t = tickets[pnr];
      const passengers = t.passengers || [];

      const card = document.createElement("div");
      card.style.cssText = "background: #ffffff; border: 1.5px solid #e9ecef; border-radius: 16px; padding: 18px 20px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 4px 15px rgba(0,0,0,0.04); transition: transform 0.2s ease, box-shadow 0.2s ease;";

      const passengerRows = passengers.map(p => {
        const isCNF = p.current_status.includes("CNF");
        const isRAC = p.current_status.includes("RAC");

        let badgeStyle = "background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd;";
        if (isCNF) badgeStyle = "background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0;";
        else if (isRAC) badgeStyle = "background: #fef3c7; color: #b45309; border: 1px solid #fde68a;";

        return `
          <div style="display: flex; align-items: center; justify-content: space-between; font-size: 12px; padding: 8px 12px; border-radius: 10px; background: #f8f9fa; border: 1px solid #e9ecef; margin-bottom: 6px;">
            <span style="font-weight: 600; color: #334155;">Passenger ${p.passenger_number}</span>
            <div style="display: flex; align-items: center; gap: 8px; font-family: monospace;">
              <span style="color: #94a3b8; text-decoration: line-through; font-size: 11px;">${p.booking_status}</span>
              <span style="font-weight: 700; font-size: 11px; padding: 3px 10px; border-radius: 9999px; ${badgeStyle}">${p.current_status}</span>
            </div>
          </div>
        `;
      }).join("");

      card.innerHTML = `
        <div>
          <!-- PNR and Train Header -->
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
            <div>
              <span style="font-size: 12px; font-family: monospace; font-weight: 800; color: #0066b2; background: #f0f7ff; padding: 2px 8px; border-radius: 6px;">PNR ${t.pnr}</span>
              <h4 style="margin: 6px 0 0 0; font-size: 15px; font-weight: 800; color: #0f172a; letter-spacing: -0.2px;">${t.train_number} - ${t.train_name}</h4>
            </div>
            <span style="font-size: 11px; font-family: monospace; background: #f8f9fa; color: #475569; padding: 4px 10px; border-radius: 9999px; border: 1px solid #e9ecef; font-weight: 600;">${t.date_of_journey || "Scheduled"}</span>
          </div>

          <!-- Route Container -->
          <div style="display: flex; align-items: center; justify-content: space-between; font-size: 12px; font-family: monospace; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 12px; padding: 10px 14px; margin-bottom: 14px;">
            <span style="font-weight: 800; color: #0f172a;">${t.from_station || "ORIGIN"}</span>
            <span style="color: #0066b2; font-weight: 900; font-size: 14px;">&rarr;</span>
            <span style="font-weight: 800; color: #0f172a;">${t.to_station || "DESTINATION"}</span>
          </div>

          <!-- Passenger Movement -->
          <div style="margin-bottom: 12px;">
            <div style="font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; font-family: monospace; margin-bottom: 6px;">Passenger Seat Movement</div>
            ${passengerRows}
          </div>
        </div>

        <!-- Footer Strip -->
        <div style="border-top: 1px dashed #e2e8f0; padding-top: 10px; display: flex; justify-content: space-between; align-items: center; font-size: 11px; font-family: monospace; color: #64748b;">
          <span>Chart: <b style="color: #0f172a;">${t.chart_prepared ? 'Prepared' : 'Not Prepared'}</b></span>
          <span style="color: #15803d; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;">
            <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #22c55e;"></span>
            Live Monitored
          </span>
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
