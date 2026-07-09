"""
Database seeding CLI.

Usage:
    python -m app.cli db seed                       # Seed reference data
    python -m app.cli db seed --force               # Force re-seed
    python -m app.cli db create-superuser --email X --password Y
    python -m app.cli db create-user EMAIL PASSWORD
"""

import asyncio
from uuid import uuid4

import typer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import select

from app.config import settings
from app.models.core import Organization, User, UserRole
from app.models.emission import (
    EmissionFactor,
    UnitConversion,
    FuelPrice,
    Airport,
    TransportDistanceMatrix,
    CurrencyConversion,
    GridEmissionFactor,
    HotelEmissionFactor,
    RefrigerantGWP,
    WasteDisposalFactor,
)
from app.data import EMISSION_FACTORS, UNIT_CONVERSIONS, FUEL_PRICES
from app.data.airports import AIRPORTS
from app.data.transport_distances import TRANSPORT_DISTANCES
from app.data.reference_data import (
    CURRENCY_RATES,
    GRID_EMISSION_FACTORS,
    HOTEL_EMISSION_FACTORS,
    REFRIGERANT_GWP,
    WASTE_DISPOSAL_FACTORS,
)
from app.api.auth import get_password_hash

app = typer.Typer()


async def seed_database(session: AsyncSession, force: bool = False) -> dict:
    """Seed the database with reference data (no user/org creation)."""
    stats = {"emission_factors": 0, "unit_conversions": 0, "fuel_prices": 0}

    # Check if already seeded
    result = await session.execute(select(EmissionFactor).limit(1))
    existing = result.scalar_one_or_none()

    if existing and not force:
        typer.echo("Database already seeded. Use --force to re-seed.")
        return stats

    # Clear existing data if force
    if force:
        typer.echo("Clearing existing data...")
        from sqlalchemy import delete

        await session.execute(delete(EmissionFactor))
        await session.execute(delete(UnitConversion))
        await session.execute(delete(FuelPrice))
        await session.commit()

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

    await session.commit()

    return stats


@app.command()
def seed(
    check_only: bool = typer.Option(
        False, "--check-only", help="Only check if seeding needed"
    ),
    force: bool = typer.Option(
        False, "--force", help="Force re-seed even if data exists"
    ),
):
    """Seed emission factors and reference data."""

    async def run():
        engine = create_async_engine(settings.async_database_url)
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

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

        await engine.dispose()

    asyncio.run(run())


@app.command()
def create_superuser(
    email: str = typer.Option(
        ..., "--email", "-e", help="Super admin email", prompt=True
    ),
    password: str = typer.Option(
        ...,
        "--password",
        "-p",
        help="Super admin password",
        prompt=True,
        hide_input=True,
    ),
    name: str = typer.Option("", "--name", "-n", help="Full name"),
    org_name: str = typer.Option(
        "", "--org-name", help="Organization name (created if no org exists)"
    ),
):
    """Create or update a super admin user.

    If the user exists, their password and role are updated.
    If no organization exists, one is created with --org-name.

    Example:
        python -m app.cli db create-superuser --email admin@example.com --password secret123
    """

    async def run():
        engine = create_async_engine(settings.async_database_url)
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            # Check if user already exists
            result = await session.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()

            if existing_user:
                existing_user.hashed_password = get_password_hash(password)
                existing_user.role = UserRole.SUPER_ADMIN
                if name:
                    existing_user.full_name = name
                existing_user.is_active = True
                await session.commit()
                typer.echo(f"Updated super admin: {email}")
                await engine.dispose()
                return

            # Need an organization
            result = await session.execute(select(Organization).limit(1))
            org = result.scalar_one_or_none()

            if not org:
                organization_name = org_name or typer.prompt("Organization name")
                org = Organization(
                    id=uuid4(),
                    name=organization_name,
                    default_region="Global",
                )
                session.add(org)
                await session.flush()
                typer.echo(f"Created organization: {organization_name}")

            # Create super admin user
            super_admin = User(
                id=uuid4(),
                organization_id=org.id,
                email=email,
                full_name=name or email.split("@")[0],
                hashed_password=get_password_hash(password),
                role=UserRole.SUPER_ADMIN,
                is_active=True,
            )
            session.add(super_admin)
            await session.commit()
            typer.echo(f"Created super admin: {email}")

        await engine.dispose()

    asyncio.run(run())


@app.command()
def create_user(
    email: str = typer.Argument(..., help="User email"),
    password: str = typer.Argument(..., help="User password"),
    name: str = typer.Option("", help="Full name"),
    role: str = typer.Option("editor", help="Role: viewer, editor, admin"),
    org_id: str = typer.Option(
        None, help="Organization ID (uses first org if not specified)"
    ),
):
    """Create a new user."""

    async def run():
        engine = create_async_engine(settings.async_database_url)
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            # Check if user already exists
            result = await session.execute(select(User).where(User.email == email))
            if result.scalar_one_or_none():
                typer.echo(f"User {email} already exists.")
                raise typer.Exit(code=1)

            # Get organization
            if org_id:
                from uuid import UUID

                result = await session.execute(
                    select(Organization).where(Organization.id == UUID(org_id))
                )
            else:
                result = await session.execute(select(Organization).limit(1))

            org = result.scalar_one_or_none()
            if not org:
                typer.echo(
                    "No organization found. Run 'seed' first or create a superuser."
                )
                raise typer.Exit(code=1)

            # Create user
            user = User(
                organization_id=org.id,
                email=email,
                full_name=name or email.split("@")[0],
                hashed_password=get_password_hash(password),
                role=UserRole(role),
                is_active=True,
            )
            session.add(user)
            await session.commit()

            typer.echo(f"Created user: {email} (role: {role}, org: {org.name})")

        await engine.dispose()

    asyncio.run(run())


@app.command()
def seed_fuel_prices(
    force: bool = typer.Option(
        False, "--force", help="Force re-seed even if data exists"
    ),
):
    """Seed fuel prices only (for existing databases)."""

    async def run():
        engine = create_async_engine(settings.async_database_url)
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

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
def seed_scope3_reference(
    force: bool = typer.Option(
        False, "--force", help="Force re-seed even if data exists"
    ),
):
    """Seed Scope 3 reference data tables."""
    from datetime import date
    from decimal import Decimal

    async def run():
        engine = create_async_engine(settings.async_database_url)
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

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

            result = await session.execute(select(Airport).limit(1))
            existing = result.scalar_one_or_none()

            if existing and not force:
                typer.echo(
                    "Scope 3 reference data already seeded. Use --force to re-seed."
                )
                raise typer.Exit(code=0)

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
                await session.commit()

            typer.echo("Seeding airports...")
            for iata_code, airport_data in AIRPORTS.items():
                name, city, country_code, latitude, longitude = airport_data
                airport = Airport(
                    id=uuid4(),
                    iata_code=iata_code,
                    name=name,
                    city=city,
                    country_code=country_code,
                    country_name=country_code,
                    latitude=Decimal(str(latitude)),
                    longitude=Decimal(str(longitude)),
                    is_active=True,
                )
                session.add(airport)
                stats["airports"] += 1

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

            typer.echo("Seeding currency conversion rates...")
            for currency, rate in CURRENCY_RATES.items():
                if currency == "USD":
                    continue
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

            typer.echo("Seeding grid emission factors...")
            for country_code, data in GRID_EMISSION_FACTORS.items():
                grid_factor = GridEmissionFactor(
                    id=uuid4(),
                    country_code=country_code,
                    country_name=country_code,
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


@app.command()
def load_cbam_defaults(
    file_path: str = typer.Argument(
        ..., help="Path to the Commission default-values file (.xlsx or .csv)"
    ),
    source: str = typer.Option(
        "EU Commission definitive-period default values (13 Feb 2026)",
        "--source",
        help="Source label stored on each row",
    ),
    valid_from: str = typer.Option(
        "2026-01-01", "--valid-from", help="Validity start date (YYYY-MM-DD)"
    ),
    replace: bool = typer.Option(
        False,
        "--replace",
        help="Deactivate existing rows with the same source before loading",
    ),
):
    """Load CBAM default emission values (per CN code x origin country).

    Ingests the EU Commission default-values file format (Excel published
    13 Feb 2026) or a CSV with equivalent columns into cbam_default_values.

    Example:
        python -m app.cli.seed load-cbam-defaults cbam_defaults_2026.xlsx
    """
    from datetime import date as date_cls
    from uuid import uuid4 as _uuid4

    from app.models.cbam import CBAMDefaultValue, CBAMSector
    from app.services.cbam_defaults_loader import parse_default_values_file

    rows = parse_default_values_file(file_path)
    valid_from_date = date_cls.fromisoformat(valid_from)

    async def run():
        engine = create_async_engine(settings.async_database_url)
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            if replace:
                from sqlalchemy import update

                await session.execute(
                    update(CBAMDefaultValue)
                    .where(CBAMDefaultValue.source == source)
                    .values(is_active=False)
                )

            skipped = 0
            loaded = 0
            for row in rows:
                if row["sector"] is None:
                    skipped += 1
                    continue
                session.add(
                    CBAMDefaultValue(
                        id=_uuid4(),
                        cn_code=row["cn_code"],
                        sector=CBAMSector(row["sector"]),
                        product_description=row["product_description"][:500],
                        country_code=row["country_code"],
                        dataset_year=row["dataset_year"],
                        dataset_version=row["dataset_version"],
                        direct_see=row["direct_see"],
                        indirect_see=row["indirect_see"],
                        total_see=row["total_see"],
                        source=source,
                        valid_from=valid_from_date,
                        is_active=True,
                    )
                )
                loaded += 1
            await session.commit()

            typer.echo(f"Loaded {loaded} default values from {file_path}")
            if skipped:
                typer.echo(f"Skipped {skipped} rows with CN codes outside CBAM Annex I")

        await engine.dispose()

    asyncio.run(run())


@app.command()
def seed_cbam_defaults(
    force: bool = typer.Option(
        False, "--force", help="Re-seed even if representative rows exist"
    ),
):
    """Seed representative per-sector CBAM default values (source=representative_v0).

    Mirrors the sector intensities in app/services/cbam_screening.py. The
    alembic migration b6c7d8e9f0a1 seeds these on deploy; this command is
    for fresh/dev databases and re-seeding.
    """
    from datetime import date as date_cls
    from uuid import uuid4 as _uuid4

    from app.models.cbam import CBAMDefaultValue, CBAMSector
    from app.services.cbam_screening import (
        _CN_PREFIX_SECTORS,
        SECTOR_DEFAULT_INTENSITY,
        SECTOR_LABELS,
    )

    async def run():
        engine = create_async_engine(settings.async_database_url)
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            result = await session.execute(
                select(CBAMDefaultValue)
                .where(CBAMDefaultValue.source == "representative_v0")
                .limit(1)
            )
            if result.scalar_one_or_none() and not force:
                typer.echo(
                    "Representative CBAM defaults already seeded. "
                    "Use --force to re-seed."
                )
                raise typer.Exit(code=0)

            if force:
                from sqlalchemy import delete

                await session.execute(
                    delete(CBAMDefaultValue).where(
                        CBAMDefaultValue.source == "representative_v0"
                    )
                )

            count = 0
            for cn_prefix, sector in _CN_PREFIX_SECTORS:
                see = SECTOR_DEFAULT_INTENSITY[sector]
                unit_note = " (tCO2e/MWh)" if sector == "electricity" else ""
                session.add(
                    CBAMDefaultValue(
                        id=_uuid4(),
                        cn_code=cn_prefix,
                        sector=CBAMSector(sector),
                        product_description=(
                            f"{SECTOR_LABELS[sector]} (representative){unit_note}"
                        ),
                        country_code=None,
                        dataset_year=2026,
                        dataset_version="representative_v0",
                        direct_see=see,
                        indirect_see=None,
                        total_see=see,
                        source="representative_v0",
                        source_reference="app/services/cbam_screening.py",
                        valid_from=date_cls(2026, 1, 1),
                        is_active=True,
                    )
                )
                count += 1
            await session.commit()
            typer.echo(f"Seeded {count} representative CBAM default values.")

        await engine.dispose()

    asyncio.run(run())


if __name__ == "__main__":
    app()
