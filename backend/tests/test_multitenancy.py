"""
Tests for multi-tenancy isolation.
Ensures users from one organization cannot access data from another.
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.fixture
async def second_org(test_session):
    """Create a second organization for isolation testing."""
    from app.models.core import Organization

    org = Organization(
        id=uuid4(),
        name="Second Organization",
        country_code="GB",
        default_region="GB",
    )
    test_session.add(org)
    await test_session.commit()
    await test_session.refresh(org)
    return org


@pytest.fixture
async def second_user(test_session, second_org):
    """Create a user in the second organization."""
    from app.models.core import User, UserRole
    from app.api.auth import get_password_hash

    user = User(
        id=uuid4(),
        email="other@example.com",
        hashed_password=get_password_hash("otherpassword123"),
        full_name="Other User",
        organization_id=second_org.id,
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def second_user_headers(second_user) -> dict:
    """Get authorization headers for second organization user."""
    from app.api.auth import create_access_token
    from datetime import timedelta

    token = create_access_token(
        data={
            "sub": str(second_user.id),
            "org_id": str(second_user.organization_id),
            "role": second_user.role.value,
        },
        expires_delta=timedelta(hours=1),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def second_period(test_session, second_org):
    """Create a period for the second organization."""
    from datetime import date
    from app.models.core import ReportingPeriod

    period = ReportingPeriod(
        id=uuid4(),
        organization_id=second_org.id,
        name="Second Org Period",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        is_locked=False,
    )
    test_session.add(period)
    await test_session.commit()
    await test_session.refresh(period)
    return period


@pytest.mark.asyncio
async def test_cannot_access_other_org_periods(
    client: AsyncClient,
    test_period,
    second_user_headers,
):
    """Test that user cannot see periods from another organization."""
    response = await client.get("/api/periods", headers=second_user_headers)
    assert response.status_code == 200
    periods = response.json()

    # Should not see test_period (belongs to first org)
    period_ids = [p["id"] for p in periods]
    assert str(test_period.id) not in period_ids


@pytest.mark.asyncio
async def test_cannot_access_other_org_period_by_id(
    client: AsyncClient,
    test_period,
    second_user_headers,
):
    """Test that user cannot access a specific period from another organization."""
    response = await client.get(
        f"/api/periods/{test_period.id}",
        headers=second_user_headers,
    )
    # Should return 404 (not found) - cannot see other org's data
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_create_activity_in_other_org_period(
    client: AsyncClient,
    test_period,
    second_user_headers,
    seed_emission_factors,
):
    """Test that user cannot create activity in another organization's period."""
    response = await client.post(
        f"/api/periods/{test_period.id}/activities",
        headers=second_user_headers,
        json={
            "scope": 1,
            "category_code": "1.1",
            "activity_key": "natural_gas_kwh",
            "description": "Unauthorized activity",
            "quantity": 100,
            "unit": "kWh",
            "activity_date": "2025-01-01",
        },
    )
    # Should fail - period belongs to different org
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_view_other_org_activities(
    client: AsyncClient,
    test_period,
    auth_headers,
    second_user_headers,
    seed_emission_factors,
):
    """Test that activities are isolated by organization."""
    # Create activity in first org's period
    create_response = await client.post(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
        json={
            "scope": 1,
            "category_code": "1.1",
            "activity_key": "natural_gas_kwh",
            "description": "Org 1 Activity",
            "quantity": 500,
            "unit": "kWh",
            "activity_date": "2025-01-01",
        },
    )
    assert create_response.status_code == 200

    # Second org user should not see it
    list_response = await client.get(
        f"/api/periods/{test_period.id}/activities",
        headers=second_user_headers,
    )
    # Should return 404 - period not accessible
    assert list_response.status_code == 404


@pytest.mark.asyncio
async def test_organizations_are_isolated(
    client: AsyncClient,
    test_org,
    second_org,
    auth_headers,
    second_user_headers,
):
    """Test that users can only see their own organization."""
    # First user gets their org
    response1 = await client.get("/api/organization", headers=auth_headers)
    assert response1.status_code == 200
    assert response1.json()["id"] == str(test_org.id)
    assert response1.json()["name"] == "Test Organization"

    # Second user gets their org
    response2 = await client.get("/api/organization", headers=second_user_headers)
    assert response2.status_code == 200
    assert response2.json()["id"] == str(second_org.id)
    assert response2.json()["name"] == "Second Organization"


@pytest.mark.asyncio
async def test_sites_are_isolated(
    client: AsyncClient,
    test_org,
    second_org,
    auth_headers,
    second_user_headers,
):
    """Test that sites are isolated by organization."""
    # Create site for first org
    create_response = await client.post(
        "/api/organization/sites",
        headers=auth_headers,
        json={"name": "Org 1 Site", "country_code": "US"},
    )
    assert create_response.status_code == 200
    site_id = create_response.json()["id"]

    # First user can see the site
    list_response1 = await client.get("/api/organization/sites", headers=auth_headers)
    assert any(s["id"] == site_id for s in list_response1.json())

    # Second user cannot see it
    list_response2 = await client.get("/api/organization/sites", headers=second_user_headers)
    assert not any(s["id"] == site_id for s in list_response2.json())


@pytest.mark.asyncio
async def test_report_isolation(
    client: AsyncClient,
    test_period,
    second_period,
    auth_headers,
    second_user_headers,
    seed_emission_factors,
):
    """Test that reports are isolated by organization."""
    # Create activity in first org
    await client.post(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
        json={
            "scope": 1,
            "category_code": "1.1",
            "activity_key": "natural_gas_kwh",
            "description": "Org 1 Gas",
            "quantity": 1000,
            "unit": "kWh",
            "activity_date": "2025-01-01",
        },
    )

    # First user can see report for their period
    report1 = await client.get(
        f"/api/periods/{test_period.id}/report/summary",
        headers=auth_headers,
    )
    assert report1.status_code == 200
    assert report1.json()["total_co2e_kg"] > 0

    # Second user cannot see report for first org's period
    report2 = await client.get(
        f"/api/periods/{test_period.id}/report/summary",
        headers=second_user_headers,
    )
    assert report2.status_code == 404
