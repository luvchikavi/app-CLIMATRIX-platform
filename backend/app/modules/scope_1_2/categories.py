"""
CLIMATRIX - Scope 1 & 2 Category Definitions

GHG Protocol compliant category structure.
STATUS: LOCKED
"""

CATEGORIES_SCOPE_1 = {
    "1.1": {
        "name": "Stationary Combustion",
        "description": "Fuel burned in stationary equipment (boilers, furnaces, generators, heaters)",
        "units": ["m3", "kWh", "liters", "kg"],
        "calculation_methods": ["physical", "spend"],
    },
    "1.2": {
        "name": "Mobile Combustion",
        "description": "Fuel burned in company-owned/controlled vehicles",
        "units": ["km", "liters"],
        "calculation_methods": ["distance", "fuel", "spend"],
    },
    "1.3": {
        "name": "Fugitive Emissions",
        "description": "Unintentional releases (refrigerants, SF6, fire suppression)",
        "units": ["kg"],
        "calculation_methods": ["physical", "spend"],
    },
}

CATEGORIES_SCOPE_2 = {
    "2.1": {
        "name": "Purchased Electricity",
        "description": "Grid electricity consumption (56 countries supported)",
        "units": ["kWh"],
        "calculation_methods": ["location-based", "market-based", "spend"],
        "requires_country": True,
    },
    "2.2": {
        "name": "Purchased Heat/Steam",
        "description": "District heating, industrial steam",
        "units": ["kWh"],
        "calculation_methods": ["physical", "spend"],
    },
    "2.3": {
        "name": "Purchased Cooling",
        "description": "Chilled water, district cooling",
        "units": ["kWh"],
        "calculation_methods": ["physical", "spend"],
    },
}

# Combined for easy access
ALL_CATEGORIES = {**CATEGORIES_SCOPE_1, **CATEGORIES_SCOPE_2}
