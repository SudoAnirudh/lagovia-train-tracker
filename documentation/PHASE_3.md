# Phase 3 Documentation — `GET /departures` Endpoint

> **Project**: Lagovia Train Tracker  
> **Phase**: Phase 3 — `GET /departures` Endpoint  
> **Status**: Completed  
> **Date**: July 24, 2026  

---

## 1. Overview & Objectives

Phase 3 implements the core endpoint `GET /departures?q=<substring>` in `backend/app/main.py`. This phase orchestrates substring matching, concurrent iRail liveboard requests across matched stations, 15-minute time window filtering, and strict error isolation.

### Key Rules & Constraints Enforced
1. **Minimum Query Validation (400 `query_too_short`)**:
   Queries shorter than 3 characters (`len(q) < 3`) return HTTP 400 Bad Request with a machine-readable error payload:
   ```json
   {
     "error": "query_too_short",
     "message": "q must be at least 3 characters",
     "min_length": 3
   }
   ```
2. **Concurrent Upstream Fan-Out**:
   Requests to iRail's `/liveboard` for matched stations run concurrently using `asyncio.gather(*tasks, return_exceptions=True)`.
3. **Per-Station Error Isolation (Partial Success)**:
   If an upstream call fails for one station (e.g. timeout or HTTP 500), that station is returned with `status: "error"` and the rest of the response succeeds with HTTP 200 OK.
4. **Offline Integration Testing**:
   Tested using `pytest` and `httpx.AsyncClient` with `ASGITransport`, mocking iRail using `respx`.

---

## 2. Endpoint Implementation ([backend/app/main.py](../backend/app/main.py))

```python
@app.get("/departures")
async def get_departures(q: Optional[str] = Query(None)):
    # 1. Validate query length
    if not q or len(q.strip()) < 3:
        return JSONResponse(
            status_code=400,
            content={
                "error": "query_too_short",
                "message": "q must be at least 3 characters",
                "min_length": 3,
            },
        )

    clean_query = q.strip()
    now_utc = datetime.now(timezone.utc)
    client = getattr(app.state, "http_client", None)

    # 2. Search stations matching query substring
    matched_stations = await search_stations(client, clean_query)
    if not matched_stations:
        return build_response_dict(clean_query, [], now_utc)

    # 3. Concurrent fan-out to iRail liveboard with return_exceptions=True
    tasks = [get_liveboard(client, s.id) for s in matched_stations]
    liveboard_results = await asyncio.gather(*tasks, return_exceptions=True)

    # 4. Handle per-station results or isolated errors
    station_results = []
    for station, result in zip(matched_stations, liveboard_results):
        if isinstance(result, IRailTimeoutError):
            station_results.append(to_station_result_error(station.name, "upstream_timeout"))
        elif isinstance(result, (IRailAPIError, IRailParseError, Exception)):
            station_results.append(to_station_result_error(station.name, "upstream_error"))
        else:
            station_results.append(to_station_result_ok(station.name, result, now_utc))

    # 5. Build final PRD §7 response
    return build_response_dict(clean_query, station_results, now_utc)
```

---

## 3. Integration Test Verification

The integration test suite in [backend/tests/test_departures_endpoint.py](../backend/tests/test_departures_endpoint.py) verifies all endpoint validation rules and error isolation:

```bash
$ venv/bin/pytest backend/tests/test_departures_endpoint.py -v

backend/tests/test_departures_endpoint.py::test_query_too_short_validation PASSED [ 25%]
backend/tests/test_departures_endpoint.py::test_departures_success_integration PASSED [ 50%]
backend/tests/test_departures_endpoint.py::test_no_matching_stations PASSED [ 75%]
backend/tests/test_departures_endpoint.py::test_partial_upstream_failure_isolation PASSED [100%]

======================== 4 passed in 0.48s ========================
```

---

## 4. Key Design Decisions & Trade-Offs

1. **Explicit 400 for Short Queries**:
   Returning HTTP 400 for queries under 3 characters differentiates validation errors from empty search results (HTTP 200 with `"stations": []`).
2. **`asyncio.gather` with `return_exceptions=True`**:
   Executing liveboard requests concurrently minimizes total request latency. Wrapping with `return_exceptions=True` guarantees that one failing upstream call never crashes the rest of the station queries.
