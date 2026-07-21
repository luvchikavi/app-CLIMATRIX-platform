"""
EPD API — declaration projects, the ISO 14025 status machine, EN 15804
document exports, and the verification workflow.

Verification reuses VerifierAccess: the same token-gated read-only portal
that serves corporate periods serves one EPD project (the
parameter-change-not-a-build insight from the module design doc).

Teaser semantics match the platform rule: modeling + workflow stay open,
document exports ride the existing entitlement lane (402 teaser, Report
Pass year lock keyed to the pinned footprint's period).
"""

import secrets
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field as PydField
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.api.verifier import _access_out, _require_admin, _resolve_token
from app.database import get_session
from app.models.core import (
    AuditAction,
    Organization,
    ReportingPeriod,
    User,
    VerifierAccess,
)
from app.models.product import (
    EPDProject,
    EPDStatus,
    Product,
    ProductFootprint,
    ProductInput,
)
from app.services import epd as epd_service
from app.services.audit import AuditService
from app.services.entitlements import (
    ensure_period_year_licensed,
    get_entitlement,
    require_report_generation,
)

router = APIRouter()


# ---------------------------------------------------------------- schemas


class EPDCreate(BaseModel):
    name: Optional[str] = PydField(default=None, max_length=255)
    pcr: str = PydField(default="EN 15804+A2", max_length=100)
    program_operator: Optional[str] = PydField(default=None, max_length=255)
    functional_unit: Optional[str] = PydField(default=None, max_length=255)
    rsl_years: Optional[int] = PydField(default=None, ge=1, le=200)
    scope_modules: Optional[List[str]] = None
    footprint_id: Optional[UUID] = None


class EPDUpdate(BaseModel):
    name: Optional[str] = PydField(default=None, min_length=1, max_length=255)
    pcr: Optional[str] = PydField(default=None, max_length=100)
    program_operator: Optional[str] = PydField(default=None, max_length=255)
    functional_unit: Optional[str] = PydField(default=None, max_length=255)
    rsl_years: Optional[int] = PydField(default=None, ge=1, le=200)
    scope_modules: Optional[List[str]] = None
    footprint_id: Optional[UUID] = None
    registration_number: Optional[str] = PydField(default=None, max_length=100)
    verifier_statement: Optional[str] = PydField(default=None, max_length=2000)
    notes: Optional[str] = PydField(default=None, max_length=2000)


class EPDTransition(BaseModel):
    status: str


class EPDVerifierInvite(BaseModel):
    verifier_email: str
    verifier_name: Optional[str] = None
    expires_in_days: Optional[int] = None


class EPDOut(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str
    footprint_id: Optional[UUID]
    name: str
    pcr: str
    program_operator: Optional[str]
    declared_unit: str
    declared_unit_amount: Decimal
    functional_unit: Optional[str]
    rsl_years: Optional[int]
    scope_modules: List[str]
    status: str
    version: int
    results_frozen_at: Optional[datetime]
    registration_number: Optional[str]
    registered_at: Optional[datetime]
    published_at: Optional[datetime]
    valid_until: Optional[date]
    days_until_expiry: Optional[int]
    verifier_statement: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


class EPDDetailOut(EPDOut):
    results: Optional[dict] = None
    results_are_frozen: bool = False
    checklist: List[dict] = []
    allowed_transitions: List[str] = []


# ---------------------------------------------------------------- helpers


def _epd_out(epd: EPDProject, product_name: str) -> EPDOut:
    status = epd_service.effective_status(epd)
    days = None
    if epd.valid_until is not None:
        days = (epd.valid_until - date.today()).days
    return EPDOut(
        id=epd.id,
        product_id=epd.product_id,
        product_name=product_name,
        footprint_id=epd.footprint_id,
        name=epd.name,
        pcr=epd.pcr,
        program_operator=epd.program_operator,
        declared_unit=epd.declared_unit,
        declared_unit_amount=epd.declared_unit_amount,
        functional_unit=epd.functional_unit,
        rsl_years=epd.rsl_years,
        scope_modules=epd.scope_modules or epd_service.DEFAULT_SCOPE_MODULES,
        status=status,
        version=epd.version,
        results_frozen_at=epd.results_frozen_at,
        registration_number=epd.registration_number,
        registered_at=epd.registered_at,
        published_at=epd.published_at,
        valid_until=epd.valid_until,
        days_until_expiry=days,
        verifier_statement=epd.verifier_statement,
        notes=epd.notes,
        created_at=epd.created_at,
        updated_at=epd.updated_at,
    )


async def _get_epd(
    epd_id: UUID, session: AsyncSession, current_user: User
) -> EPDProject:
    epd = await session.get(EPDProject, epd_id)
    if epd is None or epd.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="EPD project not found")
    return epd


async def _get_owned_footprint(
    session: AsyncSession, current_user: User, product_id: UUID, footprint_id: UUID
) -> ProductFootprint:
    fp = await session.get(ProductFootprint, footprint_id)
    if (
        fp is None
        or fp.organization_id != current_user.organization_id
        or fp.product_id != product_id
    ):
        raise HTTPException(
            status_code=404, detail="Footprint not found for this product"
        )
    return fp


def _validate_modules(modules: Optional[List[str]]) -> None:
    if not modules:
        return
    bad = [m for m in modules if m not in epd_service.EN15804_MODULES]
    if bad:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown EN 15804 modules: {', '.join(bad)}",
        )


async def _load_context(
    session: AsyncSession, epd: EPDProject
) -> tuple[Product, Optional[ProductFootprint], int, bool]:
    """Product + pinned footprint + BOM line count + has-active-verifier."""
    product = await session.get(Product, epd.product_id)
    footprint = None
    if epd.footprint_id:
        footprint = await session.get(ProductFootprint, epd.footprint_id)
    input_count = len(
        (
            await session.execute(
                select(ProductInput.id).where(ProductInput.product_id == epd.product_id)
            )
        ).all()
    )
    has_verifier = (
        await session.execute(
            select(VerifierAccess.id).where(
                VerifierAccess.epd_project_id == epd.id,
                VerifierAccess.status == "active",
            )
        )
    ).first() is not None
    return product, footprint, input_count, has_verifier


def _effective_results(
    epd: EPDProject, footprint: Optional[ProductFootprint], product: Product
) -> tuple[Optional[dict], bool]:
    """Frozen results once past draft; a live preview from the pinned
    footprint while drafting."""
    if epd.results:
        return epd.results, True
    if footprint is not None:
        return epd_service.freeze_results(epd, footprint, product), False
    return None, False


# ---------------------------------------------------------------- CRUD


@router.get("/epd", response_model=List[EPDOut])
async def list_epds(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    org_id = current_user.organization_id
    rows = (
        await session.execute(
            select(EPDProject, Product.name)
            .join(Product, Product.id == EPDProject.product_id)
            .where(EPDProject.organization_id == org_id)
            .order_by(EPDProject.created_at.desc())
        )
    ).all()
    return [_epd_out(epd, product_name) for epd, product_name in rows]


@router.post("/products/{product_id}/epd", response_model=EPDOut)
async def create_epd(
    product_id: UUID,
    data: EPDCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    product = await session.get(Product, product_id)
    if product is None or product.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Product not found")
    _validate_modules(data.scope_modules)
    if data.footprint_id:
        await _get_owned_footprint(session, current_user, product.id, data.footprint_id)

    epd = EPDProject(
        organization_id=current_user.organization_id,
        product_id=product.id,
        footprint_id=data.footprint_id,
        name=(data.name or f"{product.name} — EPD").strip(),
        pcr=data.pcr,
        program_operator=data.program_operator,
        declared_unit=product.declared_unit,
        declared_unit_amount=product.declared_unit_amount,
        functional_unit=data.functional_unit,
        rsl_years=data.rsl_years,
        scope_modules=data.scope_modules or epd_service.DEFAULT_SCOPE_MODULES,
        created_by=current_user.id,
    )
    session.add(epd)
    await session.flush()
    await AuditService.log(
        session,
        organization_id=current_user.organization_id,
        action=AuditAction.CREATE,
        resource_type="epd_project",
        resource_id=str(epd.id),
        description=f"Created EPD project '{epd.name}' ({epd.pcr})",
        user=current_user,
    )
    await session.refresh(epd)
    return _epd_out(epd, product.name)


@router.get("/epd/{epd_id}", response_model=EPDDetailOut)
async def get_epd(
    epd_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    epd = await _get_epd(epd_id, session, current_user)
    product, footprint, input_count, has_verifier = await _load_context(session, epd)
    results, frozen = _effective_results(epd, footprint, product)
    base = _epd_out(epd, product.name)
    return EPDDetailOut(
        **base.model_dump(),
        results=results,
        results_are_frozen=frozen,
        checklist=epd_service.readiness_checklist(
            epd, product, footprint, input_count, has_verifier
        ),
        allowed_transitions=sorted(
            epd_service.STATUS_TRANSITIONS.get(epd_service.effective_status(epd), set())
        ),
    )


@router.patch("/epd/{epd_id}", response_model=EPDOut)
async def update_epd(
    epd_id: UUID,
    data: EPDUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    epd = await _get_epd(epd_id, session, current_user)
    payload = data.model_dump(exclude_unset=True)

    # Declaration content is draft-only; workflow metadata (operator,
    # registration number, verifier statement, notes) stays editable until
    # publication — the registration number arrives DURING the workflow.
    workflow_fields = {
        "program_operator",
        "registration_number",
        "verifier_statement",
        "notes",
    }
    content_fields = set(payload) - workflow_fields
    if content_fields and not epd_service.can_edit(epd):
        raise HTTPException(
            status_code=409,
            detail="Declaration content is locked after draft — reopen to draft "
            f"to edit: {', '.join(sorted(content_fields))}",
        )
    if payload and epd_service.effective_status(epd) in (
        EPDStatus.PUBLISHED.value,
        EPDStatus.EXPIRED.value,
    ):
        raise HTTPException(status_code=409, detail="A published EPD is immutable")
    _validate_modules(payload.get("scope_modules"))
    if payload.get("footprint_id"):
        await _get_owned_footprint(
            session, current_user, epd.product_id, payload["footprint_id"]
        )
    for key, value in payload.items():
        setattr(epd, key, value)
    epd.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(epd)
    product = await session.get(Product, epd.product_id)
    return _epd_out(epd, product.name)


@router.delete("/epd/{epd_id}")
async def delete_epd(
    epd_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    epd = await _get_epd(epd_id, session, current_user)
    if epd.status != EPDStatus.DRAFT.value:
        raise HTTPException(
            status_code=409,
            detail="Only draft EPDs can be deleted — the workflow record is "
            "part of the audit trail once review starts",
        )
    accesses = (
        (
            await session.execute(
                select(VerifierAccess).where(VerifierAccess.epd_project_id == epd.id)
            )
        )
        .scalars()
        .all()
    )
    for a in accesses:
        await session.delete(a)
    await session.delete(epd)
    await session.commit()
    return {"ok": True}


# ---------------------------------------------------------------- workflow


@router.post("/epd/{epd_id}/transition", response_model=EPDOut)
async def transition_epd(
    epd_id: UUID,
    data: EPDTransition,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    epd = await _get_epd(epd_id, session, current_user)
    product, footprint, _count, _hv = await _load_context(session, epd)
    old_status = epd.status
    try:
        epd_service.apply_transition(epd, data.status, footprint, product)
    except epd_service.EPDTransitionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    await AuditService.log(
        session,
        organization_id=current_user.organization_id,
        action=AuditAction.STATUS_CHANGE,
        resource_type="epd_project",
        resource_id=str(epd.id),
        description=f"EPD '{epd.name}': {old_status} → {epd.status}",
        user=current_user,
        details={"from": old_status, "to": epd.status},
    )
    await session.commit()
    await session.refresh(epd)
    return _epd_out(epd, product.name)


# ---------------------------------------------------------------- documents


async def _export_guard(
    epd: EPDProject,
    session: AsyncSession,
    current_user: User,
    entitlement: dict,
) -> tuple[Organization, Product, dict]:
    """Shared export path: needs a pinned footprint; gated like every other
    export (teaser 402, Report Pass year lock on the footprint's period)."""
    product, footprint, _count, _hv = await _load_context(session, epd)
    results, _frozen = _effective_results(epd, footprint, product)
    if results is None:
        raise HTTPException(
            status_code=422,
            detail="Pin a computed footprint to this EPD before exporting " "documents",
        )
    await require_report_generation(entitlement)
    if footprint is not None:
        period = await session.get(ReportingPeriod, footprint.reporting_period_id)
        ensure_period_year_licensed(entitlement, period)
    org = await session.get(Organization, current_user.organization_id)
    return org, product, results


@router.get("/epd/{epd_id}/export/pdf")
async def export_epd_pdf(
    epd_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    entitlement: Annotated[dict, Depends(get_entitlement)],
):
    """EN 15804-structured declaration PDF (existing reportlab lane)."""
    epd = await _get_epd(epd_id, session, current_user)
    org, product, results = await _export_guard(epd, session, current_user, entitlement)
    pdf = epd_service.build_epd_pdf(org, product, epd, results)
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in epd.name)[:60]
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="epd_{safe}.pdf"'},
    )


@router.get("/epd/{epd_id}/export/ilcd")
async def export_epd_ilcd(
    epd_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    entitlement: Annotated[dict, Depends(get_entitlement)],
):
    """ILCD+EPD digital dataset (XML) — the machine-readable EPD."""
    epd = await _get_epd(epd_id, session, current_user)
    org, product, results = await _export_guard(epd, session, current_user, entitlement)
    xml = epd_service.build_ilcd_epd_xml(org, product, epd, results)
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in epd.name)[:60]
    return Response(
        content=xml,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="epd_{safe}_ilcd.xml"'},
    )


# ---------------------------------------------------------------- verification


@router.post("/epd/{epd_id}/verifier-access")
async def invite_epd_verifier(
    epd_id: UUID,
    body: EPDVerifierInvite,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Invite the third-party verifier to this EPD project — the same
    token-gated read-only portal as corporate periods, scoped to one EPD."""
    _require_admin(current_user)
    epd = await _get_epd(epd_id, session, current_user)

    expires_at = None
    if body.expires_in_days is not None:
        if body.expires_in_days <= 0:
            raise HTTPException(status_code=400, detail="expires_in_days must be > 0")
        expires_at = datetime.utcnow() + timedelta(days=body.expires_in_days)

    access = VerifierAccess(
        organization_id=current_user.organization_id,
        epd_project_id=epd.id,
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
        description=(f"Invited verifier {access.verifier_email} to EPD '{epd.name}'"),
        user=current_user,
        details={"epd_project_id": str(epd.id)},
    )
    await session.refresh(access)
    return _access_out(access)


@router.get("/epd/{epd_id}/verifier-access")
async def list_epd_verifier_access(
    epd_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    epd = await _get_epd(epd_id, session, current_user)
    rows = (
        (
            await session.execute(
                select(VerifierAccess)
                .where(
                    VerifierAccess.epd_project_id == epd.id,
                    VerifierAccess.organization_id == current_user.organization_id,
                )
                .order_by(VerifierAccess.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [_access_out(a) for a in rows]


# ------------------------------------------------------- public portal (token)


@router.get("/verify/{token}/context")
async def verifier_context(
    token: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Tells the portal page which read-only surface this token unlocks."""
    access = await _resolve_token(token, session)
    return {"kind": "epd" if access.epd_project_id else "period"}


@router.get("/verify/{token}/epd")
async def verifier_epd(
    token: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """The verifier's read-only view of one EPD project: declaration
    metadata, frozen results, per-line derivations, readiness checklist."""
    access = await _resolve_token(token, session, touch=True)
    if access.epd_project_id is None:
        raise HTTPException(
            status_code=404, detail="This link is not an EPD verification link."
        )
    epd = await session.get(EPDProject, access.epd_project_id)
    if epd is None:
        raise HTTPException(status_code=404, detail="This verifier link is not valid.")
    org = await session.get(Organization, access.organization_id)
    product, footprint, input_count, _hv = await _load_context(session, epd)
    results, frozen = _effective_results(epd, footprint, product)
    return {
        "organization_name": org.name if org else "",
        "verifier_name": access.verifier_name,
        "epd": _epd_out(epd, product.name).model_dump(mode="json"),
        "results": results,
        "results_are_frozen": frozen,
        "checklist": epd_service.readiness_checklist(
            epd, product, footprint, input_count, True
        ),
        "read_only": True,
    }
