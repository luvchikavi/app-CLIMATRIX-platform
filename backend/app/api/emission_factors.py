"""
Emission Factor Management API

Governance endpoints for viewing, creating, editing, and approving emission factors.
Only SUPER_ADMIN and ADMIN can approve/reject factors.
EDITOR can create drafts and submit for approval.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.database import get_session
from app.models.core import User, UserRole
from app.models.emission import EmissionFactor, EmissionFactorStatus
from app.api.auth import get_current_user

router = APIRouter(prefix="/emission-factors", tags=["Emission Factors"])


# =============================================================================
# SCHEMAS
# =============================================================================

class EmissionFactorCreate(BaseModel):
    """Schema for creating a new emission factor."""
    scope: int = Field(ge=1, le=3)
    category_code: str = Field(max_length=10)
    subcategory: Optional[str] = None
    activity_key: str = Field(max_length=100)
    display_name: str = Field(max_length=255)
    co2_factor: Optional[Decimal] = None
    ch4_factor: Optional[Decimal] = None
    n2o_factor: Optional[Decimal] = None
    co2e_factor: Decimal
    activity_unit: str = Field(max_length=50)
    factor_unit: str = Field(max_length=50)
    source: str = Field(max_length=100)
    region: str = Field(default="Global", max_length=50)
    year: int
    notes: Optional[str] = None
    change_reason: Optional[str] = None


class EmissionFactorUpdate(BaseModel):
    """Schema for updating an emission factor."""
    display_name: Optional[str] = None
    co2_factor: Optional[Decimal] = None
    ch4_factor: Optional[Decimal] = None
    n2o_factor: Optional[Decimal] = None
    co2e_factor: Optional[Decimal] = None
    activity_unit: Optional[str] = None
    factor_unit: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    change_reason: str = Field(..., max_length=500)  # Required for updates


class EmissionFactorResponse(BaseModel):
    """Schema for emission factor response."""
    id: UUID
    scope: int
    category_code: str
    subcategory: Optional[str]
    activity_key: str
    display_name: str
    co2_factor: Optional[Decimal]
    ch4_factor: Optional[Decimal]
    n2o_factor: Optional[Decimal]
    co2e_factor: Decimal
    activity_unit: str
    factor_unit: str
    source: str
    region: str
    year: int
    notes: Optional[str]
    is_active: bool
    status: EmissionFactorStatus
    version: int
    change_reason: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]

    class Config:
        from_attributes = True


class EmissionFactorListResponse(BaseModel):
    """Paginated list of emission factors."""
    items: List[EmissionFactorResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ApprovalAction(BaseModel):
    """Schema for approval/rejection."""
    reason: Optional[str] = Field(None, max_length=500)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("", response_model=EmissionFactorListResponse)
async def list_emission_factors(
    scope: Optional[int] = Query(None, ge=1, le=3),
    category_code: Optional[str] = None,
    status: Optional[EmissionFactorStatus] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    List all emission factors with filtering and pagination.

    - Supports filtering by scope, category, status
    - Search by activity_key or display_name
    - Paginated results
    """
    query = select(EmissionFactor)

    # Apply filters
    if scope:
        query = query.where(EmissionFactor.scope == scope)
    if category_code:
        query = query.where(EmissionFactor.category_code == category_code)
    if status:
        query = query.where(EmissionFactor.status == status)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (EmissionFactor.activity_key.ilike(search_pattern)) |
            (EmissionFactor.display_name.ilike(search_pattern))
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(EmissionFactor.scope, EmissionFactor.category_code, EmissionFactor.activity_key)
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    factors = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return EmissionFactorListResponse(
        items=[EmissionFactorResponse.model_validate(f) for f in factors],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/pending", response_model=List[EmissionFactorResponse])
async def list_pending_approvals(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    List all emission factors pending approval.
    Only ADMIN and SUPER_ADMIN can view pending approvals.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can view pending approvals")

    query = (
        select(EmissionFactor)
        .where(EmissionFactor.status == EmissionFactorStatus.PENDING_APPROVAL)
        .order_by(EmissionFactor.submitted_at)
    )
    result = await session.execute(query)
    factors = result.scalars().all()

    return [EmissionFactorResponse.model_validate(f) for f in factors]


@router.get("/{factor_id}", response_model=EmissionFactorResponse)
async def get_emission_factor(
    factor_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a single emission factor by ID."""
    result = await session.execute(
        select(EmissionFactor).where(EmissionFactor.id == factor_id)
    )
    factor = result.scalar_one_or_none()

    if not factor:
        raise HTTPException(status_code=404, detail="Emission factor not found")

    return EmissionFactorResponse.model_validate(factor)


@router.get("/{factor_id}/history", response_model=List[EmissionFactorResponse])
async def get_emission_factor_history(
    factor_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Get version history of an emission factor.
    Returns all previous versions by following previous_version_id chain.
    """
    history = []
    current_id = factor_id

    while current_id:
        result = await session.execute(
            select(EmissionFactor).where(EmissionFactor.id == current_id)
        )
        factor = result.scalar_one_or_none()

        if not factor:
            break

        history.append(EmissionFactorResponse.model_validate(factor))
        current_id = factor.previous_version_id

    return history


@router.post("", response_model=EmissionFactorResponse)
async def create_emission_factor(
    data: EmissionFactorCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new emission factor (as draft).

    - EDITOR can create drafts
    - ADMIN/SUPER_ADMIN can create and auto-approve
    """
    if current_user.role == UserRole.VIEWER:
        raise HTTPException(status_code=403, detail="Viewers cannot create emission factors")

    # Check for duplicate activity_key + region + year
    existing = await session.execute(
        select(EmissionFactor).where(
            EmissionFactor.activity_key == data.activity_key,
            EmissionFactor.region == data.region,
            EmissionFactor.year == data.year,
            EmissionFactor.status.in_([EmissionFactorStatus.APPROVED, EmissionFactorStatus.PENDING_APPROVAL]),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Emission factor already exists for {data.activity_key} in {data.region} for {data.year}"
        )

    # Determine initial status based on user role
    if current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        status = EmissionFactorStatus.APPROVED
        approved_at = datetime.utcnow()
        approved_by_id = current_user.id
    else:
        status = EmissionFactorStatus.DRAFT
        approved_at = None
        approved_by_id = None

    factor = EmissionFactor(
        **data.model_dump(),
        status=status,
        version=1,
        created_by_id=current_user.id,
        approved_at=approved_at,
        approved_by_id=approved_by_id,
    )

    session.add(factor)
    await session.commit()
    await session.refresh(factor)

    return EmissionFactorResponse.model_validate(factor)


@router.put("/{factor_id}", response_model=EmissionFactorResponse)
async def update_emission_factor(
    factor_id: UUID,
    data: EmissionFactorUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Update an emission factor.

    - Creates a new version (old version is archived)
    - Requires change_reason
    - Goes to draft status unless user is admin
    """
    if current_user.role == UserRole.VIEWER:
        raise HTTPException(status_code=403, detail="Viewers cannot edit emission factors")

    # Get existing factor
    result = await session.execute(
        select(EmissionFactor).where(EmissionFactor.id == factor_id)
    )
    old_factor = result.scalar_one_or_none()

    if not old_factor:
        raise HTTPException(status_code=404, detail="Emission factor not found")

    # Archive the old version
    old_factor.status = EmissionFactorStatus.ARCHIVED
    old_factor.is_active = False

    # Determine status for new version
    if current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        status = EmissionFactorStatus.APPROVED
        approved_at = datetime.utcnow()
        approved_by_id = current_user.id
    else:
        status = EmissionFactorStatus.DRAFT
        approved_at = None
        approved_by_id = None

    # Create new version
    new_factor = EmissionFactor(
        scope=old_factor.scope,
        category_code=old_factor.category_code,
        subcategory=old_factor.subcategory,
        activity_key=old_factor.activity_key,
        display_name=data.display_name or old_factor.display_name,
        co2_factor=data.co2_factor if data.co2_factor is not None else old_factor.co2_factor,
        ch4_factor=data.ch4_factor if data.ch4_factor is not None else old_factor.ch4_factor,
        n2o_factor=data.n2o_factor if data.n2o_factor is not None else old_factor.n2o_factor,
        co2e_factor=data.co2e_factor if data.co2e_factor is not None else old_factor.co2e_factor,
        activity_unit=data.activity_unit or old_factor.activity_unit,
        factor_unit=data.factor_unit or old_factor.factor_unit,
        source=data.source or old_factor.source,
        region=old_factor.region,
        year=old_factor.year,
        notes=data.notes if data.notes is not None else old_factor.notes,
        status=status,
        version=old_factor.version + 1,
        previous_version_id=old_factor.id,
        change_reason=data.change_reason,
        created_by_id=current_user.id,
        approved_at=approved_at,
        approved_by_id=approved_by_id,
    )

    session.add(new_factor)
    await session.commit()
    await session.refresh(new_factor)

    return EmissionFactorResponse.model_validate(new_factor)


@router.post("/{factor_id}/submit", response_model=EmissionFactorResponse)
async def submit_for_approval(
    factor_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a draft emission factor for approval.
    """
    result = await session.execute(
        select(EmissionFactor).where(EmissionFactor.id == factor_id)
    )
    factor = result.scalar_one_or_none()

    if not factor:
        raise HTTPException(status_code=404, detail="Emission factor not found")

    if factor.status != EmissionFactorStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft factors can be submitted for approval")

    factor.status = EmissionFactorStatus.PENDING_APPROVAL
    factor.submitted_at = datetime.utcnow()
    factor.submitted_by_id = current_user.id

    await session.commit()
    await session.refresh(factor)

    return EmissionFactorResponse.model_validate(factor)


@router.post("/{factor_id}/approve", response_model=EmissionFactorResponse)
async def approve_emission_factor(
    factor_id: UUID,
    action: ApprovalAction,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Approve a pending emission factor.
    Only ADMIN and SUPER_ADMIN can approve.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can approve emission factors")

    result = await session.execute(
        select(EmissionFactor).where(EmissionFactor.id == factor_id)
    )
    factor = result.scalar_one_or_none()

    if not factor:
        raise HTTPException(status_code=404, detail="Emission factor not found")

    if factor.status != EmissionFactorStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail="Only pending factors can be approved")

    # Archive any existing approved factor with same key/region/year
    existing_query = select(EmissionFactor).where(
        EmissionFactor.activity_key == factor.activity_key,
        EmissionFactor.region == factor.region,
        EmissionFactor.year == factor.year,
        EmissionFactor.status == EmissionFactorStatus.APPROVED,
        EmissionFactor.id != factor_id,
    )
    existing_result = await session.execute(existing_query)
    for existing in existing_result.scalars().all():
        existing.status = EmissionFactorStatus.ARCHIVED
        existing.is_active = False

    # Approve the factor
    factor.status = EmissionFactorStatus.APPROVED
    factor.approved_at = datetime.utcnow()
    factor.approved_by_id = current_user.id
    factor.is_active = True

    await session.commit()
    await session.refresh(factor)

    return EmissionFactorResponse.model_validate(factor)


@router.post("/{factor_id}/reject", response_model=EmissionFactorResponse)
async def reject_emission_factor(
    factor_id: UUID,
    action: ApprovalAction,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Reject a pending emission factor.
    Only ADMIN and SUPER_ADMIN can reject.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can reject emission factors")

    result = await session.execute(
        select(EmissionFactor).where(EmissionFactor.id == factor_id)
    )
    factor = result.scalar_one_or_none()

    if not factor:
        raise HTTPException(status_code=404, detail="Emission factor not found")

    if factor.status != EmissionFactorStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail="Only pending factors can be rejected")

    factor.status = EmissionFactorStatus.REJECTED
    factor.rejected_at = datetime.utcnow()
    factor.rejected_by_id = current_user.id
    factor.rejection_reason = action.reason

    await session.commit()
    await session.refresh(factor)

    return EmissionFactorResponse.model_validate(factor)


@router.delete("/{factor_id}")
async def archive_emission_factor(
    factor_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Archive (soft delete) an emission factor.
    Only ADMIN and SUPER_ADMIN can archive.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can archive emission factors")

    result = await session.execute(
        select(EmissionFactor).where(EmissionFactor.id == factor_id)
    )
    factor = result.scalar_one_or_none()

    if not factor:
        raise HTTPException(status_code=404, detail="Emission factor not found")

    factor.status = EmissionFactorStatus.ARCHIVED
    factor.is_active = False
    factor.updated_at = datetime.utcnow()
    factor.updated_by_id = current_user.id

    await session.commit()

    return {"message": "Emission factor archived successfully"}
