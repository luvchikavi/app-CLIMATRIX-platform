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
        "location_factor": Decimal("0.377"),
        "market_factor": Decimal("0.453"),
        "td_loss_percentage": Decimal("4.5"),
        "source": "EEA 2024",
        "year": 2024,
    },
    "FR": {
        "country_name": "France",
        "location_factor": Decimal("0.056"),
        "market_factor": Decimal("0.069"),
        "td_loss_percentage": Decimal("6.0"),
        "source": "EEA 2024",
        "year": 2024,
    },
    "ES": {
        "country_name": "Spain",
        "location_factor": Decimal("0.186"),
        "market_factor": Decimal("0.316"),
        "td_loss_percentage": Decimal("9.0"),
        "source": "EEA 2024",
        "year": 2024,
    },
    "IT": {
        "country_name": "Italy",
        "location_factor": Decimal("0.315"),
        "market_factor": Decimal("0.457"),
        "td_loss_percentage": Decimal("6.5"),
        "source": "EEA 2024",
        "year": 2024,
    },
    "NL": {
        "country_name": "Netherlands",
        "location_factor": Decimal("0.312"),
        "market_factor": Decimal("0.477"),
        "td_loss_percentage": Decimal("4.0"),
        "source": "EEA 2024",
        "year": 2024,
    },
    "PL": {
        "country_name": "Poland",
        "location_factor": Decimal("0.635"),
        "market_factor": Decimal("0.789"),
        "td_loss_percentage": Decimal("7.5"),
        "source": "EEA 2024",
        "year": 2024,
    },
    # Additional EU countries (EEA 2024)
    "AT": {"country_name": "Austria", "location_factor": Decimal("0.084"), "market_factor": Decimal("0.227"), "td_loss_percentage": Decimal("5.0"), "source": "EEA 2024", "year": 2024},
    "BE": {"country_name": "Belgium", "location_factor": Decimal("0.137"), "market_factor": Decimal("0.260"), "td_loss_percentage": Decimal("5.0"), "source": "EEA 2024", "year": 2024},
    "BG": {"country_name": "Bulgaria", "location_factor": Decimal("0.533"), "market_factor": Decimal("0.533"), "td_loss_percentage": Decimal("9.0"), "source": "EEA 2024", "year": 2024},
    "HR": {"country_name": "Croatia", "location_factor": Decimal("0.271"), "market_factor": Decimal("0.271"), "td_loss_percentage": Decimal("7.0"), "source": "EEA 2024", "year": 2024},
    "CY": {"country_name": "Cyprus", "location_factor": Decimal("0.700"), "market_factor": Decimal("0.700"), "td_loss_percentage": Decimal("4.0"), "source": "EEA 2024", "year": 2024},
    "CZ": {"country_name": "Czech Republic", "location_factor": Decimal("0.395"), "market_factor": Decimal("0.561"), "td_loss_percentage": Decimal("6.0"), "source": "EEA 2024", "year": 2024},
    "DK": {"country_name": "Denmark", "location_factor": Decimal("0.116"), "market_factor": Decimal("0.247"), "td_loss_percentage": Decimal("5.0"), "source": "EEA 2024", "year": 2024},
    "EE": {"country_name": "Estonia", "location_factor": Decimal("0.722"), "market_factor": Decimal("0.722"), "td_loss_percentage": Decimal("6.0"), "source": "EEA 2024", "year": 2024},
    "FI": {"country_name": "Finland", "location_factor": Decimal("0.073"), "market_factor": Decimal("0.170"), "td_loss_percentage": Decimal("3.5"), "source": "EEA 2024", "year": 2024},
    "GR": {"country_name": "Greece", "location_factor": Decimal("0.337"), "market_factor": Decimal("0.481"), "td_loss_percentage": Decimal("7.0"), "source": "EEA 2024", "year": 2024},
    "HU": {"country_name": "Hungary", "location_factor": Decimal("0.218"), "market_factor": Decimal("0.311"), "td_loss_percentage": Decimal("8.0"), "source": "EEA 2024", "year": 2024},
    "IE": {"country_name": "Ireland", "location_factor": Decimal("0.272"), "market_factor": Decimal("0.432"), "td_loss_percentage": Decimal("8.0"), "source": "EEA 2024", "year": 2024},
    "LV": {"country_name": "Latvia", "location_factor": Decimal("0.161"), "market_factor": Decimal("0.161"), "td_loss_percentage": Decimal("6.0"), "source": "EEA 2024", "year": 2024},
    "LT": {"country_name": "Lithuania", "location_factor": Decimal("0.187"), "market_factor": Decimal("0.218"), "td_loss_percentage": Decimal("6.0"), "source": "EEA 2024", "year": 2024},
    "LU": {"country_name": "Luxembourg", "location_factor": Decimal("0.137"), "market_factor": Decimal("0.291"), "td_loss_percentage": Decimal("3.0"), "source": "EEA 2024", "year": 2024},
    "MT": {"country_name": "Malta", "location_factor": Decimal("0.479"), "market_factor": Decimal("0.499"), "td_loss_percentage": Decimal("4.0"), "source": "EEA 2024", "year": 2024},
    "NO": {"country_name": "Norway", "location_factor": Decimal("0.008"), "market_factor": Decimal("0.420"), "td_loss_percentage": Decimal("6.0"), "source": "EEA 2024", "year": 2024},
    "PT": {"country_name": "Portugal", "location_factor": Decimal("0.175"), "market_factor": Decimal("0.296"), "td_loss_percentage": Decimal("8.0"), "source": "EEA 2024", "year": 2024},
    "RO": {"country_name": "Romania", "location_factor": Decimal("0.258"), "market_factor": Decimal("0.363"), "td_loss_percentage": Decimal("10.0"), "source": "EEA 2024", "year": 2024},
    "SE": {"country_name": "Sweden", "location_factor": Decimal("0.009"), "market_factor": Decimal("0.036"), "td_loss_percentage": Decimal("6.0"), "source": "EEA 2024", "year": 2024},
    "SK": {"country_name": "Slovakia", "location_factor": Decimal("0.113"), "market_factor": Decimal("0.164"), "td_loss_percentage": Decimal("5.0"), "source": "EEA 2024", "year": 2024},
    "SI": {"country_name": "Slovenia", "location_factor": Decimal("0.234"), "market_factor": Decimal("0.367"), "td_loss_percentage": Decimal("5.0"), "source": "EEA 2024", "year": 2024},

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
# ELECTRICITY WTT & T&D EMISSION FACTORS
# Source: UK DESNZ/DEFRA GHG Conversion Factors 2024 (overseas electricity)
# WTT = Well-to-Tank (upstream fuel extraction/processing for electricity generation)
# T&D = Transmission & Distribution losses (electricity lost in grid delivery)
# T&D WTT = WTT emissions for the electricity lost in T&D
# All values in kg CO2e per kWh consumed
# =============================================================================

ELECTRICITY_WTT_TD_FACTORS = {
    # Source: UK DESNZ/DEFRA GHG Conversion Factors 2024 (overseas electricity)
    # WTT = Well-to-Tank (upstream fuel extraction/processing for electricity generation)
    # T&D = Transmission & Distribution losses (electricity lost in grid delivery)
    # T&D WTT = WTT emissions for the electricity lost in T&D
    # All values in kg CO2e per kWh consumed

    "UK": {"wtt_generation": Decimal("0.04625"), "td_loss": Decimal("0.01830"), "td_wtt": Decimal("0.00400"), "source": "DESNZ_2024", "year": 2024},
    "DE": {"wtt_generation": Decimal("0.10427"), "td_loss": Decimal("0.01800"), "td_wtt": Decimal("0.00542"), "source": "BEIS_2021", "year": 2021},
    "FR": {"wtt_generation": Decimal("0.00765"), "td_loss": Decimal("0.00400"), "td_wtt": Decimal("0.00067"), "source": "BEIS_2021", "year": 2021},
    "IL": {"wtt_generation": Decimal("0.09500"), "td_loss": Decimal("0.02000"), "td_wtt": Decimal("0.00701"), "source": "BEIS_2021", "year": 2021},
    "IT": {"wtt_generation": Decimal("0.06800"), "td_loss": Decimal("0.01700"), "td_wtt": Decimal("0.00537"), "source": "BEIS_2021", "year": 2021},
    "NL": {"wtt_generation": Decimal("0.07200"), "td_loss": Decimal("0.01200"), "td_wtt": Decimal("0.00389"), "source": "BEIS_2021", "year": 2021},
    "PL": {"wtt_generation": Decimal("0.14500"), "td_loss": Decimal("0.02200"), "td_wtt": Decimal("0.01082"), "source": "BEIS_2021", "year": 2021},
    "ES": {"wtt_generation": Decimal("0.05100"), "td_loss": Decimal("0.01500"), "td_wtt": Decimal("0.00480"), "source": "BEIS_2021", "year": 2021},
    "US": {"wtt_generation": Decimal("0.08900"), "td_loss": Decimal("0.02100"), "td_wtt": Decimal("0.00650"), "source": "BEIS_2021", "year": 2021},
    "CN": {"wtt_generation": Decimal("0.13500"), "td_loss": Decimal("0.02400"), "td_wtt": Decimal("0.00912"), "source": "BEIS_2021", "year": 2021},
    "IN": {"wtt_generation": Decimal("0.16748"), "td_loss": Decimal("0.04200"), "td_wtt": Decimal("0.01100"), "source": "BEIS_2021", "year": 2021},
    "AU": {"wtt_generation": Decimal("0.17557"), "td_loss": Decimal("0.02000"), "td_wtt": Decimal("0.00800"), "source": "BEIS_2021", "year": 2021},
    "JP": {"wtt_generation": Decimal("0.10200"), "td_loss": Decimal("0.01800"), "td_wtt": Decimal("0.00580"), "source": "BEIS_2021", "year": 2021},
    "KR": {"wtt_generation": Decimal("0.09800"), "td_loss": Decimal("0.01500"), "td_wtt": Decimal("0.00520"), "source": "BEIS_2021", "year": 2021},
    "CA": {"wtt_generation": Decimal("0.03200"), "td_loss": Decimal("0.01300"), "td_wtt": Decimal("0.00213"), "source": "BEIS_2021", "year": 2021},
    "BR": {"wtt_generation": Decimal("0.01800"), "td_loss": Decimal("0.01600"), "td_wtt": Decimal("0.00150"), "source": "BEIS_2021", "year": 2021},
    "EU": {"wtt_generation": Decimal("0.07500"), "td_loss": Decimal("0.01500"), "td_wtt": Decimal("0.00564"), "source": "BEIS_2021", "year": 2021},
    "Global": {"wtt_generation": Decimal("0.10000"), "td_loss": Decimal("0.02000"), "td_wtt": Decimal("0.00700"), "source": "BEIS_2021", "year": 2021},
}


def get_wtt_td_factors(country_code: str) -> dict | None:
    """Get WTT and T&D factors for a country. Falls back to EU average, then Global."""
    factors = ELECTRICITY_WTT_TD_FACTORS.get(country_code.upper())
    if factors:
        return factors
    # Try EU fallback for European countries
    eu_countries = {"AT", "BE", "BG", "CY", "CZ", "DK", "EE", "FI", "GR", "HR", "HU", "IE", "LT", "LU", "LV", "MT", "NO", "PT", "RO", "SE", "SI", "SK"}
    if country_code.upper() in eu_countries:
        return ELECTRICITY_WTT_TD_FACTORS.get("EU")
    return ELECTRICITY_WTT_TD_FACTORS.get("Global")


# =============================================================================
# AIB RESIDUAL MIX — EU Market-Based Factors
# Source: AIB (Association of Issuing Bodies) European Residual Mixes 2024
# Used for Scope 2 market-based method in EU countries
# =============================================================================

AIB_RESIDUAL_MIX = {
    # Country code -> kg CO2e per kWh (residual mix after GO/certificates removed)
    "AT": {"co2e_per_kwh": Decimal("0.227"), "country_name": "Austria", "year": 2024},
    "BE": {"co2e_per_kwh": Decimal("0.260"), "country_name": "Belgium", "year": 2024},
    "BG": {"co2e_per_kwh": Decimal("0.533"), "country_name": "Bulgaria", "year": 2024},
    "HR": {"co2e_per_kwh": Decimal("0.271"), "country_name": "Croatia", "year": 2024},
    "CY": {"co2e_per_kwh": Decimal("0.700"), "country_name": "Cyprus", "year": 2024},
    "CZ": {"co2e_per_kwh": Decimal("0.561"), "country_name": "Czech Republic", "year": 2024},
    "DK": {"co2e_per_kwh": Decimal("0.247"), "country_name": "Denmark", "year": 2024},
    "EE": {"co2e_per_kwh": Decimal("0.722"), "country_name": "Estonia", "year": 2024},
    "FI": {"co2e_per_kwh": Decimal("0.170"), "country_name": "Finland", "year": 2024},
    "FR": {"co2e_per_kwh": Decimal("0.069"), "country_name": "France", "year": 2024},
    "DE": {"co2e_per_kwh": Decimal("0.453"), "country_name": "Germany", "year": 2024},
    "GR": {"co2e_per_kwh": Decimal("0.481"), "country_name": "Greece", "year": 2024},
    "HU": {"co2e_per_kwh": Decimal("0.311"), "country_name": "Hungary", "year": 2024},
    "IE": {"co2e_per_kwh": Decimal("0.432"), "country_name": "Ireland", "year": 2024},
    "IT": {"co2e_per_kwh": Decimal("0.457"), "country_name": "Italy", "year": 2024},
    "LV": {"co2e_per_kwh": Decimal("0.161"), "country_name": "Latvia", "year": 2024},
    "LT": {"co2e_per_kwh": Decimal("0.218"), "country_name": "Lithuania", "year": 2024},
    "LU": {"co2e_per_kwh": Decimal("0.291"), "country_name": "Luxembourg", "year": 2024},
    "MT": {"co2e_per_kwh": Decimal("0.499"), "country_name": "Malta", "year": 2024},
    "NL": {"co2e_per_kwh": Decimal("0.477"), "country_name": "Netherlands", "year": 2024},
    "NO": {"co2e_per_kwh": Decimal("0.420"), "country_name": "Norway", "year": 2024},
    "PL": {"co2e_per_kwh": Decimal("0.789"), "country_name": "Poland", "year": 2024},
    "PT": {"co2e_per_kwh": Decimal("0.296"), "country_name": "Portugal", "year": 2024},
    "RO": {"co2e_per_kwh": Decimal("0.363"), "country_name": "Romania", "year": 2024},
    "SK": {"co2e_per_kwh": Decimal("0.164"), "country_name": "Slovakia", "year": 2024},
    "SI": {"co2e_per_kwh": Decimal("0.367"), "country_name": "Slovenia", "year": 2024},
    "ES": {"co2e_per_kwh": Decimal("0.316"), "country_name": "Spain", "year": 2024},
    "SE": {"co2e_per_kwh": Decimal("0.036"), "country_name": "Sweden", "year": 2024},
    "CH": {"co2e_per_kwh": Decimal("0.128"), "country_name": "Switzerland", "year": 2024},
    "GB": {"co2e_per_kwh": Decimal("0.312"), "country_name": "United Kingdom", "year": 2024},
    # EU-27 average residual mix (fallback)
    "EU": {"co2e_per_kwh": Decimal("0.453"), "country_name": "EU-27 Average", "year": 2024},
}


def get_aib_residual_mix(country_code: str) -> Decimal | None:
    """Get AIB residual mix factor for a country (market-based Scope 2)."""
    data = AIB_RESIDUAL_MIX.get(country_code.upper())
    if data:
        return data["co2e_per_kwh"]
    # Fall back to EU average for unlisted EU countries
    eu_data = AIB_RESIDUAL_MIX.get("EU")
    return eu_data["co2e_per_kwh"] if eu_data else None


# =============================================================================
# GREEN-E RESIDUAL MIX — US Market-Based Factors
# Source: Green-e Energy Residual Mix (2024)
# Used for Scope 2 market-based method in US states/regions
# =============================================================================

GREENE_RESIDUAL_MIX = {
    # eGRID subregion code -> kg CO2e per kWh (residual after RECs removed)
    "CAMX": {"co2e_per_kwh": Decimal("0.282"), "region_name": "WECC California", "year": 2024},
    "ERCT": {"co2e_per_kwh": Decimal("0.415"), "region_name": "ERCOT Texas", "year": 2024},
    "FRCC": {"co2e_per_kwh": Decimal("0.422"), "region_name": "FRCC Florida", "year": 2024},
    "MROE": {"co2e_per_kwh": Decimal("0.612"), "region_name": "MRO East", "year": 2024},
    "MROW": {"co2e_per_kwh": Decimal("0.528"), "region_name": "MRO West", "year": 2024},
    "NEWE": {"co2e_per_kwh": Decimal("0.251"), "region_name": "NPCC New England", "year": 2024},
    "NWPP": {"co2e_per_kwh": Decimal("0.175"), "region_name": "WECC Northwest", "year": 2024},
    "NYCW": {"co2e_per_kwh": Decimal("0.263"), "region_name": "NPCC NYC/Westchester", "year": 2024},
    "NYLI": {"co2e_per_kwh": Decimal("0.468"), "region_name": "NPCC Long Island", "year": 2024},
    "NYUP": {"co2e_per_kwh": Decimal("0.112"), "region_name": "NPCC Upstate NY", "year": 2024},
    "RFCE": {"co2e_per_kwh": Decimal("0.341"), "region_name": "RFC East", "year": 2024},
    "RFCM": {"co2e_per_kwh": Decimal("0.492"), "region_name": "RFC Michigan", "year": 2024},
    "RFCW": {"co2e_per_kwh": Decimal("0.546"), "region_name": "RFC West", "year": 2024},
    "RMPA": {"co2e_per_kwh": Decimal("0.578"), "region_name": "WECC Rockies", "year": 2024},
    "SPNO": {"co2e_per_kwh": Decimal("0.541"), "region_name": "SPP North", "year": 2024},
    "SPSO": {"co2e_per_kwh": Decimal("0.498"), "region_name": "SPP South", "year": 2024},
    "SRMV": {"co2e_per_kwh": Decimal("0.398"), "region_name": "SERC Mississippi Valley", "year": 2024},
    "SRMW": {"co2e_per_kwh": Decimal("0.672"), "region_name": "SERC Midwest", "year": 2024},
    "SRSO": {"co2e_per_kwh": Decimal("0.425"), "region_name": "SERC South", "year": 2024},
    "SRTV": {"co2e_per_kwh": Decimal("0.420"), "region_name": "SERC Tennessee Valley", "year": 2024},
    "SRVC": {"co2e_per_kwh": Decimal("0.385"), "region_name": "SERC Virginia/Carolina", "year": 2024},
    "AZNM": {"co2e_per_kwh": Decimal("0.392"), "region_name": "WECC Southwest", "year": 2024},
    # US national average residual (fallback)
    "US": {"co2e_per_kwh": Decimal("0.429"), "region_name": "US National Average", "year": 2024},
}


def get_greene_residual_mix(subregion_or_state: str) -> Decimal | None:
    """Get Green-e residual mix factor (market-based Scope 2 for US)."""
    data = GREENE_RESIDUAL_MIX.get(subregion_or_state.upper())
    if data:
        return data["co2e_per_kwh"]
    # Fall back to US national average
    us_data = GREENE_RESIDUAL_MIX.get("US")
    return us_data["co2e_per_kwh"] if us_data else None


# =============================================================================
# iREC COUNTRY AVERAGES — Other Countries Market-Based
# Source: iREC Standard, various national registries
# Used as fallback market-based factor for non-EU, non-US countries
# =============================================================================

IREC_RESIDUAL_MIX = {
    # Country code -> kg CO2e per kWh
    # For countries without formal residual mix, use grid average as proxy
    "IL": {"co2e_per_kwh": Decimal("0.527"), "country_name": "Israel", "year": 2024, "notes": "Grid average (no formal iREC market)"},
    "AE": {"co2e_per_kwh": Decimal("0.456"), "country_name": "UAE", "year": 2024},
    "SA": {"co2e_per_kwh": Decimal("0.590"), "country_name": "Saudi Arabia", "year": 2024},
    "CN": {"co2e_per_kwh": Decimal("0.555"), "country_name": "China", "year": 2024},
    "IN": {"co2e_per_kwh": Decimal("0.708"), "country_name": "India", "year": 2024},
    "JP": {"co2e_per_kwh": Decimal("0.453"), "country_name": "Japan", "year": 2024},
    "KR": {"co2e_per_kwh": Decimal("0.417"), "country_name": "South Korea", "year": 2024},
    "AU": {"co2e_per_kwh": Decimal("0.656"), "country_name": "Australia", "year": 2024},
    "BR": {"co2e_per_kwh": Decimal("0.074"), "country_name": "Brazil", "year": 2024},
    "ZA": {"co2e_per_kwh": Decimal("0.928"), "country_name": "South Africa", "year": 2024},
    "SG": {"co2e_per_kwh": Decimal("0.408"), "country_name": "Singapore", "year": 2024},
    "TH": {"co2e_per_kwh": Decimal("0.470"), "country_name": "Thailand", "year": 2024},
    "TR": {"co2e_per_kwh": Decimal("0.378"), "country_name": "Turkey", "year": 2024},
}


def get_irec_factor(country_code: str) -> Decimal | None:
    """Get iREC/national average factor for market-based Scope 2."""
    data = IREC_RESIDUAL_MIX.get(country_code.upper())
    if data:
        return data["co2e_per_kwh"]
    return None


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
