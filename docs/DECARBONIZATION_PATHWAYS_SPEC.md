# Decarbonization Pathways Module - Product Specification

**Version:** 1.0
**Date:** January 2026
**Status:** Draft
**Author:** CLIMATRIX Product Team

---

## Executive Summary

The Decarbonization Pathways module transforms CLIMATRIX from an annual emissions reporting tool into a **continuous strategic planning platform**. By leveraging the emissions data clients already upload, the module provides **personalized, data-driven reduction recommendations** with full financial modeling, SBTi-aligned targets, and execution roadmaps.

### Key Value Proposition

> "Your data becomes your strategy. Every activity you've uploaded informs a reduction plan tailored specifically to your organization."

### Business Impact

| Metric | Before | After |
|--------|--------|-------|
| Client Touchpoints/Year | 1-2 | 12+ (monthly reviews) |
| Engagement Depth | Report viewer | Strategic partner |
| Revenue per Client | $X/year | $3-5X/year (premium tier) |
| Client Retention | Standard | High (switching cost) |

---

## 1. Core Principle: Data-Driven Personalization

### 1.1 The Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLIENT'S EXISTING DATA                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐ │
│  │  Activities  │   │   Sites &    │   │  Emission    │   │ Import       │ │
│  │  (Scope 1-3) │   │   Locations  │   │   Factors    │   │ History      │ │
│  └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘ │
│         │                  │                  │                  │          │
│         └──────────────────┴──────────────────┴──────────────────┘          │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     EMISSION PROFILE ANALYSIS                         │   │
│  │  • Total emissions by scope (1, 2, 3)                                │   │
│  │  • Breakdown by category (1.1, 3.1, 3.4, etc.)                      │   │
│  │  • Breakdown by site/location                                        │   │
│  │  • Breakdown by activity type (diesel, electricity, flights, etc.)  │   │
│  │  • Top 10 emission sources (Pareto analysis)                        │   │
│  │  • Year-over-year trends (if multiple periods)                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                   PERSONALIZED RECOMMENDATIONS                        │   │
│  │  Based on YOUR actual emission sources                               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 How Client Data Drives Recommendations

| Client's Activity Data | System Analysis | Recommended Initiative |
|------------------------|-----------------|----------------------|
| `activity_key: "electricity_kwh"` in Scope 2 = 1,200 tCO2e | Electricity is 40% of total | Renewable PPA, Solar installation, Energy efficiency |
| `activity_key: "diesel_volume"` in Scope 1 = 800 tCO2e | Fleet represents major source | Fleet electrification, Route optimization |
| `activity_key: "flight_economy_km"` in Scope 3.6 = 500 tCO2e | Business travel significant | Video conferencing policy, SAF purchasing |
| `activity_key: "purchased_goods_plastic"` in Scope 3.1 = 2,000 tCO2e | Plastic is #1 source | Supplier engagement, Material substitution |
| Site in `country_code: "IL"` with high electricity | High-carbon grid (0.42 kg/kWh) | Priority for renewables |

### 1.3 Recommendation Matching Logic

```python
# Pseudocode for recommendation engine
def get_recommendations(organization_id: UUID) -> list[Initiative]:
    # 1. Analyze client's emission profile
    profile = analyze_emission_profile(organization_id)

    # 2. Identify top emission sources
    top_sources = profile.get_top_sources(limit=10)

    # 3. Match initiatives to actual sources
    recommendations = []
    for source in top_sources:
        # Find initiatives that address this specific activity_key
        matching_initiatives = initiative_library.filter(
            applicable_activity_keys__contains=source.activity_key,
            applicable_scopes__contains=source.scope,
            applicable_categories__contains=source.category_code
        )

        # Calculate potential reduction based on CLIENT'S ACTUAL DATA
        for initiative in matching_initiatives:
            potential_reduction = calculate_reduction(
                current_emissions=source.total_co2e_kg,
                reduction_percentage=initiative.typical_reduction_pct,
                applicability_factor=initiative.get_applicability(source)
            )

            # Calculate financials based on CLIENT'S SCALE
            financials = calculate_financials(
                initiative=initiative,
                client_data=source,
                organization=profile.organization
            )

            recommendations.append(PersonalizedRecommendation(
                initiative=initiative,
                source=source,
                potential_reduction_tco2e=potential_reduction / 1000,
                estimated_investment=financials.capex,
                estimated_annual_savings=financials.annual_savings,
                payback_years=financials.payback,
                roi_percent=financials.roi
            ))

    # 4. Rank by impact and feasibility
    return rank_recommendations(recommendations)
```

---

## 2. Module Architecture

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DECARBONIZATION PATHWAYS MODULE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  TARGET SETTING │  │ SCENARIO ENGINE │  │ FINANCIAL MODEL │             │
│  │  ─────────────  │  │ ─────────────── │  │ ─────────────── │             │
│  │  • SBTi Wizard  │  │  • What-if      │  │  • ROI/NPV/IRR  │             │
│  │  • Base year    │  │  • Compare      │  │  • Cash flow    │             │
│  │  • Milestones   │  │  • Sensitivity  │  │  • Carbon price │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                │                                            │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      INITIATIVE LIBRARY                               │  │
│  │  Pre-built reduction measures with costs, impacts, and applicability │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                │                                            │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      RECOMMENDATION ENGINE                            │  │
│  │  Matches initiatives to client's actual emission sources             │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                │                                            │
│                                ▼                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ ROADMAP BUILDER │  │  KPI DASHBOARD  │  │ PROGRESS TRACKER│             │
│  │ ─────────────── │  │ ─────────────── │  │ ─────────────── │             │
│  │  • Gantt chart  │  │  • Real-time    │  │  • Actual vs    │             │
│  │  • Milestones   │  │  • Targets      │  │    planned      │             │
│  │  • Dependencies │  │  • Alerts       │  │  • Variance     │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Models (Backend)

#### 2.2.1 Emission Profile Analysis (Computed from existing data)

```python
class EmissionProfileAnalysis(BaseModel):
    """
    Computed analysis of organization's emission profile.
    This is NOT stored - it's calculated on-demand from Activities/Emissions.
    """
    organization_id: UUID
    period_id: UUID
    analysis_date: datetime

    # Totals
    total_co2e_tonnes: Decimal
    scope1_co2e_tonnes: Decimal
    scope2_co2e_tonnes: Decimal
    scope3_co2e_tonnes: Decimal

    # Breakdown by category
    emissions_by_category: dict[str, Decimal]  # {"1.1": 500, "2": 1200, "3.1": 2000}

    # Breakdown by activity type
    emissions_by_activity_key: dict[str, Decimal]  # {"electricity_kwh": 1200, "diesel_volume": 800}

    # Breakdown by site
    emissions_by_site: dict[UUID, Decimal]

    # Top sources (Pareto)
    top_sources: list[EmissionSource]

    # Trends (if multiple periods available)
    yoy_change_percent: Optional[Decimal]
    trend_direction: Optional[str]  # "increasing", "decreasing", "stable"


class EmissionSource(BaseModel):
    """A single emission source identified from client data."""
    activity_key: str              # "electricity_kwh"
    display_name: str              # "Electricity Consumption"
    scope: int                     # 2
    category_code: str             # "2"
    total_co2e_tonnes: Decimal     # 1,200
    percentage_of_total: Decimal   # 40%
    site_id: Optional[UUID]        # If site-specific
    site_name: Optional[str]
    activity_count: int            # Number of activities
    data_quality_avg: Decimal      # Average PCAF score
```

#### 2.2.2 Decarbonization Target

```python
class TargetType(str, Enum):
    ABSOLUTE = "absolute"      # Reduce total emissions by X%
    INTENSITY = "intensity"    # Reduce emissions per revenue/employee by X%


class TargetFramework(str, Enum):
    SBTI_1_5C = "sbti_1_5c"           # SBTi 1.5°C aligned
    SBTI_WELL_BELOW_2C = "sbti_wb2c"  # SBTi Well-below 2°C
    NET_ZERO = "net_zero"             # Net zero commitment
    CUSTOM = "custom"                  # Custom target


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
    target_type: TargetType = Field(default=TargetType.ABSOLUTE)
    framework: TargetFramework = Field(default=TargetFramework.SBTI_1_5C)

    # Base year (references existing ReportingPeriod)
    base_year: int                                       # 2023
    base_year_period_id: Optional[UUID] = Field(foreign_key="reporting_periods.id")
    base_year_emissions_tco2e: Decimal                   # 10,000 tCO2e

    # Target specification
    target_year: int                                     # 2030
    target_reduction_percent: Decimal                    # 42% (for SBTi 1.5°C)
    target_emissions_tco2e: Decimal                      # 5,800 tCO2e

    # Scope coverage
    includes_scope1: bool = Field(default=True)
    includes_scope2: bool = Field(default=True)
    includes_scope3: bool = Field(default=False)
    scope3_categories: Optional[list[str]] = Field(default=None)  # ["3.1", "3.4"]

    # For intensity targets
    intensity_metric: Optional[str] = Field(default=None)  # "revenue_million_usd", "employee"
    base_intensity_value: Optional[Decimal] = Field(default=None)
    target_intensity_value: Optional[Decimal] = Field(default=None)

    # Status
    is_sbti_validated: bool = Field(default=False)
    sbti_validation_date: Optional[date] = Field(default=None)
    is_public: bool = Field(default=False)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
```

#### 2.2.3 Initiative Library

```python
class InitiativeCategory(str, Enum):
    ENERGY_EFFICIENCY = "energy_efficiency"
    RENEWABLE_ENERGY = "renewable_energy"
    FLEET_TRANSPORT = "fleet_transport"
    SUPPLY_CHAIN = "supply_chain"
    PROCESS_CHANGE = "process_change"
    BEHAVIOR_CHANGE = "behavior_change"
    CARBON_REMOVAL = "carbon_removal"


class ComplexityLevel(str, Enum):
    LOW = "low"       # Quick wins, minimal disruption
    MEDIUM = "medium" # Moderate effort, some planning
    HIGH = "high"     # Major projects, significant change


class Initiative(SQLModel, table=True):
    """
    Pre-defined reduction initiatives in the library.
    These are curated by CLIMATRIX and matched to client data.
    """
    __tablename__ = "initiatives"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Classification
    category: InitiativeCategory
    subcategory: Optional[str] = Field(default=None, max_length=100)

    # Identity
    name: str = Field(max_length=200)           # "Solar PV Installation"
    short_description: str = Field(max_length=500)
    detailed_description: Optional[str] = Field(default=None)

    # CRITICAL: What emission sources does this initiative address?
    applicable_scopes: list[int]                # [1, 2]
    applicable_category_codes: list[str]        # ["1.1", "2"]
    applicable_activity_keys: list[str]         # ["electricity_kwh", "natural_gas_volume"]

    # Reduction potential
    typical_reduction_percent_min: Decimal      # 10%
    typical_reduction_percent_max: Decimal      # 30%
    typical_reduction_percent_median: Decimal   # 20%

    # Financial parameters (defaults - will be scaled to client)
    typical_capex_per_tco2e_reduced: Optional[Decimal] = Field(default=None)  # $/tCO2e
    typical_opex_change_percent: Optional[Decimal] = Field(default=None)      # -10% (savings)
    typical_payback_years_min: Optional[Decimal] = Field(default=None)
    typical_payback_years_max: Optional[Decimal] = Field(default=None)

    # Implementation
    complexity: ComplexityLevel
    implementation_time_months_min: int
    implementation_time_months_max: int

    # Dependencies and prerequisites
    prerequisites: Optional[list[str]] = Field(default=None)  # ["Electrical infrastructure upgrade"]

    # Co-benefits beyond emissions
    co_benefits: Optional[list[str]] = Field(default=None)  # ["Energy cost savings", "Brand value"]

    # Risks and barriers
    common_barriers: Optional[list[str]] = Field(default=None)  # ["High upfront cost", "Space requirements"]

    # Applicability conditions
    min_emissions_for_relevance_tco2e: Optional[Decimal] = Field(default=None)  # Only show if source > 100 tCO2e
    applicable_industries: Optional[list[str]] = Field(default=None)
    applicable_regions: Optional[list[str]] = Field(default=None)

    # Source/reference
    source_reference: Optional[str] = Field(default=None)  # "IEA Technology Report 2024"

    # Status
    is_active: bool = Field(default=True)
```

#### 2.2.4 Personalized Recommendation (Computed)

```python
class PersonalizedRecommendation(BaseModel):
    """
    A recommendation generated for a specific client based on their data.
    This links an Initiative to the client's actual emission source.
    """
    initiative: Initiative

    # The client's emission source this addresses
    emission_source: EmissionSource

    # Personalized impact calculations
    potential_reduction_tco2e: Decimal          # Based on CLIENT'S data
    reduction_as_percent_of_total: Decimal      # % of total footprint

    # Personalized financials (scaled to client's size)
    estimated_capex: Decimal
    estimated_annual_savings: Decimal
    payback_years: Decimal
    roi_percent: Decimal
    npv_10_years: Decimal                       # 10-year NPV at 8% discount

    # Risk-adjusted reduction range
    reduction_low_tco2e: Decimal                # Conservative estimate
    reduction_high_tco2e: Decimal               # Optimistic estimate

    # Scoring
    impact_score: int                           # 1-10
    feasibility_score: int                      # 1-10
    priority_score: int                         # Combined score for ranking

    # Why this recommendation?
    relevance_explanation: str                  # "Your electricity consumption at Tel Aviv HQ..."
```

#### 2.2.5 Scenario

```python
class Scenario(SQLModel, table=True):
    """
    A decarbonization scenario combining multiple initiatives.
    Clients can create and compare different scenarios.
    """
    __tablename__ = "scenarios"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    target_id: UUID = Field(foreign_key="decarbonization_targets.id")

    # Identity
    name: str = Field(max_length=100)           # "Aggressive Pathway"
    description: Optional[str] = Field(default=None, max_length=500)

    # Scenario type
    scenario_type: str = Field(default="custom")  # "aggressive", "moderate", "conservative", "custom"

    # Is this the active/selected scenario?
    is_active: bool = Field(default=False)

    # Summary metrics (calculated from ScenarioInitiatives)
    total_reduction_tco2e: Decimal = Field(default=0)
    total_investment: Decimal = Field(default=0)
    total_annual_savings: Decimal = Field(default=0)
    weighted_payback_years: Optional[Decimal] = Field(default=None)
    target_achievement_percent: Decimal = Field(default=0)  # % of target achieved

    # Carbon price assumptions
    carbon_price_scenario: str = Field(default="moderate")  # "low", "moderate", "high"
    assumed_carbon_price_2030: Optional[Decimal] = Field(default=None)  # $/tCO2e

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)


class ScenarioInitiative(SQLModel, table=True):
    """
    An initiative selected for a specific scenario.
    Contains client-specific implementation details.
    """
    __tablename__ = "scenario_initiatives"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    scenario_id: UUID = Field(foreign_key="scenarios.id", index=True)
    initiative_id: UUID = Field(foreign_key="initiatives.id")

    # Which emission source does this address?
    target_activity_key: str                    # "electricity_kwh"
    target_site_id: Optional[UUID] = Field(default=None, foreign_key="sites.id")

    # Client-adjusted parameters
    expected_reduction_tco2e: Decimal
    expected_reduction_percent: Decimal

    # Client-specific financials
    capex: Decimal
    annual_opex_change: Decimal                 # Negative = savings
    implementation_start: date
    implementation_end: date

    # Status
    status: str = Field(default="planned")      # "planned", "in_progress", "completed", "cancelled"

    # Notes
    notes: Optional[str] = Field(default=None, max_length=1000)
```

#### 2.2.6 Roadmap & Milestones

```python
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

    # Expected state at milestone
    cumulative_reduction_tco2e: Decimal
    cumulative_investment: Decimal
    expected_emissions_tco2e: Decimal           # Total footprint at this point

    # Status tracking
    status: str = Field(default="pending")      # "pending", "achieved", "at_risk", "missed"
    actual_date: Optional[date] = Field(default=None)
    actual_emissions_tco2e: Optional[Decimal] = Field(default=None)

    # Dependencies
    depends_on_initiatives: Optional[list[UUID]] = Field(default=None)
```

#### 2.2.7 Progress Tracking

```python
class EmissionCheckpoint(SQLModel, table=True):
    """
    Periodic emission checkpoints for tracking progress against plan.
    Created when a new ReportingPeriod is completed.
    """
    __tablename__ = "emission_checkpoints"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    target_id: UUID = Field(foreign_key="decarbonization_targets.id")
    reporting_period_id: UUID = Field(foreign_key="reporting_periods.id")

    # Actual vs planned
    actual_emissions_tco2e: Decimal
    planned_emissions_tco2e: Decimal            # From active scenario trajectory
    variance_tco2e: Decimal                     # Actual - Planned (negative = ahead)
    variance_percent: Decimal

    # Status
    on_track: bool                              # Is this checkpoint on track to meet target?

    # Analysis
    variance_explanation: Optional[str] = Field(default=None)
    recommended_actions: Optional[list[str]] = Field(default=None)

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 3. Initiative Library (Pre-Seeded Data)

### 3.1 Initiative Categories

The Initiative Library contains pre-defined reduction measures, curated by CLIMATRIX. Each initiative specifies which `activity_keys` it applies to, enabling automatic matching to client data.

### 3.2 Sample Initiatives

#### 3.2.1 Energy Efficiency Initiatives

| Initiative | Applicable Activity Keys | Typical Reduction | Complexity |
|------------|-------------------------|-------------------|------------|
| LED Lighting Retrofit | `electricity_kwh` | 10-15% | Low |
| HVAC Optimization | `electricity_kwh`, `natural_gas_volume` | 15-25% | Medium |
| Building Envelope Upgrade | `electricity_kwh`, `natural_gas_volume` | 20-40% | High |
| Industrial Process Optimization | `electricity_kwh`, `natural_gas_volume` | 10-30% | High |

#### 3.2.2 Renewable Energy Initiatives

| Initiative | Applicable Activity Keys | Typical Reduction | Complexity |
|------------|-------------------------|-------------------|------------|
| On-site Solar PV | `electricity_kwh` | 30-80% | Medium |
| Renewable Energy PPA | `electricity_kwh` | 80-100% | Medium |
| Green Tariff Procurement | `electricity_kwh` | 80-100% | Low |
| Wind PPA | `electricity_kwh` | 80-100% | Medium |

#### 3.2.3 Fleet & Transport Initiatives

| Initiative | Applicable Activity Keys | Typical Reduction | Complexity |
|------------|-------------------------|-------------------|------------|
| EV Fleet Transition | `diesel_volume`, `petrol_volume`, `company_car_km` | 60-100% | High |
| Route Optimization | `diesel_volume`, `petrol_volume` | 10-20% | Low |
| Driver Eco-Training | `diesel_volume`, `petrol_volume` | 5-15% | Low |
| Rail Modal Shift | `truck_freight_tkm` | 60-80% | Medium |

#### 3.2.4 Business Travel Initiatives

| Initiative | Applicable Activity Keys | Typical Reduction | Complexity |
|------------|-------------------------|-------------------|------------|
| Video Conferencing Policy | `flight_economy_km`, `flight_business_km` | 30-50% | Low |
| Travel Policy Tightening | `flight_economy_km`, `flight_business_km` | 20-40% | Low |
| SAF (Sustainable Aviation Fuel) | `flight_economy_km`, `flight_business_km` | 50-80% | Medium |
| Rail for Short-Haul | `flight_economy_km` | 90% | Low |

#### 3.2.5 Supply Chain Initiatives

| Initiative | Applicable Activity Keys | Typical Reduction | Complexity |
|------------|-------------------------|-------------------|------------|
| Supplier Engagement Program | `purchased_goods_*` | 10-30% | High |
| Material Substitution | `purchased_goods_plastic`, `purchased_goods_steel` | 20-50% | Medium |
| Local Sourcing | `upstream_transport_*`, `purchased_goods_*` | 10-30% | Medium |
| Circular Economy / Recycled Content | `purchased_goods_*` | 20-60% | Medium |

#### 3.2.6 Operational Changes

| Initiative | Applicable Activity Keys | Typical Reduction | Complexity |
|------------|-------------------------|-------------------|------------|
| Waste Reduction Program | `waste_landfill_*` | 30-50% | Medium |
| Recycling Expansion | `waste_landfill_*` | 20-40% | Low |
| Water Efficiency | `water_supply_m3` | 20-40% | Low |
| Refrigerant Leak Detection | `refrigerant_*` | 50-90% | Medium |

### 3.3 Initiative Data Structure Example

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "category": "renewable_energy",
  "subcategory": "solar",
  "name": "On-site Solar PV Installation",
  "short_description": "Install rooftop or ground-mounted solar panels to generate renewable electricity on-site.",
  "detailed_description": "Solar photovoltaic systems convert sunlight directly into electricity...",

  "applicable_scopes": [2],
  "applicable_category_codes": ["2"],
  "applicable_activity_keys": ["electricity_kwh"],

  "typical_reduction_percent_min": 30,
  "typical_reduction_percent_max": 80,
  "typical_reduction_percent_median": 50,

  "typical_capex_per_tco2e_reduced": 800,
  "typical_opex_change_percent": -15,
  "typical_payback_years_min": 4,
  "typical_payback_years_max": 10,

  "complexity": "medium",
  "implementation_time_months_min": 6,
  "implementation_time_months_max": 18,

  "prerequisites": ["Structural roof assessment", "Grid connection approval"],
  "co_benefits": ["Energy cost savings", "Energy independence", "Brand value", "LEED/BREEAM credits"],
  "common_barriers": ["High upfront cost", "Roof space limitations", "Grid connection delays"],

  "min_emissions_for_relevance_tco2e": 100,
  "applicable_regions": ["Global"],

  "source_reference": "IEA Solar PV Report 2024"
}
```

---

## 4. Financial Model

### 4.1 Financial Metrics Calculated

| Metric | Formula | Description |
|--------|---------|-------------|
| **CAPEX** | `initiative.capex_per_tco2e × client_reduction_tco2e` | Scaled to client's emission size |
| **Annual Savings** | `(energy_cost_savings + carbon_cost_avoided)` | Based on client's actual consumption |
| **Payback Period** | `CAPEX / Annual_Savings` | Simple payback |
| **ROI** | `(Total_Savings - CAPEX) / CAPEX × 100` | Over project lifetime |
| **NPV** | `∑(Cash_Flow_t / (1+r)^t)` | 10-year NPV at 8% discount |
| **IRR** | Rate where NPV = 0 | Internal rate of return |
| **Marginal Abatement Cost** | `CAPEX / Lifetime_Reduction_tCO2e` | $/tCO2e abated |

### 4.2 Carbon Price Scenarios

| Scenario | 2025 | 2030 | 2035 | 2040 | 2050 |
|----------|------|------|------|------|------|
| Low | $30 | $50 | $75 | $100 | $150 |
| Moderate | $50 | $100 | $150 | $200 | $300 |
| High | $80 | $150 | $250 | $350 | $500 |

### 4.3 Cost of Inaction

```python
def calculate_cost_of_inaction(
    organization: Organization,
    target: DecarbonizationTarget,
    carbon_price_scenario: str = "moderate"
) -> CostOfInactionAnalysis:
    """
    Calculate the financial risk of not reducing emissions.
    """
    carbon_prices = get_carbon_price_trajectory(carbon_price_scenario)

    current_emissions = get_current_emissions(organization)

    # Without action: emissions stay constant
    # With action: emissions follow reduction pathway

    cumulative_carbon_cost_without_action = 0
    cumulative_carbon_cost_with_action = 0

    for year in range(2025, 2051):
        price = carbon_prices[year]

        # Without action
        cumulative_carbon_cost_without_action += current_emissions * price

        # With action (linear reduction to target)
        reduced_emissions = interpolate_emissions(
            current_emissions,
            target.target_emissions_tco2e,
            target.base_year,
            target.target_year,
            year
        )
        cumulative_carbon_cost_with_action += reduced_emissions * price

    return CostOfInactionAnalysis(
        cumulative_cost_without_action=cumulative_carbon_cost_without_action,
        cumulative_cost_with_action=cumulative_carbon_cost_with_action,
        savings_from_action=cumulative_carbon_cost_without_action - cumulative_carbon_cost_with_action,
        carbon_price_scenario=carbon_price_scenario
    )
```

---

## 5. User Interface Design

### 5.1 Navigation

New sidebar section under "Modules":

```
Modules
├── GHG Inventory ✓
├── CBAM ✓
├── Decarbonization Pathways (NEW)
│   ├── Overview Dashboard
│   ├── Set Targets
│   ├── Explore Initiatives
│   ├── Build Scenario
│   ├── View Roadmap
│   └── Track Progress
├── PCAF (Coming Soon)
└── LCA (Coming Soon)
```

### 5.2 Screen Designs

#### 5.2.1 Overview Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Decarbonization Pathways                                    [Set Target]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     YOUR EMISSION PROFILE                            │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │  [PIE CHART: Emissions by Scope]  [BAR: Top 5 Sources]       │   │   │
│  │  │                                                               │   │   │
│  │  │  Scope 1: 800 tCO2e (20%)    #1 Purchased Goods: 2,000 tCO2e│   │   │
│  │  │  Scope 2: 1,200 tCO2e (30%)  #2 Electricity: 1,200 tCO2e    │   │   │
│  │  │  Scope 3: 2,000 tCO2e (50%)  #3 Fleet Diesel: 800 tCO2e     │   │   │
│  │  │                               #4 Business Travel: 500 tCO2e  │   │   │
│  │  │  TOTAL: 4,000 tCO2e          #5 Waste: 200 tCO2e            │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌───────────────────────┐  ┌───────────────────────┐                       │
│  │ TARGET STATUS         │  │ TOP RECOMMENDATIONS   │                       │
│  │ ─────────────────────│  │ ─────────────────────│                       │
│  │ SBTi 2030: -42%      │  │ 1. Renewable PPA      │                       │
│  │                       │  │    -1,200 tCO2e, $X   │                       │
│  │ [=======>    ] 15%   │  │                       │                       │
│  │                       │  │ 2. Fleet Electrify    │                       │
│  │ On track to meet     │  │    -640 tCO2e, $Y     │                       │
│  │ 2025 milestone       │  │                       │                       │
│  │                       │  │ 3. Supplier Program   │                       │
│  │ [View Roadmap →]     │  │    -400 tCO2e, $Z     │                       │
│  └───────────────────────┘  └───────────────────────┘                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 5.2.2 Target Setting Wizard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Set Decarbonization Target                              Step 2 of 4        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Select Target Framework                                                     │
│  ─────────────────────────                                                   │
│                                                                              │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                   │
│  │ ○ SBTi 1.5°C Aligned   │  │ ○ SBTi Well-Below 2°C   │                   │
│  │                         │  │                         │                   │
│  │ Most ambitious pathway  │  │ Less aggressive pathway │                   │
│  │ 42% reduction by 2030   │  │ 25% reduction by 2030   │                   │
│  │ (from 2020 levels)      │  │ (from 2020 levels)      │                   │
│  │                         │  │                         │                   │
│  │ [RECOMMENDED]           │  │                         │                   │
│  └─────────────────────────┘  └─────────────────────────┘                   │
│                                                                              │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                   │
│  │ ○ Net Zero 2050        │  │ ○ Custom Target         │                   │
│  │                         │  │                         │                   │
│  │ Long-term commitment    │  │ Define your own         │                   │
│  │ to net zero emissions   │  │ reduction target        │                   │
│  └─────────────────────────┘  └─────────────────────────┘                   │
│                                                                              │
│  Based on your current emissions (4,000 tCO2e), here's what each means:     │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Target        │ 2025        │ 2030        │ 2050                    │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  SBTi 1.5°C    │ 3,580 tCO2e │ 2,320 tCO2e │ 400 tCO2e (Net Zero)   │   │
│  │  SBTi WB 2°C   │ 3,750 tCO2e │ 3,000 tCO2e │ 600 tCO2e              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│                                            [Back]  [Continue →]             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 5.2.3 Personalized Recommendations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Recommended Initiatives                         Based on YOUR data         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Filter: [All Categories ▼]  [All Sites ▼]  Sort by: [Impact ▼]            │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  #1  RENEWABLE ENERGY PPA                              IMPACT: HIGH   │   │
│  │  ────────────────────────────────────────────────────────────────────│   │
│  │                                                                       │   │
│  │  Why this is recommended for you:                                    │   │
│  │  "Your electricity consumption (1,200 tCO2e) accounts for 30% of     │   │
│  │   your total footprint. This is your second-largest emission source  │   │
│  │   and offers a clear path to significant reduction."                 │   │
│  │                                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │ Reduction   │  │ Investment  │  │ Payback     │  │ ROI         │ │   │
│  │  │ -1,080 tCO2e│  │ $180,000    │  │ 4.5 years   │  │ 145%        │ │   │
│  │  │ (27% total) │  │ (est.)      │  │             │  │ (10-year)   │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  │                                                                       │   │
│  │  Complexity: ●●○ Medium    Timeline: 6-12 months                     │   │
│  │                                                                       │   │
│  │  Co-benefits: Energy cost savings, Price stability, Brand value      │   │
│  │                                                                       │   │
│  │                               [Learn More]  [+ Add to Scenario]       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  #2  FLEET ELECTRIFICATION                            IMPACT: HIGH    │   │
│  │  ────────────────────────────────────────────────────────────────────│   │
│  │                                                                       │   │
│  │  Why this is recommended for you:                                    │   │
│  │  "Your company vehicles consume diesel equivalent to 800 tCO2e/year. │   │
│  │   With 12 vehicles in your fleet, transitioning to EVs could reduce  │   │
│  │   emissions by up to 80%."                                           │   │
│  │                                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │ Reduction   │  │ Investment  │  │ Payback     │  │ ROI         │ │   │
│  │  │ -640 tCO2e  │  │ $420,000    │  │ 6.2 years   │  │ 95%         │ │   │
│  │  │ (16% total) │  │ (est.)      │  │             │  │ (10-year)   │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  │                                                                       │   │
│  │                               [Learn More]  [+ Add to Scenario]       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 5.2.4 Scenario Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Compare Scenarios                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐    │
│  │ AGGRESSIVE         │  │ MODERATE           │  │ CONSERVATIVE       │    │
│  │ ──────────────────│  │ ──────────────────│  │ ──────────────────│    │
│  │                    │  │                    │  │                    │    │
│  │ Initiatives: 8     │  │ Initiatives: 5     │  │ Initiatives: 3     │    │
│  │                    │  │                    │  │                    │    │
│  │ Reduction:         │  │ Reduction:         │  │ Reduction:         │    │
│  │ -2,100 tCO2e (53%) │  │ -1,500 tCO2e (38%) │  │ -900 tCO2e (23%)   │    │
│  │                    │  │                    │  │                    │    │
│  │ Investment:        │  │ Investment:        │  │ Investment:        │    │
│  │ $850,000           │  │ $480,000           │  │ $220,000           │    │
│  │                    │  │                    │  │                    │    │
│  │ Target achieved:   │  │ Target achieved:   │  │ Target achieved:   │    │
│  │ ✓ 126% of 2030     │  │ ✓ 90% of 2030      │  │ ✗ 55% of 2030      │    │
│  │                    │  │                    │  │                    │    │
│  │ [Select ✓]         │  │ [Select]           │  │ [Select]           │    │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  EMISSIONS TRAJECTORY COMPARISON                                      │   │
│  │                                                                       │   │
│  │  4,000 ─┬──────────────────────────────────────────────────────────  │   │
│  │         │  ╲                                                          │   │
│  │  3,000 ─┤   ╲_____ Conservative                                      │   │
│  │         │    ╲                                                        │   │
│  │  2,000 ─┤     ╲_____ Moderate                                        │   │
│  │         │      ╲                                                      │   │
│  │  1,000 ─┤       ╲_____ Aggressive         ← Target (2,320 tCO2e)     │   │
│  │         │                                                             │   │
│  │      0 ─┴──────┬──────┬──────┬──────┬──────┬──────────────────────   │   │
│  │              2024   2025   2026   2027   2028   2029   2030          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 5.2.5 Roadmap View (Gantt)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Implementation Roadmap                        Scenario: Aggressive         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │        2024          2025          2026          2027          2028  │   │
│  │  Q3  Q4  │  Q1  Q2  Q3  Q4  │  Q1  Q2  Q3  Q4  │  Q1  Q2  Q3  Q4    │   │
│  │  ────────────────────────────────────────────────────────────────────│   │
│  │                                                                       │   │
│  │  LED Lighting Retrofit                                               │   │
│  │  [████████]                                                          │   │
│  │  -150 tCO2e | $45K                                                   │   │
│  │                                                                       │   │
│  │  Renewable Energy PPA (Negotiation → Implementation)                 │   │
│  │  [    ████████████████████]                                          │   │
│  │  -1,080 tCO2e | $180K                                                │   │
│  │                                                                       │   │
│  │  Fleet EV Transition (Phase 1: 6 vehicles)                           │   │
│  │  [              ██████████████]                                      │   │
│  │  -320 tCO2e | $210K                                                  │   │
│  │                                                                       │   │
│  │  Supplier Engagement Program                                         │   │
│  │  [        ████████████████████████████████]                          │   │
│  │  -400 tCO2e | $80K                                                   │   │
│  │                                                                       │   │
│  │  Fleet EV Transition (Phase 2: 6 vehicles)                           │   │
│  │  [                              ██████████████]                      │   │
│  │  -320 tCO2e | $210K                                                  │   │
│  │                                                                       │   │
│  │  ────────────────────────────────────────────────────────────────────│   │
│  │                                                                       │   │
│  │  MILESTONES:                                                         │   │
│  │  ◆ 2024 Q4: Quick wins complete (-150 tCO2e)                        │   │
│  │  ◆ 2025 Q4: Renewable energy live (-1,230 tCO2e cumulative)         │   │
│  │  ◆ 2027 Q2: Phase 1 fleet complete (-1,550 tCO2e cumulative)        │   │
│  │  ◆ 2028 Q4: All initiatives complete (-2,100 tCO2e cumulative)      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Summary:                                                                    │
│  • Total Investment: $850,000 over 4 years                                  │
│  • Total Reduction: 2,100 tCO2e/year (53% of baseline)                     │
│  • Target Achievement: 126% of SBTi 2030 target                            │
│                                                                              │
│  [Export Roadmap]  [Print]  [Share with Team]                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 5.2.6 Progress Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Progress Tracking                                        Updated: Jan 2026 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  TARGET: SBTi 1.5°C Aligned (2030)                                   │   │
│  │                                                                       │   │
│  │  Current: 3,400 tCO2e    Target: 2,320 tCO2e    Gap: 1,080 tCO2e    │   │
│  │                                                                       │   │
│  │  [████████████████░░░░░░░░░░░░░░░░░░░░░░] 47% to target              │   │
│  │                                                                       │   │
│  │  Status: ✓ ON TRACK                                                  │   │
│  │  "You've reduced 600 tCO2e (15%) from your baseline. At current pace,│   │
│  │   you'll exceed your 2030 target by 8%."                             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌───────────────────────────────────┐  ┌───────────────────────────────┐  │
│  │  ACTUAL vs PLANNED               │  │  INITIATIVE STATUS            │  │
│  │  ───────────────────────────────│  │  ───────────────────────────  │  │
│  │                                   │  │                               │  │
│  │  [LINE CHART]                     │  │  ✓ LED Lighting    Complete  │  │
│  │                                   │  │  ● Renewable PPA   In Progress│  │
│  │  --- Planned trajectory          │  │  ○ Fleet Phase 1   Planned    │  │
│  │  ─── Actual emissions            │  │  ○ Fleet Phase 2   Planned    │  │
│  │                                   │  │  ○ Supplier Prog.  Planned    │  │
│  │  2024: Actual 15% ahead of plan  │  │                               │  │
│  │  2025: On track                  │  │  Progress: 1/5 complete       │  │
│  │                                   │  │  Reduction achieved: 150 tCO2e│  │
│  └───────────────────────────────────┘  └───────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  KEY METRICS                                                          │   │
│  │                                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │ Reduction   │  │ Investment  │  │ Savings     │  │ ROI to Date │ │   │
│  │  │ Achieved    │  │ to Date     │  │ to Date     │  │             │ │   │
│  │  │ ──────────  │  │ ──────────  │  │ ──────────  │  │ ──────────  │ │   │
│  │  │ 600 tCO2e   │  │ $245,000    │  │ $68,000     │  │ 28%         │ │   │
│  │  │ 15% ↓       │  │ 29% of plan │  │             │  │ (annualized)│ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  ALERTS & RECOMMENDATIONS                                             │   │
│  │                                                                       │   │
│  │  ⚠ Renewable PPA implementation delayed by 2 months.                 │   │
│  │    Consider: Accelerate negotiation or explore interim green tariff. │   │
│  │                                                                       │   │
│  │  ✓ Q3 2025 milestone achieved ahead of schedule!                     │   │
│  │    Cumulative reduction now at 600 tCO2e (target was 450 tCO2e).    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. API Endpoints

### 6.1 Profile Analysis

```
GET /api/decarbonization/profile
  → Returns EmissionProfileAnalysis based on current period data

GET /api/decarbonization/profile/sources
  → Returns detailed breakdown of emission sources

GET /api/decarbonization/profile/trends
  → Returns year-over-year trends (requires multiple periods)
```

### 6.2 Targets

```
GET /api/decarbonization/targets
  → List all targets for organization

POST /api/decarbonization/targets
  → Create new target

GET /api/decarbonization/targets/{id}
  → Get target details

PUT /api/decarbonization/targets/{id}
  → Update target

DELETE /api/decarbonization/targets/{id}
  → Delete target

GET /api/decarbonization/targets/{id}/trajectory
  → Get emissions trajectory to meet target
```

### 6.3 Initiatives & Recommendations

```
GET /api/decarbonization/initiatives
  → List all initiatives in library

GET /api/decarbonization/initiatives/{id}
  → Get initiative details

GET /api/decarbonization/recommendations
  → Get personalized recommendations based on client's emission profile
  → Query params: ?limit=10&category=renewable_energy&min_impact=high
```

### 6.4 Scenarios

```
GET /api/decarbonization/scenarios
  → List scenarios for organization

POST /api/decarbonization/scenarios
  → Create new scenario

GET /api/decarbonization/scenarios/{id}
  → Get scenario details with all initiatives

PUT /api/decarbonization/scenarios/{id}
  → Update scenario

DELETE /api/decarbonization/scenarios/{id}
  → Delete scenario

POST /api/decarbonization/scenarios/{id}/initiatives
  → Add initiative to scenario

DELETE /api/decarbonization/scenarios/{id}/initiatives/{initiative_id}
  → Remove initiative from scenario

POST /api/decarbonization/scenarios/{id}/activate
  → Set as active scenario

GET /api/decarbonization/scenarios/compare
  → Compare multiple scenarios
  → Query params: ?ids=uuid1,uuid2,uuid3
```

### 6.5 Roadmap & Progress

```
GET /api/decarbonization/roadmap
  → Get active scenario's roadmap with milestones

GET /api/decarbonization/progress
  → Get progress tracking data

GET /api/decarbonization/progress/checkpoints
  → Get historical emission checkpoints vs plan

POST /api/decarbonization/progress/checkpoint
  → Create checkpoint from current reporting period
```

### 6.6 Financial Analysis

```
GET /api/decarbonization/financials
  → Get financial summary for active scenario

GET /api/decarbonization/financials/cost-of-inaction
  → Calculate cost of inaction analysis

GET /api/decarbonization/financials/carbon-price-scenarios
  → Get financial projections under different carbon price scenarios
```

---

## 7. Implementation Phases

### Phase 1: Foundation (MVP)
- Emission profile analysis (from existing data)
- Basic target setting (SBTi wizard)
- Initiative library (30-50 pre-built initiatives)
- Basic recommendations engine
- Simple scenario builder (manual selection)

### Phase 2: Financial Layer
- Full financial modeling (ROI, NPV, payback)
- Carbon price scenarios
- Cost of inaction analysis
- Investment timeline

### Phase 3: Execution & Tracking
- Gantt chart roadmap
- Milestone tracking
- Progress dashboard
- Actual vs. planned comparison
- Alerts and notifications

### Phase 4: Intelligence
- AI-powered recommendation ranking
- Industry benchmarking
- Automated reforecasting
- Supplier-specific recommendations
- Integration with external data sources

---

## 8. Success Metrics

### 8.1 User Engagement

| Metric | Target |
|--------|--------|
| % of customers using Pathways | 60%+ |
| Average scenarios created per customer | 2+ |
| Monthly active users (returning) | 40%+ |
| Time spent in module per session | 10+ min |

### 8.2 Business Impact

| Metric | Target |
|--------|--------|
| Upgrade rate (Free → Paid) | 15%+ |
| Churn reduction | 30%+ |
| Revenue per customer increase | 50%+ |

### 8.3 Customer Outcomes

| Metric | Target |
|--------|--------|
| % setting SBTi-aligned targets | 50%+ |
| Average emissions reduction planned | 30%+ |
| % actively tracking progress | 40%+ |

---

## 9. Data Requirements

### 9.1 Minimum Client Data for Recommendations

| Data Point | Required? | Used For |
|------------|-----------|----------|
| At least 1 complete reporting period | Yes | Baseline analysis |
| Activities with valid emission factors | Yes | Source identification |
| Site information (country_code) | Recommended | Regional factors |
| Multiple periods | Recommended | Trend analysis |
| Data quality scores | Recommended | Confidence weighting |

### 9.2 Reference Data to Seed

| Data Set | Records | Source |
|----------|---------|--------|
| Initiative Library | 50-100 | Curated from IEA, CDP, etc. |
| SBTi Sector Pathways | ~20 | SBTi Sectoral Guidance |
| Carbon Price Projections | 3 scenarios | IEA, World Bank |
| Technology Cost Curves | 30+ | IRENA, BloombergNEF |

---

## 10. Integration with Existing Features

### 10.1 Connection to GHG Inventory

```
GHG Inventory (existing)          Decarbonization Pathways (new)
─────────────────────────         ─────────────────────────────

Activities → Emissions      ───►   Emission Profile Analysis
                                   ↓
Reporting Period            ───►   Base Year / Checkpoints
                                   ↓
Sites                       ───►   Site-specific recommendations
                                   ↓
Data Quality Scores         ───►   Confidence weighting
```

### 10.2 Billing Tier Integration

| Tier | Pathways Access |
|------|-----------------|
| Free | View profile analysis only |
| Starter | Set 1 target, view recommendations |
| Professional | Full access: scenarios, roadmap, tracking |
| Enterprise | + API access, + white-labeling |

---

## Appendix A: SBTi Target Calculation

### Near-Term Targets (by 2030)

For 1.5°C alignment:
- **Scope 1+2**: 4.2% linear annual reduction = 42% by 2030 (vs 2020)
- **Scope 3**: Required if >40% of total emissions

For Well-Below 2°C:
- **Scope 1+2**: 2.5% linear annual reduction = 25% by 2030 (vs 2020)

### Long-Term Targets (by 2050)

Net Zero requires:
- 90%+ reduction from baseline
- Residual emissions offset with carbon removal

---

## Appendix B: Initiative Library Schema

See `seed_initiatives.json` for full initiative library data.

---

## Appendix C: Carbon Price Assumptions

| Source | 2025 | 2030 | 2040 | 2050 |
|--------|------|------|------|------|
| IEA Net Zero | $75 | $130 | $200 | $250 |
| World Bank High | $80 | $150 | $300 | $500 |
| EU ETS Current | $70 | $100 | N/A | N/A |

---

*Document Version: 1.0*
*Last Updated: January 2026*
