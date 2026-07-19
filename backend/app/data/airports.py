"""
IATA Airport Database for Flight Distance Calculations.

Source: OpenFlights.org (bundled snapshot — see GAZETTEER_VERSION).
Loaded from airports.csv sitting next to this module: ~6,000 IATA-coded
airports worldwide with coordinates for great-circle distance calculations.
The gazetteer is bundled and versioned — no external API calls at runtime,
so every derived distance is reproducible for the audit trail.
"""

import csv
from math import radians, sin, cos, sqrt, atan2
from pathlib import Path
from typing import Optional, Tuple

# Bundled snapshot identifier, recorded in provenance of derived quantities.
GAZETTEER_VERSION = "openflights-2026-07"

_CSV_PATH = Path(__file__).parent / "airports.csv"

# =============================================================================
# IATA AIRPORT DATABASE
# Format: IATA_CODE -> (name, city, country_iso2, latitude, longitude)
# =============================================================================


def _load_airports() -> dict[str, Tuple[str, str, str, float, float]]:
    airports: dict[str, Tuple[str, str, str, float, float]] = {}
    with open(_CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            airports[row["iata"]] = (
                row["name"],
                row["city"],
                row["country"],
                float(row["lat"]),
                float(row["lon"]),
            )
    return airports


AIRPORTS: dict[str, Tuple[str, str, str, float, float]] = _load_airports()


# =============================================================================
# DISTANCE CALCULATION
# =============================================================================

EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points using Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of first point in degrees
        lat2, lon2: Latitude and longitude of second point in degrees

    Returns:
        Distance in kilometers
    """
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def get_airport(iata_code: str) -> Optional[Tuple[str, str, str, float, float]]:
    """
    Get airport details by IATA code.

    Args:
        iata_code: 3-letter IATA airport code (case-insensitive)

    Returns:
        Tuple of (name, city, country, latitude, longitude) or None if not found
    """
    return AIRPORTS.get(iata_code.upper())


def calculate_flight_distance(origin: str, destination: str) -> Optional[float]:
    """
    Calculate flight distance between two airports.

    Args:
        origin: IATA code of origin airport
        destination: IATA code of destination airport

    Returns:
        Distance in kilometers, or None if airports not found
    """
    origin_data = get_airport(origin)
    dest_data = get_airport(destination)

    if not origin_data or not dest_data:
        return None

    return haversine_distance(
        origin_data[3], origin_data[4], dest_data[3], dest_data[4]
    )


# Israel airport IATA codes
ISRAEL_AIRPORTS = {"TLV", "ETM", "VDA", "HFA", "SDV"}


def classify_flight_distance(
    distance_km: float, origin: str = None, destination: str = None
) -> str:
    """
    Classify flight distance as domestic, short, medium, or long haul.

    Israel-specific rules:
    - Israel domestic (any IL airport <-> any IL airport) -> "domestic"
    - Israel international (IL <-> non-IL) -> always "long" (DEFRA SHORT is UK-specific)

    Standard DEFRA rules (non-Israel):
    - Short-haul: < 785 km (e.g., domestic UK, Europe regional)
    - Medium-haul: 785-3700 km (e.g., UK to Middle East, intra-Europe)
    - Long-haul: > 3700 km (e.g., intercontinental)

    Args:
        distance_km: Flight distance in kilometers
        origin: IATA code of origin airport (optional, for Israel logic)
        destination: IATA code of destination airport (optional, for Israel logic)

    Returns:
        Classification: "domestic", "short", "medium", or "long"

    Note:
        When Israel domestic flights return "domestic", the emission factor key will be
        "flight_domestic_economy" (or other cabin class). Ensure that a corresponding
        emission factor (e.g., flight_domestic_economy) exists in the database/seed data.
    """
    # Israel-specific classification
    if origin and destination:
        origin_upper = origin.upper()
        dest_upper = destination.upper()
        origin_is_il = origin_upper in ISRAEL_AIRPORTS
        dest_is_il = dest_upper in ISRAEL_AIRPORTS

        if origin_is_il and dest_is_il:
            return "domestic"

        if origin_is_il or dest_is_il:
            # Israel international flights are always classified as long-haul
            # DEFRA short-haul category is UK-specific
            return "long"

    # Standard DEFRA thresholds for non-Israel flights
    if distance_km < 785:
        return "short"
    elif distance_km < 3700:
        return "medium"
    else:
        return "long"


def get_flight_emission_key(
    origin: str, destination: str, cabin_class: str = "economy"
) -> Optional[str]:
    """
    Get the appropriate emission factor activity key for a flight route.

    Args:
        origin: IATA code of origin airport
        destination: IATA code of destination airport
        cabin_class: Cabin class - "economy", "premium_economy", "business", "first"

    Returns:
        Activity key string or None if airports not found
    """
    distance = calculate_flight_distance(origin, destination)
    if distance is None:
        return None

    haul_type = classify_flight_distance(distance, origin, destination)

    cabin_map = {
        "economy": "economy",
        "premium_economy": "premium_economy",
        "business": "business",
        "first": "first",
    }
    cabin_suffix = cabin_map.get(cabin_class.lower(), "economy")

    return f"flight_{haul_type}_{cabin_suffix}"


def search_airports(query: str, limit: int = 10) -> list[dict]:
    """
    Search airports by name, city, or IATA code.

    Exact IATA-code matches rank first, then city/name prefix matches,
    then substring matches — with ~6,000 airports a bare substring scan
    would bury LHR under every city containing "lon".

    Args:
        query: Search term (case-insensitive)
        limit: Maximum number of results

    Returns:
        List of airport dictionaries
    """
    query = query.upper()
    ranked: list[tuple[int, str, dict]] = []

    for code, (name, city, country, lat, lon) in AIRPORTS.items():
        name_u = name.upper()
        city_u = city.upper()
        if query == code:
            rank = 0
        elif city_u.startswith(query) or name_u.startswith(query):
            rank = 1
        elif query in code or query in name_u or query in city_u:
            rank = 2
        else:
            continue
        ranked.append(
            (
                rank,
                code,
                {
                    "iata_code": code,
                    "name": name,
                    "city": city,
                    "country": country,
                    "latitude": lat,
                    "longitude": lon,
                },
            )
        )

    ranked.sort(key=lambda r: (r[0], r[1]))
    return [item for _, _, item in ranked[:limit]]


# =============================================================================
# AIRPORT STATISTICS
# =============================================================================


def get_airport_stats() -> dict:
    """Get statistics about the airport database."""
    countries = set()
    for _, (_, _, country, _, _) in AIRPORTS.items():
        countries.add(country)

    return {
        "total_airports": len(AIRPORTS),
        "countries_covered": len(countries),
        "country_list": sorted(countries),
    }
