from pathlib import Path
import pytest
from datetime import datetime, timezone
import httpx
from httpx import ASGITransport, AsyncClient
import respx

from app.irail_client import clear_stations_cache
from app.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> str:
    return (FIXTURES_DIR / filename).read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def reset_cache():
    clear_stations_cache()
    yield
    clear_stations_cache()


@pytest.mark.asyncio
async def test_query_too_short_validation():
    """Test queries shorter than 3 characters return HTTP 400 query_too_short."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 2 characters
        response = await client.get("/departures?q=Br")
        assert response.status_code == 400
        assert response.json() == {
            "error": "query_too_short",
            "message": "q must be at least 3 characters",
            "min_length": 3,
        }

        # Empty query
        response_empty = await client.get("/departures?q=")
        assert response_empty.status_code == 400
        assert response_empty.json()["error"] == "query_too_short"

        # Missing query param
        response_missing = await client.get("/departures")
        assert response_missing.status_code == 400
        assert response_missing.json()["error"] == "query_too_short"


@pytest.mark.asyncio
@respx.mock
async def test_departures_success_integration():
    """Test successful endpoint orchestration with mocked iRail calls."""
    respx.get("https://api.irail.be/stations/?format=json&lang=en").respond(
        status_code=200,
        text=load_fixture("stations.json"),
    )

    # Return departures for Brussels
    now_ts = int(datetime.now(timezone.utc).timestamp())
    liveboard_brussels_data = {
        "version": "1.1",
        "station": "Brussels-Central",
        "departures": {
            "number": "1",
            "departure": [
                {
                    "id": "0",
                    "delay": "240",
                    "station": "Ostend",
                    "time": str(now_ts + 300),  # +5m (in window)
                    "vehicle": "BE.NMBS.IC3033",
                    "vehicleinfo": {"shortname": "IC3033"},
                    "canceled": "0",
                }
            ],
        },
    }

    # Return empty departures for Bruges
    liveboard_bruges_data = {
        "version": "1.1",
        "station": "Bruges",
        "departures": {"number": "0"},
    }

    respx.get("https://api.irail.be/liveboard/?id=BE.NMBS.008812005&format=json&lang=en").respond(
        status_code=200, json=liveboard_brussels_data
    )
    respx.get("https://api.irail.be/liveboard/?id=BE.NMBS.008891009&format=json&lang=en").respond(
        status_code=200, json=liveboard_bruges_data
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/departures?q=Bru")
        assert response.status_code == 200

        data = response.json()
        assert data["query"] == "Bru"
        assert data["window_minutes"] == 15
        assert "generated_at" in data
        assert len(data["stations"]) == 2

        bxl = next(s for s in data["stations"] if s["station"] == "Brussels-Central")
        assert bxl["status"] == "ok"
        assert len(bxl["departures"]) == 1
        assert bxl["departures"][0]["train_number"] == "IC3033"
        assert bxl["departures"][0]["delay_minutes"] == 4
        assert bxl["departures"][0]["cancelled"] is False

        bruges = next(s for s in data["stations"] if s["station"] == "Bruges")
        assert bruges["status"] == "ok"
        assert bruges["departures"] == []


@pytest.mark.asyncio
@respx.mock
async def test_no_matching_stations():
    """Test query matching zero stations returns HTTP 200 with empty stations list."""
    respx.get("https://api.irail.be/stations/?format=json&lang=en").respond(
        status_code=200,
        text=load_fixture("stations.json"),
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/departures?q=NonexistentStation")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "NonexistentStation"
        assert data["stations"] == []


@pytest.mark.asyncio
@respx.mock
async def test_partial_upstream_failure_isolation():
    """Test per-station error isolation (constraint #5 / rule #10).

    Brussels-Central succeeds, Bruges times out -> overall HTTP 200 response with
    Brussels status: ok and Bruges status: error.
    """
    respx.get("https://api.irail.be/stations/?format=json&lang=en").respond(
        status_code=200,
        text=load_fixture("stations.json"),
    )

    now_ts = int(datetime.now(timezone.utc).timestamp())
    liveboard_bxl = {
        "version": "1.1",
        "station": "Brussels-Central",
        "departures": {
            "number": "1",
            "departure": [
                {
                    "id": "0",
                    "delay": "0",
                    "station": "Ghent",
                    "time": str(now_ts + 120),
                    "vehicle": "BE.NMBS.S1",
                    "vehicleinfo": {"shortname": "S1"},
                    "canceled": "0",
                }
            ],
        },
    }

    # Brussels succeeds
    respx.get("https://api.irail.be/liveboard/?id=BE.NMBS.008812005&format=json&lang=en").respond(
        status_code=200, json=liveboard_bxl
    )
    # Bruges times out
    respx.get("https://api.irail.be/liveboard/?id=BE.NMBS.008891009&format=json&lang=en").mock(
        side_effect=httpx.TimeoutException("Upstream timeout")
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/departures?q=Bru")
        assert response.status_code == 200  # Partial failure does NOT cause 500!

        data = response.json()
        assert len(data["stations"]) == 2

        bxl = next(s for s in data["stations"] if s["station"] == "Brussels-Central")
        assert bxl["status"] == "ok"
        assert len(bxl["departures"]) == 1

        bruges = next(s for s in data["stations"] if s["station"] == "Bruges")
        assert bruges["status"] == "error"
        assert bruges["error"] == "upstream_timeout"
        assert bruges["departures"] == []
