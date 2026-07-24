"""FastAPI application routes and endpoint orchestration for Lagovia Train Tracker.

Pure orchestration only: delegating fetch to irail_client and domain logic to domain.
"""

from contextlib import asynccontextmanager

import asyncio
from datetime import datetime, timezone
import logging
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import httpx

from app.domain import (
    build_response_dict,
    to_station_result_error,
    to_station_result_ok,
)
from app.irail_client import (
    IRailAPIError,
    IRailParseError,
    IRailTimeoutError,
    get_liveboard,
    search_stations,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application-level HTTP client lifespan."""
    app.state.http_client = httpx.AsyncClient(timeout=5.0, follow_redirects=True)
    yield
    await app.state.http_client.aclose()


app = FastAPI(
    title="Lagovia Train Tracker API",
    description="Thin layer on top of iRail API for Lagovia station departure tracking",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint to verify backend status."""
    return {"status": "ok"}


@app.get("/departures")
async def get_departures(q: Optional[str] = Query(None, description="Station search query")):
    """Get train departures scheduled in the next 15 minutes for matching stations."""
    # Constraint #4: Queries under 3 characters return HTTP 400 with error code query_too_short
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

    # Get HTTP client from app state or temporary fallback client
    client: httpx.AsyncClient = getattr(app.state, "http_client", None)
    should_close_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=5.0, follow_redirects=True)
        should_close_client = True

    try:
        # Step 1: Match stations by substring
        try:
            matched_stations = await search_stations(client, clean_query)
        except Exception as exc:
            logger.error("Failed to search stations for query '%s': %s", clean_query, exc)
            return JSONResponse(
                status_code=502,
                content={
                    "error": "upstream_error",
                    "message": "Failed to fetch station list from iRail",
                },
            )

        if not matched_stations:
            return build_response_dict(
                query=clean_query,
                station_results=[],
                now_utc=now_utc,
            )

        # Step 2: Fan out liveboard requests concurrently with return_exceptions=True
        # Constraint #5: Per-station error isolation
        tasks = [get_liveboard(client, s.id) for s in matched_stations]
        liveboard_results = await asyncio.gather(*tasks, return_exceptions=True)

        station_results = []
        for station, result in zip(matched_stations, liveboard_results):
            if isinstance(result, IRailTimeoutError):
                logger.warning("Upstream timeout for station '%s'", station.name)
                station_results.append(
                    to_station_result_error(station.name, "upstream_timeout")
                )
            elif isinstance(result, (IRailAPIError, IRailParseError, Exception)):
                logger.warning("Upstream error for station '%s': %s", station.name, result)
                station_results.append(
                    to_station_result_error(station.name, "upstream_error")
                )
            else:
                station_results.append(
                    to_station_result_ok(
                        station_name=station.name,
                        raw_departures=result,
                        now_utc=now_utc,
                    )
                )

        # Step 3: Build response dict matching PRD §7 contract
        return build_response_dict(
            query=clean_query,
            station_results=station_results,
            now_utc=now_utc,
        )
    finally:
        if should_close_client:
            await client.aclose()
