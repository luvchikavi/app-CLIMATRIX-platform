"""
Audit log API endpoints.
Provides read access to audit trail for compliance and monitoring.
"""
from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models.core import User, UserRole, AuditAction
from app.api.auth import get_current_user
from app.services.audit import AuditService


router = APIRouter(prefix="/audit", tags=["Audit"])


class AuditLogResponse(BaseModel):
    """Audit log entry response."""
    id: str
    action: str
    resource_type: str
    resource_id: str | None
    description: str
    details: str | None
    user_email: str | None
    ip_address: str | None
    created_at: str


class AuditLogsListResponse(BaseModel):
    """Paginated audit logs response."""
    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int


class AuditStatsResponse(BaseModel):
    """Audit statistics response."""
    total_events: int
    events_by_action: dict[str, int]
    events_by_resource: dict[str, int]
    recent_activity_count: int  # Last 24 hours


@router.get("/logs", response_model=AuditLogsListResponse)
async def get_audit_logs(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    user_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Get audit logs for the organization.
    Supports filtering and pagination.
    Requires admin role.
    """
    # Check permissions - only admins can view audit logs
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can view audit logs")

    # Parse action filter
    action_enum = None
    if action:
        try:
            action_enum = AuditAction(action)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

    # Get logs
    logs = await AuditService.get_logs(
        session=session,
        organization_id=current_user.organization_id,
        limit=limit,
        offset=offset,
        action=action_enum,
        resource_type=resource_type,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )

    # Get total count
    total = await AuditService.get_logs_count(
        session=session,
        organization_id=current_user.organization_id,
        action=action_enum,
        resource_type=resource_type,
    )

    return AuditLogsListResponse(
        items=[
            AuditLogResponse(
                id=str(log.id),
                action=log.action.value,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                description=log.description,
                details=log.details,
                user_email=log.user_email,
                ip_address=log.ip_address,
                created_at=log.created_at.isoformat(),
            )
            for log in logs
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Get audit statistics for the organization.
    Requires admin role.
    """
    from datetime import timedelta
    from sqlalchemy import func
    from sqlmodel import select
    from app.models.core import AuditLog

    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can view audit stats")

    org_id = current_user.organization_id

    # Total events
    total_result = await session.execute(
        select(func.count(AuditLog.id)).where(AuditLog.organization_id == org_id)
    )
    total_events = total_result.scalar() or 0

    # Events by action
    action_result = await session.execute(
        select(AuditLog.action, func.count(AuditLog.id))
        .where(AuditLog.organization_id == org_id)
        .group_by(AuditLog.action)
    )
    events_by_action = {row[0].value: row[1] for row in action_result.all()}

    # Events by resource type
    resource_result = await session.execute(
        select(AuditLog.resource_type, func.count(AuditLog.id))
        .where(AuditLog.organization_id == org_id)
        .group_by(AuditLog.resource_type)
    )
    events_by_resource = {row[0]: row[1] for row in resource_result.all()}

    # Recent activity (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_result = await session.execute(
        select(func.count(AuditLog.id))
        .where(AuditLog.organization_id == org_id)
        .where(AuditLog.created_at >= yesterday)
    )
    recent_count = recent_result.scalar() or 0

    return AuditStatsResponse(
        total_events=total_events,
        events_by_action=events_by_action,
        events_by_resource=events_by_resource,
        recent_activity_count=recent_count,
    )


@router.get("/actions")
async def get_audit_actions(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get list of available audit action types."""
    return {
        "actions": [action.value for action in AuditAction]
    }


@router.get("/resource-types")
async def get_resource_types(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get list of resource types that have audit logs."""
    from sqlmodel import select
    from app.models.core import AuditLog

    result = await session.execute(
        select(AuditLog.resource_type)
        .where(AuditLog.organization_id == current_user.organization_id)
        .distinct()
    )

    return {
        "resource_types": [row[0] for row in result.all()]
    }
