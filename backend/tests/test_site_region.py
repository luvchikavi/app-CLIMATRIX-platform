"""Per-site factor-region resolution (Site.grid_region).

The multi-country fix from the calc audit: an activity tied to a site resolves
emission factors in THAT site's grid region, not the org default. Precedence
everywhere (commit, manual entry, recalculation):

    row/activity region (e.g. hotel stay country) > site.grid_region > org default
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlmodel import select

from app.models.core import Organization, Site
from app.models.emission import Activity, Emission, EmissionFactor
from app.models.ingestion import IngestionSession, RowStatus, StagedRow
from app.services.ingestion import orchestrator


@pytest.fixture
async def regional_electricity_factors(test_session):
    """electricity_kwh in three regions with distinct factors, so the resolved
    region is visible in the committed numbers."""
    factors = {
        "Global": Decimal("0.4"),
        "US": Decimal("0.35"),
        "UK": Decimal("0.21"),
        "CA": Decimal("0.13"),
    }
    for region, value in factors.items():
        test_session.add(
            EmissionFactor(
                id=uuid4(),
                activity_key="electricity_kwh",
                display_name=f"Electricity ({region})",
                scope=2,
                category_code="2",
                co2e_factor=value,
                activity_unit="kWh",
                factor_unit="kg CO2e/kWh",
                source="TEST",
                region=region,
                year=2024,
                status="approved",
            )
        )
    await test_session.commit()
    return factors


@pytest.fixture
async def uk_site(test_session, test_org):
    site = Site(
        id=uuid4(),
        organization_id=test_org.id,
        name="London Plant",
        country_code="GB",
        grid_region="UK",
    )
    test_session.add(site)
    await test_session.commit()
    await test_session.refresh(site)
    return site


async def _staged_electricity_session(
    test_session, test_org, test_user, test_period, *, site_id=None, row_region=None
):
    ingestion = IngestionSession(
        organization_id=test_org.id,
        created_by=test_user.id,
        reporting_period_id=test_period.id,
        site_id=site_id,
        filename="electricity.csv",
    )
    test_session.add(ingestion)
    await test_session.flush()
    row = StagedRow(
        session_id=ingestion.id,
        row_index=0,
        activity_key="electricity_kwh",
        scope=2,
        category_code="2",
        quantity=100.0,
        unit="kWh",
        description="Office electricity",
        region=row_region,
        confidence=0.95,
        band="green",
        status=RowStatus.APPROVED,
    )
    test_session.add(row)
    await test_session.commit()
    await test_session.refresh(ingestion)
    return ingestion


async def _committed_emission(test_session):
    activity = (await test_session.execute(select(Activity))).scalars().one()
    emission = (
        (
            await test_session.execute(
                select(Emission).where(Emission.activity_id == activity.id)
            )
        )
        .scalars()
        .one()
    )
    return activity, emission


async def test_commit_resolves_site_grid_region(
    test_session,
    test_org,
    test_user,
    test_period,
    regional_electricity_factors,
    uk_site,
):
    """Org default US, upload attached to a UK site -> UK grid factor, and the
    committed activity carries the site."""
    ingestion = await _staged_electricity_session(
        test_session, test_org, test_user, test_period, site_id=uk_site.id
    )
    await orchestrator.commit_session(test_session, ingestion)
    await test_session.commit()

    activity, emission = await _committed_emission(test_session)
    assert activity.site_id == uk_site.id
    assert activity.region is None  # no row-level override — site is derivable
    assert emission.factor_region == "UK"
    assert emission.co2e_kg == Decimal("100") * regional_electricity_factors["UK"]


async def test_row_region_beats_site_region(
    test_session,
    test_org,
    test_user,
    test_period,
    regional_electricity_factors,
    uk_site,
):
    """A row-level region (e.g. a stay country from derivation) wins over the
    site, and is persisted on the activity so recalc keeps it."""
    ingestion = await _staged_electricity_session(
        test_session,
        test_org,
        test_user,
        test_period,
        site_id=uk_site.id,
        row_region="CA",
    )
    await orchestrator.commit_session(test_session, ingestion)
    await test_session.commit()

    activity, emission = await _committed_emission(test_session)
    assert activity.region == "CA"
    assert emission.factor_region == "CA"
    assert emission.co2e_kg == Decimal("100") * regional_electricity_factors["CA"]


async def test_commit_without_site_uses_org_default(
    test_session, test_org, test_user, test_period, regional_electricity_factors
):
    ingestion = await _staged_electricity_session(
        test_session, test_org, test_user, test_period
    )
    await orchestrator.commit_session(test_session, ingestion)
    await test_session.commit()

    _, emission = await _committed_emission(test_session)
    assert emission.factor_region == "US"  # the org fixture's default_region


async def test_manual_activity_uses_site_region(
    client,
    auth_headers,
    test_session,
    test_period,
    regional_electricity_factors,
    uk_site,
):
    resp = await client.post(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
        json={
            "scope": 2,
            "category_code": "2",
            "activity_key": "electricity_kwh",
            "description": "London electricity",
            "quantity": 100,
            "unit": "kWh",
            "activity_date": "2025-03-01",
            "site_id": str(uk_site.id),
        },
    )
    assert resp.status_code == 200, resp.text

    activity, emission = await _committed_emission(test_session)
    assert activity.site_id == uk_site.id
    assert emission.factor_region == "UK"


async def test_manual_activity_rejects_foreign_site(
    client, auth_headers, test_session, test_period, regional_electricity_factors
):
    other_org = Organization(id=uuid4(), name="Other Org", default_region="UK")
    test_session.add(other_org)
    await test_session.flush()
    foreign_site = Site(
        id=uuid4(), organization_id=other_org.id, name="Not yours", grid_region="UK"
    )
    test_session.add(foreign_site)
    await test_session.commit()

    resp = await client.post(
        f"/api/periods/{test_period.id}/activities",
        headers=auth_headers,
        json={
            "scope": 2,
            "category_code": "2",
            "activity_key": "electricity_kwh",
            "description": "cross-tenant probe",
            "quantity": 100,
            "unit": "kWh",
            "activity_date": "2025-03-01",
            "site_id": str(foreign_site.id),
        },
    )
    assert resp.status_code == 404


async def test_recalculate_respects_site_and_activity_region(
    client,
    auth_headers,
    test_session,
    test_org,
    test_user,
    test_period,
    regional_electricity_factors,
    uk_site,
):
    """Bulk recalc must not flatten a multi-site inventory onto the org region:
    site-linked activities keep the site's grid, and a persisted row region
    (stay country) survives recalculation."""
    from datetime import date

    site_linked = Activity(
        organization_id=test_org.id,
        reporting_period_id=test_period.id,
        scope=2,
        category_code="2",
        activity_key="electricity_kwh",
        quantity=Decimal("100"),
        unit="kWh",
        activity_date=date(2025, 3, 1),
        site_id=uk_site.id,
        created_by=test_user.id,
    )
    row_override = Activity(
        organization_id=test_org.id,
        reporting_period_id=test_period.id,
        scope=2,
        category_code="2",
        activity_key="electricity_kwh",
        quantity=Decimal("100"),
        unit="kWh",
        activity_date=date(2025, 3, 1),
        region="CA",
        created_by=test_user.id,
    )
    plain = Activity(
        organization_id=test_org.id,
        reporting_period_id=test_period.id,
        scope=2,
        category_code="2",
        activity_key="electricity_kwh",
        quantity=Decimal("100"),
        unit="kWh",
        activity_date=date(2025, 3, 1),
        created_by=test_user.id,
    )
    test_session.add_all([site_linked, row_override, plain])
    await test_session.commit()

    resp = await client.post(
        f"/api/periods/{test_period.id}/emissions/recalculate", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["recalculated"] == 3

    async def region_of(activity_id):
        emission = (
            (
                await test_session.execute(
                    select(Emission).where(Emission.activity_id == activity_id)
                )
            )
            .scalars()
            .one()
        )
        return emission.factor_region

    assert await region_of(site_linked.id) == "UK"
    assert await region_of(row_override.id) == "CA"
    assert await region_of(plain.id) == "US"


async def test_site_patch_updates_grid_region(client, auth_headers, uk_site):
    resp = await client.patch(
        f"/api/organization/sites/{uk_site.id}",
        headers=auth_headers,
        json={"grid_region": "CA"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["grid_region"] == "CA"
    assert body["name"] == "London Plant"  # untouched fields survive

    # Empty string clears back to "use org default".
    resp = await client.patch(
        f"/api/organization/sites/{uk_site.id}",
        headers=auth_headers,
        json={"grid_region": ""},
    )
    assert resp.status_code == 200
    assert resp.json()["grid_region"] is None


async def test_site_patch_foreign_site_404(client, auth_headers, test_session):
    other_org = Organization(id=uuid4(), name="Other Org")
    test_session.add(other_org)
    await test_session.flush()
    foreign_site = Site(id=uuid4(), organization_id=other_org.id, name="Not yours")
    test_session.add(foreign_site)
    await test_session.commit()

    resp = await client.patch(
        f"/api/organization/sites/{foreign_site.id}",
        headers=auth_headers,
        json={"grid_region": "UK"},
    )
    assert resp.status_code == 404


async def test_upload_rejects_foreign_site(
    client, auth_headers, test_session, test_period, seed_emission_factors
):
    other_org = Organization(id=uuid4(), name="Other Org")
    test_session.add(other_org)
    await test_session.flush()
    foreign_site = Site(id=uuid4(), organization_id=other_org.id, name="Not yours")
    test_session.add(foreign_site)
    await test_session.commit()

    resp = await client.post(
        "/api/ingest",
        headers=auth_headers,
        files={"file": ("data.csv", b"Activity,Quantity,Unit\nx,1,kWh\n", "text/csv")},
        data={
            "reporting_period_id": str(test_period.id),
            "site_id": str(foreign_site.id),
        },
    )
    assert resp.status_code == 404


async def test_commit_body_site_override(
    test_session,
    test_org,
    test_user,
    test_period,
    regional_electricity_factors,
    uk_site,
    client,
    auth_headers,
    monkeypatch,
):
    """A session uploaded with no site can be assigned one at commit time."""
    ingestion = await _staged_electricity_session(
        test_session, test_org, test_user, test_period
    )
    resp = await client.post(
        f"/api/ingest/{ingestion.id}/commit",
        headers=auth_headers,
        json={"site_id": str(uk_site.id)},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["site_id"] == str(uk_site.id)

    activity, emission = await _committed_emission(test_session)
    assert activity.site_id == uk_site.id
    assert emission.factor_region == "UK"


async def test_factor_regions_endpoint(client, regional_electricity_factors):
    resp = await client.get("/api/reference/factor-regions")
    assert resp.status_code == 200
    body = resp.json()
    codes = [r["code"] for r in body]
    assert codes[0] == "Global"  # Global always leads the picker
    assert {"US", "UK", "CA"} <= set(codes)
    uk = next(r for r in body if r["code"] == "UK")
    assert uk["name"] == "United Kingdom"
