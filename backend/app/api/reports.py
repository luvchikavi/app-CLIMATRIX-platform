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
from app.models.emission import Activity, Emission
from app.services.calculation.wtt import WTTService

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
