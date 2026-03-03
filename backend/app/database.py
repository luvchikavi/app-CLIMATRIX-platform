"""
Database connection and session management.
Uses SQLModel with async SQLAlchemy.
"""
import logging
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel, select

from app.config import settings

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Run Alembic migrations to ensure database schema is up to date.

    If the database has never been stamped (tables exist but no alembic_version
    row), stamp it at the comprehensive baseline revision before upgrading.
    """
    try:
        from alembic.config import Config
        from alembic import command
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine, inspect, text

        # Get the directory where this file is located
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_ini = os.path.join(base_dir, "alembic.ini")

        if os.path.exists(alembic_ini):
            # Check if alembic.ini has content
            with open(alembic_ini, 'r') as f:
                content = f.read().strip()
            if not content:
                logger.warning("alembic.ini is empty, skipping Alembic migrations")
                return

            alembic_cfg = Config(alembic_ini)
            alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

            # Check if DB needs to be stamped (tables exist but no alembic revision)
            sync_engine = create_engine(settings.database_url)
            with sync_engine.connect() as conn:
                inspector = inspect(sync_engine)
                tables = inspector.get_table_names()
                has_tables = "emission_factors" in tables
                has_version = "alembic_version" in tables
                current_rev = None
                if has_version:
                    result = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                    row = result.first()
                    current_rev = row[0] if row else None
            sync_engine.dispose()

            if has_tables and not current_rev:
                # DB was created outside of Alembic — stamp at comprehensive baseline
                logger.info("Database exists but no Alembic revision found. Stamping at baseline f1a2b3c4d5e6...")
                command.stamp(alembic_cfg, "f1a2b3c4d5e6")
                logger.info("Stamped successfully.")

            logger.info("Running Alembic migrations...")
            command.upgrade(alembic_cfg, "head")
            logger.info("Migrations completed successfully!")
        else:
            logger.warning(f"alembic.ini not found at {alembic_ini}, skipping migrations")
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")


# Create async engine (use async_database_url to handle Railway's format)
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.database_echo,
    future=True,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables and seed data if needed.

    Note: Alembic migrations are run before server startup via the
    Railway/nixpacks start command, not here (asyncio.run() cannot
    be called inside an already-running event loop).
    """
    # Create any new tables that might not exist
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Check if we need to seed data
    await seed_if_needed()


async def add_missing_emission_factors(session) -> None:
    """Add any emission factors that are in the code but missing from the database."""
    from app.models.emission import EmissionFactor
    from app.data import EMISSION_FACTORS

    # Get all existing activity_keys from the database
    result = await session.execute(select(EmissionFactor.activity_key))
    existing_keys = {row[0] for row in result.all()}

    # Add any missing factors
    added_count = 0
    for ef_data in EMISSION_FACTORS:
        if ef_data["activity_key"] not in existing_keys:
            logger.info(f"Adding missing emission factor: {ef_data['activity_key']}")
            ef = EmissionFactor(**ef_data)
            session.add(ef)
            added_count += 1

    if added_count > 0:
        await session.commit()
        logger.info(f"Added {added_count} missing emission factors")
    else:
        logger.info("All emission factors already exist")


async def update_existing_emission_factors(session) -> None:
    """Update existing emission factors when code values have changed."""
    from app.models.emission import EmissionFactor
    from app.data import EMISSION_FACTORS

    # Build lookup from code: activity_key -> factor data
    code_factors = {ef["activity_key"]: ef for ef in EMISSION_FACTORS}

    # Fetch all existing factors from DB
    result = await session.execute(select(EmissionFactor))
    db_factors = result.scalars().all()

    updated_count = 0
    fields_to_check = [
        "co2_factor", "ch4_factor", "n2o_factor", "co2e_factor",
        "display_name", "source", "activity_unit", "factor_unit",
        "region", "year", "notes",
    ]

    for db_ef in db_factors:
        code_ef = code_factors.get(db_ef.activity_key)
        if not code_ef:
            continue

        changed = False
        for field in fields_to_check:
            code_val = code_ef.get(field)
            db_val = getattr(db_ef, field, None)
            if code_val is not None and db_val != code_val:
                setattr(db_ef, field, code_val)
                changed = True

        if changed:
            updated_count += 1
            logger.info(f"Updated emission factor: {db_ef.activity_key}")

    if updated_count > 0:
        await session.commit()
        logger.info(f"Updated {updated_count} emission factors to match code values")
    else:
        logger.info("All emission factors already up to date")


async def seed_power_producers(session) -> None:
    """Seed or update Israeli power producers from reference data."""
    from app.models.emission import PowerProducer
    from app.data.reference_data import ISRAEL_POWER_PRODUCERS
    from decimal import Decimal

    # Get existing producers: (name_en, year) -> PowerProducer
    result = await session.execute(select(PowerProducer).where(PowerProducer.country_code == "IL"))
    existing = {}
    for p in result.scalars().all():
        existing[(p.producer_name_en, p.year)] = p

    added = 0
    updated = 0
    for prod_data in ISRAEL_POWER_PRODUCERS:
        for year, factor in prod_data["years"].items():
            key = (prod_data["producer_name_en"], year)
            if key in existing:
                # Update if factor changed
                db_prod = existing[key]
                if db_prod.co2e_per_kwh != Decimal(str(factor)):
                    db_prod.co2e_per_kwh = Decimal(str(factor))
                    db_prod.source = prod_data["source"]
                    updated += 1
            else:
                # Insert new
                pp = PowerProducer(
                    producer_name_en=prod_data["producer_name_en"],
                    producer_name_he=prod_data.get("producer_name_he"),
                    country_code=prod_data["country_code"],
                    co2e_per_kwh=Decimal(str(factor)),
                    source=prod_data["source"],
                    source_type=prod_data["source_type"],
                    year=year,
                )
                session.add(pp)
                added += 1

    if added or updated:
        await session.commit()
        logger.info(f"Power producers: added {added}, updated {updated}")
    else:
        logger.info("Power producers already up to date")


async def seed_if_needed() -> None:
    """Seed database with emission factors if empty."""
    from app.models.emission import EmissionFactor, UnitConversion, FuelPrice
    from app.data import EMISSION_FACTORS, UNIT_CONVERSIONS, FUEL_PRICES

    async with async_session_maker() as session:
        # Check if already seeded
        result = await session.execute(select(EmissionFactor).limit(1))
        if result.scalar_one_or_none():
            logger.info("Database already seeded, checking for missing/outdated factors...")
            # Add any missing emission factors
            await add_missing_emission_factors(session)
            # Update existing factors if code values have changed
            await update_existing_emission_factors(session)
            # Seed/update power producers
            await seed_power_producers(session)
            return

        logger.info("Seeding emission factors...")
        for ef_data in EMISSION_FACTORS:
            ef = EmissionFactor(**ef_data)
            session.add(ef)

        logger.info("Seeding unit conversions...")
        for uc_data in UNIT_CONVERSIONS:
            uc = UnitConversion(**uc_data)
            session.add(uc)

        logger.info("Seeding fuel prices...")
        for fp_data in FUEL_PRICES:
            fp = FuelPrice(**fp_data)
            session.add(fp)

        await session.commit()
        logger.info("Database seeded successfully!")

        # Seed power producers (after initial seed commit)
        await seed_power_producers(session)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
