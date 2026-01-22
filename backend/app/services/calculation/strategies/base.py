"""
Base Calculator Strategy - Abstract base for all calculation strategies.
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List

from app.models.emission import EmissionFactor
from app.services.calculation.normalizer import NormalizedQuantity
from app.services.calculation.result import CalculationResult


class BaseCalculator(ABC):
    """
    Abstract base class for emission calculators.

    Each subclass implements calculation logic for specific activity categories.
    The strategy pattern allows different formulas for different emission types.
    """

    # Category codes this calculator handles
    applicable_categories: List[str] = []

    @property
    @abstractmethod
    def name(self) -> str:
        """Calculator name for logging/debugging."""
        pass

    @abstractmethod
    def calculate(
        self,
        normalized: NormalizedQuantity,
        factor: EmissionFactor,
        wtt_factor: EmissionFactor | None = None,
    ) -> CalculationResult:
        """
        Calculate emissions from normalized quantity and factor.

        Args:
            normalized: Unit-normalized quantity from Stage 1
            factor: Emission factor from Stage 2
            wtt_factor: Optional WTT factor for 3.3 calculation

        Returns:
            CalculationResult with all emission values
        """
        pass

    def _base_calculation(
        self,
        normalized: NormalizedQuantity,
        factor: EmissionFactor,
        wtt_factor: EmissionFactor | None = None,
    ) -> CalculationResult:
        """
        Standard calculation: quantity × factor.

        Most categories use this simple formula.
        Override in subclasses for special cases (flights with RF, transport with weight×distance).
        """
        qty = normalized.quantity

        # Main emissions
        co2e_kg = qty * factor.co2e_factor
        co2_kg = qty * factor.co2_factor if factor.co2_factor else None
        ch4_kg = qty * factor.ch4_factor if factor.ch4_factor else None
        n2o_kg = qty * factor.n2o_factor if factor.n2o_factor else None

        # WTT (Well-to-Tank) for Scope 3.3
        wtt_co2e_kg = None
        if wtt_factor:
            wtt_co2e_kg = qty * wtt_factor.co2e_factor

        # Build formula string
        if normalized.conversion_applied:
            formula = (
                f"{normalized.original_quantity} {normalized.original_unit} "
                f"→ {normalized.quantity:.2f} {normalized.unit} "
                f"× {factor.co2e_factor} {factor.factor_unit} "
                f"= {co2e_kg:.2f} kg CO2e"
            )
        else:
            formula = (
                f"{normalized.quantity} {normalized.unit} "
                f"× {factor.co2e_factor} {factor.factor_unit} "
                f"= {co2e_kg:.2f} kg CO2e"
            )

        return CalculationResult(
            co2e_kg=co2e_kg,
            co2_kg=co2_kg,
            ch4_kg=ch4_kg,
            n2o_kg=n2o_kg,
            wtt_co2e_kg=wtt_co2e_kg,
            emission_factor_id=factor.id,
            factor_display_name=factor.display_name,
            factor_source=factor.source,
            factor_value=factor.co2e_factor,
            factor_unit=factor.factor_unit,
            original_quantity=normalized.original_quantity,
            original_unit=normalized.original_unit,
            converted_quantity=normalized.quantity,
            converted_unit=normalized.unit,
            unit_conversion_applied=normalized.conversion_applied,
            formula=formula,
        )
