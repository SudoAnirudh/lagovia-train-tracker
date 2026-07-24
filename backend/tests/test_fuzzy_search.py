from pathlib import Path
import pytest
from datetime import datetime, timezone
import httpx
from httpx import ASGITransport, AsyncClient
import respx

from app.irail_client import (
    Station,
    clear_stations_cache,
    fuzzy_search_stations_in_list,
    search_stations,
)
from app.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> str:
    return (FIXTURES_DIR / filename).read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def reset_cache():
    clear_stations_cache()
    yield
    clear_stations_cache()


def test_fuzzy_search_antverpen_example():
    """Test brief's specific example: 'Antverpen' (typo) fuzzy matches 'Antwerpen-Centraal'."""
    stations = [
        Station(id="BE.NMBS.008821006", name="Antwerpen-Centraal", standard_name="Antwerpen-Centraal"),
        Station(id="BE.NMBS.008812005", name="Brussels-Central", standard_name="Brussels-Central"),
        Station(id="BE.NMBS.008891009", name="Bruges", standard_name="Bruges"),
    ]

    matches = fuzzy_search_stations_in_list(stations, "Antverpen")
    assert len(matches) == 1
    assert matches[0].name == "Antwerpen-Centraal"


@pytest.mark.asyncio
@respx.mock
async def test_search_stations_primary_substring_and_fuzzy_fallback():
    """Test primary path stays substring search, and fuzzy search only triggers when substring matches = 0."""
    respx.get("https://api.irail.be/stations/?format=json&lang=en").respond(
        status_code=200,
        json={
            "station": [
                {"id": "BE.NMBS.008821006", "name": "Antwerpen-Centraal", "standardname": "Antwerpen-Centraal"},
                {"id": "BE.NMBS.008812005", "name": "Brussels-Central", "standardname": "Brussels-Central"},
                {"id": "BE.NMBS.008891009", "name": "Bruges", "standardname": "Bruges"},
            ]
        },
    )

    async with httpx.AsyncClient() as client:
        # Case 1: Substring match exists ('Bru') -> returns substring matches
        bru_results = await search_stations(client, "Bru")
        assert len(bru_results) == 2
        names = [s.name for s in bru_results]
        assert "Brussels-Central" in names
        assert "Bruges" in names

        # Case 2: Substring match = 0, fuzzy match exists ('Antverpen') -> returns Antwerpen-Centraal
        fuzzy_results = await search_stations(client, "Antverpen")
        assert len(fuzzy_results) == 1
        assert fuzzy_results[0].name == "Antwerpen-Centraal"

        # Case 3: Substring match = 0, no fuzzy match above cutoff ('XyzNonsense') -> returns []
        empty_results = await search_stations(client, "XyzNonsense")
        assert empty_results == []


@pytest.mark.asyncio
@respx.mock
async def test_departures_endpoint_fuzzy_search_integration():
    """Test GET /departures?q=Antverpen integration using fuzzy search fallback."""
    respx.get("https://api.irail.be/stations/?format=json&lang=en").respond(
        status_code=200,
        json={
            "station": [
                {"id": "BE.NMBS.008821006", "name": "Antwerpen-Centraal", "standardname": "Antwerpen-Centraal"}
            ]
        },
    )

    now_ts = int(datetime.now(timezone.utc).timestamp())
    liveboard_antwerp = {
        "version": "1.1",
        "station": "Antwerpen-Centraal",
        "departures": {
            "number": "1",
            "departure": [
                {
                    "id": "0",
                    "delay": "60",
                    "station": "Brussels-Central",
                    "time": str(now_ts + 200),
                    "vehicle": "BE.NMBS.IC100",
                    "vehicleinfo": {"shortname": "IC100"},
                    "canceled": "0",
                }
            ],
        },
    }

    respx.get("https://api.irail.be/liveboard/?id=BE.NMBS.008821006&format=json&lang=en").respond(
        status_code=200, json=liveboard_antwerp
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/departures?q=Antverpen")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Antverpen"
        assert len(data["stations"]) == 1
        assert data["stations"][0]["station"] == "Antwerpen-Centraal"
        assert data["stations"][0]["status"] == "ok"
        assert len(data["stations"][0]["departures"]) == 1
        assert data["stations"][0]["departures"][0]["train_number"] == "IC100"
