"""
CLIMATRIX - Fuel Prices for Spend-Based Calculations

Used to convert monetary spend to physical quantities for emission calculations.
Formula: quantity = spend_amount / price_per_unit

Sources:
- EIA (US Energy Information Administration)
- BEIS/DESNZ (UK Government)
- IEC (Israel Electric Corporation)
- IEA (International Energy Agency)
- World Bank Commodity Markets
- Industry associations (HVAC, Chemical, Steel)

STATUS: LOCKED (verified by verify_scope_1_2.py)
Total: 142 fuel prices across all regions
"""

from decimal import Decimal

# ============================================================================
# FUEL PRICES FOR SCOPE 1 CATEGORIES
# ============================================================================

FUEL_PRICES = {
    # ------------------------------------------------------------------------
    # Category 1.1: Stationary Combustion
    # ------------------------------------------------------------------------
    "natural_gas": {
        "Global": {"price": Decimal("0.04"), "currency": "USD", "unit": "kWh", "source": "IEA World Energy Outlook 2024"},
        "Global_m3": {"price": Decimal("0.38"), "currency": "USD", "unit": "m3", "source": "IEA - converted from kWh (1 m3 = ~10.55 kWh)"},
        "EU": {"price": Decimal("0.045"), "currency": "EUR", "unit": "kWh", "source": "Eurostat Natural Gas Prices 2024"},
        "UK": {"price": Decimal("0.06"), "currency": "GBP", "unit": "kWh", "source": "Ofgem Energy Price Cap 2024"},
        "US": {"price": Decimal("0.035"), "currency": "USD", "unit": "kWh", "source": "EIA Natural Gas Prices - Commercial Sector 2024"},
        "IL": {"price": Decimal("0.18"), "currency": "ILS", "unit": "kWh", "source": "Israel Natural Gas Authority 2024"},
    },
    "diesel": {
        "Global": {"price": Decimal("1.2"), "currency": "USD", "unit": "liter", "source": "IEA Global Average Diesel Price 2024"},
        "EU": {"price": Decimal("1.6"), "currency": "EUR", "unit": "liter", "source": "European Commission Weekly Oil Bulletin 2024"},
        "UK": {"price": Decimal("1.5"), "currency": "GBP", "unit": "liter", "source": "UK DESNZ Weekly Road Fuel Prices 2024"},
        "US": {"price": Decimal("1.0"), "currency": "USD", "unit": "liter", "source": "EIA Weekly Retail On-Highway Diesel Prices 2024"},
        "IL": {"price": Decimal("6.8"), "currency": "ILS", "unit": "liter", "source": "Israel Ministry of Energy - Regulated Fuel Prices 2024"},
    },
    "petrol": {
        "Global": {"price": Decimal("1.1"), "currency": "USD", "unit": "liter", "source": "IEA Global Average Gasoline Price 2024"},
        "EU": {"price": Decimal("1.7"), "currency": "EUR", "unit": "liter", "source": "European Commission Weekly Oil Bulletin 2024"},
        "UK": {"price": Decimal("1.45"), "currency": "GBP", "unit": "liter", "source": "UK DESNZ Weekly Road Fuel Prices 2024"},
        "US": {"price": Decimal("0.92"), "currency": "USD", "unit": "liter", "source": "EIA Weekly Retail Gasoline Prices 2024"},
        "IL": {"price": Decimal("6.5"), "currency": "ILS", "unit": "liter", "source": "Israel Ministry of Energy - Regulated Fuel Prices 2024"},
    },
    "lpg": {
        "Global": {"price": Decimal("0.8"), "currency": "USD", "unit": "liter", "source": "World Bank Commodity Prices 2024"},
        "UK": {"price": Decimal("0.85"), "currency": "GBP", "unit": "liter", "source": "UK DESNZ LPG Prices 2024"},
        "US": {"price": Decimal("0.75"), "currency": "USD", "unit": "liter", "source": "EIA Propane/LPG Prices 2024"},
        "IL": {"price": Decimal("4.5"), "currency": "ILS", "unit": "liter", "source": "Israel Ministry of Energy 2024"},
    },
    "fuel_oil": {
        "Global": {"price": Decimal("0.85"), "currency": "USD", "unit": "liter", "source": "EIA_2024"},
        "EU": {"price": Decimal("0.75"), "currency": "EUR", "unit": "liter", "source": "Eurostat_2024"},
        "UK": {"price": Decimal("0.72"), "currency": "GBP", "unit": "liter", "source": "BEIS_2024"},
    },
    "kerosene": {
        "Global": {"price": Decimal("1.05"), "currency": "USD", "unit": "liter", "source": "EIA_2024"},
        "EU": {"price": Decimal("0.95"), "currency": "EUR", "unit": "liter", "source": "Eurostat_2024"},
        "UK": {"price": Decimal("0.85"), "currency": "GBP", "unit": "liter", "source": "BEIS_2024"},
    },
    "heating_oil": {
        "Global": {"price": Decimal("1.0"), "currency": "USD", "unit": "liter", "source": "IEA Fuel Oil Average Price 2024"},
        "UK": {"price": Decimal("0.9"), "currency": "GBP", "unit": "liter", "source": "Boiler Juice UK Heating Oil Prices 2024"},
        "US": {"price": Decimal("1.05"), "currency": "USD", "unit": "liter", "source": "EIA Weekly Heating Oil Prices 2024"},
    },
    "coal": {
        "Global": {"price": Decimal("150"), "currency": "USD", "unit": "tonne", "source": "World Bank Coal Price Index 2024"},
    },

    # ------------------------------------------------------------------------
    # Category 1.3: Fugitive Emissions - Refrigerants
    # ------------------------------------------------------------------------
    "refrigerant_r134a": {"Global": {"price": Decimal("15"), "currency": "USD", "unit": "kg", "source": "HVAC Industry Average - R-134a Bulk Price 2024"}},
    "refrigerant_r32": {"Global": {"price": Decimal("12"), "currency": "USD", "unit": "kg", "source": "HVAC Industry Average - R-32 Bulk Price 2024"}},
    "refrigerant_r410a": {"Global": {"price": Decimal("18"), "currency": "USD", "unit": "kg", "source": "HVAC Industry Average - R-410A Bulk Price 2024"}},
    "refrigerant_r404a": {"Global": {"price": Decimal("25"), "currency": "USD", "unit": "kg", "source": "HVAC Industry Average - R-404A Bulk Price 2024 (phasedown impacts price)"}},
    "refrigerant_hfc23": {"Global": {"price": Decimal("50"), "currency": "USD", "unit": "kg", "source": "Fluorochemical Industry Prices 2024"}},
    "refrigerant_hfc125": {"Global": {"price": Decimal("25"), "currency": "USD", "unit": "kg", "source": "Chemical_Industry_Avg"}},
    "refrigerant_hfc143a": {"Global": {"price": Decimal("28"), "currency": "USD", "unit": "kg", "source": "Chemical_Industry_Avg"}},
    "refrigerant_hfc152a": {"Global": {"price": Decimal("12"), "currency": "USD", "unit": "kg", "source": "Chemical_Industry_Avg"}},
    "refrigerant_hfc227ea": {"Global": {"price": Decimal("35"), "currency": "USD", "unit": "kg", "source": "Chemical_Industry_Avg"}},
    "refrigerant_hfc236fa": {"Global": {"price": Decimal("45"), "currency": "USD", "unit": "kg", "source": "Chemical_Industry_Avg"}},
    "refrigerant_hfc245fa": {"Global": {"price": Decimal("30"), "currency": "USD", "unit": "kg", "source": "Chemical_Industry_Avg"}},
    "refrigerant_hfc365mfc": {"Global": {"price": Decimal("32"), "currency": "USD", "unit": "kg", "source": "Chemical_Industry_Avg"}},
    "refrigerant_hfc4310mee": {"Global": {"price": Decimal("40"), "currency": "USD", "unit": "kg", "source": "Chemical_Industry_Avg"}},
    "refrigerant_r407a": {"Global": {"price": Decimal("15"), "currency": "USD", "unit": "kg", "source": "HVAC_Industry_Avg"}},
    "refrigerant_r407c": {"Global": {"price": Decimal("14"), "currency": "USD", "unit": "kg", "source": "HVAC_Industry_Avg"}},
    "refrigerant_r407f": {"Global": {"price": Decimal("16"), "currency": "USD", "unit": "kg", "source": "HVAC_Industry_Avg"}},
    "refrigerant_r417a": {"Global": {"price": Decimal("18"), "currency": "USD", "unit": "kg", "source": "HVAC_Industry_Avg"}},
    "refrigerant_r422d": {"Global": {"price": Decimal("20"), "currency": "USD", "unit": "kg", "source": "HVAC_Industry_Avg"}},
    "refrigerant_r507a": {"Global": {"price": Decimal("22"), "currency": "USD", "unit": "kg", "source": "HVAC_Industry_Avg"}},
    "refrigerant_r508b": {"Global": {"price": Decimal("85"), "currency": "USD", "unit": "kg", "source": "HVAC_Industry_Avg"}},
    "refrigerant_r1234yf": {"Global": {"price": Decimal("45"), "currency": "USD", "unit": "kg", "source": "Automotive_Industry"}},
    "refrigerant_r1234ze": {"Global": {"price": Decimal("40"), "currency": "USD", "unit": "kg", "source": "HVAC_Industry_Avg"}},
    "refrigerant_r290": {"Global": {"price": Decimal("8"), "currency": "USD", "unit": "kg", "source": "Industrial_Gas_Avg"}},
    "refrigerant_r600a": {"Global": {"price": Decimal("10"), "currency": "USD", "unit": "kg", "source": "Industrial_Gas_Avg"}},
    "refrigerant_r717": {"Global": {"price": Decimal("3"), "currency": "USD", "unit": "kg", "source": "Industrial_Gas_Avg"}},
    "refrigerant_co2": {"Global": {"price": Decimal("3"), "currency": "USD", "unit": "kg", "source": "Industrial CO2 Prices 2024"}},
    "refrigerant_sf6": {"Global": {"price": Decimal("25"), "currency": "USD", "unit": "kg", "source": "Chemical_Industry_Avg"}},
    "refrigerant_nf3": {"Global": {"price": Decimal("120"), "currency": "USD", "unit": "kg", "source": "Semiconductor_Industry"}},
    "refrigerant_pfc14": {"Global": {"price": Decimal("50"), "currency": "USD", "unit": "kg", "source": "Chemical_Industry_Avg"}},
    "refrigerant_pfc116": {"Global": {"price": Decimal("55"), "currency": "USD", "unit": "kg", "source": "Chemical_Industry_Avg"}},
    "refrigerant_pfc218": {"Global": {"price": Decimal("60"), "currency": "USD", "unit": "kg", "source": "Chemical_Industry_Avg"}},
    "refrigerant_pfc318": {"Global": {"price": Decimal("65"), "currency": "USD", "unit": "kg", "source": "Chemical_Industry_Avg"}},

    # ------------------------------------------------------------------------
    # Category 1.4: Process Emissions - Industrial Materials
    # ------------------------------------------------------------------------
    "cement_production": {"Global": {"price": Decimal("120"), "currency": "USD", "unit": "tonne", "source": "World Bank Commodity Markets - Cement Price Index 2024"}},
    "clinker_production": {"Global": {"price": Decimal("100"), "currency": "USD", "unit": "tonne", "source": "Global Cement Report - Clinker Prices 2024"}},
    "quicklime_production": {"Global": {"price": Decimal("150"), "currency": "USD", "unit": "tonne", "source": "Industrial Minerals - Lime Prices 2024"}},
    "dolomitic_lime_production": {"Global": {"price": Decimal("160"), "currency": "USD", "unit": "tonne", "source": "Industrial Minerals - Dolomitic Lime Prices 2024"}},
    "iron_steel_production": {"Global": {"price": Decimal("550"), "currency": "USD", "unit": "tonne", "source": "World Steel Association - Steel Price Index 2024"}},
    "steel_eaf_production": {"Global": {"price": Decimal("600"), "currency": "USD", "unit": "tonne", "source": "World Steel Association - EAF Steel Prices 2024"}},
    "aluminum_primary_production": {"Global": {"price": Decimal("2400"), "currency": "USD", "unit": "tonne", "source": "London Metal Exchange - Aluminum Price 2024"}},
    "ammonia_production": {"Global": {"price": Decimal("450"), "currency": "USD", "unit": "tonne", "source": "World Bank - Ammonia (Gulf) Price 2024"}},
    "nitric_acid_production": {"Global": {"price": Decimal("350"), "currency": "USD", "unit": "tonne", "source": "ICIS Chemical Prices - Nitric Acid 2024"}},
    "adipic_acid_production": {"Global": {"price": Decimal("1800"), "currency": "USD", "unit": "tonne", "source": "ICIS Chemical Prices - Adipic Acid 2024"}},
    "glass_production": {"Global": {"price": Decimal("800"), "currency": "USD", "unit": "tonne", "source": "Glass Industry Association Price Index 2024"}},
    "ethylene_production": {"Global": {"price": Decimal("1100"), "currency": "USD", "unit": "tonne", "source": "ICIS Petrochemical Prices - Ethylene 2024"}},
    "hydrogen_smr_production": {"Global": {"price": Decimal("2000"), "currency": "USD", "unit": "tonne", "source": "IEA Global Hydrogen Review - SMR Hydrogen Prices 2024"}},

    # ------------------------------------------------------------------------
    # Category 2.1: Purchased Electricity - Multi-region prices
    # ------------------------------------------------------------------------
    "electricity": {
        "Global": {"price": Decimal("0.14"), "currency": "USD", "unit": "kWh", "source": "IEA Global Average Electricity Price 2024"},
        "EU": {"price": Decimal("0.22"), "currency": "EUR", "unit": "kWh", "source": "Eurostat Electricity Prices 2024"},
        "UK": {"price": Decimal("0.28"), "currency": "GBP", "unit": "kWh", "source": "Ofgem Energy Price Cap 2024"},
        "US": {"price": Decimal("0.15"), "currency": "USD", "unit": "kWh", "source": "EIA Average Retail Price of Electricity - Commercial 2024"},
        "IL": {"price": Decimal("0.58"), "currency": "ILS", "unit": "kWh", "source": "Israel Electric Corporation Tariffs 2024"},
        # Country-specific electricity prices
        "AE": {"price": Decimal("0.05"), "currency": "AED", "unit": "kWh", "source": "DEWA_UAE"},
        "AR": {"price": Decimal("0.09"), "currency": "USD", "unit": "kWh", "source": "CAMMESA_Argentina"},
        "AT": {"price": Decimal("0.12"), "currency": "EUR", "unit": "kWh", "source": "Eurostat_2024"},
        "AU": {"price": Decimal("0.32"), "currency": "AUD", "unit": "kWh", "source": "AER Australian Default Offer 2024"},
        "BR": {"price": Decimal("0.12"), "currency": "BRL", "unit": "kWh", "source": "ANEEL_Brazil"},
        "CA": {"price": Decimal("0.12"), "currency": "CAD", "unit": "kWh", "source": "Statistics Canada Electricity Prices 2024"},
        "CH": {"price": Decimal("0.23"), "currency": "CHF", "unit": "kWh", "source": "Swiss_Energy_Office"},
        "CL": {"price": Decimal("0.13"), "currency": "USD", "unit": "kWh", "source": "CNE_Chile"},
        "CN": {"price": Decimal("0.65"), "currency": "CNY", "unit": "kWh", "source": "NDRC China Electricity Prices 2024"},
        "CO": {"price": Decimal("0.15"), "currency": "USD", "unit": "kWh", "source": "XM_Colombia"},
        "CZ": {"price": Decimal("0.25"), "currency": "EUR", "unit": "kWh", "source": "Eurostat_2024"},
        "DE": {"price": Decimal("0.35"), "currency": "EUR", "unit": "kWh", "source": "BDEW German Electricity Prices 2024"},
        "DK": {"price": Decimal("0.35"), "currency": "EUR", "unit": "kWh", "source": "Eurostat_2024"},
        "EG": {"price": Decimal("0.03"), "currency": "EGP", "unit": "kWh", "source": "EEHC_Egypt"},
        "ES": {"price": Decimal("0.24"), "currency": "EUR", "unit": "kWh", "source": "CNMC Spanish Electricity Prices 2024"},
        "FI": {"price": Decimal("0.08"), "currency": "EUR", "unit": "kWh", "source": "Eurostat_2024"},
        "FR": {"price": Decimal("0.21"), "currency": "EUR", "unit": "kWh", "source": "CRE French Electricity Prices 2024"},
        "GR": {"price": Decimal("0.18"), "currency": "EUR", "unit": "kWh", "source": "Eurostat_2024"},
        "HK": {"price": Decimal("0.15"), "currency": "USD", "unit": "kWh", "source": "CLP_HK"},
        "HU": {"price": Decimal("0.13"), "currency": "EUR", "unit": "kWh", "source": "Eurostat_2024"},
        "ID": {"price": Decimal("0.10"), "currency": "USD", "unit": "kWh", "source": "PLN_Indonesia"},
        "IE": {"price": Decimal("0.22"), "currency": "EUR", "unit": "kWh", "source": "Eurostat_2024"},
        "IN": {"price": Decimal("8.5"), "currency": "INR", "unit": "kWh", "source": "CERC India Electricity Tariffs 2024"},
        "IT": {"price": Decimal("0.29"), "currency": "EUR", "unit": "kWh", "source": "ARERA Italian Electricity Prices 2024"},
        "JP": {"price": Decimal("28"), "currency": "JPY", "unit": "kWh", "source": "METI Japan Electricity Prices 2024"},
        "KE": {"price": Decimal("0.15"), "currency": "KES", "unit": "kWh", "source": "KPLC_Kenya"},
        "KR": {"price": Decimal("120"), "currency": "KRW", "unit": "kWh", "source": "KEPCO South Korea Electricity Tariffs 2024"},
        "MX": {"price": Decimal("0.08"), "currency": "USD", "unit": "kWh", "source": "CFE_Mexico"},
        "MY": {"price": Decimal("0.08"), "currency": "MYR", "unit": "kWh", "source": "TNB_Malaysia"},
        "NG": {"price": Decimal("0.06"), "currency": "NGN", "unit": "kWh", "source": "NERC_Nigeria"},
        "NL": {"price": Decimal("0.30"), "currency": "EUR", "unit": "kWh", "source": "ACM Dutch Electricity Prices 2024"},
        "NO": {"price": Decimal("0.06"), "currency": "EUR", "unit": "kWh", "source": "Eurostat_2024"},
        "NZ": {"price": Decimal("0.22"), "currency": "NZD", "unit": "kWh", "source": "MBIE_NZ"},
        "PH": {"price": Decimal("0.12"), "currency": "PHP", "unit": "kWh", "source": "Meralco_Philippines"},
        "PL": {"price": Decimal("0.18"), "currency": "EUR", "unit": "kWh", "source": "URE Polish Electricity Prices 2024"},
        "PT": {"price": Decimal("0.17"), "currency": "EUR", "unit": "kWh", "source": "Eurostat_2024"},
        "RO": {"price": Decimal("0.14"), "currency": "EUR", "unit": "kWh", "source": "Eurostat_2024"},
        "RU": {"price": Decimal("0.04"), "currency": "RUB", "unit": "kWh", "source": "Rosseti_Russia"},
        "SA": {"price": Decimal("0.05"), "currency": "SAR", "unit": "kWh", "source": "SEC_Saudi"},
        "SE": {"price": Decimal("0.09"), "currency": "EUR", "unit": "kWh", "source": "Eurostat_2024"},
        "SG": {"price": Decimal("0.28"), "currency": "SGD", "unit": "kWh", "source": "EMA Singapore Electricity Tariffs 2024"},
        "TH": {"price": Decimal("0.12"), "currency": "THB", "unit": "kWh", "source": "EGAT_Thailand"},
        "TR": {"price": Decimal("0.09"), "currency": "TRY", "unit": "kWh", "source": "EPDK_Turkey"},
        "TW": {"price": Decimal("0.08"), "currency": "TWD", "unit": "kWh", "source": "Taipower"},
        "US-CA": {"price": Decimal("0.22"), "currency": "USD", "unit": "kWh", "source": "CPUC_California"},
        "US-MW": {"price": Decimal("0.11"), "currency": "USD", "unit": "kWh", "source": "MISO_Midwest"},
        "US-NY": {"price": Decimal("0.18"), "currency": "USD", "unit": "kWh", "source": "NYISO"},
        "US-TX": {"price": Decimal("0.12"), "currency": "USD", "unit": "kWh", "source": "ERCOT_Texas"},
        "VN": {"price": Decimal("0.08"), "currency": "VND", "unit": "kWh", "source": "EVN_Vietnam"},
        "ZA": {"price": Decimal("0.12"), "currency": "ZAR", "unit": "kWh", "source": "Eskom_SA"},
    },

    # ------------------------------------------------------------------------
    # Category 2.2: Purchased Heat/Steam
    # ------------------------------------------------------------------------
    "district_heating": {
        "Global": {"price": Decimal("0.08"), "currency": "USD", "unit": "kWh", "source": "IEA_District_Heat"},
        "EU": {"price": Decimal("0.07"), "currency": "EUR", "unit": "kWh", "source": "Euroheat_Power"},
        "UK": {"price": Decimal("0.06"), "currency": "GBP", "unit": "kWh", "source": "BEIS_2024"},
    },
    "steam": {
        "Global": {"price": Decimal("0.05"), "currency": "USD", "unit": "kWh", "source": "Industrial_Avg"},
        "EU": {"price": Decimal("0.045"), "currency": "EUR", "unit": "kWh", "source": "Industrial_Avg"},
        "UK": {"price": Decimal("0.04"), "currency": "GBP", "unit": "kWh", "source": "Industrial_Avg"},
    },

    # ------------------------------------------------------------------------
    # Category 2.3: Purchased Cooling
    # ------------------------------------------------------------------------
    "chilled_water": {
        "Global": {"price": Decimal("0.12"), "currency": "USD", "unit": "kWh", "source": "District_Cooling_Assoc"},
        "EU": {"price": Decimal("0.10"), "currency": "EUR", "unit": "kWh", "source": "District_Cooling_Assoc"},
    },
    "district_cooling": {
        "Global": {"price": Decimal("0.15"), "currency": "USD", "unit": "kWh", "source": "District_Cooling_Assoc"},
        "EU": {"price": Decimal("0.12"), "currency": "EUR", "unit": "kWh", "source": "District_Cooling_Assoc"},
        "AE": {"price": Decimal("0.08"), "currency": "AED", "unit": "kWh", "source": "Empower_Dubai"},
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_fuel_price(fuel_type: str, region: str = "Global") -> dict:
    """
    Get fuel price for a specific fuel type and region.
    Falls back to Global if regional price not available.
    """
    if fuel_type not in FUEL_PRICES:
        return None

    prices = FUEL_PRICES[fuel_type]

    # Direct lookup (works for refrigerants and materials with only Global)
    if "Global" in prices and not isinstance(prices.get("Global"), dict):
        # Single price entry
        return prices

    # Multi-region lookup
    if region in prices:
        return prices[region]

    # Fallback to Global
    if "Global" in prices:
        return prices["Global"]

    return None


def list_available_regions(fuel_type: str) -> list:
    """List all available regions for a fuel type."""
    if fuel_type not in FUEL_PRICES:
        return []

    prices = FUEL_PRICES[fuel_type]
    if isinstance(prices, dict) and "price" in prices:
        return ["Global"]
    return list(prices.keys())


def convert_spend_to_quantity(fuel_type: str, spend_amount: Decimal, region: str = "Global") -> tuple:
    """
    Convert spend amount to physical quantity using fuel prices.
    Returns (quantity, unit, price_used) or (None, None, None) if not found.
    """
    price_info = get_fuel_price(fuel_type, region)
    if not price_info:
        return None, None, None

    price = price_info["price"]
    unit = price_info["unit"]

    quantity = spend_amount / price
    return quantity, unit, price_info


def get_all_prices_flat() -> list:
    """Get all fuel prices as a flat list for database seeding."""
    result = []
    for fuel_type, prices in FUEL_PRICES.items():
        # Check if it's a single price or multi-region
        if isinstance(prices, dict) and "price" in prices:
            # Single price entry (some refrigerants/materials)
            result.append({
                "fuel_type": fuel_type,
                "region": "Global",
                **prices
            })
        else:
            # Multi-region prices
            for region, price_info in prices.items():
                result.append({
                    "fuel_type": fuel_type,
                    "region": region,
                    **price_info
                })
    return result
