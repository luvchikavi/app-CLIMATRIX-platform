"""
Tests for the CBAM Phase 3 supplier portal.

Covers:
- creating a supplier data request (magic-link email logged in dev mode)
- org-scoped listing with status
- public GET of the request context by token (404 unknown)
- public POST of per-CN-code SEE rows, incl. idempotent re-submission
  (replaces rows) and validation errors
- expiry: 410 on GET and POST once expires_at has passed
- annual declaration preferring supplier-submitted actuals over Commission
  default values (no markup) — arithmetic asserted
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def _email_dev_mode(monkeypatch):
    """Force the email service into dev mode (log, never send) for all tests
    here — the local env may carry real SMTP credentials."""
    from app.services.email import email_service

    monkeypatch.setattr(email_service, "host", None)


# ============================================================================
# Helpers
# ============================================================================


async def _create_installation(client, auth_headers, **overrides):
    payload = {
        "name": "Izmir Steel Works",
        "country_code": "TR",
        "address": "Izmir Industrial Zone",
        "contact_email": "ops@izmirsteel.example",
        "sectors": ["iron_steel"],
    }
    payload.update(overrides)
    resp = await client.post(
        "/api/cbam/installations", json=payload, headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _create_request(client, auth_headers, installation_id, **overrides):
    payload = {
        "installation_id": installation_id,
        "supplier_email": "operator@izmirsteel.example",
        "message": "Please provide 2026 production data for our declaration.",
    }
    payload.update(overrides)
    resp = await client.post(
        "/api/cbam/data-requests", json=payload, headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _rows_payload():
    return {
        "rows": [
            {
                "cn_code": "7208",
                "direct_see_tco2e_per_t": 1.5,
                "indirect_see_tco2e_per_t": 0.3,
                "production_period_start": "2026-01-01",
                "production_period_end": "2026-06-30",
                "verifier_name": "TUV Verify GmbH",
                "verified": True,
            },
            {
                "cn_code": "7210",
                "direct_see_tco2e_per_t": 1.9,
                "indirect_see_tco2e_per_t": None,
                "production_period_start": "2026-01-01",
                "production_period_end": "2026-06-30",
                "verified": False,
            },
        ]
    }


async def _seed_default_value(
    test_session, cn_code="72081000", country="TR", see="2.0"
):
    from app.models.cbam import CBAMDefaultValue, CBAMSector

    row = CBAMDefaultValue(
        id=uuid4(),
        cn_code=cn_code,
        sector=CBAMSector.IRON_STEEL,
        product_description="Hot-rolled steel",
        country_code=country,
        dataset_year=2026,
        dataset_version="13-Feb-2026",
        direct_see=Decimal(see),
        total_see=Decimal(see),
        source="EU Commission definitive default values (13 Feb 2026)",
        valid_from=date(2026, 1, 1),
    )
    test_session.add(row)
    await test_session.commit()
    return row


async def _set_ets_price(client, auth_headers, price=80.0, price_date="2026-07-01"):
    resp = await client.put(
        "/api/cbam/ets-price",
        json={"price_date": price_date, "price_eur": price},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text


async def _expire_request(test_session, request_id):
    from uuid import UUID
    from app.models.cbam import CBAMDataRequest
    from sqlmodel import select

    result = await test_session.execute(
        select(CBAMDataRequest).where(CBAMDataRequest.id == UUID(request_id))
    )
    req = result.scalar_one()
    req.expires_at = datetime.utcnow() - timedelta(days=1)
    await test_session.commit()


# ============================================================================
# Create + list (importer side)
# ============================================================================


async def test_create_data_request_sends_email_and_lists(client, auth_headers, caplog):
    installation = await _create_installation(client, auth_headers)

    with caplog.at_level(logging.INFO, logger="app.services.email"):
        req = await _create_request(client, auth_headers, installation["id"])

    assert req["status"] == "pending"
    assert req["installation_name"] == "Izmir Steel Works"
    assert req["installation_country"] == "TR"
    assert req["supplier_email"] == "operator@izmirsteel.example"
    assert req["token"]
    assert req["supplier_portal_url"].endswith(f"/supplier-data/{req['token']}")
    assert req["rows"] == []

    # ~60-day expiry window
    expires = datetime.fromisoformat(req["expires_at"])
    created = datetime.fromisoformat(req["created_at"])
    assert 59 <= (expires - created).days <= 60

    # Email not configured in tests -> logged in dev mode, addressed to supplier
    email_log = " ".join(r.getMessage() for r in caplog.records)
    assert "operator@izmirsteel.example" in email_log
    assert "CBAM" in email_log

    # Org-scoped list with status filter
    resp = await client.get(
        "/api/cbam/data-requests?status=pending", headers=auth_headers
    )
    assert resp.status_code == 200
    listed = resp.json()
    assert len(listed) == 1
    assert listed[0]["id"] == req["id"]

    resp = await client.get(
        "/api/cbam/data-requests?status=submitted", headers=auth_headers
    )
    assert resp.json() == []


async def test_create_request_unknown_installation_404(client, auth_headers):
    resp = await client.post(
        "/api/cbam/data-requests",
        json={
            "installation_id": str(uuid4()),
            "supplier_email": "someone@example.com",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_remind_resends_email(client, auth_headers, caplog):
    installation = await _create_installation(client, auth_headers)
    req = await _create_request(client, auth_headers, installation["id"])

    with caplog.at_level(logging.INFO, logger="app.services.email"):
        resp = await client.post(
            f"/api/cbam/data-requests/{req['id']}/remind", headers=auth_headers
        )
    assert resp.status_code == 200, resp.text
    email_log = " ".join(r.getMessage() for r in caplog.records)
    assert "operator@izmirsteel.example" in email_log


# ============================================================================
# Public magic-link endpoints (no auth)
# ============================================================================


async def test_public_get_context(client, auth_headers):
    installation = await _create_installation(client, auth_headers)
    req = await _create_request(client, auth_headers, installation["id"])

    # No Authorization header — public
    resp = await client.get(f"/api/cbam/supplier-data/{req['token']}")
    assert resp.status_code == 200, resp.text
    ctx = resp.json()
    assert ctx["importer_org_name"] == "Test Organization"
    assert ctx["installation_name"] == "Izmir Steel Works"
    assert ctx["installation_country"] == "TR"
    assert ctx["status"] == "pending"
    assert ctx["rows"] == []


async def test_public_get_unknown_token_404(client):
    resp = await client.get("/api/cbam/supplier-data/not-a-real-token")
    assert resp.status_code == 404


async def test_public_submit_and_idempotent_replace(client, auth_headers):
    installation = await _create_installation(client, auth_headers)
    req = await _create_request(client, auth_headers, installation["id"])
    token = req["token"]

    # First submission: two rows
    resp = await client.post(f"/api/cbam/supplier-data/{token}", json=_rows_payload())
    assert resp.status_code == 200, resp.text
    ctx = resp.json()
    assert ctx["status"] == "submitted"
    assert ctx["submitted_at"] is not None
    assert len(ctx["rows"]) == 2
    by_cn = {r["cn_code"]: r for r in ctx["rows"]}
    assert float(by_cn["7208"]["direct_see_tco2e_per_t"]) == pytest.approx(1.5)
    assert by_cn["7208"]["verified"] is True
    assert by_cn["7210"]["indirect_see_tco2e_per_t"] is None

    # Re-submission replaces rows wholesale (idempotent while not expired)
    replacement = {
        "rows": [
            {
                "cn_code": "7208",
                "direct_see_tco2e_per_t": 1.4,
                "indirect_see_tco2e_per_t": 0.2,
                "production_period_start": "2026-01-01",
                "production_period_end": "2026-12-31",
                "verified": False,
            }
        ]
    }
    resp = await client.post(f"/api/cbam/supplier-data/{token}", json=replacement)
    assert resp.status_code == 200, resp.text
    ctx = resp.json()
    assert ctx["status"] == "submitted"
    assert len(ctx["rows"]) == 1
    assert float(ctx["rows"][0]["direct_see_tco2e_per_t"]) == pytest.approx(1.4)

    # Importer-side list shows submitted values
    resp = await client.get("/api/cbam/data-requests", headers=auth_headers)
    listed = resp.json()
    assert listed[0]["status"] == "submitted"
    assert len(listed[0]["rows"]) == 1


async def test_public_submit_validation(client, auth_headers):
    installation = await _create_installation(client, auth_headers)
    req = await _create_request(client, auth_headers, installation["id"])
    token = req["token"]

    # Negative direct SEE -> 422 (pydantic ge=0)
    bad = _rows_payload()
    bad["rows"][0]["direct_see_tco2e_per_t"] = -1
    resp = await client.post(f"/api/cbam/supplier-data/{token}", json=bad)
    assert resp.status_code == 422

    # Period end before start -> 422
    bad = _rows_payload()
    bad["rows"][0]["production_period_end"] = "2025-01-01"
    resp = await client.post(f"/api/cbam/supplier-data/{token}", json=bad)
    assert resp.status_code == 422

    # Empty rows -> 422
    resp = await client.post(f"/api/cbam/supplier-data/{token}", json={"rows": []})
    assert resp.status_code == 422


async def test_expired_link_returns_410(client, auth_headers, test_session):
    installation = await _create_installation(client, auth_headers)
    req = await _create_request(client, auth_headers, installation["id"])
    await _expire_request(test_session, req["id"])

    resp = await client.get(f"/api/cbam/supplier-data/{req['token']}")
    assert resp.status_code == 410

    resp = await client.post(
        f"/api/cbam/supplier-data/{req['token']}", json=_rows_payload()
    )
    assert resp.status_code == 410

    # Importer list reflects the expiry
    resp = await client.get("/api/cbam/data-requests", headers=auth_headers)
    assert resp.json()[0]["status"] == "expired"


# ============================================================================
# Declaration integration — supplier actuals beat defaults, no markup
# ============================================================================


async def test_declaration_prefers_supplier_actuals_over_defaults(
    client, auth_headers, test_session
):
    """
    Import: 100 t of CN 72081000 from installation in TR.

    Without supplier data the line would use the DB default:
      2.0 SEE x (1 + 10% markup) x 100 t = 220 tCO2e.
    With the supplier-submitted row (CN prefix 7208, direct 1.5 +
    indirect 0.3 = 1.8 SEE, verified) the line must be:
      1.8 x 100 t = 180 tCO2e, NO markup, cost 180 x €80 = €14,400.
    """
    await _seed_default_value(test_session)
    await _set_ets_price(client, auth_headers)

    installation = await _create_installation(client, auth_headers)
    resp = await client.post(
        "/api/cbam/imports",
        json={
            "installation_id": installation["id"],
            "cn_code": "72081000",
            "product_description": "Hot-rolled steel coil",
            "import_date": "2026-03-15",
            "mass_tonnes": 100,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text

    # Baseline: declaration built on defaults carries the 10% markup
    resp = await client.post("/api/cbam/reports/annual/2026", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    baseline_line = resp.json()["lines"][0]
    assert baseline_line["intensity_source"] == "default"
    assert float(baseline_line["emissions_tco2e"]) == pytest.approx(220.0)
    assert float(baseline_line["markup_pct"]) == pytest.approx(10.0)

    # Supplier submits actuals via the magic link
    req = await _create_request(client, auth_headers, installation["id"])
    resp = await client.post(
        f"/api/cbam/supplier-data/{req['token']}", json=_rows_payload()
    )
    assert resp.status_code == 200, resp.text

    # Regenerate: the supplier row (CN prefix 7208) must now win, no markup
    resp = await client.post("/api/cbam/reports/annual/2026", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    line = data["lines"][0]
    assert line["intensity_source"] == "actual (supplier)"
    assert float(line["see_tco2e_per_tonne"]) == pytest.approx(1.8)
    assert float(line["markup_pct"]) == pytest.approx(0.0)
    assert float(line["emissions_tco2e"]) == pytest.approx(180.0)
    assert float(line["estimated_cost_eur"]) == pytest.approx(14400.0)
    assert "Izmir Steel Works" in line["intensity_source_detail"]
    assert "verified" in line["intensity_source_detail"]

    # Totals and data quality follow
    assert float(data["gross_emissions_tco2e"]) == pytest.approx(180.0)
    assert data["data_quality"]["supplier_lines"] == 1
    assert data["data_quality"]["actual_lines"] == 1
    assert data["data_quality"]["default_lines"] == 0
    assert any("supplier portal" in a for a in data["assumptions"])
