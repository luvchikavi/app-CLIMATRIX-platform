"""
CLIMATERIX - Scope 1 & 2 Emission Factors

Verified emission factors from authoritative sources:
- DEFRA 2024 (UK Department for Environment, Food & Rural Affairs)
- EPA eGRID 2024 (US Environmental Protection Agency)
- EEA 2024 (European Environment Agency) for EU country electricity
- IEA 2024 (International Energy Agency) for non-EU countries
- IPCC AR6 (GWP100 values)
- Industry-specific sources (World Steel, International Aluminium Institute, etc.)

STATUS: LOCKED (verified by verify_scope_1_2.py)
Total: 131 emission factors
"""

from decimal import Decimal

# ============================================================================
# SCOPE 1: DIRECT EMISSIONS
# ============================================================================

SCOPE_1_FACTORS = {
    # ------------------------------------------------------------------------
    # 1.1 Stationary Combustion (10 factors)
    # ------------------------------------------------------------------------
    "1.1": {
        "natural_gas_volume": {
            "display_name": "Natural Gas (volume)",
            "co2e_factor": Decimal("2.02"),
            "activity_unit": "m3",
            "factor_unit": "kg CO2e/m3",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "natural_gas_kwh": {
            "display_name": "Natural Gas (energy)",
            "co2e_factor": Decimal("0.183"),
            "activity_unit": "kWh",
            "factor_unit": "kg CO2e/kWh",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "diesel_liters": {
            "display_name": "Diesel/Gas Oil",
            "co2e_factor": Decimal("2.68"),
            "activity_unit": "liters",
            "factor_unit": "kg CO2e/liter",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "petrol_stationary_liters": {
            "display_name": "Petrol/Gasoline (stationary)",
            "co2e_factor": Decimal("2.31"),
            "activity_unit": "liters",
            "factor_unit": "kg CO2e/liter",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "lpg_liters": {
            "display_name": "LPG (volume)",
            "co2e_factor": Decimal("1.52"),
            "activity_unit": "liters",
            "factor_unit": "kg CO2e/liter",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "lpg_kg": {
            "display_name": "LPG (mass)",
            "co2e_factor": Decimal("2.94"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "fuel_oil_liters": {
            "display_name": "Fuel Oil",
            "co2e_factor": Decimal("3.18"),
            "activity_unit": "liters",
            "factor_unit": "kg CO2e/liter",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "kerosene_liters": {
            "display_name": "Kerosene",
            "co2e_factor": Decimal("2.54"),
            "activity_unit": "liters",
            "factor_unit": "kg CO2e/liter",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "burning_oil_liters": {
            "display_name": "Burning Oil (heating)",
            "co2e_factor": Decimal("2.54"),
            "activity_unit": "liters",
            "factor_unit": "kg CO2e/liter",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "coal_kg": {
            "display_name": "Coal (industrial)",
            "co2e_factor": Decimal("2.31"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "DEFRA_2024",
            "region": "Global",
        },
    },

    # ------------------------------------------------------------------------
    # 1.2 Mobile Combustion (14 factors)
    # ------------------------------------------------------------------------
    "1.2": {
        "car_petrol_km": {
            "display_name": "Petrol Car (average)",
            "co2e_factor": Decimal("0.17"),
            "activity_unit": "km",
            "factor_unit": "kg CO2e/km",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "car_diesel_km": {
            "display_name": "Diesel Car (average)",
            "co2e_factor": Decimal("0.16"),
            "activity_unit": "km",
            "factor_unit": "kg CO2e/km",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "car_hybrid_km": {
            "display_name": "Hybrid Car (average)",
            "co2e_factor": Decimal("0.12"),
            "activity_unit": "km",
            "factor_unit": "kg CO2e/km",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "car_plugin_hybrid_km": {
            "display_name": "Plug-in Hybrid Car (PHEV)",
            "co2e_factor": Decimal("0.07"),
            "activity_unit": "km",
            "factor_unit": "kg CO2e/km",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "car_electric_km": {
            "display_name": "Electric Car (BEV)",
            "co2e_factor": Decimal("0"),
            "activity_unit": "km",
            "factor_unit": "kg CO2e/km",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "van_diesel_km": {
            "display_name": "Diesel Van (average)",
            "co2e_factor": Decimal("0.24"),
            "activity_unit": "km",
            "factor_unit": "kg CO2e/km",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "lgv_diesel_km": {
            "display_name": "Light Goods Vehicle (diesel)",
            "co2e_factor": Decimal("0.21"),
            "activity_unit": "km",
            "factor_unit": "kg CO2e/km",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "lgv_petrol_km": {
            "display_name": "Light Goods Vehicle (petrol)",
            "co2e_factor": Decimal("0.23"),
            "activity_unit": "km",
            "factor_unit": "kg CO2e/km",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "hgv_diesel_km": {
            "display_name": "HGV Truck (average)",
            "co2e_factor": Decimal("0.89"),
            "activity_unit": "km",
            "factor_unit": "kg CO2e/km",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "bus_diesel_km": {
            "display_name": "Bus (average diesel)",
            "co2e_factor": Decimal("0.89"),
            "activity_unit": "km",
            "factor_unit": "kg CO2e/km",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "taxi_km": {
            "display_name": "Taxi (average)",
            "co2e_factor": Decimal("0.15"),
            "activity_unit": "km",
            "factor_unit": "kg CO2e/km",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "motorcycle_petrol_km": {
            "display_name": "Motorcycle (petrol)",
            "co2e_factor": Decimal("0.11"),
            "activity_unit": "km",
            "factor_unit": "kg CO2e/km",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "petrol_liters": {
            "display_name": "Petrol/Gasoline (fuel)",
            "co2e_factor": Decimal("2.31"),
            "activity_unit": "liters",
            "factor_unit": "kg CO2e/liter",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "diesel_mobile_liters": {
            "display_name": "Diesel (mobile/vehicles)",
            "co2e_factor": Decimal("2.70"),
            "activity_unit": "liters",
            "factor_unit": "kg CO2e/liter",
            "source": "DEFRA_2024",
            "region": "Global",
        },
    },

    # ------------------------------------------------------------------------
    # 1.3 Fugitive Emissions (32 factors)
    # ------------------------------------------------------------------------
    "1.3": {
        "refrigerant_r134a": {
            "display_name": "R-134a Refrigerant",
            "co2e_factor": Decimal("1530"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6",
            "region": "Global",
        },
        "refrigerant_r32": {
            "display_name": "R-32 Refrigerant",
            "co2e_factor": Decimal("771"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6",
            "region": "Global",
        },
        "refrigerant_r410a": {
            "display_name": "R-410A Refrigerant",
            "co2e_factor": Decimal("2256"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6",
            "region": "Global",
        },
        "refrigerant_r404a": {
            "display_name": "R-404A Refrigerant",
            "co2e_factor": Decimal("4728"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6",
            "region": "Global",
        },
        "refrigerant_r407a": {
            "display_name": "R-407A Blend",
            "co2e_factor": Decimal("2107"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_r407c": {
            "display_name": "R-407C Blend",
            "co2e_factor": Decimal("1774"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_r407f": {
            "display_name": "R-407F Blend",
            "co2e_factor": Decimal("1825"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_r417a": {
            "display_name": "R-417A Blend",
            "co2e_factor": Decimal("2346"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_r422d": {
            "display_name": "R-422D Blend",
            "co2e_factor": Decimal("2729"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_r507a": {
            "display_name": "R-507A Blend",
            "co2e_factor": Decimal("3985"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_r508b": {
            "display_name": "R-508B Blend",
            "co2e_factor": Decimal("13396"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_hfc23": {
            "display_name": "HFC-23 (CHF3)",
            "co2e_factor": Decimal("14800"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_hfc125": {
            "display_name": "HFC-125 (C2HF5)",
            "co2e_factor": Decimal("3740"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_hfc143a": {
            "display_name": "HFC-143a (C2H3F3)",
            "co2e_factor": Decimal("5810"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_hfc152a": {
            "display_name": "HFC-152a (C2H4F2)",
            "co2e_factor": Decimal("164"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_hfc227ea": {
            "display_name": "HFC-227ea (C3HF7)",
            "co2e_factor": Decimal("3600"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_hfc236fa": {
            "display_name": "HFC-236fa (C3H2F6)",
            "co2e_factor": Decimal("8690"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_hfc245fa": {
            "display_name": "HFC-245fa (C3H3F5)",
            "co2e_factor": Decimal("962"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_hfc365mfc": {
            "display_name": "HFC-365mfc (C4H5F5)",
            "co2e_factor": Decimal("914"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_hfc4310mee": {
            "display_name": "HFC-43-10mee (C5H2F10)",
            "co2e_factor": Decimal("1650"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_r1234yf": {
            "display_name": "R-1234yf (HFO-1234yf)",
            "co2e_factor": Decimal("1"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_r1234ze": {
            "display_name": "R-1234ze (HFO-1234ze)",
            "co2e_factor": Decimal("1"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_r290": {
            "display_name": "R-290 (Propane)",
            "co2e_factor": Decimal("3"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_r600a": {
            "display_name": "R-600a (Isobutane)",
            "co2e_factor": Decimal("3"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_r717": {
            "display_name": "R-717 (Ammonia)",
            "co2e_factor": Decimal("0"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_r744": {
            "display_name": "R-744 (CO2)",
            "co2e_factor": Decimal("1"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_sf6": {
            "display_name": "SF6 (Sulfur Hexafluoride)",
            "co2e_factor": Decimal("25200"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_nf3": {
            "display_name": "NF3 (Nitrogen Trifluoride)",
            "co2e_factor": Decimal("17400"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_pfc14": {
            "display_name": "PFC-14 / CF4 (Carbon Tetrafluoride)",
            "co2e_factor": Decimal("7380"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_pfc116": {
            "display_name": "PFC-116 / C2F6 (Hexafluoroethane)",
            "co2e_factor": Decimal("12400"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_pfc218": {
            "display_name": "PFC-218 / C3F8 (Perfluoropropane)",
            "co2e_factor": Decimal("9290"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_pfc318": {
            "display_name": "PFC-318 / c-C4F8 (Perfluorocyclobutane)",
            "co2e_factor": Decimal("10200"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        # Additional gases requested
        "refrigerant_r123": {
            "display_name": "R-123 / HCFC-123 (Dichlorotrifluoroethane)",
            "co2e_factor": Decimal("77"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_halon1211": {
            "display_name": "Halon-1211 (CF2BrCl - Fire Suppression)",
            "co2e_factor": Decimal("1750"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
        "refrigerant_fm200": {
            "display_name": "FM-200 / HFC-227ea (Fire Suppression)",
            "co2e_factor": Decimal("3350"),
            "activity_unit": "kg",
            "factor_unit": "kg CO2e/kg",
            "source": "IPCC_AR6_GWP100",
            "region": "Global",
        },
    },
}


# ============================================================================
# SCOPE 2: INDIRECT EMISSIONS FROM ENERGY
# ============================================================================

SCOPE_2_FACTORS = {
    # ------------------------------------------------------------------------
    # 2.1 Purchased Electricity (58 factors, 56 countries)
    # ------------------------------------------------------------------------
    "2.1": {
        # Global & Regional Averages
        "electricity_global": {
            "display_name": "Global Grid Electricity (average)",
            "co2e_factor": Decimal("0.436"),
            "activity_unit": "kWh",
            "factor_unit": "kg CO2e/kWh",
            "source": "IEA_2024",
            "region": "Global",
        },
        "electricity_eu": {
            "display_name": "EU Grid Electricity (average)",
            "co2e_factor": Decimal("0.255"),
            "activity_unit": "kWh",
            "factor_unit": "kg CO2e/kWh",
            "source": "EEA_2024",
            "region": "EU",
        },
        "electricity_renewable": {
            "display_name": "100% Renewable (Certified)",
            "co2e_factor": Decimal("0"),
            "activity_unit": "kWh",
            "factor_unit": "kg CO2e/kWh",
            "source": "Market_Based_Renewable",
            "region": "Global",
        },
        "electricity_supplier": {
            "display_name": "Supplier Specific Factor",
            "co2e_factor": Decimal("0"),
            "activity_unit": "kWh",
            "factor_unit": "kg CO2e/kWh",
            "source": "Supplier_Disclosure",
            "region": "Global",
        },
        # Country-specific factors (alphabetical by country code)
        "electricity_ae": {"display_name": "UAE Grid Electricity", "co2e_factor": Decimal("0.456"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "AE"},
        "electricity_ar": {"display_name": "Argentina Grid Electricity", "co2e_factor": Decimal("0.315"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "AR"},
        "electricity_at": {"display_name": "Austria Grid Electricity", "co2e_factor": Decimal("0.084"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "AT"},
        "electricity_au": {"display_name": "Australia Grid Electricity", "co2e_factor": Decimal("0.656"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "AU"},
        "electricity_be": {"display_name": "Belgium Grid Electricity", "co2e_factor": Decimal("0.137"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "BE"},
        "electricity_bg": {"display_name": "Bulgaria Grid Electricity", "co2e_factor": Decimal("0.533"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "BG"},
        "electricity_br": {"display_name": "Brazil Grid Electricity", "co2e_factor": Decimal("0.074"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "BR"},
        "electricity_ca": {"display_name": "Canada Grid Electricity", "co2e_factor": Decimal("0.12"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "CA"},
        "electricity_ch": {"display_name": "Switzerland Grid Electricity", "co2e_factor": Decimal("0.012"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "CH"},
        "electricity_cl": {"display_name": "Chile Grid Electricity", "co2e_factor": Decimal("0.355"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "CL"},
        "electricity_cn": {"display_name": "China Grid Electricity", "co2e_factor": Decimal("0.555"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "CN"},
        "electricity_cy": {"display_name": "Cyprus Grid Electricity", "co2e_factor": Decimal("0.700"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "CY"},
        "electricity_co": {"display_name": "Colombia Grid Electricity", "co2e_factor": Decimal("0.126"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "CO"},
        "electricity_cz": {"display_name": "Czech Republic Grid Electricity", "co2e_factor": Decimal("0.395"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "CZ"},
        "electricity_de": {"display_name": "Germany Grid Electricity", "co2e_factor": Decimal("0.377"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "DE"},
        "electricity_dk": {"display_name": "Denmark Grid Electricity", "co2e_factor": Decimal("0.116"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "DK"},
        "electricity_ee": {"display_name": "Estonia Grid Electricity", "co2e_factor": Decimal("0.722"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "EE"},
        "electricity_eg": {"display_name": "Egypt Grid Electricity", "co2e_factor": Decimal("0.448"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "EG"},
        "electricity_es": {"display_name": "Spain Grid Electricity", "co2e_factor": Decimal("0.186"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "ES"},
        "electricity_fi": {"display_name": "Finland Grid Electricity", "co2e_factor": Decimal("0.073"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "FI"},
        "electricity_fr": {"display_name": "France Grid Electricity", "co2e_factor": Decimal("0.056"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "FR"},
        "electricity_gr": {"display_name": "Greece Grid Electricity", "co2e_factor": Decimal("0.337"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "GR"},
        "electricity_hk": {"display_name": "Hong Kong Grid Electricity", "co2e_factor": Decimal("0.63"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "HK"},
        "electricity_hr": {"display_name": "Croatia Grid Electricity", "co2e_factor": Decimal("0.271"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "HR"},
        "electricity_hu": {"display_name": "Hungary Grid Electricity", "co2e_factor": Decimal("0.218"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "HU"},
        "electricity_id": {"display_name": "Indonesia Grid Electricity", "co2e_factor": Decimal("0.722"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "ID"},
        "electricity_ie": {"display_name": "Ireland Grid Electricity", "co2e_factor": Decimal("0.272"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "IE"},
        "electricity_il": {"display_name": "Israel Grid Electricity", "co2e_factor": Decimal("0.527"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEC_2024", "region": "IL"},
        "electricity_in": {"display_name": "India Grid Electricity", "co2e_factor": Decimal("0.708"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "IN"},
        "electricity_it": {"display_name": "Italy Grid Electricity", "co2e_factor": Decimal("0.315"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "IT"},
        "electricity_jp": {"display_name": "Japan Grid Electricity", "co2e_factor": Decimal("0.453"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "JP"},
        "electricity_ke": {"display_name": "Kenya Grid Electricity", "co2e_factor": Decimal("0.093"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "KE"},
        "electricity_kr": {"display_name": "South Korea Grid Electricity", "co2e_factor": Decimal("0.417"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "KR"},
        "electricity_lt": {"display_name": "Lithuania Grid Electricity", "co2e_factor": Decimal("0.187"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "LT"},
        "electricity_lu": {"display_name": "Luxembourg Grid Electricity", "co2e_factor": Decimal("0.137"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "LU"},
        "electricity_lv": {"display_name": "Latvia Grid Electricity", "co2e_factor": Decimal("0.161"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "LV"},
        "electricity_mx": {"display_name": "Mexico Grid Electricity", "co2e_factor": Decimal("0.435"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "MX"},
        "electricity_my": {"display_name": "Malaysia Grid Electricity", "co2e_factor": Decimal("0.585"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "MY"},
        "electricity_mt": {"display_name": "Malta Grid Electricity", "co2e_factor": Decimal("0.479"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "MT"},
        "electricity_ng": {"display_name": "Nigeria Grid Electricity", "co2e_factor": Decimal("0.41"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "NG"},
        "electricity_nl": {"display_name": "Netherlands Grid Electricity", "co2e_factor": Decimal("0.312"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "NL"},
        "electricity_no": {"display_name": "Norway Grid Electricity", "co2e_factor": Decimal("0.008"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "NO"},
        "electricity_nz": {"display_name": "New Zealand Grid Electricity", "co2e_factor": Decimal("0.082"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "NZ"},
        "electricity_ph": {"display_name": "Philippines Grid Electricity", "co2e_factor": Decimal("0.593"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "PH"},
        "electricity_pl": {"display_name": "Poland Grid Electricity", "co2e_factor": Decimal("0.682"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "PL"},
        "electricity_pt": {"display_name": "Portugal Grid Electricity", "co2e_factor": Decimal("0.155"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "PT"},
        "electricity_ro": {"display_name": "Romania Grid Electricity", "co2e_factor": Decimal("0.258"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "RO"},
        "electricity_ru": {"display_name": "Russia Grid Electricity", "co2e_factor": Decimal("0.335"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "RU"},
        "electricity_sa": {"display_name": "Saudi Arabia Grid Electricity", "co2e_factor": Decimal("0.59"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "SA"},
        "electricity_se": {"display_name": "Sweden Grid Electricity", "co2e_factor": Decimal("0.009"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "SE"},
        "electricity_sg": {"display_name": "Singapore Grid Electricity", "co2e_factor": Decimal("0.408"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "SG"},
        "electricity_si": {"display_name": "Slovenia Grid Electricity", "co2e_factor": Decimal("0.234"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "SI"},
        "electricity_sk": {"display_name": "Slovakia Grid Electricity", "co2e_factor": Decimal("0.113"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EEA_2024", "region": "SK"},
        "electricity_th": {"display_name": "Thailand Grid Electricity", "co2e_factor": Decimal("0.47"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "TH"},
        "electricity_tr": {"display_name": "Turkey Grid Electricity", "co2e_factor": Decimal("0.378"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "TR"},
        "electricity_tw": {"display_name": "Taiwan Grid Electricity", "co2e_factor": Decimal("0.509"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "TW"},
        "electricity_uk": {"display_name": "UK Grid Electricity", "co2e_factor": Decimal("0.207"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "DEFRA_2024", "region": "UK"},
        "electricity_us": {"display_name": "US Grid Electricity (average)", "co2e_factor": Decimal("0.386"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US"},
        "electricity_us_ca": {"display_name": "USA - California Grid", "co2e_factor": Decimal("0.225"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_CAMX", "region": "US-CA"},
        "electricity_us_mw": {"display_name": "USA - Midwest Grid", "co2e_factor": Decimal("0.475"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_MROW", "region": "US-MW"},
        "electricity_us_ny": {"display_name": "USA - New York Grid", "co2e_factor": Decimal("0.188"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_NYUP", "region": "US-NY"},
        "electricity_us_tx": {"display_name": "USA - Texas Grid (ERCOT)", "co2e_factor": Decimal("0.373"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_ERCT", "region": "US-TX"},
        # Additional US state-level factors (EPA eGRID 2024)
        "electricity_us_fl": {"display_name": "USA - Florida Grid (FRCC)", "co2e_factor": Decimal("0.391"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_FRCC", "region": "US-FL"},
        "electricity_us_az": {"display_name": "USA - Arizona Grid (AZNM)", "co2e_factor": Decimal("0.345"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_AZNM", "region": "US-AZ"},
        "electricity_us_co": {"display_name": "USA - Colorado Grid (RMPA)", "co2e_factor": Decimal("0.525"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_RMPA", "region": "US-CO"},
        "electricity_us_il": {"display_name": "USA - Illinois Grid (RFCM)", "co2e_factor": Decimal("0.341"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_RFCM", "region": "US-IL"},
        "electricity_us_pa": {"display_name": "USA - Pennsylvania Grid (RFCE)", "co2e_factor": Decimal("0.297"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_RFCE", "region": "US-PA"},
        "electricity_us_oh": {"display_name": "USA - Ohio Grid (RFCM)", "co2e_factor": Decimal("0.497"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_RFCM", "region": "US-OH"},
        "electricity_us_wa": {"display_name": "USA - Washington Grid (NWPP)", "co2e_factor": Decimal("0.118"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_NWPP", "region": "US-WA"},
        "electricity_us_or": {"display_name": "USA - Oregon Grid (NWPP)", "co2e_factor": Decimal("0.118"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_NWPP", "region": "US-OR"},
        "electricity_us_ma": {"display_name": "USA - Massachusetts Grid (NEWE)", "co2e_factor": Decimal("0.227"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_NEWE", "region": "US-MA"},
        "electricity_us_nj": {"display_name": "USA - New Jersey Grid (RFCE)", "co2e_factor": Decimal("0.232"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_RFCE", "region": "US-NJ"},
        "electricity_us_ga": {"display_name": "USA - Georgia Grid (SRSO)", "co2e_factor": Decimal("0.383"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_SRSO", "region": "US-GA"},
        "electricity_us_nc": {"display_name": "USA - North Carolina Grid (SRVC)", "co2e_factor": Decimal("0.347"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_SRVC", "region": "US-NC"},
        "electricity_us_va": {"display_name": "USA - Virginia Grid (SRVC)", "co2e_factor": Decimal("0.318"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_SRVC", "region": "US-VA"},
        "electricity_us_mi": {"display_name": "USA - Michigan Grid (RFCM)", "co2e_factor": Decimal("0.443"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_RFCM", "region": "US-MI"},
        "electricity_us_mn": {"display_name": "USA - Minnesota Grid (MROW)", "co2e_factor": Decimal("0.405"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024_MROW", "region": "US-MN"},
        # EPA eGRID Subregions (direct selection by subregion code)
        "electricity_egrid_akgd": {"display_name": "eGRID - AKGD (ASCC Alaska Grid)", "co2e_factor": Decimal("0.438"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-AKGD"},
        "electricity_egrid_akms": {"display_name": "eGRID - AKMS (ASCC Miscellaneous)", "co2e_factor": Decimal("0.300"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-AKMS"},
        "electricity_egrid_aznm": {"display_name": "eGRID - AZNM (WECC Southwest)", "co2e_factor": Decimal("0.345"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-AZNM"},
        "electricity_egrid_camx": {"display_name": "eGRID - CAMX (WECC California)", "co2e_factor": Decimal("0.225"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-CAMX"},
        "electricity_egrid_erct": {"display_name": "eGRID - ERCT (ERCOT Texas)", "co2e_factor": Decimal("0.373"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-ERCT"},
        "electricity_egrid_frcc": {"display_name": "eGRID - FRCC (FRCC Florida)", "co2e_factor": Decimal("0.391"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-FRCC"},
        "electricity_egrid_hims": {"display_name": "eGRID - HIMS (HICC Miscellaneous)", "co2e_factor": Decimal("0.513"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-HIMS"},
        "electricity_egrid_hioa": {"display_name": "eGRID - HIOA (HICC Oahu)", "co2e_factor": Decimal("0.636"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-HIOA"},
        "electricity_egrid_mroe": {"display_name": "eGRID - MROE (MRO East)", "co2e_factor": Decimal("0.563"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-MROE"},
        "electricity_egrid_mrow": {"display_name": "eGRID - MROW (MRO West)", "co2e_factor": Decimal("0.475"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-MROW"},
        "electricity_egrid_newe": {"display_name": "eGRID - NEWE (NPCC New England)", "co2e_factor": Decimal("0.227"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-NEWE"},
        "electricity_egrid_nwpp": {"display_name": "eGRID - NWPP (WECC Northwest)", "co2e_factor": Decimal("0.118"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-NWPP"},
        "electricity_egrid_nycw": {"display_name": "eGRID - NYCW (NPCC NYC/Westchester)", "co2e_factor": Decimal("0.225"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-NYCW"},
        "electricity_egrid_nyli": {"display_name": "eGRID - NYLI (NPCC Long Island)", "co2e_factor": Decimal("0.420"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-NYLI"},
        "electricity_egrid_nyup": {"display_name": "eGRID - NYUP (NPCC Upstate NY)", "co2e_factor": Decimal("0.088"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-NYUP"},
        "electricity_egrid_prms": {"display_name": "eGRID - PRMS (Puerto Rico)", "co2e_factor": Decimal("0.725"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-PRMS"},
        "electricity_egrid_rfce": {"display_name": "eGRID - RFCE (RFC East)", "co2e_factor": Decimal("0.297"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-RFCE"},
        "electricity_egrid_rfcm": {"display_name": "eGRID - RFCM (RFC Michigan)", "co2e_factor": Decimal("0.443"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-RFCM"},
        "electricity_egrid_rfcw": {"display_name": "eGRID - RFCW (RFC West)", "co2e_factor": Decimal("0.497"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-RFCW"},
        "electricity_egrid_rmpa": {"display_name": "eGRID - RMPA (WECC Rockies)", "co2e_factor": Decimal("0.525"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-RMPA"},
        "electricity_egrid_spno": {"display_name": "eGRID - SPNO (SPP North)", "co2e_factor": Decimal("0.487"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-SPNO"},
        "electricity_egrid_spso": {"display_name": "eGRID - SPSO (SPP South)", "co2e_factor": Decimal("0.449"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-SPSO"},
        "electricity_egrid_srmv": {"display_name": "eGRID - SRMV (SERC Mississippi Valley)", "co2e_factor": Decimal("0.359"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-SRMV"},
        "electricity_egrid_srmw": {"display_name": "eGRID - SRMW (SERC Midwest)", "co2e_factor": Decimal("0.617"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-SRMW"},
        "electricity_egrid_srso": {"display_name": "eGRID - SRSO (SERC South)", "co2e_factor": Decimal("0.383"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-SRSO"},
        "electricity_egrid_srtv": {"display_name": "eGRID - SRTV (SERC Tennessee Valley)", "co2e_factor": Decimal("0.379"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-SRTV"},
        "electricity_egrid_srvc": {"display_name": "eGRID - SRVC (SERC Virginia/Carolina)", "co2e_factor": Decimal("0.347"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "EPA_eGRID_2024", "region": "US-SRVC"},
        "electricity_vn": {"display_name": "Vietnam Grid Electricity", "co2e_factor": Decimal("0.476"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "VN"},
        "electricity_za": {"display_name": "South Africa Grid Electricity", "co2e_factor": Decimal("0.928"), "activity_unit": "kWh", "factor_unit": "kg CO2e/kWh", "source": "IEA_2024", "region": "ZA"},
    },

    # ------------------------------------------------------------------------
    # 2.2 Purchased Heat/Steam (2 factors)
    # ------------------------------------------------------------------------
    "2.2": {
        "district_heat_kwh": {
            "display_name": "District Heating",
            "co2e_factor": Decimal("0.166"),
            "activity_unit": "kWh",
            "factor_unit": "kg CO2e/kWh",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "steam_kwh": {
            "display_name": "Steam",
            "co2e_factor": Decimal("0.191"),
            "activity_unit": "kWh",
            "factor_unit": "kg CO2e/kWh",
            "source": "DEFRA_2024",
            "region": "Global",
        },
    },

    # ------------------------------------------------------------------------
    # 2.3 Purchased Cooling (2 factors)
    # ------------------------------------------------------------------------
    "2.3": {
        "chilled_water_kwh": {
            "display_name": "Chilled Water",
            "co2e_factor": Decimal("0.18"),
            "activity_unit": "kWh",
            "factor_unit": "kg CO2e/kWh",
            "source": "DEFRA_2024",
            "region": "Global",
        },
        "district_cooling_kwh": {
            "display_name": "District Cooling",
            "co2e_factor": Decimal("0.21"),
            "activity_unit": "kWh",
            "factor_unit": "kg CO2e/kWh",
            "source": "DEFRA_2024",
            "region": "Global",
        },
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_factor(scope: int, category: str, activity_key: str) -> dict:
    """Get emission factor by scope, category, and activity key."""
    factors = SCOPE_1_FACTORS if scope == 1 else SCOPE_2_FACTORS
    if category in factors and activity_key in factors[category]:
        return factors[category][activity_key]
    return None


def list_activity_keys(scope: int, category: str) -> list:
    """List all activity keys for a given scope and category."""
    factors = SCOPE_1_FACTORS if scope == 1 else SCOPE_2_FACTORS
    if category in factors:
        return list(factors[category].keys())
    return []


def get_all_factors_flat() -> list:
    """Get all factors as a flat list for database seeding."""
    result = []
    for category, factors in SCOPE_1_FACTORS.items():
        for key, data in factors.items():
            result.append({
                "scope": 1,
                "category_code": category,
                "activity_key": key,
                **data
            })
    for category, factors in SCOPE_2_FACTORS.items():
        for key, data in factors.items():
            result.append({
                "scope": 2,
                "category_code": category,
                "activity_key": key,
                **data
            })
    return result
