"""Sample-data ("Load sample data") endpoint tests.

Runs against the real reference catalog (full emission-factor seed + the
initiative library), so load() exercises the same CalculationPipeline and
recommendation engine the product uses: 51 Galil Steel rows, an SBTi target
and two scenarios — then remove() takes it all back out without touching
anything the user created themselves.
"""

from datetime import date
from uuid import UUID, uuid4

import pytest
from sqlmodel import select

from app.models.core import ReportingPeriod, Site
from app.models.decarbonization import (
    DecarbonizationTarget,
    Scenario,
    ScenarioInitiative,
)
from app.models.emission import Activity, Emission


@pytest.fixture
async def seed_reference(test_session):
    """Full real reference data: emission factors + initiative library."""
    from app.cli.seed import seed_database
    from app.seeds.initiatives import seed_initiatives

    await seed_database(test_session)
    await seed_initiatives(test_session)


@pytest.mark.asyncio
async def test_status_starts_empty(client, auth_headers):
    resp = await client.get("/api/sample-data", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["loaded"] is False
    assert body["activities"] == 0
    assert body["period_id"] is None


@pytest.mark.asyncio
async def test_load_seeds_the_full_sample(
    client, auth_headers, test_session, test_user, seed_reference
):
    resp = await client.post("/api/sample-data", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # All 51 rows calculate against the real catalog — none skipped
    assert body["activities_created"] == 51
    assert body["rows_skipped"] == 0
    # Stage-verified neighborhood (~56.9 kt direct CO2e for Galil Steel)
    assert 40_000 < body["total_co2e_tonnes"] < 75_000
    assert body["target_created"] is True
    assert body["scenarios_created"] == 2

    # Status flips
    status = (await client.get("/api/sample-data", headers=auth_headers)).json()
    assert status["loaded"] is True
    assert status["activities"] == 51
    assert status["period_id"] == body["period_id"]

    # Everything seeded is flagged and org-scoped
    activities = (
        (
            await test_session.execute(
                select(Activity).where(
                    Activity.organization_id == test_user.organization_id
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(activities) == 51
    assert all(a.is_demo for a in activities)

    # Every activity has its emission row (dashboard joins on it)
    emissions = (await test_session.execute(select(Emission))).scalars().all()
    assert len(emissions) == 51

    # The sample period is visible through the periods API with its flag
    periods = (await client.get("/api/periods", headers=auth_headers)).json()
    sample = [p for p in periods if p["is_demo"]]
    assert len(sample) == 1
    assert sample[0]["name"] == "FY2025 (Sample)"

    # Report summary works against the sample period (the dashboard path)
    summary = await client.get(
        f"/api/periods/{body['period_id']}/report/summary", headers=auth_headers
    )
    assert summary.status_code == 200
    assert summary.json()["total_co2e_kg"] > 0

    # Scenarios exist, are flagged, and achievement was trimmed to a
    # credible level (not the >300% stacking artifact)
    scenarios = (
        await client.get("/api/decarbonization/scenarios", headers=auth_headers)
    ).json()
    assert len(scenarios) == 2
    active = [s for s in scenarios if s["is_active"]]
    assert len(active) == 1
    achievement = float(active[0]["target_achievement_percent"])
    assert 50 < achievement <= 125


@pytest.mark.asyncio
async def test_double_load_conflicts(client, auth_headers, seed_reference):
    first = await client.post("/api/sample-data", headers=auth_headers)
    assert first.status_code == 200
    second = await client.post("/api/sample-data", headers=auth_headers)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_remove_takes_everything_back_out(
    client, auth_headers, test_session, test_user, test_period, seed_reference
):
    # The user has real data of their own before loading the sample
    own = Activity(
        organization_id=test_user.organization_id,
        reporting_period_id=test_period.id,
        scope=1,
        category_code="1.1",
        activity_key="natural_gas_kwh",
        description="my own gas meter",
        quantity=1000,
        unit="kWh",
        activity_date=date(2025, 3, 1),
    )
    test_session.add(own)
    await test_session.commit()

    load = (await client.post("/api/sample-data", headers=auth_headers)).json()

    resp = await client.delete("/api/sample-data", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["removed_activities"] == 51
    assert body["removed_scenarios"] == 2
    assert body["removed_targets"] == 1
    assert body["period_removed"] is True

    status = (await client.get("/api/sample-data", headers=auth_headers)).json()
    assert status["loaded"] is False

    # Sample period, site, target, scenarios: gone
    assert (
        await test_session.execute(
            select(ReportingPeriod).where(
                ReportingPeriod.id == UUID(load["period_id"]),
            )
        )
    ).scalar_one_or_none() is None
    assert (
        await test_session.execute(select(Site).where(Site.id == UUID(load["site_id"])))
    ).scalar_one_or_none() is None
    assert (await test_session.execute(select(Scenario))).scalars().all() == []
    assert (
        await test_session.execute(select(DecarbonizationTarget))
    ).scalars().all() == []
    assert (
        await test_session.execute(select(ScenarioInitiative))
    ).scalars().all() == []

    # The user's own activity is untouched
    remaining = (await test_session.execute(select(Activity))).scalars().all()
    assert [a.id for a in remaining] == [own.id]


@pytest.mark.asyncio
async def test_remove_keeps_period_holding_user_data(
    client, auth_headers, test_session, test_user, seed_reference
):
    load = (await client.post("/api/sample-data", headers=auth_headers)).json()

    # The user adds their own activity INTO the sample period
    resp = await client.post(
        f"/api/periods/{load['period_id']}/activities",
        headers=auth_headers,
        json={
            "scope": 1,
            "category_code": "1.1",
            "activity_key": "natural_gas_kwh",
            "description": "my own row in the sample period",
            "quantity": 500,
            "unit": "kWh",
            "activity_date": "2025-05-01",
        },
    )
    assert resp.status_code == 200, resp.text

    body = (await client.delete("/api/sample-data", headers=auth_headers)).json()
    assert body["removed_activities"] == 51
    assert body["period_removed"] is False
    assert body["periods_kept"] == 1

    # Period survives, no longer flagged, still holds the user's row
    period = (
        await test_session.execute(
            select(ReportingPeriod).where(ReportingPeriod.id == UUID(load["period_id"]))
        )
    ).scalar_one()
    assert period.is_demo is False
    remaining = (await test_session.execute(select(Activity))).scalars().all()
    assert len(remaining) == 1
    assert remaining[0].description == "my own row in the sample period"


@pytest.mark.asyncio
async def test_sample_data_is_org_scoped(
    client, auth_headers, test_session, seed_reference
):
    """Another org never sees (or loses) data from an org's sample load."""
    from datetime import timedelta

    from app.api.auth import create_access_token, get_password_hash
    from app.models.core import Organization, User, UserRole

    other_org = Organization(id=uuid4(), name="Other Org", country_code="US")
    test_session.add(other_org)
    other_user = User(
        id=uuid4(),
        email="other@example.com",
        hashed_password=get_password_hash("password-123"),
        full_name="Other User",
        organization_id=other_org.id,
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(other_user)
    await test_session.commit()
    other_headers = {
        "Authorization": "Bearer "
        + create_access_token(
            data={
                "sub": str(other_user.id),
                "org_id": str(other_org.id),
                "role": other_user.role.value,
            },
            expires_delta=timedelta(hours=1),
        )
    }

    assert (
        await client.post("/api/sample-data", headers=auth_headers)
    ).status_code == 200

    status = (await client.get("/api/sample-data", headers=other_headers)).json()
    assert status["loaded"] is False

    # Other org removing sample data is a harmless no-op
    body = (await client.delete("/api/sample-data", headers=other_headers)).json()
    assert body["removed_activities"] == 0

    # First org's sample is still intact
    status = (await client.get("/api/sample-data", headers=auth_headers)).json()
    assert status["loaded"] is True
