"""
Electricity Calculator - Scope 2 (Purchased Energy).

Handles: Grid electricity, district heating, steam, cooling.
Supports: Location-based and market-based methods.
Formula: quantity × grid_factor (location) or supplier_factor (market)
"""
from app.models.emission import EmissionFactor
from app.services.calculation.normalizer import NormalizedQuantity
from app.services.calculation.result import CalculationResult
from app.services.calculation.strategies.base import BaseCalculator


class ElectricityCalculator(BaseCalculator):
    """
    Calculator for purchased energy (Scope 2).

    Applicable categories:
    - 2: Purchased electricity, heat, steam, cooling

    Methods:
    - Location-based: Uses grid average emission factor for region
    - Market-based: Uses supplier-specific factor (if available)

    Special behavior:
    - Tracks T&D (transmission & distribution) losses for Scope 3.3
    - Region-specific factors (IL, UK, US, EU have different grid mixes)
    """

    applicable_categories = ["2", "2.1", "2.2"]

    @property
    def name(self) -> str:
        return "electricity"

    def calculate(
        self,
        normalized: NormalizedQuantity,
        factor: EmissionFactor,
        wtt_factor: EmissionFactor | None = None,
    ) -> CalculationResult:
        """
        Calculate Scope 2 emissions from purchased energy.

        Uses location-based method by default.
        Market-based requires supplier-specific factor (future enhancement).
        """
        result = self._base_calculation(normalized, factor, wtt_factor)

        # Electricity-specific context
        if "il" in factor.activity_key.lower() or factor.region == "IL":
            result.warnings.append(
                "Using Israel Electric Corporation grid factor"
            )
        elif "uk" in factor.activity_key.lower() or factor.region == "UK":
            result.warnings.append(
                "Using UK National Grid factor"
            )
        elif factor.region == "Global":
            result.warnings.append(
                "Using global average grid factor. Consider using region-specific factor for accuracy."
            )

        # WTT for electricity (T&D losses + upstream)
        if wtt_factor:
            result.warnings.append(
                f"T&D and generation losses of {result.wtt_co2e_kg:.2f} kg CO2e will be added to Scope 3.3"
            )

        return result
