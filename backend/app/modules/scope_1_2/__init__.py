"""
CLIMATRIX - Scope 1 & 2 Module

This module contains all GHG Protocol Scope 1 and Scope 2 emission factors,
fuel prices, and calculation logic.

STATUS: LOCKED (verified by verify_scope_1_2.py)

Categories:
- 1.1 Stationary Combustion (10 factors)
- 1.2 Mobile Combustion (14 factors)
- 1.3 Fugitive Emissions (32 factors)
- 1.4 Process Emissions (13 factors)
- 2.1 Purchased Electricity (58 factors, 56 countries)
- 2.2 Purchased Heat/Steam (2 factors)
- 2.3 Purchased Cooling (2 factors)

Total: 131 emission factors + 142 fuel prices

DO NOT MODIFY without running: python -m app.cli.verify_scope_1_2
"""

from .emission_factors import (
    SCOPE_1_FACTORS,
    SCOPE_2_FACTORS,
    get_factor,
    list_activity_keys,
    get_all_factors_flat,
)
from .fuel_prices import (
    FUEL_PRICES,
    get_fuel_price,
    list_available_regions,
    convert_spend_to_quantity,
    get_all_prices_flat,
)
from .categories import (
    CATEGORIES_SCOPE_1,
    CATEGORIES_SCOPE_2,
    ALL_CATEGORIES,
)

__all__ = [
    # Emission Factors
    "SCOPE_1_FACTORS",
    "SCOPE_2_FACTORS",
    "get_factor",
    "list_activity_keys",
    "get_all_factors_flat",
    # Fuel Prices
    "FUEL_PRICES",
    "get_fuel_price",
    "list_available_regions",
    "convert_spend_to_quantity",
    "get_all_prices_flat",
    # Categories
    "CATEGORIES_SCOPE_1",
    "CATEGORIES_SCOPE_2",
    "ALL_CATEGORIES",
]
