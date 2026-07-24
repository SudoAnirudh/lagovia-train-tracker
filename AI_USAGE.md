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

---

## Log Entry: 2026-07-24 - Phase 3 Implementation

### Prompt / Intent
"Implement Phase 3 of `IMPLEMENTATION_PLAN.md`: `GET /departures` endpoint in `main.py`, 3-char minimum validation (400 `query_too_short`), async concurrent fan-out via `asyncio.gather(..., return_exceptions=True)`, per-station error isolation, and integration tests with mocked iRail."

### Kept
- Endpoint `GET /departures?q=<query>` in `backend/app/main.py`.
- Validation for `len(q) < 3` returning HTTP 400 with `{"error": "query_too_short", "message": "q must be at least 3 characters", "min_length": 3}`.
- Concurrent fan-out via `asyncio.gather(*tasks, return_exceptions=True)` across matched stations.
- Per-station error isolation mapping `IRailTimeoutError` to `status: "error"` (`error: "upstream_timeout"`) and other errors to `error: "upstream_error"` while letting remaining stations succeed (HTTP 200).
- Integration test suite `backend/tests/test_departures_endpoint.py`.

### Rewritten / Adjusted
- Shared HTTP client management in `main.py` using FastAPI lifespan context manager with fallback inline client for test execution.

### Rejected
- Returning an empty 200 list on queries shorter than 3 characters — PRD §5 FR2 strictly mandates HTTP 400 `query_too_short`.

---

## Log Entry: 2026-07-24 - Phase 4 Implementation

### Prompt / Intent
"Implement Phase 4 of `IMPLEMENTATION_PLAN.md`: React + TypeScript frontend dashboard, search form with explicit submit button and instant 3-character validation, loading state, empty state, global error state, per-station error cards, and visually distinct delay/cancelled status badges."

### Kept
- Typed API client in `frontend/src/api.ts` handling `GET /departures` and structured 400 errors.
- `SearchForm` component with instant client-side 3-character query validation and explicit submit button.
- `StationCard` component rendering per-station results, empty states, and isolated error banners (`status: "error"`).
- `DepartureRow` component showing scheduled time in local time, green `"On time"` badge for `delay_minutes === 0`, amber `"+X min"` badge for delays, and bold red `"CANCELLED"` badge with strikethrough styling for cancelled trains.
- `App.tsx` main component handling loading, global error, empty result, and success states.
- Clean design system in `frontend/src/index.css`.

### Rewritten / Adjusted
- Used explicit submit button trigger rather than keystroke debouncing for clearer user feedback and lower iRail request load.

### Rejected
- WebSocket or interval polling for live updates — out of scope per PRD §4.

---

## Log Entry: 2026-07-24 - Phase 5 Implementation

### Prompt / Intent
"Implement Phase 5 of `IMPLEMENTATION_PLAN.md`: polish & hardening, finalize README.md with run instructions and trade-offs, update AI_USAGE.md across all phases, execute live iRail API smoke tests, and line-by-line PRD review."

### Kept
- Finalized root `README.md` and component `README.md` files.
- Executed live iRail API integration smoke tests against real Belgian station data (714 stations returned, live departures verified for Brugge).
- Configured `follow_redirects=True` in `irail_client.py` and `main.py` to seamlessly follow iRail HTTP 303 redirects.
- Complete documentation showcase `documentation/PHASE_5.md`.

### Rewritten / Adjusted
- Added `follow_redirects=True` on `httpx.AsyncClient` calls after live smoke testing discovered iRail's use of HTTP 303 redirects on station endpoints.

### Rejected
- Starting Phase 6 (fuzzy search) before Phase 0-5 completion approval per explicit user constraint.
