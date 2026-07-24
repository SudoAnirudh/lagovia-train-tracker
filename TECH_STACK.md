# Tech Stack

## Choice

- **Backend**: Python 3.12 + FastAPI + `httpx` (async HTTP client) + `pytest` +
  `respx` or `pytest-httpx` for mocking iRail in tests.
- **Frontend**: React + TypeScript via Vite, no heavier framework (no Next.js — this is
  a single page with one input and one results view; a full-stack meta-framework would
  add ceremony without adding capability here).
- **Styling**: plain CSS or a minimal utility layer (e.g. plain CSS modules) — no
  component-library dependency for a page this small.
- **No database.** Every piece of state (station list, departures) is either fetched
  live from iRail or safely cache-able in-process for the process lifetime. Adding
  persistence would solve a problem this brief doesn't have.

## Why this over the stated alternative (Node/Express)

The brief explicitly allows either Node/Express or Python/FastAPI and says to justify a
different choice — this *is* one of the two suggested options, chosen because:
- FastAPI's typed request/response models (Pydantic) make the documented JSON contract
  (PRD §7) enforceable in code, not just in prose — a mismatch between docs and
  implementation becomes a validation error instead of a silent bug.
- Async support is a natural fit for fanning out concurrent per-station iRail calls
  (Phase 3 of the implementation plan) without extra middleware.
- Built-in OpenAPI generation (`/docs`) gives a live, always-accurate contract for
  free, which directly supports "Return JSON. Define the shape yourself and document
  it."

## Why not fuzzy-search libraries by default

`rapidfuzz` (or similar) is pulled in only for the bonus fuzzy-search phase, kept as an
optional/late dependency — not because it's heavy, but because pulling in dependencies
before the feature that needs them earns nothing and adds surface area to review.

## Explicitly rejected

- **Next.js / full-stack meta-framework**: no server-rendering or routing need here;
  would obscure rather than clarify the two-endpoint, one-page shape of this app.
- **Redis / any cache service**: in-process caching (or none) is sufficient at this
  scale; introducing infra to run locally raises the bar for anyone reviewing/running
  the submission for no real benefit.
- **GraphQL**: one endpoint, one shape — REST/JSON is the honest fit; GraphQL would be
  solving a problem (flexible client-driven queries across many resources) this app
  doesn't have.
- **WebSockets / SSE for live updates**: out of scope per PRD §4; flagged as a natural
  v2, not built now, to keep the submission's surface area matched to the brief.

## Dev environment expectations

- Backend: `venv` + `pip install -r requirements.txt` (or `uv`/`poetry` if preferred —
  pick one and document the exact commands in README, don't leave it ambiguous).
- Frontend: Node LTS + `npm install`.
- No Docker required for local dev given the small footprint, but a `docker-compose.yml`
  is a reasonable stretch addition if time allows — not required for the core brief.
