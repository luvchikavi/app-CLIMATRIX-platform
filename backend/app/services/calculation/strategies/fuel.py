"""
Fuel Calculator - Scope 1.1 (Stationary) and 1.2 (Mobile) Combustion.

Handles: Natural gas, diesel, petrol, LPG, coal, vehicle fuels.
Formula: quantity × factor
WTT: Automatically tracked for Scope 3.3
"""
from app.models.emission import EmissionFactor
from app.services.calculation.normalizer import NormalizedQuantity
from app.services.calculation.result import CalculationResult
from app.services.calculation.strategies.base import BaseCalculator


class FuelCalculator(BaseCalculator):
    """
    Calculator for fuel combustion (Scope 1.1 and 1.2).

    Applicable categories:
    - 1.1: Stationary combustion (boilers, furnaces, generators)
    - 1.2: Mobile combustion (company vehicles, fleet)

    Special behavior:
    - Tracks WTT emissions for automatic Scope 3.3 aggregation
    - Handles both volume-based (liters) and energy-based (kWh) factors
    """

    applicable_categories = ["1.1", "1.2"]

    @property
    def name(self) -> str:
        return "fuel"

    def calculate(
        self,
        normalized: NormalizedQuantity,
        factor: EmissionFactor,
        wtt_factor: EmissionFactor | None = None,
    ) -> CalculationResult:
        """
        Calculate fuel combustion emissions.

        Uses base calculation since fuel is straightforward: quantity × factor.
        WTT is tracked if factor has a linked WTT factor.
        """
        result = self._base_calculation(normalized, factor, wtt_factor)

        # Add fuel-specific context to warnings if needed
        if wtt_factor:
            result.warnings.append(
                f"WTT emissions of {result.wtt_co2e_kg:.2f} kg CO2e will be added to Scope 3.3"
            )

        return result
