"""Verifier read-only portal — token-gated external-auditor access.

The security contract: the token unlocks exactly ONE period's read-only
verification surface (summary + inventory + provenance + audit log) for ONE
org, and nothing else — no other org, no other period, no write, no login.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlmodel import select

from app.models.core import (
    Organization,
    ReportingPeriod,
    User,
    UserRole,
    VerifierAccess,
)
from app.models.emission import Activity, DataSource, Emission


async def _seed_line(test_session, org_id, period_id, user_id):
    activity = Activity(
        organization_id=org_id,
        reporting_period_id=period_id,
        scope=2,
        category_code="2",
        activity_key="electricity_kwh",
        description="Office electricity",
        quantity=Decimal("45600"),
        unit="kWh",
        activity_date=date(2025, 3, 1),
        region="UK",
        created_by=user_id,
        data_source=DataSource.MANUAL,
        data_quality_score=2,
        data_quality_justification="Metered supplier invoice",
    )
    test_session.add(activity)
    await test_session.flush()
    test_session.add(
        Emission(
            activity_id=activity.id,
            co2e_kg=Decimal("9576.0"),
            factor_year=2024,
            factor_region="UK",
            formula="45600 kWh × 0.21 kgCO2e/kWh",
            resolution_strategy="region",
        )
    )
    await test_session.commit()
    return activity


async def _invite(client, admin_headers, period_id, **body):
    payload = {"verifier_email": "auditor@lrqa.com", "verifier_name": "LRQA"}
    payload.update(body)
    return await client.post(
        f"/api/periods/{period_id}/verifier-access",
        headers=admin_headers,
        json=payload,
    )


# ---------------------------------------------------------------------------
# org-side management
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_invites_verifier(client, admin_headers, test_period, test_session):
    resp = await _invite(client, admin_headers, test_period.id)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["verifier_email"] == "auditor@lrqa.com"
    assert body["status"] == "active"
    assert "/verify/" in body["portal_url"]

    # The invite is audit-logged.
    from app.models.core import AuditLog

    logs = (
        (
            await test_session.execute(
                select(AuditLog).where(AuditLog.resource_type == "verifier_access")
            )
        )
        .scalars()
        .all()
    )
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_non_admin_cannot_invite(
    client, auth_headers, test_session, test_org, test_period
):
    # Demote the caller to a non-admin role.
    user = (
        await test_session.execute(select(User).where(User.email == "test@example.com"))
    ).scalar_one()
    user.role = UserRole.VIEWER
    test_session.add(user)
    await test_session.commit()

    resp = await _invite(client, auth_headers, test_period.id)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_invite_foreign_period_404(client, admin_headers, test_session):
    other_org = Organization(id=uuid4(), name="Other Org")
    test_session.add(other_org)
    await test_session.flush()
    foreign_period = ReportingPeriod(
        id=uuid4(),
        organization_id=other_org.id,
        name="Not yours",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
    )
    test_session.add(foreign_period)
    await test_session.commit()

    resp = await _invite(client, admin_headers, foreign_period.id)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# verifier-side (token) read-only surface
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_token_unlocks_period_summary(
    client, admin_headers, test_org, test_user, test_period, test_session
):
    await _seed_line(test_session, test_org.id, test_period.id, test_user.id)
    token = (
        (await _invite(client, admin_headers, test_period.id))
        .json()["portal_url"]
        .split("/verify/")[1]
    )

    resp = await client.get(f"/api/verify/{token}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["organization_name"] == test_org.name
    assert body["period_name"] == test_period.name
    assert body["read_only"] is True
    assert body["scope_2_co2e_kg"] == pytest.approx(9576.0)
    assert body["total_co2e_kg"] == pytest.approx(9576.0)
    assert body["line_count"] == 1

    # Accessing the portal stamps last_accessed_at.
    access = (await test_session.execute(select(VerifierAccess))).scalar_one()
    await test_session.refresh(access)
    assert access.last_accessed_at is not None


@pytest.mark.asyncio
async def test_token_inventory_has_traceability(
    client, admin_headers, test_org, test_user, test_period, test_session
):
    await _seed_line(test_session, test_org.id, test_period.id, test_user.id)
    token = (
        (await _invite(client, admin_headers, test_period.id))
        .json()["portal_url"]
        .split("/verify/")[1]
    )

    resp = await client.get(f"/api/verify/{token}/inventory")
    assert resp.status_code == 200, resp.text
    lines = resp.json()
    assert len(lines) == 1
    line = lines[0]
    assert line["activity_key"] == "electricity_kwh"
    assert line["co2e_kg"] == pytest.approx(9576.0)
    assert line["factor_source_year"] == 2024
    assert line["factor_region"] == "UK"
    assert "0.21" in line["formula"]
    assert line["data_quality_score"] == 2
    assert line["data_quality_justification"] == "Metered supplier invoice"


@pytest.mark.asyncio
async def test_token_audit_log_readable(client, admin_headers, test_period):
    # The invite itself writes an audit entry the verifier can then see.
    token = (
        (await _invite(client, admin_headers, test_period.id))
        .json()["portal_url"]
        .split("/verify/")[1]
    )
    resp = await client.get(f"/api/verify/{token}/audit-log")
    assert resp.status_code == 200, resp.text
    entries = resp.json()
    assert any(e["resource_type"] == "verifier_access" for e in entries)


# ---------------------------------------------------------------------------
# security: revoke / expiry / invalid / isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revoked_token_is_dead(client, admin_headers, test_period, test_session):
    invite = (await _invite(client, admin_headers, test_period.id)).json()
    token = invite["portal_url"].split("/verify/")[1]
    assert (await client.get(f"/api/verify/{token}")).status_code == 200

    revoke = await client.delete(
        f"/api/verifier-access/{invite['id']}", headers=admin_headers
    )
    assert revoke.status_code == 200
    # Immediately dead on the next request.
    assert (await client.get(f"/api/verify/{token}")).status_code == 404
    assert (await client.get(f"/api/verify/{token}/inventory")).status_code == 404


@pytest.mark.asyncio
async def test_expired_token_403(client, admin_headers, test_period, test_session):
    invite = (
        await _invite(client, admin_headers, test_period.id, expires_in_days=7)
    ).json()
    token = invite["portal_url"].split("/verify/")[1]
    # Force expiry into the past.
    access = (await test_session.execute(select(VerifierAccess))).scalar_one()
    access.expires_at = datetime.utcnow() - timedelta(days=1)
    test_session.add(access)
    await test_session.commit()
    assert (await client.get(f"/api/verify/{token}")).status_code == 403


@pytest.mark.asyncio
async def test_invalid_token_404(client):
    assert (await client.get("/api/verify/not-a-real-token")).status_code == 404


@pytest.mark.asyncio
async def test_token_isolates_to_its_period(
    client, admin_headers, test_org, test_user, test_period, test_session
):
    """A token for period A never exposes activities from period B."""
    period_b = ReportingPeriod(
        id=uuid4(),
        organization_id=test_org.id,
        name="Other period",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )
    test_session.add(period_b)
    await test_session.commit()
    await _seed_line(test_session, test_org.id, test_period.id, test_user.id)  # in A
    await _seed_line(test_session, test_org.id, period_b.id, test_user.id)  # in B

    token = (
        (await _invite(client, admin_headers, test_period.id))
        .json()["portal_url"]
        .split("/verify/")[1]
    )
    lines = (await client.get(f"/api/verify/{token}/inventory")).json()
    # Only period A's single line — not B's.
    assert len(lines) == 1
