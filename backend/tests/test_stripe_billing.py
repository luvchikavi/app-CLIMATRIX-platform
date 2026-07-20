"""Stripe wiring for the restructured catalog (mocked — no live Stripe calls).

Covers the logic our code owns: which price a checkout selects, the shape of
the Checkout session we create, and how each webhook maps back onto the org
(subscription plan resolution + Report Pass stamping)."""

from datetime import datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.config import settings
from app.models.core import Organization, SubscriptionPlan
from app.services.billing import REPORT_PASS_DAYS, BillingService


@pytest.fixture(autouse=True)
def _price_ids(monkeypatch):
    """Deterministic price IDs so selection/reverse-map logic is testable."""
    monkeypatch.setattr(settings, "stripe_price_starter_monthly", "price_sm")
    monkeypatch.setattr(settings, "stripe_price_starter_annual", "price_sa")
    monkeypatch.setattr(settings, "stripe_price_professional_annual", "price_pa")
    monkeypatch.setattr(settings, "stripe_price_report_pass", "price_rp")
    monkeypatch.setattr(settings, "stripe_price_site_pack", "price_pack")
    monkeypatch.setattr(settings, "stripe_price_seat", "price_seat")
    monkeypatch.setattr(settings, "stripe_price_id_starter", "")
    monkeypatch.setattr(settings, "stripe_price_id_professional", "")
    monkeypatch.setattr(settings, "stripe_price_id_enterprise", "")


# ---------------------------------------------------------------------------
# price selection + reverse map (pure logic)
# ---------------------------------------------------------------------------


def test_subscription_price_selection():
    f = BillingService._subscription_price_id
    assert f(SubscriptionPlan.STARTER, "monthly") == "price_sm"
    assert f(SubscriptionPlan.STARTER, "annual") == "price_sa"
    assert f(SubscriptionPlan.PROFESSIONAL, "annual") == "price_pa"
    # Professional is annual-only — no monthly price exists.
    assert f(SubscriptionPlan.PROFESSIONAL, "monthly") is None


def test_price_to_plan_reverse_map():
    m = BillingService.price_to_plan()
    assert m["price_sm"] == SubscriptionPlan.STARTER
    assert m["price_sa"] == SubscriptionPlan.STARTER
    assert m["price_pa"] == SubscriptionPlan.PROFESSIONAL
    assert "" not in m  # empty price IDs never collide


# ---------------------------------------------------------------------------
# checkout session creation (stripe mocked)
# ---------------------------------------------------------------------------


def _org():
    return Organization(
        id=uuid4(),
        name="Billing Org",
        stripe_customer_id="cus_123",
        subscription_plan="free",
    )


@pytest.mark.asyncio
async def test_professional_checkout_uses_annual_price(monkeypatch, test_session):
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(url="https://checkout.test/pro")

    import app.services.billing as billing_mod

    monkeypatch.setattr(billing_mod.stripe.checkout.Session, "create", fake_create)

    org = _org()
    url = await BillingService.create_checkout_session(
        test_session,
        org,
        SubscriptionPlan.PROFESSIONAL,
        "https://ok",
        "https://cancel",
        cadence="annual",
    )
    assert url == "https://checkout.test/pro"
    assert captured["mode"] == "subscription"
    assert captured["line_items"][0]["price"] == "price_pa"
    assert captured["metadata"]["cadence"] == "annual"
    # First-time org (no prior trial) gets the 14-day trial.
    assert captured["subscription_data"]["trial_period_days"] == 14


@pytest.mark.asyncio
async def test_professional_monthly_rejected(monkeypatch, test_session):
    import app.services.billing as billing_mod

    monkeypatch.setattr(
        billing_mod.stripe.checkout.Session,
        "create",
        lambda **k: SimpleNamespace(url="x"),
    )
    with pytest.raises(ValueError, match="annual-only"):
        await BillingService.create_checkout_session(
            test_session,
            _org(),
            SubscriptionPlan.PROFESSIONAL,
            "https://ok",
            "https://cancel",
            cadence="monthly",
        )


@pytest.mark.asyncio
async def test_returning_customer_gets_no_second_trial(monkeypatch, test_session):
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(url="x")

    import app.services.billing as billing_mod

    monkeypatch.setattr(billing_mod.stripe.checkout.Session, "create", fake_create)

    org = _org()
    org.trial_ends_at = datetime.utcnow() - timedelta(days=30)  # already trialed
    await BillingService.create_checkout_session(
        test_session, org, SubscriptionPlan.STARTER, "https://ok", "https://x", "annual"
    )
    assert captured["subscription_data"] is None


@pytest.mark.asyncio
async def test_report_pass_checkout_is_one_time_with_year(monkeypatch, test_session):
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(url="https://checkout.test/pass")

    import app.services.billing as billing_mod

    monkeypatch.setattr(billing_mod.stripe.checkout.Session, "create", fake_create)

    url = await BillingService.create_report_pass_checkout(
        test_session, _org(), 2025, "https://ok", "https://cancel"
    )
    assert url == "https://checkout.test/pass"
    assert captured["mode"] == "payment"  # one-time, not subscription
    assert captured["line_items"][0]["price"] == "price_rp"
    assert captured["metadata"]["purchase"] == "report_pass"
    assert captured["metadata"]["report_year"] == "2025"


# ---------------------------------------------------------------------------
# webhook -> org field mapping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_webhook_report_pass_stamps_org(test_session):
    org = _org()
    org.trial_ends_at = datetime.utcnow() + timedelta(days=5)  # leftover trial
    test_session.add(org)
    await test_session.commit()

    checkout = SimpleNamespace(
        metadata={
            "organization_id": str(org.id),
            "purchase": "report_pass",
            "report_year": "2025",
        },
        customer="cus_123",
    )
    await BillingService.handle_checkout_completed(test_session, checkout)
    await test_session.refresh(org)

    assert org.subscription_plan == SubscriptionPlan.REPORT_PASS.value
    assert org.subscription_status == "active"
    assert org.licensed_report_year == 2025
    assert org.plan_expires_at is not None
    delta = org.plan_expires_at - datetime.utcnow()
    assert (
        timedelta(days=REPORT_PASS_DAYS - 1)
        < delta
        < timedelta(days=REPORT_PASS_DAYS + 1)
    )
    assert org.trial_ends_at is None  # a pass is not a trial


@pytest.mark.asyncio
async def test_webhook_subscription_updated_maps_price_to_plan(test_session):
    org = _org()
    test_session.add(org)
    await test_session.commit()

    subscription = SimpleNamespace(
        customer="cus_123",
        id="sub_1",
        status="active",
        current_period_end=int((datetime.utcnow() + timedelta(days=365)).timestamp()),
        items=SimpleNamespace(
            data=[SimpleNamespace(price=SimpleNamespace(id="price_pa"))]
        ),
    )
    await BillingService.handle_subscription_updated(test_session, subscription)
    await test_session.refresh(org)

    assert org.subscription_plan == SubscriptionPlan.PROFESSIONAL.value
    assert org.subscription_status == "active"
    assert org.stripe_subscription_id == "sub_1"


# ---------------------------------------------------------------------------
# API guards
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_checkout_endpoint_rejects_report_pass_plan(
    client, auth_headers, monkeypatch
):
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_x")
    resp = await client.post(
        "/api/billing/checkout",
        headers=auth_headers,
        json={
            "plan": "report_pass",
            "success_url": "https://ok",
            "cancel_url": "https://cancel",
        },
    )
    assert resp.status_code == 400
    assert "own checkout" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_report_pass_endpoint_503_without_stripe(
    client, auth_headers, monkeypatch
):
    monkeypatch.setattr(settings, "stripe_secret_key", "")
    resp = await client.post(
        "/api/billing/report-pass/checkout",
        headers=auth_headers,
        json={
            "report_year": 2025,
            "success_url": "https://ok",
            "cancel_url": "https://cancel",
        },
    )
    assert resp.status_code == 503
