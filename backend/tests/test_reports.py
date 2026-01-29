"""
Tests for reports and period management.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_period(client: AsyncClient, test_org, auth_headers):
    """Test creating a reporting period."""
    response = await client.post(
        "/api/periods",
        headers=auth_headers,
        json={
            "name": "FY2025",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "FY2025"
    assert data["is_locked"] is False


@pytest.mark.asyncio
async def test_get_periods(client: AsyncClient, test_period, auth_headers):
    """Test listing reporting periods."""
    response = await client.get("/api/periods", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_report_summary(
    client: AsyncClient,
    test_period,
    auth_headers,
    seed_emission_factors,
):
    """Test getting report summary."""
    # Create some activities first
    await client.post(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
        json={
            "scope": 1,
            "category_code": "1.1",
            "activity_key": "natural_gas_kwh",
            "description": "Gas",
            "quantity": 1000,
            "unit": "kWh",
            "activity_date": "2025-01-15",
        },
    )
    await client.post(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
        json={
            "scope": 2,
            "category_code": "2",
            "activity_key": "electricity_kwh",
            "description": "Electricity",
            "quantity": 500,
            "unit": "kWh",
            "activity_date": "2025-01-15",
        },
    )

    # Get report summary
    response = await client.get(
        f"/api/periods/{test_period.id}/report/summary",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    # Check totals
    assert data["total_co2e_kg"] > 0
    assert data["scope_1_co2e_kg"] == pytest.approx(183.0, rel=0.01)  # 1000 * 0.183
    assert data["scope_2_co2e_kg"] == pytest.approx(200.0, rel=0.01)  # 500 * 0.4


@pytest.mark.asyncio
async def test_report_by_scope(
    client: AsyncClient,
    test_period,
    auth_headers,
    seed_emission_factors,
):
    """Test getting report breakdown by scope."""
    # Create activities
    await client.post(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
        json={
            "scope": 1,
            "category_code": "1.1",
            "activity_key": "natural_gas_kwh",
            "description": "Gas",
            "quantity": 500,
            "unit": "kWh",
            "activity_date": "2025-01-01",
        },
    )

    response = await client.get(
        f"/api/periods/{test_period.id}/report/by-scope",
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_empty_report(client: AsyncClient, test_period, auth_headers):
    """Test report summary with no activities."""
    response = await client.get(
        f"/api/periods/{test_period.id}/report/summary",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_co2e_kg"] == 0
    assert data["scope_1_co2e_kg"] == 0
    assert data["scope_2_co2e_kg"] == 0
    assert data["scope_3_co2e_kg"] == 0
