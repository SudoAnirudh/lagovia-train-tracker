# Phase 1 Documentation — iRail Client (Isolated & Tested)

> **Project**: Lagovia Train Tracker  
> **Phase**: Phase 1 — iRail Client  
> **Status**: Completed  
> **Date**: July 24, 2026  

---

## 1. Overview & Objectives

Phase 1 implements the pure, isolated iRail API integration module in `backend/app/irail_client.py`. This module is responsible for fetching Belgian station lists, searching stations by substring, and querying station liveboards for upcoming departures.

### Key Rules & Constraints Enforced
1. **Zero FastAPI Dependencies**: The module only uses standard library features (`dataclasses`, `typing`, `logging`) and `httpx`. It can be imported and tested without FastAPI running.
2. **Offline Unit Testing**: Complete test coverage via `pytest` and `respx` mock HTTP endpoints using static JSON fixtures.
3. **Explicit Upstream Timeouts**: Every network call uses an explicit timeout (`DEFAULT_TIMEOUT = 5.0s`) to prevent unbounded waits on iRail.
4. **Typed Exception Model**: Custom exceptions (`IRailTimeoutError`, `IRailAPIError`, `IRailParseError`) categorize upstream errors explicitly.
5. **In-Process Caching**: Station lists are cached in-process to prevent redundant upstream GET calls to iRail's `/stations` endpoint.

---

## 2. Component Structure

### Data Models & Exceptions ([backend/app/irail_client.py](file:///home/anirudhs/Documents/Boredom/DPS_CHALLENGE/backend/app/irail_client.py))

```python
from dataclasses import dataclass
from typing import List, Optional
import httpx

class IRailError(Exception): pass
class IRailTimeoutError(IRailError): pass
class IRailAPIError(IRailError):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
class IRailParseError(IRailError): pass

@dataclass(frozen=True)
class Station:
    id: str
    name: str
    standard_name: str

@dataclass(frozen=True)
class RawDeparture:
    station: str
    time: int        # Scheduled departure time in Unix seconds
    delay: int       # Delay in seconds
    canceled: bool
    vehicle: str
    vehicle_short_name: str
```

### Core API Functions

- `fetch_stations(client, lang="en", force_refresh=False, timeout=5.0) -> List[Station]`
  Fetches all Belgian stations from `https://api.irail.be/stations/?format=json&lang=en` and caches them in `_stations_cache`.
- `search_stations(client, query, lang="en", timeout=5.0) -> List[Station]`
  Filters cached stations by case-insensitive substring match against `station.name` or `station.standard_name`.
- `get_liveboard(client, station_id_or_name, lang="en", timeout=5.0) -> List[RawDeparture]`
  Queries `https://api.irail.be/liveboard/?id={station_id}&format=json&lang=en` and parses raw departures into `RawDeparture` dataclasses.

---

## 3. Unit Test Verification

The test suite in [backend/tests/test_irail_client.py](file:///home/anirudhs/Documents/Boredom/DPS_CHALLENGE/backend/tests/test_irail_client.py) verifies all success, caching, and error edge cases without external network requests:

```bash
$ venv/bin/pytest backend/tests/test_irail_client.py -v

backend/tests/test_irail_client.py::test_fetch_stations_success PASSED
backend/tests/test_irail_client.py::test_fetch_stations_caching PASSED
backend/tests/test_irail_client.py::test_search_stations_substring_case_insensitive PASSED
backend/tests/test_irail_client.py::test_get_liveboard_success PASSED
backend/tests/test_irail_client.py::test_get_liveboard_empty_departures PASSED
backend/tests/test_irail_client.py::test_get_liveboard_timeout PASSED
backend/tests/test_irail_client.py::test_get_liveboard_http_500_error PASSED
backend/tests/test_irail_client.py::test_get_liveboard_malformed_json PASSED

======================== 8 passed in 0.23s ========================
```

---

## 4. Key Design Decisions & Trade-Offs

1. **In-Process Caching over Redis/Disk Cache**:
   Belgian train station names rarely change during a process lifetime. In-process global list caching (`_stations_cache`) provides instantaneous substring matching without needing a Redis or database setup.
2. **Vehicle Shortname Parsing Fallback**:
   iRail responses usually contain `vehicleinfo.shortname` (e.g. `"IC3033"`). If missing, `irail_client` automatically cleans raw strings like `"BE.NMBS.IC3033"` to maintain clean train identifier formatting.
3. **Strict Typed Exceptions**:
   Categorizing upstream failures into `IRailTimeoutError`, `IRailAPIError`, and `IRailParseError` allows downstream orchestration (Phase 3) to render per-station status errors accurately.
