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
