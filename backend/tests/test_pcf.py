"""PCF module tests — product/BOM CRUD, tenancy, footprint math, supplier
PCFs, PACT export + teaser gating."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient


async def _second_org_headers(test_session):
    """A second org + user for cross-tenant checks."""
    from datetime import timedelta as td

    from app.api.auth import create_access_token
    from app.api.auth import get_password_hash
    from app.models.core import Organization, User, UserRole

    org = Organization(
        id=uuid4(),
        name="Other Org",
        country_code="DE",
        subscription_plan="professional",
        subscription_status="active",
    )
    test_session.add(org)
    user = User(
        id=uuid4(),
        email=f"other-{uuid4().hex[:8]}@example.com",
        hashed_password=get_password_hash("otherpassword123"),
        full_name="Other User",
        organization_id=org.id,
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()
    token = create_access_token(
        data={"sub": str(user.id), "org_id": str(org.id), "role": user.role.value},
        expires_delta=td(hours=1),
    )
    return {"Authorization": f"Bearer {token}"}


async def _trial_org_headers(test_session):
    """A trialing (teaser) org — compute allowed, exports 402."""
    from datetime import timedelta as td

    from app.api.auth import create_access_token
    from app.api.auth import get_password_hash
    from app.models.core import Organization, User, UserRole

    org = Organization(
        id=uuid4(),
        name="Trial Org",
        country_code="US",
        subscription_plan="professional",
        subscription_status="trialing",
        trial_ends_at=datetime.utcnow() + timedelta(days=7),
    )
    test_session.add(org)
    user = User(
        id=uuid4(),
        email=f"trial-{uuid4().hex[:8]}@example.com",
        hashed_password=get_password_hash("trialpassword123"),
        full_name="Trial User",
        organization_id=org.id,
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()
    token = create_access_token(
        data={"sub": str(user.id), "org_id": str(org.id), "role": user.role.value},
        expires_delta=td(hours=1),
    )
    return org, {"Authorization": f"Bearer {token}"}


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


# ------------------------------------------------------------- product CRUD


@pytest.mark.asyncio
async def test_create_and_list_products(client: AsyncClient, test_org, auth_headers):
    product = await _make_product(client, auth_headers)
    assert product["name"] == "Steel Beam"
    assert product["declared_unit"] == "kilogram"
    assert product["input_count"] == 0
    assert product["latest_footprint"] is None

    resp = await client.get("/api/products", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["sku"] == "SB-100"


@pytest.mark.asyncio
async def test_create_product_rejects_bad_declared_unit(
    client: AsyncClient, test_org, auth_headers
):
    resp = await client.post(
        "/api/products",
        headers=auth_headers,
        json={"name": "X", "declared_unit": "furlong"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_and_delete_product(client: AsyncClient, test_org, auth_headers):
    product = await _make_product(client, auth_headers)
    resp = await client.patch(
        f"/api/products/{product['id']}",
        headers=auth_headers,
        json={"name": "Steel Beam v2", "cn_code": "72142000"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Steel Beam v2"
    assert resp.json()["cn_code"] == "72142000"

    resp = await client.delete(f"/api/products/{product['id']}", headers=auth_headers)
    assert resp.status_code == 200
    resp = await client.get(f"/api/products/{product['id']}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_product_cross_tenant_isolation(
    client: AsyncClient, test_org, test_session, auth_headers
):
    product = await _make_product(client, auth_headers)
    other_headers = await _second_org_headers(test_session)

    resp = await client.get(f"/api/products/{product['id']}", headers=other_headers)
    assert resp.status_code == 404
    resp = await client.patch(
        f"/api/products/{product['id']}", headers=other_headers, json={"name": "Z"}
    )
    assert resp.status_code == 404
    resp = await client.get("/api/products", headers=other_headers)
    assert resp.json() == []


# ------------------------------------------------------------- BOM lines


@pytest.mark.asyncio
async def test_bom_line_crud_and_module_defaults(
    client: AsyncClient, test_org, auth_headers
):
    product = await _make_product(client, auth_headers)
    resp = await client.post(
        f"/api/products/{product['id']}/inputs",
        headers=auth_headers,
        json={
            "input_type": "transport",
            "name": "Inbound trucking",
            "quantity_per_unit": "0.5",
            "unit": "tonne-km",
            "activity_key": "hgv_tonne_km",
        },
    )
    assert resp.status_code == 200
    line = resp.json()
    assert line["en15804_module"] == "A2"  # transport defaults to A2

    resp = await client.patch(
        f"/api/products/{product['id']}/inputs/{line['id']}",
        headers=auth_headers,
        json={"quantity_per_unit": "0.75", "en15804_module": "A4"},
    )
    assert resp.status_code == 200
    assert float(resp.json()["quantity_per_unit"]) == 0.75
    assert resp.json()["en15804_module"] == "A4"

    resp = await client.delete(
        f"/api/products/{product['id']}/inputs/{line['id']}", headers=auth_headers
    )
    assert resp.status_code == 200
    detail = await client.get(f"/api/products/{product['id']}", headers=auth_headers)
    assert detail.json()["inputs"] == []


@pytest.mark.asyncio
async def test_bom_line_rejects_bad_enum_values(
    client: AsyncClient, test_org, auth_headers
):
    product = await _make_product(client, auth_headers)
    resp = await client.post(
        f"/api/products/{product['id']}/inputs",
        headers=auth_headers,
        json={
            "input_type": "wizardry",
            "name": "X",
            "quantity_per_unit": "1",
            "unit": "kg",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_bom_line_rejects_cross_tenant_supplier_pcf(
    client: AsyncClient, test_org, test_session, auth_headers
):
    other_headers = await _second_org_headers(test_session)
    resp = await client.post(
        "/api/supplier-pcfs",
        headers=other_headers,
        json={
            "supplier_name": "Their supplier",
            "product_name": "Their coil",
            "pcf_value": "2.1",
            "unit": "kilogram",
        },
    )
    their_pcf_id = resp.json()["id"]

    product = await _make_product(client, auth_headers)
    resp = await client.post(
        f"/api/products/{product['id']}/inputs",
        headers=auth_headers,
        json={
            "input_type": "supplier_pcf",
            "name": "Coil",
            "quantity_per_unit": "1",
            "unit": "kilogram",
            "supplier_pcf_id": their_pcf_id,
        },
    )
    assert resp.status_code == 404


# ------------------------------------------------------------- supplier PCFs


@pytest.mark.asyncio
async def test_supplier_pcf_manual_and_pact_upload(
    client: AsyncClient, test_org, auth_headers
):
    resp = await client.post(
        "/api/supplier-pcfs",
        headers=auth_headers,
        json={
            "supplier_name": "GreenSteel GmbH",
            "product_name": "HRC coil",
            "pcf_value": "1.85",
            "unit": "kilogram",
            "primary_data_share": 82.5,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["source"] == "manual"

    pact_file = {
        "id": str(uuid4()),
        "specVersion": "3.0.1",
        "companyName": "AluWorks BV",
        "productNameCompany": "Billet 6060",
        "pcf": {
            "declaredUnitOfMeasurement": "kilogram",
            "pcfExcludingBiogenic": "4.2",
            "primaryDataShare": 61,
        },
    }
    resp = await client.post(
        "/api/supplier-pcfs/upload",
        headers=auth_headers,
        json={"payload": pact_file},
    )
    assert resp.status_code == 200
    uploaded = resp.json()
    assert uploaded["supplier_name"] == "AluWorks BV"
    assert float(uploaded["pcf_value"]) == 4.2
    assert uploaded["source"] == "pact_json"
    assert uploaded["pact_pf_id"] == pact_file["id"]

    resp = await client.get("/api/supplier-pcfs", headers=auth_headers)
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_supplier_pcf_upload_rejects_invalid_file(
    client: AsyncClient, test_org, auth_headers
):
    resp = await client.post(
        "/api/supplier-pcfs/upload",
        headers=auth_headers,
        json={"payload": {"hello": "world"}},
    )
    assert resp.status_code == 422
    assert "PACT" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_supplier_pcf_delete_blocked_when_referenced(
    client: AsyncClient, test_org, auth_headers
):
    resp = await client.post(
        "/api/supplier-pcfs",
        headers=auth_headers,
        json={
            "supplier_name": "S",
            "product_name": "P",
            "pcf_value": "1.0",
            "unit": "kilogram",
        },
    )
    spcf_id = resp.json()["id"]
    product = await _make_product(client, auth_headers)
    await client.post(
        f"/api/products/{product['id']}/inputs",
        headers=auth_headers,
        json={
            "input_type": "supplier_pcf",
            "name": "Part",
            "quantity_per_unit": "1",
            "unit": "kilogram",
            "supplier_pcf_id": spcf_id,
        },
    )
    resp = await client.delete(f"/api/supplier-pcfs/{spcf_id}", headers=auth_headers)
    assert resp.status_code == 409


# ------------------------------------------------------------- footprint math


async def _build_steel_product(client, auth_headers):
    """1 kg product: 2 kWh natural gas (factor 0.183) + 3 kg supplier
    material at 2.5 kg CO2e/kg -> total 7.866, primary 7.5 (95.35%)."""
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
    for body in (
        {
            "input_type": "energy",
            "name": "Furnace gas",
            "quantity_per_unit": "2",
            "unit": "kWh",
            "activity_key": "natural_gas_kwh",
        },
        {
            "input_type": "supplier_pcf",
            "name": "Scrap billet",
            "quantity_per_unit": "3",
            "unit": "kilogram",
            "supplier_pcf_id": spcf_id,
        },
    ):
        r = await client.post(
            f"/api/products/{product['id']}/inputs",
            headers=auth_headers,
            json=body,
        )
        assert r.status_code == 200, r.text
    return product


@pytest.mark.asyncio
async def test_compute_footprint_math_and_provenance(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    product = await _build_steel_product(client, auth_headers)
    resp = await client.post(
        f"/api/products/{product['id']}/footprint",
        headers=auth_headers,
        params={"period_id": test_period.id},
    )
    assert resp.status_code == 200, resp.text
    fp = resp.json()

    total = Decimal(str(fp["total_kgco2e_per_unit"]))
    assert abs(total - Decimal("7.866")) < Decimal("0.001")
    assert fp["status"] == "draft"
    assert fp["primary_data_share"] == pytest.approx(95.35, abs=0.01)

    # Stage breakdown: energy -> A3, supplier material -> A1
    assert fp["stage_breakdown"]["A3"] == pytest.approx(0.366, abs=0.001)
    assert fp["stage_breakdown"]["A1"] == pytest.approx(7.5, abs=0.001)

    # Per-line derivation story
    lines = {li["name"]: li for li in fp["line_items"]}
    gas = lines["Furnace gas"]
    assert gas["factor"]["source"] == "DEFRA_2024"
    assert gas["formula"]
    billet = lines["Scrap billet"]
    assert billet["is_primary_data"] is True
    assert "GreenSteel" in billet["factor"]["source"]

    assert fp["methodology"]["standard"] == "ISO 14067:2018"
    assert fp["methodology"]["offsets_included"] is False


@pytest.mark.asyncio
async def test_compute_footprint_records_gap_for_unknown_factor(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    product = await _make_product(client, auth_headers)
    await client.post(
        f"/api/products/{product['id']}/inputs",
        headers=auth_headers,
        json={
            "input_type": "purchased_material",
            "name": "Unobtainium",
            "quantity_per_unit": "1",
            "unit": "kg",
            "activity_key": "unobtainium_kg",
        },
    )
    resp = await client.post(
        f"/api/products/{product['id']}/footprint",
        headers=auth_headers,
        params={"period_id": test_period.id},
    )
    assert resp.status_code == 200
    fp = resp.json()
    assert float(fp["total_kgco2e_per_unit"]) == 0
    assert fp["line_items"][0]["status"] == "gap"
    assert fp["warnings"]


@pytest.mark.asyncio
async def test_compute_footprint_requires_bom_and_valid_period(
    client: AsyncClient, test_org, test_period, test_session, auth_headers
):
    product = await _make_product(client, auth_headers)
    resp = await client.post(
        f"/api/products/{product['id']}/footprint",
        headers=auth_headers,
        params={"period_id": test_period.id},
    )
    assert resp.status_code == 422  # no BOM lines yet

    await client.post(
        f"/api/products/{product['id']}/inputs",
        headers=auth_headers,
        json={
            "input_type": "purchased_material",
            "name": "X",
            "quantity_per_unit": "1",
            "unit": "kg",
        },
    )
    resp = await client.post(
        f"/api/products/{product['id']}/footprint",
        headers=auth_headers,
        params={"period_id": str(uuid4())},
    )
    assert resp.status_code == 404  # foreign/unknown period


# ------------------------------------------------------------- finalize


@pytest.mark.asyncio
async def test_finalize_footprint_and_delete_protection(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    product = await _build_steel_product(client, auth_headers)
    fp = (
        await client.post(
            f"/api/products/{product['id']}/footprint",
            headers=auth_headers,
            params={"period_id": test_period.id},
        )
    ).json()

    resp = await client.post(
        f"/api/products/{product['id']}/footprints/{fp['id']}/finalize",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "final"
    assert resp.json()["finalized_at"] is not None

    resp = await client.post(
        f"/api/products/{product['id']}/footprints/{fp['id']}/finalize",
        headers=auth_headers,
    )
    assert resp.status_code == 409  # already final

    resp = await client.delete(f"/api/products/{product['id']}", headers=auth_headers)
    assert resp.status_code == 409  # finalized footprints protect the product


# ------------------------------------------------------------- PACT export


@pytest.mark.asyncio
async def test_pact_export_structure(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    product = await _build_steel_product(client, auth_headers)
    fp = (
        await client.post(
            f"/api/products/{product['id']}/footprint",
            headers=auth_headers,
            params={"period_id": test_period.id},
        )
    ).json()

    resp = await client.get(
        f"/api/products/{product['id']}/footprints/{fp['id']}/export/pact",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    doc = resp.json()
    assert doc["specVersion"] == "3.0.1"
    assert doc["companyName"] == "Test Organization"
    assert doc["productNameCompany"] == "Steel Beam"
    pcf = doc["pcf"]
    assert pcf["declaredUnitOfMeasurement"] == "kilogram"
    assert (
        Decimal(pcf["pcfExcludingBiogenic"])
        == Decimal(str(fp["total_kgco2e_per_unit"])).normalize()
    )
    assert pcf["primaryDataShare"] == pytest.approx(95.35, abs=0.01)
    assert "ISO 14067" in pcf["crossSectoralStandards"]
    assert pcf["referencePeriodStart"].startswith("2025-01-01")
    # PACT decimals serialize as strings
    assert isinstance(pcf["pcfExcludingBiogenic"], str)
    # Secondary sources listed from non-primary lines
    assert {"source": "DEFRA_2024", "version": ""} in pcf[
        "secondaryEmissionFactorSources"
    ]


@pytest.mark.asyncio
async def test_pact_export_tonne_scales_to_kilogram(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    product = await _make_product(
        client, auth_headers, name="Rebar", declared_unit="tonne"
    )
    await client.post(
        f"/api/products/{product['id']}/inputs",
        headers=auth_headers,
        json={
            "input_type": "energy",
            "name": "Gas",
            "quantity_per_unit": "1000",
            "unit": "kWh",
            "activity_key": "natural_gas_kwh",
        },
    )
    fp = (
        await client.post(
            f"/api/products/{product['id']}/footprint",
            headers=auth_headers,
            params={"period_id": test_period.id},
        )
    ).json()
    doc = (
        await client.get(
            f"/api/products/{product['id']}/footprints/{fp['id']}/export/pact",
            headers=auth_headers,
        )
    ).json()
    assert doc["pcf"]["declaredUnitOfMeasurement"] == "kilogram"
    # plain decimal string, never exponent notation ("1E+3")
    assert doc["pcf"]["declaredUnitAmount"] == "1000"
    # 183 kg CO2e per tonne -> 0.183 per kg
    assert Decimal(doc["pcf"]["pcfExcludingBiogenic"]) == Decimal("0.183")


@pytest.mark.asyncio
async def test_trial_can_compute_but_not_export(
    client: AsyncClient, test_session, test_period, test_org, seed_emission_factors
):
    """Teaser rule: the wow (compute) is visible, the benefit (export) locked."""
    trial_org, trial_headers = await _trial_org_headers(test_session)

    from datetime import date

    from app.models.core import ReportingPeriod

    period = ReportingPeriod(
        id=uuid4(),
        organization_id=trial_org.id,
        name="Trial FY2025",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
    )
    test_session.add(period)
    await test_session.commit()

    product = await _make_product(client, trial_headers)
    await client.post(
        f"/api/products/{product['id']}/inputs",
        headers=trial_headers,
        json={
            "input_type": "energy",
            "name": "Gas",
            "quantity_per_unit": "2",
            "unit": "kWh",
            "activity_key": "natural_gas_kwh",
        },
    )
    resp = await client.post(
        f"/api/products/{product['id']}/footprint",
        headers=trial_headers,
        params={"period_id": period.id},
    )
    assert resp.status_code == 200  # compute visible on trial
    fp = resp.json()

    resp = await client.get(
        f"/api/products/{product['id']}/footprints/{fp['id']}/export/pact",
        headers=trial_headers,
    )
    assert resp.status_code == 402  # export locked
    assert resp.json()["detail"]["code"] == "limit_reached"


@pytest.mark.asyncio
async def test_products_require_auth(client: AsyncClient):
    resp = await client.get("/api/products")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_delete_product_with_bom_and_footprint_under_fk_enforcement():
    """Prod-parity regression: PostgreSQL enforces FKs, the default test
    SQLite doesn't — deleting a product with BOM lines + footprints 500'd
    on prod while tests stayed green. This test turns PRAGMA foreign_keys
    ON so the delete order is actually exercised."""
    from decimal import Decimal as D

    from httpx import ASGITransport
    from sqlalchemy import event
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    from sqlmodel import SQLModel

    from app.api.auth import create_access_token, get_password_hash
    from app.database import get_session
    from app.main import app
    from app.models.core import Organization, ReportingPeriod, User, UserRole
    from app.models.emission import EmissionFactor

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(engine.sync_engine, "connect")
    def _fk_on(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        org = Organization(
            id=uuid4(),
            name="FK Org",
            country_code="US",
            default_region="US",
            subscription_plan="professional",
            subscription_status="active",
        )
        user = User(
            id=uuid4(),
            email="fk@example.com",
            hashed_password=get_password_hash("fk-password-123"),
            full_name="FK User",
            organization_id=org.id,
            role=UserRole.ADMIN,
            is_active=True,
        )
        period = ReportingPeriod(
            id=uuid4(),
            organization_id=org.id,
            name="FY2025",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31),
        )
        factor = EmissionFactor(
            id=uuid4(),
            activity_key="natural_gas_kwh",
            display_name="Natural Gas (kWh)",
            scope=1,
            category_code="1.1",
            co2e_factor=D("0.183"),
            activity_unit="kWh",
            factor_unit="kg CO2e/kWh",
            source="DEFRA_2024",
            region="Global",
            year=2024,
            status="approved",
        )
        session.add_all([org, user, period, factor])
        await session.commit()

        async def override_get_session():
            yield session

        app.dependency_overrides[get_session] = override_get_session
        try:
            token = create_access_token(
                data={
                    "sub": str(user.id),
                    "org_id": str(org.id),
                    "role": user.role.value,
                },
                expires_delta=timedelta(hours=1),
            )
            headers = {"Authorization": f"Bearer {token}"}
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                product = await _make_product(ac, headers)
                r = await ac.post(
                    f"/api/products/{product['id']}/inputs",
                    headers=headers,
                    json={
                        "input_type": "energy",
                        "name": "Gas",
                        "quantity_per_unit": "2",
                        "unit": "kWh",
                        "activity_key": "natural_gas_kwh",
                    },
                )
                assert r.status_code == 200, r.text
                r = await ac.post(
                    f"/api/products/{product['id']}/footprint",
                    headers=headers,
                    params={"period_id": str(period.id)},
                )
                assert r.status_code == 200, r.text

                r = await ac.delete(f"/api/products/{product['id']}", headers=headers)
                assert r.status_code == 200, r.text
                r = await ac.get(f"/api/products/{product['id']}", headers=headers)
                assert r.status_code == 404
        finally:
            app.dependency_overrides.clear()
    await engine.dispose()
