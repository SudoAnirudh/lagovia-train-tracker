"""Core domain logic for Lagovia Train Tracker.

Pure functions for:
1. UTC-correct time window filtering (0 to 15 minutes from now).
2. Domain model definitions and response contract shaping.

Zero FastAPI dependencies — pure Python logic, fully unit-testable without network.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.irail_client import RawDeparture


@dataclass(frozen=True)
class Departure:
    """Domain representation of a train departure matching PRD contract."""
    train_number: str
    destination: str
    scheduled_time: str  # ISO 8601 UTC string, e.g. "2026-07-24T10:22:00Z"
    delay_minutes: int
    cancelled: bool


@dataclass(frozen=True)
class StationResult:
    """Per-station departure result or isolated error status."""
    station: str
    status: str  # "ok" or "error"
    departures: List[Departure]
    error: Optional[str] = None


@dataclass(frozen=True)
class DeparturesResponse:
    """Root response structure matching PRD §7 API contract."""
    query: str
    generated_at: str  # ISO 8601 UTC string
    window_minutes: int
    stations: List[StationResult]


def format_iso8601_utc(ts: int | float | datetime) -> str:
    """Format Unix timestamp or datetime as ISO 8601 UTC string ending in 'Z'."""
    if isinstance(ts, (int, float)):
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    elif isinstance(ts, datetime):
        if ts.tzinfo is None:
            dt = ts.replace(tzinfo=timezone.utc)
        else:
            dt = ts.astimezone(timezone.utc)
    else:
        raise ValueError(f"Unsupported time type: {type(ts)}")

    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def filter_window(
    raw_departures: List[RawDeparture],
    now_utc: datetime,
    minutes: int = 15,
) -> List[RawDeparture]:
    """Filter departures scheduled in the range [now_utc, now_utc + minutes].

    Computed strictly server-side in UTC.
    Inclusive lower boundary: now_utc
    Inclusive upper boundary: now_utc + minutes
    Exclusive: departures before now_utc or strictly after now_utc + minutes
    """
    if now_utc.tzinfo is None:
        now_dt = now_utc.replace(tzinfo=timezone.utc)
    else:
        now_dt = now_utc.astimezone(timezone.utc)

    start_ts = int(now_dt.timestamp())
    end_ts = start_ts + (minutes * 60)

    return [
        dep for dep in raw_departures
        if start_ts <= dep.time <= end_ts
    ]


def to_departure(raw_dep: RawDeparture) -> Departure:
    """Map raw iRail departure to documented Departure contract model."""
    train_num = raw_dep.vehicle_short_name if raw_dep.vehicle_short_name else raw_dep.vehicle
    delay_mins = max(0, raw_dep.delay // 60)

    return Departure(
        train_number=train_num,
        destination=raw_dep.station,
        scheduled_time=format_iso8601_utc(raw_dep.time),
        delay_minutes=delay_mins,
        cancelled=raw_dep.canceled,
    )


def to_station_result_ok(
    station_name: str,
    raw_departures: List[RawDeparture],
    now_utc: datetime,
    minutes: int = 15,
) -> StationResult:
    """Filter departures in window and map to successful StationResult."""
    filtered_raw = filter_window(raw_departures, now_utc=now_utc, minutes=minutes)
    deps = [to_departure(dep) for dep in filtered_raw]
    return StationResult(
        station=station_name,
        status="ok",
        error=None,
        departures=deps,
    )


def to_station_result_error(station_name: str, error_code: str) -> StationResult:
    """Map a station with an upstream failure to an isolated error StationResult."""
    return StationResult(
        station=station_name,
        status="error",
        error=error_code,
        departures=[],
    )


def build_response_dict(
    query: str,
    station_results: List[StationResult],
    now_utc: datetime,
    window_minutes: int = 15,
) -> Dict[str, Any]:
    """Construct dict matching PRD §7 JSON response shape."""
    gen_time_str = format_iso8601_utc(now_utc)

    formatted_stations = []
    for sr in station_results:
        item: Dict[str, Any] = {
            "station": sr.station,
            "status": sr.status,
        }
        if sr.status == "error" and sr.error:
            item["error"] = sr.error

        item["departures"] = [asdict(d) for d in sr.departures]
        formatted_stations.append(item)

    return {
        "query": query,
        "generated_at": gen_time_str,
        "window_minutes": window_minutes,
        "stations": formatted_stations,
    }
