"""
Tests for the CBAM certificate ledger + 50% quarterly holding schedule.

Covers:
- pure service math: ledger summary, weighted average purchase price,
  running-balance validation, quarterly schedule (ceil of 50%, statuses),
  2026 not-applicable behaviour, milestones
- ledger endpoints: create/list/delete with the never-negative guard,
  entry_type validation, org scoping
- summary endpoint: schedule built from the imports register, declaration
  linkage, 2026 messaging
"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import cbam_certificates as svc

pytestmark = pytest.mark.asyncio


def _entry(entry_type, quantity, entry_date, unit_price=None):
    return SimpleNamespace(
        entry_date=entry_date,
        entry_type=entry_type,
        quantity=quantity,
        unit_price_eur=Decimal(str(unit_price)) if unit_price is not None else None,
        total_eur=(
            Decimal(str(unit_price)) * quantity if unit_price is not None else None
        ),
    )


# ============================================================================
# Service: ledger summary + balance guard
# ============================================================================


async def test_ledger_summary_totals_and_weighted_average():
    entries = [
        _entry("purchase", 100, date(2027, 2, 10), unit_price=80),
        _entry("purchase", 50, date(2027, 3, 10), unit_price=90),
        _entry("surrender", 60, date(2027, 9, 20)),
        _entry("repurchase", 10, date(2027, 10, 5), unit_price=80),
    ]
    summary = svc.ledger_summary(entries)

    assert summary["balance"] == 80  # 150 - 60 - 10
    assert summary["purchased"] == 150
    assert summary["surrendered"] == 60
    assert summary["repurchased"] == 10
    assert summary["total_spent_eur"] == Decimal("12500.00")  # 8000 + 4500
    assert summary["total_repurchased_eur"] == Decimal("800.00")
    # (100*80 + 50*90) / 150
    assert summary["weighted_avg_purchase_price_eur"] == Decimal("83.33")


async def test_ledger_summary_no_priced_purchases_has_no_average():
    summary = svc.ledger_summary([_entry("purchase", 10, date(2027, 2, 1))])
    assert summary["weighted_avg_purchase_price_eur"] is None
    assert summary["total_spent_eur"] == Decimal("0.00")


async def test_running_balance_never_negative():
    ok = [
        _entry("purchase", 100, date(2027, 2, 1)),
        _entry("surrender", 100, date(2027, 9, 1)),
    ]
    assert svc.running_balance_violation(ok) is None

    bad = [
        _entry("purchase", 50, date(2027, 2, 1)),
        _entry("surrender", 60, date(2027, 9, 1)),
    ]
    assert "negative" in svc.running_balance_violation(bad)

    # A surrender dated BEFORE the purchase is also caught.
    out_of_order = [
        _entry("purchase", 100, date(2027, 6, 1)),
        _entry("surrender", 40, date(2027, 3, 1)),
    ]
    assert svc.running_balance_violation(out_of_order) is not None

    # Same-day purchase + surrender nets out fine.
    same_day = [
        _entry("surrender", 30, date(2027, 5, 1)),
        _entry("purchase", 30, date(2027, 5, 1)),
    ]
    assert svc.running_balance_violation(same_day) is None


# ============================================================================
# Service: quarterly holding schedule
# ============================================================================


async def test_holding_schedule_ceils_half_of_cumulative_emissions():
    line_emissions = [
        (date(2027, 2, 15), Decimal("101")),  # Q1
        (date(2027, 5, 10), Decimal("100")),  # Q2
    ]
    entries = [_entry("purchase", 51, date(2027, 3, 1))]

    schedule = svc.quarterly_holding_schedule(
        2027, line_emissions, entries, Decimal("80"), today=date(2027, 7, 1)
    )
    assert schedule["applies"] is True
    q1, q2, q3, q4 = schedule["quarters"]

    # Q1: cum 101 -> 50% = 50.5 -> ceil 51; held 51 -> met
    assert q1["required_certificates"] == 51
    assert q1["held_certificates"] == 51
    assert q1["shortfall"] == 0
    assert q1["status"] == "met"

    # Q2: cum 201 -> ceil(100.5) = 101; held 51 -> short 50 -> 50 x €80
    assert q2["required_certificates"] == 101
    assert q2["shortfall"] == 50
    assert q2["estimated_topup_cost_eur"] == Decimal("4000.00")
    assert q2["status"] == "shortfall"

    # Q3 is the current quarter (today 2027-07-01) -> live status
    assert q3["status"] == "shortfall"
    # Q4 is in the future
    assert q4["status"] == "upcoming"


async def test_holding_schedule_not_applicable_before_2027():
    schedule = svc.quarterly_holding_schedule(
        2026,
        [(date(2026, 2, 1), Decimal("500"))],
        [],
        Decimal("75"),
        today=date(2026, 7, 12),
    )
    assert schedule["applies"] is False
    assert all(q["status"] == "not_applicable" for q in schedule["quarters"])
    assert all(q["required_certificates"] == 0 for q in schedule["quarters"])
    # Cumulative emissions still shown for planning
    assert schedule["quarters"][3]["cumulative_emissions_tco2e"] == Decimal("500.000")


async def test_milestones_for_2026_include_sales_open_and_deadlines():
    items = svc.milestones(2026, today=date(2027, 3, 1))
    labels = " | ".join(m["label"] for m in items)
    assert "sales open" in labels
    dates = [m["date"] for m in items]
    assert date(2027, 2, 1) in dates  # sales open
    assert date(2027, 9, 30) in dates  # declaration + surrender
    assert date(2027, 10, 31) in dates  # repurchase request deadline
    passed = {m["date"]: m["passed"] for m in items}
    assert passed[date(2027, 2, 1)] is True
    assert passed[date(2027, 9, 30)] is False


# ============================================================================
# API: ledger CRUD
# ============================================================================


async def _post_entry(client, auth_headers, **overrides):
    payload = {
        "entry_date": "2027-02-15",
        "entry_type": "purchase",
        "quantity": 100,
        "unit_price_eur": 82.5,
    }
    payload.update(overrides)
    return await client.post(
        "/api/cbam/certificates", json=payload, headers=auth_headers
    )


async def test_create_and_list_certificate_entries(client, auth_headers):
    resp = await _post_entry(client, auth_headers)
    assert resp.status_code == 200, resp.text
    entry = resp.json()
    assert entry["entry_type"] == "purchase"
    assert float(entry["total_eur"]) == pytest.approx(8250.0)

    resp = await client.get("/api/cbam/certificates", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_create_entry_rejects_unknown_type(client, auth_headers):
    resp = await _post_entry(client, auth_headers, entry_type="gift")
    assert resp.status_code == 422
    assert "entry_type" in resp.json()["detail"]


async def test_surrender_cannot_exceed_holdings(client, auth_headers):
    resp = await _post_entry(client, auth_headers, quantity=50)
    assert resp.status_code == 200

    resp = await _post_entry(
        client,
        auth_headers,
        entry_type="surrender",
        entry_date="2027-09-20",
        quantity=60,
        unit_price_eur=None,
    )
    assert resp.status_code == 422
    assert "negative" in resp.json()["detail"]


async def test_delete_entry_guards_dependent_surrenders(client, auth_headers):
    purchase = (await _post_entry(client, auth_headers, quantity=100)).json()
    resp = await _post_entry(
        client,
        auth_headers,
        entry_type="surrender",
        entry_date="2027-09-20",
        quantity=80,
        unit_price_eur=None,
    )
    assert resp.status_code == 200
    surrender = resp.json()

    # Deleting the purchase would strand the surrender -> 422
    resp = await client.delete(
        f"/api/cbam/certificates/{purchase['id']}", headers=auth_headers
    )
    assert resp.status_code == 422

    # Deleting the surrender first is fine, then the purchase too.
    resp = await client.delete(
        f"/api/cbam/certificates/{surrender['id']}", headers=auth_headers
    )
    assert resp.status_code == 200
    resp = await client.delete(
        f"/api/cbam/certificates/{purchase['id']}", headers=auth_headers
    )
    assert resp.status_code == 200


async def test_delete_missing_entry_404(client, auth_headers):
    resp = await client.delete(
        f"/api/cbam/certificates/{uuid4()}", headers=auth_headers
    )
    assert resp.status_code == 404


async def test_certificates_are_org_scoped(client, auth_headers, test_session):
    """A user from another org must not see this org's ledger."""
    from datetime import timedelta as td

    from app.api.auth import create_access_token, get_password_hash
    from app.models.core import Organization, User, UserRole

    await _post_entry(client, auth_headers)

    other_org = Organization(id=uuid4(), name="Other Org")
    other_user = User(
        id=uuid4(),
        email="other-org@example.com",
        hashed_password=get_password_hash("otherpassword123"),
        full_name="Other Org User",
        organization_id=other_org.id,
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(other_org)
    test_session.add(other_user)
    await test_session.commit()

    token = create_access_token(
        data={
            "sub": str(other_user.id),
            "org_id": str(other_user.organization_id),
            "role": other_user.role.value,
        },
        expires_delta=td(hours=1),
    )
    other_headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/cbam/certificates", headers=other_headers)
    assert resp.status_code == 200
    assert resp.json() == []


# ============================================================================
# API: summary + holding schedule
# ============================================================================


async def _create_import(client, auth_headers, **overrides):
    payload = {
        "cn_code": "72081000",
        "product_description": "Hot-rolled steel coil",
        "import_date": "2027-03-15",
        "mass_tonnes": 100,
        "origin_country": "TR",
        "actual_direct_see": 2.0,
        "actual_indirect_see": 0.5,
    }
    payload.update(overrides)
    resp = await client.post("/api/cbam/imports", json=payload, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_summary_builds_schedule_from_imports(client, auth_headers):
    # 100 t x 2.5 tCO2e/t actual = 250 tCO2e in Q1 2027
    await _create_import(client, auth_headers)
    await _post_entry(client, auth_headers, entry_date="2027-03-01", quantity=100)

    resp = await client.get("/api/cbam/certificates/summary/2027", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["holding_rule_applies"] is True
    assert data["balance"] == 100
    q1 = data["holding_schedule"][0]
    # ceil(250 * 0.5) = 125 required; 100 held -> 25 short
    assert q1["required_certificates"] == 125
    assert q1["held_certificates"] == 100
    assert q1["shortfall"] == 25
    # No declaration generated yet
    assert data["certificates_required"] is None
    assert len(data["milestones"]) == 2  # no sales-open row for 2027
    assert data["assumptions"]


async def test_summary_2026_marks_rule_not_applicable(client, auth_headers):
    await _create_import(client, auth_headers, import_date="2026-03-15")

    resp = await client.get("/api/cbam/certificates/summary/2026", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["holding_rule_applies"] is False
    assert all(q["status"] == "not_applicable" for q in data["holding_schedule"])
    assert any("1 Feb 2027" in a or "2027" in a for a in data["assumptions"])
    assert len(data["milestones"]) == 3  # sales open + declaration + repurchase


async def test_summary_links_generated_declaration(client, auth_headers):
    await _create_import(client, auth_headers, import_date="2026-03-15")
    resp = await client.post("/api/cbam/reports/annual/2026", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    declared = resp.json()

    resp = await client.get("/api/cbam/certificates/summary/2026", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    # The declaration endpoint serializes counts as strings; ours is an int.
    assert data["certificates_required"] == int(declared["certificates_required"])
    assert data["declaration_status"] == "draft"


async def test_summary_rejects_pre_2026(client, auth_headers):
    resp = await client.get("/api/cbam/certificates/summary/2025", headers=auth_headers)
    assert resp.status_code == 400
