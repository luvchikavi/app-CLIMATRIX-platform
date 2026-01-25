"""
Reporting Periods API endpoints.

Includes verification workflow management:
- Status transitions: draft -> review -> submitted -> audit -> verified -> locked
- Role-based permissions for status changes
"""
from datetime import date, datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.auth import get_current_user
from app.database import get_session
from app.models.core import User, ReportingPeriod, PeriodStatus, AssuranceLevel, UserRole

router = APIRouter()


# Valid status transitions
VALID_TRANSITIONS = {
    PeriodStatus.DRAFT: [PeriodStatus.REVIEW],
    PeriodStatus.REVIEW: [PeriodStatus.DRAFT, PeriodStatus.SUBMITTED],
    PeriodStatus.SUBMITTED: [PeriodStatus.REVIEW, PeriodStatus.AUDIT],
    PeriodStatus.AUDIT: [PeriodStatus.SUBMITTED, PeriodStatus.VERIFIED],
    PeriodStatus.VERIFIED: [PeriodStatus.LOCKED],
    PeriodStatus.LOCKED: [],  # No transitions from locked
}


# ============================================================================
# Schemas
# ============================================================================

class ReportingPeriodCreate(BaseModel):
    """Create reporting period request."""
    name: str
    start_date: date
    end_date: date


class ReportingPeriodResponse(BaseModel):
    """Reporting period response with verification status."""
    id: str
    name: str
    start_date: date
    end_date: date
    is_locked: bool
    organization_id: str
    # Verification workflow fields
    status: str
    assurance_level: Optional[str] = None
    submitted_at: Optional[datetime] = None
    submitted_by_id: Optional[str] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    verification_statement: Optional[str] = None


class StatusTransitionRequest(BaseModel):
    """Request to transition period status."""
    new_status: str


class VerificationRequest(BaseModel):
    """Request to verify a period (admin/auditor only)."""
    assurance_level: str  # "limited" or "reasonable"
    verified_by: str  # Auditor name/firm
    verification_statement: str


# ============================================================================
# Helper Functions
# ============================================================================

def period_to_response(period: ReportingPeriod) -> ReportingPeriodResponse:
    """Convert ReportingPeriod model to response schema."""
    return ReportingPeriodResponse(
        id=str(period.id),
        name=period.name,
        start_date=period.start_date,
        end_date=period.end_date,
        is_locked=period.is_locked,
        organization_id=str(period.organization_id),
        status=period.status.value if period.status else "draft",
        assurance_level=period.assurance_level.value if period.assurance_level else None,
        submitted_at=period.submitted_at,
        submitted_by_id=str(period.submitted_by_id) if period.submitted_by_id else None,
        verified_at=period.verified_at,
        verified_by=period.verified_by,
        verification_statement=period.verification_statement,
    )


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

    return [period_to_response(p) for p in periods]


@router.post("", response_model=ReportingPeriodResponse)
async def create_period(
    data: ReportingPeriodCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new reporting period (starts in 'draft' status)."""
    period = ReportingPeriod(
        name=data.name,
        start_date=data.start_date,
        end_date=data.end_date,
        organization_id=current_user.organization_id,
        status=PeriodStatus.DRAFT,
    )
    session.add(period)
    await session.commit()
    await session.refresh(period)

    return period_to_response(period)


@router.get("/{period_id}", response_model=ReportingPeriodResponse)
async def get_period(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a specific reporting period with verification status."""
    query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    result = await session.execute(query)
    period = result.scalar_one_or_none()

    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")

    return period_to_response(period)


@router.delete("/{period_id}")
async def delete_period(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete a reporting period (only if in draft status)."""
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

    if period.status != PeriodStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete period in '{period.status.value}' status. Only draft periods can be deleted."
        )

    await session.delete(period)
    await session.commit()

    return {"status": "deleted", "id": str(period_id)}


# ============================================================================
# Verification Workflow Endpoints
# ============================================================================

@router.post("/{period_id}/transition", response_model=ReportingPeriodResponse)
async def transition_status(
    period_id: UUID,
    data: StatusTransitionRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Transition a reporting period to a new status.

    Valid transitions:
    - draft -> review (editor+)
    - review -> draft (editor+)
    - review -> submitted (editor+)
    - submitted -> review (admin only, to request changes)
    - submitted -> audit (admin only)
    - audit -> submitted (admin only, if issues found)
    - audit -> verified (admin only, after verification)
    - verified -> locked (admin only)
    """
    query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    result = await session.execute(query)
    period = result.scalar_one_or_none()

    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")

    # Parse new status
    try:
        new_status = PeriodStatus(data.new_status)
    except ValueError:
        valid_statuses = [s.value for s in PeriodStatus]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{data.new_status}'. Valid statuses: {valid_statuses}"
        )

    # Check if transition is valid
    current_status = period.status or PeriodStatus.DRAFT
    valid_next = VALID_TRANSITIONS.get(current_status, [])

    if new_status not in valid_next:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current_status.value}' to '{new_status.value}'. "
                   f"Valid transitions: {[s.value for s in valid_next]}"
        )

    # Check permissions for certain transitions
    admin_only_transitions = [
        (PeriodStatus.SUBMITTED, PeriodStatus.AUDIT),
        (PeriodStatus.AUDIT, PeriodStatus.VERIFIED),
        (PeriodStatus.VERIFIED, PeriodStatus.LOCKED),
    ]

    if (current_status, new_status) in admin_only_transitions:
        if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=403,
                detail="Only admins can perform this status transition"
            )

    # Perform the transition
    period.status = new_status

    # Track submission
    if new_status == PeriodStatus.SUBMITTED:
        period.submitted_at = datetime.utcnow()
        period.submitted_by_id = current_user.id

    # Lock the period if moving to locked status
    if new_status == PeriodStatus.LOCKED:
        period.is_locked = True

    session.add(period)
    await session.commit()
    await session.refresh(period)

    return period_to_response(period)


@router.post("/{period_id}/verify", response_model=ReportingPeriodResponse)
async def verify_period(
    period_id: UUID,
    data: VerificationRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Mark a reporting period as verified with assurance details.
    Admin only. Period must be in 'audit' status.
    """
    # Check admin permission
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can verify periods")

    query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    result = await session.execute(query)
    period = result.scalar_one_or_none()

    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")

    if period.status != PeriodStatus.AUDIT:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot verify period in '{period.status.value}' status. Must be in 'audit' status."
        )

    # Validate assurance level
    try:
        assurance = AssuranceLevel(data.assurance_level)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid assurance level. Must be 'limited' or 'reasonable'."
        )

    # Update verification details
    period.status = PeriodStatus.VERIFIED
    period.assurance_level = assurance
    period.verified_at = datetime.utcnow()
    period.verified_by = data.verified_by
    period.verification_statement = data.verification_statement

    session.add(period)
    await session.commit()
    await session.refresh(period)

    return period_to_response(period)


@router.post("/{period_id}/lock", response_model=ReportingPeriodResponse)
async def lock_period(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Lock a verified period to prevent further changes.
    Admin only. Period must be in 'verified' status.
    """
    # Check admin permission
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can lock periods")

    query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    result = await session.execute(query)
    period = result.scalar_one_or_none()

    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")

    if period.status != PeriodStatus.VERIFIED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot lock period in '{period.status.value}' status. Must be in 'verified' status."
        )

    period.status = PeriodStatus.LOCKED
    period.is_locked = True

    session.add(period)
    await session.commit()
    await session.refresh(period)

    return period_to_response(period)


@router.get("/{period_id}/status-history")
async def get_status_history(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get the status history/audit trail for a reporting period.
    Returns current status info and key timestamps.
    """
    query = select(ReportingPeriod).where(
        ReportingPeriod.id == period_id,
        ReportingPeriod.organization_id == current_user.organization_id,
    )
    result = await session.execute(query)
    period = result.scalar_one_or_none()

    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")

    return {
        "period_id": str(period.id),
        "current_status": period.status.value if period.status else "draft",
        "is_locked": period.is_locked,
        "timeline": {
            "created_at": period.created_at.isoformat() if period.created_at else None,
            "submitted_at": period.submitted_at.isoformat() if period.submitted_at else None,
            "submitted_by_id": str(period.submitted_by_id) if period.submitted_by_id else None,
            "verified_at": period.verified_at.isoformat() if period.verified_at else None,
            "verified_by": period.verified_by,
        },
        "verification": {
            "assurance_level": period.assurance_level.value if period.assurance_level else None,
            "verification_statement": period.verification_statement,
        },
        "valid_transitions": [s.value for s in VALID_TRANSITIONS.get(period.status or PeriodStatus.DRAFT, [])],
    }
