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


# Currency conversion rates to USD (2024 annual averages)
# Source: ECB, OECD
CURRENCY_RATES_TO_USD = {
    "USD": Decimal("1.00"),
    "EUR": Decimal("1.08"),
    "GBP": Decimal("1.27"),
    "ILS": Decimal("0.27"),
    "CAD": Decimal("0.74"),
    "AUD": Decimal("0.66"),
    "JPY": Decimal("0.0067"),
    "CNY": Decimal("0.14"),
    "INR": Decimal("0.012"),
    "CHF": Decimal("1.13"),
    "SEK": Decimal("0.095"),
    "NOK": Decimal("0.092"),
    "DKK": Decimal("0.145"),
}

# Categories that use spend-based calculations (EEIO factors in USD)
# Includes: Purchased Goods (3.1), Capital Goods (3.2), Fuel/Energy (3.3),
# Transportation (3.4, 3.9), Waste (3.5), Business Travel (3.6),
# Commuting (3.7), Leased Assets (3.8), and others
SPEND_BASED_CATEGORIES = {
    "1.1", "1.2",  # Stationary & Mobile combustion (can have spend method)
    "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "3.9",
    "3.10", "3.11", "3.12", "3.13", "3.14", "3.15",
}


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

        # Currency conversion for spend-based categories
        # EEIO factors are typically in kg CO2e per USD, so convert non-USD spend to USD
        quantity = input_data.quantity
        unit = input_data.unit
        currency_conversion_warning = None

        if input_data.category_code in SPEND_BASED_CATEGORIES:
            input_currency = input_data.unit.upper()
            target_currency = factor.activity_unit.upper() if factor.activity_unit else "USD"

            # Check if both are currencies and different
            if (input_currency in CURRENCY_RATES_TO_USD and
                target_currency in CURRENCY_RATES_TO_USD and
                input_currency != target_currency):

                # Convert input currency to target currency (usually USD)
                input_rate = CURRENCY_RATES_TO_USD[input_currency]
                target_rate = CURRENCY_RATES_TO_USD[target_currency]

                # Convert: input → USD → target
                quantity = (quantity * input_rate) / target_rate
                unit = target_currency

                # Add warning about the conversion
                rate = input_rate / target_rate
                currency_conversion_warning = (
                    f"Currency converted: {input_data.quantity} {input_currency} → "
                    f"{quantity:.2f} {target_currency} (rate: {rate:.4f})"
                )

        # Stage 1: NORMALIZE units to factor's expected unit
        try:
            normalized = self.normalizer.normalize(
                quantity=quantity,
                input_unit=unit,
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

        # Add currency conversion warning if applicable
        if currency_conversion_warning:
            result.warnings.append(currency_conversion_warning)

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
