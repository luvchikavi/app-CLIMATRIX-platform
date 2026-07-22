"""The "Load sample data" dataset — Galil Steel Ltd., FY2025.

A realistic Israeli steel-plant year (EAF + rolling mill): the same 51 rows
as the conference demo org, with the activity keys the Smart Import resolved
them to in production, so every org that loads the sample sees the exact
stage-verified numbers (~56.9 kt direct CO2e, ~64.5 kt with WTT).

Everything seeded from here is flagged is_demo=True and removed wholesale by
DELETE /sample-data.
"""

from datetime import date

SAMPLE_SITE = {
    "name": "Acre Works (Sample)",
    "country_code": "IL",
    "address": "Industrial Zone, Acre",
    "grid_region": "IL",
}

SAMPLE_PERIOD = {
    "name": "FY2025 (Sample)",
    "start_date": date(2025, 1, 1),
    "end_date": date(2025, 12, 31),
}

# Factor resolution region for the sample plant (Israeli grid/fuel factors),
# independent of the loading org's own default_region.
SAMPLE_REGION = "IL"

SAMPLE_DATA_QUALITY_SCORE = 3

# Monthly quantities, January..December (from the demo workbook).
_ELECTRICITY_KWH = [
    7_495_000,
    7_365_000,
    7_560_000,
    7_300_000,
    7_430_000,
    7_625_000,
    7_755_000,
    7_820_000,
    7_690_000,
    7_495_000,
    7_430_000,
    7_560_000,
]
_NATURAL_GAS_KWH = [
    6_625_500,
    6_530_500,
    6_720_500,
    6_435_500,
    6_625_500,
    6_815_500,
    6_910_500,
    6_910_500,
    6_815_500,
    6_625_500,
    6_530_500,
    6_720_500,
]
_DIESEL_LITERS = [
    43_200,
    42_000,
    44_400,
    43_200,
    43_200,
    45_600,
    46_800,
    46_800,
    45_600,
    43_200,
    43_200,
    44_400,
]
_LPG_LITERS = [
    10_470,
    10_000,
    10_470,
    10_000,
    10_470,
    10_940,
    10_940,
    10_940,
    10_470,
    10_470,
    10_000,
    10_470,
]


def _monthly(activity_key, scope, category_code, description, unit, quantities):
    return [
        {
            "activity_key": activity_key,
            "scope": scope,
            "category_code": category_code,
            "description": description,
            "quantity": qty,
            "unit": unit,
            "activity_date": date(2025, month, 15),
        }
        for month, qty in enumerate(quantities, start=1)
    ]


SAMPLE_ACTIVITIES = (
    _monthly(
        "electricity_il",
        2,
        "2",
        "Grid electricity (EAF + rolling mill)",
        "kWh",
        _ELECTRICITY_KWH,
    )
    + _monthly(
        "natural_gas_kwh",
        1,
        "1.1",
        "Natural gas (metered energy)",
        "kWh",
        _NATURAL_GAS_KWH,
    )
    + _monthly(
        "diesel_liters_mobile",
        1,
        "1.2",
        "Diesel (yard vehicles and generators)",
        "liter",
        _DIESEL_LITERS,
    )
    + _monthly(
        "lpg_liters",
        1,
        "1.1",
        "LPG (bulk supply, cutting torches)",
        "liters",
        _LPG_LITERS,
    )
    + [
        {
            "activity_key": "refrigerant_r410a",
            "scope": 1,
            "category_code": "1.3",
            "description": "R-410A refrigerant top-up — chillers",
            "quantity": 18,
            "unit": "kg",
            "activity_date": date(2025, 6, 30),
        },
        {
            "activity_key": "commute_car_petrol",
            "scope": 3,
            "category_code": "3.7",
            "description": "Employee commuting by car (petrol) — 310 employees",
            "quantity": 1_650_000,
            "unit": "km",
            "activity_date": date(2025, 12, 31),
        },
        {
            "activity_key": "flight_short_economy",
            "scope": 3,
            "category_code": "3.6",
            "description": "Business flights economy (TLV-FRA) — sales team, 96 round trips",
            "quantity": 570_000,
            "unit": "km",
            "activity_date": date(2025, 12, 31),
        },
    ]
)

# Decarbonization seeding (mirrors qa-conference/seed_scenarios.py)
SAMPLE_TARGET_NAME = "SBTi 1.5°C pathway — 2030 (Sample)"
SAMPLE_TARGET_DESCRIPTION = (
    "Science-based target aligned with the 1.5°C pathway; "
    "FY2025 baseline, Scopes 1+2."
)
SAMPLE_TARGET_YEAR = 2030
SAMPLE_BASE_YEAR = 2025

SAMPLE_SCENARIO_1 = {
    "name": "Electrification-first pathway (Sample)",
    "description": (
        "Tackle the largest sources first: electrify high-heat processes "
        "and shift purchased power to renewables."
    ),
    "scenario_type": "aggressive",
}
SAMPLE_SCENARIO_2 = {
    "name": "Quick wins — low capex (Sample)",
    "description": (
        "High-feasibility measures deliverable inside 24 months with "
        "minimal capital outlay."
    ),
    "scenario_type": "conservative",
}

# Keep the flagship scenario believable on stage: scale initiative
# reductions down so target achievement lands near the polished demo's 112%,
# instead of stacking full technical potential to >300%.
SAMPLE_ACHIEVEMENT_CAP = 1.12


# ============================================================================
# Tool-module sample data (PCF / LCA / EPD / CBAM) — same Galil Steel story.
# Seeded together with the core dataset; all rows flagged is_demo.
# ============================================================================

# Supplier-provided cradle-to-gate PCF for the billet input (primary data on
# the PACT ladder — lifts the product's primary-data share).
SAMPLE_SUPPLIER_PCF = {
    "supplier_name": "Hadera Billets Ltd. (Sample)",
    "product_name": "Continuous-cast steel billet",
    "pcf_value": 900,  # kg CO2e per tonne, cradle-to-gate
    "unit": "tonne",
    "boundary": "cradle_to_gate",
    "primary_data_share": 100.0,
    "source": "manual",
}

# Product 1 — computed + finalized on load, so /products, the LCA matrix and
# the EPD wizard all open onto real numbers (~1,075 kg CO2e/t like the
# stage-verified demo).
SAMPLE_PRODUCT_STEEL = {
    "name": "Hot-rolled steel coil (Sample)",
    "sku": "SAMPLE-HRC-01",
    "description": (
        "1 tonne of hot-rolled coil from the Acre Works EAF route — "
        "billet remelt, reheating furnace, rolling mill."
    ),
    "declared_unit": "tonne",
    "cn_code": "72083900",
    "category": "Basic metals",
}

# (input_type, name, qty/declared unit, unit, activity_key, module)
SAMPLE_STEEL_BOM = [
    {
        "input_type": "supplier_pcf",
        "name": "Steel billet (supplier PCF)",
        "quantity_per_unit": "1.05",
        "unit": "tonne",
        "en15804_module": "A1",
    },
    {
        "input_type": "transport",
        "name": "Inbound trucking, Hadera to Acre",
        "quantity_per_unit": "120",
        "unit": "tonne-km",
        "activity_key": "road_freight_hgv",
        "en15804_module": "A2",
    },
    {
        "input_type": "energy",
        "name": "Reheating furnace, natural gas",
        "quantity_per_unit": "300",
        "unit": "kWh",
        "activity_key": "natural_gas_kwh",
        "en15804_module": "A3",
    },
    {
        "input_type": "energy",
        "name": "Rolling mill electricity (IL grid)",
        "quantity_per_unit": "120",
        "unit": "kWh",
        "activity_key": "electricity_il",
        "en15804_module": "A3",
    },
]

# Product 2 — left as a draft with a BOM but NO computed footprint, so the
# user has a "Compute" journey of their own to click through.
SAMPLE_PRODUCT_BRACKET = {
    "name": "Galvanized mounting bracket (Sample)",
    "sku": "SAMPLE-BRK-01",
    "description": "Stamped bracket, 0.4 kg recycled aluminium per piece.",
    "declared_unit": "piece",
    "category": "Fabricated metal products",
}

SAMPLE_BRACKET_BOM = [
    {
        "input_type": "purchased_material",
        "name": "Recycled aluminium sheet",
        "quantity_per_unit": "0.4",
        "unit": "kg",
        "activity_key": "aluminum_recycled_purchased_kg",
        "en15804_module": "A1",
    },
    {
        "input_type": "energy",
        "name": "Stamping press electricity",
        "quantity_per_unit": "0.8",
        "unit": "kWh",
        "activity_key": "electricity_il",
        "en15804_module": "A3",
    },
]

# EPD project pinned to the steel coil's finalized footprint; left in draft
# so the wizard shows the whole ISO 14025 walk ahead.
SAMPLE_EPD = {
    "name": "Hot-rolled steel coil — EPD (Sample)",
    "pcr": "EN 15804+A2",
    "program_operator": "The International EPD System (Sample)",
    "declared_unit": "tonne",
}

# CBAM: one supplier installation + three imports (steel / cement /
# aluminium) computed with the official default values on load.
SAMPLE_CBAM_INSTALLATION = {
    "name": "Marmara Steel Works (Sample)",
    "country_code": "TR",
    "address": "Organize Sanayi Bolgesi, Gebze",
    "operator_name": "Marmara Celik A.S. (Sample)",
    "sector": "iron_steel",
}

# (cn_code, description, mass_tonnes, origin, days_ago, links installation).
# Dates are relative to load time so the imports land inside the register's
# default current-year filter instead of vanishing behind it.
SAMPLE_CBAM_IMPORTS = [
    {
        "cn_code": "72083900",
        "product_description": "Hot-rolled steel coil (Sample)",
        "mass_tonnes": "25",
        "origin_country": "TR",
        "days_ago": 130,
        "use_installation": True,
    },
    {
        "cn_code": "25232900",
        "product_description": "Portland cement (Sample)",
        "mass_tonnes": "60",
        "origin_country": "EG",
        "days_ago": 60,
        "use_installation": False,
    },
    {
        "cn_code": "76011000",
        "product_description": "Unwrought aluminium (Sample)",
        "mass_tonnes": "8",
        "origin_country": "AE",
        "days_ago": 14,
        "use_installation": False,
    },
]
