"""
Stage 2: Factor Resolution Service

Finds the correct emission factor using ranked fallback strategies:
1. Exact match: activity_key + region + year
2. Region specific: activity_key + region (latest year)
3. Global fallback: activity_key + region='Global'

GOVERNANCE: Only factors with status='approved' are used in calculations.
"""
from enum import Enum
from typing import NamedTuple, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.emission import EmissionFactor, EmissionFactorStatus


class ResolutionStrategy(str, Enum):
    """How the factor was resolved."""
    EXACT = "exact"           # Perfect match on key + region + year
    REGION = "region"         # Matched key + region, different year
    GLOBAL = "global"         # Fell back to Global region
    SUPPLIER = "supplier"     # Supplier-provided factor
    ECOINVENT = "ecoinvent"   # EcoInvent database (stub)
    DEFRA_PHYSICAL = "defra_physical"  # DEFRA physical material factor
    EEIO_SPEND = "eeio_spend"  # EEIO spend-based (lowest tier)
    NOT_FOUND = "not_found"   # No factor found


class ResolutionResult(NamedTuple):
    """Result of factor resolution."""
    factor: Optional[EmissionFactor]
    strategy: ResolutionStrategy
    confidence: str  # "high", "medium", "low"
    message: str


class FactorResolver:
    """
    Resolves activity_key to emission factor with ranked fallback.

    Priority:
    1. Exact: activity_key + region + year → confidence: high
    2. Region: activity_key + region (any year) → confidence: high
    3. Global: activity_key + Global → confidence: medium
    4. Not found → error

    Example:
        resolver = FactorResolver(session)
        result = await resolver.resolve("electricity_il", region="IL", year=2024)
        # Returns Israel-specific factor or falls back to Global
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def resolve(
        self,
        activity_key: str,
        region: str = "Global",
        year: int = 2024,
    ) -> ResolutionResult:
        """
        Find emission factor with fallback strategies.

        Args:
            activity_key: The explicit activity identifier (e.g., "natural_gas_volume")
            region: Organization's region (e.g., "IL", "UK", "US")
            year: Reporting year for factor selection

        Returns:
            ResolutionResult with factor and metadata
        """
        # Strategy 1: Exact match (key + region + year)
        factor = await self._find_exact(activity_key, region, year)
        if factor:
            return ResolutionResult(
                factor=factor,
                strategy=ResolutionStrategy.EXACT,
                confidence="high",
                message=f"Exact match: {activity_key} for {region} {year}"
            )

        # Strategy 2: Region-specific (key + region, latest year)
        factor = await self._find_by_region(activity_key, region)
        if factor:
            return ResolutionResult(
                factor=factor,
                strategy=ResolutionStrategy.REGION,
                confidence="high",
                message=f"Region match: {activity_key} for {region} (year {factor.year})"
            )

        # Strategy 3: Global fallback
        if region != "Global":
            factor = await self._find_by_region(activity_key, "Global")
            if factor:
                return ResolutionResult(
                    factor=factor,
                    strategy=ResolutionStrategy.GLOBAL,
                    confidence="medium",
                    message=f"Using Global factor for {activity_key} (no {region}-specific factor)"
                )

        # Strategy 4: Any region (activity_key encodes region, e.g., "electricity_il")
        factor = await self._find_any_region(activity_key)
        if factor:
            return ResolutionResult(
                factor=factor,
                strategy=ResolutionStrategy.REGION,
                confidence="high",
                message=f"Found {activity_key} for region {factor.region}"
            )

        # Not found
        return ResolutionResult(
            factor=None,
            strategy=ResolutionStrategy.NOT_FOUND,
            confidence="none",
            message=f"No emission factor found for activity_key='{activity_key}'"
        )

    async def _find_exact(
        self,
        activity_key: str,
        region: str,
        year: int
    ) -> Optional[EmissionFactor]:
        """Find factor with exact key + region + year match."""
        query = (
            select(EmissionFactor)
            .where(
                EmissionFactor.activity_key == activity_key,
                EmissionFactor.region == region,
                EmissionFactor.year == year,
                EmissionFactor.is_active == True,
                EmissionFactor.status == EmissionFactorStatus.APPROVED,  # GOVERNANCE
            )
            .limit(1)  # Handle potential duplicates in database
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _find_by_region(
        self,
        activity_key: str,
        region: str
    ) -> Optional[EmissionFactor]:
        """Find factor by key + region, using latest available year."""
        query = (
            select(EmissionFactor)
            .where(
                EmissionFactor.activity_key == activity_key,
                EmissionFactor.region == region,
                EmissionFactor.is_active == True,
                EmissionFactor.status == EmissionFactorStatus.APPROVED,  # GOVERNANCE
            )
            .order_by(EmissionFactor.year.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _find_any_region(
        self,
        activity_key: str
    ) -> Optional[EmissionFactor]:
        """Find factor by activity_key only (any region), using latest year."""
        query = (
            select(EmissionFactor)
            .where(
                EmissionFactor.activity_key == activity_key,
                EmissionFactor.is_active == True,
                EmissionFactor.status == EmissionFactorStatus.APPROVED,  # GOVERNANCE
            )
            .order_by(EmissionFactor.year.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_wtt_factor(self, factor: EmissionFactor) -> Optional[EmissionFactor]:
        """Get the WTT (Well-to-Tank) factor linked to this factor."""
        if not factor.wtt_factor_id:
            return None

        query = select(EmissionFactor).where(EmissionFactor.id == factor.wtt_factor_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def resolve_with_hierarchy(
        self,
        activity_key: str,
        material_key: str | None = None,
        region: str = "Global",
        year: int = 2024,
    ) -> ResolutionResult:
        """
        Resolve emission factor using GHG Protocol hierarchy for Cat 3.1.

        Priority (highest to lowest accuracy):
        1. Supplier-specific (EPD, LCA data) — handled in pipeline, not here
        2. EcoInvent lookup (stub — returns None until license available)
        3. DEFRA physical factor (material-specific, kg CO2e/kg)
        4. EEIO spend-based (existing database factor, lowest accuracy)

        Args:
            activity_key: The standard activity_key for database lookup (EEIO fallback)
            material_key: Material identifier for DEFRA lookup (e.g., "steel_average")
            region: Region for regional factor preference
            year: Reporting year

        Returns:
            ResolutionResult with factor and hierarchy metadata
        """
        # Tier 2: EcoInvent (stub — to implement when license available)
        ecoinvent_result = self._lookup_ecoinvent(activity_key, material_key)
        if ecoinvent_result:
            return ecoinvent_result

        # Tier 3: DEFRA physical factor
        if material_key:
            defra_result = self._lookup_defra_physical(material_key)
            if defra_result:
                return defra_result

        # Tier 4: EEIO spend-based (standard database resolution)
        result = await self.resolve(
            activity_key=activity_key,
            region=region,
            year=year,
        )

        # If found via standard resolution, mark as EEIO tier
        if result.strategy != ResolutionStrategy.NOT_FOUND:
            return ResolutionResult(
                factor=result.factor,
                strategy=ResolutionStrategy.EEIO_SPEND,
                confidence="low",
                message=f"Using EEIO spend-based factor for {activity_key} "
                        f"(lowest tier in hierarchy). Consider providing material-specific data."
            )

        return result

    @staticmethod
    def _lookup_ecoinvent(activity_key: str, material_key: str | None) -> ResolutionResult | None:
        """
        Stub for EcoInvent database lookup.

        Returns None until EcoInvent license is available and integration built.
        When implemented, this will query the EcoInvent API or local database
        for process-specific LCA data.
        """
        # TODO: Implement when EcoInvent license is available
        # This would query EcoInvent for material_key or activity_key
        # and return a ResolutionResult with strategy=ECOINVENT
        return None

    @staticmethod
    def _lookup_defra_physical(material_key: str) -> ResolutionResult | None:
        """
        Look up DEFRA physical material factor.

        Creates a virtual EmissionFactor from the DEFRA data for use
        in the calculation pipeline.
        """
        from app.data.scope3_emission_factors import get_material_factor

        factor_data = get_material_factor(material_key)
        if not factor_data:
            return None

        # Create virtual EmissionFactor for pipeline compatibility
        virtual_factor = EmissionFactor(
            scope=3,
            category_code="3.1",
            activity_key=f"defra_physical_{material_key}",
            display_name=factor_data["display_name"],
            co2e_factor=factor_data["co2e_per_kg"],
            activity_unit="kg",
            factor_unit="kg CO2e/kg",
            source=factor_data["source"],
            region="Global",
            year=2024,
        )

        return ResolutionResult(
            factor=virtual_factor,
            strategy=ResolutionStrategy.DEFRA_PHYSICAL,
            confidence="medium",
            message=f"Using DEFRA physical factor for {factor_data['display_name']}: "
                    f"{factor_data['co2e_per_kg']} kg CO2e/kg"
        )


class FactorNotFoundError(Exception):
    """Raised when no emission factor can be resolved."""
    pass
