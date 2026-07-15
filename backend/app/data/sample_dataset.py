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
