"""Pure fetch and parse client for iRail API (Belgium).

Zero FastAPI dependencies. Fully unit-testable without live network calls.
"""

from dataclasses import dataclass
import logging
from typing import List, Optional
import httpx

logger = logging.getLogger(__name__)

IRAIL_BASE_URL = "https://api.irail.be"
DEFAULT_TIMEOUT = 5.0  # Explicit 5-second timeout on upstream calls


class IRailError(Exception):
    """Base exception for iRail client errors."""
    pass


class IRailTimeoutError(IRailError):
    """Raised when an upstream request to iRail times out."""
    pass


class IRailAPIError(IRailError):
    """Raised when iRail returns a non-200 HTTP status or transport error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class IRailParseError(IRailError):
    """Raised when iRail response JSON is malformed or missing expected keys."""
    pass


@dataclass(frozen=True)
class Station:
    """Represents a station returned by iRail."""
    id: str
    name: str
    standard_name: str


@dataclass(frozen=True)
class RawDeparture:
    """Represents a raw departure item parsed from iRail liveboard."""
    station: str
    time: int  # Scheduled departure time in Unix seconds
    delay: int  # Delay in seconds
    canceled: bool
    vehicle: str
    vehicle_short_name: str


# In-process cache for the station list
# Station names change very rarely during process lifetime; caching avoids
# refetching the full station list on every query.
_stations_cache: Optional[List[Station]] = None


def clear_stations_cache() -> None:
    """Utility to clear the in-process stations cache (used in tests)."""
    global _stations_cache
    _stations_cache = None


async def fetch_stations(
    client: httpx.AsyncClient,
    lang: str = "en",
    force_refresh: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> List[Station]:
    """Fetch the complete list of Belgian train stations from iRail.

    Caches results in-process unless force_refresh is True.
    """
    global _stations_cache

    if _stations_cache is not None and not force_refresh:
        return _stations_cache

    url = f"{IRAIL_BASE_URL}/stations/?format=json&lang={lang}"
    try:
        response = await client.get(url, timeout=timeout, follow_redirects=True)
    except httpx.TimeoutException as exc:
        logger.error("Timeout fetching station list from iRail: %s", exc)
        raise IRailTimeoutError("Upstream timeout fetching station list") from exc
    except httpx.RequestError as exc:
        logger.error("Network error fetching station list from iRail: %s", exc)
        raise IRailAPIError(f"Network error: {exc}") from exc

    if response.status_code != 200:
        logger.error("iRail stations endpoint returned status %d", response.status_code)
        raise IRailAPIError(
            f"Upstream returned HTTP {response.status_code}",
            status_code=response.status_code,
        )

    try:
        data = response.json()
        station_list = data.get("station", [])
        stations = [
            Station(
                id=s.get("id", s.get("@id", "")),
                name=s.get("name", ""),
                standard_name=s.get("standardname", s.get("name", "")),
            )
            for s in station_list
            if s.get("name")
        ]
        _stations_cache = stations
        return stations
    except Exception as exc:
        logger.error("Failed to parse station list JSON from iRail: %s", exc)
        raise IRailParseError("Malformed station list JSON from iRail") from exc


def search_stations_in_list(stations: List[Station], query: str) -> List[Station]:
    """Pure helper to filter a list of stations by case-insensitive substring."""
    query_lower = query.strip().lower()
    if not query_lower:
        return []

    return [
        s for s in stations
        if query_lower in s.name.lower() or query_lower in s.standard_name.lower()
    ]


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


async def search_stations(
    client: httpx.AsyncClient,
    query: str,
    lang: str = "en",
    timeout: float = DEFAULT_TIMEOUT,
    enable_fuzzy: bool = True,
) -> List[Station]:
    """Search for stations matching query.

    Primary path: case-insensitive substring match.
    Additive fallback: fuzzy search (rapidfuzz) if substring search yields 0 matches.
    """
    stations = await fetch_stations(client, lang=lang, timeout=timeout)
    substring_matches = search_stations_in_list(stations, query)
    if substring_matches:
        return substring_matches

    if enable_fuzzy:
        return fuzzy_search_stations_in_list(stations, query)

    return []


async def get_liveboard(
    client: httpx.AsyncClient,
    station_id_or_name: str,
    lang: str = "en",
    timeout: float = DEFAULT_TIMEOUT,
) -> List[RawDeparture]:
    """Fetch liveboard departures for a given station ID or name."""
    url = f"{IRAIL_BASE_URL}/liveboard/?id={station_id_or_name}&format=json&lang={lang}"
    try:
        response = await client.get(url, timeout=timeout, follow_redirects=True)
    except httpx.TimeoutException as exc:
        logger.error("Timeout fetching liveboard for station %s: %s", station_id_or_name, exc)
        raise IRailTimeoutError(f"Upstream timeout for station {station_id_or_name}") from exc
    except httpx.RequestError as exc:
        logger.error("Network error fetching liveboard for station %s: %s", station_id_or_name, exc)
        raise IRailAPIError(f"Network error for station {station_id_or_name}: {exc}") from exc

    if response.status_code != 200:
        logger.error("iRail liveboard returned status %d for station %s", response.status_code, station_id_or_name)
        raise IRailAPIError(
            f"Upstream returned HTTP {response.status_code} for station {station_id_or_name}",
            status_code=response.status_code,
        )

    try:
        data = response.json()
        departures_data = data.get("departures", {})
        if not isinstance(departures_data, dict):
            return []

        raw_list = departures_data.get("departure", [])
        if not isinstance(raw_list, list):
            return []

        results = []
        for dep in raw_list:
            if not isinstance(dep, dict):
                continue

            station_dest = dep.get("station", "")
            time_val = int(dep.get("time", 0))
            delay_val = int(dep.get("delay", 0))
            canceled_raw = dep.get("canceled", "0")
            canceled_bool = str(canceled_raw) in ("1", "true", "True")

            vehicle_info = dep.get("vehicleinfo", {})
            if isinstance(vehicle_info, dict) and vehicle_info.get("shortname"):
                vehicle_short = vehicle_info["shortname"]
            else:
                vehicle_full = dep.get("vehicle", "")
                vehicle_short = vehicle_full.replace("BE.NMBS.", "")

            results.append(
                RawDeparture(
                    station=station_dest,
                    time=time_val,
                    delay=delay_val,
                    canceled=canceled_bool,
                    vehicle=dep.get("vehicle", ""),
                    vehicle_short_name=vehicle_short,
                )
            )

        return results
    except Exception as exc:
        logger.error("Failed to parse liveboard JSON for station %s: %s", station_id_or_name, exc)
        raise IRailParseError(f"Malformed liveboard JSON for station {station_id_or_name}") from exc
