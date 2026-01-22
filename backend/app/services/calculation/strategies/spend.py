"""
Spend Calculator - Scope 3.1 (Purchased Goods) and 3.2 (Capital Goods).

Handles: Spend-based calculations using EEIO (Economic Input-Output) factors.
Formula: spend_amount × EEIO_factor
"""
from app.models.emission import EmissionFactor
from app.services.calculation.normalizer import NormalizedQuantity
from app.services.calculation.result import CalculationResult
from app.services.calculation.strategies.base import BaseCalculator


class SpendCalculator(BaseCalculator):
    """
    Calculator for spend-based emissions (Scope 3.1, 3.2).

    Applicable categories:
    - 3.1: Purchased goods and services
    - 3.2: Capital goods

    Method:
    - Uses EEIO (Environmentally Extended Input-Output) factors
    - Factor unit is typically kg CO2e per USD/EUR/GBP

    Special behavior:
    - Lower confidence than activity-based calculations
    - Recommends supplier-specific data when available
    """

    applicable_categories = ["3.1", "3.2"]

    @property
    def name(self) -> str:
        return "spend"

    def calculate(
        self,
        normalized: NormalizedQuantity,
        factor: EmissionFactor,
        wtt_factor: EmissionFactor | None = None,
    ) -> CalculationResult:
        """
        Calculate spend-based emissions using EEIO factors.

        Note: Spend-based calculations are inherently less accurate
        than activity-based ones. Use when actual quantities aren't available.
        """
        result = self._base_calculation(normalized, factor, wtt_factor)

        # Spend-based has lower confidence
        result.confidence = "medium"
        result.warnings.append(
            "Spend-based calculation. For better accuracy, consider using supplier-specific emission data."
        )

        # EEIO factors are typically sourced from EPA or academic studies
        if "eeio" in factor.source.lower() or "useeio" in factor.source.lower():
            result.warnings.append(
                f"Using US EEIO factors. May need adjustment for non-US purchases."
            )

        return result
