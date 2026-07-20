"""Subscription restructure (2026-07-20): the reporting year is the unit sold.

- Tightened included caps: Starter 2 users / 2 sites, Professional 2 users /
  5 sites — growth is sold as add-ons (extra_users / extra_sites stack on top).
- Report Pass: one-time product, Professional features for a 90-day window,
  exports licensed to ONE reporting year; past the window -> FREE.
- Super-admin subscription PATCH: plan flips, add-on grants, pass issuance.
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

from app.models.core import Organization, ReportingPeriod, SubscriptionPlan
from app.services.billing import ADDON_PRICING, PLAN_LIMITS, PLAN_PRICING
from app.services.entitlements import resolve_entitlement


def _org(plan: str, status: str | None = "active", **kwargs):
    return Organization(
        id=uuid4(),
        name="Restructure Org",
        country_code="US",
        default_region="US",
        subscription_plan=plan,
        subscription_status=status,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# the new included caps
# ---------------------------------------------------------------------------


def test_new_included_caps():
    starter = PLAN_LIMITS[SubscriptionPlan.STARTER]
    assert starter["users"] == 2
    assert starter["sites"] == 2
    professional = PLAN_LIMITS[SubscriptionPlan.PROFESSIONAL]
    assert professional["users"] == 2
    assert professional["sites"] == 5


def test_professional_is_annual_only():
    pricing = PLAN_PRICING[SubscriptionPlan.PROFESSIONAL]
    assert pricing["monthly"] is None
    assert pricing["annual"] == 3560


def test_report_pass_pricing_and_addons():
    assert PLAN_PRICING[SubscriptionPlan.REPORT_PASS]["one_time"] == 1790
    assert ADDON_PRICING["site_pack_5"] == {"annual": 490, "sites": 5}
    assert ADDON_PRICING["extra_seat"] == {"annual": 190, "users": 1}


# ---------------------------------------------------------------------------
# add-on stacking
# ---------------------------------------------------------------------------


def test_extras_stack_on_paid_plan():
    ent = resolve_entitlement(_org("professional", extra_users=3, extra_sites=10))
    assert ent["limits"]["users"] == 2 + 3
    assert ent["limits"]["sites"] == 5 + 10


def test_extras_ignored_on_trial():
    org = _org("professional", status="trialing", extra_users=5, extra_sites=5)
    org.trial_ends_at = datetime.utcnow() + timedelta(days=7)
    ent = resolve_entitlement(org)
    assert ent["is_trialing"] is True
    assert ent["limits"]["users"] == 1  # teaser stays single-seat
    assert ent["limits"]["sites"] == 1


def test_extras_ignored_on_free():
    ent = resolve_entitlement(_org("free", status=None, extra_users=5, extra_sites=5))
    assert ent["limits"]["users"] == 1
    assert ent["limits"]["sites"] == 1


# ---------------------------------------------------------------------------
# Report Pass lifecycle
# ---------------------------------------------------------------------------


def test_report_pass_active_window():
    org = _org(
        "report_pass",
        licensed_report_year=2025,
        plan_expires_at=datetime.utcnow() + timedelta(days=30),
    )
    ent = resolve_entitlement(org)
    assert ent["effective_plan"] == "report_pass"
    assert ent["licensed_report_year"] == 2025
    # Professional-level capability inside the window
    assert ent["limits"]["reports_per_month"] == -1
    assert ent["limits"]["smart_import_scopes"] == [1, 2, 3]


def test_report_pass_expired_window_falls_back_to_free():
    org = _org(
        "report_pass",
        licensed_report_year=2025,
        plan_expires_at=datetime.utcnow() - timedelta(days=1),
    )
    ent = resolve_entitlement(org)
    assert ent["effective_plan"] == "free"
    assert ent["is_expired"] is True
    assert ent["licensed_report_year"] is None


def test_report_pass_without_expiry_is_closed():
    ent = resolve_entitlement(_org("report_pass", licensed_report_year=2025))
    assert ent["effective_plan"] == "free"


def test_full_subscription_has_no_year_license():
    ent = resolve_entitlement(_org("professional"))
    assert ent["licensed_report_year"] is None


# ---------------------------------------------------------------------------
# year-gated exports over HTTP
# ---------------------------------------------------------------------------


async def _grant_report_pass(test_session, org, year: int):
    org.subscription_plan = "report_pass"
    org.subscription_status = "active"
    org.trial_ends_at = None
    org.licensed_report_year = year
    org.plan_expires_at = datetime.utcnow() + timedelta(days=90)
    test_session.add(org)
    await test_session.commit()


@pytest.mark.asyncio
async def test_report_pass_exports_licensed_year_only(
    client, test_session, test_org, test_user, test_period, auth_headers
):
    """test_period is FY2025; a 2025 pass exports it, a 2024 period is 402."""
    other_period = ReportingPeriod(
        id=uuid4(),
        organization_id=test_org.id,
        name="FY2024",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )
    test_session.add(other_period)
    await test_session.commit()
    await _grant_report_pass(test_session, test_org, 2025)

    licensed = await client.get(
        f"/api/reports/export/csv?period_id={test_period.id}", headers=auth_headers
    )
    assert licensed.status_code != 402, licensed.text

    for url in (
        f"/api/reports/export/csv?period_id={other_period.id}",
        f"/api/periods/{other_period.id}/export/cdp",
        f"/api/periods/{other_period.id}/report/audit-package",
    ):
        resp = await client.get(url, headers=auth_headers)
        assert resp.status_code == 402, f"{url} -> {resp.status_code}"
        detail = resp.json()["detail"]
        assert detail["limit_type"] == "report_pass_year"
        assert "2025" in detail["message"]


@pytest.mark.asyncio
async def test_annual_subscriber_exports_any_year(
    client, test_session, test_org, test_user, auth_headers
):
    old_period = ReportingPeriod(
        id=uuid4(),
        organization_id=test_org.id,
        name="FY2023",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
    )
    test_session.add(old_period)
    await test_session.commit()
    resp = await client.get(
        f"/api/reports/export/csv?period_id={old_period.id}", headers=auth_headers
    )
    assert resp.status_code != 402, resp.text


# ---------------------------------------------------------------------------
# tightened capacity enforcement over HTTP
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_starter_site_cap_and_addon_relief(
    client, test_session, test_org, test_user, auth_headers
):
    test_org.subscription_plan = "starter"
    test_org.subscription_status = "active"
    test_session.add(test_org)
    await test_session.commit()

    async def create_site(name):
        return await client.post(
            "/api/organization/sites", headers=auth_headers, json={"name": name}
        )

    assert (await create_site("Site 1")).status_code == 200
    assert (await create_site("Site 2")).status_code == 200
    blocked = await create_site("Site 3")
    assert blocked.status_code == 402
    assert blocked.json()["detail"]["limit_type"] == "sites"

    # A granted site pack lifts the cap without a plan change.
    test_org.extra_sites = 5
    test_session.add(test_org)
    await test_session.commit()
    assert (await create_site("Site 3")).status_code == 200


# ---------------------------------------------------------------------------
# super-admin subscription management
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_subscription_patch(client, test_session, test_org, admin_headers):
    resp = await client.patch(
        f"/api/admin/organizations/{test_org.id}/subscription",
        headers=admin_headers,
        json={
            "plan": "report_pass",
            "status": "active",
            "extra_sites": 5,
            "licensed_report_year": 2025,
            "plan_expires_at": (datetime.utcnow() + timedelta(days=90)).isoformat(),
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["plan"] == "report_pass"
    assert body["extra_sites"] == 5
    assert body["licensed_report_year"] == 2025

    # The change lands in the audit trail.
    from sqlmodel import select

    from app.models.core import AuditLog

    logs = (
        (
            await test_session.execute(
                select(AuditLog).where(
                    AuditLog.organization_id == test_org.id,
                    AuditLog.resource_type == "subscription",
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_admin_subscription_patch_rejects_invalid_plan(
    client, test_org, admin_headers
):
    resp = await client.patch(
        f"/api/admin/organizations/{test_org.id}/subscription",
        headers=admin_headers,
        json={"plan": "platinum"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_admin_subscription_patch_requires_super_admin(
    client, test_org, auth_headers
):
    resp = await client.patch(
        f"/api/admin/organizations/{test_org.id}/subscription",
        headers=auth_headers,
        json={"extra_sites": 5},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# plans endpoint carries the new structure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_plans_endpoint_new_structure(client, auth_headers):
    resp = await client.get("/api/billing/plans", headers=auth_headers)
    assert resp.status_code == 200
    plans = {p["id"]: p for p in resp.json()["plans"]}
    assert plans["professional"]["price_monthly"] is None
    assert plans["professional"]["price_annual"] == 3560
    assert plans["report_pass"]["price_one_time"] == 1790
