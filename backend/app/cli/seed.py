"""
Database seeding CLI.

Usage:
    python -m app.cli.seed                  # Seed if empty
    python -m app.cli.seed --force          # Force re-seed
    python -m app.cli.seed --check-only     # Check if seeding needed
"""
import asyncio
from uuid import uuid4

import typer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import select

from app.config import settings
from app.models.core import Organization, User, UserRole
from app.models.emission import (
    EmissionFactor, UnitConversion, FuelPrice,
    Airport, TransportDistanceMatrix, CurrencyConversion,
    GridEmissionFactor, HotelEmissionFactor, RefrigerantGWP, WasteDisposalFactor,
)
from app.data import EMISSION_FACTORS, UNIT_CONVERSIONS, FUEL_PRICES
from app.data.airports import AIRPORTS
from app.data.transport_distances import TRANSPORT_DISTANCES
from app.data.reference_data import (
    CURRENCY_RATES, GRID_EMISSION_FACTORS, HOTEL_EMISSION_FACTORS,
    REFRIGERANT_GWP, WASTE_DISPOSAL_FACTORS,
)
from app.api.auth import get_password_hash

app = typer.Typer()


async def ensure_super_admin(session: AsyncSession) -> bool:
    """
    Ensure the super admin user exists with the correct credentials.
    This user is non-changeable and always has these credentials.

    Returns True if super admin was created, False if already exists.
    """
    SUPER_ADMIN_EMAIL = "avi@drishti.com"
    SUPER_ADMIN_PASSWORD = "Luvchik!2030"
    SUPER_ADMIN_NAME = "Avi Luvchik"

    # Check if super admin already exists
    result = await session.execute(
        select(User).where(User.email == SUPER_ADMIN_EMAIL)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        # Update password to ensure it's correct (in case it was changed)
        existing_user.hashed_password = get_password_hash(SUPER_ADMIN_PASSWORD)
        existing_user.role = UserRole.SUPER_ADMIN
        existing_user.full_name = SUPER_ADMIN_NAME
        existing_user.is_active = True
        await session.commit()
        return False

    # Need to find or create an organization for the super admin
    result = await session.execute(select(Organization).limit(1))
    org = result.scalar_one_or_none()

    if not org:
        # Create a default organization
        org = Organization(
            id=uuid4(),
            name="Drishti",
            country_code="IL",
            industry_code="541611",
            base_year=2024,
            default_region="IL",
        )
        session.add(org)
        await session.flush()

    # Create super admin user
    super_admin = User(
        id=uuid4(),
        organization_id=org.id,
        email=SUPER_ADMIN_EMAIL,
        full_name=SUPER_ADMIN_NAME,
        hashed_password=get_password_hash(SUPER_ADMIN_PASSWORD),
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )
    session.add(super_admin)
    await session.commit()
    return True


async def ensure_team_users(session: AsyncSession) -> int:
    """
    Ensure team users exist with their credentials.
    Creates users if they don't exist. Does not update existing users.

    Returns count of users created.
    """
    # Team users to ensure exist
    TEAM_USERS = [
        {"email": "SivanLa@bdo.co.il", "full_name": "Sivan La", "password": "Climatrix2026!", "role": UserRole.EDITOR},
        {"email": "LihieI@bdo.co.il", "full_name": "Lihi I", "password": "Climatrix2026!", "role": UserRole.EDITOR},
    ]

    # Get organization (should exist from super admin setup)
    result = await session.execute(select(Organization).limit(1))
    org = result.scalar_one_or_none()

    if not org:
        return 0

    created_count = 0
    for user_data in TEAM_USERS:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == user_data["email"])
        )
        if result.scalar_one_or_none():
            continue

        # Create user
        new_user = User(
            id=uuid4(),
            organization_id=org.id,
            email=user_data["email"],
            full_name=user_data["full_name"],
            hashed_password=get_password_hash(user_data["password"]),
            role=user_data["role"],
            is_active=True,
        )
        session.add(new_user)
        created_count += 1

    if created_count > 0:
        await session.commit()

    return created_count


async def seed_database(session: AsyncSession, force: bool = False) -> dict:
    """Seed the database with reference data."""
    stats = {"emission_factors": 0, "unit_conversions": 0, "fuel_prices": 0, "organizations": 0, "users": 0}

    # Check if already seeded
    result = await session.execute(select(EmissionFactor).limit(1))
    existing = result.scalar_one_or_none()

    if existing and not force:
        typer.echo("Database already seeded. Use --force to re-seed.")
        # Still ensure super admin exists
        created = await ensure_super_admin(session)
        if created:
            typer.echo("Super admin user created.")
        # Ensure team users exist
        team_created = await ensure_team_users(session)
        if team_created > 0:
            typer.echo(f"Created {team_created} team user(s).")
        return stats

    # Clear existing data if force
    if force:
        typer.echo("Clearing existing data...")
        await session.execute(select(EmissionFactor).execution_options(synchronize_session=False))
        # Note: In production, use proper DELETE statements

    # Seed emission factors
    typer.echo("Seeding emission factors...")
    for ef_data in EMISSION_FACTORS:
        ef = EmissionFactor(**ef_data)
        session.add(ef)
        stats["emission_factors"] += 1

    # Seed unit conversions
    typer.echo("Seeding unit conversions...")
    for uc_data in UNIT_CONVERSIONS:
        uc = UnitConversion(**uc_data)
        session.add(uc)
        stats["unit_conversions"] += 1

    # Seed fuel prices
    typer.echo("Seeding fuel prices...")
    for fp_data in FUEL_PRICES:
        fp = FuelPrice(**fp_data)
        session.add(fp)
        stats["fuel_prices"] += 1

    # Create default organization (Drishti)
    typer.echo("Creating default organization...")
    org = Organization(
        id=uuid4(),
        name="Drishti",
        country_code="IL",
        industry_code="541611",  # Management Consulting
        base_year=2024,
        default_region="IL",
    )
    session.add(org)
    stats["organizations"] += 1

    # Create super admin user
    typer.echo("Creating super admin user...")
    super_admin = User(
        id=uuid4(),
        organization_id=org.id,
        email="avi@drishti.com",
        full_name="Avi Luvchik",
        hashed_password=get_password_hash("Luvchik!2030"),
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )
    session.add(super_admin)
    stats["users"] += 1

    await session.commit()

    return stats


@app.command()
def seed(
    check_only: bool = typer.Option(False, "--check-only", help="Only check if seeding needed"),
    force: bool = typer.Option(False, "--force", help="Force re-seed even if data exists"),
):
    """Seed emission factors and reference data."""

    async def run():
        engine = create_async_engine(settings.database_url)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            if check_only:
                result = await session.execute(select(EmissionFactor).limit(1))
                existing = result.scalar_one_or_none()
                if existing:
                    typer.echo("Database is already seeded.")
                    raise typer.Exit(code=0)
                else:
                    typer.echo("Database needs seeding.")
                    raise typer.Exit(code=1)

            stats = await seed_database(session, force=force)

            typer.echo("\n--- Seeding Complete ---")
            typer.echo(f"Emission Factors: {stats['emission_factors']}")
            typer.echo(f"Unit Conversions: {stats['unit_conversions']}")
            typer.echo(f"Fuel Prices:      {stats['fuel_prices']}")
            typer.echo(f"Organizations:    {stats['organizations']}")
            typer.echo(f"Users:            {stats['users']}")
            typer.echo("\nSuper Admin credentials:")
            typer.echo("  Email:    avi@drishti.com")
            typer.echo("  Password: Luvchik!2030")

        await engine.dispose()

    asyncio.run(run())


@app.command()
def create_user(
    email: str = typer.Argument(..., help="User email"),
    password: str = typer.Argument(..., help="User password"),
    name: str = typer.Option("", help="Full name"),
    role: str = typer.Option("editor", help="Role: viewer, editor, admin"),
    org_id: str = typer.Option(None, help="Organization ID (uses first org if not specified)"),
):
    """Create a new user."""

    async def run():
        engine = create_async_engine(settings.database_url)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            # Get organization
            if org_id:
                from uuid import UUID
                result = await session.execute(select(Organization).where(Organization.id == UUID(org_id)))
            else:
                result = await session.execute(select(Organization).limit(1))

            org = result.scalar_one_or_none()
            if not org:
                typer.echo("No organization found. Run 'seed' first.")
                raise typer.Exit(code=1)

            # Create user
            user = User(
                organization_id=org.id,
                email=email,
                full_name=name or email.split("@")[0],
                hashed_password=get_password_hash(password),
                role=UserRole(role),
            )
            session.add(user)
            await session.commit()

            typer.echo(f"Created user: {email} (role: {role})")

        await engine.dispose()

    asyncio.run(run())


@app.command()
def seed_fuel_prices(
    force: bool = typer.Option(False, "--force", help="Force re-seed even if data exists"),
):
    """Seed fuel prices only (for existing databases)."""

    async def run():
        engine = create_async_engine(settings.database_url)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            # Check if fuel prices already exist
            result = await session.execute(select(FuelPrice).limit(1))
            existing = result.scalar_one_or_none()

            if existing and not force:
                typer.echo("Fuel prices already seeded. Use --force to re-seed.")
                raise typer.Exit(code=0)

            # Clear existing fuel prices if force
            if force and existing:
                typer.echo("Clearing existing fuel prices...")
                from sqlalchemy import delete
                await session.execute(delete(FuelPrice))

            # Seed fuel prices
            typer.echo("Seeding fuel prices...")
            count = 0
            for fp_data in FUEL_PRICES:
                fp = FuelPrice(**fp_data)
                session.add(fp)
                count += 1

            await session.commit()
            typer.echo(f"Seeded {count} fuel prices.")

        await engine.dispose()

    asyncio.run(run())


@app.command()
def ensure_admin():
    """
    Ensure the super admin user exists with correct credentials.

    This creates or updates the super admin user:
    - Email: avi@drishti.com
    - Password: Luvchik!2030
    - Role: super_admin
    """

    async def run():
        engine = create_async_engine(settings.database_url)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            created = await ensure_super_admin(session)
            if created:
                typer.echo("Super admin user created.")
            else:
                typer.echo("Super admin user updated/verified.")

            typer.echo("\nSuper Admin credentials:")
            typer.echo("  Email:    avi@drishti.com")
            typer.echo("  Password: Luvchik!2030")

        await engine.dispose()

    asyncio.run(run())


@app.command()
def seed_scope3_reference(
    force: bool = typer.Option(False, "--force", help="Force re-seed even if data exists"),
):
    """
    Seed Scope 3 reference data tables:
    - Airports (for flight distance calculations)
    - Transport distance matrix (for default shipping distances)
    - Currency conversion rates (for spend-based calculations)
    - Grid emission factors (by country)
    - Hotel emission factors (by country)
    - Refrigerant GWP values
    - Waste disposal factors

    This is a separate command since these are new tables added for enhanced Scope 3 support.
    """
    from datetime import date
    from decimal import Decimal

    async def run():
        engine = create_async_engine(settings.database_url)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            stats = {
                "airports": 0,
                "transport_routes": 0,
                "currencies": 0,
                "grid_factors": 0,
                "hotel_factors": 0,
                "refrigerants": 0,
                "waste_factors": 0,
            }

            # Check if already seeded (check airports as indicator)
            result = await session.execute(select(Airport).limit(1))
            existing = result.scalar_one_or_none()

            if existing and not force:
                typer.echo("Scope 3 reference data already seeded. Use --force to re-seed.")
                raise typer.Exit(code=0)

            # Clear existing data if force
            if force:
                typer.echo("Clearing existing Scope 3 reference data...")
                from sqlalchemy import delete
                await session.execute(delete(WasteDisposalFactor))
                await session.execute(delete(RefrigerantGWP))
                await session.execute(delete(HotelEmissionFactor))
                await session.execute(delete(GridEmissionFactor))
                await session.execute(delete(CurrencyConversion))
                await session.execute(delete(TransportDistanceMatrix))
                await session.execute(delete(Airport))
                await session.commit()  # Commit deletes before inserting

            # 1. Seed Airports
            # AIRPORTS format: {IATA_CODE: (name, city, country_code, latitude, longitude)}
            typer.echo("Seeding airports...")
            for iata_code, airport_data in AIRPORTS.items():
                name, city, country_code, latitude, longitude = airport_data
                airport = Airport(
                    id=uuid4(),
                    iata_code=iata_code,
                    name=name,
                    city=city,
                    country_code=country_code,
                    country_name=country_code,  # Use country code as name for now
                    latitude=Decimal(str(latitude)),
                    longitude=Decimal(str(longitude)),
                    is_active=True,
                )
                session.add(airport)
                stats["airports"] += 1

            # 2. Seed Transport Distance Matrix
            typer.echo("Seeding transport distance matrix...")
            from datetime import datetime
            for route_key, route_data in TRANSPORT_DISTANCES.items():
                origin, destination = route_key
                transport = TransportDistanceMatrix(
                    id=uuid4(),
                    origin_country=origin,
                    destination_country=destination,
                    origin_land_km=route_data.get("origin_land_km", 500),
                    sea_distance_km=route_data["sea_distance_km"],
                    destination_land_km=route_data.get("destination_land_km", 100),
                    total_distance_km=route_data["total_distance_km"],
                    transport_mode=route_data.get("transport_mode", "sea_container"),
                    air_distance_km=route_data.get("air_distance_km"),
                    source=route_data.get("source", "Estimated"),
                    is_active=True,
                    updated_at=datetime.utcnow(),
                )
                session.add(transport)
                stats["transport_routes"] += 1

            # 3. Seed Currency Conversion Rates
            typer.echo("Seeding currency conversion rates...")
            for currency, rate in CURRENCY_RATES.items():
                if currency == "USD":
                    continue  # Skip USD to USD
                currency_conv = CurrencyConversion(
                    id=uuid4(),
                    from_currency=currency,
                    to_currency="USD",
                    rate=rate,
                    valid_from=date(2024, 1, 1),
                    source="OECD annual average 2024",
                    rate_type="annual_average",
                    is_active=True,
                )
                session.add(currency_conv)
                stats["currencies"] += 1

            # 4. Seed Grid Emission Factors
            typer.echo("Seeding grid emission factors...")
            for country_code, data in GRID_EMISSION_FACTORS.items():
                grid_factor = GridEmissionFactor(
                    id=uuid4(),
                    country_code=country_code,
                    country_name=country_code,  # Will be updated with proper names
                    location_factor=data["location_factor"],
                    market_factor=data.get("market_factor"),
                    td_loss_factor=data.get("td_loss_factor"),
                    td_loss_percentage=data.get("td_loss_percentage"),
                    source=data.get("source", "IEA 2024"),
                    year=2024,
                    is_active=True,
                )
                session.add(grid_factor)
                stats["grid_factors"] += 1

            # 5. Seed Hotel Emission Factors
            typer.echo("Seeding hotel emission factors...")
            for country_code, data in HOTEL_EMISSION_FACTORS.items():
                hotel_factor = HotelEmissionFactor(
                    id=uuid4(),
                    country_code=country_code,
                    country_name=country_code,
                    co2e_per_night=data["co2e_per_night"],
                    source=data.get("source", "DEFRA 2024"),
                    year=2024,
                    is_active=True,
                )
                session.add(hotel_factor)
                stats["hotel_factors"] += 1

            # 6. Seed Refrigerant GWP Values
            typer.echo("Seeding refrigerant GWP values...")
            for name, data in REFRIGERANT_GWP.items():
                refrigerant = RefrigerantGWP(
                    id=uuid4(),
                    name=name,
                    gwp_ar6=data["gwp_ar6"],
                    refrigerant_type=data["type"],
                    source="IPCC_AR6_2021",
                    is_active=True,
                )
                session.add(refrigerant)
                stats["refrigerants"] += 1

            # 7. Seed Waste Disposal Factors
            # WASTE_DISPOSAL_FACTORS format: {(waste_type, method): {co2e_per_kg, source}}
            typer.echo("Seeding waste disposal factors...")
            for (waste_type, method), factor_data in WASTE_DISPOSAL_FACTORS.items():
                waste_factor = WasteDisposalFactor(
                    id=uuid4(),
                    waste_type=waste_type,
                    disposal_method=method,
                    co2e_per_kg=factor_data["co2e_per_kg"],
                    source=factor_data.get("source", "DEFRA 2024"),
                    year=2024,
                    region="Global",
                    is_active=True,
                )
                session.add(waste_factor)
                stats["waste_factors"] += 1

            await session.commit()

            typer.echo("\n--- Scope 3 Reference Data Seeding Complete ---")
            typer.echo(f"Airports:          {stats['airports']}")
            typer.echo(f"Transport Routes:  {stats['transport_routes']}")
            typer.echo(f"Currency Rates:    {stats['currencies']}")
            typer.echo(f"Grid Factors:      {stats['grid_factors']}")
            typer.echo(f"Hotel Factors:     {stats['hotel_factors']}")
            typer.echo(f"Refrigerants:      {stats['refrigerants']}")
            typer.echo(f"Waste Factors:     {stats['waste_factors']}")

        await engine.dispose()

    asyncio.run(run())


if __name__ == "__main__":
    app()
