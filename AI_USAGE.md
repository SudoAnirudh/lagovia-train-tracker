# AI Usage Log

This file tracks the usage of AI coding assistance during the implementation of the Lagovia Train Tracker project, as required by repo guidelines (`RULES.md` §17).

---

## Log Entry: 2026-07-24 - Phase 0 Implementation

### Prompt / Intent
"Implement Phase 0 of `IMPLEMENTATION_PLAN.md`: set up repo structure, FastAPI `/health` endpoint, React + Vite TS app, local CI-lite check tooling, and initial documentation."

### Kept
- Backend directory structure (`backend/app`, `backend/tests`).
- FastAPI `app/main.py` with `/health` returning `{"status": "ok"}`.
- Pytest test in `backend/tests/test_health.py`.
- Vite + React + TypeScript configuration in `frontend/`.
- Root `Makefile` for local `make check` running backend unit tests and frontend typechecks.
- Initial `README.md` and `AI_USAGE.md`.

### Rewritten / Adjusted
- Standardized FastAPI endpoint structure to follow Pydantic / ASGI testing best practices with `httpx.AsyncClient` and `ASGITransport`.

### Rejected
- Full CI workflow setup (GitHub Actions) for Phase 0 (rejected in favor of local `Makefile` / `make check` per PRD and implementation plan scope).

---

## Log Entry: 2026-07-24 - Phase 1 Implementation

### Prompt / Intent
"Implement Phase 1 of `IMPLEMENTATION_PLAN.md`: create pure `irail_client.py` module for iRail API fetch and parse, zero FastAPI dependencies, typed custom exceptions, in-process station caching, and unit tests using `respx` mock fixtures."

### Kept
- `backend/app/irail_client.py` with zero FastAPI imports.
- Typed dataclasses `Station` and `RawDeparture`.
- Typed custom exception hierarchy (`IRailError`, `IRailTimeoutError`, `IRailAPIError`, `IRailParseError`).
- In-process stations list caching (`fetch_stations`, `search_stations`, `clear_stations_cache`).
- Fixtures `stations.json`, `liveboard_brussels.json`, and `liveboard_empty.json` in `backend/tests/fixtures/`.
- 8 unit tests in `backend/tests/test_irail_client.py`.

### Rewritten / Adjusted
- Vehicle shortname parsing logic to fallback gracefully to stripping `BE.NMBS.` prefix if `vehicleinfo.shortname` is absent in raw liveboard item.

### Rejected
- Adding an external cache library (e.g. Redis/diskcache) — in-process list caching is simple, dependency-free, and sufficient.

---

## Log Entry: 2026-07-24 - Phase 2 Implementation

### Prompt / Intent
"Implement Phase 2 of `IMPLEMENTATION_PLAN.md`: pure domain logic in `domain.py`, zero FastAPI dependencies, UTC ISO 8601 formatting, strict 15-minute window boundary filtering, response contract shaping matching PRD §7, and comprehensive boundary unit tests."

### Kept
- Pure module `backend/app/domain.py` with zero FastAPI imports.
- Dataclasses `Departure`, `StationResult`, `DeparturesResponse`.
- Functions `format_iso8601_utc`, `filter_window`, `to_departure`, `to_station_result_ok`, `to_station_result_error`, `build_response_dict`.
- Strict boundary unit tests in `backend/tests/test_domain.py` testing exact boundaries: `now - 1s` (excluded), `now` (included), `now + 15m` (included), `now + 15m + 1s` (excluded).

### Rewritten / Adjusted
- Delay calculation converted delay in seconds to non-negative integer minutes using floor division `delay // 60` capped at 0 minimum.

### Rejected
- Client-side or naive timezone handling in datetime parsing — all timestamps are parsed and formatted explicitly as UTC with trailing `'Z'`.
