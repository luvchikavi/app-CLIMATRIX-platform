"""
SQLModel database models.
All models are imported here for Alembic auto-discovery.
"""
from app.models.core import (
    Organization, User, Site, ReportingPeriod,
    UserRole, PeriodStatus, AssuranceLevel,
)
from app.models.emission import (
    EmissionFactor, EmissionFactorStatus, Activity, Emission, UnitConversion, FuelPrice,
    ImportBatch, ImportBatchStatus, DataQualityScore,
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
from app.models.cbam import (
    # CBAM Enums
    CBAMSector,
    CBAMCalculationMethod,
    CBAMReportStatus,
    CBAMInstallationStatus,
    # CBAM Models
    CBAMProduct,
    CBAMInstallation,
    CBAMImport,
    CBAMQuarterlyReport,
    CBAMAnnualDeclaration,
    CBAMDefaultValue,
    CBAMGridFactor,
    EUETSPrice,
)
from app.models.decarbonization import (
    # Decarbonization Enums
    TargetType,
    TargetFramework,
    InitiativeCategory,
    ComplexityLevel,
    ScenarioType,
    InitiativeStatus,
    MilestoneStatus,
    # Decarbonization Models
    DecarbonizationTarget,
    Initiative,
    Scenario,
    ScenarioInitiative,
    RoadmapMilestone,
    EmissionCheckpoint,
)

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
    "EmissionFactorStatus",
    "Activity",
    "Emission",
    "UnitConversion",
    "FuelPrice",
    # Import Tracking
    "ImportBatch",
    "ImportBatchStatus",
    # Data Quality
    "DataQualityScore",
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
    # CBAM Enums
    "CBAMSector",
    "CBAMCalculationMethod",
    "CBAMReportStatus",
    "CBAMInstallationStatus",
    # CBAM Models
    "CBAMProduct",
    "CBAMInstallation",
    "CBAMImport",
    "CBAMQuarterlyReport",
    "CBAMAnnualDeclaration",
    "CBAMDefaultValue",
    "CBAMGridFactor",
    "EUETSPrice",
    # Decarbonization Enums
    "TargetType",
    "TargetFramework",
    "InitiativeCategory",
    "ComplexityLevel",
    "ScenarioType",
    "InitiativeStatus",
    "MilestoneStatus",
    # Decarbonization Models
    "DecarbonizationTarget",
    "Initiative",
    "Scenario",
    "ScenarioInitiative",
    "RoadmapMilestone",
    "EmissionCheckpoint",
]
