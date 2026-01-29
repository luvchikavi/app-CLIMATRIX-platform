"""
Decarbonization Pathways Service.
Analyzes client's emission profile and generates personalized recommendations.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.core import Organization, ReportingPeriod, Site
from app.models.emission import Activity, Emission, EmissionFactor
from app.models.decarbonization import (
    DecarbonizationTarget,
    Initiative,
    Scenario,
    ScenarioInitiative,
    RoadmapMilestone,
    EmissionCheckpoint,
    EmissionSource,
    EmissionProfileAnalysis,
    PersonalizedRecommendation,
    InitiativeCategory,
    TargetFramework,
)


# ============================================================================
# ACTIVITY KEY DISPLAY NAMES
# ============================================================================

ACTIVITY_KEY_DISPLAY_NAMES = {
    # Scope 1 - Stationary Combustion
    "natural_gas_volume": "Natural Gas",
    "natural_gas_kwh": "Natural Gas (Energy)",
    "diesel_stationary": "Diesel (Stationary)",
    "lpg_volume": "LPG",
    "fuel_oil_volume": "Fuel Oil",

    # Scope 1 - Mobile Combustion
    "diesel_volume": "Fleet Diesel",
    "petrol_volume": "Fleet Petrol/Gasoline",
    "company_car_km": "Company Vehicles (Distance)",

    # Scope 1 - Fugitive
    "refrigerant_r134a": "Refrigerant R-134a",
    "refrigerant_r410a": "Refrigerant R-410A",
    "refrigerant_r32": "Refrigerant R-32",

    # Scope 2
    "electricity_kwh": "Purchased Electricity",
    "electricity_renewable": "Renewable Electricity",
    "steam_kwh": "Purchased Steam",
    "heating_kwh": "District Heating",
    "cooling_kwh": "District Cooling",

    # Scope 3.1 - Purchased Goods
    "purchased_goods_plastic": "Purchased Plastics",
    "purchased_goods_steel": "Purchased Steel",
    "purchased_goods_aluminum": "Purchased Aluminum",
    "purchased_goods_paper": "Purchased Paper",
    "purchased_goods_chemicals": "Purchased Chemicals",
    "purchased_goods_electronics": "Purchased Electronics",
    "purchased_goods_textiles": "Purchased Textiles",
    "purchased_services_spend": "Purchased Services (Spend)",

    # Scope 3.3 - Fuel & Energy
    "wtt_electricity": "Well-to-Tank (Electricity)",
    "wtt_natural_gas": "Well-to-Tank (Natural Gas)",
    "wtt_diesel": "Well-to-Tank (Diesel)",
    "td_losses": "T&D Losses",

    # Scope 3.4 - Upstream Transport
    "upstream_transport_road": "Upstream Transport (Road)",
    "upstream_transport_sea": "Upstream Transport (Sea)",
    "upstream_transport_air": "Upstream Transport (Air)",
    "upstream_transport_rail": "Upstream Transport (Rail)",
    "truck_freight_tkm": "Truck Freight",
    "sea_freight_tkm": "Sea Freight",
    "air_freight_tkm": "Air Freight",

    # Scope 3.5 - Waste
    "waste_landfill_mixed": "Waste to Landfill (Mixed)",
    "waste_landfill_organic": "Waste to Landfill (Organic)",
    "waste_recycling": "Waste Recycling",
    "waste_incineration": "Waste Incineration",
    "waste_composting": "Waste Composting",

    # Scope 3.6 - Business Travel
    "flight_economy_km": "Flights (Economy)",
    "flight_business_km": "Flights (Business)",
    "flight_first_km": "Flights (First Class)",
    "hotel_nights": "Hotel Stays",
    "rail_km": "Rail Travel",
    "rental_car_km": "Rental Cars",
    "taxi_km": "Taxi/Rideshare",

    # Scope 3.7 - Employee Commuting
    "commute_car_km": "Employee Commute (Car)",
    "commute_public_transit": "Employee Commute (Public Transit)",
    "commute_cycling": "Employee Commute (Cycling)",
    "remote_work_days": "Remote Work",

    # Scope 3.9 - Downstream Transport
    "downstream_transport_road": "Downstream Transport (Road)",
    "downstream_transport_sea": "Downstream Transport (Sea)",
}


def get_activity_display_name(activity_key: str) -> str:
    """Get human-readable display name for an activity key."""
    return ACTIVITY_KEY_DISPLAY_NAMES.get(activity_key, activity_key.replace("_", " ").title())


# ============================================================================
# EMISSION PROFILE ANALYSIS SERVICE
# ============================================================================

class EmissionProfileService:
    """Service for analyzing organization's emission profile."""

    @staticmethod
    async def analyze_period(
        session: AsyncSession,
        organization_id: UUID,
        period_id: UUID,
    ) -> EmissionProfileAnalysis:
        """
        Analyze emission profile for a specific reporting period.
        This is the core function that reads client's actual data.
        """
        # Get period info
        period_result = await session.execute(
            select(ReportingPeriod)
            .where(ReportingPeriod.id == period_id)
            .where(ReportingPeriod.organization_id == organization_id)
        )
        period = period_result.scalar_one_or_none()
        if not period:
            raise ValueError(f"Period {period_id} not found")

        # Get all activities with emissions for this period
        query = (
            select(
                Activity.scope,
                Activity.category_code,
                Activity.activity_key,
                Activity.site_id,
                Activity.data_quality_score,
                Emission.co2e_kg,
            )
            .join(Emission, Emission.activity_id == Activity.id)
            .where(Activity.organization_id == organization_id)
            .where(Activity.reporting_period_id == period_id)
        )
        result = await session.execute(query)
        rows = result.all()

        if not rows:
            # Return empty analysis
            return EmissionProfileAnalysis(
                organization_id=organization_id,
                period_id=period_id,
                period_name=period.name,
                analysis_date=datetime.utcnow(),
                total_co2e_kg=Decimal("0"),
                total_co2e_tonnes=Decimal("0"),
                scope1_co2e_tonnes=Decimal("0"),
                scope2_co2e_tonnes=Decimal("0"),
                scope3_co2e_tonnes=Decimal("0"),
                emissions_by_category={},
                emissions_by_activity_key={},
                emissions_by_site={},
                top_sources=[],
            )

        # Aggregate data
        total_co2e_kg = Decimal("0")
        scope_totals = {1: Decimal("0"), 2: Decimal("0"), 3: Decimal("0")}
        by_category: dict[str, Decimal] = {}
        by_activity_key: dict[str, dict] = {}  # {key: {total, count, scope, category, quality_sum}}
        by_site: dict[str, Decimal] = {}

        # Get site names for display
        sites_result = await session.execute(
            select(Site).where(Site.organization_id == organization_id)
        )
        sites = {str(s.id): s.name for s in sites_result.scalars().all()}

        for row in rows:
            scope, category_code, activity_key, site_id, quality_score, co2e_kg = row
            co2e_kg = co2e_kg or Decimal("0")

            total_co2e_kg += co2e_kg
            scope_totals[scope] = scope_totals.get(scope, Decimal("0")) + co2e_kg
            by_category[category_code] = by_category.get(category_code, Decimal("0")) + co2e_kg

            # Track by activity key with metadata
            if activity_key not in by_activity_key:
                by_activity_key[activity_key] = {
                    "total": Decimal("0"),
                    "count": 0,
                    "scope": scope,
                    "category": category_code,
                    "quality_sum": 0,
                }
            by_activity_key[activity_key]["total"] += co2e_kg
            by_activity_key[activity_key]["count"] += 1
            by_activity_key[activity_key]["quality_sum"] += quality_score or 5

            # Track by site
            if site_id:
                site_key = str(site_id)
                by_site[site_key] = by_site.get(site_key, Decimal("0")) + co2e_kg

        # Build top sources list (sorted by emissions)
        sources_list = []
        for activity_key, data in by_activity_key.items():
            total_tonnes = data["total"] / Decimal("1000")
            pct = (data["total"] / total_co2e_kg * Decimal("100")) if total_co2e_kg > 0 else Decimal("0")
            avg_quality = Decimal(data["quality_sum"]) / Decimal(data["count"]) if data["count"] > 0 else None

            sources_list.append(EmissionSource(
                activity_key=activity_key,
                display_name=get_activity_display_name(activity_key),
                scope=data["scope"],
                category_code=data["category"],
                total_co2e_kg=data["total"],
                total_co2e_tonnes=total_tonnes,
                percentage_of_total=round(pct, 2),
                activity_count=data["count"],
                data_quality_avg=round(avg_quality, 1) if avg_quality else None,
            ))

        # Sort by total emissions descending
        sources_list.sort(key=lambda x: x.total_co2e_kg, reverse=True)

        # Convert to tonnes for output
        total_tonnes = total_co2e_kg / Decimal("1000")

        # Get previous period for trend calculation
        yoy_change = None
        trend_direction = None
        prev_total = None

        prev_period_query = (
            select(ReportingPeriod)
            .where(ReportingPeriod.organization_id == organization_id)
            .where(ReportingPeriod.end_date < period.start_date)
            .order_by(ReportingPeriod.end_date.desc())
            .limit(1)
        )
        prev_period_result = await session.execute(prev_period_query)
        prev_period = prev_period_result.scalar_one_or_none()

        if prev_period:
            # Get previous period total
            prev_total_query = (
                select(func.sum(Emission.co2e_kg))
                .join(Activity, Activity.id == Emission.activity_id)
                .where(Activity.organization_id == organization_id)
                .where(Activity.reporting_period_id == prev_period.id)
            )
            prev_total_result = await session.execute(prev_total_query)
            prev_total_kg = prev_total_result.scalar() or Decimal("0")
            prev_total = prev_total_kg / Decimal("1000")

            if prev_total_kg > 0:
                change = ((total_co2e_kg - prev_total_kg) / prev_total_kg) * Decimal("100")
                yoy_change = round(change, 1)
                if change > Decimal("5"):
                    trend_direction = "increasing"
                elif change < Decimal("-5"):
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"

        return EmissionProfileAnalysis(
            organization_id=organization_id,
            period_id=period_id,
            period_name=period.name,
            analysis_date=datetime.utcnow(),
            total_co2e_kg=total_co2e_kg,
            total_co2e_tonnes=round(total_tonnes, 2),
            scope1_co2e_tonnes=round(scope_totals[1] / Decimal("1000"), 2),
            scope2_co2e_tonnes=round(scope_totals[2] / Decimal("1000"), 2),
            scope3_co2e_tonnes=round(scope_totals[3] / Decimal("1000"), 2),
            emissions_by_category={k: round(v / Decimal("1000"), 2) for k, v in by_category.items()},
            emissions_by_activity_key={k: round(v["total"] / Decimal("1000"), 2) for k, v in by_activity_key.items()},
            emissions_by_site={sites.get(k, k): round(v / Decimal("1000"), 2) for k, v in by_site.items()},
            top_sources=sources_list[:10],  # Top 10 sources
            yoy_change_percent=yoy_change,
            trend_direction=trend_direction,
            previous_period_total_tonnes=prev_total,
        )


# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================

class RecommendationEngine:
    """
    Generates personalized recommendations based on client's emission profile.
    This is the core intelligence that matches initiatives to actual data.
    """

    @staticmethod
    async def generate_recommendations(
        session: AsyncSession,
        organization_id: UUID,
        period_id: UUID,
        limit: int = 10,
        category_filter: Optional[InitiativeCategory] = None,
    ) -> list[PersonalizedRecommendation]:
        """
        Generate personalized recommendations for an organization.

        The key logic:
        1. Analyze the organization's emission profile
        2. Get initiatives from the library
        3. Match initiatives to client's actual emission sources via activity_key
        4. Calculate personalized reduction potential based on client's data
        5. Score and rank recommendations
        """
        # Step 1: Get emission profile
        profile = await EmissionProfileService.analyze_period(
            session, organization_id, period_id
        )

        if not profile.top_sources:
            return []

        # Step 2: Get active initiatives from library
        query = select(Initiative).where(Initiative.is_active == True)
        if category_filter:
            query = query.where(Initiative.category == category_filter)

        result = await session.execute(query)
        initiatives = result.scalars().all()

        if not initiatives:
            return []

        # Step 3: Match initiatives to client's emission sources
        recommendations = []

        for source in profile.top_sources:
            # Find initiatives that apply to this activity_key
            matching_initiatives = [
                init for init in initiatives
                if source.activity_key in init.applicable_activity_keys
                or source.scope in init.applicable_scopes
            ]

            for initiative in matching_initiatives:
                # Check minimum relevance threshold
                if initiative.min_emissions_for_relevance_tco2e:
                    if source.total_co2e_tonnes < initiative.min_emissions_for_relevance_tco2e:
                        continue

                # Step 4: Calculate personalized reduction potential
                median_reduction_pct = initiative.typical_reduction_percent_median / Decimal("100")
                min_reduction_pct = initiative.typical_reduction_percent_min / Decimal("100")
                max_reduction_pct = initiative.typical_reduction_percent_max / Decimal("100")

                potential_reduction = source.total_co2e_tonnes * median_reduction_pct
                reduction_low = source.total_co2e_tonnes * min_reduction_pct
                reduction_high = source.total_co2e_tonnes * max_reduction_pct

                reduction_pct_of_total = (
                    (potential_reduction / profile.total_co2e_tonnes * Decimal("100"))
                    if profile.total_co2e_tonnes > 0 else Decimal("0")
                )

                # Calculate financials if available
                estimated_capex = None
                estimated_savings = None
                payback = None
                roi = None

                if initiative.typical_capex_per_tco2e_reduced:
                    estimated_capex = potential_reduction * initiative.typical_capex_per_tco2e_reduced

                if initiative.typical_opex_change_percent and estimated_capex:
                    # Assume savings based on capex and opex change
                    # This is simplified - real calculation would use energy prices
                    estimated_savings = abs(initiative.typical_opex_change_percent / Decimal("100") * estimated_capex)

                    if estimated_savings > 0:
                        payback = estimated_capex / estimated_savings
                        # 10-year ROI
                        roi = ((estimated_savings * 10 - estimated_capex) / estimated_capex * Decimal("100"))

                # Step 5: Calculate scores
                impact_score = min(10, int(reduction_pct_of_total / Decimal("3")) + 1)

                complexity_scores = {"low": 9, "medium": 6, "high": 3}
                feasibility_score = complexity_scores.get(initiative.complexity.value, 5)

                priority_score = int((impact_score * 0.6 + feasibility_score * 0.4))

                # Generate relevance explanation
                relevance = (
                    f"Your {source.display_name} emissions ({source.total_co2e_tonnes:.0f} tCO2e) "
                    f"account for {source.percentage_of_total:.1f}% of your total footprint. "
                    f"This initiative could reduce these emissions by {initiative.typical_reduction_percent_min:.0f}-"
                    f"{initiative.typical_reduction_percent_max:.0f}%."
                )

                recommendations.append(PersonalizedRecommendation(
                    initiative_id=initiative.id,
                    initiative_name=initiative.name,
                    initiative_category=initiative.category.value,
                    initiative_description=initiative.short_description,
                    target_activity_key=source.activity_key,
                    target_source_name=source.display_name,
                    target_source_emissions_tco2e=source.total_co2e_tonnes,
                    target_source_percent_of_total=source.percentage_of_total,
                    potential_reduction_tco2e=round(potential_reduction, 1),
                    potential_reduction_low_tco2e=round(reduction_low, 1),
                    potential_reduction_high_tco2e=round(reduction_high, 1),
                    reduction_as_percent_of_total=round(reduction_pct_of_total, 1),
                    estimated_capex=round(estimated_capex, 0) if estimated_capex else None,
                    estimated_annual_savings=round(estimated_savings, 0) if estimated_savings else None,
                    payback_years=round(payback, 1) if payback else None,
                    roi_percent=round(roi, 0) if roi else None,
                    impact_score=impact_score,
                    feasibility_score=feasibility_score,
                    priority_score=priority_score,
                    complexity=initiative.complexity.value,
                    implementation_months_min=initiative.implementation_time_months_min,
                    implementation_months_max=initiative.implementation_time_months_max,
                    co_benefits=initiative.co_benefits,
                    relevance_explanation=relevance,
                ))

        # Sort by priority score (highest first)
        recommendations.sort(key=lambda r: r.priority_score, reverse=True)

        # Remove duplicates (same initiative for same activity_key)
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            key = (rec.initiative_id, rec.target_activity_key)
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(rec)

        return unique_recommendations[:limit]


# ============================================================================
# TARGET CALCULATION SERVICE
# ============================================================================

class TargetCalculationService:
    """Service for calculating SBTi-aligned targets."""

    # SBTi reduction rates (annual, from 2020 baseline)
    SBTI_RATES = {
        TargetFramework.SBTI_1_5C: Decimal("4.2"),      # 4.2% per year = 42% by 2030
        TargetFramework.SBTI_WELL_BELOW_2C: Decimal("2.5"),  # 2.5% per year = 25% by 2030
    }

    @staticmethod
    def calculate_target_emissions(
        base_year_emissions: Decimal,
        base_year: int,
        target_year: int,
        framework: TargetFramework,
    ) -> tuple[Decimal, Decimal]:
        """
        Calculate target emissions and reduction percentage.

        Returns: (target_emissions, reduction_percent)
        """
        if framework == TargetFramework.CUSTOM:
            raise ValueError("Custom framework requires manual target specification")

        if framework == TargetFramework.NET_ZERO:
            # Net zero = 90% reduction by 2050
            years = target_year - base_year
            if target_year >= 2050:
                reduction_pct = Decimal("90")
            else:
                # Linear interpolation to 2050
                total_years = 2050 - base_year
                reduction_pct = Decimal("90") * Decimal(years) / Decimal(total_years)
        else:
            annual_rate = TargetCalculationService.SBTI_RATES.get(framework, Decimal("4.2"))
            years = target_year - base_year
            reduction_pct = annual_rate * Decimal(years)

        reduction_pct = min(reduction_pct, Decimal("100"))
        target_emissions = base_year_emissions * (Decimal("1") - reduction_pct / Decimal("100"))

        return round(target_emissions, 2), round(reduction_pct, 1)

    @staticmethod
    def get_trajectory(
        base_year_emissions: Decimal,
        target_emissions: Decimal,
        base_year: int,
        target_year: int,
    ) -> dict[int, Decimal]:
        """
        Calculate linear trajectory from base year to target year.
        Returns dict of year -> expected emissions.
        """
        trajectory = {}
        years = target_year - base_year

        if years <= 0:
            return {base_year: base_year_emissions}

        annual_reduction = (base_year_emissions - target_emissions) / Decimal(years)

        for i in range(years + 1):
            year = base_year + i
            emissions = base_year_emissions - (annual_reduction * Decimal(i))
            trajectory[year] = round(max(emissions, Decimal("0")), 2)

        return trajectory


# ============================================================================
# SCENARIO SERVICE
# ============================================================================

class ScenarioService:
    """Service for managing decarbonization scenarios."""

    @staticmethod
    async def calculate_scenario_metrics(
        session: AsyncSession,
        scenario_id: UUID,
    ) -> dict:
        """
        Calculate summary metrics for a scenario based on its initiatives.
        """
        # Get scenario with initiatives
        scenario_result = await session.execute(
            select(Scenario).where(Scenario.id == scenario_id)
        )
        scenario = scenario_result.scalar_one_or_none()
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")

        # Get initiatives
        initiatives_result = await session.execute(
            select(ScenarioInitiative).where(ScenarioInitiative.scenario_id == scenario_id)
        )
        initiatives = initiatives_result.scalars().all()

        if not initiatives:
            return {
                "total_reduction_tco2e": Decimal("0"),
                "total_investment": Decimal("0"),
                "total_annual_savings": Decimal("0"),
                "weighted_payback_years": None,
                "target_achievement_percent": Decimal("0"),
            }

        total_reduction = sum(i.expected_reduction_tco2e for i in initiatives)
        total_investment = sum(i.capex for i in initiatives)
        total_savings = sum(i.annual_savings for i in initiatives)

        # Weighted average payback
        weighted_payback = None
        if total_investment > 0 and total_savings > 0:
            weighted_payback = total_investment / total_savings

        # Target achievement
        target_result = await session.execute(
            select(DecarbonizationTarget).where(DecarbonizationTarget.id == scenario.target_id)
        )
        target = target_result.scalar_one_or_none()

        target_achievement = Decimal("0")
        if target:
            required_reduction = target.base_year_emissions_tco2e - target.target_emissions_tco2e
            if required_reduction > 0:
                target_achievement = (total_reduction / required_reduction) * Decimal("100")

        return {
            "total_reduction_tco2e": round(total_reduction, 1),
            "total_investment": round(total_investment, 0),
            "total_annual_savings": round(total_savings, 0),
            "weighted_payback_years": round(weighted_payback, 1) if weighted_payback else None,
            "target_achievement_percent": round(min(target_achievement, Decimal("200")), 1),
        }

    @staticmethod
    async def update_scenario_metrics(
        session: AsyncSession,
        scenario_id: UUID,
    ) -> None:
        """Update a scenario's summary metrics based on its initiatives."""
        metrics = await ScenarioService.calculate_scenario_metrics(session, scenario_id)

        scenario_result = await session.execute(
            select(Scenario).where(Scenario.id == scenario_id)
        )
        scenario = scenario_result.scalar_one()

        scenario.total_reduction_tco2e = metrics["total_reduction_tco2e"]
        scenario.total_investment = metrics["total_investment"]
        scenario.total_annual_savings = metrics["total_annual_savings"]
        scenario.weighted_payback_years = metrics["weighted_payback_years"]
        scenario.target_achievement_percent = metrics["target_achievement_percent"]
        scenario.updated_at = datetime.utcnow()

        session.add(scenario)
        await session.commit()


# ============================================================================
# PROGRESS TRACKING SERVICE
# ============================================================================

class ProgressTrackingService:
    """Service for tracking progress against targets."""

    @staticmethod
    async def create_checkpoint(
        session: AsyncSession,
        organization_id: UUID,
        target_id: UUID,
        period_id: UUID,
    ) -> EmissionCheckpoint:
        """
        Create an emission checkpoint for progress tracking.
        Compares actual emissions to planned trajectory.
        """
        # Get actual emissions for the period
        profile = await EmissionProfileService.analyze_period(
            session, organization_id, period_id
        )
        actual_emissions = profile.total_co2e_tonnes

        # Get target and trajectory
        target_result = await session.execute(
            select(DecarbonizationTarget).where(DecarbonizationTarget.id == target_id)
        )
        target = target_result.scalar_one_or_none()
        if not target:
            raise ValueError(f"Target {target_id} not found")

        # Get period year
        period_result = await session.execute(
            select(ReportingPeriod).where(ReportingPeriod.id == period_id)
        )
        period = period_result.scalar_one()
        checkpoint_year = period.end_date.year

        # Calculate planned emissions for this year
        trajectory = TargetCalculationService.get_trajectory(
            target.base_year_emissions_tco2e,
            target.target_emissions_tco2e,
            target.base_year,
            target.target_year,
        )
        planned_emissions = trajectory.get(checkpoint_year, target.base_year_emissions_tco2e)

        # Calculate variance
        variance = actual_emissions - planned_emissions
        variance_pct = (
            (variance / planned_emissions * Decimal("100"))
            if planned_emissions > 0 else Decimal("0")
        )

        # Determine if on track (within 5% of plan)
        on_track = abs(variance_pct) <= Decimal("5") or variance < Decimal("0")

        # Get active scenario for context
        scenario_result = await session.execute(
            select(Scenario)
            .where(Scenario.organization_id == organization_id)
            .where(Scenario.target_id == target_id)
            .where(Scenario.is_active == True)
        )
        active_scenario = scenario_result.scalar_one_or_none()

        checkpoint = EmissionCheckpoint(
            organization_id=organization_id,
            target_id=target_id,
            scenario_id=active_scenario.id if active_scenario else None,
            reporting_period_id=period_id,
            checkpoint_year=checkpoint_year,
            actual_emissions_tco2e=actual_emissions,
            planned_emissions_tco2e=planned_emissions,
            variance_tco2e=round(variance, 1),
            variance_percent=round(variance_pct, 1),
            on_track=on_track,
        )

        session.add(checkpoint)
        await session.commit()
        await session.refresh(checkpoint)

        return checkpoint
