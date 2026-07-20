"""Verifier read-only portal — the "audit-ready platform + verifier read-only
role" build item (docs/AUDIT-PARTNERS-RESEARCH.md §3).

Two surfaces, deliberately separated:

- Org-side (authed admin): invite an external verifier to ONE reporting period,
  list invites, revoke. Every grant is audit-logged.
- Verifier-side (token-gated, NO login): the token is the sole credential and
  unlocks exactly that period's inventory + per-line provenance + audit log +
  evidence — read-only, one org, one period. There is no write endpoint and no
  path from the token to any other data.
"""

from __future__ import annotations

import secrets
from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.config import settings
from app.database import get_session
from app.models.core import (
    AuditAction,
    AuditLog,
    Organization,
    ReportingPeriod,
    User,
    UserRole,
    VerifierAccess,
)
from app.models.emission import Activity, Emission
from app.services.audit import AuditService

router = APIRouter()


# ---------------------------------------------------------------------------
# schemas
# ---------------------------------------------------------------------------


class VerifierInviteBody(BaseModel):
    verifier_email: str
    verifier_name: Optional[str] = None
    expires_in_days: Optional[int] = None  # None = no expiry


class VerifierAccessOut(BaseModel):
    id: UUID
    reporting_period_id: UUID
    verifier_email: str
    verifier_name: Optional[str]
    status: str
    portal_url: str
    created_at: datetime
    expires_at: Optional[datetime]
    last_accessed_at: Optional[datetime]


class VerifierLineOut(BaseModel):
    """One inventory line, with the full traceability a verifier checks."""

    id: UUID
    scope: int
    category_code: str
    activity_key: str
    description: str
    quantity: float
    unit: str
    activity_date: Optional[str]
    site: Optional[str]
    region: Optional[str]
    co2e_kg: Optional[float]
    factor_source_year: Optional[int]
    factor_region: Optional[str]
    method: Optional[str]
    formula: Optional[str]
    confidence: Optional[str]
    data_quality_score: Optional[int]
    data_quality_justification: Optional[str]


class VerifierPeriodOut(BaseModel):
    organization_name: str
    period_name: str
    period_start: Optional[str]
    period_end: Optional[str]
    status: str
    assurance_level: Optional[str]
    verified_by: Optional[str]
    verifier_name: Optional[str]
    total_co2e_kg: float
    scope_1_co2e_kg: float
    scope_2_co2e_kg: float
    scope_3_co2e_kg: float
    line_count: int
    read_only: bool = True


class VerifierAuditEntryOut(BaseModel):
    action: str
    resource_type: str
    description: str
    user_email: Optional[str]
    created_at: datetime


# ---------------------------------------------------------------------------
# org-side management (authed)
# ---------------------------------------------------------------------------


def _portal_url(token: str) -> str:
    base = (settings.frontend_url or "").rstrip("/")
    return f"{base}/verify/{token}"


def _access_out(a: VerifierAccess) -> VerifierAccessOut:
    return VerifierAccessOut(
        id=a.id,
        reporting_period_id=a.reporting_period_id,
        verifier_email=a.verifier_email,
        verifier_name=a.verifier_name,
        status=a.status,
        portal_url=_portal_url(a.token),
        created_at=a.created_at,
        expires_at=a.expires_at,
        last_accessed_at=a.last_accessed_at,
    )


def _require_admin(user: User) -> None:
    if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=403, detail="Only an organization admin can invite verifiers."
        )


@router.post("/periods/{period_id}/verifier-access", response_model=VerifierAccessOut)
async def invite_verifier(
    period_id: UUID,
    body: VerifierInviteBody,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Invite an external verifier to review this reporting period (read-only)."""
    _require_admin(current_user)

    period = await session.get(ReportingPeriod, period_id)
    if period is None or period.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Reporting period not found")

    from datetime import timedelta

    expires_at = None
    if body.expires_in_days is not None:
        if body.expires_in_days <= 0:
            raise HTTPException(status_code=400, detail="expires_in_days must be > 0")
        expires_at = datetime.utcnow() + timedelta(days=body.expires_in_days)

    access = VerifierAccess(
        organization_id=current_user.organization_id,
        reporting_period_id=period_id,
        token=secrets.token_urlsafe(32),
        verifier_email=body.verifier_email.strip(),
        verifier_name=(body.verifier_name or "").strip() or None,
        created_by=current_user.id,
        expires_at=expires_at,
    )
    session.add(access)
    await session.flush()

    await AuditService.log(
        session,
        organization_id=current_user.organization_id,
        action=AuditAction.INVITE,
        resource_type="verifier_access",
        resource_id=str(access.id),
        description=(
            f"Invited verifier {access.verifier_email} to period '{period.name}'"
        ),
        user=current_user,
        details={"period_id": str(period_id), "verifier_email": access.verifier_email},
    )
    await session.refresh(access)
    return _access_out(access)


@router.get(
    "/periods/{period_id}/verifier-access",
    response_model=list[VerifierAccessOut],
)
async def list_verifier_access(
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    period = await session.get(ReportingPeriod, period_id)
    if period is None or period.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Reporting period not found")
    rows = (
        (
            await session.execute(
                select(VerifierAccess)
                .where(
                    VerifierAccess.reporting_period_id == period_id,
                    VerifierAccess.organization_id == current_user.organization_id,
                )
                .order_by(VerifierAccess.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [_access_out(a) for a in rows]


@router.delete("/verifier-access/{access_id}")
async def revoke_verifier_access(
    access_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Revoke a verifier's access immediately (the portal 403s on next request)."""
    _require_admin(current_user)
    access = await session.get(VerifierAccess, access_id)
    if access is None or access.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Verifier access not found")
    access.status = "revoked"
    access.revoked_at = datetime.utcnow()
    await AuditService.log(
        session,
        organization_id=current_user.organization_id,
        action=AuditAction.PERMISSION_CHANGE,
        resource_type="verifier_access",
        resource_id=str(access.id),
        description=f"Revoked verifier access for {access.verifier_email}",
        user=current_user,
    )
    return {"status": "revoked", "id": str(access_id)}


# ---------------------------------------------------------------------------
# verifier-side (token-gated, no auth) — the token IS the credential
# ---------------------------------------------------------------------------


async def _resolve_token(
    token: str, session: AsyncSession, *, touch: bool = False
) -> VerifierAccess:
    access = (
        await session.execute(
            select(VerifierAccess).where(VerifierAccess.token == token)
        )
    ).scalar_one_or_none()
    if access is None or access.status != "active":
        raise HTTPException(status_code=404, detail="This verifier link is not valid.")
    if access.expires_at is not None and access.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=403, detail="This verifier link has expired.")
    if touch:
        access.last_accessed_at = datetime.utcnow()
        await session.commit()
    return access


@router.get("/verify/{token}", response_model=VerifierPeriodOut)
async def verifier_period(
    token: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Landing summary for the verifier: org, period, assurance, totals."""
    access = await _resolve_token(token, session, touch=True)
    org = await session.get(Organization, access.organization_id)
    period = await session.get(ReportingPeriod, access.reporting_period_id)
    if org is None or period is None:
        raise HTTPException(status_code=404, detail="This verifier link is not valid.")

    rows = (
        await session.execute(
            select(Activity.scope, func.coalesce(func.sum(Emission.co2e_kg), 0))
            .join(Emission, Emission.activity_id == Activity.id)
            .where(Activity.reporting_period_id == period.id)
            .group_by(Activity.scope)
        )
    ).all()
    by_scope = {int(s): float(v) for s, v in rows}
    count = (
        await session.execute(
            select(func.count())
            .select_from(Activity)
            .where(Activity.reporting_period_id == period.id)
        )
    ).scalar_one()

    return VerifierPeriodOut(
        organization_name=org.name,
        period_name=period.name,
        period_start=period.start_date.isoformat() if period.start_date else None,
        period_end=period.end_date.isoformat() if period.end_date else None,
        status=(
            period.status.value
            if hasattr(period.status, "value")
            else str(period.status)
        ),
        assurance_level=(
            period.assurance_level.value
            if period.assurance_level and hasattr(period.assurance_level, "value")
            else (period.assurance_level or None)
        ),
        verified_by=period.verified_by,
        verifier_name=access.verifier_name,
        total_co2e_kg=sum(by_scope.values()),
        scope_1_co2e_kg=by_scope.get(1, 0.0),
        scope_2_co2e_kg=by_scope.get(2, 0.0),
        scope_3_co2e_kg=by_scope.get(3, 0.0),
        line_count=int(count or 0),
    )


@router.get("/verify/{token}/inventory", response_model=list[VerifierLineOut])
async def verifier_inventory(
    token: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Every inventory line with its full traceability (source → factor →
    method → result). This per-line derivation trail is the differentiator."""
    access = await _resolve_token(token, session)
    from app.models.core import Site

    result = await session.execute(
        select(Activity, Emission)
        .join(Emission, Emission.activity_id == Activity.id, isouter=True)
        .where(Activity.reporting_period_id == access.reporting_period_id)
        .order_by(Activity.scope, Activity.category_code)
    )
    pairs = result.all()

    # Resolve site names in one pass.
    site_ids = {a.site_id for a, _ in pairs if a.site_id}
    site_names: dict = {}
    if site_ids:
        for s in (
            await session.execute(select(Site).where(Site.id.in_(site_ids)))
        ).scalars():
            site_names[s.id] = s.name

    out = []
    for a, e in pairs:
        out.append(
            VerifierLineOut(
                id=a.id,
                scope=a.scope,
                category_code=a.category_code,
                activity_key=a.activity_key,
                description=a.description or "",
                quantity=float(a.quantity),
                unit=a.unit,
                activity_date=a.activity_date.isoformat() if a.activity_date else None,
                site=site_names.get(a.site_id),
                region=getattr(a, "region", None),
                co2e_kg=float(e.co2e_kg) if e and e.co2e_kg is not None else None,
                factor_source_year=e.factor_year if e else None,
                factor_region=e.factor_region if e else None,
                method=(e.method_hierarchy or e.resolution_strategy) if e else None,
                formula=e.formula if e else None,
                confidence=(
                    e.confidence.value
                    if e and hasattr(e.confidence, "value")
                    else (str(e.confidence) if e else None)
                ),
                data_quality_score=a.data_quality_score,
                data_quality_justification=a.data_quality_justification,
            )
        )
    return out


@router.get("/verify/{token}/audit-log", response_model=list[VerifierAuditEntryOut])
async def verifier_audit_log(
    token: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """The org's audit trail — the immutable record of who changed what."""
    access = await _resolve_token(token, session)
    rows = (
        (
            await session.execute(
                select(AuditLog)
                .where(AuditLog.organization_id == access.organization_id)
                .order_by(AuditLog.created_at.desc())
                .limit(500)
            )
        )
        .scalars()
        .all()
    )
    return [
        VerifierAuditEntryOut(
            action=r.action.value if hasattr(r.action, "value") else str(r.action),
            resource_type=r.resource_type,
            description=r.description,
            user_email=r.user_email,
            created_at=r.created_at,
        )
        for r in rows
    ]
