"""
Fuel prices for spend-to-quantity conversion in Scope 1 calculations.

Sources:
- US: EIA (Energy Information Administration) Weekly Retail Prices
- UK: DESNZ (Department for Energy Security and Net Zero)
- Israel: IEC (Israel Electric Corporation), Paz/Delek fuel stations
- EU: European Commission Weekly Oil Bulletin

Last updated: January 2025

IMPORTANT: Prices are averages and should be updated quarterly.
Users can override with their actual fuel prices.
"""

from datetime import date

# Fuel prices with source documentation
FUEL_PRICES = [
    # ============================================================================
    # DIESEL
    # ============================================================================
    {
        "fuel_type": "diesel",
        "price_per_unit": 1.00,  # ~$3.80/gallon converted
        "currency": "USD",
        "unit": "liter",
        "region": "US",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "EIA Weekly Retail On-Highway Diesel Prices 2024",
        "source_url": "https://www.eia.gov/petroleum/gasdiesel/"
    },
    {
        "fuel_type": "diesel",
        "price_per_unit": 1.50,
        "currency": "GBP",
        "unit": "liter",
        "region": "UK",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "UK DESNZ Weekly Road Fuel Prices 2024",
        "source_url": "https://www.gov.uk/government/statistics/weekly-road-fuel-prices"
    },
    {
        "fuel_type": "diesel",
        "price_per_unit": 6.80,
        "currency": "ILS",
        "unit": "liter",
        "region": "IL",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Israel Ministry of Energy - Regulated Fuel Prices 2024",
        "source_url": "https://www.gov.il/he/departments/topics/fuel_prices"
    },
    {
        "fuel_type": "diesel",
        "price_per_unit": 1.60,
        "currency": "EUR",
        "unit": "liter",
        "region": "EU",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "European Commission Weekly Oil Bulletin 2024",
        "source_url": "https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en"
    },
    # Global fallback (USD)
    {
        "fuel_type": "diesel",
        "price_per_unit": 1.20,
        "currency": "USD",
        "unit": "liter",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "IEA Global Average Diesel Price 2024",
        "source_url": "https://www.iea.org/"
    },

    # ============================================================================
    # PETROL / GASOLINE
    # ============================================================================
    {
        "fuel_type": "petrol",
        "price_per_unit": 0.92,  # ~$3.50/gallon converted
        "currency": "USD",
        "unit": "liter",
        "region": "US",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "EIA Weekly Retail Gasoline Prices 2024",
        "source_url": "https://www.eia.gov/petroleum/gasdiesel/"
    },
    {
        "fuel_type": "petrol",
        "price_per_unit": 1.45,
        "currency": "GBP",
        "unit": "liter",
        "region": "UK",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "UK DESNZ Weekly Road Fuel Prices 2024",
        "source_url": "https://www.gov.uk/government/statistics/weekly-road-fuel-prices"
    },
    {
        "fuel_type": "petrol",
        "price_per_unit": 6.50,
        "currency": "ILS",
        "unit": "liter",
        "region": "IL",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Israel Ministry of Energy - Regulated Fuel Prices 2024",
        "source_url": "https://www.gov.il/he/departments/topics/fuel_prices"
    },
    {
        "fuel_type": "petrol",
        "price_per_unit": 1.70,
        "currency": "EUR",
        "unit": "liter",
        "region": "EU",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "European Commission Weekly Oil Bulletin 2024",
        "source_url": "https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en"
    },
    {
        "fuel_type": "petrol",
        "price_per_unit": 1.10,
        "currency": "USD",
        "unit": "liter",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "IEA Global Average Gasoline Price 2024",
        "source_url": "https://www.iea.org/"
    },

    # ============================================================================
    # NATURAL GAS
    # ============================================================================
    {
        "fuel_type": "natural_gas",
        "price_per_unit": 0.035,  # $0.035 per kWh (~$10/MMBtu)
        "currency": "USD",
        "unit": "kWh",
        "region": "US",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "EIA Natural Gas Prices - Commercial Sector 2024",
        "source_url": "https://www.eia.gov/naturalgas/monthly/"
    },
    {
        "fuel_type": "natural_gas",
        "price_per_unit": 0.06,  # 6 pence per kWh
        "currency": "GBP",
        "unit": "kWh",
        "region": "UK",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Ofgem Energy Price Cap 2024",
        "source_url": "https://www.ofgem.gov.uk/energy-price-cap"
    },
    {
        "fuel_type": "natural_gas",
        "price_per_unit": 0.18,  # ILS per kWh
        "currency": "ILS",
        "unit": "kWh",
        "region": "IL",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Israel Natural Gas Authority 2024",
        "source_url": "https://www.gov.il/he/departments/natural_gas_authority"
    },
    {
        "fuel_type": "natural_gas",
        "price_per_unit": 0.045,
        "currency": "EUR",
        "unit": "kWh",
        "region": "EU",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Eurostat Natural Gas Prices 2024",
        "source_url": "https://ec.europa.eu/eurostat/statistics-explained/index.php/Natural_gas_price_statistics"
    },
    {
        "fuel_type": "natural_gas",
        "price_per_unit": 0.04,
        "currency": "USD",
        "unit": "kWh",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "IEA World Energy Outlook 2024",
        "source_url": "https://www.iea.org/"
    },
    # Natural gas by m3
    {
        "fuel_type": "natural_gas",
        "price_per_unit": 0.38,  # USD per m3
        "currency": "USD",
        "unit": "m3",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "IEA - converted from kWh (1 m3 = ~10.55 kWh)",
        "source_url": "https://www.iea.org/"
    },

    # ============================================================================
    # LPG (Liquefied Petroleum Gas)
    # ============================================================================
    {
        "fuel_type": "lpg",
        "price_per_unit": 0.75,
        "currency": "USD",
        "unit": "liter",
        "region": "US",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "EIA Propane/LPG Prices 2024",
        "source_url": "https://www.eia.gov/petroleum/heatingoil/index.php"
    },
    {
        "fuel_type": "lpg",
        "price_per_unit": 0.85,
        "currency": "GBP",
        "unit": "liter",
        "region": "UK",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "UK DESNZ LPG Prices 2024",
        "source_url": "https://www.gov.uk/government/statistics/weekly-road-fuel-prices"
    },
    {
        "fuel_type": "lpg",
        "price_per_unit": 4.50,
        "currency": "ILS",
        "unit": "liter",
        "region": "IL",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Israel Ministry of Energy 2024",
        "source_url": "https://www.gov.il/he/departments/topics/fuel_prices"
    },
    {
        "fuel_type": "lpg",
        "price_per_unit": 0.80,
        "currency": "USD",
        "unit": "liter",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "World Bank Commodity Prices 2024",
        "source_url": "https://www.worldbank.org/en/research/commodity-markets"
    },

    # ============================================================================
    # ELECTRICITY (for Scope 2)
    # Prices per kWh for commercial/industrial customers
    # Sources: Eurostat, EIA, national energy regulators
    # ============================================================================
    # USA (National Average)
    {
        "fuel_type": "electricity",
        "price_per_unit": 0.15,
        "currency": "USD",
        "unit": "kWh",
        "region": "US",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "EIA Average Retail Price of Electricity - Commercial 2024",
        "source_url": "https://www.eia.gov/electricity/monthly/"
    },
    # UK
    {
        "fuel_type": "electricity",
        "price_per_unit": 0.28,  # 28 pence per kWh
        "currency": "GBP",
        "unit": "kWh",
        "region": "UK",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Ofgem Energy Price Cap 2024",
        "source_url": "https://www.ofgem.gov.uk/energy-price-cap"
    },
    # Israel
    {
        "fuel_type": "electricity",
        "price_per_unit": 0.58,  # ILS per kWh
        "currency": "ILS",
        "unit": "kWh",
        "region": "IL",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Israel Electric Corporation Tariffs 2024",
        "source_url": "https://www.iec.co.il/"
    },
    # EU Average
    {
        "fuel_type": "electricity",
        "price_per_unit": 0.22,
        "currency": "EUR",
        "unit": "kWh",
        "region": "EU",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Eurostat Electricity Prices 2024",
        "source_url": "https://ec.europa.eu/eurostat/statistics-explained/index.php/Electricity_price_statistics"
    },
    # Germany
    {
        "fuel_type": "electricity",
        "price_per_unit": 0.35,  # EUR per kWh (higher due to Energiewende)
        "currency": "EUR",
        "unit": "kWh",
        "region": "DE",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "BDEW German Electricity Prices 2024",
        "source_url": "https://www.bdew.de/"
    },
    # France
    {
        "fuel_type": "electricity",
        "price_per_unit": 0.21,  # EUR per kWh (nuclear keeps prices lower)
        "currency": "EUR",
        "unit": "kWh",
        "region": "FR",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "CRE French Electricity Prices 2024",
        "source_url": "https://www.cre.fr/"
    },
    # Spain
    {
        "fuel_type": "electricity",
        "price_per_unit": 0.24,  # EUR per kWh
        "currency": "EUR",
        "unit": "kWh",
        "region": "ES",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "CNMC Spanish Electricity Prices 2024",
        "source_url": "https://www.cnmc.es/"
    },
    # Italy
    {
        "fuel_type": "electricity",
        "price_per_unit": 0.29,  # EUR per kWh
        "currency": "EUR",
        "unit": "kWh",
        "region": "IT",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "ARERA Italian Electricity Prices 2024",
        "source_url": "https://www.arera.it/"
    },
    # Netherlands
    {
        "fuel_type": "electricity",
        "price_per_unit": 0.30,  # EUR per kWh
        "currency": "EUR",
        "unit": "kWh",
        "region": "NL",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "ACM Dutch Electricity Prices 2024",
        "source_url": "https://www.acm.nl/"
    },
    # Poland
    {
        "fuel_type": "electricity",
        "price_per_unit": 0.18,  # EUR per kWh (lower but coal-heavy)
        "currency": "EUR",
        "unit": "kWh",
        "region": "PL",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "URE Polish Electricity Prices 2024",
        "source_url": "https://www.ure.gov.pl/"
    },
    # Canada
    {
        "fuel_type": "electricity",
        "price_per_unit": 0.12,  # CAD per kWh (varies by province)
        "currency": "CAD",
        "unit": "kWh",
        "region": "CA",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Statistics Canada Electricity Prices 2024",
        "source_url": "https://www.statcan.gc.ca/"
    },
    # Japan
    {
        "fuel_type": "electricity",
        "price_per_unit": 28.0,  # JPY per kWh
        "currency": "JPY",
        "unit": "kWh",
        "region": "JP",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "METI Japan Electricity Prices 2024",
        "source_url": "https://www.meti.go.jp/"
    },
    # South Korea
    {
        "fuel_type": "electricity",
        "price_per_unit": 120.0,  # KRW per kWh
        "currency": "KRW",
        "unit": "kWh",
        "region": "KR",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "KEPCO South Korea Electricity Tariffs 2024",
        "source_url": "https://home.kepco.co.kr/"
    },
    # China
    {
        "fuel_type": "electricity",
        "price_per_unit": 0.65,  # CNY per kWh
        "currency": "CNY",
        "unit": "kWh",
        "region": "CN",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "NDRC China Electricity Prices 2024",
        "source_url": "https://www.ndrc.gov.cn/"
    },
    # Singapore
    {
        "fuel_type": "electricity",
        "price_per_unit": 0.28,  # SGD per kWh
        "currency": "SGD",
        "unit": "kWh",
        "region": "SG",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "EMA Singapore Electricity Tariffs 2024",
        "source_url": "https://www.ema.gov.sg/"
    },
    # Australia
    {
        "fuel_type": "electricity",
        "price_per_unit": 0.32,  # AUD per kWh
        "currency": "AUD",
        "unit": "kWh",
        "region": "AU",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "AER Australian Default Offer 2024",
        "source_url": "https://www.aer.gov.au/"
    },
    # India
    {
        "fuel_type": "electricity",
        "price_per_unit": 8.5,  # INR per kWh
        "currency": "INR",
        "unit": "kWh",
        "region": "IN",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "CERC India Electricity Tariffs 2024",
        "source_url": "https://cercind.gov.in/"
    },
    # Global Average
    {
        "fuel_type": "electricity",
        "price_per_unit": 0.14,
        "currency": "USD",
        "unit": "kWh",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "IEA Global Average Electricity Price 2024",
        "source_url": "https://www.iea.org/"
    },

    # ============================================================================
    # COAL
    # ============================================================================
    {
        "fuel_type": "coal",
        "price_per_unit": 150.00,  # USD per tonne
        "currency": "USD",
        "unit": "tonne",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "World Bank Coal Price Index 2024",
        "source_url": "https://www.worldbank.org/en/research/commodity-markets"
    },

    # ============================================================================
    # HEATING OIL / FUEL OIL
    # ============================================================================
    {
        "fuel_type": "heating_oil",
        "price_per_unit": 1.05,
        "currency": "USD",
        "unit": "liter",
        "region": "US",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "EIA Weekly Heating Oil Prices 2024",
        "source_url": "https://www.eia.gov/petroleum/heatingoil/"
    },
    {
        "fuel_type": "heating_oil",
        "price_per_unit": 0.90,
        "currency": "GBP",
        "unit": "liter",
        "region": "UK",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Boiler Juice UK Heating Oil Prices 2024",
        "source_url": "https://www.boilerjuice.com/heating-oil-prices/"
    },
    {
        "fuel_type": "heating_oil",
        "price_per_unit": 1.00,
        "currency": "USD",
        "unit": "liter",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "IEA Fuel Oil Average Price 2024",
        "source_url": "https://www.iea.org/"
    },

    # ============================================================================
    # REFRIGERANTS (for Scope 1.3 Fugitive Emissions)
    # Prices are for bulk refrigerant purchases ($/kg)
    # ============================================================================
    {
        "fuel_type": "refrigerant_r134a",
        "price_per_unit": 15.00,  # USD per kg
        "currency": "USD",
        "unit": "kg",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "HVAC Industry Average - R-134a Bulk Price 2024",
        "source_url": "https://www.coolingpost.com/"
    },
    {
        "fuel_type": "refrigerant_r410a",
        "price_per_unit": 18.00,  # USD per kg
        "currency": "USD",
        "unit": "kg",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "HVAC Industry Average - R-410A Bulk Price 2024",
        "source_url": "https://www.coolingpost.com/"
    },
    {
        "fuel_type": "refrigerant_r32",
        "price_per_unit": 12.00,  # USD per kg
        "currency": "USD",
        "unit": "kg",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "HVAC Industry Average - R-32 Bulk Price 2024",
        "source_url": "https://www.coolingpost.com/"
    },
    {
        "fuel_type": "refrigerant_r404a",
        "price_per_unit": 25.00,  # USD per kg
        "currency": "USD",
        "unit": "kg",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "HVAC Industry Average - R-404A Bulk Price 2024 (phasedown impacts price)",
        "source_url": "https://www.coolingpost.com/"
    },
    # CO2 refrigerant (R-744)
    {
        "fuel_type": "refrigerant_co2",
        "price_per_unit": 3.00,  # USD per kg (CO2 is much cheaper)
        "currency": "USD",
        "unit": "kg",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Industrial CO2 Prices 2024",
        "source_url": "https://www.iea.org/"
    },
    # HFC-23 (high GWP refrigerant)
    {
        "fuel_type": "refrigerant_hfc23",
        "price_per_unit": 50.00,  # USD per kg (controlled substance)
        "currency": "USD",
        "unit": "kg",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Fluorochemical Industry Prices 2024",
        "source_url": "https://www.fluorocarbons.org/"
    },

    # ============================================================================
    # PROCESS MATERIALS (for Scope 1.4 Process Emissions)
    # Prices per tonne for industrial materials
    # ============================================================================
    # Cement & Clinker
    {
        "fuel_type": "cement_production",
        "price_per_unit": 120.00,  # USD per tonne
        "currency": "USD",
        "unit": "tonne",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "World Bank Commodity Markets - Cement Price Index 2024",
        "source_url": "https://www.worldbank.org/en/research/commodity-markets"
    },
    {
        "fuel_type": "clinker_production",
        "price_per_unit": 100.00,  # USD per tonne (clinker is cheaper than finished cement)
        "currency": "USD",
        "unit": "tonne",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Global Cement Report - Clinker Prices 2024",
        "source_url": "https://www.globalcement.com/"
    },
    # Lime
    {
        "fuel_type": "quicklime_production",
        "price_per_unit": 150.00,  # USD per tonne
        "currency": "USD",
        "unit": "tonne",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Industrial Minerals - Lime Prices 2024",
        "source_url": "https://www.indmin.com/"
    },
    {
        "fuel_type": "dolomitic_lime_production",
        "price_per_unit": 160.00,  # USD per tonne
        "currency": "USD",
        "unit": "tonne",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Industrial Minerals - Dolomitic Lime Prices 2024",
        "source_url": "https://www.indmin.com/"
    },
    # Glass
    {
        "fuel_type": "glass_production",
        "price_per_unit": 800.00,  # USD per tonne (finished glass products)
        "currency": "USD",
        "unit": "tonne",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "Glass Industry Association Price Index 2024",
        "source_url": "https://www.glass.org/"
    },
    # Ammonia
    {
        "fuel_type": "ammonia_production",
        "price_per_unit": 450.00,  # USD per tonne
        "currency": "USD",
        "unit": "tonne",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "World Bank - Ammonia (Gulf) Price 2024",
        "source_url": "https://www.worldbank.org/en/research/commodity-markets"
    },
    # Iron & Steel
    {
        "fuel_type": "iron_steel_production",
        "price_per_unit": 550.00,  # USD per tonne (hot rolled coil benchmark)
        "currency": "USD",
        "unit": "tonne",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "World Steel Association - Steel Price Index 2024",
        "source_url": "https://worldsteel.org/"
    },
    {
        "fuel_type": "steel_eaf_production",
        "price_per_unit": 600.00,  # USD per tonne (EAF steel slightly premium)
        "currency": "USD",
        "unit": "tonne",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "World Steel Association - EAF Steel Prices 2024",
        "source_url": "https://worldsteel.org/"
    },
    # Aluminum
    {
        "fuel_type": "aluminum_primary_production",
        "price_per_unit": 2400.00,  # USD per tonne (LME aluminum price)
        "currency": "USD",
        "unit": "tonne",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "London Metal Exchange - Aluminum Price 2024",
        "source_url": "https://www.lme.com/"
    },
    # Chemicals
    {
        "fuel_type": "nitric_acid_production",
        "price_per_unit": 350.00,  # USD per tonne
        "currency": "USD",
        "unit": "tonne",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "ICIS Chemical Prices - Nitric Acid 2024",
        "source_url": "https://www.icis.com/"
    },
    {
        "fuel_type": "adipic_acid_production",
        "price_per_unit": 1800.00,  # USD per tonne
        "currency": "USD",
        "unit": "tonne",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "ICIS Chemical Prices - Adipic Acid 2024",
        "source_url": "https://www.icis.com/"
    },
    # Hydrogen
    {
        "fuel_type": "hydrogen_smr_production",
        "price_per_unit": 2000.00,  # USD per tonne (grey hydrogen from SMR)
        "currency": "USD",
        "unit": "tonne",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "IEA Global Hydrogen Review - SMR Hydrogen Prices 2024",
        "source_url": "https://www.iea.org/reports/global-hydrogen-review"
    },
    # Petrochemicals
    {
        "fuel_type": "ethylene_production",
        "price_per_unit": 1100.00,  # USD per tonne
        "currency": "USD",
        "unit": "tonne",
        "region": "Global",
        "valid_from": date(2024, 1, 1),
        "valid_until": date(2025, 12, 31),
        "source": "ICIS Petrochemical Prices - Ethylene 2024",
        "source_url": "https://www.icis.com/"
    },
]
