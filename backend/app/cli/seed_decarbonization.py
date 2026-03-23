"""
Seed decarbonization initiative library + NICE demo decarbonization plan.

Usage:
    python -m app.cli.seed_decarbonization                  # Seed initiatives library
    python -m app.cli.seed_decarbonization --with-nice-demo  # Also seed NICE demo plan
    python -m app.cli.seed_decarbonization --force           # Re-seed
"""
import asyncio
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import typer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import select, delete

from app.config import settings
from app.models.core import Organization, User, Site, ReportingPeriod
from app.models.emission import Activity, Emission
from app.models.decarbonization import (
    Initiative, InitiativeCategory, ComplexityLevel,
    DecarbonizationTarget, TargetType, TargetFramework,
    Scenario, ScenarioType, ScenarioInitiative, InitiativeStatus,
    RoadmapMilestone, MilestoneStatus,
)

# ============================================================================
# INITIATIVE LIBRARY — Curated for software/office companies
# ============================================================================

INITIATIVES = [
    # --- ENERGY EFFICIENCY ---
    {
        "category": "energy_efficiency",
        "subcategory": "lighting",
        "name": "LED Lighting Retrofit",
        "short_description": "Replace all fluorescent/HID lighting with LED fixtures across offices, reducing electricity consumption by 40-60%.",
        "applicable_scopes": [2],
        "applicable_category_codes": ["2"],
        "applicable_activity_keys": ["electricity_il", "electricity_us", "electricity_uk", "electricity_de", "electricity_in", "electricity_sg", "electricity_jp", "electricity_global", "electricity_eu"],
        "typical_reduction_percent_min": 5, "typical_reduction_percent_max": 12, "typical_reduction_percent_median": 8,
        "typical_capex_per_tco2e_reduced": 150, "typical_opex_change_percent": -15,
        "typical_payback_years_min": 1.5, "typical_payback_years_max": 3,
        "complexity": "low", "implementation_time_months_min": 2, "implementation_time_months_max": 6,
        "co_benefits": ["Reduced maintenance costs", "Better workplace lighting quality", "Lower heat generation"],
        "common_barriers": ["Upfront capital", "Tenant restrictions in leased spaces"],
    },
    {
        "category": "energy_efficiency",
        "subcategory": "hvac",
        "name": "Smart HVAC Controls & Optimization",
        "short_description": "Install IoT sensors and AI-driven HVAC controls to optimize heating/cooling schedules based on occupancy and weather.",
        "applicable_scopes": [2],
        "applicable_category_codes": ["2"],
        "applicable_activity_keys": ["electricity_il", "electricity_us", "electricity_uk", "electricity_de", "electricity_in", "electricity_sg", "electricity_jp", "electricity_global"],
        "typical_reduction_percent_min": 10, "typical_reduction_percent_max": 25, "typical_reduction_percent_median": 18,
        "typical_capex_per_tco2e_reduced": 200, "typical_opex_change_percent": -20,
        "typical_payback_years_min": 2, "typical_payback_years_max": 4,
        "complexity": "medium", "implementation_time_months_min": 3, "implementation_time_months_max": 9,
        "co_benefits": ["Improved employee comfort", "Predictive maintenance", "Extended equipment life"],
        "common_barriers": ["Integration with legacy BMS", "Landlord approval needed"],
    },
    {
        "category": "energy_efficiency",
        "subcategory": "it_infrastructure",
        "name": "Data Center & Server Room Efficiency",
        "short_description": "Optimize server room cooling, implement hot/cold aisle containment, and consolidate servers to improve PUE.",
        "applicable_scopes": [2],
        "applicable_category_codes": ["2"],
        "applicable_activity_keys": ["electricity_il", "electricity_us", "electricity_in", "electricity_global"],
        "typical_reduction_percent_min": 8, "typical_reduction_percent_max": 20, "typical_reduction_percent_median": 14,
        "typical_capex_per_tco2e_reduced": 300, "typical_opex_change_percent": -25,
        "typical_payback_years_min": 2, "typical_payback_years_max": 5,
        "complexity": "medium", "implementation_time_months_min": 3, "implementation_time_months_max": 12,
        "co_benefits": ["Improved system reliability", "Reduced cooling costs", "Extended hardware life"],
        "common_barriers": ["Requires IT team coordination", "Potential downtime risk"],
    },
    {
        "category": "energy_efficiency",
        "subcategory": "building_envelope",
        "name": "Building Envelope Improvements",
        "short_description": "Upgrade windows, insulation, and sealing to reduce heating/cooling energy loss by 15-30%.",
        "applicable_scopes": [2],
        "applicable_category_codes": ["2"],
        "applicable_activity_keys": ["electricity_il", "electricity_us", "electricity_uk", "electricity_de", "electricity_global"],
        "typical_reduction_percent_min": 5, "typical_reduction_percent_max": 15, "typical_reduction_percent_median": 10,
        "typical_capex_per_tco2e_reduced": 500, "typical_opex_change_percent": -10,
        "typical_payback_years_min": 5, "typical_payback_years_max": 10,
        "complexity": "high", "implementation_time_months_min": 6, "implementation_time_months_max": 18,
        "co_benefits": ["Noise reduction", "Improved comfort", "Higher property value"],
        "common_barriers": ["High upfront cost", "Not applicable to leased spaces", "Construction disruption"],
    },

    # --- RENEWABLE ENERGY ---
    {
        "category": "renewable_energy",
        "subcategory": "onsite_solar",
        "name": "Rooftop Solar PV Installation",
        "short_description": "Install rooftop solar panels to generate renewable electricity on-site, reducing grid dependency by 20-40%.",
        "applicable_scopes": [2],
        "applicable_category_codes": ["2"],
        "applicable_activity_keys": ["electricity_il", "electricity_us", "electricity_in", "electricity_global"],
        "typical_reduction_percent_min": 15, "typical_reduction_percent_max": 40, "typical_reduction_percent_median": 25,
        "typical_capex_per_tco2e_reduced": 400, "typical_opex_change_percent": -30,
        "typical_payback_years_min": 4, "typical_payback_years_max": 8,
        "complexity": "medium", "implementation_time_months_min": 4, "implementation_time_months_max": 12,
        "co_benefits": ["Energy price hedging", "Corporate sustainability branding", "Potential revenue from feed-in tariffs"],
        "common_barriers": ["Roof structural capacity", "Landlord approval", "Grid connection permits"],
    },
    {
        "category": "renewable_energy",
        "subcategory": "green_tariff",
        "name": "Renewable Energy Procurement (PPA/Green Tariff)",
        "short_description": "Switch to 100% renewable electricity via Power Purchase Agreement or green energy tariff from utility provider.",
        "applicable_scopes": [2],
        "applicable_category_codes": ["2"],
        "applicable_activity_keys": ["electricity_il", "electricity_us", "electricity_uk", "electricity_de", "electricity_in", "electricity_sg", "electricity_jp", "electricity_global", "electricity_eu"],
        "typical_reduction_percent_min": 80, "typical_reduction_percent_max": 100, "typical_reduction_percent_median": 95,
        "typical_capex_per_tco2e_reduced": 20, "typical_opex_change_percent": 5,
        "typical_payback_years_min": 0, "typical_payback_years_max": 1,
        "complexity": "low", "implementation_time_months_min": 1, "implementation_time_months_max": 6,
        "co_benefits": ["100% Scope 2 reduction possible", "SBTi-aligned", "Market-based reporting advantage"],
        "common_barriers": ["5-10% premium on electricity cost", "PPA contract length (10-15 years)", "Availability varies by region"],
    },

    # --- FLEET & TRANSPORT ---
    {
        "category": "fleet_transport",
        "subcategory": "ev_fleet",
        "name": "Fleet Electrification",
        "short_description": "Replace petrol/diesel company vehicles with electric vehicles (EVs), eliminating Scope 1 mobile combustion emissions.",
        "applicable_scopes": [1],
        "applicable_category_codes": ["1.2"],
        "applicable_activity_keys": ["car_petrol_km", "car_diesel_km", "car_hybrid_km", "van_diesel_km"],
        "typical_reduction_percent_min": 60, "typical_reduction_percent_max": 95, "typical_reduction_percent_median": 80,
        "typical_capex_per_tco2e_reduced": 600, "typical_opex_change_percent": -40,
        "typical_payback_years_min": 3, "typical_payback_years_max": 6,
        "complexity": "medium", "implementation_time_months_min": 6, "implementation_time_months_max": 24,
        "co_benefits": ["Lower fuel costs", "Reduced maintenance", "Employee satisfaction", "Brand image"],
        "common_barriers": ["High upfront vehicle cost", "Charging infrastructure needed", "Range anxiety for long routes"],
    },
    {
        "category": "fleet_transport",
        "subcategory": "fuel_efficiency",
        "name": "Eco-Driving Training & Fleet Optimization",
        "short_description": "Implement driver training programs and route optimization software to reduce fuel consumption by 10-15%.",
        "applicable_scopes": [1],
        "applicable_category_codes": ["1.2"],
        "applicable_activity_keys": ["car_petrol_km", "car_diesel_km", "van_diesel_km", "petrol_liters", "diesel_liters_mobile"],
        "typical_reduction_percent_min": 8, "typical_reduction_percent_max": 18, "typical_reduction_percent_median": 12,
        "typical_capex_per_tco2e_reduced": 30, "typical_opex_change_percent": -12,
        "typical_payback_years_min": 0.5, "typical_payback_years_max": 1.5,
        "complexity": "low", "implementation_time_months_min": 1, "implementation_time_months_max": 3,
        "co_benefits": ["Reduced accidents", "Lower maintenance costs", "Fuel cost savings"],
        "common_barriers": ["Requires ongoing training", "Driver resistance"],
    },

    # --- BUSINESS TRAVEL ---
    {
        "category": "behavior_change",
        "subcategory": "travel_policy",
        "name": "Virtual-First Travel Policy",
        "short_description": "Implement a travel policy requiring virtual meeting as default, with manager approval for flights. Target 30-50% reduction in business travel.",
        "applicable_scopes": [3],
        "applicable_category_codes": ["3.6"],
        "applicable_activity_keys": ["flight_short_economy", "flight_long_economy", "flight_long_business", "hotel_night", "rail_km"],
        "typical_reduction_percent_min": 25, "typical_reduction_percent_max": 50, "typical_reduction_percent_median": 35,
        "typical_capex_per_tco2e_reduced": 10, "typical_opex_change_percent": -50,
        "typical_payback_years_min": 0, "typical_payback_years_max": 0.5,
        "complexity": "low", "implementation_time_months_min": 1, "implementation_time_months_max": 3,
        "co_benefits": ["Significant cost savings", "Better work-life balance", "Reduced employee fatigue"],
        "common_barriers": ["Cultural resistance", "Client expectations for in-person meetings", "Sales team pushback"],
    },
    {
        "category": "behavior_change",
        "subcategory": "travel_mode",
        "name": "Rail-First Short-Haul Policy",
        "short_description": "Replace short-haul flights (<500km) with rail travel where available, reducing per-trip emissions by 70-90%.",
        "applicable_scopes": [3],
        "applicable_category_codes": ["3.6"],
        "applicable_activity_keys": ["flight_short_economy"],
        "typical_reduction_percent_min": 60, "typical_reduction_percent_max": 90, "typical_reduction_percent_median": 75,
        "typical_capex_per_tco2e_reduced": 0, "typical_opex_change_percent": -10,
        "typical_payback_years_min": 0, "typical_payback_years_max": 0,
        "complexity": "low", "implementation_time_months_min": 1, "implementation_time_months_max": 2,
        "co_benefits": ["Productive travel time", "Often faster city-center to city-center", "Cost neutral or savings"],
        "common_barriers": ["Limited rail infrastructure in some regions", "Longer travel times for some routes"],
    },

    # --- EMPLOYEE COMMUTING ---
    {
        "category": "behavior_change",
        "subcategory": "commuting",
        "name": "Hybrid Work Policy (3 days office)",
        "short_description": "Formalize hybrid work reducing in-office days to 3/week, cutting commuting emissions by ~40%.",
        "applicable_scopes": [3],
        "applicable_category_codes": ["3.7"],
        "applicable_activity_keys": ["commute_car_petrol", "commute_bus", "commute_rail"],
        "typical_reduction_percent_min": 30, "typical_reduction_percent_max": 50, "typical_reduction_percent_median": 40,
        "typical_capex_per_tco2e_reduced": 5, "typical_opex_change_percent": -20,
        "typical_payback_years_min": 0, "typical_payback_years_max": 0.5,
        "complexity": "low", "implementation_time_months_min": 1, "implementation_time_months_max": 3,
        "co_benefits": ["Office space cost reduction", "Employee satisfaction & retention", "Reduced parking demand"],
        "common_barriers": ["May not suit all roles", "Management trust concerns", "Team coordination challenges"],
    },
    {
        "category": "behavior_change",
        "subcategory": "commuting",
        "name": "Employee Shuttle / Carpool Program",
        "short_description": "Introduce company shuttle buses on major routes or subsidized carpool platform, reducing single-occupancy car commutes.",
        "applicable_scopes": [3],
        "applicable_category_codes": ["3.7"],
        "applicable_activity_keys": ["commute_car_petrol"],
        "typical_reduction_percent_min": 15, "typical_reduction_percent_max": 30, "typical_reduction_percent_median": 22,
        "typical_capex_per_tco2e_reduced": 80, "typical_opex_change_percent": 10,
        "typical_payback_years_min": 2, "typical_payback_years_max": 5,
        "complexity": "medium", "implementation_time_months_min": 3, "implementation_time_months_max": 9,
        "co_benefits": ["Employee benefit/perk", "Reduced parking pressure", "Productive commute time"],
        "common_barriers": ["Route coverage limitations", "Ongoing operational cost", "Low adoption in car-centric regions"],
    },

    # --- WASTE ---
    {
        "category": "waste_reduction",
        "subcategory": "recycling",
        "name": "Zero Waste to Landfill Program",
        "short_description": "Implement comprehensive waste sorting, recycling, and composting to eliminate landfill waste from offices.",
        "applicable_scopes": [3],
        "applicable_category_codes": ["3.5"],
        "applicable_activity_keys": ["waste_landfill_mixed", "waste_recycled_mixed", "waste_recycled_paper", "waste_recycled_plastic"],
        "typical_reduction_percent_min": 50, "typical_reduction_percent_max": 90, "typical_reduction_percent_median": 70,
        "typical_capex_per_tco2e_reduced": 50, "typical_opex_change_percent": -5,
        "typical_payback_years_min": 1, "typical_payback_years_max": 3,
        "complexity": "medium", "implementation_time_months_min": 3, "implementation_time_months_max": 12,
        "co_benefits": ["Cleaner workspace", "Employee engagement", "Regulatory compliance"],
        "common_barriers": ["Contamination in recycling streams", "Requires ongoing education", "Waste hauler capabilities"],
    },
    {
        "category": "waste_reduction",
        "subcategory": "e_waste",
        "name": "IT Equipment Lifecycle Extension & Responsible Disposal",
        "short_description": "Extend laptop/device refresh cycles from 3 to 4-5 years and ensure certified e-waste recycling.",
        "applicable_scopes": [3],
        "applicable_category_codes": ["3.1", "3.5"],
        "applicable_activity_keys": ["spend_it_equipment", "waste_ewaste"],
        "typical_reduction_percent_min": 15, "typical_reduction_percent_max": 30, "typical_reduction_percent_median": 22,
        "typical_capex_per_tco2e_reduced": 0, "typical_opex_change_percent": -20,
        "typical_payback_years_min": 0, "typical_payback_years_max": 0,
        "complexity": "low", "implementation_time_months_min": 2, "implementation_time_months_max": 6,
        "co_benefits": ["Cost savings from fewer purchases", "Reduced e-waste", "Lower embodied carbon"],
        "common_barriers": ["Performance complaints from users", "Warranty expiration risks", "IT security concerns"],
    },

    # --- SUPPLY CHAIN ---
    {
        "category": "supply_chain",
        "subcategory": "procurement",
        "name": "Sustainable IT Procurement Policy",
        "short_description": "Require EPEAT/Energy Star certification for all new IT purchases and prefer refurbished equipment where possible.",
        "applicable_scopes": [3],
        "applicable_category_codes": ["3.1"],
        "applicable_activity_keys": ["spend_it_equipment", "spend_it_services"],
        "typical_reduction_percent_min": 10, "typical_reduction_percent_max": 25, "typical_reduction_percent_median": 15,
        "typical_capex_per_tco2e_reduced": 0, "typical_opex_change_percent": 0,
        "typical_payback_years_min": 0, "typical_payback_years_max": 0,
        "complexity": "low", "implementation_time_months_min": 2, "implementation_time_months_max": 6,
        "co_benefits": ["Lower energy consumption", "Vendor engagement on sustainability", "ESG reporting alignment"],
        "common_barriers": ["Limited product availability", "Higher unit cost for certified products"],
    },
    {
        "category": "supply_chain",
        "subcategory": "cloud",
        "name": "Cloud Provider Green Migration",
        "short_description": "Migrate workloads to cloud providers using 100% renewable energy (AWS, Azure, GCP green regions).",
        "applicable_scopes": [3],
        "applicable_category_codes": ["3.1"],
        "applicable_activity_keys": ["spend_it_services", "spend_it_equipment"],
        "typical_reduction_percent_min": 30, "typical_reduction_percent_max": 70, "typical_reduction_percent_median": 50,
        "typical_capex_per_tco2e_reduced": 100, "typical_opex_change_percent": -10,
        "typical_payback_years_min": 1, "typical_payback_years_max": 3,
        "complexity": "high", "implementation_time_months_min": 6, "implementation_time_months_max": 24,
        "co_benefits": ["Scalability", "Reduced on-prem infrastructure", "Disaster recovery improvement"],
        "common_barriers": ["Migration complexity", "Data sovereignty requirements", "Vendor lock-in concerns"],
    },
    {
        "category": "supply_chain",
        "subcategory": "food",
        "name": "Plant-Forward Catering Policy",
        "short_description": "Shift office catering to 60-80% plant-based meals, reducing food-related emissions significantly.",
        "applicable_scopes": [3],
        "applicable_category_codes": ["3.1"],
        "applicable_activity_keys": ["spend_food_beverages"],
        "typical_reduction_percent_min": 30, "typical_reduction_percent_max": 60, "typical_reduction_percent_median": 40,
        "typical_capex_per_tco2e_reduced": 0, "typical_opex_change_percent": -15,
        "typical_payback_years_min": 0, "typical_payback_years_max": 0,
        "complexity": "low", "implementation_time_months_min": 1, "implementation_time_months_max": 3,
        "co_benefits": ["Cost savings", "Healthier employee diet", "Water footprint reduction"],
        "common_barriers": ["Employee preferences", "Cultural sensitivity", "Caterer capabilities"],
    },

    # --- REFRIGERANTS ---
    {
        "category": "process_change",
        "subcategory": "refrigerants",
        "name": "Low-GWP Refrigerant Transition",
        "short_description": "Replace high-GWP refrigerants (R-410A, R-404A) with low-GWP alternatives (R-32, R-1234yf) during HVAC maintenance.",
        "applicable_scopes": [1],
        "applicable_category_codes": ["1.3"],
        "applicable_activity_keys": ["refrigerant_r410a", "refrigerant_r404a", "refrigerant_r134a"],
        "typical_reduction_percent_min": 50, "typical_reduction_percent_max": 80, "typical_reduction_percent_median": 65,
        "typical_capex_per_tco2e_reduced": 100, "typical_opex_change_percent": 0,
        "typical_payback_years_min": 3, "typical_payback_years_max": 7,
        "complexity": "medium", "implementation_time_months_min": 6, "implementation_time_months_max": 24,
        "co_benefits": ["Future-proofing against F-gas regulations", "Often more energy efficient"],
        "common_barriers": ["Equipment compatibility", "Technician certification needed", "Phased rollout during maintenance cycles"],
    },

    # --- GENERATORS ---
    {
        "category": "energy_efficiency",
        "subcategory": "backup_power",
        "name": "Battery Storage Replacing Diesel Generators",
        "short_description": "Install battery energy storage systems (BESS) as backup power, reducing or eliminating diesel generator use.",
        "applicable_scopes": [1],
        "applicable_category_codes": ["1.1"],
        "applicable_activity_keys": ["diesel_liters"],
        "typical_reduction_percent_min": 60, "typical_reduction_percent_max": 100, "typical_reduction_percent_median": 85,
        "typical_capex_per_tco2e_reduced": 800, "typical_opex_change_percent": -30,
        "typical_payback_years_min": 5, "typical_payback_years_max": 10,
        "complexity": "high", "implementation_time_months_min": 6, "implementation_time_months_max": 18,
        "co_benefits": ["No noise or emissions", "Grid balancing revenue potential", "Faster power switchover"],
        "common_barriers": ["High upfront cost", "Space requirements", "Battery degradation over time"],
    },

    # --- CARBON REMOVAL ---
    {
        "category": "carbon_removal",
        "subcategory": "offsets",
        "name": "Verified Carbon Credits Portfolio",
        "short_description": "Purchase high-quality carbon credits (Gold Standard / Verra VCS) to offset residual emissions that cannot be reduced.",
        "applicable_scopes": [1, 2, 3],
        "applicable_category_codes": ["1.1", "1.2", "1.3", "2", "3.1", "3.5", "3.6", "3.7"],
        "applicable_activity_keys": ["electricity_global", "car_petrol_km", "flight_long_economy"],
        "typical_reduction_percent_min": 100, "typical_reduction_percent_max": 100, "typical_reduction_percent_median": 100,
        "typical_capex_per_tco2e_reduced": 25, "typical_opex_change_percent": 0,
        "typical_payback_years_min": 0, "typical_payback_years_max": 0,
        "complexity": "low", "implementation_time_months_min": 1, "implementation_time_months_max": 3,
        "co_benefits": ["Immediate carbon neutrality claim", "Community development co-benefits", "Biodiversity support"],
        "common_barriers": ["Not counted as reduction in SBTi", "Greenwashing perception risk", "Credit quality concerns"],
    },
]


async def seed_initiatives(session: AsyncSession, force: bool = False):
    """Seed the initiative library."""
    result = await session.execute(select(Initiative).limit(1))
    if result.scalar_one_or_none() and not force:
        typer.echo("Initiative library already seeded. Use --force to re-seed.")
        return 0

    if force:
        await session.execute(delete(Initiative))
        await session.commit()

    count = 0
    for data in INITIATIVES:
        initiative = Initiative(
            category=InitiativeCategory(data["category"]),
            subcategory=data.get("subcategory"),
            name=data["name"],
            short_description=data["short_description"],
            applicable_scopes=data["applicable_scopes"],
            applicable_category_codes=data["applicable_category_codes"],
            applicable_activity_keys=data["applicable_activity_keys"],
            typical_reduction_percent_min=Decimal(str(data["typical_reduction_percent_min"])),
            typical_reduction_percent_max=Decimal(str(data["typical_reduction_percent_max"])),
            typical_reduction_percent_median=Decimal(str(data["typical_reduction_percent_median"])),
            typical_capex_per_tco2e_reduced=Decimal(str(data.get("typical_capex_per_tco2e_reduced", 0))) if data.get("typical_capex_per_tco2e_reduced") else None,
            typical_opex_change_percent=Decimal(str(data.get("typical_opex_change_percent", 0))) if data.get("typical_opex_change_percent") is not None else None,
            typical_payback_years_min=Decimal(str(data.get("typical_payback_years_min", 0))) if data.get("typical_payback_years_min") is not None else None,
            typical_payback_years_max=Decimal(str(data.get("typical_payback_years_max", 0))) if data.get("typical_payback_years_max") is not None else None,
            complexity=ComplexityLevel(data["complexity"]),
            implementation_time_months_min=data["implementation_time_months_min"],
            implementation_time_months_max=data["implementation_time_months_max"],
            co_benefits=data.get("co_benefits"),
            common_barriers=data.get("common_barriers"),
        )
        session.add(initiative)
        count += 1

    await session.commit()
    typer.echo(f"Seeded {count} initiatives.")
    return count


async def seed_nice_decarb(session: AsyncSession, force: bool = False):
    """Seed NICE demo decarbonization plan (target + scenario + initiatives)."""

    # Find NICE org
    result = await session.execute(select(Organization).where(Organization.name == "NICE Ltd"))
    org = result.scalar_one_or_none()
    if not org:
        typer.echo("NICE Ltd organization not found. Run seed_nice_demo first.")
        return

    # Check existing target
    result = await session.execute(
        select(DecarbonizationTarget).where(DecarbonizationTarget.organization_id == org.id)
    )
    existing = result.scalar_one_or_none()
    if existing and not force:
        typer.echo("NICE decarbonization plan already exists. Use --force to re-create.")
        return

    # Clean up if force
    if existing:
        # Delete milestones, scenario_initiatives, scenarios, checkpoints, targets
        scenarios_result = await session.execute(
            select(Scenario).where(Scenario.organization_id == org.id)
        )
        for scenario in scenarios_result.scalars().all():
            await session.execute(delete(RoadmapMilestone).where(RoadmapMilestone.scenario_id == scenario.id))
            await session.execute(delete(ScenarioInitiative).where(ScenarioInitiative.scenario_id == scenario.id))
        await session.execute(delete(Scenario).where(Scenario.organization_id == org.id))
        from app.models.decarbonization import EmissionCheckpoint
        await session.execute(delete(EmissionCheckpoint).where(EmissionCheckpoint.organization_id == org.id))
        await session.execute(delete(DecarbonizationTarget).where(DecarbonizationTarget.organization_id == org.id))
        await session.commit()

    # Get admin user
    user_result = await session.execute(
        select(User).where(User.organization_id == org.id, User.role == "ADMIN")
    )
    admin = user_result.scalar_one_or_none()

    # Get period
    period_result = await session.execute(
        select(ReportingPeriod).where(ReportingPeriod.organization_id == org.id)
    )
    period = period_result.scalar_one_or_none()

    # Calculate actual total emissions from data
    from sqlalchemy import func
    emissions_result = await session.execute(
        select(func.sum(Emission.co2e_kg))
        .join(Activity, Activity.id == Emission.activity_id)
        .where(Activity.organization_id == org.id)
    )
    total_co2e_kg = emissions_result.scalar() or Decimal("68000000")
    total_tco2e = total_co2e_kg / 1000

    typer.echo(f"NICE total emissions: {float(total_tco2e):,.0f} tCO2e")

    # --- CREATE TARGET ---
    # NICE board decision: 40% reduction by 2030, aligned with SBTi 1.5°C
    target_reduction = Decimal("40")
    target_emissions = total_tco2e * (1 - target_reduction / 100)

    target = DecarbonizationTarget(
        organization_id=org.id,
        name="NICE 2030 Climate Target",
        description="Board-approved target: 40% absolute reduction in Scope 1+2+3 emissions by 2030, aligned with SBTi 1.5°C pathway. Approved Q1 2025.",
        target_type=TargetType.ABSOLUTE,
        framework=TargetFramework.SBTI_1_5C,
        base_year=2025,
        base_year_period_id=period.id if period else None,
        base_year_emissions_tco2e=total_tco2e,
        target_year=2030,
        target_reduction_percent=target_reduction,
        target_emissions_tco2e=target_emissions,
        includes_scope1=True,
        includes_scope2=True,
        includes_scope3=True,
        scope3_categories=["3.1", "3.5", "3.6", "3.7"],
        is_sbti_validated=False,
        is_public=True,
        is_active=True,
        created_by_id=admin.id if admin else None,
    )
    session.add(target)
    await session.flush()

    # --- CREATE SCENARIO ---
    scenario = Scenario(
        organization_id=org.id,
        target_id=target.id,
        name="NICE Accelerated Decarbonization Plan",
        description="Comprehensive plan combining renewable energy procurement, fleet electrification, travel policy changes, and operational efficiency improvements.",
        scenario_type=ScenarioType.AGGRESSIVE,
        is_active=True,
        carbon_price_scenario="moderate",
        assumed_carbon_price_2030=Decimal("75"),
        created_by_id=admin.id if admin else None,
    )
    session.add(scenario)
    await session.flush()

    # --- ADD INITIATIVES TO SCENARIO ---
    # Get all initiatives
    init_result = await session.execute(select(Initiative))
    all_initiatives = {i.name: i for i in init_result.scalars().all()}

    # Get sites for site-specific initiatives
    sites_result = await session.execute(
        select(Site).where(Site.organization_id == org.id, Site.is_active == True)
    )
    sites = {s.name: s for s in sites_result.scalars().all()}

    # Define the NICE scenario initiatives with realistic numbers
    nice_initiatives = [
        {
            "initiative_name": "Renewable Energy Procurement (PPA/Green Tariff)",
            "target_activity_key": "electricity_il",
            "expected_reduction_tco2e": Decimal("11500"),
            "expected_reduction_percent": Decimal("90"),
            "capex": Decimal("50000"),
            "annual_savings": Decimal("0"),
            "annual_opex_change": Decimal("120000"),  # 5% premium
            "start": date(2025, 7, 1), "end": date(2026, 1, 1),
            "status": "in_progress", "priority": 1,
            "notes": "Phase 1: Israel offices (Ra'anana + Lod). Phase 2: US offices by 2027.",
        },
        {
            "initiative_name": "Smart HVAC Controls & Optimization",
            "target_activity_key": "electricity_us",
            "expected_reduction_tco2e": Decimal("2300"),
            "expected_reduction_percent": Decimal("18"),
            "capex": Decimal("460000"),
            "annual_savings": Decimal("180000"),
            "annual_opex_change": Decimal("-180000"),
            "start": date(2025, 10, 1), "end": date(2026, 6, 1),
            "status": "planned", "priority": 2,
            "notes": "Rollout across all US offices (Hoboken, Richardson, Sandy, Atlanta, Denver).",
        },
        {
            "initiative_name": "Virtual-First Travel Policy",
            "target_activity_key": "flight_long_economy",
            "expected_reduction_tco2e": Decimal("3800"),
            "expected_reduction_percent": Decimal("35"),
            "capex": Decimal("50000"),
            "annual_savings": Decimal("2500000"),
            "annual_opex_change": Decimal("-2500000"),
            "start": date(2025, 4, 1), "end": date(2025, 7, 1),
            "status": "in_progress", "priority": 3,
            "notes": "Policy approved by CEO. Requires VP approval for any international flight. Video conferencing infrastructure upgraded.",
        },
        {
            "initiative_name": "Hybrid Work Policy (3 days office)",
            "target_activity_key": "commute_car_petrol",
            "expected_reduction_tco2e": Decimal("4200"),
            "expected_reduction_percent": Decimal("40"),
            "capex": Decimal("200000"),
            "annual_savings": Decimal("800000"),
            "annual_opex_change": Decimal("-800000"),
            "start": date(2025, 1, 1), "end": date(2025, 3, 1),
            "status": "completed", "priority": 4,
            "notes": "Already implemented company-wide. Estimated 40% reduction in daily commuting. Office space optimization in progress.",
        },
        {
            "initiative_name": "Fleet Electrification",
            "target_activity_key": "car_petrol_km",
            "expected_reduction_tco2e": Decimal("850"),
            "expected_reduction_percent": Decimal("80"),
            "capex": Decimal("1200000"),
            "annual_savings": Decimal("200000"),
            "annual_opex_change": Decimal("-200000"),
            "start": date(2026, 1, 1), "end": date(2028, 6, 1),
            "status": "planned", "priority": 5,
            "notes": "Replace 80 vehicles in IL + US fleet with EVs over 2.5 years. Install charging stations at Ra'anana HQ and Hoboken.",
        },
        {
            "initiative_name": "LED Lighting Retrofit",
            "target_activity_key": "electricity_in",
            "expected_reduction_tco2e": Decimal("650"),
            "expected_reduction_percent": Decimal("8"),
            "capex": Decimal("120000"),
            "annual_savings": Decimal("95000"),
            "annual_opex_change": Decimal("-95000"),
            "start": date(2025, 9, 1), "end": date(2026, 3, 1),
            "status": "planned", "priority": 6,
            "notes": "Priority: India offices (Pune + Bangalore) — highest grid carbon intensity.",
        },
        {
            "initiative_name": "Zero Waste to Landfill Program",
            "target_activity_key": "waste_landfill_mixed",
            "expected_reduction_tco2e": Decimal("280"),
            "expected_reduction_percent": Decimal("70"),
            "capex": Decimal("80000"),
            "annual_savings": Decimal("30000"),
            "annual_opex_change": Decimal("-30000"),
            "start": date(2025, 6, 1), "end": date(2026, 6, 1),
            "status": "planned", "priority": 7,
            "notes": "Start with HQ sites, expand to all offices by 2027.",
        },
        {
            "initiative_name": "Low-GWP Refrigerant Transition",
            "target_activity_key": "refrigerant_r410a",
            "expected_reduction_tco2e": Decimal("450"),
            "expected_reduction_percent": Decimal("65"),
            "capex": Decimal("350000"),
            "annual_savings": Decimal("20000"),
            "annual_opex_change": Decimal("-20000"),
            "start": date(2026, 1, 1), "end": date(2028, 12, 31),
            "status": "planned", "priority": 8,
            "notes": "Replace R-410A with R-32 during scheduled HVAC maintenance cycles.",
        },
        {
            "initiative_name": "Sustainable IT Procurement Policy",
            "target_activity_key": "spend_it_equipment",
            "expected_reduction_tco2e": Decimal("1500"),
            "expected_reduction_percent": Decimal("15"),
            "capex": Decimal("0"),
            "annual_savings": Decimal("0"),
            "annual_opex_change": Decimal("0"),
            "start": date(2025, 7, 1), "end": date(2025, 12, 31),
            "status": "planned", "priority": 9,
            "notes": "EPEAT Gold requirement for all new hardware. Prefer refurbished where possible.",
        },
        {
            "initiative_name": "Employee Shuttle / Carpool Program",
            "target_activity_key": "commute_car_petrol",
            "expected_reduction_tco2e": Decimal("1200"),
            "expected_reduction_percent": Decimal("22"),
            "capex": Decimal("500000"),
            "annual_savings": Decimal("0"),
            "annual_opex_change": Decimal("350000"),
            "start": date(2026, 3, 1), "end": date(2026, 9, 1),
            "status": "planned", "priority": 10,
            "notes": "Shuttle service for Ra'anana HQ (Tel Aviv routes) and Pune R&D Center.",
        },
    ]

    total_reduction = Decimal("0")
    total_investment = Decimal("0")
    total_savings = Decimal("0")

    for ni in nice_initiatives:
        initiative = all_initiatives.get(ni["initiative_name"])
        if not initiative:
            typer.echo(f"  WARN: Initiative '{ni['initiative_name']}' not found in library")
            continue

        si = ScenarioInitiative(
            scenario_id=scenario.id,
            initiative_id=initiative.id,
            target_activity_key=ni["target_activity_key"],
            expected_reduction_tco2e=ni["expected_reduction_tco2e"],
            expected_reduction_percent=ni["expected_reduction_percent"],
            capex=ni["capex"],
            annual_opex_change=ni["annual_opex_change"],
            annual_savings=ni["annual_savings"],
            implementation_start=ni["start"],
            implementation_end=ni["end"],
            status=InitiativeStatus(ni["status"]),
            priority_order=ni["priority"],
            notes=ni.get("notes"),
        )
        session.add(si)
        total_reduction += ni["expected_reduction_tco2e"]
        total_investment += ni["capex"]
        total_savings += ni["annual_savings"]

    # Update scenario metrics
    scenario.total_reduction_tco2e = total_reduction
    scenario.total_investment = total_investment
    scenario.total_annual_savings = total_savings
    required_reduction = total_tco2e * target_reduction / 100
    scenario.target_achievement_percent = min(
        Decimal("100"),
        (total_reduction / required_reduction * 100) if required_reduction > 0 else Decimal("0")
    )
    scenario.weighted_payback_years = Decimal("3.2")

    # --- CREATE ROADMAP MILESTONES ---
    milestones = [
        {
            "name": "Quick Wins Complete",
            "description": "Travel policy, hybrid work, and IT procurement policy implemented",
            "target_date": date(2025, 12, 31),
            "milestone_year": 2025,
            "cumulative_reduction_tco2e": Decimal("8000"),
            "cumulative_investment": Decimal("300000"),
            "expected_emissions_tco2e": total_tco2e - Decimal("8000"),
            "status": "pending",
        },
        {
            "name": "Renewable Energy Transition",
            "description": "All Israel offices on 100% renewable electricity. HVAC upgrades complete in US.",
            "target_date": date(2026, 12, 31),
            "milestone_year": 2026,
            "cumulative_reduction_tco2e": Decimal("16000"),
            "cumulative_investment": Decimal("1200000"),
            "expected_emissions_tco2e": total_tco2e - Decimal("16000"),
            "status": "pending",
        },
        {
            "name": "Fleet & Infrastructure Transformation",
            "description": "50% fleet electrified. Shuttle programs operational. LED retrofit complete.",
            "target_date": date(2027, 12, 31),
            "milestone_year": 2027,
            "cumulative_reduction_tco2e": Decimal("21000"),
            "cumulative_investment": Decimal("2500000"),
            "expected_emissions_tco2e": total_tco2e - Decimal("21000"),
            "status": "pending",
        },
        {
            "name": "Global Renewable Expansion",
            "description": "Extend renewable energy procurement to US, UK, and EU offices.",
            "target_date": date(2028, 12, 31),
            "milestone_year": 2028,
            "cumulative_reduction_tco2e": Decimal("24000"),
            "cumulative_investment": Decimal("2800000"),
            "expected_emissions_tco2e": total_tco2e - Decimal("24000"),
            "status": "pending",
        },
        {
            "name": "2030 Target Achievement",
            "description": "40% absolute reduction achieved across all scopes. SBTi validation submitted.",
            "target_date": date(2030, 12, 31),
            "milestone_year": 2030,
            "cumulative_reduction_tco2e": total_reduction,
            "cumulative_investment": total_investment,
            "expected_emissions_tco2e": target_emissions,
            "status": "pending",
        },
    ]

    for m in milestones:
        milestone = RoadmapMilestone(
            scenario_id=scenario.id,
            name=m["name"],
            description=m["description"],
            target_date=m["target_date"],
            milestone_year=m["milestone_year"],
            cumulative_reduction_tco2e=m["cumulative_reduction_tco2e"],
            cumulative_investment=m["cumulative_investment"],
            expected_emissions_tco2e=m["expected_emissions_tco2e"],
            status=MilestoneStatus(m["status"]),
        )
        session.add(milestone)

    await session.commit()

    typer.echo(f"\n{'='*60}")
    typer.echo(f"NICE Decarbonization Plan Seeded")
    typer.echo(f"{'='*60}")
    typer.echo(f"Target:        40% reduction by 2030 ({float(total_tco2e):,.0f} → {float(target_emissions):,.0f} tCO2e)")
    typer.echo(f"Scenario:      Accelerated Decarbonization Plan")
    typer.echo(f"Initiatives:   {len(nice_initiatives)}")
    typer.echo(f"Total Reduction: {float(total_reduction):,.0f} tCO2e ({float(scenario.target_achievement_percent):.0f}% of target)")
    typer.echo(f"Investment:    ${float(total_investment):,.0f}")
    typer.echo(f"Annual Savings: ${float(total_savings):,.0f}")
    typer.echo(f"Milestones:    {len(milestones)} (2025-2030)")
    typer.echo(f"{'='*60}")


cli = typer.Typer()


@cli.command()
def main(
    with_nice_demo: bool = typer.Option(False, "--with-nice-demo", help="Also seed NICE demo decarbonization plan"),
    force: bool = typer.Option(False, "--force", help="Re-seed data"),
):
    """Seed decarbonization initiative library and optionally NICE demo plan."""

    async def run():
        engine = create_async_engine(settings.async_database_url)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            await seed_initiatives(session, force=force)

        if with_nice_demo:
            async with async_session() as session:
                await seed_nice_decarb(session, force=force)

        await engine.dispose()

    asyncio.run(run())


if __name__ == "__main__":
    cli()
