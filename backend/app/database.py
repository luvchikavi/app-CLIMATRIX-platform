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
    """Run Alembic migrations to ensure database schema is up to date."""
    try:
        from alembic.config import Config
        from alembic import command

        # Get the directory where this file is located
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_ini = os.path.join(base_dir, "alembic.ini")

        if os.path.exists(alembic_ini):
            # Check if alembic.ini has content
            with open(alembic_ini, 'r') as f:
                content = f.read().strip()
            if content:
                logger.info("Running Alembic migrations...")
                alembic_cfg = Config(alembic_ini)
                alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
                command.upgrade(alembic_cfg, "head")
                logger.info("Migrations completed successfully!")
            else:
                logger.warning("alembic.ini is empty, skipping Alembic migrations")
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


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
