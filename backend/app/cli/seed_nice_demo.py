"""
Seed NICE Ltd demo data.

Creates a realistic demo with 14 global office sites and mock emission data
based on publicly available information about NICE (NASDAQ/TASE: NICE).

Usage:
    python -m app.cli.seed_nice_demo
    python -m app.cli.seed_nice_demo --force   # Re-create even if exists
"""
import asyncio
import random
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import typer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import select

from app.config import settings
from app.models.core import Organization, User, UserRole, Site, ReportingPeriod
from app.models.emission import Activity, Emission, EmissionFactor, DataSource, ConfidenceLevel
from app.api.auth import get_password_hash
from app.services.calculation import CalculationPipeline, ActivityInput
from app.services.calculation.pipeline import CalculationError


# ============================================================================
# NICE Ltd office data (based on public information)
# ============================================================================

NICE_SITES = [
    {"name": "Ra'anana HQ", "country_code": "IL", "address": "13 Zarchin St, Ra'anana", "grid_region": "IL", "employees": 1800},
    {"name": "Hoboken NJ (Americas HQ)", "country_code": "US", "address": "221 River St, Hoboken, NJ", "grid_region": "US", "employees": 1200},
    {"name": "Richardson TX", "country_code": "US", "address": "Richardson, TX", "grid_region": "US", "employees": 600},
    {"name": "Sandy UT", "country_code": "US", "address": "Sandy, UT", "grid_region": "US", "employees": 500},
    {"name": "Atlanta GA", "country_code": "US", "address": "Atlanta, GA", "grid_region": "US", "employees": 350},
    {"name": "London", "country_code": "GB", "address": "London, United Kingdom", "grid_region": "UK", "employees": 400},
    {"name": "Pune R&D Center", "country_code": "IN", "address": "Pune, Maharashtra, India", "grid_region": "Global", "employees": 1500},
    {"name": "Bangalore", "country_code": "IN", "address": "Bangalore, Karnataka, India", "grid_region": "Global", "employees": 800},
    {"name": "Manila Support Center", "country_code": "PH", "address": "BGC, Taguig, Manila", "grid_region": "Global", "employees": 350},
    {"name": "Singapore", "country_code": "SG", "address": "Singapore", "grid_region": "Global", "employees": 150},
    {"name": "Frankfurt", "country_code": "DE", "address": "Frankfurt am Main, Germany", "grid_region": "EU", "employees": 200},
    {"name": "Tokyo", "country_code": "JP", "address": "Tokyo, Japan", "grid_region": "Global", "employees": 120},
    {"name": "Denver CO", "country_code": "US", "address": "Denver, CO", "grid_region": "US", "employees": 300},
    {"name": "Lod (Actimize R&D)", "country_code": "IL", "address": "Lod, Israel", "grid_region": "IL", "employees": 400},
]

# Grid emission factors per country (kg CO2e / kWh)
GRID_FACTORS = {
    "IL": 0.50, "US": 0.38, "GB": 0.21, "IN": 0.70,
    "PH": 0.60, "SG": 0.41, "DE": 0.35, "JP": 0.45,
}

# Map country to electricity activity_key
ELECTRICITY_KEYS = {
    "IL": "electricity_il", "US": "electricity_us", "GB": "electricity_uk",
    "IN": "electricity_in", "SG": "electricity_sg", "DE": "electricity_de",
    "JP": "electricity_jp", "PH": "electricity_global",
}


def _generate_monthly_activities(site: dict, year: int = 2025) -> list[dict]:
    """Generate realistic monthly activity data for a site."""
    activities = []
    employees = site["employees"]
    country = site["country_code"]

    # ===== SCOPE 1 =====

    # 1.1 Stationary combustion — backup generators (diesel)
    # Larger sites and developing countries use more generator power
    generator_multiplier = 1.5 if country in ("IN", "PH", "IL") else 0.5
    monthly_diesel = employees * 0.08 * generator_multiplier  # liters/month

    if monthly_diesel > 5:
        for month in range(1, 13):
            qty = monthly_diesel * random.uniform(0.7, 1.3)
            activities.append({
                "scope": 1, "category_code": "1.1",
                "activity_key": "diesel_liters",
                "description": f"Backup generator diesel — {date(year, month, 1).strftime('%B')}",
                "quantity": round(qty, 1), "unit": "liters",
                "activity_date": date(year, month, 15),
            })

    # 1.2 Company vehicles (Israel + US offices)
    if country in ("IL", "US") and employees >= 300:
        cars = max(5, employees // 80)
        monthly_km = cars * 1800  # ~1800 km/car/month
        for month in range(1, 13):
            qty = monthly_km * random.uniform(0.8, 1.2)
            activities.append({
                "scope": 1, "category_code": "1.2",
                "activity_key": "car_petrol_km",
                "description": f"Company fleet ({cars} vehicles) — {date(year, month, 1).strftime('%B')}",
                "quantity": round(qty, 0), "unit": "km",
                "activity_date": date(year, month, 15),
            })

    # 1.3 Refrigerants (HVAC) — annual top-up
    if employees >= 200:
        r410a_kg = employees * 0.015 * random.uniform(0.6, 1.4)
        activities.append({
            "scope": 1, "category_code": "1.3",
            "activity_key": "refrigerant_r410a",
            "description": f"HVAC refrigerant R-410A annual top-up",
            "quantity": round(r410a_kg, 2), "unit": "kg",
            "activity_date": date(year, 6, 15),
        })

    # ===== SCOPE 2 =====

    # 2 Purchased electricity — monthly
    # Office electricity: ~4,500 kWh per employee per year → ~375 kWh/month
    kwh_per_employee_month = 375
    if country in ("IN", "PH"):
        kwh_per_employee_month = 280  # lower AC but older buildings
    elif country in ("SG",):
        kwh_per_employee_month = 420  # high AC

    elec_key = ELECTRICITY_KEYS.get(country, "electricity_global")
    for month in range(1, 13):
        # Seasonal variation: higher in summer/winter
        seasonal = 1.0
        if month in (7, 8):
            seasonal = 1.25  # summer AC
        elif month in (1, 2, 12):
            seasonal = 1.15  # winter heating (not tropical)
            if country in ("SG", "PH", "IN"):
                seasonal = 1.0  # no winter heating

        qty = employees * kwh_per_employee_month * seasonal * random.uniform(0.92, 1.08)
        activities.append({
            "scope": 2, "category_code": "2",
            "activity_key": elec_key,
            "description": f"Purchased electricity — {date(year, month, 1).strftime('%B')}",
            "quantity": round(qty, 0), "unit": "kWh",
            "activity_date": date(year, month, 15),
        })

    # ===== SCOPE 3 =====

    # 3.1 Purchased goods & services (quarterly spend-based)
    quarterly_it_spend = employees * 200  # ~$200/employee/quarter for IT
    quarterly_office_spend = employees * 80
    quarterly_food_spend = employees * 120
    for q, month in [(1, 3), (2, 6), (3, 9), (4, 12)]:
        activities.append({
            "scope": 3, "category_code": "3.1",
            "activity_key": "spend_it_equipment",
            "description": f"IT equipment & software licenses — Q{q}",
            "quantity": round(quarterly_it_spend * random.uniform(0.8, 1.3), 0),
            "unit": "USD",
            "activity_date": date(year, month, 28),
        })
        activities.append({
            "scope": 3, "category_code": "3.1",
            "activity_key": "spend_office_supplies",
            "description": f"Office supplies & stationery — Q{q}",
            "quantity": round(quarterly_office_spend * random.uniform(0.7, 1.2), 0),
            "unit": "USD",
            "activity_date": date(year, month, 28),
        })
        if employees >= 200:
            activities.append({
                "scope": 3, "category_code": "3.1",
                "activity_key": "spend_food_beverages",
                "description": f"Cafeteria & catering — Q{q}",
                "quantity": round(quarterly_food_spend * random.uniform(0.8, 1.1), 0),
                "unit": "USD",
                "activity_date": date(year, month, 28),
            })

    # 3.5 Waste — monthly (office waste)
    monthly_waste_kg = employees * 1.5  # ~1.5 kg/employee/month
    for month in range(1, 13):
        qty = monthly_waste_kg * random.uniform(0.7, 1.3)
        # 60% recycled, 40% landfill
        activities.append({
            "scope": 3, "category_code": "3.5",
            "activity_key": "waste_recycled_mixed",
            "description": f"Recycled office waste — {date(year, month, 1).strftime('%B')}",
            "quantity": round(qty * 0.6, 1), "unit": "kg",
            "activity_date": date(year, month, 28),
        })
        activities.append({
            "scope": 3, "category_code": "3.5",
            "activity_key": "waste_landfill_mixed",
            "description": f"General waste to landfill — {date(year, month, 1).strftime('%B')}",
            "quantity": round(qty * 0.4, 1), "unit": "kg",
            "activity_date": date(year, month, 28),
        })

    # 3.6 Business travel — flights (monthly)
    # Software company: ~2-4 flights per employee per year for HQ, less for others
    flights_per_employee = 3.0 if country in ("IL", "US") else 2.0
    if employees < 200:
        flights_per_employee = 1.5

    monthly_short_haul_pkm = employees * flights_per_employee / 12 * 800  # avg 800 km short haul
    monthly_long_haul_pkm = employees * flights_per_employee / 12 * 4000  # avg 4000 km long haul

    for month in range(1, 13):
        # Less travel in summer/holidays
        travel_factor = 0.6 if month in (7, 8, 12) else 1.15

        if monthly_short_haul_pkm > 100:
            activities.append({
                "scope": 3, "category_code": "3.6",
                "activity_key": "flight_short_economy",
                "description": f"Short-haul business flights — {date(year, month, 1).strftime('%B')}",
                "quantity": round(monthly_short_haul_pkm * 0.4 * travel_factor * random.uniform(0.8, 1.2), 0),
                "unit": "km",
                "activity_date": date(year, month, 20),
            })

        if monthly_long_haul_pkm > 100:
            activities.append({
                "scope": 3, "category_code": "3.6",
                "activity_key": "flight_long_economy",
                "description": f"Long-haul business flights (economy) — {date(year, month, 1).strftime('%B')}",
                "quantity": round(monthly_long_haul_pkm * 0.5 * travel_factor * random.uniform(0.8, 1.2), 0),
                "unit": "km",
                "activity_date": date(year, month, 20),
            })
            # Some business class
            activities.append({
                "scope": 3, "category_code": "3.6",
                "activity_key": "flight_long_business",
                "description": f"Long-haul business flights (business class) — {date(year, month, 1).strftime('%B')}",
                "quantity": round(monthly_long_haul_pkm * 0.1 * travel_factor * random.uniform(0.7, 1.3), 0),
                "unit": "km",
                "activity_date": date(year, month, 20),
            })

    # 3.6 Hotel nights (proportional to travel)
    monthly_hotel_nights = employees * flights_per_employee / 12 * 2.5  # avg 2.5 nights per trip
    for month in range(1, 13):
        travel_factor = 0.6 if month in (7, 8, 12) else 1.15
        if monthly_hotel_nights > 5:
            activities.append({
                "scope": 3, "category_code": "3.6",
                "activity_key": "hotel_night",
                "description": f"Hotel stays — {date(year, month, 1).strftime('%B')}",
                "quantity": round(monthly_hotel_nights * travel_factor * random.uniform(0.8, 1.2), 0),
                "unit": "nights",
                "activity_date": date(year, month, 20),
            })

    # 3.7 Employee commuting — monthly
    # Car commuters: 70% in US/IL, 30% in EU/Asia
    car_pct = 0.70 if country in ("IL", "US") else 0.30
    bus_pct = 0.15 if country in ("IN", "PH") else 0.10
    rail_pct = 1.0 - car_pct - bus_pct

    avg_commute_km = 25  # one-way daily
    working_days = 21

    for month in range(1, 13):
        vacation_factor = 0.7 if month in (8, 12) else 1.0

        # Car commuters
        car_km = employees * car_pct * avg_commute_km * 2 * working_days * vacation_factor
        if car_km > 0:
            activities.append({
                "scope": 3, "category_code": "3.7",
                "activity_key": "commute_car_petrol",
                "description": f"Employee commuting by car — {date(year, month, 1).strftime('%B')}",
                "quantity": round(car_km * random.uniform(0.9, 1.1), 0), "unit": "km",
                "activity_date": date(year, month, 28),
            })

        # Public transport
        rail_km = employees * rail_pct * avg_commute_km * 2 * working_days * vacation_factor
        if rail_km > 1000:
            activities.append({
                "scope": 3, "category_code": "3.7",
                "activity_key": "commute_rail",
                "description": f"Employee commuting by train — {date(year, month, 1).strftime('%B')}",
                "quantity": round(rail_km * random.uniform(0.9, 1.1), 0), "unit": "km",
                "activity_date": date(year, month, 28),
            })

        bus_km = employees * bus_pct * avg_commute_km * 2 * working_days * vacation_factor
        if bus_km > 1000:
            activities.append({
                "scope": 3, "category_code": "3.7",
                "activity_key": "commute_bus",
                "description": f"Employee commuting by bus — {date(year, month, 1).strftime('%B')}",
                "quantity": round(bus_km * random.uniform(0.9, 1.1), 0), "unit": "km",
                "activity_date": date(year, month, 28),
            })

    return activities


async def seed_nice_demo(session: AsyncSession, force: bool = False):
    """Seed NICE Ltd demo organization with sites and activities."""

    # Check if NICE org already exists
    result = await session.execute(
        select(Organization).where(Organization.name == "NICE Ltd")
    )
    existing_org = result.scalar_one_or_none()

    if existing_org and not force:
        typer.echo("NICE Ltd demo data already exists. Use --force to re-create.")
        return

    # If force, delete existing data
    if existing_org:
        typer.echo("Removing existing NICE demo data...")
        # Delete emissions, activities, sites, periods for this org
        from sqlmodel import delete
        from app.models.emission import ImportBatch

        # Get activity IDs
        act_result = await session.execute(
            select(Activity.id).where(Activity.organization_id == existing_org.id)
        )
        act_ids = [a for a in act_result.scalars().all()]
        if act_ids:
            await session.execute(delete(Emission).where(Emission.activity_id.in_(act_ids)))
            await session.execute(delete(Activity).where(Activity.organization_id == existing_org.id))
        await session.execute(delete(ImportBatch).where(ImportBatch.organization_id == existing_org.id))
        await session.execute(delete(Site).where(Site.organization_id == existing_org.id))
        await session.execute(delete(ReportingPeriod).where(ReportingPeriod.organization_id == existing_org.id))
        await session.execute(delete(User).where(User.organization_id == existing_org.id))
        await session.delete(existing_org)
        await session.commit()

    # Create organization
    typer.echo("Creating NICE Ltd organization...")
    org = Organization(
        name="NICE Ltd",
        country_code="IL",
        industry_code="software",
        base_year=2024,
        default_region="IL",
        subscription_plan="enterprise",
    )
    session.add(org)
    await session.flush()

    # Create admin user
    admin = User(
        email="demo@nice.com",
        full_name="Demo Admin",
        role=UserRole.ADMIN,
        organization_id=org.id,
        hashed_password=get_password_hash("NiceDemo2025!"),
        onboarding_completed=True,
    )
    session.add(admin)
    await session.flush()

    # Create sites
    typer.echo("Creating 14 global office sites...")
    site_map = {}  # name -> Site
    for site_data in NICE_SITES:
        site = Site(
            organization_id=org.id,
            name=site_data["name"],
            country_code=site_data["country_code"],
            address=site_data["address"],
            grid_region=site_data["grid_region"],
        )
        session.add(site)
        await session.flush()
        site_map[site_data["name"]] = site

    # Create reporting period — FY 2025
    period = ReportingPeriod(
        organization_id=org.id,
        name="FY 2025",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
    )
    session.add(period)
    await session.flush()

    await session.commit()

    # Generate and insert activities per site
    pipeline = CalculationPipeline(session)
    total_activities = 0
    total_emissions = 0
    failed = 0

    for site_data in NICE_SITES:
        site = site_map[site_data["name"]]
        site_activities = _generate_monthly_activities(site_data)
        typer.echo(f"  {site_data['name']}: generating {len(site_activities)} activities...")

        for act_data in site_activities:
            try:
                calc_result = await pipeline.calculate(ActivityInput(
                    activity_key=act_data["activity_key"],
                    quantity=Decimal(str(act_data["quantity"])),
                    unit=act_data["unit"],
                    scope=act_data["scope"],
                    category_code=act_data["category_code"],
                    region=site_data.get("grid_region", "Global"),
                    year=2024,
                ))

                activity = Activity(
                    organization_id=org.id,
                    reporting_period_id=period.id,
                    site_id=site.id,
                    scope=act_data["scope"],
                    category_code=act_data["category_code"],
                    activity_key=act_data["activity_key"],
                    description=act_data["description"],
                    quantity=Decimal(str(act_data["quantity"])),
                    unit=act_data["unit"],
                    activity_date=act_data["activity_date"],
                    data_source=DataSource.IMPORT,
                    created_by=admin.id,
                    data_quality_score=3,
                )
                session.add(activity)
                await session.flush()

                emission = Emission(
                    activity_id=activity.id,
                    emission_factor_id=calc_result.emission_factor_id,
                    co2e_kg=calc_result.co2e_kg,
                    co2_kg=calc_result.co2_kg,
                    ch4_kg=calc_result.ch4_kg,
                    n2o_kg=calc_result.n2o_kg,
                    wtt_co2e_kg=calc_result.wtt_co2e_kg,
                    converted_quantity=calc_result.converted_quantity,
                    converted_unit=calc_result.converted_unit,
                    formula=calc_result.formula,
                    confidence=ConfidenceLevel(calc_result.confidence),
                    resolution_strategy=calc_result.resolution_strategy,
                    factor_year=calc_result.factor_year,
                    factor_region=calc_result.factor_region,
                    method_hierarchy=calc_result.method_hierarchy,
                    location_co2e_kg=calc_result.location_co2e_kg,
                    market_co2e_kg=calc_result.market_co2e_kg,
                )
                session.add(emission)
                total_activities += 1
                total_emissions += float(calc_result.co2e_kg)

            except Exception as e:
                failed += 1
                if failed <= 10:
                    typer.echo(f"    WARN: {act_data['activity_key']} — {e}")

        await session.commit()

    typer.echo(f"\n{'='*60}")
    typer.echo(f"NICE Ltd Demo Seeding Complete")
    typer.echo(f"{'='*60}")
    typer.echo(f"Organization: NICE Ltd")
    typer.echo(f"Login:        demo@nice.com / NiceDemo2025!")
    typer.echo(f"Sites:        {len(NICE_SITES)}")
    typer.echo(f"Period:       FY 2025")
    typer.echo(f"Activities:   {total_activities}")
    typer.echo(f"Failed:       {failed}")
    typer.echo(f"Total CO2e:   {total_emissions/1000:,.1f} tonnes")
    typer.echo(f"{'='*60}")


cli = typer.Typer()


@cli.command()
def main(
    force: bool = typer.Option(False, "--force", help="Re-create NICE demo data"),
):
    """Seed NICE Ltd demo data with 14 sites and realistic emission activities."""

    async def run():
        engine = create_async_engine(settings.async_database_url)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            await seed_nice_demo(session, force=force)

        await engine.dispose()

    asyncio.run(run())


if __name__ == "__main__":
    cli()
