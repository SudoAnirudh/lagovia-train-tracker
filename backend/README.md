# Backend — Lagovia Train Tracker

Python + FastAPI backend service for the Lagovia Train Tracker application.

---

## Technical Stack

- **Framework**: FastAPI (Python 3.14 / 3.12+)
- **HTTP Client**: `httpx` (async)
- **Data Validation**: `pydantic` & Python `dataclasses`
- **Testing**: `pytest`, `pytest-asyncio`, `respx`

---

## Directory Layout

```text
backend/
├── app/
│   ├── __init__.py
│   ├── irail_client.py    # Pure fetch & parse client for iRail API (Zero FastAPI imports)
│   └── main.py            # FastAPI application routes & server entrypoint
├── tests/
│   ├── __init__.py
│   ├── fixtures/          # Mock JSON fixtures for offline unit testing
│   ├── test_health.py     # Diagnostic health route tests
│   └── test_irail_client.py # Pure unit tests for iRail client
├── requirements.txt       # Dependencies manifest
└── README.md              # This document
```

---

## Quickstart

### 1. Environment Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Linux/macOS
# or: venv\Scripts\activate on Windows

pip install -r requirements.txt
```

### 2. Running the Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive API documentation (OpenAPI / Swagger UI) will be available at:
`http://127.0.0.1:8000/docs`

---

## Running Tests

Run all backend unit tests:

```bash
venv/bin/pytest -v
```

All unit tests run offline against static fixtures in `tests/fixtures/` using `respx`. No live network calls are made during automated test execution.

---

## Architecture Principles

1. **Zero FastAPI Imports in Client**: `app/irail_client.py` is kept completely pure of web framework dependencies so it can be tested independently.
2. **Explicit Upstream Timeouts**: All iRail calls use an explicit timeout (default: 5.0 seconds).
3. **Typed Exceptions**: iRail errors are categorized into custom exceptions (`IRailTimeoutError`, `IRailAPIError`, `IRailParseError`).
