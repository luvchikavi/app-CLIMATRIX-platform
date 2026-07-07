"""
Organization API endpoints.

Manage organization settings including region configuration.
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.api.auth import get_current_user
from app.database import get_session
from app.models.core import (
    User,
    Organization,
    Site,
    ReportingPeriod,
    ModuleWaitlist,
)
from app.models.emission import Activity, Emission

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================


class OrganizationResponse(BaseModel):
    """Organization details response."""

    id: str
    name: str
    country_code: str | None
    industry_code: str | None
    base_year: int | None
    default_region: str
    setup_complete: bool = False
    currency: str | None = None
    unit_system: str = "metric"
    consolidation_approach: str = "operational_control"


class OrganizationUpdate(BaseModel):
    """Update organization settings."""

    name: str | None = None
    country_code: str | None = None
    industry_code: str | None = None
    base_year: int | None = None
    default_region: str | None = None
    currency: str | None = None
    unit_system: str | None = None
    consolidation_approach: str | None = None


UNIT_SYSTEMS = ["metric", "imperial"]
CONSOLIDATION_APPROACHES = [
    "operational_control",
    "financial_control",
    "equity_share",
]


class SiteResponse(BaseModel):
    """Site details response."""

    id: str
    name: str
    country_code: str | None
    address: str | None
    grid_region: str | None
    is_active: bool


class SiteCreate(BaseModel):
    """Create site request."""

    name: str
    country_code: str | None = None
    address: str | None = None
    grid_region: str | None = None


# Supported regions for emission factors
SUPPORTED_REGIONS = [
    {
        "code": "Global",
        "name": "Global Average",
        "description": "Uses worldwide average emission factors",
    },
    {
        "code": "UK",
        "name": "United Kingdom",
        "description": "DEFRA emission factors for UK",
    },
    {
        "code": "US",
        "name": "United States",
        "description": "EPA emission factors for US",
    },
    {
        "code": "EU",
        "name": "European Union",
        "description": "EU average emission factors",
    },
    {
        "code": "IL",
        "name": "Israel",
        "description": "Israel-specific grid and energy factors",
    },
]


# ============================================================================
# Endpoints
# ============================================================================


def _org_response(org: Organization) -> OrganizationResponse:
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        country_code=org.country_code,
        industry_code=org.industry_code,
        base_year=org.base_year,
        default_region=org.default_region or "Global",
        setup_complete=org.setup_complete,
        currency=org.currency,
        unit_system=org.unit_system or "metric",
        consolidation_approach=org.consolidation_approach or "operational_control",
    )


@router.get("/organization", response_model=OrganizationResponse)
async def get_organization(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user's organization details."""
    query = select(Organization).where(Organization.id == current_user.organization_id)
    result = await session.execute(query)
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return _org_response(org)


@router.patch("/organization", response_model=OrganizationResponse)
async def update_organization(
    data: OrganizationUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update organization settings."""
    # Check user has admin role
    if current_user.role.value not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=403, detail="Only admins can update organization settings"
        )

    query = select(Organization).where(Organization.id == current_user.organization_id)
    result = await session.execute(query)
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Validate region if provided
    if data.default_region:
        valid_regions = [r["code"] for r in SUPPORTED_REGIONS]
        if data.default_region not in valid_regions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid region. Supported regions: {', '.join(valid_regions)}",
            )

    if data.currency is not None and len(data.currency) != 3:
        raise HTTPException(
            status_code=400, detail="Currency must be a 3-letter ISO code (e.g. USD)"
        )
    if data.unit_system is not None and data.unit_system not in UNIT_SYSTEMS:
        raise HTTPException(
            status_code=400,
            detail=f"Unit system must be one of: {', '.join(UNIT_SYSTEMS)}",
        )
    if (
        data.consolidation_approach is not None
        and data.consolidation_approach not in CONSOLIDATION_APPROACHES
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Consolidation approach must be one of: "
                f"{', '.join(CONSOLIDATION_APPROACHES)}"
            ),
        )

    # Update fields
    if data.name is not None:
        org.name = data.name
    if data.country_code is not None:
        org.country_code = data.country_code
    if data.industry_code is not None:
        org.industry_code = data.industry_code
    if data.base_year is not None:
        org.base_year = data.base_year
    if data.default_region is not None:
        org.default_region = data.default_region
    if data.currency is not None:
        org.currency = data.currency.upper()
    if data.unit_system is not None:
        org.unit_system = data.unit_system
    if data.consolidation_approach is not None:
        org.consolidation_approach = data.consolidation_approach

    await session.commit()
    await session.refresh(org)

    return _org_response(org)


@router.get("/organization/regions")
async def get_supported_regions():
    """Get list of supported regions for emission factors."""
    return SUPPORTED_REGIONS


# ============================================================================
# Sites
# ============================================================================


@router.get("/organization/sites", response_model=list[SiteResponse])
async def list_sites(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all sites for the organization."""
    query = select(Site).where(
        Site.organization_id == current_user.organization_id,
        Site.is_active == True,
    )
    result = await session.execute(query)
    sites = result.scalars().all()

    return [
        SiteResponse(
            id=str(s.id),
            name=s.name,
            country_code=s.country_code,
            address=s.address,
            grid_region=s.grid_region,
            is_active=s.is_active,
        )
        for s in sites
    ]


@router.post("/organization/sites", response_model=SiteResponse)
async def create_site(
    data: SiteCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new site for the organization."""
    site = Site(
        organization_id=current_user.organization_id,
        name=data.name,
        country_code=data.country_code,
        address=data.address,
        grid_region=data.grid_region,
    )
    session.add(site)
    await session.commit()
    await session.refresh(site)

    return SiteResponse(
        id=str(site.id),
        name=site.name,
        country_code=site.country_code,
        address=site.address,
        grid_region=site.grid_region,
        is_active=site.is_active,
    )


@router.delete("/organization/sites/{site_id}")
async def delete_site(
    site_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Soft-delete a site (deactivate)."""
    query = select(Site).where(
        Site.id == site_id,
        Site.organization_id == current_user.organization_id,
    )
    result = await session.execute(query)
    site = result.scalar_one_or_none()

    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    site.is_active = False
    await session.commit()

    return {"status": "deleted", "id": str(site_id)}


class SiteDetailResponse(BaseModel):
    """Site details with emission statistics."""

    id: str
    name: str
    country_code: str | None
    address: str | None
    grid_region: str | None
    is_active: bool
    activity_count: int
    total_co2e_kg: float
    total_co2e_tonnes: float
    scope_1_co2e_kg: float
    scope_2_co2e_kg: float
    scope_3_co2e_kg: float


@router.get("/organization/sites/{site_id}", response_model=SiteDetailResponse)
async def get_site_detail(
    site_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    period_id: UUID | None = None,
):
    """Get site details with emission statistics, optionally for a specific period."""
    query = select(Site).where(
        Site.id == site_id,
        Site.organization_id == current_user.organization_id,
    )
    result = await session.execute(query)
    site = result.scalar_one_or_none()

    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # Build activity filters
    filters = [
        Activity.site_id == site_id,
        Activity.organization_id == current_user.organization_id,
    ]
    if period_id:
        filters.append(Activity.reporting_period_id == period_id)

    # Get emission stats by scope
    stats_query = (
        select(
            Activity.scope,
            func.sum(Emission.co2e_kg).label("total_co2e"),
            func.count(Activity.id).label("count"),
        )
        .join(Emission, Activity.id == Emission.activity_id)
        .where(*filters)
        .group_by(Activity.scope)
    )
    stats_result = await session.execute(stats_query)
    stats_rows = stats_result.all()

    scope_totals = {1: Decimal(0), 2: Decimal(0), 3: Decimal(0)}
    activity_count = 0
    for row in stats_rows:
        scope_totals[row.scope] = row.total_co2e or Decimal(0)
        activity_count += row.count

    total = sum(scope_totals.values())

    return SiteDetailResponse(
        id=str(site.id),
        name=site.name,
        country_code=site.country_code,
        address=site.address,
        grid_region=site.grid_region,
        is_active=site.is_active,
        activity_count=activity_count,
        total_co2e_kg=float(total),
        total_co2e_tonnes=float(total / 1000),
        scope_1_co2e_kg=float(scope_totals[1]),
        scope_2_co2e_kg=float(scope_totals[2]),
        scope_3_co2e_kg=float(scope_totals[3]),
    )


class SiteEmissionSummary(BaseModel):
    """Emission summary for one site in the breakdown."""

    site_id: str
    site_name: str
    total_co2e_kg: float
    total_co2e_tonnes: float
    scope_1_co2e_kg: float
    scope_2_co2e_kg: float
    scope_3_co2e_kg: float
    activity_count: int


@router.get("/organization/sites-breakdown", response_model=list[SiteEmissionSummary])
async def get_sites_emission_breakdown(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    period_id: UUID | None = None,
):
    """
    Get emission breakdown across all sites.
    Returns per-site totals for dashboard comparison charts.
    """
    # Build activity filters
    filters = [
        Activity.organization_id == current_user.organization_id,
        Activity.site_id.isnot(None),
    ]
    if period_id:
        filters.append(Activity.reporting_period_id == period_id)

    # Get per-site, per-scope totals
    query = (
        select(
            Activity.site_id,
            Activity.scope,
            func.sum(Emission.co2e_kg).label("total_co2e"),
            func.count(Activity.id).label("count"),
        )
        .join(Emission, Activity.id == Emission.activity_id)
        .where(*filters)
        .group_by(Activity.site_id, Activity.scope)
    )
    result = await session.execute(query)
    rows = result.all()

    # Group by site
    site_data: dict[UUID, dict] = {}
    for row in rows:
        sid = row.site_id
        if sid not in site_data:
            site_data[sid] = {
                "scope_totals": {1: Decimal(0), 2: Decimal(0), 3: Decimal(0)},
                "activity_count": 0,
            }
        site_data[sid]["scope_totals"][row.scope] = row.total_co2e or Decimal(0)
        site_data[sid]["activity_count"] += row.count

    # Fetch site names
    if site_data:
        sites_query = select(Site).where(
            Site.id.in_(list(site_data.keys())),
            Site.organization_id == current_user.organization_id,
        )
        sites_result = await session.execute(sites_query)
        sites = {s.id: s for s in sites_result.scalars().all()}
    else:
        sites = {}

    # Build response
    summaries = []
    for sid, data in site_data.items():
        site = sites.get(sid)
        if not site:
            continue
        total = sum(data["scope_totals"].values())
        summaries.append(
            SiteEmissionSummary(
                site_id=str(sid),
                site_name=site.name,
                total_co2e_kg=float(total),
                total_co2e_tonnes=float(total / 1000),
                scope_1_co2e_kg=float(data["scope_totals"][1]),
                scope_2_co2e_kg=float(data["scope_totals"][2]),
                scope_3_co2e_kg=float(data["scope_totals"][3]),
                activity_count=data["activity_count"],
            )
        )

    # Sort by total emissions descending
    summaries.sort(key=lambda s: s.total_co2e_kg, reverse=True)
    return summaries


# ============================================================================
# Setup gate + module waitlist
# ============================================================================


@router.patch("/organization/complete-setup", response_model=OrganizationResponse)
async def complete_setup(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Mark org setup complete after server-side validation of the required steps.

    Requires: industry_code, base_year, default_region, >=1 Site, >=1 ReportingPeriod.
    Returns 422 with the list of missing items otherwise.
    """
    org = (
        await session.execute(
            select(Organization).where(Organization.id == current_user.organization_id)
        )
    ).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # industry_code is collected for recommendations but is not a hard gate.
    missing: list[str] = []
    if not org.base_year:
        missing.append("base_year")
    if not org.default_region:
        missing.append("region")

    site_count = (
        await session.execute(
            select(func.count())
            .select_from(Site)
            .where(Site.organization_id == current_user.organization_id)
        )
    ).scalar_one()
    if not site_count:
        missing.append("site")

    period_count = (
        await session.execute(
            select(func.count())
            .select_from(ReportingPeriod)
            .where(ReportingPeriod.organization_id == current_user.organization_id)
        )
    ).scalar_one()
    if not period_count:
        missing.append("reporting_period")

    if missing:
        raise HTTPException(
            status_code=422,
            detail={"message": "Organization setup is incomplete", "missing": missing},
        )

    org.setup_complete = True
    org.setup_completed_at = datetime.utcnow()
    await session.commit()
    await session.refresh(org)

    return _org_response(org)


class WaitlistRequest(BaseModel):
    """Notify-me request for a Coming Soon module."""

    module_id: str
    email: str | None = None


class WaitlistResponse(BaseModel):
    ok: bool
    module_id: str


@router.post("/modules/waitlist", response_model=WaitlistResponse)
async def join_module_waitlist(
    data: WaitlistRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Capture a 'Notify Me' signup for a Coming Soon module (a conference lead)."""
    entry = ModuleWaitlist(
        organization_id=current_user.organization_id,
        module_id=data.module_id,
        email=(data.email or current_user.email),
    )
    session.add(entry)
    await session.commit()
    return WaitlistResponse(ok=True, module_id=data.module_id)
