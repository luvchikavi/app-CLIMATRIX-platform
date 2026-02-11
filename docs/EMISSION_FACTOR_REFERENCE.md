# CLIMATRIX Emission Factor Reference

## Source: Official DEFRA 2024 GHG Conversion Factors v1.1 (October 2024)
- Publication: UK Government GHG Conversion Factors for Company Reporting 2024
- URL: https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024
- File: ghg-conversion-factors-2024-FlatFormat_v1_1.xlsx
- GWP basis: DEFRA 2024 internally uses IPCC AR5 GWP values (CH4=28, N2O=265)

## GWP Methodology Notes

### Current State
- **Fuel factors** (Scope 1.1, 1.2): Sourced from DEFRA 2024 which uses AR5 GWPs for CH4/N2O components
- **Refrigerant GWPs** (Scope 1.3): Currently labeled as IPCC_AR6 in the database
- **This creates an inconsistency**: fuel CO2e values use AR5 GWPs, while refrigerant CO2e values use AR6 GWPs

### Framework Requirements
| Framework | Required GWP | Notes |
|-----------|-------------|-------|
| GHG Protocol | AR5 or AR6 | Tools still use AR5 |
| CDP | AR5 or AR6 | Must be consistent and disclosed |
| CSRD/ESRS E1 | AR6 expected | Latest IPCC requirement for EU |
| SBTi | AR5 or later | AR5 minimum |
| DEFRA 2024 | AR5 internally | All DEFRA factors use AR5 |

### DEFRA 2024 vs IPCC AR6 GWP Comparison (Refrigerants)
| Refrigerant | DEFRA 2024 (AR5) | IPCC AR6 | App DB Value | Issue |
|-------------|-----------------|----------|-------------|-------|
| HFC-32 | 677 | 771 | 771 | DB uses AR6 |
| HFC-134a | 1300 | 1530 | 1530 | DB uses AR6 |
| R-404A | 3943 | ~4728 | 4728 | DB uses AR6 |
| R-407C | 1624 | ~1774 | 1774 | DB uses AR6 |
| R-410A | 1924 | 2088 | **2256** | **DB value matches neither AR5 nor AR6** |
| R-507A | 3985 | 3985 | 3985 | Same in both |
| HFC-227ea | 3350 | 3350 | **3220** | **DB value is incorrect** |
| Halon-1211 | 1750 | 1750 | **1890** | **DB value is incorrect** |
| HCFC-123 | 79 | 79 | **77** | **DB value is incorrect** |
| SF6 | 23500 | 23500 | 23500 | Correct |
| R-1234yf | 1 | <1 | 1 | Correct |

### Recommendation
Decision needed: Switch all refrigerant GWPs to DEFRA 2024 (AR5) for consistency with fuel factors,
or switch everything to AR6 (requires recalculating all DEFRA fuel CO2e values with AR6 GWPs).
Either way, **R-410A (2256), HFC-227ea (3220), Halon-1211 (1890), HCFC-123 (77) are wrong in any system and must be fixed.**

---

## Complete Factor Listing

### Scope 1 - Category 1.1

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| natural_gas_volume | Natural Gas (volume) | 2.06318 | kg CO2e/m3 | DEFRA_2024 | DEFRA 2024 v1.1: Fuels > Gaseous fuels > Natural gas (100... |
| natural_gas_kwh | Natural Gas (energy) | 0.2044 | kg CO2e/kWh | DEFRA_2024 | DEFRA 2024 v1.1: Fuels > Gaseous fuels > Natural gas (100... |
| natural_gas_mmbtu | Natural Gas (MMBTU) | 59.904 | kg CO2e/MMBTU | DEFRA_2024 | Derived: DEFRA 2024 Natural gas (100% mineral) per kWh (N... |
| diesel_liters | Diesel/Gas Oil | 2.66155 | kg CO2e/liter | DEFRA_2024 | DEFRA 2024 v1.1: Fuels > Liquid fuels > Diesel (100% mine... |
| lpg_liters | LPG (volume) | 1.55713 | kg CO2e/liter | DEFRA_2024 | DEFRA 2024 v1.1: Fuels > Gaseous fuels > LPG per litre |
| lpg_kg | LPG (mass) | 2.93936 | kg CO2e/kg | DEFRA_2024 | DEFRA 2024 v1.1: Fuels > Gaseous fuels > LPG per tonne / ... |
| coal_kg | Coal (industrial) | 2.39944 | kg CO2e/kg | DEFRA_2024 | DEFRA 2024 v1.1: Fuels > Solid fuels > Coal (industrial) ... |
| fuel_oil_liters | Fuel Oil | 3.17493 | kg CO2e/liter | DEFRA_2024 | DEFRA 2024 v1.1: Fuels > Liquid fuels > Fuel oil per litre |
| kerosene_liters | Kerosene/Paraffin | 2.54015 | kg CO2e/liter | DEFRA_2024 | DEFRA 2024 v1.1: Fuels > Liquid fuels > Burning oil per l... |
| biodiesel_liters | Biodiesel (B100) | 0.17 | kg CO2e/liter | DEFRA_2024 | Biogenic CO2 excluded per GHG Protocol. Only CH4/N2O emis... |
| cng_kg | CNG (Compressed Natural Gas) | 2.56816 | kg CO2e/kg | DEFRA_2024 | DEFRA 2024 v1.1: Fuels > Gaseous fuels > CNG per tonne / ... |
| lng_liters | LNG (Liquefied Natural Gas) | 1.17216 | kg CO2e/liter | DEFRA_2024 | DEFRA 2024 v1.1: Fuels > Gaseous fuels > LNG per litre |
| hydrogen_kg | Hydrogen (grey/blue) | 0.0 | kg CO2e/kg | DEFRA_2024 | Direct combustion emissions only. Production emissions in... |
| spend_fuel | Fuel Purchases (spend) | 0.85 | kg CO2e/USD | USEEIO_2.0 | Covers gasoline, diesel, and other petroleum fuel purchas... |
| spend_natural_gas | Natural Gas (spend) | 0.72 | kg CO2e/USD | USEEIO_2.0 | Natural gas purchases by spend amount. |

### Scope 1 - Category 1.2

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| car_petrol_km | Petrol Car (average) | 0.16984 | kg CO2e/km | DEFRA_2024 | DEFRA 2024 v1.1: Cars (by fuel) > Average car > Petrol pe... |
| car_diesel_km | Diesel Car (average) | 0.1645 | kg CO2e/km | DEFRA_2024 | DEFRA 2024 v1.1: Cars (by fuel) > Average car > Diesel pe... |
| car_hybrid_km | Hybrid Car (average) | 0.12607 | kg CO2e/km | DEFRA_2024 | DEFRA 2024 v1.1: Cars (by fuel) > Average car > Hybrid pe... |
| van_diesel_km | Diesel Van (average) | 0.25023 | kg CO2e/km | DEFRA_2024 | DEFRA 2024 v1.1: Vans > Average (up to 3.5 tonnes) > Dies... |
| hgv_diesel_km | HGV Truck (average) | 0.89 | kg CO2e/km | DEFRA_2024 |  |
| petrol_liters | Petrol/Gasoline (fuel) | 2.35372 | kg CO2e/liter | DEFRA_2024 | DEFRA 2024 v1.1: Fuels > Liquid fuels > Petrol (100% mine... |
| urea_liters | Urea/AdBlue/DEF (Diesel Exhaust Fluid) | 1.33 | kg CO2e/liter | DEFRA_2024 | AdBlue/DEF used for NOx reduction in diesel vehicles. EF ... |
| diesel_liters_mobile | Diesel (mobile) | 2.66155 | kg CO2e/liter | DEFRA_2024 | Diesel fuel for mobile sources (vehicles, equipment). |
| aviation_fuel_liters | Aviation Fuel (Jet-A/Jet-A1) | 2.54269 | kg CO2e/liter | DEFRA_2024 | For company-owned aircraft. |
| marine_fuel_liters | Marine Fuel Oil | 3.10202 | kg CO2e/liter | DEFRA_2024 | For company-owned vessels. |
| car_ev_km | Electric Car (average) | 0.0 | kg CO2e/km | DEFRA_2024 | Zero direct emissions. Electricity consumption in Scope 2. |
| motorcycle_km | Motorcycle (average) | 0.11337 | kg CO2e/km | DEFRA_2024 | DEFRA 2024 v1.1: Motorbike > Average per km |
| bus_diesel_km | Diesel Bus (average) | 0.82 | kg CO2e/km | DEFRA_2024 |  |
| forklift_lpg_hour | LPG Forklift (per hour) | 2.5 | kg CO2e/hour | DEFRA_2024 | Estimated based on typical LPG consumption of 1.5kg/hour. |
| forklift_diesel_hour | Diesel Forklift (per hour) | 6.7 | kg CO2e/hour | DEFRA_2024 | Estimated based on typical diesel consumption of 2.5L/hour. |

### Scope 1 - Category 1.3

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| refrigerant_r134a | R-134a Refrigerant | 1530 | kg CO2e/kg | IPCC_AR6 |  |
| refrigerant_r410a | R-410A Refrigerant | 2256 | kg CO2e/kg | IPCC_AR6 |  |
| refrigerant_r32 | R-32 Refrigerant | 771 | kg CO2e/kg | IPCC_AR6 |  |
| refrigerant_r404a | R-404A Refrigerant | 4728 | kg CO2e/kg | IPCC_AR6 |  |
| refrigerant_r407c | R-407C Refrigerant | 1774 | kg CO2e/kg | IPCC_AR6 |  |
| refrigerant_r507a | R-507A Refrigerant | 3985 | kg CO2e/kg | IPCC_AR6 |  |
| refrigerant_r227ea | FM-200 / R-227ea (Fire Suppression) | 3220 | kg CO2e/kg | IPCC_AR6 |  |
| refrigerant_r123 | R-123 / HCFC-123 (Phased Out) | 77 | kg CO2e/kg | IPCC_AR6 |  |
| refrigerant_halon1211 | Halon-1211 (Fire Suppression) | 1890 | kg CO2e/kg | IPCC_AR6 |  |
| refrigerant_sf6 | SF6 (Switchgear) | 23500 | kg CO2e/kg | IPCC_AR6 |  |
| refrigerant_r1234yf | R-1234yf (HFO - Low GWP) | 1 | kg CO2e/kg | IPCC_AR6 |  |

### Scope 2 - Category 2

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| electricity_uk | United Kingdom Grid | 0.20705 | kg CO2e/kWh | DEFRA_2024 | DEFRA 2024 v1.1: UK electricity > Electricity generated p... |
| electricity_de | Germany Grid | 0.366 | kg CO2e/kWh | UBA_Germany_2024 |  |
| electricity_fr | France Grid | 0.052 | kg CO2e/kWh | ADEME_France_2024 |  |
| electricity_es | Spain Grid | 0.149 | kg CO2e/kWh | REE_Spain_2024 |  |
| electricity_it | Italy Grid | 0.257 | kg CO2e/kWh | ISPRA_Italy_2024 |  |
| electricity_nl | Netherlands Grid | 0.328 | kg CO2e/kWh | CBS_Netherlands_2024 |  |
| electricity_pl | Poland Grid | 0.653 | kg CO2e/kWh | KOBiZE_Poland_2024 |  |
| electricity_eu | EU Average Grid | 0.230 | kg CO2e/kWh | EEA_2024 |  |
| electricity_us | USA Grid (National Average) | 0.386 | kg CO2e/kWh | EPA_eGRID_2024 |  |
| electricity_us_ca | USA - California Grid | 0.225 | kg CO2e/kWh | EPA_eGRID_2024_CAMX |  |
| electricity_us_tx | USA - Texas Grid (ERCOT) | 0.373 | kg CO2e/kWh | EPA_eGRID_2024_ERCT |  |
| electricity_us_ny | USA - New York Grid | 0.188 | kg CO2e/kWh | EPA_eGRID_2024_NYUP |  |
| electricity_us_mw | USA - Midwest Grid | 0.475 | kg CO2e/kWh | EPA_eGRID_2024_MROW |  |
| electricity_ca | Canada Grid (National Average) | 0.120 | kg CO2e/kWh | Environment_Canada_2024 |  |
| electricity_il | Israel Grid | 0.527 | kg CO2e/kWh | IEC_Israel_2024 |  |
| electricity_jp | Japan Grid | 0.457 | kg CO2e/kWh | MOE_Japan_2024 |  |
| electricity_kr | South Korea Grid | 0.417 | kg CO2e/kWh | KEEI_Korea_2024 |  |
| electricity_cn | China Grid (National Average) | 0.555 | kg CO2e/kWh | NDRC_China_2024 |  |
| electricity_sg | Singapore Grid | 0.408 | kg CO2e/kWh | EMA_Singapore_2024 |  |
| electricity_au | Australia Grid (National Average) | 0.680 | kg CO2e/kWh | DISER_Australia_2024 |  |
| electricity_in | India Grid | 0.708 | kg CO2e/kWh | CEA_India_2024 |  |
| electricity_global | Global Average Grid | 0.436 | kg CO2e/kWh | IEA_World_2024 |  |
| electricity_renewable | 100% Renewable (Certified) | 0.000 | kg CO2e/kWh | Market_Based_Renewable |  |
| electricity_supplier | Supplier Specific Factor | 0.000 | kg CO2e/kWh | Supplier_Disclosure |  |
| electricity_custom | Custom Emission Factor | 1.000 | kg CO2e/kWh | User_Provided | Use _custom_ef field in row data for actual emission factor |
| electricity_residual_mix | Residual Mix (EU Average) | 0.453 | kg CO2e/kWh | AIB_Residual_2024 |  |
| district_heat_kwh | District Heating | 0.17965 | kg CO2e/kWh | DEFRA_2024 | DEFRA 2024 v1.1: Heat and steam > District heat and steam... |
| steam_kwh | Steam | 0.17965 | kg CO2e/kWh | DEFRA_2024 | DEFRA 2024 v1.1: Heat and steam > Onsite heat and steam p... |
| energy_supplier | Supplier-Specific Energy | 1.000 | kg CO2e/kWh | User_Provided | Use _supplier_ef field in row data for actual emission fa... |
| spend_electricity | Electricity (spend) | 0.45 | kg CO2e/USD | USEEIO_2.0 | Electricity purchases by spend amount. Based on average U... |
| spend_heat_steam | District Heat/Steam (spend) | 0.38 | kg CO2e/USD | USEEIO_2.0 | District heating or steam purchases by spend amount. |

### Scope 2 - Category 2.3

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| district_cooling_kwh | District Cooling | 0.17965 | kg CO2e/kWh | DEFRA_2024 | DEFRA 2024 v1.1: Heat and steam > District heat and steam... |

### Scope 3 - Category 3.1

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| spend_office_supplies | Office Supplies (spend) | 0.35 | kg CO2e/USD | USEEIO_2.0 |  |
| spend_it_equipment | IT Equipment (spend) | 0.42 | kg CO2e/USD | USEEIO_2.0 |  |
| spend_professional_services | Professional Services (spend) | 0.22 | kg CO2e/USD | USEEIO_2.0 |  |
| spend_food_beverages | Food & Beverages (spend) | 0.68 | kg CO2e/USD | USEEIO_2.0 |  |
| spend_other | Other Purchases (spend) | 0.30 | kg CO2e/USD | USEEIO_2.0 |  |
| spend_it_services | IT Services (spend) | 0.25 | kg CO2e/USD | USEEIO_2.0 |  |
| spend_legal_services | Legal Services (spend) | 0.18 | kg CO2e/USD | USEEIO_2.0 |  |
| spend_marketing | Marketing & Advertising (spend) | 0.28 | kg CO2e/USD | USEEIO_2.0 |  |
| spend_cleaning_services | Cleaning Services (spend) | 0.20 | kg CO2e/USD | USEEIO_2.0 |  |
| spend_telecommunications | Telecommunications (spend) | 0.32 | kg CO2e/USD | USEEIO_2.0 |  |
| spend_insurance | Insurance Services (spend) | 0.12 | kg CO2e/USD | USEEIO_2.0 |  |
| spend_banking | Banking & Financial Services (spend) | 0.10 | kg CO2e/USD | USEEIO_2.0 |  |
| spend_printing | Printing Services (spend) | 0.45 | kg CO2e/USD | USEEIO_2.0 |  |
| spend_furniture | Furniture (spend) | 0.38 | kg CO2e/USD | USEEIO_2.0 |  |
| spend_chemicals | Chemicals (spend) | 0.55 | kg CO2e/USD | USEEIO_2.0 |  |
| steel_purchased_kg | Steel (purchased) | 1.85 | kg CO2e/kg | World_Steel_Association_2023 |  |
| aluminum_primary_purchased_kg | Aluminum - Primary (purchased) | 16.5 | kg CO2e/kg | IAI_2023 |  |
| aluminum_recycled_purchased_kg | Aluminum - Recycled (purchased) | 0.5 | kg CO2e/kg | IAI_2023 |  |
| plastic_pet_purchased_kg | Plastic - PET (purchased) | 2.73 | kg CO2e/kg | DEFRA_2024 |  |
| plastic_hdpe_purchased_kg | Plastic - HDPE (purchased) | 1.93 | kg CO2e/kg | DEFRA_2024 |  |
| plastic_generic_purchased_kg | Plastic - Average (purchased) | 3.10 | kg CO2e/kg | DEFRA_2024 |  |
| paper_virgin_purchased_kg | Paper - Virgin (purchased) | 0.92 | kg CO2e/kg | DEFRA_2024 |  |
| paper_recycled_purchased_kg | Paper - Recycled (purchased) | 0.61 | kg CO2e/kg | DEFRA_2024 |  |
| cardboard_purchased_kg | Cardboard (purchased) | 0.79 | kg CO2e/kg | DEFRA_2024 |  |
| glass_purchased_kg | Glass (purchased) | 0.86 | kg CO2e/kg | DEFRA_2024 |  |
| concrete_purchased_kg | Concrete (purchased) | 0.13 | kg CO2e/kg | DEFRA_2024 |  |
| textiles_cotton_purchased_kg | Textiles - Cotton (purchased) | 8.0 | kg CO2e/kg | DEFRA_2024 |  |
| textiles_polyester_purchased_kg | Textiles - Polyester (purchased) | 5.5 | kg CO2e/kg | DEFRA_2024 |  |
| electronics_purchased_kg | Electronics (purchased) | 20.0 | kg CO2e/kg | DEFRA_2024 |  |
| food_meat_purchased_kg | Food - Meat (purchased) | 13.0 | kg CO2e/kg | DEFRA_2024 |  |
| food_dairy_purchased_kg | Food - Dairy (purchased) | 3.2 | kg CO2e/kg | DEFRA_2024 |  |
| food_vegetables_purchased_kg | Food - Vegetables (purchased) | 0.5 | kg CO2e/kg | DEFRA_2024 |  |

### Scope 3 - Category 3.10

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| processing_steel_kg | Processing - Steel/Iron | 1.85 | kg CO2e/kg | DEFRA_2024 |  |
| processing_aluminum_kg | Processing - Aluminum | 8.14 | kg CO2e/kg | DEFRA_2024 |  |
| processing_metal_kg | Processing - Metal (General) | 2.50 | kg CO2e/kg | DEFRA_2024 |  |
| processing_plastic_kg | Processing - Plastic/Polymer | 3.10 | kg CO2e/kg | DEFRA_2024 |  |
| processing_chemical_kg | Processing - Chemical/Petrochemical | 2.80 | kg CO2e/kg | DEFRA_2024 |  |
| processing_textile_kg | Processing - Textile/Fabric | 5.50 | kg CO2e/kg | DEFRA_2024 |  |
| processing_paper_kg | Processing - Paper/Pulp | 0.92 | kg CO2e/kg | DEFRA_2024 |  |
| processing_glass_kg | Processing - Glass | 0.86 | kg CO2e/kg | DEFRA_2024 |  |
| processing_food_kg | Processing - Food/Agricultural | 0.75 | kg CO2e/kg | DEFRA_2024 |  |
| processing_electronics_kg | Processing - Electronics/Components | 12.50 | kg CO2e/kg | DEFRA_2024 |  |
| processing_wood_kg | Processing - Wood/Timber | 0.45 | kg CO2e/kg | DEFRA_2024 |  |
| processing_generic_kg | Processing - Generic/Other | 2.00 | kg CO2e/kg | DEFRA_2024 |  |
| processing_energy_kwh | Processing - Energy (site-specific) | 0.436 | kg CO2e/kWh | IEA_World_2024 |  |
| processing_spend_manufacturing | Processing - Manufacturing (spend) | 0.38 | kg CO2e/USD | USEEIO_2.0 |  |

### Scope 3 - Category 3.11

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| use_phase_electricity_kwh | Use Phase - Electricity Consumption | 0.436 | kg CO2e/kWh | IEA_World_2024 |  |
| use_phase_petrol_liters | Use Phase - Petrol/Gasoline | 2.31 | kg CO2e/liter | DEFRA_2024 |  |
| use_phase_diesel_liters | Use Phase - Diesel | 2.68 | kg CO2e/liter | DEFRA_2024 |  |
| use_phase_natural_gas_kwh | Use Phase - Natural Gas | 0.184 | kg CO2e/kWh | DEFRA_2024 |  |
| use_phase_lpg_liters | Use Phase - LPG | 1.51 | kg CO2e/liter | DEFRA_2024 |  |
| use_phase_vehicle_km | Use Phase - Vehicle (per km) | 0.171 | kg CO2e/km | DEFRA_2024 |  |
| use_phase_building_m2_year | Use Phase - Building (per m²-year) | 45.0 | kg CO2e/m²-year | DEFRA_2024 |  |
| use_phase_spend_products | Use Phase - Products (spend) | 0.25 | kg CO2e/USD | USEEIO_2.0 |  |

### Scope 3 - Category 3.12

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| eol_recycling_metal | Metal Recycling (EOL) | 0.021 | kg CO2e/kg | DEFRA_2024 |  |
| eol_recycling_plastic | Plastic Recycling (EOL) | 0.021 | kg CO2e/kg | DEFRA_2024 |  |
| eol_recycling_paper | Paper/Cardboard Recycling (EOL) | 0.021 | kg CO2e/kg | DEFRA_2024 |  |
| eol_recycling_glass | Glass Recycling (EOL) | 0.021 | kg CO2e/kg | DEFRA_2024 |  |
| eol_recycling_ewaste | E-Waste Recycling (EOL) | 0.021 | kg CO2e/kg | DEFRA_2024 |  |
| eol_recycling_textile | Textile Recycling (EOL) | 0.021 | kg CO2e/kg | DEFRA_2024 |  |
| eol_recycling_mixed | Mixed Recycling (EOL) | 0.021 | kg CO2e/kg | DEFRA_2024 |  |
| eol_landfill_organic | Organic Waste to Landfill (EOL) | 0.587 | kg CO2e/kg | DEFRA_2024 |  |
| eol_landfill_plastic | Plastic to Landfill (EOL) | 0.010 | kg CO2e/kg | DEFRA_2024 |  |
| eol_landfill_paper | Paper to Landfill (EOL) | 1.042 | kg CO2e/kg | DEFRA_2024 |  |
| eol_landfill_wood | Wood to Landfill (EOL) | 0.735 | kg CO2e/kg | DEFRA_2024 |  |
| eol_landfill_textile | Textile to Landfill (EOL) | 0.587 | kg CO2e/kg | DEFRA_2024 |  |
| eol_landfill_mixed | Mixed Waste to Landfill (EOL) | 0.460 | kg CO2e/kg | DEFRA_2024 |  |
| eol_incineration | Incineration without Energy Recovery (EOL) | 0.918 | kg CO2e/kg | DEFRA_2024 |  |
| eol_incineration_energy | Incineration with Energy Recovery (EOL) | 0.429 | kg CO2e/kg | DEFRA_2024 |  |
| eol_composting | Composting (EOL) | 0.010 | kg CO2e/kg | DEFRA_2024 |  |
| eol_anaerobic_digestion | Anaerobic Digestion (EOL) | 0.010 | kg CO2e/kg | DEFRA_2024 |  |
| eol_ewaste_mixed | E-Waste Mixed Treatment (EOL) | 0.500 | kg CO2e/kg | EPA_2024 |  |
| eol_batteries | Batteries EOL Treatment | 0.750 | kg CO2e/kg | EPA_2024 |  |
| eol_hazardous | Hazardous Waste Treatment (EOL) | 1.200 | kg CO2e/kg | EPA_2024 |  |
| eol_spend_disposal | EOL Treatment (spend) | 0.40 | kg CO2e/USD | USEEIO_2.0 |  |

### Scope 3 - Category 3.13

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| downstream_leased_office_m2 | Leased Office Building (per m2) | 0.150 | kg CO2e/m2 | DEFRA_2024 |  |
| downstream_leased_warehouse_m2 | Leased Warehouse (per m2) | 0.080 | kg CO2e/m2 | DEFRA_2024 |  |
| downstream_leased_retail_m2 | Leased Retail Space (per m2) | 0.200 | kg CO2e/m2 | DEFRA_2024 |  |
| downstream_leased_industrial_m2 | Leased Industrial Space (per m2) | 0.120 | kg CO2e/m2 | DEFRA_2024 |  |
| downstream_leased_datacenter_m2 | Leased Data Center (per m2) | 1.500 | kg CO2e/m2 | DEFRA_2024 |  |
| downstream_leased_residential_m2 | Leased Residential (per m2) | 0.100 | kg CO2e/m2 | DEFRA_2024 |  |
| downstream_leased_vehicle_unit | Leased Vehicle (per unit) | 2500.0 | kg CO2e/unit | DEFRA_2024 |  |
| downstream_leased_equipment_unit | Leased Equipment (per unit) | 500.0 | kg CO2e/unit | EPA_2024 |  |
| downstream_leased_electricity_kwh | Leased Asset Electricity | 0.436 | kg CO2e/kWh | IEA_2024 |  |
| downstream_leased_gas_kwh | Leased Asset Natural Gas | 0.184 | kg CO2e/kWh | DEFRA_2024 |  |
| downstream_leased_spend_income | Downstream Leased Assets (spend) | 0.15 | kg CO2e/USD | USEEIO_2.0 |  |

### Scope 3 - Category 3.14

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| franchise_restaurant_unit | Restaurant Franchise (per unit) | 50000.0 | kg CO2e/unit | EPA_2024 |  |
| franchise_fastfood_unit | Fast Food Franchise (per unit) | 35000.0 | kg CO2e/unit | EPA_2024 |  |
| franchise_cafe_unit | Cafe/Coffee Franchise (per unit) | 20000.0 | kg CO2e/unit | EPA_2024 |  |
| franchise_retail_m2 | Retail Franchise (per m2) | 200.0 | kg CO2e/m2 | DEFRA_2024 |  |
| franchise_convenience_unit | Convenience Store Franchise (per unit) | 25000.0 | kg CO2e/unit | EPA_2024 |  |
| franchise_hotel_room | Hotel Franchise (per room) | 3500.0 | kg CO2e/room | DEFRA_2024 |  |
| franchise_gym_m2 | Gym/Fitness Franchise (per m2) | 150.0 | kg CO2e/m2 | DEFRA_2024 |  |
| franchise_service_unit | Service Franchise (per unit) | 15000.0 | kg CO2e/unit | EPA_2024 |  |
| franchise_office_m2 | Office Franchise (per m2) | 120.0 | kg CO2e/m2 | DEFRA_2024 |  |
| franchise_gasstation_unit | Gas Station Franchise (per unit) | 100000.0 | kg CO2e/unit | EPA_2024 |  |
| franchise_generic_unit | Generic Franchise (per unit) | 30000.0 | kg CO2e/unit | EPA_2024 |  |
| franchise_electricity_kwh | Franchise Electricity | 0.436 | kg CO2e/kWh | IEA_2024 |  |
| franchise_gas_kwh | Franchise Natural Gas | 0.184 | kg CO2e/kWh | DEFRA_2024 |  |
| franchise_fuel_liters | Franchise Fuel (Diesel/Petrol) | 2.68 | kg CO2e/liter | DEFRA_2024 |  |
| franchise_spend_revenue | Franchises (spend) | 0.20 | kg CO2e/USD | USEEIO_2.0 |  |

### Scope 3 - Category 3.2

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| spend_capital_equipment | Capital Equipment (spend) | 0.35 | kg CO2e/USD | USEEIO_2.0 |  |
| spend_construction | Construction (spend) | 0.45 | kg CO2e/USD | USEEIO_2.0 |  |
| capital_vehicle_unit | Vehicle - Car (per unit) | 6000 | kg CO2e/unit | DEFRA_2024 |  |
| capital_truck_unit | Vehicle - Truck/HGV (per unit) | 15000 | kg CO2e/unit | DEFRA_2024 |  |
| capital_computer_unit | Computer/Laptop (per unit) | 300 | kg CO2e/unit | Industry_LCA_Apple_Dell |  |
| capital_server_unit | Server (per unit) | 1500 | kg CO2e/unit | Industry_LCA |  |
| capital_building_m2 | Building Construction (per m²) | 500 | kg CO2e/m2 | RICS_CRREM_2023 |  |

### Scope 3 - Category 3.3

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| wtt_natural_gas_m3 | WTT - Natural Gas | 0.3366 | kg CO2e/m3 | DEFRA_2024 | DEFRA 2024 v1.1: WTT fuels > Natural gas (100% mineral bl... |
| wtt_diesel_liters | WTT - Diesel | 0.62409 | kg CO2e/liter | DEFRA_2024 | DEFRA 2024 v1.1: WTT fuels > Diesel (100% mineral diesel)... |
| wtt_electricity_kwh | WTT - Electricity (generation + T&D losses) | 0.04987 | kg CO2e/kWh | DEFRA_2024 | DEFRA 2024 v1.1: WTT UK electricity generation (0.0459) +... |
| wtt_petrol_liters | WTT - Petrol | 0.60664 | kg CO2e/liter | DEFRA_2024 | DEFRA 2024 v1.1: WTT fuels > Petrol (100% mineral petrol)... |
| wtt_natural_gas_kwh | WTT - Natural Gas (kWh) | 0.03347 | kg CO2e/kWh | DEFRA_2024 | DEFRA 2024 v1.1: WTT fuels > Natural gas (100% mineral bl... |
| wtt_lpg_liters | WTT - LPG | 0.18551 | kg CO2e/liter | DEFRA_2024 | DEFRA 2024 v1.1: WTT fuels > LPG per litre |
| wtt_lng_liters | WTT - LNG | 0.41277 | kg CO2e/liter | DEFRA_2024 | DEFRA 2024 v1.1: WTT fuels > LNG per litre |
| wtt_coal_kg | WTT - Coal | 0.41815 | kg CO2e/kg | DEFRA_2024 | DEFRA 2024 v1.1: WTT fuels > Coal (industrial) per tonne ... |
| wtt_fuel_oil_liters | WTT - Fuel Oil | 0.69539 | kg CO2e/liter | DEFRA_2024 | DEFRA 2024 v1.1: WTT fuels > Fuel oil per litre |
| wtt_car_petrol_km | WTT - Petrol Car | 0.04 | kg CO2e/km | DEFRA_2024 |  |
| wtt_car_diesel_km | WTT - Diesel Car | 0.04 | kg CO2e/km | DEFRA_2024 |  |
| wtt_hgv_diesel_km | WTT - HGV Diesel | 0.22 | kg CO2e/km | DEFRA_2024 |  |
| wtt_van_diesel_km | WTT - Diesel Van | 0.06 | kg CO2e/km | DEFRA_2024 |  |
| wtt_aviation_km | WTT - Aviation Fuel | 0.012 | kg CO2e/passenger-km | DEFRA_2024 |  |
| wtt_rail_km | WTT - Rail | 0.008 | kg CO2e/passenger-km | DEFRA_2024 |  |

### Scope 3 - Category 3.4

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| road_freight_hgv | Road Freight - HGV (average) | 0.09752 | kg CO2e/tonne-km | DEFRA_2024 | DEFRA 2024 v1.1: Freighting goods > HGV (all diesel) > Al... |
| road_freight_van | Road Freight - Van | 0.62264 | kg CO2e/tonne-km | DEFRA_2024 | DEFRA 2024 v1.1: Freighting goods > Vans > Average (up to... |
| rail_freight | Rail Freight | 0.02778 | kg CO2e/tonne-km | DEFRA_2024 | DEFRA 2024 v1.1: Freighting goods > Rail > Average per to... |
| sea_freight_container | Sea Freight - Container Ship | 0.01612 | kg CO2e/tonne-km | DEFRA_2024 | DEFRA 2024 v1.1: Freighting goods > Cargo ship > Containe... |
| sea_freight_bulk | Sea Freight - Bulk Carrier | 0.00353 | kg CO2e/tonne-km | DEFRA_2024 | DEFRA 2024 v1.1: Freighting goods > Cargo ship > Bulk car... |
| air_freight | Air Freight | 1.130 | kg CO2e/tonne-km | DEFRA_2024 |  |
| freight_spend_road | Road Freight (spend) | 0.56 | kg CO2e/USD | USEEIO_2.0 |  |
| freight_spend_air | Air Freight (spend) | 1.20 | kg CO2e/USD | USEEIO_2.0 |  |
| freight_spend_sea | Sea Freight (spend) | 0.35 | kg CO2e/USD | USEEIO_2.0 |  |
| freight_spend_courier | Courier/Parcel (spend) | 0.80 | kg CO2e/USD | USEEIO_2.0 |  |

### Scope 3 - Category 3.5

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| waste_landfill_mixed | Mixed Waste to Landfill | 0.58 | kg CO2e/kg | DEFRA_2024 |  |
| waste_recycled_mixed | Mixed Waste Recycled | 0.02 | kg CO2e/kg | DEFRA_2024 |  |
| waste_incineration | Waste Incinerated | 0.02 | kg CO2e/kg | DEFRA_2024 |  |
| waste_recycled_paper | Paper/Cardboard Recycled | 0.02 | kg CO2e/kg | DEFRA_2024 |  |
| waste_recycled_plastic | Plastic Recycled | 0.02 | kg CO2e/kg | DEFRA_2024 |  |
| waste_landfill_food | Food Waste - Landfill | 0.59 | kg CO2e/kg | DEFRA_2024 |  |
| waste_composted_food | Food Waste - Composted | 0.01 | kg CO2e/kg | DEFRA_2024 |  |
| waste_anaerobic_food | Food Waste - Anaerobic Digestion | 0.01 | kg CO2e/kg | DEFRA_2024 |  |
| waste_recycled_metal | Metal Waste - Recycled | 0.02 | kg CO2e/kg | DEFRA_2024 |  |
| waste_recycled_glass | Glass Waste - Recycled | 0.02 | kg CO2e/kg | DEFRA_2024 |  |
| waste_ewaste | Electronic Waste (WEEE) | 0.50 | kg CO2e/kg | DEFRA_2024 |  |
| waste_construction | Construction & Demolition Waste | 0.01 | kg CO2e/kg | DEFRA_2024 |  |
| waste_disposal_spend | Waste Disposal Services (spend) | 0.40 | kg CO2e/USD | USEEIO_2.0 |  |

### Scope 3 - Category 3.6

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| flight_short_economy | Short-haul Flight (Economy) | 0.18287 | kg CO2e/passenger-km | DEFRA_2024 | DEFRA 2024 v1.1: Business travel-air > Short-haul > Econo... |
| flight_long_economy | Long-haul Flight (Economy) | 0.20011 | kg CO2e/passenger-km | DEFRA_2024 | DEFRA 2024 v1.1: Business travel-air > Long-haul > Econom... |
| flight_long_business | Long-haul Flight (Business) | 0.58028 | kg CO2e/passenger-km | DEFRA_2024 | DEFRA 2024 v1.1: Business travel-air > Long-haul > Busine... |
| hotel_night | Hotel Stay | 14.6 | kg CO2e/night | DEFRA_2024 |  |
| rail_km | Rail Travel | 0.03546 | kg CO2e/passenger-km | DEFRA_2024 | DEFRA 2024 v1.1: Business travel-land > National rail per... |
| flight_short_business | Short-haul Flight (Business) | 0.2743 | kg CO2e/passenger-km | DEFRA_2024 | DEFRA 2024 v1.1: Business travel-air > Short-haul > Busin... |
| flight_long_first | Long-haul Flight (First Class) | 0.8004 | kg CO2e/passenger-km | DEFRA_2024 | DEFRA 2024 v1.1: Business travel-air > Long-haul > First ... |
| rental_car_km | Rental Car (average) | 0.16984 | kg CO2e/km | DEFRA_2024 | DEFRA 2024 v1.1: Cars (by fuel) > Average car > Petrol pe... |
| rail_domestic_km | Domestic Rail | 0.03546 | kg CO2e/passenger-km | DEFRA_2024 | DEFRA 2024 v1.1: Business travel-land > National rail per... |
| rail_international_km | International Rail (Eurostar-type) | 0.00446 | kg CO2e/passenger-km | DEFRA_2024 | DEFRA 2024 v1.1: Business travel-land > International rai... |
| taxi_km | Taxi | 0.20805 | kg CO2e/km | DEFRA_2024 | DEFRA 2024 v1.1: Taxis > Regular taxi per km |
| travel_spend_air | Air Travel (spend) | 0.95 | kg CO2e/USD | USEEIO_2.0 |  |
| travel_spend_hotel | Hotel Accommodation (spend) | 0.25 | kg CO2e/USD | USEEIO_2.0 |  |
| travel_spend_car_rental | Car Rental (spend) | 0.35 | kg CO2e/USD | USEEIO_2.0 |  |
| travel_spend_rail | Rail Travel (spend) | 0.15 | kg CO2e/USD | USEEIO_2.0 |  |
| travel_spend_taxi | Taxi/Rideshare (spend) | 0.40 | kg CO2e/USD | USEEIO_2.0 |  |
| travel_spend_general | Business Travel - General (spend) | 0.50 | kg CO2e/USD | USEEIO_2.0 |  |

### Scope 3 - Category 3.7

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| commute_car_petrol | Commute - Petrol Car | 0.16984 | kg CO2e/km | DEFRA_2024 | DEFRA 2024 v1.1: Cars (by fuel) > Average car > Petrol pe... |
| commute_bus | Commute - Bus | 0.10312 | kg CO2e/km | DEFRA_2024 | DEFRA 2024 v1.1: Bus > Average local bus per passenger.km |
| commute_rail | Commute - Rail | 0.03546 | kg CO2e/km | DEFRA_2024 | DEFRA 2024 v1.1: Business travel-land > National rail per... |
| commute_bicycle | Commute - Bicycle | 0 | kg CO2e/km | DEFRA_2024 |  |
| commute_car_electric | Commute - Electric Car | 0.05 | kg CO2e/km | DEFRA_2024 |  |
| commute_motorcycle | Commute - Motorcycle | 0.11337 | kg CO2e/km | DEFRA_2024 | DEFRA 2024 v1.1: Motorbike > Average per km |
| commute_ebike | Commute - E-bike | 0.005 | kg CO2e/km | DEFRA_2024 |  |
| commute_wfh_day | Work from Home (per day) | 0.5 | kg CO2e/day | IEA_Various |  |
| commute_spend_general | Commuting Reimbursement (spend) | 0.35 | kg CO2e/USD | USEEIO_2.0 |  |
| commute_car_diesel | Commute - Diesel Car | 0.1645 | kg CO2e/km | DEFRA_2024 | DEFRA 2024 v1.1: Cars (by fuel) > Average car > Diesel pe... |
| commute_car_hybrid | Commute - Hybrid Car | 0.12607 | kg CO2e/km | DEFRA_2024 | DEFRA 2024 v1.1: Cars (by fuel) > Average car > Hybrid pe... |
| commute_walk | Commute - Walk | 0 | kg CO2e/km | DEFRA_2024 |  |

### Scope 3 - Category 3.8

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| leased_office_m2_year | Leased Office Space (per m² per year) | 50 | kg CO2e/m2/year | CRREM_2023 |  |
| leased_warehouse_m2_year | Leased Warehouse (per m² per year) | 35 | kg CO2e/m2/year | CRREM_2023 |  |
| leased_retail_m2_year | Leased Retail Space (per m² per year) | 100 | kg CO2e/m2/year | CRREM_2023 |  |
| leased_datacenter_m2_year | Leased Data Center (per m² per year) | 1000 | kg CO2e/m2/year | Industry_Average |  |
| leased_spend_rent | Leased Property Rent (spend) | 0.15 | kg CO2e/USD | USEEIO_2.0 |  |
| leased_electricity_kwh | Leased Assets - Electricity (known) | 0.436 | kg CO2e/kWh | IEA_World_2024 |  |

### Scope 3 - Category 3.9

| Activity Key | Display Name | CO2e Factor | Unit | Source | Notes |
|-------------|-------------|------------|------|--------|-------|
| delivery_van | Delivery Van (last mile) | 0.605 | kg CO2e/tonne-km | DEFRA_2024 |  |
| delivery_hgv | Delivery HGV | 0.107 | kg CO2e/tonne-km | DEFRA_2024 |  |
| delivery_spend_road | Delivery - Road (spend) | 0.56 | kg CO2e/USD | USEEIO_2.0 |  |
| delivery_spend_courier | Delivery - Courier/Parcel (spend) | 0.80 | kg CO2e/USD | USEEIO_2.0 |  |
| delivery_spend_general | Delivery/Distribution - General (spend) | 0.60 | kg CO2e/USD | USEEIO_2.0 |  |

---

## Detailed GHG Breakdown (Scope 1 Fuels)

| Activity Key | CO2e | CO2 | CH4 | N2O | DEFRA Reference |
|-------------|------|-----|-----|-----|-----------------|
| natural_gas_volume | 2.06318 | 2.05916 | 0.00307 | 0.00095 | DEFRA 2024 v1.1: Fuels > Gaseous fuels > Natural gas (100% mineral blend) per cubic metre |
| natural_gas_kwh | 0.2044 | 0.20399 | 0.00031 | 0.0001 | DEFRA 2024 v1.1: Fuels > Gaseous fuels > Natural gas (100% mineral blend) per kWh (Net CV) |
| natural_gas_mmbtu | 59.904 | 59.79 | 0.09083 | 0.02931 | Derived: DEFRA 2024 Natural gas (100% mineral) per kWh (Net CV) x 293.07107 kWh/MMBTU |
| diesel_liters | 2.66155 | 2.62818 | 0.00029 | 0.03308 | DEFRA 2024 v1.1: Fuels > Liquid fuels > Diesel (100% mineral diesel) per litre |
| lpg_liters | 1.55713 | 1.55491 | 0.00136 | 0.00086 | DEFRA 2024 v1.1: Fuels > Gaseous fuels > LPG per litre |
| lpg_kg | 2.93936 | 2.93518 | 0.00255 | 0.00163 | DEFRA 2024 v1.1: Fuels > Gaseous fuels > LPG per tonne / 1000 |
| coal_kg | 2.39944 | 2.37487 | 0.00764 | 0.01693 | DEFRA 2024 v1.1: Fuels > Solid fuels > Coal (industrial) per tonne / 1000 |
| fuel_oil_liters | 3.17493 | 3.16262 | 0.0053 | 0.00701 | DEFRA 2024 v1.1: Fuels > Liquid fuels > Fuel oil per litre |
| kerosene_liters | 2.54015 | 2.52782 | 0.00674 | 0.00559 | DEFRA 2024 v1.1: Fuels > Liquid fuels > Burning oil per litre |
| biodiesel_liters | 0.17 | 0.0 | 0.0001 | 0.0001 |  |
| cng_kg | 2.56816 | 2.56312 | 0.00385 | 0.00119 | DEFRA 2024 v1.1: Fuels > Gaseous fuels > CNG per tonne / 1000 |
| lng_liters | 1.17216 | 1.16987 | 0.00175 | 0.00054 | DEFRA 2024 v1.1: Fuels > Gaseous fuels > LNG per litre |
| hydrogen_kg | 0.0 | 0.0 | 0.0 | 0.0001 |  |
| spend_fuel | 0.85 | - | - | - |  |
| spend_natural_gas | 0.72 | - | - | - |  |
| car_petrol_km | 0.16984 | - | - | - | DEFRA 2024 v1.1: Cars (by fuel) > Average car > Petrol per km |
| car_diesel_km | 0.1645 | - | - | - | DEFRA 2024 v1.1: Cars (by fuel) > Average car > Diesel per km |
| car_hybrid_km | 0.12607 | - | - | - | DEFRA 2024 v1.1: Cars (by fuel) > Average car > Hybrid per km |
| van_diesel_km | 0.25023 | - | - | - | DEFRA 2024 v1.1: Vans > Average (up to 3.5 tonnes) > Diesel per km |
| hgv_diesel_km | 0.89 | - | - | - |  |
| petrol_liters | 2.35372 | 2.33955 | 0.0082 | 0.00597 | DEFRA 2024 v1.1: Fuels > Liquid fuels > Petrol (100% mineral petrol) per litre |
| urea_liters | 1.33 | - | - | - |  |
| diesel_liters_mobile | 2.66155 | 2.62818 | 0.00029 | 0.03308 |  |
| aviation_fuel_liters | 2.54269 | 2.51973 | 0.00176 | 0.0212 |  |
| marine_fuel_liters | 3.10202 | 3.06194 | 0.0014 | 0.03868 |  |
| car_ev_km | 0.0 | - | - | - |  |
| motorcycle_km | 0.11337 | - | - | - | DEFRA 2024 v1.1: Motorbike > Average per km |
| bus_diesel_km | 0.82 | - | - | - |  |
| forklift_lpg_hour | 2.5 | - | - | - |  |
| forklift_diesel_hour | 6.7 | - | - | - |  |

---

## WTT (Well-to-Tank) Factors - Scope 3.3

| Activity Key | CO2e Factor | Unit | DEFRA Reference |
|-------------|------------|------|-----------------|
| wtt_natural_gas_m3 | 0.3366 | kg CO2e/m3 | DEFRA 2024 v1.1: WTT fuels > Natural gas (100% mineral blend) per cubic metre |
| wtt_diesel_liters | 0.62409 | kg CO2e/liter | DEFRA 2024 v1.1: WTT fuels > Diesel (100% mineral diesel) per litre |
| wtt_electricity_kwh | 0.04987 | kg CO2e/kWh | DEFRA 2024 v1.1: WTT UK electricity generation (0.0459) + T&D (0.00397) = 0.04987 per kWh |
| wtt_petrol_liters | 0.60664 | kg CO2e/liter | DEFRA 2024 v1.1: WTT fuels > Petrol (100% mineral petrol) per litre |
| wtt_natural_gas_kwh | 0.03347 | kg CO2e/kWh | DEFRA 2024 v1.1: WTT fuels > Natural gas (100% mineral blend) per kWh (Net CV) |
| wtt_lpg_liters | 0.18551 | kg CO2e/liter | DEFRA 2024 v1.1: WTT fuels > LPG per litre |
| wtt_lng_liters | 0.41277 | kg CO2e/liter | DEFRA 2024 v1.1: WTT fuels > LNG per litre |
| wtt_coal_kg | 0.41815 | kg CO2e/kg | DEFRA 2024 v1.1: WTT fuels > Coal (industrial) per tonne / 1000 |
| wtt_fuel_oil_liters | 0.69539 | kg CO2e/liter | DEFRA 2024 v1.1: WTT fuels > Fuel oil per litre |
| wtt_car_petrol_km | 0.04 | kg CO2e/km |  |
| wtt_car_diesel_km | 0.04 | kg CO2e/km |  |
| wtt_hgv_diesel_km | 0.22 | kg CO2e/km |  |
| wtt_van_diesel_km | 0.06 | kg CO2e/km |  |
| wtt_aviation_km | 0.012 | kg CO2e/passenger-km |  |
| wtt_rail_km | 0.008 | kg CO2e/passenger-km |  |

---

## Change Log

### 2026-02-11: Major Factor Correction
- **Root cause**: All DEFRA-sourced values were manually entered with incorrect values (not from official spreadsheet)
- **Fix**: Replaced ALL DEFRA-sourced emission factors with exact values from official DEFRA 2024 v1.1 flat file
- **Source file**: ghg-conversion-factors-2024-FlatFormat_v1_1.xlsx (531KB, downloaded from gov.uk)
- **Key changes**:
  - Diesel: 2.68 → 2.66155 (was +0.69% too high)
  - Petrol: 2.31 → 2.35372 (was -1.86% too low)
  - LPG: 1.52 → 1.55713 (was -2.39% too low)
  - LNG: 1.23 → 1.17216 (was +4.93% too high)
  - Natural Gas/kWh: 0.183 → 0.2044 (was -9.71% too low)
  - All CO2/CH4/N2O breakdowns corrected
  - All WTT factors corrected
  - All flight factors corrected (now use 'with RF' variant)
  - All freight factors corrected
  - Added missing WTT LNG factor (0.41277 kg CO2e/litre)
  - Added missing LNG mapping in wtt.py
  - Added missing diesel_liters_mobile mapping in wtt.py
  - Updated refrigerant.py fallback GWP dictionary to match DB values
- **Pending**: Refrigerant GWP source decision (AR5 vs AR6)

**Total factors in system: 259**