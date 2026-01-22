"""
Unit conversions for the application.

Used by the calculation pipeline to convert user input units
to the units expected by emission factors.
"""
from decimal import Decimal

UNIT_CONVERSIONS = [
    # Volume
    {"from_unit": "gallons", "to_unit": "liters", "multiplier": Decimal("3.78541"), "category": "volume"},
    {"from_unit": "gal", "to_unit": "liters", "multiplier": Decimal("3.78541"), "category": "volume"},
    {"from_unit": "L", "to_unit": "liters", "multiplier": Decimal("1"), "category": "volume"},
    {"from_unit": "ft3", "to_unit": "m3", "multiplier": Decimal("0.0283168"), "category": "volume"},
    {"from_unit": "cubic feet", "to_unit": "m3", "multiplier": Decimal("0.0283168"), "category": "volume"},
    {"from_unit": "cubic meters", "to_unit": "m3", "multiplier": Decimal("1"), "category": "volume"},

    # Mass
    {"from_unit": "tonnes", "to_unit": "kg", "multiplier": Decimal("1000"), "category": "mass"},
    {"from_unit": "t", "to_unit": "kg", "multiplier": Decimal("1000"), "category": "mass"},
    {"from_unit": "lb", "to_unit": "kg", "multiplier": Decimal("0.453592"), "category": "mass"},
    {"from_unit": "lbs", "to_unit": "kg", "multiplier": Decimal("0.453592"), "category": "mass"},
    {"from_unit": "oz", "to_unit": "kg", "multiplier": Decimal("0.0283495"), "category": "mass"},
    {"from_unit": "g", "to_unit": "kg", "multiplier": Decimal("0.001"), "category": "mass"},

    # Distance
    {"from_unit": "miles", "to_unit": "km", "multiplier": Decimal("1.60934"), "category": "distance"},
    {"from_unit": "mi", "to_unit": "km", "multiplier": Decimal("1.60934"), "category": "distance"},
    {"from_unit": "meters", "to_unit": "km", "multiplier": Decimal("0.001"), "category": "distance"},
    {"from_unit": "m", "to_unit": "km", "multiplier": Decimal("0.001"), "category": "distance"},

    # Energy
    {"from_unit": "MWh", "to_unit": "kWh", "multiplier": Decimal("1000"), "category": "energy"},
    {"from_unit": "GWh", "to_unit": "kWh", "multiplier": Decimal("1000000"), "category": "energy"},
    {"from_unit": "MJ", "to_unit": "kWh", "multiplier": Decimal("0.277778"), "category": "energy"},
    {"from_unit": "GJ", "to_unit": "kWh", "multiplier": Decimal("277.778"), "category": "energy"},
    {"from_unit": "therm", "to_unit": "kWh", "multiplier": Decimal("29.3071"), "category": "energy"},
    {"from_unit": "BTU", "to_unit": "kWh", "multiplier": Decimal("0.000293071"), "category": "energy"},

    # Currency (approximate conversion rates - should be updated)
    {"from_unit": "EUR", "to_unit": "USD", "multiplier": Decimal("1.08"), "category": "currency"},
    {"from_unit": "GBP", "to_unit": "USD", "multiplier": Decimal("1.27"), "category": "currency"},
    {"from_unit": "ILS", "to_unit": "USD", "multiplier": Decimal("0.27"), "category": "currency"},
]
