"""
CBAM (Carbon Border Adjustment Mechanism) API endpoints.

Implements EU CBAM requirements for:
- Installation management (non-EU production facilities)
- Import tracking and embedded emissions calculation
- Quarterly transitional reports (2024-2025) — read-only history; the
  transitional period ended 31 Dec 2025
- Annual declarations with certificate requirements (2026+), due 30 Sep
  of the following year (Omnibus, Reg. (EU) 2025/2083)
- Public 50 t screening + EU ETS price reference
"""

import secrets
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.api.auth import get_current_user
from app.config import settings
from app.database import get_session
from app.models.core import Organization, User
from app.rate_limit import limiter
from app.models.cbam import (
    CBAMInstallation,
    CBAMInstallationStatus,
    CBAMImport,
    CBAMQuarterlyReport,
    CBAMReportStatus,
    CBAMAnnualDeclaration,
    CBAMDataRequest,
    CBAMSupplierEmission,
    CBAMDefaultValue,
    EUETSPrice,
    CBAMSector,
    CBAMCalculationMethod,
)
from app.models.core import UserRole
from app.services.email import email_service
from app.services.cbam_calculator import CBAMCalculator
from app.services.cbam_declaration import build_annual_declaration_draft
from app.services.cbam_screening import (
    DEFAULT_VALUE_MARKUP_2026,
    SECTOR_DEFAULT_INTENSITY,
    screen_imports,
)
from app.services import ets_price as ets_price_service
from app.data.cbam_data import CBAM_PRODUCTS, get_sector_for_cn_code

router = APIRouter()
calculator = CBAMCalculator()


# ============================================================================
# Schemas
# ============================================================================


# Installation Schemas
class CBAMInstallationCreate(BaseModel):
    """Create CBAM installation request."""

    name: str
    country_code: str = Field(..., min_length=2, max_length=2)
    address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    sectors: List[str] = []
    verification_status: str = "pending"


class CBAMInstallationUpdate(BaseModel):
    """Update CBAM installation request."""

    name: Optional[str] = None
    country_code: Optional[str] = None
    address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    sectors: Optional[List[str]] = None
    verification_status: Optional[str] = None


class CBAMInstallationResponse(BaseModel):
    """CBAM installation response."""

    id: str
    organization_id: str
    name: str
    country_code: str
    address: Optional[str]
    contact_name: Optional[str]
    contact_email: Optional[str]
    sectors: List[str]
    verification_status: str
    created_at: datetime
    updated_at: datetime


# Import Schemas
class CBAMImportCreate(BaseModel):
    """Create CBAM import request.

    Installation is optional; when omitted, `origin_country` (ISO alpha-2)
    is required to determine the country of production.
    """

    installation_id: Optional[str] = None
    cn_code: str = Field(..., min_length=4, max_length=20)
    product_description: Optional[str] = None
    import_date: date
    mass_tonnes: Decimal = Field(..., gt=0)
    origin_country: Optional[str] = Field(default=None, min_length=2, max_length=2)
    customs_procedure: Optional[str] = None
    customs_declaration_number: Optional[str] = None
    actual_direct_see: Optional[Decimal] = None
    actual_indirect_see: Optional[Decimal] = None
    electricity_consumption_mwh: Optional[Decimal] = None
    foreign_carbon_price_eur: Optional[Decimal] = None
    # Note: the model stores the carbon price in EUR only
    # (carbon_price_paid_eur); a currency column does not exist yet, so the
    # currency hint is accepted but not persisted.
    foreign_carbon_price_currency: Optional[str] = None


class CBAMImportUpdate(BaseModel):
    """Update CBAM import request."""

    cn_code: Optional[str] = None
    product_description: Optional[str] = None
    import_date: Optional[date] = None
    mass_tonnes: Optional[Decimal] = None
    actual_direct_see: Optional[Decimal] = None
    actual_indirect_see: Optional[Decimal] = None
    electricity_consumption_mwh: Optional[Decimal] = None
    foreign_carbon_price_eur: Optional[Decimal] = None


class CBAMImportResponse(BaseModel):
    """CBAM import response."""

    id: str
    organization_id: str
    installation_id: str
    cn_code: str
    sector: str
    product_description: Optional[str]
    import_date: date
    origin_country: Optional[str]
    mass_tonnes: Decimal
    mass_kg: Decimal
    calculation_method: str
    direct_see: Decimal
    indirect_see: Decimal
    total_see: Decimal
    direct_emissions_tco2e: Decimal
    indirect_emissions_tco2e: Decimal
    total_emissions_tco2e: Decimal
    foreign_carbon_price_eur: Optional[Decimal]
    created_at: datetime


# Report Schemas
class CBAMQuarterlyReportResponse(BaseModel):
    """CBAM quarterly report response."""

    id: str
    organization_id: str
    year: int
    quarter: int
    status: str
    total_imports: int
    total_mass_tonnes: Decimal
    total_emissions_tco2e: Decimal
    by_sector: dict
    by_cn_code: dict
    submitted_at: Optional[datetime]
    created_at: datetime


class CBAMAnnualDeclarationResponse(BaseModel):
    """CBAM annual declaration response."""

    id: str
    organization_id: str
    year: int
    status: str
    total_imports: int
    total_mass_tonnes: Decimal
    gross_emissions_tco2e: Decimal
    deductions_tco2e: Decimal
    net_emissions_tco2e: Decimal
    certificates_required: Decimal
    estimated_cost_eur: Decimal
    by_sector: dict
    submitted_at: Optional[datetime]
    created_at: datetime


class CBAMDeclarationLineResponse(BaseModel):
    """One import line of the annual declaration draft."""

    import_id: str
    import_date: date
    cn_code: str
    sector: str
    product_description: Optional[str]
    origin_country: Optional[str]
    mass_tonnes: Decimal
    intensity_source: str  # "actual" | "actual (supplier)" | "default"
    intensity_source_detail: str
    see_tco2e_per_tonne: Decimal
    markup_pct: Decimal
    emissions_tco2e: Decimal
    deduction_tco2e: Decimal
    deduction_eur: Decimal
    net_emissions_tco2e: Decimal
    estimated_cost_eur: Decimal


class CBAMDataQualitySummary(BaseModel):
    """How much of the declaration rests on default vs actual values."""

    total_lines: int
    actual_lines: int
    # Of the actual lines, how many come from supplier-portal submissions
    supplier_lines: int = 0
    default_lines: int
    default_share_pct: float
    lines_without_db_default: int


class CBAMAnnualDeclarationDetailResponse(CBAMAnnualDeclarationResponse):
    """Full annual declaration draft package for the review screen."""

    submission_deadline: date
    deductions_eur: Decimal
    ets_price_eur: Decimal
    default_value_markup_pct: Decimal
    by_cn_code: dict
    lines: List[CBAMDeclarationLineResponse]
    data_quality: CBAMDataQualitySummary
    assumptions: List[str]
    # True when the imports register changed after the draft was generated
    # (regenerate to refresh the stored totals).
    stale: bool = False


class CBAMDeclarationStatusUpdate(BaseModel):
    """Move an annual declaration between draft and ready."""

    status: str = Field(..., min_length=1, max_length=20)


# CN Code Search
class CNCodeResponse(BaseModel):
    """CN code search result."""

    cn_code: str
    description: str
    sector: str


class EmissionCalculationRequest(BaseModel):
    """Request for embedded emissions calculation preview."""

    cn_code: str
    mass_tonnes: Decimal
    country_code: str
    actual_direct_see: Optional[Decimal] = None
    actual_indirect_see: Optional[Decimal] = None
    electricity_consumption_mwh: Optional[Decimal] = None
    foreign_carbon_price_eur: Optional[Decimal] = None


# Screening (public exemption checker)
class CBAMScreenItem(BaseModel):
    """One annual import line for the public screening checker."""

    cn_code_or_sector: str = Field(..., min_length=1, max_length=50)
    mass_kg: Decimal = Field(..., gt=0)
    origin_country: Optional[str] = Field(default=None, max_length=100)


class CBAMScreenRequest(BaseModel):
    """Public screening payload."""

    items: List[CBAMScreenItem] = Field(..., min_length=1, max_length=100)
    ets_price_eur: Optional[Decimal] = Field(default=None, gt=0)


# ETS price schemas
class ETSPriceUpsert(BaseModel):
    """Manual EU ETS price entry (admin)."""

    price_date: date
    price_eur: Decimal = Field(..., gt=0)
    source: str = Field(default="manual admin entry", max_length=100)
    source_url: Optional[str] = Field(default=None, max_length=500)


class ETSPriceResponse(BaseModel):
    """Latest EU ETS price with provenance."""

    price_eur: Decimal
    price_date: Optional[date]
    source: str
    is_fallback: bool
    assumption: Optional[str] = None


# Supplier portal (Phase 3) schemas
class CBAMDataRequestCreate(BaseModel):
    """Create a supplier data request (magic-link email)."""

    installation_id: str
    supplier_email: EmailStr
    message: Optional[str] = Field(default=None, max_length=2000)


class CBAMSupplierEmissionRowInput(BaseModel):
    """One per-CN-code SEE row submitted by the supplier."""

    cn_code: str = Field(..., min_length=4, max_length=10)
    direct_see_tco2e_per_t: Decimal = Field(..., ge=0)
    indirect_see_tco2e_per_t: Optional[Decimal] = Field(default=None, ge=0)
    production_period_start: date
    production_period_end: date
    verifier_name: Optional[str] = Field(default=None, max_length=255)
    verified: bool = False


class CBAMSupplierSubmission(BaseModel):
    """Public submission payload (replaces any previously submitted rows)."""

    rows: List[CBAMSupplierEmissionRowInput] = Field(..., min_length=1, max_length=100)


class CBAMSupplierEmissionRowResponse(BaseModel):
    """A stored supplier emission row."""

    id: str
    cn_code: str
    direct_see_tco2e_per_t: Decimal
    indirect_see_tco2e_per_t: Optional[Decimal]
    production_period_start: date
    production_period_end: date
    verifier_name: Optional[str]
    verified: bool


class CBAMDataRequestResponse(BaseModel):
    """Supplier data request (importer side, org-scoped)."""

    id: str
    organization_id: str
    installation_id: str
    installation_name: str
    installation_country: str
    supplier_email: str
    token: str
    status: str  # pending | submitted | expired
    message: Optional[str]
    created_at: datetime
    submitted_at: Optional[datetime]
    expires_at: datetime
    supplier_portal_url: str
    rows: List[CBAMSupplierEmissionRowResponse]


class CBAMSupplierRequestContext(BaseModel):
    """Public request context shown to the supplier (no auth)."""

    importer_org_name: str
    installation_name: str
    installation_country: str
    status: str
    message: Optional[str]
    created_at: datetime
    submitted_at: Optional[datetime]
    expires_at: datetime
    rows: List[CBAMSupplierEmissionRowResponse]


# ============================================================================
# Helper Functions
# ============================================================================


def _json_safe(value):
    """Recursively convert Decimals (and sets) for JSON column storage."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return value


def installation_to_response(inst: CBAMInstallation) -> CBAMInstallationResponse:
    """Convert installation model to response."""
    # Model uses single sector, API expects list
    sectors = [inst.sector.value] if inst.sector else []
    return CBAMInstallationResponse(
        id=str(inst.id),
        organization_id=str(inst.organization_id),
        name=inst.name,
        country_code=inst.country_code,
        address=inst.address,
        contact_name=inst.operator_contact_name,
        contact_email=inst.operator_contact_email,
        sectors=sectors,
        verification_status=(
            inst.verification_status.value if inst.verification_status else "pending"
        ),
        created_at=inst.created_at,
        updated_at=inst.updated_at or inst.created_at,
    )


def import_to_response(imp: CBAMImport) -> CBAMImportResponse:
    """Convert import model to response."""
    # Calculate Specific Embedded Emissions (SEE) from model data
    mass = imp.net_mass_tonnes or Decimal("1")  # Avoid division by zero
    direct_emissions = imp.direct_emissions_tco2e or Decimal("0")
    indirect_emissions = imp.indirect_emissions_tco2e or Decimal("0")
    total_emissions = imp.total_embedded_emissions_tco2e or Decimal("0")

    return CBAMImportResponse(
        id=str(imp.id),
        organization_id=str(imp.organization_id),
        installation_id=str(imp.installation_id) if imp.installation_id else "",
        cn_code=imp.cn_code,
        sector=imp.sector.value if imp.sector else "unknown",
        product_description=imp.product_description,
        import_date=imp.import_date,
        origin_country=imp.origin_country,
        mass_tonnes=imp.net_mass_tonnes,
        mass_kg=imp.net_mass_kg,
        calculation_method=(
            imp.calculation_method.value if imp.calculation_method else "default"
        ),
        direct_see=direct_emissions / mass if mass > 0 else Decimal("0"),
        indirect_see=indirect_emissions / mass if mass > 0 else Decimal("0"),
        total_see=imp.specific_embedded_emissions
        or (total_emissions / mass if mass > 0 else Decimal("0")),
        direct_emissions_tco2e=direct_emissions,
        indirect_emissions_tco2e=indirect_emissions,
        total_emissions_tco2e=total_emissions,
        # Model field is carbon_price_paid_eur; the API keeps the
        # foreign_carbon_price_eur name for backwards compatibility.
        foreign_carbon_price_eur=imp.carbon_price_paid_eur,
        created_at=imp.created_at,
    )


# ============================================================================
# Installation Endpoints
# ============================================================================


@router.get("/installations", response_model=List[CBAMInstallationResponse])
async def list_installations(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    country_code: Optional[str] = None,
    sector: Optional[str] = None,
):
    """List all CBAM installations for the organization."""
    query = select(CBAMInstallation).where(
        CBAMInstallation.organization_id == current_user.organization_id
    )

    if country_code:
        query = query.where(CBAMInstallation.country_code == country_code.upper())

    # Model stores a single sector enum (the API response exposes it as a
    # one-element list for backwards compatibility).
    if sector:
        try:
            query = query.where(CBAMInstallation.sector == CBAMSector(sector.lower()))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown sector: {sector}")

    result = await session.execute(query.order_by(CBAMInstallation.name))
    installations = result.scalars().all()

    return [installation_to_response(inst) for inst in installations]


@router.post("/installations", response_model=CBAMInstallationResponse)
async def create_installation(
    data: CBAMInstallationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create a new CBAM installation (non-EU production facility)."""
    # Map request fields to model fields
    # API uses sectors list, model uses single sector enum
    sector = CBAMSector(data.sectors[0].lower()) if data.sectors else CBAMSector.CEMENT

    installation = CBAMInstallation(
        id=uuid4(),
        organization_id=current_user.organization_id,
        name=data.name,
        country_code=data.country_code.upper(),
        address=data.address or "Not specified",
        operator_name=data.name,  # Use installation name as operator name
        operator_contact_name=data.contact_name,
        operator_contact_email=data.contact_email,
        sector=sector,
        verification_status=CBAMInstallationStatus(data.verification_status),
    )

    session.add(installation)
    await session.commit()
    await session.refresh(installation)

    return installation_to_response(installation)


@router.get("/installations/{installation_id}", response_model=CBAMInstallationResponse)
async def get_installation(
    installation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get a specific CBAM installation."""
    result = await session.execute(
        select(CBAMInstallation).where(
            CBAMInstallation.id == installation_id,
            CBAMInstallation.organization_id == current_user.organization_id,
        )
    )
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    return installation_to_response(installation)


@router.put("/installations/{installation_id}", response_model=CBAMInstallationResponse)
async def update_installation(
    installation_id: UUID,
    data: CBAMInstallationUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Update a CBAM installation."""
    result = await session.execute(
        select(CBAMInstallation).where(
            CBAMInstallation.id == installation_id,
            CBAMInstallation.organization_id == current_user.organization_id,
        )
    )
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    # Update fields
    if data.name is not None:
        installation.name = data.name
        installation.operator_name = data.name  # Keep in sync
    if data.country_code is not None:
        installation.country_code = data.country_code.upper()
    if data.address is not None:
        installation.address = data.address
    if data.contact_name is not None:
        installation.operator_contact_name = data.contact_name
    if data.contact_email is not None:
        installation.operator_contact_email = data.contact_email
    if data.sectors is not None and len(data.sectors) > 0:
        installation.sector = CBAMSector(data.sectors[0].lower())
    if data.verification_status is not None:
        installation.verification_status = CBAMInstallationStatus(
            data.verification_status
        )

    installation.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(installation)

    return installation_to_response(installation)


@router.delete("/installations/{installation_id}")
async def delete_installation(
    installation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Delete a CBAM installation."""
    result = await session.execute(
        select(CBAMInstallation).where(
            CBAMInstallation.id == installation_id,
            CBAMInstallation.organization_id == current_user.organization_id,
        )
    )
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    # Check for linked imports
    imports_result = await session.execute(
        select(func.count(CBAMImport.id)).where(
            CBAMImport.installation_id == installation_id
        )
    )
    import_count = imports_result.scalar() or 0

    if import_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete installation with {import_count} linked imports",
        )

    await session.delete(installation)
    await session.commit()

    return {"message": "Installation deleted successfully"}


# ============================================================================
# Supplier Data Requests (Phase 3 — supplier portal)
# ============================================================================


def _supplier_portal_url(token: str) -> str:
    """Public magic-link URL the supplier opens (no account needed)."""
    # Other transactional emails build links from settings.frontend_url
    # (e.g. password reset / invitations) — same base here.
    return f"{settings.frontend_url}/supplier-data/{token}"


def _supplier_rows_to_response(
    rows: list[CBAMSupplierEmission],
) -> list[CBAMSupplierEmissionRowResponse]:
    return [
        CBAMSupplierEmissionRowResponse(
            id=str(r.id),
            cn_code=r.cn_code,
            direct_see_tco2e_per_t=r.direct_see_tco2e_per_t,
            indirect_see_tco2e_per_t=r.indirect_see_tco2e_per_t,
            production_period_start=r.production_period_start,
            production_period_end=r.production_period_end,
            verifier_name=r.verifier_name,
            verified=r.verified,
        )
        for r in rows
    ]


def _effective_request_status(req: CBAMDataRequest) -> str:
    """Pending requests past their expiry read as expired (lazy expiry)."""
    if req.status == "pending" and req.expires_at < datetime.utcnow():
        return "expired"
    return req.status


async def _load_request_rows(
    session: AsyncSession, request_id: UUID
) -> list[CBAMSupplierEmission]:
    result = await session.execute(
        select(CBAMSupplierEmission)
        .where(CBAMSupplierEmission.request_id == request_id)
        .order_by(CBAMSupplierEmission.cn_code)
    )
    return list(result.scalars().all())


async def _data_request_to_response(
    session: AsyncSession, req: CBAMDataRequest, installation: CBAMInstallation
) -> CBAMDataRequestResponse:
    rows = await _load_request_rows(session, req.id)
    return CBAMDataRequestResponse(
        id=str(req.id),
        organization_id=str(req.organization_id),
        installation_id=str(req.installation_id),
        installation_name=installation.name,
        installation_country=installation.country_code,
        supplier_email=req.supplier_email,
        token=req.token,
        status=_effective_request_status(req),
        message=req.message,
        created_at=req.created_at,
        submitted_at=req.submitted_at,
        expires_at=req.expires_at,
        supplier_portal_url=_supplier_portal_url(req.token),
        rows=_supplier_rows_to_response(rows),
    )


async def _get_org_data_request(
    session: AsyncSession, request_id: UUID, organization_id: UUID
) -> tuple[CBAMDataRequest, CBAMInstallation]:
    result = await session.execute(
        select(CBAMDataRequest, CBAMInstallation)
        .join(CBAMInstallation, CBAMInstallation.id == CBAMDataRequest.installation_id)
        .where(
            CBAMDataRequest.id == request_id,
            CBAMDataRequest.organization_id == organization_id,
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Data request not found")
    return row[0], row[1]


@router.post("/data-requests", response_model=CBAMDataRequestResponse)
async def create_data_request(
    data: CBAMDataRequestCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Request actual embedded-emissions data from a supplier.

    Creates a tokenized magic-link request for one installation and emails
    the supplier a public form URL ({frontend}/supplier-data/{token}, valid
    60 days, no account needed).
    """
    result = await session.execute(
        select(CBAMInstallation).where(
            CBAMInstallation.id == UUID(data.installation_id),
            CBAMInstallation.organization_id == current_user.organization_id,
        )
    )
    installation = result.scalar_one_or_none()
    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    org_result = await session.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = org_result.scalar_one_or_none()
    org_name = org.name if org else "An EU importer"

    req = CBAMDataRequest(
        id=uuid4(),
        organization_id=current_user.organization_id,
        installation_id=installation.id,
        supplier_email=data.supplier_email.lower(),
        token=secrets.token_urlsafe(32),
        status="pending",
        requested_by=current_user.id,
        message=data.message,
        expires_at=datetime.utcnow() + timedelta(days=60),
    )
    session.add(req)
    await session.commit()
    await session.refresh(req)

    email_service.send_cbam_data_request_email(
        to_email=req.supplier_email,
        importer_org_name=org_name,
        installation_name=installation.name,
        portal_url=_supplier_portal_url(req.token),
        message=req.message,
    )

    return await _data_request_to_response(session, req, installation)


@router.get("/data-requests", response_model=List[CBAMDataRequestResponse])
async def list_data_requests(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    status: Optional[str] = None,
    installation_id: Optional[UUID] = None,
):
    """List the organization's supplier data requests (newest first)."""
    query = (
        select(CBAMDataRequest, CBAMInstallation)
        .join(CBAMInstallation, CBAMInstallation.id == CBAMDataRequest.installation_id)
        .where(CBAMDataRequest.organization_id == current_user.organization_id)
    )
    if installation_id:
        query = query.where(CBAMDataRequest.installation_id == installation_id)

    result = await session.execute(query.order_by(CBAMDataRequest.created_at.desc()))
    pairs = result.all()

    responses = [
        await _data_request_to_response(session, req, inst) for req, inst in pairs
    ]
    if status:
        responses = [r for r in responses if r.status == status.strip().lower()]
    return responses


@router.post(
    "/data-requests/{request_id}/remind", response_model=CBAMDataRequestResponse
)
async def remind_data_request(
    request_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Re-send the data-request email to the supplier (pending requests only)."""
    req, installation = await _get_org_data_request(
        session, request_id, current_user.organization_id
    )

    effective = _effective_request_status(req)
    if effective != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot remind a {effective} request — only pending ones",
        )

    org_result = await session.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = org_result.scalar_one_or_none()

    email_service.send_cbam_data_request_email(
        to_email=req.supplier_email,
        importer_org_name=org.name if org else "An EU importer",
        installation_name=installation.name,
        portal_url=_supplier_portal_url(req.token),
        message=req.message,
        is_reminder=True,
    )

    return await _data_request_to_response(session, req, installation)


async def _get_public_request(
    session: AsyncSession, token: str
) -> tuple[CBAMDataRequest, CBAMInstallation, Organization]:
    """Resolve a magic-link token; 404 unknown, 410 expired (lazily marked)."""
    result = await session.execute(
        select(CBAMDataRequest, CBAMInstallation, Organization)
        .join(CBAMInstallation, CBAMInstallation.id == CBAMDataRequest.installation_id)
        .join(Organization, Organization.id == CBAMDataRequest.organization_id)
        .where(CBAMDataRequest.token == token)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Unknown or revoked link")

    req, installation, org = row[0], row[1], row[2]
    if _effective_request_status(req) == "expired":
        if req.status != "expired":
            req.status = "expired"
            await session.commit()
        raise HTTPException(
            status_code=410,
            detail=(
                "This data request has expired. Ask the importer to send "
                "a new request."
            ),
        )
    return req, installation, org


@router.get("/supplier-data/{token}", response_model=CBAMSupplierRequestContext)
@limiter.limit(settings.rate_limit_default)
async def get_supplier_data_request(
    request: Request,
    token: str,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
):
    """
    PUBLIC: context for the supplier magic-link form (no auth, rate-limited).

    Shows who is asking (importer org), which installation the data is for,
    the request status and any rows already submitted (for revision).
    """
    req, installation, org = await _get_public_request(session, token)
    rows = await _load_request_rows(session, req.id)

    return CBAMSupplierRequestContext(
        importer_org_name=org.name,
        installation_name=installation.name,
        installation_country=installation.country_code,
        status=req.status,
        message=req.message,
        created_at=req.created_at,
        submitted_at=req.submitted_at,
        expires_at=req.expires_at,
        rows=_supplier_rows_to_response(rows),
    )


@router.post("/supplier-data/{token}", response_model=CBAMSupplierRequestContext)
@limiter.limit(settings.rate_limit_default)
async def submit_supplier_data(
    request: Request,
    token: str,
    payload: CBAMSupplierSubmission,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
):
    """
    PUBLIC: submit per-CN-code actual emissions rows (no auth, rate-limited).

    Idempotent: re-submission replaces the previously submitted rows while
    the request is not expired. Marks the request `submitted`.
    """
    req, installation, org = await _get_public_request(session, token)

    for row in payload.rows:
        if row.production_period_end < row.production_period_start:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Row for CN {row.cn_code}: production period end is "
                    "before its start"
                ),
            )
        if not any(ch.isdigit() for ch in row.cn_code):
            raise HTTPException(
                status_code=422,
                detail=f"Row CN code '{row.cn_code}' must contain digits",
            )

    # Replace previously submitted rows wholesale (idempotent re-submission).
    existing = await _load_request_rows(session, req.id)
    for old in existing:
        await session.delete(old)

    for row in payload.rows:
        session.add(
            CBAMSupplierEmission(
                id=uuid4(),
                request_id=req.id,
                organization_id=req.organization_id,
                installation_id=req.installation_id,
                cn_code=row.cn_code.strip(),
                direct_see_tco2e_per_t=row.direct_see_tco2e_per_t,
                indirect_see_tco2e_per_t=row.indirect_see_tco2e_per_t,
                production_period_start=row.production_period_start,
                production_period_end=row.production_period_end,
                verifier_name=row.verifier_name,
                verified=row.verified,
            )
        )

    req.status = "submitted"
    req.submitted_at = datetime.utcnow()
    await session.commit()
    await session.refresh(req)

    rows = await _load_request_rows(session, req.id)
    return CBAMSupplierRequestContext(
        importer_org_name=org.name,
        installation_name=installation.name,
        installation_country=installation.country_code,
        status=req.status,
        message=req.message,
        created_at=req.created_at,
        submitted_at=req.submitted_at,
        expires_at=req.expires_at,
        rows=_supplier_rows_to_response(rows),
    )


# ============================================================================
# Import Endpoints
# ============================================================================


@router.get("/imports", response_model=List[CBAMImportResponse])
async def list_imports(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    installation_id: Optional[UUID] = None,
    cn_code: Optional[str] = None,
    sector: Optional[str] = None,
    year: Optional[int] = None,
    quarter: Optional[int] = None,
):
    """List CBAM imports with optional filters."""
    query = select(CBAMImport).where(
        CBAMImport.organization_id == current_user.organization_id
    )

    if installation_id:
        query = query.where(CBAMImport.installation_id == installation_id)
    if cn_code:
        query = query.where(CBAMImport.cn_code == cn_code)
    if sector:
        query = query.where(CBAMImport.sector == CBAMSector(sector.lower()))
    if year:
        query = query.where(func.extract("year", CBAMImport.import_date) == year)
    if quarter:
        month_start = (quarter - 1) * 3 + 1
        month_end = quarter * 3
        query = query.where(
            func.extract("month", CBAMImport.import_date).between(
                month_start, month_end
            )
        )

    result = await session.execute(query.order_by(CBAMImport.import_date.desc()))
    imports = result.scalars().all()

    return [import_to_response(imp) for imp in imports]


@router.post("/imports", response_model=CBAMImportResponse)
async def create_import(
    data: CBAMImportCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create a new CBAM import record with automatic emissions calculation."""
    # Installation is optional; when provided it must belong to the org and
    # its country is used as the origin country.
    installation = None
    if data.installation_id:
        result = await session.execute(
            select(CBAMInstallation).where(
                CBAMInstallation.id == UUID(data.installation_id),
                CBAMInstallation.organization_id == current_user.organization_id,
            )
        )
        installation = result.scalar_one_or_none()

        if not installation:
            raise HTTPException(status_code=404, detail="Installation not found")

    origin_country = (
        installation.country_code
        if installation
        else (data.origin_country or "").upper()
    )
    if not origin_country:
        raise HTTPException(
            status_code=422,
            detail="origin_country is required when no installation is linked",
        )

    # Calculate embedded emissions
    calculation = calculator.calculate_embedded_emissions(
        cn_code=data.cn_code,
        mass_tonnes=data.mass_tonnes,
        country_code=origin_country,
        actual_direct_see=data.actual_direct_see,
        actual_indirect_see=data.actual_indirect_see,
        electricity_consumption_mwh=data.electricity_consumption_mwh,
    )

    # Determine sector from CN code
    sector_str = get_sector_for_cn_code(data.cn_code)
    sector = CBAMSector(sector_str) if sector_str else CBAMSector.OTHER

    # Create import record
    mass_tonnes = data.mass_tonnes
    mass_kg = mass_tonnes * 1000
    direct_emissions = calculation["direct_emissions_tco2e"]
    indirect_emissions = calculation.get("indirect_emissions_tco2e", Decimal("0"))
    total_emissions = calculation["total_emissions_tco2e"]
    specific_emissions = (
        total_emissions / mass_tonnes if mass_tonnes > 0 else Decimal("0")
    )

    cbam_import = CBAMImport(
        id=uuid4(),
        organization_id=current_user.organization_id,
        installation_id=installation.id if installation else None,
        cn_code=data.cn_code,
        sector=sector,
        product_description=data.product_description or f"Product {data.cn_code}",
        import_date=data.import_date,
        origin_country=origin_country,
        net_mass_kg=mass_kg,
        net_mass_tonnes=mass_tonnes,
        calculation_method=(
            CBAMCalculationMethod.ACTUAL
            if data.actual_direct_see
            else CBAMCalculationMethod.DEFAULT_VALUE
        ),
        default_value_used=data.actual_direct_see is None,
        direct_emissions_tco2e=direct_emissions,
        indirect_emissions_tco2e=indirect_emissions,
        total_embedded_emissions_tco2e=total_emissions,
        specific_embedded_emissions=specific_emissions,
        net_emissions_tco2e=total_emissions,  # No deductions applied yet
        customs_procedure=data.customs_procedure,
        customs_entry_number=data.customs_declaration_number,
        # Model field is carbon_price_paid_eur (the request keeps the old
        # foreign_carbon_price_eur name); currency is not persisted — no
        # column exists yet.
        carbon_price_paid_eur=data.foreign_carbon_price_eur,
        created_by=current_user.id,
    )

    session.add(cbam_import)
    await session.commit()
    await session.refresh(cbam_import)

    return import_to_response(cbam_import)


@router.get("/imports/{import_id}", response_model=CBAMImportResponse)
async def get_import(
    import_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get a specific CBAM import."""
    result = await session.execute(
        select(CBAMImport).where(
            CBAMImport.id == import_id,
            CBAMImport.organization_id == current_user.organization_id,
        )
    )
    cbam_import = result.scalar_one_or_none()

    if not cbam_import:
        raise HTTPException(status_code=404, detail="Import not found")

    return import_to_response(cbam_import)


@router.delete("/imports/{import_id}")
async def delete_import(
    import_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Delete a CBAM import."""
    result = await session.execute(
        select(CBAMImport).where(
            CBAMImport.id == import_id,
            CBAMImport.organization_id == current_user.organization_id,
        )
    )
    cbam_import = result.scalar_one_or_none()

    if not cbam_import:
        raise HTTPException(status_code=404, detail="Import not found")

    await session.delete(cbam_import)
    await session.commit()

    return {"message": "Import deleted successfully"}


# ============================================================================
# Calculation Preview Endpoint
# ============================================================================


@router.post("/calculate-emissions")
async def calculate_emissions_preview(
    data: EmissionCalculationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Preview embedded emissions calculation without creating a record.

    Useful for importers to estimate emissions before recording actual imports.
    """
    # Get current EU ETS price (would normally come from database)
    eu_ets_price = Decimal("80")  # Default

    calculation = calculator.calculate_import_full(
        cn_code=data.cn_code,
        mass_tonnes=data.mass_tonnes,
        country_code=data.country_code,
        actual_direct_see=data.actual_direct_see,
        actual_indirect_see=data.actual_indirect_see,
        electricity_consumption_mwh=data.electricity_consumption_mwh,
        foreign_carbon_price_eur=data.foreign_carbon_price_eur,
        eu_ets_price_eur=eu_ets_price,
        is_definitive_phase=date.today().year >= 2026,
    )

    return calculation


# ============================================================================
# Public Screening Endpoint (50 t exemption checker)
# ============================================================================


@router.post("/screen")
@limiter.limit(settings.rate_limit_default)
async def screen_cbam_exposure(
    request: Request,
    payload: CBAMScreenRequest,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
):
    """
    PUBLIC CBAM screening (no auth, rate-limited).

    Checks a basket of annual import lines against the Omnibus 50 t de
    minimis threshold and estimates 2026 embedded emissions and certificate
    cost. Every simplification is returned in `assumptions`.
    """
    extra_assumptions: list[str] = []

    if payload.ets_price_eur is not None:
        ets_price = payload.ets_price_eur
    else:
        result = await session.execute(
            select(EUETSPrice).order_by(EUETSPrice.price_date.desc()).limit(1)
        )
        latest = result.scalars().first()
        if latest:
            ets_price = latest.price_eur
            extra_assumptions.append(
                f"ETS price of €{float(latest.price_eur):,.2f}/tCO2e taken from "
                f"{latest.price_date.isoformat()} ({latest.source})."
            )
        else:
            ets_price = ets_price_service.FALLBACK_ETS_PRICE_EUR
            extra_assumptions.append(ets_price_service.FALLBACK_ASSUMPTION)

    # Load active default values (per CN x origin country) so screening
    # prefers DB values over the sector representative constants. The pure
    # function receives them as plain dicts.
    dv_result = await session.execute(
        select(CBAMDefaultValue).where(CBAMDefaultValue.is_active == True)  # noqa: E712
    )
    default_values = [
        {
            "cn_code": dv.cn_code,
            "country_code": dv.country_code,
            "total_see": dv.total_see,
            "source": dv.source,
        }
        for dv in dv_result.scalars().all()
    ]

    return screen_imports(
        [item.model_dump() for item in payload.items],
        ets_price,
        extra_assumptions=extra_assumptions,
        default_values=default_values or None,
    )


@router.get("/screen-defaults")
async def get_screen_defaults(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Reference values used for certificate-cost estimates.

    Returns the current ETS price (latest DB row, or the €75 fallback), the
    2026 default-value markup and the representative sector intensities so
    clients can compute per-import estimated certificate costs.
    """
    latest = await ets_price_service.get_latest_price(session)
    if latest:
        price = latest.price_eur
        price_date = latest.price_date.isoformat()
        source = latest.source
        is_fallback = False
    else:
        price = ets_price_service.FALLBACK_ETS_PRICE_EUR
        price_date = None
        source = "fallback"
        is_fallback = True

    return {
        "ets_price_eur": float(price),
        "ets_price_date": price_date,
        "ets_price_source": source,
        "ets_price_is_fallback": is_fallback,
        "default_value_markup_pct": float(DEFAULT_VALUE_MARKUP_2026 * 100),
        "sector_default_intensities": {
            sector: float(value) for sector, value in SECTOR_DEFAULT_INTENSITY.items()
        },
        "assumptions": ([ets_price_service.FALLBACK_ASSUMPTION] if is_fallback else []),
    }


# ============================================================================
# EU ETS Price Endpoints
# ============================================================================


@router.get("/ets-price/latest", response_model=ETSPriceResponse)
async def get_latest_ets_price(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Latest EU ETS price (public).

    Returns the newest stored price, or the €75/tCO2e fallback with an
    explicit assumption string when no price has been stored yet.
    """
    latest = await ets_price_service.get_latest_price(session)
    if latest:
        return ETSPriceResponse(
            price_eur=latest.price_eur,
            price_date=latest.price_date,
            source=latest.source,
            is_fallback=False,
        )
    return ETSPriceResponse(
        price_eur=ets_price_service.FALLBACK_ETS_PRICE_EUR,
        price_date=None,
        source="fallback",
        is_fallback=True,
        assumption=ets_price_service.FALLBACK_ASSUMPTION,
    )


@router.post("/ets-price/refresh")
async def refresh_ets_price(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Trigger the EU ETS price fetch job (admin/super_admin only).

    Currently no reliable free public EUA price endpoint exists (see
    app/services/ets_price.py), so this reports that manual entry via
    PUT /api/cbam/ets-price is the supported path until a feed is wired.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=403, detail="Admin role required to refresh the ETS price"
        )

    row = await ets_price_service.fetch_latest(session)
    if row is None:
        return {
            "updated": False,
            "detail": (
                "No live public ETS price source is configured. Enter the "
                "weekly price manually via PUT /api/cbam/ets-price."
            ),
        }
    return {
        "updated": True,
        "price_eur": float(row.price_eur),
        "price_date": row.price_date.isoformat(),
        "source": row.source,
    }


@router.put("/ets-price", response_model=ETSPriceResponse)
async def upsert_ets_price(
    data: ETSPriceUpsert,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Manually record the EU ETS price for a date (admin/super_admin only).

    This is the supported admin path while no automated feed exists;
    upserts on price_date.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=403, detail="Admin role required to set the ETS price"
        )

    row = await ets_price_service.upsert_price(
        session,
        price_date=data.price_date,
        price_eur=data.price_eur,
        source=data.source,
        source_url=data.source_url,
    )
    return ETSPriceResponse(
        price_eur=row.price_eur,
        price_date=row.price_date,
        source=row.source,
        is_fallback=False,
    )


# ============================================================================
# CN Code Search Endpoint
# ============================================================================


@router.get("/cn-codes", response_model=List[CNCodeResponse])
async def search_cn_codes(
    query: str = Query(..., min_length=2),
    sector: Optional[str] = None,
    limit: int = Query(default=20, le=100),
):
    """
    Search for CN codes by code or description.

    CN codes are the EU Combined Nomenclature classification for products.
    """
    query_lower = query.lower()
    results = []

    for product in CBAM_PRODUCTS:
        cn_code = product["cn_code"]
        description = product["description"]
        prod_sector = product["sector"]

        # Filter by sector if specified
        if sector and prod_sector.lower() != sector.lower():
            continue

        # Match by CN code or description
        if query_lower in cn_code.lower() or query_lower in description.lower():
            results.append(
                CNCodeResponse(
                    cn_code=cn_code,
                    description=description,
                    sector=prod_sector,
                )
            )

        if len(results) >= limit:
            break

    return results


# ============================================================================
# Quarterly Report Endpoints
# ============================================================================


@router.get("/reports/quarterly", response_model=List[CBAMQuarterlyReportResponse])
async def list_quarterly_reports(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    year: Optional[int] = None,
):
    """List quarterly CBAM reports (read-only transitional-period history)."""
    query = select(CBAMQuarterlyReport).where(
        CBAMQuarterlyReport.organization_id == current_user.organization_id
    )

    if year:
        query = query.where(CBAMQuarterlyReport.reporting_year == year)

    result = await session.execute(
        query.order_by(
            CBAMQuarterlyReport.reporting_year.desc(),
            CBAMQuarterlyReport.reporting_quarter.desc(),
        )
    )
    reports = result.scalars().all()

    return [
        CBAMQuarterlyReportResponse(
            id=str(r.id),
            organization_id=str(r.organization_id),
            year=r.reporting_year,
            quarter=r.reporting_quarter,
            status=r.status.value if r.status else "draft",
            total_imports=r.total_imports_count or 0,
            total_mass_tonnes=r.total_mass_tonnes or Decimal("0"),
            total_emissions_tco2e=r.total_embedded_emissions_tco2e or Decimal("0"),
            by_sector=r.by_sector or {},
            by_cn_code={},
            submitted_at=r.submitted_at,
            created_at=r.created_at,
        )
        for r in reports
    ]


_QUARTERLY_GONE_DETAIL = (
    "CBAM quarterly reports belonged to the transitional period, which "
    "ended 31 December 2025. The definitive regime (from 1 January 2026) "
    "uses annual declarations instead — see /api/cbam/reports/annual. "
    "Existing quarterly reports remain available read-only."
)


@router.post("/reports/quarterly/{year}/{quarter}", status_code=410)
async def generate_quarterly_report(
    year: int,
    quarter: int,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Retired: quarterly report generation (transitional period only).

    The transitional period ended 31 Dec 2025; quarterly reports can no
    longer be created or regenerated. GET endpoints remain for history.
    """
    raise HTTPException(status_code=410, detail=_QUARTERLY_GONE_DETAIL)


@router.post("/reports/quarterly/{year}/{quarter}/submit", status_code=410)
async def submit_quarterly_report(
    year: int,
    quarter: int,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Retired: quarterly report submission (transitional period only).

    The transitional period ended 31 Dec 2025; quarterly reports can no
    longer be submitted. GET endpoints remain for history.
    """
    raise HTTPException(status_code=410, detail=_QUARTERLY_GONE_DETAIL)


# ============================================================================
# Annual Declaration Endpoints
# ============================================================================


@router.get("/reports/annual", response_model=List[CBAMAnnualDeclarationResponse])
async def list_annual_declarations(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """List all annual CBAM declarations for the organization."""
    result = await session.execute(
        select(CBAMAnnualDeclaration)
        .where(CBAMAnnualDeclaration.organization_id == current_user.organization_id)
        .order_by(CBAMAnnualDeclaration.reporting_year.desc())
    )
    declarations = result.scalars().all()

    return [declaration_to_response(d) for d in declarations]


def declaration_to_response(
    d: CBAMAnnualDeclaration,
) -> CBAMAnnualDeclarationResponse:
    """Map the CBAMAnnualDeclaration model to the API response.

    The API keeps its historical field names (year, gross_emissions_tco2e,
    deductions_tco2e, estimated_cost_eur); the model stores these as
    reporting_year, total_embedded_emissions_tco2e,
    carbon_price_deductions_tco2e and total_certificate_cost_eur.
    """
    return CBAMAnnualDeclarationResponse(
        id=str(d.id),
        organization_id=str(d.organization_id),
        year=d.reporting_year,
        status=d.status.value if d.status else "draft",
        total_imports=d.total_imports_count or 0,
        total_mass_tonnes=d.total_mass_tonnes or Decimal("0"),
        gross_emissions_tco2e=d.total_embedded_emissions_tco2e or Decimal("0"),
        deductions_tco2e=d.carbon_price_deductions_tco2e or Decimal("0"),
        net_emissions_tco2e=d.net_emissions_tco2e or Decimal("0"),
        certificates_required=Decimal(d.certificates_required or 0),
        estimated_cost_eur=d.total_certificate_cost_eur or Decimal("0"),
        by_sector=d.by_sector or {},
        submitted_at=d.submitted_at,
        created_at=d.created_at,
    )


async def _load_declaration_inputs(
    session: AsyncSession, organization_id: UUID, year: int
) -> tuple[list[CBAMImport], list[dict], list[dict]]:
    """Load the year's imports, active default values and supplier actuals."""
    imports_result = await session.execute(
        select(CBAMImport)
        .where(
            CBAMImport.organization_id == organization_id,
            func.extract("year", CBAMImport.import_date) == year,
        )
        .order_by(CBAMImport.import_date)
    )
    imports = list(imports_result.scalars().all())

    dv_result = await session.execute(
        select(CBAMDefaultValue).where(CBAMDefaultValue.is_active == True)  # noqa: E712
    )
    default_values = [
        {
            "cn_code": dv.cn_code,
            "country_code": dv.country_code,
            "total_see": dv.total_see,
            "source": dv.source,
        }
        for dv in dv_result.scalars().all()
    ]

    # Supplier-portal actuals (submitted magic-link rows) — preferred over
    # defaults when matching an import's installation + CN prefix. Rows only
    # exist after submission, so no status filter is needed.
    se_result = await session.execute(
        select(CBAMSupplierEmission, CBAMInstallation.name)
        .join(
            CBAMInstallation,
            CBAMInstallation.id == CBAMSupplierEmission.installation_id,
        )
        .where(CBAMSupplierEmission.organization_id == organization_id)
    )
    supplier_emissions = [
        {
            "installation_id": str(se.installation_id),
            "installation_name": name,
            "cn_code": se.cn_code,
            "direct_see": se.direct_see_tco2e_per_t,
            "indirect_see": se.indirect_see_tco2e_per_t,
            "verified": se.verified,
        }
        for se, name in se_result.all()
    ]
    return imports, default_values, supplier_emissions


async def _latest_ets_price(session: AsyncSession) -> tuple[Decimal, str]:
    """Latest stored EU ETS price (or the explicit fallback) + provenance."""
    latest = await ets_price_service.get_latest_price(session)
    if latest:
        return latest.price_eur, (
            f"Certificate cost uses the latest stored EU ETS price of "
            f"€{float(latest.price_eur):,.2f}/tCO2e ({latest.price_date.isoformat()}, "
            f"{latest.source}); 2026 certificates will be priced on "
            "quarterly EU ETS auction averages."
        )
    return (
        ets_price_service.FALLBACK_ETS_PRICE_EUR,
        ets_price_service.FALLBACK_ASSUMPTION,
    )


def _declaration_detail_response(
    declaration: CBAMAnnualDeclaration, draft: dict, stale: bool
) -> CBAMAnnualDeclarationDetailResponse:
    """Stored declaration summary + computed draft package."""
    base = declaration_to_response(declaration)
    return CBAMAnnualDeclarationDetailResponse(
        **base.model_dump(),
        submission_deadline=declaration.submission_deadline,
        deductions_eur=declaration.carbon_price_deductions_eur or Decimal("0"),
        ets_price_eur=draft["ets_price_eur"],
        default_value_markup_pct=draft["markup_pct"],
        by_cn_code=_json_safe(draft["by_cn_code"]),
        lines=[CBAMDeclarationLineResponse(**line) for line in draft["lines"]],
        data_quality=CBAMDataQualitySummary(**draft["data_quality"]),
        assumptions=draft["assumptions"],
        stale=stale,
    )


def _declaration_is_stale(
    declaration: CBAMAnnualDeclaration, draft_totals: dict
) -> bool:
    """True when the imports register diverged from the stored draft."""
    stored_gross = declaration.total_embedded_emissions_tco2e or Decimal("0")
    return draft_totals["import_count"] != (declaration.total_imports_count or 0) or (
        draft_totals["gross_emissions_tco2e"] - stored_gross
    ).copy_abs() > Decimal("0.005")


@router.post(
    "/reports/annual/{year}", response_model=CBAMAnnualDeclarationDetailResponse
)
async def generate_annual_declaration(
    year: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Generate — or regenerate — the annual CBAM declaration draft for a year.

    Idempotent per org + year: regenerating replaces the existing draft
    (and moves a `ready` declaration back to `draft`, since its contents
    changed). Submitted declarations cannot be regenerated.

    The draft aggregates the imports register: default-value lines are
    re-resolved against the Commission default values in the DB with the
    Omnibus year markup (10% in 2026), actual-data lines keep their recorded
    values, carbon prices paid abroad are deducted per line, and the
    certificate cost uses the latest stored EU ETS price. Deadline: 30
    September of the following year (first: 30 Sep 2027 for 2026).
    """
    if year < 2026:
        raise HTTPException(
            status_code=400,
            detail="Annual declarations are only required from 2026 (definitive phase)",
        )

    result = await session.execute(
        select(CBAMAnnualDeclaration).where(
            CBAMAnnualDeclaration.organization_id == current_user.organization_id,
            CBAMAnnualDeclaration.reporting_year == year,
        )
    )
    existing = result.scalar_one_or_none()

    if existing and existing.status == CBAMReportStatus.SUBMITTED:
        raise HTTPException(
            status_code=400, detail="Cannot regenerate a submitted declaration"
        )

    imports, default_values, supplier_emissions = await _load_declaration_inputs(
        session, current_user.organization_id, year
    )
    ets_price, ets_assumption = await _latest_ets_price(session)

    draft = build_annual_declaration_draft(
        imports,
        year,
        ets_price_eur=ets_price,
        default_values=default_values or None,
        extra_assumptions=[ets_assumption],
        supplier_emissions=supplier_emissions or None,
    )
    totals = draft["totals"]

    if existing:
        declaration = existing
    else:
        # Deadline: 30 September of the following year (Omnibus).
        declaration = CBAMAnnualDeclaration(
            id=uuid4(),
            organization_id=current_user.organization_id,
            reporting_year=year,
            period_start=date(year, 1, 1),
            period_end=date(year, 12, 31),
            submission_deadline=date(year + 1, 9, 30),
            net_emissions_tco2e=Decimal("0"),
        )
        session.add(declaration)

    declaration.status = CBAMReportStatus.DRAFT
    declaration.total_imports_count = totals["import_count"]
    declaration.total_mass_tonnes = totals["mass_tonnes"]
    declaration.total_embedded_emissions_tco2e = totals["gross_emissions_tco2e"]
    declaration.carbon_price_deductions_tco2e = totals["deductions_tco2e"]
    declaration.carbon_price_deductions_eur = totals["deductions_eur"]
    declaration.net_emissions_tco2e = totals["net_emissions_tco2e"]
    declaration.certificates_required = totals["certificates_required"]
    declaration.total_certificate_cost_eur = totals["estimated_cost_eur"]
    declaration.average_certificate_price_eur = draft["ets_price_eur"]
    declaration.by_sector = _json_safe(draft["by_sector"])
    declaration.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(declaration)

    return _declaration_detail_response(declaration, draft, stale=False)


@router.get(
    "/reports/annual/{year}", response_model=CBAMAnnualDeclarationDetailResponse
)
async def get_annual_declaration(
    year: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Full annual declaration draft package for the review screen.

    Returns the stored declaration summary plus the per-line drill list
    (with intensity provenance), per-CN breakdown, data-quality summary and
    assumptions, recomputed from the imports register with the ETS price the
    draft was generated at. `stale: true` means the imports register changed
    since generation — regenerate to refresh the stored totals.
    """
    result = await session.execute(
        select(CBAMAnnualDeclaration).where(
            CBAMAnnualDeclaration.organization_id == current_user.organization_id,
            CBAMAnnualDeclaration.reporting_year == year,
        )
    )
    declaration = result.scalar_one_or_none()

    if not declaration:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No annual declaration generated for {year} yet — "
                f"POST /api/cbam/reports/annual/{year} to generate the draft."
            ),
        )

    imports, default_values, supplier_emissions = await _load_declaration_inputs(
        session, current_user.organization_id, year
    )
    ets_price = declaration.average_certificate_price_eur
    if ets_price:
        ets_assumption = (
            f"Certificate cost uses the EU ETS price of €{float(ets_price):,.2f}/tCO2e "
            "recorded when this draft was generated."
        )
    else:
        ets_price, ets_assumption = await _latest_ets_price(session)

    draft = build_annual_declaration_draft(
        imports,
        year,
        ets_price_eur=ets_price,
        default_values=default_values or None,
        extra_assumptions=[ets_assumption],
        supplier_emissions=supplier_emissions or None,
    )

    return _declaration_detail_response(
        declaration, draft, stale=_declaration_is_stale(declaration, draft["totals"])
    )


@router.patch(
    "/reports/annual/{year}/status", response_model=CBAMAnnualDeclarationResponse
)
async def update_annual_declaration_status(
    year: int,
    data: CBAMDeclarationStatusUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Move an annual declaration between `draft` and `ready`.

    `submitted` is rejected: submission stays manual/on-hold until the
    export is validated against the real CBAM Registry schema.
    """
    new_status = data.status.strip().lower()
    if new_status == CBAMReportStatus.SUBMITTED.value:
        raise HTTPException(status_code=400, detail=_REGISTRY_XML_ON_HOLD_DETAIL)
    if new_status not in (CBAMReportStatus.DRAFT.value, CBAMReportStatus.READY.value):
        raise HTTPException(
            status_code=422,
            detail="Annual declaration status must be 'draft' or 'ready'",
        )

    result = await session.execute(
        select(CBAMAnnualDeclaration).where(
            CBAMAnnualDeclaration.organization_id == current_user.organization_id,
            CBAMAnnualDeclaration.reporting_year == year,
        )
    )
    declaration = result.scalar_one_or_none()

    if not declaration:
        raise HTTPException(
            status_code=404, detail=f"No annual declaration generated for {year} yet"
        )
    if declaration.status == CBAMReportStatus.SUBMITTED:
        raise HTTPException(
            status_code=400, detail="Cannot change a submitted declaration"
        )

    declaration.status = CBAMReportStatus(new_status)
    declaration.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(declaration)

    return declaration_to_response(declaration)


@router.get("/reports/annual/{year}/export/csv")
async def export_annual_declaration_csv(
    year: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Export the annual declaration draft pack as CSV.

    One row per import line with intensity provenance (default vs actual),
    the year markup, deductions and net emissions, plus a TOTAL row with the
    certificates to surrender.
    """
    from fastapi.responses import Response
    from app.services.cbam_export import CBAMCSVExporter

    result = await session.execute(
        select(CBAMAnnualDeclaration).where(
            CBAMAnnualDeclaration.organization_id == current_user.organization_id,
            CBAMAnnualDeclaration.reporting_year == year,
        )
    )
    declaration = result.scalar_one_or_none()

    if not declaration:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No annual declaration generated for {year} yet — "
                "generate the draft first."
            ),
        )

    imports, default_values, supplier_emissions = await _load_declaration_inputs(
        session, current_user.organization_id, year
    )
    ets_price = declaration.average_certificate_price_eur
    if not ets_price:
        ets_price, _ = await _latest_ets_price(session)

    draft = build_annual_declaration_draft(
        imports,
        year,
        ets_price_eur=ets_price,
        default_values=default_values or None,
        supplier_emissions=supplier_emissions or None,
    )

    exporter = CBAMCSVExporter()
    csv_content = exporter.generate_annual_declaration_csv(
        year, draft["lines"], draft["totals"]
    )

    filename = f"cbam_annual_declaration_{year}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ============================================================================
# Dashboard Summary Endpoint
# ============================================================================


@router.get("/dashboard")
async def get_cbam_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Get CBAM dashboard summary with KPIs.

    Returns aggregated metrics for installations, imports, and emissions.
    """
    org_id = current_user.organization_id

    # Count installations
    inst_result = await session.execute(
        select(func.count(CBAMInstallation.id)).where(
            CBAMInstallation.organization_id == org_id
        )
    )
    installation_count = inst_result.scalar() or 0

    # Count installations by country
    country_result = await session.execute(
        select(CBAMInstallation.country_code, func.count(CBAMInstallation.id))
        .where(CBAMInstallation.organization_id == org_id)
        .group_by(CBAMInstallation.country_code)
    )
    installations_by_country = dict(country_result.all())

    # Current year imports summary
    current_year = date.today().year
    imports_result = await session.execute(
        select(
            func.count(CBAMImport.id),
            func.sum(CBAMImport.net_mass_tonnes),
            func.sum(CBAMImport.total_embedded_emissions_tco2e),
        ).where(
            CBAMImport.organization_id == org_id,
            func.extract("year", CBAMImport.import_date) == current_year,
        )
    )
    import_stats = imports_result.one()

    # Imports by sector
    sector_result = await session.execute(
        select(
            CBAMImport.sector,
            func.count(CBAMImport.id),
            func.sum(CBAMImport.total_embedded_emissions_tco2e),
        )
        .where(
            CBAMImport.organization_id == org_id,
            func.extract("year", CBAMImport.import_date) == current_year,
        )
        .group_by(CBAMImport.sector)
    )
    by_sector = [
        {
            "sector": row[0].value if row[0] else "unknown",
            "import_count": row[1],
            "total_emissions_tco2e": float(row[2] or 0),
        }
        for row in sector_result.all()
    ]

    # Quarterly report status
    report_result = await session.execute(
        select(CBAMQuarterlyReport)
        .where(
            CBAMQuarterlyReport.organization_id == org_id,
            CBAMQuarterlyReport.reporting_year == current_year,
        )
        .order_by(CBAMQuarterlyReport.reporting_quarter)
    )
    quarterly_reports = [
        {
            "quarter": r.reporting_quarter,
            "status": r.status.value if r.status else "not_started",
            "total_emissions_tco2e": float(r.total_embedded_emissions_tco2e or 0),
        }
        for r in report_result.scalars().all()
    ]

    return {
        "year": current_year,
        "installations": {
            "total": installation_count,
            "by_country": installations_by_country,
        },
        "imports": {
            "total_count": import_stats[0] or 0,
            "total_mass_tonnes": float(import_stats[1] or 0),
            "total_emissions_tco2e": float(import_stats[2] or 0),
        },
        "by_sector": by_sector,
        "quarterly_reports": quarterly_reports,
        "phase": "transitional" if current_year <= 2025 else "definitive",
    }


# ============================================================================
# Export Endpoints
# ============================================================================


_REGISTRY_XML_ON_HOLD_DETAIL = (
    "CBAM Registry XML export is on hold: the previous XML output was "
    "speculative and has not been validated against the real CBAM Registry "
    "declaration schema. It will be re-enabled once the official schema is "
    "validated. Use the CSV or EU-format (JSON) exports in the meantime."
)


@router.get("/reports/quarterly/{year}/{quarter}/export/xml", status_code=501)
async def export_quarterly_report_xml(
    year: int,
    quarter: int,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    ON HOLD: Registry XML export awaits validation against the real CBAM
    Registry schema. Returns 501 Not Implemented.
    """
    raise HTTPException(status_code=501, detail=_REGISTRY_XML_ON_HOLD_DETAIL)


@router.get("/reports/quarterly/{year}/{quarter}/export/csv")
async def export_quarterly_report_csv(
    year: int,
    quarter: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Export quarterly CBAM report data as CSV.

    Returns detailed import data for analysis.
    """
    from fastapi.responses import Response
    from app.services.cbam_export import CBAMCSVExporter

    # Get imports for this quarter
    month_start = (quarter - 1) * 3 + 1
    month_end = quarter * 3

    imports_result = await session.execute(
        select(CBAMImport).where(
            CBAMImport.organization_id == current_user.organization_id,
            func.extract("year", CBAMImport.import_date) == year,
            func.extract("month", CBAMImport.import_date).between(
                month_start, month_end
            ),
        )
    )
    imports = imports_result.scalars().all()

    # SEE per tonne is derived from stored emissions / mass (the model
    # stores emissions totals and specific_embedded_emissions, not a
    # direct/indirect SEE split).
    def _see(emissions, mass):
        if mass and mass > 0:
            return (emissions or Decimal("0")) / mass
        return Decimal("0")

    import_data = [
        {
            "id": str(imp.id),
            "cn_code": imp.cn_code,
            "sector": imp.sector.value if imp.sector else "unknown",
            "product_description": imp.product_description,
            "import_date": str(imp.import_date),
            "mass_tonnes": imp.net_mass_tonnes,
            "direct_see": _see(imp.direct_emissions_tco2e, imp.net_mass_tonnes),
            "indirect_see": _see(imp.indirect_emissions_tco2e, imp.net_mass_tonnes),
            "total_see": imp.specific_embedded_emissions
            or _see(imp.total_embedded_emissions_tco2e, imp.net_mass_tonnes),
            "direct_emissions_tco2e": imp.direct_emissions_tco2e,
            "indirect_emissions_tco2e": imp.indirect_emissions_tco2e,
            "total_emissions_tco2e": imp.total_embedded_emissions_tco2e,
            "calculation_method": (
                imp.calculation_method.value if imp.calculation_method else "default"
            ),
            # Model field is carbon_price_paid_eur
            "foreign_carbon_price_eur": imp.carbon_price_paid_eur,
            "installation_id": str(imp.installation_id) if imp.installation_id else "",
        }
        for imp in imports
    ]

    exporter = CBAMCSVExporter()
    csv_content = exporter.generate_imports_csv(import_data)

    filename = f"cbam_imports_{year}_Q{quarter}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/reports/quarterly/{year}/{quarter}/export/eu-format")
async def export_quarterly_report_eu_format(
    year: int,
    quarter: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Export quarterly CBAM report in EU Commission format.

    Returns structured JSON matching EU Commission reporting requirements.
    """
    from app.services.cbam_export import CBAMReportFormatter
    from app.models.core import Organization

    # Get the report
    result = await session.execute(
        select(CBAMQuarterlyReport).where(
            CBAMQuarterlyReport.organization_id == current_user.organization_id,
            CBAMQuarterlyReport.reporting_year == year,
            CBAMQuarterlyReport.reporting_quarter == quarter,
        )
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Get imports for this quarter
    month_start = (quarter - 1) * 3 + 1
    month_end = quarter * 3

    imports_result = await session.execute(
        select(CBAMImport).where(
            CBAMImport.organization_id == current_user.organization_id,
            func.extract("year", CBAMImport.import_date) == year,
            func.extract("month", CBAMImport.import_date).between(
                month_start, month_end
            ),
        )
    )
    imports = imports_result.scalars().all()

    # Get installations
    inst_result = await session.execute(
        select(CBAMInstallation).where(
            CBAMInstallation.organization_id == current_user.organization_id,
        )
    )
    installations = inst_result.scalars().all()

    # Get organization info
    org_result = await session.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = org_result.scalar_one_or_none()

    # Convert to dicts (model fields: reporting_year/reporting_quarter/
    # total_imports_count; a by_cn_code breakdown is not stored on the
    # model, so it is exported empty).
    report_data = {
        "year": report.reporting_year,
        "quarter": report.reporting_quarter,
        "status": report.status.value if report.status else "draft",
        "total_imports": report.total_imports_count or 0,
        "total_mass_tonnes": report.total_mass_tonnes,
        "total_emissions_tco2e": report.total_embedded_emissions_tco2e,
        "by_sector": report.by_sector or {},
        "by_cn_code": {},  # Not stored on the model
        "submitted_at": (
            report.submitted_at.isoformat() if report.submitted_at else None
        ),
    }

    import_data = [
        {
            "direct_emissions_tco2e": float(imp.direct_emissions_tco2e or 0),
            "indirect_emissions_tco2e": float(imp.indirect_emissions_tco2e or 0),
            "calculation_method": (
                imp.calculation_method.value if imp.calculation_method else "default"
            ),
        }
        for imp in imports
    ]

    installation_data = [
        {
            "id": str(inst.id),
            "name": inst.name,
            "country_code": inst.country_code,
            # Model stores a single sector enum; exported as a list
            "sectors": [inst.sector.value] if inst.sector else [],
            "verification_status": (
                inst.verification_status.value
                if inst.verification_status
                else "pending"
            ),
        }
        for inst in installations
    ]

    org_data = {
        "name": org.name if org else "",
        "country_code": org.country_code if org else "",
    }

    formatter = CBAMReportFormatter()
    formatted_report = formatter.format_quarterly_report(
        report=report_data,
        imports=import_data,
        installations=installation_data,
        organization=org_data,
    )

    return formatted_report


@router.get("/reports/annual/{year}/export/xml", status_code=501)
async def export_annual_declaration_xml(
    year: int,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    ON HOLD: annual declaration Registry XML export awaits validation
    against the real CBAM Registry declaration schema. Returns 501.
    """
    raise HTTPException(status_code=501, detail=_REGISTRY_XML_ON_HOLD_DETAIL)
