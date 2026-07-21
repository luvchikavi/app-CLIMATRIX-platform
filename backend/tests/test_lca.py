"""LCA-lite tests — impact factor library integrity, seeding sync, the
EF 3.1 indicator × EN 15804 module matrix, unit/region handling, and the
cradle-to-gate boundary fix on the PCF total."""

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.data import EF31_INDICATORS, EMISSION_FACTORS, IMPACT_FACTORS


def _impact_row(
    dataset_key,
    indicator_code,
    value,
    *,
    region="Global",
    unit="mol H+ eq",
    activity_unit="kWh",
):
    from app.models.emission import ImpactFactor

    return ImpactFactor(
        id=uuid4(),
        dataset_key=dataset_key,
        display_name=f"{dataset_key} test dataset",
        region=region,
        indicator_code=indicator_code,
        value=Decimal(str(value)),
        unit=unit,
        activity_unit=activity_unit,
        method_version="EF 3.1",
        source="test",
        year=2026,
    )


async def _make_product(client, headers, **overrides):
    body = {
        "name": "Steel Beam",
        "sku": "SB-100",
        "declared_unit": "kilogram",
        "declared_unit_amount": "1",
        **overrides,
    }
    resp = await client.post("/api/products", headers=headers, json=body)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _add_line(client, headers, product_id, **body):
    resp = await client.post(
        f"/api/products/{product_id}/inputs", headers=headers, json=body
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _compute(client, headers, product_id, period_id):
    resp = await client.post(
        f"/api/products/{product_id}/footprint",
        headers=headers,
        params={"period_id": period_id},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# --------------------------------------------------- curated data integrity


def test_curated_impact_library_covers_all_16_indicators_per_dataset():
    codes = {i["code"] for i in EF31_INDICATORS}
    assert len(codes) == 16
    by_dataset: dict[str, set] = {}
    for row in IMPACT_FACTORS:
        by_dataset.setdefault(row["dataset_key"], set()).add(row["indicator_code"])
        assert row["value"] > 0, f"{row['dataset_key']}/{row['indicator_code']} <= 0"
        assert row["method_version"] == "EF 3.1"
        assert row["notes"], "every curated row must carry a provenance note"
        assert "screening-grade" in row["notes"].lower()
    for key, seen in by_dataset.items():
        assert seen == codes, f"{key} missing {codes - seen}"


def test_curated_dataset_keys_align_with_emission_factor_library():
    """Every impact dataset must resolve on a BOM line that also resolves a
    GWP factor — dataset_key aligns with the emission library's activity_key."""
    emission_keys = {f["activity_key"] for f in EMISSION_FACTORS}
    impact_keys = {r["dataset_key"] for r in IMPACT_FACTORS}
    orphans = impact_keys - emission_keys
    assert not orphans, f"impact datasets without an emission factor: {orphans}"


@pytest.mark.asyncio
async def test_sync_impact_factors_idempotent_and_self_healing(test_session):
    from sqlmodel import select

    from app.database import sync_impact_factors
    from app.models.emission import ImpactFactor

    await sync_impact_factors(test_session)
    count = len((await test_session.execute(select(ImpactFactor))).scalars().all())
    assert count == len(IMPACT_FACTORS)

    # Second run adds nothing
    await sync_impact_factors(test_session)
    count2 = len((await test_session.execute(select(ImpactFactor))).scalars().all())
    assert count2 == count

    # A drifted value gets restored from the curated data
    row = (await test_session.execute(select(ImpactFactor).limit(1))).scalars().one()
    original = row.value
    row.value = Decimal("999999")
    await test_session.commit()
    await sync_impact_factors(test_session)
    await test_session.refresh(row)
    assert row.value == original


# --------------------------------------------------------- matrix compute


@pytest.mark.asyncio
async def test_lca_matrix_climate_from_engine_and_ef31_indicators(
    client: AsyncClient,
    test_org,
    test_period,
    test_session,
    auth_headers,
    seed_emission_factors,
):
    """2 kWh gas (0.183 -> 0.366 kg, A3) + 3 kg supplier billet at 2.5 (A1).
    Impact vector exists for gas only -> acidification A3 = 2 × 3e-4;
    supplier line is a climate-only line (honest gap on the other 15)."""
    test_session.add(_impact_row("natural_gas_kwh", "acidification", "3e-4"))
    await test_session.commit()

    resp = await client.post(
        "/api/supplier-pcfs",
        headers=auth_headers,
        json={
            "supplier_name": "GreenSteel",
            "product_name": "Scrap billet",
            "pcf_value": "2.5",
            "unit": "kilogram",
        },
    )
    spcf_id = resp.json()["id"]
    product = await _make_product(client, auth_headers)
    await _add_line(
        client,
        auth_headers,
        product["id"],
        input_type="energy",
        name="Furnace gas",
        quantity_per_unit="2",
        unit="kWh",
        activity_key="natural_gas_kwh",
    )
    await _add_line(
        client,
        auth_headers,
        product["id"],
        input_type="supplier_pcf",
        name="Scrap billet",
        quantity_per_unit="3",
        unit="kilogram",
        supplier_pcf_id=spcf_id,
    )

    fp = await _compute(client, auth_headers, product["id"], test_period.id)
    lca = fp["lca_results"]
    assert lca["method"] == "EF 3.1"
    assert "screening" in lca["note"].lower()
    assert lca["modules"] == ["A1", "A3"]
    assert len(lca["rows"]) == 16

    rows = {r["code"]: r for r in lca["rows"]}
    climate = rows["climate_change"]
    # Climate row == the PCF engine numbers, one GWP platform-wide
    assert climate["by_module"]["A3"] == pytest.approx(0.366, abs=1e-6)
    assert climate["by_module"]["A1"] == pytest.approx(7.5, abs=1e-6)
    assert climate["total"] == pytest.approx(7.866, abs=1e-6)
    assert climate["covered_lines"] == 2

    acid = rows["acidification"]
    assert acid["by_module"]["A3"] == pytest.approx(6e-4, rel=1e-6)
    assert acid["covered_lines"] == 1
    assert acid["gap_lines"] == ["Scrap billet"]

    # An indicator with no data at all: zero total, both lines as gaps
    odp = rows["ozone_depletion"]
    assert odp["total"] == 0
    assert odp["covered_lines"] == 0
    assert len(odp["gap_lines"]) == 2

    cov = {c["name"]: c for c in lca["line_coverage"]}
    assert "climate indicator only" in cov["Scrap billet"]["note"]
    assert cov["Furnace gas"]["dataset"] is not None
    assert lca["warnings"], "partial coverage must be flagged"

    # Matrix is frozen on the snapshot
    detail = await client.get(f"/api/products/{product['id']}", headers=auth_headers)
    assert detail.json()["footprints"][0]["lca_results"]["rows"]


@pytest.mark.asyncio
async def test_lca_unit_conversion_tonne_to_kg(
    client: AsyncClient,
    test_org,
    test_period,
    test_session,
    auth_headers,
    seed_emission_factors,
):
    """BOM line in tonnes against a per-kg impact dataset converts ×1000."""
    from app.models.emission import EmissionFactor

    test_session.add(
        EmissionFactor(
            id=uuid4(),
            activity_key="steel_purchased_kg",
            display_name="Steel",
            scope=3,
            category_code="3.1",
            co2e_factor=Decimal("2.1"),
            activity_unit="kg",
            factor_unit="kg CO2e/kg",
            source="TEST",
            region="Global",
            year=2024,
            status="approved",
        )
    )
    test_session.add(
        _impact_row("steel_purchased_kg", "acidification", "0.0065", activity_unit="kg")
    )
    await test_session.commit()

    product = await _make_product(client, auth_headers, declared_unit="tonne")
    await _add_line(
        client,
        auth_headers,
        product["id"],
        input_type="purchased_material",
        name="Steel coil",
        quantity_per_unit="0.002",
        unit="tonne",
        activity_key="steel_purchased_kg",
    )
    fp = await _compute(client, auth_headers, product["id"], test_period.id)
    rows = {r["code"]: r for r in fp["lca_results"]["rows"]}
    # 0.002 t = 2 kg -> 2 × 0.0065
    assert rows["acidification"]["by_module"]["A1"] == pytest.approx(0.013, rel=1e-6)


@pytest.mark.asyncio
async def test_lca_region_precedence_line_region_over_global(
    client: AsyncClient,
    test_org,
    test_period,
    test_session,
    auth_headers,
    seed_emission_factors,
):
    test_session.add(
        _impact_row("natural_gas_kwh", "acidification", "1e-4", region="Global")
    )
    test_session.add(
        _impact_row("natural_gas_kwh", "acidification", "9e-4", region="IL")
    )
    await test_session.commit()

    product = await _make_product(client, auth_headers)
    await _add_line(
        client,
        auth_headers,
        product["id"],
        input_type="energy",
        name="Gas IL",
        quantity_per_unit="1",
        unit="kWh",
        activity_key="natural_gas_kwh",
        region="IL",
    )
    fp = await _compute(client, auth_headers, product["id"], test_period.id)
    rows = {r["code"]: r for r in fp["lca_results"]["rows"]}
    assert rows["acidification"]["total"] == pytest.approx(9e-4, rel=1e-6)

    # Without a line region the org default (US) has no vector -> Global
    product2 = await _make_product(client, auth_headers, name="Beam 2", sku="SB-2")
    await _add_line(
        client,
        auth_headers,
        product2["id"],
        input_type="energy",
        name="Gas default",
        quantity_per_unit="1",
        unit="kWh",
        activity_key="natural_gas_kwh",
    )
    fp2 = await _compute(client, auth_headers, product2["id"], test_period.id)
    rows2 = {r["code"]: r for r in fp2["lca_results"]["rows"]}
    assert rows2["acidification"]["total"] == pytest.approx(1e-4, rel=1e-6)


@pytest.mark.asyncio
async def test_lca_unit_mismatch_is_honest_gap(
    client: AsyncClient,
    test_org,
    test_period,
    test_session,
    auth_headers,
    seed_emission_factors,
):
    """kWh line against a per-kg dataset: climate stays (engine converts),
    the other indicators become a flagged gap, never a silent wrong number."""
    test_session.add(
        _impact_row("natural_gas_kwh", "acidification", "3e-4", activity_unit="kg")
    )
    await test_session.commit()

    product = await _make_product(client, auth_headers)
    await _add_line(
        client,
        auth_headers,
        product["id"],
        input_type="energy",
        name="Furnace gas",
        quantity_per_unit="2",
        unit="kWh",
        activity_key="natural_gas_kwh",
    )
    fp = await _compute(client, auth_headers, product["id"], test_period.id)
    rows = {r["code"]: r for r in fp["lca_results"]["rows"]}
    assert rows["climate_change"]["total"] == pytest.approx(0.366, abs=1e-6)
    assert rows["acidification"]["total"] == 0
    cov = fp["lca_results"]["line_coverage"][0]
    assert "Unit mismatch" in cov["note"]


# ------------------------------------------- EN 15804 boundary + vocabulary


@pytest.mark.asyncio
async def test_beyond_gate_module_excluded_from_pcf_total(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    """An A4 (distribution) line shows in the stage breakdown and the LCA
    matrix but must NOT inflate the cradle-to-gate ISO 14067/PACT total."""
    product = await _make_product(client, auth_headers)
    await _add_line(
        client,
        auth_headers,
        product["id"],
        input_type="energy",
        name="Furnace gas",
        quantity_per_unit="2",
        unit="kWh",
        activity_key="natural_gas_kwh",
    )
    await _add_line(
        client,
        auth_headers,
        product["id"],
        input_type="energy",
        name="Outbound depot energy",
        quantity_per_unit="10",
        unit="kWh",
        activity_key="natural_gas_kwh",
        en15804_module="A4",
    )
    fp = await _compute(client, auth_headers, product["id"], test_period.id)

    assert float(fp["total_kgco2e_per_unit"]) == pytest.approx(0.366, abs=1e-6)
    assert fp["stage_breakdown"]["A4"] == pytest.approx(1.83, abs=1e-6)
    lines = {li["name"]: li for li in fp["line_items"]}
    a4 = lines["Outbound depot energy"]
    assert a4["in_pcf_total"] is False
    assert any("beyond cradle-to-gate" in w for w in a4["warnings"])
    rows = {r["code"]: r for r in fp["lca_results"]["rows"]}
    assert rows["climate_change"]["by_module"]["A4"] == pytest.approx(1.83, abs=1e-6)
    assert rows["climate_change"]["total"] == pytest.approx(2.196, abs=1e-6)


@pytest.mark.asyncio
async def test_full_en15804_module_vocabulary(
    client: AsyncClient, test_org, auth_headers
):
    product = await _make_product(client, auth_headers)
    for module in ("B6", "C4", "D"):
        line = await _add_line(
            client,
            auth_headers,
            product["id"],
            input_type="energy",
            name=f"Line {module}",
            quantity_per_unit="1",
            unit="kWh",
            activity_key="natural_gas_kwh",
            en15804_module=module,
        )
        assert line["en15804_module"] == module
    resp = await client.post(
        f"/api/products/{product['id']}/inputs",
        headers=auth_headers,
        json={
            "input_type": "energy",
            "name": "Bad",
            "quantity_per_unit": "1",
            "unit": "kWh",
            "en15804_module": "Z9",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_tiny_lcia_values_survive_storage(
    client: AsyncClient,
    test_org,
    test_period,
    test_session,
    auth_headers,
    seed_emission_factors,
):
    """ODP/CTUh-scale values (e-12) must round-trip the Numeric column —
    an unscaled Numeric silently zeroes them on SQLite."""
    test_session.add(
        _impact_row("natural_gas_kwh", "ozone_depletion", "3e-12", unit="kg CFC-11 eq")
    )
    await test_session.commit()

    product = await _make_product(client, auth_headers)
    await _add_line(
        client,
        auth_headers,
        product["id"],
        input_type="energy",
        name="Furnace gas",
        quantity_per_unit="2",
        unit="kWh",
        activity_key="natural_gas_kwh",
    )
    fp = await _compute(client, auth_headers, product["id"], test_period.id)
    rows = {r["code"]: r for r in fp["lca_results"]["rows"]}
    assert rows["ozone_depletion"]["total"] == pytest.approx(6e-12, rel=1e-6)
