"""
Pytest configuration and fixtures for CLIMATRIX tests.
"""
import pytest
from typing import AsyncGenerator
from uuid import uuid4

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

from app.main import app
from app.database import get_session
from app.config import settings
from app.api.auth import get_password_hash


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with overridden database session."""

    async def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_org(test_session: AsyncSession):
    """Create a test organization."""
    from app.models.core import Organization

    org = Organization(
        id=uuid4(),
        name="Test Organization",
        country_code="US",
        default_region="US",
    )
    test_session.add(org)
    await test_session.commit()
    await test_session.refresh(org)
    return org


@pytest.fixture
async def test_user(test_session: AsyncSession, test_org):
    """Create a test user."""
    from app.models.core import User, UserRole

    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        organization_id=test_org.id,
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(test_session: AsyncSession, test_org):
    """Create a test super admin user."""
    from app.models.core import User, UserRole

    user = User(
        id=uuid4(),
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin User",
        organization_id=test_org.id,
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(test_user) -> dict:
    """Get authorization headers for test user."""
    from app.api.auth import create_access_token
    from datetime import timedelta

    token = create_access_token(
        data={
            "sub": str(test_user.id),
            "org_id": str(test_user.organization_id),
            "role": test_user.role.value,
        },
        expires_delta=timedelta(hours=1),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_headers(test_admin) -> dict:
    """Get authorization headers for admin user."""
    from app.api.auth import create_access_token
    from datetime import timedelta

    token = create_access_token(
        data={
            "sub": str(test_admin.id),
            "org_id": str(test_admin.organization_id),
            "role": test_admin.role.value,
        },
        expires_delta=timedelta(hours=1),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_period(test_session: AsyncSession, test_org):
    """Create a test reporting period."""
    from datetime import date
    from app.models.core import ReportingPeriod

    period = ReportingPeriod(
        id=uuid4(),
        organization_id=test_org.id,
        name="Test Period 2025",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        is_locked=False,
    )
    test_session.add(period)
    await test_session.commit()
    await test_session.refresh(period)
    return period


@pytest.fixture
async def seed_emission_factors(test_session: AsyncSession):
    """Seed emission factors for testing."""
    from decimal import Decimal
    from app.models.emission import EmissionFactor

    factors = [
        EmissionFactor(
            id=uuid4(),
            activity_key="natural_gas_kwh",
            display_name="Natural Gas (kWh)",
            scope=1,
            category_code="1.1",
            co2e_factor=Decimal("0.183"),
            activity_unit="kWh",
            factor_unit="kg CO2e/kWh",
            source="DEFRA_2024",
            region="Global",
            year=2024,
            status="approved",
        ),
        EmissionFactor(
            id=uuid4(),
            activity_key="petrol_liters",
            display_name="Petrol (liters)",
            scope=1,
            category_code="1.2",
            co2e_factor=Decimal("2.31"),
            activity_unit="liters",
            factor_unit="kg CO2e/liter",
            source="DEFRA_2024",
            region="Global",
            year=2024,
            status="approved",
        ),
        EmissionFactor(
            id=uuid4(),
            activity_key="electricity_kwh",
            display_name="Electricity (kWh)",
            scope=2,
            category_code="2",
            co2e_factor=Decimal("0.4"),
            activity_unit="kWh",
            factor_unit="kg CO2e/kWh",
            source="IEA_2024",
            region="Global",
            year=2024,
            status="approved",
        ),
    ]

    for factor in factors:
        test_session.add(factor)

    await test_session.commit()
    return factors
