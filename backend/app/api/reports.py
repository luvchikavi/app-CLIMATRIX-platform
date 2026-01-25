"""
Reports API endpoints.
Generates emission summaries and reports.
"""
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.api.auth import get_current_user
from app.database import get_session
from app.models.core import User, ReportingPeriod
from app.models.emission import Activity, Emission, EmissionFactor
from app.services.calculation.wtt import WTTService
from app.data.reference_data import GRID_EMISSION_FACTORS

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class ScopeSummary(BaseModel):
    """Summary for a single scope."""
    scope: int
    total_co2e_kg: float
    total_wtt_co2e_kg: float
    activity_count: int


class CategorySummary(BaseModel):
    """Summary for a single category."""
    scope: int
    category_code: str
    total_co2e_kg: float
    activity_count: int


class ReportSummaryResponse(BaseModel):
    """Complete report summary."""
    period_id: str
    period_name: str
    total_co2e_kg: float
    total_co2e_tonnes: float
    scope_1_co2e_kg: float
    scope_2_co2e_kg: float
    scope_3_co2e_kg: float
    scope_3_wtt_co2e_kg: float
    by_scope: list[ScopeSummary]
    by_category: list[CategorySummary]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/periods/{period_id}/report/summary", response_model=ReportSummaryResponse)
async def get_report_summary(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get emission summary report for a reporting period."""
    # Verify period belongs to organization
    period_query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    period_result = await session.execute(period_query)
    period = period_result.scalar_one_or_none()

    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")

    # Get totals by scope
    scope_query = (
        select(
            Activity.scope,
            func.sum(Emission.co2e_kg).label("total_co2e"),
            func.sum(Emission.wtt_co2e_kg).label("total_wtt"),
            func.count(Activity.id).label("count"),
        )
        .join(Emission, Activity.id == Emission.activity_id)
        .where(
            Activity.reporting_period_id == period_id,
            Activity.organization_id == current_user.organization_id,
        )
        .group_by(Activity.scope)
    )
    scope_result = await session.execute(scope_query)
    scope_rows = scope_result.all()

    by_scope = []
    scope_totals = {1: Decimal(0), 2: Decimal(0), 3: Decimal(0)}
    wtt_total = Decimal(0)

    for row in scope_rows:
        total_co2e = row.total_co2e or Decimal(0)
        total_wtt = row.total_wtt or Decimal(0)
        scope_totals[row.scope] = total_co2e

        # WTT from Scope 1 and 2 goes to 3.3
        if row.scope in (1, 2):
            wtt_total += total_wtt

        by_scope.append(ScopeSummary(
            scope=row.scope,
            total_co2e_kg=float(total_co2e),
            total_wtt_co2e_kg=float(total_wtt),
            activity_count=row.count,
        ))

    # Get totals by category
    category_query = (
        select(
            Activity.scope,
            Activity.category_code,
            func.sum(Emission.co2e_kg).label("total_co2e"),
            func.count(Activity.id).label("count"),
        )
        .join(Emission, Activity.id == Emission.activity_id)
        .where(
            Activity.reporting_period_id == period_id,
            Activity.organization_id == current_user.organization_id,
        )
        .group_by(Activity.scope, Activity.category_code)
        .order_by(Activity.scope, Activity.category_code)
    )
    category_result = await session.execute(category_query)
    category_rows = category_result.all()

    by_category = [
        CategorySummary(
            scope=row.scope,
            category_code=row.category_code,
            total_co2e_kg=float(row.total_co2e or 0),
            activity_count=row.count,
        )
        for row in category_rows
    ]

    total_co2e = sum(scope_totals.values())

    return ReportSummaryResponse(
        period_id=str(period_id),
        period_name=period.name,
        total_co2e_kg=float(total_co2e),
        total_co2e_tonnes=float(total_co2e / 1000),
        scope_1_co2e_kg=float(scope_totals[1]),
        scope_2_co2e_kg=float(scope_totals[2]),
        scope_3_co2e_kg=float(scope_totals[3]),
        scope_3_wtt_co2e_kg=float(wtt_total),
        by_scope=by_scope,
        by_category=by_category,
    )


@router.get("/periods/{period_id}/report/by-scope")
async def get_report_by_scope(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get detailed emissions breakdown by scope."""
    # Verify period
    period_query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    period_result = await session.execute(period_query)
    if not period_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Reporting period not found")

    # Get all activities with emissions
    query = (
        select(Activity, Emission)
        .join(Emission, Activity.id == Emission.activity_id)
        .where(
            Activity.reporting_period_id == period_id,
            Activity.organization_id == current_user.organization_id,
        )
        .order_by(Activity.scope, Activity.category_code)
    )
    result = await session.execute(query)
    rows = result.all()

    # Organize by scope
    scopes = {1: [], 2: [], 3: []}
    for activity, emission in rows:
        scopes[activity.scope].append({
            "activity_id": str(activity.id),
            "description": activity.description,
            "category_code": activity.category_code,
            "activity_key": activity.activity_key,
            "quantity": float(activity.quantity),
            "unit": activity.unit,
            "co2e_kg": float(emission.co2e_kg),
            "activity_date": activity.activity_date.isoformat(),
        })

    return {
        "period_id": str(period_id),
        "scope_1": {
            "activities": scopes[1],
            "total_co2e_kg": sum(a["co2e_kg"] for a in scopes[1]),
        },
        "scope_2": {
            "activities": scopes[2],
            "total_co2e_kg": sum(a["co2e_kg"] for a in scopes[2]),
        },
        "scope_3": {
            "activities": scopes[3],
            "total_co2e_kg": sum(a["co2e_kg"] for a in scopes[3]),
        },
    }


@router.get("/periods/{period_id}/report/scope-3-3-wtt")
async def get_wtt_report(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get Scope 3.3 (Fuel and Energy Related Activities) WTT emissions.

    This report shows the WTT (Well-to-Tank) emissions auto-calculated
    from Scope 1 and Scope 2 activities. These represent:
    - Upstream emissions from fuel extraction, refining, and transport
    - Transmission and distribution losses for electricity
    """
    # Verify period
    period_query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    period_result = await session.execute(period_query)
    period = period_result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")

    # Use WTT service to aggregate
    wtt_service = WTTService(session)
    wtt_summary = await wtt_service.aggregate_wtt_for_period(period_id)

    # Get detailed WTT breakdown by activity
    query = (
        select(Activity, Emission)
        .join(Emission, Activity.id == Emission.activity_id)
        .where(
            Activity.reporting_period_id == period_id,
            Activity.organization_id == current_user.organization_id,
            Emission.wtt_co2e_kg != None,
            Emission.wtt_co2e_kg > 0,
        )
        .order_by(Activity.scope, Activity.category_code)
    )
    result = await session.execute(query)
    rows = result.all()

    activities = []
    for activity, emission in rows:
        activities.append({
            "activity_id": str(activity.id),
            "scope": activity.scope,
            "category_code": activity.category_code,
            "activity_key": activity.activity_key,
            "description": activity.description,
            "quantity": float(activity.quantity),
            "unit": activity.unit,
            "direct_co2e_kg": float(emission.co2e_kg),
            "wtt_co2e_kg": float(emission.wtt_co2e_kg),
        })

    return {
        "period_id": str(period_id),
        "period_name": period.name,
        "scope_3_3_description": "Fuel and Energy Related Activities (WTT)",
        "total_wtt_co2e_kg": wtt_summary["total_wtt_co2e_kg"],
        "total_wtt_co2e_tonnes": wtt_summary["total_wtt_co2e_tonnes"],
        "by_source": wtt_summary["by_source"],
        "activities_with_wtt": activities,
    }


# ============================================================================
# Scope 2 Location vs Market Comparison
# ============================================================================

class Scope2ActivityComparison(BaseModel):
    """Single activity comparison between location and market-based methods."""
    activity_id: str
    description: str
    country_code: str
    country_name: str
    quantity_kwh: float
    location_factor: float
    market_factor: float | None
    location_co2e_kg: float
    market_co2e_kg: float | None
    difference_kg: float | None
    difference_percent: float | None


class Scope2ComparisonResponse(BaseModel):
    """Scope 2 location vs market comparison report."""
    period_id: str
    period_name: str
    total_activities: int
    total_location_co2e_kg: float
    total_market_co2e_kg: float | None
    total_difference_kg: float | None
    total_difference_percent: float | None
    activities: list[Scope2ActivityComparison]
    countries_without_market_factor: list[str]


def _extract_country_code(activity_key: str, factor_region: str | None) -> str | None:
    """
    Extract country code from activity_key or factor region.

    Examples:
    - electricity_uk -> UK
    - electricity_il -> IL
    - electricity_us_ca -> US
    - electricity_global -> None (use Global)
    """
    if factor_region and factor_region != "Global":
        return factor_region.upper()

    # Extract from activity_key like "electricity_uk", "electricity_us_ca"
    parts = activity_key.lower().replace("electricity_", "").split("_")
    if parts and len(parts[0]) == 2:
        return parts[0].upper()

    return None


@router.get("/periods/{period_id}/report/scope-2-comparison", response_model=Scope2ComparisonResponse)
async def get_scope2_comparison(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get Scope 2 location-based vs market-based comparison.

    This report shows the difference between:
    - Location-based: Uses grid average emission factor for region
    - Market-based: Uses residual mix factor (for GHG Protocol dual reporting)

    Market-based is typically higher as it excludes tracked renewable energy.
    """
    # Verify period
    period_query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    period_result = await session.execute(period_query)
    period = period_result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")

    # Get all Scope 2 activities with their emissions and factors
    query = (
        select(Activity, Emission, EmissionFactor)
        .join(Emission, Activity.id == Emission.activity_id)
        .join(EmissionFactor, Emission.emission_factor_id == EmissionFactor.id)
        .where(
            Activity.reporting_period_id == period_id,
            Activity.organization_id == current_user.organization_id,
            Activity.scope == 2,
        )
        .order_by(Activity.activity_date)
    )
    result = await session.execute(query)
    rows = result.all()

    activities = []
    total_location = Decimal(0)
    total_market = Decimal(0)
    countries_without_market = set()
    has_any_market_factor = False

    for activity, emission, factor in rows:
        # Get country code from activity_key or factor region
        country_code = _extract_country_code(activity.activity_key, factor.region)

        # Get grid factors for this country
        grid_factor = GRID_EMISSION_FACTORS.get(country_code) if country_code else None

        # If no specific country factor, use Global
        if not grid_factor:
            grid_factor = GRID_EMISSION_FACTORS.get("GLOBAL", {
                "country_name": "Global Average",
                "location_factor": Decimal("0.436"),
                "market_factor": None,
            })
            country_name = grid_factor.get("country_name", "Global Average")
        else:
            country_name = grid_factor.get("country_name", country_code)

        location_factor = grid_factor.get("location_factor", factor.co2e_factor)
        market_factor = grid_factor.get("market_factor")

        # Calculate quantity in kWh (may already be in kWh)
        quantity_kwh = float(activity.quantity)

        # Calculate emissions with both methods
        location_co2e = quantity_kwh * float(location_factor)
        market_co2e = quantity_kwh * float(market_factor) if market_factor else None

        # Track totals
        total_location += Decimal(str(location_co2e))
        if market_co2e is not None:
            total_market += Decimal(str(market_co2e))
            has_any_market_factor = True
        else:
            countries_without_market.add(country_name or country_code or "Unknown")

        # Calculate difference
        difference_kg = None
        difference_percent = None
        if market_co2e is not None and location_co2e > 0:
            difference_kg = market_co2e - location_co2e
            difference_percent = (difference_kg / location_co2e) * 100

        activities.append(Scope2ActivityComparison(
            activity_id=str(activity.id),
            description=activity.description,
            country_code=country_code or "GLOBAL",
            country_name=country_name,
            quantity_kwh=quantity_kwh,
            location_factor=float(location_factor),
            market_factor=float(market_factor) if market_factor else None,
            location_co2e_kg=location_co2e,
            market_co2e_kg=market_co2e,
            difference_kg=difference_kg,
            difference_percent=difference_percent,
        ))

    # Calculate total difference
    total_difference_kg = None
    total_difference_percent = None
    if has_any_market_factor and total_location > 0:
        total_difference_kg = float(total_market - total_location)
        total_difference_percent = (total_difference_kg / float(total_location)) * 100

    return Scope2ComparisonResponse(
        period_id=str(period_id),
        period_name=period.name,
        total_activities=len(activities),
        total_location_co2e_kg=float(total_location),
        total_market_co2e_kg=float(total_market) if has_any_market_factor else None,
        total_difference_kg=total_difference_kg,
        total_difference_percent=total_difference_percent,
        activities=activities,
        countries_without_market_factor=list(countries_without_market),
    )


# ============================================================================
# Data Quality Report
# ============================================================================

class DataQualityBreakdown(BaseModel):
    """Breakdown of activities by data quality score."""
    score: int
    score_label: str
    activity_count: int
    total_co2e_kg: float
    percentage: float


class DataQualitySummaryResponse(BaseModel):
    """Data quality summary for a reporting period."""
    period_id: str
    period_name: str
    total_activities: int
    weighted_average_score: float
    score_interpretation: str
    by_score: list[DataQualityBreakdown]


# Score labels for PCAF methodology
DATA_QUALITY_LABELS = {
    1: "Verified Data",
    2: "Primary Data",
    3: "Activity Average",
    4: "Spend-Based",
    5: "Estimated",
}


@router.get("/periods/{period_id}/report/data-quality", response_model=DataQualitySummaryResponse)
async def get_data_quality_summary(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get data quality summary for a reporting period.

    Returns weighted average score (by CO2e) and breakdown by quality level.
    Lower score = better quality (PCAF methodology).
    """
    # Verify period belongs to organization
    period_query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    period_result = await session.execute(period_query)
    period = period_result.scalar_one_or_none()

    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")

    # Get data quality breakdown
    quality_query = (
        select(
            Activity.data_quality_score,
            func.count(Activity.id).label("count"),
            func.sum(Emission.co2e_kg).label("total_co2e"),
        )
        .join(Emission, Activity.id == Emission.activity_id)
        .where(
            Activity.reporting_period_id == period_id,
            Activity.organization_id == current_user.organization_id,
        )
        .group_by(Activity.data_quality_score)
    )
    quality_result = await session.execute(quality_query)
    quality_rows = quality_result.all()

    # Calculate totals
    total_activities = sum(row.count for row in quality_rows)
    total_co2e = sum(float(row.total_co2e or 0) for row in quality_rows)

    # Build breakdown and calculate weighted average
    by_score = []
    weighted_sum = Decimal(0)

    for score in range(1, 6):  # 1-5
        matching = next((r for r in quality_rows if (r.data_quality_score or 5) == score), None)
        count = matching.count if matching else 0
        co2e = float(matching.total_co2e or 0) if matching else 0.0
        pct = (co2e / total_co2e * 100) if total_co2e > 0 else 0.0

        by_score.append(DataQualityBreakdown(
            score=score,
            score_label=DATA_QUALITY_LABELS[score],
            activity_count=count,
            total_co2e_kg=co2e,
            percentage=round(pct, 1),
        ))

        if co2e > 0:
            weighted_sum += Decimal(str(score)) * Decimal(str(co2e))

    # Calculate weighted average score (weighted by CO2e)
    weighted_avg = float(weighted_sum / Decimal(str(total_co2e))) if total_co2e > 0 else 5.0

    # Interpret the score
    if weighted_avg <= 1.5:
        interpretation = "Excellent - Mostly verified/primary data"
    elif weighted_avg <= 2.5:
        interpretation = "Good - Mix of primary and modeled data"
    elif weighted_avg <= 3.5:
        interpretation = "Fair - Significant use of average factors"
    elif weighted_avg <= 4.5:
        interpretation = "Limited - Primarily spend-based estimates"
    else:
        interpretation = "Low - Mostly estimated data, consider improving data sources"

    return DataQualitySummaryResponse(
        period_id=str(period_id),
        period_name=period.name,
        total_activities=total_activities,
        weighted_average_score=round(weighted_avg, 2),
        score_interpretation=interpretation,
        by_score=by_score,
    )
