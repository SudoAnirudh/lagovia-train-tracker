from datetime import datetime, timezone
import pytest

from app.domain import (
    Departure,
    StationResult,
    build_response_dict,
    filter_window,
    format_iso8601_utc,
    to_departure,
    to_station_result_error,
    to_station_result_ok,
)
from app.irail_client import RawDeparture


def test_format_iso8601_utc():
    """Test timestamp formatting to ISO 8601 UTC string ending in 'Z'."""
    ts = 1784887200  # 2026-07-24T10:00:00Z
    assert format_iso8601_utc(ts) == "2026-07-24T10:00:00Z"

    dt_aware = datetime(2026, 7, 24, 10, 15, 30, tzinfo=timezone.utc)
    assert format_iso8601_utc(dt_aware) == "2026-07-24T10:15:30Z"


def test_filter_window_boundaries():
    """Test strict UTC 15-minute window boundaries (rule #8 & constraint #3).

    Boundaries tested:
    - now - 1s (10:00:00 - 1s = 09:59:59Z) -> EXCLUDED (past)
    - exactly now (10:00:00Z)             -> INCLUDED (lower boundary)
    - in window (10:07:30Z)               -> INCLUDED
    - exactly now + 15m (10:15:00Z)       -> INCLUDED (upper boundary)
    - now + 15m + 1s (10:15:01Z)          -> EXCLUDED (out of window)
    - now + 30m (10:30:00Z)               -> EXCLUDED
    """
    now_utc = datetime(2026, 7, 24, 10, 0, 0, tzinfo=timezone.utc)
    base_ts = int(now_utc.timestamp())

    dep_past = RawDeparture("Ostend", base_ts - 1, 0, False, "BE.NMBS.IC1", "IC1")
    dep_now = RawDeparture("Ostend", base_ts, 0, False, "BE.NMBS.IC2", "IC2")
    dep_mid = RawDeparture("Gent", base_ts + 450, 120, False, "BE.NMBS.IC3", "IC3")
    dep_exact_15m = RawDeparture("Antwerp", base_ts + 900, 0, True, "BE.NMBS.IC4", "IC4")
    dep_over_1s = RawDeparture("Liege", base_ts + 901, 0, False, "BE.NMBS.IC5", "IC5")
    dep_future = RawDeparture("Namur", base_ts + 1800, 0, False, "BE.NMBS.IC6", "IC6")

    raw_list = [dep_past, dep_now, dep_mid, dep_exact_15m, dep_over_1s, dep_future]

    filtered = filter_window(raw_list, now_utc=now_utc, minutes=15)

    assert len(filtered) == 3
    vehicles = [d.vehicle_short_name for d in filtered]
    assert vehicles == ["IC2", "IC3", "IC4"]
    assert dep_past not in filtered
    assert dep_over_1s not in filtered
    assert dep_future not in filtered


def test_to_departure_mapping():
    """Test mapping RawDeparture to domain Departure contract."""
    raw = RawDeparture(
        station="Ostend",
        time=1784887320,  # 2026-07-24T10:02:00Z
        delay=240,        # 240 seconds = 4 minutes
        canceled=False,
        vehicle="BE.NMBS.IC3033",
        vehicle_short_name="IC3033",
    )

    dep = to_departure(raw)

    assert dep.train_number == "IC3033"
    assert dep.destination == "Ostend"
    assert dep.scheduled_time == "2026-07-24T10:02:00Z"
    assert dep.delay_minutes == 4
    assert dep.cancelled is False


def test_to_station_result_ok():
    """Test successful station result filtering and mapping."""
    now_utc = datetime(2026, 7, 24, 10, 0, 0, tzinfo=timezone.utc)
    base_ts = int(now_utc.timestamp())

    raw_list = [
        RawDeparture("Ostend", base_ts + 300, 180, False, "BE.NMBS.IC1", "IC1"),
        RawDeparture("Gent", base_ts + 1000, 0, False, "BE.NMBS.IC2", "IC2"),  # > 15m
    ]

    result = to_station_result_ok("Brussels-Central", raw_list, now_utc=now_utc)

    assert result.station == "Brussels-Central"
    assert result.status == "ok"
    assert result.error is None
    assert len(result.departures) == 1
    assert result.departures[0].train_number == "IC1"
    assert result.departures[0].delay_minutes == 3


def test_to_station_result_error():
    """Test mapping an upstream failure to an isolated error station result."""
    result = to_station_result_error("Bruges", "upstream_timeout")

    assert result.station == "Bruges"
    assert result.status == "error"
    assert result.error == "upstream_timeout"
    assert result.departures == []


def test_build_response_dict_shape():
    """Test constructing JSON dict matching PRD §7 API contract."""
    now_utc = datetime(2026, 7, 24, 10, 15, 0, tzinfo=timezone.utc)

    ok_station = StationResult(
        station="Brussels-Central",
        status="ok",
        error=None,
        departures=[
            Departure("IC3033", "Ostend", "2026-07-24T10:22:00Z", 4, False)
        ],
    )
    err_station = StationResult(
        station="Bruges",
        status="error",
        error="upstream_timeout",
        departures=[],
    )

    response_dict = build_response_dict("Bru", [ok_station, err_station], now_utc=now_utc)

    assert response_dict == {
        "query": "Bru",
        "generated_at": "2026-07-24T10:15:00Z",
        "window_minutes": 15,
        "stations": [
            {
                "station": "Brussels-Central",
                "status": "ok",
                "departures": [
                    {
                        "train_number": "IC3033",
                        "destination": "Ostend",
                        "scheduled_time": "2026-07-24T10:22:00Z",
                        "delay_minutes": 4,
                        "cancelled": False,
                    }
                ],
            },
            {
                "station": "Bruges",
                "status": "error",
                "error": "upstream_timeout",
                "departures": [],
            },
        ],
    }
