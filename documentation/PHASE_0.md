# Phase 0 Documentation — Repo & Tooling Skeleton

> **Project**: Lagovia Train Tracker  
> **Phase**: Phase 0 — Repo & Tooling Skeleton  
> **Status**: Completed  
> **Date**: July 24, 2026  

---

## 1. Overview & Objectives

Phase 0 establishes the foundation and developer tooling for the **Lagovia Train Tracker** application. The goal of this phase is to deliver a fully functional, testable repository skeleton for both the FastAPI backend and React + TypeScript frontend, accompanied by local CI-lite automation tools.

### Key Objectives
- Establish standard repository layout separating backend logic (`backend/`) from frontend interface (`frontend/`).
- Initialize a lightweight FastAPI backend server with a working `GET /health` diagnostic endpoint.
- Initialize a React 18 + TypeScript SPA using Vite with strict linting and type-checking rules.
- Set up local CI-lite check scripts (`Makefile`) to validate code quality, backend unit tests, and frontend build outputs in a single command (`make check`).
- Document initial architecture, dependencies, and engineering rules.

---

## 2. Repository Architecture

```text
/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py          # FastAPI app entrypoint & /health route
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_health.py   # Async test suite for health endpoint
│   └── requirements.txt     # Locked Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Static placeholder UI component
│   │   ├── main.tsx         # React DOM root entrypoint
│   │   └── index.css        # Core styling & modern theme variables
│   ├── index.html           # HTML5 entry document
│   ├── package.json         # Frontend dependencies & scripts
│   ├── tsconfig.json        # Strict TypeScript compiler configuration
│   └── vite.config.ts       # Vite bundler config with backend API proxying
├── documentation/
│   └── PHASE_0.md           # Detailed Phase 0 completion showcase (this document)
├── AI_USAGE.md              # Log of AI interactions and decisions
├── Makefile                 # Local CI-lite automation targets
├── README.md                # Project quickstart & architecture overview
└── .gitignore               # Excluded build artifacts and local virtual environments
```

---

## 3. Detailed Component Explanation

### 3.1 Backend (`backend/`)

The backend is built with **Python 3.14** and **FastAPI**, chosen for fast async execution and built-in OpenAPI schema generation.

- **[backend/app/main.py](file:///home/anirudhs/Documents/Boredom/DPS_CHALLENGE/backend/app/main.py)**:
  Defines the root FastAPI application instance and the `/health` GET route.
  ```python
  from fastapi import FastAPI

  app = FastAPI(
      title="Lagovia Train Tracker API",
      description="Thin layer on top of iRail API for Lagovia station departure tracking",
      version="1.0.0",
  )

  @app.get("/health")
  async def health_check():
      return {"status": "ok"}
  ```

- **[backend/tests/test_health.py](file:///home/anirudhs/Documents/Boredom/DPS_CHALLENGE/backend/tests/test_health.py)**:
  Uses `pytest` and `httpx.AsyncClient` with `ASGITransport` to execute tests directly against the FastAPI app in-memory without opening actual network ports.
  ```python
  import pytest
  from httpx import ASGITransport, AsyncClient
  from app.main import app

  @pytest.mark.asyncio
  async def test_health_endpoint():
      async with AsyncClient(
          transport=ASGITransport(app=app), base_url="http://test"
      ) as client:
          response = await client.get("/health")
          assert response.status_code == 200
          assert response.json() == {"status": "ok"}
  ```

- **Dependencies ([requirements.txt](file:///home/anirudhs/Documents/Boredom/DPS_CHALLENGE/backend/requirements.txt))**:
  - `fastapi` & `uvicorn[standard]` — Async REST framework & ASGI server.
  - `httpx` — Non-blocking HTTP client for upstream iRail calls.
  - `pydantic` — Strict request/response data validation.
  - `pytest`, `pytest-asyncio`, `respx` — Testing framework and HTTP mocking tools.

---

### 3.2 Frontend (`frontend/`)

The frontend is built using **React 18**, **TypeScript**, and **Vite**.

- **Vite Configuration ([vite.config.ts](file:///home/anirudhs/Documents/Boredom/DPS_CHALLENGE/frontend/vite.config.ts))**:
  Includes development proxies for `/departures` and `/health` routing requests to `http://127.0.0.1:8000` during local development, preventing CORS issues.
- **TypeScript Configuration ([tsconfig.json](file:///home/anirudhs/Documents/Boredom/DPS_CHALLENGE/frontend/tsconfig.json))**:
  Enforces strict type safety (`strict: true`, `noUnusedLocals: true`, `noUnusedParameters: true`).
- **Placeholder UI ([App.tsx](file:///home/anirudhs/Documents/Boredom/DPS_CHALLENGE/frontend/src/App.tsx))**:
  Provides an initial clean placeholder showcasing the app title, description, and status box.

---

### 3.3 CI-Lite Automation ([Makefile](file:///home/anirudhs/Documents/Boredom/DPS_CHALLENGE/Makefile))

A root `Makefile` standardizes local execution across developers:

```makefile
.PHONY: check test-backend check-frontend dev-backend dev-frontend

check: test-backend check-frontend

test-backend:
	cd backend && venv/bin/pytest

check-frontend:
	cd frontend && npm run lint && npm run build

dev-backend:
	cd backend && venv/bin/uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev
```

---

## 4. Verification & Testing

Executing `make check` performs complete validation of both backend tests and frontend typechecks/builds.

### Execution Output

```bash
$ make check

cd backend && venv/bin/pytest
============================= test session starts ==============================
platform linux -- Python 3.14.3, pytest-8.4.2, pluggy-1.6.0
rootdir: /home/anirudhs/Documents/Boredom/DPS_CHALLENGE/backend
plugins: respx-0.23.1, asyncio-0.26.0, anyio-4.14.2
asyncio: mode=Mode.STRICT
collected 1 item

tests/test_health.py .                                                   [100%]
======================== 1 passed in 0.22s ========================

cd frontend && npm run lint && npm run build
> lagovia-train-tracker-frontend@1.0.0 lint
> tsc --noEmit

> lagovia-train-tracker-frontend@1.0.0 build
> tsc && vite build
vite v5.4.21 building for production...
✓ 31 modules transformed.
dist/index.html                   0.41 kB │ gzip:  0.28 kB
dist/assets/index-C7eTErin.css    0.66 kB │ gzip:  0.41 kB
dist/assets/index-DgKb_A-v.js   142.83 kB │ gzip: 45.94 kB
✓ built in 607ms
```

---

## 5. Architectural & Design Decisions

1. **Lightweight Tooling**:
   Local automation via `Makefile` was chosen over cloud CI pipelines for Phase 0 to ensure fast local developer feedback loops without adding cloud infrastructure overhead.
2. **ASGITransport Testing**:
   Testing the FastAPI application with `ASGITransport` avoids socket binding overhead and race conditions during rapid test runs.
3. **Strict TypeScript Options**:
   Enabled `noUnusedLocals` and `noImplicitAny` early to prevent technical debt from entering the codebase in subsequent implementation phases.

---

## 6. Next Steps

With Phase 0 complete and verified, the codebase is ready for **Phase 1: iRail client, isolated and tested** (`irail_client.py`).
