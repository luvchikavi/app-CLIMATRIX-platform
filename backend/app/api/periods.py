"""
Reporting Periods API endpoints.
"""
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.auth import get_current_user
from app.database import get_session
from app.models.core import User, ReportingPeriod

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class ReportingPeriodCreate(BaseModel):
    """Create reporting period request."""
    name: str
    start_date: date
    end_date: date


class ReportingPeriodResponse(BaseModel):
    """Reporting period response."""
    id: str
    name: str
    start_date: date
    end_date: date
    is_locked: bool
    organization_id: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=list[ReportingPeriodResponse])
async def list_periods(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all reporting periods for the organization."""
    query = (
        select(ReportingPeriod)
        .where(ReportingPeriod.organization_id == current_user.organization_id)
        .order_by(ReportingPeriod.start_date.desc())
    )
    result = await session.execute(query)
    periods = result.scalars().all()

    return [
        ReportingPeriodResponse(
            id=str(p.id),
            name=p.name,
            start_date=p.start_date,
            end_date=p.end_date,
            is_locked=p.is_locked,
            organization_id=str(p.organization_id),
        )
        for p in periods
    ]


@router.post("", response_model=ReportingPeriodResponse)
async def create_period(
    data: ReportingPeriodCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new reporting period."""
    period = ReportingPeriod(
        name=data.name,
        start_date=data.start_date,
        end_date=data.end_date,
        organization_id=current_user.organization_id,
    )
    session.add(period)
    await session.commit()
    await session.refresh(period)

    return ReportingPeriodResponse(
        id=str(period.id),
        name=period.name,
        start_date=period.start_date,
        end_date=period.end_date,
        is_locked=period.is_locked,
        organization_id=str(period.organization_id),
    )


@router.get("/{period_id}", response_model=ReportingPeriodResponse)
async def get_period(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a specific reporting period."""
    query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    result = await session.execute(query)
    period = result.scalar_one_or_none()

    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")

    return ReportingPeriodResponse(
        id=str(period.id),
        name=period.name,
        start_date=period.start_date,
        end_date=period.end_date,
        is_locked=period.is_locked,
        organization_id=str(period.organization_id),
    )


@router.delete("/{period_id}")
async def delete_period(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete a reporting period (if not locked)."""
    query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    result = await session.execute(query)
    period = result.scalar_one_or_none()

    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")

    if period.is_locked:
        raise HTTPException(status_code=400, detail="Cannot delete locked reporting period")

    await session.delete(period)
    await session.commit()

    return {"status": "deleted", "id": str(period_id)}
