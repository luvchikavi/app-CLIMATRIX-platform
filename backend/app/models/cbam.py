"""
CBAM (Carbon Border Adjustment Mechanism) Models.

Implements EU Regulation 2023/956 for carbon pricing on imports.
Covers: Cement, Iron/Steel, Aluminium, Fertilisers, Electricity, Hydrogen.

Phases:
- Transitional (2023-2025): Quarterly reporting, no certificates
- Definitive (2026+): Annual declarations with certificate purchase
"""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from app.models.core import Organization, ReportingPeriod


# ============================================================================
# ENUMS
# ============================================================================

class CBAMSector(str, Enum):
    """CBAM covered sectors per Annex I."""
    CEMENT = "cement"
    IRON_STEEL = "iron_steel"
    ALUMINIUM = "aluminium"
    FERTILISER = "fertiliser"
    ELECTRICITY = "electricity"
    HYDROGEN = "hydrogen"


class CBAMCalculationMethod(str, Enum):
    """Method used to determine embedded emissions."""
    ACTUAL = "actual"              # Actual emissions from installation
    DEFAULT_VALUE = "default"      # EU default values per CN code
    EQUIVALENT = "equivalent"      # Equivalent method (third-country)


class CBAMReportStatus(str, Enum):
    """Status of CBAM quarterly/annual reports."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REVISION = "revision"


class CBAMInstallationStatus(str, Enum):
    """Verification status of installation data."""
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"


# ============================================================================
# CBAM PRODUCT (Reference Data - CN Codes)
# ============================================================================

class CBAMProduct(SQLModel, table=True):
    """
    Products covered by CBAM per EU Combined Nomenclature (CN) codes.

    Reference table populated from EU Commission data.
    Maps CN codes to sectors and emission calculation requirements.
    """
    __tablename__ = "cbam_products"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # CN Code identification
    cn_code: str = Field(max_length=10, index=True)  # 4-digit or 8-digit
    cn_code_full: str = Field(max_length=12)  # Full 8-digit with spaces
    description: str = Field(max_length=500)

    # Sector classification
    sector: CBAMSector = Field(index=True)
    aggregated_category: str = Field(max_length=100)  # Per CBAM Annex I

    # Emission requirements
    direct_emissions_required: bool = Field(default=True)
    indirect_emissions_required: bool = Field(default=False)  # Only cement/fertiliser

    # Default emission value (tCO2e per tonne)
    default_see: Optional[Decimal] = Field(default=None, decimal_places=6)
    default_see_source: Optional[str] = Field(default=None, max_length=200)

    # Precursor products (for complex goods)
    has_precursors: bool = Field(default=False)
    precursor_cn_codes: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))

    # Validity
    is_active: bool = Field(default=True)
    valid_from: date = Field(default_factory=date.today)
    valid_until: Optional[date] = Field(default=None)


# ============================================================================
# CBAM INSTALLATION (Non-EU Production Facilities)
# ============================================================================

class CBAMInstallation(SQLModel, table=True):
    """
    Non-EU production installations that export CBAM goods.

    Represents the facility where CBAM-covered products are manufactured.
    Installation data comes from suppliers and is subject to verification.
    """
    __tablename__ = "cbam_installations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Installation identification
    name: str = Field(max_length=255)
    installation_id_external: Optional[str] = Field(default=None, max_length=100)  # Third-country ID

    # Location
    country_code: str = Field(max_length=2, index=True)  # ISO 3166-1 alpha-2
    region: Optional[str] = Field(default=None, max_length=100)
    address: str = Field(max_length=500)
    coordinates_lat: Optional[Decimal] = Field(default=None, decimal_places=6)
    coordinates_lng: Optional[Decimal] = Field(default=None, decimal_places=6)

    # Operator information
    operator_name: str = Field(max_length=255)
    operator_contact_name: Optional[str] = Field(default=None, max_length=255)
    operator_contact_email: Optional[str] = Field(default=None, max_length=255)
    operator_contact_phone: Optional[str] = Field(default=None, max_length=50)

    # Production details
    sector: CBAMSector = Field(index=True)
    production_processes: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    annual_production_capacity_tonnes: Optional[Decimal] = Field(default=None)

    # Emissions data (if actual data available)
    direct_emissions_intensity: Optional[Decimal] = Field(default=None)  # tCO2e/tonne
    indirect_emissions_intensity: Optional[Decimal] = Field(default=None)
    electricity_consumption_mwh_per_tonne: Optional[Decimal] = Field(default=None)
    grid_emission_factor: Optional[Decimal] = Field(default=None)  # tCO2e/MWh

    # Third-country carbon pricing
    carbon_price_paid: Optional[Decimal] = Field(default=None)  # EUR per tCO2e
    carbon_price_mechanism: Optional[str] = Field(default=None, max_length=200)

    # Verification
    verification_status: CBAMInstallationStatus = Field(default=CBAMInstallationStatus.UNVERIFIED)
    verified_at: Optional[datetime] = Field(default=None)
    verifier_name: Optional[str] = Field(default=None, max_length=255)
    verification_statement: Optional[str] = Field(default=None)

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relationships
    imports: List["CBAMImport"] = Relationship(back_populates="installation")


# ============================================================================
# CBAM IMPORT (Individual Import Declarations)
# ============================================================================

class CBAMImport(SQLModel, table=True):
    """
    Individual import of CBAM goods.

    Each record represents a single import declaration/customs entry.
    Contains embedded emissions calculation and carbon price deductions.
    """
    __tablename__ = "cbam_imports"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    reporting_period_id: UUID = Field(foreign_key="reporting_periods.id", index=True)
    installation_id: Optional[UUID] = Field(default=None, foreign_key="cbam_installations.id")

    # Import identification
    import_date: date = Field(index=True)
    customs_entry_number: Optional[str] = Field(default=None, max_length=50)
    customs_procedure: Optional[str] = Field(default=None, max_length=20)

    # Product details
    cn_code: str = Field(max_length=10, index=True)
    product_description: str = Field(max_length=500)
    origin_country: str = Field(max_length=2, index=True)  # ISO country code

    # Quantities
    net_mass_kg: Decimal = Field(decimal_places=2)
    net_mass_tonnes: Decimal = Field(decimal_places=4)  # Calculated: kg / 1000
    supplementary_unit: Optional[str] = Field(default=None, max_length=20)  # MWh, m3, etc.
    supplementary_quantity: Optional[Decimal] = Field(default=None)

    # Embedded emissions
    direct_emissions_tco2e: Decimal = Field(decimal_places=6)
    indirect_emissions_tco2e: Optional[Decimal] = Field(default=None, decimal_places=6)
    total_embedded_emissions_tco2e: Decimal = Field(decimal_places=6)
    specific_embedded_emissions: Decimal = Field(decimal_places=6)  # tCO2e per tonne

    # Calculation details
    calculation_method: CBAMCalculationMethod = Field(default=CBAMCalculationMethod.DEFAULT_VALUE)
    default_value_used: bool = Field(default=False)
    direct_ef_used: Optional[Decimal] = Field(default=None)  # Emission factor used
    indirect_ef_used: Optional[Decimal] = Field(default=None)

    # Precursor emissions (for complex goods)
    precursor_emissions_tco2e: Optional[Decimal] = Field(default=None, decimal_places=6)
    precursor_details: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    # Carbon price deduction
    carbon_price_paid_eur: Optional[Decimal] = Field(default=None, decimal_places=2)
    carbon_price_country: Optional[str] = Field(default=None, max_length=2)
    carbon_price_mechanism: Optional[str] = Field(default=None, max_length=200)
    carbon_price_deduction_tco2e: Optional[Decimal] = Field(default=None, decimal_places=6)

    # Net emissions (after deduction)
    net_emissions_tco2e: Decimal = Field(decimal_places=6)

    # Source and quality
    data_source: str = Field(default="estimate", max_length=50)  # supplier, estimate, default
    data_quality_score: int = Field(default=5, ge=1, le=5)
    supporting_documents: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = Field(default=None, foreign_key="users.id")
    updated_at: Optional[datetime] = Field(default=None)

    # Relationships
    installation: Optional[CBAMInstallation] = Relationship(back_populates="imports")


# ============================================================================
# CBAM QUARTERLY REPORT (Transitional Phase 2024-2025)
# ============================================================================

class CBAMQuarterlyReport(SQLModel, table=True):
    """
    Quarterly CBAM report for transitional phase.

    Required: Q1 2024 - Q4 2025
    Deadline: End of month following quarter (e.g., Q1 due April 30)
    Submitted to: EU CBAM Transitional Registry
    """
    __tablename__ = "cbam_quarterly_reports"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Reporting period
    reporting_year: int = Field(index=True)
    reporting_quarter: int = Field(ge=1, le=4)  # 1, 2, 3, 4
    period_start: date
    period_end: date
    submission_deadline: date

    # Aggregated totals
    total_imports_count: int = Field(default=0)
    total_mass_tonnes: Decimal = Field(default=Decimal(0), decimal_places=2)

    # Emissions by type
    total_direct_emissions_tco2e: Decimal = Field(default=Decimal(0), decimal_places=2)
    total_indirect_emissions_tco2e: Decimal = Field(default=Decimal(0), decimal_places=2)
    total_embedded_emissions_tco2e: Decimal = Field(default=Decimal(0), decimal_places=2)

    # Carbon price deductions
    total_carbon_price_deductions_tco2e: Decimal = Field(default=Decimal(0), decimal_places=2)
    total_net_emissions_tco2e: Decimal = Field(default=Decimal(0), decimal_places=2)

    # Breakdown by sector (JSON)
    by_sector: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    # {sector: {mass_tonnes, direct_tco2e, indirect_tco2e, import_count}}

    # Breakdown by country (JSON)
    by_country: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    # {country_code: {mass_tonnes, emissions_tco2e, import_count}}

    # Status
    status: CBAMReportStatus = Field(default=CBAMReportStatus.DRAFT)
    submitted_at: Optional[datetime] = Field(default=None)
    submission_reference: Optional[str] = Field(default=None, max_length=100)  # EU Registry ref
    accepted_at: Optional[datetime] = Field(default=None)
    rejection_reason: Optional[str] = Field(default=None)

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    submitted_by: Optional[UUID] = Field(default=None, foreign_key="users.id")


# ============================================================================
# CBAM ANNUAL DECLARATION (Definitive Phase from 2026)
# ============================================================================

class CBAMAnnualDeclaration(SQLModel, table=True):
    """
    Annual CBAM declaration for definitive phase.

    Required: From 2026 onwards
    Deadline: May 31 of following year
    Requires: Purchase and surrender of CBAM certificates
    """
    __tablename__ = "cbam_annual_declarations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Reporting period
    reporting_year: int = Field(index=True)
    period_start: date
    period_end: date
    submission_deadline: date

    # Aggregated emissions
    total_imports_count: int = Field(default=0)
    total_mass_tonnes: Decimal = Field(default=Decimal(0), decimal_places=2)
    total_embedded_emissions_tco2e: Decimal = Field(default=Decimal(0), decimal_places=2)

    # Carbon price deductions
    carbon_price_deductions_tco2e: Decimal = Field(default=Decimal(0), decimal_places=2)
    carbon_price_deductions_eur: Decimal = Field(default=Decimal(0), decimal_places=2)

    # Net emissions requiring certificates
    net_emissions_tco2e: Decimal = Field(decimal_places=2)

    # Certificate calculations
    certificates_required: int = Field(default=0)  # 1 certificate = 1 tCO2e
    certificates_purchased: int = Field(default=0)
    certificates_surrendered: int = Field(default=0)
    certificates_balance: int = Field(default=0)  # Surplus/deficit

    # Financial
    average_certificate_price_eur: Optional[Decimal] = Field(default=None, decimal_places=2)
    total_certificate_cost_eur: Decimal = Field(default=Decimal(0), decimal_places=2)
    total_liability_eur: Decimal = Field(default=Decimal(0), decimal_places=2)

    # Breakdown by sector
    by_sector: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    # Status
    status: CBAMReportStatus = Field(default=CBAMReportStatus.DRAFT)
    submitted_at: Optional[datetime] = Field(default=None)
    submission_reference: Optional[str] = Field(default=None, max_length=100)
    verified_at: Optional[datetime] = Field(default=None)
    verifier_name: Optional[str] = Field(default=None, max_length=255)
    verification_statement: Optional[str] = Field(default=None)

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    submitted_by: Optional[UUID] = Field(default=None, foreign_key="users.id")


# ============================================================================
# CBAM DEFAULT VALUES (Reference Data)
# ============================================================================

class CBAMDefaultValue(SQLModel, table=True):
    """
    EU Commission default emission values per CN code.

    Used when actual installation data is not available.
    Values are published by EU and updated periodically.
    """
    __tablename__ = "cbam_default_values"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Product identification
    cn_code: str = Field(max_length=10, index=True)
    sector: CBAMSector = Field(index=True)
    product_description: str = Field(max_length=500)

    # Default specific embedded emissions (tCO2e per tonne)
    direct_see: Decimal = Field(decimal_places=6)
    indirect_see: Optional[Decimal] = Field(default=None, decimal_places=6)
    total_see: Decimal = Field(decimal_places=6)

    # Source and validity
    source: str = Field(max_length=200)  # "EU Commission Implementing Regulation..."
    source_reference: Optional[str] = Field(default=None, max_length=100)
    valid_from: date
    valid_until: Optional[date] = Field(default=None)

    # Status
    is_active: bool = Field(default=True)


# ============================================================================
# CBAM GRID EMISSION FACTORS (Third-Country Electricity)
# ============================================================================

class CBAMGridFactor(SQLModel, table=True):
    """
    Grid emission factors for third countries.

    Used for calculating indirect emissions when importing
    goods with significant electricity consumption (cement, fertiliser).
    """
    __tablename__ = "cbam_grid_factors"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Country
    country_code: str = Field(max_length=2, unique=True, index=True)
    country_name: str = Field(max_length=100)

    # Emission factor (tCO2e per MWh)
    grid_factor: Decimal = Field(decimal_places=6)

    # Source and validity
    source: str = Field(max_length=200)
    year: int
    valid_from: date
    valid_until: Optional[date] = Field(default=None)

    # Status
    is_active: bool = Field(default=True)


# ============================================================================
# EU ETS PRICE (For Certificate Cost Calculation)
# ============================================================================

class EUETSPrice(SQLModel, table=True):
    """
    Weekly EU ETS carbon price.

    CBAM certificate prices are linked to EU ETS prices.
    Updated weekly by EU Commission.
    """
    __tablename__ = "eu_ets_prices"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Week identification
    price_date: date = Field(unique=True, index=True)  # Usually Wednesday
    week_number: int
    year: int

    # Price (EUR per tCO2e)
    price_eur: Decimal = Field(decimal_places=2)

    # Source
    source: str = Field(default="EU Commission", max_length=100)
    source_url: Optional[str] = Field(default=None, max_length=500)

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
