"""Seed data for CLIMATRIX v3."""
from app.data.emission_factors import EMISSION_FACTORS as BASE_EMISSION_FACTORS
from app.data.emission_factors_expanded import EXPANDED_EMISSION_FACTORS
from app.data.unit_conversions import UNIT_CONVERSIONS
from app.data.fuel_prices import FUEL_PRICES
from app.data.airports import (
    AIRPORTS,
    calculate_flight_distance,
    classify_flight_distance,
    get_airport,
    get_flight_emission_key,
    search_airports,
    get_airport_stats,
)
from app.data.transport_distances import (
    TRANSPORT_DISTANCES,
    TRANSPORT_EMISSION_FACTORS,
    get_transport_distance,
    calculate_transport_emissions,
    list_available_routes,
    get_transport_stats,
)
from app.data.reference_data import (
    CURRENCY_RATES,
    convert_to_usd,
    GRID_EMISSION_FACTORS,
    get_grid_factor,
    HOTEL_EMISSION_FACTORS,
    get_hotel_factor,
    REFRIGERANT_GWP,
    get_refrigerant_gwp,
    WASTE_DISPOSAL_FACTORS,
    get_waste_factor,
    PRICE_RANGES,
    validate_price,
)
from app.data.cbam_data import (
    CBAM_DEFAULT_VALUES,
    CBAM_GRID_FACTORS,
    CBAM_PRODUCTS,
    EU_ETS_PRICES_2024,
    get_default_see_by_cn_code,
    get_grid_factor_by_country,
    get_sector_for_cn_code,
)

# Combine base and expanded emission factors, deduplicating by activity_key.
# Base factors take priority (they are the primary audited source).
_base_keys = {f["activity_key"] for f in BASE_EMISSION_FACTORS}
_unique_expanded = [f for f in EXPANDED_EMISSION_FACTORS if f["activity_key"] not in _base_keys]
EMISSION_FACTORS = BASE_EMISSION_FACTORS + _unique_expanded

__all__ = [
    # Emission factors
    "EMISSION_FACTORS",
    "UNIT_CONVERSIONS",
    "FUEL_PRICES",
    "BASE_EMISSION_FACTORS",
    "EXPANDED_EMISSION_FACTORS",
    # Airports (Category 3.6)
    "AIRPORTS",
    "calculate_flight_distance",
    "classify_flight_distance",
    "get_airport",
    "get_flight_emission_key",
    "search_airports",
    "get_airport_stats",
    # Transport distances (Category 3.4)
    "TRANSPORT_DISTANCES",
    "TRANSPORT_EMISSION_FACTORS",
    "get_transport_distance",
    "calculate_transport_emissions",
    "list_available_routes",
    "get_transport_stats",
    # Reference data
    "CURRENCY_RATES",
    "convert_to_usd",
    "GRID_EMISSION_FACTORS",
    "get_grid_factor",
    "HOTEL_EMISSION_FACTORS",
    "get_hotel_factor",
    "REFRIGERANT_GWP",
    "get_refrigerant_gwp",
    "WASTE_DISPOSAL_FACTORS",
    "get_waste_factor",
    "PRICE_RANGES",
    "validate_price",
    # CBAM reference data
    "CBAM_DEFAULT_VALUES",
    "CBAM_GRID_FACTORS",
    "CBAM_PRODUCTS",
    "EU_ETS_PRICES_2024",
    "get_default_see_by_cn_code",
    "get_grid_factor_by_country",
    "get_sector_for_cn_code",
]
