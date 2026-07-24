from pathlib import Path
import pytest
import httpx
import respx

from app.irail_client import (
    IRailAPIError,
    IRailParseError,
    IRailTimeoutError,
    clear_stations_cache,
    fetch_stations,
    get_liveboard,
    search_stations,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> str:
    """Load a fixture JSON file as string."""
    return (FIXTURES_DIR / filename).read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def reset_cache():
    """Ensure stations cache is cleared before each test."""
    clear_stations_cache()
    yield
    clear_stations_cache()


@pytest.mark.asyncio
@respx.mock
async def test_fetch_stations_success():
    """Test fetching station list successfully from mocked iRail response."""
    respx.get("https://api.irail.be/stations/?format=json&lang=en").respond(
        status_code=200,
        text=load_fixture("stations.json"),
    )

    async with httpx.AsyncClient() as client:
        stations = await fetch_stations(client)
        assert len(stations) == 3
        assert stations[0].name == "Brussels-Central"
        assert stations[0].id == "BE.NMBS.008812005"
        assert stations[1].name == "Bruges"
        assert stations[2].name == "Gent-Sint-Pieters"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_stations_caching():
    """Test that second station fetch call reuses in-process cache without HTTP request."""
    route = respx.get("https://api.irail.be/stations/?format=json&lang=en").respond(
        status_code=200,
        text=load_fixture("stations.json"),
    )

    async with httpx.AsyncClient() as client:
        first_call = await fetch_stations(client)
        second_call = await fetch_stations(client)
        assert first_call == second_call
        assert route.call_count == 1  # Network endpoint called only once


@pytest.mark.asyncio
@respx.mock
async def test_search_stations_substring_case_insensitive():
    """Test substring searching stations with case insensitivity."""
    respx.get("https://api.irail.be/stations/?format=json&lang=en").respond(
        status_code=200,
        text=load_fixture("stations.json"),
    )

    async with httpx.AsyncClient() as client:
        # Matches 'Brussels-Central' and 'Bruges'
        results_bru = await search_stations(client, "bru")
        assert len(results_bru) == 2
        names = [s.name for s in results_bru]
        assert "Brussels-Central" in names
        assert "Bruges" in names

        # Matches 'Gent-Sint-Pieters'
        results_gent = await search_stations(client, "GENT")
        assert len(results_gent) == 1
        assert results_gent[0].name == "Gent-Sint-Pieters"

        # Non-matching substring returns empty list
        results_none = await search_stations(client, "nonexistent")
        assert results_none == []


@pytest.mark.asyncio
@respx.mock
async def test_get_liveboard_success():
    """Test fetching and parsing liveboard departures."""
    respx.get("https://api.irail.be/liveboard/?id=BE.NMBS.008812005&format=json&lang=en").respond(
        status_code=200,
        text=load_fixture("liveboard_brussels.json"),
    )

    async with httpx.AsyncClient() as client:
        departures = await get_liveboard(client, "BE.NMBS.008812005")
        assert len(departures) == 2

        # First departure
        dep1 = departures[0]
        assert dep1.station == "Ostend"
        assert dep1.delay == 240
        assert dep1.canceled is False
        assert dep1.vehicle_short_name == "IC3033"
        assert dep1.time == 1721816520

        # Second departure (canceled)
        dep2 = departures[1]
        assert dep2.station == "Antwerpen-Centraal"
        assert dep2.canceled is True
        assert dep2.vehicle_short_name == "S19"


@pytest.mark.asyncio
@respx.mock
async def test_get_liveboard_empty_departures():
    """Test liveboard with zero departures returning empty list cleanly."""
    respx.get("https://api.irail.be/liveboard/?id=BE.NMBS.008891009&format=json&lang=en").respond(
        status_code=200,
        text=load_fixture("liveboard_empty.json"),
    )

    async with httpx.AsyncClient() as client:
        departures = await get_liveboard(client, "BE.NMBS.008891009")
        assert departures == []


@pytest.mark.asyncio
@respx.mock
async def test_get_liveboard_timeout():
    """Test timeout when calling iRail liveboard raises IRailTimeoutError."""
    respx.get("https://api.irail.be/liveboard/?id=BE.NMBS.008812005&format=json&lang=en").mock(
        side_effect=httpx.TimeoutException("Connection timed out")
    )

    async with httpx.AsyncClient() as client:
        with pytest.raises(IRailTimeoutError):
            await get_liveboard(client, "BE.NMBS.008812005")


@pytest.mark.asyncio
@respx.mock
async def test_get_liveboard_http_500_error():
    """Test upstream 500 error raises IRailAPIError with status code."""
    respx.get("https://api.irail.be/liveboard/?id=BE.NMBS.008812005&format=json&lang=en").respond(
        status_code=500,
        text="Internal Server Error",
    )

    async with httpx.AsyncClient() as client:
        with pytest.raises(IRailAPIError) as exc_info:
            await get_liveboard(client, "BE.NMBS.008812005")
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
@respx.mock
async def test_get_liveboard_malformed_json():
    """Test malformed JSON response raises IRailParseError."""
    respx.get("https://api.irail.be/liveboard/?id=BE.NMBS.008812005&format=json&lang=en").respond(
        status_code=200,
        text="{ invalid_json: ",
    )

    async with httpx.AsyncClient() as client:
        with pytest.raises(IRailParseError):
            await get_liveboard(client, "BE.NMBS.008812005")
