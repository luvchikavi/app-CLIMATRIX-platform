"""Grounding — validate a proposed row against the REAL resolver + unit graph
BEFORE it reaches preview/commit. Deterministic (no LLM).

Second anti-hallucination checkpoint (after catalog retrieval): every
(activity_key, region, year, unit) the mapper proposes is resolved through the
existing FactorResolver and unit-compatibility-checked. Anything that doesn't
resolve, or whose unit can't be safely reconciled, becomes a clarifying QUESTION
— never a silent guess. Also derives the confidence ceiling and the PCAF
data-quality score (1..5) from the resolution strategy, so CSRD/PCAF disclosures
come for free.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.calculation.resolver import FactorResolver, ResolutionStrategy
from app.services.calculation.normalizer import UnitNormalizer, UnitConversionError

# Confidence ceiling by how the factor was resolved (green/amber/red bands applied later).
_CONFIDENCE_CAP = {
    ResolutionStrategy.EXACT: 1.0,
    ResolutionStrategy.REGION: 0.9,
    ResolutionStrategy.SUPPLIER: 0.9,
    ResolutionStrategy.DEFRA_PHYSICAL: 0.8,
    ResolutionStrategy.ECOINVENT: 0.8,
    ResolutionStrategy.GLOBAL: 0.7,
    ResolutionStrategy.EEIO_SPEND: 0.5,
    ResolutionStrategy.NOT_FOUND: 0.0,
}
# PCAF data-quality score (1 best .. 5 worst).
_PCAF_SCORE = {
    ResolutionStrategy.SUPPLIER: 2,
    ResolutionStrategy.EXACT: 3,
    ResolutionStrategy.REGION: 3,
    ResolutionStrategy.DEFRA_PHYSICAL: 3,
    ResolutionStrategy.ECOINVENT: 3,
    ResolutionStrategy.GLOBAL: 4,
    ResolutionStrategy.EEIO_SPEND: 5,
    ResolutionStrategy.NOT_FOUND: 5,
}

_NORMALIZER = UnitNormalizer()


@dataclass
class GroundingVerdict:
    resolved: bool
    strategy: str
    factor_unit: str | None
    unit_ok: bool
    needs_question: bool
    confidence_cap: float
    pcaf_data_quality: int
    reason: str

    @property
    def ok(self) -> bool:
        return self.resolved and self.unit_ok


def check_unit(input_unit: str, factor_unit: str) -> tuple[bool, str]:
    """Can the client's unit be reconciled to the factor's expected unit?

    Non-convertible pairs (e.g. gas m3 <-> kWh, which needs a calorific value, not
    a linear conversion) return False -> a clarifying question, never an auto-convert.
    """
    if not input_unit or not factor_unit:
        return False, "Missing unit."
    if input_unit.strip().lower() == factor_unit.strip().lower():
        return True, "Unit matches the factor."
    try:
        _NORMALIZER.normalize(Decimal("1"), input_unit, factor_unit)
        return True, f"Unit '{input_unit}' is convertible to '{factor_unit}'."
    except UnitConversionError:
        return False, (
            f"Unit '{input_unit}' cannot be safely converted to the factor unit "
            f"'{factor_unit}' — needs a clarifying question "
            f"(e.g. gas volume vs energy needs a calorific value)."
        )


async def ground_row(
    session: AsyncSession,
    activity_key: str,
    unit: str,
    region: str = "Global",
    year: int = 2024,
) -> GroundingVerdict:
    """Resolve + unit-check one proposed row. Never raises — an unresolved or
    unit-incompatible row comes back as needs_question=True."""
    resolver = FactorResolver(session)
    res = await resolver.resolve(activity_key, region=region, year=year)

    if res.strategy == ResolutionStrategy.NOT_FOUND or res.factor is None:
        return GroundingVerdict(
            resolved=False,
            strategy=ResolutionStrategy.NOT_FOUND.value,
            factor_unit=None,
            unit_ok=False,
            needs_question=True,
            confidence_cap=0.0,
            pcaf_data_quality=5,
            reason=(
                f"No emission factor for '{activity_key}' (region {region}). "
                f"Ask the client to pick a valid activity type."
            ),
        )

    factor_unit = res.factor.activity_unit
    unit_ok, unit_reason = check_unit(unit, factor_unit)
    cap = _CONFIDENCE_CAP.get(res.strategy, 0.5)
    if not unit_ok:
        cap = min(cap, 0.4)

    return GroundingVerdict(
        resolved=True,
        strategy=res.strategy.value,
        factor_unit=factor_unit,
        unit_ok=unit_ok,
        needs_question=not unit_ok,
        confidence_cap=cap,
        pcaf_data_quality=_PCAF_SCORE.get(res.strategy, 4),
        reason=unit_reason if not unit_ok else res.message,
    )
