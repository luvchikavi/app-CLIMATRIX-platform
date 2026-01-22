"""
Organization API endpoints.

Manage organization settings including region configuration.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.auth import get_current_user
from app.database import get_session
from app.models.core import User, Organization, Site


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


class OrganizationUpdate(BaseModel):
    """Update organization settings."""
    name: str | None = None
    country_code: str | None = None
    industry_code: str | None = None
    base_year: int | None = None
    default_region: str | None = None


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
    {"code": "Global", "name": "Global Average", "description": "Uses worldwide average emission factors"},
    {"code": "UK", "name": "United Kingdom", "description": "DEFRA emission factors for UK"},
    {"code": "US", "name": "United States", "description": "EPA emission factors for US"},
    {"code": "EU", "name": "European Union", "description": "EU average emission factors"},
    {"code": "IL", "name": "Israel", "description": "Israel-specific grid and energy factors"},
]


# ============================================================================
# Endpoints
# ============================================================================

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

    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        country_code=org.country_code,
        industry_code=org.industry_code,
        base_year=org.base_year,
        default_region=org.default_region or "Global",
    )


@router.patch("/organization", response_model=OrganizationResponse)
async def update_organization(
    data: OrganizationUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update organization settings."""
    # Check user has admin role
    if current_user.role.value not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admins can update organization settings")

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
                detail=f"Invalid region. Supported regions: {', '.join(valid_regions)}"
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

    await session.commit()
    await session.refresh(org)

    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        country_code=org.country_code,
        industry_code=org.industry_code,
        base_year=org.base_year,
        default_region=org.default_region or "Global",
    )


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
