"""
Reports API endpoints.
Generates emission summaries and reports.

Includes ISO 14064-1 compliant GHG inventory reports and audit package exports.
"""
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
import io
import json

from app.api.auth import get_current_user
from app.database import get_session
from app.models.core import User, ReportingPeriod, Organization, PeriodStatus
from app.models.emission import Activity, Emission, EmissionFactor, ImportBatch
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
    # Use LEFT JOIN on EmissionFactor to include supplier-provided EF activities
    # (where emission_factor_id is NULL because the factor was user-provided, not from DB)
    query = (
        select(Activity, Emission, EmissionFactor)
        .join(Emission, Activity.id == Emission.activity_id)
        .outerjoin(EmissionFactor, Emission.emission_factor_id == EmissionFactor.id)
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
        # Get country code from activity_key or factor region (factor may be None for supplier-provided)
        factor_region = factor.region if factor else None
        country_code = _extract_country_code(activity.activity_key, factor_region)

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

        location_factor_val = grid_factor.get("location_factor", factor.co2e_factor if factor else Decimal("0.436"))
        market_factor_val = grid_factor.get("market_factor")

        # Calculate quantity in kWh (may already be in kWh)
        quantity_kwh = float(activity.quantity)

        # Calculate location-based emissions using grid average
        location_co2e = quantity_kwh * float(location_factor_val)

        # For market-based: if this activity was calculated with a supplier EF,
        # use the actual stored emission value as market-based
        is_supplier_provided = (emission.resolution_strategy == "market_based_supplier" or
                                emission.resolution_strategy == "supplier_provided")
        if is_supplier_provided:
            market_co2e = float(emission.co2e_kg)
        elif market_factor_val:
            market_co2e = quantity_kwh * float(market_factor_val)
        else:
            market_co2e = None

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
            location_factor=float(location_factor_val),
            market_factor=float(market_factor_val) if market_factor_val else (float(emission.co2e_kg) / quantity_kwh if is_supplier_provided and quantity_kwh > 0 else None),
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
        .outerjoin(EmissionFactor, Emission.emission_factor_id == EmissionFactor.id)
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
                "display_name": factor.display_name if factor else activity.activity_key,
                "category_code": activity.category_code,
                "count": 0,
                "total_quantity": Decimal(0),
                "unit": activity.unit,
                "total_co2e_kg": Decimal(0),
                "emission_factor": factor.co2e_factor if factor else None,
                "factor_source": factor.source if factor else "Supplier-Provided",
                "factor_unit": factor.factor_unit if factor else None,
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


# ============================================================================
# Audit Package Export (Phase 1.4)
# ============================================================================

class ActivityAuditRecord(BaseModel):
    """Detailed activity record for audit purposes."""
    activity_id: str
    scope: int
    category_code: str
    category_name: str
    activity_key: str
    display_name: str
    description: str

    # Quantity and measurement
    quantity: float
    unit: str
    activity_date: str

    # Calculation method
    calculation_method: str

    # Source tracking
    data_source: str  # manual, import, api
    import_batch_id: Optional[str]
    import_file_name: Optional[str]

    # Data quality (PCAF)
    data_quality_score: int
    data_quality_label: str
    data_quality_justification: Optional[str]
    supporting_document_url: Optional[str]

    # Calculated emission
    co2e_kg: float
    co2e_tonnes: float
    co2_kg: Optional[float]
    ch4_kg: Optional[float]
    n2o_kg: Optional[float]
    wtt_co2e_kg: Optional[float]

    # Calculation audit trail
    emission_factor_id: str
    emission_factor_value: float
    emission_factor_unit: str
    converted_quantity: Optional[float]
    converted_unit: Optional[str]
    calculation_formula: Optional[str]
    confidence_level: str

    # Timestamps
    created_at: str
    created_by: Optional[str]


class EmissionFactorAuditRecord(BaseModel):
    """Emission factor documentation for audit."""
    factor_id: str
    activity_key: str
    display_name: str

    # Classification
    scope: int
    category_code: str
    subcategory: Optional[str]

    # Factor values
    co2e_factor: float
    co2_factor: Optional[float]
    ch4_factor: Optional[float]
    n2o_factor: Optional[float]

    # Units
    activity_unit: str
    factor_unit: str

    # Source documentation
    source: str
    region: str
    year: int

    # Validity
    valid_from: Optional[str]
    valid_until: Optional[str]

    # Usage in this period
    usage_count: int
    total_co2e_kg: float


class ImportBatchAuditRecord(BaseModel):
    """Import batch record for audit trail."""
    batch_id: str
    file_name: str
    file_type: str
    file_size_bytes: Optional[int]

    # Processing results
    status: str
    total_rows: int
    successful_rows: int
    failed_rows: int
    skipped_rows: int
    error_message: Optional[str]

    # Timestamps
    uploaded_at: str
    uploaded_by: Optional[str]
    completed_at: Optional[str]


class CalculationMethodologySection(BaseModel):
    """Detailed calculation methodology documentation."""
    overview: str
    ghg_protocol_alignment: str
    calculation_approach: str

    # Scope-specific methodology
    scope_1_methodology: dict
    scope_2_methodology: dict
    scope_3_methodology: dict

    # Data processing
    unit_conversion_approach: str
    wtt_calculation_method: str

    # Quality assurance
    data_validation_rules: list[str]
    confidence_level_criteria: dict


class AuditPackageSummary(BaseModel):
    """Summary section of the audit package."""
    period_id: str
    period_name: str
    organization_name: str
    reporting_period_start: str
    reporting_period_end: str

    # Status
    verification_status: str
    assurance_level: Optional[str]

    # Totals
    total_activities: int
    total_emissions_kg: float
    total_emissions_tonnes: float

    # By scope
    scope_1_emissions_tonnes: float
    scope_2_emissions_tonnes: float
    scope_3_emissions_tonnes: float

    # Data quality
    overall_data_quality_score: float
    data_quality_interpretation: str

    # Import history
    total_import_batches: int

    # Generation metadata
    generated_at: str
    generated_by: str


class AuditPackageResponse(BaseModel):
    """
    Complete audit package for third-party verification.

    Contains all information needed for auditors to verify:
    1. Activity data with source references
    2. Emission factors used with documentation
    3. Calculation methodology
    4. Import/change history
    """
    # Package metadata
    package_version: str

    # Summary
    summary: AuditPackageSummary

    # Detailed methodology
    methodology: CalculationMethodologySection

    # Activity records (sorted by scope, then category)
    activities: list[ActivityAuditRecord]

    # Emission factors used
    emission_factors: list[EmissionFactorAuditRecord]

    # Import history (change log)
    import_batches: list[ImportBatchAuditRecord]


@router.get("/periods/{period_id}/report/audit-package", response_model=AuditPackageResponse)
async def get_audit_package(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Generate comprehensive audit package for third-party verification.

    Returns complete documentation including:
    - All activities with source references and data quality info
    - All emission factors used with their documentation
    - Detailed calculation methodology
    - Import batch history (change log)

    This endpoint is designed for auditors and verifiers who need
    complete transparency into the emissions calculation process.
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

    # Get organization
    org_query = select(Organization).where(Organization.id == current_user.organization_id)
    org_result = await session.execute(org_query)
    org = org_result.scalar_one_or_none()

    # Get all activities with emissions and factors
    activities_query = (
        select(Activity, Emission, EmissionFactor)
        .join(Emission, Activity.id == Emission.activity_id)
        .outerjoin(EmissionFactor, Emission.emission_factor_id == EmissionFactor.id)
        .where(
            Activity.reporting_period_id == period_id,
            Activity.organization_id == current_user.organization_id,
        )
        .order_by(Activity.scope, Activity.category_code, Activity.activity_date)
    )
    activities_result = await session.execute(activities_query)
    activity_rows = activities_result.all()

    # Get import batches for this period
    batches_query = (
        select(ImportBatch)
        .where(
            ImportBatch.reporting_period_id == period_id,
            ImportBatch.organization_id == current_user.organization_id,
        )
        .order_by(ImportBatch.uploaded_at.desc())
    )
    batches_result = await session.execute(batches_query)
    import_batches = batches_result.scalars().all()

    # Build activity records
    activity_records = []
    factor_usage = {}  # Track emission factor usage
    total_co2e = Decimal(0)
    scope_totals = {1: Decimal(0), 2: Decimal(0), 3: Decimal(0)}
    quality_weighted_sum = Decimal(0)

    # Data quality labels
    dq_labels = {
        1: "Verified Data",
        2: "Primary Data",
        3: "Activity Average",
        4: "Spend-Based",
        5: "Estimated",
    }

    for activity, emission, factor in activity_rows:
        # Find import batch info if applicable
        import_file_name = None
        if activity.import_batch_id:
            for batch in import_batches:
                if batch.id == activity.import_batch_id:
                    import_file_name = batch.file_name
                    break

        # Build activity record
        dq_score = activity.data_quality_score or 5
        activity_records.append(ActivityAuditRecord(
            activity_id=str(activity.id),
            scope=activity.scope,
            category_code=activity.category_code,
            category_name=CATEGORY_NAMES.get(activity.category_code, activity.category_code),
            activity_key=activity.activity_key,
            display_name=factor.display_name if factor else activity.activity_key,
            description=activity.description or "",
            quantity=float(activity.quantity),
            unit=activity.unit,
            activity_date=activity.activity_date.isoformat(),
            calculation_method=activity.calculation_method.value if activity.calculation_method else "activity",
            data_source=activity.data_source.value if activity.data_source else "manual",
            import_batch_id=str(activity.import_batch_id) if activity.import_batch_id else None,
            import_file_name=import_file_name,
            data_quality_score=dq_score,
            data_quality_label=dq_labels.get(dq_score, "Unknown"),
            data_quality_justification=activity.data_quality_justification,
            supporting_document_url=activity.supporting_document_url,
            co2e_kg=float(emission.co2e_kg),
            co2e_tonnes=float(emission.co2e_kg) / 1000,
            co2_kg=float(emission.co2_kg) if emission.co2_kg else None,
            ch4_kg=float(emission.ch4_kg) if emission.ch4_kg else None,
            n2o_kg=float(emission.n2o_kg) if emission.n2o_kg else None,
            wtt_co2e_kg=float(emission.wtt_co2e_kg) if emission.wtt_co2e_kg else None,
            emission_factor_id=str(emission.emission_factor_id) if emission.emission_factor_id else None,
            emission_factor_value=float(factor.co2e_factor) if factor else None,
            emission_factor_unit=factor.factor_unit if factor else None,
            converted_quantity=float(emission.converted_quantity) if emission.converted_quantity else None,
            converted_unit=emission.converted_unit,
            calculation_formula=emission.formula,
            confidence_level=emission.confidence.value if emission.confidence else "high",
            created_at=activity.created_at.isoformat() if activity.created_at else "",
            created_by=str(activity.created_by) if activity.created_by else None,
        ))

        # Track factor usage (skip if no factor - supplier-provided)
        if factor:
            factor_id = str(factor.id)
            if factor_id not in factor_usage:
                factor_usage[factor_id] = {
                    "factor": factor,
                    "count": 0,
                    "total_co2e_kg": Decimal(0),
                }
            factor_usage[factor_id]["count"] += 1
            factor_usage[factor_id]["total_co2e_kg"] += emission.co2e_kg

        # Track totals
        total_co2e += emission.co2e_kg
        scope_totals[activity.scope] += emission.co2e_kg
        quality_weighted_sum += emission.co2e_kg * Decimal(str(dq_score))

    # Build emission factor records
    factor_records = []
    for factor_id, usage in factor_usage.items():
        factor = usage["factor"]
        factor_records.append(EmissionFactorAuditRecord(
            factor_id=factor_id,
            activity_key=factor.activity_key,
            display_name=factor.display_name,
            scope=factor.scope,
            category_code=factor.category_code,
            subcategory=factor.subcategory,
            co2e_factor=float(factor.co2e_factor),
            co2_factor=float(factor.co2_factor) if factor.co2_factor else None,
            ch4_factor=float(factor.ch4_factor) if factor.ch4_factor else None,
            n2o_factor=float(factor.n2o_factor) if factor.n2o_factor else None,
            activity_unit=factor.activity_unit,
            factor_unit=factor.factor_unit,
            source=factor.source,
            region=factor.region,
            year=factor.year,
            valid_from=factor.valid_from.isoformat() if factor.valid_from else None,
            valid_until=factor.valid_until.isoformat() if factor.valid_until else None,
            usage_count=usage["count"],
            total_co2e_kg=float(usage["total_co2e_kg"]),
        ))

    # Sort factors by total emissions (highest first)
    factor_records.sort(key=lambda x: x.total_co2e_kg, reverse=True)

    # Build import batch records
    batch_records = []
    for batch in import_batches:
        batch_records.append(ImportBatchAuditRecord(
            batch_id=str(batch.id),
            file_name=batch.file_name,
            file_type=batch.file_type,
            file_size_bytes=batch.file_size_bytes,
            status=batch.status.value if batch.status else "unknown",
            total_rows=batch.total_rows,
            successful_rows=batch.successful_rows,
            failed_rows=batch.failed_rows,
            skipped_rows=batch.skipped_rows,
            error_message=batch.error_message,
            uploaded_at=batch.uploaded_at.isoformat() if batch.uploaded_at else "",
            uploaded_by=str(batch.uploaded_by) if batch.uploaded_by else None,
            completed_at=batch.completed_at.isoformat() if batch.completed_at else None,
        ))

    # Calculate overall data quality
    overall_quality = float(quality_weighted_sum / total_co2e) if total_co2e > 0 else 5.0
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

    # Build methodology section
    methodology = CalculationMethodologySection(
        overview=(
            "Emissions are calculated using activity-based methodology following "
            "the GHG Protocol Corporate Standard. Activity data is multiplied by "
            "appropriate emission factors to calculate CO2-equivalent emissions."
        ),
        ghg_protocol_alignment=(
            "This inventory follows the GHG Protocol Corporate Accounting and Reporting "
            "Standard (Revised Edition), including the Scope 2 Guidance and Corporate "
            "Value Chain (Scope 3) Standard."
        ),
        calculation_approach=(
            "Activity-based approach: CO2e = Activity Data × Emission Factor. "
            "Emission factors are sourced from recognized databases including DEFRA, "
            "EPA, and IPCC. All factors use AR6 GWP values unless otherwise noted."
        ),
        scope_1_methodology={
            "description": "Direct GHG emissions from sources owned or controlled by the organization",
            "categories": {
                "1.1": "Stationary Combustion - Fuel combustion in stationary equipment",
                "1.2": "Mobile Combustion - Fuel combustion in company vehicles",
                "1.3": "Fugitive Emissions - Refrigerant leaks and other fugitive sources",
            },
            "calculation": "Physical quantity (liters, m³, kg) × Emission factor (kg CO2e/unit)",
        },
        scope_2_methodology={
            "description": "Indirect GHG emissions from purchased electricity, steam, heat, or cooling",
            "approach": "Location-based method using grid average factors; market-based available where data exists",
            "categories": {
                "2.1": "Purchased Electricity",
                "2.2": "Purchased Heat/Steam",
                "2.3": "Purchased Cooling",
            },
            "calculation": "Energy consumption (kWh) × Grid emission factor (kg CO2e/kWh)",
        },
        scope_3_methodology={
            "description": "Other indirect emissions in the value chain",
            "categories_covered": list(set(a.category_code for a in activity_records if a.scope == 3)),
            "calculation": "Various methods including activity-based, spend-based, and distance-based",
            "wtt_note": "Category 3.3 includes Well-to-Tank emissions auto-calculated from Scope 1 & 2 activities",
        },
        unit_conversion_approach=(
            "Unit conversions are performed using standardized conversion factors. "
            "All quantities are converted to factor-expected units before calculation."
        ),
        wtt_calculation_method=(
            "Well-to-Tank (WTT) emissions for Scope 1 & 2 fuels are automatically calculated "
            "and reported under Category 3.3 (Fuel and Energy Related Activities). WTT factors "
            "represent upstream emissions from fuel extraction, refining, and transportation."
        ),
        data_validation_rules=[
            "Quantity must be positive",
            "Activity date must fall within reporting period",
            "Activity key must match registered emission factor",
            "Unit must be compatible with emission factor requirements",
            "Data quality score must be between 1-5 (PCAF methodology)",
        ],
        confidence_level_criteria={
            "high": "Exact emission factor match for activity type and region",
            "medium": "Regional or similar factor used when exact match unavailable",
            "low": "Global average or proxy factor used",
        },
    )

    # Build summary
    summary = AuditPackageSummary(
        period_id=str(period_id),
        period_name=period.name,
        organization_name=org.name if org else "Organization",
        reporting_period_start=period.start_date.isoformat(),
        reporting_period_end=period.end_date.isoformat(),
        verification_status=period.status.value if period.status else "draft",
        assurance_level=period.assurance_level.value if period.assurance_level else None,
        total_activities=len(activity_records),
        total_emissions_kg=float(total_co2e),
        total_emissions_tonnes=round(float(total_co2e) / 1000, 2),
        scope_1_emissions_tonnes=round(float(scope_totals[1]) / 1000, 2),
        scope_2_emissions_tonnes=round(float(scope_totals[2]) / 1000, 2),
        scope_3_emissions_tonnes=round(float(scope_totals[3]) / 1000, 2),
        overall_data_quality_score=round(overall_quality, 2),
        data_quality_interpretation=quality_interpretation,
        total_import_batches=len(batch_records),
        generated_at=datetime.utcnow().isoformat(),
        generated_by=current_user.email,
    )

    return AuditPackageResponse(
        package_version="1.0",
        summary=summary,
        methodology=methodology,
        activities=activity_records,
        emission_factors=factor_records,
        import_batches=batch_records,
    )


# ============================================================================
# CDP Climate Change Questionnaire Export (Phase 1.5)
# ============================================================================

class CDPScope1Breakdown(BaseModel):
    """CDP C6.1 - Scope 1 emissions by source."""
    source_category: str  # Stationary combustion, Mobile combustion, etc.
    emissions_metric_tonnes: float
    methodology: str
    source_of_emission_factors: str


class CDPScope2Breakdown(BaseModel):
    """CDP C6.3 - Scope 2 emissions by location."""
    country: str
    grid_region: Optional[str]
    purchased_electricity_mwh: float
    location_based_emissions_tonnes: float
    market_based_emissions_tonnes: Optional[float]


class CDPScope3Category(BaseModel):
    """CDP C6.5 - Scope 3 emissions by category."""
    category_number: int  # 1-15
    category_name: str
    emissions_metric_tonnes: float
    calculation_methodology: str
    percentage_calculated_using_primary_data: float
    explanation: str


class CDPEmissionsTotals(BaseModel):
    """CDP C6.1/C6.3/C6.5 - Total emissions summary."""
    scope_1_metric_tonnes: float
    scope_2_location_based_metric_tonnes: float
    scope_2_market_based_metric_tonnes: Optional[float]
    scope_3_metric_tonnes: float
    total_metric_tonnes: float


class CDPTargetsAndPerformance(BaseModel):
    """CDP C4 - Targets and performance."""
    base_year: Optional[int]
    base_year_emissions_tonnes: Optional[float]
    target_year: Optional[int]
    target_reduction_percentage: Optional[float]
    current_year_emissions_tonnes: float
    progress_percentage: Optional[float]


class CDPDataQuality(BaseModel):
    """CDP data quality metrics."""
    overall_data_quality_score: float
    percentage_verified_data: float
    percentage_primary_data: float
    percentage_estimated_data: float
    verification_status: str
    assurance_level: Optional[str]


class CDPExportResponse(BaseModel):
    """
    CDP Climate Change Questionnaire Export Format.

    Aligned with CDP Climate Change 2024 questionnaire structure.
    Key sections covered:
    - C0: Introduction (organization info)
    - C4: Targets and performance
    - C6: Emissions data
    - C7: Emissions breakdown
    """
    # Metadata
    export_version: str
    export_date: str
    reporting_year: int

    # C0: Introduction
    organization_name: str
    country: Optional[str]
    primary_industry: Optional[str]
    reporting_boundary: str

    # C4: Targets
    targets: CDPTargetsAndPerformance

    # C6: Emissions totals
    emissions_totals: CDPEmissionsTotals

    # C6.1: Scope 1 breakdown
    scope_1_breakdown: list[CDPScope1Breakdown]

    # C6.3: Scope 2 breakdown
    scope_2_breakdown: list[CDPScope2Breakdown]

    # C6.5: Scope 3 categories
    scope_3_categories: list[CDPScope3Category]

    # Data quality
    data_quality: CDPDataQuality

    # Methodology
    emission_factor_sources: list[str]
    global_warming_potential_source: str


# CDP Scope 3 category names (GHG Protocol)
CDP_SCOPE3_CATEGORIES = {
    1: "Purchased goods and services",
    2: "Capital goods",
    3: "Fuel-and-energy-related activities (not included in Scope 1 or 2)",
    4: "Upstream transportation and distribution",
    5: "Waste generated in operations",
    6: "Business travel",
    7: "Employee commuting",
    8: "Upstream leased assets",
    9: "Downstream transportation and distribution",
    10: "Processing of sold products",
    11: "Use of sold products",
    12: "End of life treatment of sold products",
    13: "Downstream leased assets",
    14: "Franchises",
    15: "Investments",
}

# Map our category codes to CDP category numbers
CATEGORY_TO_CDP = {
    "3.1": 1,
    "3.2": 2,
    "3.3": 3,
    "3.4": 4,
    "3.5": 5,
    "3.6": 6,
    "3.7": 7,
    "3.8": 8,
    "3.9": 9,
    "3.10": 10,
    "3.11": 11,
    "3.12": 12,
    "3.13": 13,
    "3.14": 14,
    "3.15": 15,
}

# Map our Scope 1 categories to CDP source categories
SCOPE1_CDP_SOURCES = {
    "1.1": "Stationary combustion",
    "1.2": "Mobile combustion",
    "1.3": "Fugitive emissions",
}


@router.get("/periods/{period_id}/export/cdp", response_model=CDPExportResponse)
async def export_cdp_format(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Export emissions data in CDP Climate Change questionnaire format.

    Aligned with CDP Climate Change 2024 questionnaire.
    Returns data structured for easy transfer to CDP online platform.
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

    # Get organization
    org_query = select(Organization).where(Organization.id == current_user.organization_id)
    org_result = await session.execute(org_query)
    org = org_result.scalar_one_or_none()

    # Get all activities with emissions
    activities_query = (
        select(Activity, Emission, EmissionFactor)
        .join(Emission, Activity.id == Emission.activity_id)
        .outerjoin(EmissionFactor, Emission.emission_factor_id == EmissionFactor.id)
        .where(
            Activity.reporting_period_id == period_id,
            Activity.organization_id == current_user.organization_id,
        )
    )
    activities_result = await session.execute(activities_query)
    rows = activities_result.all()

    # Aggregate data
    scope_totals = {1: Decimal(0), 2: Decimal(0), 3: Decimal(0)}
    scope1_by_category = {}
    scope2_by_country = {}
    scope3_by_category = {}

    factor_sources = set()
    quality_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    total_activities = 0

    for activity, emission, factor in rows:
        total_activities += 1
        scope_totals[activity.scope] += emission.co2e_kg
        if factor:
            factor_sources.add(factor.source)
        else:
            factor_sources.add("Supplier-Provided")
        quality_counts[activity.data_quality_score or 5] += 1

        if activity.scope == 1:
            cat = activity.category_code
            if cat not in scope1_by_category:
                scope1_by_category[cat] = {
                    "emissions": Decimal(0),
                    "sources": set(),
                }
            scope1_by_category[cat]["emissions"] += emission.co2e_kg
            scope1_by_category[cat]["sources"].add(factor.source if factor else "Supplier-Provided")

        elif activity.scope == 2:
            country = (factor.region if factor else None) or "Global"
            if country not in scope2_by_country:
                scope2_by_country[country] = {
                    "quantity_kwh": Decimal(0),
                    "location_emissions": Decimal(0),
                    "market_emissions": Decimal(0),
                }
            scope2_by_country[country]["quantity_kwh"] += activity.quantity
            scope2_by_country[country]["location_emissions"] += emission.co2e_kg

        elif activity.scope == 3:
            cat = activity.category_code
            if cat not in scope3_by_category:
                scope3_by_category[cat] = {
                    "emissions": Decimal(0),
                    "count": 0,
                    "primary_count": 0,
                }
            scope3_by_category[cat]["emissions"] += emission.co2e_kg
            scope3_by_category[cat]["count"] += 1
            if (activity.data_quality_score or 5) <= 2:
                scope3_by_category[cat]["primary_count"] += 1

    # Build Scope 1 breakdown
    scope1_breakdown = []
    for cat, data in sorted(scope1_by_category.items()):
        scope1_breakdown.append(CDPScope1Breakdown(
            source_category=SCOPE1_CDP_SOURCES.get(cat, cat),
            emissions_metric_tonnes=round(float(data["emissions"]) / 1000, 2),
            methodology="Activity data × emission factor",
            source_of_emission_factors=", ".join(data["sources"]),
        ))

    # Build Scope 2 breakdown
    scope2_breakdown = []
    for country, data in sorted(scope2_by_country.items()):
        scope2_breakdown.append(CDPScope2Breakdown(
            country=country,
            grid_region=None,
            purchased_electricity_mwh=round(float(data["quantity_kwh"]) / 1000, 2),
            location_based_emissions_tonnes=round(float(data["location_emissions"]) / 1000, 2),
            market_based_emissions_tonnes=None,  # Would need market-based calculation
        ))

    # Build Scope 3 categories
    scope3_categories = []
    for cat, data in sorted(scope3_by_category.items()):
        cdp_num = CATEGORY_TO_CDP.get(cat, int(cat.split(".")[1]) if "." in cat else 0)
        primary_pct = (data["primary_count"] / data["count"] * 100) if data["count"] > 0 else 0
        scope3_categories.append(CDPScope3Category(
            category_number=cdp_num,
            category_name=CDP_SCOPE3_CATEGORIES.get(cdp_num, f"Category {cdp_num}"),
            emissions_metric_tonnes=round(float(data["emissions"]) / 1000, 2),
            calculation_methodology="Activity-based calculation",
            percentage_calculated_using_primary_data=round(primary_pct, 1),
            explanation=f"Calculated from {data['count']} activities",
        ))

    # Calculate data quality metrics
    verified_pct = (quality_counts[1] / total_activities * 100) if total_activities > 0 else 0
    primary_pct = ((quality_counts[1] + quality_counts[2]) / total_activities * 100) if total_activities > 0 else 0
    estimated_pct = ((quality_counts[4] + quality_counts[5]) / total_activities * 100) if total_activities > 0 else 0

    # Calculate overall weighted quality score
    total_co2e = sum(scope_totals.values())

    data_quality = CDPDataQuality(
        overall_data_quality_score=3.0,  # Would need weighted calculation
        percentage_verified_data=round(verified_pct, 1),
        percentage_primary_data=round(primary_pct, 1),
        percentage_estimated_data=round(estimated_pct, 1),
        verification_status=period.status.value if period.status else "draft",
        assurance_level=period.assurance_level.value if period.assurance_level else None,
    )

    # Targets (basic structure - would need org target data)
    targets = CDPTargetsAndPerformance(
        base_year=org.base_year if org else None,
        base_year_emissions_tonnes=None,
        target_year=None,
        target_reduction_percentage=None,
        current_year_emissions_tonnes=round(float(total_co2e) / 1000, 2),
        progress_percentage=None,
    )

    return CDPExportResponse(
        export_version="CDP-2024-v1",
        export_date=datetime.utcnow().strftime("%Y-%m-%d"),
        reporting_year=period.start_date.year,
        organization_name=org.name if org else "Organization",
        country=org.country_code if org else None,
        primary_industry=org.industry_code if org else None,
        reporting_boundary="Operational control",
        targets=targets,
        emissions_totals=CDPEmissionsTotals(
            scope_1_metric_tonnes=round(float(scope_totals[1]) / 1000, 2),
            scope_2_location_based_metric_tonnes=round(float(scope_totals[2]) / 1000, 2),
            scope_2_market_based_metric_tonnes=None,
            scope_3_metric_tonnes=round(float(scope_totals[3]) / 1000, 2),
            total_metric_tonnes=round(float(total_co2e) / 1000, 2),
        ),
        scope_1_breakdown=scope1_breakdown,
        scope_2_breakdown=scope2_breakdown,
        scope_3_categories=scope3_categories,
        data_quality=data_quality,
        emission_factor_sources=list(factor_sources),
        global_warming_potential_source="IPCC AR6 (2021) - 100-year GWP values",
    )


# ============================================================================
# ESRS E1 Climate Export (Phase 1.5)
# ============================================================================

class ESRSE1GrossEmissions(BaseModel):
    """ESRS E1-6: Gross Scope 1, 2, 3 emissions."""
    scope_1_tonnes: float
    scope_2_location_based_tonnes: float
    scope_2_market_based_tonnes: Optional[float]
    scope_3_tonnes: float
    total_ghg_emissions_tonnes: float


class ESRSE1Scope3Detail(BaseModel):
    """ESRS E1-6: Scope 3 emissions by category."""
    category: str
    emissions_tonnes: float
    percentage_of_scope_3: float


class ESRSE1IntensityMetric(BaseModel):
    """ESRS E1-6: GHG intensity metrics."""
    metric_name: str
    numerator_tonnes: float
    denominator_value: float
    denominator_unit: str
    intensity_value: float
    intensity_unit: str


class ESRSE1TargetInfo(BaseModel):
    """ESRS E1-4: Climate targets."""
    target_type: str  # "absolute" or "intensity"
    target_scope: str  # "Scope 1", "Scope 1+2", "All scopes"
    base_year: int
    base_year_value: float
    target_year: int
    target_value: float
    target_reduction_percentage: float


class ESRSE1TransitionPlan(BaseModel):
    """ESRS E1-1: Transition plan summary."""
    has_transition_plan: bool
    plan_aligned_with: Optional[str]  # "Paris Agreement", "1.5°C pathway", etc.
    key_decarbonization_levers: list[str]
    locked_in_emissions_tonnes: Optional[float]


class ESRSE1DataQuality(BaseModel):
    """Data quality disclosure for ESRS."""
    data_quality_approach: str
    percentage_estimated_scope_3: float
    significant_assumptions: list[str]
    verification_statement: Optional[str]


class ESRSE1ExportResponse(BaseModel):
    """
    ESRS E1 Climate Change Disclosure Export.

    Aligned with European Sustainability Reporting Standards (ESRS) E1.
    Covers disclosure requirements for:
    - E1-1: Transition plan
    - E1-4: Targets
    - E1-5: Energy consumption
    - E1-6: Gross GHG emissions
    - E1-7: GHG removals and carbon credits
    - E1-9: Anticipated financial effects
    """
    # Metadata
    export_version: str
    export_date: str
    reporting_period_start: str
    reporting_period_end: str

    # Organization
    undertaking_name: str
    country_of_domicile: Optional[str]
    nace_sector: Optional[str]
    consolidation_scope: str

    # E1-1: Transition plan (simplified)
    transition_plan: ESRSE1TransitionPlan

    # E1-4: Targets
    climate_targets: list[ESRSE1TargetInfo]

    # E1-6: Gross GHG emissions
    gross_emissions: ESRSE1GrossEmissions
    scope_3_breakdown: list[ESRSE1Scope3Detail]

    # E1-6: GHG intensity
    intensity_metrics: list[ESRSE1IntensityMetric]

    # Data quality
    data_quality: ESRSE1DataQuality

    # Methodology
    ghg_accounting_standard: str
    emission_factor_sources: list[str]
    gwp_values_source: str


@router.get("/periods/{period_id}/export/esrs-e1", response_model=ESRSE1ExportResponse)
async def export_esrs_e1_format(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Export emissions data in ESRS E1 (Climate Change) format.

    Aligned with European Sustainability Reporting Standards.
    For CSRD compliance and EU sustainability reporting.
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

    # Get organization
    org_query = select(Organization).where(Organization.id == current_user.organization_id)
    org_result = await session.execute(org_query)
    org = org_result.scalar_one_or_none()

    # Get all activities with emissions
    activities_query = (
        select(Activity, Emission, EmissionFactor)
        .join(Emission, Activity.id == Emission.activity_id)
        .outerjoin(EmissionFactor, Emission.emission_factor_id == EmissionFactor.id)
        .where(
            Activity.reporting_period_id == period_id,
            Activity.organization_id == current_user.organization_id,
        )
    )
    activities_result = await session.execute(activities_query)
    rows = activities_result.all()

    # Aggregate emissions
    scope_totals = {1: Decimal(0), 2: Decimal(0), 3: Decimal(0)}
    scope3_by_category = {}
    factor_sources = set()
    estimated_count = 0
    total_count = 0

    for activity, emission, factor in rows:
        total_count += 1
        scope_totals[activity.scope] += emission.co2e_kg
        if factor:
            factor_sources.add(factor.source)
        else:
            factor_sources.add("Supplier-Provided")

        if (activity.data_quality_score or 5) >= 4:
            estimated_count += 1

        if activity.scope == 3:
            cat = activity.category_code
            cdp_num = CATEGORY_TO_CDP.get(cat, int(cat.split(".")[1]) if "." in cat else 0)
            cat_name = CDP_SCOPE3_CATEGORIES.get(cdp_num, f"Category {cdp_num}")

            if cat_name not in scope3_by_category:
                scope3_by_category[cat_name] = Decimal(0)
            scope3_by_category[cat_name] += emission.co2e_kg

    total_co2e = sum(scope_totals.values())
    scope3_total = scope_totals[3]

    # Build Scope 3 breakdown
    scope3_breakdown = []
    for cat_name, emissions in sorted(scope3_by_category.items(), key=lambda x: x[1], reverse=True):
        pct = float(emissions / scope3_total * 100) if scope3_total > 0 else 0
        scope3_breakdown.append(ESRSE1Scope3Detail(
            category=cat_name,
            emissions_tonnes=round(float(emissions) / 1000, 2),
            percentage_of_scope_3=round(pct, 1),
        ))

    # Gross emissions
    gross_emissions = ESRSE1GrossEmissions(
        scope_1_tonnes=round(float(scope_totals[1]) / 1000, 2),
        scope_2_location_based_tonnes=round(float(scope_totals[2]) / 1000, 2),
        scope_2_market_based_tonnes=None,
        scope_3_tonnes=round(float(scope_totals[3]) / 1000, 2),
        total_ghg_emissions_tonnes=round(float(total_co2e) / 1000, 2),
    )

    # Transition plan (placeholder - would need actual plan data)
    transition_plan = ESRSE1TransitionPlan(
        has_transition_plan=False,
        plan_aligned_with=None,
        key_decarbonization_levers=[],
        locked_in_emissions_tonnes=None,
    )

    # Climate targets (placeholder - would need actual target data)
    climate_targets = []
    if org and org.base_year:
        climate_targets.append(ESRSE1TargetInfo(
            target_type="absolute",
            target_scope="All scopes",
            base_year=org.base_year,
            base_year_value=0,  # Would need historical data
            target_year=2030,  # Placeholder
            target_value=0,
            target_reduction_percentage=0,
        ))

    # Intensity metrics (placeholder)
    intensity_metrics = [
        ESRSE1IntensityMetric(
            metric_name="Total GHG intensity per activity",
            numerator_tonnes=round(float(total_co2e) / 1000, 2),
            denominator_value=float(total_count) if total_count > 0 else 1,
            denominator_unit="activities",
            intensity_value=round(float(total_co2e) / 1000 / max(total_count, 1), 4),
            intensity_unit="tCO2e/activity",
        ),
    ]

    # Data quality
    estimated_pct = (estimated_count / total_count * 100) if total_count > 0 else 0
    data_quality = ESRSE1DataQuality(
        data_quality_approach="PCAF data quality scoring (1-5 scale)",
        percentage_estimated_scope_3=round(estimated_pct, 1),
        significant_assumptions=[
            "Emission factors from recognized databases (DEFRA, EPA, IPCC)",
            "GWP values from IPCC AR6 (100-year horizon)",
            "Operational control approach for organizational boundaries",
        ],
        verification_statement=period.verification_statement if period.verification_statement else None,
    )

    return ESRSE1ExportResponse(
        export_version="ESRS-E1-2024-v1",
        export_date=datetime.utcnow().strftime("%Y-%m-%d"),
        reporting_period_start=period.start_date.isoformat(),
        reporting_period_end=period.end_date.isoformat(),
        undertaking_name=org.name if org else "Organization",
        country_of_domicile=org.country_code if org else None,
        nace_sector=org.industry_code if org else None,
        consolidation_scope="Operational control",
        transition_plan=transition_plan,
        climate_targets=climate_targets,
        gross_emissions=gross_emissions,
        scope_3_breakdown=scope3_breakdown,
        intensity_metrics=intensity_metrics,
        data_quality=data_quality,
        ghg_accounting_standard="GHG Protocol Corporate Standard",
        emission_factor_sources=list(factor_sources),
        gwp_values_source="IPCC AR6 (2021) - 100-year GWP values",
    )
