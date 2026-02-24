"""
Reference data for Scope 3 calculations.

Contains:
- Currency conversion rates
- Grid emission factors by country
- Hotel emission factors by country
- Refrigerant GWP values
- Waste disposal emission factors
- Price ranges for validation

Sources:
- Currency: ECB, OECD annual averages
- Grid factors: IEA, DEFRA, EPA eGRID
- Hotels: DEFRA, CRREM
- Refrigerants: IPCC AR6
- Waste: DEFRA, EPA WARM
"""
from decimal import Decimal


# =============================================================================
# CURRENCY CONVERSION RATES (2024 Annual Averages)
# Source: ECB, OECD
# =============================================================================

CURRENCY_RATES = {
    # To USD (all EEIO factors are in USD)
    "EUR": Decimal("1.08"),    # 1 EUR = 1.08 USD
    "GBP": Decimal("1.27"),    # 1 GBP = 1.27 USD
    "ILS": Decimal("0.27"),    # 1 ILS = 0.27 USD
    "CAD": Decimal("0.74"),    # 1 CAD = 0.74 USD
    "AUD": Decimal("0.66"),    # 1 AUD = 0.66 USD
    "JPY": Decimal("0.0067"),  # 1 JPY = 0.0067 USD
    "CNY": Decimal("0.14"),    # 1 CNY = 0.14 USD
    "INR": Decimal("0.012"),   # 1 INR = 0.012 USD
    "CHF": Decimal("1.13"),    # 1 CHF = 1.13 USD
    "SEK": Decimal("0.095"),   # 1 SEK = 0.095 USD
    "NOK": Decimal("0.092"),   # 1 NOK = 0.092 USD
    "DKK": Decimal("0.145"),   # 1 DKK = 0.145 USD
    "USD": Decimal("1.00"),    # 1 USD = 1.00 USD (identity)
}


def convert_to_usd(amount: Decimal, currency: str) -> Decimal | None:
    """
    Convert amount from local currency to USD.

    Args:
        amount: Amount in local currency
        currency: 3-letter currency code

    Returns:
        Amount in USD or None if currency not supported
    """
    rate = CURRENCY_RATES.get(currency.upper())
    if rate is None:
        return None
    return amount * rate


# =============================================================================
# GRID EMISSION FACTORS BY COUNTRY (2024)
# Sources: IEA 2024, DEFRA 2024, EPA eGRID 2024
# =============================================================================

GRID_EMISSION_FACTORS = {
    # Country -> {location_factor, market_factor, td_loss_percentage, source}
    # Factors in kg CO2e per kWh

    # Europe
    "GB": {
        "country_name": "United Kingdom",
        "location_factor": Decimal("0.207"),
        "market_factor": Decimal("0.312"),  # Residual mix
        "td_loss_percentage": Decimal("8.0"),
        "source": "DEFRA 2024",
        "year": 2024,
    },
    "DE": {
        "country_name": "Germany",
        "location_factor": Decimal("0.364"),
        "market_factor": Decimal("0.453"),
        "td_loss_percentage": Decimal("4.5"),
        "source": "AIB 2024",
        "year": 2024,
    },
    "FR": {
        "country_name": "France",
        "location_factor": Decimal("0.052"),
        "market_factor": Decimal("0.453"),  # EU residual
        "td_loss_percentage": Decimal("6.0"),
        "source": "IEA 2024",
        "year": 2024,
    },
    "ES": {
        "country_name": "Spain",
        "location_factor": Decimal("0.162"),
        "market_factor": Decimal("0.453"),
        "td_loss_percentage": Decimal("9.0"),
        "source": "IEA 2024",
        "year": 2024,
    },
    "IT": {
        "country_name": "Italy",
        "location_factor": Decimal("0.316"),
        "market_factor": Decimal("0.453"),
        "td_loss_percentage": Decimal("6.5"),
        "source": "IEA 2024",
        "year": 2024,
    },
    "NL": {
        "country_name": "Netherlands",
        "location_factor": Decimal("0.328"),
        "market_factor": Decimal("0.453"),
        "td_loss_percentage": Decimal("4.0"),
        "source": "IEA 2024",
        "year": 2024,
    },
    "PL": {
        "country_name": "Poland",
        "location_factor": Decimal("0.635"),
        "market_factor": Decimal("0.453"),
        "td_loss_percentage": Decimal("7.5"),
        "source": "IEA 2024",
        "year": 2024,
    },

    # North America
    "US": {
        "country_name": "United States",
        "location_factor": Decimal("0.386"),  # National average
        "market_factor": None,  # Varies by state
        "td_loss_percentage": Decimal("5.0"),
        "source": "EPA eGRID 2024",
        "year": 2024,
    },
    "CA": {
        "country_name": "Canada",
        "location_factor": Decimal("0.120"),
        "market_factor": None,
        "td_loss_percentage": Decimal("7.0"),
        "source": "Environment Canada 2024",
        "year": 2024,
    },

    # US eGRID Subregions (EPA eGRID 2024)
    "US-CAMX": {"country_name": "USA - CAMX (California)", "location_factor": Decimal("0.225"), "market_factor": None, "td_loss_percentage": Decimal("5.0"), "source": "EPA eGRID 2024", "year": 2024},
    "US-ERCT": {"country_name": "USA - ERCT (Texas)", "location_factor": Decimal("0.373"), "market_factor": None, "td_loss_percentage": Decimal("5.0"), "source": "EPA eGRID 2024", "year": 2024},
    "US-FRCC": {"country_name": "USA - FRCC (Florida)", "location_factor": Decimal("0.391"), "market_factor": None, "td_loss_percentage": Decimal("5.0"), "source": "EPA eGRID 2024", "year": 2024},
    "US-NEWE": {"country_name": "USA - NEWE (New England)", "location_factor": Decimal("0.227"), "market_factor": None, "td_loss_percentage": Decimal("5.0"), "source": "EPA eGRID 2024", "year": 2024},
    "US-NWPP": {"country_name": "USA - NWPP (Northwest)", "location_factor": Decimal("0.118"), "market_factor": None, "td_loss_percentage": Decimal("5.0"), "source": "EPA eGRID 2024", "year": 2024},
    "US-RFCE": {"country_name": "USA - RFCE (PJM East)", "location_factor": Decimal("0.297"), "market_factor": None, "td_loss_percentage": Decimal("5.0"), "source": "EPA eGRID 2024", "year": 2024},
    "US-RFCM": {"country_name": "USA - RFCM (Michigan)", "location_factor": Decimal("0.443"), "market_factor": None, "td_loss_percentage": Decimal("5.0"), "source": "EPA eGRID 2024", "year": 2024},
    "US-RFCW": {"country_name": "USA - RFCW (PJM West)", "location_factor": Decimal("0.497"), "market_factor": None, "td_loss_percentage": Decimal("5.0"), "source": "EPA eGRID 2024", "year": 2024},
    "US-RMPA": {"country_name": "USA - RMPA (Rockies)", "location_factor": Decimal("0.525"), "market_factor": None, "td_loss_percentage": Decimal("5.0"), "source": "EPA eGRID 2024", "year": 2024},
    "US-SRSO": {"country_name": "USA - SRSO (SERC South)", "location_factor": Decimal("0.383"), "market_factor": None, "td_loss_percentage": Decimal("5.0"), "source": "EPA eGRID 2024", "year": 2024},
    "US-SRVC": {"country_name": "USA - SRVC (Virginia/Carolina)", "location_factor": Decimal("0.347"), "market_factor": None, "td_loss_percentage": Decimal("5.0"), "source": "EPA eGRID 2024", "year": 2024},
    "US-MROW": {"country_name": "USA - MROW (MRO West)", "location_factor": Decimal("0.475"), "market_factor": None, "td_loss_percentage": Decimal("5.0"), "source": "EPA eGRID 2024", "year": 2024},

    # Middle East
    "IL": {
        "country_name": "Israel",
        "location_factor": Decimal("0.527"),
        "market_factor": None,
        "td_loss_percentage": Decimal("3.5"),
        "source": "IEC 2024",
        "year": 2024,
    },
    "AE": {
        "country_name": "UAE",
        "location_factor": Decimal("0.402"),
        "market_factor": None,
        "td_loss_percentage": Decimal("4.0"),
        "source": "IEA 2024",
        "year": 2024,
    },
    "SA": {
        "country_name": "Saudi Arabia",
        "location_factor": Decimal("0.528"),
        "market_factor": None,
        "td_loss_percentage": Decimal("6.0"),
        "source": "IEA 2024",
        "year": 2024,
    },

    # Asia
    "CN": {
        "country_name": "China",
        "location_factor": Decimal("0.555"),
        "market_factor": None,
        "td_loss_percentage": Decimal("5.5"),
        "source": "IEA 2024",
        "year": 2024,
    },
    "JP": {
        "country_name": "Japan",
        "location_factor": Decimal("0.470"),
        "market_factor": None,
        "td_loss_percentage": Decimal("4.5"),
        "source": "IEA 2024",
        "year": 2024,
    },
    "IN": {
        "country_name": "India",
        "location_factor": Decimal("0.708"),
        "market_factor": None,
        "td_loss_percentage": Decimal("19.0"),  # High losses
        "source": "IEA 2024",
        "year": 2024,
    },
    "KR": {
        "country_name": "South Korea",
        "location_factor": Decimal("0.417"),
        "market_factor": None,
        "td_loss_percentage": Decimal("3.5"),
        "source": "IEA 2024",
        "year": 2024,
    },
    "SG": {
        "country_name": "Singapore",
        "location_factor": Decimal("0.408"),
        "market_factor": None,
        "td_loss_percentage": Decimal("2.0"),
        "source": "IEA 2024",
        "year": 2024,
    },

    # Oceania
    "AU": {
        "country_name": "Australia",
        "location_factor": Decimal("0.656"),  # National average
        "market_factor": None,
        "td_loss_percentage": Decimal("5.0"),
        "source": "Australian Government 2024",
        "year": 2024,
    },
    "NZ": {
        "country_name": "New Zealand",
        "location_factor": Decimal("0.074"),  # High renewable
        "market_factor": None,
        "td_loss_percentage": Decimal("5.5"),
        "source": "MfE 2024",
        "year": 2024,
    },

    # Global default (World average)
    "GLOBAL": {
        "country_name": "Global Average",
        "location_factor": Decimal("0.436"),
        "market_factor": None,
        "td_loss_percentage": Decimal("8.0"),
        "source": "IEA 2024 World Average",
        "year": 2024,
    },
}


def get_grid_factor(country_code: str) -> dict | None:
    """Get grid emission factor for a country."""
    return GRID_EMISSION_FACTORS.get(country_code.upper()) or GRID_EMISSION_FACTORS.get("GLOBAL")


# =============================================================================
# HOTEL EMISSION FACTORS BY COUNTRY
# Source: DEFRA 2024, CRREM
# =============================================================================

HOTEL_EMISSION_FACTORS = {
    # Country -> kg CO2e per room-night
    "GB": {"country_name": "United Kingdom", "co2e_per_night": Decimal("14.6"), "source": "DEFRA 2024"},
    "US": {"country_name": "United States", "co2e_per_night": Decimal("20.2"), "source": "EPA 2024"},
    "DE": {"country_name": "Germany", "co2e_per_night": Decimal("18.5"), "source": "CRREM"},
    "FR": {"country_name": "France", "co2e_per_night": Decimal("8.5"), "source": "CRREM"},  # Low due to nuclear
    "IT": {"country_name": "Italy", "co2e_per_night": Decimal("16.8"), "source": "CRREM"},
    "ES": {"country_name": "Spain", "co2e_per_night": Decimal("12.3"), "source": "CRREM"},
    "NL": {"country_name": "Netherlands", "co2e_per_night": Decimal("17.2"), "source": "CRREM"},
    "IL": {"country_name": "Israel", "co2e_per_night": Decimal("22.5"), "source": "IEC estimate"},
    "AE": {"country_name": "UAE", "co2e_per_night": Decimal("28.0"), "source": "Dubai estimate"},
    "CN": {"country_name": "China", "co2e_per_night": Decimal("24.5"), "source": "IEA estimate"},
    "JP": {"country_name": "Japan", "co2e_per_night": Decimal("19.8"), "source": "MOE Japan"},
    "IN": {"country_name": "India", "co2e_per_night": Decimal("18.0"), "source": "BEE estimate"},
    "AU": {"country_name": "Australia", "co2e_per_night": Decimal("21.3"), "source": "DCCEEW"},
    "SG": {"country_name": "Singapore", "co2e_per_night": Decimal("17.5"), "source": "BCA"},
    "CA": {"country_name": "Canada", "co2e_per_night": Decimal("16.5"), "source": "NRCan"},

    # Global average
    "GLOBAL": {"country_name": "Global Average", "co2e_per_night": Decimal("14.6"), "source": "DEFRA default"},
}


def get_hotel_factor(country_code: str) -> Decimal:
    """Get hotel emission factor for a country (kg CO2e per night)."""
    data = HOTEL_EMISSION_FACTORS.get(country_code.upper()) or HOTEL_EMISSION_FACTORS.get("GLOBAL")
    return data["co2e_per_night"]


# =============================================================================
# REFRIGERANT GWP VALUES (IPCC AR6)
# Source: IPCC AR6 (2021)
# =============================================================================

REFRIGERANT_GWP = {
    # Refrigerant -> {gwp_ar6, gwp_ar5, type, applications}
    # GWP = 100-year Global Warming Potential

    # HFCs (most common)
    "R-134a": {"gwp_ar6": 1430, "gwp_ar5": 1300, "type": "HFC", "applications": "Vehicle AC, chillers"},
    "R-410A": {"gwp_ar6": 2088, "gwp_ar5": 1924, "type": "HFC", "applications": "HVAC, heat pumps"},
    "R-407C": {"gwp_ar6": 1774, "gwp_ar5": 1624, "type": "HFC", "applications": "HVAC retrofit"},
    "R-32": {"gwp_ar6": 675, "gwp_ar5": 677, "type": "HFC", "applications": "HVAC, newer AC units"},
    "R-404A": {"gwp_ar6": 3922, "gwp_ar5": 3943, "type": "HFC", "applications": "Commercial refrigeration"},
    "R-507A": {"gwp_ar6": 3985, "gwp_ar5": 3985, "type": "HFC", "applications": "Commercial refrigeration"},
    "R-125": {"gwp_ar6": 3500, "gwp_ar5": 3170, "type": "HFC", "applications": "Blends, fire suppression"},
    "R-143a": {"gwp_ar6": 4470, "gwp_ar5": 4800, "type": "HFC", "applications": "Blends"},
    "R-152a": {"gwp_ar6": 124, "gwp_ar5": 138, "type": "HFC", "applications": "Aerosols, some AC"},
    "R-227ea": {"gwp_ar6": 3220, "gwp_ar5": 3350, "type": "HFC", "applications": "Fire suppression, metered dose inhalers"},

    # HCFCs (being phased out)
    "R-22": {"gwp_ar6": 1810, "gwp_ar5": 1760, "type": "HCFC", "applications": "Legacy AC (phased out)", "phased_out": True},
    "R-123": {"gwp_ar6": 77, "gwp_ar5": 79, "type": "HCFC", "applications": "Chillers (phased out)", "phased_out": True},

    # HFOs (low GWP alternatives)
    "R-1234yf": {"gwp_ar6": 1, "gwp_ar5": 1, "type": "HFO", "applications": "Vehicle AC (new)"},
    "R-1234ze(E)": {"gwp_ar6": 1, "gwp_ar5": 1, "type": "HFO", "applications": "Chillers, aerosols"},
    "R-1233zd(E)": {"gwp_ar6": 1, "gwp_ar5": 1, "type": "HFO", "applications": "Centrifugal chillers"},

    # Natural refrigerants
    "R-744": {"gwp_ar6": 1, "gwp_ar5": 1, "type": "Natural", "applications": "CO2 systems, transcritical"},
    "R-717": {"gwp_ar6": 0, "gwp_ar5": 0, "type": "Natural", "applications": "Ammonia - industrial"},
    "R-290": {"gwp_ar6": 3, "gwp_ar5": 3, "type": "Natural", "applications": "Propane - small commercial"},
    "R-600a": {"gwp_ar6": 3, "gwp_ar5": 3, "type": "Natural", "applications": "Isobutane - domestic refrigerators"},

    # SF6 and other industrial gases
    "SF6": {"gwp_ar6": 23500, "gwp_ar5": 23500, "type": "Other", "applications": "Electrical switchgear"},

    # Halons (fire suppression - being phased out)
    "Halon-1211": {"gwp_ar6": 1890, "gwp_ar5": 1890, "type": "Halon", "applications": "Fire suppression (phased out)", "phased_out": True},
    "Halon-1301": {"gwp_ar6": 7140, "gwp_ar5": 7140, "type": "Halon", "applications": "Fire suppression (phased out)", "phased_out": True},
}


def get_refrigerant_gwp(refrigerant: str, ar_version: str = "ar6") -> int | None:
    """
    Get GWP value for a refrigerant.

    Args:
        refrigerant: Refrigerant name (e.g., "R-134a", "R-410A")
        ar_version: "ar6" (default, 2021) or "ar5" (2014)

    Returns:
        GWP value or None if not found
    """
    # Normalize input
    ref = refrigerant.upper().replace(" ", "")
    if not ref.startswith("R-"):
        ref = "R-" + ref

    data = REFRIGERANT_GWP.get(ref)
    if data is None:
        return None

    if ar_version.lower() == "ar5":
        return data.get("gwp_ar5")
    return data.get("gwp_ar6")


# =============================================================================
# WASTE DISPOSAL EMISSION FACTORS
# Source: DEFRA 2024, EPA WARM
# =============================================================================

WASTE_DISPOSAL_FACTORS = {
    # (waste_type, disposal_method) -> kg CO2e per kg

    # Mixed waste
    ("mixed", "landfill"): {"co2e_per_kg": Decimal("0.457"), "source": "DEFRA 2024"},
    ("mixed", "incineration"): {"co2e_per_kg": Decimal("0.021"), "source": "DEFRA 2024"},
    ("mixed", "recycling"): {"co2e_per_kg": Decimal("0.021"), "source": "DEFRA 2024"},

    # Organic waste
    ("organic", "landfill"): {"co2e_per_kg": Decimal("0.572"), "source": "DEFRA 2024"},
    ("organic", "composting"): {"co2e_per_kg": Decimal("0.010"), "source": "DEFRA 2024"},
    ("organic", "anaerobic_digestion"): {"co2e_per_kg": Decimal("-0.030"), "source": "DEFRA 2024"},  # Negative = benefit

    # Paper/cardboard
    ("paper", "landfill"): {"co2e_per_kg": Decimal("0.832"), "source": "DEFRA 2024"},
    ("paper", "recycling"): {"co2e_per_kg": Decimal("0.021"), "source": "DEFRA 2024"},
    ("paper", "incineration"): {"co2e_per_kg": Decimal("0.021"), "source": "DEFRA 2024"},

    # Plastics
    ("plastic", "landfill"): {"co2e_per_kg": Decimal("0.021"), "source": "DEFRA 2024"},
    ("plastic", "recycling"): {"co2e_per_kg": Decimal("0.021"), "source": "DEFRA 2024"},
    ("plastic", "incineration"): {"co2e_per_kg": Decimal("2.530"), "source": "DEFRA 2024"},  # High due to fossil carbon

    # Glass
    ("glass", "landfill"): {"co2e_per_kg": Decimal("0.021"), "source": "DEFRA 2024"},
    ("glass", "recycling"): {"co2e_per_kg": Decimal("0.021"), "source": "DEFRA 2024"},

    # Metals
    ("metal", "landfill"): {"co2e_per_kg": Decimal("0.021"), "source": "DEFRA 2024"},
    ("metal", "recycling"): {"co2e_per_kg": Decimal("0.021"), "source": "DEFRA 2024"},

    # E-waste
    ("ewaste", "landfill"): {"co2e_per_kg": Decimal("0.021"), "source": "DEFRA 2024"},
    ("ewaste", "recycling"): {"co2e_per_kg": Decimal("0.021"), "source": "DEFRA 2024"},

    # Construction
    ("construction", "landfill"): {"co2e_per_kg": Decimal("0.021"), "source": "DEFRA 2024"},
    ("construction", "recycling"): {"co2e_per_kg": Decimal("0.021"), "source": "DEFRA 2024"},
}


def get_waste_factor(waste_type: str, disposal_method: str) -> Decimal | None:
    """Get waste disposal emission factor (kg CO2e per kg)."""
    key = (waste_type.lower(), disposal_method.lower())
    data = WASTE_DISPOSAL_FACTORS.get(key)
    if data:
        return data["co2e_per_kg"]
    # Try mixed as fallback
    fallback = WASTE_DISPOSAL_FACTORS.get(("mixed", disposal_method.lower()))
    return fallback["co2e_per_kg"] if fallback else None


# =============================================================================
# PRICE RANGES FOR VALIDATION (Category 3.1 spend validation)
# =============================================================================

PRICE_RANGES = {
    # material_type -> {min_usd_per_kg, max_usd_per_kg, typical_usd_per_kg}

    # Raw materials
    "plastic": {"min": Decimal("0.50"), "max": Decimal("5.00"), "typical": Decimal("1.50"), "unit": "kg"},
    "steel": {"min": Decimal("0.30"), "max": Decimal("3.00"), "typical": Decimal("0.80"), "unit": "kg"},
    "aluminum": {"min": Decimal("1.50"), "max": Decimal("5.00"), "typical": Decimal("2.50"), "unit": "kg"},
    "paper": {"min": Decimal("0.20"), "max": Decimal("2.00"), "typical": Decimal("0.60"), "unit": "kg"},
    "glass": {"min": Decimal("0.10"), "max": Decimal("1.00"), "typical": Decimal("0.30"), "unit": "kg"},
    "copper": {"min": Decimal("6.00"), "max": Decimal("12.00"), "typical": Decimal("8.00"), "unit": "kg"},
    "cement": {"min": Decimal("0.05"), "max": Decimal("0.30"), "typical": Decimal("0.12"), "unit": "kg"},

    # Fuels
    "diesel": {"min": Decimal("0.80"), "max": Decimal("2.50"), "typical": Decimal("1.40"), "unit": "liter"},
    "petrol": {"min": Decimal("0.80"), "max": Decimal("2.50"), "typical": Decimal("1.50"), "unit": "liter"},
    "natural_gas": {"min": Decimal("0.02"), "max": Decimal("0.15"), "typical": Decimal("0.05"), "unit": "kWh"},
    "electricity": {"min": Decimal("0.05"), "max": Decimal("0.50"), "typical": Decimal("0.15"), "unit": "kWh"},
}


def validate_price(material_type: str, price_per_unit: Decimal) -> dict:
    """
    Validate if a price per unit is within expected range.

    Returns:
        {
            "valid": bool,
            "warning": str or None,
            "expected_range": {min, max, typical}
        }
    """
    ranges = PRICE_RANGES.get(material_type.lower())
    if not ranges:
        return {"valid": True, "warning": None, "expected_range": None}

    if price_per_unit < ranges["min"]:
        return {
            "valid": False,
            "warning": f"Price ${price_per_unit}/{ranges['unit']} is below minimum expected ${ranges['min']}/{ranges['unit']}",
            "expected_range": ranges,
        }
    if price_per_unit > ranges["max"]:
        return {
            "valid": False,
            "warning": f"Price ${price_per_unit}/{ranges['unit']} is above maximum expected ${ranges['max']}/{ranges['unit']}",
            "expected_range": ranges,
        }
    return {"valid": True, "warning": None, "expected_range": ranges}
