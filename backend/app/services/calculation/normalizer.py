"""
Stage 1: Unit Normalization Service

Uses Pint library for physics-grade unit conversions.
Converts user input to the unit expected by the emission factor.
"""
from decimal import Decimal
from typing import NamedTuple

import pint

# Initialize unit registry with custom definitions
ureg = pint.UnitRegistry()

# Add custom units for GHG calculations
ureg.define("tonne = 1000 * kilogram = t = metric_ton")
ureg.define("therm = 105.5 * megajoule")
ureg.define("cubic_meter = meter ** 3 = m3 = m³")
ureg.define("kilowatt_hour = kilowatt * hour = kWh")
ureg.define("passenger_km = kilometer = pkm")
ureg.define("tonne_km = tonne * kilometer = tkm")


class NormalizedQuantity(NamedTuple):
    """Result of unit normalization."""
    quantity: Decimal
    unit: str
    original_quantity: Decimal
    original_unit: str
    conversion_factor: Decimal
    conversion_applied: bool


# Unit aliases - map common variations to Pint-compatible units
UNIT_ALIASES = {
    # Volume
    "m3": "cubic_meter",
    "m³": "cubic_meter",
    "cubic meters": "cubic_meter",
    "liters": "liter",
    "litres": "liter",
    "l": "liter",
    "L": "liter",
    "gallons": "gallon",
    "gal": "gallon",
    "us_gallon": "gallon",
    "uk_gallon": "imperial_gallon",

    # Mass
    "kg": "kilogram",
    "kilograms": "kilogram",
    "tonnes": "tonne",
    "tons": "tonne",
    "t": "tonne",
    "metric tons": "tonne",
    "lbs": "pound",
    "pounds": "pound",

    # Energy
    "kwh": "kilowatt_hour",
    "kWh": "kilowatt_hour",
    "KWH": "kilowatt_hour",
    "mwh": "megawatt_hour",
    "MWh": "megawatt_hour",
    "therms": "therm",
    "mj": "megajoule",
    "MJ": "megajoule",
    "gj": "gigajoule",
    "GJ": "gigajoule",

    # Distance
    "km": "kilometer",
    "kilometers": "kilometer",
    "kilometres": "kilometer",
    "mi": "mile",
    "miles": "mile",

    # Currency (pass-through, no conversion)
    "usd": "USD",
    "USD": "USD",
    "eur": "EUR",
    "EUR": "EUR",
    "gbp": "GBP",
    "GBP": "GBP",
    "ils": "ILS",
    "ILS": "ILS",

    # Special units
    "nights": "nights",
    "night": "nights",
    "pkm": "passenger_km",
    "passenger-km": "passenger_km",
    "tkm": "tonne_km",
    "tonne-km": "tonne_km",
}

# Units that shouldn't be converted (currencies, counts)
NON_CONVERTIBLE_UNITS = {"USD", "EUR", "GBP", "ILS", "nights", "units", "each"}


class UnitNormalizer:
    """
    Converts user input units to emission factor expected units.

    Example:
        normalizer = UnitNormalizer()
        result = normalizer.normalize(1000, "gallons", "liters")
        # result.quantity = 3785.41
        # result.unit = "liters"
    """

    def __init__(self):
        self.ureg = ureg

    def _resolve_alias(self, unit: str) -> str:
        """Resolve unit aliases to Pint-compatible names."""
        return UNIT_ALIASES.get(unit, unit)

    def normalize(
        self,
        quantity: Decimal,
        input_unit: str,
        target_unit: str
    ) -> NormalizedQuantity:
        """
        Convert quantity from input_unit to target_unit.

        Args:
            quantity: The amount to convert
            input_unit: Unit provided by user
            target_unit: Unit expected by emission factor

        Returns:
            NormalizedQuantity with converted value and metadata
        """
        input_resolved = self._resolve_alias(input_unit)
        target_resolved = self._resolve_alias(target_unit)

        # If units match, no conversion needed
        if input_resolved == target_resolved:
            return NormalizedQuantity(
                quantity=quantity,
                unit=target_unit,
                original_quantity=quantity,
                original_unit=input_unit,
                conversion_factor=Decimal("1"),
                conversion_applied=False,
            )

        # Non-convertible units (currencies, counts)
        if input_resolved in NON_CONVERTIBLE_UNITS or target_resolved in NON_CONVERTIBLE_UNITS:
            if input_resolved != target_resolved:
                raise UnitConversionError(
                    f"Cannot convert between '{input_unit}' and '{target_unit}'. "
                    f"These units are not compatible."
                )
            return NormalizedQuantity(
                quantity=quantity,
                unit=target_unit,
                original_quantity=quantity,
                original_unit=input_unit,
                conversion_factor=Decimal("1"),
                conversion_applied=False,
            )

        # Use Pint for conversion
        try:
            input_qty = float(quantity) * self.ureg(input_resolved)
            output_qty = input_qty.to(target_resolved)
            converted = Decimal(str(output_qty.magnitude))
            factor = Decimal(str(output_qty.magnitude / float(quantity))) if quantity else Decimal("1")

            return NormalizedQuantity(
                quantity=converted,
                unit=target_unit,
                original_quantity=quantity,
                original_unit=input_unit,
                conversion_factor=factor,
                conversion_applied=True,
            )
        except pint.DimensionalityError:
            raise UnitConversionError(
                f"Cannot convert '{input_unit}' to '{target_unit}'. "
                f"Incompatible dimensions (e.g., mass vs volume)."
            )
        except pint.UndefinedUnitError as e:
            raise UnitConversionError(
                f"Unknown unit: {e}. "
                f"Please use standard units like kg, liters, kWh, km."
            )


class UnitConversionError(Exception):
    """Raised when unit conversion fails."""
    pass
