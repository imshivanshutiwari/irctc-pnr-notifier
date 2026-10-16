"""
cadence_engine.py - Autonomous Per-PNR Adaptive Polling Cadence Engine for RailPulse

Rules:
1. When journey date is within 2 days (journey_day, journey_day - 1, journey_day - 2),
   cadence is 2 hours (7200 seconds) - "priority-2h".
2. When journey date is > 2 days away,
   cadence is 5 hours (18000 seconds) - "standard-5h".
3. When chart is already prepared (chart_prepared == True) or journey has passed (< 0 days),
   cadence remains relaxed or standard.
4. Calculations are performed relative to Indian Standard Time (IST, UTC+5:30).
"""

from datetime import datetime, date, timezone, timedelta
from typing import Dict, Any, Optional, Tuple

PRIORITY_CADENCE_SECONDS = 2 * 3600    # 7200 seconds (2 hours)
STANDARD_CADENCE_SECONDS = 5 * 3600    # 18000 seconds (5 hours)

IST_TIMEZONE = timezone(timedelta(hours=5, minutes=30))

def parse_journey_date(doj_str: Optional[str]) -> Optional[date]:
    """Parse journey date from string in formats like 'DD-MM-YYYY' or 'YYYY-MM-DD'."""
    if not doj_str or not isinstance(doj_str, str):
        return None
    cleaned = doj_str.strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None

def compute_pnr_cadence(
    date_of_journey: Optional[str],
    chart_prepared: bool = False,
    now_dt: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Computes polling interval and priority metadata for a specific PNR.
    Returns:
        {
            "cadence_seconds": int,
            "cadence_hours": float,
            "priority_tier": "priority-2h" | "standard-5h",
            "tier_label": str,
            "days_until_journey": Optional[int],
            "is_near_journey": bool
        }
    """
    if now_dt is None:
        now_dt = datetime.now(IST_TIMEZONE)
    elif now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=IST_TIMEZONE)
    else:
        now_dt = now_dt.astimezone(IST_TIMEZONE)

    today_ist = now_dt.date()
    j_date = parse_journey_date(date_of_journey)

    if not j_date:
        return {
            "cadence_seconds": STANDARD_CADENCE_SECONDS,
            "cadence_hours": 5.0,
            "priority_tier": "standard-5h",
            "tier_label": "Standard Cadence (5h)",
            "days_until_journey": None,
            "is_near_journey": False,
        }

    days_until_journey = (j_date - today_ist).days

    # Rule: journey_day - 1, journey_day - 2, and journey_day itself (0 <= days <= 2)
    # If journey has not departed yet and is within 2 calendar days:
    if 0 <= days_until_journey <= 2:
        return {
            "cadence_seconds": PRIORITY_CADENCE_SECONDS,
            "cadence_hours": 2.0,
            "priority_tier": "priority-2h",
            "tier_label": "⚡ Priority Journey Cadence (2h)",
            "days_until_journey": days_until_journey,
            "is_near_journey": True,
        }
    else:
        return {
            "cadence_seconds": STANDARD_CADENCE_SECONDS,
            "cadence_hours": 5.0,
            "priority_tier": "standard-5h",
            "tier_label": "Standard Fleet Cadence (5h)",
            "days_until_journey": days_until_journey,
            "is_near_journey": False,
        }
