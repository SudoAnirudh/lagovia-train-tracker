# PRD — Lagovia Train Tracker

## 1. Problem & Goal

Lagovia's citizens want a fast way to answer one question: *"For any station whose name
matches what I typed, what's departing in the next 15 minutes, and how late is it?"*

We are building a thin, honest layer on top of the iRail API (Belgium) that answers this
question well — not a full journey planner, not a timetable browser. Scope discipline is
itself part of the deliverable: the brief is intentionally open-ended, and the strongest
signal we can send is knowing what *not* to build.

## 2. Users & Use Case

- Primary user: someone who knows roughly which station they care about ("Bru", "Aac",
  "Gent") and wants an at-a-glance delay overview, not a route planner.
- Secondary "user": an API consumer (script, another service) hitting `GET /departures`
  directly and expecting a stable, documented JSON contract.

## 3. In Scope

- `GET /departures?q=<substring>` — backend endpoint, case-insensitive substring match
  against iRail station names.
- A minimal React frontend: search box + results grouped by station.
- Departure window: only departures scheduled 0–15 minutes from request time (server
  clock, not client clock — see §6).
- Per-departure fields: station name, train number, destination, scheduled departure
  time, delay in minutes, cancelled flag.
- Input validation: queries `< 3` chars return a structured 4xx error, not a 200 with an
  empty list — the two mean different things and the API should say which.
- Graceful degradation when iRail is slow, down, or returns malformed data for one
  station but not others.

## 4. Explicitly Out of Scope (v1)

- Journey planning / multi-leg routing.
- Historical delay stats or trends.
- Auth, accounts, saved favourite stations.
- Push/poll live updates (frontend does on-demand search only, no websocket/interval
  polling in v1 — flagged as a natural v2 in the README).
- Fuzzy search — bonus only, built as a clearly separable layer on top of substring
  search so it can be judged independently and skipped without touching the core path.

## 5. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR1 | `GET /departures?q=<string>` returns JSON. |
| FR2 | `len(q) < 3` → HTTP 400 with a machine-readable error code (`query_too_short`), not a silent empty result. |
| FR3 | Station matching is substring, case-insensitive, applied to iRail's station list. |
| FR4 | For every matched station, fetch upcoming departures via iRail `liveboard`. |
| FR5 | Filter departures to `now ≤ scheduled_departure ≤ now + 15min`, computed server-side in UTC. |
| FR6 | Each returned departure includes: station name, train number, destination, scheduled time (ISO 8601), delay in minutes, `cancelled: boolean`. |
| FR7 | If a matched station's upstream call fails, that station is reported as errored *without* failing the whole response (partial success is a first-class outcome, not an edge case). |
| FR8 | No matching stations → HTTP 200 with an empty `stations` array, not a 404 (empty result set is a valid answer to a valid query). |
| FR9 | Frontend: search input, explicit trigger (submit/debounce — implementer's choice, documented), results grouped/labelled by station, delay and cancelled state visually distinct. |

## 6. Non-Functional Requirements & Decisions to Document

- **Time zone correctness**: iRail returns Unix timestamps; "next 15 minutes" must be
  computed against server time in UTC, independent of user locale. This is a common
  source of subtle bugs — call it out explicitly in code comments and tests.
- **Upstream is a dependency, not a foundation**: iRail is free/unauthenticated/best-effort.
  Timeouts, retries (or deliberate absence thereof), and error shapes must be designed
  as if it will occasionally misbehave, because it will.
- **Partial failure model**: a query spanning multiple stations should degrade per-station,
  not all-or-nothing.
- **Response shape stability**: document the JSON contract (this doc + an OpenAPI/JSON
  schema in the repo) so the frontend and any grader can verify against a spec, not
  against implementation behavior.

## 7. API Contract (illustrative — refine in code, keep README/OpenAPI as source of truth)

```
GET /departures?q=Bru

200 OK
{
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
          "cancelled": false
        }
      ]
    },
    {
      "station": "Bruges",
      "status": "error",
      "error": "upstream_timeout",
      "departures": []
    }
  ]
}

400 Bad Request  (q shorter than 3 chars)
{
  "error": "query_too_short",
  "message": "q must be at least 3 characters",
  "min_length": 3
}
```

## 8. Success Criteria (how we'll judge our own build)

- Correct behavior on: normal query, short query, query matching zero stations, query
  matching a station with zero departures in-window, cancelled train, upstream failure
  on one of several matched stations.
- A reviewer can read the README, run two commands, and see it work.
- Every non-obvious decision in this PRD has a one-line justification in code or README
  — not because the brief asks for it, but because it's the difference between "I built
  this" and "I can defend this."

## 9. Open Questions (resolve during build, record answer in README)

- Debounce vs explicit search button on the frontend?
- Timeout/retry policy for iRail calls — one retry, or fail fast?
- Do we cache the iRail station list (it changes rarely) to avoid re-fetching per request?
