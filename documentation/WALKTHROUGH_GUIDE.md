# Code Walkthrough & Architecture Defense Guide

> **Project**: Lagovia Train Tracker  
> **Purpose**: Technical architecture walkthrough, engineering decision defense, and live modification cheat sheet for technical reviews & follow-up interviews.  

---

## 1. High-Level System Architecture & Request Flow

```text
[ React + TS Frontend ]
       │
       │ HTTP GET /departures?q=Bru (Proxied to backend)
       ▼
[ FastAPI App ] (app/main.py)
       │  • Validates len(q) >= 3 (Returns 400 'query_too_short' if invalid)
       │
       ▼
[ iRail API Client ] (app/irail_client.py)
       │  • Checks in-process station list cache (fetches /stations from iRail if empty)
       │  • 1. Primary Path: Case-insensitive substring match ('Bru' -> Brussels-Central, Bruges)
       │  • 2. Additive Fallback: Fuzzy match via rapidfuzz if substring yields 0 stations (e.g., 'Antverpen')
       │  • Fans out concurrent liveboard requests using asyncio.gather(..., return_exceptions=True)
       │
       ▼
[ Business Domain Logic ] (app/domain.py)
       │  • Filters departures within strict UTC window [now, now + 15 minutes]
       │  • Formats ISO 8601 UTC strings with trailing 'Z'
       │  • Shapes response contract (to_departure, to_station_result_ok, to_station_result_error)
       │
       ▼
[ JSON Response ] -> [ Frontend UI Renders Station Cards & Badges ]
```

---

## 2. Module Ownership & Code Deep Dive

### 📦 Module A: [backend/app/irail_client.py](../backend/app/irail_client.py)
- **Role**: Communicates with the external iRail API (`api.irail.be`).
- **Key Guarantee**: **Zero FastAPI imports**. Completely decoupled and unit-testable without a web server or network access.
- **Custom Exceptions**:
  - `IRailError` (base)
  - `IRailTimeoutError`
  - `IRailAPIError`
  - `IRailParseError`
- **In-Process Caching**: `_stations_cache` stores the 700+ station list during process lifetime because station names change very rarely.
- **`follow_redirects=True`**: Configured on `httpx.AsyncClient` calls to resolve live iRail 303 See Other HTTP redirects automatically.
- **Additive Fuzzy Fallback**: `fuzzy_search_stations_in_list` uses `rapidfuzz.process.extract` with `fuzz.WRatio` and a cutoff score of 70.0. It **only** executes if primary substring search returns zero results.

### 📦 Module B: [backend/app/domain.py](../backend/app/domain.py)
- **Role**: Pure business logic and contract shaping.
- **Key Guarantee**: **Zero FastAPI imports**.
- **Time Window Rule**: `filter_window(departures, now, window_minutes=15)` filters departures strictly within `[now_utc, now_utc + 15m]`.
- **Exact Boundary Rules**:
  - `now - 1s` -> **Excluded** (past train)
  - `now` -> **Included** (departing right now)
  - `now + 15m` -> **Included** (exact upper bound)
  - `now + 15m + 1s` -> **Excluded** (outside window)
- **Contract Mappers**: `to_departure()`, `to_station_result_ok()`, `to_station_result_error()`.

### 📦 Module C: [backend/app/main.py](../backend/app/main.py)
- **Role**: FastAPI HTTP layer and route handlers.
- **Lifespan Context Manager**: Manages a shared `httpx.AsyncClient` lifespan (`app.state.http_client`).
- **Validation**:
  ```python
  if len(q.strip()) < 3:
      raise HTTPException(
          status_code=400,
          detail={"error": "query_too_short", "message": "q must be at least 3 characters", "min_length": 3}
      )
  ```
- **Concurrent Fan-Out & Partial Success Isolation**:
  ```python
  results = await asyncio.gather(*tasks, return_exceptions=True)
  ```
  If 1 station call times out or fails upstream, it is mapped to `status: "error"` (`error: "upstream_timeout"`) inside its station card, allowing all other stations to succeed with HTTP 200 OK.

### 🎨 Module D: [frontend/src/](../frontend/src/)
- **[api.ts](../frontend/src/api.ts)**: Typed client calling `GET /departures?q=<query>`.
- **[SearchForm.tsx](../frontend/src/components/SearchForm.tsx)**: Instant 3-character client-side validation and explicit submit button trigger.
- **[DepartureRow.tsx](../frontend/src/components/DepartureRow.tsx)**: Renders `delay_minutes === 0` as **"On time"** (green), delays as **"+X min"** (amber), and cancelled departures as **"CANCELLED"** (bold red badge with strikethrough text).

---

## 3. Defense Answers: "Why did you choose X over Y?"

| Question / Topic | Your Defense Answer |
|------------------|---------------------|
| **Why FastAPI over Node/Express?** | *"FastAPI gives us typed Pydantic models for strict contract enforcement and native async/await for non-blocking concurrent API calls to iRail."* |
| **Why zero FastAPI imports in `irail_client.py` and `domain.py`?** | *"Separation of Concerns. Business logic and API parsing should be testable without instantiating an ASGI app or running HTTP networks."* |
| **Why in-process memory cache for stations?** | *"Belgium's train station list (700+ entries) rarely changes. In-process caching avoids refetching the full station list on every query while keeping zero infra overhead."* |
| **Why `asyncio.gather(..., return_exceptions=True)`?** | *"Partial success architecture. If one station iRail request fails or times out, we isolate the error to that station card rather than failing the user's entire HTTP request."* |
| **Why explicit submit button instead of debouncing input?** | *"To avoid spamming the public iRail API on every keystroke. It provides a clearer user experience and respects upstream rate limits."* |
| **Why `rapidfuzz` as an additive fallback?** | *"Substring matching is our primary deterministic path. Fuzzy matching only activates when substring search yields 0 matches, successfully resolving typos like 'Antverpen' without altering standard queries."* |

---

## 4. Cheat Sheet for Live Modifications (Interview Scenarios)

If the reviewer asks you to make a small live change during the session:

### 🛠️ Scenario A: "Change the departure window from 15 minutes to 30 minutes"
1. Open [backend/app/domain.py](../backend/app/domain.py).
2. Change `DEFAULT_WINDOW_MINUTES = 15` to `30`.
3. Open [backend/app/main.py](../backend/app/main.py).
4. Run tests: `make check`.

### 🛠️ Scenario B: "Change minimum search query length from 3 characters to 2"
1. Open [backend/app/main.py](../backend/app/main.py).
2. Change `len(q.strip()) < 3` to `< 2` and `"min_length": 2`.
3. Open [frontend/src/components/SearchForm.tsx](../frontend/src/components/SearchForm.tsx).
4. Change `trimmed.length < 3` to `< 2`.
5. Run tests: `make check`.

### 🛠️ Scenario C: "Add platform number / track to the departure item"
1. Open [backend/app/irail_client.py](../backend/app/irail_client.py) and add `platform: str = ""` to `RawDeparture`.
2. Open [backend/app/domain.py](../backend/app/domain.py) and add `platform: str` to `Departure`.
3. Map `platform=item.get("platform", "")` in `to_departure()`.
4. Update `frontend/src/types.ts` and `DepartureRow.tsx`.
5. Run `make check`.

---

## 5. Verification Commands Ready at Your Fingertips

```bash
# 1. Run all 22 backend unit and integration tests
cd backend && venv/bin/pytest -v

# 2. Run frontend typechecking and build
cd frontend && npm run lint && npm run build

# 3. Run full CI-Lite automated test suite
make check
```
