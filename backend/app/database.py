"""
Database connection and session management.
Uses SQLModel with async SQLAlchemy.
"""
import logging
import os
from typing import AsyncGenerator
from uuid import uuid4
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


async def add_missing_columns() -> None:
    """Add missing columns to existing tables (manual migration)."""
    from sqlalchemy import text

    # SQL statements to add missing columns if they don't exist
    # PostgreSQL syntax with IF NOT EXISTS simulation
    migrations = [
        # ReportingPeriod columns
        ("reporting_periods", "status", "ALTER TABLE reporting_periods ADD COLUMN IF NOT EXISTS status VARCHAR(20)"),
        ("reporting_periods", "status_fix", "UPDATE reporting_periods SET status = 'DRAFT' WHERE status IS NULL OR status = 'draft'"),
        ("reporting_periods", "assurance_level", "ALTER TABLE reporting_periods ADD COLUMN IF NOT EXISTS assurance_level VARCHAR(20)"),
        ("reporting_periods", "submitted_at", "ALTER TABLE reporting_periods ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP"),
        ("reporting_periods", "submitted_by_id", "ALTER TABLE reporting_periods ADD COLUMN IF NOT EXISTS submitted_by_id UUID"),
        ("reporting_periods", "verified_at", "ALTER TABLE reporting_periods ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP"),
        ("reporting_periods", "verified_by", "ALTER TABLE reporting_periods ADD COLUMN IF NOT EXISTS verified_by VARCHAR(255)"),
        ("reporting_periods", "verification_statement", "ALTER TABLE reporting_periods ADD COLUMN IF NOT EXISTS verification_statement TEXT"),
        # Activity columns for data quality
        ("activities", "data_quality_score", "ALTER TABLE activities ADD COLUMN IF NOT EXISTS data_quality_score INTEGER DEFAULT 5"),
        ("activities", "data_quality_justification", "ALTER TABLE activities ADD COLUMN IF NOT EXISTS data_quality_justification VARCHAR(500)"),
        ("activities", "supporting_document_url", "ALTER TABLE activities ADD COLUMN IF NOT EXISTS supporting_document_url VARCHAR(500)"),
        # CBAMImport sector column
        ("cbam_imports", "sector", "ALTER TABLE cbam_imports ADD COLUMN IF NOT EXISTS sector VARCHAR(20)"),
        # Make emission_factor_id nullable for supplier-specific factors
        ("emissions", "emission_factor_id_nullable", "ALTER TABLE emissions ALTER COLUMN emission_factor_id DROP NOT NULL"),
        # Organization subscription/billing columns
        ("organizations", "stripe_customer_id", "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255)"),
        ("organizations", "stripe_subscription_id", "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255)"),
        ("organizations", "subscription_plan", "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS subscription_plan VARCHAR(20) DEFAULT 'free'"),
        ("organizations", "subscription_status", "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(20)"),
        ("organizations", "subscription_current_period_end", "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS subscription_current_period_end TIMESTAMP"),
        ("organizations", "trial_ends_at", "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMP"),
        # EmissionFactor governance columns
        ("emission_factors", "status", "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'approved'"),
        ("emission_factors", "version", "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1"),
        ("emission_factors", "previous_version_id", "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS previous_version_id UUID"),
        ("emission_factors", "change_reason", "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS change_reason VARCHAR(500)"),
        ("emission_factors", "notes", "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS notes VARCHAR(1000)"),
        ("emission_factors", "submitted_at", "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP"),
        ("emission_factors", "submitted_by_id", "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS submitted_by_id UUID"),
        ("emission_factors", "approved_at", "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP"),
        ("emission_factors", "approved_by_id", "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS approved_by_id UUID"),
        ("emission_factors", "rejected_at", "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMP"),
        ("emission_factors", "rejected_by_id", "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS rejected_by_id UUID"),
        ("emission_factors", "rejection_reason", "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS rejection_reason VARCHAR(500)"),
        ("emission_factors", "created_by_id", "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS created_by_id UUID"),
        ("emission_factors", "updated_at", "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP"),
        ("emission_factors", "updated_by_id", "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS updated_by_id UUID"),
    ]

    async with engine.begin() as conn:
        for table, column, sql in migrations:
            try:
                await conn.execute(text(sql))
                logger.info(f"Added/verified column {table}.{column}")
            except Exception as e:
                # Column might already exist or table doesn't exist yet
                logger.debug(f"Migration for {table}.{column}: {e}")

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
    """Initialize database tables and seed data if needed."""
    # Run Alembic migrations first (sync operation)
    run_migrations()

    # Then create any new tables that might not exist
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Add missing columns to existing tables (Phase 1 & 2 columns)
    await add_missing_columns()

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
    from app.models.core import Organization, User, UserRole
    from app.data import EMISSION_FACTORS, UNIT_CONVERSIONS, FUEL_PRICES
    from app.api.auth import get_password_hash

    async with async_session_maker() as session:
        # Check if already seeded
        result = await session.execute(select(EmissionFactor).limit(1))
        if result.scalar_one_or_none():
            logger.info("Database already seeded, checking for missing/outdated factors...")
            # Add any missing emission factors
            await add_missing_emission_factors(session)
            # Update existing factors if code values have changed
            await update_existing_emission_factors(session)
            # Still ensure team users exist
            await ensure_team_users(session)
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

        # Create default organization
        logger.info("Creating default organization...")
        org = Organization(
            id=uuid4(),
            name="Drishti",
            country_code="IL",
            industry_code="541611",
            base_year=2024,
            default_region="IL",
        )
        session.add(org)

        # Create super admin user
        logger.info("Creating super admin user...")
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

        await session.commit()
        logger.info("Database seeded successfully!")

        # Create team users
        await ensure_team_users(session)


async def ensure_team_users(session: AsyncSession) -> None:
    """Ensure team users exist with their credentials."""
    from app.models.core import Organization, User, UserRole
    from app.api.auth import get_password_hash

    # Team users to ensure exist (passwords reset on every deploy)
    TEAM_USERS = [
        {"email": "avi@drishti.com", "full_name": "Avi Luvchik", "password": "Luvchik!2030", "role": UserRole.SUPER_ADMIN},
        {"email": "SivanLa@bdo.co.il", "full_name": "Sivan La", "password": "Climatrix2026", "role": UserRole.EDITOR},
        {"email": "LihieI@bdo.co.il", "full_name": "Lihi I", "password": "Climatrix2026", "role": UserRole.EDITOR},
    ]

    # Get organization
    result = await session.execute(select(Organization).limit(1))
    org = result.scalar_one_or_none()

    if not org:
        logger.warning("No organization found, cannot create team users")
        return

    for user_data in TEAM_USERS:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == user_data["email"])
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            # Update password and ensure user is active
            logger.info(f"Updating user: {user_data['email']}")
            existing_user.hashed_password = get_password_hash(user_data["password"])
            existing_user.is_active = True
            existing_user.role = user_data["role"]
            continue

        # Create user
        logger.info(f"Creating user: {user_data['email']}")
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

    await session.commit()


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
