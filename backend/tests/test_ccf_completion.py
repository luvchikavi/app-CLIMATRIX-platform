"""
CCF completion tests: base-year recalculation policy, Scope-3 screening
disclosure in the GHG inventory report, and the VSME Basic Module export.
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_org_recalculation_threshold_defaults_and_patch(
    client: AsyncClient, test_org, auth_headers
):
    """Threshold defaults to 5%, is editable, and rejects nonsense values."""
    response = await client.get("/api/organization", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["recalculation_threshold_pct"] == 5.0

    response = await client.patch(
        "/api/organization",
        headers=auth_headers,
        json={"recalculation_threshold_pct": 10},
    )
    assert response.status_code == 200
    assert response.json()["recalculation_threshold_pct"] == 10.0

    for bad in (0, -1, 150):
        response = await client.patch(
            "/api/organization",
            headers=auth_headers,
            json={"recalculation_threshold_pct": bad},
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_ghg_report_recalculation_policy(
    client: AsyncClient, test_org, test_period, auth_headers
):
    """The report states the base-year recalculation policy with the org's
    real base year and threshold."""
    # Without a base year: honest "not set" statement.
    response = await client.get(
        f"/api/periods/{test_period.id}/report/ghg-inventory",
        headers=auth_headers,
    )
    assert response.status_code == 200
    policy = response.json()["recalculation_policy"]
    assert "No base year has been set" in policy
    assert "5%" in policy

    # With a base year + custom threshold: both appear.
    response = await client.patch(
        "/api/organization",
        headers=auth_headers,
        json={"base_year": 2023, "recalculation_threshold_pct": 10},
    )
    assert response.status_code == 200

    response = await client.get(
        f"/api/periods/{test_period.id}/report/ghg-inventory",
        headers=auth_headers,
    )
    assert response.status_code == 200
    policy = response.json()["recalculation_policy"]
    assert "Base year: 2023" in policy
    assert "10%" in policy
    assert "GHG Protocol" in policy


@pytest.mark.asyncio
async def test_ghg_report_scope3_screening(
    client: AsyncClient, test_session, test_org, test_period, auth_headers
):
    """All 15 Scope-3 categories appear with the hub relevance decision and
    real measured coverage for the period."""
    # Document one exclusion in the hub profile.
    response = await client.put(
        "/api/hub/profile",
        headers=auth_headers,
        json={
            "entries": [
                {
                    "category_code": "3.14",
                    "relevance": "not_relevant",
                    "exclusion_reason": "No franchise operations",
                }
            ]
        },
    )
    assert response.status_code == 200

    # Measure one category: seed a Scope-3 factor and record an activity.
    from app.models.emission import EmissionFactor

    test_session.add(
        EmissionFactor(
            id=uuid4(),
            activity_key="flight_km",
            display_name="Flight (km)",
            scope=3,
            category_code="3.6",
            co2e_factor=Decimal("0.15"),
            activity_unit="km",
            factor_unit="kg CO2e/km",
            source="DEFRA_2024",
            region="Global",
            year=2024,
            status="approved",
        )
    )
    await test_session.commit()

    response = await client.post(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
        json={
            "scope": 3,
            "category_code": "3.6",
            "activity_key": "flight_km",
            "description": "Flight",
            "quantity": 1000,
            "unit": "km",
            "activity_date": "2025-01-15",
        },
    )
    assert response.status_code == 200

    response = await client.get(
        f"/api/periods/{test_period.id}/report/ghg-inventory",
        headers=auth_headers,
    )
    assert response.status_code == 200
    screening = response.json()["scope3_screening"]

    assert len(screening) == 15
    by_code = {row["category_code"]: row for row in screening}

    assert by_code["3.14"]["relevance"] == "not_relevant"
    assert by_code["3.14"]["exclusion_reason"] == "No franchise operations"
    assert by_code["3.14"]["measured_this_period"] is False

    assert by_code["3.6"]["measured_this_period"] is True
    assert by_code["3.6"]["activity_count"] == 1
    # Value goes through the flight calculator (RF uplift) — just assert
    # the measured tonnage is present, not its exact size.
    assert by_code["3.6"]["co2e_tonnes"] > 0

    # Untouched categories stay honestly unassessed.
    assert by_code["3.11"]["relevance"] == "not_sure"
    assert by_code["3.11"]["measured_this_period"] is False


@pytest.mark.asyncio
async def test_vsme_export(
    client: AsyncClient,
    test_org,
    test_period,
    auth_headers,
    seed_emission_factors,
):
    """VSME B3 export carries scope totals and metered electricity in MWh."""
    for payload in (
        {
            "scope": 1,
            "category_code": "1.1",
            "activity_key": "natural_gas_kwh",
            "description": "Gas",
            "quantity": 1000,
            "unit": "kWh",
            "activity_date": "2025-01-15",
        },
        {
            "scope": 2,
            "category_code": "2",
            "activity_key": "electricity_kwh",
            "description": "Electricity",
            "quantity": 500,
            "unit": "kWh",
            "activity_date": "2025-01-15",
        },
    ):
        response = await client.post(
            f"/api/periods/{test_period.id}/activities",
            headers=auth_headers,
            json=payload,
        )
        assert response.status_code == 200

    response = await client.get(
        f"/api/periods/{test_period.id}/export/vsme",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert "VSME" in data["standard"]
    assert data["ghg_emissions"]["scope_1_tonnes"] == 0.18  # 1000 × 0.183 kg
    assert data["ghg_emissions"]["scope_2_location_based_tonnes"] == 0.2
    assert data["ghg_emissions"]["scope_1_and_2_tonnes"] == 0.38
    assert data["ghg_emissions"]["scope_3_tonnes"] is None  # none measured
    assert data["energy"]["electricity_consumption_mwh"] == 0.5
    assert "DEFRA_2024" in data["emission_factor_sources"]


@pytest.mark.asyncio
async def test_vsme_export_requires_auth(client: AsyncClient, test_period):
    """Anonymous callers get 401, like every other export."""
    response = await client.get(f"/api/periods/{test_period.id}/export/vsme")
    assert response.status_code == 401
