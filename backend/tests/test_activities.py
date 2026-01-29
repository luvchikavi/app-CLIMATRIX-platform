"""
Tests for activities and emission calculations.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_activity(
    client: AsyncClient,
    test_period,
    auth_headers,
    seed_emission_factors,
):
    """Test creating an activity with emission calculation."""
    response = await client.post(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
        json={
            "scope": 1,
            "category_code": "1.1",
            "activity_key": "natural_gas_kwh",
            "description": "Office heating",
            "quantity": 1000,
            "unit": "kWh",
            "activity_date": "2025-06-15",
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Check activity was created
    assert data["activity"]["activity_key"] == "natural_gas_kwh"
    assert data["activity"]["quantity"] == 1000

    # Check emission was calculated
    assert data["emission"] is not None
    assert data["emission"]["co2e_kg"] == pytest.approx(183.0, rel=0.01)  # 1000 * 0.183


@pytest.mark.asyncio
async def test_create_activity_unauthorized(client: AsyncClient, test_period):
    """Test creating activity without auth."""
    response = await client.post(
        f"/api/periods/{test_period.id}/activities",
        json={
            "scope": 1,
            "category_code": "1.1",
            "activity_key": "natural_gas_kwh",
            "description": "Test",
            "quantity": 100,
            "unit": "kWh",
            "activity_date": "2025-01-01",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_activities(
    client: AsyncClient,
    test_period,
    auth_headers,
    seed_emission_factors,
):
    """Test getting activities for a period."""
    # First create an activity
    await client.post(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
        json={
            "scope": 1,
            "category_code": "1.2",
            "activity_key": "petrol_liters",
            "description": "Company car",
            "quantity": 50,
            "unit": "liters",
            "activity_date": "2025-03-01",
        },
    )

    # Get activities
    response = await client.get(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_activities_filter_by_scope(
    client: AsyncClient,
    test_period,
    auth_headers,
    seed_emission_factors,
):
    """Test filtering activities by scope."""
    # Create scope 1 activity
    await client.post(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
        json={
            "scope": 1,
            "category_code": "1.1",
            "activity_key": "natural_gas_kwh",
            "description": "Scope 1 activity",
            "quantity": 100,
            "unit": "kWh",
            "activity_date": "2025-01-01",
        },
    )

    # Create scope 2 activity
    await client.post(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
        json={
            "scope": 2,
            "category_code": "2",
            "activity_key": "electricity_kwh",
            "description": "Scope 2 activity",
            "quantity": 200,
            "unit": "kWh",
            "activity_date": "2025-01-01",
        },
    )

    # Filter by scope 1
    response = await client.get(
        f"/api/periods/{test_period.id}/activities?scope=1",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    for item in data:
        assert item["activity"]["scope"] == 1


@pytest.mark.asyncio
async def test_emission_calculation_accuracy(
    client: AsyncClient,
    test_period,
    auth_headers,
    seed_emission_factors,
):
    """Test that emission calculations are accurate."""
    # Test natural gas: 1000 kWh * 0.183 = 183 kg CO2e
    response = await client.post(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
        json={
            "scope": 1,
            "category_code": "1.1",
            "activity_key": "natural_gas_kwh",
            "description": "Gas test",
            "quantity": 1000,
            "unit": "kWh",
            "activity_date": "2025-01-01",
        },
    )
    assert response.status_code == 200
    assert response.json()["emission"]["co2e_kg"] == pytest.approx(183.0, rel=0.01)

    # Test petrol: 100 liters * 2.31 = 231 kg CO2e
    response = await client.post(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
        json={
            "scope": 1,
            "category_code": "1.2",
            "activity_key": "petrol_liters",
            "description": "Petrol test",
            "quantity": 100,
            "unit": "liters",
            "activity_date": "2025-01-01",
        },
    )
    assert response.status_code == 200
    assert response.json()["emission"]["co2e_kg"] == pytest.approx(231.0, rel=0.01)


@pytest.mark.asyncio
async def test_delete_activity(
    client: AsyncClient,
    test_period,
    auth_headers,
    seed_emission_factors,
):
    """Test deleting an activity."""
    # Create activity
    create_response = await client.post(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
        json={
            "scope": 1,
            "category_code": "1.1",
            "activity_key": "natural_gas_kwh",
            "description": "To delete",
            "quantity": 100,
            "unit": "kWh",
            "activity_date": "2025-01-01",
        },
    )
    activity_id = create_response.json()["activity"]["id"]

    # Delete activity
    delete_response = await client.delete(
        f"/api/activities/{activity_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 200

    # Verify it's gone
    get_response = await client.get(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
    )
    activities = get_response.json()
    activity_ids = [a["activity"]["id"] for a in activities]
    assert activity_id not in activity_ids
