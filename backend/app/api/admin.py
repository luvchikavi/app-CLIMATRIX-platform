"""
Admin API endpoints for super users.
Provides access to all organizations, users, and activity logs.
"""
from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.database import get_session
from app.models.core import User, Organization, UserRole, ReportingPeriod, Site
from app.models.emission import Activity, Emission
from app.api.auth import get_current_user, get_password_hash

router = APIRouter()


# ============================================================================
# Super Admin Check
# ============================================================================

async def require_super_admin(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Require super admin role for access."""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Super admin access required"
        )
    return current_user


# ============================================================================
# Response Schemas
# ============================================================================

class OrganizationSummary(BaseModel):
    id: str
    name: str
    country_code: str | None
    default_region: str
    is_active: bool
    created_at: datetime
    user_count: int
    period_count: int
    activity_count: int
    total_co2e_kg: float


class UserSummary(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    is_active: bool
    organization_id: str
    organization_name: str
    created_at: datetime
    last_login: datetime | None


class ActivityLog(BaseModel):
    id: str
    organization_name: str
    user_email: str | None
    scope: int
    category_code: str
    activity_key: str
    description: str
    quantity: float
    unit: str
    co2e_kg: float | None
    activity_date: str
    created_at: datetime


class AdminStats(BaseModel):
    total_organizations: int
    total_users: int
    total_activities: int
    total_co2e_tonnes: float
    active_organizations: int
    activities_this_month: int


class CreateUserRequest(BaseModel):
    """Request to create a new user."""
    email: str
    password: str
    full_name: str
    role: str = "editor"  # viewer, editor, admin
    organization_id: Optional[str] = None  # If not provided, uses super admin's org


class CreateUserResponse(BaseModel):
    """Response after creating a user."""
    id: str
    email: str
    full_name: str
    role: str
    organization_id: str
    organization_name: str
    created_at: datetime


# ============================================================================
# Admin Endpoints
# ============================================================================

@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[User, Depends(require_super_admin)],
):
    """Get overall platform statistics."""
    # Total organizations
    org_result = await session.execute(select(func.count(Organization.id)))
    total_orgs = org_result.scalar() or 0

    # Active organizations
    active_org_result = await session.execute(
        select(func.count(Organization.id)).where(Organization.is_active == True)
    )
    active_orgs = active_org_result.scalar() or 0

    # Total users
    user_result = await session.execute(select(func.count(User.id)))
    total_users = user_result.scalar() or 0

    # Total activities
    activity_result = await session.execute(select(func.count(Activity.id)))
    total_activities = activity_result.scalar() or 0

    # Total emissions
    emission_result = await session.execute(select(func.sum(Emission.co2e_kg)))
    total_co2e_kg = emission_result.scalar() or 0

    # Activities this month
    from datetime import date
    first_of_month = date.today().replace(day=1)
    month_result = await session.execute(
        select(func.count(Activity.id)).where(Activity.created_at >= first_of_month)
    )
    activities_this_month = month_result.scalar() or 0

    return AdminStats(
        total_organizations=total_orgs,
        total_users=total_users,
        total_activities=total_activities,
        total_co2e_tonnes=total_co2e_kg / 1000,
        active_organizations=active_orgs,
        activities_this_month=activities_this_month
    )


@router.post("/users", response_model=CreateUserResponse)
async def create_user(
    data: CreateUserRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(require_super_admin)],
):
    """
    Create a new user (super admin only).

    - If organization_id is not provided, the user will be added to the super admin's organization.
    - Valid roles: viewer, editor, admin
    """
    from uuid import uuid4

    # Validate role
    try:
        role = UserRole(data.role)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role: {data.role}. Must be one of: viewer, editor, admin"
        )

    # Check if email already exists
    existing_result = await session.execute(
        select(User).where(User.email == data.email)
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Email {data.email} is already registered"
        )

    # Determine organization
    if data.organization_id:
        org_result = await session.execute(
            select(Organization).where(Organization.id == UUID(data.organization_id))
        )
        org = org_result.scalar_one_or_none()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
    else:
        # Use super admin's organization
        org_result = await session.execute(
            select(Organization).where(Organization.id == current_user.organization_id)
        )
        org = org_result.scalar_one_or_none()

    # Create user
    new_user = User(
        id=uuid4(),
        email=data.email,
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password),
        role=role,
        organization_id=org.id,
        is_active=True,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return CreateUserResponse(
        id=str(new_user.id),
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role.value,
        organization_id=str(org.id),
        organization_name=org.name,
        created_at=new_user.created_at
    )


class UpdatePasswordRequest(BaseModel):
    """Request to update a user's password."""
    email: str
    new_password: str


@router.put("/users/password")
async def update_user_password(
    data: UpdatePasswordRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[User, Depends(require_super_admin)],
):
    """
    Update a user's password (super admin only).
    """
    # Find user by email
    result = await session.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail=f"User with email {data.email} not found")

    # Update password
    user.hashed_password = get_password_hash(data.new_password)
    await session.commit()

    return {"message": f"Password updated for {data.email}"}


@router.get("/organizations", response_model=list[OrganizationSummary])
async def list_all_organizations(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[User, Depends(require_super_admin)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List all organizations with summary statistics."""
    result = await session.execute(
        select(Organization).offset(skip).limit(limit).order_by(Organization.created_at.desc())
    )
    organizations = result.scalars().all()

    summaries = []
    for org in organizations:
        # Get counts
        user_count = await session.execute(
            select(func.count(User.id)).where(User.organization_id == org.id)
        )
        period_count = await session.execute(
            select(func.count(ReportingPeriod.id)).where(ReportingPeriod.organization_id == org.id)
        )
        activity_count = await session.execute(
            select(func.count(Activity.id)).where(Activity.organization_id == org.id)
        )

        # Get total emissions
        emission_sum = await session.execute(
            select(func.sum(Emission.co2e_kg))
            .join(Activity, Emission.activity_id == Activity.id)
            .where(Activity.organization_id == org.id)
        )

        summaries.append(OrganizationSummary(
            id=str(org.id),
            name=org.name,
            country_code=org.country_code,
            default_region=org.default_region,
            is_active=org.is_active,
            created_at=org.created_at,
            user_count=user_count.scalar() or 0,
            period_count=period_count.scalar() or 0,
            activity_count=activity_count.scalar() or 0,
            total_co2e_kg=emission_sum.scalar() or 0
        ))

    return summaries


@router.get("/organizations/{org_id}", response_model=OrganizationSummary)
async def get_organization_details(
    org_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[User, Depends(require_super_admin)],
):
    """Get detailed information about a specific organization."""
    result = await session.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get counts
    user_count = await session.execute(
        select(func.count(User.id)).where(User.organization_id == org.id)
    )
    period_count = await session.execute(
        select(func.count(ReportingPeriod.id)).where(ReportingPeriod.organization_id == org.id)
    )
    activity_count = await session.execute(
        select(func.count(Activity.id)).where(Activity.organization_id == org.id)
    )
    emission_sum = await session.execute(
        select(func.sum(Emission.co2e_kg))
        .join(Activity, Emission.activity_id == Activity.id)
        .where(Activity.organization_id == org.id)
    )

    return OrganizationSummary(
        id=str(org.id),
        name=org.name,
        country_code=org.country_code,
        default_region=org.default_region,
        is_active=org.is_active,
        created_at=org.created_at,
        user_count=user_count.scalar() or 0,
        period_count=period_count.scalar() or 0,
        activity_count=activity_count.scalar() or 0,
        total_co2e_kg=emission_sum.scalar() or 0
    )


@router.get("/users", response_model=list[UserSummary])
async def list_all_users(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[User, Depends(require_super_admin)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    org_id: Optional[UUID] = None,
):
    """List all users across all organizations."""
    query = select(User, Organization.name).join(Organization, User.organization_id == Organization.id)

    if org_id:
        query = query.where(User.organization_id == org_id)

    query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
    result = await session.execute(query)
    rows = result.all()

    return [
        UserSummary(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            organization_id=str(user.organization_id),
            organization_name=org_name,
            created_at=user.created_at,
            last_login=user.last_login
        )
        for user, org_name in rows
    ]


@router.get("/activities", response_model=list[ActivityLog])
async def list_all_activities(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[User, Depends(require_super_admin)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    org_id: Optional[UUID] = None,
    scope: Optional[int] = None,
):
    """List all activities across all organizations (activity log)."""
    query = (
        select(Activity, Organization.name, Emission.co2e_kg)
        .join(Organization, Activity.organization_id == Organization.id)
        .outerjoin(Emission, Emission.activity_id == Activity.id)
    )

    if org_id:
        query = query.where(Activity.organization_id == org_id)
    if scope:
        query = query.where(Activity.scope == scope)

    query = query.offset(skip).limit(limit).order_by(Activity.created_at.desc())
    result = await session.execute(query)
    rows = result.all()

    return [
        ActivityLog(
            id=str(activity.id),
            organization_name=org_name,
            user_email=None,  # Would need to track created_by
            scope=activity.scope,
            category_code=activity.category_code,
            activity_key=activity.activity_key,
            description=activity.description,
            quantity=float(activity.quantity),
            unit=activity.unit,
            co2e_kg=float(co2e_kg) if co2e_kg else None,
            activity_date=activity.activity_date.isoformat(),
            created_at=activity.created_at
        )
        for activity, org_name, co2e_kg in rows
    ]


@router.get("/organizations/{org_id}/report")
async def get_organization_report(
    org_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[User, Depends(require_super_admin)],
):
    """Get full emissions report for a specific organization."""
    # Verify organization exists
    org_result = await session.execute(select(Organization).where(Organization.id == org_id))
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get all activities with emissions for this org
    result = await session.execute(
        select(Activity, Emission)
        .outerjoin(Emission, Emission.activity_id == Activity.id)
        .where(Activity.organization_id == org_id)
        .order_by(Activity.scope, Activity.category_code)
    )
    rows = result.all()

    # Calculate totals by scope
    scope_totals = {1: 0.0, 2: 0.0, 3: 0.0}
    activities_by_scope = {1: [], 2: [], 3: []}

    for activity, emission in rows:
        co2e = float(emission.co2e_kg) if emission else 0
        scope_totals[activity.scope] += co2e
        activities_by_scope[activity.scope].append({
            "id": str(activity.id),
            "category_code": activity.category_code,
            "activity_key": activity.activity_key,
            "description": activity.description,
            "quantity": float(activity.quantity),
            "unit": activity.unit,
            "co2e_kg": co2e,
            "activity_date": activity.activity_date.isoformat()
        })

    total_co2e = sum(scope_totals.values())

    return {
        "organization": {
            "id": str(org.id),
            "name": org.name,
            "country_code": org.country_code
        },
        "total_co2e_kg": total_co2e,
        "total_co2e_tonnes": total_co2e / 1000,
        "by_scope": {
            "scope_1": {
                "total_co2e_kg": scope_totals[1],
                "activity_count": len(activities_by_scope[1]),
                "activities": activities_by_scope[1]
            },
            "scope_2": {
                "total_co2e_kg": scope_totals[2],
                "activity_count": len(activities_by_scope[2]),
                "activities": activities_by_scope[2]
            },
            "scope_3": {
                "total_co2e_kg": scope_totals[3],
                "activity_count": len(activities_by_scope[3]),
                "activities": activities_by_scope[3]
            }
        }
    }
