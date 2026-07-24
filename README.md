# Lagovia Train Tracker

A lightweight train departure tracker that answers: *"For any Belgian station matching what I typed, what's departing in the next 15 minutes, and how late is it?"*

Built on top of the iRail API (Belgium).

---

## Technical Stack

- **Backend**: Python 3.14 / 3.12+ + FastAPI + `httpx` + `rapidfuzz` + `pytest` + `respx`
- **Frontend**: React 18 + TypeScript + Vite + CSS Modules / Plain CSS

---

## Documentation Index

- [Phase 0 Showcase — Repo & Tooling Skeleton](documentation/PHASE_0.md)
- [Phase 1 Showcase — iRail Client (Isolated & Tested)](documentation/PHASE_1.md)
- [Phase 2 Showcase — Core Domain Logic](documentation/PHASE_2.md)
- [Phase 3 Showcase — `GET /departures` Endpoint](documentation/PHASE_3.md)
- [Phase 4 Showcase — Frontend UI Implementation](documentation/PHASE_4.md)
- [Phase 5 Showcase — Polish, Hardening & Live Smoke Testing](documentation/PHASE_5.md)
- [Phase 6 Showcase — Additive Fuzzy Search Fallback](documentation/PHASE_6.md)

---

## Quickstart

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Or backend/venv/bin/activate
pip install -r requirements.txt

# Run backend dev server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install

# Run frontend dev server
npm run dev
```

The frontend application will run at `http://localhost:3000` and automatically proxy API requests to `http://127.0.0.1:8000`.

---

## Running Verification & Tests

```bash
# Run backend pytest suite (22 unit & integration tests)
cd backend && venv/bin/pytest -v

# Run frontend typecheck & lint
cd frontend && npm run lint

# Run full local CI-lite suite (Backend tests + Frontend typecheck & production build)
make check
```

---

## Key Architecture & Design Trade-Offs

1. **Local CI-Lite Automation**: Used a root `Makefile` (`make check`) to provide instant local verification of backend tests, TypeScript types, and Vite production builds.
2. **In-Process Station List Caching**: Belgian train station names change very rarely. Station lists are cached in memory (`_stations_cache`) during process lifetime to avoid repeated full `/stations` GET queries to iRail.
3. **Additive Fuzzy Search (`rapidfuzz`)**: Substring matching remains the primary search path. If substring matching yields 0 results, rapidfuzz acts as an additive fallback to resolve typos (e.g. `"Antverpen"` → `"Antwerpen-Centraal"`).
4. **UTC Time Window Handling**: All departures are filtered server-side in UTC (`[now_utc, now_utc + 15 minutes]`). Trailing ISO 8601 `'Z'` strings are sent over the wire; local display formatting (`HH:mm`) is handled in the frontend UI.
5. **Per-Station Error Isolation**: Concurrent fan-out via `asyncio.gather(*tasks, return_exceptions=True)` ensures an upstream failure for one station (e.g. timeout or 500) renders as `status: "error"` for that station card while letting remaining stations return HTTP 200 OK.
6. **Explicit Submit Trigger over Keystroke Debouncing**: Search queries require clicking "Search Departures" (or pressing Enter), preventing unnecessary multi-character upstream requests while typing.
