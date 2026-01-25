"""
Sheet configuration for template parser.

Defines how each sheet in the template should be parsed,
including column mappings and activity_key resolution.
"""
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class SheetConfig:
    """Configuration for parsing a single sheet."""
    sheet_name: str
    scope: int
    category_code: str
    header_row: int = 5  # Row where headers are (1-indexed)
    
    # Column name mappings (template column -> standard field)
    column_map: dict = None
    
    # How to determine activity_key from row data
    activity_key_resolver: Optional[Callable] = None
    
    # Whether this sheet uses spend-based calculation
    is_spend_based: bool = False
    
    # Default unit if not specified
    default_unit: str = None


# =============================================================================
# Activity Key Resolvers
# =============================================================================

def resolve_stationary_fuel(row: dict) -> tuple[str, str]:
    """Resolve activity_key for stationary combustion fuels."""
    # Support both legacy and generated template column names
    fuel_type = (row.get('Fuel_Type') or row.get('Fuel Type') or '').lower().strip()
    calc_type = (row.get('Calc_Type') or row.get('Method') or '').lower().strip()
    input_unit = (row.get('Physical_Unit') or row.get('Unit/Currency') or '').lower().strip()

    # Spend-based - use spend_other as generic spend factor
    if calc_type == 'spend':
        return 'spend_other', 'USD'

    # Check if user provided energy units (kWh, MWh, etc.)
    is_energy_unit = 'kwh' in input_unit or 'mwh' in input_unit or 'wh' in input_unit

    # Natural gas can be in volume (m3) or energy (kWh)
    if 'natural gas' in fuel_type:
        if is_energy_unit:
            return 'natural_gas_kwh', 'kWh'
        else:
            return 'natural_gas_volume', 'm3'

    # Physical-based fuel mapping (using existing activity_keys from emission_factors)
    fuel_map = {
        'diesel': ('diesel_liters', 'liters'),
        'petrol': ('petrol_liters', 'liters'),
        'gasoline': ('petrol_liters', 'liters'),
        'lpg': ('lpg_liters', 'liters'),
        'coal': ('coal_kg', 'kg'),
        'fuel oil': ('fuel_oil_liters', 'liters'),
        'kerosene': ('diesel_liters', 'liters'),  # Use diesel as proxy
        'burning oil': ('diesel_liters', 'liters'),  # Use diesel as proxy
    }

    for key, (activity_key, unit) in fuel_map.items():
        if key in fuel_type:
            return activity_key, unit

    # Default fallback - check if energy unit, otherwise volume
    if is_energy_unit:
        return 'natural_gas_kwh', 'kWh'
    return 'natural_gas_volume', 'm3'


def resolve_mobile_fuel(row: dict) -> tuple[str, str]:
    """Resolve activity_key for mobile combustion."""
    # Support both legacy and generated template column names
    vehicle_type = (row.get('Vehicle_Type') or row.get('Vehicle Type') or '').lower().strip()
    fuel_type = (row.get('Fuel_Type') or row.get('Fuel Type') or '').lower().strip()
    calc_type = (row.get('Calc_Type') or row.get('Method') or '').lower().strip()
    unit = (row.get('Physical_Unit') or row.get('Unit/Currency') or '').lower().strip()

    # Spend-based - use spend_other as generic spend factor
    if calc_type == 'spend':
        return 'spend_other', 'USD'

    # If unit is liters/gallons, use fuel-based (direct fuel consumption)
    if 'liter' in unit or 'gallon' in unit:
        if 'diesel' in fuel_type:
            return 'diesel_liters', 'liters'  # Use diesel_liters (exists)
        elif 'petrol' in fuel_type or 'gasoline' in fuel_type:
            return 'petrol_liters', 'liters'

    # Distance-based by vehicle type (using existing activity_keys from emission_factors)
    vehicle_map = {
        'passenger car': {
            'petrol': 'car_petrol_km',
            'gasoline': 'car_petrol_km',
            'diesel': 'car_diesel_km',
            'hybrid': 'car_hybrid_km',
            'electric': 'car_hybrid_km',  # Use hybrid as proxy for electric
        },
        'car': {
            'petrol': 'car_petrol_km',
            'gasoline': 'car_petrol_km',
            'diesel': 'car_diesel_km',
        },
        'van': {
            'diesel': 'van_diesel_km',
            'petrol': 'van_diesel_km',  # Use van_diesel as proxy
        },
        'light truck': {
            'diesel': 'van_diesel_km',  # Use van as proxy for light truck
        },
        'truck': {
            'diesel': 'hgv_diesel_km',
        },
        'hgv': {
            'diesel': 'hgv_diesel_km',
        },
        'bus': {
            'diesel': 'commute_bus',  # Use commute_bus as proxy
        },
        'motorcycle': {
            'petrol': 'car_petrol_km',  # Use car_petrol as proxy
        },
    }

    for v_key, fuel_options in vehicle_map.items():
        if v_key in vehicle_type:
            for f_key, activity_key in fuel_options.items():
                if f_key in fuel_type:
                    return activity_key, 'km'
            # Default to first option
            return list(fuel_options.values())[0], 'km'

    # Default: petrol car
    return 'car_petrol_km', 'km'


def resolve_refrigerant(row: dict) -> tuple[str, str]:
    """Resolve activity_key for fugitive emissions."""
    # Support both legacy and generated template column names
    gas_type = (row.get('Gas_Type') or row.get('Refrigerant Type') or '').upper().strip()

    # Map common refrigerants (using existing activity_keys from emission_factors)
    refrigerant_map = {
        'R-410A': 'refrigerant_r410a',
        'R410A': 'refrigerant_r410a',
        'R-134A': 'refrigerant_r134a',
        'R134A': 'refrigerant_r134a',
        'R-32': 'refrigerant_r32',
        'R32': 'refrigerant_r32',
        'R-404A': 'refrigerant_r404a',
        'R404A': 'refrigerant_r404a',
        'R-407C': 'refrigerant_r410a',  # Use R-410A as proxy (similar GWP)
        'R-22': 'refrigerant_r134a',  # Use R-134a as proxy
    }

    for key, activity_key in refrigerant_map.items():
        if key in gas_type:
            return activity_key, 'kg'

    # Default
    return 'refrigerant_r410a', 'kg'


def resolve_electricity(row: dict) -> tuple[str, str]:
    """Resolve activity_key for electricity."""
    # Support both legacy and generated template column names
    calc_type = (row.get('Calc_Type') or row.get('Method') or '').lower().strip()
    country = (row.get('Country/Region') or row.get('country_code') or '').upper().strip()

    # Spend-based - use spend_other as generic spend factor
    if calc_type == 'spend':
        return 'spend_other', 'USD'

    # Map country codes to activity keys (using existing activity_keys from emission_factors)
    country_map = {
        'IL': 'electricity_il',
        'US': 'electricity_us',
        'UK': 'electricity_uk',
        'GB': 'electricity_uk',
        'DE': 'electricity_de',
        'FR': 'electricity_fr',
        'EU': 'electricity_eu',
        'GLOBAL': 'electricity_global',
        'AU': 'electricity_au',
        'CA': 'electricity_ca',
        'CN': 'electricity_cn',
        'ES': 'electricity_es',
        'IN': 'electricity_in',
        'IT': 'electricity_it',
        'JP': 'electricity_jp',
        'KR': 'electricity_kr',
        'NL': 'electricity_nl',
        'PL': 'electricity_pl',
        'SG': 'electricity_sg',
    }

    activity_key = country_map.get(country, 'electricity_il')  # Default to Israel
    return activity_key, 'kWh'


def resolve_heat_steam(row: dict) -> tuple[str, str]:
    """Resolve activity_key for heat/steam/cooling."""
    # Support both legacy and generated template column names
    energy_type = (row.get('Energy_Type') or row.get('Energy Type') or '').lower().strip()
    calc_type = (row.get('Calc_Type') or row.get('Method') or '').lower().strip()

    # Spend-based - use spend_other as generic spend factor
    if calc_type == 'spend':
        return 'spend_other', 'USD'

    # Use existing activity_keys from emission_factors
    if 'cooling' in energy_type:
        return 'district_heat_kwh', 'kWh'  # Use heat as proxy for cooling
    elif 'steam' in energy_type:
        return 'steam_kwh', 'kWh'
    else:
        return 'district_heat_kwh', 'kWh'


def resolve_waste(row: dict) -> tuple[str, str]:
    """Resolve activity_key for waste."""
    treatment = (row.get('Treatment') or '').lower().strip()
    waste_type = (row.get('Waste_Type') or '').lower().strip()
    
    if 'recycl' in treatment:
        if 'paper' in waste_type:
            return 'waste_recycled_paper', 'kg'
        elif 'plastic' in waste_type:
            return 'waste_recycled_plastic', 'kg'
        else:
            return 'waste_recycled_mixed', 'kg'
    elif 'inciner' in treatment or 'combust' in treatment:
        return 'waste_incineration', 'kg'
    else:  # Landfill
        return 'waste_landfill_mixed', 'kg'


def resolve_transport(row: dict) -> tuple[str, str]:
    """Resolve activity_key for transport/freight."""
    transport_mode = (row.get('Transport_Mode') or '').lower().strip()
    
    if 'ship' in transport_mode or 'sea' in transport_mode:
        return 'sea_freight_container', 'tonne.km'
    elif 'air' in transport_mode or 'plane' in transport_mode:
        return 'air_freight', 'tonne.km'
    elif 'rail' in transport_mode or 'train' in transport_mode:
        return 'rail_freight', 'tonne.km'
    elif 'van' in transport_mode:
        return 'road_freight_van', 'tonne.km'
    else:  # Default to truck
        return 'road_freight_hgv', 'tonne.km'


def resolve_flight(row: dict) -> tuple[str, str]:
    """Resolve activity_key for business travel flights."""
    travel_class = (row.get('Class') or '').lower().strip()
    distance = row.get('Distance_km') or 0
    
    # Determine short vs long haul (threshold: 3700 km)
    is_long_haul = distance > 3700 if distance else True
    
    if 'business' in travel_class:
        return 'flight_long_business' if is_long_haul else 'flight_short_economy', 'km'
    else:  # Economy
        return 'flight_long_economy' if is_long_haul else 'flight_short_economy', 'km'


def resolve_hotel(row: dict) -> tuple[str, str]:
    """Resolve activity_key for hotel stays."""
    return 'hotel_night', 'nights'


def resolve_commute(row: dict) -> tuple[str, str]:
    """Resolve activity_key for employee commuting."""
    transport_mode = (row.get('Transport_Mode') or '').lower().strip()
    
    commute_map = {
        'car': 'commute_car_petrol',
        'petrol': 'commute_car_petrol',
        'diesel': 'commute_car_petrol',  # Using petrol as proxy
        'bus': 'commute_bus',
        'rail': 'commute_rail',
        'train': 'commute_rail',
        'bicycle': 'commute_bicycle',
        'bike': 'commute_bicycle',
        'walk': 'commute_bicycle',  # Zero emission
    }
    
    for key, activity_key in commute_map.items():
        if key in transport_mode:
            return activity_key, 'km'
    
    return 'commute_car_petrol', 'km'


def resolve_spend_generic(row: dict, default_key: str = 'spend_other') -> tuple[str, str]:
    """Resolve activity_key for spend-based categories."""
    return default_key, 'USD'


def resolve_purchased_goods(row: dict) -> tuple[str, str]:
    """Resolve activity_key for 3.1 Purchased Goods & Services."""
    category = (row.get('Category') or '').lower().strip()
    method = (row.get('Method') or '').lower().strip()

    # If spend-based
    if method == 'spend' or 'spend' in category:
        spend_map = {
            'office supplies': ('spend_office_supplies', 'USD'),
            'it equipment': ('spend_it_equipment', 'USD'),
            'professional services': ('spend_professional_services', 'USD'),
            'food & beverages': ('spend_food_beverages', 'USD'),
        }
        for key, result in spend_map.items():
            if key in category:
                return result
        return 'spend_other', 'USD'

    # Physical-based materials
    material_map = {
        'steel': ('steel_purchased_kg', 'kg'),
        'aluminum (primary)': ('aluminum_primary_purchased_kg', 'kg'),
        'aluminum - primary': ('aluminum_primary_purchased_kg', 'kg'),
        'aluminum (recycled)': ('aluminum_recycled_purchased_kg', 'kg'),
        'aluminum - recycled': ('aluminum_recycled_purchased_kg', 'kg'),
        'plastic - pet': ('plastic_pet_purchased_kg', 'kg'),
        'plastic - hdpe': ('plastic_hdpe_purchased_kg', 'kg'),
        'plastic - generic': ('plastic_generic_purchased_kg', 'kg'),
        'plastic': ('plastic_generic_purchased_kg', 'kg'),
        'paper (virgin)': ('paper_virgin_purchased_kg', 'kg'),
        'paper - virgin': ('paper_virgin_purchased_kg', 'kg'),
        'paper (recycled)': ('paper_recycled_purchased_kg', 'kg'),
        'paper - recycled': ('paper_recycled_purchased_kg', 'kg'),
        'cardboard': ('cardboard_purchased_kg', 'kg'),
        'glass': ('glass_purchased_kg', 'kg'),
        'concrete': ('concrete_purchased_kg', 'kg'),
        'textiles - cotton': ('textiles_cotton_purchased_kg', 'kg'),
        'cotton': ('textiles_cotton_purchased_kg', 'kg'),
        'textiles - polyester': ('textiles_polyester_purchased_kg', 'kg'),
        'polyester': ('textiles_polyester_purchased_kg', 'kg'),
        'electronics': ('electronics_purchased_kg', 'kg'),
        'food - meat': ('food_meat_purchased_kg', 'kg'),
        'meat': ('food_meat_purchased_kg', 'kg'),
        'food - dairy': ('food_dairy_purchased_kg', 'kg'),
        'dairy': ('food_dairy_purchased_kg', 'kg'),
        'food - vegetables': ('food_vegetables_purchased_kg', 'kg'),
        'vegetables': ('food_vegetables_purchased_kg', 'kg'),
    }

    for key, result in material_map.items():
        if key in category:
            return result

    # Default to spend_other
    return 'spend_other', 'USD'


def resolve_capital_goods(row: dict) -> tuple[str, str]:
    """Resolve activity_key for 3.2 Capital Goods."""
    asset_type = (row.get('Asset Type') or '').lower().strip()
    method = (row.get('Method') or '').lower().strip()

    # Spend-based
    if method == 'spend' or 'spend' in asset_type:
        if 'construction' in asset_type:
            return 'spend_construction', 'USD'
        return 'spend_capital_equipment', 'USD'

    # Physical-based
    asset_map = {
        'vehicle - car': ('capital_vehicle_unit', 'unit'),
        'car': ('capital_vehicle_unit', 'unit'),
        'vehicle - truck': ('capital_truck_unit', 'unit'),
        'truck': ('capital_truck_unit', 'unit'),
        'hgv': ('capital_truck_unit', 'unit'),
        'computer': ('capital_computer_unit', 'unit'),
        'laptop': ('capital_computer_unit', 'unit'),
        'server': ('capital_server_unit', 'unit'),
        'building': ('capital_building_m2', 'm2'),
    }

    for key, result in asset_map.items():
        if key in asset_type:
            return result

    return 'spend_capital_equipment', 'USD'


def resolve_upstream_transport(row: dict) -> tuple[str, str]:
    """Resolve activity_key for 3.4 Upstream Transportation."""
    mode = (row.get('Transport Mode') or '').lower().strip()
    method = (row.get('Method') or '').lower().strip()

    # Spend-based
    if method == 'spend':
        spend_map = {
            'road': ('freight_spend_road', 'USD'),
            'hgv': ('freight_spend_road', 'USD'),
            'van': ('freight_spend_road', 'USD'),
            'air': ('freight_spend_air', 'USD'),
            'sea': ('freight_spend_sea', 'USD'),
            'courier': ('freight_spend_courier', 'USD'),
            'parcel': ('freight_spend_courier', 'USD'),
        }
        for key, result in spend_map.items():
            if key in mode:
                return result
        return 'freight_spend_road', 'USD'

    # Distance-based (tonne-km)
    distance_map = {
        'road - hgv': ('road_freight_hgv', 'tonne-km'),
        'hgv': ('road_freight_hgv', 'tonne-km'),
        'road - van': ('road_freight_van', 'tonne-km'),
        'van': ('road_freight_van', 'tonne-km'),
        'rail': ('rail_freight', 'tonne-km'),
        'sea - container': ('sea_freight_container', 'tonne-km'),
        'container': ('sea_freight_container', 'tonne-km'),
        'sea - bulk': ('sea_freight_bulk', 'tonne-km'),
        'bulk': ('sea_freight_bulk', 'tonne-km'),
        'air': ('air_freight', 'tonne-km'),
        'courier': ('road_freight_van', 'tonne-km'),
    }

    for key, result in distance_map.items():
        if key in mode:
            return result

    return 'road_freight_hgv', 'tonne-km'


def resolve_waste_v2(row: dict) -> tuple[str, str]:
    """Resolve activity_key for 3.5 Waste (enhanced version)."""
    waste_type = (row.get('Waste Type') or '').lower().strip()
    treatment = (row.get('Treatment Method') or row.get('Treatment') or '').lower().strip()

    # Treatment-based resolution
    if 'landfill' in treatment:
        if 'food' in waste_type or 'organic' in waste_type:
            return 'waste_landfill_food', 'kg'
        return 'waste_landfill_mixed', 'kg'

    if 'recycl' in treatment:
        if 'paper' in waste_type or 'cardboard' in waste_type:
            return 'waste_recycled_paper', 'kg'
        if 'plastic' in waste_type:
            return 'waste_recycled_plastic', 'kg'
        if 'metal' in waste_type:
            return 'waste_recycled_metal', 'kg'
        if 'glass' in waste_type:
            return 'waste_recycled_glass', 'kg'
        return 'waste_recycled_mixed', 'kg'

    if 'inciner' in treatment or 'combust' in treatment:
        return 'waste_incineration', 'kg'

    if 'compost' in treatment:
        return 'waste_composted_food', 'kg'

    if 'anaerobic' in treatment:
        return 'waste_anaerobic_food', 'kg'

    # Type-based fallback
    if 'electronic' in waste_type or 'weee' in waste_type:
        return 'waste_ewaste', 'kg'

    if 'construction' in waste_type:
        return 'waste_construction', 'kg'

    return 'waste_landfill_mixed', 'kg'


def resolve_flight_v2(row: dict) -> tuple[str, str]:
    """Resolve activity_key for 3.6 Business Travel - Flights (enhanced)."""
    cabin_class = (row.get('Cabin Class') or row.get('Class') or '').lower().strip()

    # Determine distance from airports if possible
    from_airport = row.get('From Airport') or ''
    to_airport = row.get('To Airport') or ''

    # Approximate: if we have airport codes, we'll calculate distance later
    # For now, assume long-haul for safety
    is_long_haul = True

    if 'first' in cabin_class:
        return 'flight_long_first', 'km'
    elif 'business' in cabin_class:
        if is_long_haul:
            return 'flight_long_business', 'km'
        else:
            return 'flight_short_business', 'km'
    else:  # Economy
        if is_long_haul:
            return 'flight_long_economy', 'km'
        else:
            return 'flight_short_economy', 'km'


def resolve_commute_v2(row: dict) -> tuple[str, str]:
    """Resolve activity_key for 3.7 Employee Commuting (enhanced)."""
    mode = (row.get('Transport Mode') or '').lower().strip()

    commute_map = {
        'car - petrol': ('commute_car_petrol', 'km'),
        'petrol': ('commute_car_petrol', 'km'),
        'car - diesel': ('commute_car_petrol', 'km'),  # Use petrol as proxy
        'diesel': ('commute_car_petrol', 'km'),
        'car - hybrid': ('commute_car_petrol', 'km'),  # Use petrol as proxy
        'hybrid': ('commute_car_petrol', 'km'),
        'car - electric': ('commute_car_electric', 'km'),
        'electric': ('commute_car_electric', 'km'),
        'bus': ('commute_bus', 'km'),
        'rail': ('commute_rail', 'km'),
        'metro': ('commute_rail', 'km'),
        'train': ('commute_rail', 'km'),
        'motorcycle': ('commute_motorcycle', 'km'),
        'e-bike': ('commute_ebike', 'km'),
        'ebike': ('commute_ebike', 'km'),
        'bicycle': ('commute_bicycle', 'km'),
        'bike': ('commute_bicycle', 'km'),
        'walk': ('commute_bicycle', 'km'),  # Zero emission
        'work from home': ('commute_wfh_day', 'day'),
        'wfh': ('commute_wfh_day', 'day'),
    }

    for key, result in commute_map.items():
        if key in mode:
            return result

    return 'commute_car_petrol', 'km'


def resolve_leased_assets(row: dict) -> tuple[str, str]:
    """Resolve activity_key for 3.8 Upstream Leased Assets."""
    asset_type = (row.get('Asset Type') or '').lower().strip()
    method = (row.get('Method') or '').lower().strip()

    # Area-based
    if method == 'area' or 'm2' in str(row.get('Unit') or '').lower():
        asset_map = {
            'office': ('leased_office_m2_year', 'm2-year'),
            'warehouse': ('leased_warehouse_m2_year', 'm2-year'),
            'retail': ('leased_retail_m2_year', 'm2-year'),
            'data center': ('leased_datacenter_m2_year', 'm2-year'),
            'datacenter': ('leased_datacenter_m2_year', 'm2-year'),
        }

        for key, result in asset_map.items():
            if key in asset_type:
                return result

        return 'leased_office_m2_year', 'm2-year'

    # Energy-based - use electricity factors
    # This would use the country's grid factor
    return 'electricity_global', 'kWh'


def resolve_downstream_transport(row: dict) -> tuple[str, str]:
    """Resolve activity_key for 3.9 Downstream Transportation."""
    mode = (row.get('Transport Mode') or '').lower().strip()
    method = (row.get('Method') or '').lower().strip()

    # Same logic as upstream, but uses delivery_ keys where available
    if method == 'spend':
        if 'air' in mode:
            return 'freight_spend_air', 'USD'
        if 'sea' in mode:
            return 'freight_spend_sea', 'USD'
        return 'freight_spend_road', 'USD'

    # Distance-based
    if 'van' in mode:
        return 'delivery_van', 'tonne-km'
    if 'hgv' in mode or 'truck' in mode:
        return 'delivery_hgv', 'tonne-km'

    return 'delivery_van', 'tonne-km'


# =============================================================================
# Sheet Configurations
# =============================================================================

# Column mappings for generated template format (from generate_template.py)
# Sheets like "1.1 Stationary" have headers at row 4, data starts at row 6
GENERATED_TEMPLATE_COLUMN_MAP_STATIONARY = {
    'Fuel Type': 'fuel_type',
    'Method': 'calc_type',
    'Description': 'description',
    'Quantity/Amount': 'quantity',
    'Unit/Currency': 'unit',
    'Date': 'activity_date',
    'Site (Optional)': 'site',
    'Site': 'site',  # Also support without "(Optional)"
}

GENERATED_TEMPLATE_COLUMN_MAP_MOBILE = {
    'Vehicle Type': 'vehicle_type',
    'Fuel Type': 'fuel_type',
    'Method': 'calc_type',
    'Description': 'description',
    'Quantity/Amount': 'quantity',
    'Unit/Currency': 'unit',
    'Date': 'activity_date',
}

GENERATED_TEMPLATE_COLUMN_MAP_FUGITIVE = {
    'Refrigerant Type': 'gas_type',
    'Method': 'calc_type',
    'Description': 'description',
    'Quantity/Amount': 'quantity',
    'Unit/Currency': 'unit',
    'Date': 'activity_date',
}

GENERATED_TEMPLATE_COLUMN_MAP_ELECTRICITY = {
    'Electricity Type': 'electricity_type',
    'Method': 'calc_type',
    'Country/Region': 'country_code',
    'Description': 'description',
    'Quantity/Amount': 'quantity',
    'Unit/Currency': 'unit',
    'Date': 'activity_date',
}

GENERATED_TEMPLATE_COLUMN_MAP_HEAT_STEAM = {
    'Energy Type': 'energy_type',
    'Method': 'calc_type',
    'Description': 'description',
    'Quantity/Amount': 'quantity',
    'Unit/Currency': 'unit',
    'Date': 'activity_date',
}

GENERATED_TEMPLATE_COLUMN_MAP_COOLING = {
    'Cooling Type': 'cooling_type',
    'Method': 'calc_type',
    'Description': 'description',
    'Quantity/Amount': 'quantity',
    'Unit/Currency': 'unit',
    'Date': 'activity_date',
}

SHEET_CONFIGS = {
    # =========================================================================
    # Original sheet names (for legacy templates)
    # =========================================================================
    'Scope1_Stationary': SheetConfig(
        sheet_name='Scope1_Stationary',
        scope=1,
        category_code='1.1',
        header_row=5,
        column_map={
            'Site': 'site',
            'Description': 'description',
            'Fuel_Type': 'fuel_type',
            'Year': 'year',
            'Calc_Type': 'calc_type',
            'Physical_Amount': 'quantity',
            'Physical_Unit': 'unit',
            'Spend_Amount': 'spend_amount',
            'Spend_Currency': 'spend_currency',
            'Comment': 'comment',
        },
        activity_key_resolver=resolve_stationary_fuel,
    ),

    # =========================================================================
    # Generated template sheet names (from generate_template.py)
    # Headers at row 3, row 4 is sample data (contains "SAMPLE" - auto-skipped), data starts at row 5+
    # =========================================================================
    '1.1 Stationary': SheetConfig(
        sheet_name='1.1 Stationary',
        scope=1,
        category_code='1.1',
        header_row=3,  # Headers at row 3 in template
        column_map=GENERATED_TEMPLATE_COLUMN_MAP_STATIONARY,
        activity_key_resolver=resolve_stationary_fuel,
    ),
    
    'Scope1_Mobile': SheetConfig(
        sheet_name='Scope1_Mobile',
        scope=1,
        category_code='1.2',
        header_row=5,
        column_map={
            'Site': 'site',
            'Description': 'description',
            'Vehicle_Type': 'vehicle_type',
            'Fuel_Type': 'fuel_type',
            'Year': 'year',
            'Calc_Type': 'calc_type',
            'Physical_Amount': 'quantity',
            'Physical_Unit': 'unit',
            'Spend_Amount': 'spend_amount',
            'Spend_Currency': 'spend_currency',
            'Comment': 'comment',
        },
        activity_key_resolver=resolve_mobile_fuel,
    ),

    '1.2 Mobile': SheetConfig(
        sheet_name='1.2 Mobile',
        scope=1,
        category_code='1.2',
        header_row=3,  # Headers at row 3 in template
        column_map=GENERATED_TEMPLATE_COLUMN_MAP_MOBILE,
        activity_key_resolver=resolve_mobile_fuel,
    ),

    'Scope1_Fugitive': SheetConfig(
        sheet_name='Scope1_Fugitive',
        scope=1,
        category_code='1.3',
        header_row=5,
        column_map={
            'Site': 'site',
            'Description': 'description',
            'Source_Type': 'source_type',
            'Gas_Type': 'gas_type',
            'Year': 'year',
            'Calc_Type': 'calc_type',
            'Physical_Amount': 'quantity',
            'Physical_Unit': 'unit',
            'Spend_Amount': 'spend_amount',
            'Spend_Currency': 'spend_currency',
            'Comment': 'comment',
        },
        activity_key_resolver=resolve_refrigerant,
    ),

    '1.3 Fugitive': SheetConfig(
        sheet_name='1.3 Fugitive',
        scope=1,
        category_code='1.3',
        header_row=3,  # Headers at row 3 in template
        column_map=GENERATED_TEMPLATE_COLUMN_MAP_FUGITIVE,
        activity_key_resolver=resolve_refrigerant,
    ),

    'Scope2_Electricity': SheetConfig(
        sheet_name='Scope2_Electricity',
        scope=2,
        category_code='2.1',
        header_row=5,
        column_map={
            'Site': 'site',
            'Description': 'description',
            'Source': 'source',
            'Year': 'year',
            'Calc_Type': 'calc_type',
            'Physical_Amount': 'quantity',
            'Physical_Unit': 'unit',
            'Spend_Amount': 'spend_amount',
            'Spend_Currency': 'spend_currency',
            'Comment': 'comment',
        },
        activity_key_resolver=resolve_electricity,
    ),

    '2.1 Electricity': SheetConfig(
        sheet_name='2.1 Electricity',
        scope=2,
        category_code='2.1',
        header_row=3,  # Headers at row 3 in template
        column_map=GENERATED_TEMPLATE_COLUMN_MAP_ELECTRICITY,
        activity_key_resolver=resolve_electricity,
    ),

    'Scope2_HeatSteam': SheetConfig(
        sheet_name='Scope2_HeatSteam',
        scope=2,
        category_code='2.2',
        header_row=5,
        column_map={
            'Site': 'site',
            'Description': 'description',
            'Energy_Type': 'energy_type',
            'Year': 'year',
            'Calc_Type': 'calc_type',
            'Physical_Amount': 'quantity',
            'Physical_Unit': 'unit',
            'Spend_Amount': 'spend_amount',
            'Spend_Currency': 'spend_currency',
            'Comment': 'comment',
        },
        activity_key_resolver=resolve_heat_steam,
    ),

    '2.2 Heat-Steam': SheetConfig(
        sheet_name='2.2 Heat-Steam',
        scope=2,
        category_code='2.2',
        header_row=3,  # Headers at row 3 in template
        column_map=GENERATED_TEMPLATE_COLUMN_MAP_HEAT_STEAM,
        activity_key_resolver=resolve_heat_steam,
    ),

    '2.3 Cooling': SheetConfig(
        sheet_name='2.3 Cooling',
        scope=2,
        category_code='2.3',
        header_row=3,  # Headers at row 3 in template
        column_map=GENERATED_TEMPLATE_COLUMN_MAP_COOLING,
        activity_key_resolver=lambda row: ('district_heat_kwh', 'kWh'),  # Use heat as proxy for cooling
    ),

    'Cat1_RawMaterials': SheetConfig(
        sheet_name='Cat1_RawMaterials',
        scope=3,
        category_code='3.1',
        header_row=5,
        column_map={
            'Site': 'site',
            'Description': 'description',
            'Year': 'year',
            'Calc_Type': 'calc_type',
            'Physical_Amount': 'quantity',
            'Physical_Unit': 'unit',
            'Spend_Amount': 'spend_amount',
            'Spend_Currency': 'spend_currency',
            'Comment': 'comment',
        },
        activity_key_resolver=lambda row: resolve_spend_generic(row, 'spend_other'),
        is_spend_based=True,
    ),
    
    'Cat1_Services': SheetConfig(
        sheet_name='Cat1_Services',
        scope=3,
        category_code='3.1',
        header_row=5,
        column_map={
            'Site': 'site',
            'Description': 'description',
            'Year': 'year',
            'Calc_Type': 'calc_type',
            'Physical_Amount': 'quantity',
            'Physical_Unit': 'unit',
            'Spend_Amount': 'spend_amount',
            'Spend_Currency': 'spend_currency',
            'Comment': 'comment',
        },
        activity_key_resolver=lambda row: ('spend_professional_services', 'USD'),
        is_spend_based=True,
    ),
    
    'Cat2_CapitalGoods': SheetConfig(
        sheet_name='Cat2_CapitalGoods',
        scope=3,
        category_code='3.2',
        header_row=5,
        column_map={
            'Site': 'site',
            'Description': 'description',
            'Year': 'year',
            'Calc_Type': 'calc_type',
            'Physical_Amount': 'quantity',
            'Physical_Unit': 'unit',
            'Spend_Amount': 'spend_amount',
            'Spend_Currency': 'spend_currency',
            'Comment': 'comment',
        },
        activity_key_resolver=lambda row: ('spend_capital_equipment', 'USD'),
        is_spend_based=True,
    ),
    
    'Cat4_9_Transport': SheetConfig(
        sheet_name='Cat4_9_Transport',
        scope=3,
        category_code='3.4',
        header_row=5,
        column_map={
            'Site': 'site',
            'Description': 'description',
            'Transport_Mode': 'transport_mode',
            'Distance_km': 'distance_km',
            'Year': 'year',
            'Calc_Type': 'calc_type',
            'Physical_Amount': 'quantity',
            'Physical_Unit': 'unit',
            'Spend_Amount': 'spend_amount',
            'Spend_Currency': 'spend_currency',
            'Comment': 'comment',
        },
        activity_key_resolver=resolve_transport,
    ),
    
    'Cat5_Waste': SheetConfig(
        sheet_name='Cat5_Waste',
        scope=3,
        category_code='3.5',
        header_row=5,
        column_map={
            'Site': 'site',
            'Description': 'description',
            'Waste_Type': 'waste_type',
            'Treatment': 'treatment',
            'Year': 'year',
            'Calc_Type': 'calc_type',
            'Physical_Amount': 'quantity',
            'Physical_Unit': 'unit',
            'Spend_Amount': 'spend_amount',
            'Spend_Currency': 'spend_currency',
            'Comment': 'comment',
        },
        activity_key_resolver=resolve_waste,
    ),
    
    'Cat6_BusinessTravel': SheetConfig(
        sheet_name='Cat6_BusinessTravel',
        scope=3,
        category_code='3.6',
        header_row=5,
        column_map={
            'Site': 'site',
            'Description': 'description',
            'Travel_Type': 'travel_type',
            'Trip_Type': 'trip_type',
            'From_Airport': 'from_airport',
            'To_Airport': 'to_airport',
            'Distance_km': 'distance_km',
            'Class': 'travel_class',
            'Year': 'year',
            'Calc_Type': 'calc_type',
            'Physical_Amount': 'quantity',
            'Physical_Unit': 'unit',
            'Spend_Amount': 'spend_amount',
            'Spend_Currency': 'spend_currency',
            'Comment': 'comment',
        },
        activity_key_resolver=resolve_flight,
    ),
    
    'Cat6_Hotels': SheetConfig(
        sheet_name='Cat6_Hotels',
        scope=3,
        category_code='3.6',
        header_row=5,
        column_map={
            'Site': 'site',
            'Description': 'description',
            'Country': 'country',
            'Nights': 'nights',
            'Year': 'year',
            'Calc_Type': 'calc_type',
            'Physical_Amount': 'quantity',
            'Physical_Unit': 'unit',
            'Spend_Amount': 'spend_amount',
            'Spend_Currency': 'spend_currency',
            'Comment': 'comment',
        },
        activity_key_resolver=resolve_hotel,
    ),
    
    'Cat7_Commuting': SheetConfig(
        sheet_name='Cat7_Commuting',
        scope=3,
        category_code='3.7',
        header_row=5,
        column_map={
            'Site': 'site',
            'Description': 'description',
            'Transport_Mode': 'transport_mode',
            'Employees': 'employees',
            'Working_Days': 'working_days',
            'Avg_Distance_km': 'avg_distance_km',
            'Year': 'year',
            'Calc_Type': 'calc_type',
            'Physical_Amount': 'quantity',
            'Physical_Unit': 'unit',
            'Spend_Amount': 'spend_amount',
            'Spend_Currency': 'spend_currency',
            'Comment': 'comment',
        },
        activity_key_resolver=resolve_commute,
    ),
    
    'Cat12_EndOfLife': SheetConfig(
        sheet_name='Cat12_EndOfLife',
        scope=3,
        category_code='3.12',
        header_row=5,
        column_map={
            'Site': 'site',
            'Description': 'description',
            'Product_Type': 'product_type',
            'Treatment': 'treatment',
            'Year': 'year',
            'Calc_Type': 'calc_type',
            'Physical_Amount': 'quantity',
            'Physical_Unit': 'unit',
            'Spend_Amount': 'spend_amount',
            'Spend_Currency': 'spend_currency',
            'Comment': 'comment',
        },
        activity_key_resolver=resolve_waste,  # Same as waste
    ),

    # =========================================================================
    # NEW SCOPE 3 TEMPLATE SHEETS (v1 - January 2025)
    # =========================================================================

    '3.1 Purchased Goods': SheetConfig(
        sheet_name='3.1 Purchased Goods',
        scope=3,
        category_code='3.1',
        header_row=4,
        column_map={
            'Description': 'description',
            'Category': 'category',
            'Method': 'calc_type',
            'Quantity/Amount': 'quantity',
            'Unit/Currency': 'unit',
            'Supplier (Optional)': 'supplier',
            'Date (Optional)': 'activity_date',
            'Site (Optional)': 'site',
        },
        activity_key_resolver=resolve_purchased_goods,
    ),

    '3.2 Capital Goods': SheetConfig(
        sheet_name='3.2 Capital Goods',
        scope=3,
        category_code='3.2',
        header_row=4,
        column_map={
            'Description': 'description',
            'Asset Type': 'asset_type',
            'Method': 'calc_type',
            'Quantity/Amount': 'quantity',
            'Unit/Currency': 'unit',
            'Purchase Date': 'activity_date',
            'Expected Lifetime (Years)': 'lifetime',
        },
        activity_key_resolver=resolve_capital_goods,
    ),

    '3.4 Upstream Transport': SheetConfig(
        sheet_name='3.4 Upstream Transport',
        scope=3,
        category_code='3.4',
        header_row=4,
        column_map={
            'Description': 'description',
            'Transport Mode': 'transport_mode',
            'Method': 'calc_type',
            'Weight (tonnes)': 'weight',
            'Distance (km)': 'distance',
            'Spend Amount': 'spend_amount',
            'Currency': 'currency',
            'Date': 'activity_date',
        },
        activity_key_resolver=resolve_upstream_transport,
    ),

    '3.5 Waste': SheetConfig(
        sheet_name='3.5 Waste',
        scope=3,
        category_code='3.5',
        header_row=4,
        column_map={
            'Description': 'description',
            'Waste Type': 'waste_type',
            'Treatment Method': 'treatment',
            'Quantity': 'quantity',
            'Unit': 'unit',
            'Date': 'activity_date',
            'Site (Optional)': 'site',
        },
        activity_key_resolver=resolve_waste_v2,
    ),

    '3.6 Flights': SheetConfig(
        sheet_name='3.6 Flights',
        scope=3,
        category_code='3.6',
        header_row=4,
        column_map={
            'Description': 'description',
            'From Airport': 'from_airport',
            'To Airport': 'to_airport',
            'Trip Type': 'trip_type',
            'Cabin Class': 'travel_class',
            'Number of Trips': 'quantity',
            'Date': 'activity_date',
            'Traveler (Optional)': 'traveler',
        },
        activity_key_resolver=resolve_flight_v2,
    ),

    '3.6 Hotels': SheetConfig(
        sheet_name='3.6 Hotels',
        scope=3,
        category_code='3.6',
        header_row=4,
        column_map={
            'Description': 'description',
            'Country': 'country',
            'Number of Nights': 'quantity',
            'Number of Rooms': 'rooms',
            'Date': 'activity_date',
            'Traveler (Optional)': 'traveler',
        },
        activity_key_resolver=resolve_hotel,
    ),

    '3.7 Commuting': SheetConfig(
        sheet_name='3.7 Commuting',
        scope=3,
        category_code='3.7',
        header_row=4,
        column_map={
            'Site/Department': 'site',
            'Transport Mode': 'transport_mode',
            'Number of Employees': 'employees',
            'Avg Distance (km one-way)': 'avg_distance_km',
            'Working Days/Year': 'working_days',
            'Year': 'year',
            'Comments': 'comment',
        },
        activity_key_resolver=resolve_commute_v2,
    ),

    '3.8 Leased Assets': SheetConfig(
        sheet_name='3.8 Leased Assets',
        scope=3,
        category_code='3.8',
        header_row=4,
        column_map={
            'Description': 'description',
            'Asset Type': 'asset_type',
            'Method': 'calc_type',
            'Quantity': 'quantity',
            'Unit': 'unit',
            'Country/Region': 'country',
            'Year': 'year',
        },
        activity_key_resolver=resolve_leased_assets,
    ),

    '3.9 Downstream Transport': SheetConfig(
        sheet_name='3.9 Downstream Transport',
        scope=3,
        category_code='3.9',
        header_row=4,
        column_map={
            'Description': 'description',
            'Transport Mode': 'transport_mode',
            'Method': 'calc_type',
            'Weight (tonnes)': 'weight',
            'Distance (km)': 'distance',
            'Spend Amount': 'spend_amount',
            'Currency': 'currency',
            'Date': 'activity_date',
        },
        activity_key_resolver=resolve_downstream_transport,
    ),

    # =========================================================================
    # V3 TEMPLATE SHEETS (Short names: 3.1, 3.2, etc.)
    # These support [Physical]/[Spend] prefix format in Activity Type column
    # Headers at row 4, data starts at row 8
    # =========================================================================

    '3.1': SheetConfig(
        sheet_name='3.1',
        scope=3,
        category_code='3.1',
        header_row=4,
        column_map={
            'Method': 'calc_type',
            'Activity Type': 'activity_type',
            'Description': 'description',
            'Quantity': 'quantity',
            'Unit': 'unit',
            'Date': 'activity_date',
            'Site': 'site',
            'Notes': 'comment',
        },
        activity_key_resolver=lambda row: resolve_v3_activity(row, '3.1'),
    ),

    '3.2': SheetConfig(
        sheet_name='3.2',
        scope=3,
        category_code='3.2',
        header_row=4,
        column_map={
            'Method': 'calc_type',
            'Activity Type': 'activity_type',
            'Description': 'description',
            'Quantity': 'quantity',
            'Unit': 'unit',
            'Date': 'activity_date',
            'Site': 'site',
            'Notes': 'comment',
        },
        activity_key_resolver=lambda row: resolve_v3_activity(row, '3.2'),
    ),

    '3.4': SheetConfig(
        sheet_name='3.4',
        scope=3,
        category_code='3.4',
        header_row=4,
        column_map={
            'Method': 'calc_type',
            'Activity Type': 'activity_type',
            'Description': 'description',
            'Quantity': 'quantity',
            'Unit': 'unit',
            'Date': 'activity_date',
            'Site': 'site',
            'Notes': 'comment',
        },
        activity_key_resolver=lambda row: resolve_v3_activity(row, '3.4'),
    ),

    '3.5': SheetConfig(
        sheet_name='3.5',
        scope=3,
        category_code='3.5',
        header_row=4,
        column_map={
            'Method': 'calc_type',
            'Activity Type': 'activity_type',
            'Description': 'description',
            'Quantity': 'quantity',
            'Unit': 'unit',
            'Date': 'activity_date',
            'Site': 'site',
            'Notes': 'comment',
        },
        activity_key_resolver=lambda row: resolve_v3_activity(row, '3.5'),
    ),

    '3.6': SheetConfig(
        sheet_name='3.6',
        scope=3,
        category_code='3.6',
        header_row=4,
        column_map={
            'Method': 'calc_type',
            'Activity Type': 'activity_type',
            'Description': 'description',
            'Quantity': 'quantity',
            'Unit': 'unit',
            'Date': 'activity_date',
            'Site': 'site',
            'Notes': 'comment',
        },
        activity_key_resolver=lambda row: resolve_v3_activity(row, '3.6'),
    ),

    '3.7': SheetConfig(
        sheet_name='3.7',
        scope=3,
        category_code='3.7',
        header_row=4,
        column_map={
            'Method': 'calc_type',
            'Activity Type': 'activity_type',
            'Description': 'description',
            'Quantity': 'quantity',
            'Unit': 'unit',
            'Date': 'activity_date',
            'Site': 'site',
            'Notes': 'comment',
        },
        activity_key_resolver=lambda row: resolve_v3_activity(row, '3.7'),
    ),

    '3.8': SheetConfig(
        sheet_name='3.8',
        scope=3,
        category_code='3.8',
        header_row=4,
        column_map={
            'Method': 'calc_type',
            'Activity Type': 'activity_type',
            'Description': 'description',
            'Quantity': 'quantity',
            'Unit': 'unit',
            'Date': 'activity_date',
            'Site': 'site',
            'Notes': 'comment',
        },
        activity_key_resolver=lambda row: resolve_v3_activity(row, '3.8'),
    ),

    '3.9': SheetConfig(
        sheet_name='3.9',
        scope=3,
        category_code='3.9',
        header_row=4,
        column_map={
            'Method': 'calc_type',
            'Activity Type': 'activity_type',
            'Description': 'description',
            'Quantity': 'quantity',
            'Unit': 'unit',
            'Date': 'activity_date',
            'Site': 'site',
            'Notes': 'comment',
        },
        activity_key_resolver=lambda row: resolve_v3_activity(row, '3.9'),
    ),
}


def get_sheet_config(sheet_name: str) -> SheetConfig | None:
    """Get configuration for a sheet by name."""
    return SHEET_CONFIGS.get(sheet_name)


def get_all_sheet_configs() -> dict[str, SheetConfig]:
    """Get all sheet configurations."""
    return SHEET_CONFIGS


# =============================================================================
# V3 Template Resolver - Handles [Physical]/[Spend] prefix format
# =============================================================================

def resolve_v3_activity(row: dict, category: str) -> tuple[str, str]:
    """
    Resolve activity_key for v3 template format.

    V3 template uses:
    - Method column: "Physical" or "Spend"
    - Activity Type column: "[Physical] Steel" or "[Spend] Office Supplies"

    This resolver extracts the activity name and maps to backend activity_key.
    """
    activity_type = (row.get('Activity Type') or '').strip()
    method = (row.get('Method') or '').lower().strip()

    # Extract the actual activity name by removing [Physical]/[Spend] prefix
    if activity_type.startswith('[Physical] '):
        activity_name = activity_type[11:].strip()  # Remove "[Physical] "
        method = 'physical'
    elif activity_type.startswith('[Spend] '):
        activity_name = activity_type[8:].strip()  # Remove "[Spend] "
        method = 'spend'
    elif activity_type.startswith('[Energy] '):
        activity_name = activity_type[9:].strip()  # Remove "[Energy] "
        method = 'energy'
    else:
        activity_name = activity_type

    activity_lower = activity_name.lower()

    # Category-specific mappings
    if category == '3.1':
        # Purchased Goods & Services
        physical_map = {
            'steel': ('steel_purchased_kg', 'kg'),
            'aluminum (primary)': ('aluminum_primary_purchased_kg', 'kg'),
            'aluminum (recycled)': ('aluminum_recycled_purchased_kg', 'kg'),
            'plastic - pet': ('plastic_pet_purchased_kg', 'kg'),
            'plastic - hdpe': ('plastic_hdpe_purchased_kg', 'kg'),
            'plastic - average': ('plastic_generic_purchased_kg', 'kg'),
            'paper (virgin)': ('paper_virgin_purchased_kg', 'kg'),
            'paper (recycled)': ('paper_recycled_purchased_kg', 'kg'),
            'cardboard': ('cardboard_purchased_kg', 'kg'),
            'glass': ('glass_purchased_kg', 'kg'),
            'concrete': ('concrete_purchased_kg', 'kg'),
            'textiles - cotton': ('textiles_cotton_purchased_kg', 'kg'),
            'textiles - polyester': ('textiles_polyester_purchased_kg', 'kg'),
            'electronics': ('electronics_purchased_kg', 'kg'),
            'food - meat': ('food_meat_purchased_kg', 'kg'),
            'food - dairy': ('food_dairy_purchased_kg', 'kg'),
            'food - vegetables': ('food_vegetables_purchased_kg', 'kg'),
        }
        spend_map = {
            'office supplies': ('spend_office_supplies', 'USD'),
            'it equipment': ('spend_it_equipment', 'USD'),
            'professional services': ('spend_professional_services', 'USD'),
            'food & beverages': ('spend_food_beverages', 'USD'),
            'other purchases': ('spend_other', 'USD'),
        }

        for key, result in physical_map.items():
            if key in activity_lower:
                return result
        for key, result in spend_map.items():
            if key in activity_lower:
                return result
        return ('spend_other', 'USD')

    elif category == '3.2':
        # Capital Goods
        physical_map = {
            'vehicle - car': ('capital_vehicle_unit', 'unit'),
            'vehicle - truck': ('capital_truck_unit', 'unit'),
            'computer/laptop': ('capital_computer_unit', 'unit'),
            'server': ('capital_server_unit', 'unit'),
            'building': ('capital_building_m2', 'm2'),
        }
        spend_map = {
            'equipment': ('spend_capital_equipment', 'USD'),
            'construction': ('spend_construction', 'USD'),
        }

        for key, result in physical_map.items():
            if key in activity_lower:
                return result
        for key, result in spend_map.items():
            if key in activity_lower:
                return result
        return ('spend_capital_equipment', 'USD')

    elif category == '3.4':
        # Upstream Transport
        physical_map = {
            'road - hgv': ('road_freight_hgv', 'tonne-km'),
            'road - van': ('road_freight_van', 'tonne-km'),
            'rail': ('rail_freight', 'tonne-km'),
            'sea - container': ('sea_freight_container', 'tonne-km'),
            'sea - bulk': ('sea_freight_bulk', 'tonne-km'),
            'air freight': ('air_freight', 'tonne-km'),
        }
        spend_map = {
            'road freight (spend)': ('freight_spend_road', 'USD'),
            'air freight (spend)': ('freight_spend_air', 'USD'),
            'sea freight (spend)': ('freight_spend_sea', 'USD'),
            'courier': ('freight_spend_courier', 'USD'),
        }

        for key, result in physical_map.items():
            if key in activity_lower:
                return result
        for key, result in spend_map.items():
            if key in activity_lower:
                return result
        return ('road_freight_hgv', 'tonne-km')

    elif category == '3.5':
        # Waste
        physical_map = {
            'mixed waste - landfill': ('waste_landfill_mixed', 'kg'),
            'mixed waste - recycled': ('waste_recycled_mixed', 'kg'),
            'mixed waste - incinerated': ('waste_incineration', 'kg'),
            'paper/cardboard - recycled': ('waste_recycled_paper', 'kg'),
            'plastic - recycled': ('waste_recycled_plastic', 'kg'),
            'metal - recycled': ('waste_recycled_metal', 'kg'),
            'glass - recycled': ('waste_recycled_glass', 'kg'),
            'food waste - landfill': ('waste_landfill_food', 'kg'),
            'food waste - composted': ('waste_composted_food', 'kg'),
            'food waste - anaerobic': ('waste_anaerobic_food', 'kg'),
            'electronic waste': ('waste_ewaste', 'kg'),
            'construction': ('waste_construction', 'kg'),
        }
        spend_map = {
            'waste disposal (spend)': ('waste_disposal_spend', 'USD'),
        }

        for key, result in physical_map.items():
            if key in activity_lower:
                return result
        for key, result in spend_map.items():
            if key in activity_lower:
                return result
        return ('waste_landfill_mixed', 'kg')

    elif category == '3.6':
        # Business Travel
        physical_map = {
            'short-haul flight - economy': ('flight_short_economy', 'passenger-km'),
            'short-haul flight - business': ('flight_short_business', 'passenger-km'),
            'long-haul flight - economy': ('flight_long_economy', 'passenger-km'),
            'long-haul flight - business': ('flight_long_business', 'passenger-km'),
            'long-haul flight - first': ('flight_long_first', 'passenger-km'),
            'hotel stay': ('hotel_night', 'nights'),
            'rail - domestic': ('rail_domestic_km', 'passenger-km'),
            'rail - international': ('rail_international_km', 'passenger-km'),
            'rental car': ('rental_car_km', 'km'),
            'taxi': ('taxi_km', 'km'),
        }
        spend_map = {
            'air travel (spend)': ('travel_spend_air', 'USD'),
            'hotel (spend)': ('travel_spend_hotel', 'USD'),
            'car rental (spend)': ('travel_spend_car_rental', 'USD'),
            'rail (spend)': ('travel_spend_rail', 'USD'),
            'taxi/rideshare': ('travel_spend_taxi', 'USD'),
            'general travel': ('travel_spend_general', 'USD'),
        }

        for key, result in physical_map.items():
            if key in activity_lower:
                return result
        for key, result in spend_map.items():
            if key in activity_lower:
                return result
        return ('travel_spend_general', 'USD')

    elif category == '3.7':
        # Commuting
        physical_map = {
            'car - petrol': ('commute_car_petrol', 'km'),
            'car - diesel': ('commute_car_diesel', 'km'),
            'car - hybrid': ('commute_car_hybrid', 'km'),
            'car - electric': ('commute_car_electric', 'km'),
            'bus': ('commute_bus', 'km'),
            'rail/metro': ('commute_rail', 'km'),
            'motorcycle': ('commute_motorcycle', 'km'),
            'e-bike': ('commute_ebike', 'km'),
            'bicycle': ('commute_bicycle', 'km'),
            'walk': ('commute_walk', 'km'),
            'work from home': ('commute_wfh_day', 'days'),
        }
        spend_map = {
            'commuting reimbursement': ('commute_spend_general', 'USD'),
        }

        for key, result in physical_map.items():
            if key in activity_lower:
                return result
        for key, result in spend_map.items():
            if key in activity_lower:
                return result
        return ('commute_car_petrol', 'km')

    elif category == '3.8':
        # Leased Assets
        physical_map = {
            'office space': ('leased_office_m2_year', 'm2-year'),
            'warehouse': ('leased_warehouse_m2_year', 'm2-year'),
            'retail space': ('leased_retail_m2_year', 'm2-year'),
            'data center': ('leased_datacenter_m2_year', 'm2-year'),
        }
        energy_map = {
            'known electricity use': ('leased_electricity_kwh', 'kWh'),
        }
        spend_map = {
            'leased property rent': ('leased_spend_rent', 'USD'),
        }

        for key, result in physical_map.items():
            if key in activity_lower:
                return result
        for key, result in energy_map.items():
            if key in activity_lower:
                return result
        for key, result in spend_map.items():
            if key in activity_lower:
                return result
        return ('leased_office_m2_year', 'm2-year')

    elif category == '3.9':
        # Downstream Transport
        physical_map = {
            'delivery van': ('delivery_van', 'tonne-km'),
            'delivery hgv': ('delivery_hgv', 'tonne-km'),
        }
        spend_map = {
            'delivery - road (spend)': ('delivery_spend_road', 'USD'),
            'delivery - courier (spend)': ('delivery_spend_courier', 'USD'),
            'delivery - general (spend)': ('delivery_spend_general', 'USD'),
        }

        for key, result in physical_map.items():
            if key in activity_lower:
                return result
        for key, result in spend_map.items():
            if key in activity_lower:
                return result
        return ('delivery_spend_general', 'USD')

    # Default fallback
    return ('spend_other', 'USD')


# =============================================================================
# V4 TEMPLATE RESOLVERS (January 2025 - Full GHG Protocol Implementation)
# =============================================================================

def resolve_v4_purchased_goods(row: dict) -> tuple[str, str]:
    """
    Resolve activity_key for v4 template 3.1 Purchased Goods.

    Supports 3 methods per GHG Protocol:
    1. Physical - material type + quantity (kg)
    2. Spend - spend category + amount (USD)
    3. Supplier-Specific - user provides their own EF

    Returns: (activity_key, unit)
    """
    method = (row.get('Method') or '').strip().lower()

    # =========================================================================
    # METHOD 1: SUPPLIER-SPECIFIC
    # User provides their own emission factor (from EPD or supplier)
    # =========================================================================
    if method == 'supplier-specific':
        # activity_key signals to use row['Supplier EF'] directly
        # Unit comes from the row
        unit = (row.get('Unit') or 'kg').strip()
        return ('supplier_specific_3_1', unit)

    # =========================================================================
    # METHOD 2: SPEND
    # EEIO-based factors per spend category
    # =========================================================================
    if method == 'spend':
        category = (row.get('Category') or '').strip().lower()

        # Direct mapping: Category → activity_key
        spend_map = {
            'office supplies': 'spend_office_supplies',
            'it equipment': 'spend_it_equipment',
            'it services': 'spend_it_services',
            'professional services': 'spend_professional_services',
            'legal services': 'spend_legal_services',
            'marketing': 'spend_marketing',
            'food & catering': 'spend_food_beverages',
            'food & beverages': 'spend_food_beverages',
            'cleaning services': 'spend_cleaning_services',
            'telecommunications': 'spend_telecommunications',
            'insurance': 'spend_insurance',
            'banking': 'spend_banking',
            'printing': 'spend_printing',
            'furniture': 'spend_furniture',
            'chemicals': 'spend_chemicals',
            'other': 'spend_other',
        }

        activity_key = spend_map.get(category, 'spend_other')
        return (activity_key, 'USD')

    # =========================================================================
    # METHOD 3: PHYSICAL
    # Material-based factors (kg CO2e per kg)
    # =========================================================================
    if method == 'physical':
        material_type = (row.get('Material Type') or row.get('Sub-Category') or '').strip().lower()

        # Direct mapping: Material Type → activity_key
        physical_map = {
            # Metals
            'steel - primary': 'steel_purchased_kg',
            'steel - recycled': 'steel_recycled_purchased_kg',
            'steel': 'steel_purchased_kg',
            'aluminum - primary': 'aluminum_primary_purchased_kg',
            'aluminum - recycled': 'aluminum_recycled_purchased_kg',
            'aluminum': 'aluminum_primary_purchased_kg',
            'copper': 'copper_purchased_kg',
            # Plastics
            'pet': 'plastic_pet_purchased_kg',
            'hdpe': 'plastic_hdpe_purchased_kg',
            'pvc': 'plastic_pvc_purchased_kg',
            'pp': 'plastic_pp_purchased_kg',
            'ldpe': 'plastic_ldpe_purchased_kg',
            'plastic - average': 'plastic_generic_purchased_kg',
            'average/mixed': 'plastic_generic_purchased_kg',
            # Paper & Cardboard
            'paper - virgin': 'paper_virgin_purchased_kg',
            'virgin paper': 'paper_virgin_purchased_kg',
            'paper - recycled': 'paper_recycled_purchased_kg',
            'recycled paper': 'paper_recycled_purchased_kg',
            'cardboard': 'cardboard_purchased_kg',
            # Glass
            'glass - primary': 'glass_purchased_kg',
            'primary glass': 'glass_purchased_kg',
            'glass - recycled': 'glass_recycled_purchased_kg',
            'recycled glass': 'glass_recycled_purchased_kg',
            'glass': 'glass_purchased_kg',
            # Textiles
            'cotton': 'textiles_cotton_purchased_kg',
            'polyester': 'textiles_polyester_purchased_kg',
            'textiles - mixed': 'textiles_mixed_purchased_kg',
            # Food
            'beef': 'food_meat_purchased_kg',
            'meat': 'food_meat_purchased_kg',
            'poultry': 'food_poultry_purchased_kg',
            'dairy': 'food_dairy_purchased_kg',
            'vegetables': 'food_vegetables_purchased_kg',
            'food - mixed': 'food_mixed_purchased_kg',
            'mixed food': 'food_mixed_purchased_kg',
            # Electronics
            'electronics': 'electronics_purchased_kg',
            'average electronics': 'electronics_purchased_kg',
            # Construction
            'cement': 'cement_purchased_kg',
            'portland cement': 'cement_purchased_kg',
            'concrete': 'concrete_purchased_kg',
            # Wood
            'wood': 'wood_purchased_kg',
            'timber': 'wood_purchased_kg',
            'softwood': 'wood_purchased_kg',
            'hardwood': 'wood_purchased_kg',
            # Chemicals
            'chemicals': 'chemicals_purchased_kg',
            'industrial chemicals': 'chemicals_purchased_kg',
        }

        activity_key = physical_map.get(material_type)
        if activity_key:
            return (activity_key, 'kg')

        # Fallback: try to match by category if material type not found
        category = (row.get('Category') or '').strip().lower()
        category_fallback = {
            'metals': 'steel_purchased_kg',
            'plastics': 'plastic_generic_purchased_kg',
            'paper & cardboard': 'paper_virgin_purchased_kg',
            'glass': 'glass_purchased_kg',
            'textiles': 'textiles_cotton_purchased_kg',
            'electronics': 'electronics_purchased_kg',
            'food & beverages': 'food_mixed_purchased_kg',
            'chemicals': 'chemicals_purchased_kg',
            'concrete & cement': 'concrete_purchased_kg',
            'wood & timber': 'wood_purchased_kg',
        }

        activity_key = category_fallback.get(category, 'material_generic_purchased_kg')
        return (activity_key, 'kg')

    # =========================================================================
    # FALLBACK: Unknown method - default to spend_other
    # =========================================================================
    return ('spend_other', 'USD')


def resolve_v4_capital_goods(row: dict) -> tuple[str, str]:
    """
    Resolve activity_key for v4 template 3.2 Capital Goods.

    Supports 3 methods:
    1. Physical - Asset-based (unit count or m2)
    2. Spend - Invoice amount (USD)
    3. Supplier-Specific - User provides their own emission factor
    """
    method = (row.get('Method') or '').lower().strip()
    asset_category = (row.get('Asset Category') or '').lower().strip()
    asset_type = (row.get('Asset Type') or '').lower().strip()

    # =================================================================
    # METHOD 1: SUPPLIER-SPECIFIC
    # User provides their own emission factor from EPD or supplier data
    # =================================================================
    if method == 'supplier-specific':
        # Get user's unit, default to 'unit'
        unit = (row.get('Unit') or 'unit').strip()
        return ('supplier_specific_3_2', unit)

    # =================================================================
    # METHOD 2: SPEND-BASED (EEIO)
    # Uses Economic Input-Output model for spend categories
    # =================================================================
    if method == 'spend':
        # Map asset category to spend activity_key
        spend_category_map = {
            'vehicles': 'spend_capital_vehicles',
            'it equipment': 'spend_capital_it',
            'machinery': 'spend_capital_machinery',
            'buildings': 'spend_capital_buildings',
            'furniture': 'spend_capital_furniture',
            'hvac': 'spend_capital_hvac',
            'solar': 'spend_capital_renewable',
        }
        for key, activity_key in spend_category_map.items():
            if key in asset_category:
                return (activity_key, 'USD')
        return ('spend_capital_equipment', 'USD')

    # =================================================================
    # METHOD 3: PHYSICAL (Asset-based)
    # Uses physical units (count, m2, kW)
    # =================================================================
    asset_map = {
        # Vehicles
        'small car': ('capital_car_small_unit', 'unit'),
        'medium car': ('capital_car_medium_unit', 'unit'),
        'large car': ('capital_car_large_unit', 'unit'),
        'suv': ('capital_car_large_unit', 'unit'),
        'van': ('capital_van_unit', 'unit'),
        'truck': ('capital_truck_unit', 'unit'),
        'hgv': ('capital_truck_unit', 'unit'),
        # IT Equipment
        'laptop': ('capital_laptop_unit', 'unit'),
        'desktop': ('capital_desktop_unit', 'unit'),
        'monitor': ('capital_monitor_unit', 'unit'),
        'server': ('capital_server_unit', 'unit'),
        'smartphone': ('capital_smartphone_unit', 'unit'),
        'tablet': ('capital_tablet_unit', 'unit'),
        'printer': ('capital_printer_unit', 'unit'),
        # Buildings
        'office': ('capital_building_office_m2', 'm2'),
        'warehouse': ('capital_building_warehouse_m2', 'm2'),
        'retail': ('capital_building_retail_m2', 'm2'),
        'industrial': ('capital_building_industrial_m2', 'm2'),
        # Other
        'hvac': ('capital_hvac_unit', 'unit'),
        'solar pv': ('capital_solar_unit', 'kW'),
        'solar panel': ('capital_solar_unit', 'kW'),
        'office desk': ('capital_furniture_unit', 'unit'),
        'office chair': ('capital_furniture_unit', 'unit'),
        'furniture': ('capital_furniture_unit', 'unit'),
    }

    for key, result in asset_map.items():
        if key in asset_type.lower():
            return result

    # Fallback based on asset category
    category_fallback = {
        'vehicles': ('capital_car_medium_unit', 'unit'),
        'it equipment': ('capital_laptop_unit', 'unit'),
        'buildings': ('capital_building_office_m2', 'm2'),
        'furniture': ('capital_furniture_unit', 'unit'),
        'machinery': ('capital_machinery_unit', 'unit'),
    }
    for key, result in category_fallback.items():
        if key in asset_category:
            return result

    return ('spend_capital_equipment', 'USD')


def resolve_v4_transport(row: dict) -> tuple[str, str]:
    """
    Resolve activity_key for v4 template 3.4/3.9 Transport.

    Supports 3 methods:
    1. Distance - Weight × distance based (tonne-km)
    2. Spend - Invoice amount (USD)
    3. Supplier-Specific - User provides their own emission factor
    """
    method = (row.get('Method') or '').lower().strip()
    transport_mode = (row.get('Transport Mode') or '').lower().strip()

    # METHOD 1: SUPPLIER-SPECIFIC
    # User provides their own emission factor (e.g., from logistics provider)
    if method == 'supplier-specific':
        # Unit is tonne-km by default, or user can specify
        unit = (row.get('Unit') or 'tonne-km').strip()
        return ('supplier_specific_3_4', unit)

    # METHOD 2: SPEND-BASED (EEIO)
    if method == 'spend':
        spend_map = {
            'road': ('freight_spend_road', 'USD'),
            'hgv': ('freight_spend_road', 'USD'),
            'van': ('freight_spend_road', 'USD'),
            'rail': ('freight_spend_rail', 'USD'),
            'sea': ('freight_spend_sea', 'USD'),
            'air': ('freight_spend_air', 'USD'),
        }
        for key, result in spend_map.items():
            if key in transport_mode:
                return result
        return ('freight_spend_road', 'USD')

    # METHOD 3: DISTANCE-BASED (default)
    distance_map = {
        'road-hgv': ('road_freight_hgv', 'tonne-km'),
        'road-van': ('road_freight_van', 'tonne-km'),
        'road-lgv': ('road_freight_van', 'tonne-km'),
        'rail': ('rail_freight', 'tonne-km'),
        'sea-container': ('sea_freight_container', 'tonne-km'),
        'sea-bulk': ('sea_freight_bulk', 'tonne-km'),
        'sea-tanker': ('sea_freight_tanker', 'tonne-km'),
        'air': ('air_freight', 'tonne-km'),
        'air-long': ('air_freight_long', 'tonne-km'),
        'air-short': ('air_freight_short', 'tonne-km'),
    }

    for key, result in distance_map.items():
        if key in transport_mode.lower().replace(' ', '-'):
            return result

    # Fallback: try to match just the mode
    if 'van' in transport_mode or 'lgv' in transport_mode:
        return ('road_freight_van', 'tonne-km')
    if 'hgv' in transport_mode or 'truck' in transport_mode or 'lorry' in transport_mode:
        return ('road_freight_hgv', 'tonne-km')
    if 'rail' in transport_mode or 'train' in transport_mode:
        return ('rail_freight', 'tonne-km')
    if 'sea' in transport_mode or 'ship' in transport_mode or 'maritime' in transport_mode:
        return ('sea_freight_container', 'tonne-km')
    if 'air' in transport_mode or 'plane' in transport_mode or 'flight' in transport_mode:
        return ('air_freight', 'tonne-km')

    return ('road_freight_hgv', 'tonne-km')


def resolve_v4_waste(row: dict) -> tuple[str, str]:
    """
    Resolve activity_key for v4 template 3.5 Waste.

    Supports 3 methods:
    1. Physical - Weight-based with treatment method (kg)
    2. Spend - Disposal cost (USD)
    3. Supplier-Specific - User provides own EF from waste contractor
    """
    method = (row.get('Method') or '').lower().strip()
    waste_type = (row.get('Waste Type') or '').lower().strip()
    treatment = (row.get('Treatment Method') or '').lower().strip()

    # METHOD 1: SUPPLIER-SPECIFIC
    # User provides their own emission factor (e.g., from waste contractor report)
    if method == 'supplier-specific':
        unit = (row.get('Unit') or 'kg').strip()
        return ('supplier_specific_3_5', unit)

    # METHOD 2: SPEND-BASED (EEIO)
    if method == 'spend':
        return ('waste_disposal_spend', 'USD')

    # METHOD 3: PHYSICAL (Weight-based with treatment method)
    # Treatment + Waste Type combinations
    waste_map = {
        # Landfill
        ('landfill', 'mixed'): ('waste_landfill_mixed', 'kg'),
        ('landfill', 'general'): ('waste_landfill_mixed', 'kg'),
        ('landfill', 'commercial'): ('waste_landfill_commercial', 'kg'),
        ('landfill', 'food'): ('waste_landfill_food', 'kg'),
        ('landfill', 'organic'): ('waste_landfill_food', 'kg'),
        ('landfill', 'paper'): ('waste_landfill_paper', 'kg'),
        ('landfill', 'plastic'): ('waste_landfill_plastic', 'kg'),
        ('landfill', 'wood'): ('waste_landfill_wood', 'kg'),
        ('landfill', 'textile'): ('waste_landfill_textile', 'kg'),
        # Recycling (closed-loop)
        ('recycling', 'paper'): ('waste_recycled_paper', 'kg'),
        ('recycling', 'cardboard'): ('waste_recycled_cardboard', 'kg'),
        ('recycling', 'plastic'): ('waste_recycled_plastic', 'kg'),
        ('recycling', 'metal'): ('waste_recycled_metal', 'kg'),
        ('recycling', 'aluminium'): ('waste_recycled_aluminium', 'kg'),
        ('recycling', 'aluminum'): ('waste_recycled_aluminium', 'kg'),
        ('recycling', 'steel'): ('waste_recycled_steel', 'kg'),
        ('recycling', 'glass'): ('waste_recycled_glass', 'kg'),
        ('recycling', 'mixed'): ('waste_recycled_mixed', 'kg'),
        ('recycling', 'wood'): ('waste_recycled_wood', 'kg'),
        # Incineration (with/without energy recovery)
        ('incineration', ''): ('waste_incineration', 'kg'),
        ('incineration', 'mixed'): ('waste_incineration', 'kg'),
        ('incineration', 'energy recovery'): ('waste_incineration_energy', 'kg'),
        # Composting
        ('composting', 'food'): ('waste_composted_food', 'kg'),
        ('composting', 'organic'): ('waste_composted_food', 'kg'),
        ('composting', 'garden'): ('waste_composted_garden', 'kg'),
        ('composting', 'mixed'): ('waste_composted_mixed', 'kg'),
        # Anaerobic Digestion
        ('anaerobic digestion', 'food'): ('waste_anaerobic_food', 'kg'),
        ('anaerobic digestion', 'organic'): ('waste_anaerobic_food', 'kg'),
        ('anaerobic', 'food'): ('waste_anaerobic_food', 'kg'),
        # Wastewater
        ('wastewater', ''): ('waste_wastewater', 'm3'),
        ('wastewater treatment', ''): ('waste_wastewater', 'm3'),
    }

    for (t, w), result in waste_map.items():
        if t in treatment and (not w or w in waste_type):
            return result

    # Special waste types (treatment-independent)
    # Electronic waste (WEEE)
    if 'electronic' in waste_type or 'weee' in waste_type or 'e-waste' in waste_type:
        if 'recycl' in treatment:
            return ('waste_ewaste_recycled', 'kg')
        return ('waste_ewaste', 'kg')

    # Construction & Demolition waste
    if 'construction' in waste_type or 'demolition' in waste_type or 'c&d' in waste_type:
        if 'recycl' in treatment:
            return ('waste_construction_recycled', 'kg')
        return ('waste_construction', 'kg')

    # Hazardous waste
    if 'hazardous' in waste_type or 'chemical' in waste_type:
        return ('waste_hazardous', 'kg')

    # Batteries
    if 'batter' in waste_type:
        return ('waste_batteries', 'kg')

    # Default fallback based on treatment
    if 'recycl' in treatment:
        return ('waste_recycled_mixed', 'kg')
    if 'compost' in treatment:
        return ('waste_composted_mixed', 'kg')
    if 'inciner' in treatment:
        return ('waste_incineration', 'kg')

    return ('waste_landfill_mixed', 'kg')


def resolve_v4_flights(row: dict) -> tuple[str, str]:
    """Resolve activity_key for v4 template 3.6 Flights."""
    method = (row.get('Method') or '').lower().strip()
    cabin_class = (row.get('Cabin Class') or '').lower().strip()
    origin = row.get('Origin Airport (IATA)') or ''
    dest = row.get('Destination Airport (IATA)') or ''

    if method == 'spend':
        return ('travel_spend_air', 'USD')

    # Calculate distance if airports are provided
    is_long_haul = True  # Default to long-haul
    if origin and dest:
        try:
            from app.data.airports import calculate_flight_distance
            distance = calculate_flight_distance(origin, dest)
            if distance and distance < 3700:
                is_long_haul = False
        except Exception:
            pass

    # Return factor based on class and haul type
    if 'first' in cabin_class:
        return ('flight_long_first', 'passenger-km')
    elif 'business' in cabin_class:
        return ('flight_long_business', 'passenger-km') if is_long_haul else ('flight_short_business', 'passenger-km')
    elif 'premium' in cabin_class:
        return ('flight_long_premium_economy', 'passenger-km') if is_long_haul else ('flight_short_economy', 'passenger-km')
    else:  # Economy
        return ('flight_long_economy', 'passenger-km') if is_long_haul else ('flight_short_economy', 'passenger-km')


def resolve_v4_hotels(row: dict) -> tuple[str, str]:
    """Resolve activity_key for v4 template 3.6 Hotels."""
    method = (row.get('Method') or '').lower().strip()

    if method == 'spend':
        return ('travel_spend_hotel', 'USD')

    return ('hotel_night', 'nights')


def resolve_v4_other_travel(row: dict) -> tuple[str, str]:
    """Resolve activity_key for v4 template 3.6 Other Travel."""
    travel_type = (row.get('Travel Type') or '').lower().strip()
    method = (row.get('Method') or '').lower().strip()

    if method == 'spend':
        spend_map = {
            'rail': ('travel_spend_rail', 'USD'),
            'taxi': ('travel_spend_taxi', 'USD'),
            'rental': ('travel_spend_car_rental', 'USD'),
            'bus': ('travel_spend_bus', 'USD'),
        }
        for key, result in spend_map.items():
            if key in travel_type:
                return result
        return ('travel_spend_general', 'USD')

    # Distance-based
    distance_map = {
        'rail': ('rail_domestic_km', 'km'),
        'taxi': ('taxi_km', 'km'),
        'rental': ('rental_car_km', 'km'),
        'bus': ('bus_km', 'km'),
    }

    for key, result in distance_map.items():
        if key in travel_type:
            return result

    return ('rental_car_km', 'km')


def resolve_v4_commuting(row: dict) -> tuple[str, str]:
    """Resolve activity_key for v4 template 3.7 Commuting."""
    method = (row.get('Method') or '').lower().strip()
    mode = (row.get('Transport Mode') or '').lower().strip()

    if method == 'spend':
        return ('commute_spend_general', 'USD')

    if method == 'average':
        # Use national average - country-based
        return ('commute_average', 'employee-km')

    # Survey-based: specific transport mode
    mode_map = {
        'car - petrol': ('commute_car_petrol', 'km'),
        'car - diesel': ('commute_car_diesel', 'km'),
        'car - hybrid': ('commute_car_hybrid', 'km'),
        'car - electric': ('commute_car_electric', 'km'),
        'bus': ('commute_bus', 'km'),
        'rail': ('commute_rail', 'km'),
        'metro': ('commute_rail', 'km'),
        'motorcycle': ('commute_motorcycle', 'km'),
        'e-bike': ('commute_ebike', 'km'),
        'bicycle': ('commute_bicycle', 'km'),
        'walk': ('commute_walk', 'km'),
        'work from home': ('commute_wfh_day', 'days'),
    }

    for key, result in mode_map.items():
        if key in mode:
            return result

    return ('commute_car_petrol', 'km')


def resolve_v4_leased_assets(row: dict) -> tuple[str, str]:
    """Resolve activity_key for v4 template 3.8 Leased Assets."""
    method = (row.get('Method') or '').lower().strip()
    building_type = (row.get('Building Type') or '').lower().strip()

    if method == 'spend':
        return ('leased_spend_rent', 'USD')

    if method == 'energy':
        return ('electricity_global', 'kWh')

    # Area-based
    area_map = {
        'office': ('leased_office_m2_year', 'm2-year'),
        'warehouse': ('leased_warehouse_m2_year', 'm2-year'),
        'retail': ('leased_retail_m2_year', 'm2-year'),
        'industrial': ('leased_industrial_m2_year', 'm2-year'),
        'data center': ('leased_datacenter_m2_year', 'm2-year'),
    }

    for key, result in area_map.items():
        if key in building_type:
            return result

    return ('leased_office_m2_year', 'm2-year')


def resolve_v4_processing_sold_products(row: dict) -> tuple[str, str]:
    """
    Resolve activity_key for v4 template 3.10 Processing of Sold Products.

    Covers emissions from processing of intermediate products sold by the
    reporting company by third parties (downstream manufacturers).

    Methods:
    - Site-specific: Actual processing energy/data from customer
    - Average: Industry average processing factors by product type
    - Spend: Revenue-based using EEIO factors
    """
    method = (row.get('Method') or '').lower().strip()
    product_type = (row.get('Product Type') or row.get('Product Category') or '').lower().strip()
    process_type = (row.get('Processing Type') or row.get('Process') or '').lower().strip()

    # Spend-based method
    if method == 'spend' or 'spend' in method:
        return ('processing_spend_manufacturing', 'USD')

    # Site-specific: use energy-based factor
    if method == 'site-specific' or 'site' in method:
        return ('processing_energy_kwh', 'kWh')

    # Average-data method - map by product type
    # Processing emissions per kg of product
    product_map = {
        # Metals
        'steel': ('processing_steel_kg', 'kg'),
        'aluminum': ('processing_aluminum_kg', 'kg'),
        'aluminium': ('processing_aluminum_kg', 'kg'),
        'copper': ('processing_metal_kg', 'kg'),
        'metal': ('processing_metal_kg', 'kg'),
        # Plastics
        'plastic': ('processing_plastic_kg', 'kg'),
        'pet': ('processing_plastic_kg', 'kg'),
        'hdpe': ('processing_plastic_kg', 'kg'),
        'polymer': ('processing_plastic_kg', 'kg'),
        # Chemicals
        'chemical': ('processing_chemical_kg', 'kg'),
        'petrochemical': ('processing_chemical_kg', 'kg'),
        # Textiles
        'textile': ('processing_textile_kg', 'kg'),
        'fabric': ('processing_textile_kg', 'kg'),
        'fiber': ('processing_textile_kg', 'kg'),
        # Paper/Pulp
        'paper': ('processing_paper_kg', 'kg'),
        'pulp': ('processing_paper_kg', 'kg'),
        'cardboard': ('processing_paper_kg', 'kg'),
        # Glass
        'glass': ('processing_glass_kg', 'kg'),
        # Food/Agriculture
        'food': ('processing_food_kg', 'kg'),
        'agricultural': ('processing_food_kg', 'kg'),
        'grain': ('processing_food_kg', 'kg'),
        # Electronics
        'electronic': ('processing_electronics_kg', 'kg'),
        'component': ('processing_electronics_kg', 'kg'),
        'semiconductor': ('processing_electronics_kg', 'kg'),
        # Wood
        'wood': ('processing_wood_kg', 'kg'),
        'timber': ('processing_wood_kg', 'kg'),
        'lumber': ('processing_wood_kg', 'kg'),
    }

    for key, result in product_map.items():
        if key in product_type:
            return result

    # Also check process type for clues
    process_map = {
        'melt': ('processing_metal_kg', 'kg'),
        'smelt': ('processing_metal_kg', 'kg'),
        'forge': ('processing_metal_kg', 'kg'),
        'mold': ('processing_plastic_kg', 'kg'),
        'extrude': ('processing_plastic_kg', 'kg'),
        'weave': ('processing_textile_kg', 'kg'),
        'assemble': ('processing_electronics_kg', 'kg'),
        'refine': ('processing_chemical_kg', 'kg'),
        'mill': ('processing_food_kg', 'kg'),
    }

    for key, result in process_map.items():
        if key in process_type:
            return result

    # Default: generic processing factor
    return ('processing_generic_kg', 'kg')


def resolve_v4_use_sold_products(row: dict) -> tuple[str, str]:
    """
    Resolve activity_key for v4 template 3.11 Use of Sold Products.

    Covers emissions from the use of goods sold by the reporting company
    during their expected lifetime.

    Methods:
    - Direct Use-Phase: Based on product energy consumption specs
    - Fuel-Based: For fuel-consuming products (vehicles, equipment)
    - Spend: Revenue-based using EEIO factors
    """
    method = (row.get('Method') or '').lower().strip()
    product_type = (row.get('Product Type') or row.get('Product Category') or '').lower().strip()
    energy_source = (row.get('Energy Source') or row.get('Fuel Type') or '').lower().strip()

    # Spend-based method
    if method == 'spend' or 'spend' in method:
        return ('use_phase_spend_products', 'USD')

    # Fuel-based method (for vehicles, combustion equipment)
    if method == 'fuel' or 'fuel' in method:
        fuel_map = {
            'petrol': ('use_phase_petrol_liters', 'liters'),
            'gasoline': ('use_phase_petrol_liters', 'liters'),
            'diesel': ('use_phase_diesel_liters', 'liters'),
            'natural gas': ('use_phase_natural_gas_kwh', 'kWh'),
            'lpg': ('use_phase_lpg_liters', 'liters'),
        }
        for key, result in fuel_map.items():
            if key in energy_source:
                return result
        return ('use_phase_petrol_liters', 'liters')

    # Direct use-phase (electricity-consuming products)
    product_map = {
        # Vehicles
        'vehicle': ('use_phase_vehicle_km', 'km'),
        'car': ('use_phase_vehicle_km', 'km'),
        'truck': ('use_phase_vehicle_km', 'km'),
        'motorcycle': ('use_phase_vehicle_km', 'km'),
        # Appliances
        'appliance': ('use_phase_electricity_kwh', 'kWh'),
        'refrigerator': ('use_phase_electricity_kwh', 'kWh'),
        'washing machine': ('use_phase_electricity_kwh', 'kWh'),
        'air conditioner': ('use_phase_electricity_kwh', 'kWh'),
        'hvac': ('use_phase_electricity_kwh', 'kWh'),
        'heater': ('use_phase_electricity_kwh', 'kWh'),
        # Electronics
        'electronic': ('use_phase_electricity_kwh', 'kWh'),
        'computer': ('use_phase_electricity_kwh', 'kWh'),
        'laptop': ('use_phase_electricity_kwh', 'kWh'),
        'server': ('use_phase_electricity_kwh', 'kWh'),
        'phone': ('use_phase_electricity_kwh', 'kWh'),
        'tv': ('use_phase_electricity_kwh', 'kWh'),
        'display': ('use_phase_electricity_kwh', 'kWh'),
        # Machinery
        'machinery': ('use_phase_electricity_kwh', 'kWh'),
        'equipment': ('use_phase_electricity_kwh', 'kWh'),
        'motor': ('use_phase_electricity_kwh', 'kWh'),
        'pump': ('use_phase_electricity_kwh', 'kWh'),
        # Buildings
        'building': ('use_phase_building_m2_year', 'm2-year'),
        'property': ('use_phase_building_m2_year', 'm2-year'),
        # Lighting
        'lighting': ('use_phase_electricity_kwh', 'kWh'),
        'lamp': ('use_phase_electricity_kwh', 'kWh'),
        'bulb': ('use_phase_electricity_kwh', 'kWh'),
    }

    for key, result in product_map.items():
        if key in product_type:
            return result

    # Check energy source for clues
    if 'electric' in energy_source or 'kwh' in energy_source:
        return ('use_phase_electricity_kwh', 'kWh')
    if 'fuel' in energy_source or 'petrol' in energy_source or 'diesel' in energy_source:
        return ('use_phase_petrol_liters', 'liters')

    # Default: electricity-based (most common for consumer products)
    return ('use_phase_electricity_kwh', 'kWh')


def resolve_v4_end_of_life(row: dict) -> tuple[str, str]:
    """
    Resolve activity_key for v4 template 3.12 End-of-Life Treatment of Sold Products.

    Covers emissions from disposal and treatment of products sold by the
    reporting company at end of their useful life.

    Methods:
    - Waste-Type: Based on material composition and disposal method
    - Average: Industry average disposal factors
    - Spend: Revenue-based using EEIO factors
    """
    method = (row.get('Method') or '').lower().strip()
    material_type = (row.get('Material Type') or row.get('Product Material') or '').lower().strip()
    disposal_method = (row.get('Disposal Method') or row.get('Treatment') or '').lower().strip()

    # Spend-based method
    if method == 'spend' or 'spend' in method:
        return ('eol_spend_disposal', 'USD')

    # Check for special material types first (before disposal method)
    # These materials have specific treatment requirements regardless of disposal method
    if 'battery' in material_type or 'batteries' in material_type:
        return ('eol_batteries', 'kg')
    if 'hazard' in material_type:
        return ('eol_hazardous', 'kg')

    # Map disposal method first
    if 'recycl' in disposal_method:
        # Recycling by material type
        material_recycling_map = {
            'metal': ('eol_recycling_metal', 'kg'),
            'aluminum': ('eol_recycling_metal', 'kg'),
            'steel': ('eol_recycling_metal', 'kg'),
            'plastic': ('eol_recycling_plastic', 'kg'),
            'paper': ('eol_recycling_paper', 'kg'),
            'cardboard': ('eol_recycling_paper', 'kg'),
            'glass': ('eol_recycling_glass', 'kg'),
            'electronic': ('eol_recycling_ewaste', 'kg'),
            'e-waste': ('eol_recycling_ewaste', 'kg'),
            'weee': ('eol_recycling_ewaste', 'kg'),
            'textile': ('eol_recycling_textile', 'kg'),
        }
        for key, result in material_recycling_map.items():
            if key in material_type:
                return result
        return ('eol_recycling_mixed', 'kg')

    if 'landfill' in disposal_method:
        # Landfill by material type
        landfill_map = {
            'organic': ('eol_landfill_organic', 'kg'),
            'food': ('eol_landfill_organic', 'kg'),
            'plastic': ('eol_landfill_plastic', 'kg'),
            'paper': ('eol_landfill_paper', 'kg'),
            'wood': ('eol_landfill_wood', 'kg'),
            'textile': ('eol_landfill_textile', 'kg'),
        }
        for key, result in landfill_map.items():
            if key in material_type:
                return result
        return ('eol_landfill_mixed', 'kg')

    if 'inciner' in disposal_method or 'combust' in disposal_method:
        if 'energy' in disposal_method or 'recovery' in disposal_method:
            return ('eol_incineration_energy', 'kg')
        return ('eol_incineration', 'kg')

    if 'compost' in disposal_method:
        return ('eol_composting', 'kg')

    if 'anaerobic' in disposal_method or 'digestion' in disposal_method:
        return ('eol_anaerobic_digestion', 'kg')

    # Material-based fallback (assume typical disposal mix)
    material_default_map = {
        'electronic': ('eol_ewaste_mixed', 'kg'),
        'e-waste': ('eol_ewaste_mixed', 'kg'),
        'battery': ('eol_batteries', 'kg'),
        'hazardous': ('eol_hazardous', 'kg'),
        'metal': ('eol_recycling_metal', 'kg'),  # Metals typically recycled
        'plastic': ('eol_landfill_plastic', 'kg'),  # Plastic typically landfilled
        'paper': ('eol_recycling_paper', 'kg'),  # Paper typically recycled
        'glass': ('eol_recycling_glass', 'kg'),  # Glass typically recycled
        'textile': ('eol_landfill_textile', 'kg'),
        'wood': ('eol_landfill_wood', 'kg'),
        'organic': ('eol_composting', 'kg'),
        'food': ('eol_composting', 'kg'),
    }

    for key, result in material_default_map.items():
        if key in material_type:
            return result

    # Default: mixed waste to landfill
    return ('eol_landfill_mixed', 'kg')


def resolve_v4_downstream_leased_assets(row: dict) -> tuple[str, str]:
    """
    Resolve activity_key for v4 template 3.13 Downstream Leased Assets.

    Covers emissions from assets owned by the reporting company and leased
    to other entities (lessor perspective - you own, others lease from you).

    Methods:
    - Asset-Specific: Actual energy consumption data from leased assets
    - Average: Based on building/asset type and floor area
    - Spend: Based on rental income (revenue-based)
    """
    method = (row.get('Method') or '').lower().strip()
    asset_type = (row.get('Asset Type') or row.get('Building Type') or '').lower().strip()

    # Spend-based method (based on rental income)
    if method == 'spend' or 'spend' in method or 'income' in method:
        return ('downstream_leased_spend_income', 'USD')

    # Asset-specific: Use energy-based factor
    if method == 'asset-specific' or 'asset' in method or 'energy' in method:
        energy_type = (row.get('Energy Type') or row.get('Energy Source') or '').lower().strip()
        if 'gas' in energy_type or 'natural' in energy_type:
            return ('downstream_leased_gas_kwh', 'kWh')
        return ('downstream_leased_electricity_kwh', 'kWh')

    # Average-data method - map by asset/building type
    asset_map = {
        # Commercial buildings
        'office': ('downstream_leased_office_m2', 'm2'),
        'warehouse': ('downstream_leased_warehouse_m2', 'm2'),
        'retail': ('downstream_leased_retail_m2', 'm2'),
        'industrial': ('downstream_leased_industrial_m2', 'm2'),
        'data center': ('downstream_leased_datacenter_m2', 'm2'),
        'datacenter': ('downstream_leased_datacenter_m2', 'm2'),
        # Residential
        'residential': ('downstream_leased_residential_m2', 'm2'),
        'apartment': ('downstream_leased_residential_m2', 'm2'),
        'housing': ('downstream_leased_residential_m2', 'm2'),
        # Vehicles/Equipment
        'vehicle': ('downstream_leased_vehicle_unit', 'unit'),
        'car': ('downstream_leased_vehicle_unit', 'unit'),
        'truck': ('downstream_leased_vehicle_unit', 'unit'),
        'equipment': ('downstream_leased_equipment_unit', 'unit'),
        'machinery': ('downstream_leased_equipment_unit', 'unit'),
    }

    for key, result in asset_map.items():
        if key in asset_type:
            return result

    # Default: office building per m2
    return ('downstream_leased_office_m2', 'm2')


def resolve_v4_franchises(row: dict) -> tuple[str, str]:
    """
    Resolve activity_key for v4 template 3.14 Franchises.

    Covers emissions from the operation of franchises not included in
    Scope 1 or 2 (reported by franchisor).

    Methods:
    - Franchise-Specific: Actual energy/fuel data from franchise locations
    - Average: Based on franchise type and count/floor area
    - Spend: Based on franchise revenue (revenue-based)
    """
    method = (row.get('Method') or '').lower().strip()
    franchise_type = (row.get('Franchise Type') or row.get('Business Type') or '').lower().strip()

    # Spend-based method (based on franchise revenue)
    if method == 'spend' or 'spend' in method or 'revenue' in method:
        return ('franchise_spend_revenue', 'USD')

    # Franchise-specific: Use energy-based factor
    if method == 'franchise-specific' or 'specific' in method or 'energy' in method:
        energy_type = (row.get('Energy Type') or row.get('Energy Source') or '').lower().strip()
        if 'gas' in energy_type or 'natural' in energy_type:
            return ('franchise_gas_kwh', 'kWh')
        if 'fuel' in energy_type or 'diesel' in energy_type or 'petrol' in energy_type:
            return ('franchise_fuel_liters', 'liters')
        return ('franchise_electricity_kwh', 'kWh')

    # Average-data method - map by franchise type
    # Check specific types first before generic ones
    # Convenience must come before store
    if 'convenience' in franchise_type:
        return ('franchise_convenience_unit', 'unit')

    franchise_map = {
        # Food service
        'restaurant': ('franchise_restaurant_unit', 'unit'),
        'fast food': ('franchise_fastfood_unit', 'unit'),
        'cafe': ('franchise_cafe_unit', 'unit'),
        'coffee': ('franchise_cafe_unit', 'unit'),
        'food': ('franchise_restaurant_unit', 'unit'),
        # Retail (store/shop are generic, checked after convenience)
        'retail': ('franchise_retail_m2', 'm2'),
        'store': ('franchise_retail_m2', 'm2'),
        'shop': ('franchise_retail_m2', 'm2'),
        # Services
        'hotel': ('franchise_hotel_room', 'room'),
        'hospitality': ('franchise_hotel_room', 'room'),
        'gym': ('franchise_gym_m2', 'm2'),
        'fitness': ('franchise_gym_m2', 'm2'),
        'service': ('franchise_service_unit', 'unit'),
        # Other
        'office': ('franchise_office_m2', 'm2'),
        'gas station': ('franchise_gasstation_unit', 'unit'),
        'fuel': ('franchise_gasstation_unit', 'unit'),
    }

    for key, result in franchise_map.items():
        if key in franchise_type:
            return result

    # Default: generic franchise per unit
    return ('franchise_generic_unit', 'unit')


# =============================================================================
# V4 TEMPLATE SHEET CONFIGURATIONS
# =============================================================================

V4_SHEET_CONFIGS = {
    # 3.1 Purchased Goods - v4
    # Supports 3 methods: Physical, Spend, Supplier-Specific
    '3.1 Purchased Goods': SheetConfig(
        sheet_name='3.1 Purchased Goods',
        scope=3,
        category_code='3.1',
        header_row=5,  # After title (1), info (2), warning (3), blank (4), headers (5)
        column_map={
            # Common fields
            'Method': 'calc_type',              # Physical / Spend / Supplier-Specific
            'Description': 'description',
            'Date': 'activity_date',
            # Physical method fields (Sub-Category used for material type in current template)
            'Sub-Category': 'material_type',    # Steel, Aluminum, Plastic-PET, etc.
            'Quantity': 'quantity',
            'Unit': 'unit',
            # Spend method fields
            'Category': 'spend_category',       # Office Supplies, IT Equipment, etc.
            'Spend Amount': 'spend_amount',
            'Currency': 'currency',
            # Supplier-Specific method fields
            'Supplier EF (kg CO2e/unit)': 'supplier_ef',
            'EPD Reference': 'epd_reference',
            # Optional
            'Supplier Country': 'supplier_country',
        },
        activity_key_resolver=resolve_v4_purchased_goods,
    ),

    # 3.2 Capital Goods - v4
    # Supports 3 methods: Physical, Spend, Supplier-Specific
    '3.2 Capital Goods': SheetConfig(
        sheet_name='3.2 Capital Goods',
        scope=3,
        category_code='3.2',
        header_row=5,  # Row 5 is headers (after title, instructions, method guide)
        column_map={
            'Method': 'calc_type',
            'Asset Category': 'asset_category',
            'Asset Type': 'asset_type',
            'Description': 'description',
            'Quantity': 'quantity',
            'Unit': 'unit',
            'Spend Amount': 'spend_amount',
            'Currency': 'currency',
            'Supplier EF': 'supplier_ef',  # For Supplier-Specific method
            'Purchase Date': 'activity_date',
            'Expected Lifetime (Years)': 'lifetime',
        },
        activity_key_resolver=resolve_v4_capital_goods,
    ),

    # 3.4 Upstream Transport - v4
    # Supports 3 methods: Distance, Spend, Supplier-Specific
    '3.4 Upstream Transport': SheetConfig(
        sheet_name='3.4 Upstream Transport',
        scope=3,
        category_code='3.4',
        header_row=5,  # After title, instructions, method guide
        column_map={
            'Method': 'calc_type',
            'Transport Mode': 'transport_mode',
            'Description': 'description',
            # Distance method fields
            'Weight (tonnes)': 'weight_tonnes',
            'Distance (km)': 'distance_km',
            'Origin': 'origin',
            'Destination': 'destination',
            # Spend method fields
            'Spend Amount': 'spend_amount',
            'Currency': 'currency',
            # Supplier-Specific method fields
            'Supplier EF': 'supplier_ef',  # kg CO2e per tonne-km
            'Unit': 'unit',
            # Optional
            'Related 3.1 Entry': 'related_entry',
            'Date': 'activity_date',
        },
        activity_key_resolver=resolve_v4_transport,
    ),

    # 3.5 Waste - v4
    # 3.5 Waste - v4
    # Supports 3 methods: Physical, Spend, Supplier-Specific
    '3.5 Waste': SheetConfig(
        sheet_name='3.5 Waste',
        scope=3,
        category_code='3.5',
        header_row=5,  # After title, instructions, method guide
        column_map={
            'Method': 'calc_type',
            'Waste Type': 'waste_type',
            'Treatment Method': 'treatment',
            'Description': 'description',
            # Physical method fields
            'Quantity': 'quantity',
            'Unit': 'unit',
            # Spend method fields
            'Spend Amount': 'spend_amount',
            'Currency': 'currency',
            # Supplier-Specific method fields
            'Supplier EF': 'supplier_ef',  # kg CO2e per kg
            # Optional
            'Site': 'site',
            'Date': 'activity_date',
        },
        activity_key_resolver=resolve_v4_waste,
    ),

    # 3.6 Flights - v4
    '3.6 Flights': SheetConfig(
        sheet_name='3.6 Flights',
        scope=3,
        category_code='3.6',
        header_row=4,
        column_map={
            'Method': 'calc_type',
            'Origin Airport (IATA)': 'origin_airport',
            'Destination Airport (IATA)': 'destination_airport',
            'Cabin Class': 'cabin_class',
            'Trip Type': 'trip_type',
            'Number of Passengers': 'num_passengers',
            'Spend Amount': 'spend_amount',
            'Currency': 'currency',
            'Traveler Name': 'traveler',
            'Date': 'activity_date',
        },
        activity_key_resolver=resolve_v4_flights,
    ),

    # 3.6 Hotels - v4
    '3.6 Hotels': SheetConfig(
        sheet_name='3.6 Hotels',
        scope=3,
        category_code='3.6',
        header_row=4,
        column_map={
            'Method': 'calc_type',
            'Number of Nights': 'num_nights',
            'Number of Rooms': 'num_rooms',
            'Country': 'country',
            'Spend Amount': 'spend_amount',
            'Currency': 'currency',
            'Traveler Name': 'traveler',
            'Date': 'activity_date',
        },
        activity_key_resolver=resolve_v4_hotels,
    ),

    # 3.6 Other Travel - v4
    '3.6 Other Travel': SheetConfig(
        sheet_name='3.6 Other Travel',
        scope=3,
        category_code='3.6',
        header_row=4,
        column_map={
            'Travel Type': 'travel_type',
            'Method': 'calc_type',
            'Distance (km)': 'distance_km',
            'Spend Amount': 'spend_amount',
            'Currency': 'currency',
            'Description': 'description',
            'Date': 'activity_date',
        },
        activity_key_resolver=resolve_v4_other_travel,
    ),

    # 3.7 Commuting - v4
    '3.7 Commuting': SheetConfig(
        sheet_name='3.7 Commuting',
        scope=3,
        category_code='3.7',
        header_row=4,
        column_map={
            'Method': 'calc_type',
            'Transport Mode': 'transport_mode',
            'Number of Employees': 'num_employees',
            'Avg Distance One-Way (km)': 'avg_distance_km',
            'Working Days/Year': 'working_days',
            'Country': 'country',
            '% Remote Work': 'remote_work_pct',
            'Spend Amount': 'spend_amount',
            'Currency': 'currency',
            'Site/Department': 'site',
            'Year': 'year',
        },
        activity_key_resolver=resolve_v4_commuting,
    ),

    # 3.8 Leased Assets - v4
    '3.8 Leased Assets': SheetConfig(
        sheet_name='3.8 Leased Assets',
        scope=3,
        category_code='3.8',
        header_row=5,  # After title and warning
        column_map={
            'Method': 'calc_type',
            'Building Type': 'building_type',
            'Description': 'description',
            'Floor Area (m\u00b2)': 'floor_area_m2',
            'Electricity (kWh)': 'electricity_kwh',
            'Gas (kWh)': 'gas_kwh',
            'Country': 'country',
            'Spend Amount': 'spend_amount',
            'Currency': 'currency',
            'Year': 'year',
        },
        activity_key_resolver=resolve_v4_leased_assets,
    ),

    # 3.9 Downstream Transport - v4
    '3.9 Downstream Transport': SheetConfig(
        sheet_name='3.9 Downstream Transport',
        scope=3,
        category_code='3.9',
        header_row=4,
        column_map={
            'Method': 'calc_type',
            'Description': 'description',
            'Weight (tonnes)': 'weight_tonnes',
            'Origin Country': 'origin_country',
            'Destination Country': 'destination_country',
            'Distance (km)': 'distance_km',
            'Transport Mode': 'transport_mode',
            'Spend Amount': 'spend_amount',
            'Currency': 'currency',
            'Customer/Region': 'customer',
            'Date': 'activity_date',
        },
        activity_key_resolver=resolve_v4_transport,
    ),

    # 3.10 Processing of Sold Products - v4
    # Supports 3 methods: Site-specific, Average, Spend
    '3.10 Processing of Sold Products': SheetConfig(
        sheet_name='3.10 Processing of Sold Products',
        scope=3,
        category_code='3.10',
        header_row=5,  # After title, instructions, method guide
        column_map={
            'Method': 'calc_type',
            'Product Type': 'product_type',
            'Product Category': 'product_category',
            'Processing Type': 'process_type',
            'Description': 'description',
            # Average method fields
            'Quantity Sold': 'quantity',
            'Unit': 'unit',
            # Site-specific method fields
            'Processing Energy (kWh)': 'energy_kwh',
            'Customer/Processor': 'processor',
            # Spend method fields
            'Revenue from Product': 'revenue',
            'Currency': 'currency',
            # Supplier-specific
            'Supplier EF': 'supplier_ef',
            # Optional
            'Date': 'activity_date',
        },
        activity_key_resolver=resolve_v4_processing_sold_products,
    ),

    # 3.11 Use of Sold Products - v4
    # Supports 3 methods: Direct Use-Phase, Fuel-Based, Spend
    '3.11 Use of Sold Products': SheetConfig(
        sheet_name='3.11 Use of Sold Products',
        scope=3,
        category_code='3.11',
        header_row=5,  # After title, instructions, method guide
        column_map={
            'Method': 'calc_type',
            'Product Type': 'product_type',
            'Product Category': 'product_category',
            'Description': 'description',
            # Direct use-phase fields
            'Units Sold': 'units_sold',
            'Lifetime Energy (kWh/unit)': 'lifetime_energy',
            'Lifetime (years)': 'lifetime_years',
            # Fuel-based fields
            'Lifetime Fuel (liters/unit)': 'lifetime_fuel',
            'Fuel Type': 'fuel_type',
            'Energy Source': 'energy_source',
            # Spend method fields
            'Revenue': 'revenue',
            'Currency': 'currency',
            # Optional
            'Date': 'activity_date',
        },
        activity_key_resolver=resolve_v4_use_sold_products,
    ),

    # 3.12 End-of-Life Treatment of Sold Products - v4
    # Supports 3 methods: Waste-Type, Average, Spend
    '3.12 End-of-Life Treatment': SheetConfig(
        sheet_name='3.12 End-of-Life Treatment',
        scope=3,
        category_code='3.12',
        header_row=5,  # After title, instructions, method guide
        column_map={
            'Method': 'calc_type',
            'Material Type': 'material_type',
            'Product Material': 'product_material',
            'Disposal Method': 'disposal_method',
            'Treatment': 'treatment',
            'Description': 'description',
            # Waste-type method fields
            'Weight (kg)': 'weight_kg',
            'Units Sold': 'units_sold',
            'Unit Weight (kg)': 'unit_weight',
            # Spend method fields
            'Revenue': 'revenue',
            'Currency': 'currency',
            # Optional
            'Date': 'activity_date',
        },
        activity_key_resolver=resolve_v4_end_of_life,
    ),

    # 3.13 Downstream Leased Assets - v4
    # Emissions from assets owned by reporting company and leased to others
    # Supports 3 methods: Asset-Specific, Average, Spend
    '3.13 Downstream Leased Assets': SheetConfig(
        sheet_name='3.13 Downstream Leased Assets',
        scope=3,
        category_code='3.13',
        header_row=5,  # After title, instructions, method guide
        column_map={
            'Method': 'calc_type',
            'Asset Type': 'asset_type',
            'Building Type': 'building_type',
            'Description': 'description',
            # Asset-specific method fields
            'Energy Type': 'energy_type',
            'Energy Consumption': 'energy_consumption',
            'Energy Unit': 'energy_unit',
            # Average method fields
            'Floor Area (m2)': 'floor_area',
            'Number of Units': 'num_units',
            # Spend method fields (rental income)
            'Rental Income': 'rental_income',
            'Currency': 'currency',
            # Optional
            'Tenant': 'tenant',
            'Location': 'location',
            'Date': 'activity_date',
        },
        activity_key_resolver=resolve_v4_downstream_leased_assets,
    ),

    # 3.14 Franchises - v4
    # Emissions from operation of franchises (reported by franchisor)
    # Supports 3 methods: Franchise-Specific, Average, Spend
    '3.14 Franchises': SheetConfig(
        sheet_name='3.14 Franchises',
        scope=3,
        category_code='3.14',
        header_row=5,  # After title, instructions, method guide
        column_map={
            'Method': 'calc_type',
            'Franchise Type': 'franchise_type',
            'Business Type': 'business_type',
            'Description': 'description',
            # Franchise-specific method fields
            'Energy Type': 'energy_type',
            'Energy Consumption': 'energy_consumption',
            'Fuel Consumption': 'fuel_consumption',
            # Average method fields
            'Number of Locations': 'num_locations',
            'Floor Area (m2)': 'floor_area',
            'Number of Rooms': 'num_rooms',
            # Spend method fields (franchise revenue)
            'Franchise Revenue': 'franchise_revenue',
            'Currency': 'currency',
            # Optional
            'Franchisee Name': 'franchisee_name',
            'Location': 'location',
            'Date': 'activity_date',
        },
        activity_key_resolver=resolve_v4_franchises,
    ),
}

# Add V4 configs to main SHEET_CONFIGS
SHEET_CONFIGS.update(V4_SHEET_CONFIGS)


def create_auto_detect_config(sheet_name: str, headers: list[str]) -> SheetConfig | None:
    """
    Auto-detect sheet configuration based on column headers.

    This is a fallback for sheets with non-standard names (like "Sheet1", "Data", etc.)
    """
    headers_lower = [h.lower().strip() if h else '' for h in headers]

    # Check for common patterns to determine sheet type
    has_fuel_type = any('fuel' in h for h in headers_lower)
    has_vehicle = any('vehicle' in h for h in headers_lower)
    has_refrigerant = any('refrigerant' in h or 'gas type' in h for h in headers_lower)
    has_electricity = any('electricity' in h or 'kwh' in h for h in headers_lower)
    has_quantity = any('quantity' in h or 'amount' in h for h in headers_lower)
    has_description = any('description' in h or 'desc' in h for h in headers_lower)
    has_unit = any('unit' in h for h in headers_lower)
    has_scope = any('scope' in h for h in headers_lower)
    has_category = any('category' in h for h in headers_lower)

    # Build column map based on detected headers
    column_map = {}
    for i, header in enumerate(headers):
        if not header:
            continue
        h = header.lower().strip()

        # Description variations
        if 'description' in h or h == 'desc':
            column_map[header] = 'description'
        # Quantity variations
        elif 'quantity' in h or 'amount' in h or h == 'qty':
            column_map[header] = 'quantity'
        # Unit variations
        elif 'unit' in h or 'currency' in h:
            column_map[header] = 'unit'
        # Date variations
        elif 'date' in h or 'year' in h:
            column_map[header] = 'year' if 'year' in h else 'activity_date'
        # Site variations
        elif 'site' in h or 'location' in h or 'facility' in h:
            column_map[header] = 'site'
        # Scope
        elif 'scope' in h:
            column_map[header] = 'scope'
        # Category
        elif 'category' in h:
            column_map[header] = 'category_code'
        # Fuel type
        elif 'fuel' in h:
            column_map[header] = 'fuel_type'
        # Vehicle type
        elif 'vehicle' in h:
            column_map[header] = 'vehicle_type'
        # Method/calc type
        elif 'method' in h or 'calc' in h:
            column_map[header] = 'calc_type'
        # Refrigerant
        elif 'refrigerant' in h or 'gas type' in h:
            column_map[header] = 'gas_type'
        # Country/Region
        elif 'country' in h or 'region' in h:
            column_map[header] = 'country_code'
        # Activity type/key
        elif 'activity' in h and ('type' in h or 'key' in h):
            column_map[header] = 'activity_key'

    if not has_quantity or not column_map:
        return None

    # Determine scope and category based on content indicators
    # Default to a generic spend-based approach which is most flexible
    scope = 3
    category_code = '3.1'
    resolver = lambda row: resolve_spend_generic(row, 'spend_other')

    if has_refrigerant:
        scope = 1
        category_code = '1.3'
        resolver = resolve_refrigerant
    elif has_vehicle:
        scope = 1
        category_code = '1.2'
        resolver = resolve_mobile_fuel
    elif has_fuel_type and not has_vehicle:
        scope = 1
        category_code = '1.1'
        resolver = resolve_stationary_fuel
    elif has_electricity:
        scope = 2
        category_code = '2.1'
        resolver = resolve_electricity

    return SheetConfig(
        sheet_name=sheet_name,
        scope=scope,
        category_code=category_code,
        header_row=1,  # Will be overridden by auto-detection
        column_map=column_map,
        activity_key_resolver=resolver,
        is_spend_based=(scope == 3 and category_code in ['3.1', '3.2']),
    )
