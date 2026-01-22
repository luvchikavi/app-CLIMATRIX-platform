"""
Calculation Pipeline - Main orchestrator for emission calculations.

3-Stage Architecture:
1. NORMALIZE: Convert user input units to factor-expected units (Pint)
2. RESOLVE: Find emission factor with fallback strategies
3. CALCULATE: Apply appropriate calculation strategy

This separates business logic from HTTP concerns.
The API layer just calls pipeline.calculate() - no business logic in controllers.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Type

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.emission import EmissionFactor
from app.services.calculation.normalizer import UnitNormalizer, UnitConversionError
from app.services.calculation.resolver import FactorResolver, ResolutionStrategy, FactorNotFoundError
from app.services.calculation.result import CalculationResult
from app.services.calculation.strategies.base import BaseCalculator
from app.services.calculation.strategies.fuel import FuelCalculator
from app.services.calculation.strategies.electricity import ElectricityCalculator
from app.services.calculation.strategies.spend import SpendCalculator
from app.services.calculation.strategies.flight import FlightCalculator
from app.services.calculation.strategies.transport import TransportCalculator
from app.services.calculation.strategies.waste import WasteCalculator
from app.services.calculation.strategies.refrigerant import RefrigerantCalculator
from app.services.calculation.wtt import WTTService


@dataclass
class ActivityInput:
    """Input data for calculation pipeline."""
    activity_key: str
    quantity: Decimal
    unit: str
    scope: int
    category_code: str
    region: str = "Global"
    year: int = 2024
    # For Supplier-Specific method (3.1, 3.2): user provides their own EF
    supplier_ef: Decimal | None = None
    supplier_ef_unit: str | None = None  # e.g., "kg CO2e/kg"


class CalculationPipeline:
    """
    Main orchestrator for emission calculations.

    Separates concerns:
    - API layer handles HTTP (request/response, auth, validation)
    - Pipeline handles business logic (normalization, factor lookup, calculation)

    Usage:
        pipeline = CalculationPipeline(session)
        result = await pipeline.calculate(ActivityInput(
            activity_key="natural_gas_volume",
            quantity=Decimal("1000"),
            unit="m3",
            scope=1,
            category_code="1.1",
            region="Global"
        ))
    """

    # Map category codes to calculator strategies
    CALCULATORS: Dict[str, Type[BaseCalculator]] = {
        # Scope 1 - Direct Emissions
        "1.1": FuelCalculator,      # Stationary Combustion
        "1.2": FuelCalculator,      # Mobile Combustion
        "1.3": RefrigerantCalculator,  # Fugitive Emissions (refrigerants, SF6)

        # Scope 2 - Indirect Energy
        "2": ElectricityCalculator,
        "2.1": ElectricityCalculator,   # Purchased Electricity
        "2.2": ElectricityCalculator,   # Purchased Heat/Steam

        # Scope 3 - Value Chain
        "3.1": SpendCalculator,     # Purchased Goods & Services
        "3.2": SpendCalculator,     # Capital Goods
        "3.3": FuelCalculator,      # Fuel & Energy Related (WTT auto-calculated)
        "3.4": TransportCalculator, # Upstream Transportation
        "3.5": WasteCalculator,     # Waste Generated in Operations
        "3.6": FlightCalculator,    # Business Travel
        "3.7": FuelCalculator,      # Employee Commuting (distance-based)
        "3.9": TransportCalculator, # Downstream Transportation
        "3.12": WasteCalculator,    # End-of-Life Treatment
    }

    # Default calculator for categories without specific strategy
    DEFAULT_CALCULATOR = FuelCalculator

    def __init__(self, session: AsyncSession):
        self.session = session
        self.normalizer = UnitNormalizer()
        self.resolver = FactorResolver(session)
        self.wtt_service = WTTService(session)

    async def calculate(self, input_data: ActivityInput) -> CalculationResult:
        """
        Execute the 3-stage calculation pipeline.

        Stage 1: NORMALIZE - Convert units
        Stage 2: RESOLVE - Find emission factor (or use supplier-provided)
        Stage 3: CALCULATE - Apply strategy

        Args:
            input_data: Activity details from user

        Returns:
            CalculationResult with emissions and metadata

        Raises:
            FactorNotFoundError: No factor for activity_key
            UnitConversionError: Incompatible units
        """
        # =================================================================
        # SPECIAL CASE: Supplier-Specific Method
        # User provides their own emission factor (EPD, supplier data)
        # =================================================================
        if input_data.activity_key.startswith('supplier_specific'):
            return await self._calculate_supplier_specific(input_data)

        # =================================================================
        # STANDARD FLOW: Lookup factor from database
        # =================================================================

        # Stage 2: RESOLVE factor (do this first to get expected unit)
        resolution = await self.resolver.resolve(
            activity_key=input_data.activity_key,
            region=input_data.region,
            year=input_data.year,
        )

        if resolution.strategy == ResolutionStrategy.NOT_FOUND:
            raise FactorNotFoundError(resolution.message)

        factor = resolution.factor

        # Stage 1: NORMALIZE units to factor's expected unit
        try:
            normalized = self.normalizer.normalize(
                quantity=input_data.quantity,
                input_unit=input_data.unit,
                target_unit=factor.activity_unit,
            )
        except UnitConversionError as e:
            raise CalculationError(str(e))

        # Get WTT factor using WTT service (pattern-based mapping)
        wtt_factor = await self.wtt_service.get_wtt_factor(
            input_data.activity_key,
            normalized.unit  # Use the converted unit
        )

        # Stage 3: CALCULATE using appropriate strategy
        calculator_class = self.CALCULATORS.get(
            input_data.category_code,
            self.DEFAULT_CALCULATOR
        )
        calculator = calculator_class()
        result = calculator.calculate(normalized, factor, wtt_factor)

        # Add resolution metadata
        result.resolution_strategy = resolution.strategy.value
        if resolution.strategy == ResolutionStrategy.GLOBAL:
            result.confidence = "medium"
            result.warnings.append(resolution.message)

        return result

    async def _calculate_supplier_specific(self, input_data: ActivityInput) -> CalculationResult:
        """
        Calculate emissions using supplier-provided emission factor.

        Used when:
        - User has EPD (Environmental Product Declaration) data
        - Supplier provides their own emission factor

        This is the most accurate method per GHG Protocol hierarchy.
        """
        if input_data.supplier_ef is None:
            raise CalculationError(
                "Supplier-Specific method requires 'supplier_ef' field with "
                "emission factor in kg CO2e per unit"
            )

        # Create a "virtual" emission factor from user input
        factor = EmissionFactor(
            scope=input_data.scope,
            category_code=input_data.category_code,
            activity_key=input_data.activity_key,
            display_name="Supplier-Specific Factor",
            co2e_factor=input_data.supplier_ef,
            activity_unit=input_data.unit,
            factor_unit=f"kg CO2e/{input_data.unit}",
            source="Supplier-Provided",
            region="Supplier",
            year=input_data.year,
        )

        # Normalize (usually no conversion needed for supplier-specific)
        normalized = self.normalizer.normalize(
            quantity=input_data.quantity,
            input_unit=input_data.unit,
            target_unit=input_data.unit,  # No conversion
        )

        # Calculate using simple spend calculator (just quantity × factor)
        calculator = SpendCalculator()
        result = calculator.calculate(normalized, factor, wtt_factor=None)

        # Mark as supplier-specific with high confidence
        result.resolution_strategy = "supplier_specific"
        result.confidence = "high"
        result.warnings.append(
            "Using supplier-provided emission factor. This is the most accurate method."
        )

        return result

    async def recalculate_for_period(self, period_id: str) -> Dict[str, any]:
        """
        Recalculate all emissions for a reporting period.

        Useful when:
        - Emission factors are updated
        - User wants to refresh with latest factors

        Returns summary of recalculated emissions.
        """
        # TODO: Implement batch recalculation
        pass

    async def aggregate_wtt_for_period(self, period_id: str) -> Decimal:
        """
        Sum all WTT emissions for a period to populate Scope 3.3.

        WTT (Well-to-Tank) emissions from Scope 1 and 2 activities
        are automatically tracked and aggregated into Category 3.3.

        Returns total WTT emissions in kg CO2e.
        """
        # TODO: Implement WTT aggregation
        pass


class CalculationError(Exception):
    """Raised when calculation fails."""
    pass
