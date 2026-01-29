"""
Decarbonization Pathways models.
Enables data-driven reduction planning based on client's actual emission profile.
"""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from app.models.core import Organization, ReportingPeriod, Site


# ============================================================================
# ENUMS
# ============================================================================

class TargetType(str, Enum):
    """Type of emissions target."""
    ABSOLUTE = "absolute"      # Reduce total emissions by X%
    INTENSITY = "intensity"    # Reduce emissions per revenue/employee by X%


class TargetFramework(str, Enum):
    """Target framework alignment."""
    SBTI_1_5C = "sbti_1_5c"           # SBTi 1.5°C aligned (42% by 2030)
    SBTI_WELL_BELOW_2C = "sbti_wb2c"  # SBTi Well-below 2°C (25% by 2030)
    NET_ZERO = "net_zero"             # Net zero commitment
    CUSTOM = "custom"                  # Custom target


class InitiativeCategory(str, Enum):
    """Category of reduction initiative."""
    ENERGY_EFFICIENCY = "energy_efficiency"
    RENEWABLE_ENERGY = "renewable_energy"
    FLEET_TRANSPORT = "fleet_transport"
    SUPPLY_CHAIN = "supply_chain"
    PROCESS_CHANGE = "process_change"
    BEHAVIOR_CHANGE = "behavior_change"
    WASTE_REDUCTION = "waste_reduction"
    CARBON_REMOVAL = "carbon_removal"


class ComplexityLevel(str, Enum):
    """Implementation complexity."""
    LOW = "low"       # Quick wins, minimal disruption
    MEDIUM = "medium" # Moderate effort, some planning
    HIGH = "high"     # Major projects, significant change


class ScenarioType(str, Enum):
    """Pre-defined scenario types."""
    AGGRESSIVE = "aggressive"
    MODERATE = "moderate"
    CONSERVATIVE = "conservative"
    CUSTOM = "custom"


class InitiativeStatus(str, Enum):
    """Status of an initiative in a scenario."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class MilestoneStatus(str, Enum):
    """Status of a roadmap milestone."""
    PENDING = "pending"
    ACHIEVED = "achieved"
    AT_RISK = "at_risk"
    MISSED = "missed"


# ============================================================================
# DECARBONIZATION TARGET
# ============================================================================

class DecarbonizationTarget(SQLModel, table=True):
    """
    Organization's decarbonization targets.
    Can have multiple targets (e.g., near-term 2030 + long-term 2050).
    """
    __tablename__ = "decarbonization_targets"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)

    # Target definition
    name: str = Field(max_length=100)                    # "SBTi 2030 Target"
    description: Optional[str] = Field(default=None, max_length=500)
    target_type: TargetType = Field(default=TargetType.ABSOLUTE)
    framework: TargetFramework = Field(default=TargetFramework.SBTI_1_5C)

    # Base year
    base_year: int                                       # 2023
    base_year_period_id: Optional[UUID] = Field(default=None, foreign_key="reporting_periods.id")
    base_year_emissions_tco2e: Decimal                   # 10,000 tCO2e

    # Target specification
    target_year: int                                     # 2030
    target_reduction_percent: Decimal                    # 42% (for SBTi 1.5°C)
    target_emissions_tco2e: Decimal                      # 5,800 tCO2e

    # Scope coverage
    includes_scope1: bool = Field(default=True)
    includes_scope2: bool = Field(default=True)
    includes_scope3: bool = Field(default=False)
    scope3_categories: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))

    # For intensity targets
    intensity_metric: Optional[str] = Field(default=None, max_length=50)  # "revenue_million_usd"
    base_intensity_value: Optional[Decimal] = Field(default=None)
    target_intensity_value: Optional[Decimal] = Field(default=None)

    # Validation status
    is_sbti_validated: bool = Field(default=False)
    sbti_validation_date: Optional[date] = Field(default=None)
    is_public: bool = Field(default=False)
    is_active: bool = Field(default=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    created_by_id: Optional[UUID] = Field(default=None, foreign_key="users.id")

    # Relationships
    scenarios: list["Scenario"] = Relationship(back_populates="target")


# ============================================================================
# INITIATIVE LIBRARY
# ============================================================================

class Initiative(SQLModel, table=True):
    """
    Pre-defined reduction initiatives in the library.
    These are curated and matched to client data via applicable_activity_keys.
    """
    __tablename__ = "initiatives"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Classification
    category: InitiativeCategory
    subcategory: Optional[str] = Field(default=None, max_length=100)

    # Identity
    name: str = Field(max_length=200)
    short_description: str = Field(max_length=500)
    detailed_description: Optional[str] = Field(default=None)

    # CRITICAL: What emission sources does this initiative address?
    # These fields enable matching to client's actual data
    applicable_scopes: list[int] = Field(sa_column=Column(JSON))  # [1, 2]
    applicable_category_codes: list[str] = Field(sa_column=Column(JSON))  # ["1.1", "2"]
    applicable_activity_keys: list[str] = Field(sa_column=Column(JSON))  # ["electricity_kwh"]

    # Reduction potential (percentage of addressed emissions)
    typical_reduction_percent_min: Decimal = Field(default=Decimal("10"))
    typical_reduction_percent_max: Decimal = Field(default=Decimal("30"))
    typical_reduction_percent_median: Decimal = Field(default=Decimal("20"))

    # Financial parameters (defaults - will be scaled to client)
    typical_capex_per_tco2e_reduced: Optional[Decimal] = Field(default=None)
    typical_opex_change_percent: Optional[Decimal] = Field(default=None)  # Negative = savings
    typical_payback_years_min: Optional[Decimal] = Field(default=None)
    typical_payback_years_max: Optional[Decimal] = Field(default=None)

    # Implementation
    complexity: ComplexityLevel = Field(default=ComplexityLevel.MEDIUM)
    implementation_time_months_min: int = Field(default=3)
    implementation_time_months_max: int = Field(default=12)

    # Dependencies and prerequisites
    prerequisites: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))

    # Co-benefits beyond emissions
    co_benefits: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))

    # Risks and barriers
    common_barriers: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))

    # Applicability conditions
    min_emissions_for_relevance_tco2e: Optional[Decimal] = Field(default=None)
    applicable_industries: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    applicable_regions: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))

    # Source/reference
    source_reference: Optional[str] = Field(default=None, max_length=500)

    # Status
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# SCENARIO
# ============================================================================

class Scenario(SQLModel, table=True):
    """
    A decarbonization scenario combining multiple initiatives.
    Clients can create and compare different scenarios.
    """
    __tablename__ = "scenarios"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    target_id: UUID = Field(foreign_key="decarbonization_targets.id", index=True)

    # Identity
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    scenario_type: ScenarioType = Field(default=ScenarioType.CUSTOM)

    # Is this the active/selected scenario?
    is_active: bool = Field(default=False)

    # Summary metrics (calculated from ScenarioInitiatives)
    total_reduction_tco2e: Decimal = Field(default=Decimal("0"))
    total_investment: Decimal = Field(default=Decimal("0"))
    total_annual_savings: Decimal = Field(default=Decimal("0"))
    weighted_payback_years: Optional[Decimal] = Field(default=None)
    target_achievement_percent: Decimal = Field(default=Decimal("0"))

    # Carbon price assumptions
    carbon_price_scenario: str = Field(default="moderate", max_length=20)
    assumed_carbon_price_2030: Optional[Decimal] = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    created_by_id: Optional[UUID] = Field(default=None, foreign_key="users.id")

    # Relationships
    target: DecarbonizationTarget = Relationship(back_populates="scenarios")
    initiatives: list["ScenarioInitiative"] = Relationship(back_populates="scenario")
    milestones: list["RoadmapMilestone"] = Relationship(back_populates="scenario")


# ============================================================================
# SCENARIO INITIATIVE (Junction table with additional data)
# ============================================================================

class ScenarioInitiative(SQLModel, table=True):
    """
    An initiative selected for a specific scenario.
    Contains client-specific implementation details.
    """
    __tablename__ = "scenario_initiatives"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    scenario_id: UUID = Field(foreign_key="scenarios.id", index=True)
    initiative_id: UUID = Field(foreign_key="initiatives.id", index=True)

    # Which emission source does this address?
    target_activity_key: str = Field(max_length=100)
    target_site_id: Optional[UUID] = Field(default=None, foreign_key="sites.id")

    # Client-adjusted reduction estimates
    expected_reduction_tco2e: Decimal
    expected_reduction_percent: Decimal

    # Client-specific financials
    capex: Decimal = Field(default=Decimal("0"))
    annual_opex_change: Decimal = Field(default=Decimal("0"))  # Negative = savings
    annual_savings: Decimal = Field(default=Decimal("0"))

    # Timeline
    implementation_start: Optional[date] = Field(default=None)
    implementation_end: Optional[date] = Field(default=None)

    # Status tracking
    status: InitiativeStatus = Field(default=InitiativeStatus.PLANNED)
    actual_start_date: Optional[date] = Field(default=None)
    actual_end_date: Optional[date] = Field(default=None)
    actual_reduction_tco2e: Optional[Decimal] = Field(default=None)

    # Priority/order
    priority_order: int = Field(default=0)

    # Notes
    notes: Optional[str] = Field(default=None, max_length=1000)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relationships
    scenario: Scenario = Relationship(back_populates="initiatives")
    initiative: Initiative = Relationship()


# ============================================================================
# ROADMAP MILESTONE
# ============================================================================

class RoadmapMilestone(SQLModel, table=True):
    """
    Key milestones in the decarbonization roadmap.
    """
    __tablename__ = "roadmap_milestones"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    scenario_id: UUID = Field(foreign_key="scenarios.id", index=True)

    # Milestone definition
    name: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)

    # Timing
    target_date: date
    milestone_year: int  # For easy filtering

    # Expected state at milestone
    cumulative_reduction_tco2e: Decimal
    cumulative_investment: Decimal
    expected_emissions_tco2e: Decimal

    # Status tracking
    status: MilestoneStatus = Field(default=MilestoneStatus.PENDING)
    actual_date: Optional[date] = Field(default=None)
    actual_emissions_tco2e: Optional[Decimal] = Field(default=None)

    # Linked initiatives that must be complete
    linked_initiative_ids: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    scenario: Scenario = Relationship(back_populates="milestones")


# ============================================================================
# EMISSION CHECKPOINT (Progress Tracking)
# ============================================================================

class EmissionCheckpoint(SQLModel, table=True):
    """
    Periodic emission checkpoints for tracking progress against plan.
    Created when a new ReportingPeriod is completed.
    """
    __tablename__ = "emission_checkpoints"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    target_id: UUID = Field(foreign_key="decarbonization_targets.id", index=True)
    scenario_id: Optional[UUID] = Field(default=None, foreign_key="scenarios.id")
    reporting_period_id: UUID = Field(foreign_key="reporting_periods.id", index=True)

    # Checkpoint year
    checkpoint_year: int = Field(index=True)

    # Actual vs planned
    actual_emissions_tco2e: Decimal
    planned_emissions_tco2e: Decimal
    variance_tco2e: Decimal                     # Actual - Planned (negative = ahead)
    variance_percent: Decimal

    # Status
    on_track: bool = Field(default=True)

    # Analysis
    variance_explanation: Optional[str] = Field(default=None, max_length=1000)
    recommended_actions: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# PYDANTIC MODELS FOR API RESPONSES (Not stored in DB)
# ============================================================================

class EmissionSource(SQLModel):
    """A single emission source identified from client data."""
    activity_key: str
    display_name: str
    scope: int
    category_code: str
    total_co2e_kg: Decimal
    total_co2e_tonnes: Decimal
    percentage_of_total: Decimal
    site_id: Optional[UUID] = None
    site_name: Optional[str] = None
    activity_count: int
    data_quality_avg: Optional[Decimal] = None


class EmissionProfileAnalysis(SQLModel):
    """
    Computed analysis of organization's emission profile.
    This is NOT stored - it's calculated on-demand from Activities/Emissions.
    """
    organization_id: UUID
    period_id: UUID
    period_name: str
    analysis_date: datetime

    # Totals
    total_co2e_kg: Decimal
    total_co2e_tonnes: Decimal
    scope1_co2e_tonnes: Decimal
    scope2_co2e_tonnes: Decimal
    scope3_co2e_tonnes: Decimal

    # Breakdown by category
    emissions_by_category: dict[str, Decimal]

    # Breakdown by activity type
    emissions_by_activity_key: dict[str, Decimal]

    # Breakdown by site
    emissions_by_site: dict[str, Decimal]

    # Top sources (Pareto)
    top_sources: list[EmissionSource]

    # Trends (if multiple periods available)
    yoy_change_percent: Optional[Decimal] = None
    trend_direction: Optional[str] = None  # "increasing", "decreasing", "stable"
    previous_period_total_tonnes: Optional[Decimal] = None


class PersonalizedRecommendation(SQLModel):
    """
    A recommendation generated for a specific client based on their data.
    """
    initiative_id: UUID
    initiative_name: str
    initiative_category: str
    initiative_description: str

    # The client's emission source this addresses
    target_activity_key: str
    target_source_name: str
    target_source_emissions_tco2e: Decimal
    target_source_percent_of_total: Decimal

    # Personalized impact calculations
    potential_reduction_tco2e: Decimal
    potential_reduction_low_tco2e: Decimal
    potential_reduction_high_tco2e: Decimal
    reduction_as_percent_of_total: Decimal

    # Personalized financials
    estimated_capex: Optional[Decimal] = None
    estimated_annual_savings: Optional[Decimal] = None
    payback_years: Optional[Decimal] = None
    roi_percent: Optional[Decimal] = None

    # Scoring
    impact_score: int  # 1-10
    feasibility_score: int  # 1-10
    priority_score: int  # Combined

    # Complexity and timing
    complexity: str
    implementation_months_min: int
    implementation_months_max: int

    # Co-benefits
    co_benefits: Optional[list[str]] = None

    # Why this recommendation
    relevance_explanation: str
