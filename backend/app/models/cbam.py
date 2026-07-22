"""
CBAM (Carbon Border Adjustment Mechanism) Models.

Implements EU Regulation 2023/956 for carbon pricing on imports.
Covers: Cement, Iron/Steel, Aluminium, Fertilisers, Electricity, Hydrogen.

Phases:
- Transitional (2023-2025): Quarterly reporting, no certificates
- Definitive (2026+): Annual declarations with certificate purchase
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    pass


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
    OTHER = "other"  # For products not clearly in a single sector


class CBAMCalculationMethod(str, Enum):
    """Method used to determine embedded emissions."""

    ACTUAL = "actual"  # Actual emissions from installation
    DEFAULT_VALUE = "default"  # EU default values per CN code
    EQUIVALENT = "equivalent"  # Equivalent method (third-country)


class CBAMReportStatus(str, Enum):
    """Status of CBAM quarterly/annual reports.

    Annual declarations (definitive regime) move draft -> ready; submission
    stays manual/on-hold until the CBAM Registry schema is validated.
    Stored as varchar (no native PG enum), so adding members is safe.
    """

    DRAFT = "draft"
    READY = "ready"
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
    default_see: Optional[Decimal] = Field(default=None)
    default_see_source: Optional[str] = Field(default=None, max_length=200)

    # Precursor products (for complex goods)
    has_precursors: bool = Field(default=False)
    precursor_cn_codes: Optional[List[str]] = Field(
        default=None, sa_column=Column(JSON)
    )

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
    installation_id_external: Optional[str] = Field(
        default=None, max_length=100
    )  # Third-country ID

    # Location
    country_code: str = Field(max_length=2, index=True)  # ISO 3166-1 alpha-2
    region: Optional[str] = Field(default=None, max_length=100)
    address: str = Field(max_length=500)
    coordinates_lat: Optional[Decimal] = Field(default=None)
    coordinates_lng: Optional[Decimal] = Field(default=None)

    # Operator information
    operator_name: str = Field(max_length=255)
    operator_contact_name: Optional[str] = Field(default=None, max_length=255)
    operator_contact_email: Optional[str] = Field(default=None, max_length=255)
    operator_contact_phone: Optional[str] = Field(default=None, max_length=50)

    # Production details
    sector: CBAMSector = Field(index=True)
    production_processes: Optional[List[str]] = Field(
        default=None, sa_column=Column(JSON)
    )
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
    verification_status: CBAMInstallationStatus = Field(
        default=CBAMInstallationStatus.UNVERIFIED
    )
    verified_at: Optional[datetime] = Field(default=None)
    verifier_name: Optional[str] = Field(default=None, max_length=255)
    verification_statement: Optional[str] = Field(default=None)

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Seeded by "Load sample data"; removed wholesale by DELETE /sample-data
    is_demo: bool = Field(default=False)

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
    reporting_period_id: Optional[UUID] = Field(
        default=None, foreign_key="reporting_periods.id", index=True
    )
    installation_id: Optional[UUID] = Field(
        default=None, foreign_key="cbam_installations.id"
    )

    # Import identification
    import_date: date = Field(index=True)
    customs_entry_number: Optional[str] = Field(default=None, max_length=50)
    customs_procedure: Optional[str] = Field(default=None, max_length=20)

    # Product details
    cn_code: str = Field(max_length=10, index=True)
    sector: Optional[CBAMSector] = Field(
        default=None, index=True
    )  # Derived from CN code
    product_description: str = Field(max_length=500)
    origin_country: str = Field(max_length=2, index=True)  # ISO country code

    # Quantities
    net_mass_kg: Decimal = Field()
    net_mass_tonnes: Decimal = Field()  # Calculated: kg / 1000
    supplementary_unit: Optional[str] = Field(
        default=None, max_length=20
    )  # MWh, m3, etc.
    supplementary_quantity: Optional[Decimal] = Field(default=None)

    # Embedded emissions
    direct_emissions_tco2e: Decimal = Field()
    indirect_emissions_tco2e: Optional[Decimal] = Field(default=None)
    total_embedded_emissions_tco2e: Decimal = Field()
    specific_embedded_emissions: Decimal = Field()  # tCO2e per tonne

    # Calculation details
    calculation_method: CBAMCalculationMethod = Field(
        default=CBAMCalculationMethod.DEFAULT_VALUE
    )
    default_value_used: bool = Field(default=False)
    direct_ef_used: Optional[Decimal] = Field(default=None)  # Emission factor used
    indirect_ef_used: Optional[Decimal] = Field(default=None)

    # Precursor emissions (for complex goods)
    precursor_emissions_tco2e: Optional[Decimal] = Field(default=None)
    precursor_details: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    # Carbon price deduction
    carbon_price_paid_eur: Optional[Decimal] = Field(default=None)
    carbon_price_country: Optional[str] = Field(default=None, max_length=2)
    carbon_price_mechanism: Optional[str] = Field(default=None, max_length=200)
    carbon_price_deduction_tco2e: Optional[Decimal] = Field(default=None)

    # Net emissions (after deduction)
    net_emissions_tco2e: Decimal = Field()

    # Source and quality
    data_source: str = Field(
        default="estimate", max_length=50
    )  # supplier, estimate, default
    data_quality_score: int = Field(default=5, ge=1, le=5)
    supporting_documents: Optional[List[str]] = Field(
        default=None, sa_column=Column(JSON)
    )

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = Field(default=None, foreign_key="users.id")
    updated_at: Optional[datetime] = Field(default=None)

    # Seeded by "Load sample data"; removed wholesale by DELETE /sample-data
    is_demo: bool = Field(default=False)

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
    total_mass_tonnes: Decimal = Field(default=Decimal(0))

    # Emissions by type
    total_direct_emissions_tco2e: Decimal = Field(default=Decimal(0))
    total_indirect_emissions_tco2e: Decimal = Field(default=Decimal(0))
    total_embedded_emissions_tco2e: Decimal = Field(default=Decimal(0))

    # Carbon price deductions
    total_carbon_price_deductions_tco2e: Decimal = Field(default=Decimal(0))
    total_net_emissions_tco2e: Decimal = Field(default=Decimal(0))

    # Breakdown by sector (JSON)
    by_sector: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    # {sector: {mass_tonnes, direct_tco2e, indirect_tco2e, import_count}}

    # Breakdown by country (JSON)
    by_country: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    # {country_code: {mass_tonnes, emissions_tco2e, import_count}}

    # Status
    status: CBAMReportStatus = Field(default=CBAMReportStatus.DRAFT)
    submitted_at: Optional[datetime] = Field(default=None)
    submission_reference: Optional[str] = Field(
        default=None, max_length=100
    )  # EU Registry ref
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
    Deadline: 30 September of the following year (Omnibus, Reg. (EU)
    2025/2083 — moved from the original 31 May). First: 30 Sep 2027.
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
    total_mass_tonnes: Decimal = Field(default=Decimal(0))
    total_embedded_emissions_tco2e: Decimal = Field(default=Decimal(0))

    # Carbon price deductions
    carbon_price_deductions_tco2e: Decimal = Field(default=Decimal(0))
    carbon_price_deductions_eur: Decimal = Field(default=Decimal(0))

    # Net emissions requiring certificates
    net_emissions_tco2e: Decimal = Field()

    # Certificate calculations
    certificates_required: int = Field(default=0)  # 1 certificate = 1 tCO2e
    certificates_purchased: int = Field(default=0)
    certificates_surrendered: int = Field(default=0)
    certificates_balance: int = Field(default=0)  # Surplus/deficit

    # Financial
    average_certificate_price_eur: Optional[Decimal] = Field(default=None)
    total_certificate_cost_eur: Decimal = Field(default=Decimal(0))
    total_liability_eur: Decimal = Field(default=Decimal(0))

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
# CBAM SUPPLIER DATA REQUESTS (Phase 3 — supplier portal)
# ============================================================================


def _data_request_default_expiry() -> datetime:
    """Supplier data requests expire 60 days after creation by default."""
    return datetime.utcnow() + timedelta(days=60)


class CBAMDataRequest(SQLModel, table=True):
    """
    A tokenized request for actual embedded-emissions data, sent by an EU
    importer to the operator of a non-EU installation.

    The supplier opens a public magic link ({frontend}/supplier-data/{token},
    no account needed) and submits per-CN-code specific embedded emissions
    (SEE). Submitted rows live in CBAMSupplierEmission and are preferred
    over Commission default values when building the annual declaration.

    `status` is a plain varchar (pending / submitted / expired) — no native
    PG enum, per the existing prod rule.
    """

    __tablename__ = "cbam_data_requests"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    installation_id: UUID = Field(foreign_key="cbam_installations.id", index=True)

    supplier_email: str = Field(max_length=255)
    token: str = Field(max_length=64, unique=True, index=True)
    status: str = Field(default="pending", max_length=20)  # pending/submitted/expired

    requested_by: Optional[UUID] = Field(default=None, foreign_key="users.id")
    message: Optional[str] = Field(default=None, max_length=2000)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = Field(default=None)
    expires_at: datetime = Field(default_factory=_data_request_default_expiry)


class CBAMSupplierEmission(SQLModel, table=True):
    """
    One per-CN-code actual-emissions row submitted by a supplier via a
    CBAMDataRequest magic link.

    Kept as a separate table (not JSON on the request) so the annual
    declaration builder can match rows by installation + CN-code prefix.
    Re-submission replaces the request's rows wholesale.
    """

    __tablename__ = "cbam_supplier_emissions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    request_id: UUID = Field(foreign_key="cbam_data_requests.id", index=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    installation_id: UUID = Field(foreign_key="cbam_installations.id", index=True)

    cn_code: str = Field(max_length=10, index=True)
    direct_see_tco2e_per_t: Decimal = Field()
    indirect_see_tco2e_per_t: Optional[Decimal] = Field(default=None)
    production_period_start: date = Field()
    production_period_end: date = Field()
    verifier_name: Optional[str] = Field(default=None, max_length=255)
    verified: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# CBAM CERTIFICATE LEDGER (Definitive Phase — purchases / surrenders)
# ============================================================================


class CBAMCertificateEntry(SQLModel, table=True):
    """
    One movement on the organization's CBAM certificate account.

    Definitive-regime certificate ledger: purchases on the central platform
    (sales open 1 Feb 2027, covering 2026 imports retroactively), surrenders
    with the annual declaration (due 30 September), and repurchases (excess
    certificates the Commission buys back on request — requests due by
    31 October). The ledger is the source of truth for the 50% quarterly
    holding check; `entry_type` is a plain varchar
    (purchase / surrender / repurchase) — no native PG enum, per the
    existing prod rule.
    """

    __tablename__ = "cbam_certificate_entries"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    entry_date: date = Field(index=True)
    entry_type: str = Field(max_length=20)  # purchase / surrender / repurchase
    quantity: int = Field(gt=0)  # certificates, 1 certificate = 1 tCO2e

    # Unit price actually paid/received (EUR per certificate); total is
    # stored so the ledger keeps the historical amount even if price
    # conventions change.
    unit_price_eur: Optional[Decimal] = Field(default=None)
    total_eur: Optional[Decimal] = Field(default=None)

    # For surrenders: the declaration year the certificates were
    # surrendered against (e.g. 2026 for the 30 Sep 2027 declaration).
    declaration_year: Optional[int] = Field(default=None, index=True)

    note: Optional[str] = Field(default=None, max_length=500)

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = Field(default=None, foreign_key="users.id")


# ============================================================================
# CBAM DEFAULT VALUES (Reference Data)
# ============================================================================


class CBAMDefaultValue(SQLModel, table=True):
    """
    EU Commission default emission values per CN code and origin country.

    Used when actual installation data is not available.
    Values are published by the EU Commission (definitive-period defaults
    published 13 Feb 2026, per CN code x origin country) and updated
    periodically. `country_code` is NULL for country-independent values
    (fallback row for a CN code / prefix).
    """

    __tablename__ = "cbam_default_values"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Product identification
    cn_code: str = Field(max_length=10, index=True)
    sector: CBAMSector = Field(index=True)
    product_description: str = Field(max_length=500)

    # Origin country (ISO 3166-1 alpha-2); NULL = applies to any country
    country_code: Optional[str] = Field(default=None, max_length=2, index=True)

    # Dataset versioning (e.g. year 2026, version "13-Feb-2026")
    dataset_year: Optional[int] = Field(default=None, index=True)
    dataset_version: Optional[str] = Field(default=None, max_length=50)

    # Default specific embedded emissions (tCO2e per tonne)
    direct_see: Decimal = Field()
    indirect_see: Optional[Decimal] = Field(default=None)
    total_see: Decimal = Field()

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
    grid_factor: Decimal = Field()

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
    price_eur: Decimal = Field()

    # Source
    source: str = Field(default="EU Commission", max_length=100)
    source_url: Optional[str] = Field(default=None, max_length=500)

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
