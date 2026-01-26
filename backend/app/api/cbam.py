"""
CBAM (Carbon Border Adjustment Mechanism) API endpoints.

Implements EU CBAM requirements for:
- Installation management (non-EU production facilities)
- Import tracking and embedded emissions calculation
- Quarterly transitional reports (2024-2025)
- Annual declarations with certificate requirements (2026+)
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.api.auth import get_current_user
from app.database import get_session
from app.models.core import User
from app.models.cbam import (
    CBAMInstallation,
    CBAMInstallationStatus,
    CBAMImport,
    CBAMQuarterlyReport,
    CBAMReportStatus,
    CBAMAnnualDeclaration,
    CBAMProduct,
    CBAMDefaultValue,
    CBAMGridFactor,
    EUETSPrice,
    CBAMSector,
    CBAMCalculationMethod,
)
from app.services.cbam_calculator import (
    CBAMCalculator,
    aggregate_quarterly_report,
    aggregate_annual_declaration,
)
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
    """Create CBAM import request."""
    installation_id: str
    cn_code: str = Field(..., min_length=8, max_length=20)
    product_description: Optional[str] = None
    import_date: date
    mass_tonnes: Decimal = Field(..., gt=0)
    customs_procedure: Optional[str] = None
    customs_declaration_number: Optional[str] = None
    actual_direct_see: Optional[Decimal] = None
    actual_indirect_see: Optional[Decimal] = None
    electricity_consumption_mwh: Optional[Decimal] = None
    foreign_carbon_price_eur: Optional[Decimal] = None
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
    mass_tonnes: Decimal
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


# ============================================================================
# Helper Functions
# ============================================================================

def installation_to_response(inst: CBAMInstallation) -> CBAMInstallationResponse:
    """Convert installation model to response."""
    return CBAMInstallationResponse(
        id=str(inst.id),
        organization_id=str(inst.organization_id),
        name=inst.name,
        country_code=inst.country_code,
        address=inst.address,
        contact_name=inst.contact_name,
        contact_email=inst.contact_email,
        sectors=inst.sectors or [],
        verification_status=inst.verification_status.value if inst.verification_status else "pending",
        created_at=inst.created_at,
        updated_at=inst.updated_at,
    )


def import_to_response(imp: CBAMImport) -> CBAMImportResponse:
    """Convert import model to response."""
    return CBAMImportResponse(
        id=str(imp.id),
        organization_id=str(imp.organization_id),
        installation_id=str(imp.installation_id),
        cn_code=imp.cn_code,
        sector=imp.sector.value if imp.sector else "unknown",
        product_description=imp.product_description,
        import_date=imp.import_date,
        mass_tonnes=imp.net_mass_tonnes,
        calculation_method=imp.calculation_method.value if imp.calculation_method else "default",
        direct_see=imp.direct_see or Decimal("0"),
        indirect_see=imp.indirect_see or Decimal("0"),
        total_see=imp.total_see or Decimal("0"),
        direct_emissions_tco2e=imp.direct_emissions_tco2e or Decimal("0"),
        indirect_emissions_tco2e=imp.indirect_emissions_tco2e or Decimal("0"),
        total_emissions_tco2e=imp.total_embedded_emissions_tco2e or Decimal("0"),
        foreign_carbon_price_eur=imp.foreign_carbon_price_eur,
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

    result = await session.execute(query.order_by(CBAMInstallation.name))
    installations = result.scalars().all()

    # Filter by sector if specified (sectors is a JSON array)
    if sector:
        installations = [
            inst for inst in installations
            if sector.lower() in [s.lower() for s in (inst.sectors or [])]
        ]

    return [installation_to_response(inst) for inst in installations]


@router.post("/installations", response_model=CBAMInstallationResponse)
async def create_installation(
    data: CBAMInstallationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create a new CBAM installation (non-EU production facility)."""
    installation = CBAMInstallation(
        id=uuid4(),
        organization_id=current_user.organization_id,
        name=data.name,
        country_code=data.country_code.upper(),
        address=data.address,
        contact_name=data.contact_name,
        contact_email=data.contact_email,
        sectors=data.sectors,
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
    if data.country_code is not None:
        installation.country_code = data.country_code.upper()
    if data.address is not None:
        installation.address = data.address
    if data.contact_name is not None:
        installation.contact_name = data.contact_name
    if data.contact_email is not None:
        installation.contact_email = data.contact_email
    if data.sectors is not None:
        installation.sectors = data.sectors
    if data.verification_status is not None:
        installation.verification_status = CBAMInstallationStatus(data.verification_status)

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
            detail=f"Cannot delete installation with {import_count} linked imports"
        )

    await session.delete(installation)
    await session.commit()

    return {"message": "Installation deleted successfully"}


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
            func.extract("month", CBAMImport.import_date).between(month_start, month_end)
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
    # Verify installation exists and belongs to organization
    result = await session.execute(
        select(CBAMInstallation).where(
            CBAMInstallation.id == UUID(data.installation_id),
            CBAMInstallation.organization_id == current_user.organization_id,
        )
    )
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    # Calculate embedded emissions
    calculation = calculator.calculate_embedded_emissions(
        cn_code=data.cn_code,
        mass_tonnes=data.mass_tonnes,
        country_code=installation.country_code,
        actual_direct_see=data.actual_direct_see,
        actual_indirect_see=data.actual_indirect_see,
        electricity_consumption_mwh=data.electricity_consumption_mwh,
    )

    # Determine sector from CN code
    sector_str = get_sector_for_cn_code(data.cn_code)
    sector = CBAMSector(sector_str) if sector_str else CBAMSector.OTHER

    # Create import record
    cbam_import = CBAMImport(
        id=uuid4(),
        organization_id=current_user.organization_id,
        installation_id=installation.id,
        cn_code=data.cn_code,
        sector=sector,
        product_description=data.product_description,
        import_date=data.import_date,
        mass_tonnes=data.mass_tonnes,
        calculation_method=CBAMCalculationMethod.ACTUAL if data.actual_direct_see else CBAMCalculationMethod.DEFAULT,
        direct_see=calculation["direct_see"],
        indirect_see=calculation["indirect_see"],
        total_see=calculation["total_see"],
        direct_emissions_tco2e=calculation["direct_emissions_tco2e"],
        indirect_emissions_tco2e=calculation["indirect_emissions_tco2e"],
        total_emissions_tco2e=calculation["total_emissions_tco2e"],
        customs_procedure=data.customs_procedure,
        customs_declaration_number=data.customs_declaration_number,
        foreign_carbon_price_eur=data.foreign_carbon_price_eur,
        foreign_carbon_price_currency=data.foreign_carbon_price_currency,
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
            results.append(CNCodeResponse(
                cn_code=cn_code,
                description=description,
                sector=prod_sector,
            ))

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
    """List all quarterly CBAM reports for the organization."""
    query = select(CBAMQuarterlyReport).where(
        CBAMQuarterlyReport.organization_id == current_user.organization_id
    )

    if year:
        query = query.where(CBAMQuarterlyReport.year == year)

    result = await session.execute(
        query.order_by(CBAMQuarterlyReport.year.desc(), CBAMQuarterlyReport.quarter.desc())
    )
    reports = result.scalars().all()

    return [
        CBAMQuarterlyReportResponse(
            id=str(r.id),
            organization_id=str(r.organization_id),
            year=r.year,
            quarter=r.quarter,
            status=r.status.value if r.status else "draft",
            total_imports=r.total_imports or 0,
            total_mass_tonnes=r.total_mass_tonnes or Decimal("0"),
            total_emissions_tco2e=r.total_emissions_tco2e or Decimal("0"),
            by_sector=r.by_sector or {},
            by_cn_code=r.by_cn_code or {},
            submitted_at=r.submitted_at,
            created_at=r.created_at,
        )
        for r in reports
    ]


@router.post("/reports/quarterly/{year}/{quarter}", response_model=CBAMQuarterlyReportResponse)
async def generate_quarterly_report(
    year: int,
    quarter: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Generate or regenerate a quarterly CBAM report.

    Aggregates all imports for the specified quarter.
    """
    if quarter < 1 or quarter > 4:
        raise HTTPException(status_code=400, detail="Quarter must be 1-4")

    # Check if report already exists
    result = await session.execute(
        select(CBAMQuarterlyReport).where(
            CBAMQuarterlyReport.organization_id == current_user.organization_id,
            CBAMQuarterlyReport.year == year,
            CBAMQuarterlyReport.quarter == quarter,
        )
    )
    existing_report = result.scalar_one_or_none()

    if existing_report and existing_report.status == CBAMReportStatus.SUBMITTED:
        raise HTTPException(
            status_code=400,
            detail="Cannot regenerate a submitted report"
        )

    # Get imports for this quarter
    month_start = (quarter - 1) * 3 + 1
    month_end = quarter * 3

    imports_result = await session.execute(
        select(CBAMImport).where(
            CBAMImport.organization_id == current_user.organization_id,
            func.extract("year", CBAMImport.import_date) == year,
            func.extract("month", CBAMImport.import_date).between(month_start, month_end),
        )
    )
    imports = imports_result.scalars().all()

    # Convert to calculation format
    import_data = []
    for imp in imports:
        import_data.append({
            "summary": {
                "cn_code": imp.cn_code,
                "sector": imp.sector.value if imp.sector else "unknown",
                "mass_tonnes": imp.net_mass_tonnes,
                "country_code": "XX",  # Would come from installation
            },
            "embedded_emissions": {
                "direct_emissions_tco2e": imp.direct_emissions_tco2e or Decimal("0"),
                "indirect_emissions_tco2e": imp.indirect_emissions_tco2e or Decimal("0"),
                "total_emissions_tco2e": imp.total_embedded_emissions_tco2e or Decimal("0"),
            },
        })

    # Aggregate the report
    aggregated = aggregate_quarterly_report(import_data, quarter, year)

    if existing_report:
        # Update existing report
        existing_report.total_imports = len(imports)
        existing_report.total_mass_tonnes = aggregated["totals"]["mass_tonnes"]
        existing_report.total_emissions_tco2e = aggregated["totals"]["total_emissions_tco2e"]
        existing_report.by_sector = aggregated["by_sector"]
        existing_report.by_cn_code = aggregated["by_cn_code"]
        existing_report.updated_at = datetime.utcnow()
        report = existing_report
    else:
        # Create new report
        report = CBAMQuarterlyReport(
            id=uuid4(),
            organization_id=current_user.organization_id,
            year=year,
            quarter=quarter,
            status=CBAMReportStatus.DRAFT,
            total_imports=len(imports),
            total_mass_tonnes=aggregated["totals"]["mass_tonnes"],
            total_emissions_tco2e=aggregated["totals"]["total_emissions_tco2e"],
            by_sector=aggregated["by_sector"],
            by_cn_code=aggregated["by_cn_code"],
        )
        session.add(report)

    await session.commit()
    await session.refresh(report)

    return CBAMQuarterlyReportResponse(
        id=str(report.id),
        organization_id=str(report.organization_id),
        year=report.year,
        quarter=report.quarter,
        status=report.status.value if report.status else "draft",
        total_imports=report.total_imports or 0,
        total_mass_tonnes=report.total_mass_tonnes or Decimal("0"),
        total_emissions_tco2e=report.total_emissions_tco2e or Decimal("0"),
        by_sector=report.by_sector or {},
        by_cn_code=report.by_cn_code or {},
        submitted_at=report.submitted_at,
        created_at=report.created_at,
    )


@router.post("/reports/quarterly/{year}/{quarter}/submit")
async def submit_quarterly_report(
    year: int,
    quarter: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Mark a quarterly report as submitted."""
    result = await session.execute(
        select(CBAMQuarterlyReport).where(
            CBAMQuarterlyReport.organization_id == current_user.organization_id,
            CBAMQuarterlyReport.year == year,
            CBAMQuarterlyReport.quarter == quarter,
        )
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.status == CBAMReportStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Report already submitted")

    report.status = CBAMReportStatus.SUBMITTED
    report.submitted_at = datetime.utcnow()
    report.submitted_by_id = current_user.id
    report.updated_at = datetime.utcnow()

    await session.commit()

    return {"message": f"Q{quarter} {year} report submitted successfully"}


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
        select(CBAMAnnualDeclaration).where(
            CBAMAnnualDeclaration.organization_id == current_user.organization_id
        ).order_by(CBAMAnnualDeclaration.year.desc())
    )
    declarations = result.scalars().all()

    return [
        CBAMAnnualDeclarationResponse(
            id=str(d.id),
            organization_id=str(d.organization_id),
            year=d.year,
            status=d.status.value if d.status else "draft",
            total_imports=d.total_imports or 0,
            total_mass_tonnes=d.total_mass_tonnes or Decimal("0"),
            gross_emissions_tco2e=d.gross_emissions_tco2e or Decimal("0"),
            deductions_tco2e=d.deductions_tco2e or Decimal("0"),
            net_emissions_tco2e=d.net_emissions_tco2e or Decimal("0"),
            certificates_required=d.certificates_required or Decimal("0"),
            estimated_cost_eur=d.estimated_cost_eur or Decimal("0"),
            by_sector=d.by_sector or {},
            submitted_at=d.submitted_at,
            created_at=d.created_at,
        )
        for d in declarations
    ]


@router.post("/reports/annual/{year}", response_model=CBAMAnnualDeclarationResponse)
async def generate_annual_declaration(
    year: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Generate or regenerate an annual CBAM declaration.

    Only applicable from 2026 (definitive phase). Calculates certificate requirements.
    """
    if year < 2026:
        raise HTTPException(
            status_code=400,
            detail="Annual declarations are only required from 2026 (definitive phase)"
        )

    # Check if declaration already exists
    result = await session.execute(
        select(CBAMAnnualDeclaration).where(
            CBAMAnnualDeclaration.organization_id == current_user.organization_id,
            CBAMAnnualDeclaration.year == year,
        )
    )
    existing = result.scalar_one_or_none()

    if existing and existing.status == CBAMReportStatus.SUBMITTED:
        raise HTTPException(
            status_code=400,
            detail="Cannot regenerate a submitted declaration"
        )

    # Get all imports for the year
    imports_result = await session.execute(
        select(CBAMImport).where(
            CBAMImport.organization_id == current_user.organization_id,
            func.extract("year", CBAMImport.import_date) == year,
        )
    )
    imports = imports_result.scalars().all()

    # Get EU ETS prices for the year (if available)
    ets_result = await session.execute(
        select(EUETSPrice).where(
            func.extract("year", EUETSPrice.price_date) == year
        )
    )
    ets_prices = ets_result.scalars().all()
    ets_price_data = [{"price_eur": p.price_eur} for p in ets_prices]

    # Calculate full CBAM for each import
    import_calculations = []
    for imp in imports:
        calc = calculator.calculate_import_full(
            cn_code=imp.cn_code,
            mass_tonnes=imp.net_mass_tonnes,
            country_code="XX",  # Would come from installation
            actual_direct_see=imp.direct_see,
            actual_indirect_see=imp.indirect_see,
            foreign_carbon_price_eur=imp.foreign_carbon_price_eur,
            is_definitive_phase=True,
        )
        import_calculations.append(calc)

    # Aggregate annual declaration
    aggregated = aggregate_annual_declaration(import_calculations, year, ets_price_data)

    if existing:
        # Update existing
        existing.total_imports = len(imports)
        existing.total_mass_tonnes = sum(imp.net_mass_tonnes for imp in imports)
        existing.gross_emissions_tco2e = aggregated["totals"]["gross_emissions_tco2e"]
        existing.deductions_tco2e = aggregated["totals"]["deductions_tco2e"]
        existing.net_emissions_tco2e = aggregated["totals"]["net_emissions_tco2e"]
        existing.certificates_required = aggregated["totals"]["certificates_required"]
        existing.estimated_cost_eur = aggregated["totals"]["estimated_total_cost_eur"]
        existing.by_sector = aggregated["by_sector"]
        existing.updated_at = datetime.utcnow()
        declaration = existing
    else:
        # Create new
        declaration = CBAMAnnualDeclaration(
            id=uuid4(),
            organization_id=current_user.organization_id,
            year=year,
            status=CBAMReportStatus.DRAFT,
            total_imports=len(imports),
            total_mass_tonnes=sum(imp.net_mass_tonnes for imp in imports),
            gross_emissions_tco2e=aggregated["totals"]["gross_emissions_tco2e"],
            deductions_tco2e=aggregated["totals"]["deductions_tco2e"],
            net_emissions_tco2e=aggregated["totals"]["net_emissions_tco2e"],
            certificates_required=aggregated["totals"]["certificates_required"],
            estimated_cost_eur=aggregated["totals"]["estimated_total_cost_eur"],
            by_sector=aggregated["by_sector"],
        )
        session.add(declaration)

    await session.commit()
    await session.refresh(declaration)

    return CBAMAnnualDeclarationResponse(
        id=str(declaration.id),
        organization_id=str(declaration.organization_id),
        year=declaration.year,
        status=declaration.status.value if declaration.status else "draft",
        total_imports=declaration.total_imports or 0,
        total_mass_tonnes=declaration.total_mass_tonnes or Decimal("0"),
        gross_emissions_tco2e=declaration.gross_emissions_tco2e or Decimal("0"),
        deductions_tco2e=declaration.deductions_tco2e or Decimal("0"),
        net_emissions_tco2e=declaration.net_emissions_tco2e or Decimal("0"),
        certificates_required=declaration.certificates_required or Decimal("0"),
        estimated_cost_eur=declaration.estimated_cost_eur or Decimal("0"),
        by_sector=declaration.by_sector or {},
        submitted_at=declaration.submitted_at,
        created_at=declaration.created_at,
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
        select(
            CBAMInstallation.country_code,
            func.count(CBAMInstallation.id)
        ).where(
            CBAMInstallation.organization_id == org_id
        ).group_by(CBAMInstallation.country_code)
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
        ).where(
            CBAMImport.organization_id == org_id,
            func.extract("year", CBAMImport.import_date) == current_year,
        ).group_by(CBAMImport.sector)
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
        select(CBAMQuarterlyReport).where(
            CBAMQuarterlyReport.organization_id == org_id,
            CBAMQuarterlyReport.year == current_year,
        ).order_by(CBAMQuarterlyReport.quarter)
    )
    quarterly_reports = [
        {
            "quarter": r.quarter,
            "status": r.status.value if r.status else "not_started",
            "total_emissions_tco2e": float(r.total_emissions_tco2e or 0),
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

@router.get("/reports/quarterly/{year}/{quarter}/export/xml")
async def export_quarterly_report_xml(
    year: int,
    quarter: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Export quarterly CBAM report as XML for EU Registry submission.

    Returns XML formatted according to EU CBAM Registry requirements.
    """
    from fastapi.responses import Response
    from app.services.cbam_export import CBAMXMLExporter
    from app.models.core import Organization

    # Get the report
    result = await session.execute(
        select(CBAMQuarterlyReport).where(
            CBAMQuarterlyReport.organization_id == current_user.organization_id,
            CBAMQuarterlyReport.year == year,
            CBAMQuarterlyReport.quarter == quarter,
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
            func.extract("month", CBAMImport.import_date).between(month_start, month_end),
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

    # Convert to dicts for export
    report_data = {
        "year": report.year,
        "quarter": report.quarter,
        "status": report.status.value if report.status else "draft",
        "total_imports": report.total_imports,
        "total_mass_tonnes": report.total_mass_tonnes,
        "total_emissions_tco2e": report.total_emissions_tco2e,
        "by_sector": report.by_sector,
        "by_cn_code": report.by_cn_code,
    }

    import_data = [
        {
            "id": str(imp.id),
            "cn_code": imp.cn_code,
            "product_description": imp.product_description,
            "mass_tonnes": imp.net_mass_tonnes,
            "direct_see": imp.direct_see,
            "indirect_see": imp.indirect_see,
            "total_see": imp.total_see,
            "direct_emissions_tco2e": imp.direct_emissions_tco2e,
            "indirect_emissions_tco2e": imp.indirect_emissions_tco2e,
            "total_emissions_tco2e": imp.total_embedded_emissions_tco2e,
            "calculation_method": imp.calculation_method.value if imp.calculation_method else "default",
            "installation_id": str(imp.installation_id),
            "foreign_carbon_price_eur": imp.foreign_carbon_price_eur,
            "foreign_carbon_price_currency": imp.foreign_carbon_price_currency,
        }
        for imp in imports
    ]

    installation_data = [
        {
            "id": str(inst.id),
            "name": inst.name,
            "country_code": inst.country_code,
            "address": inst.address,
            "verification_status": inst.verification_status.value if inst.verification_status else "pending",
        }
        for inst in installations
    ]

    declarant_data = {
        "name": org.name if org else "",
        "eori": "",  # Would come from organization settings
        "address": "",
        "country": org.country_code if org else "",
    }

    # Generate XML
    exporter = CBAMXMLExporter()
    xml_content = exporter.generate_quarterly_xml(
        report=report_data,
        imports=import_data,
        installations=installation_data,
        declarant=declarant_data,
    )

    filename = f"cbam_quarterly_report_{year}_Q{quarter}.xml"
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


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
            func.extract("month", CBAMImport.import_date).between(month_start, month_end),
        )
    )
    imports = imports_result.scalars().all()

    import_data = [
        {
            "id": str(imp.id),
            "cn_code": imp.cn_code,
            "sector": imp.sector.value if imp.sector else "unknown",
            "product_description": imp.product_description,
            "import_date": str(imp.import_date),
            "mass_tonnes": imp.net_mass_tonnes,
            "direct_see": imp.direct_see,
            "indirect_see": imp.indirect_see,
            "total_see": imp.total_see,
            "direct_emissions_tco2e": imp.direct_emissions_tco2e,
            "indirect_emissions_tco2e": imp.indirect_emissions_tco2e,
            "total_emissions_tco2e": imp.total_embedded_emissions_tco2e,
            "calculation_method": imp.calculation_method.value if imp.calculation_method else "default",
            "foreign_carbon_price_eur": imp.foreign_carbon_price_eur,
            "installation_id": str(imp.installation_id),
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
            CBAMQuarterlyReport.year == year,
            CBAMQuarterlyReport.quarter == quarter,
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
            func.extract("month", CBAMImport.import_date).between(month_start, month_end),
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

    # Convert to dicts
    report_data = {
        "year": report.year,
        "quarter": report.quarter,
        "status": report.status.value if report.status else "draft",
        "total_imports": report.total_imports,
        "total_mass_tonnes": report.total_mass_tonnes,
        "total_emissions_tco2e": report.total_emissions_tco2e,
        "by_sector": report.by_sector,
        "by_cn_code": report.by_cn_code,
        "submitted_at": report.submitted_at.isoformat() if report.submitted_at else None,
    }

    import_data = [
        {
            "direct_emissions_tco2e": float(imp.direct_emissions_tco2e or 0),
            "indirect_emissions_tco2e": float(imp.indirect_emissions_tco2e or 0),
            "calculation_method": imp.calculation_method.value if imp.calculation_method else "default",
        }
        for imp in imports
    ]

    installation_data = [
        {
            "id": str(inst.id),
            "name": inst.name,
            "country_code": inst.country_code,
            "sectors": inst.sectors or [],
            "verification_status": inst.verification_status.value if inst.verification_status else "pending",
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


@router.get("/reports/annual/{year}/export/xml")
async def export_annual_declaration_xml(
    year: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Export annual CBAM declaration as XML for EU Registry submission.
    """
    from fastapi.responses import Response
    from app.services.cbam_export import CBAMXMLExporter
    from app.models.core import Organization

    # Get the declaration
    result = await session.execute(
        select(CBAMAnnualDeclaration).where(
            CBAMAnnualDeclaration.organization_id == current_user.organization_id,
            CBAMAnnualDeclaration.year == year,
        )
    )
    declaration = result.scalar_one_or_none()

    if not declaration:
        raise HTTPException(status_code=404, detail="Declaration not found")

    # Get imports for this year
    imports_result = await session.execute(
        select(CBAMImport).where(
            CBAMImport.organization_id == current_user.organization_id,
            func.extract("year", CBAMImport.import_date) == year,
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

    # Convert to dicts
    declaration_data = {
        "year": declaration.year,
        "gross_emissions_tco2e": declaration.gross_emissions_tco2e,
        "deductions_tco2e": declaration.deductions_tco2e,
        "net_emissions_tco2e": declaration.net_emissions_tco2e,
        "certificates_required": declaration.certificates_required,
        "estimated_cost_eur": declaration.estimated_cost_eur,
        "by_sector": declaration.by_sector,
    }

    import_data = [
        {
            "id": str(imp.id),
            "cn_code": imp.cn_code,
            "mass_tonnes": imp.net_mass_tonnes,
            "total_emissions_tco2e": imp.total_embedded_emissions_tco2e,
        }
        for imp in imports
    ]

    installation_data = [
        {
            "id": str(inst.id),
            "name": inst.name,
            "country_code": inst.country_code,
        }
        for inst in installations
    ]

    declarant_data = {
        "name": org.name if org else "",
        "eori": "",
        "auth_number": "",
    }

    exporter = CBAMXMLExporter()
    xml_content = exporter.generate_annual_xml(
        declaration=declaration_data,
        imports=import_data,
        installations=installation_data,
        declarant=declarant_data,
    )

    filename = f"cbam_annual_declaration_{year}.xml"
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
