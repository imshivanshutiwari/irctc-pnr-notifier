import os
import re

SKELETON_HTML = r"E:\irctc-pnr-notifier\irctc_skeleton\index.html"
OUTPUT_HTML = r"E:\irctc-pnr-notifier\static\index.html"

with open(SKELETON_HTML, "r", encoding="utf-8", errors="ignore") as f:
    html = f.read()

# 1. Update base href and ensure stylesheet links
html = re.sub(r'<base\s+href="[^"]*">', '<base href="/">', html)
if '<link rel="stylesheet" href="/static/styles.css">' not in html:
    html = html.replace(
        '<link rel="stylesheet" href="styles.css">',
        '<link rel="stylesheet" href="/static/styles.css"><link rel="stylesheet" href="/styles.css">'
    )

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

# ---------------------------------------------------------------------------
# 3. REPLACE TOP BAR:
# Remove old Travel Advisory, A-/A/A+, static datetime, change language img.
# Add RailPulse Project details and live running clock (date + time with seconds).
# ---------------------------------------------------------------------------
OLD_ADVISORY = "Travel Advisory: Passengers are advised to check the latest train running status, platform information, and coach position before commencing their journey."
NEW_PROJECT_INFO = "RailPulse: Autonomous 24/7 IRCTC PNR Waiting List Watcher & Push Alert Engine &bull; Zero Spam &bull; Live Status Checks"

html = html.replace(OLD_ADVISORY, NEW_PROJECT_INFO)

# Replace the entire right side of the advisory bar:
# Static timestamp "14-10-2026 | 00:09:02", font buttons A-, A, A+, and the language image.
OLD_ADVISORY_RIGHT = html[html.find('class="advisory-right">'):html.find('</div><!----></div><', html.find('class="advisory-right">'))]

NEW_ADVISORY_RIGHT = """class="advisory-right" style="display: flex; align-items: center; gap: 14px;">
  <div style="display: inline-flex; align-items: center; gap: 8px; font-family: monospace; font-size: 13px; font-weight: 700; color: #1e293b; background: rgba(255, 255, 255, 0.9); padding: 5px 12px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); border: 1px solid #cbd5e1;">
    <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #16a34a; box-shadow: 0 0 6px #22c55e;"></span>
    <span id="liveClockDisplay">Loading live time...</span>
  </div>
"""

html = html.replace(OLD_ADVISORY_RIGHT, NEW_ADVISORY_RIGHT)

# ---------------------------------------------------------------------------
# GLOBAL CSS FIX BLOCK
# ---------------------------------------------------------------------------
GLOBAL_FIX_CSS = """
<style id="railpulse-global-fixes">
/* ===== ISSUE 1, 2, 3: Type Scale, Colour Palette & Corner Radii System ===== */
:root {
  --rp-fs-xs:   12px;
  --rp-fs-sm:   13px;
  --rp-fs-base: 14px;
  --rp-fs-md:   16px;
  --rp-fs-lg:   18px;
  --rp-fs-xl:   22px;
  --rp-fs-2xl:  32px;
  --rp-fs-hero: 48px;

  --rp-text-primary:   #0f172a;
  --rp-text-secondary: #374151;
  --rp-text-muted:     #6b7280;
  --rp-text-faint:     #9ca3af;
  --rp-text-link:      #0b57d0;
  --rp-text-success:   #15803d;
  --rp-text-warn:      #d26700;
  --rp-text-white:     #ffffff;

  --rp-brand-primary:  #0b57d0;
  --rp-brand-orange:   #f37023;
  --rp-border:         #dde3ee;
  --rp-border-light:   #eef0f5;
  --rp-surface:        #ffffff;
  --rp-surface-muted:  #f8fafc;

  --rp-radius-sm:   6px;
  --rp-radius-md:   10px;
  --rp-radius-lg:   16px;
  --rp-radius-xl:   20px;
  --rp-radius-full: 9999px;
}

/* ===== Button Styles Unification ===== */
button {
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  line-height: 1;
}
button:hover { opacity: 0.9; }
button:focus-visible { outline: 2px solid var(--rp-brand-primary); outline-offset: 2px; }

/* ===== Prevent text truncation on secondary actions and inputs ===== */
.action-title,
.select-placeholder,
.action-info span {
  overflow: visible !important;
  text-overflow: clip !important;
  white-space: normal !important;
  word-break: normal !important;
}

/* ===== Action buttons sizing and layout balance ===== */
.quick-actions {
  display: flex !important;
  flex-direction: column !important;
  justify-content: space-between !important;
  gap: 12px !important;
  min-width: 210px !important;
}
.quick-action-item {
  flex: 1 !important;
  display: flex !important;
}
.action-btn {
  width: 100% !important;
  min-height: 52px !important;
  padding: 10px 16px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 12px !important;
  border-radius: 12px !important;
  box-sizing: border-box !important;
}
.action-btn img {
  width: 32px !important;
  height: 32px !important;
  flex-shrink: 0 !important;
  order: -1 !important;
}
.action-info {
  display: flex !important;
  flex-direction: column !important;
  align-items: flex-start !important;
  text-align: left !important;
}

/* ===== Standardize icon placement to Left across all form fields ===== */
.journey-date-col .field-icon,
.date-picker-icon,
.cal-icon {
  order: -1 !important;
  margin-right: 8px !important;
}

/* ===== Full height vertical divider alignment ===== */
.card-divider {
  align-self: stretch !important;
  height: auto !important;
  min-height: 100% !important;
  margin: 0 16px !important;
  border-left: 1px solid var(--rp-border-light) !important;
}

/* ===== Search Trains CTA Prominence ===== */
.search-btn {
  min-width: 200px !important;
  padding: 16px 28px !important;
  font-size: 16px !important;
  font-weight: 800 !important;
  border-radius: 9999px !important;
  box-shadow: 0 4px 14px rgba(11, 87, 208, 0.35) !important;
  background-color: var(--rp-brand-primary) !important;
}

/* ===== From icon pin indicator distinction ===== */
.field-icon {
  filter: hue-rotate(180deg) saturate(1.4);
}
</style>
"""

# Inject global CSS into <head>
html = html.replace('</head>', GLOBAL_FIX_CSS + '</head>')

# ---------------------------------------------------------------------------
# RAILPULSE SECTION
# ---------------------------------------------------------------------------
RAILPULSE_SECTION = """
<section id="railpulse-monitor" style="background: linear-gradient(135deg, #eef2fb 0%, #f5f0ea 100%); padding: 40px 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <div style="max-width: 1200px; margin: 0 auto;">

    <!-- Hero headline -->
    <div style="margin-bottom: 28px;">
      <h2 style="margin: 0 0 4px 0; font-size: 38px; font-weight: 800; color: #0f172a; letter-spacing: -1px; line-height: 1.15;">
        Your Tickets, <span style="color: #f37023;">Monitored Live</span>
      </h2>
      <p style="margin: 0; font-size: 14px; color: #6b7280; font-weight: 500;">
        Autonomous 24/7 background watcher with instant push notifications on seat movement
      </p>
    </div>

    <!-- Main card: IRCTC search-card style -->
    <div style="background: #ffffff; border: 1px solid #dde3ee; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.07); overflow: hidden;">

      <!-- Row 1: Direct Input-to-Action Grouping -->
      <div style="display: flex; flex-wrap: wrap; align-items: stretch; border-bottom: 1px solid #eef0f5;">

        <!-- Primary Task Sub-region: Input + Direct Action -->
        <div style="flex: 3; display: flex; align-items: center; padding: 18px 24px; border-right: 1px solid #eef0f5; gap: 14px; min-width: 340px;">
          <div style="width: 36px; height: 36px; border-radius: 9999px; background: #eff6ff; border: 1px solid #bfdbfe; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0b57d0" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
              <circle cx="12" cy="10" r="3"/>
            </svg>
          </div>
          <div style="flex: 1; min-width: 0;">
            <div style="font-size: 12px; color: #475569; font-weight: 700; margin-bottom: 3px; text-transform: uppercase; letter-spacing: 0.5px;">PNR Number</div>
            <form id="addPnrForm" onsubmit="addPNR(event)" style="display: flex; align-items: center; gap: 10px;">
              <input type="text" id="pnrInput" placeholder="Enter 10-digit PNR..." required pattern="[0-9]{10}" maxlength="10"
                     aria-label="PNR Number"
                     style="border: none; outline: none; font-size: 15px; font-weight: 700; color: #0f172a; font-family: monospace; background: transparent; flex: 1; padding: 0;">
              <button type="submit"
                      style="background: #0b57d0; color: #ffffff; font-size: 13px; font-weight: 700; padding: 10px 22px; border: none; border-radius: 9999px; cursor: pointer; white-space: nowrap; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 2px 8px rgba(11,87,208,0.3);">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                Track PNR
              </button>
            </form>
          </div>
        </div>

        <!-- Secondary Config Sub-region: Unified Settings Block -->
        <div style="flex: 2; display: flex; align-items: center; justify-content: space-around; padding: 14px 20px; background: #fafbfd; gap: 16px; min-width: 280px;">
          <div>
            <div style="font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.4px;">Scheduler</div>
            <div style="font-size: 13px; font-weight: 700; color: #0f172a; font-family: monospace;">Every 5 Hours</div>
          </div>
          <div style="width: 1px; height: 26px; background: #e2e8f0;"></div>
          <div>
            <div style="font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.4px;">Alert Channel</div>
            <div style="font-size: 13px; font-weight: 700; color: #15803d;">ntfy Webhook</div>
          </div>
          <div style="width: 1px; height: 26px; background: #e2e8f0;"></div>
          <div>
            <div style="font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.4px;">Spam Filter</div>
            <div style="font-size: 13px; font-weight: 700; color: #d26700;">Silent on no change</div>
          </div>
        </div>

      </div>

      <!-- Row 2: Secondary Quick Actions Row -->
      <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 24px; background: #ffffff;">
        <div style="display: inline-flex; align-items: center; gap: 8px;">
          <span style="font-size: 12px; font-weight: 700; color: #1e293b; background: #f1f5f9; border: 1px solid #e2e8f0; padding: 4px 10px; border-radius: 6px; text-transform: uppercase; letter-spacing: 0.5px;">
            Quick Controls
          </span>
          <span style="font-size: 12px; color: #64748b;">Instant background triggers</span>
        </div>
        
        <div style="display: flex; align-items: center; gap: 10px;">
          <button id="refreshBtn" onclick="triggerCheck()"
                  style="background: #ffffff; color: #0b57d0; font-size: 13px; font-weight: 700; padding: 9px 18px; border: 1.5px solid #0b57d0; border-radius: 9999px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px;">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.95"/>
            </svg>
            Check Now
          </button>
          <button id="pingBtn" onclick="testNotification()"
                  style="background: #ffffff; color: #0b57d0; font-size: 13px; font-weight: 700; padding: 9px 18px; border: 1.5px solid #0b57d0; border-radius: 9999px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px;">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            Test Alert
          </button>
        </div>
      </div>
    </div>

    <!-- Tickets section header with Status Legend -->
    <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 36px; margin-bottom: 18px; flex-wrap: wrap; gap: 12px;">
      <div style="display: flex; align-items: center; gap: 10px;">
        <h3 style="margin: 0; font-size: 18px; font-weight: 800; color: #0f172a; letter-spacing: -0.3px;">Active Monitored Tickets</h3>
        <span id="ticketCountBadge" style="background: #0b57d0; color: #ffffff; font-size: 12px; font-weight: 700; padding: 2px 10px; border-radius: 9999px; font-family: monospace;">3</span>
      </div>
      <div style="display: flex; align-items: center; gap: 14px; font-size: 12px; color: #475569;" role="note" aria-label="Status Legend">
        <span style="display: inline-flex; align-items: center; gap: 5px;">
          <span style="width: 8px; height: 8px; border-radius: 50%; background: #0284c7; display: inline-block;"></span> Waiting List
        </span>
        <span style="display: inline-flex; align-items: center; gap: 5px;">
          <span style="width: 8px; height: 8px; border-radius: 50%; background: #d97706; display: inline-block;"></span> RAC
        </span>
        <span style="display: inline-flex; align-items: center; gap: 5px;">
          <span style="width: 8px; height: 8px; border-radius: 50%; background: #16a34a; display: inline-block;"></span> Confirmed
        </span>
        <span style="display: inline-flex; align-items: center; gap: 5px;">
          <span style="width: 8px; height: 8px; border-radius: 50%; background: #64748b; display: inline-block;"></span> Chart Prepared
        </span>
      </div>
    </div>

    <!-- Ticket Cards Grid with stretch alignment -->
    <div id="ticketsGrid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 16px; align-items: stretch;">
    </div>

    <!-- Event Log (Behind interactive details toggle) -->
    <details style="background: #ffffff; border: 1px solid #dde3ee; border-radius: 14px; padding: 12px 18px; margin-top: 24px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
      <summary style="cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-size: 13px; font-weight: 700; color: #334155; user-select: none;">
        <span style="display: inline-flex; align-items: center; gap: 8px;">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2">
            <polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>
          </svg>
          Technical Operation Log
        </span>
        <span style="font-size: 12px; font-weight: 500; color: #0b57d0;">View Details &darr;</span>
      </summary>
      <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #eef0f5;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <span style="font-size: 11px; color: #94a3b8; font-family: monospace;">Topic: shivanshu-irctc-4763331979</span>
        </div>
        <div id="eventLogBox" style="font-family: monospace; font-size: 12px; color: #374151; line-height: 1.7; height: 90px; overflow-y: auto; background: #f8fafc; border-radius: 8px; padding: 10px;" role="log" aria-live="polite">
          <div style="color: #0b57d0; font-weight: 600;">[Init] RailPulse Engine connected to IRCTC Portal.</div>
          <div style="color: #6b7280;">[Status] Direct Open Rail Gateway operational without quota limitations.</div>
        </div>
      </div>
    </details>

  </div>
</section>
"""

# Inject RailPulse section right after </app-jp-input>
if "</app-jp-input>" in html:
    html = html.replace("</app-jp-input>", "</app-jp-input>" + RAILPULSE_SECTION)
else:
    html = html.replace("<app-footer", RAILPULSE_SECTION + "<app-footer")

# ---------------------------------------------------------------------------
# CLIENT SCRIPT WITH LIVE SECONDS TICKING CLOCK
# ---------------------------------------------------------------------------
CLIENT_SCRIPT = """
<script>
  // Live Clock ticking date and time till seconds
  function updateLiveClock() {
    var el = document.getElementById("liveClockDisplay");
    if (!el) return;
    var now = new Date();
    var day = String(now.getDate()).padStart(2, "0");
    var monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    var month = monthNames[now.getMonth()];
    var year = now.getFullYear();
    var hours = String(now.getHours()).padStart(2, "0");
    var minutes = String(now.getMinutes()).padStart(2, "0");
    var seconds = String(now.getSeconds()).padStart(2, "0");
    el.textContent = day + " " + month + " " + year + " | " + hours + ":" + minutes + ":" + seconds;
  }
  setInterval(updateLiveClock, 1000);
  updateLiveClock();

  function logEvent(msg) {
    var box = document.getElementById("eventLogBox");
    if (!box) return;
    var el = document.createElement("div");
    el.textContent = "[" + new Date().toLocaleTimeString() + "] " + msg;
    box.appendChild(el);
    box.scrollTop = box.scrollHeight;
  }

  async function loadTickets() {
    try {
      var res = await fetch("/api/tickets");
      var data = await res.json();
      renderTickets(data);
    } catch (e) {
      logEvent("Failed to load tickets: " + e);
    }
  }

  function renderTickets(tickets) {
    var grid = document.getElementById("ticketsGrid");
    if (!grid) return;
    grid.innerHTML = "";
    var pnrList = Object.keys(tickets);
    var badge = document.getElementById("ticketCountBadge");
    if (badge) badge.textContent = pnrList.length;

    if (pnrList.length === 0) {
      grid.innerHTML = '<div style="grid-column:1/-1;padding:48px;text-align:center;color:#6b7280;background:#ffffff;border:1px solid #dde3ee;border-radius:16px;font-size:14px;">No tickets tracked yet. Enter a 10-digit PNR above to start.</div>';
      return;
    }

    pnrList.forEach(function(pnr) {
      var t = tickets[pnr];
      var passengers = t.passengers || [];

      var card = document.createElement("div");
      card.style.cssText = [
        "background:#ffffff",
        "border:1px solid #dde3ee",
        "border-radius:16px",
        "padding:20px 22px",
        "box-shadow:0 2px 8px rgba(0,0,0,0.05)",
        "display:flex",
        "flex-direction:column"
      ].join(";");

      var passengerRows = passengers.map(function(p) {
        var isCNF = p.current_status.includes("CNF");
        var isRAC = p.current_status.includes("RAC");
        var badgeStyle;
        if (isCNF) {
          badgeStyle = "color:#15803d;background:#dcfce7;border:1px solid #bbf7d0;";
        } else if (isRAC) {
          badgeStyle = "color:#b45309;background:#fef3c7;border:1px solid #fde68a;";
        } else {
          badgeStyle = "color:#0369a1;background:#e0f2fe;border:1px solid #bae6fd;";
        }
        return '<div style="display:flex;align-items:center;justify-content:space-between;padding:9px 12px;border-radius:10px;background:#f8fafc;border:1px solid #eef0f5;margin-bottom:6px;">'
          + '<span style="font-size:13px;font-weight:600;color:#374151;">Passenger ' + p.passenger_number + '</span>'
          + '<div style="display:flex;align-items:center;gap:8px;font-family:monospace;">'
          + '<span style="font-size:12px;color:#9ca3af;text-decoration:line-through;">' + p.booking_status + '</span>'
          + '<span style="font-size:12px;font-weight:700;padding:3px 10px;border-radius:9999px;' + badgeStyle + '">' + p.current_status + '</span>'
          + '</div></div>';
      }).join("");

      card.innerHTML = ''
        + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
          + '<div style="display:flex;flex-direction:column;gap:4px;">'
            + '<div style="display:inline-flex;align-items:center;font-size:12px;font-family:monospace;font-weight:700;color:#0b57d0;background:#eff6ff;padding:3px 8px;border-radius:6px;align-self:flex-start;">PNR ' + t.pnr + '</div>'
            + '<div style="font-size:16px;font-weight:800;color:#0f172a;letter-spacing:-0.3px;">' + t.train_number + ' - ' + t.train_name + '</div>'
          + '</div>'
          + '<span style="font-size:12px;font-family:monospace;background:#f1f5f9;color:#374151;padding:4px 10px;border-radius:9999px;border:1px solid #dde3ee;font-weight:600;white-space:nowrap;align-self:flex-start;">' + (t.date_of_journey || "Scheduled") + '</span>'
        + '</div>'
        + '<div style="display:flex;align-items:center;justify-content:space-between;background:#f8fafc;border:1px solid #eef0f5;border-radius:10px;padding:10px 16px;margin-bottom:16px;font-family:monospace;font-size:13px;">'
          + '<span style="font-weight:800;color:#0f172a;">' + (t.from_station || "ORIGIN") + '</span>'
          + '<span style="color:#0b57d0;font-size:18px;font-weight:900;">&rarr;</span>'
          + '<span style="font-weight:800;color:#0f172a;">' + (t.to_station || "DESTINATION") + '</span>'
        + '</div>'
        + '<div style="font-size:12px;font-weight:700;color:#0b57d0;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:8px;">Passenger Seat Movement</div>'
        + '<div style="flex:1;">' + passengerRows + '</div>'
        + '<div style="border-top:1px solid #eef0f5;padding-top:10px;margin-top:auto;display:flex;justify-content:space-between;align-items:center;font-size:12px;color:#6b7280;font-family:monospace;">'
          + '<span>Chart: <b style="color:#0f172a;">' + (t.chart_prepared ? 'Prepared' : 'Not Prepared') + '</b></span>'
          + '<span style="color:#15803d;font-weight:700;display:inline-flex;align-items:center;gap:5px;">'
            + '<span style="width:7px;height:7px;border-radius:50%;background:#22c55e;display:inline-block;"></span>Live Monitored'
          + '</span>'
        + '</div>';

      grid.appendChild(card);
    });
  }

  async function triggerCheck() {
    var btn = document.getElementById("refreshBtn");
    if (btn) btn.disabled = true;
    logEvent("Checking active PNR status via live Railway Gateway...");
    try {
      var res = await fetch("/api/check-now", { method: "POST" });
      var d = await res.json();
      logEvent(d.message);
      loadTickets();
    } catch (e) {
      logEvent("Check error: " + e);
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  async function testNotification() {
    var btn = document.getElementById("pingBtn");
    if (btn) btn.disabled = true;
    logEvent("Dispatching test alert to configured device...");
    try {
      var res = await fetch("/api/test-notify", { method: "POST" });
      logEvent("Notification alert dispatched successfully.");
    } catch (e) {
      logEvent("Notification error: " + e);
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  async function addPNR(e) {
    e.preventDefault();
    var pnr = document.getElementById("pnrInput").value.trim();
    if (!pnr) return;
    logEvent("Querying PNR " + pnr + "...");
    try {
      var res = await fetch("/api/add-pnr?pnr=" + pnr, { method: "POST" });
      var d = await res.json();
      logEvent(d.message);
      document.getElementById("pnrInput").value = "";
      loadTickets();
    } catch (e) {
      logEvent("Failed to register PNR: " + e);
    }
  }

  window.addEventListener("DOMContentLoaded", loadTickets);
</script>
"""

html = html.replace("</body>", CLIENT_SCRIPT + "</body>")

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("Generated", OUTPUT_HTML, "length:", len(html))
