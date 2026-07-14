"""Regression test for WAVE2 finding #9.

DELETE /decarbonization/scenarios/{id} 500'd in prod when the scenario had
initiatives: the "delete associated initiatives" block ran a SELECT instead
of a DELETE, so the scenario delete hit the scenario_initiatives FK. SQLite
doesn't enforce that FK here, so the regression assertion is the orphan
check: after deleting a scenario, its initiative links must be gone.
"""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlmodel import select

from app.models.decarbonization import (
    ComplexityLevel,
    DecarbonizationTarget,
    Initiative,
    InitiativeCategory,
    Scenario,
    ScenarioInitiative,
)


@pytest.fixture
async def scenario_with_initiatives(test_session, test_user):
    """A scenario holding two initiative links, like any real scenario."""
    target = DecarbonizationTarget(
        organization_id=test_user.organization_id,
        name="Test target",
        base_year=2025,
        base_year_emissions_tco2e=Decimal("1000"),
        target_year=2030,
        target_reduction_percent=Decimal("21"),
        target_emissions_tco2e=Decimal("790"),
    )
    test_session.add(target)
    await test_session.flush()

    initiative = Initiative(
        id=uuid4(),
        category=InitiativeCategory.ENERGY_EFFICIENCY,
        name="Test initiative",
        short_description="test",
        applicable_scopes=[1, 2],
        applicable_category_codes=["1.1", "2"],
        applicable_activity_keys=["natural_gas_kwh", "electricity_il"],
        complexity=ComplexityLevel.LOW,
        created_at=datetime.utcnow(),
    )
    test_session.add(initiative)

    scenario = Scenario(
        organization_id=test_user.organization_id,
        target_id=target.id,
        name="Scenario with initiatives",
    )
    test_session.add(scenario)
    await test_session.flush()

    for key in ("natural_gas_kwh", "electricity_il"):
        test_session.add(
            ScenarioInitiative(
                scenario_id=scenario.id,
                initiative_id=initiative.id,
                target_activity_key=key,
                expected_reduction_tco2e=Decimal("50"),
                expected_reduction_percent=Decimal("10"),
            )
        )
    await test_session.commit()
    return scenario


@pytest.mark.asyncio
async def test_delete_scenario_with_initiatives(
    client, auth_headers, test_session, scenario_with_initiatives
):
    scenario_id = scenario_with_initiatives.id

    resp = await client.delete(
        f"/api/decarbonization/scenarios/{scenario_id}", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text

    # Scenario gone
    assert (
        await test_session.execute(select(Scenario).where(Scenario.id == scenario_id))
    ).scalar_one_or_none() is None

    # Regression: initiative links must be deleted, not orphaned (the
    # orphans are what made the FK-enforcing prod database return 500)
    orphans = (
        (
            await test_session.execute(
                select(ScenarioInitiative).where(
                    ScenarioInitiative.scenario_id == scenario_id
                )
            )
        )
        .scalars()
        .all()
    )
    assert orphans == []


@pytest.mark.asyncio
async def test_delete_scenario_not_found(client, auth_headers):
    resp = await client.delete(
        f"/api/decarbonization/scenarios/{uuid4()}", headers=auth_headers
    )
    assert resp.status_code == 404
