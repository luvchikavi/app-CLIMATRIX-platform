"""Seed 3 demo companies with realistic Scope 1/2/3 footprints so the app is
immediately demo-able (login -> populated dashboards).

Companies (per Ana's master design):
  - Aeris Labs      — B2B SaaS startup (Scope-2 dominant + travel/services Scope 3)
  - Galil Steel Ltd.— iron & steel factory (heavy Scope 1+2, CBAM-relevant, multi-site)
  - Meridian Advisory — management consultancy (~80% Scope 3 travel/services)

Each activity is run through the real CalculationPipeline so emissions are genuine.
Any activity whose activity_key/unit doesn't resolve is skipped (logged) — the seed
never fails as a whole. Re-running skips companies that already exist.

Run:  PYTHONPATH=. python -m app.cli.seed_demo_companies
"""
import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import select

from app.config import settings
from app.models.core import (
    Organization,
    User,
    UserRole,
    Site,
    ReportingPeriod,
    PeriodStatus,
    SubscriptionPlan,
    SubscriptionStatus,
)
from app.models.emission import Activity, Emission, DataSource, ConfidenceLevel
from app.api.auth import get_password_hash
from app.services.calculation import CalculationPipeline, ActivityInput
from app.services.calculation.pipeline import CalculationError
from app.services.calculation.resolver import FactorNotFoundError
from app.services.calculation.normalizer import UnitConversionError

PASSWORD = "DemoClimatrix2026"

# (activity_key, quantity, unit, scope, category_code, description)
COMPANIES = [
    {
        "name": "Aeris Labs",
        "email": "aeris@climetrix.io",
        "admin": "Dana Cohen",
        "country": "IL",
        "industry_code": "J62",
        "base_year": 2025,
        "period": ("FY 2025", date(2025, 1, 1), date(2025, 12, 31)),
        "sites": [("Tel Aviv HQ", "IL", "IL")],
        "activities": [
            ("electricity_il", 45600, "kWh", 2, "2", "Office electricity"),
            ("electricity_il", 31200, "kWh", 2, "2", "Cloud/colo allocation"),
            ("car_petrol_km", 12000, "km", 1, "1.2", "Company car"),
            ("flight_short_economy", 60000, "km", 3, "3.6", "Business travel — short-haul"),
            ("flight_long_economy", 18000, "km", 3, "3.6", "Business travel — long-haul"),
            ("hotel_night", 96, "nights", 3, "3.6", "Business travel — hotels"),
            ("commute_car_petrol", 8400, "km", 3, "3.7", "Employee commuting — car"),
            ("commute_bus", 10800, "km", 3, "3.7", "Employee commuting — bus"),
            ("electronics_purchased_kg", 400, "kg", 3, "3.1", "Purchased laptops/equipment"),
            ("paper_virgin_purchased_kg", 200, "kg", 3, "3.1", "Purchased paper"),
            ("waste_cardboard_recycled", 1440, "kg", 3, "3.5", "Office waste — recycled"),
        ],
    },
    {
        "name": "Galil Steel Ltd.",
        "email": "galil@climetrix.io",
        "admin": "Yossi Levi",
        "country": "IL",
        "industry_code": "C24.1",
        "base_year": 2024,
        "period": ("FY 2024", date(2024, 1, 1), date(2024, 12, 31)),
        "sites": [
            ("Karmiel Mill", "IL", "IL"),
            ("Ashdod Finishing & Port", "IL", "IL"),
        ],
        "activities": [
            ("natural_gas_kwh", 30000000, "kWh", 1, "1.1", "Reheat/annealing furnaces"),
            ("diesel_liters", 720000, "liters", 1, "1.1", "Generators"),
            ("coal_kg", 3000000, "kg", 1, "1.1", "Coal — Karmiel"),
            ("car_diesel_km", 200000, "km", 1, "1.2", "Yard fleet"),
            ("electricity_il", 28800000, "kWh", 2, "2", "Arc/rolling grid electricity"),
            ("steel_purchased_kg", 10800000, "kg", 3, "3.1", "Scrap/semi-finished inputs"),
            ("aluminum_primary_purchased_kg", 360000, "kg", 3, "3.1", "Purchased aluminium"),
            ("road_freight_hgv", 2000000, "tonne-km", 3, "3.4", "Upstream road freight"),
            ("rail_freight", 800000, "tonne-km", 3, "3.4", "Upstream rail freight"),
            ("flight_long_business", 50000, "km", 3, "3.6", "Business travel"),
            ("waste_steel_cans_recycled", 100000, "kg", 3, "3.5", "Operational waste — recycled"),
        ],
    },
    {
        "name": "Meridian Advisory",
        "email": "meridian@climetrix.io",
        "admin": "Tamar Barak",
        "country": "IL",
        "industry_code": "M70.22",
        "base_year": 2025,
        "period": ("FY 2025", date(2025, 1, 1), date(2025, 12, 31)),
        "sites": [("Tel Aviv Office", "IL", "IL"), ("London Desk", "GB", "UK")],
        "activities": [
            ("electricity_il", 114000, "kWh", 2, "2", "Tel Aviv office electricity"),
            ("electricity_uk", 38400, "kWh", 2, "2", "London desk electricity"),
            ("flight_long_business", 400000, "km", 3, "3.6", "Business travel — long-haul"),
            ("flight_short_business", 120000, "km", 3, "3.6", "Business travel — short-haul"),
            ("hotel_night", 2160, "nights", 3, "3.6", "Business travel — hotels"),
            ("rail_international_km", 96000, "km", 3, "3.6", "Business travel — rail"),
            ("commute_car_petrol", 150000, "km", 3, "3.7", "Employee commuting — car"),
            ("commute_rail", 60000, "km", 3, "3.7", "Employee commuting — rail"),
            ("electronics_purchased_kg", 600, "kg", 3, "3.1", "Purchased equipment"),
            ("paper_virgin_purchased_kg", 800, "kg", 3, "3.1", "Purchased paper"),
            ("waste_cardboard_recycled", 1200, "kg", 3, "3.5", "Office waste — recycled"),
        ],
    },
]


async def seed_company(session: AsyncSession, spec: dict) -> None:
    existing = (
        await session.execute(select(User).where(User.email == spec["email"]))
    ).scalar_one_or_none()
    if existing:
        print(f"  ~ {spec['name']}: already seeded ({spec['email']}) — skipping")
        return

    now = datetime.utcnow()
    org = Organization(
        id=uuid4(),
        name=spec["name"],
        country_code=spec["country"],
        industry_code=spec["industry_code"],
        base_year=spec["base_year"],
        default_region=spec["country"],
        setup_complete=True,
        setup_completed_at=now,
        subscription_plan=SubscriptionPlan.PROFESSIONAL.value,
        subscription_status=SubscriptionStatus.TRIALING.value,
        trial_ends_at=now + timedelta(days=14),
    )
    session.add(org)
    await session.flush()

    user = User(
        id=uuid4(),
        organization_id=org.id,
        email=spec["email"],
        full_name=spec["admin"],
        hashed_password=get_password_hash(PASSWORD),
        role=UserRole.ADMIN,
        is_active=True,
    )
    session.add(user)

    site_ids = []
    for sname, scountry, sgrid in spec["sites"]:
        site = Site(
            id=uuid4(),
            organization_id=org.id,
            name=sname,
            country_code=scountry,
            grid_region=sgrid,
            is_active=True,
        )
        session.add(site)
        site_ids.append(site.id)

    pname, pstart, pend = spec["period"]
    period = ReportingPeriod(
        id=uuid4(),
        organization_id=org.id,
        name=pname,
        start_date=pstart,
        end_date=pend,
        status=PeriodStatus.DRAFT,
    )
    session.add(period)
    await session.flush()

    pipeline = CalculationPipeline(session)
    ok, skipped = 0, 0
    for i, (key, qty, unit, scope, cat, desc) in enumerate(spec["activities"]):
        site_id = site_ids[i % len(site_ids)] if site_ids else None
        try:
            calc = await pipeline.calculate(
                ActivityInput(
                    activity_key=key,
                    quantity=Decimal(str(qty)),
                    unit=unit,
                    scope=scope,
                    category_code=cat,
                    region=spec["country"],
                    year=spec["base_year"],
                )
            )
        except (FactorNotFoundError, UnitConversionError, CalculationError) as e:
            skipped += 1
            print(f"    - skip {key} ({unit}): {type(e).__name__}")
            continue

        activity = Activity(
            organization_id=org.id,
            reporting_period_id=period.id,
            scope=scope,
            category_code=cat,
            activity_key=key,
            description=desc,
            quantity=Decimal(str(qty)),
            unit=unit,
            activity_date=pstart,
            site_id=site_id,
            created_by=user.id,
            data_source=DataSource.MANUAL,
            data_quality_score=3,
        )
        session.add(activity)
        await session.flush()

        session.add(
            Emission(
                activity_id=activity.id,
                emission_factor_id=calc.emission_factor_id,
                co2e_kg=calc.co2e_kg,
                co2_kg=calc.co2_kg,
                ch4_kg=calc.ch4_kg,
                n2o_kg=calc.n2o_kg,
                wtt_co2e_kg=calc.wtt_co2e_kg,
                converted_quantity=calc.converted_quantity,
                converted_unit=calc.converted_unit,
                formula=calc.formula,
                confidence=ConfidenceLevel(calc.confidence),
                resolution_strategy=calc.resolution_strategy,
                factor_year=calc.factor_year,
                factor_region=calc.factor_region,
                method_hierarchy=calc.method_hierarchy,
                location_co2e_kg=calc.location_co2e_kg,
                market_co2e_kg=calc.market_co2e_kg,
            )
        )
        ok += 1

    await session.commit()
    print(f"  + {spec['name']}: {ok} activities seeded, {skipped} skipped  ({spec['email']} / {PASSWORD})")


async def run():
    engine = create_async_engine(settings.async_database_url)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    print("Seeding demo companies...")
    async with Session() as session:
        for spec in COMPANIES:
            await seed_company(session, spec)
    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(run())
