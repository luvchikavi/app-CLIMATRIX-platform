"""
Decarbonization Pathways API endpoints.
Provides data-driven reduction planning based on client's actual emission profile.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models.core import User, UserRole
from app.models.decarbonization import (
    DecarbonizationTarget,
    Initiative,
    Scenario,
    ScenarioInitiative,
    RoadmapMilestone,
    EmissionCheckpoint,
    EmissionProfileAnalysis,
    PersonalizedRecommendation,
    TargetType,
    TargetFramework,
    InitiativeCategory,
    ScenarioType,
    InitiativeStatus,
    MilestoneStatus,
)
from app.api.auth import get_current_user
from app.services.decarbonization import (
    EmissionProfileService,
    RecommendationEngine,
    TargetCalculationService,
    ScenarioService,
    ProgressTrackingService,
)


router = APIRouter(prefix="/decarbonization", tags=["Decarbonization Pathways"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class TargetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    target_type: str
    framework: str
    base_year: int
    base_year_emissions_tco2e: Decimal
    target_year: int
    target_reduction_percent: Decimal
    target_emissions_tco2e: Decimal
    includes_scope1: bool
    includes_scope2: bool
    includes_scope3: bool
    scope3_categories: Optional[list[str]]
    is_sbti_validated: bool
    is_public: bool
    is_active: bool
    created_at: str


class TargetCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    target_type: TargetType = TargetType.ABSOLUTE
    framework: TargetFramework = TargetFramework.SBTI_1_5C
    base_year: int
    base_year_period_id: Optional[str] = None
    base_year_emissions_tco2e: Decimal
    target_year: int
    target_reduction_percent: Optional[Decimal] = None  # Auto-calculated if framework is SBTi
    target_emissions_tco2e: Optional[Decimal] = None    # Auto-calculated if framework is SBTi
    includes_scope1: bool = True
    includes_scope2: bool = True
    includes_scope3: bool = False
    scope3_categories: Optional[list[str]] = None


class InitiativeResponse(BaseModel):
    id: str
    category: str
    subcategory: Optional[str]
    name: str
    short_description: str
    detailed_description: Optional[str]
    applicable_scopes: list[int]
    applicable_category_codes: list[str]
    applicable_activity_keys: list[str]
    typical_reduction_percent_min: Decimal
    typical_reduction_percent_max: Decimal
    typical_reduction_percent_median: Decimal
    typical_capex_per_tco2e_reduced: Optional[Decimal]
    typical_payback_years_min: Optional[Decimal]
    typical_payback_years_max: Optional[Decimal]
    complexity: str
    implementation_time_months_min: int
    implementation_time_months_max: int
    co_benefits: Optional[list[str]]
    common_barriers: Optional[list[str]]


class ScenarioResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    scenario_type: str
    is_active: bool
    total_reduction_tco2e: Decimal
    total_investment: Decimal
    total_annual_savings: Decimal
    weighted_payback_years: Optional[Decimal]
    target_achievement_percent: Decimal
    carbon_price_scenario: str
    created_at: str
    initiatives_count: int


class ScenarioCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    target_id: str
    scenario_type: ScenarioType = ScenarioType.CUSTOM
    carbon_price_scenario: str = "moderate"


class ScenarioInitiativeRequest(BaseModel):
    initiative_id: str
    target_activity_key: str
    target_site_id: Optional[str] = None
    expected_reduction_tco2e: Decimal
    expected_reduction_percent: Decimal
    capex: Decimal = Decimal("0")
    annual_opex_change: Decimal = Decimal("0")
    annual_savings: Decimal = Decimal("0")
    implementation_start: Optional[date] = None
    implementation_end: Optional[date] = None
    notes: Optional[str] = None


class ScenarioInitiativeResponse(BaseModel):
    id: str
    scenario_id: str
    initiative_id: str
    initiative_name: str
    target_activity_key: str
    target_site_id: Optional[str]
    expected_reduction_tco2e: Decimal
    expected_reduction_percent: Decimal
    capex: Decimal
    annual_savings: Decimal
    implementation_start: Optional[str]
    implementation_end: Optional[str]
    status: str
    priority_order: int


class TrajectoryResponse(BaseModel):
    target_id: str
    base_year: int
    base_year_emissions: Decimal
    target_year: int
    target_emissions: Decimal
    trajectory: dict[int, Decimal]


class CheckpointResponse(BaseModel):
    id: str
    checkpoint_year: int
    actual_emissions_tco2e: Decimal
    planned_emissions_tco2e: Decimal
    variance_tco2e: Decimal
    variance_percent: Decimal
    on_track: bool
    created_at: str


# ============================================================================
# EMISSION PROFILE ENDPOINTS
# ============================================================================

@router.get("/profile", response_model=EmissionProfileAnalysis)
async def get_emission_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    period_id: UUID = Query(..., description="Reporting period ID to analyze"),
):
    """
    Get emission profile analysis for a reporting period.
    This is the foundation for personalized recommendations.
    """
    try:
        profile = await EmissionProfileService.analyze_period(
            session=session,
            organization_id=current_user.organization_id,
            period_id=period_id,
        )
        return profile
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# RECOMMENDATIONS ENDPOINTS
# ============================================================================

@router.get("/recommendations", response_model=list[PersonalizedRecommendation])
async def get_recommendations(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    period_id: UUID = Query(..., description="Reporting period ID"),
    limit: int = Query(default=10, le=50),
    category: Optional[InitiativeCategory] = Query(default=None),
):
    """
    Get personalized reduction recommendations based on client's emission data.
    Recommendations are matched to actual emission sources and ranked by impact.
    """
    recommendations = await RecommendationEngine.generate_recommendations(
        session=session,
        organization_id=current_user.organization_id,
        period_id=period_id,
        limit=limit,
        category_filter=category,
    )
    return recommendations


# ============================================================================
# TARGETS ENDPOINTS
# ============================================================================

@router.get("/targets", response_model=list[TargetResponse])
async def list_targets(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """List all decarbonization targets for the organization."""
    result = await session.execute(
        select(DecarbonizationTarget)
        .where(DecarbonizationTarget.organization_id == current_user.organization_id)
        .order_by(DecarbonizationTarget.target_year)
    )
    targets = result.scalars().all()

    return [
        TargetResponse(
            id=str(t.id),
            name=t.name,
            description=t.description,
            target_type=t.target_type.value,
            framework=t.framework.value,
            base_year=t.base_year,
            base_year_emissions_tco2e=t.base_year_emissions_tco2e,
            target_year=t.target_year,
            target_reduction_percent=t.target_reduction_percent,
            target_emissions_tco2e=t.target_emissions_tco2e,
            includes_scope1=t.includes_scope1,
            includes_scope2=t.includes_scope2,
            includes_scope3=t.includes_scope3,
            scope3_categories=t.scope3_categories,
            is_sbti_validated=t.is_sbti_validated,
            is_public=t.is_public,
            is_active=t.is_active,
            created_at=t.created_at.isoformat(),
        )
        for t in targets
    ]


@router.post("/targets", response_model=TargetResponse)
async def create_target(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    request: TargetCreateRequest,
):
    """
    Create a new decarbonization target.
    For SBTi frameworks, target emissions are auto-calculated.
    """
    # Auto-calculate target if using SBTi framework
    if request.framework in [TargetFramework.SBTI_1_5C, TargetFramework.SBTI_WELL_BELOW_2C, TargetFramework.NET_ZERO]:
        target_emissions, reduction_pct = TargetCalculationService.calculate_target_emissions(
            base_year_emissions=request.base_year_emissions_tco2e,
            base_year=request.base_year,
            target_year=request.target_year,
            framework=request.framework,
        )
    else:
        if request.target_reduction_percent is None or request.target_emissions_tco2e is None:
            raise HTTPException(
                status_code=400,
                detail="Custom targets require target_reduction_percent and target_emissions_tco2e"
            )
        target_emissions = request.target_emissions_tco2e
        reduction_pct = request.target_reduction_percent

    target = DecarbonizationTarget(
        organization_id=current_user.organization_id,
        name=request.name,
        description=request.description,
        target_type=request.target_type,
        framework=request.framework,
        base_year=request.base_year,
        base_year_period_id=UUID(request.base_year_period_id) if request.base_year_period_id else None,
        base_year_emissions_tco2e=request.base_year_emissions_tco2e,
        target_year=request.target_year,
        target_reduction_percent=reduction_pct,
        target_emissions_tco2e=target_emissions,
        includes_scope1=request.includes_scope1,
        includes_scope2=request.includes_scope2,
        includes_scope3=request.includes_scope3,
        scope3_categories=request.scope3_categories,
        created_by_id=current_user.id,
    )

    session.add(target)
    await session.commit()
    await session.refresh(target)

    return TargetResponse(
        id=str(target.id),
        name=target.name,
        description=target.description,
        target_type=target.target_type.value,
        framework=target.framework.value,
        base_year=target.base_year,
        base_year_emissions_tco2e=target.base_year_emissions_tco2e,
        target_year=target.target_year,
        target_reduction_percent=target.target_reduction_percent,
        target_emissions_tco2e=target.target_emissions_tco2e,
        includes_scope1=target.includes_scope1,
        includes_scope2=target.includes_scope2,
        includes_scope3=target.includes_scope3,
        scope3_categories=target.scope3_categories,
        is_sbti_validated=target.is_sbti_validated,
        is_public=target.is_public,
        is_active=target.is_active,
        created_at=target.created_at.isoformat(),
    )


@router.get("/targets/{target_id}", response_model=TargetResponse)
async def get_target(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    target_id: UUID,
):
    """Get a specific target by ID."""
    result = await session.execute(
        select(DecarbonizationTarget)
        .where(DecarbonizationTarget.id == target_id)
        .where(DecarbonizationTarget.organization_id == current_user.organization_id)
    )
    target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    return TargetResponse(
        id=str(target.id),
        name=target.name,
        description=target.description,
        target_type=target.target_type.value,
        framework=target.framework.value,
        base_year=target.base_year,
        base_year_emissions_tco2e=target.base_year_emissions_tco2e,
        target_year=target.target_year,
        target_reduction_percent=target.target_reduction_percent,
        target_emissions_tco2e=target.target_emissions_tco2e,
        includes_scope1=target.includes_scope1,
        includes_scope2=target.includes_scope2,
        includes_scope3=target.includes_scope3,
        scope3_categories=target.scope3_categories,
        is_sbti_validated=target.is_sbti_validated,
        is_public=target.is_public,
        is_active=target.is_active,
        created_at=target.created_at.isoformat(),
    )


@router.get("/targets/{target_id}/trajectory", response_model=TrajectoryResponse)
async def get_target_trajectory(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    target_id: UUID,
):
    """Get the emissions trajectory for a target."""
    result = await session.execute(
        select(DecarbonizationTarget)
        .where(DecarbonizationTarget.id == target_id)
        .where(DecarbonizationTarget.organization_id == current_user.organization_id)
    )
    target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    trajectory = TargetCalculationService.get_trajectory(
        target.base_year_emissions_tco2e,
        target.target_emissions_tco2e,
        target.base_year,
        target.target_year,
    )

    return TrajectoryResponse(
        target_id=str(target.id),
        base_year=target.base_year,
        base_year_emissions=target.base_year_emissions_tco2e,
        target_year=target.target_year,
        target_emissions=target.target_emissions_tco2e,
        trajectory=trajectory,
    )


@router.delete("/targets/{target_id}")
async def delete_target(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    target_id: UUID,
):
    """Delete a target."""
    result = await session.execute(
        select(DecarbonizationTarget)
        .where(DecarbonizationTarget.id == target_id)
        .where(DecarbonizationTarget.organization_id == current_user.organization_id)
    )
    target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    await session.delete(target)
    await session.commit()

    return {"message": "Target deleted"}


# ============================================================================
# INITIATIVES LIBRARY ENDPOINTS
# ============================================================================

@router.get("/initiatives", response_model=list[InitiativeResponse])
async def list_initiatives(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    category: Optional[InitiativeCategory] = Query(default=None),
    scope: Optional[int] = Query(default=None, ge=1, le=3),
):
    """List all initiatives from the library."""
    query = select(Initiative).where(Initiative.is_active == True)

    if category:
        query = query.where(Initiative.category == category)

    result = await session.execute(query.order_by(Initiative.category, Initiative.name))
    initiatives = result.scalars().all()

    # Filter by scope if provided
    if scope:
        initiatives = [i for i in initiatives if scope in i.applicable_scopes]

    return [
        InitiativeResponse(
            id=str(i.id),
            category=i.category.value,
            subcategory=i.subcategory,
            name=i.name,
            short_description=i.short_description,
            detailed_description=i.detailed_description,
            applicable_scopes=i.applicable_scopes,
            applicable_category_codes=i.applicable_category_codes,
            applicable_activity_keys=i.applicable_activity_keys,
            typical_reduction_percent_min=i.typical_reduction_percent_min,
            typical_reduction_percent_max=i.typical_reduction_percent_max,
            typical_reduction_percent_median=i.typical_reduction_percent_median,
            typical_capex_per_tco2e_reduced=i.typical_capex_per_tco2e_reduced,
            typical_payback_years_min=i.typical_payback_years_min,
            typical_payback_years_max=i.typical_payback_years_max,
            complexity=i.complexity.value,
            implementation_time_months_min=i.implementation_time_months_min,
            implementation_time_months_max=i.implementation_time_months_max,
            co_benefits=i.co_benefits,
            common_barriers=i.common_barriers,
        )
        for i in initiatives
    ]


@router.get("/initiatives/{initiative_id}", response_model=InitiativeResponse)
async def get_initiative(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    initiative_id: UUID,
):
    """Get a specific initiative by ID."""
    result = await session.execute(
        select(Initiative).where(Initiative.id == initiative_id)
    )
    initiative = result.scalar_one_or_none()

    if not initiative:
        raise HTTPException(status_code=404, detail="Initiative not found")

    return InitiativeResponse(
        id=str(initiative.id),
        category=initiative.category.value,
        subcategory=initiative.subcategory,
        name=initiative.name,
        short_description=initiative.short_description,
        detailed_description=initiative.detailed_description,
        applicable_scopes=initiative.applicable_scopes,
        applicable_category_codes=initiative.applicable_category_codes,
        applicable_activity_keys=initiative.applicable_activity_keys,
        typical_reduction_percent_min=initiative.typical_reduction_percent_min,
        typical_reduction_percent_max=initiative.typical_reduction_percent_max,
        typical_reduction_percent_median=initiative.typical_reduction_percent_median,
        typical_capex_per_tco2e_reduced=initiative.typical_capex_per_tco2e_reduced,
        typical_payback_years_min=initiative.typical_payback_years_min,
        typical_payback_years_max=initiative.typical_payback_years_max,
        complexity=initiative.complexity.value,
        implementation_time_months_min=initiative.implementation_time_months_min,
        implementation_time_months_max=initiative.implementation_time_months_max,
        co_benefits=initiative.co_benefits,
        common_barriers=initiative.common_barriers,
    )


# ============================================================================
# SCENARIOS ENDPOINTS
# ============================================================================

@router.get("/scenarios", response_model=list[ScenarioResponse])
async def list_scenarios(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    target_id: Optional[UUID] = Query(default=None),
):
    """List all scenarios for the organization."""
    query = select(Scenario).where(Scenario.organization_id == current_user.organization_id)

    if target_id:
        query = query.where(Scenario.target_id == target_id)

    result = await session.execute(query.order_by(Scenario.created_at.desc()))
    scenarios = result.scalars().all()

    response = []
    for s in scenarios:
        # Count initiatives
        init_result = await session.execute(
            select(ScenarioInitiative).where(ScenarioInitiative.scenario_id == s.id)
        )
        initiatives_count = len(init_result.scalars().all())

        response.append(ScenarioResponse(
            id=str(s.id),
            name=s.name,
            description=s.description,
            scenario_type=s.scenario_type.value,
            is_active=s.is_active,
            total_reduction_tco2e=s.total_reduction_tco2e,
            total_investment=s.total_investment,
            total_annual_savings=s.total_annual_savings,
            weighted_payback_years=s.weighted_payback_years,
            target_achievement_percent=s.target_achievement_percent,
            carbon_price_scenario=s.carbon_price_scenario,
            created_at=s.created_at.isoformat(),
            initiatives_count=initiatives_count,
        ))

    return response


@router.post("/scenarios", response_model=ScenarioResponse)
async def create_scenario(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    request: ScenarioCreateRequest,
):
    """Create a new scenario."""
    # Verify target exists and belongs to org
    target_result = await session.execute(
        select(DecarbonizationTarget)
        .where(DecarbonizationTarget.id == UUID(request.target_id))
        .where(DecarbonizationTarget.organization_id == current_user.organization_id)
    )
    if not target_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Target not found")

    scenario = Scenario(
        organization_id=current_user.organization_id,
        target_id=UUID(request.target_id),
        name=request.name,
        description=request.description,
        scenario_type=request.scenario_type,
        carbon_price_scenario=request.carbon_price_scenario,
        created_by_id=current_user.id,
    )

    session.add(scenario)
    await session.commit()
    await session.refresh(scenario)

    return ScenarioResponse(
        id=str(scenario.id),
        name=scenario.name,
        description=scenario.description,
        scenario_type=scenario.scenario_type.value,
        is_active=scenario.is_active,
        total_reduction_tco2e=scenario.total_reduction_tco2e,
        total_investment=scenario.total_investment,
        total_annual_savings=scenario.total_annual_savings,
        weighted_payback_years=scenario.weighted_payback_years,
        target_achievement_percent=scenario.target_achievement_percent,
        carbon_price_scenario=scenario.carbon_price_scenario,
        created_at=scenario.created_at.isoformat(),
        initiatives_count=0,
    )


@router.post("/scenarios/{scenario_id}/activate")
async def activate_scenario(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    scenario_id: UUID,
):
    """Set a scenario as the active/selected scenario."""
    # Get scenario
    result = await session.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.organization_id == current_user.organization_id)
    )
    scenario = result.scalar_one_or_none()

    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Deactivate other scenarios for same target
    other_scenarios_result = await session.execute(
        select(Scenario)
        .where(Scenario.target_id == scenario.target_id)
        .where(Scenario.organization_id == current_user.organization_id)
        .where(Scenario.id != scenario_id)
    )
    for other in other_scenarios_result.scalars().all():
        other.is_active = False
        session.add(other)

    # Activate this scenario
    scenario.is_active = True
    session.add(scenario)
    await session.commit()

    return {"message": "Scenario activated"}


@router.post("/scenarios/{scenario_id}/initiatives", response_model=ScenarioInitiativeResponse)
async def add_initiative_to_scenario(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    scenario_id: UUID,
    request: ScenarioInitiativeRequest,
):
    """Add an initiative to a scenario."""
    # Verify scenario exists and belongs to org
    scenario_result = await session.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.organization_id == current_user.organization_id)
    )
    if not scenario_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Verify initiative exists
    initiative_result = await session.execute(
        select(Initiative).where(Initiative.id == UUID(request.initiative_id))
    )
    initiative = initiative_result.scalar_one_or_none()
    if not initiative:
        raise HTTPException(status_code=404, detail="Initiative not found")

    # Get current max priority order
    max_order_result = await session.execute(
        select(ScenarioInitiative.priority_order)
        .where(ScenarioInitiative.scenario_id == scenario_id)
        .order_by(ScenarioInitiative.priority_order.desc())
        .limit(1)
    )
    max_order = max_order_result.scalar() or 0

    scenario_initiative = ScenarioInitiative(
        scenario_id=scenario_id,
        initiative_id=UUID(request.initiative_id),
        target_activity_key=request.target_activity_key,
        target_site_id=UUID(request.target_site_id) if request.target_site_id else None,
        expected_reduction_tco2e=request.expected_reduction_tco2e,
        expected_reduction_percent=request.expected_reduction_percent,
        capex=request.capex,
        annual_opex_change=request.annual_opex_change,
        annual_savings=request.annual_savings,
        implementation_start=request.implementation_start,
        implementation_end=request.implementation_end,
        notes=request.notes,
        priority_order=max_order + 1,
    )

    session.add(scenario_initiative)
    await session.commit()
    await session.refresh(scenario_initiative)

    # Update scenario metrics
    await ScenarioService.update_scenario_metrics(session, scenario_id)

    return ScenarioInitiativeResponse(
        id=str(scenario_initiative.id),
        scenario_id=str(scenario_initiative.scenario_id),
        initiative_id=str(scenario_initiative.initiative_id),
        initiative_name=initiative.name,
        target_activity_key=scenario_initiative.target_activity_key,
        target_site_id=str(scenario_initiative.target_site_id) if scenario_initiative.target_site_id else None,
        expected_reduction_tco2e=scenario_initiative.expected_reduction_tco2e,
        expected_reduction_percent=scenario_initiative.expected_reduction_percent,
        capex=scenario_initiative.capex,
        annual_savings=scenario_initiative.annual_savings,
        implementation_start=scenario_initiative.implementation_start.isoformat() if scenario_initiative.implementation_start else None,
        implementation_end=scenario_initiative.implementation_end.isoformat() if scenario_initiative.implementation_end else None,
        status=scenario_initiative.status.value,
        priority_order=scenario_initiative.priority_order,
    )


@router.get("/scenarios/{scenario_id}/initiatives", response_model=list[ScenarioInitiativeResponse])
async def list_scenario_initiatives(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    scenario_id: UUID,
):
    """List all initiatives in a scenario."""
    # Verify scenario exists and belongs to org
    scenario_result = await session.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.organization_id == current_user.organization_id)
    )
    if not scenario_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Scenario not found")

    result = await session.execute(
        select(ScenarioInitiative, Initiative)
        .join(Initiative, Initiative.id == ScenarioInitiative.initiative_id)
        .where(ScenarioInitiative.scenario_id == scenario_id)
        .order_by(ScenarioInitiative.priority_order)
    )
    rows = result.all()

    return [
        ScenarioInitiativeResponse(
            id=str(si.id),
            scenario_id=str(si.scenario_id),
            initiative_id=str(si.initiative_id),
            initiative_name=init.name,
            target_activity_key=si.target_activity_key,
            target_site_id=str(si.target_site_id) if si.target_site_id else None,
            expected_reduction_tco2e=si.expected_reduction_tco2e,
            expected_reduction_percent=si.expected_reduction_percent,
            capex=si.capex,
            annual_savings=si.annual_savings,
            implementation_start=si.implementation_start.isoformat() if si.implementation_start else None,
            implementation_end=si.implementation_end.isoformat() if si.implementation_end else None,
            status=si.status.value,
            priority_order=si.priority_order,
        )
        for si, init in rows
    ]


@router.delete("/scenarios/{scenario_id}/initiatives/{initiative_id}")
async def remove_initiative_from_scenario(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    scenario_id: UUID,
    initiative_id: UUID,
):
    """Remove an initiative from a scenario."""
    # Verify scenario exists and belongs to org
    scenario_result = await session.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.organization_id == current_user.organization_id)
    )
    if not scenario_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Find and delete the scenario initiative
    result = await session.execute(
        select(ScenarioInitiative)
        .where(ScenarioInitiative.scenario_id == scenario_id)
        .where(ScenarioInitiative.id == initiative_id)
    )
    scenario_initiative = result.scalar_one_or_none()

    if not scenario_initiative:
        raise HTTPException(status_code=404, detail="Initiative not found in scenario")

    await session.delete(scenario_initiative)
    await session.commit()

    # Update scenario metrics
    await ScenarioService.update_scenario_metrics(session, scenario_id)

    return {"message": "Initiative removed from scenario"}


@router.delete("/scenarios/{scenario_id}")
async def delete_scenario(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    scenario_id: UUID,
):
    """Delete a scenario."""
    result = await session.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.organization_id == current_user.organization_id)
    )
    scenario = result.scalar_one_or_none()

    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Delete associated initiatives first
    await session.execute(
        select(ScenarioInitiative).where(ScenarioInitiative.scenario_id == scenario_id)
    )

    await session.delete(scenario)
    await session.commit()

    return {"message": "Scenario deleted"}


# ============================================================================
# PROGRESS TRACKING ENDPOINTS
# ============================================================================

@router.get("/progress/checkpoints", response_model=list[CheckpointResponse])
async def list_checkpoints(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    target_id: UUID = Query(...),
):
    """List all emission checkpoints for a target."""
    result = await session.execute(
        select(EmissionCheckpoint)
        .where(EmissionCheckpoint.organization_id == current_user.organization_id)
        .where(EmissionCheckpoint.target_id == target_id)
        .order_by(EmissionCheckpoint.checkpoint_year)
    )
    checkpoints = result.scalars().all()

    return [
        CheckpointResponse(
            id=str(c.id),
            checkpoint_year=c.checkpoint_year,
            actual_emissions_tco2e=c.actual_emissions_tco2e,
            planned_emissions_tco2e=c.planned_emissions_tco2e,
            variance_tco2e=c.variance_tco2e,
            variance_percent=c.variance_percent,
            on_track=c.on_track,
            created_at=c.created_at.isoformat(),
        )
        for c in checkpoints
    ]


@router.post("/progress/checkpoints", response_model=CheckpointResponse)
async def create_checkpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    target_id: UUID = Query(...),
    period_id: UUID = Query(...),
):
    """Create an emission checkpoint for progress tracking."""
    try:
        checkpoint = await ProgressTrackingService.create_checkpoint(
            session=session,
            organization_id=current_user.organization_id,
            target_id=target_id,
            period_id=period_id,
        )

        return CheckpointResponse(
            id=str(checkpoint.id),
            checkpoint_year=checkpoint.checkpoint_year,
            actual_emissions_tco2e=checkpoint.actual_emissions_tco2e,
            planned_emissions_tco2e=checkpoint.planned_emissions_tco2e,
            variance_tco2e=checkpoint.variance_tco2e,
            variance_percent=checkpoint.variance_percent,
            on_track=checkpoint.on_track,
            created_at=checkpoint.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
