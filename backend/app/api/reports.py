"""
Reports API endpoints.
Generates emission summaries and reports.

Includes ISO 14064-1 compliant GHG inventory reports.
"""
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
import io

from app.api.auth import get_current_user
from app.database import get_session
from app.models.core import User, ReportingPeriod, Organization, PeriodStatus
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
# ISO 14064-1 GHG Inventory Report Schemas
# ============================================================================

class OrganizationInfo(BaseModel):
    """Organization information for report header."""
    name: str
    country: Optional[str]
    industry: Optional[str]
    base_year: Optional[int]


class ReportingBoundary(BaseModel):
    """Organizational and operational boundaries."""
    consolidation_approach: str  # "operational_control" or "equity_share"
    included_facilities: int
    reporting_period_start: str
    reporting_period_end: str


class EmissionSourceDetail(BaseModel):
    """Detail for a single emission source/activity type."""
    activity_key: str
    display_name: str
    category_code: str
    activity_count: int
    total_quantity: float
    unit: str
    total_co2e_kg: float
    total_co2e_tonnes: float
    emission_factor: float
    factor_source: str
    factor_unit: str
    avg_data_quality: float


class ScopeDetail(BaseModel):
    """Detailed breakdown for a scope."""
    scope: int
    scope_name: str
    total_co2e_kg: float
    total_co2e_tonnes: float
    percentage_of_total: float
    activity_count: int
    avg_data_quality: float
    sources: list[EmissionSourceDetail]


class MethodologySection(BaseModel):
    """Methodology description for the report."""
    calculation_approach: str
    emission_factor_sources: list[str]
    gwp_values: str
    exclusions: list[str]
    assumptions: list[str]


class BaseYearComparison(BaseModel):
    """Comparison with base year emissions."""
    base_year: int
    base_year_emissions_tonnes: float
    current_emissions_tonnes: float
    absolute_change_tonnes: float
    percentage_change: float


class VerificationInfo(BaseModel):
    """Verification/assurance information."""
    status: str
    assurance_level: Optional[str]
    verified_by: Optional[str]
    verified_at: Optional[str]
    verification_statement: Optional[str]


class ISO14064Report(BaseModel):
    """
    Complete ISO 14064-1 compliant GHG Inventory Report.

    Sections align with ISO 14064-1:2018 requirements:
    1. Organization description
    2. Reporting boundaries
    3. GHG emissions by scope
    4. Methodology
    5. Base year comparison
    6. Verification statement
    """
    # Report metadata
    report_title: str
    report_date: str
    reporting_period: str

    # 1. Organization
    organization: OrganizationInfo

    # 2. Boundaries
    boundaries: ReportingBoundary

    # 3. Executive Summary
    executive_summary: dict

    # 4. Emissions by Scope (detailed)
    scope_1: ScopeDetail
    scope_2: ScopeDetail
    scope_3: ScopeDetail
    total_emissions_kg: float
    total_emissions_tonnes: float

    # 5. Data Quality
    overall_data_quality_score: float
    data_quality_interpretation: str

    # 6. Methodology
    methodology: MethodologySection

    # 7. Base Year Comparison (optional)
    base_year_comparison: Optional[BaseYearComparison]

    # 8. Verification
    verification: VerificationInfo


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


# ============================================================================
# ISO 14064-1 GHG Inventory Report
# ============================================================================

# Category names for display
CATEGORY_NAMES = {
    "1.1": "Stationary Combustion",
    "1.2": "Mobile Combustion",
    "1.3": "Fugitive Emissions",
    "2.1": "Purchased Electricity",
    "2.2": "Purchased Heat/Steam",
    "2.3": "Purchased Cooling",
    "3.1": "Purchased Goods & Services",
    "3.2": "Capital Goods",
    "3.3": "Fuel & Energy Related",
    "3.4": "Upstream Transportation",
    "3.5": "Waste Generated",
    "3.6": "Business Travel",
    "3.7": "Employee Commuting",
    "3.8": "Upstream Leased Assets",
    "3.9": "Downstream Transportation",
    "3.10": "Processing of Sold Products",
    "3.11": "Use of Sold Products",
    "3.12": "End-of-Life Treatment",
    "3.13": "Downstream Leased Assets",
    "3.14": "Franchises",
    "3.15": "Investments",
}

SCOPE_NAMES = {
    1: "Direct Emissions (Scope 1)",
    2: "Indirect Emissions from Energy (Scope 2)",
    3: "Other Indirect Emissions (Scope 3)",
}


@router.get("/periods/{period_id}/report/ghg-inventory", response_model=ISO14064Report)
async def get_ghg_inventory_report(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Generate ISO 14064-1 compliant GHG Inventory Report.

    Returns a comprehensive report including:
    - Organization information
    - Reporting boundaries
    - Emissions by scope with source details
    - Methodology description
    - Data quality assessment
    - Base year comparison (if available)
    - Verification status
    """
    # Get period and verify access
    period_query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    period_result = await session.execute(period_query)
    period = period_result.scalar_one_or_none()

    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")

    # Get organization
    org_query = select(Organization).where(Organization.id == current_user.organization_id)
    org_result = await session.execute(org_query)
    org = org_result.scalar_one_or_none()

    # Get facility count
    from app.models.core import Site
    site_query = select(func.count(Site.id)).where(
        Site.organization_id == current_user.organization_id,
        Site.is_active == True
    )
    site_result = await session.execute(site_query)
    facility_count = site_result.scalar() or 1

    # Get all activities with emissions for this period
    activities_query = (
        select(Activity, Emission, EmissionFactor)
        .join(Emission, Activity.id == Emission.activity_id)
        .join(EmissionFactor, Emission.emission_factor_id == EmissionFactor.id)
        .where(
            Activity.reporting_period_id == period_id,
            Activity.organization_id == current_user.organization_id,
        )
    )
    activities_result = await session.execute(activities_query)
    rows = activities_result.all()

    # Aggregate by scope and activity_key
    scope_data = {1: {}, 2: {}, 3: {}}
    scope_totals = {1: Decimal(0), 2: Decimal(0), 3: Decimal(0)}
    scope_counts = {1: 0, 2: 0, 3: 0}
    scope_quality_sums = {1: Decimal(0), 2: Decimal(0), 3: Decimal(0)}

    total_quality_weighted_sum = Decimal(0)
    total_co2e = Decimal(0)

    for activity, emission, factor in rows:
        scope = activity.scope
        key = activity.activity_key

        if key not in scope_data[scope]:
            scope_data[scope][key] = {
                "display_name": factor.display_name,
                "category_code": activity.category_code,
                "count": 0,
                "total_quantity": Decimal(0),
                "unit": activity.unit,
                "total_co2e_kg": Decimal(0),
                "emission_factor": factor.co2e_factor,
                "factor_source": factor.source,
                "factor_unit": factor.factor_unit,
                "quality_sum": Decimal(0),
            }

        scope_data[scope][key]["count"] += 1
        scope_data[scope][key]["total_quantity"] += activity.quantity
        scope_data[scope][key]["total_co2e_kg"] += emission.co2e_kg
        scope_data[scope][key]["quality_sum"] += Decimal(str(activity.data_quality_score or 5))

        scope_totals[scope] += emission.co2e_kg
        scope_counts[scope] += 1
        scope_quality_sums[scope] += Decimal(str(activity.data_quality_score or 5))

        total_co2e += emission.co2e_kg
        total_quality_weighted_sum += emission.co2e_kg * Decimal(str(activity.data_quality_score or 5))

    # Build scope details
    def build_scope_detail(scope: int) -> ScopeDetail:
        sources = []
        for key, data in scope_data[scope].items():
            avg_quality = float(data["quality_sum"] / data["count"]) if data["count"] > 0 else 5.0
            sources.append(EmissionSourceDetail(
                activity_key=key,
                display_name=data["display_name"],
                category_code=data["category_code"],
                activity_count=data["count"],
                total_quantity=float(data["total_quantity"]),
                unit=data["unit"],
                total_co2e_kg=float(data["total_co2e_kg"]),
                total_co2e_tonnes=float(data["total_co2e_kg"]) / 1000,
                emission_factor=float(data["emission_factor"]),
                factor_source=data["factor_source"],
                factor_unit=data["factor_unit"],
                avg_data_quality=round(avg_quality, 1),
            ))

        # Sort by emissions (highest first)
        sources.sort(key=lambda x: x.total_co2e_kg, reverse=True)

        scope_total = scope_totals[scope]
        pct = float(scope_total / total_co2e * 100) if total_co2e > 0 else 0
        avg_quality = float(scope_quality_sums[scope] / scope_counts[scope]) if scope_counts[scope] > 0 else 5.0

        return ScopeDetail(
            scope=scope,
            scope_name=SCOPE_NAMES[scope],
            total_co2e_kg=float(scope_total),
            total_co2e_tonnes=float(scope_total) / 1000,
            percentage_of_total=round(pct, 1),
            activity_count=scope_counts[scope],
            avg_data_quality=round(avg_quality, 1),
            sources=sources,
        )

    scope_1_detail = build_scope_detail(1)
    scope_2_detail = build_scope_detail(2)
    scope_3_detail = build_scope_detail(3)

    # Overall data quality
    overall_quality = float(total_quality_weighted_sum / total_co2e) if total_co2e > 0 else 5.0

    if overall_quality <= 1.5:
        quality_interpretation = "Excellent - Predominantly verified data"
    elif overall_quality <= 2.5:
        quality_interpretation = "Good - Mix of primary and modeled data"
    elif overall_quality <= 3.5:
        quality_interpretation = "Fair - Significant use of average factors"
    elif overall_quality <= 4.5:
        quality_interpretation = "Limited - Primarily economic estimates"
    else:
        quality_interpretation = "Low - Consider improving data sources"

    # Executive summary
    executive_summary = {
        "total_emissions_tonnes": round(float(total_co2e) / 1000, 2),
        "scope_1_tonnes": round(float(scope_totals[1]) / 1000, 2),
        "scope_2_tonnes": round(float(scope_totals[2]) / 1000, 2),
        "scope_3_tonnes": round(float(scope_totals[3]) / 1000, 2),
        "scope_1_percentage": scope_1_detail.percentage_of_total,
        "scope_2_percentage": scope_2_detail.percentage_of_total,
        "scope_3_percentage": scope_3_detail.percentage_of_total,
        "total_activities": scope_counts[1] + scope_counts[2] + scope_counts[3],
        "data_quality_score": round(overall_quality, 1),
        "top_emission_sources": [
            s.display_name for s in sorted(
                scope_1_detail.sources + scope_2_detail.sources + scope_3_detail.sources,
                key=lambda x: x.total_co2e_kg,
                reverse=True
            )[:5]
        ],
    }

    # Base year comparison (if org has base year and we have data)
    base_year_comparison = None
    if org and org.base_year and org.base_year < period.start_date.year:
        # This would query historical data - simplified for now
        base_year_comparison = BaseYearComparison(
            base_year=org.base_year,
            base_year_emissions_tonnes=0,  # Would need historical data
            current_emissions_tonnes=round(float(total_co2e) / 1000, 2),
            absolute_change_tonnes=0,
            percentage_change=0,
        )

    # Verification info
    verification = VerificationInfo(
        status=period.status.value if period.status else "draft",
        assurance_level=period.assurance_level.value if period.assurance_level else None,
        verified_by=period.verified_by,
        verified_at=period.verified_at.isoformat() if period.verified_at else None,
        verification_statement=period.verification_statement,
    )

    # Build methodology section
    factor_sources = set()
    for scope in [1, 2, 3]:
        for data in scope_data[scope].values():
            factor_sources.add(data["factor_source"])

    methodology = MethodologySection(
        calculation_approach="Activity-based calculations using GHG Protocol methodology",
        emission_factor_sources=list(factor_sources) or ["DEFRA 2024", "EPA eGRID"],
        gwp_values="IPCC AR6 100-year GWP values (CO2=1, CH4=27.9, N2O=273)",
        exclusions=["Biogenic emissions reported separately", "De minimis sources (<1% of total)"],
        assumptions=[
            "Operational control approach for organizational boundaries",
            "Location-based method for Scope 2 unless market-based data available",
            "Average emission factors used where supplier-specific data unavailable",
        ],
    )

    return ISO14064Report(
        report_title=f"GHG Inventory Report - {org.name if org else 'Organization'}",
        report_date=datetime.utcnow().strftime("%Y-%m-%d"),
        reporting_period=f"{period.start_date.strftime('%Y-%m-%d')} to {period.end_date.strftime('%Y-%m-%d')}",
        organization=OrganizationInfo(
            name=org.name if org else "Organization",
            country=org.country_code if org else None,
            industry=org.industry_code if org else None,
            base_year=org.base_year if org else None,
        ),
        boundaries=ReportingBoundary(
            consolidation_approach="operational_control",
            included_facilities=facility_count,
            reporting_period_start=period.start_date.strftime("%Y-%m-%d"),
            reporting_period_end=period.end_date.strftime("%Y-%m-%d"),
        ),
        executive_summary=executive_summary,
        scope_1=scope_1_detail,
        scope_2=scope_2_detail,
        scope_3=scope_3_detail,
        total_emissions_kg=float(total_co2e),
        total_emissions_tonnes=round(float(total_co2e) / 1000, 2),
        overall_data_quality_score=round(overall_quality, 1),
        data_quality_interpretation=quality_interpretation,
        methodology=methodology,
        base_year_comparison=base_year_comparison,
        verification=verification,
    )
