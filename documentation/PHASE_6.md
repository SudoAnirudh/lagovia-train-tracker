# Phase 6 Documentation — Additive Fuzzy Search Fallback

> **Project**: Lagovia Train Tracker  
> **Phase**: Phase 6 — Additive Fuzzy Search (Bonus Phase)  
> **Status**: Completed  
> **Date**: July 24, 2026  

---

## 1. Overview & Objectives

Phase 6 implements the bonus fuzzy search fallback in `backend/app/irail_client.py` using `rapidfuzz`.

### Key Requirements Enforced
1. **Primary Substring Path Untouched**: Case-insensitive substring matching remains the primary search path. If substring matching returns 1 or more stations (e.g. `"Bru"` -> `"Brussels-Central"`, `"Bruges"`), fuzzy matching is never triggered.
2. **Additive Fallback**: Fuzzy search is strictly an additive layer that only executes when primary substring matching returns **zero** matching stations.
3. **Typo Handling (`"Antverpen"` Example)**: Fuzzy search successfully resolves typos like `"Antverpen"` to `"Antwerpen-Centraal"` (or `"Antwerp-Central"`).
4. **Dependency Documentation**: Added `rapidfuzz` to `backend/requirements.txt` and documented its justification in `docs/TECH_STACK.md` per `RULES.md` Rule 6.

---

## 2. Implementation & Code Architecture

### 2.1 Pure Fuzzy Search Function (`irail_client.py`)
```python
def fuzzy_search_stations_in_list(
    stations: List[Station],
    query: str,
    score_cutoff: float = 70.0,
    limit: int = 5,
) -> List[Station]:
    """Additive fuzzy fallback search using rapidfuzz.

    Only invoked when primary substring matching returns zero results.
    Matches query against station.name and station.standard_name.
    """
    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        logger.warning("rapidfuzz library not available for fuzzy search")
        return []

    query_lower = query.strip().lower()
    if not query_lower:
        return []

    station_map = {}
    for s in stations:
        station_map[s.name.lower()] = s
        station_map[s.standard_name.lower()] = s

    names = list(station_map.keys())
    matches = process.extract(
        query_lower,
        names,
        scorer=fuzz.WRatio,
        score_cutoff=score_cutoff,
        limit=limit,
    )

    matched_stations = []
    seen_ids = set()
    for matched_name, _score, _index in matches:
        st = station_map[matched_name]
        if st.id not in seen_ids:
            seen_ids.add(st.id)
            matched_stations.append(st)

    return matched_stations
```

### 2.2 Orchestration Flow in `search_stations`
```python
async def search_stations(
    client: httpx.AsyncClient,
    query: str,
    lang: str = "en",
    timeout: float = DEFAULT_TIMEOUT,
    enable_fuzzy: bool = True,
) -> List[Station]:
    stations = await fetch_stations(client, lang=lang, timeout=timeout)
    
    # 1. Primary path: Substring match
    substring_matches = search_stations_in_list(stations, query)
    if substring_matches:
        return substring_matches

    # 2. Additive fallback: Fuzzy match if substring matches == 0
    if enable_fuzzy:
        return fuzzy_search_stations_in_list(stations, query)

    return []
```

---

## 3. Live API & Unit Verification

### 3.1 Unit & Integration Test Suite (`test_fuzzy_search.py`)
```bash
$ backend/venv/bin/pytest backend/tests/test_fuzzy_search.py -v
============================= test session starts ==============================
collected 3 items

backend/tests/test_fuzzy_search.py::test_fuzzy_search_antverpen_example PASSED
backend/tests/test_fuzzy_search.py::test_search_stations_primary_substring_and_fuzzy_fallback PASSED
backend/tests/test_fuzzy_search.py::test_departures_endpoint_fuzzy_search_integration PASSED
============================== 3 passed in 0.33s ===============================
```

### 3.2 Live iRail API Smoke Test Output
```text
Found 5 station(s) for fuzzy query "Antverpen":
  - Antwerp-Berchem (BE.NMBS.008821121)
  - Antwerp-Central (BE.NMBS.008821006)
  - Antwerp-East (BE.NMBS.008821022)
  - Antwerp-Haven (BE.NMBS.008821048)
  - Antwerp-Linkeroever (BE.NMBS.008894839)
```

---

## 4. Full Automated Verification

Executing `make check` verifies all 22 pytest backend unit/integration tests and frontend TypeScript compilation:

```bash
$ make check

cd backend && venv/bin/pytest
======================= 22 passed in 0.65s =======================

cd frontend && npm run lint && npm run build
✓ 35 modules transformed.
dist/assets/index-azsEFXEP.css    6.70 kB
dist/assets/index-D5PwPlhN.js   149.30 kB
✓ built in 1.05s
```
