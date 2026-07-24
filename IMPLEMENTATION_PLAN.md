# Implementation Plan — Lagovia Train Tracker

Phased so that at the end of every phase there is something that runs. No phase depends
on "just trust me, it'll come together" — each one is independently demoable.

## Phase 0 — Repo & tooling skeleton (target: <1 hr)
- `backend/`, `frontend/`, root `README.md`, `AGENTS.md`, `TECH_STACK.md`, `RULES.md`.
- Backend: FastAPI app boots, `GET /health` returns 200.
- Frontend: Vite + React + TS boots, shows a static placeholder page.
- CI-lite: a `make check` / `npm run check` that runs lint + type-check locally (no need
  for hosted CI unless time allows — note this trade-off in README).
- Commit. This is the "does the scaffolding work" checkpoint.

## Phase 1 — iRail client, isolated and tested
- A small `irail_client` module: `search_stations(substring) -> list[Station]`,
  `get_liveboard(station) -> list[RawDeparture]`.
- No FastAPI dependency in this module — it's pure fetch + parse, so it can be unit
  tested against recorded/mocked iRail responses without hitting the network.
- Handle: HTTP timeout, non-200, malformed JSON, empty results — each as a distinct,
  typed outcome, not a generic exception swallowed into `None`.
- Decide and document: station list source (iRail `/stations` endpoint) and whether it's
  cached in-process (station names don't change during a process lifetime — safe to
  cache with a long TTL or for process lifetime, documented as a deliberate trade-off).

## Phase 2 — Core domain logic
- Pure function: `filter_window(departures, now, minutes=15) -> list[Departure]`.
  Kept pure and separately tested — this is where the "next 15 minutes, UTC-correct"
  requirement lives, and it's the single easiest place to introduce an off-by-timezone
  bug, so it gets the most direct unit tests (boundary at exactly now, exactly +15,
  one second over).
- Pure function: `to_response_shape(station, departures) -> StationResult`, mapping
  iRail's fields to our documented contract (train number, destination, scheduled time,
  delay minutes, cancelled).
- Unit tests for both before wiring to HTTP — logic bugs are cheaper to find here than
  through the API layer.

## Phase 3 — `GET /departures` endpoint
- Validate `q`: `< 3` chars → 400 `query_too_short` (test this first, it's constraint #1
  in the brief for a reason — it's the easiest thing to forget under time pressure).
- Orchestrate: substring-match stations → fan out to `get_liveboard` per station
  (concurrently — `asyncio.gather` with `return_exceptions=True` so one slow/broken
  station doesn't block or fail the others) → filter window → shape response.
- Per-station error isolation: a failed upstream call produces `status: "error"` for
  that station, not a 500 for the whole request.
- Integration test with a mocked iRail (no live network dependency in the test suite —
  live iRail is for manual smoke testing, not CI).

## Phase 4 — Frontend
- Search input + submit (explicit trigger, not fire-on-every-keystroke — cheaper on
  iRail and clearer UX; documented as the chosen trade-off over debouncing).
- Loading state, empty state ("no stations match"), per-station error state (station
  shown, marked as temporarily unavailable, rest of the list still renders).
- Results grouped by station, each row showing train number, destination, scheduled
  time (localized for display), delay (0 shown as "on time", not hidden), cancelled
  flag visually distinct (not just a text label buried in a row).
- Client-side validation mirrors the backend's 3-char minimum so the error is instant,
  but the backend remains the source of truth (never trust client-only validation).

## Phase 5 — Polish & hardening
- README finalized: run instructions, decisions/trade-offs, known limitations.
- AI_USAGE.md written honestly, including what was rejected/rewritten.
- Manual smoke test against live iRail for a handful of real substrings ("Bru", "Gent",
  "Aac", a nonsense string, a 2-char string).
- Re-read the brief line by line against the running app — cheap insurance against
  scope drift.

## Phase 6 — Bonus: fuzzy search (only if 0–5 land solidly first)
- Layered on top of, not instead of, substring search: substring matches first, fuzzy
  matches (e.g. Levenshtein/rapidfuzz, or a simple normalized-distance heuristic) fill
  in if substring finds nothing. Kept as an additive, togglable layer so the core
  request path is legible without reading the fuzzy logic.
- "Antverpen" → "Antwerpen-Centraal" is the brief's own example — good acceptance test.

## Sequencing rationale
Domain logic (Phases 1–2) is built and tested before the HTTP layer (Phase 3) so that
the trickiest correctness requirement — the 15-minute UTC window — is nailed down in
isolation, not debugged through a browser. Frontend comes after the API is stable so it
consumes a contract that's already been exercised by tests, not a moving target.
