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
            logger.info("Running Alembic migrations...")
            alembic_cfg = Config(alembic_ini)
            # Set the database URL in alembic config
            alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
            command.upgrade(alembic_cfg, "head")
            logger.info("Migrations completed successfully!")
        else:
            logger.warning(f"alembic.ini not found at {alembic_ini}, skipping migrations")
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        # Don't crash the app, just log the error
        # The app might still work with create_all

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
    # This ensures new columns are added to existing tables
    run_migrations()

    # Then create any new tables that might not exist
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Check if we need to seed data
    await seed_if_needed()


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
            logger.info("Database already seeded, skipping...")
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

    # Team users to ensure exist
    TEAM_USERS = [
        {"email": "SivanLa@bdo.co.il", "full_name": "Sivan La", "password": "Climatrix2026!", "role": UserRole.EDITOR},
        {"email": "LihieI@bdo.co.il", "full_name": "Lihi I", "password": "Climatrix2026!", "role": UserRole.EDITOR},
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
