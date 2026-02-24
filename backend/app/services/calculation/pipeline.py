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
from app.services.calculation.strategies.leased_assets import LeasedAssetsCalculator
from app.services.calculation.wtt import WTTService


class CalculationError(Exception):
    """Raised when emission calculation fails."""
    pass


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
        "3.8": LeasedAssetsCalculator,   # Upstream Leased Assets
        "3.9": TransportCalculator, # Downstream Transportation
        "3.12": WasteCalculator,    # End-of-Life Treatment
        "3.13": LeasedAssetsCalculator,  # Downstream Leased Assets
        "3.14": LeasedAssetsCalculator,  # Franchises
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
        # SPECIAL CASE: Supplier EF for electricity/energy (Scope 2)
        # When user provides supplier emission factor for Scope 2.
        # Works with any electricity activity_key (electricity_il, electricity_supplier, etc.)
        # This enables market-based calculation while preserving country info for dual reporting.
        # =================================================================
        if (input_data.scope == 2 and
            input_data.supplier_ef is not None and
            input_data.activity_key.startswith('electricity')):
            return await self._calculate_supplier_ef(input_data)

        # =================================================================
        # SPECIAL CASE: Supplier EF for Scope 1 (fuels, refrigerants)
        # When user provides their own emission factor (e.g., Urea with no DEFRA factor)
        # Overrides the standard database factor with the supplier-provided value
        # =================================================================
        if (input_data.supplier_ef is not None and
            input_data.scope == 1):
            return await self._calculate_scope1_supplier_ef(input_data)

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
        # Clear emission_factor_id since this is a virtual factor not in the database
        result.emission_factor_id = None
        result.warnings.append(
            "Using supplier-provided emission factor. This is the most accurate method."
        )

        return result

    async def _calculate_scope1_supplier_ef(self, input_data: ActivityInput) -> CalculationResult:
        """
        Calculate Scope 1 emissions using a supplier-provided emission factor.

        Used when the standard DEFRA/IPCC factor doesn't exist or the user has a more
        accurate supplier-specific factor (e.g., Urea/AdBlue, custom fuel blends,
        or supplier-provided refrigerant GWP).

        The supplier EF overrides the database lookup entirely.
        """
        if input_data.supplier_ef is None:
            raise CalculationError(
                "Supplier emission factor required but not provided"
            )

        # Create a "virtual" emission factor from user input
        factor = EmissionFactor(
            scope=input_data.scope,
            category_code=input_data.category_code,
            activity_key=input_data.activity_key,
            display_name=f"{input_data.activity_key} (Supplier-Provided)",
            co2e_factor=input_data.supplier_ef,
            activity_unit=input_data.unit,
            factor_unit=f"kg CO2e/{input_data.unit}",
            source="Supplier-Provided",
            region="Supplier",
            year=input_data.year,
        )

        # Normalize (usually identity for Scope 1 since units match)
        normalized = self.normalizer.normalize(
            quantity=input_data.quantity,
            input_unit=input_data.unit,
            target_unit=input_data.unit,
        )

        # Calculate using the appropriate strategy for the category
        calculator_class = self.CALCULATORS.get(
            input_data.category_code,
            self.DEFAULT_CALCULATOR
        )
        calculator = calculator_class()
        result = calculator.calculate(normalized, factor, wtt_factor=None)

        # Mark as supplier-provided with high confidence
        result.resolution_strategy = "supplier_provided"
        result.confidence = "high"
        result.emission_factor_id = None
        result.warnings.append(
            f"Using supplier-provided emission factor ({input_data.supplier_ef} kg CO2e/{input_data.unit}). "
            "This overrides the standard DEFRA/IPCC factor."
        )

        return result

    async def _calculate_supplier_ef(self, input_data: ActivityInput) -> CalculationResult:
        """
        Calculate emissions using supplier-provided emission factor for Scope 2.

        Used for market-based method when user provides the supplier's emission factor
        (e.g., from electricity supplier's environmental report).

        This enables accurate market-based reporting per GHG Protocol Scope 2 guidance.
        """
        if input_data.supplier_ef is None:
            raise CalculationError(
                "Supplier emission factor required but not provided"
            )

        # Create a "virtual" emission factor from user input
        display_name = "Electricity Supplier" if input_data.activity_key == 'electricity_supplier' else "Energy Supplier"
        factor = EmissionFactor(
            scope=input_data.scope,
            category_code=input_data.category_code,
            activity_key=input_data.activity_key,
            display_name=f"{display_name} (Market-Based)",
            co2e_factor=input_data.supplier_ef,
            activity_unit="kWh",
            factor_unit="kg CO2e/kWh",
            source="Supplier-Provided",
            region="Supplier",
            year=input_data.year,
        )

        # Normalize to kWh
        normalized = self.normalizer.normalize(
            quantity=input_data.quantity,
            input_unit=input_data.unit,
            target_unit="kWh",
        )

        # Calculate using electricity calculator
        calculator = ElectricityCalculator()
        result = calculator.calculate(normalized, factor, wtt_factor=None)

        # Mark as market-based with high confidence
        result.resolution_strategy = "market_based_supplier"
        result.confidence = "high"
        # Clear emission_factor_id since this is a virtual factor not in the database
        result.emission_factor_id = None
        result.warnings.append(
            f"Using supplier-provided emission factor ({input_data.supplier_ef} kg CO2e/kWh). "
            "This is the market-based method per GHG Protocol Scope 2 Guidance."
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
        from uuid import UUID
        from datetime import datetime
        from sqlmodel import select
        from app.models.emission import Activity, Emission

        uid = UUID(period_id)
        query = select(Activity).where(Activity.reporting_period_id == uid)
        result = await self.session.execute(query)
        activities = result.scalars().all()

        updated = 0
        failed = 0
        errors = []

        for act in activities:
            try:
                input_data = ActivityInput(
                    activity_key=act.activity_key,
                    quantity=act.quantity,
                    unit=act.unit,
                    scope=act.scope,
                    category_code=act.category_code,
                    region="Global",
                    year=2024,
                )
                calc_result = await self.calculate(input_data)

                # Update existing emission record
                em_query = select(Emission).where(Emission.activity_id == act.id)
                em_result = await self.session.execute(em_query)
                emission = em_result.scalar_one_or_none()

                if emission:
                    emission.co2e_kg = calc_result.co2e_kg
                    emission.co2_kg = calc_result.co2_kg
                    emission.ch4_kg = calc_result.ch4_kg
                    emission.n2o_kg = calc_result.n2o_kg
                    emission.wtt_co2e_kg = calc_result.wtt_co2e_kg
                    emission.emission_factor_id = calc_result.emission_factor_id
                    emission.formula = calc_result.formula
                    emission.confidence = calc_result.confidence
                    emission.resolution_strategy = calc_result.resolution_strategy
                    emission.warnings = calc_result.warnings or None
                    emission.recalculated_at = datetime.utcnow()
                    updated += 1
                else:
                    failed += 1
                    errors.append({"activity_id": str(act.id), "error": "No emission record found"})
            except Exception as e:
                failed += 1
                errors.append({"activity_id": str(act.id), "error": str(e)})

        await self.session.commit()

        return {
            "period_id": period_id,
            "total_activities": len(activities),
            "updated": updated,
            "failed": failed,
            "errors": errors[:20],
        }

    async def aggregate_wtt_for_period(self, period_id: str) -> dict:
        """
        Sum all WTT emissions for a period to populate Scope 3.3.

        WTT (Well-to-Tank) emissions from Scope 1 and 2 activities
        are automatically tracked and aggregated into Category 3.3.

        Returns dict with total_wtt_co2e_kg, by_source breakdown, and activity_count.
        """
        from uuid import UUID
        return await self.wtt_service.aggregate_wtt_for_period(UUID(period_id))
