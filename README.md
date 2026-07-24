# Lagovia Train Tracker

A lightweight train departure tracker that answers: *"For any Belgian station matching what I typed, what's departing in the next 15 minutes, and how late is it?"*

Built on top of the iRail API (Belgium).

---

## Technical Stack

- **Backend**: Python 3.14 + FastAPI + `httpx` + `pytest`
- **Frontend**: React 18 + TypeScript + Vite + CSS Modules / Plain CSS

---

## Documentation

- [Phase 0 Documentation — Repo & Tooling Skeleton](documentation/PHASE_0.md)
- [Phase 1 Documentation — iRail Client (Isolated & Tested)](documentation/PHASE_1.md)
- [Phase 2 Documentation — Core Domain Logic](documentation/PHASE_2.md)

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

---

## Running Verification & Tests

```bash
# Backend tests
cd backend && venv/bin/pytest

# Frontend typecheck & lint
cd frontend && npm run lint

# CI-Lite local check
make check
```

---

## Architecture & Design Trade-offs

1. **CI-Lite vs. Hosted CI**: Local automated checking via `make check` is provided to ensure clean build, linting, and tests pass before committing.
2. **In-Process Caching (Phase 1)**: Station lists change infrequently, so in-process caching is used to avoid refetching iRail's full `/stations` endpoint on every query.
3. **UTC Time Window Handling (Phase 2)**: 15-minute window calculations are enforced server-side in UTC to prevent client-side timezone drift.
