"""Tests for the Data Hub — inventory profile + coverage matrix."""

from uuid import uuid4

import pytest

from app.models.hub import GHG_CATEGORIES


@pytest.mark.asyncio
async def test_hub_categories_lists_full_matrix(client, auth_headers):
    resp = await client.get("/api/hub/categories", headers=auth_headers)
    assert resp.status_code == 200
    cats = resp.json()
    assert len(cats) == len(GHG_CATEGORIES) == 19
    codes = [c["code"] for c in cats]
    assert "1.1" in codes and "2.1" in codes and "3.14" in codes


@pytest.mark.asyncio
async def test_profile_upsert_roundtrip_and_update(client, auth_headers, test_org):
    body = {
        "entries": [
            {"category_code": "1.1", "relevance": "relevant"},
            {
                "category_code": "2.3",
                "relevance": "not_relevant",
                "exclusion_reason": "No district heating at any site",
            },
        ]
    }
    resp = await client.put("/api/hub/profile", json=body, headers=auth_headers)
    assert resp.status_code == 200, resp.text

    resp = await client.get("/api/hub/profile", headers=auth_headers)
    assert resp.status_code == 200
    saved = {e["category_code"]: e for e in resp.json()}
    assert saved["1.1"]["relevance"] == "relevant"
    assert saved["1.1"]["scope"] == 1
    assert saved["2.3"]["exclusion_reason"] == "No district heating at any site"

    # Upserting the same category updates in place — no duplicate rows
    body = {
        "entries": [
            {
                "category_code": "1.1",
                "relevance": "relevant",
                "data_owner": "Facilities",
                "expected_form": "invoices",
            }
        ]
    }
    resp = await client.put("/api/hub/profile", json=body, headers=auth_headers)
    assert resp.status_code == 200
    resp = await client.get("/api/hub/profile", headers=auth_headers)
    rows = [e for e in resp.json() if e["category_code"] == "1.1"]
    assert len(rows) == 1
    assert rows[0]["data_owner"] == "Facilities"
    assert rows[0]["expected_form"] == "invoices"


@pytest.mark.asyncio
async def test_not_relevant_requires_exclusion_reason(client, auth_headers):
    body = {"entries": [{"category_code": "3.14", "relevance": "not_relevant"}]}
    resp = await client.put("/api/hub/profile", json=body, headers=auth_headers)
    assert resp.status_code == 422
    assert "3.14" in str(resp.json()["detail"])


@pytest.mark.asyncio
async def test_unknown_category_rejected(client, auth_headers):
    body = {"entries": [{"category_code": "9.9", "relevance": "relevant"}]}
    resp = await client.put("/api/hub/profile", json=body, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_viewer_cannot_edit_profile(client, test_session, test_org):
    from datetime import timedelta

    from app.api.auth import create_access_token, get_password_hash
    from app.models.core import User, UserRole

    viewer = User(
        id=uuid4(),
        email="viewer@example.com",
        hashed_password=get_password_hash("viewerpassword123"),
        organization_id=test_org.id,
        role=UserRole.VIEWER,
        is_active=True,
    )
    test_session.add(viewer)
    await test_session.commit()
    token = create_access_token(
        data={
            "sub": str(viewer.id),
            "org_id": str(viewer.organization_id),
            "role": viewer.role.value,
        },
        expires_delta=timedelta(hours=1),
    )
    body = {"entries": [{"category_code": "1.1", "relevance": "relevant"}]}
    resp = await client.put(
        "/api/hub/profile",
        json=body,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_site_profile_is_separate_layer(client, auth_headers, test_org):

    # org-level answer
    await client.put(
        "/api/hub/profile",
        json={"entries": [{"category_code": "1.2", "relevance": "relevant"}]},
        headers=auth_headers,
    )
    # site-level override
    resp = await client.post(
        "/api/organization/sites",
        json={"name": "Plant B", "country_code": "IL"},
        headers=auth_headers,
    )
    site_id = resp.json()["id"]
    resp = await client.put(
        "/api/hub/profile",
        json={
            "site_id": site_id,
            "entries": [
                {
                    "category_code": "1.2",
                    "relevance": "not_relevant",
                    "exclusion_reason": "Plant B has no vehicles",
                }
            ],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200

    org_level = (await client.get("/api/hub/profile", headers=auth_headers)).json()
    site_level = (
        await client.get(f"/api/hub/profile?site_id={site_id}", headers=auth_headers)
    ).json()
    assert {e["category_code"]: e["relevance"] for e in org_level}["1.2"] == "relevant"
    assert {e["category_code"]: e["relevance"] for e in site_level}[
        "1.2"
    ] == "not_relevant"


@pytest.mark.asyncio
async def test_overview_defaults_to_all_not_sure(client, auth_headers):
    resp = await client.get("/api/hub/overview", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["categories"]) == 19
    assert data["stats"]["not_sure"] == 19
    assert data["stats"]["open_questions"] == 0


@pytest.mark.asyncio
async def test_overview_aggregates_staged_rows_and_questions(
    client, auth_headers, test_session, test_org, test_user, test_period
):
    from app.models.ingestion import (
        ClarificationQuestion,
        IngestionSession,
        StagedRow,
    )

    ingestion = IngestionSession(
        organization_id=test_org.id,
        reporting_period_id=test_period.id,
        created_by=test_user.id,
        filename="fleet.xlsx",
        status="needs_answers",
    )
    test_session.add(ingestion)
    await test_session.commit()

    rows = [
        # two fleet rows on the ladder
        StagedRow(
            session_id=ingestion.id,
            category_code="1.2",
            scope=1,
            measurement_tier="calculated",
            status="ready",
        ),
        StagedRow(
            session_id=ingestion.id,
            category_code="1.2",
            scope=1,
            measurement_tier="estimated",
            status="needs_review",
        ),
        # market-based electricity ("2.2") must roll up into the 2.1 hub row
        StagedRow(
            session_id=ingestion.id,
            category_code="2.2",
            scope=2,
            measurement_tier="measured",
            status="ready",
        ),
        # rejected rows don't count
        StagedRow(
            session_id=ingestion.id,
            category_code="1.2",
            scope=1,
            measurement_tier="gap",
            status="rejected",
        ),
    ]
    for r in rows:
        test_session.add(r)
    await test_session.commit()

    # one question with its own category, one legacy question that falls back
    # to its staged row's category
    test_session.add(
        ClarificationQuestion(
            session_id=ingestion.id,
            question="Diesel or petrol fleet?",
            category_code="1.2",
        )
    )
    test_session.add(
        ClarificationQuestion(
            session_id=ingestion.id,
            staged_row_id=rows[2].id,
            question="Which supplier factor applies?",
        )
    )
    await test_session.commit()

    resp = await client.get("/api/hub/overview", headers=auth_headers)
    assert resp.status_code == 200
    by_code = {c["code"]: c for c in resp.json()["categories"]}

    fleet = by_code["1.2"]["coverage"]
    assert fleet["staged_count"] == 2
    assert fleet["staged_by_tier"]["calculated"] == 1
    assert fleet["staged_by_tier"]["estimated"] == 1
    assert fleet["open_questions"] == 1

    electricity = by_code["2.1"]["coverage"]
    assert electricity["staged_count"] == 1
    assert electricity["staged_by_tier"]["measured"] == 1
    assert electricity["open_questions"] == 1

    assert resp.json()["stats"]["open_questions"] == 2


@pytest.mark.asyncio
async def test_organization_profile_fields_roundtrip(client, auth_headers):
    resp = await client.patch(
        "/api/organization",
        json={
            "currency": "ils",
            "unit_system": "metric",
            "consolidation_approach": "operational_control",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["currency"] == "ILS"
    assert data["unit_system"] == "metric"
    assert data["consolidation_approach"] == "operational_control"

    resp = await client.patch(
        "/api/organization", json={"unit_system": "cubits"}, headers=auth_headers
    )
    assert resp.status_code == 400
    resp = await client.patch(
        "/api/organization", json={"currency": "SHEKELS"}, headers=auth_headers
    )
    assert resp.status_code == 400
