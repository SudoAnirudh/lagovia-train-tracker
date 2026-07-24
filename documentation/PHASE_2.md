# Phase 2 Documentation — Core Domain Logic

> **Project**: Lagovia Train Tracker  
> **Phase**: Phase 2 — Core Domain Logic  
> **Status**: Completed  
> **Date**: July 24, 2026  

---

## 1. Overview & Objectives

Phase 2 implements the pure domain logic in `backend/app/domain.py`. This module handles time window filtering, ISO 8601 UTC formatting, and response shaping according to the exact API contract defined in **PRD §7**.

### Key Rules & Constraints Enforced
1. **Zero FastAPI Dependencies**: `domain.py` contains pure Python data models and functions. It imports zero web framework or FastAPI modules.
2. **UTC Server-Side Time Window**: All departures are filtered against `now_utc` for the 15-minute window (`[now_utc, now_utc + 15 minutes]`).
3. **Explicit Boundary Verification**: Includes tests verifying exact lower boundary (`now`), exact upper boundary (`now + 15m`), and exclusion of departures outside the window (`now - 1s`, `now + 15m + 1s`).
4. **Contract Fidelity**: Data structures match PRD §7 shape (`query`, `generated_at`, `window_minutes`, `stations` list with `station`, `status`, `error`, `departures`).

---

## 2. Core Functions & Data Models ([backend/app/domain.py](file:///home/anirudhs/Documents/Boredom/DPS_CHALLENGE/backend/app/domain.py))

```python
@dataclass(frozen=True)
class Departure:
    train_number: str
    destination: str
    scheduled_time: str   # ISO 8601 UTC string (e.g., "2026-07-24T10:22:00Z")
    delay_minutes: int
    cancelled: bool

@dataclass(frozen=True)
class StationResult:
    station: str
    status: str           # "ok" or "error"
    departures: List[Departure]
    error: Optional[str] = None
```

### Key Logic Functions

- `filter_window(raw_departures, now_utc, minutes=15) -> List[RawDeparture]`  
  Filters raw departures where `now_utc.timestamp() <= dep.time <= (now_utc.timestamp() + minutes * 60)`.
- `format_iso8601_utc(ts) -> str`  
  Converts Unix timestamp or `datetime` to ISO 8601 string formatted with UTC timezone indicator (`"YYYY-MM-DDTHH:MM:SSZ"`).
- `to_departure(raw_dep) -> Departure`  
  Converts `RawDeparture` to `Departure` domain model (`delay_minutes = raw_dep.delay // 60`).
- `to_station_result_ok(station_name, raw_departures, now_utc, minutes=15) -> StationResult`  
  Constructs a successful station result with filtered departures.
- `to_station_result_error(station_name, error_code) -> StationResult`  
  Constructs an isolated error station result (`status="error"`, `error=error_code`, `departures=[]`).
- `build_response_dict(query, station_results, now_utc, window_minutes=15) -> Dict[str, Any]`  
  Constructs the final dictionary matching the PRD §7 API response schema.

---

## 3. Unit Test Verification

The test suite in [backend/tests/test_domain.py](file:///home/anirudhs/Documents/Boredom/DPS_CHALLENGE/backend/tests/test_domain.py) exercises boundary filtering and contract shaping:

```bash
$ venv/bin/pytest backend/tests/test_domain.py -v

backend/tests/test_domain.py::test_format_iso8601_utc PASSED             [ 16%]
backend/tests/test_domain.py::test_filter_window_boundaries PASSED       [ 33%]
backend/tests/test_domain.py::test_to_departure_mapping PASSED           [ 50%]
backend/tests/test_domain.py::test_to_station_result_ok PASSED           [ 66%]
backend/tests/test_domain.py::test_to_station_result_error PASSED        [ 83%]
backend/tests/test_domain.py::test_build_response_dict_shape PASSED      [100%]

========================= 6 passed in 0.06s =========================
```

---

## 4. Key Design Decisions & Trade-Offs

1. **Integer Minute Delays**:
   Delays from iRail arrive in seconds. Floor division `delay // 60` converts seconds to integer minutes to match the contract, ensuring non-negative integers.
2. **ISO 8601 UTC Serialization**:
   All timestamps are converted to UTC and serialized as `YYYY-MM-DDTHH:MM:SSZ`. Local formatting is strictly deferred to the client rendering layer.
