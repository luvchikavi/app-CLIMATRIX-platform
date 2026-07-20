"""
Tests for the CBAM Phase 2 annual declaration builder.

Covers:
- generate: complete draft from the imports register — DB default values
  with the 2026 +10% markup where actual data is absent, actual lines kept
  as recorded, carbon-price-paid deductions summed from imports,
  certificate count (rounded up) and cost at the latest ETS price,
  per-sector + per-CN breakdowns, data-quality summary, assumptions
- regenerate: idempotent per org + year (replaces the draft, no duplicate)
- list endpoint
- detail endpoint (GET /reports/annual/{year}) incl. the stale flag
- status flow draft -> ready (submitted stays on hold)
- annual declaration CSV export
"""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

pytestmark = pytest.mark.asyncio


# ============================================================================
# Helpers
# ============================================================================


async def _create_import(client, auth_headers, **overrides):
    payload = {
        "cn_code": "72081000",
        "product_description": "Hot-rolled steel coil",
        "import_date": "2026-03-15",
        "mass_tonnes": 100,
        "origin_country": "TR",
    }
    payload.update(overrides)
    resp = await client.post("/api/cbam/imports", json=payload, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


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


async def _set_ets_price(client, admin_headers, price=80.0, price_date="2026-07-01"):
    resp = await client.put(
        "/api/cbam/ets-price",
        json={"price_date": price_date, "price_eur": price},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text


async def _seed_mixed_imports(client, auth_headers, admin_headers, test_session):
    """Two 2026 imports: one on defaults, one actual with a carbon price paid.

    Expected declaration arithmetic at ETS €80:
    - default line: DB default SEE 2.0 x (1 + 10% markup) x 100 t = 220 tCO2e
    - actual line: (2.0 + 0.5) SEE x 50 t = 125 tCO2e, no markup;
      carbon price paid €10/tCO2e -> deduction €1250 = 15.625 tCO2e,
      net 109.375 tCO2e
    - totals: gross 345, net 329.375, certificates ceil = 330,
      cost 329.375 x 80 = €26,350.00
    """
    await _seed_default_value(test_session)
    await _set_ets_price(client, admin_headers)

    default_line = await _create_import(client, auth_headers, mass_tonnes=100)
    actual_line = await _create_import(
        client,
        auth_headers,
        mass_tonnes=50,
        actual_direct_see=2.0,
        actual_indirect_see=0.5,
        foreign_carbon_price_eur=10.0,
    )
    return default_line, actual_line


# ============================================================================
# Generate — happy path arithmetic
# ============================================================================


async def test_generate_declaration_totals_and_data_quality(
    client, auth_headers, admin_headers, test_session
):
    await _seed_mixed_imports(client, auth_headers, admin_headers, test_session)

    resp = await client.post("/api/cbam/reports/annual/2026", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["year"] == 2026
    assert data["status"] == "draft"
    assert data["total_imports"] == 2
    assert float(data["total_mass_tonnes"]) == pytest.approx(150.0)
    assert data["submission_deadline"] == "2027-09-30"

    # DB default 2.0 x 1.10 x 100 = 220; actual 2.5 x 50 = 125
    assert float(data["gross_emissions_tco2e"]) == pytest.approx(345.0)
    # Deduction: €10/tCO2e x 125 tCO2e = €1250 -> 1250 / 80 = 15.625 tCO2e
    assert float(data["deductions_tco2e"]) == pytest.approx(15.625)
    assert float(data["deductions_eur"]) == pytest.approx(1250.0)
    assert float(data["net_emissions_tco2e"]) == pytest.approx(329.375)
    # Certificates to surrender rounded UP to whole certificates
    assert float(data["certificates_required"]) == pytest.approx(330.0)
    # Cost at the latest ETS price (€80, not the €75 fallback)
    assert float(data["ets_price_eur"]) == pytest.approx(80.0)
    assert float(data["estimated_cost_eur"]) == pytest.approx(26350.0)
    assert float(data["default_value_markup_pct"]) == pytest.approx(10.0)

    # Per-sector and per-CN breakdowns
    sector = data["by_sector"]["iron_steel"]
    assert sector["import_count"] == 2
    assert sector["default_lines"] == 1
    assert sector["actual_lines"] == 1
    assert float(sector["gross_emissions_tco2e"]) == pytest.approx(345.0)
    cn = data["by_cn_code"]["72081000"]
    assert cn["import_count"] == 2
    assert cn["countries"] == ["TR"]

    # Per-line drill list with intensity source
    assert len(data["lines"]) == 2
    by_source = {line["intensity_source"]: line for line in data["lines"]}
    assert float(by_source["default"]["see_tco2e_per_tonne"]) == pytest.approx(2.2)
    assert float(by_source["default"]["markup_pct"]) == pytest.approx(10.0)
    assert float(by_source["default"]["emissions_tco2e"]) == pytest.approx(220.0)
    assert float(by_source["actual"]["markup_pct"]) == pytest.approx(0.0)
    assert float(by_source["actual"]["net_emissions_tco2e"]) == pytest.approx(109.375)

    # Data-quality summary
    dq = data["data_quality"]
    assert dq["total_lines"] == 2
    assert dq["default_lines"] == 1
    assert dq["actual_lines"] == 1
    assert dq["default_share_pct"] == pytest.approx(50.0)
    assert dq["lines_without_db_default"] == 0

    # Assumptions are explicit
    assert any("markup" in a for a in data["assumptions"])
    assert any("€80" in a for a in data["assumptions"])
    assert any("CBAM Registry" in a for a in data["assumptions"])
    assert data["stale"] is False


async def test_generate_falls_back_to_import_time_default(client, auth_headers):
    """No DB default value row -> import-time SEE is used, plus the markup."""
    await _create_import(client, auth_headers, mass_tonnes=10)

    resp = await client.post("/api/cbam/reports/annual/2026", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    line = data["lines"][0]
    assert line["intensity_source"] == "default"
    assert "import-time default" in line["intensity_source_detail"]
    assert float(line["markup_pct"]) == pytest.approx(10.0)
    assert data["data_quality"]["lines_without_db_default"] == 1
    # ETS fallback price is used and surfaced
    assert float(data["ets_price_eur"]) == pytest.approx(75.0)


# ============================================================================
# Regenerate + list
# ============================================================================


async def test_regenerate_replaces_draft_not_duplicates(
    client, auth_headers, admin_headers, test_session
):
    await _seed_mixed_imports(client, auth_headers, admin_headers, test_session)

    resp1 = await client.post("/api/cbam/reports/annual/2026", headers=auth_headers)
    assert resp1.status_code == 200, resp1.text
    first = resp1.json()

    # Register another import, then regenerate
    await _create_import(client, auth_headers, mass_tonnes=100)
    resp2 = await client.post("/api/cbam/reports/annual/2026", headers=auth_headers)
    assert resp2.status_code == 200, resp2.text
    second = resp2.json()

    assert second["id"] == first["id"]  # replaced in place
    assert second["total_imports"] == 3
    # 345 + another default line 220 = 565
    assert float(second["gross_emissions_tco2e"]) == pytest.approx(565.0)

    # Exactly one declaration for the org + year
    resp = await client.get("/api/cbam/reports/annual", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    declarations = resp.json()
    assert len(declarations) == 1
    assert declarations[0]["year"] == 2026
    assert declarations[0]["total_imports"] == 3


# ============================================================================
# Detail endpoint
# ============================================================================


async def test_declaration_detail_404_before_generation(client, auth_headers):
    resp = await client.get("/api/cbam/reports/annual/2026", headers=auth_headers)
    assert resp.status_code == 404
    assert "generate" in resp.json()["detail"].lower()


async def test_declaration_detail_and_stale_flag(
    client, auth_headers, admin_headers, test_session
):
    await _seed_mixed_imports(client, auth_headers, admin_headers, test_session)
    resp = await client.post("/api/cbam/reports/annual/2026", headers=auth_headers)
    assert resp.status_code == 200, resp.text

    # Fresh detail: consistent with the stored draft
    resp = await client.get("/api/cbam/reports/annual/2026", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    detail = resp.json()
    assert detail["stale"] is False
    assert len(detail["lines"]) == 2
    assert float(detail["ets_price_eur"]) == pytest.approx(80.0)

    # Imports change after generation -> detail flags the draft as stale
    await _create_import(client, auth_headers, mass_tonnes=25)
    resp = await client.get("/api/cbam/reports/annual/2026", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["stale"] is True


# ============================================================================
# Status flow
# ============================================================================


async def test_declaration_status_flow_draft_ready(
    client, auth_headers, admin_headers, test_session
):
    await _seed_mixed_imports(client, auth_headers, admin_headers, test_session)
    resp = await client.post("/api/cbam/reports/annual/2026", headers=auth_headers)
    assert resp.status_code == 200, resp.text

    # draft -> ready
    resp = await client.patch(
        "/api/cbam/reports/annual/2026/status",
        json={"status": "ready"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "ready"

    # submitted stays on hold
    resp = await client.patch(
        "/api/cbam/reports/annual/2026/status",
        json={"status": "submitted"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "CBAM Registry" in resp.json()["detail"]

    # invalid status rejected
    resp = await client.patch(
        "/api/cbam/reports/annual/2026/status",
        json={"status": "accepted"},
        headers=auth_headers,
    )
    assert resp.status_code == 422

    # regenerating a ready declaration resets it to draft
    resp = await client.post("/api/cbam/reports/annual/2026", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "draft"


async def test_declaration_status_404_before_generation(client, auth_headers):
    resp = await client.patch(
        "/api/cbam/reports/annual/2026/status",
        json={"status": "ready"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ============================================================================
# CSV export
# ============================================================================


async def test_annual_declaration_csv_export(
    client, auth_headers, admin_headers, test_session
):
    await _seed_mixed_imports(client, auth_headers, admin_headers, test_session)
    resp = await client.post("/api/cbam/reports/annual/2026", headers=auth_headers)
    assert resp.status_code == 200, resp.text

    resp = await client.get(
        "/api/cbam/reports/annual/2026/export/csv", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/csv")
    assert "cbam_annual_declaration_2026.csv" in resp.headers["content-disposition"]

    body = resp.text
    assert "72081000" in body
    assert "Intensity Source" in body
    assert "TOTAL" in body
    assert "certificates to surrender: 330" in body


async def test_annual_declaration_csv_404_before_generation(client, auth_headers):
    resp = await client.get(
        "/api/cbam/reports/annual/2026/export/csv", headers=auth_headers
    )
    assert resp.status_code == 404
