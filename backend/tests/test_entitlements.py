"""Teaser-trial entitlement gating (GOING-LIVE-PLAN Wave 4).

The 14-day trial shows the capability (parser, engine, on-screen results) but
withholds the benefit: no exports of any kind, 1 site / 1 period / 1 seat,
capped import volume, CBAM workflow + decarbonization management locked.
Expired trial falls back to FREE — data preserved, uploads closed.
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.models.core import Organization, SubscriptionPlan
from app.services.billing import PLAN_LIMITS, TRIAL_LIMITS
from app.services.entitlements import resolve_entitlement


def _org(plan: str, status: str | None, trial_delta_days: int | None = None):
    return Organization(
        id=uuid4(),
        name="Entitlement Org",
        country_code="US",
        default_region="US",
        subscription_plan=plan,
        subscription_status=status,
        trial_ends_at=(
            datetime.utcnow() + timedelta(days=trial_delta_days)
            if trial_delta_days is not None
            else None
        ),
    )


# ---------------------------------------------------------------------------
# resolve_entitlement unit tests
# ---------------------------------------------------------------------------


def test_resolve_none_org_is_free():
    ent = resolve_entitlement(None)
    assert ent["effective_plan"] == "free"
    assert not ent["is_trialing"]
    assert ent["limits"]["reports_per_month"] == 0


def test_resolve_active_trial_gets_teaser_limits():
    ent = resolve_entitlement(_org("professional", "trialing", trial_delta_days=7))
    assert ent["is_trialing"] is True
    assert ent["is_expired"] is False
    # the teaser: no exports, single site/period/seat, capped import volume
    assert ent["limits"] == TRIAL_LIMITS
    assert ent["limits"]["reports_per_month"] == 0
    assert ent["limits"]["sites"] == 1
    assert ent["limits"]["periods"] == 1
    assert ent["limits"]["users"] == 1
    assert ent["limits"]["import_files"] == 3
    assert ent["limits"]["import_rows"] == 500


def test_resolve_expired_trial_falls_back_to_free():
    ent = resolve_entitlement(_org("professional", "trialing", trial_delta_days=-1))
    assert ent["is_trialing"] is False
    assert ent["is_expired"] is True
    assert ent["effective_plan"] == "free"
    assert ent["limits"]["import_files"] == 0  # uploads closed, data preserved


def test_resolve_paid_professional_is_unrestricted():
    ent = resolve_entitlement(_org("professional", "active"))
    assert ent["is_trialing"] is False
    assert ent["limits"] == PLAN_LIMITS[SubscriptionPlan.PROFESSIONAL]
    assert ent["limits"]["reports_per_month"] == -1
    assert ent["limits"]["import_files"] == -1


# ---------------------------------------------------------------------------
# endpoint gating — org-state helpers
# ---------------------------------------------------------------------------


async def _set_org_state(
    test_session, org, *, plan: str, status: str | None, trial_delta_days=None
):
    org.subscription_plan = plan
    org.subscription_status = status
    org.trial_ends_at = (
        datetime.utcnow() + timedelta(days=trial_delta_days)
        if trial_delta_days is not None
        else None
    )
    test_session.add(org)
    await test_session.commit()


def _assert_402(response, limit_type: str):
    assert response.status_code == 402, response.text
    detail = response.json()["detail"]
    assert detail["code"] == "limit_reached"
    assert detail["limit_type"] == limit_type


# ---------------------------------------------------------------------------
# exports are locked during trial
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_trial_blocks_report_exports(
    client, test_session, test_org, test_user, test_period, auth_headers
):
    await _set_org_state(
        test_session,
        test_org,
        plan="professional",
        status="trialing",
        trial_delta_days=7,
    )
    for url in (
        f"/api/reports/export/csv?period_id={test_period.id}",
        f"/api/reports/export/pdf?period_id={test_period.id}",
        f"/api/periods/{test_period.id}/export/cdp",
        f"/api/periods/{test_period.id}/export/esrs-e1",
        f"/api/periods/{test_period.id}/report/audit-package",
    ):
        _assert_402(await client.get(url, headers=auth_headers), "exports")


@pytest.mark.asyncio
async def test_trial_allows_onscreen_report_view(
    client, test_session, test_org, test_user, test_period, auth_headers
):
    await _set_org_state(
        test_session,
        test_org,
        plan="professional",
        status="trialing",
        trial_delta_days=7,
    )
    resp = await client.get(
        f"/api/periods/{test_period.id}/report/ghg-inventory", headers=auth_headers
    )
    assert resp.status_code != 402, resp.text


@pytest.mark.asyncio
async def test_paid_org_export_not_402(
    client, test_org, test_user, test_period, auth_headers
):
    # conftest org is professional/active — the export gate must not trigger
    resp = await client.get(
        f"/api/reports/export/csv?period_id={test_period.id}", headers=auth_headers
    )
    assert resp.status_code != 402, resp.text


@pytest.mark.asyncio
async def test_expired_trial_blocks_report_view(
    client, test_session, test_org, test_user, test_period, auth_headers
):
    await _set_org_state(
        test_session,
        test_org,
        plan="professional",
        status="trialing",
        trial_delta_days=-1,
    )
    resp = await client.get(
        f"/api/periods/{test_period.id}/report/ghg-inventory", headers=auth_headers
    )
    _assert_402(resp, "reports")


# ---------------------------------------------------------------------------
# caps: sites / periods / seats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_trial_caps_sites_at_one(
    client, test_session, test_org, test_user, auth_headers
):
    await _set_org_state(
        test_session,
        test_org,
        plan="professional",
        status="trialing",
        trial_delta_days=7,
    )
    first = await client.post(
        "/api/organization/sites",
        json={"name": "HQ", "country_code": "US"},
        headers=auth_headers,
    )
    assert first.status_code == 200, first.text
    second = await client.post(
        "/api/organization/sites",
        json={"name": "Plant 2", "country_code": "US"},
        headers=auth_headers,
    )
    _assert_402(second, "sites")


@pytest.mark.asyncio
async def test_trial_caps_periods_at_one(
    client, test_session, test_org, test_user, test_period, auth_headers
):
    await _set_org_state(
        test_session,
        test_org,
        plan="professional",
        status="trialing",
        trial_delta_days=7,
    )
    resp = await client.post(
        "/api/periods",
        json={"name": "FY2026", "start_date": "2026-01-01", "end_date": "2026-12-31"},
        headers=auth_headers,
    )
    _assert_402(resp, "periods")


@pytest.mark.asyncio
async def test_trial_is_single_seat(
    client, test_session, test_org, test_user, auth_headers
):
    await _set_org_state(
        test_session,
        test_org,
        plan="professional",
        status="trialing",
        trial_delta_days=7,
    )
    resp = await client.post(
        "/api/auth/invitations",
        json={"email": "teammate@example.com", "role": "member"},
        headers=auth_headers,
    )
    _assert_402(resp, "users")


@pytest.mark.asyncio
async def test_paid_org_can_invite(client, test_org, test_user, auth_headers):
    resp = await client.post(
        "/api/auth/invitations",
        json={"email": "teammate@example.com", "role": "member"},
        headers=auth_headers,
    )
    assert resp.status_code != 402, resp.text


# ---------------------------------------------------------------------------
# import volume
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_expired_trial_blocks_uploads(
    client, test_session, test_org, test_user, auth_headers
):
    await _set_org_state(
        test_session,
        test_org,
        plan="professional",
        status="trialing",
        trial_delta_days=-1,
    )
    resp = await client.post(
        "/api/ingest",
        files={"file": ("data.csv", b"description,quantity,unit\n", "text/csv")},
        headers=auth_headers,
    )
    _assert_402(resp, "import_files")


@pytest.mark.asyncio
async def test_trial_file_cap_exhausts_after_three(
    client, test_session, test_org, test_user, auth_headers
):
    from app.models.ingestion import IngestionSession

    await _set_org_state(
        test_session,
        test_org,
        plan="professional",
        status="trialing",
        trial_delta_days=7,
    )
    for i in range(3):
        test_session.add(
            IngestionSession(
                organization_id=test_org.id,
                created_by=test_user.id,
                filename=f"file{i}.csv",
            )
        )
    await test_session.commit()

    resp = await client.post(
        "/api/ingest",
        files={"file": ("data.csv", b"description,quantity,unit\n", "text/csv")},
        headers=auth_headers,
    )
    _assert_402(resp, "import_files")


@pytest.mark.asyncio
async def test_trial_row_cap_blocks_commit_over_500(
    client, test_session, test_org, test_user, test_period, auth_headers
):
    from app.models.ingestion import IngestionSession, RowStatus, StagedRow

    await _set_org_state(
        test_session,
        test_org,
        plan="professional",
        status="trialing",
        trial_delta_days=7,
    )
    ingestion = IngestionSession(
        organization_id=test_org.id,
        created_by=test_user.id,
        reporting_period_id=test_period.id,
        filename="big.csv",
        committed_count=480,  # earlier imports already used most of the allowance
    )
    test_session.add(ingestion)
    await test_session.flush()
    for i in range(30):  # 480 + 30 > 500
        test_session.add(
            StagedRow(
                session_id=ingestion.id,
                row_index=i,
                status=RowStatus.APPROVED,
                description=f"row {i}",
            )
        )
    await test_session.commit()

    resp = await client.post(f"/api/ingest/{ingestion.id}/commit", headers=auth_headers)
    _assert_402(resp, "import_rows")


# ---------------------------------------------------------------------------
# CBAM workflow + decarbonization management are paid-Professional features
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_trial_locks_cbam_workflow(
    client, test_session, test_org, test_user, auth_headers
):
    await _set_org_state(
        test_session,
        test_org,
        plan="professional",
        status="trialing",
        trial_delta_days=7,
    )
    # DELETE routes carry no body, so the gate is what must answer first
    resp = await client.delete(f"/api/cbam/imports/{uuid4()}", headers=auth_headers)
    _assert_402(resp, "cbam")
    resp = await client.get(
        "/api/cbam/reports/annual/2026/export/csv", headers=auth_headers
    )
    _assert_402(resp, "cbam")


@pytest.mark.asyncio
async def test_paid_org_cbam_workflow_open(client, test_org, test_user, auth_headers):
    resp = await client.delete(f"/api/cbam/imports/{uuid4()}", headers=auth_headers)
    assert resp.status_code == 404, resp.text  # gate passed, record not found


@pytest.mark.asyncio
async def test_trial_locks_decarb_writes(
    client, test_session, test_org, test_user, auth_headers
):
    await _set_org_state(
        test_session,
        test_org,
        plan="professional",
        status="trialing",
        trial_delta_days=7,
    )
    resp = await client.delete(
        f"/api/decarbonization/targets/{uuid4()}", headers=auth_headers
    )
    _assert_402(resp, "decarbonization")


@pytest.mark.asyncio
async def test_trial_recommendations_teaser_one_item(
    client, test_session, test_org, test_user, test_period, auth_headers
):
    await _set_org_state(
        test_session,
        test_org,
        plan="professional",
        status="trialing",
        trial_delta_days=7,
    )
    resp = await client.get(
        f"/api/decarbonization/recommendations?period_id={test_period.id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) <= 1
    assert resp.headers.get("x-recommendations-teaser") == "1"
    assert "x-recommendations-total" in resp.headers


# ---------------------------------------------------------------------------
# /billing/subscription reflects entitlements (expiry-aware)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_subscription_endpoint_reports_expired_trial(
    client, test_session, test_org, test_user, auth_headers
):
    await _set_org_state(
        test_session,
        test_org,
        plan="professional",
        status="trialing",
        trial_delta_days=-1,
    )
    resp = await client.get("/api/billing/subscription", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["is_trialing"] is False
    assert body["is_expired"] is True
    assert body["plan"] == "free"


@pytest.mark.asyncio
async def test_subscription_endpoint_trial_shows_teaser_limits(
    client, test_session, test_org, test_user, auth_headers
):
    await _set_org_state(
        test_session,
        test_org,
        plan="professional",
        status="trialing",
        trial_delta_days=7,
    )
    resp = await client.get("/api/billing/subscription", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["is_trialing"] is True
    assert body["plan_limits"]["reports_per_month"] == 0
    assert body["plan_limits"]["import_files"] == 3


# ============================================================================
# Starter plan: full AI parser for Scope 1+2, Scope 3 commit-locked
# ============================================================================


async def test_starter_scope_gate_on_commit(
    test_session, test_org, test_user, test_period, seed_emission_factors
):
    from app.models.ingestion import IngestionSession, RowStatus, StagedRow
    from app.services.ingestion import orchestrator

    ing = IngestionSession(
        organization_id=test_org.id,
        created_by=test_user.id,
        reporting_period_id=test_period.id,
        filename="mixed.csv",
        file_size_bytes=10,
    )
    test_session.add(ing)
    await test_session.commit()
    await test_session.refresh(ing)

    s1 = StagedRow(
        session_id=ing.id,
        row_index=0,
        activity_key="electricity_kwh",
        scope=2,
        category_code="2",
        quantity=1000,
        unit="kWh",
        description="Electricity",
        status=RowStatus.APPROVED,
    )
    s3 = StagedRow(
        session_id=ing.id,
        row_index=1,
        activity_key="electricity_kwh",
        scope=3,
        category_code="3.6",
        quantity=500,
        unit="kWh",
        description="Value-chain row",
        status=RowStatus.APPROVED,
    )
    test_session.add(s1)
    test_session.add(s3)
    await test_session.commit()

    await orchestrator.commit_session(
        test_session, ing, reporting_period_id=test_period.id, allowed_scopes={1, 2}
    )
    await test_session.refresh(s1)
    await test_session.refresh(s3)

    assert s1.committed_activity_id is not None
    assert s3.committed_activity_id is None
    assert "Professional" in (s3.commit_error or "")


def test_starter_plan_promises_scope12_parser():
    from app.services.billing import PLAN_LIMITS
    from app.models.core import SubscriptionPlan

    starter = PLAN_LIMITS[SubscriptionPlan.STARTER]
    assert starter["smart_import_scopes"] == [1, 2]
    assert starter["ai_extractions"] == -1  # unlimited within its scopes
    assert "pdf" in starter["export_formats"]
    assert PLAN_LIMITS[SubscriptionPlan.PROFESSIONAL]["smart_import_scopes"] == [
        1,
        2,
        3,
    ]
