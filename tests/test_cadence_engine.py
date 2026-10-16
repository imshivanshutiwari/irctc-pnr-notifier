import pytest
from datetime import datetime, date, timezone, timedelta
from cadence_engine import compute_pnr_cadence, parse_journey_date, PRIORITY_CADENCE_SECONDS, STANDARD_CADENCE_SECONDS, IST_TIMEZONE

def test_parse_journey_date():
    assert parse_journey_date("17-10-2026") == date(2026, 10, 17)
    assert parse_journey_date("2026-10-18") == date(2026, 10, 18)
    assert parse_journey_date("15/11/2026") == date(2026, 11, 15)
    assert parse_journey_date(None) is None
    assert parse_journey_date("invalid-date") is None

def test_user_three_pnr_scenarios():
    # Simulated current IST time: 16-10-2026
    simulated_now = datetime(2026, 10, 16, 19, 30, tzinfo=IST_TIMEZONE)

    # 1. PNR 4763331979: Journey tomorrow 17-10-2026 (days = 1 -> journey_day - 1)
    res_tomorrow = compute_pnr_cadence("17-10-2026", now_dt=simulated_now)
    assert res_tomorrow["cadence_seconds"] == 7200
    assert res_tomorrow["cadence_hours"] == 2.0
    assert res_tomorrow["priority_tier"] == "priority-2h"
    assert res_tomorrow["days_until_journey"] == 1
    assert res_tomorrow["is_near_journey"] is True

    # 2. PNR 7000126327: Journey day after tomorrow 18-10-2026 (days = 2 -> journey_day - 2)
    res_day_after = compute_pnr_cadence("18-10-2026", now_dt=simulated_now)
    assert res_day_after["cadence_seconds"] == 7200
    assert res_day_after["cadence_hours"] == 2.0
    assert res_day_after["priority_tier"] == "priority-2h"
    assert res_day_after["days_until_journey"] == 2
    assert res_day_after["is_near_journey"] is True

    # 3. PNR 6610459110: Journey 15-11-2026 (days = 30 -> > 2 days)
    res_far_away = compute_pnr_cadence("15-11-2026", now_dt=simulated_now)
    assert res_far_away["cadence_seconds"] == 18000
    assert res_far_away["cadence_hours"] == 5.0
    assert res_far_away["priority_tier"] == "standard-5h"
    assert res_far_away["days_until_journey"] == 30
    assert res_far_away["is_near_journey"] is False

def test_journey_today_is_priority():
    simulated_now = datetime(2026, 10, 17, 8, 0, tzinfo=IST_TIMEZONE)
    res_today = compute_pnr_cadence("17-10-2026", now_dt=simulated_now)
    assert res_today["cadence_seconds"] == 7200
    assert res_today["days_until_journey"] == 0
    assert res_today["is_near_journey"] is True

def test_past_journey_fallback():
    simulated_now = datetime(2026, 10, 20, 8, 0, tzinfo=IST_TIMEZONE)
    res_past = compute_pnr_cadence("17-10-2026", now_dt=simulated_now)
    # Passed journey days = -3, drops back to standard 5h
    assert res_past["cadence_seconds"] == 18000
    assert res_past["is_near_journey"] is False

def test_invalid_date_fallback():
    res = compute_pnr_cadence(None)
    assert res["cadence_seconds"] == 18000
    assert res["priority_tier"] == "standard-5h"

def test_destination_arrival_calculation():
    from cadence_engine import compute_destination_arrival, is_journey_completed

    # Overnight journey: Dep 17-10-2026 18:25 -> Arr 09:55 next day (18-10-2026 09:55)
    arr_dt = compute_destination_arrival("17-10-2026", "18:25", "09:55")
    assert arr_dt == datetime(2026, 10, 18, 9, 55, tzinfo=IST_TIMEZONE)

    # Same-day journey: Dep 18-10-2026 19:06 -> Arr 23:50 (18-10-2026 23:50)
    arr_same = compute_destination_arrival("18-10-2026", "19:06", "23:50")
    assert arr_same == datetime(2026, 10, 18, 23, 50, tzinfo=IST_TIMEZONE)

    # Before completion: 18-10-2026 09:00 (train has not arrived)
    before_dt = datetime(2026, 10, 18, 9, 0, tzinfo=IST_TIMEZONE)
    completed_before, _ = is_journey_completed("17-10-2026", "18:25", "09:55", buffer_minutes=60, now_dt=before_dt)
    assert completed_before is False

    # After arrival + buffer: 18-10-2026 11:30 (buffer 60 mins -> threshold 10:55)
    after_dt = datetime(2026, 10, 18, 11, 30, tzinfo=IST_TIMEZONE)
    completed_after, _ = is_journey_completed("17-10-2026", "18:25", "09:55", buffer_minutes=60, now_dt=after_dt)
    assert completed_after is True
