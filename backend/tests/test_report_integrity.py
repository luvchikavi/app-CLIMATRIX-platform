"""Report-integrity tests (GHG coverage review, Tier A fixes).

Every disclosure a report prints must be backed by real data:
- A1: consolidation approach comes from the org, never hardcoded
- A2: biogenic CO2 is computed, stored, and disclosed separately
- A3: base-year comparison is real or omitted — never fabricated zeros
- A4: market-based Scope 2 flows into the CDP/ESRS exports
- C3: exclusions come from the org's documented CategoryProfile rows
"""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def biodiesel_factor(test_session: AsyncSession):
    """Biodiesel factor carrying a biogenic outside-of-scopes factor."""
    from app.models.emission import EmissionFactor

    factor = EmissionFactor(
        id=uuid4(),
        activity_key="biodiesel_liters",
        display_name="Biodiesel (B100)",
        scope=1,
        category_code="1.1",
        co2_factor=Decimal("0.0"),
        ch4_factor=Decimal("0.0001"),
        n2o_factor=Decimal("0.0001"),
        co2e_factor=Decimal("0.17"),
        biogenic_co2_factor=Decimal("2.4952"),
        activity_unit="liters",
        factor_unit="kg CO2e/liter",
        source="DEFRA_2024",
        region="Global",
        year=2024,
        status="approved",
    )
    test_session.add(factor)
    await test_session.commit()
    return factor


@pytest.fixture
async def gb_electricity_factor(test_session: AsyncSession):
    """GB grid factor — GB has a residual-mix market factor (0.312)."""
    from app.models.emission import EmissionFactor

    factor = EmissionFactor(
        id=uuid4(),
        activity_key="electricity_gb",
        display_name="Electricity (UK Grid)",
        scope=2,
        category_code="2",
        co2e_factor=Decimal("0.207"),
        activity_unit="kWh",
        factor_unit="kg CO2e/kWh",
        source="DEFRA_2024",
        region="GB",
        year=2024,
        status="approved",
    )
    test_session.add(factor)
    await test_session.commit()
    return factor


async def _create_activity(client: AsyncClient, period_id, headers, **overrides):
    payload = {
        "scope": 1,
        "category_code": "1.1",
        "activity_key": "natural_gas_kwh",
        "description": "Test activity",
        "quantity": 1000,
        "unit": "kWh",
        "activity_date": "2025-06-15",
    }
    payload.update(overrides)
    response = await client.post(
        f"/api/periods/{period_id}/activities", headers=headers, json=payload
    )
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------------------
# A1 — consolidation approach reflects the org setting
# ---------------------------------------------------------------------------


async def test_iso_report_uses_org_consolidation_approach(
    client: AsyncClient, test_session, test_org, test_period, auth_headers
):
    test_org.consolidation_approach = "financial_control"
    test_session.add(test_org)
    await test_session.commit()

    response = await client.get(
        f"/api/periods/{test_period.id}/report/ghg-inventory", headers=auth_headers
    )
    assert response.status_code == 200
    report = response.json()
    assert report["boundaries"]["consolidation_approach"] == "financial_control"
    # The assumptions narrative must carry the same approach, not a hardcoded one
    assert any(
        "Financial control" in line for line in report["methodology"]["assumptions"]
    )


async def test_cdp_and_esrs_use_org_consolidation_approach(
    client: AsyncClient, test_session, test_org, test_period, auth_headers
):
    test_org.consolidation_approach = "equity_share"
    test_session.add(test_org)
    await test_session.commit()

    cdp = await client.get(
        f"/api/periods/{test_period.id}/export/cdp", headers=auth_headers
    )
    assert cdp.status_code == 200
    assert cdp.json()["reporting_boundary"] == "Equity share"

    esrs = await client.get(
        f"/api/periods/{test_period.id}/export/esrs-e1", headers=auth_headers
    )
    assert esrs.status_code == 200
    assert esrs.json()["consolidation_scope"] == "Equity share"


# ---------------------------------------------------------------------------
# A2 — biogenic CO2 computed, stored, and disclosed separately
# ---------------------------------------------------------------------------


async def test_biodiesel_biogenic_co2_computed_and_disclosed(
    client: AsyncClient, test_period, auth_headers, biodiesel_factor
):
    data = await _create_activity(
        client,
        test_period.id,
        auth_headers,
        activity_key="biodiesel_liters",
        quantity=100,
        unit="liters",
    )
    # Scope 1 CO2e counts only non-CO2 gases; biogenic CO2 is separate
    assert data["emission"]["co2e_kg"] == pytest.approx(17.0, rel=0.01)

    report = await client.get(
        f"/api/periods/{test_period.id}/report/ghg-inventory", headers=auth_headers
    )
    assert report.status_code == 200
    body = report.json()
    # 100 L × 2.4952 kg/L = 249.52 kg = 0.24952 t, and never in the scope total
    assert body["biogenic_co2_tonnes"] == pytest.approx(0.2495, rel=0.01)
    assert body["total_emissions_kg"] == pytest.approx(17.0, rel=0.01)
    assert any(
        "Biogenic" in line for line in body["methodology"]["exclusions"]
    ), "biogenic policy line missing while biogenic CO2 exists"


async def test_no_biogenic_line_without_biogenic_sources(
    client: AsyncClient, test_period, auth_headers, seed_emission_factors
):
    await _create_activity(client, test_period.id, auth_headers)
    report = await client.get(
        f"/api/periods/{test_period.id}/report/ghg-inventory", headers=auth_headers
    )
    body = report.json()
    assert body["biogenic_co2_tonnes"] is None
    assert not any("Biogenic" in line for line in body["methodology"]["exclusions"])


# ---------------------------------------------------------------------------
# A3 — base-year comparison: real numbers or omitted
# ---------------------------------------------------------------------------


async def test_base_year_comparison_omitted_without_data(
    client: AsyncClient,
    test_session,
    test_org,
    test_period,
    auth_headers,
    seed_emission_factors,
):
    test_org.base_year = 2023
    test_session.add(test_org)
    await test_session.commit()

    await _create_activity(client, test_period.id, auth_headers)
    report = await client.get(
        f"/api/periods/{test_period.id}/report/ghg-inventory", headers=auth_headers
    )
    assert report.status_code == 200
    # No 2023 inventory exists — the section must be omitted, not zeros
    assert report.json()["base_year_comparison"] is None


async def test_base_year_comparison_computed_from_real_data(
    client: AsyncClient,
    test_session,
    test_org,
    test_period,
    auth_headers,
    seed_emission_factors,
):
    from app.models.core import ReportingPeriod

    test_org.base_year = 2023
    test_session.add(test_org)

    base_period = ReportingPeriod(
        id=uuid4(),
        organization_id=test_org.id,
        name="FY2023",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        is_locked=False,
    )
    test_session.add(base_period)
    await test_session.commit()

    # 2023: 2000 kWh gas = 366 kg; 2025: 1000 kWh = 183 kg
    await _create_activity(
        client,
        base_period.id,
        auth_headers,
        quantity=2000,
        activity_date="2023-06-15",
    )
    await _create_activity(client, test_period.id, auth_headers)

    report = await client.get(
        f"/api/periods/{test_period.id}/report/ghg-inventory", headers=auth_headers
    )
    comparison = report.json()["base_year_comparison"]
    assert comparison is not None
    assert comparison["base_year"] == 2023
    assert comparison["base_year_emissions_tonnes"] == pytest.approx(0.37, rel=0.05)
    assert comparison["current_emissions_tonnes"] == pytest.approx(0.18, rel=0.06)
    assert comparison["absolute_change_tonnes"] < 0
    assert comparison["percentage_change"] < 0


# ---------------------------------------------------------------------------
# A4 — market-based Scope 2 present in CDP / ESRS exports
# ---------------------------------------------------------------------------


async def test_cdp_export_carries_market_based_scope2(
    client: AsyncClient, test_period, auth_headers, gb_electricity_factor
):
    await _create_activity(
        client,
        test_period.id,
        auth_headers,
        scope=2,
        category_code="2",
        activity_key="electricity_gb",
        quantity=10000,
        unit="kWh",
    )

    cdp = await client.get(
        f"/api/periods/{test_period.id}/export/cdp", headers=auth_headers
    )
    assert cdp.status_code == 200
    body = cdp.json()
    # 10,000 kWh × 0.312 (GB residual mix) = 3,120 kg = 3.12 t
    assert body["emissions_totals"][
        "scope_2_market_based_metric_tonnes"
    ] == pytest.approx(3.12, rel=0.01)
    gb_rows = [
        r
        for r in body["scope_2_breakdown"]
        if r["market_based_emissions_tonnes"] is not None
    ]
    assert gb_rows, "no scope-2 breakdown row carries a market-based figure"

    esrs = await client.get(
        f"/api/periods/{test_period.id}/export/esrs-e1", headers=auth_headers
    )
    assert esrs.json()["gross_emissions"][
        "scope_2_market_based_tonnes"
    ] == pytest.approx(3.12, rel=0.01)


# ---------------------------------------------------------------------------
# C3 — exclusions come from documented CategoryProfile rows
# ---------------------------------------------------------------------------


async def test_iso_exclusions_reflect_category_profiles(
    client: AsyncClient,
    test_session,
    test_org,
    test_period,
    auth_headers,
    seed_emission_factors,
):
    from app.models.hub import CategoryProfile, CategoryRelevance

    profile = CategoryProfile(
        organization_id=test_org.id,
        scope=3,
        category_code="3.14",
        relevance=CategoryRelevance.NOT_RELEVANT,
        exclusion_reason="No franchise operations",
    )
    test_session.add(profile)
    await test_session.commit()

    await _create_activity(client, test_period.id, auth_headers)
    report = await client.get(
        f"/api/periods/{test_period.id}/report/ghg-inventory", headers=auth_headers
    )
    exclusions = report.json()["methodology"]["exclusions"]
    assert any(
        "3.14" in line and "No franchise operations" in line for line in exclusions
    )
    # The old static fiction must be gone
    assert not any("De minimis" in line for line in exclusions)


async def test_iso_exclusions_honest_when_none_documented(
    client: AsyncClient, test_period, auth_headers, seed_emission_factors
):
    await _create_activity(client, test_period.id, auth_headers)
    report = await client.get(
        f"/api/periods/{test_period.id}/report/ghg-inventory", headers=auth_headers
    )
    assert report.json()["methodology"]["exclusions"] == [
        "No GHG inventory categories excluded"
    ]


# ---------------------------------------------------------------------------
# Methodology single source of truth
# ---------------------------------------------------------------------------


async def test_methodology_reference_endpoint(client: AsyncClient):
    response = await client.get("/api/reference/methodology")
    assert response.status_code == 200
    body = response.json()
    assert body["gwp_source"] == "IPCC AR6 (2021) - 100-year GWP values"
    assert {a["value"] for a in body["consolidation_approaches"]} == {
        "operational_control",
        "financial_control",
        "equity_share",
    }
    assert {t["tier"] for t in body["data_quality_tiers"]} == {
        "measured",
        "calculated",
        "estimated",
    }
    assert body["biogenic_policy"]
