# AGENTS.md

Instructions for any AI coding agent (Claude Code, Copilot, Cursor, etc.) working in
this repository. Human contributors: this doubles as a fast-onboarding doc.

## What this repo is

A small, scope-disciplined app: one backend endpoint (`GET /departures`), one frontend
page. See `PRD.md` for requirements and `IMPLEMENTATION_PLAN.md` for build order. Read
both before making non-trivial changes — this repo is small enough that "just start
coding" reliably produces drift from the brief.

## Repo layout

```
/backend        FastAPI app
  /app
    irail_client.py   # pure fetch+parse against iRail, no FastAPI imports
    domain.py          # pure functions: window filter, response shaping
    main.py            # FastAPI routes, orchestration only
  /tests
/frontend       Vite + React + TypeScript
  /src
    api.ts             # typed client for GET /departures
    App.tsx
    components/
/PRD.md
/IMPLEMENTATION_PLAN.md
/TECH_STACK.md
/RULES.md
/README.md
/AI_USAGE.md
```

## Ground rules for agents

1. **Don't expand scope.** No auth, no journey planning, no polling/websockets, no
   database, unless explicitly asked. If a change seems to require one of these, stop
   and flag it rather than adding it silently.
2. **Keep `irail_client.py` and `domain.py` pure and dependency-free of FastAPI.** They
   must be testable without spinning up the app or hitting the network. `main.py` is the
   only place HTTP/orchestration concerns live.
3. **Never let one failing station take down the whole response.** Any change to the
   fan-out logic must preserve per-station error isolation (see PRD §5, FR7).
4. **Time handling is UTC, server-side, always.** Any change touching the 15-minute
   window must not introduce client-timezone dependence. Add/update a boundary test
   (exactly now, exactly +15min, +15min+1s) for any change here.
5. **The 3-character minimum query is a validation error (400), not an empty result
   (200).** These are semantically different and both are explicitly required by the
   brief — don't collapse them for convenience.
6. **Tests before claiming done.** `domain.py` and `irail_client.py` changes need unit
   tests against mocked responses (no live-network tests in the default test run).
   Endpoint changes need at least one integration test with iRail mocked.
7. **Match the documented API contract.** If you change the response shape, update
   `PRD.md` §7 and any OpenAPI/schema file in the same change — the contract doc and the
   code must never silently diverge.
8. **Prefer small, explainable diffs.** This project will be discussed live, line by
   line, in a walkthrough. Code that can't be explained in one or two sentences by
   whoever "owns" it afterward is a liability, not a feature — favor clarity over
   cleverness even when cleverness is shorter.
9. **When iRail behaves unexpectedly (rate limit, malformed field, downtime), fail
   loud in logs, fail soft in the response.** Never let an upstream quirk surface as an
   unhandled 500 to the frontend.

## Commands agents should know

```
# backend
cd backend && uvicorn app.main:app --reload
cd backend && pytest

# frontend
cd frontend && npm run dev
cd frontend && npm run lint && npm run build
```//adjust if the eventual implementation differs — keep this file in sync with reality.

## When you're unsure

Prefer asking (or leaving a `# TODO(decision needed): ...` comment referencing the
relevant PRD section) over guessing on anything that changes the documented contract,
the error model, or the scope. Silent scope creep is the failure mode this file exists
to prevent.
