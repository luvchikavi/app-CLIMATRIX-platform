"""
Audit logging service for tracking all significant actions.
Provides methods for logging and querying audit events.
"""
import json
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc

from app.models.core import AuditLog, AuditAction, User


class AuditService:
    """Service for managing audit logs."""

    @staticmethod
    async def log(
        session: AsyncSession,
        organization_id: UUID,
        action: AuditAction,
        resource_type: str,
        description: str,
        user: Optional[User] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            session: Database session
            organization_id: Organization ID
            action: Type of action performed
            resource_type: Type of resource affected (e.g., "activity", "period")
            description: Human-readable description
            user: User performing the action (optional)
            resource_id: ID of the affected resource (optional)
            details: Additional details as dict (will be JSON serialized)
            ip_address: Client IP address (optional)
            user_agent: Client user agent (optional)

        Returns:
            Created AuditLog entry
        """
        log_entry = AuditLog(
            organization_id=organization_id,
            user_id=user.id if user else None,
            user_email=user.email if user else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            details=json.dumps(details) if details else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        session.add(log_entry)
        await session.commit()
        await session.refresh(log_entry)

        return log_entry

    @staticmethod
    async def log_activity_create(
        session: AsyncSession,
        organization_id: UUID,
        user: User,
        activity_id: str,
        activity_description: str,
        emission_kg: Optional[float] = None,
    ) -> AuditLog:
        """Log activity creation."""
        details = {"emission_kg": emission_kg} if emission_kg else None
        return await AuditService.log(
            session=session,
            organization_id=organization_id,
            action=AuditAction.CREATE,
            resource_type="activity",
            resource_id=activity_id,
            description=f"Created activity: {activity_description}",
            user=user,
            details=details,
        )

    @staticmethod
    async def log_activity_delete(
        session: AsyncSession,
        organization_id: UUID,
        user: User,
        activity_id: str,
        activity_description: str,
    ) -> AuditLog:
        """Log activity deletion."""
        return await AuditService.log(
            session=session,
            organization_id=organization_id,
            action=AuditAction.DELETE,
            resource_type="activity",
            resource_id=activity_id,
            description=f"Deleted activity: {activity_description}",
            user=user,
        )

    @staticmethod
    async def log_import(
        session: AsyncSession,
        organization_id: UUID,
        user: User,
        file_name: str,
        records_imported: int,
        period_id: str,
    ) -> AuditLog:
        """Log data import."""
        return await AuditService.log(
            session=session,
            organization_id=organization_id,
            action=AuditAction.IMPORT,
            resource_type="import",
            resource_id=period_id,
            description=f"Imported {records_imported} records from {file_name}",
            user=user,
            details={
                "file_name": file_name,
                "records_imported": records_imported,
                "period_id": period_id,
            },
        )

    @staticmethod
    async def log_status_change(
        session: AsyncSession,
        organization_id: UUID,
        user: User,
        resource_type: str,
        resource_id: str,
        old_status: str,
        new_status: str,
    ) -> AuditLog:
        """Log status change (e.g., period verification status)."""
        return await AuditService.log(
            session=session,
            organization_id=organization_id,
            action=AuditAction.STATUS_CHANGE,
            resource_type=resource_type,
            resource_id=resource_id,
            description=f"Changed {resource_type} status from {old_status} to {new_status}",
            user=user,
            details={"old_status": old_status, "new_status": new_status},
        )

    @staticmethod
    async def log_login(
        session: AsyncSession,
        organization_id: UUID,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log user login."""
        return await AuditService.log(
            session=session,
            organization_id=organization_id,
            action=AuditAction.LOGIN,
            resource_type="user",
            resource_id=str(user.id),
            description=f"User logged in: {user.email}",
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    async def log_export(
        session: AsyncSession,
        organization_id: UUID,
        user: User,
        export_type: str,
        period_id: Optional[str] = None,
    ) -> AuditLog:
        """Log data export."""
        return await AuditService.log(
            session=session,
            organization_id=organization_id,
            action=AuditAction.EXPORT,
            resource_type="export",
            resource_id=period_id,
            description=f"Exported data in {export_type} format",
            user=user,
            details={"export_type": export_type, "period_id": period_id},
        )

    @staticmethod
    async def log_invitation(
        session: AsyncSession,
        organization_id: UUID,
        user: User,
        invited_email: str,
        role: str,
    ) -> AuditLog:
        """Log user invitation."""
        return await AuditService.log(
            session=session,
            organization_id=organization_id,
            action=AuditAction.INVITE,
            resource_type="invitation",
            description=f"Invited {invited_email} as {role}",
            user=user,
            details={"invited_email": invited_email, "role": role},
        )

    @staticmethod
    async def get_logs(
        session: AsyncSession,
        organization_id: UUID,
        limit: int = 100,
        offset: int = 0,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        user_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[AuditLog]:
        """
        Query audit logs with optional filters.

        Args:
            session: Database session
            organization_id: Organization to query
            limit: Max number of results
            offset: Pagination offset
            action: Filter by action type
            resource_type: Filter by resource type
            user_id: Filter by user
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of audit log entries
        """
        query = select(AuditLog).where(
            AuditLog.organization_id == organization_id
        )

        if action:
            query = query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)

        query = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_logs_count(
        session: AsyncSession,
        organization_id: UUID,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
    ) -> int:
        """Get total count of audit logs matching filters."""
        from sqlalchemy import func

        query = select(func.count(AuditLog.id)).where(
            AuditLog.organization_id == organization_id
        )

        if action:
            query = query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)

        result = await session.execute(query)
        return result.scalar() or 0
