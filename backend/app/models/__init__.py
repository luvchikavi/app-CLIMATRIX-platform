"""
SQLModel database models.
All models are imported here for Alembic auto-discovery.
"""
from app.models.core import (
    Organization, User, Site, ReportingPeriod,
    UserRole, PeriodStatus, AssuranceLevel,
)
from app.models.emission import (
    EmissionFactor, Activity, Emission, UnitConversion, FuelPrice,
    ImportBatch, ImportBatchStatus,
    # New Scope 3 Reference Tables
    Airport,
    TransportDistanceMatrix,
    CurrencyConversion,
    PriceRange,
    HotelEmissionFactor,
    GridEmissionFactor,
    RefrigerantGWP,
    WasteDisposalFactor,
)
from app.models.jobs import ImportJob, JobStatus, JobType

__all__ = [
    # Core
    "Organization",
    "User",
    "Site",
    "ReportingPeriod",
    "UserRole",
    "PeriodStatus",
    "AssuranceLevel",
    # Emission
    "EmissionFactor",
    "Activity",
    "Emission",
    "UnitConversion",
    "FuelPrice",
    # Import Tracking
    "ImportBatch",
    "ImportBatchStatus",
    # Jobs
    "ImportJob",
    "JobStatus",
    "JobType",
    # Scope 3 Reference Tables
    "Airport",
    "TransportDistanceMatrix",
    "CurrencyConversion",
    "PriceRange",
    "HotelEmissionFactor",
    "GridEmissionFactor",
    "RefrigerantGWP",
    "WasteDisposalFactor",
]
