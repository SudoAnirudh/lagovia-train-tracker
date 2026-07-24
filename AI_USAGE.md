# AI Usage Report

This document records the usage of AI coding assistance during the implementation of the **Lagovia Train Tracker** project, as required by repository guidelines (`RULES.md` §17).

---

## 1. Overview & AI Tools Used

| Tool / Model | Primary Usage Area | Scope of Execution |
|--------------|--------------------|--------------------|
| **Google Antigravity AI Agentic IDE** (Gemini 2.5 Pro) | End-to-End Implementation | Code scaffolding, TDD unit/integration tests, UTC boundary logic, live iRail API smoke testing, glassmorphic UI design, and phase documentation. |

---

## 2. Conversation Transcripts & Representative Prompts

- **Local Session Logs**: Complete untruncated conversation transcripts are saved locally in JSON Lines format:
  `brain/65779b61-61f1-4335-a751-72e9e001c349/.system_generated/logs/transcript.jsonl`
- **Conversation ID**: `65779b61-61f1-4335-a751-72e9e001c349`

### Representative Prompt Sequence
1. **Phase 0**: *"Set up project skeleton: FastAPI backend with `/health` endpoint, Vite React TS app, root `Makefile` for `make check`."*
2. **Phase 1**: *"Implement `irail_client.py` with zero FastAPI imports, custom typed exceptions, station list caching, and `respx` unit tests."*
3. **Phase 2**: *"Implement pure domain logic in `domain.py` with zero FastAPI imports, strict 15-minute UTC window boundary filtering, and boundary tests."*
4. **Phase 3**: *"Implement `GET /departures?q=<query>` in `main.py`, 400 `query_too_short` validation, `asyncio.gather(*tasks, return_exceptions=True)` fan-out, per-station error isolation."*
5. **Phase 4**: *"Implement React 18 + TS UI dashboard with 3-char instant validation, loading/empty/error states, and status badges ('On time', '+X min', 'CANCELLED')."*
6. **Phase 5**: *"Polish & hardening: execute live iRail API smoke tests, configure `follow_redirects=True` for HTTP 303 redirects, finalize documentation."*
7. **Phase 6**: *"Additive fuzzy search (`rapidfuzz`): keep substring path primary, trigger fuzzy matching only on 0 substring matches (e.g. 'Antverpen' → 'Antwerpen-Centraal')."*

---

## 3. Decision Matrix: Accepted, Rewritten & Rejected

| Phase | Accepted As-Is | Rewritten / Adjusted | Rejected |
|-------|----------------|----------------------|----------|
| **Phase 0** | Directory structure, FastAPI `/health` route, Vite TS config, `Makefile` | Standardized ASGI async test harness with `httpx.AsyncClient` | GitHub Actions CI (rejected in favor of local `make check`) |
| **Phase 1** | Decoupled `irail_client.py`, custom exceptions, station caching | Vehicle shortname parsing fallback when `vehicleinfo` is absent | Redis/diskcache external library (in-process cache is sufficient) |
| **Phase 2** | `domain.py` data models, 15-min UTC window filter | Delay calculation converted seconds to integer minutes via floor division `delay // 60` | Client-side/local timezone parsing (all timestamps explicitly UTC `'Z'`) |
| **Phase 3** | `GET /departures`, 400 `query_too_short`, `asyncio.gather(..., return_exceptions=True)` | Lifespan context manager for HTTP client with fallback inline client for tests | Returning empty 200 list on queries < 3 chars (PRD strictly mandates 400) |
| **Phase 4** | React components (`SearchForm`, `StationCard`, `DepartureRow`), status badges | Explicit submit button trigger rather than input keystroke debouncing | WebSocket / SSE interval polling (out of scope per PRD §4) |
| **Phase 5** | Live smoke testing against `api.irail.be`, documentation showcase | Added `follow_redirects=True` to handle iRail HTTP 303 redirects | Unverified manual commits without running full `make check` |
| **Phase 6** | `fuzzy_search_stations_in_list` function using `rapidfuzz` | Set WRatio similarity cutoff score to 70.0 | Modifying/replacing primary substring search path |

---

## 4. Detailed Phase Logs

### Log Entry: Phase 0 Implementation
- **Prompt**: Implement Phase 0 of `IMPLEMENTATION_PLAN.md`: set up repo structure, FastAPI `/health` endpoint, React + Vite TS app, local CI-lite check tooling, and initial documentation.
- **Kept**: FastAPI `app/main.py` `/health`, pytest `test_health.py`, Vite + React + TypeScript setup, root `Makefile`.
- **Rewritten**: Standardized FastAPI endpoint structure to follow Pydantic / ASGI testing best practices.
- **Rejected**: Full CI workflow setup in favor of local `make check`.

### Log Entry: Phase 1 Implementation
- **Prompt**: Implement Phase 1 of `IMPLEMENTATION_PLAN.md`: pure `irail_client.py` module for iRail API fetch and parse, zero FastAPI dependencies, typed custom exceptions, in-process station caching, and unit tests using `respx`.
- **Kept**: `backend/app/irail_client.py` zero FastAPI imports, custom exceptions (`IRailError`, `IRailTimeoutError`, etc.), station caching, unit test fixtures (`stations.json`, `liveboard_brussels.json`).
- **Rewritten**: Vehicle shortname parsing logic to fallback gracefully to stripping `BE.NMBS.` prefix if `vehicleinfo.shortname` is absent.
- **Rejected**: Adding external Redis / diskcache library.

### Log Entry: Phase 2 Implementation
- **Prompt**: Implement Phase 2 of `IMPLEMENTATION_PLAN.md`: pure domain logic in `domain.py`, zero FastAPI dependencies, UTC ISO 8601 formatting, strict 15-minute window boundary filtering, response contract shaping, and boundary tests.
- **Kept**: `backend/app/domain.py`, UTC ISO 8601 formatting, `filter_window()` logic, strict boundary tests (`now - 1s`, `now`, `now + 15m`, `now + 15m + 1s`).
- **Rewritten**: Delay calculation converted delay in seconds to non-negative integer minutes using floor division `delay // 60`.
- **Rejected**: Client-side timezone parsing.

### Log Entry: Phase 3 Implementation
- **Prompt**: Implement Phase 3 of `IMPLEMENTATION_PLAN.md`: `GET /departures` endpoint in `main.py`, 3-char minimum validation (400 `query_too_short`), async concurrent fan-out via `asyncio.gather(..., return_exceptions=True)`, per-station error isolation.
- **Kept**: Endpoint `GET /departures?q=<query>`, 3-char validation 400 error, `asyncio.gather(*tasks, return_exceptions=True)` fan-out, per-station error isolation.
- **Rewritten**: Shared HTTP client management in `main.py` using FastAPI lifespan context manager.
- **Rejected**: Returning an empty 200 list on queries shorter than 3 characters.

### Log Entry: Phase 4 Implementation
- **Prompt**: Implement Phase 4 of `IMPLEMENTATION_PLAN.md`: React + TypeScript frontend dashboard, search form with explicit submit button and instant 3-character validation, loading state, empty state, global error state, per-station error cards, and status badges.
- **Kept**: Typed API client in `frontend/src/api.ts`, `SearchForm`, `StationCard`, `DepartureRow`, status badges (`On time`, `+X min`, `CANCELLED`).
- **Rewritten**: Used explicit submit button trigger rather than keystroke debouncing.
- **Rejected**: WebSocket or interval polling for live updates.

### Log Entry: Phase 5 Implementation
- **Prompt**: Implement Phase 5 of `IMPLEMENTATION_PLAN.md`: polish & hardening, finalize README.md, update AI_USAGE.md, execute live iRail API smoke tests, and line-by-line PRD review.
- **Kept**: Finalized root `README.md`, executed live iRail API smoke tests (714 stations returned, live departures verified), showcase documentation `documentation/PHASE_5.md`.
- **Rewritten**: Added `follow_redirects=True` on `httpx.AsyncClient` calls after live smoke testing discovered iRail's use of HTTP 303 redirects.
- **Rejected**: Starting Phase 6 before Phase 0-5 completion approval.

### Log Entry: Phase 6 Implementation
- **Prompt**: Implement Phase 6 (fuzzy search): substring matching stays primary path; fuzzy matching (rapidfuzz) only fills in when substring search returns zero stations. Add 'Antverpen' -> 'Antwerpen-Centraal' test case. Update TECH_STACK.md.
- **Kept**: `rapidfuzz>=3.0.0` dependency, `fuzzy_search_stations_in_list` helper, updated `search_stations` fallback, unit and integration tests in `test_fuzzy_search.py`.
- **Rewritten**: Set similarity score threshold to 70.0 in rapidfuzz `WRatio` to prevent low-quality match noise.
- **Rejected**: Modifying or replacing the primary substring search path.
