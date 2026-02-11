"""
Emission-related models: EmissionFactor, Activity, Emission, UnitConversion.
These handle the core GHG calculation functionality.
"""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String as SAString
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from app.models.core import Organization, Site, ReportingPeriod, User


class CalculationMethod(str, Enum):
    """Method used for emission calculation."""
    ACTIVITY = "activity"      # Physical quantity (liters, kWh, km)
    SPEND = "spend"            # Monetary spend (USD, EUR)
    DISTANCE = "distance"      # Distance-based (km, miles)
    SUPPLIER = "supplier"      # Supplier-specific data


class DataSource(str, Enum):
    """Source of activity data."""
    MANUAL = "manual"
    IMPORT = "import"
    API = "api"


class ConfidenceLevel(str, Enum):
    """Confidence level of emission calculation."""
    HIGH = "high"        # Exact factor match
    MEDIUM = "medium"    # Regional or similar factor
    LOW = "low"          # Global average or proxy


class ImportBatchStatus(str, Enum):
    """Status of an import batch."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some rows failed


class EmissionFactorStatus(str, Enum):
    """Status of an emission factor in the approval workflow."""
    DRAFT = "draft"                    # New or edited, not yet submitted
    PENDING_APPROVAL = "pending"       # Submitted for approval
    APPROVED = "approved"              # Approved and active for calculations
    REJECTED = "rejected"              # Rejected by admin
    ARCHIVED = "archived"              # Replaced by newer version


class DataQualityScore(int, Enum):
    """
    Data quality score based on PCAF methodology (1=best, 5=worst).

    Score 1: Audited/verified data from primary sources
             - Audited energy bills, verified supplier data
    Score 2: Non-audited data from primary sources
             - Unaudited utility bills, supplier invoices
    Score 3: Physical activity data with average emission factors
             - Measured km driven with average fuel efficiency
    Score 4: Economic activity-based modeling
             - Spend-based calculations, revenue proxies
    Score 5: Estimated data with high uncertainty
             - Industry averages, EEIO models, extrapolations
    """
    VERIFIED = 1
    PRIMARY = 2
    ACTIVITY_AVERAGE = 3
    SPEND_BASED = 4
    ESTIMATED = 5


# ============================================================================
# IMPORT BATCH (Track Uploaded Files)
# ============================================================================

class ImportBatch(SQLModel, table=True):
    """
    Track imported files for audit and review.

    Each Excel/CSV upload creates an ImportBatch.
    Activities created from that file reference this batch.
    """
    __tablename__ = "import_batches"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    reporting_period_id: UUID = Field(foreign_key="reporting_periods.id", index=True)

    # File info
    file_name: str = Field(max_length=255)
    file_type: str = Field(max_length=50)  # "excel", "csv"
    file_size_bytes: Optional[int] = Field(default=None)

    # Processing status
    status: ImportBatchStatus = Field(default=ImportBatchStatus.PENDING)

    # Row counts
    total_rows: int = Field(default=0)
    successful_rows: int = Field(default=0)
    failed_rows: int = Field(default=0)
    skipped_rows: int = Field(default=0)

    # Error tracking
    error_message: Optional[str] = Field(default=None, max_length=1000)
    row_errors: Optional[list] = Field(default=None, sa_column=Column(JSON))  # [{row: 5, error: "..."}]

    # Audit
    uploaded_by: UUID = Field(foreign_key="users.id")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    # Relationships
    activities: list["Activity"] = Relationship(back_populates="import_batch")


# ============================================================================
# EMISSION FACTOR (Reference Data - Single Source of Truth)
# ============================================================================

class EmissionFactorBase(SQLModel):
    """Base fields for EmissionFactor."""
    # Classification
    scope: int = Field(ge=1, le=3, index=True)
    category_code: str = Field(max_length=10, index=True)  # "1.1", "2", "3.5"
    subcategory: Optional[str] = Field(default=None, max_length=100)

    # Factor Identification - THE KEY FIELD
    activity_key: str = Field(max_length=100, index=True)  # "natural_gas_volume", "diesel_km"
    display_name: str = Field(max_length=255)

    # Factor Values (AR6 GWP by default)
    co2_factor: Optional[Decimal] = Field(default=None)
    ch4_factor: Optional[Decimal] = Field(default=None)
    n2o_factor: Optional[Decimal] = Field(default=None)
    co2e_factor: Decimal

    # Units
    activity_unit: str = Field(max_length=50)   # "liters", "kWh", "km", "USD"
    factor_unit: str = Field(max_length=50)     # "kg CO2e/liter"

    # Metadata
    source: str = Field(max_length=100)         # "DEFRA_2024", "EPA_2024", "EEIO"
    region: str = Field(default="Global", max_length=50, index=True)
    year: int = Field(index=True)

    # Notes (optional documentation)
    notes: Optional[str] = Field(default=None, max_length=1000)

    # Validity
    is_active: bool = Field(default=True)


class EmissionFactor(EmissionFactorBase, table=True):
    """
    Master emission factor registry.
    Single source of truth for all emission factors.

    Uses explicit activity_key instead of fuzzy matching.

    Governance: Only factors with status='approved' are used in calculations.
    Changes require approval workflow.
    """
    __tablename__ = "emission_factors"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # WTT Link (self-referential for Well-to-Tank factors)
    wtt_factor_id: Optional[UUID] = Field(
        default=None,
        foreign_key="emission_factors.id"
    )

    # Validity dates
    valid_from: Optional[date] = Field(default=None)
    valid_until: Optional[date] = Field(default=None)

    # ===========================================
    # GOVERNANCE FIELDS
    # ===========================================

    # Approval Status (only 'approved' factors are used in calculations)
    # Use sa_column with String to avoid native PostgreSQL ENUM type mismatch
    status: str = Field(
        default="approved",
        sa_column=Column("status", SAString(20), default="approved", index=True),
    )

    # Version Control (for tracking changes)
    version: int = Field(default=1)
    previous_version_id: Optional[UUID] = Field(
        default=None,
        foreign_key="emission_factors.id"
    )

    # Change Tracking
    change_reason: Optional[str] = Field(default=None, max_length=500)

    # Approval Workflow
    submitted_at: Optional[datetime] = Field(default=None)
    submitted_by_id: Optional[UUID] = Field(default=None, foreign_key="users.id")
    approved_at: Optional[datetime] = Field(default=None)
    approved_by_id: Optional[UUID] = Field(default=None, foreign_key="users.id")
    rejected_at: Optional[datetime] = Field(default=None)
    rejected_by_id: Optional[UUID] = Field(default=None, foreign_key="users.id")
    rejection_reason: Optional[str] = Field(default=None, max_length=500)

    # ===========================================
    # AUDIT FIELDS
    # ===========================================
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_id: Optional[UUID] = Field(default=None, foreign_key="users.id")
    updated_at: Optional[datetime] = Field(default=None)
    updated_by_id: Optional[UUID] = Field(default=None, foreign_key="users.id")

    class Config:
        # Ensure unique constraint on (activity_key, region, year)
        pass


# ============================================================================
# UNIT CONVERSION (Database-Driven)
# ============================================================================

class UnitConversionBase(SQLModel):
    """Base fields for UnitConversion."""
    from_unit: str = Field(max_length=50)
    to_unit: str = Field(max_length=50)
    multiplier: Decimal
    category: Optional[str] = Field(default=None, max_length=50)  # "volume", "mass", "distance", "energy"


class UnitConversion(UnitConversionBase, table=True):
    """
    Unit conversion factors.
    Used to convert user input to factor-expected units.
    """
    __tablename__ = "unit_conversions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)


# ============================================================================
# FUEL PRICE (For Spend → Quantity Conversion)
# ============================================================================

class FuelPrice(SQLModel, table=True):
    """
    Fuel prices for converting monetary spend to physical quantity.

    Used in Scope 1 calculations when user provides spend instead of quantity.
    Formula: quantity = spend_amount / price_per_unit

    Sources:
    - EIA (US Energy Information Administration) for US prices
    - BEIS/DESNZ for UK prices
    - IEC (Israel Electric Corporation) for Israel prices
    """
    __tablename__ = "fuel_prices"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Fuel identification
    fuel_type: str = Field(max_length=50, index=True)  # diesel, petrol, natural_gas, lpg, electricity

    # Price information
    price_per_unit: Decimal  # e.g., 1.50
    currency: str = Field(max_length=3)  # USD, EUR, GBP, ILS
    unit: str = Field(max_length=20)  # liter, gallon, m3, kWh, therm

    # Regional/temporal scope
    region: str = Field(max_length=50, index=True)  # US, UK, IL, EU, Global

    # Validity period
    valid_from: date
    valid_until: Optional[date] = Field(default=None)

    # Source tracking
    source: str = Field(max_length=200)  # "EIA Weekly Retail Prices Q4 2024"
    source_url: Optional[str] = Field(default=None, max_length=500)

    # Status
    is_active: bool = Field(default=True)

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)


# ============================================================================
# ACTIVITY (User Input)
# ============================================================================

class ActivityBase(SQLModel):
    """Base fields for Activity."""
    # GHG Classification
    scope: int = Field(ge=1, le=3)
    category_code: str = Field(max_length=10)

    # Activity Details
    description: str = Field(default="", max_length=500)  # Optional - activity type is descriptive enough
    activity_key: str = Field(max_length=100, index=True)  # Links to EmissionFactor

    # Quantity & Unit
    quantity: Decimal
    unit: str = Field(max_length=50)

    # Method
    calculation_method: CalculationMethod = Field(default=CalculationMethod.ACTIVITY)

    # Date
    activity_date: date


class Activity(ActivityBase, table=True):
    """
    Activity data entered by users.
    Each activity results in one emission calculation.
    """
    __tablename__ = "activities"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    reporting_period_id: UUID = Field(foreign_key="reporting_periods.id", index=True)
    site_id: Optional[UUID] = Field(default=None, foreign_key="sites.id")

    # Source Tracking
    data_source: DataSource = Field(default=DataSource.MANUAL)
    import_batch_id: Optional[UUID] = Field(default=None, foreign_key="import_batches.id", index=True)

    # Data Quality (PCAF methodology: 1=best, 5=worst)
    data_quality_score: int = Field(default=5, ge=1, le=5)  # Default to estimated (most conservative)
    data_quality_justification: Optional[str] = Field(default=None, max_length=500)
    supporting_document_url: Optional[str] = Field(default=None, max_length=500)

    # Audit
    created_by: Optional[UUID] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relationships
    reporting_period: "ReportingPeriod" = Relationship(back_populates="activities")
    site: Optional["Site"] = Relationship(back_populates="activities")
    emission: Optional["Emission"] = Relationship(back_populates="activity")
    import_batch: Optional["ImportBatch"] = Relationship(back_populates="activities")


# ============================================================================
# EMISSION (Calculated Result)
# ============================================================================

class Emission(SQLModel, table=True):
    """
    Calculated emission for an activity.
    One-to-one relationship with Activity.
    """
    __tablename__ = "emissions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    activity_id: UUID = Field(foreign_key="activities.id", unique=True, index=True)

    # Link to Factor Used (nullable for supplier-specific factors)
    emission_factor_id: Optional[UUID] = Field(default=None, foreign_key="emission_factors.id")

    # Calculated Values (in kg)
    co2_kg: Optional[Decimal] = Field(default=None)
    ch4_kg: Optional[Decimal] = Field(default=None)
    n2o_kg: Optional[Decimal] = Field(default=None)
    co2e_kg: Decimal

    # WTT (Scope 3.3) - Auto-calculated
    wtt_co2e_kg: Optional[Decimal] = Field(default=None)

    # Calculation Details
    converted_quantity: Optional[Decimal] = Field(default=None)
    converted_unit: Optional[str] = Field(default=None, max_length=50)
    formula: Optional[str] = Field(default=None, max_length=500)

    # Quality Indicators
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.HIGH)
    resolution_strategy: Optional[str] = Field(default="exact", max_length=50)  # exact, region, global
    needs_review: bool = Field(default=False)
    warnings: Optional[list] = Field(default=None, sa_column=Column(JSON))

    # Audit
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    recalculated_at: Optional[datetime] = Field(default=None)

    # Relationships
    activity: Activity = Relationship(back_populates="emission")


# ============================================================================
# AIRPORT DATABASE (For Flight Distance Calculations - Category 3.6)
# ============================================================================

class Airport(SQLModel, table=True):
    """
    Airport reference data for flight distance calculations.

    Used in Category 3.6 Business Travel to calculate:
    1. Great circle distance between airports
    2. Apply 9% uplift for non-direct routing
    3. Determine short-haul vs long-haul threshold (3,700 km)

    Sources:
    - IATA (International Air Transport Association)
    - OpenFlights database
    """
    __tablename__ = "airports"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Airport identification
    iata_code: str = Field(max_length=3, unique=True, index=True)  # TLV, LHR, JFK
    icao_code: Optional[str] = Field(default=None, max_length=4)  # LLBG, EGLL, KJFK
    name: str = Field(max_length=255)  # Ben Gurion International Airport

    # Location
    city: str = Field(max_length=100)  # Tel Aviv
    country_code: str = Field(max_length=2, index=True)  # IL, GB, US
    country_name: str = Field(max_length=100)  # Israel

    # Coordinates (for Haversine distance calculation)
    latitude: Decimal = Field(decimal_places=6)   # 32.0094
    longitude: Decimal = Field(decimal_places=6)  # 34.8808

    # Timezone (for reference)
    timezone: Optional[str] = Field(default=None, max_length=50)  # Asia/Jerusalem

    # Metadata
    is_active: bool = Field(default=True)

    class Config:
        pass


# ============================================================================
# TRANSPORT DISTANCE MATRIX (For Category 3.4 Default Distances)
# ============================================================================

class TransportDistanceMatrix(SQLModel, table=True):
    """
    Default transport distances between regions/countries.

    Used in Category 3.4 Upstream Transportation when client knows:
    - Origin country (e.g., China)
    - Weight of goods
    - But NOT exact factory location or shipping route

    Distances include:
    - Default land distance to/from ports (500 km each end)
    - Sea distance between major ports

    Sources:
    - Sea distances: Sea-distances.org, UNCTAD
    - Land distances: Regional averages
    """
    __tablename__ = "transport_distance_matrix"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Route identification
    origin_country: str = Field(max_length=2, index=True)  # CN, IN, TR
    origin_region: Optional[str] = Field(default=None, max_length=50)  # Asia, Europe
    destination_country: str = Field(max_length=2, index=True)  # IL, GB, US
    destination_region: Optional[str] = Field(default=None, max_length=50)

    # Distance components (in km)
    origin_land_km: int = Field(default=500)  # Factory → Origin port (default 500)
    sea_distance_km: int  # Port → Port
    destination_land_km: int = Field(default=100)  # Destination port → Company

    # Total distance
    total_distance_km: int  # Sum of all legs

    # Primary transport mode for sea leg
    transport_mode: str = Field(default="sea_container", max_length=50)  # sea_container, sea_bulk, air

    # Alternative modes (if available)
    air_distance_km: Optional[int] = Field(default=None)  # For air freight option
    rail_distance_km: Optional[int] = Field(default=None)  # For rail freight (e.g., China-EU)

    # Source and notes
    source: str = Field(max_length=200)
    notes: Optional[str] = Field(default=None, max_length=500)

    # Validity
    is_active: bool = Field(default=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# CURRENCY CONVERSION (For Spend-Based Calculations)
# ============================================================================

class CurrencyConversion(SQLModel, table=True):
    """
    Currency conversion rates for spend-based calculations.

    EEIO factors are typically in USD, so we need to convert
    user input in local currencies (EUR, GBP, ILS) to USD.

    Sources:
    - European Central Bank
    - OECD rates (for annual averages)
    """
    __tablename__ = "currency_conversions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Currency identification
    from_currency: str = Field(max_length=3, index=True)  # EUR, GBP, ILS
    to_currency: str = Field(max_length=3, default="USD")  # Always USD for EEIO

    # Conversion rate
    rate: Decimal = Field(decimal_places=6)  # 1 EUR = 1.08 USD

    # Validity period
    valid_from: date = Field(index=True)
    valid_until: Optional[date] = Field(default=None)

    # Source
    source: str = Field(max_length=100)  # "ECB", "OECD"
    rate_type: str = Field(default="annual_average", max_length=50)  # annual_average, spot

    # Status
    is_active: bool = Field(default=True)


# ============================================================================
# PRICE RANGE VALIDATION (For Data Quality Checks)
# ============================================================================

class PriceRange(SQLModel, table=True):
    """
    Expected price ranges for validation.

    Used to flag potential data entry errors when:
    - User enters spend but implied price per unit is unrealistic
    - E.g., $1,000,000 for 100 kg of plastic → $10,000/kg (flag error)

    Sources:
    - Market prices for common materials
    - Industry averages
    """
    __tablename__ = "price_ranges"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Material/activity identification
    material_type: str = Field(max_length=100, index=True)  # plastic, steel, aluminum
    activity_category: str = Field(max_length=10)  # 3.1, 3.2

    # Price range (per unit)
    min_price_usd: Decimal  # Minimum expected price per unit
    max_price_usd: Decimal  # Maximum expected price per unit
    typical_price_usd: Decimal  # Typical/median price per unit
    unit: str = Field(max_length=50)  # kg, unit, liter

    # Regional variation
    region: str = Field(default="Global", max_length=50)

    # Source and validity
    source: str = Field(max_length=200)
    valid_year: int
    is_active: bool = Field(default=True)


# ============================================================================
# HOTEL EMISSION FACTORS BY COUNTRY (For Category 3.6)
# ============================================================================

class HotelEmissionFactor(SQLModel, table=True):
    """
    Country-specific hotel emission factors.

    Hotel emissions vary significantly by country based on:
    - Grid electricity carbon intensity
    - Climate (heating/cooling needs)
    - Building efficiency standards

    Sources:
    - DEFRA UK Government GHG Conversion Factors
    - EPA for US
    - CRREM for European countries
    """
    __tablename__ = "hotel_emission_factors"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Location
    country_code: str = Field(max_length=2, index=True)  # GB, US, IL
    country_name: str = Field(max_length=100)

    # Emission factor
    co2e_per_night: Decimal  # kg CO2e per room-night

    # Breakdown (optional)
    electricity_kwh_per_night: Optional[Decimal] = Field(default=None)
    heating_kwh_per_night: Optional[Decimal] = Field(default=None)
    water_liters_per_night: Optional[Decimal] = Field(default=None)

    # Source and year
    source: str = Field(max_length=100)
    year: int

    # Validity
    is_active: bool = Field(default=True)


# ============================================================================
# GRID EMISSION FACTORS BY COUNTRY (For Scope 2 & 3.3)
# ============================================================================

class GridEmissionFactor(SQLModel, table=True):
    """
    Country-specific grid electricity emission factors.

    Used in:
    - Scope 2: Purchased electricity
    - Scope 3.3: T&D losses
    - Scope 3.8: Leased assets (if electricity-based)

    Provides both location-based and market-based factors.

    Sources:
    - IEA (International Energy Agency) - Global coverage
    - EPA eGRID - US regional factors
    - DEFRA - UK factors
    - Israel Electric Corporation - Israel factors
    """
    __tablename__ = "grid_emission_factors"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Location
    country_code: str = Field(max_length=2, index=True)
    country_name: str = Field(max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)  # For US subgrids

    # Location-based factor (average grid mix)
    location_factor: Decimal  # kg CO2e/kWh

    # Market-based factor (residual mix for RE certificates)
    market_factor: Optional[Decimal] = Field(default=None)  # kg CO2e/kWh

    # Breakdown by gas (optional)
    co2_factor: Optional[Decimal] = Field(default=None)
    ch4_factor: Optional[Decimal] = Field(default=None)
    n2o_factor: Optional[Decimal] = Field(default=None)

    # T&D losses (for Category 3.3)
    td_loss_factor: Optional[Decimal] = Field(default=None)  # kg CO2e/kWh lost in transmission
    td_loss_percentage: Optional[Decimal] = Field(default=None)  # % of electricity lost

    # Source and year
    source: str = Field(max_length=100)  # IEA, eGRID, DEFRA
    year: int = Field(index=True)

    # Validity
    is_active: bool = Field(default=True)


# ============================================================================
# REFRIGERANT GWP VALUES (For Scope 1.3)
# ============================================================================

class RefrigerantGWP(SQLModel, table=True):
    """
    Global Warming Potential values for refrigerants.

    Used in Scope 1.3 Fugitive Emissions for calculating
    CO2e from refrigerant leakage.

    GWP values from IPCC AR6 (2021) unless otherwise noted.

    Formula: CO2e = leaked_mass_kg × GWP
    """
    __tablename__ = "refrigerant_gwp"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Refrigerant identification
    name: str = Field(max_length=100, index=True)  # R-134a, R-410A, R-32
    chemical_formula: Optional[str] = Field(default=None, max_length=100)  # CH2FCF3
    cas_number: Optional[str] = Field(default=None, max_length=20)  # 811-97-2

    # GWP values (100-year time horizon)
    gwp_ar6: int  # IPCC AR6 (2021) value - PREFERRED
    gwp_ar5: Optional[int] = Field(default=None)  # IPCC AR5 (2014) value
    gwp_ar4: Optional[int] = Field(default=None)  # IPCC AR4 (2007) value - for legacy

    # Refrigerant type
    refrigerant_type: str = Field(max_length=50)  # HFC, HCFC, HFO, Natural

    # Common applications
    applications: Optional[str] = Field(default=None, max_length=500)  # AC, refrigeration, etc.

    # Phase-out status
    is_phased_out: bool = Field(default=False)
    phase_out_date: Optional[date] = Field(default=None)

    # Source
    source: str = Field(default="IPCC_AR6_2021", max_length=100)

    # Status
    is_active: bool = Field(default=True)


# ============================================================================
# WASTE DISPOSAL EMISSION FACTORS (For Category 3.5)
# ============================================================================

class WasteDisposalFactor(SQLModel, table=True):
    """
    Emission factors for waste disposal methods.

    Used in Category 3.5 Waste Generated in Operations.

    Factors depend on:
    - Waste type (mixed, organic, plastic, paper, etc.)
    - Disposal method (landfill, recycling, incineration, composting)
    - Country (landfill practices vary)

    Sources:
    - DEFRA UK GHG Conversion Factors
    - EPA WARM model
    """
    __tablename__ = "waste_disposal_factors"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Waste identification
    waste_type: str = Field(max_length=100, index=True)  # mixed, organic, plastic, paper
    disposal_method: str = Field(max_length=50, index=True)  # landfill, recycling, incineration

    # Emission factor
    co2e_per_kg: Decimal  # kg CO2e per kg of waste

    # Breakdown (optional)
    co2_per_kg: Optional[Decimal] = Field(default=None)
    ch4_per_kg: Optional[Decimal] = Field(default=None)
    n2o_per_kg: Optional[Decimal] = Field(default=None)

    # Negative emissions (for recycling)
    avoided_co2e_per_kg: Optional[Decimal] = Field(default=None)  # Emissions avoided

    # Regional variation
    country_code: Optional[str] = Field(default=None, max_length=2)  # GB, US or NULL for global
    region: str = Field(default="Global", max_length=50)

    # Source and year
    source: str = Field(max_length=100)
    year: int

    # Status
    is_active: bool = Field(default=True)
