"""
Tests for the CBAM Phase 1 endpoint fixes.

Covers:
- imports/installations CRUD against the real model fields (the old code
  read attributes that did not exist and raised AttributeError at runtime)
- annual declaration generate/list (definitive regime, 30 Sep deadline)
- quarterly create/submit retired with 410 (transitional period ended
  31 Dec 2025); GET history endpoints still work
- Registry XML exports on hold with 501
- EU ETS price endpoints (latest/refresh/manual upsert) incl. admin gating
"""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

pytestmark = pytest.mark.asyncio


# ============================================================================
# Fixtures / helpers
# ============================================================================


@pytest.fixture
async def viewer_headers(test_session, test_org):
    """Auth headers for a non-admin (viewer) user."""
    from datetime import timedelta as td

    from app.api.auth import create_access_token, get_password_hash
    from app.models.core import User, UserRole

    user = User(
        id=uuid4(),
        email="viewer@example.com",
        hashed_password=get_password_hash("viewerpassword123"),
        full_name="Viewer User",
        organization_id=test_org.id,
        role=UserRole.VIEWER,
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()

    token = create_access_token(
        data={
            "sub": str(user.id),
            "org_id": str(user.organization_id),
            "role": user.role.value,
        },
        expires_delta=td(hours=1),
    )
    return {"Authorization": f"Bearer {token}"}


async def _create_installation(client, auth_headers, **overrides):
    payload = {
        "name": "Test Steel Plant",
        "country_code": "TR",
        "address": "Industrial Zone 1",
        "sectors": ["iron_steel"],
        "verification_status": "pending",
    }
    payload.update(overrides)
    resp = await client.post(
        "/api/cbam/installations", json=payload, headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _create_import(client, auth_headers, **overrides):
    payload = {
        "cn_code": "72081000",
        "product_description": "Hot-rolled steel coil",
        "import_date": "2026-03-15",
        "mass_tonnes": 100,
        "origin_country": "TR",
        "actual_direct_see": 2.0,
        "actual_indirect_see": 0.5,
    }
    payload.update(overrides)
    resp = await client.post("/api/cbam/imports", json=payload, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ============================================================================
# Installations
# ============================================================================


async def test_installations_sector_filter_uses_model_field(client, auth_headers):
    """The old code filtered on inst.sectors, which doesn't exist."""
    await _create_installation(client, auth_headers, sectors=["iron_steel"])
    await _create_installation(
        client, auth_headers, name="Cement Works", sectors=["cement"]
    )

    resp = await client.get(
        "/api/cbam/installations?sector=iron_steel", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data) == 1
    assert data[0]["sectors"] == ["iron_steel"]


# ============================================================================
# Imports
# ============================================================================


async def test_create_import_without_installation(client, auth_headers):
    """Installation is optional; origin_country drives the calculation."""
    imp = await _create_import(client, auth_headers)
    assert imp["origin_country"] == "TR"
    assert imp["installation_id"] == ""
    assert float(imp["mass_kg"]) == pytest.approx(100000.0)
    # actual SEE 2.0 + 0.5 over 100 t
    assert float(imp["total_emissions_tco2e"]) == pytest.approx(250.0)
    assert imp["calculation_method"] == "actual"


async def test_create_import_requires_origin_when_no_installation(client, auth_headers):
    resp = await client.post(
        "/api/cbam/imports",
        json={
            "cn_code": "72081000",
            "import_date": "2026-03-15",
            "mass_tonnes": 10,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_create_import_with_installation_and_carbon_price(client, auth_headers):
    """The old code passed foreign_carbon_price_eur= to the model (no such
    column) and read imp.foreign_carbon_price_eur back."""
    inst = await _create_installation(client, auth_headers)
    imp = await _create_import(
        client,
        auth_headers,
        installation_id=inst["id"],
        origin_country=None,
        foreign_carbon_price_eur=12.5,
    )
    assert imp["installation_id"] == inst["id"]
    assert imp["origin_country"] == "TR"  # from installation
    assert float(imp["foreign_carbon_price_eur"]) == 12.5

    # And the list endpoint round-trips without AttributeError
    resp = await client.get("/api/cbam/imports", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 1


# ============================================================================
# Annual declarations (definitive regime)
# ============================================================================


async def test_generate_annual_declaration_2026(client, auth_headers, test_session):
    """The old endpoint read/wrote ~8 nonexistent model fields."""
    await _create_import(client, auth_headers, mass_tonnes=100)

    resp = await client.post("/api/cbam/reports/annual/2026", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["year"] == 2026
    assert data["total_imports"] == 1
    assert float(data["total_mass_tonnes"]) == pytest.approx(100.0)
    assert float(data["gross_emissions_tco2e"]) == pytest.approx(250.0)
    assert float(data["net_emissions_tco2e"]) == pytest.approx(250.0)
    assert float(data["certificates_required"]) == pytest.approx(250.0)
    assert float(data["estimated_cost_eur"]) > 0
    assert "iron_steel" in data["by_sector"]

    # Deadline stored per Omnibus: 30 September of the following year
    from sqlmodel import select

    from app.models.cbam import CBAMAnnualDeclaration

    row = (await test_session.execute(select(CBAMAnnualDeclaration))).scalars().one()
    assert row.submission_deadline == date(2027, 9, 30)

    # Regeneration updates in place
    resp2 = await client.post("/api/cbam/reports/annual/2026", headers=auth_headers)
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["id"] == data["id"]

    # And the list endpoint works
    resp3 = await client.get("/api/cbam/reports/annual", headers=auth_headers)
    assert resp3.status_code == 200, resp3.text
    assert len(resp3.json()) == 1


async def test_generate_annual_declaration_rejects_pre_2026(client, auth_headers):
    resp = await client.post("/api/cbam/reports/annual/2025", headers=auth_headers)
    assert resp.status_code == 400


async def test_annual_xml_export_on_hold_501(client, auth_headers):
    resp = await client.get(
        "/api/cbam/reports/annual/2026/export/xml", headers=auth_headers
    )
    assert resp.status_code == 501
    assert "CBAM Registry" in resp.json()["detail"]


# ============================================================================
# Quarterly reports (retired transitional period)
# ============================================================================


async def test_quarterly_generate_and_submit_are_gone(client, auth_headers):
    resp = await client.post("/api/cbam/reports/quarterly/2025/4", headers=auth_headers)
    assert resp.status_code == 410
    assert "transitional period" in resp.json()["detail"]

    resp = await client.post(
        "/api/cbam/reports/quarterly/2025/4/submit", headers=auth_headers
    )
    assert resp.status_code == 410


async def _seed_quarterly_report(test_session, org_id):
    from app.models.cbam import CBAMQuarterlyReport, CBAMReportStatus

    report = CBAMQuarterlyReport(
        id=uuid4(),
        organization_id=org_id,
        reporting_year=2025,
        reporting_quarter=4,
        period_start=date(2025, 10, 1),
        period_end=date(2025, 12, 31),
        submission_deadline=date(2026, 1, 31),
        status=CBAMReportStatus.SUBMITTED,
        total_imports_count=2,
        total_mass_tonnes=Decimal("120"),
        total_embedded_emissions_tco2e=Decimal("300"),
        by_sector={"iron_steel": {"mass_tonnes": 120.0}},
    )
    test_session.add(report)
    await test_session.commit()
    return report


async def test_quarterly_history_get_endpoints_still_work(
    client, auth_headers, test_session, test_org
):
    await _seed_quarterly_report(test_session, test_org.id)

    resp = await client.get("/api/cbam/reports/quarterly", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    reports = resp.json()
    assert len(reports) == 1
    assert reports[0]["year"] == 2025
    assert reports[0]["quarter"] == 4

    # EU-format export used report.year / report.quarter / inst.sectors —
    # none of which exist on the models.
    resp = await client.get(
        "/api/cbam/reports/quarterly/2025/4/export/eu-format", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text

    # CSV export used imp.direct_see / imp.total_see etc.
    resp = await client.get(
        "/api/cbam/reports/quarterly/2025/4/export/csv", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text

    # Registry XML is on hold
    resp = await client.get(
        "/api/cbam/reports/quarterly/2025/4/export/xml", headers=auth_headers
    )
    assert resp.status_code == 501


# ============================================================================
# EU ETS price endpoints
# ============================================================================


async def test_ets_price_latest_falls_back_when_empty(client):
    resp = await client.get("/api/cbam/ets-price/latest")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["is_fallback"] is True
    assert float(data["price_eur"]) == 75.0
    assert "placeholder" in data["assumption"]


async def test_ets_price_manual_upsert_and_latest(client, admin_headers):
    resp = await client.put(
        "/api/cbam/ets-price",
        json={"price_date": "2026-07-01", "price_eur": 82.4},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text

    # Upsert on the same date updates rather than duplicating
    resp = await client.put(
        "/api/cbam/ets-price",
        json={"price_date": "2026-07-01", "price_eur": 83.1},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text

    resp = await client.get("/api/cbam/ets-price/latest")
    data = resp.json()
    assert data["is_fallback"] is False
    assert float(data["price_eur"]) == 83.1
    assert data["price_date"] == "2026-07-01"


async def test_ets_price_endpoints_require_admin(client, viewer_headers, auth_headers):
    resp = await client.put(
        "/api/cbam/ets-price",
        json={"price_date": "2026-07-01", "price_eur": 82.4},
        headers=viewer_headers,
    )
    assert resp.status_code == 403

    resp = await client.post("/api/cbam/ets-price/refresh", headers=viewer_headers)
    assert resp.status_code == 403

    # The ETS price is PLATFORM data: an org admin (any self-signup) is 403 too.
    resp = await client.put(
        "/api/cbam/ets-price",
        json={"price_date": "2026-07-01", "price_eur": 82.4},
        headers=auth_headers,
    )
    assert resp.status_code == 403


async def test_ets_price_refresh_reports_no_live_source(client, admin_headers):
    resp = await client.post("/api/cbam/ets-price/refresh", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["updated"] is False
    assert "manually" in data["detail"] or "PUT /api/cbam/ets-price" in data["detail"]


async def test_screen_defaults_endpoint(client):
    resp = await client.get("/api/cbam/screen-defaults")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["default_value_markup_pct"] == 10.0
    assert data["sector_default_intensities"]["iron_steel"] == 2.5
    assert data["ets_price_is_fallback"] is True


async def test_screen_defaults_uses_newest_ets_price(client, test_session):
    from app.models.cbam import EUETSPrice

    for d, price in [
        (date(2026, 6, 24), Decimal("82.50")),
        (date(2026, 7, 1), Decimal("84.10")),
    ]:
        test_session.add(
            EUETSPrice(
                id=uuid4(),
                price_date=d,
                week_number=d.isocalendar()[1],
                year=d.year,
                price_eur=price,
            )
        )
    await test_session.commit()

    resp = await client.get("/api/cbam/screen-defaults")
    data = resp.json()
    assert data["ets_price_eur"] == 84.10
    assert data["ets_price_is_fallback"] is False
