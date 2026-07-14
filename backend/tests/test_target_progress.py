"""The single progress-vs-target calculation (core-journeys Phase 1).

GET /decarbonization/targets/{id}/progress is the one source of truth the
UI renders; POST /progress/checkpoints persists the same math. Before this,
the frontend re-derived progress with its own (different) on-track rule.
"""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.decarbonization import DecarbonizationTarget
from app.models.emission import Activity, Emission


@pytest.fixture
async def target_with_emissions(test_session, test_user, test_period):
    """A 1000→790 t target with 900 t of actual emissions in the base period."""
    target = DecarbonizationTarget(
        organization_id=test_user.organization_id,
        name="Progress test target",
        base_year=2025,
        base_year_emissions_tco2e=Decimal("1000"),
        target_year=2030,
        target_reduction_percent=Decimal("21"),
        target_emissions_tco2e=Decimal("790"),
    )
    test_session.add(target)

    for i in range(2):
        activity = Activity(
            organization_id=test_user.organization_id,
            reporting_period_id=test_period.id,
            scope=2,
            category_code="2",
            activity_key="electricity_il",
            description=f"meter {i}",
            quantity=1,
            unit="kWh",
            activity_date=date(2025, 6, 1),
        )
        test_session.add(activity)
        await test_session.flush()
        test_session.add(Emission(activity_id=activity.id, co2e_kg=Decimal("450000")))

    await test_session.commit()
    await test_session.refresh(target)
    return target


@pytest.mark.asyncio
async def test_target_progress_math(
    client, auth_headers, target_with_emissions, test_period
):
    resp = await client.get(
        f"/api/decarbonization/targets/{target_with_emissions.id}/progress",
        params={"period_id": str(test_period.id)},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["checkpoint_year"] == 2025
    assert float(body["actual_emissions_tco2e"]) == 900.0
    assert float(body["planned_emissions_tco2e"]) == 1000.0
    assert float(body["variance_tco2e"]) == -100.0
    assert body["on_track"] is True  # below plan
    # 100 t of the required 210 t reduction achieved
    assert abs(float(body["progress_percent"]) - 47.6) < 0.1
    # base-year period: none of the 2025→2030 window has elapsed
    assert float(body["expected_progress_percent"]) == 0.0


@pytest.mark.asyncio
async def test_checkpoint_persists_the_same_math(
    client, auth_headers, target_with_emissions, test_period
):
    live = (
        await client.get(
            f"/api/decarbonization/targets/{target_with_emissions.id}/progress",
            params={"period_id": str(test_period.id)},
            headers=auth_headers,
        )
    ).json()
    checkpoint_resp = await client.post(
        "/api/decarbonization/progress/checkpoints",
        params={
            "target_id": str(target_with_emissions.id),
            "period_id": str(test_period.id),
        },
        headers=auth_headers,
    )
    assert checkpoint_resp.status_code == 200, checkpoint_resp.text
    checkpoint = checkpoint_resp.json()

    for field in (
        "actual_emissions_tco2e",
        "planned_emissions_tco2e",
        "variance_tco2e",
        "variance_percent",
    ):
        assert float(checkpoint[field]) == float(live[field])
    assert checkpoint["on_track"] == live["on_track"]


@pytest.mark.asyncio
async def test_target_progress_unknown_target_404(client, auth_headers, test_period):
    resp = await client.get(
        f"/api/decarbonization/targets/{uuid4()}/progress",
        params={"period_id": str(test_period.id)},
        headers=auth_headers,
    )
    assert resp.status_code == 404
