"""EPD generator tests — project CRUD + tenancy, the ISO 14025 status
machine (one step, freeze semantics, 5-year validity), EN 15804 PDF +
ILCD+EPD XML exports with teaser gating, and the verifier token portal
reuse. Ends with the end-to-end tools walk (PCF → LCA → EPD)."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from xml.etree import ElementTree as ET

import pytest
from httpx import AsyncClient


async def _second_org_headers(test_session):
    from datetime import timedelta as td

    from app.api.auth import create_access_token, get_password_hash
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


async def _trial_org_setup(test_session):
    """Trialing org + its own period (teaser: workflow open, exports 402)."""
    from datetime import timedelta as td

    from app.api.auth import create_access_token, get_password_hash
    from app.models.core import Organization, ReportingPeriod, User, UserRole

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
    period = ReportingPeriod(
        id=uuid4(),
        organization_id=org.id,
        name="Trial FY2025",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
    )
    test_session.add(period)
    await test_session.commit()
    token = create_access_token(
        data={"sub": str(user.id), "org_id": str(org.id), "role": user.role.value},
        expires_delta=td(hours=1),
    )
    return period, {"Authorization": f"Bearer {token}"}


async def _product_with_footprint(
    client, headers, period_id, *, finalize=True, name="Steel Beam"
):
    """Product + one gas BOM line + computed (optionally final) footprint."""
    resp = await client.post(
        "/api/products",
        headers=headers,
        json={"name": name, "sku": "SB-100", "declared_unit": "kilogram"},
    )
    assert resp.status_code == 200, resp.text
    product = resp.json()
    resp = await client.post(
        f"/api/products/{product['id']}/inputs",
        headers=headers,
        json={
            "input_type": "energy",
            "name": "Furnace gas",
            "quantity_per_unit": "2",
            "unit": "kWh",
            "activity_key": "natural_gas_kwh",
        },
    )
    assert resp.status_code == 200, resp.text
    resp = await client.post(
        f"/api/products/{product['id']}/footprint",
        headers=headers,
        params={"period_id": str(period_id)},
    )
    assert resp.status_code == 200, resp.text
    footprint = resp.json()
    if finalize:
        resp = await client.post(
            f"/api/products/{product['id']}/footprints/{footprint['id']}/finalize",
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        footprint = resp.json()
    return product, footprint


async def _make_epd(client, headers, product_id, **overrides):
    resp = await client.post(
        f"/api/products/{product_id}/epd", headers=headers, json=overrides
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _walk_to(client, headers, epd_id, target):
    """Walk the one-step machine to a target status."""
    order = ["internal_review", "verification", "registered", "published"]
    for status in order:
        resp = await client.post(
            f"/api/epd/{epd_id}/transition", headers=headers, json={"status": status}
        )
        assert resp.status_code == 200, resp.text
        if status == target:
            return resp.json()
    raise AssertionError(f"target {target} not reached")


# ------------------------------------------------------------- CRUD + registry


@pytest.mark.asyncio
async def test_create_epd_defaults_and_registry(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    product, footprint = await _product_with_footprint(
        client, auth_headers, test_period.id
    )
    epd = await _make_epd(client, auth_headers, product["id"])
    assert epd["name"] == "Steel Beam — EPD"
    assert epd["pcr"] == "EN 15804+A2"
    assert epd["status"] == "draft"
    assert epd["declared_unit"] == "kilogram"
    assert epd["scope_modules"] == ["A1", "A2", "A3", "C1", "C2", "C3", "C4", "D"]
    assert epd["valid_until"] is None

    resp = await client.get("/api/epd", headers=auth_headers)
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["product_name"] == "Steel Beam"


@pytest.mark.asyncio
async def test_epd_rejects_bad_modules_and_foreign_footprint(
    client: AsyncClient,
    test_org,
    test_period,
    test_session,
    auth_headers,
    seed_emission_factors,
):
    product, footprint = await _product_with_footprint(
        client, auth_headers, test_period.id
    )
    resp = await client.post(
        f"/api/products/{product['id']}/epd",
        headers=auth_headers,
        json={"scope_modules": ["A1", "Z9"]},
    )
    assert resp.status_code == 422

    # A footprint belonging to another product 404s on pin.
    other_product, other_fp = await _product_with_footprint(
        client, auth_headers, test_period.id, name="Other Product"
    )
    resp = await client.post(
        f"/api/products/{product['id']}/epd",
        headers=auth_headers,
        json={"footprint_id": other_fp["id"]},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_epd_cross_tenant_isolation(
    client: AsyncClient,
    test_org,
    test_period,
    test_session,
    auth_headers,
    seed_emission_factors,
):
    product, footprint = await _product_with_footprint(
        client, auth_headers, test_period.id
    )
    epd = await _make_epd(client, auth_headers, product["id"])
    other = await _second_org_headers(test_session)

    assert (await client.get(f"/api/epd/{epd['id']}", headers=other)).status_code == 404
    assert (
        await client.patch(f"/api/epd/{epd['id']}", headers=other, json={"notes": "x"})
    ).status_code == 404
    assert (
        await client.post(
            f"/api/epd/{epd['id']}/transition",
            headers=other,
            json={"status": "internal_review"},
        )
    ).status_code == 404
    assert (await client.get("/api/epd", headers=other)).json() == []


@pytest.mark.asyncio
async def test_epd_requires_auth(client: AsyncClient):
    assert (await client.get("/api/epd")).status_code == 401


# ------------------------------------------------------------- checklist


@pytest.mark.asyncio
async def test_checklist_reflects_readiness(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    # A bare product: everything red except RSL (no B modules declared).
    resp = await client.post(
        "/api/products",
        headers=auth_headers,
        json={"name": "Bare", "declared_unit": "kilogram"},
    )
    bare = resp.json()
    epd = await _make_epd(client, auth_headers, bare["id"])
    detail = (await client.get(f"/api/epd/{epd['id']}", headers=auth_headers)).json()
    checks = {c["key"]: c for c in detail["checklist"]}
    assert checks["bom"]["ok"] is False
    assert checks["footprint"]["ok"] is False
    assert checks["rsl"]["ok"] is True  # not required without B modules
    assert checks["operator"]["ok"] is False
    assert detail["results"] is None

    # Declaring B modules makes RSL required until rsl_years is set.
    resp = await client.patch(
        f"/api/epd/{epd['id']}",
        headers=auth_headers,
        json={"scope_modules": ["A1", "A2", "A3", "B1"]},
    )
    assert resp.status_code == 200
    checks = {
        c["key"]: c
        for c in (
            await client.get(f"/api/epd/{epd['id']}", headers=auth_headers)
        ).json()["checklist"]
    }
    assert checks["rsl"]["ok"] is False

    # A pinned final footprint flips the data checks green.
    product, footprint = await _product_with_footprint(
        client, auth_headers, test_period.id
    )
    epd2 = await _make_epd(
        client, auth_headers, product["id"], footprint_id=footprint["id"]
    )
    detail = (await client.get(f"/api/epd/{epd2['id']}", headers=auth_headers)).json()
    checks = {c["key"]: c for c in detail["checklist"]}
    assert checks["bom"]["ok"] is True
    assert checks["footprint"]["ok"] is True
    assert checks["final"]["ok"] is True
    assert detail["results"] is not None
    assert detail["results_are_frozen"] is False  # live preview while drafting


# ------------------------------------------------------------- status machine


@pytest.mark.asyncio
async def test_transition_requires_final_footprint(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    product, footprint = await _product_with_footprint(
        client, auth_headers, test_period.id, finalize=False
    )
    # No footprint pinned at all -> 422.
    epd = await _make_epd(client, auth_headers, product["id"])
    resp = await client.post(
        f"/api/epd/{epd['id']}/transition",
        headers=auth_headers,
        json={"status": "internal_review"},
    )
    assert resp.status_code == 422
    assert "Pin a computed footprint" in resp.json()["detail"]

    # Draft (non-final) footprint -> 422.
    resp = await client.patch(
        f"/api/epd/{epd['id']}",
        headers=auth_headers,
        json={"footprint_id": footprint["id"]},
    )
    assert resp.status_code == 200
    resp = await client.post(
        f"/api/epd/{epd['id']}/transition",
        headers=auth_headers,
        json={"status": "internal_review"},
    )
    assert resp.status_code == 422
    assert "finalize" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_transition_one_step_and_unknown_status(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    product, footprint = await _product_with_footprint(
        client, auth_headers, test_period.id
    )
    epd = await _make_epd(
        client, auth_headers, product["id"], footprint_id=footprint["id"]
    )
    # Jumping two steps is a 409 (the tracker idiom).
    resp = await client.post(
        f"/api/epd/{epd['id']}/transition",
        headers=auth_headers,
        json={"status": "verification"},
    )
    assert resp.status_code == 409
    # Unknown status is a 422.
    resp = await client.post(
        f"/api/epd/{epd['id']}/transition",
        headers=auth_headers,
        json={"status": "approved"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_freeze_publish_validity_and_immutability(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    product, footprint = await _product_with_footprint(
        client, auth_headers, test_period.id
    )
    epd = await _make_epd(
        client, auth_headers, product["id"], footprint_id=footprint["id"]
    )

    # Leave draft -> results freeze.
    resp = await client.post(
        f"/api/epd/{epd['id']}/transition",
        headers=auth_headers,
        json={"status": "internal_review"},
    )
    assert resp.status_code == 200
    detail = (await client.get(f"/api/epd/{epd['id']}", headers=auth_headers)).json()
    assert detail["results_are_frozen"] is True
    frozen_total = detail["results"]["pcf"]["total_kgco2e_per_unit"]
    assert frozen_total == pytest.approx(0.366, abs=0.001)

    # Frozen results survive a product recompute (that's the point).
    resp = await client.post(
        f"/api/products/{product['id']}/inputs",
        headers=auth_headers,
        json={
            "input_type": "energy",
            "name": "More gas",
            "quantity_per_unit": "10",
            "unit": "kWh",
            "activity_key": "natural_gas_kwh",
        },
    )
    assert resp.status_code == 200
    resp = await client.post(
        f"/api/products/{product['id']}/footprint",
        headers=auth_headers,
        params={"period_id": str(test_period.id)},
    )
    assert resp.status_code == 200
    detail = (await client.get(f"/api/epd/{epd['id']}", headers=auth_headers)).json()
    assert detail["results"]["pcf"]["total_kgco2e_per_unit"] == pytest.approx(
        frozen_total
    )

    # Content edits are locked outside draft; workflow fields stay open.
    resp = await client.patch(
        f"/api/epd/{epd['id']}", headers=auth_headers, json={"name": "New name"}
    )
    assert resp.status_code == 409
    resp = await client.patch(
        f"/api/epd/{epd['id']}",
        headers=auth_headers,
        json={"program_operator": "EPD International"},
    )
    assert resp.status_code == 200

    # verification -> registered -> published; validity = +5 years.
    for status in ("verification", "registered", "published"):
        resp = await client.post(
            f"/api/epd/{epd['id']}/transition",
            headers=auth_headers,
            json={"status": status},
        )
        assert resp.status_code == 200, resp.text
    published = resp.json()
    assert published["published_at"] is not None
    assert published["valid_until"] is not None
    valid_until = date.fromisoformat(published["valid_until"])
    assert valid_until.year == datetime.utcnow().year + 5
    assert published["days_until_expiry"] > 1700

    # A published EPD is immutable — even workflow fields.
    resp = await client.patch(
        f"/api/epd/{epd['id']}", headers=auth_headers, json={"notes": "x"}
    )
    assert resp.status_code == 409
    # And cannot be deleted.
    resp = await client.delete(f"/api/epd/{epd['id']}", headers=auth_headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_registered_requires_program_operator(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    product, footprint = await _product_with_footprint(
        client, auth_headers, test_period.id
    )
    epd = await _make_epd(
        client, auth_headers, product["id"], footprint_id=footprint["id"]
    )
    for status in ("internal_review", "verification"):
        resp = await client.post(
            f"/api/epd/{epd['id']}/transition",
            headers=auth_headers,
            json={"status": status},
        )
        assert resp.status_code == 200
    resp = await client.post(
        f"/api/epd/{epd['id']}/transition",
        headers=auth_headers,
        json={"status": "registered"},
    )
    assert resp.status_code == 422
    assert "program operator" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reopen_to_draft_thaws_results(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    product, footprint = await _product_with_footprint(
        client, auth_headers, test_period.id
    )
    epd = await _make_epd(
        client, auth_headers, product["id"], footprint_id=footprint["id"]
    )
    await client.post(
        f"/api/epd/{epd['id']}/transition",
        headers=auth_headers,
        json={"status": "internal_review"},
    )
    resp = await client.post(
        f"/api/epd/{epd['id']}/transition",
        headers=auth_headers,
        json={"status": "draft"},
    )
    assert resp.status_code == 200
    detail = (await client.get(f"/api/epd/{epd['id']}", headers=auth_headers)).json()
    assert detail["results_are_frozen"] is False
    assert detail["results_frozen_at"] is None
    # Content is editable again.
    resp = await client.patch(
        f"/api/epd/{epd['id']}", headers=auth_headers, json={"name": "Renamed EPD"}
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_draft_only(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    product, footprint = await _product_with_footprint(
        client, auth_headers, test_period.id
    )
    epd = await _make_epd(
        client, auth_headers, product["id"], footprint_id=footprint["id"]
    )
    await client.post(
        f"/api/epd/{epd['id']}/transition",
        headers=auth_headers,
        json={"status": "internal_review"},
    )
    assert (
        await client.delete(f"/api/epd/{epd['id']}", headers=auth_headers)
    ).status_code == 409

    epd2 = await _make_epd(client, auth_headers, product["id"])
    assert (
        await client.delete(f"/api/epd/{epd2['id']}", headers=auth_headers)
    ).status_code == 200
    assert (
        await client.get(f"/api/epd/{epd2['id']}", headers=auth_headers)
    ).status_code == 404


# ------------------------------------------------------------- documents


@pytest.mark.asyncio
async def test_pdf_and_ilcd_exports(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    product, footprint = await _product_with_footprint(
        client, auth_headers, test_period.id
    )
    epd = await _make_epd(
        client, auth_headers, product["id"], footprint_id=footprint["id"]
    )

    resp = await client.get(f"/api/epd/{epd['id']}/export/pdf", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:5] == b"%PDF-"
    assert len(resp.content) > 2000

    resp = await client.get(f"/api/epd/{epd['id']}/export/ilcd", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert "xml" in resp.headers["content-type"]
    root = ET.fromstring(resp.content)
    assert root.tag.endswith("processDataSet")
    text = resp.content.decode("utf-8")
    # The EN 15804 abbreviations + module-resolved amounts are in the dataset.
    assert "GWP-total" in text
    assert 'module="A3"' in text or ":module=" in text
    assert "EN 15804+A2" in text


@pytest.mark.asyncio
async def test_export_requires_pinned_footprint(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    resp = await client.post(
        "/api/products",
        headers=auth_headers,
        json={"name": "Bare", "declared_unit": "kilogram"},
    )
    epd = await _make_epd(client, auth_headers, resp.json()["id"])
    resp = await client.get(f"/api/epd/{epd['id']}/export/pdf", headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_trial_workflow_open_exports_locked(
    client: AsyncClient, test_session, test_org, seed_emission_factors
):
    """Teaser rule on EPD: modeling + workflow visible, documents locked."""
    period, trial_headers = await _trial_org_setup(test_session)
    product, footprint = await _product_with_footprint(client, trial_headers, period.id)
    epd = await _make_epd(
        client, trial_headers, product["id"], footprint_id=footprint["id"]
    )
    resp = await client.post(
        f"/api/epd/{epd['id']}/transition",
        headers=trial_headers,
        json={"status": "internal_review"},
    )
    assert resp.status_code == 200  # workflow open on trial

    for fmt in ("pdf", "ilcd"):
        resp = await client.get(
            f"/api/epd/{epd['id']}/export/{fmt}", headers=trial_headers
        )
        assert resp.status_code == 402
        assert resp.json()["detail"]["code"] == "limit_reached"


# ------------------------------------------------------------- verifier portal


@pytest.mark.asyncio
async def test_epd_verifier_token_flow(
    client: AsyncClient, test_org, test_period, auth_headers, seed_emission_factors
):
    product, footprint = await _product_with_footprint(
        client, auth_headers, test_period.id
    )
    epd = await _make_epd(
        client, auth_headers, product["id"], footprint_id=footprint["id"]
    )
    await client.post(
        f"/api/epd/{epd['id']}/transition",
        headers=auth_headers,
        json={"status": "internal_review"},
    )

    resp = await client.post(
        f"/api/epd/{epd['id']}/verifier-access",
        headers=auth_headers,
        json={"verifier_email": "verifier@sii.org.il", "verifier_name": "SII"},
    )
    assert resp.status_code == 200, resp.text
    access = resp.json()
    token = access["portal_url"].rstrip("/").split("/")[-1]

    # The token resolves to the EPD surface…
    resp = await client.get(f"/api/verify/{token}/context")
    assert resp.status_code == 200
    assert resp.json()["kind"] == "epd"

    resp = await client.get(f"/api/verify/{token}/epd")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["read_only"] is True
    assert payload["organization_name"] == test_org.name
    assert payload["epd"]["product_name"] == "Steel Beam"
    assert payload["results_are_frozen"] is True
    assert payload["results"]["pcf"]["total_kgco2e_per_unit"] == pytest.approx(
        0.366, abs=0.001
    )

    # …and NOT to the period surface.
    assert (await client.get(f"/api/verify/{token}")).status_code == 404
    assert (await client.get(f"/api/verify/{token}/inventory")).status_code == 404
    assert (await client.get(f"/api/verify/{token}/audit-log")).status_code == 404

    # Listed on the project; revocation kills the link immediately.
    resp = await client.get(
        f"/api/epd/{epd['id']}/verifier-access", headers=auth_headers
    )
    assert len(resp.json()) == 1
    resp = await client.delete(
        f"/api/verifier-access/{access['id']}", headers=auth_headers
    )
    assert resp.status_code == 200
    assert (await client.get(f"/api/verify/{token}/epd")).status_code == 404


@pytest.mark.asyncio
async def test_period_token_context_still_period(
    client: AsyncClient, test_org, test_period, auth_headers
):
    resp = await client.post(
        f"/api/periods/{test_period.id}/verifier-access",
        headers=auth_headers,
        json={"verifier_email": "auditor@example.com"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["portal_url"].rstrip("/").split("/")[-1]
    resp = await client.get(f"/api/verify/{token}/context")
    assert resp.json()["kind"] == "period"
    # Period tokens must not open the EPD surface.
    assert (await client.get(f"/api/verify/{token}/epd")).status_code == 404
    # And the period surface still works (regression on the nullable change).
    assert (await client.get(f"/api/verify/{token}")).status_code == 200


# ------------------------------------------------------------- E2E tools walk


@pytest.mark.asyncio
async def test_e2e_pcf_lca_epd_walk(
    client: AsyncClient,
    test_org,
    test_period,
    test_session,
    auth_headers,
    seed_emission_factors,
):
    """End-to-end QA across the product tool chain: model a product (PCF),
    get the LCA matrix, prepare + publish the EPD, verify through the
    portal token, export both documents."""
    from app.models.emission import ImpactFactor

    # Give the gas line an EF 3.1 vector so the LCA matrix has a non-climate row.
    test_session.add(
        ImpactFactor(
            dataset_key="natural_gas_kwh",
            display_name="Natural gas",
            region="Global",
            indicator_code="acidification",
            value=Decimal("0.0003"),
            unit="mol H+ eq",
            activity_unit="kWh",
            method_version="EF 3.1",
            source="test",
            year=2025,
            is_active=True,
        )
    )
    await test_session.commit()

    # 1) PCF: model + compute + finalize.
    product, footprint = await _product_with_footprint(
        client, auth_headers, test_period.id, name="E2E Widget"
    )
    assert footprint["status"] == "final"
    assert footprint["total_kgco2e_per_unit"]

    # 2) LCA-lite matrix came with the compute.
    lca = footprint["lca_results"]
    assert lca["method"] == "EF 3.1"
    by_code = {r["code"]: r for r in lca["rows"]}
    assert by_code["climate_change"]["total"] == pytest.approx(0.366, abs=0.001)
    assert by_code["acidification"]["total"] == pytest.approx(0.0006, abs=1e-6)

    # 3) EPD: prepare, freeze, walk to published.
    epd = await _make_epd(
        client, auth_headers, product["id"], footprint_id=footprint["id"]
    )
    await client.patch(
        f"/api/epd/{epd['id']}",
        headers=auth_headers,
        json={"program_operator": "EPD International"},
    )
    published = await _walk_to(client, auth_headers, epd["id"], "published")
    assert published["status"] == "published"
    assert published["valid_until"] is not None

    # 4) Verifier portal sees the frozen declaration.
    resp = await client.post(
        f"/api/epd/{epd['id']}/verifier-access",
        headers=auth_headers,
        json={"verifier_email": "verifier@sii.org.il"},
    )
    token = resp.json()["portal_url"].rstrip("/").split("/")[-1]
    payload = (await client.get(f"/api/verify/{token}/epd")).json()
    assert payload["results_are_frozen"] is True
    frozen_rows = {r["code"]: r for r in payload["results"]["lca"]["rows"]}
    assert frozen_rows["acidification"]["total"] == pytest.approx(0.0006, abs=1e-6)

    # 5) Both documents export.
    pdf = await client.get(f"/api/epd/{epd['id']}/export/pdf", headers=auth_headers)
    assert pdf.status_code == 200 and pdf.content[:5] == b"%PDF-"
    ilcd = await client.get(f"/api/epd/{epd['id']}/export/ilcd", headers=auth_headers)
    assert ilcd.status_code == 200
    assert b"AP" in ilcd.content and b"GWP-total" in ilcd.content
